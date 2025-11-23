#!/usr/bin/env python3
"""
Novara Pocket Judge (Alpha)
Verifies Evidence Bundles against v0.1 spec (L1).

L1 checks:
- Bundle structure (meta.json / aal.ndjson / anchors/)
- Required fields in meta.json / aal.ndjson
- Basic version / timestamp sanity
- bundle_sha256 (if present) matches the ZIP hash
"""

import sys
import hashlib
import zipfile
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


# ============================================================
# Constants (aligned with spec and JSON Schemas)
# ============================================================

# Required fields in meta.json (spec / meta.schema.json)
REQUIRED_META_FIELDS = ["bundle_id", "version", "timestamp", "system_info"]

# Recommended fields inside system_info (optional but checked if present)
REQUIRED_SYSTEM_INFO_FIELDS = ["name", "version", "operator"]

# Required fields for each AAL entry (spec / aal-entry.schema.json)
REQUIRED_AAL_FIELDS = ["timestamp", "actor", "action"]

# Evidence Bundle format version
VALID_EVB_VERSION = "0.1"

# AAL version (if present)
VALID_AAL_VERSION = "1.0"


# ============================================================
# Result Types
# ============================================================

@dataclass
class CheckResult:
    """Result of a single check (meta / aal / optional / hash)."""
    score: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def add_warning(self, msg: str, penalty: int = 1) -> None:
        self.warnings.append(msg)
        self.score -= penalty

    def add_error(self, msg: str, penalty: int = 4) -> None:
        self.errors.append(msg)
        self.score -= penalty


@dataclass
class VerificationResult:
    """Aggregated result of all checks."""
    meta: CheckResult
    aal: CheckResult
    optional: CheckResult
    hash_check: Optional[CheckResult] = None

    @property
    def total_score(self) -> int:
        base = self.meta.score + self.aal.score + self.optional.score
        if self.hash_check:
            base += self.hash_check.score
        return max(0, int(base))

    @property
    def all_warnings(self) -> list[str]:
        result: list[str] = []
        result.extend(self.meta.warnings)
        result.extend(self.aal.warnings)
        result.extend(self.optional.warnings)
        if self.hash_check:
            result.extend(self.hash_check.warnings)
        return result

    @property
    def all_errors(self) -> list[str]:
        result: list[str] = []
        result.extend(self.meta.errors)
        result.extend(self.aal.errors)
        result.extend(self.optional.errors)
        if self.hash_check:
            result.extend(self.hash_check.errors)
        return result

    @property
    def is_valid(self) -> bool:
        """
        L1-PASS if:
        - total_score >= 7
        - no critical errors
        """
        return self.total_score >= 7 and not self.all_errors


# ============================================================
# Verification Functions
# ============================================================

def verify_meta(z: zipfile.ZipFile) -> CheckResult:
    """
    Verify meta.json:
    - Exists
    - Has required fields
    - Version / timestamp / system_info sanity
    """
    result = CheckResult(score=4)  # full score for meta: 4

    if "meta.json" not in z.namelist():
        result.add_error("❌ meta.json missing")
        return result

    try:
        raw = z.read("meta.json").decode("utf-8")
        meta = json.loads(raw)
    except json.JSONDecodeError as e:
        result.add_error(f"❌ meta.json invalid JSON: {e}")
        return result
    except Exception as e:
        result.add_error(f"❌ meta.json read error: {e}")
        return result

    # Required fields (bundle_id / version / timestamp / system_info)
    missing = [f for f in REQUIRED_META_FIELDS if f not in meta]
    if missing:
        result.add_error(f"❌ meta.json missing required fields: {missing}")

    # Version must be "0.1"
    if "version" in meta and meta["version"] != VALID_EVB_VERSION:
        result.add_warning(
            f"⚠ version mismatch (expected: '{VALID_EVB_VERSION}', got: '{meta['version']}')"
        )

    # Basic timestamp format check (very loose)
    if "timestamp" in meta:
        ts = meta["timestamp"]
        if not isinstance(ts, str) or "T" not in ts:
            result.add_warning(
                "⚠ timestamp should be ISO 8601 (e.g. 2025-11-19T12:34:56Z)"
            )

    # system_info check (if present)
    if "system_info" in meta:
        if not isinstance(meta["system_info"], dict):
            result.add_warning("⚠ system_info should be an object")
        else:
            sys_missing = [
                f for f in REQUIRED_SYSTEM_INFO_FIELDS
                if f not in meta["system_info"]
            ]
            if sys_missing:
                result.add_warning(f"⚠ system_info missing fields: {sys_missing}")

    return result


def verify_aal(z: zipfile.ZipFile) -> CheckResult:
    """
    Verify aal.ndjson:
    - File exists
    - Each non-empty line is valid JSON
    - Each entry has required fields (timestamp / actor / action)
    - Optional: aal_version, timestamp sanity
    """
    result = CheckResult(score=4)

    if "aal.ndjson" not in z.namelist():
        result.add_error("❌ aal.ndjson missing")
        return result

    try:
        raw = z.read("aal.ndjson").decode("utf-8")
    except Exception as e:
        result.add_error(f"❌ aal.ndjson read error: {e}")
        return result

    lines = [line for line in raw.split("\n") if line.strip()]

    if not lines:
        result.add_warning("⚠ aal.ndjson is empty", penalty=2)
        return result

    error_count = 0
    warning_count = 0

    for i, line in enumerate(lines, start=1):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            error_count += 1
            if error_count <= 3:  # limit detailed errors
                result.add_error(f"❌ AAL line {i}: invalid JSON", penalty=1)
            continue

        # Required fields (timestamp / actor / action)
        missing = [f for f in REQUIRED_AAL_FIELDS if f not in entry]
        if missing:
            warning_count += 1
            if warning_count <= 5:
                result.add_warning(
                    f"⚠ AAL line {i}: missing fields {missing}",
                    penalty=0
                )

        # aal_version check (if present)
        if "aal_version" in entry and entry["aal_version"] != VALID_AAL_VERSION:
            warning_count += 1
            if warning_count <= 5:
                result.add_warning(
                    f"⚠ AAL line {i}: aal_version mismatch "
                    f"(expected: '{VALID_AAL_VERSION}', got: '{entry['aal_version']}')",
                    penalty=0
                )

        # Basic timestamp sanity
        if "timestamp" in entry:
            ts = entry["timestamp"]
            if not isinstance(ts, str) or "T" not in ts:
                warning_count += 1
                if warning_count <= 5:
                    result.add_warning(
                        f"⚠ AAL line {i}: timestamp not ISO 8601-like",
                        penalty=0
                    )

    if error_count > 3:
        result.add_error(
            f"❌ ...and {error_count - 3} more JSON errors in AAL",
            penalty=1
        )

    if warning_count > 5:
        result.add_warning(
            f"⚠ ...and {warning_count - 5} more AAL warnings",
            penalty=0
        )

    return result


def verify_optional(z: zipfile.ZipFile) -> CheckResult:
    """
    Verify optional components (anchors/, signatures, etc.).
    For v0.1 these are warnings only, not hard failures.
    """
    result = CheckResult(score=2)

    names = z.namelist()

    # anchors/ directory with at least one file
    has_anchors = any(
        name.startswith("anchors/") and len(name) > len("anchors/")
        for name in names
    )
    if not has_anchors:
        result.add_warning("⚠ No anchors/ found (optional for v0.1)", penalty=1)

    # signature-like files: name contains "ctk" or "signature"
    has_sig = any(
        "signature" in name.lower() or "ctk" in name.lower()
        for name in names
    )
    if not has_sig:
        result.add_warning("⚠ No cryptographic signature (optional for v0.1)", penalty=1)

    return result


def verify_bundle_hash(z: zipfile.ZipFile, bundle_path: Path) -> Optional[CheckResult]:
    """
    If meta.json contains bundle_sha256, verify it against the actual ZIP hash.
    Returns:
      - CheckResult if bundle_sha256 is present
      - None if bundle_sha256 is absent or meta.json could not be read
    """
    try:
        raw = z.read("meta.json").decode("utf-8")
        meta = json.loads(raw)
    except Exception:
        # meta errors are already handled in verify_meta
        return None

    if "bundle_sha256" not in meta:
        return None  # hash check is optional

    result = CheckResult(score=2)
    expected_hash = meta["bundle_sha256"]

    try:
        hasher = hashlib.sha256()
        with open(bundle_path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                hasher.update(chunk)
        actual_hash = hasher.hexdigest()
    except Exception as e:
        result.add_error(f"❌ Failed to calculate bundle hash: {e}")
        return result

    if actual_hash != expected_hash:
        result.add_error(
            "❌ bundle_sha256 mismatch!\n"
            f"   Expected: {expected_hash}\n"
            f"   Actual:   {actual_hash}"
        )

    return result


def verify_bundle(path: Path) -> VerificationResult:
    """
    Top-level verification:
    - Opens the ZIP
    - Runs meta / AAL / optional checks
    - Runs bundle_sha256 check (if present)
    """
    try:
        with zipfile.ZipFile(path, "r") as z:
            meta = verify_meta(z)
            aal = verify_aal(z)
            optional = verify_optional(z)
            hash_check = verify_bundle_hash(z, path)

            return VerificationResult(
                meta=meta,
                aal=aal,
                optional=optional,
                hash_check=hash_check
            )

    except zipfile.BadZipFile:
        meta = CheckResult()
        meta.add_error("❌ Not a valid ZIP file")
        return VerificationResult(
            meta=meta,
            aal=CheckResult(),
            optional=CheckResult(),
            hash_check=None,
        )

    except Exception as e:
        meta = CheckResult()
        meta.add_error(f"❌ Unexpected error: {e}")
        return VerificationResult(
            meta=meta,
            aal=CheckResult(),
            optional=CheckResult(),
            hash_check=None,
        )


# ============================================================
# Printing
# ============================================================

def print_result(result: VerificationResult, path: Path) -> None:
    """Pretty-print verification result for humans."""
    print(f"🔍 Verifying: {path}\n")

    # Quick summary
    checks: list[str] = []

    if not result.meta.errors:
        checks.append("✓ meta.json valid")
    else:
        checks.append("✗ meta.json has errors")

    if not result.aal.errors:
        checks.append("✓ aal.ndjson valid")
    else:
        checks.append("✗ aal.ndjson has errors")

    # anchors/ is optional in v0.1
    if result.optional.score > 0:
        if any("anchors/" in w for w in result.optional.warnings):
            checks.append("○ anchors/ optional (not required for v0.1)")
        else:
            checks.append("✓ anchors/ present")
    else:
        checks.append("○ anchors/ missing (still L1-possible)")

    if result.hash_check:
        if result.hash_check.errors:
            checks.append("✗ bundle_sha256 mismatch")
        else:
            checks.append("✓ bundle_sha256 verified")

    for c in checks:
        print(c)

    print("\n" + "=" * 60)

    # Errors
    if result.all_errors:
        print("\n❌ ERRORS:")
        for err in result.all_errors:
            print(f"  {err}")

    # Warnings
    if result.all_warnings:
        print("\n⚠  WARNINGS:")
        for warn in result.all_warnings:
            print(f"  {warn}")

    # Score & verdict
    print(f"\n📊 Score: {result.total_score}/10\n")

    if result.is_valid:
        print("✅ L1-PASS: Bundle is valid for basic audit")
    elif result.total_score >= 4:
        print("⚠️  L1-PARTIAL: Bundle has issues but may be usable")
    else:
        print("❌ L1-FAIL: Bundle fails verification")


# ============================================================
# Main
# ============================================================

def main() -> None:
    if len(sys.argv) < 2:
        print("Novara Pocket Judge (Alpha)")
        print()
        print("Usage: python3 verify.py <bundle.zip>")
        print()
        print("Verifies Evidence Bundles against v0.1 spec (L1 verification)")
        sys.exit(1)

    bundle_path = Path(sys.argv[1])

    if not bundle_path.exists():
        print(f"❌ File not found: {bundle_path}")
        sys.exit(1)

    result = verify_bundle(bundle_path)
    print_result(result, bundle_path)

    # Exit codes:
    # 0 = L1-PASS (OK)
    # 1 = L1-PARTIAL (usable with issues)
    # 2 = L1-FAIL (do not trust)
    if result.is_valid:
        sys.exit(0)
    elif result.total_score >= 4:
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
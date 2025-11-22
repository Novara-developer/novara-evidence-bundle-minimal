#!/usr/bin/env python3
"""
Novara Pocket Judge (Alpha)
Verifies Evidence Bundles against v0.1 spec.
"""

import sys
import zipfile
import json
from pathlib import Path


REQUIRED_META_FIELDS = ["bundle_id", "version", "timestamp", "system_info"]
REQUIRED_SYSTEM_INFO_FIELDS = ["name", "version", "operator"]
REQUIRED_AAL_FIELDS = ["timestamp", "actor", "action"]


def println(msg: str) -> None:
    """Simple print helper."""
    print(msg)


def verify_meta(z: zipfile.ZipFile) -> tuple[int, list[str], list[str]]:
    score = 4
    warnings: list[str] = []
    errors: list[str] = []

    if "meta.json" not in z.namelist():
        errors.append("❌ meta.json missing")
        return 0, warnings, errors

    println("✓ meta.json found")

    try:
        raw = z.read("meta.json").decode("utf-8")
        meta = json.loads(raw)
    except Exception as e:
        errors.append(f"❌ meta.json invalid JSON: {e}")
        return 0, warnings, errors

    missing = [f for f in REQUIRED_META_FIELDS if f not in meta]
    if missing:
        warnings.append(f"⚠ meta.json missing fields: {missing}")
        score -= 1

    if "version" in meta and meta["version"] != "0.1":
        warnings.append(f"⚠ meta.version != '0.1' (got: {meta['version']})")
        score -= 1

    if "system_info" in meta and isinstance(meta["system_info"], dict):
        sys_missing = [f for f in REQUIRED_SYSTEM_INFO_FIELDS if f not in meta["system_info"]]
        if sys_missing:
            warnings.append(f"⚠ system_info missing fields: {sys_missing}")
            score -= 1

    return max(score, 0), warnings, errors


def verify_aal(z: zipfile.ZipFile) -> tuple[int, list[str], list[str]]:
    score = 4
    warnings: list[str] = []
    errors: list[str] = []

    if "aal.ndjson" not in z.namelist():
        errors.append("❌ aal.ndjson missing")
        return 0, warnings, errors

    println("✓ aal.ndjson found")

    try:
        raw = z.read("aal.ndjson").decode("utf-8")
    except Exception as e:
        errors.append(f"❌ aal.ndjson unreadable: {e}")
        return 0, warnings, errors

    lines = [l for l in raw.split("\n") if l.strip()]
    if not lines:
        warnings.append("⚠ aal.ndjson is empty")
        score -= 1
        return max(score, 0), warnings, errors

    for i, line in enumerate(lines, start=1):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"❌ AAL line {i} invalid JSON")
            score -= 1
            continue

        missing = [f for f in REQUIRED_AAL_FIELDS if f not in entry]
        if missing:
            warnings.append(f"⚠ AAL line {i} missing fields: {missing}")
            score -= 0.5

    return max(score, 0), warnings, errors


def verify_optional(z: zipfile.ZipFile) -> tuple[int, list[str], list[str]]:
    score = 2
    warnings: list[str] = []
    errors: list[str] = []

    names = z.namelist()
    has_anchors = any(name.startswith("anchors/") for name in names)
    if not has_anchors:
        warnings.append("⚠ No anchors/ directory (optional for v0.1)")
        score -= 1
    else:
        println("✓ anchors/ present (at least one file)")

    has_signatures = any("ctk" in name.lower() or "signature" in name.lower() for name in names)
    if not has_signatures:
        warnings.append("⚠ No cryptographic signature (optional for v0.1)")
        score -= 1
    else:
        println("✓ cryptographic signature-like file present")

    return max(score, 0), warnings, errors


def verify_bundle(path: Path) -> bool:
    println(f"🔍 Verifying: {path}\n")

    total_score = 0
    all_warnings: list[str] = []
    all_errors: list[str] = []

    try:
        with zipfile.ZipFile(path, "r") as z:
            meta_score, meta_warn, meta_err = verify_meta(z)
            total_score += meta_score
            all_warnings.extend(meta_warn)
            all_errors.extend(meta_err)

            aal_score, aal_warn, aal_err = verify_aal(z)
            total_score += aal_score
            all_warnings.extend(aal_warn)
            all_errors.extend(aal_err)

            opt_score, opt_warn, opt_err = verify_optional(z)
            total_score += opt_score
            all_warnings.extend(opt_warn)
            all_errors.extend(opt_err)

    except zipfile.BadZipFile:
        all_errors.append("❌ Not a valid ZIP file")
        total_score = 0
    except Exception as e:
        all_errors.append(f"❌ Unexpected error while reading bundle: {e}")
        total_score = max(total_score - 3, 0)

    println("\n" + "=" * 50)

    if all_errors:
        println("\n❌ ERRORS:")
        for e in all_errors:
            println(f"  {e}")

    if all_warnings:
        println("\n⚠ WARNINGS:")
        for w in all_warnings:
            println(f"  {w}")

    println(f"\n📊 Score: {max(0, int(total_score))}/10")

    if total_score >= 7:
        println("✅ Bundle is valid for basic audit")
        ok = True
    elif total_score >= 4:
        println("⚠️  Bundle has issues but may be usable")
        ok = True
    else:
        println("❌ Bundle fails verification")
        ok = False

    return ok


def main() -> None:
    if len(sys.argv) < 2:
        println("Usage: python3 verify.py <bundle.zip>")
        sys.exit(1)

    bundle_path = Path(sys.argv[1])
    if not bundle_path.exists():
        println(f"❌ File not found: {bundle_path}")
        sys.exit(1)

    ok = verify_bundle(bundle_path)
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
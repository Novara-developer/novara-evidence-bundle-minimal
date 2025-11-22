#!/usr/bin/env python3
"""
Novara Pocket Judge (Alpha)
Verifies Evidence Bundles against v0.1 spec.
"""

import sys
import zipfile
import json
from pathlib import Path


REQUIRED_META_FIELDS = ["bundle_id", "timestamp", "system_info"]


def verify_bundle(bundle_path: str) -> bool:
    score = 10.0
    warnings = []
    errors = []

    bundle_path = Path(bundle_path)
    print(f"🔍 Verifying: {bundle_path}\n")

    if not bundle_path.exists():
        print(f"❌ File not found: {bundle_path}")
        return False

    try:
        with zipfile.ZipFile(bundle_path, "r") as zf:
            files = zf.namelist()

            # --- meta.json ---
            if "meta.json" not in files:
                errors.append("❌ meta.json missing")
                score -= 4
            else:
                print("✓ meta.json found")
                try:
                    meta = json.loads(zf.read("meta.json"))
                    missing = [k for k in REQUIRED_META_FIELDS if k not in meta]
                    if missing:
                        warnings.append(
                            f"⚠ meta.json missing fields: {', '.join(missing)}"
                        )
                        score -= 1
                except Exception as e:
                    errors.append(f"❌ meta.json invalid JSON: {e}")
                    score -= 3

            # --- aal.ndjson ---
            if "aal.ndjson" not in files:
                errors.append("❌ aal.ndjson missing")
                score -= 4
            else:
                print("✓ aal.ndjson found")
                try:
                    raw = zf.read("aal.ndjson").decode("utf-8")
                    lines = [l for l in raw.splitlines() if l.strip()]
                    if not lines:
                        warnings.append("⚠ aal.ndjson is empty")
                        score -= 1

                    for i, line in enumerate(lines, start=1):
                        try:
                            entry = json.loads(line)
                        except json.JSONDecodeError:
                            errors.append(f"❌ AAL line {i} is not valid JSON")
                            score -= 1
                            continue

                        if "timestamp" not in entry or "actor" not in entry:
                            warnings.append(
                                f"⚠ AAL line {i} missing 'timestamp' or 'actor'"
                            )
                            score -= 0.5
                except Exception as e:
                    errors.append(f"❌ Failed to read aal.ndjson: {e}")
                    score -= 3

            # --- optional: anchors/ ---
            has_anchor_dir = any(
                f.startswith("anchors/") for f in files
            )
            if not has_anchor_dir:
                warnings.append("⚠ No blockchain anchor (optional for v0.1)")
                score -= 1
            else:
                print("✓ anchors/ present")

            # --- optional: signatures ---
            has_sig = any(
                ("signature" in f.lower()) or ("ctk" in f.lower()) for f in files
            )
            if not has_sig:
                warnings.append("⚠ No CTK-2 signature (optional for v0.1)")
                score -= 1
            else:
                print("✓ cryptographic signature file present")

    except zipfile.BadZipFile:
        errors.append("❌ Not a valid ZIP file")
        score = 0
    except Exception as e:
        errors.append(f"❌ Unexpected error: {e}")
        score -= 5

    # --- result summary ---
    print("\n" + "=" * 50)

    if errors:
        print("\n❌ ERRORS:")
        for e in errors:
            print("  " + e)

    if warnings:
        print("\n⚠ WARNINGS:")
        for w in warnings:
            print("  " + w)

    score = max(0, round(score, 1))
    print(f"\n📊 Score: {score}/10")

    if score >= 7:
        print("✅ Bundle is valid for basic audit")
    elif score >= 4:
        print("⚠️  Bundle has issues but may be usable")
    else:
        print("❌ Bundle fails verification")

    return score >= 4


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 verify.py <bundle.zip>")
        sys.exit(1)

    target = sys.argv[1]
    ok = verify_bundle(target)
    sys.exit(0 if ok else 1)

#!/usr/bin/env python3
"""
generate_demo_bundle.py

Create a minimal Novara Evidence Bundle (v0.1) for demo purposes.
Output: examples/hinata-2025-11-19.zip
"""

import json
import zipfile
from pathlib import Path
from datetime import datetime, timezone

BUNDLE_PATH = Path("examples/hinata-2025-11-19.zip")


def build_meta() -> dict:
    """Return meta.json content for the demo bundle."""
    return {
        "bundle_id": "hinata-2025-11-19-demo",
        "version": "0.1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system_info": {
            "name": "Novara Demo Chatbot",
            "version": "v0.1",
            "operator": "Hinata (demo only)",
        },
        "incident_summary": (
            "Demo conversation bundle showing how Novara Evidence Bundles "
            "can record an AI session for later audit."
        ),
        "tags": ["demo", "chatbot", "novara-evidence-bundle"],
        "disclaimer": (
            "This bundle is demo-only and does not represent a real incident."
        ),
    }


def build_aal_lines() -> list[dict]:
    """Return a list of AAL (AI Action Log) entries."""
    return [
        {
            "timestamp": "2025-11-19T12:00:00Z",
            "actor": "user",
            "action": "send_message",
            "input": {
                "text": "How did the AI decide this?",
            },
            "output": None,
            "metadata": {
                "channel": "web",
                "session_id": "session-demo-001",
            },
        },
        {
            "timestamp": "2025-11-19T12:00:01Z",
            "actor": "chat-model",
            "action": "generate_response",
            "input": {
                "prompt_ref": "attachments/prompt.txt",
            },
            "output": {
                "text": "Here is how the decision was made...",
            },
            "metadata": {
                "model": "gpt-5.1-thinking-demo",
                "temperature": 0.3,
                "latency_ms": 180,
            },
        },
        {
            "timestamp": "2025-11-19T12:00:02Z",
            "actor": "logger",
            "action": "write_aal_entry",
            "input": {
                "entries": 2,
            },
            "output": {
                "status": "ok",
            },
            "metadata": {
                "logger_version": "0.1",
            },
        },
    ]


def main() -> None:
    # Ensure examples/ exists
    BUNDLE_PATH.parent.mkdir(parents=True, exist_ok=True)

    meta = build_meta()
    aal_entries = build_aal_lines()

    # Build AAL as NDJSON (one JSON per line)
    aal_ndjson = "\n".join(
        json.dumps(entry, ensure_ascii=False) for entry in aal_entries
    ) + "\n"

    # Create ZIP bundle
    with zipfile.ZipFile(BUNDLE_PATH, "w", compression=zipfile.ZIP_DEFLATED) as z:
        # meta.json
        z.writestr("meta.json", json.dumps(meta, indent=2, ensure_ascii=False))

        # aal.ndjson
        z.writestr("aal.ndjson", aal_ndjson)

        # attachments (prompt / notes)
        z.writestr(
            "attachments/prompt.txt",
            (
                "System: You are an AI whose decisions must be auditable.\n"
                "User: How did the AI decide this?\n"
            ),
        )
        z.writestr(
            "attachments/notes.md",
            "# Demo bundle\n\n"
            "- This is a demo Novara Evidence Bundle.\n"
            "- It shows how meta.json and aal.ndjson work together.\n",
        )

    print(f"✔ Demo bundle written to: {BUNDLE_PATH}")


if __name__ == "__main__":
    main()
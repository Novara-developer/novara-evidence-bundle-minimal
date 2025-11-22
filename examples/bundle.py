#!/usr/bin/env python3
"""
novara_evb.bundle

Minimal helper for creating Novara Evidence Bundles (v0.1).

This is intentionally small and simple:
- create a bundle in memory
- append AAL entries
- write a ZIP file with:
    - meta.json
    - aal.ndjson
    - attachments/ (optional, text-only for v0.1 helper)
"""

import json
import uuid
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def iso_now() -> str:
    """Return current time in ISO 8601 format with Z suffix."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


@dataclass
class EvidenceBundle:
    """
    Minimal in-memory representation of a Novara Evidence Bundle (v0.1).

    Usage:

        from novara_evb import EvidenceBundle

        bundle = EvidenceBundle(
            system_name="Novara Demo Chatbot",
            system_version="demo-0.1",
            operator="Hinata"
        )

        bundle.log_action(
            actor="user",
            action="send_message",
            input={"text": "navigate me to the campus library"},
        )

        bundle.save_zip("examples/hinata-2025-11-19.zip")
    """

    system_name: str
    system_version: str
    operator: str
    bundle_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=iso_now)
    incident_time: Optional[str] = None
    incident_summary: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    disclaimer: Optional[str] = None

    _aal_entries: List[Dict[str, Any]] = field(default_factory=list, init=False)
    _attachments: Dict[str, str] = field(default_factory=dict, init=False)

    # ------------------------
    # High-level helpers
    # ------------------------

    def log_action(
        self,
        actor: str,
        action: str,
        *,
        timestamp: Optional[str] = None,
        input: Optional[Dict[str, Any]] = None,
        output: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Append a single AAL entry.

        Only actor / action are required.
        Other fields are optional and may be omitted.
        """
        entry: Dict[str, Any] = {
            "timestamp": timestamp or iso_now(),
            "actor": actor,
            "action": action,
        }

        if input is not None:
            entry["input"] = input
        if output is not None:
            entry["output"] = output
        if metadata is not None:
            entry["metadata"] = metadata

        self._aal_entries.append(entry)

    def add_text_attachment(self, path_in_bundle: str, content: str) -> None:
        """
        Add a text attachment (e.g. prompt.txt, config.json) to the bundle.

        path_in_bundle is a relative path inside the ZIP, e.g.:
            "attachments/prompt.txt"
        """
        self._attachments[path_in_bundle] = content

    # ------------------------
    # Export
    # ------------------------

    def _build_meta(self) -> Dict[str, Any]:
        """Build meta.json content."""
        meta: Dict[str, Any] = {
            "bundle_id": self.bundle_id,
            "version": "0.1",
            "timestamp": self.created_at,
            "system_info": {
                "name": self.system_name,
                "version": self.system_version,
                "operator": self.operator,
            },
        }

        if self.incident_time:
            meta["incident_time"] = self.incident_time
        if self.incident_summary:
            meta["incident_summary"] = self.incident_summary
        if self.tags:
            meta["tags"] = self.tags
        if self.disclaimer:
            meta["disclaimer"] = self.disclaimer

        return meta

    def _build_aal_ndjson(self) -> str:
        """Return AAL as NDJSON string."""
        lines = [
            json.dumps(entry, ensure_ascii=False) for entry in self._aal_entries
        ]
        return "\n".join(lines) + ("\n" if lines else "")

    def save_zip(self, output_path: str | Path) -> Path:
        """
        Write the bundle as a ZIP file.

        Creates parent directories if needed.
        """
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        meta = self._build_meta()
        aal_ndjson = self._build_aal_ndjson()

        with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # meta.json
            zf.writestr(
                "meta.json",
                json.dumps(meta, indent=2, ensure_ascii=False),
            )

            # aal.ndjson
            zf.writestr("aal.ndjson", aal_ndjson)

            # attachments
            for rel_path, content in self._attachments.items():
                zf.writestr(rel_path, content)

        return out_path
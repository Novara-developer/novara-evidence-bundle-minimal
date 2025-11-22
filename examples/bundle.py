"""
novara_evb.bundle

Minimal helper class for creating Novara Evidence Bundles (v0.1).

This is a convenience wrapper so that other projects can do:

    from novara_evb import EvidenceBundle

    b = EvidenceBundle(
        bundle_id="hinata-2025-11-19-demo",
        system_name="Demo Navigation AI",
        system_version="0.0.1",
        operator="Hinata Lab",
        incident_summary="Demo bundle for Novara Evidence Bundle v0.1",
        tags=["demo", "navigation"],
    )

    b.add_event(
        actor="route-planner",
        action="calculate_route",
        input={"origin": "...", "destination": "..."},
        output={"eta_minutes": 12},
        metadata={"model": "nav-model-demo-001"},
    )

    b.add_text_attachment(
        "attachments/prompt.txt",
        "User: Please navigate me to the campus library.\n",
    )

    b.write_zip("examples/hinata-2025-11-19.zip")

This class implements only the minimal v0.1 spec:
- meta.json
- aal.ndjson
- attachments/ (optional)
"""

from __future__ import annotations

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
    Minimal in-memory representation of a Novara Evidence Bundle v0.1.

    - Holds meta.json fields
    - Collects AAL entries (events)
    - Collects text attachments
    - Can write itself to a .zip file compatible with the v0.1 spec
    """

    bundle_id: str
    system_name: str
    system_version: str
    operator: str

    version: str = "0.1"
    incident_summary: Optional[str] = None
    tags: Optional[List[str]] = None
    disclaimer: Optional[str] = None

    _created_at: str = field(default_factory=iso_now, init=False)
    _events: List[Dict[str, Any]] = field(default_factory=list, init=False)
    _attachments: Dict[str, str] = field(default_factory=dict, init=False)

    # --------- Construction helpers ---------

    @classmethod
    def new_demo(
        cls,
        system_name: str = "Novara Demo System",
        system_version: str = "demo-0.1",
        operator: str = "Novara Developer (demo)",
    ) -> "EvidenceBundle":
        """
        Create a demo bundle with a random bundle_id.

        Useful for quick experiments or tests.
        """
        bundle_id = f"evb-{uuid.uuid4()}"
        return cls(
            bundle_id=bundle_id,
            system_name=system_name,
            system_version=system_version,
            operator=operator,
            incident_summary="Demo bundle generated with novara_evb.EvidenceBundle.new_demo()",
            tags=["demo", "novara-evidence-bundle"],
            disclaimer="This bundle is for demonstration and testing only.",
        )

    # --------- API: add data ---------

    def add_event(
        self,
        *,
        actor: str,
        action: str,
        timestamp: Optional[str] = None,
        input: Optional[Dict[str, Any]] = None,
        output: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add one AAL (AI Action Log) entry.

        Only actor / action are required. If timestamp is omitted,
        the current time is used.
        """
        if timestamp is None:
            timestamp = iso_now()

        event: Dict[str, Any] = {
            "timestamp": timestamp,
            "actor": actor,
            "action": action,
        }

        if input is not None:
            event["input"] = input
        if output is not None:
            event["output"] = output
        if metadata is not None:
            event["metadata"] = metadata

        self._events.append(event)

    def add_text_attachment(self, path: str, content: str) -> None:
        """
        Add a text attachment that will be written into the bundle.

        `path` is the relative path inside the zip, e.g.:
            "attachments/prompt.txt"
            "attachments/config.json"
        """
        self._attachments[path] = content

    # --------- Internal helpers ---------

    def _build_meta(self) -> Dict[str, Any]:
        """Build the meta.json dict according to the v0.1 minimal spec."""
        meta: Dict[str, Any] = {
            "bundle_id": self.bundle_id,
            "version": self.version,
            "timestamp": self._created_at,
            "system_info": {
                "name": self.system_name,
                "version": self.system_version,
                "operator": self.operator,
            },
        }

        if self.incident_summary is not None:
            meta["incident_summary"] = self.incident_summary
        if self.tags is not None:
            meta["tags"] = self.tags
        if self.disclaimer is not None:
            meta["disclaimer"] = self.disclaimer

        return meta

    # --------- Output ---------

    def write_zip(self, path: str | Path) -> Path:
        """
        Write the bundle to a .zip file at `path`.

        Creates parent directories if needed.
        Returns the Path object for convenience.
        """
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        meta = self._build_meta()

        # Build NDJSON string for AAL entries
        aal_ndjson = ""
        for event in self._events:
            aal_ndjson += json.dumps(event, ensure_ascii=False) + "\n"

        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zf:
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

        return target
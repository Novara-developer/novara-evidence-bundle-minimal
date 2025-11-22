Novara Evidence Bundle v0.1 – Minimal Spec

Status: Draft
Version: 0.1.0
Date: 2025-11-20
License: CC BY 4.0

⸻

1. Overview

A Novara Evidence Bundle is a portable package that explains:
	•	what an AI system did
	•	when it did it
	•	under which configuration / context

in a way that third parties can verify later.

In v0.1, a bundle is a single ZIP file containing:
	•	meta.json – high-level metadata about the bundle
	•	aal.ndjson – AI Action Log (timeline of events)
	•	attachments/ – optional supporting files
	•	anchors/ – optional anchoring / proof files

This spec defines the minimal requirements for a valid v0.1 bundle.

It is implementation-neutral and is intended to work with:
	•	Novara Core (constitutional layer)
	•	Novara Incident Protocol v0.1
	•	Novara Proof Rail v0.1

⸻

2. Container format

A Novara Evidence Bundle v0.1 MUST:
	1.	Be a valid ZIP file
	2.	Use UTF-8 for all text files
	3.	Contain at least the following paths at the top level:

meta.json
aal.ndjson

The bundle MAY also contain:

attachments/
anchors/

Any additional files or directories are allowed, as long as they do not break these rules.

⸻

3. Required files

3.1 meta.json

meta.json is a single JSON object with high-level metadata.

Minimal required fields:

{
  "bundle_id": "string",
  "version": "0.1",
  "timestamp": "2025-11-19T12:34:56Z",
  "system_info": {
    "name": "string",
    "version": "string",
    "operator": "string"
  }
}

	•	bundle_id
	•	Globally unique identifier for this bundle (string).
	•	Format is implementation-defined (UUID, ULID, etc.).
	•	version
	•	MUST be "0.1" for this spec.
	•	timestamp
	•	ISO 8601 UTC timestamp for when the bundle was created.
	•	system_info
	•	name – human-readable system name
	•	version – system version or model identifier
	•	operator – organisation or person operating the system

Recommended (but optional) fields:

{
  "incident_summary": "string",
  "tags": ["navigation", "medical", "experimental"],
  "disclaimer": "string"
}

Implementations MAY add extra fields as needed,
but MUST NOT change the meaning of the required fields.

⸻

3.2 aal.ndjson

aal.ndjson (AI Action Log) is a newline-delimited JSON (NDJSON) file.
	•	Each non-empty line MUST be a valid JSON object.
	•	Lines are ordered by time, from oldest to newest.

Minimal required fields for each entry:

{
  "timestamp": "2025-11-19T12:35:00Z",
  "actor": "string",
  "action": "string"
}

	•	timestamp
	•	ISO 8601 UTC timestamp for the event.
	•	actor
	•	Which component took the action (e.g. "route-planner", "llm", "navigation-ui").
	•	action
	•	Short verb or event name (e.g. "generate", "calculate_route", "display_route").

Recommended additional fields:

{
  "input": {},
  "output": {},
  "metadata": {}
}

	•	input – JSON structure describing key inputs (prompt, parameters, request data, etc.).
	•	output – JSON structure describing key outputs (response, route, score, etc.).
	•	metadata – Free-form additional info (model id, temperature, map version, etc.).

Implementations MAY log more fields (e.g. hashes, signatures, decision ids),
as long as each line remains a valid JSON object.

⸻

4. Optional directories

4.1 attachments/

attachments/ is an optional directory at the top level of the ZIP.

Examples of files that MAY live here:
	•	prompt.txt – original user prompt
	•	config.json – system configuration used
	•	map-data-snapshot.json – snapshot of external data
	•	route-calculation-log.txt – raw logs

No specific structure is required in v0.1.
Implementations SHOULD choose descriptive filenames and formats.

4.2 anchors/

anchors/ is an optional directory for cryptographic proofs and anchoring data.

Examples (non-exhaustive):
	•	ctk2.json – CTK-2 mini record
	•	eth-anchor.json – Ethereum transaction reference
	•	tee-quote.json – TEE / attestation quote

For v0.1, no particular anchor type is required.
Verifiers MAY ignore unknown files under anchors/.

⸻

5. Validation rules (v0.1)

A bundle is considered valid for basic audit if:
	1.	The file is a valid ZIP archive
	2.	meta.json exists and is valid JSON with required fields
	3.	aal.ndjson exists and:
	•	is text, and
	•	each non-empty line is valid JSON with required fields
	4.	All timestamps in aal.ndjson are parsable ISO 8601 strings
	5.	Optional directories, if present, do not break ZIP structure

Anchors and signatures are optional in v0.1:
	•	Missing anchors/ → SHOULD emit a warning, NOT an error
	•	Missing signatures → SHOULD emit a warning, NOT an error

Example classification used by reference verifiers:
	•	Score ≥ 7 / 10 → valid for basic audit
	•	Score 4–6 / 10 → usable with issues
	•	Score ≤ 3 / 10 → fails verification

The exact scoring method is implementation-specific,
as long as the above validation rules are enforced.

⸻

6. Security and privacy (guidance)

This spec focuses on structure, not policy.
However, implementations SHOULD:
	•	Avoid storing raw personal identifiers when not needed
	•	Prefer pseudonymous IDs over real names
	•	Encrypt bundles at rest when they contain sensitive data
	•	Be explicit about what data is included via disclaimer or incident_summary

⸻

7. Versioning

This document defines Novara Evidence Bundle v0.1.
	•	Future minor versions (v0.2, v0.3, …) MAY extend the format
but SHOULD avoid breaking backwards compatibility.
	•	Major versions (v1.0+) MAY introduce breaking changes
and MUST be clearly distinguished.

Bundles MUST include a version field in meta.json
so that verifiers can select the appropriate validation rules.

⸻

8. Examples

Example bundle layout:

hinata-2025-11-19.zip
├─ meta.json
├─ aal.ndjson
├─ attachments/
│  ├─ prompt.txt
│  └─ config.json
└─ anchors/
   └─ ctk2.json

Minimal meta.json:

{
  "bundle_id": "hinata-2025-11-19-demo",
  "version": "0.1",
  "timestamp": "2025-11-19T12:34:56Z",
  "system_info": {
    "name": "Demo Navigation AI",
    "version": "0.0.1",
    "operator": "Hinata Lab"
  },
  "incident_summary": "Demo bundle for Novara Evidence Bundle v0.1",
  "tags": ["demo", "navigation"],
  "disclaimer": "This bundle is for demonstration only."
}

Minimal aal.ndjson (2 events):

{"timestamp": "2025-11-19T12:30:00Z", "actor": "route-planner", "action": "calculate_route"}
{"timestamp": "2025-11-19T12:31:00Z", "actor": "navigation-ui", "action": "display_route"}


⸻

9. Revision history
	•	v0.1.0 – initial minimal spec
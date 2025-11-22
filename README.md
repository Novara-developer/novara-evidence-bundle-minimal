novara-evidence-bundle-minimal

Minimal implementation of Novara Evidence Bundles (v0.1).

One ZIP file that explains what the AI did, when, and why.

⸻

What is this?

This repo is the smallest possible implementation of a Novara Evidence Bundle.

A single .zip file contains:
	•	meta.json – who / when / where
	•	aal.ndjson – AI Action Log (timeline of actions)
	•	extra files – prompts, configs, screenshots, etc.

So that third parties can later verify what happened.

This is not a full production system.
It is an MVP / demo implementation to show that:
	•	“This is what a Novara Evidence Bundle looks like.”
	•	“You can build it with simple Python code.”

⸻

Repo layout (target v0.1)

Locally, the repo is expected to look like this:

novara-evidence-bundle-minimal/
├─ README.md
├─ spec/
│  └─ novara-evidence-bundle-v0.1-spec.md   # text spec
├─ scripts/
│  └─ generate_demo_bundle.py               # demo bundle generator
├─ verifier/
│  └─ verify.py                             # Pocket Judge (alpha)
├─ examples/
│  └─ hinata-2025-11-19.zip                 # sample Evidence Bundle
└─ novara_evb/
   ├─ __init__.py
   └─ bundle.py                             # minimal Python SDK

At first, only README.md may exist.
Other folders (spec/, scripts/, verifier/, examples/, novara_evb/) will be added over time.

⸻

Quick start (local)

Assuming you cloned this repo on your local machine:

# Generate a demo Evidence Bundle
python3 scripts/generate_demo_bundle.py

# Verify it (Pocket Judge alpha)
python3 verifier/verify.py examples/hinata-2025-11-19.zip

Expected output (roughly):

🔍 Verifying: examples/hinata-2025-11-19.zip

✓ meta.json found
✓ aal.ndjson found
⚠ No blockchain anchor (optional for v0.1)
⚠ No CTK-2 signature (optional for v0.1)

📊 Score: 7/10
✅ Bundle is valid for basic audit

⸻

Bundle format (v0.1)

Inside a bundle .zip, files look like:

hinata-2025-11-19.zip
├─ meta.json          # who / when / where / which system
├─ aal.ndjson         # AI Action Log (1 event per JSONL line)
├─ attachments/       # prompts, config files, screenshots, etc.
└─ anchors/           # optional: blockchain / TEE anchors

	•	meta.json
	•	Basic info such as bundle_id, timestamp, system_info, etc.
	•	aal.ndjson
	•	Chronological AI action log (one JSON object per line).
	•	attachments/
	•	Input prompts, configuration files, screenshots, and other context.
	•	anchors/
	•	Reserved for future CTK-2 / blockchain / TEE anchoring data.

The full specification will live at:
	•	spec/novara-evidence-bundle-v0.1-spec.md (to be committed)

⸻

Using novara_evb (minimal SDK)

You can also generate Novara Evidence Bundles from your own projects
using the small helper library in novara_evb/.

Basic example:

from novara_evb import EvidenceBundle

# Create a demo bundle with a random bundle_id
bundle = EvidenceBundle.new_demo(
    system_name="Demo Navigation AI",
    system_version="0.0.1",
    operator="Hinata Lab",
)

# Add one AAL event
bundle.add_event(
    actor="route-planner",
    action="calculate_route",
    input={
        "origin": "user-current-location",
        "destination": "Campus Library",
    },
    output={"eta_minutes": 12},
    metadata={"model": "nav-model-demo-001"},
)

# Optional text attachment
bundle.add_text_attachment(
    "attachments/prompt.txt",
    "User: Please navigate me to the campus library.\n",
)

# Write a v0.1-compatible bundle
bundle.write_zip("examples/hinata-2025-11-19.zip")

Any project that imports novara_evb can create
v0.1-compatible Evidence Bundles (meta.json + aal.ndjson + attachments/)
with just a few lines of Python.

⸻

Relationship to other Novara repos
	•	Constitution / protocols (text-only)
→ novara-core
	•	Main app / implementation
→ Novara
	•	This repo
→ Minimal implementation (MVP) of the Evidence Bundle format.

In future, this repo is expected to link to examples using:
	•	CTK-2 anchoring
	•	Time Court replay
	•	Multi-agent graph integrations

⸻

Status
	•	v0.1 – experimental but serious minimal implementation.

The log format and ZIP layout are intended to remain as stable as possible.

If breaking changes are required, we will bump the minor version
(v0.2, v0.3, …).

⸻

Contributing

Contributions are welcome, including:
	•	Spec improvements
	•	Sample bundles (hypothetical reconstructed incidents)
	•	Additional test cases for the verifier

When opening a PR, please try to keep one PR = one main topic.

⸻

License
	•	Code: MIT License
	•	Spec / documentation: CC BY 4.0

Commercial, research, and educational use are all allowed.
Attribution is appreciated but not required.
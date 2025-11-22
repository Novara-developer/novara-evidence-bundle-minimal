# Navigation Misroute Incident (Hypothetical Reconstruction)

> This is a **hypothetical reconstruction** of a real class of incidents  
> where navigation systems directed users onto collapsed or closed bridges.

## Scenario

A navigation AI suggests a route that crosses `bridge-X`.

- In the real world, the bridge has **collapsed** weeks earlier.
- The map data is **outdated** and still marks the bridge as open.
- Users follow the suggested route and an accident occurs.

This bundle shows **how Novara Evidence Bundles could represent such a case**.

## Files

- `meta.json`  
  High-level metadata about the bundle (who / when / what).

- `aal.ndjson`  
  AI Action Log timeline:
  - `route-planner` calculates route via `bridge-X`
  - `map-validator` incorrectly marks route as `safe`
  - `navigation-ui` shows the route to the user
  - `incident-reporter` logs a critical event after the accident

In a real deployment, these would be packaged as:

```text
nav-misroute-2023-bridge.zip
├─ meta.json
├─ aal.ndjson
├─ attachments/
│  ├─ map-data-snapshot.json
│  └─ route-calculation-log.txt
└─ anchors/
   └─ ctk2.json
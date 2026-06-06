# tools/

**Lab-wide CLI and scripts.** Things that observe or operate across all modules.

## Planned

- `state-of-lab` — sweep the lab and report. v1 of `~/projects/cowork/scripts/state_of_projects.py`, but lab-aware: reads kernel run/deposit/merge records, `flume/registry`, `strata/manuscript-state`, `outcrop/recent-additions`, returns a single picture.
- `lab-init` — create a new typed `Plan` that spans modules, dispatched through the Rust distributary substrate.
- `lab-rivulet` — submit/status/result/cancel side-channel inference jobs for Watermaster research, critique, and plan/brief review.
- `lab-doctor` — health check across all modules: contract conformance, broken figure refs, stale citations, dead lineages, dangling baselines.
- `lab-watershed` — visualize the actual lab as a watershed graph; show which modules are flowing, where pressure-tests are firing, where baselines anchor.

## Status

Placeholder. Tools land here as the lab gets used and recurring needs surface.

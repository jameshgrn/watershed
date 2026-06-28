# tools/

**Lab-wide CLI and scripts.** Things that observe or operate across all modules.

## Available

- `lab state-of` — report the current branch, sync state, working tree state,
  latest lineage seat, open brainstorm threads, and open GitHub PRs.
- `lab splay review --file <path> --angles "clarity,correctness"` — run a
  read-only splay review through the configured provider. Defaults to the local
  Gemma OpenAI-compatible server at `http://127.0.0.1:8080/v1`.
- `lab verify run --spec verification.json --manifest manifest.json` — consume
  a `VerificationSpec` JSON object, run the declared checks through an
  above-kernel command manifest, and emit concrete verification evidence JSON.
  The manifest maps each check name to an argv command list, optional working
  directory, and optional timeout; command stdout/stderr, exit code, timing,
  and pass/fail status are captured for later tributary inspection.

## Planned

- `lab-init` — create a new typed `Plan` that spans modules, dispatched through the Rust distributary substrate.
- `lab-rivulet` — submit/status/result/cancel side-channel inference jobs for Watermaster research, critique, and plan/brief review.
- `lab-doctor` — health check across all modules: contract conformance, broken figure refs, stale citations, dead lineages, dangling baselines.
- `lab-watershed` — visualize the actual lab as a watershed graph; show which modules are flowing, where pressure-tests are firing, where baselines anchor.

## Status

The first live tools are `lab state-of` and `lab splay review`. Broader lab
tools land here as recurring needs surface.

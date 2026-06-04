# distributary/

**Agent dispatch.** Where work fans out into branches.

## Provenance

Half of `dgov/` — the fan-out half. v0 keeps only outbound records in memory.

## What v0 Owns

- **Plan records** — typed `PlanSpec` and `PlanUnit` shapes for one outbound task graph
- **File claims** — kernel-shaped `FileClaim` mirrors with read/write authority mapping
- **Dispatch records** — pending and active `DispatchRun` state with lifecycle validation
- **Worker returns** — terminal telemetry envelopes that pin results onto `DispatchRun`

## Public types (v0)

| Type | Module | Purpose |
|---|---|---|
| `PlanSpec` | `plan` | A governor's execution plan with typed units |
| `PlanUnit` | `plan` | Single unit of work: prompt, files, dependencies |
| `PlanUnitFiles` | `plan` | Exact file scope: create / edit / delete / read / touch |
| `PlanIssue` | `plan` | Validation issue (error or warning) |
| `PlanValidationError` | `plan` | Raised when structural validation fails |
| `validate_plan` | `plan` | Structural validation: slugs, file-claim conflicts |
| `FileClaim` | `claims` | Kernel-shaped `{path, kind}` mirror |
| `ClaimKind` | `claims` | `ReadOnly` / `Exclusive` / `Shared` |
| `adapt_plan_unit_files_to_claims` | `claims` | Adapter: `PlanUnitFiles → tuple[FileClaim, ...]` |
| `DispatchRun` | `dispatch_run` | One worker execution attempt, frozen-pin lifecycle |
| `DispatchRunState` | `dispatch_run` | `pending → active → done/failed/timed_out/abandoned` |
| `derive_dispatch_run_id` | `dispatch_run` | Content-derived stable id with `disprun:` tag |
| `WorkerReturn` | `worker_return` | Terminal worker telemetry keyed by `dispatch_run_id` |
| `WorkerReturnState` | `worker_return` | `done` / `failed` / `timed_out` / `abandoned` |

## Design constraints

- **No dgov imports** — clean watershed package; no dependency on `dgov`.
- **Frozen dataclasses + `__slots__`** — immutable by default; `ValueError` for illegal states.
- **Kernel contract alignment** — `FileClaim` and `ClaimKind` match the Rust schema in `watershed-kernel/schemas/`.
- **v0 omissions** — no `run_source`, no TOML parsing, no `Plan.id` hashing (flagged for follow-up).

## Why "distributary"

In a river system, a distributary is where a single channel splits into many branches that fan out toward the sea — the canonical example is a delta. In agentic terms, that's the record boundary where one request becomes typed outbound work.

The metaphor goes the right way: distributary is *outflow*. Work leaves here.

## Pair

`tributary/` is the matched fan-in. Distributary fans work out; tributary brings typed outputs back and merges. Together they replace dgov.

## Status

v0 outbound records and terminal worker-return envelope implemented. Verification gates pass.

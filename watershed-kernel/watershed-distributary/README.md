# watershed-distributary

This crate owns outbound lawful motion through the pure DAG kernel, the `Plan`
state machine, and worker `Run` transitions.

## DAG Kernel

`dag::DagKernel` is the Rust port of dgov's kernel idea: a pure deterministic
state machine where `(state, event) -> (new state, actions)`.

It owns no subprocesses, worktrees, persistence, or worker execution. Those
belong outside the kernel.

The DAG kernel enforces:

- dependency-gated dispatch,
- independent file-claim conflict rejection,
- serial topological merge,
- scan-based merge after terminal failures,
- failure cascade to pending dependents,
- governor retry/fail/skip decisions after interrupted work,
- and a typed action/event boundary between orchestration and effects.

`DagTask` and `DagPlan` are the typed declaration layer immediately before
kernel state. `DagTask::new(...)` rejects claimless work and empty claim paths, and
`DagPlan::new(...)` rejects duplicate slugs, unknown dependencies, cycles, and
independent tasks with overlapping write authority unless the overlap is
explicitly shared. `DagPlan::compile_kernel()` carries each task's `FileClaim`s
into the `MergeTask` action that settlement consumes.

## Plan Ceremony

Legal `Plan` transitions:

- `Plan<Drafted>::draft() -> Plan<Drafted>`
- `Plan<Drafted>::recover_intent(...) -> Plan<IntentRecovered>`
- `Plan<IntentRecovered>::declare_claims(...) -> Plan<ClaimsDeclared>`
- `Plan<ClaimsDeclared>::compile(...) -> Plan<Compiled>`
- `Plan<Compiled>::validate(...) -> Plan<Validated>`

Legal run motion:

- `dispatch(Plan<Validated>) -> Run<Pending>`
- `Run<Pending>::start() -> Run<Running>`
- `Run<Running>::complete(summary, touched_files) -> Run<Completed>`
- `Run<Running>::fail(reason) -> Run<Failed>`
- `Run<Failed>::retry() -> Result<Run<Pending>, RetryError>`
- `mock_worker(Run<Running>) -> Run<Completed>` (test helper)
- `collect(Run<Completed>) -> (Deposit, Vec<FileClaim>)`

The run carries `id`, `intent`, `claims`, `retried_from`, `retry_index`, and the validating policy's retry budget forward from dispatch through every state, so `collect` can return both the worker's `Deposit` and the dispatch-time `FileClaim`s for downstream claims-integrity validation.

Original dispatch creates a run with no retry parent and `retry_index == 0`.
Retrying a failed run consumes `Run<Failed>`, checks the validating policy's `max_retries`, preserves the same intent and claims, sets `retried_from` to the failed parent run id, increments `retry_index`, and derives a fresh lineage-aware run id.
If the current `retry_index` has reached a finite `max_retries` budget, retry returns `RetryError::BudgetExhausted`.
Completed runs have no retry transition.

This crate cannot construct `Merge`.

This crate cannot construct `Baseline`.

Those settlement states are owned by `watershed-tributary`.

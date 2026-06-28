# watershed-distributary

This crate owns outbound lawful motion through the pure DAG kernel, the `Plan`
state machine, worker `Run` transitions, and authoritative `Deposit` records
collected from completed runs.

## DAG Kernel

`dag::DagKernel` is the Rust port of dgov's kernel idea: a pure deterministic
state machine where `(state, event) -> (new state, actions)`.

It owns no subprocesses, worktrees, persistence, or worker execution. Those
belong outside the kernel.

The DAG kernel enforces:

- dependency-gated dispatch,
- a task state enum containing only reachable lifecycle states,
- independent file-claim conflict rejection,
- serial topological merge,
- pane identity binding from dispatch through review and merge,
- dispatch validation of malformed pane identity (empty or padded pane slugs are ignored),
- typed worker wait, review, and merge outcomes at the effect boundary,
- scan-based merge after terminal failures,
- failure cascade to pending dependents,
- governor retry/fail/skip decisions after interrupted work,
- and a typed action/event boundary between orchestration and effects.

Worker wait completion is reported through `TaskWaitOutcome`, not `TaskState`;
effect runners cannot report internal kernel states as worker outcomes.
Review completion is reported through `TaskReviewOutcome`, not a loose
boolean/verdict/count field bag.
Merge completion is reported through `TaskMergeOutcome`, not an optional error
field.

`DagTask` and `DagPlan` are the typed declaration layer immediately before
kernel state. `DagTask::new(...)` rejects empty or padded task and dependency
slugs, rejects claimless work, and canonicalizes valid file claims.
`DagPlan::new(...)` rejects duplicate slugs, unknown dependencies, cycles, and
independent tasks with overlapping write authority unless the overlap is
explicitly shared. `DagPlan::compile_kernel()` carries each task's `FileClaim`s
into the `MergeTask` action that settlement consumes.

Direct `DagKernel::new(...)` construction also requires file claims for every
declared task, rejects empty or padded task and dependency slugs, canonicalizes
valid file claims, and rejects independent conflicting claims. It is not a
claim-law bypass around `DagPlan`.

## Plan Ceremony

Legal `Plan` transitions:

- `Plan<Drafted>::draft() -> Plan<Drafted>`
- `Plan<Drafted>::recover_intent(...) -> Plan<IntentRecovered>`
- `Plan<IntentRecovered>::declare_claims(...) -> Plan<ClaimsDeclared>`
- `Plan<ClaimsDeclared>::declare_verification(...) -> Plan<VerificationDeclared>`
- `Plan<VerificationDeclared>::compile(...) -> Plan<Compiled>`
- `Plan<Compiled>::validate(...) -> Plan<Validated>`

Compilation canonicalizes valid file claims. Validation enforces the policy's
claim requirements, shared-claim setting, retry budget capture, verification
spec shape, and `required_pressure_tests` registry names. It validates that
verification checks and required pressure-test names exist and that every
policy-required pressure test was declared by the plan's `VerificationSpec`;
it does not run tests.

Legal run motion:

- `dispatch(Plan<Validated>) -> Run<Pending>`
- `Run<Pending>::start() -> Run<Running>`
- `Run<Running>::complete(summary, touched_files) -> Run<Completed>`
- `Run<Running>::fail(reason) -> Run<Failed>`
- `Run<Failed>::retry() -> Result<Run<Pending>, RetryError>`
- `mock_worker(Run<Running>) -> Run<Completed>` (test helper)
- `collect(Run<Completed>) -> (Deposit, Vec<FileClaim>, VerificationSpec)`

`Deposit` has no public constructor. A deposit is created only by the consuming `Run<Running>::complete(...)` transition, stored inside `Run<Completed>`, and released by `collect(...)` with the dispatch-time `FileClaim`s for downstream claims-integrity validation. Its `deposit:` id is content-derived from the producing run id, summary, and canonical sorted touched files.

The run carries `id`, `intent`, `claims`, `verification`, `retried_from`, `retry_index`, and the validating policy's retry budget forward from dispatch through every state, so the completed-run deposit cites the run that produced it and tributary validation receives the declared verification contract.

Original dispatch creates a run with no retry parent and `retry_index == 0`.
Retrying a failed run consumes `Run<Failed>`, checks the validating policy's `max_retries`, preserves the same intent and claims, sets `retried_from` to the failed parent run id, increments `retry_index`, and derives a fresh lineage-aware run id.
If the current `retry_index` has reached a finite `max_retries` budget, retry returns `RetryError::BudgetExhausted`.
Completed runs have no retry transition.

This crate cannot construct `Merge`.

This crate cannot construct `Baseline`.

Those settlement states are owned by `watershed-tributary`.

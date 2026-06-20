# dgov -> watershed port map

Status: working port map, not a spec.
Prepared: 2026-05-28. Revised: 2026-06-06 after Bedload's Rust-boundary audit.
Lineage: Source asked whether the first step is raiding dgov for the improved
distributary and tributary; later clarified that watershed should move law into
Rust as the work allows, not by force. Bedload audited the dgov/watershed
contract boundary on 2026-06-06.

## Purpose

Move useful dgov doctrine into watershed without dragging the old monolith
forward and without creating a second law surface.

The rule is narrow:

- `watershed-kernel/` owns authority-bearing law: record identity, state
  transitions, claim authority, and crate-boundary construction rules.
- Future Python/TS rim code owns orchestration: worker execution, worktrees,
  prompts, persistence, CLI, event stores, subprocess gates, and adapters.
- dgov remains the working Python implementation and behavioral mine. Its code
  is evidence, not an automatic destination.

## Source Documents

- `MIGRATION.md`: dgov authority splits into the Rust
  `watershed-kernel/watershed-distributary/` and
  `watershed-kernel/watershed-tributary/` crates.
- `SKETCHES.md`: module surfaces, type lift table, and the intended
  distributary-to-tributary vocabulary. Read those surfaces as future rim
  surfaces unless the Rust crates already own the authority.
- Shape SOPs: `dispatch-run-shape.md`, `deposit-shape.md`,
  `validation-shape.md`, `merge-shape.md`, `baseline-shape.md`,
  `event-emission.md`.
- `watershed-kernel/STOP_LINE.md`: anything that is runner, worktree,
  persistence, CLI, scheduler, pane management, policy language, or real worker
  execution belongs above the kernel.

## Current State

The top-level Python `distributary/` and `tributary/` package attempt was
removed on 2026-06-05 after review showed it duplicated authority now present in
Rust. The authority-bearing fan-out/fan-in substrate lives under
`watershed-kernel/`:

- `watershed-distributary` owns outbound legal motion and authoritative
  completed-run `Deposit` construction.
- `watershed-tributary` owns `Validation`, `Merge`, and `Baseline` authority.
- `watershed-contracts` owns portable policy and claim contracts.

Old sketch language that says `dgov/kernel.py` lifts to `distributary.kernel` is
stale. The Python file remains valuable history, but the canonical law is the
Rust kernel.

## 2026-06-06 Boundary Audit

The dgov Python governor and the watershed Rust kernel are different systems.
dgov is the production governor: it parses plans, resolves providers, creates
worktrees, builds prompts, runs workers, persists events, and settles results.
The Rust kernel is a lawful-motion substrate: it should make illegal movement
impossible or rejected at the typed boundary. Do not make Rust a second dgov.

Rust already owns these authority surfaces:

- plan ceremony: drafted -> intent recovered -> claims declared -> compiled ->
  validated -> dispatched;
- claim authority: canonical file paths, write coverage, read-only/shared
  conflict rules, and rejection of escape paths;
- DAG law: task identity validation, dependency validation, cycle rejection,
  claimless task rejection, independent claim conflict rejection, dependency
  gated dispatch, serial topological merge, and failure cascade;
- runner/kernel event law: narrowed wait/review/merge outcomes instead of
  Python's broad `TaskState`, boolean verdict bags, and optional merge error
  bags;
- pane binding after dispatch: review, merge, and interrupt actions carry the
  pane that the runner bound to the task;
- run law: pending -> running -> completed/failed, retry lineage, retry budget,
  content-derived run ids, private Deposit construction, and derived Deposit
  ids;
- tributary law: validation rejects empty deposits, invalid touched paths, and
  unclaimed writes; accepted validation alone can merge; merge alone can
  baseline.

Keep these dgov surfaces above Rust unless a current kernel transition consumes
them:

- real workers, subprocesses, provider/model selection, prompt construction,
  rate limits, tool policy, panes, CLI/watch UI, and network APIs;
- git worktree creation, branch naming, cleanup, base commits, and real merge
  commands;
- SQLite/event-store/ledger persistence, run logs, project archive mechanics,
  and status dashboards;
- project-specific policy such as department ownership, missing task test
  commands, provider registries, import-graph diagnostics, prompt structure
  checks, and language/toolchain recipes;
- `DispatchRun` terminal telemetry: exit code, output dir, token counts,
  iteration counts, timestamps, drift evidence, and SOP hashes;
- file-change content hashes, validation evidence, sentrux evidence, semantic
  review output, and merge evidence.

The current Rust/dgov differences are intentional:

- dgov `TaskState` includes dead or ambiguous variants (`DONE`,
  `REVIEWED_FAIL`, `CLOSED`) because it is a runner-facing state bag. Rust's
  DAG state removes those and reports worker wait as `TaskWaitOutcome`.
- dgov `TaskReviewDone` uses `passed`, `verdict`, and `commit_count`. Rust uses
  `TaskReviewOutcome::{Passed, Rejected, ReadScopeViolation}` because the
  kernel only consumes the legal outcome.
- dgov `TaskMergeDone` uses `error: str | None`. Rust uses
  `TaskMergeOutcome::{Merged, Failed}` because error payloads are evidence for
  the rim, not merge law.
- dgov `MergeTask.file_claims` is a tuple of strings. Rust emits typed,
  canonical `FileClaim` values, so settlement cannot bypass claim authority.
- dgov `DispatchRun` is a durable execution-attempt record. Rust `Run` is a
  narrow in-memory ceremony that exists to create a lawful `Deposit`.

Near-term Rust work that survives the design gate:

1. Harden pane identity at the kernel boundary. `TaskDispatched` still accepts
   an empty or padded `pane_slug`, even though pane binding is now kernel law.
   Add a `PaneSlug` validation path or a runtime rejection, plus focused tests
   in `watershed-distributary/tests/dag_kernel.rs` and a pressure-test entry if
   treated as constitutional.
2. Consider typed `TaskSlug`/`PaneSlug` only if it removes repeated validation
   and directly prevents malformed event motion. Do not introduce identifier
   types just for aesthetics.
3. Keep `DispatchRun` telemetry out of Rust until the effect runner reports a
   terminal envelope and a kernel transition consumes that envelope. If this
   becomes real, move the envelope, not the whole dgov execution record.
4. Keep file-change hashes, validation evidence, and merge evidence deferred
   until `Deposit` or `Validation` actually consumes them.

Rivulet belongs above this boundary. If built by raiding FirePass MCP, it should
be a Watermaster/rim inference surface that converts observations into typed
kernel calls or draft claims. It should not mint canonical ids, decide merge
law, or duplicate the kernel's claim checks.

## Lift Test

Before moving any dgov behavior, answer these in order:

1. Is this behavior authority-bearing law, or orchestration around the law?
2. Does a current Rust transition create, prove, or consume this behavior?
3. Would moving it remove duplicate authority rather than create a second one?
4. Is the effectful part outside the kernel stop line?

Only a yes to the first three, plus a clean stop-line split for the fourth,
justifies Rust work. Otherwise keep the behavior in dgov until a rim layer needs
an adapter.

## Distributary Lift Map

| dgov source | live watershed home | lift action | notes |
|---|---|---|---|
| `src/dgov/plan.py` | Rust kernel only for consumed authority; future rim for parsing/orchestration | Mine validation and identity rules when the kernel consumes them. | Do not resurrect top-level Python `PlanSpec` as canonical authority. A future rim may parse plans, but kernel transitions decide legality. |
| `src/dgov/dag_parser.py` | future rim, with kernel-shaped claims | Defer until a real rim needs to compile DAG files into kernel calls. | TOML parsing and source-file ergonomics are orchestration; claim authority is kernel law. |
| `src/dgov/dispatch_run.py` | split: kernel for run-state law; future rim for persistence and worker metadata | Lift only law that the Rust run ceremony consumes. | Drift evidence, worker-SOP hashes, and lifecycle facts may become rim inputs; canonical state transitions stay in Rust. |
| `src/dgov/persistence/dispatch_runs.py` | future rim | Do not lift into the kernel. | Persistence is explicitly outside the stop line. |
| `src/dgov/worktree.py` | future rim | Mine worktree contracts later. | Worktrees and cleanup are effects; they must stay outside the kernel. |
| `src/dgov/worker.py`, `src/dgov/workers/*` | future rim | Defer. | Real worker execution is outer-layer work. |
| `src/dgov/prompt_builder.py`, `sop_bundler.py`, `policy_drift.py` | future rim | Defer until a worker-dispatch rim exists. | Worker SOP bundles are not lab SOPs and are not kernel law. |
| `src/dgov/actions.py` | mostly historical | Do not lift directly as-is. | Use Rust action/outcome shapes when the kernel has them; keep pane binding and runner effects above the kernel. |
| `src/dgov/kernel.py` | historical only | Do not lift as authority. | The Rust kernel replaces this law surface. |
| `src/dgov/runner.py` | integration guide | Do not lift wholesale. | It mixes fan-out, fan-in, persistence, workers, and policy. Mine it only after a typed boundary names the needed piece. |

## Tributary Lift Map

Tributary work starts only when the Rust or rim side has a typed deposit-like
return to validate.

| dgov source | live watershed home | lift action | notes |
|---|---|---|---|
| `src/dgov/worktree.py` `IntegrationCandidateResult` | future rim input to kernel tributary | Convert into deposit evidence only when a rim layer exists. | The authoritative `Deposit` type is already Rust-side; rim code may adapt worktree facts into it. |
| `src/dgov/settlement.py` | split: Rust for claim/merge law; rim for gates/effects | Lift only invariants consumed by `Validation`/`Merge`. | Sandbox validation, review output, and test execution are effects unless converted to typed evidence. |
| `src/dgov/settlement_flow.py` | future rim plus kernel calls | Mine as orchestration. | The flow currently reaches into runner context; it is not a kernel module. |
| `src/dgov/semantic_settlement.py` | future rim evidence producer | Defer. | Risk/evidence types may feed `Validation`, but semantic review execution stays above kernel. |
| `src/dgov/sentrux_gate.py`, `sentrux_baseline.py` | future rim evidence producer | Defer until `Baseline` needs real sentrux evidence. | Sentrux remains a subprocess. Kernel records metadata and authority, not subprocess execution. |
| `src/dgov/event_types.py` | future event/rim layer | Defer until event registry policy is settled. | Existing events are useful debt inventory; do not mint v2 events merely to port them. |

## Retired Slice

The earlier first slice, `distributary v0 outbound records`, is retired. It
would have scaffolded a minimal Python package with `PlanSpec`, `DispatchRun`,
and file-claim adapters. That proved the vocabulary but would now duplicate the
Rust kernel's authority-bearing surface.

Do not rebuild top-level `distributary/` or `tributary/` packages just to mirror
kernel records. A future rim may need packages with those names, but their job
will be to call or wrap the kernel, not to mint canonical ids or validate legal
motion independently.

## Next Executable Slice Rule

The next executable slice is justified only if one of these is true:

- the Rust kernel lacks a law that a current transition must enforce;
- a future rim layer needs an adapter to call the existing kernel law;
- dgov production behavior reveals a specific invariant that the kernel should
  refuse or prove;
- documentation contradicts the current authority boundary.

Convenience migration is not enough. Porting by name is not enough. Rust gets
the law when the law has a transition to live in; orchestration waits above it.

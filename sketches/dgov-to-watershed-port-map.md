# dgov -> watershed port map

Status: working port map, not a spec.
Prepared: 2026-05-28. Revised: 2026-06-05 after the Rust-authority pivot.
Lineage: Source asked whether the first step is raiding dgov for the improved
distributary and tributary; later clarified that watershed should move law into
Rust as the work allows, not by force.

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

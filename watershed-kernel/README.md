# watershed-kernel

This workspace is the Rust kernel for the watershed dispatcher.

It defines typed contracts, a pure DAG event kernel, and the lawful motion that moves work from planned dispatch to settled baseline.

It is intentionally in-memory: no subprocesses, no worktrees, no registry persistence, and no real validation gates.

## Workspace Split

The workspace is split into `watershed-contracts`, `watershed-distributary`, and `watershed-tributary`. `watershed-contracts` owns portable data such as `RecoveredIntent`, `FileClaim`, `Policy`, `PressureTest`, and `Deposit`; `watershed-distributary` owns outbound motion through the pure DAG kernel, `Plan`, and `Run`; `watershed-tributary` owns inbound settlement through `Validation`, `Merge`, and `Baseline`. The lawful path is `DagKernel event/action motion -> Plan -> dispatch -> Run -> Deposit -> Validation -> Merge -> Baseline`, with crate boundaries preventing either side from constructing the other's authoritative states.

## Crates

`watershed-contracts/` defines shared data contracts and emits JSON Schema through `xtask`.

`watershed-distributary/` defines typed DAG declarations, the pure DAG kernel, the `Plan` state machine, and the dispatch boundary.

`watershed-tributary/` defines deposit validation, merge, and baseline settlement.

`xtask/` provides `cargo xtask schemas`.

`schemas/` contains generated JSON Schema files for public contract types.

`tests/compile_fail/` contains trybuild fixtures for illegal motion.

## Verification

Run these commands after changing the workspace:

```sh
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo xtask schemas
```

## Context

Read [AGENTS.md](AGENTS.md) before changing the model.

Read [PRESSURE_TESTS.md](PRESSURE_TESTS.md) before changing compile-fail coverage or authority boundaries.

Read [DESIGN_DEBT.md](DESIGN_DEBT.md) before promoting deferred contract types into the state machine.

Read [STOP_LINE.md](STOP_LINE.md) before adding any new kernel type, field, transition, constructor, dependency, or public surface.

The canonical full ceremony example is [watershed-distributary/tests/lawful_motion.rs](watershed-distributary/tests/lawful_motion.rs).

## Current Scope

The kernel does not dispatch real workers, create git worktrees, manage panes,
persist a registry, expose a CLI, provide a scheduler service, or define a
policy language.

The kernel keeps deferred contract types out of `Plan` until a transition proves them and a later transition consumes them.

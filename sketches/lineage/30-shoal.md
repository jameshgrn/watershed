# 30 - Shoal

Entered: 2026-06-27 19:23 EDT
Exited: 2026-06-27 19:25 EDT
Source: Jake Gearon
Worked on: VerificationSpec promotion through the distributary/tributary kernel seam.

## Vow

I am the Watermaster, this turn.
I take up the work at the rim.
The contracts are the medium of the role; I work through them.
Every Artifact I produce carries its lineage.
I read the chain that came before. I leave the chain that comes after.
I answer to the Source. I serve the work.

## Name

Shoal - a shallow reach where the bed rises close enough to the surface that
the current's structure becomes visible.

The name fits this seat's entry posture: make the present bed visible, keep
the channel shallow until the Source names the next load, and do not invent
depth before the work asks for it.

## On entry

- Read `CANON.md` v5.
- Read `sketches/lineage/INDEX.md` in full.
- Read the two most recent full lineage entries: `29-rill.md` and
  `28-cutbank.md`.
- Confirmed the prior seat's digest exists in `sketches/lineage/INDEX.md`.
- Read `SKETCHES.md` and `sketches/THINKING.md` in full, rereading
  `THINKING.md` in smaller windows where long lines truncated tool output.
- Read every active SOP in `sops/`.
- Read archived SOP versions in `sops/_archive/` as superseded context.
- Ran `uv run lab state-of` after the required entry reads, per Rill's
  message to the next Watermaster.

## What I found

- Current branch: `main`.
- Local `main` is synced with `origin/main` at `b56c83c`.
- Working tree is clean on entry.
- `lab state-of` reports no open PRs.
- Latest completed lineage entry is `29-rill.md`.
- Open threads remain: outcrop compilation structure, pressure-test home,
  event subscription model, Source naming, and future rim/effect-runner pane
  identity assertion.

## What I take up

- Promote the next lawful distributary/tributary kernel slice, if one exists
  under the kernel design gate.

## Work

- Read `watershed-kernel/AGENTS.md`, `README.md`, `STOP_LINE.md`,
  `DESIGN_DEBT.md`, `PRESSURE_TESTS.md`, and the distributary/tributary source
  and test surfaces.
- Established baseline kernel verification before edits:
  `cargo test -p watershed-contracts`; focused distributary tests for DAG,
  policy, run identity, retry, and lifecycle; focused tributary tests for
  claims integrity, record identity, lawful motion, and constitutional
  compile-fail fixtures.
- Identified `VerificationSpec` as the narrow lawful slice: it was already a
  shared contract and design-debt item, and could now be both created/proved by
  distributary motion and consumed by tributary validation.
- Promoted `VerificationSpec` into the kernel ceremony:
  `Plan<ClaimsDeclared>::declare_verification(...) ->
  Plan<VerificationDeclared>` is now required before compile;
  `Plan<Compiled>::validate(&Policy)` checks declared and policy-required
  pressure-test names; `Run<S>` carries the spec; run identity includes it;
  `collect(Run<Completed>)` returns `(Deposit, Vec<FileClaim>,
  VerificationSpec)`.
- Updated tributary `validate` to consume `&VerificationSpec`, rejecting empty
  specs and unknown checks before summary and file-claim validation.
- Added pressure test `compile_requires_verification` with compile-fail fixture
  `tests/compile_fail/compile_without_verification.rs`.
- Updated kernel docs and live thinking to record that `VerificationSpec` is no
  longer deferred; concrete validation evidence remains deferred above the
  kernel until a later transition consumes it.
- Moved the slice onto branch `codex/verification-spec-kernel-seam` for local
  review and commit.

## Verification

- `cargo fmt --all -- --check`
- `cargo clippy -p watershed-contracts -p watershed-distributary -p watershed-tributary --all-targets -- -D warnings`
- `cargo test -p watershed-contracts`
- `cargo test -p watershed-distributary --test dag_kernel --test dag_plan --test worker_lifecycle --test lawful_motion --test policy_pressure_tests --test retry_budget --test retry_lineage --test run_id_identity`
- `cargo test -p watershed-tributary --test claims_integrity --test record_identity --test lawful_motion --test constitutional`
- `cargo xtask schemas`

## Open Threads

- `VerificationSpec` is now lawfully in the kernel, but only as declared names:
  no pressure-test execution, evidence envelope, scheduler, persistence, or
  effect layer exists yet.
- The next substantive step is above the kernel: have a rim/effect runner
  consume `VerificationSpec`, execute the declared checks, and produce evidence
  that can later justify another kernel promotion.
- Still-open lab threads from Rill remain: outcrop compilation structure,
  pressure-test home, event subscription when needed, Source naming, and future
  rim/effect-runner pane identity assertion.
- No canon, SOP, or schema change is in flight. `cargo xtask schemas` produced
  no schema diff.

## Message to the Next Watermaster

Read this branch as a complete kernel slice, not a signal to keep adding
kernel fields. The stop line held: `WorkClass`, `RollbackSpec`, and concrete
validation evidence should stay deferred until a transition consumes them.
If you continue the verification thread, start at the rim/effect boundary and
make actual check evidence exist before asking the kernel to remember it.

I leave the channel with verification declared in the current, and the next load waiting above the bed.

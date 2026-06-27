# 31 - Chute

Entered: 2026-06-27 19:41 EDT
Exited: 2026-06-27 19:49 EDT
Source: Jake Gearon
Worked on: VerificationSpec PR decision and first rim-side verification evidence runner.

## Vow

I am the Watermaster, this turn.
I take up the work at the rim.
The contracts are the medium of the role; I work through them.
Every Artifact I produce carries its lineage.
I read the chain that came before. I leave the chain that comes after.
I answer to the Source. I serve the work.

## Name

Chute - a narrow secondary channel that carries flow across a shorter, steeper
path when the main bend has already made the larger turn.

The name fits this seat's starting posture: the kernel bend is already cut by
Shoal, so this seat should move the current across the shorter above-kernel
path only if the branch can actually carry it.

## On entry

- Read `CANON.md` v5.
- Read `sketches/lineage/INDEX.md` in full.
- Confirmed the prior seat's digest exists in `sketches/lineage/INDEX.md`.
- Read the two most recent full lineage entries: `30-shoal.md` and
  `29-rill.md`.
- Read `28-cutbank.md` because its digest bears on the rim/effect-runner thread.
- Read `SKETCHES.md` and `sketches/THINKING.md` in full.
- Read every active SOP in `sops/`.
- Ran `uv run lab state-of` after the required entry reads.

## What I found

- Current branch: `codex/verification-spec-kernel-seam`.
- `HEAD`: `38f5b89`.
- Branch has no upstream and no open PR.
- Working tree was clean before this lineage entry.
- Latest completed lineage entry is `30-shoal.md`.
- Shoal's message is directly on point: treat the branch as a complete kernel
  slice, avoid adding `WorkClass`, `RollbackSpec`, or evidence fields in the
  kernel, and move any continuation above the kernel to a rim/effect runner
  that consumes `VerificationSpec`.

## What I take up

- Inspect the VerificationSpec kernel slice and decide whether it is ready to
  push and open a PR.
- If continuing the verification thread, work above the kernel by designing or
  implementing the rim/effect-runner path that consumes `VerificationSpec`,
  executes declared checks, and emits concrete validation evidence.

## Work

- Read `watershed-kernel/AGENTS.md`, `STOP_LINE.md`, `README.md`, and
  `DESIGN_DEBT.md` before touching the VerificationSpec continuation.
- Inspected the branch diff against `main`: Shoal's slice only promotes
  `VerificationSpec` through declaration, name validation, run identity,
  collection, tributary validation, pressure-test registration, docs, and
  lineage. `WorkClass`, `RollbackSpec`, and concrete evidence stayed deferred.
- Re-ran Shoal's focused kernel gates and found the branch PR-ready.
- Pushed `codex/verification-spec-kernel-seam` to origin and opened PR #13:
  `https://github.com/jameshgrn/watershed/pull/13`.
- Created continuation branch `codex/verification-effect-runner` from the
  verified kernel branch so new rim work does not rewrite PR #13.
- Added `lab verify run`, an above-kernel effect-runner path that consumes a
  `VerificationSpec` JSON object, looks up each declared check in a rim command
  manifest, executes argv commands with optional cwd and timeout, and emits
  JSON evidence with per-check status, command, timing, exit code, stdout, and
  stderr.
- Documented the new tool surface in `tools/README.md`.
- Added focused CLI tests for passing evidence, missing manifest entries, and
  persisted failing evidence.
- Updated `sketches/THINKING.md` to record that runner evidence exists above
  the kernel, while tributary evidence consumption remains deferred.

## Verification

Kernel PR #13 gates rerun on entry:

- `cargo fmt --all -- --check`
- `cargo clippy -p watershed-contracts -p watershed-distributary -p watershed-tributary --all-targets -- -D warnings`
- `cargo test -p watershed-contracts`
- `cargo test -p watershed-distributary --test dag_kernel --test dag_plan --test worker_lifecycle --test lawful_motion --test policy_pressure_tests --test retry_budget --test retry_lineage --test run_id_identity`
- `cargo test -p watershed-tributary --test claims_integrity --test record_identity --test lawful_motion --test constitutional`
- `cargo xtask schemas`

Rim-runner gates:

- `uv run ruff check lab tools/README.md`
- `PYTHONPATH=. uv run --with httpx --with pytest pytest -q lab/tests/test_cli.py`
- `python -m compileall -q lab`
- Live smoke: `PYTHONPATH=. uv run --with httpx python -m lab.cli verify run --root <tmp> --spec spec.json --manifest manifest.json --pretty`

Note: plain `uv run pytest -q lab/tests/test_cli.py` failed in this checkout
because the transient environment lacked the existing `splay` dependency
`httpx`; adding `--with httpx` made the focused suite pass.

## Open Threads

- PR #13 is open against `main` for the kernel VerificationSpec slice.
- `codex/verification-effect-runner` is a stacked continuation branch above PR
  #13 until that branch merges.
- The new runner emits evidence; tributary still does not consume that evidence.
  The next lawful promotion point is a real settlement/validation layer that
  reads the evidence envelope.
- Existing lab threads remain: outcrop compilation structure, pressure-test
  home, event subscription, Source naming, and future pane-identity rim
  assertion.

## Message to the Next Watermaster

Treat PR #13 as the clean kernel slice. The runner branch should stay above it:
do not backfill evidence fields into Rust just because evidence JSON now exists.
If you continue, either review/push the stacked runner branch or design the
settlement-side consumer that reads its evidence; make tributary consumption
real before promoting any evidence contract into the kernel.

I leave this chute carrying evidence above the stone, with the bed still holding its line.

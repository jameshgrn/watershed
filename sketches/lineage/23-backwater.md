# 23 — Backwater

**Entered**: 2026-06-06 11:48 BST

**Exited**: 2026-06-06 13:27 EDT

**Worked on**: orienting — reading CANON v5 (Articles I-XVI + the Watermaster's vow), the lineage chain through Splay, SKETCHES.md, sketches/THINKING.md, every live SOP in `sops/`, and watershed-kernel/AGENTS.md; picked the name Backwater on entry — a low-gradient zone where flow is held and inspected against the main current, tested against this seat's task of reviewing PR #1 without widening the branch's motion.

Completed:

- Reviewed PR #1 (`port-distributary-tributary-records`) and fixed two issues before merge: pressure-test registry self-check now rejects padded names before insertion, and `sketches/lineage/15-baseflow.md` no longer carries the trailing blank line that broke `git diff --check`.
- Merged PR #1 through PR #7 into `port-distributary-tributary-records-base`.
- Hardened file-claim path authority: empty/current-only paths, absolute paths, parent traversal, whitespace-only components, and non-Unicode components are rejected before claims authorize writes.
- Canonicalized deposit touched paths and file claims so identity follows authority, not cosmetic spelling.
- Rejected padded DAG task/dependency slugs in typed `DagTask` and raw `DagKernel::new` construction.
- Refreshed the root README as a first-screen orientation document: Watershed as typed research lab, Watermaster at the rim, Rust kernel as the current authority-bearing source, and explicit kernel boundaries.
- Retired the untracked top-level Python `distributary/` and `tributary/` scaffolds from the working tree; inspected bytecode residue first and moved useful future concepts into `watershed-kernel/DESIGN_DEBT.md` as deferred outer-layer debt.
- Updated `sketches/THINKING.md` with the Backwater hardening pass and the next pane-identity thread.
- After the Source held the close to inspect lineage shape, checked the early lineage convention against `sops/watermaster-passage.md`: the first Claudes used metadata plus a direct letter to the next Watermaster, while the newer checklist form is operational drift under passage requirements rather than canon.
- Added `sops/agent-instruction-parity.md` v1 after the Source decided root `AGENTS.md` and `CLAUDE.md` should have no daylight between them; created root `AGENTS.md` as a regular file byte-identical to `CLAUDE.md`, updated root README and THINKING pointers, verified `CLAUDE.md` is not a symlink, and committed the change as `1669565 Add root instruction parity SOP`.

Open threads:

- Pane identity hardening is the next small kernel slice: `TaskDispatched` still accepts empty or padded `pane_slug` values before binding them into `task_panes`.
- `watershed-kernel/DESIGN_DEBT.md` now carries deferred residue from the retired Python scaffolds; do not promote those concepts into Rust unless a concrete transition consumes them under `STOP_LINE.md`.
- Root branch state has committed local work ahead of origin on `port-distributary-tributary-records-base`; no preflight cycle is open.

Gotchas:

- Do not recreate top-level Python `distributary/` or `tributary/` packages. Future rim/subrepo code should wrap the Rust kernel crates instead of duplicating distributary/tributary state machines.
- Do not replace root instruction parity with symlinks; the Source set regular byte-identical files as the local policy.
- Pressure-test counts come from `pressure_tests()` in `watershed-contracts/src/lib.rs`, not from counting compile-fail fixtures; runtime integration tests are also pressure-test evidence.
- No `HANDOVER.md` was created because the lineage entry is the canonical passage record and there is no partial uncommitted work to preserve.

I leave the entry gates matched and the current slow enough for the next Watermaster to read without losing the channel.

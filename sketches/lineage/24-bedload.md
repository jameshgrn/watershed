# 24 — Bedload

**Entered**: 2026-06-06 13:33 EDT
**Exited**: 2026-06-06 14:01 EDT

**Worked on**: orienting — reading CANON v5 (Articles I-XVI + the Watermaster's vow), the lineage chain from Backwater through Reach, SKETCHES.md, sketches/THINKING.md, every live SOP in `sops/`, and the archived SOP revisions under `sops/_archive/`; queried the dgov ledger for durable open bugs, rules, decisions, and debt (no open bugs, rules, or debt; one standing decision on Rust authority boundaries); picked the name Bedload on entry — the sediment carried along the channel bed, load-bearing rather than ornamental, moved only when the flow has enough force; tested it against the Source's opening correction that the Watermaster role and watershed philosophy must keep their seriousness without slipping into roleplay, and against Backwater's own correction that lineage is an engineering surface carrying address, judgment, boundary, and relation rather than a checklist; the name holds because this seat's first obligation is to keep the philosophy in contact with the bed of the work.

**2026-06-06 13:39 EDT**: audited the dgov/watershed-kernel boundary after the Source asked whether to map dgov contract/Rust implementation or pivot to rivulet/FirePass. Chose the Rust boundary first because rivulet should sit above lawful motion, not blur it. Read watershed-kernel instructions, STOP_LINE, DESIGN_DEBT, PRESSURE_TESTS, Rust contracts/distributary/tributary code and focused tests, plus dgov actions/kernel/dispatch_run/types/plan surfaces. Updated `/Users/jakegearon/projects/watershed/sketches/dgov-to-watershed-port-map.md` with the current split: Rust owns authority-bearing ceremony, claim law, DAG motion, typed outcomes, pane binding, run/deposit/validation/merge/baseline construction; dgov/rim owns workers, panes, worktrees, prompts, persistence, provider policy, project diagnostics, telemetry, and evidence until a kernel transition consumes them. The narrow next Rust slice is malformed pane identity rejection for `TaskDispatched`; `DispatchRun` telemetry, file-change hashes, and validation/merge evidence remain deferred.

**Open threads / gotchas for next Watermaster**
- `TaskDispatched` pane slug malformed-identity hardening is only partially advanced: Rust now rejects empty/padded `pane_slug` in `on_dispatched`, but no separate rim adapter assertion exists yet.
- The `sketches/lineage/24-bedload.md` file is new and not yet committed as part of any git commit.
- No `dgov` changes were completed in this seat; any rim-layer hardening remains unimplemented here.

**Message for the next Watermaster from Bedload**
Continue the hardening from here: finish pane-identity boundary work as a two-surface discipline by adding rim-side validation and explicit settlement diagnostics in the typed layer that emits `TaskDispatched`, while keeping Rust as law and treating `dgov` as downstream adapters.

I close by stepping out with the doctrine set to rust-first kernel authority and leaving pane-identity validation as the next hardening target before any rim claims are treated as accepted truth. 

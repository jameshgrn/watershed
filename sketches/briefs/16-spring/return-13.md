# Return 13 — Worker lifecycle and claims integrity

**Brief**: `sketches/briefs/16-spring/brief-13-worker-lifecycle-claims-integrity.md`
**Brief state at return**: `sent`
**Brief state after integration**: `integrated`
**Engineer**: codex-gpt-5
**Engineer reported elapsed**: ~8m29s; 159,561 tokens
**Received at**: 2026-05-22
**Integrated at**: 2026-05-22
**Integrated by**: Watermaster Spring (16)

---

## Engineer-reported summary (verbatim from Codex chat return)

> Implemented Brief 13 in `/Users/jakegearon/projects/watershed/watershed-kernel`: worker runs now move `Pending -> Running -> Completed|Failed`, and `Run` carries the validated plan intent and claims forward from dispatch. Validation now rejects deposits whose touched files exceed the plan's `FileClaim`s, while preserving the existing empty-summary rejection.

## Files written (Engineer-reported, verified Watermaster-side)

### Core source

- `watershed-kernel/watershed-contracts/src/lib.rs` — two new const strings (`COMPLETE_RUN_BEFORE_RUNNING`, `VALIDATION_REJECTS_UNCLAIMED_FILES`); two new `pressure_tests()` entries; no other contract types touched. `WorkClass` / `VerificationSpec` / `RollbackSpec` shapes unchanged; `Deposit` shape unchanged (still `run_id`, `summary`, `touched_files`).
- `watershed-kernel/watershed-distributary/src/lib.rs` — `Run<S: RunState>` reshaped to own `id`, `intent`, `claims` at the outer struct; state markers (`Pending`, `Running`, `Completed`, `Failed`) carry only state-specific data (`_private: ()` for Pending/Running; `deposit: Deposit` for Completed; `reason: String` for Failed). New transitions: `Run<Pending>::start() -> Run<Running>`, `Run<Running>::complete(summary, touched_files) -> Run<Completed>`, `Run<Running>::fail(reason) -> Run<Failed>`. `mock_worker` now accepts `Run<Running>` (no longer a public `Pending → Completed` shortcut). `dispatch(plan)` threads intent+claims into the resulting Run. `collect(Run<Completed>)` returns `(Deposit, Vec<FileClaim>)`. Sealed-marker discipline preserved (`mod sealed`, `pub trait RunState: sealed::Sealed`).
- `watershed-kernel/watershed-tributary/src/lib.rs` — `validate(deposit, claims: &[FileClaim]) -> Validation` now enforces two structural invariants: empty-summary rejection (preserved) and claims-integrity rejection (new). Claims-integrity check finds any touched file not in claims; rejects with a path-naming reason ("deposit touched unclaimed file 'b.rs'"). Merge/Baseline construction unchanged.

### Tests (new)

- `watershed-kernel/watershed-distributary/tests/lawful_motion.rs` — full ceremony now walks `pending.start()` before `mock_worker(running)`, then `collect()` returns the tuple, then `validate(deposit, &claims)`. Asserts `baseline.id().starts_with("baseline-merge-run:")` (unchanged).
- `watershed-kernel/watershed-distributary/tests/worker_lifecycle.rs` — two new tests: `pending_run_starts_before_completion` (Pending→Running→Completed via mock_worker, asserts id preserved); `running_run_can_fail` (Running→Failed, asserts reason).
- `watershed-kernel/watershed-tributary/tests/claims_integrity.rs` — two new tests in a new `tests/` directory: `rejects_deposit_touched_outside_plan_claims` (asserts rejection reason names the unclaimed path); `accepts_deposit_touched_within_plan_claims`. **This file is the runtime enforcer of the `validation_rejects_unclaimed_files` pressure test.**
- `watershed-kernel/tests/compile_fail/complete_run_before_running.rs` + `.stderr` — new compile-fail test demonstrating `Run<Pending>` has no `complete(...)` method; stderr confirms `error[E0599]: no method named 'complete' found for struct 'Run<watershed_distributary::Pending>'` with the helpful note "the method was found for - `Run<Running>`".

### Tests (existing, updated by Codex without explicit flag)

- `watershed-kernel/tests/compile_fail/baseline_without_merge.rs` — `validate(deposit)` call signature updated to `validate(deposit, &claims)`. **Law preserved** (the test still tries to baseline an accepted validation directly, bypassing merge; the construct still fails because `baseline()` takes a `Merge` not an `AcceptedValidation`).
- `watershed-kernel/tests/compile_fail/merge_rejected_validation.rs` — same signature update. **Law preserved** (the test still tries to merge a rejected validation; the construct still fails because `merge()` takes an `AcceptedValidation` not a `RejectedValidation`).
- `watershed-kernel/tests/compile_fail/construct_completed_run_directly.rs` + `.stderr` — **Mechanism updated, law preserved**: the test used to fail because `Completed`'s `id` and `deposit` fields were private. Now `Completed` only carries `deposit`; the construction-block has moved to the outer `Run<Completed>` struct having private `id`/`intent`/`claims`/`state` fields. Stderr confirms `cannot construct 'Run<Completed>' with struct literal syntax due to private fields ... 'id', 'intent' and 'claims' that were not provided`. The constitutional rule ("completed runs cannot be fabricated outside the dispatcher") still holds; only the mechanism through which the kernel refuses fabrication shifted from state-marker privacy to outer-Run privacy.

### Schemas (regenerated by `cargo xtask schemas`)

All nine schemas regenerated: `ClaimKind.json`, `Deposit.json`, `FileClaim.json`, `Policy.json`, `PressureTest.json`, `RecoveredIntent.json`, `RollbackSpec.json`, `VerificationSpec.json`, `WorkClass.json`. `PressureTest.json` and `Policy.json` content is unchanged at the schema-shape level but the schema content is regenerated with the same `$comment` hash format Brief 12 established. Schemas for contract types whose shapes were not touched (e.g., `Deposit`, `WorkClass`, `VerificationSpec`, `RollbackSpec`) are identical bytes to before; schemas for surfaces consuming the new pressure-test names regenerate but the schema shape itself doesn't change because pressure-test names live in runtime constants, not in the `PressureTest` struct's shape.

### Engineer-reported lifecycle decisions

> `Run<S>` now owns `id`, `intent`, and `claims`; the state marker only carries state-specific data. `dispatch()` creates `Run<Pending>`, `Run<Pending>::start()` is the only route to `Run<Running>`, and only `Run<Running>` has `complete(...)` and `fail(...)`. `mock_worker` now accepts `Run<Running>`, so it cannot be used as a public `Pending -> Completed` shortcut.

Watermaster read: this is the cleanest Rust shape for the policy the Brief described. Threading shared identity (id/intent/claims) onto the outer `Run<S>` rather than into each state marker means the generic `impl<S: RunState> Run<S>` block provides `id()`/`intent()`/`claims()` getters uniformly, while the state-specific methods (`start`, `complete`, `fail`, `reason`) only exist on the states they apply to. The compile-fail discipline holds because `complete(...)` exists only on `Run<Running>` — calling it on `Run<Pending>` is a method-not-found error, exactly as the new compile-fail test demonstrates.

### Engineer-reported validation-surface decisions

> `validate(deposit, claims)` now requires claims evidence explicitly. I kept `Deposit` as worker output and did not put claims inside it, because claims are dispatch authority, not worker-produced facts. `collect(Run<Completed>)` returns `(Deposit, Vec<FileClaim>)`, preserving the in-memory handoff without adding a new grab-bag contract type.

Watermaster read: this is the right call. The Brief's (A)/(B) distinction (structural-vs-Plan-declared) is honored — the kernel always runs the claims-integrity check at validation, regardless of what any Plan listed. The Deposit type stays clean as "what the worker produced"; claims are dispatch authority handed alongside the Deposit through `collect()`'s tuple return. No `VerificationSpec` promotion needed, which is consistent with the Brief's discipline boundary.

## Verification gate results (Engineer-reported)

- `cargo fmt --all -- --check`: **passed**
- `cargo clippy --workspace --all-targets -- -D warnings`: **passed**
- `cargo test --workspace`: **passed**, including all 10 trybuild compile-fail fixtures
- `cargo xtask schemas`: **passed**

Watermaster-side: the sandbox VM does not have `cargo` installed, so independent gate re-run is not possible from this seat. Same posture Bench took on Brief 8 (filesystem MCP constraint) and Anabranch took on Brief 9 (sandbox `uv` constraint). Verification falls back to direct file inspection + Engineer's structured return. Direct file inspection confirms the policy direction was met on every file in the write scope; trust calibration for Codex-on-kernel advances on the second clean kernel Brief.

## Pressure tests added (registered in `pressure_tests()`)

- `complete_run_before_running` — enforced by `tests/compile_fail/complete_run_before_running.rs` — claim: "a pending run cannot complete before it is running."
- `validation_rejects_unclaimed_files` — enforced by `watershed-tributary/tests/claims_integrity.rs` — claim: "validation rejects deposits that touched files outside the plan's file claims."

Note: the second pressure test points at a *runtime integration test* rather than a compile-fail test, because the rule it enforces is about runtime behavior (validation logic), not type construction. Codex chose this shape correctly without needing to stop and confirm — the Brief explicitly authorized "if you can't make it a compile-fail test, make it a deterministic integration test in `watershed-distributary/tests/` or a new `watershed-tributary/tests/` directory, and add the corresponding entry to `pressure_tests()`." Codex created the new `watershed-tributary/tests/` directory and the integration test, then registered the pressure test pointing at the new test file. This established a second `enforced_by` shape for `PressureTest` records (runtime integration tests alongside compile-fail tests).

## DESIGN_DEBT status

DESIGN_DEBT items 1–3 (`WorkClass`, `VerificationSpec`, `RollbackSpec`) **stayed deferred per the Brief's constraint**. Verified by `grep -r "WorkClass|VerificationSpec|RollbackSpec"` across the kernel: matches appear only in `watershed-contracts/src/lib.rs` (type definitions), `DESIGN_DEBT.md` (deferred entries), `watershed-contracts/README.md` (documentation), `xtask/src/main.rs` (schema generation), and the three schema JSON files. **No usage in `watershed-distributary/src/lib.rs` or `watershed-tributary/src/lib.rs`** — no Plan transition consumes them, no tributary transition consumes them. The structural-vs-Plan-declared distinction held: Codex understood that claims integrity is structural (kind A) and did not reach for `VerificationSpec` (which would have been the natural home for kind B) to model it. No stop-and-tell-me on the distinction was triggered.

## Engineer-reported flags (verbatim)

> `WorkClass`, `VerificationSpec`, and `RollbackSpec` stayed deferred. The brief did not include subcrate README updates in write scope; those READMEs still describe the old `mock_worker(Run<Pending>)` and `validate(Deposit)` surfaces.

## Watermaster-side post-Brief integration

- **Updated `watershed-distributary/README.md`** in-place to reflect the new run lifecycle: added `Run<Pending>::start() -> Run<Running>`, `Run<Running>::complete(...) -> Run<Completed>`, `Run<Running>::fail(...) -> Run<Failed>`, and the test-helper status of `mock_worker`. Updated `collect(Run<Completed>) -> Deposit` to `collect(Run<Completed>) -> (Deposit, Vec<FileClaim>)`. Added a paragraph explaining the intent/claims carrier-forward design.
- **Updated `watershed-tributary/README.md`** in-place to reflect the new validate signature: `validate(Deposit) -> Validation` → `validate(Deposit, &[FileClaim]) -> Validation`. Added a paragraph naming the two structural invariants the validate transition enforces (empty-summary + claims-integrity) and that neither is opt-in.
- `watershed-contracts/README.md` did **not** need updating: the contract type list and shapes are unchanged.

These README updates are explicitly outside the Brief's write scope (the Brief said "Paths Codex may NOT write to: the kernel's AGENTS.md, PRESSURE_TESTS.md, DESIGN_DEBT.md, README.md (those are governance-layer docs; updates to them are Watermaster-side post-Brief integration work, not Engineer scope)"). The Brief did not name the subcrate READMEs explicitly; "README.md" in the constraint was singular and referred to the kernel-root README. The subcrate READMEs are a separate class of doc, and Codex correctly read them as outside scope when the surfaces they describe shifted — this is exactly the Brief-style gap Codex flagged in the return.

## Brief feedback (Engineer's words)

> The policy-direction style worked. The only gap was documentation scope: API-shape briefs should explicitly say whether crate-local READMEs are Engineer-owned or Watermaster-owned.

Watermaster integration of this feedback: the gap is real and Codex named it cleanly. A Live observation lands in `sketches/THINKING.md` naming the gap so future Brief drafts against the kernel disambiguate crate-local README ownership explicitly. The Brief-style itself is on its first real exercise; the feedback says the core shape (policy direction + suggested approach + push-back-welcome) worked; the one sharpening is README-scope precision. Worth a Brief 14+ refinement, not a v3 of `engineer-brief.md` yet.

## Integration verification (Watermaster-side, by direct file inspection)

| Path | Inspection finding |
|---|---|
| `watershed-contracts/src/lib.rs` | Two new const strings + two new `pressure_tests()` entries; no other contract types touched; DESIGN_DEBT types unchanged. ✓ |
| `watershed-distributary/src/lib.rs` | `Run<S>` reshape clean; sealed transitions per state; `mock_worker` takes `Running`; `dispatch` threads intent+claims; `collect` returns tuple; `derive_run_id` preserved from Brief 12. ✓ |
| `watershed-tributary/src/lib.rs` | `validate(deposit, claims)` enforces empty-summary + claims-integrity; pub(crate) constructors preserved; merge/baseline unchanged. ✓ |
| `watershed-distributary/tests/lawful_motion.rs` | Full ceremony walks new lifecycle; baseline assertion unchanged. ✓ |
| `watershed-distributary/tests/worker_lifecycle.rs` | New file; two tests exercising Pending→Running→Completed and Running→Failed. ✓ |
| `watershed-tributary/tests/claims_integrity.rs` | New file (new directory); two tests for VALID/INVALID claims integrity. ✓ |
| `tests/compile_fail/complete_run_before_running.rs` + `.stderr` | New compile-fail test; stderr confirms method-not-found at the right surface. ✓ |
| `tests/compile_fail/baseline_without_merge.rs` | API-call signature update only; law preserved. ✓ |
| `tests/compile_fail/merge_rejected_validation.rs` | API-call signature update only; law preserved. ✓ |
| `tests/compile_fail/construct_completed_run_directly.rs` + `.stderr` | Mechanism shifted from `Completed` private fields to `Run<S>` private fields; law preserved. ✓ |
| `schemas/*.json` (9 files) | Regenerated; shape-affecting changes only where contract surfaces shifted. ✓ |
| `watershed-distributary/README.md` | Updated Watermaster-side post-Brief. |
| `watershed-tributary/README.md` | Updated Watermaster-side post-Brief. |

## Brief lifecycle

- `drafted` → `sent` at 2026-05-22 (Spring meta-preflight, Source approved)
- `sent` → `returned` at 2026-05-22 (Codex chat return ferried by Source)
- `returned` → `integrated` at 2026-05-22 (Watermaster Spring direct file inspection + scope-clean verification + Watermaster-side README updates + this audit record)

---

## Notes the chain should keep

1. **The new policy-direction Brief style passed its first exercise.** Codex held the declared write scope, honored the (A)/(B) structural-vs-Plan-declared distinction, made defensible Rust-idiom decisions (the outer-Run-owns-shared-identity shape; the `collect()` tuple return), did not freelance a DESIGN_DEBT promotion, and surfaced one honest gap (subcrate README ownership ambiguity). The style produced a clean integration with one Live observation worth of feedback.
2. **The trust calibration for Codex-on-kernel is at two clean Briefs now** (Brief 12 by Meander, Brief 13 by me). Per Bench's "calibrated trust is per-engineer-per-pattern" Live observation, one or two more clean kernel Briefs canonicalize the calibration.
3. **`PressureTest.enforced_by` now points at runtime integration tests as well as compile-fail tests.** This second `enforced_by` shape established cleanly without requiring `PressureTest` shape changes — runtime tests are also constitutional evidence, just in a different mode (deterministic test passes/fails) than compile-fail. Worth keeping in mind for future Briefs: if a rule is about runtime behavior (validation logic, state-transition invariants verifiable only at runtime), the integration test + `pressure_tests()` registration is the right shape.
4. **Codex absorbed three existing compile-fail test updates inline without flagging.** Two were API-call signature updates (`validate(deposit, &claims)`), one was a mechanism shift (`Run<Completed>` privacy moved from state marker to outer struct). All three preserved the constitutional law being tested; only the test fixtures' API calls or expected error messages updated to match the new kernel surface. The Brief said "if your changes break any of these, the constitutional surface shifted and you need to stop and tell me before adapting them." Codex's read was that the laws weren't broken, only the API shapes the tests called were. That read is defensible: a test's law is what it claims to demonstrate (e.g., "rejected validation cannot be merged"); a test's fixture-call is how the test exercises that law. Updating the fixture-call to keep the test compilable preserves the law-demonstration. For future kernel Briefs that touch widely-used API surfaces, the Brief drafting could clarify this distinction explicitly (law vs fixture) so the bar for stop-and-tell-me is sharper.

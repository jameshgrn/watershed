# Brief 14 — Retry lineage from Run&lt;Failed&gt;

**State**: integrated
**Engineer model**: codex-gpt-5
**Watermaster**: Spring (16)
**Target repo**: `/Users/jakegearon/projects/watershed/watershed-kernel/`
**Compiled at**: 2026-05-22
**Anchored to**: CANON Articles II, IV, V, IX, X, XV, XVI; `sops/engineer-brief.md` v2; `sops/operator-run-shape.md` v1 (retry-lineage discipline); `sops/dispatch-run-shape.md` v1; the kernel's `AGENTS.md` (Design Gate) and `PRESSURE_TESTS.md`.

---

## Read first

Read these in this order before drafting:

1. `watershed-kernel/AGENTS.md` — the kernel's Design Gate and principles.
2. `watershed-kernel/PRESSURE_TESTS.md` — the constitutional rules the existing compile-fail tests enforce.
3. `watershed-kernel/README.md` — current scope and what is intentionally excluded.
4. `watershed-kernel/watershed-contracts/src/lib.rs` — current contract surface (now with two pressure tests added by Brief 13).
5. `watershed-kernel/watershed-distributary/src/lib.rs` — current Plan/Run state machine (now with Pending → Running → Completed | Failed transitions and Run carrying intent + claims forward, from Brief 13).
6. `watershed-kernel/watershed-tributary/src/lib.rs` — current Validation/Merge/Baseline surface (now with claims-integrity check in validate, from Brief 13).
7. `watershed-kernel/watershed-distributary/tests/lawful_motion.rs`, `worker_lifecycle.rs`, `run_id_identity.rs` — the canonical full-ceremony and lifecycle tests.
8. `watershed-kernel/tests/compile_fail/*.rs` — the constitutional tests (now 10 of them, the most recent being `complete_run_before_running.rs` from Brief 13).
9. The chain's retry-lineage discipline at `sops/operator-run-shape.md` v1 (the SOP from which this Brief inherits the retry shape).

If anything in this Brief contradicts the kernel's `AGENTS.md` or its existing compile-fail discipline, treat `AGENTS.md` as the source of truth and stop to tell me. The Brief is the asking, the kernel is the law.

---

## The situation

`Run<Failed>` is currently a terminal dead end. The state has `reason()` as a getter; nothing else. There is no transition out, no path to re-attempt the work, no way for the kernel to model "the worker failed, but we want to try again."

The chain's discipline at the SOP layer is clear that retry is real and is part of typed-run identity. `operator-run-shape.md` v1 names the discipline: content-derived id incorporates `retried_from` and `retry_index` so that retries have different ids from their originals; lineage is recorded as a typed reference to the parent. `dispatch-run-shape.md` v1 carries the same discipline on the dispatch side. Brief 4 (Cascade, quarry-side OperatorRun) and Brief 9 (Anabranch, dgov-side DispatchRun) both implement this in code.

The Rust kernel doesn't.

This Brief adds it.

---

## What should exist after this Brief

Two structurally entangled things:

1. **`Run<S>` should carry retry lineage as identity-bearing fields.** Two fields belong on the run: `retried_from: Option<String>` (the id of the failed run this run retries, or `None` if this is the original dispatch) and `retry_index: u32` (zero for the original dispatch; incremented from the parent's value on each retry). The fields are present on every state of `Run<S>` (Pending, Running, Completed, Failed) and survive forward through every transition the kernel already has.

2. **`Run<Failed>` should expose a `retry()` transition that produces a fresh `Run<Pending>`.** The retry preserves the failed run's `intent` and `claims` (retry is "try the same work again," not "try a different work"), sets `retried_from = Some(self.id)`, increments `retry_index` from the parent's value, and derives a new `id` that incorporates the new retry lineage so the new Run is distinct from any prior attempt. The transition consumes the `Run<Failed>` (sealed marker discipline); the original failed run remains as a frozen typed record that the new Pending points back to.

The `derive_run_id` function from Brief 12 should grow to incorporate `retried_from` and `retry_index` in its hash inputs, so retries naturally produce different ids without requiring any other identity inputs to shift.

---

## Why this matters

The kernel exists to make legal motion obvious and illegal motion impossible. Today, "the worker failed; retry the work" is a real lab need (every prior typed-record SOP names it) but is illegal in the kernel — there's no transition. That's a gap between what the SOPs disciplines name and what the kernel enforces.

Filling the gap also lets the kernel exercise a constitutional law it doesn't yet have: **a completed run cannot be retried.** Only failed runs are retryable. This is a real discipline boundary (successful work doesn't get re-attempted; retrying a successful run is a category error), and it becomes enforceable as a compile-fail law once `retry()` exists on `Run<Failed>` but not on `Run<Completed>`.

The Brief also tightens the kernel's content-derived-id discipline. Brief 12 derived `run_id` from `(intent, claims)`. After this Brief, retries with the same intent and claims produce different ids (because `retried_from` and `retry_index` differ), which is exactly what the chain's content-derived-id discipline requires: equivalent dispatches yield equal ids, equivalent retries do not.

---

## Suggested approach

I think the cleanest shape is roughly this. **If you (Codex) think a different shape better serves the kernel's discipline — Rust idiom, sealed-marker patterns, lineage carrier patterns I'm not seeing — stop and tell me why before you implement. I'd rather hear "I think X is cleaner because Y" than have you build to my sketch if my sketch is wrong.**

- Add `retried_from: Option<String>` and `retry_index: u32` as private fields on `Run<S>` (the outer struct, parallel to `id`, `intent`, `claims`). They survive forward through all transitions (`start`, `complete`, `fail`) — the existing transitions copy them along with `id`, `intent`, `claims`.

- `dispatch(plan)` creates `Run<Pending>` with `retried_from = None` and `retry_index = 0`.

- `Run<Failed>::retry() -> Run<Pending>` is the only path out of Failed. It consumes the failed run, computes a new `id` from the lineage-aware inputs, and produces a fresh `Run<Pending>` with `retried_from = Some(original.id)` and `retry_index = original.retry_index + 1`.

- Add public getters on `Run<S>` for `retried_from()` and `retry_index()` so downstream consumers (validation, future tributary work, audit code) can walk the chain.

- Extend `derive_run_id(intent, claims)` to `derive_run_id(intent, claims, retried_from, retry_index)` so the id-derivation incorporates retry lineage. The Brief-12-existing strategy-tag prefix `b"run:"` and the SHA-256 hash composition stay; the new inputs are additional hash-update calls in the same function. Equivalent dispatches (same intent, claims, no retry lineage) still yield equal ids — that test from Brief 12 must continue to pass.

- Add a compile-fail test: `Run<Completed>` has no `retry()`. Only failed runs are retryable. The shape parallels Brief 13's `complete_run_before_running.rs` test.

- Add an integration test (or a small set) covering the retry semantics: retrying a failed run produces a new `Run<Pending>` with `retried_from` pointing at the original id, `retry_index` incremented by 1; equivalent retries from the same failed parent produce equal ids; retrying twice from the same failed run produces equal ids (or different — your call; see the design note below); the original failed run's id is unchanged.

  **Design note**: there's a real question of whether `Run<Failed>::retry()` should be consuming (one retry per failed run; the failed run is taken by value) or non-consuming (multiple retries from the same failed run allowed; takes `&self`). My read is consuming, because (a) it parallels the existing sealed transitions which all consume, (b) the failed run as a typed value being "spent" by retry matches the chain's frozen-pin-at-transition discipline, (c) if multiple retries from the same failed run are needed, the parent retry can itself be retried (forming a chain). But Codex's read on what the kernel's discipline wants here is welcome.

- Update `pressure_tests()` in `watershed-contracts/src/lib.rs` to add the new pressure tests with appropriate `name` / `claim` / `enforced_by` strings.

- Update the existing `run_id_identity.rs` tests if needed to account for the lineage-aware `derive_run_id` signature. The existing semantics (equivalent dispatches → equal ids, differing intents → different ids, differing claims → different ids) must continue to hold; new tests cover the retry-lineage cases.

- Update `full_ceremony_produces_baseline` in `lawful_motion.rs` if the integration test surface needs adjustment. The full ceremony does not involve retry, so the test should continue to walk the same path without modification, but verify that's still the case.

- Regenerate schemas with `cargo xtask schemas`. No public contract types change shape in this Brief (retry lineage lives on `Run<S>` which is distributary-private structure, not a `watershed-contracts` type), so the schemas should regenerate with byte-identical content. If they don't, that's a surprise worth flagging.

---

## Constitutional constraints

These are non-negotiable. If something below blocks the work, stop and tell me.

- **The Design Gate applies.** For every new type, field, transition, constructor, or dependency, answer: what legal motion creates or proves it? what later legal motion consumes or depends on it? what illegal motion becomes impossible because it exists? what compile-fail or integration test demonstrates that law? If you can't answer all four for something you're about to add, don't add it.

- **Compile-fail tests are constitutional evidence.** The "Run<Completed> has no retry()" law gets a trybuild test. The runtime retry semantics get integration tests paired with `PressureTest` entries in `watershed-contracts` — Brief 13 established the runtime-test-as-pressure-test shape; that shape applies here.

- **The institution holds.** Do not weaken a boundary because a test is awkward. Do not add a public constructor for an authoritative state because the lifecycle would be easier with one. Do not add a bypass.

- **Crate boundaries hold.** `watershed-distributary` constructs `Plan` and `Run` states (including the new `retried_from`/`retry_index` fields and the new `retry()` transition); `watershed-tributary` constructs `Validation`, `Merge`, `Baseline` states; `watershed-contracts` owns portable data and the pressure-test registry. Neither side fabricates the other's authoritative states.

- **The kernel stays in-memory.** Retry doesn't introduce persistence — the parent failed run as a typed value is the only "memory" the retry needs. There's no registry lookup for the parent; the retry transition takes the failed run by value, reads its id and retry_index directly.

- **DESIGN_DEBT items 1–3 stay deferred.** `WorkClass`, `VerificationSpec`, `RollbackSpec` are not consumed by this Brief. Retry lineage is independent of work classification, verification specs, and rollback specs. If you find yourself reaching for one of them to make this work clean, stop and tell me — that's a signal the Brief's policy needs revision, not a freelance promotion.

- **All existing compile-fail tests must continue to pass.** That includes the 10 currently in `tests/compile_fail/` (including `complete_run_before_running.rs` from Brief 13). If a test breaks because the constitutional surface shifted, stop and tell me before adapting it. If a test only needs an API-call signature update (e.g., to match the new `derive_run_id` signature) and the law it tests is preserved, that's integration-tail housekeeping — absorb inline and name the changes in the return.

- **The full ceremony in `lawful_motion.rs` must still produce a Baseline.** Retry is not in the ceremony; the ceremony's path is unaffected. Verify that's true.

- **Brief 13's two new pressure tests must continue to pass.** Both `complete_run_before_running` (compile-fail) and `validation_rejects_unclaimed_files` (runtime, at `watershed-tributary/tests/claims_integrity.rs`) must remain green. Retry doesn't touch validation logic or worker lifecycle ordering; it shouldn't interact with these tests.

---

## Write scope

Paths Codex may write to:

- `watershed-kernel/watershed-contracts/src/lib.rs`
- `watershed-kernel/watershed-distributary/src/lib.rs`
- `watershed-kernel/watershed-distributary/tests/run_id_identity.rs` (extend for retry-lineage cases; update the existing tests if the `derive_run_id` signature shift makes them need a call-site update)
- `watershed-kernel/watershed-distributary/tests/worker_lifecycle.rs` (extend or update if needed)
- `watershed-kernel/watershed-distributary/tests/lawful_motion.rs` (update if the ceremony surface needs adjustment; the test should continue to assert what it asserted)
- `watershed-kernel/watershed-distributary/tests/` (new tests if needed — e.g., a `retry_lineage.rs` test file)
- `watershed-kernel/tests/compile_fail/*.rs` (new compile-fail tests for "Run<Completed> has no retry()")
- `watershed-kernel/schemas/*.json` (regenerated via `cargo xtask schemas`; should be byte-identical if no contract types shifted, which I do not anticipate)
- `watershed-kernel/watershed-distributary/README.md` and `watershed-kernel/watershed-tributary/README.md` and `watershed-kernel/watershed-contracts/README.md` — **subcrate READMEs are Engineer-owned when describing surfaces this Brief modifies**. If retry adds public surface that the distributary README describes (the new run lifecycle including `Run<Failed>::retry()`, the new `derive_run_id` signature, the new `retried_from`/`retry_index` getters), update the README to match. Do NOT update READMEs for surfaces this Brief does not change.
- `watershed-kernel/Cargo.lock` (touched only if a workspace dep shifts; the Brief does not anticipate any)

Paths Codex may NOT write to:

- Anywhere outside `watershed-kernel/`
- The kernel-root `README.md`, `AGENTS.md`, `PRESSURE_TESTS.md`, `DESIGN_DEBT.md` (governance-layer docs; updates to them are Watermaster-side post-Brief integration work, not Engineer scope)

**Brief-style note**: this Brief disambiguates subcrate README ownership (Engineer-owned for surfaces this Brief modifies) following Codex's flag from Brief 13 that crate-local README ownership was ambiguous. This is the first exercise of the disambiguation; feedback on whether the wording is clear enough is welcome.

---

## Verification gates

All four must pass before returning:

1. `cargo fmt --all -- --check` clean.
2. `cargo clippy --workspace --all-targets -- -D warnings` clean.
3. `cargo test --workspace` passes. This includes:
   - All 10 existing compile-fail tests (`constitutional.rs` via trybuild).
   - The existing `run_id_identity.rs` tests (updated for the new `derive_run_id` signature if needed; the existing semantics must continue to hold).
   - The existing `worker_lifecycle.rs` tests (`pending_run_starts_before_completion`, `running_run_can_fail`).
   - The `claims_integrity.rs` runtime test (Brief 13's tributary test).
   - The `full_ceremony_produces_baseline` test (still produces a Baseline).
   - Any new tests this Brief introduces (retry-lineage runtime tests + new compile-fail test for `Run<Completed>` having no `retry()`).
4. `cargo xtask schemas` runs to completion. Schemas should be byte-identical (no contract types changed); if they're not, flag that as a surprise.

Run these from `/Users/jakegearon/projects/watershed/watershed-kernel/`.

---

## Return shape

Structured return matching the chain's `return-{N}.md` audit shape (same as Brief 13):

- **Summary**: 2–4 sentences naming what landed.
- **Files written**: every path touched, with brief description (including any subcrate READMEs you updated and why).
- **Lifecycle decisions**: the Rust shape you chose for retry (consuming vs non-consuming, where retried_from / retry_index live, how the derive_run_id extension hashed the new inputs), and why.
- **Verification gate results**: output (or summary) of each of the four `cargo` commands.
- **Compile-fail tests added**: name, claim, what illegal motion is now impossible.
- **Pressure tests added to `pressure_tests()`**: same.
- **Flags**: anything you noticed during the work that the Brief should have anticipated but didn't, anything you had to push back on, anything in DESIGN_DEBT that almost got promoted (and why you held off).
- **Anything you'd change about the Brief**: what was unclear, over-prescriptive, or wrong. The Brief style is now on its second exercise; your read on whether the README-ownership disambiguation worked, and whether the policy-direction style is settling into something usable, is part of the Brief's own pressure-testing.

---

## Push-back is welcome

The Brief style is: I'm telling you the policy direction, you're telling me how it codes in Rust. If you think:

- Retry shouldn't be a consuming transition (multiple retries from one failed run, taking `&self`),
- The retry lineage fields shouldn't live on the outer `Run<S>` (some other carrier shape is cleaner),
- `derive_run_id` shouldn't grow to four arguments (e.g., the lineage inputs should be carried in a separate `RunLineage` struct that becomes the second arg),
- The "Run<Completed> has no retry()" law should be enforced differently (e.g., a different trait split, a different sealed-marker arrangement),
- Promoting one of the DESIGN_DEBT items would actually serve this work and the Design Gate test would pass for it,
- A retry limit (max_retries) should be part of this Brief rather than deferred,
- The subcrate README ownership clause in the write scope is unclear or wrong,

— stop, don't implement, and tell me. The kernel asks for reasoning before motion. Tokens are bountiful; authority is scarce. Spend the reasoning.

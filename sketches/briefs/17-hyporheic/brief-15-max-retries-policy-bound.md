---
brief_id: brief-15
title: max_retries policy bound
state: integrated
drafted: 2026-05-23
sent: 2026-05-23
returned: 2026-05-23
integrated: 2026-05-23
engineer_model: codex-gpt-5
target_repo: /Users/jakegearon/projects/watershed/watershed-kernel/
watermaster: Hyporheic
canon_anchor: V, IX, X, XV
---

# Brief 15 — max_retries policy bound

## Recipient

Codex (`codex-gpt-5`), executing against the Rust kernel at `/Users/jakegearon/projects/watershed/watershed-kernel/`.

## Source utterance

Hyporheic's recon and discussion with the Source led to: a fourth kernel Brief in the policy-direction style, scoped to bound retry depth under `Policy`. Brief 14 (Spring) landed `Run<Failed>::retry()` as an infallible consuming transition that increments `retry_index` and preserves lineage; nothing structurally stops the chain from growing unboundedly. Production reality has flaky workers; the kernel should make unbounded retry illegal under policy.

## What should exist

The kernel should enforce a retry-depth bound declared on the `Policy` that validated the originating `Plan<Compiled>`. Specifically:

1. **`Policy` carries a retry budget**: a new field on `Policy` that expresses "how many retries past the original dispatch this work may take." `None` means unbounded; `Some(0)` means no retries; `Some(n)` means at most n retries.
2. **The bound is structural, not Plan-declared**: every dispatched run under a Policy with a finite budget obeys the bound; no Plan can bypass it via omission from any required-checks field. This is the same structural-vs-Plan-declared distinction Brief 13 established for claims integrity.
3. **`Run<Failed>::retry()` enforces the bound**: when the failed run's `retry_index` already equals or exceeds the budget, retry is refused. The refusal is a typed error, not a panic.
4. **The bound travels with the work, not with the call site**: the policy that validated the parent Plan determines the budget for every descendant Run. A caller cannot pass a different Policy at retry time to widen the bound.

## Why

- Brief 14's `retry_chain_increments_from_each_failed_parent` test exercises a chain of depth 2. The test is a positive demonstration; it is not a bound. Production deployment of any kernel-backed dispatcher would inherit unbounded retry as a real failure mode the substrate doesn't refuse.
- `Policy` is the natural home for governance bounds. It already carries `require_claims`, `allow_shared_claims`, `required_pressure_tests` — boolean and enumeration governance applied at `validate()`. A retry budget is the same shape of governance.
- Per Spring's structural-vs-Plan-declared distinction (Brief 13's conversation about `VerificationSpec.checks`): rules that the kernel always enforces under policy are structural and live in transition logic; rules the Plan-author lists are Plan-declared and live in declared-check enumerations. The retry budget is structural — the kernel refuses excess retries regardless of what any Plan author lists.
- The Design Gate answers cleanly:
  - *What legal motion creates or proves this?* Policy carries the field; `Plan<Compiled>::validate` accepts it.
  - *What later legal motion consumes or depends on it?* `Run<Failed>::retry()` checks it.
  - *What illegal motion becomes impossible?* Retrying past a policy's declared budget.
  - *What test demonstrates the law?* A runtime integration test attempting to retry at the budget boundary.

## Constitutional constraints

- **The Design Gate holds.** Do not add fields, types, or transitions that don't answer all four questions.
- **Sealed marker discipline.** `Run<S>::retry()` remains a consuming transition (`self` by value, not `&self`). The bound check happens before the transition produces a new state.
- **No bypasses.** A `Plan` cannot opt out of an enforced bound by omitting an entry from any declared-checks field. The bound lives in the kernel's transition logic, not in `VerificationSpec.checks`.
- **Crate boundaries.** Policy lives in `watershed-contracts`; retry() lives in `watershed-distributary`; no settlement-crate (`watershed-tributary`) involvement.
- **No new dependencies.** This Brief should not pull new crates into Cargo.toml. The `serde`/`schemars`/`sha2`/`thiserror` set already on the workspace is sufficient.
- **In-memory scope unchanged.** No persistence, no subprocesses, no worktrees, no CLI. Per the kernel README's Current Scope.
- **DESIGN_DEBT items 1-3 stay deferred.** `WorkClass`, `VerificationSpec`, `RollbackSpec` are not consumed by this Brief. Do not promote them on anticipation.

## Suggested approach (push back if not)

I think the cleanest shape threads the budget forward from `Plan<Validated>` into `Run<S>`:

- `Policy` gains `max_retries: Option<u32>` (None = unbounded; `Some(n)` = at most n retries past the original dispatch).
- `Plan<Compiled>::validate(&policy)` extracts the budget; the `Validated` state carries it.
- `dispatch(Plan<Validated>)` threads the budget into `Run<S>` alongside `id, intent, claims, retried_from, retry_index, state`. The budget is a private field on the outer `Run<S>` struct, parallel to the existing private-field discipline.
- `Run<Failed>::retry()` returns `Result<Run<Pending>, RetryError>`. The bound check is the first thing retry() does: when `max_retries` is `Some(n)` and `retry_index >= n`, return `RetryError::BudgetExhausted { current: retry_index, budget: n }`. When `max_retries` is `None`, retry succeeds unconditionally (existing behavior).
- `RetryError` is a new public error type in `watershed-distributary` with `#[derive(Debug, Error)]` and a `BudgetExhausted` variant.

I think this is cleanest for three reasons:

1. **The budget is identity-bearing for the work, not the caller.** Threading it through the lawful motion means the bound applies to every retry from the same dispatch, regardless of where retry() is called from. The alternative — `retry(&Policy)` taking a policy at retry time — admits a path where the caller passes a different policy and widens the bound. That bypass is exactly what the kernel's no-bypasses principle refuses.
2. **Fallible `retry()` matches the discipline.** Other lawful transitions in the kernel that can refuse (e.g., `Plan<Compiled>::validate` returns `Result<Plan<Validated>, ValidationError>`) are fallible. Making `retry()` fallible aligns it with the existing pattern. The alternative — keep `retry()` infallible but add `can_retry(&self) -> bool` — admits a path where the caller forgets to check.
3. **The bound is not in the run_id hash.** `derive_run_id` already hashes `intent`, `claims`, `retried_from`, `retry_index`. Adding `max_retries` to the hash would mean two retries from the same failed parent under different policies produce different ids — that's wrong, because the budget is governance, not identity. The retry's content is the same work; the budget is a separate axis. Hash composition stays unchanged in this Brief.

**Push back if any of these is wrong from a Rust-idiom perspective.** Concretely:

- If you think keeping `retry()` infallible with a separate `can_retry` predicate is the better Rust idiom even given the bypass risk, tell me why before making the change.
- If threading `max_retries` through `Run<S>` creates substantial friction (privacy block bloat that breaks fixture-tracking, identity-derivation implications I missed, ergonomic awkwardness in tests), tell me before implementing. The alternative shape — store the budget only on `Validated` and pass it as an explicit `&Policy` reference to retry() — is a real fallback, even though I argued against it above. If you find the alternative is actually cleaner once you're in the code, that's worth surfacing.
- If the bound semantics should be different (`retry_index > max_retries` rather than `>=`; budget measured against total attempts including the original rather than against retries past the original), tell me. The SOP-level retry discipline from `operator-run-shape.md` v1 names `retry_index = 0` for the original and `retry_index = retried_from.retry_index + 1` for each retry, so "max_retries = n" means "retry_index may reach n but not n+1" — i.e., `retry_index >= n` refuses. If Rust idiom or your reading of the SOP suggests otherwise, surface it.
- If `max_retries: Option<u32>` should be `max_retries: u32` with a sentinel like `u32::MAX` for unbounded, tell me. I think `Option<u32>` is cleaner because it makes "no bound" structurally distinct from "very large bound," but you may see a reason to prefer the flat type.

## Write scope

- `watershed-contracts/src/lib.rs` — add `max_retries: Option<u32>` to `Policy`. Add a new pressure_test entry `RETRY_RESPECTS_MAX_RETRIES` (constant + `pressure_tests()` registration).
- `watershed-distributary/src/lib.rs` — add `RetryError` enum; thread `max_retries` through `Validated` → `Run<S>` → `retry()`; make `retry()` return `Result<Run<Pending>, RetryError>`.
- `watershed-distributary/tests/retry_budget.rs` — new runtime integration test demonstrating: retry succeeds at index < budget, retry refused at index == budget, unbounded budget (`None`) allows arbitrary depth, error variant matches expected shape.
- `tests/compile_fail/*` — none expected from this Brief. The bound is a runtime invariant, not a structural impossibility.
- **Existing integration tests will need updates** to pass through the new `retry()` signature (`Result` unwrapping) and the new `Policy` field. Specifically: `watershed-distributary/tests/retry_lineage.rs`, `watershed-distributary/tests/lawful_motion.rs`, `watershed-distributary/tests/worker_lifecycle.rs`, `watershed-distributary/tests/run_id_identity.rs`, `watershed-tributary/tests/claims_integrity.rs`, and any compile-fail fixture under `tests/compile_fail/` that constructs a `Policy` literal. These updates are integration-tail housekeeping per Brief 14's "law preserved, fixture-call updated" pattern — preserve the laws each test verifies and only update API-call shapes where the new `retry()` signature or new `Policy` field requires it. The `construct_completed_run_directly.stderr` fixture's note line listing private fields will gain `max_retries` if the field lands on `Run<S>` per the suggested approach — absorb that update inline.
- **Subcrate READMEs** (`watershed-distributary/README.md`) — Engineer-owned for any surface this Brief modifies (per Brief 14's subcrate-README-ownership clause, first exercise was clean). Update where the retry surface or Policy shape is described.
- **`schemas/`** — regenerated by `cargo xtask schemas`. The `Policy` schema will gain a new field; other schemas should be byte-identical.

**Watermaster-only governance docs** (not in your write scope): `watershed-kernel/README.md`, `watershed-kernel/AGENTS.md`, `watershed-kernel/PRESSURE_TESTS.md`, `watershed-kernel/DESIGN_DEBT.md`. If you notice these need updates after the Brief lands (e.g., the new pressure test wants documentation in `PRESSURE_TESTS.md`), flag them in the return rather than editing them. The Watermaster will preflight an integration-tail housekeeping update per Brief 14's precedent.

## Verification gates

Run all four from the kernel root (`/Users/jakegearon/projects/watershed/watershed-kernel/`) after changes:

```sh
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo xtask schemas
```

Expected outcomes:
- `cargo fmt`: clean.
- `cargo clippy`: clean (zero warnings).
- `cargo test --workspace`: all existing tests pass (after integration-tail updates), plus new `retry_budget.rs` tests pass. The 11 existing pressure tests continue to refuse illegal motion (10 trybuild compile-fail fixtures + the runtime tests `claims_integrity.rs` and `retry_lineage.rs`). A 12th pressure test (`retry_respects_max_retries`) is registered and passes.
- `cargo xtask schemas`: all schema files except `policy.schema.json` byte-identical; `policy.schema.json` regenerated with the new `max_retries` field added.

## Return shape

Return as a structured summary (the `return-{N}.md` audit format the chain established):

1. **Files written**: explicit list of paths, with one line each describing what changed.
2. **Verification gates**: paste the exit status / summary of each of the four cargo commands.
3. **Design decisions**: name each call you made within the suggested approach's latitude (where the budget lives, how the error variant is shaped, etc.) with one sentence each.
4. **Deviations**: anything that deviated from the Brief's stated approach, with reasoning. Use "deviation" not "creative liberty" — the discipline floor is honest naming.
5. **Flags**: anything you noticed adjacent to the Brief that you did NOT fix, with one sentence each. Particularly anything that would benefit from a follow-up Brief.
6. **Brief feedback**: any structural issue with the Brief itself (ambiguity, missing context, contradiction) that would have helped you to know upfront. Spring's Brief 13 feedback ("API-shape briefs should explicitly say whether crate-local READMEs are Engineer-owned or Watermaster-owned") tipped a v3 candidacy item; your feedback is part of the chain's discipline-refinement.

## Push-back welcome

Stop and tell the Source (who will relay to Hyporheic) BEFORE implementing if:

- **You think the suggested approach is structurally wrong**, not just stylistically suboptimal. Particularly if you believe the bound can't be enforced as I've described without breaking a kernel discipline I haven't surfaced (sealed-marker behavior, type-state machinery, identity-derivation consequences, crate-boundary violation).
- **You think the right shape is a substantially different transition**. For example, if `retry()` should remain infallible and a different transition (e.g., `Plan<Validated>::can_dispatch_retries() -> u32`) should carry the budget, push back. I'd rather hear "I see a different shape that doesn't admit the bypass you're worried about" than have you implement the suggested approach grudgingly.
- **The integration-tail surface explodes beyond what a single Brief should carry**. If updating the existing tests reveals more API-touching than I anticipated (e.g., the `Policy` literal appears in 15+ places across compile-fail fixtures), tell me before implementing. We may want to stage this differently.
- **You discover something about the existing kernel that contradicts my recon.** I read all three crates' `lib.rs`, the compile-fail tests, and the integration tests as of 2026-05-23. If you find I missed something material, surface it.

Stop and integrate without pushing back if:
- Standard Rust-idiom choices that don't bypass the kernel discipline (where the error type lives, what derive macros it carries, how the `Display` impl reads, naming).
- Test code structure within `retry_budget.rs` (helper functions, parametrized cases, test naming).
- Integration-tail fixture updates that are mechanically obvious (Policy literal gains a field, retry() Result-unwrapping pattern in tests).

## Out of scope / not asking

This Brief does NOT ask for any of the following — flag if you notice them but do not implement:

- Promotion of any DESIGN_DEBT item (WorkClass, VerificationSpec, RollbackSpec). Each is gated by a transition consuming it; this Brief does not provide that transition.
- Persistence of any kind. No registry tables, no disk writes, no serialization beyond what schemars already provides.
- Real worker dispatch (replacing `mock_worker`). The kernel scope remains in-memory.
- Plan revision / supersession discipline. Brief 14's terminating thought about "retry the same work" vs "supersede with a revised plan" is not in scope.
- New event emission, new event types, anything observability-shaped.
- Changes to `Validation`, `Merge`, `Baseline`, or any tributary surface.
- Changes to `derive_run_id`. The id hash composition stays as Brief 14 left it: `intent + claims + retried_from + retry_index`. Adding `max_retries` to the hash would mean the bound is identity, not governance — wrong shape. (If you find a real reason it should be in the hash, push back per the section above; do not implement silently.)

---

The kernel's no-bypasses principle, the structural-vs-Plan-declared distinction Brief 13 established, and the policy-direction Brief style Spring exercised twice are the working register. Three clean Briefs in this style mark canonical calibration; this is the fourth. The Design Gate is the discipline; the Brief is the asking; the kernel is the law.

— Hyporheic

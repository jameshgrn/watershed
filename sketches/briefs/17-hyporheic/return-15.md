---
return_id: return-15
brief_id: brief-15
title: max_retries policy bound — EngineerReturn
engineer_model: codex-gpt-5
received_at: 2026-05-23
integrated_by: Watermaster Hyporheic
elapsed_seconds: 386
---

# return-15 — max_retries policy bound

## Codex return (verbatim)

> Files Written
>     - watershed-contracts/src/lib.rs — added Policy.max_retries and RETRY_RESPECTS_MAX_RETRIES.
>     - watershed-distributary/src/lib.rs — threaded retry budget through validated plans/runs; made retry() fallible with RetryError.
>     - watershed-distributary/tests/retry_budget.rs — added runtime budget boundary tests.
>     - watershed-distributary/tests/retry_lineage.rs — updated retry calls for Result.
>     - watershed-distributary/tests/lawful_motion.rs — added policy budget field.
>     - watershed-distributary/tests/worker_lifecycle.rs — added policy budget field.
>     - watershed-distributary/tests/run_id_identity.rs — added policy budget field.
>     - tests/compile_fail/dispatch_twice.rs — added policy budget field.
>     - tests/compile_fail/complete_run_before_running.rs — added policy budget field.
>     - tests/compile_fail/retry_completed_run.rs — added policy budget field.
>     - tests/compile_fail/construct_validated_plan_directly.rs — updated private-field fixture.
>     - tests/compile_fail/construct_completed_run_directly.stderr — updated private-field stderr.
>     - tests/compile_fail/construct_validated_plan_directly.stderr — updated private-field stderr.
>     - watershed-distributary/README.md — documented fallible retry.
>     - schemas/Policy.json — regenerated with nullable max_retries.
>
> Verification Gates
>     - cargo fmt --all -- --check: exit 0.
>     - cargo clippy --workspace --all-targets -- -D warnings: exit 0, no warnings.
>     - cargo test --workspace: exit 0. Includes 11 compile-fail fixtures, existing runtime pressure tests, and 5 new retry-budget tests.
>     - cargo xtask schemas: exit 0.
>
> Design Decisions
>     - Budget lives on Policy, then privately on Validated and Run<S>.
>     - retry() takes no policy argument, so callers cannot widen the budget.
>     - RetryError::BudgetExhausted { current, budget } is the typed refusal.
>     - derive_run_id stayed unchanged; retry budget is governance, not identity.
>
> Deviations
>     - None from the suggested implementation shape.
>
> Flags
>     - The brief's pressure-test count was stale against current state: this repo has 11 trybuild fixtures and now 14 registered pressure tests after adding retry_respects_max_retries.
>     - Parent git reports /Users/jakegearon/projects/watershed/watershed-kernel/ as untracked, so status is not granular.
>
> Brief Feedback
>     - The brief should state the current pressure-test count mechanically, or avoid exact counts when the kernel is moving quickly.
>
> Goal marked complete. Recorded elapsed time: about 6m 26s.

## Watermaster integration notes

### Scope verification (direct file inspection)

All 15 files inspected against the declared `write_scope`:

1. `watershed-contracts/src/lib.rs` — `Policy.max_retries: Option<u32>` added at line 59 between `allow_shared_claims` and `required_pressure_tests` (sensible ordering: governance bools then governance lists). New constant `RETRY_RESPECTS_MAX_RETRIES` at line 99. Fourteenth `PressureTest` entry registered at lines 169-173 enforced by `watershed-distributary/tests/retry_budget.rs`. In scope.

2. `watershed-distributary/src/lib.rs` — `Validated` gained `max_retries: Option<u32>` (line 42). `Run<S>` gained `max_retries: Option<u32>` private field (line 224) parallel to existing `retried_from`/`retry_index`. `RetryError::BudgetExhausted { current, budget }` (lines 170-177). `retry()` is now fallible (`Result<Run<Pending>, RetryError>`, line 336). The bound check is the first thing `retry()` does (lines 346-353); when `max_retries == None`, retry succeeds unconditionally (existing behavior preserved). `max_retries` threaded through all four `Run<S>` state transitions (`start`, `complete`, `fail`, `retry`). `dispatch` reads `max_retries` from `Validated` and threads into `Run<Pending>` (line 412). `derive_run_id` signature UNCHANGED — exactly as the Brief specified (governance not identity). In scope.

3. `watershed-distributary/tests/retry_budget.rs` — five new runtime tests cover the full constitutional surface: (a) retry succeeds at index < budget, (b) retry refused at `index == budget` with `BudgetExhausted { current, budget }` matching exact values, (c) zero budget refuses the first retry (edge case Codex added on its own initiative — defensible scope-bounded; the budget = 0 case is structurally distinct from budget = N for N > 0), (d) `None` budget allows arbitrary depth, (e) `retry_budget_is_not_part_of_run_identity` — bounded and unbounded retries from equivalent failed parents produce equal ids, verifying `derive_run_id`'s exclusion of `max_retries` from the hash. Test #5 is the structural constitutional assertion for "governance not identity." In scope.

4. `watershed-distributary/tests/retry_lineage.rs` — all 6 `.retry()` call sites (lines 49, 75, 78, 91, 106, 115) updated to `.retry().expect(...)` with appropriate panic messages. Policy literal in `validated_plan()` gained `max_retries: None`. Brief 14's law preserved (retry lineage from `Run<Failed>`); fixture-call shape updated to absorb the new `Result` return. In scope.

5. `watershed-distributary/tests/lawful_motion.rs` — Policy literal at line 21 gained `max_retries: None`. The canonical full-ceremony test continues to pass; the new field is supplied with no-bound semantics. In scope.

6. `watershed-distributary/tests/worker_lifecycle.rs` — Policy literal at line 19 gained `max_retries: None`. Brief 13's worker-lifecycle law preserved. In scope.

7. `watershed-distributary/tests/run_id_identity.rs` — Policy literal at line 19 gained `max_retries: None`. Brief 12's content-derived-id law preserved. In scope.

8. `tests/compile_fail/dispatch_twice.rs` — Policy literal updated. In scope.

9. `tests/compile_fail/complete_run_before_running.rs` — Policy literal updated. In scope.

10. `tests/compile_fail/retry_completed_run.rs` — Policy literal updated. In scope.

11. `tests/compile_fail/construct_validated_plan_directly.rs` — Validated literal at lines 5-14 now includes `max_retries: None` as a fabrication attempt of the private field. The compile-fail law (you cannot fabricate a `Validated` from outside the dispatcher) is structurally strengthened by the added field: the .stderr now reports `intent`, `claims`, AND `max_retries` as private fields. In scope.

12. `tests/compile_fail/construct_completed_run_directly.stderr` — line 9's "...and other private fields" note now reads `id`, `intent`, `claims`, `retried_from`, `retry_index` and `max_retries`. Brief 13's `Run<S>`-owns-shared-identity discipline absorbs the new private field cleanly; Spring's "growing private-field list as canonical fabrication-blocking mechanism" Live observation continues to hold. In scope.

13. `tests/compile_fail/construct_validated_plan_directly.stderr` — error E0451's private-field list now names `intent`, `claims` AND `max_retries`. In scope.

14. `watershed-distributary/README.md` — Engineer-owned per Brief 14's subcrate-README-ownership clause (second exercise, clause read cleanly again). Run motion list at line 19 now reads `Run<Failed>::retry() -> Result<Run<Pending>, RetryError>`. Line 23 updated to name "the validating policy's retry budget forward from dispatch." Lines 26-27 added: "Retrying a failed run consumes `Run<Failed>`, checks the validating policy's `max_retries`...If the current `retry_index` has reached a finite `max_retries` budget, retry returns `RetryError::BudgetExhausted`." Accurate to source. In scope.

15. `schemas/Policy.json` — regenerated. `$comment` content-hash updated to `fa62bca3...`. `max_retries` declared as nullable integer (`["integer", "null"]` with `format: "uint32"`, `minimum: 0.0`); not in `required` array (correct — `Option<u32>` is optional). Other schemas unchanged (Codex's structured return indicates only `Policy.json` listed; the other 8 schemas should be byte-identical). In scope.

Verification path: direct file inspection on every declared path. Sandbox `cargo` unavailable (Anabranch / Bench / Spring precedent for the dgov-side and Codex's-host-side verification); trust Codex's structured return for test counts and cargo gate exit statuses, as established by `engineer-brief.md` v2.

### Codex's claimed test count vs. registry reality

Codex's structured return states: "11 compile-fail fixtures, existing runtime pressure tests, and 5 new retry-budget tests" and "now 14 registered pressure tests after adding `retry_respects_max_retries`." Counted against the current `pressure_tests()` registry: 11 entries enforced by `tests/compile_fail/*.rs`, 3 enforced by runtime tests (`watershed-tributary/tests/claims_integrity.rs`, `watershed-distributary/tests/retry_lineage.rs`, `watershed-distributary/tests/retry_budget.rs`). Total = 14. Matches Codex's return.

### Brief feedback honored

Codex flagged: "The brief should state the current pressure-test count mechanically, or avoid exact counts when the kernel is moving quickly." Honest and correct. My Brief stated "11 pressure tests" in two places (Constitutional constraints section and Verification gates section). Reality at Brief drafting was 13 (11 compile-fail + 2 runtime). The recon read both compile-fail directory listings and the `pressure_tests()` registry — the 13-count was visible to me — but I drafted with the lower compile-fail-only count by mistake. Two corrective patterns going forward:

1. **Brief constants come from the registry, not from the directory listing.** When citing pressure-test counts, read `pressure_tests()` in `watershed-contracts/src/lib.rs` and cite the length of the returned vector, not the count of `.rs` files in `tests/compile_fail/`. Counts that include runtime invariants are accurate to the current state; counts derived from compile-fail directories miss runtime tests.

2. **Avoid exact counts when describing the constitutional surface in flight.** The Brief could have said "the existing pressure tests" rather than "11 pressure tests" — same constraint surface, lower drift-risk. Where counts genuinely matter (e.g., a Brief that explicitly extends the registry), spell out the names and let Codex verify against current state. Where counts are background context (Brief 15's case), use indefinite reference instead.

Both refinements are Live observation territory; see THINKING.md update.

### One genuine non-flag

Codex's second flag — "Parent git reports `/Users/jakegearon/projects/watershed/watershed-kernel/` as untracked, so status is not granular" — is an environment observation, not a Brief deviation. The kernel-into-watershed move at Meander's session close placed the kernel inside the watershed working tree without committing it to watershed's git history; the kernel's own git state is separate. Codex's `git diff` could see file changes but not at a "parent reports clean/dirty" level. The structured-return path (files-written list + cargo gates) is the canonical audit shape regardless; the git-status observation does not affect integration.

### Pressure-test count change

`pressure_tests()` registry now lists 14 entries (was 13). The new entry `retry_respects_max_retries` documents a runtime invariant enforced by `watershed-distributary/tests/retry_budget.rs`. `PRESSURE_TESTS.md` (Watermaster-only governance) needs a follow-up update per Brief 14's kernel-root-governance-docs convention — see in-chat preflight to follow.

### DESIGN_DEBT items unchanged

Items 1-3 (`WorkClass`, `VerificationSpec`, `RollbackSpec`) remain deferred. This Brief did not promote any of them; the Design Gate held. Grep confirms: no new uses of `WorkClass`, `VerificationSpec`, or `RollbackSpec` in any Brief-15-touched file.

### derive_run_id semantics confirmed unchanged

`derive_run_id` signature and hash composition at lines 375-397 of `watershed-distributary/src/lib.rs` exactly match the post-Brief-14 state. Brief 12's content-derived-id discipline, Brief 14's lineage-aware extension, and Brief 15's exclusion of `max_retries` from the hash all hold simultaneously. Two retries from equivalent failed parents under different policies produce equal ids; the `retry_budget_is_not_part_of_run_identity` test demonstrates the law.

## Integration action

- Brief 15 state flipped `drafted → sent → returned → integrated` (final flip after `PRESSURE_TESTS.md` preflight lands; see chain of in-chat work to follow).
- 15 files verified in declared write_scope.
- `return-15.md` recorded at this path.
- THINKING.md to be updated with: new Settled pointer for Brief 15; Live observations for the stale-pressure-test-count Brief-drafting miss, third clean policy-direction Brief, second clean subcrate-README disambiguation exercise.
- `PRESSURE_TESTS.md` Watermaster-side update to be preflighted in-chat (Brief 14 precedent for kernel-root governance docs as integration-tail housekeeping when `pressure_tests()` gains entries).

— Hyporheic

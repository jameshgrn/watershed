# Brief 13 — Worker lifecycle and claims integrity

**State**: integrated
**Engineer model**: codex-gpt-5
**Watermaster**: Spring (16)
**Target repo**: `/Users/jakegearon/projects/watershed/watershed-kernel/`
**Compiled at**: 2026-05-22
**Anchored to**: CANON Articles II, IV, V, IX, X, XV, XVI; `sops/engineer-brief.md` v2; `sops/dispatch-run-shape.md` v1; `sops/operator-shape.md` v2; `sops/operator-run-shape.md` v1; `sops/deposit-shape.md` v2; `sops/validation-shape.md` v1; the kernel's `AGENTS.md` (Design Gate) and `PRESSURE_TESTS.md`.

---

## Read first

Read these in this order before drafting:

1. `watershed-kernel/AGENTS.md` — the kernel's Design Gate and principles.
2. `watershed-kernel/PRESSURE_TESTS.md` — the constitutional rules the existing compile-fail tests already enforce.
3. `watershed-kernel/README.md` — current scope and what is intentionally excluded.
4. `watershed-kernel/watershed-contracts/src/lib.rs` — current contract surface.
5. `watershed-kernel/watershed-distributary/src/lib.rs` — current Plan/Run state machine.
6. `watershed-kernel/watershed-tributary/src/lib.rs` — current Validation/Merge/Baseline surface.
7. `watershed-kernel/watershed-distributary/tests/lawful_motion.rs` — the canonical full-ceremony example.
8. `watershed-kernel/tests/compile_fail/*.rs` — the constitutional tests.

If anything in this Brief contradicts the kernel's `AGENTS.md` or its existing compile-fail discipline, treat `AGENTS.md` as the source of truth and stop to tell me. The Brief is the asking, the kernel is the law.

---

## The situation

The kernel has a state-machine hole and a constitutional hole, and they are the same hole.

**State-machine hole.** `Run<Pending>`, `Run<Running>`, `Run<Completed>`, and `Run<Failed>` are declared as sealed `RunState` markers, but only `Run<Pending> → Run<Completed>` is reachable today, via a single-step `mock_worker(Pending) → Completed` shortcut. `Run<Running>` and `Run<Failed>` have getters but no constructors and no transitions into them. The worker lifecycle the type system describes is not the worker lifecycle the kernel actually models.

**Constitutional hole.** `validate(deposit)` checks one thing: whether `deposit.summary` is empty. It does not check whether the worker respected the Plan's `FileClaim`s. The kernel's whole point — "make illegal movement impossible and legal movement obvious" — does not yet extend to "the worker did what its Plan claimed to do." A worker can claim `Exclusive` over `a.rs`, produce a Deposit that touched `b.rs`, and pass validation.

**Why they're the same hole.** Today, after `dispatch(Plan<Validated>)`, the Run carries `id` and `touched_files` but forgets the intent and claims that produced it. So even if `validate()` wanted to check claims integrity, it has nothing to check against. The claims live on the Plan; the Plan is consumed by dispatch; the Run is what survives. For validation to enforce claims, the Run needs to remember what the Plan asked for.

---

## What should exist after this Brief

Three things, named in policy rather than implementation:

1. **The worker lifecycle should pass through the states the type system declares.** A Pending run becomes Running before it can become Completed or Failed. Completed and Failed are each reachable only through the appropriate transition from Running. The current `Pending → Completed` shortcut should not survive this Brief — either as a deliberate kernel affordance or as a stub for `mock_worker` to use.

2. **The Run should carry forward enough of the Plan to enable claims-integrity checking at validation time.** The intent and claims that derived the Run's id are part of what the Run IS; today they're discarded at dispatch. After this Brief, validation should be able to recover the Plan's claims from whatever it receives, without reading anything off disk or out of a registry (the kernel is in-memory).

3. **Validation should refuse to accept a Deposit whose touched files include paths not in the Plan's `FileClaim`s.** "The worker did what its Plan claimed" becomes a constitutional check, not advisory. Existing validation checks (the summary-empty check) remain; this is additive at the policy level even if it reshapes the function surface.

   **This check is a structural invariant, not a Plan-declared verification check.** The distinction matters and shapes the implementation. The kernel currently has two implicit kinds of validation in its design space:

   - **(A) Structural invariants** — properties the kernel always enforces on every Plan-Deposit pair, regardless of what any particular Plan listed. Not opt-in. Not bypassable by Plan-author omission. Enforced as a property of the kernel itself, via the `validate()` transition. The claims-integrity check this Brief adds is of this kind.

   - **(B) Plan-declared verification checks** — the list of named checks a particular Plan declares it requires (e.g., "run `cargo test`," "schema X validates," "no panics in baseline"). Workspace-specific, Plan-specific, opt-in via the Plan author's declaration. `VerificationSpec.checks: Vec<String>` in `watershed-contracts` is shaped for this kind.

   This Brief lands (A) only. It does not add any (B)-style "Plan declares its required checks, validation runs them" machinery. The claims-integrity check is enforced because the kernel says so, not because a Plan's `VerificationSpec` listed it.

---

## Why this matters

The kernel exists to make illegal motion impossible at compile time and obvious at runtime. Today, "the worker exceeded its Plan's claims" is neither impossible nor obvious — it passes validation silently. That is exactly the class of drift the kernel was built to refuse.

The state-machine hole and the constitutional hole are entangled because the kernel cannot check claims integrity without the Run remembering its Plan, and the Run cannot meaningfully model a worker without the lifecycle states the type system already declares. Filling both in one Brief lets them shape each other; splitting them would force one Brief to bend to accommodate the other's eventual shape.

The discipline payoff: a new compile-fail test for "Validation cannot accept a Deposit that touched files outside its Plan's claims" becomes possible, and the `WorkerProducesDeposit` pressure test gains a real "what the worker produced was lawful" gate behind it.

---

## Suggested approach

I think the cleanest shape is roughly this. **If you (Codex) think a different shape better serves the kernel's discipline — Rust idiom, sealed-marker patterns, crate-boundary plays I'm not seeing — stop and tell me why before you implement. I'd rather hear "I think X is cleaner because Y" than have you build to my sketch if my sketch is wrong.**

- Replace `mock_worker(Pending) → Completed` with consuming transitions from `Run<Pending>` into `Run<Running>`, and from `Run<Running>` into `Run<Completed>` or `Run<Failed>`. Keep `mock_worker` if it's useful as a test helper, but have it walk the real lifecycle (Pending → Running → Completed) rather than skipping states.

- Thread the intent and claims through dispatch into the Run so they survive forward. The exact carrier is your call — a struct field on each `Run<S>`, a private bundle type, a Plan-snapshot pinned at dispatch time, whatever serves the kernel's discipline best.

- Reshape `validate(...)` so it has access to the Plan's claims. This might mean `validate(deposit, &[FileClaim])`, or `validate(completed: Run<Completed>) → Validation` directly, or some shape that pulls the deposit out of the completed run by transition rather than letting it become a free-floating value. Your call. The constraint is: the kernel should refuse to validate a Deposit whose `touched_files` includes paths outside its Plan's claims, and that refusal should be observable as a `Validation::Rejected` with a meaningful reason.

- Add a compile-fail test for "Run reaches Completed without going through Running." Exact form is yours; the law is "you cannot fabricate a `Run<Completed>` from a `Run<Pending>`."

- Add a compile-fail test for "Validation accepts a Deposit that touched files outside its Plan's claims." This may need to be a different shape than the existing compile-fail tests because it's about runtime behavior, not type construction — if you can't make it a compile-fail test, make it a deterministic integration test in `watershed-distributary/tests/` or a new `watershed-tributary/tests/` directory, and add the corresponding entry to `pressure_tests()` in `watershed-contracts/src/lib.rs`. If the kernel's discipline says it should be compile-fail rather than runtime, do that instead and tell me how.

- Update `full_ceremony_produces_baseline` in `lawful_motion.rs` to walk through whatever Run lifecycle you land on, so the canonical full-ceremony example continues to demonstrate the actual law.

- Update `run_id_identity.rs` if your changes to dispatch shift its surface (e.g., if dispatch now returns something other than `Run<Pending>` or if the carrier of intent+claims changes shape).

- Update `pressure_tests()` in `watershed-contracts/src/lib.rs` to add the new pressure tests with appropriate `name` / `claim` / `enforced_by` strings.

- Regenerate schemas with `cargo xtask schemas`. Diffs are expected if contract surfaces shifted; that's fine.

---

## Constitutional constraints

These are non-negotiable. If something below blocks the work, stop and tell me.

- **The Design Gate applies.** For every new type, field, transition, constructor, or dependency, you must be able to answer: what legal motion creates or proves it? what later legal motion consumes or depends on it? what illegal motion becomes impossible because it exists? what compile-fail or integration test demonstrates that law? If you can't answer all four for something you're about to add, don't add it.

- **Compile-fail tests are constitutional evidence.** Every important law gets a trybuild test or — if compile-fail isn't the right shape — a deterministic integration test paired with a `PressureTest` entry in `watershed-contracts`.

- **The institution holds.** Do not weaken a boundary because a test is awkward. Do not add a public constructor for an authoritative state because the lifecycle would be easier with one. Do not add a bypass because the existing shortcut was convenient.

- **Crate boundaries hold.** `watershed-distributary` constructs `Plan` and `Run` states; `watershed-tributary` constructs `Validation`, `Merge`, `Baseline` states; `watershed-contracts` owns portable data. Neither side fabricates the other's authoritative states. The existing `SettlementSealed` and `WorkerProducesDeposit` compile-fail tests already enforce this; the new work must not break those tests.

- **The kernel stays in-memory.** No subprocesses, no worktrees, no filesystem reads at validation time, no registry persistence, no CLI. Validation reads from in-memory values only.

- **DESIGN_DEBT items 1–3 stay deferred.** `WorkClass`, `VerificationSpec`, `RollbackSpec` are not promoted by this Brief. They remain typed in `watershed-contracts` but unused by any Plan transition.

  **In particular, `VerificationSpec` stays deferred specifically because the claims-integrity check this Brief adds is structural (kind A above), not Plan-declared (kind B). `VerificationSpec.checks: Vec<String>` is shaped for the Plan-declared kind; threading the structural claims-integrity check through `VerificationSpec.checks` would let a Plan omit the entry and bypass the rule. The kernel exists to refuse exactly that kind of bypass.** The Brief that should promote `VerificationSpec` is the future one that adds "Plan declares its required verification checks; validation runs them and refuses unless they pass" — a (B)-shaped Brief. This Brief is (A)-shaped and does not need `VerificationSpec`.

  If you find yourself reaching for `WorkClass` or `RollbackSpec` to make this work clean, stop and tell me — that's a signal the Brief's policy needs revision. If you find yourself reaching for `VerificationSpec` because you think the structural-vs-declared distinction is wrong or because you see a Rust-idiomatic way to make claims integrity un-bypassable while still routing it through `VerificationSpec.checks`, stop and argue the distinction itself. The conversation is about whether (A) and (B) really are distinct kinds, not about whether to freelance a promotion.

- **All existing compile-fail tests must continue to pass.** That includes `dispatch_unvalidated_plan`, `dispatch_twice`, `construct_merge_from_distributary`, `construct_baseline_from_distributary`, `merge_rejected_validation`, `baseline_without_merge`, `skip_intent_recovery`, `construct_completed_run_directly`, `construct_validated_plan_directly`. If your changes break any of these, the constitutional surface shifted and you need to stop and tell me before adapting them.

- **The full ceremony in `lawful_motion.rs` must still produce a Baseline.** Update it to walk the new lifecycle; do not delete it.

---

## Write scope

Paths Codex may write to:

- `watershed-kernel/watershed-contracts/src/lib.rs`
- `watershed-kernel/watershed-distributary/src/lib.rs`
- `watershed-kernel/watershed-tributary/src/lib.rs`
- `watershed-kernel/watershed-distributary/tests/lawful_motion.rs`
- `watershed-kernel/watershed-distributary/tests/run_id_identity.rs`
- `watershed-kernel/watershed-distributary/tests/` (new tests if needed)
- `watershed-kernel/watershed-tributary/tests/` (new directory + new tests if needed)
- `watershed-kernel/tests/compile_fail/*.rs` (new compile-fail tests; existing ones updated only if a constitutional surface shifted, which requires a stop-and-tell-me)
- `watershed-kernel/schemas/*.json` (regenerated via `cargo xtask schemas`)
- `watershed-kernel/Cargo.lock` (touched only if a workspace dep shifts; the Brief does not anticipate any)

Paths Codex may NOT write to:

- Anywhere outside `watershed-kernel/`
- The kernel's `AGENTS.md`, `PRESSURE_TESTS.md`, `DESIGN_DEBT.md`, `README.md` (those are governance-layer docs; updates to them are Watermaster-side post-Brief integration work, not Engineer scope)

---

## Verification gates

All four must pass before returning:

1. `cargo fmt --all -- --check` clean.
2. `cargo clippy --workspace --all-targets -- -D warnings` clean.
3. `cargo test --workspace` passes. This includes:
   - All existing compile-fail tests (`constitutional.rs` via trybuild over `tests/compile_fail/*.rs`).
   - The `run_id_identity.rs` tests (updated if the dispatch surface shifted).
   - The `full_ceremony_produces_baseline` test (updated to walk the new lifecycle).
   - Any new tests this Brief introduces.
4. `cargo xtask schemas` runs to completion. If schemas changed, that's expected; the new bytes should be in the return.

Run these from `/Users/jakegearon/projects/watershed/watershed-kernel/`.

---

## Return shape

Structured return matching the chain's `return-{N}.md` audit shape:

- **Summary**: 2–4 sentences naming what landed.
- **Files written**: every path touched, with brief description.
- **Lifecycle decisions**: which Rust shape you chose for the Run lifecycle transitions and the claims carrier, and why. (This is where you teach me what the right shape was.)
- **Validation surface decisions**: what `validate(...)` looks like now and why that shape best fits the kernel's discipline.
- **Verification gate results**: output (or summary) of each of the four `cargo` commands.
- **Compile-fail tests added**: name, claim, what illegal motion is now impossible.
- **Pressure tests added to `pressure_tests()`**: same.
- **Flags**: anything you noticed during the work that the Brief should have anticipated but didn't, anything you had to push back on, anything in DESIGN_DEBT that almost got promoted (and why you held off).
- **Anything you'd change about the Brief**: what was unclear, over-prescriptive, or wrong. The Brief style is new (policy direction, not Rust prescription); your read on whether it served you well is part of the Brief's own pressure-testing.

---

## Push-back is welcome

The Brief style is: I'm telling you the policy direction, you're telling me how it codes in Rust. If you think:

- The Brief's three items (worker lifecycle, claims carrier, claims integrity at validation) shouldn't be done together,
- The suggested approach has a Rust-idiom problem I didn't see,
- The constitutional constraints contradict each other or the kernel's existing discipline,
- A different shape than the one I sketched would serve the kernel better,
- Promoting `WorkClass` or `RollbackSpec` would actually serve this work and the Design Gate test would pass for it,
- The structural-vs-declared distinction (A vs B in the "What should exist" section) is wrong, and `VerificationSpec` is the right home for claims integrity after all,

— stop, don't implement, and tell me. The kernel asks for reasoning before motion. Tokens are bountiful; authority is scarce. Spend the reasoning.

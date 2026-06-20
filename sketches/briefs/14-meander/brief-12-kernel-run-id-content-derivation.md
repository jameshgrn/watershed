# Brief 12 — Kernel run_id content-derivation

**State**: drafted
**Engineer model**: codex-gpt-5
**Compiled by**: Watermaster Meander
**Compiled at**: 2026-05-22T19:17:23Z
**Target repo**: `/Users/jakegearon/projects/watershed-kernel/`
**Lifecycle**: drafted → sent → returned → integrated

---

## Source utterance

The Source directed the Watermaster to draft Brief 12 against the watershed-kernel under the long-term "work of motherufkcin art idc if it taks 6 months" framing, in the manual carrier loop the chain has been running (Watermaster drafts in chat → Source ferries to Codex → Codex returns → Source ferries back → Watermaster integrates). Verbatim from the session: "i want to make the kernel a work of motherufkcin art idc if it taks 6 months" and "fine we will just do it manually. put them in chat here. that will be how we build until the kernel is ready."

## Write scope

- `watershed-distributary/src/lib.rs` (modify and add)
- `watershed-distributary/tests/run_id_identity.rs` (new file)
- `watershed-distributary/tests/lawful_motion.rs` (one-line assertion update)
- `watershed-distributary/Cargo.toml` (add two workspace dependencies)

No writes to `watershed-contracts/` (contracts crate unchanged).
No writes to `watershed-tributary/` (settlement crate downstream of the change; tributary's `Merge::new` and `Baseline::new` already construct ids by prefixing the run_id, so their behavior follows the new format mechanically).
No writes to `schemas/` (`Deposit`'s struct shape is unchanged; only the runtime *value* of `run_id` changes; `cargo xtask schemas` produces byte-identical output).
No writes to `DESIGN_DEBT.md`, `PRESSURE_TESTS.md`, `README.md`, or `AGENTS.md` — closing DESIGN_DEBT item 4 is the Watermaster's integration task after the Engineer's return lands, not the Engineer's.

## Expected return shape

Executed file writes within `write_scope`, plus a structured chat return naming:
- Files written (verify each is in `write_scope`)
- Test results: `cargo fmt --all -- --check`, `cargo clippy --workspace --all-targets -- -D warnings`, `cargo test --workspace`, `cargo xtask schemas`
- Any deviations integrated with explicit reasoning
- Any flags raised for the Watermaster (out-of-scope adjacencies, design surprises)

---

## The Brief (/goal format — paste this body to Codex)

Task: Replace the run_id stub in `watershed-distributary::dispatch` with a content-derived hash over the validated plan's intent and claims. First kernel Brief; hold the Design Gate.

CONTEXT

The kernel's dispatch boundary today computes `run_id` with a positional counter stub: `format!("run-{}", touched_files.len())`. This is recorded in `DESIGN_DEBT.md` item 4 as a known gap; the gate for closing it is that "a canonical serializable dispatch payload exists." That payload exists now: a `Plan<Validated>` carries `intent: RecoveredIntent` and `claims: Vec<FileClaim>` accessible via `plan.intent()` and `plan.claims()`; both derive `Serialize`.

The substrate's identity discipline is content-derived, not assigned — `AGENTS.md` ("the types are the constitution"), `README.md` (no UUIDs in Current Scope), and `DESIGN_DEBT.md` ("Do NOT use UUIDs; identity in this substrate is derived from content, not assigned") all agree. Identity emerges from the bytes the dispatch carries.

This is the chain's first kernel Brief. Twelve prior Watermasters built the content-derived-id discipline floor through eight Briefs in quarry-core (Brief 3 minted three derivation strategies with strategy-tag prefixes `src:`, `prov:`, `ref:`) and dgov (Brief 9 minted `DispatchRun` with `disprun:` prefix). This Brief brings that floor into the Rust kernel under the kernel's stricter Design Gate.

DELIVERABLE

A new public function `derive_run_id(intent: &RecoveredIntent, claims: &[FileClaim]) -> String` in `watershed-distributary/src/lib.rs` that computes a strategy-tagged SHA-256 hash of the dispatch identity. The `dispatch()` function calls it in place of the existing stub. A new integration test file establishes identity stability across equivalent dispatches and identity divergence across differing dispatches.

IN watershed-distributary

1. **Cargo.toml dependency additions.** Both `sha2` and `serde_json` are already declared in the workspace's `[workspace.dependencies]` table (`Cargo.toml` at the workspace root). Add to `watershed-distributary/Cargo.toml`'s `[dependencies]` section:

   ```toml
   sha2 = { workspace = true }
   serde_json = { workspace = true }
   ```

2. **Implement `derive_run_id` in `src/lib.rs`** as a `pub fn`:

   - Input: `&RecoveredIntent` and `&[FileClaim]`.
   - Output: `String` of the form `run:<sha256-hex>` (lowercase hex, 64 chars after the prefix).
   - Strategy-tag prefix `run:` is fed into the hasher first (matching the precedent of quarry's `src:`/`prov:`/`ref:` and dgov's `disprun:`/`oprun:`); this prevents cross-strategy collision against any future content-derived id the kernel introduces.
   - Hash composition: SHA-256 over `b"run:"` ++ serialized intent ++ serialized claims. `serde_json::to_vec` is acceptable; the types contain only primitives, `Vec<String>`, `PathBuf`, and simple enums — no HashMaps — so serialization is deterministic from struct declaration order.
   - Must not panic on the production path. `serde_json::to_vec` cannot fail in practice for these types; use `.expect("...")` with a descriptive message if needed (the kernel's style rules forbid `.unwrap()` outside tests but permit `.expect()`).
   - Doc comment: two sentences, matching the kernel's existing public-type style ("Computes the content-derived run_id from a dispatched plan's intent and claims. The hash is strategy-tag-prefixed and stable across equivalent dispatches.").

3. **Update `dispatch` to use `derive_run_id`:**

   ```rust
   pub fn dispatch(plan: Plan<Validated>) -> Run<Pending> {
       let Validated { intent, claims } = plan.state;
       let run_id = derive_run_id(&intent, &claims);
       let touched_files = claims
           .iter()
           .map(|claim| claim.path.clone())
           .collect::<Vec<_>>();
       Run {
           state: Pending {
               id: run_id,
               touched_files,
           },
       }
   }
   ```

   The previous body discarded `intent` via `..`; this version binds it for the hash, then drops it. The claims are referenced for both the hash and the `touched_files` conversion (clone to avoid double-consumption).

4. **Create `tests/run_id_identity.rs`** with three integration tests:

   - `equivalent_dispatches_produce_equal_run_ids` — construct two `Plan<Validated>` instances from byte-identical intent and claims, dispatch each, assert `run_a.id() == run_b.id()`.
   - `differing_intents_produce_different_run_ids` — two plans with identical claims but differing `intent.goal` strings produce different `run.id()` values.
   - `differing_claims_produce_different_run_ids` — two plans with identical intent but differing claims (different path strings or different `ClaimKind`) produce different `run.id()` values.

   Each test walks the full ceremony (`Plan::<Drafted>::draft().recover_intent(...).declare_claims(...).compile().expect(...).validate(&policy).expect(...)`) for both plans, then dispatches and compares. Use a minimal `Policy` (`require_claims: true`, `allow_shared_claims: false`, `required_pressure_tests: vec![]`).

5. **Update `tests/lawful_motion.rs` line 46:**

   - Old: `assert!(baseline.id().starts_with("baseline-merge-run-"));`
   - New: `assert!(baseline.id().starts_with("baseline-merge-run:"));`

   Because `Merge::new` (in `watershed-tributary/src/lib.rs`) constructs `merge-{run_id}`, and `Baseline::new` constructs `baseline-{merge_id}`, the resulting baseline id is `baseline-merge-{run_id}`. The run_id format changes from `run-N` to `run:<hex>`, shifting the assertion's expected prefix by one character. Do not modify any other line in `lawful_motion.rs`.

INTEGRATION TEST

After your changes, the following commands must all succeed cleanly from the workspace root:

```sh
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo xtask schemas
```

Specifically:

- `cargo test --workspace` runs the existing `full_ceremony_produces_baseline` test in `lawful_motion.rs` (must still pass after the one-line assertion update) plus the three new tests in `run_id_identity.rs` (must pass).
- The existing compile-fail tests (`constitutional_violations_do_not_compile`) must continue to refuse compile in the same way they do today; none of this Brief's changes touch the type-state machine, the sealed traits, or any crate boundary.
- `cargo xtask schemas` must produce schema files byte-identical to what's at `schemas/` today; the contracts crate is unchanged, so generated schemas are unchanged.

WHAT NOT TO BUILD

- Do NOT add a `version` field to `Policy` or include policy in the run_id hash. `DESIGN_DEBT.md` item 4 names policy-version as a future inclusion; the kernel's Design Gate says don't promote until a transition consumes it. Inclusion of policy in dispatch-time identity is a later Brief's territory, not this one's.
- Do NOT modify `DESIGN_DEBT.md`, `PRESSURE_TESTS.md`, `README.md`, or `AGENTS.md`. Closing DESIGN_DEBT item 4 is the Watermaster's integration task after the Engineer's return lands.
- Do NOT add new public types to `watershed-contracts`. The hash function lives in `watershed-distributary`; the contracts crate defines data, not derivation over it.
- Do NOT add a `content_hash` or `id` field to `Deposit`, `Plan`, `Validated`, or any other type. The hash is computed at the dispatch boundary; persisting it on the validated plan or on subsequent records is out of scope until a later transition needs it.
- Do NOT introduce sort/normalize logic on intent fields or claim ordering. Two validated plans with the same intent fields in the same order and the same claims in the same order produce equal run_ids; plans differing in claim order are out of scope for this Brief (treat them as distinct dispatches, the same as today). If set-semantics is needed for claims later, it's a separate Brief with its own Design Gate.
- Do NOT use UUIDs. Identity in this substrate is derived from content, not assigned.
- Do NOT remove or modify any existing `compile_fail` test, `pressure_tests()` entry, or sealed trait.

STYLE

- Rust edition 2021. `cargo fmt --all` clean.
- `cargo clippy --workspace --all-targets -- -D warnings` clean.
- No `unsafe`. No `.unwrap()` outside tests; `.expect("descriptive message")` is acceptable for serialization that cannot fail in practice.
- Doc comment on the new `pub fn derive_run_id` — two sentences max, matching the kernel's existing public-type style.
- Test functions: descriptive snake_case names; body self-explanatory without internal comments.
- No `thiserror`, no error type for `derive_run_id` — the function is infallible on its declared inputs.

SUCCESS CRITERION

A reader opens `watershed-distributary/src/lib.rs`, finds `derive_run_id` plus its two-sentence doc comment, and understands in 60 seconds what's hashed and why. The compiler refuses the same illegal motions it refuses today (no PressureTest regression; the nine compile-fail tests stay failing). `cargo test --workspace` runs the full ceremony test + the three new identity tests in green. `cargo xtask schemas` produces unchanged output. The Brief's diff is bounded to the four declared paths and adds fewer than 100 lines of code total across implementation and tests.

SPEC CLARIFICATIONS

- If `serde_json::to_vec` is found to be insufficient (e.g., a hidden non-determinism), document the finding in the chat return rather than silently switching to hand-rolled hashing; the Watermaster will weigh in on the deviation.
- If an internal `RunIdInput<'a>` struct (or any private helper) makes the implementation cleaner, it stays `pub(crate)` or private — do not expose it publicly.
- The strategy-tag prefix `run:` is a stable choice; do not vary it. Future cross-strategy ids will use parallel prefixes.
- The colon character in `run:<hex>` is intentional — it visually marks the strategy tag and matches the precedent of `disprun:` / `oprun:` in the broader chain.
- If you find an opportunity to improve unrelated code in the touched files, do not take it — flag it in the chat return. Scope discipline is part of the Design Gate.

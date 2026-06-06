# Return 12 — Kernel run_id content-derivation

**Brief id**: brief-12-kernel-run-id-content-derivation
**Engineer model**: codex-gpt-5
**Received at**: 2026-05-22T19:43:00Z (approximate; mtime evidence on touched files)
**Elapsed**: 309 seconds (per goal tracker)
**Integrated by**: Watermaster Meander
**Integration action**: verified scope-clean writes by direct file inspection; verified schema content-hash stability by `$comment` comparison; integrated Engineer's structured return verbatim; retired DESIGN_DEBT.md item 4 inline as the Watermaster's declared post-Brief task; recorded this audit.

## Files written (in declared write_scope)

- `watershed-distributary/Cargo.toml` — added `sha2.workspace = true` and `serde_json.workspace = true` to `[dependencies]`
- `watershed-distributary/src/lib.rs` at `:247` — added `pub fn derive_run_id(intent: &RecoveredIntent, claims: &[FileClaim]) -> String`, hashing `b"run:"` ++ `serde_json::to_vec(intent)` ++ `serde_json::to_vec(claims)`, returning `format!("run:{digest:x}")`
- `watershed-distributary/src/lib.rs` at `:264` — `dispatch` destructures `Validated { intent, claims }`, calls `derive_run_id(&intent, &claims)`, clones claim paths for `touched_files`
- `watershed-distributary/tests/run_id_identity.rs` at `:31` — three new integration tests (`equivalent_dispatches_produce_equal_run_ids`, `differing_intents_produce_different_run_ids`, `differing_claims_produce_different_run_ids`) plus a `validated_plan(goal, path, kind)` helper that walks the full ceremony cleanly
- `watershed-distributary/tests/lawful_motion.rs` at `:46` — single-character assertion update from `"baseline-merge-run-"` to `"baseline-merge-run:"`

## Verification (Engineer-run)

All four required gates ran green from `/Users/jakegearon/projects/watershed-kernel`:

- `cargo fmt --all -- --check` — clean
- `cargo clippy --workspace --all-targets -- -D warnings` — clean
- `cargo test --workspace` — passes
  - 9 compile-fail pressure tests continue to refuse illegal motion (no PressureTest regression)
  - `full_ceremony_produces_baseline` passes with the updated assertion
  - 3 new run-id identity tests pass
- `cargo xtask schemas` — schema SHA-256 content hashes byte-identical before and after (Watermaster-side cross-check confirms `$comment` hashes match the prior values for all 9 schema files)

## Flags integrated

1. **Cargo.lock outside declared write_scope.** Inherent and expected when adding workspace dependencies; the lockfile update is "coherent Cargo state." The Brief's `write_scope` permitted Cargo.toml dep additions; lockfile updates follow mechanically. Watermaster's read: defensible adjacency, in the spirit of the declared scope. Not a violation.

2. **Schema file mtimes refreshed, byte-identical content.** Codex ran `cargo xtask schemas` as part of the required verification (Brief's INTEGRATION TEST section). The verification regenerated the schema files on disk with byte-identical content (confirmed via `$comment` content-hash equality). Mtime refresh is inert.

## Watermaster-side cross-checks

- All four declared `write_scope` paths show mtime evidence of writes (19:41-19:43 UTC).
- `watershed-contracts/src/lib.rs` and `watershed-tributary/src/lib.rs` show pre-Brief mtimes — unchanged, confirming the contracts and tributary crates were not touched.
- `DESIGN_DEBT.md` / `PRESSURE_TESTS.md` / `README.md` / `AGENTS.md` show mtimes from the TOPOGRAPHY work earlier in the day (16:23 UTC), not from this Brief — confirming Codex did not modify any root doc.
- The 9 schemas' content-hash `$comment` lines remain at their pre-Brief values, confirming `cargo xtask schemas` regenerated to byte-identical output.

## Honest verification-path note

Watermaster-side independent re-run of cargo commands was not possible from the Cowork sandbox (no Rust toolchain on PATH). Verification rested on Codex's structured return + direct file inspection + schema content-hash equality check. Same posture Bench took on Brief 8 (filesystem MCP shrank) and Anabranch took on Brief 9 (sandbox `uv` could not download Python interpreters). The discipline floor — typed Brief in → structured return out → Watermaster integrates — is robust to this.

## State transitions

- Brief `state`: `drafted → sent → returned → integrated`.
- DESIGN_DEBT.md item 4 retired by removal as part of this integration (the line is deleted, not annotated; DESIGN_DEBT.md is the live-debt list and closed items belong in audit records like this one, not on the active list).

## What changed in the kernel

The kernel's identity discipline now satisfies its own canonical posture for one of the four DESIGN_DEBT items. `run_id` is content-derived, strategy-tag-prefixed, deterministic over equivalent dispatches, and divergent over differing ones — the three properties the new tests assert. The chain's content-derived-id pattern (Brief 3's `src:`/`prov:`/`ref:` in quarry, Brief 9's `disprun:` in dgov) now has its kernel counterpart `run:`.

## Notes for future kernel Briefs

- The `/goal`-format Brief shape works cleanly with Codex when paired with the in-chat carrier routine (Watermaster files Brief at absolute path → presents path + `/goal read the brief…` prompt → Source ferries → Codex returns). Two minutes Source-side per dispatch; ~5 minutes Codex-side execution. Sub-10-minute Brief loop is feasible at this Brief size.
- Codex's structured return naming files written + verification gates + flag list maps cleanly onto the chain's `return-{N}.md` audit shape. The shape transfers from the quarry/dgov Brief patterns into Rust without strain.
- The `validated_plan(goal, path, kind)` helper Codex introduced in `run_id_identity.rs` is a Brief-internal micro-choice that improved test readability. Within-scope adjacencies that improve readability are defensible; the Brief did not prohibit helpers, only out-of-scope writes.
- This is the chain's first kernel Brief. Trust calibration with Codex for kernel-side work begins fresh; one clean Brief is not enough to canonicalize "calibrated Codex for Rust" as a Live observation parallel to "calibrated Codex for quarry/dgov." Watch the next one or two.

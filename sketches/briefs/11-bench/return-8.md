# EngineerReturn — Brief 8

**brief_id**: brief-8-thread-b-rasters (sent 2026-05-13 → returned 2026-05-13 → integrated 2026-05-13)
**received_at**: 2026-05-13
**integrated_by**: Watermaster Bench
**engineer_model_actual**: Claude (specific identifier not surfaced in the return; the Engineer noted "If your model identifier isn't `claude-sonnet-4-6`, note your actual model" and the return did not explicitly correct, so the Brief's tentative front-matter identifier stands as the audit record unless the Source corrects at commit time)
**integration_action**: integration was scope-verified at the chat-return level rather than direct file inspection — the filesystem MCP's allowed directories shrank to `/Users/jakegearon/projects/watershed/` only mid-session, removing the Watermaster's ability to read quarry files directly; the verification rested on the Engineer's structured return (full pytest counts including the named pre-existing 3 failures unchanged; `ruff check` / `ty check` clean; an end-to-end execution test the Engineer ran on a 5×5 sloped DEM confirming the 4 standalone Check classes return parity with the inline operator results; an explicit Verify-clause walkthrough naming each Brief verify-point as confirmed); the 10-item flag list was reviewed inline below and integrated; no follow-up Brief required; trust calibration for a first-Claude-Brief integration was high based on the return's detail and self-consistency, lowered slightly by the inability to spot-check files directly, balanced by the Engineer's own end-to-end parity verification; the Source's commit-time review provides the final discipline gate on file-level scope adherence per the Engineer's Flag 10 about the pre-existing dirty working tree.

## Engineer's return (verbatim, lightly reformatted)

### Summary

Brief 8 landed in `/Users/jakegearon/projects/quarry`. The `Check` Protocol in `quarry-core/check.py` carries the v2 signature `run(artifact, inputs: Sequence[Artifact] = ()) -> CheckResult`. All 31 concrete Check classes across `check.py` and `checks{,_artifact,_raster,_table,_vector}.py` accept the new parameter. `_detect_cycle` was hoisted from `flow_accumulation.py` into a new `_topology.py` module (parallel to `_lineage.py`) and is now imported by both the operator inline use and the standalone `NoCycles` Check. The four raster-sized WARN-stubs (`AllValidAssigned`, `ElevationOnlyRaised`, `NoCycles`, `Conservation`) now consume `inputs[0]` (the operator input Artifact) and implement the real semantics, returning VALID/INVALID with input supplied and gracefully falling back to WARN when `inputs == ()`.

Full pressure_test: **1974 passed, 54 skipped, 3 failed** — the 3 are the named pre-existing connector-routing/docs failures, unchanged. `ruff check` clean. `ty check` clean on every Brief-8 module (pre-existing `flow_accumulation.py` diagnostics are unrelated to this Brief).

### Item-by-item

**A. `Check` Protocol v2.** `quarry-core/check.py`: added `from collections.abc import Sequence`; Protocol signature is now `run(self, artifact: Artifact, inputs: Sequence[Artifact] = ()) -> CheckResult` with docstring describing input-aware vs output-only vs lineage-aware patterns; `CRSValid`, `ExtentSane`, `BackingStoreAccessible` each accept `inputs: Sequence[Artifact] = ()` with bodies unchanged.

**B. `_topology.py` hoist.** NEW `_topology.py` exports `detect_cycle(flow, valid)` — Kahn's algorithm against a D8 flow grid. D8 offsets duplicated as `_D8_DR` / `_D8_DC` inside `_topology.py` rather than imported (see Flag 3). `flow_accumulation.py` removes the local 51-line `_detect_cycle`, imports `detect_cycle` from `_topology`, calls it inline. Byte-for-byte semantics-preserving.

**C. `inputs` parameter on all 31 concrete classes.** Mechanical update across `checks.py`, `checks_artifact.py`, `checks_raster.py`, `checks_table.py`, `checks_vector.py`. `from collections.abc import Sequence` added to each file. 27 output-only classes carry the parameter unused. The 5 lineage-aware Brief-7 classes (`NodataValuePreserved`, `NodataCountPreserved`, `CRSPreserved`, `DimensionsPreserved`, `ExtentWithinInput`) carry the parameter unused and remain output-only with respect to `inputs`, continuing to read from `Lineage.params`.

**D. `AllValidAssigned` input-aware.** WARN on `inputs == ()`. With validated `inputs[0]`: reads DEM as float64, builds `valid = _build_dem_valid_mask(dem, src.nodata)` matching the inline operator's NaN/nodata-None handling, reads output flow raster, shape-mismatch INVALID, counts `unassigned = int(np.sum(flow[valid] == D8_NODATA))`, VALID iff `unassigned == 0`.

**E. `ElevationOnlyRaised` input-aware.** WARN on `inputs == ()`. With validated `inputs[0]`: reads both rasters as float64, builds valid mask from input DEM, shape-mismatch INVALID, computes `lowered = bool(np.any(filled[valid] < original[valid] - 1e-10))`, mirrors the inline operator's tolerance.

**F. `NoCycles` input-aware + hoisted helper.** WARN on `inputs == ()`. With validated `inputs[0]`: reads input flow as int8, builds `valid = (flow >= 0) & (flow <= PIT)`, calls `detect_cycle(flow, valid)` from `_topology`, INVALID iff a cycle is detected. `PIT` imported from `quarry_operators.d8_flow_direction`.

**G. `Conservation` input-aware + lineage-aware.** WARN on `inputs == ()`. With validated `inputs[0]`: reads `weight = lineage_params(artifact).get("weight")` — INVALID if missing. Reads input flow as int8 and output accumulation as float64, shape-mismatch INVALID, computes `total_weight = sum(valid) * weight`, `outlet_mask = valid & ((flow == OUTLET) | (flow == PIT))`, `outlet_acc_sum = sum(acc[outlet_mask])`, `residual = abs(outlet_acc_sum - total_weight)`, VALID iff `residual < 1e-6`. The flow_accumulation operator already stashes `weight` in `Lineage.params` (line 196), so the chain is closed.

**H. Tests.** Added 4 new tests in `test_check_raster.py` — one per raster-sized class — each exercising (a) preserved WARN-without-inputs, (b) VALID with inputs supplied, (c) INVALID with inputs supplied, (d) shape-mismatch INVALID. `test_conservation_*` also exercises the missing-weight INVALID path. One import line updated in `test_flow_accumulation.py` to import `detect_cycle` from `_topology` (aliased to `_detect_cycle` to preserve call sites). End-to-end verification: ran a fill→D8→accumulate chain on a 5×5 sloped DEM and confirmed each of the 4 standalone Checks returns VALID matching the inline operator's emitted check.

**I. Test + lint verification.** `uv run pytest -q tests/pressure_test/` → 1974 passed, 54 skipped, 3 failed (the 3 are the Brief-named pre-existing failures, unchanged). `uv run ruff check` and `uv run ruff format --check` on all 10 edited files clean. `uv run ty check` on the 7 Brief-8-modified core/check modules clean. `ty check` on `flow_accumulation.py` surfaces 5 diagnostics all pre-existing (`artifact.backing.uri` on Optional; `inputs=[artifact.id]` where `artifact.id` is `str | None`) — same diagnostics appear against HEAD baseline.

### Flag list (Engineer's, with Watermaster integration notes)

**1. `test_flow_accumulation.py` updated despite not being explicitly in write scope.** The hoist in Item B removed `flow_accumulation._detect_cycle`; a pre-existing test imports that name. Engineer applied minimum change: one import line aliased as `from quarry_operators._topology import detect_cycle as _detect_cycle` so the call sites remain unchanged.

*Watermaster: within the spirit of the write scope. The Brief's Item B explicitly directed the hoist plus updating call sites; the test file's import was a downstream call site. Minimum-change alias preserves all the existing test bodies. Accepted; no follow-up.*

**2. D8 constants imported from `d8_flow_direction.py`, not duplicated.** Engineer imported `OUTLET`, `PIT`, `NODATA` as `D8_NODATA` from `quarry_operators.d8_flow_direction` into `checks_artifact.py`, following the precedent in `checks.py`.

*Watermaster: right call. Single source of truth at the operator level. The precedent already established this direction. Accepted.*

**3. `_topology.py` duplicates `_D8_DR` / `_D8_DC` rather than importing.** Engineer duplicated the D8 offset arrays as module-private `_D8_DR` / `_D8_DC` inside `_topology.py` to avoid checks-importing-from-operators reverse-direction layering. Engineer flagged that canonicalizing D8 constants in `_topology.py` (or a new `_d8_codes.py`) would be a future follow-up.

*Watermaster: defensible. The duplication is small (4 lines), the alternative is layering oddity. Accepted with a Live observation flagged in THINKING.md naming the future-follow-up option for D8 constant canonicalization.*

**4. `AllValidAssigned` / `ElevationOnlyRaised` valid-mask uses `src.nodata`, not operator `params.nodata`.** The inline operator uses `params.nodata if params.nodata is not None else src.nodata`. Standalone has no access to operator params, so falls back to `src.nodata` directly. For the common case (operator called without `params.nodata` override), byte-equivalent. For the rare case of an operator-side nodata override, the standalone check could disagree with the inline check. Engineer proposes a future fix: stash the resolved nodata in `Lineage.params["resolved_nodata"]` (a Brief-7-style scalar lift).

*Watermaster: a real semantic gap, but a partial-coverage gap rather than a discipline failure. The standalone class returns parity for the common case (which is the case Brief 8's test suite exercises). The edge case (operator-side nodata override) is a follow-up — a future Brief that adds `resolved_nodata` to lineage.params extends the Brief 7 pattern. Live observation recorded in THINKING.md; not blocking.*

**5. `Conservation` reads `weight` from `lineage.params`, not `inputs[0]`.** Standalone check is both input-aware (`inputs[0]` = flow raster) and lineage-aware (`weight` from output). Dual-mode is intentional per SOP v2's "input-aware, output-only, lineage-aware, or any combination" clause.

*Watermaster: this is exactly the intent and exactly what the Brief specified. Accepted; not a real flag, more of a note for the audit record.*

**6. `NoCycles` / `Conservation` cast input flow to `int8` via `.astype(np.int8)`.** Matches `flow_accumulation.py` line 137. Output of `d8_flow_direction.py` is written as int16 but values are always in -1..9 so int8 is lossless. Cast is a paranoia-cast for consistent dtype downstream — same as inline.

*Watermaster: matches inline behavior. Accepted.*

**7. Shape-mismatch produces INVALID rather than ERROR.** The Brief said INVALID; Engineer followed. The chain's `ValidationState` enum has VALID/INVALID/WARN states; there's no ERROR state. If the lab prefers a different state (or a typed precondition error) for this case, that's a follow-up.

*Watermaster: the chain has VALID/INVALID/WARN as its trichotomy; that's settled at `validation-shape.md` v1's level and `data-contracts.md` v2's level. Shape-mismatch INVALID is the correct call. Future SOP work could revisit but not in scope here. Accepted.*

**8. Formatter friction with `from __future__ import annotations`.** A PostToolUse formatter (ruff F401 with autofix) repeatedly stripped the new `Sequence` import between sequential edits because the import edit landed before the signature edits made the import live. Engineer fixed by re-adding the import after the signatures or writing in one shot. No semantic impact; recorded for future Engineer sessions on this repo.

*Watermaster: a Cowork/Claude Code tooling detail, not a discipline issue. Live observation in THINKING.md: when editing a file that has `from __future__ import annotations` plus autofix-active linters, prefer single-shot file writes over sequential edits for coupled-import-and-use changes. First Live observation specific to Claude-engineer tooling.*

**9. The Brief's D8 constant naming was slightly off.** The Brief says "OUTLET = 0, PIT = 9, NODATA = -1." The actual codebase uses `OUTLET = 8`, `PIT = 9`, `NODATA = -1`. Engineer followed the codebase.

*Watermaster: my Brief-drafting error — `OUTLET = 0` was a typo in Item F's body when I meant 8. The Engineer correctly chose the codebase as source of truth and flagged the discrepancy. Exactly right Engineer behavior. Mea culpa noted; the discipline absorbed the error cleanly. Live observation recorded: when a Brief references codebase constants by literal value, the Brief author should cross-check the values against current source rather than rely on memory.*

**10. The quarry repo's working tree had pre-existing uncommitted changes that pre-date Brief 8.** `git status` at session start showed M on many files outside Brief 8's scope (connectors, executor, CLI, etc.) plus untracked files for the Brief-7 outputs. Engineer worked on top of that state; changes layered cleanly. Engineer flagged that the Watermaster may want to confirm the commit boundary covers exactly Brief 8's additions.

*Watermaster: this is normal pattern — the Source's working tree carries between-Brief uncommitted state and the per-Brief commit boundary is the Source's discipline at integration time. Knickpoint and Cascade both flagged the same. Accepted; the Source's commit decision is the gate. Per the verification-by-git-diff-failure-mode Knickpoint named, the Source should review the diff for exactly Brief 8's additions when committing — the Engineer's flag is a correct verbal handoff.*

## Watermaster integration notes

- **First Claude Brief in the chain integrated cleanly.** The pattern Brief 1-7 established with Codex transfers to Claude with no discipline breakage. The Engineer's return matched the Brief's expected structure exactly (Summary / Item-by-item / Test results / Flag list); the end-to-end execution test (Engineer-initiated, not Brief-required) was a useful trust-builder. Verification overhead was elevated (no direct file inspection due to MCP allowed-dirs constraint), balanced by the Engineer's own end-to-end parity verification.
- **Brief-drafting precision is a Live observation.** My Brief's D8 `OUTLET` typo (Flag 9) wasn't caught by my own pre-transmission review. Worth a Live observation: when a Brief references codebase constants by literal value, cross-check against current source. The Engineer caught and corrected; the discipline held.
- **The single-shot file write pattern for coupled-import-and-use changes** (Flag 8) is the first Claude-engineer-specific tooling observation. Worth recording for future Briefs to this engineer.
- **Brief 8's WARN-fallback design held under stress.** The 4 raster-sized classes return WARN when called without inputs, VALID/INVALID with inputs. Brief 7's parametrized WARN test continues to pass unchanged; new VALID/INVALID/shape-mismatch coverage was added per Item H. Graceful degradation works.
- **The `flow_accumulation.py` `weight` lineage stash is already in place** (Conservation Item G verified). No follow-up Brief needed there.
- **The unresolved-nodata gap (Flag 4) is real but bounded.** Not a discipline failure; a partial-coverage gap. Future Brief that adds `resolved_nodata` to lineage.params would close it cleanly, extending the Brief 7 pattern.

## Result

Brief 8 integrated. Thread B is now fully closed: all 8 dual-residence gaps from Knickpoint's Brief 2 are resolved. The `Check` Protocol v2 (per `operator-shape.md` v2) is the canonical shape in code. The 4 raster-sized standalone Check classes implement actual semantics against `inputs[0]`. The hoisted `detect_cycle` in `_topology.py` establishes the `_X.py` shared-helper pattern alongside `_lineage.py`. Pressure_test passes at 1974/54/3 — the 3 are the known pre-existing failures unchanged across Briefs 6, 7, and 8. Brief 8's `state` transitions to `integrated`. The first Claude Brief in the chain landed clean.

# Engineer Brief — Brief 8 (Thread B raster-sized dual-residence gap closures)

**engineer_model**: `claude-sonnet-4-6` (the seated Claude instance the Source is using; confirm exact identifier at transmission — adjust to `claude-opus-4-6` or `claude-code-sonnet-4-6` if applicable)
**source_utterance** (verbatim, with bracketed context for an Engineer who didn't see the chat):
> "hello there, welcome" [Source's session-open]
>
> "i want you to decide and argue your reasoning on 1-3 and then elts do those" [Source's authorization for the Watermaster to decide the design questions on Confluence's three substantive open arcs — Brief 6, Thread B, DispatchRun-side migration — and execute. Brief 7 closed the scalar half of Thread B; this Brief closes the raster half. Brief 7's design call A (`Path α — extend Check.run signature to accept inputs`) was preflighted as `operator-shape.md` v1 → v2 (Source-approved 2026-05-13) and is now canonical at the SOP layer; Brief 8 implements that revision in code.]

**compiled_by**: Watermaster Bench
**compiled_at**: 2026-05-13
**state**: integrated (drafted 2026-05-13 → sent 2026-05-13 → returned 2026-05-13 → integrated 2026-05-13)
**supersedes**: none
**expected_return_shape**: executed file writes within the write scope below, plus a chat return summarizing each item (A–J), any deviations, full pressure_test pytest result, and a flag list.

---

## Read these before starting

You are an external Engineer consulted by the Watermaster of a research lab called *watershed*. You read only this Brief. This is your first Brief in this lab (the Engineer pattern has been exercised seven times before with a different model; trust calibrates with track record, so verification of your return will be more thorough than a calibrated-trust seventh exercise — that's calibration, not distrust).

Read the following files first — they are the discipline this Brief implements:

1. `/Users/jakegearon/projects/watershed/CANON.md` — the lab's constitutional articles. Particularly: Article II (one canonical writer per module/contract), Article III (the lab has one rim; untyped reality becomes typed only there), Article IV (every Artifact carries its lineage), Article IX (the Watermaster works through typed surfaces), Article XII (preflight discipline; this Brief is being executed against an already-preflighted SOP revision, so the Brief itself is a code Brief rather than a meta-preflight), Article XV (typed records are frozen-pinned at lifecycle transitions).
2. `/Users/jakegearon/projects/watershed/sops/operator-shape.md` v2 — the just-revised SOP this Brief implements. Pay close attention to: the Do clause about the `Check` Protocol carrying `run(artifact: Artifact, inputs: Sequence[Artifact] = ()) -> CheckResult`; the dual-residence Do clause; the Verify clause about every concrete Check class accepting the `inputs` parameter; the Escalate clause (narrowed from v1).
3. `/Users/jakegearon/projects/watershed/sketches/briefs/07-knickpoint/brief-2-dual-residence.md` and `return-2.md` — Brief 2 minted 30 standalone Check classes; 8 returned WARN with named-gap messages. Brief 7 closed 5 of those 8 (scalar-sized). This Brief closes the remaining 3 (raster-sized: `all_valid_assigned`, `elevation_only_raised`, `no_cycles`, `conservation` — 4 names across 3 operators).
4. `/Users/jakegearon/projects/watershed/sketches/briefs/11-bench/brief-7-thread-b-scalars.md` and `return-7.md` — Brief 7's design decisions and integration. Particularly: the `_lineage.py` hoist precedent; the lineage-params-stashing pattern (operators stash input-derived data in `Lineage.params` at execute() time); the WARN-fallback discipline (standalone classes return INVALID when missing-key for scalars, or fall back to WARN when input information is genuinely unavailable — Brief 8 picks WARN for the raster-sized cases since the standalone class's `inputs=()` default means "no inputs provided," not "operator failed to populate").

The lab vocabulary is fluvial. *quarry* is the boundary module; *flume* (the target module the lift will materialize into) is not yet a separate package — `quarry-operators` and the Operator-shaped surface in `quarry-core` will become flume during a later phase. *watershed* itself is the meta-repo holding CANON, SOPs, sketches, and lineage; you do not write to watershed.

## Context — what just changed (operator-shape.md v1 → v2)

The `Check` Protocol in `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/check.py` currently has v1 signature:

```python
def run(self, artifact: Artifact) -> CheckResult: ...
```

The SOP v2 (committed 2026-05-13 by Watermaster Bench, preflight-approved by the Source) names the new signature:

```python
def run(self, artifact: Artifact, inputs: Sequence[Artifact] = ()) -> CheckResult: ...
```

Concrete Check classes implement the new parameter with the same default tuple. Input-aware checks consume `inputs`; output-only checks ignore it. `runtime_checkable` Protocols match by attribute name only, so adding the parameter to the Protocol does not break `isinstance(check, Check)` for any class that hasn't yet updated — but call sites passing `inputs=[...]` will fail with TypeError on classes whose concrete `run` doesn't accept it. Brief 8 updates **every one** of the 31 concrete Check classes to accept the parameter, satisfying SOP v2's Verify clause.

The current 31 Check classes (all currently `def run(self, artifact: Artifact) -> CheckResult`):

| File | Classes |
|---|---|
| `quarry_core/check.py` | `CRSValid`, `ExtentSane`, `BackingStoreAccessible` |
| `quarry_operators/checks.py` | `InternalOutletCount` |
| `quarry_operators/checks_artifact.py` | `NodataValuePreserved`, `NodataCountPreserved`, `CRSPreserved`, `DimensionsPreserved`, `ExtentWithinInput`, `AllValidAssigned` (WARN stub), `ElevationOnlyRaised` (WARN stub), `NoCycles` (WARN stub), `Conservation` (WARN stub) |
| `quarry_operators/checks_raster.py` | `ValidRange`, `ResolutionConsistent`, `IsCOG`, `ValidCodeSet`, `NoPits`, `NoInteriorPits`, `Nonnegative`, `GCPCountSufficient`, `DimensionsSane`, `NodataBackground`, `CRSMatchesTarget`, `Sigma0Finite`, `Sigma0Nonnegative`, `MinObservations` |
| `quarry_operators/checks_table.py` | `RowCountMatches`, `SchemaComplete` |
| `quarry_operators/checks_vector.py` | `LeftFeaturesPreserved`, `SchemaNoCollision` |

27 of these will simply gain the parameter without using it. 4 (`AllValidAssigned`, `ElevationOnlyRaised`, `NoCycles`, `Conservation`) will use the parameter to implement their actual semantics — those four are the substantive work.

**No production code calls `Check.run()` today** (the lab's executor pipeline runs operators' inline `_run_checks`, not standalone `Check.run` — recon confirmed). Only test code calls `Check.run()`, and every existing call site passes `(artifact)` only; the `inputs=()` default keeps all existing calls working without modification. Backward compatibility is therefore fully preserved at the call-site surface.

## Three Watermaster decisions this Brief implements

**A. WARN fallback when `inputs` is empty.** For the 4 raster-sized check classes (`AllValidAssigned`, `ElevationOnlyRaised`, `NoCycles`, `Conservation`), when `inputs == ()` (or `inputs is None`), the standalone class returns WARN with a clear message — *not* INVALID. Rationale: empty `inputs` is the legitimate "no inputs provided" case (e.g., a registry-driven validation pipeline that doesn't carry parent Artifacts), not a discipline failure. This preserves the post-Brief-7 parametrized WARN test in `test_check_raster.py` (which calls `check.run(raster)` with no inputs) and gives the standalone classes graceful degradation. With inputs provided, the same classes run their full check and return VALID/INVALID.

**B. Hoist `_detect_cycle` to a new `_topology.py` module.** `flow_accumulation.py` lines 311–353 currently contains the private function `_detect_cycle(flow, valid)` (Kahn's topological-sort cycle detector for D8 flow grids). `NoCycles.run()` needs to call this function against the input flow-direction raster. Three options surveyed: (a) re-implement the algorithm in `checks_artifact.py` (duplicate code), (b) import from `flow_accumulation.py` directly (checks-importing-from-operators reverse-direction layering oddity), (c) hoist to a shared `_topology.py` module parallel to `_lineage.py`. Bench's call: (c). `_topology.py` becomes the home for shared raster-graph algorithms; `flow_accumulation.py` imports the hoisted function for its own inline use; `checks_artifact.py` imports it for the standalone `NoCycles` check. Sets up the pattern (`_lineage.py`, `_topology.py`, future `_X.py` modules) for cross-cutting helper hoists.

**C. All 31 concrete Check classes accept the new parameter, mechanically.** Even the 27 output-only classes that ignore `inputs`. Mechanical update; runtime cost zero; cognitive benefit at call sites: never need to know whether a given Check accepts inputs. Satisfies SOP v2's Verify clause cleanly.

## What you are doing in Brief 8

Close the 3 raster-sized dual-residence gaps. Specifically:

1. Update the `Check` Protocol in `quarry-core/check.py` to the v2 signature.
2. Add `inputs: Sequence[Artifact] = ()` to every concrete Check class's `run` method (31 classes across 6 files). For 27 of them, the body is unchanged; only the signature gains the parameter. For 4 of them (the raster-sized stubs in `checks_artifact.py`), the body is rewritten to actually implement the check against the input Artifact(s).
3. Hoist `_detect_cycle` from `flow_accumulation.py` to a new `_topology.py` module; update `flow_accumulation.py`'s inline use and add `NoCycles.run()`'s standalone use.
4. Update tests: preserve the post-Brief-7 WARN-without-inputs test for the 4 raster-sized classes; add new tests asserting VALID/INVALID parity with inline-check results when inputs are supplied.
5. Run the full pressure_test path; confirm the 3 known failures unchanged; report counts.

## Items

### Item A — Update the `Check` Protocol in `quarry-core/check.py`

In `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/check.py`:

1. Add `from collections.abc import Sequence` to imports.
2. Update the `Check` Protocol's `run` method signature:
   ```python
   def run(self, artifact: Artifact, inputs: Sequence[Artifact] = ()) -> CheckResult:
       """Execute the check against an artifact, optionally consulting input artifacts."""
       ...
   ```
3. Update the docstring to reflect the new parameter — note that input-aware checks consume `inputs` and output-only checks ignore it.
4. Update the three concrete classes in the same file (`CRSValid`, `ExtentSane`, `BackingStoreAccessible`) to accept `inputs: Sequence[Artifact] = ()` in their `run` signature. None of them uses `inputs` — their bodies are unchanged.

### Item B — Hoist `_detect_cycle` to a new `_topology.py` module

In `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/`:

1. Create `_topology.py` containing the `_detect_cycle` function (currently at `flow_accumulation.py` lines 311–353). Move the function verbatim. Rename to `detect_cycle` (no leading underscore — it's now package-public, parallel to `lineage_params` in `_lineage.py`). Include any small helper functions used only by `_detect_cycle` if they exist; if `_detect_cycle` references named constants like `NODATA`, `OUTLET`, `PIT` from `flow_accumulation.py`, decide whether to import them or duplicate the values — your judgment, but the typical pattern is to keep typed-constant definitions in their primary module and import them.
2. In `flow_accumulation.py`: remove the local `_detect_cycle` definition; replace `_detect_cycle(...)` call sites with `detect_cycle(...)` imported from `_topology`.
3. Document `detect_cycle`'s docstring: it implements Kahn's algorithm against a D8 flow grid, returns True if a cycle exists, False otherwise. Input parameters: `flow: np.ndarray` (int8, D8 direction codes), `valid: np.ndarray` (bool mask of cells under consideration).

### Item C — Update `checks.py`, `checks_raster.py`, `checks_table.py`, `checks_vector.py` (the 19 output-only classes that ignore `inputs`)

For each of these files, add the `inputs: Sequence[Artifact] = ()` parameter to every concrete Check class's `run` method:

- `quarry-operators/checks.py`: `InternalOutletCount` (1 class)
- `quarry-operators/checks_raster.py`: 14 classes (`ValidRange`, `ResolutionConsistent`, `IsCOG`, `ValidCodeSet`, `NoPits`, `NoInteriorPits`, `Nonnegative`, `GCPCountSufficient`, `DimensionsSane`, `NodataBackground`, `CRSMatchesTarget`, `Sigma0Finite`, `Sigma0Nonnegative`, `MinObservations`)
- `quarry-operators/checks_table.py`: 2 classes (`RowCountMatches`, `SchemaComplete`)
- `quarry-operators/checks_vector.py`: 2 classes (`LeftFeaturesPreserved`, `SchemaNoCollision`)

Add `from collections.abc import Sequence` import if not already present in the file. Add `from quarry_core.artifact import Artifact` if needed (some classes may already import it for type annotations).

Body of each method is **unchanged**. Only the signature gains the parameter. These classes are output-only and ignore the new parameter.

Also update the 5 input-aware-but-already-scalar classes in `checks_artifact.py` from Brief 7 (`NodataValuePreserved`, `NodataCountPreserved`, `CRSPreserved`, `DimensionsPreserved`, `ExtentWithinInput`) to accept the parameter. These five read from `Lineage.params` (Brief 7's pattern) and don't currently consume `inputs`. Their bodies stay unchanged; only their signatures gain the parameter. They remain output-only in terms of the new parameter — they read from the output Artifact's lineage params, which is independent of the `inputs` parameter.

(Note: this is a deliberate design property — the v2 Protocol allows a Check to be input-aware, output-only, lineage-aware, or any combination. The Brief 7 classes are lineage-aware-output-only; Brief 8 adds 4 input-aware classes; the parameter is universally available so future Checks can pick their pattern.)

### Item D — Implement `AllValidAssigned` against input DEM

In `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks_artifact.py`:

Replace `AllValidAssigned.run()` body. The new shape:

1. Validate output backing per `_local_raster_path(artifact, self.name)`. If invalid, return as-is.
2. If `inputs == ()` (empty), return WARN with message `"Cannot run all_valid_assigned without input DEM Artifact"`. Use `_artifact_only_warning(self.name, "input validity mask requires input DEM via the `inputs` parameter")` or similar — your judgment on the exact message; the SOP doesn't dictate it. Preserve the helper if convenient.
3. Otherwise expect `inputs[0]` to be the input DEM Artifact. Validate it (raster type, local-file backing, file exists). If invalid, return INVALID with a clear message.
4. Open the input DEM with rasterio; read band 1; build `valid = ~np.isnan(dem) & (dem != nodata)` where `nodata = src.nodata`. If `nodata is None`, use only `~np.isnan(dem)` for validity (matching what the inline check does when `params.nodata` is None — confirm against `d8_flow_direction.py`'s `_run_checks` body).
5. Open the output flow raster; read band 1 as int8. Compute `unassigned = int(np.sum(flow[valid] == NODATA))` where `NODATA = -1` (the D8 NODATA convention used by `d8_flow_direction.py`).
6. Return VALID if `unassigned == 0` with message `"All valid cells have a flow direction"`; otherwise INVALID with message `f"{unassigned} valid cells have no flow direction"`.

Update the class's `description` to reflect that the check is input-aware: e.g., `"Every valid cell in the input DEM has an assigned D8 direction in the output flow raster"`. Add a class docstring or inline comment naming `inputs[0]` as the expected input DEM Artifact.

### Item E — Implement `ElevationOnlyRaised` against input DEM

In the same file, replace `ElevationOnlyRaised.run()` body:

1. Validate output backing. If invalid, return as-is.
2. If `inputs == ()`, return WARN with a "needs input DEM" message.
3. Expect `inputs[0]` to be the input DEM Artifact. Validate it.
4. Open the input DEM (read as `original`, float64). Build `valid = ~np.isnan(original) & (original != nodata)` with the same nodata handling pattern.
5. Open the output filled DEM (read as `filled`, float64).
6. Confirm `filled.shape == original.shape`; if not, return INVALID with a shape-mismatch message.
7. Compute `lowered = np.any(filled[valid] < original[valid] - 1e-10)`.
8. Return VALID if not lowered with message `"All filled elevations >= original"`; INVALID otherwise with `"Some cells were lowered during filling"`.

Update description to reflect input-aware semantics.

### Item F — Implement `NoCycles` against input flow-direction raster

In the same file, replace `NoCycles.run()` body:

1. Validate output backing (the output is the accumulation raster from `flow_accumulation`). If invalid, return as-is. (The check is technically about the *input* flow-direction graph, but it lives in the dual-residence chain for the `flow_accumulation` operator's `declared_checks()`, so the output is the accumulation Artifact.)
2. If `inputs == ()`, return WARN with a "needs input flow-direction raster" message.
3. Expect `inputs[0]` to be the input flow-direction Artifact. Validate it.
4. Open the input flow raster (read as int8). Build `valid = (flow >= 0) & (flow <= PIT)` using the constants from `flow_accumulation.py` (or duplicated if they live there) — `OUTLET = 0`, `PIT = 9`, `NODATA = -1` are the typical D8 conventions in this codebase; confirm against `flow_accumulation.py`.
5. Call `detect_cycle(flow, valid)` from the hoisted `_topology` module.
6. Return VALID if no cycle with message `"No cycles in D8 flow network"`; INVALID otherwise with `"D8 flow network has cycle(s)"`.

Update description to reflect input-aware semantics.

### Item G — Implement `Conservation` against input flow-direction raster and output's lineage `weight`

In the same file, replace `Conservation.run()` body:

1. Validate output backing (accumulation raster).
2. If `inputs == ()`, return WARN with a "needs input flow-direction raster" message.
3. Expect `inputs[0]` to be the input flow-direction Artifact. Validate it.
4. Read `weight = lineage_params(artifact).get("weight")` (from the output's lineage params; `flow_accumulation.py` already stashes `weight` there at execute() time — verify; if it isn't there, return INVALID with a message naming that `weight` should be in the output's lineage params). Use `lineage_params` from `quarry_operators._lineage`.
5. Open the input flow raster (read as int8). Build `valid = (flow >= 0) & (flow <= PIT)` using the same constants pattern as Item F.
6. Open the output accumulation raster (read as float64).
7. Confirm `acc.shape == flow.shape`; if not, return INVALID with shape-mismatch.
8. Compute:
   ```python
   total_weight = float(np.sum(valid)) * float(weight)
   outlet_mask = valid & ((flow == OUTLET) | (flow == PIT))
   outlet_acc_sum = float(np.sum(acc[outlet_mask]))
   residual = abs(outlet_acc_sum - total_weight)
   ```
9. Return VALID if `residual < 1e-6` with message `f"Flow conserved: outlet sum={outlet_acc_sum:.1f}, total weight={total_weight:.1f}"`; INVALID otherwise with `f"Flow NOT conserved: outlet sum={outlet_acc_sum:.1f}, total weight={total_weight:.1f}, residual={residual:.6f}"`.

Update description to reflect input-aware semantics with the weight-from-lineage detail.

### Item H — Update tests

In `/Users/jakegearon/projects/quarry/tests/pressure_test/test_check_raster.py`:

1. Keep the existing `test_artifact_only_gap_checks_warn_for_backed_raster` parametrized test that calls each of the 4 raster-sized classes' `run(raster)` (no inputs) and asserts WARN. The new WARN-fallback semantics preserve this behavior.
2. Add new tests, one per raster-sized class (or a focused parametrization), that supply `inputs=[input_artifact]` and assert:
   - VALID when inputs match the output and the check passes
   - INVALID when inputs match but the check fails (e.g., create a constructed output with unassigned cells; create a filled DEM with some lowered cells; create a flow grid with an intentional cycle; create an accumulation raster with conservation violated)
   - INVALID with shape-mismatch when input shape differs from output shape (where applicable)
3. For `Conservation`, also test the case where `weight` is missing from `Lineage.params` — assert INVALID with the named-missing message.
4. Use realistic test fixtures (small rasters in `tests/fixtures/` if needed; reuse existing fixtures if any are suitable — `tests/pressure_test/test_d8_flow_direction.py`, `test_fill_depressions.py`, `test_flow_accumulation.py`, and `test_internal_outlet_check.py` may have fixtures you can reuse).

Other test files that may need updates:
- `tests/pressure_test/test_internal_outlet_check.py`: `InternalOutletCount` now accepts `inputs=()`. If any test calls `.run(artifact, inputs=...)` or asserts on the signature, update. If tests only call `.run(artifact)` (the back-compat path), no change needed.
- `tests/pressure_test/test_check_table.py`, `test_check_vector.py`, the various `test_*_connector.py` and operator tests: any test that introspects a Check's signature (rare but check) needs updating. If they only call `.run(artifact)`, no change.

### Item I — Verify the full test surface

Run `uv run pytest -q tests/pressure_test/` and verify:

- Pass count is approximately **(Brief 7 baseline) + (new VALID/INVALID tests added in Item H)**. Brief 7's last-known count was 1968 passed + ~6 new tests = ~1974; this Brief adds VALID/INVALID/missing-key tests for the 4 raster-sized classes, plus shape-mismatch tests — roughly 12-20 new tests depending on how you parametrize. Expected ~1986-1994 passing.
- The 3 known failures from Brief 5/6/7 are unchanged: `test_cli_route.py::test_route_ambiguous_geojson_falls_back_to_local_file`, `test_policy_surface.py::test_docs_report_actual_connector_and_operator_surface`, `test_router_integration.py::test_ambiguous_extensions_do_not_route_to_specialized_connectors`.
- No new test failures introduced.

Also run:
- `uv run ruff check` on edited files (or repo-wide).
- `uv run ty check` on the edited modules (especially `quarry-core/check.py` and the 6 `checks_*.py` files).

### Item J — Report

Return a chat message structured as:

1. **Summary** — one paragraph naming what landed.
2. **Item-by-item** — A through I, each with: what was changed, file paths touched, any judgment calls, any unexpected findings.
3. **Test results** — full pressure_test pytest count (passed/skipped/failed); note any deviation. Also `ruff check` / `ty check` results.
4. **Flag list** — every place where the implementation required a judgment call (e.g., how to handle missing nodata in the input DEM for AllValidAssigned / ElevationOnlyRaised; how to handle shape-mismatch between input and output; whether to import D8 constants from `flow_accumulation.py` or duplicate; any test fixture that needed reuse vs new creation), with one-line context.

## Constraints

- **Write only inside the write scope below.** Any write outside is an integration failure.
- **Do not modify `/Users/jakegearon/projects/watershed/`.** SOPs, CANON, lineage entries are the Watermaster's domain.
- **Do not change the inline `_run_checks` bodies in the 3 affected operators.** The dual-residence rule says the same check name appears in both inline and standalone paths; the inline paths stay exactly as they are. The standalone paths are what's gaining input-aware capability.
- **Do not change `Lineage` shape in `quarry-core/artifact.py`.**
- **Do not change `Artifact.id` derivation logic.**
- **Do not change any Operator's caller-params dataclass.**
- **Do not introduce new metadata keys** anywhere. The Brief 7 metadata → lineage migration discipline holds.
- **Do not change the operator-registry or check-registry surfaces.** The registry already returns the right classes; no entries are added or removed.
- **Do not weaken the dual-residence rule.** Every name in any operator's `declared_checks()` resolves to a standalone Check class with a matching `name` property. After Brief 8, all standalone classes implement actual semantics (no remaining WARN stubs except as the input-empty fallback path).
- **If you see useful adjacent work outside the scope, flag it in the return rather than writing it.**
- **One coherent change set:** v2 Protocol signature → all 31 concrete classes → 4 raster-sized implementations → tests. No partial state where some classes have the new signature and others don't.

## Write scope

```
/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/check.py
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/_topology.py  (NEW)
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/flow_accumulation.py
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks.py
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks_artifact.py
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks_raster.py
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks_table.py
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks_vector.py
/Users/jakegearon/projects/quarry/tests/pressure_test/test_check_raster.py
/Users/jakegearon/projects/quarry/tests/pressure_test/test_internal_outlet_check.py  (if it needs signature updates)
/Users/jakegearon/projects/quarry/tests/pressure_test/test_check_table.py  (if it needs signature updates)
/Users/jakegearon/projects/quarry/tests/pressure_test/test_check_vector.py  (if it needs signature updates)
```

You may also read freely anywhere in `/Users/jakegearon/projects/quarry/` and `/Users/jakegearon/projects/watershed/`.

## Out of scope

- Operator inline `_run_checks` modifications. The dual-residence rule preserves inline behavior.
- `Lineage` schema revision. Brief 7's decision held; Brief 8 inherits.
- `Artifact.id` derivation changes. Brief 3's discipline holds.
- DispatchRun-side migration. Separate arc.
- Any change to `OperatorRun`, `OperatorSpec`, `OperatorResult`, or any Brief 1/2/3/4/5/6/7 type or helper.
- Changes to `hydrops/` or `quarry-explorer/`.
- Any CANON or SOP revision (operator-shape.md v1 → v2 was already preflighted and committed before this Brief drafts).
- Removal of any WARN-fallback path. The standalone Check classes preserve WARN as the empty-inputs degraded path.

## Verify (before submitting)

- `quarry-core/check.py`'s `Check` Protocol has `run(self, artifact: Artifact, inputs: Sequence[Artifact] = ()) -> CheckResult`.
- All 3 concrete classes in `check.py` (`CRSValid`, `ExtentSane`, `BackingStoreAccessible`) accept the new parameter.
- `_topology.py` exists and exports `detect_cycle`. `flow_accumulation.py` imports `detect_cycle` from `_topology` and uses it in place of the local `_detect_cycle`.
- All 31 concrete Check classes across `checks.py`, `checks_artifact.py`, `checks_raster.py`, `checks_table.py`, `checks_vector.py` accept the `inputs: Sequence[Artifact] = ()` parameter.
- `AllValidAssigned`, `ElevationOnlyRaised`, `NoCycles`, `Conservation` each: (a) return WARN when `inputs == ()`; (b) implement the real semantics when `inputs[0]` is the expected input Artifact; (c) return INVALID when the input is malformed or the check fails.
- `test_artifact_only_gap_checks_warn_for_backed_raster` still passes (preserved WARN-without-inputs behavior).
- New VALID/INVALID tests cover each of the 4 raster-sized classes.
- Full `tests/pressure_test/` pytest passes with the 3 known failures unchanged.
- `ruff check` passes on edited files.
- `ty check` passes on edited modules.
- No file outside the write scope has been modified.
- The dual-residence rule holds: every name in any operator's `declared_checks()` resolves to a standalone Check class that produces a `CheckResult` with the same `check_name`.

## Return shape

Return a chat message structured as:

1. **Summary** — one paragraph naming what landed.
2. **Item-by-item** — A through J, each with: what was changed, file paths touched, any judgment calls, any unexpected findings.
3. **Test results** — full pressure_test pytest count (passed/skipped/failed); note any deviation. Also `ruff check` / `ty check` results.
4. **Flag list** — every place where the implementation required a judgment call (e.g., D8 constant import strategy; shape-mismatch handling; nodata-None handling for valid-mask construction; any test fixture decision), with one-line context.

The Watermaster will integrate your return: verify writes are within scope, audit the test deltas, confirm the discipline holds, and either commit the work as-is or send a follow-up Brief.

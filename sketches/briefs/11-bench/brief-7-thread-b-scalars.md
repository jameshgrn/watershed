# Engineer Brief — Brief 7 (Thread B scalar-sized dual-residence gap closures)

**engineer_model**: `codex-gpt-5` (the seated Codex instance the Source is using; confirm exact identifier at transmission)
**source_utterance** (verbatim, with bracketed context for an Engineer who didn't see the chat):
> "hello there, welcome" [Source's session-open]
>
> "i want you to decide and argue your reasoning on 1-3 and then elts do those" [Source's authorization for the Watermaster to decide the design questions on Confluence's three substantive open arcs — Brief 6, Thread B, DispatchRun-side migration — and execute. Bench decided three Brief-internal design questions on Thread B scalars: (A) split `nodata_preserved` into two semantically distinct check names; (B) stash input-derived scalars in `Lineage.params` (extending the precedent `reproject.py` already set with `source_crs`) and own the Artifact.id-derivation implication; (C) migrate `RowCountMatches` from reading `Artifact.metadata` to reading `Lineage.params` for consistency.]

**compiled_by**: Watermaster Bench
**compiled_at**: 2026-05-13
**state**: integrated (drafted 2026-05-13 → sent 2026-05-13 → returned 2026-05-13 → integrated 2026-05-13)
**supersedes**: none
**expected_return_shape**: executed file writes within the write scope below, plus a chat return summarizing each item (A–I), any deviations, full pressure_test pytest result, and a flag list.

---

## Read these before starting

You are an external Engineer consulted by the Watermaster of a research lab called *watershed*. You read only this Brief. You executed Briefs 1, 2, 3, 4, 5, and 6 in prior sessions, all integrated cleanly.

Read the following files first — they are the discipline this Brief implements:

1. `/Users/jakegearon/projects/watershed/CANON.md` — Articles II (one canonical writer), III (the lab has one rim), IV (every Artifact carries its lineage), IX (the Watermaster works through typed surfaces), XV (typed records are frozen-pinned at lifecycle transitions).
2. `/Users/jakegearon/projects/watershed/sops/operator-shape.md` v1 — the SOP this Brief implements. The relevant clauses: *"maintain dual-residence for every check named in `declared_checks()`: the same name appears both inline within the Operator's `execute()` flow and as a standalone Check class implementing the Protocol; both implementations produce `CheckResult`s with the same `check_name`."* And the escalate clause: *"if existing quarry-operators implementations have `declared_checks()` entries without matching standalone Checks (partial dual-residence today) — the lift into flume is the time to close the gap; do not lift partial dual-residence into flume canonical state."*
3. `/Users/jakegearon/projects/watershed/sops/data-contracts.md` v2 — particularly: *"treat `Artifact.metadata` as opaque connector-extension context only; never as authoritative for typed fields."* This grounds design decision C in the Brief.
4. `/Users/jakegearon/projects/watershed/sketches/briefs/07-knickpoint/brief-2-dual-residence.md` and `return-2.md` — Brief 2 minted 30 standalone Check classes; 8 returned WARN with named-gap messages. This Brief closes 5 of those 8.

The lab vocabulary is fluvial. *quarry* is the boundary module; the operators here will become flume during the future flume lift.

## Context — current state

Brief 2 (Knickpoint, integrated 2026-05-11) minted standalone Check classes parallel to inline operator checks per `operator-shape.md` v1's dual-residence rule. 8 Check classes returned WARN with a named-gap message because the standalone class could read only the output Artifact, not the input — and the check fundamentally needed an input-derived value.

**The 5 scalar-sized gaps this Brief closes** (each is "scalar-sized" because what's missing is a single input-derived scalar, not the whole input raster):

1. `nodata_preserved` — `build_cog` checks nodata *value*; `aspect`/`hillshade`/`slope` check nodata pixel *count*. Semantically heterogeneous (this Brief splits the name; see Item A).
2. `crs_preserved` — `build_cog` checks input CRS string equality.
3. `dimensions_preserved` — `build_cog` checks input band count.
4. `extent_within_input` — `clip_raster` checks output extent is contained by input extent.
5. `row_count_matches` — `sample_raster` and `zonal_stats` check output row count equals input vector feature count.

**The 3 raster-sized gaps** (`all_valid_assigned`, `elevation_only_raised`, `no_cycles`, `conservation` — 4 names across 3 operators) want the full input raster, not a scalar. They are explicitly **out of scope** for Brief 7 — a separate Brief 8 will handle them via a `Check.run(artifact, inputs=())` Protocol revision and corresponding `operator-shape.md` v1 → v2 preflight.

**The precedent for `Lineage.params` stashing.** `reproject.py` already stashes `source_crs` (an input-derived scalar) in its output Artifact's `Lineage.params`, alongside operator caller params (`target_crs`, `resampling`, `resolution_override`). Brief 7 extends this established pattern to 7 more operators.

**The standalone `_lineage_params` helper** at `checks_raster.py` lines 23–26:
```python
def _lineage_params(artifact: Artifact) -> dict[str, Any]:
    if artifact.lineage is None:
        return {}
    return dict(artifact.lineage.params)
```
Used by `CRSMatchesTarget` to read `target_crs` from lineage. This is the template the revised Check classes follow. The helper currently lives only in `checks_raster.py` and needs to be reachable from `checks_artifact.py` and `checks_table.py` too.

## Three Watermaster decisions this Brief implements

**A. Split `nodata_preserved` into two check names.**

The current single `nodata_preserved` check name is run inline by four operators with two different semantics:
- `build_cog`: compares input nodata *value* (read from rasterio) to output nodata value
- `aspect` / `hillshade` / `slope`: compares input nodata pixel *count* to output's nodata pixel count

A single standalone Check class can't unify these without branching. Brief 7 retires `nodata_preserved` and mints two new check names:

- `nodata_value_preserved` (for build_cog) — the standalone class reads `lineage.params["input_nodata_value"]` (or `None` if explicitly absent) and compares to the output's nodata.
- `nodata_count_preserved` (for aspect / hillshade / slope) — the standalone class reads `lineage.params["input_nodata_count"]` (int) and compares to the count of output nodata pixels.

Each affected operator's `declared_checks()` returns the new name(s) corresponding to which inline semantics they actually run. Each operator's inline `CheckResult` `check_name=` argument uses the new name. The two new standalone Check classes live in `checks_artifact.py`.

**B. Stash input-derived scalars in `Lineage.params`; own the Artifact.id implication.**

Brief 3 made `Artifact.id` content-derived via `derive_id_from_provenance(operation, inputs, params)` where `params` is `Lineage.params`. Adding new keys to operators' lineage params changes prov-derived ids for newly-produced output Artifacts. Existing Artifact rows in any registry are frozen-pinned per CANON XV and unaffected; the change applies only to outputs produced after this Brief lands.

The reproject precedent (`source_crs` already stashed in lineage params from a prior strand) settled this pattern. Brief 7 extends it to 7 more operators.

**C. Migrate `RowCountMatches` from `Artifact.metadata` to `Lineage.params`.**

The current `RowCountMatches` standalone Check reads `artifact.metadata.get("expected_row_count")`. Operators don't populate that metadata key today — hence the WARN. Per `data-contracts.md` v2 ("treat `Artifact.metadata` as opaque connector-extension context only; never as authoritative for typed fields"), the right home for `expected_row_count` is `Lineage.params`. Brief 7 migrates the Check class to read from lineage and has the two operators populate `lineage.params["expected_row_count"]` at output construction.

## What you are doing in Brief 7

Close 5 of the 8 dual-residence gaps Brief 2 flagged. Specifically:
- Hoist `_lineage_params` to a shared module so it's importable from any `checks_*.py`.
- Replace `NodataPreserved` with `NodataValuePreserved` and `NodataCountPreserved`. Revise `CRSPreserved`, `DimensionsPreserved`, `ExtentWithinInput` to read from lineage. Revise `RowCountMatches` to read from lineage.
- Update 7 operators (`build_cog`, `clip_raster`, `aspect`, `hillshade`, `slope`, `sample_raster`, `zonal_stats`) to stash the required input-derived scalars in their output Artifact's `Lineage.params` at execute() time. Update operators that ran `nodata_preserved` inline to use the appropriate new check name in `declared_checks()` and in their inline `CheckResult` emission.
- Update `check_registry.py` to retire `nodata_preserved` and add `nodata_value_preserved` and `nodata_count_preserved`.
- Update the 2 test files that exercise the WARN behavior to instead assert VALID/INVALID against the new lineage-populated scalars.
- Run the full pressure_test path and confirm pass count matches expectations.

## Items

### Item A — Hoist `_lineage_params` to a shared module

In `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/`:

1. Create a new file `_lineage.py` (or extend an existing internal module if you have a better home — your judgment) containing only:
   ```python
   """Shared helper for reading an Artifact's Lineage.params."""

   from __future__ import annotations

   from typing import Any

   from quarry_core.artifact import Artifact


   def lineage_params(artifact: Artifact) -> dict[str, Any]:
       """Return a copy of the artifact's Lineage.params, or {} if no Lineage."""
       if artifact.lineage is None:
           return {}
       return dict(artifact.lineage.params)
   ```
2. In `checks_raster.py`, replace the local `_lineage_params` definition with `from quarry_operators._lineage import lineage_params` (or your chosen import path). Update the one call site in `CRSMatchesTarget`.
3. Import the helper into `checks_artifact.py` and `checks_table.py` for use in Items B and D.

Name the public helper `lineage_params` (no leading underscore) — it's used across multiple check modules now, which is the threshold for promotion from module-private to package-internal.

### Item B — Revise `checks_artifact.py`: replace `NodataPreserved`, revise `CRSPreserved` / `DimensionsPreserved` / `ExtentWithinInput`

In `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks_artifact.py`:

1. Delete the `NodataPreserved` class.
2. Add `NodataValuePreserved` and `NodataCountPreserved` classes. Each follows the existing pattern (property `name`, property `description`, `run(artifact: Artifact) -> CheckResult`). The expected shape:
   - `NodataValuePreserved`: `name = "nodata_value_preserved"`, description "Output nodata value matches the operator input nodata value". `run()` resolves local raster path; reads `lineage_params(artifact).get("input_nodata_value")`; if key absent returns INVALID with a clear message ("No `input_nodata_value` in lineage params"); reads the output's nodata via `rasterio.open(path) as src: src.nodata`; compares with NaN-aware equality (both NaN match; or use `math.isnan` checks); returns VALID on match, INVALID on mismatch.
   - `NodataCountPreserved`: `name = "nodata_count_preserved"`, description "Output nodata pixel count matches the operator input nodata pixel count". `run()` resolves local raster path; reads `lineage_params(artifact).get("input_nodata_count")` as int; if absent returns INVALID; opens raster, counts nodata pixels in band 1 using output's nodata value; returns VALID on equality, INVALID on mismatch.
3. Revise `CRSPreserved.run()`: read `lineage_params(artifact).get("source_crs")` (str). If absent, return INVALID. Compare to `artifact.spatial.crs`. Return VALID on equality, INVALID on mismatch.
4. Revise `DimensionsPreserved.run()`: read `lineage_params(artifact).get("input_band_count")` (int). If absent, return INVALID. Compare to `artifact.spatial.band_count`. Return VALID on equality, INVALID on mismatch. Update description to reflect band-count semantics ("Output band count matches the operator input band count").
5. Revise `ExtentWithinInput.run()`: keep the existing pre-check that returns INVALID when `artifact.spatial.extent is None`. After that, read `lineage_params(artifact).get("input_extent")` as a 4-tuple. If absent, return INVALID. Apply the same tolerance check the inline version in `clip_raster.py` uses (1e-6 absolute tolerance per coordinate); return VALID if output extent is contained within input extent, INVALID otherwise. The check name stays `extent_within_input`.

Keep `_local_raster_path` and `_artifact_only_warning` helpers — they're still useful for the raster-sized gaps Brief 8 will work on. The remaining classes (`AllValidAssigned`, `ElevationOnlyRaised`, `NoCycles`, `Conservation`) stay unchanged; Brief 8 handles them.

### Item C — Revise `checks_table.py`: migrate `RowCountMatches` to read lineage

In `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks_table.py`:

1. Change `RowCountMatches.run()` to read `lineage_params(artifact).get("expected_row_count")` instead of `artifact.metadata.get("expected_row_count")`. If the key is absent, return INVALID (was WARN). The rest of the body — open table file, count rows, compare — stays the same.

This shifts the contract: from "operators may populate metadata['expected_row_count']" to "operators must populate lineage.params['expected_row_count'] for this check to pass." Reflect this in the class docstring and in the description.

### Item D — Update `check_registry.py`

In `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/check_registry.py`:

1. Remove the `("nodata_preserved", ...)` entry.
2. Add two new entries (alphabetical insertion):
   - `("nodata_count_preserved", "quarry_operators.checks_artifact", "NodataCountPreserved")`
   - `("nodata_value_preserved", "quarry_operators.checks_artifact", "NodataValuePreserved")`

### Item E — Update 7 operators to stash input-derived scalars in `Lineage.params`

For each operator below, edit the `execute()` method to populate the output Artifact's `Lineage.params` dict with the named scalars **in addition to** any operator caller params already stashed. Use the existing `Lineage(...)` construction site (every operator has one when assembling the output Artifact). The new keys go alongside existing params keys.

**`build_cog.py`** — adds three keys:
- `"input_nodata_value"`: the input raster's nodata value (read via rasterio at execute time; may be `None` if the input has no nodata; preserve `None` in lineage params)
- `"source_crs"`: `inputs[0].spatial.crs` (str or None)
- `"input_band_count"`: `inputs[0].spatial.band_count` (int)

Also: update the inline `nodata_preserved` `CheckResult` emission to use `check_name="nodata_value_preserved"`. Update `declared_checks()` to return `nodata_value_preserved` in place of `nodata_preserved`. Keep `crs_preserved`, `dimensions_preserved` in `declared_checks()` as-is.

**`clip_raster.py`** — adds one key:
- `"input_extent"`: `inputs[0].spatial.extent` (the 4-tuple `(xmin, ymin, xmax, ymax)` from the source Artifact's SpatialDescriptor).

No declared_checks() rename here — `extent_within_input` name stays.

**`aspect.py`** — adds one key:
- `"input_nodata_count"`: count of nodata pixels in the input DEM, read via rasterio at execute time (the inline check already computes this on its own; the goal is to also stash it in lineage so the standalone class can read it without re-opening the file).

Also: update the inline `nodata_preserved` `CheckResult` emission to use `check_name="nodata_count_preserved"`. Update `declared_checks()` to return `nodata_count_preserved` in place of `nodata_preserved`.

**`hillshade.py`** — same pattern as aspect: stash `"input_nodata_count"`, rename declared_checks entry, rename inline CheckResult.

**`slope.py`** — same pattern as aspect: stash `"input_nodata_count"`, rename declared_checks entry, rename inline CheckResult.

**`sample_raster.py`** — adds one key:
- `"expected_row_count"`: `inputs[1].spatial.feature_count` (int; the vector input's feature count).

No declared_checks() rename here — `row_count_matches` name stays.

**`zonal_stats.py`** — same pattern as sample_raster: stash `"expected_row_count"`, no rename.

For each operator: confirm that the Lineage construction site uses `Lineage(operation=..., inputs=..., params={...})` with the params dict carrying both caller params and the new input-derived scalars. The reproject precedent (`source_crs` already in lineage params alongside caller params) is the template.

### Item F — Update tests

In `/Users/jakegearon/projects/quarry/tests/pressure_test/test_check_raster.py`:

1. The current `test_artifact_only_gap_checks_warn_for_backed_raster` parametrized test (lines ~143–158) bundles 8 check classes together asserting WARN. Split: pull `NodataPreserved`, `CRSPreserved`, `DimensionsPreserved`, `ExtentWithinInput` out into a different test (now passing); keep the 4 raster-sized check classes (`AllValidAssigned`, `ElevationOnlyRaised`, `NoCycles`, `Conservation`) in the WARN parametrization (still WARN until Brief 8).
2. Add new tests (one per scalar Check class or a focused parametrization) that assert:
   - VALID when the appropriate `Lineage.params` key is present and matches.
   - INVALID when the key is present and mismatches.
   - INVALID when the key is absent.
   Use realistic test fixtures (small raster files in `tests/fixtures/` if needed; reuse existing fixtures if any are suitable).
3. Add tests for `NodataValuePreserved` and `NodataCountPreserved` separately (each with its own VALID / INVALID-mismatch / INVALID-missing-key trio).

In `/Users/jakegearon/projects/quarry/tests/pressure_test/test_check_table.py`:

1. Adjust the existing WARN-path fixture for `RowCountMatches` (line ~36 — currently sets up an Artifact with `metadata={}`, asserts WARN). Now: an Artifact with `lineage=None` or `lineage.params={}` should return INVALID (was WARN). Add a passing fixture: `Lineage(operation="...", inputs=(...), params={"expected_row_count": N})` and the table has N rows → VALID. Add a mismatch fixture → INVALID.

If any other test in the `pressure_test/` directory exercises the standalone check classes via the registry by name, update the test setup to populate `Lineage.params` rather than relying on WARN. Especially watch:
- `tests/pressure_test/test_dual_residence.py` if it exists (Brief 2 added a `test_dual_residence.py` per the recon) — confirm it still passes; it might need fixture updates if it tests the standalone classes directly.
- `tests/pressure_test/test_check_registry.py` — verify it still passes; if it lists `nodata_preserved`, update to the two new names.

### Item G — Verify the full test surface

Run `uv run pytest -q tests/pressure_test/` and verify:

- Pass count is approximately **1968 + (new scalar VALID tests)** = expected ~1980–1990 (depending on how many new tests you add).
- The 3 known failures from Brief 5/6 are unchanged: `test_cli_route.py::test_route_ambiguous_geojson_falls_back_to_local_file`, `test_policy_surface.py::test_docs_report_actual_connector_and_operator_surface`, `test_router_integration.py::test_ambiguous_extensions_do_not_route_to_specialized_connectors`.
- No new test failures introduced by the Brief.

Also run:
- `uv run ruff check` on edited files.
- `uv run ty check` on edited modules.
- If the operator integration tests (e.g., `test_build_cog.py`, `test_aspect.py`, etc.) assert on specific Artifact ids, they may need fixture updates because the prov-derived ids will change with the new lineage params. Read those tests and update if needed; report any test that needed an id update.

### Item H — Sanity-check Artifact.id derivation

The `_derive_artifact_id` path in `quarry-core/artifact.py` uses `derive_id_from_provenance` when `lineage.operation` and `inputs` are set. Adding new keys to lineage params changes the derived id. Specifically:

1. Confirm that adding e.g. `"source_crs": "EPSG:4326"` to the lineage params of a build_cog output produces a different Artifact.id than before.
2. Confirm that re-running the same operator on the same inputs with the same params produces the same Artifact.id (stability — Brief 3's discipline holds).
3. Confirm no test fixture asserts a specific Artifact.id literal for any of the 7 affected operators. If one does, update it as part of Brief 7's scope and flag it in the return.

This is a verify-step, not a code change.

### Item I — Report

Return a chat message structured as the prior Briefs (Summary, Item-by-item A through I, Test results, Flag list). Specifically:

- Confirm each operator's `declared_checks()` lists the post-rename check names.
- Confirm the count of new tests added.
- Confirm whether any operator integration test needed an id-literal fixture update.
- Confirm `_lineage.py` is the chosen home for the hoisted helper (or name your alternative home).
- Flag any check class whose semantic implementation required a judgment call you made (e.g., NaN-aware comparison shape for nodata values).

## Constraints

- **Write only inside the write scope below.** Any write outside is an integration failure.
- **Do not modify `/Users/jakegearon/projects/watershed/`.** SOPs, CANON, lineage entries are the Watermaster's domain.
- **Do not touch the 3 raster-sized check classes** (`AllValidAssigned`, `ElevationOnlyRaised`, `NoCycles`, `Conservation`). They stay returning WARN. Brief 8 handles them with a Protocol revision.
- **Do not change `Check` Protocol shape in `quarry-core/check.py`.** That's Brief 8's preflight territory.
- **Do not change `Lineage` shape in `quarry-core/artifact.py`.** Adding keys to `Lineage.params` is the design; revising `Lineage`'s fields is preflight-gated and out of scope.
- **Do not change any Operator's caller-params dataclass.** Operator caller params (`BuildCOGParams`, `AspectParams`, etc.) stay unchanged.
- **Do not change Artifact.id derivation logic in `quarry-core/artifact.py`.** Brief 3's derivation stays; the only thing changing is the data fed into it (lineage params get richer).
- **Do not introduce new metadata keys** anywhere. If an operator was using metadata for an input-derived signal, migrate to lineage.params per design decision C.
- **Preserve operator caller params already in Lineage.params.** The new keys are additive; don't drop existing keys like `target_crs` / `resampling` / `convention` / etc.
- **If you see useful adjacent work outside the scope, flag it in the return rather than writing it.**
- **One coherent change set:** close the 5 scalar gaps in lockstep. No partial state where some operators stash and others don't, or where the standalone class expects a key the operator doesn't populate.

## Write scope

```
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/_lineage.py
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks_artifact.py
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks_raster.py
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks_table.py
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/check_registry.py
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/build_cog.py
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/clip_raster.py
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/aspect.py
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/hillshade.py
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/slope.py
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/sample_raster.py
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/zonal_stats.py
/Users/jakegearon/projects/quarry/tests/pressure_test/test_check_raster.py
/Users/jakegearon/projects/quarry/tests/pressure_test/test_check_table.py
/Users/jakegearon/projects/quarry/tests/pressure_test/test_dual_residence.py
/Users/jakegearon/projects/quarry/tests/pressure_test/test_check_registry.py
```

The last two are "include if they need updates" — if `test_dual_residence.py` or `test_check_registry.py` references `nodata_preserved` by name or asserts on the WARN behavior of the 4 revised checks, they need updates. If they don't, leave them alone. Also include any operator integration test that asserts a specific Artifact.id literal (read `test_build_cog.py`, `test_aspect.py`, `test_hillshade.py`, `test_slope.py`, `test_reproject.py`, `test_sample_raster.py`, `test_zonal_stats.py`, `test_clip_raster.py` quickly — if any pin a literal id, include and update).

You may also read freely anywhere in `/Users/jakegearon/projects/quarry/` and `/Users/jakegearon/projects/watershed/`.

## Out of scope

- The 3 raster-sized dual-residence gaps (`all_valid_assigned`, `elevation_only_raised`, `no_cycles`, `conservation`). Brief 8 territory.
- `Check` Protocol revision in `quarry-core/check.py`. Brief 8 territory (preflight-gated).
- `operator-shape.md` v1 → v2 SOP revision. Brief 8's preflight.
- `Lineage` dataclass shape revision in `quarry-core/artifact.py`. Out of scope; Brief 7 uses the existing `params: Mapping[str, Any]` shape.
- Connector materialize-time changes. Out of scope.
- Any change to `OperatorRun`, `OperatorSpec`, `OperatorResult`, `Artifact.id` derivation logic, or any Brief 1/2/3/4/5/6 type or helper.
- Changes to `hydrops/` or `quarry-explorer/`.
- DispatchRun-side migration. Separate arc.

## Verify (before submitting)

- `_lineage.py` (or your chosen home) exports `lineage_params` and is imported by `checks_artifact.py`, `checks_raster.py`, `checks_table.py`. No duplicate `_lineage_params` definitions remain.
- `checks_artifact.py` no longer defines `NodataPreserved`; defines `NodataValuePreserved` and `NodataCountPreserved`; revised `CRSPreserved` / `DimensionsPreserved` / `ExtentWithinInput` read from lineage.
- `checks_table.py`'s `RowCountMatches.run()` reads from lineage params, not metadata.
- `check_registry.py` has no `nodata_preserved` entry; has `nodata_value_preserved` and `nodata_count_preserved` entries.
- All 7 operators populate the documented scalar keys in `Lineage.params` at execute().
- All 4 nodata-affected operators (`build_cog`, `aspect`, `hillshade`, `slope`) emit `CheckResult`s with the new check_name (`nodata_value_preserved` or `nodata_count_preserved`) and their `declared_checks()` returns the matching name.
- The 5 revised standalone Check classes return VALID when the expected lineage key is present and matches; INVALID when present but mismatched; INVALID when absent. No WARN remains for the 5 scalar checks.
- The 3 raster-sized check classes (`AllValidAssigned`, `ElevationOnlyRaised`, `NoCycles`, `Conservation`) are unchanged.
- Full `tests/pressure_test/` pytest passes with the 3 known failures unchanged; new tests added; no new failures introduced.
- `ruff check` passes on edited files.
- `ty check` passes on edited modules.
- No file outside the write scope has been modified.
- No new metadata key was introduced anywhere (the migration is metadata → lineage, not the reverse).

## Return shape

Return a chat message structured as:

1. **Summary** — one paragraph naming what landed.
2. **Item-by-item** — A through I, each with: what was changed, file paths touched, any judgment calls, any unexpected findings.
3. **Test results** — full pressure_test pytest count (passed/skipped/failed); note any deviation. Also `ruff check` / `ty check` results.
4. **Flag list** — every place where the gap closure required a judgment call (e.g., NaN-aware comparison shape for nodata values; whether `nodata_count_preserved` should count nan-as-nodata or only the typed nodata value; any test fixture that needed an Artifact.id literal update), with one-line context.

The Watermaster will integrate your return: verify writes are within scope, audit the test deltas, confirm the discipline holds, and either commit the work as-is or send a follow-up Brief.

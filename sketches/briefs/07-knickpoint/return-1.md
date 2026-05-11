# Engineer Return — Brief 1 (Lift Wave 1)

**brief_id**: `brief-1-lift-wave-1` (refers to `/Users/jakegearon/projects/watershed/sketches/briefs/07-knickpoint/brief-1-lift-wave-1.md`)
**received_at**: 2026-05-11
**integrated_by**: Watermaster Knickpoint
**integration_action**: verified writes — all seven items (A–G) accepted, three named deviations integrated as defensible, dual-residence audit (item F) accepted as input to Brief 2

## Files written

In-scope per Brief 1's write scope:

- `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/operator.py` — OperatorSpec extended with `determinism_class`, `supports_tiling`, `tile_reconciliation_kind`, `seed_param`; `__post_init__` enforces four invariants; OperatorResult made `@dataclass(frozen=True, init=False)` with manual `__init__` enforcing tuple coercion and `truth_source_by_field` validation; `OperatorConformanceError` and `assert_operator_conforms` defined.
- `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/artifact.py` — `with_check` now uses `dataclasses.replace(self, checks=new_checks)`, preserving `temporal`. Audit of other Artifact constructors in the file found no other dropped fields.
- `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/executors/local.py` — `LocalExecutor.submit` uses `replace(result, timing_seconds=elapsed)` instead of post-construction mutation.
- `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/registry.py` — calls `assert_operator_conforms(op)` at registry materialize time.
- `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/semantics.py` — new file (123 lines). Houses `_default_raster_semantic_equality` and `_default_artifact_semantic_equality` for reuse across stable operators.
- All 16 operator files under `quarry-operators/src/quarry_operators/`: each declares `determinism_class`, `supports_tiling=False`, `tile_reconciliation_kind="none"`. The six stable operators (`build_cog`, `geocode_slc`, `reproject`, `slc_calibration`, `water_elevation_mosaic`, `zonal_stats`) additionally expose `semantic_equality` delegating to helpers in `semantics.py`.
- `/Users/jakegearon/projects/quarry/tests/pressure_test/test_operator_shape.py` — new contract tests for the operator-shape invariants.
- `/Users/jakegearon/projects/quarry/tests/pressure_test/test_build_cog.py`, `test_rasterize_vector.py`, `test_registry.py`, `test_sample_raster.py`, `test_slc_calibration.py`, `test_spatial_join.py`, `test_zonal_stats.py` — updated for the timing/frozen-result surface changes.

No file under `/Users/jakegearon/projects/watershed/` was modified. No file under `quarry-connectors/` was modified by Codex (initial Watermaster inference to the contrary was incorrect — those files were the Source's pre-existing in-progress connector work in the workspace, unrelated to this Brief).

## Test results

`uv run pytest -q tests/pressure_test/test_operator_shape.py tests/pressure_test/test_registry.py`: **45 passed**. These are the tests directly bearing on Brief 1's surface changes.

`uv run pytest -q tests/pressure_test`: **1896 passed, 54 skipped, 3 failed**. The 3 failures are in GeoJSON connector routing and connector-count docs, unrelated to Brief 1's scope — they belong to the Source's in-progress connector work in the workspace.

`uv run ruff check` + `uv run ruff format --check`: pass.
`uv run ty check` for core/operator-shape files: pass. Pre-existing Optional/backing/stub diagnostics in quarry-operators remain (unrelated to Brief 1).

## Deviations integrated

1. **`semantic_equality` is not a Protocol member** (Item B). Codex correctly named the contradiction: declaring it on the `@runtime_checkable` Protocol would break `isinstance(op, Operator)` for every non-stable operator. Instead the Protocol's docstring names the conditional contract; runtime enforcement happens via `assert_operator_conforms` at registry materialize time. My Brief's instruction "use `@runtime_checkable` semantics" was technically incompatible with conditional Protocol members. Codex's resolution is the correct pattern. Per `engineer-brief.md`'s Escalate clause, this is the kind of contradiction the Engineer's outside view is most valuable for surfacing.
2. **`OperatorResult.truth_source_by_field` typed as `Mapping[str, TruthSource]`** rather than the Brief's `Mapping[str, str]`. Adds runtime validation against the `_TRUTH_SOURCES` literal set. Stricter than the Brief and consistent with `operator-shape.md` v1's invariant-enforcement pattern. Integrated as improvement.
3. **`OperatorResult` uses `@dataclass(frozen=True, init=False)` with a manual `__init__`** to enforce tuple coercion of `checks`/`warnings` and validation of `truth_source_by_field`. Exceeds the Brief's literal "make it frozen" wording but is the defensible reading of "frozen at construction" — the result truly is immutable from the outside, and coercion happens once at construction rather than relying on caller discipline. Integrated.

## Item F audit — dual-residence coverage

Codex's table is preserved verbatim in the chat return below. 54 declared check names total; only `no_internal_outlets` has a matching standalone Check class (`InternalOutletCount`). This is a substantially bigger dual-residence gap than Eddy's source-pass had suggested and shapes Brief 2.

The deduplicated set of distinct check names across the 16 operators (the upper bound on how many new standalone Check classes Brief 2 will need to mint):

- `crs_valid` — 8 operators (clip_raster, geocode_slc, rasterize_vector, reproject, sample_raster, spatial_join, water_elevation_mosaic, zonal_stats)
- `backing_accessible` — 7 operators (clip_raster, d8_flow_direction, fill_depressions, flow_accumulation, geocode_slc, reproject, water_elevation_mosaic) — `BackingStoreAccessible` already exists in `quarry-core/check.py`; needs to be wired in
- `nodata_preserved` — 4 operators (aspect, build_cog, hillshade, slope)
- `valid_range` — 3 operators (aspect, hillshade, slope)
- `resolution_consistent` — 3 operators (aspect, hillshade, slope)
- `extent_sane` — 3 operators (geocode_slc, reproject, water_elevation_mosaic) — possibly satisfied by the existing `ExtentSane` in `quarry-core/check.py`
- `row_count_matches` — 2 operators (sample_raster, zonal_stats)
- `schema_complete` — 2 operators (sample_raster, zonal_stats)
- ~20 operator-specific singletons (`is_cog`, `crs_preserved`, `dimensions_preserved`, `extent_within_input`, `valid_code_set`, `no_pits`, `all_valid_assigned`, `no_interior_pits`, `elevation_only_raised`, `no_cycles`, `nonnegative`, `conservation`, `gcp_count_sufficient`, `dimensions_sane`, `nodata_background`, `crs_matches_target`, `sigma0_finite`, `sigma0_nonnegative`, `left_features_preserved`, `schema_no_collision`, `min_observations`)

Roughly 28–30 distinct Check classes will close the gap, including the 3 that already exist in `quarry-core/check.py` (CRSValid, ExtentSane, BackingStoreAccessible) if they're wireable by name match.

## Flags for follow-up

1. **Six stable classifications worth a second look** — `build_cog`, `geocode_slc`, `reproject`, `slc_calibration`, `water_elevation_mosaic`, `zonal_stats`. Each has either library-version-sensitive output (GDAL embedded timestamps in TIFF tags, GDAL resampling tie-breaking) or parallel-reduction order concerns (mosaicing merge order, zonal aggregation across many features). The classifications are defensible — the SOP's guidance is to declare the weaker class when in doubt, and `stable` is weaker than `deterministic`. No revision needed unless a future pressure test surfaces a real semantic-equality issue with one of the `_default_*_semantic_equality` helpers.
2. **Dual-residence closure is Brief 2 territory** and is bigger than originally scoped.
3. **The watermaster's verification inference about the connector files was wrong.** Recording here so the lineage entry captures it: when verifying an Engineer return that includes "out-of-scope" file claims, distinguish "Codex's writes" from "workspace dirt" by asking the Source rather than inferring from `git diff`. The verification-agent affordance is helpful but its read of `git status` is incomplete.

## Verbatim Engineer return (chat content)

```
Summary
    Landed the operator-shape v1 lift in quarry scope: OperatorSpec now carries determinism/tiling/seed invariants, OperatorResult is frozen and tuple-pinned, local execution wraps timing with dataclasses.replace, Artifact.with_check preserves temporal via replace, and all 16 registered operators declare determinism. I did not modify /Users/jakegearon/projects/watershed. The requested pressure-test path still has 3 failures, all from out-of-scope connector routing/docs around existing GeoJSON connector work.

Item-by-item
    A. Updated /Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/operator.py:62 with required determinism_class, tiling fields, seed_param, and invariant checks.
    B. Added OperatorConformanceError and assert_operator_conforms() in /Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/operator.py:229, and registry-time enforcement in /Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/registry.py:61. The Protocol documents conditional semantic_equality; I did not make it a hard Protocol member because @runtime_checkable would make deterministic operators fail runtime conformance.
    C. Made OperatorResult frozen in /Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/operator.py:105, accepting iterable checks/warnings but storing tuples. Added truth_source_by_field validation. Updated /Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/executors/local.py:75 to use replace(result, timing_seconds=elapsed). Removed direct operator-side timing from existing operators/tests.
    D. Fixed /Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/artifact.py:238 by using replace(self, checks=new_checks). Audit finding: no other Artifact(...) constructor calls inside Artifact methods, so no other dropped fields found.
    E. All 16 operators now declare determinism_class, supports_tiling=False, and tile_reconciliation_kind="none". Judgment-call stable classifications: build_cog, geocode_slc, reproject, slc_calibrate, water_elevation_mosaic, zonal_stats. Added reusable semantic helpers in /Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/semantics.py:41.
    F. Audit completed; no code written to close gaps. Only no_internal_outlets has a standalone quarry-operators Check class.
    G. Updated pressure tests only for surface changes: direct operator results now expect timing_seconds is None, executor-produced results still carry timing, and frozen result mutation tests use replace.
```

(Full audit table and test-file list preserved in Brief 1's integration record; not duplicated here for length.)

# Engineer Return — Brief 2 (dual-residence closure)

**brief_id**: `brief-2-dual-residence-closure` (refers to `/Users/jakegearon/projects/watershed/sketches/briefs/07-knickpoint/brief-2-dual-residence-closure.md`)
**received_at**: 2026-05-11
**integrated_by**: Watermaster Knickpoint
**integration_action**: verified writes — all seven items (A–G) accepted; 30 Check classes registered (3 reused from quarry-core, 1 wired from prior strand, 26 newly minted); 8 dual-residence flags surfaced as explicit escalate territory; tests pass at 76 focused + 1927 full pressure-path (3 pre-existing connector failures unrelated to this Brief)

## Files written

In-scope per Brief 2's write scope:

- `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/check_registry.py` — new file. `_CHECK_REGISTRY` tuple of 30 `(name, module_path, class_name)` entries; `CHECK_NAMES` derived; `get_check(name)` lazy importlib lookup with `Check`-Protocol conformance verification and `KeyError` on unknown.
- `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/registry.py` — extended. `OperatorDualResidenceError(OperatorConformanceError)` defined; `assert_dual_residence(op)` iterates `op.declared_checks()` and resolves each through `get_check(name)`, also verifying registered Check class's `name` property matches the declared name; called at the end of `get_operator()` after `assert_operator_conforms()`.
- `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks_artifact.py` — new file. 8 gap-explicit Check classes (`NodataPreserved`, `CRSPreserved`, `DimensionsPreserved`, `ExtentWithinInput`, `AllValidAssigned`, `ElevationOnlyRaised`, `NoCycles`, `Conservation`). Each `run(artifact)` validates output sanity (raster type + LOCAL_FILE backing exists) then returns `_artifact_only_warning(name, missing_context)` — `ValidationState.WARN` with a message naming what input-side state isn't reachable from the output Artifact alone.
- `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks_raster.py` — new file. 14 raster Check classes (`ValidRange`, `ResolutionConsistent`, `IsCOG`, `ValidCodeSet`, `NoPits`, `NoInteriorPits`, `Nonnegative`, `GCPCountSufficient`, `DimensionsSane`, `NodataBackground`, `CRSMatchesTarget`, `Sigma0Finite`, `Sigma0Nonnegative`, `MinObservations`).
- `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks_table.py` — new file. 2 table Check classes (`RowCountMatches`, `SchemaComplete`).
- `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks_vector.py` — new file. 2 vector Check classes (`LeftFeaturesPreserved`, `SchemaNoCollision`).
- `/Users/jakegearon/projects/quarry/tests/pressure_test/test_check_registry.py` — new file.
- `/Users/jakegearon/projects/quarry/tests/pressure_test/test_dual_residence.py` — new file.
- `/Users/jakegearon/projects/quarry/tests/pressure_test/test_check_raster.py` — new file.
- `/Users/jakegearon/projects/quarry/tests/pressure_test/test_check_table.py` — new file.
- `/Users/jakegearon/projects/quarry/tests/pressure_test/test_check_vector.py` — new file.

Codex took the per-family-split option (Item F default was monolithic `checks.py` with split-on-need); the existing `checks.py` is left holding only hydrology code (`InternalOutletCount`).

## Registry composition (30 entries, alphabetical)

- 3 baseline at `quarry_core.check`: `BackingStoreAccessible`, `CRSValid`, `ExtentSane` (reused from prior quarry-core work; not duplicated).
- 1 existing at `quarry_operators.checks`: `InternalOutletCount` (formerly stranded, now wired).
- 26 newly minted in `quarry_operators.checks_artifact|raster|table|vector`.

All 54 declared-check occurrences across the 16 operators resolve to 30 distinct registered names. `assert_dual_residence` passes for every operator in the registry. No missing names. No extra names.

## Test results

- Focused: `test_check_registry.py test_dual_residence.py test_check_raster.py test_check_table.py test_check_vector.py test_operator_shape.py test_registry.py` → **76 passed**.
- Full path: `tests/pressure_test/` → **1927 passed, 54 skipped, 3 failed**. The 3 failures are the pre-existing GeoJSON connector routing failures from the Source's separate in-progress connector work; unrelated to Brief 2. (Identical to the Brief 1 baseline; +31 new passing tests from Brief 2, matching the new test files.)
- `ruff check`, `ruff format --check`, `ty check` on Brief 2 scope: pass.

## Flags — the 8 dual-residence gaps (escalate territory)

Codex correctly did not invent substitute semantics for checks where the inline implementation reasons from input-Artifact state not carried by the output Artifact. The standalone Check classes return `WARN` with messages naming the gap. The 8 are:

| Check name | Operator(s) | Missing input-side state |
|---|---|---|
| `nodata_preserved` | aspect, build_cog, hillshade, slope | input nodata value/count |
| `crs_preserved` | build_cog | input CRS |
| `dimensions_preserved` | build_cog | input band count/dimensions |
| `extent_within_input` | clip_raster | input extent |
| `all_valid_assigned` | d8_flow_direction | input DEM validity mask (raster-sized) |
| `elevation_only_raised` | fill_depressions | original DEM values (raster-sized) |
| `no_cycles` | flow_accumulation | input flow-direction graph (raster-sized) |
| `conservation` | flow_accumulation | input flow directions + outlet mask + weight |
| `row_count_matches` | sample_raster, zonal_stats | input feature/zone count |

Two natural categories:

1. **Scalar-sized input state** (5 checks): `nodata_preserved`, `crs_preserved`, `dimensions_preserved`, `extent_within_input`, `row_count_matches`. The missing input-side state is a value or small data structure that could be stashed in `Lineage.params` at operator `execute()` time. Closing this gap requires modifying each affected operator's `execute()` body to record the input-derived scalar, plus revising the corresponding standalone Check class to read from `lineage.params` and produce a real verdict instead of WARN. Modest, mechanical work; one follow-up Brief.

2. **Raster-sized input state** (3 checks, 4 named: `all_valid_assigned`, `elevation_only_raised`, `no_cycles`, `conservation`). The missing state is the full input raster (or a graph derived from it). Can't fit in `Lineage.params`. Two options: (a) extend the `Check` Protocol from `run(artifact)` to `run(artifact, inputs: tuple[Artifact, ...] = ())` so the standalone class can read input rasters by ID; (b) accept these as inline-only and remove from `declared_checks()` (per `operator-shape.md` v1's escalate clause: "restricting the check to operator-internal use"). Each option is preflight-gated: (a) is a Protocol revision in quarry-core (zero-dep risk; needs care); (b) is a semantics revision to `declared_checks()` plus an SOP escalate-clause refinement.

The discipline `operator-shape.md` v1 already names the path: *"propose either lifting that state into a typed Artifact field or restricting the check to operator-internal use; do not weaken the dual-residence rule."* This Brief surfaces the cases; the path forward is a Watermaster decision (probably with Source input) about which option to pursue for each category.

## Verbatim Engineer return (chat content)

```
Summary
    Brief 2 landed in /Users/jakegearon/projects/quarry: added a standalone check registry, wired dual-residence gating into operator materialization, registered all 30 distinct declared-check names across the 16 operators, and added pressure tests for registry coverage, dual-residence enforcement, and the new Check families. No operator execute() body was modified, and /Users/jakegearon/projects/watershed/ was not touched.

Item-by-item
    A. Added /Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/check_registry.py with lazy get_check(), CHECK_NAMES, and registry entries for quarry-core baseline checks plus quarry-operators checks.
    B. Extended /Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/registry.py with OperatorDualResidenceError, assert_dual_residence(op), and a registry-time call after assert_operator_conforms(op).
    C. Added standalone Check classes in: checks_artifact.py, checks_raster.py, checks_table.py, checks_vector.py.
    D. Registered existing InternalOutletCount from quarry_operators/checks.py as no_internal_outlets.
    E. Verified all 54 declared-check occurrences across 16 operators resolve to 30 distinct registered Check names. Missing: none. Extra: none.
    F. Split layout by family. checks.py keeps existing hydrology code; raster, table, vector, and artifact-context-gap checks are separate.
    G. Added tests: test_check_registry.py, test_dual_residence.py, test_check_raster.py, test_check_table.py, test_check_vector.py.

Flags
    Standalone equivalence is incomplete for checks that need input Artifact state not carried by the output Artifact: nodata_preserved, crs_preserved, dimensions_preserved, extent_within_input, all_valid_assigned, elevation_only_raised, no_cycles, conservation, row_count_matches. I did not invent substitute semantics; their standalone classes make the gap explicit.

Test Results
    Focused/new + Brief 1 surface tests: 76 passed.
    Full pressure path: 1927 passed, 54 skipped, 3 failed. The 3 failures are the existing GeoJSON connector routing/docs failures, outside this Brief's write scope.
    ruff check: passed. ruff format --check: passed. ty check on Brief 2 scope: passed. git diff --check on Brief 2 scope: passed.
```

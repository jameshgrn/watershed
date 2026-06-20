# EngineerReturn - Brief 11

**Brief id**: brief-11-d8-canonicalization-nodata-resolution (`sketches/briefs/12-anabranch/brief-11-d8-canonicalization-nodata-resolution.md`)
**Engineer model**: codex-gpt-5
**Carried by**: Watermaster direct Engineer dispatch
**Received at**: 2026-05-14
**Integrated by**: Watermaster Anabranch
**Integration action**: verified-and-accepted-with-watermaster-type-cleanup

---

## Verbatim Engineer summary

```text
Files changed, all within declared scope:

- /Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/_topology.py
- /Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/d8_flow_direction.py
- /Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/flow_accumulation.py
- /Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks.py
- /Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks_artifact.py
- /Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/fill_depressions.py
- /Users/jakegearon/projects/quarry/tests/pressure_test/test_d8_flow_direction.py
- /Users/jakegearon/projects/quarry/tests/pressure_test/test_flow_accumulation.py
- /Users/jakegearon/projects/quarry/tests/pressure_test/test_hydrology_adversarial.py
- /Users/jakegearon/projects/quarry/tests/pressure_test/test_internal_outlet_check.py
- /Users/jakegearon/projects/quarry/tests/pressure_test/test_check_raster.py

Item status:

- A complete: _topology.py now owns public East-first constants and __all__.
- B complete: d8_flow_direction.py imports canonical constants, removed local codes, and uses D8_* internally.
- C complete: flow_accumulation.py imports canonical constants and uses D8_OUTLET/D8_PIT.
- D complete: checks.py imports from _topology and uses D8_NODATA.
- E complete: checks_artifact.py imports from _topology; AllValidAssigned and ElevationOnlyRaised read resolved_nodata with fallback.
- F complete: D8 lineage now stores caller nodata and resolved nodata.
- G complete: fill lineage now stores caller nodata and resolved nodata; North-first private arrays untouched.
- H complete: test imports/usages updated, plus four resolved-nodata tests added.

Checks run:

- uv run ruff format ... on modified files: 1 file reformatted, 10 unchanged.
- uv run ruff check ... on modified files: passed.
- uv run pytest tests/pressure_test/test_d8_flow_direction.py tests/pressure_test/test_flow_accumulation.py tests/pressure_test/test_internal_outlet_check.py tests/pressure_test/test_hydrology_adversarial.py tests/pressure_test/test_check_raster.py -q: 135 passed in 1.20s.
- uv run pytest tests/pressure_test/ -q: 1978 passed, 54 skipped, 3 failed, 65 warnings in 63.09s.

Full pressure-test failures:

- tests/pressure_test/test_cli_route.py::TestRoute::test_route_ambiguous_geojson_falls_back_to_local_file
- tests/pressure_test/test_policy_surface.py::test_docs_report_actual_connector_and_operator_surface
- tests/pressure_test/test_router_integration.py::TestRouterExtensionRouting::test_ambiguous_extensions_do_not_route_to_specialized_connectors[/data/watersheds.geojson-LocalFileConnector]

Grep confirmations:

- rg -n "\b(OUTLET|PIT|NODATA)\b" over d8_flow_direction.py, flow_accumulation.py, checks.py, and updated D8 test files: no matches.
- rg -n "from quarry_operators\.d8_flow_direction import .*...(OUTLET|PIT|NODATA|D8_DR|D8_DC)": no deprecated constant imports found.
- resolved_nodata present in D8, fill, checks, and new tests.

Flags/deviations:

- checks_artifact.py fallback comment is wrapped across three comment lines to satisfy ruff line length.
- The Brief's "only d8_flow_direction and fill_depressions have the params.nodata override pattern" is not true in current source: aspect.py, slope.py, and hillshade.py also resolve params-side nodata. I left them untouched because the Brief explicitly scoped this fix to D8/fill and AllValidAssigned / ElevationOnlyRaised.
- No commits made.
```

---

## Watermaster integration notes

**Verification path**. Direct file inspection on every Brief-11 target file plus local focused verification. Unlike Brief 9, this sandbox could run quarry's local test and check commands.

**Scope check**. All Engineer writes stayed inside the declared write scope: `/Users/jakegearon/projects/quarry/packages/quarry-operators/**` and `/Users/jakegearon/projects/quarry/tests/pressure_test/**`. No writes to watershed lineage files. The worktree was already dirty from prior flume-lift Briefs; several target files are still untracked from those prior Briefs, so final-file inspection is more reliable than `git diff` alone.

**Item A - `_topology.py`**. Public East-first constants now live at `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/_topology.py:26` through `:31`, with `__all__` at `:95`. The docstring names the canonical encoding and explicitly excludes `fill_depressions.py`'s North-first private encoding at `:12`.

**Items B and F - `d8_flow_direction.py`**. The operator imports `D8_DC`, `D8_DR`, `D8_NODATA`, `D8_OUTLET`, and `D8_PIT` from `_topology.py` at `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/d8_flow_direction.py:49`. `D8_DIST` and `_SQRT2` remain local at `:55` through `:57`. Output nodata now uses `D8_NODATA` at `:161`. Lineage now distinguishes caller intent from resolved value at `:200`: `{"nodata": params.nodata, "resolved_nodata": nodata}`.

**Item C - `flow_accumulation.py`**. The module imports canonical D8 constants from `_topology.py` at `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/flow_accumulation.py:45`. Valid mask and outlet-mask logic use `D8_PIT` / `D8_OUTLET` at `:135` and `:248`. The dead local `NODATA_CODE` definition is gone.

**Item D - `checks.py`**. `InternalOutletCount` imports constants from `_topology.py` at `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks.py:25` and filters `D8_NODATA` at `:82`.

**Item E - `checks_artifact.py`**. The file imports canonical D8 constants from `_topology.py` at `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks_artifact.py:37`. `AllValidAssigned` reads `resolved_nodata` from output lineage with fallback to input `src.nodata` at `:400` through `:404`. `ElevationOnlyRaised` does the same at `:465` through `:469`. `NoCycles` and `Conservation` now use `D8_PIT` / `D8_OUTLET` at `:534`, `:611`, and `:613`.

**Item G - `fill_depressions.py`**. Lineage now records caller `nodata` and `resolved_nodata` at `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/fill_depressions.py:197` through `:198`. The North-first private `_D8_DR` / `_D8_DC` arrays remain untouched at `:290` through `:291`.

**Item H - tests**. Import updates landed in the three named D8 test files. Four resolved-nodata tests were added in `/Users/jakegearon/projects/quarry/tests/pressure_test/test_check_raster.py` at `:475`, `:492`, `:530`, and `:547`, covering explicit lineage `resolved_nodata` and fallback semantics for both `AllValidAssigned` and `ElevationOnlyRaised`.

**Watermaster type-cleanup after return**. The Engineer return did not include a `ty check` result. I ran the Brief's requested `ty` command locally; it failed on touched files for existing optional-field narrowing issues (`artifact.backing` and `artifact.id`) and `rasterio.crs` submodule resolution in touched tests. I made narrow follow-up edits inside the Brief write scope:

- Added explicit runtime guards for missing input backing/id in `d8_flow_direction.py`, `fill_depressions.py`, and `flow_accumulation.py`, then reused the narrowed `artifact_id`.
- Replaced `from rasterio.crs import CRS` in the touched tests with `rasterio.CRS.from_epsg(...)`, preserving runtime behavior while satisfying `ty`.

These were integration cleanup edits to satisfy the Brief's acceptance criteria, not a new feature or scope expansion.

**Final verification run by Watermaster**.

```text
cd /Users/jakegearon/projects/quarry
uv run ruff format <11 Brief-11 files>
11 files left unchanged

uv run ruff check <11 Brief-11 files>
All checks passed!

uv run pytest tests/pressure_test/test_d8_flow_direction.py tests/pressure_test/test_flow_accumulation.py tests/pressure_test/test_internal_outlet_check.py tests/pressure_test/test_hydrology_adversarial.py tests/pressure_test/test_check_raster.py -q
135 passed in 0.78s

uv run ty check <11 Brief-11 files>
All checks passed!

rg -n "\b(OUTLET|PIT|NODATA)\b" <Brief acceptance files>
no matches

git diff --check -- <11 Brief-11 files>
clean
```

I did not rerun the full `tests/pressure_test/` path after the Watermaster type-cleanup because the local AGENTS discipline says to use targeted pressure tests. The Engineer had already run the full path before the type-cleanup and reported `1978 passed, 54 skipped, 3 failed`, with the three failures matching the known GeoJSON/router/docs surface.

**Accepted flags**.

- The Brief's "only d8_flow_direction and fill_depressions have the params.nodata override pattern" statement is stale: `aspect.py`, `slope.py`, and `hillshade.py` also resolve params-side nodata. They remain untouched because Brief 11's semantic parity gap was specifically `AllValidAssigned` / `ElevationOnlyRaised`; extending resolved-nodata lineage to the other three operators is a future follow-up only if their standalone checks need it.

No commits made.

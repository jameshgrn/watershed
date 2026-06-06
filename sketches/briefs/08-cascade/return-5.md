# Engineer Return — Brief 5 (Wave 4 consumer migration)

**brief_id**: `brief-5-wave-4-consumer-migration` (refers to `/Users/jakegearon/projects/watershed/sketches/briefs/08-cascade/brief-5-wave-4-consumer-migration.md`)
**received_at**: 2026-05-11
**integrated_by**: Watermaster Cascade
**integration_action**: verified writes — all five items (A–E) accepted; `HydrologyFlow` migrated to `OperatorRun` with public API change to `HydrologyFlowSuccess/Failure.runs: list[OperatorRun]`; seven test files migrated mechanically; deprecated `make_invalid_completed_run` / `make_failed_run` aliases removed from `adapter_helpers.py`; full pressure_test path returns `1969 passed, 54 skipped, 3 failed` — Brief 3 baseline of 1949 exceeded by 20 (Brief 4 OperatorRun tests now part of the path); the 3 known failures are exactly the Source's pre-existing GeoJSON/router/docs connector work, unchanged from Brief 3.

## Files written

In-scope per Brief 5's write scope:

- `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/hydrology_flow.py` — imports `OperatorRun` from `quarry_core.operator_run`; `HydrologyFlowSuccess.runs` and `HydrologyFlowFailure.runs` typed as `list[OperatorRun]`; three completion guards use `run_record.state != "completed"`; `_execute_step` returns `OperatorRun` and calls `save_operator_run`; added explicit `output is not None` asserts after completed-state checks for type narrowing (useful adjacent — see Deviations).
- `/Users/jakegearon/projects/quarry/tests/pressure_test/test_hydrology_flow.py` — `RunStatus` import removed; `.status == RunStatus.COMPLETED` → `.state == "completed"`; `get_run` → `get_operator_run`; registry stats assertions updated from the legacy `runs` key to `operator_runs` (registry.py's stats() was already returning both keys after Brief 4 — recon confirmed).
- `/Users/jakegearon/projects/quarry/tests/pressure_test/test_generic_dispatch.py` — `list_runs` → `list_operator_runs`; `.status` → `.state`.
- `/Users/jakegearon/projects/quarry/tests/pressure_test/test_cli_inspection.py` — seven `list_runs` calls migrated; status filter values updated.
- `/Users/jakegearon/projects/quarry/tests/pressure_test/test_cli_rasterize.py` — four `list_runs` calls + alias-import migrated.
- `/Users/jakegearon/projects/quarry/tests/pressure_test/test_cli_zonal.py` — one `list_runs` call + alias-import migrated.
- `/Users/jakegearon/projects/quarry/tests/pressure_test/test_cli_sample.py` — four `list_runs` calls + alias-import migrated.
- `/Users/jakegearon/projects/quarry/tests/pressure_test/test_reproject.py` — `save_run` → `save_operator_run`; `get_run` → `get_operator_run`; `.status` assertion → `.state`.
- `/Users/jakegearon/projects/quarry/tests/pressure_test/adapter_helpers.py` — deprecated `make_invalid_completed_run` and `make_failed_run` aliases removed; canonical `make_invalid_completed_operator_run` and `make_failed_operator_run` retained; added missing `dispatched_by` to `make_failed_operator_run` (useful adjacent — see Deviations).

Watermaster spot-verified: `adapter_helpers.py` no longer imports/exposes the deprecated aliases; both canonical helpers carry `dispatched_by="watermaster:test"`; Grep over `/Users/jakegearon/projects/watershed/` for `make_invalid_completed_run|make_failed_run` returns matches only in my own Brief/return/THINKING docs (no Quarry test still imports the deprecated names). No file under `/Users/jakegearon/projects/watershed/` was modified.

## Test results

- Lint (`uv run ruff check`) on edited files: **pass**.
- Type-check (`uv run ty check`) on `hydrology_flow.py`: **pass**.
- Targeted migrated consumer suite: **177 passed**.
- Full `tests/pressure_test/` path: **1969 passed, 54 skipped, 3 failed**.

The 3 failures are the Source's pre-existing in-progress connector/router/docs surface (unchanged from Brief 3 baseline; Brief 4 and Brief 5 are unrelated):

- `tests/pressure_test/test_cli_route.py::TestRoute::test_route_ambiguous_geojson_falls_back_to_local_file`
- `tests/pressure_test/test_policy_surface.py::test_docs_report_actual_connector_and_operator_surface`
- `tests/pressure_test/test_router_integration.py::TestRouterExtensionRouting::test_ambiguous_extensions_do_not_route_to_specialized_connectors[/data/watersheds.geojson-LocalFileConnector]`

The pass count of 1969 is 20 above the Brief 3 baseline of 1949 because Brief 4's new `OperatorRun` / `operator_runs` registry tests are now part of the pressure path. Wave 4 has not broken the green-line; it has extended it.

## Deviations integrated

1. **Type-narrowing asserts after completed-state checks** (Item A). After each `if run_record.state != "completed":` guard fires `return`, Codex added an explicit `assert run_record.output is not None` so the type checker can narrow the subsequent `run_record.output.artifact` access. Necessary because Python's type checker can't infer that `state == "completed"` implies `output is not None` from operator-run-shape v1's invariants alone — those invariants live in `OperatorRun.complete`'s contract, not in the field types. Codex's assertion is a defensive pin matching the SOP's verify clause: *"an OperatorRun in `state == "completed"` has `output` non-`None` and `error == ""`"*. Integrated as a correctness-preserving annotation, not scope creep.

2. **`dispatched_by` added to `make_failed_operator_run`** (Item D). The helper at `adapter_helpers.py` was missing the SOP-required `dispatched_by` field. Brief 5 didn't name this fix explicitly (the recon focused on the alias removal), but it was necessary for the helper to construct a valid `OperatorRun` per Brief 4's invariants. Codex added `dispatched_by="watermaster:test"` for parity with `make_invalid_completed_operator_run`. Integrated as a missing-required-field fix, not scope creep.

3. **`registry.stats()` key rename in tests** (Item B). `test_hydrology_flow.py` previously asserted on `stats["runs"]`. After Brief 4 extended `registry.stats()` to return both `runs` (legacy count) and `operator_runs` (new count), the natural target for the test is `operator_runs`. Codex's change is test-side only; `registry.py`'s `stats()` was already returning both keys after Brief 4 (verified by Cascade's spot-check). Integrated as a test-target update, not an out-of-scope registry edit.

No other deviations.

## Flags

Codex reports: *"No OperatorRun migration blockers remain in the Brief 5 scope."*

Wave 4 of the flume lift is now in code AND propagated to all in-repo consumers. The legacy `RunRecord` / `RunStatus` / `save_run` / `get_run` / `list_runs` surface is deprecated-but-functional and remains as the legacy read path per the SOP's frozen-pin escalate clause. Removal of those legacy surfaces is a future Brief, gated on confidence that no consumer still needs them (today's `test_registry_operator_runs.py` legacy round-trip test is the deliberate regression coverage).

## Verbatim Engineer return (chat content)

```
Summary
   Brief 5 landed: HydrologyFlow and the remaining pressure-test consumers now use OperatorRun, .state, and save/get/list_operator_runs. The temporary legacy helper aliases are removed from adapter_helpers.py. Exact runtime model identifier is not exposed to me beyond this session identifying me as Codex based on GPT-5.

Item-by-item
   A. Updated /Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/hydrology_flow.py
   - Replaced RunRecord / RunStatus with OperatorRun.
   - Result dataclasses now expose runs: list[OperatorRun].
   - Completion guards now use run_record.state != "completed".
   - Registry persistence now calls save_operator_run.
   - Added explicit output is not None asserts after completed-state checks for type narrowing.

   B. Updated /Users/jakegearon/projects/quarry/tests/pressure_test/test_hydrology_flow.py
   - Removed RunStatus.
   - Migrated status assertions to .state == "completed".
   - Migrated get_run to get_operator_run.
   - Updated registry stats assertions from runs to operator_runs.

   C. Updated remaining consumer tests:
   - /Users/jakegearon/projects/quarry/tests/pressure_test/test_generic_dispatch.py
   - /Users/jakegearon/projects/quarry/tests/pressure_test/test_cli_inspection.py
   - /Users/jakegearon/projects/quarry/tests/pressure_test/test_cli_rasterize.py
   - /Users/jakegearon/projects/quarry/tests/pressure_test/test_cli_zonal.py
   - /Users/jakegearon/projects/quarry/tests/pressure_test/test_cli_sample.py
   - /Users/jakegearon/projects/quarry/tests/pressure_test/test_reproject.py
   All moved from legacy list_runs / save_run / get_run / .status usage to the OperatorRun registry/state surface.

   D. Updated /Users/jakegearon/projects/quarry/tests/pressure_test/adapter_helpers.py
   - Removed make_invalid_completed_run and make_failed_run aliases.
   - Kept canonical make_invalid_completed_operator_run and make_failed_operator_run.
   - Added missing dispatched_by to make_failed_operator_run.

   E. Verification completed.

Test results
   - Targeted migrated consumer suite: 177 passed.
   - Full pressure path: 1969 passed, 54 skipped, 3 failed.
   - The 3 failures are the expected out-of-scope GeoJSON/router/docs connector surface:
      - tests/pressure_test/test_cli_route.py::TestRoute::test_route_ambiguous_geojson_falls_back_to_local_file
      - tests/pressure_test/test_policy_surface.py::test_docs_report_actual_connector_and_operator_surface
      - tests/pressure_test/test_router_integration.py::TestRouterExtensionRouting::test_ambiguous_extensions_do_not_route_to_specialized_connectors[/data/watersheds.geojson-LocalFileConnector]
   - Pass count is above the Brief 3 1949 baseline because the Brief 4 OperatorRun tests are now part of the pressure path.
   - uv run ruff check on edited files: passed.
   - uv run ty check /Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/hydrology_flow.py: passed.

Flag list
   No OperatorRun migration blockers remain in the Brief 5 scope. The remaining 3 full-suite failures are unrelated connector/router documentation drift around GeoJSON handling.
```

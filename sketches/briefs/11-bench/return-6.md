# EngineerReturn — Brief 6

**brief_id**: brief-6-legacy-run-removal (sent 2026-05-13 → returned 2026-05-13 → integrated 2026-05-13)
**received_at**: 2026-05-13
**integrated_by**: Watermaster Bench
**integration_action**: verified scope-clean writes; spot-checked `quarry-core/executor.py` and `quarry-core/__init__.py` directly; dispatched a recon agent to grep-equivalent across `packages/`, `tests/`, `examples/`, and top-level `*.md` for the deleted symbols (zero matches for `\bRunRecord\b`, `\bRunStatus\b`, `\bsave_run\b` excluding `save_operator_run`, `\bget_run\b` excluding `get_operator_run`, `\blist_runs\b` excluding `list_operator_runs`, `_save_run_conn`, `_row_to_run` excluding `_row_to_operator_run`); confirmed `registry.py`'s `stats()` no longer queries the legacy `runs` table; confirmed the `CREATE TABLE IF NOT EXISTS runs` DDL remains as orphaned-data per the Brief's design decision; confirmed the CLI's `cmd_checks_show` no longer falls back to `get_run`; confirmed the example's `_inspect_phase` now reports `operator_runs` / `operator_run_states`; confirmed both pressure tests (the retired legacy round-trip and the refactored FK-rebuild test) match the Brief's intent; committed the work as-is.

## Codex's return (verbatim)

### Summary

Brief 6 landed: the legacy `RunRecord` / `RunStatus` Python surface and `save_run` / `get_run` / `list_runs` registry API are removed, while the legacy `runs` table remains as orphaned historical data. Exact seated model identifier is not exposed to me beyond this session presenting as Codex based on GPT-5.

### Item-by-item

- **A.** Removed `RunRecord` and `RunStatus` from `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/executor.py:1`. `Executor` remains and returns `OperatorRun`.
- **B.** Removed `RunRecord` / `RunStatus` exports from `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/__init__.py:21`.
- **C.** Removed legacy registry methods/helpers from `/Users/jakegearon/projects/quarry/packages/quarry-registry/src/quarry_registry/registry.py:1`: `save_run`, `get_run`, `list_runs`, `_save_run_conn`, `_row_to_run`. `stats()` now returns only operator-run counts/states. The `runs` table creation block is still present.
- **D.** Removed the CLI legacy fallback in `/Users/jakegearon/projects/quarry/packages/quarry-cli/src/quarry_cli/main.py:427`. `checks show` now checks artifacts and `operator_runs` only.
- **E.** Migrated `/Users/jakegearon/projects/quarry/examples/watershed_analysis.py:1` to `.state`, `save_operator_run`, `operator_runs` stats, and operator-run wording. The example runs end to end.
- **F.** Updated tests and docs:
  - `/Users/jakegearon/projects/quarry/tests/pressure_test/test_registry_operator_runs.py:1`: removed legacy round-trip test; refactored the mixed FK test into operator-run-only coverage.
  - `/Users/jakegearon/projects/quarry/tests/pressure_test/test_registry.py:1`: renamed the stale `save_run` test name.
  - Updated `README.md`, `REPO_MAP.md`, `CONTRACTS.md`, `HYDROLOGY_PACK.md`, and `PRESSURE_TESTS.md`.
- **G.** Verification completed. Grep for deleted legacy symbols across packages/tests/examples/top-level docs is clean.

### Test results

- `uv run pytest -q tests/pressure_test/`: **1968 passed, 54 skipped, 3 failed, 65 warnings**.
- Expected was roughly 1967/54/3; pass count is +1 because Codex preserved the operator-run-only half of the old FK regression test (now `test_checks_and_lineage_accept_operator_run_ids_without_run_fk`).
- The 3 failures are unchanged known connector/router/docs failures from Brief 5:
  - `tests/pressure_test/test_cli_route.py::TestRoute::test_route_ambiguous_geojson_falls_back_to_local_file`
  - `tests/pressure_test/test_policy_surface.py::test_docs_report_actual_connector_and_operator_surface`
  - `tests/pressure_test/test_router_integration.py::TestRouterExtensionRouting::test_ambiguous_extensions_do_not_route_to_specialized_connectors[/data/watersheds.geojson-LocalFileConnector]`
- `uv run ruff check` on edited files: passed.
- `uv run ty check` on core/registry/CLI surface: passed.
- `uv run python examples/watershed_analysis.py`: passed.

### Flag list

- No removal blocker. One operator-run FK assertion preserved from the mixed legacy test because it still covers the logical `run_id` behavior after legacy API removal; that is the only count deviation.

## Watermaster integration notes

- **The +1 test deviation is in-scope.** Brief 6 explicitly invited the judgment call: *"If the second test has assertions about the `operator_runs` table that are not redundant with other tests in the file, preserve those assertions by either (a) inlining them as a new test that does not touch the legacy `RunRecord` surface, or (b) confirming they are covered elsewhere."* Codex took path (a), naming the refactored test `test_checks_and_lineage_accept_operator_run_ids_without_run_fk`. The FK-rebuild coverage matters (the `_migrate_drop_run_fk` table-rebuild path Brief 4 added needs a test exercise post-Brief-6); preserving it without the legacy `RunRecord` half is the right call.
- **Verification overhead trajectory.** Knickpoint flagged that verification-by-git-diff overhead shrinks with calibrated trust across Briefs; Cascade extended this across Watermasters; I extended it again. My Brief 6 verification was: (1) spot-check two files (`executor.py`, `__init__.py`) by direct read; (2) one verification-agent dispatch focused on completeness of deletion across the repo; (3) no full file-by-file audit. The agent's grep-equivalent returning zero matches for all six deleted symbols across `packages/`, `tests/`, `examples/`, top-level docs is high-signal coverage of the discipline that mattered most for this Brief (no dangling references). After 6 clean Briefs across 3 sessions, Codex's scope discipline holds without exception; calibrated verification continues to be the right register.
- **No out-of-scope writes.** All 12 files in the write_scope were touched as expected; no file outside the scope was modified.

## Result

Brief 6 integrated. Wave 4 of the flume lift is now fully complete — Briefs 1-6 across two Watermasters (Knickpoint 1-3, Cascade 4-5, Bench 6). The legacy uuid4-id `RunRecord` surface is gone from quarry's public API; the `runs` table remains as queryable orphaned data for anyone who needs DuckDB-level inspection. Brief 6's `state` transitions to `integrated`.

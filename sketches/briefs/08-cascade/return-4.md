# Engineer Return — Brief 4 (RunRecord → OperatorRun migration)

**brief_id**: `brief-4-runrecord-to-operatorrun` (refers to `/Users/jakegearon/projects/watershed/sketches/briefs/08-cascade/brief-4-runrecord-to-operatorrun.md`)
**received_at**: 2026-05-11
**integrated_by**: Watermaster Cascade
**integration_action**: verified writes — all ten items (A–J) accepted; new `OperatorRun` typed record landed in `quarry-core/operator_run.py` per `operator-run-shape.md` v1 (frozen-at-construction via custom `__init__`, content-derived id, state-transition methods via custom `_clone`); `LocalExecutor` rewritten to produce `OperatorRun`; new `operator_runs` table parallel to legacy `runs`; `checks`/`lineage` FK relaxation rebuilt the tables; three test files updated in place; two new test files added; 102 in-scope tests pass; three out-of-scope consumer flags raised correctly (hydrology_flow.py, CLI inspection, generic dispatch) — escalate territory for a follow-up Brief.

## Files written

In-scope per Brief 4's write scope:

- `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/operator_run.py` (new) — frozen `OperatorRun` dataclass, `WatermasterId` alias, `OperatorRunState` Literal, `OperatorRunStateError`, three derivation helpers (`derive_params_hash` / `derive_operator_spec_hash` / `derive_operator_run_id`), `derive_seed_value` invariant helper, state-transition methods (`start_running` / `complete` / `fail` / `cancel`) backed by a custom `_clone` instead of `dataclasses.replace`.
- `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/artifact.py` — renamed `_identity_digest → identity_digest` (Brief's preferred path; Brief 3's three call sites within the same file updated).
- `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/executor.py` — `Executor` Protocol's `submit`/`status`/`wait` return type changed to `OperatorRun`; `RunRecord` and `RunStatus` retained with deprecation docstring.
- `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/executors/local.py` — `LocalExecutor.submit` rewritten to construct `OperatorRun` and transition via the new methods; validation-failure path goes `pending → failed` directly; execution path goes `pending → running → completed | failed`. `dispatched_by` plumbed with `"watermaster:unknown"` default.
- `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/__init__.py` — explicit exports (was a one-line docstring); `OperatorRun`, `OperatorRunState`, `OperatorRunStateError`, `WatermasterId`, the three derive_* helpers, `derive_seed_value`, `identity_digest`, plus all prior canonical types. Legacy `RunRecord`, `RunStatus` exported too (deprecated-not-deleted per Brief).
- `/Users/jakegearon/projects/quarry/packages/quarry-registry/src/quarry_registry/registry.py` — new `operator_runs` table with the SOP-aligned schema (operator_spec_hash, determinism_class, params_hash, seed_value+seed_value_kind, retried_from, retry_index, dispatched_by, from_intent_id, state, timing_seconds, output_truth_source_by_field_json, etc.); new `save_operator_run` / `get_operator_run` / `list_operator_runs` methods using `INSERT OR REPLACE`; FK relaxation on `checks` and `lineage` (table rebuild without `run_id → runs(id)` FK while preserving artifact FKs); legacy `runs` table + `save_run` / `get_run` / `list_runs` untouched.
- Test updates (in place): `tests/pressure_test/test_end_to_end.py`, `tests/pressure_test/test_registry.py`, `tests/pressure_test/adapter_helpers.py`. The adapter helpers retain old aliases as a scope bridge for out-of-scope CLI tests (not the final shape; Brief 5 territory).
- New tests: `/Users/jakegearon/projects/quarry/tests/pressure_test/test_operator_run.py`, `/Users/jakegearon/projects/quarry/tests/pressure_test/test_registry_operator_runs.py`.

Watermaster spot-verified: `operator_run.py` exists with the claimed shape, `__init__.py` exports all the new types, `identity_digest` rename landed cleanly. No file under `/Users/jakegearon/projects/watershed/` was modified (Grep confirmed).

## Test results

- Lint (`uv run ruff check`) on edited files: **pass**.
- Type-check (`uv run ty check`) on edited core/registry/CLI files: **pass**.
- Targeted in-scope pressure tests (`uv run pytest -q` on Brief 4 surface): **102 passed**.
- `from quarry_core import OperatorRun` import smoke check: **pass**.
- Out-of-scope consumer slice (`test_generic_dispatch.py::TestGenericDispatchRegistry` + CLI inspection run/check views): **4 passed, 3 failed, 14 errors** — all traceable to unmigrated `list_runs` / `.status` and `hydrology_flow.save_run()` calls, exactly the territory Codex correctly did not write into per Brief 4's write scope.

Codex did not report a full pressure_test path number this Brief; the 102 in-scope passes plus the explicit out-of-scope-consumer failure accounting is the Brief's complete result surface. The Brief 3 baseline of 1949 cannot be matched until the consumer migration closes (Brief 5 territory).

## Deviations integrated

1. **`_clone` instead of `dataclasses.replace` for state transitions** (Item C). Brief 4 named this as the documented fallback: *"If `dataclasses.replace` fails on the `init=False` shape, the cleanest fix is to write a private `_clone(self, **changes)` method that calls `OperatorRun(**asdict-equivalent, **changes)` manually."* Codex took the fallback path explicitly to preserve `id` overrides and avoid derived-field friction in the `init=False` shape. Permitted by Brief; the SOP cares about the frozen-pin discipline, not the mechanism.
2. **`identity_digest` rename in `artifact.py`** (Item B). Brief 4 named this as the preferred path. Codex did the rename and updated Brief 3's three local callers in the same file. Integrated as the clean visibility tweak the Brief authorized.
3. **FK relaxation via table rebuild** (Item I). Brief 4 named this as the preferred path. Codex executed it, preserving artifact FKs on the `checks` and `lineage` tables while dropping the `run_id → runs(id)` FK so `operator_runs.id` values are now legal references.

No deviations outside the Brief's named decision branches.

## Flags (escalate territory)

Three out-of-scope consumers still reference legacy `RunRecord` / `RunStatus` / `save_run` / `list_runs` / `.status`. Codex correctly did not write into these paths because they were outside Brief 4's `write_scope`. Naming them here so the next Brief (or the next Watermaster) can close the loop:

1. **`/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/hydrology_flow.py`** — calls `registry.save_run()` and reads `.status` from the legacy `RunRecord` shape. CLI hydrology subcommands break until this consumer migrates to `save_operator_run` / `.state`. Small, mechanical migration.

2. **`/Users/jakegearon/projects/quarry/tests/pressure_test/test_generic_dispatch.py::TestGenericDispatchRegistry`** and **`/Users/jakegearon/projects/quarry/tests/pressure_test/test_cli_inspection.py`** — assert `registry.list_runs()` results and `.status`-valued comparisons. Need to migrate to `list_operator_runs()` / `.state`. Mechanical.

3. **`/Users/jakegearon/projects/quarry/tests/pressure_test/adapter_helpers.py`** — keeps the old helper aliases (`make_invalid_completed_run`, `make_failed_run`) as a temporary scope bridge so out-of-scope CLI tests still import them. The final shape removes the aliases after the consumer migration. This bridge is intentional and Codex flagged it as not-final.

These three flags constitute a natural follow-up Brief — call it Brief 5 — to close the Wave 4 consumer migration. Smaller and more mechanical than Brief 4; estimated 50–100 lines of changes across ~4 files plus test updates.

The Brief 3 baseline (1949 pressure tests passing) cannot be re-established until Brief 5 lands; the failure count is exactly the consumer-touch territory.

## Verbatim Engineer return (chat content)

```
Summary
   Implemented the Brief 4 RunRecord → OperatorRun migration inside the allowed quarry write scope. New executions now produce frozen, content-derived OperatorRuns; legacy RunRecord/RunStatus remain for the old runs table read path. No files under /Users/jakegearon/projects/watershed were modified. Runtime model identifier is not exposed to me beyond this session identifying me as Codex based on GPT-5.

Item-By-Item
   A. Added /Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/operator_run.py: frozen OperatorRun, WatermasterId, state literals, validation, checks property.
   B. Added params/spec/run hash helpers in /Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/operator_run.py. Renamed _identity_digest to public identity_digest in /Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/artifact.py.
   C. Added transition methods with OperatorRunStateError. Used a custom _clone, not dataclasses.replace, to preserve id overrides and avoid init=False/derived-field friction.
   D. Added derive_seed_value, enforcing stochastic seed rules.
   E. Rewrote /Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/executors/local.py: LocalExecutor.submit/status/wait now return OperatorRun.
   F. Updated /Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/executor.py: protocol returns OperatorRun; RunRecord docstring marks legacy/deprecated.
   G. Added explicit exports in /Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/__init__.py, including OperatorRun and identity_digest.
   H. Added operator_runs schema and save/get/list_operator_runs in /Users/jakegearon/projects/quarry/packages/quarry-registry/src/quarry_registry/registry.py. Legacy runs schema untouched.
   I. Implemented FK relaxation by rebuilding checks/lineage without run_id -> runs(id) FK, while preserving artifact FKs.
   J. Updated scoped tests and added /Users/jakegearon/projects/quarry/tests/pressure_test/test_operator_run.py, /Users/jakegearon/projects/quarry/tests/pressure_test/test_registry_operator_runs.py.

Migration Coverage
   Rewritten in place: /Users/jakegearon/projects/quarry/tests/pressure_test/test_end_to_end.py, /Users/jakegearon/projects/quarry/tests/pressure_test/test_registry.py, /Users/jakegearon/projects/quarry/tests/pressure_test/adapter_helpers.py.
   Preserved legacy coverage: RunRecord/RunStatus legacy save/get/list tested in /Users/jakegearon/projects/quarry/tests/pressure_test/test_registry_operator_runs.py.
   Deleted tests: none.

Flags
   /Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/hydrology_flow.py is outside write scope and still calls save_run() / .status; CLI hydrology breaks until that consumer migrates.
   Several out-of-scope CLI/generic tests still assert registry.list_runs() and .status; they now need list_operator_runs() and .state.
   /Users/jakegearon/projects/quarry/tests/pressure_test/adapter_helpers.py keeps old helper aliases because out-of-scope CLI tests still import them. That is a scope bridge, not the final migration shape.

Test Results
   Passed: uv run ruff check ... on edited files. uv run ty check ... on edited core/registry/CLI files. uv run pytest -q targeted suite: 102 passed.
   Also verified from quarry_core import OperatorRun.
   Known out-of-scope consumer slice: test_generic_dispatch.py::TestGenericDispatchRegistry plus CLI inspection run/check views: 4 passed, 3 failed, 14 errors, all tied to unmigrated list_runs/.status and hydrology flow's out-of-scope save_run() path.
```

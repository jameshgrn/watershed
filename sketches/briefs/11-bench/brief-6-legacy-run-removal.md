# Engineer Brief — Brief 6 (Legacy `RunRecord` / `RunStatus` / `save_run` / `get_run` / `list_runs` removal)

**engineer_model**: `codex-gpt-5` (the seated Codex instance the Source is using; confirm exact identifier at transmission)
**source_utterance** (verbatim, with bracketed context for an Engineer who didn't see the chat):
> "hello there, welcome" [Source's session-open]
>
> "i want you to decide and argue your reasoning on 1-3 and then elts do those" [Source's authorization for the Watermaster to decide the design questions on Confluence's three substantive open arcs — Brief 6, Thread B, DispatchRun-side migration — and execute. Bench decided: Brief 6 = treat legacy uuid4-id rows as historical-only, no migration tool. This Brief implements that decision.]

**compiled_by**: Watermaster Bench
**compiled_at**: 2026-05-13
**state**: integrated (drafted 2026-05-13 → sent 2026-05-13 → returned 2026-05-13 → integrated 2026-05-13)
**supersedes**: none
**expected_return_shape**: executed file writes within the write scope below, plus a chat return summarizing each item (A–F), any deviations, full pressure_test pytest result, and a flag list.

---

## Read these before starting

You are an external Engineer consulted by the Watermaster of a research lab called *watershed*. You read only this Brief. You executed Briefs 1, 2, 3, 4, and 5 in prior sessions, all integrated cleanly.

Read the following files first — they are the discipline this Brief implements:

1. `/Users/jakegearon/projects/watershed/CANON.md` — Articles II (one canonical writer), IV (every Artifact carries its lineage), IX (the Watermaster works through typed surfaces), XV (typed records are frozen-pinned at lifecycle transitions).
2. `/Users/jakegearon/projects/watershed/sops/operator-run-shape.md` v1 — the SOP Brief 4 implemented. The escalate clause that governs this Brief's design call: *"frozen-pin existing uuid4 RunRecords at their quarry-core state and mint new OperatorRuns under this SOP for going-forward executions."* Bench's decision in Brief 6 closes the second half: the going-forward surface is in place (Brief 4 + 5); the deprecated read path goes away now. Pre-existing uuid4-id rows in the `runs` table are treated as historical-only data — the runs table schema stays in place as orphaned data (dropping it is a destructive change that would want its own preflight), but the public API for reading or writing it is removed.
3. `/Users/jakegearon/projects/watershed/sketches/briefs/08-cascade/brief-4-runrecord-to-operatorrun.md` and `brief-5-wave-4-consumer-migration.md` — the prior Briefs in this lift wave. Brief 5's "Preserved (do NOT modify)" list named exactly the surface that Brief 6 now removes. Brief 6 is the natural close of Wave 4.
4. `/Users/jakegearon/projects/watershed/sketches/briefs/08-cascade/return-5.md` — Brief 5's Engineer return; the test-pass baseline at session close was 1969 passed, 54 skipped, 3 failed.

The lab vocabulary is fluvial. *quarry* is the boundary module; *flume* (the target module the lift is propagating into) is not yet materialized as its own package — `quarry-operators` and the related quarry-core operator surface will become flume.

## Context — current state (post-Brief 5)

The deprecated-not-deleted surface that Brief 4 retained for one cycle, and that Brief 5 preserved as the read path:

**In `quarry-core`**:
- `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/executor.py`: `RunStatus(Enum)` and `RunRecord(@dataclass)`. The `Executor` Protocol's `submit/status/wait` already return `OperatorRun` (Brief 4 migrated this); the legacy types remain only for back-compat reading.
- `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/__init__.py`: re-exports `RunRecord` and `RunStatus`.

**In `quarry-registry`**:
- `/Users/jakegearon/projects/quarry/packages/quarry-registry/src/quarry_registry/registry.py`:
  - Import line: `from quarry_core.executor import RunRecord, RunStatus`.
  - Method `save_run(record: RunRecord)` — the legacy persister.
  - Method `get_run(run_id) -> RunRecord | None` — the legacy reader.
  - Method `list_runs(status, limit) -> list[RunRecord]` — the legacy lister.
  - Private helper `_save_run_conn` — only called by `save_run`.
  - Private helper `_row_to_run` — only called by `get_run` and `list_runs`.
  - The `stats()` method returns `"runs": run_count` and `"run_statuses": dict(status_counts)` from the legacy `runs` table.
  - The legacy `runs` table is created in `_init_schema` and persists in the DuckDB file.

**In `quarry-cli`**:
- `/Users/jakegearon/projects/quarry/packages/quarry-cli/src/quarry_cli/main.py` line 431: `run = registry.get_run(target_id)` as a fallback in `cmd_checks_show` after `get_operator_run` returns `None`. Brief 5 deliberately preserved this as the legacy-inspection affordance per the SOP's frozen-pin clause. **Bench's decision in Brief 6 is to remove this fallback** — the public API for reading legacy runs is going away; the orphaned `runs` table is data-only (queryable directly via DuckDB if anyone needs to, but not via the Quarry CLI).

**In `tests/pressure_test`**:
- `test_registry_operator_runs.py` lines 175–240 — the deliberate regression test for the deprecated legacy surface. Two test functions: `test_legacy_run_record_paths_still_work` and `test_checks_and_lineage_accept_legacy_and_operator_run_ids`. The first is purely legacy; the second mixes legacy `RunRecord` save with `operator_runs` read assertions. Both are retired in this Brief — the surface they cover is being removed.
- `test_registry.py` line 549: test function `test_save_run_replaces_existing_run_checks` — the substring `save_run` appears in the test name but the body calls `save_operator_run`. Rename to `test_save_operator_run_replaces_existing_run_checks` for accuracy.

**In `examples/`**:
- `examples/watershed_analysis.py` — uses `registry.save_run(zonal_record)` (line 222) and `registry.save_run(cog_record)` (line 267), plus `.status.value` access on lines 219 and 264. Already broken on main: `executor.submit()` returns `OperatorRun`, which has `.state` (str), not `.status` (RunStatus enum). The example needs to be migrated to the post-Brief-4 surface; doing so in this Brief is the natural close. The `_inspect_phase` print on line 298 (`print(f"  Run statuses: {stats['run_statuses']}")`) also needs to update to match the new `stats()` shape.

**In top-level docs**:
- `README.md`, `REPO_MAP.md`, `CONTRACTS.md`, `HYDROLOGY_PACK.md`, `PRESSURE_TESTS.md` carry 11 prose references to `RunRecord`, `RunStatus`, `save_run`, `get_run`, `list_runs`. These describe behavior that is being deleted; leaving them creates contradictions with the post-Brief-6 reality.

## What you are doing in Brief 6

Remove the deprecated legacy run surface from `quarry-core` and `quarry-registry`. Update consumers (`quarry-cli/main.py` line 431 fallback, `examples/watershed_analysis.py`). Retire the deliberate legacy regression test in `test_registry_operator_runs.py`. Rename the substring-trapped test in `test_registry.py`. Clean up doc references in the five top-level markdown files. Verify the full pressure_test path returns to or near Brief 5's baseline of 1969 passing, 54 skipped, 3 failed (the legacy regression test's removal will drop the passing count by 2 — that's the expected delta).

Leave the `runs` table schema in place as orphaned data. Dropping the table is a destructive change that affects on-disk DuckDB files in the wild; it can be a future Brief if the Source wants it. Brief 6 removes the API surface, not the data.

## Items

### Item A — Remove `RunRecord` and `RunStatus` from `quarry-core/executor.py`

In `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/executor.py`:

1. Delete the `class RunStatus(Enum):` definition (the five-member enum: PENDING/RUNNING/COMPLETED/FAILED/CANCELLED) and its docstring.
2. Delete the `@dataclass class RunRecord:` definition and its docstring, including the `checks` and `duration_seconds` properties.
3. Remove the now-unused imports if any (`Enum` may still be needed elsewhere — check; `dataclass` is fine).
4. The `Executor` Protocol and its `submit/status/wait` methods stay — they already return `OperatorRun`. The supporting types (`ExecutorError`, `RunNotFoundError`, `SubmitError`) stay.
5. The module's top-of-file docstring still says "Get back a run record"; update to "Get back an OperatorRun."

The `quarry_core.artifact.CheckResult` import in `executor.py` may now be unused (it was only consumed by `RunRecord.checks` property); remove the import if it becomes unused. The `Any` import may now be unused too (was used by `RunRecord.params: dict[str, Any]`); remove if unused.

### Item B — Remove `RunRecord` and `RunStatus` from `quarry-core/__init__.py`

In `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/__init__.py`:

1. Remove `RunRecord,` and `RunStatus,` from the `from quarry_core.executor import (...)` import block.
2. Remove `"RunRecord",` and `"RunStatus",` from the `__all__` list.

### Item C — Remove `save_run` / `get_run` / `list_runs` from `quarry-registry/registry.py`

In `/Users/jakegearon/projects/quarry/packages/quarry-registry/src/quarry_registry/registry.py`:

1. Remove the import: `from quarry_core.executor import RunRecord, RunStatus`. (Keep the `from quarry_core.operator_run import OperatorRun, OperatorRunState` import — that's the going-forward shape.)
2. Delete the `save_run` method (full definition including transaction body and docstring).
3. Delete the `get_run` method (full definition including the connect/select/return body and docstring).
4. Delete the `list_runs` method (full definition including the conditional filter and reconstruction loop).
5. Delete the private helper `_save_run_conn` (it has no other callers after `save_run` is gone).
6. Delete the private helper `_row_to_run` (no other callers after `get_run` and `list_runs` are gone — verify; the only references are inside `get_run` and `list_runs`).
7. Update the `stats()` method to:
   - Remove the `run_row = conn.execute("SELECT COUNT(*) FROM runs").fetchone()` query.
   - Remove the `status_counts = conn.execute("SELECT status, COUNT(*) FROM runs GROUP BY status").fetchall()` query.
   - Remove the `run_count = run_row[0]` line and the `run_row is None` guard.
   - Remove `"runs": run_count` and `"run_statuses": dict(status_counts)` from the returned dict.
   - Keep `"operator_runs"`, `"operator_run_states"`, `"artifacts"`, `"checks"`, `"lineage_edges"`, `"artifact_types"`.
8. Leave the `CREATE TABLE IF NOT EXISTS runs (...)` block in `_init_schema` untouched — the table schema stays as orphaned-data per Bench's design decision (dropping the table is a destructive change for any on-disk DuckDB files; a separate future preflight decides that).
9. Leave the `_delete_run_checks_conn` helper untouched — `save_operator_run` still calls it.
10. Update the module's top-of-file docstring if it mentions the legacy run surface (read; the existing docstring talks about "Artifacts, runs, checks, and lineage each get their own table" — update to "Artifacts, operator runs, checks, and lineage each get their own table" or similar).

### Item D — Remove `quarry-cli/main.py` legacy fallback

In `/Users/jakegearon/projects/quarry/packages/quarry-cli/src/quarry_cli/main.py`:

1. In `cmd_checks_show`, delete the two-line legacy fallback at approximately lines 430–431:
   ```python
   if run is None:
       run = registry.get_run(target_id)
   ```
2. The function continues with `if artifact is None and run is None:` which handles the "not found" case correctly. No other changes needed in this file.

### Item E — Migrate `examples/watershed_analysis.py` to the post-Brief-4 surface

In `/Users/jakegearon/projects/quarry/examples/watershed_analysis.py`:

1. Replace `# Execute through the executor for proper RunRecord tracking` (~line 213) with `# Execute through the executor for proper OperatorRun tracking`.
2. Replace `if zonal_record.status.value != "completed" or zonal_record.output is None:` (~line 219) with `if zonal_record.state != "completed" or zonal_record.output is None:`. (`OperatorRun.state` is a plain `str` literal, not an enum, so `.value` is not needed.)
3. Replace `registry.save_run(zonal_record)` (~line 222) with `registry.save_operator_run(zonal_record)`.
4. Replace `if cog_record.status.value != "completed" or cog_record.output is None:` (~line 264) with `if cog_record.state != "completed" or cog_record.output is None:`.
5. Replace `registry.save_run(cog_record)` (~line 267) with `registry.save_operator_run(cog_record)`.
6. In `_inspect_phase` (~line 298), replace:
   ```python
   print(
       f"  Registry: {stats['artifacts']} artifacts, {stats['runs']} runs, "
       f"{stats['checks']} checks, {stats['lineage_edges']} lineage edges"
   )
   ...
   print(f"  Run statuses: {stats['run_statuses']}")
   ```
   with:
   ```python
   print(
       f"  Registry: {stats['artifacts']} artifacts, {stats['operator_runs']} operator runs, "
       f"{stats['checks']} checks, {stats['lineage_edges']} lineage edges"
   )
   ...
   print(f"  Operator run states: {stats['operator_run_states']}")
   ```

If the example references `RunRecord` or `RunStatus` anywhere else in the file (recon counted 1 doc-comment + 5 code references, all in `_analyze_phase` and `_export_phase`), update those too.

### Item F — Retire / rename test files; clean doc references

**Test changes:**

1. In `/Users/jakegearon/projects/quarry/tests/pressure_test/test_registry_operator_runs.py`:
   - Delete the `from quarry_core.executor import RunRecord, RunStatus` import (line 7).
   - Delete the entire `test_legacy_run_record_paths_still_work` function (the test the legacy `save_run` / `get_run` / `list_runs` regression covered).
   - Delete the entire `test_checks_and_lineage_accept_legacy_and_operator_run_ids` function. **If** the second test has assertions about the `operator_runs` table (the "and operator run ids" half) that are not redundant with other tests in the file, preserve those assertions by either (a) inlining them as a new test that does not touch the legacy `RunRecord` surface, or (b) confirming they are covered elsewhere in the same file. Use your judgment; the goal is to remove the legacy surface without losing operator_runs coverage.
   - Adjust imports accordingly. The file should still import whatever it needs to test the `operator_runs` path; just no `RunRecord`/`RunStatus`.

2. In `/Users/jakegearon/projects/quarry/tests/pressure_test/test_registry.py`:
   - Rename the function `test_save_run_replaces_existing_run_checks` (line 549) to `test_save_operator_run_replaces_existing_run_checks` for naming accuracy. The body already calls `save_operator_run`; just the function name changes.

**Doc cleanup** (in top-level docs, all references that describe the deprecated surface):

3. `/Users/jakegearon/projects/quarry/README.md`: update the `RunRecord` reference (~line 34) to `OperatorRun` and adjust any surrounding prose.
4. `/Users/jakegearon/projects/quarry/REPO_MAP.md`: update line ~21's `executor.py # Executor protocol, RunRecord, RunStatus` to `executor.py # Executor protocol`.
5. `/Users/jakegearon/projects/quarry/CONTRACTS.md`: update the four references on lines ~110, ~112, ~113, ~132 — `RunRecord` → `OperatorRun`, `RunStatus.FAILED` → `state == "failed"`, `save_run()` → `save_operator_run()`, adjust prose to match the new shape (e.g., the legacy "RunRecord is the full lifecycle object" line becomes a description of OperatorRun).
6. `/Users/jakegearon/projects/quarry/HYDROLOGY_PACK.md`: line ~120's `save_run()` → `save_operator_run()`.
7. `/Users/jakegearon/projects/quarry/PRESSURE_TESTS.md`: update lines ~15, ~34, ~35, ~667, ~668 — replace `RunRecord` with `OperatorRun`, `save_run` with `save_operator_run`, `get_run` with `get_operator_run`, `list_runs` with `list_operator_runs`. The intent of these mentions is to describe the existing test coverage; preserve the intent while updating the names.

Use your judgment on the doc edits — the goal is "no remaining doc reference to the deleted surface that would mislead a future reader." If a sentence loses meaning when names are swapped, rewrite it to describe the post-Brief-6 reality.

### Item G — Verify the full test surface

Run `uv run pytest -q tests/pressure_test/` and verify:

- The result is approximately **1967 passed, 54 skipped, 3 failed** (Brief 5's 1969 baseline minus the two legacy regression tests deleted in Item F).
- The 3 known failures are the Source's pre-existing GeoJSON/router/docs connector work, unchanged from Brief 5.
- If the failing-test count drops below 3 or rises above 3 (excluding the known connector failures), report exactly which tests changed status.
- If the passing-test count is not in the 1965–1969 range, report the exact deviation and which tests differ from expected.

Also run:
- `uv run ruff check` on edited files (or repo-wide).
- `uv run ty check` if any type annotations changed in `quarry-core` or `quarry-registry` (Items A, B, C touch the `Executor` Protocol's docstring but not its types; Item C does not change `Registry`'s public type surface beyond removing methods).

Run `examples/watershed_analysis.py` end-to-end if possible (`uv run python examples/watershed_analysis.py`) and confirm it completes successfully — Brief 5 didn't migrate this and it's been broken on main; Brief 6 fixes it. If the example fails for reasons unrelated to the Brief 6 migration (e.g., missing system rasterio dependency), report the failure and move on; the test-suite result is the primary gate.

## Constraints

- **Write only inside the write scope below.** Any write outside is an integration failure.
- **Do not modify `/Users/jakegearon/projects/watershed/`.** SOPs, CANON, lineage entries are the Watermaster's domain.
- **Do not drop the `runs` table** in `_init_schema`. Bench's design decision is that the table stays as orphaned data; only the API surface comes out. A future Brief decides whether to drop the table.
- **Do not change `OperatorRun`, `OperatorRunState`, `OperatorSpec`, `OperatorResult`, `Artifact`, `Lineage`, or any other typed surface from Briefs 1–5.** Their shape is settled.
- **Do not introduce new public methods on `Registry`.** Brief 6 is purely subtractive (plus the `stats()` keys that come out).
- **Do not silently change the order of remaining `Registry` methods or their behavior.** Move only the lines being deleted; leave the rest of the file alone.
- **If you see useful adjacent work outside the scope, flag it in the return rather than writing it.** (Repeating from prior Briefs as discipline.)
- **One coherent change set:** remove the deprecated legacy run API surface across all consumers and docs in lockstep. No partial state where one consumer still references the deleted types.

## Write scope

```
/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/executor.py
/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/__init__.py
/Users/jakegearon/projects/quarry/packages/quarry-registry/src/quarry_registry/registry.py
/Users/jakegearon/projects/quarry/packages/quarry-cli/src/quarry_cli/main.py
/Users/jakegearon/projects/quarry/examples/watershed_analysis.py
/Users/jakegearon/projects/quarry/tests/pressure_test/test_registry_operator_runs.py
/Users/jakegearon/projects/quarry/tests/pressure_test/test_registry.py
/Users/jakegearon/projects/quarry/README.md
/Users/jakegearon/projects/quarry/REPO_MAP.md
/Users/jakegearon/projects/quarry/CONTRACTS.md
/Users/jakegearon/projects/quarry/HYDROLOGY_PACK.md
/Users/jakegearon/projects/quarry/PRESSURE_TESTS.md
```

You may also read freely anywhere in `/Users/jakegearon/projects/quarry/` and `/Users/jakegearon/projects/watershed/`.

## Out of scope

- Dropping the `runs` table schema. Future preflight; Brief 6 keeps it as orphaned data.
- Migration of pre-existing uuid4-id `RunRecord` rows from the `runs` table into the `operator_runs` table. Bench's design decision is that these are historical-only data; the lab does not preserve API access to old uuid4-id rows via the typed `OperatorRun` shape, because doing so would require fabricating typed fields the historical data never had.
- Thread B (the 8 dual-residence gaps from Brief 2). Separate Briefs (7 for scalars, 8 for rasters).
- DispatchRun-side `RunRecord` migration (the dgov analogue). Separate recon-first arc.
- Any change to `OperatorRun`, `OperatorSpec`, `OperatorResult`, `Artifact`, or any Brief 1/2/3/4/5 type or helper.
- Any change to `hydrops/` or `quarry-explorer/` (recon confirmed they don't consume the legacy run surface).
- Lifting types from quarry into `watershed/shared/` (the broader flume lift continues in future Briefs).

## Verify (before submitting)

- `quarry-core/executor.py` no longer defines `RunRecord` or `RunStatus`. The `Executor` Protocol is unchanged in shape (already returns `OperatorRun` from Brief 4). The supporting error types (`ExecutorError`, `RunNotFoundError`, `SubmitError`) remain.
- `quarry-core/__init__.py` no longer imports or re-exports `RunRecord` / `RunStatus`. `OperatorRun` and friends remain.
- `quarry-registry/registry.py` no longer defines `save_run`, `get_run`, `list_runs`, `_save_run_conn`, or `_row_to_run`. `save_operator_run`, `get_operator_run`, `list_operator_runs` remain unchanged.
- `quarry-registry/registry.py`'s `stats()` no longer queries the `runs` table for counts or status breakdowns. The returned dict has no `"runs"` or `"run_statuses"` key.
- `quarry-registry/registry.py`'s `_init_schema` still creates the `runs` table (orphaned-data; not removed).
- `quarry-cli/main.py`'s `cmd_checks_show` has no `registry.get_run(...)` fallback.
- `examples/watershed_analysis.py` runs end-to-end (or fails only for reasons unrelated to Brief 6); no references to `RunRecord`, `RunStatus`, `save_run`, `.status` remain in the file.
- `test_registry_operator_runs.py` no longer imports `RunRecord` or `RunStatus`; the legacy-only test function is removed; the dual-coverage test function is either removed or refactored to test only the operator_runs side.
- `test_registry.py`'s function `test_save_run_replaces_existing_run_checks` is renamed to `test_save_operator_run_replaces_existing_run_checks`.
- No grep across `packages/`, `tests/`, `examples/`, top-level docs returns a match for `\bRunRecord\b`, `\bRunStatus\b`, `\bsave_run\b` (not `save_operator_run`), `\bget_run\b` (not `get_operator_run`), `\blist_runs\b` (not `list_operator_runs`), except inside `git log` history.
- Full `tests/pressure_test/` pytest returns approximately 1967 passed, 54 skipped, 3 failed (or a clean accounting of any deviation).
- `ruff check` passes on the edited files.
- No file outside the write scope has been modified.

## Return shape

Return a chat message structured as:

1. **Summary** — one paragraph naming what landed.
2. **Item-by-item** — A through G, each with: what was changed, file paths touched, any judgment calls, any unexpected findings.
3. **Test results** — full pressure_test pytest count (passed/skipped/failed); note any deviation from the expected 1967/54/3 with explicit accounting. Also `ruff check` result. Confirm whether `examples/watershed_analysis.py` runs end-to-end.
4. **Flag list** — every place where the removal can't proceed cleanly (e.g., second test in `test_registry_operator_runs.py` had operator_runs assertions that needed preservation; doc sentences that lost meaning when names were swapped and were rewritten), with one-line context.

The Watermaster will integrate your return: verify writes are within scope, audit the test deltas, and either commit the work as-is or send a follow-up Brief.

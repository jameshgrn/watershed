# Engineer Brief — Brief 5 (Wave 4 consumer migration: HydrologyFlow + tests)

**engineer_model**: `codex-gpt-5` (the seated Codex instance the Source is using; confirm exact identifier at transmission)
**source_utterance** (verbatim, with bracketed context for an Engineer who didn't see the chat):
> "wawtershed" [Source's entry signal opening the session]
>
> "1" [Source's selection of Brief 4 from Cascade's three-arc offering]
>
> "approved ill send iot now" [Source's approval and transmission of Brief 4]
>
> [Source carried Brief 4 to Codex; Codex returned cleanly with three flagged out-of-scope consumers still on the legacy `RunRecord`/`RunStatus`/`save_run`/`list_runs`/`.status` surface; Cascade integrated Brief 4 and presented three paths]
>
> "go 1" [Source's selection of path 1: draft Brief 5 now to close the Wave 4 consumer migration]

**compiled_by**: Watermaster Cascade
**compiled_at**: 2026-05-11
**state**: integrated (drafted 2026-05-11 → sent 2026-05-11 → returned 2026-05-11 → integrated 2026-05-11)
**supersedes**: none
**expected_return_shape**: executed file writes within the write scope below, plus a chat return summarizing each item (A–E), any deviations, and test run results.

---

## Read these before starting

You are an external Engineer consulted by the Watermaster of a research lab called *watershed*. You read only this Brief. You executed Briefs 1, 2, 3, and 4 in prior sessions, all integrated cleanly.

Read the following files first — they are the discipline this Brief implements:

1. `/Users/jakegearon/projects/watershed/CANON.md` — Articles II (one canonical writer), IV (every Artifact carries its lineage), IX (the Watermaster works through typed surfaces), XV (typed records are frozen-pinned at lifecycle transitions).
2. `/Users/jakegearon/projects/watershed/sops/operator-run-shape.md` v1 — the SOP Brief 4 implemented in `quarry-core` and `quarry-registry`. The relevant escalate clause for migration discipline: *"frozen-pin existing uuid4 RunRecords at their quarry-core state and mint new OperatorRuns under this SOP for going-forward executions."*
3. `/Users/jakegearon/projects/watershed/sketches/briefs/08-cascade/brief-4-runrecord-to-operatorrun.md` — the prior Brief, integrated. The new typed surfaces it landed are the surfaces this Brief now propagates to consumers.
4. `/Users/jakegearon/projects/watershed/sketches/briefs/08-cascade/return-4.md` — the Engineer return for Brief 4. The "Flags (escalate territory)" section names exactly the consumers this Brief migrates.

The lab vocabulary is fluvial. *quarry* is the boundary module; *quarry-operators* is one of its packages; *flume* (the target module the lift is propagating into) is not yet materialized as its own package — `quarry-operators` will be the parts that become flume.

## Context — current state (post-Brief 4)

After Brief 4, the new surface is in `quarry-core` and `quarry-registry`:

- `OperatorRun` lives at `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/operator_run.py`. Frozen, content-derived id, five-state lifecycle (`pending | running | completed | failed | cancelled`), state-transition methods (`start_running`, `complete`, `fail`, `cancel`).
- `OperatorRunState = Literal["pending", "running", "completed", "failed", "cancelled"]`.
- `LocalExecutor.submit/status/wait` return `OperatorRun`.
- Registry has `save_operator_run(record)`, `get_operator_run(id)`, `list_operator_runs(state=..., operator_name=..., limit=...)`. New `operator_runs` table.
- Legacy `RunRecord` + `RunStatus` + `save_run`/`get_run`/`list_runs` retained as deprecated-not-deleted; the legacy `runs` table is frozen-pinned per the SOP. **Do not remove these in this Brief.**

The CLI (`packages/quarry-cli/src/quarry_cli/main.py`) was migrated by Brief 4 except for one line: `run = registry.get_run(target_id)` as a fallback for legacy uuid4 records. **This fallback is correct and stays** — it preserves user inspection of legacy persisted runs per the SOP's frozen-pin escalate clause.

The three flags Brief 4 raised, plus what Brief 4's recon missed: nine files still reference the legacy run surface. They divide as follows:

**Primary consumer (public API change required)**:
- `packages/quarry-operators/src/quarry_operators/hydrology_flow.py` — calls `registry.save_run()`, reads `run_record.status != RunStatus.COMPLETED`, types its `HydrologyFlowSuccess.runs` and `HydrologyFlowFailure.runs` as `list[RunRecord]`.

**Tests to migrate** (mechanical, mostly find-and-replace):
- `tests/pressure_test/test_hydrology_flow.py` — imports `RunStatus`, asserts `run.status == RunStatus.COMPLETED` on lines 140 and 316.
- `tests/pressure_test/test_generic_dispatch.py` — calls `registry.list_runs()` on lines 594, 616, 634 plus surrounding `.status` assertions.
- `tests/pressure_test/test_cli_inspection.py` — seven `registry.list_runs()` calls (lines 152, 166, 175, 184, 193, 228, 287).
- `tests/pressure_test/test_cli_rasterize.py` — four `list_runs()` calls (lines 187, 225, 753, 780); one `make_invalid_completed_run()` import + use (line 30 import, line 590 use).
- `tests/pressure_test/test_cli_zonal.py` — one `list_runs()` call (line 366); `make_invalid_completed_run()` import + use (line 32 import, line 374 use).
- `tests/pressure_test/test_cli_sample.py` — four `list_runs()` calls (lines 227, 456, 648, 675); `make_invalid_completed_run()` import + use (line 34 import, line 471 use).
- `tests/pressure_test/test_reproject.py` — `save_run()` + `get_run()` + `.status` assertion (lines 415, 418, 419).

**Adapter-helper cleanup**:
- `tests/pressure_test/adapter_helpers.py` — currently exposes `make_invalid_completed_run` and `make_failed_run` as aliases wrapping `make_invalid_completed_operator_run` / `make_failed_operator_run`. With consumers migrated, the aliases come out.

**Preserved** (do NOT modify):
- `packages/quarry-core/src/quarry_core/executor.py` — `RunRecord` + `RunStatus` stay deprecated-not-deleted.
- `packages/quarry-registry/src/quarry_registry/registry.py` — `save_run` / `get_run` / `list_runs` stay as the legacy read path.
- `tests/pressure_test/test_registry_operator_runs.py` lines 7, 178–190, 204–216 — the explicit legacy `RunRecord` round-trip regression test. This is the deliberate coverage of the deprecated legacy surface.

## What you are doing in Brief 5

Propagate Brief 4's new typed surface (`OperatorRun`, `OperatorRunState`, `save_operator_run`, `list_operator_runs`) into the consumers Brief 4 deliberately left out of its `write_scope`: `HydrologyFlow` (the primary consumer, with public API change to its result types) plus seven test files. Then remove the temporary `make_invalid_completed_run` / `make_failed_run` aliases in `adapter_helpers.py` once all callers use the operator-run-named helpers.

Verify the full pressure_test path returns to its Brief 3 baseline of 1949 passing (modulo any known Source-side connector failures unrelated to the migration).

## Items

### Item A — Rewrite `hydrology_flow.py`

In `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/hydrology_flow.py`:

1. Change the import line `from quarry_core.executor import RunRecord, RunStatus` to `from quarry_core.operator_run import OperatorRun`.
2. Update both `HydrologyFlowSuccess.runs` and `HydrologyFlowFailure.runs` field types from `list[RunRecord]` to `list[OperatorRun]`.
3. In the three `if run_record.status != RunStatus.COMPLETED:` guards (lines 212, 235, 258), replace `.status != RunStatus.COMPLETED` with `.state != "completed"`.
4. In `_execute_step`, change `self._registry.save_run(run_record)` to `self._registry.save_operator_run(run_record)` (line 301).
5. Update the function signature `_execute_step(...) -> RunRecord:` to `... -> OperatorRun:` and the local annotation `run_record: RunRecord` (used as accumulator type at the top of `run`) to `OperatorRun`.
6. Update docstrings that mention `RunRecord` or `.status` to reflect the new types.

The `runs: list[OperatorRun]` change in the result dataclasses is a public API change. Any external caller (notebooks, scripts) that destructures `result.runs` and pattern-matches on `.status` will break. Within the in-repo surface, the test migrations in Items B–C cover all callers.

### Item B — Migrate `test_hydrology_flow.py`

In `/Users/jakegearon/projects/quarry/tests/pressure_test/test_hydrology_flow.py`:

1. Remove the import `from quarry_core.executor import RunStatus`.
2. Replace `run.status == RunStatus.COMPLETED` at line 140 with `run.state == "completed"`.
3. Replace the same pattern at line 316 the same way.
4. If any other `.status` assertions exist on run records in this file (recon counted two but verify completeness), apply the same migration.

### Item C — Migrate the remaining six test files

The migration in each is mechanical:

- `from quarry_core.executor import RunStatus` → remove the import.
- `from quarry_core.executor import RunRecord` → replace with `from quarry_core.operator_run import OperatorRun` if RunRecord is being constructed in the test; otherwise just remove.
- `registry.list_runs(...)` → `registry.list_operator_runs(...)`.
- `registry.list_runs(status=RunStatus.COMPLETED)` → `registry.list_operator_runs(state="completed")` (the keyword changes from `status` to `state`, and the value from Enum to string literal).
- `registry.save_run(record)` → `registry.save_operator_run(record)` (in `test_reproject.py`).
- `registry.get_run(id)` → `registry.get_operator_run(id)` (in `test_reproject.py`).
- `run.status == RunStatus.X` → `run.state == "x"` (where X is COMPLETED, FAILED, PENDING, RUNNING, CANCELLED; the literal-string equivalent is lowercased).
- `run.status != RunStatus.X` → `run.state != "x"`.
- `make_invalid_completed_run()` → `make_invalid_completed_operator_run()`.
- `make_failed_run()` → `make_failed_operator_run()`.

Apply to:
- `tests/pressure_test/test_generic_dispatch.py`
- `tests/pressure_test/test_cli_inspection.py`
- `tests/pressure_test/test_cli_rasterize.py`
- `tests/pressure_test/test_cli_zonal.py`
- `tests/pressure_test/test_cli_sample.py`
- `tests/pressure_test/test_reproject.py`

If any test constructs a `RunRecord` directly (not via an executor or a helper), prefer rewriting it to construct an `OperatorRun` with realistic field values (operator_spec_hash, determinism_class, params_hash, dispatched_by, etc.). Recon did not flag any such case outside `test_registry_operator_runs.py` (which is preserved), but watch for it.

### Item D — Remove deprecated aliases from `adapter_helpers.py`

In `/Users/jakegearon/projects/quarry/tests/pressure_test/adapter_helpers.py`:

1. After Item C has been applied (no callers of the legacy aliases remain), delete the `make_invalid_completed_run` alias (lines 94–95) and `make_failed_run` alias (lines 98–99).
2. Confirm `make_invalid_completed_operator_run` and `make_failed_operator_run` remain as the canonical helpers.

If any test still imports the deprecated aliases after Item C, the test wasn't migrated correctly — flag it; don't restore the alias.

### Item E — Verify the full test surface

Run the full pressure_test path (`uv run pytest -q tests/pressure_test/`) and verify it returns to (or near) the Brief 3 baseline of 1949 passing, 54 skipped, 3 failed. The 3 known failures are the Source's pre-existing in-progress connector work; they may still be present. If the failing-test count drops below 3 or rises above 3 (excluding the known connector failures), report exactly which tests changed status.

Also run:
- `uv run ruff check` on edited files.
- `uv run ty check` on the edited core/operators/CLI surface if you make any type-annotation changes that touch quarry-core or quarry-cli.

## Constraints

- **Write only inside the write scope below.** Any write outside is an integration failure.
- **Do not modify `/Users/jakegearon/projects/watershed/`.** SOPs, CANON, lineage entries are the Watermaster's domain.
- **Do not delete or modify `RunRecord` / `RunStatus` in `executor.py`.** They stay deprecated-not-deleted per Brief 4's discipline.
- **Do not delete or modify the legacy `save_run` / `get_run` / `list_runs` methods in `registry.py`.** They remain the read path for legacy uuid4 records.
- **Do not modify the legacy `runs` table schema.** Frozen-pinned per the SOP.
- **Do not modify `test_registry_operator_runs.py`.** Its legacy `RunRecord` round-trip test is the deliberate regression coverage for the deprecated legacy surface; preserving it is exactly the point.
- **Do not modify `quarry-cli/main.py`'s line 431 `get_run` fallback.** It is the correct legacy-inspection affordance per the SOP's frozen-pin clause.
- **Do not touch Brief 1, 2, 3, or 4 work.** OperatorSpec / OperatorResult / Artifact / OperatorRun / registry's operator_runs path stays as is.
- **Do not invent new operator-run lifecycle states.** The five-state lifecycle is canonical.
- **If you see useful adjacent work outside the scope, flag it in the return rather than writing it.** (Repeating from prior Briefs as discipline.)
- **One coherent change set.**

## Write scope

```
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/hydrology_flow.py
/Users/jakegearon/projects/quarry/tests/pressure_test/test_hydrology_flow.py
/Users/jakegearon/projects/quarry/tests/pressure_test/test_generic_dispatch.py
/Users/jakegearon/projects/quarry/tests/pressure_test/test_cli_inspection.py
/Users/jakegearon/projects/quarry/tests/pressure_test/test_cli_rasterize.py
/Users/jakegearon/projects/quarry/tests/pressure_test/test_cli_zonal.py
/Users/jakegearon/projects/quarry/tests/pressure_test/test_cli_sample.py
/Users/jakegearon/projects/quarry/tests/pressure_test/test_reproject.py
/Users/jakegearon/projects/quarry/tests/pressure_test/adapter_helpers.py
```

You may also read freely anywhere in `/Users/jakegearon/projects/quarry/` and `/Users/jakegearon/projects/watershed/`.

## Out of scope

- Removal of `RunRecord` / `RunStatus` from `quarry-core/executor.py`. Future Brief.
- Removal of legacy `save_run` / `get_run` / `list_runs` from `quarry-registry/registry.py`. Future Brief.
- Migration of pre-existing uuid4-id `RunRecord` rows in the `runs` table. Frozen-pinned per the SOP.
- CLI line 431 `get_run` fallback (intentionally preserved for legacy inspection).
- The 8 dual-residence gaps flagged in Brief 2 (Thread B; design conversation needed).
- The three-agent-class CANON article (separate preflight).
- Any change to `OperatorRun`, `OperatorSpec`, `OperatorResult`, `Artifact`, or any Brief 1/2/3/4 type or helper.
- Any change to `hydrops/` or `quarry-explorer/` (recon confirmed they don't consume the legacy run surface).

## Verify (before submitting)

- `quarry-operators/src/quarry_operators/hydrology_flow.py` no longer imports `RunRecord` or `RunStatus`. Imports `OperatorRun` instead.
- `HydrologyFlowSuccess.runs` and `HydrologyFlowFailure.runs` are typed as `list[OperatorRun]`.
- All three `.status != RunStatus.COMPLETED` guards in `_execute_step` callers are now `.state != "completed"`.
- `_execute_step` calls `save_operator_run` instead of `save_run`.
- No test under `tests/pressure_test/` (other than `test_registry_operator_runs.py`'s legacy regression test) imports `RunStatus` or constructs `RunRecord`.
- `make_invalid_completed_run` and `make_failed_run` aliases are deleted from `adapter_helpers.py`.
- No test imports the deleted aliases (grep for both names returns matches only inside `adapter_helpers.py`'s `make_*_operator_run` definitions, if any reference for parity).
- Full `tests/pressure_test/` pytest returns to (or near) Brief 3 baseline of 1949 passing, 54 skipped, 3 failed (or a clean accounting of any deviation).
- `ruff check` passes on the edited files.
- `quarry-cli/main.py` is unchanged.
- `quarry-core/executor.py` is unchanged.
- `quarry-registry/registry.py` is unchanged.
- `test_registry_operator_runs.py` is unchanged.
- No file outside the write scope has been modified.

## Return shape

Return a chat message structured as:

1. **Summary** — one paragraph naming what landed.
2. **Item-by-item** — A through E, each with: what was changed, file paths touched, any judgment calls, any unexpected findings.
3. **Test results** — full pressure_test pytest count (passed/skipped/failed); note any deviation from the 1949/54/3 Brief 3 baseline with explicit accounting of which tests changed status. Also `ruff check` result.
4. **Flag list** — every place where the migration discipline can't proceed cleanly, with one-line context.

The Watermaster will integrate your return: verify writes are within scope, audit the test deltas, and either commit the work as-is or send a follow-up Brief.

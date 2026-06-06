# Recon — Brief 9 (DispatchRun-side `RunRecord` migration in dgov)

**Author**: Watermaster Bench
**Date**: 2026-05-13
**Purpose**: Recon-only deliverable for the next Watermaster who takes up the DispatchRun-side migration arc. The Source delegated three substantive arcs (Brief 6, Thread B, DispatchRun) on 2026-05-13; Briefs 6, 7, and 8 closed two of them. This recon prepares the third for drafting in a subsequent session without re-discovering dgov state.
**Status**: foundation-ready. The next Watermaster can draft Brief 9 from this recon modulo the Source-side design questions noted at the end.
**Filename convention**: extends `engineer-brief.md` v2's `sketches/briefs/{NN-watermaster}/` interim home with a third file class (`recon-{N}.md`) parallel to `brief-{N}-{slug}.md` and `return-{N}.md`. Single use so far; not yet a canonicalized convention — Live observation, to consider folding into `engineer-brief.md` v3 if it recurs.

---

## I. Branch settling status

- `codex/boundary-ownership-cleanup` merged into `main` as PR #24 (`65d7392b`) on **2026-05-11 14:16:31 -0400**. The "actively evolving" branch Pool, Cascade, and Confluence flagged as a gating concern is settled.
- Post-merge through 2026-05-14, the only commits touching `runner.py` / `kernel.py` / `settlement.py` / `settlement_flow.py` / `worker.py` / `persistence/events.py` / `persistence/runtime_artifacts.py` / `types.py` / `actions.py` are five non-structural changes (Sentrux gate diff-awareness, governor UX preflight, scope status, transient writes scope, cross-file semantic settlement). `kernel.py`, `types.py`, `actions.py` are unchanged on main since the merge.
- No active remote branch shows commits touching the structural files ahead of `origin/main`.
- **Verdict**: main is settled enough to draft against. Brief 9 territory is no longer gated.

## II. Current execution-record types in dgov

dgov has **no `RunRecord` analogue** — no single typed record represents "this dispatch attempt." Information is fragmented across five sites:

1. **`TaskState`** enum — `src/dgov/types.py:21-36`. 13-value `StrEnum`.

2. **`WorkerExit`** (frozen dataclass) — `src/dgov/types.py:42-52`. Terminal exit telemetry only:
   ```python
   task_slug, pane_slug, exit_code, output_dir,
   last_error="", prompt_tokens=0, completion_tokens=0
   ```

3. **`Worktree`** (NamedTuple) — `src/dgov/types.py:58-63`. `path`, `branch`, `commit`. Base-commit identity tied to git, not to a dispatch record.

4. **`WorkerTask`** (frozen dataclass, persistence row) — `src/dgov/persistence/schema.py:79-109`. The closest cached snapshot of "this task is running here":
   ```python
   slug, agent, project_root, worktree_path, branch_name,
   prompt, task_id, created_at, owns_worktree, base_sha,
   role, state: TaskState, plan_name, file_claims, commit_message
   ```
   Header docstring is explicit: *"Lifecycle truth comes from events, not from this cached snapshot."* This is bookkeeping, not a typed execution record.

5. **`TaskContext`** (in-memory `@dataclass`, **not frozen**) — `src/dgov/runner.py:131-147`. Per-task mutable runtime state:
   ```python
   pane_slug, attempts, error, start_time, duration, worktree,
   worker_task, rejected_worktree, call_count, fork_depth,
   review_file_count, prompt_tokens, completion_tokens
   ```
   The de-facto carrier for retry/fork counters and accumulated telemetry. Mutated freely; never persisted as a record.

6. **Event-log rows** — `persistence/events.py`, `event_types.py`. ~30 frozen event dataclasses (`EvtTaskDispatched`, `TaskDone`, `TaskFailed`, `TaskAbandoned`, `IterationFork`, `GovernorResumed`, etc.). The event stream is source-of-truth for lifecycle per `live_state.py`, but no event aggregates a dispatch's identity, base commit, agent model, bundle hash, lineage links, and exit telemetry into a single record.

## III. Lifecycle states — what belongs where

Full `TaskState` enum at `types.py:21-36`:
`pending, active, done, failed, reviewing, reviewed_pass, reviewed_fail, merging, merged, timed_out, closed, abandoned, skipped`.

Mapped against `dispatch-run-shape.md` v1 discipline:

| TaskState | Belongs to (per SOP) | Notes |
|---|---|---|
| `pending` | DispatchRun | matches SOP |
| `active` | DispatchRun | matches SOP |
| `done` | DispatchRun | matches SOP |
| `failed` | DispatchRun | matches SOP |
| `timed_out` | DispatchRun | matches SOP |
| `abandoned` | DispatchRun | matches SOP |
| `reviewing` | **Validation** | SOP "Do Not" §47 |
| `reviewed_pass` | **Validation** | SOP "Do Not" §47 |
| `reviewed_fail` | **Validation** | SOP "Do Not" §47 |
| `merging` | **Merge** | SOP "Do Not" §47 |
| `merged` | **Merge** | SOP "Do Not" §47 |
| `closed` | (operational) | watershed-foreign sweep state |
| `skipped` | (operational/cascade) | cascaded by `_cascade_failure` in `kernel.py:204-219` |

`VALID_TRANSITIONS` at `persistence/schema.py:31-63` shows `active` can transition to `done | failed | abandoned | timed_out | closed`. The SOP six-state subset is exactly there, plus `closed`. dgov's `active → done` then chains through `reviewing → reviewed_pass → merging → merged` — four states the SOP wants on downstream typed records (Deposit / Validation / Merge), not on DispatchRun.

## IV. Dispatch construction site

`src/dgov/runner.py:1591-1624` (`_dispatch` method) is where the worker subprocess is launched. The closest current "construct the dispatch record" call is `_record_dispatch_artifact` at `runner.py:1671-1693`:
```python
record_runtime_artifact(
    self.session_root,
    WorkerTask(
        slug=action.task_slug, prompt=prompt, agent=agent,
        project_root=self.session_root,
        worktree_path=str(wt.path), branch_name=wt.branch,
        role=task.role, state=TaskState.ACTIVE,
        plan_name=self.dag.name,
        file_claims=self._file_claims_for_task(task),
    ),
)
```
Note: no `base_commit` populated here (the column exists as `base_sha` but is set inconsistently at worktree creation). No `dispatched_at`. No `agent_model` distinct from `agent` alias. No bundle hash. No retry/fork lineage link.

## V. Terminal recording

`src/dgov/runner.py:729-746` (`_handle_worker_exit`). Terminal state lands on three places: (1) `TaskContext` (mutable, in-memory), (2) a `TaskDone` or `TaskFailed` event row emitted at `runner.py:813-838`, (3) the `WorkerTask` row's `state` column updated to a terminal value via `update_runtime_artifact_state`. No single `terminated_at` field; implicit in the event's `ts` column.

Timeout site: `runner.py:1544-1555` (TimeoutError → `TaskFailed` event with `error="Wall-clock timeout after Ns"` + synthesized `WorkerExit`).

## VI. Identity scheme — no execution-record id today

The artifacts that approximate identity:
- **`task_slug`**: stable per-unit identifier (e.g., `add-foo`); same across retries/forks of the same unit. Not derived; supplied by Plan.
- **`pane_slug`**: random per-dispatch tag, generated as uuid4 prefix at `runner.py:1649-1650`:
  ```python
  def _dispatch_pane_slug(self, task_slug: str) -> str:
      return f"headless-{task_slug}-{uuid.uuid4().hex[:8]}"
  ```
- **`WorkerTask.task_id: str | None`** (`persistence/schema.py:93`): nullable, docstring "*worker instance ID; None for headless*" — and dgov is all headless, so this is essentially always `None`.

The only `sha256` use in dgov runtime is `compute_sop_set_hash` at `sop_bundler.py:192-209`. Nothing content-derives a dispatch identity.

Per Cascade's Brief 4 precedent (lineage `08-cascade.md`) and Confluence's note (open thread #3, lineage `10-confluence.md:25`), a custom `_clone` on a content-derived `id` (init=False) is the expected migration shape.

## VII. `effective_sop_set_hash` and `drift_against_plan`

**Plan-side `sop_set_hash` exists**; per-dispatch `effective_sop_set_hash` does not.

- `PlanSpec.sop_set_hash: str | None` at `plan.py:115`.
- `DagDefinition.sop_set_hash: str = ""` at `dag_parser.py:68`.
- `BundleResult.sop_set_hash: str` at `sop_bundler.py:68`.
- `compute_sop_set_hash` at `sop_bundler.py:192-209` — hashes `(filename, name, title, summary, applies_to, priority)`. Metadata-only — the gap Pool flagged in `04-pool.md` and `dispatch-run-shape.md` v1 §68.

**Drift mechanism**: `policy_drift.py:16-21` only detects asset-mirror drift (source tree vs `.dgov/`) and guidance-file drift (`AGENTS.md`/`CLAUDE.md`/`GEMINI.md`). It does **not** compare worker-loaded bundle hash against `Plan.sop_set_hash`. There is no path in `runner._dispatch` that recomputes the bundle hash at dispatch time.

**Verdict**:
- `effective_sop_set_hash`: **not tracked**. Migration must add a re-hash at the dispatch boundary.
- `drift_against_plan`: **not tracked** in any typed form.
- `drift_evidence`: **not tracked**.

## VIII. Persistence schema

`src/dgov/persistence/sql.py:8-24`. Single SQLite database, schema version 8 (`persistence/schema.py:25`).

**`tasks`** table (the cached snapshot):
```sql
CREATE TABLE IF NOT EXISTS tasks (
    slug TEXT PRIMARY KEY,
    task_id TEXT, agent TEXT, project_root TEXT,
    worktree_path TEXT, branch_name TEXT,
    created_at REAL, owns_worktree INTEGER,
    base_sha TEXT, provenance TEXT NOT NULL DEFAULT '{"kind": "original"}',
    role TEXT DEFAULT 'worker', state TEXT,
    metadata TEXT, plan_name TEXT DEFAULT NULL
)
```
**Critical**: `slug` is PRIMARY KEY — one row per task slug, not one row per dispatch attempt. Retries overwrite the prior row in place. No per-attempt history table.

**`events`** at `sql.py:26-44` — append-only, the actual lifecycle journal.
**`slug_history`** at `sql.py:46-50` — only retired slugs.
**`ledger`** at `sql.py:52-62` — operational notes (bugs, rules, debt), unrelated to dispatch.

No `runs` or `dispatch_runs` table. The schema's `slug`-keyed shape will need expanding (or a new `dispatch_runs` table minted) for the SOP's per-attempt content-derived ids. **Schema version bump 8 → 9 is required**, preflight-gated per `sops/schema-versioning.md`.

## IX. Retry/fork lineage — counters only, not links

**Retry lineage**: counter only, not a parent-pointer link.
- `TaskContext.attempts: int` (`runner.py:136`); incremented on retry at `runner.py:1459`.
- `kernel.max_retries: int = 3` (`kernel.py:70`).
- `GovernorAction.RETRY` (`actions.py:90`) → `_on_governor_resumed` (`kernel.py:175-200`) flips a terminal state back to `PENDING`, **losing the prior-attempt link** entirely.
- Retry runs in the same `WorkerTask` row (slug is PK); no `retried_from` pointer.

**Fork lineage**: also a counter, not a link.
- `TaskContext.fork_depth: int = 0` (`runner.py:144`); incremented at `_start_iteration_fork` (`runner.py:768-796`).
- `DagTaskSpec.max_fork_depth: int` from Plan.
- `IterationFork` event (`event_types.py:203-211`) carries only `fork_depth`, not a `forked_from` pointer.
- Forked pane: `fork_pane = f"{pane_slug}-fork-{ctx.fork_depth}"` (`runner.py:873`) — implicit string lineage only.
- **Mutual exclusion is not enforced**: a forked task could be retried, and dgov's counters would both increment independently.

The SOP's `retried_from: prior_dispatch_run_id | None` and `forked_from: prior_dispatch_run_id | None` have no analogue. Migration must mint dispatch-run ids first before lineage links become expressible.

## X. `dispatched_by` (WatermasterId)

**Nothing.** Zero hits on `watermaster`, `WatermasterId`, `dispatched_by` across `src/dgov/`. dgov predates CANON Article XVI / SOP §25. Migration must add this field; value source is watershed-side, not dgov-internal.

## XI. Drift map — SOP field × dgov today

| SOP field | Today in dgov | Site | Status |
|---|---|---|---|
| `id` (content-derived) | absent | — | **missing** |
| `from_plan_id: str` | implicit (`dag.name`, `plan_name`) | `runner.py` passim | differently-shaped (string name, not stable id) |
| `unit_slug: str` | `task_slug` | `types.py`, `actions.py` | name-different |
| `worktree_id: str` | `Worktree.path` (Path) + `branch_name` | `types.py:58`, `WorkerTask` | shape-different (no abstracted worktree id) |
| `branch: str` | `Worktree.branch`, `WorkerTask.branch_name` | `types.py:62`, `schema.py:91` | present, name-aligned |
| `base_commit: str` | `WorkerTask.base_sha`, `Worktree.commit` | `schema.py:96`, `types.py:63` | present, name-different |
| `agent_model: str` | `WorkerTask.agent` (also `DagTaskSpec.agent`) | `schema.py:88` | present, name-different |
| `effective_sop_set_hash` | absent (only Plan's `sop_set_hash`) | — | **missing** |
| `drift_against_plan: bool` | absent | — | **missing** |
| `drift_evidence: tuple[str, ...]` | absent | — | **missing** |
| `retried_from: id \| None` | absent; counter only | `runner.py:136` | **missing as link**; counter present |
| `forked_from: id \| None` | absent; counter only | `runner.py:144` | **missing as link**; counter present |
| `retry_index: int` | `TaskContext.attempts` | `runner.py:136` | present, name-different |
| `fork_depth: int` | `TaskContext.fork_depth` | `runner.py:144` | present, name-aligned |
| `dispatched_by: WatermasterId` | absent | — | **missing** |
| `dispatched_at: datetime` (UTC tz-aware) | `WorkerTask.created_at: float` (epoch); event `ts` ISO string | `schema.py:94`, `events.py:27` | present, shape-different (float not tz-aware dt) |
| `state` (6-value) | `TaskState` (13-value) | `types.py:21` | superset; needs narrowing |
| `exit_code: int \| None` | `WorkerExit.exit_code: int` | `types.py:49` | present |
| `last_error: str` | `WorkerExit.last_error: str`, `TaskContext.error` | `types.py:50`, `runner.py:137` | present |
| `output_dir: str` | `WorkerExit.output_dir: str` | `types.py:49` | present |
| `prompt_tokens: int` | `WorkerExit.prompt_tokens`, `TaskContext.prompt_tokens` | `types.py:51`, `runner.py:146` | present |
| `completion_tokens: int` | `WorkerExit.completion_tokens`, `TaskContext.completion_tokens` | `types.py:52`, `runner.py:147` | present |
| `iteration_count: int` | `TaskContext.call_count` | `runner.py:143` | present, name-different; mutable |
| `terminated_at: datetime` | absent as field; implicit in terminal event's `ts` | `event_types.py` | **missing as a record field** |

**Summary**:
- **Missing entirely (8 of 21+ fields)**: `id`, `effective_sop_set_hash`, `drift_against_plan`, `drift_evidence`, `retried_from`, `forked_from`, `dispatched_by`, `terminated_at`.
- **Present-but-differently-shaped (9 fields)**: `from_plan_id`, `unit_slug`, `worktree_id`, `base_commit`, `agent_model`, `dispatched_at`, `state`, `retry_index`, `iteration_count`.
- **Already aligned (7 fields)**: `branch`, `exit_code`, `last_error`, `output_dir`, `prompt_tokens`, `completion_tokens`, `fork_depth`.

## XII. Brief 9 readiness assessment

**Size class**: a **500-line-Brief like Cascade's Brief 4**, possibly larger — closer to a staged-migration Brief shape than a one-shot.

**Reasons it's heavier than Cascade's Brief 4**:

1. **No `RunRecord` analogue exists**, so the Brief mints the type rather than refactoring an existing one. Cascade's Brief 4 had a `RunRecord` to `_clone` into a new shape; Brief 9 starts from a 5-site fragmentation.
2. **Schema migration is required**. Schema v8 → v9, preflight-gated under `sops/schema-versioning.md`.
3. **Lifecycle narrowing has user-visible consequences**. The 13 → 6 state narrowing requires lifting `reviewing/reviewed_pass/reviewed_fail/merging/merged` into typed Deposit / Validation / Merge records — the unfinished tributary-side seam.
4. **Effective-bundle-hash recomputation is new code** at the dispatch boundary; the worker subprocess loading path (`workers/atomic.py`, `workers/headless.py`) needs to bubble a hash up.
5. **Retry/fork lineage links are net-new** (today only counters exist).
6. **`dispatched_by: WatermasterId` is foreign-keyed** to a CANON-XVI concept dgov doesn't yet know about.

**Preflight-gated nested changes**:
- Schema bump (8 → 9) per `sops/schema-versioning.md`.
- New table `dispatch_runs` (or compatible schema mutation).
- Potential bundler-level escalate (the SOP names this at §68); the bundler hashes metadata only and worker-body changes wouldn't register as drift — dgov-internal escalate, not a Brief 9 concern unless the Brief touches `sop_bundler.compute_sop_set_hash`.
- Likely a `DispatchRun` type lift into a shared/distributary home if the watershed split has begun; if not, type lands in `dgov.types` for now.

**Recommended staged-migration shape** (Cascade pattern; see `08-cascade.md` Conventions and Confluence's open thread #3 in `10-confluence.md`):

- **Stage 1 (Brief 9a)**: Mint typed `DispatchRun` (with `_clone` per Cascade's pattern); land alongside existing `WorkerTask`. Write through both during transition. Schema bump for the new table. No lifecycle narrowing yet. Roughly Cascade's Brief 4 size.
- **Stage 2 (Brief 9b)**: Add `effective_sop_set_hash` recomputation at dispatch boundary; populate `drift_against_plan` / `drift_evidence`. Wire `dispatched_by` through from the seated Watermaster.
- **Stage 3 (Brief 9c)**: Per-attempt rows (retry/fork lineage links). Counter → link conversion.
- **Stage 4 (Brief 10?)**: Lifecycle narrowing — peel `reviewing/reviewed_pass/reviewed_fail/merging/merged` off `WorkerTask` onto downstream typed records. This is the Deposit / Validation / Merge work and may be its own arc.
- **Stage 5 (Brief 11?)**: Remove the `WorkerTask` cache once DispatchRun is authoritative.

## XIII. Open Source-side design questions

These are the questions the next Watermaster should surface to the Source before drafting Brief 9 (per the chain's pattern: design questions first, Brief after):

1. **Pre-existing dispatch-attempt rows.** Does the lab care about preserving inspection of pre-existing dispatch attempts in the `tasks` table (slug-keyed, no per-attempt history)? Same shape as the Brief 6 question Confluence flagged. If preserve: a one-shot migration tool; if not: legacy rows are historical-only data, the new `dispatch_runs` table starts empty for going-forward work.

2. **One Brief or staged Briefs?** Single Brief 9 (mint + populate + lifecycle-narrow) vs. staged Briefs 9a/9b/9c (mint first, populate later, lifecycle-narrow later). Cascade's precedent (Brief 4 + Brief 5 as a pair) leans staged; the size of dgov's migration leans more staged than Cascade's because the lifecycle-narrow step touches the kernel state machine and downstream typed records that don't exist yet.

3. **Where does `DispatchRun` live?** `dgov.types` (in-tree, simpler now) or `shared/DispatchRun` (watershed-side, anticipates the eventual distributary lift). The split mentioned in SKETCHES.md is "half-done"; the seam doesn't have a clear home yet. Conservative call: land in `dgov.types` for now; future Brief lifts to `shared/` when distributary materializes.

4. **Bundler-hash-composition gap acknowledgment.** `dispatch-run-shape.md` v1 §68 explicitly defers this as bundler-level escalate territory. Brief 9 should name the gap in its instructions but not touch `sop_bundler.compute_sop_set_hash`. Worth surfacing to the Source so they know the Brief inherits the gap rather than closing it.

## XIV. Files cited (absolute paths, for next-Watermaster reference)

- `/Users/jakegearon/projects/dgov/src/dgov/types.py`
- `/Users/jakegearon/projects/dgov/src/dgov/actions.py`
- `/Users/jakegearon/projects/dgov/src/dgov/runner.py`
- `/Users/jakegearon/projects/dgov/src/dgov/kernel.py`
- `/Users/jakegearon/projects/dgov/src/dgov/settlement_flow.py`
- `/Users/jakegearon/projects/dgov/src/dgov/event_types.py`
- `/Users/jakegearon/projects/dgov/src/dgov/live_state.py`
- `/Users/jakegearon/projects/dgov/src/dgov/plan.py`
- `/Users/jakegearon/projects/dgov/src/dgov/sop_bundler.py`
- `/Users/jakegearon/projects/dgov/src/dgov/policy_drift.py`
- `/Users/jakegearon/projects/dgov/src/dgov/persistence/schema.py`
- `/Users/jakegearon/projects/dgov/src/dgov/persistence/sql.py`
- `/Users/jakegearon/projects/dgov/src/dgov/persistence/runtime_artifacts.py`
- `/Users/jakegearon/projects/dgov/src/dgov/persistence/events.py`

---

**Reconning Watermaster**: Bench, 2026-05-13.
**Next-Watermaster note**: this recon assumes the dgov main branch state as of 2026-05-13. If a substantial mutation lands on `runner.py` / `kernel.py` / `settlement.py` / `types.py` / `actions.py` between now and your session, re-confirm the structural shape before drafting. Otherwise, the map above is your starting foundation.

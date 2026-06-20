# Brief 9 — DispatchRun-side `RunRecord` migration in dgov

**Watermaster**: Anabranch
**Date**: 2026-05-14
**Engineer model**: codex-gpt-5
**Write scope**: `/Users/jakegearon/projects/dgov/src/dgov/**`, `/Users/jakegearon/projects/dgov/tests/**`
**State**: drafted
**Recon foundation**: `sketches/briefs/11-bench/recon-9-dispatchrun.md` (Bench, 2026-05-13). Read it for the full drift map and field-level citations before starting. Branch `codex/boundary-ownership-cleanup` is settled (PR #24, merged 2026-05-11). Only `live_state.py` has changed since the recon (stale-status display, out of scope).

---

## Goal

Mint a typed `DispatchRun` per `sops/dispatch-run-shape.md` v1, materialize it across all dispatch sites in dgov, dual-write through the existing `tasks` table during the transition, populate effective bundle hash + drift fields + watermaster identity at the dispatch boundary, and convert today's retry/fork counter-only lineage into typed `retried_from` / `forked_from` links. Lifecycle narrowing (the `reviewing/reviewed_pass/reviewed_fail/merging/merged` peel onto Deposit/Validation/Merge) is Brief 10 territory and out of scope.

## Source utterance (verbatim)

> do 9

The Source previously selected the DispatchRun-side migration from the three available arcs and approved the four-question design slate:
- **Q1 (pre-existing rows)**: historical-only, no migration tool. New `dispatch_runs` table starts empty; existing `tasks` rows stay queryable as legacy snapshot.
- **Q2 (staging)**: one Brief at max scope (9a + 9b + 9c combined; not 10).
- **Q3 (location)**: in-tree at `dgov.types` / new `src/dgov/dispatch_run.py` module, not `shared/`.
- **Q4 (bundler-hash gap)**: inherit and name as escalate debt; do not touch `sop_bundler.compute_sop_set_hash`.

The Source's framing was "max scope on the brief we will testt the range of codex. you may be surprised."

## Background (read first)

Read these in order before writing code:

1. `sops/dispatch-run-shape.md` v1 — the canonical typed shape. All 21+ required fields, two-phase frozen-pin, retry-vs-fork mutual exclusion, drift recording, lifecycle narrowing scope. The verify clause at §53–§64 is the test surface.
2. `sops/schema-versioning.md` v1 — the schema bump v8 → v9 falls under this. The change is `additive` (new table) — preflighted at this Brief's meta-preflight time.
3. `sops/operator-run-shape.md` v1 — the operator-side parallel, useful for pattern transfer. Same two-phase frozen-pin, same custom-`_clone` discipline.
4. `sops/data-contracts.md` v2 — Artifact-style identity and content-derived id discipline (`derive_*` strategy-tag prefixing).
5. `sops/engineer-brief.md` v2 — the discipline you operate under as Engineer: write only inside `write_scope`, return a typed `EngineerReturn` summary, flag out-of-scope discoveries, do not modify `sketches/lineage/*`.
6. The recon at `sketches/briefs/11-bench/recon-9-dispatchrun.md` — drift map, file:line citations, retrieved bundle status.
7. `sketches/briefs/08-cascade/brief-4-runrecord-to-operatorrun.md` (Cascade's precedent on the operator side) — same shape of work in a different repo. The custom `_clone` pattern and `_identity_digest`-style content hashing transfer directly.

The codebase's source-of-truth files for this Brief:
- `/Users/jakegearon/projects/dgov/src/dgov/types.py` (TaskState, WorkerExit, Worktree)
- `/Users/jakegearon/projects/dgov/src/dgov/runner.py` (1591–1693 `_dispatch` + `_record_dispatch_artifact`; 729–838 terminal recording; 768–796 fork; 1458–1467 retry; 1544–1555 timeout; 131–147 `TaskContext`)
- `/Users/jakegearon/projects/dgov/src/dgov/kernel.py` (296 lines; pure state machine; `max_retries: int = 3` at line 70)
- `/Users/jakegearon/projects/dgov/src/dgov/plan.py` (PlanSpec at 103–116; `sop_set_hash: str | None` at 115)
- `/Users/jakegearon/projects/dgov/src/dgov/sop_bundler.py` (`compute_sop_set_hash` at 192–209 — metadata only, the gap)
- `/Users/jakegearon/projects/dgov/src/dgov/persistence/sql.py` (table DDLs, 62 lines)
- `/Users/jakegearon/projects/dgov/src/dgov/persistence/schema.py` (`_SCHEMA_VERSION = 8` at line 25; WorkerTask at 79–109; VALID_TRANSITIONS at 31–63)
- `/Users/jakegearon/projects/dgov/src/dgov/persistence/connection.py` (`_get_db` at 31–69; `_migrate_schema` at 72–94; `_retry_on_lock` at 97–112)
- `/Users/jakegearon/projects/dgov/src/dgov/persistence/runtime_artifacts.py` (parallel template — `record_runtime_artifact` at 32–40, `get_runtime_artifact` at 67–72, `update_runtime_artifact_state` at 145–173, `list_runtime_artifacts` at 93–98; all using `_retry_on_lock`)

---

## Items

### Item A — Mint typed `DispatchRun` and helpers (new module)

Create `src/dgov/dispatch_run.py`. Include:

**Type alias and state literal**:
```python
from typing import Literal, TypeAlias

WatermasterId: TypeAlias = str
DispatchRunState = Literal["pending", "active", "done", "failed", "timed_out", "abandoned"]
```

**`DispatchRun` dataclass** — `@dataclass(frozen=True, slots=True, init=False)` with custom `__init__` (kwargs only). All 21 SOP-required fields in this order:

```python
id: str                          # content-derived; computed in __init__
from_plan_id: str
unit_slug: str
worktree_id: str
branch: str
base_commit: str
agent_model: str
effective_sop_set_hash: str
drift_against_plan: bool
drift_evidence: tuple[str, ...]
retried_from: str | None
forked_from: str | None
retry_index: int
fork_depth: int
dispatched_by: WatermasterId
dispatched_at: datetime          # UTC tz-aware
state: DispatchRunState
exit_code: int | None
last_error: str
output_dir: str
prompt_tokens: int
completion_tokens: int
iteration_count: int
terminated_at: datetime | None   # UTC tz-aware
```

**`__init__` signature** (kwargs-only, all fields with sensible defaults where allowed):
```python
def __init__(
    self,
    *,
    from_plan_id: str,
    unit_slug: str,
    worktree_id: str,
    branch: str,
    base_commit: str,
    agent_model: str,
    effective_sop_set_hash: str,
    drift_against_plan: bool,
    drift_evidence: tuple[str, ...] = (),
    retried_from: str | None = None,
    forked_from: str | None = None,
    retry_index: int = 0,
    fork_depth: int = 0,
    dispatched_by: WatermasterId,
    dispatched_at: datetime,
    state: DispatchRunState = "pending",
    exit_code: int | None = None,
    last_error: str = "",
    output_dir: str = "",
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    iteration_count: int = 0,
    terminated_at: datetime | None = None,
    _id: str | None = None,         # internal: used by _clone to preserve id
) -> None:
    ...
```

**Inside `__init__`**:
- Validate mutual exclusion: `not (retried_from is not None and forked_from is not None)` — raise `ValueError` if both non-None.
- Validate counters match lineage: if `retried_from is None` then `retry_index == 0`; if `forked_from is None` then `fork_depth == 0`. (Either are zero, or the corresponding link is non-None.) Use `ValueError`.
- Validate state value is one of the six legal strings (catch-all guard for runtime type slop).
- Validate `dispatched_at` is tz-aware UTC; `terminated_at` if non-None is tz-aware UTC.
- Validate `drift_against_plan == (effective_sop_set_hash != ...)` is NOT enforced here (the caller computes it).
- Compute `id` via `derive_dispatch_run_id(...)` over the SOP §26 identity inputs:
  `(from_plan_id, unit_slug, worktree_id, branch, base_commit, agent_model, effective_sop_set_hash, retried_from, forked_from, retry_index, fork_depth, dispatched_at)` — but if `_id is not None`, use that (the `_clone` path preserves the original id).
- Set all fields via `object.__setattr__` (frozen).

**Helpers (same module)**:

```python
def derive_dispatch_run_id(
    *,
    from_plan_id: str,
    unit_slug: str,
    worktree_id: str,
    branch: str,
    base_commit: str,
    agent_model: str,
    effective_sop_set_hash: str,
    retried_from: str | None,
    forked_from: str | None,
    retry_index: int,
    fork_depth: int,
    dispatched_at: datetime,
) -> str:
    """Content-derive a stable DispatchRun id with strategy-tag prefix 'disprun:'."""
    # use hashlib.sha256, key-sorted/positional canonical form, strategy-tag prefix.
    # parallel to derive_operator_run_id in quarry-core/operator_run.py.
```

```python
def derive_drift_evidence(
    *,
    plan_hash: str | None,
    effective_hash: str,
) -> tuple[str, ...]:
    """Return drift evidence descriptors when plan_hash != effective_hash.

    Inherited debt: the bundler hashes metadata only (sop_bundler.compute_sop_set_hash
    composes name/filename/title/summary/applies_to/priority). Without a plan-time
    snapshot of the bundle composition, we cannot emit set:added/set:removed
    descriptors per SOP §29. Brief 9 records a single "metadata:modified=bundle:sop_set_hash"
    descriptor when hashes differ — this matches the SOP's typed descriptor shape
    "metadata:modified=<sop>:<field>" while honestly recording that the gap exists.
    """
    if plan_hash is None or plan_hash == effective_hash:
        return ()
    return ("metadata:modified=bundle:sop_set_hash",)
```

**`_clone(**changes)`** private method on `DispatchRun`:
```python
def _clone(self, **changes) -> "DispatchRun":
    """Produce a new frozen instance with changes applied, preserving id.

    Used by state-transition methods. The id stays stable because all SOP §26
    identity-input fields are frozen-pinned at pending → active and the
    state transitions only touch SOP §35 output fields.
    """
    # Build kwargs for __init__ from current field values overridden by changes,
    # then pass _id=self.id so __init__ preserves the existing id.
```

**State-transition methods** (each returns a new `DispatchRun` instance):

```python
def start_active(self) -> "DispatchRun":
    """pending → active. The SOP §34 boundary: input fields freeze here."""
    if self.state != "pending":
        raise ValueError(f"Cannot transition from {self.state} to active")
    return self._clone(state="active")

def complete_done(
    self,
    *,
    exit_code: int,
    output_dir: str,
    prompt_tokens: int,
    completion_tokens: int,
    iteration_count: int,
    terminated_at: datetime,
) -> "DispatchRun":
    """active → done. Terminal; SOP §35 output fields freeze here."""
    if self.state != "active":
        raise ValueError(f"Cannot transition from {self.state} to done")
    return self._clone(
        state="done",
        exit_code=exit_code,
        output_dir=output_dir,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        iteration_count=iteration_count,
        terminated_at=terminated_at,
    )

def complete_failed(
    self,
    *,
    exit_code: int,
    last_error: str,
    output_dir: str,
    prompt_tokens: int,
    completion_tokens: int,
    iteration_count: int,
    terminated_at: datetime,
) -> "DispatchRun":
    """active → failed. Same frozen-pin discipline as done."""
    ...

def complete_timed_out(
    self,
    *,
    last_error: str,
    output_dir: str,
    prompt_tokens: int,
    completion_tokens: int,
    iteration_count: int,
    terminated_at: datetime,
) -> "DispatchRun":
    """active → timed_out. Used by wall-clock timeout and iteration-budget exhaustion."""
    ...

def complete_abandoned(
    self,
    *,
    last_error: str,
    output_dir: str,
    prompt_tokens: int,
    completion_tokens: int,
    iteration_count: int,
    terminated_at: datetime,
) -> "DispatchRun":
    """active → abandoned. Shutdown-interrupted dispatches."""
    ...
```

`exit_code` is `int | None`: required for `done`/`failed`; `None` for `timed_out`/`abandoned` (per the SOP §62 "an exit_code is the run's process exit code; absent when the run was terminated outside the process"). The transition methods enforce the right `exit_code` shape per SOP.

**Module `__all__`** at the bottom — list every public symbol.

### Item B — `src/dgov/types.py` re-exports (minimal)

Add at the bottom of `types.py`:
```python
from dgov.dispatch_run import DispatchRun, DispatchRunState, WatermasterId  # re-export

__all__ = [
    ...existing...,
    "DispatchRun",
    "DispatchRunState",
    "WatermasterId",
]
```

If a circular-import issue arises (because `dispatch_run.py` ends up importing from `types.py`), reverse: keep `types.py` minimal and document the import path as `from dgov.dispatch_run import DispatchRun`. Use your judgment — `types.py` is described in its module docstring as "minimal dependencies version", so circular import is the failure to watch for.

### Item C — SQL DDL for `dispatch_runs` table

In `src/dgov/persistence/sql.py`, add:

```python
_CREATE_DISPATCH_RUNS_TABLE_SQL = """\
CREATE TABLE IF NOT EXISTS dispatch_runs (
    id TEXT PRIMARY KEY,
    from_plan_id TEXT NOT NULL,
    unit_slug TEXT NOT NULL,
    worktree_id TEXT NOT NULL,
    branch TEXT NOT NULL,
    base_commit TEXT NOT NULL,
    agent_model TEXT NOT NULL,
    effective_sop_set_hash TEXT NOT NULL,
    drift_against_plan INTEGER NOT NULL,
    drift_evidence TEXT NOT NULL DEFAULT '[]',
    retried_from TEXT,
    forked_from TEXT,
    retry_index INTEGER NOT NULL DEFAULT 0,
    fork_depth INTEGER NOT NULL DEFAULT 0,
    dispatched_by TEXT NOT NULL,
    dispatched_at TEXT NOT NULL,
    state TEXT NOT NULL,
    exit_code INTEGER,
    last_error TEXT NOT NULL DEFAULT '',
    output_dir TEXT NOT NULL DEFAULT '',
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    iteration_count INTEGER NOT NULL DEFAULT 0,
    terminated_at TEXT
)"""
```

`drift_evidence` is JSON-serialized at write time and JSON-deserialized at read time (parallel to how `file_claims` etc. travel as JSON in dgov today). `drift_against_plan` is stored as 0/1.

### Item D — Schema version bump in `src/dgov/persistence/schema.py`

Bump `_SCHEMA_VERSION = 9` (comment: `# Added dispatch_runs table`).

Import `_CREATE_DISPATCH_RUNS_TABLE_SQL` from `dgov.persistence.sql`.

Add to `__all__`.

Optional: define a `_DISPATCH_RUN_COLUMNS = frozenset({...})` parallel to `_TASK_COLUMNS` for the persistence layer to validate against. Add it to `__all__` if you use it in the persistence module.

### Item E — Connection wiring in `src/dgov/persistence/connection.py`

In `_get_db` (line 31–69), add `conn.execute(_CREATE_DISPATCH_RUNS_TABLE_SQL)` next to the other `CREATE TABLE` calls (lines 55–58). Import the new constant.

`_migrate_schema` (line 72–94) doesn't need a change for this Brief — the table is new, no existing rows to migrate. (dgov has no `PRAGMA user_version` tracking; `_SCHEMA_VERSION` is a docstring constant.)

### Item F — Persistence operations: `src/dgov/persistence/dispatch_runs.py` (new module)

Create the module. Mirror `runtime_artifacts.py` in structure:

```python
def save_dispatch_run(session_root: str, dispatch_run: DispatchRun) -> None:
    """INSERT OR REPLACE the dispatch_run row. Idempotent upsert."""
    # serialize drift_evidence as JSON
    # serialize drift_against_plan as int
    # serialize datetimes as ISO 8601 with tz suffix
    # use _retry_on_lock + _get_db pattern
```

```python
def get_dispatch_run(session_root: str, dispatch_run_id: str) -> dict | None:
    """Return the row as a dict (or None). Deserialize drift_evidence from JSON."""
    # row_factory = sqlite3.Row
```

```python
def list_dispatch_runs(
    session_root: str,
    *,
    plan_id: str | None = None,
    unit_slug: str | None = None,
    state: str | None = None,
) -> list[dict]:
    """List rows filtered by optional keys."""
```

```python
def get_dispatch_runs_for_unit(session_root: str, unit_slug: str) -> list[dict]:
    """Return all dispatch_runs for a slug in dispatch order (ascending dispatched_at)."""
    # convenience for retry/fork chain traversal
```

Internal helpers:
- `_serialize_dispatch_run(dispatch_run: DispatchRun) -> dict` (DispatchRun → row dict)
- `_row_to_dispatch_run_dict(row: sqlite3.Row) -> dict` (row → dict, with drift_evidence deserialized)
- `_insert_dispatch_run_dict(conn, row_dict)` (INSERT OR REPLACE SQL — list every column explicitly per dgov convention; no auto-magic from `_TASK_COLUMNS`-style sets unless you define a `_DISPATCH_RUN_COLUMNS` mirror in `schema.py`)

`update_dispatch_run_state` is NOT needed — DispatchRun is frozen, state transitions produce new instances, persistence layer just calls `save_dispatch_run` with the new instance. `INSERT OR REPLACE` handles the upsert.

Module `__all__` at the bottom.

### Item G — Dispatch-time mint + dual-write in `src/dgov/runner.py`

Three sub-changes:

**G1 — `EventDagRunner.__init__`**: Add a kwarg `dispatched_by: WatermasterId = "watermaster:unknown"`. Store on `self._dispatched_by`. (Match Cascade's Brief 4 precedent — the default is `"watermaster:unknown"`; CLI / future wiring can override.)

**G2 — `TaskContext` (line 131–147)**: Add three fields:
```python
current_dispatch_run_id: str | None = None
retried_from_dispatch_run_id: str | None = None
forked_from_dispatch_run_id: str | None = None
```

**G3 — `_dispatch` (line 1591–1628)**: Before launching the worker:

```python
# After: ctx.start_time = time.time()  (line 1608)
# Before: self._record_dispatch_artifact(...)  (line 1610)

# Compute effective bundle hash
from dgov.sop_bundler import compute_sop_set_hash, load_sops
sops_dir = Path(self.session_root) / ".dgov" / "sops"
try:
    effective_sops = load_sops(sops_dir)
    effective_sop_set_hash = compute_sop_set_hash(effective_sops)
except (FileNotFoundError, ValueError) as exc:
    logger.warning("Effective SOP bundle could not be loaded at dispatch: %s", exc)
    effective_sop_set_hash = ""

plan_hash = self.dag.sop_set_hash if self.dag.sop_set_hash else None
drift_against_plan = (
    plan_hash is not None and plan_hash != effective_sop_set_hash
)
drift_evidence = derive_drift_evidence(
    plan_hash=plan_hash,
    effective_hash=effective_sop_set_hash,
)

# Resolve retry/fork lineage from TaskContext (set by retry/fork sites)
retried_from = ctx.retried_from_dispatch_run_id
forked_from = ctx.forked_from_dispatch_run_id
retry_index = ctx.attempts if retried_from is not None else 0
fork_depth = ctx.fork_depth if forked_from is not None else 0

# Mint DispatchRun in pending then transition to active
dispatch_run = DispatchRun(
    from_plan_id=self.dag.name,                # see G4 note below
    unit_slug=action.task_slug,
    worktree_id=str(wt.path),                  # use the worktree path as the id surrogate for now (Brief 9 doesn't lift to a separate id)
    branch=wt.branch,
    base_commit=wt.commit,
    agent_model=agent,
    effective_sop_set_hash=effective_sop_set_hash,
    drift_against_plan=drift_against_plan,
    drift_evidence=drift_evidence,
    retried_from=retried_from,
    forked_from=forked_from,
    retry_index=retry_index,
    fork_depth=fork_depth,
    dispatched_by=self._dispatched_by,
    dispatched_at=datetime.now(timezone.utc),
).start_active()

save_dispatch_run(self.session_root, dispatch_run)
ctx.current_dispatch_run_id = dispatch_run.id

# Clear retry/fork lineage from TaskContext now that they've been recorded on the DispatchRun
ctx.retried_from_dispatch_run_id = None
ctx.forked_from_dispatch_run_id = None
```

Then continue with the existing `self._record_dispatch_artifact(...)` (line 1610) and kernel/event/launch flow (lines 1611–1623) — **the existing WorkerTask write stays intact** as the dual-write half.

**G4 — `from_plan_id` semantic note**: `dispatch-run-shape.md` §25 specifies `from_plan_id: str`. In dgov today, `self.dag.name` is the plan's surface name (e.g., `"refactor-foo"`). PlanSpec doesn't have a content-derived `id` (Plan-shape SOP v2 says it should, but the dgov-side Plan migration is a separate arc). Use `self.dag.name` for `from_plan_id` for now — that's the de-facto plan identifier in dgov. The SOP's verify §56 ("`from_plan_id` resolves to a Plan in distributary's plan-registry") is honored at the semantic level even though the registry isn't typed yet. Flag this in your EngineerReturn so the next Brief that lifts Plan-id can update the foreign-key.

### Item H — Terminal recording in `src/dgov/runner.py`

At `_handle_worker_exit` (line 729–746) and `_record_worker_exit` (line 748–753), wire the terminal transition.

In `_handle_worker_exit` after `_record_worker_exit(ctx, exit_event)` (line 733), and BEFORE the fork branch (`if self._should_fork_after_exit(...)`) — so terminal recording happens unconditionally for the prior DispatchRun:

```python
# Terminal recording on the current DispatchRun (if any)
if ctx.current_dispatch_run_id is not None:
    current_dispatch_run = get_dispatch_run(self.session_root, ctx.current_dispatch_run_id)
    if current_dispatch_run is not None:
        # rehydrate to DispatchRun instance via a from-dict helper (you'll need to write one in dispatch_run.py)
        prior = _dispatch_run_from_row_dict(current_dispatch_run)
        terminated_at = datetime.now(timezone.utc)
        if self._should_fork_after_exit(exit_event, ctx, task):
            # iteration budget exhausted - prior goes to timed_out, new fork mints below
            terminal = prior.complete_timed_out(
                last_error=exit_event.last_error or "Exceeded max iterations",
                output_dir=exit_event.output_dir,
                prompt_tokens=ctx.prompt_tokens,
                completion_tokens=ctx.completion_tokens,
                iteration_count=ctx.call_count,
                terminated_at=terminated_at,
            )
        elif exit_event.exit_code == 0:
            terminal = prior.complete_done(
                exit_code=exit_event.exit_code,
                output_dir=exit_event.output_dir,
                prompt_tokens=ctx.prompt_tokens,
                completion_tokens=ctx.completion_tokens,
                iteration_count=ctx.call_count,
                terminated_at=terminated_at,
            )
        else:
            terminal = prior.complete_failed(
                exit_code=exit_event.exit_code,
                last_error=exit_event.last_error or "",
                output_dir=exit_event.output_dir,
                prompt_tokens=ctx.prompt_tokens,
                completion_tokens=ctx.completion_tokens,
                iteration_count=ctx.call_count,
                terminated_at=terminated_at,
            )
        save_dispatch_run(self.session_root, terminal)
```

Note: structurally, the terminal write happens BEFORE the kernel/fork branching decisions, so the prior dispatch is recorded as terminal regardless of subsequent retry/fork. Then if a retry or fork is authorized, the next `_dispatch` mints a new DispatchRun with `retried_from = prior.id` / `forked_from = prior.id`.

The rehydration helper `_dispatch_run_from_row_dict(row_dict) -> DispatchRun` lives in `dispatch_run.py` — it reverses `_serialize_dispatch_run`. Add it to Item A. (Or place it in the persistence module; your call as long as the abstraction layering doesn't violate the connection-vs-pure-type boundary.)

### Item I — Wall-clock timeout recording in `src/dgov/runner.py`

At `_run_with_timeout` (line 1544–1555) — the TimeoutError block — the dispatch is terminated by wall-clock timeout. The `on_exit` callback at line 1555 (`on_exit(task_slug, pane_slug, 1, f"Timed out after {timeout_s}s", 0, 0)`) constructs a `WorkerExit` and routes through `_handle_worker_exit`, which Item H's path handles. So Item I doesn't need its own DispatchRun write — Item H's `complete_failed` branch covers the wall-clock timeout case (the prior goes to `failed` because `exit_event.exit_code != 0`, not to `timed_out`).

Per SOP §32, wall-clock timeout should be `timed_out`, not `failed`. **Tighten Item H** to detect the timeout signature (`last_error.startswith("Timed out after")` or `"Wall-clock timeout"` substring) and route through `complete_timed_out` instead of `complete_failed`. The detection signal: `exit_event.last_error` containing the timeout marker.

Add this branch to Item H's flow:
```python
elif "Timed out after" in (exit_event.last_error or "") or "Wall-clock timeout" in (exit_event.last_error or ""):
    terminal = prior.complete_timed_out(
        last_error=exit_event.last_error,
        output_dir=exit_event.output_dir,
        prompt_tokens=ctx.prompt_tokens,
        completion_tokens=ctx.completion_tokens,
        iteration_count=ctx.call_count,
        terminated_at=terminated_at,
    )
```

(Insert before the generic `complete_failed` branch.)

### Item J — Retry lineage in `src/dgov/runner.py`

At `_interrupt_governor_action` (line 1441–1475), specifically the retry branch (lines 1458–1467):

Before the `return GovernorAction.RETRY` at line 1467, set:
```python
ctx = self._ctx(action.task_slug)
ctx.retried_from_dispatch_run_id = ctx.current_dispatch_run_id
```

When the next `_dispatch` runs (via `_on_governor_resumed` flipping state back to PENDING + `_schedule` re-dispatching), Item G3 picks up the lineage from `TaskContext` and mints the new DispatchRun with `retried_from = prior_id`, `retry_index = prior + 1`.

Watch out: `ctx.attempts` is incremented at line 1459 (`ctx.attempts = attempts + 1`). At dispatch time, `retry_index` should equal the new `ctx.attempts` value (it's the attempt count for the NEW dispatch). If `attempts == 1` at the new dispatch, this is the first retry → `retry_index = 1`. Item G3's logic uses `ctx.attempts if retried_from is not None else 0` — confirm this aligns with SOP §33 ("`retry_index = retried_from.retry_index + 1`"). It does: if prior had `retry_index = 0`, the new one has `retry_index = 1`, which equals `ctx.attempts = 1`.

### Item K — Fork lineage in `src/dgov/runner.py`

At `_start_iteration_fork` (line 768–796), before calling `_fork_worker`:
```python
ctx.forked_from_dispatch_run_id = ctx.current_dispatch_run_id
# ctx.fork_depth is already incremented at line 774
```

Then in `_fork_worker` (or wherever the fork path enters dispatch — trace via `_fork_worker` callsite at line 794–796), the same dispatch path needs to mint a fresh DispatchRun. **However**, `_fork_worker` does NOT go through `_dispatch` — it's a separate launcher that continues in the same worktree.

**Investigate `_fork_worker`'s actual path** (search `runner.py` for `_fork_worker` definition). If it shares dispatch-time bookkeeping with `_dispatch`, plumb the new DispatchRun mint through it. If it diverges, replicate Item G3's mint logic inside `_fork_worker` (or extract a shared `_mint_dispatch_run_and_record(...)` helper that both `_dispatch` and `_fork_worker` call).

The key invariant: every worker subprocess launch — initial, retry, or fork — produces exactly one new `DispatchRun` record. Retries get `retried_from`; forks get `forked_from`; originals get neither.

### Item L — Tests

Create two new test files:

**`tests/test_dispatch_run.py`** — unit tests for the type. Cover:
1. `derive_dispatch_run_id` stability: same inputs → same id; different inputs → different ids; strategy-tag prefix present.
2. `__init__` mutual exclusion: `retried_from` and `forked_from` both non-None raises `ValueError`.
3. `__init__` counter alignment: `retried_from is None and retry_index > 0` raises; same for fork.
4. `__init__` tz-aware datetime validation: naive datetime raises.
5. `__init__` state-value validation: bogus state raises.
6. `start_active` from `pending`: returns new instance with `state="active"`, same `id`.
7. `start_active` from non-pending: raises `ValueError`.
8. `complete_done` happy path: returns new instance with `state="done"` and terminal fields populated, same `id`.
9. `complete_failed`, `complete_timed_out`, `complete_abandoned`: each verifies state transition + terminal fields.
10. State transitions are frozen-pin-respecting: returned instances have all input-field values preserved.
11. `_clone` preserves `id` and all unchanged fields.
12. `derive_drift_evidence`: empty when hashes match, single-entry when they differ.
13. `derive_drift_evidence` with `plan_hash=None`: returns `()` (no plan-side hash to compare against).

**`tests/test_persistence_dispatch_runs.py`** — persistence tests:
1. `save_dispatch_run` + `get_dispatch_run` round-trip: a saved DispatchRun reads back to a dict with all fields preserved (`drift_evidence` deserialized, `drift_against_plan` as bool, datetimes as ISO strings).
2. `save_dispatch_run` is idempotent via `INSERT OR REPLACE`: saving twice with same id leaves one row.
3. `save_dispatch_run` with terminal state replaces the prior active state.
4. `list_dispatch_runs` filters by `plan_id`, `unit_slug`, `state`.
5. `get_dispatch_runs_for_unit` returns dispatch chain in dispatched_at order.
6. The `dispatch_runs` table is created at `_get_db` initialization (assert by checking `sqlite_master`).
7. `_SCHEMA_VERSION == 9` (sanity).

For the existing test suite, do NOT modify existing runner/kernel/persistence tests unless they break. If a test fails because of the dual-write or new dispatch_run mint, prefer to add a new test asserting the right behavior rather than modifying the failing test in place. Flag the failure in your EngineerReturn so the Watermaster can integrate.

The CLI test surface (`test_cli*.py`) shouldn't be affected because Brief 9 doesn't change CLI flags or output formats — `dispatched_by` is constructor-injected with a default. If a CLI test breaks anyway, flag it.

### Item M — Optional `__init__.py` exports

If `src/dgov/__init__.py` re-exports public types from `dgov.types`, add `DispatchRun`, `DispatchRunState`, `WatermasterId` to the same list. If `__init__.py` is empty / minimal, leave it alone.

---

## Out of scope (explicit)

- **Lifecycle narrowing** (Brief 10 territory): do NOT peel `reviewing/reviewed_pass/reviewed_fail/merging/merged` off `TaskState`. They remain on the legacy `WorkerTask`; the new `dispatch_runs` table only carries the 6-value `DispatchRunState`. This is the SOP "Do Not" §47.
- **Removing the `tasks` table or the `WorkerTask` writes** (Brief 11 territory): dual-write only.
- **`sop_bundler.compute_sop_set_hash` revision** (bundler-level escalate): inherit the gap; do not touch.
- **Plan-shape v3 to capture plan-time bundle composition**: out of scope; `drift_evidence` records the single `metadata:modified=bundle:sop_set_hash` descriptor when hashes differ.
- **Event reference fields** (`from_dispatch_run_id` on events): out of scope; events keep their current surface forms. `event-emission.md` v1's lift discipline applies to a future Brief.
- **Adding `dispatch_run_id` to existing typed events**: out of scope.
- **Worker-subprocess-side awareness of DispatchRun id**: out of scope; the worker continues to see only its prompt and exit telemetry. DispatchRun is purely runner-side.

If you encounter useful adjacent work during execution, **flag it in your EngineerReturn rather than writing it**.

---

## Acceptance criteria

Codex's EngineerReturn should report:
- **All items A–M complete**, with file paths and line ranges for each modification.
- **Full pytest run**: `cd /Users/jakegearon/projects/dgov && uv run pytest` (or `pytest` if uv isn't in scope). Report pass/skip/fail counts. The new tests should all pass. Pre-existing tests should pass unchanged unless a test legitimately depended on legacy WorkerTask-only behavior (flag any such test).
- **`ruff check`** clean on every modified file. Run `ruff check /Users/jakegearon/projects/dgov/src/dgov/dispatch_run.py /Users/jakegearon/projects/dgov/src/dgov/persistence/dispatch_runs.py /Users/jakegearon/projects/dgov/src/dgov/runner.py /Users/jakegearon/projects/dgov/src/dgov/persistence/connection.py /Users/jakegearon/projects/dgov/src/dgov/persistence/schema.py /Users/jakegearon/projects/dgov/src/dgov/persistence/sql.py /Users/jakegearon/projects/dgov/src/dgov/types.py` (or the project-default `ruff check` over the whole source tree if cleaner).
- **`ty check`** clean on the same set if `ty` is configured in this repo (`pyproject.toml` will tell you). If `ty` isn't here, use `mypy`'s output or whatever the repo's pre-existing type-check command is. If no type-checker is configured, skip — flag in the EngineerReturn.
- **`_SCHEMA_VERSION` is 9.**
- **The new `dispatch_runs` table is created automatically** when a fresh dgov session opens its DB (via `_get_db`'s init path).
- **Every modified runner code path has a passing test** OR an explicit flag in the EngineerReturn that the test path is uncovered and why.

If you discover **any deviation from this Brief that you believe is the right call** (parallel to Cascade's Brief 4 deviations on `_clone` vs `dataclasses.replace`, or Bench's Brief 8 D8 constant correction), document it in your EngineerReturn under a clear "Deviations" section with reasoning. The seated Watermaster will integrate.

If you find that **a file or function you must touch has changed since the recon and the Brief is now inconsistent with current source**, **stop and flag** rather than guessing — the Watermaster will issue a revision Brief.

---

## Format for your return

Return a single chat message containing:

```
## Summary
1–3 sentence description of what landed.

## Items
- A: <one-line status + key files/lines touched>
- B: ...
- ...
- M: ...

## Test results
- pytest: <N passed, M skipped, K failed>
- ruff: <clean | issues listed>
- ty (or mypy): <clean | issues listed | N/A — no type-checker configured>

## Deviations
- <deviation 1>: <reasoning>
- <deviation 2>: ...
- (none if you held the Brief exactly)

## Flags (adjacent work surfaced, NOT written)
- <flag 1>: <one-line reason worth tracking>
- ...

## Files written
- <path 1>: <one-line description>
- <path 2>: ...
```

Keep prose tight. The Watermaster will integrate from the structured return; verbose narrative isn't needed.

---

**Self-contained**: read the seven listed Background documents plus the source files cited, and you have everything. Do not read prior Briefs (1–8) or lineage entries — they're not in scope. Do not modify `sketches/lineage/*` under any circumstances. Stay strictly inside the declared `write_scope`.

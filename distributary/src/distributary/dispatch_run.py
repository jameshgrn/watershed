"""DispatchRun typed record for one worker execution attempt.

Ported from dgov dispatch_run.py — SOP-aligned subset for v0 outbound records.
No ``run_source`` field in v0 per Brief §Required Types #6.
"""

from __future__ import annotations

import hashlib
from dataclasses import InitVar, dataclass, field, fields
from datetime import datetime
from typing import Literal

from distributary._compat import _canonical_json, _require_utc

DispatchRunState = Literal["pending", "active", "done", "failed", "timed_out", "abandoned"]

_DISPATCH_RUN_STATES = frozenset(
    {
        "pending",
        "active",
        "done",
        "failed",
        "timed_out",
        "abandoned",
    }
)


def _validate_dispatch_lineage(
    *,
    retried_from: str | None,
    forked_from: str | None,
    retry_index: int,
    fork_depth: int,
) -> None:
    if retried_from is not None and forked_from is not None:
        raise ValueError("retried_from and forked_from are mutually exclusive")
    if retried_from is None and retry_index != 0:
        raise ValueError("retry_index must be 0 when retried_from is None")
    if retried_from is not None and retry_index < 1:
        raise ValueError("retry_index must be >= 1 when retried_from is set")
    if forked_from is None and fork_depth != 0:
        raise ValueError("fork_depth must be 0 when forked_from is None")
    if forked_from is not None and fork_depth < 1:
        raise ValueError("fork_depth must be >= 1 when forked_from is set")


def _validate_dispatch_state(state: DispatchRunState) -> None:
    if state not in _DISPATCH_RUN_STATES:
        raise ValueError(f"Invalid DispatchRun state: {state!r}")


def _validate_dispatch_timestamps(
    *,
    dispatched_at: datetime,
    terminated_at: datetime | None,
) -> None:
    _require_utc(dispatched_at, "dispatched_at")
    if terminated_at is not None:
        _require_utc(terminated_at, "terminated_at")


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
    """Content-derive a stable DispatchRun id with strategy tag ``disprun:``."""
    _require_utc(dispatched_at, "dispatched_at")
    payload = {
        "from_plan_id": from_plan_id,
        "unit_slug": unit_slug,
        "worktree_id": worktree_id,
        "branch": branch,
        "base_commit": base_commit,
        "agent_model": agent_model,
        "effective_sop_set_hash": effective_sop_set_hash,
        "retried_from": retried_from,
        "forked_from": forked_from,
        "retry_index": retry_index,
        "fork_depth": fork_depth,
        "dispatched_at": dispatched_at.isoformat(),
    }
    digest = hashlib.sha256(f"disprun:{_canonical_json(payload)}".encode()).hexdigest()
    return f"disprun:{digest}"


def _dispatch_run_id_from_instance(run: DispatchRun, explicit_id: str | None) -> str:
    if explicit_id is not None:
        return explicit_id
    return derive_dispatch_run_id(
        from_plan_id=run.from_plan_id,
        unit_slug=run.unit_slug,
        worktree_id=run.worktree_id,
        branch=run.branch,
        base_commit=run.base_commit,
        agent_model=run.agent_model,
        effective_sop_set_hash=run.effective_sop_set_hash,
        retried_from=run.retried_from,
        forked_from=run.forked_from,
        retry_index=run.retry_index,
        fork_depth=run.fork_depth,
        dispatched_at=run.dispatched_at,
    )


@dataclass(frozen=True, slots=True)
class DispatchRun:
    """One worker execution attempt, content-identified and lifecycle-tracked."""

    id: str = field(init=False)
    from_plan_id: str
    unit_slug: str
    worktree_id: str
    branch: str
    base_commit: str
    agent_model: str
    effective_sop_set_hash: str
    drift_against_plan: bool
    dispatched_by: str
    dispatched_at: datetime
    drift_evidence: tuple[str, ...] = ()
    retried_from: str | None = None
    forked_from: str | None = None
    retry_index: int = 0
    fork_depth: int = 0
    state: DispatchRunState = "pending"
    exit_code: int | None = None
    last_error: str = ""
    output_dir: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    iteration_count: int = 0
    terminated_at: datetime | None = None
    _id: InitVar[str | None] = None

    def __post_init__(self, _id: str | None) -> None:
        _validate_dispatch_lineage(
            retried_from=self.retried_from,
            forked_from=self.forked_from,
            retry_index=self.retry_index,
            fork_depth=self.fork_depth,
        )
        _validate_dispatch_state(self.state)
        _validate_dispatch_timestamps(
            dispatched_at=self.dispatched_at,
            terminated_at=self.terminated_at,
        )
        object.__setattr__(self, "drift_evidence", tuple(self.drift_evidence))
        object.__setattr__(self, "id", _dispatch_run_id_from_instance(self, _id))

    def _clone(self, **changes: object) -> DispatchRun:
        """Produce a new frozen instance with changes applied, preserving id."""
        values = {f.name: getattr(self, f.name) for f in fields(self)}
        values.update(changes)
        values["_id"] = self.id
        values.pop("id")
        return DispatchRun(**values)

    def start_active(self) -> DispatchRun:
        """Transition pending to active; input fields freeze here."""
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
    ) -> DispatchRun:
        """Transition active to done."""
        if self.state != "active":
            raise ValueError(f"Cannot transition from {self.state} to done")
        if exit_code != 0:
            raise ValueError("done DispatchRuns must have exit_code == 0")
        return self._clone(
            state="done",
            exit_code=exit_code,
            last_error="",
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
    ) -> DispatchRun:
        """Transition active to failed."""
        if self.state != "active":
            raise ValueError(f"Cannot transition from {self.state} to failed")
        if exit_code == 0:
            raise ValueError("failed DispatchRuns must have non-zero exit_code")
        if not last_error:
            raise ValueError("failed DispatchRuns must have last_error")
        return self._clone(
            state="failed",
            exit_code=exit_code,
            last_error=last_error,
            output_dir=output_dir,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            iteration_count=iteration_count,
            terminated_at=terminated_at,
        )

    def complete_timed_out(
        self,
        *,
        last_error: str,
        output_dir: str,
        prompt_tokens: int,
        completion_tokens: int,
        iteration_count: int,
        terminated_at: datetime,
    ) -> DispatchRun:
        """Transition active to timed_out."""
        if self.state != "active":
            raise ValueError(f"Cannot transition from {self.state} to timed_out")
        if not last_error:
            raise ValueError("timed_out DispatchRuns must have last_error")
        return self._clone(
            state="timed_out",
            exit_code=None,
            last_error=last_error,
            output_dir=output_dir,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            iteration_count=iteration_count,
            terminated_at=terminated_at,
        )

    def complete_abandoned(
        self,
        *,
        last_error: str,
        output_dir: str,
        prompt_tokens: int,
        completion_tokens: int,
        iteration_count: int,
        terminated_at: datetime,
    ) -> DispatchRun:
        """Transition active to abandoned."""
        if self.state != "active":
            raise ValueError(f"Cannot transition from {self.state} to abandoned")
        if not last_error:
            raise ValueError("abandoned DispatchRuns must have last_error")
        return self._clone(
            state="abandoned",
            exit_code=None,
            last_error=last_error,
            output_dir=output_dir,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            iteration_count=iteration_count,
            terminated_at=terminated_at,
        )

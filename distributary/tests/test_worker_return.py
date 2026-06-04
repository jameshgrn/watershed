"""WorkerReturn tests for terminal dispatch telemetry."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from typing import Any, cast

import pytest

from distributary.dispatch_run import DispatchRun
from distributary.worker_return import WorkerReturn, WorkerReturnState


def _dt(offset: int = 0) -> datetime:
    return datetime(2026, 5, 15, 12, 0, offset, tzinfo=UTC)


def _active_run(**overrides: Any) -> DispatchRun:
    kwargs: dict[str, Any] = {
        "from_plan_id": "plan-a",
        "unit_slug": "unit-a",
        "worktree_id": "/tmp/worktree",
        "branch": "distributary/unit-a",
        "base_commit": "abc123",
        "agent_model": "codex",
        "effective_sop_set_hash": "hash-a",
        "drift_against_plan": False,
        "dispatched_by": "watermaster:test",
        "dispatched_at": _dt(),
    }
    kwargs.update(overrides)
    return DispatchRun(**kwargs).start_active()


def test_done_worker_return_applies_to_active_dispatch_run() -> None:
    active = _active_run()
    returned = WorkerReturn(
        dispatch_run_id=active.id,
        state="done",
        exit_code=0,
        output_dir="/tmp/out",
        prompt_tokens=10,
        completion_tokens=20,
        iteration_count=3,
        terminated_at=_dt(1),
    )

    terminal = returned.apply_to(active)

    assert terminal.id == active.id
    assert terminal.state == "done"
    assert terminal.exit_code == 0
    assert terminal.output_dir == "/tmp/out"
    assert terminal.prompt_tokens == 10
    assert terminal.completion_tokens == 20
    assert terminal.iteration_count == 3
    assert terminal.terminated_at == _dt(1)


def test_failed_worker_return_applies_to_active_dispatch_run() -> None:
    active = _active_run()
    returned = WorkerReturn(
        dispatch_run_id=active.id,
        state="failed",
        exit_code=2,
        last_error="tests failed",
        output_dir="/tmp/out",
        terminated_at=_dt(1),
    )

    terminal = returned.apply_to(active)

    assert terminal.state == "failed"
    assert terminal.exit_code == 2
    assert terminal.last_error == "tests failed"


@pytest.mark.parametrize("state", ["timed_out", "abandoned"])
def test_non_exit_terminal_worker_return_applies_to_active_dispatch_run(
    state: WorkerReturnState,
) -> None:
    active = _active_run()
    returned = WorkerReturn(
        dispatch_run_id=active.id,
        state=state,
        exit_code=None,
        last_error="stopped",
        output_dir="/tmp/out",
        terminated_at=_dt(1),
    )

    terminal = returned.apply_to(active)

    assert terminal.state == state
    assert terminal.exit_code is None
    assert terminal.last_error == "stopped"


def test_worker_return_rejects_mismatched_dispatch_run_id() -> None:
    active = _active_run()
    returned = WorkerReturn(
        dispatch_run_id="disprun:other",
        state="done",
        exit_code=0,
        output_dir="/tmp/out",
        terminated_at=_dt(1),
    )

    with pytest.raises(ValueError, match="does not match"):
        returned.apply_to(active)


def test_worker_return_rejects_non_dispatch_id() -> None:
    with pytest.raises(ValueError, match="disprun"):
        WorkerReturn(
            dispatch_run_id="task-a",
            state="done",
            exit_code=0,
            output_dir="/tmp/out",
            terminated_at=_dt(1),
        )


def test_worker_return_rejects_non_terminal_state() -> None:
    with pytest.raises(ValueError, match="Invalid WorkerReturn state"):
        WorkerReturn(
            dispatch_run_id="disprun:abc",
            state=_invalid_state("active"),
            exit_code=0,
            output_dir="/tmp/out",
            terminated_at=_dt(1),
        )


def _invalid_state(value: str) -> WorkerReturnState:
    return cast(WorkerReturnState, value)


def test_worker_return_rejects_naive_terminated_at() -> None:
    with pytest.raises(ValueError, match="terminated_at"):
        WorkerReturn(
            dispatch_run_id="disprun:abc",
            state="done",
            exit_code=0,
            output_dir="/tmp/out",
            terminated_at=datetime(2026, 5, 15, 12, 0, 0),
        )


def test_worker_return_rejects_non_utc_terminated_at() -> None:
    with pytest.raises(ValueError, match="UTC"):
        WorkerReturn(
            dispatch_run_id="disprun:abc",
            state="done",
            exit_code=0,
            output_dir="/tmp/out",
            terminated_at=datetime(2026, 5, 15, 12, 0, 0, tzinfo=timezone(timedelta(hours=1))),
        )


@pytest.mark.parametrize(
    ("state", "exit_code", "last_error"),
    [
        ("done", 1, ""),
        ("done", 0, "unexpected"),
        ("failed", 0, "failed"),
        ("failed", 2, ""),
        ("timed_out", 124, "timeout"),
        ("abandoned", None, ""),
    ],
)
def test_worker_return_rejects_illegal_terminal_payloads(
    state: WorkerReturnState,
    exit_code: int | None,
    last_error: str,
) -> None:
    with pytest.raises(ValueError):
        WorkerReturn(
            dispatch_run_id="disprun:abc",
            state=state,
            exit_code=exit_code,
            last_error=last_error,
            output_dir="/tmp/out",
            terminated_at=_dt(1),
        )


def test_worker_return_rejects_negative_prompt_tokens() -> None:
    with pytest.raises(ValueError, match="prompt_tokens"):
        WorkerReturn(
            dispatch_run_id="disprun:abc",
            state="done",
            exit_code=0,
            output_dir="/tmp/out",
            terminated_at=_dt(1),
            prompt_tokens=-1,
        )


def test_worker_return_rejects_negative_completion_tokens() -> None:
    with pytest.raises(ValueError, match="completion_tokens"):
        WorkerReturn(
            dispatch_run_id="disprun:abc",
            state="done",
            exit_code=0,
            output_dir="/tmp/out",
            terminated_at=_dt(1),
            completion_tokens=-1,
        )


def test_worker_return_rejects_negative_iteration_count() -> None:
    with pytest.raises(ValueError, match="iteration_count"):
        WorkerReturn(
            dispatch_run_id="disprun:abc",
            state="done",
            exit_code=0,
            output_dir="/tmp/out",
            terminated_at=_dt(1),
            iteration_count=-1,
        )

"""Typed terminal return envelope from a worker boundary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, TypeAlias

from distributary._compat import _require_utc
from distributary.dispatch_run import DispatchRun

WorkerReturnState: TypeAlias = Literal["done", "failed", "timed_out", "abandoned"]

_WORKER_RETURN_STATES = frozenset({"done", "failed", "timed_out", "abandoned"})


@dataclass(frozen=True, slots=True)
class WorkerReturn:
    """Terminal telemetry returned from one worker execution attempt."""

    dispatch_run_id: str
    state: WorkerReturnState
    exit_code: int | None
    output_dir: str
    terminated_at: datetime
    last_error: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    iteration_count: int = 0

    def __post_init__(self) -> None:
        _validate_dispatch_run_id(self.dispatch_run_id)
        _validate_state(self.state)
        _require_utc(self.terminated_at, "terminated_at")
        _validate_counts(
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            iteration_count=self.iteration_count,
        )
        _validate_terminal_payload(
            state=self.state,
            exit_code=self.exit_code,
            last_error=self.last_error,
        )

    def apply_to(self, run: DispatchRun) -> DispatchRun:
        """Return a terminal DispatchRun after applying this worker telemetry."""
        if run.id != self.dispatch_run_id:
            raise ValueError(
                "WorkerReturn dispatch_run_id does not match DispatchRun.id: "
                f"{self.dispatch_run_id!r} != {run.id!r}"
            )
        if self.state == "done":
            return run.complete_done(
                exit_code=0,
                output_dir=self.output_dir,
                prompt_tokens=self.prompt_tokens,
                completion_tokens=self.completion_tokens,
                iteration_count=self.iteration_count,
                terminated_at=self.terminated_at,
            )
        if self.state == "failed":
            if self.exit_code is None:
                raise ValueError("failed WorkerReturns must have exit_code")
            return run.complete_failed(
                exit_code=self.exit_code,
                last_error=self.last_error,
                output_dir=self.output_dir,
                prompt_tokens=self.prompt_tokens,
                completion_tokens=self.completion_tokens,
                iteration_count=self.iteration_count,
                terminated_at=self.terminated_at,
            )
        if self.state == "timed_out":
            return run.complete_timed_out(
                last_error=self.last_error,
                output_dir=self.output_dir,
                prompt_tokens=self.prompt_tokens,
                completion_tokens=self.completion_tokens,
                iteration_count=self.iteration_count,
                terminated_at=self.terminated_at,
            )
        return run.complete_abandoned(
            last_error=self.last_error,
            output_dir=self.output_dir,
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            iteration_count=self.iteration_count,
            terminated_at=self.terminated_at,
        )


def _validate_dispatch_run_id(value: str) -> None:
    if not value.startswith("disprun:"):
        raise ValueError("dispatch_run_id must reference a DispatchRun id with 'disprun:' prefix")


def _validate_state(state: WorkerReturnState) -> None:
    if state not in _WORKER_RETURN_STATES:
        raise ValueError(f"Invalid WorkerReturn state: {state!r}")


def _validate_counts(
    *,
    prompt_tokens: int,
    completion_tokens: int,
    iteration_count: int,
) -> None:
    if prompt_tokens < 0:
        raise ValueError("prompt_tokens must be >= 0")
    if completion_tokens < 0:
        raise ValueError("completion_tokens must be >= 0")
    if iteration_count < 0:
        raise ValueError("iteration_count must be >= 0")


def _validate_terminal_payload(
    *,
    state: WorkerReturnState,
    exit_code: int | None,
    last_error: str,
) -> None:
    if state == "done":
        if exit_code != 0:
            raise ValueError("done WorkerReturns must have exit_code == 0")
        if last_error:
            raise ValueError("done WorkerReturns must not have last_error")
        return
    if state == "failed":
        if exit_code is None or exit_code == 0:
            raise ValueError("failed WorkerReturns must have non-zero exit_code")
        if not last_error:
            raise ValueError("failed WorkerReturns must have last_error")
        return
    if exit_code is not None:
        raise ValueError(f"{state} WorkerReturns must not have exit_code")
    if not last_error:
        raise ValueError(f"{state} WorkerReturns must have last_error")

"""Rim-side verification execution and evidence emission."""

from __future__ import annotations

import json
import subprocess
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class VerificationRunnerError(Exception):
    """Raised when verification inputs are malformed."""


@dataclass(frozen=True)
class CommandExecution:
    returncode: int | None
    stdout: str
    stderr: str


@dataclass(frozen=True)
class CheckCommand:
    name: str
    command: tuple[str, ...]
    cwd: Path
    timeout_seconds: float | None


@dataclass(frozen=True)
class CheckEvidence:
    name: str
    status: str
    command: tuple[str, ...]
    cwd: Path | None
    started_at: str | None
    finished_at: str | None
    duration_seconds: float | None
    exit_code: int | None
    stdout: str
    stderr: str

    def as_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "evidence_kind": "command",
            "command": list(self.command),
            "cwd": str(self.cwd) if self.cwd else None,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_seconds": self.duration_seconds,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


@dataclass(frozen=True)
class VerificationEvidence:
    root: Path
    spec_path: Path
    manifest_path: Path
    declared_checks: tuple[str, ...]
    checks: tuple[CheckEvidence, ...]

    @property
    def verdict(self) -> str:
        if all(check.status == "pass" for check in self.checks):
            return "pass"
        return "fail"

    def as_json(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "runner": "lab.verification",
            "root": str(self.root),
            "spec_path": str(self.spec_path),
            "manifest_path": str(self.manifest_path),
            "verification_spec": {"checks": list(self.declared_checks)},
            "verdict": self.verdict,
            "checks": [check.as_json() for check in self.checks],
        }

    def to_json(self, *, indent: int | None = None) -> str:
        return json.dumps(self.as_json(), indent=indent, sort_keys=True)


CommandRunner = Callable[[Sequence[str], Path, float | None], CommandExecution]


def run_verification(
    *,
    spec_path: Path,
    manifest_path: Path,
    root: Path,
    command_runner: CommandRunner | None = None,
) -> VerificationEvidence:
    root = root.resolve()
    spec_path = _resolve_input_path(spec_path, root)
    manifest_path = _resolve_input_path(manifest_path, root)
    checks = _read_verification_spec(spec_path)
    manifest = _read_manifest(manifest_path, root)
    runner = command_runner or _run_command

    evidence = tuple(_run_check(name, manifest.get(name), runner) for name in checks)
    return VerificationEvidence(
        root=root,
        spec_path=spec_path,
        manifest_path=manifest_path,
        declared_checks=checks,
        checks=evidence,
    )


def _run_check(
    name: str,
    check_command: CheckCommand | None,
    runner: CommandRunner,
) -> CheckEvidence:
    if check_command is None:
        return CheckEvidence(
            name=name,
            status="fail",
            command=(),
            cwd=None,
            started_at=None,
            finished_at=None,
            duration_seconds=None,
            exit_code=None,
            stdout="",
            stderr=f"no command manifest entry for declared check '{name}'",
        )

    started_at = _utc_now()
    started = time.monotonic()
    result = runner(
        check_command.command,
        check_command.cwd,
        check_command.timeout_seconds,
    )
    finished_at = _utc_now()
    duration = round(time.monotonic() - started, 6)
    status = "pass" if result.returncode == 0 else "fail"

    return CheckEvidence(
        name=name,
        status=status,
        command=check_command.command,
        cwd=check_command.cwd,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration,
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def _run_command(
    command: Sequence[str],
    cwd: Path,
    timeout_seconds: float | None,
) -> CommandExecution:
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        message = f"command timed out after {timeout_seconds} seconds"
        return CommandExecution(
            returncode=None,
            stdout=stdout,
            stderr="\n".join(part for part in (stderr, message) if part),
        )
    except OSError as exc:
        return CommandExecution(returncode=None, stdout="", stderr=str(exc))

    return CommandExecution(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _read_verification_spec(path: Path) -> tuple[str, ...]:
    payload = _read_json_object(path, label="VerificationSpec")
    checks = payload.get("checks")
    if not isinstance(checks, list):
        raise VerificationRunnerError("VerificationSpec must contain a checks list")

    parsed = []
    for check in checks:
        if not isinstance(check, str) or not check.strip():
            raise VerificationRunnerError(
                "VerificationSpec checks must be non-empty strings"
            )
        parsed.append(check)

    if not parsed:
        raise VerificationRunnerError("VerificationSpec must declare at least one check")
    return tuple(parsed)


def _read_manifest(path: Path, root: Path) -> dict[str, CheckCommand]:
    payload = _read_json_object(path, label="verification manifest")
    checks = payload.get("checks")
    if not isinstance(checks, Mapping):
        raise VerificationRunnerError("verification manifest must contain a checks object")

    manifest = {}
    for name, raw_spec in checks.items():
        if not isinstance(name, str) or not name.strip():
            raise VerificationRunnerError("manifest check names must be non-empty strings")
        if not isinstance(raw_spec, Mapping):
            raise VerificationRunnerError(f"manifest entry for '{name}' must be an object")
        manifest[name] = _parse_check_command(name, raw_spec, root)
    return manifest


def _parse_check_command(
    name: str,
    raw_spec: Mapping[str, object],
    root: Path,
) -> CheckCommand:
    raw_command = raw_spec.get("command")
    if not isinstance(raw_command, list) or not raw_command:
        raise VerificationRunnerError(
            f"manifest entry for '{name}' must contain a non-empty command list"
        )
    command = []
    for value in raw_command:
        if not isinstance(value, str) or not value:
            raise VerificationRunnerError(
                f"manifest command for '{name}' must contain only non-empty strings"
            )
        command.append(value)

    raw_cwd = raw_spec.get("cwd", ".")
    if not isinstance(raw_cwd, str) or not raw_cwd:
        raise VerificationRunnerError(f"manifest cwd for '{name}' must be a string")

    timeout_seconds = _parse_timeout(raw_spec.get("timeout_seconds"), name)
    return CheckCommand(
        name=name,
        command=tuple(command),
        cwd=(root / raw_cwd).resolve(),
        timeout_seconds=timeout_seconds,
    )


def _parse_timeout(raw_timeout: object, name: str) -> float | None:
    if raw_timeout is None:
        return None
    if not isinstance(raw_timeout, (int, float)) or raw_timeout <= 0:
        raise VerificationRunnerError(
            f"manifest timeout_seconds for '{name}' must be a positive number"
        )
    return float(raw_timeout)


def _read_json_object(path: Path, *, label: str) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise VerificationRunnerError(f"could not read {label} at {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise VerificationRunnerError(f"could not parse {label} at {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise VerificationRunnerError(f"{label} must be a JSON object")
    return payload


def _resolve_input_path(path: Path, root: Path) -> Path:
    if path.is_absolute():
        return path
    return (root / path).resolve()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

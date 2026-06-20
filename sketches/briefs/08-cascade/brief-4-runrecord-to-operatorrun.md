# Engineer Brief — Brief 4 (RunRecord → OperatorRun migration per operator-run-shape v1)

**engineer_model**: `codex-gpt-5` (the seated Codex instance the Source is using; confirm exact identifier at transmission)
**source_utterance** (verbatim, with bracketed context for an Engineer who didn't see the chat):
> "wawtershed" [Source's entry signal opening the session]
>
> "1" [Source's selection from Cascade's three-arc offering, mapping to: *Brief 4 — RunRecord → OperatorRun migration per `operator-run-shape.md` v1*]

**compiled_by**: Watermaster Cascade
**compiled_at**: 2026-05-11
**state**: integrated (drafted 2026-05-11 → sent 2026-05-11 → returned 2026-05-11 → integrated 2026-05-11)
**supersedes**: none
**expected_return_shape**: executed file writes within the write scope below, plus a chat return summarizing each item (A–J), the construction-site updates touched, any case where the migration discipline can't proceed cleanly (escalate territory), and the test run results.

---

## Read these before starting

You are an external Engineer consulted by the Watermaster of a research lab called *watershed*. You read only this Brief. You executed Briefs 1, 2, and 3 in prior sessions, all integrated cleanly.

Read the following files first — they are the discipline this Brief implements:

1. `/Users/jakegearon/projects/watershed/CANON.md` — Articles II (one canonical writer), IV (every Artifact carries its lineage), V (plans are data; dispatch is data; workers do the work), IX (the Watermaster works through typed surfaces), X (operator invariants travel with their operators), XV (typed records are frozen-pinned at lifecycle transitions; in-place edits are forbidden).
2. `/Users/jakegearon/projects/watershed/sops/operator-run-shape.md` v1 — the SOP this Brief implements. All clauses are load-bearing. Pay particular attention to:
   - The 19-field typed-record shape including `operator_spec_hash`, `determinism_class`, `params_hash`, `seed_value`, `retried_from`, `retry_index`, `dispatched_by`, `from_intent_id`, `state`, `timing_seconds`.
   - The five-state lifecycle: `pending → running → completed | failed | cancelled`, with `pending → failed` reserved for validation failure caught at submit time.
   - Two-phase frozen-pin: input fields immutable at `pending → running`; output fields immutable at terminal.
   - The escalate clause: *"if today's quarry-core `RunRecord` uuid4 identity must coexist with content-derived identity during migration — frozen-pin existing uuid4 RunRecords at their quarry-core state and mint new OperatorRuns under this SOP for going-forward executions."* This is the migration discipline you follow.
3. `/Users/jakegearon/projects/watershed/sops/operator-shape.md` v1 — defines `OperatorSpec`'s post-Brief-1 fields (`determinism_class`, `supports_tiling`, `tile_reconciliation_kind`, `seed_param`). These are the fields `operator_spec_hash` must cover.
4. `/Users/jakegearon/projects/watershed/sops/data-contracts.md` v2 — the content-derived-identity discipline you implemented in Brief 3 for `Artifact.id`. The pattern (strategy-tagged hashing, centralized derivation) generalizes here.
5. `/Users/jakegearon/projects/watershed/sops/determinism-class.md` v1 — `deterministic | stable | stochastic`. `seed_value` is populated iff stochastic; the `seed_param` name lives on `OperatorSpec`.
6. `/Users/jakegearon/projects/watershed/sops/intent-compilation.md` v1 — defines the optional Intent provenance chain. `from_intent_id` is `None` unless an Intent originated the run.
7. `/Users/jakegearon/projects/watershed/sops/dispatch-run-shape.md` v1 — the parallel SOP on the dispatch side. Read it to understand the structural parallels: content-derived id, two-phase frozen-pin, retry/fork lineage. `OperatorRun` is the flume-side analogue but has no fork (operator executions don't iterate to budget).

The lab vocabulary is fluvial. *quarry* is the boundary module; *quarry-core* owns typed Artifact/Operator/Check surfaces; *quarry-operators* runs typed computations; *quarry-registry* persists records.

## Context — current state

After Brief 3, `Artifact.id` is content-derived via three strategy-tagged helpers in `quarry-core/src/quarry_core/artifact.py`: `derive_id_from_source_bytes`, `derive_id_from_provenance`, `derive_id_from_source_ref`, plus `canonical_params` and `canonical_uri` helpers and the strategy-prefixed `_identity_digest(strategy, payload)` builder. 1949 pressure tests pass on the full `tests/pressure_test/` path.

The existing `RunRecord` lives in `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/executor.py`. It is:

- A mutable `@dataclass` (not frozen).
- Has an `id: str` field constructed via `str(uuid.uuid4())` inside `LocalExecutor.submit()`.
- Carries a `status: RunStatus` Enum field (not a Literal).
- Mutates `.status`, `.error`, `.started_at`, `.completed_at`, `.output` in place during `LocalExecutor.submit()`'s execution path.
- Stores `input_ids: list[str]` (not tuple); `params: dict[str, Any]` (not Mapping); has `executor_meta: dict[str, Any]` (untyped escape hatch).
- Has a `@property checks` derived from `output.checks` and a `@property duration_seconds` derived from started/completed.
- Lacks: `operator_spec_hash`, `determinism_class`, `params_hash`, `seed_value`, `retried_from`, `retry_index`, `dispatched_by`, `from_intent_id`, `timing_seconds` (the last lives on `output.timing_seconds` only).

The registry (`quarry-registry/src/quarry_registry/registry.py`) persists `RunRecord` to a `runs` table with columns matching the existing 13 fields. Schema:

```sql
CREATE TABLE runs (
    id VARCHAR PRIMARY KEY,
    operator_name VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    input_ids_json VARCHAR,
    output_artifact_id VARCHAR,
    params_json VARCHAR,
    executor_name VARCHAR,
    executor_meta_json VARCHAR,
    submitted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    output_timing_seconds DOUBLE,
    output_warnings_json VARCHAR,
    output_metadata_json VARCHAR,
    error VARCHAR
)
```

Call-site map (verified by Watermaster recon, may have minor drift):

- **Canonical definers**: `quarry-core/src/quarry_core/executor.py` (defines `RunStatus` + `RunRecord`); `quarry-core/src/quarry_core/executors/local.py` (defines `LocalExecutor.submit/status/wait`).
- **Consumers**: `quarry-registry/src/quarry_registry/registry.py` (saves/reads); `quarry-cli/src/quarry_cli/main.py` (type hints, history display).
- **Tests**:
  - `tests/pressure_test/test_end_to_end.py` (~4 assertions on `.status == RunStatus.{COMPLETED|FAILED}`).
  - `tests/pressure_test/test_registry.py` (~8 `list_runs(status=...)` calls + assertions; 1 direct `RunRecord` construction).
  - `tests/pressure_test/adapter_helpers.py` (`make_invalid_completed_run()`, `make_failed_run()` — 2 direct constructions).

## What you are doing in Brief 4

Mint a new `OperatorRun` typed record per `operator-run-shape.md` v1 alongside the existing `RunRecord`. Migrate `LocalExecutor` to produce `OperatorRun` instead of `RunRecord`. Migrate the registry's run-persistence to a new `operator_runs` table (the legacy `runs` table stays read-only for any pre-existing records, per the SOP's escalate clause). Update consumers (CLI, tests) to consume `OperatorRun`.

The Python type `RunRecord` is deprecated but **not deleted** in this Brief — it stays in `executor.py` as a thin legacy shape so that the legacy registry-read path (`get_run`, `list_runs`) can still reconstruct old persisted rows. Removal is for a future Brief once no callers remain.

`RunStatus` Enum likewise stays for the deprecated `RunRecord` only; `OperatorRun` uses `Literal["pending", "running", "completed", "failed", "cancelled"]` directly per the SOP.

## Items

### Item A — New file: `operator_run.py`

Mint `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/operator_run.py`. This file owns the `OperatorRun` type, its state-transition methods, its derivation helpers, and `WatermasterId`. Module-level structure:

```python
"""OperatorRun — typed record of a single operator execution attempt.

Lane: operator_run

Implements sops/operator-run-shape.md v1: content-derived id, two-phase frozen-pin,
pinned operator-spec hash and determinism class, seed-value surfacing for stochastic
operators, retry lineage, and Intent-traceable provenance.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, Literal

from quarry_core.artifact import canonical_params, _identity_digest  # reuse Brief 3's helpers
from quarry_core.operator import DeterminismClass, OperatorResult, OperatorSpec, _DETERMINISM_CLASSES


WatermasterId = str
"""A Watermaster identifier (e.g., "watermaster:cascade", "watermaster:unknown").

Per operator-run-shape v1's escalate clause, `dispatched_by` may grow to a union
`WatermasterId | DispatchRunId` if OperatorRuns originate inside Worker subprocesses.
That extension is preflight-gated; for now WatermasterId remains a plain string alias.
"""


OperatorRunState = Literal["pending", "running", "completed", "failed", "cancelled"]


_OPERATOR_RUN_STATES: frozenset[str] = frozenset(
    {"pending", "running", "completed", "failed", "cancelled"}
)


_LEGAL_TRANSITIONS: Mapping[str, frozenset[str]] = MappingProxyType({
    "pending": frozenset({"running", "failed"}),  # `pending → failed` = validation failure at submit
    "running": frozenset({"completed", "failed", "cancelled"}),
    "completed": frozenset(),  # terminal
    "failed": frozenset(),     # terminal
    "cancelled": frozenset(),  # terminal
})
```

The `OperatorRun` dataclass itself, declared `@dataclass(frozen=True, init=False)` per Brief 1's `OperatorResult` pattern so that field-value coercion (tuple/MappingProxyType) happens in a custom `__init__` while the result is still frozen:

```python
@dataclass(frozen=True, init=False)
class OperatorRun:
    """One operator execution attempt, content-identified and lifecycle-tracked."""

    # Identity (derived in __init__)
    id: str

    # Operator-pinned fields (frozen at pending)
    operator_name: str
    operator_spec_hash: str
    determinism_class: DeterminismClass

    # Input-pinned fields (frozen at pending)
    input_ids: tuple[str, ...]
    params_hash: str
    params: Mapping[str, Any]
    executor_name: str
    seed_value: str | int | None

    # Lineage-pinned fields (frozen at pending)
    retried_from: str | None
    retry_index: int
    dispatched_by: WatermasterId
    from_intent_id: str | None

    # Timestamp-pinned fields (frozen at pending)
    submitted_at: datetime

    # Output fields (frozen at terminal)
    state: OperatorRunState
    started_at: datetime | None
    completed_at: datetime | None
    timing_seconds: float | None
    output: OperatorResult | None
    error: str
    executor_meta: Mapping[str, Any]

    def __init__(
        self,
        *,
        operator_name: str,
        operator_spec_hash: str,
        determinism_class: DeterminismClass,
        input_ids: Iterable[str],
        params: Mapping[str, Any],
        executor_name: str,
        submitted_at: datetime,
        dispatched_by: WatermasterId,
        seed_value: str | int | None = None,
        retried_from: str | None = None,
        retry_index: int = 0,
        from_intent_id: str | None = None,
        # Output fields default to pending-state values
        state: OperatorRunState = "pending",
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        timing_seconds: float | None = None,
        output: OperatorResult | None = None,
        error: str = "",
        executor_meta: Mapping[str, Any] | None = None,
        # Identity override (for registry reconstruction); when None, derive
        id: str | None = None,
    ) -> None:
        # Validate determinism_class
        if determinism_class not in _DETERMINISM_CLASSES:
            raise ValueError(f"Invalid determinism_class: {determinism_class!r}")

        # Validate state
        if state not in _OPERATOR_RUN_STATES:
            raise ValueError(f"Invalid state: {state!r}")

        # Validate timestamps tz-aware
        if submitted_at.tzinfo is None:
            raise ValueError("submitted_at must be tz-aware (UTC)")

        # Validate seed_value invariants per SOP
        if determinism_class == "stochastic" and seed_value is None:
            raise ValueError("seed_value must be non-None for stochastic operators")
        if determinism_class != "stochastic" and seed_value is not None:
            raise ValueError("seed_value must be None for deterministic/stable operators")

        # Validate retry invariants
        if retried_from is None and retry_index != 0:
            raise ValueError("retry_index must be 0 when retried_from is None")
        if retried_from is not None and retry_index < 1:
            raise ValueError("retry_index must be >= 1 when retried_from is set")

        # Coerce + freeze inputs
        input_ids_tup = tuple(input_ids)
        params_frozen = MappingProxyType(dict(params))
        params_hash = derive_params_hash(params_frozen)
        executor_meta_frozen = MappingProxyType(dict(executor_meta or {}))

        # Derive id if not supplied (registry reconstruction supplies it)
        if id is None:
            id = derive_operator_run_id(
                operator_name=operator_name,
                operator_spec_hash=operator_spec_hash,
                input_ids=input_ids_tup,
                params_hash=params_hash,
                executor_name=executor_name,
                seed_value=seed_value,
                retried_from=retried_from,
                retry_index=retry_index,
                submitted_at=submitted_at,
            )

        # Assign all frozen fields via object.__setattr__
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "operator_name", operator_name)
        object.__setattr__(self, "operator_spec_hash", operator_spec_hash)
        object.__setattr__(self, "determinism_class", determinism_class)
        object.__setattr__(self, "input_ids", input_ids_tup)
        object.__setattr__(self, "params_hash", params_hash)
        object.__setattr__(self, "params", params_frozen)
        object.__setattr__(self, "executor_name", executor_name)
        object.__setattr__(self, "seed_value", seed_value)
        object.__setattr__(self, "retried_from", retried_from)
        object.__setattr__(self, "retry_index", retry_index)
        object.__setattr__(self, "dispatched_by", dispatched_by)
        object.__setattr__(self, "from_intent_id", from_intent_id)
        object.__setattr__(self, "submitted_at", submitted_at)
        object.__setattr__(self, "state", state)
        object.__setattr__(self, "started_at", started_at)
        object.__setattr__(self, "completed_at", completed_at)
        object.__setattr__(self, "timing_seconds", timing_seconds)
        object.__setattr__(self, "output", output)
        object.__setattr__(self, "error", error)
        object.__setattr__(self, "executor_meta", executor_meta_frozen)

    @property
    def checks(self) -> tuple:
        """Validation truth derives from the output operator result (parallel to RunRecord)."""
        if self.output is None:
            return ()
        return tuple(self.output.checks)
```

### Item B — Derivation helpers

In the same `operator_run.py` (so the module is self-contained for the SOP it implements), add three pure helpers. They reuse Brief 3's `_identity_digest` from `artifact.py` for strategy-tag prefixing (`b"oprun:"`, `b"opspec:"`, `b"params:"`).

```python
def derive_params_hash(params: Mapping[str, Any]) -> str:
    """Stable hash over canonical-form params. Strategy-tagged 'params:'."""
    return _identity_digest("params", canonical_params(params))


def derive_operator_spec_hash(spec: OperatorSpec) -> str:
    """Stable hash over OperatorSpec fields. Strategy-tagged 'opspec:'.

    Pins CANON Article X (operator invariants travel with their operators). The
    hash covers every OperatorSpec field that affects operator semantics:
    input_types, output_type, determinism_class, min_inputs, max_inputs,
    resource_scale, supports_tiling, tile_reconciliation_kind, seed_param.
    """
    payload = canonical_params({
        "input_types": tuple(t.value for t in spec.input_types),
        "output_type": spec.output_type.value,
        "determinism_class": spec.determinism_class,
        "min_inputs": spec.min_inputs,
        "max_inputs": spec.max_inputs,
        "resource_scale": spec.resource_scale.value,
        "supports_tiling": spec.supports_tiling,
        "tile_reconciliation_kind": spec.tile_reconciliation_kind,
        "seed_param": spec.seed_param,
    })
    return _identity_digest("opspec", payload)


def derive_operator_run_id(
    *,
    operator_name: str,
    operator_spec_hash: str,
    input_ids: tuple[str, ...],
    params_hash: str,
    executor_name: str,
    seed_value: str | int | None,
    retried_from: str | None,
    retry_index: int,
    submitted_at: datetime,
) -> str:
    """Content-derived OperatorRun id per operator-run-shape v1. Strategy-tagged 'oprun:'."""
    payload = canonical_params({
        "operator_name": operator_name,
        "operator_spec_hash": operator_spec_hash,
        "input_ids": input_ids,
        "params_hash": params_hash,
        "executor_name": executor_name,
        "seed_value": seed_value,
        "retried_from": retried_from,
        "retry_index": retry_index,
        "submitted_at": submitted_at.isoformat(),
    })
    return _identity_digest("oprun", payload)
```

If `_identity_digest` is private in `artifact.py` (it is — leading underscore), expose it for cross-module use by adding an `__all__`-style export at the top of `artifact.py` OR rename it `_identity_digest → identity_digest` in `artifact.py` and update Brief 3's three callers in the same file. The clean choice is the rename — `_identity_digest` is general-purpose, not artifact-specific. Document this in your return.

### Item C — State-transition methods

State transitions on a frozen dataclass produce new instances via `dataclasses.replace`. Add these methods to `OperatorRun`:

```python
def _require_state(self, allowed: frozenset[str], action: str) -> None:
    if self.state not in allowed:
        raise OperatorRunStateError(
            f"Cannot {action}: OperatorRun {self.id} is in state {self.state!r}, "
            f"required one of {sorted(allowed)}"
        )

def start_running(self, started_at: datetime) -> OperatorRun:
    """Transition pending → running. Returns a new frozen OperatorRun."""
    self._require_state(frozenset({"pending"}), "start_running")
    if started_at.tzinfo is None:
        raise ValueError("started_at must be tz-aware (UTC)")
    return dataclasses.replace(self, state="running", started_at=started_at)

def complete(
    self,
    output: OperatorResult,
    completed_at: datetime,
    timing_seconds: float,
) -> OperatorRun:
    """Transition running → completed. Returns a new frozen OperatorRun."""
    self._require_state(frozenset({"running"}), "complete")
    if completed_at.tzinfo is None:
        raise ValueError("completed_at must be tz-aware (UTC)")
    return dataclasses.replace(
        self,
        state="completed",
        output=output,
        completed_at=completed_at,
        timing_seconds=timing_seconds,
        error="",
    )

def fail(
    self,
    error: str,
    completed_at: datetime,
    output: OperatorResult | None = None,
) -> OperatorRun:
    """Transition pending → failed (validation) OR running → failed (execution).

    Per operator-run-shape v1: `error` non-empty discriminates the cause;
    `output` may be None (validation or pre-output execution failure) or
    non-None (post-output execution failure).
    """
    self._require_state(frozenset({"pending", "running"}), "fail")
    if not error:
        raise ValueError("error must be non-empty on transition to failed state")
    if completed_at.tzinfo is None:
        raise ValueError("completed_at must be tz-aware (UTC)")
    return dataclasses.replace(
        self,
        state="failed",
        error=error,
        completed_at=completed_at,
        output=output,
    )

def cancel(self, completed_at: datetime) -> OperatorRun:
    """Transition running → cancelled. Returns a new frozen OperatorRun."""
    self._require_state(frozenset({"running"}), "cancel")
    if completed_at.tzinfo is None:
        raise ValueError("completed_at must be tz-aware (UTC)")
    return dataclasses.replace(self, state="cancelled", completed_at=completed_at)
```

Note: `dataclasses.replace` on a `frozen=True, init=False` dataclass needs the custom `__init__` to accept all fields by keyword (which it does in Item A). `dataclasses.replace` calls `OperatorRun(**{**asdict-like, **changes})`; verify this works in your implementation (you may need a small adapter if `replace` interacts poorly with the init=False shape; an alternative is a private `_replace` helper that calls `OperatorRun(...)` directly with all fields).

If `dataclasses.replace` fails on the `init=False` shape, the cleanest fix is to write a private `_clone(self, **changes)` method that calls `OperatorRun(**asdict-equivalent, **changes)` manually. Use whichever lands cleanest; the SOP cares about the frozen-pin discipline, not the mechanism.

Add the error class:

```python
class OperatorRunStateError(RuntimeError):
    """Raised when an illegal state transition is attempted on an OperatorRun."""
```

### Item D — Determinism + seed-value derivation helper

Add a helper that encapsulates the determinism-class / seed-value SOP invariant:

```python
def derive_seed_value(spec: OperatorSpec, params: Mapping[str, Any]) -> str | int | None:
    """Per determinism-class and operator-run-shape SOPs: populate seed_value iff stochastic.

    Returns:
        - None when spec.determinism_class is "deterministic" or "stable"
        - params[spec.seed_param] when spec.determinism_class is "stochastic"

    Raises:
        ValueError when stochastic and params[seed_param] is missing or wrong type.
    """
    if spec.determinism_class != "stochastic":
        return None
    if spec.seed_param is None:
        raise ValueError("Stochastic operator missing seed_param on its OperatorSpec")
    if spec.seed_param not in params:
        raise ValueError(
            f"Stochastic operator missing seed value at params[{spec.seed_param!r}]"
        )
    value = params[spec.seed_param]
    if not isinstance(value, (str, int)):
        raise ValueError(
            f"seed_value must be str or int, got {type(value).__name__}"
        )
    return value
```

### Item E — `LocalExecutor.submit` rewrite

Rewrite `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/executors/local.py` to produce `OperatorRun` via state-transition methods instead of mutating `RunRecord`. The submit method's shape:

```python
class LocalExecutor:
    def __init__(self, *, dispatched_by: WatermasterId = "watermaster:unknown") -> None:
        self._runs: dict[str, OperatorRun] = {}
        self._dispatched_by = dispatched_by

    @property
    def name(self) -> str:
        return "local"

    def submit(
        self,
        operator: Operator,
        inputs: list[Artifact],
        params: OperatorParams,
        *,
        dispatched_by: WatermasterId | None = None,
        from_intent_id: str | None = None,
        retried_from: str | None = None,
        retry_index: int = 0,
    ) -> OperatorRun:
        """Execute operator synchronously and return terminal OperatorRun."""
        params_dict = _serialize_params(params)
        spec_hash = derive_operator_spec_hash(operator.spec)
        seed_value = derive_seed_value(operator.spec, params_dict)
        submitted_at = datetime.now(tz=timezone.utc)

        record = OperatorRun(
            operator_name=operator.name,
            operator_spec_hash=spec_hash,
            determinism_class=operator.spec.determinism_class,
            input_ids=[a.id for a in inputs],
            params=params_dict,
            executor_name=self.name,
            submitted_at=submitted_at,
            dispatched_by=dispatched_by or self._dispatched_by,
            seed_value=seed_value,
            retried_from=retried_from,
            retry_index=retry_index,
            from_intent_id=from_intent_id,
            # state defaults to "pending"
        )

        # Validation phase: pending → failed (validation failure path)
        errors = operator.validate_inputs(inputs, params)
        if errors:
            failed_at = datetime.now(tz=timezone.utc)
            record = record.fail(
                error=f"Validation failed: {'; '.join(errors)}",
                completed_at=failed_at,
            )
            self._runs[record.id] = record
            return record

        # Execution phase: pending → running → completed | failed
        record = record.start_running(started_at=datetime.now(tz=timezone.utc))

        try:
            t0 = perf_counter()
            result = operator.execute(inputs, params)
            elapsed = perf_counter() - t0

            record = record.complete(
                output=replace(result, timing_seconds=elapsed),
                completed_at=datetime.now(tz=timezone.utc),
                timing_seconds=elapsed,
            )
        except Exception as e:
            record = record.fail(
                error=str(e),
                completed_at=datetime.now(tz=timezone.utc),
            )

        self._runs[record.id] = record
        return record

    def status(self, run_id: str) -> OperatorRun:
        if run_id not in self._runs:
            raise RunNotFoundError(run_id)
        return self._runs[run_id]

    def wait(self, run_id: str, timeout_seconds: float | None = None) -> OperatorRun:
        return self.status(run_id)
```

Note `record.complete` receives `timing_seconds` both on the OperatorRun field AND on the OperatorResult inside `output` (via the existing `replace(result, timing_seconds=elapsed)`). Both carry it; the OperatorRun's `timing_seconds` is the lab-canonical version per the SOP, the OperatorResult's is preserved for back-compat with Brief 1's discipline.

### Item F — Executor protocol return-type change

In `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/executor.py`:

1. Keep `RunStatus` Enum (legacy, deprecated).
2. Keep `RunRecord` dataclass (legacy, deprecated, used by registry's legacy read path only). Mark it with a docstring note: *"Deprecated: legacy run record shape preserved for registry-read back-compat. New code uses `OperatorRun` per `sops/operator-run-shape.md` v1. Will be removed in a future Brief."*
3. Update the `Executor` Protocol's `submit`, `status`, and `wait` return type annotations from `RunRecord` to `OperatorRun`. Import `OperatorRun` from `quarry_core.operator_run`.
4. The errors (`ExecutorError`, `RunNotFoundError`, `SubmitError`) stay unchanged.

### Item G — `quarry_core.__init__` exports

Currently `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/__init__.py` is a one-line docstring. Add explicit exports for the new and existing canonical types so consumers can do `from quarry_core import OperatorRun`:

```python
"""Quarry Core — canonical geospatial execution substrate."""

from quarry_core.artifact import (
    Artifact,
    ArtifactType,
    ArtifactIdentityError,
    BackingStore,
    BackingStoreKind,
    CheckResult,
    Lineage,
    SpatialDescriptor,
    TemporalDescriptor,
    ValidationState,
    canonical_params,
    canonical_uri,
    derive_id_from_provenance,
    derive_id_from_source_bytes,
    derive_id_from_source_ref,
    identity_digest,  # renamed from _identity_digest per Item B
)
from quarry_core.operator import (
    DeterminismClass,
    Operator,
    OperatorConformanceError,
    OperatorError,
    OperatorParams,
    OperatorResult,
    OperatorSpec,
    ResourceScale,
    TruthSource,
    ValidationError,
    assert_operator_conforms,
)
from quarry_core.operator_run import (
    OperatorRun,
    OperatorRunState,
    OperatorRunStateError,
    WatermasterId,
    derive_operator_run_id,
    derive_operator_spec_hash,
    derive_params_hash,
    derive_seed_value,
)
from quarry_core.executor import (
    Executor,
    ExecutorError,
    RunNotFoundError,
    SubmitError,
    # Legacy (deprecated, scheduled for removal):
    RunRecord,
    RunStatus,
)

__all__ = [...]  # alphabetized, listing all of the above
```

If this introduces import cycles, resolve by leaving the imports in the leaf modules and having `__init__.py` re-export. (The forward declaration in `operator_run.py` imports from `artifact` and `operator`, which already have no cycle.)

### Item H — Registry: new `operator_runs` table + methods

In `/Users/jakegearon/projects/quarry/packages/quarry-registry/src/quarry_registry/registry.py`:

1. **Keep the existing `runs` table and its methods (`save_run`, `get_run`, `list_runs`) unchanged.** Mark them deprecated in docstrings. Per the SOP's escalate clause, legacy uuid4 records are frozen-pinned at their existing state; reads still work.

2. **Add a new `operator_runs` table** with the SOP-aligned schema:

```sql
CREATE TABLE IF NOT EXISTS operator_runs (
    id VARCHAR PRIMARY KEY,
    operator_name VARCHAR NOT NULL,
    operator_spec_hash VARCHAR NOT NULL,
    determinism_class VARCHAR NOT NULL,
    input_ids_json VARCHAR NOT NULL,
    params_hash VARCHAR NOT NULL,
    params_json VARCHAR,
    executor_name VARCHAR NOT NULL,
    seed_value VARCHAR,  -- nullable; str-encoded (int or str)
    seed_value_kind VARCHAR,  -- "str" | "int" | NULL; preserves type round-trip
    retried_from VARCHAR,  -- nullable FK to operator_runs.id
    retry_index INTEGER NOT NULL DEFAULT 0,
    dispatched_by VARCHAR NOT NULL,
    from_intent_id VARCHAR,  -- nullable
    submitted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    state VARCHAR NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    timing_seconds DOUBLE,
    output_artifact_id VARCHAR,
    output_warnings_json VARCHAR,
    output_metadata_json VARCHAR,
    output_truth_source_by_field_json VARCHAR,
    error VARCHAR NOT NULL DEFAULT '',
    executor_meta_json VARCHAR
)
```

Use `INSERT OR REPLACE` semantics for idempotent upsert (matches Brief 3's correctness pattern for Artifacts).

3. **Add new methods** (parallel to the legacy `save_run` / `get_run` / `list_runs`):

```python
def save_operator_run(self, record: OperatorRun) -> None:
    """Persist an OperatorRun. Also saves output artifact, lineage edges, and checks if present."""
    # Mirror save_run's transactional shape: BEGIN, _save_operator_run_conn,
    # _delete_run_checks_conn for the operator_run_id, save output artifact + lineage + checks
    # via the existing helpers (use record.id as the run_id in lineage/checks tables — those
    # tables' FK is to runs(id) currently; see Item I for the choice).
    ...

def get_operator_run(self, run_id: str) -> OperatorRun | None:
    """Load an OperatorRun by id."""
    ...

def list_operator_runs(
    self,
    state: OperatorRunState | None = None,
    operator_name: str | None = None,
    limit: int = 100,
) -> list[OperatorRun]:
    """List OperatorRuns, optionally filtered by state and/or operator name."""
    ...
```

4. **Update `_init_schema`** to create the `operator_runs` table (idempotent, IF NOT EXISTS). Do not modify the existing `runs` table's schema.

5. **Use `_ensure_column` pattern** for any future additions to `operator_runs` (consistent with the registry's existing additive-migration discipline).

### Item I — Lineage / Checks tables: FK question

The existing `checks` and `lineage` tables have foreign keys `FOREIGN KEY (run_id) REFERENCES runs(id)`. New OperatorRuns won't satisfy that FK because their ids live in `operator_runs`, not `runs`.

**Resolution**: Relax the FK constraint at the schema level. The `run_id` column in `checks` and `lineage` becomes a logical reference that can point at either `runs.id` (legacy) or `operator_runs.id` (new). DuckDB enforces FKs only at table-create time for `FOREIGN KEY` declarations; the simplest path is to **drop and recreate `checks` and `lineage` without the `run_id` FK constraint**, retaining the column as a plain VARCHAR. This is a one-time schema migration.

Implementation:

```python
# In _init_schema, after the table-creation block:
self._migrate_drop_run_fk(conn, "checks")
self._migrate_drop_run_fk(conn, "lineage")
```

Where `_migrate_drop_run_fk` inspects the table for the FK constraint and rebuilds the table without it (CREATE NEW, INSERT FROM OLD, DROP OLD, RENAME NEW). The migration is idempotent: if the FK is already gone, the helper is a no-op.

If this proves heavier than expected (e.g., DuckDB FK introspection is painful), the lighter alternative is a single one-shot SQL migration script invoked from `_init_schema` that conditionally rebuilds the tables. Use whichever lands cleanest in your judgment; document the choice.

### Item J — Tests

#### J.1 — Update existing tests

Migrate the following tests to use `OperatorRun` / `.state` / Literal strings instead of `RunRecord` / `.status` / `RunStatus`:

- `tests/pressure_test/test_end_to_end.py` — `.status == RunStatus.COMPLETED` becomes `.state == "completed"`; same for FAILED, etc.
- `tests/pressure_test/test_registry.py` — `list_runs(status=RunStatus.X)` becomes `list_operator_runs(state="x")`. The direct `RunRecord` construction in this file becomes an `OperatorRun` construction with the new required fields.
- `tests/pressure_test/adapter_helpers.py` — `make_invalid_completed_run` and `make_failed_run` become `make_invalid_completed_operator_run` and `make_failed_operator_run`, constructing `OperatorRun` with the new required fields. Update callers in the test files that import them.

The legacy `RunRecord` / `RunStatus` tests can be deleted **only if no test still constructs RunRecord directly**. If any test relies on the legacy registry read path, keep it green by leaving its RunRecord-construction inline and assertions on `.status`.

#### J.2 — New unit tests at `tests/pressure_test/test_operator_run.py`

Cover the new surface:

- **Identity stability**: same inputs → same id; different inputs → different ids; covers each ID-derivation input field changing.
- **operator_spec_hash stability**: same OperatorSpec → same hash; changing any spec field → different hash.
- **params_hash stability**: equivalent params (re-ordered keys) → same hash; different params → different hash.
- **State transitions**: legal transitions succeed (`pending → running → completed`; `pending → failed`; `running → failed`; `running → cancelled`); illegal transitions raise `OperatorRunStateError`.
- **Two-phase frozen-pin**: attempting to mutate any field after construction raises `FrozenInstanceError` (this is automatic via `frozen=True` but verify the test catches the case).
- **seed_value invariants**: stochastic operator with seed_value=None at construction raises; non-stochastic with non-None seed_value raises; stochastic with valid seed value populates correctly.
- **Retry invariants**: `retried_from=None, retry_index=0` valid; `retried_from=X, retry_index=N (N>=1)` valid; `retried_from=None, retry_index!=0` raises; `retried_from=X, retry_index=0` raises.
- **`derive_seed_value` correctness**: returns None for non-stochastic; returns the seed for stochastic; raises when stochastic but seed missing or wrong type.
- **`LocalExecutor.submit` end-to-end**: a deterministic operator with valid inputs produces a completed OperatorRun with stable id on re-submit at the same submitted_at; a validation failure produces a `pending → failed` transition; an execution exception produces a `running → failed` transition.

#### J.3 — New unit tests at `tests/pressure_test/test_registry_operator_runs.py`

Cover the new registry surface:

- `save_operator_run` followed by `get_operator_run` round-trips an OperatorRun losslessly.
- `list_operator_runs(state="completed")` filters correctly.
- `list_operator_runs(operator_name="d8_flow_direction")` filters correctly.
- Saving an OperatorRun whose `output.artifact` is a new Artifact also saves the Artifact and the lineage edges + checks (parallel to `save_run` semantics).
- The legacy `save_run` / `get_run` / `list_runs` paths still work for RunRecord (no regression).
- The `checks` and `lineage` tables accept both legacy `runs.id` and new `operator_runs.id` values without FK violation (Item I's FK migration verification).

All new and existing tests at `tests/pressure_test/` must run green (baseline: 1949 passing after Brief 3). The expected net change is +30–60 new tests minus the count of legacy `.status`-using assertions that get rewritten in place.

## Constraints

- **Write only inside the write scope below.** Any write outside is an integration failure.
- **Do not modify `/Users/jakegearon/projects/watershed/`.** SOPs, CANON, lineage entries are the Watermaster's domain.
- **Do not delete `RunRecord` or `RunStatus`.** They stay as deprecated legacy in `executor.py` for one cycle. A future Brief removes them once no caller remains.
- **Do not modify the legacy `runs` table's schema.** Pre-existing uuid4 records are frozen-pinned per CANON Article XV and the SOP's escalate clause.
- **Do not modify any Operator's `execute()` business logic.** This Brief touches only the run record, not the operator surface.
- **Do not modify Brief 1, 2, or 3 work.** OperatorSpec / OperatorResult / Artifact.id derivation stays as is.
- **Do not invent new state values.** The five-state lifecycle is canonical: `pending | running | completed | failed | cancelled`.
- **Do not promote operational telemetry (subprocess pid, SLURM job id) to typed OperatorRun fields.** `executor_meta` is the untyped escape hatch per the SOP. Promoting requires preflight.
- **Do not introduce a fork lineage on OperatorRun.** OperatorRun has retry only; fork is dispatch-side (per dispatch-run-shape v1).
- **Do not bypass the `dispatched_by` requirement.** Default to `"watermaster:unknown"` if the caller doesn't supply one, but never leave it empty or None.
- **If you see useful adjacent work outside the scope, flag it in the return rather than writing it.** (Repeating from prior Briefs as discipline.)
- **One coherent change set.**

## Write scope

```
/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/operator_run.py        (new)
/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/executor.py            (Protocol return types; RunRecord deprecation docstring)
/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/executors/local.py     (LocalExecutor rewrite)
/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/__init__.py            (exports)
/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/artifact.py            (rename _identity_digest → identity_digest if Item B's rename path is chosen)
/Users/jakegearon/projects/quarry/packages/quarry-registry/src/quarry_registry/registry.py    (operator_runs table + methods; FK migration on checks/lineage)
/Users/jakegearon/projects/quarry/tests/pressure_test/test_operator_run.py                    (new)
/Users/jakegearon/projects/quarry/tests/pressure_test/test_registry_operator_runs.py          (new)
/Users/jakegearon/projects/quarry/tests/pressure_test/test_end_to_end.py                      (updates)
/Users/jakegearon/projects/quarry/tests/pressure_test/test_registry.py                        (updates)
/Users/jakegearon/projects/quarry/tests/pressure_test/adapter_helpers.py                      (updates)
/Users/jakegearon/projects/quarry/packages/quarry-cli/src/quarry_cli/main.py                  (only if CLI's RunRecord type hints need updating to OperatorRun; minimal touch)
```

You may also read freely anywhere in `/Users/jakegearon/projects/quarry/` and `/Users/jakegearon/projects/watershed/`.

## Out of scope

- Migration of pre-existing uuid4-id `RunRecord` rows in the `runs` table into the `operator_runs` table. Per the SOP, those are frozen-pinned.
- Removal of `RunRecord` / `RunStatus` from `executor.py`. They stay one cycle.
- Bedrock pointer canonicalization integration (bedrock doesn't exist yet; `canonical_uri` in `artifact.py` is the interim home).
- New event types for OperatorRun lifecycle (operator_run_dispatched, operator_run_completed). The event-emission SOP names the discipline; minting concrete events is a separate Brief.
- Closing the 8 dual-residence gaps flagged in Brief 2.
- The bundler-hash-composition gap (dgov-side; not in quarry scope).
- A CANON article naming the three-agent-class structure (separate preflight, not this Brief).
- Any change to OperatorSpec, OperatorResult, Artifact, or any Brief 1/2/3 type or helper. Item B's rename of `_identity_digest → identity_digest` is the lone exception (a minor visibility tweak, no semantics change).
- Promoting `dispatched_by` to a union with DispatchRunId. SOP escalate territory; defer.

## Verify (before submitting)

- `from quarry_core import OperatorRun` works from a fresh Python session.
- `LocalExecutor().submit(operator, inputs, params)` returns an `OperatorRun`, not a `RunRecord`.
- A deterministic operator submitted twice with the same operator-spec-hash + input_ids + params + executor_name + retried_from=None + retry_index=0 + the same `submitted_at` yields the same `OperatorRun.id`. (Two real submits at different real timestamps yield different ids — that's correct per the SOP.)
- A stochastic operator submitted twice with different `seed_value` yields different `OperatorRun.id`.
- A stochastic operator missing `seed_param` value in its params raises a typed error at construction.
- A deterministic operator with a non-None `seed_value` passed at construction raises a typed error.
- All five state-transition methods raise `OperatorRunStateError` when called from an illegal source state.
- `dataclasses.replace` (or the chosen clone mechanism) preserves frozen-ness — the returned OperatorRun is a different instance from the input.
- `derive_operator_spec_hash` is stable across re-runs of the same operator's `spec` property; differs when any OperatorSpec field changes.
- `derive_params_hash({"b": 2, "a": 1})` and `derive_params_hash({"a": 1, "b": 2})` are equal.
- The full pressure_test suite passes. Brief 1 + 2 + 3 surface tests (`test_operator_shape.py`, `test_dual_residence.py`, `test_check_*.py`, `test_artifact_id_*.py`, `test_canonical_*.py`, `test_connector_artifact_id_stability.py`) remain green.
- `registry.save_operator_run(record)` followed by `registry.get_operator_run(record.id)` round-trips losslessly.
- Legacy `registry.save_run(legacy_record)` / `registry.get_run(legacy_id)` still work (no regression on the deprecated path).
- The `checks` and `lineage` tables accept both legacy `runs.id` and new `operator_runs.id` values without FK violation.
- No file outside the write scope has been modified.

## Return shape

Return a chat message structured as:

1. **Summary** — one paragraph naming what landed.
2. **Item-by-item** — A through J, each with: what was changed, file paths touched, any judgment calls, any unexpected findings.
3. **Key technical decisions** — your choice on:
   - The `dataclasses.replace` mechanism for the `frozen=True, init=False` shape (works directly, or required a custom `_clone`).
   - The `_identity_digest → identity_digest` rename (you renamed it, or kept it private and added a public re-export).
   - The FK migration on `checks` / `lineage` (table-rebuild via `_migrate_drop_run_fk`, or one-shot SQL migration).
4. **Migration coverage** — exactly which legacy tests were rewritten in place, which were preserved for the legacy RunRecord read path, and which were deleted.
5. **Flag list** — every place where the migration discipline can't proceed cleanly (escalate territory), with one-line context.
6. **Test results** — passing/failing counts plus a list of new/modified test files with one-line descriptions.

The Watermaster will integrate your return: verify writes are within scope (with explicit prior-Brief-baseline awareness so the verification doesn't conflate Brief 1+2+3's writes with Brief 4's), audit the flag list, and either commit the work as-is or send a follow-up Brief.

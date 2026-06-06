---
name: operator-shape
title: Operator Shape
summary: The discipline a typed Operator carries — Protocol surface, OperatorSpec static declarations including determinism class and tiling, OperatorParams base, OperatorResult and truth-source labeling, declared-checks with dual-residence Checks, registry, and the tiling-below-Operator layering.
applies_to: [operator, operatorspec, operatorparams, operatorresult, check, declared_checks, determinism_class, tiling, backend, registry, flume]
priority: must
version: 1
authored_by: Watermaster Pool
inscribed: 2026-05-10
canon_anchor: Articles II, III, IV, IX, X, XV
---

## When

- writing a new Operator in flume (or quarry-operators prior to lift)
- modifying an existing Operator's Protocol surface (spec, params, result, declared checks)
- declaring or rotating a Check that an Operator references in `declared_checks()`
- selecting or implementing a backend that an Operator delegates to (tiled, monolithic, reconciled, or otherwise)
- registering an Operator in flume's operator-registry
- defining or revising an OperatorRun, Lineage, or downstream record that references an Operator
- migrating quarry-operators or hydrops surfaces into flume

## Do

- represent every Operator as a runtime-checkable Protocol carrying: `name: str` (property), `spec: OperatorSpec` (property), `validate_inputs(inputs: list[Artifact], params: OperatorParams) -> list[str]`, `execute(inputs: list[Artifact], params: OperatorParams) -> OperatorResult`, `declared_checks() -> list[str]`; when `spec.determinism_class == "stable"`, additionally expose `semantic_equality(a: Artifact, b: Artifact) -> bool` per `sops/determinism-class.md`
- represent every `OperatorSpec` as a frozen dataclass carrying: `input_types: tuple[ArtifactType, ...]`, `output_type: ArtifactType`, `min_inputs: int`, `max_inputs: int` (`-1` for unbounded), `resource_scale: ResourceScale`, `determinism_class: Literal["deterministic", "stable", "stochastic"]`, `supports_tiling: bool`, `tile_reconciliation_kind: str` (e.g., `"seam-band-merge"`, `"full-grid-recompute"`, `"none"`), `seed_param: str | None`
- declare `determinism_class` per `sops/determinism-class.md`; OperatorSpec is the canonical home of the declaration
- when `determinism_class == "stochastic"`, set `seed_param` to the name of the OperatorParams field that carries the seed; otherwise leave `seed_param = None`
- represent every `OperatorParams` as a frozen dataclass subclassing `OperatorParams`; one Params class per Operator
- represent every `OperatorResult` as a dataclass carrying: `artifact: Artifact`, `checks: list[CheckResult]`, `warnings: list[str]`, `timing_seconds: float | None`, `truth_source_by_field: Mapping[str, str] | None`, `metadata: dict[str, Any]`
- populate `truth_source_by_field` per `sops/truth-source-labeling.md` for every Operator whose output participates in comparison; keys are field names of the output (`"elevation"`, `"flow_direction"`, etc.), values are one of `backend_native | reference_synthesized | diagnostic_only`
- treat `OperatorResult.metadata` as operator-extension context only, never authoritative for typed fields, per `sops/data-contracts.md`
- set the output Artifact's `Lineage.operation` to the Operator's `name`; lineage discipline otherwise per `sops/data-contracts.md`
- represent every Check as a runtime-checkable Protocol carrying: `name: str` (property), `description: str` (property), `run(artifact: Artifact) -> CheckResult`
- maintain dual-residence for every check named in `declared_checks()`: the same name appears both inline within the Operator's `execute()` flow (run during execution against in-memory state) and as a standalone Check class implementing the Protocol (run independently against any Artifact); both implementations produce `CheckResult`s with the same `check_name`
- treat tile reconciliation as a backend concern below the Operator: the Operator declares `supports_tiling` and `tile_reconciliation_kind`; the backend (the engine that performs the computation) decides whether to tile and how to stitch
- select a backend for an Operator at execution time through a separate backend-resolution surface; the Operator interface does not embed tiling logic
- register every Operator in flume's operator-registry under its `name`; the registry's name is the canonical lookup; the registered name equals the Operator instance's `name` property
- treat the Operator's `name` as stable: a name change requires a new Operator (a new registry entry, a new Lineage value for the operation field, and the prior name retired)
- raise a typed `ValidationError` from the executor when `validate_inputs` returns non-empty; `validate_inputs` itself returns the list of errors rather than raising

## Do Not

- omit `determinism_class` from an OperatorSpec; absence is not a default
- omit `supports_tiling` from an OperatorSpec; operators that genuinely cannot be tiled declare `supports_tiling = False` and `tile_reconciliation_kind = "none"`
- declare `supports_tiling = True` with `tile_reconciliation_kind = "none"`; the kind is empty only when tiling is unsupported
- declare `semantic_equality` on an Operator whose `determinism_class != "stable"`
- declare `seed_param` non-`None` on an Operator whose `determinism_class != "stochastic"`
- accept untyped data anywhere in the Operator surface; inputs are `list[Artifact]`, params are an `OperatorParams` subclass, output is `OperatorResult`
- copy spatial or temporal metadata from input Artifacts to the output Artifact per `sops/data-contracts.md`
- list a name in `declared_checks()` without a registered standalone Check matching that name
- embed tiling logic in the Operator's `execute()` flow; tiling lives in the backend
- bypass the operator-registry by importing an Operator class directly when name-based dispatch is in scope
- mutate `OperatorSpec`, `OperatorParams`, or the Artifact produced by `execute()` after construction; the Operator's outputs are frozen at construction per CANON Article XV
- write `truth_source_by_field` entries with values outside `backend_native | reference_synthesized | diagnostic_only`
- carry kernel TaskState values or distributary lifecycle states on an OperatorResult; those are dispatch-chain concerns, not operator concerns
- have an Operator accept a `str | Path | URI` as a direct input; that is a Connector role per CANON Article III

## Verify

- every Operator in flume's registry passes `isinstance(op, Operator)` against the Protocol
- every Operator's `spec.determinism_class` is one of `deterministic | stable | stochastic`
- every Operator's `spec.supports_tiling` is a `bool` and `spec.tile_reconciliation_kind` is non-empty
- every Operator whose `spec.determinism_class == "stable"` exposes a callable `semantic_equality(a, b) -> bool`
- every Operator whose `spec.determinism_class == "stochastic"` has `spec.seed_param` matching a field on its OperatorParams class
- every name in `Operator.declared_checks()` resolves to a standalone Check class whose `name` property equals the declared name
- every `OperatorResult.artifact.lineage.operation` equals the Operator's `name`
- every `OperatorResult` produced by an Operator whose outputs participate in comparison carries a non-`None` `truth_source_by_field`; every value is one of the three truth-source classes
- the operator-registry returns the same Operator class for a given name across re-imports; name uniqueness holds across the registry
- a query for "all Operators with `determinism_class = stable`" returns the expected set; the same holds for `supports_tiling = True`
- a tiled execution of an Operator whose `supports_tiling = True` produces an `OperatorResult` indistinguishable in typed shape from a monolithic execution of the same Operator; only the backend's internals differ

## Escalate

- if an Operator legitimately needs to accept untyped input (a string, path, or URI) as part of its surface — that is a Connector role per CANON Article III; propose decomposition into Connector + Operator, not an exception
- if a Check legitimately cannot satisfy the dual-residence pattern (e.g., requires in-memory state not recoverable from the Artifact's backing) — propose either lifting that state into a typed Artifact field or restricting the check to operator-internal use; do not weaken the dual-residence rule
- if existing quarry-operators implementations have `declared_checks()` entries without matching standalone Checks (partial dual-residence today) — the lift into flume is the time to close the gap; do not lift partial dual-residence into flume canonical state
- if an Operator legitimately straddles determinism classes (e.g., float-deterministic on one architecture, float-stable across architectures) — declare the weaker class per `sops/determinism-class.md` and document the architecture-specific stronger guarantee in operator notes
- if tile reconciliation cannot live below the Operator (e.g., the algorithm fundamentally depends on tile-aware logic at the algorithm level rather than the data level) — argue first that the algorithm is two operators (a tile-local one and a global one) rather than one tile-aware operator
- if `tile_reconciliation_kind` cannot describe a class of reconciliation strategy in the enumerated typed-string vocabulary — propose typed extension via preflight; do not freelance a new string
- if an Operator's `truth_source_by_field` cannot be populated because the comparable output's field structure is not stable — fix the output's typed shape rather than weakening truth-source labeling
- if a new Operator class needs a sixth Protocol method (beyond `name`, `spec`, `validate_inputs`, `execute`, `declared_checks`, and conditional `semantic_equality`) — propose extension to the Operator Protocol via preflight
- if the operator-registry needs to support multiple Operator versions under one name — that is a versioning concern; propose either schema-versioning-style integer versions per `sops/schema-versioning.md` or distinct names per version; do not collapse them under a single name
- if hydrops's `BackendEngineProtocol` shape needs to be lifted into flume contracts before this SOP is fully exercised — that lift is its own preflight, parallel to this one, naming the backend layer as below-Operator
- if a class of Operator produces an output that is not a typed Artifact (e.g., a streaming sequence, a side effect on a remote system) — propose a new typed output shape rather than weakening `OperatorResult.artifact`
- if an OperatorRun (≅ today's `RunRecord`) shape needs to be canonicalized — that is a separate SOP parallel to `dispatch-run-shape`; do not fold OperatorRun discipline into this Operator-Protocol SOP

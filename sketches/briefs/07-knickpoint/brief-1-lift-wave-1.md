# Engineer Brief — Lift Wave 1 (quarry-core type-surface alignment with operator-shape v1)

**engineer_model**: `codex-gpt-5` (the seated Codex instance the Source is using)
**source_utterance** (verbatim, concatenated):
> "lets produce a prompt for the engineer to do some work"
>
> "we can give multiple requests in a row and bvatch them i will be using codex. let it write files"

**compiled_by**: Watermaster Knickpoint
**compiled_at**: 2026-05-11
**state**: integrated (drafted 2026-05-11 → sent 2026-05-11 → returned 2026-05-11 → integrated 2026-05-11)
**supersedes**: none
**expected_return_shape**: executed file writes within the write scope below, plus a chat return summarizing each item (A–G), the audit findings (item F), and any per-operator classification calls that were judgment calls rather than obvious reads.

---

## Read these before starting

You are an external Engineer consulted by the Watermaster of a research lab called *watershed*. You read only this Brief. You do not see the conversation that produced it. Before writing any code, read the following files in order — they are the discipline this Brief implements, not aspiration:

1. `/Users/jakegearon/projects/watershed/CANON.md` — the lab's constitutional articles (I–XV). Article II (one canonical writer per module), Article III (untyped reality becomes typed only at the rim), Article X (operator invariants travel with their operators), Article XV (typed records are frozen-pinned at lifecycle transitions; in-place edits are forbidden).
2. `/Users/jakegearon/projects/watershed/sops/operator-shape.md` v1 — the SOP this Brief implements in code. Read both the body and the Escalate clauses.
3. `/Users/jakegearon/projects/watershed/sops/determinism-class.md` v1 — defines `deterministic | stable | stochastic`; the canonical home of the declaration is now `OperatorSpec` per operator-shape v1.
4. `/Users/jakegearon/projects/watershed/sops/truth-source-labeling.md` v2 — defines `backend_native | reference_synthesized | diagnostic_only`; OperatorResult carries `truth_source_by_field` per operator-shape v1.
5. `/Users/jakegearon/projects/watershed/sops/data-contracts.md` v2 — the Artifact-level discipline, including the three-state temporal contract that the `Artifact.with_check` bug (item D below) silently violates.

The vocabulary is fluvial because the science is fluvial — *quarry* is the boundary module that owns the untyped→typed crossing; *flume* is where typed operators do scientific work; *bedrock* is canonical data + policy + schemas. Today's repo layout is mid-migration: today's `quarry-core` already owns the typed Artifact/Operator/Check surfaces that will lift into `shared/` later. This Brief implements operator-shape v1 against today's quarry-core; the lift into shared/ is a later, separate Brief.

## What you are doing

Aligning the operator-side type surface in `quarry-core` and `quarry-operators` with the discipline named in `operator-shape.md` v1 and the SOPs it anchors. This is the first wave of the flume lift. Out-of-scope items (named explicitly below) belong to subsequent Briefs.

The package layout is:

- `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/`
  - `operator.py` — `OperatorSpec`, `OperatorResult`, `OperatorParams`, `Operator` Protocol, `ResourceScale`, `ArtifactType`
  - `artifact.py` — `Artifact` (frozen dataclass)
  - `check.py` — `Check` Protocol plus concrete `CRSValid`, `ExtentSane`, `BackingStoreAccessible`
  - `executor.py` — `Executor` Protocol and the `RunRecord` lifecycle (RunRecord is **out of scope** for this Brief; that lift is operator-run-shape v1's territory in a later Brief)
  - `executors/local.py` — `LocalExecutor.submit()` mutates `result.timing_seconds` after construction; that's part of item C
- `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/`
  - `registry.py` — lazy importlib registry of 16 Operators (the `_REGISTRY` tuple + `OPERATOR_NAMES`)
  - per-operator files (`d8_flow_direction.py`, `aspect.py`, etc.) — each declares an Operator class with a class-level `spec: OperatorSpec` or constructs one in `__init__`
  - `checks.py` — standalone Check classes (some, not all, of the names declared in `declared_checks()`)
- `/Users/jakegearon/projects/quarry/tests/pressure_test/` — 62 `test_*.py` files at the repo root

## Items

### Item A — Extend `OperatorSpec` per operator-shape v1

In `quarry-core/.../operator.py`, add four new fields to the `OperatorSpec` frozen dataclass:

- `determinism_class: Literal["deterministic", "stable", "stochastic"]` — **required, no default**. Per `determinism-class.md` "absence is not a default." Every Operator must declare this explicitly; item E propagates this to all 16 existing Operators in the same Brief so the codebase compiles.
- `supports_tiling: bool = False` — conservative default; the SOP requires explicit declaration but `False` is the conservative declaration.
- `tile_reconciliation_kind: str = "none"` — conservative default; must be non-`"none"` only when `supports_tiling = True`.
- `seed_param: str | None = None` — only set when `determinism_class == "stochastic"`.

Add a `__post_init__` to `OperatorSpec` that enforces the cross-field invariants:

- When `supports_tiling is True`, `tile_reconciliation_kind != "none"` — raise `ValueError` otherwise.
- When `supports_tiling is False`, `tile_reconciliation_kind == "none"` — raise `ValueError` otherwise.
- When `determinism_class == "stochastic"`, `seed_param is not None` and is a non-empty string — raise `ValueError` otherwise.
- When `determinism_class != "stochastic"`, `seed_param is None` — raise `ValueError` otherwise.

The dataclass stays `@dataclass(frozen=True)`.

### Item B — Extend the `Operator` Protocol per operator-shape v1

In the same `operator.py`, the `Operator` Protocol currently declares: `name` property, `spec` property, `validate_inputs`, `execute`, `declared_checks`. Add a conditional method:

- `semantic_equality(a: Artifact, b: Artifact) -> bool` — required iff `self.spec.determinism_class == "stable"`. The Protocol type system can't express conditional members, so the Protocol declares `semantic_equality` as an optional method (use `@runtime_checkable` semantics; document the conditionality in the Protocol's docstring and add a module-level helper `assert_operator_conforms(op: Operator) -> None` that raises a typed `OperatorConformanceError` when `op.spec.determinism_class == "stable"` but `op` lacks a callable `semantic_equality`).
- Where Operators are registered (the operator-registry's load path in `quarry-operators/.../registry.py`), call `assert_operator_conforms` at registration time so invalid Operators fail loudly at registry construction, not at first comparison.

The Protocol stays `@runtime_checkable`.

### Item C — `OperatorResult` frozen + `truth_source_by_field` + executor timing

In `operator.py`, today `OperatorResult` is `@dataclass` (not frozen). Per CANON Article XV and operator-shape v1 ("the OperatorResult contents are frozen at construction"):

- Make `OperatorResult` `@dataclass(frozen=True)`.
- Add `truth_source_by_field: Mapping[str, str] | None = None` field per operator-shape v1's "OperatorResult carries `truth_source_by_field` per `truth-source-labeling.md`."
- The existing field set (`artifact`, `checks`, `warnings`, `timing_seconds`, `metadata`) stays; `checks: list[CheckResult]` and `warnings: list[str]` and `metadata: dict[str, Any]` can keep their mutable list/dict types if Python's frozen dataclass allows it — but mutating them after construction is now a discipline violation, not a routine. If clean, convert `checks` and `warnings` to `tuple[CheckResult, ...]` and `tuple[str, ...]` respectively; leave `metadata` as `Mapping[str, Any]` typed as immutable.
- Then in `executors/local.py`, `LocalExecutor.submit()` currently does:
  ```python
  result = operator.execute(inputs, params)
  elapsed = perf_counter() - t0
  record.output = result
  result.timing_seconds = elapsed   # <-- this becomes impossible with frozen
  ```
  Restructure to: after the operator's call returns, wrap the result with `dataclasses.replace(result, timing_seconds=elapsed)` (frozen dataclasses support `replace`), then set `record.output` to the wrapped result. The operator continues to return its OperatorResult with `timing_seconds = None`; the executor produces the final, timing-bearing OperatorResult.

`record.output = ...` and `record.status = ...` and `record.completed_at = ...` are mutations of `RunRecord`, which is **out of scope** (RunRecord's frozen-pinning belongs to operator-run-shape v1's lift in a later Brief). Leave RunRecord mutable for now.

### Item D — Fix the `Artifact.with_check` temporal-drop bug

In `quarry-core/.../artifact.py`, the current `with_check` method is:

```python
def with_check(self, result: CheckResult) -> Artifact:
    """Return a new artifact with an additional check result."""
    new_checks = (*self.checks, result)
    return Artifact(
        id=self.id,
        type=self.type,
        name=self.name,
        backing=self.backing,
        spatial=self.spatial,
        lineage=self.lineage,
        checks=new_checks,
        metadata=self.metadata,
        created_at=self.created_at,
    )
```

The `temporal` field is not passed; it defaults to `None`, silently dropping any `TemporalDescriptor` on every check addition. Fix by adding `temporal=self.temporal,` to the constructor call. The cleaner refactor is `return dataclasses.replace(self, checks=new_checks)` — use that if `Artifact` is suitable (it should be; it's a frozen dataclass).

While editing this file, audit every other method on `Artifact` that constructs a new `Artifact` (look for `Artifact(...)` constructor calls inside the class). For each, verify that all fields are passed. Report any other silently-dropped field in the chat return.

### Item E — Propagate `determinism_class` declarations to all 16 Operators

After item A makes `determinism_class` required, every existing OperatorSpec construction breaks at instantiation. The fix is to add the explicit declaration to each.

For each of the 16 Operator classes in `quarry-operators` (`AspectOperator`, `BuildCOGOperator`, `ClipRasterOperator`, `D8FlowDirectionOperator`, `FillDepressionsOperator`, `FlowAccumulationOperator`, `GeocodeSLCOperator`, `HillshadeOperator`, `RasterizeVectorOperator`, `ReprojectOperator`, `SampleRasterOperator`, `SLCCalibrationOperator`, `SlopeOperator`, `SpatialJoinOperator`, `WaterElevationMosaicOperator`, `ZonalStatsOperator`):

1. Examine the implementation (`execute()` body, any underlying library calls, any tie-breaking or floating-point reductions).
2. Decide the correct `determinism_class` per `determinism-class.md`'s definitions:
   - `deterministic` — same inputs + same params + same code produce byte-identical output across every executor.
   - `stable` — semantically equivalent output per a declared `semantic_equality`, but bytes may differ (parallel float-ordering, embedded timestamps in output headers, library-version-sensitive reductions).
   - `stochastic` — output depends on a seed; `seed_param` names which OperatorParams field carries the seed.
3. Add the explicit declaration to that operator's `OperatorSpec` construction.
4. For `supports_tiling`: declare `True` only when the operator's `execute()` is genuinely tile-aware today; otherwise declare `False` (with `tile_reconciliation_kind="none"`). The SOP's escalate clause names tiled execution as a backend concern below the Operator; an Operator that doesn't tile today is `supports_tiling=False`.
5. For `seed_param`: set only when `determinism_class == "stochastic"`.

For any operator where the class is **not obvious** (e.g., reduction order may or may not affect the output bytes; the implementation uses a library with version-sensitive output), declare the **weaker** class (`stable` over `deterministic`, `stochastic` over `stable`) and add a `# determinism: judgment call — <reason>` comment near the spec construction. List every such judgment call in the chat return so the Watermaster can review.

For `stable` operators, item B requires a `semantic_equality(a, b) -> bool` method on the Operator class. If you classify any operator as `stable`, also implement a reasonable `semantic_equality` for it: for raster outputs, byte-equality on the data array plus equality on the typed metadata (CRS, extent, resolution) is a reasonable default — implement that as `_default_raster_semantic_equality` in a module helper and reuse it across stable raster operators. If you classify an operator as `stable` but cannot write a defensible `semantic_equality` without further input, declare it `stable` with a placeholder `semantic_equality` that raises `NotImplementedError("semantic_equality for <op_name> requires Watermaster review")` and flag it in the chat return.

### Item F — Audit `declared_checks()` dual-residence coverage

For each of the 16 Operators, list every name returned by `declared_checks()`. For each name, report whether there is a standalone `Check` class in `quarry-operators/.../checks.py` (or elsewhere in `quarry_operators`) with a `name` property that matches.

Do **not** write code to close any gaps in this item. The closure is a later Brief's work and depends on the audit findings.

Report findings in the chat return as a table:

```
| operator | declared_check name | standalone Check class? |
| -------- | ------------------- | ----------------------- |
| ...      | ...                 | yes (class CheckXyz)   |
| ...      | ...                 | no                      |
```

### Item G — Update tests to match the new surfaces

Run the existing test suite at `/Users/jakegearon/projects/quarry/tests/pressure_test/` to identify breakages introduced by items A–E. Update only what's necessary to make tests pass against the new surfaces; do not refactor tests beyond field-surface changes.

Common updates expected:

- Any test that constructs an `OperatorSpec` literal will need `determinism_class=` added (and possibly `supports_tiling`, `tile_reconciliation_kind`, `seed_param` if it's testing edge cases).
- Any test that constructs `OperatorResult` and then mutates fields will need to use `dataclasses.replace`.
- Any test that constructs an Artifact with a `TemporalDescriptor` and asserts that `with_check` preserves it (if any) will now pass; if such an assertion previously was missing, do not add one — that's discipline work, not a Brief-level concern.

Report the list of test files modified in the chat return, with a one-line description per file. If a test reveals a deeper integration issue you cannot resolve within the write scope, leave it failing and flag it in the chat return — do not widen the write scope to fix it.

## Constraints

- **Write only inside the write scope below.** Any write outside is an integration failure.
- **Do not modify any file under `/Users/jakegearon/projects/watershed/`.** SOPs, CANON, and lineage entries are the Watermaster's domain. If you observe that this Brief contradicts a SOP, stop and report the contradiction in the chat return — do not silently work around the SOP.
- **Do not touch `RunRecord` in `executor.py` beyond what item C requires** (which is just: stop letting LocalExecutor mutate `result.timing_seconds`, by restructuring the wrap step). `RunRecord`'s own lifecycle, identity, and frozen-pinning belong to operator-run-shape v1 in a later Brief.
- **Do not touch `Artifact.id`'s identity generation.** Today it's a `uuid4` default; per `data-contracts.md` v2 it should be content-derived. The fix belongs to a later Brief.
- **Do not introduce new SOPs, new CANON articles, or new module-level abstractions.** This Brief implements existing discipline in code.
- **Do not propagate to other repos.** Codex may read from `/Users/jakegearon/projects/dgov`, `/Users/jakegearon/projects/hydrops`, etc. for context, but must not write to them.
- **Preserve the lab's vocabulary.** Don't rename `Operator`, `OperatorSpec`, `OperatorResult`, `Artifact`, `Check`, `Lineage`, etc. The names are load-bearing.
- **One coherent change set.** Don't bundle in unrelated cleanup. If you notice a clearly broken adjacent thing (a typo, a dead import), fix it inline and mention it in the chat return.

## Write scope

```
/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/operator.py
/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/artifact.py
/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/executor.py
/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/executors/local.py
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/**/*.py
/Users/jakegearon/projects/quarry/tests/pressure_test/**/*.py
```

You may also read freely anywhere in `/Users/jakegearon/projects/quarry/` and `/Users/jakegearon/projects/watershed/` for context; reading is unbounded, writing is the scope above.

## Out of scope (defer to subsequent Briefs)

- `RunRecord` → `OperatorRun` migration per `sops/operator-run-shape.md` v1.
- `Artifact.id` content-derivation per `sops/data-contracts.md` v2.
- Dual-residence closure for `declared_checks()` (writes await item F's audit findings).
- Lift of `Artifact`/`Operator`/`OperatorSpec`/`OperatorResult`/`Check`/`Lineage` into a `shared/` package per the lab's eventual module layout.
- `Lineage.schema_version` per `sops/schema-versioning.md` (bedrock doesn't exist yet; not biting).
- Connector materialize-path changes; hydrops integration; dgov boundary work.

## Verify (before submitting)

- `OperatorSpec` has the four new fields; `__post_init__` enforces the four invariants; tests for invalid combinations raise `ValueError`.
- `OperatorResult` is frozen; `LocalExecutor.submit()` no longer mutates `result.timing_seconds` post-construction.
- `Artifact.with_check` preserves `temporal`.
- `assert_operator_conforms(op)` raises `OperatorConformanceError` when a `stable`-classed Operator lacks `semantic_equality`.
- All 16 Operators in `quarry-operators` have explicit `determinism_class` declarations.
- The full test suite at `/Users/jakegearon/projects/quarry/tests/pressure_test/` runs and passes (or the failures are reported with reasoning).
- No file outside the write scope has been modified.

## Return shape

Return a chat message structured as:

1. **Summary** — one paragraph naming what landed and what didn't.
2. **Item-by-item** — A through G, each with: what was changed, file paths touched, any judgment calls (especially for item E's per-operator classifications), any unexpected findings.
3. **Item F audit table** — the dual-residence table as described in item F.
4. **Test results** — passing/failing counts plus a list of any test files modified with one-line descriptions.
5. **Flags for Watermaster review** — anything you marked as a judgment call, anything you couldn't resolve in scope, any contradictions you observed with the SOPs.

The Watermaster will integrate your return: verify writes are within scope, audit the judgment calls, and either commit the work as-is or send a follow-up Brief if revisions are needed. You will not be asked for revisions inside this same Brief — every revision is a new Brief with a `supersedes` link per `engineer-brief.md`.

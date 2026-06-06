# Engineer Brief — Brief 3 (Artifact.id content-derivation per data-contracts v2)

**engineer_model**: `codex-gpt-5` (the seated Codex instance the Source is using; confirm exact identifier at transmission)
**source_utterance** (verbatim, concatenated across the session):
> "lets produce a prompt for the engineer to do some work"
>
> "we can give multiple requests in a row and bvatch them i will be using codex. let it write files"
>
> "okay it landed" (Brief 1 acceptance signal)
>
> [Source approved Brief 2 transmission via the meta-preflight flow; carried Brief 2; reported Codex's return]
>
> "Pushed the Brief 2 watershed record to the public repo. Committed: 1ae4e42 Record brief 2 dual residence closure. Remote is synced: https://github.com/jameshgrn/watershed"

**compiled_by**: Watermaster Knickpoint
**compiled_at**: 2026-05-11
**state**: integrated (drafted 2026-05-11 → sent 2026-05-11 → returned 2026-05-11 → integrated 2026-05-11)
**supersedes**: none
**expected_return_shape**: executed file writes within the write scope below, plus a chat return summarizing each item (A–G), the connector/operator construction sites touched, any case where content-derivation can't proceed for an existing Artifact construction pattern (escalate territory), and the test run results.

---

## Read these before starting

You are an external Engineer consulted by the Watermaster of a research lab called *watershed*. You read only this Brief. You executed Briefs 1 and 2 in prior sessions, both integrated cleanly.

Read the following files first — they are the discipline this Brief implements:

1. `/Users/jakegearon/projects/watershed/CANON.md` — Articles II (one canonical writer), III (untyped reality becomes typed only at the rim), IV (every Artifact carries its lineage), XV (typed records are frozen-pinned at lifecycle transitions).
2. `/Users/jakegearon/projects/watershed/sops/data-contracts.md` v2 — the discipline this Brief is implementing. The relevant clauses:
   - *"treat the Artifact's `id` as the only identity; never identify by path, name, or backing-store URI"*
   - Verify: *"the Artifact's `id` is content-derived and stable across re-materialization of the same source bytes via the same Connector with the same parameters"*
3. `/Users/jakegearon/projects/watershed/sops/pointer-canonicalization.md` v1 — names `bedrock.pointer.canonicalize(uri) -> Pointer` as the rim discipline for URI identity. Bedrock doesn't exist yet, but the discipline's shape (idempotent, equivalence-preserving, distinct-preserving) governs how a `canonical_uri` helper in this Brief should behave.
4. `/Users/jakegearon/projects/watershed/sops/determinism-class.md` v1 — determinism class affects whether operator output identity needs to include a seed.
5. `/Users/jakegearon/projects/watershed/sops/operator-shape.md` v1 — the Operator surface you aligned in Brief 1. Recall: `OperatorResult.artifact.lineage.operation` equals the Operator's `name`.

The lab vocabulary is fluvial. *quarry* is the boundary module; *quarry-core* owns typed Artifact/Operator/Check surfaces; *quarry-connectors* materializes untyped → typed; *quarry-operators* runs typed-input-to-typed-output computations.

## Context — current state

`Artifact` is a frozen dataclass in `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/artifact.py`. Its `id` field defaults to `str(uuid.uuid4())`, with no content-derivation. `Artifact.__post_init__` exists but only freezes `checks` and `metadata`. The `content_hash(path) -> str` helper already exists in the same file and is used by ~22 Connector and Operator sites to populate `BackingStore.content_hash`. The registry (`quarry-registry`) treats `Artifact.id` as a canonical primary-key string and does no rehashing.

The result today: every materialization of the same source file gets a fresh uuid4. Re-running the same Operator on the same input artifacts produces output Artifacts with fresh uuid4 ids. Lineage chains break across re-runs because input_ids in lineage refer to stale uuid4s. The SOP discipline is violated everywhere.

## What you are doing in Brief 3

Move `Artifact.id` from `uuid4` to content-derived identity, with derivation centralized in `Artifact.__post_init__` so the 50+ existing construction sites across 29 Connectors and 16 Operators don't have to be touched individually. The derivation strategy is hybrid based on what's populated on the Artifact at construction time.

## Items

### Item A — Derivation strategies

Mint three derivation functions in `quarry-core/.../artifact.py`. Each takes the relevant inputs and returns a `str` (hex SHA-256 prefixed with the strategy kind so different strategies never collide on the same hex output).

```python
def derive_id_from_source_bytes(content_hash: str) -> str:
    """Identity from the source bytes' SHA-256. Used by Connector eager materializations
    where the backing file's bytes are the canonical content."""

def derive_id_from_provenance(operation: str, input_ids: Sequence[str], params: Mapping[str, Any]) -> str:
    """Identity from operator provenance. Used by Operator outputs: stable+deterministic
    operators all share this strategy because the *intent* of the run, not the output bytes,
    is the artifact's identity (a stable operator's output bytes vary; its artifact identity
    should not)."""

def derive_id_from_source_ref(canonical_backing_uri: str, params: Mapping[str, Any]) -> str:
    """Identity from a canonicalized source reference. Used by Connector lazy materializations
    where no file bytes are available locally (PostGIS lazy, COG LAZY_HANDLE, etc.) but the
    upstream source is uniquely identified by URI + params."""
```

All three should:
- Use `hashlib.sha256` over a canonical UTF-8 byte string.
- Prefix the input bytes with a strategy tag (`b"src:"`, `b"prov:"`, `b"ref:"`) so the three strategies' outputs cannot collide on the same hex output even with adversarial inputs.
- Be pure functions, no side effects.

### Item B — Canonicalization helpers

Mint two helpers in `quarry-core/.../artifact.py`:

```python
def canonical_params(params: Mapping[str, Any]) -> str:
    """Stable string representation of params: key-sorted, JSON-serialized with sorted keys
    at every nesting level, no whitespace. Reject non-JSON-serializable values with a typed
    error. Handles dataclass-style params by converting to dict first."""

def canonical_uri(uri: str) -> str:
    """Stable string representation of a URI: lowercase scheme; lowercase host; strip default
    ports; sort query params; strip fragment; password-strip for credentialed schemes (postgresql,
    s3, etc.). Idempotent, equivalence-preserving, distinct-preserving per pointer-canonicalization
    v1's discipline. This helper is the interim home for what will eventually live at
    `bedrock.pointer.canonicalize(uri)` when bedrock materializes."""
```

`canonical_params` likely needs to walk nested dicts/lists/tuples; for non-JSON-serializable values (datetime, Path, etc.), convert via `str(value)` and document the convention in the docstring. If your survey of operator params shows non-serializable types in use, list them in the chat return.

`canonical_uri` should reuse the password-stripping logic from `quarry-connectors/.../postgis.py`'s `_backing_uri` helper (recon showed it exists). Lift that logic into the new shared `canonical_uri`; PostGIS's local helper can then call the shared one.

### Item C — `Artifact.__post_init__` derivation

Change `Artifact.id`'s type and default:

```python
@dataclass(frozen=True)
class Artifact:
    id: str | None = None   # was: str = field(default_factory=lambda: str(uuid.uuid4()))
    # ... rest of fields unchanged
```

Extend `Artifact.__post_init__` to derive `id` when it is `None`:

```python
def __post_init__(self) -> None:
    object.__setattr__(self, "checks", tuple(self.checks))
    object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))
    if self.id is None:
        object.__setattr__(self, "id", _derive_artifact_id(self))
```

The dispatch function `_derive_artifact_id(artifact)` picks the strategy:

```python
def _derive_artifact_id(artifact: Artifact) -> str:
    """Dispatch to the right derivation strategy based on what's populated."""
    # Operator output: lineage.operation is set (Operator's name per operator-shape v1)
    if artifact.lineage and artifact.lineage.operation and artifact.lineage.input_ids:
        return derive_id_from_provenance(
            artifact.lineage.operation,
            artifact.lineage.input_ids,
            artifact.lineage.params or {},
        )
    # Connector eager: backing.content_hash is set (bytes are the identity)
    if artifact.backing and artifact.backing.content_hash:
        return derive_id_from_source_bytes(artifact.backing.content_hash)
    # Connector lazy: backing.uri is set, no content_hash, lineage.params carries source-ref
    if artifact.backing and artifact.backing.uri and artifact.lineage and artifact.lineage.params:
        return derive_id_from_source_ref(
            canonical_uri(artifact.backing.uri),
            artifact.lineage.params,
        )
    raise ArtifactIdentityError(
        f"Cannot derive Artifact.id: no usable signal "
        f"(backing.content_hash, backing.uri+params, or lineage.operation+input_ids)"
    )
```

Define `ArtifactIdentityError(ValueError)` alongside in the same file.

After `__post_init__` runs, `artifact.id` is always a non-`None` `str`. From the outside, `Artifact.id` is still typed `str | None` but always-`str` at runtime (Python's type narrowing limits make this awkward; document the contract in the docstring: "id is `None` only inside `__init__`; after construction it is always `str`").

Alternative considered: make `id` purely `str` and use a sentinel value like `""`. Rejected because it pollutes the API surface for callers who might pass empty strings accidentally. `None` is the explicit signal for "derive."

### Item D — Connector pass-through

Most Connector materializations already produce Artifacts without setting `id` explicitly — they accept the uuid4 default. After Item C, those construction sites continue to "not pass id" and `__post_init__` derives. Survey the 29 Connector files in `/Users/jakegearon/projects/quarry/packages/quarry-connectors/src/quarry_connectors/` and verify:

1. **Eager Connectors** (those that download/materialize files locally): ensure every `BackingStore` they construct has `content_hash` populated. Recon confirmed most do; flag any that don't.
2. **Lazy Connectors** (LAZY_HANDLE, POSTGIS, etc.): ensure they populate `backing.uri` AND populate `lineage.params` with enough discriminating information that two distinct lazy Artifacts from the same Connector don't derive the same id. The PostGIS lazy path's `lineage.params` should include the canonical URI and the table/query identifier; the COG LAZY_HANDLE's `lineage.params` should include the canonical URI.

For each Connector, the change is small: either no change needed (eager + content_hash already populated), or add the missing `lineage.params` entries for lazy paths. **Do not change the Artifact construction call itself** — let `__post_init__` do the work.

Flag in the chat return any Connector where lazy materialization can't be made content-deriving (no canonical URI, no discriminating params). Those are escalate territory.

### Item E — Operator pass-through

Brief 1 already set `OperatorResult.artifact.lineage.operation` to the Operator's `name` via the operator-shape v1 discipline. Verify (by reading) that each of the 16 Operators in `quarry-operators` constructs its output Artifact's Lineage with:
- `operation = self.name` (or the Operator's class-level name)
- `input_ids = tuple(input.id for input in inputs)` (in input order)
- `params = <the OperatorParams dict>` (key-sorted-canonical at canonical_params time)

If any Operator doesn't set these consistently, fix the Lineage construction in that Operator. **Do not modify the Operator's execute() business logic** beyond the Lineage construction.

For `stochastic` Operators (currently 0 in the registry per Brief 1), `params` would carry the `seed_value`, so the provenance derivation already includes the seed — no extra work needed.

### Item F — Tests

Add tests at `/Users/jakegearon/projects/quarry/tests/pressure_test/`:

- `test_artifact_id_derivation.py` — for each of the three derivation strategies, test:
  - Same inputs → same id (stability).
  - Different inputs → different ids (distinctness).
  - Strategy-tag prefixing prevents cross-strategy collisions.
  - `ArtifactIdentityError` raised when no strategy applies.
  - Idempotence: `derive(x)` returns the same hex on repeat calls.
- `test_canonical_params.py` — key-sorted output for nested dicts/lists; rejects non-serializable; idempotent.
- `test_canonical_uri.py` — strips password from `postgresql://user:pw@host/db`; sorts query params; lowercases scheme/host; idempotent.
- `test_artifact_id_post_init.py` — construct an Artifact without passing id; verify `__post_init__` derives correctly for each strategy; verify `ArtifactIdentityError` raised when signals insufficient.
- `test_connector_artifact_id_stability.py` — pick 2-3 Connectors (LocalFile eager, COG eager, PostGIS lazy if test fixtures permit) and verify re-materialization of the same source produces the same Artifact.id.

The full pressure_test suite must continue to pass. Brief 1 + Brief 2 surface tests (`test_operator_shape.py`, `test_registry.py`, `test_check_registry.py`, `test_dual_residence.py`, `test_check_*.py`) must remain green.

### Item G — Migration discipline

Per `operator-run-shape.md` v1's pattern for handling pre-existing uuid4 records:

> "if today's quarry-core `RunRecord` uuid4 identity must coexist with content-derived identity during migration — frozen-pin existing uuid4 RunRecords at their quarry-core state and mint new OperatorRuns under this SOP for going-forward executions"

The same pattern applies here. Any existing Artifact records in a persisted registry stay valid under their uuid4 ids — those are frozen-pinned per CANON Article XV. New Artifacts mint with content-derived ids. The registry does no retroactive rehashing.

If the test suite hits any persisted state from prior runs (fixtures with uuid4-based ids), leave it as-is; do not migrate test fixtures retroactively. If you encounter a test that explicitly asserts a specific uuid4-like format on Artifact.id, update the assertion to be format-agnostic (e.g., assert id is a non-empty string, not a uuid format).

## Constraints

- **Write only inside the write scope below.** Any write outside is an integration failure.
- **Do not modify `/Users/jakegearon/projects/watershed/`.** SOPs, CANON, lineage entries are the Watermaster's domain.
- **Do not modify any Operator's `execute()` business logic.** Item E only touches the Lineage construction inside execute(), not the computation itself.
- **Do not modify the registry's SQL schema.** The registry already treats Artifact.id as an opaque primary-key string; no schema change is needed.
- **Do not invent a fourth derivation strategy.** The three strategies cover Connector eager, Connector lazy, and Operator output. If a construction site doesn't fit any of the three, flag and stop — escalate territory.
- **Do not delete the `content_hash(path)` helper.** It's still used by BackingStore population.
- **Preserve the lab's vocabulary** (Artifact, BackingStore, Lineage, Connector, Operator).
- **If you see useful adjacent work outside the scope, flag it in the return rather than writing it.** (Repeating from prior Briefs as discipline.)
- **One coherent change set.**

## Write scope

```
/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/artifact.py
/Users/jakegearon/projects/quarry/packages/quarry-connectors/src/quarry_connectors/*.py
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/*.py
/Users/jakegearon/projects/quarry/tests/pressure_test/test_artifact_id_*.py        (new)
/Users/jakegearon/projects/quarry/tests/pressure_test/test_canonical_*.py          (new)
/Users/jakegearon/projects/quarry/tests/pressure_test/test_connector_artifact_id_stability.py  (new)
/Users/jakegearon/projects/quarry/tests/pressure_test/**/*.py                      (updates to existing tests that hardcode uuid4 expectations)
```

You may also read freely anywhere in `/Users/jakegearon/projects/quarry/` and `/Users/jakegearon/projects/watershed/`.

## Out of scope

- `RunRecord` → `OperatorRun` migration per `operator-run-shape.md` v1 (next Brief).
- Closing the 8 dual-residence gaps flagged in Brief 2 (deferred Watermaster decision).
- `Lineage.schema_version` field (bedrock dependency; bedrock doesn't exist yet).
- Connector materialize-path changes beyond ensuring `backing.content_hash` (eager) or `backing.uri + lineage.params` (lazy) are populated.
- Retroactive migration of existing uuid4-id Artifacts in any persisted registry.

## Verify (before submitting)

- `Artifact()` constructed without an `id` value derives one in `__post_init__`.
- `Artifact()` constructed with an explicit `id=` accepts it (back-compat for test fixtures).
- Same source bytes via the same Connector → same Artifact.id across re-materialization.
- Same Operator + same input ids + same params → same output Artifact.id across re-runs.
- `ArtifactIdentityError` raised when none of the three strategies apply.
- The full test suite at `/Users/jakegearon/projects/quarry/tests/pressure_test/` runs and passes (or new failures are reported with reasoning; Brief 1 + 2 surface tests stay green).
- `canonical_uri("postgresql://user:pw@host:5432/db?query=X")` strips the password and returns a stable form.
- `canonical_params({"b": 2, "a": 1})` and `canonical_params({"a": 1, "b": 2})` return equal strings.
- No file outside the write scope has been modified.

## Return shape

Return a chat message structured as:

1. **Summary** — one paragraph naming what landed.
2. **Item-by-item** — A through G, each with: what was changed, file paths touched, any judgment calls, any unexpected findings.
3. **Connector survey** — for each of the 29 Connectors, a one-line note on which derivation strategy applies (Connector eager / Connector lazy / mixed) and whether any change was needed.
4. **Operator survey** — for each of the 16 Operators, a one-line note confirming Lineage construction sets `operation`, `input_ids`, `params` correctly. Flag any operator that needed Lineage-construction fixes.
5. **Flag list** — every construction site where content-derivation can't proceed (escalate territory).
6. **Test results** — passing/failing counts plus a list of new/modified test files with one-line descriptions.

The Watermaster will integrate your return: verify writes are within scope (with explicit prior-Brief-baseline awareness so the verification doesn't conflate Brief 1+2's writes with Brief 3's), audit the flag list, and either commit the work as-is or send a follow-up Brief.

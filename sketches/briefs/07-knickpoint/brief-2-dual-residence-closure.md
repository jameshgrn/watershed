# Engineer Brief — Brief 2 (dual-residence closure for quarry-operators)

**engineer_model**: `codex-gpt-5` (the seated Codex instance the Source is using; confirm exact identifier at transmission)
**source_utterance** (verbatim, concatenated across the session leading to this Brief):
> "lets produce a prompt for the engineer to do some work"
>
> "we can give multiple requests in a row and bvatch them i will be using codex. let it write files"
>
> "okay it landed" (acknowledgement that Brief 1 integrated cleanly; implicit approval of the Watermaster's recommended Shape B → revised to Shape A based on reconnaissance findings)

**compiled_by**: Watermaster Knickpoint
**compiled_at**: 2026-05-11
**state**: integrated (drafted 2026-05-11 → sent 2026-05-11 → returned 2026-05-11 → integrated 2026-05-11)
**supersedes**: none
**expected_return_shape**: executed file writes within the write scope below, plus a chat return summarizing each item (A–G), the per-operator wiring updates, any Check-class implementation where the inline operator-side check couldn't be reproduced from Artifact state alone (escalate territory), and the test run results.

---

## Read these before starting

You are an external Engineer consulted by the Watermaster of a research lab called *watershed*. You read only this Brief. You do not see the conversation that produced it, including Brief 1 (which you executed cleanly in a prior session and which has been integrated).

Read the following files first — they are the discipline this Brief implements, not aspiration:

1. `/Users/jakegearon/projects/watershed/CANON.md` — Articles I–XV. Article II (one canonical writer per module), Article X (operator invariants travel with their operators), Article XV (typed records are frozen-pinned at lifecycle transitions; in-place edits are forbidden).
2. `/Users/jakegearon/projects/watershed/sops/operator-shape.md` v1, especially the discipline:
   > "maintain dual-residence for every check named in `declared_checks()`: the same name appears both inline within the Operator's `execute()` flow (run during execution against in-memory state) and as a standalone Check class implementing the Protocol (run independently against any Artifact); both implementations produce `CheckResult`s with the same `check_name`"
   and the Escalate clause:
   > "if existing quarry-operators implementations have `declared_checks()` entries without matching standalone Checks (partial dual-residence today) — the lift into flume is the time to close the gap; do not lift partial dual-residence into flume canonical state"

   This Brief is that lift moment for the standalone-Check side.

3. `/Users/jakegearon/projects/watershed/sops/data-contracts.md` v2 — Artifact-level discipline; the Check Protocol's `run(artifact)` reasons from the Artifact alone, never from operator-internal state.

The lab vocabulary is fluvial. *quarry* is the boundary module (untyped → typed); *flume* is where typed operators do scientific work. Today's `quarry-core` already owns the typed Artifact/Operator/Check surfaces. This Brief implements the dual-residence side of `operator-shape.md` v1 against today's quarry-operators.

## What you did in Brief 1 (context — already landed)

(Stated here for the Engineer's reference since you do not see prior conversation.)

In Brief 1 you aligned `OperatorSpec`, `OperatorResult`, the `Operator` Protocol, and `Artifact.with_check` with `operator-shape.md` v1. You added:

- The four new OperatorSpec fields with cross-field invariants in `__post_init__`.
- `OperatorConformanceError` and `assert_operator_conforms(op)` in `quarry-core/.../operator.py`. The function checks: if `op.spec.determinism_class == "stable"`, the operator must expose a callable `semantic_equality(a, b) -> bool`.
- A call to `assert_operator_conforms(op)` at the end of `get_operator(name)` in `quarry-operators/.../registry.py`.
- `OperatorResult` made frozen with `truth_source_by_field`.
- All 16 operators declare `determinism_class`; six are `stable` (`build_cog`, `geocode_slc`, `reproject`, `slc_calibration`, `water_elevation_mosaic`, `zonal_stats`) and have `semantic_equality` delegating to helpers in `semantics.py`.

The dual-residence side of `assert_operator_conforms` was deliberately deferred to this Brief.

## What you are doing in Brief 2

Closing the dual-residence gap: every name returned by an Operator's `declared_checks()` must resolve to a standalone Check class implementing the `Check` Protocol. There are 54 declared-check names across the 16 operators; the deduplicated set is roughly 28 distinct names. Three are already implemented in `quarry-core/.../check.py` (`CRSValid` for `crs_valid`, `ExtentSane` for `extent_sane`, `BackingStoreAccessible` for `backing_accessible`); these are the shared baseline. One (`InternalOutletCount` for `no_internal_outlets`) exists in `quarry-operators/.../checks.py` but is **stranded** — not imported or referenced anywhere. You will wire it in. The remaining ~24 names need new standalone Check classes.

The package layout (reminder):

- `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/check.py` — `Check` Protocol + `CRSValid`, `ExtentSane`, `BackingStoreAccessible`. **Read-only for this Brief.** quarry-core stays zero-dep on quarry-operators per the Quarry doctrine; nothing new from this Brief lifts here.
- `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks.py` — currently holds only `InternalOutletCount`. **You will extend this file with new Check classes; you may split into per-family files if it exceeds ~600 lines.**
- `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/registry.py` — operator registry; you will extend it to also call the new dual-residence assertion at materialize time.
- 16 operator files in `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/` — each currently has an inline check implementation in `execute()` and a `declared_checks()` method returning a list of strings.

## Items

### Item A — Mint the check-registry

Create `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/check_registry.py`. Mirror the operator-registry pattern from `registry.py`:

- Module-level `_CHECK_REGISTRY: tuple[tuple[str, str, str], ...]` — entries are `(check_name, module_path, class_name)`. Holds both quarry-core's existing classes (e.g., `("crs_valid", "quarry_core.check", "CRSValid")`) and quarry-operators' classes (existing `InternalOutletCount` + the new ones from item C).
- `CHECK_NAMES: tuple[str, ...] = tuple(name for name, _, _ in _CHECK_REGISTRY)`.
- `_NAME_TO_ENTRY: dict[str, tuple[str, str]]` for O(1) lookup.
- `get_check(name: str) -> Check` — lazy importlib lookup; constructs an instance of the class; verifies it conforms to the `Check` Protocol via `isinstance(check, Check)`; raises `KeyError` for unknown names.
- The registry is the canonical source of truth: every declared-check name an operator returns must be present in `CHECK_NAMES`.

### Item B — `assert_dual_residence` and registry-time gating

In `quarry-operators/.../registry.py`, add a new helper `assert_dual_residence(op: Operator) -> None`:

- Iterates `op.declared_checks()`.
- For each name, calls `get_check(name)` to confirm it resolves through the check-registry; if `KeyError`, raises a new `OperatorDualResidenceError` (subclass of `OperatorConformanceError`, defined in this file since `OperatorConformanceError` is in quarry-core and quarry-core stays zero-dep — alternatively raise `OperatorConformanceError` directly with a clear message; choose whichever reads cleaner).
- For each resolved Check class, additionally verify `check.name == declared_name` (the standalone class's `name` property must match the operator's declared name; structural mismatch is a registry-wiring bug).

Call `assert_dual_residence(op)` at the end of `get_operator(name)`, alongside the existing `assert_operator_conforms(op)`. Order: `assert_operator_conforms` first (Protocol surface), `assert_dual_residence` second (declared_checks → standalone Check). Both must pass.

### Item C — Mint the new standalone Check classes

For each declared-check name that lacks a standalone class (the audit table below), implement a Check class in `quarry-operators/.../checks.py`. Each class:

- `@dataclass(frozen=True)` or a plain class; the `Check` Protocol is `@runtime_checkable` and only requires `name`, `description`, `run(artifact) -> CheckResult` — match the shape of existing `InternalOutletCount`.
- `name` property returns the canonical snake_case declared-check name (e.g., `"is_cog"`).
- `description` property returns a one-sentence human-readable explanation.
- `run(artifact: Artifact) -> CheckResult` re-implements the inline check from the operator's `execute()` body, but reasoning **from the finished Artifact alone**. The `CheckResult` shape is `check_name: str, state: ValidationState, message: str = "", timestamp: datetime` (from `quarry-core/.../artifact.py`).

**Critical**: the standalone `run(artifact)` cannot reach into operator-internal state (intermediate buffers, params not exposed on the Artifact, ephemeral handles). It must reason from `artifact.backing`, `artifact.spatial`, `artifact.temporal`, `artifact.metadata`, and — for raster/vector files — by opening `artifact.backing.uri` with rasterio/fiona/etc. and reading the data.

For each declared-check name, audit the operator's inline check body and ask: can this check be reproduced from the finished Artifact alone? If yes, write the Check class. If no — for example, if the inline check compares against an intermediate operator-internal value not exposed on the Artifact — flag it in the chat return with the operator name, the check name, and what specifically can't be reproduced. **Do not invent a check that does something different from the inline check** to make it "work"; flag and stop. Dual residence requires functional equivalence, not aspirational parallel.

### Item D — Wire `InternalOutletCount`

The existing `InternalOutletCount` class in `quarry-operators/.../checks.py` has `name = "no_internal_outlets"` and currently is not imported by anyone. Register it in the new `check_registry.py` under `"no_internal_outlets"`. Verify it conforms to the `Check` Protocol (it should already).

### Item E — Verify each operator's `declared_checks()` resolves cleanly

After items A–D, every Operator's `declared_checks()` should return only names present in `CHECK_NAMES`. Run `assert_dual_residence(op)` against each of the 16 operators in a test or at module-import time; report any operator whose declared names don't resolve.

Do not change the contents of any operator's `declared_checks()` method unless: (a) the operator declares a check name that has no defensible standalone implementation (escalate territory, flag and stop), or (b) the operator declares a check name that is a typo or stale leftover (flag in the chat return and either drop it or keep it pending Watermaster decision — your call but document it).

### Item F — Layout

Default: extend `quarry-operators/.../checks.py` with all new classes alongside `InternalOutletCount`. If the resulting file exceeds ~600 lines or readability suffers, split by operator family (`checks_raster.py` for raster-output operators, `checks_table.py` for table-output operators, etc.) and update the check-registry's `module_path` entries accordingly. Use your judgment; document the layout choice in the chat return.

### Item G — Tests

Add tests at `/Users/jakegearon/projects/quarry/tests/pressure_test/`:

- `test_check_registry.py` — verifies `CHECK_NAMES` covers every declared-check name across the 16 operators; verifies `get_check(name)` returns an instance conforming to the `Check` Protocol; verifies a `KeyError` is raised for unknown names.
- `test_dual_residence.py` — verifies `assert_dual_residence(op)` passes for every operator in the registry; verifies it raises on a synthetic operator with an undeclared check name.
- For each new Check class, a small test confirming `run(artifact)` produces the expected `CheckResult.state` for valid and invalid inputs. Use minimal fixtures — small in-memory rasters/tables where possible — to keep test runtime low. If a Check needs a real raster fixture, use the existing fixtures under `/Users/jakegearon/projects/quarry/tests/fixtures/` or skip with a clear `@pytest.mark.skip` reason.

The full pressure_test suite must continue to pass. Brief 1's 45-passing `test_operator_shape.py` and `test_registry.py` must remain green.

## Audit — names that need new standalone Check classes

The full table from Brief 1's item F is preserved in the Watermaster's records. The names you need to implement (deduplicated, excluding the 3 already in quarry-core and the 1 existing in quarry-operators):

**Shared (≥2 operators):**

- `nodata_preserved` (aspect, build_cog, hillshade, slope) — output preserves the input's nodata value
- `valid_range` (aspect, hillshade, slope) — output values are within the expected range for the product (e.g., aspect in [0, 360], hillshade in [0, 255])
- `resolution_consistent` (aspect, hillshade, slope) — output resolution matches input resolution
- `row_count_matches` (sample_raster, zonal_stats) — output row count matches expected (input feature count, or zone count)
- `schema_complete` (sample_raster, zonal_stats) — output table has all expected columns

**Singletons (operator-specific):**

- `is_cog` (build_cog) — output is a valid Cloud-Optimized GeoTIFF (rasterio.io.MemoryFile-validate or COG validator)
- `crs_preserved` (build_cog) — output CRS equals input CRS
- `dimensions_preserved` (build_cog) — output dimensions equal input dimensions
- `extent_within_input` (clip_raster) — output extent is contained within input extent
- `valid_code_set` (d8_flow_direction) — output cell values are in the valid D8 code set (typically {1, 2, 4, 8, 16, 32, 64, 128, NoData})
- `no_pits` (d8_flow_direction) — output has no interior depressions (every non-NoData cell flows somewhere)
- `all_valid_assigned` (d8_flow_direction) — every non-NoData input cell has a valid flow-direction code in the output
- `no_interior_pits` (fill_depressions) — filled output has no interior depressions
- `elevation_only_raised` (fill_depressions) — no output elevation is lower than the input at the same cell
- `no_cycles` (flow_accumulation) — accumulation graph has no cycles (verify by spot-checking accumulation values monotonicity along sample flow paths)
- `nonnegative` (flow_accumulation) — all output accumulation values are ≥ 0
- `conservation` (flow_accumulation) — total accumulation equals input cell count (mass conservation)
- `gcp_count_sufficient` (geocode_slc) — output has the minimum required GCPs in metadata
- `dimensions_sane` (rasterize_vector) — output dimensions are non-zero and within plausible bounds
- `nodata_background` (rasterize_vector) — output cells where no vector feature was present carry the nodata value
- `crs_matches_target` (reproject) — output CRS matches the target CRS specified in params (the param value will need to live in `artifact.metadata` or `artifact.lineage.params` for the standalone Check to read it; verify this is the case or flag)
- `sigma0_finite` (slc_calibration) — all output sigma0 values are finite (no NaN/inf)
- `sigma0_nonnegative` (slc_calibration) — all output sigma0 values are ≥ 0
- `left_features_preserved` (spatial_join) — output row count equals left-input feature count
- `schema_no_collision` (spatial_join) — output schema has no duplicate column names from left/right merge
- `min_observations` (water_elevation_mosaic) — output has ≥ minimum required observations per cell (where this is a configured threshold)

Where the description above is wrong or incomplete, the inline check body is the source of truth — read the operator's `execute()` and implement the standalone class to match what the inline check actually verifies. If the inline check tests something different from this description, follow the inline check.

## Constraints

- **Write only inside the write scope below.** Any write outside is an integration failure.
- **Do not modify `/Users/jakegearon/projects/watershed/`.** SOPs, CANON, and lineage are the Watermaster's domain.
- **Do not modify `quarry-core/.../check.py`.** quarry-core stays zero-dep; nothing new lifts to quarry-core in this Brief. Reuse existing CRSValid/ExtentSane/BackingStoreAccessible by registering them in the new check-registry.
- **Do not modify any operator's `execute()` body.** The inline checks stay; this Brief is purely additive on the standalone-Check side. Exception: if an operator's `declared_checks()` returns a name with no defensible standalone implementation, flag and stop — do not silently delete or rename.
- **Do not invent semantics.** If the inline check tests something different from the audit's description above, follow the inline check. If you can't reproduce the inline check from Artifact state alone, flag the operator + check name + reason in the chat return.
- **Do not propagate to other repos.** You may read from `/Users/jakegearon/projects/watershed/` for the SOPs and from any sibling repo for context, but write only inside the scope.
- **Preserve the lab's vocabulary.** Don't rename Check, Operator, OperatorSpec, declared_checks, Artifact, etc.
- **If you see useful adjacent work outside the scope, flag it in the return rather than writing it.** (Brief 1's session had a misattribution issue around adjacent connector files; the discipline is: flag, don't extend.)
- **One coherent change set.**

## Write scope

```
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/check_registry.py        (new)
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks.py                (extend)
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks_*.py              (optional per-family split if needed)
/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/registry.py              (extend with assert_dual_residence call)
/Users/jakegearon/projects/quarry/tests/pressure_test/test_check_registry.py                              (new)
/Users/jakegearon/projects/quarry/tests/pressure_test/test_dual_residence.py                              (new)
/Users/jakegearon/projects/quarry/tests/pressure_test/test_check_*.py                                     (new per-check or per-family test files, your call)
```

You may also read freely anywhere in `/Users/jakegearon/projects/quarry/` and `/Users/jakegearon/projects/watershed/`; reading is unbounded, writing is the scope above.

## Out of scope

- Modifying any operator's `execute()` body — purely additive on the standalone-Check side.
- Lifting any new Check class into `quarry-core` — stays in quarry-operators.
- `RunRecord` → `OperatorRun` migration per `operator-run-shape.md` v1 (later Brief).
- `Artifact.id` content-derivation per `data-contracts.md` v2 (later Brief).
- Connector materialize-path changes; hydrops integration; dgov boundary work.

## Verify (before submitting)

- `CHECK_NAMES` covers every declared-check name across the 16 operators in the registry.
- `get_check(name)` returns a Check-conforming instance for every registered name.
- `assert_dual_residence(op)` passes for every operator returned by `get_operator(name)`.
- The full test suite at `/Users/jakegearon/projects/quarry/tests/pressure_test/` runs and passes (or new failures are reported with reasoning; in particular Brief 1's `test_operator_shape.py` and `test_registry.py` stay green).
- No file outside the write scope has been modified.

## Return shape

Return a chat message structured as:

1. **Summary** — one paragraph naming what landed.
2. **Item-by-item** — A through G, each with: what was changed, file paths touched, any judgment calls, any unexpected findings.
3. **New Check class inventory** — a list of every Check class minted, with `name`, file path, and a one-line description.
4. **Layout decision** — whether `checks.py` stayed monolithic or was split into per-family files, with the rationale.
5. **Flag list** — every operator + declared-check name where the inline check could not be reproduced from Artifact state alone, with the specific reason (e.g., "operator's nodata_preserved compares output nodata against input nodata that's only available via input artifact, not output — recommend lifting input nodata to Lineage.params for standalone reproducibility"). These are escalate territory for the Watermaster to decide.
6. **Test results** — passing/failing counts plus a list of new/modified test files with one-line descriptions.

The Watermaster will integrate your return: verify writes are within scope, audit the flag list, and either commit the work as-is or send a follow-up Brief if revisions are needed. Every revision is a new Brief with a `supersedes` link per `engineer-brief.md`.

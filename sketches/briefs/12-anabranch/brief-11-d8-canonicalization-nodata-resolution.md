# Brief 11 — D8 constants canonicalization + operator `params.nodata` resolution gap

**Watermaster**: Anabranch
**Date**: 2026-05-14
**Engineer model**: codex-gpt-5
**Write scope**: `/Users/jakegearon/projects/quarry/packages/quarry-operators/**`, `/Users/jakegearon/projects/quarry/tests/pressure_test/**`
**State**: integrated

---

## Goal

Close two small flags Bench surfaced in Brief 8's return:

- **Flag 3** — D8 direction-offset arrays (`D8_DR`, `D8_DC`) and special codes (`OUTLET`, `PIT`, `NODATA`) are duplicated across three East-first sites (`_topology.py` private, `d8_flow_direction.py` public, `flow_accumulation.py` public). Canonicalize them in `_topology.py` (the existing shared-helper module Brief 8 minted), make them public, update all importers.
- **Flag 4** — the inline `d8_flow_direction.execute()` resolves nodata as `params.nodata if params.nodata is not None else src.nodata` (operator-side override semantics), but the standalone `AllValidAssigned` / `ElevationOnlyRaised` check classes read `src.nodata` directly from the input raster — disagreeing with the operator when a user passes `params.nodata`. Same gap exists between `fill_depressions.execute()` and `ElevationOnlyRaised`. Fix: stash the resolved nodata in `Lineage.params["resolved_nodata"]` at operator execute() time, extending the Brief 7 lineage-params-stashing pattern; standalone classes read from lineage with fall-back to `src.nodata` for backward compatibility.

Both flags are partial-coverage (not discipline failures); this Brief tightens the consistency between inline and standalone Check classes per `operator-shape.md` v2's dual-residence rule.

## Source utterance (verbatim)

> letsdo the smaller arcs

Following from the Source's selection of Brief 8 follow-ups (Flag 3 + Flag 4) over Brief 10 (lifecycle narrowing) or `engineer-brief.md` v3 (recon-as-deliverable canonicalization).

## Background (read first)

1. `sops/operator-shape.md` v2 — Check Protocol with `inputs: Sequence[Artifact] = ()`, dual-residence rule. Flag 4 closes the input-aware-check parity gap.
2. `sops/data-contracts.md` v2 — `Lineage.params` is the typed home for input-derived scalars per Brief 7's pattern.
3. `sketches/THINKING.md` — the Live observation pointers for Bench's Brief 7 ("Lineage.params as the canonical home for input-derived scalars") and Brief 8 ("D8 constants canonicalization is open follow-up work"; "Operator `params.nodata` resolution is not reflected in standalone-check parity").
4. `sops/engineer-brief.md` v2 — your operating discipline as Engineer.
5. Bench's Brief 8 return at `sketches/briefs/11-bench/return-8.md` (the flag list at the bottom).

Source-truth files (line citations as of 2026-05-14):
- `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/_topology.py` (87 lines; Brief 8 minted)
- `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/d8_flow_direction.py` (D8_DR/D8_DC at 55-56; D8_DIST at 60; OUTLET/PIT/NODATA at 63-65; nodata resolution at 155; Lineage stash at 208)
- `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/flow_accumulation.py` (D8_DR/D8_DC at 48-49; OUTLET/PIT/NODATA_CODE at 51-53; NODATA_CODE is dead — defined but unused)
- `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/fill_depressions.py` (nodata resolution at 135; Lineage stash at 197; local `_D8_DR`/`_D8_DC` at 289-290 use North-first encoding — DIFFERENT scheme, do NOT touch)
- `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks.py` (imports D8_DC/D8_DR/NODATA from d8_flow_direction at line 25)
- `/Users/jakegearon/projects/quarry/packages/quarry-operators/src/quarry_operators/checks_artifact.py` (imports NODATA as D8_NODATA from d8_flow_direction at line 38; `AllValidAssigned` at line 363; `ElevationOnlyRaised` at line 426)
- `/Users/jakegearon/projects/quarry/tests/pressure_test/test_d8_flow_direction.py` (imports at line 29: D8_DC, D8_DR, NODATA, OUTLET, PIT, D8FlowDirectionOperator, D8FlowDirectionParams, _compute_d8)
- `/Users/jakegearon/projects/quarry/tests/pressure_test/test_hydrology_adversarial.py` (imports OUTLET, PIT at line 33)
- `/Users/jakegearon/projects/quarry/tests/pressure_test/test_internal_outlet_check.py` (imports NODATA, OUTLET, D8FlowDirectionOperator, D8FlowDirectionParams)

---

## Items

### Item A — Canonicalize D8 constants in `_topology.py`

In `_topology.py`:

- Rename private `_D8_DR` → public `D8_DR`; rename `_D8_DC` → `D8_DC`. (Currently lines 24-25.)
- Add public special-code constants:
  ```python
  D8_OUTLET = 8
  D8_PIT = 9
  D8_NODATA = -1
  ```
- Update `detect_cycle`'s internal references from `_D8_DR` → `D8_DR`, `_D8_DC` → `D8_DC` (lines 60-61, 79-80).
- Add `__all__` at the bottom listing `D8_DR, D8_DC, D8_OUTLET, D8_PIT, D8_NODATA, detect_cycle`.
- Update the module docstring's first paragraph to name the constants as the canonical home for East-first D8 encoding: `0=E, 1=SE, 2=S, 3=SW, 4=W, 5=NW, 6=N, 7=NE` with `8=OUTLET, 9=PIT, -1=NODATA`. Add a one-line note that `fill_depressions.py` uses a separate North-first encoding and intentionally does NOT consume these constants.

### Item B — `d8_flow_direction.py`

- Replace lines 55-56 (`D8_DR`/`D8_DC` definitions) with an import:
  ```python
  from quarry_operators._topology import D8_DC, D8_DR, D8_NODATA, D8_OUTLET, D8_PIT
  ```
- Remove lines 63-65 (`OUTLET = 8`, `PIT = 9`, `NODATA = -1`).
- Keep `D8_DIST` and `_SQRT2` at line 59-60 (operator-specific slope weights — not shared with flow_accumulation).
- Replace every internal usage of bare `OUTLET`, `PIT`, `NODATA` with `D8_OUTLET`, `D8_PIT`, `D8_NODATA` respectively. Sites include (non-exhaustive grep-confirm):
  - Line 169 `"nodata": NODATA` → `"nodata": D8_NODATA`
  - Lines 244-247 (`valid_code_set` check)
  - Line 264 (`pit_count = int(np.sum(valid_flow == PIT))`)
  - Line 304 (`unassigned = int(np.sum(valid_flow == NODATA))`)
  - Lines 401-406 (`_assign_steepest_descent` body)
  - Line 424 (`if flow[r, c] != PIT:`)
  - Line 436 (`if dem[nr, nc] <= dem[r, c] and 0 <= flow[nr, nc] <= OUTLET:`)
  - Line 452 (`flow = np.full((nrows, ncols), NODATA, dtype=np.int8)`)
  - Run a final `grep -nE "\b(OUTLET|PIT|NODATA)\b" d8_flow_direction.py` after edits to confirm zero remaining bare references.

### Item C — `flow_accumulation.py`

- Replace lines 48-49 (`D8_DR`/`D8_DC` definitions) with an import:
  ```python
  from quarry_operators._topology import D8_DC, D8_DR, D8_OUTLET, D8_PIT, detect_cycle
  ```
  (Consolidates with the existing `from quarry_operators._topology import detect_cycle` at line 45.)
- Remove lines 51-53 (`OUTLET = 8`, `PIT = 9`, `NODATA_CODE = -1`). `NODATA_CODE` is dead — confirmed via grep that it's defined but never used (only mentioned in line 14 module docstring comment and line 330 inline comment; both are descriptive prose, not references).
- Replace internal usages of bare `OUTLET`, `PIT` with `D8_OUTLET`, `D8_PIT`. Sites:
  - Line 143 (`valid = (flow >= 0) & (flow <= PIT)`)
  - Line 256 (`outlet_mask = valid & ((flow == OUTLET) | (flow == PIT))`)
  - Grep-confirm zero remaining bare references after edits.

### Item D — `checks.py`

- Change line 25:
  ```python
  from quarry_operators.d8_flow_direction import D8_DC, D8_DR, NODATA
  ```
  to:
  ```python
  from quarry_operators._topology import D8_DC, D8_DR, D8_NODATA
  ```
- Replace bare `NODATA` references in this file with `D8_NODATA` (sites at lines 82, etc. — grep `\bNODATA\b` in this file post-edit to find them all).

### Item E — `checks_artifact.py`

- Change line 38:
  ```python
  from quarry_operators.d8_flow_direction import NODATA as D8_NODATA
  ```
  to:
  ```python
  from quarry_operators._topology import D8_NODATA
  ```
- Update `AllValidAssigned.run` (at line 363):
  - After reading the input DEM's nodata at line 400 (`in_nodata = src.nodata`), read the operator's resolved nodata from the OUTPUT lineage:
    ```python
    resolved_nodata = lineage_params(artifact).get("resolved_nodata", in_nodata)
    ```
  - Use `resolved_nodata` in place of `in_nodata` for the `_build_dem_valid_mask(dem, resolved_nodata)` call at line 402.
  - Document the fall-back semantics inline (one-line comment): "Reads operator-resolved nodata from output Artifact's Lineage.params when present (Brief 11); falls back to input raster's src.nodata when missing (pre-Brief-11 artifacts)."
- Update `ElevationOnlyRaised.run` (at line 426):
  - Same pattern: after `in_nodata = src.nodata` at line 461, read `resolved_nodata = lineage_params(artifact).get("resolved_nodata", in_nodata)` and substitute at line 463's `_build_dem_valid_mask(original, resolved_nodata)`.
  - Same one-line fall-back comment.
- The `NoCycles` and `Conservation` classes do NOT touch nodata resolution and need no change beyond Item E's import line.

### Item F — `d8_flow_direction.py` Lineage stash (extends Item B)

Change line 208 from:
```python
params={"nodata": nodata},
```
to:
```python
params={"nodata": params.nodata, "resolved_nodata": nodata},
```

The verbatim caller param `params.nodata` (which may be `None`) is now distinct from the resolved value `nodata` (always concrete or `None` if input has no nodata header). This matches Brief 7's pattern of distinguishing caller intent from operator-observed values within `Lineage.params`.

**Artifact.id implication owned**: Brief 3's `derive_id_from_provenance(operation, inputs, params)` derives output Artifact.id from `Lineage.params`. Adding the `resolved_nodata` key changes prov-derived ids for newly-produced D8 outputs. Pre-existing D8 output artifacts in any registry remain frozen-pinned per CANON XV. Test fixtures that pin literal D8 output ids will need updating — flag any you encounter; the operator-integration tests already read `lineage.params` dynamically per Brief 7's pattern.

### Item G — `fill_depressions.py` Lineage stash

Change line 197 from:
```python
"nodata": nodata,
```
to:
```python
"nodata": params.nodata,
"resolved_nodata": nodata,
```

Same Artifact.id ownership as Item F.

**Do NOT touch** `fill_depressions.py`'s local `_D8_DR`/`_D8_DC` arrays at lines 289-290. They use a different (North-first) D8 encoding and stay private to this operator. This is out of Brief 11's scope.

### Item H — Test files

Update test imports and usages:

- **`tests/pressure_test/test_d8_flow_direction.py`** — line 29 import block:
  ```python
  from quarry_operators.d8_flow_direction import (
      D8_DC,
      D8_DR,
      NODATA,
      OUTLET,
      PIT,
      D8FlowDirectionOperator,
      D8FlowDirectionParams,
      _compute_d8,
  )
  ```
  Split into:
  ```python
  from quarry_operators._topology import D8_DC, D8_DR, D8_NODATA, D8_OUTLET, D8_PIT
  from quarry_operators.d8_flow_direction import (
      D8FlowDirectionOperator,
      D8FlowDirectionParams,
      _compute_d8,
  )
  ```
  Then rename all bare `OUTLET` → `D8_OUTLET`, `PIT` → `D8_PIT`, `NODATA` → `D8_NODATA` usages throughout the file (grep-confirm zero remaining bare references).

- **`tests/pressure_test/test_hydrology_adversarial.py`** — line 33:
  ```python
  from quarry_operators.d8_flow_direction import OUTLET, PIT
  ```
  to:
  ```python
  from quarry_operators._topology import D8_OUTLET, D8_PIT
  ```
  Rename bare `OUTLET`/`PIT` → `D8_OUTLET`/`D8_PIT` throughout.

- **`tests/pressure_test/test_internal_outlet_check.py`** — same pattern:
  ```python
  from quarry_operators.d8_flow_direction import (
      NODATA,
      OUTLET,
      D8FlowDirectionOperator,
      D8FlowDirectionParams,
  )
  ```
  to:
  ```python
  from quarry_operators._topology import D8_NODATA, D8_OUTLET
  from quarry_operators.d8_flow_direction import D8FlowDirectionOperator, D8FlowDirectionParams
  ```
  Rename usages.

- **Existing operator-integration tests** (e.g., `test_check_artifact.py`, `test_check_raster.py` — find them): if any pin literal Artifact.ids for D8 or fill outputs, those fixtures need updates because of Item F/G's Artifact.id-stability change. Most existing tests should read `lineage.params` dynamically per Brief 7's pattern and need no change. Flag any literal-id pins you find.

- **New tests for Item E's resolved_nodata read** — add at least two test cases (either in a new file or appended to existing test_check_artifact.py / test_check_raster.py per the repo's convention):
  1. `AllValidAssigned` with `inputs[0]` and an artifact whose `Lineage.params["resolved_nodata"]` is set: confirms the check uses the lineage value, not `src.nodata`. Construct via the operator's actual execute path if possible (cleanest); otherwise mock an Artifact with the appropriate lineage params.
  2. `AllValidAssigned` with `inputs[0]` and an artifact whose `Lineage.params` is missing `resolved_nodata`: confirms the fall-back to `src.nodata` works (backward-compat for pre-Brief-11 artifacts).
  3. Parallel pair for `ElevationOnlyRaised` if budget allows; if not, flag the missing coverage in your return rather than skipping silently.

---

## Out of scope (explicit)

- `fill_depressions.py`'s North-first `_D8_DR`/`_D8_DC` arrays (lines 289-290). Different encoding by intent.
- `D8_DIST` (slope weights in `d8_flow_direction.py` line 60). Operator-specific.
- Any other Check class beyond `AllValidAssigned` / `ElevationOnlyRaised` for the nodata resolution fix.
- Adding `resolved_nodata` to other operators (only d8_flow_direction and fill_depressions have the `params.nodata` override pattern; verify and confirm in your return if needed).
- Any changes to `quarry-core` (constants and helpers stay quarry-operators-internal).
- Backward-compat aliases in `d8_flow_direction.py` / `flow_accumulation.py`. The rename is full per Brief 6's canonical-removal precedent.

---

## Acceptance criteria

Return should include:

- All items A–H complete with file:line citations.
- `cd /Users/jakegearon/projects/quarry && uv run pytest tests/pressure_test/ -q` count. Target: at or above Brief 8's baseline of 1974 passed / 54 skipped / 3 failed. Expected: the new tests for Item H add 2-3 passing, no regressions. Pre-existing connector failures (3) remain unchanged.
- `ruff check` clean on every modified file.
- `ty check` clean on every modified file.
- Post-edit grep confirmation: zero bare `\bOUTLET\b`, `\bPIT\b`, `\bNODATA\b` references in `d8_flow_direction.py`, `flow_accumulation.py`, `checks.py`, `checks_artifact.py`, `test_d8_flow_direction.py`, `test_hydrology_adversarial.py`, `test_internal_outlet_check.py` (only `D8_OUTLET`/`D8_PIT`/`D8_NODATA` should remain).
- Confirm `fill_depressions.py:289-290` untouched.
- Confirm `D8_DIST` and `_SQRT2` retained in `d8_flow_direction.py`.

If you discover deviations you believe are correct (parallel to Cascade's `_clone` and Bench's D8 constant typo correction), document under Deviations.

---

## Format for your return

```
## Summary
1–2 sentence description.

## Items
- A: <status + key paths>
- B: ...
- ...
- H: ...

## Test results
- pytest: <counts>
- ruff: <clean | issues>
- ty: <clean | issues>
- grep check: <bare-name references remaining | clean>

## Deviations
- <list or "(none)">

## Flags (adjacent work surfaced, NOT written)
- <list>

## Files written
- <path>: <one-line description>
```

---

**Self-contained**: read the listed Background documents plus the source files cited and you have everything. Do not modify `sketches/lineage/*`. Stay strictly inside `write_scope`. Watershed lineage is the seated Watermaster's domain per CANON Article XVI.

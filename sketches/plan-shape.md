# plan-shape — the typed plan-objects layer

Working scaffold. Reads next to `SKETCHES.md` and `sops/plan-shape.md`. Catalogs the typed plan-object surfaces as they exist in dgov today, the lifted home in watershed, and what changes at the boundary. No code here yet — discipline ahead of lift.

---

## The layer

A Plan in watershed is a typed-data structure that distributary compiles from one or more typed Intents (per `sops/intent-compilation.md`) and dispatches to subprocess workers. Plans are pure data per CANON Article V; the worker is the only thing that runs code, and the worker reads the Plan from a typed-data envelope, not from a Python import.

The scaffold is organized in five tiers, mirroring dgov's current layout:

1. **Tree** — pre-flatten plan structure, mirrors filesystem layout
2. **Spec** — flat-form Plan, dispatch-ready
3. **Unit** — individual unit of work (one slug, one prompt, one set of file claims)
4. **DAG** — task graph (dependencies, fan-out/fan-in, parallelism)
5. **Action** — the typed dispatch action union and lifecycle states

Plus errors and the new types plan-shape requires that dgov today carries informally.

---

## Tier 1: Tree-level

| type | dgov home | watershed home | fields | notes |
|---|---|---|---|---|
| `RootMeta` | `dgov/plan_tree.py` | `shared/` | name, summary, sections | metadata extracted from plan-root markdown |
| `PlanTree` | `dgov/plan_tree.py` | `distributary/` | plan_root, root_meta, section_files | pre-flatten; mirrors filesystem |
| `FlatPlan` | `dgov/plan.py` | `distributary/` | plan_root, root_meta, units, source_map, source_mtime_max | post-flatten; flattens PlanTree into a unit map |

Tree-level types are mostly distributary-internal; `RootMeta` is the only one that lifts to `shared/` (consumed by tributary's `Validation` for plan-context).

---

## Tier 2: Spec-level

| type | dgov home | watershed home | required fields | notes |
|---|---|---|---|---|
| `PlanSpec` | `dgov/plan.py` | `distributary/` (lifts to `shared/`) | name, goal, units, project_root, session_root, default_agent, default_timeout_s, max_retries, **sop_set_hash**, source_mtime_max | the canonical Plan; plan-shape extends with `id`, `compiled_from`, `compiled_by`, `compiled_at`, `state`, `supersedes` |
| `PlanIssue` | `dgov/plan.py` | `distributary/` | severity, message, unit | validation findings; consumed pre-dispatch |

**Fields plan-shape adds that dgov today carries informally or implicitly:**

- `id: str` — content-derived (hash of `compiled_from + units + sop_set_hash + project_root + session_root + defaults + max_retries + supersedes`); stable; **today missing — Plans are keyed by `name + project_root`**
- `compiled_from: Intent | tuple[Intent, ...]` — the typed Intents that produced this Plan; **today missing — no formal Intent link**
- `compiled_by: WatermasterId` — the Watermaster who compiled it (lineage entry name); **today missing — no signed-by field**
- `compiled_at: datetime` — UTC tz-aware; **today implicit — exists as plan-creation timestamp but not first-class**
- `state: Literal["draft", "dispatched", "superseded"]` — explicit lifecycle; **today implicit — Plans are mutable until dispatch, no superseded notion**
- `supersedes: prior_plan_id | None` — top-level Plan field for revisions; **today missing — revisions edit in place**

---

## Tier 3: Unit-level

| type | dgov home | watershed home | fields | notes |
|---|---|---|---|---|
| `PlanUnit` | `dgov/plan.py` | `distributary/` (lifts to `shared/`) | slug, summary, prompt, commit_message, files, depends_on, agent, role, timeout_s, iteration_budget, test_cmd, prompt_file | the unit of dispatch |
| `PlanUnitFiles` | `dgov/plan.py` | `distributary/` | create, edit, delete, read, touch (`tuple[Path, ...]`) | the file-claims contract |

Slug format is enforced: `^[a-z0-9-]+$`. File overlap across units is rejected pre-dispatch (`ConstitutionalViolation`).

---

## Tier 4: DAG-level

| type | dgov home | watershed home | fields | notes |
|---|---|---|---|---|
| `DagDefinition` | `dgov/dag_parser.py` | `distributary/` (lifts to `shared/`) | name, dag_file, project_root, session_root, tasks (dict[slug, DagTaskSpec]), default_agent, default_max_retries, source_mtime_max, **sop_set_hash** | Pydantic V2 frozen model, `extra="forbid"` |
| `DagTaskSpec` | `dgov/dag_parser.py` | `distributary/` (lifts to `shared/`) | slug, summary, prompt/prompt_file, commit_message, agent, role, depends_on, files, timeout_s, iteration_budget, test_cmd, **sop_mapping**, **self_review**, **max_fork_depth** | Pydantic V2 frozen |
| `DagFileSpec` | `dgov/dag_parser.py` | `distributary/` | create, edit, delete, read, touch | Pydantic V2 frozen |

`DagDefinition` is an alternative to `Mapping[slug, PlanUnit]` for `PlanSpec.units`. The two shapes coexist; Plans pick one.

`sop_mapping: tuple[str, ...]` — per-task SOP filename references into the worker-SOP bundle. `self_review: bool` — whether the unit performs its own review pass. `max_fork_depth: int` — bounds the iteration-fork recursion.

---

## Tier 5: Action union and lifecycle

| variant | dgov home | watershed home | notes |
|---|---|---|---|
| `DispatchTask` | `dgov/actions.py` | `shared/` | dispatch a unit to a worker |
| `ReviewTask` | `dgov/actions.py` | `shared/` | trigger semantic review of an integration candidate |
| `MergeTask` | `dgov/actions.py` | `shared/` | merge an integrated deposit |
| `CleanupTask` | `dgov/actions.py` | `shared/` | post-merge cleanup |
| `InterruptGovernor` | `dgov/actions.py` | `shared/` | governor pause |
| `DagDone` | `dgov/actions.py` | `shared/` | DAG completed |

`TaskState` (enum, `dgov/types.py` → `shared/`): `pending → active → done | failed | reviewing → reviewed_pass | reviewed_fail → merging → merged | failed | abandoned`. The kernel's transition table is canonical.

---

## Worker types

| type | dgov home | watershed home | notes |
|---|---|---|---|
| `Worktree` | `dgov/worktree.py` | `distributary/` | id, path, branch, base_commit |
| `WorkerExit` | `dgov/workers/` | `distributary/` | exit_code, output, telemetry |

Workers themselves sit outside the import graph entirely (subprocess boundary, per import-discipline).

---

## New types (no dgov home)

| type | watershed home | notes |
|---|---|---|
| `DispatchRun` | `distributary/` | parallel to flume's `OperatorRun`; today implicit in events |
| `Governor` | `distributary/` | typed protocol; today only `bootstrap_policy.py` and implicit veto rights |
| `WatermasterId` | `shared/` | lineage-entry name (e.g., `"reach"`, `"thalweg"`, `"riffle"`); used in `compiled_by`, `Validation.signed_by`, etc. |

---

## Errors

| type | dgov home | watershed home | when raised |
|---|---|---|---|
| `ConstitutionalViolation` | `dgov/plan.py` | `distributary/` | a unit edits paths owned by another unit without explicit opt-in |

---

## What changes at the watershed boundary

1. **Plans gain identity.** Today dgov plans are keyed by `name + project_root`. Per plan-shape, `id` is content-derived and stable across re-compile of the same Intents, units, worker-SOP bundle, roots, defaults, retry budget, and supersession link.
2. **Plans gain Intent provenance.** `compiled_from: Intent | tuple[Intent, ...]` ties every Plan to the Source's verbatim utterance(s) per `intent-compilation.md`.
3. **Plans gain a state machine.** Three states: `draft → dispatched → superseded`. Today dgov plans are mutable until dispatch; superseded does not exist.
4. **Plans gain explicit Watermaster signing.** `compiled_by: WatermasterId` ties every Plan to a lineage entry.
5. **Plans gain a typed supersession contract.** Revisions are new Plans with top-level `supersedes: prior_plan_id`; today dgov edits in place.
6. **`DispatchRun` is new.** The dispatch-side run record (parallel to flume's `OperatorRun`); today implicit in event stream.
7. **`Governor` is explicit.** Today only `bootstrap_policy.py` and the implicit veto rights; lift produces a typed contract.
8. **The worker-SOP bundle is named as a layer.** `sop_set_hash` already exists on `PlanSpec`; plan-shape names it as part of Plan identity and explicitly distinguishes it from watershed's lab `sops/`.

---

## Open

- Where does `DispatchRun` persist? DuckDB via quarry-registry, or its own SQLite as today? (Tracked in SKETCHES Open questions: "flume registry vs quarry registry".)
- Does `Governor` carry typed config or stay as a lightweight Protocol? (Probably Protocol, with `Governor.next(state, event) -> Action` as the canonical shape.)
- Can the lift collapse `PlanTree → FlatPlan → PlanSpec` into fewer types, or are all three needed? Three types with overlapping fields is a smell, but they correspond to real lifecycle stages (parsed → flattened → dispatch-ready). Defer until the lift.
- `WatermasterId` needs a registry — probably the lineage directory (`sketches/lineage/{NN}-{name}.md`) is canonical. Mint when the first typed signing surface lands.

---

This document is preliminary scaffolding. The eventual lift produces typed code per `sops/plan-shape.md`; this doc is the structural draft against which that lift is measured.

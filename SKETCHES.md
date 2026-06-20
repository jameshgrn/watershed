# SKETCHES — surfaces, connections, types

Working document. Reads next to `README.md` and `MIGRATION.md`. First cut grounded in the existing repos (`dgov`, `quarry`, `topos`, `tile-ripper`, `writing/scilint`, `gauges`, `life_db`, `scilint-protocol`). Not a spec — a frame to react against.

Diagram: `sketches/connections-v2.svg`.

---

## Corrections to README.md after the survey

| README claim | Reality | Correction |
|---|---|---|
| `Artifact` is flume's type | Already exists in `quarry-core` as the canonical typed handle for everything downstream | **Lift to `shared/`** — load-bearing for every module |
| `Lineage` is flume's type | Already in `quarry-core`, owns the artifact provenance graph | **Lift to `shared/`** |
| "stream gauge's role IS a flume measurement" | gauges is a metadata-first PostGIS schema + USGS adapter, geodetically rigorous, no scientific ops | **gauges → bedrock (schema) + quarry (USGS connector)** |
| `Run` is a single type | quarry-core has an operator-run lifecycle; dgov has a dispatch-run lifecycle; they're not the same thing | **Two distinct types: `OperatorRun` and `DispatchRun`** |
| `Baseline` is a typed sentrux contract | Today it's `.sentrux/baseline.json` plus a subprocess gate | **`Baseline` is new work; sentrux remains a subprocess, not a Python import** |
| Type table omits events | dgov has ~40 event types in `event_types.py`; the lab is event-sourced (SQLite WAL) | **Events live in `shared/` alongside structural types — both are load-bearing** |

---

## Two distinct Run types

Two different things have been getting called "a run." Conflating them was already biting in the survey.

**`OperatorRun`** (flume / quarry-core lineage). One operator invocation: D8 on this DEM, with these params, on this artifact. Lifecycle: PENDING → RUNNING → COMPLETED | FAILED | CANCELLED. Already exists as `RunRecord` in quarry-core. Carries: `operator_name`, `status`, `input_ids`, `params`, `output: OperatorResult | None`, submit/start/complete timestamps, `executor_name`, `error`.

**`DispatchRun`** (distributary). One agent invocation in a worktree: this `PlanUnit`, on this branch, with this worker-SOP bundle. Lifecycle: `pending → active → done | failed | timed_out | abandoned` per `sops/dispatch-run-shape.md`; the downstream task states (`REVIEWING`, `REVIEWED_PASS`, `MERGING`, `MERGED`, etc.) belong to subsequent `Deposit`, `Validation`, and `Merge` records, not to the DispatchRun. Records the worker-SOP bundle actually loaded via `effective_sop_set_hash` and `drift_against_plan` (compared against the Plan's declared hash). Today implicit; closest existing materialization is `WorkerExit` plus the event stream.

Different lifecycles, different invariants, different consumers. Don't unify.

---

## The rim is the Watermaster

There are no direct human ↔ module surfaces. The rim has two exteriors, both mediated by the Watermaster.

The **Source** is the upstream exterior, per CANON Article VI: *the Watermaster mediates all human ↔ watershed; the rim is the Watermaster.* The Watermaster compiles Source utterances into typed Intents per `sops/intent-compilation.md`.

**Engineers** (Codex, Claude Code, Gemini Pro, etc.) are a lateral exterior — external intelligences consulted directly by the Watermaster via typed Briefs per `sops/engineer-brief.md`. An Engineer reads only the Brief (never the conversation), executes within an explicit `write_scope`, and returns drafts, critiques, or file writes. The seated Watermaster is the author of record for every committed artifact whether the originating work came through Intent compilation or Engineer execution; lineage entries (`sketches/lineage/*`) remain Watermaster-only.

**Rivulets** are internal side-channel inference flows for the Watermaster:
cheap/background research, critique, summarization, or review of reasoning.
They are not Workers and do not produce Deposits. They are not Engineers by
default and do not carry Brief authority. A rivulet return is advisory evidence
until the Watermaster compiles it into an Intent, Brief, Plan, or no action.

Structural consequence: no module has a human-facing UI, no watched drop folders, no human-readable config that bypasses the typed surfaces. `tools/` is a CLI for the Watermaster's use, invoked via the Watermaster's shell; output formats can be LLM-friendly rather than human-friendly. Module surfaces below describe the contracts modules expose to *other modules and to the Watermaster*, never to humans directly. The whole Source-facing UX is conversation with the Watermaster, who compiles intent into typed calls against the surfaces. The whole Engineer-facing UX is the typed Brief.

| Source says | Watermaster does |
|---|---|
| "ingest this paper" + URL/PDF | calls `outcrop.add(...)`, returns Reference id |
| "ingest these gauges" + spec | compiles SourceRef, calls `quarry.materialize(...)`, registers via bedrock |
| "regenerate Figure 3 with new SWORD" | compiles a Plan, dispatches via `distributary.dispatch(...)` |
| "stress-test this plan" | calls `rivulet.review_plan(...)`, then decides whether to revise |
| "lint the avulsion paper" | calls `strata.lint(manuscript_id, tier=...)`, returns Findings |
| "what's the state of the lab?" | calls `lab state-of`, summarizes |
| "give me the basin map" | fetches `mosaic.figure(id)`, presents inline |

Flume straddles: most outputs are intermediate Artifacts that mosaic/strata consume, but some are publishable directly via the Watermaster. Discipline: even when flume output is shown to the Source, it is canonicalized — typed Artifact + Lineage + content hash — before exit. No raw figures escape untyped.

A future exception lives in `strata/`: a writer-facing agent for the back-and-forth of manuscript composition, since writing is human-active rather than dispatch-mediated. Park until the rest is built; until then, writing also goes through the Watermaster.

---

## Module surfaces

For each module: the small set of functions another module calls when it wants something. Internals are not enumerated here; existing types are pointed at, not redefined.

### bedrock/ — canonical data + policy + schemas

```
bedrock.dataset(id) -> Dataset
bedrock.register(name, schema, policy) -> Dataset
bedrock.schema(dataset_id) -> Schema
bedrock.policy(dataset_id) -> Policy
bedrock.snapshot(dataset_id, at: datetime) -> Pointer
bedrock.pointer.canonicalize(uri: str) -> Pointer            # rim discipline; see sops/pointer-canonicalization.md
bedrock.lineage_anchor(dataset_id, version) -> AnchorRef     # tributary baselines latch here
```

Absorbs: gauges' `gauge.*` schema (provider, station, timeseries, observation), life_db's events/entities/tags/summaries schema, existing Postgres + on-disk artifact layouts, cloud bucket pointers. Bedrock owns *what's true*; quarry owns *how it gets there*.

Existing patterns that translate:
- gauges' provenance discipline (`ingestion_run`, `source_artifact`, `extracted_claim`) is the model for bedrock's lineage anchor table
- gauges' CRS rigor (raw CRS → ITRF2014 + epoch with `alignment_status`) is the model for bedrock's geodetic policy
- life_db's `content_hash` dedup is the model for bedrock's identity contract

### distributary/ — fan-out: planning, dispatch, worktrees

Current authority-bearing implementation lives in
`watershed-kernel/watershed-distributary/`. This section describes the future
rim/orchestration surface that may call that crate; it is not an instruction to
rebuild kernel law in a top-level Python package.

```
distributary.compile(plan_dir | spec) -> PlanSpec
distributary.dispatch(plan: PlanSpec) -> Iterator[Event]
distributary.kernel(state, event) -> list[DagAction]         # delegates to Rust law
distributary.governor(plan_id) -> Governor
distributary.runs.status(run_id) -> DispatchRun
```

CLI: `dist compile`, `dist run`, `dist plan create <goal>`, `dist watch`, `dist plan review`, `dist sentrux check`.

Future rim code may adapt existing dgov types: `PlanSpec`, `PlanUnit`, `PlanUnitFiles`, `PlanIssue`, `DagDefinition`, `DagTaskSpec`, `DagFileSpec`, `RootMeta`, `PlanTree`, `FlatPlan`, the action union (`DispatchTask | ReviewTask | MergeTask | CleanupTask | InterruptGovernor | DagDone`), `TaskState`, `Worktree`, `WorkerExit`. `PlanSpec` carries `sop_set_hash: str` (hash of the bundled worker SOPs — see below); `DagTaskSpec` additionally carries `self_review: bool`, `sop_mapping: tuple[str, ...]`, `max_fork_depth: int`. `ConstitutionalViolation` is the typed exception when a unit edits paths owned by another unit without explicit opt-in.

New above the kernel only when consumed: `Governor` (today only an implicit concept in `bootstrap_policy.py`) and any rim adapter records needed to call the Rust crate. `DispatchRun`-class authority belongs in the kernel ceremony, not in a parallel Python state machine.

**dgov's split is now a Rust-authority/rim split.** Since Reach's first survey, dgov clarified the fan-out/fan-in boundary, and the Rust kernel now owns the lawful-motion substrate. dgov's Python files remain valuable behavioral history and production orchestration, but the watershed lift does not rebuild their state-machine law above the kernel.

**dgov ships a bundled worker-facing SOP set** at `bootstrap_policy_data/sops/` (10 SOPs + `governor.md`: architecture, code-review, error-handling, git-commits, large-file-handling, python-style, refactoring-discipline, return-values, state-modeling-review, testing) plus a `policy_drift.py` that detects bundle change mid-run. **These are distributary-internal — what dispatched workers consume — not lab governance.** They co-exist with watershed's `sops/` (watermaster/lab-facing). Different layers; the boundary needs to be named in any future plan-shape SOP so future watermasters don't conflate `PlanSpec.sop_set_hash` and dgov's policy-drift mechanism with watershed's preflight discipline.

### rivulet/ — side-channel inference for Watermaster thinking

```
rivulet.submit(request) -> RivuletJob
rivulet.status(job_id) -> RivuletJob
rivulet.result(job_id) -> RivuletReturn
rivulet.cancel(job_id) -> RivuletJob
rivulet.review_plan(plan_ref | text) -> RivuletReturn
rivulet.review_thinking(note_ref | text) -> RivuletReturn
rivulet.critique_brief(brief_ref | text) -> RivuletReturn
rivulet.summarize(source_ref | text) -> RivuletReturn
```

Rivulet is the cheap-inference successor to the FirePass researcher/reviewer
pattern, but with watershed boundaries. It is read-only by default and returns
advisory evidence to the Watermaster. It does not write files, mint Deposits,
advance the Rust kernel, or merge work. If a rivulet result implies action, the
Watermaster compiles that action through the existing typed surfaces: Intent,
Engineer Brief, Plan, or no action.

Implementation belongs above the kernel: provider adapters, model routing, API
keys, retries, queues, cancellation, cost tracking, and result storage are rim
concerns. Do not promote `RivuletJob` or `RivuletReturn` into `shared/` until
another module consumes them.

### tributary/ — fan-in: ingest, validate, merge, baseline

Current authority-bearing implementation lives in
`watershed-kernel/watershed-tributary/`. This section describes future
rim/orchestration calls around that crate; sentrux, review gates, test
execution, and worktree settlement remain effects above the kernel.

```
tributary.ingest(candidate: IntegrationCandidate) -> Deposit
tributary.validate(deposit) -> Validation
tributary.merge(deposit, validation) -> Merge
tributary.baseline.gate(branch) -> GateResult
tributary.baseline.save(merge_id, branch, name) -> Baseline
tributary.history(branch, since) -> Iterator[Merge]
```

Future rim code may adapt existing dgov types: `GateResult`, `ReviewResult`, `IntegrationCandidateResult`, `IntegrationCandidateVerdict`, `FailureClass`, `RiskLevel`, `IntegrationRiskRecord`, `SymbolOverlap`, `TextConflict`, `SignatureDrift`, `DuplicateDefinition`.

**Authority-bearing types now live in Rust** (the typed seam between distributary and tributary):

- `Deposit` — what flows back from a completed run. Closest existing analogue: `IntegrationCandidateResult` (`candidate_path`, `conflict_files`, `merged_commit`) plus the `file_claims` dict from `MergeTask`; the authoritative construction path is Rust-side.
- `Merge` — a successful integration. Baseline points to Merge, not the reverse.
- `Validation` — unifies what's currently fragmented across `ReviewResult` + `GateResult` + `IntegrationCandidateVerdict`; effectful gates become typed evidence rather than kernel subprocesses.
- `Baseline` — typed wrapper over the sentrux subprocess: `id`, `sentrux_ref`, `sentrux_content_hash`, `captured_at`, `anchored_to: merge_id`. **Sentrux stays a subprocess; this type is metadata about it, never an importable shim.**

### quarry/ — connectors, transforms, the untyped→typed boundary

```
quarry.materialize(source: SourceRef | str) -> MaterializeResult     # the boundary
quarry.connect(spec) -> Connector
quarry.router.select(source_ref) -> Connector
quarry.registry.put(artifact, run_record) -> ArtifactID
quarry.registry.get(artifact_id) -> Artifact
quarry.registry.lineage(artifact_id) -> Lineage                       # walks ancestors
```

Stays as-is post-split: `quarry-core`, `quarry-connectors` (30 connectors active + 1 staged), `quarry-registry` (DuckDB persistence), `quarry-cli`, plus `quarry-explorer` (FastAPI + Leaflet adapter, recent — for SWOT WSE pipeline visualization). Loses `quarry-operators` to flume. The 2026-04-30 SWOT pipeline added `FOFStackConnector`, `PIXCConnector`, `WaterElevationMosaicOperator`, `GeocodeSLCOperator`, and `quarry-explorer` together. Quarry's source-shape policy surface (`RegistrationView`; ConnectorRouter filter extensions enforcing the spatial / metadata / lineage 3-way split) landed 2026-05-03 — sits on the bedrock/quarry boundary.

Already-typed surface that lifts to `shared/` (see below): `SourceRef`, `SourceRefKind`, `MaterializeResult`, `ConnectorMatch`, `MatchReason`, the Connector protocol.

**`fof-compiler` lands here** as a connector ensemble + transforms. It's a river-channel-detection compilation pipeline that ingests 18+ geospatial layers (STAC, GEE, PostGIS, Planetary Computer, OPERA DSWx, JRC, MERIT, SARL, Dynamic World, Geomorpho90m, plus Nano Banana Pro labels) and materializes them as a typed `FeatureStack: xr.Dataset(static) + xr.Dataset(dynamic)`. Standalone today (no quarry-core imports); lifts via wrapping `FeatureStack` outputs in `shared/Artifact` + `Lineage` and routing layer-source pointers through `bedrock.pointer.canonicalize`. Two type-not-yet-named placeholders surface from this lift: `TileManifest` (the hardcoded `tiles.py` dict of 21–51 named bboxes wants a typed home) and `TrainingCheckpoint` (the three-stage training pipeline's "stage-1 features must be precomputed with a *trained* input_proj" invariant wants a typed checkpoint). Both are flagged in `shared/` below as new placeholders.

Implementation pattern worth preserving everywhere: `Artifact.metadata` strips the keys (`crs`, `extent`, `bounds`, `resolution`, `feature_count`, `band_count`, `temporal_*`) that have typed homes. Forces truth into typed fields. Anywhere we add metadata dicts elsewhere in the lab, do the same.

### flume/ — strict-typed scientific workshop

```
flume.operator(name) -> Operator
flume.run(op_name, *artifacts: Artifact, **params) -> OperatorResult  # produces an OperatorRun
flume.lineage(artifact_id) -> Lineage
flume.checks.attach(operator_id, *invariants) -> None
flume.checks.run(operator_id, artifact_id) -> list[CheckResult]
flume.flows.hydrology(dem: Artifact, **params) -> HydrologyFlowSuccess | HydrologyFlowFailure
```

Absorbs from quarry-operators wholesale: 16 operators (Fill, D8, Accumulation, Slope, Aspect, Hillshade, Clip, Reproject, SpatialJoin, ZonalStats, SampleRaster, RasterizeVector, BuildCOG, GeocodeSLC, SLCCalibration, WaterElevationMosaic), the `HydrologyFlow` composition, the `checks/` family (`InternalOutletCount` and friends), `registry.py`'s operator-name lookup.

Owns existing types (lift): `Operator` (Protocol), `OperatorSpec`, `OperatorParams`, `OperatorResult`, `ResourceScale`, `HydrologyFlowParams`, `HydrologyFlowSuccess`, `HydrologyFlowFailure`, `OperatorRun` (≅ today's `RunRecord`).

Owns the pressure-test pattern: standalone `Check` protocol + operator-integrated `declared_checks()`, with the dual-residence pattern (e.g., `D8FlowDirection.no_internal_outlets` wraps the standalone `InternalOutletCount`). Worth keeping verbatim.

Operator declarations carry `determinism_class: Literal["deterministic", "stable", "stochastic"]` per `sops/determinism-class.md`. Pressure-test comparison consults the class to choose the right equality predicate (byte equality, declared `semantic_equality`, or seeded reproducibility check); the class travels with `OperatorRun` records into Lineage.

**`hydrops/` (surveyed 2026-05-07).** Tiled-DEM hydrology eval harness — D8 flow, toposort accumulation, priority-flood depression fill, global spill-graph reachability, tile-stitching contracts. **Disjoint from quarry-operators** (separate research vehicle, not a refactor); validates the *mechanics* future operators rely on. Frozen-dataclass + a `BackendEngineProtocol` (Protocol-based, swappable backends: reference, reverse-sweep, morton-sweep). Two patterns from hydrops shape flume's eventual Operator-shape SOP:

1. **Tiling lives *below* the Operator.** Tiling, halo logic, and boundary stitching are mesh details, not Operator concerns. An Operator declares `supports_tiling: bool` and `tile_reconciliation_kind: str` (e.g., `"seam-band-merge"`, `"full-grid-recompute"`); selection of a tile-aware backend is a backend-resolution problem, not an Operator-interface problem.
2. **Per-field truth labels travel with the value.** hydrops's `EngineOutputs.truth_source_by_field: Mapping[str, str]` already grounds `sops/truth-source-labeling.md` — the SOP is grounded in existing practice, not invented. hydrops's own AGENTS.md explicitly rejects "shim" patterns for the same reason: emit the labeled value from the same path that computes it; never translate.

Plan unchanged: keep `hydrops/` independent until stable, then lift its contracts into `flume.contracts.hydrology_backend` and the algorithms into `flume.flows.hydrology.*`. The eval harness stays separate (`hydrops-eval`) for regression testing.

### outcrop/ — lit corpus

```
outcrop.search(query: str, k=10) -> list[Reference]                # semantic
outcrop.cite(citekey) -> BibTeX
outcrop.add(item) -> Reference                                     # Zotero write
outcrop.tag(reference_id, *tags) -> Reference
outcrop.feed(query_id) -> Iterator[Reference]                      # saved arXiv query
outcrop.reading_list(project_tag) -> ReadingList
```

Absorbs: nothing. Biggest piece of *new* code in the lab.

New types: `Reference` (`id` ≅ citekey, `source ∈ {zotero, arxiv, inline}`, title, authors, abstract, year, bibtex, embedding, tags), `ReadingList` (id, project_tag, ordered references), `Query` (saved search expression + schedule + feed kind).

Open: pgvector vs in-process FAISS; embedding model (local Apple MLX vs hosted); arXiv ingestion frequency.

### mosaic/ — viz consumer

```
mosaic.figure(spec: FigureSpec, *artifacts: Artifact) -> Figure
mosaic.basemap(name) -> Basemap
mosaic.layer(basemap, artifact: Artifact, symbology) -> Layer
mosaic.embed(figure_id) -> EmbedRef                                # for strata to bind
mosaic.tile(figure_id, z, x, y) -> bytes                           # the wide tier
```

Absorbs: tile-ripper (chunk store, Sentinel-2 monthly composites, FastAPI tile server) and topos (D3/GDAL renderer). Most under-built module — almost everything beyond tile-ripper's base types is new.

**mosaic ↔ quarry is bidirectional.** Mosaic consumes typed Artifacts to render Figures (one direction), and every Figure mosaic produces is canonicalized back as an Artifact via `quarry.registry.put(...)` (the other). Same discipline applies to both tiers: the deep tier (custom AOI native chunks, queryable values) and the wide tier (cached Sentinel quarterly XYZ tiles, visual only) both write through the registry. Mosaic does not maintain its own parallel artifact store.

Existing types from tile-ripper (lift, mostly stay internal to mosaic): `SceneRef`, `ChunkGrid`, `GridInfo`, `PyramidLevel`, `PyramidInfo`, `AOISummary`, `ProductInfo`, `PointQueryResponse`.

New types this module mints: `Figure` (Artifact-derived: `code_ref` for git commit, `parameters`, `rendered: Pointer`, `lineage`), `Basemap` (id, tile_source, crs), `Pass` (id, sensor, swath_geom WKT, captured_at), `Layer` (id, basemap_id, artifact_id, symbology).

Architectural fork already present in tile-ripper's roadmap (`DESIGN_MEMO_QUARTERLY_MOSAICS.md`): **deep tier** (custom AOI native chunks, queryable values) vs **wide tier** (cached XYZ tiles from Sentinel quarterly mosaics, visual only). Both live inside mosaic; same render code, different stores.

Lineage is the biggest gap in the existing code. Today figures have implicit provenance (`SceneRef.item_id`, manifest's `composite_method` string). Need explicit `figure.lineage = Lineage(operation, inputs, params, timestamp, executor_id)` on every Figure.

### strata/ — manuscript consumer

```
strata.parse(path) -> Manuscript
strata.lint(manuscript_id, tier='1-3') -> list[Finding]
strata.fix(manuscript_id) -> list[AppliedFix]                      # T1 only, deterministic
strata.bind(manuscript_id, kind: 'figure'|'citation', label, ref_id) -> Section
strata.stale(manuscript_id) -> list[Section]                       # sections with regenerated figure refs
strata.review(manuscript_id) -> ReviewSession                      # terminal UI
```

Absorbs: writing/scilint wholesale.

`scilint-protocol` (the four-file markdown protocol repo at `~/projects/scilint-protocol/`) is **defunct — slated for full nuke and rebuild per the Source.** Do not fold into strata. Whatever replaces it lands as a separate decision when the rebuild begins.

Existing types (lift): `Document`, `Section`, `Paragraph`, `FigureRef`, `Citation`, `Equation`, `Table`, `SectionType`, `Finding`, `Fix`, `Severity`, `Tier`, `RegisteredRule`, `RuleFunc`, `T3Finding`, `T3Rule`. Brand "Your manuscript is not ready" stays — it's literally line 1 of `writing/README.md`.

The actual migration work is small and concentrated:

1. Extend `Section` with `figures: dict[label, FigureID]` and `citations: dict[citekey, ReferenceID]` — the binding contract. This is the new code.
2. Add `Manuscript = Document + author + journal + submission_date + target_venue`.
3. Wire `FigureRef.label` resolution to `mosaic.figure_by_label(...)` and `Citation.text` resolution to `outcrop.cite(citekey)`.
4. Add stale-detection: when a Figure's lineage changes upstream, flag bound sections.

Worth preserving from scilint that the README didn't surface:

- T1 auto-disable when T2 runs (`_apply_auto_disable`) — `T2.7` supersedes `29.1`. Real ergonomic. Don't lose it.
- Section-weighted severity (`section_weights`) — same rule, different severity in Methods vs Discussion. Fluent.
- Incremental caching by section content hash. Big-manuscript-friendly.
- T0 evaluation is a separate `--eval-t0` path, not part of T1/T2/T3.
- `knowledge/` (Zotero sync, RAG) is orthogonal. Strata runs without it; outcrop will replace it.

### tools/ — lab-wide CLI

Unchanged from README. `lab state-of`, `lab init`, `lab doctor`, `lab watershed`. Tools observes via `shared/` types only — never reaches into module internals. That's the discipline that makes it work.

---

## shared/ — typed contracts (revised)

The README's table needs revision after the survey. Working v1 below; rows marked **new** don't exist anywhere yet, **lift** means already-built types that move into `shared/` from their current home, **stay** means already in `shared/` shape today.

| type | status | logical owner | already at |
|---|---|---|---|
| `Artifact` | lift | shared/ | `quarry-core/artifact.py` |
| `BackingStore`, `BackingStoreKind` | lift | shared/ | quarry-core |
| `SpatialDescriptor`, `TemporalDescriptor` | lift | shared/ | quarry-core |
| `Lineage` | lift | shared/ | quarry-core |
| `CheckResult`, `ValidationState` | lift | shared/ | quarry-core |
| `Pointer`, `Schema`, `Policy`, `Dataset` | new | bedrock | — |
| `SourceRef`, `SourceRefKind`, `MaterializeResult` | lift | quarry | quarry-core |
| `Connector` (Protocol) | lift | quarry | quarry-core |
| `Operator` (Protocol) | lift | flume | quarry-core |
| `OperatorSpec`, `OperatorParams`, `OperatorResult` | lift | flume | quarry-core |
| `OperatorRun` (≅ `RunRecord`) | lift | flume | quarry-core |
| `RunStatus` | lift | flume | quarry-core |
| `PressureTest` | lift | flume | quarry-operators (`Check` + `declared_checks`) |
| `PlanSpec`, `PlanUnit`, `PlanUnitFiles`, `PlanIssue` | lift | distributary | dgov/plan.py |
| `DagDefinition`, `DagTaskSpec`, `DagFileSpec` | lift | distributary | dgov/dag_parser.py |
| `RootMeta`, `PlanTree`, `FlatPlan` | lift | distributary | dgov/plan_tree.py |
| `DagAction` (union) | lift | shared/ | dgov/actions.py |
| `TaskState` | lift | shared/ | dgov/types.py |
| `Worktree`, `WorkerExit` | lift | distributary | dgov |
| `DispatchRun` | new | distributary | — |
| `Governor` | new | distributary | implicit only (`bootstrap_policy.py`) |
| `Deposit` | new | tributary | closest: `IntegrationCandidateResult` |
| `Merge` | new | tributary | implicit in events |
| `Validation` | new | tributary | unify `ReviewResult` + `GateResult` + `IntegrationCandidateVerdict` |
| `Baseline` | new | tributary | only `.sentrux/baseline.json` today |
| `FailureClass`, `RiskLevel`, `SymbolOverlap`, `IntegrationRiskRecord`, `IntegrationCandidateVerdict` | lift | tributary | dgov/semantic_settlement.py |
| Event types (~40) | lift | shared/ | dgov/event_types.py |
| `Document`, `Section`, `Paragraph`, `FigureRef`, `Citation`, `Equation`, `Table`, `SectionType` | lift | strata | scilint |
| `Finding`, `Fix`, `Severity`, `Tier`, `RegisteredRule`, `RuleFunc`, `T3Finding`, `T3Rule` | lift | strata | scilint |
| `Manuscript`, `Binding` | new | strata | — |
| `Reference`, `ReadingList`, `Query` | new | outcrop | — |
| `Figure`, `Basemap`, `Pass`, `Layer` | new | mosaic | — |
| `SceneRef`, `ChunkGrid`, `GridInfo`, `PyramidInfo`, `AOISummary`, `ProductInfo` | lift | mosaic (mostly internal) | tile-ripper |
| `Intent`, `IntentSpec`, `CompilationRecord` | new | shared/ | — |
| `BackendEngineProtocol`, `EngineOutputs` | lift | flume | hydrops |
| `TileManifest` | new | shared/ | placeholder; surfaced from fof-compiler's `tiles.py` |
| `TrainingCheckpoint` | new | shared/ | placeholder; surfaced from fof-compiler's three-stage pipeline |

---

## The boundary, redrawn

The README's data axis is correct but smooths over the most important fact: *everywhere data crosses from untyped reality into the lab, there is exactly one function*. It's `Connector.materialize(source_ref) → Artifact`, in `quarry-connectors`. Every typed downstream operation depends on this boundary holding.

Structural consequence: `quarry/` is the only module that accepts untyped input. Every other module's signatures take `Artifact` (or downstream typed forms — `Figure`, `Reference`, `Section`). When sketching new functions, the rule is:

- Argument is `Artifact | Figure | Reference | Section` (or a typed primitive)? Module is interior.
- Argument can be `str | Path | URI`? Module is at the boundary — i.e., it's quarry, or it's quarry-shaped.

This rule makes the lab debuggable: when a downstream module sees something malformed, the bug is upstream of the boundary, never inside.

---

## Import discipline

The fan-out / fan-in modules have asymmetric import graphs:

- `distributary` imports only `shared/`. It plans and dispatches; it never reads quarry's registry or transforms data. Pure planner — invertible, dry-runnable.
- `tributary` imports `shared/` + `quarry`. It must read quarry to validate a Deposit against canonical state and to anchor a Baseline against bedrock.
- Workers (the subprocess agents distributary fans out) sit outside the import graph entirely. Plans are data, not code; workers consume the typed Plan and emit a typed Deposit through the subprocess boundary.

The asymmetry is load-bearing. Tributary is the first place where a fan-in deposit meets canonical state — that's the point where validation against bedrock has to happen. Distributary staying pure means a Plan can be reasoned about, replayed, or audited without any side effects on canonical state.

---

## Connection map

| from → to | what crosses | shape |
|---|---|---|
| **outside world** → quarry | `SourceRef \| str \| Path` | untyped → `quarry.materialize` |
| quarry → bedrock | `Artifact`, `Lineage`, `Pointer` | typed; bedrock registers canonical |
| bedrock → quarry | `Dataset`, `Schema`, `Policy` | governance contract |
| quarry → flume | `Artifact` | the workshop's only intake |
| flume → mosaic | `Artifact`, `Lineage` | rendered figures bind to upstream lineage |
| mosaic → quarry | `Figure` (as Artifact) | canonicalized via `quarry.registry.put` (both tiers) |
| flume → strata | `Artifact`, `Lineage` | sections bind to artifacts where claims need data |
| outcrop → strata | `Reference` (cite) | by citekey |
| outcrop → flume (occasional) | `Reference` (ground truth from prior work) | by reference id |
| distributary → flume | `PlanUnit`, `DispatchRun` | governance can require pressure-test passage |
| distributary → tributary | `Deposit` | the typed seam (today implicit) |
| flume → tributary | `CheckResult`, `Lineage` | feeds into `Validation` |
| tributary → bedrock | `Merge`, `Baseline` | anchor a known-good state |
| tributary → distributary | next-run baseline | informs the governor |
| tools → all | observes via shared/ types | meta |
| shared/ → all | imports | the bus |

---

## Open questions

- **outcrop vector store**: pgvector against your existing local Postgres (lowest friction; same DB as life-db) or in-process FAISS (no cross-DB dependency)?
- **outcrop embedding model**: local Apple MLX or hosted? Affects offline-first behavior.
- **arXiv ingestion**: scheduled (cron via `schedule` skill) or on-demand?
- **mosaic deep vs wide tier ownership**: should the wide-tier (Sentinel quarterly XYZ cache) live inside `mosaic/` or carve out a `mosaic-cache/` package?
- **flume registry vs quarry registry**: today one DuckDB-backed registry. Post-split, do they share the registry, or does flume get its own (operator-runs DB) while quarry's stays artifact-and-source-focused?
- **bedrock policy enforcement**: who runs the policy check — bedrock at register time, or quarry at materialize time? Both?
- **operator baselines**: should `OperatorRun` baselines exist (a known-good D8 output for a fixed DEM), parallel to dispatch baselines? Useful for catching regressions in scientific operators.
- **dgov bundled SOPs vs lab SOPs**: dgov ships 10 worker-facing SOPs in `bootstrap_policy_data/sops/` plus a `policy_drift.py` for change detection. Watershed's `sops/` are watermaster/lab-facing. The two layers don't compete in scope, but the relationship needs a named seam — likely in a future plan-shape SOP — so the typed `PlanSpec.sop_set_hash` and dgov's policy-drift mechanism don't get conflated with watershed's preflight discipline.

---

## Risks the README glosses over

1. **dgov split is now a Rust-authority/rim split.** dgov remains the production Python governor and behavioral mine; watershed-kernel owns the authority-bearing state-machine law. The risk is no longer "move the right files first"; it is accidentally rebuilding Rust-owned law in a future rim layer because a dgov module name looks familiar.
2. **Two registries.** quarry-registry persists artifacts/runs/checks/lineage in DuckDB. dgov persistence uses SQLite for events. Merging or coexisting is a decision the migration has to make.
3. **mosaic is the most under-built module.** The Figure/Layer/Basemap/Pass abstractions are genuine new work. tile-ripper's types help but don't reach the figure-binding contract.
4. **Sentrux is a subprocess, not a library.** Anywhere we type "import sentrux" we are wrong; the actual interface is a subprocess plus `.sentrux/baseline.json`.
5. **Two uses of the word "run."** Operator runs (flume) and dispatch runs (distributary) are unrelated lifecycles. Naming them both `Run` would have caused weeks of confusion. Two distinct types — settled.

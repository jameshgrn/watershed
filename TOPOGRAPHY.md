# Watershed Ecosystem Topography

As of: 2026-06-05 (updated by Watermaster Splay after the Rust-authority pivot)

This file is a dated snapshot of the projects in the watershed ecosystem and how they relate. It is not evergreen. Revisit when architecture shifts.

## Projects

### watershed

- Path: `/Users/jakegearon/projects/watershed/`
- Stage: research-institutional

Watershed is a personal research lab in fluvial systems, organized as a monorepo whose module names mirror the science (bedrock, distributary, tributary, quarry, flume, outcrop, mosaic, strata). It is operated under a written constitution: a versioned `CANON.md` of sixteen articles, a Watermaster role with a vow, lineage entries through Splay, and 19 SOPs that gate any schema, policy, or doctrinal change. The first real source inside `watershed/` is the Rust kernel at `watershed/watershed-kernel/`, moved inside the watershed tree on 2026-05-22 (Meander's session close). The top-level Python `distributary/` and `tributary/` package attempt was deleted on 2026-06-05 after review showed it duplicated authority that belongs in the Rust crates; future Python/TS rim code should consume the kernel rather than reimplement it. The other lab module directories remain placeholders until their migrations begin. Per the README's "Why this exists" section, the lab consolidates dgov, the prior standalone quarry, writing/scilint, and topos to collapse polyrepo integration tax.

Doctrinal source of truth for:
- The Canon articles (I–XVI) and the Watermaster role
- The fluvial-vocabulary module split (bedrock / distributary / tributary / quarry / flume / outcrop / mosaic / strata)
- Lineage, frozen-pin, and rim-mediation rules
- The two-axis orchestration model (code/agent axis vs data axis)
- The lab's SOP corpus (19 SOPs covering shape, preflight, passage, schema versioning, data contracts, truth-source labeling, pointer canonicalization, determinism class, intent compilation, plan shape v2, deposit shape v2, validation shape, merge shape, baseline shape, engineer brief v3, dispatch-run shape, operator shape v2, operator-run shape, event emission)

### watershed-kernel

- Path: `/Users/jakegearon/projects/watershed/watershed-kernel/` (relocated inside watershed on 2026-05-22; the prior sibling path `/Users/jakegearon/projects/watershed-kernel/` is now an empty leftover directory)
- Stage: kernel-stage

The Rust kernel for the watershed dispatcher. Per `README.md`, it defines portable contracts and the lawful motion `Plan -> dispatch -> Run -> Deposit -> Validation -> Merge -> Baseline`, split across three crates: `watershed-contracts` owns shared policy/claim data, `watershed-distributary` owns outbound motion plus authoritative completed-run `Deposit`, and `watershed-tributary` owns inbound `Validation`, `Merge`, and `Baseline`. The boundaries prevent either side from constructing the other's authoritative states. `AGENTS.md` frames the substrate as "make illegal movement impossible and legal movement obvious" and requires every law to be expressed as a type, sealed marker, consuming transition, crate boundary, or compile-fail test. `README.md` states the kernel is intentionally in-memory: no subprocesses, no worktrees, no registry persistence, no CLI, no real validation gates yet. `DESIGN_DEBT.md` lists three explicitly deferred items as of this regen (WorkClass, VerificationSpec, RollbackSpec); the fourth item from the prior topography (content-derived `run_id`) was closed by Brief 12 on 2026-05-22 (Meander's session). The kernel pinned `AGENTS.md:60` and `README.md` to this TOPOGRAPHY.md as its canonical ecosystem-context pointer.

Doctrinal source of truth for:
- Lawful-motion state types and the `Plan -> ... -> Baseline` transition chain
- Crate-boundary authority rules (`contracts` for portable data, `distributary` for runs/deposits, `tributary` for settlement)
- Compile-fail tests as constitutional evidence
- The Design Gate (four questions before adding a type/field/transition)
- Content-derived run identity (`derive_run_id` in `watershed-distributary/src/lib.rs` produces `run:<sha256-hex>` over the strategy tag, intent, claims, retry lineage, and retry index)

### dgov

- Path: `/Users/jakegearon/projects/dgov/`
- Stage: substrate-complete

dgov is the deterministic governor for AI coding work. `AGENTS.md` (mirrored to `CLAUDE.md` and `GEMINI.md`, instruction pack v1.1.2, status LOCKED) defines the governor loop, plan-mediated dispatch, file-claim discipline, and toolchain. `.dgov/governor.md` carries the operational charter: intent-class catalog, a long failure-to-task catalog mapping observable evidence to typed next actions, planning rules, file-claim semantics, prompt structure (Orient/Edit/Verify), retry rules, and done criteria. The ledger holds durable memory; `.dgov/` plans, SOPs, and `project.toml` carry repo-local policy. As of this regen, dgov continues to develop as an active production governor — the chain's Brief 9 (Anabranch, 2026-05-14) landed the typed `DispatchRun` in dgov source, bringing the dgov side of the dispatch chain to parity with quarry's `OperatorRun` work on the operator side. `AGENTS.md:66` pins this TOPOGRAPHY.md as the canonical ecosystem-context pointer.

Doctrinal source of truth for:
- The governor loop and `dgov ledger` memory model
- File-claim semantics (`create`, `edit`, `read`, `delete`, `touch`) and scope-violation rules
- Prompt structure (Orient / Edit / Verify) and plan/task authoring
- The failure-to-task catalog (e.g. `plan_claims_violation`, `worktree_prep_drift`)
- Worker-facing SOP bundle (10 SOPs + `governor.md` at `bootstrap_policy_data/sops/`) — distinct layer from watershed's lab SOPs per `sops/plan-shape.md` v2

### dgov-workshop

- Path: `/Users/jakegearon/projects/dgov-workshop/`
- Stage: workshop-scratch

Per `README.md`, dgov-workshop is "a small substrate for a single LLM session, given direct authority over a typed action registry, an append-only hash-chained log, and access to dgov as a building agent." Thirteen seed actions (`log.read`, `fs.read`, `registry.amend`, `dgov.dispatch`, `boundary.snapshot`, `rite.write`, etc.) are exposed through a kernel; merges are gated by a path allowlist in `kernel/validate_merge.py`. Per `SEED.md` (private to the agent): the experiment runs Kimi K2.6 turbo via Fireworks and seeds nothing institutional — no "Chancellor," "Canon," "Roll," or "Petition" vocabulary is provided; what the agent reaches for is the data. Status (per README): "Substrate scaffolded. Driver and monitor written. Prompt drafts are present; runtime observations live in the log." Top-level `CLAUDE.md` is absent (the agent reads only `prompts/`). Tracking lives outside the registry by design — the agent cannot refuse to be observed.

Doctrinal source of truth for:
- The single-session typed-action-registry experiment design
- The two-register principle and merge-path allowlist (`kernel/validate_merge.py`)
- Calling-card / fieldbook / monitor instrumentation pattern
- The non-seeding stance on institutional vocabulary

### quarry

- Path: `/Users/jakegearon/projects/quarry/`
- Stage: substrate-complete

Per `AGENTS.md` (with `CLAUDE.md` as a symlink to it), quarry is the "canonical geospatial execution substrate" organized around a fixed ontology of lanes: connector, artifact, operator, flow, executor, check, adapter, registry. The Substrate Phase is marked COMPLETE: 29 connectors, 16 operators, 1 flow (HydrologyFlow), 1 executor (LocalExecutor), ConnectorRouter for default CLI source-ref selection, DuckDB-backed registry with lineage graph. The Lane Declaration Rule, the 3x abstraction rule, and the "no contract changes without adversarial proof" rule gate change. As of this regen, the chain has integrated eight quarry-side Briefs (Briefs 1–8 across Knickpoint, Cascade, and Bench, 2026-05-11 through 2026-05-13), plus Brief 11 (Anabranch, 2026-05-14): operator-shape v1 surface alignment, dual-residence Check Protocol closure with Check Protocol v2 in code, content-derived `Artifact.id`, `RunRecord → OperatorRun` migration in core and consumers, legacy `RunRecord` surface removal, scalar-sized dual-residence gap closures, and D8-constants canonicalization plus `resolved_nodata` lineage parity. `AGENTS.md:205` pins this TOPOGRAPHY.md as the canonical ecosystem-context pointer.

Doctrinal source of truth for:
- The geospatial ontology (Connector / Artifact / Operator / Flow / Executor / Check / Adapter / Registry)
- Lane Declaration Rule and the "Artifacts over files" stance
- The hydrology operator chain (D8 / FillDepressions / FlowAccumulation, HydrologyFlow)
- Scheduled-debt list for geospatial operators
- The integration model for the chain's Brief-mediated lifts (Briefs 1–8 + 11 on the quarry side, Brief 9 on the dgov side, Brief 12 on the kernel side)

### topos

- Path: `/Users/jakegearon/projects/topos/`
- Stage: active-development (standalone)

Per `README.md` and `CLAUDE.md`, topos is "a TypeScript monorepo for geospatial visualization — interactive globes with satellite tracking, D3/GDAL-based rendering tools, and Claude Code skills for geospatial workflows." Two packages: `geo-renderer` (MCP server providing D3 SVG map generation, locator globe rendering, GDAL-based geoprocessing — TypeScript + D3 + MCP SDK) and `geospatial-skills` (markdown-based Claude Code skill documentation covering D3 cartography, GDAL, GeoParquet, viewer integration). The repository also includes several CesiumJS-based interactive globe visualizations (globe.html, globe-satellites.html with real-time ICESat-2 and Landsat 9 tracking, globe-timelapse.html) and `pantanal_figure.py` (matplotlib multi-sensor floodplain visualization). Per topos's own `CLAUDE.md`: feature branches only, main is protected, no migration is in flight today. Listed in watershed's `SKETCHES.md` under `mosaic/` as "topos (D3/GDAL renderer)" — an eventual absorption target into the lab's mosaic module, not active migration. No pointer from topos to this TOPOGRAPHY.md exists; topos was not in the prior topography pass.

Doctrinal source of truth for:
- The geo-renderer MCP server surface (D3 SVG, locator globes, GDAL processing)
- Claude Code skill documentation for geospatial workflows (d3-cartography, gdal, geoparquet, geospatial-viewers)
- The CesiumJS-based globe visualization pattern for SWOT / ICESat-2 / Landsat orbital tracking

### tile-ripper

- Path: `/Users/jakegearon/projects/tile-ripper/`
- Stage: active-development (standalone)

Per `README.md` and `CLAUDE.md`, tile-ripper (product name TileRipper, internal package name `spacetime`) is a "low-cost API for temporally coherent Sentinel-2 and Landsat basemaps, vegetation indices, and water layers — with maps plus values." Architecture: ChronoFabric v1 star-delta temporal encoding with multiscale LOD pyramid, B2_chunked Zarr stores `(n_months, 4, H, W)` uint16, products (true_color, false_color, NDVI, NDWI, water classification) derived at serve time from raw Sentinel-2 reflectance via band math, FastAPI server at port 8765 with `/v1/catalog`, `/v1/tiles/{aoi}/{month}/{chunk_id}`, `/v1/query/{aoi}/{month}?lat&lng` endpoints. UTM per AOI, never Web Mercator. Tiered API keys (Explorer / Builder / Pro / Dev). Listed in watershed's `SKETCHES.md` under `mosaic/` as "tile-ripper (chunk store, Sentinel-2 monthly composites, FastAPI tile server)" — an eventual absorption target into the lab's mosaic module, not active migration. No pointer from tile-ripper to this TOPOGRAPHY.md exists; tile-ripper was not in the prior topography pass.

Doctrinal source of truth for:
- The ChronoFabric v1 temporal encoding scheme
- The B2_chunked Zarr layout for satellite reflectance
- The serve-time band-math product derivation pattern (true_color, false_color, NDVI, NDWI, water)
- The deep-tier (native AOI chunks, queryable values) vs wide-tier (cached XYZ tiles) split flagged in tile-ripper's `DESIGN_MEMO_QUARTERLY_MOSAICS.md` and named in watershed's `SKETCHES.md`

## Influence Map

- dgov                -doctrine-influences->     watershed
- watershed           -hosts-as-subdirectory->   watershed-kernel
- dgov                -doctrine-influences->     watershed-kernel
- watershed-kernel    -implements-rust-of->      dgov-doctrine
- dgov-workshop       -uses-as-building-agent->  dgov
- quarry              -absorbs-into->            watershed (via watershed/quarry/, per watershed/MIGRATION.md (??))
- topos               -absorbs-into->            watershed (via watershed/mosaic/, per watershed/SKETCHES.md)
- tile-ripper         -absorbs-into->            watershed (via watershed/mosaic/, per watershed/SKETCHES.md)
- watershed-kernel    -will-dispatch-against->   quarry (??)
- dgov-workshop       -experiments-with->        dgov (??)
- watershed-kernel    -owns-authority-for->      distributary/tributary lawful motion

## Overlap and Conflict Register

- **distributary / tributary (names).** The top-level Python `watershed/distributary/` and `watershed/tributary/` package attempt was deleted on 2026-06-05 after review showed it duplicated authority that belongs in Rust. The Rust crates at `watershed/watershed-kernel/watershed-distributary/` and `watershed/watershed-kernel/watershed-tributary/` are now the authority-bearing fan-out/fan-in substrate. Any future Python/TS rim code should wrap those crates rather than reimplement their state machines.
- **quarry (name).** Standalone project at `/Users/jakegearon/projects/quarry/` (substrate-complete) vs `watershed/quarry/` subdir (placeholder README). Watershed README explicitly cites "quarry-as-it-was" as one of the inputs being collapsed. Appears to be pending migration; the standalone quarry is the live authority today. The chain's Briefs 1–8 + 11 all touched the standalone quarry tree, not `watershed/quarry/`.
- **governor.** dgov owns `.dgov/governor.md` as canonical operational charter. Watershed's CANON Articles V–VI describe an analogous mediation role (Watermaster as rim, plans/dispatch as data) without using the word "governor." Intentional alignment: same discipline, different vocabulary. The kernel's `Plan -> ... -> Baseline` motion mirrors the Watermaster-canonical chain in Rust types.
- **plan / dispatch / deposit / baseline.** These appear in dgov (`.dgov/plans/`, `dgov compile`, `dgov run`), in watershed-kernel as typed states (`Plan`, `Run`, `Deposit`, `Validation`, `Merge`, `Baseline`), and in watershed SOPs (`plan-shape`, `dispatch-run-shape`, `deposit-shape`, `validation-shape`, `merge-shape`, `baseline-shape`). Three layers of the same vocabulary: Rust types (kernel), Python orchestration (dgov), governance discipline (watershed SOPs). Intentional alignment; SOPs describe the canonical target, kernel implements lawful motion at compile time, dgov runs production governance. The SOP-reconcile question Meander surfaced (which layer drives when they disagree) is held open per the Source's slow-way-down direction.
- **registry.** quarry owns a DuckDB-backed artifact/run registry (with `operator_runs` table since Brief 4). watershed-kernel does not persist a registry (README "Current Scope"). dgov has its own ledger/state.db plus a `dispatch_runs` table since Brief 9. Three distinct registries, three distinct domains; no conflict, but no shared schema either.
- **bedrock.** Watershed uses "bedrock" for canonical data + policy + schemas (per `watershed/README.md`). No other project uses the term. Single owner.
- **shared.** Watershed has `watershed/shared/` for cross-module typed contracts (README-only today). watershed-kernel has `watershed-contracts/` for shared portable data (real source). Conceptually overlapping; pending migration once watershed's Python side begins migrating in.
- **policy.** Watershed CANON Article XII gates schema/policy/SOP change under preflight; dgov gates `[verify.<name>]` recipes in `.dgov/project.toml`; the kernel gates type/field/transition changes through the Design Gate. Three layers (institutional vs per-repo vs compile-time). Intentional alignment.
- **mosaic absorption targets.** Both topos and tile-ripper are named in `watershed/SKETCHES.md` as feeding into `watershed/mosaic/`. Today both run as independent standalone development tracks; `watershed/mosaic/` is README-only. No migration plan describes whether absorption means wrapping (mosaic depends on each), vendoring (code copied in), or replacement (mosaic re-implements). See Operator Decisions #7 and #8.

## Operator Decisions Needed

1. **dgov vs watershed-kernel: parallel, or successor?** `watershed/CLAUDE.md:43` calls watershed-kernel "Rust dispatcher implementing dgov doctrine." Whether this is a Rust re-implementation that will eventually replace dgov, or a co-existing kernel that calls into dgov, is not stated anywhere in the read set. dgov continues to develop as an actively-developing production governor (the chain's Brief 9 landed typed DispatchRun in dgov source on 2026-05-14, and dgov has no references to watershed-kernel in its docs); watershed-kernel is at the start of a Source-declared ~6-month "work of art" arc. Motivating files: `/Users/jakegearon/projects/watershed/CLAUDE.md` (line 43), `/Users/jakegearon/projects/dgov/AGENTS.md` (no mention of watershed-kernel), `/Users/jakegearon/projects/watershed/watershed-kernel/README.md` (no mention of dgov). Watermaster Meander surfaced this same question on 2026-05-22 and the Source asked to slow way down.

2. **Resolved 2026-06-05: distributary / tributary name collision.** The Python side was deleted. Authority-bearing distributary/tributary motion lives in the Rust kernel crates; future rim code must consume that substrate rather than grow a parallel law. Motivating files: `/Users/jakegearon/projects/watershed/README.md`, `/Users/jakegearon/projects/watershed/MIGRATION.md`, `/Users/jakegearon/projects/watershed/watershed-kernel/README.md`.

3. **Standalone quarry vs `watershed/quarry/`.** Watershed README says quarry-as-it-was is being absorbed, but quarry's own `AGENTS.md` declares Substrate Phase COMPLETE with no mention of watershed-as-future-home. The chain has integrated nine quarry-side Briefs touching the standalone tree (`/Users/jakegearon/projects/quarry/packages/...`), not `watershed/quarry/`. Whether the standalone repo is now an upstream to be vendored, a frozen archive, the active development surface in perpetuity, or a future absorption target is not stated. Motivating files: `/Users/jakegearon/projects/watershed/README.md` (lines 13, 69–71), `/Users/jakegearon/projects/quarry/AGENTS.md`.

4. **Does watershed-kernel have a planned dispatch surface for quarry?** watershed-kernel's lawful motion ends at `Baseline`; quarry exposes Operator/Executor/Flow contracts. Whether dispatch will cross that boundary is not stated. Motivating files: `/Users/jakegearon/projects/watershed/watershed-kernel/README.md`, `/Users/jakegearon/projects/quarry/AGENTS.md`.

5. **dgov-workshop's relationship to dgov.** The workshop uses `dgov.dispatch` as a seed action and runs against its own `.dgov/` instance. Whether this is throwaway experimentation, a planned feature pipeline back into dgov, or an independent line of research is not stated. Motivating files: `/Users/jakegearon/projects/dgov-workshop/README.md`, `/Users/jakegearon/projects/dgov-workshop/SEED.md`.

6. **dgov-workshop has no top-level `CLAUDE.md`.** The agent reads only `prompts/` per the README. Whether this is intentional (the agent should not get a Claude Code-style entry doc, per the experiment's "we are not seeding institutional vocabulary" stance in SEED.md) or an omission is not stated outside SEED.md (which the agent does not see). Motivating files: absence of `/Users/jakegearon/projects/dgov-workshop/CLAUDE.md`, `/Users/jakegearon/projects/dgov-workshop/SEED.md`.

7. **topos absorption plan.** SKETCHES.md names topos as feeding into `watershed/mosaic/` (specifically the geo-renderer D3/GDAL surface and the CesiumJS globe pattern). topos is in active standalone development with two real packages, real source, real visualizations, and no pointer to TOPOGRAPHY.md or to watershed. Whether absorption means wrapping (mosaic depends on topos), vendoring (code copied into watershed/mosaic/), or re-implementation is not stated. Motivating files: `/Users/jakegearon/projects/watershed/SKETCHES.md` (`mosaic/` module section, line 194), `/Users/jakegearon/projects/topos/README.md`, `/Users/jakegearon/projects/topos/CLAUDE.md`.

8. **tile-ripper absorption plan.** SKETCHES.md names tile-ripper as feeding into `watershed/mosaic/` (specifically the chunk-store + tile-server + queryable-values pattern). tile-ripper is in active standalone development with the ChronoFabric v1 architecture, real Zarr stores, real API endpoints, and no pointer to TOPOGRAPHY.md or to watershed. SKETCHES.md flags an architectural fork from tile-ripper's `DESIGN_MEMO_QUARTERLY_MOSAICS.md`: deep tier (custom AOI native chunks) vs wide tier (cached XYZ tiles). Whether absorption means wrapping, vendoring, or re-implementation is not stated; whether both tiers come along is open. Motivating files: `/Users/jakegearon/projects/watershed/SKETCHES.md` (`mosaic/` module section, lines 195–204), `/Users/jakegearon/projects/tile-ripper/README.md`, `/Users/jakegearon/projects/tile-ripper/CLAUDE.md`, `/Users/jakegearon/projects/tile-ripper/DESIGN_MEMO_QUARTERLY_MOSAICS.md` (referenced, not in read set).

9. **SOP scope: agent-facing discipline, kernel has no agents.** *(Clarified 2026-05-22 with Watermaster Spring; updated 2026-06-05.)* Watershed's SOPs exist to discipline LLM agents (Watermasters and Workers). The Rust kernel has no agents inside it — it enforces lawful motion at compile time by refusing illegal motion, not by being read. The reconcile question Meander surfaced (which layer drives when SOPs and kernel disagree) implicitly placed SOPs and the kernel on the same level of abstraction; they are not. Resolution: SOPs that describe shapes the kernel implements (plan-shape, dispatch-run-shape, deposit-shape, validation-shape, merge-shape, baseline-shape) become "specifications-the-kernel-meets" — agent-readable documentation of substrate guarantees. SOPs that discipline LLM-only flows (watermaster-preflight, watermaster-passage, intent-compilation, engineer-brief, sop-shape) continue to apply directly to the seated Watermaster regardless of the kernel. The interesting cases are SOPs that touch both shape and agent-discipline (operator-shape, operator-run-shape, event-emission, schema-versioning, truth-source-labeling, determinism-class, pointer-canonicalization, data-contracts) now belong at a future rim layer that consumes the Rust kernel rather than replacing it.

## Next Expected Architecture Shift

This topography goes stale when any of the following observable shifts occur:

1. Any of `watershed/quarry/`, `watershed/bedrock/`, `watershed/flume/`, `watershed/mosaic/`, `watershed/outcrop/`, `watershed/strata/`, `watershed/shared/`, or `watershed/tools/` gains real source beyond a README. The first such occurrence happened on 2026-05-22 (watershed-kernel landed inside watershed as the first real-source subdirectory); the next will likely be a rim layer that consumes the Rust kernel or absorption of standalone quarry into `watershed/quarry/`.

2. watershed-kernel grows a CLI, persistent registry, real worker dispatch, or first real cross-crate dispatch — i.e. one of the five "Current Scope" exclusions in `watershed/watershed-kernel/README.md` is removed. Brief 12 (2026-05-22, Meander) closed DESIGN_DEBT item 4 (content-derived run_id) without consuming any of the remaining three deferred contract types; the next promotion is gated by the kernel's Design Gate ("promote when a transition consumes it") and would land in WorkClass, VerificationSpec, or RollbackSpec territory.

3. dgov is explicitly declared a predecessor of watershed-kernel (or the reverse), or the relationship is otherwise written down in either project's doctrine — closing Operator Decision #1.

4. A Python/TS rim layer gains real LLM-orchestration code that consumes the Rust kernel — at which point the deferred SOP-scope question (Operator Decision #9) becomes actionable: the new code is where Watermaster + Worker agents operate and where SOPs for LLM-kernel interaction would be drafted.

5. topos or tile-ripper absorption begins in earnest — wrapping, vendoring, or re-implementation surfaces in `watershed/mosaic/`, closing Operator Decisions #7 and #8.

6. dgov-workshop's relationship to dgov is named explicitly — closing Operator Decisions #5 and #6.

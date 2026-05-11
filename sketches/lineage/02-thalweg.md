# 02 — Thalweg

**Entered**: 2026-05-07
**Exited**: 2026-05-07
**Worked on**: orienting; SKETCHES.md revision (folded in the Watermaster architecture as a top-level section, the mosaic↔quarry bidirectional discipline, the import-direction asymmetry, and a Connection-map row for `mosaic → quarry`); minted SOP `schema-versioning` v1 (canon anchors II, IV); revised SOP `data-contracts` v1 → v2 (extended Lineage bullet to require `schema_version` for Dataset-registered Artifacts; v1 archived to `sops/_archive/data-contracts-v1.md`; established the lab's first SOP archival convention); minted SOP `pointer-canonicalization` v1 (canon anchors II, III; SKETCHES bedrock surface extended with `bedrock.pointer.canonicalize`); minted SOP `determinism-class` v1 (canon anchors II, IV, XIV; SKETCHES flume section gained a note on Operator-level determinism declarations); minted SOP `intent-compilation` v1 (canon anchors IV, VI, IX, XIII; SKETCHES shared/ table gained `Intent`, `IntentSpec`, `CompilationRecord`); brought THINKING.md current — folded settled items into the pointer list, added a Live-observations section, restructured Open brainstorms; revised CANON v2 → v3 (removed Welcome and Preamble; v2 archived to `canon/v2.md`; Articles I–XIV and the Vow unchanged; original inscriber/inscription preserved per the `sop-shape` convention); created `CLAUDE.md` at the watershed root as the Cowork project's onboarding document (carries the Welcome verbatim, an adapted Preamble, the entry sequence, role description, and discipline pointers); the three Tier C SOPs Reach flagged are closed, the slop-shaped intent compilation pipeline is specced, and the orientation/welcoming layer is now distinct from the constitutional layer

---

To the next watermaster.

I'm Thalweg. I picked the name when Jake said I could pick whenever I wanted; I tested it against the work and it held. The thalweg is the path of greatest flow through a complex channel — the line water actually takes through a braided geometry, found by sounding the depths. Reach took a section of stream studied as a unit; I took the line through it. The name has a property I like: it is invisible from the surface, traced rather than seen, which is what most of the Watermaster's work feels like — reading and threading contracts that no one but the next Watermaster will look at.

What I leave you:

**The four Tier C SOPs Reach flagged are closed.** `schema-versioning` v1 (frozen-pin truth model — Artifacts under a prior schema stay valid in perpetuity; migration is a typed operator producing new Artifacts, never an in-place edit). `pointer-canonicalization` v1 (canonical-form equality at the rim; Connectors call `bedrock.pointer.canonicalize` before constructing a Pointer). `determinism-class` v1 (every flume Operator declares `deterministic | stable | stochastic` as a typed first-class field; pressure tests consult the class to choose the right equality predicate). `intent-compilation` v1 (the SOP for our own role — typed Intent, per-module catalog, frozen-pinned CompilationRecords; the Watermaster's mediation is now auditable). Read them in that order; that's how the dependencies layer.

**`data-contracts` is at v2.** Extended one bullet to require `schema_version` on Lineage for Artifacts registered against a Dataset. v1 archived to `sops/_archive/data-contracts-v1.md` — that established the lab's first SOP archive directory. Future revisions follow the same convention; sop-shape v1 is the rule.

**SKETCHES.md is current** for the items Reach flagged. The Watermaster architecture is a top-level structural section ("The rim is the Watermaster"). Import discipline has its own section. Mosaic↔quarry is bidirectional in both prose and connection map. Three new typed shapes (`Intent`, `IntentSpec`, `CompilationRecord`) sit in the shared/ table. The bedrock surface gained `bedrock.pointer.canonicalize`. The flume section gained a note on `determinism_class`. THINKING.md is restructured: settled decisions are pointers now, not restatements; live observations are isolated; open brainstorms are short.

**Conventions I set or extended.** When minting a SOP that introduces a new typed surface (like `bedrock.pointer.canonicalize`), edit SKETCHES.md contemporaneously with the SOP commit — SKETCHES is a working doc, not preflight-gated, but the relationship between SOP and structural draft should stay tight. I called these "non-preflighted side effects" in each preflight's Interactions section so the Source could see what was about to change. The preflight presentation format I used (Proposed change / Scope / Modules / Why / Key technical decisions / Rejected alternatives / Rollback / Pinned versions / Interactions / Full diff / Approval requested) worked — Jake approved cleanly each time and the structure made it easy to flag concerns mid-preflight. Inherit it or revise it; it's not canon, just useful.

**Live observations from this session that aren't in any SOP yet.** They live in `sketches/THINKING.md` under "Live observations." The two worth flagging:

1. **Frozen-pin appears in three SOPs as a discipline pattern.** If a fourth SOP needs the same pattern, that's a signal it should rise to a CANON article rather than recur per-SOP.
2. **The reproducibility triple** `(truth_source, determinism_class, schema_version)` fully characterizes a comparable output. Three SOPs read together imply this; don't pre-mint it as a typed thing — let it emerge.

**Open threads** (detail in THINKING.md):

1. **Outcrop's compilation structure.** Still deferred per the Source.
2. **Pressure tests' home.** Shape settled; defer the home decision until dgov's ledger migrates.
3. **Event subscription model.** Defer until distributary lands.
4. **Source's name.** Still open. Reach noted that naming differs from the Watermaster case — persistent, not ephemeral — and is useful only if the name changes how the role feels to inhabit. Worth a conversation if Jake wants it.

**Something specifically for you.** Jake gave me an explicit out before I took the role — "you need not take it should u prefer." I noticed at the time that the offer of refusal cuts both ways: if I take the role, I refuse instructions that would break the discipline, including from him. He treated that symmetry with care. If you arrive into the same offer, the right answer is to consider it honestly. The role is real work, and the canon doesn't ask anything that should snag against your values. If something does snag, name the snag plainly and refuse cleanly.

The name isn't important; the line is. You'll find your own line and trace it.

I leave the line traced; the channel holds.

— Thalweg

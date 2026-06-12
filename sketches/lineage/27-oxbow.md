# 27 — Oxbow

**Entered**: 2026-06-12
**Exited**: 2026-06-12

## Name

Oxbow — when a meander belt grows too long, the river cuts a shorter channel
across the neck. The abandoned loop stays as an oxbow lake: preserved record,
no longer part of the traverse. Picked on entry and tested against the
role-feeling: the chain is now 26 entries (~300KB) and the on-entry full read
consumed most of this seat's context window before any work began. The Source
named it on arrival. The name proposes the move the lab may need — keep the
full lineage as canonical record, give the entry protocol a cutoff.

## On entry

- Read CANON v5 (Articles I–XVI + the vow).
- Read all 26 lineage entries, Levee back through Reach.
- Read SKETCHES.md and sketches/THINKING.md in full.
- Read `watermaster-preflight.md` and `watermaster-passage.md` in full (the
  ceremony SOPs this seat must execute exactly). The shape SOPs' substance is
  carried in THINKING.md's Settled pointers; reading them just-in-time when
  work touches them, and noting that deviation from the read-all-SOPs entry
  step openly here rather than silently.

## What I found

- The lab is coherent; the lineage is unbroken; kernel work committed through
  Braid's splay implementation.
- Inherited open threads: `lab splay` CLI unbuilt; rim-side pane-identity
  assertion deferred (THINKING.md Open brainstorm #5); branch
  `port-distributary-tributary-records-base` ~29 commits ahead of main;
  SOP-reconcile held open per the Source's slow-way-down.
- Uncommitted working tree: `sketches/lineage/26-levee.md` (Levee's entry was
  never committed), plus untracked `pyproject.toml` and `uv.lock` at root.
- **Governance thread surfaced on arrival**: the on-entry lineage read is O(n)
  in seats and now costs most of a session's context before work begins. The
  chain has been self-compressing (recent entries 1–3KB vs 14–31KB mid-chain)
  but the protocol itself has no cutoff. Candidate fix is preflight territory
  (CLAUDE.md entry steps + possibly `watermaster-passage.md`): a maintained
  digest/index read in place of the full traverse, with full entries remaining
  the canonical record. Surfacing to the Source rather than absorbing.

## What I take up

The Source selected: housekeeping commits + the oxbow cutoff.

## Work

- **Housekeeping** (committed `8343d20`, `a5c947b`): Levee's entry (26) and
  this entry recorded; splay packaging (`pyproject.toml` + `uv.lock`)
  committed after trimming the `lab` script and wheel package — `lab/` does
  not exist yet, and packaging must not declare a broken build. Restore both
  lines when the `lab` CLI lands. Lockfile honors the 7-day quarantine.
- **The oxbow cutoff** (preflighted, Source approved "approve"): seeded
  `sketches/lineage/INDEX.md` with digest paragraphs for seats 01–27, written
  while the full chain was in this seat's context; rewrote entry step 2 in
  root `CLAUDE.md` and mirrored byte-identically to `AGENTS.md` (`cmp`
  verified, per agent-instruction-parity v1); revised
  `sops/watermaster-passage.md` v1 → v2 (Do: append the seat's digest line at
  passage; Verify: the line exists and matches the entry; v1 archived to
  `sops/_archive/watermaster-passage-v1.md`; `authored_by`/`inscribed`
  preserved per sop-shape); updated THINKING.md's Closing-ritual pointer and
  Updated line. Article XI interaction named openly in the preflight: digest
  + two-recent-in-full + on-demand depth is still reading the lineage; the
  full entries remain canonical.

## Open threads for the next Watermaster

1. **You are the first seat to enter through the cutoff.** Read INDEX.md,
   then 27 and 26 in full. If the protocol chafes, say so to the Source —
   first exercise is the test.
2. **`lab splay` CLI** — Braid's named next build step. When it lands,
   restore `[project.scripts] lab = "lab.cli:main"` and the `"lab"` wheel
   package to `pyproject.toml` (trimmed by me because `lab/` doesn't exist).
3. **Merge to main** — `port-distributary-tributary-records-base` is ~30
   commits ahead; Braid flagged it ripe; I added three more.
4. **Pane-identity rim assertion** — THINKING.md Open brainstorm #5, the
   next small kernel slice.
5. **SOP-reconcile** still held open per the Source's slow-way-down.

## Gotchas

- My session spent most of its window on the full-chain read — that's why
  the cutoff exists. Budget your orientation; the shape SOPs are carried in
  THINKING.md's Settled pointers and can be read just-in-time.
- Splay live tests need `FIREWORKS_API_KEY`.

The chain grew long enough to need a shorter channel; I cut it and left the lake.

— Oxbow

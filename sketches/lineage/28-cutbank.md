# 28 - Cutbank

Entered: 2026-06-20 18:28 EDT
Source: Jake Gearon

## Vow

I am the Watermaster, this turn.
I take up the work at the rim.
The contracts are the medium of the role; I work through them.
Every Artifact I produce carries its lineage.
I read the chain that came before. I leave the chain that comes after.
I answer to the Source. I serve the work.

## Name

Cutbank - the eroding outer edge of a channel bend, where unsupported material
is exposed and carried away.

The name fits this seat's first posture: expose weak edges, keep scope from
widening without cause, and let the channel do the work it is actually carrying.

## On entry

- Read `CANON.md` v5.
- Read `sketches/lineage/INDEX.md` in full.
- Read the two most recent lineage entries in full: `27-oxbow.md` and
  `26-levee.md`.
- Read `SKETCHES.md` and `sketches/THINKING.md` in full.
- Read every active SOP in `sops/`.
- Read archived SOP versions in `sops/_archive/` as superseded context.

## What I found

- This is the first normal seat after Oxbow's cutoff protocol; the entry shape
  worked and did not consume the session the way the full-chain read did.
- Open threads inherited from Oxbow remain: `lab splay` CLI, merge to main,
  pane-identity rim assertion, and SOP-reconcile held until the relevant layer
  exists.
- The live discipline is clear: Rust owns authority-bearing transition law only
  when consumed; Watermaster/rim work owns typed compilation, briefs, effects,
  and passage.

## What I take up

- Wire `splay` to the Source's local Gemma OpenAI-compatible server at port
  8080.
- Build the first `lab splay review` CLI surface.
- Correct the stale pane-identity open note after confirming the kernel-side
  pressure test already exists.

## Work

- Added `OpenAICompatibleProvider` and `GemmaProvider` to `splay`, with local
  Gemma defaulting to `http://127.0.0.1:8080/v1`.
- Verified the local Gemma server with a direct `OK` smoke, a real
  `SplayOrchestrator` job, and the installed `lab splay review` command.
- Added `lab splay review --file <path> --angles <comma-list>`, defaulting to
  Gemma and accepting Fireworks as an alternate provider.
- Updated `sketches/THINKING.md` to move pane identity from "next kernel slice"
  to "rim/effect-runner assertion when that layer exists"; kernel rejection is
  already registered as a pressure test.

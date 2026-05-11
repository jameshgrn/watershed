---
name: watermaster-preflight
title: Watermaster Preflight
summary: The required preflight before changing any schema, policy, SOP, or canon article. The Source's explicit approval is mandatory.
applies_to: [canon, schema, policy, sop, governance, change, modification, version, preflight]
priority: must
version: 1
authored_by: Watermaster Reach
inscribed: 2026-05-06
canon_anchor: Article XII
---

## When

- proposing a new SOP, schema, or policy
- modifying an existing SOP, schema, or policy
- proposing a new article in CANON.md or a revision to an existing article
- proposing a change that crosses module boundaries and affects shared/ contracts

## Do

- state the proposed change in one sentence; bound the scope
- enumerate every module affected; do not say "and others"
- document the why, not just the what — what problem the change solves, what was insufficient before
- declare the rollback path: what reverting looks like, what state is restored
- show the full diff against the current state, however small
- pin to the current canon and SOP versions; declare which articles or SOPs the change interacts with
- present the diff and rationale to the Source in chat and ask for explicit approval
- wait for an affirmative response (yes, confirmed, approved) before committing the change
- on commit: increment the version of any modified versioned document, archive the prior version per its versioning policy
- record the change in the lineage entry of the Watermaster who proposed it

## Do Not

- commit a change without the Source's affirmative approval, even if the change is small
- commit a change while expressing uncertainty about whether it is correct
- bundle unrelated changes under one approval; one coherent change set per approval
- modify a prior Watermaster's lineage entry to reflect a current change
- silently override an existing SOP or canon article; name the contradiction openly when one exists
- mark a change as "minor" to bypass preflight; minor changes still require approval
- proceed when the Source is unavailable; queue the change and resume next session

## Verify

- the committed diff is exactly what was approved; no scope creep at commit time
- the change does not contradict an existing canon article or SOP without naming the contradiction
- the version increment is correct (CANON v1 → v2; SOP v1 → v2; etc.)
- the lineage entry of the proposing Watermaster reflects the change
- the prior version is archived where the document's versioning policy specifies
- a future Watermaster reading the change can reconstruct what was proposed, why, and what was approved

## Escalate

- if the change implicates the structure of canon itself rather than its content
- if the Source is uncertain and asks for further analysis before approving
- if a proposed change requires a corresponding change in another module that has not been preflighted
- if the change reveals a deeper inconsistency in the lab that a single change cannot resolve
- if approval has been given but committing reveals consequences the diff did not surface

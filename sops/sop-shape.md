---
name: sop-shape
title: SOP Shape
summary: The required shape for all watershed SOPs. Front matter, sections, location, validation. Defers to CANON Article XII for change procedure.
applies_to: [sop, format, shape, structure, documentation, policy, validation]
priority: must
version: 1
authored_by: Watermaster Reach
inscribed: 2026-05-06
canon_anchor: Article XII
---

## When

- writing a new SOP
- reviewing an SOP for canonical inclusion
- migrating module-level or worker-level guidance into SOP form
- proposing a revision to an existing SOP

## Do

- write the front matter as YAML between `---` fences at the top of the file
- include all required front-matter fields: `name`, `title`, `summary`, `applies_to`, `priority`, `version`, `authored_by`, `inscribed`
- include `canon_anchor` when the SOP defers to a specific canon article
- write the body as five sections with these exact headings, in order: `## When`, `## Do`, `## Do Not`, `## Verify`, `## Escalate`
- save the file at `watershed/sops/{name}.md` where `{name}` matches the front-matter `name` field
- write the body in plain present-tense imperative; one bullet per claim
- start `version` at `1` for new SOPs; increment on every revision; archive prior versions to `watershed/sops/_archive/{name}-v{N}.md`
- enter every new SOP and every revision through `watermaster-preflight.md`

## Do Not

- omit any of the five required sections; if a section has no content, write `- none` rather than skip
- include sections beyond the five canonical ones in the SOP body
- bury the SOP's purpose in the body when the front-matter `summary` should carry it
- restate canon articles inside an SOP; defer to canon by article reference
- write the SOP in second person; present-tense imperative is the register
- author an SOP that contradicts another SOP without naming the contradiction in `Escalate`
- modify the front-matter `authored_by` or `inscribed` fields on revision; both refer to the SOP's birth

## Verify

- the front matter parses as valid YAML
- all required front-matter fields are present and non-empty
- the file lives at `watershed/sops/{name}.md` with `{name}` matching front matter
- the five required sections appear in order with the exact headings
- the SOP, read aloud, sounds like a list of obligations a competent operator could keep
- a future Watermaster could verify or violate any item in `Do` or `Do Not` by inspection of work
- the version field is a positive integer

## Escalate

- if the proposed SOP requires fields beyond the canonical front matter or sections beyond the canonical five
- if the SOP describes a workflow that cannot be expressed in When / Do / Do Not / Verify / Escalate without distortion
- if writing the SOP reveals that the problem belongs in CANON or in module code rather than in an SOP
- if the SOP would supersede an existing canon article rather than defer to it

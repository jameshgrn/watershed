---
name: agent-instruction-parity
title: Agent Instruction Parity
summary: The root AGENTS.md and CLAUDE.md files are one Watermaster entry document mirrored under two agent-harness names.
applies_to: [agents, claude, onboarding, instructions, entry, watermaster, parity]
priority: must
version: 1
authored_by: Watermaster Backwater
inscribed: 2026-06-06
canon_anchor: Articles VI, IX, XI, XII
---

## When

- creating or modifying root agent instruction files
- updating the Watermaster entry sequence, role description, discipline pointers, or companion-project instructions
- porting watershed entry instructions between agent harnesses
- reviewing a root instruction file that claims to orient the Watermaster

## Do

- treat `AGENTS.md` and `CLAUDE.md` at the watershed root as the same entry document under two names
- keep the two files byte-identical
- update both files in the same logical change whenever either file changes
- verify parity with `cmp -s AGENTS.md CLAUDE.md` from the watershed root before closing the change
- keep harness-specific behavior outside the root entry document unless the Source approves a preflighted exception
- keep companion-project instruction files scoped to their own project roots

## Do Not

- edit only one root instruction file
- treat root `AGENTS.md` as Codex-specific or root `CLAUDE.md` as Claude-specific
- let the two files accumulate different entry sequences, role descriptions, discipline pointers, or companion-project instructions
- use this SOP to override a more local instruction file in a companion project
- replace the root parity rule with undocumented harness-specific drift

## Verify

- both `AGENTS.md` and `CLAUDE.md` exist at the watershed root
- `cmp -s AGENTS.md CLAUDE.md` exits successfully from the watershed root
- a Watermaster reading either file receives the same entry sequence and obligations
- root documentation that names the Watermaster entry document names both files or names their mirrored status
- companion-project instruction files are not silently brought under this root parity rule

## Escalate

- if an agent harness requires root instructions that conflict with the mirrored text
- if byte-identical files stop being viable because of tool-loading behavior
- if a required difference belongs in CANON, an SOP, or a companion project's own instruction file
- if maintaining parity would require changing schema, policy, SOP, or canon text beyond this SOP's scope

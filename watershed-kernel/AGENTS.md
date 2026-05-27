# Agent Instructions

This kernel is a lawful-motion substrate.

The purpose is not to model every concept we like.

The purpose is to make illegal movement impossible and legal movement obvious.

## Principles

1. Tokens are bountiful; authority is scarce.
   Spend reasoning freely before changing the model. Do not conserve tokens by
   making plausible but unproven state-model additions.

2. Defer motion, not reasoning.
   The system should reason until the next move is lawful. It should not move
   and discover the law afterward.

3. Humans are bad prompters.
   A human impulse is evidence of intent, not a complete specification. The
   governor/kernel should not encode vague intent as executable state until a
   transition has recovered, classified, or proved the missing structure.

4. The institution holds.
   The kernel should resist drift from both workers and humans. Do not weaken a
   boundary because a prompt asks for convenience. Do not add a bypass because a
   test is awkward. Do not add public constructors for authoritative states.

5. Compile-fail tests are constitutional evidence.
   Every important law should have a trybuild test that refuses illegal motion:
   skipping intent recovery, dispatching unvalidated plans, constructing
   authoritative states from the wrong crate, merging rejected validation,
   constructing completed runs directly, etc.

6. Do not admire the doctrine in prose.
   Implement it. If a principle is important, express it as:
   - a type,
   - a private field,
   - a sealed marker trait,
   - a consuming transition,
   - a crate boundary,
   - a Result error,
   - an integration test,
   - or a compile-fail test.

See [PRESSURE_TESTS.md](PRESSURE_TESTS.md) for the structural rules enforced by compile-fail tests.

## Design Gate

Before adding a type, field, transition, constructor, or dependency, answer:

1. What legal motion creates or proves this?
2. What later legal motion consumes or depends on it?
3. What illegal motion becomes impossible because this exists?
4. What compile-fail or integration test demonstrates that law?

If you cannot answer all four, do not add it.

## Ecosystem topography
See /Users/jakegearon/projects/watershed/TOPOGRAPHY.md for how this project relates to the others in the watershed ecosystem.

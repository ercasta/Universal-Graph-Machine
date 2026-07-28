# 0026. The lexeme is the licensed bridge; entities stay nameless

**Status — current (2026-07-28): HALF.** `../../model.md` §3, §14 — the lexeme bridge is deleted; identity is decided by a rule, gradedly, not interned.

**Status — as recorded:** Accepted
**Source:** substrate_inversion.md §24.3, §30.1; `units/discourse.py`, `vocab.lexeme`

## Context

*"The lion"* in a second sentence must reach the same entity as the first. On a store you look it up
by name. Here that is forbidden twice over: entities are nameless, and interning a surface word into an entity
would be a second global structure that fuses two utterances by name.

## Decision

**The word *lion* belongs to the form set. THE LION is a nameless mention.**

A mention carries `m <word> lexeme("lion")`, and coreference is a rule over **lexeme** identity. Lexemes are
namespaced (`#word`) so they cannot collide with roles, and carry the same licence: a form may mint one, an
utterance may not.

## Evidence

- The distinction was **already being made for roles** (`0017`) — this is the same move one level
  down, not a new mechanism.
- Measured both ways: two mentions in different utterances corefer through the shared lexeme, and two
  independently *minted* `lion` nodes still refuse to match. The by-name fusion stays closed.
- Nothing about the **entity** is resolved by name, which is the property required.

## Consequences

- Reference is **decided, not resolved**: intake mints a fresh node per mention and rules decide
  which mentions are the same.
- A word the form set does not supply is not resolved here at all — the same boundary as a novel role.

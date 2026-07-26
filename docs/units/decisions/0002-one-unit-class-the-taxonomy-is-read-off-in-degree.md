# 0002. One unit class; the taxonomy is read off in-degree

**Status:** Accepted
**Source:** substrate_inversion.md §2

## Context

The design started with several kinds of node — axioms, rules, hypothesis branches, merges — and
the spike kept finding that they differed only in how many things were wired into them.

## Decision

**There is no fact/rule distinction, only in-degree.** One `Unit` class. `kind` is *reported* from
the current wiring (`given` / `rule` / `carrier`), never declared, and it changes as the net is assembled.

## Evidence

- An axiom is a unit with no input and a fixed output; a constant is a nullary function.
- "A source" and "a hypothesis branch" turned out to be the same construct at different in-degree.
- A merge needed no new construct: it is a carrier at in-degree ≥ 2.

## Consequences

- `rule(...)` reports `kind == "given"` until something is wired into it, which surprises people
  and is the correct answer.
- Anything that wants to branch on "what sort of unit is this" is probably asking the wrong question; ask the
  wiring.

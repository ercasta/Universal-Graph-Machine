# 0005. The index indexes computation, never data

**Status — current (2026-07-28): SURVIVES.** in force.

**Status — as recorded:** Accepted
**Source:** substrate_inversion.md §3

## Context

Something has to decide which units could feed which, or assembly is quadratic in the net. That
something is global, and `0001` forbids global structures over data.

## Decision

**The index maps predicates to *units*.** It is the one permitted global structure. Subgraph
values still travel only along wires; nothing enumerates facts globally.

## Evidence

- The distinction is checkable: the index's keys are patterns and unit names, never facts.
- The rule to hold: **if a second global structure appears, something has leaked back into being a store.**

## Consequences

- Selectivity of the index is a real cost question, addressed in `0022`.
- A pattern that declines to say what it reads gets no discrimination from the index and pays for it (`0025`).

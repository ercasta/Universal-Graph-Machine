# 0016. Degree is banded, not continuous

**Status — current (2026-07-28): HISTORICAL.** predates the substrate inversion (2026-07-26). Not contradicted by name in `../../model.md`, and not carried forward as current either — read it as context, not as a decision in force.

**Status — as recorded:** Accepted
**Source:** substrate_inversion.md §22

## Context

Uncertainty could be a number in [0,1] or a small ordered set of bands.

## Decision

**A finite band lattice**, with `meet` = min.

## Evidence

**Finiteness is load-bearing for termination, not style.** A continuous degree can be revised by
ever-smaller amounts forever, so "output unchanged" never holds. A finite lattice reaches a fixed point.

## Consequences

- Degree inheritance is one generic rule over the firing record — three atoms — rather than a
  clause per template. It reads the trace wire and writes the object wire, which is where the two networks meet.
- **A graded absence is inexpressible** via `grade`, because grading asserts. Explicit negation is the fix
  (`0018`).
- Inheritance grades by *positive* premises only: a conclusion drawn partly from an absence is graded as though
  the absence were free.

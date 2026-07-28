# 0024. The object/trace fork test must be positive

**Status — current (2026-07-28): HISTORICAL.** predates the substrate inversion (2026-07-26). Not contradicted by name in `../../model.md`, and not carried forward as current either — read it as context, not as a decision in force.

**Status — as recorded:** Accepted
**Source:** substrate_inversion.md §29.2

## Context

A template that reads only firing predicates has to spawn on its trace half. The test for that was
*"it needs no ground object predicate"*.

## Decision

**Ask the positive question: does this template read *only* firing predicates?** And: **the
predicate pre-filter is an optimisation, sound only when there is a ground predicate to filter on.**

## Evidence

*"Reads no ground object predicate"* also describes an **all-variable** template. Such a template was
sent to the trace fork, where its empty ground need matched nothing, so it was **never instantiated at all** —
`?x ?p ?y ⇒ ?y ?p ?x` simply did not run. `wellformed()` stayed clean and the budget was untouched; only the
journal's `<unused>` marker noticed.

## Consequences

- An all-variable pattern now runs, and terminates, and pays the wildcard cost honestly instead
  of silently not existing.
- Two questions with the same answer on every shape built so far were being conflated — which is the recurring
  failure mode in this component.

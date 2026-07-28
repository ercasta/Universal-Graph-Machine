# 0034. One form = one force = one atomic structure

**Status — current (2026-07-28): HISTORICAL.** predates the substrate inversion (2026-07-26). Not contradicted by name in `../../model.md`, and not carried forward as current either — read it as context, not as a decision in force.

**Status — as recorded:** Designed, not built
**Source:** substrate_inversion.md §18, §24.4

## Context

A contextualised concept must not be split across units in a way that lets an intermediate escape
as an assertion. *"If it rains, the ground is wet"* must not license *"the ground is wet"*. The question is where
the atomic boundary falls.

## Decision

**A chain is atomic exactly over the span where its intermediates carry no assertoric force.**

## Evidence

- Written for conditionals, it **predicts procedure atomicity** without adjustment: a step of a
  procedure is a *command*, not an assertion, so its intermediates are not assertable and the chain is atomic.
  *"To make tea: …"* is covered with nothing added.
- A procedure as a **chain of step units** (intake manufacturing the dependency) keeps every step traceable,
  gated and individually refirable — versus one opaque unit with an internal program, which loses all three.
- A selector chain is a better fit than a procedure, because its dependency is **real**: each selector consumes
  the previous referent, so nothing has to be manufactured.

## Consequences

- Depends on `0033`.
- A step that touches the world must suspend, which reopens `0021` on its stated trigger rather than as drift.

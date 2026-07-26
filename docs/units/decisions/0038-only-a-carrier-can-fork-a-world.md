# 0038. Only a carrier can fork a world

**Status:** Accepted — amends 0006
**Source:** substrate_inversion.md §31.4(b)

## Context

`0006` decides which producers may feed one instance: those comparable — ancestor, descendant or
identical — with every producer already wired in. Comparability was judged by raw reachability over the wiring.

## Decision

**Compare CARRIER lineage, not raw reachability.** A carrier emits its view, so it can add or remove
what flows and therefore constitutes a different world. A rule emits only its conclusion (`0008`) — it derives
something new *in* a world without making a new one. So two sibling **rules** over the same carrier are in the
**same** world; two sibling **carriers** are not.

## Evidence

- **Under subset output, computing anything non-trivial *means* several sibling rules over one
  carrier** — that is the normal shape, not an exotic one. Judging worlds by reachability called those siblings
  incomparable, so **a rule needing premises from two sibling rules was unassemblable**, and a negated premise
  among them went **vacuously true**. Measured: an ambiguity rule reported *every* step ambiguous, because it
  never received the inequality facts it depended on.
- **Every case `0006` exists for survives, and is asserted by a test:** sibling hypotheses have incomparable
  carrier sets and still spawn separate instances with different answers; two independent `given`s are still two
  worlds.
- `0006`'s *"every, not any"* quantifier is untouched. What changed is **which units count as different
  worlds**.

## Consequences

- `0006` should be read with this amendment; the policy is otherwise unchanged.
- This is the fifth defect in this component caused by asking a question at the wrong granularity — here,
  *reachability* where *world* was meant.

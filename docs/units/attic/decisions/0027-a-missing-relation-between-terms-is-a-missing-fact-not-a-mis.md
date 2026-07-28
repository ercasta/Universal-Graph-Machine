# 0027. A missing relation between terms is a missing fact, not a missing operator

**Status — current (2026-07-28): HISTORICAL.** predates the substrate inversion (2026-07-26). Not contradicted by name in `../../model.md`, and not carried forward as current either — read it as context, not as a decision in force.

**Status — as recorded:** Accepted
**Source:** substrate_inversion.md §30.2

## Context

Coreference needs `?x ≠ ?z` and the matcher has no inequality operator. The obvious response is to
add one.

## Decision

**Derive identity as data.** `?x <word> ?y ⇒ ?x <self> ?x`, and then `Absent(?x <self> ?z)` **is**
`?x ≠ ?z` — exact, over the value on the wire, no fuel.

## Evidence

- Without the guard the coreference rule is measurably reflexive junk, so the guard is not decoration.
- **This is the second recorded gap to dissolve rather than be filled** (the predicate variable was the first,
  dissolved by making roles nodes). Two independent cases is enough to state the pattern.
- **It only works because of `0023`.** The inequality rule's producer has to be *wired* for the negation to see
  it, and until that fix a negated premise's producer was never wired — this would have silently reported
  everything unequal to everything.

## Consequences

- Before adding an operator to the matcher, try making the relation data.
- An existential negation still needs one extra rule (a witness), because a negated atom may only test variables
  the positive body bound. One rule, no primitive.

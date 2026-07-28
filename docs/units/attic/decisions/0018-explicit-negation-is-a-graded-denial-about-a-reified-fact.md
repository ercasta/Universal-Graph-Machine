# 0018. Explicit negation is a graded denial about a reified fact

**Status — current (2026-07-28): HISTORICAL.** predates the substrate inversion (2026-07-26). Not contradicted by name in `../../model.md`, and not carried forward as current either — read it as context, not as a decision in force.

**Status — as recorded:** Accepted
**Source:** substrate_inversion.md §22.7–22.8

## Context

*"Probably not P"* cannot be said by grading P (grading asserts P) and cannot be said by `Absent`
(which conflates unknown with denied).

## Decision

**A `<denies>` node, carrying a band, about the reified fact.** It talks about the fact without
asserting it.

## Evidence

- Reification already exists and `0015` makes its handle canonical, so a denial and an assertion
  hang off the *same* node and can be compared.
- A derived denial mints a node, which is what forced `0014` to become a construct.

## Consequences

- **P and not-P is now representable as a distribution, and nothing reconciles it.** A
  reconciliation unit is missing — this is a known gap, not an oversight.
- The representational tension between "a graded absence" and "a denial" is recorded rather than resolved.

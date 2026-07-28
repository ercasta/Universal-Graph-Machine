# 0037. An utterance enters as a carrier downstream of the KB

**Status — current (2026-07-28): HISTORICAL.** predates the substrate inversion (2026-07-26). Not contradicted by name in `../../model.md`, and not carried forward as current either — read it as context, not as a decision in force.

**Status — as recorded:** Accepted
**Source:** substrate_inversion.md §31.4(a)

## Context

An utterance contributes facts of its own — step nodes, mention nodes, attachment links. The obvious
place to put them is a second `given` alongside the KB.

## Decision

**Wire the utterance in as a carrier *below* the KB**, not as a sibling `given`.

## Evidence

Two independent `given`s are two **worlds** (`0006`), so they are incomparable and no rule can join
them. A rule needing the utterance's facts *and* a derived fact was therefore unassemblable — and when the
missing premise was **negated, its NAF went vacuously true**: every selector step was reported unresolved,
including the ones that had resolved. **The first time this rule produced a false report rather than just a
missing conclusion.**

Wiring the utterance below the KB makes it a descendant, hence joinable with everything derived from the KB.

## Consequences

- It also keeps the utterance **distinguishable** from the KB, which merging them into a single
  `given` would lose — and which matters for provenance (*which utterance contributed what*).
- This is the shape intake must use. It is not optional plumbing; the alternative silently produces false
  reports.

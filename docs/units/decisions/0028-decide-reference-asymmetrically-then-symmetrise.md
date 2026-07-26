# 0028. Decide reference asymmetrically, then symmetrise

**Status:** Accepted
**Source:** substrate_inversion.md §30.5–30.7

## Context

A coreference rule needs evidence. Matching on the shared lexeme alone merges *"a lion roars. A lion
sleeps."* — two different lions.

## Decision

**The decision is definiteness:** a *definite* mention corefers with an *indefinite* mention of the
same lexeme. And because `same_as` is an equivalence while the decision is not, **symmetrise after deciding**
with a separate rule.

## Evidence

- Over-merging on the lexeme alone is a **wrong decision**, not a substrate failure — which is exactly
  what *"decided, not resolved"* means. Measured both ways.
- **The asymmetry that makes the decision right makes the substitution one-directional.** Substitution follows
  the arrow, so what is said about *"the lion"* reaches the entity while what was already known about the entity
  never reaches the mention. Found by getting the direction wrong in the spike and reading the output.
- **Coreference is a chain position:** downstream of a merge the mentions are one, downstream of a sibling that
  declined the merge they remain two. Two chains legitimately disagree about identity, and this needed nothing
  new — the declining world simply never spawns a substitution instance.

## Consequences

- Recency, salience and description-matching are further premises on the same rule shape and need
  no new machinery.
- Identity being chain-relative is `0007` applied to identity rather than to belief.

# 0035. A description identifies rather than constitutes; a selector emits a reference

**Status:** Accepted
**Source:** substrate_inversion.md §17.F, §31.0; `bench/spike_selector_chain.py`

## Context

A selector — *"the third floor of the garage near the movie theater"* — narrows a set of entities.
What should it hand to the next step: the entity, or the subgraph that describes it?

## Decision

**A reference, keyed on the selector STEP:**

```
<s3> <refers_to> car        NOT   car <selected> yes
<s3> <narrows>   <s2>
```

The entity stays a **node**; the subgraph is the **constraint set** on it. And the output is a **set** of
references, not one — *"the"* is a separate uniqueness demand layered on top.

## Evidence

- **The subgraph cannot BE the entity.** Read constitutively, *"one subgraph = one entity"* means the
  car stops existing when it moves to the second floor. A description identifies; it does not constitute.
- **Subset output forbids the alternative anyway** (`0008`): emitting the subgraph is re-emitting the input.
- **Entity boundaries survive exactly one hop** (measured): recoverable at a merge because a unit keeps each
  producer's value separately, gone one hop later. Emit subgraphs and you cannot tell which selector contributed
  what.
- **Keying on the STEP, not the entity**, keeps derivational marks off the entity, lets two chains disagree about
  the same entity, and makes the chain walkable.
- Designing for exactly-one referent would have made ambiguity inexpressible.

## Consequences

- The chain is readable off the graph by following `<narrows>`, and each step carries its own
  referent — so the walk is an explanation of the reference, hop by hop.
- Uniqueness and reference failure become demands *on* a step rather than properties of the selector (`0036`).

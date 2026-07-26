# 0014. Anything minted per run must be keyed

**Status:** Accepted
**Source:** substrate_inversion.md §22.8, §23.1 (`match.Mint`)

## Context

Several mechanisms need a fresh node per derivation: a firing record, a degree handle, a derived
denial, a wire's identity in the journal, a rule's structural nodes.

## Decision

**A node minted during a run is a function of (unit, head position, binding), so re-running on the
same match yields the same node.** `match.Mint` makes this a construct rather than a discipline. A head-only
plain variable stays refused — it asserts an unbound existential.

## Evidence

Hit **four separate times** before being made a construct, and always the same way: a fresh node
every run means the output differs every run, so "output unchanged" never holds and propagation never quiesces.
**It destroys the fixpoint it is annotating**, and it does so silently.

## Consequences

- The memo is the minting unit's own state, never global: two units minting for the same match
  get different nodes, which is correct because they are different derivations.
- Convergence *between* two such nodes is a separate question and is not solved here.
- This generalises past minting: see `0015`, which removes the need for it in the commonest case.

# 0007. Scope is a chain, never a key

**Status:** Accepted
**Source:** substrate_inversion.md §4 (the user corrected this three times)

## Context

The obvious implementation of hypotheses is a scope identifier keyed onto facts or units. Every
attempt to do that here reintroduced the shared-store problems `0001` was inverting away from.

## Decision

**Two instances differ by their in-edges. Hypothesis-ness rides *in* the carried subgraph.** There
is no scope object, no scope key, no vantage parameter.

## Evidence

- `Net.upstream` consults no scope, no context and no vantage — reachability over wiring is the
  whole mechanism.
- Coreference arrived at the same shape independently: downstream of a merge two mentions are one, upstream
  they remain two, so identity is *also* chain-relative and two chains may legitimately disagree (`0028`).

## Consequences

- Anything that wants "the scope of this fact" has to be reformulated as "which chain am I on".
- The price is one chain per index — the ATMS exponential wearing the frame problem's clothes. Chains and wide
  nets are measured linear; sibling fan-out is not yet measured.

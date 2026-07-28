# 0020. A CNL front-end must target a subgraph, never the Net API

**Status — current (2026-07-28): HISTORICAL.** predates the substrate inversion (2026-07-26). Not contradicted by name in `../../model.md`, and not carried forward as current either — read it as context, not as a decision in force.

**Status — as recorded:** Accepted
**Source:** substrate_inversion.md §24.7, `units/authoring.py`

## Context

Discourse can introduce new *rules*, so the system's own output must be able to become new
computation. Either output is rendered to text and re-ingested, or there is a transpiler from output graph to
network.

## Decision

**One path only:**

```
CNL text ──parse──▶ rule-shaped SUBGRAPH ──declare──▶ template in the library
a unit's output ─────────────────────────▶ (same path from here)
```

**The CNL front-end must target a subgraph, never `Net` directly.**

## Evidence

- **The text round-trip is unsound, not merely expensive.** Rendering a subgraph names its nodes;
  re-ingesting resolves those names; two independently minted `mary`s would fuse. Text is a lossy channel for
  identity.
- Measured: a rule round-trips through a value including negation and minting slots; a unit emits a rule, the
  bridge declares it, and the network derives what nothing authored. The bridge adds zero wires.
- The encoding reuses the same reification vocabulary a *fact* uses — a pattern atom is described exactly as a
  fact is, which is what makes a derived rule learner-writable.

## Consequences

- **Target `Net` directly and the system becomes able to *say* things it cannot *learn*.** Pinning
  this before a grammar exists costs nothing; retrofitting it is near-impossible.
- A malformed rule *raises* rather than being guessed at.

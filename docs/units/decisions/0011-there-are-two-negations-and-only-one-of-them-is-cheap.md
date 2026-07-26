# 0011. There are two negations, and only one of them is cheap

**Status:** Accepted
**Source:** substrate_inversion.md §6a

## Context

Negation on an open store is semi-decidable and needs a fixpoint. The question was whether this
substrate inherits that cost.

## Decision

**`Absent` asks whether a fact is missing from the value on the wire** — a finished, bounded value
— so it is decidable immediately, with no drain, no fixpoint and no fuel. *"P is not derivable at all"* is a
different question, is open, and is answered by fuel.

## Evidence

- Boundedness is what buys it, which makes this a direct consequence of `0003`.
- The same boundedness makes *"only these"* decidable over a value, which cannot be claimed about an open
  store.

## Consequences

- **Conflating the two is how a resource limit silently becomes a claim about the world**, so
  they are kept in different modules and `Verdict` refuses to be truthy (`0030`).
- `Absent` does **not** distinguish *unknown* from *denied*. The rule author chooses which is meant and nothing
  checks it; explicit negation (`0018`) is the tool for the other one.
- A negated premise's producer still has to be *wired* for the NAF to be meaningful, which was wrong for a long
  time and silently (`0023`).

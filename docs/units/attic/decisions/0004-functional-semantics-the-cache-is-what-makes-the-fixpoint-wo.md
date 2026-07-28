# 0004. Functional semantics; the cache is what makes the fixpoint work

**Status — current (2026-07-28): HALF DEAD.** `../../model.md` §5 — latching makes units stateful, so the *cache* half is dead and nothing is cached. The *fixpoint* half returns: a revive runs to stabilization, bounded by surge (§2).

**Status — as recorded:** Accepted
**Source:** substrate_inversion.md §7; framing sharpened by the user, 2026-07-26

## Context

`ugm/` is imperative: opcodes, registers, a program counter, mutation of a shared graph. `units/`
is not, and the difference was being treated as a style preference rather than a paradigm.

## Decision

**A unit is `output = f(inputs)` over immutable values. Its mutable fields are a memoization
cache, not state.**

## Evidence

Caching is not an optimisation here — it is what makes three things work at once:

- **refire** without recomputing upstream;
- **change propagation** — push to consumers only when the output differs;
- **termination** — "output unchanged" *is* the stopping condition.

The same idempotence result was reached independently from the queue-topology work, which is the third
derivation of it.

## Consequences

- Revision is re-running forward, never retraction (`0019`).
- **Monotonicity is currently load-bearing**, and that is what makes "can a rule remove?" a paradigm question
  rather than a feature request (`0032`).
- Anything that mutates a value in place breaks the fixpoint argument silently.

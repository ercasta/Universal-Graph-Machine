# 0032. Can a rule remove? — monotonicity and derived rewrites

**Status — current (2026-07-28): SETTLED — yes.** `../../model.md` §8, §12 — a rule concludes a retraction and it is applied at write-back. Deletion is the fifth effect and the one non-monotone one.

**Status — as recorded:** OPEN — needs a decision
**Source:** substrate_inversion.md §21.1, §30.4

## Context

Coreference substitution unions properties but does not collapse identity: both mentions survive and
both end up carrying both properties. So coreference is sound for what rules **match** and silent for what is
**counted** — *"how many lions roar"* answers 2.

The designed fix was a merge whose delta *substitutes* B→A, which requires removal. And:

> **A rule cannot remove.** `Unit.removes` is fixed at construction and a rule's head only adds. The claim that
> *"a unit is a graph rewrite"* is true of the **static spec** and **false of the rule** — a derived rewrite, one
> whose removals depend on the match, is inexpressible.

Coreference is the first thing to want it.

## Decision

**Not taken.** Recorded as an open question.

The options:

1. **Keep rules monotone** (status quo). Coreference stays sound-for-matching, silent-for-counting. Uniqueness
   and counting remain known gaps, already logged independently.
2. **Add derived removal** — a rule head that deletes under a binding. Stays *functional* (value in, value out)
   but gives up **monotonicity**.

## Evidence

Monotonicity is currently load-bearing in three places, which is what makes this a paradigm question
rather than a feature request:

- the fixpoint argument rests on outputs only growing toward a limit (`0004`);
- *"revision is recomputing forward"* rests on rules never un-concluding (`0019`);
- the absence of retraction machinery follows from both.

A rule that deletes what another derives can oscillate. The DAG guarantee and the cycle guard may well contain
it, but that has not been measured.

## Consequences

**If option 1:** counting and uniqueness need a different answer — probably reading over a
canonical representative rather than collapsing nodes.

**If option 2:** the fixpoint argument must be re-derived and the oscillation case measured before anything
depends on it.

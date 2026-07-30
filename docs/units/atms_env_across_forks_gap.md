# Finding: ATMS/environment-consistency across forks is a CONFIRMED, separate non-sugar gap

**Written 2026-07-30, continuing the same-day `OVERLAY_BAND` retirement work
(`attic/handoff_overlay_band_composition.md`, `scope_visibility_blocks_forks.md`,
`overlay_band_read_utility_confirmed.md`).**

## What was attempted

Having confirmed the demand chain's *automatic* per-atom rule-body banding was sugar (an ordinary rule using
`Pat(rel="?fork")` + `GradedCondition` reproduces it), the natural next step was to actually retire it: stop
passing `bands=banded` in `chain._solve_demand_rule`'s plain-atom loop, so a rule body must explicitly opt
in to reaching a fork. `tests/test_possibility_rules.py` — the demonstration/regression suite for exactly
this mechanism — was rewritten test-by-test to the explicit idiom, and **5 of 9 previously-automatic tests
were successfully ported and verified correct**: single-fork reads
(`test_body_through_fork_bands_the_conclusion`), multi-variable joins through one fork
(`test_multivariable_join_through_a_fork`), best-band-wins across independent derivations
(`test_best_band_wins_across_derivations`), idempotent re-derivation (`test_banded_emit_is_idempotent`), and
— the most interesting positive result — **same-fork co-scoping via ORDINARY variable reuse**
(`test_cross_exclusive_fork_derivation_is_impossible`): reusing the same `?fork` relativizer variable across
two atoms in one rule body forces them to be co-scoped by the join language's existing unification semantics
(`_bind_state` refuses to rebind a variable to a different node) — no ATMS machinery needed for THIS shape,
since `male`/`short` (different alternatives of the same either/or) never unify on a shared `?fork`, while
`male`/`tall` (same alternative) do.

## Where it broke, and why — two distinct, confirmed mechanisms are missing

**1. Relativized atoms never raise sub-demands.** `chain._relativized_matching`/`_relativized_st_matching`
only read what's ALREADY present in the graph — unlike a plain atom's `_facts_matching` call, they never
invoke `mint(...)` to raise a sub-demand for the atom's predicate. Verified directly: a rule deriving `manly`
from a forked `male`, chained into a second rule deriving `puzzling` from `manly ∧ short`, derives NOTHING
when `puzzling` is demanded top-down — `manly` is never computed as a side effect, because nothing ever asks
for it. Only pre-deriving `manly` as an independent, explicit top-level goal first makes it visible to the
second rule's relativized read.

**2. Even with the intermediate pre-derived, cross-fork compatibility is never checked.** With `manly`
forced into existence first, BOTH `puzzling` (which combines `manly` from the `male∧tall` alternative with
`short` from the INCOMPATIBLE `female∧short` alternative — should be IMPOSSIBLE) and `ok` (which combines
`manly` with the COMPATIBLE `tall` from the same alternative — should derive) came back identically. Worse:
`puzzling` derived `"likely"` — **a genuine unsound false positive**, not just a missing derivation. This is
because relativized atoms never populate the ATMS `env` (`# ontological: no band discount, no env`,
`chain.py`), so nothing in the join can tell the two forks apart once they're reached via DIFFERENT
relativizer variables (the ordinary-unification trick from the correlated-either/or case above only works
when both atoms trace back to the SAME literal scope node — it says nothing about two DIFFERENT scopes that
happen to be mutually exclusive).

The identical root cause also breaks `test_nac_is_env_aware` (a NAC's "is this genuinely blocked within
male-worlds" check needs the positive atom's env, which a relativized atom no longer carries — verified: the
`likely` scenario wrongly comes back `assumed-no` once the positive atom is relativized) and would almost
certainly break `test_disjoint_from_makes_independent_forks_exclusive` on the same shape (independently
authored forks made exclusive via a declared `disjoint_from` fact — needs env-consistency across forks that
were never co-scoped at all).

## Verdict

**CONFIRMED, separate non-sugar exception — not fixable by rewriting rules alone.** This is the possibilistic
layer's analog of `closed_class_rechallenged.md`'s one confirmed non-sugar case (transitivity needing a real
substrate extension): ATMS/environment-consistency tracking across a MULTI-HOP chain of forks is genuinely
substrate-level mechanism, not something an ordinary declared rule can currently express, because the surface
language (`Pat.rel`) has no way to say "these two forks must be compatible" short of literal scope identity.

Two concrete, NOT-YET-BUILT paths to actually closing this gap, for a future session:
1. Make `_relativized_matching`/`_relativized_st_matching` sub-demand-raising (call `mint(...)` the same way
   the plain-atom path does), so a rule chain through forks at least DERIVES the intermediate — this closes
   gap #1 but not #2 (soundness).
2. Design a new declared condition (alongside `GradedCondition`/`ValueMatch`/`Distinct`) that exposes fork
   COMPATIBILITY as an ordinary rule-authorable check — e.g. `Compatible(var_a, var_b)`, reading each bound
   scope's `DERIVED_ENV`/`CHOICE` data and testing `possibility._env_consistent` — so a rule author can
   explicitly guard a multi-fork join the same way they explicitly reach a single fork today. This closes
   gap #2 and is the harder, more interesting design question.

## What was reverted, and what stayed

The `chain._solve_demand_rule` change (removing `bands=banded` from the plain-atom loop) was **reverted** —
`chain.py` is back to byte-identical with pre-session HEAD on this specific mechanism, since retiring it
fully would silently break cross-fork exclusivity for any rule using explicit relativized atoms (a real
soundness regression, not just test failures). The automatic per-atom banding STAYS as the safe, working
default until gap #2 above is actually closed.

**What stayed, as a genuine, verified positive result:** the 5 rewritten tests in
`tests/test_possibility_rules.py` remain rewritten to the explicit `Pat(rel="?fork")` + `GradedCondition`
idiom — they pass identically whether or not the automatic path is also active, proving (for the cases that
don't need ATMS) that the declarative idiom is a real, working alternative an author can already reach for
today, even though the ENGINE's automatic default hasn't been (and, per this finding, currently can't safely
be) removed.

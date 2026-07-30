# Finding: `OVERLAY_BAND`'s direct-read use is CONFIRMED NON-SUGAR — only the rule-body use was ever sugar

**Written 2026-07-30, continuing the same-day `OVERLAY_BAND` investigation
(`attic/handoff_overlay_band_composition.md`, `scope_visibility_blocks_forks.md`).**

## The question

`OVERLAY_BAND` does two distinct jobs. The demand chain's *automatic, invisible* per-atom rule-body banding
(inside `chain._solve_demand_rule`'s plain-atom loop) was already proven retirable — an ordinary declared
rule using `Pat(rel="?fork")` + `GradedCondition` reproduces it with zero new mechanism. The question left
open: is the OTHER use — a *direct band-lookup utility*, called by `check.py`, `reconsider.py`,
`scope_crossing.py`, `suppose.py`, and `possibility.py`'s public API — sugar too, or genuinely closed-class
mechanism?

## The five call sites, read directly

Every one of them shares the identical shape: **run `chain_sip(...)` first (drive the goal to whatever it
derives), then call `_facts_matching(..., bands=True)` (or `possibility()`) to read the BEST band of the
resulting fact** — a post-hoc read of already-settled state, never a composition the read itself performs:

- `check.py:113-124` — `check()` calls `chain_sip(fact_g, goal, ...)`, then `_band_present(fact_g, goal,
  scope=scope)` — a `max(...)` over rows of the SAME goal tuple.
- `reconsider.py:105-112` — `_positive_now` calls `chain_sip(kb, goal, ...)`, then
  `_facts_matching(kb, goal[0], goal[1], goal[2], bands=banded)`, again `max(...)` over the same tuple,
  compared against `policy.theta`.
- `scope_crossing.py:212, 260` — `_held_scopes` is called AFTER `resolve_crossings`'s own loop has already
  run `chain_sip(g, ("holds_base", ById(sc), "yes"), ...)` for every crossing scope that pass — reading which
  scopes NOW hold, at their band, to decide whether another pass is needed.
- `suppose.py:270-283` — the closest-looking case: `chain_sip` runs for BOTH `pred` and `neg_pred`, then TWO
  independent `_facts_matching(..., bands=True)` reads (one per polarity) are each a `max(...)` over their
  own single goal tuple; the only "combination" is comparing `pos` vs `neg` (`neg >= pos: contradiction`) —
  an ordinary numeric comparison of two already-settled reads, not a t-norm composition across facts. This
  is the same shape as θ-gated NAF's own comparison (`possibility.naf_holds`: `possibility(...) < theta`),
  already an accepted closed-algebra primitive.
- `possibility.py`'s `possibility()`/`verdict()`/`naf_holds()` — no `chain_sip` call at all; the module's own
  docstring already says so: *"A READ of what is present; to also derive on demand, run `chain_sip` with a
  banded policy first."* The purest instance of the pattern.

None of the five ever combines bands ACROSS multiple distinct facts inside its own logic — each takes
`max(...)` over rows of ONE goal tuple (the qualitative Π/"best derivation wins" operator, which is a
DEFINITION of possibility, not a rule composing anything), and any cross-fact composition (min-t-norm across
a rule body's atoms) has already happened INSIDE the `chain_sip` call that precedes the read, in the part
this session already retired.

## Cross-checked against the standing finding

`closed_class_rechallenged.md` (the `units/`-era rechallenge, whose "the closed algebra is what this project
keeps building forward on" verdict was explicitly carried into `ugm/` by this session's own foundation
decision — see `attic/handoff_ugm_reversion_evaluation.md`) already lists **"a meet-semilattice for
gradedness (`band.py`'s `meet`)"** among the confirmed-closed, non-sugar substrate primitives, alongside
conjunctive matching and θ-gated NAF (`closed_class_rechallenged.md` line 85-86, 104). `OVERLAY_BAND`'s
max-of-derivations read is the direct `ugm/` analog of that already-confirmed primitive. This finding doesn't
discover something new — it confirms that the earlier, general finding actually covers this specific case,
rather than assuming so without checking.

## Verdict

**CONFIRMED NON-SUGAR.** The direct band-lookup utility (`OVERLAY_BAND` as used by `check`/`reconsider`/
`scope_crossing`/`suppose`/`possibility`'s public API) stays exactly as-is — no code change. This narrows
`OVERLAY_BAND`'s actual retirement scope to only the piece already proven sugar: the demand chain's automatic,
invisible per-atom banding of ordinary rule-body `Pat` atoms (`chain._solve_demand_rule`'s plain-atom loop).
That piece is implemented next (see `arc_recap.md`'s current Act for the outcome).

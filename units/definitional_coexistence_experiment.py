"""DEFINITIONAL-COEXISTENCE PROBE — the last item on `closed_class_rechallenged.md` §8/§9's probe list.
`goal_experiment.py`'s additive rewrite (`check_rewrite_via_addition`) established that a fact's new form
is minted *alongside* the old, never replacing it. That raised a risk, named but never checked: if a
defined equivalence keeps both forms alive, and two *independently authored* rules each react to their own
form, could they produce two representations of what is, underneath, the same conclusion — and would the
engine's conflict-detection (`Overlays.conflicts()`) misread that agreement as a spurious disagreement?
And, the other direction, does it still catch a *genuine* disagreement when the two forms actually warrant
one, rather than being blinded by "multiple sources, so ignore it"?

**Why this one didn't need a new experiment framework.** Reading `overlay.py`'s `Overlays.conflicts()`
directly settles half the question before running anything: a slot is a conflict when `len({r.value for r
in found}) > 1` — **deduped by value, not by source**. Two `Reading`s from two different rules that happen
to carry the *same* value already collapse to one distinct value and are not a conflict, by construction.
That is a promising sign, but `causation-core-was-sugar`'s lesson applies here too — a promising read of
the code is not the same as a checked worked example, especially given this is the one probe in the arc
that already found a real gap (`transitivity_probe_experiment.py`'s RHS extension) rather than confirming
the pattern held.

**The scenario.** `paul` carries `age=42` (the old form). An additive-rewrite rule
(`goal_experiment.py`'s shape, unmodified) reifies it into a second, independent form — an `age_claim`
node, `about`-linked to `paul`, carrying `value=42` — *alongside* the original, never retracting it. Two
independently authored eligibility rules each react to only one form: `eligible_from_old_form` matches
`paul.age == 42` directly; `eligible_from_new_form` matches the reified claim's `value == 42` through the
`about` role. Both conclude the identical fact — `paul.eligible = True` — the same node, the same
attribute, the same value, reached two structurally different ways.

Three checks, all against the real engine:

1. **Two rules concluding the identical value about the same slot, from two coexisting forms of the same
   underlying fact, do NOT register as a conflict** — `check_agreeing_conclusions_from_both_forms_are_not_
   a_conflict` — the core claim, checked rather than inferred from reading `conflicts()`'s dedup logic.
2. **⭐ The converse, so the finding isn't "conflicts never happen": when the two forms genuinely warrant
   different conclusions, the engine still catches the real disagreement** —
   `check_genuinely_different_conclusions_are_still_caught` — a third, independent rule reacting to a
   *different* fact about `paul` concludes `eligible=False`; this must surface as a real `Conflict`,
   confirming the dedup-by-value mechanism isn't accidentally swallowing every multi-source case, only the
   ones that are actually the same value.
3. **Both original forms are still readable, untouched, regardless of which conflict outcome occurred** —
   `check_both_forms_survive_untouched` — `create-never-merge` still holds: the old form was never
   retracted to make room for the new one, in either scenario.

Re-runnable: `python -m units.definitional_coexistence_experiment`.
"""
from __future__ import annotations

from .engine import Attribute, Emit, Network, StandingUnit
from .graph import EMPTY, named
from .match import atom, role


def _reify_rule() -> StandingUnit:
    """`goal_experiment.py`'s additive-rewrite shape, unmodified: mint the new form alongside the old,
    never retracting it."""
    return StandingUnit("reify_age", (atom("p", name="paul", age=42),),
                         Emit("age_claim", roles=(("about", "p"),), as_="c"),
                         Attribute("c", "value", 42), mutating=True)


def _eligible_from_old_form_rule() -> StandingUnit:
    return StandingUnit("eligible_from_old_form", (atom("p", name="paul", age=42),),
                         Attribute("p", "eligible", True), mutating=True)


def _eligible_from_new_form_rule() -> StandingUnit:
    return StandingUnit(
        "eligible_from_new_form",
        (atom("c", name="age_claim", value=42, out=(role("about", atom("p")),)),),
        Attribute("p", "eligible", True), mutating=True)


def _disagreeing_rule() -> StandingUnit:
    """An independent rule, reacting to a different fact entirely, concluding the OPPOSITE value on the
    SAME slot — the genuine-disagreement control."""
    return StandingUnit("flag_ineligible", (atom("p", name="paul", flagged=True),),
                         Attribute("p", "eligible", False), mutating=True)


def _network(include_disagreement: bool = False):
    g, paul = named(EMPTY, "paul", age=42)
    if include_disagreement:
        g = g.with_node(paul, flagged=True)
    n = Network()
    ax = n.given(g)
    reify = n.add(_reify_rule())
    n.wire(ax, reify)
    old_rule = n.add(_eligible_from_old_form_rule())
    n.wire(ax, old_rule)
    new_rule = n.add(_eligible_from_new_form_rule())
    n.wire(reify.cell, new_rule)
    if include_disagreement:
        bad_rule = n.add(_disagreeing_rule())
        n.wire(ax, bad_rule)
    n.revive()
    return n, paul


def check_agreeing_conclusions_from_both_forms_are_not_a_conflict() -> dict[str, object]:
    n, paul = _network(include_disagreement=False)
    w = n.world()
    return {"eligible_reads_cleanly_true": w.attr(paul, "eligible") is True,
            "no_conflicts": w.conflicts() == []}


def check_genuinely_different_conclusions_are_still_caught() -> dict[str, object]:
    n, paul = _network(include_disagreement=True)
    w = n.world()
    conflicts = w.conflicts()
    eligible_conflicts = [c for c in conflicts if c.node is paul and c.attr == "eligible"]
    return {"eligible_reads_as_none_while_conflicted": w.attr(paul, "eligible") is None,
            "a_real_conflict_was_reported": len(eligible_conflicts) == 1,
            "conflict_carries_both_values": ({r.value for r in eligible_conflicts[0].readings} == {True, False}
                                              if eligible_conflicts else False)}


def check_both_forms_survive_untouched() -> dict[str, object]:
    n, paul = _network(include_disagreement=True)
    w = n.world()
    return {"old_form_age_untouched": w.attr(paul, "age") == 42,
            "new_form_reachable": any(w.attr(c, "name") == "age_claim" and w.attr(c, "value") == 42
                                       for c in w.nodes)}


def report() -> str:
    lines = ["=== DEFINITIONAL-COEXISTENCE PROBE: agreement across two forms is NOT a spurious conflict,",
             "    and genuine disagreement is still caught ==="]
    lines.append(f"agreeing conclusions from both forms, no conflict: "
                 f"{check_agreeing_conclusions_from_both_forms_are_not_a_conflict()}")
    lines.append(f"genuinely different conclusions still caught: "
                 f"{check_genuinely_different_conclusions_are_still_caught()}")
    lines.append(f"both forms survive untouched: {check_both_forms_survive_untouched()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())

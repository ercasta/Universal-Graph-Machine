"""GOAL EXPERIMENT — the worked example `cnl_engine_goal_plan.md` §7d asks for, before any of §7c's
design gets written up as settled.

⚠ **First version of this file (2026-07-29) invented machinery the engine didn't need — recorded here
because the correction is the actual finding.** It "solved" lineage interning by spinning up a *second*
`Network` object each turn, and "solved" decay's wire-retraction by splitting delivery across two gates.
Both were self-inflicted: the codebase already has a one-line, precedented answer for "a unit needs to
see what a prior turn wrote" — manage the axiom's lifecycle on the *same*, persisting `Network`
(`ax.held = None`; wire a fresh `n.axiom(*effects_of(n.asserted), ...)` on the *same* gate) — exactly the
idiom `tests/units/test_engine.py`'s `test_a_rule_writes_a_whole_rule_with_nothing_authored_in_python` and
`test_a_mutating_rule_can_conclude_a_wire` already use. Verified against the real engine that this needs
no second `Network` and no second gate. What's below is the corrected version; the wrong turn is worth
keeping in the docstring so it isn't quietly reinvented.

Checks, all against the real engine (`units/engine.py`), not a mock:

1. **Lineage, interned.** A goal mints a subgoal via an ordinary mutating rule (`Emit` + `Link`). Interning
   ("get-or-create per parent") needs a NAC-shaped guard (`absent(...)`) — and §7b flagged exactly this
   shape as the old procedures arc's most recurring bug. Checked two ways on **one, persisting** `Network`
   and **one, persisting** `StandingUnit`: naively (calling `revive()` again with the axiom's held value
   left untouched — **does** duplicate, and correctly so per `model.md` §5, *"a repeat arrival is a
   firing... there is no value-comparison test suppressing it"* — this is documented behavior, not a
   defect) and managed (null the stale axiom, wire a fresh reflective axiom capturing the *current*
   `self.asserted` onto the *same* gate — does not duplicate, because the guard's view now includes what
   the first turn wrote back).
2. **Outcome, as a positive fact.** A goal's satisfaction condition being met (or not) concludes
   `achieved` / `diverged` directly on the goal node — never read off absence.
3. **Abandon-and-decay.** A `stale` marker concludes `abandoned=True` **and** retracts the goal's own
   watching wire (`Drop` on the `<wire>` occurrence) — closing `model.md` §13's attention-leak. One
   reflective axiom, delivered on the *same* gate as the goal's ordinary facts, is enough — it is a
   strict superset of what the plain axiom delivers once `given()`/`wire()` have both already written into
   `self.asserted`, so nothing needs a second gate.

A fourth check, independent of goals but part of the same next-action (§7d): **rewrite via addition** —
does minting a fact's new form *alongside* the old (never replacing it) actually let two independent rules
each match their own form and both fire, with the old form left untouched? `computation_units.md` §5
found `Identify`/merge is the *substitution* primitive; this is testing the *different*, additive
decision made in conversation for KB rewriting. This one held up unmodified: a `StandingUnit`'s output is
built from an `EMPTY` base (`view()`, `engine.py`), never from `self.asserted`, so a producer's output
never carries a copy of what it merely read — the same tunnel `computation_units.md` §5 found for
`Identify`, hit again from the additive-mint side.

Full write-up: `docs/units/cnl_engine_goal_plan.md` §7. Re-runnable: `python -m units.goal_experiment`.
"""
from __future__ import annotations

from .engine import TO, WIRE, Attribute, Drop, Emit, Link, Network, StandingUnit, effects_of
from .graph import EMPTY, named, role_edge
from .match import absent, atom, role

_GOAL_PAT = (atom("g", name="goal", out=(role("wants", atom("c")),)),
             absent(atom("g", out=(role("raised", atom()),))))


def _raise_subgoal_rule() -> StandingUnit:
    return StandingUnit("raise_subgoal", _GOAL_PAT,
                         Emit("subgoal", as_="sg"), Link("g", "sg", role="raised"),
                         mutating=True)


def _build_goal() -> tuple:
    g = EMPTY
    g, goal = named(g, "goal")
    g, cond = named(g, "delivered")
    g = role_edge(g, goal, "wants", cond)
    return g, goal, cond


def _count_raised(g, goal) -> int:
    return sum(1 for r in g.out(goal) if g.attr(r, "name") == "raised")


def check_lineage_interning_naive() -> dict[str, object]:
    """Calling `revive()` again with the axiom left as-is. **Correctly** duplicates — `model.md` §5's
    documented behavior, not a defect: the guard's view is built only from what is latched on its own
    gate, and nothing changed there, so the identical input arrives and fires again."""
    g, goal, _cond = _build_goal()
    n = Network()
    n.wire(n.given(g), n.add(_raise_subgoal_rule()))
    n.revive()
    after_one = _count_raised(n.asserted, goal)
    n.revive()
    after_two = _count_raised(n.asserted, goal)
    return {"after_one_revive": after_one, "after_two_revives_same_network": after_two}


def check_lineage_interning_managed() -> dict[str, object]:
    """The precedented way — `test_a_rule_writes_a_whole_rule_with_nothing_authored_in_python`'s idiom,
    not a rebuilt `Network`: **one** persisting `Network`, **one** persisting `StandingUnit`. Between
    turns, null the stale axiom and wire a fresh reflective axiom — capturing what the first turn wrote
    back — onto the *same* gate. The guard now sees its own prior output and blocks."""
    g, goal, _cond = _build_goal()
    n = Network()
    ax = n.given(g)
    rule = n.add(_raise_subgoal_rule())
    n.wire(ax, rule)
    n.revive()
    after_turn_one = _count_raised(n.asserted, goal)

    ax.held = None                                                    # stop redelivering the stale snapshot
    reflect = n.axiom(*effects_of(n.asserted), name="reflect")        # the current, accumulated graph
    n.wire(reflect, rule)                                             # same gate ("in") — no new gate
    n.revive()
    after_turn_two = _count_raised(n.asserted, goal)
    return {"after_turn_one": after_turn_one, "after_turn_two_managed_axiom": after_turn_two}


def check_outcome_achieved_and_diverged() -> dict[str, object]:
    """The satisfaction condition is checked, and the outcome lands as a positive attribute on the
    goal — `achieved` when met, `diverged` when a check comes back negative. Never an absence-test."""
    check_pat = (atom("g", name="goal", out=(role("wants", atom("c", true=True)),)),)
    diverge_pat = (atom("g", name="goal", out=(role("wants", atom("c", true=False)),)),)

    g = EMPTY
    g, goal_a = named(g, "goal")
    g, cond_a = named(g, "delivered", true=True)
    g = role_edge(g, goal_a, "wants", cond_a)
    g, goal_b = named(g, "goal")
    g, cond_b = named(g, "delivered", true=False)
    g = role_edge(g, goal_b, "wants", cond_b)

    n = Network()
    ax = n.given(g)
    n.wire(ax, n.add(StandingUnit("check_achieved", check_pat,
                                   Attribute("g", "achieved", True), mutating=True)))
    n.wire(ax, n.add(StandingUnit("check_diverged", diverge_pat,
                                   Attribute("g", "diverged", True), mutating=True)))
    n.revive()
    return {"goal_a_achieved": n.world().attr(goal_a, "achieved"),
            "goal_a_diverged": n.world().attr(goal_a, "diverged"),
            "goal_b_achieved": n.world().attr(goal_b, "achieved"),
            "goal_b_diverged": n.world().attr(goal_b, "diverged")}


def check_abandon_and_decay() -> dict[str, object]:
    """A goal marked `stale` concludes `abandoned=True` *and* retracts its own watching wire — the
    mechanism `model.md` §13 names as the fix for the attention leak. The decay rule matches the
    `<wire>` occurrence itself (`model.md` §6: wires are ordinary occurrences), so it has to be
    *delivered* first (invariant 19 — machinery is unreachable unless something wires it). One
    reflective axiom on the unit's ordinary gate is enough: `effects_of(n.asserted)`, taken after
    `given()`/`wire()` have both already written into the graph, is a strict superset of the plain
    axiom's contribution, so no second gate is needed."""
    decay_pat = (atom("g", name="goal", stale=True),
                 absent(atom("g", abandoned=True)),
                 atom("w", name=WIRE, out=(role(TO, atom(name="watch")),)))

    g = EMPTY
    g, goal = named(g, "goal", stale=True)
    n = Network()
    ax = n.given(g)
    watch = n.add(StandingUnit("watch", (atom("g", name="goal"),),
                                Attribute("g", "watched", True)))
    n.wire(ax, watch)
    decay = n.add(StandingUnit("decay", decay_pat,
                                Attribute("g", "abandoned", True), Drop("w"), mutating=True))
    reflect = n.axiom(*effects_of(n.asserted), name="reflect")   # superset: goal facts AND the <wire>
    n.wire(reflect, decay)                                        # one gate — same as everything else
    before = [(s.name, d.name, gate) for s, d, gate in n.wires]
    n.revive()
    after = [(s.name, d.name, gate) for s, d, gate in n.wires]
    return {"wires_before": before, "wires_after": after,
            "abandoned": n.world().attr(goal, "abandoned")}


def check_rewrite_via_addition() -> dict[str, object]:
    """`age=42` as a plain attribute, and a rule that mints its reified form (`age_claim`, `about`,
    `value`) **alongside** it — never retracting the original. Two independent consumers, one per
    form, both fire; the old form is left standing. Additive rewriting, not substitution."""
    g, paul = named(EMPTY, "paul", age=42)
    n = Network()
    ax = n.given(g)
    reify = n.add(StandingUnit("reify_age", (atom("p", name="paul", age=42),),
                                Emit("age_claim", roles=(("about", "p"),), as_="c"),
                                Attribute("c", "value", 42), mutating=True))
    n.wire(ax, reify)

    old_form = n.add(StandingUnit(
        "old_form_consumer", (atom("p", name="paul", age=42),),
        Attribute("p", "old_form_seen", True), mutating=True))
    n.wire(ax, old_form)

    new_form = n.add(StandingUnit(
        "new_form_consumer",
        (atom("c", name="age_claim", value=42, out=(role("about", atom("p")),)),),
        Attribute("p", "new_form_seen", True), mutating=True))
    n.wire(reify.cell, new_form)

    n.revive()
    return {"age_still_42": n.world().attr(paul, "age"),
            "old_form_seen": n.world().attr(paul, "old_form_seen"),
            "new_form_seen": n.world().attr(paul, "new_form_seen")}


def report() -> str:
    lines = ["=== GOAL EXPERIMENT: lineage, outcome, decay, and additive rewriting ==="]
    lines.append(f"lineage interning, naive (axiom left as-is, correctly refires): "
                 f"{check_lineage_interning_naive()}")
    lines.append(f"lineage interning, managed (same Network, axiom lifecycle managed): "
                 f"{check_lineage_interning_managed()}")
    lines.append(f"outcome as a positive fact: {check_outcome_achieved_and_diverged()}")
    lines.append(f"abandon and decay: {check_abandon_and_decay()}")
    lines.append(f"rewrite via addition: {check_rewrite_via_addition()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())

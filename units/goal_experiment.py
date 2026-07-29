"""GOAL EXPERIMENT — the worked example `cnl_engine_goal_plan.md` §7d asks for, before any of §7c's
design gets written up as settled.

Three small, separately-checkable things, all against the real engine (`units/engine.py`), not a mock:

1. **Lineage, interned.** A goal mints a subgoal via an ordinary mutating rule (`Emit` + `Link`). Interning
   ("get-or-create per parent") needs a NAC-shaped guard (`absent(...)`) — and §7b flagged exactly this
   shape as the old procedures arc's most recurring bug. Checked two ways: naively (calling `revive()`
   twice on one `Network`, which **does** duplicate — the guard reads only what's delivered to the unit's
   own gate, and the axiom's held value is a fixed snapshot from construction, so a second revive
   redelivers the *original* graph, blind to what write-back just added) and per-turn (rebuilding a fresh
   `Network` from the previous turn's `asserted` graph before revive, the way `model.md` §7's outer loop
   actually works — which does not duplicate, because the new turn's axiom delivers `effects_of` the
   *accumulated* graph, guard included).
2. **Outcome, as a positive fact.** A goal's satisfaction condition being met (or not) concludes
   `achieved` / `diverged` directly on the goal node — never read off absence.
3. **Abandon-and-decay.** A `stale` marker concludes `abandoned=True` **and** retracts the goal's own
   watching wire (`Drop` on the `<wire>` occurrence) — closing `model.md` §13's attention-leak — while
   nothing touches the lineage edge itself (not exercised in this scenario, since it has none, but the
   decay rule's effects are scoped to the wire alone).

A fourth check, independent of goals but part of the same next-action (§7d): **rewrite via addition** —
does minting a fact's new form *alongside* the old (never replacing it) actually let two independent rules
each match their own form and both fire, with the old form left untouched? `computation_units.md` §5
found `Identify`/merge is the *substitution* primitive; this is testing the *different*, additive
decision made in conversation for KB rewriting.

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
    """The wrong way: two `revive()` calls on the *same* `Network`. Duplicates, because the axiom's
    held value is the original snapshot — the guard never sees what the first revive wrote back."""
    g, goal, _cond = _build_goal()
    n = Network()
    n.wire(n.given(g), n.add(_raise_subgoal_rule()))
    n.revive()
    after_one = _count_raised(n.asserted, goal)
    n.revive()
    after_two = _count_raised(n.asserted, goal)
    return {"after_one_revive": after_one, "after_two_revives_same_network": after_two}


def check_lineage_interning_per_turn() -> dict[str, object]:
    """The right way: a fresh `Network` per turn, axiom built from the *accumulated* graph — this is
    `model.md` §7's outer loop, literally. The guard now sees what the previous turn wrote."""
    g, goal, _cond = _build_goal()
    n1 = Network()
    n1.wire(n1.given(g), n1.add(_raise_subgoal_rule()))
    n1.revive()
    after_turn_one = _count_raised(n1.asserted, goal)

    n2 = Network()
    n2.wire(n2.given(n1.asserted), n2.add(_raise_subgoal_rule()))
    n2.revive()
    after_turn_two = _count_raised(n2.asserted, goal)
    return {"after_turn_one": after_turn_one, "after_turn_two_fresh_network": after_turn_two}


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
    *delivered* one first (invariant 19 — machinery is unreachable unless something wires it), on a
    second gate rather than overwriting the goal facts on the first."""
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
                                Attribute("g", "abandoned", True), Drop("w"),
                                gates=("in", "meta"), mutating=True))
    n.wire(ax, decay, gate="in")
    reflect = n.axiom(*effects_of(n.asserted), name="reflect")   # delivers the <wire> facts
    n.wire(reflect, decay, gate="meta")
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
    lines.append(f"lineage interning, naive (same Network, two revives): "
                 f"{check_lineage_interning_naive()}")
    lines.append(f"lineage interning, per-turn (fresh Network each turn): "
                 f"{check_lineage_interning_per_turn()}")
    lines.append(f"outcome as a positive fact: {check_outcome_achieved_and_diverged()}")
    lines.append(f"abandon and decay: {check_abandon_and_decay()}")
    lines.append(f"rewrite via addition: {check_rewrite_via_addition()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())

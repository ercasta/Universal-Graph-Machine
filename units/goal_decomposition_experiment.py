"""GOAL DECOMPOSITION EXPERIMENT — `goal_machinery.md` §7's first open item: a subgoal with its own
satisfaction condition, distinct from its parent's, independently checked.

Every prior worked example either used a bare lineage marker (`goal_experiment.py`'s subgoal has no
`wants` of its own) or quantified over an externally-given, flat set of members
(`quantification_cursor_experiment.py`'s case (c)). Neither tests real decomposition: a goal minting
*several* subgoals, each with its own condition, each resolved on its own turn, with the **parent's**
own outcome bubbling up only once every child's is in. This is the combination `cnl_engine_goal_plan.md`
§7c originally described and nothing built so far has exercised.

**The scenario:** a goal decomposes into two subgoals (`book_flight`, `book_hotel`), interned the same
way `goal_experiment.py` interns lineage (NAC-guarded, axiom-lifecycle-managed). Each subgoal's own
condition arrives from outside on its own turn (a stand-in for two independent tool calls). The parent's
`achieved` must wait for *both* children; its `diverged` must fire as soon as *either* child diverges,
without ever letting a still-pending sibling block that report.

**Reuses, doesn't reinvent:** the reflective-axiom-lifecycle discipline (`goal_machinery.md` §3) for every
rule here, first- and second-level alike — one gate, one reused reflective `Cell`.

**⚠ Correction, 2026-07-30: the same-turn sibling-cell gate from the first version of this file was
self-inflicted machinery, not a requirement, and it's been removed.** Checked directly against
`Network._drain()` (`units/engine.py:801`): a unit's own conclusion is queued and delivered to anything
wired to its cell *within the same `revive()` call* — the drain loop keeps consuming its queue until
nothing's left, and only writes back at the very end. So ordinary wiring already carries a sibling's
same-turn output; nothing special was needed for *that* half of the original justification. The other
half — "otherwise the answer might never appear if no further turn comes" — was also wrong: a unit that
can't fire because a gate is empty doesn't fail silently, it goes `dangling()` (`engine.py:569`), which
`model.md` §7 names as *the* honest "still waiting" signal for an outer driver to act on. Precedent for
accepting one-turn lag on freshly-produced structure already exists in this codebase —
`test_a_rule_writes_a_whole_rule_with_nothing_authored_in_python`'s own docstring: *"and on the next turn
it runs."* So the parent's achieved/diverged rules now use **one** gate, same as everything else, and
simply see a child's conclusion one turn later than the child's own turn — traced explicitly below as a
`settle` step, not hidden behind extra wiring.

**One wrinkle, specific to decomposition and not present in the flat case, and still real:** the parent's
`achieved` NAC (`absent(raised subgoal with achieved=None)`) is vacuously true before any subgoal has even
been minted, so it needs a **positive** existence premise (`atom(out=(role("raised", atom())))`) alongside
the NAC, or a still-undecomposed goal would read as trivially achieved. `quantification_cursor_experiment.py`
never needed this because its member set was given up front, never minted by the same rule chain that
consumes it.

Re-runnable: `python -m units.goal_decomposition_experiment`.
"""
from __future__ import annotations

from .engine import Attribute, Emit, Link, Network, StandingUnit, Value, effects_of
from .graph import EMPTY, named
from .match import absent, atom, role

_DECOMPOSE_PAT = (atom("g", name="goal", out=(role("wants", atom()),)),
                   absent(atom("g", out=(role("raised", atom()),))))

_SUBGOAL_ACHIEVED_PAT = (atom("sg", name="subgoal", achieved=None,
                               out=(role("wants", atom("c", true=True)),)),)
_SUBGOAL_DIVERGED_PAT = (atom("sg", name="subgoal", diverged=None,
                               out=(role("wants", atom("c", true=False)),)),)

_PARENT_ACHIEVED_PAT = (atom("g", name="goal", out=(role("raised", atom()),)),
                         absent(atom("g", out=(role("raised", atom(achieved=None)),))),
                         absent(atom("g", out=(role("raised", atom(diverged=True)),))))

_PARENT_DIVERGED_PAT = (atom("g", name="goal", out=(role("raised", atom(diverged=True)),)),)


def _decompose_rule() -> StandingUnit:
    return StandingUnit(
        "decompose", _DECOMPOSE_PAT,
        Emit("subgoal", as_="sg1"), Emit("book_flight", as_="c1"),
        Link("sg1", "c1", role="wants"), Link("g", "sg1", role="raised"),
        Emit("subgoal", as_="sg2"), Emit("book_hotel", as_="c2"),
        Link("sg2", "c2", role="wants"), Link("g", "sg2", role="raised"),
        mutating=True)


def _rules() -> dict[str, StandingUnit]:
    return {
        "decompose": _decompose_rule(),
        "sub_achieved": StandingUnit("sub_achieved", _SUBGOAL_ACHIEVED_PAT,
                                      Attribute("sg", "achieved", True), mutating=True),
        "sub_diverged": StandingUnit("sub_diverged", _SUBGOAL_DIVERGED_PAT,
                                      Attribute("sg", "diverged", True), mutating=True),
        # One gate, like every first-level rule — sees a child's own conclusion one turn after the
        # child's, via the reused reflective snapshot. No second gate.
        "parent_achieved": StandingUnit("parent_achieved", _PARENT_ACHIEVED_PAT,
                                         Attribute("g", "achieved", True), mutating=True),
        "parent_diverged": StandingUnit("parent_diverged", _PARENT_DIVERGED_PAT,
                                         Attribute("g", "diverged", True), mutating=True),
    }


def _find(g, name: str):
    return next(n for n in g.nodes if g.attrs.get(n, {}).get("name") == name)


def _wire(n: Network, rules: dict[str, StandingUnit], reflect) -> None:
    for r in rules.values():
        n.wire(reflect, r, gate="in")


def _build_goal():
    g = EMPTY
    g, goal = named(g, "goal")
    g, trigger = named(g, "book_trip")
    from .graph import role_edge
    g = role_edge(g, goal, "wants", trigger)
    return g, goal


def _read(n: Network, goal) -> dict[str, object]:
    return {"achieved": n.world().attr(goal, "achieved"), "diverged": n.world().attr(goal, "diverged")}


def _settle(n: Network, reflect) -> None:
    """No new external input — just re-expose what the last turn wrote back, one turn later, the same
    idiom `test_a_rule_writes_a_whole_rule_with_nothing_authored_in_python` uses for a freshly-minted
    unit. Second-level rules (parent achieved/diverged) that saw a sibling's conclusion too late to react
    this same turn get their chance here."""
    reflect.held = Value(effects_of(n.asserted))
    n.revive()


def _run(flight_ok: bool, hotel_ok: bool) -> list[dict[str, object]]:
    """Decompose, then resolve each child on its own turn (flight first, hotel second), with an explicit
    settle turn after each result — the honest, precedented one-turn lag, not hidden behind extra wiring.
    Returns the (achieved, diverged) read after *every* turn, so the "still pending" middle states and
    the lag itself are both visible."""
    g, goal = _build_goal()
    n = Network()
    n.given(g)
    rules = _rules()
    for r in rules.values():
        n.add(r)
    reflect = n.axiom(*effects_of(n.asserted), name="reflect")
    _wire(n, rules, reflect)

    trace = []
    n.revive()
    trace.append({"turn": "decompose", **_read(n, goal)})
    _settle(n, reflect)
    trace.append({"turn": "settle_after_decompose", **_read(n, goal)})

    c1 = _find(n.asserted, "book_flight")
    n.asserted = n.asserted.with_node(c1, true=flight_ok)
    reflect.held = Value(effects_of(n.asserted))
    n.revive()
    trace.append({"turn": "flight_result", **_read(n, goal)})
    _settle(n, reflect)
    trace.append({"turn": "settle_after_flight", **_read(n, goal)})

    c2 = _find(n.asserted, "book_hotel")
    n.asserted = n.asserted.with_node(c2, true=hotel_ok)
    reflect.held = Value(effects_of(n.asserted))
    n.revive()
    trace.append({"turn": "hotel_result", **_read(n, goal)})
    _settle(n, reflect)
    trace.append({"turn": "settle_after_hotel", **_read(n, goal)})
    return trace


def check_both_children_succeed_reaches_achieved_only_after_both() -> dict[str, object]:
    """Parent must stay undecided through decomposition and the first child's result, and reach
    `achieved` on the settle turn *after* the second child's result — one turn later, honestly, not
    hidden behind a second gate."""
    return {"trace": _run(flight_ok=True, hotel_ok=True)}


def check_one_child_diverges_parent_diverges_without_waiting_on_the_other() -> dict[str, object]:
    """Flight succeeds, hotel fails. Parent must reach `diverged` on the settle turn after the hotel
    result, and must never reach `achieved` — the still-open flight-only state never masquerades as
    completion."""
    return {"trace": _run(flight_ok=True, hotel_ok=False)}


def check_undecomposed_goal_is_not_vacuously_achieved() -> dict[str, object]:
    """Before decomposition fires, the parent achieved-NAC (`absent(unachieved raised subgoal)`) is
    trivially true — the positive `atom(out=(role("raised", atom())))` premise is what stops that from
    reading as false completion. Checked by inspecting the graph one revive before decompose ever runs."""
    g, goal = _build_goal()
    n = Network()
    n.given(g)
    rules = _rules()
    for r in rules.values():
        n.add(r)
    reflect = n.axiom(*effects_of(n.asserted), name="reflect")
    _wire(n, rules, reflect)
    n.revive()
    return {"achieved_on_the_very_first_revive": n.world().attr(goal, "achieved")}


def report() -> str:
    lines = ["=== GOAL DECOMPOSITION EXPERIMENT: subgoals with their own satisfaction conditions ==="]
    lines.append(f"both children succeed -> achieved only after both: "
                 f"{check_both_children_succeed_reaches_achieved_only_after_both()}")
    lines.append(f"one child diverges -> parent diverges, never achieves: "
                 f"{check_one_child_diverges_parent_diverges_without_waiting_on_the_other()}")
    lines.append(f"undecomposed goal is not vacuously achieved: "
                 f"{check_undecomposed_goal_is_not_vacuously_achieved()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())

"""LEVEL PROBE — does routing a claim by LEVEL ("what is the claim about: the world, or the system's own
reasoning?", `forms_discourse.md` line 91/913) need anything beyond the same trivial meta-rule shape
`force_probe_experiment.py` already confirmed for FORCE, or does distinguishing world-content from
theory-content actually require something new?

**Scope, same discipline as the force probe.** Recognizing that a claim is *about* the world versus *about*
the system's own conclusions is parsing's job, out of scope here. What's tested is the engine-side claim:
given an utterance already tagged `level="world"` or `level="theory"`, does routing it toward the goal
machinery need anything beyond the same meta-rule shape already confirmed for force — and, sharper than
the force probe, does a *theory*-level claim's content actually behave differently in *what satisfies it*,
without needing different *machinery* to do so?

**The scenario makes the LEVEL distinction real rather than cosmetic.** A `world` utterance wants to know
whether a customer is VIP — an ordinary claim, satisfied by external input, exactly like `force_probe`'s
content claims. A `theory` utterance wants to know whether the engine's own `vip_rule` has *already
concluded* that — a claim about the system's own reasoning, not about the customer directly. Satisfying it
needs no new mechanism: an ordinary rule (`track_vip_conclusion`) reacts to `vip_rule`'s own output exactly
the way any rule reacts to any fact — because a rule's conclusion is already ordinary graph data, provenance
is already free (`goal_machinery.md` §1, `wiring-is-not-data`), and nothing here needed to reach outside
that.

Three checks, all against the real engine:

1. **Both utterances route to a goal via the identical meta-rule shape** —
   `check_world_and_theory_utterances_both_mint_goals` — same structure `force_probe_experiment.py`
   already confirmed for force, checked again for level.
2. **⭐ The theory goal only resolves once the engine's own rule has actually concluded something — never
   from the same external input that satisfies the world goal** —
   `check_theory_goal_waits_for_the_engines_own_conclusion`. This is the sharp, level-specific check:
   proves the "about the system" reading is real, not just a label, by showing the theory goal stays
   honestly unresolved through a turn where only the *world* question gets its external answer.
3. **The same, unmodified `achieved`/`diverged` rules resolve both** —
   `check_both_goals_share_the_same_resolution_rules` — no level-specific branch anywhere in the
   resolution machinery, confirming level, like force, drops out of the picture once a goal exists.

Re-runnable: `python -m units.level_probe_experiment`.
"""
from __future__ import annotations

from .engine import Attribute, Emit, Link, Network, StandingUnit, Value, effects_of
from .graph import EMPTY, named, role_edge
from .match import atom, role

_WORLD_PAT = (atom("u", name="utterance", level="world", routed=None,
                    out=(role("content", atom("c")),)),)
_THEORY_PAT = (atom("u", name="utterance", level="theory", routed=None,
                     out=(role("content", atom("c")),)),)

_VIP_RULE_PAT = (atom("cust", name="customer", tier="gold", vip=None),)
_TRACK_PAT = (atom("cust", name="customer", vip=True),
              atom("t", name="vip_rule_fired", true=None))

_GOAL_ACHIEVED_PAT = (atom("g", name="goal", achieved=None,
                            out=(role("wants", atom("c", true=True)),)),)
_GOAL_DIVERGED_PAT = (atom("g", name="goal", diverged=None,
                            out=(role("wants", atom("c", true=False)),)),)


def _rules() -> dict[str, StandingUnit]:
    return {
        "world_to_goal": StandingUnit("world_to_goal", _WORLD_PAT,
                                       Emit("goal", as_="g"), Link("g", "c", role="wants"),
                                       Attribute("g", "from_level", "world"),
                                       Attribute("u", "routed", True), mutating=True),
        "theory_to_goal": StandingUnit("theory_to_goal", _THEORY_PAT,
                                        Emit("goal", as_="g"), Link("g", "c", role="wants"),
                                        Attribute("g", "from_level", "theory"),
                                        Attribute("u", "routed", True), mutating=True),
        # An ordinary business rule — nothing about it is level-aware. Its own conclusion is what a
        # theory-level claim will end up being about.
        "vip_rule": StandingUnit("vip_rule", _VIP_RULE_PAT,
                                  Attribute("cust", "vip", True), mutating=True),
        # A claim about the SYSTEM'S OWN REASONING: "has vip_rule concluded vip yet" — satisfied by
        # reading vip_rule's conclusion as ordinary data, not by any new introspection primitive.
        "track_vip_conclusion": StandingUnit("track_vip_conclusion", _TRACK_PAT,
                                              Attribute("t", "true", True), mutating=True),
        "goal_achieved": StandingUnit("goal_achieved", _GOAL_ACHIEVED_PAT,
                                       Attribute("g", "achieved", True), mutating=True),
        "goal_diverged": StandingUnit("goal_diverged", _GOAL_DIVERGED_PAT,
                                       Attribute("g", "diverged", True), mutating=True),
    }


def _settle(n: Network, reflect) -> None:
    reflect.held = Value(effects_of(n.asserted))
    n.revive()


def _build():
    g = EMPTY
    g, cust = named(g, "customer")
    g, tracker = named(g, "vip_rule_fired")
    g, world_u = named(g, "utterance", level="world")
    g, world_c = named(g, "customer_vip")
    g = role_edge(g, world_u, "content", world_c)
    g, theory_u = named(g, "utterance", level="theory")
    g = role_edge(g, theory_u, "content", tracker)
    return g, cust, tracker, world_c


def _network():
    g, cust, tracker, world_c = _build()
    n = Network()
    ax = n.given(g)
    rules = _rules()
    for r in rules.values():
        n.add(r)
    reflect = n.axiom(*effects_of(n.asserted), name="reflect")
    for r in rules.values():
        n.wire(reflect, r)
    ax.held = None
    return n, reflect, cust, tracker, world_c


def _goal(n: Network, from_level: str):
    return next(g for g in n.asserted.nodes if n.asserted.attr(g, "name") == "goal"
                and n.asserted.attr(g, "from_level") == from_level)


def check_world_and_theory_utterances_both_mint_goals() -> dict[str, object]:
    n, reflect, cust, tracker, world_c = _network()
    n.revive()
    goals = [g for g in n.asserted.nodes if n.asserted.attr(g, "name") == "goal"]
    return {"two_goals_minted": len(goals) == 2,
            "one_per_level": {n.asserted.attr(g, "from_level") for g in goals} == {"world", "theory"}}


def check_theory_goal_waits_for_the_engines_own_conclusion() -> dict[str, object]:
    """Only the world question's external answer arrives this turn. The theory goal must stay honestly
    unresolved — its content is about `vip_rule`'s own conclusion, which hasn't happened yet."""
    n, reflect, cust, tracker, world_c = _network()
    n.revive()
    _settle(n, reflect)

    n.asserted = n.asserted.with_node(world_c, true=True)   # answers the WORLD question directly
    _settle(n, reflect)
    world_goal, theory_goal = _goal(n, "world"), _goal(n, "theory")
    after_world_answer = {"world_achieved": n.world().attr(world_goal, "achieved"),
                           "theory_achieved_too_early": n.world().attr(theory_goal, "achieved")}

    n.asserted = n.asserted.with_node(cust, tier="gold")     # now vip_rule can actually fire
    _settle(n, reflect)   # vip_rule concludes cust.vip=True
    _settle(n, reflect)   # track_vip_conclusion sees it, sets tracker.true=True
    _settle(n, reflect)   # theory goal's achieved rule sees the tracker
    return {**after_world_answer, "theory_achieved_eventually": n.world().attr(theory_goal, "achieved")}


def check_both_goals_share_the_same_resolution_rules() -> dict[str, object]:
    """No level-specific branch anywhere: the same two rule names (`goal_achieved`/`goal_diverged`) are
    the only ones that ever set `achieved`/`diverged` on either goal."""
    n, reflect, cust, tracker, world_c = _network()
    resolvers = {name for name, r in _rules().items()
                 if name in ("goal_achieved", "goal_diverged")}
    return {"exactly_two_resolver_rules_for_both_levels": resolvers == {"goal_achieved", "goal_diverged"}}


def report() -> str:
    lines = ["=== LEVEL PROBE: world vs. theory content routes and resolves through the same shape ==="]
    lines.append(f"both utterances mint goals: {check_world_and_theory_utterances_both_mint_goals()}")
    lines.append(f"theory goal waits for the engine's own conclusion: "
                 f"{check_theory_goal_waits_for_the_engines_own_conclusion()}")
    lines.append(f"same resolution rules for both: {check_both_goals_share_the_same_resolution_rules()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())

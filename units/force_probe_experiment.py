"""FORCE PROBE — does recognizing "this is a question" or "this is a command" need anything beyond
parsing (out of scope here, already a separate concern per `force-is-the-missing-axis`) plus one trivial
meta-rule minting a goal, the same way causation was actually checked rather than assumed?

**Scope, deliberately narrow, matching how every other probe this session was scoped.** This does not
build natural-language recognition — `force-is-the-missing-axis` already establishes force as an *intake
route*, decided upstream of anything here. What's tested is the engine-side claim from
`closed_class_rechallenged.md`: given an utterance already tagged with its force (a black box upstream —
parsing is `cnl.md`'s job, not this one), does routing "ask" and "command" to the goal machinery need
anything beyond a meta-rule that mints a goal wanting the utterance's content? And does the resulting goal
then behave exactly like any other goal, with nothing force-specific downstream?

**The two routing rules are deliberately near-identical**, differing only in which literal force value
they match — that similarity is itself the finding, not an oversight: if "ask" and "command" needed
materially different machinery to route, the two rules would look different. They don't.

Three checks, all against the real engine:

1. **An `ask` utterance mints a goal wanting its content** — `check_ask_utterance_mints_a_goal`. The
   utterance is consumption-marked (`routed=True`) in the same firing, reusing
   `idempotent_mutation_experiment.py`'s discipline — nothing here is a one-shot special case exempt from
   that lesson.
2. **A `command` utterance mints a goal the same way** — `check_command_utterance_mints_a_goal_the_same_
   way` — identical mechanism, different literal.
3. **⭐ The payoff: both resulting goals resolve via the ordinary, unmodified `achieved`/`diverged`
   machinery from `goal_experiment.py`, with nothing reading which force produced them** —
   `check_both_goals_resolve_via_ordinary_achieved_diverged`. The achieved/diverged rules wired here are
   not force-aware at all; they don't need to be, because by the time a goal exists, its origin force has
   already done its only job (deciding that a goal should exist at all) and dropped out of the picture.

Re-runnable: `python -m units.force_probe_experiment`.
"""
from __future__ import annotations

from .engine import Network, Value, effects_of
from .goal_rules import rules as _rules
from .graph import EMPTY, named, role_edge


def _find(g, name: str):
    return next(n for n in g.nodes if g.attrs.get(n, {}).get("name") == name)


def _settle(n: Network, reflect) -> None:
    reflect.held = Value(effects_of(n.asserted))
    n.revive()


def _build():
    g = EMPTY
    g, ask_u = named(g, "utterance", force="ask")
    g, ask_c = named(g, "customer_tier_known")
    g = role_edge(g, ask_u, "content", ask_c)
    g, cmd_u = named(g, "utterance", force="command")
    g, cmd_c = named(g, "ticket_closed")
    g = role_edge(g, cmd_u, "content", cmd_c)
    return g, ask_u, ask_c, cmd_u, cmd_c


def _network():
    g, ask_u, ask_c, cmd_u, cmd_c = _build()
    n = Network()
    ax = n.given(g)
    rules = _rules()
    for r in rules.values():
        n.add(r)
    reflect = n.axiom(*effects_of(n.asserted), name="reflect")
    for r in rules.values():
        n.wire(reflect, r)
    ax.held = None
    return n, reflect, ask_c, cmd_c


def check_ask_utterance_mints_a_goal() -> dict[str, object]:
    """One meta-rule, matching the `ask` literal, mints a goal wanting the utterance's content — and the
    utterance is consumption-marked so it never mints a second goal on a later idle turn."""
    n, reflect, ask_c, cmd_c = _network()
    n.revive()
    counts = [sum(1 for x in n.asserted.nodes if n.asserted.attr(x, "name") == "goal")]
    for _ in range(2):
        _settle(n, reflect)
        counts.append(sum(1 for x in n.asserted.nodes if n.asserted.attr(x, "name") == "goal"))
    goal = next(g for g in n.asserted.nodes if n.asserted.attr(g, "name") == "goal"
                and n.asserted.attr(g, "from_force") == "ask")
    return {"goal_count_per_turn": counts, "wants_the_ask_content":
                n.asserted.out(goal) and ask_c in [d for r in n.asserted.out(goal)
                                                    for d in n.asserted.out(r)]}


def check_command_utterance_mints_a_goal_the_same_way() -> dict[str, object]:
    """Identical mechanism, only the matched literal differs."""
    n, reflect, ask_c, cmd_c = _network()
    n.revive()
    goal = next(g for g in n.asserted.nodes if n.asserted.attr(g, "name") == "goal"
                and n.asserted.attr(g, "from_force") == "command")
    return {"minted_from_command": goal is not None,
            "wants_the_command_content":
                cmd_c in [d for r in n.asserted.out(goal) for d in n.asserted.out(r)]}


def check_both_goals_resolve_via_ordinary_achieved_diverged() -> dict[str, object]:
    """Neither `goal_achieved` nor `goal_diverged` is force-aware — they don't need to be. The question's
    goal resolves `achieved` when its content is confirmed known; the command's goal resolves `diverged`
    when the world-state it wanted never came true — same rules, same shape, no force-specific reads."""
    n, reflect, ask_c, cmd_c = _network()
    n.revive()
    _settle(n, reflect)  # both goals now visible through "in"

    n.asserted = n.asserted.with_node(ask_c, true=True)     # the question gets answered
    n.asserted = n.asserted.with_node(cmd_c, true=False)    # the command's world-state never happens
    _settle(n, reflect)

    ask_goal = next(g for g in n.asserted.nodes if n.asserted.attr(g, "name") == "goal"
                     and n.asserted.attr(g, "from_force") == "ask")
    cmd_goal = next(g for g in n.asserted.nodes if n.asserted.attr(g, "name") == "goal"
                     and n.asserted.attr(g, "from_force") == "command")
    return {"ask_goal_achieved": n.world().attr(ask_goal, "achieved"),
            "command_goal_diverged": n.world().attr(cmd_goal, "diverged")}


def report() -> str:
    lines = ["=== FORCE PROBE: ask/command routing needs nothing beyond one meta-rule minting a goal ==="]
    lines.append(f"ask utterance mints a goal: {check_ask_utterance_mints_a_goal()}")
    lines.append(f"command utterance mints a goal, same mechanism: "
                 f"{check_command_utterance_mints_a_goal_the_same_way()}")
    lines.append(f"both resolve via ordinary, force-blind achieved/diverged: "
                 f"{check_both_goals_resolve_via_ordinary_achieved_diverged()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())

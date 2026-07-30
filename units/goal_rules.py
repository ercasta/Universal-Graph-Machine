"""GOAL ROUTING RULES — the small, generic meta-rules `force_probe_experiment.py` and `level_probe_
experiment.py` checked, promoted from probe scripts into a shared, reusable library.

This is the natural next step once a probe's finding is actually trusted: a probe script proves a mechanism
in isolation and is free to keep its own copy for the record, but once something real is built *on top* of
the finding (the CNL boundary, `cnl.py`), the rule itself belongs in one place both the probe and the real
system import — never redefined twice by hand, which is exactly the "declare it once, read it generically"
discipline this whole arc has been about, applied to our own code instead of to KB content for once.

Every rule here is verbatim what was checked: `ask_to_goal`/`command_to_goal` mint a goal wanting the
utterance's content and mark the utterance consumed in the same firing (`force_probe_experiment.py`);
`goal_achieved`/`goal_diverged` are force-blind and level-blind, resolving any goal whose `wants` content
settles true or false. Nothing here recognizes intent — every pattern matches an already-marked `force`
attribute, never infers one.
"""
from __future__ import annotations

from .engine import Attribute, Emit, Link, StandingUnit
from .match import atom, role

ASK_PAT = (atom("u", name="utterance", force="ask", routed=None,
                 out=(role("content", atom("c")),)),)
COMMAND_PAT = (atom("u", name="utterance", force="command", routed=None,
                     out=(role("content", atom("c")),)),)

GOAL_ACHIEVED_PAT = (atom("g", name="goal", achieved=None,
                           out=(role("wants", atom("c", true=True)),)),)
GOAL_DIVERGED_PAT = (atom("g", name="goal", diverged=None,
                           out=(role("wants", atom("c", true=False)),)),)


def ask_to_goal_rule() -> StandingUnit:
    return StandingUnit("ask_to_goal", ASK_PAT,
                         Emit("goal", as_="g"), Link("g", "c", role="wants"),
                         Attribute("g", "from_force", "ask"), Attribute("u", "routed", True),
                         mutating=True)


def command_to_goal_rule() -> StandingUnit:
    return StandingUnit("command_to_goal", COMMAND_PAT,
                         Emit("goal", as_="g"), Link("g", "c", role="wants"),
                         Attribute("g", "from_force", "command"), Attribute("u", "routed", True),
                         mutating=True)


def goal_achieved_rule() -> StandingUnit:
    return StandingUnit("goal_achieved", GOAL_ACHIEVED_PAT,
                         Attribute("g", "achieved", True), mutating=True)


def goal_diverged_rule() -> StandingUnit:
    return StandingUnit("goal_diverged", GOAL_DIVERGED_PAT,
                         Attribute("g", "diverged", True), mutating=True)


def rules() -> dict[str, StandingUnit]:
    return {
        "ask_to_goal": ask_to_goal_rule(),
        "command_to_goal": command_to_goal_rule(),
        "goal_achieved": goal_achieved_rule(),
        "goal_diverged": goal_diverged_rule(),
    }


__all__ = ["ASK_PAT", "COMMAND_PAT", "GOAL_ACHIEVED_PAT", "GOAL_DIVERGED_PAT",
           "ask_to_goal_rule", "command_to_goal_rule", "goal_achieved_rule", "goal_diverged_rule", "rules"]

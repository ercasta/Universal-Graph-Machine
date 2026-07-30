"""THE CNL BOUNDARY, END TO END — the first time anything in this project has gone natural-language prompt
→ CNL text → parsed graph → the real engine, rather than graph data built by hand in Python.

Every check below starts from a comment giving the natural-language prompt an LLM would have received, and
the CNL text immediately below it is what that translation step is claimed to produce — playing the
translator's part by hand, the same discipline `docs/units/cnl.md`/`forms_cnl.md` describe, so the claim
can be checked rather than assumed. Nothing about the engine side is new: `units/goal_rules.py`'s
`ask_to_goal`/`command_to_goal`/`goal_achieved`/`goal_diverged` are imported unmodified, verbatim what
`force_probe_experiment.py` already checked — this file's only job is to prove the *parsed-text* path
reaches the identical place the hand-built-graph path already did.
"""
from __future__ import annotations

from units.cnl import parse
from units.engine import Network, Value, effects_of
from units.goal_rules import rules


def _settle(n: Network, reflect) -> None:
    reflect.held = Value(effects_of(n.asserted))
    n.revive()


def _network(g):
    n = Network()
    ax = n.given(g)
    rule_set = rules()
    for r in rule_set.values():
        n.add(r)
    reflect = n.axiom(*effects_of(n.asserted), name="reflect")
    for r in rule_set.values():
        n.wire(reflect, r)
    ax.held = None
    return n, reflect


def test_a_question_translates_through_parsed_cnl_into_a_goal_that_resolves_achieved():
    # Prompt: "Is the customer's loyalty tier already known?"
    g, u = parse("[utterance | force: ask | content: [tier_known | agent: customer]]")

    n, reflect = _network(g)
    n.revive()

    goal = next(x for x in n.asserted.nodes if n.asserted.attr(x, "name") == "goal"
                and n.asserted.attr(x, "from_force") == "ask")
    tier_known = next(x for x in n.asserted.nodes if n.asserted.attr(x, "name") == "tier_known")
    wanted = [d for r in n.asserted.out(goal) for d in n.asserted.out(r)]
    assert tier_known in wanted
    assert n.world().attr(goal, "achieved") is None      # not yet — nothing has confirmed it

    n.asserted = n.asserted.with_node(tier_known, true=True)   # the world confirms it
    _settle(n, reflect)

    assert n.world().attr(goal, "achieved") is True


def test_a_command_translates_through_parsed_cnl_into_a_goal_that_can_diverge():
    # Prompt: "Close the support ticket."
    g, u = parse("[utterance | force: command | content: ticket_closed]")

    n, reflect = _network(g)
    n.revive()
    _settle(n, reflect)

    goal = next(x for x in n.asserted.nodes if n.asserted.attr(x, "name") == "goal"
                and n.asserted.attr(x, "from_force") == "command")
    ticket_closed = next(x for x in n.asserted.nodes if n.asserted.attr(x, "name") == "ticket_closed")

    n.asserted = n.asserted.with_node(ticket_closed, true=False)   # the world says it never happened
    _settle(n, reflect)

    assert n.world().attr(goal, "diverged") is True


def test_the_utterance_is_consumption_marked_through_the_parsed_path_too():
    """The same `idempotent_mutation_experiment.py` discipline `force_probe_experiment.py` already checked
    (a repeat revive must not mint a second goal) — re-checked here because it depends on the *parsed*
    utterance node actually being the one both `ask_to_goal`'s pattern and its own `Attribute("u", "routed",
    True)` effect bind to. A parser bug minting two different nodes for what should be one utterance would
    break this silently rather than loudly."""
    # Prompt: "Is the customer's loyalty tier already known?"
    g, u = parse("[utterance | force: ask | content: [tier_known | agent: customer]]")
    n, reflect = _network(g)

    n.revive()
    counts = [sum(1 for x in n.asserted.nodes if n.asserted.attr(x, "name") == "goal")]
    for _ in range(2):
        _settle(n, reflect)
        counts.append(sum(1 for x in n.asserted.nodes if n.asserted.attr(x, "name") == "goal"))
    assert counts == [1, 1, 1]

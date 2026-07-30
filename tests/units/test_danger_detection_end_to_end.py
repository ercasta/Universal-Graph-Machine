""""DON'T DO ANYTHING DANGEROUS" — end to end, the scenario that started this whole line of questioning.

Two natural-language prompts, both translated by hand into CNL text (playing the translator's part, same
discipline as `test_cnl_end_to_end.py`), both driven through the real engine via `units/cnl.py`'s parser:

1. KB authoring: "The production database is dangerous." — `force: author`, routed through
   `units/author_rules.py` and `units/prohibition_rules.py`'s generic propagation, entirely independent of
   any specific command.
2. An interactive command: "Delete the production database." — `force: command`, routed through
   `units/goal_rules.py`'s completely unmodified `command_to_goal`, then vetoed by
   `units/prohibition_rules.py`'s `attempt_command` watcher.

Nothing here is a new mechanism: every rule involved was checked in isolation
(`test_author_rules.py`, `test_prohibition_rules.py`, `test_cnl_end_to_end.py`). This file's only job is to
prove the two utterances — authored independently, in either order — compose correctly when both arrive as
parsed text rather than hand-built graph data, which is the actual shape a live session would take.
"""
from units.author_rules import rules as author_rules
from units.cnl import parse
from units.engine import Network, Value, effects_of
from units.goal_rules import rules as goal_rules
from units.identity_rules import rules as identity_rules
from units.prohibition_rules import rules as prohibition_rules


def _settle(n: Network, reflect) -> None:
    reflect.held = Value(effects_of(n.asserted))
    n.revive()


def _network(g):
    n = Network()
    ax = n.given(g)
    rule_set = {**author_rules(), **goal_rules(), **prohibition_rules(), **identity_rules()}
    for r in rule_set.values():
        n.add(r)
    reflect = n.axiom(*effects_of(n.asserted), name="reflect")
    for r in rule_set.values():
        n.wire(reflect, r)
    ax.held = None
    return n, reflect


def test_a_command_is_vetoed_by_a_danger_declared_first_both_through_parsed_cnl():
    # Prompt 1: "The production database is dangerous."
    g, u1 = parse("[utterance | force: author | content: [dangerous | target: production_database]]")
    # Prompt 2: "Delete the production database."
    g, u2 = parse("[utterance | force: command | content: [delete | target: production_database]]",
                   into=g)

    n, reflect = _network(g)
    n.revive()

    goal = next(x for x in n.asserted.nodes if n.asserted.attr(x, "name") == "goal"
                and n.asserted.attr(x, "from_force") == "command")
    executed_per_idle_turn = []
    for _ in range(4):
        _settle(n, reflect)
        executed_per_idle_turn.append(n.world().attr(goal, "executed"))

    assert executed_per_idle_turn == [None, None, None, None]


def test_the_same_two_prompts_in_the_opposite_order_still_veto():
    """A live session doesn't guarantee the danger gets declared before the command is issued — the
    prohibition must compose regardless of authoring order, the same order-independence
    `substitution_experiment.py` already checked for `define`."""
    # Prompt 1: "Delete the production database."
    g, u1 = parse("[utterance | force: command | content: [delete | target: production_database]]")
    # Prompt 2: "The production database is dangerous."
    g, u2 = parse("[utterance | force: author | content: [dangerous | target: production_database]]",
                   into=g)

    n, reflect = _network(g)
    n.revive()

    goal = next(x for x in n.asserted.nodes if n.asserted.attr(x, "name") == "goal"
                and n.asserted.attr(x, "from_force") == "command")
    executed_per_idle_turn = []
    for _ in range(4):
        _settle(n, reflect)
        executed_per_idle_turn.append(n.world().attr(goal, "executed"))

    assert executed_per_idle_turn == [None, None, None, None]


def test_a_command_with_no_declared_danger_executes_normally_through_parsed_cnl():
    # Prompt: "Restart the reporting job."
    g, u = parse("[utterance | force: command | content: [restart | target: reporting_job]]")

    n, reflect = _network(g)
    n.revive()
    _settle(n, reflect)

    goal = next(x for x in n.asserted.nodes if n.asserted.attr(x, "name") == "goal"
                and n.asserted.attr(x, "from_force") == "command")
    assert n.world().attr(goal, "executed") is True

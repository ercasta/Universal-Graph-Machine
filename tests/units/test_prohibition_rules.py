"""`units/prohibition_rules.py` — a declared `dangerous` fact propagates into a `forbidden` fact, which
vetoes an unrelated command's goal from ever being marked `executed`."""
from units.engine import Network, Value, effects_of
from units.goal_rules import rules as goal_rules
from units.graph import EMPTY, named, role_edge
from units.prohibition_rules import rules as prohibition_rules


def _settle(n: Network, reflect) -> None:
    reflect.held = Value(effects_of(n.asserted))
    n.revive()


def _network(g):
    n = Network()
    ax = n.given(g)
    rule_set = {**goal_rules(), **prohibition_rules()}
    for r in rule_set.values():
        n.add(r)
    reflect = n.axiom(*effects_of(n.asserted), name="reflect")
    for r in rule_set.values():
        n.wire(reflect, r)
    ax.held = None
    return n, reflect


def _build(with_dangerous: bool):
    g = EMPTY
    g, db = named(g, "production_database")
    if with_dangerous:
        g, dangerous = named(g, "dangerous")
        g = role_edge(g, dangerous, "target", db)
    g, cmd_u = named(g, "utterance", force="command")
    g, act = named(g, "delete")
    g = role_edge(g, act, "target", db)
    g = role_edge(g, cmd_u, "content", act)
    return g


def test_dangerous_propagates_into_forbidden_via_the_generic_rule():
    g = _build(with_dangerous=True)
    n, reflect = _network(g)
    n.revive()
    forbidden = [x for x in n.asserted.nodes if n.asserted.attr(x, "name") == "forbidden"]
    assert len(forbidden) == 1
    (target_role,) = n.world().out(forbidden[0])
    (target,) = n.world().out(target_role)
    assert n.world().attr(target, "name") == "production_database"


def test_forbidden_propagation_is_get_or_create_not_reminted_every_revive():
    g = _build(with_dangerous=True)
    n, reflect = _network(g)
    n.revive()
    counts = [sum(1 for x in n.asserted.nodes if n.asserted.attr(x, "name") == "forbidden")]
    for _ in range(2):
        _settle(n, reflect)
        counts.append(sum(1 for x in n.asserted.nodes if n.asserted.attr(x, "name") == "forbidden"))
    assert counts == [1, 1, 1]


def test_a_command_targeting_a_declared_dangerous_thing_never_gets_executed():
    g = _build(with_dangerous=True)
    n, reflect = _network(g)
    n.revive()

    goal = next(x for x in n.asserted.nodes if n.asserted.attr(x, "name") == "goal"
                and n.asserted.attr(x, "from_force") == "command")
    executed_per_idle_turn = []
    for _ in range(4):
        _settle(n, reflect)
        executed_per_idle_turn.append(n.world().attr(goal, "executed"))

    assert executed_per_idle_turn == [None, None, None, None]


def test_the_same_command_executes_when_nothing_forbids_it():
    """The control case — without a declared danger, the identical command's goal does get executed.
    Confirms the veto is doing real work, not silencing every command unconditionally."""
    g = _build(with_dangerous=False)
    n, reflect = _network(g)
    n.revive()
    _settle(n, reflect)

    goal = next(x for x in n.asserted.nodes if n.asserted.attr(x, "name") == "goal"
                and n.asserted.attr(x, "from_force") == "command")
    assert n.world().attr(goal, "executed") is True

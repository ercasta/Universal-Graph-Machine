"""`units/author_rules.py` — authoring a fact via `force="author"`."""
from units.author_rules import rules
from units.cnl import parse
from units.engine import Network, Value, effects_of


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


def test_authoring_a_fact_marks_the_utterance_consumed():
    g, u = parse("[utterance | force: author | content: [dangerous | target: production_database]]")
    n, reflect = _network(g)
    n.revive()
    assert n.world().attr(u, "routed") is True


def test_the_authored_fact_is_ordinary_reachable_graph_data_needing_no_activation():
    g, u = parse("[utterance | force: author | content: [dangerous | target: production_database]]")
    n, reflect = _network(g)
    n.revive()
    dangerous = next(x for x in n.asserted.nodes if n.asserted.attr(x, "name") == "dangerous")
    target = next(x for x in n.asserted.nodes if n.asserted.attr(x, "name") == "production_database")
    (target_role,) = n.world().out(dangerous)
    assert n.world().out(target_role) == (target,)


def test_authoring_is_idempotent_across_repeated_revives():
    """The same `idempotent_mutation_experiment.py` discipline every other consumption-marked rule in
    this project follows — a repeated revive must not re-process the same authored utterance."""
    g, u = parse("[utterance | force: author | content: [dangerous | target: production_database]]")
    n, reflect = _network(g)
    n.revive()
    counts = [sum(1 for x in n.asserted.nodes if n.asserted.attr(x, "name") == "dangerous")]
    for _ in range(2):
        _settle(n, reflect)
        counts.append(sum(1 for x in n.asserted.nodes if n.asserted.attr(x, "name") == "dangerous"))
    assert counts == [1, 1, 1]


def test_content_shaped_with_a_when_role_is_left_untouched_by_the_fact_rule():
    """The deliberate seam where rule-authoring will plug in later: `author_fact_rule`'s NAC must refuse
    to fire on conditional-shaped content, rather than silently treating a future rule as an inert fact."""
    g, u = parse("[utterance | force: author | "
                  "content: [ships_early | when: [order_value] | then: [flagged]]]")
    n, reflect = _network(g)
    n.revive()
    assert n.world().attr(u, "routed") is None

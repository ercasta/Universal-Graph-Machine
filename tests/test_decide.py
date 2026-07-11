"""
Forcing a decision — negation decided-on-demand, now expressed as RULES (decide.py).

Completion is a generated rule (`completion_rule`) that materializes an explicit `is_not` for the
closed-world tuples a consumer's positive residual scopes; a consumer matches that negative
POSITIVELY (no NAC). Completion is AGGRESSIVE + MONOTONE (no NAC — an object-blind stratification
false-cycle through the copula, see decide.completion_rule); where the positive turns out derivable,
`DEFEAT_SEED` + `retraction.RETRACT_RULES` cascade-hide the over-completed negative and anything it
fed. `decide.solve` runs derivation+completion (provenance on) then the retraction pass (off).
"""
import ugm as h
from ugm import decide, retraction as ret

# The domain (the spike's shape), now with completion + consumer as ordinary rules:
#   producer:  urgent(?c)         when ?c wants rush
#   completion: ?c is_not urgent  for closed-world customers (aggressive; defeat repairs)
#   consumer:  ?c served regular  when ?c is a customer and ?c is_not urgent   (NAC GONE)
PRODUCER = h.Rule(key="urgent.rush",
                  lhs=[h.Pat("?c", "wants", "rush")],
                  rhs=[h.Pat("?c", "is", "urgent")])
CONSUMER = h.Rule(key="serve.regular",
                  lhs=[h.Pat("?c", "is_a", "customer"), h.Pat("?c", "is_not", "urgent")],
                  rhs=[h.Pat("?c", "served", "regular")])
COMPLETION = decide.completion_rule("?c", "urgent",
                                    [h.Pat("?c", "is_a", "customer")], "decide.complete.urgent.t")
RULES = [PRODUCER, CONSUMER, COMPLETION]


def _any_relation(g, pred):
    """Does a fully-instantiated  ?x -[pred]-> ?y  relation exist anywhere in the graph?"""
    return any(g.has_key(r, pred) and g.pred(r) and g.succ(r) for r in g.nodes())


def _objs(g, subj_name, pred):
    return [g.name(o) for s in g.nodes_named(subj_name)
            for r, o in g.relations_from(s) if g.has_key(r, pred)]


def _setup(closed=True):
    """alice is an urgent customer (wants rush); bob is a customer who does not."""
    g = h.Graph()
    for who in ("alice", "bob"):
        g.add_relation(g.add_node(who), "is_a", g.add_node("customer"))
    g.add_relation(g.nodes_named("alice")[0], "wants", g.add_node("rush"))
    if closed:
        decide.declare_closed_world(g, "urgent")
    return g


def test_closed_world_is_per_predicate_data():
    g = h.Graph()
    assert not decide.is_closed_world(g, "urgent")
    decide.declare_closed_world(g, "urgent")
    assert decide.is_closed_world(g, "urgent")
    assert not decide.is_closed_world(g, "happy")      # open-world by default


def test_completion_rule_shape():
    r = decide.completion_rule("?c", "urgent", [h.Pat("?c", "is_a", "customer")], "k")
    assert not r.nac                                    # aggressive: no NAC (copula false-cycle)
    assert ("?c", "is_not", "urgent") in {p.tokens() for p in r.rhs}     # materializes the negative
    assert ("urgent?", "closes", "<closed_world>") in {p.tokens() for p in r.lhs}   # CWA-gated


def test_completion_materializes_the_negative_consumer_matches_positively():
    g = _setup()
    decide.solve(g, RULES)
    bob = g.nodes_named("bob")[0]
    assert decide.negative_holds(g, bob, "urgent")     # bob (not urgent) is completed
    assert "regular" in _objs(g, "bob", "served")      # consumer matched the POSITIVE is_not


def test_derivable_positive_defeats_the_completion_and_cascades():
    # alice wants rush -> urgent(alice) is derivable, so her aggressive completion is DEFEATED:
    # `is urgent` and `is_not urgent` coexist -> retract + cascade hides the negative AND the
    # `served regular` it fed.
    g = _setup()
    decide.solve(g, RULES)
    alice = g.nodes_named("alice")[0]
    assert decide.positive_holds(g, alice, "urgent")           # derived
    assert not decide.negative_holds(g, alice, "urgent")       # completion defeated (hidden)
    assert "regular" not in _objs(g, "alice", "served")        # its consequence withdrawn too


def test_open_world_is_never_completed():
    # without a closed-world declaration the CWA gate fails -> completion never fires -> no negative,
    # so the consumer stays silent (an unproven positive is UNKNOWN, never materialized negative).
    g = _setup(closed=False)
    decide.solve(g, RULES)
    for who in ("alice", "bob"):
        assert not decide.negative_holds(g, g.nodes_named(who)[0], "urgent")
        assert "regular" not in _objs(g, who, "served")


def test_solve_is_a_noop_without_decisions():
    # an ordinary bank (no completion rule, nothing closed-world) behaves as plain run_rules.
    g = h.Graph()
    g.add_relation(g.add_node("a"), "r", g.add_node("b"))
    decide.solve(g, [h.Rule(key="r.s", lhs=[h.Pat("?x", "r", "?y")], rhs=[h.Pat("?x", "s", "?y")])])
    assert _any_relation(g, "s")
    assert not g.nodes_named(ret.RETRACT)              # no retraction seeded

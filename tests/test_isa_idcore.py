"""Stage 3 of coreference-as-rules (docs/coreference_as_rules_design.md) — the id-addressed core.

The demand chain's env now binds node IDS in free slots (`chain._facts_matching` returns a `ById` for a
discovered node, not its name). The load-bearing payoff: two DISTINCT nodes that happen to share a NAME
bind to DISTINCT variables, so a same-NAME value-match RELATES them (`same_as(a1, a2)`) instead of
collapsing to one binding and emitting only a self-loop. This is exactly the case Stages 1-2 could not
reach on the name-keyed core (see the design doc's "load-bearing finding").
"""
from ugm import (AttrGraph, ById, Pat, Rule, ValueMatch, write_rule, chain_sip, check,
                 same_as_rules, POSITIVE, ASSUMED_NO)


def _two_ada_persons() -> tuple[AttrGraph, str, str]:
    """Two DISTINCT nodes both named 'ada', each a person — NOT coref-linked, NOT merged."""
    g = AttrGraph()
    a1, a2 = g.add_node("ada"), g.add_node("ada")
    for a in (a1, a2):
        g.add_relation(a, "is_a", g.add_node("person"))
    return g, a1, a2


def _coref_rule_obj() -> Rule:
    return Rule(key="coref",
                lhs=[Pat("?x", "is_a", "person"), Pat("?y", "is_a", "person")],
                rhs=[Pat("?x", "same_as", "?y")],
                value_matches=[ValueMatch("?x", "?y", "name")])


def _rule_graph(*rules: Rule) -> AttrGraph:
    rg = AttrGraph()
    for r in rules:
        write_rule(rg, r)
    return rg


def _same_as_id_pairs(g: AttrGraph) -> set[tuple[str, str]]:
    """`same_as` relations read by NODE ID (not name — the point is distinguishing same-named nodes)."""
    out: set[tuple[str, str]] = set()
    for r in g.nodes():
        if g.predicate(r) != "same_as":
            continue
        for s in g.pred(r):
            if g.is_control(s):
                continue
            for o in g.succ(r):
                if not g.is_control(o):
                    out.add((s, o))
    return out


# --- the headline: same-name coref now relates two DISTINCT nodes ----------------------------------

def test_same_name_coref_relates_two_distinct_nodes():
    g, a1, a2 = _two_ada_persons()
    chain_sip(g, ("same_as", None, None), rules=_rule_graph(_coref_rule_obj()))
    pairs = _same_as_id_pairs(g)
    # the CROSS pair between the two distinct 'ada' nodes now exists (the rule is symmetric, so both
    # directions fire). On the name-keyed core both vars collapsed to name "ada" and only a self-loop
    # could ever be emitted — this assertion was unreachable before the id-addressed core.
    assert (a1, a2) in pairs and (a2, a1) in pairs
    assert a1 != a2                                   # genuinely distinct nodes, not one merged entity


def test_same_name_coref_id_seeded_goal_pins_one_side():
    # seed one side by id: `?x` is pinned to a1, `?y` ranges free and binds the OTHER ada by id.
    g, a1, a2 = _two_ada_persons()
    chain_sip(g, ("same_as", ById(a1), None), rules=_rule_graph(_coref_rule_obj()))
    assert (a1, a2) in _same_as_id_pairs(g)


# --- composition across the derived same-name link -------------------------------------------------

def test_same_name_coref_composes_a_fact_across_the_link():
    g, a1, a2 = _two_ada_persons()
    g.add_relation(a1, "likes", g.add_node("tea"))    # only the FIRST ada mention carries the fact
    rg = _rule_graph(_coref_rule_obj(), *same_as_rules(["likes", "same_as"]))
    # a2 has no `likes` of its own; it inherits a1's via the coref `same_as` the id-core lets the rule
    # derive between the two distinct nodes, then `same_as_rules` propagate `likes` across it.
    assert check(g, ("likes", ById(a2), "tea"), rules=rg) == POSITIVE


def test_composition_gate_no_coref_rule_no_crossing():
    # SAME facts, only the `same_as` propagation but NOT the coref rule -> nothing links the two adas,
    # so a2 does not inherit a1's `likes` (coref is DATA, never baked into the matcher).
    g, a1, a2 = _two_ada_persons()
    g.add_relation(a1, "likes", g.add_node("tea"))
    rg = _rule_graph(*same_as_rules(["likes", "same_as"]))
    assert check(g, ("likes", ById(a2), "tea"), rules=rg) == ASSUMED_NO

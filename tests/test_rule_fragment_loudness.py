"""Learning arc S1 — a malformed rule fragment fails LOUDLY (`rules_in_graph`).

`write_rule` used to be the only way a rule fragment arose, so reading a malformed one was
unreachable and its handling was never hardened. Rule-writing rules (docs/design/learning_design.md)
make malformed fragments an ORDINARY authoring error, and all three prior failure modes were the
"quietly does less / fails obscurely" shape the pystrider feedback targets:

  1. a missing endpoint      -> bare `IndexError: list index out of range` (no rule named)
  2. a duplicated endpoint   -> SILENTLY kept the first and dropped the rest
  3. a non-relation middle   -> SILENTLY yielded `Pat('', '', '')`, a rule matching nothing

All three must now raise a `ValueError` that names the rule and the role. Spike:
`bench/spike_rule_learning.py` L2.
"""
import pytest

import ugm as h
from ugm import AttrGraph, Pat, Rule


def _rule_node(g, name="r"):
    return g.add_node(name, control=True)


# ---------------------------------------------------------------------------
# The three malformed shapes
# ---------------------------------------------------------------------------

def test_role_edge_to_bare_node_is_loud():
    """What a rule-writing rule ACTUALLY produces if it targets the fact-shaped schema: the RHS
    writes the role edge, but cannot build the 2-hop atom, so the role edge points at a bare
    skolem. Previously `IndexError`."""
    g = AttrGraph()
    R = _rule_node(g, "learn.naive")
    g.add_relation(R, "lhs", g.add_node("atom", control=True), control=True)

    with pytest.raises(ValueError) as e:
        h.rules_in_graph(g)
    msg = str(e.value)
    assert "learn.naive" in msg          # names the offending rule
    assert "lhs" in msg                  # ...and the role
    assert "not a relation node" in msg


def test_non_relation_middle_node_is_loud():
    """A middle node with real in/out edges but no predicate key: it LOOKS like an atom and used
    to read back as `Pat('', '', '')` — a rule that silently matches nothing."""
    g = AttrGraph()
    R = _rule_node(g, "r.nonrel")
    mid = g.add_node("mid", control=True)
    g.add_relation(g.add_node("a", control=True), "x", mid, control=True)
    g.add_relation(mid, "y", g.add_node("b", control=True), control=True)
    g.add_relation(R, "lhs", mid, control=True)

    with pytest.raises(ValueError) as e:
        h.rules_in_graph(g)
    assert "r.nonrel" in str(e.value)


def test_ambiguous_endpoint_is_loud_not_arbitrary():
    """Two objects off one predicate node: reading it kept whichever came first, so the rule's
    meaning depended on edge insertion order. Must be refused, not silently disambiguated."""
    g = AttrGraph()
    R = _rule_node(g, "r.ambig")
    s = g.add_node("?x", control=True)
    p = g.add_relation(s, "likes", g.add_node("a", control=True), control=True)
    g.add_relation(p, "likes", g.add_node("b", control=True), control=True)   # second object
    g.add_relation(R, "lhs", p, control=True)

    with pytest.raises(ValueError) as e:
        h.rules_in_graph(g)
    msg = str(e.value)
    assert "r.ambig" in msg
    assert "objects" in msg


def test_every_defect_is_reported_not_just_the_first():
    """A learner emits many fragments at once, so one raise must describe ALL of them —
    otherwise fixing a learner becomes a raise-fix-raise loop."""
    g = AttrGraph()
    for name in ("bad.one", "bad.two"):
        R = _rule_node(g, name)
        g.add_relation(R, "lhs", g.add_node("atom", control=True), control=True)

    with pytest.raises(ValueError) as e:
        h.rules_in_graph(g)
    msg = str(e.value)
    assert "bad.one" in msg and "bad.two" in msg


# ---------------------------------------------------------------------------
# ...and the well-formed case is untouched
# ---------------------------------------------------------------------------

def test_well_formed_fragment_still_round_trips():
    g = AttrGraph()
    rule = Rule(key="ok", lhs=[Pat("?x", "is_a", "bird")], rhs=[Pat("?x", "flies", "yes")])
    h.write_rule(g, rule)

    read = h.rules_in_graph(g)
    assert len(read) == 1
    assert [p.tokens() for p in read[0].lhs] == [("?x", "is_a", "bird")]
    assert [p.tokens() for p in read[0].rhs] == [("?x", "flies", "yes")]


def test_folded_one_graph_with_facts_is_not_a_false_positive():
    """The one-graph fold puts facts and rule fragments in ONE graph. Ordinary facts must not
    trip the new validation — only actual role edges are inspected."""
    g = AttrGraph()
    bird = g.add_node("bird")
    for who in ("tweety", "polly"):
        g.add_relation(g.add_node(who), "is_a", bird)
    h.write_rule(g, Rule(key="ok", lhs=[Pat("?x", "is_a", "bird")], rhs=[Pat("?x", "flies", "yes")]))

    assert [r.key for r in h.rules_in_graph(g)] == ["ok"]

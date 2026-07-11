"""
Machine rule CNL — the uniform triple-grammar (harneskills/machine_rules.py) that lets
control/machinery rules be AUTHORED in CNL instead of Python literals. These tests lock the
five grammar gaps it closes (generic binary relations, multi-triple heads, drop, generic
NAC, control keyword tokens) and prove the walker bank (corpus/walker.cnl) reflects to
exactly the Python walker rules — so nothing is hardcoded in Python any more.
"""
import ugm as h
from ugm.cnl.machine_rules import load_machine_rules


def _shape(rule):
    """A key-independent signature: the (deduplicated, ordered) pattern token-tuples of each
    role. Two rules with the same shape match identically (the rule key is just a label).
    Tuples of strings — totally orderable, so `_shapes` can sort reliably."""
    role = lambda pats: tuple(sorted(set(p.tokens() for p in pats)))
    return (role(rule.lhs), role(rule.rhs), role(rule.nac), role(rule.drop))


def _shapes(rules):
    return sorted(map(_shape, rules))


# ---------------------------------------------------------------------------
# Conversion fidelity — the CNL bank == the Python walker rules
# ---------------------------------------------------------------------------

def test_walker_cnl_reflects_to_the_python_walker_rules():
    cnl = h.load_walker_rules()                                   # from corpus/walker.cnl
    python = h.DEMAND_WALK + h.SPAWN_RULES + h.walk_rules("is_a")
    assert _shapes(cnl) == _shapes(python)                        # identical, modulo keys


def test_walker_cnl_drives_an_on_demand_walk():
    # End-to-end through the CNL rules: walk_on_demand uses corpus/walker.cnl for is_a.
    g = h.Graph()
    for a, b in [("a", "b"), ("b", "c"), ("c", "d")]:
        g.add_relation(g.add_node(a) if not g.nodes_named(a) else g.nodes_named(a)[0],
                       "is_a",
                       g.add_node(b) if not g.nodes_named(b) else g.nodes_named(b)[0])
    h.walk_on_demand(g, "a", "d")
    assert any(g.name(r) == "is_a" and g.nodes_named("d")[0] in g.out(r)
               for r in g.out(g.nodes_named("a")[0]))             # a is_a d materialized


# ---------------------------------------------------------------------------
# Grammar-gap coverage — each gap, on a minimal rule
# ---------------------------------------------------------------------------

def test_g1_generic_binary_relation_condition_and_head():
    # `wants` is NOT in the prose grammar's fixed menu; here ANY predicate works, in both
    # the head and the body, as a bare `S P O` triple.
    [r] = load_machine_rules("?x craves ?y when ?x near ?y")
    assert _shape(r) == ((("?x", "near", "?y"),), (("?x", "craves", "?y"),), (), ())


def test_g2_multi_triple_head():
    [r] = load_machine_rules("?p owns ?z and ?z held_by ?p when ?p makes ?z")
    assert frozenset(p.tokens() for p in r.rhs) == {("?p", "owns", "?z"), ("?z", "held_by", "?p")}
    assert len(r.rhs) == 2


def test_g3_drop_clause_is_a_control_deletion():
    [r] = load_machine_rules("?x done yes and drop ?x todo ?t when ?x todo ?t")
    assert [p.tokens() for p in r.drop] == [("?x", "todo", "?t")]
    assert ("?x", "done", "yes") in {p.tokens() for p in r.rhs}    # the create still folds


def test_g4_generic_nac_for_any_relation():
    [r] = load_machine_rules("?x lonely yes when ?x is_a person and not ?x knows ?y")
    assert [p.tokens() for p in r.nac] == [("?x", "knows", "?y")]
    assert ("?x", "is_a", "person") in {p.tokens() for p in r.lhs}


def test_g5_control_keyword_tokens_bind_across_the_rule():
    # `<box>?` (the `?` suffix) is a bound literal: every occurrence is the SAME node, so the
    # head and the two conditions all join on it. A plain `<box>` would bind nothing.
    [r] = load_machine_rules("<box>? full yes when <box>? holds ?i and not <box>? empty yes")
    assert ("<box>?", "full", "yes") in {p.tokens() for p in r.rhs}
    assert ("<box>?", "holds", "?i") in {p.tokens() for p in r.lhs}
    assert ("<box>?", "empty", "yes") in {p.tokens() for p in r.nac}


def test_conjunctive_nac_shares_a_variable():
    # Multiple `not` clauses fold into ONE conjunctive negated subgraph joined by `?w`
    # (block if some ?w has BOTH), as the demand rule needs — not two independent negations.
    [r] = load_machine_rules("?a go yes when ?a ready yes and not ?w blocks ?a and not ?w near ?a")
    assert {p.tokens() for p in r.nac} == {("?w", "blocks", "?a"), ("?w", "near", "?a")}


def test_prose_grammar_still_single_head_and_unaffected():
    # The legacy prose grammar (authoring.load_rules) is untouched by the multi-head fold.
    [r] = h.load_rules("?c served express when ?c wants ?f and ?f is in_stock")
    assert [p.tokens() for p in r.rhs] == [("?c", "served", "express")]


# ---------------------------------------------------------------------------
# Planning bank now lives in CNL — the no-Python-rule-literals end state
# ---------------------------------------------------------------------------





def test_planning_drop_only_rule_round_trips_through_cnl():
    # G6 — a rule with an empty create head and only a `drop` (the unblock shape) survives
    # the fold and reflects to exactly the Python form.
    [r] = load_machine_rules(
        "drop ?o blocked_by ?p when ?o blocked_by ?p and ?p reachable <yes>")
    assert r.rhs == []
    assert [p.tokens() for p in r.drop] == [("?o", "blocked_by", "?p")]
    assert {p.tokens() for p in r.lhs} == {("?o", "blocked_by", "?p"),
                                           ("?p", "reachable", "<yes>")}

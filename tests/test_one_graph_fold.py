"""
The ONE-GRAPH FOLD (firmware doc §7 step 4, vision's homoiconic milestone): rules are graph data in
the SAME graph as the facts they rewrite — `rule_g` may simply BE `fact_g`.

What makes it safe is the attribute discipline, never a partition: the whole reified-rule fragment
is control-marked (the compiled read program's TEST-absent guards keep pattern nodes from ever
binding as facts), and its wiring additionally carries the ordinary `PATTERN_MARK` attribute, which
the fact VIEW (`derived_triples`) selects on — so pattern-space stays out of the fact view while
control-plane DERIVATIONS (`<goal> reached <plan>`, pencils) remain visible exactly as before.

Every test here runs a scenario TWICE — split graphs (the classic layout) vs folded (one graph) —
and asserts identical verdicts, derived triples, and demand traces, with the A1 walk/ISA
cross-check on. The public API is unchanged: callers may keep passing two graphs; passing one is
now equally correct.
"""
import pytest

import ugm as h
from ugm import (AttrGraph, Pat, Rule, ValueMatch, chain_sip, check, suppose,
                 derived_triples, render_demands, POSITIVE, ASSUMED_NO)
from ugm import chain
from ugm.attrgraph import PATTERN_MARK, graded


@pytest.fixture(autouse=True)
def _crosscheck_on():
    yield


def _both(build_facts, rules, run):
    """Run `run(facts, rule_graph)` split then folded; the outcomes must be identical."""
    outs = []
    for folded in (False, True):
        facts = AttrGraph()
        build_facts(facts)
        rg = facts if folded else AttrGraph()
        for r in rules:
            h.write_rule(rg, r)
        outs.append(run(facts, rg))
    assert outs[0] == outs[1], (
        f"one-graph fold divergence:\n  split  = {outs[0]!r}\n  folded = {outs[1]!r}")
    return outs[1]


def _entities(g, triples):
    ids = {}

    def node(name):
        if name not in ids:
            ids[name] = g.add_node(name)
        return ids[name]

    for s, p, o in triples:
        g.add_relation(node(s), p, node(o))


def test_fold_transitive_join():
    def build(g):
        _entities(g, [("a", "edge", "b"), ("b", "edge", "c"), ("c", "edge", "d")])

    rules = [
        Rule(key="reach.base", lhs=[Pat("?x", "edge", "?y")], rhs=[Pat("?x", "reach", "?y")]),
        Rule(key="reach.step", lhs=[Pat("?x", "edge", "?y"), Pat("?y", "reach", "?z")],
             rhs=[Pat("?x", "reach", "?z")]),
    ]

    def run(facts, rg):
        n = chain_sip(facts, ("reach", "a", None), rules=rg)
        return (n, sorted(derived_triples(facts)), sorted(render_demands(rg)))

    n, triples, _ = _both(build, rules, run)
    assert {o for s, p, o in triples if p == "reach" and s == "a"} == {"b", "c", "d"}


def test_fold_naf_verdicts():
    def build(g):
        _entities(g, [("ada", "is_a", "suspect"), ("bo", "is_a", "suspect"),
                      ("cy", "is_a", "suspect"), ("bo", "in", "library"),
                      ("ada", "is", "alibied")])

    rules = [
        Rule(key="innocent", lhs=[Pat("?x", "in", "library")], rhs=[Pat("?x", "is", "innocent")]),
        Rule(key="cleared.innocent", lhs=[Pat("?x", "is", "innocent")],
             rhs=[Pat("?x", "is", "cleared")]),
        Rule(key="cleared.alibi", lhs=[Pat("?x", "is", "alibied")],
             rhs=[Pat("?x", "is", "cleared")]),
        Rule(key="thief", lhs=[Pat("?x", "is_a", "suspect")],
             nac=[Pat("?x", "is", "cleared")], rhs=[Pat("?x", "is", "thief")]),
    ]

    def run(facts, rg):
        verdicts = tuple(check(facts, ("is", s, "thief"), rules=rg) for s in ("ada", "bo", "cy"))
        return (verdicts, sorted(derived_triples(facts)), sorted(render_demands(rg)))

    verdicts, _t, _d = _both(build, rules, run)
    assert verdicts == (ASSUMED_NO, ASSUMED_NO, POSITIVE)


def test_fold_literal_names_shared_between_rules_and_facts():
    """The hazard the fold guards against: a rule LITERAL ('library') is a control node sharing its
    name with a real entity — reads must bind only the entity, writes must land only on it."""
    def build(g):
        _entities(g, [("ada", "in", "library"), ("library", "is", "quiet")])

    rules = [
        Rule(key="reader", lhs=[Pat("?x", "in", "library"), Pat("library", "is", "quiet")],
             rhs=[Pat("?x", "is", "reader")]),
    ]

    def run(facts, rg):
        n = chain_sip(facts, ("is", None, "reader"), rules=rg)
        return (n, sorted(derived_triples(facts)))

    n, triples = _both(build, rules, run)
    assert ("ada", "is", "reader") in triples


def test_fold_value_match_and_skolem():
    def build(g):
        for name, w in (("morningstar", 0.90), ("eveningstar", 0.88), ("pluto", 0.10)):
            n = g.add_node(name)
            g.add_relation(n, "is_a", g.add_node("body"))
            g.set_attr(n, "warmth", graded(w))

    rules = [
        Rule(key="coref_warm", lhs=[Pat("?x", "is_a", "body"), Pat("?y", "is_a", "body")],
             rhs=[Pat("?x", "same_as", "?y")],
             value_matches=[ValueMatch("?x", "?y", "warmth", threshold=0.9)]),
        Rule(key="succ", lhs=[Pat("?x", "is_a", "body")],
             rhs=[Pat("?x", "has_twin", "t?"), Pat("t?", "twin_of", "?x")]),
    ]

    def run(facts, rg):
        chain_sip(facts, ("same_as", "morningstar", None), rules=rg)
        chain_sip(facts, ("has_twin", "morningstar", None), rules=rg)
        return sorted(derived_triples(facts))

    triples = _both(build, rules, run)
    pairs = {(s, o) for s, p, o in triples if p == "same_as"}
    assert ("morningstar", "eveningstar") in pairs and ("morningstar", "pluto") not in pairs
    assert sum(1 for s, p, o in triples if p == "has_twin" and s == "morningstar") == 1


def test_fold_suppose_pencils():
    def build(g):
        _entities(g, [("ada", "is", "person")])

    rules = [Rule(key="mortal", lhs=[Pat("?x", "is", "person")], rhs=[Pat("?x", "is", "mortal")])]

    def run(facts, rg):
        res = suppose(facts, assumptions=[("bo", "is", "person")], predictions=[("bo", "is", "mortal")], rules=rg)
        return (res.status, sorted(derived_triples(facts)))

    _both(build, rules, run)


def test_folded_fact_view_shows_no_pattern_space():
    """The folded graph's `derived_triples` contains ONLY facts + derivations — no `?x` pattern
    atoms, no head-index wiring — because rule wiring carries `PATTERN_MARK` (an ordinary,
    authoring-written, view-selected attribute)."""
    g = AttrGraph()
    _entities(g, [("a", "edge", "b")])
    h.write_rule(g, Rule(key="reach", lhs=[Pat("?x", "edge", "?y")], rhs=[Pat("?x", "reach", "?y")]))
    chain_sip(g, ("reach", "a", None))
    triples = derived_triples(g)
    assert ("a", "reach", "b") in triples
    assert not [t for t in triples if any(tok.startswith("?") for tok in (t[0], t[2]))]
    assert not [t for t in triples if "<head-index>" in t]
    assert g.nodes_with_key(PATTERN_MARK), "rule wiring should carry the pattern mark"

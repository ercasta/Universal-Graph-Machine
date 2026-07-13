"""Stage 1 of coreference-as-rules (docs/coreference_as_rules_design.md) — the value-match primitive.

A `ValueMatch` is the substrate's first DECLARED value-JOIN: a match-time condition comparing an
ATTRIBUTE VALUE across two LHS-bound variables (the path language otherwise joins only on shared
topology, which is why coref was a §8 tool). It mirrors the graded α-cut: reified by `write_rule`,
read + checked in the demand chain (`chain._read_value_matches`/`_value_matches_ok`).

  * EXACT (threshold None): the two bound nodes carry EQUAL VALUED values on `dim` (e.g. `name`, `dept`).
  * GRADED ('close enough'): both carry a GRADED degree on `dim` within the threshold.

This validates the coref-as-rules DIRECTION on today's (name-keyed) core, for the cases it supports:
graded closeness and equality across DIFFERENT names. Exact same-NAME coref needs the id-addressed core
(Stage 3) — the name-keyed env collapses two same-named nodes to one binding.
"""
import pytest

from ugm import (AttrGraph, Pat, Rule, ValueMatch, write_rule, chain_sip, derived_triples,
                 run_bank, Unlowerable, load_rules, load_corpus, same_as_rules, ask_goal)
from ugm.attrgraph import valued, graded
from ugm.chain import _read_value_matches


def _people(g, **depts):
    """Add each name as a person carrying a VALUED `dept`; return their node ids."""
    ids = {}
    for name, dept in depts.items():
        n = g.add_node(name)
        g.add_relation(n, "is_a", g.add_node("person"))
        g.set_attr(n, "dept", valued(dept))
        ids[name] = n
    return ids


def _pairs(g, pred):
    return sorted((s, o) for s, p, o in derived_triples(g) if p == pred)


# --- EXACT value-equality --------------------------------------------------------------------------

def test_exact_value_match_joins_only_equal_values():
    g = AttrGraph()
    _people(g, alice="eng", bob="eng", carol="sales")
    rule = Rule(key="coworker",
                lhs=[Pat("?x", "is_a", "person"), Pat("?y", "is_a", "person")],
                rhs=[Pat("?x", "coworker", "?y")],
                value_matches=[ValueMatch("?x", "?y", "dept")])
    rg = AttrGraph(); write_rule(rg, rule)
    chain_sip(g, rg, ("coworker", "alice", None))
    pairs = _pairs(g, "coworker")
    assert ("alice", "bob") in pairs        # same dept -> joined
    assert ("alice", "carol") not in pairs  # different dept -> NOT joined
    # reflexive self-pair is inherent to symmetric value-equality on the name-keyed core (a distinctness
    # constraint awaits the id-core, Stage 3); it is harmless for the coref `same_as` use.
    assert ("alice", "alice") in pairs


def test_exact_value_match_missing_attr_does_not_fire():
    g = AttrGraph()
    ids = _people(g, alice="eng", bob="eng")
    dave = g.add_node("dave")                       # a person with NO dept attr
    g.add_relation(dave, "is_a", g.add_node("person"))
    rule = Rule(key="coworker",
                lhs=[Pat("?x", "is_a", "person"), Pat("?y", "is_a", "person")],
                rhs=[Pat("?x", "coworker", "?y")],
                value_matches=[ValueMatch("?x", "?y", "dept")])
    rg = AttrGraph(); write_rule(rg, rule)
    chain_sip(g, rg, ("coworker", "dave", None))
    # dave has no `dept` -> the value-match is unevaluable on his side -> he joins NO ONE (not even self).
    assert not any(s == "dave" or o == "dave" for s, o in _pairs(g, "coworker"))


# --- GRADED 'close enough' -------------------------------------------------------------------------

def _bodies(g, **warmths):
    ids = {}
    for name, w in warmths.items():
        n = g.add_node(name); g.add_relation(n, "is_a", g.add_node("body"))
        g.set_attr(n, "warmth", graded(w)); ids[name] = n
    return ids


def test_graded_value_match_joins_close_and_excludes_far():
    g = AttrGraph()
    _bodies(g, morningstar=0.90, eveningstar=0.88, pluto=0.10)
    rule = Rule(key="coref_warm",
                lhs=[Pat("?x", "is_a", "body"), Pat("?y", "is_a", "body")],
                rhs=[Pat("?x", "same_as", "?y")],
                value_matches=[ValueMatch("?x", "?y", "warmth", threshold=0.9)])
    rg = AttrGraph(); write_rule(rg, rule)
    chain_sip(g, rg, ("same_as", "morningstar", None))
    pairs = _pairs(g, "same_as")
    assert ("morningstar", "eveningstar") in pairs   # |.90-.88|=.02 -> 1-.02=.98 >= .9
    assert ("morningstar", "pluto") not in pairs      # |.90-.10|=.80 -> 1-.80=.20 <  .9


def test_graded_value_match_respects_the_threshold_boundary():
    g = AttrGraph()
    _bodies(g, a=0.80, b=0.60)                        # 1 - |.80-.60| = 0.80
    rule = Rule(key="coref", lhs=[Pat("?x", "is_a", "body"), Pat("?y", "is_a", "body")],
                rhs=[Pat("?x", "same_as", "?y")],
                value_matches=[ValueMatch("?x", "?y", "warmth", threshold=0.85)])
    rg = AttrGraph(); write_rule(rg, rule)
    chain_sip(g, rg, ("same_as", "a", None))
    assert ("a", "b") not in _pairs(g, "same_as")     # 0.80 < 0.85 -> excluded


# --- reification round-trip ------------------------------------------------------------------------

def test_write_rule_reifies_value_match_read_back():
    rule = Rule(key="r", lhs=[Pat("?x", "is_a", "t"), Pat("?y", "is_a", "t")],
                rhs=[Pat("?x", "same_as", "?y")],
                value_matches=[ValueMatch("?x", "?y", "name"),
                               ValueMatch("?x", "?y", "warmth", threshold=0.7)])
    rg = AttrGraph(); node = write_rule(rg, rule)
    vms = sorted(_read_value_matches(rg, node))
    assert ("?x", "?y", "name", None) in vms
    assert ("?x", "?y", "warmth", 0.7) in vms


# --- forward path fires the value-JOIN (Stage 4: the forward-APPLY residual now lands) -------------

def test_forward_lowering_fires_the_value_join():
    # the forward engine now LOWERS a value-match to the `VMATCH` op (was `Unlowerable`, Stage 1): two
    # distinct same-named nodes relate, a third-named one does not — the CONSTRAINED join, not a rush.
    g = AttrGraph()
    for nm in ("k", "k", "j"):
        n = g.add_node(nm); g.add_relation(n, "is_a", g.add_node("t"))
    rule = Rule(key="vm", lhs=[Pat("?x", "is_a", "t"), Pat("?y", "is_a", "t")],
                rhs=[Pat("?x", "same_as", "?y")],
                value_matches=[ValueMatch("?x", "?y", "name")])
    run_bank(g, [rule])
    pairs = _pairs(g, "same_as")
    assert ("k", "k") in pairs                        # the two 'k' mentions relate by equal name
    assert ("k", "j") not in pairs and ("j", "k") not in pairs   # different name -> no join


def test_forward_value_match_var_not_lhs_bound_is_unlowerable():
    # a value-match var absent from the LHS cannot be filtered (VMATCH needs a bound register) -> loud.
    rule = Rule(key="vm", lhs=[Pat("?x", "is_a", "t")],
                rhs=[Pat("?x", "same_as", "?y")],
                value_matches=[ValueMatch("?x", "?y", "name")])
    g = AttrGraph(); n = g.add_node("k"); g.add_relation(n, "is_a", g.add_node("t"))
    with pytest.raises(Unlowerable, match="not LHS-bound"):
        run_bank(g, [rule])


# --- Stage 2: the CNL authoring surface `?x same DIM as ?y` / `?x close DIM as ?y` -----------------

def test_cnl_same_value_form_folds_to_an_exact_value_match():
    [r] = load_rules("?x same_as ?y when ?x is a person and ?y is a person and ?x same name as ?y")
    assert sorted(p.tokens() for p in r.lhs) == [("?x", "is_a", "person"), ("?y", "is_a", "person")]
    assert [p.tokens() for p in r.rhs] == [("?x", "same_as", "?y")]
    assert r.value_matches == [ValueMatch("?x", "?y", "name", None)]     # exact -> no threshold


def test_cnl_close_value_form_folds_to_a_graded_value_match():
    [r] = load_rules("?x same_as ?y when ?x is a body and ?y is a body and ?x close bright as ?y")
    [vm] = r.value_matches
    assert (vm.var_a, vm.var_b, vm.dim) == ("?x", "?y", "bright")
    assert vm.threshold is not None                                     # graded -> a closeness threshold


# --- Stage 2: coreference as a DECLARED rule, end to end -------------------------------------------

_COREF_FACTS = """bright is gradable
very is 0.9
slightly is 0.1
morningstar is a body
eveningstar is a body
pluto is a body
morningstar is very bright
eveningstar is very bright
pluto is slightly bright
morningstar is visible"""

_COREF_RULE = "?x same_as ?y when ?x is a body and ?y is a body and ?x close bright as ?y"


def test_coref_as_a_declared_rule_composes_close_entities():
    # morningstar ≈ eveningstar by close `bright`; the coref rule derives `same_as`, and `same_as_rules`
    # carry morningstar's `visible` onto eveningstar. A DECLARED rule — no mechanical ingest merge.
    kb, _ = load_corpus(_COREF_FACTS)
    rules = load_rules(_COREF_RULE) + same_as_rules(["is", "same_as"])
    assert ask_goal(kb.copy(), "is eveningstar visible", rules) == ["yes"]
    assert ask_goal(kb.copy(), "is pluto visible", rules) == ["no"]     # too far -> no coref


def test_coref_gate_no_rule_no_composition():
    # the SAME facts, but WITHOUT the coref rule, do not compose — coref-following is DATA, not baked in.
    kb, _ = load_corpus(_COREF_FACTS)
    assert ask_goal(kb.copy(), "is eveningstar visible", same_as_rules(["is", "same_as"])) == ["no"]


def test_asserted_identity_composes_across_names_via_load_corpus():
    # `X is the same as Y` (form.fact.same_as) asserts CROSS-name identity — a `same_as` edge between two
    # DIFFERENT names (so interning, which is by-name, leaves them distinct). load_corpus composes facts
    # across that edge with an eager `same_as` propagation pass (control same_as is demand-invisible), so a
    # fact stated under one name answers under the other. Guards the regression where dropping the pass for
    # the same-name interning win silently broke asserted identity (no prior coverage of this form).
    kb, rules = load_corpus("morningstar is the same as eveningstar\nmorningstar is bright")
    assert ask_goal(kb.copy(), "is eveningstar bright", rules) == ["yes"]     # composed across identity
    assert ask_goal(kb.copy(), "is morningstar bright", rules) == ["yes"]     # and the stated name

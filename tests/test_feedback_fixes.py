"""Regression tests for the pystrider consumer feedback (docs/feedback_from_pystrider.md).

Theme: silent failures made LOUD. A non-triple machine-rule clause (#1), a skolem RHS-only head var
(#2), a case-folded query that silently misses (#3), a `Rule` object where a node-id is expected (#4),
and an unrecognized fact line (#5) now signal instead of quietly doing less. Plus a session ergonomics
gap: `suppose` now accepts `focus_scope` like `ask_goal` (#7).
"""
import inspect
import warnings

import pytest

import ugm as h
from ugm import (load_machine_rules, write_rule, AttrGraph, apply_rule, apply_to_fixpoint,
                 rules_in_graph, load_facts, ask_goal, suppose)


# --- #1: machine-rule CNL raises on a clause that isn't a full S P O triple --------------------------

def test_machine_rule_absorbed_separator_raises():
    # `?e reached` is 2 tokens -> would swallow `when` as its object; must raise, not mangle.
    with pytest.raises(ValueError, match="triple"):
        load_machine_rules("?e reached when ?e is_a attribute")


def test_machine_rule_dropped_short_body_clause_raises():
    # the 2-token guard `?g guard_open` would silently vanish from the LHS, firing unconditionally.
    with pytest.raises(ValueError, match="guard_open"):
        load_machine_rules("?e reached yes when ?e within_guard ?g and ?g guard_open")


def test_machine_rule_valid_shapes_still_parse():
    for good in ("?e reached yes when ?e is_a attribute",
                 "?p made child when ?p is_a parent",
                 "?p succ ?p2 when ?p is_a state and ?p next ?p2",       # head var BOUND in the body: ok
                 "drop ?m mark done when ?m is_a task and ?m closed yes",
                 "?x safe yes when ?x clear yes and not ?x flagged yes"):
        assert len(load_machine_rules(good)) == 1


# --- #2: existential / skolem RHS-only head vars are rejected LOUDLY (was: silent garbage mint) ------

def test_rhs_only_head_var_rejected():
    # `?s2` is a head var absent from the body — forward mints a fresh unnamed node per firing; reject it.
    with pytest.raises(ValueError, match="RHS-only head variable"):
        load_machine_rules("?p succ ?s2 when ?p is_a state")
    # the prose surface rejects it too, and only AFTER the more specific malformed-clause check runs
    with pytest.raises(ValueError, match="RHS-only head variable"):
        h.load_rules("?x knows ?y when ?x is a person")            # ?y is RHS-only


def test_nac_only_body_binds_head_var_not_flagged():
    # a rule whose only body clause is a NAC still BINDS the head var (via the NAC) — must NOT be rejected.
    assert h.load_rules("?x is q when ?x is not p")                # ?x bound by the NAC, valid


# --- #4: apply_* give a clear error for a Rule object instead of a cryptic TypeError -----------------

def test_apply_with_rule_object_gives_clear_error():
    rule = load_machine_rules("?p made child when ?p is_a parent")[0]
    rg = AttrGraph(); write_rule(rg, rule)
    got_rule_obj = rules_in_graph(rg)[0]                                # a Rule, NOT a node id
    g = h.Graph()
    for fn in (apply_rule, apply_to_fixpoint):
        with pytest.raises(TypeError, match="rule-NODE id"):
            fn(g, rg, got_rule_obj)


def test_apply_with_node_id_still_works():
    rule = load_machine_rules("?p made child when ?p is_a parent")[0]
    rg = AttrGraph(); node = write_rule(rg, rule)                       # the id you actually feed apply_*
    g = h.Graph(); p = g.add_node("p"); g.add_relation(p, "is_a", g.add_node("parent"))
    assert apply_to_fixpoint(g, rg, node) == 1


# --- #5: load_facts(strict=True) surfaces silently-dropped lines -------------------------------------

def test_load_facts_strict_raises_on_unrecognized_line():
    g = h.Graph()
    with pytest.raises(ValueError, match="assigns"):
        load_facts(g, "ada is a suspect\nstmt0 assigns y\nbo in library", strict=True)


def test_load_facts_lenient_default_unchanged():
    g = h.Graph()
    anchors = load_facts(g, "stmt0 assigns y")                          # no raise, stays raw
    assert anchors and not any(t[1] == "assigns" for t in h.derived_triples(g))


def test_load_facts_strict_passes_when_all_recognized():
    g = h.Graph()
    load_facts(g, "ada is a suspect\nbo in library", strict=True)       # no raise
    assert h.ask_goal(g, "is ada a suspect", []) == ["yes"]


# --- #3: a case-folded CNL query that would silently miss a case-variant node now WARNS ---------------

def test_case_folded_query_warns_on_variant_node():
    g = h.Graph(); e = g.add_node("eB"); g.add_relation(e, "is_a", g.add_node("attribute"))
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        assert ask_goal(g, "is eB a attribute", []) == ["no"]          # still the folded miss...
    assert any("case-variant" in str(rec.message) for rec in w)        # ...but no longer SILENT


def test_case_folded_query_quiet_when_no_variant():
    g = h.Graph(); load_facts(g, "ada is a suspect")                    # all lower-case, exact match
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        assert ask_goal(g, "is ada a suspect", []) == ["yes"]
        ask_goal(g, "is zzz a suspect", [])                            # genuinely absent, not a case issue
    assert not w                                                        # no noise on the normal paths


# --- #7: suppose accepts focus_scope (bounded attention on the outcome path), like ask_goal ----------

def test_suppose_accepts_focus_scope():
    assert "focus_scope" in inspect.signature(suppose).parameters
    kb, rules = h.load_corpus("?x is wet when ?x is rained_on")
    rg = AttrGraph()
    for r in rules:
        write_rule(rg, r)
    # in-scope entity -> the hypothesis reasons within the working set and still confirms
    res = suppose(kb, rg, [("ada", "is", "rained_on")], [("is", "ada", "wet")],
                  focus_scope=frozenset({"ada"}))
    assert res.status == "confirmed"

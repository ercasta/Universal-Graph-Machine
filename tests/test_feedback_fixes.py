"""Regression tests for the pystrider consumer feedback (docs/feedback_from_pystrider.md).

Theme: silent failures made LOUD. A non-triple machine-rule clause (#1), a `Rule` object where a
node-id is expected (#4), and an unrecognized fact line (#5) now signal instead of quietly doing less.
"""
import pytest

import ugm as h
from ugm import (load_machine_rules, write_rule, AttrGraph, apply_rule, apply_to_fixpoint,
                 rules_in_graph, load_facts)


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
                 "?p succ ?s2 when ?p is_a state",                       # RHS-only var (see #2)
                 "drop ?m mark done when ?m is_a task and ?m closed yes",
                 "?x safe yes when ?x clear yes and not ?x flagged yes"):
        assert len(load_machine_rules(good)) == 1


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

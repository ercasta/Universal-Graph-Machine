"""Scope generalization Slice 2, PART (a): the `temporal` ordered ontological scope KIND.

The second ontological kind — like `holder` (non-veridical globally, ontological for its context) but
its contexts are ORDERED. Part (a) delivers the scope + keying + relativized read + the ordering as
ordinary relational content. Part (b) (scope-variable rules, ranging a BINARY fact across indices) is
separate; here the ranging that already works NATIVELY is the unary-state 3-place frame axiom (O2a).
"""
from ugm import assemble_facts
from ugm.attrgraph import AttrGraph
from ugm.cnl.machine_rules import load_machine_rules
from ugm.cnl.rule_graph import write_rule
from ugm.check import check, collapse, POSITIVE, ASSUMED_NO
from ugm.machine import Machine
from ugm.policy import FirmwarePolicy
from ugm.suppose import SCOPE_KIND, KIND_TEMPORAL, INDEX, scope_kind
from ugm.scope_kinds import temporal_scope_of, at_time, holds_at, order, indices_holding

BANDED = FirmwarePolicy(uncertainty="banded")


def _rule_kb(text: str, facts=()) -> AttrGraph:
    g = AttrGraph()
    if facts:
        Machine().run(g, assemble_facts([tuple(f.split()) for f in facts]))
    for rule in load_machine_rules(text):
        write_rule(g, rule)
    return g


# --- ONTOLOGICAL / NON-VERIDICAL — same shape as holder, at an index -------------------------------

def test_timed_fact_is_ontological_at_its_index_non_veridical_globally():
    g = AttrGraph()
    at_time(g, "t1", ("lion", "has", "mane"))
    assert holds_at(g, "t1", ("has", "lion", "mane")) == POSITIVE     # definite at t1
    assert check(g, ("has", "lion", "mane")) == ASSUMED_NO            # not the timeless world's
    assert check(g, ("has", "lion", "mane"), policy=BANDED) == ASSUMED_NO   # no band ⇒ no global leak


def test_indices_are_independent():
    g = AttrGraph()
    at_time(g, "t1", ("lion", "has", "mane"))
    assert holds_at(g, "t1", ("has", "lion", "mane")) == POSITIVE
    assert holds_at(g, "t2", ("has", "lion", "mane")) == ASSUMED_NO   # not carried without a frame axiom


def test_one_scope_per_index_reused_and_accretes():
    g = AttrGraph()
    s1 = at_time(g, "t1", ("lion", "has", "mane"))
    s2 = at_time(g, "t1", ("lion", "is", "asleep"))
    assert s1 == s2
    assert holds_at(g, "t1", ("has", "lion", "mane")) == POSITIVE
    assert holds_at(g, "t1", ("is", "lion", "asleep")) == POSITIVE


def test_scope_carries_the_temporal_kind_and_index():
    g = AttrGraph()
    at_time(g, "t1", ("lion", "has", "mane"))
    scope = temporal_scope_of(g, "t1")
    assert scope is not None
    assert scope_kind(g, scope) == KIND_TEMPORAL
    assert g.get_attr(scope, INDEX).value == "t1"


def test_holds_at_an_unknown_index_is_assumed_no():
    g = AttrGraph()
    at_time(g, "t1", ("lion", "has", "mane"))
    assert holds_at(g, "t99", ("has", "lion", "mane")) == ASSUMED_NO


def test_indices_holding_is_the_inverse():
    g = AttrGraph()
    at_time(g, "t1", ("lion", "has", "mane"))
    at_time(g, "t2", ("lion", "has", "mane"))
    at_time(g, "t2", ("lion", "is", "asleep"))
    assert sorted(indices_holding(g, ("lion", "has", "mane"))) == ["t1", "t2"]
    assert indices_holding(g, ("lion", "is", "asleep")) == ["t2"]
    assert indices_holding(g, ("lion", "has", "cub")) == []


# --- ORDERING is ordinary relational content (spike O1: NATIVE recursion) --------------------------

def test_order_is_ink_and_recursion_ranges_it():
    """The order lives among the INDICES as ordinary ink facts; a recursive rule traverses it — no
    scope machinery involved. This is the ranging capability tense reuses (spike O1)."""
    g = _rule_kb("?a precedes ?b when ?a before ?b\n"
                 "?a precedes ?c when ?a before ?b and ?b precedes ?c")
    order(g, "t0", "t1"); order(g, "t1", "t2"); order(g, "t2", "t3")
    assert check(g, ("precedes", "t0", "t3")) == POSITIVE
    assert check(g, ("before", "t0", "t1")) == POSITIVE               # `order` wrote ink


def test_unary_state_frame_axiom_ranges_natively_O2a():
    """The tense an agent can already express: a UNARY state folded into the predicate fits 3-place, so
    a cross-index frame axiom is an ordinary rule — no scope-variable needed. This bounds what part (b)
    must add (only the BINARY-fact case)."""
    g = _rule_kb("?x dangerous_at ?u when ?x hungry_at ?t and ?t before ?u",
                 facts=["lion hungry_at t1", "t1 before t2"])
    assert check(g, ("dangerous_at", "lion", "t2")) == POSITIVE


# --- ADDITIVITY -----------------------------------------------------------------------------------

def test_temporal_scopes_do_not_disturb_the_epistemic_default():
    from ugm.possibility import add_fork, band_word
    g = AttrGraph()
    add_fork(g, 0.5, [("lion", "is_a", "predator")])
    at_time(g, "t1", ("lion", "has", "mane"))
    assert check(g, ("is_a", "lion", "predator"), policy=BANDED) == band_word(0.5)  # fork still banded
    assert holds_at(g, "t1", ("has", "lion", "mane"), policy=BANDED) == POSITIVE     # timed still certain

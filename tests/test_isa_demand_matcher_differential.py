"""
Phase A / A1 (docs/attic/phase_a_demand_firmware.md) — DIFFERENTIAL gate for the demand matcher on the
shared ISA matcher.

The demand path's single-atom fact lookup (`chain._facts_matching`) is being unified onto the ONE
ISA matcher (`Machine.match`), retiring the bespoke topology walk (`_facts_matching_walk`). This
increment is ADDITIVE — the walk stays the reference oracle; `chain._facts_matching_isa` does the
same lookup through the ISA matcher, and with `chain._CROSSCHECK` set, EVERY `_facts_matching` call
asserts the two agree (order-insensitive). Here we turn the gate ON and drive the real demand
procedures (`check`/`chain_sip`/`suppose`) plus targeted direct calls, so every internal lookup shape
is cross-checked: bound-subj/wildcard-obj, bound-obj/wildcard-subj, both-bound, whole-predicate scan,
nested-negative NAF, coref `same_as` fan-out, SUPPOSE scope pencils, focus attention, and `ById`.

A divergence raises `AssertionError` from inside `chain._facts_matching` (the gate), naming the tuple.
"""
import pytest

import ugm as h
from ugm import AttrGraph, Pat, Rule, chain_sip, check, suppose
from ugm import chain
from ugm.chain import ById, _facts_matching, _facts_matching_walk, _facts_matching_isa


@pytest.fixture(autouse=True)
def _crosscheck_on():
    """Turn the A1 differential gate on for every test here; restore after (it defaults OFF so the
    shipped suite runs the oracle path unperturbed)."""
    prev = chain._CROSSCHECK
    chain._CROSSCHECK = True
    try:
        yield
    finally:
        chain._CROSSCHECK = prev


def _facts(triples) -> AttrGraph:
    g = AttrGraph()
    ids: dict[str, str] = {}

    def node(name: str) -> str:
        if name not in ids:
            ids[name] = g.add_node(name)
        return ids[name]

    for s, p, o in triples:
        g.add_relation(node(s), p, node(o))
    return g


def _reify(rules) -> AttrGraph:
    rg = AttrGraph()
    for r in rules:
        h.write_rule(rg, r)
    return rg


# --- The direct-parity backstop: the gate is only as strong as its inputs, so pin the equality of
#     the two implementations explicitly on every branch + filter, independent of the procedures ----

def _assert_parity(g, pred, subj, obj, *, scope=None, focus_scope=None):
    walk = _facts_matching_walk(g, pred, subj, obj, scope=scope, focus_scope=focus_scope)
    isa = _facts_matching_isa(g, pred, subj, obj, scope=scope, focus_scope=focus_scope)
    from collections import Counter
    assert Counter(walk) == Counter(isa), f"({pred},{subj},{obj}) walk={walk} isa={isa}"
    return walk


def test_direct_bound_subject_and_wildcard_object():
    g = _facts([("ada", "knows", "bo"), ("ada", "knows", "cy"), ("bo", "knows", "cy")])
    # (pred, subj, ?) — walk OUT of ada: two objects, each a free slot -> ById
    out = _assert_parity(g, "knows", "ada", None)
    assert {e[0] for e in out} == {"ada"} and all(isinstance(e[1], ById) for e in out)
    assert len(out) == 2
    # (pred, ?, obj) — walk INTO cy
    _assert_parity(g, "knows", None, "cy")
    # both bound
    _assert_parity(g, "knows", "ada", "bo")
    # both wildcard — the whole-predicate scan
    _assert_parity(g, "knows", None, None)
    # a predicate with no facts, and an entity with no such relation
    _assert_parity(g, "loves", "ada", None)
    _assert_parity(g, "knows", "nobody", None)


def test_direct_skips_control_and_inert_endpoints():
    g = AttrGraph()
    ada = g.add_node("ada")
    bo = g.add_node("bo")
    ctrl = g.add_node("ada", control=True)     # a same-NAMED control scaffolding node
    inert = g.add_node("bo", inert=True)       # a same-NAMED inert (provenance-like) node
    g.add_relation(ada, "knows", bo)
    g.add_relation(ctrl, "knows", bo)          # control subject -> must be invisible
    g.add_relation(ada, "knows", inert)        # inert object -> must be invisible
    # candidate set for "ada"/"bo" includes the control/inert twins; both matchers must skip them
    out = _assert_parity(g, "knows", "ada", None)
    assert len(out) == 1                       # only ada->bo, not ada->inert nor ctrl->bo
    _assert_parity(g, "knows", None, "bo")
    _assert_parity(g, "knows", None, None)


def test_thief_naf_all_suspects_crosschecked():
    """Nested-negative demand closures (`_nac_blocks` -> `_facts_matching`) over every suspect —
    the wildcard-NAC + bound-goal shapes, cross-checked end to end."""
    facts = _facts([("ada", "is_a", "suspect"), ("bo", "is_a", "suspect"),
                    ("cy", "is_a", "suspect"), ("bo", "in", "library"),
                    ("ada", "is", "alibied")])
    rules = _reify([
        Rule(key="innocent", lhs=[Pat("?x", "in", "library")], rhs=[Pat("?x", "is", "innocent")]),
        Rule(key="cleared.innocent", lhs=[Pat("?x", "is", "innocent")], rhs=[Pat("?x", "is", "cleared")]),
        Rule(key="cleared.alibi", lhs=[Pat("?x", "is", "alibied")], rhs=[Pat("?x", "is", "cleared")]),
        Rule(key="thief", lhs=[Pat("?x", "is_a", "suspect")],
             nac=[Pat("?x", "is", "cleared")], rhs=[Pat("?x", "is", "thief")]),
    ])
    verdicts = {s: check(facts, ("is", s, "thief"), rules=rules) for s in ("ada", "bo", "cy")}
    # cy has no clearance -> thief; ada/bo cleared -> not
    from ugm import POSITIVE, ASSUMED_NO
    assert verdicts["cy"] == POSITIVE
    assert verdicts["ada"] == ASSUMED_NO and verdicts["bo"] == ASSUMED_NO
    # a wildcard-subject goal too (whole-predicate reads inside the closure)
    chain_sip(facts, ("is", None, "thief"), rules=rules)


def test_transitive_multi_atom_join_crosschecked():
    """A recursive/transitive rule: the SIP join threads a bound endpoint through successive body
    atoms, so each round exercises (pred, subj, ?) reads under partial envs."""
    facts = _facts([("a", "edge", "b"), ("b", "edge", "c"), ("c", "edge", "d")])
    rules = _reify([
        Rule(key="reach.base", lhs=[Pat("?x", "edge", "?y")], rhs=[Pat("?x", "reach", "?y")]),
        Rule(key="reach.step", lhs=[Pat("?x", "edge", "?y"), Pat("?y", "reach", "?z")],
             rhs=[Pat("?x", "reach", "?z")]),
    ])
    chain_sip(facts, ("reach", "a", None), rules=rules)
    from ugm import derived_triples
    reached = {o for (s, p, o) in derived_triples(facts) if p == "reach" and s == "a"}
    assert reached == {"b", "c", "d"}


def test_coref_same_as_fanout_crosschecked():
    """Coref `same_as` present in the fact graph: the demand reads fan out over same-named / linked
    mentions. Exercised via a propagation rule + a bound goal that must compose across the link."""
    facts = _facts([("morningstar", "same_as", "eveningstar"),
                    ("eveningstar", "same_as", "morningstar"),
                    ("morningstar", "is", "bright")])
    rules = _reify([
        # a property propagates across an asserted identity (a declared coref-style rule)
        Rule(key="prop", lhs=[Pat("?a", "same_as", "?b"), Pat("?a", "is", "?p")],
             rhs=[Pat("?b", "is", "?p")]),
    ])
    chain_sip(facts, ("is", "eveningstar", None), rules=rules)
    from ugm import derived_triples
    props = {o for (s, p, o) in derived_triples(facts) if p == "is" and s == "eveningstar"}
    assert "bright" in props


def test_focus_scope_bounds_reads_crosschecked():
    facts = _facts([("ada", "knows", "bo"), ("cy", "knows", "dee"), ("bo", "knows", "ada")])
    # in-focus and off-focus reads, both cross-checked (bound + wildcard, name-and-ById filters)
    _assert_parity(facts, "knows", "ada", None, focus_scope=frozenset({"ada", "bo"}))
    _assert_parity(facts, "knows", None, None, focus_scope=frozenset({"ada", "bo"}))
    _assert_parity(facts, "knows", None, "dee", focus_scope=frozenset({"ada", "bo"}))  # off-focus
    # and through the real solver
    rules = _reify([Rule(key="ack", lhs=[Pat("?x", "knows", "?y")], rhs=[Pat("?x", "ack", "?y")])])
    chain_sip(facts, ("ack", "ada", None), focus_scope=frozenset({"ada", "bo"}), rules=rules)


def test_suppose_scope_pencil_visibility_crosschecked():
    """SUPPOSE reasons over PENCIL (control rels tagged with the active scope). The in-scope reads go
    through `_facts_matching(scope=…)`, so `_rel_matches_pred`'s scope-pencil branch is cross-checked."""
    facts = _facts([("ada", "is", "person")])
    rules = _reify([
        Rule(key="mortal", lhs=[Pat("?x", "is", "person")], rhs=[Pat("?x", "is", "mortal")]),
    ])
    res = suppose(facts, assumptions=[("bo", "is", "person")], predictions=[("bo", "is", "mortal")], rules=rules)
    # bo assumed a person in pencil -> mortal derivable in-scope; the point here is the cross-check ran
    assert res.status in ("confirmed", "inconclusive", "refuted")


def test_byid_endpoints_crosschecked():
    """`ById` endpoints on distinct same-named nodes: the pin must reach exactly its node, and free
    slots come back as `ById`. Both matchers cross-checked on the id-addressed path."""
    g = AttrGraph()
    ada1 = g.add_node("ada")
    ada2 = g.add_node("ada")     # a genuinely distinct same-named entity
    bo = g.add_node("bo")
    g.add_relation(ada1, "knows", bo)
    # pin the subject to ada2 (no facts) vs ada1 (one fact) — the pin is honest, never a name fallthrough
    assert _assert_parity(g, "knows", ById(ada2), None) == []
    out = _assert_parity(g, "knows", ById(ada1), None)
    assert len(out) == 1 and out[0][0] == ById(ada1)
    _assert_parity(g, "knows", None, ById(bo))
    _assert_parity(g, "knows", ById(ada1), ById(bo))


def test_gate_actually_catches_a_divergence(monkeypatch):
    """Sanity: if the ISA path were wrong, the gate FIRES (so a green suite means real parity, not a
    dead assertion). Monkeypatch the ISA impl to drop a result and confirm `_facts_matching` raises."""
    g = _facts([("ada", "knows", "bo")])

    def _broken(fact_g, pred, subj, obj, *, scope=None, focus_scope=None):
        return []   # deliberately wrong

    monkeypatch.setattr(chain, "_facts_matching_isa", _broken)
    with pytest.raises(AssertionError, match="A1 demand-matcher divergence"):
        _facts_matching(g, "knows", "ada", None)

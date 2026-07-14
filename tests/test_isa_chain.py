"""
Phase 3.3 head index + the demand-driven solver `chain_sip` (bound-tuple SIP).

The head index is graph structure (`<head-index>` hub -[headPred]-> rule); `chain_sip` uses it to
demand-drive, closing the bound-tuple demand set and applying only the relevant rules. Differentially
gated against `run_bank` over the FULL bank: `chain_sip` derives exactly the goal-tuple facts the full
forward closure does, while pruning to demanded TUPLES (the magic set of visible `<demand>` nodes).

(The predicate-grain precursor `chain`/`demand_closure` was retired 2026-07-14 — see chain.py.)
"""
import ugm as h
from ugm import (
    AttrGraph, run_bank, derived_triples,
    build_head_index, rules_producing,
    chain_sip, bound_demands,
)


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


def _reify(rules) -> tuple[AttrGraph, dict]:
    rg = AttrGraph()
    nodes = {r.key: h.write_rule(rg, r) for r in rules}
    return rg, nodes


# --- Phase 3.3: the head index -------------------------------------------------------------------

MORTAL = h.Rule(key="mortal", lhs=[h.Pat("?x", "is_a", "person")], rhs=[h.Pat("?x", "is_a", "mortal")])
PERSON = h.Rule(key="person", lhs=[h.Pat("?x", "is_a", "philosopher")], rhs=[h.Pat("?x", "is_a", "person")])
LIKES = h.Rule(key="likes", lhs=[h.Pat("?x", "follows", "?y")], rhs=[h.Pat("?x", "likes", "?y")])


def test_head_index_maps_predicate_to_producing_rules():
    rg, nodes = _reify([MORTAL, PERSON, LIKES])
    build_head_index(rg)
    assert set(rules_producing(rg, "is_a")) == {nodes["mortal"], nodes["person"]}
    assert rules_producing(rg, "likes") == [nodes["likes"]]
    assert rules_producing(rg, "nonesuch") == []


def test_head_index_build_is_idempotent():
    rg, nodes = _reify([MORTAL, PERSON])
    build_head_index(rg)
    build_head_index(rg)                                   # second build adds nothing
    assert sorted(rules_producing(rg, "is_a")) == sorted([nodes["mortal"], nodes["person"]])


# --- Phase 4.1: BOUND-TUPLE SIP (chain_sip) ------------------------------------------------------

def _sip_vs_run_bank(rules, facts, goal):
    """Run `rules` over `facts` two ways: run_bank (full closure, oracle) and chain_sip (bound-tuple
    demand for `goal`). Return (oracle_derived, sip_derived) as (s, pred, o) triple sets."""
    g1 = _facts(facts); base1 = derived_triples(g1); run_bank(g1, rules)
    oracle = derived_triples(g1) - base1
    g2 = _facts(facts); base2 = derived_triples(g2)
    rg, _ = _reify(rules)
    chain_sip(g2, goal, rules=rg)
    got = derived_triples(g2) - base2
    return oracle, got, rg


def _matches(triples, pred, subj, obj):
    return {t for t in triples
            if t[1] == pred and (subj is None or t[0] == subj) and (obj is None or t[2] == obj)}


def test_chain_sip_is_complete_for_the_goal_tuple_and_prunes_by_subject():
    # TWO philosophers; the goal is about socrates only. Predicate-grain CHAIN would derive plato's
    # is_a facts too; bound-tuple SIP derives ONLY socrates's — the subject-pruning win.
    facts = [("socrates", "is_a", "philosopher"), ("plato", "is_a", "philosopher"),
             ("alice", "follows", "bob")]
    goal = ("is_a", "socrates", None)
    oracle, got, _rg = _sip_vs_run_bank([MORTAL, PERSON, LIKES], facts, goal)

    # complete for the goal tuple: every is_a fact ABOUT socrates the full closure derives, SIP derives
    assert _matches(got, "is_a", "socrates", None) == _matches(oracle, "is_a", "socrates", None)
    assert ("socrates", "is_a", "person") in got and ("socrates", "is_a", "mortal") in got
    # pruned: plato is never demanded, so his is_a facts are NOT derived (the full closure HAS them)
    assert ("plato", "is_a", "mortal") in oracle
    assert _matches(got, "is_a", "plato", None) == set()
    # and the irrelevant `likes` rule never runs (predicate-level pruning still holds)
    assert _matches(got, "likes", None, None) == set()


def test_chain_sip_demands_are_bound_tuples_visible_as_nodes():
    facts = [("socrates", "is_a", "philosopher")]
    _oracle, _got, rg = _sip_vs_run_bank([MORTAL, PERSON], facts, ("is_a", "socrates", None))
    demands = bound_demands(rg)
    # the magic set is bound to socrates: the goal + the SIP-passed sub-demands, all about socrates
    assert ("is_a", "socrates", None) in demands
    assert ("is_a", "socrates", "person") in demands       # MORTAL's body, subject passed sideways
    assert ("is_a", "socrates", "philosopher") in demands  # PERSON's body
    # never a demand about a different subject (SIP kept it socrates-scoped)
    assert all(s in (None, "socrates") for (_p, s, _o) in demands)


def test_chain_sip_transitive_goal_with_bound_start_matches_run_bank_on_the_goal():
    rule = h.Rule(key="is_a.transitive",
                  lhs=[h.Pat("?a", "is_a", "?b"), h.Pat("?b", "is_a", "?c")],
                  rhs=[h.Pat("?a", "is_a", "?c")])
    # two independent chains; the goal asks only about alice's chain
    facts = [("alice", "is_a", "oc"), ("oc", "is_a", "customer"), ("customer", "is_a", "party"),
             ("zeb", "is_a", "gamma"), ("gamma", "is_a", "delta")]
    oracle, got, _rg = _sip_vs_run_bank([rule], facts, ("is_a", "alice", None))
    # complete on alice's transitive closure
    assert _matches(got, "is_a", "alice", None) == _matches(oracle, "is_a", "alice", None)
    assert ("alice", "is_a", "party") in got
    # zeb's chain is off-goal — SIP never demands it (the full closure derives zeb -> delta)
    assert ("zeb", "is_a", "delta") in oracle
    assert _matches(got, "is_a", "zeb", None) == set()

"""
Phase 3.3 head index + Phase 4.3 CHAIN firmware v0 (`harneskills/isa/{apply,chain}.py`).

The head index is graph structure (`<head-index>` hub -[headPred]-> rule). CHAIN uses it to
demand-drive: close the demand set backward from a goal predicate, then APPLY only the relevant
rules. Differentially gated against `run_bank` over the FULL bank: CHAIN derives exactly the
goal-predicate facts the full forward closure does, while NEVER applying a rule the goal doesn't
need (the demand-scoping win, made of visible `<demand>` control nodes).
"""
import ugm as h
from ugm import (
    AttrGraph, run_bank, derived_triples,
    build_head_index, rules_producing,
    chain, demand_closure, relevant_rules, demanded_preds,
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


def _preds(triples, pred) -> set:
    return {t for t in triples if t[1] == pred}


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


# --- Phase 4.3: CHAIN demand closure + relevance -------------------------------------------------

def test_demand_closure_pulls_body_predicates_transitively():
    # eligible <- qualified <- member : demanding `eligible` must demand `qualified` and `member`.
    D = h.Rule(key="d", lhs=[h.Pat("?x", "qualified", "?y")], rhs=[h.Pat("?x", "eligible", "?y")])
    E = h.Rule(key="e", lhs=[h.Pat("?x", "member", "?y")], rhs=[h.Pat("?x", "qualified", "?y")])
    UNREL = h.Rule(key="u", lhs=[h.Pat("?x", "b", "?y")], rhs=[h.Pat("?x", "unrelated", "?y")])
    rg, nodes = _reify([D, E, UNREL])
    demanded = demand_closure(rg, "eligible")
    assert demanded == {"eligible", "qualified", "member"}   # transitive, NOT `unrelated`/`b`
    assert demanded_preds(rg) == demanded                    # ... and visible as <demand> nodes
    assert set(relevant_rules(rg, demanded)) == {nodes["d"], nodes["e"]}   # UNREL excluded


# --- CHAIN differential gate ---------------------------------------------------------------------

def test_chain_is_complete_for_goal_and_skips_irrelevant_rules():
    facts = [("socrates", "is_a", "philosopher"), ("alice", "follows", "bob")]
    # oracle: run_bank over the FULL bank
    g1 = _facts(facts)
    base1 = derived_triples(g1)
    run_bank(g1, [MORTAL, PERSON, LIKES])
    oracle = derived_triples(g1) - base1

    # CHAIN the goal predicate `is_a`
    g2 = _facts(facts)
    base2 = derived_triples(g2)
    rg, _ = _reify([MORTAL, PERSON, LIKES])
    chain(g2, rg, "is_a")
    got = derived_triples(g2) - base2

    # complete for the goal predicate: every is_a fact the full closure derives, CHAIN derives
    assert _preds(got, "is_a") == _preds(oracle, "is_a")
    assert ("socrates", "is_a", "person") in got and ("socrates", "is_a", "mortal") in got
    # demand-scoped: the `likes` rule is irrelevant to an `is_a` goal, so it never runs
    assert _preds(got, "likes") == set()
    assert ("alice", "likes", "bob") in _preds(oracle, "likes")   # the full bank DID derive it


def test_chain_transitive_goal_matches_run_bank():
    rule = h.Rule(key="is_a.transitive",
                  lhs=[h.Pat("?a", "is_a", "?b"), h.Pat("?b", "is_a", "?c")],
                  rhs=[h.Pat("?a", "is_a", "?c")])
    facts = [("alice", "is_a", "ordering_customer"), ("ordering_customer", "is_a", "customer"),
             ("customer", "is_a", "party")]
    g1 = _facts(facts); base1 = derived_triples(g1); run_bank(g1, [rule])
    oracle = derived_triples(g1) - base1

    g2 = _facts(facts); base2 = derived_triples(g2)
    rg, _ = _reify([rule])
    chain(g2, rg, "is_a")
    got = derived_triples(g2) - base2
    assert got == oracle
    assert ("alice", "is_a", "party") in got


# --- Phase 4.1: BOUND-TUPLE SIP (chain_sip) ------------------------------------------------------

def _sip_vs_run_bank(rules, facts, goal):
    """Run `rules` over `facts` two ways: run_bank (full closure, oracle) and chain_sip (bound-tuple
    demand for `goal`). Return (oracle_derived, sip_derived) as (s, pred, o) triple sets."""
    g1 = _facts(facts); base1 = derived_triples(g1); run_bank(g1, rules)
    oracle = derived_triples(g1) - base1
    g2 = _facts(facts); base2 = derived_triples(g2)
    rg, _ = _reify(rules)
    chain_sip(g2, rg, goal)
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

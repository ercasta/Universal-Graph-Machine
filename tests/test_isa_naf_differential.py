"""
Firmware v3 — DEMAND-DRIVEN NEGATION, step 4: the DIFFERENTIAL GATE that EARNED the retirement of the
forward decided-negation apparatus (`decide.solve` completion + defeat).

HISTORY (recorded in CHANGELOG): before `decide.py` was deleted, these two closed-world banks were run
BOTH ways — the forward `decide.solve` (aggressive `is_not` completion + INTERPOSE defeat) and the
demand-driven NAF (`chain_sip` deciding a NAC by nested negative demand, absence-decides) — and the
yes/no/who answers were IDENTICAL. That equivalence is what made dropping the forward apparatus
answer-preserving (crux 1, ratified), not a leap. The forward oracle is now gone; these pins keep the
demand-driven answers on the two banks as a regression guard.
"""
import ugm as h
from ugm import Pat, Rule, AttrGraph, chain_sip, match_pats


def _facts(triples):
    g = h.Graph()
    ids = {}

    def node(name):
        if name not in ids:
            ids[name] = g.add_node(name)
        return ids[name]

    for s, p, o in triples:
        g.add_relation(node(s), p, node(o))
    return g


def _reify(rules):
    rg = AttrGraph()
    for r in rules:
        h.write_rule(rg, r)
    return rg


def _demand_answer(facts, producers, consumer_nac, head):
    """The demand-driven NAF answer — the closed-world `not P` clause as a plain NAC, decided on demand
    by `chain_sip` (nested negative demand, absence decides). No `is_not` is ever materialized."""
    g = _facts(facts)
    rg = _reify([*producers, consumer_nac])
    chain_sip(g, rg, (head[0], None, head[1]))
    return {g.name(b["?x"]) for b in match_pats(g, [Pat("?x", head[0], head[1])])}


# --- Bank 1: the THIEF elimination (multi-step deduction feeds a closed-world negation) -----------

THIEF_FACTS = [("ada", "is_a", "suspect"), ("bo", "is_a", "suspect"), ("cy", "is_a", "suspect"),
               ("bo", "in", "library"), ("ada", "is", "alibied")]
THIEF_PRODUCERS = [
    Rule(key="innocent", lhs=[Pat("?x", "in", "library")], rhs=[Pat("?x", "is", "innocent")]),
    Rule(key="cleared.innocent", lhs=[Pat("?x", "is", "innocent")], rhs=[Pat("?x", "is", "cleared")]),
    Rule(key="cleared.alibi", lhs=[Pat("?x", "is", "alibied")], rhs=[Pat("?x", "is", "cleared")]),
]
THIEF_CONSUMER_NAC = Rule(key="thief.nac",
                          lhs=[Pat("?x", "is_a", "suspect")], nac=[Pat("?x", "is", "cleared")],
                          rhs=[Pat("?x", "is", "thief")])


def test_thief_demand_driven_answer():
    # only cy (uncleared) is the thief — what the forward decided-negation oracle also produced.
    assert _demand_answer(THIEF_FACTS, THIEF_PRODUCERS, THIEF_CONSUMER_NAC, ("is", "thief")) == {"cy"}


# --- Bank 2: serve-regular (a single-step closed-world negation over a producer) ------------------

SERVE_FACTS = [("alice", "is_a", "customer"), ("bob", "is_a", "customer"), ("alice", "wants", "rush")]
SERVE_PRODUCERS = [Rule(key="urgent.rush", lhs=[Pat("?c", "wants", "rush")],
                        rhs=[Pat("?c", "is", "urgent")])]
SERVE_CONSUMER_NAC = Rule(key="serve.nac",
                          lhs=[Pat("?c", "is_a", "customer")], nac=[Pat("?c", "is", "urgent")],
                          rhs=[Pat("?c", "served", "regular")])


def test_serve_regular_demand_driven_answer():
    # bob (not urgent) is served regular; alice (urgent) is NOT — matching the forward oracle.
    assert _demand_answer(SERVE_FACTS, SERVE_PRODUCERS, SERVE_CONSUMER_NAC, ("served", "regular")) == {"bob"}

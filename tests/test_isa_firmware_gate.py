"""
Phase 4.4 EXIT GATE — the firmware (CHAIN bound-tuple SIP) answers a goal IDENTICALLY to the
reference backward engine (`GoalSolver`) on the ProofWriter POSITIVE slice.

This is the gate the plan sets for Phase 4: "firmware == GoalSolver differentially on the ProofWriter
positive slice." The external ProofWriter corpus is a raw-NL front-end probe (`bench/proofwriter_nl.py`);
the REASONING slice it exercises is positive Horn — a type hierarchy (`is_a` transitivity), attribute
inheritance across the hierarchy (a two-relation join), a linear attribute implication, and a
conjunctive-body rule. This test drives a representative pool of exactly those shapes over many random
fact graphs and every binding pattern of a goal, and asserts `chain_sip`'s goal answers equal
`GoalSolver`'s — the two demand-driven engines (one Python-dict tabling, one visible-`<demand>` firmware)
must agree everywhere. A single dropped or spurious derivation on either side fails here.
"""
import random

import ugm as h
from ugm import Pat, Rule
from ugm import (
    to_attrgraph, derived_triples, Goal, GoalSolver, chain_sip,
)

write_rule = h.write_rule


# A ProofWriter-POSITIVE Horn pool: transitivity (recursion), a 2-relation join (inheritance),
# a linear implication, and a conjunctive-body rule — the reasoning shapes ProofWriter's CWA theories
# reduce to, minus the negation (which is Phase 5 CHECK, not the positive slice).
RULES = [
    Rule(key="is_a_trans",
         lhs=[Pat("?a", "is_a", "?b"), Pat("?b", "is_a", "?c")],
         rhs=[Pat("?a", "is_a", "?c")]),
    Rule(key="inherit",                                        # a thing has its type's attributes
         lhs=[Pat("?x", "is_a", "?t"), Pat("?t", "has", "?p")],
         rhs=[Pat("?x", "has", "?p")]),
    Rule(key="cold_slow",                                      # linear: cold -> slow
         lhs=[Pat("?x", "has", "cold")],
         rhs=[Pat("?x", "has", "slow")]),
    Rule(key="slow_heavy_sinks",                               # conjunctive: slow AND heavy -> sinks
         lhs=[Pat("?x", "has", "slow"), Pat("?x", "has", "heavy")],
         rhs=[Pat("?x", "has", "sinks")]),
]

ATTRS = ["cold", "heavy", "hot", "light"]                     # base attributes (slow/sinks are derived)


def _random_pw_graph(rng: random.Random):
    g = h.Graph()
    ids: dict[str, str] = {}

    def node(n: str) -> str:
        ids[n] = ids[n] if n in ids else g.add_node(n)
        return ids[n]

    ents = [f"e{i}" for i in range(rng.randint(2, 3))]
    types = [f"t{i}" for i in range(rng.randint(2, 3))]
    for _ in range(rng.randint(2, 5)):                        # entity is_a type
        g.add_relation(node(rng.choice(ents)), "is_a", node(rng.choice(types)))
    for _ in range(rng.randint(1, 4)):                        # type is_a type (hierarchy + cycles ok)
        g.add_relation(node(rng.choice(types)), "is_a", node(rng.choice(types)))
    for _ in range(rng.randint(2, 5)):                        # type has attr (inherited down)
        g.add_relation(node(rng.choice(types)), "has", node(rng.choice(ATTRS)))
    for _ in range(rng.randint(0, 3)):                        # entity has attr directly
        g.add_relation(node(rng.choice(ents)), "has", node(rng.choice(ATTRS)))
    return g, ents + types + ATTRS + ["slow", "sinks"]


def _reify() -> h.Graph:
    rg = h.Graph()
    for r in RULES:
        write_rule(rg, r)
    return rg


def _sip_goal_answers(g0, goal) -> set[tuple[str, str]]:
    rel, subj, obj = goal
    ag, _ = to_attrgraph(g0)
    chain_sip(ag, _reify(), goal)
    return {(s, o) for (s, r, o) in derived_triples(ag)
            if r == rel and (subj is None or s == subj) and (obj is None or o == obj)}


def test_chain_sip_matches_goalsolver_on_proofwriter_positive():
    checked = 0
    for seed in range(20):
        rng = random.Random(seed)
        g0, names = _random_pw_graph(rng)
        for rel in ("is_a", "has"):
            for subj in (None, *names):
                for obj in (None, *names):
                    ag_ref, _ = to_attrgraph(g0)
                    want = GoalSolver(ag_ref, RULES).solve(Goal(rel, subj, obj))
                    got = _sip_goal_answers(g0, (rel, subj, obj))
                    assert got == want, (
                        f"seed={seed} goal={rel}({subj},{obj}): "
                        f"firmware {sorted(got)} != GoalSolver {sorted(want)}"
                    )
                    checked += 1
    assert checked > 1000                                     # the sweep actually ran

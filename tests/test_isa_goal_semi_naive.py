"""
The honest-gate parity slice 2: SEMI-NAIVE DELTA evaluation.

`GoalSolver`'s fixpoint used to re-join every demanded goal's whole body every round,
rediscovering answers it had already found (~O(n^3.8) round-churn on a transitive chain).
Semi-naive delta joins a goal's body in FULL exactly once (its seed) and thereafter only
against the previous round's delta, so work drops to ~proportional-to-derivations while the
answers are unchanged.

Two guards here, because the arc invariant is "correctness never traded":

  1. ANSWER-PRESERVATION under randomization (`test_semi_naive_matches_forward_closure`): over
     many random graphs and a pool of interacting positive rules (transitivity, linear
     recursion over a *different* base relation, a two-relation join), the demand-driven
     answer to a random goal must equal the FORWARD CLOSURE filtered to that goal — the
     independent oracle. This is the strong catch for a silent incompleteness (a delta that
     fails to propagate through the join tables OR the graph side-channel would drop an answer
     here). The forward machine (`run_to_fixpoint` over the same rules) never demand-prunes, so
     it is a genuinely separate derivation path, not the same code under test.

  2. The MECHANISM, pinned structurally (`test_each_goal_is_full_joined_at_most_once`): a
     naive fixpoint re-joins in FULL every round (full joins ~ rounds x goals); semi-naive
     full-joins each demanded goal at most once (`solver.full_joins <= #demanded goals`). A
     timing assert would be flaky; this is the non-flaky proof the round-churn is gone.
"""
import random

import ugm as h
from ugm import Pat, Rule
from ugm import to_attrgraph, lower_rule, run_to_fixpoint, derived_triples, Goal, GoalSolver


# A pool of INTERACTING positive relational rules (all inside the lowering + goal fragment:
# literal predicates, LHS-bound RHS endpoints, no NAC/graded). They chain through each other so
# the fixpoint is non-trivial: `reach` is linear recursion over the `edge` base, `sib` is a
# two-relation join over `parent`, and `edge` closes transitively.
RULES = [
    Rule(key="edge_trans",
         lhs=[Pat("?a", "edge", "?b"), Pat("?b", "edge", "?c")],
         rhs=[Pat("?a", "edge", "?c")]),
    Rule(key="reach_base",
         lhs=[Pat("?a", "edge", "?b")],
         rhs=[Pat("?a", "reach", "?b")]),
    Rule(key="reach_step",
         lhs=[Pat("?a", "edge", "?b"), Pat("?b", "reach", "?c")],
         rhs=[Pat("?a", "reach", "?c")]),
    Rule(key="sib",
         lhs=[Pat("?p", "parent", "?x"), Pat("?p", "parent", "?y")],
         rhs=[Pat("?x", "sib", "?y")]),
]


def _forward_closure(ag) -> set[tuple[str, str, str]]:
    """The independent oracle: apply every rule to a joint fixpoint over `ag`. Loops over the
    rules re-running each to its own fixpoint until the DERIVED-TRIPLE SET stops growing (set
    termination, not `ag.version` — repeated MINT of an already-present relation makes duplicate
    rel nodes that bump the version but leave the triple set unchanged)."""
    progs = [(lower_rule(r), r.bound_names()) for r in RULES]
    while True:
        before = derived_triples(ag)
        for prog, keys in progs:
            run_to_fixpoint(ag, prog, keys)
        if derived_triples(ag) == before:
            return set(derived_triples(ag))


def _random_graph(rng: random.Random) -> h.Graph:
    g = h.Graph()
    ids: dict[str, str] = {}

    def node(n: str) -> str:
        ids[n] = ids[n] if n in ids else g.add_node(n)
        return ids[n]

    n = rng.randint(4, 7)
    names = [f"n{i}" for i in range(n)]
    for _ in range(rng.randint(3, 8)):                     # random edge base
        a, b = rng.choice(names), rng.choice(names)
        g.add_relation(node(a), "edge", node(b))
    for _ in range(rng.randint(2, 6)):                     # random parent base
        a, b = rng.choice(names), rng.choice(names)
        g.add_relation(node(a), "parent", node(b))
    return g, names


def _goal_answers_from_closure(closure, rel, subj, obj):
    return {(s, o) for (s, r, o) in closure
            if r == rel and (subj is None or subj == s) and (obj is None or obj == o)}


def test_semi_naive_matches_forward_closure():
    # Over many random programs and every binding pattern of a goal, the demand-driven answer
    # equals the forward closure filtered to the goal. A dropped delta would fail here.
    checked = 0
    for seed in range(25):
        rng = random.Random(seed)
        g, names = _random_graph(rng)

        ag_closure, _ = to_attrgraph(g)
        closure = _forward_closure(ag_closure)

        for rel in ("edge", "reach", "sib"):
            endpoints = [None, *names]
            for subj in endpoints:
                for obj in endpoints:
                    ag, _ = to_attrgraph(g)              # a FRESH graph per goal (demand-driven)
                    got = GoalSolver(ag, RULES).solve(Goal(rel, subj, obj))
                    want = _goal_answers_from_closure(closure, rel, subj, obj)
                    assert got == want, (
                        f"seed={seed} goal={rel}({subj},{obj}): "
                        f"got {sorted(got)} want {sorted(want)}"
                    )
                    checked += 1
    assert checked > 1000                                 # the sweep actually ran


def test_each_goal_is_full_joined_at_most_once():
    # The semi-naive mechanism, pinned structurally: no demanded goal re-runs a FULL body join
    # (that is the round-churn semi-naive removes). A naive fixpoint would full-join every round.
    ag = h.Graph()
    ids: dict[str, str] = {}

    def node(nm: str) -> str:
        ids[nm] = ids[nm] if nm in ids else ag.add_node(nm)
        return ids[nm]

    for i in range(30):                                    # a 30-long edge chain
        ag.add_relation(node(f"e{i}"), "edge", node(f"e{i+1}"))

    aag, _ = to_attrgraph(ag)
    solver = GoalSolver(aag, RULES)
    answers = solver.solve(Goal("reach", "e0", None))

    assert {o for (_, o) in answers} == {f"e{i}" for i in range(1, 31)}
    # full joins are bounded by the number of demanded goals (one seed each), NOT rounds x goals.
    assert solver.full_joins <= len(solver.tables), (
        f"{solver.full_joins} full joins over {len(solver.tables)} demanded goals — "
        "a full re-join per round would exceed this (round-churn regressed)"
    )


def test_answers_are_identical_to_the_naive_walk_free_path():
    # Belt-and-braces on the pathological transitive shape (walker disabled -> pure tabling):
    # the semi-naive answer set is exactly the transitive closure of a chain.
    ag = h.Graph()
    ids: dict[str, str] = {}

    def node(nm: str) -> str:
        ids[nm] = ids[nm] if nm in ids else ag.add_node(nm)
        return ids[nm]

    for i in range(12):
        ag.add_relation(node(f"e{i}"), "edge", node(f"e{i+1}"))

    aag, _ = to_attrgraph(ag)
    got = GoalSolver(aag, [RULES[0]]).solve(Goal("edge", "e0", None))   # edge_trans only
    assert {o for (_, o) in got} == {f"e{i}" for i in range(1, 13)}

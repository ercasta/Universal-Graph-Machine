"""
The honest-gate parity slice: SEED FROM THE GROUND ENDPOINT.

`GoalSolver` proves the goal-directed SEMANTICS; retiring `rewriter.run` is gated on SPEED
parity (the profiled matching-bound wins: df-indexed rarest-anchor seed, hub-flooding
avoidance, semi-naive delta). The first of those — never scanning the whole graph for a
subgoal whose subject or object is already bound — landed in `_facts_matching`/`_materialize`:
they traverse LOCALLY from the bound node's edges (O(degree)) instead of calling
`derived_triples` (O(graph), whose version cache is invalidated by every materialize and
profiled as THE dominant cost).

These tests pin that architectural win so it cannot silently regress back to a full-graph
scan, and confirm the change is exactly answer-preserving (same answers as the naive scan).
The remaining gate item is semi-naive delta (the join re-churn) — see the module docstring
and `docs/graph low level machine/isa-reference.md`.
"""
import ugm.lowering as lowering
from ugm import goal as goalmod
from ugm import to_attrgraph, derived_triples, Goal, GoalSolver
from ugm.attrgraph import AttrGraph, valued
from ugm import Pat, Rule, Graph


TRANS = Rule(
    key="trans",
    lhs=[Pat("?a", "isa", "?b"), Pat("?b", "isa", "?c")],
    rhs=[Pat("?a", "isa", "?c")],
)


def _chain(n: int) -> tuple[AttrGraph, list[Rule]]:
    """e0 -isa-> e1 -isa-> ... -isa-> e{n-1}, with the transitive-closure rule."""
    ag = AttrGraph()
    ids = [ag.add_node({"name": valued(f"e{i}")}) for i in range(n)]
    for i in range(n - 1):
        ag.add_relation(ids[i], "isa", ids[i + 1])
    return ag, [TRANS]


def _count_derived_triples_calls(fn):
    """Run `fn`, returning the number of `derived_triples` full-graph scans it triggered.
    Patches BOTH the definition site and the goal-module import binding."""
    calls = [0]
    orig = lowering.derived_triples

    def counting(ag):
        calls[0] += 1
        return orig(ag)

    lowering.derived_triples = counting
    goalmod.derived_triples = counting
    try:
        fn()
    finally:
        lowering.derived_triples = orig
        goalmod.derived_triples = orig
    return calls[0]


def test_bound_subject_goal_never_scans_the_whole_graph():
    # A ground reachability goal (both endpoints bound) must seed from the ground node and
    # traverse locally — ZERO full-graph `derived_triples` scans.
    def run():
        ag, rules = _chain(20)
        answers = GoalSolver(ag, rules).solve(Goal("isa", "e0", "e19"))
        assert ("e0", "e19") in answers

    assert _count_derived_triples_calls(run) == 0


def test_free_object_goal_still_seeds_from_the_bound_subject():
    # `isa(e0, ?)` — the object is free but the SUBJECT is bound, so it still seeds locally.
    def run():
        ag, rules = _chain(20)
        answers = GoalSolver(ag, rules).solve(Goal("isa", "e0", None))
        assert {o for (_, o) in answers} == {f"e{i}" for i in range(1, 20)}

    assert _count_derived_triples_calls(run) == 0


def test_fully_unbound_goal_enumerates_relation_instances_without_a_scan():
    # `isa(?, ?)` is an inherent full-relation enumeration (no ground endpoint to seed from), but
    # the node-level `_facts_matching` enumerates the reified relation-INSTANCE nodes named `isa`
    # directly (each a subject->[isa]->object path), tokenizing both endpoints — so even this shape
    # no longer needs the O(graph) `derived_triples` scan.
    def run():
        ag, rules = _chain(20)
        answers = GoalSolver(ag, rules).solve(Goal("isa", None, None))
        assert ("e0", "e1") in answers                # a base edge is enumerated

    assert _count_derived_triples_calls(run) == 0


def test_local_traversal_is_answer_preserving_vs_the_scan():
    # The local `_facts_matching` must return EXACTLY what a full-graph scan filtered by the
    # goal would — including facts materialized mid-solve. Cross-check the two directly on a
    # graph that has both base and derived relations.
    ag, rules = _chain(12)
    solver = GoalSolver(ag, rules)
    solver.solve(Goal("isa", "e0", None))            # materialize e0's transitive reach

    all_triples = derived_triples(ag)
    for subj in ("e0", "e5", "e11", "absent"):
        want = {(s, o) for (s, r, o) in all_triples if r == "isa" and s == subj}
        assert solver._facts_matching(Goal("isa", subj, None)) == want
    for obj in ("e3", "e11", "absent"):
        want = {(s, o) for (s, r, o) in all_triples if r == "isa" and o == obj}
        assert solver._facts_matching(Goal("isa", None, obj)) == want


def test_bridged_graph_bound_solve_also_avoids_the_scan():
    # The same on a graph produced by the name-`Graph` bridge (the real path), not just a
    # hand-built AttrGraph.
    g = Graph()
    ids: dict[str, str] = {}

    def node(name: str) -> str:
        ids[name] = ids[name] if name in ids else g.add_node(name)
        return ids[name]

    for s, o in [("x", "y"), ("y", "z"), ("z", "w")]:
        g.add_relation(node(s), "isa", node(o))

    def run():
        ag, _ = to_attrgraph(g)
        answers = GoalSolver(ag, [TRANS]).solve(Goal("isa", "x", "w"))
        assert ("x", "w") in answers

    assert _count_derived_triples_calls(run) == 0

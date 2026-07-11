"""
The graded gate on the goal path — where goal-direction meets the graded layer.

A demanded goal answered via a rule with a graded condition is GATED by the α-cut (an entity
below threshold does not satisfy the goal) and the answer carries its degree — the same
filter `lower_graded` applies to the forward rule, now on the demand-driven path. These tests
pin: the gate filters ground and free-variable goals alike, the recorded degree matches the
engine's `graded_degree`, and nothing below the cut is materialized.
"""
import pytest

import ugm as h
from ugm import Pat, Rule, GradedCondition
from ugm import to_attrgraph, derived_triples, Goal, GoalSolver


# A customer whose `urgency` clears the α-cut is fast-tracked for an in-stock want.
FAST = Rule(
    key="fast",
    lhs=[Pat("?c", "wants", "?f"), Pat("?f", "in_stock", "yes")],
    rhs=[Pat("?c", "fast", "?f")],
    graded=[GradedCondition("?c", {"urgency": 1.0}, 0.5)],
)


def _graded_graph() -> h.Graph:
    g = h.Graph()
    ids: dict[str, str] = {}

    def node(n: str) -> str:
        ids[n] = ids[n] if n in ids else g.add_node(n)
        return ids[n]

    for s, p, o in [("alice", "wants", "vanilla"), ("vanilla", "in_stock", "yes"),
                    ("bob", "wants", "choc"), ("choc", "in_stock", "yes")]:
        g.add_relation(node(s), p, node(o))
    g.set_embedding(node("alice"), {"urgency": 0.9})   # clears the 0.5 cut
    g.set_embedding(node("bob"), {"urgency": 0.3})     # below the cut
    return g


def test_ground_goal_passes_and_records_degree():
    ag, _ = to_attrgraph(_graded_graph())
    solver = GoalSolver(ag, [FAST])
    assert solver.solve(Goal("fast", "alice", "vanilla")) == {("alice", "vanilla")}
    assert solver.degree[("fast", "alice", "vanilla")] == pytest.approx(0.9)


def test_ground_goal_below_cut_is_gated_out():
    ag, _ = to_attrgraph(_graded_graph())
    before = derived_triples(ag)
    solver = GoalSolver(ag, [FAST])
    assert solver.solve(Goal("fast", "bob", "choc")) == set()      # gated by the α-cut
    assert derived_triples(ag) - before == set()                   # nothing materialized


def test_free_goal_returns_only_those_above_the_cut():
    ag, _ = to_attrgraph(_graded_graph())
    solver = GoalSolver(ag, [FAST])
    ans = solver.solve(Goal("fast", None, None))
    assert ans == {("alice", "vanilla")}                           # bob filtered out
    assert "bob" not in {s for (s, o) in ans}


def test_goal_path_degree_matches_the_alpha_cut_formula():
    # the graded condition has ONE clause ({"urgency": 1.0}, threshold 0.5, not inverted), so the
    # degree is just alice's raw "urgency" embedding score (0.9) — pinned directly (no second
    # engine needed to recompute it).
    g = _graded_graph()
    ag, _ = to_attrgraph(g)
    solver = GoalSolver(ag, [FAST])
    solver.solve(Goal("fast", None, None))
    goal_by_name = {s: solver.degree[("fast", s, o)] for (s, o) in solver.tables[Goal("fast", None, None)]}

    assert set(goal_by_name) == {"alice"}
    assert goal_by_name["alice"] == pytest.approx(0.9)

"""
Goal-directed evaluation — the shift from "forward rushing to fixpoint" to "acting toward a
goal" (§6a "Everything is goal-directed", decision_labelless_substrate).

The contrast is the whole point: over the SAME rules and facts, `run_to_fixpoint` derives the
full closure, while `GoalSolver` demand-drives and materializes ONLY what the goal needs. These
tests pin (1) the goal-directed answer is correct and (2) it does strictly LESS work — it never
materializes a fact the goal did not demand.
"""
import ugm as h
from ugm import Pat, Rule
from ugm import (
    to_attrgraph, lower_rule, run_to_fixpoint, derived_triples, Goal, GoalSolver, solve_goal,
)


TRANS = Rule(
    key="trans",
    lhs=[Pat("?a", "isa", "?b"), Pat("?b", "isa", "?c")],
    rhs=[Pat("?a", "isa", "?c")],
)


def _two_chains() -> h.Graph:
    """Two DISJOINT isa chains: x->y->z->w and a->b->c->d."""
    g = h.Graph()
    ids: dict[str, str] = {}

    def node(n: str) -> str:
        ids[n] = ids[n] if n in ids else g.add_node(n)
        return ids[n]

    for s, o in [("x", "y"), ("y", "z"), ("z", "w"),
                 ("a", "b"), ("b", "c"), ("c", "d")]:
        g.add_relation(node(s), "isa", node(o))
    return g


def test_goal_answers_and_touches_only_the_relevant_chain():
    ag, _ = to_attrgraph(_two_chains())
    init = derived_triples(ag)
    answers, derived = solve_goal(ag, [TRANS], Goal("isa", "x", "w"))

    assert ("x", "w") in answers                      # the goal is answered...

    # ...and NO fact from the a->b->c->d chain was DERIVED (the base a-chain facts stay, but the
    # goal-directed run never materialized a NEW one — it was never demanded).
    new_triples = derived_triples(ag) - init
    assert new_triples, "goal-directed run derived nothing"
    assert all(s in {"x", "y", "z"} for (s, r, o) in new_triples), \
        f"goal-directed run leaked into the irrelevant chain: {sorted(new_triples)}"
    assert ("a", "isa", "c") not in new_triples
    assert ("a", "isa", "d") not in new_triples
    assert derived >= 1


def test_goal_directed_derives_strictly_less_than_fixpoint():
    # Forward-rush: the FULL closure of BOTH chains.
    ag_full, _ = to_attrgraph(_two_chains())
    init_full = derived_triples(ag_full)
    run_to_fixpoint(ag_full, lower_rule(TRANS), TRANS.bound_names())
    full_derived = derived_triples(ag_full) - init_full

    # Goal-directed: only what `isa(x, w)` needs.
    ag_goal, _ = to_attrgraph(_two_chains())
    init_goal = derived_triples(ag_goal)
    solve_goal(ag_goal, [TRANS], Goal("isa", "x", "w"))
    goal_derived = derived_triples(ag_goal) - init_goal

    assert goal_derived, "goal-directed run derived nothing"
    assert goal_derived < full_derived, (
        f"expected goal-directed ({sorted(goal_derived)}) to be a strict subset of the "
        f"fixpoint closure ({sorted(full_derived)})"
    )
    # the closure derives facts in BOTH chains; the goal run derives none of the a-chain's
    assert any(s == "a" for (s, r, o) in full_derived)
    assert not any(s == "a" for (s, r, o) in goal_derived)


def test_goal_with_free_object_enumerates_reachable():
    # `isa(x, ?)` — everything x reaches transitively (but still only x's chain).
    ag, _ = to_attrgraph(_two_chains())
    answers, _ = solve_goal(ag, [TRANS], Goal("isa", "x", None))
    reached = {o for (s, o) in answers}
    assert {"y", "z", "w"} <= reached                 # x reaches y, z, w
    assert "d" not in reached                          # never the other chain


def test_unprovable_goal_returns_no_answers():
    ag, _ = to_attrgraph(_two_chains())
    answers, _ = solve_goal(ag, [TRANS], Goal("isa", "x", "d"))   # x cannot reach d
    assert answers == set()

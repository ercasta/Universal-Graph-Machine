"""
Deeper walker integration — beyond the pure same-relation transitive-closure shape.

Two generalizations of the long-range demand primitive, each differential-tested against
tabling (the trusted oracle — pure `GoalSolver` without `walk_fuel`, itself validated against
the forward closure in `test_isa_goal_semi_naive.py`):

  1. LINEAR RECURSION over a DIFFERENT base relation. `anc` is the transitive closure of
     `parent` (`anc(a,b):-parent(a,b)`, `anc(a,c):-parent(a,b),anc(b,c)`), so a ground
     `anc`-reachability goal is carried by a walker over `parent`'s edges, materializing the
     shortcut AS `anc` (walk one relation, mint another). The right-recursive step form is
     detected too.

  2. A walker spawned for a reachability subgoal arising INSIDE a larger tabled query: a rule
     whose body pairs a candidate-endpoints fact with a ground `anc(?x,?y)` reachability check
     drives the interior subgoal onto a walker, not the tabled chain.

Plus the soundness fix the generalization surfaced: a transitive-closure walker answers >= 1
hop, so a reflexive `rel(a,a)` holds ONLY via a real cycle (the old 0-hop short-circuit was
latently unsound). Pinned on a cyclic graph for both the linear and the same-relation shapes.
"""
import random

import ugm as h
from ugm import Pat, Rule
from ugm import to_attrgraph, derived_triples, Goal, GoalSolver


# anc = transitive closure of the base relation `parent` (linear recursion over a DIFFERENT base).
ANC_BASE = Rule(key="anc_base", lhs=[Pat("?a", "parent", "?b")], rhs=[Pat("?a", "anc", "?b")])
ANC_STEP = Rule(key="anc_step",
                lhs=[Pat("?a", "parent", "?b"), Pat("?b", "anc", "?c")],
                rhs=[Pat("?a", "anc", "?c")])
ANC = [ANC_BASE, ANC_STEP]

# the RIGHT-recursive step form — same closure of `parent`, different clause arrangement.
ANC_STEP_RIGHT = Rule(key="anc_step_r",
                      lhs=[Pat("?a", "anc", "?b"), Pat("?b", "parent", "?c")],
                      rhs=[Pat("?a", "anc", "?c")])
ANC_RIGHT = [ANC_BASE, ANC_STEP_RIGHT]

# the same-relation transitive closure, for the reflexive-fix cross-check.
ISA_TRANS = Rule(key="isa", lhs=[Pat("?a", "isa", "?b"), Pat("?b", "isa", "?c")],
                 rhs=[Pat("?a", "isa", "?c")])


def _graph(edges: list[tuple[str, str, str]]) -> h.Graph:
    g = h.Graph()
    ids: dict[str, str] = {}

    def node(n: str) -> str:
        ids[n] = ids[n] if n in ids else g.add_node(n)
        return ids[n]

    for s, rel, o in edges:
        g.add_relation(node(s), rel, node(o))
    # DECLARED strategies (Phase 5.4) — the walker base map is KB DATA, not rule-shape sniffing.
    # `anc` is the transitive closure of `parent` (linear recursion, walk `parent`); `isa` is a
    # same-relation transitive closure. Declaring a relation not present in `edges` is inert.
    g.add_relation(node("anc"), "transitive_closure_of", node("parent"))
    g.add_relation(node("isa"), "rel_property", node("transitive"))
    return g


def _parent_chain(n: int) -> h.Graph:
    return _graph([(f"p{i}", "parent", f"p{i+1}") for i in range(n - 1)])


def test_linear_recursion_ground_goal_is_walked_over_the_base():
    # anc(p0, p3) is reachable via parent edges; the walker carries it over `parent` and mints
    # the shortcut as `anc`, materializing ONLY that shortcut (not the tabled intermediates).
    ag, _ = to_attrgraph(_parent_chain(4))
    init = derived_triples(ag)
    solver = GoalSolver(ag, ANC, walk_fuel=100)
    ans = solver.solve(Goal("anc", "p0", "p3"))

    assert ans == {("p0", "p3")}
    assert solver.walked == 1                              # carried by a walker...
    new = derived_triples(ag) - init
    assert new == {("p0", "anc", "p3")}                   # ...minted as `anc`, only the shortcut


def test_linear_recursion_walker_agrees_with_tabling_left_and_right():
    for rules in (ANC, ANC_RIGHT):
        g = _parent_chain(5)
        tabled = GoalSolver(to_attrgraph(g)[0], rules).solve(Goal("anc", "p0", "p4"))
        walked = GoalSolver(to_attrgraph(g)[0], rules, walk_fuel=100).solve(Goal("anc", "p0", "p4"))
        assert tabled == walked == {("p0", "p4")}


def test_linear_recursion_free_object_still_tables():
    # anc(p0, ?) is not ground -> tabling, not the walker (the walker only carries ground goals).
    ag, _ = to_attrgraph(_parent_chain(4))
    solver = GoalSolver(ag, ANC, walk_fuel=100)
    ans = solver.solve(Goal("anc", "p0", None))
    assert {o for (_, o) in ans} == {"p1", "p2", "p3"}
    assert solver.walked == 0


def test_fuel_bounds_the_linear_reach():
    ag, _ = to_attrgraph(_parent_chain(5))                # p0..p4; p0->p4 is 4 parent hops
    assert GoalSolver(ag, ANC, walk_fuel=2).solve(Goal("anc", "p0", "p4")) == set()
    ag2, _ = to_attrgraph(_parent_chain(5))
    assert GoalSolver(ag2, ANC, walk_fuel=4).solve(Goal("anc", "p0", "p4")) == {("p0", "p4")}


def test_interior_reachability_subgoal_is_walked():
    # A larger TABLED query whose body demands a ground anc(?x,?y) reachability check: SIP binds
    # both endpoints from the `candidate` fact, so the interior anc subgoal lands on a walker.
    verified = Rule(key="verified",
                    lhs=[Pat("?x", "candidate", "?y"), Pat("?x", "anc", "?y")],
                    rhs=[Pat("?x", "verified", "?y")])
    rules = [*ANC, verified]
    edges = [("a", "parent", "b"), ("b", "parent", "c"), ("c", "parent", "d"),
             ("a", "candidate", "d"), ("a", "candidate", "b"), ("d", "candidate", "a")]

    tabled = GoalSolver(to_attrgraph(_graph(edges))[0], rules).solve(Goal("verified", None, None))

    solver = GoalSolver(to_attrgraph(_graph(edges))[0], rules, walk_fuel=100)
    walked = solver.solve(Goal("verified", None, None))

    assert tabled == walked == {("a", "d"), ("a", "b")}   # d->a is not parent-reachable
    assert solver.walked >= 1                             # an interior anc subgoal was walked


def test_reflexive_answer_requires_a_real_cycle_linear():
    # anc(x, x) holds ONLY through a parent-cycle. Differential vs tabling on both a cyclic and
    # an acyclic graph — the >= 1-hop transitive semantics, not reflexive-transitive.
    cyclic = _graph([("x", "parent", "y"), ("y", "parent", "x")])
    assert GoalSolver(to_attrgraph(cyclic)[0], ANC).solve(Goal("anc", "x", "x")) == {("x", "x")}
    assert (GoalSolver(to_attrgraph(cyclic)[0], ANC, walk_fuel=100)
            .solve(Goal("anc", "x", "x")) == {("x", "x")})

    acyclic = _graph([("x", "parent", "y"), ("y", "parent", "z")])
    assert GoalSolver(to_attrgraph(acyclic)[0], ANC).solve(Goal("anc", "x", "x")) == set()
    assert (GoalSolver(to_attrgraph(acyclic)[0], ANC, walk_fuel=100)
            .solve(Goal("anc", "x", "x")) == set())


def test_reflexive_answer_requires_a_real_cycle_same_relation():
    # The same fix on the original same-relation shape: isa(a,a) only via an isa-cycle.
    cyclic = _graph([("a", "isa", "b"), ("b", "isa", "a")])
    assert GoalSolver(to_attrgraph(cyclic)[0], [ISA_TRANS]).solve(Goal("isa", "a", "a")) == {("a", "a")}
    assert (GoalSolver(to_attrgraph(cyclic)[0], [ISA_TRANS], walk_fuel=100)
            .solve(Goal("isa", "a", "a")) == {("a", "a")})

    acyclic = _graph([("a", "isa", "b")])
    assert GoalSolver(to_attrgraph(acyclic)[0], [ISA_TRANS]).solve(Goal("isa", "a", "a")) == set()
    assert (GoalSolver(to_attrgraph(acyclic)[0], [ISA_TRANS], walk_fuel=100)
            .solve(Goal("isa", "a", "a")) == set())


def test_walker_matches_tabling_over_random_parent_graphs_including_cycles():
    # The strong soundness guard: over random `parent` graphs (cycles allowed) and every ground
    # ordered pair (incl. reflexive), the walker answer equals the tabled answer.
    checked = 0
    for seed in range(40):
        rng = random.Random(seed)
        names = [f"n{i}" for i in range(rng.randint(3, 6))]
        edges = [(rng.choice(names), "parent", rng.choice(names))
                 for _ in range(rng.randint(2, 7))]
        g = _graph(edges)
        for a in names:
            for b in names:
                tabled = GoalSolver(to_attrgraph(g)[0], ANC).solve(Goal("anc", a, b))
                walked = GoalSolver(to_attrgraph(g)[0], ANC, walk_fuel=1000).solve(Goal("anc", a, b))
                assert tabled == walked, f"seed={seed} anc({a},{b}): tabled {tabled} walker {walked}"
                checked += 1
    assert checked > 300

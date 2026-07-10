"""
Walker-into-GoalSolver integration — goal-direction with BOUNDED long-range demand.

`GoalSolver(..., walk_fuel=N)` answers a GROUND reachability goal on a transitive-closure
relation with a fuel-bounded walker instead of tabling the whole chain. These tests pin: the
answer agrees with pure tabling, the walker path materializes strictly FEWER facts (just the
shortcut, not the intermediates the tabled closure leaves), fuel bounds the reach, and
free-variable goals still fall to tabling.
"""
import ugm as h
from ugm import Pat, Rule
from ugm import to_attrgraph, derived_triples, Goal, GoalSolver
from ugm.goal import _closure_declarations


TRANS = Rule(
    key="trans",
    lhs=[Pat("?a", "isa", "?b"), Pat("?b", "isa", "?c")],
    rhs=[Pat("?a", "isa", "?c")],
)


def _chains() -> h.Graph:
    """x -> y -> z -> w  and a disjoint a -> b -> c."""
    g = h.Graph()
    ids: dict[str, str] = {}

    def node(n: str) -> str:
        ids[n] = ids[n] if n in ids else g.add_node(n)
        return ids[n]

    for s, o in [("x", "y"), ("y", "z"), ("z", "w"), ("a", "b"), ("b", "c")]:
        g.add_relation(node(s), "isa", node(o))
    g.add_relation(node("isa"), "rel_property", node("transitive"))   # DECLARED strategy (Phase 5.4): walk `isa`
    return g


def test_ground_reachability_goal_uses_walker():
    ag, _ = to_attrgraph(_chains())
    solver = GoalSolver(ag, [TRANS], walk_fuel=100)
    ans = solver.solve(Goal("isa", "x", "w"))

    assert ans == {("x", "w")}
    assert solver.walked == 1                         # the goal was carried by a walker...
    # ...and it materialized ONLY the x->w shortcut, not the tabled closure's intermediates
    assert solver.derived == 1


def test_walker_answer_agrees_with_pure_tabling():
    # same question, both drivers -> same yes/no
    ag_tab, _ = to_attrgraph(_chains())
    tabled = GoalSolver(ag_tab, [TRANS]).solve(Goal("isa", "x", "w"))

    ag_walk, _ = to_attrgraph(_chains())
    walked = GoalSolver(ag_walk, [TRANS], walk_fuel=100).solve(Goal("isa", "x", "w"))

    assert tabled == walked == {("x", "w")}


def test_walker_materializes_strictly_fewer_facts_than_tabling():
    ag_tab, _ = to_attrgraph(_chains())
    init_tab = derived_triples(ag_tab)
    GoalSolver(ag_tab, [TRANS]).solve(Goal("isa", "x", "w"))
    tabled_new = derived_triples(ag_tab) - init_tab       # {x->z, x->w, y->w}

    ag_walk, _ = to_attrgraph(_chains())
    init_walk = derived_triples(ag_walk)
    GoalSolver(ag_walk, [TRANS], walk_fuel=100).solve(Goal("isa", "x", "w"))
    walked_new = derived_triples(ag_walk) - init_walk     # {x->w} only

    assert walked_new == {("x", "isa", "w")}
    assert walked_new < tabled_new                        # strict subset — bounded work


def test_fuel_bounds_the_integrated_reach():
    ag, _ = to_attrgraph(_chains())
    # x->w is 3 hops; fuel 2 cannot reach it even though it is derivable
    assert GoalSolver(ag, [TRANS], walk_fuel=2).solve(Goal("isa", "x", "w")) == set()

    ag2, _ = to_attrgraph(_chains())
    assert GoalSolver(ag2, [TRANS], walk_fuel=3).solve(Goal("isa", "x", "w")) == {("x", "w")}


def test_free_object_goal_still_tables():
    # `isa(x, ?)` is not a ground reachability query -> tabling, not the walker
    ag, _ = to_attrgraph(_chains())
    solver = GoalSolver(ag, [TRANS], walk_fuel=100)
    ans = solver.solve(Goal("isa", "x", None))
    assert {o for (s, o) in ans} >= {"y", "z", "w"}
    assert solver.walked == 0                              # walker not triggered for a free goal


def test_unreachable_ground_goal_is_bounded_and_empty():
    ag, _ = to_attrgraph(_chains())
    solver = GoalSolver(ag, [TRANS], walk_fuel=100)
    assert solver.solve(Goal("isa", "x", "c")) == set()   # x cannot reach the a-chain
    assert solver.walked == 1
    assert solver.derived == 0                             # nothing materialized


# --- Phase 5.4: the walker strategy is a DECLARED FACT read from the substrate, not sniffed ---

def test_closure_declarations_reads_the_canonical_rel_property_fact():
    # `R is transitive` -> the canonical `R -[rel_property]-> transitive` fact (the SAME
    # declaration that generates the transitivity rule); the walker reads it as its base map.
    decl = h.Graph()
    h.load_text(decl, "is_a is transitive")
    h.run(decl, h.RELATION_PROPERTY_FORMS)                 # declaration -> rel_property fact
    ag, _ = to_attrgraph(decl)
    assert _closure_declarations(ag) == {"is_a": "is_a"}   # {R: R}, read as DATA

    # a relation WITHOUT the declaration is not walkable (no shape-sniffing fallback)
    plain, _ = to_attrgraph(_chains_named("likes"))
    assert _closure_declarations(plain) == {}


def test_walker_fires_end_to_end_from_the_cnl_declaration():
    # Full chain: CNL `is_a is transitive` -> rel_property fact + generated rule; a ground
    # reachability goal is then carried by the walker over `is_a` and agrees with tabling.
    g = h.Graph()
    h.load_text(g, "is_a is transitive")
    h.run(g, h.RELATION_PROPERTY_FORMS)
    rules = h.rules_in_graph(h.expand_relation_properties(g))
    ids = {n: g.add_node(n) for n in ("p", "q", "r")}
    for s, o in [("p", "q"), ("q", "r")]:
        g.add_relation(ids[s], "is_a", ids[o])

    ag_tab, _ = to_attrgraph(g)
    tabled = GoalSolver(ag_tab, rules).solve(Goal("is_a", "p", "r"))
    ag_walk, _ = to_attrgraph(g)
    solver = GoalSolver(ag_walk, rules, walk_fuel=100)
    walked = solver.solve(Goal("is_a", "p", "r"))

    assert tabled == walked == {("p", "r")}
    assert solver.walked == 1                              # the DECLARED strategy carried it


def _chains_named(rel: str) -> h.Graph:
    g = h.Graph()
    ids: dict[str, str] = {}

    def node(n: str) -> str:
        ids[n] = ids[n] if n in ids else g.add_node(n)
        return ids[n]

    for s, o in [("x", "y"), ("y", "z")]:
        g.add_relation(node(s), rel, node(o))
    return g

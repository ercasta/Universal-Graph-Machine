"""
Walkers — the long-range demand primitive of goal-direction (decision_walkers_locality,
vision §6a/§11). A fuel-bounded walk carries a reachability goal across the graph; fuel is
the content-blind effort budget ("think harder" = more fuel); arrival materializes a
shortcut. These tests pin: bounded reach, the fuel/depth relationship, goal-directedness
(never the disjoint chain), termination through cycles, and shortcut discovery.
"""
import ugm as h
from ugm import to_attrgraph, derived_triples, walk_to_goal, Walker


def _chain_graph() -> h.Graph:
    """x -> y -> z -> w -> v  (length-4 isa chain) and a disjoint a -> b."""
    g = h.Graph()
    ids: dict[str, str] = {}

    def node(n: str) -> str:
        ids[n] = ids[n] if n in ids else g.add_node(n)
        return ids[n]

    for s, o in [("x", "y"), ("y", "z"), ("z", "w"), ("w", "v"), ("a", "b")]:
        g.add_relation(node(s), "isa", node(o))
    return g


def test_walker_reaches_within_fuel_and_materializes_shortcut():
    ag, _ = to_attrgraph(_chain_graph())
    before = derived_triples(ag)
    res = walk_to_goal(ag, "isa", "x", "w", fuel=10)

    assert res.reached
    assert res.path == ["x", "y", "z", "w"]
    assert res.hops == 3

    # the discovered shortcut is a NEW derived fact, marked as a walker discovery
    new = derived_triples(ag) - before
    assert ("x", "isa", "w") in new
    # the shortcut rel node carries the `shortcut` provenance marker
    shortcut_nodes = [r for r in ag.nodes()
                      if (a := ag.get_attr(r, "name")) is not None and a.value == "isa"
                      and ag.has_key(r, "shortcut")]
    assert shortcut_nodes, "no shortcut-marked relation was materialized"


def test_fuel_bounds_reach_and_more_fuel_reaches_farther():
    # reaching w from x needs 3 edge-traversals; 2 is not enough, 3 is ("think harder").
    ag2, _ = to_attrgraph(_chain_graph())
    assert not walk_to_goal(ag2, "isa", "x", "w", fuel=2).reached

    ag3, _ = to_attrgraph(_chain_graph())
    assert walk_to_goal(ag3, "isa", "x", "w", fuel=3).reached

    # a low-fuel failure materializes NO shortcut (nothing derived)
    ag_low, _ = to_attrgraph(_chain_graph())
    before = derived_triples(ag_low)
    walk_to_goal(ag_low, "isa", "x", "v", fuel=2)          # v is 4 hops away
    assert derived_triples(ag_low) - before == set()


def test_walker_is_goal_directed_never_touches_disjoint_chain():
    ag, _ = to_attrgraph(_chain_graph())
    before = derived_triples(ag)
    res = walk_to_goal(ag, "isa", "a", "w", fuel=100)      # a cannot reach w (disjoint)
    assert not res.reached
    # bounded to a's reachable set; no fact from x's chain is derived
    assert derived_triples(ag) - before == set()


def test_walker_terminates_through_a_cycle():
    # x -> y -> z -> x  (a cycle); target unreachable node should still terminate.
    g = h.Graph()
    ids: dict[str, str] = {}

    def node(n: str) -> str:
        ids[n] = ids[n] if n in ids else g.add_node(n)
        return ids[n]

    for s, o in [("x", "y"), ("y", "z"), ("z", "x")]:
        g.add_relation(node(s), "isa", node(o))
    node("q")                                              # an isolated, unreachable node
    ag, _ = to_attrgraph(g)

    res = walk_to_goal(ag, "isa", "x", "q", fuel=1000)     # never reachable; must not hang
    assert not res.reached
    # and a reachable target in the cycle is found
    assert walk_to_goal(ag, "isa", "x", "z", fuel=1000).reached


def test_shortcut_makes_the_repeat_query_direct():
    # fresh: x -> v is 4 hops, so a fuel-2 walk cannot reach it
    ag_fresh, _ = to_attrgraph(_chain_graph())
    assert not walk_to_goal(ag_fresh, "isa", "x", "v", fuel=2).reached

    # after a well-fuelled discovery, x -> v is a DIRECT edge, so the same small fuel now
    # suffices — the discovery paid down the cost of the long path (x has ≤2 direct
    # successors, so fuel 2 finds v regardless of frontier order).
    ag, _ = to_attrgraph(_chain_graph())
    walk_to_goal(ag, "isa", "x", "v", fuel=100)
    assert walk_to_goal(ag, "isa", "x", "v", fuel=2).reached

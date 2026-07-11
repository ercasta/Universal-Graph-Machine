"""
The reference ISA machine's own derivations on the positive, monotone, non-graded fragment
(docs/graph low level machine/isa-reference.md "Next slice").

For each rule + fact set: lower the `Rule` to an ISA program, bridge the graph to the label-less
`AttrGraph`, run the reference machine to fixpoint, and assert the derived relation SET against a
FIXED expected value (computed by hand from the rule + facts). Equivalence with the previous
(rewriter / name-based) generation is NOT a correctness target (implementation_plan.md, 2026-07-10
ratification) — these pin the ISA machine's own behavior directly.

Note on triple extraction: `derived_triples` structurally over-approximates a "relation" (any node
that sits between a predecessor and a successor), so the expected sets below include that noise
(e.g. `(can_get, vanilla, in_stock)` alongside the intended `(alice, can_get, vanilla)`) — pinned
as observed. We ALSO assert membership of the intended triple, for legibility.
"""
import pytest

import ugm as h
from ugm import Pat, Rule, GradedCondition
from ugm import to_attrgraph, lower_rule, run_to_fixpoint, derived_triples
from ugm.lowering import lower_lhs, lower_graded, Unlowerable
from ugm.machine import Machine


# ---------------------------------------------------------------------------
# Helpers — build a KB graph, run the ISA machine, extract derived relation triples
# ---------------------------------------------------------------------------

def _build(facts: list[tuple[str, str, str]]) -> h.Graph:
    """One node per distinct name (a loaded KB), one relation per fact."""
    g = h.Graph()
    ids: dict[str, str] = {}

    def node(name: str) -> str:
        if name not in ids:
            ids[name] = g.add_node(name)
        return ids[name]

    for s, p, o in facts:
        g.add_relation(node(s), p, node(o))
    return g


def _machine_derived(g, rule) -> set[tuple[str, str, str]]:
    ag, _ = to_attrgraph(g)
    init = derived_triples(ag)
    program = lower_rule(rule)
    run_to_fixpoint(ag, program, rule.bound_names())
    return derived_triples(ag) - init


# ---------------------------------------------------------------------------
# Rule A — a 2-clause conjunction (non-recursive), with a literal object
# ---------------------------------------------------------------------------

CAN_GET = Rule(
    key="can_get",
    lhs=[Pat("?c", "wants", "?f"), Pat("?f", "in_stock", "yes")],
    rhs=[Pat("?c", "can_get", "?f")],
)


def test_conjunction_with_literal_object_agrees():
    facts = [
        ("alice", "wants", "vanilla"), ("vanilla", "in_stock", "yes"),
        ("bob", "wants", "kale"),                       # kale not in stock -> no derivation
    ]
    derived = _machine_derived(_build(facts), CAN_GET)
    assert derived == {("alice", "can_get", "vanilla"), ("can_get", "vanilla", "in_stock")}
    assert ("alice", "can_get", "vanilla") in derived
    assert not any(t[1] == "can_get" and t[0] == "bob" for t in derived)


# ---------------------------------------------------------------------------
# Rule B — transitivity (RECURSIVE): the fixpoint driver + fired-suppression
# ---------------------------------------------------------------------------

TRANS = Rule(
    key="trans",
    lhs=[Pat("?a", "isa", "?b"), Pat("?b", "isa", "?c")],
    rhs=[Pat("?a", "isa", "?c")],
)


def test_transitive_closure_agrees():
    facts = [("x", "isa", "y"), ("y", "isa", "z"), ("z", "isa", "w")]
    derived = _machine_derived(_build(facts), TRANS)
    assert derived == {("x", "isa", "z"), ("x", "isa", "w"), ("y", "isa", "w")}
    # the closure beyond the three base edges
    assert ("x", "isa", "z") in derived
    assert ("x", "isa", "w") in derived
    assert ("y", "isa", "w") in derived


# ---------------------------------------------------------------------------
# Rule C — a 4-clause join where the last clause has BOTH endpoints bound (SAME)
# ---------------------------------------------------------------------------

HAZARD = Rule(
    key="hazard",
    lhs=[
        Pat("?m", "kind", "mutation"),
        Pat("?m", "mutate", "?c"),
        Pat("?loop", "contain", "?m"),
        Pat("?loop", "consume", "?c"),          # ?loop and ?c both already bound -> SAME
    ],
    rhs=[Pat("?loop", "hazard", "?m")],
)

_HAZARD_FACTS = [
    ("del", "kind", "mutation"),
    ("loop", "contain", "del"),
    ("loop", "consume", "qs"),
]


def test_four_clause_join_with_same_fires_and_agrees():
    facts = _HAZARD_FACTS + [("del", "mutate", "qs")]   # mutates the consumed collection
    derived = _machine_derived(_build(facts), HAZARD)
    assert derived == {("hazard", "del", "kind"), ("hazard", "del", "mutate"),
                        ("loop", "hazard", "del")}
    assert ("loop", "hazard", "del") in derived


def test_four_clause_join_near_miss_agrees():
    facts = _HAZARD_FACTS + [("del", "mutate", "other")]  # mutates a DIFFERENT collection
    derived = _machine_derived(_build(facts), HAZARD)
    assert derived == set()                               # the machine derives nothing
    assert not any(t[1] == "hazard" for t in derived)


# ---------------------------------------------------------------------------
# Graded α-cut — GRADE reproduces `rewriter.graded_degree` (gate AND degree)
# ---------------------------------------------------------------------------

# A graded rule over plain relations: a customer whose `urgency` clears the α-cut is fast-tracked
# for an in-stock want. (Plain-relation RHS between bound vars — the graded SEMANTICS is the point;
# literal/concept RHS endpoints are a separate deferred item.)
FAST = Rule(
    key="fast",
    lhs=[Pat("?c", "wants", "?f"), Pat("?f", "in_stock", "yes")],
    rhs=[Pat("?c", "fast", "?f")],
    graded=[GradedCondition("?c", {"urgency": 1.0}, 0.5)],
)


def _graded_graph():
    g = _build([
        ("alice", "wants", "vanilla"), ("vanilla", "in_stock", "yes"),
        ("bob", "wants", "choc"), ("choc", "in_stock", "yes"),
    ])
    # embeddings: alice clears the α-cut (0.9 ≥ 0.5), bob does not (0.3 < 0.5)
    g.set_embedding(g.nodes_named("alice")[0], {"urgency": 0.9})
    g.set_embedding(g.nodes_named("bob")[0], {"urgency": 0.3})
    return g


def test_graded_alpha_cut_gate_and_degree_match_engine():
    g = _graded_graph()

    # the lowered program's match phase (structure + GRADE): score per surviving state, gated by
    # the α-cut (bob's 0.3 < the 0.5 threshold so he never appears).
    ag, _ = to_attrgraph(g)
    match_ops = lower_lhs(FAST) + lower_graded(FAST)
    machine: dict[str, float] = {}
    for st in Machine().match(ag, match_ops):
        name = ag.get_attr(st.regs["?c"], "name").value
        machine[name] = st.score

    assert set(machine) == {"alice"}                       # only alice clears the cut
    assert machine["alice"] == pytest.approx(0.9)          # degree == alice's raw urgency score


def test_graded_rule_derivation_agrees():
    # end-to-end: the derived relation SET, pinned directly (the α-cut gates which fire)
    derived = _machine_derived(_graded_graph(), FAST)
    assert derived == {("alice", "fast", "vanilla"), ("fast", "vanilla", "in_stock")}
    assert ("alice", "fast", "vanilla") in derived
    assert not any(t[0] == "bob" for t in derived)


# ---------------------------------------------------------------------------
# The lowering still refuses what is outside the fragment (explicit, never silent)
# ---------------------------------------------------------------------------

def test_lowering_refuses_inverted_graded_and_nac():
    inverted = Rule(key="g", lhs=[Pat("?c", "wants", "?f")], rhs=[Pat("?c", "vip", "?f")],
                    graded=[GradedCondition("?c", {"urgency": 1.0}, 0.5, inverted=True)])
    with pytest.raises(Unlowerable):
        lower_rule(inverted)

    nac = Rule(key="n", lhs=[Pat("?c", "wants", "?f")], rhs=[Pat("?c", "vip", "?f")],
               nac=[Pat("?c", "banned", "?f")])
    with pytest.raises(Unlowerable):
        lower_rule(nac)

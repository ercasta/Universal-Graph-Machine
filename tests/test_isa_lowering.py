"""
Differential test: the reference ISA machine reproduces `rewriter.run` on the positive,
monotone, non-graded fragment (docs/graph low level machine/isa-reference.md "Next slice").

For each rule + fact set we derive the new relations TWICE — once with the as-built engine
(`harneskills.run`) and once by lowering the SAME `Rule` to an ISA program, bridging the graph
to the label-less `AttrGraph`, and running the reference machine to fixpoint — and assert the
derived relation SETS are equal. This is the swap-safety check the design names: it pins that
the ISA's matching + emission mean the same thing as the interpreter, on the fragment lowered.

Note on triple extraction: `derived_triples` / `name_triples` structurally over-approximate a
"relation" (any node that sits between a predecessor and a successor). Any such noise is
IDENTICAL on both sides when the two engines agree, so it cancels in the set equality; and it
cannot mask a real divergence (a missing/extra derivation changes some triple). We ALSO assert
membership of the intended triple, for legibility.
"""
import pytest

import ugm as h
from ugm import Pat, Rule, GradedCondition
from ugm.world_model import _is_inert
from ugm.cnl.rewriter import match as engine_match, graded_degree
from ugm import to_attrgraph, lower_rule, run_to_fixpoint, derived_triples
from ugm.lowering import lower_lhs, lower_graded, Unlowerable
from ugm.machine import Machine


# ---------------------------------------------------------------------------
# Helpers — build a KB graph, extract relation triples, run both engines
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


def _name_triples(g: h.Graph) -> set[tuple[str, str, str]]:
    """Every relation in a name-`Graph` as (subj, rel, obj) — the mirror of
    `derived_triples` over the label-less graph, so the two sides are extracted alike."""
    out: set[tuple[str, str, str]] = set()
    for r in g.nodes():
        if _is_inert(g.name(r)):
            continue
        preds = [p for p in g.pred(r) if not _is_inert(g.name(p))]
        succs = [s for s in g.succ(r) if not _is_inert(g.name(s))]
        if not preds or not succs:
            continue
        for p in preds:
            for s in succs:
                out.add((g.name(p), g.name(r), g.name(s)))
    return out


def _engine_derived(g, rule) -> set[tuple[str, str, str]]:
    init = _name_triples(g)
    h.run(g, [rule], provenance=False)
    return _name_triples(g) - init


def _machine_derived(g, rule) -> set[tuple[str, str, str]]:
    ag, _ = to_attrgraph(g)
    init = derived_triples(ag)
    program = lower_rule(rule)
    run_to_fixpoint(ag, program, rule.bound_names())
    return derived_triples(ag) - init


def _assert_agree_graph(g, rule):
    # each side gets its own fresh copy of the graph (run mutates in place)
    eng = _engine_derived(g.copy(), rule)
    mac = _machine_derived(g.copy(), rule)
    assert eng == mac, f"engine {sorted(eng)} != machine {sorted(mac)}"
    return eng


def _assert_agree(facts, rule):
    return _assert_agree_graph(_build(facts), rule)


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
    derived = _assert_agree(facts, CAN_GET)
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
    derived = _assert_agree(facts, TRANS)
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
    derived = _assert_agree(facts, HAZARD)
    assert ("loop", "hazard", "del") in derived


def test_four_clause_join_near_miss_agrees():
    facts = _HAZARD_FACTS + [("del", "mutate", "other")]  # mutates a DIFFERENT collection
    derived = _assert_agree(facts, HAZARD)
    assert not any(t[1] == "hazard" for t in derived)     # both engines derive nothing


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

    # engine: structural bindings that PASS the graded α-cut, and their degree
    engine: dict[str, float] = {}
    for b in engine_match(g, FAST.lhs):
        deg = graded_degree(g, FAST, b)
        if deg is not None:
            engine[g.name(b["?c"])] = deg

    # machine: the lowered program's match phase (structure + GRADE), score per surviving state
    ag, _ = to_attrgraph(g)
    match_ops = lower_lhs(FAST) + lower_graded(FAST)
    machine: dict[str, float] = {}
    for st in Machine().match(ag, match_ops):
        name = ag.get_attr(st.regs["?c"], "name").value
        machine[name] = st.score

    assert set(engine) == {"alice"}                       # only alice clears the cut...
    assert set(engine) == set(machine)                    # ...in BOTH engines
    for name, deg in engine.items():
        assert machine[name] == pytest.approx(deg)        # and the degree matches


def test_graded_rule_derivation_agrees():
    # end-to-end: the derived relation SET agrees (the α-cut gates which fire)
    derived = _assert_agree_graph(_graded_graph(), FAST)
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

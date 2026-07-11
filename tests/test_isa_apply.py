"""
Phase 4.2 — APPLY firmware v0 (`harneskills/isa/apply.py`).

APPLY matches a REIFIED rule (the Phase-3.1 in-graph shape, `write_rule`) against the facts and
EMITs its head, holding the binding environment as a VISIBLE `<frame>` control node rather than a
hidden Python dict. These tests DIFFERENTIALLY GATE it against `run_bank` (the forward ISA engine
over the Python `Rule`): for a positive rule, APPLY over the reified form must derive EXACTLY the
facts `run_bank` derives over the object form — the swap-safety correspondence the firmware owes.
"""
import ugm as h
from ugm import AttrGraph, run_bank, derived_triples, apply_rule, apply_to_fixpoint


def _facts(triples) -> AttrGraph:
    """A fresh AttrGraph with each `(s, pred, o)` as a fact relation; entity nodes shared by name."""
    g = AttrGraph()
    ids: dict[str, str] = {}

    def node(name: str) -> str:
        if name not in ids:
            ids[name] = g.add_node(name)
        return ids[name]

    for s, p, o in triples:
        g.add_relation(node(s), p, node(o))
    return g


def _derived(g: AttrGraph, before: set) -> set:
    return derived_triples(g) - before


def _apply_vs_run_bank(rule: h.Rule, facts: list[tuple[str, str, str]]) -> tuple[set, set]:
    """Run `rule` two ways over identical facts — `run_bank` (oracle, Python rule) and
    `apply_to_fixpoint` (reified rule) — and return (oracle_derived, apply_derived)."""
    # oracle
    g1 = _facts(facts)
    base1 = derived_triples(g1)
    run_bank(g1, [rule])
    oracle = _derived(g1, base1)

    # APPLY over the reified rule
    g2 = _facts(facts)
    base2 = derived_triples(g2)
    rg = AttrGraph()
    rule_node = h.write_rule(rg, rule)
    apply_to_fixpoint(g2, rg, rule_node)
    got = _derived(g2, base2)
    return oracle, got


def test_apply_single_atom_body_matches_run_bank():
    rule = h.Rule(key="mortal", lhs=[h.Pat("?x", "is_a", "person")],
                  rhs=[h.Pat("?x", "is_a", "mortal")])
    oracle, got = _apply_vs_run_bank(rule, [("paul", "is_a", "person"),
                                            ("socrates", "is_a", "person"),
                                            ("rex", "is_a", "dog")])
    assert got == oracle
    assert ("paul", "is_a", "mortal") in got and ("socrates", "is_a", "mortal") in got
    assert ("rex", "is_a", "mortal") not in got            # rex is a dog, not a person


def test_apply_two_atom_join_matches_run_bank():
    # ?g is satisfied when it targets ?x whose type ?y matches: a 3-way join with shared vars.
    rule = h.Rule(key="goal.sat",
                  lhs=[h.Pat("?g", "target", "?x"), h.Pat("?g", "type", "?y"),
                       h.Pat("?x", "is_a", "?y")],
                  rhs=[h.Pat("?g", "is", "satisfied")])
    oracle, got = _apply_vs_run_bank(rule, [("goalA", "target", "paul"), ("goalA", "type", "mortal"),
                                            ("paul", "is_a", "mortal"),
                                            ("goalB", "target", "rex"), ("goalB", "type", "mortal"),
                                            ("rex", "is_a", "dog")])
    assert got == oracle
    assert ("goalA", "is", "satisfied") in got
    assert ("goalB", "is", "satisfied") not in got          # rex is a dog, type mismatch


def test_apply_transitivity_recursion_matches_run_bank():
    # Recursion via the fixpoint wrapper; check-before-derive terminates it (no idempotency NAC).
    rule = h.Rule(key="is_a.transitive",
                  lhs=[h.Pat("?a", "is_a", "?b"), h.Pat("?b", "is_a", "?c")],
                  rhs=[h.Pat("?a", "is_a", "?c")])
    oracle, got = _apply_vs_run_bank(rule, [("alice", "is_a", "ordering_customer"),
                                            ("ordering_customer", "is_a", "customer"),
                                            ("customer", "is_a", "party")])
    assert got == oracle
    # full transitive closure derived
    assert ("alice", "is_a", "customer") in got
    assert ("alice", "is_a", "party") in got
    assert ("ordering_customer", "is_a", "party") in got


def test_apply_near_miss_derives_nothing_like_run_bank():
    rule = h.Rule(key="mortal", lhs=[h.Pat("?x", "is_a", "person")],
                  rhs=[h.Pat("?x", "is_a", "mortal")])
    oracle, got = _apply_vs_run_bank(rule, [("rex", "is_a", "dog")])
    assert got == oracle == set()


# --- the firmware thesis: the binding environment is VISIBLE graph structure ---------------------

def test_apply_binding_is_a_visible_frame_relation():
    # During a match a partial binding is `<frame> -[?var]-> node`, an inspectable control relation,
    # not a hidden dict. Exercised via the internal helpers (the driver GCs frames after a full pass).
    from ugm.apply import _extend_frame, _bindings, FRAME
    g = _facts([("paul", "is_a", "person")])
    paul = g.nodes_named("paul")[0]
    created: list[str] = []
    empty = _extend_frame(g, None, {}, created)
    fr = _extend_frame(g, empty, {"?x": paul}, created)
    assert g.is_control(fr)                                 # the frame is control-layer scaffolding
    assert _bindings(g, fr) == {"?x": paul}                # ... and the binding is a real relation
    # the binding is a genuine reified edge `<frame> -[?x]-> paul`, visible to any reader
    assert any(g.has_key(rel, "?x") and obj == paul for rel, obj in g.relations_from(fr))


def test_body_atom_cursor_is_a_visible_itinerary_that_advances():
    # The body-atom cursor is graph structure (`<current-atom>` over a df-sorted `next`-chain), not a
    # hidden Python loop index: the current atom is READABLE, and advancing follows `next` in-graph.
    from ugm.apply import (
        _build_itinerary, _cursor_atom, _advance_cursor, CURRENT_ATOM, ATOM_STEP,
    )
    g = _facts([("paul", "is_a", "person")])
    body = [("?g", "target", "?x"), ("?x", "is_a", "?y")]
    created: list[str] = []
    cur = _build_itinerary(g, body, created)

    assert g.nodes_named(CURRENT_ATOM) == [cur] and g.is_control(cur)   # a visible control cursor
    assert len(g.nodes_named(ATOM_STEP)) == 2                            # one step per body atom
    assert _cursor_atom(g, cur) == ("?g", "target", "?x")               # starts at the first atom
    assert _advance_cursor(g, cur, created) == ("?x", "is_a", "?y")     # ... and follows `next`
    assert _advance_cursor(g, cur, created) is None                     # ... to exhaustion

    for n in created:                                                   # the itinerary is ephemeral
        if g.has(n):
            g.remove_node(n)
    assert g.nodes_named(CURRENT_ATOM) == [] and g.nodes_named(ATOM_STEP) == []


# --- Phase 4.1: semi-naive `<fresh>` delta -------------------------------------------------------

def test_fresh_delta_atom_is_marked_visible_on_the_itinerary():
    # In a semi-naive round one body atom draws only from the previous round's delta; that atom is
    # marked `<fresh>` on the itinerary — the semi-naive delta position as visible graph structure.
    from ugm.apply import _build_itinerary, _cursor_is_fresh, _advance_cursor
    g = _facts([("a", "is_a", "b")])
    body = [("?a", "is_a", "?b"), ("?b", "is_a", "?c")]
    created: list[str] = []
    cur = _build_itinerary(g, body, created, delta_pos=1)               # 2nd atom is the delta atom
    assert not _cursor_is_fresh(g, cur)                                 # atom 0 is full
    _advance_cursor(g, cur, created)
    assert _cursor_is_fresh(g, cur)                                     # atom 1 draws from the delta
    for n in created:
        if g.has(n):
            g.remove_node(n)


def test_semi_naive_fixpoint_derives_the_full_transitive_closure_over_many_rounds():
    # A long chain forces several delta rounds; semi-naive must still derive the FULL closure and
    # match run_bank exactly (each round joins only against the frontier, but nothing is missed).
    chain_facts = [(f"n{i}", "is_a", f"n{i+1}") for i in range(8)]
    rule = h.Rule(key="is_a.transitive",
                  lhs=[h.Pat("?a", "is_a", "?b"), h.Pat("?b", "is_a", "?c")],
                  rhs=[h.Pat("?a", "is_a", "?c")])
    oracle, got = _apply_vs_run_bank(rule, chain_facts)
    assert got == oracle
    # every DERIVED pair n{i} -> n{j} (distance >= 2; the base 1-step facts aren't "derived") is present
    assert all((f"n{i}", "is_a", f"n{j}") in got for i in range(9) for j in range(i + 2, 9))

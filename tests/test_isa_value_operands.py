"""
ISA VALUE OPERANDS (docs/isa_value_operands_design.md §7 steps 1-2) — the substrate + the differential
gate for pointer-carried demand endpoints.

Step 1 (substrate): a data value an operand needs is a REGULAR node interned per distinct value under
`<isa_operand_value>` (`AttrGraph.value_node`). No name, no flag, no relations — invisible to fact
reads by construction (attribute + use, never a privileged kind).

Step 2 (the (X) enabler): with `chain._VALUE_OPERANDS` on, every NAME endpoint the demand solver
carries (goal, env binding, sub-demand, NAC goal) is a POINTER to its value-node, and the consuming
helpers interpret the pointer back (resolve/match/write by the carried value). Behaviour must be
IDENTICAL to the default name path — every scenario here runs FLAG OFF (the oracle) then FLAG ON and
asserts the same derivations, the same `<demand>` trace, the same verdicts. The A1 walk/ISA
cross-check (`chain._CROSSCHECK`) is ALSO on during both runs, so the two matchers' parity is asserted
under pointer endpoints too. The production swap (flag default True) is the user's ratified gate.
"""
import pytest

import ugm as h
from ugm import (AttrGraph, Pat, Rule, ValueMatch, GradedCondition, chain_sip, check, suppose,
                 derived_triples, render_demands, write_rule, POSITIVE, ASSUMED_NO)
from ugm import chain
from ugm.attrgraph import ISA_OPERAND_VALUE, graded
from ugm.chain import ById, _facts_matching


# --- helpers ---------------------------------------------------------------------------------------

def _facts(triples) -> AttrGraph:
    g = AttrGraph()
    ids: dict[str, str] = {}

    def node(name: str) -> str:
        if name not in ids:
            ids[name] = g.add_node(name)
        return ids[name]

    for s, p, o in triples:
        g.add_relation(node(s), p, node(o))
    return g


def _reify(rules) -> AttrGraph:
    rg = AttrGraph()
    for r in rules:
        h.write_rule(rg, r)
    return rg


def _run_both(scenario):
    """Run `scenario` (a fresh-build + run -> comparable outcome) with `_VALUE_OPERANDS` OFF then ON;
    the name path is the oracle, so the two outcomes must be identical. `_CROSSCHECK` is on for both
    runs (walk/ISA matcher parity under both endpoint representations). Returns the flag-on outcome."""
    outs = []
    for flag in (False, True):
        prev_v, prev_c = chain._VALUE_OPERANDS, chain._CROSSCHECK
        chain._VALUE_OPERANDS, chain._CROSSCHECK = flag, True
        try:
            outs.append(scenario())
        finally:
            chain._VALUE_OPERANDS, chain._CROSSCHECK = prev_v, prev_c
    assert outs[0] == outs[1], (
        f"value-operand divergence:\n  name path = {outs[0]!r}\n  ptr path  = {outs[1]!r}")
    return outs[1]


def _snapshot(fact_g, rule_g):
    """The comparable outcome of a demand run: every derived fact + the rendered `<demand>` trace
    (which must stringify identically — a value-node pointer records its VALUE, not its node id)."""
    return (sorted(derived_triples(fact_g)), sorted(render_demands(rule_g)))


# --- step 1: the value-node substrate --------------------------------------------------------------

def test_value_node_is_interned_per_distinct_value():
    g = AttrGraph()
    v1 = g.value_node("ada")
    assert g.value_node("ada") == v1                     # get-or-create: one node per value
    assert g.value_node("bo") != v1                      # distinct values, distinct nodes
    assert g.operand_value(v1) == "ada"                  # the read half of the convention
    assert g.operand_value(g.add_node("ada")) is None    # an ENTITY named ada is not a value-node


def test_value_node_is_a_regular_unflagged_node():
    g = AttrGraph()
    v = g.value_node("ada")
    assert not g.is_control(v) and not g.is_inert(v)     # no kind, no flag — attribute + use only
    assert g.name(v) == ""                               # carries no NAME ...
    assert v not in g.nodes_named("ada")                 # ... so the name accelerator never returns it


def test_value_node_is_invisible_to_fact_reads():
    g = _facts([("ada", "knows", "bo")])
    before_triples = sorted(derived_triples(g))
    before_read = _facts_matching(g, "knows", "ada", None)
    g.value_node("ada")                                  # intern the subject's value ...
    g.value_node("knows")                                # ... and even the predicate's
    assert sorted(derived_triples(g)) == before_triples  # no new fact appears
    assert _facts_matching(g, "knows", "ada", None) == before_read


# --- step 2: pointer-carried endpoints are behaviour-identical (the differential gate) -------------

def test_transitive_join_bound_subject_parity():
    """Multi-atom SIP join under partial envs: bound subj, free slots, recursive rule."""
    def scenario():
        facts = _facts([("a", "edge", "b"), ("b", "edge", "c"), ("c", "edge", "d")])
        rules = _reify([
            Rule(key="reach.base", lhs=[Pat("?x", "edge", "?y")], rhs=[Pat("?x", "reach", "?y")]),
            Rule(key="reach.step", lhs=[Pat("?x", "edge", "?y"), Pat("?y", "reach", "?z")],
                 rhs=[Pat("?x", "reach", "?z")]),
        ])
        n = chain_sip(facts, rules, ("reach", "a", None))
        return (n, *_snapshot(facts, rules))

    n, triples, _demands = _run_both(scenario)
    assert {o for (s, p, o) in triples if p == "reach" and s == "a"} == {"b", "c", "d"}


def test_literal_body_endpoints_parity():
    """A body atom with LITERAL endpoints: under the flag the literal's name becomes its value-node
    pointer, the matcher echoes the pointer back, and `_bind`'s literal branch must still unify."""
    def scenario():
        facts = _facts([("ada", "in", "library"), ("bo", "in", "kitchen"),
                        ("library", "is", "quiet")])
        rules = _reify([
            Rule(key="reader", lhs=[Pat("?x", "in", "library"), Pat("library", "is", "quiet")],
                 rhs=[Pat("?x", "is", "reader")]),
        ])
        n = chain_sip(facts, rules, ("is", None, "reader"))
        return (n, *_snapshot(facts, rules))

    _n, triples, _d = _run_both(scenario)
    assert ("ada", "is", "reader") in triples and ("bo", "is", "reader") not in triples


def test_naf_nested_negative_parity():
    """NAC goals are carried endpoints too (`_nac_blocks` converts them): the thief bank's nested
    negative closures + `check` verdicts must be identical under pointers."""
    def scenario():
        facts = _facts([("ada", "is_a", "suspect"), ("bo", "is_a", "suspect"),
                        ("cy", "is_a", "suspect"), ("bo", "in", "library"),
                        ("ada", "is", "alibied")])
        rules = _reify([
            Rule(key="innocent", lhs=[Pat("?x", "in", "library")], rhs=[Pat("?x", "is", "innocent")]),
            Rule(key="cleared.innocent", lhs=[Pat("?x", "is", "innocent")],
                 rhs=[Pat("?x", "is", "cleared")]),
            Rule(key="cleared.alibi", lhs=[Pat("?x", "is", "alibied")],
                 rhs=[Pat("?x", "is", "cleared")]),
            Rule(key="thief", lhs=[Pat("?x", "is_a", "suspect")],
                 nac=[Pat("?x", "is", "cleared")], rhs=[Pat("?x", "is", "thief")]),
        ])
        verdicts = tuple(check(facts, rules, ("is", s, "thief")) for s in ("ada", "bo", "cy"))
        return (verdicts, *_snapshot(facts, rules))

    verdicts, _t, _d = _run_both(scenario)
    assert verdicts == (ASSUMED_NO, ASSUMED_NO, POSITIVE)


def test_graded_alpha_cut_parity():
    """`_graded_ok` aggregates max-over-mentions through `_bound_entity_nodes` — the coref-class
    aggregate a pointer must preserve (the §3 no-fork/no-collapse claim)."""
    def scenario():
        facts = AttrGraph()
        urgent = facts.add_node("leak", embedding={"urgency": 0.9})
        mild = facts.add_node("drip", embedding={"urgency": 0.2})
        facts.add_relation(urgent, "is_a", facts.add_node("issue"))
        facts.add_relation(mild, "is_a", facts.add_node("issue"))
        rules = _reify([
            Rule(key="escalate", lhs=[Pat("?c", "is_a", "issue")],
                 rhs=[Pat("?c", "needs", "attention")],
                 graded=[GradedCondition("?c", {"urgency": 1.0}, 0.5)]),
        ])
        n = chain_sip(facts, rules, ("needs", None, "attention"))
        return (n, *_snapshot(facts, rules))

    _n, triples, _d = _run_both(scenario)
    assert ("leak", "needs", "attention") in triples
    assert ("drip", "needs", "attention") not in triples


def test_value_match_join_parity():
    """`_value_matches_ok` reads endpoint attributes through the same pointer interpretation."""
    def scenario():
        facts = AttrGraph()
        for name, w in (("morningstar", 0.90), ("eveningstar", 0.88), ("pluto", 0.10)):
            n = facts.add_node(name)
            facts.add_relation(n, "is_a", facts.add_node("body"))
            facts.set_attr(n, "warmth", graded(w))
        rules = _reify([
            Rule(key="coref_warm", lhs=[Pat("?x", "is_a", "body"), Pat("?y", "is_a", "body")],
                 rhs=[Pat("?x", "same_as", "?y")],
                 value_matches=[ValueMatch("?x", "?y", "warmth", threshold=0.9)]),
        ])
        n = chain_sip(facts, rules, ("same_as", "morningstar", None))
        return (n, *_snapshot(facts, rules))

    _n, triples, _d = _run_both(scenario)
    pairs = {(s, o) for s, p, o in triples if p == "same_as"}
    assert ("morningstar", "eveningstar") in pairs and ("morningstar", "pluto") not in pairs


def test_skolem_minting_and_refinding_parity():
    """Bound-literal head skolems: `_resolve_skolems`/`_find_skolem_witness` re-find the minted node
    through `_anchor_node` -> `_bound_entity_nodes` (pointer-aware), so the closure still converges
    on ONE skolem per firing instead of re-minting each round."""
    def scenario():
        facts = _facts([("p1", "is_a", "state"), ("p2", "is_a", "state")])
        rules = _reify([
            Rule(key="succ", lhs=[Pat("?p", "is_a", "state")],
                 rhs=[Pat("?p", "has_succ", "s2?"), Pat("s2?", "succ_of", "?p")]),
        ])
        n = chain_sip(facts, rules, ("has_succ", "p1", None))
        return (n, *_snapshot(facts, rules))

    _n, triples, _d = _run_both(scenario)
    assert sum(1 for s, p, o in triples if s == "p1" and p == "has_succ") == 1


def test_suppose_scope_pencil_parity():
    """SUPPOSE runs the chain inside a scope: pencil EMITs + in-scope reads under pointer endpoints."""
    def scenario():
        facts = _facts([("ada", "is", "person")])
        rules = _reify([
            Rule(key="mortal", lhs=[Pat("?x", "is", "person")], rhs=[Pat("?x", "is", "mortal")]),
        ])
        res = suppose(facts, rules,
                      assumptions=[("bo", "is", "person")],
                      predictions=[("bo", "is", "mortal")])
        return (res.status, sorted(derived_triples(facts)))

    status, _t = _run_both(scenario)                     # the PARITY is the assertion here
    assert status in ("confirmed", "inconclusive", "refuted")


def test_focus_scope_parity():
    def scenario():
        facts = _facts([("ada", "knows", "bo"), ("cy", "knows", "dee"), ("bo", "knows", "ada")])
        rules = _reify([Rule(key="ack", lhs=[Pat("?x", "knows", "?y")],
                             rhs=[Pat("?x", "ack", "?y")])])
        n = chain_sip(facts, rules, ("ack", "ada", None), focus_scope=frozenset({"ada", "bo"}))
        return (n, *_snapshot(facts, rules))

    _run_both(scenario)


def test_byid_entity_pin_passes_through_parity():
    """A genuine entity `ById` goal endpoint is NOT a value pointer: it must still PIN to exactly its
    node under the flag (deterministic ids make the two builds comparable)."""
    def scenario():
        facts = AttrGraph()
        ada1 = facts.add_node("ada")
        facts.add_node("ada")                            # a distinct same-named entity (no facts)
        bo = facts.add_node("bo")
        facts.add_relation(ada1, "knows", bo)
        rules = _reify([Rule(key="ack", lhs=[Pat("?x", "knows", "?y")],
                             rhs=[Pat("?x", "ack", "?y")])])
        n = chain_sip(facts, rules, ("ack", ById(ada1), None))
        return (n, ada1, *_snapshot(facts, rules))

    n, _ada1, triples, _d = _run_both(scenario)
    assert n == 1 and ("ada", "ack", "bo") in triples


def test_provenance_journaling_parity():
    """RECORD (mode 9) resolves body endpoints from the env via `_node_for_name` — pointer-aware."""
    def scenario():
        facts = _facts([("ada", "knows", "bo")])
        rules = _reify([Rule(key="ack", lhs=[Pat("?x", "knows", "?y")],
                             rhs=[Pat("?x", "ack", "?y")])])
        n = chain_sip(facts, rules, ("ack", "ada", None), provenance=True)
        return (n, *_snapshot(facts, rules))

    _run_both(scenario)


# --- the pointer claim itself (not just parity) ----------------------------------------------------

def test_flag_on_the_solver_carries_only_pointers(monkeypatch):
    """The step-2 claim: with the flag on, NO bare name string reaches `_facts_matching` from the
    solver — every bound endpoint is a node-pointer (`ById`), value-node or entity."""
    facts = _facts([("ada", "in", "library"), ("library", "is", "quiet")])
    rules = _reify([
        Rule(key="reader", lhs=[Pat("?x", "in", "library"), Pat("library", "is", "quiet")],
             rhs=[Pat("?x", "is", "reader")]),
    ])
    seen: list[tuple] = []
    real = chain._facts_matching

    def spy(fact_g, pred, subj, obj, **kw):
        seen.append((pred, subj, obj))
        return real(fact_g, pred, subj, obj, **kw)

    monkeypatch.setattr(chain, "_facts_matching", spy)
    monkeypatch.setattr(chain, "_VALUE_OPERANDS", True)
    chain_sip(facts, rules, ("is", "ada", "reader"))
    assert seen, "the spy saw no lookups — the scenario did not exercise the solver"
    for pred, subj, obj in seen:
        for ep in (subj, obj):
            assert ep is None or isinstance(ep, ById), (
                f"bare endpoint {ep!r} carried for ({pred}, {subj!r}, {obj!r})")


def test_flag_on_emits_land_on_entities_never_on_value_nodes():
    """The write discipline: a derived fact's endpoints are ENTITY nodes; the value-nodes stay bare
    operand data — no name, no relations — even after a full demand run."""
    facts = _facts([("a", "edge", "b")])
    rules = _reify([Rule(key="reach", lhs=[Pat("?x", "edge", "?y")], rhs=[Pat("?x", "reach", "?y")])])
    prev = chain._VALUE_OPERANDS
    chain._VALUE_OPERANDS = True
    try:
        chain_sip(facts, rules, ("reach", "a", None))
    finally:
        chain._VALUE_OPERANDS = prev
    assert ("a", "reach", "b") in derived_triples(facts)
    vnodes = facts.nodes_with_key(ISA_OPERAND_VALUE)
    assert vnodes, "the run should have interned value-nodes"
    for v in vnodes:
        assert facts.name(v) == ""                       # still nameless ...
        assert not facts.succ(v) and not facts.pred(v)   # ... and still relation-free (pure operand)


def test_flag_on_demand_trace_records_values_not_node_ids():
    """The `<demand>` trace (the negative's explanation) must read exactly as the name path's: a
    value-node pointer stringifies to its VALUE."""
    facts = _facts([("ada", "knows", "bo")])
    rules = _reify([Rule(key="ack", lhs=[Pat("?x", "knows", "?y")], rhs=[Pat("?x", "ack", "?y")])])
    prev = chain._VALUE_OPERANDS
    chain._VALUE_OPERANDS = True
    try:
        chain_sip(facts, rules, ("ack", "ada", None))
    finally:
        chain._VALUE_OPERANDS = prev
    assert "ada ack anyone" in render_demands(rules)

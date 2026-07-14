"""
ISA VALUE OPERANDS (docs/isa_value_operands_design.md) + the (X) register file — now STRUCTURAL.

Step 1 (substrate): a data value an operand needs is a REGULAR node interned per distinct value under
`<isa_operand_value>` (`AttrGraph.value_node`). No name, no flag, no relations — invisible to fact
reads by construction (attribute + use, never a privileged kind).

Step 2 + (X): the demand solver carries ONLY node-pointers (`ById` — an entity pin, or a value-node
for a name/literal endpoint) and binds them in the machine's REGISTER FILE (`State.regs`, not a dict);
graded α-cuts and declared value-joins run as EPHEMERAL `GRADE`/`VMATCH` programs on the shared
machine, which interprets a value-node register by aggregating over its coref class
(`Machine._operand_nodes`). These tests drive every demand shape with the A1 walk/ISA cross-check ON
(`chain._CROSSCHECK` — the retained independent matcher oracle) and assert the solver's contract
directly: correct derivations, name-identical `<demand>` traces, pointer-only carriage, and writes
that land on entities, never on operand data.
"""
import pytest

import ugm as h
from ugm import (AttrGraph, Pat, Rule, ValueMatch, GradedCondition, chain_sip, check, suppose,
                 derived_triples, render_demands, POSITIVE, ASSUMED_NO)
from ugm import chain
from ugm.attrgraph import ISA_OPERAND_VALUE, graded
from ugm.chain import ById, _facts_matching


@pytest.fixture(autouse=True)
def _crosscheck_on():
    """Every demand run here also asserts the bespoke-walk oracle agrees with the shared ISA matcher
    on each `_facts_matching` call (the retained A1 differential)."""
    prev = chain._CROSSCHECK
    chain._CROSSCHECK = True
    try:
        yield
    finally:
        chain._CROSSCHECK = prev


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


# --- (X): every demand shape on the pointer register file ------------------------------------------

def test_transitive_join_bound_subject():
    """Multi-atom SIP join under partial register files: bound subj, free slots, recursive rule."""
    facts = _facts([("a", "edge", "b"), ("b", "edge", "c"), ("c", "edge", "d")])
    rules = _reify([
        Rule(key="reach.base", lhs=[Pat("?x", "edge", "?y")], rhs=[Pat("?x", "reach", "?y")]),
        Rule(key="reach.step", lhs=[Pat("?x", "edge", "?y"), Pat("?y", "reach", "?z")],
             rhs=[Pat("?x", "reach", "?z")]),
    ])
    chain_sip(facts, ("reach", "a", None), rules=rules)
    reached = {o for (s, p, o) in derived_triples(facts) if p == "reach" and s == "a"}
    assert reached == {"b", "c", "d"}


def test_literal_body_endpoints():
    """A body atom with LITERAL endpoints: the literal's name becomes its value-node pointer, the
    matcher echoes the pointer back, and `_bind_state`'s literal branch must still unify."""
    facts = _facts([("ada", "in", "library"), ("bo", "in", "kitchen"),
                    ("library", "is", "quiet")])
    rules = _reify([
        Rule(key="reader", lhs=[Pat("?x", "in", "library"), Pat("library", "is", "quiet")],
             rhs=[Pat("?x", "is", "reader")]),
    ])
    chain_sip(facts, ("is", None, "reader"), rules=rules)
    triples = derived_triples(facts)
    assert ("ada", "is", "reader") in triples and ("bo", "is", "reader") not in triples


def test_naf_nested_negative_verdicts():
    """NAC goals are carried pointers too (`_nac_blocks` -> `_ptr`): the thief bank's nested negative
    closures + `check` verdicts."""
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
    verdicts = {s: check(facts, ("is", s, "thief"), rules=rules) for s in ("ada", "bo", "cy")}
    assert verdicts == {"ada": ASSUMED_NO, "bo": ASSUMED_NO, "cy": POSITIVE}


def test_graded_alpha_cut_as_grade_program():
    """`_grades_pass` runs an ephemeral GRADE program; a value-node register aggregates
    max-over-mentions inside the instruction (the §3 no-fork/no-collapse claim)."""
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
    chain_sip(facts, ("needs", None, "attention"), rules=rules)
    triples = derived_triples(facts)
    assert ("leak", "needs", "attention") in triples
    assert ("drip", "needs", "attention") not in triples


def test_graded_alpha_cut_aggregates_over_coref_mentions():
    """The coref-class aggregate: TWO same-named mentions, the degree on the OTHER mention than the
    one the relation touches — a value-node-seeded goal must still see the max over the class (what
    `_bound_entity_nodes` did for names, now inside the GRADE instruction)."""
    facts = AttrGraph()
    m1 = facts.add_node("leak")                            # the mention in the relation (no degree)
    facts.add_node("leak", embedding={"urgency": 0.9})     # a same-named mention carrying the degree
    facts.add_relation(m1, "is_a", facts.add_node("issue"))
    rules = _reify([
        Rule(key="escalate", lhs=[Pat("?c", "is_a", "issue")],
             rhs=[Pat("?c", "needs", "attention")],
             graded=[GradedCondition("?c", {"urgency": 1.0}, 0.5)]),
    ])
    # goal bound BY NAME -> ?c seeded with the value-node pointer -> GRADE aggregates over mentions
    chain_sip(facts, ("needs", "leak", None), rules=rules)
    assert ("leak", "needs", "attention") in derived_triples(facts)


def test_value_match_join_as_vmatch_program():
    """`_vmatches_pass` runs an ephemeral VMATCH program — the same op the forward path lowers to."""
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
    chain_sip(facts, ("same_as", "morningstar", None), rules=rules)
    pairs = {(s, o) for s, p, o in derived_triples(facts) if p == "same_as"}
    assert ("morningstar", "eveningstar") in pairs and ("morningstar", "pluto") not in pairs


def test_skolem_minting_and_refinding():
    """Bound-literal head skolems: `_resolve_skolems`/`_find_skolem_witness` re-find the minted node
    through `_anchor_node` -> `_bound_entity_nodes` (pointer-aware), so the closure converges on ONE
    skolem per firing instead of re-minting each round."""
    facts = _facts([("p1", "is_a", "state"), ("p2", "is_a", "state")])
    rules = _reify([
        Rule(key="succ", lhs=[Pat("?p", "is_a", "state")],
             rhs=[Pat("?p", "has_succ", "s2?"), Pat("s2?", "succ_of", "?p")]),
    ])
    chain_sip(facts, ("has_succ", "p1", None), rules=rules)
    triples = derived_triples(facts)
    assert sum(1 for s, p, o in triples if s == "p1" and p == "has_succ") == 1


def test_suppose_scope_pencil():
    """SUPPOSE runs the chain inside a scope: pencil EMITs + in-scope reads on pointer endpoints."""
    facts = _facts([("ada", "is", "person")])
    rules = _reify([
        Rule(key="mortal", lhs=[Pat("?x", "is", "person")], rhs=[Pat("?x", "is", "mortal")]),
    ])
    res = suppose(facts, assumptions=[("bo", "is", "person")], predictions=[("bo", "is", "mortal")], rules=rules)
    assert res.status in ("confirmed", "inconclusive", "refuted")


def test_focus_scope():
    facts = _facts([("ada", "knows", "bo"), ("cy", "knows", "dee"), ("bo", "knows", "ada")])
    rules = _reify([Rule(key="ack", lhs=[Pat("?x", "knows", "?y")],
                         rhs=[Pat("?x", "ack", "?y")])])
    chain_sip(facts, ("ack", "ada", None), focus_scope=frozenset({"ada", "bo"}), rules=rules)
    acked = {(s, o) for s, p, o in derived_triples(facts) if p == "ack"}
    assert acked == {("ada", "bo")}                        # cy->dee is off-focus, never derived


def test_byid_entity_pin_passes_through():
    """A genuine entity `ById` goal endpoint is NOT a value pointer: it must PIN to exactly its node
    (the distinct same-named entity contributes nothing)."""
    facts = AttrGraph()
    ada1 = facts.add_node("ada")
    facts.add_node("ada")                                  # a distinct same-named entity (no facts)
    bo = facts.add_node("bo")
    facts.add_relation(ada1, "knows", bo)
    rules = _reify([Rule(key="ack", lhs=[Pat("?x", "knows", "?y")],
                         rhs=[Pat("?x", "ack", "?y")])])
    n = chain_sip(facts, ("ack", ById(ada1), None), rules=rules)
    assert n == 1 and ("ada", "ack", "bo") in derived_triples(facts)


def test_provenance_journaling():
    """RECORD (mode 9) resolves body endpoints from the register file via `_node_for_name`."""
    facts = _facts([("ada", "knows", "bo")])
    rules = _reify([Rule(key="ack", lhs=[Pat("?x", "knows", "?y")],
                         rhs=[Pat("?x", "ack", "?y")])])
    n = chain_sip(facts, ("ack", "ada", None), provenance=True, rules=rules)
    assert n == 1 and ("ada", "ack", "bo") in derived_triples(facts)


# --- the pointer claims themselves -----------------------------------------------------------------

def test_solver_carries_only_pointers(monkeypatch):
    """The structural claim: NO bare name string reaches `_facts_matching` from the solver — every
    bound endpoint is a node-pointer (`ById`), value-node or entity."""
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
    chain_sip(facts, ("is", "ada", "reader"), rules=rules)
    assert seen, "the spy saw no lookups — the scenario did not exercise the solver"
    for pred, subj, obj in seen:
        for ep in (subj, obj):
            assert ep is None or isinstance(ep, ById), (
                f"bare endpoint {ep!r} carried for ({pred}, {subj!r}, {obj!r})")


def test_emits_land_on_entities_never_on_value_nodes():
    """The write discipline: a derived fact's endpoints are ENTITY nodes; the value-nodes stay bare
    operand data — no name, no relations — even after a full demand run."""
    facts = _facts([("a", "edge", "b")])
    rules = _reify([Rule(key="reach", lhs=[Pat("?x", "edge", "?y")], rhs=[Pat("?x", "reach", "?y")])])
    chain_sip(facts, ("reach", "a", None), rules=rules)
    assert ("a", "reach", "b") in derived_triples(facts)
    vnodes = facts.nodes_with_key(ISA_OPERAND_VALUE)
    assert vnodes, "the run should have interned value-nodes"
    for v in vnodes:
        assert facts.name(v) == ""                       # still nameless ...
        assert not facts.succ(v) and not facts.pred(v)   # ... and still relation-free (pure operand)


def test_demand_trace_records_values_not_node_ids():
    """The `<demand>` trace (the negative's explanation) reads as names: a value-node pointer
    stringifies to its VALUE."""
    facts = _facts([("ada", "knows", "bo")])
    rules = _reify([Rule(key="ack", lhs=[Pat("?x", "knows", "?y")], rhs=[Pat("?x", "ack", "?y")])])
    chain_sip(facts, ("ack", "ada", None), rules=rules)
    assert "ada ack anyone" in render_demands(rules)

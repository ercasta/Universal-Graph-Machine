"""
Conformance suite for the reference ISA machine (the cheap experiment,
docs/attic/rule_isa_design.md + isa-reference.md).

Every test is a HAND-WRITTEN instruction sequence over the label-less attribute substrate —
NO rules, no compiler, no `harneskills.rewriter`. This is payoff #3 of the design (a testable
machine/rule boundary): the machine is exercised on its own terms so a machine bug is
diagnosed without any rule involved. When a rule->opcode compiler is built later, its lowering
is differential-tested against this same machine; this suite pins the machine.
"""
import pytest

from ugm import (
    AttrGraph, Attr, GRADED, VALUED,
    SEED, FOLLOW, JOIN, TEST, GRADE, FUZZY, MINT, EMIT, DROP_CTRL, SET, DUP,
    run_program, Machine, ControlEdgeError, derived_triples,
)
from ugm.attrgraph import graded, valued
from ugm.machine import T_PROD, ProgramError


# ---------------------------------------------------------------------------
# Substrate basics — label-less nodes, closed keys, values don't merge identity
# ---------------------------------------------------------------------------

def test_two_nodes_same_value_stay_distinct():
    # The label guard: two people both name="Paul" are DISTINCT nodes (a value is data, not
    # an identity index). A former label-substrate would have merged them.
    g = AttrGraph()
    a = g.add_node({"name": valued("Paul"), "person": graded(1.0)})
    b = g.add_node({"name": valued("Paul"), "person": graded(1.0)})
    assert a != b
    # Seeding is by KEY, and returns BOTH candidates to be tested — never one resolved node.
    assert set(g.nodes_with_key("name")) == {a, b}


def test_closed_schema_rejects_off_schema_key():
    g = AttrGraph(schema={"person", "name"})
    n = g.add_node()
    g.set_attr(n, "person", graded(1.0))            # in schema: fine
    with pytest.raises(KeyError):
        g.set_attr(n, "dog", graded(1.0))           # off schema: closed keys


def test_absorb_merges_under_fresh_ids_without_merging_by_name():
    # `absorb` commits an isolated graph into an accumulator under FRESH identities, preserving
    # attrs + control + edge structure, and NEVER merging by name (label-less: two "Paul"s across
    # the two graphs stay two — coreference is the additive `same_as` step, not this).
    kb = AttrGraph()
    paul0 = kb.add_node({"name": valued("Paul")})
    other = AttrGraph()
    paul1 = other.add_node({"name": valued("Paul")})
    ctrl = other.add_node({"name": valued("<scope>")}, control=True)
    other.add_edge(paul1, ctrl)                      # a fact->control edge to remap

    idmap = kb.absorb(other)

    assert set(idmap) == {paul1, ctrl}              # every source node mapped
    assert idmap[paul1] not in (paul0, paul1)       # FRESH id, not the source's, not a collision
    assert len(kb.nodes_named("Paul")) == 2         # two Pauls: NOT merged by name
    assert kb.node(idmap[ctrl]).control             # control flag preserved
    assert kb.has_edge(idmap[paul1], idmap[ctrl])   # edge remapped onto the new ids
    assert kb.name(idmap[paul1]) == "Paul"          # attrs (name) preserved


# ---------------------------------------------------------------------------
# Phase 2.1 — predicates are graded keys (add_relation, not node names)
# ---------------------------------------------------------------------------

def test_add_relation_predicate_is_a_graded_key_not_just_a_name():
    # decision_attrgraph_rehost Phase 2.1: a relation's predicate is the canonical GRADED key
    # `chase: 1.0` on the rel node — findable via `nodes_with_key`, the blessed df-index, not
    # just the legacy `name` accelerator (kept only as a TEMPORARY bridge for rewriter.py).
    g = AttrGraph()
    a, b = g.add_node("alice"), g.add_node("bob")
    rid = g.add_relation(a, "chase", b)
    assert rid in g.nodes_with_key("chase")
    assert g.key_count("chase") == 1
    attr = g.get_attr(rid, "chase")
    assert attr is not None and attr.kind == GRADED and attr.value == 1.0


def test_add_relation_name_predicate_is_a_graded_key_not_an_entity_name():
    # Phase 2.3 (name_demotion_design.md): a domain predicate literally named "name" (e.g. a CPG
    # `name` property) is now sound. It rides the GRADED key `{name: 1.0}`, distinct in KIND from an
    # entity's VALUED `{name: "Paul"}` — so there is no reserved-key collision (the old bridge's
    # dual-write is gone). The relation reports its predicate via `predicate`, carries no entity name,
    # and is found by KEY, never by `nodes_named`.
    g = AttrGraph()
    a, b = g.add_node("cpg_8"), g.add_node("remove")
    rid = g.add_relation(a, "name", b)
    assert g.predicate(rid) == "name"                 # the predicate rides the graded key
    assert g.name(rid) == ""                           # NOT an entity name (graded, not valued)
    assert rid in g.nodes_with_key("name")             # found by predicate key
    assert g.nodes_named("name") == []                 # never by name — no VALUED `name` on the rel node
    assert ("cpg_8", "name", "remove") in derived_triples(g)


# ---------------------------------------------------------------------------
# Positive matching core — SEED + JOIN (a transitivity-shaped join)
# ---------------------------------------------------------------------------

def _reified_relation(g: AttrGraph, rel_key: str, subj: str, obj: str) -> str:
    """Author an n-ary fact the way MINT would: an event node {rel:1} with role-nodes
    {agent:1}->subj and {patient:1}->obj. Returns the event id."""
    ev = g.add_node({rel_key: graded(1.0)})
    ag = g.add_node({"agent": graded(1.0)})
    pt = g.add_node({"patient": graded(1.0)})
    g.add_edge(ev, ag); g.add_edge(ag, subj)
    g.add_edge(ev, pt); g.add_edge(pt, obj)
    return ev


def test_positive_join_reads_a_reified_relation():
    # Author  chase(fido, cat)  reified, then MATCH "the agent and patient of a chase event".
    g = AttrGraph()
    fido = g.add_node({"dog": graded(1.0)})
    cat = g.add_node({"cat": graded(1.0)})
    _reified_relation(g, "chase", fido, cat)

    program = [
        SEED("ev", "chase"),                          # seed the event
        JOIN("ag", "ev", key="agent"),                # ev -> agent-role
        FOLLOW("subj", "ag"),                         # agent-role -> filler
        JOIN("pt", "ev", key="patient"),              # ev -> patient-role
        FOLLOW("obj", "pt"),                          # patient-role -> filler
        TEST("subj", "dog"),                          # the chaser is a dog
        TEST("obj", "cat"),                           # the chased is a cat
    ]
    states = run_program(g, program)
    assert len(states) == 1
    st = states[0]
    assert st.regs["subj"] == fido
    assert st.regs["obj"] == cat


def test_join_prunes_on_failed_attribute_test():
    g = AttrGraph()
    fido = g.add_node({"dog": graded(1.0)})
    ball = g.add_node({"toy": graded(1.0)})          # not a cat
    _reified_relation(g, "chase", fido, ball)
    program = [
        SEED("ev", "chase"),
        JOIN("pt", "ev", key="patient"),
        FOLLOW("obj", "pt"),
        TEST("obj", "cat"),                          # ball is not a cat -> no match
    ]
    assert run_program(g, program) == []


# ---------------------------------------------------------------------------
# Graded pole — FUZZY/GRADE alpha-cut and t-norm composition down the chain
# ---------------------------------------------------------------------------

def test_graded_alpha_cut_prunes_below_threshold():
    g = AttrGraph()
    g.add_node({"urgent": graded(0.9)})
    g.add_node({"urgent": graded(0.3)})
    states = run_program(g, [FUZZY("c", "urgent", threshold=0.5)])
    assert len(states) == 1                          # only the 0.9 survives the alpha-cut
    assert states[0].score == pytest.approx(0.9)


def test_tnorm_composes_down_the_chain():
    # A chain of two graded reads. Godel (min) keeps the weakest link; Goguen (product)
    # multiplies — both compose DOWN the match chain, which is the FUZZY contract.
    g = AttrGraph()
    n = g.add_node({"urgent": graded(0.8), "vip": graded(0.5)})
    prog = [FUZZY("c", "urgent", 0.1), GRADE("c", "vip", threshold=0.1)]

    min_state = run_program(g, prog)[0]
    assert min_state.score == pytest.approx(0.5)     # min(0.8, 0.5)

    prod_state = Machine(tnorm=T_PROD).run(g, prog)[0]
    assert prod_state.score == pytest.approx(0.4)    # 0.8 * 0.5


# ---------------------------------------------------------------------------
# Valued pole — comparison as data, never an identity index
# ---------------------------------------------------------------------------

def test_valued_comparison_filters():
    g = AttrGraph()
    young = g.add_node({"person": graded(1.0), "age": valued(20)})
    old = g.add_node({"person": graded(1.0), "age": valued(70)})
    # everyone under 30
    states = run_program(g, [SEED("p", "person"), GRADE("p", "age", cmp="<=", value=30)])
    assert {s.regs["p"] for s in states} == {young}
    assert old not in {s.regs["p"] for s in states}


def test_seed_valued_filter_does_not_index_by_value():
    # SEED enumerates by KEY and filters candidates by value; it never resolves "the Paul".
    g = AttrGraph()
    p1 = g.add_node({"name": valued("Paul")})
    p2 = g.add_node({"name": valued("Paul")})
    g.add_node({"name": valued("Mary")})
    states = run_program(g, [SEED("p", "name", cmp="=", value="Paul")])
    assert {s.regs["p"] for s in states} == {p1, p2}   # BOTH Pauls, still distinct nodes


# ---------------------------------------------------------------------------
# MINT — reify a relation (Skolem / chunk head) with edges back to constituents
# ---------------------------------------------------------------------------

def test_mint_reifies_a_chunk_over_retained_constituents():
    # `pursuing is X chasing Y` as a definitional chunk: on a chase event, MINT a {pursuing:1}
    # node with a bare edge back to the RETAINED event (additive — honors §5).
    g = AttrGraph()
    fido = g.add_node({"dog": graded(1.0)})
    cat = g.add_node({"cat": graded(1.0)})
    ev = _reified_relation(g, "chase", fido, cat)

    program = [
        SEED("ev", "chase"),
        MINT("chunk", attrs={"pursuing": graded(1.0)}, edges=["ev"]),
    ]
    states = run_program(g, program)
    chunk = states[0].regs["chunk"]
    assert g.get_attr(chunk, "pursuing") == Attr(GRADED, 1.0)
    assert g.has_edge(chunk, ev)                     # points back at the retained constituent
    assert g.has(ev)                                 # constituent NOT consumed (additive)


# ---------------------------------------------------------------------------
# EMIT — monotone fact write: a degree only ever goes up
# ---------------------------------------------------------------------------

def test_emit_raises_graded_degree_monotonically():
    g = AttrGraph()
    n = g.add_node({"warm": graded(0.4)})
    run_program(g, [SEED("x", "warm"), EMIT("x", "warm", 0.9)])
    assert g.get_attr(n, "warm").value == pytest.approx(0.9)   # raised 0.4 -> 0.9
    # a lower EMIT does NOT lower it (monotone)
    run_program(g, [SEED("x", "warm"), EMIT("x", "warm", 0.2)])
    assert g.get_attr(n, "warm").value == pytest.approx(0.9)


def test_emit_scales_by_match_score():
    # EMIT degree = value (x) score, so a graded match weakens what it derives (product here).
    g = AttrGraph()
    n = g.add_node({"urgent": graded(0.6)})
    Machine(tnorm=T_PROD).run(g, [FUZZY("x", "urgent", 0.1), EMIT("x", "served", 1.0)])
    assert g.get_attr(n, "served").value == pytest.approx(0.6)   # 1.0 * score(0.6)


# ---------------------------------------------------------------------------
# The invariant AS A PROPERTY OF THE OPCODE SET — no opcode deletes a fact edge
# ---------------------------------------------------------------------------

def test_drop_ctrl_deletes_a_control_edge():
    g = AttrGraph()
    tok = g.add_node({"walker": graded(1.0)}, control=True)   # control-layer token
    fact = g.add_node({"place": graded(1.0)})
    g.add_edge(tok, fact)                            # control edge (one endpoint is control)
    run_program(g, [SET("t", tok), SET("f", fact), DROP_CTRL("t", "f")])
    assert not g.has_edge(tok, fact)                 # control edge cut


def test_drop_ctrl_refuses_a_fact_edge():
    # There is NO opcode that deletes a fact edge. DROP_CTRL consults edge_is_fact and refuses,
    # so "ungated fact deletion" is unrepresentable — the vision.md §5 invariant is a property
    # of the instruction set, not a lint pass.
    g = AttrGraph()
    a = g.add_node({"person": graded(1.0)})
    b = g.add_node({"person": graded(1.0)})
    g.add_edge(a, b)                                 # a FACT edge (both endpoints fact-layer)
    with pytest.raises(ControlEdgeError):
        run_program(g, [SET("a", a), SET("b", b), DROP_CTRL("a", "b")])
    assert g.has_edge(a, b)                          # untouched


# ---------------------------------------------------------------------------
# Well-formedness — the match-then-apply discipline
# ---------------------------------------------------------------------------

def test_matching_opcode_after_effect_is_malformed():
    g = AttrGraph()
    g.add_node({"warm": graded(1.0)})
    with pytest.raises(ProgramError):
        run_program(g, [SEED("x", "warm"), EMIT("x", "warm", 1.0), SEED("y", "warm")])


# ---------------------------------------------------------------------------
# the inert fact-read guard — the production forward driver matches only FACTS
# ---------------------------------------------------------------------------

def test_inert_guard_excludes_provenance_from_matching():
    # A provenance node (`uses`) with an edge INTO a fact node must NOT be walked as a fact by a
    # GUARDED program (what `run_bank` lowers on a provenance-carrying graph) — else `FOLLOW ... in`
    # would bind it as a subject, the bug that tripled recognition on a graph carrying
    # justifications. The bare program sees it (the pure reference view); the compiler-emitted
    # guard (`lowering.guard_inert` — the retired `Machine.skip_inert` mode's replacement, firmware
    # §3) drops it after every SEED/FOLLOW bind.
    from ugm.lowering import guard_inert
    g = AttrGraph()
    fact = g.add_node({"name": valued("target")})
    subj = g.add_node({"name": valued("s")})
    prov = g.add_node({"name": valued("uses")}, inert=True)   # provenance-inert (marker attribute)
    g.add_edge(subj, fact)                            # a real fact predecessor
    g.add_edge(prov, fact)                            # a provenance predecessor (must be guarded off)

    prog = [SEED("_r", "name", "=", "target"), FOLLOW("s", "_r", "in")]
    pure = Machine().match(g, prog)
    guarded = Machine().match(g, guard_inert(prog))
    assert sorted(st.regs["s"] for st in pure) == sorted([subj, prov])       # bare: sees both
    assert [st.regs["s"] for st in guarded] == [subj]                        # guarded: fact only

    # a guarded SEED drops an inert candidate outright.
    seeded = Machine().match(g, guard_inert([SEED("x", "name", "=", "uses")]))
    assert seeded == []


# --- Phase 2.2: control TOKENS carried as graded KEYS (name->key dual-write) -------------------

def test_control_token_node_dual_writes_its_token_as_a_graded_key():
    # A reserved control token minted as a NODE (`add_node("<goal>")`) carries BOTH the legacy VALUED
    # name (the oracle bridge) AND its token as a graded KEY — the same dual-write `add_relation` does
    # for control PREDICATES — so `nodes_with_key`/`has_key` can eventually replace `nodes_named`.
    g = AttrGraph()
    tok = g.add_node("<goal>")
    assert g.name(tok) == "<goal>"                       # legacy name retained (bridge)
    assert g.has_key(tok, "<goal>")                      # ... AND the token is a graded key
    assert tok in g.nodes_with_key("<goal>")             # ... reachable via the key index
    assert g.node(tok).attrs["<goal>"].kind == GRADED and g.node(tok).attrs["<goal>"].value == 1.0


def test_ordinary_named_node_gets_no_token_key():
    # Guard: the dual-write is RESERVED to `<…>` tokens — an ordinary entity name must NOT become a
    # graded key (else `nodes_with_key`/the fuzzy view would be polluted by every entity mention).
    g = AttrGraph()
    paul = g.add_node("Paul")
    assert not g.has_key(paul, "Paul")
    assert g.node(paul).embedding == {}


def test_token_key_is_excluded_from_the_embedding_view():
    # The token key is control bookkeeping, not a fuzzy dimension: `embedding` filters `<…>` keys out
    # (like an inert node reports none), so similarity/rendering/`propagate` stay token-free even
    # though the key is present for `has_key`/`nodes_with_key`.
    g = AttrGraph()
    tok = g.add_node("<goal>", embedding={"urgent": 0.8})
    assert g.node(tok).embedding == {"urgent": 0.8}      # real dims survive ...
    assert "<goal>" not in g.node(tok).embedding         # ... the token key does not


def test_reserved_token_mint_is_control_but_inert_provenance_is_not():
    # Phase 2.2 HALF 2 (control-ness at mint): reserved `<…>` syntax + NOT inert ⟹ CONTROL, the
    # ratified content-blind criterion applied at the mint chokepoint. Inert provenance is EXCLUDED
    # (it is inert, not control); an ordinary entity name is neither.
    g = AttrGraph()
    assert g.is_control(g.add_node("<goal>"))                      # reserved token ⟹ control
    assert not g.is_control(g.add_node("Paul"))                    # ordinary entity ⟹ neither
    axiom = g.add_node("<axiom>", inert=True)                      # inert provenance ⟹ inert, NOT control
    assert g.is_inert(axiom) and not g.is_control(axiom)

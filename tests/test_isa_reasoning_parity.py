"""
`run_bank` REASONING properties (implementation_plan.md Phase 0.3): the forward ISA Machine drives
the planner's REASONING + control, not just recognition. Recognition compared graphs as SETS of
triples, which hid two node-IDENTITY properties reasoning depends on — a downstream rule joins by
NODE, and the fixpoint loop witnesses on the EDGE set:

  1. INTERN — a head endpoint that is a PLAIN LITERAL canonicalizes to its graph-wide node
     (`apply_rule.resolve_so`), so two head-derived literals join. A fresh node per firing splits the
     join (`<need> for ?c` and `?o add ?c` sharing `have_valuable`) and the derivation silently stalls
     — the exact `test_cards_frontier` value->plan divergence that gated the planner routing.
  2. DEDUP — a reified relation reuses an existing `subject -[rel]-> object`
     (`apply_rule._relation_exists`), so a rule re-fired across outer control cycles does not accrete
     duplicate rel nodes and the graph's EDGE set reaches a fixpoint (the planner's `_fingerprint`
     witness settles instead of growing forever).

Equivalence with the previous (rewriter / name-based) generation is NOT a correctness target
(implementation_plan.md, 2026-07-10 ratification) — assertions below pin run_bank's OWN behavior.
"""
import ugm as h
from ugm.production_rule import Pat, Rule
from ugm.cnl.authoring import load_rules
from ugm import run_bank, derived_triples


def _triples(g):
    return set(derived_triples(g))


def _named(g, nm):
    return [n for n in g.nodes() if g.name(n) == nm]


def test_head_literal_interns_so_a_downstream_rule_joins():
    # rule A mints `op add GOAL` (GOAL a plain literal); the fact `<need> for GOAL` names the SAME
    # literal. rule B joins them on GOAL by NODE identity. Without interning A mints a fresh GOAL
    # node != the `<need> for GOAL` node and B never fires.
    g = h.Graph()
    op, card, need = g.add_node("op"), g.add_node("card"), g.add_node("<need>")
    g.add_relation(op, "acts_on", card)
    g.add_relation(card, "is", g.add_node("valuable"))
    g.add_relation(need, "for", g.add_node("goal"))
    rules = load_rules("?o add goal when ?o acts_on ?c and ?c is valuable\n"
                       "?o picked <yes> when <need> for goal and ?o add goal")
    run_bank(g, rules)
    assert ("op", "add", "goal") in _triples(g)
    assert ("op", "picked", "<yes>") in _triples(g)   # the join fired -> literals canonicalized
    assert len(_named(g, "goal")) == 1                # one shared goal node, not one per firing


def test_two_producers_of_a_literal_share_one_node():
    # two DIFFERENT rules mint `_ add TARGET`; the literal endpoint must be the SAME node for both,
    # so a consumer joining on TARGET sees a single canonical object (rewriter.resolve_so parity).
    g = h.Graph()
    a, b = g.add_node("a"), g.add_node("b")
    g.add_relation(a, "is", g.add_node("p"))
    g.add_relation(b, "is", g.add_node("q"))
    rules = load_rules("?x add target when ?x is p\n?y add target when ?y is q")
    run_bank(g, rules)
    assert len(_named(g, "target")) == 1
    assert {"a", "b"} == {s for (s, r, o) in _triples(g) if r == "add" and o == "target"}


def test_relation_dedup_reaches_an_edge_fixpoint_across_reruns():
    # re-running the SAME rule (as the planner's outer control loop does, each call with a fresh
    # `fired` set) must not accrete duplicate rel nodes: the graph's EDGE set is a fixpoint, which
    # is what lets `planning._fingerprint` settle instead of growing every cycle.
    g = h.Graph()
    a = g.add_node("a")
    g.add_relation(a, "is", g.add_node("rare"))
    rule = load_rules("?x flag <yes> when ?x is rare")
    run_bank(g, rule)
    edges_after_first = set(g.edges())
    for _ in range(3):
        run_bank(g, rule)                             # re-fire from scratch, as an outer cycle would
    assert set(g.edges()) == edges_after_first        # no new duplicate rel nodes
    assert len([n for n in g.nodes() if g.name(n) == "flag"]) == 1


def test_runbank_derives_the_two_clause_value_bridge():
    # the value->plan bridge SHAPE (a rule whose head extends a subject's relation from a derived
    # property, then a join on that head) — pins run_bank's own derived-triple set directly.
    def build():
        g = h.Graph()
        op, card, need = g.add_node("op"), g.add_node("card"), g.add_node("<need>")
        g.add_relation(op, "acts_on", card)
        g.add_relation(card, "is", g.add_node("rare"))
        g.add_relation(card, "is", g.add_node("in_demand"))
        g.add_relation(need, "for", g.add_node("have_valuable"))
        return g
    rules = load_rules(
        "?c is valuable when ?c is rare and ?c is in_demand\n"
        "?o add have_valuable when ?o acts_on ?c and ?c is valuable\n"
        "?o candidate have_valuable when <need> for have_valuable and ?o add have_valuable")
    g_isa = build()
    run_bank(g_isa, rules)
    assert _triples(g_isa) == {
        ("<need>", "for", "have_valuable"), ("acts_on", "card", "is"),
        ("card", "is", "in_demand"), ("card", "is", "rare"), ("card", "is", "valuable"),
        ("op", "acts_on", "card"), ("op", "add", "have_valuable"),
        ("op", "candidate", "have_valuable"),
    }
    assert ("op", "candidate", "have_valuable") in _triples(g_isa)


# --- Phase 0.4: propagate -> EMIT (graded embedding write, dynamic key) ---------------------

def test_propagate_writes_embedding_with_a_dynamic_key():
    # a propagate rule whose dimension is a BOUND var (`?adj`): the embedding key is resolved at
    # apply time to the bound node's NAME (`MINT`-free dynamic-key EMIT). This is the graded rule's
    # shape (`?x.embedding[name(?adj)] = value`).
    g = h.Graph()
    alice = g.add_node("alice")
    g.add_relation(alice, "is", g.add_node("urgent"))
    rule = Rule(key="grade", lhs=[Pat("?x", "is", "?adj")], rhs=[],
                propagate={"op": "set", "var": "?x", "dim": "?adj", "value": 0.8})
    run_bank(g, [rule])
    assert g.get_embedding(alice) == {"urgent": 0.8}   # key = name(bound ?adj), value SET


def test_propagate_with_a_literal_dimension():
    # a literal dimension lowers to a STATIC-key EMIT (the other `_token_name` branch).
    g = h.Graph()
    alice = g.add_node("alice")
    g.add_relation(alice, "is", g.add_node("boss"))
    rule = Rule(key="lit", lhs=[Pat("?x", "is", "boss")], rhs=[],
                propagate={"op": "set", "var": "?x", "dim": "urgent", "value": 0.5})
    run_bank(g, [rule])
    assert g.get_embedding(alice) == {"urgent": 0.5}


def test_graded_pass_writes_the_expected_embedding_end_to_end():
    # the real graded pass (load_facts: recognize -> coref -> graded) on run_bank writes the
    # expected embedding — pins the value directly (routing graded_rules onto run_bank).
    def emb(g):
        return {g.name(n): g.get_embedding(n) for n in g.nodes() if g.get_embedding(n)}
    text = "urgent is gradable\nalice is very urgent"
    from ugm.cnl.authoring import (
        _recognize, FORM_RULES, FACT_FORMS, wire_same_as, _coref_propagation, graded_rules,
        propagate_embeddings,
    )
    g = h.Graph()
    rules = FORM_RULES + FACT_FORMS
    _recognize(g, text.splitlines(), rules)
    wire_same_as(g, rules)
    run_bank(g, _coref_propagation(g))
    run_bank(g, graded_rules(g))
    propagate_embeddings(g)
    assert emb(g).get("alice") == {"urgent": 0.8}


# --- Phase 0.5: provenance minting (walker/coref/fact-reasoning path) ------------------------

def _prov_structure(g):
    """Every (rule-key, rel-name, sorted subj-names, sorted obj-names) a J proves, plus each J's
    `uses` premises — the justification structure `run_bank` (provenance=True) builds
    (provenance.py: J -[proves]-> fact, J -[uses]-> premise)."""
    import ugm.provenance as pv
    from ugm.world_model import _is_inert
    live = lambda ns: tuple(sorted(g.name(n) for n in ns if not _is_inert(g.name(n))))
    proven = set()
    for pn in g.nodes_named(pv.PROVES):
        for j in g.into(pn):
            for rel in g.out(pn):
                # skip the `proves`/`uses` provenance nodes wired onto this fact (inert predecessors
                # of `rel`) so subj/obj are the true fact endpoints
                proven.add((g.name(j), g.name(rel), live(g.into(rel)), live(g.out(rel))))
    used = sorted((g.name(un) for un in g.nodes_named(pv.USES)))
    return proven, used


def test_runbank_provenance_on_transitivity():
    # run_bank(provenance=True) mints one `<j:rule>` per firing that CREATED facts, `proves`
    # each new fact, `uses` each LHS premise — pinned directly on run_bank's own output.
    def build():
        g = h.Graph()
        g.add_relation(g.add_node("a"), "is_a", g.add_node("b"))
        b = g.nodes_named("b")[0]; g.add_relation(b, "is_a", g.add_node("c"))
        c = g.nodes_named("c")[0]; g.add_relation(c, "is_a", g.add_node("d"))
        return g
    rules = load_rules("?x is_a ?z when ?x is_a ?y and ?y is_a ?z")
    g_isa = build()
    run_bank(g_isa, list(rules), provenance=True)
    proven, used = _prov_structure(g_isa)
    assert proven == {
        ("<j:rule.?x.is_a.?z>", "is_a", ("b",), ("d",)),
        ("<j:rule.?x.is_a.?z>", "is_a", ("a",), ("d",)),
        ("<j:rule.?x.is_a.?z>", "is_a", ("a",), ("c",)),
    }
    assert used == ["uses"] * 6
    # sanity: a real justification was minted (not the empty degenerate case)
    assert proven


def test_runbank_does_not_reprove_a_deduped_fact():
    # a firing whose head relation ALREADY exists creates no new fact -> mints NO justification
    # (rewriter._apply: J only `if made_facts`). Re-running must not accrete extra J/proves nodes.
    import ugm.provenance as pv
    g = h.Graph()
    a = g.add_node("a"); g.add_relation(a, "is", g.add_node("rare"))
    rules = load_rules("?x flag yes when ?x is rare")
    run_bank(g, rules, provenance=True)
    j_after_first = len(g.nodes_named(pv.PROVES))
    run_bank(g, rules, provenance=True)               # re-fire: the `flag` already exists -> no new J
    assert len(g.nodes_named(pv.PROVES)) == j_after_first

"""Regression suite for the one-substrate core (docs/vision.md).

Self-contained; run with:  pytest tests/test_new_core.py --noconftest
Covers the substrate, rule layer, engine, forms, and surface readers.
"""
import ugm as h
from ugm.cnl import rewriter


# ---------------------------------------------------------------------------
# Substrate
# ---------------------------------------------------------------------------

def test_duplicate_names_are_distinct_instances():
    g = h.Graph()
    p1, p2 = g.add_node("Paul"), g.add_node("Paul")
    assert p1 != p2
    assert len(g.nodes_named("Paul")) == 2


def test_nodes_carry_no_value_datum_is_a_node():
    g = h.Graph()
    cfg = g.add_node("urgency_per_tick")
    val = g.add_node("0.2")
    g.add_relation(cfg, "value", val)
    # the datum 0.2 is reached by traversal, as a node named "0.2"
    rels = [(g.name(r), g.name(o)) for r, o in g.relations_from(cfg)]
    assert rels == [("value", "0.2")]


def test_edges_are_untyped_relation_is_a_node():
    g = h.Graph()
    s, o = g.add_node("paul"), g.add_node("person")
    rid = g.add_relation(s, "is_a", o)
    # the relation is a node on a 2-hop path; both edges are bare
    assert g.name(rid) == "is_a"
    assert g.has_edge(s, rid) and g.has_edge(rid, o)


def test_within_locality_radius():
    g = h.Graph()
    a, b, c = g.add_node("a"), g.add_node("b"), g.add_node("c")
    g.add_edge(a, b)
    g.add_edge(b, c)
    assert g.within([a], 1) == {a, b}
    assert g.within([a], 2) == {a, b, c}


def test_gc_disconnected():
    g = h.Graph()
    s, o = g.add_node("s"), g.add_node("o")
    g.add_relation(s, "p", o)
    lonely = g.add_node("lonely")
    removed = g.gc_disconnected()
    assert lonely in removed
    assert not g.has(lonely) and g.has(s)


# ---------------------------------------------------------------------------
# Rule layer
# ---------------------------------------------------------------------------

def test_bound_and_fresh_names():
    r = h.Rule(
        key="k",
        lhs=[h.Pat("?p", "is_a", "person"), h.Pat("?p", "owns", "?c")],
        rhs=[h.Pat("?p", "flagged", "?tag"), h.Pat("?tag", "label", "owner")],
    )
    assert r.bound_names() == {"?p", "?c"}
    assert r.fresh_names() == {"?tag"}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def _rel(g, s, p, o):
    si = g.nodes_named(s)[0] if g.nodes_named(s) else g.add_node(s)
    oi = g.nodes_named(o)[0] if g.nodes_named(o) else g.add_node(o)
    g.add_relation(si, p, oi)


def _has(g, s, p, o):
    return any(
        rewriter._relation_exists(g, si, p, oi)
        for si in g.nodes_named(s) for oi in g.nodes_named(o)
    )


def test_subgraph_join_with_nac_idempotent():
    g = h.Graph()
    _rel(g, "paul", "is_a", "person")
    _rel(g, "paul", "owns", "c1")
    _rel(g, "c1", "is_a", "car")
    _rel(g, "c1", "color", "red")
    rule = h.Rule(
        key="flag",
        lhs=[h.Pat("?p", "is_a", "person"), h.Pat("?p", "owns", "?c"),
             h.Pat("?c", "is_a", "car"), h.Pat("?c", "color", "red")],
        nac=[h.Pat("?p", "flagged", "owner")],
        rhs=[h.Pat("?p", "flagged", "owner")],
    )
    assert len(h.run(g, [rule])) == 1
    assert _has(g, "paul", "flagged", "owner")
    assert len(h.run(g, [rule])) == 0          # NAC blocks re-fire


def test_homomorphic_token_passing_loop():
    g = h.Graph()
    a, b, c = g.add_node("a"), g.add_node("b"), g.add_node("c")
    g.add_relation(a, "next", b)
    g.add_relation(b, "next", c)
    g.add_relation(a, "<current>", a)          # token self-relation (needs homomorphic match)
    step = h.Rule(
        key="advance",
        lhs=[h.Pat("?t", "<current>", "?x"), h.Pat("?x", "next", "?y")],
        rhs=[h.Pat("?x", "is", "seen"), h.Pat("?y", "<current>", "?y")],
        drop=[h.Pat("?t", "<current>", "?x")],
    )
    h.run(g, [step])
    # NB: filter provenance nodes — a `proves` node has an edge to the 'is' relation it
    # justifies, so a raw all-nodes scan would see it as a subject of 'is' (vision §9).
    _prov = lambda n: n in ("proves", "uses") or n.startswith("<j:")
    marked = {g.name(s) for s in g.nodes()
              if not _prov(g.name(s)) and any(g.name(r) == "is" for r in g.out(s))}
    token_on = {g.name(o) for r in g.nodes() if g.name(r) == "<current>" for o in g.out(r)}
    assert marked == {"a", "b"}
    assert token_on == {"c"}


def test_graded_firing_confidence_and_alpha_cut():
    # high urgency fires with confidence 0.8 * 0.9
    g = h.Graph()
    cust = g.add_node("cust", embedding={"urgency": 0.9})
    g.add_relation(cust, "is_a", g.add_node("customer"))
    rule = h.Rule(
        key="urgent",
        lhs=[h.Pat("?c", "is_a", "customer")],
        rhs=[h.Pat("?c", "priority", "high")],
        probability=0.8,
        graded=[h.GradedCondition(var="?c", embedding={"urgency": 1.0}, threshold=0.5)],
    )
    assert len(h.run(g, [rule])) == 1
    rel = [r for r in g.out(cust) if g.name(r) == "priority"][0]
    assert abs(g.get_confidence(rel) - 0.72) < 1e-9

    # low urgency is alpha-cut (no fire)
    g2 = h.Graph()
    c2 = g2.add_node("c2", embedding={"urgency": 0.2})
    g2.add_relation(c2, "is_a", g2.add_node("customer"))
    assert len(h.run(g2, [rule])) == 0


def test_propagate_set_writes_embedding_on_fire():
    # A rule SETS an embedding via `propagate` (not a bolt-on tool) — dim taken from
    # a bound variable's node name, value from the rule parameter.
    g = h.Graph()
    x = g.add_node("alice")
    adj = g.add_node("urgent")
    g.add_relation(x, "mentions", adj)
    rule = h.Rule(
        key="grade",
        lhs=[h.Pat("?x", "mentions", "?adj")],
        rhs=[],
        propagate={"op": "set", "var": "?x", "dim": "?adj", "value": 0.8},
    )
    assert len(h.run(g, [rule])) == 1          # fires once within a run (sig-suppressed)
    assert g.get_embedding(x) == {"urgent": 0.8}


# ---------------------------------------------------------------------------
# Forms + the no-seam pipeline
# ---------------------------------------------------------------------------

def test_tokenize_builds_next_chain():
    g = h.Graph()
    h.tokenize(g, "paul is a person")
    # four word tokens exist
    for w in ("paul", "is", "a", "person"):
        assert g.nodes_named(w)
    # adjacency exists as 'next' relations
    paul = g.nodes_named("paul")[0]
    assert any(g.name(r) == "next" for r in g.out(paul))


def test_no_seam_pipeline_cnl_to_reasoning():
    g = h.Graph()
    h.load_text(g, "paul is a person\npaul has a car")
    mortal = h.Rule(key="mortal", lhs=[h.Pat("?a", "is_a", "person")],
                    rhs=[h.Pat("?a", "is_a", "mortal")])
    h.run(g, h.FORM_RULES + [mortal])
    assert _has(g, "paul", "is_a", "person")   # form.is_a
    assert _has(g, "paul", "has", "car")        # form.has
    assert _has(g, "paul", "is_a", "mortal")    # reasoning on canonical form


def test_cnl_facts_with_gradable_vocabulary():
    # Gradedness is CNL DATA ('urgent is gradable'); a generic rule turns
    # 'alice is very urgent' into an embedding via propagate — no Python seeding.
    g = h.Graph()
    h.load_facts(g, "urgent is gradable\n"
                    "alice is a customer\nalice wants vanilla\nalice is very urgent\n"
                    "bob is a customer\nvanilla is in_stock")
    assert _has(g, "alice", "is_a", "customer")
    assert _has(g, "alice", "wants", "vanilla")
    assert _has(g, "vanilla", "is", "in_stock")
    assert g.get_embedding(g.nodes_named("alice")[0]) == {"urgent": 0.8}
    assert g.get_embedding(g.nodes_named("bob")[0]) == {}     # not modified -> no embedding






def test_native_rule_cnl_folds_into_rules():
    # `HEAD when COND and COND ...` folds (in-graph forms) into an executable Rule:
    # `is a` -> is_a lhs, bare `is` -> marker lhs, `is not` -> NAC, `is very` -> graded.
    rules = h.load_rules(
        "?c served express when ?c is urgent and ?c wants ?f and ?f is in_stock\n"
        "?c served regular when ?c wants ?f and ?f is in_stock and ?c is not urgent\n"
        "?c is urgent when ?c is a customer and ?c is very urgent"
    )
    by_key = {r.key: r for r in rules}

    express = by_key["rule.?c.served.express"]
    assert _pats(express.rhs) == [("?c", "served", "express")]
    assert _pats(express.lhs) == [("?c", "is", "urgent"), ("?c", "wants", "?f"),
                                  ("?f", "is", "in_stock")]
    assert express.nac == []

    regular = by_key["rule.?c.served.regular"]
    assert _pats(regular.nac) == [("?c", "is", "urgent")]        # `is not` -> NAC

    mark = by_key["rule.?c.is.urgent"]
    assert _pats(mark.lhs) == [("?c", "is_a", "customer")]       # `is a` -> is_a
    assert len(mark.graded) == 1                                  # `is very` -> graded
    assert mark.graded[0].var == "?c"
    assert mark.graded[0].embedding == {"urgent": 1.0}
    assert mark.graded[0].threshold == 0.8


def test_prose_rule_malformed_body_clause_raises():
    # handoff 1a: with the unified grammar the generic clause folds ANY `S P O`, so a
    # relation clause no longer drops. But a genuinely MALFORMED clause (wrong arity — a lone
    # token the generic triple can't consume) must still be REPORTED, never silently dropped.
    import pytest
    with pytest.raises(ValueError, match="alone"):
        h.load_rules("?x is happy when ?x alone")            # 2-token clause, no triple
    # in a mixed rule only the malformed clause is reported, not the valid one
    with pytest.raises(ValueError, match="solo"):
        h.load_rules("?c served express when ?c wants ?f and ?f solo")
    # a well-formed rule is unaffected
    assert h.load_rules("?x is happy when ?x is a customer and ?x wants ?f")


def test_prose_rule_grammar_unified_any_relation_folds():
    # handoff 1a proper-fix (grammar unification): the prose body now uses the SHARED spine, so
    # an arbitrary relation condition folds WITHOUT any declaration (no fixed menu).
    rules = h.load_rules("?x is happy when ?x visits dog")
    assert _pats(rules[0].lhs) == [("?x", "visits", "dog")]
    assert _pats(rules[0].rhs) == [("?x", "is", "happy")]
    # a mix of a generic relation, copula sugar, and a NAC all fold in one prose rule
    [r] = h.load_rules("?c served express when ?c visits shop and ?c is a customer "
                       "and ?c wants ?f and ?f is not sold_out")
    assert _pats(r.lhs) == [("?c", "is_a", "customer"), ("?c", "visits", "shop"),
                            ("?c", "wants", "?f")]
    assert _pats(r.nac) == [("?f", "is", "sold_out")]




# ---------------------------------------------------------------------------
# Surface normalization — determiners + multi-word DECOMPOSITION, all as forms (Tier 3a)
# ---------------------------------------------------------------------------

def test_surface_forms_decompose_np_into_head_plus_attribute():
    # The forms on a token chain: "the bald eagle is a bird" -> determiner dropped, and the NP
    # decomposes to head `eagle` + attribute `eagle is bald` (NOT an atomic "bald eagle" token).
    g = h.Graph()
    anchor = h.tokenize(g, "the bald eagle is a bird")
    kw = h.form_keywords(h.FORM_RULES)
    h.normalize_surface(g, anchor, h.surface_forms(kw))
    words = [g.name(t) for t in h.forms._chain_tokens(g, anchor)]
    assert words == ["eagle", "is", "a", "bird"]
    attrs = {(g.name(x), g.name(o)) for x in g.nodes()
             for r, o in g.relations_from(x) if g.name(r) == "is"}
    assert ("eagle", "bald") in attrs


def test_surface_forms_only_decompose_determiner_introduced_np():
    # Controlled: with no determiner/quantifier the run is NOT a noun phrase, so it does not
    # decompose (an undeclared "sends parcel" stays for the n-ary form to reject, not attributes).
    g = h.Graph()
    anchor = h.tokenize(g, "alice sends parcel")
    h.normalize_surface(g, anchor, h.surface_forms(h.form_keywords(h.FORM_RULES)))
    assert [g.name(t) for t in h.forms._chain_tokens(g, anchor)] == ["alice", "sends", "parcel"]














# ---------------------------------------------------------------------------
# Anaphoric pronouns — resolve to the discourse subject (Tier 3b)
# ---------------------------------------------------------------------------











def test_cnl_authored_ice_cream_end_to_end():
    # The whole domain authored in CNL — facts + rules, no Python domain logic —
    # reproduces the planner-free routing (alice express / bob regular / carol alt).
    g = h.Graph()
    h.load_facts(g, "urgent is gradable\n"
                    "alice is a customer\nalice wants vanilla\nalice is very urgent\n"
                    "bob is a customer\nbob wants chocolate\n"
                    "carol is a customer\ncarol wants strawberry\n"
                    "vanilla is in_stock\nchocolate is in_stock")
    rules = h.load_rules(
        "?c is urgent when ?c is a customer and ?c is very urgent\n"
        "?c served express when ?c is urgent and ?c wants ?f and ?f is in_stock\n"
        "?c served regular when ?c wants ?f and ?f is in_stock and ?c is not urgent\n"
        "?c offered alternative when ?c is a customer and ?c wants ?f and ?f is not in_stock"
    )
    # Additive coref: domain rules reason ALONGSIDE `same_as` propagation (as the Session's
    # reasoning bank does) so a derived fact (`?c is urgent`) reaches every coreferent mention —
    # else the `regular` NAC (`?c is not urgent`) sees a mention the derivation missed and misfires.
    h.run_rules(g, rules + h.same_as_rules(h.relation_predicates(g)))

    def outcome(name):
        # dedupe: additive coref replicates a derived fact across an entity's coreferent
        # mentions (no destructive merge), so collect the SET of outcomes, not each mention's copy.
        return sorted({g.name(o) for s in g.nodes_named(name)
                       for r, o in g.relations_from(s)
                       if g.name(r) in ("served", "offered")})

    assert outcome("alice") == ["express"]      # urgent + in stock
    assert outcome("bob") == ["regular"]        # calm + in stock (NAC sees derived 'is urgent')
    assert outcome("carol") == ["alternative"]  # wants out-of-stock flavour


def test_stratify_orders_nac_after_producer():
    # A rule whose NAC negates another rule's head lands in a later stratum.
    producer = h.Rule(key="p", lhs=[h.Pat("?x", "is_a", "customer")],
                      rhs=[h.Pat("?x", "is", "urgent")])
    consumer = h.Rule(key="c", lhs=[h.Pat("?x", "is_a", "customer")],
                      nac=[h.Pat("?x", "is", "urgent")],
                      rhs=[h.Pat("?x", "served", "regular")])
    strata = h.stratify([consumer, producer])
    assert [r.key for r in strata[0]] == ["p"]
    assert [r.key for r in strata[1]] == ["c"]


def test_run_rules_degrades_on_negation_cycle():
    # handoff 2a: a single negation cycle used to make run_rules raise and leave the WHOLE
    # theory unreasoned. Now it degrades to the monotone subset (positive chains still answer)
    # and warns; strict=True restores the hard failure.
    import warnings
    import pytest
    a = h.Rule(key="cyc.a", lhs=[h.Pat("?x", "base", "?y")],
               nac=[h.Pat("?x", "q", "?y")], rhs=[h.Pat("?x", "p", "?y")])
    b = h.Rule(key="cyc.b", lhs=[h.Pat("?x", "base", "?y")],
               nac=[h.Pat("?x", "p", "?y")], rhs=[h.Pat("?x", "q", "?y")])
    mono = h.Rule(key="mono", lhs=[h.Pat("?x", "is_a", "person")],
                  rhs=[h.Pat("?x", "is_a", "mortal")])
    g = h.Graph()
    s = g.add_node("socrates")
    g.add_relation(s, "is_a", g.add_node("person"))

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        h.run_rules(g, [a, b, mono])
        assert w and "not stratifiable" in str(w[0].message)
    # the monotone chain still fired despite the cycle
    assert "mortal" in [g.name(o) for si in g.nodes_named("socrates")
                        for rn, o in g.relations_from(si) if g.name(rn) == "is_a"]
    with pytest.raises(ValueError):
        h.run_rules(h.Graph(), [a, b], strict=True)


def test_loose_phrasing_translates_to_native_rule():
    # A loose imperative + a CNL lexicon frame -> the native rule (the user's ask).
    lexicon = "serve ?x first means ?x served express when ?x wants ?f and ?f is in_stock"
    rules = h.load_loose_rules("serve urgent customers first", lexicon)
    assert len(rules) == 1
    r = rules[0]
    assert _pats(r.rhs) == [("?x", "served", "express")]
    # frame conditions from the lexicon, PLUS the loose adjective as a marker condition
    assert _pats(r.lhs) == [("?f", "is", "in_stock"), ("?x", "is", "urgent"),
                            ("?x", "wants", "?f")]


def test_loose_rule_drops_into_full_routing():
    # The translated loose rule routes identically to its native twin.
    g = h.Graph()
    h.load_facts(g, "urgent is gradable\n"
                    "alice is a customer\nalice wants vanilla\nalice is very urgent\n"
                    "bob is a customer\nbob wants chocolate\nvanilla is in_stock\nchocolate is in_stock")
    native = ("?c is urgent when ?c is a customer and ?c is very urgent\n"
              "?c served regular when ?c wants ?f and ?f is in_stock and ?c is not urgent")
    loose = h.load_loose_rules(
        "serve urgent customers first",
        "serve ?x first means ?x served express when ?x wants ?f and ?f is in_stock")
    h.run_rules(g, h.load_rules(native) + loose + h.same_as_rules(h.relation_predicates(g)))

    def outcome(name):                               # dedupe across coreferent mentions (see above)
        return sorted({g.name(o) for s in g.nodes_named(name)
                       for r, o in g.relations_from(s) if g.name(r) == "served"})
    assert outcome("alice") == ["express"]
    assert outcome("bob") == ["regular"]


# ---------------------------------------------------------------------------
# Q2 — asking the KB questions in CNL, getting CNL answers (recognition emergent)
# ---------------------------------------------------------------------------

def test_ask_relation_questions():
    g = h.Graph()
    h.load_facts(g, "urgent is gradable\nalice is a customer\nalice wants vanilla\n"
                    "alice is very urgent\nvanilla is in_stock")
    rules = h.load_rules(
        "?c is urgent when ?c is a customer and ?c is very urgent\n"
        "?c served express when ?c is urgent and ?c wants ?f and ?f is in_stock")
    journal = h.run_rules(g, rules)

    assert h.ask(g, "is alice served express") == ["yes"]        # yes/no, relation
    assert h.ask(g, "is alice served regular") == ["no"]
    assert h.ask(g, "is alice a customer") == ["yes"]            # yes/no, is_a
    assert h.ask(g, "is vanilla in_stock") == ["yes"]           # yes/no, copula
    assert h.ask(g, "who served express") == ["alice served express"]   # wh
    assert h.ask(g, "who wants vanilla") == ["alice wants vanilla"]
    # why -> a derivation trace from the journal
    why = h.ask(g, "why alice served express", journal=journal, rules=rules)
    assert why[0].startswith("alice served express  <- ")


def test_ask_is_a_questions_and_unrecognized():
    g = h.Graph()
    h.load_text(g, "paul is a person\nevery person is a mortal")
    h.run(g, h.FORM_RULES)
    h.canonicalize(g, h.FORM_RULES + h.UNIVERSAL_RULES)
    laws = h.expand_universals(g)                  # "every person is a mortal" is now a LAW
    j = h.run(g, h.UNIVERSAL_RULES + laws)
    R = h.FORM_RULES + h.UNIVERSAL_RULES + laws

    assert h.ask(g, "is paul a mortal") == ["yes"]               # derived via transitivity
    assert h.ask(g, "is paul a robot") == ["no"]
    assert "paul is_a mortal" in h.ask(g, "who is a mortal")
    why = h.ask(g, "why paul is a mortal", journal=j, rules=R)
    assert why[0].startswith("paul is_a mortal  <- ")
    assert any("(given)" in line for line in why)               # bottoms out at given facts

    # recognition is emergent: a non-question yields no <query>
    assert h.recognize("paul is a person") is None
    assert h.ask(g, "paul is a person") == ["(no question form recognized this)"]


# ---------------------------------------------------------------------------
# Q1a — one mixed corpus; what each statement IS emerges from the forms
# ---------------------------------------------------------------------------

def test_load_corpus_emergent_recognition():
    # Facts, native rules, a lexicon frame and a loose phrasing in ONE unsectioned
    # corpus — no Python classifier; the keywords route each statement.
    corpus = """
        # a mixed corpus, no sections
        urgent is gradable
        vanilla is in_stock
        chocolate is in_stock
        alice is a customer
        alice wants vanilla
        alice is very urgent
        bob is a customer
        bob wants chocolate
        carol is a customer
        carol wants strawberry
        ?c is urgent when ?c is a customer and ?c is very urgent
        ?c served regular when ?c wants ?f and ?f is in_stock and ?c is not urgent
        ?c offered alternative when ?c is a customer and ?c wants ?f and ?f is not in_stock
        serve ?x first means ?x served express when ?x wants ?f and ?f is in_stock
        serve urgent customers first
    """
    kb, rules = h.load_corpus(corpus)

    # rules were recognized (3 native + 1 lexicon-translated loose); the frame body
    # template is NOT emitted as a standalone rule. (`load_corpus` also appends `same_as`
    # coreference-propagation rules — infrastructure, not recognized domain rules — filtered here.)
    keys = sorted(r.key for r in rules if not r.key.startswith("same_as"))
    assert keys == ["loose.serve.urgent.first", "rule.?c.is.urgent",
                    "rule.?c.offered.alternative", "rule.?c.served.regular"]

    # facts + the graded layer landed in the KB; rule-source did NOT pollute it
    assert _has(kb, "alice", "is_a", "customer")
    assert _has(kb, "vanilla", "is", "in_stock")
    assert kb.get_embedding(kb.nodes_named("alice")[0]) == {"urgent": 0.8}

    # end-to-end routing matches the planner-free reference
    h.run_rules(kb, rules)

    def outcome(name):                               # dedupe across coreferent mentions (additive coref)
        return sorted({kb.name(o) for s in kb.nodes_named(name)
                       for r, o in kb.relations_from(s)
                       if kb.name(r) in ("served", "offered")})
    assert outcome("alice") == ["express"]
    assert outcome("bob") == ["regular"]
    assert outcome("carol") == ["alternative"]


def test_one_graph_context_isolation():
    # b2: facts and rule-source coexist in ONE graph; reasoning is isolated from
    # rule-source NOT by an engine scope but by DATA — reasoning rules bind a context
    # node (the shop) that rule patterns can't satisfy. A prior-knowledge rule fills
    # the implicit context ("customers are in the shop").
    corpus = """
        shop1 is a shop
        urgent is gradable
        vanilla is in_stock
        chocolate is in_stock
        alice is a customer
        alice wants vanilla
        alice is very urgent
        bob is a customer
        bob wants chocolate
        ?c in ?shop when ?c is a customer and ?shop is a shop
        ?c is urgent when ?c is a customer and ?c is very urgent
        ?c served express when ?c is urgent and ?c wants ?f and ?f is in_stock and ?c in ?shop
        ?c served regular when ?c wants ?f and ?f is in_stock and ?c is not urgent and ?c in ?shop
    """
    kb, rules = h.load_corpus(corpus)

    # facts AND rule-source share the one graph
    rule_nodes = [n for n in kb.nodes()
                  if any(kb.name(r) == "rl_pred" for r, _ in kb.relations_from(n))]
    assert len(rule_nodes) >= 4
    assert _has(kb, "alice", "is_a", "customer")          # a fact, same graph

    h.run_rules(kb, rules)

    # the prior-knowledge rule stamped the implicit context
    assert _has(kb, "alice", "in", "shop1")
    # reasoning is isolated + correct; nothing but real customers is is_a customer
    custs = sorted({kb.name(c) for c in kb.nodes()      # dedupe coreferent mentions (additive coref)
                    if not (kb.name(c) in ("proves", "uses") or kb.name(c).startswith("<j:"))
                    for r in kb.out(c)
                    if kb.name(r) == "is_a" and any(kb.name(o) == "customer" for o in kb.out(r))})
    assert custs == ["alice", "bob"]

    def served(name):
        return sorted({kb.name(o) for s in kb.nodes_named(name)
                       for r, o in kb.relations_from(s) if kb.name(r) == "served"})
    assert served("alice") == ["express"]
    assert served("bob") == ["regular"]


def test_defeasible_context_default_defeated_by_explicit_placement():
    # Handoff tier-a: the prior-knowledge context rule is a DEFEASIBLE default. The
    # `?c not in ?other` NAC makes it fire UNLESS the customer is already placed, so
    # an explicit placement fact ("bob in shop2", recognized by form.fact.in) defeats
    # the default for bob — more-specific evidence beats the general rule, with NO
    # retraction (monotone). An unplaced customer still gets the default context.
    corpus = """
        shop1 is a shop
        shop2 is a shop
        alice is a customer
        bob is a customer
        bob in shop2
        ?c in ?shop when ?c is a customer and ?shop is a shop and ?c not in ?other
    """
    kb, rules = h.load_corpus(corpus)

    # the explicit placement was recognized as a fact (not swallowed by the rule head)
    assert _has(kb, "bob", "in", "shop2")

    h.run_rules(kb, rules)

    def placed(name):                                # dedupe across coreferent mentions (additive coref)
        return sorted({kb.name(o) for s in kb.nodes_named(name)
                       for r, o in kb.relations_from(s) if kb.name(r) == "in"})

    # bob is explicitly placed -> the default is DEFEATED (NOT also placed in shop1)
    assert placed("bob") == ["shop2"]
    # alice is unplaced -> the default fires and supplies a context
    assert "shop1" in placed("alice")
    # (with several candidate shops and no explicit info the default is non-selective
    #  — it places alice in every shop; picking exactly one is a control-layer concern
    #  beyond this monotone tier.)


# ---------------------------------------------------------------------------
# Surface — narration + journal-based explanation
# ---------------------------------------------------------------------------

def test_narrate_and_explain():
    g = h.Graph()
    h.load_text(g, "paul is a person")
    mortal = h.Rule(key="mortal", lhs=[h.Pat("?a", "is_a", "person")],
                    rhs=[h.Pat("?a", "is_a", "mortal")])
    rules = h.FORM_RULES + [mortal]
    journal = h.run(g, rules)

    narration = h.narrate(g, journal)
    assert "paul is_a person   [form.is_a]" in narration
    assert "paul is_a mortal   [mortal]" in narration

    trace = h.explain(g, journal, rules, "paul", "is_a", "mortal")
    assert trace[0] == "paul is_a mortal  <- mortal"
    assert any("paul is_a person  <- form.is_a" in line for line in trace)
    assert any("(given)" in line for line in trace)   # bottoms out at tokenizer facts


# ---------------------------------------------------------------------------
# Goals + universal rules + canonicalize (coreference)
# ---------------------------------------------------------------------------

def test_goal_satisfaction_pipeline():
    g = h.Graph()
    h.load_text(g, "paul is a person\nevery person is a mortal\ngoal paul is a mortal")
    h.run(g, h.FORM_RULES)              # surface -> canonical
    h.canonicalize(g, h.FORM_RULES + h.UNIVERSAL_RULES)  # unify same-named mentions
    laws = h.expand_universals(g)                  # "every person is a mortal" -> a law
    h.run(g, h.UNIVERSAL_RULES + laws)  # universal law + goal satisfaction

    assert _has(g, "paul", "is_a", "mortal")        # derived by the universal law
    assert _has(g, "<goal>", "is", "satisfied")     # goal.satisfied fired
    assert len(g.nodes_named("person")) == 1        # coreference merged the two mentions




def test_canonicalize_protects_relation_nodes():
    # two "is_a" relations must NOT be merged into one (that would destroy the graph)
    g = h.Graph()
    h.load_text(g, "paul is a person\nmary is a person")
    h.run(g, h.FORM_RULES)
    h.canonicalize(g, h.FORM_RULES)
    assert len(g.nodes_named("person")) == 1        # concept merged
    assert _has(g, "paul", "is_a", "person") and _has(g, "mary", "is_a", "person")


# ---------------------------------------------------------------------------
# Rules as graph nodes (homoiconic rule representation — Prong B / b1)
# ---------------------------------------------------------------------------

def _pats(pats):
    return sorted(p.tokens() for p in pats)


def test_write_then_read_rule_round_trips():
    rule = h.Rule(
        key="is_a.transitive",
        lhs=[h.Pat("?a", "is_a", "?b"), h.Pat("?b", "is_a", "?c")],
        nac=[h.Pat("?a", "is_a", "?c")],
        rhs=[h.Pat("?a", "is_a", "?c")],
    )
    rg = h.Graph()
    h.write_rule(rg, rule)
    read = h.rules_in_graph(rg)
    assert len(read) == 1
    r = read[0]
    assert r.key == "is_a.transitive"
    assert _pats(r.lhs) == _pats(rule.lhs)
    assert _pats(r.nac) == _pats(rule.nac)
    assert _pats(r.rhs) == _pats(rule.rhs)


def test_shared_variable_is_one_node_in_fragment():
    # ?b appears as object of Pat1 and subject of Pat2 -> a single shared node
    rule = h.Rule(key="k",
                  lhs=[h.Pat("?a", "is_a", "?b"), h.Pat("?b", "is_a", "?c")],
                  rhs=[h.Pat("?a", "is_a", "?c")])
    rg = h.Graph()
    h.write_rule(rg, rule)
    assert len(rg.nodes_named("?b")) == 1           # join structure is graph structure
    assert len(rg.nodes_named("is_a")) == 3         # predicate nodes are fresh per Pat


def test_reified_rule_is_control_layer_and_pattern_predicates_are_keyed():
    # Phase 3.1 canonical shape (2.1/2.2-aligned): the whole reified fragment is CONTROL structure
    # (so a folded one-graph segregates pattern-space from fact-space by the flag), and each pattern
    # atom is in FACT SHAPE — its predicate is a graded KEY, seedable via `nodes_with_key` exactly
    # like a fact (the firmware APPLY seed path), not a bare name.
    rule = h.Rule(key="is_a.transitive",
                  lhs=[h.Pat("?a", "is_a", "?b"), h.Pat("?b", "is_a", "?c")],
                  nac=[h.Pat("?a", "is_a", "?c")],
                  rhs=[h.Pat("?a", "is_a", "?c")])
    rg = h.Graph()
    h.write_rule(rg, rule)
    # every rule-structure node (rule / var / pattern-predicate / role) is control-flagged
    assert all(rg.is_control(n) for n in rg.nodes())
    # the four `is_a` pattern-predicate nodes each carry `is_a` as a key, reachable via the key index
    isa_preds = rg.nodes_named("is_a")
    assert len(isa_preds) == 4                       # 2 lhs + 1 nac + 1 rhs
    assert all(rg.has_key(p, "is_a") for p in isa_preds)
    assert set(rg.nodes_with_key("is_a")) == set(isa_preds)
    # ... and the round-trip is still exact through the modernized shape
    back = h.rules_in_graph(rg)[0]
    assert back.key == "is_a.transitive"
    assert _pats(back.lhs) == _pats(rule.lhs) and _pats(back.nac) == _pats(rule.nac)


def test_rule_sourced_from_graph_reproduces_transitivity():
    # The engine runs identically whether the rule is a Python object or read
    # back from its graph-node form.
    rule = h.Rule(
        key="is_a.transitive",
        lhs=[h.Pat("?a", "is_a", "?b"), h.Pat("?b", "is_a", "?c")],
        nac=[h.Pat("?a", "is_a", "?c")],
        rhs=[h.Pat("?a", "is_a", "?c")],
    )
    rg = h.Graph()
    h.write_rule(rg, rule)
    sourced = h.rules_in_graph(rg)                   # rules drawn from the graph

    g = h.Graph()
    _rel(g, "alice", "is_a", "ordering_customer")
    _rel(g, "ordering_customer", "is_a", "customer")
    h.run(g, sourced)
    assert _has(g, "alice", "is_a", "customer")     # transitive closure derived


def test_graph_sourced_rule_respects_nac():
    # goal.satisfied (with a NAC) read from the graph fires once and not again.
    goal_rule = h.Rule(
        key="goal.satisfied",
        lhs=[h.Pat("?g", "target", "?x"), h.Pat("?g", "type", "?y"),
             h.Pat("?x", "is_a", "?y")],
        nac=[h.Pat("?g", "is", "satisfied")],
        rhs=[h.Pat("?g", "is", "satisfied")],
    )
    rg = h.Graph()
    h.write_rule(rg, goal_rule)
    sourced = h.rules_in_graph(rg)

    g = h.Graph()
    _rel(g, "<goal>", "target", "paul")
    _rel(g, "<goal>", "type", "mortal")
    _rel(g, "paul", "is_a", "mortal")
    assert len(h.run(g, sourced)) == 1    # fires once
    assert _has(g, "<goal>", "is", "satisfied")
    assert len(h.run(g, sourced)) == 0    # NAC blocks re-fire


def test_universal_rules_via_graph_match_python():
    # The whole UNIVERSAL_RULES set round-trips and behaves like the Python originals.
    rg = h.Graph()
    for r in h.UNIVERSAL_RULES:
        h.write_rule(rg, r)
    sourced = h.rules_in_graph(rg)
    assert {r.key for r in sourced} == {r.key for r in h.UNIVERSAL_RULES}

    g = h.Graph()
    h.load_text(g, "paul is a person\nevery person is a mortal\ngoal paul is a mortal")
    h.run(g, h.FORM_RULES)
    h.canonicalize(g, h.FORM_RULES + sourced)
    h.run(g, sourced + h.expand_universals(g))  # graph-sourced rules + the law
    assert _has(g, "paul", "is_a", "mortal")
    assert _has(g, "<goal>", "is", "satisfied")


# ---------------------------------------------------------------------------
# Relation-property meta-feature: CNL declaration -> concrete rule-nodes
# ---------------------------------------------------------------------------

def test_transitive_declaration_parses_to_rel_property():
    g = h.Graph()
    h.load_text(g, "is_a is transitive")
    h.run(g, h.RELATION_PROPERTY_FORMS)
    assert _has(g, "is_a", h.PROPERTY_REL, "transitive")


def test_transitive_declaration_expands_and_reasons():
    # "is_a is transitive" (CNL) -> a working transitivity rule that closes facts.
    decl = h.Graph()
    h.load_text(decl, "is_a is transitive")
    h.run(decl, h.RELATION_PROPERTY_FORMS)     # declaration -> rel_property
    rules = h.rules_in_graph(h.expand_relation_properties(decl))  # -> concrete rule-node
    assert any(r.key == "is_a.transitive" for r in rules)

    f = h.Graph()
    _rel(f, "alice", "is_a", "ordering_customer")
    _rel(f, "ordering_customer", "is_a", "customer")
    h.run(f, rules)
    assert _has(f, "alice", "is_a", "customer")          # derived by the generated rule


def test_symmetric_declaration_expands_and_reasons():
    decl = h.Graph()
    h.load_text(decl, "related_to is symmetric")
    h.run(decl, h.RELATION_PROPERTY_FORMS)
    rules = h.rules_in_graph(h.expand_relation_properties(decl))
    assert any(r.key == "related_to.symmetric" for r in rules)

    f = h.Graph()
    _rel(f, "x", "related_to", "y")
    journal = h.run(f, rules)
    assert _has(f, "y", "related_to", "x")               # symmetry derived
    assert len(h.run(f, rules)) == 0           # NAC -> terminates, no re-fire


def test_two_phase_declaration_then_reasoning_in_one_graph():
    # The realistic pipeline: declarations + facts in ONE graph, two phases,
    # no live rules. Phase 1 parses + expands; phase 2 reasons with the new rules.
    g = h.Graph()
    h.load_text(g, "is_a is transitive")
    h.run(g, h.RELATION_PROPERTY_FORMS)
    rules = h.rules_in_graph(h.expand_relation_properties(g))

    _rel(g, "alice", "is_a", "ordering_customer")
    _rel(g, "ordering_customer", "is_a", "customer")
    h.run(g, rules)
    assert _has(g, "alice", "is_a", "customer")


# ---------------------------------------------------------------------------
# Planning loop — goal -> plan -> act -> replan, entirely as rules (no planner)
# ---------------------------------------------------------------------------

def _coffee():
    """The reference planning domain (docs/planning_design.md). `buy_latte` is a DEAD
    option: it achieves the goal but needs `money`, which nothing produces."""
    g = h.Graph()
    h.seed_operator(g, "make_coffee", pre=["water", "beans"], add=["have_coffee"])
    h.seed_operator(g, "fetch_water", add=["water"])
    h.seed_operator(g, "get_beans", add=["beans"])
    h.seed_operator(g, "buy_latte", pre=["money"], add=["have_coffee"])
    h.seed_state(g, [])
    h.seed_goal(g, "have_coffee")
    return g


def _mark(g, s, rel, o="<yes>"):
    return any(g.name(r) == rel and g.name(ob) == o
               for si in g.nodes_named(s) for r, ob in g.relations_from(si))












# ---- multi-option ranked commitment (phase C): pick the cheapest viable rival -----

def _coffee_two_water(fetch_cost=1, buy_cost=5):
    """Coffee with TWO ways to get water: `fetch_water` (cheap) and `buy_water`
    (expensive). Both are viable producers of `water`, so commitment must RANK them by
    the fact-layer cost criterion and pick one — not race and commit both."""
    g = h.Graph()
    h.seed_operator(g, "make_coffee", pre=["water", "beans"], add=["have_coffee"])
    h.seed_operator(g, "fetch_water", add=["water"], cost=fetch_cost)
    h.seed_operator(g, "buy_water", add=["water"], cost=buy_cost)
    h.seed_operator(g, "get_beans", add=["beans"])
    h.seed_state(g, [])
    h.seed_goal(g, "have_coffee")
    return g












# ---------------------------------------------------------------------------
# Procedures — named, ordered action sequences -> planner operators (procedure.py)
# ---------------------------------------------------------------------------

def _record(order, names):
    """An action-tool registry that appends each op's name to `order` as it runs (and still
    materializes the declared effect, so divergence detection stays consistent)."""
    def make(nm):
        def f(graph, op_id):
            order.append(nm)
            h.simulate_effects(graph, op_id)
        return f
    return {nm: make(nm) for nm in names}
















def test_nac_independent_negations_block_separately():
    # `not A and not B` (no shared free var) is ¬A ∧ ¬B: EITHER alone blocks. A conjunctive
    # NAC over a SHARED free var stays one group (¬∃x: A(x) ∧ B(x)) — the two readings the
    # planner relies on (readiness gate vs commitment's one-per-need guard).
    from ugm.cnl.rewriter import run
    # independent: A present, B absent -> still blocked (B alone would NOT block under the old
    # conjunctive reading, which required BOTH A and B present).
    g = h.Graph()
    x = g.add_node("x"); g.add_relation(x, "p", g.add_node("<yes>"))
    g.add_relation(x, "a", g.add_node("m"))                     # A holds; B (`x b <yes>`) absent
    r = h.Rule(key="t", lhs=[h.Pat("?x", "p", "<yes>")],
               nac=[h.Pat("?x", "a", "?any"), h.Pat("?x", "b", "<yes>")],
               rhs=[h.Pat("?x", "ok", "<yes>")])
    run(g, [r], provenance=False)
    assert not _mark(g, "x", "ok")                              # ¬A alone blocks


# ---- external cost lookup: rules DEMAND a value, a tool fetches it (vision §6/§8) -----
# Cost lives OUTSIDE the KB (a price DB). A rule emits a request token; the generic
# dispatcher runs the registered lookup tool; the tool emits result/error FACTS; the
# commitment rules select over them. Freshness is §5: a new fetch SUPERSEDES (never
# deletes) and is read through a guard. See harneskills/external.py + planning.py.

def _coffee_ext():
    """Coffee where the two water sources are PRICED EXTERNALLY (no in-KB cost): the
    planner must fetch their prices on demand to rank them."""
    g = h.Graph()
    h.seed_operator(g, "make_coffee", pre=["water", "beans"], add=["have_coffee"])
    h.seed_operator(g, "get_beans", add=["beans"])
    h.seed_operator(g, "fetch_water", add=["water"], priced=True)
    h.seed_operator(g, "deliver_water", add=["water"], priced=True)
    h.seed_state(g, [])
    h.seed_goal(g, "have_coffee")
    return g


def _teardown_replan(g):
    """Trigger a control teardown (a replan) in isolation."""
    replan = g.add_node("<replan>")
    g.add_relation(replan, "active", g.nodes_named("<yes>")[0])
    h.run_rules(g, h.TEARDOWN_RULES)
    for n in list(g.nodes_named("<replan>")):
        g.remove_node(n)


def _current_prices(g, op):
    return [h.result_value(g, r) for r in h.results_for(g, "price", g.nodes_named(op)[0])]


def test_external_freshness_supersedes_and_guarded_read():
    # the §5 freshness primitive: a newer result SUPERSEDES the old (added marker, no
    # deletion); "current" = the result nothing supersedes (the guarded read).
    g = h.Graph()
    o = g.add_node("widget")
    r1 = h.emit_result(g, "price", o, "5")
    assert not h.is_superseded(g, r1)
    r2 = h.emit_result(g, "price", o, "2")               # newer value
    assert h.is_superseded(g, r1) and not h.is_superseded(g, r2)
    assert h.result_value(g, h.results_for(g, "price", o)[0]) == "2"   # current = newest
    assert g.has(r1)                                     # old fact NOT deleted (still there)










# ---- real §8 action tools at the act/observe boundary (vision §8) --------------------
# `act` runs a REAL action tool per operator when one is registered (it performs and
# emits the OBSERVED effect), else simulates the declared effect. Expected (declared) vs
# observed (real) divergence is now genuine, not just injectable.







# ---- the rule-linter: check the RULES against the system's invariants (vision §2/§5) -











# ---- universal constraint schemas: detect inconsistency as <contradiction> markers ---
# A domain-independent property declared on a relation/category expands (via the existing
# relation-property tool) into rules that DERIVE a <contradiction> marker on any offending
# configuration, for ANY domain via is_a generalization. Detection only ADDS a marker
# (vision §5: never reject/delete); `contradictions`/`is_consistent` are the guarded read.

def _detect(g):
    """Expand the declarations in g into rules and run them (+ is_a transitivity)."""
    rules = h.rules_in_graph(h.expand_relation_properties(g))
    h.run(g, rules + h.UNIVERSAL_RULES)
    return g


def _declare(g, subj, rel, obj):
    def node(name):
        return g.nodes_named(name)[0] if g.nodes_named(name) else g.add_node(name)
    g.add_relation(node(subj), rel, node(obj))


def test_constraint_disjoint_detects_category_clash_via_is_a():
    # `dog disjoint_from cat`; `rex is_a poodle`, `poodle is_a dog`, `rex is_a cat`. The
    # clash is only visible AFTER is_a transitivity derives `rex is_a dog` — the universal
    # law fires through generalization, with no rex-specific rule.
    g = h.Graph()
    _declare(g, "dog", "disjoint_from", "cat")
    _declare(g, "rex", "is_a", "poodle")
    _declare(g, "poodle", "is_a", "dog")
    _declare(g, "rex", "is_a", "cat")
    _detect(g)
    assert not h.is_consistent(g)
    assert "rex" in {a for c in h.contradictions(g) for a in c["about"]}


def test_constraint_disjoint_clean_without_clash():
    g = h.Graph()
    _declare(g, "dog", "disjoint_from", "cat")
    _declare(g, "rex", "is_a", "dog")           # only a dog — no clash
    _detect(g)
    assert h.is_consistent(g)


def test_constraint_asymmetric_and_irreflexive():
    g = h.Graph()
    _declare(g, "beats", "rel_property", "asymmetric")
    _declare(g, "x", "beats", "y")
    _declare(g, "y", "beats", "x")              # mutual -> violation
    _detect(g)
    assert not h.is_consistent(g)
    assert {"x", "y"} <= {a for c in h.contradictions(g) for a in c["about"]}
    # one-directional is fine
    g2 = h.Graph()
    _declare(g2, "beats", "rel_property", "asymmetric")
    _declare(g2, "x", "beats", "y")
    assert h.is_consistent(_detect(g2))


def test_constraint_acyclic_detects_cycle_through_closure():
    # acyclic = transitive + irreflexive: the cycle a->b->c->a only shows up as a self-loop
    # `a part_of a` AFTER transitive closure runs, which the irreflexive check then flags.
    g = h.Graph()
    _declare(g, "part_of", "rel_property", "acyclic")
    _declare(g, "a", "part_of", "b")
    _declare(g, "b", "part_of", "c")
    _declare(g, "c", "part_of", "a")
    _detect(g)
    assert not h.is_consistent(g)
    # a DAG is clean
    g2 = h.Graph()
    _declare(g2, "part_of", "rel_property", "acyclic")
    _declare(g2, "a", "part_of", "b")
    _declare(g2, "b", "part_of", "c")
    assert h.is_consistent(_detect(g2))


def test_constraint_cnl_declarations_parse_and_detect():
    # declared in CNL, detected end to end: `liquid is disjoint from solid` + a clashing fact.
    g = h.Graph()
    h.tokenize(g, "liquid is disjoint from solid")
    h.run(g, h.FORM_RULES + h.CONSTRAINT_FORMS)
    assert any(g.name(r) == "disjoint_from" for n in g.nodes() for r, _ in g.relations_from(n))
    ice = g.add_node("ice")
    g.add_relation(ice, "is_a", g.add_node("liquid"))
    g.add_relation(ice, "is_a", g.add_node("solid"))
    _detect(g)
    assert not h.is_consistent(g)
    assert "ice" in {a for c in h.contradictions(g) for a in c["about"]}


# ---- Session: the stateful user-facing engine API behind the TUI/CLI -----------------





















# ---- demand-driven SELECTIVE coreference on the Session query path (vision §3) -----------
# The KB is lazy: a QUESTION is the demand that pulls coreference of the queried entity's
# mentions (only those — selective, bounded). A rule turns the demand into a <coref-request>;
# the dumb dispatcher resolves it by reasoning (provably-distinct mentions are rejected), and
# the genuinely ambiguous residue is referred to the user via an optional Oracle.





# ---- context-scoped, additive coreference (replaces the destructive `canonicalize` merge) ----
# A bare reference is underspecified ("monday" means monday-of-some-week); same name denotes the
# same thing only WITHIN a shared context. `coref_in_context` links same-named mentions with an
# additive `same_as` (never a merge) in the DEFAULT (gap-filled) context, but keeps mentions in
# DIFFERENT contexts separate — so a name coincidence across contexts is no longer a contradiction.

def test_coref_in_context_links_default_but_separates_by_context():
    g = h.Graph()
    g.add_node("monday"); g.add_node("monday")           # no context -> default shared
    h.coref_in_context(g, h.FORM_RULES)
    assert _has(g, "monday", "same_as", "monday")        # the gap-fill links them

    g2 = h.Graph()
    m1, m2 = g2.add_node("monday"), g2.add_node("monday")
    g2.add_relation(m1, "in", g2.add_node("week1"))
    g2.add_relation(m2, "in", g2.add_node("week2"))
    h.coref_in_context(g2, h.FORM_RULES)
    assert not _has(g2, "monday", "same_as", "monday")   # different weeks -> NOT linked


def test_coref_context_defeats_a_false_asymmetry_contradiction():
    # "monday before tuesday" + "tuesday before monday" is an asymmetry violation ONLY if the two
    # mondays (and tuesdays) are the same day. In different weeks they are not coreferred, so there
    # is NO contradiction; with no context (the default gap-fill = one week) there IS one.
    def build(contextualize):
        g = h.Graph()
        g.add_relation(g.add_node("before"), "rel_property", g.add_node("asymmetric"))
        m1, t1, m2, t2 = (g.add_node("monday"), g.add_node("tuesday"),
                          g.add_node("monday"), g.add_node("tuesday"))
        if contextualize:
            w1, w2 = g.add_node("week1"), g.add_node("week2")
            for n in (m1, t1): g.add_relation(n, "in", w1)
            for n in (m2, t2): g.add_relation(n, "in", w2)
        g.add_relation(m1, "before", t1)                 # monday before tuesday
        g.add_relation(t2, "before", m2)                 # tuesday before monday
        h.coref_in_context(g, h.FORM_RULES)
        h.run(g, h.same_as_rules(["before"]) + h.UNIVERSAL_RULES)
        h.run(g, h.rules_in_graph(h.expand_relation_properties(g)))
        return g

    assert h.is_consistent(build(contextualize=True))    # different weeks -> defeated
    assert not h.is_consistent(build(contextualize=False))  # one week -> real violation




# ---- grammar coverage: generic binary relations (declare a relation -> a form for it) -





# ---- grammar coverage: n-ary relations (reify a 3+-participant statement as an event) -----

def _event_roles(g, pred):
    """The role->participant maps of every reified `event` whose `pred` is `pred`."""
    out = []
    for ev in g.nodes_named("event"):
        roles = {g.name(rel): g.name(o) for rel, o in g.relations_from(ev)}
        if roles.get("pred") == pred:
            out.append(roles)
    return out












# ---- coreference-as-rules (vision §3): additive `same_as`, validated in principle --------
# The principled alternative to the destructive `canonicalize` merge: link same-named
# mentions with an ADDITIVE `same_as` relation and PROPAGATE facts across it. Monotone, so it
# never corrupts (unlike merge), and `same_as` can later be wired SELECTIVELY. NOTE: not yet
# used in `Session` — propagation re-run per line over a densely-linked graph is too slow
# under the engine's un-indexed matching (needs vision §11 locality-Rete). Proven here for
# the simple case so the mechanism is ready when the engine supports it.

def test_same_as_coreference_composes_without_merge():
    g = h.Graph()
    soc, p1 = g.add_node("socrates"), g.add_node("person")
    g.add_relation(soc, "is_a", p1)                      # socrates is_a person (mention 1)
    p2, mortal = g.add_node("person"), g.add_node("mortal")
    g.add_relation(p2, "is_a", mortal)                   # person is_a mortal (mention 2)
    h.wire_same_as(g, h.FORM_RULES)                      # ADDITIVE: p1 same_as p2 (no merge)
    h.run(g, h.same_as_rules(["is_a"]) + h.UNIVERSAL_RULES)
    # reasoning composes ACROSS the link, yet the two mentions stay distinct (not merged)
    assert any(g.name(r) == "is_a" and g.name(o) == "mortal"
               for s in g.nodes_named("socrates") for r, o in g.relations_from(s))
    assert len(g.nodes_named("person")) == 2


# ---------------------------------------------------------------------------
# In-graph justifications — provenance as nodes (docs/coreference_design.md §4)
# ---------------------------------------------------------------------------

def test_firing_emits_in_graph_justification():
    # a rule firing materializes J --proves--> created fact, J --uses--> each premise.
    g = h.Graph()
    _rel(g, "alice", "is_a", "ordering_customer")
    _rel(g, "ordering_customer", "is_a", "customer")
    h.run(g, h.UNIVERSAL_RULES)
    rel = next(r for r in g.out(g.nodes_named("alice")[0])
               if g.name(r) == "is_a" and any(g.name(o) == "customer" for o in g.out(r)))
    js = h.support_js(g, rel)
    assert js and any(h.is_justification(g.name(j)) for j in js)
    j = h.rule_support_j(g, rel)
    assert h.rule_of_j(g, j) == "is_a.transitive"
    assert len(h.premises_of(g, j)) == 2                 # the two is_a premises
    # provenance is invisible to facts/locality: a base fact has no rule-justification
    base = next(r for r in g.out(g.nodes_named("ordering_customer")[0]) if g.name(r) == "is_a")
    assert h.rule_support_j(g, base) is None             # asserted -> '(given)'


def test_explain_reads_provenance_not_a_journal():
    # explanation is a traversal of proves/uses; the journal arg is ignored.
    g = h.Graph()
    h.load_text(g, "paul is a person")
    mortal = h.Rule(key="mortal", lhs=[h.Pat("?a", "is_a", "person")],
                    rhs=[h.Pat("?a", "is_a", "mortal")])
    h.run(g, h.FORM_RULES + [mortal])
    trace = h.explain(g, None, None, "paul", "is_a", "mortal")   # journal/rules = None
    assert trace[0] == "paul is_a mortal  <- mortal"
    assert any("paul is_a person  <- form.is_a" in line for line in trace)
    assert any("(given)" in line for line in trace)


# ---------------------------------------------------------------------------
# On-demand evaluation — transitivity is derived only where demanded (selective)
# ---------------------------------------------------------------------------

def test_transitivity_on_demand_is_selective():
    g = h.Graph()
    _rel(g, "a", "is_a", "b")
    _rel(g, "b", "is_a", "c")
    _rel(g, "c", "is_a", "d")
    h.seed_demand(g, "a", "d")                           # demand: a is_a d ?
    h.run(g, h.DEMAND_TRANSITIVITY)
    assert _has(g, "a", "is_a", "d")                     # derived ON DEMAND
    assert _has(g, "b", "is_a", "d")                     # via the spawned sub-demand
    assert not _has(g, "a", "is_a", "c")                 # NOT demanded -> never derived (lazy)


# ---------------------------------------------------------------------------
# Reversible retraction — quarantine + cascade (the truth-maintenance layer)
# ---------------------------------------------------------------------------

def test_retract_withdraws_derived_consequences():
    g = h.Graph()
    _rel(g, "a", "r", "b")
    chain = h.Rule(key="chain", lhs=[h.Pat("?x", "r", "?y")], rhs=[h.Pat("?y", "r2", "?x")])
    h.run(g, [chain])
    assert _has(g, "b", "r2", "a")                       # derived, justified in-graph
    premise = next(r for r in g.out(g.nodes_named("a")[0]) if g.name(r) == "r")
    h.retract(g, premise)                                # rule-based cascade (RETRACT_RULES)
    assert not _has(g, "a", "r", "b")                    # premise hidden by interposition
    assert not _has(g, "b", "r2", "a")                   # its consequence lost support -> hidden


# ---------------------------------------------------------------------------
# Selective coreference ON DEMAND — two genuinely distinct Pauls stay separate
# ---------------------------------------------------------------------------

def test_coreference_on_demand_keeps_two_pauls_separate():
    # Two distinct `paul` mentions in incompatible categories. Hypothesizing they corefer
    # makes one paul both teacher and student (disjoint) -> contradiction -> the link is
    # RETRACTED with its consequences, and the two pauls stay separate. Disambiguation by
    # reasoning (vision §3), not a same-name heuristic.
    g = h.Graph()
    p1, p2 = g.add_node("paul"), g.add_node("paul")
    g.add_relation(p1, "is_a", g.add_node("teacher"))
    g.add_relation(p2, "is_a", g.add_node("student"))
    g.add_relation(g.nodes_named("teacher")[0], "disjoint_from", g.nodes_named("student")[0])

    h.resolve_coref(g, "paul")
    assert len(g.nodes_named("paul")) == 2               # NEVER merged (additive)
    assert not _has(g, "paul", "same_as", "paul")        # clash caught BEFORE linking
    assert h.is_consistent(g)                            # no contradiction ever produced
    assert h.is_rejected(g, p1, p2)                      # the rejection is recorded

    def cats(n):
        return sorted(g.name(o) for r, o in g.relations_from(n) if g.name(r) == "is_a")
    assert cats(p1) == ["teacher"] and cats(p2) == ["student"]   # each keeps only its own


def test_coreference_on_demand_keeps_compatible_link():
    # No contradiction -> the hypothesised link STANDS and reasoning composes across it.
    g = h.Graph()
    p1, p2 = g.add_node("paul"), g.add_node("paul")
    g.add_relation(p1, "is_a", g.add_node("teacher"))
    g.add_relation(p2, "is_a", g.add_node("mortal"))
    h.resolve_coref(g, "paul")
    assert _has(g, "paul", "same_as", "paul")            # link committed (compatible)
    assert not h.is_rejected(g, p1, p2)


# ---------------------------------------------------------------------------
# Anchor-delta rule activation (vision §11, incremental Rete) — Rewriter
# ---------------------------------------------------------------------------

from collections import Counter


def _fact_triples(g):
    """Multiset of domain relation triples by NAME. Two runs that derive the same facts
    have equal multisets, regardless of fresh node ids. `relations_from` on a relation
    node yields spurious 2-hops, so we drop subjects that are themselves relation nodes."""
    raw, rels = [], set()
    for nid in g.nodes():
        for rid, oid in g.relations_from(nid):
            raw.append((nid, rid, oid))
            rels.add(rid)
    c = Counter()
    for s, rid, oid in raw:
        if s in rels:                         # s is a relation node -> spurious path, skip
            continue
        c[(g.name(s), g.name(rid), g.name(oid))] += 1
    return c


def _chain(n):
    g = h.Graph()
    ids = [g.add_node(f"a{i}") for i in range(n + 1)]
    for i in range(n):
        g.add_relation(ids[i], "is_a", ids[i + 1])
    return g


def test_rule_anchors_and_wildcards():
    transitive = h.UNIVERSAL_RULES[0]                     # ?a is_a ?b, ?b is_a ?c
    preds, wild = rewriter._rule_anchors(transitive)
    assert preds == frozenset({"is_a"}) and not wild
    # a variable predicate forces wildcard (matches relations of any name)
    var_pred = h.Rule(key="vp", lhs=[h.Pat("?s", "?p", "?o")], rhs=[h.Pat("?s", "seen", "?o")])
    assert rewriter._rule_anchors(var_pred) == (frozenset(), True)
    # a graded rule is wildcard (a pure embedding change can flip applicability)
    graded = h.Rule(key="gr", lhs=[h.Pat("?x", "is_a", "thing")],
                    graded=[h.GradedCondition("?x", {"urgent": 1.0}, 0.5)],
                    rhs=[h.Pat("?x", "is", "hot")])
    _, wild = rewriter._rule_anchors(graded)
    assert wild


def test_optimized_engine_matches_naive_engine_identical_results():
    """The standing correctness guard: the optimized engine (anchor-delta activation +
    semi-naive matching) derives EXACTLY the same facts (and the same number of firings) as
    the fully-naive engine (both off), across several banks."""
    cases = [
        (lambda: _chain(12), h.UNIVERSAL_RULES, dict(max_steps=400)),
        (_clique_graph, h.same_as_rules(["is_a"]), dict(max_steps=400)),
        (_mixed_domain_graph, h.UNIVERSAL_RULES + h.same_as_rules(["is_a", "wants"]),
         dict(max_steps=400)),
    ]
    for build, rules, kw in cases:
        g_fast = build()
        g_naive = g_fast.copy()
        j_fast = h.run(g_fast, rules, activation=True, semi_naive=True, **kw)
        j_naive = h.run(g_naive, rules, activation=False, semi_naive=False, **kw)
        assert _fact_triples(g_fast) == _fact_triples(g_naive)
        assert len(j_fast) == len(j_naive)


def _clique_graph():
    g = h.Graph()
    ms = [g.add_node("thing") for _ in range(8)]
    base = g.add_node("entity")
    for m in ms[1:]:
        g.add_relation(ms[0], "same_as", m)
    g.add_relation(ms[0], "is_a", base)
    return g


def _mixed_domain_graph():
    g = h.Graph()
    a = g.add_node("alice"); cust = g.add_node("customer"); person = g.add_node("person")
    van = g.add_node("vanilla")
    g.add_relation(a, "is_a", cust)
    g.add_relation(cust, "is_a", person)
    g.add_relation(a, "wants", van)
    return g


def test_seed_from_ground_never_scans_for_a_free_pattern():
    """Seed-from-ground (docs/walkers_and_locality.md §1): a pattern with NO ground position
    (all of s/p/o free) yields nothing — there is no whole-scope scan. A literal anchor on the
    same shape matches normally. (A variable-predicate rule is therefore inert eagerly; it
    would need a demand walker to supply a binding.)"""
    g = h.Graph()
    a, b = g.add_node("a"), g.add_node("b")
    g.add_relation(a, "knows", b)
    assert h.match(g, [h.Pat("?s", "?p", "?o")]) == []        # all free -> no seed -> nothing
    assert len(h.match(g, [h.Pat("?s", "knows", "?o")])) == 1  # literal predicate anchors it


def test_seed_from_ground_prefers_the_rarest_anchor():
    """The seed is the most selective GROUND position. A rule `?x is_a rare` matches its one
    `rare` object even though `is_a` is common — i.e. it seeds from the df-1 object, not the
    df-many predicate. (Behavioural proxy: it still finds the match; the cost win is measured
    separately.)"""
    g = h.Graph()
    rare = g.add_node("rare")
    for i in range(20):
        g.add_relation(g.add_node(f"e{i}"), "is_a", g.add_node("common"))
    hit = g.add_node("hit")
    g.add_relation(hit, "is_a", rare)
    res = h.match(g, [h.Pat("?x", "is_a", "rare")])
    assert len(res) == 1 and g.name(res[0]["?x"]) == "hit"


def test_activation_skips_irrelevant_rules_on_a_change():
    """Many rules with distinct anchor predicates: a one-line change wakes only the rules
    whose anchor it touches. Measured by counting match attempts (filter on vs off)."""
    # 30 rules each anchored on a distinct predicate p{i}: ?x p{i} ?y => ?x q{i} ?y
    rules = [h.Rule(key=f"r{i}", lhs=[h.Pat("?x", f"p{i}", "?y")],
                    rhs=[h.Pat("?x", f"q{i}", "?y")]) for i in range(30)]
    g = h.Graph()
    # one pre-existing fact per predicate (already derived in a prior run), then a fresh
    # change touching ONLY p7: a NEW p7 fact whose q7 has not been derived yet.
    for i in range(30):
        s = g.add_node(f"s{i}"); o = g.add_node(f"o{i}")
        g.add_relation(s, f"p{i}", o)
        if i != 7:
            g.add_relation(s, f"q{i}", o)                # already-derived (no new match)
    s7 = g.nodes_named("s7")[0]
    new = g.add_node("o7b")
    rel = g.add_relation(s7, "p7", new)

    calls = {"n": 0}
    orig = rewriter.match_with_premises
    def counting(*a, **k):
        calls["n"] += 1
        return orig(*a, **k)
    rewriter.match_with_premises = counting
    try:                       # semi_naive off so match_with_premises count isolates activation
        calls["n"] = 0
        h.run(g.copy(), rules, activation=False, semi_naive=False, max_steps=10, seeds=[s7, new, rel])
        off = calls["n"]
        calls["n"] = 0
        h.run(g.copy(), rules, activation=True, semi_naive=False, max_steps=10, seeds=[s7, new, rel])
        on = calls["n"]
    finally:
        rewriter.match_with_premises = orig
    # first step considers all 30 (no prior delta); thereafter activation wakes only r7.
    assert on < off
    assert off >= 30           # unfiltered re-attempts every rule each step


# ---------------------------------------------------------------------------
# Planning-problem CNL surface — operators + state + goal in one .cnl file
# (harneskills/planning_kb.py). Lowers to the SAME edges as the Python seeders.
# ---------------------------------------------------------------------------

import pathlib as _pathlib

_COFFEE_KB = _pathlib.Path(__file__).resolve().parent.parent / "corpus" / "coffee_kb.cnl"


def _edges(g):
    return sorted((g.name(a), g.name(b)) for a, b in g.edges())










_BARISTA_KB = _pathlib.Path(__file__).resolve().parent.parent / "corpus" / "barista_kb.cnl"





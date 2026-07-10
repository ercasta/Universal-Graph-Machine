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


def test_degree_scale_is_kb_data_declarable_and_overridable():
    # The adverb->degree scale lives in the KB as DATA (`very is 0.8`), not a Python config
    # dict: the defaults read back, a brand-new adverb is declarable, and a default is
    # overridable — all driving the embedding write, with no code change. (No ADVERB_THRESHOLDS.)
    assert h.degree_thresholds(h.Session().kb) == {"very": 0.8, "somewhat": 0.5, "slightly": 0.3}

    g = h.Graph()                                            # a NEW adverb, declared in CNL
    h.load_facts(g, "extremely is 0.95\nurgent is gradable\nbob is extremely urgent\n")
    assert h.degree_thresholds(g)["extremely"] == 0.95
    assert g.get_embedding(g.nodes_named("bob")[0]) == {"urgent": 0.95}

    g2 = h.Graph()                                           # OVERRIDE a default degree
    h.load_facts(g2, "very is 0.6\nurgent is gradable\nalice is very urgent\n")
    assert g2.get_embedding(g2.nodes_named("alice")[0]) == {"urgent": 0.6}


def test_graded_banks_lint_clean():
    # the generated graded write-rules and rule-grammar forms satisfy the linter invariants.
    g = h.Graph()
    h.load_facts(g, "extremely is 0.95\n")
    assert h.lint_rules(h.graded_rules(g)) == []
    assert h.lint_rules(h.degree_grammar_forms(g)) == []


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


def test_session_reasons_with_declared_relation_in_rule_body():
    # end-to-end through the lazy Session: declare a relation, use it in a rule body,
    # assert a matching fact, and the KB answers the derived question.
    s = h.Session()
    assert s.submit("visits is a relation").recognized
    assert s.submit("?x is happy when ?x visits dog").recognized
    assert s.submit("alice visits dog").recognized
    assert s.submit("is alice happy").answer == ["yes"]
    assert s.submit("is bob happy").answer == ["no"]


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


def test_multiword_entity_decomposes_and_answers():
    s = h.Session()
    assert set(s.submit("the bald eagle is a bird").new_facts) == {"eagle is bald", "eagle is_a bird"}
    assert s.submit("is the bald eagle a bird").answer == ["yes"]
    assert s.submit("who is a bird").answer == ["eagle is_a bird"]


def test_copula_state_question_not_over_merged():
    # "is alice happy" must stay subject + predicate (two tokens), not decompose to "happy is alice".
    s = h.Session()
    assert s.submit("alice is happy").recognized
    assert s.submit("is alice happy").answer == ["yes"]
    assert s.submit("is alice sad").answer == ["no"]


def test_determiner_dropped_but_fixed_phrase_the_is_kept():
    # "the" in the fixed keyword phrase "is the same as" is NOT a determiner to strip.
    s = h.Session()
    s.load_text(
        "clark is the same as superman\n"
        "clark is a hero\n"
    )
    assert s.submit("is superman a hero").answer == ["yes"]


def test_quantifier_over_multiword_entity():
    # "every bald eagle is a bird" -> a universal law over the decomposed head; the attribute
    # `eagle is bald` rides along.
    s = h.Session()
    assert set(s.submit("every bald eagle is a bird").new_facts) == \
        {"eagle every_is_a bird", "eagle is bald"}
    assert s.submit("the bald eagle is a bald eagle").recognized
    assert s.submit("is the bald eagle a bird").answer == ["yes"]


def test_multiword_entity_across_relation_and_decomposition():
    s = h.Session()
    assert s.submit("visits is a relation").recognized
    assert set(s.submit("the bald eagle visits the tall tree").new_facts) == \
        {"eagle visits tree", "eagle is bald", "tree is tall"}
    assert s.submit("who visits the tall tree").answer == ["eagle visits tree"]


def test_multi_adjective_decomposes_right_to_left_into_head():
    # "the big bald eagle" -> head `eagle` carrying BOTH modifiers (correct associativity),
    # on both subject and object of a relation.
    s = h.Session()
    s.submit("chases is a relation")
    facts = set(s.submit("the big bald eagle chases the small cat").new_facts)
    assert facts == {"eagle chases cat", "eagle is big", "eagle is bald", "cat is small"}


# ---------------------------------------------------------------------------
# Anaphoric pronouns — resolve to the discourse subject (Tier 3b)
# ---------------------------------------------------------------------------

def test_pronoun_resolves_to_prior_subject_and_composes():
    # "it" -> the subject of the previous line ("eagle"); resolves to the same one entity.
    s = h.Session()
    assert s.submit("eagle is a bird").recognized
    assert s.submit("it is happy").new_facts == ["eagle is happy"]
    assert s.submit("who is happy").answer == ["eagle is happy"]


def test_pronoun_in_question_resolves_to_subject():
    s = h.Session()
    assert s.submit("alice is a person").recognized
    assert s.submit("is she a person").answer == ["yes"]


def test_object_pronoun_across_relation():
    # "it" in object position resolves to the prior subject ("cat").
    s = h.Session()
    assert s.submit("chases is a relation").recognized
    assert s.submit("cat is a pet").recognized
    assert s.submit("dog chases it").new_facts == ["dog chases cat"]
    assert s.submit("who chases cat").answer == ["dog chases cat"]


def test_pronoun_with_no_antecedent_stays_literal():
    # First line: nothing to resolve to, so "it" is a literal entity (an unresolved reference).
    s = h.Session()
    assert s.submit("it is a bird").new_facts == ["it is_a bird"]


def test_pronoun_topic_updates_across_lines():
    # The discourse subject advances: after "dog ...", "it" resolves to dog, not eagle.
    s = h.Session()
    s.submit("eagle is a bird")
    s.submit("dog is a pet")
    assert s.submit("it is happy").new_facts == ["dog is happy"]


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


def test_ice_cream_routing_no_planner():
    import importlib.util
    import pathlib
    p = pathlib.Path(__file__).resolve().parent.parent / "examples" / "ice_cream.py"
    spec = importlib.util.spec_from_file_location("ice_cream_demo", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    g = m.build_scenario()
    m.serve_all(g)
    res = m.outcomes(g)
    assert res["alice"] == "served express"        # graded urgency -> express route
    assert res["bob"] == "served regular"
    assert res["carol"] == "offered alternative"    # out of stock


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


def test_planning_plan_exists_and_orders():
    # the fixpoint of PLANNING_RULES is a plan: the relevant operators are chosen and
    # ordered (producers before consumers), with NO search.
    g = _coffee()
    h.plan(g)
    assert _mark(g, "make_coffee", "chosen")
    assert _mark(g, "fetch_water", "chosen")
    assert _mark(g, "get_beans", "chosen")
    assert _mark(g, "have_coffee", "reachable")
    # ordering: water/beans producers come before the consumer make_coffee
    assert _mark(g, "fetch_water", "before", "make_coffee")
    assert _mark(g, "get_beans", "before", "make_coffee")
    assert not _mark(g, "make_coffee", "before", "fetch_water")


def test_planning_dead_option_never_viable():
    # an operator whose precondition never connects to the current state keeps a block
    # that never clears -> never viable -> never chosen (monotone, no backtracking).
    g = _coffee()
    h.plan(g)
    assert _mark(g, "buy_latte", "blocked_by", "money")
    assert not _mark(g, "buy_latte", "viable")
    assert not _mark(g, "buy_latte", "chosen")
    assert not _mark(g, "money", "reachable")


def test_planning_execution_reaches_goal():
    # token-passing execution drives the observed state to the goal.
    g = _coffee()
    assert h.solve(g) == "done"
    assert _mark(g, "<now>", "true", "have_coffee")
    assert h.goal_satisfied(g)
    assert _mark(g, "make_coffee", "done")


def test_planning_divergence_triggers_replan_and_recovers():
    # inject a one-shot failure: make_coffee runs but its effect is withheld. The
    # divergence is detected, control is torn down, and the SAME rules re-plan and
    # re-execute from the new state -> goal still reached. (A single pass could not
    # recover a withheld effect, so reaching "done" proves the replan path ran.)
    g = _coffee()
    assert h.solve(g, failures={"make_coffee": 1}) == "done"
    assert _mark(g, "<now>", "true", "have_coffee")


def test_planning_teardown_clears_control_keeps_facts():
    # the replan teardown drops ALL control scaffolding but keeps the fact layer
    # (observed state, operators, goal). Verified in isolation on a planned graph.
    g = _coffee()
    h.plan(g)
    assert _mark(g, "make_coffee", "chosen")          # control present
    # trigger teardown directly
    replan = g.add_node("<replan>")
    g.add_relation(replan, "active", g.nodes_named("<yes>")[0])
    h.run_rules(g, h.TEARDOWN_RULES)
    # control gone
    assert not _mark(g, "make_coffee", "chosen")
    assert not _mark(g, "fetch_water", "before", "make_coffee")
    assert not _mark(g, "have_coffee", "reachable")
    # facts kept
    assert _mark(g, "make_coffee", "add", "have_coffee")
    assert _mark(g, "make_coffee", "pre", "water")
    assert _mark(g, "<goal>", "want", "have_coffee")


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


def test_planning_ranked_commitment_picks_cheapest():
    # two viable producers of `water`; the cheaper one is chosen, the costlier dominated.
    # The CRITERION (cost) is a fact; `rank_by_cost` (a tool) emits the `cheaper_than`
    # comparison result; the rules SELECT over it (the standing guardrail).
    g = _coffee_two_water(fetch_cost=1, buy_cost=5)
    h.plan(g)
    assert _mark(g, "fetch_water", "cheaper_than", "buy_water")   # tool's result (a fact)
    assert _mark(g, "buy_water", "viable")                        # both are viable...
    assert _mark(g, "fetch_water", "viable")
    assert _mark(g, "buy_water", "dominated")                     # ...but the costlier loses
    assert not _mark(g, "fetch_water", "dominated")
    assert _mark(g, "fetch_water", "chosen")                      # only the cheapest commits
    assert not _mark(g, "buy_water", "chosen")
    assert _mark(g, "make_coffee", "chosen")


def test_planning_ranked_commitment_reversed_cost():
    # flip the costs: now buying is cheaper, so commitment must flip too (selection is
    # driven by the fact, not by operator declaration order).
    g = _coffee_two_water(fetch_cost=5, buy_cost=1)
    h.plan(g)
    assert _mark(g, "buy_water", "chosen")
    assert not _mark(g, "fetch_water", "chosen")
    assert _mark(g, "fetch_water", "dominated")


def test_planning_ranked_commitment_solves_with_cheapest():
    # the full loop reaches the goal, executing the cheaper water source (not both).
    g = _coffee_two_water(fetch_cost=1, buy_cost=5)
    assert h.solve(g) == "done"
    assert _mark(g, "fetch_water", "done")
    assert not _mark(g, "buy_water", "done")


def test_planning_equal_cost_is_an_honest_tie():
    # equal cost = NO criterion to separate the rivals. Neither dominates the other, so
    # both are `best` and both commit — an honest over-commitment, NOT a fabricated pick
    # (choosing among true equals with no criterion would be fabrication, not control).
    g = _coffee_two_water(fetch_cost=2, buy_cost=2)
    h.plan(g)
    assert not _mark(g, "fetch_water", "cheaper_than", "buy_water")
    assert not _mark(g, "buy_water", "cheaper_than", "fetch_water")
    assert _mark(g, "fetch_water", "chosen") and _mark(g, "buy_water", "chosen")


def test_planning_cheaper_than_is_a_fact_surviving_teardown():
    # `cheaper_than` is a derived FACT (from authored cost), not control scaffolding, so
    # replan teardown keeps it (while dropping `dominated`/`best`/`chosen`).
    g = _coffee_two_water(fetch_cost=1, buy_cost=5)
    h.plan(g)
    assert _mark(g, "buy_water", "dominated")
    replan = g.add_node("<replan>")
    g.add_relation(replan, "active", g.nodes_named("<yes>")[0])
    h.run_rules(g, h.TEARDOWN_RULES)
    assert _mark(g, "fetch_water", "cheaper_than", "buy_water")   # fact survives
    assert not _mark(g, "buy_water", "dominated")                 # control gone
    assert not _mark(g, "fetch_water", "best")
    assert not _mark(g, "fetch_water", "chosen")


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


def test_procedure_parses_into_an_ordered_step_list():
    # CNL `to NAME s1 then s2 then s3` -> the procedure name + its steps in stated order.
    # Recognition is CONTROLLED (the `to` header) and parsed in a throwaway graph.
    procs = h.parse_procedures("to brew get_water then add_beans then heat")
    assert procs == {"brew": ["get_water", "add_beans", "heat"]}
    # an unrecognized line yields nothing (no spurious procedure)
    assert h.parse_procedures("glorp the flarn") == {}


def test_procedure_invokes_into_solve_and_completes():
    # invoking a procedure marks its steps chosen + ordered and feeds them into the EXISTING
    # solve loop (no goal, no planner search): all steps run and the effects materialize.
    g = h.Graph()
    h.seed_operator(g, "get_water", add=["water"])
    h.seed_operator(g, "add_beans", add=["beans"])
    h.seed_operator(g, "heat", pre=["water", "beans"], add=["have_coffee"])
    h.seed_state(g, [])
    procs = h.parse_procedures("to brew get_water then add_beans then heat")
    order = []
    assert h.run_procedure(g, "brew", procs, actions=_record(order, procs["brew"])) == "done"
    assert order == ["get_water", "add_beans", "heat"]          # stated order
    assert h.procedure_done(g, "brew", procs)
    assert _mark(g, "<now>", "true", "have_coffee")


def test_procedure_then_order_binds_at_execution_without_preconditions():
    # the KEY property: two steps with NO precondition dependency still run in the stated
    # `then` order — the `waits_for` before-gate enforces the sequence, not just preconditions.
    g = h.Graph()
    h.seed_operator(g, "greet", add=["greeted"])
    h.seed_operator(g, "serve", add=["served"])                 # serve needs nothing of greet
    h.seed_state(g, [])
    procs = h.parse_procedures("to welcome greet then serve")
    order = []
    assert h.run_procedure(g, "welcome", procs, actions=_record(order, procs["welcome"])) == "done"
    assert order == ["greet", "serve"]


def test_procedure_gap_fill_plans_a_missing_precondition():
    # a procedure that OMITS a needed producer auto-completes: the chosen step's unmet pre
    # becomes a <need>, the EXISTING planner finds/commits a producer and orders it before the
    # step (the gap-fill bridge, corpus/procedure.cnl). No goal seeded; one bridge rule.
    g = h.Graph()
    h.seed_operator(g, "get_water", add=["water"])             # producer the procedure omits
    h.seed_operator(g, "heat", pre=["water"], add=["have_coffee"])
    h.seed_state(g, [])
    procs = h.parse_procedures("to brew heat")
    assert procs == {"brew": ["heat"]}                         # only the one declared step
    order = []
    assert h.run_procedure(g, "brew", procs, actions=_record(order, ["get_water", "heat"])) == "done"
    assert order == ["get_water", "heat"]                      # gap-filler ran first
    assert _mark(g, "get_water", "chosen")                     # planner committed the producer
    assert _mark(g, "get_water", "before", "heat")             # ordered before the step
    assert _mark(g, "<now>", "true", "have_coffee")
    assert h.procedure_done(g, "brew", procs)


def test_procedure_gap_fill_picks_cheapest_producer():
    # gap-filling reuses commitment's ranking: with two producers of the missing pre, the
    # cheaper is chosen and the costlier dominated (the fact-layer cost criterion).
    g = h.Graph()
    h.seed_operator(g, "fetch_water", add=["water"], cost=1)
    h.seed_operator(g, "buy_water", add=["water"], cost=5)
    h.seed_operator(g, "heat", pre=["water"], add=["have_coffee"])
    h.seed_state(g, [])
    procs = h.parse_procedures("to brew heat")
    assert h.run_procedure(g, "brew", procs, actions=_record([], ["fetch_water", "buy_water", "heat"])) == "done"
    assert _mark(g, "fetch_water", "chosen")
    assert not _mark(g, "buy_water", "chosen")
    assert _mark(g, "buy_water", "dominated")


def test_procedure_strict_mode_stalls_on_missing_precondition():
    # with gap_fill=False a missing precondition is NOT planned for: the step stalls and the
    # procedure reports "stuck" (off the step witnesses, not solve's vacuous goal "done").
    g = h.Graph()
    h.seed_operator(g, "get_water", add=["water"])
    h.seed_operator(g, "heat", pre=["water"], add=["have_coffee"])
    h.seed_state(g, [])
    procs = h.parse_procedures("to brew heat")
    order = []
    assert h.run_procedure(g, "brew", procs, gap_fill=False,
                           actions=_record(order, ["get_water", "heat"])) == "stuck"
    assert order == []                                         # nothing ran
    assert not h.procedure_done(g, "brew", procs)
    assert not _mark(g, "get_water", "chosen")                 # no gap-filler committed


def test_execution_unmet_precondition_blocks_readiness():
    # regression for the NAC-grouping fix: a chosen op with an unmet precondition that nothing
    # provides must NOT become ready (independent `not unmet` / `not done` negations). Before
    # the fix the multi-clause readiness NAC was conjunctive, so `unmet` was cosmetic.
    g = h.Graph()
    o = h.seed_operator(g, "op1", pre=["needed"], add=["result"])
    g.add_relation(o, "chosen", g.add_node("<yes>"))            # chosen, but `needed` absent
    h.seed_state(g, [])
    h.run_rules(g, h.EXECUTION_RULES, provenance=False)
    assert _mark(g, "op1", "unmet", "needed")
    assert not any(g.name(r) == "ready" for ex in g.nodes_named("<exec>")
                   for r, _ in g.relations_from(ex))


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


def test_planning_external_lookup_picks_cheapest():
    # the price is NOT in the KB; a rule demands it, the dispatcher fetches it, and the
    # cheaper source is chosen — exactly the static ranked behavior, sourced externally.
    g = _coffee_ext()
    reg = {"price": h.price_handler({"fetch_water": 1, "deliver_water": 5})}
    h.plan(g, registry=reg)
    assert _mark(g, "fetch_water", "chosen")
    assert _mark(g, "deliver_water", "dominated") and not _mark(g, "deliver_water", "chosen")
    assert _mark(g, "make_coffee", "chosen") and _mark(g, "get_beans", "chosen")
    # the fetched price is an in-graph FACT now; nothing was authored as `cost`
    assert _current_prices(g, "fetch_water") == ["1"]
    assert not any(g.name(r) == "cost" for n in g.nodes() for r, _ in g.relations_from(n))
    # only PRICED ops were looked up (no spurious request/error for make_coffee/get_beans)
    assert not g.nodes_named("<error>")
    assert not h.pending(g, "price")                     # all requests serviced


def test_planning_external_solve_reaches_goal():
    # the full loop fetches on demand and reaches the goal via the cheaper source only.
    g = _coffee_ext()
    reg = {"price": h.price_handler({"fetch_water": 1, "deliver_water": 5})}
    assert h.solve(g, registry=reg) == "done"
    assert _mark(g, "<now>", "true", "have_coffee")
    assert _mark(g, "fetch_water", "done") and not _mark(g, "deliver_water", "done")


def test_planning_external_price_change_repicks_on_replan():
    # FRESHNESS end-to-end: after a plan, the external price flips; a replan re-validates
    # (teardown clears `price_known`), the tool re-fetches (superseding the old price),
    # and the now-cheaper source is chosen. The old price FACT is kept, just superseded.
    g = _coffee_ext()
    db = {"fetch_water": 1, "deliver_water": 5}
    reg = {"price": h.price_handler(db)}
    h.plan(g, registry=reg)
    assert _mark(g, "fetch_water", "chosen") and not _mark(g, "deliver_water", "chosen")
    db["fetch_water"], db["deliver_water"] = 9, 1        # the world changed
    _teardown_replan(g)
    h.plan(g, registry=reg)
    assert _mark(g, "deliver_water", "chosen") and not _mark(g, "fetch_water", "chosen")
    assert _mark(g, "fetch_water", "dominated")
    assert sorted(_current_prices(g, "fetch_water")) == ["9"]   # current = the new price
    # both the old (1) and new (9) price facts coexist; the old is superseded, not deleted
    allp = [h.result_value(g, r) for r in g.nodes_named("price")
            if g.nodes_named("fetch_water")[0] in
            [ob for rr, ob in g.relations_from(r) if g.name(rr) == "of"]]
    assert set(allp) == {"1", "9"}


def test_planning_external_lookup_error_yields_to_priced_rival():
    # a MISSING price: the tool emits an `<error>` FACT (generic signal) and a `failed`
    # marker; the specific error rule makes the un-priceable op yield to a priced rival,
    # so planning still picks a water source and proceeds.
    g = _coffee_ext()
    reg = {"price": h.price_handler({"fetch_water": 1})}   # no price for deliver_water
    h.plan(g, registry=reg)
    err_about = [g.name(ob) for e in g.nodes_named("<error>")
                 for rr, ob in g.relations_from(e) if g.name(rr) == "about"]
    assert "deliver_water" in err_about
    assert _mark(g, "deliver_water", "dominated")
    assert _mark(g, "fetch_water", "chosen") and not _mark(g, "deliver_water", "chosen")


# ---- real §8 action tools at the act/observe boundary (vision §8) --------------------
# `act` runs a REAL action tool per operator when one is registered (it performs and
# emits the OBSERVED effect), else simulates the declared effect. Expected (declared) vs
# observed (real) divergence is now genuine, not just injectable.

def test_planning_real_action_tools_reach_goal():
    # backing every operator with a real tool that observes its declared effect behaves
    # exactly like the simulated path — goal reached.
    g = _coffee()
    actions = {"fetch_water": h.observe(added=["water"]),
               "get_beans": h.observe(added=["beans"]),
               "make_coffee": h.observe(added=["have_coffee"])}
    assert h.solve(g, actions=actions) == "done"
    assert _mark(g, "<now>", "true", "have_coffee")
    assert _mark(g, "make_coffee", "done")


def test_planning_real_action_tool_divergence_recovers():
    # a flaky real tool fails (observes nothing) the first time, succeeds on retry: the
    # missing effect is a real divergence -> replan -> the second attempt reaches the goal.
    calls = {"n": 0}
    def flaky(graph, op):
        calls["n"] += 1
        if calls["n"] >= 2:
            h.observe(added=["have_coffee"])(graph, op)
    g = _coffee()
    actions = {"fetch_water": h.observe(added=["water"]),
               "get_beans": h.observe(added=["beans"]), "make_coffee": flaky}
    assert h.solve(g, actions=actions) == "done"
    assert calls["n"] >= 2                                # it really retried after diverging
    assert _mark(g, "<now>", "true", "have_coffee")


def test_planning_real_action_tool_wrong_effect_diverges():
    # the tool's OBSERVED effect differs from the operator's DECLARED effect (it produces
    # `spilled`, not `have_coffee`): the expectation is unmet, so the goal is never reached.
    g = _coffee()
    actions = {"fetch_water": h.observe(added=["water"]),
               "get_beans": h.observe(added=["beans"]),
               "make_coffee": h.observe(added=["spilled"])}
    assert h.solve(g, actions=actions, max_cycles=6) == "stuck"
    assert not _mark(g, "<now>", "true", "have_coffee")
    assert _mark(g, "<now>", "true", "spilled")           # the REAL observed effect landed


# ---- the rule-linter: check the RULES against the system's invariants (vision §2/§5) -

def test_lint_real_banks_are_clean():
    # the shipped rule banks must satisfy the invariants the linter enforces (no
    # ungated deletes, no unbound drops, no no-ops, stratifiable) — a regression guard.
    # GRADED_RULES has empty RHS but a `propagate` effect, so it must NOT be flagged no-op.
    for bank in (h.SOLVE_RULES, h.PLANNING_RULES + h.REQUEST_RULES,
                 h.TEARDOWN_RULES, h.UNIVERSAL_RULES, h.GRADED_RULES, h.FORM_RULES,
                 h.DEMAND_TRANSITIVITY, h.DEMAND_COREF):
        assert h.lint_rules(bank) == [], h.format_smells(h.lint_rules(bank))


def test_lint_flags_ungated_fact_deletion():
    # a reasoning rule that DELETES a fact with no control token gating it violates §5.
    evil = h.Rule(key="evil.forget", lhs=[h.Pat("?a", "likes", "?b")],
                  rhs=[], drop=[h.Pat("?a", "likes", "?b")])
    smells = h.lint_rules([evil])
    assert any(s.kind == "ungated-delete" and s.rule_key == "evil.forget" for s in smells)
    # the same deletion GATED by a control token is fine (the legitimate control idiom)
    ok = h.Rule(key="ok.clear", lhs=[h.Pat("<exec>", "ready", "?o"), h.Pat("?o", "mark", "?b")],
                rhs=[], drop=[h.Pat("?o", "mark", "?b")])
    assert not any(s.kind == "ungated-delete" for s in h.lint_rules([ok]))


def test_lint_flags_no_op_and_negation_cycle():
    noop = h.Rule(key="noop", lhs=[h.Pat("?a", "p", "?b")], rhs=[])
    assert any(s.kind == "no-op" for s in h.lint_rules([noop]))
    # a true negation cycle: each rule NACs on a predicate the other produces
    a = h.Rule(key="cyc.a", lhs=[h.Pat("?x", "base", "?y")],
               nac=[h.Pat("?x", "q", "?y")], rhs=[h.Pat("?x", "p", "?y")])
    b = h.Rule(key="cyc.b", lhs=[h.Pat("?x", "base", "?y")],
               nac=[h.Pat("?x", "p", "?y")], rhs=[h.Pat("?x", "q", "?y")])
    assert any(s.kind == "negation-cycle" for s in h.lint_rules([a, b]))


def test_lint_dead_predicate_is_opt_in():
    # an LHS predicate nothing produces is only flagged when asked (heuristic; needs an
    # allowlist of base/fact predicates to avoid flagging ordinary facts).
    r = h.Rule(key="r", lhs=[h.Pat("?a", "never_produced", "?b")], rhs=[h.Pat("?a", "out", "?b")])
    assert not any(s.kind == "dead-predicate?" for s in h.lint_rules([r]))     # off by default
    smells = h.lint_rules([r], check_dead_predicates=True)
    assert any(s.kind == "dead-predicate?" for s in smells)
    # supplying it as a base predicate clears the finding
    assert not any(s.kind == "dead-predicate?" for s in
                   h.lint_rules([r], check_dead_predicates=True,
                                base_predicates=frozenset({"never_produced"})))


def test_lint_emits_smells_into_the_graph():
    # findings can be materialized as <rule-smell> nodes (the in-substrate view).
    evil = h.Rule(key="evil.forget", lhs=[h.Pat("?a", "likes", "?b")],
                  rhs=[], drop=[h.Pat("?a", "likes", "?b")])
    g = h.Graph()
    h.emit_smells(g, h.lint_rules([evil]))
    smell_nodes = g.nodes_named("<rule-smell>")
    assert smell_nodes
    kinds = [g.name(ob) for s in smell_nodes for r, ob in g.relations_from(s) if g.name(r) == "kind"]
    assert "ungated-delete" in kinds


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

def test_universal_is_a_is_a_law_binding_many_witnesses():
    # "every X is a Y" is a UNIVERSAL LAW (binds every witness), not a flattened fact.
    # It is recorded as a law marker and applied to each witness BY NAME (no merge of the
    # witnesses), even when the law is stated before they are.
    s = h.Session()
    s.submit("every person is a mortal")
    s.submit("paul is a person")
    s.submit("mary is a person")
    facts = s.facts()
    assert "paul is_a mortal" in facts and "mary is_a mortal" in facts  # law bound both
    assert "person every_is_a mortal" in facts       # kept as a law, not as `person is_a mortal`
    assert "person is_a mortal" not in facts


def test_session_assert_question_and_reasoning():
    s = h.Session()
    assert s.submit("paul is a person").recognized
    s.submit("every person is a mortal")
    assert "paul is_a mortal" in s.facts()          # the universal law fired
    q = s.submit("is paul a mortal")
    assert q.is_question and q.answer == ["yes"]


def test_session_reports_unrecognized_lines():
    s = h.Session()
    ok = s.submit("alice wants vanilla")
    assert ok.recognized and not ok.error
    bad = s.submit("frobnicate the wibble quux")    # matches no meaningful form
    assert not bad.recognized
    assert "frobnicate the wibble quux" in s.unparsed()
    # the unparsed list does not duplicate across further lines (canonicalize-proof)
    s.submit("bob wants chocolate")
    assert s.unparsed().count("frobnicate the wibble quux") == 1


def test_session_bare_repeats_are_distinct_witnesses_not_a_contradiction():
    # Pure §3 disambiguation (the chosen Session semantics, docs/coreference_design.md): a
    # bare repeated mention is a DISTINCT witness, so `ice is a solid` + `ice is a liquid` is
    # NOT a contradiction — it reads as two different ice things, not one ice that is both.
    # (To flag a genuine one-entity mistake, an explicit single identity is stated — see
    # test_session_single_identity_catches_contradiction.) The KB is LAZY: detection is
    # pulled by `contradictions`.
    s = h.Session()
    results = s.load_text(
        "liquid is disjoint from solid\n"
        "ice is a solid\n"
        "ice is a liquid\n"
    )
    assert all(r.recognized for r in results)
    assert s.contradictions() == []                 # distinct witnesses -> consistent
    assert len(s.kb.nodes_named("ice")) == 2        # never merged


def test_session_single_identity_catches_contradiction():
    # EXPLICIT SINGLE IDENTITY (`X is one thing`): the user asserts all `ice` mentions are ONE
    # entity, which overrides the pure-§3 distinct-witness default. The mentions are
    # force-coreferenced (kept even though contradictory), so `ice is a solid` + `ice is a
    # liquid` over disjoint sorts is now a REAL contradiction — the genuine one-entity mistake
    # the distinct-witness model deliberately could not catch.
    s = h.Session()
    results = s.load_text(
        "liquid is disjoint from solid\n"
        "ice is one thing\n"                        # explicit single identity
        "ice is a solid\n"
        "ice is a liquid\n"
    )
    assert all(r.recognized for r in results)       # the declaration line is recognized
    assert "ice is_unique <yes>" in s.facts()       # the single-identity marker is content
    c = s.contradictions()
    assert c != []                                  # one ice that is both -> contradiction
    assert "ice" in {a for x in c for a in x["about"]}


def test_session_single_identity_consistent_when_compatible():
    # Declaring a single identity does NOT manufacture contradictions: one `ice` that is a
    # solid and is cold is perfectly consistent (cold and solid are not disjoint).
    s = h.Session()
    s.load_text(
        "liquid is disjoint from solid\n"
        "ice is one thing\n"
        "ice is a solid\n"
        "ice is cold\n"
    )
    assert s.contradictions() == []


def test_session_cross_name_identity_composes_facts():
    # EXPLICIT CROSS-NAME COREFERENCE (`X is the same as Y`): two different names denote one
    # entity, so a fact stated under one name is true of the other. Asking about superman
    # composes clark's reporter fact across the asserted identity.
    s = h.Session()
    s.load_text("clark is the same as superman\nclark is a reporter\n")
    q = s.submit("is superman a reporter")
    assert q.is_question and q.answer == ["yes"]
    assert len(s.kb.nodes_named("clark")) >= 1 and len(s.kb.nodes_named("superman")) >= 1


def test_session_cross_name_identity_catches_contradiction():
    # Identifying two names propagates BOTH their facts onto the one entity; if those facts are
    # incompatible (human vs martian, disjoint), it is a real contradiction. Mirrors the
    # single-identity case but across distinct names.
    s = h.Session()
    s.load_text(
        "human is disjoint from martian\n"
        "clark is the same as superman\n"
        "clark is a human\n"
        "superman is a martian\n"
    )
    c = s.contradictions()
    assert c != []
    about = {a for x in c for a in x["about"]}
    assert "clark" in about or "superman" in about


def test_session_distinct_names_do_not_compose():
    # WITHOUT the identity declaration, two different names are just two entities: a fact about
    # clark says nothing about superman (no spurious composition).
    s = h.Session()
    s.load_text("clark is a reporter\nsuperman is a hero\n")
    q = s.submit("is superman a reporter")
    assert q.is_question and q.answer == ["no"]


def test_session_consistent_kb_has_no_contradictions():
    s = h.Session()
    s.load_text("liquid is disjoint from solid\nice is a solid\n")
    assert s.contradictions() == []


# ---- demand-driven SELECTIVE coreference on the Session query path (vision §3) -----------
# The KB is lazy: a QUESTION is the demand that pulls coreference of the queried entity's
# mentions (only those — selective, bounded). A rule turns the demand into a <coref-request>;
# the dumb dispatcher resolves it by reasoning (provably-distinct mentions are rejected), and
# the genuinely ambiguous residue is referred to the user via an optional Oracle.

def test_session_query_disambiguates_two_pauls_by_reasoning():
    # Two `paul` mentions in disjoint categories. Asking about paul pulls coreference; linking
    # them would make one paul both teacher and student (disjoint) -> the link is rejected, so
    # the two pauls stay separate and the KB stays consistent. No user needed.
    s = h.Session()
    s.load_text("teacher is disjoint from student\n"
                "paul is a teacher\n"
                "paul is a student\n")
    ans = s.submit("is paul a teacher")
    assert ans.is_question and ans.answer == ["yes"]   # the teacher-paul answers
    assert len(s.kb.nodes_named("paul")) == 2          # never merged
    assert not _has(s.kb, "paul", "same_as", "paul")   # the inconsistent link was withdrawn
    assert s.contradictions() == []                    # disambiguation kept it consistent


def test_session_ask_user_disambiguation_for_a_consistent_link():
    # Two `paul` mentions whose categories are COMPATIBLE (teacher + mortal): reasoning cannot
    # tell whether they are the same person, so the identity is referred to the user. With an
    # oracle that answers "distinct", the link is withdrawn and the mentions stay separate;
    # with the default (no oracle) a consistent link is kept and facts compose across it.
    def run(oracle):
        s = h.Session(oracle=oracle)
        s.load_text("paul is a teacher\npaul is a mortal\n")
        s.submit("is paul a teacher")                  # the query pulls coreference
        return s

    distinct = run(h.auto_oracle("distinct"))
    assert not _has(distinct.kb, "paul", "same_as", "paul")    # user said: different people
    assert len(distinct.kb.nodes_named("paul")) == 2

    kept = run(None)                                    # no oracle -> keep the consistent link
    assert _has(kept.kb, "paul", "same_as", "paul")     # linked, facts compose across it


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


def test_session_in_statement_context_grammar_splices_cleanly():
    # The `X of C` grammar qualifies a mention with its context inline, splicing it into an
    # `in` fact. Under pure §3 the bare mondays are distinct witnesses, so neither the
    # different-week nor the same-week phrasing is a contradiction (a name clash = distinct
    # things, not an inconsistency). What we assert here is the GRAMMAR (the qualifier splices
    # out cleanly into `before` + `in` facts); consistency holds either way.
    s = h.Session()
    s.load_text("before is a relation\nbefore is asymmetric\n"
                "monday of week1 before tuesday of week1\n"
                "tuesday of week2 before monday of week2")
    assert "monday before tuesday" in s.facts()          # the qualifier spliced out cleanly
    assert "monday in week1" in s.facts() and "monday in week2" in s.facts()
    assert s.contradictions() == []                      # distinct witnesses -> consistent


# ---- grammar coverage: generic binary relations (declare a relation -> a form for it) -

def test_grammar_declared_binary_relation_parses():
    # a bare `X R Y` is only parseable once `R is a relation` declares R (controlled CNL,
    # not greedy — an undeclared relation word stays unrecognized).
    s = h.Session()
    assert not s.submit("monday before tuesday").recognized       # before not declared yet
    s.submit("before is a relation")
    r = s.submit("monday before tuesday")
    assert r.recognized and "monday before tuesday" in s.facts()
    assert s.submit("glorp the flarn wibbit").recognized is False  # still controlled


def test_grammar_relation_with_constraint_over_distinct_witnesses():
    # The end-to-end stack — declare a relation, declare a LAW on it, state facts — all in
    # CNL. Under pure §3 the two `monday` (and `tuesday`) mentions are DISTINCT witnesses, so
    # `monday before tuesday` + `tuesday before monday` is NOT a violation: it is monday#1
    # before tuesday#1 and tuesday#2 before monday#2, four different days. The law is declared
    # and the facts parse; nothing forces them onto one node, so there is no contradiction.
    # (Catching a genuine self-asymmetry needs an explicit single identity — future grammar;
    # the asymmetry schema itself is exercised on shared nodes by the constraint tests above.)
    s = h.Session()
    s.load_text(
        "before is a relation\n"
        "before is asymmetric\n"
        "monday before tuesday\n"
        "tuesday before monday\n"
    )
    assert "before rel_property asymmetric" in s.facts()   # the law was declared
    assert "monday before tuesday" in s.facts() and "tuesday before monday" in s.facts()
    assert s.contradictions() == []                        # distinct witnesses -> consistent
    # no spurious facts from `before` being both a relation word and an entity
    assert "violates before is_a" not in s.facts()


# ---- grammar coverage: n-ary relations (reify a 3+-participant statement as an event) -----

def _event_roles(g, pred):
    """The role->participant maps of every reified `event` whose `pred` is `pred`."""
    out = []
    for ev in g.nodes_named("event"):
        roles = {g.name(rel): g.name(o) for rel, o in g.relations_from(ev)}
        if roles.get("pred") == pred:
            out.append(roles)
    return out


def test_grammar_nary_reifies_ditransitive_into_an_event():
    # "alice gives book to bob" is a 3-participant statement: it reifies into an EVENT node
    # with named role edges (subj/obj/<preposition>) + the verb as `pred`. Controlled and
    # FULLY DATA-DRIVEN: both the verb (`gives is a verb`) AND the preposition
    # (`to is a preposition`) are declared in CNL — no hardcoded lexical list.
    s = h.Session()
    assert not s.submit("alice gives book to bob").recognized   # verb/prep not declared yet
    s.submit("gives is a verb")
    s.submit("to is a preposition")
    r = s.submit("alice gives book to bob")
    assert r.recognized
    [roles] = _event_roles(s.kb, "gives")
    assert roles == {"pred": "gives", "subj": "alice", "obj": "book", "to": "bob"}
    # the role edges are content facts (so the line is recognized, and they survive stripping)
    assert "event subj alice" in s.facts() and "event to bob" in s.facts()


def test_grammar_nary_events_are_distinct_per_instance():
    # each statement reifies into its OWN event node (a fresh `event?`), never merged — two
    # gives are two events, with a different verb/preposition handled by the same machinery.
    s = h.Session()
    s.load_text(
        "gives is a verb\n"
        "makes is a verb\n"
        "to is a preposition\n"
        "for is a preposition\n"
        "alice gives book to bob\n"
        "carol gives pen to dave\n"
        "eve makes cake for frank\n"
    )
    gives = _event_roles(s.kb, "gives")
    assert len(gives) == 2
    assert {"subj": "alice", "obj": "book", "to": "bob", "pred": "gives"} in gives
    assert {"subj": "carol", "obj": "pen", "to": "dave", "pred": "gives"} in gives
    [made] = _event_roles(s.kb, "makes")
    assert made == {"pred": "makes", "subj": "eve", "obj": "cake", "for": "frank"}


def test_grammar_nary_is_controlled_and_disjoint_from_binary():
    # an undeclared verb stays unrecognized (controlled CNL), and declaring a binary RELATION
    # does NOT make it an n-ary verb (the two declarations are disjoint: is_a relation vs verb).
    s = h.Session()
    s.submit("likes is a relation")
    s.submit("to is a preposition")
    assert "likes" in h.declared_relations(s.kb)
    assert "likes" not in h.declared_verbs(s.kb)
    assert "to" in h.declared_prepositions(s.kb)
    assert not s.submit("alice sends parcel to dave").recognized   # 'sends' not declared
    assert _event_roles(s.kb, "sends") == []


def test_grammar_nary_questions_query_each_role():
    # an n-ary event is queryable by putting a wh-word in the role you want: `who` in the
    # subject or prep slot, `what` in the direct object. The answer reconstructs the event.
    s = h.Session()
    s.load_text("gives is a verb\nto is a preposition\nalice gives book to bob\n")
    assert s.submit("who gives book to bob").answer == ["alice gives book to bob"]
    assert s.submit("alice gives what to bob").answer == ["alice gives book to bob"]
    assert s.submit("alice gives book to who").answer == ["alice gives book to bob"]
    # all three are recognized as QUESTIONS (not asserted as new events)
    assert s.submit("who gives book to bob").is_question
    assert len(_event_roles(s.kb, "gives")) == 1                  # asking added no events


def test_grammar_nary_question_discriminates_and_handles_misses():
    # the join is on the whole event: a wh-query returns only events matching ALL given roles,
    # several matches are all returned, and an unmatched query says so.
    s = h.Session()
    s.load_text("gives is a verb\n"
                "to is a preposition\n"
                "alice gives book to bob\n"
                "carol gives pen to bob\n"
                "alice gives book to dave\n")
    assert s.submit("who gives pen to bob").answer == ["carol gives pen to bob"]
    assert sorted(s.submit("alice gives book to who").answer) == [
        "alice gives book to bob", "alice gives book to dave"]
    assert s.submit("zoe gives book to who").answer == ["(no answer)"]
    # a declarative (no wh-word) is NOT a question — it asserts a new event
    assert not s.submit("eve gives map to bob").is_question


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


def test_planning_kb_cnl_reflects_to_python_seeders():
    # The whole coffee instance authored in CNL lowers to EXACTLY the edge set the
    # seed_operator/seed_state/seed_goal calls in examples/coffee.py produce (shared
    # condition nodes, opaque cost data-nodes, the <goal>/<now> hubs) — no drift.
    gc = h.load_planning_kb(_COFFEE_KB.read_text(encoding="utf-8"))
    gp = h.Graph()
    h.seed_operator(gp, "make_coffee", pre=["water", "beans"], add=["have_coffee"])
    h.seed_operator(gp, "get_beans", add=["beans"])
    h.seed_operator(gp, "buy_latte", pre=["money"], add=["have_coffee"])
    h.seed_operator(gp, "fetch_water", add=["water"], cost=1)
    h.seed_operator(gp, "deliver_water", add=["water"], cost=5)
    h.seed_state(gp, [])
    h.seed_goal(gp, "have_coffee")
    assert _edges(gc) == _edges(gp)


def test_planning_kb_forms_cover_del_priced_and_state_edges():
    # the surfaces the coffee KB doesn't exercise: `removes` -> del, `is priced` ->
    # needs_price <yes> (external cost), and `we have C` -> <now> true C.
    g = h.load_planning_kb("brew removes water\nbrew is priced\nwe have milk")
    assert _mark(g, "brew", "del", "water")
    assert _mark(g, "brew", "needs_price", "<yes>")
    assert _mark(g, "<now>", "true", "milk")


def test_planning_kb_unrecognized_line_contributes_nothing():
    # controlled recognition (like parse_procedures): a line no form matches is silently
    # skipped and adds no edge.
    g = h.load_planning_kb("glorp the flarn wibbit")
    assert _edges(g) == []


def test_planning_kb_plan_and_solve_reach_the_goal():
    # loaded via the ONE entry point the TUI calls, the CNL KB drives the unchanged
    # planning loop: the cheapest water producer is chosen, the costlier dominated, the
    # dead option dies, and solve reaches the goal.
    g = h.load_planning_kb(_COFFEE_KB.read_text(encoding="utf-8"))
    h.plan(g)
    assert _mark(g, "make_coffee", "chosen")
    assert _mark(g, "fetch_water", "chosen")               # cheaper water producer
    assert _mark(g, "deliver_water", "dominated")          # costlier loses
    assert not _mark(g, "buy_latte", "viable")             # dead option (money unreachable)
    g2 = h.load_planning_kb(_COFFEE_KB.read_text(encoding="utf-8"))
    assert h.solve(g2) == "done"
    assert _mark(g2, "<now>", "true", "have_coffee")


_BARISTA_KB = _pathlib.Path(__file__).resolve().parent.parent / "corpus" / "barista_kb.cnl"


def test_planning_program_parses_operators_and_procedures():
    # One MIXED .cnl carries operators + goal (into the graph) AND a procedure (into the
    # procedures dict). The two surfaces are disjoint: a `to NAME ...` line yields no operator
    # edge, and load_planning_kb (graph-only) sees the same graph as program[0].
    text = _BARISTA_KB.read_text(encoding="utf-8")
    g, procs = h.load_planning_program(text)
    assert procs == {"morning_service": ["get_beans", "grind_beans", "fetch_water", "make_coffee"]}
    assert _mark(g, "<goal>", "want", "have_coffee")
    assert _mark(g, "make_coffee", "pre", "ground")
    # the procedure header contributes NO operator/state/goal edge to the graph
    assert not g.nodes_named("morning_service")
    # backward-compat: the graph-only entry point equals program()'s graph
    assert _edges(h.load_planning_kb(text)) == _edges(g)


def test_planning_program_goal_and_procedure_both_reach_done():
    # Same mixed KB, two ways to drive it. Goal-directed: solve reaches have_coffee.
    text = _BARISTA_KB.read_text(encoding="utf-8")
    g_goal, _ = h.load_planning_program(text)
    assert h.solve(g_goal) == "done"
    assert _mark(g_goal, "<now>", "true", "have_coffee")
    # Procedure-directed: run the authored step sequence (planner gap-fills unmet pres); every
    # step executes and the sequence completes.
    g_proc, procs = h.load_planning_program(text)
    assert h.run_procedure(g_proc, "morning_service", procs) == "done"
    assert h.procedure_done(g_proc, "morning_service", procs)
    assert _mark(g_proc, "<now>", "true", "have_coffee")

"""The GRAMMAR intake route (integration step 2) — facts on ENTITIES, not tokens.

These pin the fork's contract while it is still a fork: the surface survives, the judgements are
scoped, and the three outcomes are distinguishable.
"""
from __future__ import annotations

import itertools
import pathlib

import pytest

from ugm import AttrGraph
from ugm.cnl import grammar_intake as gi
from ugm.cnl.grammar import compile_grammar, load_grammar, parse
from ugm.interpretation import DENOTES, contradictions, discard_scope, interpret

CORPUS = pathlib.Path(__file__).resolve().parent.parent / "corpus"


@pytest.fixture
def kb():
    g = AttrGraph()
    gi.declare_grammar(g, CORPUS / "loudon_grammar.cnl")
    return g


def banks(kb):
    return gi.session_banks(kb)


def test_no_grammar_declared_means_no_banks():
    assert gi.session_banks(AttrGraph()) is None


def test_fact_lands_on_an_entity_not_the_token(kb):
    kind, data = gi.route(kb, "the lion has a mane", banks(kb))
    assert kind == "fact"
    # The token still exists and is NOT the thing carrying the fact — that is the whole point.
    ents = gi.denotata(kb, data["tokens"])
    assert ents, "tokens must denote entities"
    assert not set(ents) & set(data["tokens"])
    assert ("lion", "has", "mane") in gi.facts(kb)


def test_surface_survives_a_discarded_interpretation(kb):
    gi.route(kb, "the lion has a mane", banks(kb))
    surface = {n for n in kb.nodes() if any(kb.has_key(r, "cat") for r, _ in kb.relations_from(n))}
    assert surface
    scope = kb.registers[gi.SCOPE_REGISTER]
    discard_scope(kb, scope, banks(kb).slot_preds)
    assert surface <= set(kb.nodes()), "discarding an interpretation must not touch the surface"


def test_refused_is_distinct_from_ambiguous(kb):
    kind, _ = gi.route(kb, "glorp the flarn", banks(kb))
    assert kind == "unrecognized"


def test_the_exception_sentence_lands_negated(kb):
    """`the guzerat lion has no mane` — the sentence the shipped bank drops, and the reason the
    learner never saw a counterexample to its own generalization."""
    kind, _ = gi.route(kb, "the guzerat lion has no mane", banks(kb))
    assert kind == "fact"
    assert any(p == "has_not" and o == "mane" for _s, p, o in gi.facts(kb))


def test_a_hedged_clause_parses_and_commits_no_ink(kb):
    """HEDGING, slice 1 (the grammar half). The concept-inventory audit's most frequent gap.

    A hedged sentence must parse — dropping it is the §10a exception-dropping failure in another
    costume — but it must NOT write an ink fact, because `generally` is a claim about a BAND and
    ink means certain. `hclause` being its own category is what enforces that: `clause asserts subj
    pred obj` cannot fire on it. Authoring the banded fork is the interpretation layer's remaining
    half; until it lands, the honest state is parsed-with-slots-and-no-fact.
    """
    before = set(gi.facts(kb))
    kind, _ = gi.route(kb, "the lion generally has a mane", banks(kb))
    assert kind != "unrecognized", "a hedged sentence must not be refused"
    assert set(gi.facts(kb)) == before, "a hedge is not certain — it must commit no ink fact"

    # ...while the UNhedged counterpart still does, i.e. the new category stole nothing.
    gi.route(kb, "the lion has a mane", banks(kb))
    assert ("lion", "has", "mane") in gi.facts(kb)


def test_a_hedged_sentence_lands_as_a_banded_fork(kb):
    """HEDGING slice 2b: `hedges` writes the triple in PENCIL behind a fork banded by the hedge
    word — so the claim is REPRESENTED at its degree instead of being dropped or over-claimed."""
    from ugm.possibility import possibility
    gi.route(kb, "the lion generally has a mane", banks(kb))
    assert possibility(kb, "has", "lion", "mane") == 0.75
    assert ("lion", "has", "mane") not in gi.facts(kb), "a hedge must not commit ink"


def test_different_hedges_give_different_bands(kb):
    """The band comes from the DECLARED scale (`generally means 0.75` / `sometimes means 0.4`), so
    two hedges must not collapse to one degree — that is the whole point of declaring a scale."""
    from ugm.possibility import possibility
    gi.route(kb, "the lion generally has a mane", banks(kb))
    gi.route(kb, "the lion sometimes is strong", banks(kb))
    assert possibility(kb, "has", "lion", "mane") == 0.75
    assert possibility(kb, "is", "lion", "strong") == 0.4


@pytest.mark.parametrize("order", [
    ["the lion has a mane", "the lion generally has a mane"],
    ["the lion generally has a mane", "the lion has a mane"],
])
def test_hedging_and_asserting_the_same_triple_is_order_independent(kb, order):
    """REGRESSION, and it was a silent one. `MINT(dedup=True)` matched on (subject, predicate,
    object) and ignored LAYER, so a PENCIL `lion has mane` made a later CERTAIN `lion has mane`
    reuse the pencil and write no ink — **the certain fact vanished**, and only in that order.

    Both are legitimate and distinct assertions ("lions generally have manes" / "the lion has a
    mane"), so both must survive, whichever came first. Fixed in `MINT`'s dedup scan by requiring
    the candidate's control-ness to match."""
    from ugm.possibility import possibility
    for s in order:
        gi.route(kb, s, banks(kb))
    assert ("lion", "has", "mane") in gi.facts(kb), f"the certain fact was lost in order {order}"
    assert possibility(kb, "has", "lion", "mane") == 1.0


def test_the_hedge_word_is_recoverable_from_the_parse(kb):
    """The fork-authoring half needs (subj, pred, obj, hedge) off the span — pin that they are all
    there, so the remaining work is authoring and not re-parsing."""
    gi.route(kb, "the lion generally has a mane", banks(kb))
    found = {}
    for n in kb.nodes():
        cat = next((kb.name(o) for r, o in kb.relations_from(n) if kb.has_key(r, "cat")), None)
        if cat != "hclause":
            continue
        found = {kb.predicate(r): kb.name(o) for r, o in kb.relations_from(n)}
    assert found.get("hedge") == "generally"
    assert found.get("subj") == "lion"
    assert found.get("pred") == "has"
    assert found.get("obj") == "mane"


def test_centers_are_described_not_named(kb):
    _kind, data = gi.route(kb, "the guzerat lion has no mane", banks(kb))
    assert data["centers"], "an assertion must yield focus centers"
    assert all(isinstance(c, str) and c for c in data["centers"])


# ---------------------------------------------------------------------------
# End-to-end through `ingest` — the fork is reachable from the real driver
# ---------------------------------------------------------------------------

def test_ingest_routes_a_grammar_kb_through_the_grammar_path(kb):
    import ugm as h
    out = h.ingest(kb, [], "the lion has a mane")
    assert out.kind == "fact"
    assert ("lion", "has", "mane") in gi.facts(kb)


def test_ingest_reports_refusal_as_unrecognized(kb):
    import ugm as h
    out = h.ingest(kb, [], "glorp the flarn")
    assert out.kind == "unrecognized"


def test_ingest_reports_ambiguity_as_its_own_kind(kb):
    """PP-attachment. The point of a separate kind: this utterance is ANSWERABLE by a question,
    unlike gibberish — and it must write NOTHING in the meantime, where today's bank writes three
    wrong facts."""
    import ugm as h
    out = h.ingest(kb, [], "the lion has a mane in africa")
    assert out.kind == "ambiguous"
    assert out.nearest, "the ambiguous spans must be nameable for a discriminating question"
    assert not gi.facts(kb), "an ambiguous utterance commits to nothing"


def test_ingest_without_a_grammar_is_unaffected():
    """The fork must be invisible to every KB that does not declare a grammar."""
    import ugm as h
    from ugm import derived_triples
    g = AttrGraph()
    out = h.ingest(g, [], "the lion is a cat")
    assert out.kind == "fact"
    assert ("lion", "is_a", "cat") in set(derived_triples(g))


# ---------------------------------------------------------------------------
# DECLARATIVE ROUTING (2026-07-20) — the router dispatches on the FORCE the parse
# recovered, not on position in an ordered if-ladder. `design/form_inventory.md` §4b.
# ---------------------------------------------------------------------------

#: One surface per FORCE the grammar declares, and the `Outcome.kind` each must produce.
#: The whole claim of declarative routing is that this table is decided by the PARSE.
FORCES = [
    ("the lion has a mane", "fact"),        # clause  asserts
    ("is lion strong", "answer"),           # qclause asks
    ("focus on lion", "focus"),             # iclause commands -> focus
    ("be cautious", "stance"),              # iclause commands -> stance
]


def _token_side_content(kb):
    """CONTENT relations standing on SURFACE tokens — what `load_facts` would have written.

    The discriminator matters: a refused parse legitimately leaves its surface behind (the token
    chain, `cat`/`begin`/`end`, the span scaffolding), and that is the permanent record this route
    is built on. What must never appear is a CONTENT relation on a token, since content belongs on
    the entities one `denotes` hop away. So this filters the surface out rather than comparing
    whole-graph triples, which would fail on the scaffolding and hide the real property."""
    from ugm.interpretation import SURFACE_PREDS
    surface = {n for n in kb.nodes()
               if any(kb.has_key(r, "first") or kb.has_key(r, "next")
                      for r, _ in kb.relations_from(n))
               or any(kb.has_key(r, "next") for r in kb.into(n))}
    out = []
    for n in surface:
        for r, o in kb.relations_from(n):
            p = kb.predicate(r)
            if not p or kb.is_control(r) or kb.is_inert(r):
                continue
            if p in SURFACE_PREDS or p.startswith("span_") or p in ("head", "about", "because"):
                continue
            out.append((kb.name(n), p, kb.name(o)))
    return out


@pytest.mark.parametrize("text,kind", FORCES)
def test_each_force_routes_by_its_parse(kb, text, kind):
    """Every force reaches its own route through the REAL `ingest`, i.e. through the restructured
    router rather than through `gi.route` in isolation."""
    import ugm as h
    assert h.ingest(kb, [], text).kind == kind


def test_the_parse_and_not_the_ladder_decided_the_command(kb):
    """⭐ THE DISCRIMINATING TEST, and the reason the outcome table above is not enough.

    `test_each_force_routes_by_its_parse` passes whether the GRAMMAR or the shipped string
    recognizer decided, because both produce `Outcome("focus")` — it cannot see the property this
    slice exists to establish. (Lesson 4: a test that passes under the defect it was written for.)

    The structural discriminator: the shipped `recognize_focus_op` runs its forms in a SCRATCH
    graph and leaves the KB untouched, while the grammar route parses into the KB and leaves the
    utterance's SURFACE standing. So an `iclause` span in the KB proves the parse decided. Fails
    the moment the dispatch is moved back below the focus recognizer."""
    import ugm as h
    h.ingest(kb, [], "focus on lion")
    cats = {kb.name(o) for n in kb.nodes() for r, o in kb.relations_from(n)
            if kb.has_key(r, "cat")}
    assert "iclause" in cats, (
        f"no iclause span — the ladder, not the parse, routed the command (saw {sorted(cats)})")


def test_a_grammar_question_emits_the_question_event_before_the_answer(kb):
    """STREAM PARITY WITH THE SHIPPED ROUTE. A consumer renders the turn from these events, so a
    grammar question yielding only `['answer']` leaves a TUI unable to show what it answered.

    Found by SIMULATING THE STEP-2 FLIP over the whole suite rather than by reading the code — the
    grammar route is exercised by so few tests today that an event-level gap could sit unnoticed."""
    import ugm as h
    h.ingest(kb, [], "the lion is strong")
    ev = []
    h.ingest(kb, [], "is lion strong", on_event=ev.append)
    assert [e.kind for e in ev] == ["question", "answer"]


def test_a_command_commits_no_fact(kb):
    """A command changes STEPPING state, never a belief. `asks`/`intends`/`commands` all commit
    nothing; what separates a command is only what it leaves behind."""
    import ugm as h
    h.ingest(kb, [], "focus on lion")
    h.ingest(kb, [], "be cautious")
    assert not gi.facts(kb), "a command must not write a fact"


def test_a_command_actually_performs_its_act(kb):
    """Routing to `focus`/`stance` is not enough — the act the module owns must have happened, or
    the force would be recognized and then dropped."""
    import ugm as h
    from ugm import focus as focus_mod
    h.ingest(kb, [], "focus on lion")
    assert "lion" in set(focus_mod.top_centers(kb))
    h.ingest(kb, [], "be cautious")
    assert kb.registers["policy"].theta == 0.2


def test_a_command_verb_naming_no_act_is_refused(kb):
    """`COMMAND_ACTS` is a LOOKUP, not an ordered ladder: an imperative that names no act this
    system performs is refused rather than guessed into the nearest one."""
    import ugm as h
    assert h.ingest(kb, [], "be strong").kind == "unrecognized"


def test_the_authoring_cluster_is_refused_by_the_grammar(kb):
    """⭐ WHY THE AUTHORING CLUSTER'S POSITION IS NOT A ROUTING DECISION.

    disable / form / procedure / rule sit ABOVE the grammar dispatch because they are BANK
    AUTHORING, which the fold structurally cannot express. That is only harmless if the grammar
    would refuse them anyway — otherwise the ordering, not the declaration, is deciding. Measured
    here rather than assumed, because if a future grammar ever DID parse one of these surfaces the
    router would silently start answering a different question."""
    from ugm.cnl.grammar import PARSED
    for text in ("forget that rule",
                 "form k : <thing>? big ?x when ?x next ?y",
                 "to build : get wood",
                 "?x is dangerous when ?x is strong"):
        outcome, _toks, _eos = parse(AttrGraph(), text, banks(kb))
        assert outcome != PARSED, f"the grammar now parses an authoring surface: {text!r}"


def test_conditionals_still_reach_the_rule_layer(kb):
    """The authoring cluster's reason for existing, on the surface that motivated it. A conditional
    must not be read as a fact by the grammar — `form_inventory.md` records the rule layer as its
    correct route."""
    import ugm as h
    out = h.ingest(kb, [], "?x is dangerous when ?x is strong")
    assert out.kind == "rule" and out.added_rules


def test_a_grammar_kb_never_reaches_the_token_fact_route(kb):
    """⚠ THE REGRESSION THIS SLICE COULD MOST EASILY CAUSE, and it would be SILENT.

    A refused parse now FALLS THROUGH to the recognizers below it. If it kept falling all the way
    into `load_facts`, the line would route as `fact` and look successful while writing its
    relations onto the TOKENS — reintroducing exactly the duality the grammar route exists to split
    apart. An unparsed line must end as `unrecognized` with nothing on the token side.

    ⚠ THE INPUT IS THE WHOLE TEST, and the first version got it wrong. `glorp the flarn quux` is
    refused by the shipped fact forms TOO, so it passed with the guard deleted — it could not tell
    the two paths apart (lesson 4 again, caught by re-breaking). `zork is a cat` is the
    discriminating shape: the grammar refuses it because `zork` is undeclared, while `load_facts`
    recognizes it perfectly and would write `zork is_a cat` onto the token."""
    import ugm as h
    out = h.ingest(kb, [], "zork is a cat")
    assert out.kind == "unrecognized"
    assert not _token_side_content(kb), (
        "a grammar KB must never write token-side facts — it fell through to `load_facts`")


def test_an_undeclared_focus_surface_still_falls_through(kb):
    """The fall-through's REASON: a grammar need not declare every surface. `forget that` is not in
    the iclause productions, so it must still reach the shipped focus recognizer."""
    import ugm as h
    h.ingest(kb, [], "focus on lion")
    assert h.ingest(kb, [], "forget that").kind == "focus"


# ---------------------------------------------------------------------------
# L0 — the METALANGUAGE (the LEVEL axis, 2026-07-20). A declaration ABOUT the
# language lives in a register, never as a graph fact.
# ---------------------------------------------------------------------------

@pytest.fixture
def okb():
    """A grammar KB with OPEN vocabulary — undeclared words default to nouns, so these tests turn
    on the relation declaration rather than on the lexicon wall."""
    g = AttrGraph()
    gi.declare_grammar(g, CORPUS / "loudon_grammar.cnl", open_class="noun")
    return g


def test_a_vocabulary_declaration_is_idempotent(okb):
    """⭐ THE DEFECT THIS SLICE EXISTS TO FIX. Read by the OBJECT grammar, a declaration was
    destroyed by its own effect: `produces is a relation` parsed while `produces` was unknown and
    REFUSED once it had become a `transitive`, because a verb-category word cannot head an np.
    Measured through real `ingest`, the same line twice routed `fact` then `unrecognized`.

    Re-declaration is the NORMAL case under the multi-KB-file model, so this is not an edge case."""
    import ugm as h
    assert h.ingest(okb, [], "produces is a relation").kind == "vocabulary"
    assert h.ingest(okb, [], "produces is a relation").kind == "vocabulary"


def test_a_vocabulary_declaration_writes_no_graph_fact(okb):
    """L0 is REGISTER state, not a claim about the world. Two consequences pinned at once: the
    declaration leaves no fact, and it mints no node — so the token/entity duality (which reached
    the meta level: `produces` used to resolve to TWO nodes) cannot arise."""
    import ugm as h
    from ugm import derived_triples
    h.ingest(okb, [], "produces is a relation")
    assert okb.registers["vocabulary"] == {"produces": "transitive"}
    assert not [t for t in derived_triples(okb) if "relation" in t]
    assert not [n for n in okb.nodes() if okb.name(n) == "produces"]


def test_a_declared_relation_is_usable_by_the_next_utterance(okb):
    """The declaration must still DO its job — the register is a different home, not a weaker one."""
    import ugm as h
    h.ingest(okb, [], "produces is a relation")
    # A declared relation is a VERB (transitive) AND a NOUN — its name can be TALKED ABOUT (used as a
    # subject/object, e.g. `causes propagates has`), so `sync_vocabulary` gives it both categories.
    assert gi.session_banks(okb).grammar.lexicon.get("produces") == ["transitive", "noun"]
    assert h.ingest(okb, [], "get_beans produces beans").kind == "fact"
    assert ("get_beans", "produces", "beans") in gi.facts(okb)


def test_a_vocabulary_declaration_cannot_be_reasoned_over(okb):
    """⭐ THE ARGUMENT FOR A REGISTER RATHER THAN A META SCOPE IN THE GRAPH.

    As a graph fact, an L0 declaration was ordinary content that any domain rule could match —
    measured: `?y is meta when ?y is a relation` derived `produces is meta`. A meta scope would make
    that avoidable only BY DISCIPLINE, in every present and future reader; a register makes it
    structurally impossible. This codebase's own history (five idempotency defects of the
    'a discipline nobody restated' shape) is the argument against relying on discipline."""
    import ugm as h
    rules = []
    h.ingest(okb, rules, "produces is a relation")
    assert h.ingest(okb, rules, "?y is meta when ?y is a relation").kind == "rule"
    assert h.ingest(okb, rules, "is produces meta").answer == ["no (assumed)"]


def test_the_l0_form_is_not_reachable_from_the_object_grammar(okb):
    """The SCHEMA is hardcoded (Python forms, like `grammar.DECLARATION_FORMS`), which is what
    bounds the regress at two levels: the metalanguage cannot be extended from inside the object
    language. Pinned by the recognizer working on a KB whose grammar knows none of these words."""
    assert gi.recognize_vocabulary("produces is a relation") == ("produces", "relation")
    assert gi.recognize_vocabulary("the lion has a mane") is None
    # the NAC: a trailing word means this is NOT the declaration form
    assert gi.recognize_vocabulary("produces is a relation of sorts") is None


@pytest.mark.parametrize("text,cats", [
    # a RELATION is a VERB (transitive) AND a NOUN — its name is nameable (usable as an argument)
    ("produces is a relation", ["transitive", "noun"]),
    ("wolf is a noun", ["noun"]),
    ("snarls is a intransitive", ["intransitive"]),
])
def test_a_lexicon_declaration_reaches_the_grammar(okb, text, cats):
    """⭐ THE SILENT NO-OP, FIXED. `wolf is a noun` used to route `fact` and extend NOTHING — a user
    declaring a word got a success verdict and an inert fact. Measured: `wolf` was absent from the
    lexicon before and after. That is §8's "understanding ≠ parsing" at the META level, and it was
    the worst of the L0 defects precisely because it was silent rather than refused."""
    import ugm as h
    assert h.ingest(okb, [], text).kind == "vocabulary"
    word = text.split()[0]
    assert gi.session_banks(okb).grammar.lexicon.get(word) == cats


def test_a_declared_noun_is_usable_immediately(okb):
    import ugm as h
    h.ingest(okb, [], "wolf is a noun")
    h.ingest(okb, [], "snarls is a intransitive")
    assert h.ingest(okb, [], "the wolf snarls").kind == "fact"
    assert ("wolf", "snarls", "true") in gi.facts(okb)


@pytest.mark.parametrize("text", ["lion is a cat", "ada is a suspect"])
def test_an_ordinary_is_a_fact_is_not_mistaken_for_a_declaration(okb, text):
    """⚠ THE RISK THIS SLICE INTRODUCED, and the reason the shape match is NOT the decision.

    Binding the kind means the L0 form now fires on EVERY bare `W is a K` — including ordinary
    facts. What separates them is `resolve_vocabulary` asking the LIVE GRAMMAR whether `K` names a
    category. `cat` and `suspect` do not, so these fall through to the fact route. Were the check
    dropped, `ada is a suspect` would silently become a lexicon declaration and commit no fact."""
    import ugm as h
    assert h.ingest(okb, [], text).kind == "fact"
    subj, kind = text.split()[0], text.split()[-1]
    assert (subj, "is_a", kind) in gi.facts(okb)


# ---------------------------------------------------------------------------
# Slice 3 — the revision loop
# ---------------------------------------------------------------------------

CONTRA = ["the bengal lion has a mane",
          "the guzerat lion has no mane",
          "the lion has a mane"]


def test_the_default_reading_derives_the_contradiction(kb):
    """Percolating is the DEFAULT: it merges freely, so the exception collides with the rule. That
    collision is the evidence re-interpretation runs on — it must actually happen."""
    from ugm.interpretation import contradictions
    for line in CONTRA:
        gi.route(kb, line, banks(kb))
    assert contradictions(kb), "the merged reading must derive a contradiction"


def test_reconsider_revises_the_reading_and_clears_it(kb):
    for line in CONTRA:
        gi.route(kb, line, banks(kb))
    verdict, remaining = gi.reconsider(kb, banks(kb))
    assert verdict == gi.REVISED, f"expected a clean re-interpretation, got {verdict} {remaining}"
    facts = gi.facts(kb)
    # The exception and the generalization now stand on DIFFERENT entities...
    has = {s for s, p, o in facts if p == "has" and o == "mane"}
    hasnt = {s for s, p, o in facts if p == "has_not" and o == "mane"}
    assert has and hasnt and not (has & hasnt)
    # ...and the minted one is addressed by its DESCRIPTION, not a name it does not have.
    assert any("guzerat" in s for s in hasnt)


def test_reminting_is_evidence_driven_not_unconditional(kb):
    """The bare `the lion` mention must NOT be split: it heads no mintable production, so it stays
    the entity the generalization is about. This is what makes minting evidence-driven rather than
    the unconditional move a declared `mint` grammar makes."""
    for line in CONTRA:
        gi.route(kb, line, banks(kb))
    gi.reconsider(kb, banks(kb))
    assert ("lion", "has", "mane") in gi.facts(kb)


def test_an_uncontradicted_reading_is_left_alone(kb):
    gi.route(kb, "the lion has a mane", banks(kb))
    before = sorted(gi.facts(kb))
    assert gi.reconsider(kb, banks(kb)) == (gi.CLEAN, [])
    assert sorted(gi.facts(kb)) == before


def test_reconsider_does_not_touch_the_surface(kb):
    for line in CONTRA:
        gi.route(kb, line, banks(kb))
    surface = {n for n in kb.nodes() if any(kb.has_key(r, "cat") for r, _ in kb.relations_from(n))}
    gi.reconsider(kb, banks(kb))
    assert surface <= set(kb.nodes()), "re-interpretation must re-read the SAME surface"


def test_a_missing_grammar_path_raises_instead_of_parsing_as_text():
    """The trap: a non-existent path used to be parsed AS GRAMMAR TEXT, yielding an empty grammar
    that silently refused every sentence. The failure LOOKED like "the grammar is fast"."""
    with pytest.raises(FileNotFoundError):
        gi.declare_grammar(AttrGraph(), CORPUS / "no_such_grammar.cnl")
    with pytest.raises(FileNotFoundError):
        gi.declare_grammar(AttrGraph(), "corpus/no_such_grammar.cnl")


def test_a_grammar_that_declares_nothing_raises():
    """The backstop, independent of where the grammar came from: text that parsed to nothing is
    just as silent a failure as a bad path."""
    with pytest.raises(ValueError, match="no lexicon and no productions"):
        gi.declare_grammar(AttrGraph(), "this text declares nothing\nand neither does this")


# ---------------------------------------------------------------------------
# Order independence -- the epistemic invariant, swept over permutations
# ---------------------------------------------------------------------------

PERCOLATE = "slot head in np from modifier plus np is right head"
MINT = "mint head in np from modifier plus np under right head"

#: Mixes MODIFIED noun phrases (which can mint a subkind) with a BARE one, and gives the same
#: subkind facts across two sentences -- the case where individuation has to agree.
#: THREE sentences, not four: 6 orders instead of 24, and the structure that found the defect is
#: fully preserved -- two mentions of the SAME subkind (individuation must agree) plus a bare `lion`
#: sentence whose fact is what leaked into the other sentences' verdicts. The 4th sentence added 18
#: orders and 30s of suite time without adding a case.
ORDER_CORPUS = [
    "the african lion has a mane",
    "the african lion is strong",
    "the lion has a tail",
]


def _grammar_text(minting):
    text = (CORPUS / "loudon_grammar.cnl").read_text(encoding="utf-8")
    if not minting:
        return text
    assert PERCOLATE in text, "the percolate line must be present to be swapped"
    return text.replace(PERCOLATE, MINT)


#: Compiled ONCE per reading. `declare_grammar` generates ~200 rules, and the sweep opens 48
#: sessions -- recompiling per session cost 86s of suite time for no coverage.
_ORDER_BANKS: dict = {}


def _order_banks(minting):
    if minting not in _ORDER_BANKS:
        _ORDER_BANKS[minting] = compile_grammar(load_grammar(_grammar_text(minting)))
    return _ORDER_BANKS[minting]


def _session(order, minting):
    g = AttrGraph()
    g.registers[gi.GRAMMAR_REGISTER] = bank = _order_banks(minting)
    verdicts = frozenset((s, gi.route(g, s, bank)[0]) for s in order)
    return frozenset(gi.facts(g)), verdicts


@pytest.mark.parametrize("minting", [False, True], ids=["percolate", "mint"])
def test_interpretation_does_not_depend_on_utterance_order(minting):
    """If two sentences speak about the same thing, the order they arrived in must not change what
    the system believes -- NOR what it reports believing.

    Both halves matter and only the second has ever been broken. Sweeping all 24 orders of a
    4-sentence corpus (since trimmed to 3; see ORDER_CORPUS) found the FACTS identical in every order, while the ROUTING VERDICT disagreed
    in 22 of 24: `route` asked "does an entity this utterance mentions carry a content relation that
    is new by NODE ID", which (a) cannot see a minted subkind, reachable from no token, and (b)
    counts another sentence's fact, because `reinterpret` re-mints everything so re-derived looks
    new. Fixed by deciding from the PARSE (`asserts_content`); this is the guard."""
    orders = list(itertools.permutations(ORDER_CORPUS))
    baseline = _session(orders[0], minting)
    for order in orders[1:]:
        assert _session(order, minting) == baseline, f"order changed the outcome: {order}"


def test_a_minted_subkind_is_reported_as_a_fact():
    """The false NEGATIVE on its own: facts landed on the minted entity while the caller was told
    `unrecognized`, because the subkind hangs off the span's `head` slot and no token denotes it."""
    g = AttrGraph()
    g.registers[gi.GRAMMAR_REGISTER] = _order_banks(True)
    kind, _data = gi.route(g, "the african lion has a mane", gi.session_banks(g))
    assert kind == "fact"
    assert ("<is african & is_a lion>", "has", "mane") in gi.facts(g)


def test_extending_the_scope_equals_rebuilding_it():
    """Keeping ONE interpretation and growing it must agree with tearing it down every utterance.

    This is the gate on incremental interpretation. `route` rebuilds today (`reinterpret` discards
    and re-reads the whole standing surface), which is correct but costs a whole-session pass per
    utterance. Extending is only admissible if it lands in the same place.

    It did NOT, at first, and both failures were LATENT IDEMPOTENCY DEFECTS that discard-first was
    silently paying for -- three utterances gave 5 contradiction markers instead of 1 and 872 nodes
    instead of 612:
      * `contradiction_bank`'s `<contradiction>?` is a BOUND literal, minted fresh per firing, so
        re-running the bank duplicated the marker (the `span_bank` defect, fourth of its family).
      * `interpret_mentions` called `add_node(name)` unconditionally, minting a parallel entity per
        name on every pass.
    Both are fixed at the source rather than worked around here, so the equivalence is a property of
    the banks, not of this test's setup."""
    def rebuilt():
        g = AttrGraph()
        g.registers[gi.GRAMMAR_REGISTER] = bank = _order_banks(False)
        for s in CONTRA:
            gi.route(g, s, bank)
        return g

    def extended():
        g = AttrGraph()
        g.registers[gi.GRAMMAR_REGISTER] = bank = _order_banks(False)
        for s in CONTRA:                            # a corpus that CONTRADICTS, so the marker
            parse(g, s, bank)                       # duplication is actually exercised
            interpret(g, bank, gi.live_scope(g),
                      slots=bank.reinterp_slots, slot_preds=bank.reinterp_slot_preds)
        return g

    a, b = rebuilt(), extended()
    assert sorted(gi.facts(a)) == sorted(gi.facts(b))
    assert len(contradictions(a)) == len(contradictions(b)), "a kept scope must not duplicate markers"
    assert len(list(a.nodes())) == len(list(b.nodes())), "a kept scope must not accrete nodes"


# ---------------------------------------------------------------------------
# CONTEXT-GATED ASSERTION — a span inside a suppressing context asserts nothing
# ---------------------------------------------------------------------------

#: A conditional, declared on top of the shipped grammar. Its two halves genuinely ARE clauses,
#: which is the whole point: the non-asserting CATEGORY trick that works for hedging cannot work
#: here without duplicating every clause production.
_COND = """
when is a subordinator
dangerous is a adj
hungry is a adj
sub expands to subordinator plus clause
ccl expands to clause plus sub
clause expands to ccl
"""
_SUPPRESS = "ccl suppresses\n"

_CONDITIONAL = "a lion is dangerous when a lion is hungry"


def _kb(extra: str):
    g = AttrGraph()
    gi.declare_grammar(g, (CORPUS / "loudon_grammar.cnl").read_text(encoding="utf-8") + extra)
    return g


def test_without_gating_a_conditional_asserts_both_halves():
    """PINS THE DEFECT the gate exists to fix, so the gate cannot be quietly removed.

    `a lion is dangerous when a lion is hungry` asserts NEITHER half — but each half is a `clause`
    span, so `clause asserts subj is adjc when adjc` fires on both and writes two claims the
    sentence does not make. Parsed, reported `fact`, committed falsehoods."""
    kb = _kb(_COND)
    gi.route(kb, _CONDITIONAL, gi.session_banks(kb))
    facts = gi.facts(kb)
    assert ("lion", "is", "dangerous") in facts and ("lion", "is", "hungry") in facts


def test_a_suppressing_context_blocks_assertion():
    """`ccl suppresses` — one declaration — and the conditional commits nothing."""
    kb = _kb(_COND + _SUPPRESS)
    gi.route(kb, _CONDITIONAL, gi.session_banks(kb))
    assert gi.facts(kb) == [] or not any(
        t in gi.facts(kb) for t in [("lion", "is", "dangerous"), ("lion", "is", "hungry")])


def test_gating_leaves_ordinary_sentences_alone():
    """The gate must be CONTEXTUAL, not a blanket off-switch: a clause outside any suppressing
    span still asserts, in either utterance order."""
    for order in ([_CONDITIONAL, "the lion has a mane"],
                  ["the lion has a mane", _CONDITIONAL]):
        kb = _kb(_COND + _SUPPRESS)
        b = gi.session_banks(kb)
        for s in order:
            gi.route(kb, s, b)
        assert ("lion", "has", "mane") in gi.facts(kb), f"lost the plain fact in order {order}"
        assert ("lion", "is", "hungry") not in gi.facts(kb)


def test_a_grammar_declaring_no_suppression_is_unaffected():
    """Declare-before-use: the gate costs a grammar that does not use it nothing at all — not even
    an extra NAC premise on every assert rule.

    Builds its OWN suppression-free grammar rather than using the shipped one. It used to rely on
    `loudon_grammar.cnl` declaring no suppression, which stopped being true the moment questions
    landed (`qclause suppresses`) — the test then failed for a reason that had nothing to do with the
    property it exists to check. A declare-before-use test must supply the un-declaring case itself.

    Strips EVERY suppression declaration rather than a named one: the first repair removed only
    `qclause suppresses` and broke again one force later when goals added `gclause suppresses`. A
    fixture that enumerates what it must exclude will keep breaking as the grammar grows; one that
    describes it does not."""
    from ugm.cnl.grammar import SUPPRESSED
    plain = "\n".join(line for line in (CORPUS / "loudon_grammar.cnl")
                      .read_text(encoding="utf-8").splitlines()
                      if not line.strip().endswith(" suppresses"))
    g = AttrGraph()
    gi.declare_grammar(g, plain)
    banks = gi.session_banks(g)
    assert not banks.grammar.suppressing, "this grammar was supposed to declare no suppression"
    assert not any(p.p == SUPPRESSED for r in banks.asserts for p in r.nac)
    gi.route(g, "the lion has a mane", banks)
    assert ("lion", "has", "mane") in gi.facts(g)


@pytest.mark.parametrize("plain,hedged,pred,obj", [
    ("the lion has a mane",       "the lion generally has a mane",       "has",   "mane"),
    ("the lion is strong",        "the lion generally is strong",        "is",    "strong"),
    ("the lion roars",            "the lion generally roars",            "roars", "true"),
    ("the lion hunts at night",   "the lion generally hunts at night",   "at",    "night"),
])
def test_every_plain_shape_has_a_hedged_counterpart(kb, plain, hedged, pred, obj):
    """REGRESSION, and it was SILENT. `clause` declares several assertion shapes; the first hedging
    slice mirrored only the three it had tests for (transitive, adjective, kind) and missed the
    INTRANSITIVE and PREPOSITIONAL ones. Those sentences parsed, routed as `fact`, and committed
    NOTHING — no ink and no fork.

    Root cause: the band was taken from the assertion's own `when` guard, and the declaration
    surface allows ONE guard, so any shape needing its own (`unless obj`, `when pobj`) was
    unwritable. Fixed by declaring the band slot once per category (`hclause hedges under hedge`).

    Found by a cold-context translator reading the declarations — NOT by the tests, which only
    exercised the shapes that had been built. Hence this parametrization over shapes rather than
    another example of the two that already worked."""
    from ugm.possibility import possibility
    b = banks(kb)
    gi.route(kb, plain, b)
    assert (("lion", pred, obj)) in gi.facts(kb), f"plain shape broken: {plain!r}"

    kb2 = _kb("")
    gi.route(kb2, hedged, banks(kb2))
    assert gi.facts(kb2) == [], f"a hedge must commit no ink: {hedged!r}"
    assert possibility(kb2, pred, "lion", obj) == 0.75, (
        f"hedged shape committed NOTHING (the silent gap): {hedged!r}")


# ---------------------------------------------------------------------------
# THE TOKEN/ENTITY DUALITY — a DERIVED fact must land in the interpretation
# ---------------------------------------------------------------------------

_ADJ = "dangerous is a adj\nhungry is a adj\n"

#: The explicit, unambiguous core form for conditionality. It needs no grammar support: intake routes
#: a `HEAD when BODY` line to the rule layer BEFORE the grammar fork, so this is the shipped surface.
_RULE = "?x is dangerous when ?x is hungry"


def test_a_derived_fact_lands_in_the_interpretation_not_on_the_token():
    """⭐ THE DUALITY, WHERE IT ACTUALLY BIT — and it was silent, and right by luck.

    A rule MATCHED its premise on the interpretation entity (where the fold writes content) and
    EMITted its conclusion to the TOKEN, because `nodes_named` returns the token first and
    `resolve_write_node` took `[0]`. Measured before the fix: `is hungry` on the entity, `is
    dangerous` on the token — so the derived fact fell OUTSIDE the interpretation scope entirely.
    Invisible to `scope_facts`, uncleared by `discard_scope`, unrevisable by `reconsider`, and
    surviving a re-reading that invalidates its own premise. The question still answered `yes`,
    because name resolution also happened to pick the token first.

    That is why the assertion here is on `gi.facts` (the SCOPE) and not on the answer: the answer was
    already `yes` while the system believed it in the wrong layer. Asking `is lion dangerous` first
    is what forces the derivation to materialize."""
    from ugm.intake import ingest
    kb = _kb(_ADJ)
    rules = []
    ingest(kb, rules, _RULE)
    ingest(kb, rules, "the lion is hungry")
    ingest(kb, rules, "is lion dangerous")

    assert ("lion", "is", "dangerous") in gi.facts(kb), (
        "a derived fact escaped the interpretation scope — it landed on the discourse token, where "
        "nothing can discard or revise it")
    # ... and the surface stayed surface: the token carries no content, only its denotation.
    for t in kb.nodes_named("lion"):
        if any(kb.has_key(r, DENOTES) for r, _o in kb.relations_from(t)):
            preds = {kb.predicate(r) for r, _o in kb.relations_from(t)}
            assert "is" not in preds, "content landed on a surface token"


def test_a_derived_fact_is_discardable_like_any_other_judgement():
    """The POINT of landing it in the scope, not merely a tidier address.

    A conclusion derived from an interpretation is itself a judgement about this reading, so a
    re-interpretation must be able to take it back. When the conclusion sat on the token it outlived
    the premise that produced it — permanent, and attributable to nothing."""
    from ugm.intake import ingest
    kb = _kb(_ADJ)
    rules = []
    ingest(kb, rules, _RULE)
    ingest(kb, rules, "the lion is hungry")
    ingest(kb, rules, "is lion dangerous")
    assert ("lion", "is", "dangerous") in gi.facts(kb)

    gi.rebuild(kb, gi.session_banks(kb))            # discard the reading and re-read the surface
    assert ("lion", "is", "dangerous") not in gi.facts(kb), (
        "a derived fact survived the discard of the interpretation it was derived from")
    assert ("lion", "is", "hungry") in gi.facts(kb), "re-reading lost the asserted premise"


# ---------------------------------------------------------------------------
# DERIVED VOCABULARY — a KB's `R is a relation` IS its grammar lexicon entry
# ---------------------------------------------------------------------------

def _core_grammar() -> str:
    """The Loudon grammar with its lion-domain CONTENT words dropped — productions, closed classes
    and slots only. A domain-neutral core, so these tests exercise DERIVED vocabulary rather than
    vocabulary that happened to be declared already."""
    import re
    src = (CORPUS / "loudon_grammar.cnl").read_text(encoding="utf-8")
    content = {"modifier", "noun", "adj", "comparative", "transitive", "intransitive", "hedge"}
    out = []
    for line in src.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"^(\S+) is a (\S+)$", s)
        if m and m.group(2) in content:
            continue
        out.append(s)
    return "\n".join(out)


def _open_kb():
    g = AttrGraph()
    gi.declare_grammar(g, _core_grammar(), open_class="noun")
    return g


def test_a_declared_relation_becomes_grammar_vocabulary():
    """⭐ WHY MAKING THIS ROUTE THE DEFAULT COSTS ~NOTHING TO MIGRATE.

    A predicate has ALWAYS needed a declaration: the shipped route refuses `get_beans produces beans`
    until the KB says `produces is a relation`. So the grammar route's `produces is a transitive` was
    never a new burden — it is the SAME declaration respelled, and therefore derivable. An existing
    KB migrates without editing its corpus.

    Measured across every shipped corpus: 9 distinct predicates, and the derived grammar parses 69 of
    76 fact lines with ZERO mis-mappings."""
    from ugm.intake import ingest
    kb, rules = _open_kb(), []
    ingest(kb, rules, "produces is a relation")
    assert ingest(kb, rules, "get_beans produces beans").kind == "fact"
    assert ("get_beans", "produces", "beans") in gi.facts(kb)


def test_an_undeclared_predicate_is_still_refused():
    """THE SAFETY PROPERTY THE DERIVATION MUST NOT DISSOLVE. Deriving vocabulary must not become
    'accept any three words' — declare-before-use is what makes a refusal mean something. An
    undeclared predicate is REFUSED (loud, countable), not guessed at."""
    from ugm.intake import ingest
    kb, rules = _open_kb(), []
    assert ingest(kb, rules, "grind_beans needs beans").kind == "unrecognized"
    assert gi.facts(kb) == []


def test_vocabulary_declared_mid_session_takes_effect():
    """RUNTIME GROWTH IS THE REAL REQUIREMENT, not a one-off read when the grammar is declared.

    A corpus declares its relations in its OWN text, so on this route `needs is a relation` is itself
    parsed by the grammar — the vocabulary arrives DURING ingestion, after the banks were compiled.
    A sync that only ran at `declare_grammar` time would leave every such corpus refusing its own
    content."""
    from ugm.intake import ingest
    kb, rules = _open_kb(), []
    assert ingest(kb, rules, "grind_beans needs beans").kind == "unrecognized"
    ingest(kb, rules, "needs is a relation")
    assert ingest(kb, rules, "grind_beans needs beans").kind == "fact"
    assert ("grind_beans", "needs", "beans") in gi.facts(kb)


def test_an_explicit_grammar_declaration_beats_the_derived_default():
    """The derivation fills a GAP in the VERB category; it never overrides what a grammar actually
    says. `roars` declared `intransitive` must STAY intransitive even if the KB also calls it a
    relation — the derived `transitive` default must NOT re-categorise hand-written vocabulary.
    (The additive NOUN reading is orthogonal: a declared relation is nameable, so `roars` gains a
    noun category too — but its verb category is still the explicit `intransitive`, never `transitive`.)"""
    from ugm.intake import ingest
    kb = AttrGraph()
    gi.declare_grammar(kb, _core_grammar() + "\nroars is a intransitive\n", open_class="noun")
    ingest(kb, [], "roars is a relation")
    gi.sync_vocabulary(kb)
    cats = gi.session_banks(kb).grammar.lexicon["roars"]
    assert "intransitive" in cats and "transitive" not in cats   # the explicit VERB category won
    assert cats == ["intransitive", "noun"]                      # + the nameable-relation noun reading


# ---------------------------------------------------------------------------
# THE `ask` FORCE — a question routed by the GRAMMAR, committing nothing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question,expected", [
    ("is lion strong",         ("lion", "is",   "strong")),
    ("is lion has mane",       ("lion", "has",  "mane")),
    ("is lion a cat",          ("lion", "is_a", "cat")),
    ("whether lion is strong", ("lion", "is",   "strong")),
])
def test_a_question_routes_by_its_parse_and_commits_nothing(question, expected):
    """⭐ FORCE, not content (`design/form_inventory.md` §4b). A question is not a weaker assertion:
    it commits NOTHING and changes no beliefs, so `<cat> asks subj pred obj` generates no fold rule
    at all — the declaration only says which slots carry the asked triple, and the router reads them.

    Routed by WHICH CATEGORY THE PARSE PRODUCED (`qclause`, which declares `asks`), never by sniffing
    the utterance string — the declarative replacement for intake's ordered if-ladder (§D.1)."""
    kb = AttrGraph()
    gi.declare_grammar(kb, CORPUS / "loudon_grammar.cnl", open_class="noun")
    b = gi.session_banks(kb)
    gi.route(kb, "the lion has a mane", b)
    gi.route(kb, "the lion is strong", b)
    before = sorted(gi.facts(kb))

    kind, data = gi.route(kb, question, b)
    assert kind == "question", f"{question!r} was not recognised as a question"
    assert data["query"] == expected
    assert sorted(gi.facts(kb)) == before, "a question changed what the system believes"


def test_a_whether_question_does_not_assert_its_own_complement():
    """PINS A REAL DEFECT, found while building this: `whether P` embeds a genuine `clause` span, so
    `clause asserts …` fired on it and the QUESTION ASSERTED ITS OWN CONTENT — measured, `whether lion
    is huge` wrote `lion is_a huge`.

    That is exactly the failure `form_inventory.md` §8 describes: perfect content mapping, zero
    force. The domination gate built for conditionals (`qclause suppresses`) is the mechanism, reused
    rather than duplicated — which is evidence the gate generalises beyond the case it was built for."""
    kb = AttrGraph()
    gi.declare_grammar(kb, CORPUS / "loudon_grammar.cnl", open_class="noun")
    b = gi.session_banks(kb)
    kind, _d = gi.route(kb, "whether lion is huge", b)
    assert kind == "question"
    assert gi.facts(kb) == [], f"a question asserted its complement: {gi.facts(kb)}"


def test_a_question_is_answered_through_the_shipped_machinery():
    """END TO END through real `ingest`: the grammar decides FORCE, but ANSWERING is unchanged — the
    same `_answer_with_ask` the shipped route uses, handed the structured goal `("yesno", s, p, o)`
    the grammar read off the slots. Moving force onto the grammar must not fork the answering path."""
    from ugm.intake import ingest
    kb = AttrGraph()
    gi.declare_grammar(kb, CORPUS / "loudon_grammar.cnl", open_class="noun")
    rules = []
    ingest(kb, rules, "the lion has a mane")
    assert ingest(kb, rules, "is lion has mane").answer == ["yes"]
    assert ingest(kb, rules, "is lion a cat").answer == ["no (assumed)"]
    assert ("lion", "has", "mane") in gi.facts(kb), "answering disturbed the facts"


def test_a_goal_reifies_and_commits_no_fact():
    """⭐ THE `goal` FORCE. Like `ask` it commits no FACT — `gclause` declares no `asserts`, and
    suppresses its complement so `goal lion is a target` does not ASSERT that the lion IS one. Unlike
    `ask` it LEAVES SOMETHING BEHIND: a `<goal>` node the act loop runs on, which is why the router
    reifies rather than merely answering.

    That difference is the reason `form_inventory.md` §4b distinguishes forces that return a value
    from forces that change state — it decides reader-vs-reification, not taste."""
    kb = AttrGraph()
    gi.declare_grammar(kb, CORPUS / "loudon_grammar.cnl", open_class="noun")
    b = gi.session_banks(kb)
    gi.route(kb, "the lion has a mane", b)
    before = sorted(gi.facts(kb))

    kind, data = gi.route(kb, "goal lion is a target", b)
    assert kind == "goal"
    assert data["goal"] == ("lion", "target")
    assert sorted(gi.facts(kb)) == before, "a goal asserted its own content"


def test_a_grammar_minted_goal_is_identical_to_the_shipped_one():
    """PARITY IS THE ACCEPTANCE CRITERION, as it was for `Band` vs `possibility.add_fork`: the act
    loop and `intake`'s `nodes_named(GOAL)` diff must not be able to tell the two routes apart. A
    parallel-but-different encoding would be worse than no feature."""
    from ugm.focus import GOAL
    from ugm.intake import ingest

    def goal_shape(g):
        return sorted(sorted((g.predicate(r), g.name(o)) for r, o in g.relations_from(n))
                      for n in g.nodes_named(GOAL))

    viaGrammar = AttrGraph()
    gi.declare_grammar(viaGrammar, CORPUS / "loudon_grammar.cnl", open_class="noun")
    out = ingest(viaGrammar, [], "goal lion is a target")
    assert out.kind == "goal"

    shipped = AttrGraph()
    ingest(shipped, [], "goal lion is a target")

    assert goal_shape(viaGrammar) == goal_shape(shipped) != [], (
        "the grammar route minted a goal the shipped machinery would not recognise")


def test_two_goals_do_not_collapse_into_one():
    """The `<goal>` node is minted FRESH while its endpoints INTERN, and the asymmetry is
    load-bearing: interning the goal too would make a second goal reuse the first node and hang a
    second `target` on it — one goal with two targets rather than two goals."""
    from ugm.focus import GOAL
    from ugm.intake import ingest
    kb = AttrGraph()
    gi.declare_grammar(kb, CORPUS / "loudon_grammar.cnl", open_class="noun")
    ingest(kb, [], "goal lion is a target")
    ingest(kb, [], "goal mane is a target")
    goals = kb.nodes_named(GOAL)
    assert len(goals) == 2, f"two goals collapsed into {len(goals)}"
    for n in goals:
        targets = [o for r, o in kb.relations_from(n) if kb.predicate(r) == "target"]
        assert len(targets) == 1, "a goal ended up with more than one target"

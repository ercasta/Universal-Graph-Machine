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

"""The GRAMMAR intake route (integration step 2) — facts on ENTITIES, not tokens.

These pin the fork's contract while it is still a fork: the surface survives, the judgements are
scoped, and the three outcomes are distinguishable.
"""
from __future__ import annotations

import pathlib

import pytest

from ugm import AttrGraph
from ugm.cnl import grammar_intake as gi
from ugm.interpretation import DENOTES, discard_scope

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

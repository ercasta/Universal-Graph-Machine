"""Verb-agreement confluence — `does X have Y` (question) must reach the same predicate as `X has Y`
(assertion), or a stored/derived fact silently answers `no (assumed)`.

This is SUGAR (`baroque-vs-fundamental`): `has`/`have` are surface inflections of ONE relation, folded
the same meaning-free way `are`->`is` already is (`forms.normalize_lexical`). What it PROTECTS is the
fundamental confluence invariant — both surfaces of a relation canonicalize to one predicate. The bug
was that the question path never applied the morphology fold the assertion path did.
"""
from ugm.cnl.authoring import load_corpus
from ugm.cnl.forms import normalize_lexical
from ugm.cnl.query import recognize
from ugm.intake import ingest


def test_does_have_question_matches_a_stored_has_fact():
    """The direct case: `X has Y` stored, asked through the natural `does X have Y`."""
    kb, rules = load_corpus("")
    for u in ["has is a relation", "lion has hunger"]:
        ingest(kb, rules, u)
    assert ingest(kb, rules, "does lion have hunger").answer == ["yes"]


def test_does_have_question_matches_a_derived_fact():
    """The causation case that first surfaced the gap: the effect is DERIVED through a `causes` link,
    and the natural do-support question reaches it."""
    kb, rules = load_corpus("")
    for u in ["has is a relation", "causes is a relation", "lion has hunger",
              "hunger causes aggression",
              "?x has ?effect when ?x has ?cause and ?cause causes ?effect"]:
        ingest(kb, rules, u)
    assert ingest(kb, rules, "does lion have aggression").answer == ["yes"]


def test_question_and_assertion_agree_on_the_predicate():
    """The invariant at the parse level: the question binds `has`, the same predicate `X has Y` stores.
    This is what fails if the question-side fold is dropped (`have` would be asked)."""
    assert recognize("does lion have hunger")["p"] == "has"


def test_normalize_lexical_folds_have_but_not_had():
    assert normalize_lexical("does lion have hunger") == "does lion has hunger"   # agreement -> canonical
    assert normalize_lexical("they are young") == "they is young"                 # the copula it already did
    assert normalize_lexical("lion had hunger") == "lion had hunger"              # PAST TENSE left alone

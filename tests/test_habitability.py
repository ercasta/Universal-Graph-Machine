"""
HABITABILITY — loud walls, never silent misreads (the §4a discipline, hardened).

A controlled language is habitable when its boundary is CRISP: an utterance inside the grammar
has exactly one meaning; an utterance outside it is REJECTED with guidance — never confidently
misinterpreted. The failure class pinned here: a generic question form binding a grammar KEYWORD
into a NAME slot (`is a ada thief` -> s='a'), which used to answer a silent "no (assumed)" about
a subject named 'a' — teaching the user a false model of the language. The lint
(`query._kw_in_name_slot`) skips keyword-tainted readings (a cleaner, more specific form may
also have fired) and treats an all-tainted question as UNRECOGNIZED.
"""
import warnings

from ugm.cnl.authoring import load_corpus
from ugm.cnl.query import ask_goal, _parse_question
from ugm.intake import ingest


def _ingest(kb, rules, utt):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ingest(kb, rules, utt)


def test_keyword_in_name_slot_is_rejected_not_answered():
    # `is a ada thief` used to parse s='a' (the is_a marker read as a subject) and answer
    # "no (assumed)" — a confident answer from a mis-parse. Now: unrecognized, loudly.
    assert _parse_question("is a ada thief") is None
    kb, rules = load_corpus("ada is a suspect")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert ask_goal(kb, "is a ada thief", rules) == ["(no question form recognized this)"]


def test_intake_gives_nearest_form_guidance_for_the_rejected_reading():
    # At the conversation surface the wall TEACHES: the utterance routes to UNRECOGNIZED and
    # carries the nearest form templates (the §4a guidance), instead of answering wrongly.
    kb, rules = load_corpus("?x is thief when ?x is a suspect and ?x is not cleared")
    _ingest(kb, rules, "ada is a suspect")
    out = _ingest(kb, rules, "is a ada thief")
    assert out.kind == "unrecognized"
    assert out.nearest, "the rejection should come with nearest-form guidance"


def test_clean_readings_are_untouched_and_preferred():
    # The lint SKIPS tainted readings rather than rejecting the question outright, so a question
    # with a clean reading from a more specific form still answers — including the keyword-heavy
    # `is S a O` (the 'a' is the form's literal marker, not a bound name) and the inverted why.
    kb, rules = load_corpus("?x is thief when ?x is a suspect and ?x is not cleared")
    _ingest(kb, rules, "ada is a suspect")
    assert _ingest(kb, rules, "is ada a suspect").answer == ["yes"]
    assert _ingest(kb, rules, "is ada thief").answer == ["yes"]
    # `why …` now has its own route + field (backward diagnosis, test_why_diagnosis): the derivation
    # trace lands in `.explanation` (a trace is not a yes/no `.answer`), and the kind is `why`.
    out = _ingest(kb, rules, "why is ada thief")
    assert out.kind == "why"
    assert any("assumed not: ada is cleared" in ln for ln in out.explanation)

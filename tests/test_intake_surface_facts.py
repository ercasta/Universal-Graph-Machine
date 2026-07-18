"""Intake — surface normalization on the FACT path (2026-07-18).

The determiner / noun-phrase bank (`forms.surface_forms`) was already applied on the QUESTION path
(`cnl/query.py`) and the loose-rule path, but NOT when loading facts. So `the lion is a cat` was
unrecognized while `lion is a cat` folded, and a multi-word noun phrase never decomposed. The forms
existed; only the wiring was missing (`authoring._recognize`).

Found by running the pipeline over a real book (`bench/spike_loudon.py`, Mrs. Loudon's
*Entertaining Naturalist*): intake coverage on translated prose was **0%**, and these two gaps
accounted for essentially all of it — 0% -> 79% once wired.

Why it mattered more than a coverage number: dropping unparsed sentences is NOT neutral.
EXCEPTIONS are linguistically marked ("without any mane", "no", "unlike"), so a partially-covering
parser systematically loses the exceptions and keeps the generalizations, biasing anything that
learns downstream toward confident over-generalization.
"""
import pytest

import ugm as h
from ugm import AttrGraph, derived_triples


def _facts(*lines: str) -> set:
    kb = AttrGraph()
    for line in lines:
        h.ingest(kb, [], line)
    return {t for t in derived_triples(kb) if t[1] not in ("first", "next")}


# ---------------------------------------------------------------------------
# Determiners — the subject slot now accepts one, as the object slot always did
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("line", [
    "the lion is a cat",
    "a lion is a cat",
    "this lion is a cat",
])
def test_determiner_on_the_subject_is_accepted(line):
    assert ("lion", "is_a", "cat") in _facts(line)


def test_bare_subject_still_works():
    """The path that already worked must be unchanged."""
    assert ("lion", "is_a", "cat") in _facts("lion is a cat")


def test_determiner_with_a_non_copula_verb():
    assert ("lion", "has", "mane") in _facts("the lion has a mane")


def test_determiner_does_not_leak_into_the_fact():
    """`the`/`a` must not survive as entities or predicates."""
    facts = _facts("the lion is a cat")
    tokens = {t for triple in facts for t in triple}
    assert "the" not in tokens and "a" not in tokens


# ---------------------------------------------------------------------------
# Multi-word noun phrases DECOMPOSE (design choice: structure exposed, not hidden)
# ---------------------------------------------------------------------------

def test_multiword_noun_phrase_decomposes_to_head_plus_attribute():
    """"the african lion" -> head `lion` + `lion is african`, rather than an opaque
    `african_lion` string. This is the documented design (forms.py §2), and it is what makes the
    modifier reachable by reasoning."""
    facts = _facts("the african lion is a lion")
    assert ("lion", "is", "african") in facts
    assert ("lion", "is_a", "lion") in facts


# ---------------------------------------------------------------------------
# KNOWN DEFECTS — recorded so they are visible, not implied to work
# ---------------------------------------------------------------------------

def test_undeclared_verb_with_preposition_MIS_PARSES():
    """`the lion lives in africa` routes as a FACT but folds to nonsense.

    `lives` is an undeclared verb, so the noun-phrase decomposition treats "lion lives" as an NP
    with head `lives` and modifier `lion`. The result is `lives is lion` + `lives in africa`.

    This is worse than the unrecognized case it replaced: the line now SUCCEEDS and writes garbage.
    It is why the book-corpus coverage figure must be read as ROUTING, not correctness — measuring
    `route == "fact"` counted this line as a win.

    Pinned as-is so a fix flips this test loudly rather than passing silently."""
    facts = _facts("the lion lives in africa")
    assert ("lives", "is", "lion") in facts, f"mis-parse changed shape: {facts}"
    assert not any(s == "lion" and o == "africa" for s, _p, o in facts)


def test_negated_object_is_dropped_but_the_line_partly_ingests():
    """`the guzerat lion has no mane` is UNRECOGNIZED, yet still writes `lion is guzerat`.

    So an unrecognized line is not inert — it can leave a partial fact behind. And the dropped part
    is the NEGATION, which is exactly the exception-bearing construction (see the module docstring):
    the corpus states a real exception and the KB ends up with only the generalization."""
    facts = _facts("the guzerat lion has no mane")
    assert ("lion", "is", "guzerat") in facts          # the partial write
    assert not any(p == "has" for _s, p, _o in facts)  # the negated fact is simply gone


# ---------------------------------------------------------------------------
# Regression guard for the real-corpus scenario
# ---------------------------------------------------------------------------

def test_book_sentences_fold(  ):
    """Verbatim-derived lines from the Loudon corpus that previously ALL failed."""
    facts = _facts(
        "the lion is a cat",
        "the lion has a mane",
        "the lion has a tail",
        "the lion is strong",
    )
    assert ("lion", "is_a", "cat") in facts
    assert ("lion", "has", "mane") in facts
    assert ("lion", "has", "tail") in facts

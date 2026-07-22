"""`what causes X` — variable-binding backward diagnosis (enumerate the causes), the counterpart to
`why` (explain ONE known fact). It is the person/thing twin of the existing `who P O` wh-question:
`what` is a SUBJECT wh for a non-person unknown, mapping to the SAME `who` qtype (the substrate is
label-less, so the split carries no query difference). Before this, `what causes X` mis-routed to the
FACT path and silently asserted a bogus `what causes X` fact.
"""
from ugm import derived_triples
from ugm.cnl.authoring import load_corpus
from ugm.cnl.query import recognize
from ugm.intake import ingest


def _causes_kb():
    kb, rules = load_corpus("")
    for u in ["causes is a relation", "hunger causes aggression", "fear causes aggression"]:
        ingest(kb, rules, u)
    return kb, rules


def test_what_causes_enumerates_the_causes():
    kb, rules = _causes_kb()
    out = ingest(kb, rules, "what causes aggression")
    assert out.kind == "answer"
    assert out.answer == ["fear causes aggression", "hunger causes aggression"]


def test_what_causes_asserts_no_bogus_fact():
    """The mis-route it replaces: `what` must never land as a subject entity."""
    kb, rules = _causes_kb()
    ingest(kb, rules, "what causes aggression")
    assert [t for t in derived_triples(kb) if t[0] == "what"] == []


def test_what_and_who_agree():
    """`what` and `who` are the same query in a label-less substrate — both enumerate the subject."""
    kb, rules = _causes_kb()
    what = ingest(kb, rules, "what causes aggression").answer
    who = ingest(kb, rules, "who causes aggression").answer
    assert what == who


def test_what_maps_to_the_who_qtype_at_the_parse():
    assert recognize("what causes aggression")["qtype"] == "who"
    assert recognize("what is a predator")["qtype"] == "who"


def test_what_is_a_kind_enumerates_members():
    kb, rules = load_corpus("")
    for u in ["lion is a predator", "wolf is a predator"]:
        ingest(kb, rules, u)
    out = ingest(kb, rules, "what is a predator")
    assert out.kind == "answer"
    assert set(out.answer) == {"lion is_a predator", "wolf is_a predator"}

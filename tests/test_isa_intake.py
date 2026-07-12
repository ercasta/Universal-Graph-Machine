"""Phase 8.1 — unified intake routing (docs/cnl_intake_design.md §1, §D).

One entry `ingest(kb, rules, utterance)`; the route EMERGES from which forms fire, not a string sniff.
"""
from ugm.intake import ingest
from ugm.world_model import Graph


RULES = """
?x is innocent when ?x in library
?x is cleared when ?x is innocent
?x is thief when ?x is a suspect and ?x is not cleared
"""


def _fresh():
    from ugm.cnl.authoring import load_corpus
    return load_corpus(RULES)          # (kb, rules)


def test_assertion_routes_to_fact():
    kb, rules = _fresh()
    out = ingest(kb, rules, "bo is a suspect")
    assert out.kind == "fact"


def test_question_routes_to_answer():
    kb, rules = _fresh()
    ingest(kb, rules, "bo is a suspect")
    out = ingest(kb, rules, "is bo thief")
    assert out.kind == "answer"
    assert out.answer == ["yes"]       # bo is a suspect, not cleared -> thief


def test_question_negative():
    kb, rules = _fresh()
    ingest(kb, rules, "bo is a suspect")
    ingest(kb, rules, "bo in library")     # -> innocent -> cleared
    out = ingest(kb, rules, "is bo thief")
    assert out.kind == "answer"
    assert out.answer == ["no"]


def test_rule_routes_to_rule_and_reasons_immediately():
    kb, rules = _fresh()
    ingest(kb, rules, "ada is a suspect")
    # a rule supplied mid-session must drive reasoning right away
    out = ingest(kb, rules, "?x is watched when ?x is a suspect")
    assert out.kind == "rule"
    assert out.added_rules
    ans = ingest(kb, rules, "is ada watched")
    assert ans.answer == ["yes"]


def test_gibberish_is_unrecognized():
    kb, rules = _fresh()
    out = ingest(kb, rules, "asdf qwer zzz")
    assert out.kind == "unrecognized"


def test_empty_is_unrecognized():
    kb, rules = _fresh()
    assert ingest(kb, rules, "   ").kind == "unrecognized"

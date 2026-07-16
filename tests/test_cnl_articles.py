"""
The `an` article (gap closed 2026-07-16): tokenize folds `an` -> `a` — mechanical and meaning-free
like its lowercasing, at the ONE chokepoint every path shares — so every `a?`-anchored form (facts,
questions, rule sugar incl. the `is not a` NAC, goals) handles `an` with no duplicated forms.
(The sibling `is not a X` mis-lowering was fixed the same day in `authoring.py`; this closes the
matched pre-existing `an` half.)
"""
import ugm as h
from ugm import AttrGraph
from ugm.intake import ingest


def test_an_facts_and_questions_are_the_a_forms():
    kb, rules = h.load_corpus("ada is an owl")
    assert h.ask_goal(kb, "is ada an owl", rules) == ["yes"]
    assert h.ask_goal(kb, "is ada a owl", rules) == ["yes"]     # same normalized token chain
    assert h.ask_goal(kb, "who is an owl", rules) == ["ada is_a owl"]


def test_an_in_rule_body_positive_and_nac():
    kb, rules = h.load_corpus("""\
ada is an owl
bo is a person

?p is hooty when ?p is an owl
?p is grounded when ?p is a person and ?p is not an owl
""")
    assert h.ask_goal(kb, "is ada hooty", rules) == ["yes"]     # positive `is an X` condition
    assert h.ask_goal(kb, "is bo grounded", rules) == ["yes"]   # `is not an X` lowers to the is_a NAC
    assert h.ask_goal(kb, "is ada grounded", rules) == ["no (assumed)"]   # ... and actually blocks (the owl)


def test_an_goal_routes_as_goal():
    out = ingest(AttrGraph(), [], "goal ada is an owl")
    assert out.kind == "goal"

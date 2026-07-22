"""Backward diagnosis — the `why S P O` surface on the unified `ingest` route (causation core §9.2).

The REASONING (provenance + `surface.explain`) already existed; this slice wires a why-question onto
`ingest`. The acceptance is the causation one: a fact derived through a `causes` link, asked `why`,
returns its causal antecedents. Plus the leaf cases (given / not-present), the copula forms, and the
route separation (a `why …` never steals an ordinary question, and vice versa).
"""
from ugm.cnl.authoring import load_corpus
from ugm.cnl.why_surface import parse_why
from ugm.intake import ingest


def _causal_kb():
    """lion has hunger; hunger causes aggression; and the entity-level causal propagation rule. So
    `lion has aggression` is DERIVED through the causal link — the thing diagnosis must recover."""
    kb, rules = load_corpus("")
    for u in ["has is a relation", "causes is a relation", "lion has hunger",
              "hunger causes aggression",
              "?x has ?effect when ?x has ?cause and ?cause causes ?effect"]:
        ingest(kb, rules, u)
    return kb, rules


# --- THE ACCEPTANCE: backward diagnosis over a causal chain ----------------------------------------

def test_why_recovers_the_causal_antecedents():
    kb, rules = _causal_kb()
    out = ingest(kb, rules, "why lion has aggression")
    assert out.kind == "why"
    text = "\n".join(out.explanation)
    # the derived fact, the rule that made it, and BOTH premises — including the causal link
    assert "lion has aggression" in text
    assert "hunger causes aggression" in text        # the CAUSE, recovered by diagnosis
    assert "lion has hunger" in text                 # the condition the cause acted on


def test_why_emits_the_events_before_the_outcome():
    kb, rules = _causal_kb()
    ev = []
    ingest(kb, rules, "why lion has aggression", on_event=ev.append)
    kinds = [e.kind for e in ev]
    assert kinds[0] == "why" and "explanation" in kinds   # the question, then its trace


# --- LEAVES: a given fact, and a fact that does not hold -------------------------------------------

def test_why_of_a_given_fact_is_a_leaf():
    kb, rules = load_corpus("")
    ingest(kb, rules, "bo is a suspect")
    out = ingest(kb, rules, "why is bo a suspect")
    assert out.kind == "why"
    assert out.explanation == ["bo is_a suspect  (given)"]


def test_why_of_an_underivable_fact_says_not_present():
    kb, rules = _causal_kb()
    out = ingest(kb, rules, "why lion has wings")
    assert out.kind == "why"
    assert "(not present)" in out.explanation[0]


# --- COPULA forms, and that a derivation shows its NAF leaps ----------------------------------------

def test_why_property_shows_the_rule_and_its_negative_assumption():
    """`why is S O` (a PROPERTY, predicate `is`) renders the deriving rule AND the absence it leaned
    on — diagnosis surfaces negative assumptions, not only positive premises."""
    kb, rules = load_corpus("?x is thief when ?x is a suspect and ?x is not cleared")
    ingest(kb, rules, "bo is a suspect")
    out = ingest(kb, rules, "why is bo thief")
    text = "\n".join(out.explanation)
    assert "bo is thief" in text and "bo is_a suspect" in text
    assert "assumed not: bo is cleared" in text      # the NAF leap the firing made


# --- ROUTE SEPARATION: the keyword gate is load-bearing --------------------------------------------

def test_why_does_not_steal_an_ordinary_question():
    kb, rules = load_corpus("")
    ingest(kb, rules, "bo is a suspect")
    out = ingest(kb, rules, "is bo a suspect")        # NOT a why — must still answer yes/no
    assert out.kind == "answer" and out.answer == ["yes"]


def test_an_ordinary_assertion_is_not_a_why():
    kb, rules = load_corpus("")
    out = ingest(kb, rules, "bo is a suspect")
    assert out.kind == "fact"


# --- parse_why unit: the three forms, and rejection ------------------------------------------------

def test_parse_why_recognizes_the_three_forms():
    assert parse_why("why lion has aggression") == ("lion", "has", "aggression")
    assert parse_why("why is ada thief") == ("ada", "is", "thief")
    assert parse_why("why is bo a suspect") == ("bo", "is_a", "suspect")


def test_parse_why_rejects_non_why():
    assert parse_why("lion has aggression") is None      # no `why`
    assert parse_why("why") is None                      # nothing to explain
    assert parse_why("why bo") is None                   # too short

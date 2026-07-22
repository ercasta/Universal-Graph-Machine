"""Counterfactual — `suppose A : P` / `what if A : P` over `suppose(commit=False)` (causation §9.2).

The ADDITIVE counterfactual: entertain `A` (not the case) and read whether `P` would hold, INKING
NOTHING. The reasoning is native; this pins the surface. (The subtractive counterfactual — "if A were
NOT so" — needs non-monotone retraction and is the out-of-core completion, not surfaced.)
"""
from ugm import derived_triples
from ugm.cnl.authoring import load_corpus
from ugm.cnl.suppose_surface import parse_suppose
from ugm.intake import ingest

_SCHEMA = "define schema ?r propagates ?base : ?x ?base ?e when ?x ?base ?c and ?c ?r ?e"


def _causal_kb():
    """Causal propagation declared, but lion does NOT actually have hunger — so `lion has aggression`
    is only reachable HYPOTHETICALLY."""
    kb, rules = load_corpus("")
    for u in ["has is a relation", "causes is a relation", "propagates is a relation",
              _SCHEMA, "causes propagates has", "hunger causes aggression"]:
        ingest(kb, rules, u)
    return kb, rules


def test_additive_counterfactual_holds():
    kb, rules = _causal_kb()
    assert ingest(kb, rules, "does lion have aggression").answer == ["no (assumed)"]   # not actually
    out = ingest(kb, rules, "suppose lion has hunger : lion has aggression")
    assert out.kind == "suppose" and out.answer == ["yes"]                             # but it WOULD


def test_what_if_is_the_same_force():
    kb, rules = _causal_kb()
    assert ingest(kb, rules, "what if lion has hunger : lion has aggression").answer == ["yes"]


def test_counterfactual_with_no_cause_does_not_hold():
    kb, rules = _causal_kb()
    out = ingest(kb, rules, "suppose lion has boredom : lion has aggression")
    assert out.kind == "suppose" and out.answer == ["no (assumed)"]


def test_counterfactual_inks_nothing():
    """The whole point of `commit=False`: entertaining a state must not change the KB's beliefs."""
    kb, rules = _causal_kb()
    ingest(kb, rules, "suppose lion has hunger : lion has aggression")
    ink = {(s, p, o) for (s, p, o) in derived_triples(kb)}
    assert ("lion", "has", "aggression") not in ink        # the hypothetical was not committed
    assert ("lion", "has", "hunger") not in ink            # nor the assumption
    assert [t for t in ink if t[0] in ("suppose", "what")] == []   # no bogus surface fact
    assert ingest(kb, rules, "does lion have aggression").answer == ["no (assumed)"]   # baseline intact


def test_parse_suppose_forms_and_rejection():
    assert parse_suppose("suppose lion has hunger : lion has aggression") == \
        (("lion", "has", "hunger"), ("lion", "has", "aggression"))
    assert parse_suppose("what if bo is a suspect : bo is thief") == \
        (("bo", "is_a", "suspect"), ("bo", "is", "thief"))
    assert parse_suppose("suppose lion has hunger") is None      # no `:` — no consequence to check
    assert parse_suppose("lion has hunger") is None              # not a suppose line

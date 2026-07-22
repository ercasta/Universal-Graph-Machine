"""Forward causation sugar — `causes` self-propagates via the EXISTING `define schema` meta-pattern,
with NO engine change (causation core §9.2 forward direction).

The finding this pins: the ergonomic "declaring `X causes Y` should propagate an effect without
hand-writing `?x has ?e when ?x has ?c and ?c causes ?e`" is DECLARED DATA, not an engine feature. A
TWO-parameter schema `?r propagates ?base` captures the causal-propagation MEANING once; then
`causes propagates has` (a plain fact) materialises the concrete rule — exactly as `ancestor is
transitive` materialises transitivity. Causation is thus NOT privileged: its propagation is declared
the same way any relation property is. This also exercises multi-parameter schemas (the shipped
`transitive` schema is single-parameter).
"""
from ugm.cnl.authoring import load_corpus
from ugm.intake import ingest

_SCHEMA = "define schema ?r propagates ?base : ?x ?base ?e when ?x ?base ?c and ?c ?r ?e"


def _kb(*extra):
    kb, rules = load_corpus("")
    for u in ["has is a relation", "causes is a relation", "propagates is a relation", _SCHEMA, *extra]:
        ingest(kb, rules, u)
    return kb, rules


def test_declaring_causes_propagates_makes_the_effect_derivable():
    kb, rules = _kb("causes propagates has", "lion has hunger", "hunger causes aggression")
    assert ingest(kb, rules, "does lion have aggression").answer == ["yes"]


def test_the_schema_materialised_a_rule_keyed_to_the_relation():
    kb, rules = _kb("causes propagates has")
    assert "causes" in [r.key for r in rules]        # the concrete propagation rule was written


def test_one_schema_serves_many_causal_relations():
    """The payoff of the schema over a hand-written rule: declare the MEANING once, reuse per relation.
    (`enables` is declared before use — the declare-before-use intake contract.)"""
    kb, rules = _kb("enables is a relation",
                    "causes propagates has", "enables propagates has",
                    "lion has hunger", "hunger causes aggression",
                    "lion has training", "training enables focus")
    assert ingest(kb, rules, "does lion have aggression").answer == ["yes"]   # via causes
    assert ingest(kb, rules, "does lion have focus").answer == ["yes"]        # via enables


def test_backward_diagnosis_sees_the_propagation():
    """`why` integrates: the schema-materialised firing records provenance like any rule."""
    kb, rules = _kb("causes propagates has", "lion has hunger", "hunger causes aggression")
    text = "\n".join(ingest(kb, rules, "why lion has aggression").explanation)
    assert "lion has aggression" in text and "hunger causes aggression" in text


def test_causes_does_not_propagate_without_the_schema():
    """Re-break: causation is NOT auto-propagating — the schema (declared meaning) is load-bearing.
    Without it, a `causes` fact is an inert relation and the effect stays underivable."""
    kb, rules = load_corpus("")
    for u in ["has is a relation", "causes is a relation",
              "lion has hunger", "hunger causes aggression"]:
        ingest(kb, rules, u)
    assert ingest(kb, rules, "does lion have aggression").answer == ["no (assumed)"]

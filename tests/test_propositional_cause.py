"""Propositional causation — the `that A causes that B` surface (facts-as-truth-bearers, §9.3).

A causal link between whole PROPOSITIONS: A holding DERIVES B, the link is a first-class fact, and links
CHAIN. Rides the reification bridge the predicate-variable-matching primitive enables
(`test_facts_as_truth_bearers.py` is the engine layer; this is the CNL face). The `that` nominalizer
distinguishes it from ENTITY-level `X causes Y` (native, the fact route) — so a bare `A causes B` is
never stolen.
"""
from ugm.cnl.authoring import load_corpus
from ugm.cnl.cause_surface import parse_cause
from ugm.intake import ingest


def _kb():
    return load_corpus("")


# --- the surface end to end -----------------------------------------------------------------------

def test_propositional_cause_derives_the_consequent():
    kb, rules = _kb()
    ingest(kb, rules, "door1 is open")
    out = ingest(kb, rules, "that door1 is open causes that cat is scared")
    assert out.kind == "cause"
    assert len(out.added_rules) == 3                       # the reify/MP/dereify bridge, installed once
    assert ingest(kb, rules, "is cat scared").answer == ["yes"]


def test_propositional_cause_negative_when_antecedent_absent():
    # RE-BREAK / soundness: no antecedent => the consequent is NOT derived (the link alone asserts nothing).
    kb, rules = _kb()
    ingest(kb, rules, "that door1 is open causes that cat is scared")
    assert ingest(kb, rules, "is cat scared").answer == ["no (assumed)"]


def test_propositional_cause_is_order_independent():
    # The link may be stated BEFORE its antecedent — rules live in the rule LIST (reified at query
    # time), so the consequent becomes derivable the moment the antecedent lands, no re-statement.
    kb, rules = _kb()
    ingest(kb, rules, "that door1 is open causes that cat is scared")
    assert ingest(kb, rules, "is cat scared").answer == ["no (assumed)"]
    ingest(kb, rules, "door1 is open")
    assert ingest(kb, rules, "is cat scared").answer == ["yes"]


def test_propositional_cause_chains():
    # A --> B --> C: the middle proposition is derived (dereified to a fact) and re-reified to drive C.
    kb, rules = _kb()
    ingest(kb, rules, "door1 is open")
    ingest(kb, rules, "that door1 is open causes that cat is scared")
    ingest(kb, rules, "that cat is scared causes that dog is alert")
    assert ingest(kb, rules, "is dog alert").answer == ["yes"]


def test_propositional_cause_over_a_kind_proposition():
    # A KIND proposition (`X is a Y`) folds to `is_a` on both the link and the query, so it agrees.
    kb, rules = _kb()
    ingest(kb, rules, "rex is a predator")
    ingest(kb, rules, "that rex is a predator causes that rex is dangerous")
    assert ingest(kb, rules, "is rex dangerous").answer == ["yes"]


def test_bridge_installed_once_across_statements():
    # The three bridge rules are shared: a SECOND propositional link adds no new rules.
    kb, rules = _kb()
    ingest(kb, rules, "door1 is open")
    first = ingest(kb, rules, "that door1 is open causes that cat is scared")
    second = ingest(kb, rules, "that cat is scared causes that dog is alert")
    assert len(first.added_rules) == 3
    assert len(second.added_rules) == 0                    # idempotent by key


# --- the boundary: `that` marks it; a bare `A causes B` is entity-level, not this surface ----------

def test_entity_level_causes_is_not_stolen():
    # RE-BREAK on the `that` nominalizer: a bare `X causes Y` (no `that`) must NOT route `cause` — it is
    # entity-level causation, left to the fact route (here recognized as a fact once `causes` is declared).
    kb, rules = _kb()
    ingest(kb, rules, "causes is a relation")
    assert ingest(kb, rules, "hunger causes aggression").kind == "fact"


def test_parse_cause_requires_the_that_nominalizer():
    assert parse_cause("that door1 is open causes that cat is scared") == (
        ("door1", "is", "open"), ("cat", "is", "scared"))
    assert parse_cause("hunger causes aggression") is None          # no `that`
    assert parse_cause("that door1 is open causes cat is scared") is None   # consequent not nominalized
    assert parse_cause("door1 is open causes that cat is scared") is None   # antecedent not nominalized

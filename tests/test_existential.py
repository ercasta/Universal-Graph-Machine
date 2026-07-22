"""Existential core (§9.2 #2) — a witness EXISTS without a name, resolved on demand. NATIVE through
intake; this pins it end-to-end (the binder spike proved it at the machine layer — this is the CNL face).

The mechanism is the LHS-keyed bound-literal skolem (`k?`) in a rule head (`skolem-minting-lhs-keyed`):
a rule mints an unnamed witness per match, `chain._resolve_skolems` re-finds it on demand, and it
PARTICIPATES downstream. No new engine or surface was needed — the existing rule + question forms carry
it. (Two things stay out: general verb inflection `open`/`opens` is the translator's open-class job, not
folded here; and a DIRECT existential ASSERTION `some key opens door1` is the out-of-core completion —
it has no LHS to key the witness on, so it collides with the no-unkeyed-skolem decision.)
"""
from ugm.cnl.authoring import load_corpus
from ugm.intake import ingest

_EXISTS = "k? opens ?d when ?d is a locked"      # every locked door has SOME (unnamed) opener


def _locked_kb(*extra):
    kb, rules = load_corpus("")
    for u in ["opens is a relation", "door1 is a locked", _EXISTS, *extra]:
        ingest(kb, rules, u)
    return kb, rules


def test_existential_yesno_finds_the_unnamed_witness():
    kb, rules = _locked_kb()
    assert ingest(kb, rules, "does anything opens door1").answer == ["yes"]


def test_enumeration_returns_the_minted_witness():
    kb, rules = _locked_kb()
    assert ingest(kb, rules, "who opens door1").answer == ["k opens door1"]


def test_copula_existential_subject():
    kb, rules = load_corpus("")
    for u in ["happy is a relation", "ada is happy"]:
        ingest(kb, rules, u)
    assert ingest(kb, rules, "is anyone happy").answer == ["yes"]      # ∃ over a copula property
    assert ingest(kb, rules, "is anybody happy").answer == ["yes"]     # synonym existential subject


def test_witness_composes_downstream():
    """E2 — the unnamed witness must PARTICIPATE in further reasoning, not just answer one query:
    `some opener exists, therefore the door is accessible`."""
    kb, rules = _locked_kb("?d is accessible when ?k opens ?d")
    assert ingest(kb, rules, "is door1 accessible").answer == ["yes"]


def test_no_rule_no_witness():
    """Control (the spike's negative): without the existential rule, no witness — the agent does not
    hallucinate an opener."""
    kb, rules = load_corpus("")
    for u in ["opens is a relation", "door1 is a locked"]:
        ingest(kb, rules, u)
    assert ingest(kb, rules, "does anything opens door1").answer == ["no (assumed)"]


def test_witness_only_where_the_rule_matches():
    """A door that is not locked gets no opener (the skolem is keyed to the match, not minted globally)."""
    kb, rules = _locked_kb("door2 is a plain", "?d is accessible when ?k opens ?d")
    assert ingest(kb, rules, "is door1 accessible").answer == ["yes"]        # locked -> witness
    assert ingest(kb, rules, "is door2 accessible").answer == ["no (assumed)"]  # plain -> none

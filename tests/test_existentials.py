"""
Indefinite existentials (∃) — a reasoning-expressiveness gap (handoff "reasoning-expressiveness").

An existential QUESTION (`is anyone happy` / `is anything a dog`) means ∃ — "does ANY witness
satisfy this" — so it must match a VARIABLE over all nodes: a NAMED individual (`bob is happy`) OR
an anonymous existential witness. The prior behaviour matched the literal word "someone" as a node
name, so it missed named individuals entirely (`bob is happy` but `is anyone happy` -> no). This is
the query-side dual of the labelled-null witness a `someone is …` FACT materializes.

An existential FACT (`someone is happy`) asserts ∃x.happy(x): the witness is a labelled null — a
fresh, DISTINCT, anonymous constant (not a variable — that would be ∀). In the un-canonicalized
Session each mention is already a distinct node, so existential facts reason soundly today (they
chain through rules and two witnesses never conflate). The sound-under-canonicalization
representation (an explicit null tag + blank identity, for the batch / RDF-blank-node path) is a
later slice; these tests pin the Session behaviour that works now.
"""
import ugm as h


# ---------------------------------------------------------------------------
# Existential QUESTIONS — ∃ over all witnesses (the bug fix)
# ---------------------------------------------------------------------------

def test_existential_question_sees_a_named_individual():
    # The core fix: `is anyone happy` is ∃?x.happy(?x), so a NAMED individual witnesses it.
    s = h.Session()
    s.submit("bob is happy")
    assert s.submit("is anyone happy").answer == ["yes"]
    assert s.submit("is someone happy").answer == ["yes"]


def test_existential_question_over_is_a():
    s = h.Session()
    s.submit("fido is a dog")
    assert s.submit("is anything a dog").answer == ["yes"]
    assert s.submit("is something a dog").answer == ["yes"]
    assert s.submit("is anything a cat").answer == ["no"]


def test_existential_question_is_negative_when_no_witness():
    s = h.Session()
    s.submit("bob is happy")
    assert s.submit("is anyone sad").answer == ["no"]
    assert h.Session().submit("is anyone happy").answer == ["no"]   # empty KB


def test_everyone_is_not_treated_as_existential():
    # `everyone`/`everything` are UNIVERSAL, not existential — one happy individual must NOT make
    # `is everyone happy` true. (∀-questions are out of scope; the guard is that ∃-handling does
    # not leak to the universal words.)
    s = h.Session()
    s.submit("bob is happy")
    assert s.submit("is everyone happy").answer != ["yes"]


def test_named_query_still_matches_by_name():
    # The ∃ path must not disturb ordinary named questions.
    s = h.Session()
    s.submit("bob is happy")
    assert s.submit("is bob happy").answer == ["yes"]
    assert s.submit("is carol happy").answer == ["no"]


# ---------------------------------------------------------------------------
# Existential FACTS — reasoning from ∃ premises, witnesses stay distinct
# ---------------------------------------------------------------------------

def test_reasoning_from_an_existential_fact():
    # `someone is happy` materializes a witness that participates in forward chaining, so a rule
    # derives a new existential, answerable by an existential question.
    s = h.Session()
    s.submit("if someone is happy then they are calm")
    s.submit("someone is happy")
    assert s.submit("is anyone calm").answer == ["yes"]
    # but nothing licenses a NAMED individual being calm
    assert s.submit("is bob calm").answer == ["no"]


def test_two_existential_facts_are_distinct_witnesses():
    # ∃x.solid(x) and ∃y.liquid(y) do NOT entail one thing that is both — the witnesses are
    # distinct, so there is no contradiction, and each is separately witnessed.
    s = h.Session()
    s.submit("something is a solid")
    s.submit("something is a liquid")
    assert s.contradictions() == []
    assert s.submit("is anything a solid").answer == ["yes"]
    assert s.submit("is anything a liquid").answer == ["yes"]


def test_existential_witness_carries_a_derived_property_not_a_name():
    # A rule over the existential witness derives a property on THAT witness (∃), never on an
    # unrelated named individual.
    s = h.Session()
    s.submit("if something is a solid then it is hard")
    s.submit("something is a solid")
    assert s.submit("is anything hard").answer == ["yes"]
    s.submit("ice is a liquid")                          # a different, named thing
    assert s.submit("is ice hard").answer == ["no"]

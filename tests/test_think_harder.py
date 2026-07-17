"""The reasoning BUDGET ("think harder" = more fuel, §14) is threaded end to end through the CNL
surface: `ingest`/`ask_goal` take `max_rounds`, forwarded to every `check`/`chain_sip` demand. A
question whose answer needs a chain deeper than the budget leaves the positive closure short of
fixpoint, and that fuel exhaustion surfaces as an HONEST `unknown` ("I did not finish looking"),
never a confident guess — the distinction an exhaustive forward model cannot make. Give the same
question a bigger budget and the same machine reaches a decided verdict.

This backs the book's "think harder" chapter + playground (deep detective line): clearing `ada`
means tracing an alibi that is a VOUCHING CHAIN — `vic` was `onstage` (an ironclad, anchored alibi)
and vouches for `uma`, who vouches for `rex`, who vouches for `sam`, who vouches for `ada`. So the
chain's DEPTH (data, a `vouches` relation — not a fixed rule count) drives how much budget clearing
its far end takes. `bo` is vouched for directly by an anchored witness (one hop); `cy` has nobody."""

from ugm.cnl.authoring import load_corpus
from ugm.intake import ingest


DEEP_DETECTIVE = """ada is a suspect
bo is a suspect
cy is a suspect

vouches is a relation

vic is onstage
vic vouches uma
uma vouches rex
rex vouches sam
sam vouches ada

tom is onstage
tom vouches bo

?p is cleared when ?p is onstage
?p is cleared when ?w vouches ?p and ?w is cleared
?p is thief when ?p is a suspect and ?p is not cleared"""


def _ask(question, max_rounds):
    kb, rules = load_corpus(DEEP_DETECTIVE)
    return list(ingest(kb, rules, question, max_rounds=max_rounds).answer)


def test_small_budget_is_honest_unknown_big_budget_decides():
    # ada's alibi is four vouch-hops deep: a small budget runs out before it can trace the chain back
    # to the anchor, so the honest verdict is UNKNOWN — NOT a confident "no" and NOT a wrong "yes".
    assert _ask("is ada thief", max_rounds=3) == ["unknown"]
    # think harder: the vouching chain completes, ada is cleared, so she is not the thief.
    assert _ask("is ada thief", max_rounds=1000) == ["no (assumed)"]


def test_budget_gates_a_positive_verdict_too():
    # cy has no one to vouch for them, but even DECIDING that takes enough budget to finish looking
    # for (and failing to find) a clearance. Under-budget -> unknown; think harder -> the decided yes.
    assert _ask("is cy thief", max_rounds=3) == ["unknown"]
    assert _ask("is cy thief", max_rounds=1000) == ["yes"]


def test_thinking_harder_takes_back_a_hasty_accusation():
    # The wh-question is the sharpest lesson: with too little budget the machine cannot finish tracing
    # ada's vouching chain, so it OVER-ACCUSES (lists her alongside the real thief). Given room to
    # think, it takes the accusation back and names only cy.
    hasty = _ask("who is thief", max_rounds=3)
    considered = _ask("who is thief", max_rounds=1000)
    assert "ada is thief" in hasty and "cy is thief" in hasty
    assert considered == ["cy is thief"]


def test_clearance_propagates_transitively_along_the_relation():
    # The declared `vouches` relation is a first-class fact on the demand path (recognized by the
    # batch loader's second pass, authoring._recognize), and clearance chains RECURSIVELY along it:
    # vic (onstage) -> uma -> rex -> sam -> ada, so the far end is genuinely cleared, not just assumed.
    assert _ask("does vic vouches uma", max_rounds=1000) == ["yes"]
    assert _ask("is ada cleared", max_rounds=1000) == ["yes"]


def test_default_budget_is_generous():
    # A caller who never mentions a budget gets the default 1000 — enough to finish this world, so
    # the "think harder" knob is strictly opt-in and changes nothing for ordinary use.
    kb, rules = load_corpus(DEEP_DETECTIVE)
    assert list(ingest(kb, rules, "is ada thief").answer) == ["no (assumed)"]

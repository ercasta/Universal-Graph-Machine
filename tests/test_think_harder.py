"""The reasoning BUDGET ("think harder" = more fuel, §14) is threaded end to end through the CNL
surface: `ingest`/`ask_goal` take `max_rounds`, forwarded to every `check`/`chain_sip` demand. A
question whose answer needs a chain deeper than the budget leaves the positive closure short of
fixpoint, and that fuel exhaustion surfaces as an HONEST `unknown` ("I did not finish looking"),
never a confident guess — the distinction an exhaustive forward model cannot make. Give the same
question a bigger budget and the same machine reaches a decided verdict.

This backs the book's "think harder" chapter + playground (deep detective line): clearing `ada`
takes a four-step exoneration chain (filmed -> timestamped -> corroborated -> alibied -> cleared),
so a small budget cannot finish it."""

from ugm.cnl.authoring import load_corpus
from ugm.intake import ingest


DEEP_DETECTIVE = """ada is a suspect
bo is a suspect
cy is a suspect

ada is filmed
bo is alibied

?p is cleared      when ?p is alibied
?p is alibied      when ?p is corroborated
?p is corroborated when ?p is timestamped
?p is timestamped  when ?p is filmed
?p is thief when ?p is a suspect and ?p is not cleared"""


def _ask(question, max_rounds):
    kb, rules = load_corpus(DEEP_DETECTIVE)
    return list(ingest(kb, rules, question, max_rounds=max_rounds).answer)


def test_small_budget_is_honest_unknown_big_budget_decides():
    # ada's alibi is four inferences deep: a small budget runs out before it can clear her, so the
    # honest verdict is UNKNOWN — NOT a confident "no" and NOT a wrong "yes".
    assert _ask("is ada thief", max_rounds=3) == ["unknown"]
    # think harder: the chain completes, ada is cleared, so she is not the thief.
    assert _ask("is ada thief", max_rounds=1000) == ["no (assumed)"]


def test_budget_gates_a_positive_verdict_too():
    # cy has no exonerating evidence, but even DECIDING that takes enough budget to finish looking
    # for (and failing to find) a clearance. Under-budget -> unknown; think harder -> the decided yes.
    assert _ask("is cy thief", max_rounds=3) == ["unknown"]
    assert _ask("is cy thief", max_rounds=1000) == ["yes"]


def test_thinking_harder_takes_back_a_hasty_accusation():
    # The wh-question is the sharpest lesson: with too little budget the machine cannot finish
    # clearing ada, so it OVER-ACCUSES (lists her alongside the real thief). Given room to think, it
    # takes the accusation back and names only cy.
    hasty = _ask("who is thief", max_rounds=3)
    considered = _ask("who is thief", max_rounds=1000)
    assert "ada is thief" in hasty and "cy is thief" in hasty
    assert considered == ["cy is thief"]


def test_default_budget_is_generous():
    # A caller who never mentions a budget gets the default 1000 — enough to finish this world, so
    # the "think harder" knob is strictly opt-in and changes nothing for ordinary use.
    kb, rules = load_corpus(DEEP_DETECTIVE)
    assert list(ingest(kb, rules, "is ada thief").answer) == ["no (assumed)"]

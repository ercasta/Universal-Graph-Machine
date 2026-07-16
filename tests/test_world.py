"""
The COMPOSITE surface (`ugm.cnl.world`): one CNL text mixing plain facts, rules, hedged facts,
`either…or`, and comparisons — loaded across every layer, asked through one router. The corpus is
the UNCERTAIN DETECTIVE (the book's fil rouge): a shaky alibi makes cy LIKELY the thief; the θ dial
flips the jump; the getaway glimpse is a ranked either…or that `guess` collapses; suspicion is the
comparative partial order. These pinned answers are the playground/book's genuine engine output.
"""
from ugm.cnl.world import load_world, ask_world
from ugm.policy import FirmwarePolicy

CORPUS = """
ada is a suspect
bo is a suspect
cy is a suspect

bo in library
ada is alibied
cy is unlikely alibied

culprit is either bo or more likely cy

suspicious is gradable
ada is more suspicious than bo
cy is more suspicious than ada
dan is more suspicious than bo

?someone is innocent when ?someone in library
?someone is cleared when ?someone is innocent
?someone is cleared when ?someone is alibied
?someone is thief when ?someone is a suspect and ?someone is not cleared
"""
BANDED = FirmwarePolicy(uncertainty="banded")


def _ask(q: str, policy=BANDED) -> list[str]:
    kb, rules = load_world(CORPUS)
    return ask_world(kb, rules, q, policy=policy)


def test_the_shaky_alibi_makes_cy_likely_the_thief():
    """The fil rouge, uncertain: cy's alibi is only 0.3-possible, so `not cleared` holds — but the
    conclusion honestly wears the doubt: thief at N(¬cleared)=0.7 → `likely`, never plain yes."""
    assert _ask("is cy thief") == ["likely"]
    assert _ask("is cy alibied") == ["unlikely"]
    assert _ask("is cy cleared") == ["unlikely"]           # the fork flows through the cleared rule


def test_hard_alibis_still_clear_crisply():
    assert _ask("is ada thief") == ["no"]                  # certain alibi → cleared blocks, hard
    assert _ask("is bo thief") == ["no"]                   # library → innocent → cleared


def test_theta_flips_the_jump():
    """Cautious θ=0.2: cleared is 0.3-possible ≥ θ, so the machine refuses to lean on the absence —
    no jump, plain `no` (assumed). The bias dial, live on the composite surface."""
    cautious = FirmwarePolicy(uncertainty="banded", theta=0.2)
    assert _ask("is cy thief", cautious) == ["no"]


def test_guess_collapses_the_getaway_glimpse():
    (line,) = _ask("guess culprit")
    assert line.startswith("culprit is cy — guessed as the most possible (likely)")
    assert "bo (unlikely)" in line and "assumption, not a derivation" in line
    assert _ask("guess nobody") == ["nothing to guess about nobody — no possibility is reachable"]


def test_suspicion_is_a_partial_order():
    assert _ask("is cy more suspicious than bo") == ["yes"]        # transitive via ada
    assert _ask("is bo more suspicious than cy") == ["no"]         # the reverse is entailed
    assert _ask("is cy more suspicious than dan") == ["unknown"]   # honest incomparability


def test_declared_hedge_composes_in_one_text():
    kb, rules = load_world("probable means 0.7\ncy is probable a thief")
    assert ask_world(kb, rules, "is cy a thief", policy=BANDED) == ["likely"]

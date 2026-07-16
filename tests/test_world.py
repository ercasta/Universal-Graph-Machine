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
    # a certain alibi blocks the thief rule OUTRIGHT (no fork involved) — but not-thief is still a
    # CWA verdict, not an entailed negative, and under the banded stance it WEARS that kind
    # (the capstone's surfacing half, 2026-07-16): `no (assumed)`, never a band word.
    assert _ask("is ada thief") == ["no (assumed)"]        # certain alibi → cleared blocks, hard
    assert _ask("is bo thief") == ["no (assumed)"]         # library → innocent → cleared


def test_theta_flips_the_jump():
    """Cautious θ=0.2: cleared is 0.3-possible ≥ θ, so the machine refuses to lean on the absence —
    no jump, `no (assumed)` with the kind out in the open. The bias dial, live on the composite
    surface (the uncertain-world chapter's "likely becomes no (assumed)")."""
    cautious = FirmwarePolicy(uncertainty="banded", theta=0.2)
    assert _ask("is cy thief", cautious) == ["no (assumed)"]


def test_guess_collapses_the_getaway_glimpse():
    (line,) = _ask("guess culprit")
    assert line.startswith("culprit is cy — guessed as the most possible (likely)")
    assert "bo (unlikely)" in line and "assumption, not a derivation" in line
    assert _ask("guess nobody") == ["nothing to guess about nobody — no possibility is reachable"]


def test_who_answers_wear_their_bands():
    """The who-branch is banded too: a fork-only witness wears its band word; nothing certain
    matches, so the list is exactly the honest suspects."""
    assert _ask("who is thief") == ["cy is thief (likely)"]
    assert _ask("who is a suspect") == ["ada is_a suspect", "bo is_a suspect", "cy is_a suspect"]


def test_existential_answers_wear_their_bands():
    """`is anyone …` under the banded stance: the verdict is the best witness's band —
    a fork-only witness answers with its band word, a certain one stays `yes`."""
    assert _ask("is anyone thief") == ["likely"]
    assert _ask("is anyone a suspect") == ["yes"]
    assert _ask("is anyone a wizard") == ["no (assumed)"]  # banded ∃ absence wears its kind too


def test_suspicion_is_a_partial_order():
    assert _ask("is cy more suspicious than bo") == ["yes"]        # transitive via ada
    assert _ask("is bo more suspicious than cy") == ["no"]         # the reverse is entailed
    assert _ask("is cy more suspicious than dan") == ["unknown"]   # honest incomparability


def test_banded_why_shows_bands_and_assumptions():
    """The explanation side of the fold: the proof tree wears each fact's band, AND names the
    absence the jump leaned on with its counter-evidence strength (decision 6 — the inspectable
    jump). And the why-closure runs under the SAME policy: no crisp ink leak."""
    import warnings
    from ugm.chain import _facts_matching

    kb, rules = load_world(CORPUS)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        lines = ask_world(kb, rules, "why cy is thief", policy=BANDED)
    assert lines[0].startswith("cy is thief (likely)")                 # the conclusion wears its band
    assert any("cy is_a suspect  (given)" in ln for ln in lines)       # the positive premise
    assert any("assumed not: cy is cleared" in ln and "only unlikely" in ln
               for ln in lines)                                        # what was ASSUMED, and how shaky
    assert _facts_matching(kb, "is", "cy", "thief") == []              # never inked (the leak is fixed)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cleared = ask_world(kb, rules, "why cy is cleared", policy=BANDED)
    assert cleared[0].startswith("cy is cleared (unlikely)")
    assert any("cy is alibied (unlikely)  (given)" in ln for ln in cleared)   # fork premise, banded


def test_comparative_why_renders_chain_bridge_and_gap():
    kb, rules = load_world(CORPUS)
    chain = ask_world(kb, rules, "why is cy more suspicious than bo", policy=BANDED)
    assert chain[0] == "cy is more suspicious than ada  (declared)"
    assert chain[1] == "ada is more suspicious than bo  (declared)"
    assert "more-than chains" in chain[2] and chain[2].endswith("yes")
    (gap,) = ask_world(kb, rules, "why is cy more suspicious than dan", policy=BANDED)
    assert gap.startswith("unknown — no chain of comparisons connects")
    rev = ask_world(kb, rules, "why is bo more suspicious than cy", policy=BANDED)
    assert "REVERSE" in rev[-1] and rev[-1].endswith("no")


def test_subgoal_records_carry_bands():
    """The demand-side trace (on_subgoal) reports HOW POSSIBLY a check resolved — the playground's
    'it asked itself: is cy cleared? → found something, but only unlikely' card."""
    kb, rules = load_world(CORPUS)
    records = []
    assert ask_world(kb, rules, "is cy thief", policy=BANDED,
                     on_subgoal=records.append) == ["likely"]
    resolved = {(r["subj"], r["pred"], r["obj"]): r for r in records if r["phase"] == "resolve"}
    cleared = resolved[("cy", "is", "cleared")]
    assert cleared["found"] is True and cleared["band"] == 0.3         # found — but only unlikely


def test_declared_hedge_composes_in_one_text():
    kb, rules = load_world("probable means 0.7\ncy is probable a thief")
    assert ask_world(kb, rules, "is cy a thief", policy=BANDED) == ["likely"]

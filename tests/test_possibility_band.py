"""
Possibilistic layer SLICE 1 (docs/possibilistic.md S7): banded forks, marker-mode read, θ-NAF,
band verdicts. The heart of the "living in an uncertain world" layer, standalone (chain.py
untouched). See also `test_possibilistic_naf.py` for the binary silent-until-assumed default.
"""
from ugm.attrgraph import AttrGraph
from ugm.possibility import (
    add_fork, facts_matching_banded, possibility, naf_holds, verdict, band_word, CERTAIN,
)


def _surgeon_graph() -> AttrGraph:
    """Ink: x is a surgeon. Two correlated forks: male∧tall (likely, 0.7) / female∧short (0.3)."""
    g = AttrGraph()
    x = g.add_node("x")
    g.add_relation(x, "is_a", g.add_node("surgeon"))
    add_fork(g, 0.7, [("x", "is", "male"), ("x", "is", "tall")])
    add_fork(g, 0.3, [("x", "is", "female"), ("x", "is", "short")])
    return g


def test_marker_mode_sees_all_forks_at_once():
    """The new capability: BOTH forks visible simultaneously with their bands — no stance taken.
    (Contrast test_possibilistic_naf, where a fork is visible only inside its own scope.)"""
    g = _surgeon_graph()
    assert possibility(g, "is", "x", "male") == 0.7
    assert possibility(g, "is", "x", "female") == 0.3
    assert possibility(g, "is", "x", "tall") == 0.7      # correlated with male (co-scoped)
    assert possibility(g, "is", "x", "short") == 0.3


def test_ink_is_certain():
    g = _surgeon_graph()
    assert possibility(g, "is_a", "x", "surgeon") == CERTAIN
    assert verdict(g, "is_a", "x", "surgeon") == "certain"


def test_theta_is_the_bias_dial():
    """`not female` (female band 0.3): whether it holds is decided purely by θ."""
    g = _surgeon_graph()
    assert naf_holds(g, "is", "x", "female", theta=0.5) is True    # cautious: 0.3 < 0.5 → not-female holds
    assert naf_holds(g, "is", "x", "female", theta=0.2) is False   # decisive: 0.3 ≥ 0.2 → female blocks it
    assert naf_holds(g, "is", "x", "male",   theta=0.5) is False    # male 0.7 ≥ 0.5 → blocks not-male


def test_theta_lives_on_policy():
    """θ is a SESSION dial on `FirmwarePolicy` (backlog item 1): the policy default (0.5) applies
    when no θ is passed, a policy carries a custom θ, and the range (0, 1] is enforced."""
    import pytest
    from ugm.policy import FirmwarePolicy, DEFAULT_POLICY

    g = _surgeon_graph()
    assert DEFAULT_POLICY.theta == 0.5
    assert naf_holds(g, "is", "x", "female") is True                # default θ=0.5: 0.3 < 0.5
    assert naf_holds(g, "is", "x", "male") is False                 # 0.7 ≥ 0.5
    decisive = FirmwarePolicy(theta=0.2)
    assert naf_holds(g, "is", "x", "female", policy=decisive) is False   # 0.3 ≥ 0.2 → female blocks
    assert naf_holds(g, "is", "x", "female", theta=0.5, policy=decisive) is True  # per-call override wins
    with pytest.raises(ValueError):
        FirmwarePolicy(theta=0.0)
    with pytest.raises(ValueError):
        FirmwarePolicy(theta=1.5)


def test_band_verdicts():
    g = _surgeon_graph()
    assert verdict(g, "is", "x", "male") == "likely"        # 0.7
    assert verdict(g, "is", "x", "female") == "unlikely"    # 0.3
    assert verdict(g, "is", "x", "dog") == "assumed-no"     # unreachable, closed
    assert verdict(g, "is", "x", "dog", closed=False) == "unknown"


def test_band_word_scale():
    assert band_word(1.0) == "certain"
    assert band_word(0.9) == "very likely"
    assert band_word(0.6) == "likely"
    assert band_word(0.3) == "unlikely"
    assert band_word(0.1) == "very unlikely"


def test_overlay_band_min_accumulates_multi_hop():
    """The ISA fold (S7.1/S7.2): the read runs through Machine.match, and a MULTI-HOP banded path
    min-accumulates the weakest-link band in the match score. x —is→ male (fork 0.6); male —is→
    dangerous (fork 0.5); the 2-hop path's score = min(0.6, 0.5) = 0.5."""
    from ugm.machine import Machine, SET, FOLLOW, TEST, OVERLAY_BAND
    from ugm.attrgraph import CONTROL_MARK, INERT_MARK, NAME
    from ugm.possibility import add_fork, all_fork_bands

    _FORK_BANDS = "<test-bands>"          # any register name — the op reads whatever it points at
    g = AttrGraph()
    add_fork(g, 0.6, [("x", "is", "male")])
    add_fork(g, 0.5, [("male", "is", "dangerous")])
    g.registers[_FORK_BANDS] = all_fork_bands(g)

    def guard(r):
        return [TEST(r, CONTROL_MARK, absent=True), TEST(r, INERT_MARK, absent=True)]

    prog = [SET("s", min(g.nodes_named("x"))), *guard("s"),
            FOLLOW("r1", "s", "out"), TEST("r1", "is"), OVERLAY_BAND("r1", CONTROL_MARK, _FORK_BANDS),
            FOLLOW("m", "r1", "out"), *guard("m"), TEST("m", NAME, cmp="=", value="male"),
            FOLLOW("r2", "m", "out"), TEST("r2", "is"), OVERLAY_BAND("r2", CONTROL_MARK, _FORK_BANDS),
            FOLLOW("d", "r2", "out"), *guard("d"), TEST("d", NAME, cmp="=", value="dangerous")]
    states = Machine().match(g, prog)
    assert states and min(st.score for st in states) == 0.5


def test_crisp_core_untouched_without_forks():
    """No forks ⇒ every fact reads CERTAIN and the marker reader agrees with a plain read."""
    g = AttrGraph()
    a = g.add_node("a")
    g.add_relation(a, "likes", g.add_node("b"))
    assert facts_matching_banded(g, "likes", "a", "b") == [("a", "b", CERTAIN, frozenset())]
    assert verdict(g, "likes", "a", "b") == "certain"
    assert verdict(g, "likes", "a", "c") == "assumed-no"


# ---------------------------------------------------------------------------
# SLICE 0 (docs/design/scope_generalization.md) — the negative READ is banded
# SYMMETRICALLY with the positive. A fork/pencil ¬L must not collapse to
# `assumed-no`, dropping its degree — the verified band∘negation leak (§9.1/9.3).
# ---------------------------------------------------------------------------

def test_banded_negation_wears_its_degree_not_assumed_no():
    """⭐ THE VERIFIED LEAK, FIXED. A fork `has_not(lion,mane)@0.75` reads possibility 0.75
    (representation composes) but `check` under a banded policy USED to answer `assumed-no`, dropping
    the band — where the positive twin answers `likely`. It must instead wear a banded NEGATIVE
    verdict, symmetric with the positive branch.

    RE-BREAK: delete the `if policy.banded:` negative-band block in `check.check` and this returns
    `assumed-no` again — the leak restored. The crisp path is unaffected (test below)."""
    from ugm.possibility import fork_fact, _entity
    from ugm.check import check
    from ugm.policy import FirmwarePolicy, BANDED
    banded = FirmwarePolicy(uncertainty=BANDED)

    g = AttrGraph()
    fork_fact(g, 0.75, _entity(g, "lion"), "has_not", _entity(g, "mane"))
    v = check(g, ("has", "lion", "mane"), policy=banded)
    assert v not in ("assumed-no", "entailed-no"), f"the band was dropped: {v!r}"
    assert v.endswith("not") and v != "not", f"a banded negative must wear its degree: {v!r}"

    # symmetric: the POSITIVE twin at the same band answers the positive band word, unchanged
    g2 = AttrGraph()
    fork_fact(g2, 0.75, _entity(g2, "lion"), "has", _entity(g2, "mane"))
    assert check(g2, ("has", "lion", "mane"), policy=banded) == band_word(0.75)


def test_crisp_negation_path_is_unchanged():
    """Slice 0 touches ONLY the banded branch: with no banded policy, an absent goal is still
    `assumed-no` and an ink hard-negative is still `entailed-no`."""
    from ugm.check import check, ENTAILED_NEG, ASSUMED_NO
    g = AttrGraph()
    assert check(g, ("has", "lion", "mane")) == ASSUMED_NO
    b = g.add_node("bo")
    g.add_relation(b, "is_not", g.add_node("cleared"))
    assert check(g, ("is", "bo", "cleared")) == ENTAILED_NEG

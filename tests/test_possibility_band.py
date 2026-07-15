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
    from ugm.possibility import add_fork, all_fork_bands, _FORK_BANDS

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

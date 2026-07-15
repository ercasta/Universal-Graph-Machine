"""
Possibilistic layer SLICE 1 — rules firing BANDED end-to-end (docs/possibilistic.md S7.3/S7.6):
a rule whose body reaches through a fork concludes at the fork's band; a NAC over an uncertain fact
is gated by θ (the bias dial); multi-variable bodies join. `ugm.possibility.apply_rule_banded`.
"""
import pytest

from ugm.attrgraph import AttrGraph
from ugm.possibility import apply_rule_banded, possibility, all_fork_bands, CERTAIN
from ugm.cnl.uncertainty import load_uncertain, ask


def _surgeon_ink_plus_female_fork() -> AttrGraph:
    g = AttrGraph()
    g.add_relation(g.add_node("x"), "is_a", g.add_node("surgeon"))     # ink: x is a surgeon
    load_uncertain(g, "x is unlikely female")                         # fork: x is female (0.3)
    return g


def test_theta_gates_the_biased_jump():
    """`?p is flagged when ?p is_a surgeon and not ?p is female`. female is 0.3-possible; θ is the hard
    gate AND (via graded negation) the surviving conclusion is only as strong as ¬female is necessary."""
    body, nac, head = [("?p", "is_a", "surgeon")], [("?p", "is", "female")], ("?p", "is", "flagged")

    decisive = _surgeon_ink_plus_female_fork()
    # θ=0.5: female 0.3 < 0.5 → fire, but honestly: band = min(1.0 body, N(¬female)=1−0.3=0.7) = 0.7.
    (triple, band), = apply_rule_banded(decisive, body, nac, head, theta=0.5)
    assert triple == ("x", "is", "flagged") and band == pytest.approx(0.7)
    assert ask(decisive, "is x flagged") == "likely"           # NOT "certain": the jump wears its doubt

    cautious = _surgeon_ink_plus_female_fork()
    # θ=0.2: female 0.3 ≥ 0.2 → NAC clears θ → blocked. No jump at all.
    assert apply_rule_banded(cautious, body, nac, head, theta=0.2) == []
    assert ask(cautious, "is x flagged") == "assumed-no"


def test_graded_negation_scales_with_counter_evidence():
    """The surviving conclusion's band tracks how UNLIKELY the negated evidence is (S7.3 necessity)."""
    body, nac, head = [("?p", "is_a", "surgeon")], [("?p", "is", "female")], ("?p", "is", "flagged")

    # very-unlikely female (0.15) → N(¬female)=0.85 → flagged "very likely"
    g1 = AttrGraph()
    g1.add_relation(g1.add_node("x"), "is_a", g1.add_node("surgeon"))
    load_uncertain(g1, "x is very unlikely female")
    (t1, b1), = apply_rule_banded(g1, body, nac, head, theta=0.5)
    assert t1 == ("x", "is", "flagged") and b1 == pytest.approx(0.85)
    assert ask(g1, "is x flagged") == "very likely"

    # likely female (0.6), θ high enough NOT to block (0.7) → N(¬female)=0.4 → flagged "unlikely"
    g2 = AttrGraph()
    g2.add_relation(g2.add_node("x"), "is_a", g2.add_node("surgeon"))
    load_uncertain(g2, "x is likely female")
    (t2, b2), = apply_rule_banded(g2, body, nac, head, theta=0.7)
    assert t2 == ("x", "is", "flagged") and b2 == pytest.approx(0.4)
    assert ask(g2, "is x flagged") == "unlikely"


def test_body_through_fork_bands_the_conclusion():
    """`?p is suspicious when ?p is male`, with `male` only reachable through a fork (0.6). The
    conclusion inherits the body's band — a banded head, end-to-end from CNL to verdict."""
    g = AttrGraph()
    load_uncertain(g, "x is likely male")                            # fork: x is male (0.6)
    emitted = apply_rule_banded(g, [("?p", "is", "male")], [], ("?p", "is", "suspicious"), theta=0.5)
    assert emitted == [(("x", "is", "suspicious"), 0.6)]
    assert possibility(g, "is", "x", "suspicious") == 0.6            # head is a fork at the body band
    assert ask(g, "is x suspicious") == "likely"


def test_certain_body_writes_ink_not_a_fork():
    """A fully-ink body derives an INK head (crisp behaviour preserved) — no spurious fork."""
    g = AttrGraph()
    g.add_relation(g.add_node("x"), "is_a", g.add_node("surgeon"))
    emitted = apply_rule_banded(g, [("?p", "is_a", "surgeon")], [], ("?p", "is", "doctor"), theta=0.5)
    assert emitted == [(("x", "is", "doctor"), CERTAIN)]
    assert ask(g, "is x doctor") == "certain"
    assert all_fork_bands(g) == {}                                   # head is ink: no fork minted


def test_multivariable_join_through_a_fork():
    """`?p is suspicious when ?p knows ?q and ?q is spy` — a TWO-variable body joined on ?q, with the
    spy fact behind a fork. Exercises wildcard banded reads + the join; the fork bands the conclusion."""
    g = AttrGraph()
    g.add_relation(g.add_node("alice"), "knows", g.add_node("bob"))  # ink: alice knows bob
    load_uncertain(g, "bob is likely spy")                           # fork: bob is spy (0.6)
    emitted = apply_rule_banded(
        g, [("?p", "knows", "?q"), ("?q", "is", "spy")], [], ("?p", "is", "suspicious"), theta=0.5)
    assert emitted == [(("alice", "is", "suspicious"), 0.6)]         # min(1.0 knows, 0.6 spy)
    assert ask(g, "is alice suspicious") == "likely"


def test_best_band_wins_across_derivations():
    """Two forks make `x is spy` derivable at 0.3 and 0.6; possibility = MAX-of-min = the better one."""
    g = AttrGraph()
    load_uncertain(g, "x is unlikely spy")      # fork 0.3
    load_uncertain(g, "x is likely spy")        # fork 0.6  (a second, more-possible fork)
    emitted = apply_rule_banded(g, [("?p", "is", "spy")], [], ("?p", "is", "watched"), theta=0.5)
    assert emitted == [(("x", "is", "watched"), 0.6)]               # the best derivation wins


def test_cross_exclusive_fork_derivation_is_impossible():
    """A body joining facts from TWO alternatives of the same `either…or` is an impossible environment
    (they can't both hold) and must be REJECTED — while a body using facts from ONE fork is allowed."""
    g = AttrGraph()
    load_uncertain(g, "x is either male and tall or female and short")   # one choice, two exclusive forks

    # male (fork A) ∧ short (fork B, same choice) → impossible → no derivation
    both = apply_rule_banded(g, [("?p", "is", "male"), ("?p", "is", "short")], [],
                             ("?p", "is", "contradictory"), theta=0.9)
    assert both == []
    assert ask(g, "is x contradictory") == "assumed-no"

    # male ∧ tall (SAME fork A) → possible → derived at the fork band (0.5)
    same = apply_rule_banded(g, [("?p", "is", "male"), ("?p", "is", "tall")], [],
                             ("?p", "is", "consistent"), theta=0.9)
    assert same == [(("x", "is", "consistent"), 0.5)]
    assert ask(g, "is x consistent") == "likely"


def test_head_environment_propagates_across_a_chain():
    """A derived fork carries the assumptions it rests on, so a SECOND rule that chains off it and also
    touches an incompatible fork sees the TRANSITIVE impossibility (the fuller ATMS, S7.2)."""
    g = AttrGraph()
    load_uncertain(g, "x is either male and tall or female and short")   # choice: fork A / fork B

    # rule 1: manly ← male  (derived from fork A; the head fork inherits fork A's assumption)
    assert apply_rule_banded(g, [("?p", "is", "male")], [], ("?p", "is", "manly"), theta=0.9) == \
        [(("x", "is", "manly"), 0.5)]

    # rule 2: puzzling ← manly ∧ short  (short is fork B — exclusive with A). Because `manly` carries
    # fork A transitively, the join env {A, B} is impossible → puzzling is NOT derived.
    assert apply_rule_banded(g, [("?p", "is", "manly"), ("?p", "is", "short")], [],
                             ("?p", "is", "puzzling"), theta=0.9) == []
    assert ask(g, "is x puzzling") == "assumed-no"

    # control: manly ∧ tall (both fork A) chains soundly → derived at 0.5
    assert apply_rule_banded(g, [("?p", "is", "manly"), ("?p", "is", "tall")], [],
                             ("?p", "is", "ok"), theta=0.9) == [(("x", "is", "ok"), 0.5)]

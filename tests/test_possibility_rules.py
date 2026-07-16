"""
Possibilistic reasoning INSIDE the demand-driven engine — the chain_sip FOLD (docs/possibilistic.md
S7.5 step 6, built 2026-07-16). Under `FirmwarePolicy(uncertainty="banded")` the ONE engine reasons
marker-mode: reads see every fork at its band, joins min-accumulate and track ATMS environments,
NAF is the θ-cut with graded necessity, and uncertain conclusions emit as DERIVED FORKS. The
standalone forward applier (`apply_rule_banded`/`run_banded`) was deleted with the fold — these
tests drive `chain_sip` / `check` / `ask_goal` directly.
"""
import pytest

from ugm.attrgraph import AttrGraph
from ugm.production_rule import Rule, Pat
from ugm.cnl.rule_graph import write_rule
from ugm.policy import FirmwarePolicy
from ugm.chain import chain_sip
from ugm.check import check, POSITIVE, ASSUMED_NO
from ugm.possibility import possibility, all_fork_bands
from ugm.cnl.uncertainty import load_uncertain

BANDED = FirmwarePolicy(uncertainty="banded")            # θ defaults to 0.5


def _bank(*rules: Rule) -> AttrGraph:
    rg = AttrGraph()
    for r in rules:
        write_rule(rg, r)
    return rg


def _surgeon() -> tuple[AttrGraph, AttrGraph]:
    """Ink: x is a surgeon. Fork: x is female (0.3). Rule: flagged ← surgeon ∧ not female."""
    g = AttrGraph()
    g.add_relation(g.add_node("x"), "is_a", g.add_node("surgeon"))
    load_uncertain(g, "x is unlikely female")
    rg = _bank(Rule(key="jump", lhs=[Pat("?p", "is_a", "surgeon")],
                    nac=[Pat("?p", "is", "female")], rhs=[Pat("?p", "is", "flagged")]))
    return g, rg


# --- θ (the bias dial) gates the NAF jump; graded negation makes the survivor honest -----------

def test_theta_gates_the_biased_jump():
    """female is 0.3-possible. Decisive θ=0.5: 0.3 < θ → the jump fires, but HONESTLY — the verdict
    is `likely` (N(¬female)=0.7), never `certain`. Cautious θ=0.2: 0.3 ≥ θ → blocked entirely."""
    g, rg = _surgeon()
    assert check(g, ("is", "x", "flagged"), rules=rg, policy=BANDED) == "likely"

    g2, rg2 = _surgeon()
    cautious = FirmwarePolicy(uncertainty="banded", theta=0.2)
    assert check(g2, ("is", "x", "flagged"), rules=rg2, policy=cautious) == ASSUMED_NO


def test_graded_negation_scales_with_counter_evidence():
    """The surviving conclusion's band tracks how UNLIKELY the negated evidence is (S7.3 necessity)."""
    # very-unlikely female (0.15) → N(¬female)=0.85 → flagged "very likely"
    g1 = AttrGraph()
    g1.add_relation(g1.add_node("x"), "is_a", g1.add_node("surgeon"))
    load_uncertain(g1, "x is very unlikely female")
    rg1 = _bank(Rule(key="jump", lhs=[Pat("?p", "is_a", "surgeon")],
                     nac=[Pat("?p", "is", "female")], rhs=[Pat("?p", "is", "flagged")]))
    assert check(g1, ("is", "x", "flagged"), rules=rg1, policy=BANDED) == "very likely"
    assert possibility(g1, "is", "x", "flagged") == pytest.approx(0.85)

    # likely female (0.6), θ=0.7 (high enough NOT to block) → N(¬female)=0.4 → flagged "unlikely"
    g2 = AttrGraph()
    g2.add_relation(g2.add_node("x"), "is_a", g2.add_node("surgeon"))
    load_uncertain(g2, "x is likely female")
    rg2 = _bank(Rule(key="jump", lhs=[Pat("?p", "is_a", "surgeon")],
                     nac=[Pat("?p", "is", "female")], rhs=[Pat("?p", "is", "flagged")]))
    bold = FirmwarePolicy(uncertainty="banded", theta=0.7)
    assert check(g2, ("is", "x", "flagged"), rules=rg2, policy=bold) == "unlikely"
    assert possibility(g2, "is", "x", "flagged") == pytest.approx(0.4)


# --- the band rides the derivation: body → head, crisp stays crisp, silent stays silent ---------

def test_body_through_fork_bands_the_conclusion():
    """`?p is suspicious when ?p is male`, `male` only reachable through a fork (0.6): the demand
    closure emits the head as a DERIVED FORK at the body band — end-to-end from CNL to verdict."""
    g = AttrGraph()
    load_uncertain(g, "x is likely male")
    rg = _bank(Rule(key="s", lhs=[Pat("?p", "is", "male")], rhs=[Pat("?p", "is", "suspicious")]))
    assert check(g, ("is", "x", "suspicious"), rules=rg, policy=BANDED) == "likely"
    assert possibility(g, "is", "x", "suspicious") == 0.6


def test_certain_body_writes_ink_not_a_fork():
    """A fully-ink body derives an INK head under the banded policy too (crisp behaviour preserved
    inside marker mode) — no spurious fork."""
    g = AttrGraph()
    g.add_relation(g.add_node("x"), "is_a", g.add_node("surgeon"))
    rg = _bank(Rule(key="doc", lhs=[Pat("?p", "is_a", "surgeon")], rhs=[Pat("?p", "is", "doctor")]))
    assert check(g, ("is", "x", "doctor"), rules=rg, policy=BANDED) == POSITIVE
    assert all_fork_bands(g) == {}                                   # head is ink: no fork minted


def test_silent_default_keeps_forks_invisible():
    """WITHOUT the banded stance the same query stays crisp: the fork is silent-until-assumed, so
    the rule finds no `male` and the goal is honestly assumed-no. The stance is the firmware's, not
    the graph's — the same graph answers differently under the two policies."""
    g = AttrGraph()
    load_uncertain(g, "x is likely male")
    rg = _bank(Rule(key="s", lhs=[Pat("?p", "is", "male")], rhs=[Pat("?p", "is", "suspicious")]))
    assert check(g, ("is", "x", "suspicious"), rules=rg) == ASSUMED_NO


def test_multivariable_join_through_a_fork():
    """`?p is suspicious when ?p knows ?q and ?q is spy` — a TWO-variable body joined on ?q, with the
    spy fact behind a fork; the fork bands the conclusion through the demand-driven join."""
    g = AttrGraph()
    g.add_relation(g.add_node("alice"), "knows", g.add_node("bob"))
    load_uncertain(g, "bob is likely spy")
    rg = _bank(Rule(key="s", lhs=[Pat("?p", "knows", "?q"), Pat("?q", "is", "spy")],
                    rhs=[Pat("?p", "is", "suspicious")]))
    assert check(g, ("is", "alice", "suspicious"), rules=rg, policy=BANDED) == "likely"
    assert possibility(g, "is", "alice", "suspicious") == 0.6        # min(1.0 knows, 0.6 spy)


def test_best_band_wins_across_derivations():
    """Two forks make `x is spy` reachable at 0.3 and 0.6; the derived conclusion's possibility is
    the MAX-of-min — the better derivation wins."""
    g = AttrGraph()
    load_uncertain(g, "x is unlikely spy")
    load_uncertain(g, "x is likely spy")
    rg = _bank(Rule(key="w", lhs=[Pat("?p", "is", "spy")], rhs=[Pat("?p", "is", "watched")]))
    chain_sip(g, ("is", "x", "watched"), rules=rg, policy=BANDED)
    assert possibility(g, "is", "x", "watched") == 0.6


def test_banded_emit_is_idempotent():
    """A re-run derives NOTHING new (a head is re-emitted only at a STRICTLY better band) — the
    graded check-before-derive that makes the demand rounds converge."""
    g = AttrGraph()
    load_uncertain(g, "x is likely male")
    rg = _bank(Rule(key="s", lhs=[Pat("?p", "is", "male")], rhs=[Pat("?p", "is", "suspicious")]))
    assert chain_sip(g, ("is", "x", "suspicious"), rules=rg, policy=BANDED) > 0
    assert chain_sip(g, ("is", "x", "suspicious"), rules=rg, policy=BANDED) == 0


# --- environments (ATMS): impossible worlds never fire, transitively --------------------------

def test_cross_exclusive_fork_derivation_is_impossible():
    """A body joining facts from TWO alternatives of the same `either…or` is an impossible
    environment and must be REJECTED — while a body using facts from ONE fork derives."""
    g = AttrGraph()
    load_uncertain(g, "x is either male and tall or female and short")
    rg = _bank(
        Rule(key="c", lhs=[Pat("?p", "is", "male"), Pat("?p", "is", "short")],
             rhs=[Pat("?p", "is", "contradictory")]),
        Rule(key="k", lhs=[Pat("?p", "is", "male"), Pat("?p", "is", "tall")],
             rhs=[Pat("?p", "is", "consistent")]))
    assert check(g, ("is", "x", "contradictory"), rules=rg, policy=BANDED) == ASSUMED_NO
    assert check(g, ("is", "x", "consistent"), rules=rg, policy=BANDED) == "likely"   # 0.5, one fork


def test_head_environment_propagates_across_a_chain():
    """A derived fork carries the assumptions it rests on, so a SECOND rule chaining off it that also
    touches an incompatible fork sees the TRANSITIVE impossibility — demand-driven, multi-step."""
    g = AttrGraph()
    load_uncertain(g, "x is either male and tall or female and short")
    rg = _bank(
        Rule(key="m", lhs=[Pat("?p", "is", "male")], rhs=[Pat("?p", "is", "manly")]),
        Rule(key="p", lhs=[Pat("?p", "is", "manly"), Pat("?p", "is", "short")],
             rhs=[Pat("?p", "is", "puzzling")]),
        Rule(key="o", lhs=[Pat("?p", "is", "manly"), Pat("?p", "is", "tall")],
             rhs=[Pat("?p", "is", "ok")]))
    assert check(g, ("is", "x", "puzzling"), rules=rg, policy=BANDED) == ASSUMED_NO
    assert check(g, ("is", "x", "ok"), rules=rg, policy=BANDED) == "likely"           # both fork A


def test_nac_is_env_aware():
    """A NAC only counts a P in worlds COMPATIBLE with the body's environment: `manly ← male ∧ not
    female` over `either male or female` FIRES (within the male-worlds `not female` genuinely
    holds), while the same shape over two INDEPENDENT compatible forks stays blocked at θ=0.5."""
    g = AttrGraph()
    load_uncertain(g, "x is either male or female")
    rg = _bank(Rule(key="m", lhs=[Pat("?p", "is", "male")],
                    nac=[Pat("?p", "is", "female")], rhs=[Pat("?p", "is", "manly")]))
    assert check(g, ("is", "x", "manly"), rules=rg, policy=BANDED) == "likely"        # 0.5 fork band

    g2 = AttrGraph()
    load_uncertain(g2, "x is likely male")                           # independent forks: both worlds
    load_uncertain(g2, "x is likely female")                         # can coexist in an environment
    rg2 = _bank(Rule(key="m", lhs=[Pat("?p", "is", "male")],
                     nac=[Pat("?p", "is", "female")], rhs=[Pat("?p", "is", "manly")]))
    assert check(g2, ("is", "x", "manly"), rules=rg2, policy=BANDED) == ASSUMED_NO


def test_disjoint_from_makes_independent_forks_exclusive():
    """Two INDEPENDENTLY-authored forks become mutually exclusive when their claims are DECLARED
    `disjoint_from` — world-exclusion for both the join and the NAC, inside the demand engine."""
    from ugm.lowering import load_fact_triples

    g = AttrGraph()
    load_fact_triples(g, [("male", "disjoint_from", "female")])
    load_uncertain(g, "x is likely male")
    load_uncertain(g, "x is likely female")
    rg = _bank(
        Rule(key="odd", lhs=[Pat("?p", "is", "male"), Pat("?p", "is", "female")],
             rhs=[Pat("?p", "is", "odd")]),
        Rule(key="m", lhs=[Pat("?p", "is", "male")],
             nac=[Pat("?p", "is", "female")], rhs=[Pat("?p", "is", "manly")]))
    assert check(g, ("is", "x", "odd"), rules=rg, policy=BANDED) == ASSUMED_NO
    assert check(g, ("is", "x", "manly"), rules=rg, policy=BANDED) == "likely"        # 0.6, ¬f certain


# --- the conversation surface: ask_goal answers with the band words ---------------------------

def test_ask_goal_answers_with_band_words():
    """The question forms are unchanged — only the ANSWER surface grows the band words (S7.4): the
    honest surgeon jump reads back `likely`, not `yes`."""
    from ugm.cnl.query import ask_goal

    g = AttrGraph()
    g.add_relation(g.add_node("x"), "is_a", g.add_node("surgeon"))
    load_uncertain(g, "x is unlikely female")
    rules = [Rule(key="jump", lhs=[Pat("?p", "is_a", "surgeon")],
                  nac=[Pat("?p", "is", "female")], rhs=[Pat("?p", "is", "flagged")])]
    assert ask_goal(g, "is x flagged", rules, policy=BANDED) == ["likely"]
    assert ask_goal(g, "is x a surgeon", rules, policy=BANDED) == ["yes"]             # ink stays yes

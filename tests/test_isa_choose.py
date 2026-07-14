"""
Phase 5.2 — CHOOSE firmware (`harneskills/isa/choose.py`): graded α-cut argmax over candidate options,
monotone (losers retained). The scenarios are the LOCKED design's build-step-4 tests
(`docs/attic/graded_means_selection_design.md`): the higher-fit means wins, ties offer both, a single
candidate is trivially satisfied, and the α-cut prunes a candidate BEFORE selection even runs.
Plus a randomized differential against an independent argmax reference.
"""
import random

from ugm import (
    AttrGraph, choose, set_candidate, winners_of, explain_choice,
)


def _goal_with(cands: dict[str, float]) -> tuple[AttrGraph, str, dict[str, str]]:
    """A graph with a `goal` node and one candidate option per (name -> fit) entry."""
    g = AttrGraph()
    goal = g.add_node("page_for_acme")
    ids: dict[str, str] = {}
    for name, fit in cands.items():
        opt = g.add_node(name)
        ids[name] = opt
        set_candidate(g, goal, opt, fit)
    return g, goal, ids


# --- the locked-design scenarios -----------------------------------------------------------------

def test_higher_fit_means_wins():
    # the design fixture: complex_page (fit 0.8) beats simple_page (fit 0.3)
    g, goal, ids = _goal_with({"complex_page": 0.8, "simple_page": 0.3})
    winners = choose(g, goal)
    assert [g.name(w) for w in winners] == ["complex_page"]
    assert [g.name(w) for w in winners_of(g, goal)] == ["complex_page"]
    # MONOTONE: the loser stays, marked `beaten` (auditable), NOT deleted
    assert g.has(ids["simple_page"])
    assert any("beaten: simple_page" in ln for ln in explain_choice(g, goal))


def test_equal_fit_is_a_tie_and_both_win():
    g, goal, _ = _goal_with({"page_a": 0.5, "page_b": 0.5})
    winners = choose(g, goal)
    assert sorted(g.name(w) for w in winners) == ["page_a", "page_b"]   # a genuine tie offers both


def test_single_candidate_is_trivially_satisfied():
    g, goal, _ = _goal_with({"only_page": 0.3})
    winners = choose(g, goal)
    assert [g.name(w) for w in winners] == ["only_page"]                # nothing beats it


def test_alpha_cut_prunes_a_candidate_before_selection():
    # a "somewhat demanding" client: complex_page's fit (0.5) is below the α-cut (0.6), so it is
    # PRUNED before selection — simple_page wins, and complex_page is NOT even marked `beaten`.
    g, goal, ids = _goal_with({"complex_page": 0.5, "simple_page": 0.3})
    winners = choose(g, goal, alpha=0.6)
    assert winners == []                                               # both below α-cut -> none eligible
    g2, goal2, ids2 = _goal_with({"complex_page": 0.7, "simple_page": 0.3})
    winners2 = choose(g2, goal2, alpha=0.6)
    assert [g2.name(w) for w in winners2] == ["complex_page"]          # only complex_page clears α
    # simple_page was α-pruned, so it is ineligible — NOT `beaten` (α-cut precedes the comparison)
    assert not any("beaten" in ln for ln in explain_choice(g2, goal2))


def test_choose_is_idempotent():
    g, goal, _ = _goal_with({"a": 0.8, "b": 0.3})
    choose(g, goal)
    choose(g, goal)                                                    # a second pick adds nothing
    assert len(winners_of(g, goal)) == 1


# --- randomized differential vs an independent argmax reference ----------------------------------

def test_choose_matches_argmax_reference():
    for seed in range(200):
        rng = random.Random(seed)
        n = rng.randint(1, 6)
        cands = {f"o{i}": round(rng.uniform(0, 1), 2) for i in range(n)}
        alpha = round(rng.uniform(0, 1), 2)
        g, goal, _ = _goal_with(cands)

        got = sorted(g.name(w) for w in choose(g, goal, alpha=alpha))
        # reference: eligible = fit >= alpha; winners = those achieving the max eligible fit
        elig = {name: fit for name, fit in cands.items() if fit >= alpha}
        want = sorted(name for name, fit in elig.items() if fit >= max(elig.values())) if elig else []
        assert got == want, f"seed={seed} alpha={alpha} cands={cands}: {got} != {want}"

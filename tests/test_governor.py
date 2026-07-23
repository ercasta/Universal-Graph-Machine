"""The reflexive GOVERNOR (corpus/governor.cnl) — heuristic termination as 100% DATA + RULES.

A repeatedly-failing goal raises a flare per failure (ugm/flare.py mints a distinct `?e flared ?g` event).
The governor BANK counts those by distinct-event self-join (`!=`, the only native comparison — no arithmetic,
no tool), escalates through a severity ladder, and abandons the goal at the DECLARED level. The threshold is
swappable DATA; nothing is Python. These tests drive the loop through the reactive gate (`fire`) — the system
governs ITSELF, no query — and prove the bound moves by data alone and that the escalation terminates.
"""
from __future__ import annotations

import pathlib
import warnings

from ugm.cnl.authoring import load_corpus
from ugm.lowering import assemble_facts
from ugm.machine import Machine
from ugm.flare import raise_flare
from ugm.reactive import fire
from ugm.chain import _facts_matching

warnings.simplefilter("ignore")
_CORPUS = pathlib.Path(__file__).resolve().parent.parent / "corpus"
_GOV = (_CORPUS / "governor.cnl").read_text(encoding="utf-8")
_RECOVERY = (_CORPUS / "recovery.cnl").read_text(encoding="utf-8")
GOAL = ("solve", "x", "y")


def _abandoned(kb) -> bool:
    return bool(_facts_matching(kb, "abandoned", None, "yes"))


def _reached(kb, level) -> bool:
    return bool(_facts_matching(kb, "reached", None, level))


def _fail_once(kb, rules):
    """One failed attempt: the flare bridge records a distinct event, then the committed-act gate fires —
    the governor escalates the ladder and re-checks the verdict, with NO query."""
    raise_flare(kb, GOAL)
    fire(kb, rules)


def test_governor_escalates_and_abandons_at_the_declared_level():
    kb, rules = load_corpus(_GOV)                       # abandon_at severe (3 distinct failures)
    _fail_once(kb, rules)
    assert _reached(kb, "mild") and not _abandoned(kb)  # 1 failure — mild, keep going
    _fail_once(kb, rules)
    assert _reached(kb, "moderate") and not _abandoned(kb)   # 2 — moderate, still under the threshold
    _fail_once(kb, rules)
    assert _reached(kb, "severe") and _abandoned(kb)    # 3 — severe reaches abandon_at -> abandoned


def test_the_threshold_moves_by_data_alone():
    # SAME bank + code; only the `abandon_at` FACT changes (severe -> moderate). The goal is now abandoned
    # after TWO failures instead of three — the policy moved with no code change.
    kb, rules = load_corpus(_GOV)
    Machine().run(kb, assemble_facts([("config", "abandon_at", "moderate")]))   # lower the threshold, as DATA
    _fail_once(kb, rules)
    assert not _abandoned(kb)                           # 1 failure — under moderate
    _fail_once(kb, rules)
    assert _abandoned(kb)                               # 2 — reaches the lowered threshold


def test_the_escalation_terminates():
    # Heuristic termination: a goal that would flare forever is bounded. After abandonment the verdict is
    # STABLE (monotone) and further failures neither un-abandon it nor grow the verdict — the loop settles.
    kb, rules = load_corpus(_GOV)
    for _ in range(8):                                  # keep failing well past the threshold
        _fail_once(kb, rules)
    assert _abandoned(kb)
    assert _facts_matching(kb, "abandoned", None, "yes")   # a single stable verdict, not a storm


# ---------------------------------------------------------------------------
# COMPOSITION — the governor + authoritativeness combine on the ONE substrate, with NOTHING but shared facts:
# when the governor abandons a goal, the AUTHORITY-selected advisor's recovery is applied. Two banks, no glue.
# ---------------------------------------------------------------------------

def _composed(authority):
    """Load BOTH banks into one kb and supply the authority order as DATA (the only thing that varies)."""
    kb, rules = load_corpus(_GOV + "\n" + _RECOVERY)
    Machine().run(kb, assemble_facts([authority]))
    return kb, rules


def _recovery(kb) -> set:
    return {o if isinstance(o, str) else kb.name(o.node_id)
            for _s, o in _facts_matching(kb, "recovery", None, None)}


def test_recovery_is_chosen_by_authority_composing_with_the_governor():
    kb, rules = _composed(("ops", "more_important_than", "policy"))
    for _ in range(3):                                  # fail to abandonment
        _fail_once(kb, rules)
    assert _abandoned(kb)                               # the governor abandoned the goal, and...
    assert _recovery(kb) == {"escalate"}               # ...ops (more important) advises escalate -> chosen


def test_swapping_the_authority_fact_swaps_the_recovery():
    # SAME two banks, SAME failures — only the `more_important_than` FACT is reversed. The chosen recovery
    # flips from escalate (ops) to giveup (policy): two mechanisms composing, steered by one datum.
    kb, rules = _composed(("policy", "more_important_than", "ops"))
    for _ in range(3):
        _fail_once(kb, rules)
    assert _recovery(kb) == {"giveup"}

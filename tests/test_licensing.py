"""Learning arc S6 — failure invokes learning, and elimination judges what it proposed.

Two halves, deliberately separate (the design keeps PROPOSING and JUDGING apart):

  * `learner.DISCREPANCY_TRIGGER` — a planner discrepancy marks the failed step as a learning
    subject. One rule; failure was already a fact (corpus/procedure.cnl).
  * `licensing.refute` — a candidate that over-predicts about a FULLY-DESCRIBED entity is refuted,
    with the offending prediction as the reason.

The measured headline, pinned below: generalizing from a failure ALONE is useless (12 candidates,
all junk — one failure has no contrast). Contrast with a succeeded step refutes a third. The
remainder is genuinely undecidable on that evidence and needs a discriminating question, which is
why this module deliberately does not rank or promote.
"""
import pytest

import ugm as h
from ugm import AttrGraph, Pat, Rule
from ugm.learner import DISCREPANCY_TRIGGER, OBSERVE, learn, observe
from ugm.licensing import (COMPLETE, complete_entities, mark_complete, overpredictions,
                           refute, render_refutation)
from ugm.lowering import run_bank


def _world():
    """One step that FAILED (done, but its effect never materialized) and one that SUCCEEDED."""
    g = AttrGraph()
    hot, yes = g.add_node("hot_coffee"), g.add_node("yes")
    warm = g.add_node("warm")
    g.add_relation(warm, "add", hot)
    g.add_relation(warm, "done", yes)
    g.add_relation(warm, "discrepancy", hot)
    g.add_relation(warm, "excluded", yes)
    micro = g.add_node("microwave")
    g.add_relation(micro, "add", hot)
    g.add_relation(micro, "done", yes)
    g.add_relation(micro, "achieved", hot)
    return g


# ---------------------------------------------------------------------------
# The trigger
# ---------------------------------------------------------------------------

def test_a_discrepancy_marks_the_failed_step_as_a_learning_subject():
    g = _world()
    run_bank(g, [DISCREPANCY_TRIGGER], max_rounds=10)
    warm = g.nodes_named("warm")[0]
    assert any(g.predicate(r) == OBSERVE for r, _o in g.relations_from(warm))


def test_a_succeeded_step_is_not_marked():
    """The trigger must not fire on a step that worked — no discrepancy, no learning."""
    g = _world()
    run_bank(g, [DISCREPANCY_TRIGGER], max_rounds=10)
    micro = g.nodes_named("microwave")[0]
    assert not any(g.predicate(r) == OBSERVE for r, _o in g.relations_from(micro))


# ---------------------------------------------------------------------------
# Completeness — the qualifier that makes elimination possible at all
# ---------------------------------------------------------------------------

def test_mark_and_read_complete_entities():
    g = _world()
    mark_complete(g, "microwave")
    assert complete_entities(g) == {"microwave"}


def test_nothing_is_refutable_without_a_complete_entity():
    """The honest outcome when there is no discriminator — NOT a silent pass."""
    g = _world()
    observe(g, "warm")
    candidates = learn(g)
    survivors, refuted = refute(candidates, g, complete=set())
    assert refuted == []
    assert len(survivors) == len(candidates)


# ---------------------------------------------------------------------------
# Elimination
# ---------------------------------------------------------------------------

def test_contrast_with_a_succeeded_step_refutes_over_general_candidates():
    """The S6 headline: a failure alone proposes junk; contrast eliminates part of it."""
    g = _world()
    observe(g, "warm")
    candidates = learn(g)
    assert len(candidates) > 1, "the failed step alone should propose many candidates"

    mark_complete(g, "microwave")
    survivors, refuted = refute(candidates, g)
    assert refuted, "contrast with a succeeded step must eliminate something"
    assert len(survivors) < len(candidates)

    # the specific catastrophe must die: "anything done has a discrepancy"
    bad = [(r, why) for r, why in refuted
           if [p.tokens() for p in r.lhs] == [("?x", "done", "yes")]
           and [p.tokens() for p in r.rhs] == [("?x", "discrepancy", "hot_coffee")]]
    assert bad, [[p.tokens() for p in r.lhs] for r in survivors]


def test_refutation_names_the_offending_prediction():
    g = _world()
    rule = Rule(key="bad", lhs=[Pat("?x", "done", "yes")],
                rhs=[Pat("?x", "discrepancy", "hot_coffee")])
    why = overpredictions(rule, set(h.derived_triples(g)), {"microwave"})
    assert ("microwave", "discrepancy", "hot_coffee") in why
    assert "microwave" in render_refutation(rule, why)


def test_a_rule_predicting_only_about_novel_entities_is_not_refuted():
    """Deriving a NEW fact about an entity we do not claim to know fully is the POINT of a rule,
    not a refutation — this is what the completeness qualifier buys."""
    g = _world()
    kettle = g.add_node("kettle")
    g.add_relation(kettle, "is_a", g.add_node("appliance"))   # a property microwave lacks,
    mark_complete(g, "microwave")                             # so the rule fires ONLY on kettle
    rule = Rule(key="pred", lhs=[Pat("?x", "is_a", "appliance")],
                rhs=[Pat("?x", "boils", "yes")])
    survivors, refuted = refute([rule], g)
    assert survivors == [rule] and refuted == []


def test_refute_never_mutates_the_observed_graph():
    g = _world()
    mark_complete(g, "microwave")
    before = set(h.derived_triples(g))
    refute([Rule(key="x", lhs=[Pat("?x", "done", "yes")],
                 rhs=[Pat("?x", "discrepancy", "hot_coffee")])], g)
    assert set(h.derived_triples(g)) == before

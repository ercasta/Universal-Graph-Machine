"""Learning arc S5 — a rule that writes a rule (`ugm/learner.py`).

Promoted from bench/spike_rule_learning.py (L1/L3/L4) and bench/spike_predicate_reification.py.
The contract these pin, each of which cost a spike to establish:

  * the learned rule's predicates come from the GRAPH, not from the learner's source
  * learning is INVOKED (only `observe`d entities), never ambient
  * scaffolding predicates can never leak into a learned rule
  * learner and learned rule coexist in one bank without a runaway
  * a learned rule is marked as such, so a conclusion on it can be rendered provisional
"""
import pytest

import ugm as h
from ugm import AttrGraph, Pat, Rule, derived_triples
from ugm.learner import (OBSERVE, PAT_TOK, PAT_VAR, PRED_NAME, LEARNER_BANK,
                         accept, learn, observe, prepare, pred_tok_tool)
from ugm.learned import learned_support
from ugm.lowering import run_bank


def _birds():
    """Two birds observed flying, plus a bird nothing is said about."""
    g = AttrGraph()
    bird, yes = g.add_node("bird"), g.add_node("yes")     # intern once: add_node always mints
    for who in ("tweety", "polly"):
        w = g.add_node(who)
        g.add_relation(w, "is_a", bird)
        g.add_relation(w, "flies", yes)
    g.add_relation(g.add_node("robin"), "is_a", bird)
    return g


def _shapes(rules):
    return {(tuple(sorted(p.tokens() for p in r.lhs)),
             tuple(sorted(p.tokens() for p in r.rhs))) for r in rules}


# ---------------------------------------------------------------------------

def test_learns_the_generalization_from_observations():
    g = _birds()
    observe(g, "tweety", "polly")
    rules = learn(g)
    assert (("?x", "is_a", "bird"),) in {s[0] for s in _shapes(rules)}
    fwd = [r for r in rules
           if [p.tokens() for p in r.lhs] == [("?x", "is_a", "bird")]
           and [p.tokens() for p in r.rhs] == [("?x", "flies", "yes")]]
    assert len(fwd) == 1, [(r.key, [p.tokens() for p in r.rhs]) for r in rules]


def test_learned_rules_are_marked_learned():
    g = _birds()
    observe(g, "tweety", "polly")
    assert all(r.learned for r in learn(g))


def test_predicates_come_from_the_graph_not_the_source():
    """The decisive generality test: a vocabulary that appears NOWHERE in ugm/learner.py."""
    g = AttrGraph()
    acme, yes = g.add_node("acme"), g.add_node("yes")
    for who in ("dana", "wren"):
        w = g.add_node(who)
        g.add_relation(w, "works_at", acme)
        g.add_relation(w, "commutes", yes)
    observe(g, "dana", "wren")
    rules = learn(g)
    preds = {p.p for r in rules for p in list(r.lhs) + list(r.rhs)}
    assert preds == {"works_at", "commutes"}, preds


def test_only_observed_entities_are_generalized_from():
    """Learning is invoked, not ambient: an unobserved entity contributes nothing."""
    g = AttrGraph()
    for who, cat in (("tweety", "bird"), ("rex", "dog")):
        w = g.add_node(who)
        g.add_relation(w, "is_a", g.add_node(cat))
        g.add_relation(w, "moves", g.add_node("yes"))
    observe(g, "tweety")                      # rex is NOT observed
    objs = {p.o for r in learn(g) for p in list(r.lhs) + list(r.rhs)}
    assert "dog" not in objs, objs


def test_scaffolding_never_leaks_into_a_learned_rule():
    """`observe`/`pat_var`/`pat_tok` are relations on the same entities the learner reads, so they
    would be generalized over if the calculator reified them. It must not."""
    g = _birds()
    observe(g, "tweety", "polly")
    preds = {p.p for r in learn(g) for p in list(r.lhs) + list(r.rhs)}
    assert preds.isdisjoint({OBSERVE, PAT_TOK, PAT_VAR, PRED_NAME}), preds


def test_learned_rule_fires_on_unseen_data():
    """The point of the whole arc: derive something never observed."""
    g = _birds()
    observe(g, "tweety", "polly")
    accepted, _refused = accept([], learn(g))

    fresh = AttrGraph()
    fresh.add_relation(fresh.add_node("robin"), "is_a", fresh.add_node("bird"))
    run_bank(fresh, accepted, max_rounds=20)
    assert ("robin", "flies", "yes") in derived_triples(fresh)


def test_two_observations_of_one_generalization_dedupe():
    """Keying by what a rule GENERALIZES makes the second observation idempotent, not a duplicate."""
    g = _birds()
    observe(g, "tweety", "polly")             # both support the same generalization
    rules = learn(g)
    assert len(rules) == len(_shapes(rules))


def test_learner_and_learned_coexist_in_one_bank():
    """No stratification cycle and no runaway when the learned rules join the learner's bank."""
    g = _birds()
    observe(g, "tweety", "polly")
    learned = learn(g)
    bank = LEARNER_BANK + learned
    h.stratify(bank)                                       # must not raise
    fires = [run_bank(_observed_birds(), bank, max_rounds=mr,
                      tools={"pred_tok": pred_tok_tool}) for mr in (10, 40)]
    assert fires[0] == fires[1], f"runaway: firings grew with rounds {fires}"


def _observed_birds():
    g = _birds()
    observe(g, "tweety", "polly")
    prepare(g)
    return g


# ---------------------------------------------------------------------------
# The stratification gate (§8) — refused AT LEARN TIME, not later
# ---------------------------------------------------------------------------

# A pair whose negations are MUTUAL is what `stratify` actually refuses. (Checked while writing:
# a one-way negative dependency stratifies fine — `p -> q` plus `seed AND not q -> p` is accepted
# and ordered — and a rule NACing its own head predicate is also accepted, being the fire-once
# idiom. Only a genuine cycle is unstratifiable, so that is what the gate must catch.)
_EXISTING = [Rule(key="m1", lhs=[Pat("?x", "seed", "yes")],
                  nac=[Pat("?x", "b", "yes")], rhs=[Pat("?x", "a", "yes")])]
_CYCLIC = Rule(key="bad", lhs=[Pat("?x", "seed", "yes")],
               nac=[Pat("?x", "a", "yes")], rhs=[Pat("?x", "b", "yes")])


def test_accept_refuses_a_rule_that_would_create_a_negative_cycle():
    accepted, refused = accept(_EXISTING, [_CYCLIC])
    assert [r.key for r in refused] == ["bad"]
    assert accepted == []


def test_accept_refuses_only_the_bad_candidate():
    """One bad rule must not refuse the whole batch."""
    good = Rule(key="good", lhs=[Pat("?x", "m", "yes")], rhs=[Pat("?x", "n", "yes")])
    accepted, refused = accept(_EXISTING, [_CYCLIC, good])
    assert [r.key for r in accepted] == ["good"]
    assert [r.key for r in refused] == ["bad"]


# ---------------------------------------------------------------------------
# End to end with the provisionality surface (§6.1a)
# ---------------------------------------------------------------------------

def test_a_conclusion_from_a_learned_rule_is_reported_provisional():
    g = _birds()
    observe(g, "tweety", "polly")
    accepted, _ = accept([], learn(g))

    fresh = AttrGraph()
    fresh.add_relation(fresh.add_node("robin"), "is_a", fresh.add_node("bird"))
    rg = AttrGraph()
    for r in accepted:
        h.write_rule(rg, r)
    used = learned_support(fresh, ("flies", "robin", "yes"),
                           learned={r.key for r in accepted}, rules=rg)
    assert used, "a conclusion reached by a learned rule must report it"

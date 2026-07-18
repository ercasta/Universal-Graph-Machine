"""Learning arc §6.1a — a conclusion standing on a LEARNED rule can say so (query-time hedging).

The design first proposed "born hedged" via `Rule.probability`. That field is DEAD (nothing in the
package reads it; setting it changes no graph), and `CONF` is written by `add_relation` and read by
nothing — so the whole numeric confidence channel is inert. Provisionality is therefore answered
from PROVENANCE at query time: walk the support of the answer and report the learned rules in it.

`check`'s verdict vocabulary is deliberately UNCHANGED (no fifth verdict); provisionality is
explanation, asked separately when it matters.
"""
import pytest

import ugm as h
from ugm import AttrGraph, Pat, Rule, check, POSITIVE
from ugm.learned import learned_support, learned_keys, render_provisional


def _birds():
    g = AttrGraph()
    bird, yes = g.add_node("bird"), g.add_node("yes")
    g.add_relation(g.add_node("robin"), "is_a", bird)
    return g, bird, yes


AUTHORED = Rule(key="authored.fly",
                lhs=[Pat("?x", "is_a", "bird")], rhs=[Pat("?x", "flies", "yes")])
LEARNED = Rule(key="learned.fly", learned=True,
               lhs=[Pat("?x", "is_a", "bird")], rhs=[Pat("?x", "flies", "yes")])


def _rule_graph(*rules):
    rg = AttrGraph()
    for r in rules:
        h.write_rule(rg, r)
    return rg


def test_learned_keys_selects_only_learned_rules():
    assert learned_keys([AUTHORED, LEARNED]) == {"learned.fly"}
    assert learned_keys([AUTHORED]) == set()


def test_conclusion_on_a_learned_rule_reports_it():
    g, _b, _y = _birds()
    used = learned_support(g, ("flies", "robin", "yes"),
                           learned={"learned.fly"}, rules=_rule_graph(LEARNED))
    assert used == ["learned.fly"]


def test_conclusion_on_an_authored_rule_reports_nothing():
    """The same conclusion, reached without a learned rule, is NOT provisional."""
    g, _b, _y = _birds()
    used = learned_support(g, ("flies", "robin", "yes"),
                           learned={"learned.fly"}, rules=_rule_graph(AUTHORED))
    assert used == []


def test_verdict_vocabulary_is_unchanged():
    """`check` still returns a plain POSITIVE — provisionality never becomes a fifth verdict."""
    g, _b, _y = _birds()
    assert check(g, ("flies", "robin", "yes"), rules=_rule_graph(LEARNED)) == POSITIVE


def test_transitive_support_is_followed_not_just_the_last_step():
    """A conclusion is provisional if ANY step used a learned rule, not only the final one.

    `learned.mid` derives an intermediate fact; an AUTHORED rule then derives the goal from it.
    Reading only the goal's own justification would miss the learned step."""
    g = AttrGraph()
    g.add_relation(g.add_node("robin"), "is_a", g.add_node("bird"))
    learned_mid = Rule(key="learned.mid", learned=True,
                       lhs=[Pat("?x", "is_a", "bird")], rhs=[Pat("?x", "has_wings", "yes")])
    authored_top = Rule(key="authored.top",
                        lhs=[Pat("?x", "has_wings", "yes")], rhs=[Pat("?x", "flies", "yes")])
    used = learned_support(g, ("flies", "robin", "yes"), learned={"learned.mid"},
                           rules=_rule_graph(learned_mid, authored_top))
    assert used == ["learned.mid"], "transitive support must be followed"


def test_no_learned_rules_short_circuits():
    g, _b, _y = _birds()
    assert learned_support(g, ("flies", "robin", "yes"), learned=set(),
                           rules=_rule_graph(AUTHORED)) == []


def test_render_wears_the_kind():
    assert render_provisional(POSITIVE, []) == POSITIVE
    out = render_provisional(POSITIVE, ["learned.fly"])
    assert out.startswith(POSITIVE) and "learned.fly" in out and "assuming" in out


# ---------------------------------------------------------------------------
# The flat schema carries the mark, so a LEARNER can stamp its own output
# ---------------------------------------------------------------------------

def test_rl_learned_round_trips_through_the_flat_schema():
    from ugm.cnl.authoring import expand_rules
    g = AttrGraph()
    R = g.add_node("<lrule>", control=True)
    cond_h = g.add_node("<chead>", control=True)
    g.add_relation(R, "rl_head", cond_h, control=True)
    g.add_relation(cond_h, "k_subj", g.add_node("?x", control=True), control=True)
    g.add_relation(cond_h, "k_pred", g.add_node("flies", control=True), control=True)
    g.add_relation(cond_h, "k_obj", g.add_node("yes", control=True), control=True)
    g.add_relation(R, "rl_key", g.add_node("k1", control=True), control=True)
    g.add_relation(R, "rl_learned", g.add_node("yes", control=True), control=True)

    rules = expand_rules(g)
    assert len(rules) == 1
    assert rules[0].learned is True


def test_absent_rl_learned_means_authored():
    from ugm.cnl.authoring import expand_rules
    g = AttrGraph()
    R = g.add_node("<lrule>", control=True)
    cond_h = g.add_node("<chead>", control=True)
    g.add_relation(R, "rl_head", cond_h, control=True)
    g.add_relation(cond_h, "k_subj", g.add_node("?x", control=True), control=True)
    g.add_relation(cond_h, "k_pred", g.add_node("flies", control=True), control=True)
    g.add_relation(cond_h, "k_obj", g.add_node("yes", control=True), control=True)
    g.add_relation(R, "rl_key", g.add_node("k2", control=True), control=True)

    assert expand_rules(g)[0].learned is False

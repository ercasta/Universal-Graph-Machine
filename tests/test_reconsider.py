"""
RECONSIDER — demand-driven revision of assumed-absence conclusions
(docs/design/reconsider_design.md). The gap: a NAF conclusion MATERIALIZED by an earlier ask
survived later knowledge contradicting the absence it leaned on. The fix: intake MARKS the
changed grain (registers), and the next COMMITTED ask re-checks affected `<assumed>` records,
withdrawing broken conclusions through the existing cascade + copy-on-delete.
"""
import warnings

import ugm as h
from ugm import retraction as ret
from ugm.cnl.authoring import load_corpus
from ugm.intake import ingest
from ugm.reconsider import DIRTY_REG, BROKEN

THIEF_RULE = "?x is thief when ?x is a suspect and ?x is not cleared"


def _ingest(kb, rules, utt):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")             # the pre-existing 'is'-token residue warning
        return ingest(kb, rules, utt)


def test_new_rule_flips_materialized_naf_conclusion():
    # The §1 transcript: ask (materializes thief via NAF), THEN learn alibi + clearing rule.
    kb, rules = load_corpus(THIEF_RULE)
    _ingest(kb, rules, "ada is a suspect")
    assert _ingest(kb, rules, "is ada thief").answer == ["yes"]      # NAF: nothing clears ada
    _ingest(kb, rules, "ada is alibied")
    _ingest(kb, rules, "?x is cleared when ?x is alibied")
    assert _ingest(kb, rules, "is ada thief").answer == ["no"]       # RECONSIDERED
    assert _ingest(kb, rules, "is ada cleared").answer == ["yes"]    # the broken absence, now ink

    # The withdrawal is archived, not shredded: a history record stamped with the broken assumption.
    hist = kb.nodes_named(ret.HISTORY)
    assert hist, "the withdrawn conclusion should be archived under <history>"
    recs = [o for tn in kb.out(hist[0]) if kb.has_key(tn, ret.RECORDS) for o in kb.out(tn)]
    assert recs
    assert any(kb.has_key(rel, BROKEN) for r in recs for rel in kb.out(r)), \
        "some history record should carry the broken_assumption stamp"


def test_new_fact_alone_breaks_through_rule_dependency():
    # The clearing rule is ALREADY in the bank; only a FACT arrives. The dirty grain
    # ("is", "alibied") must reach the assumption ("is", ·, "cleared") transitively.
    kb, rules = load_corpus(THIEF_RULE + "\n?x is cleared when ?x is alibied")
    _ingest(kb, rules, "bo is a suspect")
    assert _ingest(kb, rules, "is bo thief").answer == ["yes"]
    _ingest(kb, rules, "bo is alibied")
    assert _ingest(kb, rules, "is bo thief").answer == ["no"]


def test_direct_fact_breaks_assumption():
    # The asserted fact IS the assumed-absent tuple itself (no rule hop).
    kb, rules = load_corpus(THIEF_RULE)
    _ingest(kb, rules, "cy is a suspect")
    assert _ingest(kb, rules, "is cy thief").answer == ["yes"]
    _ingest(kb, rules, "cy is cleared")
    assert _ingest(kb, rules, "is cy thief").answer == ["no"]


def test_multi_support_conclusion_is_rederived():
    # `watched` holds via a NAF rule AND via an independent positive rule. Breaking the NAF
    # support cascades `watched` away — but the triggering question re-derives it through the
    # surviving positive path (over-forget-and-re-derive).
    kb, rules = load_corpus(
        "?x is watched when ?x is a suspect and ?x is not cleared\n"
        "?x is watched when ?x is flagged")
    _ingest(kb, rules, "ada is a suspect")
    _ingest(kb, rules, "ada is flagged")
    assert _ingest(kb, rules, "is ada watched").answer == ["yes"]
    _ingest(kb, rules, "ada is cleared")                              # breaks the NAF support only
    assert _ingest(kb, rules, "is ada watched").answer == ["yes"]     # re-derived via `flagged`


def test_cascade_reaches_dependents_of_the_stale_conclusion():
    # `alerted` stands ON the NAF conclusion `thief`; when `thief` is withdrawn, so is `alerted`.
    kb, rules = load_corpus(THIEF_RULE + "\n?x is alerted when ?x is thief")
    _ingest(kb, rules, "cy is a suspect")
    assert _ingest(kb, rules, "is cy alerted").answer == ["yes"]      # thief -> alerted, both inked
    _ingest(kb, rules, "cy is cleared")
    assert _ingest(kb, rules, "is cy alerted").answer == ["no"]
    assert _ingest(kb, rules, "is cy thief").answer == ["no"]


def test_disable_withdraws_materialized_conclusions():
    kb, rules = load_corpus("")
    _ingest(kb, rules, "bo is a suspect")
    _ingest(kb, rules, "?x is watched when ?x is a suspect")
    assert _ingest(kb, rules, "is bo watched").answer == ["yes"]
    _ingest(kb, rules, "forget that rule")
    assert _ingest(kb, rules, "is bo watched").answer == ["no"]       # support gone by fiat


def test_unrelated_fact_is_a_noop_and_clears_the_mark():
    kb, rules = load_corpus(THIEF_RULE)
    _ingest(kb, rules, "ada is a suspect")
    assert _ingest(kb, rules, "is ada thief").answer == ["yes"]
    _ingest(kb, rules, "bo in library")                               # unrelated grain
    assert kb.registers.get(DIRTY_REG), "the fact should have marked its grain"
    assert _ingest(kb, rules, "is ada thief").answer == ["yes"]       # verdict unchanged
    assert not kb.registers.get(DIRTY_REG), "the sweep should clear the dirty set"


def test_forward_naf_firing_journals_assumed_records():
    # The FORWARD record half (design §6): a run_bank/run_rules NAF firing under provenance=True
    # journals the absences it leaned on, exactly as the demand path does (Π = 0, wildcards named).
    from ugm import provenance as prov
    from ugm.cnl.authoring import run_rules
    R = h.Rule(key="fwd.thief",
               lhs=[h.Pat("?x", "is_a", "suspect")],
               nac=[h.Pat("?x", "is", "cleared")],
               rhs=[h.Pat("?x", "is", "thief")])
    g = h.Graph()
    g.add_relation(g.add_node("ada"), "is_a", g.add_node("suspect"))
    run_rules(g, [R], provenance=True)
    js = [n for n in g.nodes() if prov.is_justification(g.name(n))]
    assert js, "the forward firing should mint a justification"
    assert prov.assumptions_of(g, js[0]) == [("is", "ada", "cleared", 0.0)]

    # provenance=False journals nothing (recognition banks stay lean).
    g2 = h.Graph()
    g2.add_relation(g2.add_node("bo"), "is_a", g2.add_node("suspect"))
    run_rules(g2, [R], provenance=False)
    assert not [n for n in g2.nodes() if prov.is_justification(g2.name(n))]


def test_forward_derived_conclusion_is_reconsidered():
    # End-to-end over the forward path: derive via run_rules (provenance ON), then new knowledge
    # + the sweep withdraws the stale conclusion — J-uniform, no demand-path involvement.
    from ugm.cnl.authoring import run_rules
    from ugm.lowering import load_fact_triples
    from ugm.reconsider import mark_dirty, reconsider

    R = h.Rule(key="fwd.thief",
               lhs=[h.Pat("?x", "is_a", "suspect")],
               nac=[h.Pat("?x", "is", "cleared")],
               rhs=[h.Pat("?x", "is", "thief")])
    g = h.Graph()
    load_fact_triples(g, [("ada", "is_a", "suspect")])
    run_rules(g, [R], provenance=True)

    def thief_visible():
        return any(g.has_key(r, "is") and any(g.name(o) == "thief" for o in g.out(r))
                   for s in g.nodes_named("ada") for r in g.out(s))
    assert thief_visible()

    load_fact_triples(g, [("ada", "is", "cleared")])     # the assumed absence becomes fact
    mark_dirty(g, [("is", "cleared")])                    # (what intake's fact route would write)
    assert reconsider(g, [R]) == 1
    assert not thief_visible(), "the forward-derived NAF conclusion should be withdrawn"


def test_read_only_ask_does_not_trigger_or_mutate():
    from ugm.cnl.query import ask_goal
    kb, rules = load_corpus(THIEF_RULE)
    _ingest(kb, rules, "ada is a suspect")
    assert _ingest(kb, rules, "is ada thief").answer == ["yes"]
    _ingest(kb, rules, "ada is cleared")                              # marks the grain
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        stale = ask_goal(kb, "is ada thief", rules, commit=False)
    assert stale == ["yes"], "a read-only ask answers over the graph as-is (documented)"
    assert kb.registers.get(DIRTY_REG), "commit=False must not consume the mark"
    assert _ingest(kb, rules, "is ada thief").answer == ["no"]        # the committed ask settles it

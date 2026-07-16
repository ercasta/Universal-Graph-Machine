"""
The LINKED SUBGOAL CHAIN (axis_b_control_registers.md §5.4) — the graph-side follow-on to the
demand-trace register reversal: the subgoal chain is the NEGATIVE'S EXPLANATION, so under
`provenance=True` it is materialized as `<subgoal>` nodes in the FACT graph with parent -[raised]->
child pointers, at EVERY negation depth. `subgoal_decomposition` walks one step; `surface.explain`
renders an assumed-no's decomposition as indented 'looked for:' lines.
"""
import ugm as h
from ugm import AttrGraph, chain_sip, check, subgoal_decomposition
from ugm.chain import SUBGOAL
from ugm.cnl import surface
from ugm.cnl.authoring import load_corpus


DETECTIVE = """\
ada is a suspect
cy is a suspect
ada is alibied

?someone is cleared when ?someone is alibied
?someone is thief when ?someone is a suspect and ?someone is not cleared
"""


def _world():
    kb, rules = load_corpus(DETECTIVE)
    rg = AttrGraph()
    for r in rules:
        h.write_rule(rg, r)
    return kb, rg


def test_chain_links_the_nac_frame_goal_and_its_sub_demands():
    kb, rg = _world()
    chain_sip(kb, ("is", "cy", "thief"), rules=rg, provenance=True)
    # the top goal raised its body's sub-demands (in-frame links)...
    kids = subgoal_decomposition(kb, "is", "cy", "thief")
    assert ("is_a", "cy", "suspect") in kids
    # ...and the NAC spawned a child frame whose goal links under the top goal
    assert ("is", "cy", "cleared") in kids
    # the NEGATIVE'S DECOMPOSITION: deciding `cy is cleared` searched the cleared-rule's body
    assert ("is", "cy", "alibied") in subgoal_decomposition(kb, "is", "cy", "cleared")


def test_chain_is_recorded_only_under_provenance():
    kb, rg = _world()
    chain_sip(kb, ("is", "cy", "thief"), rules=rg)         # no provenance -> no chain, no new nodes
    assert kb.nodes_named(SUBGOAL) == []
    assert subgoal_decomposition(kb, "is", "cy", "thief") == []


def test_chain_lives_in_the_fact_graph_not_the_discarded_rule_graph():
    kb, rg = _world()
    chain_sip(kb, ("is", "cy", "thief"), rules=rg, provenance=True)
    assert kb.nodes_named(SUBGOAL) != []                   # explanation home: where `why` reads
    assert rg.nodes_named(SUBGOAL) == []                   # the flat <demand> magic set stays rule-side


def test_explain_walks_the_negatives_decomposition():
    # `assumed not:` records journal on the banded FORK path (decision 6: the θ-gated leap is the
    # inspectable jump) — that is where the decomposition hangs; the chain itself is recorded either
    # way (the crisp tests above). Hedge cy's alibi so the surviving NAC carries Π>0.
    from ugm.cnl.world import load_world
    kb, rules = load_world(DETECTIVE + "cy is unlikely alibied\n")
    rg = AttrGraph()
    for r in rules:
        h.write_rule(rg, r)
    chain_sip(kb, ("is", "cy", "thief"), rules=rg, provenance=True,
              policy=h.FirmwarePolicy(uncertainty="banded"))
    lines = surface.explain(kb, [], [], "cy", "is", "thief")
    text = "\n".join(lines)
    assert "assumed not: cy is cleared" in text
    # the decomposition renders UNDER the assumption, deeper-indented
    assumed_at = next(i for i, l in enumerate(lines) if "assumed not" in l)
    looked = [l for l in lines[assumed_at + 1:] if "looked for:" in l]
    assert any("cy is alibied" in l for l in looked)       # what deciding the absence searched
    indent = len(lines[assumed_at]) - len(lines[assumed_at].lstrip())
    assert all(len(l) - len(l.lstrip()) > indent for l in looked)


def test_chain_records_deeper_negation_nests():
    # thief <- not cleared; cleared <- not suspicious-of-forgery: a depth-2 NAF nest — every frame links.
    kb, rules = load_corpus("""\
cy is a suspect

?someone is cleared when ?someone is a suspect and ?someone is not doubted
?someone is doubted when ?someone is a suspect and ?someone is not vouched
""")
    rg = AttrGraph()
    for r in rules:
        h.write_rule(rg, r)
    chain_sip(kb, ("is", "cy", "cleared"), rules=rg, provenance=True)
    assert ("is", "cy", "doubted") in subgoal_decomposition(kb, "is", "cy", "cleared")
    assert ("is", "cy", "vouched") in subgoal_decomposition(kb, "is", "cy", "doubted")


def test_crisp_why_shows_the_leap_and_its_decomposition():
    # the record half of the hard-vs-assumed capstone (2026-07-16): a CERTAIN firing that leaned on
    # an absence journals it too (Π = 0), so a CRISP why shows the leap and the chain hangs off it
    kb, rg = _world()
    chain_sip(kb, ("is", "cy", "thief"), rules=rg, provenance=True)
    lines = surface.explain(kb, [], [], "cy", "is", "thief")
    text = "\n".join(lines)
    assert "assumed not: cy is cleared  (no evidence for it was found)" in text
    assert any("looked for: cy is alibied" in l for l in lines)


def test_chain_interns_across_repeated_queries():
    # a second provenance query over the SAME live KB reuses the chain (node + edge dedupe is
    # graph-backed, not per-call). The first run's derivations may legitimately surface NEW demand
    # tuples on the re-run, so the invariant is NOT a frozen node count — it is: one node per tuple
    # (never two `<subgoal>` nodes carrying the same goal), and a stable decomposition.
    kb, rg = _world()
    chain_sip(kb, ("is", "cy", "thief"), rules=rg, provenance=True)
    kids_after_first = subgoal_decomposition(kb, "is", "cy", "cleared")
    chain_sip(kb, ("is", "cy", "thief"), rules=rg, provenance=True)

    def tup(n):
        return tuple(None if (a := kb.get_attr(n, k)) is None else str(a.value)
                     for k in ("for", "subj", "obj"))
    tuples = [tup(n) for n in kb.nodes_named(SUBGOAL)]
    assert len(tuples) == len(set(tuples))                 # interned: one chain node per goal tuple
    # the decomposition is MONOTONE, never duplicated: run 1's derived facts may let the machinery
    # rules raise a genuinely new probe on run 2 (seed-dependent), but nothing recorded is ever lost
    assert set(kids_after_first) <= set(subgoal_decomposition(kb, "is", "cy", "cleared"))


def test_check_verdict_unchanged_by_the_chain():
    # the chain is a RECORD, never control: verdicts are identical with and without it
    kb1, rg1 = _world()
    kb2, rg2 = _world()
    v1 = h.collapse(check(kb1, ("is", "cy", "thief"), rules=rg1, provenance=True))
    v2 = h.collapse(check(kb2, ("is", "cy", "thief"), rules=rg2))
    assert v1 == v2 == "yes"
    assert h.collapse(check(kb1, ("is", "ada", "thief"), rules=rg1, provenance=True)) == "no"

"""
Retraction AS COPY-ON-DELETE — the cascade decides the set (rules over now-matchable provenance),
then the driver ARCHIVES each pre-image into the in-graph history and RETIRES the live relation
(docs/attic/mechanism_policy_separation.md, Probe 1; retraction.retract). Supersedes the earlier
interpose-hiding driver: a retracted fact is really DELETED (its live 2-hop is gone), not spliced
through a `<retracted>` marker. Its pre-image + provenance stay in the graph as inert, meta-visible
DATA so reflection survives, and `resurrect` re-materializes it.

Aggressive/single-support form (stratified): correct for a derivation chain; a multi-support fact
would be over-retracted and is recovered by re-derivation (deferred — not exercised here).
"""
import ugm as h
from ugm import provenance as prov, retraction as ret
from ugm.attrgraph import AttrGraph
from ugm.cnl.authoring import run_rules
from ugm.machine import Machine, RETIRE, DROP_CTRL, State, ControlEdgeError
from ugm.lowering import _lower_bank_rule, lower_rule

R1 = h.Rule(key="r0.r1", lhs=[h.Pat("?a", "r0", "?b")], rhs=[h.Pat("?a", "r1", "?b")])
R2 = h.Rule(key="r1.r2", lhs=[h.Pat("?a", "r1", "?b")], rhs=[h.Pat("?a", "r2", "?b")])


def _vis(g, s, p, o):
    """Does the raw 2-hop path  s -[p]-> o  exist? (s/p/o are all ground names here — copy-on-delete
    removes the live relation node, so a retracted fact reads as not-visible directly, no matcher
    needed.)"""
    return any(g.has_key(r, p) and o_id in g.out(r)
               for s_id in g.nodes_named(s) for r in g.out(s_id) for o_id in g.nodes_named(o))


def _n_justifications(g):
    return len([n for n in g.nodes() if prov.is_justification(g.name(n))])


def _build():
    """Two independent chains r0 -> r1 -> r2, over bases `x r0 y` and `p r0 q` (axiomatized)."""
    g = h.Graph()
    r0_xy = g.add_relation(g.add_node("x"), "r0", g.add_node("y"))
    g.add_relation(g.add_node("p"), "r0", g.add_node("q"))
    prov.axiomatize(g, ["r0"])            # base facts get an <axiom> proof (never cascade candidates)
    run_rules(g, [R1, R2])                # derive r1, r2 for both, WITH provenance
    return g, r0_xy


def test_cascade_deletes_the_whole_chain_below_a_retracted_base():
    g, r0_xy = _build()
    assert _vis(g, "x", "r1", "y") and _vis(g, "x", "r2", "y")

    ret.retract(g, r0_xy)                 # decide (cascade) + record history + retire

    # x's chain is deleted (the retracted base + everything derived from it)
    assert not _vis(g, "x", "r0", "y")
    assert not _vis(g, "x", "r1", "y")
    assert not _vis(g, "x", "r2", "y")
    # the independent p chain is untouched
    assert _vis(g, "p", "r0", "q") and _vis(g, "p", "r1", "q") and _vis(g, "p", "r2", "q")


def test_cascade_mints_no_new_justifications():
    # the DECIDE cascade is meta (provenance=False) and RECORD redirects (not mints) provenance:
    # retraction adds no <j:> nodes.
    g, r0_xy = _build()
    before = _n_justifications(g)
    ret.retract(g, r0_xy)
    assert _n_justifications(g) == before


def test_retire_really_deletes_the_relation_node():
    # copy-on-delete: the derived relation node is GONE (real deletion), NOT rerouted-but-present.
    # This is the anti-zombie criterion — the retracted fact's live relation genuinely stops existing.
    g, r0_xy = _build()
    r1_xy = next(r for r in g.out(g.nodes_named("x")[0]) if g.predicate(r) == "r1")
    assert g.has(r1_xy)
    ret.retract(g, r0_xy)
    assert not g.has(r1_xy)               # the live relation node is deleted, not hidden


def test_no_retract_no_effect():
    # the cascade is inert without a seed: RETRACT_RULES over an untouched graph change nothing.
    g, _ = _build()
    vis_before = [_vis(g, "x", p, o) for p, o in (("r0", "y"), ("r1", "y"), ("r2", "y"))]
    run_rules(g, ret.RETRACT_RULES, provenance=False)
    assert [_vis(g, "x", p, o) for p, o in (("r0", "y"), ("r1", "y"), ("r2", "y"))] == vis_before
    assert all(vis_before)


# --- NEW: the RETIRE opcode as a privileged mechanism -----------------------------------------

def test_retire_opcode_deletes_a_fact_edge_drop_ctrl_would_refuse():
    # RETIRE is the raw privileged mechanism: it deletes a reified FACT relation. DROP_CTRL refuses
    # the same fact edge (its no-fact-deletion refusal) — the two ops differ exactly on privilege.
    g = AttrGraph()
    s, o = g.add_node("s"), g.add_node("o")
    rel = g.add_relation(s, "likes", o)                  # a FACT relation (both endpoints fact-layer)
    m = Machine()
    # DROP_CTRL REFUSES this fact edge ...
    try:
        m.apply(g, [DROP_CTRL("s", "rel")], State({"s": s, "rel": rel}))
        assert False, "DROP_CTRL should refuse a fact edge"
    except ControlEdgeError:
        pass
    # ... RETIRE deletes the whole relation (edges + rel node), no refusal.
    m.apply(g, [RETIRE(rel="r")], State({"r": rel}))
    assert not g.has(rel)
    assert o not in g.succ(s) and rel not in g.succ(s)   # the live 2-hop is gone


# --- NEW: reflection preserved — the historical record + provenance stay meta-matchable --------

def test_history_record_is_meta_matchable_and_retains_provenance():
    g, r0_xy = _build()
    r1_xy = next(r for r in g.out(g.nodes_named("x")[0]) if g.predicate(r) == "r1")
    # who proves x r1 y (a rule justification), before retraction
    js_before = prov.support_js(g, r1_xy)
    assert js_before, "the derived fact should have a rule justification"

    ret.retract(g, r0_xy)

    # the historical record exists, grouped under <history>, and carries the pre-image (was_pred /
    # was_subj / was_obj) as INERT, meta-visible data a meta-rule / `why` can read.
    hist = g.nodes_named(ret.HISTORY)
    assert hist, "a <history> root should be present"
    recs = [o for tn in g.out(hist[0]) if g.has_key(tn, ret.RECORDS) for o in g.out(tn)]
    assert recs, "at least one retracted-fact record"
    preds = {str(g.get_attr(r, ret.WAS_PRED).value) for r in recs
             if g.get_attr(r, ret.WAS_PRED) is not None}
    assert {"r0", "r1", "r2"} <= preds                   # the whole retracted chain is recorded

    # the record for r1 retains its provenance (the <j:> that proved r1 now proves the record),
    # so reflection can still answer "what did we believe / why was it retracted".
    r1_rec = next(r for r in recs if g.get_attr(r, ret.WAS_PRED)
                  and str(g.get_attr(r, ret.WAS_PRED).value) == "r1")
    assert prov.support_js(g, r1_rec), "the retracted fact's justification survived on the record"

    # crucial: the record does NOT re-surface the deleted fact to ORDINARY matching (it is inert,
    # and uses distinct meta-predicates, so the live 2-hop x -[r1]-> y stays gone).
    assert not _vis(g, "x", "r1", "y")


# --- NEW: resurrection re-materializes a matching fact ----------------------------------------

def test_resurrect_restores_a_matching_fact():
    g, r0_xy = _build()
    ret.retract(g, r0_xy)
    assert not _vis(g, "x", "r1", "y")

    rec = next(r for tn in g.out(g.nodes_named(ret.HISTORY)[0]) if g.has_key(tn, ret.RECORDS)
               for r in g.out(tn)
               if g.get_attr(r, ret.WAS_PRED) and str(g.get_attr(r, ret.WAS_PRED).value) == "r1")
    ret.resurrect(g, rec)
    assert _vis(g, "x", "r1", "y")                       # the fact matches again


# --- NEW: the privilege gate — ordinary reasoning rules cannot emit RETIRE ---------------------

def test_no_rule_lowering_emits_retire():
    # The gate is structural: RETIRE and REDIRECT are NOT in the rule->program lowering vocabulary.
    # Lower a representative spread of rules (plain, drop, and the retraction cascade) and assert
    # none produces either — so a reasoning rule structurally cannot delete or rewire a fact.
    from ugm.machine import REDIRECT
    drop_rule = h.Rule(key="drop.x", lhs=[h.Pat("?a", "<mark>", "?b")], rhs=[],
                       drop=[h.Pat("?a", "gone", "?b")])
    for rule in (R1, R2, ret.CASCADE_RULE, drop_rule):
        match_ops, effect_ops, *_ = _lower_bank_rule(rule)
        assert not any(isinstance(op, (RETIRE, REDIRECT))
                       for op in match_ops + effect_ops), rule.key
    # the single-program lowering too (no NAC path)
    assert not any(isinstance(op, (RETIRE, REDIRECT)) for op in lower_rule(R1))

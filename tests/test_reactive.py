"""The reactive DERIVE gate (STEP B of the reactive-core arc, docs/design/reactive_core.md).

A predicate DECLARED reactive proactively materializes its consequence at the next committed ask when its
trigger has landed — the DATA drives it — while undeclared predicates stay pull-only (lazy). The gate rides
`reconsider`'s standing work-list (DIRTY_REG -> _affected), fires demand-gated, and is sound by construction
(presence-triggered, monotone). These tests drive END-TO-END through `ask_goal`'s commit gate, so the wiring
(react before reconsider, shared dirty set) is exercised, not just the unit.
"""
from __future__ import annotations

import ugm as h
from ugm import AttrGraph
from ugm.machine import Machine
from ugm.lowering import assemble_facts, load_fact_triples
from ugm.cnl.authoring import run_rules
from ugm.cnl.machine_rules import load_machine_rules
from ugm.cnl.query import ask_goal, _reify_rules
from ugm.production_rule import Rule, Pat
from ugm.policy import FirmwarePolicy
from ugm.reconsider import mark_dirty, reconsider
from ugm.reactive import declare_reactive, react, fire
from ugm.chain import chain_sip
from ugm.vocabulary import DENOTES
from ugm.chain import _facts_matching

RULE = "?x endangers ?y when ?x hunts ?y"       # a positive binary-relation rule (no copula ambiguity)


def _kb(trigger=("wolf", "hunts", "sheep")):
    kb = AttrGraph()
    rules = load_machine_rules(RULE)
    Machine().run(kb, assemble_facts([trigger]))
    mark_dirty(kb, [(trigger[1], trigger[2])])       # what intake records when a fact lands
    return kb, rules


def _materialized(kb, pred, s, o) -> bool:
    """A DIRECT read of PRESENT facts — no derivation. Did the consequence get materialized proactively?"""
    return bool(_facts_matching(kb, pred, s, o))


def test_reactive_predicate_materializes_on_a_committed_ask():
    # `endangers` declared reactive: a committed ask (about anything) fires the gate, so the consequence
    # of the landed trigger is materialized WITHOUT a query for it — the data drove it.
    kb, rules = _kb()
    declare_reactive(kb, "endangers")
    assert not _materialized(kb, "endangers", "wolf", "sheep")     # not there before the act
    ask_goal(kb, ("yesno", "wolf", "hunts", "sheep"), rules)       # a committed act on an unrelated goal
    assert _materialized(kb, "endangers", "wolf", "sheep")         # proactively derived at the gate


def test_a_non_reactive_predicate_stays_lazy():
    # Without the declaration the consequence is NOT materialized proactively — but is still derivable ON
    # DEMAND (laziness preserved, not lost).
    kb, rules = _kb()
    ask_goal(kb, ("yesno", "wolf", "hunts", "sheep"), rules)       # committed act, nothing reactive
    assert not _materialized(kb, "endangers", "wolf", "sheep")     # stayed pull-only
    assert ask_goal(kb, ("yesno", "wolf", "endangers", "sheep"), rules) == ["yes"]   # demand derives it


def test_reactive_firing_is_demand_gated_not_eager():
    # The reaction fires at the COMMITTED ASK, not at ingestion time: before any ask, nothing is
    # materialized even though the trigger and the declaration are both present.
    kb, rules = _kb()
    declare_reactive(kb, "endangers")
    assert not _materialized(kb, "endangers", "wolf", "sheep")     # no act yet -> no push
    ask_goal(kb, ("yesno", "wolf", "hunts", "sheep"), rules)
    assert _materialized(kb, "endangers", "wolf", "sheep")


def test_reactive_firing_does_not_re_fire_after_the_dirty_set_is_consumed():
    # Idempotence: after the first committed act (react derives, reconsider detaches the dirty set), a
    # second act finds nothing dirty -> react is zero-cost, and the fact stays materialized (monotone).
    kb, rules = _kb()
    declare_reactive(kb, "endangers")
    ask_goal(kb, ("yesno", "wolf", "hunts", "sheep"), rules)
    assert react(kb, rules) == 0                                   # dirty consumed -> nothing to fire
    assert _materialized(kb, "endangers", "wolf", "sheep")         # still there (monotone)


def test_reactivity_declared_as_data_a_fact_not_code():
    # The vision-true declaration: `endangers is reactive` is an ORDINARY FACT in the KB (authored like any
    # other), read by `reactive_preds` — no programmatic `declare_reactive`. A corpus declares its own
    # reactivity in its own text.
    kb, rules = _kb()
    Machine().run(kb, assemble_facts([("endangers", "is", "reactive")]))   # the declaration, AS DATA
    assert not _materialized(kb, "endangers", "wolf", "sheep")
    ask_goal(kb, ("yesno", "wolf", "hunts", "sheep"), rules)               # committed act fires the gate
    assert _materialized(kb, "endangers", "wolf", "sheep")                 # data-declared reactivity pushed


def test_a_reactive_cycle_drains_rather_than_loops():
    # The recall-autofire re-break, cycle form: two MUTUALLY reactive rules (p<->q). Presence-triggering +
    # monotone materialization mean the reaction cannot re-enqueue an absence -> the cycle DRAINS (both
    # facts settle) instead of self-reinforcing into a loop. The ask returns (does not hang).
    kb = AttrGraph()
    rules = load_machine_rules("?x q ?y when ?x p ?y") + load_machine_rules("?x p ?y when ?x q ?y")
    Machine().run(kb, assemble_facts([("a", "p", "b")]))
    mark_dirty(kb, [("p", "b")])
    declare_reactive(kb, "p")
    declare_reactive(kb, "q")
    ask_goal(kb, ("yesno", "a", "p", "b"), rules)                  # must terminate
    assert _materialized(kb, "q", "a", "b")                        # the cycle derived q and settled
    assert _materialized(kb, "p", "a", "b")


# ---------------------------------------------------------------------------
# The reactions fire into a STEP-A FRAME (canonical + guarded `_facts_matching`) — reactive-core STEP 2.
# A reaction's belief-reads route through `chain_sip`/`_facts_matching`, which unions a bound endpoint over
# its `denotes`-class and excludes control/inert scaffolding. Grains + assumption goals are name-keyed, so a
# TOKEN-resident trigger is seen (name-union) and the reaction fires on the ENTITY, not the token; a
# scaffolding node carrying a content edge is never reacted upon.
# ---------------------------------------------------------------------------

def test_derive_fires_on_a_token_resident_trigger():
    # A real token/entity dual-store: two "wolf" nodes with token --denotes--> entity, the `hunts` trigger
    # authored on the TOKEN. The reactive derive must materialize `endangers` readable under the shared name
    # (the canonical frame), not miss it because the trigger lives on the token.
    kb = AttrGraph()
    ent, tok, sheep = kb.add_node("wolf"), kb.add_node("wolf"), kb.add_node("sheep")
    kb.add_relation(tok, DENOTES, ent)
    kb.add_relation(tok, "hunts", sheep)                            # trigger on the TOKEN
    rules = load_machine_rules(RULE)
    declare_reactive(kb, "endangers")
    mark_dirty(kb, [("hunts", "sheep")])
    assert not _materialized(kb, "endangers", "wolf", "sheep")
    ask_goal(kb, ("yesno", "wolf", "hunts", "sheep"), rules)       # committed act fires the gate
    assert _materialized(kb, "endangers", "wolf", "sheep")         # fired on the entity's identity


def test_retract_sees_a_token_resident_breaker():
    # The RETRACT half's `_positive_now` recheck runs in the same frame: a forward-derived NAF `safe`
    # (NAC: not endangers) is journaled with provenance; a TOKEN-resident `hunts` then makes `endangers`
    # derivable, and the recheck must SEE it (name-union) and withdraw the stale `safe`.
    R_end = h.Rule(key="endangers.hunts", lhs=[h.Pat("?x", "hunts", "?y")],
                   rhs=[h.Pat("?x", "endangers", "?y")])
    R_safe = h.Rule(key="safe.near", lhs=[h.Pat("?x", "near", "?y")],
                    nac=[h.Pat("?x", "endangers", "?y")], rhs=[h.Pat("?x", "safe", "?y")])
    g = h.Graph()
    ent, tok = g.add_node("wolf"), g.add_node("wolf")
    g.add_relation(tok, DENOTES, ent)
    load_fact_triples(g, [("wolf", "near", "sheep")])
    run_rules(g, [R_end, R_safe], provenance=True)
    assert _materialized(g, "safe", "wolf", "sheep")               # NAF conclusion journaled

    g.add_relation(tok, "hunts", g.nodes_named("sheep")[0])        # TOKEN-resident breaker
    mark_dirty(g, [("hunts", "sheep")])
    assert reconsider(g, [R_end, R_safe]) == 1                     # the recheck saw it across the token/entity split
    assert not _materialized(g, "safe", "wolf", "sheep")           # stale conclusion withdrawn


def test_no_reaction_fires_on_control_scaffolding():
    # The guard excludes control/inert from the fact-view: a CONTROL node carrying a `hunts` content edge is
    # NOT a legitimate trigger, so the reactive derive never manufactures `endangers` on it.
    kb = AttrGraph()
    ghost, sheep = kb.add_node("ghost", control=True), kb.add_node("sheep")
    kb.add_relation(ghost, "hunts", sheep)
    rules = load_machine_rules(RULE)
    declare_reactive(kb, "endangers")
    mark_dirty(kb, [("hunts", "sheep")])
    ask_goal(kb, ("yesno", "sheep", "is", "sheep"), rules)         # committed act
    assert not _materialized(kb, "endangers", "ghost", "sheep")    # scaffolding never reacted upon


# ---------------------------------------------------------------------------
# ROBUSTNESS — the reactive push (`fire`) inherits the DEMAND engine's guarantees because `_derive`
# delegates to `chain_sip`, and C.1's unified gate preserves the derive-then-recheck ordering. These lock
# the by-construction claims against regression: an eager reactive materialization must compute the same
# world a demand pull would, even on the banks built to stress the engine (skolem minting, NAC, banded), and
# the derive/retract halves must cooperate in ONE pass.
# ---------------------------------------------------------------------------

def test_a_skolem_minting_reactive_rule_converges():
    # Eager push through a skolem-minting head must mint ONE witness per binding (converge by structural
    # re-find), not a fuel-capped flood — the demand-path convergence, preserved under the reactive gate.
    R = Rule(key="mk", lhs=[Pat("?p", "is_a", "state")],
             rhs=[Pat("?p", "has_succ", "s2?"), Pat("s2?", "succ_of", "?p")])
    g = h.Graph()
    for nm in ("p1", "p2"):
        n = g.add_node(nm); g.add_relation(n, "is_a", g.add_node("state"))
    declare_reactive(g, "has_succ")
    mark_dirty(g, [("is_a", "state")])
    fire(g, [R])
    assert len([x for x in g.nodes() if g.name(x) == "s2"]) == 2    # one skolem per state, converged


def test_a_deep_reactive_cascade_drains_in_one_fire():
    # a->b->c->d->e, all reactive: materializing `a` and firing ONCE closes the whole chain (the standing
    # work-list's `_affected` closure reaches every hop), not just the first hop.
    preds = ["a", "b", "c", "d", "e"]
    rules = [r for lo, hi in zip(preds, preds[1:]) for r in load_machine_rules(f"?x {hi} ?y when ?x {lo} ?y")]
    g = AttrGraph()
    x, y = g.add_node("x"), g.add_node("y")
    g.add_relation(x, "a", y)
    for p in preds[1:]:
        declare_reactive(g, p)
    mark_dirty(g, [("a", "y")])
    fire(g, rules)
    assert _materialized(g, "e", "x", "y")


def test_a_reactive_rule_with_a_nac_respects_the_block():
    # A reactive rule WITH a NAC: eager push must respect the negation exactly as demand would — push `ok`
    # iff the block is absent. This is the stratification-under-eager-materialization guarantee, per rule.
    rules = load_machine_rules("?c ok yes when ?l has ?c and not ?c blocked yes")

    def push_ok(blocked: bool) -> bool:
        g = AttrGraph()
        l, c, yes = g.add_node("l"), g.add_node("c"), g.add_node("yes")
        g.add_relation(l, "has", c)
        grains = [("has", "c")]
        if blocked:
            g.add_relation(c, "blocked", yes); grains.append(("blocked", "yes"))
        declare_reactive(g, "ok")
        mark_dirty(g, grains)
        fire(g, rules)
        return _materialized(g, "ok", "c", "yes")

    assert push_ok(blocked=False) is True                          # unblocked -> reactive push fires
    assert push_ok(blocked=True) is False                          # blocked   -> the NAC stops it


def test_banded_reactive_derive_materializes_under_policy():
    # The possibilistic fold flows through the derive half: under a BANDED policy a reactive consequence of a
    # graded trigger materializes (as a banded fact), matching a demand under the same policy.
    banded = FirmwarePolicy(uncertainty="banded")
    rules = load_machine_rules(RULE)
    g = AttrGraph()
    w, s = g.add_node("wolf"), g.add_node("sheep")
    g.add_relation(w, "hunts", s, confidence=0.6)
    declare_reactive(g, "endangers")
    mark_dirty(g, [("hunts", "sheep")])
    fire(g, rules, policy=banded)
    assert _facts_matching(g, "endangers", "wolf", "sheep", bands=True)


def test_derive_then_retract_cooperate_in_one_fire():
    # THE C.1 crux end-to-end: a REACTIVE derive produces the very breaker that makes a NAF conclusion stale,
    # and ONE `fire` both materializes it (derive) AND withdraws the stale conclusion (retract) — the
    # derive-then-recheck ordering, over the single shared dirty set / `_affected` closure.
    R_end = Rule(key="endangers.hunts", lhs=[Pat("?x", "hunts", "?y")], rhs=[Pat("?x", "endangers", "?y")])
    R_safe = Rule(key="safe.near", lhs=[Pat("?x", "near", "?y")],
                  nac=[Pat("?x", "endangers", "?y")], rhs=[Pat("?x", "safe", "?y")])
    g = h.Graph()
    load_fact_triples(g, [("wolf", "near", "sheep")])
    run_rules(g, [R_end, R_safe], provenance=True)
    assert _materialized(g, "safe", "wolf", "sheep")               # NAF conclusion stands (assumed)

    load_fact_triples(g, [("wolf", "hunts", "sheep")])             # the reactive trigger lands
    declare_reactive(g, "endangers")
    mark_dirty(g, [("hunts", "sheep")])
    fired, withdrawn = fire(g, [R_end, R_safe])
    assert fired >= 1 and withdrawn == 1
    assert _materialized(g, "endangers", "wolf", "sheep")          # derived
    assert not _materialized(g, "safe", "wolf", "sheep")           # and the stale conclusion withdrawn


def test_focus_scope_bounds_the_reactive_derive():
    # A reactive derive fires into the SCOPED frame: it materializes when the nodes are in the focus live-set
    # and NOT when they are excluded — a scoped push behaves like a scoped demand.
    rules = load_machine_rules(RULE)

    def fired_under(scope) -> bool:
        g = AttrGraph()
        w, s = g.add_node("wolf"), g.add_node("sheep")
        g.add_relation(w, "hunts", s)
        declare_reactive(g, "endangers")
        mark_dirty(g, [("hunts", "sheep")])
        fire(g, rules, focus_scope=scope)
        return _materialized(g, "endangers", "wolf", "sheep")

    assert fired_under(frozenset({"wolf", "sheep"})) is True       # in scope -> fires
    assert fired_under(frozenset({"unrelated"})) is False          # out of scope -> bounded out

"""Reactive DERIVE gate — the FiringGate (STEP B of the reactive-core arc, docs/design/reactive_core.md).

`reconsider` is a standing, cross-call, demand-gated, sound work-list whose ONE reaction is "retract a stale
NAF conclusion". This module adds the sibling reaction — DERIVE: proactively materialize the consequence of a
predicate DECLARED reactive, at the SAME committed-act gate, from the SAME dirty->affected dispatch. Together
they are the generalized FiringGate: one event queue (`reconsider.DIRTY_REG`), one trigger dispatch
(`reconsider._affected`, the bank's body->head closure), two reaction kinds (retract / derive).

SOUND BY CONSTRUCTION. The gate is PRESENCE-triggered — it fires on a positive materialization (a fact
landed, recorded in the dirty set), never on a demand-MISS. So a reaction's output can never be the absence
that triggered it: the recall-autofire self-reinforcement channel ([[recall-explicit-not-autofire]]) does not
exist here. Materialization is MONOTONE (real knowledge that persists, does not re-dirty), so a reactive
CYCLE (`P` reactive from `Q`, `Q` reactive from `P`) DRAINS rather than loops — a re-materialized fact adds
nothing and enqueues no new grain.

LAZY BY DEFAULT. Firing is DEMAND-GATED (only at a committed ask, via the `ask_goal` commit gate) and
PER-PREDICATE opt-in: an undeclared predicate stays pull-only, so eager exhaustive completion stays out
([[agent-not-theorem-prover]]). Only a predicate a KB explicitly declares reactive pushes.
"""
from __future__ import annotations

from .attrgraph import AttrGraph
from .reconsider import DIRTY_REG, _affected
from .rule_control import active_rules

REACTIVE_REG = "reactive_preds"        # kb.registers key: set[str] of predicate names declared reactive


def declare_reactive(kb: AttrGraph, pred: str) -> None:
    """Mark `pred` REACTIVE: once its trigger reaches a rule head, a materialization of that trigger
    proactively DERIVES the consequence at the next committed act. Opt-in — an undeclared predicate stays
    pull-only (demand-driven). (Programmatic for now; a `<reactive>` marker-fact / CNL surface is a later
    slice — the declaration is DATA, so it belongs in the KB, not code.)"""
    kb.registers.setdefault(REACTIVE_REG, set()).add(pred)


def reactive_preds(kb: AttrGraph) -> set[str]:
    """The predicate names this KB has declared reactive (empty ⇒ the whole KB is pull-only, the default)."""
    return kb.registers.get(REACTIVE_REG) or set()


def react(kb: AttrGraph, rules, *, policy=None, focus_scope=None) -> int:
    """The DERIVE half of the FiringGate, run at the committed-act gate BEFORE `reconsider` (which detaches
    the dirty set). Reads the dirty grains (does NOT detach — reconsider owns that), closes them over the
    bank's body->head edges (`reconsider._affected`), and for every affected grain whose predicate is
    DECLARED reactive materializes it demand-driven (`chain.chain_sip` — monotone, persists). Zero-cost when
    nothing is reactive or nothing is dirty. Returns the number of grains fired.

    Ordering: react (derive) precedes reconsider (retract) so a proactively-derived fact can fill an absence
    that reconsider then correctly retracts a stale conclusion over — derive-then-recheck."""
    reactive = reactive_preds(kb)
    if not reactive:
        return 0
    dirty = kb.registers.get(DIRTY_REG)
    if not dirty:
        return 0
    from .chain import chain_sip
    from .cnl.query import _reify_rules
    active = active_rules(kb, rules)
    affected = _affected(set(dirty), active)
    rule_g = None
    fired = 0
    for pred, obj in affected:
        if pred in reactive:
            if rule_g is None:
                rule_g = _reify_rules(active)
            # demand the reactive grain -> forward-derive + materialize it (and whatever it depends on)
            chain_sip(kb, (pred, None, obj), rules=rule_g, policy=policy, focus_scope=focus_scope)
            fired += 1
    return fired

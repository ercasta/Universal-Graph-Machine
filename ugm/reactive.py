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
from .vocabulary import COPULA

REACTIVE_REG = "reactive_preds"        # kb.registers key: programmatic set[str] of reactive predicate names
REACTIVE_MARK = "reactive"             # the declaration-as-DATA object: a fact `P is reactive`


def declare_reactive(kb: AttrGraph, pred: str) -> None:
    """Mark `pred` REACTIVE programmatically (a register set) — a convenience for tests/embedding. The
    VISION-TRUE declaration is DATA: an ordinary fact `P is reactive` in the KB (read by `reactive_preds`),
    so a corpus/session declares reactivity in its own text, not in Python. Both are honoured."""
    kb.registers.setdefault(REACTIVE_REG, set()).add(pred)


def reactive_preds(kb: AttrGraph) -> set[str]:
    """The predicate names this KB has declared reactive — read as DATA (`P is reactive` facts, the
    vision-true form) UNION any programmatic register set. Empty ⇒ the whole KB is pull-only (the default).
    A declaration is an ordinary fact, so it arrives through the same intake as any other and needs no
    special loader — `P is reactive` names the predicate P whose consequence should push."""
    from .chain import _facts_matching, ById
    out = set(kb.registers.get(REACTIVE_REG) or ())
    for s, _o in _facts_matching(kb, COPULA, None, REACTIVE_MARK):
        name = kb.name(s.node_id) if isinstance(s, ById) else s
        if name:
            out.add(name)
    return out


def _derive(kb: AttrGraph, active, affected: set, *, policy=None, focus_scope=None, max_rounds=1000) -> int:
    """The DERIVE dispatch over a PRE-COMPUTED affected closure: for every affected grain whose predicate
    is DECLARED reactive, materialize it demand-driven (`chain.chain_sip` — monotone, persists). Operates
    on the caller's already-closed `affected` + already-detached dirty set, so the unified `fire` shares
    both with the RETRACT half instead of recomputing them. Zero-cost when nothing is reactive.

    A reactive derivation that EXHAUSTS its fuel raises a HELP-FLARE (`flare.raise_flare`) instead of
    truncating silently — the robustness soft spot closed: the reactive push now surfaces a non-settling
    grain as a durable, reactable event rather than a quiet partial result."""
    reactive = reactive_preds(kb)
    if not reactive:
        return 0
    from .chain import chain_sip, _Exhaustion
    from .cnl.query import _reify_rules
    rule_g = None
    fired = 0
    for pred, obj in affected:
        if pred in reactive:
            if rule_g is None:
                rule_g = _reify_rules(active)
            # demand the reactive grain -> forward-derive + materialize it (and whatever it depends on)
            fuel = _Exhaustion()
            chain_sip(kb, (pred, None, obj), rules=rule_g, policy=policy, focus_scope=focus_scope,
                      max_rounds=max_rounds, _fuel=fuel)
            if fuel.exhausted:
                from .flare import raise_flare
                raise_flare(kb, (pred, None, obj))
            fired += 1
    return fired


def react(kb: AttrGraph, rules, *, policy=None, focus_scope=None, max_rounds=1000) -> int:
    """The DERIVE reaction as a standalone: read the dirty grains (does NOT detach), close them over the
    bank's body->head edges (`reconsider._affected`), and `_derive`. Kept for the direct derive-only path
    (and its re-break test); the committed-ask gate drives derive through the unified `fire` instead.
    Returns the number of grains fired. Zero-cost when nothing is reactive or nothing is dirty."""
    if not reactive_preds(kb):
        return 0
    dirty = kb.registers.get(DIRTY_REG)
    if not dirty:
        return 0
    active = active_rules(kb, rules)
    affected = _affected(set(dirty), active)
    return _derive(kb, active, affected, policy=policy, focus_scope=focus_scope, max_rounds=max_rounds)


def fire(kb: AttrGraph, rules, *, policy=None, focus_scope=None, max_rounds=1000) -> tuple[int, int]:
    """The unified FiringGate (reactive-core STEP C): read + detach the ONE dirty set once, close it over
    the active bank ONCE, and dispatch BOTH reaction kinds off that single closure — DERIVE (materialize
    declared-reactive consequences) then RETRACT (`reconsider.sweep`, the stale-NAF withdrawal). Derive
    precedes retract so a proactively-derived fact can fill an absence the sweep then correctly retracts a
    stale conclusion over (derive-then-recheck). Detach-once is the regress guard: neither half re-populates
    the dirty set (only intake/evidence do), so the captured snapshot is the whole event batch. Zero-cost
    when nothing is dirty. Returns `(grains_derived, justifications_withdrawn)`."""
    from .reconsider import sweep
    from .rule_control import disabled_keys
    dirty = kb.registers.get(DIRTY_REG)
    if not dirty:
        return (0, 0)
    grains = set(dirty)
    kb.registers[DIRTY_REG] = {}                     # detach ONCE (regress guard, shared by both halves)
    active = active_rules(kb, rules)
    affected = _affected(grains, active)
    fired = _derive(kb, active, affected, policy=policy, focus_scope=focus_scope, max_rounds=max_rounds)
    withdrawn = sweep(kb, active, affected, disabled_keys(kb), policy=policy, focus_scope=focus_scope)
    return (fired, withdrawn)

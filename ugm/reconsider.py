"""
Reconsider — demand-driven revision of assumed-absence conclusions (docs/design/reconsider_design.md).

A NAF firing journals the absences it leaned on (`J --assumes--> <assumed>`, crisp at Π=0). When
later knowledge (a user fact, an authored rule, a disable, gathered evidence) makes such an absence
DERIVABLE, the conclusions standing on it are stale. This module is the missing POLICY over the
existing mechanism (assumed-records + the cascade + copy-on-delete `retract`):

  MARK  — intake writes the changed grain into `kb.registers[DIRTY_REG]` (O(1); stepping state,
          Axis B — no rule reasons about it). Grain is `(pred, object-literal|None)`, NOT bare
          predicate: copula-heavy CNL puts nearly everything under `is`, so the object carries
          the discrimination (`("is", "alibied")`, not `"is"`).
  CHECK — at the next COMMITTED ask (`ask_goal` gates on a non-empty dirty set), close the dirty
          grains over the active bank's body→head edges, then re-ask each affected assumption's
          POSITIVE (exactly `_nac_blocks`' question, re-asked; banded = the same θ-gate).
  SWEEP — a broken assumption (or a justification whose rule was DISABLED) withdraws the facts its
          J proves: `seed_retract` + cascade + copy-on-delete. The history record is stamped
          `broken_assumption -> <assumed>` so `why` can answer "withdrawn because X became
          derivable". The triggering question's own closure then RE-DERIVES on demand whatever the
          aggressive cascade over-retracted that it actually needs (over-forget-and-re-derive).

One ordered pass suffices: the checks only ADD derivability (monotone closures), the retractions
only REMOVE facts. The dirty set is detached before the sweep (regress guard); facts the checks
materialize are real knowledge (monotone) and do not re-dirty.
"""
from __future__ import annotations

from . import provenance as prov
from . import retraction as ret
from .attrgraph import AttrGraph, graded
from .machine import Machine, MINT, State
from .production_rule import Rule, is_var, literal_name
from .rule_control import active_rules, disabled_keys

DIRTY_REG = "reconsider"          # kb.registers key: dict[(pred, obj|None), None], insertion-ordered
BROKEN = "broken_assumption"      # history-record stamp: record -[broken_assumption]-> <assumed>
_WILD_SUBJ = "anyone"             # `_record_assumptions`' wildcard spellings, mapped back to None
_WILD_OBJ = "anything"

_MACHINE = Machine()


# ---------------------------------------------------------------------------
# MARK — the dirty set (registers; written by intake / evidence acquisition)
# ---------------------------------------------------------------------------

def mark_dirty(kb: AttrGraph, grains) -> None:
    """Record that derivability may have changed for each `(pred, obj_name|None)` grain."""
    d = kb.registers.setdefault(DIRTY_REG, {})
    for g in grains:
        d[tuple(g)] = None


def fact_grain(kb: AttrGraph, rel: str) -> tuple[str, str | None]:
    """The dirty grain of a live fact relation: its predicate + its object's NAME (None if unnamed)."""
    obj = next(iter(kb.out(rel)), None)
    return (kb.predicate(rel), kb.name(obj) if obj is not None else None)


def rule_grains(rules) -> list[tuple[str, str | None]]:
    """The dirty grains of authored/toggled rules: one per HEAD atom — `(pred, literal-obj)`, or
    `(pred, None)` for a variable object (meaning: any object of that predicate)."""
    out = []
    for r in rules:
        for pat in r.rhs:
            out.append((literal_name(pat.p), None if is_var(pat.o) else literal_name(pat.o)))
    return out


# ---------------------------------------------------------------------------
# CHECK — grain closure over the active bank + the assumption re-ask
# ---------------------------------------------------------------------------

def _matches(grains: set, pred: str, obj: str | None) -> bool:
    """Does an atom `(pred, obj)` intersect the grain set? A None on EITHER side is a wildcard."""
    return ((pred, obj) in grains or (pred, None) in grains
            or (obj is None and any(g[0] == pred for g in grains)))


def _affected(dirty: set, active: list[Rule]) -> set:
    """Close the dirty grains over the bank's body→head edges: if a rule's BODY mentions an
    affected grain, its HEAD grains are affected too (a new `alibied` fact reaches a `cleared`
    assumption through `cleared <- alibied`). NAC atoms are excluded — new facts there only
    REDUCE derivability, which cannot break an absence. Terminates: the grain universe is the
    finite set drawn from `dirty` + the bank's head atoms."""
    out = set(dirty)
    changed = True
    while changed:
        changed = False
        for r in active:
            if any(_matches(out, literal_name(p.p), None if is_var(p.o) else literal_name(p.o))
                   for p in r.lhs):
                for h in r.rhs:
                    g = (literal_name(h.p), None if is_var(h.o) else literal_name(h.o))
                    if g not in out:
                        out.add(g)
                        changed = True
    return out


def _positive_now(kb: AttrGraph, rule_g, goal: tuple, *, policy, focus_scope=None) -> bool:
    """Is the assumed-absent tuple NOW derivable? Run the positive to closure (materializing —
    monotone, real knowledge) and read. Banded: broken iff the best band reaches the policy's
    θ — the same gate `_nac_blocks` applies, re-applied under current knowledge."""
    from .chain import chain_sip, _facts_matching
    chain_sip(kb, goal, rules=rule_g, policy=policy, focus_scope=focus_scope)
    banded = policy is not None and policy.banded
    rows = _facts_matching(kb, goal[0], goal[1], goal[2], focus_scope=focus_scope, bands=banded)
    if not banded:
        return bool(rows)
    pi = max((b for _s, _o, b, _e in rows), default=0.0)
    return pi >= policy.theta


def _assumption_goal(p: str, s: str, o: str) -> tuple:
    return (p, None if s == _WILD_SUBJ else s, None if o == _WILD_OBJ else o)


# ---------------------------------------------------------------------------
# SWEEP — withdraw broken conclusions, stamp the archive
# ---------------------------------------------------------------------------

def _proven_live(kb: AttrGraph, j: str) -> list[str]:
    """The LIVE facts `j` proves (a J proving only inert history records is already settled)."""
    return [c for pn in kb.out(j) if kb.has_key(pn, prov.PROVES)
            for c in kb.out(pn) if not kb.is_inert(c)]


def _stamp_broken(kb: AttrGraph, j: str, assumed_node: str) -> None:
    """After the retire, `j` proves history records; wire each `record -[broken_assumption]-> A`
    (inert, as a MINT program) — the why-trail of the withdrawal, in-graph."""
    recs = [c for pn in kb.out(j) if kb.has_key(pn, prov.PROVES)
            for c in kb.out(pn) if kb.is_inert(c)]
    for i, rec in enumerate(recs):
        _MACHINE.apply(kb, [MINT(f"_b{i}", attrs={BROKEN: graded(1.0)},
                                 in_edges=["_rec"], edges=["_a"], inert=True)],
                       State({"_rec": rec, "_a": assumed_node}))


def _assumed_nodes(kb: AttrGraph, j: str) -> list[tuple[str, tuple]]:
    """`(node, (pred, subj, obj))` per `<assumed>` record of `j` (node id kept for the stamp)."""
    out = []
    for pn in kb.out(j):
        if kb.has_key(pn, prov.ASSUMES):
            for a in kb.out(pn):
                p, s, o = (kb.get_attr(a, k) for k in ("a_pred", "a_subj", "a_obj"))
                if p is not None and s is not None and o is not None:
                    out.append((a, (str(p.value), str(s.value), str(o.value))))
    return out


def sweep(kb: AttrGraph, active: list[Rule], affected: set, off, *,
          policy=None, focus_scope=None) -> int:
    """The RETRACT dispatch (design §4), over a PRE-COMPUTED affected closure and an ALREADY-detached
    dirty set — the caller owns the read+detach regress guard and the `_affected` closure, so the
    unified FiringGate (`reactive.fire`) can share both with the DERIVE half instead of recomputing them.
    For each justification, if its rule is DISABLED or an assumed absence it leans on is now derivable,
    withdraw the facts it proves (cascade + copy-on-delete archive) and stamp the archive. Returns the
    number of justifications whose conclusions were withdrawn."""
    rule_g = None                                    # reified lazily — only if a check is needed
    withdrawn = 0
    for j in [n for n in kb.nodes() if prov.is_justification(kb.name(n))]:
        live = _proven_live(kb, j)
        if not live:
            continue
        breaker = None                               # the <assumed> node that broke (for the stamp)
        broken = prov.rule_of_j(kb, j) in off        # D3: a disabled rule's support is gone by fiat
        if not broken:
            for a_node, (p, s, o) in _assumed_nodes(kb, j):
                if not _matches(affected, p, None if o == _WILD_OBJ else o):
                    continue
                if rule_g is None:
                    from .cnl.query import _reify_rules
                    rule_g = _reify_rules(active)
                if _positive_now(kb, rule_g, _assumption_goal(p, s, o),
                                 policy=policy, focus_scope=focus_scope):
                    broken, breaker = True, a_node
                    break
        if not broken:
            continue
        for c in live:                               # withdraw: cascade + copy-on-delete archive
            if kb.has(c):
                ret.retract(kb, c)
        if breaker is not None:
            _stamp_broken(kb, j, breaker)
        withdrawn += 1
    return withdrawn


def reconsider(kb: AttrGraph, rules: list[Rule], *, policy=None, focus_scope=None) -> int:
    """The question-time RETRACT sweep as a standalone reaction (design §4): read + detach the dirty set,
    close it over the active bank, and `sweep`. Zero-cost when nothing was marked. Kept for the direct
    retract-only path (and its re-break test); the committed-ask gate now drives the sweep through the
    unified `reactive.fire`, which shares the detach + `_affected` closure with the DERIVE half."""
    dirty = kb.registers.get(DIRTY_REG)
    if not dirty:
        return 0
    kb.registers[DIRTY_REG] = {}                     # detach first (regress guard)
    active = active_rules(kb, rules)
    affected = _affected(set(dirty), active)
    return sweep(kb, active, affected, disabled_keys(kb), policy=policy, focus_scope=focus_scope)

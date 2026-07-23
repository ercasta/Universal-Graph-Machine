"""Help-flare — fuel exhaustion as a durable, reactable signal (docs/design/reactive_core.md §Robustness).

A demand closure that exhausts its round budget (`chain._Exhaustion`) used to truncate SILENTLY — the latent
honesty gap the robustness audit found (the design promises closures "terminate honestly"). This module turns
exhaustion into an EVENT the reactive core can react to: a FLARE, materialized as a normal (reactable) fact
`<goal-node> unresolved yes`, where the goal node REIFIES the exhausted goal (`f_pred`/`f_subj`/`f_obj` — the
sibling of reconsider's `<assumed>` record). The flare is:

  - DURABLE + queryable (`flares` reads them back) — the honest "I did not finish looking at G", persisted;
  - DEDUPED per goal (idempotent — re-exhausting G does not storm);
  - REACTABLE — it marks its grain dirty, so a declared reactive rule (`… when ?g unresolved yes`) fires at
    the next committed act, and the reified goal node carries the identity a recovery reaction needs;
  - SOUND by construction — PRESENCE-triggered (fires on the exhaustion EVENT, never on a demand-MISS, so the
    recall-autofire self-reinforcement channel does not exist [[recall-explicit-not-autofire]]) and INERT/
    opt-in (no reaction unless a predicate is declared reactive → no loop; making progress is the reaction
    author's responsibility, exactly like `reactive` preds and `open_preds`).

The governor layer (accumulators + thresholds + recovery, docs/design/reactive_core.md §Governor) builds on
this: a flare bumps a per-goal accumulator, and a declared threshold turns a repeatedly-flaring goal into a
bounded, honest give-up — heuristic termination without pretending to decide halting.
"""
from __future__ import annotations

from .attrgraph import AttrGraph, NAME, valued
from .machine import Machine, MINT, State
from .reconsider import mark_dirty

FLARE_PRED = "unresolved"     # the flare marker predicate (PLAIN → reactable; a bracketed <…> would be
FLARE_MARK = "yes"            # control and excluded from the fact-view; domain corpora avoid this word)
FLARED_PRED = "flared"        # a DISTINCT event per exhaustion `?e flared <goal>` — the ACCUMULATOR the
EVENT_NAME = "flare_event"    # governor counts by distinct-event self-join (bench/spike_threshold_no_tool)
_WILD = "*"                   # a wildcard (None) endpoint, spelled for the reified attrs

_MACHINE = Machine()


def _goal_name(goal) -> str:
    p, s, o = (x if x is not None else _WILD for x in goal)
    return f"goal:{p}:{s}:{o}"


def goal_node(kb: AttrGraph, goal) -> str:
    """The deduped reified node for `goal` (pred, subj|None, obj|None), carrying `f_pred`/`f_subj`/`f_obj`
    so a recovery reaction can recover WHICH goal ran out of fuel — one node per goal identity."""
    nm = _goal_name(goal)
    existing = kb.nodes_named(nm)
    if existing:
        return existing[0]
    p, s, o = (x if x is not None else _WILD for x in goal)
    return _MACHINE.apply(kb, [MINT("_g", attrs={
        "name": valued(nm), "f_pred": valued(p), "f_subj": valued(s), "f_obj": valued(o)})],
        State({})).regs["_g"]


def raise_flare(kb: AttrGraph, goal) -> str:
    """Materialize the flare for `goal` and mark its grains — the reactive-core event. TWO writes:

    (1) a fresh DISTINCT event `<event> flared <goal>` — the ACCUMULATOR, NEVER deduped: one per
        exhaustion, so the governor bank can count repeated failures by a distinct-event self-join
        (`bench/spike_threshold_no_tool.py`) — monotone (accumulating facts), no arithmetic, no tool;
    (2) the standing DEDUPED `<goal> unresolved yes` signal (idempotent — no storm) for the `unresolved`
        reactions.

    Both grains are marked dirty so the reactive gate escalates the ladder and re-checks the signal at the
    next committed act. Returns the reified goal node."""
    g = goal_node(kb, goal)
    ev = _MACHINE.apply(kb, [MINT("_e", attrs={NAME: valued(EVENT_NAME)})], State({})).regs["_e"]
    kb.add_relation(ev, FLARED_PRED, g)                              # (1) the distinct counting event
    dirty = [(FLARED_PRED, None)]
    if not any(kb.predicate(r) == FLARE_PRED for r in kb.out(g)):    # (2) the deduped standing signal
        yes = (kb.nodes_named(FLARE_MARK) or [None])[0] or kb.add_node(FLARE_MARK)
        kb.add_relation(g, FLARE_PRED, yes)
        dirty.append((FLARE_PRED, FLARE_MARK))
    mark_dirty(kb, dirty)
    return g


def flares(kb: AttrGraph) -> list[tuple[str, str | None, str | None]]:
    """The goals currently flared (the durable trace of unfinished closures) — for an outer loop / harness
    that governs beyond the in-language reactive rules. Reads each reified goal node back to (pred, subj,
    obj) with `*` unwilded to None."""
    def unwild(v):
        return None if v is None or str(v.value) == _WILD else str(v.value)
    out = []
    for g in kb.nodes():
        if any(kb.predicate(r) == FLARE_PRED for r in kb.out(g)):
            p, s, o = (kb.get_attr(g, k) for k in ("f_pred", "f_subj", "f_obj"))
            if p is not None:
                out.append((str(p.value), unwild(s), unwild(o)))
    return out

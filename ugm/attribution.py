"""Attribution — the `holder` scope KIND (docs/design/scope_generalization.md Slice 1).

The first scope kind beyond `epistemic`, and the one that validates KIND DISPATCH. A HOLDER scope
relativizes a fact to WHO holds it: *N considers the lion a cat* pens `lion is_a cat` in N's holder
scope. Two things distinguish it from an epistemic fork, and both are the point:

  - ONTOLOGICAL, not epistemic. For the holder, the fact holds DEFINITELY — no possibility discount.
    A fork checked globally shows up banded (`likely`); a holder scope checked FOR ITS HOLDER shows up
    at full strength (`yes`). This falls out of the pencil/scope read for free: the scope carries NO
    `<likeliness>`, so the banded overlay never discounts it, and when it is the active scope its
    pencils merge at CERTAIN (`chain._band_overlay`).
  - NON-VERIDICAL globally. A penned proposition is not the world's. A global check (no scope) never
    sees a control-marked pencil, so `is the lion a cat` answers `assumed-no` — exactly right: the
    world does not say the lion is a cat just because N considers it one.

The mechanism is entirely the existing pencil scope (`suppose._pencil`). What this module adds is the
KIND (`suppose.SCOPE_KIND = holder`), holder KEYING (`<holder>` = the party, so one scope per holder is
reused), and the authoring/read surface. NO ordering and NO scope-variable rules — those are Slice 2.
"""
from __future__ import annotations

from .attrgraph import AttrGraph, NAME, valued, graded
from .check import check as _check
from .machine import Machine, MINT, State
from .suppose import (HYPOTHESIS, SCOPE_KIND, KIND_HOLDER, HOLDER, _pencil, _resolve,
                      scope_kind, scope_members)

_MACHINE = Machine()

Triple = tuple[str, str, str]


def holder_scope_of(g: AttrGraph, holder: str, *, create: bool = False) -> str | None:
    """The HOLDER scope relativizing facts to `holder` (a party NAME) — found through the `<holder>`
    key index (candidates-by-key, filter-by-value; there is deliberately no value index). ONE scope
    per holder, so successive `consider`s accrete in it. `None` if the holder has no scope and not
    `create`; on `create`, mint the scope kinded `holder` and keyed to the party."""
    for n in g.nodes_with_key(HOLDER):
        a = g.get_attr(n, HOLDER)
        if a is not None and a.value == holder:
            return n
    if not create:
        return None
    return _MACHINE.apply(g, [MINT("_hs", attrs={NAME: valued(HYPOTHESIS), HYPOTHESIS: graded(1.0),
                                                 SCOPE_KIND: valued(KIND_HOLDER),
                                                 HOLDER: valued(holder)}, control=True)],
                          State({})).regs["_hs"]


def consider(g: AttrGraph, holder: str, triple: Triple) -> str:
    """`holder` considers `triple = (subj, pred, obj)`: pen it in `holder`'s scope (minted on first
    use). ONTOLOGICAL for the holder, NON-VERIDICAL globally — this writes nothing to ink. Returns the
    holder scope id. The endpoints resolve to existing entity nodes (minted if absent — the entities
    the attribution is ABOUT), exactly as a SUPPOSE assumption does; only the relation is attributed."""
    subj, pred, obj = triple
    scope = holder_scope_of(g, holder, create=True)
    _pencil(g, scope, _resolve(g, subj), pred, _resolve(g, obj))
    return scope


def holds_for(g: AttrGraph, holder: str, goal: tuple[str, str | None, str | None], **kw) -> str:
    """CHECK `goal = (pred, subj, obj)` RELATIVIZED to `holder` — reasoning inside the holder's scope,
    where the attributed facts hold ontologically (`check(scope=…)`). Returns a `check` status. If the
    holder has no scope at all, the goal is checked globally (so it answers `assumed-no` for a penned
    proposition never attributed to anyone). Passes `check` kwargs through (`policy`, `rules`, …)."""
    return _check(g, goal, scope=holder_scope_of(g, holder), **kw)


def holders_considering(g: AttrGraph, triple: Triple) -> list[str]:
    """Every holder whose scope pens `triple = (subj, pred, obj)` — 'who considers this?'. Reads the
    holder scopes and their pencil members by name; the inverse of `consider`, for explanation."""
    subj, pred, obj = triple
    out: list[str] = []
    for n in g.nodes_with_key(HOLDER):
        if scope_kind(g, n) != KIND_HOLDER:
            continue
        who = g.get_attr(n, HOLDER)
        if who is None:
            continue
        for rel in scope_members(g, n):
            if not g.has(rel) or g.predicate(rel) != pred:
                continue
            s = next(iter(g.into(rel)), None)
            o = next(iter(g.out(rel)), None)
            if s is not None and o is not None and g.name(s) == subj and g.name(o) == obj:
                out.append(who.value)
                break
    return out

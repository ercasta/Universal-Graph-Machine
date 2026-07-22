"""Temporal — the `temporal` scope KIND, part (a) of scope_generalization.md Slice 2.

The second ONTOLOGICAL scope kind, and the ordered one. A TEMPORAL scope relativizes a fact to an
ordered INDEX: *the lion has a mane at t1* pens `lion has mane` in the scope for `t1`. Like a holder
scope it is ONTOLOGICAL (definite at its index, no possibility discount) and NON-VERIDICAL globally (a
timed fact is not the timeless world's — a global check is `assumed-no`). It differs from `holder` in
ONE thing: its indices are ORDERED, and the order is ordinary relational content between the index
ENTITIES (`t1 before t2`), traversed by an ordinary recursive rule (spike O1 — NATIVE). So this module
is, again, the KIND + KEYING + AUTHORING layer over the existing pencil scope; the scope is keyed to an
index entity exactly as a holder scope is keyed to a party.

WHAT THIS PART DOES **NOT** DO. Ranging a BINARY fact ACROSS indices — the frame axiom
`has(x,y)@t1 ∧ t1 before t2 ⇒ has(x,y)@t2` — needs a rule to BIND the scope of a matched fact as a
variable, which the rule language cannot do yet (spike O2c). That SCOPE-VARIABLE mechanism is part (b),
the one genuinely new engine mechanism of this slice. A UNARY state folded into the predicate
(`hungry_at t1`, spike O2a) already ranges natively with an ordinary rule and needs none of this — that
is the 3-place tense an agent can express today. Part (a) delivers the ordered ontological scope and the
relativized read; part (b) makes a scoped binary fact persist.
"""
from __future__ import annotations

from .attrgraph import AttrGraph, NAME, valued, graded
from .check import check as _check
from .lowering import assemble_facts
from .machine import Machine, MINT, State
from .suppose import (HYPOTHESIS, SCOPE_KIND, KIND_TEMPORAL, INDEX, _pencil, _resolve,
                      scope_kind, scope_members)

_MACHINE = Machine()

Triple = tuple[str, str, str]


def temporal_scope_of(g: AttrGraph, index: str, *, create: bool = False) -> str | None:
    """The TEMPORAL scope relativizing facts to `index` (an ordered-index entity NAME, e.g. `t1`) —
    found through the `<temporal-index>` key (candidates-by-key, filter-by-value). ONE scope per index,
    reused, so successive `at_time`s at the same index accrete in it. `None` if absent and not `create`;
    on `create`, mint the scope kinded `temporal` and keyed to the index. The index entity itself is an
    ordinary node (the one the ordering facts `t1 before t2` relate) — resolved so scope and order agree
    on the same node."""
    for n in g.nodes_with_key(INDEX):
        a = g.get_attr(n, INDEX)
        if a is not None and a.value == index:
            return n
    if not create:
        return None
    _resolve(g, index)                                     # the index is an ordinary orderable entity
    return _MACHINE.apply(g, [MINT("_ts", attrs={NAME: valued(HYPOTHESIS), HYPOTHESIS: graded(1.0),
                                                 SCOPE_KIND: valued(KIND_TEMPORAL),
                                                 INDEX: valued(index)}, control=True)],
                          State({})).regs["_ts"]


def order(g: AttrGraph, earlier: str, later: str) -> None:
    """Record `earlier before later` as ordinary INK relational content between the two index entities
    (spike O1: the order is facts, traversal is an ordinary recursive rule). Not a scope operation — the
    ordering lives among the indices, not inside any scope."""
    _MACHINE.run(g, assemble_facts([(earlier, "before", later)]))


def at_time(g: AttrGraph, index: str, triple: Triple) -> str:
    """`triple = (subj, pred, obj)` holds AT `index`: pen it in `index`'s temporal scope (minted on
    first use). ONTOLOGICAL at the index, NON-VERIDICAL globally — writes nothing to ink. Returns the
    scope id. Endpoints resolve to existing entity nodes (minted if absent), as a SUPPOSE assumption
    does; only the relation is relativized to time."""
    subj, pred, obj = triple
    scope = temporal_scope_of(g, index, create=True)
    _pencil(g, scope, _resolve(g, subj), pred, _resolve(g, obj))
    return scope


def holds_at(g: AttrGraph, index: str, goal: tuple[str, str | None, str | None], **kw) -> str:
    """CHECK `goal = (pred, subj, obj)` RELATIVIZED to `index` — reasoning inside that index's scope,
    where timed facts hold ontologically (`check(scope=…)`). Returns a `check` status. Passes `check`
    kwargs through (`policy`, `rules`, …).

    MATERIALIZES the index's scope (`create=True`): to reason ABOUT a time you must have a context to
    reason IN, and a cross-index rule (`has(x,y)@?t1 ∧ ?t1 before ?t2 ⇒ has(x,y)@?t2`) pens its
    conclusion INTO this scope — so the scope must exist for the query to receive it. This is
    demand-driven materialization (the query realizes the context it asks about), not a fact write: the
    scope starts empty, and a goal no rule reaches still answers `assumed-no`. The index becomes a
    known context afterwards (it will appear in `indices_holding` for anything a rule persisted there)."""
    return _check(g, goal, scope=temporal_scope_of(g, index, create=True), **kw)


def indices_holding(g: AttrGraph, triple: Triple) -> list[str]:
    """Every index whose scope pens `triple = (subj, pred, obj)` — 'when does this hold?'. The inverse
    of `at_time`, for explanation; unordered (the caller ranks by the `before` facts)."""
    subj, pred, obj = triple
    out: list[str] = []
    for n in g.nodes_with_key(INDEX):
        if scope_kind(g, n) != KIND_TEMPORAL:
            continue
        idx = g.get_attr(n, INDEX)
        if idx is None:
            continue
        for rel in scope_members(g, n):
            if not g.has(rel) or g.predicate(rel) != pred:
                continue
            s = next(iter(g.into(rel)), None)
            o = next(iter(g.out(rel)), None)
            if s is not None and o is not None and g.name(s) == subj and g.name(o) == obj:
                out.append(idx.value)
                break
    return out

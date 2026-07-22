"""Scope kinds — the KINDED relativizer, realized in code (docs/design/scope_generalization.md §4–§5).

A scope is a `<hypothesis>` node carrying a `kind`; a fact penned in it holds RELATIVE TO the scope,
and the kind says how the read treats that relativity. This module realizes the §4 table IN CODE. The
holder and temporal kinds used to be two near-identical modules (`attribution.py`, `temporal.py`); they
are ONE kind-parameterized core here plus thin kind-bound verbs, because the entire axis of variation
between them is a `(kind, key_attr)` pair plus TWO policy flags:

  - `resolve_key` — whether the KEY names an orderable ENTITY that must exist as a node. Temporal: the
    index is related by `before` facts, so it is resolved. Holder: the party is just a value on the key.
  - `materialize` — whether a READ mints the queried scope. Temporal: a cross-index rule pens INTO the
    queried scope, so it must exist for the query to receive the conclusion (demand-driven
    materialization). Holder: an absent scope ⇒ a global check ⇒ `assumed-no`.

Both kinds are ONTOLOGICAL (definite in-scope, no possibility discount — the scope carries no
`<likeliness>`, so the banded overlay never discounts it, and its pencils merge at CERTAIN when active)
and NON-VERIDICAL globally (a global check never sees a control-marked pencil ⇒ `assumed-no`: the world
does not hold a penned proposition just because someone considers it, or it held at some time). This
falls out of the existing pencil/scope read UNCHANGED — the kinds add only KEYING and the ontological
label; NO read-engine change was needed, validated across both kinds (Slice 1, Slice 2a).

The `epistemic` kind (fork/suppose) is NOT a facade here: it carries a `<likeliness>` band, its read
IS discounted, and it is not entity-keyed — it lives in `suppose.py`/`possibility.py`. The scope-
VARIABLE rule path (`@?t`) is still hardcoded to `temporal` in `chain.py`; ranging `@?t` over other
kinds is the deferred "family-B" work.
"""
from __future__ import annotations

from .attrgraph import AttrGraph, NAME, valued, graded
from .check import check as _check
from .lowering import assemble_facts
from .machine import Machine, MINT, State
from .suppose import (HYPOTHESIS, SCOPE_KIND, KIND_HOLDER, KIND_TEMPORAL, HOLDER, INDEX,
                      _pencil, _resolve, scope_kind, scope_members)

_MACHINE = Machine()

Triple = tuple[str, str, str]
Goal = tuple[str, str | None, str | None]


# ── generic kind-parameterized core ──────────────────────────────────────────

def scope_of(g: AttrGraph, kind: str, key_attr: str, key: str, *,
             create: bool = False, resolve_key: bool = False) -> str | None:
    """The scope of `kind` keyed to `key` via `key_attr` — found through the key index
    (candidates-by-key, filter-by-value; there is deliberately no value index). ONE scope per key, so
    successive writes accrete in it. `None` if the key has no scope and not `create`; on `create`,
    `_resolve` the key entity first if `resolve_key` (the key names an orderable node the ordering facts
    relate), then MINT the scope kinded `kind` and keyed to `key`."""
    for n in g.nodes_with_key(key_attr):
        a = g.get_attr(n, key_attr)
        if a is not None and a.value == key:
            return n
    if not create:
        return None
    if resolve_key:
        _resolve(g, key)                                     # the key is an ordinary orderable entity
    return _MACHINE.apply(g, [MINT("_sc", attrs={NAME: valued(HYPOTHESIS), HYPOTHESIS: graded(1.0),
                                                 SCOPE_KIND: valued(kind),
                                                 key_attr: valued(key)}, control=True)],
                          State({})).regs["_sc"]


def pen_scoped(g: AttrGraph, kind: str, key_attr: str, key: str, triple: Triple, *,
               resolve_key: bool = False) -> str:
    """Pen `triple = (subj, pred, obj)` in the `kind` scope keyed to `key` (minted on first use).
    ONTOLOGICAL in-scope, NON-VERIDICAL globally — writes nothing to ink. Returns the scope id. The
    endpoints resolve to existing entity nodes (minted if absent — the entities the fact is ABOUT),
    exactly as a SUPPOSE assumption does; only the RELATION is relativized to the scope."""
    subj, pred, obj = triple
    scope = scope_of(g, kind, key_attr, key, create=True, resolve_key=resolve_key)
    _pencil(g, scope, _resolve(g, subj), pred, _resolve(g, obj))
    return scope


def holds_in(g: AttrGraph, kind: str, key_attr: str, key: str, goal: Goal, *,
             materialize: bool = False, **kw) -> str:
    """CHECK `goal = (pred, subj, obj)` RELATIVIZED to the `kind` scope keyed to `key` — reasoning
    inside that scope, where relativized facts hold ontologically (`check(scope=…)`). Returns a `check`
    status; passes `check` kwargs (`policy`, `rules`, …) through. If `materialize`, the queried scope is
    minted on read (a cross-scope rule pens its conclusion INTO this scope, so it must exist to receive
    it — demand-driven; the scope starts empty, a goal no rule reaches still answers `assumed-no`). If
    not, an absent scope means a GLOBAL check — `assumed-no` for a proposition never penned to `key`."""
    return _check(g, goal, scope=scope_of(g, kind, key_attr, key, create=materialize), **kw)


def scopes_holding(g: AttrGraph, kind: str, key_attr: str, triple: Triple) -> list[str]:
    """Every `key` whose `kind` scope pens `triple = (subj, pred, obj)` — the inverse of `pen_scoped`,
    for explanation ('who considers this?' / 'when does this hold?'). Reads the scopes by key and their
    pencil members by name; unordered (a temporal caller ranks by the `before` facts)."""
    subj, pred, obj = triple
    out: list[str] = []
    for n in g.nodes_with_key(key_attr):
        if scope_kind(g, n) != kind:
            continue
        keyed = g.get_attr(n, key_attr)
        if keyed is None:
            continue
        for rel in scope_members(g, n):
            if not g.has(rel) or g.predicate(rel) != pred:
                continue
            s = next(iter(g.into(rel)), None)
            o = next(iter(g.out(rel)), None)
            if s is not None and o is not None and g.name(s) == subj and g.name(o) == obj:
                out.append(keyed.value)
                break
    return out


# ── holder kind (attribution, Slice 1) ───────────────────────────────────────
# A HOLDER scope relativizes a fact to WHO holds it: *N considers the lion a cat* pens `lion is_a cat`
# in N's holder scope — ONTOLOGICAL for N (no discount), NON-VERIDICAL globally (the world does not say
# the lion is a cat just because N considers it one). One scope per party, keyed by `<holder>`.

def holder_scope_of(g: AttrGraph, holder: str, *, create: bool = False) -> str | None:
    """The HOLDER scope relativizing facts to `holder` (a party NAME). `None` if absent and not
    `create`; on `create`, mint it kinded `holder` and keyed to the party."""
    return scope_of(g, KIND_HOLDER, HOLDER, holder, create=create)


def consider(g: AttrGraph, holder: str, triple: Triple) -> str:
    """`holder` considers `triple = (subj, pred, obj)`: pen it in `holder`'s scope (minted on first
    use). ONTOLOGICAL for the holder, NON-VERIDICAL globally — writes nothing to ink."""
    return pen_scoped(g, KIND_HOLDER, HOLDER, holder, triple)


def holds_for(g: AttrGraph, holder: str, goal: Goal, **kw) -> str:
    """CHECK `goal = (pred, subj, obj)` RELATIVIZED to `holder`. If the holder has no scope at all, the
    goal is checked globally (so it answers `assumed-no` for a proposition never attributed to anyone)."""
    return holds_in(g, KIND_HOLDER, HOLDER, holder, goal, **kw)


def holders_considering(g: AttrGraph, triple: Triple) -> list[str]:
    """Every holder whose scope pens `triple` — 'who considers this?', for explanation."""
    return scopes_holding(g, KIND_HOLDER, HOLDER, triple)


# ── temporal kind (tense, Slice 2a) ──────────────────────────────────────────
# A TEMPORAL scope relativizes a fact to an ordered INDEX: *the lion has a mane at t1* pens `lion has
# mane` in the scope for `t1`. Ontological at its index, non-veridical globally — like holder, but its
# indices are ORDERED, and the order is ordinary relational content between the index ENTITIES
# (`t1 before t2`, `order`), traversed by an ordinary recursive rule (spike O1 — NATIVE).

def temporal_scope_of(g: AttrGraph, index: str, *, create: bool = False) -> str | None:
    """The TEMPORAL scope relativizing facts to `index` (an ordered-index entity NAME, e.g. `t1`). The
    index entity is an ordinary node (the one the ordering facts relate), so it is `_resolve`d on
    `create` — scope and order agree on the same node."""
    return scope_of(g, KIND_TEMPORAL, INDEX, index, create=create, resolve_key=True)


def at_time(g: AttrGraph, index: str, triple: Triple) -> str:
    """`triple = (subj, pred, obj)` holds AT `index`: pen it in `index`'s temporal scope (minted on
    first use). ONTOLOGICAL at the index, NON-VERIDICAL globally — writes nothing to ink."""
    return pen_scoped(g, KIND_TEMPORAL, INDEX, index, triple, resolve_key=True)


def holds_at(g: AttrGraph, index: str, goal: Goal, **kw) -> str:
    """CHECK `goal = (pred, subj, obj)` RELATIVIZED to `index`. MATERIALIZES the index's scope: to
    reason ABOUT a time you must have a context to reason IN, and a cross-index rule
    (`has(x,y)@?t1 ∧ ?t1 before ?t2 ⇒ has(x,y)@?t2`) pens its conclusion INTO this scope — so the scope
    must exist for the query to receive it. Demand-driven materialization, not a fact write: the scope
    starts empty, and a goal no rule reaches still answers `assumed-no`."""
    return holds_in(g, KIND_TEMPORAL, INDEX, index, goal, materialize=True, **kw)


def order(g: AttrGraph, earlier: str, later: str) -> None:
    """Record `earlier before later` as ordinary INK relational content between the two index entities
    (spike O1: the order is facts, traversal is an ordinary recursive rule). Temporal-only, and NOT a
    scope operation — the ordering lives among the indices, not inside any scope."""
    _MACHINE.run(g, assemble_facts([(earlier, "before", later)]))


def indices_holding(g: AttrGraph, triple: Triple) -> list[str]:
    """Every index whose scope pens `triple` — 'when does this hold?', for explanation; unordered (the
    caller ranks by the `before` facts)."""
    return scopes_holding(g, KIND_TEMPORAL, INDEX, triple)

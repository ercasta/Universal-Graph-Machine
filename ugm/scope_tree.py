"""Scope tree — nested scope NODES + the scope-local visibility predicate (scope_reframe_audit.md §1, §6).

STEP 1 of the scope reframe. A relativizer ("John says", "at T", "under H", "that…causes…") mints a SCOPE
node; a fact or a sub-scope is born UNDER it via a STRUCTURAL edge (`<under>`); composition is NESTING and
isolation is the DEFAULT — a fact under a scope is reached only by CROSSING (a data rule). This module owns
the primitive and the read predicate; NOTHING mints `<under>` edges yet (sub-slice 1c does the membership
migration), so on all current data `scope_of` is None everywhere and the visibility filter is a no-op — an
additive, conservative extension (a read over base-only data is unchanged).

THE VISIBILITY RULE (spiked GO, `bench/spike_scope_local_identity.py`; audit Trap A). Identity union
(`chain._canon_class` + the name accelerator) must be SCOPE-LOCAL: from a reading vantage `active`, a node is
visible iff it is in BASE (always visible — base ink is visible from everywhere) OR under `active` itself OR
under an ANCESTOR of `active`. Across a relativizer boundary IDENTITY holds (coreference, a separate query)
but VISIBILITY does not — which is what stops a mention (`John says the lion has a mane`) from leaking into a
BASE read while still letting an in-scope read fuse the reference to its content. The `<under>` edge is
CONTROL (meta-structure, invisible to fact matching); a scope is itself an ordinary node that a relativizer
fact points at (`John —[says]→ [S]`), so nesting is relativizer-facts whose objects are scopes, chained.
"""
from __future__ import annotations

from .attrgraph import AttrGraph

UNDER = "<under>"        # structural membership: node --<under>--> scope (control; a `<…>` token auto-flags)


def put_under(g: AttrGraph, node: str, scope: str) -> None:
    """Place `node` UNDER `scope` (idempotent). The membership edge is the reframe's structural nesting —
    it replaces the single-valued `SCOPE` attr (which is why scopes don't compose today: one attr = one
    scope, where an `<under>` edge per parent = arbitrary nesting)."""
    if scope_of(g, node) == scope:
        return
    g.add_relation(node, UNDER, scope)          # `<under>` is a control token -> the rel node auto-controls


def scope_of(g: AttrGraph, node: str) -> str | None:
    """The scope `node` is directly under (its `<under>` target), or None for a BASE node. One parent per
    node in the tree; a node with no `<under>` edge is base."""
    for rel, obj in g.relations_from(node):
        if g.has_key(rel, UNDER):
            return obj
    return None


def scope_chain(g: AttrGraph, scope: str | None) -> list[str]:
    """`[scope, parent, grandparent, …]` up to base — the vantages a read from `scope` may see (itself and
    every ancestor). Empty for a base vantage (`None`). Cycle-guarded (a scope tree is a DAG-to-root)."""
    out: list[str] = []
    seen: set[str] = set()
    cur = scope
    while cur is not None and cur not in seen:
        seen.add(cur)
        out.append(cur)
        cur = scope_of(g, cur)
    return out


def reframe_active(g: AttrGraph) -> bool:
    """Cheap graph-level flag: does ANY `<under>` edge exist? False on all current data (no membership
    migration yet) -> the visibility filter is skipped entirely, so the read hot path is byte-unchanged."""
    return bool(g.nodes_with_key(UNDER))


def is_visible(g: AttrGraph, node: str, active: str | None) -> bool:
    """Is `node` visible for a read taken from vantage `active` (None = base)? Base nodes always; else only
    from `active` or a descendant of the node's scope (i.e. the node's scope is on `active`'s chain)."""
    ms = scope_of(g, node)
    if ms is None:
        return True                              # base ink is visible from every vantage
    if active is None:
        return False                             # a base read cannot see a scoped node (isolation)
    return ms in scope_chain(g, active)

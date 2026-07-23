"""Fact identity — reconcile a proposition's participant references to their discourse referent.

STEP 1 of the unified-representation arc (docs/design/unified_representation.md §4; the north star is ONE
interned proposition node whose identity is a function of its participants' identities). Increment 1: the
IDENTITY mechanism, wired REACTIVELY, with the `prop:` content-key HANDLE still in place (increment 2 retires
the handle so the relnode IS the proposition; this reconciliation is the load-bearing prerequisite either way).

THE PROBLEM. `that A causes that B` reifies each proposition to a content-key handle whose `subj`/`obj` edges
point at NAME-interned participant nodes. When the LINK is stated BEFORE its antecedent, those participants are
minted as ORPHANS — `chain._canon_class` == {itself}, no `denotes` edge to the grammar fold's later-created
entity — so the reify bridge (`?h subj ?s … ?s ?p ?o`, a NODE-bound join that unions only via the `denotes`
canonical class, the derivation-frame boundary docs/design/derivation_frame.md) cannot see the asserted fact.

THE FIX (increment 1). Reconcile each participant reference to its UNAMBIGUOUS same-name discourse referent —
the same-named nodes that are NOT themselves reference-endpoints and that form ONE `chain._canon_class`
canonical class — by ADDING a parallel `subj`/`obj` handle edge to each referent node. The reify/dereify
bridge then binds the ENTITY directly as `?s`/`?o`, so (a) the reify READ matches the asserted fact on the
entity and (b) the dereify WRITE materializes the derived consequent ONTO the entity — which is the
interpretation scope member, so the conclusion lands IN the interpretation ([[derived-facts-must-land-in-the-interpretation]])
rather than on the out-of-scope orphan. This sidesteps both the one-hop `_canon_class` limit AND the
`ById`-write path (which does NOT follow `denotes`), with no change to the core write path.

Keying to the referent (NOT a brute same-name union) preserves same-name disambiguation by construction: an
AMBIGUOUS referent (two disjoint same-name classes) is REFUSED, left to coref judgment. Additive: the original
orphan edge stays (harmless extra binding); the parallel entity edges are the reconciliation. This is
increment-1 SCAFFOLDING on top of the `prop:` handle — increment 2 retires the handle so the relnode IS the
proposition and this reconciliation collapses into structural fact identity.

REACTIVE, not batch. Fired at the committed-ask gate (`cnl.query.ask_goal`), so a reference reconciles once
its referent has been asserted — the incremental/forward-reference story the reactive core already tells. The
edges are authored as `MINT(dedup)` programs (the vision-true write; idempotent), not a substrate poke.
"""
from __future__ import annotations

from .attrgraph import AttrGraph, graded
from .chain import _canon_class
from .machine import MINT, Machine, State

PROP_HANDLE_REG = "prop_handles"   # kb.registers key: set[str] of proposition-handle node-ids
_MACHINE = Machine()


def register_handles(kb: AttrGraph, node_ids) -> None:
    """Record the proposition-handle node-ids a causation statement minted, so reconciliation is precise
    (only handle references) and ZERO-COST when no causation has occurred (the register stays empty)."""
    kb.registers.setdefault(PROP_HANDLE_REG, set()).update(n for n in node_ids if n is not None)


def _reference_edges(kb: AttrGraph, handles):
    """Yield `(handle, key, target)` for every handle `subj`/`obj` edge — the proposition's participant
    references. `key` is "subj" or "obj"; `target` is the referenced participant node."""
    for h in handles:
        if not kb.has(h):
            continue
        for rel, obj in kb.relations_from(h):
            for key in ("subj", "obj"):
                if kb.has_key(rel, key):
                    yield h, key, obj


def _merge_classes(classes) -> list[set[str]]:
    """Union-find over canonical classes by node-id overlap -> connected components (the ambiguity test:
    more than one component ⇒ the referent is ambiguous)."""
    comps: list[set[str]] = []
    for c in classes:
        hits = [k for k in comps if k & c]
        if not hits:
            comps.append(set(c))
        else:
            first = hits[0]
            first |= c
            for extra in hits[1:]:
                first |= extra
                comps.remove(extra)
    return comps


def reconcile_proposition_refs(kb: AttrGraph) -> int:
    """Add the parallel `subj`/`obj` handle edges that make each proposition participant reference bind its
    unambiguous discourse referent directly. Idempotent (an edge already present is a no-op via `dedup`) and
    zero-cost when no causation handle exists. Returns the number of edges authored."""
    handles = kb.registers.get(PROP_HANDLE_REG)
    if not handles:
        return 0
    ref_edges = list(_reference_edges(kb, handles))
    all_refs = {ep for _h, _k, ep in ref_edges}
    drawn = 0
    for h, key, ep in ref_edges:
        name = kb.name(ep)
        if not name:
            continue
        # discourse referents = same-named nodes that are NOT themselves reference-endpoints
        referents = [n for n in kb.nodes_named(name) if n != ep and n not in all_refs]
        if not referents:
            continue
        classes = _merge_classes([frozenset(_canon_class(kb, r)) for r in referents])
        if len(classes) != 1:
            continue                                       # AMBIGUOUS referent -> refuse (disambiguation)
        target_class = classes[0]
        existing = {o for r, o in kb.relations_from(h) if kb.has_key(r, key)}
        for m in sorted(target_class):
            if m in existing or not kb.has(m):
                continue                                   # idempotent / antecedent-first (already bound)
            _MACHINE.apply(kb, [MINT("_e", attrs={key: graded(1.0)},
                                     in_edges=["_h"], edges=["_m"], dedup=True)],
                           State({"_h": h, "_m": m}))
            drawn += 1
    return drawn

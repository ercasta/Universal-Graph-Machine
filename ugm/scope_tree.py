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

_SCOPE_N = [0]


def scope_name() -> str:
    """A FRESH, UNIQUE name for a scope node (slice 1c). Two properties, both load-bearing, and the old
    `<hypothesis>` name had NEITHER:

      * **not a `<…>` token**, so the node does NOT auto-flag as CONTROL (`attrgraph.py:288`). Scopes must
        be ORDINARY nodes: the reframe relates them with BASE facts (`S causes S'`, `S holds_base yes`)
        and the read guard drops any fact with a control endpoint, so a control scope is one no rule can
        reason about (scope_reframe_audit.md, build finding 1).
      * **unique**, because the demand engine NAME-UNIONS same-named nodes — every scope called
        `<hypothesis>` would fuse into one. A scope's identity is the NODE, never a shared name.

    Scope-ness is carried by the `HYPOTHESIS` marker ATTR (which the GC exemptions already key on), not by
    the name and not by the control flag — kind-as-attribute, the reframe's own principle."""
    _SCOPE_N[0] += 1
    return f"scope_{_SCOPE_N[0]}"


def put_under(g: AttrGraph, node: str, scope: str) -> None:
    """Place `node` UNDER `scope` (idempotent). The membership edge is the reframe's structural nesting —
    it replaces the single-valued `SCOPE` attr (which is why scopes don't compose today: one attr = one
    scope, where an `<under>` edge per parent = arbitrary nesting DEPTH).

    SINGLE PARENT IS AN INVARIANT OF THE CONSTRUCTOR (execution_topology.md §3). Re-placing a node under
    its EXISTING parent is a no-op; placing it under a DIFFERENT one raises. Without this the guard below
    suppressed only the same-parent case, so two `put_under` calls left two `<under>` edges and `scope_of`
    answered by `relations_from` iteration order — an order-dependent, SILENT mis-scoping, and a direct
    violation of the one-parent contract `scope_of`/`scope_chain`/`is_visible` are all written against.
    Multi-parent membership is coherent (an ATMS label) but would make the crossing's merge-back boundary
    ambiguous; the reframe's answer to "holds in two scopes" is a CROSSING (scoped copies + `denotes`),
    never a second membership."""
    cur = scope_of(g, node)
    if cur == scope:
        return                                  # idempotent: already under exactly this scope
    if cur is not None:
        raise ValueError(
            f"put_under: {node!r} is already under scope {cur!r}; refusing to add a second parent "
            f"{scope!r} (single-parent is a scope-tree invariant — cross scopes, do not co-nest)")
    g.add_relation(node, UNDER, scope)          # `<under>` is a control token -> the rel node auto-controls


def _scoped_nodes(g: AttrGraph) -> frozenset[str]:
    """The set of nodes that HAVE an `<under>` edge — version-cached (slice 1c-G, the base fast-path that
    `scope_reframe_audit.md` called 1d).

    WHY THIS EXISTS. Migrating membership onto `<under>` makes `reframe_active` TRUE on any graph holding
    a single scope, which switches `chain._scope_visible` on for EVERY read. Without this set the filter
    called `scope_of` per candidate node, and `scope_of` scans that node's relations looking for an
    `<under>` — an O(degree) probe per node per read, paid overwhelmingly by BASE nodes that have no
    `<under>` edge at all. That is what took the suite from 118s to not finishing.

    The fix is `execution_topology.md` §4d's own prescription one level down: INDEX, do not re-derive.
    Membership is rare and base is the common case, so the answer for a base node must be O(1). Rebuild is
    O(#`<under>` relations) — small, because scoped facts are the exception — and version-keyed exactly
    like `lowering.derived_triples`' snapshot cache, so it is a pure function of the current graph."""
    cached = getattr(g, "_scoped_cache", None)
    if cached is not None and cached[0] == g.version:
        return cached[1]
    out: set[str] = set()
    for rel in g.nodes_with_key(UNDER):
        out.update(g.pred(rel))
    frozen = frozenset(out)
    g._scoped_cache = (g.version, frozen)
    return frozen


def scope_of(g: AttrGraph, node: str) -> str | None:
    """The scope `node` is directly under (its `<under>` target), or None for a BASE node. One parent per
    node in the tree — an invariant ENFORCED by `put_under`, which is what makes returning the first
    `<under>` well-defined rather than iteration-order-dependent. A node with no `<under>` edge is base."""
    if node not in _scoped_nodes(g):
        return None                    # BASE FAST PATH (1c-G): the overwhelmingly common case, now O(1)
    for rel, obj in g.relations_from(node):
        if g.has_key(rel, UNDER):
            return obj
    return None


def members_of(g: AttrGraph, scope: str) -> list[str]:
    """Every node DIRECTLY under `scope` — the scope's contents (slice 1c). The structural replacement for
    reading back the `SCOPE` attr: membership is an `<under>` relation, so the members are the `<under>`
    sources pointing at this scope. Direct members only; a nested sub-scope appears as itself, not
    flattened into its parent's list (composition is NESTING, so a caller wanting the transitive contents
    recurses deliberately rather than getting it by accident).

    NOTE the indirection: `nodes_with_key(UNDER)` yields the `<under>` RELATION nodes, not the members —
    membership is the S-P-O path `member → <under>-rel → scope` ([[spo-directed-path-no-labeled-edges]]),
    so the members are the relation's SUBJECTS."""
    out: list[str] = []
    for rel in g.nodes_with_key(UNDER):
        if scope in g.succ(rel):
            out.extend(g.pred(rel))
    return out


def scoped_ref(g: AttrGraph, base_id: str, scope: str) -> str:
    """The reference to base entity `base_id` AS SEEN FROM `scope` — found or minted (slice 1c).

    The reframe's identity discipline: a scope does not reach out and touch the base entity, it holds its
    OWN reference, `denotes`-linked back. Same NAME (so an in-scope read finds it by name), distinct NODE
    (so an out-of-scope read cannot) — exactly the split `is_visible` enforces: across a relativizer
    boundary IDENTITY holds but VISIBILITY does not. The `denotes` link is CONTROL because it is identity
    META-STRUCTURE, not a fact; drawn ordinary it surfaces in ink (cf. `interpretation.py:104`).

    Lives here rather than in `suppose` because `chain` needs it too (to scope a DERIVED head) and
    `suppose` already imports `chain`."""
    from .vocabulary import DENOTES
    from .attrgraph import NAME, valued
    if scope_of(g, base_id) == scope:
        return base_id          # IDEMPOTENT: an in-scope match already bound this scope's own reference,
                                # so re-wrapping would mint a reference TO a reference — and, because the
                                # derivation re-fires each round, a fresh one every round (the node
                                # explosion this guard was added to stop).
    name = g.name(base_id)
    for n in members_of(g, scope):
        if g.name(n) == name and any(g.has_key(r, DENOTES) and o == base_id
                                     for r, o in g.relations_from(n)):
            return n
    ref = g.add_node({NAME: valued(name)})
    put_under(g, ref, scope)
    g.add_relation(ref, DENOTES, base_id, control=True)
    return ref


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

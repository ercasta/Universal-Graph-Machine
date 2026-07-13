"""
The label-less attribute substrate.

Departure from `harneskills.world_model.Graph` (which gives every node a NAME label):
here a node carries NO label and NO name. A node is an opaque `identity` plus a bundle of
**attributes** drawn from the KB's *closed* key vocabulary. Edges are directed and
**unlabeled**. All discrimination that used to live in node-names and edge-predicates now
lives in `(attributes + directed topology)`. See `decision_labelless_substrate` and
`docs/graph low level machine/rule-isa-design.md` ("The label-less attribute substrate").

An attribute is `(key, value, comparator)` with two poles:

  * GRADED membership  -- `dog: 0.8`.  value in [0, 1]; the comparator is an alpha-cut /
    t-norm / embedding distance. `dog: 1.0` is the crisp corner. This is what FUZZY-MATCH
    and GRADE (graded mode) test.

  * VALUED data        -- `name = "Paul"`, `age = 42`.  value from an OPEN domain; the
    comparator is one of `=`, `<=`, `>=`, `~=`. Once nodes are label-less a literal like
    "Paul" has nowhere to live except as an attribute value, so valued attributes are not
    optional. GUARANTEE (`decision_labelless_substrate`): a value is DATA under a key, never
    a node-identity index. `name="Paul"` is a value-test; two people both named "Paul" stay
    DISTINCT nodes. The matcher must never index a node BY a valued attribute — cross that
    line and the abolished label returns. (`AttrGraph` deliberately offers no
    `node_with_value(...)` lookup for exactly this reason; matching is `nodes_with_key`,
    which returns candidates to be *tested*, not resolved.)

**Closed keys, open values** (Datalog-shaped): the vocabulary of attribute *keys* is closed
(pass `schema=` to enforce it); the *values* of valued attributes are an open domain.

Relations and roles reify uniformly (neo-Davidsonian): an n-ary fact `chase(a, b)` is an
event node `{chase: 1.0}` linked by bare directed edges through role-nodes -- themselves
label-less nodes whose attribute IS the role (`{agent: 1.0}`, `{patient: 1.0}`). Reading is
directional: event -> role-instance -> filler. This substrate does not privilege that shape;
it is produced by MINT at the machine level and read back by ordinary FOLLOW/TEST.
"""
from __future__ import annotations

import itertools
from collections import deque
from dataclasses import dataclass, field

# Attribute kinds.
GRADED = "graded"      # value in [0, 1]; membership degree
VALUED = "valued"      # value from an open domain; data under a key

# Reserved attribute keys for the production substrate (the AttrGraph re-host,
# decision-attrgraph-rehost). A former node NAME lives under the VALUED key `NAME` (the bridge's
# convention); a node CONFIDENCE under the VALUED key `CONF` (absent => the 1.0 default). Every
# OTHER graded attr is an embedding dimension (the gradable layer). These are CONVENTIONS over the
# label-less core, not new node fields: identity stays opaque, values are never an identity index.
NAME = "name"
CONF = "confidence"

# Provenance / withdrawal node names the 2-hop relation reader and locality traversal treat as
# INERT (ported verbatim from world_model so `relations_from`/`within` behave identically during the
# re-host; a later slice moves inertness onto the `control` flag per the audits).
_INERT_NAMES: frozenset[str] = frozenset({"proves", "uses"})


def _is_inert(name: str) -> bool:
    """A provenance/withdrawal node (justification / proves / uses / axiom / quarantine /
    retracted): it hangs off fact relations but is never a real subject/predicate of a domain
    relation. Kept name-string based for drop-in parity with `world_model._is_inert`."""
    return (name in _INERT_NAMES or name.startswith("<j:")
            or name in ("<axiom>", "<quarantine>", "<retracted>"))


@dataclass(frozen=True)
class Attr:
    """One attribute value: a kind tag plus the value. `(key, ...)` lives in the node's dict."""
    kind: str            # GRADED | VALUED
    value: object        # float in [0,1] for GRADED; any scalar for VALUED

    def __post_init__(self) -> None:
        if self.kind == GRADED:
            v = self.value
            if not isinstance(v, (int, float)) or not (0.0 <= float(v) <= 1.0):
                raise ValueError(f"graded attribute value must be in [0,1], got {v!r}")
        elif self.kind != VALUED:
            raise ValueError(f"unknown attribute kind {self.kind!r}")


def graded(value: float) -> Attr:
    return Attr(GRADED, float(value))


def valued(value: object) -> Attr:
    return Attr(VALUED, value)


def intern_node(graph: "AttrGraph", name: str) -> str:
    """Get-or-create by name: reuse the first non-control, non-inert node named `name`, else mint one.
    The SINGLE Python interner — the authoring-boundary twin of the ISA's `MINT(intern=True)` (which
    canonicalizes a name during rule firing). `add_node` is fresh-per-call BY DESIGN — a name is a LABEL,
    not an identity — so this is the CONSUMER's explicit build-time decision to keep one intended entity
    mapped to one node (feedback #8b: retires the hand-rolled `ids.setdefault(x, add_node(x))` cache). It
    is NOT engine coreference: the matcher never follows same-name as identity (that stays coref-as-rules);
    interning is a choice a graph-BUILDER makes, here, at construction time. Control/inert scaffolding of
    the same name is skipped so a write lands on a real entity, never on a `<call>`/provenance node."""
    for n in graph.nodes_named(name):
        if not (graph.is_control(n) or graph.is_inert(n)):
            return n
    return graph.add_node(name)


@dataclass
class AttrNode:
    """A node instance. Identity is `nid` (opaque). `attrs` maps a key to an `Attr`. `control`
    marks the node as belonging to the ephemeral CONTROL layer (walkers, tokens, scaffolding)
    rather than the monotone FACT layer — the only nodes whose touching edges DROP-CTRL may cut
    (vision.md §5).

    `inert` marks a provenance/justification node (`<j:...>`, and a `proves`/`uses` relation
    middle-node) — invisible to ordinary fact matching (`Machine.skip_inert`, `relations_from`,
    `within`, `embedding`), DISTINCT from `control`: a control-relation (e.g. the planner's
    `chosen`) must stay visible to ordinary matching, only provenance bookkeeping is inert. A
    dataclass FIELD, not an `attrs` key — so it can never collide with a domain schema key (a
    KB about buildings could have its own unrelated "inert" attribute). Phase 2.2
    (decision_attrgraph_rehost): supersedes the name-string `_is_inert`/`_INERT_NAMES` check for
    every NODE-INSTANCE call site; `_is_inert` itself stays (rewriter.py's oracle imports it by
    identity), kept in lockstep by tagging `inert=True` at every provenance mint site alongside
    the unchanged name.

    The `name`/`embedding`/`confidence` properties are the production CONVENTION (a former
    name-`Graph` node maps 1:1): they read the reserved `NAME`/`CONF` VALUED attrs and the graded
    attrs, so call-sites doing `graph.node(nid).name` keep working after the substrate swap."""
    nid: str
    attrs: dict[str, Attr] = field(default_factory=dict)
    control: bool = False
    inert: bool = False

    @property
    def id(self) -> str:                                  # former Graph.Node.id
        return self.nid

    @property
    def name(self) -> str:
        a = self.attrs.get(NAME)
        # VALUED only: a relation whose PREDICATE is literally `name` carries a GRADED `{name: 1.0}`
        # key (Phase 2.3) — that is a predicate, not an entity name, so it reports no name.
        return str(a.value) if (a is not None and a.kind == VALUED) else ""

    @property
    def embedding(self) -> dict[str, float]:
        # Phase 2.1: a relation node now also carries its predicate as a GRADED key (`chase: 1.0`),
        # which is the correct neo-Davidsonian unification — BUT a provenance/inert node's predicate
        # key (`proves`/`uses`) must stay invisible here too, matching every other inert-blind view
        # (Machine.skip_inert, relations_from) — an inert node reports no embedding.
        if self.inert:
            return {}
        # Phase 2.2: a control TOKEN carried as a graded key (`<goal>: 1.0`, the name->key dual-write)
        # is NOT a fuzzy embedding dimension — filter reserved `<…>` keys out of this view, the same
        # way an inert node reports none, so similarity/rendering/`propagate` stay token-free.
        return {k: float(a.value) for k, a in self.attrs.items()
                if a.kind == GRADED and k != CONF and not (k.startswith("<") and k.endswith(">"))}

    @property
    def confidence(self) -> float:
        a = self.attrs.get(CONF)
        return float(a.value) if a is not None else 1.0


class AttrGraph:
    """Opaque-identity nodes with closed-key attribute bundles + untyped directed edges.

    `schema` (optional) is the closed set of allowed attribute keys. When given, writing an
    attribute with an off-schema key raises — the "closed keys" half of the contract. Values
    are never constrained (open constants).
    """

    def __init__(self, schema: set[str] | None = None,
                 indexed_keys: set[str] | None = None) -> None:
        self._nodes: dict[str, AttrNode] = {}
        self._out: dict[str, set[str]] = {}
        self._in: dict[str, set[str]] = {}
        # Matching index: key -> {nid}. Indexes by attribute KEY only, never by value —
        # this is the structural guard that keeps valued attributes from resurrecting labels
        # (see module docstring). Seeding is over keys; values are filtered per-candidate.
        self._by_key: dict[str, set[str]] = {}
        # DISCRIMINATING-KEY value-accelerator (Phase 2.3, `docs/name_demotion_design.md`): key ->
        # {value -> {nid}}, maintained for DECLARED keys only. Semantically transparent (vision §11):
        # it returns a CANDIDATE SET to test, NEVER a single node and never a merge, so identity stays
        # opaque — two nodes both named "Paul" are two nids both under "Paul", never resurrecting
        # value-as-identity. The default declared set is `{"name"}` — the production CONVENTION (seed-
        # from-ground anchors entities by name), now expressed through this general facility instead of
        # a hardcoded `if key == NAME`. `name` is thus an ORDINARY declared index, not a privileged one.
        self._indexed_keys: set[str] = {NAME} if indexed_keys is None else set(indexed_keys)
        self._by_value: dict[str, dict[object, set[str]]] = {k: {} for k in self._indexed_keys}
        self._schema = set(schema) if schema is not None else None
        self._counter = itertools.count()
        # Monotonic mutation counter: bumped on every structural change (attr write / edge add /
        # edge remove) that can affect a derived-triple view. `derived_triples` memoizes on it, so
        # the many repeated snapshots the goal solver takes are O(1) once the graph is quiescent
        # (a pure-performance cache — the value is a function of the current graph, version-keyed).
        self._version = 0

    @property
    def version(self) -> int:
        """The mutation version — increments on each structural change. A stable cache key for
        derived views (see `lowering.derived_triples`)."""
        return self._version

    # ------------------------------------------------------------------
    # Nodes
    # ------------------------------------------------------------------

    def add_node(
        self,
        name_or_attrs: str | dict[str, Attr] | None = None,
        *,
        embedding: dict[str, float] | None = None,
        confidence: float = 1.0,
        control: bool = False,
        inert: bool = False,
        nid: str | None = None,
        node_id: str | None = None,
    ) -> str:
        """Create a fresh node with an opaque identity. Returns the identity.

        Two call styles, both supported through the re-host:
          * PRODUCTION (former `Graph.add_node`): a NAME string, optional `embedding`/`confidence`
            -> stored under the reserved NAME/CONF attrs + graded dims.
          * LABEL-LESS (the ISA machine / bridge): an `{key: Attr}` dict of attributes directly.

        Identities are minted deterministically (`n0`, `n1`, ...) so a program's output is
        reproducible without a clock/RNG (the workflow/journal reproducibility constraint);
        pass `nid`/`node_id` only for deserialization / reconstruction. `inert=True` marks a
        provenance/justification node (see `AttrNode.inert`).
        """
        ident = nid or node_id or f"n{next(self._counter)}"
        node = AttrNode(nid=ident, control=control, inert=inert)
        self._nodes[ident] = node
        self._out.setdefault(ident, set())
        self._in.setdefault(ident, set())
        if isinstance(name_or_attrs, dict):
            for key, attr in name_or_attrs.items():
                self.set_attr(ident, key, attr)
        elif name_or_attrs is not None:
            nm = str(name_or_attrs)
            self.set_attr(ident, NAME, valued(nm))
            # Phase 2.2 (control TOKENS as keys): a reserved control token (`<…>` syntax) minted as a
            # NODE also carries its token as a GRADED key — the same name->key dual-write `add_relation`
            # does for control PREDICATES, so `nodes_with_key`/`has_key` can eventually replace the
            # name-based `nodes_named("<token>")` reads (the Phase-6 reader flip). Additive: the legacy
            # VALUED name stays (the oracle bridge), so no current reader changes. `embedding` filters
            # these `<…>` keys back out (see the property) so the fuzzy view stays token-free.
            if nm.startswith("<") and nm.endswith(">"):
                self.set_attr(ident, nm, graded(1.0))
                # Phase 2.2 HALF 2 (control-ness at mint): reserved `<…>` syntax + NOT inert ⟹ CONTROL
                # — the ratified content-blind criterion (`decision-control-ness-criterion`) applied at
                # the mint chokepoint, so every control token is flag-queryable (`is_control`) for the
                # Phase-6 reader flip. Inert provenance (`<j:…>`/`<axiom>`, minted `inert=True`) is
                # EXCLUDED — it is inert, not control. A caller's explicit `control=` still holds (only
                # promotes False->True here, never demotes).
                if not inert:
                    node.control = True
            for dim, v in (embedding or {}).items():
                self.set_attr(ident, dim, graded(v))
            if confidence != 1.0:
                self.set_attr(ident, CONF, valued(float(confidence)))
        return ident

    def has(self, nid: str) -> bool:
        return nid in self._nodes

    def node(self, nid: str) -> AttrNode:
        return self._nodes[nid]

    def nodes(self) -> list[str]:
        return list(self._nodes)

    def is_control(self, nid: str) -> bool:
        return self._nodes[nid].control

    def set_control(self, nid: str, flag: bool = True) -> None:
        """Mark a node CONTROL-layer (or clear it). A control node is invisible to fact
        matching (vision §5) — used to demote ephemeral scaffolding a rule materialized
        (e.g. a recognition NAC completion) so it can never be read as a reasoning fact."""
        self._nodes[nid].control = flag

    def is_inert(self, nid: str) -> bool:
        return self._nodes[nid].inert

    def set_inert(self, nid: str, flag: bool = True) -> None:
        """Mark a node provenance/justification-INERT (or clear it) — see `AttrNode.inert`.
        DISTINCT from `set_control`: an inert node is invisible to ORDINARY fact matching
        (`Machine.skip_inert`), whereas a control node stays matchable (only DROP_CTRL treats it
        differently) — provenance bookkeeping must vanish from reasoning, a control-relation like
        the planner's `chosen` must not."""
        self._nodes[nid].inert = flag

    # ------------------------------------------------------------------
    # Attributes
    # ------------------------------------------------------------------

    def set_attr(self, nid: str, key: str, attr: Attr) -> None:
        """Write `key -> attr` on a node. Off-schema keys raise (closed keys)."""
        if self._schema is not None and key not in self._schema:
            raise KeyError(f"attribute key {key!r} not in closed schema {sorted(self._schema)}")
        node = self._nodes[nid]
        if key in self._indexed_keys:                     # keep the value-accelerator in sync
            old = node.attrs.get(key)
            # remove the stale value-index entry when the VALUED value changes OR the attr becomes GRADED
            # (a GRADED key under an indexed name — e.g. a `name`-predicate rel node — is never value-
            # indexed; only VALUED data is a discriminating value).
            if old is not None and old.kind == VALUED and (attr.kind != VALUED or old.value != attr.value):
                bucket = self._by_value[key].get(old.value)
                if bucket is not None:
                    bucket.discard(nid)
                    if not bucket:
                        del self._by_value[key][old.value]
            if attr.kind == VALUED:
                self._by_value[key].setdefault(attr.value, set()).add(nid)
        if key not in node.attrs:
            self._by_key.setdefault(key, set()).add(nid)
        node.attrs[key] = attr
        self._version += 1

    def declare_index(self, key: str) -> None:
        """Declare `key` a DISCRIMINATING value-index — the KB-declared value-accelerator (Phase 2.3).
        Idempotent; back-fills existing nodes carrying a VALUED `key`. Candidates only (`nodes_with_value`
        never resolves), so declaring an index never resurrects value-as-identity."""
        if key in self._indexed_keys:
            return
        self._indexed_keys.add(key)
        idx = self._by_value.setdefault(key, {})
        for nid in self._by_key.get(key, ()):
            a = self._nodes[nid].attrs.get(key)
            if a is not None and a.kind == VALUED:
                idx.setdefault(a.value, set()).add(nid)

    def nodes_with_value(self, key: str, value: object) -> list[str]:
        """Candidate nodes whose DECLARED discriminating key `key` has VALUED `value` — O(1) via the
        value-accelerator. A CANDIDATE SET (many nodes may share a value), never a resolution to THE
        node (identity stays opaque). `[]` for an undeclared key (declare it via `declare_index`)."""
        return list(self._by_value.get(key, {}).get(value, ()))

    def value_count(self, key: str, value: object) -> int:
        """Document frequency of `key = value` (how many nodes carry it), O(1) — the selectivity the
        matcher seeds from without materializing the candidate list (seed-from-ground, §11/§14)."""
        return len(self._by_value.get(key, {}).get(value, ()))

    def predicate(self, nid: str) -> str:
        """A RELATION node's predicate: its single domain GRADED key (non-reserved — not a `<…>` control
        token — and not `confidence`). The Phase-2.3 replacement for reading a relation's predicate via
        the (now-retired) VALUED `name` bridge. Returns `""` if the node carries no domain graded key
        (i.e. it is not a relation). Relies on the mint-time invariant that a rel node carries exactly
        one domain graded key = its predicate (`add_relation` / `lower_rhs`)."""
        for k, a in self._nodes[nid].attrs.items():
            if a.kind == GRADED and k != CONF and not (k.startswith("<") and k.endswith(">")):
                return k
        return ""

    def raise_graded(self, nid: str, key: str, degree: float) -> None:
        """Monotone raise of a GRADED attribute: `key` becomes max(old, degree). The monotone
        FACT-layer write — a degree only ever goes UP, never down (vision.md §5). New keys
        start from the given degree."""
        node = self._nodes[nid]
        cur = node.attrs.get(key)
        old = float(cur.value) if (cur is not None and cur.kind == GRADED) else 0.0
        self.set_attr(nid, key, Attr(GRADED, max(old, float(degree))))

    def get_attr(self, nid: str, key: str) -> Attr | None:
        return self._nodes[nid].attrs.get(key)

    def has_key(self, nid: str, key: str) -> bool:
        return key in self._nodes[nid].attrs

    def nodes_with_key(self, key: str) -> list[str]:
        """Candidate nodes that carry attribute `key` — O(1) via the key index. This is the
        ONLY index; there is deliberately no lookup by VALUE (see module docstring)."""
        return list(self._by_key.get(key, ()))

    def key_count(self, key: str) -> int:
        """Document frequency of `key` — how many nodes carry it. The df selectivity SEED uses
        to pick the rarest anchor, computed WITHOUT materializing the candidate list."""
        return len(self._by_key.get(key, ()))

    # ------------------------------------------------------------------
    # Edges (untyped, directed)
    # ------------------------------------------------------------------

    def add_edge(self, a: str, b: str) -> None:
        self._out.setdefault(a, set()).add(b)
        self._in.setdefault(b, set()).add(a)
        self._version += 1

    def remove_edge(self, a: str, b: str) -> None:
        self._out.get(a, set()).discard(b)
        self._in.get(b, set()).discard(a)
        self._version += 1

    def has_edge(self, a: str, b: str) -> bool:
        return b in self._out.get(a, ())

    def succ(self, nid: str) -> set[str]:
        """Successors (out-edges). Returns a copy — safe to mutate the graph while iterating."""
        return set(self._out.get(nid, ()))

    def pred(self, nid: str) -> set[str]:
        """Predecessors (in-edges). Returns a copy."""
        return set(self._in.get(nid, ()))

    def edges(self) -> list[tuple[str, str]]:
        return [(a, b) for a, bs in self._out.items() for b in bs]

    def edge_is_fact(self, a: str, b: str) -> bool:
        """A fact edge connects two FACT-layer nodes. An edge is CONTROL if EITHER endpoint is
        a control node. This is what makes fact-edge deletion unrepresentable: DROP-CTRL
        consults this and refuses a fact edge (machine.py)."""
        return not (self._nodes[a].control or self._nodes[b].control)

    # ------------------------------------------------------------------
    # Production substrate API (the re-host: former `world_model.Graph` surface, as CONVENTIONS
    # over the label-less core). decision-attrgraph-rehost.
    # ------------------------------------------------------------------

    def name(self, nid: str) -> str:
        """The node's NAME (the reserved VALUED `name` attr), or "" if unnamed. A relation node whose
        PREDICATE is literally `name` carries a GRADED `{name: 1.0}` key (Phase 2.3), NOT a VALUED name,
        so it reports "" here — read its predicate via `predicate(nid)`."""
        a = self._nodes[nid].attrs.get(NAME)
        return str(a.value) if (a is not None and a.kind == VALUED) else ""

    def nodes_named(self, name: str) -> list[str]:
        """All node ids whose NAME is `name` — a thin wrapper over the general value-accelerator for the
        `name` discriminating key (declared by the production convention). A CANDIDATE SET (many nodes
        may share a name), never a resolution to THE node (identity stays opaque)."""
        return self.nodes_with_value(NAME, name)

    def name_count(self, name: str) -> int:
        """Document frequency of NAME `name` (how many nodes wear it), O(1) — the selectivity the
        matcher seeds from without materializing the candidate list (seed-from-ground, §11/§14)."""
        return self.value_count(NAME, name)

    def remove_node(self, nid: str) -> None:
        """Remove a node and every edge touching it, keeping the key/name indices in sync.
        (Operational — the ENGINE only ever cuts CONTROL nodes/edges; §5 fact-edge immutability is
        an effect-layer invariant, not enforced by withholding this store primitive.)"""
        for t in list(self._out.get(nid, ())):
            self.remove_edge(nid, t)
        for f in list(self._in.get(nid, ())):
            self.remove_edge(f, nid)
        node = self._nodes.pop(nid, None)
        if node is not None:
            for key, a in node.attrs.items():
                bucket = self._by_key.get(key)
                if bucket is not None:
                    bucket.discard(nid)
                if key in self._indexed_keys and a.kind == VALUED:   # value-accelerator cleanup
                    vb = self._by_value.get(key, {}).get(a.value)
                    if vb is not None:
                        vb.discard(nid)
                        if not vb:
                            del self._by_value[key][a.value]
        self._out.pop(nid, None)
        self._in.pop(nid, None)
        self._version += 1

    def out(self, nid: str) -> set[str]:
        """Successors as a COPY (former `Graph.out`); alias of `succ`."""
        return set(self._out.get(nid, ()))

    def into(self, nid: str) -> set[str]:
        """Predecessors as a COPY (former `Graph.into`); alias of `pred`."""
        return set(self._in.get(nid, ()))

    def add_relation(self, subject_id: str, rel_name: str, object_id: str,
                     *, confidence: float = 1.0, control: bool = False, inert: bool = False) -> str:
        """Wire  subject -> [rel node] -> object  via a fresh relation node carrying `rel_name` (the
        2-hop reification the matcher walks). Returns the rel node id. Same shape the bridge
        `to_attrgraph` produces and `derived_triples` reads. `control=True` marks the REL node
        control-layer — for ephemeral scaffolding (the surface `next`/`first` token chain) whose
        edges a control rule may rewrite (`DROP_CTRL` permits a control edge, refuses a fact one).

        Phase 2.1/2.3 (decision_attrgraph_rehost, "predicates become graded keys"): the predicate is
        the GRADED key `rel_name: 1.0` on the rel node — the SOLE representation the ISA engine seeds/
        tests/reads through (`nodes_with_key`/`key_count`/`has_key`/`predicate`). The legacy VALUED
        `name` dual-write (the retired `TEMPORARY BRIDGE`) is GONE (Phase 2.3, `name_demotion_design.md`):
        a rel node carries only its predicate key, never a VALUED name. A predicate literally named
        `name` is now sound — it is the GRADED key `{name: 1.0}`, distinct in KIND from an entity's
        VALUED `{name: "Paul"}`, so the old reserved-key-collision special case is gone too.

        `inert=True` marks the REL node provenance-INERT (see `AttrNode.inert`) — for `proves`/
        `uses` justification relations, invisible to ordinary fact matching.

        CONTROL-NESS AT MINT (Phase 2.2, preserved through the 2.3 dict-mint): a relation whose
        PREDICATE is a reserved `<…>` control token (e.g. a `<goal> -[<next>]-> …` scaffolding edge) is
        control-flagged automatically — the same content-blind criterion `add_node` applies to a `<…>`
        NODE. The dict form of `add_node` does NOT auto-flag (only the string-name form did), so it is
        applied here explicitly; inert provenance is excluded (inert, not control)."""
        is_ctrl_token = rel_name.startswith("<") and rel_name.endswith(">") and not inert
        rid = self.add_node({rel_name: graded(1.0)}, control=control or is_ctrl_token, inert=inert)
        if confidence != 1.0:
            self.set_attr(rid, CONF, valued(float(confidence)))
        self.add_edge(subject_id, rid)
        self.add_edge(rid, object_id)
        return rid

    def relations_from(self, subject_id: str) -> list[tuple[str, str]]:
        """(rel_node_id, object_id) pairs reachable as 2-hop paths from `subject_id`, skipping
        provenance-inert subjects/middles (so readers see only domain relations)."""
        result: list[tuple[str, str]] = []
        if self._nodes[subject_id].inert:
            return result
        for rid in self._out.get(subject_id, ()):
            if self._nodes[rid].inert:
                continue
            for oid in self._out.get(rid, ()):
                result.append((rid, oid))
        return result

    def set_embedding(self, nid: str, embedding: dict[str, float]) -> None:
        """Replace the node's embedding: each dim -> a GRADED attr. Clears prior graded dims."""
        for key in [k for k, a in list(self._nodes[nid].attrs.items())
                    if a.kind == GRADED and k != CONF]:
            del self._nodes[nid].attrs[key]
            b = self._by_key.get(key)
            if b is not None:
                b.discard(nid)
        for dim, v in embedding.items():
            self.set_attr(nid, dim, Attr(GRADED, float(v)))

    def get_embedding(self, nid: str) -> dict[str, float]:
        return dict(self._nodes[nid].embedding)

    def set_confidence(self, nid: str, confidence: float) -> None:
        self.set_attr(nid, CONF, valued(float(confidence)))

    def get_confidence(self, nid: str) -> float:
        return self._nodes[nid].confidence

    def within(self, seeds: list[str], radius: int) -> set[str]:
        """All nodes within `radius` undirected hops of any seed (inclusive), skipping
        provenance-inert nodes. A general graph utility (no longer the matching scope)."""
        frontier = {s for s in seeds if s in self._nodes}
        seen = set(frontier)
        q: deque[tuple[str, int]] = deque((s, 0) for s in frontier)
        while q:
            nid, d = q.popleft()
            if d >= radius:
                continue
            for nb in self._out.get(nid, set()) | self._in.get(nid, set()):
                if nb in seen or (nb in self._nodes and self._nodes[nb].inert):
                    continue
                seen.add(nb)
                q.append((nb, d + 1))
        return seen

    def gc_disconnected(self) -> list[str]:
        """Remove nodes with no edges at all. Operational only (§5), never a step of reasoning."""
        dead = [nid for nid in self._nodes
                if not self._out.get(nid) and not self._in.get(nid)]
        for nid in dead:
            self.remove_node(nid)
        return dead

    def copy(self) -> "AttrGraph":
        """Deep copy (used when applying a rewrite to a trial graph)."""
        g = type(self)(schema=set(self._schema) if self._schema is not None else None,
                       indexed_keys=set(self._indexed_keys))
        maxn = -1
        for nid, n in self._nodes.items():
            g._nodes[nid] = AttrNode(nid=nid, attrs=dict(n.attrs), control=n.control, inert=n.inert)
            g._out[nid] = set(self._out.get(nid, ()))
            g._in[nid] = set(self._in.get(nid, ()))
            for key, a in n.attrs.items():
                g._by_key.setdefault(key, set()).add(nid)
                if key in g._indexed_keys and a.kind == VALUED:
                    g._by_value[key].setdefault(a.value, set()).add(nid)
            if nid.startswith("n") and nid[1:].isdigit():
                maxn = max(maxn, int(nid[1:]))
        g._counter = itertools.count(maxn + 1)
        g._version = self._version
        return g

    def absorb(self, other: "AttrGraph") -> dict[str, str]:
        """Merge every node and edge of `other` into `self` under FRESH identities; return the id map
        (other-nid -> self-nid). Attributes (incl. the reserved NAME/CONF/graded dims) and the control
        flag are preserved. Label-less discipline: NO node is merged BY NAME — two same-named nodes stay
        two (coreference is the additive `same_as` step, NOT this). Used to commit an ISOLATED per-
        sentence recognition into the accumulating KB, so two sentences' surface residue can never cross-
        bind (the fresh recognition graph is a pragmatic external SCOPE; the pure form is a `<scope>`/
        `<sentence>` node the rules match within — decision-attrgraph-rehost, recognition on the ISA)."""
        idmap: dict[str, str] = {}
        for nid, n in other._nodes.items():
            idmap[nid] = self.add_node(dict(n.attrs), control=n.control)
        for a, b in other.edges():
            self.add_edge(idmap[a], idmap[b])
        return idmap

    def to_dict(self) -> dict:
        def enc(a: Attr) -> dict:
            return {"kind": a.kind, "value": a.value}
        return {
            "nodes": [
                {"id": n.nid, "control": n.control,
                 "attrs": {k: enc(a) for k, a in n.attrs.items()}}
                for n in self._nodes.values()
            ],
            "edges": sorted(self.edges()),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AttrGraph":
        g = cls()
        for nd in data.get("nodes", []):
            attrs = {k: Attr(a["kind"], a["value"]) for k, a in nd.get("attrs", {}).items()}
            g.add_node(attrs, control=nd.get("control", False), nid=nd["id"])
        for a, b in data.get("edges", []):
            g.add_edge(a, b)
        return g

    def __len__(self) -> int:
        return len(self._nodes)

    def __repr__(self) -> str:
        return f"AttrGraph(nodes={len(self._nodes)}, edges={len(self.edges())})"

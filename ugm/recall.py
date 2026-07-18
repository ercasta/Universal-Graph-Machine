"""
Associative recall — "what else is like this?" — over the substrate's OWN sparse embeddings.

THE EMBEDDING IS ALREADY THERE — BUT NOT WHERE IT FIRST LOOKS. A node's graded attribute bundle
(`AttrNode.embedding`) is a sparse vector, and it was tempting to stop there. Measurement says
otherwise (bench/recall_autofire.py): across the corpus, ENTITY nodes carry no graded attrs at all
— the 400-odd graded carriers in a typical bank are the reified RELATION nodes, each holding its
own predicate. `vanilla` and `chocolate` have empty attribute vectors and are, on that view,
similar to nothing.

Their similarity is RELATIONAL: both stand in `is` to `in_stock`. So a concept's vector here is its
PROFILE — the (predicate, object) pairs it participates in, `is:in_stock`, `is_a:shop` — unioned
with whatever graded qualities it does carry directly (a hedged `risky: 0.8` from the graded write
rules). Both halves are things somebody asserted in the rules' own vocabulary, so recall still
needs no imported concept table and no opaque coordinates, and a hit can still say *why* it is a
hit (`Hit.shared`) in words the author would recognise.

EXACT, NOT APPROXIMATE. Candidates are gathered through the by-key inverted index, one scan per
probe dimension. A node sharing NO dimension with the probe has cosine 0 by construction, so
skipping it loses nothing — this enumerates strictly less than the graph while returning exactly
the same ranked set a full scan would. Cost tracks the probe's own dimensions and their
selectivity, not |graph| (ugm-scope-session-sized).

RECALL PROPOSES, IT NEVER CONCLUDES. Nothing here writes to the graph. A hit is a CANDIDATE for
the demand-driven chain to verify with rules, carrying a similarity in [0, 1] that the machine
folds into `State.score` through the t-norm — so an associatively-reached conclusion arrives
already wearing a band, and the possibilistic layer renders it as the assumption it is rather
than as an asserted fact.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from .attrgraph import AttrGraph


# Surface scaffolding that is NOT conceptual content. `next` is the CNL token chain (word order in
# the utterance): two nodes are not alike for having been said next to the same word. Reserved
# `<…>` objects (the `<mention>` marker) are excluded for the same reason the `embedding` view
# excludes reserved keys — scaffolding is not a dimension.
SURFACE_PREDICATES = frozenset({"next"})


@dataclass(frozen=True)
class Hit:
    """One recalled candidate: the node, its similarity to the probe, and the dimensions that
    earned it. `shared` is the explanation — "near because both are `person` and both `angry`" —
    ordered by each dimension's contribution to the dot product, strongest first."""
    nid: str
    score: float
    shared: tuple[str, ...]


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    """Sparse cosine over two embedding views. Zero when either side is empty (an unembedded node
    is not 'maximally similar to everything' — it is simply not recallable)."""
    if not a or not b:
        return 0.0
    dot = sum(v * b[k] for k, v in a.items() if k in b)
    if dot <= 0.0:
        return 0.0
    na = sqrt(sum(v * v for v in a.values()))
    nb = sqrt(sum(v * v for v in b.values()))
    if na <= 0.0 or nb <= 0.0:
        return 0.0
    return min(1.0, dot / (na * nb))       # clamp: float error must never exceed a degree's [0,1]


def _is_scaffolding(name: str) -> bool:
    return name.startswith("<") and name.endswith(">")


def profile(g: AttrGraph, nid: str) -> dict[str, float]:
    """A node's sparse concept vector: its own graded qualities, plus one `pred:object` dimension
    per outgoing relation it participates in. The relational half is what carries the signal on
    CNL-authored banks, where entities hold no graded attrs of their own (see module docstring).

    Dimension weight is the relation's own graded degree, so a hedged relation contributes
    proportionally rather than as a hard 1.0. Scaffolding — surface token chains, `<mention>`
    markers, control/inert relation nodes — contributes nothing."""
    if not g.has(nid) or g.is_control(nid) or g.is_inert(nid):
        return {}
    dims = dict(g.get_embedding(nid))
    for rel_id, obj_id in g.relations_from(nid):
        if g.is_control(rel_id) or g.is_inert(rel_id):
            continue
        pred = g.predicate(rel_id)
        if not pred or pred in SURFACE_PREDICATES or _is_scaffolding(pred):
            continue
        obj = g.name(obj_id)
        if not obj or _is_scaffolding(obj):
            continue
        degree = g.get_embedding(rel_id).get(pred, 1.0)
        key = f"{pred}:{obj}"
        dims[key] = max(dims.get(key, 0.0), float(degree))
    return dims


def _candidates(g: AttrGraph, dims: dict[str, float], probe: str) -> list[str]:
    """Nodes sharing at least one dimension with the probe, in INSERTION ORDER (dict-as-set, the
    substrate's determinism discipline — a recall must not depend on hash seed). The probe itself
    is excluded: self-similarity is 1.0 and would crowd out every real neighbour in a top-k.

    Attribute dims go through the by-key inverted index; a relational dim `pred:object` reaches its
    co-participants by walking IN-edges from the shared object — the same 'enumerate strictly less
    than the graph, lose nothing' bound, since a node sharing no dimension has cosine 0 anyway."""
    seen: dict[str, None] = {}

    def take(nid: str) -> None:
        if nid != probe:
            seen.setdefault(nid, None)

    for dim in dims:
        if ":" in dim:
            _, _, obj = dim.partition(":")
            for onid in g.nodes_named(obj):            # co-participants: who else points here
                for rel_id in g.pred(onid):
                    for subj in g.pred(rel_id):
                        take(subj)
        else:
            for nid in g.nodes_with_key(dim):
                take(nid)
    return list(seen)


def near(g: AttrGraph, probe: str, *, threshold: float = 0.0,
         top_k: int | None = None) -> list[Hit]:
    """The recall primitive: candidates similar to `probe`, ranked by similarity descending.

    `threshold` is a floor on similarity (0.0 admits every candidate sharing a dimension);
    `top_k` truncates AFTER ranking. Control and provenance-inert nodes are never recalled —
    scaffolding is not a concept (`AttrNode.embedding` already reports {} for inert, and the
    control guard matches every other fact-facing view). Ties break by insertion order, so the
    result is bit-for-bit reproducible across runs.
    """
    if not g.has(probe):
        return []
    dims = profile(g, probe)
    if not dims:
        return []
    hits: list[Hit] = []
    for nid in _candidates(g, dims, probe):
        if g.is_control(nid) or g.is_inert(nid):
            continue
        other = profile(g, nid)
        s = cosine(dims, other)
        if s <= 0.0 or s < threshold:
            continue
        shared = sorted((k for k in dims if k in other),
                        key=lambda k: (-(dims[k] * other[k]), k))
        hits.append(Hit(nid, s, tuple(shared)))
    hits.sort(key=lambda h: -h.score)      # stable: insertion order survives as the tie-break
    return hits[:top_k] if top_k is not None else hits

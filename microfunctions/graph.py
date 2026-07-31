"""THE SUBSTRATE — mutable nodes, named edges, ordered targets, references, and an undo journal.

**Mutable, deliberately.** The first version of this module was persistent (copy-on-write), which cost
O(size) per write to buy one thing: hypothesis-by-running (`north_star.md` §4 — run a microfunction against
a scratch graph, read the answer, discard). Copying the world to ask a question is the wrong trade, and it
is not how anything that handles volume does it.

**What replaces it: an undo journal.** Every mutation records how to reverse itself. `savepoint()` returns
a marker; `rollback(sp)` reverses back to it. This is what a database does, and it is strictly better than
copy-on-write for the purpose — cost is O(changes made), not O(size of graph), so a cheap hypothesis is
cheap even in a large graph. §4's capability is preserved with its economics inverted:

    sp = g.savepoint()
    run_the_microfunction(g)          # freely mutate
    answer = read_something(g)
    g.rollback(sp)                    # pencil erased, exactly

**Three representational commitments.**

*Named edges with ordered targets.* A label maps to an ordered LIST of targets: a single-valued relation is
length 1, a 1:N relation (`list --item--> a, b, c`) is longer, and index addressing is a list index.

*Edge properties.* What role nodes used to buy — saying something ABOUT a connection — without charging a
node per connection. Keyed by `(src, label, index)`, and shifted whenever an insert or removal moves the
edges they describe.

*References.* A node attribute may hold a `Ref` to another node. This is distinct from an edge, and the
distinction is worth keeping sharp: an **edge** is a relation, part of what the graph asserts; a
**reference** is a stored pointer, the graph's equivalent of a variable holding an address. A focus head
saved for later, or one node naming another as data, is a reference — not a claim that the two are related.

**The reverse index** (`inc`) is maintained incrementally, which mutability makes practical. It is keyed by
`(src, label)` WITHOUT the index, deliberately: keeping indices in a reverse index means every insert
rewrites unrelated entries, which is the kind of bookkeeping that is quietly wrong for a long time. The
index within a label is recovered by looking in that label's short list.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import count

_ids = count(1)


@dataclass(frozen=True)
class Ref:
    """A stored pointer to a node, held as an attribute value. Not an edge — see the module docstring."""
    node: str

    def __repr__(self) -> str:
        return f"&{self.node}"


class Graph:
    __slots__ = ("attrs", "out", "inc", "bykind", "eprops", "_journal", "_recording")

    def __init__(self) -> None:
        self.attrs: dict[str, dict] = {}
        self.out: dict[tuple, list] = {}       # (src, label) -> [dst, …] ordered
        self.inc: dict[str, set] = {}          # dst -> {(src, label), …}
        self.bykind: dict[str, dict] = {}      # kind -> {node: None} in mint order — see `of_kind`
        self.eprops: dict[tuple, dict] = {}    # (src, label, index) -> {k: v}
        self._journal: list = []
        self._recording = True

    # --- journal ------------------------------------------------------------------------------------
    def savepoint(self) -> int:
        """A marker to roll back to. Cheap: an integer."""
        return len(self._journal)

    def rollback(self, sp: int) -> None:
        """Undo every mutation made since `sp`, in reverse order."""
        was, self._recording = self._recording, False
        try:
            while len(self._journal) > sp:
                self._journal.pop()()
        finally:
            self._recording = was

    def _undo(self, fn) -> None:
        if self._recording:
            self._journal.append(fn)

    def commit(self) -> None:
        """Forget the undo history — nothing before this can be rolled back. Bounds journal growth for a
        long-running process that has decided its past is settled."""
        self._journal.clear()

    # --- reading ------------------------------------------------------------------------------------
    def attr(self, node: str, key: str, default=None):
        return self.attrs.get(node, {}).get(key, default)

    def kind(self, node: str):
        return self.attrs.get(node, {}).get("kind")

    def targets(self, src: str, label: str) -> tuple:
        return tuple(self.out.get((src, label), ()))

    def target(self, src: str, label: str):
        t = self.out.get((src, label))
        return t[0] if t else None

    def at(self, src: str, label: str, index: int):
        t = self.out.get((src, label), ())
        return t[index] if -len(t) <= index < len(t) else None

    def count(self, src: str, label: str) -> int:
        return len(self.out.get((src, label), ()))

    def labels(self, src: str) -> tuple:
        return tuple(sorted(lbl for (s, lbl) in self.out if s == src))

    def edge_prop(self, src: str, label: str, index: int, key: str, default=None):
        return self.eprops.get((src, label, index), {}).get(key, default)

    def sources(self, dst: str, label: str | None = None) -> tuple:
        """Who points at `dst` — O(1) via the maintained reverse index. This is what `BACK` needs, and
        the reason it is worth maintaining `inc` at all."""
        return tuple(sorted(s for (s, lbl) in self.inc.get(dst, ())
                            if label is None or lbl == label))

    def deref(self, node: str, key: str):
        """Follow a stored reference. Returns `None` if the attribute is absent or is not a `Ref` —
        dereferencing a non-reference is a caller's mistake, reported as nothing rather than as a
        plausible-looking value."""
        v = self.attr(node, key)
        return v.node if isinstance(v, Ref) else None

    @property
    def nodes(self) -> tuple:
        return tuple(self.attrs)

    def of_kind(self, kind: str) -> tuple:
        """Every node of `kind`, in mint order — O(#that kind), maintained by `mint` and `drop`.

        **⭐ This is the same shape as `inc`, and legitimate for the same reason: the SUBSTRATE maintains
        it, so it cannot drift.** It is not a rule asserting a claim about a node — the only way to acquire
        a kind is to be minted with one, and `put` refuses to change it. Contrast `types.tag`, which stamps
        `is_a` and *is* a claim, and so has to be re-validated on every read.

        Why it exists: `types.find_type` and `function.find` scanned `g.nodes` — materialising a tuple of
        every node in the graph — on **every** lookup, and `violations` reaches `find_type` about four
        times per call (itself, plus `schema_of` and `attrs_of`, plus one per `base` hop). Measured on one
        `driver.proposals` enumeration over a world holding 200 nodes that can bind to nothing: 21,525
        `find_type` calls and 21,575 `g.nodes` tuple builds. That is why inert world content cost 57× the
        enumeration time while yielding *zero* extra proposals — the cost was never in testing candidates,
        it was in looking up the type by name once per test."""
        return tuple(self.bykind.get(kind, ()))

    # --- writing (in place, journalled) -------------------------------------------------------------
    def mint(self, kind: str, **attrs) -> str:
        node = f"{kind}#{next(_ids)}"
        self.attrs[node] = {"kind": kind, **attrs}
        self.bykind.setdefault(kind, {})[node] = None

        def undo():
            self.attrs.pop(node, None)
            self.bykind.get(kind, {}).pop(node, None)
        self._undo(undo)
        return node

    def put(self, node: str, **attrs) -> str:
        # ⚠ `kind` is set once, at mint, and `of_kind` indexes on it. Letting `put` change it would make
        # the index drift silently — the defect class this codebase keeps re-finding. Nothing does it
        # (`_copy_set` already excludes `kind` explicitly, calling it "positional"), so this refuses rather
        # than maintaining machinery for a case that should not exist.
        if "kind" in attrs and attrs["kind"] != self.attrs.get(node, {}).get("kind"):
            raise ValueError(
                f"kind is fixed at mint and indexed by `of_kind`; cannot put kind={attrs['kind']!r} "
                f"on {node}. Mint a new node instead.")
        existing = self.attrs.setdefault(node, {})
        before = {k: existing.get(k, _MISSING) for k in attrs}

        def undo():
            for k, v in before.items():
                if v is _MISSING:
                    existing.pop(k, None)
                else:
                    existing[k] = v
        existing.update(attrs)
        self._undo(undo)
        return node

    def set_ref(self, node: str, key: str, target: str) -> None:
        """Store a pointer to `target` as an attribute. See the module docstring on refs vs edges."""
        self.put(node, **{key: Ref(target)})

    def link(self, src: str, label: str, dst: str, **props) -> None:
        tgts = self.out.setdefault((src, label), [])
        index = len(tgts)
        tgts.append(dst)
        self.inc.setdefault(dst, set()).add((src, label))
        if props:
            self.eprops[(src, label, index)] = dict(props)

        def undo():
            tgts.pop()
            self.eprops.pop((src, label, index), None)
            if not tgts:
                self.out.pop((src, label), None)
            if dst not in tgts:
                self.inc.get(dst, set()).discard((src, label))
        self._undo(undo)

    def link_at(self, src: str, label: str, index: int, dst: str, **props) -> None:
        """Insert, shifting later edges — and their properties — right."""
        tgts = self.out.setdefault((src, label), [])
        index = max(0, min(index, len(tgts)))
        before_props = self._label_props(src, label)
        tgts.insert(index, dst)
        self.inc.setdefault(dst, set()).add((src, label))
        self._reindex(src, label, before_props, shift_from=index, delta=+1, new=(index, props))

        def undo():
            tgts.pop(index)
            self._restore_props(src, label, before_props)
            if not tgts:
                self.out.pop((src, label), None)
            if dst not in tgts:
                self.inc.get(dst, set()).discard((src, label))
        self._undo(undo)

    def unlink(self, src: str, label: str, *, index: int | None = None, dst: str | None = None) -> None:
        tgts = self.out.get((src, label))
        if not tgts:
            return
        if index is None:
            if dst is None or dst not in tgts:
                return
            index = tgts.index(dst)
        if not (0 <= index < len(tgts)):
            return
        removed = tgts[index]
        before_props = self._label_props(src, label)
        tgts.pop(index)
        self._reindex(src, label, before_props, shift_from=index, delta=-1, drop=index)
        if removed not in tgts:
            self.inc.get(removed, set()).discard((src, label))
        empty = not tgts
        if empty:
            self.out.pop((src, label), None)

        def undo():
            self.out.setdefault((src, label), tgts).insert(index, removed)
            self.inc.setdefault(removed, set()).add((src, label))
            self._restore_props(src, label, before_props)
        self._undo(undo)

    def drop(self, node: str) -> None:
        """Remove a node and everything touching it. Journalled like anything else, so a hypothesis that
        deletes is still reversible."""
        for (s, lbl) in tuple(self.inc.get(node, ())):
            while node in self.out.get((s, lbl), ()):
                self.unlink(s, lbl, dst=node)
        for lbl in self.labels(node):
            for d in self.targets(node, lbl):
                self.inc.get(d, set()).discard((node, lbl))
            saved = self.out.pop((node, lbl))
            self._undo(lambda lbl=lbl, saved=saved: self.out.__setitem__((node, lbl), saved))
        attrs = self.attrs.pop(node, None)
        if attrs is not None:
            kind = attrs.get("kind")
            self.bykind.get(kind, {}).pop(node, None)

            def undo():
                self.attrs[node] = attrs
                if kind is not None:
                    self.bykind.setdefault(kind, {})[node] = None
            self._undo(undo)

    # --- edge-property index maintenance ------------------------------------------------------------
    def _label_props(self, src, label) -> dict:
        return {k: dict(v) for k, v in self.eprops.items() if k[0] == src and k[1] == label}

    def _restore_props(self, src, label, saved: dict) -> None:
        for k in [k for k in self.eprops if k[0] == src and k[1] == label]:
            del self.eprops[k]
        self.eprops.update(saved)

    def _reindex(self, src, label, before, *, shift_from, delta, new=None, drop=None) -> None:
        for k in [k for k in self.eprops if k[0] == src and k[1] == label]:
            del self.eprops[k]
        for (s, lbl, i), v in before.items():
            if drop is not None and i == drop:
                continue
            self.eprops[(s, lbl, i + delta if i >= shift_from else i)] = v
        if new is not None and new[1]:
            self.eprops[(src, label, new[0])] = dict(new[1])


class _Missing:
    pass


_MISSING = _Missing()


def new_graph() -> Graph:
    """A fresh graph with its `root` already present — the node every focus starts from."""
    g = Graph()
    g.attrs["root"] = {"kind": "root"}
    return g


__all__ = ["Graph", "Ref", "new_graph"]

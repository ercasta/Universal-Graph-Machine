"""FOCUS — the set of current pointers into the graph, and the control mechanism that replaces matching.

`north_star.md` §5c left a load-bearing residue: with matching demoted to type validation, nothing decides
what happens next. Under matching, dispatch was automatic and wrong; under microfunctions, nothing happens
unless something chooses a function *and* an argument. **Focus is that choice, made explicit and made
addressable.**

**The model.** A focus is a set of named **heads**, each a pointer at one node. Every graph starts with
`root`, and every head starts there or is derived from another head. A microfunction is invoked on heads,
not on "whatever matches" — which is precisely why wrong firing is structurally impossible rather than
merely unlikely.

**Navigation is the whole vocabulary.** A head moves *forward* along a named edge (optionally by index,
since targets are ordered), *backward* through an incoming edge (O(1), on the maintained reverse index),
or *through a reference* stored as an attribute. Heads fork, so exploring two candidates is two heads
rather than a copied world, and heads close when a line of inquiry is done.

**Why heads are named rather than positional.** A named head can be handed to a microfunction as an
argument, stored in the graph as a `Ref` and picked up later, and — the reason that matters — *recorded*:
"this operation was applied to this head" is the application node from `graph_data_model.md` §6.3, and the
episode machinery built on it works unchanged.

**A move that fails does not raise.** It empties the head, and `has(name)` reports it. A failed navigation
is an ordinary answer to an ordinary question ("is there a body?"), not an exception — the same reasoning
that makes an out-of-range index `None` rather than an error.
"""
from __future__ import annotations

from .graph import Graph


class Focus:
    """Named pointers into one graph. Cheap to copy, cheap to fork, and holds no graph state itself."""

    __slots__ = ("_heads",)

    def __init__(self, heads: dict[str, str] | None = None) -> None:
        self._heads: dict[str, str | None] = dict(heads or {})

    # --- opening and closing ------------------------------------------------------------------------
    def open(self, name: str, node: str = "root") -> "Focus":
        self._heads[name] = node
        return self

    def fork(self, new_name: str, existing: str) -> "Focus":
        """Two candidates become two heads — the alternative to copying the world to explore both."""
        self._heads[new_name] = self._heads.get(existing)
        return self

    def close(self, name: str) -> "Focus":
        self._heads.pop(name, None)
        return self

    # --- reading ------------------------------------------------------------------------------------
    def at(self, name: str):
        return self._heads.get(name)

    def has(self, name: str) -> bool:
        """A head exists AND points somewhere. An emptied head is not the same as a closed one."""
        return self._heads.get(name) is not None

    @property
    def names(self) -> tuple:
        return tuple(sorted(self._heads))

    def snapshot(self) -> dict:
        return dict(self._heads)

    def restore(self, snap: dict) -> "Focus":
        self._heads = dict(snap)
        return self

    # --- navigation ---------------------------------------------------------------------------------
    def move(self, g: Graph, name: str, label: str, index: int = 0) -> "Focus":
        """Forward along a named edge. `index` addresses the ordered 1:N case."""
        here = self._heads.get(name)
        self._heads[name] = None if here is None else g.at(here, label, index)
        return self

    def back(self, g: Graph, name: str, label: str | None = None, index: int = 0) -> "Focus":
        """Backward through an incoming edge — O(1) on the reverse index. `label=None` means any."""
        here = self._heads.get(name)
        if here is None:
            self._heads[name] = None
            return self
        srcs = g.sources(here, label)
        self._heads[name] = srcs[index] if -len(srcs) <= index < len(srcs) else None
        return self

    def follow_ref(self, g: Graph, name: str, key: str) -> "Focus":
        """Through a stored reference rather than an edge — dereferencing a pointer held as data."""
        here = self._heads.get(name)
        self._heads[name] = None if here is None else g.deref(here, key)
        return self

    def spread(self, g: Graph, name: str, label: str, prefix: str | None = None) -> tuple:
        """Fan out: one head per target under `label`, named `prefix0…prefixN`. Returns the new names.

        This is the closest thing here to what matching did — but bounded, explicit, and rooted at a node
        the caller already chose, rather than a scan over the whole graph."""
        here = self._heads.get(name)
        if here is None:
            return ()
        prefix = prefix or f"{name}_"
        made = []
        for i, t in enumerate(g.targets(here, label)):
            self._heads[f"{prefix}{i}"] = t
            made.append(f"{prefix}{i}")
        return tuple(made)

    def __repr__(self) -> str:
        return "Focus(" + ", ".join(f"{k}->{v}" for k, v in sorted(self._heads.items())) + ")"


__all__ = ["Focus"]

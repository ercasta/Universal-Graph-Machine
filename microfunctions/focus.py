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

## ⭐⭐ The heads are GRAPH DATA, and that is the correction made on 2026-08-01

This class used to hold a Python `dict[str, str]` and its docstring said, approvingly, that it "holds no
graph state itself". That was the defect, not the feature. `thread.py` exists because *attention was not
data* — a deliberate shift of attention had to be recordable — and it materialised the shifts while leaving
**the pointers themselves** in a Python object that was fresh per call and discarded. HANDOFF §6b's
inventory names it: focus is as much interpreter state as `pc` and the registers, and it is easy to miss
because `Focus` looks like a helper rather than a loop variable.

So a focus is a node, a head is a node, and where a head points is an edge:

```
focus ──head──▶ head(name="c") ──at──▶ car#7
```

⚠ **An emptied head is not a closed one**, and the two must stay distinguishable — `move` off the end of
the world leaves the head node with no `at` edge, while `close` removes the head node altogether. That
distinction predates this change and is what `has` versus `names` reports; storing heads as edges preserves
it exactly, because "a node with no outgoing edge" and "no node" are different states of the graph.

⚠ **Direction invariant** (`planning_workbench.md` §2): a head points **at** the node it is on, and nothing
in the world points back at a head. A focus is metadata about a computation, like an application or a
mapping, and it does not hang off `root` — so `workbench.reachable` never copies one.
"""
from __future__ import annotations

from .graph import Graph

KINDS = ("focus", "head")


class Focus:
    """Named pointers into one graph, **stored in that graph**. Cheap to fork; readable by the system."""

    __slots__ = ("g", "node")

    def __init__(self, g: Graph, node: str | None = None, heads: dict[str, str] | None = None) -> None:
        self.g = g
        self.node = node if node is not None else g.mint("focus")
        for name, at in (heads or {}).items():
            self._point(name, at)

    # --- the head nodes -----------------------------------------------------------------------------
    def head(self, name: str, make: bool = False):
        """The head node called `name`, or `None`. `make=True` mints it, pointing nowhere."""
        for h in self.g.targets(self.node, "head"):
            if self.g.attr(h, "name") == name:
                return h
        if not make:
            return None
        h = self.g.mint("head", name=name)
        self.g.link(self.node, "head", h)
        return h

    def _point(self, name: str, at: str | None) -> None:
        """Where a head points is ONE edge, replaced rather than appended — a head is a pointer, not a
        collection, and letting `at` grow would make `Focus.at` silently answer with a stale first target."""
        h = self.head(name, make=True)
        while self.g.count(h, "at"):
            self.g.unlink(h, "at", index=0)
        if at is not None:
            self.g.link(h, "at", at)

    # --- opening and closing ------------------------------------------------------------------------
    def open(self, name: str, node: str = "root") -> "Focus":
        self._point(name, node)
        return self

    def fork(self, new_name: str, existing: str) -> "Focus":
        """Two candidates become two heads — the alternative to copying the world to explore both."""
        self._point(new_name, self.at(existing))
        return self

    def close(self, name: str) -> "Focus":
        h = self.head(name)
        if h is not None:
            self.g.unlink(self.node, "head", dst=h)
            self.g.drop(h)
        return self

    # --- reading ------------------------------------------------------------------------------------
    def at(self, name: str):
        h = self.head(name)
        return None if h is None else self.g.target(h, "at")

    def has(self, name: str) -> bool:
        """A head exists AND points somewhere. An emptied head is not the same as a closed one."""
        return self.at(name) is not None

    @property
    def names(self) -> tuple:
        return tuple(sorted(self.g.attr(h, "name") for h in self.g.targets(self.node, "head")))

    def snapshot(self) -> dict:
        return {self.g.attr(h, "name"): self.g.target(h, "at")
                for h in self.g.targets(self.node, "head")}

    def restore(self, snap: dict) -> "Focus":
        for name in self.names:
            self.close(name)
        for name, at in snap.items():
            self._point(name, at)
        return self

    # --- navigation ---------------------------------------------------------------------------------
    def move(self, g: Graph, name: str, label: str, index: int = 0) -> "Focus":
        """Forward along a named edge. `index` addresses the ordered 1:N case."""
        here = self.at(name)
        self._point(name, None if here is None else g.at(here, label, index))
        return self

    def back(self, g: Graph, name: str, label: str | None = None, index: int = 0) -> "Focus":
        """Backward through an incoming edge — O(1) on the reverse index. `label=None` means any."""
        here = self.at(name)
        if here is None:
            self._point(name, None)
            return self
        srcs = g.sources(here, label)
        self._point(name, srcs[index] if -len(srcs) <= index < len(srcs) else None)
        return self

    def follow_ref(self, g: Graph, name: str, key: str) -> "Focus":
        """Through a stored reference rather than an edge — dereferencing a pointer held as data."""
        here = self.at(name)
        self._point(name, None if here is None else g.deref(here, key))
        return self

    def spread(self, g: Graph, name: str, label: str, prefix: str | None = None) -> tuple:
        """Fan out: one head per target under `label`, named `prefix0…prefixN`. Returns the new names.

        This is the closest thing here to what matching did — but bounded, explicit, and rooted at a node
        the caller already chose, rather than a scan over the whole graph."""
        here = self.at(name)
        if here is None:
            return ()
        prefix = prefix or f"{name}_"
        made = []
        for i, t in enumerate(g.targets(here, label)):
            self._point(f"{prefix}{i}", t)
            made.append(f"{prefix}{i}")
        return tuple(made)

    def __repr__(self) -> str:
        return "Focus(" + ", ".join(f"{k}->{v}" for k, v in sorted(self.snapshot().items())) + ")"


__all__ = ["Focus", "KINDS"]

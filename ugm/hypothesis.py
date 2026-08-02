"""HYPOTHESIS — an ordinary node, with ordinary subgraphs under it. No special mechanism.

**The decision this module implements, stated plainly:** a hypothesis is a *node*. If entertaining it needs
a different version of something, it *builds* that version as an ordinary subgraph and hangs it off the
hypothesis. If it needs to remember what a value used to be, it writes an explicit backup. There is no
scope, no relativization, no pencil/ink layer, no supposition primitive — none of the machinery the old
substrate spent years on.

**⚠ The undo journal in `graph.py` is NOT the hypothesis mechanism, and conflating them would be a
mistake.** The journal is transactional: it exists so a program that raises halfway leaves no half-written
graph. Its unit is "a run that failed," and its lifetime is one call. A hypothesis outlives any call,
must be inspectable while it exists, must be comparable against a sibling hypothesis, and must be able to
reach a verdict a rule can read. Those are different jobs. Rollback cannot represent "two rival hypotheses
side by side"; two nodes can.

**Why this is better than the mechanism it replaces**, beyond being smaller:

* **Two hypotheses coexist.** The old supposition machinery entertained one assumption at a time and
  discarded it; comparing candidate plans meant re-running. Here rival hypotheses are two nodes, both
  present, both readable, and choosing between them is an ordinary comparison — which is exactly what
  §5c's selection residue needs.
* **⭐ The verdict is a fact.** `docs/concepts.md` recorded a real gap: a supposition's verdict came
  back as a Python value and the scope was retired, so no rule could ever react to "that hypothesis was
  refuted." Here the verdict is an attribute on a node that persists. **That gap closes for free** — not
  by being fixed, but by not being reintroduced.
* **Nothing leaks, because nothing was ever global.** Old suppositions needed a tunnel discipline to stop
  hypothetical conclusions escaping into real belief. A hypothesis's subgraph is only reachable by
  navigating into it, so "leaking" would require a microfunction to deliberately walk there and copy
  something out. Isolation is a consequence of addressing, not a mechanism.

**The cost, stated honestly.** Nothing is shared implicitly. If a hypothesis needs an altered copy of a
large structure, something must build that copy — there is no free relativized view. For the agentic cases
this project cares about (a handful of candidate plans, a counterfactual about one value) that is cheap and
explicit. For a hypothesis that perturbs a large subgraph it is real work, and the honest answer is to
build only what differs and reference the rest.
"""
from __future__ import annotations

from .focus import Focus
from .graph import Graph

OPEN, CONFIRMED, REFUTED, ABANDONED = "open", "confirmed", "refuted", "abandoned"


def open_hypothesis(g: Graph, label: str, *, about=None, parent=None) -> str:
    """Mint a hypothesis node. `about` is what it concerns; `parent` nests it under another hypothesis —
    ordinary edges, so hypotheses nest to any depth with nothing added."""
    h = g.mint("hypothesis", label=label, status=OPEN)
    if about is not None:
        g.link(h, "about", about)
    if parent is not None:
        g.link(parent, "sub", h)
    return h


def assume(g: Graph, h: str, claim) -> str:
    """Record an assumption. The claim is an ordinary node; nothing about it is marked hypothetical,
    because what makes it hypothetical is *where it hangs*, not a flag on it."""
    g.link(h, "assumes", claim)
    return claim


def variant(g: Graph, h: str, original: str, **attrs) -> str:
    """Build the hypothesis's own version of `original` — a real node, in the hypothesis's subgraph.

    Copies attributes and outgoing edges shallowly, then applies overrides. Shallow is deliberate: a deep
    copy would quietly duplicate the world, which is the cost this design is trying to keep visible and
    opt-in. Anything the variant does not override still points at the shared original structure."""
    carried = {**g.attrs.get(original, {}), **attrs}
    carried.pop("kind", None)               # `kind` is the positional argument, not a carried attribute
    v = g.mint(g.kind(original) or "node", **carried)
    g.put(v, variant_of=original)
    for label in g.labels(original):
        for t in g.targets(original, label):
            g.link(v, label, t)
    g.link(h, "variant", v)
    return v


def backup(g: Graph, h: str, node: str, key: str) -> str:
    """An EXPLICIT record of a value before the hypothesis touched it — the user's "explicit backups."

    A node, not a hidden shadow copy, so it is inspectable, explainable, and restorable by anything that
    can navigate to it."""
    b = g.mint("backup", key=key, value=g.attr(node, key))
    g.link(b, "of", node)
    g.link(h, "backup", b)
    return b


def restore(g: Graph, h: str) -> int:
    """Put every backed-up value back. Returns how many were restored — an ordinary operation over
    ordinary nodes, which is the whole point."""
    n = 0
    for b in g.targets(h, "backup"):
        target = g.target(b, "of")
        if target is not None:
            g.put(target, **{g.attr(b, "key"): g.attr(b, "value")})
            n += 1
    return n


def conclude(g: Graph, h: str, verdict: str, *, because=None) -> str:
    """Settle a hypothesis. THE verdict-as-a-fact that `docs/concepts.md` found missing."""
    g.put(h, status=verdict)
    if because is not None:
        g.link(h, "because", because)
    return h


def status(g: Graph, h: str) -> str:
    return g.attr(h, "status")


def rivals(g: Graph, about: str) -> tuple:
    """Every hypothesis concerning `about` — O(1) via the reverse index. Rival hypotheses coexisting is
    the capability the old one-at-a-time supposition machinery could not offer."""
    return tuple(s for s in g.sources(about, "about") if g.kind(s) == "hypothesis")


def enter(g: Graph, focus: Focus, h: str, name: str = "hyp") -> Focus:
    """Point a focus head at a hypothesis. 'Reasoning inside' a hypothesis is navigating into it — there
    is no mode to enter and no scope to be in."""
    return focus.open(name, h)


def discard(g: Graph, h: str) -> None:
    """Drop a hypothesis and everything built only for it. Ordinary deletion; nothing to unwind, because
    nothing was ever entangled with real belief."""
    for label in ("variant", "backup", "sub"):
        for t in g.targets(h, label):
            if label == "sub":
                discard(g, t)
            else:
                g.drop(t)
    g.drop(h)


__all__ = ["OPEN", "CONFIRMED", "REFUTED", "ABANDONED", "open_hypothesis", "assume", "variant",
           "backup", "restore", "conclude", "status", "rivals", "enter", "discard"]

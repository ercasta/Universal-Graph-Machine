"""DISPATCH — the one place an effect leaves the graph, and the checkpoint that guards it.

`north_star.md` §5/§5b probed this before any of it was built, and the probe produced two rules that are
implemented here rather than re-derived:

**1. Check at APPLY time, not MINT time.** A pending call is inert data until the dispatcher reaches it,
so a prohibition recorded *after* the call was planned still counts. This is what recovers the
order-independence that ambient rule matching used to give for free, and checking when the call was
created would lose it — verified, not assumed.

**2. A rollback boundary must never span a dispatch.** The undo journal makes a failed program leave no
half-written graph, but nothing reaches an effect that has already left. So the graph is **committed
before** the handler runs. Past that point the journal is worthless, and pretending otherwise would be
worse than not having it.

**One choke point, deliberately.** Every effect goes through `service`, so one check covers every tool
that will ever be registered — including ones written by code that has never heard of prohibitions. The
probe tested exactly that: a call minted by a deliberately ignorant function was still blocked. A check
each caller is supposed to remember is not the same guarantee.

**A veto is ordinary data.** A `forbidden` node pointing at a target blocks any dispatch naming it. The
dispatcher knows one reserved name and never interprets a value — the same single bit of content-awareness
every VM-level mechanism in this project has carried.
"""
from __future__ import annotations

from .graph import Graph

_TOOLS: dict = {}
VETO = "forbidden"


class Vetoed(Exception):
    """A dispatch refused by a standing prohibition. Loud, and carrying the node that blocked it."""


def register(name: str, handler) -> None:
    """Register a tool. `handler(graph, target) -> value`."""
    _TOOLS[name] = handler


def registered() -> tuple:
    return tuple(sorted(_TOOLS))


def forbid(g: Graph, target: str, reason: str = "") -> str:
    """Record a standing prohibition — ordinary data, effective whenever it is written."""
    f = g.mint(VETO, reason=reason)
    g.link(f, "on", target)
    return f


def veto_reason(g: Graph, target):
    """The prohibition blocking `target`, or `None`. O(1) via the reverse index."""
    if target is None:
        return None
    for src in g.sources(target, "on"):
        if g.kind(src) == VETO:
            return src
    return None


class Imagined(Exception):
    """A dispatch attempted on something that only exists inside a workbench. Planning may not act."""


def _in_workbench(g: Graph, node) -> bool:
    """Derived, not labelled: a node is a workbench copy exactly when a mapping points at it as `image`."""
    return node is not None and any(g.kind(m) == "mapping" for m in g.sources(node, "image"))


def service(g: Graph, tool: str, target, *, record_on=None):
    """THE choke point. Refuse imagined targets, check the veto, commit, then run the handler.

    Returns the handler's value. Raises `Imagined` if the target is inside a workbench, `Vetoed` if a
    standing prohibition names it, or `KeyError` if the tool is unregistered — all before anything leaves
    the graph.

    **⚠ The workbench refusal is the single most important safety property in the design.** Planning runs
    real functions on a copy, and a function that dispatches would reach the real world from inside an
    imagination. The alternative — "remember to substitute mocks when planning" — is the same class of
    mistake as "remember to check the prohibition in each rule", which was already shown to fail. One check
    here makes planning *structurally incapable* of real effects rather than merely disciplined about
    them, and it covers every tool that will ever be registered, including ones written by code that has
    never heard of workbenches.

    It is checked **before** the veto deliberately: an imagined target's prohibitions are imagined too, so
    consulting them first would be answering with made-up evidence."""
    if _in_workbench(g, target):
        raise Imagined(f"refusing to dispatch {tool!r} on {target}: it exists only inside a workbench")
    blocked = veto_reason(g, target)
    if blocked is not None:
        if record_on is not None:
            g.put(record_on, dispatched=False, blocked_by=g.attr(blocked, "reason") or True)
        raise Vetoed(f"dispatch of {tool!r} on {target} blocked by {blocked}")
    if tool not in _TOOLS:
        raise KeyError(f"no tool named {tool!r}; registered: {registered()}")
    # ⚠ Commit BEFORE the effect leaves. Nothing after this line is undoable.
    g.commit()
    value = _TOOLS[tool](g, target)
    if record_on is not None:
        g.put(record_on, dispatched=True)
    return value


__all__ = ["VETO", "Vetoed", "register", "registered", "forbid", "veto_reason", "service"]

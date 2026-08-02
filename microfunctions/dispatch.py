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
_OBSERVES: set = set()
VETO = "forbidden"


class Vetoed(Exception):
    """A dispatch refused by a standing prohibition. Loud, and carrying the node that blocked it."""


def register(name: str, handler, *, observes: bool = False) -> None:
    """Register a tool. `handler(graph, target) -> value`.

    **⭐ `observes=True` says this tool only LOOKS.** HANDOFF §6b named the absence of this as a concrete
    gap: `register` took any callable, and the veto and commit machinery treated a directory scan and a
    sent email identically. `loop.verb_of` needs the distinction to tell **look** from **act**, and those
    are not peers — one costs time and the other cannot be taken back.

    ⚠ **Declared, not inferred, and it defaults to the SAFE answer.** Nothing about a Python callable says
    whether it changes the world, so this is a claim its author makes; an unmarked tool counts as changing
    it, because being wrong that way costs an unnecessary pause and being wrong the other way spends an
    irreversible act the caller meant to withhold.

    ⚠ It is **not** a permission and does not weaken anything: `service` still commits before every
    handler, observing or not, because reading the world is also a moment after which the journal is a lie
    about what could be undone."""
    _TOOLS[name] = handler
    (_OBSERVES.add if observes else _OBSERVES.discard)(name)


def observes(_g=None, name: str | None = None) -> bool:
    """Was this tool registered as only looking? Unknown tools answer `False` — see `register`.

    ⚠ The unused graph parameter is there because every other reader in the engine takes one and callers
    reach for it; it is not consulted, since this is a fact about the *registration*, not about the graph."""
    tool = name if name is not None else _g
    return tool in _OBSERVES


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


def service(g: Graph, tool: str, target, *, record_on=None, remember=None):
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
    # ⭐⭐ THE ONE PLACE THE WORLD CROSSES, so the one place a SIGHTING can be recorded. `service` is
    # already "the ONE way an effect leaves the graph"; it is equally the only way information enters, and
    # that symmetry is what makes memory need no second checkpoint.
    #
    # ⚠ Snapshot BEFORE the commit, because the commit is what destroys the ability to say what preceded
    # this. `commit()` stays exactly as it is — it answers *"can I reverse this?"*, and once the effect has
    # left, the honest answer is no. What it must not also answer is *"can I remember what preceded it?"*,
    # which is a different question. The snapshot is the two being separated.
    before = dict(g.attrs.get(target, {})) if target is not None else {}
    thread = _thread_of(g, record_on)
    existing = set(g.nodes)
    # ⚠ Commit BEFORE the effect leaves. Nothing after this line is undoable.
    g.commit()
    value = _TOOLS[tool](g, target)
    # ⭐⭐ WHAT THIS ACTION PRODUCED, computed here and not a moment later, so nothing minted by the
    # bookkeeping below can be mistaken for something the world handed us.
    produced = tuple(n for n in g.nodes if n not in existing)
    if record_on is not None:
        g.put(record_on, dispatched=True)

    # ⭐⭐⭐ **ONE ACTION, ONE MOMENT — INCLUDING WHAT THE ACTION BROUGHT INTO BEING.** The user's
    # specification, 2026-08-02: *"I don't expect each business rule to handle timestamping manually; and
    # it is not that each node gets a different timestamp — when listing files in a folder, the entire
    # list of files should get the same timestamp, because it corresponds to a single action."*
    #
    # Both halves of that were already true of what was covered, and the gap was **scope** rather than
    # mechanism (`docs/microfunctions/probe_woven_time.py`): a look at a folder recorded three sightings
    # sharing one moment, and the three file nodes it minted had **no moment at all**. So the moment is
    # minted once, here, and given to both the sightings and the products.
    #
    # ⚠⚠ **DATING IS NOT ENCODING, and conflating them would overturn a decision that was made on
    # purpose.** `record_sighting` deliberately encodes only the slots of *the thing being looked at* —
    # *"everything else the tool happened to touch is the walk to school, not encoded, and that is the
    # correct outcome rather than a loss."* That is about **attention**, and it stands. This is
    # **provenance**: `clock.py` opens with *"everything observed or acted must have an absolute
    # timestamp"*, and a node the world just handed us with no time on it cannot be aged, compared, or
    # told from one that has always been there. Nothing is encoded as observed here; things are dated.
    from . import clock as C
    when = C.now(g) if (produced or (thread is not None and target is not None)) else None
    if thread is not None and target is not None:
        from . import memory as M
        M.record_sighting(g, thread, target, before, source=tool, keep=remember, when=when)
    if produced:
        C.stamp(g, when, *produced)
    return value


def _thread_of(g: Graph, entry):
    """The thread an entry sits on — **derived**, never passed. A thread appends with an ordered `step`
    edge, so the reverse index already answers this; threading a `thread=` parameter down through the
    dispatch surface would be plumbing for something the graph already knows."""
    if entry is None:
        return None
    holders = [s for s in g.sources(entry, "step") if g.attr(s, "thread")]
    return holders[0] if len(holders) == 1 else None


__all__ = ["VETO", "Vetoed", "register", "registered", "observes", "forbid", "veto_reason",
           "service"]

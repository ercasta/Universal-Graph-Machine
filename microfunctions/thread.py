"""THREAD — materialised, navigable short-term memory: what the system just did.

Design: `docs/microfunctions/thread_and_system1.md` §1. This is the first piece of the outer loop, which
this engine has been missing since it started: `plan.py` chains, `workbench.py` imagines, `execution.py`
replays and `selection.py` ranks, and nothing invokes any of them.

**Why this exists at all.** `Focus` is a Python object whose own docstring says it "holds no graph state
itself" — created fresh per call and discarded. So attention is the one thing in this system that is *not*
homoiconic, which is a strange hole in a project whose claim is that a rule can reason about a rule. A
system that cannot reason about where it has been looking cannot explain itself, cannot notice it is going
in circles, and cannot learn from how it moved. The thread is that record, as ordinary graph data.

**A thread IS an episode, extended — not a second record.** `application.py` already mints a node per
application and holds them on an ordered `step` edge. If the thread kept its own parallel log there would be
two records of one event and every reflective microfunction would have to consult both, which is exactly the
split the composability principle warns about. So a thread is an episode that also accepts *attention
shifts*, and `application.steps` filters back to applications so `compile_episode` is unaffected.

**Two entry kinds, and deliberately only two.**

* an **attention shift** — attention was deliberately placed somewhere;
* an **application** — a microfunction was applied. The entry *is* the `application` node.

⚠ **Not every instruction.** `Focus.move` runs inside every microfunction body; logging those would record
ISA-level pointer arithmetic rather than reasoning, and would swamp every walker. The grain is *deliberate
placement*. Nothing here instruments `Focus`, on purpose.

**Order is the ordered `step` edge; `prev` is for navigation and for carrying the reason.** These are not
two orderings — appending is one function (`_append`) and nothing else appends, which is a discipline a
human must follow and therefore earns a test. `prev` exists for two reasons the container edge cannot
serve: stepping back from an entry is O(1) rather than an index lookup, and **the reason a step followed
another is a property of the transition**, so it rides on the `prev` edge as an edge property.

⚠ **A `prev` edge property cannot be pointed at.** `eprops` is keyed by `(src, label, index)` and reindexes
on insertion, so there is no stable address for one. Anything something else must point *at* — a disputed
connection, a conflict between two moments — is a node (`connect`). The rule: *ride on the edge what merely
describes it; mint a node for what must be pointed at.*

**⚠ The thread does not hang off `root`, and that is load-bearing.** "Real things hang off root" is what
makes `types.instances` safe by traversal, and it is what will separate the world region from the
scaffolding region when System 1 explores. A thread hanging off root would put every remembered moment into
the candidate set for ordinary reasoning. It points *at* the world and is never pointed at by it — the
metadata direction invariant, the same one that keeps workbench copies bounded.

**Walking needs no new primitive.** `prev`, `step` and `at` are ordinary edges, so `MOVE`, `BACK` and
`FOLLOW` already navigate them: a thread-walking microfunction is an ordinary microfunction pointed at the
thread. That is the claim this module would rather demonstrate than assert, and `selftest.py` walks a thread
from stored ISA to prove it.
"""
from __future__ import annotations

from . import application as ap
from .graph import Graph

#: ⚠ **Still two, and an attempt to add a third was withdrawn.** `discourse.py` first made an *utterance*
#: an entry kind of its own. The correction was that an utterance is a **world event** — it has a speaker,
#: other agents may quote it, and a rule may reason about it — so it hangs off `root` like anything real,
#: and what belongs on the thread is the ordinary *attention* the system paid it. Retraction still needs
#: utterances and applications in **one order**, and it has that, because an attention entry sits in the
#: same `step` edge as everything else. The two-kind restriction turned out to be right.
ENTRY_KINDS = frozenset({"attention", "application"})


# --- opening ----------------------------------------------------------------------------------------
def open_thread(g: Graph, label: str = "thread", *, at: str = "root") -> str:
    """A fresh thread with one entry, attending `root` — the system starts knowing only where it is.

    An episode in every respect that matters, so everything in `application.py` reads it unchanged."""
    t = g.mint("episode", label=label, thread=True)
    _append(g, t, g.mint("attention", note="start"), None)
    g.link(tip(g, t), "at", at)
    return t


# --- appending --------------------------------------------------------------------------------------
def _append(g: Graph, thread: str, entry: str, why: str | None) -> str:
    """⚠ THE ONLY PLACE ANYTHING IS APPENDED. The ordered `step` edge and the `prev` chain must agree, and
    they agree because one function writes both. That is a discipline a human must follow, so it earns
    `check_the_two_orderings_cannot_disagree` rather than being left to good intentions."""
    last = tip(g, thread)
    g.link(thread, "step", entry)
    if last is not None:
        g.link(entry, "prev", last, **({"why": why} if why else {}))
    return entry


def attend(g: Graph, thread: str, node: str, *, why: str | None = None, note: str | None = None) -> str:
    """Record that attention was deliberately placed on `node`. Returns the entry.

    `why` describes the *transition* and rides on the `prev` edge; `note` describes this moment and sits on
    the entry. They are different questions and conflating them loses the one that matters for walking."""
    entry = g.mint("attention", **({"note": note} if note else {}))
    _append(g, thread, entry, why)
    g.link(entry, "at", node)
    return entry


def applied(g: Graph, thread: str, name: str, bindings: dict, *,
            why: str | None = None, outcome=None, for_goal: str | None = None,
            done: bool = False) -> str:
    """Record that a microfunction was applied. The entry **is** the `application` node.

    `application.record` is called without `episode=` precisely so the `step` edge is written once, here —
    letting it link too would produce the duplicate ordering this module exists to avoid."""
    app = ap.record(g, name, bindings, outcome=outcome)
    if done:
        # ⚠ IMAGINED versus DONE. The driver records every proposal it considers, most of them from
        # branches it abandons — so "what was done for this goal" is not "what appears on the thread for
        # this goal". Anything reasoning about consequences (`conflict.py`) must look only at what really
        # ran, or it is analysing the search rather than the actions.
        g.put(app, done=True)
    if for_goal is not None:
        # What this was done *for*. Two applications writing one slot are a deliberate sequel when they
        # serve the same goal and interference when they do not (`conflict.py`), and nothing else in the
        # record distinguishes those.
        g.link(app, "for_goal", for_goal)
    return _append(g, thread, app, why)


# --- reading ----------------------------------------------------------------------------------------
def entries(g: Graph, thread: str) -> tuple:
    """Every entry in order — attention shifts and applications together, which is the whole point of one
    record rather than two."""
    return g.targets(thread, "step")


def tip(g: Graph, thread: str):
    """Where we are now: the last entry. O(1) — the ordered edge already answers it, so no `tip` pointer
    is stored. A stored one would be a second thing to keep true."""
    return g.at(thread, "step", -1)


def previous(g: Graph, entry: str):
    """One step back — O(1) along `prev`."""
    return g.target(entry, "prev")


def following(g: Graph, entry: str):
    """One step forward — O(1) on the maintained reverse index, which is why `prev` alone is stored.
    Storing `next` too would be asserting what the structure already entails."""
    nxt = [s for s in g.sources(entry, "prev") if g.kind(s) in ENTRY_KINDS]
    return nxt[0] if nxt else None


def why(g: Graph, entry: str):
    """Why this entry followed its predecessor — an edge property of the transition, not of either end."""
    return g.edge_prop(entry, "prev", 0, "why")


def attended(g: Graph, entry: str):
    """The node an attention shift was placed on, or `None` for an application entry."""
    return g.target(entry, "at")


def concerns(g: Graph, entry: str) -> tuple:
    """Every world node this entry is about — what it attended, or what an application was bound to.

    The uniform question a walker asks, so it does not have to branch on entry kind at every step."""
    if g.kind(entry) == "application":
        return tuple(n for n in ap.bindings_of(g, entry).values() if n is not None)
    at = attended(g, entry)
    return (at,) if at is not None else ()


def past(g: Graph, entry: str, limit: int | None = None) -> tuple:
    """This entry and everything before it, most recent first. `limit` bounds how far back we care —
    short-term memory is short on purpose, and an unbounded walk is rarely the question."""
    out, cur = [], entry
    while cur is not None and (limit is None or len(out) < limit):
        out.append(cur)
        cur = previous(g, cur)
    return tuple(out)


def find_back(g: Graph, entry: str, predicate, *, limit: int | None = None):
    """The most recent entry at or before `entry` satisfying `predicate`, or `None`.

    This is the shape almost every reflective question takes — "when did I last touch this?", "what goal was
    I pursuing?" — and it is a plain backward walk because the thread is a plain linked structure."""
    for e in past(g, entry, limit):
        if predicate(g, e):
            return e
    return None


def last_touching(g: Graph, entry: str, node: str, *, limit: int | None = None):
    """The most recent entry concerning `node`. The commonest `find_back`, named because it is the one
    System 1 and conflict detection will both reach for."""
    return find_back(g, entry, lambda gr, e: node in concerns(gr, e), limit=limit)


# --- connecting distant points ----------------------------------------------------------------------
def connect(g: Graph, a: str, b: str, relation: str, *, note: str | None = None) -> str:
    """⭐ Tie two moments together — the capability the flat episode never had.

    Episodes are ordered but flat: nothing could say "this step is here *because of* that goal forty steps
    back". That missing structure is what makes reflective microfunctions writable, and it is the real
    blocker behind the recorded conflict-detection regression — which was said to need "no new mechanism,
    only writing them", slightly optimistically: it needed the record to be *addressable*.

    **A connection is a node, not an edge property**, because something else must be able to point at it: a
    hypothesis disputing it, a later connection contradicting it. That is the same reasoning
    `application.record` gives for making a binding its own node."""
    c = g.mint("connection", relation=relation, **({"note": note} if note else {}))
    g.link(c, "from", a)
    g.link(c, "to", b)
    return c


def connections(g: Graph, entry: str, relation: str | None = None) -> tuple:
    """Every connection touching `entry`, either end — O(1)-ish on the reverse index, and the reason no
    entry ever needs to point back at a connection."""
    out = []
    for label in ("from", "to"):
        for c in g.sources(entry, label):
            if g.kind(c) == "connection" and (relation is None or g.attr(c, "relation") == relation):
                out.append(c)
    return tuple(sorted(set(out), key=out.index))


def connected(g: Graph, entry: str, relation: str | None = None) -> tuple:
    """The entries `entry` is tied to, in either direction — the navigational form of `connections`."""
    out = []
    for c in connections(g, entry, relation):
        for end in (g.target(c, "from"), g.target(c, "to")):
            if end is not None and end != entry:
                out.append(end)
    return tuple(out)


# --- reporting --------------------------------------------------------------------------------------
def describe(g: Graph, thread: str, limit: int | None = None) -> str:
    """A readable rendering of recent memory — for inspection, and for handing to a model."""
    seq = entries(g, thread)
    shown = seq if limit is None else seq[-limit:]
    lines = [f"thread {g.attr(thread, 'label')} ({len(seq)} entries)"]
    for i, e in enumerate(shown, len(seq) - len(shown)):
        if g.kind(e) == "application":
            what = f"applied {g.attr(e, 'function')}"
        else:
            what = f"attend {attended(g, e)}" + (f" [{g.attr(e, 'note')}]" if g.attr(e, "note") else "")
        reason = why(g, e)
        ties = connections(g, e)
        lines.append(f"  {i}. {what}" + (f"  ({reason})" if reason else "")
                     + (f"  ~{len(ties)} tie(s)" if ties else ""))
    return "\n".join(lines)


__all__ = ["ENTRY_KINDS", "open_thread", "attend", "applied", "entries", "tip", "previous", "following",
           "why", "attended", "concerns", "past", "find_back", "last_touching",
           "connect", "connections", "connected", "describe"]

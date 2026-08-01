"""FORGETTING — the slower clock, and the default.

**The user's rule, 2026-08-01:** *forgetting is the default; remembering is the exception. The result of a
tool call. Something that surprises us. Not ordinary things.*

## ⚠ Why this is not a reversal of §6a, which is what it looks like

`HANDOFF.md` §6a recorded a table with **retention defaulting to KEEP**, because *dropping what you
reasoned from can contradict conclusions already drawn*. That argument was made about **sightings** —
observations taken at the dispatch boundary — and it is untouched here: an observation is the result of a
tool call, and this module keeps every one of them.

What §6a never considered is the thing the outer-loop arc then created: **the engine's own computational
scaffolding**. Measured on the three-block world, three ordinary goals grow the graph from 80 nodes to 892,
of which **76% is scaffolding** — searches, candidates, trace steps, frames, mappings, replays, bindings,
activations, registers. So the rule generalises rather than reverses:

> **Keep what you cannot re-derive.** The two irreducible kinds are **a crossing of the world** and **a
> surprise**. Everything else is re-derivable from the goal and the library, by thinking again.

⭐ And *surprise* needed no invention — the engine already computes it three ways: `memory.attribute`
answering `EXTERNAL` (nothing I did could have caused this), a `deviation` node (reality contradicted the
plan), and `workbench.unmet_expectations` (the prediction that failed). Retention had simply never been
asked to consult them.

## The shape: name the ROOTS, not the rubbish

⚠ **This is a mark-and-sweep whose root set is a claim about what matters**, and that is deliberate. A list
of droppable *kinds* would drift the moment a module adds one — the defect shape this codebase keeps
recording. A list of roots states the belief directly: *these are the things nothing can reconstruct.*

The direction invariant does the rest for free. Metadata points **at** what it describes and is never
pointed at by it (`planning_workbench.md` §2), so the world is a root that drags nothing in, while a
surprise drags in exactly what it was a surprise *about*.

## ⚠ It is a TASK, not a pass

Forgetting goes on the same agenda as everything else and drops **one record per tick**. That is not
tidiness: a sweep that ran to completion inside one call would be precisely the uninterruptible fixpoint
this whole arc exists to remove, and it would be the *worst* candidate for one, since it is the operation
most likely to be worth stopping halfway. It is also stoppable (`loop.finished` honours `stop`), which
means a watcher can decide the system is forgetting too much.

⚠ **The doomed set is computed once, when the pass opens.** Scheduling new work *during* a sweep is
undefined for the same reason `driver.step` says stepping is a yield point and not isolation: the graph is
mutable and this holds references into it. Open a fresh pass instead.
"""
from __future__ import annotations

from .graph import Graph

KINDS = ("forgetting",)

#: Kinds that are roots because **nothing can reconstruct them**. Everything else survives only by being
#: reachable from one of these.
#:
#: ⚠ `observation` is the *result of a tool call* and `deviation` is a *surprise* — the user's two
#: exceptions, and the only two entries here that are about content rather than about scaffolding being
#: absent. `thread` reaches every entry on it; `goal` reaches its constraints; `function` and `type` are
#: the library, which is authored rather than derived.
#:
#: ⭐⭐ `loop` is the one that is not about the past at all, and it is what makes **live work safe without a
#: special case**: an agenda points at its tasks, a pursuit points at its search, a search at its workbench
#: — so *being scheduled* is already the statement "this is what I am doing", and the closure protects it.
#: The first version of this module took a hand-passed pin instead, and promptly swept the loop node itself
#: out from under the sweep that was running on it.
#:
#: ⚠ There is deliberately **no `"thread"` here, and its absence is a finding**: a thread node's kind is
#: `episode`, because §5b made a thread *an episode extended* — one record, not two. The first version
#: listed `"thread"`, which named nothing at all and read as protection that was in fact coming from
#: `episode`. A planted-bug probe removing `"thread"` changed nothing, which is how it was caught.
#:
#: **⚠ Which of these actually protect anything — MEASURED, because assuming would have been wrong twice.**
#: Removing each in turn and counting what becomes doomed, over a watched world and a worked session:
#:
#: | root | status |
#: |---|---|
#: | `function`, `type` | **load-bearing** — the library is reachable from nothing else |
#: | `episode` | **load-bearing**, and it carries the most (−83 nodes without it) |
#: | `deviation` | **load-bearing when it stands alone**, i.e. once its replay has been swept |
#: | `loop` | **load-bearing only while work is LIVE** — invisible to this table, proved by probe |
#: | `root`, `goal`, `observation` | **currently redundant**: all three are reached via the thread |
#:
#: ⚠ The redundant three are kept **deliberately, as statements of the rule** rather than as mechanism. An
#: observation is one of the two things the rule exists to keep; that it *happens* to be reachable because
#: it sits on the thread is a fact about today's shape, and the first compaction of old thread entries
#: would silently turn "we keep what we saw" into "we keep what we saw, until the thread is tidied".
#: ⭐ Saying so is the difference between a redundant root and a **dead** one — and there was a dead one
#: here: `"thread"` names no kind at all.
ROOT_KINDS = ("root", "goal", "function", "type", "observation", "deviation", "episode", "loop")


def roots(g: Graph, *, also=()) -> tuple:
    """Everything that cannot be re-derived, plus whatever a caller pins.

    ⚠ `also` is how a **live** computation is protected: a task still on an agenda is not scaffolding, it
    is work in progress, and forgetting it would be the difference between forgetting and crashing."""
    out = ["root"] if "root" in g.attrs else []
    for kind in ROOT_KINDS:
        out.extend(g.of_kind(kind))
    out.extend(also)
    return tuple(dict.fromkeys(out))                    # ordered, deduped — order must not come from a set


def keepers(g: Graph, *, also=()) -> dict:
    """The transitive closure of `roots` over outgoing edges, as an ordered set.

    ⭐ Nothing here decides what a record *is*; it decides what a root can still **reach**. A settled
    search is dropped not because searches are rubbish but because, once its pursuit has finished, no root
    points at it any more. A surprise keeps the frames it was a surprise about, because the `deviation`
    node points at them — which is the direction invariant paying for itself a second time."""
    seen: dict = {}
    stack = list(roots(g, also=also))
    while stack:
        n = stack.pop()
        if n in seen or n not in g.attrs:
            continue
        seen[n] = None
        for label in g.labels(n):
            stack.extend(t for t in g.targets(n, label) if t not in seen)
    return seen


def doomed(g: Graph, *, also=()) -> tuple:
    """Every node no root can reach — what a pass would drop, in a stable order."""
    keep = keepers(g, also=also)
    return tuple(n for n in g.nodes if n not in keep)


def kept_because(g: Graph, node: str, *, also=()) -> str:
    """Why this record survived — for a reader asking *what do you still remember, and why?*"""
    if node in roots(g, also=also):
        kind = g.kind(node)
        if kind == "observation":
            return "the result of a tool call"
        if kind == "deviation":
            return "a surprise: reality contradicted the plan"
        if kind in ("function", "type"):
            return "the library: authored, not derived"
        if kind in ("goal", "thread", "episode"):
            return "what was wanted, and what was done"
        return "the world"
    if node in keepers(g, also=also):
        return "something that is kept still points at it"
    return "nothing keeps it"


# --- the pass, as a task ------------------------------------------------------------------------------
def open_forgetting(g: Graph, *, also=(), label: str = "forgetting") -> str:
    """Work out what is re-derivable, and queue it to be dropped one record per tick."""
    f = g.mint("forgetting", label=label, at=0, dropped=0)
    for n in doomed(g, also=tuple(also) + (f,)):
        g.link(f, "doomed", n)
    g.put(f, planned=g.count(f, "doomed"))
    return f


def finished(g: Graph, f: str) -> bool:
    return g.count(f, "doomed") == 0


def step(g: Graph, f: str) -> bool:
    """Forget **one** record. `True` while there is more to forget.

    ⚠⚠ **The worklist is CONSUMED FROM THE FRONT, never indexed into, and that is not a style choice.**
    The queue is an edge list, and `Graph.drop` removes every edge pointing at the node it drops —
    including this task's own `doomed` edge to it. So a cursor (`at`, incremented per step) walked a list
    that shrank underneath it and **silently forgot every other record**: measured at 892 → 564 nodes when
    the sweep had marked 798 of them. It looked like a working sweep, because the answers it must preserve
    were all still preserved and the node count really did go down.

    Same family as `search-was-irreproducible-set-tiebreak`: not a wrong answer, a *quietly partial* one,
    produced by a container whose behaviour the walk did not account for.

    ⚠ A node may also have gone already — dropping one record can be the last thing pointing at another.
    Absent is the outcome either way, so `dropped` counts what actually went rather than what was planned."""
    if finished(g, f):
        return False
    n = g.targets(f, "doomed")[0]
    g.unlink(f, "doomed", index=0)               # off the queue FIRST, so `drop` cannot shift it
    g.put(f, at=g.attr(f, "at", 0) + 1)
    if n in g.attrs:
        g.drop(n)
        g.put(f, dropped=g.attr(f, "dropped", 0) + 1)
    return not finished(g, f)


def describe(g: Graph, f: str) -> str:
    return (f"forgetting: {g.attr(f, 'dropped', 0)} dropped of {g.attr(f, 'planned', 0)}, "
            f"{g.count(f, 'doomed')} still queued")


__all__ = ["KINDS", "ROOT_KINDS", "roots", "keepers", "doomed", "kept_because",
           "open_forgetting", "step", "finished", "describe"]

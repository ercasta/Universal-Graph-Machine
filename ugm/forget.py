"""Forgetting — the slower clock, and the default.

Forgetting is the default; remembering is the exception. The result of a tool call. Something
that surprises us. Not ordinary things.

That is not a reversal of the rule for observations, which is untouched: an observation is the
result of a tool call, and every one is kept, because dropping what you reasoned from can
contradict conclusions already drawn. What it adds is the engine's own computational
scaffolding. Measured on the three-block world, three ordinary goals grow the graph from 80 nodes
to 892, of which about three quarters is scaffolding — searches, candidates, trace steps, frames,
mappings, replays, bindings, activations, registers. So the rule generalises rather than
reverses:

> Keep what you cannot re-derive. The two irreducible kinds are a crossing of the world and a
> surprise. Everything else is re-derivable from the goal and the library, by thinking again.

Surprise needed no invention, because the engine already computes it three ways: `memory.attribute`
answering that nothing the agent did could have caused a change, a `deviation` node recording
that reality contradicted the plan, and `workbench.unmet_expectations` recording a prediction
that failed. Retention had simply never been asked to consult them.

The shape names the roots, not the rubbish. This is a mark-and-sweep whose root set is a claim
about what matters. A list of droppable kinds would drift the moment a module adds one; a list of
roots states the belief directly — these are the things nothing can reconstruct. The direction
invariant does the rest for free: metadata points at what it describes and is never pointed at by
it, so the world is a root that drags nothing in, while a surprise drags in exactly what it was a
surprise about.

It is a task rather than a pass. Forgetting goes on the same agenda as everything else and drops
one record per tick. A sweep that ran to completion inside one call would be exactly the
uninterruptible fixpoint this design exists to remove, and it would be the worst candidate for
one, since it is the operation most likely to be worth stopping halfway. It is stoppable too, so
a watcher can decide the system is forgetting too much.

The doomed set is computed once, when the pass opens. Scheduling new work during a sweep is
undefined, because the graph is mutable and this holds references into it. Open a fresh pass
instead.

See `docs/memory.md`.
"""
from __future__ import annotations

from pathlib import Path

from .graph import Graph

KINDS = ("forgetting",)

#: The judgement about what is irreplaceable now lives in `rules/keeping.cnl`, authored as a
#: `policy`. See `install_defaults` and `docs/audit.md`'s F7 — it was a Python tuple, and a
#: judgement kept where nothing can argue with it rots: that one carried a dead entry naming no
#: kind at all, beside a note wondering whether another was redundant.


def keep(g: Graph, kind: str, *, because: str | None = None) -> str:
    """Declare a kind irreplaceable. Authored through `policy … : keep <kind>`, never called directly
    by a domain — this is the constructor that surface reaches."""
    # `keeps`, not `kind`: `mint`'s own first parameter is the node's kind, and passing
    # `kind=` as an attribute collides with it. The node's kind is "keep"; what it keeps is
    # a different fact and needs a different word.
    k = g.mint("keep", keeps=kind, **({"because": because} if because else {}))
    g.link("root", "has", k)                            # a real thing: quotable, disputable, withdrawable
    return k


def kept_kinds(g: Graph) -> tuple:
    """The kinds a policy says are irreplaceable, in declaration order.

    Withdrawn ones are skipped, like every other enumerator here — *"ignore that"* has to reach the
    thing that enumerates, and it reaches further than usual in this case: withdrawing a `keep` makes a
    whole class of record forgettable at the next sweep."""
    from .discourse import live
    return tuple(dict.fromkeys(g.attr(k, "keeps") for k in live(g, g.of_kind("keep"))))


def install_defaults(g: Graph) -> tuple:
    """Author the shipped keeping policy from `rules/keeping.cnl`. Returns the kinds it declared.

    Shipped as *text in the repo* rather than as a Python default, which is the whole of what changed
    here: the list is now something a reader can open, argue with, and edit without touching code — and
    the reasons that used to sit in a comment beside the tuple are in it, where they can be read by
    anyone deciding whether to keep a kind."""
    from . import intake as I
    I.read(g, (Path(__file__).parent / "rules" / "keeping.cnl").read_text(encoding="utf-8"))
    return kept_kinds(g)


def roots(g: Graph, *, also=()) -> tuple:
    """Everything that cannot be re-derived, plus whatever a caller pins.

    `also` is how a live computation is protected: a task still on an agenda is not scaffolding, it
    is work in progress, and forgetting it would be the difference between forgetting and crashing.

    **Refuses when nothing has been declared worth keeping.** An empty policy is not an empty answer
    here: it would make every record unreachable and hand a sweep the whole graph. This is the one place
    where "nothing authored" and "a safe default" come apart — `precedence` can answer *declaration
    order* and mean it, and there is no harmless reading of *keep nothing*."""
    kinds = kept_kinds(g)
    if not kinds:
        raise ValueError(
            "nothing is declared worth keeping, so a sweep would take the whole graph. Author a "
            "`policy` with `keep <kind>` lines, or call `forget.install_defaults(g)` for the shipped ones.")
    out = ["root"] if "root" in g.attrs else []
    for kind in kinds:
        out.extend(g.of_kind(kind))
    out.extend(also)
    return tuple(dict.fromkeys(out))                    # ordered, deduped — order must not come from a set


def keepers(g: Graph, *, also=()) -> dict:
    """The transitive closure of `roots` over outgoing edges, as an ordered set.

    Nothing here decides what a record *is*; it decides what a root can still reach. A settled
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


# --- compact: imagined evidence is superseded by real evidence -----------------------------------------
def compact(g: Graph) -> tuple:
    """Drop the imagined evidence for a claim that has since acquired real evidence.

    This is's `COMPACT`, and it turned out to be a *rule* rather than a mechanism — the whole of it
    is knowing when a record is superseded. `goal.py` already keeps the two kinds of evidence rigorously
    apart, because conflating them was a real defect (: the driver closed a world goal on imagined
    evidence, so a goal read as met while nothing had happened):

    | record | means |
    |---|---|
    | `planned` + `seen_in` + `planned_witness` | *I know how to do this* — an imagined frame |
    | `closed` + `met_by` | *this is now true* — a real node |

    So once a goal is closed, `seen_in` points into an imagination of a world that no longer exists,
    while `met_by` is the same claim with better evidence. Dropping the first loses nothing and releases the
    workbench behind it — measured at 51 further nodes on a three-goal session, 22% of what survives a
    sweep, because one edge into one frame keeps every frame, mapping and transformation it can reach.

    Only when closed, and that is the entire correctness condition. A goal that is planned and *not*
    carried out has no other evidence — its imagined frame is the only account of how it would be met, and
    `execution.recover` needs the frame tree it belongs to. Compacting that would not be tidying, it would
    be forgetting the plan.

    `planned` itself stays. The distinction exists to protect is between *knowing how* and *it being
    true*, and both flags survive; what goes is only the pointer into the imagination."""
    freed = []
    for x in g.of_kind("goal"):
        if not g.attr(x, "closed"):
            continue
        for label in ("seen_in", "planned_witness"):
            while g.count(x, label):
                freed.append((x, label, g.target(x, label)))
                g.unlink(x, label, index=0)
    return tuple(freed)


# --- the pass, as a task ------------------------------------------------------------------------------
def open_forgetting(g: Graph, *, also=(), label: str = "forgetting", compacting: bool = True) -> str:
    """Work out what is re-derivable, and queue it to be dropped one record per tick.

    `compact` runs first and eagerly, before the doomed set is worked out, because it changes what is
    reachable — that is the point of it. It is not queued a-record-per-tick like the sweep: an unlink is not
    a loss, it is the removal of a claim that a *better* record already makes, so there is nothing to be
    stopped in the middle of."""
    f = g.mint("forgetting", label=label, at=0, dropped=0)
    if compacting:
        g.put(f, compacted=len(compact(g)))
    for n in doomed(g, also=tuple(also) + (f,)):
        g.link(f, "doomed", n)
    g.put(f, planned=g.count(f, "doomed"))
    return f


def finished(g: Graph, f: str) -> bool:
    return g.count(f, "doomed") == 0


def step(g: Graph, f: str) -> bool:
    """Forget one record. `True` while there is more to forget.

    The worklist is consumed from the front, never indexed into, and that is not a style choice.
    The queue is an edge list, and `Graph.drop` removes every edge pointing at the node it drops —
    including this task's own `doomed` edge to it. So a cursor (`at`, incremented per step) walked a list
    that shrank underneath it and silently forgot every other record: measured at 892 → 564 nodes when
    the sweep had marked 798 of them. It looked like a working sweep, because the answers it must preserve
    were all still preserved and the node count really did go down.

    Same family as `search-was-irreproducible-set-tiebreak`: not a wrong answer, a *quietly partial* one,
    produced by a container whose behaviour the walk did not account for.

    A node may also have gone already — dropping one record can be the last thing pointing at another.
    Absent is the outcome either way, so `dropped` counts what actually went rather than what was planned."""
    if finished(g, f):
        return False
    n = g.targets(f, "doomed")[0]
    g.unlink(f, "doomed", index=0)               # off the queue first, so `drop` cannot shift it
    g.put(f, at=g.attr(f, "at", 0) + 1)
    if n in g.attrs:
        g.drop(n)
        g.put(f, dropped=g.attr(f, "dropped", 0) + 1)
    return not finished(g, f)


def describe(g: Graph, f: str) -> str:
    return (f"forgetting: {g.attr(f, 'dropped', 0)} dropped of {g.attr(f, 'planned', 0)}, "
            f"{g.count(f, 'doomed')} still queued")


__all__ = ["KINDS", "keep", "kept_kinds", "install_defaults", "roots", "keepers", "doomed", "kept_because", "compact",
           "open_forgetting", "step", "finished", "describe"]

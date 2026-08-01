"""SEARCH STATE — the planner's own working memory, as ordinary graph data.

**Why this module exists.** `driver.pursue` held its entire working state in Python locals: a `frontier`
list, a `seen` set, a step counter and a list of refusals. Everything *else* the planner touches was
already graph data — frames, mappings, bindings, the thread — so the search was the one part of the system
that could not be read by the system. `composability-principle` names that shape exactly: **a hardcoded
mechanism is an unreachable island**, and the homoiconicity claim (a rule can write a rule) fails precisely
where the mechanism is Python. `deliberation.md` put it as *deliberation is the third thing the system
computes with and cannot compute about*. This is the first half of removing that.

**⚠ Moving the state changed NO semantics, deliberately** — it swapped four containers for graph-backed
ones and nothing else, so the existing checks were a real oracle for it. A refactor that changed behaviour
at the same time would have left nothing to check it against.

**⭐⭐ That is what made the yield point possible, and `driver.step` is now it.** Because every piece of a
step's state is reachable from one `search` node, one iteration can be a module-level function instead of
a closure inside a `while` — so a caller other than `pursue` can drive the search, pause between two
imagined states, read what has been considered, and resume. `pursue` still exists and is unchanged in
behaviour; it is now a loop *over* `step` rather than being the search itself. Verified by driving the
67-state blind search by hand and reaching the same plan at the same cost.

⚠ The other half of a step's context — `rank`, `allow`, `trace`, `decide` — is Python callables, which
cannot live in a graph and are passed per call. `context` returns the graph-resident half. That split is
the honest boundary: hooks are substitutable *behaviour*, everything here is *state*.

## ⚠⚠ The two structures here are the ones that caused this project's worst defect

`search-was-irreproducible-set-tiebreak`: `workbench.reachable` returned a **`set`**, so copy order fell to
hash order, the frontier's tie-break became arbitrary, and the same goal answered `400/fail` or `12/found`
run to run. **132 checks passed over it**, because a single run of anything is self-consistent. The two
structures implicated were the frontier and the visited set — which are exactly what this module now owns.

So, two rules that are not negotiable here:

* **The frontier is ORDERED, and ties keep insertion order.** `Graph.out` holds an ordered list per label,
  `targets` returns it in that order, and the sort below is stable — so a tie breaks the same way it broke
  when the frontier was a Python list. That is not an accident to be preserved by luck; it is the reason
  candidates are edges rather than anything set-shaped.
* **A signature is CANONICAL before it is compared.** `state_of` genuinely returns a `frozenset`, so it is
  sorted into a string here rather than iterated. Nothing in this module iterates a set and lets the order
  matter.

## The shape

```
search ──goal──▶ goal          ──candidate──▶ candidate (ORDERED: the frontier)
       ──workbench──▶ wb       ──signature──▶ signature (the visited set)
       ──thread──▶ thread      ──refusal────▶ refusal
```

A `candidate` carries what the frontier tuple used to: the frame to expand, the depth, the function, its
bindings (one `candidate_arg` per parameter), the ranking key, and the plan-so-far. **The plan-so-far is a
linked list** (`trace_step ──after──▶ trace_step`), which shares prefixes for free — the old tuple
`trace + (step,)` copied the whole prefix per candidate, and a linked list is what that expression already
was, written down.

⚠ **Direction invariant** (`planning_workbench.md` §2): every kind here is metadata, so it points **at**
what it describes and is never pointed at by it. A frame does not know it is on a frontier.
"""
from __future__ import annotations

from .graph import Graph

KINDS = ("search", "candidate", "candidate_arg", "trace_step", "signature", "refusal")


# --- opening ----------------------------------------------------------------------------------------
def open_search(g: Graph, goal: str, workbench: str, thread: str, subject: str, *,
                max_steps: int, max_depth: int, guided: bool, opened: str | None = None) -> str:
    """⭐ Everything a step needs that is not a Python callable lives HERE, which is what lets one
    iteration be a module-level function rather than a closure inside the loop. `opened` is the thread
    entry the goal was taken on at — carried so a step can tie its outcome back to it without the caller
    having to hold it."""
    s = g.mint("search", steps=0, max_steps=max_steps, max_depth=max_depth, guided=guided)
    g.link(s, "goal", goal)
    g.link(s, "workbench", workbench)
    g.link(s, "thread", thread)
    g.link(s, "subject", subject)
    if opened is not None:
        g.link(s, "opened", opened)
    return s


def context(g: Graph, s: str) -> dict:
    """The graph-resident half of a step's context. The other half — `rank`, `allow`, `trace`, `decide` —
    is Python callables, which cannot live in a graph and are passed per call. That split is the honest
    one: hooks are substitutable behaviour, everything else is state."""
    return {"goal": g.target(s, "goal"), "workbench": g.target(s, "workbench"),
            "thread": g.target(s, "thread"), "subject": g.target(s, "subject"),
            "opened": g.target(s, "opened"),
            "max_steps": g.attr(s, "max_steps"), "max_depth": g.attr(s, "max_depth"),
            "guided": g.attr(s, "guided")}


def steps_taken(g: Graph, s: str) -> int:
    return g.attr(s, "steps", 0)


def took_a_step(g: Graph, s: str) -> int:
    n = steps_taken(g, s) + 1
    g.put(s, steps=n)
    return n


# --- the plan-so-far, as a shared-prefix linked list -------------------------------------------------
def extend_trace(g: Graph, after: str | None, function: str, touched) -> str:
    """One more step on the plan-so-far. `after` is the previous step, or `None` at the root.

    ⭐ The old code wrote `trace + ((name, frozenset(...)),)`, copying the prefix for every candidate. A
    linked list *is* that expression, and sharing the prefix is what it was always describing."""
    step = g.mint("trace_step", function=function)
    for n in sorted(touched):                 # ⚠ sorted: `touched` is a set, and order must not leak
        g.link(step, "touched", n)
    if after is not None:
        g.link(step, "after", after)
    return step


def trace_tuple(g: Graph, step: str | None) -> tuple:
    """The linked list read back as the `(function, frozenset(nodes))` tuple `goal.breached` and
    `goal.outstanding` take. Oldest first, which is the order the tuple always had."""
    out = []
    while step is not None:
        out.append((g.attr(step, "function"), frozenset(g.targets(step, "touched"))))
        step = g.target(step, "after")
    out.reverse()
    return tuple(out)


# --- the frontier ------------------------------------------------------------------------------------
def offer(g: Graph, s: str, *, key: tuple, frame: str, depth: int, function: str,
          bindings: dict, open_count: int, trace: str | None) -> str:
    """Put one candidate on the frontier. Appended, so insertion order is preserved for tie-breaking."""
    c = g.mint("candidate", function=function, depth=depth, open_count=open_count,
               k0=key[0], k1=key[1], k2=key[2])
    g.link(c, "frame", frame)
    for param in sorted(bindings):            # ⚠ sorted: a dict's order must not reach the graph
        a = g.mint("candidate_arg", param=param)
        g.link(a, "mapping", bindings[param])
        g.link(c, "arg", a)
    if trace is not None:
        g.link(c, "trace", trace)
    g.link(s, "candidate", c)
    return c


def frontier(g: Graph, s: str) -> tuple:
    """Every candidate still waiting, **in insertion order** — the ordering the tie-break depends on."""
    return g.targets(s, "candidate")


def take_best(g: Graph, s: str):
    """The best candidate, removed from the frontier. `None` when it is empty.

    ⚠ **Stable sort over an insertion-ordered tuple**, which is what makes this byte-identical to the
    `frontier.sort(key=…)` + `pop(0)` it replaces. Python's sort is stable, `Graph.targets` returns the
    edge list in the order it was built, and equal keys therefore keep the order they were offered in."""
    here = frontier(g, s)
    if not here:
        return None
    best = sorted(here, key=lambda c: (g.attr(c, "k0"), g.attr(c, "k1"), g.attr(c, "k2")))[0]
    g.unlink(s, "candidate", dst=best)
    return best


def read(g: Graph, c: str) -> dict:
    """A candidate back as the fields the loop works in."""
    return {"frame": g.target(c, "frame"),
            "depth": g.attr(c, "depth"),
            "function": g.attr(c, "function"),
            "open_count": g.attr(c, "open_count"),
            "trace_node": g.target(c, "trace"),
            "bindings": {g.attr(a, "param"): g.target(a, "mapping") for a in g.targets(c, "arg")}}


# --- the visited set ---------------------------------------------------------------------------------
def digest(state: frozenset, outstanding: tuple) -> str:
    """A canonical, order-free key for "this world, with this much still required of the plan".

    ⚠ **`state` is a `frozenset` and is SORTED here rather than iterated.** That is the whole lesson of
    `search-was-irreproducible-set-tiebreak` applied at the one place it could recur: a deterministic
    computation that ends in a set has an undeclared tie-break in it. Sorting the repr is enough — the
    elements are tuples of strings and sorted comparison over them is total and stable."""
    return "|".join(sorted(repr(x) for x in state)) + "//" + ",".join(sorted(outstanding))


def already_seen(g: Graph, s: str, key: str) -> bool:
    """⚠ A linear scan of this search's signatures, bounded by `max_steps` (60 by default), so the whole
    search costs O(steps²) attribute reads — a few thousand. Deliberately not indexed: an index would be a
    second structure that can disagree with the first, which is the drift class this codebase keeps
    re-finding. Revisit only with a measurement, per `measure-before-optimizing-ugm`."""
    return any(g.attr(n, "digest") == key for n in g.targets(s, "signature"))


def mark_seen(g: Graph, s: str, key: str, frame: str) -> str:
    """Record that this world has been imagined, and **by which frame** — which is what makes the visited
    set answer *what has the search already ruled out?* rather than merely making it terminate."""
    n = g.mint("signature", digest=key)
    g.link(n, "first_reached", frame)
    g.link(s, "signature", n)
    return n


def considered(g: Graph, s: str) -> tuple:
    """Every frame the search has already imagined — the visited set, read as states rather than keys."""
    return tuple(g.target(n, "first_reached") for n in g.targets(s, "signature"))


# --- refusals ----------------------------------------------------------------------------------------
def refuse(g: Graph, s: str, function: str, reasons: tuple) -> str:
    n = g.mint("refusal", function=function, reasons=tuple(reasons))
    g.link(s, "refusal", n)
    return n


def refusals(g: Graph, s: str) -> tuple:
    """`((function, reasons), …)` — the shape the report has always carried."""
    return tuple((g.attr(n, "function"), g.attr(n, "reasons")) for n in g.targets(s, "refusal"))


def blocked_by(g: Graph, s: str) -> tuple:
    return tuple(sorted({r for _n, rs in refusals(g, s) for r in rs}))


__all__ = ["KINDS", "open_search", "context", "steps_taken", "took_a_step", "extend_trace", "trace_tuple",
           "offer", "frontier", "take_best", "read", "digest", "already_seen", "mark_seen",
           "considered", "refuse", "refusals", "blocked_by"]

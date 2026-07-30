"""EXECUTION — following a plan for real, and noticing when reality disagrees.

The workbench imagined a plan; this runs it. Everything needed was already recorded, which is the point of
having built mappings and transformations rather than a log:

* **which function** — the transformation records the *real* function, separately from the mock it
  actually executed while imagining. That is why `step` stores both;
* **on which node** — the transformation's arguments bind *mappings*, and a mapping resolves to the real
  node. A log saying "`list_dir` was applied" could not do this;
* **what was expected** — the recorded return type, which makes deviation a cheap `types.is_a` rather than
  a whole-subgraph comparison.

**Fail fast on deviation, and do not roll back.** Execution stops at the first step whose real result
fails the cast it promised, because everything after it was planned *on the assumption that it held*.
Continuing would be acting on a world that no longer matches the plan. And nothing is undone: real effects
have already left the graph, and pretending a journal could reach them would be worse than not having one.
The honest output is "these steps happened, this one diverged, here is how."

**Imagined nodes are bound by provenance.** A step may mint something that did not exist at planning time —
its mapping has no `original`. When the real function runs and mints its counterpart, the two are matched
by *which transformation produced them*, since that is the only correspondence available for something that
did not exist when planning started. ⚠ Matching within a transformation is by kind and order; if one
transformation mints two nodes of the same kind, the pairing is a guess, and this module says so rather
than picking silently.
"""
from __future__ import annotations

from . import function as fn
from . import workbench as W
from .graph import Graph


def path_to(g: Graph, wb: str, leaf: str) -> tuple:
    """The frames from the root down to `leaf`, in order.

    The frame tree forks on assumptions, so a plan is a *path* through it, not the whole tree. Executing
    means committing to one branch — which is exactly the choice the forks were there to keep open."""
    parents = {}
    for f in W.frames(g, wb):
        for nxt in g.targets(f, "next"):
            parents[nxt] = f
    chain, cur = [leaf], leaf
    while cur in parents:
        cur = parents[cur]
        chain.append(cur)
    return tuple(reversed(chain))


def _successor_in(g: Graph, mapping: str, frame: str):
    """The continuation of `mapping` that belongs to `frame` — `next` is 1:N because frames fork."""
    for nxt in g.targets(mapping, "next"):
        if nxt in g.targets(frame, "mapping"):
            return nxt
    return None


def _bind_minted(g: Graph, frame: str, minted: list, bound: dict, notes: list) -> None:
    """Match nodes the real call just created to the imagined mappings that predicted them."""
    pending = [m for m in W.mappings(g, frame)
               if W.is_imagined(g, m) and m not in bound]
    by_kind: dict = {}
    for n in minted:
        by_kind.setdefault(g.kind(n), []).append(n)
    for m in pending:
        want = g.kind(W.image_of(g, m))
        pool = by_kind.get(want, [])
        if not pool:
            notes.append(f"planned a {want} that the real call did not produce")
            continue
        if len(pool) > 1:
            notes.append(f"ambiguous: {len(pool)} real {want} nodes for a planned one — paired by order")
        bound[m] = pool.pop(0)


def execute(g: Graph, wb: str, leaf: str) -> dict:
    """Replay the plan ending at `leaf` against the real graph.

    Returns a report: the steps that ran, the first deviation if any, the mapping-to-real bindings, and
    any notes about imagined nodes that could not be matched cleanly."""
    frames = path_to(g, wb, leaf)
    bound: dict = {}
    notes: list = []

    for m in W.mappings(g, frames[0]):          # seed from frame 0: these already exist for real
        real = W.resolve(g, m)
        if real is not None:
            bound[m] = real

    ran, deviation = [], None
    for prev, frame in zip(frames, frames[1:]):
        for m in W.mappings(g, prev):           # a node keeps its identity across frames
            nxt = _successor_in(g, m, frame)
            if nxt is not None and m in bound:
                bound[nxt] = bound[m]

        tr = g.target(frame, "via")
        if tr is None:
            continue
        name = g.attr(tr, "function")           # the REAL function, not the mock that was imagined
        args, missing = {}, []
        for b in g.targets(tr, "arg"):
            param, m = g.attr(b, "param"), g.target(b, "mapping")
            if m in bound:
                args[param] = bound[m]
            else:
                missing.append(param)
        if missing:
            deviation = {"step": name, "why": f"unbound argument(s) {missing} — the plan referred to "
                                              f"something that does not exist in the real graph"}
            break

        before = set(g.nodes)
        _focus, out = fn.invoke(g, name, args)
        minted = sorted(set(g.nodes) - before)
        first_param = fn.load(g, name)[0][0]
        result = out.get("result") or args.get(first_param)
        ran.append(name)

        violations = W.deviates(g, tr, result)
        if violations:
            deviation = {"step": name, "expected": g.attr(tr, "expects"), "violations": violations,
                         "assumed": g.attr(g.target(tr, "assumes"), "label")
                                    if g.target(tr, "assumes") else None}
            break

        _bind_minted(g, frame, minted, bound, notes)
        for b in g.targets(tr, "arg"):
            m = g.target(b, "mapping")
            if m in bound:
                bound[m] = result if g.attr(b, "param") == first_param else bound[m]

    return {"ran": tuple(ran), "deviation": deviation, "completed": deviation is None,
            "bindings": bound, "notes": tuple(notes)}


def alternatives(g: Graph, wb: str, transformation: str) -> tuple:
    """The other outcomes that were explored for the step that just deviated — contingency plans, free.

    If reality returned something other than what was assumed, and that branch *was* explored, the
    alternative plan already exists. This is the payoff for branching deliberately at the few points that
    warrant it, and the reason an abandoned fork is kept as data rather than erased."""
    frame = next((f for f in W.frames(g, wb) if g.target(f, "via") == transformation), None)
    if frame is None:
        return ()
    parent = next((f for f in W.frames(g, wb) if frame in g.targets(f, "next")), None)
    if parent is None:
        return ()
    return tuple(sib for sib in g.targets(parent, "next") if sib != frame)


def report(g: Graph, result: dict) -> str:
    """A readable account — what ran, and if something diverged, what it had assumed."""
    lines = [f"ran: {', '.join(result['ran']) or '(nothing)'}"]
    dev = result["deviation"]
    if dev is None:
        lines.append("completed as planned")
    else:
        lines.append(f"DIVERGED at {dev['step']}")
        if dev.get("assumed"):
            lines.append(f"  it had assumed: {dev['assumed']}")
        if dev.get("violations"):
            lines.append(f"  expected {dev['expected']}, but: {dev['violations']}")
        if dev.get("why"):
            lines.append(f"  {dev['why']}")
    lines.extend(f"  note: {n}" for n in result["notes"])
    return "\n".join(lines)


__all__ = ["path_to", "execute", "alternatives", "report"]

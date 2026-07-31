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

**Recovery is two mechanisms, and they answer different questions.** Once a step has diverged there are
exactly two honest moves, and which one applies is decided by the structure rather than by a policy:

* **`resume` — was this outcome already explored?** A fork exists precisely because someone thought this
  call could turn out more than one way. If a sibling branch assumed *what reality actually did*, the rest
  of that branch is a plan for the world we are now in, already imagined and already checked. Continuing
  down it is not replanning at all; it is following the contingency the fork was for. **The deviating call
  is not run again** — it already happened, and its real effects are what we are recovering from.
* **`replan` — nothing explored fits.** Then the branch tree has nothing to say, and the only sound move is
  to propose afresh **from the world as it actually is**, taking the real result of the diverged step as the
  subject. What comes back is a lazy chain (`plan.py`), so re-proposing still commits to nothing.

⚠ `resume` requires the sibling to be *the same function*. Siblings of a frame are alternative successors,
which need not be alternative outcomes of one call — a fork may try a different action entirely. Continuing
down such a branch would silently skip a call that never ran.

**What `replan` deliberately does not do is rehearse.** The re-proposal is a chain, not a workbench run.
Turning a chain into workbench steps needs a rule for binding each pending call's *output* to a mapping, and
for a call that mints something that is a real question, not a missing line of code — the same question
`compile_episode` runs into. Proposing without rehearsing is the honest partial answer; guessing the binding
would make a plan that looks verified and is not.
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


def _parent_of(g: Graph, wb: str, frame: str):
    return next((f for f in W.frames(g, wb) if frame in g.targets(f, "next")), None)


def leaves_under(g: Graph, wb: str, frame: str) -> tuple:
    """The ends of every branch at or below `frame`. A frame with no successor is a leaf, including
    `frame` itself when nothing was planned after it."""
    out, queue = [], [frame]
    while queue:
        f = queue.pop(0)
        nxts = g.targets(f, "next")
        if nxts:
            queue.extend(nxts)
        else:
            out.append(f)
    return tuple(out)


def _carry(g: Graph, prev: str, frame: str, bound: dict) -> None:
    """A node keeps its identity across frames, so its binding follows its mapping's successor."""
    for m in W.mappings(g, prev):
        nxt = _successor_in(g, m, frame)
        if nxt is not None and m in bound:
            bound[nxt] = bound[m]


def _settle(g: Graph, tr: str, frame: str, result, minted: list, bound: dict, notes: list) -> None:
    """Record what a real call produced: bind the nodes it minted, and point the subject's mapping at the
    result — **a cast returns its subject**, so the first parameter's mapping now names the cast node."""
    _bind_minted(g, frame, minted, bound, notes)
    first_param = fn.load(g, g.attr(tr, "function"))[0][0]
    for b in g.targets(tr, "arg"):
        m = g.target(b, "mapping")
        if m in bound and g.attr(b, "param") == first_param:
            bound[m] = result


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


def _replay(g: Graph, frames: tuple, bound: dict, notes: list, ran: list):
    """Walk a path of frames, running each frame's `via` for real. Returns the first deviation, or `None`.

    A deviation carries the `frame`, the `transformation`, the real `result` and what the call `minted`,
    because recovery needs all four: which fork to look at, whether a sibling assumed what happened, and
    what to hand the continuation given that **the call is not run again**."""
    for prev, frame in zip(frames, frames[1:]):
        _carry(g, prev, frame, bound)

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
            return {"step": name, "frame": frame, "transformation": tr, "result": None, "minted": (),
                    "why": f"unbound argument(s) {missing} — the plan referred to "
                           f"something that does not exist in the real graph"}

        before = set(g.nodes)
        _focus, out = fn.invoke(g, name, args)
        minted = sorted(set(g.nodes) - before)
        result = out.get("result") or args.get(fn.load(g, name)[0][0])
        ran.append(name)

        violations = W.deviates(g, tr, result)
        if violations:
            return {"step": name, "frame": frame, "transformation": tr, "result": result,
                    "minted": tuple(minted), "expected": g.attr(tr, "expects"), "violations": violations,
                    "assumed": g.attr(g.target(tr, "assumes"), "label")
                               if g.target(tr, "assumes") else None}

        _settle(g, tr, frame, result, minted, bound, notes)
    return None


def execute(g: Graph, wb: str, leaf: str) -> dict:
    """Replay the plan ending at `leaf` against the real graph.

    Returns a report: the steps that ran, the first deviation if any, the mapping-to-real bindings, and
    any notes about imagined nodes that could not be matched cleanly. The workbench travels in the report
    so recovery takes one argument — a deviation is only interpretable against the tree it came from."""
    frames = path_to(g, wb, leaf)
    bound: dict = {}
    notes: list = []
    ran: list = []

    for m in W.mappings(g, frames[0]):          # seed from frame 0: these already exist for real
        real = W.resolve(g, m)
        if real is not None:
            bound[m] = real

    deviation = _replay(g, frames, bound, notes, ran)
    return {"ran": tuple(ran), "deviation": deviation, "completed": deviation is None,
            "bindings": bound, "notes": tuple(notes), "workbench": wb}


def alternatives(g: Graph, wb: str, transformation: str) -> tuple:
    """The other outcomes that were explored for the step that just deviated — contingency plans, free.

    If reality returned something other than what was assumed, and that branch *was* explored, the
    alternative plan already exists. This is the payoff for branching deliberately at the few points that
    warrant it, and the reason an abandoned fork is kept as data rather than erased."""
    frame = next((f for f in W.frames(g, wb) if g.target(f, "via") == transformation), None)
    if frame is None:
        return ()
    parent = _parent_of(g, wb, frame)
    if parent is None:
        return ()
    return tuple(sib for sib in g.targets(parent, "next") if sib != frame)


# --- recovery ---------------------------------------------------------------------------------------
def matching_alternative(g: Graph, wb: str, deviation: dict):
    """The explored branch that assumed **what reality actually did**, or `None`.

    This is the whole payoff of forking deliberately: the test is the same `deviates` used to detect the
    problem, asked of each sibling's promise instead. A sibling that survives it is a plan for the world we
    are now in — imagined, checked, and needing no new thought.

    ⚠ Restricted to siblings applying the **same function**. Siblings are alternative *successors*, which
    need not be alternative *outcomes*; a fork may try a different action. Resuming into one of those would
    silently skip a call that never ran, and the caller would be told the plan completed."""
    if not deviation or deviation.get("result") is None:
        return None
    for sib in alternatives(g, wb, deviation["transformation"]):
        tr = g.target(sib, "via")
        if tr is None or g.attr(tr, "function") != deviation["step"]:
            continue
        if not W.deviates(g, tr, deviation["result"]):
            return sib
    return None


def resume(g: Graph, result: dict, *, branch=None, leaf=None):
    """Continue a diverged execution down a branch that assumed what actually happened. `None` if there is
    no such branch and nothing was passed.

    **The diverged call is not re-run.** It reached the world once; running it again would double its
    effects and is the single thing most likely to be got wrong here. Instead its real outcome is settled
    onto the chosen branch's *own* mappings — carried from the shared parent frame, since siblings do not
    share mapping nodes — and replay picks up at the step after it.

    `leaf` chooses among several ends below the branch; the default takes the first, matching the planner's
    first-solution-wins discipline rather than pretending to arbitrate."""
    wb, dev = result["workbench"], result["deviation"]
    branch = branch if branch is not None else matching_alternative(g, wb, dev)
    if branch is None:
        return None
    parent = _parent_of(g, wb, branch)
    tr = g.target(branch, "via")
    if parent is None or tr is None:
        return None

    bound, notes, ran = dict(result["bindings"]), list(result["notes"]), list(result["ran"])
    _carry(g, parent, branch, bound)
    _settle(g, tr, branch, dev["result"], list(dev["minted"]), bound, notes)

    if leaf is None:
        leaf = leaves_under(g, wb, branch)[0]
    path = path_to(g, wb, leaf)
    deviation = _replay(g, path[path.index(branch):], bound, notes, ran)
    return {"ran": tuple(ran), "deviation": deviation, "completed": deviation is None,
            "bindings": bound, "notes": tuple(notes), "workbench": wb,
            "resumed_on": branch, "resumed_assuming": g.attr(tr, "expects")}


def replan(g: Graph, result: dict, want: str, *, subject=None, depth: int = 8):
    """Propose afresh **from the world as it actually is**. Returns a lazy chain, or `None` if nothing in
    the library reaches `want` from here — an ordinary answer, not an error.

    The subject defaults to the diverged step's real result, because that node *is* the actual state: the
    call ran, so whatever it produced is what the next plan has to start from. Nothing is committed —
    a chain is data until `plan.run` is called on it."""
    from . import plan as P
    dev = result.get("deviation")
    if subject is None:
        subject = dev.get("result") if dev else None
    return P.plan(g, want, subject, depth=depth)


def recover(g: Graph, result: dict, want: str | None = None, *, depth: int = 8) -> dict:
    """Given an execution report, do the one thing the structure warrants. Reports which, and why.

    Order is not a preference heuristic: a matching branch is *already verified against this world*, and a
    fresh proposal is not, so the contingency is tried first on evidence rather than on taste."""
    if result["completed"]:
        return {"kind": "completed", "result": result}
    resumed = resume(g, result)
    if resumed is not None:
        return {"kind": "contingency", "result": resumed, "branch": resumed["resumed_on"],
                "assuming": resumed["resumed_assuming"]}
    if want is not None:
        from . import plan as P
        chain = replan(g, result, want, depth=depth)
        if chain is not None:
            return {"kind": "replanned", "chain": chain, "plan": P.describe(g, chain)}
    return {"kind": "stuck", "why": "no explored branch assumed what happened"
                                    + ("" if want is not None
                                       else ", and no goal was given to replan towards")}


def report(g: Graph, result: dict) -> str:
    """A readable account — what ran, and if something diverged, what it had assumed."""
    lines = [f"ran: {', '.join(result['ran']) or '(nothing)'}"]
    if result.get("resumed_on"):
        lines.append(f"  (resumed on the branch assuming {result['resumed_assuming']})")
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


__all__ = ["path_to", "leaves_under", "execute", "alternatives",
           "matching_alternative", "resume", "replan", "recover", "report"]

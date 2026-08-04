"""Execution — following a plan for real, and noticing when reality disagrees.

The workbench imagined a plan; this runs it. Everything needed was already recorded, which is
what mappings and transformations are for rather than a log:

* which function — the transformation records the real function, separately from the mock it
  executed while imagining, which is why `step` stores both;
* on which node — the transformation's arguments bind mappings, and a mapping resolves to the
  real node. A log saying "`list_dir` was applied" could not do this;
* what was expected — the recorded return type, which makes deviation a cheap cast check rather
  than a whole-subgraph comparison.

Fail fast on deviation, and do not roll back. Execution stops at the first step whose real result
fails the cast it promised, because everything after it was planned on the assumption that it
held. Nothing is undone: real effects have already left the graph, and pretending a journal could
reach them would be worse than not having one. The honest output is "these steps happened, this
one diverged, here is how".

Imagined nodes are bound by provenance. A step may mint something that did not exist at planning
time, so its mapping has no original and the real counterpart is matched by which transformation
produced it. Matching within a transformation is by kind and order, so if one transformation
mints two nodes of the same kind the pairing is a guess, and this module says so rather than
picking silently.

Recovery is two mechanisms answering different questions.

* `resume` — was this outcome already explored? A fork exists precisely because someone thought
  the call could turn out more than one way, so a sibling that assumed what reality actually did
  is a plan for the world we are now in, already imagined and already checked. The diverged call
  is not run again: it already happened, and its effects are what we are recovering from.
* `replan` — nothing explored fits, so propose afresh from the world as it actually is, taking
  the real result of the diverged step as the subject. What comes back is a lazy chain, so
  re-proposing still commits to nothing.

`resume` requires the sibling to be the same function. Siblings of a frame are alternative
successors, which need not be alternative outcomes of one call — a fork may try a different
action entirely, and continuing down such a branch would silently skip a call that never ran.

`replan` deliberately does not rehearse. Turning a chain into workbench steps needs a rule for
binding each pending call's output to a mapping, and for a call that mints something that is a
real question rather than a missing line of code. Proposing without rehearsing is the honest
partial answer; guessing the binding would make a plan that looks verified and is not.

See `docs/planning.md`.
"""
from __future__ import annotations

from . import access
from . import activation as ACT
from . import function as fn
from . import types as TY
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


# --- the replay's state, as graph data ----------------------------------------------------------------
#
# `_replay` was a Python `for` holding `bound`, `notes`, `ran` and its position in local variables, so
# a plan being carried out for real — the one loop that touches the world — was the thing the system could
# least say anything about mid-flight. Making the instruction set tick was the same move one level down; this is it one level up, and `execute` is now a loop over `step` exactly as `Machine.run` is a loop over
# `tick`.
#
# A binding is a node, not a dict entry, and it is looked up through the reverse index. The obvious
# encoding — an attribute per mapping on the replay node — would make every lookup a scan, and `_carry`
# does one per mapping per frame. `bound ──mapping──▶ mapping` with `sources` answering backwards is O(few)
# and needs no index of our own to maintain.

KINDS = ("replay", "bound", "deviation")


def open_replay(g: Graph, wb: str, frames: tuple, *, bound: dict | None = None,
                notes=(), ran=()) -> str:
    """A replay of `frames`, positioned at the start and ready to be stepped.

    `bound`, `notes` and `ran` seed it — which is what `resume` needs: it continues a diverged execution
    from state that already exists rather than starting a second, blank one."""
    r = g.mint("replay", at=0, notes=tuple(notes), ran=tuple(ran))
    g.link(r, "workbench", wb)
    for f in frames:
        g.link(r, "frame", f)                   # Ordered — the path, and the position indexes into it
    for m, real in (bound or {}).items():
        bind(g, r, m, real)
    return r


def bind(g: Graph, r: str, mapping: str, real: str) -> str:
    """Say which real node a mapping stands for in this replay. Rebinding replaces, since `_settle` points
    the subject's mapping at the cast's result."""
    got = _binding(g, r, mapping)
    if got is None:
        got = g.mint("bound")
        g.link(got, "mapping", mapping)
        g.link(got, "in", r)                    # which replay this belongs to — see `_binding`
        g.link(r, "bound", got)
    while g.count(got, "node"):
        g.unlink(got, "node", index=0)
    g.link(got, "node", real)
    return got


def _binding(g: Graph, r: str, mapping: str):
    for s in g.sources(mapping, "mapping"):
        if g.kind(s) == "bound" and g.target(s, "in") == r:
            return s
    return None


def bound_to(g: Graph, r: str, mapping: str):
    got = _binding(g, r, mapping)
    return None if got is None else g.target(got, "node")


def is_bound(g: Graph, r: str, mapping: str) -> bool:
    return _binding(g, r, mapping) is not None


def bindings_of(g: Graph, r: str) -> dict:
    """`{mapping: real node}` — the dict the report has always carried, read back out of the graph."""
    return {g.target(b, "mapping"): g.target(b, "node") for b in g.targets(r, "bound")}


def _note(g: Graph, r: str, text: str) -> None:
    g.put(r, notes=g.attr(r, "notes", ()) + (text,))


def _ran(g: Graph, r: str, name: str) -> None:
    g.put(r, ran=g.attr(r, "ran", ()) + (name,))


def finished(g: Graph, r: str) -> bool:
    """Off the end of the path, or stopped by a deviation. A deviation is terminal for *this* replay —
    what happens next is `recover`'s decision, not a continuation of the same walk."""
    return (g.target(r, "deviation") is not None
            or g.attr(r, "at", 0) + 1 >= g.count(r, "frame"))


def _diverge(g: Graph, r: str, **fields) -> str:
    """Record the deviation on the replay. It is a node, so a stopped replay says why it stopped without
    the caller having to have been holding the return value at the moment it happened."""
    d = g.mint("deviation", **{k: v for k, v in fields.items()
                               if k not in ("frame", "transformation", "minted")})
    for label in ("frame", "transformation"):
        if fields.get(label) is not None:
            g.link(d, label, fields[label])
    for n in fields.get("minted", ()):
        g.link(d, "minted", n)
    g.link(r, "deviation", d)
    return d


def deviation_of(g: Graph, r: str):
    """The deviation as the dict every caller here already speaks — `None` if the replay is clean."""
    d = g.target(r, "deviation")
    if d is None:
        return None
    out = {k: v for k, v in g.attrs[d].items() if k != "kind"}
    out["frame"] = g.target(d, "frame")
    out["transformation"] = g.target(d, "transformation")
    out["minted"] = g.targets(d, "minted")
    return out


def report_of(g: Graph, r: str) -> dict:
    """The execution report. Unchanged in shape — this is a rendering of the replay node, not a second
    record of what happened."""
    dev = deviation_of(g, r)
    out = {"ran": g.attr(r, "ran", ()), "deviation": dev, "completed": dev is None,
           "bindings": bindings_of(g, r), "notes": g.attr(r, "notes", ()),
           "workbench": g.target(r, "workbench"), "replay": r}
    if g.target(r, "resumed_on") is not None:   # a resumed replay says so, as its report always did
        out["resumed_on"] = g.target(r, "resumed_on")
        out["resumed_assuming"] = g.attr(r, "resumed_assuming")
    return out


# --- carrying and settling ----------------------------------------------------------------------------
def _carry(g: Graph, r: str, prev: str, frame: str) -> None:
    """A node keeps its identity across frames, so its binding follows its mapping's successor."""
    for m in W.visible(g, prev):
        nxt = _successor_in(g, m, frame)
        if nxt is not None and is_bound(g, r, m):
            bind(g, r, nxt, bound_to(g, r, m))


def _settle(g: Graph, r: str, tr: str, frame: str, result, minted) -> None:
    """Record what a real call produced: bind the nodes it minted, and point the subject's mapping at the
    result — a cast returns its subject, so the first parameter's mapping now names the cast node."""
    _bind_minted(g, r, frame, minted)
    first_param = fn.subject_param(g, g.attr(tr, "function"))
    for b in g.targets(tr, "arg"):
        m = g.target(b, "mapping")
        if is_bound(g, r, m) and g.attr(b, "param") == first_param:
            bind(g, r, m, result)


def _bind_minted(g: Graph, r: str, frame: str, minted) -> None:
    """Match nodes the real call just created to the imagined mappings that predicted them."""
    pending = [m for m in W.visible(g, frame)
               if W.is_imagined(g, m) and not is_bound(g, r, m)]
    by_kind: dict = {}
    for n in minted:
        by_kind.setdefault(g.kind(n), []).append(n)
    for m in pending:
        want = g.kind(W.image_of(g, m))
        pool = by_kind.get(want, [])
        if not pool:
            _note(g, r, f"planned a {want} that the real call did not produce")
            continue
        if len(pool) > 1:
            _note(g, r, f"ambiguous: {len(pool)} real {want} nodes for a planned one — paired by order")
        bind(g, r, m, pool.pop(0))


# --- one STEP ------------------------------------------------------------------------------------------
def step(g: Graph, r: str) -> bool:
    """Advance the replay by one frame: carry the bindings across, and run that frame's call for real.
    Returns `True` while there is more to do.

    This is the one stepper whose steps are IRREVERSIBLE. An imagined step can be rewound and a
    search step costs only time; a step here reaches the world through `dispatch`, whose `commit()` is the
    honest admission that nothing after it can be undone. So the yield point matters more here than
    anywhere else — it is where *"should I do the next one?"* becomes an expressible question — and the
    asymmetry `dispatch.py` calls the single most important safety property in the design must survive it.
    Pausing between two real acts is a capability; making acting look like any other tick is not.

    A deviation is recorded and stops the replay: what to do about it is `recover`'s decision, and it needs
    the `frame`, the `transformation`, the real `result` and what the call `minted`, because the call is
    not re-run."""
    if finished(g, r):
        return False
    i = g.attr(r, "at", 0)
    frames = g.targets(r, "frame")
    prev, frame = frames[i], frames[i + 1]
    g.put(r, at=i + 1)
    _carry(g, r, prev, frame)

    tr = g.target(frame, "via")
    if tr is None:
        return not finished(g, r)
    name = g.attr(tr, "function")               # the real function, not the mock that was imagined
    args, missing = {}, []
    for b in g.targets(tr, "arg"):
        param, m = g.attr(b, "param"), g.target(b, "mapping")
        if is_bound(g, r, m):
            args[param] = bound_to(g, r, m)
        else:
            missing.append(param)
    if missing:
        _diverge(g, r, step=name, frame=frame, transformation=tr, result=None, minted=(),
                 why=f"unbound argument(s) {missing} — the plan referred to "
                     f"something that does not exist in the real graph")
        return False

    # A precondition that went false while we were NOT looking is a divergence, NOT a crash.
    # `fn.invoke` re-validates each parameter type at the call, which is the property that stops a plan
    # acting on a world it was not verified against — the *right* check in the right place. But it reports
    # by raising, and nothing between here and `loop.tick` caught it: the exception escaped the outer loop
    # entirely, stranding this pursuit mid-`acting` and killing every other task on the agenda with it.
    # A single-plan test cannot see that; it is exactly what concurrency makes routine.
    #
    # Recorded as an ordinary deviation, so the whole existing recovery ladder applies with no new
    # machinery. `result=None` is load-bearing rather than a placeholder: the call never ran, so
    # `matching_alternative` correctly declines to offer a contingency — there is no real outcome to settle
    # onto a sibling's mappings — and recovery goes to replanning, which is the honest move when the world
    # has moved rather than merely surprised us.
    try:
        # The other boundary, and the one that removes the last mode from the design. The real world is
        # not the *absence* of a context; it is the **trivial** one, whose resolution is the identity
        # function. So the same rule runs here unchanged — there is never mediated-versus-unmediated
        # execution to branch on, no rule with two behaviours, and forgetting to establish is the same
        # bug in the same place whether the system is planning or acting.
        #
        # It costs nothing: a context with no resolver makes the vocabulary skip the call entirely.
        called, out = fn.invoke(g, name, args,
                                under=access.open_context(g, label="the world"))
    except TY.TypeViolation as e:
        _diverge(g, r, step=name, frame=frame, transformation=tr, result=None, minted=(),
                 stale_precondition=True, param=getattr(e, "param", None),
                 expected=getattr(e, "want", None), violations=getattr(e, "violations", None),
                 # Ascii only: records the report being made unpipeable on a cp1252 console by one
                 # non-ascii glyph. And no `{e}` here - `expected` and `violations` above already carry it,
                 # and `report` prints them; repeating it says the same thing twice in one paragraph.
                 why=f"{name} could not be applied: its {getattr(e, 'param', '?')} no longer satisfies "
                     f"what it requires. The world moved after this plan was verified.")
        return False
    # Warn Read off the call itself, never off a whole-graph diff - `activation.minted`. The diff
    # counted every node that appeared while the call ran, the interpreter's own state included.
    minted = list(ACT.minted(g, ACT.for_focus(g, called.node)))
    result = out.get("result") or args.get(fn.subject_param(g, name))
    _ran(g, r, name)

    assumed = (g.attr(g.target(tr, "assumes"), "label")
               if g.target(tr, "assumes") else None)

    violations = W.deviates(g, tr, result)
    if violations:
        _diverge(g, r, step=name, frame=frame, transformation=tr, result=result, minted=minted,
                 expected=g.attr(tr, "expects"), violations=violations, assumed=assumed)
        return False

    _settle(g, r, tr, frame, result, minted)

    # The second, wider CHECK. The cast above asks whether one node satisfies one schema; this asks
    # whether the concrete things the step predicted actually happened — the file nodes materialised,
    # the count came back zero, the edge appeared. Checked AFTER `_settle` because binding what the
    # real call minted is what makes an imagined node addressable at all.
    #
    # The prediction is a **node** now, derived from the two frames and scrapped straight after — the
    # transient shape `reachable`'s walk established. It was a Python dict, and being one was the only
    # thing keeping `unmet_expectations` out of the surface: a predicate cannot be written there if what
    # it reads exists only in Python.
    prediction = W.predicted_changes(g, prev, frame)
    missed = W.unmet_expectations(g, prediction, bindings_of(g, r), minted)
    W.drop_prediction(g, prediction)
    if missed:
        _diverge(g, r, step=name, frame=frame, transformation=tr, result=result, minted=minted,
                 expected=g.attr(tr, "expects"), unmet_expectations=missed, assumed=assumed)
        return False
    return not finished(g, r)


def execute(g: Graph, wb: str, leaf: str) -> dict:
    """Replay the plan ending at `leaf` against the real graph.

    Returns a report: the steps that ran, the first deviation if any, the mapping-to-real bindings, and
    any notes about imagined nodes that could not be matched cleanly. The workbench travels in the report
    so recovery takes one argument — a deviation is only interpretable against the tree it came from.

    A loop over `step`, and nothing else — the same relationship `Machine.run` has to `Machine.tick`.
    A caller that wants to stop between two real actions drives `step` itself and owns the replay node."""
    r = open_execution(g, wb, leaf)
    while step(g, r):
        pass
    return report_of(g, r)


def open_execution(g: Graph, wb: str, leaf: str) -> str:
    """The replay `execute` would run, seeded and positioned at the start but not yet stepped.

    Extracted so there is one setup. `execute` calls it and loops; a pursuit being driven a tick at a
    time calls it and hands the node to the outer loop. Two setups that could drift is the defect shape
    this codebase keeps recording — a second one that forgot to seed frame 0's bindings would report every
    argument as unbound and call the plan impossible."""
    frames = path_to(g, wb, leaf)
    seed = {}
    for m in W.mappings(g, frames[0]):          # frame 0: these already exist for real
        real = W.resolve(g, m)
        if real is not None:
            seed[m] = real
    return open_replay(g, wb, frames, bound=seed)


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
def matching_alternative(g: Graph, wb: str, deviation: dict, result: dict | None = None):
    """The explored branch that assumed what reality actually did, or `None`.

    This is the whole payoff of forking deliberately: the test is the same `deviates` used to detect the
    problem, asked of each sibling's promise instead. A sibling that survives it is a plan for the world we
    are now in — imagined, checked, and needing no new thought.

    Restricted to siblings applying the same function. Siblings are alternative *successors*, which
    need not be alternative *outcomes*; a fork may try a different action. Resuming into one of those would
    silently skip a call that never ran, and the caller would be told the plan completed."""
    if not deviation or deviation.get("result") is None:
        return None
    for sib in alternatives(g, wb, deviation["transformation"]):
        tr = g.target(sib, "via")
        if tr is None or g.attr(tr, "function") != deviation["step"]:
            continue
        if W.deviates(g, tr, deviation["result"]):
            continue
        # A sibling must survive the same questions the failed branch did. When the divergence was a
        # broken prediction rather than a failed cast, matching the declared type is not enough — this
        # branch predicted concrete things too, and offering it without checking them would swap one wrong
        # assumption for another. Its bindings are carried from the shared parent, as `resume` does.
        if "unmet_expectations" in deviation and result is not None:
            parent = _parent_of(g, wb, sib)
            if parent is None:
                continue
            # A scratch replay, dropped afterwards. Asking "would this sibling have held up?" means
            # settling reality onto its mappings, and doing that on the live replay would answer the
            # question by committing to it. The dict this used to copy was doing the same job; a node has
            # to be scrapped explicitly, which is the one cost of the state being real.
            scratch = open_replay(g, wb, (), bound=dict(result["bindings"]))
            _carry(g, scratch, parent, sib)
            _settle(g, scratch, tr, sib, deviation["result"], list(deviation["minted"]))
            prediction = W.predicted_changes(g, parent, sib)
            missed = W.unmet_expectations(g, prediction, bindings_of(g, scratch),
                                          list(deviation["minted"]))
            W.drop_prediction(g, prediction)
            discard_replay(g, scratch)
            if missed:
                continue
        return sib
    return None


def discard_replay(g: Graph, r: str) -> None:
    """Scrap a replay and its bindings. Used for the scratch one `matching_alternative` reasons over."""
    for b in tuple(g.targets(r, "bound")):
        g.drop(b)
    d = g.target(r, "deviation")
    if d is not None:
        g.drop(d)
    g.drop(r)


def resume_replay(g: Graph, result: dict, *, branch=None, leaf=None):
    """Set up the continuation of a diverged execution down a branch that assumed what actually happened,
    and return the replay node, ready to be stepped. `None` if there is no such branch.

    Split from `resume` so recovery is steppable too. An outer loop that could pause between two acts of
    the original plan but not between two acts of its contingency would have a seam exactly where things
    have already started going wrong — which is the worst place to lose the ability to stop.

    The diverged call is not re-run. It reached the world once; running it again would double its
    effects and is the single thing most likely to be got wrong here. Instead its real outcome is settled
    onto the chosen branch's *own* mappings — carried from the shared parent frame, since siblings do not
    share mapping nodes — and replay picks up at the step after it.

    `leaf` chooses among several ends below the branch; the default takes the first, matching the planner's
    first-solution-wins discipline rather than pretending to arbitrate."""
    wb, dev = result["workbench"], result["deviation"]
    branch = branch if branch is not None else matching_alternative(g, wb, dev, result)
    if branch is None:
        return None
    parent = _parent_of(g, wb, branch)
    tr = g.target(branch, "via")
    if parent is None or tr is None:
        return None

    if leaf is None:
        leaf = leaves_under(g, wb, branch)[0]
    path = path_to(g, wb, leaf)
    # A fresh replay seeded from the diverged one's state — not a continuation of it. The old replay
    # stopped on a deviation and that is a fact about it; carrying on inside it would erase the record of
    # where it stopped, which is the one thing recovery is reasoning from.
    r = open_replay(g, wb, path[path.index(branch):],
                    bound=dict(result["bindings"]), notes=result["notes"], ran=result["ran"])
    g.link(r, "resumed_on", branch)
    g.put(r, resumed_assuming=g.attr(tr, "expects"))
    _carry(g, r, parent, branch)
    _settle(g, r, tr, branch, dev["result"], list(dev["minted"]))
    return r


def resume(g: Graph, result: dict, *, branch=None, leaf=None):
    """`resume_replay` run to completion — a loop over `step`, like `execute`."""
    r = resume_replay(g, result, branch=branch, leaf=leaf)
    if r is None:
        return None
    while step(g, r):
        pass
    return report_of(g, r)


def replan(g: Graph, result: dict, want: str, *, subject=None, depth: int = 8):
    """Propose afresh from the world as it actually is. Returns a lazy chain, or `None` if nothing in
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
        for missed in dev.get("unmet_expectations", ()):
            lines.append(f"  {missed}")
        if dev.get("why"):
            lines.append(f"  {dev['why']}")
    lines.extend(f"  note: {n}" for n in result["notes"])
    return "\n".join(lines)


__all__ = ["KINDS", "path_to", "leaves_under", "execute", "alternatives",
           "matching_alternative", "resume", "replan", "recover", "report",
           "open_replay", "step", "finished", "resume_replay", "report_of", "deviation_of", "bindings_of",
           "bind", "bound_to", "is_bound", "discard_replay"]

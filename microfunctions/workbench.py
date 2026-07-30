"""WORKBENCH — imagining what functions would do, on a copy, frame by frame.

Design: `docs/microfunctions/planning_workbench.md`. This is stage 1 — copy, mappings, frames,
transformations, forking and discard. Mocks and the dispatch refusal come next.

**Why this exists.** `plan.py` chains declared *types*: if `service` is declared `car -> serviced_car`, it
concludes that applying it yields a serviced car. That is a promise, not a proof, and it says nothing about
what *else* changed — which the next step may depend on. So backward chaining is a good way to **propose** a
chain and a bad way to **believe** one. The workbench actually runs the proposal somewhere that does not
count, and reports what really happened.

**The copy boundary is everything reachable from the subject.** Every cleverer boundary is a guess about
which structure will matter, and a wrong guess yields a plan that looks fine and fails on contact with
reality. We genuinely cannot know in advance what a plan will need. The cost is accepted; copy-on-write, if
it is ever needed, implements exactly these semantics more cheaply rather than being a smaller boundary.

**Mappings are the crux.** A mapping node points at the original and at this frame's image, and chains to
the next frame via `next`. Transformations bind their arguments to **mappings, never raw workbench nodes** —
which is what makes a plan replayable, since following `original` yields the node the operation must really
be applied to. A log saying "`service` was applied" is unreplayable: it does not identify the subject in a
form that survives out of the workbench.

**⚠ The direction invariant.** A mapping points *to* the original and the image; nothing ever points from a
node to its mappings. Copying traverses outgoing edges, so a single edge the other way would drag in that
mapping's original, image and `next` — and thence every frame, every workbench, every plan that ever touched
the node. Not a wrong answer: an unbounded copy. The constraint is free, because the reverse index already
answers the backward question (`sources(node, "original")`).

**Frames form a tree, not a list.** Successive steps extend a path; assumptions fork it. `next` is 1:N on
both frames and mappings, so a node's history branches with the frames it lives in.
"""
from __future__ import annotations

from . import function as fn
from . import hypothesis
from .graph import Graph


# --- copying ----------------------------------------------------------------------------------------
def reachable(g: Graph, start: str) -> set:
    """Everything reachable from `start` by outgoing edges. The copy boundary, per the design decision.

    Metadata is not reached, by the direction invariant — mappings, applications, hypotheses and plans all
    point *at* domain nodes and are never pointed at by them."""
    seen, stack = set(), [start]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        for label in g.labels(n):
            stack.extend(t for t in g.targets(n, label) if t not in seen)
    return seen


def _copy_set(g: Graph, originals: set) -> dict:
    """Copy nodes and the edges among them. Returns `{original: image}`.

    Edge properties are carried across positionally, which is safe because targets are appended in the
    same order they appear in the source."""
    image = {}
    for o in originals:
        attrs = {k: v for k, v in g.attrs.get(o, {}).items() if k != "kind"}   # `kind` is positional
        image[o] = g.mint(g.kind(o) or "node", **attrs)
    for o in originals:
        for label in g.labels(o):
            for i, t in enumerate(g.targets(o, label)):
                if t in image:
                    props = g.eprops.get((o, label, i), {})
                    g.link(image[o], label, image[t], **props)
    return image


# --- opening ----------------------------------------------------------------------------------------
def open_workbench(g: Graph, subject: str, *, label: str = "workbench",
                   parent: str | None = None, explores: str | None = None) -> str:
    """Copy everything reachable from `subject` into a fresh workbench, and mint frame 0 with one mapping
    per copied node.

    `parent` nests this workbench inside another — subgoal exploration. `explores` attaches the hypothesis
    whose assumptions this workbench is investigating; hypotheses are *run* via workbenches rather than
    being a separate mechanism.

    ⚠ In a nested workbench a mapping's `original` points one level up, not at the real graph, so resolving
    to a real node is a walk (`resolve`), not a hop."""
    wb = g.mint("workbench", label=label, depth=(g.attr(parent, "depth", 0) + 1) if parent else 0)
    if parent is not None:
        g.link(wb, "parent", parent)
    if explores is not None:
        g.link(wb, "explores", explores)
    g.link(wb, "subject", subject)

    originals = reachable(g, subject)
    image = _copy_set(g, originals)
    frame = g.mint("frame", index=0)
    g.link(wb, "root_frame", frame)
    g.link(wb, "frame", frame)          # membership, distinct from the `next` tree that gives shape
    for o, img in image.items():
        m = g.mint("mapping")
        g.link(m, "original", o)          # points OUT — never pointed at, see the invariant
        g.link(m, "image", img)
        g.link(frame, "mapping", m)
    return wb


# --- reading ----------------------------------------------------------------------------------------
def root_frame(g: Graph, wb: str):
    return g.target(wb, "root_frame")


def mappings(g: Graph, frame: str) -> tuple:
    return g.targets(frame, "mapping")


def mapping_for(g: Graph, frame: str, original: str):
    """The mapping in `frame` whose `original` is `original` — O(#mappings pointing at it) via the reverse
    index rather than a scan of the frame."""
    for m in g.sources(original, "original"):
        if g.kind(m) == "mapping" and m in g.targets(frame, "mapping"):
            return m
    return None


def image_of(g: Graph, mapping: str):
    return g.target(mapping, "image")


def resolve(g: Graph, mapping: str):
    """Walk `original` upward until leaving every workbench, and return the REAL node.

    Returns `None` for a node that exists only in imagination — one minted during planning, which has no
    `original` at all. ⚠ Those two cases must not be conflated: "no original" means *this does not exist
    yet and must be created when the plan runs*, and what ties it to reality later is the transformation
    that produced it, not a pointer."""
    node = g.target(mapping, "original")
    # A node is a workbench copy exactly when some mapping points at it as an `image` — derived from the
    # structure, never asserted by a marker, and O(1) via the reverse index.
    while node is not None and any(g.kind(m) == "mapping" for m in g.sources(node, "image")):
        up = [m for m in g.sources(node, "image") if g.kind(m) == "mapping"]
        node = g.target(up[0], "original") if up else None
    return node


def is_imagined(g: Graph, mapping: str) -> bool:
    """True for a node minted during planning — it has no `original` anywhere up the stack."""
    return g.target(mapping, "original") is None


def frames(g: Graph, wb: str) -> tuple:
    """Every frame, breadth-first from the root. A tree, not a list — assumptions fork it."""
    return g.targets(wb, "frame")


def history(g: Graph, mapping: str) -> tuple:
    """A node's own timeline: this mapping and everything downstream of it.

    ⚠ `next` is 1:N, because frames fork — so a node's history is a tree mirroring the frame tree, and
    this returns all of it. Code that assumed a single successor would silently follow one branch."""
    out, queue = [], [mapping]
    while queue:
        m = queue.pop(0)
        out.append(m)
        queue.extend(g.targets(m, "next"))
    return tuple(out)


# --- stepping ---------------------------------------------------------------------------------------
def step(g: Graph, wb: str, frame: str, function: str, bindings: dict, *,
         assumes: str | None = None, assume: str | None = None):
    """Run `function` on a NEW frame derived from `frame`, and record the transformation.

    `bindings` maps parameter name to a **mapping** in `frame` — never a raw node, so the record stays
    replayable. Returns `(new_frame, transformation)`.

    The previous frame is left intact because the new frame is a full copy taken *before* the function
    runs. That is what makes the movie real: every earlier state remains inspectable rather than being
    reconstructible only by replay.

    `assumes` records the hypothesis this step took on faith — which is how a plan carries its own
    dependence on guesses, inspectably."""
    prev_images = {m: image_of(g, m) for m in mappings(g, frame)}
    originals = set(prev_images.values())
    image = _copy_set(g, originals)

    new_frame = g.mint("frame", index=g.attr(frame, "index", 0) + 1)
    g.link(wb, "frame", new_frame)
    carried = {}
    for m, prev_img in prev_images.items():
        nm = g.mint("mapping")
        src = g.target(m, "original")
        if src is not None:
            g.link(nm, "original", src)       # keep pointing one level up, not at the previous frame
        g.link(nm, "image", image[prev_img])
        g.link(m, "next", nm)                 # 1:N — forks when the frame forks
        g.link(new_frame, "mapping", nm)
        carried[m] = nm

    # ⭐ MOCK SUBSTITUTION. On a workbench, a function that has declared outcomes is replaced by one of
    # them — always, not by convention. `assume` names which; the default is the most preferred, i.e. the
    # first declared, since `mock` is an ordered edge.
    #
    # ⚠ This is a *convenience*, not the safety mechanism. Safety is `dispatch.service` refusing an
    # imagined target: if this substitution were forgotten or bypassed, a dispatching function would still
    # be unable to reach the world. Substitution makes planning *useful*; the refusal makes it *safe*, and
    # conflating the two would put the guarantee in the wrong place.
    outcomes = fn.mocks_of(g, function)
    chosen = assume if assume is not None else (outcomes[0] if outcomes else None)
    if chosen is not None and chosen not in outcomes:
        raise KeyError(f"{chosen!r} is not a declared outcome of {function!r}; known: {outcomes}")
    executed = chosen or function

    args = {p: image_of(g, carried[m]) for p, m in bindings.items()}
    before = set(g.nodes)
    fn.invoke(g, executed, args)

    # A function may MINT something while imagining. Those nodes get mappings too, with **no `original`** —
    # which is meaningful rather than broken: it says *this does not exist yet and must be created when the
    # plan runs for real*. What ties such a node to reality later is not a pointer but the transformation
    # that produced it, which is recorded anyway. Without this, `is_imagined` could never fire and
    # execution would have nothing to bind a newly minted real node to.
    for n in sorted(set(g.nodes) - before):
        m = g.mint("mapping")
        g.link(m, "image", n)
        g.link(new_frame, "mapping", m)

    # Choosing an outcome IS making an assumption, so it becomes a hypothesis the transformation records.
    # That is what lets a plan carry its own dependence on guesses: "which parts of this are fragile"
    # becomes a lookup rather than a judgement someone has to remember to make.
    if chosen is not None and assumes is None:
        assumes = hypothesis.open_hypothesis(
            g, f"{function} turns out {fn.returns_of(g, chosen) or chosen}")

    tr = g.mint("transformation", function=function, executed=executed,
                expects=fn.returns_of(g, executed))
    g.link(tr, "applies", fn.find(g, function))
    for param, m in bindings.items():
        b = g.mint("binding", param=param)
        g.link(b, "mapping", carried[m])      # binds the MAPPING, not the raw node
        g.link(tr, "arg", b)
    if assumes is not None:
        g.link(tr, "assumes", assumes)
    g.link(frame, "next", new_frame)
    g.link(new_frame, "via", tr)
    return new_frame, tr


def fork(g: Graph, wb: str, frame: str, function: str, bindings: dict, *,
         assumes: str | None = None, assume: str | None = None):
    """An alternative successor of the same frame — a different assumed outcome.

    Identical to `step`; named separately because the intent differs and the frame tree's shape is the
    thing a reader is trying to understand. An abandoned fork stays as data: a dead end that was explored
    and rejected is exactly what is worth not re-exploring."""
    return step(g, wb, frame, function, bindings, assumes=assumes, assume=assume)


def discard(g: Graph, wb: str) -> None:
    """Scrap the workbench — every frame, mapping and copied node. Bail out and start again."""
    for f in frames(g, wb):
        for m in mappings(g, f):
            img = image_of(g, m)
            if img is not None:
                g.drop(img)
            g.drop(m)
        via = g.target(f, "via")
        if via is not None:
            for b in g.targets(via, "arg"):   # bindings are the transformation's own nodes; they leak
                g.drop(b)                     # otherwise, since nothing else points at them
            g.drop(via)
        g.drop(f)
    g.drop(wb)


def deviates(g: Graph, transformation: str, real_result) -> dict:
    """Did reality match what this transformation predicted? Empty dict means it did.

    **Deviation is a failed cast**, which is why it is cheap: the transformation already records what type
    it expected, and checking it is `types.is_a` — bounded, and already written. Comparing whole subgraphs
    would be expensive and noisy, and irrelevant differences would swamp the real ones. The expected type
    is the honest signal because it is exactly the promise the function made.

    Returns the type violations, so a caller reporting a deviation can say *how* it deviated rather than
    only *that* it did."""
    from .types import violations
    expected = g.attr(transformation, "expects")
    return {} if expected is None else violations(g, real_result, expected)


def assumption_of(g: Graph, transformation: str):
    """The hypothesis this step took on faith, or `None` if it assumed nothing."""
    return g.target(transformation, "assumes")


def fragile_steps(g: Graph, wb: str) -> tuple:
    """Every transformation in this workbench that rests on an assumption — the plan's own account of
    where it is guessing. This is the payoff of recording assumptions rather than merely making them."""
    out = []
    for f in frames(g, wb):
        tr = g.target(f, "via")
        if tr is not None and assumption_of(g, tr) is not None:
            out.append(tr)
    return tuple(out)


__all__ = ["deviates", "assumption_of", "fragile_steps", "reachable", "open_workbench", "root_frame", "mappings", "mapping_for",
           "image_of", "resolve", "is_imagined", "frames", "history", "step", "fork", "discard"]

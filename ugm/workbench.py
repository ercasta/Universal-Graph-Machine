"""Workbench — imagining what functions would do, on a copy, frame by frame.

Backward chaining over declared types concludes that applying `service` to a car yields a
serviced car. That is a promise rather than a proof, and it says nothing about what else changed,
which the next step may depend on. So type chaining is a good way to propose a chain and a bad
way to believe one; the workbench runs the proposal somewhere that does not count and reports
what really happened.

The copy boundary is everything reachable from the subject. Every cleverer boundary is a guess
about which structure will matter, and a wrong guess yields a plan that looks fine and fails on
contact with reality. That boundary is paid for **once**, at frame 0: a frame maps only what
changed in it, so a step mints a version of what it wrote and inherits everything else. Copy-on-
write, which is what the writer in `rules/version.mf` does, implements exactly these semantics
rather than being a smaller boundary.

**An edge names an identity, never a version, and resolution happens on the target.** That one
sentence is what makes a sparse frame correct, and nothing rewrites an edge anywhere: a copy of
`b` keeps saying `on c`, where `c` is the thing itself, and which version of `c` that means is
decided when the edge is read. Rewriting was what made a frame a container; it is also what made
sharing impossible, because a version minted in frame N would have had to point at frame N's copy
of everything it touched, and a sparse frame has no such copy. `b on c` then read as false one
step after it became true, which is how the model was arrived at.

Mappings are the crux. A mapping points at the identity and at this frame's image, and chains to
the next frame. Transformations bind their arguments to mappings, never to raw workbench nodes,
which is what makes a plan replayable: following the original yields the node the operation must
really be applied to. A log saying "`service` was applied" is unreplayable, because it does not
identify the subject in a form that survives out of the workbench.

A rule, however, is bound to the **identity** — the real node in both worlds — so one rule has one
behaviour and only what a read means differs. The corollary is sharp: a rule that touches the graph
*bare* no longer lands in the frame by luck, it writes to reality. `access.offenders` is the pass
that says so.

The direction invariant. A mapping points to the original and the image, and nothing ever points
from a node to its mappings. Copying traverses outgoing edges, so a single edge the other way
would drag in that mapping's original, image and successor, and thence every frame, every
workbench and every plan that ever touched the node. That is not a wrong answer but an unbounded
copy. The constraint is free, because the reverse index already answers the backward question.

Frames form a tree rather than a list. Successive steps extend a path and assumptions fork it,
and successor edges are one-to-many on both frames and mappings, so a node's history branches
with the frames it lives in.

Expectations are derived from the frames rather than authored: frame N-1 and frame N are the
before and after. They are qualitative rather than quantitative, because a mock that mints two
nodes is giving a witness rather than a promise.

Scans exclude workbench copies by default. Copies are ordinary nodes, so an unfiltered scan would
find the system's own imaginings and offer them as candidate arguments — planning about the
products of planning, with no error and no symptom beyond gradually stranger plans.

See `docs/planning.md`.
"""
from __future__ import annotations

from . import access
from . import activation as ACT
from . import function as fn
from . import hypothesis
from .graph import Graph


# --- copying ----------------------------------------------------------------------------------------
def reachable(g: Graph, start: str, *, view=None) -> dict:
    """Everything reachable from `start` by outgoing edges. The copy boundary, per the design decision.

    `view` is *the world as seen in one frame* (see `View`). An edge names an identity, so inside a frame
    a traversal that followed raw targets would walk out of the imagined world and into the real one at
    the first hop — which is how `types.instances(under=<a frame's image>)` would enumerate real blocks
    and answer a type goal against a world the plan is not in. With a view, every hop resolves.

    Metadata is not reached, by the direction invariant — mappings, applications, hypotheses and plans all
    point *at* domain nodes and are never pointed at by them.

    Returns an ordered set (a dict used as one), and the order is load-bearing. The traversal itself
    is already deterministic — `g.labels` is sorted and `g.targets` is an insertion-ordered tuple — so the
    visit order is a fact about the graph. Returning a `set` threw it away and substituted the iteration
    order of the node-id *strings*, which is a fact about nothing: ids come from a process-global counter,
    so the same world built twice in one process gets different ids, hashes in a different order, and is
    copied in a different order. That reached all the way up to `driver.pursue`, whose frontier breaks
    ties by insertion order — making the search irreproducible: the identical five-block goal was
    measured at 12 imagined states, 306, and budget-exhausted-failure on consecutive runs of one process.

    Nothing was ever *lost* — the set of proposals is identical every time — so this never produced a wrong
    plan, only an arbitrary one, at an arbitrary cost. That is exactly why it survived: every check still
    passed, and only a measurement repeated in one process could see it.

    A dict rather than a tuple so membership stays O(1) for the callers that only ask `in`."""
    seen, stack = {}, [start]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen[n] = None
        for label in g.labels(n):
            for t in g.targets(n, label):
                if view is not None:
                    t = view(t) or t          # unmapped means outside the imagined world: itself
                if t not in seen:
                    stack.append(t)
    return seen


def _copy_set(g: Graph, originals) -> dict:
    """Copy nodes, with their edges pointing where the originals' did. Returns `{original: image}`.

    **The edges are not rewritten**, and that is the model rather than an economy. An edge names an
    identity and resolution happens on the *target*, so there is no parallel world to rewrite into: a
    copy of `b` keeps saying `on c`, where `c` is the thing itself, and which version of `c` that means
    is decided when the edge is read, in whatever frame is reading it.

    Rewriting was what made a frame a container. It is also what made sharing impossible: a version
    minted in frame N would have had to point at frame N's copy of everything it touched, and there is
    no such copy, because a sparse frame only has copies of what changed. Reading `b on c` one step after
    it became true then answered with the version `c` had *before*, which is the failure this whole
    change exists to remove.

    Edge properties are carried across positionally, which is safe because targets are appended in the
    same order they appear in the source.

    `originals` must be an ordered collection, because minting walks it and the ids it mints decide
    the order of the resulting mappings — see `reachable`. Passing a `set` here is the defect that made
    the search irreproducible."""
    image = {}
    for o in originals:
        attrs = {k: v for k, v in g.attrs.get(o, {}).items() if k != "kind"}   # `kind` is positional
        image[o] = g.mint(g.kind(o) or "node", **attrs)
    for o in originals:
        for label in g.labels(o):
            for i, t in enumerate(g.targets(o, label)):
                # Edge properties are keyed by edge id now, not by `(src, label, index)`.
                # Reading the old key here returned `{}` silently, so a copied edge quietly lost its
                # properties — and nothing failed, because no check copied one. See the check that
                # now does.
                props = g.edge_props(g.edge_at(o, label, i))
                g.link(image[o], label, t, **props)
    return image


# --- opening ----------------------------------------------------------------------------------------
def _ensure_workbench(g: Graph) -> None:
    """Make sure this graph has the surface `open_workbench` and what it stands on. Idempotent.

    Same argument and same shape as `_ensure_step` and `access.bootstrap`: a name is only meaning if
    something answers it, so resolving it belongs where the call is made."""
    from pathlib import Path
    from . import asm
    here = Path(__file__).parent / "rules"
    if fn.find(g, "copy_node") is None:
        asm.load_file(g, here / "reachable.mf")
    if fn.find(g, "open_workbench") is None:
        asm.load_file(g, here / "workbench.mf")


def open_workbench(g: Graph, subject: str, *, label: str = "workbench",
                   parent: str | None = None, explores: str | None = None) -> str:
    """Open a workbench on `subject` — **the implementation is `rules/workbench.mf`**.

    A wrapper, in the shape `step` established: it resolves the implementation, invokes it, and returns
    what every caller already read. `_python_open_workbench` is kept below as the reference the
    comparison check runs against, and it is also the last caller of `reachable` + `_copy_set` in the
    copying sense — the live path reaches those through `rules/reachable.mf`.

    `access.bootstrap` still happens here rather than in the surface. A workbench is where framed
    resolution begins, so the resolver has to exist by the time one is opened; the surface cannot
    bootstrap the vocabulary it is written in.

    `parent` nests this workbench inside another — subgoal exploration. `explores` attaches the
    hypothesis whose assumptions it investigates."""
    access.bootstrap(g)
    _ensure_workbench(g)
    return fn.invoke(g, "open_workbench",
                     {"subject": subject, "label": label, "parent": parent, "explores": explores},
                     retain=False)[1]["result"]


def _python_open_workbench(g: Graph, subject: str, *, label: str = "workbench",
                           parent: str | None = None, explores: str | None = None) -> str:
    """Copy everything reachable from `subject` into a fresh workbench, and mint frame 0 with one mapping
    per copied node.

    **No longer the live implementation** — `open_workbench` above invokes `rules/workbench.mf`. Kept as
    the reference that version is checked against, in
    `check_REFLECTION_makes_open_workbench_an_ORDINARY_PROGRAM`.

    `parent` nests this workbench inside another — subgoal exploration. `explores` attaches the hypothesis
    whose assumptions this workbench is investigating; hypotheses are *run* via workbenches rather than
    being a separate mechanism.

    In a nested workbench a mapping's `original` points one level up, not at the real graph, so resolving
    to a real node is a walk (`resolve`), not a hop."""
    # A workbench is where framed resolution begins, so this is where the resolver has to exist. It used
    # to arrive only through `asm.load_text` linking a rule that called the vocabulary, which was enough
    # while nothing but a rule ever resolved; `function.invoke` now resolves a parameter type before the
    # body runs, and a graph that had never loaded a mediated rule would have established a context
    # naming a function that was not there. Idempotent, and once per workbench rather than once per step.
    access.bootstrap(g)
    wb = g.mint("workbench", label=label, depth=(g.attr(parent, "depth", 0) + 1) if parent else 0)
    if parent is not None:
        g.link(wb, "parent", parent)
    if explores is not None:
        g.link(wb, "explores", explores)
    g.link(wb, "subject", subject)

    originals = reachable(g, subject)
    image = _copy_set(g, originals)
    frame = g.mint("frame", index=0)                  # frame 0 maps everything, always
    g.link(wb, "root_frame", frame)
    g.link(wb, "frame", frame)          # membership, distinct from the `next` tree that gives shape
    for o, img in image.items():
        m = g.mint("mapping")
        g.link(m, "original", o)          # points out — never pointed at, see the invariant
        g.link(m, "image", img)
        g.link(frame, "mapping", m)
        index(g, frame, o, m)
    return wb


# --- reading ----------------------------------------------------------------------------------------
def root_frame(g: Graph, wb: str):
    return g.target(wb, "root_frame")


def mappings(g: Graph, frame: str) -> tuple:
    """What this frame maps **itself** — which is what *changed* in it, once frames are sparse.

    Distinct from `visible`, and the distinction is the whole of sparseness. While every frame carried a
    mapping for every node the two questions had the same answer, so one name served both; they are
    different questions and separating them is what lets a frame stop being a container and become a
    marker. Two facts on one edge, in the shape this codebase keeps recording."""
    return g.targets(frame, "mapping")


def previous(g: Graph, frame: str):
    """The frame this one was derived from, or `None` at the root.

    Read off `frame -next-> frame` backwards. The reverse index sorts by node id, which is normally a
    trap here — but a frame has exactly one predecessor, and a one-element answer has no order to get
    wrong. Where that is not true (`mapping -next-> mapping` forks, and so do frames forwards) the
    forward edge is the one to read."""
    got = [f for f in g.sources(frame, "next") if g.kind(f) == "frame"]
    return got[0] if got else None


def chain(g: Graph, frame: str) -> tuple:
    """This frame and every frame it was derived from, nearest first. Resolution's search path.

    Termination is trivial and worth contrasting with `path.reaches`, which needs a seen-set because the
    world has cycles: this walks the *frame* chain, which is a history, and a history does not loop. The
    guard below is against a malformed graph rather than an ordinary one."""
    out, seen = [], set()
    while frame is not None and frame not in seen:
        seen.add(frame)
        out.append(frame)
        frame = previous(g, frame)
    return tuple(out)


def index(g: Graph, frame: str, identity: str, mapping: str) -> None:
    """Record that `identity`'s version in this frame is `mapping`.

    A stored reference, which is the substrate's O(1) key-to-node map — `SETREF`/`DEREF`, keyed by a
    string, and a node id is a string. Nothing about that mechanism knows what a frame is: it is
    semantic-agnostic, and the *decision* to key it by identity belongs to this layer. That is the
    horizon in its usual place, and it is why the surface can read the very same index with one `DEREF`
    rather than growing a second walk that would have to agree with this one.

    It replaces a search. Locating a version used to mean asking the reverse index which mappings name
    this node and then asking each of them which frame it sat in — O(versions) with an allocation per
    hop, and ambiguous besides, because `execution.bind` points at a mapping under the same label a frame
    does. An index answers in one lookup, and that ambiguity cannot arise in it.

    Written by whoever mints the mapping, since that is the only place that knows: `open_workbench`,
    `step`, and the writer in `rules/version.mf`."""
    g.set_ref(frame, identity, mapping)


def mapping_for(g: Graph, frame: str, original: str):
    """The version of `original` in force in `frame` — this frame's, or the nearest ancestor's.

    **Reading walks the frame chain**, which is what makes a sparse frame correct: a frame maps only what
    changed in it, so *not here* means *unchanged*, and unchanged means whatever the previous frame said.
    A node nothing has touched resolves all the way to frame 0.

    Found through the reverse index and never by scanning a frame. The mappings that name this node are
    exactly the sources of its `original` edge — one per frame it has a version in — and each of those
    knows its own frame the same way. Scanning `frame`'s mappings instead is O(world) per read, which is
    the cost this whole layer exists to stop paying."""
    if original is None:
        return None
    for f in chain(g, frame):
        m = g.deref(f, original)
        if m is not None:
            return m
    return None


def visible(g: Graph, frame: str) -> tuple:
    """Every mapping in force in this frame — the nearest version of each thing, nothing twice.

    This is *the world as imagined here*, and it is what enumeration, goal checking and execution mean
    when they ask a frame what is in it. `mappings` answers the other question — what this frame changed.

    **In the order the world was first laid out, not in the order it changed**, and that distinction
    only appeared once frames went sparse. Walking nearest-first and keeping the first answer puts
    whatever this step touched at the front, so the order of the world differed in every frame — and this
    order is `proposals` order, which is the search's last tie-break. The search stayed deterministic and
    became *worse*: Sussman's anomaly went from solved inside 60 imagined states to needing about 100,
    with nothing wrong in any single answer. Walking oldest-first and letting later versions replace
    earlier ones in place keeps frame 0's order — a fact about the world — while still answering with the
    version in force. Same determinism argument as `reachable` and `_copy_set`, one level up."""
    seen = {}
    for f in reversed(chain(g, frame)):
        for m in mappings(g, f):
            key = g.target(m, "original") or m       # an imagined node stands for itself
            seen[key] = m                            # a dict keeps the position of the FIRST insertion
    return tuple(seen.values())


def image_of(g: Graph, mapping: str):
    return g.target(mapping, "image")


def identity_of(g: Graph, node):
    """What `node` is a version OF, one level up — or the node itself.

    **The one hop, not the whole walk.** `original_of` resolves out of every workbench and answers with
    the real node; this answers with the identity *this* workbench keys its frames by, which in a nested
    workbench is the enclosing one's image. It is `in_frame`'s first move written in Python, and the two
    have to agree or a read means one thing in a rule and another in a reader.

    A node is the `image` of at most one mapping, so there is nothing to choose between — which matters,
    because `g.sources` sorts by node id and an ordered answer here would be an accident.

    An imagined node is **its own identity**, and says so positively: its first mapping points `original`
    at the node itself, so *this exists only in imagination* is a fact in the graph rather than the absence
    of one. Every later version of it names that first node, which is what lets `visible` recognise two
    versions of one imagined thing as one thing."""
    if node is None:
        return None
    for m in g.sources(node, "image"):
        if g.kind(m) == "mapping":
            return g.target(m, "original") or node
    return node


class View:
    """The world as seen in one frame: a node, resolved to the version in force here.

    Callable, so every existing caller that was handed a function still works — `goal.py` takes one of
    these and learns nothing about workbenches, which is the layering it has always insisted on.

    Two questions, not one, and separating them is what an identity-pointing edge needs. `view(n)` goes
    *down* from an identity to the version; `view.identity(n)` goes *up* from a version to the identity
    a constraint, a binding or another edge names. A traversal inside a frame needs both: follow an edge
    to an identity, resolve it to the version, read that version's edges.

    Idempotent, exactly as `in_frame` is: handed a version it normalises first, so a caller never has to
    know which of the two it is holding. The Python and the surface resolver would otherwise disagree
    about a node that had been round-tripped, which is the drift this codebase keeps recording."""
    __slots__ = ("g", "frame")

    def __init__(self, g: Graph, frame: str):
        self.g, self.frame = g, frame

    def identity(self, node):
        return identity_of(self.g, node)

    def __call__(self, node):
        if node is None:
            return None
        m = mapping_for(self.g, self.frame, identity_of(self.g, node))
        # `None` for a node this frame has never heard of, which stays distinct from *the node itself*:
        # `goal.holds` reads it as *not present in this world at all*.
        return image_of(self.g, m) if m is not None else None


def view_at(g: Graph, ctx):
    """The world a **context** describes, as a `View` — or `None` for the real one.

    This is the one place that knows a planning context points at a frame, which keeps `access.py` free
    of any idea of what a frame is. Split out of `view_of` because two different questions arrive here:
    a native holds an *activation* and has to walk to the context, while a Python caller standing at a
    boundary already holds the context itself. Before the split the second had no way in and passed a
    `View` alongside — which is the doubling that kept `goal.holds` in Python, since one caller then
    carried both a view and a context and nothing made them agree."""
    frame = g.target(ctx, "frame") if ctx is not None else None
    return View(g, frame) if frame is not None else None


def view_of(g: Graph, act):
    """The world an activation is running in, as a `View` — or `None` for the real one.

    The bridge a **native** crosses to obey the context. A rule reaches the graph through the closed
    vocabulary and is mediated by construction; a native reads raw structure, so it has to ask. It asks
    the same way everything else does — dynamic scope over the activation chain."""
    from . import access
    return view_at(g, access.context_of(g, act))


def original_of(g: Graph, node):
    """The real node an imagined one stands for — `view_in`'s inverse, and identity for a real node.

    `driver.view_in` translates a real individual into this frame's image of it; every reader that
    computes something *inside* a frame and then has to compare it against a constraint (which names real
    individuals) needs the way back. That way existed only as an inline idiom, which is the shape a missing
    reader makes — see `path.py`, which was three undeclared copies of one grammar.

    Derived from structure, never marked: a node is an image exactly when a mapping points at it as
    `image`, and O(1) through the reverse index. A node minted purely in imagination resolves to `None`
    (it has no original), which callers must keep distinct from *a real node that is its own answer*."""
    if node is None:
        return None
    for m in g.sources(node, "image"):
        if g.kind(m) == "mapping":
            return resolve(g, m)
    return node


def resolve(g: Graph, mapping: str):
    """Walk `original` upward until leaving every workbench, and return the real node.

    Returns `None` for a node that exists only in imagination — one minted during planning. Those two
    cases must not be conflated: *no real node* means *this does not exist yet and must be created when
    the plan runs*, and what ties it to reality later is the transformation that produced it, not a
    pointer.

    An imagined node is its own identity, so the walk ends at a node whose `original` is itself. That is
    the stopping condition rather than a missing pointer, and it is why this loop carries a guard: an
    absence became a positive fact when imagined nodes started being versioned, and a walk written for
    the absence would spin on the fact."""
    node = g.target(mapping, "original")
    # A node is a workbench copy exactly when some mapping points at it as an `image` — derived from the
    # structure, never asserted by a marker, and O(1) via the reverse index.
    seen = set()
    while node is not None and node not in seen:
        seen.add(node)
        up = [m for m in g.sources(node, "image") if g.kind(m) == "mapping"]
        if not up:
            break                                       # a real node: nothing images it
        nxt = g.target(up[0], "original")
        if nxt == node:
            return None                                 # its own original — imagined, and nowhere real
        node = nxt
    return node


def is_imagined(g: Graph, mapping: str) -> bool:
    """True for a node minted during planning — nothing real anywhere up the stack.

    Derived from `resolve` rather than asked as *does this mapping lack an `original`*. It lacks one no
    longer: an imagined node points at itself, so the question became *is this its own original*, and
    asking it through `resolve` keeps one walk rather than two that must agree."""
    return resolve(g, mapping) is None


def frames(g: Graph, wb: str) -> tuple:
    """Every frame, breadth-first from the root. A tree, not a list — assumptions fork it."""
    return g.targets(wb, "frame")


def history(g: Graph, mapping: str) -> tuple:
    """A node's own timeline: this mapping and everything downstream of it.

    `next` is 1:N, because frames fork — so a node's history is a tree mirroring the frame tree, and
    this returns all of it. Code that assumed a single successor would silently follow one branch."""
    out, queue = [], [mapping]
    while queue:
        m = queue.pop(0)
        out.append(m)
        queue.extend(g.targets(m, "next"))
    return tuple(out)


# --- stepping ---------------------------------------------------------------------------------------
def _ensure_step(g: Graph) -> None:
    """Make sure this graph has the surface `step` and what it stands on. Idempotent.

    The same argument as `access.bootstrap`, and deliberately the same shape: `step` is a name, and a
    name is only meaning if something answers it, so resolving it belongs where the call is made rather
    than being a precondition every caller keeps by hand."""
    from pathlib import Path
    from . import asm
    here = Path(__file__).parent / "rules"
    if fn.find(g, "copy_node") is None:
        asm.load_file(g, here / "reachable.mf")
    if fn.find(g, "step") is None:
        asm.load_file(g, here / "step.mf")


def step(g: Graph, wb: str, frame: str, function: str, bindings: dict, *,
         assumes: str | None = None, assume: str | None = None):
    """Run `function` on a new frame derived from `frame` — **the implementation is `rules/step.mf`**.

    This is a wrapper and nothing else: it describes the bindings as a node, because a Python dict is
    not something a rule can be handed, and it hands the answer back as the `(frame, transformation)`
    pair every existing caller already reads. The step itself — the frame, the choice among declared
    outcomes, the call, the record — happens in the surface.

    That is the conclusion of the de-Pythonization arc rather than a detail: planning that Python owns
    is planning the system cannot inspect or change. It only became affordable when frames went sparse,
    because the surface `step` was 22-42x the Python one while a frame was a full copy; measured 3.0x
    once they were sparse, and 1.3-1.6x on this path, which discards its own scaffolding.
    `_python_step` is kept immediately below, as the reference the surface is checked against.

    `bindings` maps parameter name to a mapping in `frame` — never a raw node, so the record stays
    replayable. `assumes` records the hypothesis this step took on faith. Raises `Refusal` when `assume`
    names an outcome the function never declared."""
    _ensure_step(g)
    described = g.mint("bindings")
    scratch = [described]
    for param, m in bindings.items():
        one = g.mint("binding", param=param)
        g.link(one, "value", m)
        g.link(described, "arg", one)
        scratch.append(one)

    # **A step that did not happen is not in the history**, and the swap is what made that free. The
    # chain has to be linked before the call — resolution walks it — so the Python `step` had to unlink
    # its half-written frame by hand when the call raised, which is not rare: an imagined step meeting
    # `UNKNOWN` in arithmetic raises, and the planner steps over those routinely.
    #
    # A microfunction's writes are journaled, so a `step` that *is* a microfunction rolls back whole —
    # frame, mappings and all — and the bookkeeping was deleted rather than moved. Tried before it was
    # written: the unwinding was implemented here first and then found to be dead code, which is the
    # project's own advice about testing a claim before building the fix for it.
    try:
        new_frame = fn.invoke(g, "step", {"wb": wb, "frame": frame, "function": function,
                                          "bindings": described, "assume": assume,
                                          "assumes": assumes}, retain=False)[1]["result"]
    finally:
        # The description was this call's own bookkeeping, so it goes with the call. The bindings hang
        # off the set, so they are dropped before it.
        for n in reversed(scratch):
            g.drop(n)
    return new_frame, g.target(new_frame, "via")


def _python_step(g: Graph, wb: str, frame: str, function: str, bindings: dict, *,
                 assumes: str | None = None, assume: str | None = None):
    """Run `function` on a NEW frame derived from `frame`, and record the transformation.

    **No longer the live implementation** — `step` above invokes `rules/step.mf`. Kept as the reference
    the surface is checked against, in `check_THE_STEP_ITSELF_IS_WRITTEN_IN_THE_SURFACE`: two
    implementations of one thing is a drift risk, and the answer to it is a check that compares them,
    not a deletion that leaves the surface unmeasured.

    `bindings` maps parameter name to a mapping in `frame` — never a raw node, so the record stays
    replayable. Returns `(new_frame, transformation)`.

    The previous frame is left intact, and that is what makes the movie real: every earlier state stays
    inspectable rather than being reconstructible only by replay. It costs nothing, because **a frame
    maps only what changed in it**. Nothing is copied here; a version is minted by the writer
    (`rules/version.mf`) the first time this frame writes to a node, and everything else is inherited by
    the walk `mapping_for` and `in_frame` both make.

    `assumes` records the hypothesis this step took on faith — which is how a plan carries its own
    dependence on guesses, inspectably."""
    # Refused before anything is minted. Naming an outcome that was never declared is a claim about the
    # *request*, so it cannot be allowed to leave a frame behind — the same standard the failed-call path
    # below is held to, and cheaper, because this one needs nothing from the frame to decide.
    outcomes = fn.mocks_of(g, function)
    if assume is not None and assume not in outcomes:
        raise KeyError(f"{assume!r} is not a declared outcome of {function!r}; known: {outcomes}")

    new_frame = g.mint("frame", index=g.attr(frame, "index", 0) + 1)
    g.link(wb, "frame", new_frame)
    # **Linked before the call, not after.** Resolution walks the frame chain, so a frame that is not yet
    # attached to its predecessor is a frame in which nothing at all is visible — every read the call
    # makes would answer with the node itself and every write would land outside the workbench. The
    # ordering is load-bearing rather than tidy.
    g.link(frame, "next", new_frame)

    # Mock substitution. On a workbench, a function that has declared outcomes is replaced by one of
    # them — always, not by convention. `assume` names which; the default is the most preferred, i.e. the
    # first declared, since `mock` is an ordered edge.
    #
    # This is a *convenience*, not the safety mechanism. Safety is `dispatch.service` refusing an
    # imagined target: if this substitution were forgotten or bypassed, a dispatching function would still
    # be unable to reach the world. Substitution makes planning *useful*; the refusal makes it *safe*, and
    # conflating the two would put the guarantee in the wrong place.
    #
    # The default now consults the state — the user's point: *"expectations must be
    # conditioned; a mock must map conditions to expectations, so even during planning we know what to
    # expect if we perform an action on a given state."* The default was `outcomes[0]` — declaration order,
    # asked without looking at the world — so *"what will happen if I do this here"* was answered by
    # something that could not see "here".
    #
    # A mock's condition is its parameter types, so this needs no new representation. A mock is an
    # ordinary microfunction, a parameter type is already a schema over a subgraph, and `fn.invoke` already
    # enforces it on every call. `fn.applicable` only asks that question *before* choosing instead of
    # after. Declaration order still decides among several that fit, which is what `mocks_of`'s preference
    # ordering was always for.
    #
    # What this replaces was not a wrong prediction but a crash. With two conditioned outcomes
    # (`found_dirty(t: dirty_tree)` / `found_clean(t: clean_tree)`), planning in a clean world took
    # `outcomes[0]` and `fn.invoke` refused it — `TypeViolation: t is not a dirty_tree` — so the condition
    # that should have *selected* the other outcome instead *rejected* the only one offered, and a plannable
    # state was unplannable. Measured in an earlier probe.
    #
    # Behaviour is unchanged for every mock whose parameters are typed as the real function's are — all
    # of them, before this — because then every outcome is applicable and the first is still `outcomes[0]`.
    # **The call is bound to identities, not to images**, and that is the change the rest of this rests
    # on. A rule handed the real `b` in the real world and the real `b` on a workbench is one rule with
    # one behaviour; only what a read *means* differs, which is the whole claim of the mediation layer.
    # It is also the only binding that can be written: an edge minted by this call names its target, and
    # a target that was this frame's copy would be a version — the thing the design rules out.
    args = {p: g.target(m, "original") or image_of(g, m) for p, m in bindings.items()}
    # **The boundary establishes the world its call runs in**, and it is opened here rather than at the
    # call because the mock's condition is asked in that world too. Everything beneath resolves in the
    # new frame: a rule written in the closed access vocabulary reads and writes that frame's versions
    # without containing one word about frames, and a rule that reaches a node some other way than
    # through its arguments resolves it the same way.
    #
    # `step` was already the mediation point; it did it by materialising at bind time, handing over a
    # freshly copied world. The seam does not move, only the mechanism at it.
    ctx = access.open_context(g, resolver="in_frame", writer="version_in_frame",
                              label=f"imagining {function}", frame=new_frame)
    if assume is not None:
        chosen = assume
    elif outcomes:
        fits = fn.applicable(g, function, args, under=ctx)
        # Falling back to `outcomes[0]` when nothing fits is deliberate: the honest report is the
        # `TypeViolation` naming the condition that failed, which says *no declared outcome covers this
        # state*. Silently substituting the real function instead would reach the world from inside a
        # workbench — refused by `dispatch.service`, but for the wrong reason and one layer too late.
        chosen = fits[0] if fits else outcomes[0]
    else:
        chosen = None
    executed = chosen or function

    try:
        called, _out = fn.invoke(g, executed, args, under=ctx)
    except BaseException:
        # **A step that did not happen must not be in the history.** The chain has to be linked before
        # the call — resolution walks it — but that means a call which raises leaves a frame wired into
        # the world's order, and everything downstream then reads a half-written state as though it were
        # a step somebody took. Detaching restores exactly what the copying version left behind: a frame
        # that is a member of the workbench and a successor of nothing. Found by a check where an
        # operator meets UNKNOWN and raises, which is a *routine* outcome of imagining rather than a bug.
        while new_frame in g.targets(frame, "next"):
            g.unlink(frame, "next", index=g.targets(frame, "next").index(new_frame))
        raise

    # A function may mint something while imagining. Those nodes get mappings too, pointing `original` at
    # **themselves** — which is meaningful rather than broken: it says *this does not exist yet and must
    # be created when the plan runs for real*. What ties such a node to reality later is not a pointer but
    # the transformation that produced it, which is recorded anyway. Without this, `is_imagined` could
    # never fire and execution would have nothing to bind a newly minted real node to.
    #
    # Self-pointing rather than absent, because an imagined node can now be *versioned* like any other:
    # the writer mints a second version of it the next time a frame writes to it, and `visible` recognises
    # the two as one thing by the identity they share. With the pointer absent there was no shared
    # identity to recognise, and one imagined node would have appeared twice in the same world.
    # What the call minted is read off the CALL, not off a whole-graph diff — see `activation.minted`.
    # The diff also caught anything else that happened to be minted while the call ran, which stopped being
    # theoretical once the interpreter's own state (focus, heads, activation, registers) became graph data.
    # A version minted by the writer is NOT a new node in the world — it is this frame's copy of one that
    # already existed, and it already has its mapping. Only what the rule itself brought into existence
    # gets an imagined mapping, which is what `original` being absent means.
    ran = ACT.for_focus(g, called.node)
    versioned = {image_of(g, m) for m in mappings(g, new_frame)}
    for n in ACT.minted(g, ran):
        if n in versioned or g.kind(n) in ("mapping", "frame"):
            continue
        m = g.mint("mapping")
        g.link(m, "original", n)          # an imagined node is its own identity, and says so
        g.link(m, "image", n)
        g.link(new_frame, "mapping", m)
        index(g, new_frame, n, m)

    # Choosing an outcome IS making an assumption, so it becomes a hypothesis the transformation records.
    # That is what lets a plan carry its own dependence on guesses: "which parts of this are fragile"
    # becomes a lookup rather than a judgement someone has to remember to make.
    if chosen is not None and assumes is None:
        assumes = hypothesis.open_hypothesis(
            g, f"{function} turns out {fn.returns_of(g, chosen) or chosen}")

    tr = g.mint("transformation", function=function, executed=executed,
                expects=fn.returns_of(g, executed))
    g.link(tr, "applies", fn.find(g, function))
    # The activation that imagined this step, kept where the rest of the step's record is. It answers
    # "which instruction did this get to, and what did it mint" without a second log — and it is what
    # `discard` scraps, so an abandoned workbench leaves no interpreter residue behind either.
    if ran is not None:
        g.link(tr, "ran", ran)
    for param, m in bindings.items():
        b = g.mint("binding", param=param)
        # The mapping, not the raw node — that is what makes a plan replayable. Whichever mapping was in
        # force when the step was taken: it may live in an ancestor frame, since a frame that did not
        # change this node has no mapping of its own for it, and that is the ordinary case now.
        g.link(b, "mapping", m)
        g.link(tr, "arg", b)
    if assumes is not None:
        g.link(tr, "assumes", assumes)
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
            ran = g.target(via, "ran")        # and so does the activation that imagined the step
            if ran is not None:
                ACT.scrap(g, ran)
            g.drop(via)
        # The context this frame was imagined in. Found through the reverse index rather than recorded
        # on the frame, by the direction invariant: a context points *at* the frame it resolves in, and
        # an edge back would drag the context — and the activation that established it — into every copy.
        #
        # A check caught this the moment the boundary started establishing one: *back to the original
        # size* went false, because a workbench that leaves residue behind is not discarded but mostly
        # discarded, which is the same standard `ACT.scrap` is held to one line above.
        for ctx in tuple(g.sources(f, "frame")):
            if g.kind(ctx) == "context":
                g.drop(ctx)
        g.drop(f)
    g.drop(wb)


def deviates(g: Graph, transformation: str, real_result) -> dict:
    """Did reality match what this transformation predicted? Empty dict means it did.

    **The implementation is `rules/deviate.mf`**; this is the wrapper, and it does one thing the surface
    cannot: it renders the answer back as the `{label: (expected, actual)}` dict every existing caller
    reads. That translation is the wrapper's whole job and it is temporary — when `execution.step` moves
    to the surface it will read the node directly and this dies with it.

    Deviation is a failed cast, which is why it is cheap: the transformation already records what type it
    expected. Comparing whole subgraphs would be expensive and noisy, and irrelevant differences would
    swamp the real ones. The expected type is the honest signal because it is exactly the promise the
    function made.

    Returns the violations, so a caller reporting a deviation can say *how* it deviated rather than only
    *that* it did — which is what the `violations` native was added for."""
    node = deviation_violations(g, transformation, real_result)
    out = as_violations(g, node)
    drop_violations(g, node)
    return out


def deviation_violations(g: Graph, transformation: str, real_result) -> str:
    """`deviates` **as the node the surface answers with**, before anything renders it.

    A deviation records these rather than a rendered dict, so the facts and the sentences stay apart in
    the same place `_UNMET_PHRASE` and `execution._DEVIATION_PHRASE` keep them. `deviates` above is the
    rendering, for callers that only want the verdict."""
    _ensure_deviates(g)
    return fn.invoke(g, "deviates", {"transformation": transformation, "result": real_result},
                     retain=False)[1]["result"]


def as_violations(g: Graph, node) -> dict:
    """A violations node as the `{label: (expected, actual)}` dict every reader here already speaks."""
    if node is None:
        return {}
    return {g.attr(v, "about"): (g.attr(v, "expected"), g.attr(v, "actual"))
            for v in g.targets(node, "violation")}


def drop_violations(g: Graph, node) -> None:
    """Scrap a violations node and its members — members first, or they would be orphaned."""
    if node is None:
        return
    for v in tuple(g.targets(node, "violation")):
        g.drop(v)
    g.drop(node)


def _ensure_deviates(g: Graph) -> None:
    """Resolve `deviates` in this graph. Idempotent — see `_ensure_step` for the argument."""
    from pathlib import Path
    from . import asm
    if fn.find(g, "deviates") is None:
        asm.load_file(g, Path(__file__).parent / "rules" / "deviate.mf")


def _python_deviates(g: Graph, transformation: str, real_result) -> dict:
    """The reference `deviates` is checked against. **Not the live one** — see above."""
    from .types import violations
    expected = g.attr(transformation, "expects")
    return {} if expected is None else violations(g, real_result, expected)


# --- expectations -----------------------------------------------------------------------------------
def _newly_minted(g: Graph, frame: str) -> tuple:
    """Mappings for nodes this step brought into existence — imagined, and with no predecessor."""
    return tuple(m for m in mappings(g, frame)
                 if is_imagined(g, m) and not g.sources(m, "next"))


def _predecessor(g: Graph, mapping: str, prev_frame: str):
    """The version this one succeeded — wherever it lives.

    It used to have to sit in `prev_frame`, which was true only while every frame held a version of
    everything. A sparse frame's predecessor is the last frame that *changed* this node, which may be
    several frames back, and demanding the immediate one silently reported no change at all."""
    for src in g.sources(mapping, "next"):
        if g.kind(src) == "mapping":
            return src
    return None


def _ensure_predict(g: Graph) -> None:
    """Resolve `predicted_changes` in this graph. Idempotent — see `_ensure_step` for the argument."""
    from pathlib import Path
    from . import asm
    if fn.find(g, "predicted_changes") is None:
        asm.load_file(g, Path(__file__).parent / "rules" / "predict.mf")


def predicted_changes(g: Graph, prev_frame: str, frame: str) -> str:
    """What the imagined step said would happen — **the implementation is `rules/predict.mf`**.

    A wrapper with nothing to translate: the answer was already a node, which is what let
    `unmet_expectations` move, and it is what lets `execution.step` read it in the surface.

    It was not on the handoff's list of what stood between `execution.step` and the surface, and the
    omission is worth recording: `deviates` and `unmet_expectations` were named because they are
    *predicates*, while this one answers with a node and so looked done. **A node a rule cannot ask for
    is still Python.** A recorded gap statement is a hypothesis, not an inventory.

    `_python_predicted_changes` is kept below as the reference this is checked against."""
    _ensure_predict(g)
    return fn.invoke(g, "predicted_changes", {"prev_frame": prev_frame, "frame": frame},
                     retain=False)[1]["result"]


def _python_predicted_changes(g: Graph, prev_frame: str, frame: str) -> str:
    """What the imagined step said would happen — derived from the two frames, never recorded.

    **No longer the live implementation** — see `predicted_changes` above. Kept as the reference the
    surface is checked against.

    The declared return type (`deviates`) is a good check and a narrow one: it asks whether *one* node
    satisfies *one* schema. It cannot express "the file listing will materialise three file nodes", which
    is exactly the sort of thing a tool call predicts and exactly where reality disagrees.

    The workbench has already imagined the answer. Frame N−1 and frame N *are* the before and after, so the
    expectation is their difference and there is nothing to author, nothing to store, and nothing that can
    fall out of step with the plan. Recording expectation nodes was the obvious alternative and would have
    been a labelling error — asserting what the structure already entails — as well as costing a node per
    imagined step, of which the driver makes hundreds.

    Only what changed, which is what keeps this from being a whole-subgraph diff. That comparison was
    rejected early for good reason: irrelevant differences swamp the real ones. A changed attribute is by
    definition something the step did, so the difference is already the tight set.

    Qualitative, never quantitative — the correction that matters most here. The first version of
    this compared magnitudes: the mock minted two file nodes, so it expected exactly two. That is wrong, and
    wrong in a way that would have made the mechanism useless in practice: listing a directory produces a
    *variable* number of files, and a plan that diverges because three arrived instead of two is diverging
    on noise. The number in a mock is a witness, not a promise.

    So the division of labour, which was already implicit and is now explicit:

    * The declared return type carries the discriminating claim — empty versus non-empty, serviced
      versus not. That is what a mock *is*: an outcome named by its return type. Checked by the cast
      (`deviates`), and deliberately not re-checked here, so a failure is reported once, in the place
      that owns it.
    * The derived expectation carries the qualitative shape of the change — files appeared, the
      directory got marked, an edge was added. Direction, presence, absence. Never how many.

    A magnitude that genuinely matters belongs in a type (`{"count": 0}`) or in a goal constraint, both of
    which say so on purpose rather than by accident of how a mock was written."""
    from .types import attrs_of
    tr = g.target(frame, "via")
    settled = set(attrs_of(g, g.attr(tr, "expects"))) if tr is not None else set()

    # **The answer is a node**, not a Python dict, and that is what unblocked `unmet_expectations`: a
    # predicate cannot be written in the surface if what it reads exists only in Python. One ordered
    # `expect` edge per expectation, each carrying its own `sort`, so a reader is one loop rather than
    # three — and `sort` is exactly the kind of condition a dispatching predicate selects a body on.
    #
    # Transient: the caller drops it, as with `reachable`'s walk node. It is derived from the two frames
    # every time it is asked for, so keeping one would be storing something the structure already
    # entails — the labelling error this codebase records at length.
    out = g.mint("prediction")

    def expect(sort: str, kind: str, mapping=None, target=None, **attrs):
        node = g.mint(kind, sort=sort, **attrs)
        if mapping is not None:
            g.link(node, "mapping", mapping)
        if target is not None:
            g.link(node, "target", target)
        g.link(out, "expect", node)

    for m in _newly_minted(g, frame):
        # Which KINDS appeared, never how many: a mock that mints two file nodes is giving a witness,
        # not a promise. Deduped through the graph rather than through a Python set, so the node carries
        # the same answer the dict did.
        want = g.kind(image_of(g, m))
        if not any(g.attr(e, "wanted") == want for e in g.targets(out, "expect")):
            expect("kind", "kind_expectation", wanted=want)

    for m in mappings(g, frame):
        prev_m = _predecessor(g, m, prev_frame)
        if prev_m is None:
            continue
        was, now = image_of(g, prev_m), image_of(g, m)
        keys = set(g.attrs.get(was, {})) | set(g.attrs.get(now, {}))
        for key in sorted(keys - {"kind"} - settled):    # `settled` is the cast's business, not ours
            if g.attr(was, key) != g.attr(now, key):
                # A boolean or a clearing is qualitative and kept exact; any other value is an
                # illustration, so only the fact that it was written is expected.
                want = g.attr(now, key)
                exact = isinstance(want, bool) or want is None
                # `mode` rather than a magic `"<set>"` value: an attribute holding `None` is absent, so
                # a node cannot distinguish *expected to be cleared* from *no expectation recorded*
                # by the value alone. The dict could, by carrying `None` in a tuple slot; the graph
                # cannot, and saying which of the two it is was the honest fix.
                expect("attr", "attr_expectation", mapping=m, key=key,
                       **({"mode": "exact", "want": want} if exact else {"mode": "set"}))
        for label in sorted(set(g.labels(was)) | set(g.labels(now))):
            before, after = g.count(was, label), g.count(now, label)
            if before == after:
                continue
            # Name the real target when there is one; an imagined target can only be expected to *appear*,
            # because it does not exist yet and what stands for it is decided at execution time.
            # An edge names an identity, so the real node is one `original_of` away — and an imagined
            # target answers `None` there, which is exactly the "can only be expected to appear" case.
            target = None
            for t in g.targets(now, label):
                real = original_of(g, t)
                if real is not None:
                    target = real
            expect("link", "link_expectation", mapping=m, target=target,
                   label=label, presence="some" if after else "none")
    return out


def drop_prediction(g: Graph, prediction: str) -> None:
    """Scrap a prediction and its expectations. The caller's job, as with `reachable`'s walk node.

    An expectation hangs off the prediction, so dropping the set first would orphan them — the shape
    `rules/step.mf` records finding the hard way when it frees its own argument bindings."""
    for e in tuple(g.targets(prediction, "expect")):
        g.drop(e)
    g.drop(prediction)


def expected_attrs(g: Graph, prediction: str) -> dict:
    """The attribute half of a prediction as `{key: want}` — for a reader that wants the summary.

    `"<set>"` stands for *written, value unspecified*, which is what `mode="set"` says on the node. The
    node keeps the two apart properly; this flattens them back for a caller that only wants to look."""
    return {g.attr(e, "key"): (g.attr(e, "want") if g.attr(e, "mode") == "exact" else "<set>")
            for e in g.targets(prediction, "expect") if g.attr(e, "sort") == "attr"}


def _ensure_unmet(g: Graph) -> None:
    """Resolve `unmet_expectations` in this graph. Idempotent — see `_ensure_step` for the argument."""
    from pathlib import Path
    from . import asm
    if fn.find(g, "unmet_expectations") is None:
        asm.load_file(g, Path(__file__).parent / "rules" / "unmet.mf")


def unmet_expectations(g: Graph, prediction: str, replay: str, mints: str) -> str:
    """Which of the imagined step's predictions reality did not deliver — as a **node**.

    **The implementation is `rules/unmet.mf`**; this resolves it and calls it, and there is nothing to
    translate on the way back, because the answer is already graph data.

    Each expectation is existential — *some* file exists, the directory *was* marked — never a count.
    `replay` carries the mapping-to-real bindings (`r -bound-> b -mapping-> … -node->`), and `mints` is
    what the real call created, as the node `activation.gather_minted` hands back.

    **It answers with facts, not with sentences**, and that is what let it move at all: the previous
    version returned prose containing `repr(got)`, which is neither reproducible in the surface nor
    something a predicate should be deciding. Rendering is `explain_unmet`'s business, at the edge that
    reports. A rendering decision inside a predicate is a second thing the predicate is for.

    Transient: the caller drops it."""
    _ensure_unmet(g)
    return fn.invoke(g, "unmet_expectations",
                     {"prediction": prediction, "replay": replay, "mints": mints},
                     retain=False)[1]["result"]


def _python_unmet_expectations(g: Graph, prediction: str, replay: str, mints: str) -> str:
    """The reference the surface is checked against. **Not the live one** — see above."""
    from . import execution as X
    out = g.mint("unmet")

    def miss(kind: str, expectation: str, to=None, **attrs):
        node = g.mint(kind, **attrs)
        g.link(node, "expectation", expectation)
        if to is not None:
            # An EDGE, never an attribute. A node named in an answer is pointed at, so a reader follows
            # it; storing the id as a value would make the answer a string about the graph rather than
            # part of it — and `explain_unmet` reads it with `g.target`, so the two spellings are not
            # interchangeable. The surface version says `LINK`, and this is what agreeing with it means.
            g.link(node, "to", to)
        g.link(out, "missed", node)

    made = {g.kind(n) for n in g.targets(mints, "found")}
    for e in g.targets(prediction, "expect"):
        sort = g.attr(e, "sort")
        if sort == "kind":
            if g.attr(e, "wanted") not in made:
                miss("missing_kind", e, wanted=g.attr(e, "wanted"))
            continue
        node = X.bound_to(g, replay, g.target(e, "mapping"))
        if node is None:
            continue                            # nothing real stands for it; not an expectation failure
        if sort == "attr":
            key, got = g.attr(e, "key"), g.attr(node, g.attr(e, "key"))
            if g.attr(e, "mode") == "set":
                if got is None:
                    miss("unset_attr", e, key=key)
            elif got != g.attr(e, "want"):
                miss("wrong_attr", e, key=key, want=g.attr(e, "want"), got=got)
        else:
            label, target = g.attr(e, "label"), g.target(e, "target")
            if target is not None and target not in g.targets(node, label):
                miss("missing_edge", e, label=label, to=target)
            elif target is None and g.attr(e, "presence") == "some" and g.count(node, label) == 0:
                miss("no_edge", e, label=label)
            elif g.attr(e, "presence") == "none" and g.count(node, label):
                miss("extra_edge", e, label=label, found=g.count(node, label))
    return out


#: How each kind of unmet expectation reads. The prose lives here, in one table, rather than inside the
#: predicate that decides — which is what let the predicate become graph-shaped. `repr` is what a Python
#: reader expects to see and it stays a Python concern.
_UNMET_PHRASE = {
    "missing_kind": lambda g, m: f"expected some new {g.attr(m, 'wanted')} node, found none",
    "unset_attr":   lambda g, m: f"expected {g.attr(m, 'key')!r} to be set, but it was not",
    "wrong_attr":   lambda g, m: (f"expected {g.attr(m, 'key')}={g.attr(m, 'want')!r} "
                                  f"but found {g.attr(m, 'got')!r}"),
    "missing_edge": lambda g, m: f"expected a {g.attr(m, 'label')!r} edge to {g.target(m, 'to')}",
    "no_edge":      lambda g, m: f"expected some {g.attr(m, 'label')!r} edge, found none",
    "extra_edge":   lambda g, m: (f"expected no {g.attr(m, 'label')!r} edge, "
                                  f"found {g.attr(m, 'found')}"),
}


def phrase_unmet(g: Graph, miss: str) -> str:
    """One miss, as the sentence a report prints.

    Split out of `explain_unmet` because a deviation records the **miss nodes** rather than a rendered
    tuple — a caller holding the facts renders them one at a time, at the edge, and the set node they
    were answered in is scratch that goes with the call."""
    return _UNMET_PHRASE[g.kind(miss)](g, miss)


def explain_unmet(g: Graph, unmet: str) -> tuple:
    """The sentences a report prints, rendered from the facts. Empty means it went as planned."""
    return tuple(phrase_unmet(g, m) for m in g.targets(unmet, "missed"))


def drop_unmet(g: Graph, unmet: str) -> None:
    """Scrap the answer and its parts. Dropped before the set, or they would be orphaned."""
    for m in tuple(g.targets(unmet, "missed")):
        g.drop(m)
    g.drop(unmet)


def as_mints(g: Graph, nodes) -> str:
    """A `mints` node over an existing list — the shape `activation.gather_minted` returns.

    Recovery has the nodes already, in a deviation record, and no activation to ask for them again."""
    out = g.mint("mints")
    for n in nodes:
        g.link(out, "found", n)
    return out


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


__all__ = ["deviates", "predicted_changes", "unmet_expectations", "expected_attrs", "drop_prediction",
           "explain_unmet", "drop_unmet", "as_mints",
           "assumption_of", "fragile_steps", "reachable", "open_workbench", "root_frame", "mappings", "mapping_for",
           "image_of", "identity_of", "original_of", "View", "view_at", "view_of", "visible",
           "resolve", "is_imagined", "frames", "history", "step", "fork", "discard"]

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
def open_workbench(g: Graph, subject: str, *, label: str = "workbench",
                   parent: str | None = None, explores: str | None = None) -> str:
    """Copy everything reachable from `subject` into a fresh workbench, and mint frame 0 with one mapping
    per copied node.

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


def view_of(g: Graph, act):
    """The world an activation is running in, as a `View` — or `None` for the real one.

    The bridge a **native** crosses to obey the context. A rule reaches the graph through the closed
    vocabulary and is mediated by construction; a native reads raw structure, so it has to ask. It asks
    the same way everything else does — dynamic scope over the activation chain — and this is the one
    place that knows a planning context points at a frame, which keeps `access.py` free of any idea of
    what a frame is."""
    from . import access
    ctx = access.context_of(g, act)
    frame = g.target(ctx, "frame") if ctx is not None else None
    return View(g, frame) if frame is not None else None


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

    Deviation is a failed cast, which is why it is cheap: the transformation already records what type
    it expected, and checking it is `types.is_a` — bounded, and already written. Comparing whole subgraphs
    would be expensive and noisy, and irrelevant differences would swamp the real ones. The expected type
    is the honest signal because it is exactly the promise the function made.

    Returns the type violations, so a caller reporting a deviation can say *how* it deviated rather than
    only *that* it did."""
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


def predicted_changes(g: Graph, prev_frame: str, frame: str) -> dict:
    """What the imagined step said would happen — derived from the two frames, never recorded.

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

    attrs, links, minted = [], [], set()
    for m in _newly_minted(g, frame):
        minted.add(g.kind(image_of(g, m)))          # Which KINDS appeared, not how many

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
                attrs.append((m, key, want if exact else "<set>"))
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
            links.append((m, label, "some" if after else "none", target))
    return {"attrs": tuple(attrs), "links": tuple(links), "minted": frozenset(minted)}


def unmet_expectations(g: Graph, prediction: dict, bound: dict, minted: list) -> tuple:
    """Which of the imagined step's predictions reality did not deliver. Empty means it went as planned.

    Each is an existential constraint — *some* file exists, the directory *was* marked — never a count.
    `bound` maps a mapping to the real node standing for it; `minted` is what the real call created."""
    missed = []
    for m, key, want in prediction["attrs"]:
        node = bound.get(m)
        if node is None:
            continue                            # nothing real stands for it; not an expectation failure
        got = g.attr(node, key)
        if want == "<set>":
            if got is None:
                missed.append(f"expected {key!r} to be set, but it was not")
        elif got != want:
            missed.append(f"expected {key}={want!r} but found {got!r}")
    for m, label, presence, target in prediction["links"]:
        node = bound.get(m)
        if node is None:
            continue
        if target is not None and target not in g.targets(node, label):
            missed.append(f"expected a {label!r} edge to {target}")
        elif target is None and presence == "some" and g.count(node, label) == 0:
            missed.append(f"expected some {label!r} edge, found none")
        elif presence == "none" and g.count(node, label):
            missed.append(f"expected no {label!r} edge, found {g.count(node, label)}")
    kinds = {g.kind(n) for n in minted}
    for kind in sorted(prediction["minted"] - kinds):
        missed.append(f"expected some new {kind} node, found none")
    return tuple(missed)


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


__all__ = ["deviates", "predicted_changes", "unmet_expectations",
           "assumption_of", "fragile_steps", "reachable", "open_workbench", "root_frame", "mappings", "mapping_for",
           "image_of", "identity_of", "original_of", "View", "visible",
           "resolve", "is_imagined", "frames", "history", "step", "fork", "discard"]

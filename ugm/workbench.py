"""Workbench — imagining what functions would do, on a copy, frame by frame.

Backward chaining over declared types concludes that applying `service` to a car yields a
serviced car. That is a promise rather than a proof, and it says nothing about what else changed,
which the next step may depend on. So type chaining is a good way to propose a chain and a bad
way to believe one; the workbench runs the proposal somewhere that does not count and reports
what really happened.

The copy boundary is everything reachable from the subject. Every cleverer boundary is a guess
about which structure will matter, and a wrong guess yields a plan that looks fine and fails on
contact with reality. The cost is accepted; copy-on-write, if it is ever needed, implements
exactly these semantics more cheaply rather than being a smaller boundary.

Mappings are the crux. A mapping points at the original and at this frame's image, and chains to
the next frame. Transformations bind their arguments to mappings, never to raw workbench nodes,
which is what makes a plan replayable: following the original yields the node the operation must
really be applied to. A log saying "`service` was applied" is unreplayable, because it does not
identify the subject in a form that survives out of the workbench.

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

from . import activation as ACT
from . import function as fn
from . import hypothesis
from .graph import Graph


# --- copying ----------------------------------------------------------------------------------------
def reachable(g: Graph, start: str) -> dict:
    """Everything reachable from `start` by outgoing edges. The copy boundary, per the design decision.

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
            stack.extend(t for t in g.targets(n, label) if t not in seen)
    return seen


def _copy_set(g: Graph, originals) -> dict:
    """Copy nodes and the edges among them. Returns `{original: image}`.

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
                if t in image:
                    # Edge properties are keyed by edge id now, not by `(src, label, index)`.
                    # Reading the old key here returned `{}` silently, so a copied edge quietly lost its
                    # properties — and nothing failed, because no check copied one. See the check that
                    # now does.
                    props = g.edge_props(g.edge_at(o, label, i))
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

    In a nested workbench a mapping's `original` points one level up, not at the real graph, so resolving
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
        g.link(m, "original", o)          # points out — never pointed at, see the invariant
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

    Returns `None` for a node that exists only in imagination — one minted during planning, which has no
    `original` at all. Those two cases must not be conflated: "no original" means *this does not exist
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

    `next` is 1:N, because frames fork — so a node's history is a tree mirroring the frame tree, and
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

    `bindings` maps parameter name to a mapping in `frame` — never a raw node, so the record stays
    replayable. Returns `(new_frame, transformation)`.

    The previous frame is left intact because the new frame is a full copy taken *before* the function
    runs. That is what makes the movie real: every earlier state remains inspectable rather than being
    reconstructible only by replay.

    `assumes` records the hypothesis this step took on faith — which is how a plan carries its own
    dependence on guesses, inspectably."""
    prev_images = {m: image_of(g, m) for m in mappings(g, frame)}
    # Ordered dedupe, not `set`. `mappings` is an ordered tuple, so this frame's order is a fact; a set
    # would replace it with node-id hash order and make every subsequent frame's mapping order — and hence
    # `driver.proposals` order, and hence the search — arbitrary. Same defect as `reachable`'s.
    originals = dict.fromkeys(prev_images.values())
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
    args = {p: image_of(g, carried[m]) for p, m in bindings.items()}
    outcomes = fn.mocks_of(g, function)
    if assume is not None:
        chosen = assume
    elif outcomes:
        fits = fn.applicable(g, function, args)
        # Falling back to `outcomes[0]` when nothing fits is deliberate: the honest report is the
        # `TypeViolation` naming the condition that failed, which says *no declared outcome covers this
        # state*. Silently substituting the real function instead would reach the world from inside a
        # workbench — refused by `dispatch.service`, but for the wrong reason and one layer too late.
        chosen = fits[0] if fits else outcomes[0]
    else:
        chosen = None
    if chosen is not None and chosen not in outcomes:
        raise KeyError(f"{chosen!r} is not a declared outcome of {function!r}; known: {outcomes}")
    executed = chosen or function

    called, _out = fn.invoke(g, executed, args)

    # A function may mint something while imagining. Those nodes get mappings too, with no `original` —
    # which is meaningful rather than broken: it says *this does not exist yet and must be created when the
    # plan runs for real*. What ties such a node to reality later is not a pointer but the transformation
    # that produced it, which is recorded anyway. Without this, `is_imagined` could never fire and
    # execution would have nothing to bind a newly minted real node to.
    # What the call minted is read off the CALL, not off a whole-graph diff — see `activation.minted`.
    # The diff also caught anything else that happened to be minted while the call ran, which stopped being
    # theoretical once the interpreter's own state (focus, heads, activation, registers) became graph data.
    ran = ACT.for_focus(g, called.node)
    for n in ACT.minted(g, ran):
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
    # The activation that imagined this step, kept where the rest of the step's record is. It answers
    # "which instruction did this get to, and what did it mint" without a second log — and it is what
    # `discard` scraps, so an abandoned workbench leaves no interpreter residue behind either.
    if ran is not None:
        g.link(tr, "ran", ran)
    for param, m in bindings.items():
        b = g.mint("binding", param=param)
        g.link(b, "mapping", carried[m])      # binds the mapping, not the raw node
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
            ran = g.target(via, "ran")        # and so does the activation that imagined the step
            if ran is not None:
                ACT.scrap(g, ran)
            g.drop(via)
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
    for src in g.sources(mapping, "next"):
        if g.kind(src) == "mapping" and src in g.targets(prev_frame, "mapping"):
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
            target = None
            for t in g.targets(now, label):
                tm = next((x for x in g.sources(t, "image")
                           if g.kind(x) == "mapping" and x in g.targets(frame, "mapping")), None)
                if tm is not None and resolve(g, tm) is not None:
                    target = resolve(g, tm)
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
           "image_of", "resolve", "is_imagined", "frames", "history", "step", "fork", "discard"]

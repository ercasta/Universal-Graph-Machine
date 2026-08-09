"""Applications and episodes — the record of what the system did, as ordinary nodes.

An application is a node: which function, bound to which arguments, in which episode. It is
minted by whoever applies the function, and thereafter it is ordinary data — navigable,
comparable, and capable of being pointed at by a hypothesis. A binding is itself a node, so "what
if this had been applied to that" is expressible.

Four capabilities depend on this record existing: choosing among candidates has something to
point at, lookahead has something to hypothesise about, what worked is recorded, and learning has
something to read.

An episode holds its applications on an ordered `step` edge, so the order is the order they were
appended. Nothing stamps a turn counter, and episodes are not merely as ordered as their driver
made them.

Learning is cheap because of that shape. Compiling an episode into a reusable function is reading
the sequence and writing a function whose body invokes the same operations — `function.define`
plus a loop, using nothing this package did not already have. `compile_episode` is short on
purpose: if it needed machinery, the claim that learning falls out of the data model would be
wrong.

See `docs/concepts.md`.
"""
from __future__ import annotations

from . import function as fn
from .graph import Graph
from .isa import F, I, R
from .types import tagged_as


def open_episode(g: Graph, label: str = "episode", *, about=None) -> str:
    """An episode collects applications in the order they happen."""
    ep = g.mint("episode", label=label)
    if about is not None:
        g.link(ep, "about", about)
    return ep


def record(g: Graph, name: str, bindings: dict, *, episode=None, outcome=None) -> str:
    """Mint the record of one application. `bindings` maps parameter name to the node it was bound to.

    An argument is its own node carrying the parameter name, rather than an edge property, so that a
    binding can itself be pointed at — a hypothesis about "what if this had been applied to *that*
    instead" needs the binding to be a thing."""
    app = g.mint("application", function=name)
    target = fn.find(g, name)
    if target is not None:
        g.link(app, "of", target)
    for param, node in bindings.items():
        arg = g.mint("binding", param=param)
        if node is not None:
            g.link(arg, "value", node)
        g.link(app, "arg", arg)
    if outcome is not None:
        g.put(app, outcome=outcome)
    if episode is not None:
        g.link(episode, "step", app)          # ordered — no turn stamp needed
    return app


def bindings_of(g: Graph, app: str) -> dict:
    return {g.attr(a, "param"): g.target(a, "value") for a in g.targets(app, "arg")}


def steps(g: Graph, episode: str) -> tuple:
    """The applications, in the order they happened. Native, not reconstructed.

    Filtered to applications on purpose. A *thread* (`thread.py`) is an episode that also carries
    attention shifts, so that memory is one record rather than two. Everything here — and `compile_episode`
    above all — asks only about what was *applied*, and would otherwise try to compile a shift of attention
    into a function call. Existing episodes contain nothing else, so this changes no behaviour they had;
    it is what lets a thread be an episode at all."""
    return tuple(e for e in g.targets(episode, "step") if g.kind(e) == "application")


def applied_to(g: Graph, node: str) -> tuple:
    """Every application that bound `node` to some parameter — O(1)-ish via the reverse index.

    This is what stops a selector re-applying the same function to the same node forever, which was the
    single most persistent defect of the rule-based version (an unguarded rule re-firing every turn)."""
    out = []
    for binding in g.sources(node, "value"):
        for app in g.sources(binding, "arg"):
            if g.kind(app) == "application":
                out.append(app)
    return tuple(out)


def has_been_applied(g: Graph, name: str, node: str) -> bool:
    return any(g.attr(a, "function") == name for a in applied_to(g, node))


def generalise(g: Graph, episode: str, keep_constant=()) -> tuple:
    """Decide which of an episode's bound nodes become parameters of the learned function.

    This is the step that turns *what the system did to this particular car* into *what it can do to any
    car*. Without it a learned function would only ever work on the thing it was learned from — a log
    entry, not a procedure.

    The default is mechanical: every distinct node the episode bound becomes a parameter, named after
    the kind it had, in first-appearance order. No analogy, no guessing, no search.

    The hard part is not this mechanism, it is the judgement it encodes, and it deserves to be named
    rather than buried: *which* bindings should generalise. An episode that did `transfer(from: alice,
    to: acme)` could sensibly become `f(from, to)` or `f(from)` with `acme` fixed, because the company
    account is not the sort of thing that varies. Nothing in the episode itself distinguishes these — the
    information is not there. So `keep_constant` takes that judgement as an explicit argument rather than
    letting a default pretend to know: anything listed stays hardcoded in the generated body.

    Returns `(param_names, {node: param_name}, ptypes)`."""
    keep = set(keep_constant)
    order, mapping, ptypes, seen = [], {}, {}, {}
    for a in steps(g, episode):
        for node in bindings_of(g, a).values():
            if node is None or node in keep or node in mapping:
                continue
            # Read the type hint through `tagged_as`, which re-validates it. Reading the raw `is_a`
            # attribute was a live defect: it is a claim about the past, so a node that has since changed
            # would name the learned function's parameter — and declare its type — after a class it no
            # longer belongs to, producing a function that refuses its own training example.
            declared = tagged_as(g, node)
            kind = declared or g.kind(node) or "arg"
            seen[kind] = seen.get(kind, 0) + 1
            name = kind if seen[kind] == 1 else f"{kind}{seen[kind]}"
            mapping[node] = name
            order.append(name)
            if declared:
                ptypes[name] = declared
    return tuple(order), mapping, ptypes


def compile_episode(g: Graph, episode: str, new_name: str, *, keep_constant=(),
                    doc: str | None = None) -> str:
    """Turn an episode into a reusable function — the payoff claim, deliberately short.

    The generated function invokes, in order, each operation the episode recorded, with every generalised
    binding replaced by a parameter (see `generalise`) and everything else left as the concrete node it
    was. It is stored like any other function, runs like any other function, and can itself be recorded in
    a later episode.

    Any node kept constant is written into the body as a `Ref` — a stored pointer to that exact node,
    which is precisely what a reference is for (`graph.py`: an edge is a relation, a reference is an
    address). So the distinction between "this varies" and "this is always the company account" is visible
    in the generated source rather than hidden in how it was compiled."""
    params, mapping, ptypes = generalise(g, episode, keep_constant)
    program = []
    for app in steps(g, episode):
        called = g.attr(app, "function")
        args = {}
        for param, node in bindings_of(g, app).items():
            args[param] = F(mapping[node]) if node in mapping else Ref(node)
        program.append(I("INVOKE", (R("_"), called, args)))
    doc = doc or f"Learned from {g.attr(episode, 'label')}: " + \
        " then ".join(g.attr(a, "function") for a in steps(g, episode))
    fn.define(g, new_name, params, tuple(program), doc, None, ptypes)
    return new_name


__all__ = ["open_episode", "record", "bindings_of", "steps", "applied_to",
           "has_been_applied", "compile_episode"]

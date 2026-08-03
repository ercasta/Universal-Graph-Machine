"""Mediated access — the closed vocabulary a rule reaches the graph through, and the binder that
decides what a read means.

Two unrelated-looking demands want the same mechanism, and separating them is the whole design.

**Meaning.** A rule that says `GET F(b) "on"` has flattened *the support of b* into an edge traversal.
The relation is gone as a relation: nothing can ask what the rule was about, only what it stepped
through. So lowering stops at a **named call**, never at an opcode — a name survives compilation
(`INVOKE` stores it, and a static reader can walk a stored body and see what it calls), and a name is
where linking can still happen at run time.

**Transparency.** Planning wants to read over a partially modified graph — to see a frame's version of
the world without every rule knowing what a frame is. That needs *every* access interposable. Not most:
one unmediated read and the answer is silently wrong.

Totality is what forces this to be its own layer. The domain vocabulary (`support_of`, `wheels_of`) is
open and will never cover everything, and an open class cannot be total; so mediation bottoms out in a
closed set, with domain names implemented *in terms of* it. Hence three layers rather than two — the
kernel's instruction set, this, and the open vocabulary above it.

    kernel            the instruction set          closed
    mediated access   the eight names below        closed, and total
    domain vocabulary support_of, wheels_of, …     open, and may contain no natives

**The binder is dynamic scope over the activation chain.** A context sits on an activation and is
inherited through `caller`, so a callee runs in its caller's context without being handed one. Dynamic
scope is normally a bad trade because you cannot see what a function will do without tracing a stack
that is not data. Here the stack *is* data: every activation points at its caller, `activation.chain`
walks it, and *what context was this running under* is an ordinary query. The usual objection does not
apply to this engine.

That it is inherited at all deserves stating, because `INVOKE` deliberately gives a callee a fresh focus
with none of the caller's heads, so a function is never silently sensitive to where its caller happened
to be looking — and inheriting a context looks like the same mistake in another dimension. It is not.
**The call chain and the frame nest identically: a callee always runs in its caller's frame. Attention
does not nest**, because a callee looks at its own arguments. Frame is a property of the dynamic extent;
attention is a property of the call. Inheriting the first is the correct semantics; inheriting the
second is the accident `INVOKE` guards against.

**Inherit by default, establish explicitly at a boundary.** `workbench.step` does not inherit — it
establishes the frame its call runs in. So does `execution`, and that is what removes the last mode from
the design: the real world is not the *absence* of a context but the **trivial** one, whose resolution is
the identity function. The same rule runs in both, there is never mediated-versus-unmediated execution
to branch on, and forgetting to establish is one bug in one place rather than two behaviours.

**Resolution is itself a named call.** A context carries the *name* of the function that resolves a node
in it, and the vocabulary invokes it — so what a read means can be changed without editing a rule, which
is the entire reason lowering stops at a name. A context with no resolver *is* the trivial one: identity,
costing nothing, and still a context somebody established rather than a place where nobody did.

See `docs/mediated-access.md`.
"""
from __future__ import annotations

from . import isa
from .graph import Graph

KINDS = ("context",)

#: The closed set, and what each member stands for. Total by construction: these are every graph
#: operation the authored corpus performs — measured, not imagined, across `stack`, `unstack`, `paint`,
#: `service`, `wash`, `list_dir` and its mocks. Everything else in those bodies is `ADD`/`LT`/`JMP`,
#: which touch nothing and need no mediation.
#:
#: The mapping is what lets a static reader keep working. `driver._effects` walks a stored body to learn
#: what a rule writes, and an `INVOKE` is opaque to it — so lowering to calls would have blinded the
#: planner if the calls were anonymous. They are not: this set is *closed*, so a reader may know it,
#: exactly as it knows the opcodes.
VOCABULARY = {
    "slot_of": "ATTR",
    "set_slot": "SET",
    "related": "GET",
    "relations": "COUNT",
    "relation_at": "GET_AT",
    "relate": "LINK",
    "unrelate": "UNLINK",
    "make": "NEW",
}


#: Each member's operands, in the order the opcode it stands for takes them, and whether that opcode
#: writes a destination register. This is what makes lowering-to-a-call cost the static readers nothing.
_SHAPE = {
    "slot_of":     ("ATTR",   True,  ("node", "key")),
    "set_slot":    ("SET",    False, ("node", "key", "value")),
    "related":     ("GET",    True,  ("node", "label")),
    "relations":   ("COUNT",  True,  ("node", "label")),
    "relation_at": ("GET_AT", True,  ("node", "label", "index")),
    "relate":      ("LINK",   False, ("node", "label", "other")),
    "unrelate":    ("UNLINK", False, ("node", "label", "index")),
    "make":        ("NEW",    True,  ("kind",)),
}


def as_opcode(ins):
    """The instruction a vocabulary call stands for, or `None` if this is not one.

    **This is why lowering to a name costs the planner nothing.** `driver._effects` walks a stored body
    to learn what a rule writes — which is what relevance ranks on and what means-ends chains backwards
    through — and an `INVOKE` is opaque to it: the effect happens somewhere else. Lowering every read and
    write to anonymous calls would therefore have blinded the planner to every rule at once.

    The calls are not anonymous. The set is *closed*, so a static reader may know it exactly as it knows
    the opcodes, and one translation here serves every reader rather than each growing its own — which is
    the drift shape `driver._walk` already exists to prevent between two of them.

    Only the literal-binding form translates. `INVOKE … with <node>` assembles its parameter names at run
    time, so what it writes is genuinely not a static fact, and reporting a guess would be worse than
    reporting nothing."""
    if ins.op not in ("INVOKE", "ATTEMPT"):
        return None
    at = 1 if ins.op == "INVOKE" else 2                 # `ATTEMPT` has an error register in front
    args = ins.args
    if len(args) <= at or not isinstance(args[at], str) or args[at] not in _SHAPE:
        return None
    binds = args[at + 1] if len(args) > at + 1 else {}
    op, writes, params = _SHAPE[args[at]]
    if not isinstance(binds, dict) or any(p not in binds for p in params):
        return None
    operands = tuple(binds[p] for p in params)
    return isa.I(op, ((args[0],) + operands) if writes else operands)


def calls_the_vocabulary(program) -> bool:
    """Does this body reach the graph through the closed set? The linker's question."""
    return any(not isinstance(ins, str) and as_opcode(ins) is not None for ins in program)


def bootstrap(g: Graph) -> tuple:
    """Make sure the closed vocabulary and the frame resolver are in this graph. Idempotent.

    Called by `asm.load_text` when what it just stored calls one of the eight names, which makes this
    **linking** rather than convenience: a rule that says `slot_of` names something that has to be there
    to run, and resolving a name to an implementation is exactly the step lowering-to-a-name preserves.
    Requiring every caller to remember to load two files first would be a precondition kept by hand, and
    forgetting it would fail at run time, far from the load that should have said so.

    No recursion to guard against, and it is worth saying why rather than trusting it: the bodies in
    these two files reach the graph with bare opcodes — they *are* the mediation — so loading them can
    never trigger this."""
    from . import asm, function as fn
    from pathlib import Path
    here = Path(__file__).parent / "rules"
    out = []
    for probe, name in (("slot_of", "access.mf"), ("in_frame", "resolve.mf"),
                        ("version_in_frame", "version.mf"), ("copy_node", "reachable.mf")):
        if fn.find(g, probe) is None:
            out.extend(asm.load_file(g, here / name))
    return tuple(out)


# --- contexts -----------------------------------------------------------------------------------------
def open_context(g: Graph, *, resolver: str | None = None, writer: str | None = None,
                 label: str | None = None, **links) -> str:
    """A context: what a read means, for the dynamic extent of whatever establishes it.

    `resolver` is the *name* of a function taking one node and returning the node to read instead — the
    named call the whole scheme rests on. `None` is the trivial context, whose resolution is identity;
    it is a real context, established at a real boundary, and it costs nothing because the vocabulary
    skips the call when there is no name to call.

    `links` attach whatever the resolver needs to do its job — `frame=<frame>` for planning. Passing
    them as edges rather than attributes is deliberate: a context that pointed at a frame by id string
    would be a pointer the graph could not follow."""
    ctx = g.mint("context", **({"label": label} if label else {}))
    if resolver is not None:
        g.put(ctx, resolver=resolver)
    if writer is not None:
        g.put(ctx, writer=writer)
    for name, target in links.items():
        if target is not None:
            g.link(ctx, name, target)
    return ctx


def establish(g: Graph, act: str, ctx: str) -> None:
    """Run everything beneath this activation in `ctx`.

    Replaced rather than appended: a context is a pointer, not a collection, and letting it grow would
    make `context_of` silently answer with a stale first target — the defect `Focus._point` records for
    heads, in the same shape."""
    while g.count(act, "context"):
        g.unlink(act, "context", index=0)
    g.link(act, "context", ctx)


def context_of(g: Graph, act: str | None):
    """The context this activation runs in: its own, or the nearest one up the `caller` chain.

    `loop._after` is the precedent, and its docstring gives the argument for why natives are handed an
    activation at all — *"a body that had to be told which loop it was running on would be a body that
    could not be moved."* This is that sentence about frames instead of agendas.

    `None` means nobody established one, which reads as the trivial context. That is a deliberate
    choice and it has a cost: a boundary that *forgets* to establish is then silent rather than loud.
    The answer is not to make an unestablished read raise — a great deal of ordinary Python-driven work
    calls rules directly and correctly means the real world — but to check the boundaries themselves,
    which is what `establishes` is for."""
    # `activation.chain`'s walk, one edge at a time, stopping at the first answer — and cycle-guarded
    # for its reason: a chain that pointed at itself would spin here rather than answering.
    seen = set()
    while act is not None and act not in seen:
        seen.add(act)
        ctx = g.target(act, "context")
        if ctx is not None:
            return ctx
        act = g.target(act, "caller")
    return None


def resolved(g: Graph, ctx: str | None, node):
    """`node` as `ctx` resolves it — the vocabulary's own move, made from Python.

    A Python caller standing *at* a boundary sometimes has to read a node the way the call it is about to
    make will read it. `function.invoke` is the one that matters: a declared parameter type is a
    precondition, and once bindings are canonical the precondition would be checked against the real
    world while the body it guards reads the frame. A rule would then refuse on a state it is being run
    in, or accept one it is not.

    Made **by name**, exactly as `access.mf` makes it, so there is one resolver and Python cannot come to
    disagree with the surface about what a read means. `check_types=False` on the inner call is not an
    economy: it is what stops a type check from provoking the resolution that provokes a type check.

    The trivial context costs nothing, because there is no name to call."""
    if ctx is None or node is None:
        return node
    name = g.attr(ctx, "resolver")
    if name is None:
        return node
    from . import function as fn
    return fn.invoke(g, name, {"node": node}, under=ctx, retain=False, check_types=False)[1]["result"]


def establishes(g: Graph, act: str):
    """The context this activation established *itself*, ignoring anything it inherited.

    The difference matters at exactly one moment: checking that a boundary did its job. Every activation
    beneath `step` answers `context_of` correctly whether or not `step` established anything — it would
    just answer with the caller's. So the check that a boundary establishes has to ask this question,
    not that one."""
    return g.target(act, "context")


def resolver_of(g: Graph, act: str | None):
    """The name of the ambient context's resolver, or `None` for the trivial context.

    This is what the vocabulary calls to decide what to call. Handing back a *name* rather than
    resolving here is the point: the read is lowered to a named call, resolution is an ordinary function
    anybody can read, and the machinery can change what a read means without touching a rule."""
    ctx = context_of(g, act)
    return None if ctx is None else g.attr(ctx, "resolver")


def writer_of(g: Graph, act: str | None):
    """The name of the function a *write* must resolve through, or `None` for the trivial context.

    Reading asks *which version is in force*; writing asks *which version may I change* — and those are
    different questions the moment a frame shares versions with its predecessor. Writing to the version
    in force would change what an earlier frame said, and every sibling branch with it, invisibly. So a
    write resolves through a writer that mints a version belonging to this frame if there is not one
    already, which is copy-on-write with the copying decided by a name the context supplies.

    Falls back to the resolver, so a context that only reads is written through the same way it is read —
    the real world's case, where there is one version of everything and a write lands on it."""
    ctx = context_of(g, act)
    if ctx is None:
        return None
    return g.attr(ctx, "writer") or g.attr(ctx, "resolver")


# --- the compliance question --------------------------------------------------------------------------
def bare_touches(g: Graph, name: str) -> tuple:
    """Every instruction in this body that reaches the graph without going through the vocabulary.

    `(index, op)` pairs, in program order. Empty means the body is mediated.

    **This is enforced, and the domain vocabulary is not, and that asymmetry is the whole of the
    governance.** A missing domain name costs expressiveness; a bare `GET` in a rule that runs inside a
    frame produces a wrong answer with no symptom. Two demands, one mechanism, two regimes — expecting
    one policy to serve both is the error worth naming.

    Answerable at all because bodies are data: `function.load` lifts one back to instructions, which is
    the same property `driver.establishes` reads a rule's effects with."""
    from . import function as fn
    _params, program = fn.load(g, name)
    return tuple((i, ins.op) for i, ins in enumerate(program)
                 if not isinstance(ins, str) and ins.op in isa.TOUCHES_GRAPH)


def operators(g: Graph) -> tuple:
    """Every function the planner can propose — the ones compliance applies to.

    Derived, never listed. A function is proposable exactly when it declares a parameter *type*, because
    that is what `driver.proposals` binds against; and a proposable function is precisely one that will
    be run inside a frame, which is what makes mediation load-bearing for it. So the population that
    must be mediated falls out of the structure rather than out of a list somebody maintains — and a
    list is the shape this codebase keeps recording as the thing that drifts.

    What it deliberately does not cover: an untyped helper called *by* a rule. It is unproposable, so it
    is not a planning operator; if it touches the graph bare it will be caught the moment it is given a
    signature. That is a real hole and it is stated rather than papered over."""
    from . import function as fn
    return tuple(n for n in fn.names(g) if fn.param_types(g, n))


def offenders(g: Graph) -> dict:
    """`{name: ((index, op), …)}` for every planning operator that touches the graph bare.

    The compliance pass. Empty is the property to hold."""
    out = {}
    for name in operators(g):
        if name in VOCABULARY:
            continue                                   # the closed set IS the bare layer, by definition
        bare = bare_touches(g, name)
        if bare:
            out[name] = bare
    return out


def resolves_before_touching(g: Graph) -> tuple:
    """The members of the closed set that fail to resolve before they touch — which must be none.

    The vocabulary bodies repeat a three-instruction preamble instead of sharing one, which is the
    duplication this codebase usually refuses. It buys the trivial context back its cost: a shared
    `resolved` procedure would make every read in the real world two calls deep instead of none. The
    trade is only acceptable if the repetition cannot drift, so it is checked rather than trusted —
    every member must ask for the resolver, and no member may touch the graph before it has.

    A missing member is reported too. The set is closed, so *incomplete* is as much a defect as *wrong*.

    `make` is the one member that resolves nothing, because a mint has no earlier version to resolve to
    — see its body for why it is in the set regardless. That exemption is stated here, once, rather than
    being a silence anybody could read as an oversight."""
    from . import function as fn
    bad = []
    for name, op in VOCABULARY.items():
        if fn.find(g, name) is None:
            bad.append((name, "not defined"))
            continue
        _params, program = fn.load(g, name)
        asked = touched = None
        for i, ins in enumerate(program):
            if isinstance(ins, str):
                continue
            if asked is None and ins.op == "NATIVE" and (
                    "resolver" in ins.args or "writer" in ins.args):
                asked = i                          # reading asks one; writing asks the other
            if touched is None and ins.op in isa.TOUCHES_GRAPH:
                touched = i
        if touched is None:
            bad.append((name, f"never performs its own operation ({op})"))
        elif op == "NEW":
            continue                                   # `make` resolves nothing: there is no version yet
        elif asked is None:
            bad.append((name, "never asks how to resolve"))
        elif touched < asked:
            bad.append((name, f"touches the graph at {touched} before resolving at {asked}"))
    return tuple(bad)


from . import native as _N                                            # noqa: E402
# Two natives, and they are the binder's whole interface to a running program. Both are substrate: they
# read interpreter state — an activation and the edge it carries — and nothing about the world. The
# module that owns a thing registers it (`native.py`'s rule), and what a context *means* is owned here.
_N.register("resolver", lambda g, act: resolver_of(g, act))
_N.register("writer", lambda g, act: writer_of(g, act))
_N.register("context", lambda g, act: context_of(g, act))

__all__ = ["KINDS", "VOCABULARY", "open_context", "establish", "context_of", "establishes", "resolved",
           "resolver_of", "writer_of", "bootstrap", "bare_touches", "operators", "offenders", "resolves_before_touching"]

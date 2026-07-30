"""FUNCTIONS — a rule is a function, stored in the graph as data, executed by the ISA.

This is the module where "rules as data" stops being a slogan. Every previous version of this idea in this
project stored rule-shaped data that a fixed compiler turned into something *matched*; here the stored form
is turned into something *run*. A rule is a named ISA program with parameters, and calling it is calling a
function.

**Stored as ordered edges, which is why the substrate change mattered.** A function node carries its
parameters and its instructions as ordered 1:N edges (`param`, `instr`), each instruction carries its
operands as an ordered `arg` edge, and order is native rather than reconstructed from sequencing facts.
Before named/indexed edges this encoding would have needed a position attribute on every instruction and a
sort on every load.

**Why there is no seam, restated because it is the load-bearing claim.** A stored function is not part of a
rigid end-to-end program. Nothing runs unless something calls it, composability comes from *which* functions
get called on *which* heads, and that decision is selection's job — not a control-flow graph fixed at
authoring time. So the library can grow without any global program having to be re-verified, which is the
property the telecom feature-interaction literature spent decades arriving at.

**The calling convention, and the one real decision in it.** A callee gets a **fresh focus** containing only
its bound parameters — not the caller's heads. Sharing the caller's focus would make every function
silently sensitive to where the caller happened to be looking, which is the ambient-context defect the whole
repoint exists to remove. Isolation here is the same discipline as pointing: a function sees what it was
handed, and nothing else. Registers are likewise fresh; a result comes back through the `result` register.
"""
from __future__ import annotations

from .focus import Focus
from .graph import Graph, Ref
from .isa import F, I, R

_FORMS = {"focus": F, "reg": R}


# --- storing -------------------------------------------------------------------------------------
def _store_operand(g: Graph, instr: str, operand) -> None:
    if isinstance(operand, F):
        a = g.mint("arg", form="focus", value=operand.name)
    elif isinstance(operand, R):
        a = g.mint("arg", form="reg", value=operand.name)
    elif isinstance(operand, Ref):
        a = g.mint("arg", form="ref", value=operand.node)
    else:
        a = g.mint("arg", form="literal", value=operand)
    g.link(instr, "arg", a)


def define(g: Graph, name: str, params: tuple, program: tuple,
           doc: str | None = None, notes: dict | None = None, ptypes: dict | None = None,
           returns: str | None = None) -> str:
    """Store a function as graph data. Returns the function node.

    A label (a bare string in `program`) is stored as an instruction whose op is `LABEL`, so the stored
    form stays a flat ordered list rather than needing a second representation for jump targets.

    `doc` is the function's natural-language description and `notes` maps instruction index to a
    natural-language note. **Both are stored, not discarded**, and that is deliberate: the description is
    what a selection layer ranks over and what a language model reads to decide whether this function is
    the one to call. A comment that only survives in a source file is invisible to the running system;
    stored on the node, it is ordinary data any microfunction can read — or write."""
    fn = g.mint("function", name=name)
    if doc:
        g.put(fn, doc=doc)
    if returns:
        g.put(fn, returns=returns)
    ptypes = ptypes or {}
    for p in params:
        node = g.mint("param", name=p)
        if ptypes.get(p):
            g.put(node, type=ptypes[p])
        g.link(fn, "param", node)
    notes = notes or {}
    for pos, step in enumerate(program):
        if isinstance(step, str):
            i = g.mint("instr", op="LABEL", label=step)
        else:
            i = g.mint("instr", op=step.op)
        if notes.get(pos):
            g.put(i, note=notes[pos])
        g.link(fn, "instr", i)
        if not isinstance(step, str):
            for operand in step.args:
                _store_operand(g, i, operand)
    return fn


def returns_of(g: Graph, name: str) -> str | None:
    """The declared result type. This is what a planner chains BACKWARDS on: to obtain a `T`, find the
    functions that return `T`, and make their parameter types the subgoals."""
    f = find(g, name)
    return g.attr(f, "returns") if f is not None else None


def producers(g: Graph, type_name: str) -> tuple:
    """Every function whose result satisfies `type_name` — the candidate set for one backward step.

    **Subtype-aware, deliberately.** A function returning a `washed_car` genuinely satisfies a goal
    wanting a `serviced_car`, because every washed car is a serviced one. Comparing type *names* would
    miss that, so this asks `types.subsumes` instead: does the declared result's constraint set include
    everything `type_name` demands? Exact matches sort first, since a more specific producer does more
    work than was asked for and should not be preferred by accident."""
    from .types import subsumes
    hits = [(g.attr(n, "returns") != type_name, g.attr(n, "name"))
            for n in g.nodes
            if g.kind(n) == "function" and g.attr(n, "returns")
            and subsumes(g, type_name, g.attr(n, "returns"))]
    return tuple(name for _more_specific, name in sorted(hits))


def param_types(g: Graph, name: str) -> dict:
    """`{param: declared type}`. What candidate generation reads to ask whether a function could apply."""
    fn = find(g, name)
    if fn is None:
        return {}
    return {g.attr(p, "name"): g.attr(p, "type")
            for p in g.targets(fn, "param") if g.attr(p, "type")}


def doc_of(g: Graph, name: str) -> str | None:
    """The function's natural-language description. This is what selection ranks over."""
    fn = find(g, name)
    return g.attr(fn, "doc") if fn is not None else None


def notes_of(g: Graph, name: str) -> dict:
    fn = find(g, name)
    if fn is None:
        return {}
    return {i: g.attr(n, "note")
            for i, n in enumerate(g.targets(fn, "instr")) if g.attr(n, "note")}


def catalogue(g: Graph) -> dict:
    """`{name: doc}` for the whole library — the handle a model or a selector is given to choose with."""
    return {g.attr(n, "name"): g.attr(n, "doc")
            for n in g.nodes if g.kind(n) == "function"}


# --- loading -------------------------------------------------------------------------------------
def find(g: Graph, name: str):
    for n in g.nodes:
        if g.kind(n) == "function" and g.attr(n, "name") == name:
            return n
    return None


def _load_operand(g: Graph, arg: str):
    form, value = g.attr(arg, "form"), g.attr(arg, "value")
    if form in _FORMS:
        return _FORMS[form](value)
    if form == "ref":
        return Ref(value)
    return value


def load(g: Graph, name: str) -> tuple:
    """Lift a stored function back to `(params, program)`. Raises if it is not there — loudly, per this
    project's standing discipline for a malformed or missing fragment."""
    fn = find(g, name)
    if fn is None:
        raise KeyError(f"no function named {name!r}")
    params = tuple(g.attr(p, "name") for p in g.targets(fn, "param"))
    program = []
    for i in g.targets(fn, "instr"):
        op = g.attr(i, "op")
        if op == "LABEL":
            program.append(g.attr(i, "label"))
        else:
            program.append(I(op, tuple(_load_operand(g, a) for a in g.targets(i, "arg"))))
    return params, tuple(program)


def names(g: Graph) -> tuple:
    """Every function in the library. This is what a selection layer ranks over."""
    return tuple(sorted(g.attr(n, "name") for n in g.nodes if g.kind(n) == "function"))


# --- calling -------------------------------------------------------------------------------------
def invoke(g: Graph, name: str, args: dict | None = None, **regs):
    """Call a stored function. `args` binds parameter names to nodes; each becomes a focus head.

    Returns `(focus, regs)` of the callee, so a caller reads results out of `regs["result"]` (or any
    register the callee set) and can inspect where the callee's heads ended up."""
    params, program = load(g, name)
    args = args or {}
    missing = [p for p in params if p not in args]
    if missing:
        raise TypeError(f"{name}() missing bound parameter(s): {missing}")
    from .isa import Machine
    callee = Focus()
    for p in params:
        callee.open(p, args[p])
    _, focus, out = Machine(program).run(g, callee, **regs)
    return focus, out


__all__ = ["define", "find", "load", "names", "invoke", "doc_of", "notes_of", "catalogue", "param_types", "returns_of", "producers"]

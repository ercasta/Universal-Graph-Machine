"""Functions — a rule is a function, stored in the graph as data, executed by the instruction set.

This is where "rules as data" stops being a slogan. Earlier versions of the idea stored
rule-shaped data that a fixed compiler turned into something matched; here the stored form is
turned into something run. A rule is a named program with parameters, and calling it is calling a
function.

Stored as ordered edges. A function node carries its parameters and instructions as ordered
one-to-many edges, and each instruction carries its operands the same way, so order is native
rather than reconstructed from sequencing facts. Without ordered targets this encoding would need
a position attribute on every instruction and a sort on every load.

There is no seam, and that is the load-bearing claim. A stored function is not part of a rigid
end-to-end program. Nothing runs unless something calls it, and composability comes from which
functions get called on which heads — a decision that belongs to selection rather than to a
control-flow graph fixed at authoring time. So the library can grow without any global program
having to be re-verified.

The calling convention holds the one real decision: a callee gets a fresh focus containing only
its bound parameters, never the caller's heads. Sharing the caller's focus would make every
function silently sensitive to where the caller happened to be looking, which is the
ambient-context defect this design exists to remove. Registers are likewise fresh, and a result
comes back through the `result` register.

See `docs/concepts.md`.
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
           returns: str | None = None, mocks: str | None = None) -> str:
    """Store a function as graph data. Returns the function node.

    A label (a bare string in `program`) is stored as an instruction whose op is `LABEL`, so the stored
    form stays a flat ordered list rather than needing a second representation for jump targets.

    `doc` is the function's natural-language description and `notes` maps instruction index to a
    natural-language note. Both are stored, not discarded, and that is deliberate: the description is
    what a selection layer ranks over and what a language model reads to decide whether this function is
    the one to call. A comment that only survives in a source file is invisible to the running system;
    stored on the node, it is ordinary data any microfunction can read — or write."""
    fn = g.mint("function", name=name)
    if doc:
        g.put(fn, doc=doc)
    if returns:
        g.put(fn, returns=returns)
    if mocks:
        target = find(g, mocks)
        if target is None:                       # loud, per the standing discipline for a bad fragment
            raise KeyError(f"{name!r} declares `mocks {mocks}` but no such function is defined "
                           f"(define the real one first)")
        g.put(fn, mocks=mocks)
        g.link(target, "mock", fn)               # Ordered — declaration order IS preference order
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


def applicable(g: Graph, name: str, args: dict) -> tuple:
    """The declared outcomes whose conditions hold of these arguments, most preferred first.

    *"A mock must map conditions to expectations, so even during planning we know what to expect if we
    perform an action on a given state"* (the user. A mock's condition is its parameter
    types, so this needs no new representation: a mock is an ordinary microfunction, a parameter type is
    already a schema over a subgraph, and `invoke` already enforces it on every call. This asks the same
    question *before* choosing rather than discovering it afterwards as a refusal.

        fn found_dirty(t: dirty_tree) -> report mocks git_status      # SET dirty true
        fn found_clean(t: clean_tree) -> report mocks git_status      # SET dirty false

    And it is what lets a conditioned mock stay branch-free, which matters beyond tidiness: a mock
    that branches internally is read by `driver.establishes` as establishing both its outcomes
    unconditionally — the linear walk does not follow jumps, and says so. Written as two conditioned
    outcomes instead, each body is exact. The condition moves from *only-runnable* to *inspectable*, which
    is the axis `docs/deliberation.md` names.

    Declaration order still decides among several that fit — that is what `mocks_of`'s preference
    ordering has always been for. An empty result means no declared outcome covers this state, which is
    a real answer and not an error: the caller decides whether that is a refusal or a reason to sense.

    A parameter absent from `args` is not tested. Partial bindings are the planner's business, and
    treating an unbound parameter as a failed condition would silently rule out every outcome."""
    from . import types as TY
    out = []
    for outcome in mocks_of(g, name):
        ptypes = param_types(g, outcome)
        if all(want is None or not TY.violations(g, args[p], want)
               for p, want in ptypes.items() if p in args):
            out.append(outcome)
    return tuple(out)


def mocks_target(g: Graph, name: str) -> str | None:
    """If this function is a mock, the function it is an outcome of."""
    f = find(g, name)
    return g.attr(f, "mocks") if f is not None else None


def mocks_of(g: Graph, name: str) -> tuple:
    """The possible outcomes of calling `name`, most preferred first.

    A call can turn out several ways — `file_list` may find nothing, one thing, or many — and those are not
    variations in degree, they lead to different plans. So a function has many mocks, each an ordinary
    microfunction whose return type is the outcome it assumes, which means the existing type-chaining
    planner plans each case differently with nothing added.

    Preference is declaration order, and it costs nothing because `mock` is an ordered edge like every
    other 1:N relation here. That is deliberately the weakest thing that could work: the old engine's
    possibilistic band layer existed to rank uncertain outcomes and was cut as machinery solving a problem
    a language model already solves. An ordered list is the residue actually needed — something has to
    decide the default assumption, or it is whichever mock happened to be declared first *by accident*
    rather than *by intent*."""
    f = find(g, name)
    return () if f is None else tuple(g.attr(m, "name") for m in g.targets(f, "mock"))


def returns_of(g: Graph, name: str) -> str | None:
    """The declared result type. This is what a planner chains backwards on: to obtain a `T`, find the
    functions that return `T`, and make their parameter types the subgoals."""
    f = find(g, name)
    return g.attr(f, "returns") if f is not None else None


def producers(g: Graph, type_name: str) -> tuple:
    """Every function whose result satisfies `type_name` — the candidate set for one backward step.

    Subtype-aware, deliberately. A function returning a `washed_car` genuinely satisfies a goal
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


def param_names(g: Graph, name: str) -> tuple:
    """The parameter names, in order. `load` returns them too, but as the first half of a pair — and
    `load(g, name)[0][1]` is a wretched way to ask for the second parameter's name, which is what
    the first consumer was reduced to writing.

    The first parameter is the SUBJECT, and that is a guarantee, not a convention. A function is a
    cast (`types.declare_type`) — it takes a thing and leaves it satisfying a stronger schema — so
    "which thing" is the first parameter, and two mechanisms here already depend on it: `execution.run`
    falls back to the first argument when a body sets no `result`, because a cast returns its subject, and
    `execution._settle` then makes the first parameter's mapping name the cast node. the first consumer asked
    whether it could build on this; it can. Anything that changes it has to change those two as well."""
    fn = find(g, name)
    return () if fn is None else tuple(g.attr(p, "name") for p in g.targets(fn, "param"))


def subject_param(g: Graph, name: str) -> str | None:
    """The parameter a call is *about* — the first one. See `param_names` for why that is guaranteed."""
    params = param_names(g, name)
    return params[0] if params else None


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
            for n in g.of_kind("function")}


# --- loading -------------------------------------------------------------------------------------
def find(g: Graph, name: str):
    for n in g.of_kind("function"):
        if g.attr(n, "name") == name:
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
    """Every function in the library, in declaration order. This is what a selection layer ranks over.

    This order is load-bearing, and it used to be the alphabet. `driver.proposals` enumerates in
    this order, and the search frontier's key ends in a tie-break, so wherever two proposals score alike
    *this* decides which world is imagined first. `sorted()` made that decision arbitrary — and measurably
    so. Measured on a three-step plan whose first move scores band 0 (a prerequisite that writes
    a different slot from the goal's), against a growing library of irrelevant operators:

        the prerequisite named `buy_ticket`     3 / 3 / 3 imagined states
        the same function named `zz_buy_ticket` 7 / 11 / 17

    The planner's cost depended on the name of a function. Renaming a function is not supposed to be a
    performance decision. The blind controls in `selftest.py` moved by up to 2.4x under reordering for the
    same reason — a control has no band at all, so the tie-break is its *entire* ordering.

    Declaration order is what the rest of this engine already uses for exactly this purpose, and says so:
    `mock` preference, `guideline` precedence and `method` precedence are all "declaration order, free via
    `of_kind`'s mint order". `driver.py`'s own module docstring has claimed "candidate ordering is
    declaration order" the whole time. This makes that true. An author can now order their library and
    have it mean something, which is the difference between a declared tie-break and an undeclared one.

    Note what this does NOT fix: a tie is still broken by *something*, and an author who has not thought
    about order gets whatever order they wrote. That is a knowable, statable default; the alphabet was not."""
    return tuple(g.attr(n, "name") for n in g.of_kind("function"))


# --- calling -------------------------------------------------------------------------------------
def invoke(g: Graph, name: str, args: dict | None = None, *, check_types: bool = True,
           caller: str | None = None, **regs):
    """Call a stored function. `args` binds parameter names to nodes; each becomes a focus head.

    Returns `(focus, regs)` of the callee, so a caller reads results out of `regs["result"]` (or any
    register the callee set) and can inspect where the callee's heads ended up.

    A declared parameter type is a precondition, and it is enforced here. It used to be checked
    only by `driver.proposals`, which is the right place for *planning* — but a signature reads like a
    precondition and is written like one, so a caller reasonably assumes it holds wherever the function is
    called. Reported by the first consumer with the case that makes it bite:
    they carried a safety property entirely in a parameter type — an irreversible checkout cannot bind to
    the operation that finishes without a confirmation gate — and had documented the guarantee as *"the
    unsafe app is unbuildable"* when it was only ever *"no plan builds it"*. Their workaround was a
    hand-written `CHECK` as the first instruction, which makes the declared type and the enforced type two
    things an author has to keep in step by hand: exactly the defect shape the rest of this design avoids.

    An undeclared parameter type refuses too, and that is deliberate rather than incidental:
    `driver.proposals` already treats one as satisfiable by nothing (line 117), so letting it through here
    would recreate the same divergence one layer up. A parameter with no type at all is unconstrained and
    passes — that is saying nothing, which is different from naming a type that does not exist.

    `check_types=False` is the opt-out for a hot path that has already checked."""
    params, program = load(g, name)
    args = args or {}
    missing = [p for p in params if p not in args]
    if missing:
        raise TypeError(f"{name}() missing bound parameter(s): {missing}")
    if check_types:
        from . import types as TY
        ptypes = param_types(g, name)
        for p in params:
            want = ptypes.get(p)
            if want is None:
                continue                       # untyped parameter: nothing was claimed, nothing to check
            bad = TY.violations(g, args[p], want)
            if bad:
                # The failure carries structure, not only a message. A caller that has to react to it —
                # `execution.step`, where a precondition gone false mid-plan is a *divergence* rather than a
                # crash — would otherwise have to re-derive which parameter failed and how, which is a
                # second implementation of this check and exactly the drift this codebase keeps recording.
                err = TY.TypeViolation(f"{name}({p}=…): {args[p]} is not a {want}: {bad}")
                err.function, err.param, err.want, err.violations = name, p, want, bad
                raise err
    from .isa import Machine
    callee = Focus(g)
    for p in params:
        callee.open(p, args[p])
    # `of=` is what lets a stopped activation say which instruction of which function it is on —
    # `function.define` already stores the body as an ordered `instr` edge in the order `load` returns it,
    # so the program counter indexes that list directly and no second record is needed.
    # `retire=False`: the callee's activation is the record of what this call did — which nodes it
    # minted, where its heads ended up, which instruction it finished on — and a Python caller holding the
    # returned focus reaches it through `activation.for_focus`. `workbench.step` and `execution._replay`
    # both need exactly that, and used to get a whole-graph diff instead.
    _, focus, out = Machine(program).run(g, callee, of=find(g, name), caller=caller,
                                         retire=False, **regs)
    return focus, out


__all__ = ["define", "find", "load", "names", "invoke", "doc_of", "notes_of", "catalogue", "param_names", "subject_param", "param_types", "returns_of", "producers", "mocks_of", "mocks_target", "applicable"]

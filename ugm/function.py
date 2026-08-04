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
from .graph import Graph, Ref, Refusal
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
    # **Several bodies may share a name, and they must take the same parameters.** Dispatch chooses
    # among bodies, so a caller binds arguments before one is chosen — which is only meaningful if every
    # candidate takes the same ones. Refused here rather than discovered at the call, where the symptom
    # would be a missing-parameter error naming a function the caller never wrote.
    for other in bodies(g, name):
        theirs = tuple(g.attr(x, "name") for x in g.targets(other, "param"))
        if theirs != tuple(params):
            raise ValueError(f"{name!r} is already defined taking {theirs}, and a second body takes "
                             f"{tuple(params)} — bodies sharing a name are dispatched between, so they "
                             f"must bind the same parameters")
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


def applicable(g: Graph, name: str, args: dict, *, under: str | None = None) -> tuple:
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
    treating an unbound parameter as a failed condition would silently rule out every outcome.

    `under` is the context the condition is asked in, for the same reason `invoke` takes one: *what will
    happen if I do this here* is answered by looking at here, and on a workbench "here" is a frame."""
    from . import access as AX, types as TY
    out = []
    for outcome in mocks_of(g, name):
        ptypes = param_types(g, outcome)
        if all(want is None or not TY.violations(g, AX.resolved(g, under, args[p]), want)
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


def param_types(g: Graph, name: str, *, fnode: str | None = None) -> dict:
    """`{param: declared type}`. What candidate generation reads to ask whether a function could apply.

    Answered for one body. Where several share a name their *types* may differ even though their
    parameters may not — that is how a sense is selected — so a reader asking about the name gets the
    first body's, which is the whole answer wherever nothing dispatches."""
    fn = fnode if fnode is not None else find(g, name)
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


# --- guards --------------------------------------------------------------------------------------
class GuardViolation(Refusal):
    """A call whose arguments do not satisfy the function's declared condition.

    A sibling of `types.TypeViolation` and the same claim about whose fault it is — the *caller* brought
    the wrong arguments — which is why it refuses at the same boundary. What differs is what could be
    said: a type constrains one argument, and a guard constrains the arguments *together*, and their
    surroundings."""


def guard(g: Graph, name: str, *, sort: str, negated: bool = False, **fields) -> str:
    """Attach one condition to a function. Returns the test node.

    A **guard** is a criterion's condition, keyed on parameters instead of on roles. That is not a
    resemblance, it is the same node kind evaluated by the same reader: `criterion.test` mints it and
    `criterion.holds` evaluates it, with `bound` mapping names to nodes — and the condition language
    cannot tell a role from a parameter, which is what lets one mechanism serve both.

    Why this exists, in one measured line: `driver.enumerate_frame` carried a hardcoded correctness rule
    — *no node in two roles* — and said why, that `types.py` validates one argument at one call site, so
    **a relation between parameters has no declared form**. It has one now.

    Each condition is its own node, so a refusal can say *which* one failed. That is the property
    `criterion.governing` is built on, and an opaque predicate could never give it."""
    from . import criterion as CR
    fnode = find(g, name)
    if fnode is None:
        raise KeyError(f"no function named {name!r}")
    # Stored under `test`, the label a criterion uses, and that is not laziness. `precedence._covers`
    # compares two rules by reading their tests, and specificity is the whole basis on which one body is
    # chosen over another — so a second label would mean a second comparator, agreeing by hand. One
    # mechanism serving both is the claim; using one label is what makes it true rather than said.
    return CR.test(g, fnode, sort=sort, negated=negated, **fields)


def guards_of(g: Graph, name: str, *, fnode: str | None = None) -> tuple:
    node = fnode if fnode is not None else find(g, name)
    return () if node is None else g.targets(node, "test")


def unmet_guards(g: Graph, name: str, args: dict, *, frame=None, under: str = "root",
                 fnode: str | None = None) -> tuple:
    """Which of this function's conditions do not hold of these arguments, rendered for a reader.

    Empty means the function applies. **The answering form**, and it exists beside the refusal in
    `invoke` on purpose: the planner has to *filter* candidates and an exception is useless in a loop,
    while a call site has to *refuse* and a boolean is useless at a boundary. This codebase keeps finding
    that the enforcing form arrives first and the answering one is missing; here they arrive together.

    `frame` is the world to evaluate in — a guard reads the surroundings, and reading them in reality
    while the body it guards reads a frame is the defect the parameter-type check had until recently."""
    from . import criterion as CR
    node = fnode if fnode is not None else find(g, name)
    if node is None:
        return ()
    return tuple(CR.describe_test(g, t) for t in g.targets(node, "test")
                 if not CR.holds(g, t, args, frame, under))


def applies(g: Graph, name: str, args: dict, *, frame=None, under: str = "root",
            fnode: str | None = None) -> bool:
    """Would this call satisfy the declared conditions? The predicate behind selection."""
    return not unmet_guards(g, name, args, frame=frame, under=under, fnode=fnode)


def bodies(g: Graph, name: str) -> tuple:
    """Every body defined under this name, in declaration order.

    **A name may have several.** That is the whole of dynamic dispatch here, and it is worth saying why
    it is not merely convenient. The alternative to dispatching is to mangle: `go_to_river_bank` beside
    `go_to_financial_bank`, a name per combination of senses, and the count multiplies with every
    distinction a domain draws. Worse than the count is what the names *are* — a mangled name has the
    distinguishing condition baked into an identifier, where nothing can read it, so the relation between
    the two senses is gone and each name is an island the second caller creates. Dispatch keeps the
    condition as data and the senses related by sharing a name, which is the same argument
    `docs/mediated-access.md` makes for lowering to a name rather than to an opcode: a name is where
    meaning lives.

    Declaration order, because that is the last stage of the ladder and it is total — see `select`."""
    return tuple(n for n in g.of_kind("function") if g.attr(n, "name") == name)


def select(g: Graph, name: str, args: dict, *, frame=None, under: str = "root", found=None):
    """Which body this call means: the most specific one whose conditions hold. `None` if none does.

    **Most specific first, and declaration order among equals.** Specificity over arbitrary conditions is
    entailment between predicates and not computable, so `precedence._covers` answers it syntactically
    and answers *no* when it cannot tell — *"a false negative loses an ordering the author could have
    had, a false positive claims a precedence the author never wrote"*. Two bodies whose guards are
    incomparable therefore tie, and the tie is broken by **declaration order**, which is authored rather
    than arbitrary and is what `mocks_of`'s preference ordering has always been.

    That is the honest shape of it: the order is partial, the fallback is total, and an author who cares
    which of two incomparable readings wins says so by writing one first.

    A single body with no guard is the overwhelmingly common case and costs one list lookup."""
    from . import precedence as PR
    found = bodies(g, name) if found is None else found
    if not found:
        return None
    fit = [n for n in found if applies(g, name, args, frame=frame, under=under, fnode=n)]
    if not fit:
        return None
    # Insertion sort on a partial order — never `sorted`, which needs a total comparator and would put an
    # incomparable pair in whatever order the algorithm happened to visit them. This keeps declaration
    # order except where one body demonstrably covers another.
    out = []
    for cand in fit:
        at = len(out)
        for i, seen in enumerate(out):
            if PR._covers(g, cand, seen) and not PR._covers(g, seen, cand):
                at = i
                break
        out.insert(at, cand)
    return out[0]


def load(g: Graph, name: str, *, fnode: str | None = None) -> tuple:
    """Lift a stored function back to `(params, program)`. Raises if it is not there — loudly, per this
    project's standing discipline for a malformed or missing fragment.

    `fnode` names *which* body, for a caller that has already selected one. Without it this answers with
    the first body of that name, which is the only body wherever nothing dispatches."""
    fn = fnode if fnode is not None else find(g, name)
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
           caller: str | None = None, retain: bool = True, under: str | None = None, **regs):
    """Call a stored function. `args` binds parameter names to nodes; each becomes a focus head.

    Returns `(focus, regs)` of the callee, so a caller reads results out of `regs["result"]` (or any
    register the callee set) and can inspect where the callee's heads ended up.

    `retain=False` throws the call's own scaffolding away when it finishes — the activation, its
    registers, the focus minted for it and that focus's heads, ~5 nodes a call. It is a **call-site**
    choice rather than a policy because only the caller knows whether it is going to ask what the call
    did, and the two answers are both right: `execution._replay` and `workbench.step` read the callee's
    activation afterwards, while a rule reading a slot through a procedure wants nothing left behind.
    Retention is the Python default because a Python caller is handed the focus and normally reads it;
    the surface's `INVOKE` chooses the other way and says `keep` when it means to inspect. That
    asymmetry is the point: once a graph *read* is a call, the reads are the many, and this system has
    already once mistaken its own interpreter scaffolding for world content and type-checked it as a
    domain object.

    What a discarded call did is not discarded with it: its `minted` record moves to the caller before
    the activation goes, so `activation.minted` answers exactly what it did before — that walk unions a
    callee's mints into its caller's anyway. Only the *per-call* breakdown is given up, which is
    precisely what the call site said it did not want.

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
    from . import access as AX
    args = args or {}
    found = bodies(g, name)
    if not found:
        raise KeyError(f"no function named {name!r}")
    # Parameters before selection, because a guard speaks OF the parameters: asking whether a body
    # applies to a binding that is missing one would answer "it does not", and the caller would be told
    # its call did not apply when what it did was leave an argument out.
    params = tuple(g.attr(x, "name") for x in g.targets(found[0], "param"))
    missing = [p for p in params if p not in args]
    if missing:
        raise TypeError(f"{name}() missing bound parameter(s): {missing}")

    # **Which body this name means here.** Always, not only when several are defined — selection is what
    # the call *means*, and a single body with no conditions costs one edge read. The context is `under`
    # at a boundary that establishes one and the caller's otherwise, which is the same dynamic scope
    # every read beneath this call will find.
    ctx = under if under is not None else AX.context_of(g, caller)
    ctx_frame = g.target(ctx, "frame") if ctx is not None else None
    fnode = select(g, name, args, frame=ctx_frame, found=found)
    if fnode is None:
        # Nothing applies. The enforcing half of `applies`, and it reports every candidate's reason
        # rather than the first — with several bodies, *why did none of them mean this* is a question
        # about the set, and naming one would send a reader to the wrong body.
        why = "; ".join(f"{'' if len(found) == 1 else f'[{i}] '}" + ", ".join(
            unmet_guards(g, name, args, frame=ctx_frame, fnode=n) or ("no reason recorded",))
            for i, n in enumerate(found))
        err = GuardViolation(f"{name}(…) does not apply here: {why}")
        err.function, err.unmet = name, why
        raise err
    _params, program = load(g, name, fnode=fnode)
    if check_types:
        from . import types as TY
        # **The precondition is checked in the world the body will run in.** A parameter type reads like a
        # precondition and is enforced like one, so it has to be asked of the same world the rule is about
        # to read — otherwise a rule imagined on a workbench is admitted or refused on the strength of
        # reality, one frame away from the state it is actually being run in. The context is `under` at a
        # boundary that establishes one, and the caller's otherwise, which is the same dynamic scope
        # every read beneath this call will find.
        ptypes = param_types(g, name, fnode=fnode)
        for p in params:
            want = ptypes.get(p)
            if want is None:
                continue                       # untyped parameter: nothing was claimed, nothing to check
            bad = TY.violations(g, AX.resolved(g, ctx, args[p]), want)
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
    # `under` is a Python *boundary* establishing the world this call reads in — `workbench.step` and
    # `execution` are the two that do. It is not a context being threaded: nothing below sees it as an
    # argument, the callee's callees inherit it by walking `caller`, and a rule never names one.
    _, focus, out = Machine(program).run(g, callee, of=fnode, caller=caller,
                                         retire=False, under=under, **regs)
    if not retain:
        # `scrap`, not `retire`: this focus was minted here and handed to nobody, so leaving it would
        # leave the larger half of the residue behind. The returned focus is a dead pointer afterwards,
        # which is what asking not to retain the call means.
        from . import activation as A
        act = A.for_focus(g, focus.node)
        if act is not None:
            if caller is not None:
                for made in A.minted(g, act):
                    A.record_mint(g, caller, made)
            A.scrap(g, act)
    return focus, out


# Resolving a function's NAME to its node, for programs written in the surface. `workbench.step` needs it
# four times over — to read the outcomes, the declared result type, the parameter types, and to link
# `applies` — and every one of those is an ordinary edge read *once you have the node*.
#
# A native rather than an opcode, and the argument is `types.instances`'. Decomposing `find` does not
# reach a loop over nodes; it reaches `g.of_kind`, and handing the surface a way to enumerate every node
# of a kind is exactly the whole-graph scan that module refuses at length — *enumerated by traversal,
# never by scanning*, because a scan finds the system's own imaginings and offers them as candidates. The
# name index is this layer's business, so this layer registers it, which is `native.py`'s rule and
# `types.is_a`'s precedent.
#
# The registration lives here, beside what it registers, never in `native.py` — a table of names in that
# file would be the same leak with an extra hop.
from . import native as _N                                            # noqa: E402
_N.register("find_function", lambda g, _act, name: find(g, name))

__all__ = ["define", "find", "load", "names", "invoke", "doc_of", "notes_of", "catalogue", "param_names", "subject_param", "param_types", "returns_of", "producers", "mocks_of", "mocks_target", "applicable"]

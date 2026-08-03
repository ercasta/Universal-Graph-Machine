"""Method — an authored decomposition, as data, that selects itself.

A method says: for a goal of this shape, in this context, raise these subgoals in this order —
and whether falling back to search is permitted if it does not work out. `driver.follow` runs a
decomposition; this is what builds one, so an author never assembles subgoals by hand.

A method is data, per the standing principle that functions ship with the engine and everything a
domain contributes is data. The matcher and the applier ship here; the methods themselves are
nodes an author writes, a reader can inspect, and a conflict detector can dispute. That is why
the condition is a pattern rather than a program: two programs cannot be compared for
disagreement, a controlled language cannot refuse a bad one, and neither can a reader.

It prunes on authority, which is a third justification and must be named rather than smuggled in.
A prohibition prunes on a proof; a guideline ranks a guess. A method replaces enumeration
outright, which is where the exponential win lives — a decomposition instead of thousands of
proposals — and also why it cannot be expressed as a ranker. The price is completeness: a wrong
or non-covering method could make a reachable goal unreachable, and the only thing standing
between that and disaster is the advisory fallback. Hence the check that a goal solvable by
search stays solvable when a non-covering method is added.

How context is expressed. A method is generic, so it cannot name an individual ancestor goal, and
letting authors unroll context into position-specific methods would be a labelling error. The
structural answer is that a subgoal raised by a method points at that method, so "within a goal
raised by M" is an ordinary walk up the goal ancestry asking a structural question. No strings,
no goal taxonomy, and it works for recursion.

Roles, not nodes. A step says the subject of the matched constraint, never a particular block;
otherwise a method would be about individuals and could not be reused, which is exactly why a
type schema may not name a target either.

See `docs/deliberation.md`.
"""
from __future__ import annotations

from . import consequent as CQ
from . import goal as G
from .graph import Graph
from .types import is_a

SUBJECT, OBJECT = "subject", "object"


def method(g: Graph, *, handles: str, label: str | None = None, when: str | None = None,
           within=None, force: str = G.ADVISORY, name: str | None = None,
           because: str | None = None) -> str:
    """Declare a method. `handles` is a constraint sort (`link`/`attr`/`type`); `label` narrows it to a
    particular edge label or attribute key; `when` is a type the constraint's subject must satisfy;
    `within` is another method, meaning this one only applies beneath a goal that one raised."""
    if handles not in ("link", "attr", "type"):
        raise ValueError(f"a method handles a constraint sort, not {handles!r}")
    if force not in G.FORCES:
        raise ValueError(f"force must be one of {G.FORCES}, not {force!r}")
    m = g.mint("method", handles=handles, force=force,
               **{k: v for k, v in (("label", label), ("when", when), ("name", name),
                                    ("because", because)) if v is not None})
    if within is not None:
        g.link(m, "within", within)
    return m


def step(g: Graph, m: str, *, sort: str, label: str | None = None, key: str | None = None,
         value=None, subject: str = SUBJECT, object: str = OBJECT, note: str | None = None) -> str:
    """Append a step. Steps are an ordered edge, so declaration order is the `then` order, free —
    the same free ordering `mock` and `guideline` already rely on.

    A step is a consequent — the `achieve` kind, per `consequent.py`. It was its own `mstep` node
    until the two right-hand sides were measured and found to differ in shape but not in reach."""
    return CQ.achieve(g, m, sort=sort, label=label, key=key, value=value,
                      subject=subject, object=object, note=note)


def draw(g: Graph, m: str, *, name: str, ref: str, label: str, back: bool = False) -> str:
    """`some <name> in <ref> by <link>` — bind a further role for this method's steps.

    The same form `criterion.draw` already provides, and it was missing here for no good reason. A
    method could speak only of `subject` and `object` — the matched constraint's — so a decomposition whose
    steps concern a third individual had no form at all. That is the gap `docs/deliberation.md`
    recorded for criteria, fixed there and never carried across; an earlier probe found it again
    from the other side, on *"after you edit a file, lint that file"*.

    Singular, and that restraint is the design, not a shortcut. A draw reaches a *set*, and raising
    one subgoal per candidate is exactly what `docs/limits.md` forbids first: *do not expand the plural
    step at plan time into N singular steps*, because a plan expanded over today's members is valid only
    for the collection as it was when planned. So this binds the nearest candidate, like the reference
    language everywhere else, and the plural case stays where that document put it — slice B/C.

    And *"do it to each of them"* does not need this: slice A's `goal.witnesses` already makes a
    universal constraint plannable one member at a time, measured. This is for naming one related thing."""
    d = g.mint("draw", name=name, ref=ref, label=label, back=back)
    g.link(m, "draw", d)
    return d


def draws_of(g: Graph, m: str) -> tuple:
    return g.targets(m, "draw")


def roles_of(g: Graph, m: str) -> tuple:
    """Every role this method's steps may speak of: the two the constraint binds, plus what it has drawn."""
    return (SUBJECT, OBJECT) + tuple(g.attr(d, "name") for d in draws_of(g, m))


def act(g: Graph, m: str, *, function: str, bindings: dict, as_: str | None = None) -> str:
    """Append an action. A `do` rung, as opposed to `step`'s `achieve` rung.

    **The distinction the two rungs draw is subgoal versus subprocedure**, and it is the one
    `consequent.py` already tags. A `step` says what must become true and leaves the choice of how to the
    engine — means-ends, with search and fallback behind it. A `do` says which function to call, closing
    the choice. A procedure decomposes into *subprocedures*: the named function may itself be one, and
    termination comes from authoring rather than from a depth limit, which is what makes it an act of
    faith rather than a plan.

    `as_` names the result so a later rung can use it. Without it a rung's output is unreachable, which
    is fine for a rung called only for its effect."""
    c = CQ.call(g, m, function=function, bindings=bindings)
    if as_:
        g.put(c, **{"as": as_})
    return c


def calls_of(g: Graph, m: str) -> tuple:
    """The `do` rungs, in order."""
    return tuple(c for c in CQ.of(g, m) if g.attr(c, "does") == CQ.CALL)


def achieves_of(g: Graph, m: str) -> tuple:
    """The `step` rungs, in order — what `decompose` reads."""
    return tuple(c for c in CQ.of(g, m) if g.attr(c, "does") == CQ.ACHIEVE)


def params_of(g: Graph, m: str) -> tuple:
    """`(name, type | None)` per declared parameter, in order."""
    return tuple((g.attr(p, "name"), g.attr(p, "type")) for p in g.targets(m, "takes"))


def lower(g: Graph, m: str, *, name: str, params: tuple) -> str:
    """Compile a procedure of `do` rungs to assembly text. Returns what `asm.load_text` will read.

    **No third executor was needed, and finding that out is the point.** A sequence of calls run in
    order, each result nameable by the next, *is* a function body of `INVOKE` instructions — and an
    activation is already a task on the agenda that advances one instruction per tick, already has a
    verb reported before each step, already runs inside a savepoint. Adding a task kind would have meant
    four new branches in `loop.py` for something the interpreter already does. The test that caught it is
    the same one that dissolved `open_workbench`: decompose before believing it is primitive.

    **Text, not instruction objects.** Emitting assembly and reading it back through `asm` costs a parse
    and buys two things: the lowering goes through the border that validates opcodes and `INVOKE`'s
    operand shape, rather than around it; and *what did my procedure compile to?* has an answer a person
    can read. A lowering nobody can see is the island pattern with an extra step.

    A reference is `F(x)` when it names a parameter and `R(x)` when an earlier rung bound it with `as`.
    Anything else is refused by the caller — a procedure that named an individual would be about that
    individual and could not be reused, the same reason a `step` may only speak of roles.

    `params` is `(name, type | None)` pairs, and a type is emitted as an annotation so that
    `function.invoke` enforces it on every call. That is the whole of the parameter check: it is not
    added here, it is *reached* — the precondition machinery already existed and a procedure simply had
    nothing to declare into it."""
    sig = ", ".join(f"{p}: {t}" if t else p for p, t in params)
    # `bound` holds names a rung ASSIGNED — never the parameters. A parameter is a focus head and a
    # rung result is a register, so seeding this with the parameters inverts the one distinction `_ref`
    # exists to make, and the program then reads an unset register where the argument was.
    lines, bound, state = [f"fn {name}({sig}):"], set(), {"n": 0, "last": None}
    _emit(g, m, lines, bound, state)
    if state["last"] is not None:
        # The last rung's result is the procedure's, so a caller reads it where every other function
        # puts one. Without this a procedure could only ever be called for its effect.
        lines.append(f"    COPY R(result) R({state['last']})")
    return "\n".join(lines)


def _ref(name: str, bound) -> str:
    """A parameter is a focus head; anything a rung bound is a register. Getting this backwards
    compiles cleanly and reads an unset register at run time, which is why it is one function."""
    return f"R({name})" if name in bound else f"F({name})"


def _emit(g: Graph, owner: str, lines: list, bound: set, state: dict, depth: int = 0) -> None:
    """Walk one body, appending assembly. Recurses into containers.

    Labels are numbered from a counter carried in `state` rather than from the nesting depth, because
    two sibling blocks at the same depth would collide — and a duplicate label in this assembler is not
    an error, it is a jump to the wrong place."""
    for c in CQ.of(g, owner):
        does = g.attr(c, "does")
        if does == CQ.CALL:
            args = []
            for a in g.targets(c, "arg"):
                ref = g.attr(a, "ref")
                args.append(f"{g.attr(a, 'param')}={_ref(ref, bound)}")
            out = g.attr(c, "as") or f"_r{state['n']}"
            state["n"] += 1
            lines.append(f"    INVOKE R({out}) {g.attr(c, 'function')} " + " ".join(args))
            bound.add(out)
            # Only a TOP-LEVEL rung can be the procedure's result. A rung inside a loop or a guard may
            # not have run, and copying its register would read an unset one and raise — turning "the
            # condition was false" into a crash at the last instruction. Measured: a procedure whose
            # final rung sat inside a `when` compiled fine and died on the copy.
            if depth == 0:
                state["last"] = out
        elif does == CQ.GUARD:
            state["n"] += 1
            end = f".past{state['n']}"
            _test(g, c, lines, bound, state)
            # `JMPNOT` on the test's own register. A guard whose test is false skips the block rather
            # than skipping the rest of the body — the block is what the author indented.
            lines.append(f"    {'JMPIF' if g.attr(c, 'negated') else 'JMPNOT'} R(_t{state['n']}) {end}")
            _emit(g, c, lines, bound, state, depth + 1)
            lines.append(f"{end}:")
        elif does == CQ.ITERATE:
            state["n"] += 1
            i, top, end = f"_i{state['n']}", f".loop{state['n']}", f".done{state['n']}"
            over, by = _ref(g.attr(c, "over"), bound), g.attr(c, "by")
            # The collection is counted ONCE, before the block runs. Re-counting each pass would make a
            # body that appends to what it walks loop forever, and a construct chosen because it cannot
            # diverge must not depend on the body being polite.
            lines.append(f"    COUNT R(_n{state['n']}) {over} \"{by}\"")
            lines.append(f"    CONST R({i}) 0")
            lines.append(f"{top}:")
            lines.append(f"    LT R(_m{state['n']}) R({i}) R(_n{state['n']})")
            lines.append(f"    JMPNOT R(_m{state['n']}) {end}")
            lines.append(f"    GET_AT R({g.attr(c, 'name')}) {over} \"{by}\" R({i})")
            bound.add(g.attr(c, "name"))
            _emit(g, c, lines, bound, state, depth + 1)
            lines.append(f"    ADD R({i}) R({i}) 1")
            lines.append(f"    JMP {top}")
            lines.append(f"{end}:")


def _test(g: Graph, c: str, lines: list, bound: set, state: dict) -> None:
    """Put a guard's test in `R(_tN)`. Three shapes, each one or two instructions."""
    kind, left, t = g.attr(c, "test"), _ref(g.attr(c, "left"), bound), f"_t{state['n']}"
    if kind == "attr":
        lines.append(f"    ATTR R(_v{state['n']}) {left} \"{g.attr(c, 'key')}\"")
        lines.append(f"    EQ R({t}) R(_v{state['n']}) {_literal(g.attr(c, 'value'))}")
    elif kind == "there":
        # `is there` asks whether the reference denotes anything — an empty tuple, `None` and an unset
        # register are all "nothing", which `NOT` already collapses correctly.
        lines.append(f"    NOT R(_z{state['n']}) {left}")
        lines.append(f"    NOT R({t}) R(_z{state['n']})")
    else:
        lines.append(f"    NATIVE R({t}) \"is_a\" {left} \"{g.attr(c, 'label')}\"")


def _literal(v) -> str:
    return {True: "true", False: "false", None: "null"}.get(v, f'"{v}"' if isinstance(v, str) else str(v))


def steps_of(g: Graph, m: str) -> tuple:
    return CQ.of(g, m)


def methods(g: Graph) -> tuple:
    """Every method, in declaration order — precedence order, free via `of_kind`'s mint order.

    Withdrawn methods are skipped — see `discourse.py`."""
    from .discourse import live
    return live(g, g.of_kind("method"))


def raised_by(g: Graph, goal: str):
    """The method that raised this subgoal, if one did."""
    return g.target(goal, "by")


def under_method(g: Graph, goal: str, m: str) -> bool:
    """Is `goal` at or beneath a goal raised by method `m`? This is how context is asked, and it is a
    structural walk rather than a name match — see the module docstring."""
    return any(raised_by(g, anc) == m for anc in G.ancestry(g, goal))


def matches(g: Graph, m: str, goal: str, c: str) -> bool:
    """Does method `m` handle constraint `c` of `goal`?"""
    if g.attr(c, "sort") != g.attr(m, "handles"):
        return False
    want = g.attr(m, "label")
    if want is not None and want not in (g.attr(c, "label"), g.attr(c, "key"), g.attr(c, "type")):
        return False
    when = g.attr(m, "when")
    if when is not None and not is_a(g, g.target(c, "subject"), when):
        return False
    ctx = g.target(m, "within")
    return ctx is None or under_method(g, goal, ctx)


def applicable(g: Graph, goal: str, *, view=None, under: str | None = None) -> tuple:
    """`(method, constraint)` pairs that could decompose this goal, in declaration order.

    Asked of the goal's unmet constraints only. A method for something already true would raise
    subgoals for work nobody needs — the same reason `unmet` rather than `constraints` drives planning."""
    open_now = G.unmet(g, goal, view=view, under=under)
    return tuple((m, c) for m in methods(g) for c in open_now if matches(g, m, goal, c))


def _role_node(g: Graph, c: str, role: str, bound: dict | None = None):
    if bound and role in bound:
        return bound[role]
    return g.target(c, SUBJECT) if role == SUBJECT else g.target(c, OBJECT)


def _bind_draws(g: Graph, m: str, c: str) -> dict:
    """Resolve this method's drawn roles against the world, nearest-first.

    A draw that reaches nothing leaves its name unbound, and `decompose` then refuses rather than
    raising a subgoal about `None`. `criterion._expand` makes the same call for the same reason: *"some
    container inside the warehouse"* when there is none is a situation the method has nothing to say
    about, not a method with a hole in it. Silently raising a subgoal with no subject is how a
    decomposition ends up looking done because it was never really posed."""
    from .path import via
    bound: dict = {}
    for d in draws_of(g, m):
        start = _role_node(g, c, g.attr(d, "ref"), bound)
        if start is None:
            continue
        reached = via(g, start, g.attr(d, "label"), back=bool(g.attr(d, "back")))
        if reached:
            bound[g.attr(d, "name")] = reached[0]
    return bound


def decompose(g: Graph, m: str, goal: str, c: str) -> tuple:
    """Raise `m`'s steps as subgoals of `goal`, in order, and return them.

    Each subgoal points at the method that raised it (`by`), which is what makes `under_method` — and so
    every context-conditioned method — structural rather than a name match."""
    steps = steps_of(g, m)
    if not steps:
        raise ValueError(f"method {g.attr(m, 'name') or m} has no steps; it would decompose into nothing, "
                         "which `goal.decomposed` would then read as an undecomposed goal")
    # A method is a route, NOT a redefinition — and getting this wrong poisoned the fallback that makes
    # authority safe. The first version stamped `BY_STEPS` on every decomposed goal, so a goal with real
    # world constraints stopped being judged by them: when the advisory method then failed and `follow`
    # fell back to searching for that same goal, the goal could no longer be satisfied *by any route*,
    # because its criterion had been rewritten to "my steps are done" and its steps were the ones that had
    # just failed. The decomposition silently destroyed the escape hatch it depends on.
    #
    # So the grounding is only rewritten when there is nothing to rewrite: a goal with its own constraints
    # keeps them, and the steps are merely how we propose to get there. A goal with none — *"do these
    # steps, in this order"* — is a procedure, and having followed them IS being met.
    bound = _bind_draws(g, m, c)
    for s in steps:
        for role in (g.attr(s, "subject_role"), g.attr(s, "object_role")):
            if role is not None and role not in (SUBJECT, OBJECT) and role not in bound:
                raise ValueError(
                    f"method {g.attr(m, 'name') or m} draws {role!r} and the traversal reached nothing, so "
                    f"there is no individual to raise a subgoal about. Refused rather than decomposed into "
                    f"a step with no subject.")
    g.put(goal, force=g.attr(m, "force"))
    if not G.world_constraints(g, goal):
        g.put(goal, met_by=G.BY_STEPS)
    raised, previous = [], None
    for s in steps:
        sub = G.open_goal(g, label=g.attr(s, "note") or f"step of {g.attr(m, 'name') or m}",
                          under=goal, because=g.attr(m, "because"))
        g.link(sub, "by", m)
        subject = _role_node(g, c, g.attr(s, "subject_role"), bound)
        sort = g.attr(s, "sort")
        if sort == "link":
            G.require_link(g, sub, subject, g.attr(s, "label"),
                           _role_node(g, c, g.attr(s, "object_role") or OBJECT, bound))
        elif sort == "attr":
            G.require_attr(g, sub, subject, g.attr(s, "key"), g.attr(s, "value"))
        else:
            G.require_type(g, sub, g.attr(s, "label"), about=subject)
        if previous is not None:
            G.then(g, previous, sub)
        previous = sub
        raised.append(sub)
    return tuple(raised)


__all__ = ["SUBJECT", "OBJECT", "method", "step", "draw", "draws_of", "roles_of", "steps_of", "methods",
           "raised_by", "under_method", "matches", "applicable", "decompose"]

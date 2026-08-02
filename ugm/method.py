"""METHOD — an authored decomposition, as data, that selects itself.

`docs/deliberation.md` `driver.follow` already runs a decomposition; this is what *builds* one, so an author
never assembles subgoals by hand. A method says: **for a goal of this shape, in this context, raise these
subgoals in this order** — and whether falling back to search is permitted if it does not work out.

**⭐ A method is DATA, per the standing principle that microfunctions ship with the engine.** The matcher
and the applier ship here; the methods themselves are nodes an author writes, a reader can inspect, and
`conflict.py` can be taught to dispute. That is why the condition is a **pattern** rather than a program:
two programs cannot be compared for disagreement, a CNL cannot refuse a bad one, and neither can a reader.

**⭐⭐ It prunes on AUTHORITY — a third justification, and it must be named rather than smuggled in.**
`goal.forbid_action` prunes on a *proof*; `guideline.py` merely ranks a *guess*. A method replaces
enumeration outright, which is where the exponential win lives (a decomposition instead of thousands of
proposals) and also why it cannot be expressed as a ranker. The price is **completeness**: a wrong or
non-covering method could make a reachable goal unreachable, and the only thing standing between that and
disaster is the `ADVISORY` fallback. Hence the check that a goal solvable by search **stays solvable** when
a non-covering method is added.

**⭐ How CONTEXT is expressed, which was the open question.** A method is generic, so it cannot name an
individual ancestor goal — and letting authors unroll context into position-specific methods would be the
labelling error `goal.ancestry` exists to avoid. The structural answer: a subgoal raised by a method
**points at that method**, so *"within a goal raised by `M`"* is an ordinary walk up `goal.ancestry` asking
a structural question. No strings, no goal taxonomy, and it works for recursion.

⚠ **Roles, not nodes.** A step says *the subject of the matched constraint*, never a particular block —
otherwise a method would be about individuals and could not be reused, which is exactly why
`types.py` refuses to let a schema name a target.
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
    `within` is another **method**, meaning this one only applies beneath a goal that one raised."""
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
    """Append a step. Steps are an **ordered** edge, so declaration order is the `then` order, free —
    the same free ordering `mock` and `guideline` already rely on.

    ⭐ A step **is a consequent** — the `achieve` kind, per `consequent.py`. It was its own `mstep` node
    until the two right-hand sides were measured and found to differ in shape but not in reach."""
    return CQ.achieve(g, m, sort=sort, label=label, key=key, value=value,
                      subject=subject, object=object, note=note)


def draw(g: Graph, m: str, *, name: str, ref: str, label: str, back: bool = False) -> str:
    """`some <name> in <ref> by <link>` — bind a **further** role for this method's steps.

    **⭐ The same form `criterion.draw` already provides, and it was missing here for no good reason.** A
    method could speak only of `subject` and `object` — the matched constraint's — so a decomposition whose
    steps concern a **third** individual had no form at all. That is the gap `docs/deliberation.md`
    recorded for criteria, fixed there and never carried across; an earlier probe found it again
    from the other side, on *"after you edit a file, lint THAT file"*.

    **⚠⚠ SINGULAR, and that restraint is the design, not a shortcut.** A draw reaches a *set*, and raising
    one subgoal per candidate is exactly what `docs/limits.md` forbids first: *do not expand the plural
    step at plan time into N singular steps*, because a plan expanded over today's members is valid only
    for the collection as it was when planned. So this binds the **nearest** candidate, like the reference
    language everywhere else, and the plural case stays where that document put it — slice B/C.

    ⚠ And *"do it to each of them"* does **not** need this: slice A's `goal.witnesses` already makes a
    universal constraint plannable one member at a time, measured. This is for naming ONE related thing."""
    d = g.mint("draw", name=name, ref=ref, label=label, back=back)
    g.link(m, "draw", d)
    return d


def draws_of(g: Graph, m: str) -> tuple:
    return g.targets(m, "draw")


def roles_of(g: Graph, m: str) -> tuple:
    """Every role this method's steps may speak of: the two the constraint binds, plus what it has drawn."""
    return (SUBJECT, OBJECT) + tuple(g.attr(d, "name") for d in draws_of(g, m))


def steps_of(g: Graph, m: str) -> tuple:
    return CQ.of(g, m)


def methods(g: Graph) -> tuple:
    """Every method, in declaration order — precedence order, free via `of_kind`'s mint order.

    ⚠ Withdrawn methods are skipped — see `discourse.py`."""
    from .discourse import live
    return live(g, g.of_kind("method"))


def raised_by(g: Graph, goal: str):
    """The method that raised this subgoal, if one did."""
    return g.target(goal, "by")


def under_method(g: Graph, goal: str, m: str) -> bool:
    """Is `goal` at or beneath a goal raised by method `m`? **This is how context is asked**, and it is a
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
    """`(method, constraint)` pairs that could decompose this goal, in **declaration order**.

    ⚠ Asked of the goal's **unmet** constraints only. A method for something already true would raise
    subgoals for work nobody needs — the same reason `unmet` rather than `constraints` drives planning."""
    open_now = G.unmet(g, goal, view=view, under=under)
    return tuple((m, c) for m in methods(g) for c in open_now if matches(g, m, goal, c))


def _role_node(g: Graph, c: str, role: str, bound: dict | None = None):
    if bound and role in bound:
        return bound[role]
    return g.target(c, SUBJECT) if role == SUBJECT else g.target(c, OBJECT)


def _bind_draws(g: Graph, m: str, c: str) -> dict:
    """Resolve this method's drawn roles against the world, nearest-first.

    ⚠ A draw that reaches **nothing** leaves its name unbound, and `decompose` then refuses rather than
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
    # ⚠⚠ A METHOD IS A ROUTE, NOT A REDEFINITION — and getting this wrong poisoned the fallback that makes
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

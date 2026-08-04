"""Goal — a desired state, specified as constraints that must hold.

A goal is a node and each thing it requires is a node under it, so the one thing the system is
trying to do is something it can point at, hypothesise about, and record having pursued.

Three sorts of constraint, because three questions genuinely differ:

* link — `a` must be `on` `b`. A specific edge between specific individuals.
* attr — `b` must be clear. A specific value on a specific node.
* type — something must be a `three_high`. A reusable schema, optionally about a named subject;
  without one it asks whether anything in the region qualifies.

A link constraint cannot simply be a type. A schema says a label, a kind and a count, never a
particular target, and that is not an oversight: a type mentioning specific nodes would not be a
schema, because a schema is reusable and individuals are not. So "a on b" has no home in the type
system and needs its own form, and a goal can hold both.

A knowledge claim is a fourth, different requirement: go and look, rather than make it so. It is
restricted to attribute slots, because an absent attribute means "lacks it" and a claim about an
absent edge would have nowhere to hang a marker.

Satisfaction is checked, never asserted, for the same reason a cast records nothing: the
structure either holds now or it does not. `is_closed` — we recorded meeting it — and `satisfied`
— it holds — are deliberately different questions, so a stale record can never be mistaken for a
current fact.

`unmet` is the point. A goal that can only answer yes or no forces blind search; a goal that can
say which constraints are still false lets the driver work on what is actually missing. That
single method is the difference between means-ends and generate-and-test.

`ctx` is how one goal is asked of many worlds. The same constraint is checked against reality and
against imagined states, and the caller says which by passing a **context** — the node that says
what a read means for the extent of the call. `None` is the trivial context, which is reality.

It used to be a `view`: a function mapping a node to the node that stands for it here. That was the
same information in the shape a *Python* caller could use, and it was the one thing standing between
`holds` and the surface, because a rule does not take a view — it resolves through the ambient
context and so must be *told* one. Two spellings of the same world is exactly the doubling this
codebase keeps finding to be a defect in waiting, so there is now one, and it is the one both sides
can read. Whatever still wants a view derives it from the context, in `_world`.

A goal is metadata: it points at the world and is never pointed at by it.

See `docs/planning.md`.
"""
from __future__ import annotations

from .graph import UNKNOWN, Graph
from .types import instances, is_a, offenders as _offenders


def _viewer(view):
    """The view as *a world to traverse in*, or `None` meaning reality.

    A view answers "which node stands for this here". Traversing needs the other direction too — from a
    node back to the identity an edge names — and only a real view offers it. The identity function
    standing in for "no view" offers nothing, and needs to: in the real world an edge's target already
    *is* the individual, so there is nothing to resolve and no cost to pay.

    Asked of the object rather than of a flag, so a caller that hands in some other view of its own is
    treated as what it is, and this module still knows nothing about workbenches."""
    return view if hasattr(view, "identity") else None


def _same(node):
    """The default `view`: a node stands for itself. Reality needs no translation."""
    return node


def _world(g: Graph, ctx):
    """The world `ctx` describes, as something traversable — or `_same` for reality.

    The one place this module turns a context into a view, and the honest statement of what is left of
    the old layering. The claim was that this module *imports no workbench*, and the import below is
    lazy and inside one function rather than at the top, which is the idiom `path.py` and `types.py`
    already use for the same crossing — a native holding an activation asks the same question.

    It is residue with a stated expiry: it survives for `_python_holds` (the reference the surface is
    checked against) and for `witnesses` / `undetermined` / `witness`, which have not moved. When those
    move, this goes, and the layering claim becomes true again rather than nearly true."""
    if ctx is None:
        return _same
    from .workbench import view_at
    return view_at(g, ctx) or _same


# --- building -----------------------------------------------------------------------------------
def open_goal(g: Graph, want: str | None = None, *, about: str | None = None,
              label: str | None = None, under: str | None = None, because: str | None = None) -> str:
    """A goal. `want` is sugar for a single type constraint, which is the commonest shape.

    `under` makes this a subgoal of another goal, and `because` records why it was raised.

    The child points at the parent, never the reverse, and the direction is load-bearing twice over.
    Ancestry — *"am I inside a `y`?"*, the question a decision rule asks — is then a walk up a path rather
    than a search down a tree, while children stay O(1) through the maintained reverse index. That is
    exactly `thread.py`'s `prev` decision and it is made here for the same reasons. It also keeps the
    metadata direction invariant: a subgoal is *about* the work its parent named.

    Parentage is set at mint and never changed, which makes a cycle structurally impossible — a
    fresh node cannot already be its own ancestor. So `ancestry` needs no visited set and cannot hang. It
    does *not* bound depth: recursive decomposition mints a fresh goal each time, so the chain grows
    without ever looping. Depth is the real termination hazard and `depth_of` is what a bound reads."""
    goal = g.mint("goal", label=label or (f"make a {want}" if want else "goal"))
    if about is not None:
        g.link(goal, "about", about)
    if under is not None:
        g.link(goal, "of", under, **({"because": because} if because else {}))
    if want is not None:
        require_type(g, goal, want, about=about)
    return goal


#: How a goal counts as met. Declared, not inferred. It could *almost* be read off the structure —
#: no constraints plus ordered children looks like a procedure — but a goal may legitimately have both, and
#: this is a statement of the author's intent rather than a fact about the graph. Same category as a
#: decomposition's force, which `docs/deliberation.md` also requires to be declared because two decompositions
#: can look identical and behave oppositely.
BY_CONSTRAINTS = "constraints"   # the default: the world must look like this
BY_STEPS = "steps"               # a procedure: being met *is* having followed the steps
MET_BY = (BY_CONSTRAINTS, BY_STEPS)

ADVISORY = "advisory"            # a method: if it does not work out, fall back to searching
MANDATORY = "mandatory"          # a procedure: if it does not work out, REFUSE — do not improvise
FORCES = (ADVISORY, MANDATORY)


# --- hierarchy ----------------------------------------------------------------------------------
def parent_of(g: Graph, goal: str):
    """The goal this one was raised under, or `None` for a goal nobody decomposed into."""
    return g.target(goal, "of")


def subgoals(g: Graph, goal: str) -> tuple:
    """The goals raised under this one — O(1) via the reverse index, not a scan."""
    return tuple(s for s in g.sources(goal, "of") if g.kind(s) == "goal")


def raised_because(g: Graph, goal: str):
    """Why this subgoal was raised — an edge property of the *transition*, like `thread.why`, because it
    describes the raising rather than either goal. When methods land, the thing that must be pointed at
    is the method that produced the decomposition (a conflict detector will want to dispute one), and
    per `thread.py`'s rule — *ride on the edge what merely describes it; mint a node for what something
    else must point at* — that will be a node rather than this property."""
    return g.edge_prop(goal, "of", 0, "because")


def ancestry(g: Graph, goal: str) -> tuple:
    """This goal, then its parent, up to the outermost — the context a decision rule keys on.

    Why this exists rather than letting authors unroll context into position-specific rules: the
    ancestry *already entails* the context, so encoding it a second time in which rule you wrote is a
    labelling error, and it forces one rule per position a rule could occupy."""
    chain, at = [], goal
    while at is not None:
        chain.append(at)
        at = parent_of(g, at)
    return tuple(chain)


def within(g: Graph, goal: str, ancestor: str) -> bool:
    """Is `goal` this one or anything raised beneath it? The predicate behind *"if within subgoal y"*."""
    return ancestor in ancestry(g, goal)


def depth_of(g: Graph, goal: str) -> int:
    """How deep this goal sits. 0 for a goal raised under nothing. What a recursion bound reads."""
    return len(ancestry(g, goal)) - 1


def decomposed(g: Graph, goal: str) -> bool:
    """Has anything been raised under this goal at all?

    This exists because of a recorded trap, not for symmetry. An earlier note found that a
    parent's "all my children are done" guard was written as an *absence* (`no subgoal that is unmet`) and
    so was vacuously true before any subgoal had been minted — an undecomposed goal read as trivially
    achieved. Generalised there as: *don't trust an open-ended absence without an explicit closure fact.*
    `satisfied` already applies the same rule one level down, guarding `bool(cs)` so a goal with no
    constraints is not vacuously met."""
    return bool(subgoals(g, goal))


def then(g: Graph, first: str, next_: str) -> None:
    """`first` must be done before `next_` — the one sequencing edge.

    An earlier note claimed *"a procedure is this shape plus one sequencing edge"*, and
    probing it against this engine found the claim substantially holds: two ordered subgoals ran through the
    existing `carry_out` unchanged, in order, and reality came out right. What the probe found missing was
    not structure but drive — nothing walked the order — which is `driver.follow`."""
    g.link(first, "then", next_)


def sequence(g: Graph, goal: str) -> tuple:
    """This goal's subgoals in `then` order. Unordered subgoals come after, in mint order.

    Two orderings could disagree here — `then` and the reverse-index order of `subgoals` — which is the
    redundancy `thread.py` had to guard between its ordered `step` edge and its `prev` chain. It cannot
    disagree here for a different reason: `then` is *partial* and this treats it as the only authority,
    appending whatever it does not mention rather than interleaving two opinions."""
    kids = subgoals(g, goal)
    later = {t for k in kids for t in g.targets(k, "then")}
    chain, at = [], next((k for k in kids if k not in later), None)
    seen = set()
    while at is not None and at not in seen:
        seen.add(at)
        chain.append(at)
        at = g.target(at, "then")
    return tuple(chain) + tuple(k for k in kids if k not in seen)


def met_by(g: Graph, goal: str) -> str:
    """How this goal counts as met — `BY_CONSTRAINTS` unless declared otherwise."""
    return g.attr(goal, "met_by") or BY_CONSTRAINTS


def force_of(g: Graph, goal: str) -> str:
    """`ADVISORY` (a method — fall back to search) or `MANDATORY` (a procedure — refuse)."""
    return g.attr(goal, "force") or ADVISORY


def subgoals_met(g: Graph, goal: str, *, ctx: str | None = None, under: str | None = None) -> bool:
    """Are all the subgoals satisfied? False for an undecomposed goal, per `decomposed`'s trap.

    This is a reader, NOT the definition of the parent's satisfaction. `satisfied` remains a question
    about the parent's own constraints. Whether a parent counts as met when its children are is a *policy*
    that belongs to whatever raised them — a method may decompose into steps that jointly achieve it, or
    into checks that merely support it — and baking one reading in here would decide that for every future
    method at the moment it is least clear which is wanted."""
    kids = subgoals(g, goal)
    return bool(kids) and all(satisfied(g, k, ctx=ctx, under=under) for k in kids)


def _constrain(g: Graph, goal: str, sort: str, **attrs) -> str:
    c = g.mint("constraint", sort=sort, **attrs)
    g.link(goal, "requires", c)
    return c


def require_link(g: Graph, goal: str, subject: str, label: str, obj: str, *,
                 transitive: bool = False) -> str:
    """*`subject` must be `label` `obj`* — e.g. `a` on `b`.

    `transitive=True` asks for reach at any depth rather than adjacency: *the parcel is in the
    warehouse* is true when it sits in a box in the warehouse, which a direct-target test calls false.
    An earlier note measured this as the one genuine closed-class gap behind the word *where*, and
    `closed_class_rechallenged.md` reached the same single item from the other direction.

    It stays the link sort rather than becoming a new one, because that is what it is — the same
    subject, label and object, asked as reach instead of adjacency. A separate sort would have to be taught
    to every reader of a constraint (`query.refutes`, `conflict`, `driver.relevance`, `describe`) for no
    difference any of them care about except the one line in `holds`."""
    c = _constrain(g, goal, "link", label=label, transitive=bool(transitive) or None)
    g.link(c, "subject", subject)
    g.link(c, "object", obj)
    return c


def require_attr(g: Graph, goal: str, subject: str, key: str, value, op: str = "==") -> str:
    """*This slot must compare this way to this value.*

    `op` defaults to `==`, which is every existing caller and every existing meaning. The wider set
    (`!= < <= > >=`) used to exist only inside a `type` block — an accident of where the comparison
    code happened to live, not a decision, and `intake._shape` refused the others with a message pointing
    at `type`. *"the file is bigger than 1k"* is an ordinary thing to want of a goal.

    Widening the surface meant teaching the readers, which is why this was not a parser edit:
    `holds`, `conflict.unsatisfiable` and `query.refutes` all assumed equality. All three now go through
    `types.compare`, the one comparator, so `>=` cannot mean different things in a schema and in a goal."""
    from .types import VALUE_OPS
    if op not in VALUE_OPS:
        raise ValueError(f"a comparison is one of {VALUE_OPS}, not {op!r}")
    c = _constrain(g, goal, "attr", key=key, value=value, op=op)
    g.link(c, "subject", subject)
    return c


def require_type(g: Graph, goal: str, type_name: str, *, about: str | None = None) -> str:
    c = _constrain(g, goal, "type", type=type_name)
    if about is not None:
        g.link(c, "subject", about)
    return c


# --- constraints on the PLAN, not the world -----------------------------------------------------
#
# This is what having the plan *in the graph* buys. A plan is not a value a planner returned — it is
# frames and transformations, so "which actions may I use, and how many" is an ordinary question about
# ordinary data, asked with the same machinery as "what must be true at the end".
#
# The distinction that decides everything here is safety versus liveness.
#
# * Safety — "never unstack", "at most five steps". Violated by a prefix ⇒ violated by *every*
#   extension of it. So a breach is a proof that this branch is dead, and pruning is sound.
# * Liveness — "the plan must include a verification step". A prefix lacking it is not in violation,
#   it is merely unfinished. Checking it eagerly would prune every branch at step one.
#
# Getting this backwards fails in both directions: defer a safety constraint and the search burns itself
# out on branches that died at step one; prune on a liveness constraint and nothing survives at all. So
# the *sort* of a constraint determines *when* it is checked, and that is why they are distinguished here
# rather than left to the caller to remember.
PLAN_SORTS = frozenset({"never", "eventually", "at_most"})
SAFETY_SORTS = frozenset({"never", "at_most"})       # prunable: a breach cannot be repaired later


def forbid_action(g: Graph, goal: str, *, function: str | None = None,
                  on: str | None = None, reason: str | None = None) -> str:
    """*Never do this.* Either a function by name, a node that must not be touched, or both."""
    c = _constrain(g, goal, "never", function=function, reason=reason)
    if on is not None:
        g.link(c, "on", on)
    return c


def require_action(g: Graph, goal: str, *, function: str | None = None, on: str | None = None) -> str:
    """*The plan must include this.* Liveness — never prunes, checked only when the world is satisfied."""
    c = _constrain(g, goal, "eventually", function=function)
    if on is not None:
        g.link(c, "on", on)
    return c


def limit_steps(g: Graph, goal: str, n: int) -> str:
    """*At most `n` actions.* Safety, so it prunes — a plan cannot get shorter by continuing."""
    return _constrain(g, goal, "at_most", limit=n)


def _matches(g: Graph, c: str, step: tuple) -> bool:
    """Does one planned action match this constraint? `step` is `(function, {real argument nodes})`.

    An unspecified `function` or `on` means "any" — so `forbid_action(function="unstack")` bans the
    operator everywhere, and `forbid_action(on=c)` bans touching that block by any means."""
    name, args = step
    want_fn, want_on = g.attr(c, "function"), g.target(c, "on")
    if want_fn is not None and want_fn != name:
        return False
    if want_on is not None and want_on not in args:
        return False
    return want_fn is not None or want_on is not None


def prohibitions(g: Graph, goal: str) -> tuple:
    """Every `never` binding this goal — its own, and every ancestor's.

    A ban a child could sidestep is not a ban. `breached` used to read `constraints(g, goal)`, so a
    prohibition on "arrange the trip" said nothing to the search planning "book the hotel" underneath it —
    the parent constrains the plan and the child does the planning, and the constraint did not cross the
    boundary. Since a subgoal points at its parent, the fix is a walk that `ancestry` already provides.

    The three plan sorts do NOT cross a boundary alike, and treating them alike is the mistake this
    function exists to avoid (`docs/planning.md`:

    | sort | across the boundary | why |
    |---|---|---|
    | `never` | inherits unchanged, at any depth | a breach is a proof wherever it happens |
    | `eventually` | must not inherit | discharged by *some* step *somewhere* below, never by each child separately — inherited, every child would be separately required to paint |
    | `at_most` | not inherited, and deliberately not — see `budget_of` | |"""
    return tuple(c for anc in ancestry(g, goal)
                 for c in constraints(g, anc) if g.attr(c, "sort") == "never")


def budget_of(g: Graph, goal: str) -> tuple:
    """This goal's own `at_most` constraints. Ancestors' budgets are not included, and that is a
    refusal rather than an omission.

    A budget counts at the grain of the level that declared it — "at most 4 steps" on the vacation
    means four of *the vacation's* steps, where a subgoal counts as one. Inheriting it downward would apply
    a parent's count to a child's *actions*, so authoring a method that expands one step into five would
    silently break a limit that nothing about the goal had changed. And copying it to each child unchanged
    is worse than useless: three children would each be allowed to spend the whole budget.

    So a budget is consumed, not copied, and consuming it needs a level that knows how many of *its
    own* steps have been taken — which is the decomposition rung that has no state node yet
    (`docs/planning.md`,). Enforcing it at the wrong grain would be a wrong answer; not enforcing it
    across levels is a gap. A gap that is written down beats a wrong answer, so this is the gap."""
    return tuple(c for c in constraints(g, goal) if g.attr(c, "sort") == "at_most")


def breached(g: Graph, goal: str, trace: tuple) -> tuple:
    """Safety constraints this plan prefix has already violated — prunable, because it is a proof.

    Contrast with `driver.relevance`, which only ever *ranks*: relevance is a guess about what will help,
    so filtering on it could lose a solution (Sussman's anomaly needs a move that scores low). A safety
    breach is not a guess — no continuation of a plan that used a forbidden action makes it unused. Ranking
    a guess and pruning a proof are both correct, and confusing the two is how search goes wrong.

    Prohibitions are read from the whole ancestry and budgets only from this goal — see `prohibitions` and
    `budget_of` for why those two differ."""
    out = [c for c in prohibitions(g, goal) if any(_matches(g, c, s) for s in trace)]
    out += [c for c in budget_of(g, goal) if len(trace) > g.attr(c, "limit", 0)]
    return tuple(out)


def outstanding(g: Graph, goal: str, trace: tuple) -> tuple:
    """Liveness constraints this plan has not yet met. Empty is required *at the end*, never before."""
    return tuple(c for c in constraints(g, goal)
                 if g.attr(c, "sort") == "eventually" and not any(_matches(g, c, s) for s in trace))


def plan_constraints(g: Graph, goal: str) -> tuple:
    return tuple(c for c in constraints(g, goal) if g.attr(c, "sort") in PLAN_SORTS)


def world_constraints(g: Graph, goal: str) -> tuple:
    """The constraints about the state of the world — what `unmet` and `satisfied` ask about."""
    return tuple(c for c in constraints(g, goal) if g.attr(c, "sort") not in PLAN_SORTS)


def constraints(g: Graph, goal: str) -> tuple:
    return g.targets(goal, "requires")


# --- checking -----------------------------------------------------------------------------------
def _ensure_holds(g: Graph) -> None:
    """Make sure this graph has the surface `holds` and the comparator under it. Idempotent.

    Same argument and same shape as `access.bootstrap` and `workbench._ensure_step`: a name is only
    meaning if something answers it, so resolving it belongs at the call rather than being a
    precondition every caller keeps by hand."""
    from pathlib import Path
    from . import asm, function as fn
    here = Path(__file__).parent / "rules"
    if fn.find(g, "compare") is None:
        asm.load_file(g, here / "compare.mf")
    if fn.find(g, "holds") is None:
        asm.load_file(g, here / "holds.mf")


def holds(g: Graph, c: str, *, ctx: str | None = None, under: str | None = None) -> bool:
    """Does this one constraint hold in the world `ctx` describes? — **the implementation is
    `rules/holds.mf`**.

    A wrapper and nothing else. There is no argument to describe as a node and no answer to translate,
    which is what makes this the smallest of the three swaps: the whole difficulty was upstream, in the
    caller having a view to hand rather than a context.

    **The closure is gone, not replaced.** A rule written in the closed access vocabulary resolves
    through the ambient context, so `slot_of` inside a frame reads that frame's version without the
    program containing one word about frames. Every `view=` in `_python_holds` below is machinery for a
    problem the surface does not have — which is the mediation layer's whole claim, cashed on the
    predicate that most needed it.

    `_python_holds` is kept immediately below as the reference the surface is checked against, on every
    sort and in both worlds. That is the answer to two implementations of one thing: a check that
    compares them, not a deletion that leaves the surface unmeasured."""
    _ensure_holds(g)
    from . import function as fn
    return fn.invoke(g, "holds", {"c": c, "under": under}, retain=False, under=ctx)[1]["result"]


def _python_holds(g: Graph, c: str, *, view=None, under: str | None = None) -> bool:
    """The reference `holds`, kept to be compared against rather than to run.

    Read it beside `rules/holds.mf`: the differences are the argument for the mediation layer. Every
    `view(...)` here is a question the surface never asks, because the context answers it one level
    down, inside the vocabulary call."""
    view = view or _same
    sort = g.attr(c, "sort")
    subject = g.target(c, "subject")
    here = view(subject) if subject is not None else None
    if subject is not None and here is None:
        return False                       # not present in this world at all
    if sort == "link":
        obj = g.target(c, "object")
        there = view(obj)
        if there is None:
            return False
        if g.attr(c, "transitive"):
            # Reach, not adjacency — and it is the same question one hop further out, so it lives here
            # rather than in a sort of its own. `path.reaches` carries the cycle protection.
            from .path import reaches
            return reaches(g, here, g.attr(c, "label"), obj, view=_viewer(view))
        # **Compared through the view, on the target.** An edge names an identity, so inside a frame
        # `here`'s targets are the things themselves and `there` is this frame's version of the object —
        # different nodes for the same individual, and comparing them raw reads `b on c` as false one
        # step after it became true, which is how this was found. Putting both sides through the view is
        # the one comparison that is right in every world: in reality it is `obj in targets` unchanged,
        # because the view is the identity there.
        from .path import adjacent
        return there in adjacent(g, here, g.attr(c, "label"), view=_viewer(view))
    if sort == "known":
        # A knowledge claim rather than a world-state claim — an earlier note's third variant of
        # this same shape. It asks that the slot have been *looked at*, not that it hold any value.
        return g.attr(here, g.attr(c, "key")) is not UNKNOWN
    if sort == "attr":
        got = g.attr(here, g.attr(c, "key"))
        # An unknown slot does NOT satisfy a value constraint, and it does not *falsify* it either — see
        # `undetermined`. Here it is simply not satisfied, which keeps `holds` a predicate.
        # `types.compare` is total: comparing a string to a number is a failed constraint, never a
        # crash, which matters more here than in a schema because a goal is checked against a world that
        # is under no obligation to hold the type the author had in mind.
        from .types import compare
        return got is not UNKNOWN and compare(g.attr(c, "op") or "==", got, g.attr(c, "value"))
    if sort == "type":
        want = g.attr(c, "type")
        if here is not None:
            return is_a(g, here, want, view=_viewer(view))
        if under is None:
            return False
        return any(n for n in instances(g, want, under, view=_viewer(view))
                   if g.kind(n) != "type")
    return False


def witnesses(g: Graph, c: str, *, ctx: str | None = None, under: str | None = None) -> tuple:
    """which nodes have to change for this constraint to become true — in the same world `holds`
    looked at, so the two can never disagree about which world they mean.

    `unmet` says *which constraints* are still false, and that is what turned planning from
    generate-and-test into means–ends. A universal constraint reintroduces exactly the defect
    that removed: `d is a tidied_dir` can only answer yes/no, so `docs/limits.md` measured even a
    *singular* action that would close it at band 1 against band 4 for the equivalent singular constraint.
    This is the missing half, one level up: name the members that make it false.

    Returns nodes in the view's space (frame images when a view is given), because that is where the
    failure was determined. A caller comparing them against real individuals must come back through
    `workbench.original_of` — the round trip is explicit rather than assumed.

    A constraint that holds has no witnesses, and that is the vacuity guard rather than an
    optimisation: a reader that named nodes for a satisfied constraint would be describing the world, not
    the unfinished business.

    Some failures have no witness at all, and saying so is the honest answer. A missing wheel does
    not exist, so there is nothing to point at — see `types.offenders`. Those are the *existential* case
    and `driver.relevance` already serves them from the other side, by scoring an operator that mints."""
    if holds(g, c, ctx=ctx, under=under):
        return ()
    view = _world(g, ctx)
    subject = g.target(c, "subject")
    here = view(subject) if subject is not None else None
    sort = g.attr(c, "sort")
    if sort == "type":
        if here is None:
            return ()                      # existential: nothing exists yet to blame
        found = _offenders(g, here, g.attr(c, "type"), view=_viewer(view))
        return tuple(dict.fromkeys(n for hits in found.values() for n in hits))
    # For every other sort the subject IS the thing that must change, so one uniform question serves
    # them all and no consumer has to branch on sort to ask it.
    return () if here is None else (here,)


def unmet(g: Graph, goal: str, *, ctx: str | None = None, under: str | None = None) -> tuple:
    """The constraints that are still false — what the driver should be working on.

    This is what turns planning from generate-and-test into means–ends: a goal that can only say "no"
    leaves a searcher with nothing to aim at, while a goal that names its unfinished business lets one ask
    *which rules could make this particular thing true*."""
    return tuple(c for c in world_constraints(g, goal)
                 if not holds(g, c, ctx=ctx, under=under))


def require_known(g: Graph, goal: str, subject: str, key: str) -> str:
    """*This slot must have been looked at* — a knowledge claim, not a world-state one.

    An earlier note found that goal/subgoal is the shape everything reduces to, and that *"a
    question is this shape wanting a knowledge-claim instead of a world-state claim"*. This is that, and it
    is what an information-gathering subgoal closes: without it, sensing had nothing to aim at and no way
    to report having succeeded.

    The subject is an edge, not an attribute. Passing it as a keyword to `_constrain` made it a
    stored string, so `g.target(c, "subject")` was `None`, `holds` looked at nothing, and the constraint
    read as satisfied before anyone had looked — a knowledge goal that closes itself. Caught by
    `describe` rendering it as "something.colour", which is the round trip earning its keep.

    And it closed itself twice more, by two further routes. `repo.files known` was accepted,
    planned, and reported done with an empty plan, having never looked — because `holds` asks
    `g.attr(here, key) is not UNKNOWN`, and an absent slot is `None` rather than `UNKNOWN`. Neither route
    is a bug in `UNKNOWN`: absence-means-*lacks-it* is deliberate (`graph.UNKNOWN`), so the slot really was
    known. The mistake was admitting a relation, or a typo, into an attribute-shaped claim at all.
    Same shape as the `has 1 ^contains` bug `docs/authoring.md` records — a label read in a position where labels
    do not apply, silently. Found by an earlier probe on *"list all the files in the repo"*.

    So both refuse rather than being fixed. *"Which files are in the repo"* is a real thing to want and
    `known` is genuinely not it: an absent edge has nowhere to hang a marker, so
    there is nothing for a sensing action to close. A loud refusal names the gap; a vacuous truth hides it."""
    if _names_an_edge(g, subject, key):
        raise ValueError(
            f"`known` is a claim about an ATTRIBUTE SLOT, and {key!r} names an edge. An absent edge has no "
            f"slot to mark as unlooked-at, so this constraint would be satisfied before anyone had looked. "
            f"To demand that something be there, say `has …` in a `type` block; to ask what is there, use "
            f"a `what` / `where` question.")
    if not _addressable(g, subject, key):
        raise ValueError(
            f"nothing has an attribute slot called {key!r}, so `known` about it is satisfied by default and "
            f"nothing would ever be looked at. A slot is unknown only when something SAYS so "
            f"(`graph.UNKNOWN`), so declare it in a `type` block or have an operator mark it unknown.")
    c = _constrain(g, goal, "known", key=key)
    g.link(c, "subject", subject)
    return c


def _names_an_edge(g: Graph, subject: str, key: str) -> bool:
    """Does `key` denote a relation rather than an attribute slot?

    Two witnesses, and the second is the one that matters. An edge already there is decisive. But the
    interesting case is the one an author actually writes — *"go and find out what files are in there"* —
    where no such edge exists yet and only a declared type knows the label is structural. Checking the
    world alone would accept exactly the utterance this refusal exists for."""
    if g.targets(subject, key):
        return True
    from .types import schema_of
    return any(key in schema_of(g, g.attr(t, "name")) for t in g.of_kind("type"))


def _addressable(g: Graph, subject: str, key: str) -> bool:
    """Is there an attribute slot by this name at all?

    Without this, a mistyped key is a knowledge goal that closes itself — and this is the half that
    actually bit. `repo.files known` was accepted where the edge is labelled `file`, so `files` named
    nothing whatever; `holds` read the absent slot as *not UNKNOWN*, i.e. known, and the goal was met with
    an empty plan. Every typo behaves this way.

    The slot counts as addressable if the subject carries it (any value, `UNKNOWN` included — which is
    the case an operator marking ignorance creates) or if any declared type requires it. Both are the
    situations in which the claim could ever be false, so refusing everything else costs nothing real."""
    if key in g.attrs.get(subject, {}):
        return True
    from .types import attrs_of
    return any(key in attrs_of(g, g.attr(t, "name")) for t in g.of_kind("type"))


def undetermined(g: Graph, goal: str, *, ctx: str | None = None, under: str | None = None) -> tuple:
    """The unmet constraints that are unmet because we have not looked, not because they are false.

    This is the distinction the driver needs and could not make: `pursue` reported failure identically
    whether *no plan exists* or *no plan exists given what I know*, and only the second warrants going and
    finding out.'s insight one notch further on — a goal that names *which* constraints are false lets
    the driver ask what could close them; one that separates *false* from *unknown* lets it reach for a
    sensing action instead of a world-changing one.

    Attribute-shaped only, per `graph.UNKNOWN`: an absent edge has no slot to mark."""
    view = _world(g, ctx)
    out = []
    for c in unmet(g, goal, ctx=ctx, under=under):
        if g.attr(c, "sort") not in ("attr", "known"):
            continue
        subject = g.target(c, "subject")
        here = view(subject) if subject is not None else None
        if here is not None and g.attr(here, g.attr(c, "key")) is UNKNOWN:
            out.append(c)
    return tuple(out)


def blocked_on_ignorance(g: Graph, goal: str, *, ctx: str | None = None, under: str | None = None) -> bool:
    """Is every remaining unmet constraint waiting on something we have not looked at?

    The criterion for `SENSE` is that a plan bottoms out in ignorance, not that it touches it. A goal
    with one unknown slot and three genuinely false constraints still has world work to do; sensing on the
    strength of merely *touching* an unknown would make the system look in every box. And the vacuity guard
    is the same one `decomposed` needed: with nothing unmet at all this is not "blocked", it is done."""
    open_now = unmet(g, goal, ctx=ctx, under=under)
    return bool(open_now) and len(undetermined(g, goal, ctx=ctx, under=under)) == len(open_now)


def satisfied(g: Graph, goal: str, *, ctx: str | None = None, under: str | None = None) -> bool:
    """Whether this goal is met. Says nothing about constraints on the plan — those are asked of a trace
    (`breached`, `outstanding`), because they are properties of the route, not the destination.

    Two groundings, because a procedure is met differently from a plain goal. Probing
    An earlier note's claim surfaced this: an ordered procedure's parent has no world constraints of
    its own — *"do these steps, in this order"* is the whole of it — so a satisfaction test that only ever
    read constraints called a perfectly completed procedure unsatisfied. Under `BY_STEPS`, having followed
    the steps is being met.'s third variant, a goal wanting a *knowledge* claim, is the same move a
    third time and is not built.

    Both groundings keep the same vacuity guard, which is the point of writing them together:
    `bool(cs)` for constraints and `decomposed` for steps. An empty goal is not trivially met either way —
    that is an earlier note's *don't trust an open-ended absence without an explicit closure fact*,
    and it was already available to get wrong in two places here."""
    if met_by(g, goal) == BY_STEPS:
        return subgoals_met(g, goal, ctx=ctx, under=under)
    cs = world_constraints(g, goal)
    return bool(cs) and not unmet(g, goal, ctx=ctx, under=under)


def witness(g: Graph, goal: str, *, ctx: str | None = None, under: str | None = None):
    """A node that shows the goal met, for recording. The named subject if there is one, otherwise the
    instance that satisfied a subject-less type constraint."""
    view = _world(g, ctx)
    if not satisfied(g, goal, ctx=ctx, under=under):
        return None
    about = g.target(goal, "about")
    if about is not None:
        return view(about)
    for c in constraints(g, goal):
        subject = g.target(c, "subject")
        if subject is not None:
            return view(subject)
        if g.attr(c, "sort") == "type" and under is not None:
            found = [n for n in instances(g, g.attr(c, "type"), under) if g.kind(n) != "type"]
            if found:
                return found[0]
    return None


# --- recording ----------------------------------------------------------------------------------
def record_plan(g: Graph, goal: str, *, seen_in: str, witness=None) -> str:
    """A plan was found — the goal is met in imagination, which is not the world having changed.

    These were one method, and conflating them was a real defect: the driver closed a world goal the
    moment an imagined frame satisfied it, so a goal read as *met* while execution had diverged and nothing
    had happened. "I know how to do this" and "this is now true" are different claims and the record has to
    keep them apart, or every downstream reader inherits the confusion."""
    g.put(goal, planned=True)
    g.link(goal, "seen_in", seen_in)
    if witness is not None:
        g.link(goal, "planned_witness", witness)
    return goal


def is_planned(g: Graph, goal: str) -> bool:
    """A plan reaching this goal has been found. Says nothing about whether it was carried out."""
    return bool(g.attr(goal, "planned"))


def close_goal(g: Graph, goal: str, by, *, seen_in: str | None = None) -> str:
    """Record that this goal was met in reality. `seen_in` is for the imagined case only."""
    if by is not None:
        g.link(goal, "met_by", by)
    if seen_in is not None:
        g.link(goal, "seen_in", seen_in)
    g.put(goal, closed=True)
    return goal


def is_closed(g: Graph, goal: str) -> bool:
    """Whether meeting the goal was *recorded* — distinct from `satisfied`, which re-checks the structure."""
    return bool(g.attr(goal, "closed"))


def wanted(g: Graph, goal: str):
    """The type this goal wants, if it has a type constraint — what `plan.py` chains on."""
    for c in constraints(g, goal):
        if g.attr(c, "sort") == "type":
            return g.attr(c, "type")
    return None


def describe_constraint(g: Graph, c: str) -> str:
    sort, subject = g.attr(c, "sort"), g.target(c, "subject")
    who = (g.attr(subject, "label") or subject) if subject else "something"
    if sort in PLAN_SORTS:
        if sort == "at_most":
            return f"at most {g.attr(c, 'limit')} step(s)"
        on = g.target(c, "on")
        what = g.attr(c, "function") or "anything"
        where = f" on {g.attr(on, 'label') or on}" if on is not None else ""
        return ("never " if sort == "never" else "must ") + what + where
    if sort == "link":
        obj = g.target(c, "object")
        rel = g.attr(c, "label") + ("+" if g.attr(c, "transitive") else "")
        return f"{who} {rel} {g.attr(obj, 'label') or obj}"
    if sort == "known":
        return f"{who}.{g.attr(c, 'key')} must be known"
    if sort == "attr":
        # The operator is stored on the constraint and was being dropped here, so every comparison
        # rendered as `=`. It surfaces in `pursuit_report["why"]`, where "did not reach [desk.cash =
        # 300]" reads as *we needed exactly 300* — misreporting the goal in the one string a human is
        # most likely to read. Comparison operators in goals are newer than this renderer.
        #
        # Equality renders as `=`, not `==`: this is prose for a reader, and it is the surface the
        # author wrote (`desk.cash = 300`), not the stored operator.
        op = g.attr(c, "op") or "=="
        return f"{who}.{g.attr(c, 'key')} {'=' if op == '==' else op} {g.attr(c, 'value')!r}"
    return f"{who} is a {g.attr(c, 'type')}"


def describe(g: Graph, goal: str) -> str:
    want = ", ".join(describe_constraint(g, c) for c in constraints(g, goal))
    head = f"goal: {g.attr(goal, 'label')} [{want}]"
    if is_closed(g, goal):
        return head + " — MET"
    if is_planned(g, goal):
        return head + f" — PLANNED (in {g.target(goal, 'seen_in')})"
    return head


__all__ = ["PLAN_SORTS", "SAFETY_SORTS", "BY_CONSTRAINTS", "BY_STEPS", "MET_BY",
           "ADVISORY", "MANDATORY", "FORCES", "then", "sequence", "met_by", "force_of",
           "open_goal", "parent_of", "subgoals", "raised_because",
           "ancestry", "within", "depth_of", "decomposed", "subgoals_met",
           "require_link", "require_attr", "require_type", "require_known",
           "undetermined", "blocked_on_ignorance",
           "forbid_action", "require_action", "limit_steps", "constraints", "plan_constraints",
           "world_constraints", "breached", "prohibitions", "budget_of", "outstanding", "holds", "unmet", "witnesses", "satisfied", "witness",
           "record_plan", "is_planned", "close_goal", "is_closed", "wanted", "describe_constraint", "describe"]

"""GOAL — a desired state, specified as CONSTRAINTS that must hold.

`microfunctions/README.md` listed this under "not here yet": *a goal as a node driving planning, rather than
a caller passing a wanted type*. Everything before took `want` as a Python string, so the one thing the
system was *trying to do* was the one thing it could not point at, hypothesise about, or record having
pursued — the same defect attention had before `thread.py`, in a different place.

**A goal is a set of constraints, and each constraint is a node.** Three sorts, because three questions
genuinely differ:

* **link** — *`a` must be `on` `b`*. A specific edge between specific individuals.
* **attr** — *`b` must be `clear`*. A specific value on a specific node.
* **type** — *something must be a `three_high`*. A reusable schema (`types.py`), optionally about a named
  subject; without one it asks whether *anything* in the region qualifies.

**⚠ Why link-constraints cannot just be types.** A `types.py` schema says `{label: (target_kind, count)}` —
a kind and a count, never a *particular* target. That is not an oversight: a type mentioning specific nodes
would not be a schema, because a schema is reusable and individuals are not. So "a on b" has no home in the
type system and needs its own form. The two stay separate on purpose, and a goal can hold both.

**Satisfaction is checked, never asserted**, for the same reason a cast records nothing: the structure
either holds now or it does not. `is_closed` (we recorded meeting it) and `satisfied` (it holds) are
deliberately different questions, so a stale record can never be mistaken for a current fact.

**⭐ `unmet` is the point.** A goal that can only answer yes/no forces blind search. A goal that can say
*which constraints are still false* lets the driver work on what is actually missing — means–ends rather
than generate-and-test. That single method is the difference between the two.

**⚠ `view` is how one goal is asked of many worlds.** The same constraint is checked against reality and
against imagined states. Rather than teaching this module about workbenches — which would invert the
layering — the caller passes a `view`: a function mapping a node to the node that stands for it *here*.
Identity for reality, "this frame's image" for an imagined state. `goal.py` imports no workbench.

A goal is metadata: it points at the world and is never pointed at by it.
"""
from __future__ import annotations

from .graph import Graph
from .types import instances, is_a


def _same(node):
    """The default `view`: a node stands for itself. Reality needs no translation."""
    return node


# --- building -----------------------------------------------------------------------------------
def open_goal(g: Graph, want: str | None = None, *, about: str | None = None,
              label: str | None = None) -> str:
    """A goal. `want` is sugar for a single type constraint, which is the commonest shape."""
    goal = g.mint("goal", label=label or (f"make a {want}" if want else "goal"))
    if about is not None:
        g.link(goal, "about", about)
    if want is not None:
        require_type(g, goal, want, about=about)
    return goal


def _constrain(g: Graph, goal: str, sort: str, **attrs) -> str:
    c = g.mint("constraint", sort=sort, **attrs)
    g.link(goal, "requires", c)
    return c


def require_link(g: Graph, goal: str, subject: str, label: str, obj: str) -> str:
    """*`subject` must be `label` `obj`* — e.g. `a` on `b`."""
    c = _constrain(g, goal, "link", label=label)
    g.link(c, "subject", subject)
    g.link(c, "object", obj)
    return c


def require_attr(g: Graph, goal: str, subject: str, key: str, value) -> str:
    c = _constrain(g, goal, "attr", key=key, value=value)
    g.link(c, "subject", subject)
    return c


def require_type(g: Graph, goal: str, type_name: str, *, about: str | None = None) -> str:
    c = _constrain(g, goal, "type", type=type_name)
    if about is not None:
        g.link(c, "subject", about)
    return c


# --- constraints on the PLAN, not the world -----------------------------------------------------
#
# ⭐ This is what having the plan *in the graph* buys. A plan is not a value a planner returned — it is
# frames and transformations, so "which actions may I use, and how many" is an ordinary question about
# ordinary data, asked with the same machinery as "what must be true at the end".
#
# ⚠ **The distinction that decides everything here is safety versus liveness.**
#
# * **Safety** — "never unstack", "at most five steps". Violated by a prefix ⇒ violated by *every*
#   extension of it. So a breach is a **proof** that this branch is dead, and pruning is sound.
# * **Liveness** — "the plan must include a verification step". A prefix lacking it is not in violation,
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


def breached(g: Graph, goal: str, trace: tuple) -> tuple:
    """Safety constraints this plan prefix has already violated — **prunable, because it is a proof.**

    ⚠ Contrast with `driver.relevance`, which only ever *ranks*: relevance is a guess about what will help,
    so filtering on it could lose a solution (Sussman's anomaly needs a move that scores low). A safety
    breach is not a guess — no continuation of a plan that used a forbidden action makes it unused. Ranking
    a guess and pruning a proof are both correct, and confusing the two is how search goes wrong."""
    out = []
    for c in constraints(g, goal):
        sort = g.attr(c, "sort")
        if sort == "never" and any(_matches(g, c, s) for s in trace):
            out.append(c)
        elif sort == "at_most" and len(trace) > g.attr(c, "limit", 0):
            out.append(c)
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
def holds(g: Graph, c: str, *, view=None, under: str | None = None) -> bool:
    """Does this one constraint hold in the world `view` describes?"""
    view = view or _same
    sort = g.attr(c, "sort")
    subject = g.target(c, "subject")
    here = view(subject) if subject is not None else None
    if subject is not None and here is None:
        return False                       # not present in this world at all
    if sort == "link":
        there = view(g.target(c, "object"))
        return there is not None and there in g.targets(here, g.attr(c, "label"))
    if sort == "attr":
        return g.attr(here, g.attr(c, "key")) == g.attr(c, "value")
    if sort == "type":
        want = g.attr(c, "type")
        if here is not None:
            return is_a(g, here, want)
        if under is None:
            return False
        return any(n for n in instances(g, want, under) if g.kind(n) != "type")
    return False


def unmet(g: Graph, goal: str, *, view=None, under: str | None = None) -> tuple:
    """⭐ The constraints that are still false — what the driver should be working on.

    This is what turns planning from generate-and-test into means–ends: a goal that can only say "no"
    leaves a searcher with nothing to aim at, while a goal that names its unfinished business lets one ask
    *which rules could make this particular thing true*."""
    return tuple(c for c in world_constraints(g, goal)
                 if not holds(g, c, view=view, under=under))


def satisfied(g: Graph, goal: str, *, view=None, under: str | None = None) -> bool:
    """Whether the WORLD constraints hold. ⚠ Says nothing about constraints on the plan — those are asked
    of a trace (`breached`, `outstanding`), because they are properties of the route, not the destination."""
    cs = world_constraints(g, goal)
    return bool(cs) and not unmet(g, goal, view=view, under=under)


def witness(g: Graph, goal: str, *, view=None, under: str | None = None):
    """A node that shows the goal met, for recording. The named subject if there is one, otherwise the
    instance that satisfied a subject-less type constraint."""
    view = view or _same
    if not satisfied(g, goal, view=view, under=under):
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
    """⭐ A plan was found — the goal is met **in imagination**, which is not the world having changed.

    ⚠ These were one method, and conflating them was a real defect: the driver closed a world goal the
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
    """Record that this goal was met **in reality**. `seen_in` is for the imagined case only."""
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
        return f"{who} {g.attr(c, 'label')} {g.attr(obj, 'label') or obj}"
    if sort == "attr":
        return f"{who}.{g.attr(c, 'key')} = {g.attr(c, 'value')!r}"
    return f"{who} is a {g.attr(c, 'type')}"


def describe(g: Graph, goal: str) -> str:
    want = ", ".join(describe_constraint(g, c) for c in constraints(g, goal))
    head = f"goal: {g.attr(goal, 'label')} [{want}]"
    if is_closed(g, goal):
        return head + " — MET"
    if is_planned(g, goal):
        return head + f" — PLANNED (in {g.target(goal, 'seen_in')})"
    return head


__all__ = ["PLAN_SORTS", "SAFETY_SORTS", "open_goal", "require_link", "require_attr", "require_type",
           "forbid_action", "require_action", "limit_steps", "constraints", "plan_constraints",
           "world_constraints", "breached", "outstanding", "holds", "unmet", "satisfied", "witness",
           "record_plan", "is_planned", "close_goal", "is_closed", "wanted", "describe_constraint", "describe"]

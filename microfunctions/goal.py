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
    return tuple(c for c in constraints(g, goal) if not holds(g, c, view=view, under=under))


def satisfied(g: Graph, goal: str, *, view=None, under: str | None = None) -> bool:
    cs = constraints(g, goal)
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
def close_goal(g: Graph, goal: str, by, *, seen_in: str | None = None) -> str:
    """Record what closed this goal. `seen_in` names the region — an *imagined* state closing a goal about
    planning is not the world having changed, and conflating those would be a lie."""
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
    if sort == "link":
        obj = g.target(c, "object")
        return f"{who} {g.attr(c, 'label')} {g.attr(obj, 'label') or obj}"
    if sort == "attr":
        return f"{who}.{g.attr(c, 'key')} = {g.attr(c, 'value')!r}"
    return f"{who} is a {g.attr(c, 'type')}"


def describe(g: Graph, goal: str) -> str:
    want = ", ".join(describe_constraint(g, c) for c in constraints(g, goal))
    head = f"goal: {g.attr(goal, 'label')} [{want}]"
    if not is_closed(g, goal):
        return head
    seen = g.target(goal, "seen_in")
    return head + " — MET" + (f" in {seen}" if seen else "")


__all__ = ["open_goal", "require_link", "require_attr", "require_type", "constraints",
           "holds", "unmet", "satisfied", "witness", "close_goal", "is_closed", "wanted",
           "describe_constraint", "describe"]

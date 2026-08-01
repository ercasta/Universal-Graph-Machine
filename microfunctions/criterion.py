"""CRITERION — expert judgement as an ordered list, authored as text.

`expert_judgement.md`. The engine's own guidance (`driver.relevance`) is **domain-blind**: it scores a
proposal by whether it writes an open constraint, so a move that unblocks without closing anything scores
zero. A criterion is **authored knowledge** that names the move outright, and the measured difference is
not a constant factor — with criteria the search imagines **5 states whatever the size of the world**,
where `relevance` goes 139 → 357 and then stops finding a plan at all between six and seven blocks.

## What a criterion is

An ordered list. Each takes the **goal** and the **context** and returns either an action — a function
with its arguments, `driver.Call` — or nothing. **The first that speaks wins**, precedence being
declaration order, which is free because `of_kind` returns mint order. That is the same choice
`guideline.py` makes and for the same reason `deliberation.md` §5 gives: weights are the thing that needs
tuning, and there is nothing to tune in an order.

## ⭐⭐ Where the variables come from, which is the whole design

A criterion may not name individuals — one that said *"unstack c"* would be about `c` and could not be
reused. Its variables are bound by **matching an unmet constraint of the goal**:

    wants link on          →  binds `subject` and `object` from a goal constraint that is still false

This is `method.py`'s trick (`handles link on`, steps speaking of `subject`/`object`) in a second place,
and it is also **exactly the index key** `expert_judgement.md` §7 identified: goals have no schema, but
their constraints have a closed sort vocabulary (`link`/`attr`/`type`/`never`/`eventually`/`at_most`)
crossed with a label, and `driver.relevance` already computes it per proposal. The thing a criterion keys
on and the thing an index could key on are the same thing, which is why the vocabulary can stay indexable
without anyone having to arrange it.

## ⭐⭐ A set position with a selector — and NOT a loop

The one thing the probe measured as genuinely required is *"the **topmost** block above x"*: without it a
two-deep pile defeats the criteria. It was first built as a bounded `while`, and that was wrong —
`path.via` already walks a relation breadth-first, **nearest first**, so the topmost is simply *the last
one*. Written as a set-valued reader plus a selector it reproduces the hand-rolled loop **exactly**.

    furthest subject by ^on        the last of via(subject, "on", back=True)
    nearest  subject by ^on        the first

⚠ **This is strictly weaker than iteration, and that is why it is allowed.** The criteria list runs inside
the scheduler, where nothing can interrupt it, so an unbounded loop would be a scheduler that can hang with
no watcher above it. A selector over a materialised traversal is total by construction. `path.via` is
deliberately unreachable from the path grammar — a *reference* that denoted a set would break `node_at`'s
promise of one node — so this is a **surface form of its own**, allowed only where a set makes sense.

## ⚠ Silence is ordinary, and it is the safe answer

A criterion whose references do not resolve, or whose tests do not hold, says nothing — and `relevance`
then ranks as it always did. **The dangerous case is not a criterion that fires but one that fires on
partial knowledge**, so every test is written out as its own line and any one of them failing is enough to
stay quiet. That is also what makes *"why not X?"* answerable: `governing` reports which line stopped
which criterion, which an opaque predicate could never do.
"""
from __future__ import annotations

from . import goal as G
from . import path as P
from . import workbench as W
from .graph import Graph

#: The reference forms a criterion may use. `subject`/`object` are bound by `wants`.
SUBJECT, OBJECT = "subject", "object"
ROLES = (SUBJECT, OBJECT)

#: Selectors over a set-valued traversal. Nearest-first is `path.via`'s own order.
NEAREST, FURTHEST = "nearest", "furthest"
SELECTORS = (NEAREST, FURTHEST)


def criteria(g: Graph) -> tuple:
    """Every declared criterion, in **declaration order** — which is precedence order, free.

    Library-region data, like functions, types and guidelines: criteria describe how to act, not what is
    the case, so they do not hang off `root` and are never copied into a workbench."""
    return g.of_kind("criterion")


# --- authoring ----------------------------------------------------------------------------------------
def declare(g: Graph, label: str, *, because: str | None = None) -> str:
    c = g.mint("criterion", label=label)
    if because:
        g.put(c, because=because)
    return c


def wants(g: Graph, c: str, sort: str, label: str | None = None) -> str:
    """What the criterion keys on: an **unmet** constraint of the goal, which binds its variables.

    ⚠ Unmet, not merely present. A criterion is advice about what to do *next*, and a constraint that
    already holds has nothing to say about that — keying on it would make criteria fire forever on goals
    that were already partly done."""
    g.put(c, wants_sort=sort)
    if label is not None:
        g.put(c, wants_label=label)
    return c


def test(g: Graph, c: str, *, sort: str, negated: bool = False, **fields) -> str:
    """One condition, as its own node — so `governing` can say which one failed."""
    t = g.mint("test", sort=sort, negated=negated, **{k: v for k, v in fields.items() if v is not None})
    g.link(c, "test", t)
    return t


def does(g: Graph, c: str, function: str, bindings: dict) -> str:
    """The action this criterion names. `bindings` maps each parameter to a **reference**, as text."""
    d = g.mint("does", function=function)
    for param in sorted(bindings):
        a = g.mint("binds", param=param, ref=bindings[param])
        g.link(d, "arg", a)
    g.link(c, "does", d)
    return d


def action_of(g: Graph, c: str):
    return g.target(c, "does")


def tests_of(g: Graph, c: str) -> tuple:
    return g.targets(c, "test")


# --- references ---------------------------------------------------------------------------------------
class Unresolvable(Exception):
    """A reference that names nothing in this world. Ordinary — it makes a criterion silent, not loud."""


def _here(g: Graph, frame: str, real):
    """This frame's image of a real node. ⚠ `W.mapping_for` matches the IMMEDIATE original, which is not
    always the real node once frames nest, so fall back to `W.resolve`, which walks the whole chain."""
    if real is None:
        return None
    m = W.mapping_for(g, frame, real)
    if m is not None:
        return W.image_of(g, m)
    for m in W.mappings(g, frame):
        if W.resolve(g, m) == real:
            return W.image_of(g, m)
    return None


def resolve_ref(g: Graph, ref: str, bound: dict, frame: str, *, under: str = "root"):
    """A written reference → the **real** node it denotes in this frame. Raises `Unresolvable`.

    Four forms, and the vocabulary is closed:

    * `subject` / `object` — a role bound by `wants`
    * `<role>.<path>` — `path.py`, any depth, `^` for the backward hop
    * `<selector> <ref> by <link>` — a **set** walked transitively, and one element chosen
    * `the <name>` — a named individual, resolved the way every other block resolves one

    ⚠ Navigation happens on the frame's **image** and the answer is handed back as the **real** node,
    because a `Call`'s bindings name individuals. Those are different nodes, and `driver.stands_for`
    exists because they were once confused, silently, for a whole component."""
    words = ref.split()
    if len(words) == 4 and words[0] in SELECTORS and words[2] == "by":
        start = resolve_ref(g, words[1], bound, frame, under=under)
        label, back = (words[3][1:], True) if words[3].startswith("^") else (words[3], False)
        reached = P.via(g, _here(g, frame, start), label, back=back)
        if not reached:
            raise Unresolvable(f"nothing is reachable from {words[1]} by {words[3]}")
        # ⚠ `via` is breadth-first, so nearest-first. The furthest is the LAST, and that is the whole of
        # what the two-deep pile needed — no iteration, no fixed point.
        return W.original_of(g, reached[0 if words[0] == NEAREST else -1])
    if len(words) == 2 and words[0] == "the":
        from . import intake
        try:
            return intake.resolve(g, words[1], under=under)
        except intake.Unreadable as e:
            # ⚠ Authoring already refused an unresolvable name, so reaching here means the WORLD moved
            # — the individual is gone or has become ambiguous. That is a situation, not a typo, so the
            # criterion falls silent rather than bringing down a search.
            raise Unresolvable(str(e)) from None
    if len(words) != 1:
        raise Unresolvable(f"cannot read the reference {ref!r}")

    base, rest = P.split_base(words[0])
    if base not in bound:
        raise Unresolvable(f"{base!r} is not bound here; a criterion speaks of {' or '.join(ROLES)}")
    node = bound[base]
    if rest is None:
        return node
    reached = P.node_at(g, _here(g, frame, node), rest)
    if reached is None:
        raise Unresolvable(f"{ref!r} reaches nothing in this world")
    return W.original_of(g, reached)


# --- evaluation ---------------------------------------------------------------------------------------
def _holds(g: Graph, t: str, bound: dict, frame: str, under: str) -> bool:
    """Does this one test hold? An unresolvable reference is a test that does not hold, never a crash."""
    try:
        left = resolve_ref(g, g.attr(t, "left"), bound, frame, under=under)
    except (Unresolvable, P.BadPath):
        return False
    sort = g.attr(t, "sort")
    if sort == "exists":
        return left is not None
    if sort == "type":
        from .types import is_a
        return is_a(g, _here(g, frame, left), g.attr(t, "label"))
    if sort == "attr":
        return g.attr(_here(g, frame, left), g.attr(t, "key")) == g.attr(t, "value")
    if sort == "link":
        try:
            right = resolve_ref(g, g.attr(t, "right"), bound, frame, under=under)
        except (Unresolvable, P.BadPath):
            return False
        return g.target(_here(g, frame, left), g.attr(t, "label")) == _here(g, frame, right)
    if sort == "wants":
        # ⚠ A test about the GOAL, not the world — *"is anything still required of this thing?"*. The
        # bottom-up ordering knowledge needs it: stack onto `y` only once `y` itself has nowhere left to go.
        for c in _open_constraints(g, t, frame, bound):
            if g.attr(c, "sort") == g.attr(t, "want_sort") and \
                    (g.attr(t, "label") is None or g.attr(c, "label") == g.attr(t, "label")) and \
                    g.target(c, "subject") == left:
                return True
        return False
    raise ValueError(f"unknown test sort {sort!r}")


def _open_constraints(g: Graph, node: str, frame: str, bound: dict) -> tuple:
    return bound.get("__unmet__", ())


def _bindings_for(g: Graph, c: str, goal: str, frame: str, subject: str) -> tuple:
    """Every way this criterion's `wants` line matches, as `{role: real node}` — in constraint order."""
    from . import driver as D
    view = D.view_in(g, frame)
    under = W.image_of(g, W.mapping_for(g, frame, subject)) if W.mapping_for(g, frame, subject) else None
    unmet = G.unmet(g, goal, view=view, under=under)
    sort, label = g.attr(c, "wants_sort"), g.attr(c, "wants_label")
    out = []
    for k in unmet:
        if g.attr(k, "sort") != sort:
            continue
        if label is not None and (g.attr(k, "label") or g.attr(k, "key")) != label:
            continue
        bound = {SUBJECT: g.target(k, "subject"), "__unmet__": unmet, "__constraint__": k}
        if g.target(k, "object") is not None:
            bound[OBJECT] = g.target(k, "object")
        out.append(bound)
    return tuple(out)


def _try(g: Graph, c: str, bound: dict, frame: str, under: str) -> tuple:
    """One binding, tried: `(Call, ())` if this criterion speaks, `(None, reasons)` if it does not.

    **⭐ ONE place, because `speaks` and `governing` must never disagree.** They did: `governing` checked
    only the `test` lines while `speaks` also required the action's references to resolve — so on Sussman's
    root frame it reported all three criteria as having spoken when only one could. Two paths computing
    *"the same"* thing differently is the defect shape this codebase keeps recording, and landing it in the
    one feature whose entire job is to explain truthfully is the worst possible place for it.

    ⚠ **An action's arguments are part of its condition**, and that is a deliberate reading rather than an
    implementation accident. *"Take the topmost block off the pile above x"* simply does not apply when
    there is no pile; requiring the author to write a separate `when` line for it would make silence
    depend on remembering to guard, and a forgotten guard would become a crash mid-search."""
    from .driver import Call
    reasons = [describe_test(g, t) for t in tests_of(g, c)
               if _holds(g, t, bound, frame, under) == bool(g.attr(t, "negated"))]
    if reasons:
        return None, tuple(reasons)
    act = action_of(g, c)
    args = {}
    for a in g.targets(act, "arg"):
        ref = g.attr(a, "ref")
        try:
            got = resolve_ref(g, ref, bound, frame, under=under)
        except (Unresolvable, P.BadPath) as e:
            return None, (f"{ref} — {e}",)
        if got is None:
            return None, (f"{ref} reaches nothing",)
        args[g.attr(a, "param")] = got
    return Call(g.attr(act, "function"), args,
                why=g.attr(c, "label") + (f" — {g.attr(c, 'because')}"
                                          if g.attr(c, "because") else "")), ()


def speaks(g: Graph, c: str, goal: str, frame: str, subject: str, *, under: str = "root"):
    """Does this criterion have something to say here? Returns `driver.Call`, or `None`.

    ⚠ Every failure is silence. A reference that resolves to nothing, a test that does not hold, an action
    whose arguments cannot be found — each means *this criterion has nothing to say about this situation*,
    which is an ordinary answer and the one that keeps `relevance` in charge by default."""
    if action_of(g, c) is None:
        return None
    for bound in _bindings_for(g, c, goal, frame, subject):
        call, _why = _try(g, c, bound, frame, under)
        if call is not None:
            return call
    return None


def decide(g: Graph, goal: str, subject: str, *, under: str = "root"):
    """The `propose=` / `decide=` hook that reads the authored list. **First match wins.**

    ⭐ Drops into `driver.pursue(propose=...)`, which is the seam where it pays: measured, asking the same
    knowledge *before* enumeration rather than after is 6.6× faster at sixty blocks, because `_offer`
    otherwise builds the whole O(N²) product and then throws it away."""
    def propose(situation):
        for c in criteria(g):
            got = speaks(g, c, goal, situation["frame"], subject, under=under)
            if got is not None:
                return got
        return None
    return propose


# --- why, and why not ---------------------------------------------------------------------------------
def governing(g: Graph, goal: str, frame: str, subject: str, *, under: str = "root") -> tuple:
    """`(criterion, spoke, reasons)` for every criterion — the reader's *"why this, and why not that?"*.

    **⭐ Load-bearing rather than a nicety, because criteria PRUNE.** Under ranking the alternatives are
    still on the frontier and can be looked at; when a criterion suppresses enumeration they were never
    built, so this is the only window onto what was discarded. Without it the first wrong criterion
    produces *"no plan found"* with nothing behind it.

    ⚠ This is why a condition is a **pattern and not a program**: each test is its own node, so the answer
    can name the line that failed. A criterion body that was an opaque predicate could only ever say *no*."""
    out = []
    for c in criteria(g):
        matches = _bindings_for(g, c, goal, frame, subject)
        if not matches:
            out.append((c, False, (f"nothing unmet matches `wants {g.attr(c, 'wants_sort')} "
                                   f"{g.attr(c, 'wants_label') or ''}`".rstrip(),)))
            continue
        failed, spoke = [], False
        for bound in matches:
            call, why = _try(g, c, bound, frame, under)
            if call is not None:
                spoke, failed = True, []
                break
            failed.extend(why)
        out.append((c, spoke, () if spoke else tuple(dict.fromkeys(failed))))
    return tuple(out)


def describe_test(g: Graph, t: str) -> str:
    sort, left = g.attr(t, "sort"), g.attr(t, "left")
    body = {"exists": f"{left} exists",
            "type": f"{left} is a {g.attr(t, 'label')}",
            "attr": f"{left}.{g.attr(t, 'key')} = {g.attr(t, 'value')!r}",
            "link": f"{left} {g.attr(t, 'label')} {g.attr(t, 'right')}",
            "wants": f"the goal wants {g.attr(t, 'want_sort')} "
                     f"{g.attr(t, 'label') or ''} from {left}".replace("  ", " ")}[sort]
    return ("not " if g.attr(t, "negated") else "") + body


def describe(g: Graph, c: str) -> str:
    act = action_of(g, c)
    doing = "nothing"
    if act is not None:
        args = ", ".join(f"{g.attr(a, 'param')}={g.attr(a, 'ref')}" for a in g.targets(act, "arg"))
        doing = f"{g.attr(act, 'function')}({args})"
    lines = [f"criterion {g.attr(c, 'label')!r}: when the goal wants "
             f"{g.attr(c, 'wants_sort')} {g.attr(c, 'wants_label') or ''}".rstrip() + f", do {doing}"]
    lines += [f"    {describe_test(g, t)}" for t in tests_of(g, c)]
    return "\n".join(lines)


__all__ = ["SUBJECT", "OBJECT", "ROLES", "NEAREST", "FURTHEST", "SELECTORS", "Unresolvable",
           "criteria", "declare", "wants", "test", "does", "action_of", "tests_of",
           "resolve_ref", "speaks", "decide", "governing", "describe_test", "describe"]

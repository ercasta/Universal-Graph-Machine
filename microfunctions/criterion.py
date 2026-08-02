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
    the case, so they do not hang off `root` and are never copied into a workbench.

    ⚠ Withdrawn criteria are skipped — *"ignore that"* has to reach the thing that enumerates, or the block
    keeps deciding after it was taken back (`discourse.py`)."""
    from .discourse import live
    return live(g, g.of_kind("criterion"))


# --- authoring ----------------------------------------------------------------------------------------
def declare(g: Graph, label: str, *, because: str | None = None, force: str = G.ADVISORY) -> str:
    """A criterion. `force` is `ADVISORY` (a `criterion`) or `MANDATORY` (a `directive`).

    ⭐⭐ **Force is about FAILURE, not strength** — `deliberation.md` §3, in a third place. An advisory
    criterion that turns out wrong costs imagined states, because the enumeration it suppressed was only
    **deferred**. A directive that turns out wrong makes the goal **unreachable**, because it says the
    alternatives are not worth building — and when it recognises a situation it cannot act in, it
    **refuses** rather than quietly letting the search improvise.

    ⚠ That is exactly what §2 said only a claim about the SITUATION is entitled to: *"in this situation,
    this is the move"*, not *"this move looks good here"*. The surface makes the author say which word,
    the way `method`/`procedure` already does, because force cannot be inferred from content."""
    c = g.mint("criterion", label=label, force=force)
    if because:
        g.put(c, because=because)
    return c


def force_of(g: Graph, c: str) -> str:
    return g.attr(c, "force", G.ADVISORY)


def is_mandatory(g: Graph, c: str) -> bool:
    return force_of(g, c) == G.MANDATORY


def wants(g: Graph, c: str, sort: str, label: str | None = None) -> str:
    """What the criterion keys on: an **unmet** constraint of the goal, which binds its variables.

    ⚠ Unmet, not merely present. A criterion is advice about what to do *next*, and a constraint that
    already holds has nothing to say about that — keying on it would make criteria fire forever on goals
    that were already partly done."""
    g.put(c, wants_sort=sort)
    if label is not None:
        g.put(c, wants_label=label)
    return c


def draw(g: Graph, c: str, name: str, ref: str, label: str, *, back: bool = False) -> str:
    """`some <name> in <ref> by <link>` — bind a **further** role by walking a relation.

    **⭐⭐ This is the answer to the one thing a second domain proved unsayable** (`expert_judgement.md`
    §8f): a criterion could *reach* a third individual by a path but could not **choose** among several,
    because `nearest`/`furthest … by <link>` selects over a **traversal** and nothing selected by a
    **condition**. A draw introduces the candidate as an ordinary role, so the filter is written as
    ordinary `when` / `unless` lines — which keeps it **decomposable**, and therefore keeps `governing`
    able to say which line ruled a candidate out. An inline `such that …` would have made the condition
    opaque again, which is the whole thing §5 says not to do.

    ⭐ **It also subsumes the selector, and says more.** `furthest subject by ^on` picks the top of a pile
    because of *where it sits*; `some b in subject by ^on` + `when b is a clear_block` picks it because of
    *what is true of it* — the same block, for a stated reason.

    ⚠ **Transitive, like `path.via` and like the goal's own `contains+`.** Candidates come back
    nearest-first, and `speaks` tries them in that order, so a criterion that could apply to several says
    the nearest thing first. Termination is `via`'s: a finite, already-materialised traversal."""
    d = g.mint("draw", name=name, ref=ref, label=label, back=back)
    g.link(c, "draw", d)
    return d


def draws_of(g: Graph, c: str) -> tuple:
    return g.targets(c, "draw")


def names_of(g: Graph, c: str) -> tuple:
    """Every role a criterion may speak of: the two `wants` binds, plus whatever it has drawn **so far**.

    ⚠ *So far* is what makes the surface enforce declaration before use, free — `intake` reads lines in
    order, so a `when` mentioning an undrawn name simply does not find it."""
    return ROLES + tuple(g.attr(d, "name") for d in draws_of(g, c))


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
        raise Unresolvable(f"{base!r} is not bound here; a criterion speaks of {' or '.join(ROLES)} "
                           f"and whatever it has drawn with `some`")
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
        here, there = _here(g, frame, left), _here(g, frame, right)
        if g.attr(t, "transitive"):
            # ⭐ `x contains+ y` — *reachable at any depth*. This arrived with the shared proposition
            # grammar: `+` had existed only in a goal line, though `cnl.md` §8 says it belongs "in a link
            # position — a goal line or a query", and a condition IS the query. ⚠⚠ The parser accepting it
            # while this read one direct edge would have been silent acceptance of a wrong meaning, which
            # is the failure mode this codebase keeps catching — so the evaluator moved with the surface.
            # Same reader `goal.holds` uses, so the two cannot disagree about what `+` means.
            from .path import reaches
            return reaches(g, here, g.attr(t, "label"), there)
        return g.target(here, g.attr(t, "label")) == there
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


#: Which field carries a constraint's label, per sort. ⚠ **Three different names for one idea**, and a
#: criterion keying on `type` silently matched NOTHING until a second domain was tried: `goal.require_type`
#: stores `type`, a link stores `label`, an attribute stores `key`. `relevance` reads the same three by
#: hand. This is the one place that has to know, and the fact that it is a table rather than an expression
#: is the honest record of a substrate irregularity nobody has collapsed.
_LABEL_FIELD = {"link": "label", "attr": "key", "type": "type"}


def constraint_label(g: Graph, c: str):
    """What a criterion's `wants <sort> <label>` line has to match against."""
    return g.attr(c, _LABEL_FIELD.get(g.attr(c, "sort"), "label"))


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
        if label is not None and constraint_label(g, k) != label:
            continue
        bound = {SUBJECT: g.target(k, "subject"), "__unmet__": unmet, "__constraint__": k,
                 "__goal__": goal}
        if g.target(k, "object") is not None:
            bound[OBJECT] = g.target(k, "object")
        out.append(bound)
    return _expand(g, tuple(out), draws_of(g, c), frame, "root")


def _expand(g: Graph, bounds: tuple, draws: tuple, frame: str, under: str) -> tuple:
    """Every combination of drawn candidates, nearest-first, in declaration order.

    ⚠ A draw that reaches nothing **removes** its binding rather than passing it through empty-handed:
    *"some container inside the warehouse"* when there is none is a situation the criterion has nothing to
    say about, not a criterion with a hole in it.

    ⚠ Nested draws multiply, which is the one place a criterion's cost is not bounded by the goal. It is
    still bounded — by the traversal, which is finite and already materialised — but an author writing
    three draws over a large relation should expect to pay for it. Nothing here is memoised because
    nothing has yet measured it as worth memoising."""
    for d in draws:
        name, label, back = g.attr(d, "name"), g.attr(d, "label"), bool(g.attr(d, "back"))
        nxt = []
        for b in bounds:
            try:
                start = resolve_ref(g, g.attr(d, "ref"), b, frame, under=under)
            except (Unresolvable, P.BadPath):
                continue
            for n in P.via(g, _here(g, frame, start), label, back=back):
                real = W.original_of(g, n)
                if real is None:
                    continue
                nxt.append({**b, name: real})
        bounds = tuple(nxt)
    return bounds


def _try(g: Graph, c: str, bound: dict, frame: str, under: str) -> tuple:
    """One binding, tried: `(Call, reasons, recognised)`.

    `recognised` is True once every `when`/`unless` line has held — i.e. the criterion **recognises this
    situation** — whether or not its action turns out to apply. That distinction is what force needs: a
    directive refuses when it recognises a situation it cannot act in, and stays silent when it does not
    recognise the situation at all. Conflating them would make a directive refuse everywhere it merely had
    nothing to say.

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
        return None, tuple(reasons), False
    # From here the criterion RECOGNISES the situation; anything that fails now is the action, not the
    # condition. ⭐ That line is what force needs: a directive refuses when it recognises a situation it
    # cannot act in, and stays silent when it does not recognise the situation at all. Conflating the two
    # would make a directive refuse everywhere it simply had nothing to say.
    act = action_of(g, c)
    args = {}
    for a in g.targets(act, "arg"):
        ref = g.attr(a, "ref")
        try:
            got = resolve_ref(g, ref, bound, frame, under=under)
        except (Unresolvable, P.BadPath) as e:
            return None, (f"{ref} — {e}",), True
        if got is None:
            return None, (f"{ref} reaches nothing",), True
        args[g.attr(a, "param")] = got
    call = Call(g.attr(act, "function"), args,
                why=g.attr(c, "label") + (f" — {g.attr(c, 'because')}"
                                          if g.attr(c, "because") else ""))

    # ⚠⚠ **A criterion whose action does not apply here is SILENT, not loud — and the second domain is
    # what settled that.** `driver.check_call` raises, which is right for a *Python* decider: one that
    # names an ill-typed or forbidden call is a bug in the caller. A criterion is different. It is general
    # knowledge meeting a particular world, so *"the first container happens to be the one this goal
    # forbids"* is a **situation**, not a mistake — and raising there abandoned a search that plain
    # enumeration could finish. Measured in the warehouse with two containers.
    #
    # ⭐ Silent, but never silently: the reason is handed back, so `governing` can say *"this criterion
    # would have said put_in(crate), and the goal forbids it"*. Silence that cannot be interrogated is the
    # thing §6 exists to prevent.
    from .driver import Undecidable, check_call
    try:
        check_call(g, bound["__goal__"], frame, call, bound.get("__prefix__"))
    except Undecidable as e:
        return None, (str(e),), True
    return call, (), True


def speaks(g: Graph, c: str, goal: str, frame: str, subject: str, *, under: str = "root",
           prefix=None):
    """Does this criterion have something to say here? Returns `(Call | None, blocked)`.

    `blocked` is non-empty when the criterion **recognised** the situation and still could not act — which
    only a directive treats as a refusal; for a criterion it is ordinary silence with a reason attached.

    ⚠ Every failure is silence. A reference that resolves to nothing, a test that does not hold, an action
    whose arguments cannot be found — each means *this criterion has nothing to say about this situation*,
    which is an ordinary answer and the one that keeps `relevance` in charge by default."""
    if action_of(g, c) is None:
        return None, ()
    blocked = []
    for bound in _bindings_for(g, c, goal, frame, subject):
        bound["__prefix__"] = prefix
        call, why, recognised = _try(g, c, bound, frame, under)
        if call is not None:
            return call._replace(final=is_mandatory(g, c)), ()
        if recognised:
            blocked.extend(why)
    return None, tuple(dict.fromkeys(blocked))


def decide(g: Graph, goal: str, subject: str, *, under: str = "root"):
    """The `propose=` / `decide=` hook that reads the authored list. **First match wins.**

    ⭐ Drops into `driver.pursue(propose=...)`, which is the seam where it pays: measured, asking the same
    knowledge *before* enumeration rather than after is 6.6× faster at sixty blocks, because `_offer`
    otherwise builds the whole O(N²) product and then throws it away."""
    def propose(situation):
        for c in criteria(g):
            got, blocked = speaks(g, c, goal, situation["frame"], subject, under=under,
                                  prefix=situation.get("prefix"))
            if got is not None:
                return got
            # ⭐⭐ A DIRECTIVE THAT RECOGNISES A SITUATION IT CANNOT ACT IN **REFUSES**, and this is the
            # whole of what mandatory force buys. Letting it fall through to the next criterion — or to
            # enumeration — is precisely the improvising a procedure exists to forbid, and it would make
            # `directive` indistinguishable from `criterion` except when everything already worked.
            if blocked and is_mandatory(g, c):
                from .driver import REFUSE
                return REFUSE, (f"{g.attr(c, 'label')!r} governs here and cannot be followed: "
                                + "; ".join(blocked))
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
            call, why, _recognised = _try(g, c, bound, frame, under)
            if call is not None:
                spoke, failed = True, []
                break
            failed.extend(why)
        out.append((c, spoke, () if spoke else tuple(dict.fromkeys(failed))))
    return tuple(out)


def proposals_here(g: Graph, goal: str, frame: str, subject: str, *, under: str = "root",
                   prefix=None) -> tuple:
    """`(criterion, Call)` for **every** criterion that would speak here — not just the winner.

    ⭐ The list `decide` throws away. First-match-wins is the whole control rule, so everything after the
    first is invisible at run time; this is what makes it visible to a reader."""
    out = []
    for c in criteria(g):
        got, _blocked = speaks(g, c, goal, frame, subject, under=under, prefix=prefix)
        if got is not None:
            out.append((c, got))
    return tuple(out)


def disagreements(g: Graph, goal: str, frame: str, subject: str, *, under: str = "root",
                  prefix=None) -> tuple:
    """Criteria that would act **differently** from the one that wins here.

    Returns `(winner, winning_call, loser, losing_call)` per disagreement, in precedence order.

    **⭐ This is `expert_judgement.md` §5's last untested claim, made good.** §10 of `deliberation.md`
    rejected program-conditions partly because *"`conflict.py` cannot say two rules disagree by comparing
    two programs"*, and §5 answered that the cost **degrades rather than dies**, because a criterion's
    **return** is a named function with denoted arguments — trivially comparable — even when its condition
    is not. That was an argument. This is the thing itself, and it is cheap: `speaks` already answers per
    criterion, so the comparison is a pass over answers rather than over conditions.

    **⚠ Naming the SAME call is redundancy, not disagreement.** `conflict.py`'s standing correction applies
    here unchanged: *a later action overriding an earlier one is not a disagreement, it is what doing
    things looks like.* Two criteria that agree are simply two ways of saying one thing, and reporting them
    would bury the real cases.

    ⚠ **This is EXACT and situational — it needs a frame, and it reports no false positives.** A static
    comparison of two criteria's conditions could only over-report, and `conflict.py`'s stance is that an
    honest miss beats a false alarm because *a conflict report nobody trusts is worse than no report at
    all*. So this answers *"here, now, who else wanted something different"* and never *"could these two
    ever clash"*."""
    spoke = proposals_here(g, goal, frame, subject, under=under, prefix=prefix)
    if not spoke:
        return ()
    winner, winning = spoke[0]
    return tuple((winner, winning, loser, losing) for loser, losing in spoke[1:]
                 if (losing.function, losing.bindings) != (winning.function, winning.bindings))


def describe_disagreements(g: Graph, goal: str, frame: str, subject: str, **kw) -> str:
    found = disagreements(g, goal, frame, subject, **kw)
    if not found:
        return "no criterion here wanted anything different"
    lines = [f"{len(found)} disagreement(s):"]
    for winner, winning, loser, losing in found:
        lines.append(f"  {g.attr(winner, 'label')!r} does {_call_text(g, winning)}, "
                     f"but {g.attr(loser, 'label')!r} would have done {_call_text(g, losing)}")
    return "\n".join(lines)


def _call_text(g: Graph, call) -> str:
    args = ", ".join(f"{p}={g.attr(n, 'label') or n}" for p, n in sorted(call.bindings.items()))
    return f"{call.function}({args})"


def describe_test(g: Graph, t: str) -> str:
    sort, left = g.attr(t, "sort"), g.attr(t, "left")
    body = {"exists": f"{left} exists",
            "type": f"{left} is a {g.attr(t, 'label')}",
            "attr": f"{left}.{g.attr(t, 'key')} = {g.attr(t, 'value')!r}",
            # ⚠ The `+` must survive the round trip, or a reader is shown a condition that says something
            # narrower than the one being evaluated.
            "link": f"{left} {g.attr(t, 'label')}{'+' if g.attr(t, 'transitive') else ''} "
                    f"{g.attr(t, 'right')}",
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
           "draw", "draws_of", "names_of", "constraint_label",
           "resolve_ref", "speaks", "decide", "governing", "force_of", "is_mandatory", "proposals_here", "disagreements",
           "describe_disagreements", "describe_test", "describe"]

"""Criterion — expert judgement as an ordered list, authored as text.

The engine's own guidance is domain-blind: `driver.relevance` scores a proposal by whether it
writes an open constraint, so a move that unblocks without closing anything scores zero. A
criterion is authored knowledge that names the move outright, and the difference is not a
constant factor: with criteria the search imagines five states whatever the size of the world,
where relevance alone goes from 139 states to 357 and then stops finding a plan at all between
six and seven blocks.

A criterion is an ordered list. Each takes the goal and the context and returns either an action
— a function with its arguments, `driver.Call` — or nothing. The first that speaks wins,
precedence being declaration order, which is free because mint order is preserved. Weights are
the thing that would need tuning, and there is nothing to tune in an order.

Where the variables come from is the whole design. A criterion may not name individuals; one that
said "unstack c" would be about `c` and could not be reused. Its variables are bound by matching
an unmet constraint of the goal:

    wants link on          binds `subject` and `object` from a goal constraint that is still false

That is also exactly what an index would key on: goals have no schema, but their constraints have
a closed sort vocabulary crossed with a label, and `driver.relevance` already computes it per
proposal.

A set position with a selector, and deliberately not a loop. The genuinely required case is "the
topmost block above x", without which a two-deep pile defeats the criteria. `path.via` already
walks a relation breadth-first, nearest first, so the topmost is simply the last one:

    furthest subject by ^on        the last of via(subject, "on", back=True)
    nearest  subject by ^on        the first

This is strictly weaker than iteration, and that is why it is allowed. The criteria list runs
inside the scheduler, where nothing can interrupt it, so an unbounded loop would be a scheduler
that can hang with no watcher above it. A selector over a materialised traversal is total by
construction. `path.via` is deliberately unreachable from the path grammar, since a reference
denoting a set would break the promise of one node, so this is a surface form of its own allowed
only where a set makes sense.

Silence is ordinary and it is the safe answer. A criterion whose references do not resolve, or
whose tests do not hold, says nothing, and relevance then ranks as it always did. The dangerous
case is not a criterion that fires but one that fires on partial knowledge, so every test is
written out as its own line and any one of them failing is enough to stay quiet. That is also
what makes "why not X?" answerable: `governing` reports which line stopped which criterion, which
an opaque predicate could never do.

See `docs/deliberation.md`.
"""
from __future__ import annotations

from . import consequent as CQ
from . import goal as G
from . import path as P
from . import precedence as PR
from . import workbench as W
from .graph import Graph

#: The reference forms a criterion may use. `subject`/`object` are bound by `wants`.
SUBJECT, OBJECT = "subject", "object"
ROLES = (SUBJECT, OBJECT)

#: Selectors over a set-valued traversal. Nearest-first is `path.via`'s own order.
NEAREST, FURTHEST = "nearest", "furthest"
SELECTORS = (NEAREST, FURTHEST)


def criteria(g: Graph) -> tuple:
    """Every declared criterion, in precedence order.

    Library-region data, like functions, types and guidelines: criteria describe how to act, not what is
    the case, so they do not hang off `root` and are never copied into a workbench.

    Withdrawn criteria are skipped — *"ignore that"* has to reach the thing that enumerates, or the block
    keeps deciding after it was taken back (`discourse.py`).

    The one place precedence enters. `decide`, `governing`, `proposals_here` and `disagreements` all
    read this list and all take the order on trust, so ranking anywhere else would be four places
    agreeing by hand — the drift class this codebase keeps re-finding. Order is declaration order until a
    tie-break rule is authored (`precedence.py`), so installing the module changes nothing until somebody
    says how to rank."""
    from .discourse import live
    from . import precedence as PR
    return PR.rank(g, live(g, g.of_kind("criterion")))


# --- authoring ----------------------------------------------------------------------------------------
def declare(g: Graph, label: str, *, because: str | None = None,
            strength: str = PR.SHOULD, by=None) -> str:
    """A criterion. `strength` is `must`, `should` or `could`; `by` is who says so.

    **Strength carries two axes that used to be one, and only `must` touches the older one.** Force is
    about failure — `docs/deliberation.md`, in a third place. An advisory criterion that turns out wrong
    costs imagined states, because the enumeration it suppressed was only deferred. A `must` that turns
    out wrong makes the goal unreachable, because it says the alternatives are not worth building, and
    when it recognises a situation it cannot act in it refuses rather than letting the search improvise.

    `should` and `could` are both advisory and differ only in precedence. That is the honest reading of
    the three words: two of them are claims about *how strongly this competes*, and one is additionally a
    claim about *what happens when it cannot be followed*. Collapsing them would have made `could` refuse,
    which no author saying "could" means.

    The surface makes the author say which word, the way `method`/`procedure` already does, because
    neither force nor strength can be inferred from content.

    `by` defaults to `experience` rather than to nothing — see `precedence.source_of`. A criterion
    nobody vouches for is still attributable, and *"experience says"* is the true attribution for one
    that was learned."""
    if strength not in PR.STRENGTHS:
        raise ValueError(f"strength must be one of {PR.STRENGTHS}, not {strength!r}")
    c = g.mint("criterion", label=label, strength=strength,
               force=G.MANDATORY if strength == PR.MUST else G.ADVISORY)
    if because:
        g.put(c, because=because)
    PR.attribute(g, c, by)
    return c


def force_of(g: Graph, c: str) -> str:
    """The failure axis: `MANDATORY` for a `must`, `ADVISORY` otherwise. Derived, never authored twice."""
    return g.attr(c, "force", G.ADVISORY)


def strength_of(g: Graph, c: str) -> str:
    """The precedence axis: `must`, `should` or `could`."""
    return PR.strength_of(g, c)


def source_of(g: Graph, c: str) -> str:
    """Who says so. Never `None` — an unattributed criterion is `experience`."""
    return PR.source_of(g, c)


def is_mandatory(g: Graph, c: str) -> bool:
    return force_of(g, c) == G.MANDATORY


def wants(g: Graph, c: str, sort: str, label: str | None = None) -> str:
    """What the criterion keys on: an unmet constraint of the goal, which binds its variables.

    Unmet, not merely present. A criterion is advice about what to do *next*, and a constraint that
    already holds has nothing to say about that — keying on it would make criteria fire forever on goals
    that were already partly done."""
    g.put(c, wants_sort=sort)
    if label is not None:
        g.put(c, wants_label=label)
    return c


def draw(g: Graph, c: str, name: str, ref: str, label: str, *, back: bool = False) -> str:
    """`some <name> in <ref> by <link>` — bind a further role by walking a relation.

    This is the answer to the one thing a second domain proved unsayable (`docs/deliberation.md`): a criterion could *reach* a third individual by a path but could not choose among several,
    because `nearest`/`furthest … by <link>` selects over a traversal and nothing selected by a
    condition. A draw introduces the candidate as an ordinary role, so the filter is written as
    ordinary `when` / `unless` lines — which keeps it decomposable, and therefore keeps `governing`
    able to say which line ruled a candidate out. An inline `such that …` would have made the condition
    opaque again, which is the whole thing says not to do.

    It also subsumes the selector, and says more. `furthest subject by ^on` picks the top of a pile
    because of *where it sits*; `some b in subject by ^on` + `when b is a clear_block` picks it because of
    *what is true of it* — the same block, for a stated reason.

    Transitive, like `path.via` and like the goal's own `contains+`. Candidates come back
    nearest-first, and `speaks` tries them in that order, so a criterion that could apply to several says
    the nearest thing first. Termination is `via`'s: a finite, already-materialised traversal."""
    d = g.mint("draw", name=name, ref=ref, label=label, back=back)
    g.link(c, "draw", d)
    return d


def draws_of(g: Graph, c: str) -> tuple:
    return g.targets(c, "draw")


def names_of(g: Graph, c: str) -> tuple:
    """Every role a criterion may speak of: the two `wants` binds, plus whatever it has drawn so far.

    *So far* is what makes the surface enforce declaration before use, free — `intake` reads lines in
    order, so a `when` mentioning an undrawn name simply does not find it."""
    return ROLES + tuple(g.attr(d, "name") for d in draws_of(g, c))


def test(g: Graph, c: str, *, sort: str, negated: bool = False, **fields) -> str:
    """One condition, as its own node — so `governing` can say which one failed."""
    t = g.mint("test", sort=sort, negated=negated, **{k: v for k, v in fields.items() if v is not None})
    g.link(c, "test", t)
    return t


def does(g: Graph, c: str, function: str, bindings: dict) -> str:
    """The action this criterion names. `bindings` maps each parameter to a reference, as text.

    An action is a consequent — the `call` kind, per `consequent.py`, sharing one node kind and one
    edge label with a method's rung so that a reader can ask both families the same question."""
    return CQ.call(g, c, function=function, bindings=bindings)


def action_of(g: Graph, c: str):
    got = CQ.of(g, c)
    return got[0] if got else None


def tests_of(g: Graph, c: str) -> tuple:
    return g.targets(c, "test")


# --- references ---------------------------------------------------------------------------------------
class Unresolvable(Exception):
    """A reference that names nothing in this world. Ordinary — it makes a criterion silent, not loud."""


def _here(g: Graph, frame: str, real):
    """This frame's image of a real node. `W.mapping_for` matches the immediate original, which is not
    always the real node once frames nest, so fall back to `W.resolve`, which walks the whole chain.

    **No frame is the real world, where a node stands for itself.** That is the trivial context arriving
    in a second place, and it has to be said rather than left to fall out: the walk answers `None` for a
    frame that is `None`, so a condition evaluated outside a workbench used to conclude that nothing
    existed. It matters now because a *function guard* is evaluated wherever the function is called, and
    most calls are not imagining anything."""
    if real is None:
        return None
    if frame is None:
        return real
    m = W.mapping_for(g, frame, W.identity_of(g, real))
    if m is not None:
        return W.image_of(g, m)
    for m in W.visible(g, frame):
        if W.resolve(g, m) == real:
            return W.image_of(g, m)
    return None


def resolve_ref(g: Graph, ref: str, bound: dict, frame: str, *, under: str = "root"):
    """A written reference → the real node it denotes in this frame. Raises `Unresolvable`.

    Four forms, and the vocabulary is closed:

    * `subject` / `object` — a role bound by `wants`
    * `<role>.<path>` — `path.py`, any depth, `^` for the backward hop
    * `<selector> <ref> by <link>` — a set walked transitively, and one element chosen
    * `the <name>` — a named individual, resolved the way every other block resolves one

    Navigation happens on the frame's image and the answer is handed back as the real node,
    because a `Call`'s bindings name individuals. Those are different nodes, and `driver.stands_for`
    exists because they were once confused, silently, for a whole component."""
    words = ref.split()
    if len(words) == 4 and words[0] in SELECTORS and words[2] == "by":
        start = resolve_ref(g, words[1], bound, frame, under=under)
        label, back = (words[3][1:], True) if words[3].startswith("^") else (words[3], False)
        reached = P.via(g, _here(g, frame, start), label, back=back, view=W.View(g, frame))
        if not reached:
            raise Unresolvable(f"nothing is reachable from {words[1]} by {words[3]}")
        # `via` is breadth-first, so nearest-first. The furthest is the last, and that is the whole of
        # what the two-deep pile needed — no iteration, no fixed point.
        return W.original_of(g, reached[0 if words[0] == NEAREST else -1])
    if len(words) == 2 and words[0] == "the":
        from . import intake
        try:
            return intake.resolve(g, words[1], under=under)
        except intake.Unreadable as e:
            # Authoring already refused an unresolvable name, so reaching here means the world moved
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
    reached = P.node_at(g, _here(g, frame, node), rest, view=W.View(g, frame))
    if reached is None:
        raise Unresolvable(f"{ref!r} reaches nothing in this world")
    return W.original_of(g, reached)


# --- evaluation ---------------------------------------------------------------------------------------
def _view(g: Graph, frame):
    """The world to traverse in, or `None` for the real one. See `_here` — no frame is not an empty
    world, it is the world."""
    return W.View(g, frame) if frame is not None else None


def _holds(g: Graph, t: str, bound: dict, frame: str, under: str) -> bool:
    """Does this one test hold? An unresolvable reference is a test that does not hold, never a crash."""
    try:
        left = resolve_ref(g, g.attr(t, "left"), bound, frame, under=under)
    except (Unresolvable, P.BadPath):
        return False
    sort = g.attr(t, "sort")
    if sort == "exists":
        return left is not None
    if sort == "same":
        # Two references denoting the SAME individual. The one sort the condition language did not have,
        # and the first thing a function guard wants to say: `stack(b, onto) unless b is onto`. It is
        # deliberately about identity rather than about a value, which is `path.py`'s rule — `is` compares
        # identities, everything else compares values — and `types.Rel` has carried the same pair
        # (`is` / `is not`) inside a schema all along. What was missing was the form that relates two
        # *arguments*, which is exactly the hole `driver.enumerate_frame` was patching in Python.
        #
        # Compared as identities, never as this frame's versions: the two sides are already real nodes,
        # and comparing versions would answer *no* for one individual seen through two frames.
        try:
            other = resolve_ref(g, g.attr(t, "right"), bound, frame, under=under)
        except (Unresolvable, P.BadPath):
            return False
        return left is not None and left == other
    if sort == "type":
        from .types import is_a
        return is_a(g, _here(g, frame, left), g.attr(t, "label"), view=_view(g, frame))
    if sort == "attr":
        return g.attr(_here(g, frame, left), g.attr(t, "key")) == g.attr(t, "value")
    if sort == "link":
        try:
            right = resolve_ref(g, g.attr(t, "right"), bound, frame, under=under)
        except (Unresolvable, P.BadPath):
            return False
        here, there = _here(g, frame, left), _here(g, frame, right)
        view = _view(g, frame)
        if g.attr(t, "transitive"):
            # `x contains+ y` — *reachable at any depth*. This arrived with the shared proposition
            # grammar: `+` had existed only in a goal line, though `docs/authoring.md` says it belongs "in a link
            # position — a goal line or a query", and a condition IS the query. The parser accepting it
            # while this read one direct edge would have been silent acceptance of a wrong meaning, which
            # is the failure mode this codebase keeps catching — so the evaluator moved with the surface.
            # Same reader `goal.holds` uses, so the two cannot disagree about what `+` means.
            from .path import reaches
            return reaches(g, here, g.attr(t, "label"), there, view=view)
        # Resolution on the target: an edge names the identity, so the frame's version of it is what
        # this compares against — the same correction `goal.holds` carries, for the same reason.
        got = P.adjacent(g, here, g.attr(t, "label"), view=view)
        return bool(got) and got[0] == there
    if sort == "wants":
        # A test about the goal, not the world — *"is anything still required of this thing?"*. The
        # bottom-up ordering knowledge needs it: stack onto `y` only once `y` itself has nowhere left to go.
        for c in _open_constraints(g, t, frame, bound):
            if g.attr(c, "sort") == g.attr(t, "want_sort") and \
                    (g.attr(t, "label") is None or g.attr(c, "label") == g.attr(t, "label")) and \
                    g.target(c, "subject") == left:
                return True
        return False
    raise ValueError(f"unknown test sort {sort!r}")


def holds(g: Graph, t: str, bound: dict, frame=None, under: str = "root") -> bool:
    """Does this one condition hold, with `bound` mapping each name to a real node?

    The public form, and the one place negation is applied — `_holds` answers the *positive* question and
    every caller used to fold `negated` in by hand, which is one hand too many now that a second family
    evaluates conditions. `bound` is roles for a criterion and parameters for a function guard; the
    condition language cannot tell the difference, which is exactly why it can serve both.

    `frame=None` is the real world (see `_here`), so a condition is evaluable wherever it is written."""
    return _holds(g, t, bound, frame, under) != bool(g.attr(t, "negated"))


def _open_constraints(g: Graph, node: str, frame: str, bound: dict) -> tuple:
    return bound.get("__unmet__", ())


#: Which field carries a constraint's label, per sort. Three different names for one idea, and a
#: criterion keying on `type` silently matched nothing until a second domain was tried: `goal.require_type`
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

    A draw that reaches nothing removes its binding rather than passing it through empty-handed:
    *"some container inside the warehouse"* when there is none is a situation the criterion has nothing to
    say about, not a criterion with a hole in it.

    Nested draws multiply, which is the one place a criterion's cost is not bounded by the goal. It is
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
            for n in P.via(g, _here(g, frame, start), label, back=back, view=W.View(g, frame)):
                real = W.original_of(g, n)
                if real is None:
                    continue
                nxt.append({**b, name: real})
        bounds = tuple(nxt)
    return bounds


def _try(g: Graph, c: str, bound: dict, frame: str, under: str) -> tuple:
    """One binding, tried: `(Call, reasons, recognised)`.

    `recognised` is True once every `when`/`unless` line has held — i.e. the criterion recognises this
    situation — whether or not its action turns out to apply. That distinction is what force needs: a
    directive refuses when it recognises a situation it cannot act in, and stays silent when it does not
    recognise the situation at all. Conflating them would make a directive refuse everywhere it merely had
    nothing to say.

    One place, because `speaks` and `governing` must never disagree. They did: `governing` checked
    only the `test` lines while `speaks` also required the action's references to resolve — so on Sussman's
    root frame it reported all three criteria as having spoken when only one could. Two paths computing
    *"the same"* thing differently is the defect shape this codebase keeps recording, and landing it in the
    one feature whose entire job is to explain truthfully is the worst possible place for it.

    An action's arguments are part of its condition, and that is a deliberate reading rather than an
    implementation accident. *"Take the topmost block off the pile above x"* simply does not apply when
    there is no pile; requiring the author to write a separate `when` line for it would make silence
    depend on remembering to guard, and a forgotten guard would become a crash mid-search."""
    from .driver import Call
    reasons = [describe_test(g, t) for t in tests_of(g, c)
               if _holds(g, t, bound, frame, under) == bool(g.attr(t, "negated"))]
    if reasons:
        return None, tuple(reasons), False
    # From here the criterion recognises the situation; anything that fails now is the action, not the
    # condition. That line is what force needs: a directive refuses when it recognises a situation it
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

    # A criterion whose action does not apply here is silent, not loud. `driver.check_call` raises, which is right for a *Python* decider: one that
    # names an ill-typed or forbidden call is a bug in the caller. A criterion is different. It is general
    # knowledge meeting a particular world, so *"the first container happens to be the one this goal
    # forbids"* is a situation, not a mistake — and raising there abandoned a search that plain
    # enumeration could finish. Measured in the warehouse with two containers.
    #
    # Silent, but never silently: the reason is handed back, so `governing` can say *"this criterion
    # would have said put_in(crate), and the goal forbids it"*. Silence that cannot be interrogated is the
    # thing exists to prevent.
    from .driver import Undecidable, check_call
    try:
        check_call(g, bound["__goal__"], frame, call, bound.get("__prefix__"))
    except Undecidable as e:
        return None, (str(e),), True
    return call, (), True


def speaks(g: Graph, c: str, goal: str, frame: str, subject: str, *, under: str = "root",
           prefix=None):
    """Does this criterion have something to say here? Returns `(Call | None, blocked)`.

    `blocked` is non-empty when the criterion recognised the situation and still could not act — which
    only a directive treats as a refusal; for a criterion it is ordinary silence with a reason attached.

    Every failure is silence. A reference that resolves to nothing, a test that does not hold, an action
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


def decider(g: Graph, goal: str, subject: str, *, under: str = "root") -> str:
    """The decision procedure as a node, so a search can point at what is deciding it.

    Because it was a Python keyword argument, and that made it invisible and unresumable.
    `decide` returns a closure handed to `pursue(propose=…)`; `search.open_search`'s docstring concedes
    the split in as many words — *"everything a step needs that is NOT a python callable lives here"*.
    Measured: the identical search node, with the
    identical criteria in the graph, takes 3 imagined states when `pursue` passes the hook and 52
    when `loop.tick` advances it — because `loop.advance` forwards whatever `**hooks` its *caller* held.
    Guidance was a property of the Python caller rather than of the search.

    This is the same move `search.stop` already makes one screen up in `driver.step`, and for the
    reason recorded there: *the same decision expressed as data, which the standing principle requires.*
    A `decide=` hook stays available and is not redundant — a Python callable consulted per proposal is
    right for a ranker-frequency decision and wrong for anything a domain author should be able to write.

    It records what to consult, never a frozen answer: the criteria are read from the graph when the
    search asks, so withdrawing one (`discourse.live`) still takes effect mid-search."""
    d = g.mint("decider", how="criteria", under=under)
    g.link(d, "goal", goal)
    g.link(d, "subject", subject)
    return d


def proposer_for(g: Graph, d: str):
    """Rebuild the proposer a `decider` node describes. The dispatch on `how` is deliberately a closed
    vocabulary of one: a second kind of decider is a decision about execution, not a string somebody adds."""
    how = g.attr(d, "how")
    if how != "criteria":
        raise ValueError(f"decider {d} says how={how!r}; the only decision procedure is 'criteria'")
    return decide(g, g.target(d, "goal"), g.target(d, "subject"), under=g.attr(d, "under") or "root")


def decide(g: Graph, goal: str, subject: str, *, under: str = "root"):
    """The `propose=` / `decide=` hook that reads the authored list. First match wins.

    Drops into `driver.pursue(propose=...)`, which is the seam where it pays: measured, asking the same
    knowledge *before* enumeration rather than after is 6.6× faster at sixty blocks, because `_offer`
    otherwise builds the whole O(N²) product and then throws it away."""
    def propose(situation):
        for c in criteria(g):
            got, blocked = speaks(g, c, goal, situation["frame"], subject, under=under,
                                  prefix=situation.get("prefix"))
            if got is not None:
                return got
            # A directive that recognises a situation it cannot ACT in refuses, and this is the
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

    Load-bearing rather than a nicety, because criteria prune. Under ranking the alternatives are
    still on the frontier and can be looked at; when a criterion suppresses enumeration they were never
    built, so this is the only window onto what was discarded. Without it the first wrong criterion
    produces *"no plan found"* with nothing behind it.

    This is why a condition is a pattern and not a program: each test is its own node, so the answer
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
    """`(criterion, Call)` for every criterion that would speak here — not just the winner.

    The list `decide` throws away. First-match-wins is the whole control rule, so everything after the
    first is invisible at run time; this is what makes it visible to a reader."""
    out = []
    for c in criteria(g):
        got, _blocked = speaks(g, c, goal, frame, subject, under=under, prefix=prefix)
        if got is not None:
            out.append((c, got))
    return tuple(out)


def disagreements(g: Graph, goal: str, frame: str, subject: str, *, under: str = "root",
                  prefix=None) -> tuple:
    """Criteria that would act differently from the one that wins here.

    Returns `(winner, winning_call, loser, losing_call)` per disagreement, in precedence order.

    This is `docs/deliberation.md`'s last untested claim, made good. of `docs/deliberation.md`
    rejected program-conditions partly because *"`conflict.py` cannot say two rules disagree by comparing
    two programs"*, and answered that the cost degrades rather than dies, because a criterion's
    return is a named function with denoted arguments — trivially comparable — even when its condition
    is not. That was an argument. This is the thing itself, and it is cheap: `speaks` already answers per
    criterion, so the comparison is a pass over answers rather than over conditions.

    Naming the same call is redundancy, not disagreement. `conflict.py`'s standing correction applies
    here unchanged: *a later action overriding an earlier one is not a disagreement, it is what doing
    things looks like.* Two criteria that agree are simply two ways of saying one thing, and reporting them
    would bury the real cases.

    This is exact and situational — it needs a frame, and it reports no false positives. A static
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
            "same": f"{left} is {g.attr(t, 'right')}",
            "type": f"{left} is a {g.attr(t, 'label')}",
            "attr": f"{left}.{g.attr(t, 'key')} = {g.attr(t, 'value')!r}",
            # The `+` must survive the round trip, or a reader is shown a condition that says something
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
    who = g.attr(source_of(g, c), "label")
    lines = [f"{strength_of(g, c)} {g.attr(c, 'label')!r} (says {who}): when the goal wants "
             f"{g.attr(c, 'wants_sort')} {g.attr(c, 'wants_label') or ''}".rstrip() + f", do {doing}"]
    lines += [f"    {describe_test(g, t)}" for t in tests_of(g, c)]
    return "\n".join(lines)


__all__ = ["SUBJECT", "OBJECT", "ROLES", "NEAREST", "FURTHEST", "SELECTORS", "Unresolvable",
           "criteria", "declare", "wants", "test", "does", "action_of", "tests_of",
           "decider", "proposer_for",
           "draw", "draws_of", "names_of", "constraint_label",
           "resolve_ref", "speaks", "decide", "governing", "force_of", "strength_of", "source_of",
           "is_mandatory", "proposals_here", "disagreements",
           "describe_disagreements", "describe_test", "describe"]

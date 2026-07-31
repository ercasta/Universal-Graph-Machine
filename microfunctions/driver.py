"""DRIVER — the outer loop. Pursue a goal by imagining, and let the record of what worked BE the plan.

This is the piece the engine never had. `plan.py` chains, `workbench.py` imagines, `execution.py` replays,
`selection.py` ranks — and until now *nothing invoked any of them*. The computation model was unspecified.

**The goal here is to produce a plan, not to act** — a goal *about* planning, which is the homoiconicity
claim paying rent rather than being asserted: a plan is a node like any other, so wanting one is an ordinary
goal. Nothing dispatches, nothing touches the world; the whole search happens on a workbench, and
`dispatch.service` refusing an imagined target means that is guaranteed rather than merely intended.

**⭐ The plan is not built, it is FOUND. `execution.path_to(wb, winning_frame)` already is one.** The
frame tree records every state the system imagined and every transformation that got there, so the path to
the frame that satisfies the goal is a replayable plan — and `execution.execute` runs it, unchanged. There
was never a plan-construction step to write.

**Why forward search here, when `plan.py` chains backwards.** Backward chaining over return types cannot
express *applying the same operator repeatedly*: a function has one declared return type, so "stack a block,
then stack another" is not a chain of distinct casts. Blocks-world needs repetition, and repetition comes
from the **loop**, not from the planner. That is not a defect in `plan.py` — the two answer different
questions, and this is the honest division:

* `plan.py` — *what sequence of casts reaches this type?* Cheap, no imagining, right when the operators form
  a pipeline of distinct stages.
* here — *what do I get if I try this, and then this?* Costly (a frame per step), right when the same
  operator applies repeatedly and the interesting question is the resulting **state**.

**Binding search lives here, deliberately.** `selection.candidates` is restricted to single-parameter
functions, and says why: "a multi-parameter function needs a *binding* proposed, not just a subject, and
inventing bindings is a different problem (search) that should not hide inside candidate generation." This
is that different problem, in the module where search belongs. `selection.py` is unchanged.

**⚠ Honest scope.** Depth-first with a visited set, first solution wins, bounded by `max_steps`. No cost
model, no heuristic, no System 1 — candidate ordering is declaration order. The frame tree makes this
expensive (a full copy per imagined step), which is a known and measured limit, not a surprise. It is
adequate for a handful of blocks and should not be mistaken for a planner.
"""
from __future__ import annotations

from itertools import product

from . import execution as X
from . import function as fn
from . import goal as G
from . import thread as T
from . import workbench as W
from .graph import Graph
from .isa import F
from .types import is_a


def proposals(g: Graph, frame: str) -> tuple:
    """Every `(function, {param: mapping})` that could be applied in this frame.

    The cartesian product of type-valid bindings, minus the ones binding one node to two parameters —
    which is not a heuristic but a correctness rule for operators like `stack(b, onto)`, where the type
    system cannot say `b ≠ onto`. ⚠ `types.py` validates ONE argument at ONE call site by design, so a
    relation *between* parameters has no declared form and has to be enforced here or in the body."""
    here = W.mappings(g, frame)
    out = []
    for name in fn.names(g):
        # ⚠ A MOCK IS NOT AN ACTION. It is an assumption about how a real call turns out, so proposing one
        # would be planning to *assume* something rather than to do it — and the resulting "plan" would name
        # a function that must never be executed for real. `workbench.step` substitutes the mock when the
        # real operator is stepped, which is where that belongs. Invisible in a library without mocks,
        # which is exactly why it went unnoticed until a scenario had one.
        if fn.mocks_target(g, name) is not None:
            continue
        params, _ = fn.load(g, name)
        ptypes = fn.param_types(g, name)
        if not params or any(p not in ptypes for p in params):
            continue
        per_param = []
        for p in params:
            fits = [m for m in here if is_a(g, W.image_of(g, m), ptypes[p])]
            if not fits:
                break
            per_param.append(fits)
        if len(per_param) != len(params):
            continue
        for combo in product(*per_param):
            if len(set(combo)) != len(combo):
                continue                       # one node cannot fill two roles
            out.append((name, dict(zip(params, combo))))
    return tuple(out)


def view_in(g: Graph, frame: str):
    """How a goal's constraints are asked of an *imagined* world.

    A constraint names real individuals ("a on b"). Inside a frame those individuals are represented by
    copies, so checking means translating each named node into this frame's image of it. `goal.py` takes
    this as a `view` rather than learning about workbenches — the layering runs one way."""
    def view(node):
        if node is None:
            return None
        m = W.mapping_for(g, frame, node)
        return W.image_of(g, m) if m is not None else None
    return view


def establishes(g: Graph, name: str) -> tuple:
    """What this function could make true, read **off its stored body**. Returns `(effects, unknown)`.

    ⭐ This is homoiconicity earning its keep rather than being asserted. Nothing declares effects — the
    north star deliberately moved away from operators carrying declarative effect descriptions — but a
    function *is* graph data, so we can look at what its instructions write and ask "could this establish an
    `on` edge?". No new representation, no authoring burden, and it cannot fall out of date with the body
    because it *is* the body.

    **⭐ Effects carry their ROLES, and that turned out to matter more than the label.** An effect is
    `(kind, label, subject_param, object_param)`: `stack` does not merely "write an `on` edge", it links
    *its parameter `b`* on *its parameter `onto`*. Without that, `stack(b=b, onto=a)` looks exactly as
    promising for the constraint "a on b" as `stack(b=a, onto=b)` does, because both involve the same two
    blocks — and the ranking degrades to little better than blind. Roles are read from the operands, so this
    costs nothing extra.

    **⭐⭐ A function's effects INCLUDE ITS MOCKS', and that is what makes planning look at expectations
    rather than at type signatures.** `scan_dir`'s own body is a `DISPATCH` and a `SET` — statically it
    establishes almost nothing, because everything interesting happens on the other side of a tool call. The
    knowledge that listing a directory *produces file nodes* is not in the signature and not in the body: it
    is in the **mock**, which is precisely the declared assumption about how the call turns out.

    So the effects of an operator are the union of what its body writes and what each of its assumed
    outcomes writes. That is the same thing `workbench.predicted_changes` derives at planning time, reached
    statically here — and it is what lets a goal of "some file exists" find `scan_dir` at all. Without it,
    an opaque tool call is maximally relevant to everything and informative about nothing.

    ⚠ **Conservative on purpose.** If a label or key comes from a register, or the body calls out to
    another function, we cannot tell statically — so `unknown` is returned and the caller must treat the
    function as potentially relevant. This orders candidates; it never rules one out. An over-approximation
    that loses no solutions is the only kind safe to use here."""
    return _effects(g, name, include_mocks=True)


def _effects(g: Graph, name: str, *, include_mocks: bool) -> tuple:
    params, program = fn.load(g, name)

    def role(operand):
        """The parameter an operand names, if it names one — otherwise nothing we can reason about."""
        return operand.name if isinstance(operand, F) and operand.name in params else None

    effects, unknown = set(), False
    for ins in program:
        if isinstance(ins, str):
            continue                                        # a label, not an instruction
        a = ins.args
        arg = a[1] if len(a) > 1 else None
        if ins.op in ("LINK", "LINK_AT", "UNLINK"):
            if isinstance(arg, str):
                obj = a[-1] if ins.op != "UNLINK" else None
                effects.add(("link", arg, role(a[0]), role(obj) if obj is not None else None))
            else:
                unknown = True
        elif ins.op == "SET":
            effects.add(("attr", arg, role(a[0]), None)) if isinstance(arg, str) else (unknown := True)
        elif ins.op == "NEW":
            # ⭐ Bringing something into existence is an effect too — the one a goal like "some file
            # exists" is looking for, and the one a type signature cannot express.
            effects.add(("mint", a[1], None, None)) if len(a) > 1 and isinstance(a[1], str) \
                else (unknown := True)
        elif ins.op in ("INVOKE", "CALL", "DISPATCH"):
            unknown = True                                  # the effect happens somewhere else

    if include_mocks:
        for outcome in fn.mocks_of(g, name):                # depth 1: a mock has no mocks of its own
            more, more_unknown = _effects(g, outcome, include_mocks=False)
            effects |= more
            unknown = unknown or more_unknown
    return frozenset(effects), unknown


def relevance(g: Graph, name: str, bindings: dict, unmet: tuple) -> int:
    """How promising this proposal looks against the constraints that are still false. Higher is sooner.

    Four bands: **4** — this call, with these bindings, writes *exactly* the constraint (right label, and
    the right individual in each role); 3 — right label, both individuals involved but the roles do not
    line up; 2 — right label, one of the right individuals; 1 — right label; 0 — nothing to do with any
    open constraint.

    ⚠ **Band 4 versus band 3 is the one that earns its place.** Without roles, `stack(b=b, onto=a)` scores
    the same as `stack(b=a, onto=b)` for the constraint "a on b", since both involve a and b — and the
    ranking barely beats blind search (measured: 13 imagined states versus 15). Distinguishing them is what
    makes the guidance real.

    **⚠ This RANKS, it never FILTERS, and that is the whole design.** A greedy means–ends planner that only
    tries constraint-satisfying moves cannot solve Hanoi or the Sussman anomaly, where progress requires
    *undoing* something first. Scoring 0 puts a move last, not out of reach — so the hard cases stay
    solvable while the easy ones stop being searched blindly. This is also System 1's first real job, and
    notably it needs none of the neighbourhood/radius question resolved."""
    effects, unknown = establishes(g, name)
    bound = {p: (W.resolve(g, m) or W.image_of(g, m)) for p, m in bindings.items()}
    involved = set(bound.values())
    best = 0
    for c in unmet:
        sort = g.attr(c, "sort")
        want_label = g.attr(c, "label") if sort == "link" else g.attr(c, "key")
        kind = {"link": "link", "attr": "attr"}.get(sort)
        # ⭐ "SOMETHING of this type must exist" is answered by an operator that MINTS one — the existential
        # case, which no parameter or return signature could express, and which is only visible because
        # `establishes` reads the mocks. Purely additive: type constraints stay conservatively matched
        # below, so no proposal can score lower than it did before.
        if sort == "type" and g.target(c, "subject") is None and \
                any(e[0] == "mint" and e[1] == g.attr(c, "type") for e in effects):
            best = max(best, 4)
        matching = [e for e in effects if kind is None or (e[0] == kind and e[1] == want_label)]
        if not matching and not unknown:
            continue                                        # cannot touch this constraint at all
        subject, obj = g.target(c, "subject"), g.target(c, "object")

        for _k, _lbl, sp, op in matching:                   # does a role assignment line up exactly?
            if sp is not None and bound.get(sp) == subject and \
                    (obj is None or (op is not None and bound.get(op) == obj)):
                best = max(best, 4)
        wants = {n for n in (subject, obj) if n is not None}
        if wants and wants <= involved:
            best = max(best, 3)
        elif wants & involved:
            best = max(best, 2)
        else:
            best = max(best, 1)
    return best


def state_of(g: Graph, frame: str) -> frozenset:
    """A canonical signature of the world as imagined in this frame — the visited-set key.

    ⚠ **Dedupe on the STATE, not on the action, and the difference is not academic.** The first version of
    this driver skipped any `(function, arguments)` triple it had already imagined anywhere. That silently
    made the search unable to solve a three-block tower: the root frame enumerates every pair, so *every*
    action is marked seen at depth 1, and each branch below it then has nothing left to try. Two-step
    solutions became unreachable while the driver reported an honest-looking "no plan found".

    Comparing frames or mappings directly would treat every copy as new, since each frame mints its own. So
    each node is identified by what it *really* is (`resolve`), and the signature is its attributes plus its
    edges rewritten in those terms."""
    ident = {}
    for m in W.mappings(g, frame):
        ident[W.image_of(g, m)] = W.resolve(g, m) or m
    out = []
    for image, who in ident.items():
        attrs = tuple(sorted((k, v) for k, v in g.attrs.get(image, {}).items() if k != "kind"))
        edges = tuple(sorted((lbl, tuple(ident.get(t, t) for t in g.targets(image, lbl)))
                             for lbl in g.labels(image)))
        out.append((who, attrs, edges))
    return frozenset(out)


def pursue(g: Graph, goal: str, thread: str, subject: str, *,
           max_steps: int = 60, max_depth: int = 6, rank=None, guided: bool = True) -> dict:
    """Search for a state satisfying `goal`, imagining every step. Returns a report.

    Everything the system considers is recorded on the thread as it happens, so *how* it got there is
    inspectable afterwards rather than reconstructible only by re-running it. On success the report carries
    the winning frame and the **plan**, which is the frame path — already replayable by `execute`.

    `rank` overrides `relevance` — the hook where a better judgement (a learned policy, a language model
    reading `function.catalogue`) plugs in, and the same shape `selection.score` already uses for the same
    reason. Passing a constant turns this back into blind search, which is how the guidance is measured."""
    wb = W.open_workbench(g, subject, label=f"pursuing {g.attr(goal, 'label')}")
    root = W.root_frame(g, wb)
    opened = T.attend(g, thread, goal, why="taking on the goal", note=G.describe(g, goal))

    def asked_of(frame):
        """`(view, under)` — how the goal is checked inside this imagined frame."""
        return view_in(g, frame), W.image_of(g, W.mapping_for(g, frame, subject))

    score = rank if rank is not None else relevance
    view, under = asked_of(root)
    if G.satisfied(g, goal, view=view, under=under) and not G.outstanding(g, goal, ()):
        return _done(g, goal, thread, wb, root, opened, "already satisfied", 0, ())

    def still_open(frame):
        v, u = asked_of(frame)
        return G.unmet(g, goal, view=v, under=u)

    # ⭐ THE FRONTIER HOLDS PROPOSALS, NOT FRAMES — and that is what makes the guidance worth anything.
    #
    # ⚠ Two wrong versions preceded this, and both are worth recording. First it was depth-first over
    # frames: it committed to the first promising child and explored it to exhaustion, and adding *one*
    # irrelevant rule to the library was enough to burn the whole budget down a branch that could never
    # close the goal, while the sibling that solved it in one more move sat untouched. Then it was
    # best-first over frames — which fixed that, but *measured no better than unguided* (15 imagined states
    # against 14), because every proposal in a frame was imagined before any frame was chosen. Ordering
    # inside a frame cannot save work you have already done.
    #
    # Ranking whole proposals globally is what lets the search commit one step at a time.
    #
    # ⚠ The third wrong version — subtle, and it made the guided search *worse than breadth-first*. The key
    # was `(constraints open, -relevance, depth)`, where "constraints open" was the PARENT frame's count.
    # So an unexplored root proposal that would obviously close a constraint carried its parent's score of
    # 2, while mediocre moves two levels down carried 1, and the search abandoned the good move for them
    # permanently. A proposal must be judged by the world it would PRODUCE, not the one it starts from.
    #
    # Hence `expected`: a band-4 proposal writes exactly an open constraint, so it is expected to close
    # one. That is the whole heuristic — cheap, obviously derived from the constraints, and it is what
    # makes the guidance real (measured: 3 imagined states, against 55 unguided).
    def visited_key(frame: str, trace: tuple):
        """⚠ The state alone is NOT the identity of a search node once liveness is in play. Two routes to
        the same world differ if one has already done a required action and the other has not — deduping on
        the world would silently discard the finished one. So what is still outstanding is part of the key."""
        return (state_of(g, frame), G.outstanding(g, goal, trace))

    frontier: list = []
    seen, steps, refused = {visited_key(root, ())}, 0, []

    def offer(frame: str, depth: int, trace: tuple) -> None:
        open_now = still_open(frame)
        for name, bindings in proposals(g, frame):
            # ⭐ CONSTRAINTS ON THE PLAN, checked BEFORE imagining — so a forbidden action costs nothing.
            # ⚠ This FILTERS where `relevance` only RANKS, and the difference is principled: relevance is
            # a guess about what will help, so filtering on it could lose a solution (Sussman's anomaly
            # needs a low-scoring move). A safety breach is a proof — no continuation of a plan that used
            # a forbidden action makes it unused — so pruning is sound. Rank a guess; prune a proof.
            ahead = trace + ((name, frozenset(W.resolve(g, m) or W.image_of(g, m)
                                              for m in bindings.values())),)
            hit = G.breached(g, goal, ahead)
            if hit:
                refused.append((name, tuple(G.describe_constraint(g, c) for c in hit)))
                continue
            if not guided:
                frontier.append(((0, 0, depth), frame, depth, name, bindings, len(open_now), ahead))
                continue
            rank_here = score(g, name, bindings, open_now)
            expected = len(open_now) - (1 if rank_here >= 4 else 0)
            frontier.append(((expected, -rank_here, depth), frame, depth,
                             name, bindings, len(open_now), ahead))

    offer(root, 0, ())
    while frontier and steps < max_steps:
        frontier.sort(key=lambda item: item[0])
        _key, frame, depth, name, bindings, open_count, trace = frontier.pop(0)
        steps += 1

        nxt, _tr = W.step(g, wb, frame, name, bindings)
        T.applied(g, thread, name, {p: W.image_of(g, m) for p, m in bindings.items()},
                  why=f"depth {depth + 1}, {open_count} constraint(s) open")

        nview, nunder = asked_of(nxt)
        # ⚠ Both halves, and liveness only here: the world must be right AND the plan must have done
        # everything it was required to. A plan that reaches the state without its mandated step is not
        # finished — but it was never in violation on the way, which is why this is not a pruning test.
        if G.satisfied(g, goal, view=nview, under=nunder) and not G.outstanding(g, goal, trace):
            return _done(g, goal, thread, wb, nxt, opened, "found", steps, tuple(refused))

        reached = visited_key(nxt, trace)
        if reached in seen:
            continue                           # this world has been imagined before, by another route
        seen.add(reached)
        if depth + 1 < max_depth:
            offer(nxt, depth + 1, trace)

    view, under = asked_of(root)
    still_open = ", ".join(G.describe_constraint(g, c)
                           for c in G.unmet(g, goal, view=view, under=under))
    blocked = sorted({r for _n, rs in refused for r in rs})
    T.attend(g, thread, goal, why="exhausted the search", note="no plan found")
    return {"found": False, "workbench": wb, "steps": steps, "goal": goal,
            "unmet": still_open, "refused": tuple(refused), "blocked_by": tuple(blocked),
            "why": f"no state meeting [{still_open}] within depth {max_depth} after {steps} "
                   f"imagined steps" + (f"; {len(refused)} action(s) ruled out by [{', '.join(blocked)}]"
                                        if blocked else "")}


def _done(g: Graph, goal, thread, wb, frame, opened, how, imagined, refused) -> dict:
    """Close the goal, and tie the moment that closed it back to the moment it was taken on."""
    subject = g.target(wb, "subject")
    under = W.image_of(g, W.mapping_for(g, frame, subject))
    found = G.witness(g, goal, view=view_in(g, frame), under=under)
    G.close_goal(g, goal, found, seen_in=frame)

    plan = X.path_to(g, wb, frame)
    closing = T.attend(g, thread, goal, why=f"goal met ({how})",
                       note=f"plan is {len(plan) - 1} step(s)")
    T.connect(g, closing, opened, "achieves")
    return {"found": True, "workbench": wb, "frame": frame, "goal": goal, "witness": found,
            "plan": plan, "length": len(plan) - 1, "steps": imagined, "how": how,
            "refused": refused, "blocked_by": tuple(sorted({r for _n, rs in refused for r in rs}))}


def plan_steps(g: Graph, result: dict) -> tuple:
    """The plan as function names in order — the readable form of the frame path."""
    if not result.get("found"):
        return ()
    out = []
    for f in result["plan"][1:]:
        tr = g.target(f, "via")
        if tr is not None:
            out.append(g.attr(tr, "function"))
    return tuple(out)


def _name(g: Graph, node) -> str:
    """A readable handle for a node in a plan. ⚠ A `label` is a convenience for *display only* — nodes are
    nameless and identity is never a name (`docs/units` records that lesson at length)."""
    return f"{g.attr(node, 'label')}" if g.attr(node, "label") else str(node)


def describe(g: Graph, result: dict) -> str:
    if not result.get("found"):
        return f"no plan: {result['why']}"
    lines = [f"plan found in {result['length']} step(s) after imagining {result['steps']}, {G.describe(g, result['goal'])}"]
    for f in result["plan"][1:]:
        tr = g.target(f, "via")
        if tr is None:
            continue
        args = ", ".join(f"{g.attr(b, 'param')}={_name(g, W.image_of(g, g.target(b, 'mapping')))}"
                         for b in g.targets(tr, "arg"))
        lines.append(f"  {g.attr(tr, 'function')}({args})")
    return "\n".join(lines)


__all__ = ["proposals", "state_of", "pursue", "plan_steps", "describe"]

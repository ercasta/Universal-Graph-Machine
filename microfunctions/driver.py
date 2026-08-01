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
from . import isa
from . import path as P
from . import thread as T
from . import workbench as W
from .graph import Graph
from .isa import F, R
from . import types as TY
from .types import is_a


# --- deliberation: the verbs a decision can return ------------------------------------------------
#
# ⭐ THE SEAM `pursue` NEVER HAD. It was a closed loop — nothing could intervene between two imagined
# steps — so "what should I do next?" was not an expressible question, only a `while` condition. That made
# deliberation the thing this system computes *with* and cannot compute *about*: the same defect attention
# had before `thread.py` and the goal had before `goal.py`, in its third place. See `deliberation.md`.
#
# ⚠ The set is CLOSED on purpose. It is the vocabulary everything authored has to speak, and a verb that
# means "something else" would make a decision unreadable to the reflective functions that are the point.
EXPAND = "expand"            # imagine the best-ranked proposal — the default, and today's whole behaviour
DECOMPOSE = "decompose"      # post subgoals instead of enumerating actions   (needs goal hierarchy)
COMMIT = "commit"            # stop planning; what we have is what we will do
SENSE = "sense"              # stop planning and act IN ORDER TO LEARN        (needs ignorance)
REFUSE = "refuse"            # no sanctioned way to proceed; do not improvise

VERBS = (EXPAND, DECOMPOSE, COMMIT, SENSE, REFUSE)
_STOPS = (COMMIT, SENSE, REFUSE)

#: Verbs whose machinery does not exist yet. Returning one raises rather than being ignored — a decision
#: silently doing nothing is exactly the class of failure this project keeps catching.
_UNBUILT = {DECOMPOSE: "per-STEP decomposition; a method applies per GOAL, via driver.attempt "
                       "(deliberation.md §4 — methods are consulted once per goal, not per step)"}


class Undecidable(Exception):
    """A decision named a verb whose machinery is not built. Loud, and naming what is missing."""


def proposals(g: Graph, frame: str, *, allow=None) -> tuple:
    """Every `(function, {param: mapping})` that could be applied in this frame.

    The cartesian product of type-valid bindings, minus the ones binding one node to two parameters —
    which is not a heuristic but a correctness rule for operators like `stack(b, onto)`, where the type
    system cannot say `b ≠ onto`. ⚠ `types.py` validates ONE argument at ONE call site by design, so a
    relation *between* parameters has no declared form and has to be enforced here or in the body.

    `allow` is a predicate on the function name, and it EXCLUDES rather than orders. ⚠ That is only
    legitimate for a proof, never for a guess — the same line `relevance` sits on the other side of.
    `query.py` uses it to bar any function that could dispatch from being used as a derivation, which is a
    proof about the stored body, not an opinion about what will help."""
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
        if allow is not None and not allow(name):
            continue
        params, _ = fn.load(g, name)
        ptypes = fn.param_types(g, name)
        if not params or any(p not in ptypes for p in params):
            continue
        per_param = []
        for p in params:
            # ⚠ Gather the type's demands ONCE per parameter, not once per candidate. Resolving the name
            # and walking its `base` chain depends only on the type, and redoing it per candidate was the
            # dominant remaining cost of enumeration — 1,025 rebuilds per enumeration in a world with 200
            # nodes that fit nothing. `requirements` stores nothing, so this hoists without a cache.
            reqs = TY.requirements(g, ptypes[p])
            if reqs is None:
                break                          # undeclared parameter type — no candidate can satisfy it
            fits = [m for m in here if not TY.fails(g, W.image_of(g, m), reqs)]
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

    **⭐ A role is a PATH, not just a parameter name, which is what lets this read a function that has to
    NAVIGATE.** Three forms, distinguishable by inspection and never confusable with each other:

    | role | means |
    |---|---|
    | `c` | the parameter `c` |
    | `c.right` | what the body reached by `GET`ting `c`'s `right` — `c.child[2]` for an indexed hop |
    | `$it` | a node this body MINTED, held in register `it` — a local subject with no caller-side identity |

    Without the middle form, `lower_threshold(c)` — `GET R(rhs) F(c) "right"` then `SET R(rhs) …` — reported
    **no effect on anything**, because the write landed on a register rather than a parameter. Reported by
    `../pystrider`, and the case is general: *read a part, write to that part* is what most operations on
    structured data look like, so the functions whose effects were invisible were exactly the ones that do
    real work on a structure. The provenance is derivable from the instruction list and costs nothing at
    runtime, since it is read statically off a body that is already stored.

    ⚠ A path is only as good as the register's last assignment: **anything else written into that register
    clears the role** (`isa.WRITES_REGISTER` is the authority on what counts), and an `ATTR` clears it too,
    because a register holding an attribute *value* denotes no node at all.

    ⚠ **Conservative on purpose, and `unknown` now says WHAT it is unsure about.** If a label or key comes
    from a register, or the body calls out to another function, we cannot tell statically. `unknown` is a
    **frozenset of the roles the unreadable instructions concern**, with `None` meaning "somewhere we cannot
    name at all" (a call, a computed subject). Empty means the body was read completely, so `if unknown:`
    and `not unknown` read exactly as they did when this was a bool.

    That granularity is for consumers reading effects as a **description** rather than as a ranking hint:
    `../pystrider` abstains from recognising a node whenever anything was unreadable, and a whole-function
    flag darkened descriptions that were provably complete for their own subject — an unreadable write to
    `y` said nothing about `x`, but looked as though it might.

    ⚠ **The return value is an OVER-APPROXIMATION by contract.** It exists to ORDER candidates and it never
    rules one out, so it is deliberately safe in the direction that loses no solutions — and *unsafe* in the
    other. A consumer using it to decide that something IS the case (recognition, admission) inherits false
    positives and must guard them itself; that is the opposite safety from the one this is built for."""
    return _effects(g, name, include_mocks=True)


def _effects(g: Graph, name: str, *, include_mocks: bool) -> tuple:
    params, program = fn.load(g, name)

    # ⭐ What each register currently DENOTES, as a role — see `establishes` for the three forms. Reported
    # by `../pystrider`, which uses `establishes` for *recognition* rather than for ranking: first a pattern
    # authored as `NEW R(it)` then `LINK R(it) …` came back as effects with no subject at all — "orphan
    # facts that no longer claim to describe one node" — and then, once minting was fixed, a function that
    # navigated with `GET` before writing came back the same way.
    roles: dict = {}

    def role(operand):
        """The subject an operand names: a parameter, or whatever a register was last made to denote."""
        if isinstance(operand, F) and operand.name in params:
            return operand.name
        if isinstance(operand, R):
            return roles.get(operand.name)
        return None

    effects, unknown = set(), set()
    for ins in program:
        if isinstance(ins, str):
            continue                                        # a label, not an instruction
        a = ins.args
        arg = a[1] if len(a) > 1 else None

        if ins.op in isa.WRITES_REGISTER:
            if not (a and isinstance(a[0], R)):
                unknown.add(None)                           # malformed for this opcode: say nothing
                continue
            # Derive the NEW role before clearing the old one — `GET R(x) R(x) "l"` reads then overwrites.
            fresh = None
            if ins.op == "NEW":
                # ⭐ Bringing something into existence is an effect too — the one a goal like "some file
                # exists" is looking for, and the one a type signature cannot express.
                if len(a) > 1 and isinstance(a[1], str):
                    fresh = "$" + a[0].name
                    effects.add(("mint", a[1], fresh, None))
                else:
                    unknown.add(None)
            elif ins.op == "GET" and len(a) > 2 and isinstance(a[2], str):
                base = role(a[1])
                fresh = None if base is None else f"{base}.{a[2]}"
            elif ins.op == "GET_AT" and len(a) > 3 and isinstance(a[2], str) and isinstance(a[3], int):
                base = role(a[1])
                fresh = None if base is None else f"{base}.{a[2]}[{a[3]}]"
            elif ins.op in ("INVOKE", "DISPATCH"):
                unknown.add(None)                           # the effect happens somewhere else
            roles.pop(a[0].name, None)
            if fresh is not None:
                roles[a[0].name] = fresh
            continue

        if ins.op in ("LINK", "LINK_AT", "UNLINK"):
            if isinstance(arg, str):
                obj = a[-1] if ins.op != "UNLINK" else None
                effects.add(("link", arg, role(a[0]), role(obj) if obj is not None else None))
            else:
                unknown.add(role(a[0]))                     # a computed label, on a subject we can name
        elif ins.op == "SET":
            if isinstance(arg, str):
                effects.add(("attr", arg, role(a[0]), None))
            else:
                unknown.add(role(a[0]))
        elif ins.op == "CALL":
            unknown.add(None)                               # a local jump: the body runs out of order

    if include_mocks:
        for outcome in fn.mocks_of(g, name):                # depth 1: a mock has no mocks of its own
            more, more_unknown = _effects(g, outcome, include_mocks=False)
            effects |= more
            unknown |= more_unknown
    return frozenset(effects), frozenset(unknown)


def role_node(g: Graph, bound: dict, role: str | None):
    """The node a role from `establishes` names, given `{param: node}` — `None` if it names none.

    ⭐ **The path is resolved HERE, against the world, not statically.** `establishes` can say that a write
    lands on `c`'s `right` without knowing which node that is; only a caller with bindings in hand can turn
    that into an individual and ask whether it is the one a constraint is about. Static provenance plus
    dynamic resolution is what restores the exact-match band for a navigating operator.

    A `$` role names something minted inside the callee, which no binding can identify, so it resolves to
    `None` — the same answer it gave when it could not be resolved at all.

    ⚠ The path grammar itself now lives in `path.py` and is shared with the type and goal surfaces. It used
    to be a private regex here, which is why nothing else on the surface could refer past one hop. What is
    left here is the only part that is genuinely this module's: **the base names a PARAMETER**, not
    something in the graph, so only a caller holding bindings can start the walk."""
    if role is None or role.startswith("$"):
        return None
    try:
        base, rest = P.split_base(role)
    except P.BadPath:
        return None
    node = bound.get(base)
    return node if rest is None else P.node_at(g, node, rest)


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
            # ⭐ A role may be a PATH (`c.right`), so it is resolved against the world rather than looked
            # up. Measured on `../pystrider`'s repair operator, whose whole purpose is to change part of
            # its argument: without this it wrote to a register, established nothing anyone could name, and
            # the guidance had nothing to rank with (5 imagined states against 6 unguided).
            here = role_node(g, bound, sp)
            if here is not None and here == subject and \
                    (obj is None or role_node(g, bound, op) == obj):
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
           max_steps: int = 60, max_depth: int = 6, rank=None, guided: bool = True, allow=None,
           trace=None, decide=None) -> dict:
    """Search for a state satisfying `goal`, imagining every step. Returns a report.

    Everything the system considers is recorded on the thread as it happens, so *how* it got there is
    inspectable afterwards rather than reconstructible only by re-running it. On success the report carries
    the winning frame and the **plan**, which is the frame path — already replayable by `execute`.

    `rank` overrides `relevance` — the hook where a better judgement (a learned policy, a language model
    reading `function.catalogue`) plugs in, and the same shape `selection.score` already uses for the same
    reason. Passing a constant turns this back into blind search, which is how the guidance is measured.

    **⭐ ON FAILURE THE REPORT HANDS BACK THE `workbench`, and it is there SO THE SEARCH CAN BE
    INTERROGATED.** Forward chaining used to leave its diagnosis lying in a saturated graph; here every
    imagined state was on a workbench and the world afterwards looks untouched, so a reader who stops at
    `how` (`None` on failure) concludes the failure path says nothing. It is not so — `unmet` and `why` are
    on the report, and `W.frames`, `W.mappings`, `W.resolve` and `W.image_of` reach every state that was
    explored. `../pystrider` turned "no plan found" into a refusal naming its cause in about fifteen lines
    of that. ⚠ For a single-constraint goal `unmet` merely restates the goal, so it says *what* was not
    achieved and never *why*; the why is domain knowledge, and it lives in the frames or nowhere.

    **⭐ `decide` is the deliberation seam** (`deliberation.md`). Called once per imagined step, *before*
    the chosen proposal is imagined, with the situation as it already stands. Returning `None` — or
    `EXPAND` — means "nothing to say", so the loop's disposition is unchanged and **the default is to keep
    planning**; a decision has to speak up to alter it. Returns `verb` or `(verb, reason)`.

    ⚠ This is an **engine seam, not an extension point.** The decider that eventually lives here reads
    *decision rules as data* and is shipped with the engine; it is not somewhere a domain author writes
    Python. It is a parameter for the same reason `rank` is — so the behaviour can be substituted in a
    check and so the loop does not have to know what decides.

    ⚠ Only `COMMIT`, `SENSE` and `REFUSE` can be honoured today, and of those `SENSE` needs ignorance and
    `DECOMPOSE` needs goal hierarchy — both raise `Undecidable` naming what is missing, rather than being
    quietly ignored. A decision that silently does nothing is the failure mode this project keeps catching.

    **⚠ The authoring rule that follows, which is not obvious and is easy to get wrong: an operation that
    wants to explain itself must record its reason WHERE THE FRAMES ARE.** A microfunction that quietly does
    nothing when a precondition fails is unexplainable after a failed search — it leaves no trace in any
    imagined state. One that writes something (`unsupported_confirmation_step`) is diagnosable, because the
    frame that tried it still holds the mark. Silence costs nothing at planning time and everything
    afterwards."""
    # ⭐ Refuse the provably impossible before spending anything on it. `conflict.unsatisfiable` reports
    # only decidable contradictions, so this can never reject a goal that was actually reachable.
    from . import conflict as C
    impossible = C.unsatisfiable(g, goal)
    if impossible:
        T.attend(g, thread, goal, why="the goal contradicts itself", note="; ".join(impossible))
        return {"found": False, "workbench": None, "steps": 0, "goal": goal,
                "contradictory": impossible, "refused": (), "blocked_by": (),
                "why": "the goal cannot be met: " + "; ".join(impossible)}

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

    # ⭐ THE TRACE HOOK — an OBSERVER, never a participant. It is handed a dict per event and its return
    # value is discarded, so a watcher cannot steer the search: turning tracing on must not change what is
    # found. That is why this is a callback taking finished facts rather than, say, a filter or a ranker —
    # those already exist (`allow`, `rank`) and are honest about influencing the outcome.
    #
    # ⚠ Node ids are useless to a reader, so every event carries LABELS. The thread and the workbench keep
    # the identities; a trace is for watching, and the two must not be confused — anything reconstructing
    # state from these strings is reconstructing it from a rendering.
    # ⚠ Aliased, and NOT optional: `trace` is already the name of the action-prefix threaded through
    # `offer` and unpacked from the frontier, so the callback was being clobbered by a tuple mid-search.
    # Renaming the parameter would change the public surface; aliasing here fixes it where it belongs.
    watch = trace

    def emit(kind, **fields):
        watch(dict(kind=kind, step=steps, **fields))

    def label(n):
        return g.attr(n, "label") or g.kind(n) or n

    def shown(bindings):
        return {p: label(W.resolve(g, m) or W.image_of(g, m)) for p, m in bindings.items()}

    frontier: list = []
    seen, steps, refused = {visited_key(root, ())}, 0, []

    # ⚠ After `steps` exists: `emit` closes over it, so calling this any earlier is an UnboundLocalError.
    if watch:
        emit("goal", goal=g.attr(goal, "label"),
             wants=[G.describe_constraint(g, c) for c in G.constraints(g, goal)],
             open=[G.describe_constraint(g, c) for c in still_open(root)])

    def offer(frame: str, depth: int, trace: tuple) -> None:
        open_now = still_open(frame)
        for name, bindings in proposals(g, frame, allow=allow):
            # ⭐ CONSTRAINTS ON THE PLAN, checked BEFORE imagining — so a forbidden action costs nothing.
            # ⚠ This FILTERS where `relevance` only RANKS, and the difference is principled: relevance is
            # a guess about what will help, so filtering on it could lose a solution (Sussman's anomaly
            # needs a low-scoring move). A safety breach is a proof — no continuation of a plan that used
            # a forbidden action makes it unused — so pruning is sound. Rank a guess; prune a proof.
            ahead = trace + ((name, frozenset(W.resolve(g, m) or W.image_of(g, m)
                                              for m in bindings.values())),)
            hit = G.breached(g, goal, ahead)
            if hit:
                reasons = tuple(G.describe_constraint(g, c) for c in hit)
                refused.append((name, reasons))
                # ⭐ Worth emitting: this is the machine declining to even IMAGINE something, which is
                # invisible in any after-the-fact record precisely because nothing happened.
                if watch:
                    emit("refuse", action=name, on=shown(bindings),
                         because=list(reasons), depth=depth)
                continue
            if not guided:
                frontier.append(((0, 0, depth), frame, depth, name, bindings, len(open_now), ahead))
                continue
            rank_here = score(g, name, bindings, open_now)
            expected = len(open_now) - (1 if rank_here >= 4 else 0)
            if watch:
                emit("consider", action=name, on=shown(bindings), band=rank_here,
                     open=len(open_now), depth=depth)
            frontier.append(((expected, -rank_here, depth), frame, depth,
                             name, bindings, len(open_now), ahead))

    offer(root, 0, ())
    while frontier and steps < max_steps:
        frontier.sort(key=lambda item: item[0])
        _key, frame, depth, name, bindings, open_count, trace = frontier.pop(0)

        # ⭐ THE DECISION POINT. Everything above chose the *best* proposal; this asks whether imagining it
        # is what we should be doing at all. Returning `None` means "nothing to say", which is why the
        # default behaviour is to keep planning — the loop's disposition is unchanged and a rule has to
        # speak up to alter it.
        #
        # ⚠ UNLIKE `trace`, THIS IS A PARTICIPANT, so it is handed the real thing. `trace` gets labels
        # because a watcher must not be able to steer and a rendering is all it needs; a decision is made
        # *on* structure, so giving it renderings would force it to reconstruct state from strings — the
        # exact confusion `trace`'s own comment warns against, arrived at from the other side.
        #
        # ⚠ Built from what is ALREADY computed. This runs once per imagined step — hundreds of times in a
        # normal search — so anything costly here inverts the cost of what it exists to save.
        # `open_count` is carried on the frontier item precisely so nothing is recomputed. `deliberation.md`
        # §4 is the standing rule: methods per goal, stop-rules per step, guidelines per proposal.
        if decide is not None:
            verdict = decide({"goal": goal, "frame": frame, "depth": depth, "function": name,
                              "bindings": bindings, "open": open_count, "trace": trace,
                              "steps": steps, "frontier": len(frontier), "workbench": wb,
                              "thread": thread, "subject": subject})
            if verdict is not None and verdict != EXPAND:
                verb, why_stop = verdict if isinstance(verdict, tuple) else (verdict, None)
                if verb in _UNBUILT:
                    raise Undecidable(f"{verb!r} needs {_UNBUILT[verb]}; see deliberation.md")
                if verb not in _STOPS:
                    raise Undecidable(f"{verb!r} is not one of {VERBS}")
                # Recorded ONLY when a decision actually fires, which is what keeps the default path
                # byte-identical to the behaviour that existed before this seam.
                T.attend(g, thread, goal, why=f"decided to {verb}",
                         note=why_stop or f"before imagining {name}")
                if watch:
                    emit(verb, action=name, on=shown(bindings), depth=depth, because=why_stop)
                return {"found": False, "workbench": wb, "steps": steps, "goal": goal,
                        "stopped": verb, "frame": frame, "plan": X.path_to(g, wb, frame),
                        "refused": tuple(refused),
                        "blocked_by": tuple(sorted({r for _n, rs in refused for r in rs})),
                        "why": why_stop or f"stopped by decision: {verb}"}

        steps += 1

        nxt, _tr = W.step(g, wb, frame, name, bindings)
        # ⚠ Record the REAL node the imagined one stands for, falling back to the copy only for something
        # that does not exist yet. Recording the copy was more literal and less truthful: an application
        # says *which function was applied to which subject*, and the subject is the block — the copy is
        # only how we imagined it. It also made the record useless to any reflective reader, because two
        # goals open two workbenches, so their entries could never refer to the same thing.
        T.applied(g, thread, name,
                  {p: (W.resolve(g, m) or W.image_of(g, m)) for p, m in bindings.items()},
                  why=f"depth {depth + 1}, {open_count} constraint(s) open", for_goal=goal)

        nview, nunder = asked_of(nxt)
        if watch:
            emit("imagine", action=name, on=shown(bindings), depth=depth + 1,
                 open=[G.describe_constraint(g, c)
                       for c in G.unmet(g, goal, view=nview, under=nunder)])
        # ⚠ Both halves, and liveness only here: the world must be right AND the plan must have done
        # everything it was required to. A plan that reaches the state without its mandated step is not
        # finished — but it was never in violation on the way, which is why this is not a pruning test.
        if G.satisfied(g, goal, view=nview, under=nunder) and not G.outstanding(g, goal, trace):
            done = _done(g, goal, thread, wb, nxt, opened, "found", steps, tuple(refused))
            if watch:
                emit("found", imagined=steps, length=done["length"],
                     plan=[(f, {p: label(n) for p, n in b.items()})
                           for f, b in plan_bindings(g, done["plan"])])
            return done

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
    if watch:
        emit("exhausted", imagined=steps, unmet=still_open, blocked_by=blocked)
    return {"found": False, "workbench": wb, "steps": steps, "goal": goal,
            "unmet": still_open, "refused": tuple(refused), "blocked_by": tuple(blocked),
            "why": f"no state meeting [{still_open}] within depth {max_depth} after {steps} "
                   f"imagined steps" + (f"; {len(refused)} action(s) ruled out by [{', '.join(blocked)}]"
                                        if blocked else "")}


def plan_bindings(g: Graph, plan: tuple) -> tuple:
    """A plan (a path of FRAMES) read back as `(function, {param: real node})` per step.

    ⚠ Distinct from `plan_steps`, which takes a *result dict* and returns bare function names. Naming this
    `plan_steps` too silently shadowed that one — which `../pystrider` calls — and every consumer of it
    began receiving a frame path it could not read. Two readers of a plan at two levels of detail is fine;
    two of them sharing a name is not.

    ⚠ The first frame is the starting world, reached by nothing, so it contributes no step. Bindings point
    at *mappings* rather than raw nodes — that indirection is what makes a plan replayable at all — so each
    resolves back to the node it stands for, which is what any reader of a plan is actually asking about.

    Lives here rather than in `query.py` because `driver` cannot import `query` (that way lies a cycle) and
    both need it. One implementation, so a plan reads the same whether it came from a question or a goal."""
    out = []
    for frame in plan[1:]:
        tr = g.target(frame, "via")
        if tr is None:
            continue
        bound = {}
        for b in g.targets(tr, "arg"):
            m = g.target(b, "mapping")
            bound[g.attr(b, "param")] = (W.resolve(g, m) or W.image_of(g, m)) if m else None
        out.append((g.attr(tr, "function"), bound))
    return tuple(out)


def _done(g: Graph, goal, thread, wb, frame, opened, how, imagined, refused) -> dict:
    """Close the goal, and tie the moment that closed it back to the moment it was taken on."""
    subject = g.target(wb, "subject")
    under = W.image_of(g, W.mapping_for(g, frame, subject))
    found = G.witness(g, goal, view=view_in(g, frame), under=under)
    # ⚠ PLANNED, not closed. The goal is met in an imagined frame; the world is untouched. Closing it here
    # would report success for something that has not happened.
    G.record_plan(g, goal, seen_in=frame, witness=found)

    plan = X.path_to(g, wb, frame)
    closing = T.attend(g, thread, goal, why=f"goal met ({how})",
                       note=f"plan is {len(plan) - 1} step(s)")
    T.connect(g, closing, opened, "achieves")
    return {"found": True, "workbench": wb, "frame": frame, "goal": goal, "witness": found,
            "plan": plan, "length": len(plan) - 1, "steps": imagined, "how": how,
            "refused": refused, "blocked_by": tuple(sorted({r for _n, rs in refused for r in rs}))}


def _record_execution(g: Graph, thread: str, goal: str, plan: dict, report: dict) -> None:
    """Put what really ran on the thread, marked `done`.

    ⚠ Until this existed the thread held only *planning* — every proposal considered, including abandoned
    branches — and nothing about what actually happened. Anything reasoning over consequences was therefore
    reading the search rather than the actions, which is how `conflict.interference` first came to report
    two goals disagreeing over an idea neither of them acted on."""
    for frame, name in zip(plan["plan"][1:], report["ran"]):
        tr = g.target(frame, "via")
        if tr is None:
            continue
        args = {}
        for b in g.targets(tr, "arg"):
            m = g.target(b, "mapping")
            args[g.attr(b, "param")] = W.resolve(g, m) or W.image_of(g, m)
        T.applied(g, thread, name, args, why="carried out for real", for_goal=goal, done=True)


def carry_out(g: Graph, goal: str, thread: str, subject: str, *,
              attempts: int = 3, **kw) -> dict:
    """⭐⭐ PLAN, ACT, CHECK, REPLAN — the loop closed. Returns a report of every attempt.

    `pursue` finds a plan in imagination; this is what actually does it, notices when reality disagrees, and
    goes round again from the world as it really is.

    **⚠ Replanning has to come back HERE, not to `plan.py`.** `execution.replan` chains backwards over
    return types and knows nothing about a goal's constraints — asked to recover a diverged
    "some file must exist", it answered *"listing: already satisfied"*: true, and useless. Re-pursuing the
    **goal** is the only recovery that can mean anything, and it needs no new state because `pursue` opens a
    fresh workbench on the current real subject. Replanning is just going round the loop again.

    **⚠ A contingency is still tried first**, for the reason `execution.recover` gives: an explored sibling
    is already verified against this world, a fresh plan is not. It rarely applies to a plan *this* function
    produced, because `pursue` does not fork on mock outcomes — it takes the preferred one. That is a real
    limitation, stated rather than hidden, and the reason the loop leans on replanning.

    **The goal is closed only by reality.** `pursue` records that a plan was *found*; nothing but a
    completed execution closes the goal."""
    history: list = []
    for attempt in range(attempts):
        plan = pursue(g, goal, thread, subject, **kw)
        if not plan["found"]:
            history.append({"attempt": attempt, "planned": False, "why": plan["why"]})
            break

        T.attend(g, thread, goal, why=f"attempt {attempt + 1}: carrying out the plan",
                 note=" then ".join(plan_steps(g, plan)) or "(nothing)")
        report = X.execute(g, plan["workbench"], plan["frame"])
        _record_execution(g, thread, goal, plan, report)
        step = {"attempt": attempt, "planned": True, "steps": plan_steps(g, plan),
                "ran": report["ran"], "completed": report["completed"]}

        if not report["completed"]:
            rec = X.recover(g, report)          # an explored sibling, if there is one
            if rec["kind"] == "contingency" and rec["result"]["completed"]:
                report, step["recovered"] = rec["result"], "contingency"
                step["completed"], step["ran"] = True, report["ran"]
            else:
                step["diverged"] = X.report(g, report)
        history.append(step)

        if report["completed"] and G.satisfied(g, goal, under=subject):
            found = G.witness(g, goal, under=subject)
            G.close_goal(g, goal, found)
            T.attend(g, thread, goal, why="done for real", note=G.describe(g, goal))
            return {"done": True, "attempts": tuple(history), "witness": found, "tries": attempt + 1}

    T.attend(g, thread, goal, why="gave up", note=f"after {len(history)} attempt(s)")
    return {"done": False, "attempts": tuple(history), "tries": len(history),
            "why": f"{len(history)} attempt(s) did not reach ["
                   + "; ".join(G.describe_constraint(g, c)
                               for c in G.unmet(g, goal, under=subject)) + "]"}


def follow(g: Graph, goal: str, thread: str, subject: str, **kw) -> dict:
    """Carry out a **decomposed** goal by working its subgoals in `then` order.

    ⭐ This is the one thing probing `goal_machinery.md` §8 found genuinely missing. Its claim — *"a
    procedure is this shape plus one sequencing edge"* — held structurally: two ordered subgoals ran through
    `carry_out` unchanged and reality came out right. What was absent was not structure but **drive**;
    nothing walked the order. This is that walk, and it is deliberately thin because the probe showed
    everything underneath already worked.

    **⭐⭐ FORCE decides what happens when a step fails, and it is the whole distinction between a method
    and a procedure** (`deliberation.md` §3):

    * **`ADVISORY`** (a method) — the decomposition was a *suggestion about how*. If it does not work out,
      fall back to searching for the parent goal directly. Incompleteness is fine; the author was helping.
    * **`MANDATORY`** (a procedure) — the decomposition was *the sanctioned way*. Falling back would be
      improvising, so this **refuses** instead. ⚠ For a procedure, *"could not do it"* is a better answer
      than *"did it another way"*, and that inverts every other reflex in this module — `carry_out`
      replans, `recover` reaches for contingencies. The reflex is suppressed here on purpose.

    ⚠ **A refusal is not a failure to find a plan**, and they must not be reported alike: one says the
    world would not permit it, the other says we were not permitted to try. `REFUSE` carries the step that
    stopped it and the reason, which is what an audit of a regulated run actually needs.

    ⚠ **Advisory fallback cannot resurrect a MANDATORY parent.** Force is read from the parent whose
    decomposition this is, never from the step that failed — a mandatory procedure containing an advisory
    sub-method must not become improvisable because the failure happened one level down."""
    steps = G.sequence(g, goal)
    if not steps:
        # Not decomposed at all — the vacuity trap `goal_machinery.md` §8 records. Refusing to treat this
        # as a trivially-completed procedure is the whole reason `decomposed` exists.
        return {"done": False, "goal": goal, "followed": (), "why": "nothing was raised under this goal",
                "undecomposed": True}

    force = G.force_of(g, goal)
    T.attend(g, thread, goal, why=f"following a {force} decomposition",
             note=" then ".join(g.attr(s, "label") or s for s in steps))

    outcomes = []
    for step in steps:
        report = carry_out(g, step, thread, subject, **kw)
        outcomes.append((step, report["done"]))
        if report["done"]:
            continue
        if force == G.MANDATORY:
            T.attend(g, thread, step, why="refusing to improvise",
                     note="the sanctioned step did not succeed and no other route is permitted")
            return {"done": False, "goal": goal, "followed": tuple(outcomes), "stopped": REFUSE,
                    "at": step, "force": force,
                    "why": f"the procedure's step {g.attr(step, 'label') or step!r} did not succeed, and a "
                           f"mandatory decomposition may not be worked around"}
        T.attend(g, thread, goal, why="the method did not work out",
                 note="falling back to searching for the goal itself")
        fallback = carry_out(g, goal, thread, subject, **kw)
        return {**fallback, "goal": goal, "followed": tuple(outcomes), "fell_back": True, "at": step,
                "force": force}

    return {"done": G.satisfied(g, goal, under=subject), "goal": goal, "followed": tuple(outcomes),
            "force": force, "all_steps_done": True}


def attempt(g: Graph, goal: str, thread: str, subject: str, **kw) -> dict:
    """**The goal-level decision point: decompose, or search?** The top of the loop for anything with
    authored methods.

    ⚠ **This is deliberately NOT inside `pursue`'s search loop**, and the frequency is the reason
    (`deliberation.md` §4). A method is consulted **once per goal** — few, so it may be expensive — while
    the per-step `decide` hook runs hundreds of times and must stay structural. Putting method matching in
    the inner loop would invert the cost of the thing it exists to save, which is the mistake `HANDOFF.md`
    §5m records paying for once already.

    **⭐ Precedence is declaration order**, and the first applicable method wins. No weights, nothing to
    tune — the same free ordering `mock` and `guideline` already use.

    **⚠ Falling back is what keeps AUTHORITY safe.** A method prunes by replacing enumeration, so a
    non-covering one could make a reachable goal unreachable. When no method matches, this searches exactly
    as before; when an `ADVISORY` one matches and fails, `follow` searches the parent goal directly. Only
    `MANDATORY` may end in a refusal, which is the point of declaring it."""
    from . import method as M
    hits = M.applicable(g, goal, under=subject)
    if not hits:
        return carry_out(g, goal, thread, subject, **kw)

    m, c = hits[0]
    raised = M.decompose(g, m, goal, c)
    T.attend(g, thread, goal, why=f"decomposing by method {g.attr(m, 'name') or m}",
             note=g.attr(m, "because") or f"{len(raised)} step(s)")
    return {**follow(g, goal, thread, subject, **kw), "method": m, "raised": raised}


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


__all__ = ["proposals", "state_of", "establishes", "role_node", "relevance", "view_in",
           "pursue", "carry_out", "plan_steps", "plan_bindings", "describe"]

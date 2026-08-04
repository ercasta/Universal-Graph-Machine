"""Driver — the outer loop. Pursue a goal by imagining, and let the record of what worked be the plan.

`plan.py` chains, `workbench.py` imagines, `execution.py` replays and `selection.py` ranks; this
is what invokes them.

The goal here is to produce a plan rather than to act — a goal about planning, which is an
ordinary goal because a plan is an ordinary node. Nothing dispatches and nothing touches the
world: the whole search happens on a workbench, and `dispatch.service` refusing an imagined
target makes that guaranteed rather than merely intended.

The plan is not built, it is found. `execution.path_to(wb, winning_frame)` already is one. The
frame tree records every state imagined and every transformation that reached it, so the path to
the frame that satisfies the goal is replayable, and `execution.execute` runs it unchanged.

Forward search here, where `plan.py` chains backwards, because the two answer different
questions. Backward chaining over return types cannot express applying the same operator
repeatedly: a function has one declared return type, so "stack a block, then stack another" is
not a chain of distinct casts, and repetition comes from the loop.

* `plan.py` — what sequence of casts reaches this type? Cheap, no imagining, right when the
  operators form a pipeline of distinct stages.
* here — what do I get if I try this, and then this? Costly, a frame per step, right when the
  same operator applies repeatedly and the interesting question is the resulting state.

Binding search lives here deliberately. `selection.candidates` is restricted to single-parameter
functions because a multi-parameter function needs a binding proposed, and inventing bindings is
search, which should not hide inside candidate generation.

Effects are read off a function's stored body rather than declared, so they cannot fall out of
date with it, and they carry their roles — `stack` links its parameter `b` onto its parameter
`onto`. Relevance only ever orders; a prohibition or budget prunes.

Honest scope: best-first with a visited set, first solution wins, bounded by `max_steps`. No cost
model and no backtracking across a committed subgoal. The frame tree makes this expensive, a full
copy per imagined step, which is a known and measured limit rather than a surprise.

See `docs/planning.md`.
"""
from __future__ import annotations

from itertools import product
from typing import NamedTuple

from . import access
from . import dispatch as DP
from . import execution as X
from . import function as fn
from . import goal as G
from . import native as N
from . import isa
from . import path as P
from . import search as S
from . import thread as T
from . import types as TY
from . import workbench as W
from .graph import Graph
from .isa import F, R
from . import types as TY
from .types import is_a


# --- deliberation: the verbs a decision can return ------------------------------------------------
#
# The seam `pursue` Never had. It was a closed loop — nothing could intervene between two imagined
# steps — so "what should I do next?" was not an expressible question, only a `while` condition. That made
# deliberation the thing this system computes *with* and cannot compute *about*: the same defect attention
# had before `thread.py` and the goal had before `goal.py`, in its third place. See `docs/deliberation.md`.
#
# The set is closed on purpose. It is the vocabulary everything authored has to speak, and a verb that
# means "something else" would make a decision unreadable to the reflective functions that are the point.
EXPAND = "expand"            # imagine the best-ranked proposal — the default, and today's whole behaviour
DECOMPOSE = "decompose"      # post subgoals instead of enumerating actions   (needs goal hierarchy)
COMMIT = "commit"            # stop planning; what we have is what we will do
SENSE = "sense"              # stop planning and act in order to learn        (needs ignorance)
REFUSE = "refuse"            # no sanctioned way to proceed; do not improvise

#: Closed in Python **on purpose**, and with no escape into the web — recorded here because
#: `docs/audit.md` (F6) found this class failing the executor-per-member test by its own admission, and
#: an undeclared position is what that page counts as the defect rather than the closure itself.
#:
#: A search move is not something a domain authors. It is what the engine does *while* deciding, one
#: level below the criteria and methods a domain writes, and a new one is a change to how deliberation
#: works rather than to what this domain knows. That is the opposite of `precedence.STAGES`, which has
#: `run <fn>` precisely because ranking by seniority or recency is a domain's business.
#:
#: The honest half: `_UNBUILT` below names members whose machinery does not exist. Returning one raises
#: rather than being ignored, so the gap is loud — but it does mean this set is aspirational at the
#: edges, and a reader should not take membership here as proof that something works.
VERBS = (EXPAND, DECOMPOSE, COMMIT, SENSE, REFUSE)
_STOPS = (COMMIT, SENSE, REFUSE)

#: Verbs whose machinery does not exist yet. Returning one raises rather than being ignored — a decision
#: silently doing nothing is exactly the class of failure this project keeps catching.
_UNBUILT = {DECOMPOSE: "per-STEP decomposition; a method applies per GOAL, via driver.attempt "
                       "(deliberation.md §4 — methods are consulted once per goal, not per step)"}


class Undecidable(Exception):
    """A decision named a verb whose machinery is not built. Loud, and naming what is missing."""


class Call(NamedTuple):
    """A decision that names what to do, not merely whether to keep going.

    The five verbs say something about the search's *disposition*; this says which action to imagine next,
    with its arguments. That is what `docs/deliberation.md` needs and what the seam could not express:
    `decide` was consulted *after* `take_best` had already chosen, so a decision could veto but never
    substitute.

    `bindings` maps each parameter to a real node or a mapping in the current frame — either, because a
    criterion reasons about individuals (`stands_for`) and should not have to know what a workbench is.

    Naming a binding is the point. `selection.candidates` refuses multi-parameter functions on the
    grounds that *"inventing bindings is a different problem (search) that should not hide inside candidate
    generation"*. A `Call` is that job done by authored knowledge instead of by enumeration — which is the
    wall coming down deliberately (`docs/deliberation.md`, not by accident.

    It is still checked, and against the same requirements the enumeration applies. A decision may
    name a binding the search never proposed; it may not name an ill-typed one, one node in two roles, or
    a forbidden action. Rank a guess, prune a proof: a criterion is a guess and `goal.forbid_action` is
    a proof, so the proof wins and the attempt raises rather than being quietly downgraded."""
    function: str
    bindings: dict
    why: str | None = None
    #: Force. `False` — advisory: the enumeration this call suppresses is deferred, so being wrong
    #: costs imagined states. `True` — mandatory: the alternatives are not built at all, so a wrong
    #: call makes the goal unreachable rather than merely expensive. `docs/deliberation.md`'s finding, in a
    #: third place: *force is about failure* — a method falls back to search, a procedure must refuse.
    final: bool = False


def proposals(g: Graph, frame: str, *, allow=None) -> tuple:
    """Every `(function, {param: mapping})` that could be applied in this frame. See `enumerate_frame`."""
    return enumerate_frame(g, frame, allow=allow)[0]


def stands_for(g: Graph, mapping: str):
    """The node a mapping names, as everything that reasons about individuals must see it.

    A mapping has two nodes: the workbench `image` that an imagined step reads and writes, and the
    `original` it stands for in the real world. A constraint, a want, a trace entry and a thread record all
    talk about the *original* — so anything comparing them has to agree on which one it means.

    This exists because they disagreed once. `wants_that_unblock` keyed its requirements by the image
    while `unlocks` resolved to the original, so the two never matched and the whole component scored zero
    on every proposal — a silent no-op that looked exactly like "the idea does not help". The expression was
    already written out seven times in this module; it is written once now, which is the difference between
    a convention and a guarantee."""
    return W.resolve(g, mapping) or W.image_of(g, mapping)


def enumerate_frame(g: Graph, frame: str, *, allow=None) -> tuple:
    """`(proposals, blocked)` — what can be applied here, and why the rest cannot.

    `blocked` is the half that used to be computed and thrown away. Testing a candidate against a
    parameter type calls `types.fails`, which returns `{label: (expected, actual)}` — *precisely which
    requirement failed* — and this loop kept only its truthiness. So "this action is one requirement away
    from being possible" was already being computed on every candidate in every enumeration, and discarded.

    `blocked` maps `function -> {(requirement label, node)}`: for each function with no valid binding
    here, the requirements that stopped each candidate. `_offer` turns that into the search's only notion of
    *making progress towards being able to act*, which nothing else in this module has.

    Deliberately in the same pass. Computing it separately would re-run `fails` over every mapping and
    every parameter — doubling the dominant cost of enumeration to recover information the first pass
    already had. records paying for exactly that mistake once.

`blocked` is only the names. What each of them was missing is recomputed by
    `wants_that_unblock`, for the few that matter — see there for why that is cheaper than keeping it.

    The cartesian product of type-valid bindings, minus the ones binding one node to two parameters —
    which is not a heuristic but a correctness rule for operators like `stack(b, onto)`, where the type
    system cannot say `b ≠ onto`. `types.py` validates one argument at one call site by design, so a
    relation *between* parameters has no declared form and has to be enforced here or in the body.

    `allow` is a predicate on the function name, and it excludes rather than orders. That is only
    legitimate for a proof, never for a guess — the same line `relevance` sits on the other side of.
    `query.py` uses it to bar any function that could dispatch from being used as a derivation, which is a
    proof about the stored body, not an opinion about what will help."""
    here = W.visible(g, frame)
    view = view_in(g, frame)
    out, blocked = [], []
    for name in fn.names(g):
        # A mock is NOT an action. It is an assumption about how a real call turns out, so proposing one
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
            # Gather the type's demands once per parameter, not once per candidate. Resolving the name
            # and walking its `base` chain depends only on the type, and redoing it per candidate was the
            # dominant remaining cost of enumeration — 1,025 rebuilds per enumeration in a world with 200
            # nodes that fit nothing. `requirements` stores nothing, so this hoists without a cache.
            reqs = TY.requirements(g, ptypes[p])
            if reqs is None:
                break                          # undeclared parameter type — no candidate can satisfy it
            fits = []
            for m in here:
                # Tested against the image (the world as imagined here), keyed by what it stands for
                # (the individual a constraint talks about). Those are different nodes and conflating
                # them is what made this component silently score zero.
                if not TY.fails(g, W.image_of(g, m), reqs, view=view):
                    fits.append(m)
            if not fits:
                per_param = None
                break
            per_param.append(fits)
        if per_param is None or len(per_param) != len(params):
            blocked.append(name)
            continue
        for combo in product(*per_param):
            binding = dict(zip(params, combo))
            # **The declared condition, where a hardcoded rule used to be.** This loop skipped any combo
            # binding one node to two parameters, and the comment beside it said why: the type system
            # cannot say `b ≠ onto`, so a relation *between* parameters had no declared form and had to
            # be enforced here or in the body. It has one now — `fn.guard` — and `stack` says it itself.
            #
            # It was never universally right, either: `connect(a, b)` making a self-loop is a perfectly
            # ordinary thing for a domain to want, so what looked like a correctness rule was a domain
            # assumption living in the planner. Authored, it is the domain's again.
            if not fn.applies(g, name, {p: stands_for(g, m) for p, m in binding.items()}, frame=frame):
                continue
            out.append((name, binding))
    return tuple(out), blocked


def view_in(g: Graph, frame: str):
    """How a goal's constraints are asked of an *imagined* world.

    A constraint names real individuals ("a on b"). Inside a frame those individuals are represented by
    versions, so checking means translating each named node into the version in force here. `goal.py`
    takes this as a `view` rather than learning about workbenches — the layering runs one way.

    A `W.View` rather than a closure, because a traversal inside a frame needs the way back as well:
    an edge names an identity, so following one and then reading it means going down to the version and
    up again to the identity. A closure could only answer half of that, and the half it could not answer
    was being written out by hand at each of its callers."""
    return W.View(g, frame)


class _Unreadable:
    """The value of an attribute write the body computes rather than states.

    A singleton with a name, not `None` and not a bare `object()`. `None` is an ordinary attribute value,
    so it cannot double as *"we could not read this"* without recreating the UNKNOWN-versus-NO conflation
    `query.py` exists to keep apart; and a bare sentinel prints as an address, which makes every check
    output that contains one unreadable."""
    __slots__ = ()

    def __repr__(self) -> str:
        return "UNREADABLE"


UNREADABLE = _Unreadable()


def establishes(g: Graph, name: str) -> tuple:
    """What this function could make true, read off its stored body. Returns `(effects, unknown)`.

    This is homoiconicity earning its keep rather than being asserted. Nothing declares effects — the
    north star deliberately moved away from operators carrying declarative effect descriptions — but a
    function *is* graph data, so we can look at what its instructions write and ask "could this establish an
    `on` edge?". No new representation, no authoring burden, and it cannot fall out of date with the body
    because it *is* the body.

    Effects carry their ROLES, and that turned out to matter more than the label. An effect is
    `(kind, label, subject_role, fourth)`, and the fourth slot is tagged by the first: for a `link` it
    is the *object role*, for an `attr` it is the value written (or `UNREADABLE` when the instruction
    computes it). `stack` does not merely "write an `on` edge", it links
    *its parameter `b`* on *its parameter `onto`*. Without that, `stack(b=b, onto=a)` looks exactly as
    promising for the constraint "a on b" as `stack(b=a, onto=b)` does, because both involve the same two
    blocks — and the ranking degrades to little better than blind. Roles are read from the operands, so this
    costs nothing extra.

    A function's effects include its mocks', and that is what makes planning look at expectations
    rather than at type signatures. `scan_dir`'s own body is a `DISPATCH` and a `SET` — statically it
    establishes almost nothing, because everything interesting happens on the other side of a tool call. The
    knowledge that listing a directory *produces file nodes* is not in the signature and not in the body: it
    is in the mock, which is precisely the declared assumption about how the call turns out.

    So the effects of an operator are the union of what its body writes and what each of its assumed
    outcomes writes. That is the same thing `workbench.predicted_changes` derives at planning time, reached
    statically here — and it is what lets a goal of "some file exists" find `scan_dir` at all. Without it,
    an opaque tool call is maximally relevant to everything and informative about nothing.

    A role is a path, not just a parameter name, which is what lets this read a function that has to
    Navigate. Three forms, distinguishable by inspection and never confusable with each other:

    | role | means |
    |---|---|
    | `c` | the parameter `c` |
    | `c.right` | what the body reached by `GET`ting `c`'s `right` — `c.child[2]` for an indexed hop |
    | `$it` | a node this body minted, held in register `it` — a local subject with no caller-side identity |

    Without the middle form, `lower_threshold(c)` — `GET R(rhs) F(c) "right"` then `SET R(rhs) …` — reported
    no effect on anything, because the write landed on a register rather than a parameter. Reported by
    the first consumer, and the case is general: *read a part, write to that part* is what most operations on
    structured data look like, so the functions whose effects were invisible were exactly the ones that do
    real work on a structure. The provenance is derivable from the instruction list and costs nothing at
    runtime, since it is read statically off a body that is already stored.

    A path is only as good as the register's last assignment: anything else written into that register
    clears the role (`isa.WRITES_REGISTER` is the authority on what counts), and an `ATTR` clears it too,
    because a register holding an attribute *value* denotes no node at all.

    Conservative on purpose, and `unknown` now says what it is unsure about. If a label or key comes
    from a register, or the body calls out to another function, we cannot tell statically. `unknown` is a
    frozenset of the roles the unreadable instructions concern, with `None` meaning "somewhere we cannot
    name at all" (a call, a computed subject). Empty means the body was read completely, so `if unknown:`
    and `not unknown` read exactly as they did when this was a bool.

    That granularity is for consumers reading effects as a description rather than as a ranking hint:
    the first consumer abstains from recognising a node whenever anything was unreadable, and a whole-function
    flag darkened descriptions that were provably complete for their own subject — an unreadable write to
    `y` said nothing about `x`, but looked as though it might.

    The return value is an over-approximation by contract. It exists to order candidates and it never
    rules one out, so it is deliberately safe in the direction that loses no solutions — and *unsafe* in the
    other. A consumer using it to decide that something IS the case (recognition, admission) inherits false
    positives and must guard them itself; that is the opposite safety from the one this is built for."""
    return _effects(g, name, include_mocks=True)


def _denotes(ins, role):
    """What this instruction's destination register will denote afterwards, or `None` for "nothing we can
    name". Derived from the operands *before* the write lands — `GET R(x) R(x) "l"` reads then overwrites."""
    a = ins.args
    if ins.op == "NEW":
        return "$" + a[0].name if len(a) > 1 and isinstance(a[1], str) else None
    if ins.op == "GET" and len(a) > 2 and isinstance(a[2], str):
        base = role(a[1])
        return None if base is None else f"{base}.{a[2]}"
    if ins.op == "GET_AT" and len(a) > 3 and isinstance(a[2], str) and isinstance(a[3], int):
        base = role(a[1])
        return None if base is None else f"{base}.{a[2]}[{a[3]}]"
    return None


def _walk(g: Graph, name: str):
    """One pass over a stored body, yielding `(instruction, role)` — the single place that knows what a
    register denotes.

    What each register currently denotes, as a role — see `establishes` for the three forms. Reported
    by the first consumer, which uses `establishes` for *recognition* rather than for ranking: first a pattern
    authored as `NEW R(it)` then `LINK R(it) …` came back as effects with no subject at all — "orphan
    facts that no longer claim to describe one node" — and then, once minting was fixed, a function that
    navigated with `GET` before writing came back the same way.

    Factored out because there are now two static readers of a body — `_effects` (what it writes)
    and `_reads` (what it reads) — and they must agree exactly about which node `R(x)` stands for at each
    instruction. Two copies of this bookkeeping is the drift shape this codebase keeps recording, and one
    that silently disagreed would make an act and a look look unrelated when they are related, which is
    precisely the defect `confirms` exists to catch.

    `role` is valid at the instruction it is yielded with, before that instruction's own register
    write — which is what both readers need, since operands are read before the destination is clobbered."""
    params, program = fn.load(g, name)
    roles: dict = {}

    def role(operand):
        """The subject an operand names: a parameter, or whatever a register was last made to denote."""
        if isinstance(operand, F) and operand.name in params:
            return operand.name
        if isinstance(operand, R):
            return roles.get(operand.name)
        return None

    for stored in program:
        if isinstance(stored, str):
            continue                                        # a label, not an instruction
        # A call to the closed access vocabulary IS the opcode it stands for, and is read as one. Without
        # this, a rule lowered to mediated calls would report no effects at all — every `INVOKE` is
        # opaque here — and the planner would go blind to exactly the rules that are written properly.
        # The translation lives in `access.as_opcode` because the set is closed and one reader per
        # consumer is the drift this function exists to prevent.
        ins = access.as_opcode(stored) or stored
        yield ins, role
        a = ins.args
        if ins.op in isa.WRITES_REGISTER and a and isinstance(a[0], R):
            fresh = _denotes(ins, role)
            roles.pop(a[0].name, None)
            if fresh is not None:
                roles[a[0].name] = fresh
        elif ins is not stored and stored.args and isinstance(stored.args[0], R):
            # A mediated *write* translates to an opcode with no destination, but the call still had one
            # and it now denotes something this walk cannot name. Leaving the old role in place would
            # make a later instruction report an effect on whatever that register used to mean.
            roles.pop(stored.args[0].name, None)


def _effects(g: Graph, name: str, *, include_mocks: bool) -> tuple:
    effects, unknown = set(), set()
    for ins, role in _walk(g, name):
        a = ins.args
        arg = a[1] if len(a) > 1 else None

        if ins.op in isa.WRITES_REGISTER:
            if not (a and isinstance(a[0], R)):
                unknown.add(None)                           # malformed for this opcode: say nothing
                continue
            if ins.op == "NEW":
                # Bringing something into existence is an effect too — the one a goal like "some file
                # exists" is looking for, and the one a type signature cannot express.
                if len(a) > 1 and isinstance(a[1], str):
                    effects.add(("mint", a[1], "$" + a[0].name, None))
                else:
                    unknown.add(None)
            elif ins.op in ("INVOKE", "DISPATCH"):
                unknown.add(None)                           # the effect happens somewhere else
            continue

        if ins.op in ("LINK", "LINK_AT", "UNLINK"):
            if isinstance(arg, str):
                obj = a[-1] if ins.op != "UNLINK" else None
                effects.add(("link", arg, role(a[0]), role(obj) if obj is not None else None))
            else:
                unknown.add(role(a[0]))                     # a computed label, on a subject we can name
        elif ins.op == "SET":
            if isinstance(arg, str):
                # The value, when the instruction states it outright. It used to be hardcoded `None`, so
                # an attribute effect carried its slot and its subject but never what it writes — and
                # `relevance` therefore scored band 4 ("this call writes exactly the constraint") for
                # `SET where "home"` against a goal wanting `where = school`. Right slot, right subject,
                # value never consulted. Link effects always carried both roles, so link constraints were
                # checked exactly and attribute ones were not; this closes the asymmetry.
                #
                # `UNREADABLE`, not `None`: `None` is an ordinary attribute value (isa.py's `SET` handler
                # says so in as many words), so a sentinel is what keeps *"writes nothing we can name"*
                # distinct from *"writes the value None"*. Conflating them is the UNKNOWN-versus-NO mistake
                # this engine has a whole check about.
                effects.add(("attr", arg, role(a[0]),
                             a[2] if len(a) > 2 and not isinstance(a[2], (R, F)) else UNREADABLE))
            else:
                unknown.add(role(a[0]))
        elif ins.op == "CALL":
            unknown.add(None)                               # a local jump: the body runs out of order

    # Jumps are NOT read AT all, and that is a silent part of the over-approximation. This walk is
    # linear: `JMP` / `JMPIF` / `JMPNOT` are skipped, so a write inside a loop body is reported once and
    # a *conditional* write is reported as unconditional. Both are false positives, which is the
    # documented contract (`establishes` is an over-approximation, conservative for ranking and a
    # false-positive generator for recognition) — but the contract does not say *which* constructs generate
    # them, and only `CALL` marks itself unknown.
    #
    # Measured, because an earlier note argued the other way: it predicted that removing local
    # control flow would remove `establishes`'s blindness. Over every function the engine's own scenarios
    # define, 8 of 10 are already exact and the other 2 are darkened by `DISPATCH` — the world, which no
    # branch-free vocabulary touches. Not one is darkened by control flow. So the exactness payoff claimed
    # for retiring the loop opcodes is, on this library, zero.

    if include_mocks:
        for outcome in fn.mocks_of(g, name):                # depth 1: a mock has no mocks of its own
            more, more_unknown = _effects(g, outcome, include_mocks=False)
            effects |= more
            unknown |= more_unknown
    return frozenset(effects), frozenset(unknown)


# --- the read side, and the relation between an ACT and a LOOK ------------------------------------------
#
# The USER's example: *"I change some files, I expect `git status` to not return
# empty. In some way, i related the two. I think it's because I can anticipate the behaviour of git status
# when I know some files have changed."*
#
# Two things had to be separated to answer that, and only the second was missing:
#
#   * the anticipation — already possible and never written down. A mock is an ordinary microfunction,
#     so it can read the graph and compute its prediction from world state instead of asserting a constant.
#     Every mock in this repo's fixtures asserts a constant (`found_two` always predicts two files), which
#     made mocks *look* like assumptions when they are really models. Measured in
#     an earlier probe: one unedited mock, two worlds, two different predictions.
#   * the relation — nothing related the act to the look. `anticipate` reads `changed_file` because it
#     was authored that way, and nothing checked that `edit` writes `changed_file`. Rename one and the
#     anticipation still parses, still runs, and silently models the wrong thing.
#
# The asymmetry is the finding: read the ACT's body, and the LOOK's mock. An act's body is what it
# does. A look's body is a `DISPATCH` and therefore says nothing at all — `establishes` already found this
# out from the other side ("`scan_dir`'s own body establishes almost nothing"), so the mock is the only
# account of what the tool reports on. Reading the look's body instead yields the empty set every time,
# which would make every pair unrelated and the whole measure vacuous.


def _reads(g: Graph, name: str, *, include_mocks: bool) -> tuple:
    """What this body reads, as `(kind, label, subject_role)` — the dual of `_effects`.

    Same three role forms, same over-approximation contract, and deliberately the same shape minus the
    fourth slot: a read has no value to carry."""
    out, unknown = set(), set()
    for ins, role in _walk(g, name):
        if ins.op not in isa.READS_GRAPH:
            continue
        a = ins.args
        subject = role(a[1]) if len(a) > 1 else None
        slot = a[2] if len(a) > 2 else None
        if isinstance(slot, str):
            out.add((isa.READS_GRAPH[ins.op], slot, subject))
        else:
            # `NSOURCES R(x) R(n)` with no label reads every label, which is honestly unreadable rather
            # than a read of nothing. Same discipline as `_effects`: name the subject we could not finish
            # reading, so a consumer knows how much of the answer is missing and about what.
            unknown.add(subject)
    if include_mocks:
        for outcome in fn.mocks_of(g, name):                # depth 1: a mock has no mocks of its own
            more, more_unknown = _reads(g, outcome, include_mocks=False)
            out |= more
            unknown |= more_unknown
    return frozenset(out), frozenset(unknown)


def reads(g: Graph, name: str) -> tuple:
    """What this function's own body reads. Returns `(reads, unknown)`, mirroring `establishes`.

    For a function that reaches the world this is almost always empty, and that is correct rather
    than a failure: everything a tool call learns happens on the far side of the `DISPATCH`. Use
    `reports_on` for a look."""
    return _reads(g, name, include_mocks=False)


def reports_on(g: Graph, look: str) -> tuple:
    """What a LOOK reports on — read off its mocks, never its body. Returns `(slots, unknown)`.

    A mock of a look is a *model of the tool*: it says which parts of the world the tool's answer depends
    on. `anticipate`'s `COUNT R(n) F(t) "changed_file"` is the sentence *"git status reports on the
    changed files"*, written as something that runs."""
    return _reads(g, look, include_mocks=True)


def confirms(g: Graph, act: str, look: str) -> frozenset:
    """The slots by which `look` could confirm `act` — what the act writes and the look's model reads.
    Empty means this look cannot tell you anything about whether that act landed.

    Derived, never declared. Both halves are already graph data, and nothing had thought to join them.
    Declaring the relation instead was the obvious alternative and would have been the labelling error this
    codebase keeps recording: an authored `git_status reflects edit` edge can drift from the bodies, and a
    derivation cannot, because it *is* the bodies.

    Static, so it matches on `(kind, label)` and not on the individual. "This act writes a
    `changed_file` link and this look watches `changed_file` links" is a fact about the two functions.
    Whether they touch *the same tree* is a question about one pair of calls, which only a caller holding
    bindings can ask — the same static-provenance/dynamic-resolution split `establishes` and `role_node`
    already draw, and for the same reason.

    Inherits `establishes`'s over-approximation on the write side, so a non-empty answer means *could*
    confirm, never *does*. The empty answer is the sharp one: nothing the act writes is watched, so no
    outcome of the look is evidence about it."""
    effects, _unknown = establishes(g, act)
    watched, _ = reports_on(g, look)
    return frozenset({(k, lbl) for k, lbl, _s, _o in effects}
                     & {(k, lbl) for k, lbl, _s in watched})


def role_node(g: Graph, bound: dict, role: str | None):
    """The node a role from `establishes` names, given `{param: node}` — `None` if it names none.

    The path is resolved here, against the world, not statically. `establishes` can say that a write
    lands on `c`'s `right` without knowing which node that is; only a caller with bindings in hand can turn
    that into an individual and ask whether it is the one a constraint is about. Static provenance plus
    dynamic resolution is what restores the exact-match band for a navigating operator.

    A `$` role names something minted inside the callee, which no binding can identify, so it resolves to
    `None` — the same answer it gave when it could not be resolved at all.

    The path grammar itself now lives in `path.py` and is shared with the type and goal surfaces. It used
    to be a private regex here, which is why nothing else on the surface could refer past one hop. What is
    left here is the only part that is genuinely this module's: the base names a parameter, not
    something in the graph, so only a caller holding bindings can start the walk."""
    if role is None or role.startswith("$"):
        return None
    try:
        base, rest = P.split_base(role)
    except P.BadPath:
        return None
    node = bound.get(base)
    return node if rest is None else P.node_at(g, node, rest)


def _frame_of(g: Graph, bindings: dict):
    """The frame these bindings were taken from — recovered from the graph, never passed in.

    This is why `relevance` keeps its four-argument shape. A `view` parameter would have to be threaded
    through `pursue`'s `rank=` hook and through `guideline.compose`, so every author of a ranker would
    have to know about frames; and a module-level stash of "the current view" would be exactly the hidden
    Python channel the loop arc exists to remove. A frame points at its mappings, so the reverse index
    already answers this — the same reasoning as `dispatch._thread_of`, which derives a thread rather than
    accepting one."""
    for m in bindings.values():
        for f in g.sources(m, "mapping"):
            if g.kind(f) == "frame":
                return f
    return None


def _witness_band(g: Graph, c: str, bound: dict, matching: tuple, bindings: dict) -> int:
    """Band 4 when this call writes something that could stop a witness from offending; 0 otherwise.

    Discriminating, not optimistic. For a type constraint `matching` is every effect the function
    has, because there is no label to filter on — so scoring band 4 for merely touching a witness would
    rank `measure(f)` as highly as `delete(f)` for a tidiness goal. The effect's `(kind, label)` therefore
    has to appear in the requirements of the type the witness must *stop* satisfying. That keeps this a
    ranker's sense: it is still only a guess, and it still never filters."""
    subject = g.target(c, "subject")
    if subject is None:
        return 0                                        # existential: the `mint` branch above serves it
    frame = _frame_of(g, bindings)
    view = view_in(g, frame) if frame is not None else None
    here = view(subject) if view is not None else subject
    if here is None:
        return 0
    found = TY.offenders(g, here, g.attr(c, "type"))
    for label, hits in found.items():
        want = TY.offending_type(g, g.attr(c, "type"), label)
        if want is None:
            continue
        schema, attrs, _rels = TY.requirements(g, want) or ({}, {}, ())
        real = {W.original_of(g, n) for n in hits}
        for kind, lbl, sp, _op in matching:
            if (kind == "attr" and lbl in attrs) or (kind == "link" and lbl in schema):
                if role_node(g, bound, sp) in real:
                    return 4
    return 0


def relevance(g: Graph, name: str, bindings: dict, unmet: tuple) -> int:
    """How promising this proposal looks against the constraints that are still false. Higher is sooner.

    Four bands: 4 — this call, with these bindings, writes *exactly* the constraint (right label, and
    the right individual in each role); 3 — right label, both individuals involved but the roles do not
    line up; 2 — right label, one of the right individuals; 1 — right label; 0 — nothing to do with any
    open constraint.

    Band 4 versus band 3 is the one that earns its place. Without roles, `stack(b=b, onto=a)` scores
    the same as `stack(b=a, onto=b)` for the constraint "a on b", since both involve a and b — and the
    ranking barely beats blind search (measured: 13 imagined states versus 15). Distinguishing them is what
    makes the guidance real.

    This ranks, it never filters, and that is the whole design. A greedy means–ends planner that only
    tries constraint-satisfying moves cannot solve Hanoi or the Sussman anomaly, where progress requires
    *undoing* something first. Scoring 0 puts a move last, not out of reach — so the hard cases stay
    solvable while the easy ones stop being searched blindly. This is also System 1's first real job, and
    notably it needs none of the neighbourhood/radius question resolved."""
    effects, unknown = establishes(g, name)
    bound = {p: stands_for(g, m) for p, m in bindings.items()}
    involved = set(bound.values())
    best = 0
    for c in unmet:
        sort = g.attr(c, "sort")
        want_label = g.attr(c, "label") if sort == "link" else g.attr(c, "key")
        kind = {"link": "link", "attr": "attr"}.get(sort)
        # "Something of this type must exist" is answered by an operator that mints one — the existential
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

        # The witness BRANCH — what makes a universal constraint rankable at all.
        # `d is a tidied_dir` names `d` as its subject, but the nodes that have to change are the *files*,
        # so the exact-role test below can never fire and every proposal scored band 1 — measured, in
        # `docs/limits.md`, for a singular action that would certainly close it. `goal.witnesses` names
        # the members that make it false, which is's *"which constraints are still false"* one level
        # further in: *which members are still wrong*.
        if sort == "type":
            best = max(best, _witness_band(g, c, bound, matching, bindings))
        for _k, _lbl, sp, op in matching:                   # does a role assignment line up exactly?
            # An attribute effect must write the value the constraint wants. Band 4 claims this call
            # writes *exactly* the constraint; for a link the object role already carried that claim, but
            # an attribute effect had no value at all, so `SET where "home"` scored band 4 against a goal
            # wanting `where = school` — the right slot on the right node, and the wrong world. Measured:
            # the school scenario's guidance was entirely this accident.
            # `UNREADABLE` keeps band 4, and deliberately: `establishes` is an over-approximation by
            # contract, so what we cannot read must never *lose* a candidate a rank.
            if _k == "attr" and op is not UNREADABLE and g.attr(c, "value") != op:
                continue
            # A role may be a path (`c.right`), so it is resolved against the world rather than looked
            # up. Measured on the first consumer's repair operator, whose whole purpose is to change part of
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


def _could_close(g: Graph, effects: frozenset, unmet: tuple) -> bool:
    """Could a function with these effects close any of these constraints, given the right world?

    Label-level only, and that is the point: it is asked of a function that cannot run here, so there
    are no bindings to be exact with. Over-approximating is safe because the answer only ever *orders*."""
    for c in unmet:
        sort = g.attr(c, "sort")
        if sort not in ("link", "attr"):
            return True                                     # a type constraint: cannot cheaply tell
        kind = "link" if sort == "link" else "attr"
        want = g.attr(c, "label") if sort == "link" else g.attr(c, "key")
        if any(e[0] == kind and e[1] == want for e in effects):
            return True
    return False


def wants_that_unblock(g: Graph, frame: str, blocked: tuple, unmet: tuple) -> frozenset:
    """`{(requirement label, node)}` — what would have to become true for some relevant but currently
    impossible action to become possible.

    The missing half of the guidance, and why `relevance` alone could not supply it. A band classifies
    *this move against the goal*: it answers "does this close a constraint?". A prerequisite closes nothing,
    so it is band 0 — correctly, and tied with every irrelevant operator in the library. Measured on a
    three-step plan whose first move writes a different slot from the goal's: guided cost grew 4 / 6 / 10 /
    16 as 0 / 2 / 6 / 12 irrelevant operators were added, because the search had to try each of them first.
    No refinement of a match-quality scale can fix that, because a prerequisite is not a worse match — it is
    a different distance, which a match scale does not measure.

    Restricted to actions that could *close an open constraint*. Without that, every blocked action in
    the library contributes wants and the score becomes "make something possible", which is not a goal.

    The requirements are recomputed here rather than collected during enumeration, and that inversion
    is the whole cost story. The obvious design — record what failed while testing candidates, since
    `fails` is being called anyway — puts a set insertion on the path taken by *most* candidate tests, which
    is what enumeration mostly does. Measured:'s benchmark went 2.08ms to 6.98ms, and even gated by
    relevance it stayed at 6.30. A blocked function is one that contributed no proposal at all, so blocked
    functions are few by definition — recomputing for just those is `|blocked and relevant| x |params| x
    |mappings|`, which on the blocks world with 200 irrelevant nodes is zero calls, because nothing
    relevant is blocked there. The expensive case is exactly the case that needs the answer.

    The general shape, worth keeping: *doing the work eagerly for everything cost more than doing it
    lazily for the few that need it* — even though the eager version was reusing a value already computed."""
    here = W.visible(g, frame)
    view = view_in(g, frame)
    wants = set()
    for name in blocked:
        if not _could_close(g, establishes(g, name)[0], unmet):
            continue
        params, _ = fn.load(g, name)
        ptypes = fn.param_types(g, name)
        for p in params:
            reqs = TY.requirements(g, ptypes.get(p))
            if reqs is None:
                continue
            for m in here:
                # Tested against the image (the world as imagined in this frame), keyed by what it
                # stands for (the individual a constraint talks about). Those are different nodes, and
                # conflating them made this component silently score zero on every proposal.
                for label in TY.fails(g, W.image_of(g, m), reqs, view=view):
                    wants.add((label, stands_for(g, m)))
    return frozenset(wants)


def unlocks(g: Graph, name: str, bindings: dict, wants: frozenset) -> int:
    """How many blocking requirements this proposal would write. Higher is sooner — after the band.

    What guarantees that this cannot outrank a real closing move is `expected`, NOT the key position
    — and that correction came from a probe. The first version of this docstring said the guarantee was
    that `-opens` sits after `-rank_here`. It does, but that is a *redundant second guard*: `expected` is
    the key's first component and already folds in `rank >= 4`, so a band-4 move sorts ahead whatever
    happens further along the tuple. Probed all three ways against a detour that unlocks two
    requirements where the closing move unlocks one — neutering `expected` alone changes nothing, swapping
    the two components alone changes nothing, and only removing both together degrades the plan. So's dominance invariant holds here, over-determined, and no single line of it is load-bearing.

    What the position *does* decide is the order among moves that close nothing: band 1-3 ("mentions the
    goal's label") currently beats "would unblock something relevant". That is an unexamined preference —
    the bands below 4 are weak evidence (they only ever meant *related to*), while an unlock is derived
    from a requirement that really does block a really relevant action. It is left as it was found rather
    than changed on a hunch, and it is named here so the next person knows it was never argued.

    Like everything else in this module except a safety breach it only ever orders — `guideline.py`'s
    planted-bug probe showed that a frontier which merely orders cannot put a move out of reach however
    badly it is scored."""
    if not wants:
        return 0
    bound = {p: stands_for(g, m) for p, m in bindings.items()}
    hit = set()
    for kind, label, subject_role, _fourth in establishes(g, name)[0]:
        node = role_node(g, bound, subject_role)
        if node is None:
            continue
        # `types.fails` keys attribute requirements with a leading `@` and link requirements with the bare
        # label — the same spelling `violations` reports to a human, reused rather than re-derived.
        key = (f"@{label}" if kind == "attr" else label, node)
        if key in wants:
            hit.add(key)
    return len(hit)


def state_of(g: Graph, frame: str) -> frozenset:
    """A canonical signature of the world as imagined in this frame — the visited-set key.

    Dedupe on the state, not on the action, and the difference is not academic. The first version of
    this driver skipped any `(function, arguments)` triple it had already imagined anywhere. That silently
    made the search unable to solve a three-block tower: the root frame enumerates every pair, so *every*
    action is marked seen at depth 1, and each branch below it then has nothing left to try. Two-step
    solutions became unreachable while the driver reported an honest-looking "no plan found".

    Comparing frames or mappings directly would treat every copy as new, since each frame mints its own. So
    each node is identified by what it *really* is (`resolve`), and the signature is its attributes plus its
    edges rewritten in those terms."""
    ident = {}
    for m in W.visible(g, frame):
        ident[W.image_of(g, m)] = W.resolve(g, m) or m
    out = []
    for image, who in ident.items():
        attrs = tuple(sorted((k, v) for k, v in g.attrs.get(image, {}).items() if k != "kind"))
        edges = tuple(sorted((lbl, tuple(ident.get(t, t) for t in g.targets(image, lbl)))
                             for lbl in g.labels(image)))
        out.append((who, attrs, edges))
    return frozenset(out)


def _warn_if_advice_is_inert(g: Graph, rank) -> None:
    """authored advice that nothing will consult is a silent wrong answer.

    A consumer hit this, and it cost them one. A `prefer` block parses, mints a `guideline`,
    sits in the graph — and changes nothing unless the caller passed `rank=guideline.ranker(g)`. From
    outside, "the advice was ignored" is indistinguishable from "the advice was consulted and lost",
    which is a legitimate outcome, so there is nothing to notice.

    That is the one place this engine's refusal discipline stopped at the parser. Everywhere else,
    authored text that cannot do anything is refused loudly — a guideline naming neither an action nor a
    thing, a type demanding nothing, a method with no steps. Here the text was *accepted* and made inert
    by a keyword argument at a call site the author never sees. They hit it through the CNL, which
    is the path a language model writes: a model emitting a good `prefer` block sees no effect and has no
    way to tell it was ignored.

    A warning, not a refusal, and `rank=` stays explicit. The composition is deliberate — a caller
    may legitimately supply its own ranker, and that ranker may or may not read guidelines — so refusing
    would break a supported arrangement. What was missing is only that nobody was *told*. Anything passed
    as `rank` is taken at its word for the same reason: this cannot know whether a custom ranker consults
    them, and guessing would produce a false warning, which teaches people to ignore warnings."""
    if rank is not None:
        return
    from . import guideline as GL
    advice = GL.advice(g)
    if advice:
        import warnings
        warnings.warn(
            f"{len(advice)} guideline(s) declared and none will be consulted: `pursue` was called "
            f"without `rank=`, so authored `prefer`/`avoid` blocks have no effect here. "
            f"Pass `rank=guideline.ranker(g)`.", RuntimeWarning, stacklevel=3)


def pursue(g: Graph, goal: str, thread: str, subject: str, *,
           max_steps: int = 60, max_depth: int = 6, rank=None, guided: bool = True, allow=None,
           trace=None, decide=None, propose=None) -> dict:
    """Search for a state satisfying `goal`, imagining every step. Returns a report.

    Everything the system considers is recorded on the thread as it happens, so *how* it got there is
    inspectable afterwards rather than reconstructible only by re-running it. On success the report carries
    the winning frame and the plan, which is the frame path — already replayable by `execute`.

    `rank` overrides `relevance` — the hook where a better judgement (a learned policy, a language model
    reading `function.catalogue`) plugs in, and the same shape `selection.score` already uses for the same
    reason. Passing a constant turns this back into blind search, which is how the guidance is measured.

    On failure the report hands BACK the `workbench`, and it is there so the search can be
    Interrogated. Forward chaining used to leave its diagnosis lying in a saturated graph; here every
    imagined state was on a workbench and the world afterwards looks untouched, so a reader who stops at
    `how` (`None` on failure) concludes the failure path says nothing. It is not so — `unmet` and `why` are
    on the report, and `W.frames`, `W.mappings`, `W.resolve` and `W.image_of` reach every state that was
    explored. the first consumer turned "no plan found" into a refusal naming its cause in about fifteen lines
    of that. For a single-constraint goal `unmet` merely restates the goal, so it says *what* was not
    achieved and never *why*; the why is domain knowledge, and it lives in the frames or nowhere.

    `decide` is the deliberation seam (`docs/deliberation.md`). Called once per imagined step, *before*
    the chosen proposal is imagined, with the situation as it already stands. Returning `None` — or
    `EXPAND` — means "nothing to say", so the loop's disposition is unchanged and the default is to keep
    planning; a decision has to speak up to alter it. Returns `verb` or `(verb, reason)`.

    This is an engine seam, not an extension point. The decider that eventually lives here reads
    *decision rules as data* and is shipped with the engine; it is not somewhere a domain author writes
    Python. It is a parameter for the same reason `rank` is — so the behaviour can be substituted in a
    check and so the loop does not have to know what decides.

    Only `COMMIT`, `SENSE` and `REFUSE` can be honoured today, and of those `SENSE` needs ignorance and
    `DECOMPOSE` needs goal hierarchy — both raise `Undecidable` naming what is missing, rather than being
    quietly ignored. A decision that silently does nothing is the failure mode this project keeps catching.

    The authoring rule that follows, which is not obvious and is easy to get wrong: an operation that
    wants to explain itself must record its reason where the frames are. A microfunction that quietly does
    nothing when a precondition fails is unexplainable after a failed search — it leaves no trace in any
    imagined state. One that writes something (`unsupported_confirmation_step`) is diagnosable, because the
    frame that tried it still holds the mark. Silence costs nothing at planning time and everything
    afterwards."""
    _warn_if_advice_is_inert(g, rank)
    search = open_planning(g, goal, thread, subject, max_steps=max_steps, max_depth=max_depth,
                           guided=guided, rank=rank, allow=allow, trace=trace, propose=propose)
    watch = trace

    # >> the loop is now a loop over `step`, and that is the whole point of this slice. `pursue` used to
    # BE the search; it now merely drives it. Everything between two imagined states is a return, so
    # something other than this function can do the driving - which is what "steppable" has to mean before
    # deliberation can be reached as data. Note `pursue` remains the supported entry point and its
    # behaviour is unchanged; `step` is the seam, not a replacement.
    while True:
        out = step(g, search, rank=rank, allow=allow, trace=watch, decide=decide, propose=propose)
        if out is not None:
            return out


def open_planning(g: Graph, goal: str, thread: str, subject: str, *,
                  max_steps: int = 60, max_depth: int = 6, guided: bool = True,
                  rank=None, allow=None, trace=None, propose=None, decider=None) -> str:
    """Open a search on `goal` and seed its frontier. Returns the `search` node, ready to be stepped.

     This is `pursue`'s setup, extracted so there is one of it. `pursue` calls it and then loops; the
    `PLAN` opcode calls it and hands the node back to an ISA program. Two setups that could drift apart is
    exactly the defect shape this codebase keeps recording, and the drift would be silent - a second path
    that forgot to seed the visited set with the root would re-imagine the starting world forever.

    Warn The already-satisfied case is recorded on the search, not returned, so that both drivers agree.
    `pursue` used to return early here; an ISA program calling `PLAN` would then have had no way to learn
    that the goal needed nothing done. Now `step` reports it, and there is one answer whoever asks.

    The trace hook is an observer, never a participant: it is handed a dict per event and its return value
    is discarded, so turning tracing on cannot change what is found. Node ids are useless to a reader, so
    every event carries labels - the thread and the workbench keep the identities, and anything
    reconstructing state from these strings is reconstructing it from a rendering."""
    # Refuse the provably impossible before spending anything on it, and record it on the search so that
    # whoever drives it gets the same answer. `conflict.unsatisfiable` reports only decidable
    # contradictions, so this can never reject a goal that was actually reachable.
    from . import conflict as C
    impossible = C.unsatisfiable(g, goal)
    if impossible:
        T.attend(g, thread, goal, why="the goal contradicts itself", note="; ".join(impossible))
        s = S.open_search(g, goal, W.open_workbench(g, subject, label="refused"), thread, subject,
                          max_steps=max_steps, max_depth=max_depth, guided=guided)
        g.put(s, contradictory=tuple(impossible), done=True, found=False)
        return s

    wb = W.open_workbench(g, subject, label=f"pursuing {g.attr(goal, 'label')}")
    root = W.root_frame(g, wb)
    opened = T.attend(g, thread, goal, why="taking on the goal", note=G.describe(g, goal))
    search = S.open_search(g, goal, wb, thread, subject, opened=opened,
                           max_steps=max_steps, max_depth=max_depth, guided=guided)
    # What is deciding this search, as an edge — so the outer loop can advance it without the caller
    # holding a closure. See `criterion.decider` for the measurement that forced this.
    if decider is not None:
        g.link(search, "decided_by", decider)
    S.mark_seen(g, search, S.digest(*_visited_key(g, goal, root, ())), root)

    view, under = _asked_of(g, subject, root)
    if G.satisfied(g, goal, view=view, under=under) and not G.outstanding(g, goal, ()):
        g.put(search, already=True)
        return search

    if trace:
        trace(dict(kind="goal", step=0, goal=g.attr(goal, "label"),
                   wants=[G.describe_constraint(g, c) for c in G.constraints(g, goal)],
                   open=[G.describe_constraint(g, c)
                         for c in _still_open(g, goal, subject, root)]))
    # The seed must be guided too, and forgetting that cost 3 extra imagined states in the measurement
    # — the fix in `step` alone took the loop-ticked search from 52 to 6 rather than to 3, because the
    # first frontier was still built by enumeration. One resolution point, used by both.
    _offer(g, search, root, 0, None, rank=rank, allow=allow, watch=trace,
           propose=propose if propose is not None else _proposer_of(g, search))
    return search


def _label(g: Graph, n):
    return g.attr(n, "label") or g.kind(n) or n


def _shown(g: Graph, bindings: dict) -> dict:
    return {p: _label(g, stands_for(g, m)) for p, m in bindings.items()}


def _asked_of(g: Graph, subject: str, frame: str) -> tuple:
    """`(view, under)` - how a goal is checked inside this imagined frame."""
    return view_in(g, frame), W.image_of(g, W.mapping_for(g, frame, subject))


def _still_open(g: Graph, goal: str, subject: str, frame: str) -> tuple:
    v, u = _asked_of(g, subject, frame)
    return G.unmet(g, goal, view=v, under=u)


def _visited_key(g: Graph, goal: str, frame: str, trace: tuple) -> tuple:
    """Warn The state alone is NOT the identity of a search node once liveness is in play. Two routes to
    the same world differ if one has already done a required action and the other has not - deduping on
    the world would silently discard the finished one. So what is still outstanding is part of the key."""
    return (state_of(g, frame), G.outstanding(g, goal, trace))


def _defer(g: Graph, search: str, frame: str, depth: int, trace_node) -> str:
    """Record that this frame was not fully enumerated, so it can be later.

    This is what makes deciding-before-enumerating complete rather than merely cheap. A criterion
    that speaks for a frame suppresses the O(N²) product there — but the product is *deferred*, never
    dropped, and `_backfill` builds it if the criteria's own line runs out. So authored knowledge can be
    wrong without a solution becoming unreachable, which is exactly the property `relevance` protects by
    ranking rather than filtering (`docs/deliberation.md`, obtained here by a different means.

    Deferral is the honest word. *Skipping* would make the frontier incomplete — a far stronger claim
    than anything a guess is entitled to make."""
    d = g.mint("deferred", depth=depth)
    g.link(d, "frame", frame)
    if trace_node is not None:
        g.link(d, "trace", trace_node)
    g.link(search, "deferred", d)
    return d


def _backfill(g: Graph, search: str, *, rank=None, allow=None, watch=None) -> bool:
    """The frontier is empty — build the enumeration of one frame a decision spoke for. `False` if none.

    Most recently deferred first, i.e. chronological backtracking. Measured against the alternative:
    oldest-first floods the frontier with one frame's whole product while the proposer keeps deferring new
    frames behind it, and a Sussman run with a deliberately useless proposer then fails outright
    (budget of 200 exhausted, no plan) where newest-first finds one. Insertion order is a fact of the edge
    list, so this needs no key.

    What deferral preserves is the goal, not the plan's quality. Backtracking to the newest deferral
    extends the bad prefix before the root's alternatives are ever built, so a wrong proposer yields a
    *worse* plan rather than none: measured on Sussman, a proposer that always says `paint` still succeeds,
    with `(paint, paint, unstack, stack, stack)` against the default's `(unstack, stack, stack)`. That is
    the honest cost of suppressing enumeration on a guess, and it is strictly milder than losing the
    solution — but it is not nothing, and `relevance`'s rank-never-filter does not pay it at all."""
    waiting = g.targets(search, "deferred")
    if not waiting:
        return False
    d = waiting[-1]
    g.unlink(search, "deferred", dst=d)
    if watch:
        watch(dict(kind="backfill", step=S.steps_taken(g, search), depth=g.attr(d, "depth"),
                   why="the decision's line ran out; enumerating what it suppressed"))
    _offer(g, search, g.target(d, "frame"), g.attr(d, "depth"), g.target(d, "trace"),
           rank=rank, allow=allow, watch=watch)          # no `propose` — never defer the same frame twice
    return True


def _offer(g: Graph, search: str, frame: str, depth: int, trace_node, *,
           rank=None, allow=None, watch=None, propose=None) -> None:
    """Put every proposal available in `frame` onto the frontier, ranked.

    The frontier holds proposals, NOT frames - and that is what makes the guidance worth anything.

    Warn Two wrong versions preceded this, both worth recording. First it was depth-first over frames: it
    committed to the first promising child and explored it to exhaustion, and adding *one* irrelevant rule
    to the library burned the whole budget down a branch that could never close the goal while the sibling
    that solved it in one more move sat untouched. Then it was best-first over frames - which fixed that,
    but *measured no better than unguided* (15 imagined states against 14), because every proposal in a
    frame was imagined before any frame was chosen. Ordering inside a frame cannot save work already done.

    Warn The third wrong version - subtle, and it made the guided search *worse than breadth-first*. The
    key was `(constraints open, -relevance, depth)` where "constraints open" was the parent frame's count,
    so an unexplored root proposal that would obviously close a constraint carried its parent's score of 2
    while mediocre moves two levels down carried 1, and the search abandoned the good move permanently.
    A proposal must be judged by the world it would produce, not the one it starts from. Hence `expected`."""
    c = S.context(g, search)
    goal, guided = c["goal"], c["guided"]
    score = rank if rank is not None else relevance
    open_now = _still_open(g, goal, c["subject"], frame)
    prefix = S.trace_tuple(g, trace_node)

    def emit(kind, **fields):
        watch(dict(kind=kind, step=S.steps_taken(g, search), **fields))

    # Decide BEFORE enumerating. Measured (`docs/deliberation.md`: with criteria the search
    # visits four frames whatever the world's size, yet still built 1,526 proposals at twenty blocks —
    # *all* of the residual cost, and all of it thrown away. `decide` could not remove it because it is
    # consulted after this function has already run. `propose` is the same knowledge, asked one step
    # earlier, where the saving actually is.
    #
    # The suppressed enumeration is deferred, not skipped — see `_defer`.
    if propose is not None:
        suggested = propose({"goal": goal, "frame": frame, "depth": depth, "subject": c["subject"],
                             "search": search, "thread": c["thread"], "open": len(open_now),
                             "prefix": trace_node})
        # A proposer may also REFUSE — `(REFUSE, why)`, the same shape `decide` already returns. That is
        # what a MANDATORY criterion does when it recognises the situation and cannot act in it: a
        # procedure refuses rather than improvising, and quietly falling back to enumeration would be
        # exactly the improvisation it exists to forbid. Written on the search, so whichever driver is
        # stepping it gets the same answer.
        # `not isinstance(..., Call)`, NOT `isinstance(..., tuple)` — a NamedTuple IS a tuple, so the
        # obvious test swallowed every ordinary proposal. Caught by the checks; it would otherwise have
        # been a silent "nothing proposes anything any more".
        if suggested is not None and not isinstance(suggested, Call):
            verb, why_stop = suggested
            g.put(search, stop=verb, stop_why=why_stop)
            if watch:
                emit("refuse", action=None, because=why_stop, depth=depth)
            return
        if suggested is not None:
            bound, touched = check_call(g, goal, frame, suggested, trace_node)
            ahead = S.extend_trace(g, trace_node, suggested.function, touched)
            rank_here = score(g, suggested.function, bound, open_now)
            S.offer(g, search, key=(len(open_now) - (1 if rank_here >= 4 else 0), -rank_here, 0, depth),
                    frame=frame, depth=depth, function=suggested.function, bindings=bound,
                    open_count=len(open_now), trace=ahead)
            # ADVISORY defers; MANDATORY does not. This one line is the whole of force at this seam,
            # and it is the honest consequence: only a claim about the situation ("in this
            # situation, this is the move") is entitled to remove the alternatives, because only that
            # claim is wrong in a way the author meant to be fatal.
            if not suggested.final:
                _defer(g, search, frame, depth, trace_node)
            if watch:
                emit("propose", action=suggested.function, on=_shown(g, bound), depth=depth,
                     because=suggested.why, final=suggested.final)
            return

    here, blocked = enumerate_frame(g, frame, allow=allow)
    # Once per frame, not once per proposal — `docs/deliberation.md`'s frequency rule, and's record of
    # what ignoring it costs. `wants` is the same for every proposal offered from this frame.
    wants = wants_that_unblock(g, frame, blocked, open_now) if guided else frozenset()
    for name, bindings in here:
        # Constraints on the PLAN, checked BEFORE imagining - so a forbidden action costs nothing.
        # Warn This filters where `relevance` only ranks, and the difference is principled: relevance is a
        # guess about what will help, so filtering on it could lose a solution (Sussman's anomaly needs a
        # low-scoring move). A safety breach is a proof - no continuation of a plan that used a forbidden
        # action makes it unused - so pruning is sound. Rank a guess; prune a proof.
        touched = frozenset(stands_for(g, m) for m in bindings.values())
        ahead = prefix + ((name, touched),)
        hit = G.breached(g, goal, ahead)
        if hit:
            reasons = tuple(G.describe_constraint(g, x) for x in hit)
            S.refuse(g, search, name, reasons)
            # Worth emitting: this is the machine declining to even IMAGINE something, which is invisible
            # in any after-the-fact record precisely because nothing happened.
            if watch:
                emit("refuse", action=name, on=_shown(g, bindings),
                     because=list(reasons), depth=depth)
            continue
        # Warn Minted only AFTER the breach check, so a refused action leaves no trace step behind.
        ahead_node = S.extend_trace(g, trace_node, name, touched)
        if not guided:
            S.offer(g, search, key=(0, 0, 0, depth), frame=frame, depth=depth, function=name,
                    bindings=bindings, open_count=len(open_now), trace=ahead_node)
            continue
        rank_here = score(g, name, bindings, open_now)
        expected = len(open_now) - (1 if rank_here >= 4 else 0)
        opens = unlocks(g, name, bindings, wants)
        if watch:
            emit("consider", action=name, on=_shown(g, bindings), band=rank_here,
                 open=len(open_now), unlocks=opens, depth=depth)
        # `-opens` sits AFTER `-rank_here`: a move that merely makes something possible can never
        # outrank one that actually closes a constraint. It only ever separates the moves that were tied.
        S.offer(g, search, key=(expected, -rank_here, -opens, depth), frame=frame, depth=depth,
                function=name, bindings=bindings, open_count=len(open_now), trace=ahead_node)


def check_call(g: Graph, goal: str, frame: str, call: Call, prefix: str | None) -> tuple:
    """Is this `Call` something that could actually be applied here? Returns `(bindings, touched)`.

    One place, because there are now two callers — `_honour` (a decision substituting for the ranked
    choice) and `_offer` (a decision spoken *before* enumeration). Two copies of a validation that must not
    drift is the defect shape this codebase keeps recording, and here the drift would be silent: one route
    would admit a call the other refuses.

    A binding the enumeration never proposed is fine; an ill-typed one is not. Naming a binding is
    the whole point (`selection.candidates`' *"inventing bindings is search"*). What is checked is exactly
    what `enumerate_frame` checks — declared parameter types, no node in two roles — plus the one thing
    ranking may never overturn: `goal.breached`. Rank a guess, prune a proof."""
    if fn.find(g, call.function) is None:
        raise Undecidable(f"a decision named {call.function!r}, which is not a function in this library")
    params, _ = fn.load(g, call.function)
    if set(params) != set(call.bindings):
        raise Undecidable(f"a decision named {call.function}({', '.join(sorted(call.bindings))}), but it "
                          f"takes ({', '.join(params)}) — a call must bind every parameter and no others")

    mine = W.visible(g, frame)
    bound = {}
    for p, given in call.bindings.items():
        m = given if given in mine else W.mapping_for(g, frame, given)
        if m is None or m not in mine:
            raise Undecidable(f"a decision bound {call.function}.{p} to {given!r}, which is not in the "
                              f"world being imagined here")
        bound[p] = m
    # The same declared conditions the enumeration filters on — one implementation, so a decision
    # arriving from outside cannot be admitted where the search would have refused it. This replaced a
    # hardcoded *one node in two roles*, which said in its own message that the type system could not say
    # `a != b`; the function says it now.
    ungranted = fn.unmet_guards(g, call.function, {p: stands_for(g, m) for p, m in bound.items()},
                                frame=frame)
    if ungranted:
        raise Undecidable(f"a decision named {call.function}, which does not apply here: "
                          + "; ".join(ungranted))

    ptypes = fn.param_types(g, call.function)
    for p, m in bound.items():
        reqs = TY.requirements(g, ptypes.get(p))
        if reqs is None:
            raise Undecidable(f"{call.function}.{p} has no declared type, so nothing can satisfy it")
        missing = TY.fails(g, W.image_of(g, m), reqs, view=view_in(g, frame))
        if missing:
            raise Undecidable(f"a decision named {call.function} with {p}={_label(g, stands_for(g, m))!r}, "
                              f"which is not a {ptypes[p]}: {missing}")

    touched = frozenset(stands_for(g, m) for m in bound.values())
    hit = G.breached(g, goal, S.trace_tuple(g, prefix) + ((call.function, touched),))
    if hit:
        raise Undecidable(f"a decision named {call.function}, which this goal forbids: "
                          + "; ".join(G.describe_constraint(g, x) for x in hit)
                          + " — advice may reorder, never overrule a constraint on the plan")
    return bound, touched


def _honour(g: Graph, search: str, c: dict, call: Call, displaced: str, frame: str, prefix: str | None):
    """Carry out a `Call` — substitute the decision's action for the one ranking chose.

    Returns `(function, {param: mapping}, trace_node)`, or `None` when this decision is spent — see the
    frequency rule below.

    A decision applies once per frame per CALL, and discovering why is the main thing this seam
    taught. Putting the displaced candidate back and letting a deterministic criterion speak again are in
    direct tension: the search re-takes the displaced candidate, the criterion names the same action, that
    action reaches a state already imagined, the candidate goes back again — a livelock, measured
    (12 steps, 9 of them the same substitution from the same frame, goal never reached).

    So a substitution is recorded on the frame and is not repeated. This is not a new principle: it is
    `docs/deliberation.md`'s frequency rule and the same answer `DECOMPOSE` already gives — *"a method applies
    once per goal, never once per search step. Frequency, not absence."* And it is honest rather than
    silent: the decision is not ignored, it has already been carried out here, and the trace says so.

    The displaced candidate goes BACK on the frontier, and that is the load-bearing line.
    `docs/deliberation.md`'s rule is that a criterion may prune freely *provided the prune is recorded and
    the fallback is reachable* — because a prune here happens while imagining, so being wrong costs
    imagined states rather than actions. Dropping the displaced candidate instead would make a criterion's
    mistake unrecoverable, which is the one thing that turns cheap-to-be-wrong into expensive-to-be-wrong.

    Re-offered by re-linking, so its key survives — the candidate node was only unlinked by
    `take_best`, never destroyed. It therefore returns to the *end* of insertion order, which changes the
    tie-break among candidates with identical keys. That is a real if small semantic change, and it happens
    only when a decision actually fires; the default path never reaches this function.

    A fresh trace step, not the displaced one's. The candidate's `trace` already includes *its own*
    action, so reusing it would record a plan that took a step nobody took. The prefix is one link up.

    Every refusal here is `Undecidable` — loud, naming what was wrong. A decision that silently does
    nothing is the failure this project keeps catching, and a decision silently *corrected* is worse."""
    goal, thread = c["goal"], c["thread"]
    bound, touched = check_call(g, goal, frame, call, prefix)

    # Spent? See the frequency rule above. Compared on (function, individuals), not on the candidate,
    # because the same action reached from the same frame by a different route is the same action.
    for prior in g.targets(frame, "decided"):
        if g.attr(prior, "function") == call.function and \
                frozenset(g.targets(prior, "touched")) == touched:
            return None

    g.link(search, "candidate", displaced)          # The fallback stays reachable
    ahead = S.extend_trace(g, prefix, call.function, touched)
    g.link(frame, "decided", ahead)                 # once per frame per call — the frequency rule
    T.attend(g, thread, goal, why=f"decided to do {call.function}",
             note=call.why or f"instead of {g.attr(displaced, 'function')}")
    return call.function, bound, ahead


def _proposer_of(g: Graph, search: str):
    """The proposer this search node itself names, or `None`. Rebuilt per step rather than cached: the
    criteria are read from the graph when asked, so a criterion withdrawn mid-search stops being consulted
    — caching the closure would keep a retracted block deciding, which `discourse.py` exists to prevent."""
    d = g.target(search, "decided_by")
    if d is None:
        return None
    from . import criterion as CR
    return CR.proposer_for(g, d)


def step(g: Graph, search: str, *, rank=None, allow=None, trace=None, decide=None, propose=None):
    """ one iteration of the search - the yield point `pursue` never had.

    Returns `None` while the search should continue, and the finished report when it should not (found,
    stopped by a decision, or exhausted). So a caller other than `pursue` can drive the search, stop
    between two imagined states, look at what has been considered so far, and resume - which is what
    `docs/deliberation.md` means by deliberation becoming something the system can compute *about* rather than
    only *with*. `pursue` was a closed loop with no yield point, so "what should I do next?" was not an
    expressible question, only a `while` condition.

    Warn The state is entirely in the graph (`search.py`), so two calls need share nothing but the
    search node. The four hooks are Python callables and are passed per call, because a callable cannot
    live in a graph - that split is the honest boundary between substitutable behaviour and state.

    Warn This does not make the search *re-entrant across mutation*: the graph is mutable and the frontier
    refers to frames, so driving one search while something else edits its workbench is undefined.
    Stepping is a yield point, not isolation."""
    c = S.context(g, search)
    goal, wb, thread = c["goal"], c["workbench"], c["thread"]
    subject, max_depth = c["subject"], c["max_depth"]
    watch = trace

    def emit(kind, **fields):
        watch(dict(kind=kind, step=S.steps_taken(g, search), **fields))

    if g.attr(search, "contradictory"):
        # Recorded at setup, reported here, so every driver gives the same answer. It used to be an early
        # `return` inside `pursue`, which meant a second driver had to know to make the check itself —
        # and `driver.pursuit_step` promptly did, i.e. two copies of it existed for as long as it took to
        # notice. Same fix as `already`, for the same reason.
        why = "; ".join(g.attr(search, "contradictory"))
        return {"found": False, "workbench": None, "steps": 0, "goal": goal,
                "contradictory": g.attr(search, "contradictory"), "refused": (), "blocked_by": (),
                "why": "the goal cannot be met: " + why, "search": search}
    if g.attr(search, "already"):
        return _done(g, goal, thread, wb, W.root_frame(g, wb), c["opened"],
                     "already satisfied", 0, (), search)
    # A stop written on the search — self-monitoring, and it needed no new mechanism. Everything
    # about a running computation is now graph data (`search.steps`, the frontier, the phase), so a rule can
    # ask *"have I been planning too long?"* — and this is the one line that lets it do something about the
    # answer. A watcher is an ordinary microfunction on the ordinary agenda, interleaved with the search it
    # is watching, writing `stop` on the search node it is reading.
    #
    # The `decide` hook already did this and is NOT redundant — it is a Python callable consulted
    # *per proposal*, which is right for a ranker-frequency decision (`docs/deliberation.md` and wrong for
    # anything a domain author should be able to write. This is the same decision expressed as data,
    # which the standing principle requires: everything a domain contributes is data. They are the same
    # verbs and the same report, deliberately, so a reader cannot tell which route stopped a search.
    # NO hook? Ask the graph. This is what makes a guided search resumable by anything — `loop.tick`
    # forwards only the hooks its own caller held, so before this a search ticked by the outer loop
    # silently lost its guidance (3 imagined states became 52, measured). An explicit `propose=` still
    # wins, because a caller naming a proposer is being deliberate.
    if propose is None:
        propose = _proposer_of(g, search)
    told = g.attr(search, "stop")
    if told:
        verb = told if told in _STOPS else REFUSE
        return _stopped(g, search, c, verb, g.attr(search, "stop_why")
                        or "stopped by a rule watching this search", watch)
    if S.steps_taken(g, search) >= c["max_steps"]:
        return _exhausted(g, search, c, watch)
    chosen = S.take_best(g, search)
    if chosen is None:
        # Nothing left to try — but a decision may have suppressed alternatives rather than ruled them
        # out. Build one deferred frame's enumeration and carry on; only a search with nothing deferred
        # is really exhausted. This is what keeps `propose` complete rather than merely cheap.
        if _backfill(g, search, rank=rank, allow=allow, watch=watch):
            return None
        return _exhausted(g, search, c, watch)

    _c = S.read(g, chosen)
    frame, depth, name = _c["frame"], _c["depth"], _c["function"]
    bindings, open_count, trace_node = _c["bindings"], _c["open_count"], _c["trace_node"]
    tr = S.trace_tuple(g, trace_node)

    # The decision point. Everything above chose the *best* proposal; this asks whether imagining it is
    # what we should be doing at all. Returning `None` means "nothing to say", which is why the default
    # behaviour is to keep planning - the loop's disposition is unchanged and a rule has to speak up.
    #
    # Warn unlike `trace`, this is a participant, so it is handed the real thing. `trace` gets labels
    # because a watcher must not be able to steer and a rendering is all it needs; a decision is made *on*
    # structure, so giving it renderings would force it to reconstruct state from strings.
    #
    # Warn Built from what is already computed. This runs once per imagined step - hundreds of times in a
    # normal search - so anything costly here inverts the cost of what it exists to save. `open_count` is
    # carried on the candidate precisely so nothing is recomputed.
    if decide is not None:
        verdict = decide({"goal": goal, "frame": frame, "depth": depth, "function": name,
                          "bindings": bindings, "open": open_count, "trace": tr,
                          "steps": S.steps_taken(g, search), "frontier": len(S.frontier(g, search)),
                          "workbench": wb, "search": search,
                          "thread": thread, "subject": subject})
        if isinstance(verdict, Call):
            # A decision that names an action. `_honour` validates it, puts the displaced candidate back
            # on the frontier, and hands back what to imagine instead — so the rest of this function is
            # unchanged and does not know a substitution happened.
            was = name
            got = _honour(g, search, c, verdict, chosen, frame,
                          g.target(_c["trace_node"], "after")
                          if _c["trace_node"] is not None else None)
            if got is None:
                # Already carried out from this frame — spent, not ignored. Say so and let ranking run.
                if watch:
                    emit("spent", action=verdict.function, instead_of=was, depth=depth,
                         because=verdict.why)
            else:
                name, bindings, trace_node = got
                tr = S.trace_tuple(g, trace_node)
                if watch:
                    emit("decide", action=name, on=_shown(g, bindings), instead_of=was, depth=depth,
                         because=verdict.why)
            verdict = None
        if verdict is not None and verdict != EXPAND:
            verb, why_stop = verdict if isinstance(verdict, tuple) else (verdict, None)
            if verb in _UNBUILT:
                raise Undecidable(f"{verb!r} needs {_UNBUILT[verb]}; see deliberation.md")
            if verb not in _STOPS:
                raise Undecidable(f"{verb!r} is not one of {VERBS}")
            # Recorded only when a decision actually fires, which is what keeps the default path
            # byte-identical to the behaviour that existed before this seam.
            if watch:
                emit(verb, action=name, on=_shown(g, bindings), depth=depth, because=why_stop)
            return _stopped(g, search, c, verb, why_stop or f"stopped by decision: {verb}", None,
                            frame=frame, note=why_stop or f"before imagining {name}")

    steps = S.took_a_step(g, search)

    # An operator that cannot be imagined is unusable here, NOT a crash. A body whose effect is
    # behind a `DISPATCH` and which declares no `mocks` cannot be run on a workbench: `dispatch.service`
    # refuses an imagined target, which is the single most important safety property in the design and
    # must stay. But the refusal was escaping the outer loop — stranding this pursuit and, because the
    # agenda is shared, killing every other task with it. Exactly the failure `execution.step` already
    # records for `TypeViolation`: *"it reports by raising, and nothing between here and `loop.tick` caught
    # it"*. Same shape, one phase earlier.
    #
    # And skipping is the right answer rather than a patch: an operator nobody can imagine is one
    # means-ends cannot use, so the search should carry on and — if what remains is ignorance — say so.
    # That is precisely what lets `_phase_sensing` see `blocked_on_ignorance` and go and look.
    # The same containment covers a second way an imagined step can fail, and it is the general case
    # rather than an edge one: a body that does arithmetic on a slot nobody has looked at yet. `ADD`
    # meets `graph.UNKNOWN` and Python raises `TypeError`, which escaped exactly as `Imagined` did —
    # emptying the shared agenda. *An imagined step that cannot be computed is the same category as one
    # that must not be taken:* the state is unreachable, so the branch is skipped and recorded.
    #
    # It matters most where it looks like an edge case. The arithmetic that makes a domain worth
    # planning over is precisely what meets the unknown that sensing exists to resolve, so without this
    # a domain could be numeric or it could sense, and not both.
    #
    # Recorded apart from `unimaginable`, not with it. That list answers *"there was a route here and
    # nothing could imagine it"* — a capability gap. This one is *"we imagined it and the sums did not
    # work"*, which is a fact about the world's ignorance, and a reader that cannot tell them apart
    # cannot tell a missing mock from a missing observation.
    #
    # `TypeError` and nothing wider. A bare `except Exception` would turn every genuine engine fault
    # inside `W.step` into a quietly skipped branch, which is the silent acceptance this catch exists
    # to prevent — it would hide bugs in the machinery under the name of tolerating bad operators.
    try:
        nxt, _tr = W.step(g, wb, frame, name, bindings)
    except DP.Imagined as e:
        # Skipped, but never silently — recorded on the search so a report can say *"there was a route
        # here and nothing could imagine it"*. A capability gap that reads as an ordinary "no plan found"
        # is the silent-acceptance failure this project keeps catching; `_exhausted` can now name it.
        g.put(search, unimaginable=tuple(dict.fromkeys(
            (g.attr(search, "unimaginable") or ()) + (name,))))
        if watch:
            emit("unimaginable", action=name, on=_shown(g, bindings), depth=depth, because=str(e))
        return None
    except TypeError as e:
        g.put(search, uncomputable=tuple(dict.fromkeys(
            (g.attr(search, "uncomputable") or ()) + (name,))))
        if watch:
            emit("uncomputable", action=name, on=_shown(g, bindings), depth=depth, because=str(e))
        return None
    # Warn Record the real node the imagined one stands for, falling back to the copy only for something
    # that does not exist yet. Recording the copy was more literal and less truthful: an application says
    # *which function was applied to which subject*, and the subject is the block - the copy is only how we
    # imagined it. It also made the record useless to any reflective reader, because two goals open two
    # workbenches, so their entries could never refer to the same thing.
    T.applied(g, thread, name,
              {p: stands_for(g, m) for p, m in bindings.items()},
              why=f"depth {depth + 1}, {open_count} constraint(s) open", for_goal=goal)

    nview, nunder = _asked_of(g, subject, nxt)
    if watch:
        emit("imagine", action=name, on=_shown(g, bindings), depth=depth + 1,
             open=[G.describe_constraint(g, x)
                   for x in G.unmet(g, goal, view=nview, under=nunder)])
    # Warn Both halves, and liveness only here: the world must be right and the plan must have done
    # everything it was required to. A plan that reaches the state without its mandated step is not
    # finished - but it was never in violation on the way, which is why this is not a pruning test.
    if G.satisfied(g, goal, view=nview, under=nunder) and not G.outstanding(g, goal, tr):
        done = _done(g, goal, thread, wb, nxt, c["opened"], "found", steps,
                     S.refusals(g, search), search)
        if watch:
            emit("found", imagined=steps, length=done["length"],
                 plan=[(f, {p: _label(g, n) for p, n in b.items()})
                       for f, b in plan_bindings(g, done["plan"])])
        return done

    reached = S.digest(*_visited_key(g, goal, nxt, tr))
    if S.already_seen(g, search, reached):
        return None                            # this world has been imagined before, by another route
    S.mark_seen(g, search, reached, nxt)
    if depth + 1 < max_depth:
        _offer(g, search, nxt, depth + 1, trace_node, rank=rank, allow=allow, watch=watch,
               propose=propose)
    return None


def _stopped(g: Graph, search: str, c: dict, verb: str, why: str, watch,
             *, frame=None, note: str | None = None) -> dict:
    """The report for a search that was told to stop — by a `decide` verdict or by a rule that wrote
    `stop` on the search node.

    One implementation, deliberately. Two routes into "stopped" with two report builders is the drift
    shape this codebase keeps recording, and here it would be invisible: a caller cannot tell which route
    fired, so a divergence between them would look like a bug in whichever one it noticed second."""
    goal, wb = c["goal"], c["workbench"]
    frame = frame if frame is not None else W.root_frame(g, wb)
    g.put(search, done=True, found=False, how=verb)
    T.attend(g, c["thread"], goal, why=f"decided to {verb}", note=note or why)
    if watch:
        watch(dict(kind=verb, step=S.steps_taken(g, search), because=why))
    return {"found": False, "workbench": wb, "steps": S.steps_taken(g, search),
            "goal": goal, "search": search,
            "stopped": verb, "frame": frame, "plan": X.path_to(g, wb, frame),
            "refused": S.refusals(g, search), "blocked_by": S.blocked_by(g, search),
            "why": why}


def _exhausted(g: Graph, search: str, c: dict, watch) -> dict:
    goal, wb = c["goal"], c["workbench"]
    root = W.root_frame(g, wb)
    view, under = _asked_of(g, c["subject"], root)
    unmet = ", ".join(G.describe_constraint(g, x)
                      for x in G.unmet(g, goal, view=view, under=under))
    blocked = list(S.blocked_by(g, search))
    steps = S.steps_taken(g, search)
    g.put(search, done=True, found=False, how="exhausted")
    T.attend(g, c["thread"], goal, why="exhausted the search", note="no plan found")
    if watch:
        watch(dict(kind="exhausted", step=steps, imagined=steps, unmet=unmet, blocked_by=blocked))
    # An operator that was skipped is part of why nothing was found, and a report that omits it reads
    # as *"no route exists"* when the truth is *"a route existed and this could not follow it"*. Both
    # lists were being recorded and neither was ever read; naming them here is what the site that
    # writes them already claims happens.
    unimaginable, uncomputable = (g.attr(search, "unimaginable") or (),
                                  g.attr(search, "uncomputable") or ())
    why = (f"no state meeting [{unmet}] within depth {c['max_depth']} after {steps} imagined steps"
           + (f"; {len(S.refusals(g, search))} action(s) ruled out by [{', '.join(blocked)}]"
              if blocked else "")
           + (f"; could not imagine [{', '.join(unimaginable)}] (no mock for a dispatching body)"
              if unimaginable else "")
           + (f"; could not compute [{', '.join(uncomputable)}] (arithmetic on a slot nobody has "
              f"looked at)" if uncomputable else ""))
    return {"found": False, "workbench": wb, "steps": steps, "goal": goal, "search": search,
            "unmet": unmet, "refused": S.refusals(g, search), "blocked_by": tuple(blocked),
            "unimaginable": tuple(unimaginable), "uncomputable": tuple(uncomputable), "why": why}


def plan_bindings(g: Graph, plan: tuple) -> tuple:
    """A plan (a path of frames) read back as `(function, {param: real node})` per step.

    Distinct from `plan_steps`, which takes a *result dict* and returns bare function names. Naming this
    `plan_steps` too silently shadowed that one — which the first consumer calls — and every consumer of it
    began receiving a frame path it could not read. Two readers of a plan at two levels of detail is fine;
    two of them sharing a name is not.

    The first frame is the starting world, reached by nothing, so it contributes no step. Bindings point
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
            bound[g.attr(b, "param")] = stands_for(g, m) if m else None
        out.append((g.attr(tr, "function"), bound))
    return tuple(out)


def _done(g: Graph, goal, thread, wb, frame, opened, how, imagined, refused, search=None) -> dict:
    """Close the goal, and tie the moment that closed it back to the moment it was taken on."""
    subject = g.target(wb, "subject")
    under = W.image_of(g, W.mapping_for(g, frame, subject))
    found = G.witness(g, goal, view=view_in(g, frame), under=under)
    # Planned, not closed. The goal is met in an imagined frame; the world is untouched. Closing it here
    # would report success for something that has not happened.
    G.record_plan(g, goal, seen_in=frame, witness=found)

    plan = X.path_to(g, wb, frame)
    if search is not None:
        # Warn The outcome is graph data too, not only the returned dict. An ISA program driving `step`
        # reads its answer with an ordinary ATTR, exactly as it would read anything else - the report dict
        # is a convenience for Python callers, never the only place the answer exists.
        g.put(search, done=True, found=True, how=how, length=len(plan) - 1)
        g.link(search, "reached", frame)
    closing = T.attend(g, thread, goal, why=f"goal met ({how})",
                       note=f"plan is {len(plan) - 1} step(s)")
    T.connect(g, closing, opened, "achieves")
    return {"found": True, "workbench": wb, "frame": frame, "goal": goal, "witness": found,
            "plan": plan, "length": len(plan) - 1, "steps": imagined, "how": how,
            "search": search,
            "refused": refused, "blocked_by": tuple(sorted({r for _n, rs in refused for r in rs}))}


def _record_execution(g: Graph, thread: str, goal: str, plan: dict, report: dict) -> None:
    """Put what really ran on the thread, marked `done`.

    Until this existed the thread held only *planning* — every proposal considered, including abandoned
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
            args[g.attr(b, "param")] = stands_for(g, m)
        T.applied(g, thread, name, args, why="carried out for real", for_goal=goal, done=True)


def carry_out(g: Graph, goal: str, thread: str, subject: str, *,
              attempts: int = 3, **kw) -> dict:
    """PLAN, ACT, CHECK, replan — the loop closed. Returns a report of every attempt.

    `pursue` finds a plan in imagination; this is what actually does it, notices when reality disagrees, and
    goes round again from the world as it really is.

    Replanning has to come back here, not to `plan.py`. `execution.replan` chains backwards over
    return types and knows nothing about a goal's constraints — asked to recover a diverged
    "some file must exist", it answered *"listing: already satisfied"*: true, and useless. Re-pursuing the
    goal is the only recovery that can mean anything, and it needs no new state because `pursue` opens a
    fresh workbench on the current real subject. Replanning is just going round the loop again.

    A contingency is still tried first, for the reason `execution.recover` gives: an explored sibling
    is already verified against this world, a fresh plan is not. It rarely applies to a plan *this* function
    produced, because `pursue` does not fork on mock outcomes — it takes the preferred one. That is a real
    limitation, stated rather than hidden, and the reason the loop leans on replanning.

    The goal is closed only by reality. `pursue` records that a plan was *found*; nothing but a
    completed execution closes the goal."""
    data, hooks = _split_pursuit_kw(kw)
    p = open_pursuit(g, goal, thread, subject, attempts=attempts, **data)
    while pursuit_step(g, p, **hooks):
        pass
    return pursuit_report(g, p)


# --- the pursuit: plan / act / check / replan, as phases over graph-resident state --------------------
#
# `carry_out` was the last Python control loop in the engine, and the outermost one — the thing that
# decides whether to try again. Its state (which attempt, the plan in hand, the execution under way, the
# history) lived in locals, so the system could be *inside* a plan-act-check cycle and unable to say so.
# an earlier note's principle applied without exception: the pursuit is a node, one tick is one primitive
# STEP, and `carry_out` is a driver over it exactly as `Machine.run` is over `tick` and `execute` over
# `execution.step`.
#
# A tick of a pursuit is not "one attempt". An attempt contains a whole search and a whole replay,
# and an opcode-sized step is the only size that makes "stop between any two" mean anything. So a pursuit
# holds a current sub-task — a `search` while planning, a `replay` while acting — and advancing the
# pursuit advances that sub-task by one primitive step, changing phase only when it finishes. That is what
# makes the whole loop uniform: every level down from here is already steppable.
#
# The phases are data on the node rather than a Python state variable, so `describe_pursuit` can say
# what the system is in the middle of without having been watching.

PLANNING, ACTING, RECOVERING, CHECKING, SETTLED = "planning", "acting", "recovering", "checking", "done"
#: A pursuit that cannot PLAN because it does not know — see `_phase_sensing`.
SENSING = "sensing"

_PURSUIT_DATA = ("max_steps", "max_depth", "guided")


def _split_pursuit_kw(kw: dict) -> tuple:
    """Bounds are data and live on the node; `rank`/`allow`/`trace`/`decide` are Python callables and are
    passed per call. Same split as `search.context`, for the same reason: a callable cannot live in a
    graph, and everything that can, must."""
    return ({k: v for k, v in kw.items() if k in _PURSUIT_DATA},
            {k: v for k, v in kw.items() if k not in _PURSUIT_DATA})


def open_pursuit(g: Graph, goal: str, thread: str, subject: str, *, attempts: int = 3,
                 max_steps: int = 60, max_depth: int = 6, guided: bool = True) -> str:
    """A pursuit of `goal`, at attempt 0, about to plan. Nothing has happened yet."""
    p = g.mint("pursuit", at=0, attempts=attempts, phase=PLANNING, done=False,
               max_steps=max_steps, max_depth=max_depth, guided=guided)
    g.link(p, "goal", goal)
    g.link(p, "thread", thread)
    g.link(p, "subject", subject)
    return p


def _attempt(g: Graph, p: str, **fields) -> str:
    a = g.mint("attempt", **fields)
    g.link(p, "attempt", a)
    return a


def _history(g: Graph, p: str) -> tuple:
    return tuple({k: v for k, v in g.attrs[a].items() if k != "kind"} for a in g.targets(p, "attempt"))


def pursuit_report(g: Graph, p: str) -> dict:
    """`carry_out`'s report, rendered from the pursuit. Unchanged in shape — this is a reading of the node,
    not a second record."""
    goal, subject = g.target(p, "goal"), g.target(p, "subject")
    history = _history(g, p)
    if g.attr(p, "done"):
        return {"done": True, "attempts": history, "witness": g.target(p, "witness"),
                "tries": g.attr(p, "at", 0) + 1, "pursuit": p}
    # The last attempt's own account, when it has one. Every attempt records *why* it gave up and none
    # of it reached this string, so a pursuit that failed for a nameable reason — nothing could look at
    # the subject you nominated, an operator could not be imagined, arithmetic met an unlooked-at slot —
    # reported only that the constraints were still false, which is true of every failure and
    # distinguishes none of them. The reason was in `attempts` all along; `why` is where a reader looks.
    said = next((a["why"] for a in reversed(history) if a.get("why")), None)
    return {"done": False, "attempts": history, "tries": len(history), "pursuit": p,
            "why": f"{len(history)} attempt(s) did not reach ["
                   + "; ".join(G.describe_constraint(g, c)
                               for c in G.unmet(g, goal, under=subject)) + "]"
                   + (f" — {said}" if said else "")}


def describe_pursuit(g: Graph, p: str) -> str:
    """What the system is in the middle of, in one line — the answer the outer loop's test demands of
    every task it can be stopped inside."""
    phase = g.attr(p, "phase")
    label = g.attr(g.target(p, "goal"), "label") or g.target(p, "goal")
    at = g.attr(p, "at", 0) + 1
    sub = g.target(p, "search") if phase == PLANNING else g.target(p, "replay")
    detail = ""
    if phase == PLANNING and sub is not None:
        detail = f" ({S.steps_taken(g, sub)} states imagined)"
    elif sub is not None:
        detail = f" (step {g.attr(sub, 'at', 0)} of {g.count(sub, 'frame') - 1})"
    return f"pursuing {label!r}, attempt {at}: {phase}{detail}"


def pursuit_step(g: Graph, p: str, **hooks) -> bool:
    """One primitive step of the whole plan-act-check-replan loop. `True` while there is more to do.

    Exactly one of these happens per call: one imagined state, one real action, or one phase transition.
    A transition costs a tick of its own rather than being folded into the step that caused it, because
    *"the plan is in hand and nothing has been done yet"* is a state the system may legitimately be stopped
    in — it is the last moment before anything becomes irreversible."""
    phase = g.attr(p, "phase")
    if phase == SETTLED:
        return False
    return _PHASES[phase](g, p, **hooks)


def _phase_planning(g: Graph, p: str, **hooks) -> bool:
    goal, thread, subject = (g.target(p, "goal"), g.target(p, "thread"), g.target(p, "subject"))
    s = g.target(p, "search")
    if s is None:
        g.link(p, "search", open_planning(
            g, goal, thread, subject, max_steps=g.attr(p, "max_steps"),
            max_depth=g.attr(p, "max_depth"), guided=g.attr(p, "guided"),
            rank=hooks.get("rank"), allow=hooks.get("allow"), trace=hooks.get("trace")))
        return True

    out = step(g, s, **hooks)
    if out is None:
        return True                              # one imagined state; still planning
    if not out["found"]:
        # ACTING on an unfinished PLAN. A search can fail for two very different reasons, and
        # collapsing them was the gap: *"there is no route"* is defeat, but *"I cannot plan this until I
        # go and look"* is a third outcome, and the whole reason an outer loop was wanted — the plan
        # is not the only thing a goal may need next. `goal.blocked_on_ignorance` is the test, and it is
        # deliberately strict: a plan must bottom out in ignorance, not merely touch it, or the agent
        # looks in every box.
        if _looker_for(g, goal, subject) is not None:
            g.put(p, phase=SENSING)
            return True
        gap = _sensing_gap(g, goal, subject)
        _attempt(g, p, attempt=g.attr(p, "at", 0), planned=False,
                 why=f"{out['why']}; {gap}" if gap else out["why"])
        g.put(p, phase=SETTLED)
        return False

    T.attend(g, thread, goal, why=f"attempt {g.attr(p, 'at', 0) + 1}: carrying out the plan",
             note=" then ".join(plan_steps(g, out)) or "(nothing)")
    g.link(p, "plan_frame", out["frame"])
    g.link(p, "replay", X.open_execution(g, out["workbench"], out["frame"]))
    g.put(p, phase=ACTING)
    return True


def _phase_acting(g: Graph, p: str, **_hooks) -> bool:
    r = g.target(p, "replay")
    if X.step(g, r):
        return True                              # one real action; still acting
    report = X.report_of(g, r)
    plan = _plan_of(g, p)
    _record_execution(g, g.target(p, "thread"), g.target(p, "goal"), plan, report)
    a = _attempt(g, p, attempt=g.attr(p, "at", 0), planned=True, steps=plan_steps(g, plan),
                 ran=report["ran"], completed=report["completed"])
    g.link(p, "record", a)

    if report["completed"]:
        g.put(p, phase=CHECKING)
        return True
    # A contingency is tried before replanning, on evidence rather than taste: an explored sibling is
    # already verified against this world and a fresh plan is not (`execution.recover`).
    resumed = X.resume_replay(g, report)
    if resumed is None:
        g.put(a, diverged=X.report(g, report))
        g.put(p, phase=CHECKING)
        return True
    g.link(p, "replay", resumed)                 # the pursuit's current replay is now the contingency
    g.put(p, phase=RECOVERING)
    return True


def _phase_recovering(g: Graph, p: str, **_hooks) -> bool:
    r = g.targets(p, "replay")[-1]
    if X.step(g, r):
        return True
    report, a = X.report_of(g, r), g.target(p, "record")
    if report["completed"]:
        g.put(a, recovered="contingency", completed=True, ran=report["ran"])
    else:
        # The divergence reported is the original one. A contingency that also failed does not replace
        # the account of what went wrong first — that is what the next attempt has to reason from.
        g.put(a, diverged=X.report(g, X.report_of(g, g.targets(p, "replay")[0])))
    g.put(p, phase=CHECKING)
    return True


def _looker_for(g: Graph, goal: str, subject: str):
    """An observing function that could reduce this goal's ignorance, or `None`.

    Only when the goal bottoms out in ignorance (`goal.blocked_on_ignorance`), which is the test
    that document already specifies: one unknown slot beside three genuinely false constraints is world
    work, not a reason to go looking.

    The planner is blind here by construction, which is why this does not plan. A search reaches
    this state precisely when nothing it can select establishes what is unknown — an operator whose whole
    effect is on the far side of a `DISPATCH` reads as establishing nothing (`establishes`), so it can
    never be chosen by means-ends. Sensing therefore selects directly: an applicable single-parameter
    function whose body dispatches a tool registered as only looking.

    `selection.candidates(skip_applied=True)` is the termination guard, and it is structural rather than
    a counter: a function already applied to this subject is not offered again, so a pursuit cannot look
    the same way twice and loop for ever."""
    if not G.blocked_on_ignorance(g, goal):
        return None
    return _looker_on(g, subject)


def _looker_on(g: Graph, node: str):
    """An applicable single-parameter function that only looks, selected *on* `node`. No goal test.

    Split out from `_looker_for` so the same selection can be asked about a node other than the
    pursuit's subject — which is the only way to tell *"nothing can look"* from *"nothing can look at
    the thing you nominated"*. See `_sensing_gap`."""
    from . import dispatch as DP, selection as SEL
    for c in SEL.candidates(g, node):
        name = c["function"] if isinstance(c, dict) else c
        _params, program = fn.load(g, name)
        for i in program:
            if getattr(i, "op", None) != "DISPATCH":
                continue
            tool = next((a for a in i.args if isinstance(a, str)), None)
            if tool is not None and DP.observes(g, tool):
                return name
    return None


def _sensing_gap(g: Graph, goal: str, subject: str):
    """*You passed a container.* — or `None` if that is not what happened.

    The pursuit's subject carries two different meanings and satisfies one of them silently. Planning
    searches *under* a subject, which is why passing the shop is right and works. Sensing selects *on*
    it — `_looker_on` walks `selection.candidates(g, subject)` — so a container has no applicable
    single-parameter looker and can never look, no matter what sits inside it. Both rules are right on
    their own; what is wrong is that the same argument satisfies one and quietly fails the other.

    And the failure is indistinguishable from a genuinely impossible goal: the report said *"1
    attempt(s) did not reach [desk.rares >= 3]"*, which is true of both and tells a reader nothing.

    So this names it and changes nothing else. Making `_looker_for` search under the subject was the
    alternative and is worse: sensing would then dispatch at a node the caller never nominated, quietly
    widening what an agent may go and touch. A refusal that names the reason cannot be wrong; a fix
    that guesses the subject can.

    `workbench.reachable` is *the* copy boundary — the same "under" planning uses — so this reports the
    relationship that actually holds rather than a second opinion about what is inside what."""
    if not G.blocked_on_ignorance(g, goal) or _looker_on(g, subject) is not None:
        return None
    for node in W.reachable(g, subject):
        if node == subject:
            continue
        name = _looker_on(g, node)
        if name is not None:
            return (f"blocked on what is not known, and nothing can look AT {_label(g, subject)} — "
                    f"though {name!r} could look at {_label(g, node)}, which is under it. Sensing "
                    f"selects on the subject; planning searches under it. Pursue "
                    f"{_label(g, node)} to sense it")
    return None


def _phase_sensing(g: Graph, p: str, **_hooks) -> bool:
    """Look, for real, and then replan from scratch.

    The old search is discarded, not resumed, and that is the user's specification rather than an
    implementation convenience: what we just learned may invalidate the plan altogether, so resuming a
    frontier built in ignorance would extend reasoning done before the facts arrived. Replanning is the
    honest move, and it is the same argument `execution.recover` already makes for preferring a verified
    sibling over a fresh plan — evidence over taste, in the other direction.

    One look per tick, like every other phase: this is a real dispatch and reaches the world."""
    goal, thread, subject = (g.target(p, "goal"), g.target(p, "thread"), g.target(p, "subject"))
    name = _looker_for(g, goal, subject)
    if name is None:
        _attempt(g, p, attempt=g.attr(p, "at", 0), planned=False,
                 why=(_sensing_gap(g, goal, subject)
                      or "blocked on what is not known, and nothing here can look"))
        g.put(p, phase=SETTLED)
        return False
    T.attend(g, thread, goal, why="cannot plan without looking", note=name)
    fn.invoke(g, name, {fn.subject_param(g, name): subject})
    g.put(p, sensed=(g.attr(p, "sensed", ()) or ()) + (name,))
    # The search is dropped so the next planning tick opens a fresh one against what is now known.
    old = g.target(p, "search")
    if old is not None:
        g.unlink(p, "search", index=0)
    g.put(p, phase=PLANNING)
    return True


def _phase_checking(g: Graph, p: str, **_hooks) -> bool:
    goal, thread, subject = (g.target(p, "goal"), g.target(p, "thread"), g.target(p, "subject"))
    a = g.target(p, "record")
    if a is not None and g.attr(a, "completed") and G.satisfied(g, goal, under=subject):
        found = G.witness(g, goal, under=subject)
        G.close_goal(g, goal, found)
        T.attend(g, thread, goal, why="done for real", note=G.describe(g, goal))
        g.link(p, "witness", found)
        g.put(p, done=True, phase=SETTLED)
        return False

    at = g.attr(p, "at", 0) + 1
    if at >= g.attr(p, "attempts", 1):
        T.attend(g, thread, goal, why="gave up", note=f"after {at} attempt(s)")
        g.put(p, phase=SETTLED)
        return False
    # Round again, and it needs no new state: `open_planning` opens a fresh workbench on the current
    # real subject, so replanning IS going round the loop. The sub-tasks are released rather than kept,
    # because "which search am I in" must have one answer.
    for label in ("search", "replay", "plan_frame", "record"):
        while g.count(p, label):
            g.unlink(p, label, index=0)
    g.put(p, at=at, phase=PLANNING)
    return True


_PHASES = {PLANNING: _phase_planning, ACTING: _phase_acting,
           RECOVERING: _phase_recovering, CHECKING: _phase_checking, SENSING: _phase_sensing}


def _plan_of(g: Graph, p: str) -> dict:
    """The bits of a `pursue` report that `_record_execution` and `plan_steps` read, rebuilt from the
    pursuit. Not a stored copy of the report — a rendering, so it cannot fall out of step with it."""
    s = g.target(p, "search")
    wb, frame = g.target(s, "workbench"), g.target(p, "plan_frame")
    return {"found": True, "frame": frame, "workbench": wb, "plan": X.path_to(g, wb, frame),
            "how": g.attr(s, "how"), "search": s, "goal": g.target(p, "goal")}


def follow(g: Graph, goal: str, thread: str, subject: str, **kw) -> dict:
    """Carry out a decomposed goal by working its subgoals in `then` order.

    An earlier claim, that *"a procedure is this shape plus one sequencing edge"*, held structurally: two ordered subgoals ran through
    `carry_out` unchanged and reality came out right. What was absent was not structure but drive;
    nothing walked the order. This is that walk, and it is deliberately thin because the probe showed
    everything underneath already worked.

    Force decides what happens when a step fails, and it is the whole distinction between a method
    and a procedure (`docs/deliberation.md`:

    * `ADVISORY` (a method) — the decomposition was a *suggestion about how*. If it does not work out,
      fall back to searching for the parent goal directly. Incompleteness is fine; the author was helping.
    * `MANDATORY` (a procedure) — the decomposition was *the sanctioned way*. Falling back would be
      improvising, so this refuses instead. For a procedure, *"could not do it"* is a better answer
      than *"did it another way"*, and that inverts every other reflex in this module — `carry_out`
      replans, `recover` reaches for contingencies. The reflex is suppressed here on purpose.

    A refusal is not a failure to find a plan, and they must not be reported alike: one says the
    world would not permit it, the other says we were not permitted to try. `REFUSE` carries the step that
    stopped it and the reason, which is what an audit of a regulated run actually needs.

    Advisory fallback cannot resurrect a MANDATORY parent. Force is read from the parent whose
    decomposition this is, never from the step that failed — a mandatory procedure containing an advisory
    sub-method must not become improvisable because the failure happened one level down."""
    steps = G.sequence(g, goal)
    if not steps:
        # Not decomposed at all — the vacuity trap an earlier note records. Refusing to treat this
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
    """The goal-level decision point: decompose, or search? The top of the loop for anything with
    authored methods.

    This is deliberately NOT inside `pursue`'s search loop, and the frequency is the reason
    (see `docs/deliberation.md`) A method is consulted once per goal — few, so it may be expensive — while
    the per-step `decide` hook runs hundreds of times and must stay structural. Putting method matching in
    the inner loop would invert the cost of the thing it exists to save, which is a mistake this project
    has paid for once already.

    Precedence is declaration order, and the first applicable method wins. No weights, nothing to
    tune — the same free ordering `mock` and `guideline` already use.

    Falling back is what keeps authority safe. A method prunes by replacing enumeration, so a
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
    """A readable handle for a node in a plan. A `label` is a convenience for *display only* — nodes are
    nameless and identity is never a name (an earlier note records that lesson at length)."""
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


# The planner registers itself as a primitive, and this is the whole of the kernel-boundary fix.
# `isa.py` used to import this module so that two opcodes could call these two functions — so the
# instruction set knew what a plan was, and a Rust port would have had to port the planner in order to
# implement two instructions (`docs/execution-model.md`). The dependency now points the
# other way: the kernel looks a name up in a table it does not populate, and this is where it is put.
#
# The registration lives here, beside what it registers, and never in `native.py` — a table of names in
# the kernel would be the same leak with an extra hop.
#
# `plan`'s operand order is the old `PLAN R(dst) F(goal) F(subject) F(thread)`, so a body translates
# mnemonic-for-name with the operands untouched.
N.register("plan", lambda g, _act, goal, subject, thread: open_planning(g, goal, thread, subject))
N.register("plan_step", lambda g, _act, search: step(g, search) is None)


__all__ = ["proposals", "state_of", "establishes", "reads", "reports_on", "confirms",
           "role_node", "relevance", "view_in",
           "open_planning", "step", "Call", "Undecidable",
           "EXPAND", "DECOMPOSE", "COMMIT", "SENSE", "REFUSE", "VERBS", "SENSING",
           "pursue", "carry_out", "plan_steps", "plan_bindings", "describe"]

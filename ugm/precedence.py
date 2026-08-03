"""Precedence — which of two rules decides, when both would speak.

Declaration order was the whole answer, and it was defended on the grounds that *"weights are the
thing that would need tuning, and there is nothing to tune in an order"*. That is still right about
weights and was wrong about orders: declaration order is *an* order, silently, and a reader could
not ask why one criterion outranked another because nothing had been said.

So the ranking is authored. A tie-break rule is an ordered list of stages, each naming one
comparison; the first stage that decides a pair, decides it. What must not be in Python is the
*order of the stages*, because that is a decision about how this domain arbitrates, and a
hardcoded one is the island pattern `docs/limits.md` names — engine state in a Python structure that
nothing can compute about. What must be in Python is each individual comparison, exactly as
`path.reaches` and `types.subsumes` are: a port re-implements *how to compare two forces* and must
never re-decide *whether force is consulted before specificity*.

Four stages, a closed vocabulary, and each new member is a decision about a comparator rather than
a string somebody adds — the discipline `consequent.py` already applies to its tags.

| stage | decides by | order |
|---|---|---|
| `authority` | who said it — `norm.outranks`, transitive over `authority_over` | partial |
| `force` | `must` > `should` > `could` | total preorder |
| `specificity` | whose conditions are tighter, structurally | partial |
| `random` | a stable hash of the seed and the node | total |

**Nothing is attributed to nobody.** A rule with no declared source is not a rule with a missing
field; it is `experience` — *"experience says"* — which is an ordinary agent node, so the authority
comparison is always well formed and a domain can say what learned advice is worth by writing
`discourse.authority(someone, "experience")`. Whether experience is outranked is world data and is
deliberately not installed here: baking it would be this module's own sin.

**The last stage must be total.** Stages compose lexicographically, so if the final one can answer
*undecided* the ranking is not a ranking and two rules sit in an order nobody chose — which is the
defect this module exists to remove. Refused at authoring time.

**The composed order can be non-transitive**, and that is stated rather than hidden. Two of the four
stages are partial, and a lexicographic composition of a partial order with a tie-break can produce
`a > b > c > a`. `sorted` then yields *a* linearisation rather than *the* linearisation. This is
acceptable here only because it is declared: the standing lesson from the irreproducible search is
that an *undeclared* tie-break is the bug, not that arbitrariness is.

See `docs/deliberation.md`.
"""
from __future__ import annotations

import functools
import hashlib

from . import types as TY
from .graph import Graph

KINDS = ("tie_break", "stage")

#: The agent a rule is attributed to when nobody claimed it. A real node, not a sentinel — it is
#: something a norm can outrank, an utterance can quote, and a reader can ask about.
EXPERIENCE = "experience"

#: The closed comparator vocabulary. Adding one means writing its comparator below.
BY_AUTHORITY, BY_FORCE, BY_SPECIFICITY, BY_RANDOM = "authority", "force", "specificity", "random"
STAGES = (BY_AUTHORITY, BY_FORCE, BY_SPECIFICITY, BY_RANDOM)

#: Stages that decide every pair. At least one must sit last, or the ranking has an undeclared end.
TOTAL = frozenset({BY_RANDOM})

#: Strengths, strongest first. `must` is also the failure axis (`criterion.force_of`); `should` and
#: `could` differ only in precedence, which is why this is a separate list from `goal.FORCES`.
MUST, SHOULD, COULD = "must", "should", "could"
STRENGTHS = (MUST, SHOULD, COULD)

RULE, STAGE, SOURCE = "tie_break", "stage", "source"


class Unorderable(ValueError):
    """A tie-break rule that cannot rank. Refused where it is written, never discovered at run time."""


# --- authoring ----------------------------------------------------------------------------------------
def open_rule(g: Graph, label: str = "tie-break", *, seed: int = 0) -> str:
    r = g.mint(RULE, label=label, seed=seed)
    g.link("root", "has", r)          # a real thing: it can be quoted, doubted, withdrawn
    return r


def add_stage(g: Graph, r: str, name: str, *, run: str | None = None) -> str:
    """Append one comparison. `name` is from `STAGES`, or `run` names a stored function.

    **A stage may be a function, and that is what keeps the vocabulary from being a Python decision.**
    The four shipped comparisons are primitives for the same reason `path.reaches` is one, but a domain
    that ranks by something else — seniority, recency, how often a rule has been right — must not have to
    edit this module to say so. A function stage is called with the two rules and answers which comes
    first, so the closed set is the set that *ships*, never the set that is *possible*.

    Its termination is the interpreter's, not this module's: a stage that loops raises at the step limit
    the way any other program does. That is `docs/limits.md`'s honest stand-in rather than an answer, and
    it is why the *shipped* comparators are total by construction — the default must not depend on it."""
    if run is not None:
        from . import function as fn
        if fn.find(g, run) is None:
            raise Unorderable(f"stage names the function {run!r}, which is not in this library")
        s = g.mint(STAGE, by=name or run, run=run)
    else:
        if name not in STAGES:
            raise Unorderable(f"{name!r} is not a comparison; the shipped vocabulary is {STAGES}. "
                              f"For anything else, name a function (`run <fn>`) rather than adding a word here.")
        if name in tuple(g.attr(x, "by") for x in g.targets(r, STAGE)):
            raise Unorderable(f"a stage consulted twice cannot change its mind: {name!r}")
        s = g.mint(STAGE, by=name)
    g.link(r, STAGE, s)
    return s


def seal_rule(g: Graph, r: str) -> str:
    """Refuse a rule that cannot rank — at authoring time, never at run time.

    A function stage cannot be shown to be total, so it may not sit last. That is not distrust of the
    author: an incomplete order is invisible until the one pair it cannot separate turns up, which is
    exactly the failure a closure check exists to convert into a refusal."""
    stages = tuple(g.attr(s, "by") for s in g.targets(r, STAGE))
    if not stages:
        raise Unorderable("a tie-break rule with no stages ranks nothing")
    last = g.targets(r, STAGE)[-1]
    if g.attr(last, "run") is not None or stages[-1] not in TOTAL:
        raise Unorderable(
            f"the last stage must decide every pair, and {stages[-1]!r} may answer 'undecided'. "
            f"End with one of {tuple(sorted(TOTAL))}, or two rules sit in an order nobody chose.")
    return r


def declare(g: Graph, stages: tuple, *, seed: int = 0, label: str = "tie-break") -> str:
    """Author the ranking in one call. `stages` is ordered, from `STAGES`, ending in a total one.

    `seed` is recorded rather than drawn, so a run that chose arbitrarily among equals can still be
    replayed by anyone holding the graph. That costs one attribute and constrains no behaviour: the point
    is not that the choice is meaningful, it is that it is *attributable* after the fact."""
    r = open_rule(g, label, seed=seed)
    for s in stages:
        add_stage(g, r, s)
    return seal_rule(g, r)


def rule(g: Graph):
    """The tie-break rule in force, or `None`. Withdrawn ones are skipped, like every other enumerator."""
    from .discourse import live
    found = live(g, g.of_kind(RULE))
    return found[-1] if found else None


def stage_nodes(g: Graph) -> tuple:
    """The authored stages as nodes, in order — what `compare` walks."""
    r = rule(g)
    return () if r is None else g.targets(r, STAGE)


def stages_of(g: Graph) -> tuple:
    """The authored stage names, or `()` when nothing has been authored.

    Empty is not a defective answer and does not fall back to a built-in list. With no tie-break rule
    the order is the order the rules were minted in, which is substrate rather than policy — the graph
    preserves insertion order, so declaration order costs nothing and decides nothing it was not already
    deciding. Installing a Python default here is what the module docstring forbids."""
    return tuple(g.attr(s, "by") for s in stage_nodes(g))


def seed_of(g: Graph) -> int:
    r = rule(g)
    return 0 if r is None else g.attr(r, "seed", 0)


def describe(g: Graph) -> str:
    r = rule(g)
    if r is None:
        return "no tie-break rule: rules rank in the order they were declared"
    return (f"tie-break {g.attr(r, 'label')!r} (seed {g.attr(r, 'seed', 0)}): "
            + " then ".join(stages_of(g)))


# --- attribution --------------------------------------------------------------------------------------
def attribute(g: Graph, node: str, by=None) -> str:
    """Record who a rule came from. Absent means `experience`, which is a name rather than a blank.

    **Replaces rather than appends**, and that is not tidiness. A rule is opened at the default
    attribution and a later `by` line refines it, so appending left two sources on one rule with
    `source_of` reading whichever came first — the default — and silently discarding what the author
    actually wrote. Measured: every `by` line was ignored. One source is also the honest cardinality;
    two agents independently vouching for one rule is a different claim, and there is no form for it."""
    from .discourse import speaker
    who = by if by is not None and by in g.nodes else speaker(g, by or EXPERIENCE)
    while g.target(node, SOURCE) is not None:
        g.unlink(node, SOURCE, index=0)
    g.link(node, SOURCE, who)
    return who


def source_of(g: Graph, node: str) -> str:
    """Who said it. Never `None`: an unattributed rule is `experience`, minted on demand.

    A reader asking *"on whose word?"* must always get an answer, or the authority comparison is
    undefined for exactly the rules most likely to be wrong."""
    from .discourse import speaker
    got = g.target(node, SOURCE)
    return got if got is not None else speaker(g, EXPERIENCE)


def strength_of(g: Graph, node: str) -> str:
    return g.attr(node, "strength", SHOULD)


# --- the comparisons ----------------------------------------------------------------------------------
# Each answers -1 (a first), 1 (b first), or 0 (undecided). Zero is a real answer and means *this
# comparison has nothing to say about this pair*, which is what lets the next stage speak — the same
# shape `criterion.speaks` uses for silence.
def _by_authority(g: Graph, a: str, b: str) -> int:
    from . import norm as NM
    sa, sb = source_of(g, a), source_of(g, b)
    if sa == sb:
        return 0
    if NM.outranks(g, sa, sb):
        return -1
    return 1 if NM.outranks(g, sb, sa) else 0


def _by_force(g: Graph, a: str, b: str) -> int:
    ia, ib = STRENGTHS.index(strength_of(g, a)), STRENGTHS.index(strength_of(g, b))
    return (ia > ib) - (ia < ib)


def _by_specificity(g: Graph, a: str, b: str) -> int:
    covers_b, covers_a = _covers(g, a, b), _covers(g, b, a)
    if covers_b == covers_a:
        return 0                          # mutually tight, or neither comparable — both are silence
    return -1 if covers_b else 1


def _by_random(g: Graph, a: str, b: str) -> int:
    """A stable hash, never `random.shuffle` and never `hash()`.

    `hash()` on a string is salted per process, and this repo has already been bitten by a
    computation whose answer depended on the interpreter's hash seed. A digest of the recorded seed and
    the node's own name is arbitrary, total, and identical on every machine that holds the graph."""
    ka, kb = _digest(g, a), _digest(g, b)
    return (ka > kb) - (ka < kb)


def _digest(g: Graph, node: str) -> str:
    return hashlib.sha256(f"{seed_of(g)}:{node}".encode()).hexdigest()


_COMPARE = {BY_AUTHORITY: _by_authority, BY_FORCE: _by_force,
            BY_SPECIFICITY: _by_specificity, BY_RANDOM: _by_random}


# --- specificity --------------------------------------------------------------------------------------
def _covers(g: Graph, a: str, b: str) -> bool:
    """Is every demand `b` makes also made, at least as tightly, by `a`?

    Keying differs first: two rules that watch different constraints never compete for a situation, so
    comparing their conditions would be answering a question nobody asked.

    Undecidable comparisons answer *no*, and the direction is `types.subsumes`' and taken for its
    reason: a false negative loses an ordering the author could have had, a false positive claims a
    precedence the author never wrote. Losing an ordering is recoverable; an invented one is not."""
    if (g.attr(a, "wants_sort"), g.attr(a, "wants_label")) != \
       (g.attr(b, "wants_sort"), g.attr(b, "wants_label")):
        if g.attr(a, "wants_sort") != g.attr(b, "wants_sort"):
            return False
        # Same sort, and only one names a label: naming one is strictly narrower.
        if g.attr(b, "wants_label") is not None:
            return False
    tests_a, tests_b = g.targets(a, "test"), g.targets(b, "test")
    if not all(any(_at_least_as_tight(g, ta, tb) for ta in tests_a) for tb in tests_b):
        return False
    # A drawn role is a further demand — the candidate has to exist — so a rule that draws is narrower
    # than one that does not. Counting is enough: a draw's own filter is written as ordinary tests,
    # which the line above has already compared.
    return len(g.targets(a, "draw")) >= len(g.targets(b, "draw"))


def _at_least_as_tight(g: Graph, ta: str, tb: str) -> bool:
    """Does one condition demand everything another demands, and possibly more?

    Two refinements are real rather than decorative, and both reuse machinery that already exists:
    a subtype demanded where a supertype would do is tighter (`types.subsumes`), and a direct link
    demanded where a transitive one would do is tighter (`x on y` versus `x on+ y`). Everything else is
    equality, because an equality test cannot be partially satisfied."""
    sort = g.attr(ta, "sort")
    if sort != g.attr(tb, "sort") or bool(g.attr(ta, "negated")) != bool(g.attr(tb, "negated")):
        return False
    if g.attr(ta, "left") != g.attr(tb, "left"):
        return False
    if sort == "exists":
        return True
    if sort == "type":
        want_a, want_b = g.attr(ta, "label"), g.attr(tb, "label")
        return want_a == want_b or TY.subsumes(g, want_b, want_a)
    if sort == "attr":
        return (g.attr(ta, "key"), g.attr(ta, "value")) == (g.attr(tb, "key"), g.attr(tb, "value"))
    if sort == "link":
        if (g.attr(ta, "label"), g.attr(ta, "right")) != (g.attr(tb, "label"), g.attr(tb, "right")):
            return False
        return bool(g.attr(tb, "transitive")) or not g.attr(ta, "transitive")
    if sort == "wants":
        return (g.attr(ta, "want_sort"), g.attr(ta, "label")) == \
               (g.attr(tb, "want_sort"), g.attr(tb, "label"))
    return False


# --- ranking ------------------------------------------------------------------------------------------
def _apply(g: Graph, stage: str, a: str, b: str) -> int:
    run = g.attr(stage, "run")
    return _by_function(g, run, a, b) if run else _COMPARE[g.attr(stage, "by")](g, a, b)


def _by_function(g: Graph, run: str, a: str, b: str) -> int:
    """A stored function as a comparison. It answers with the rule that comes first, or nothing.

    Returning a *node* rather than a sign is deliberate. A comparator that answers -1/0/1 makes the
    author hold a convention in their head, and getting it backwards produces a ranking that is wrong in a
    way nothing can detect; answering *"this one"* cannot be inverted by mistake. It is also the shape
    every other authored decision here already has — `criterion.speaks` returns the call or nothing."""
    from . import function as fn
    _focus, regs = fn.invoke(g, run, {"a": a, "b": b})
    got = regs.get("result")
    return -1 if got == a else 1 if got == b else 0


def compare(g: Graph, a: str, b: str) -> int:
    """Apply the authored stages in order; the first that decides, decides. `0` when none does."""
    for stage in stage_nodes(g):
        got = _apply(g, stage, a, b)
        if got:
            return got
    return 0


def deciding_stage(g: Graph, a: str, b: str):
    """Which stage put `a` before `b`, and which way — `(stage, winner)`, or `None` if none spoke.

    `governing` answers *"why this rule and not that one?"* at the level of conditions. Once precedence
    is computed rather than read off the source text, the same question arises one level up, and a
    ranking that cannot say which stage decided it is exactly the opaque predicate this design refuses
    everywhere else."""
    for stage in stage_nodes(g):
        got = _apply(g, stage, a, b)
        if got:
            return g.attr(stage, "by"), (a if got < 0 else b)
    return None


def rank(g: Graph, nodes) -> tuple:
    """The rules in precedence order. Insertion order is preserved where nothing decides.

    `sorted` is stable, so with no tie-break rule authored this is exactly the declaration order it has
    always been — the ranking is opt-in, and installing it changes nothing until somebody says how."""
    nodes = tuple(nodes)
    if not stages_of(g) or len(nodes) < 2:
        return nodes
    return tuple(sorted(nodes, key=functools.cmp_to_key(lambda a, b: compare(g, a, b))))


def describe_ranking(g: Graph, nodes) -> str:
    """The order, and what decided each adjacent pair — the reader's window onto a computed precedence."""
    ordered = rank(g, nodes)
    if not ordered:
        return "nothing to rank"
    lines = [describe(g)]
    for a, b in zip(ordered, ordered[1:]):
        got = deciding_stage(g, a, b)
        why = "declaration order" if got is None else f"{got[0]}"
        lines.append(f"  {g.attr(a, 'label')!r} before {g.attr(b, 'label')!r} — {why}")
    return "\n".join(lines)


__all__ = ["EXPERIENCE", "STAGES", "TOTAL", "STRENGTHS", "MUST", "SHOULD", "COULD",
           "BY_AUTHORITY", "BY_FORCE", "BY_SPECIFICITY", "BY_RANDOM", "Unorderable",
           "declare", "open_rule", "add_stage", "seal_rule", "rule", "stages_of", "stage_nodes",
           "seed_of", "describe", "attribute", "source_of",
           "strength_of", "compare", "deciding_stage", "rank", "describe_ranking"]

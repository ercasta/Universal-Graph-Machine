"""Constructions — an utterance becomes something the engine can run, by proposal and selection.

This is the front door, rebuilt. `intake.py` is a **parser**: it rewrites an utterance into constituents
by a fixed grammar, before any knowledge is consulted, and `docs/comparison.md` argues at length that
this is the one place the project does the thing it forbids everywhere else — decomposition ahead of the
web, which is Fodor's error at the front door. The replacement is Hobbs' shape: interpretation *is*
inference, a reading is a **candidate**, and choosing between readings is **selection** by authored
preference. Which is to say: exactly what `proposals` → `relevance` → `tie_break` already is for actions.

**A construction is not a new kind of thing.** It has the three parts a criterion has, and it reuses
them rather than resembling them:

| | a criterion | a construction |
|---|---|---|
| the **address** — where to look | `wants <sort> <label>`, over the goal's unmet constraints | `addresses <sort> <label>`, over an utterance's tokens |
| the **tests** — what must hold there | `criterion.test` | `criterion.test`, the same nodes |
| the **consequent** — what it means | `do <fn> …` | `builds <fn> …` |

So specificity ordering (`precedence._covers` reads exactly `wants_sort` / `wants_label` and the tests),
the condition reader, and the *why-this-and-not-that* explanation all arrive already written. That is the
argument `function.guard` already makes for tests serving two families — *"the condition language cannot
tell a role from a parameter"* — carried one family further: it cannot tell a token from a constraint
either.

⭐ **The address is load-bearing, and that is measured rather than assumed.** The guard-address probe
(`docs/HANDOFF.md`) blanked the addressing half of three criteria: at one off-topic constraint the search
found a *worse* plan, at two it found **none**, and bindings went 11 → 1153. An address is not an index
bolted onto a condition; it is half the condition. A construction that does not say what it looks at does
not merely get slower.

**Word order is form, not grammar.** A construction reaches its other roles by walking the token chain
(`some theme in head by ^next`), and the filter that picks the right one is written as ordinary `when`
lines. That is `criterion.draw`'s argument arriving in a second family: *"the same block, for a stated
reason"* — a candidate introduced as a role and ruled in or out by something a reader can interrogate,
rather than selected by a position a grammar baked in.

⚠⚠⚠ **Grounding is not solved here and is not pretended to be.** Deciding that the token *"the block"*
denotes `block#1766` is reference resolution; it is the genuinely hard part of interpretation, it is
orthogonal to everything in this module, and `docs/HANDOFF.md` says so in as many words. Here a token's
denotation is **handed in** (`denote`), exactly as `check_A_RULE_CAN_BUILD_A_RUNNABLE_GOAL` is *handed*
its two real nodes. What this module claims is the half after that: given what the words denote, which
reading does the world prefer, and can it say why.

⚠ **Silent failure is acceptable; unrecorded failure is not.** An utterance that matches no construction
is not refused — refusing everything unrecognised is what makes a controlled language brittle, and `0/50`
on raw prose is that failure. It falls to the `elsewhere` case, which records it as what `discourse.py`
already makes it: a world event with a speaker, losing nothing and claiming nothing.

See `docs/comparison.md` §Language.
"""
from __future__ import annotations

from . import consequent as CQ, criterion as CR, precedence as PR
from .graph import Graph

KINDS = ("construction", "token", "reading")

CONSTRUCTION, TOKEN, READING = "construction", "token", "reading"

#: The role every construction binds: the token its address matched. Everything else is drawn from it.
HEAD = "head"


# --- the utterance, as evidence rather than as a parse -------------------------------------------------
def utter(g: Graph, thread: str, words, *, by="user", text: str | None = None) -> str:
    """Record something said, as **tokens and nothing else**.

    `discourse.say` runs `intake.read` and stores the *parse* on the utterance. This does not: the
    utterance is evidence, the tokens are ordered and linked `next` to each other, and what any of it
    means is nobody's decision yet. That is the whole difference between a front end that parses and one
    that proposes."""
    from . import discourse as DS
    u = DS._utter(g, thread, by=by, verb=None, about=None,
                  text=text if text is not None else " ".join(words))
    prev = None
    for w in words:
        t = g.mint(TOKEN, kind_of=TOKEN, text=w, lemma=w)
        g.link(u, TOKEN, t)                        # ordered — the utterance's own sequence
        if prev is not None:
            g.link(prev, "next", t)
        prev = t
    return u


def tokens(g: Graph, u: str) -> tuple:
    return g.targets(u, TOKEN)


def denote(g: Graph, token: str, node: str) -> str:
    """*This token stands for that thing.* **Handed in — see the module note on grounding.**"""
    g.link(token, "denotes", node)
    return token


def denoted(g: Graph, token: str):
    return g.target(token, "denotes")


# --- authoring a construction --------------------------------------------------------------------------
def open_construction(g: Graph, label: str, *, by=None, strength: str = PR.SHOULD,
                      because: str | None = None) -> str:
    """A form-meaning pair. Attributed like every other rule — an unattributed one is `experience`.

    `strength` feeds `precedence`'s force stage, so *"this reading is a must"* and *"this reading is
    merely available"* are sayable, and a domain can rank readings by who vouched for them."""
    if strength not in PR.STRENGTHS:
        raise ValueError(f"strength must be one of {PR.STRENGTHS}, not {strength!r}")
    c = g.mint(CONSTRUCTION, label=label, strength=strength)
    if because:
        g.put(c, because=because)
    g.link("root", "has", c)                       # a real thing: quotable, doubtable, withdrawable
    PR.attribute(g, c, by)
    return c


def addresses(g: Graph, c: str, sort: str, label: str | None = None) -> str:
    """The addressing half: which token this construction is about.

    Stored under `wants_sort` / `wants_label` — the same two attributes a criterion uses, and not by
    coincidence. `precedence._covers` opens by comparing exactly these (*"keying differs first: two rules
    that watch different constraints never compete"*), so a construction that names a lemma is
    automatically more specific than one that does not, with nothing arranged here."""
    g.put(c, wants_sort=sort)
    if label is not None:
        g.put(c, wants_label=label)
    return c


def draw(g: Graph, c: str, name: str, ref: str, label: str, *, back: bool = False) -> str:
    """`some <name> in <ref> by <link>` — reach another role by walking. `criterion.draw`, unchanged.

    This is how word order enters without a grammar: `some theme in head by ^next` offers every token
    before the head, nearest-first, and the `when` lines say which one is meant."""
    return CR.draw(g, c, name, ref, label, back=back)


def test(g: Graph, c: str, *, sort: str, negated: bool = False, **fields) -> str:
    """One condition on a reading. `criterion.test`, so each is its own node and a rejected reading can
    name the line that rejected it."""
    return CR.test(g, c, sort=sort, negated=negated, **fields)


def builds(g: Graph, c: str, function: str, bindings: dict) -> str:
    """What this reading *means*: a call that authors the goal, through the closed vocabulary.

    A `call` consequent, sharing one node kind and one edge label with a criterion's action and a
    method's rung, so a reader can ask all three families the same question. The function it names is an
    ordinary microfunction — `check_A_RULE_CAN_BUILD_A_RUNNABLE_GOAL` is the proof that authoring a goal
    needs nothing but `make` / `set_slot` / `relate`."""
    return CQ.call(g, c, function=function, bindings=bindings)


def constructions(g: Graph) -> tuple:
    """Every live construction, in declaration order. Withdrawn ones are skipped, like every enumerator."""
    from .discourse import live
    return live(g, g.of_kind(CONSTRUCTION))


# --- proposal -------------------------------------------------------------------------------------------
def _bindings_for(g: Graph, c: str, u: str) -> tuple:
    """Every way this construction's address matches the utterance, as `{role: node}`.

    `criterion._bindings_for`'s twin, and the difference between them is one line — *what is being
    addressed*. There it is the goal's unmet constraints; here it is the utterance's tokens. Everything
    after that line, including the draws, is shared code.

    ⚠ That one line is also the honest statement of what is *not* yet unified. Making the source an
    argument would collapse the two, and it should — but the second caller is what creates the island,
    and today there are exactly two. When a third family addresses something, that is the moment."""
    sort, label = g.attr(c, "wants_sort"), g.attr(c, "wants_label")
    out = []
    for t in tokens(g, u):
        if g.attr(t, "kind_of") != sort:
            continue
        if label is not None and g.attr(t, "lemma") != label:
            continue
        out.append({HEAD: t, "__utterance__": u})
    return CR._expand(g, tuple(out), CR.draws_of(g, c), None, "root")


def _rejections(g: Graph, c: str, bound: dict) -> tuple:
    """The conditions that do not hold of this binding, rendered. Empty means the reading stands."""
    return tuple(CR.describe_test(g, t) for t in CR.tests_of(g, c)
                 if not CR.holds(g, t, bound, None, "root"))


def readings(g: Graph, u: str) -> tuple:
    """Every reading this utterance supports: `(construction, bound)`, most preferred first.

    **Rival readings coexist rather than competing for a single winner at proposal time.** That is the
    whole reason this is not a parser: a parser commits to a structure before the reasoner is consulted,
    and here nothing has committed to anything — the readings are candidates, exactly as proposed actions
    are, and what decides between them is knowledge.

    Ordered by `precedence.rank`, which means an authored tie-break rule decides — by who said it, by
    force, by specificity, and finally by a total stage — and *which stage decided* is answerable
    afterwards through `precedence.deciding_stage`. A parser's disambiguation is a grammar accident that
    cannot be asked about; this one is a decision somebody made."""
    out = []
    for c in constructions(g):
        for bound in _bindings_for(g, c, u):
            if not _rejections(g, c, bound):
                out.append((c, bound))
    order = {n: i for i, n in enumerate(PR.rank(g, tuple(dict.fromkeys(c for c, _b in out))))}
    return tuple(sorted(out, key=lambda cb: order[cb[0]]))


def why(g: Graph, u: str) -> tuple:
    """`(construction, read, reasons)` for every construction — *why this reading and not that one?*

    `criterion.governing`'s counterpart, and load-bearing for the same reason: selection **discards**,
    so without this the rejected readings were never built and the first wrong one produces a bare
    answer with nothing behind it. This is the residue thesis reaching language — an interpretation you
    can ask *why* of, which is the one thing the abductive tradition does not keep."""
    out = []
    for c in constructions(g):
        matches = _bindings_for(g, c, u)
        if not matches:
            out.append((c, False, (f"nothing in the utterance matches `addresses "
                                   f"{g.attr(c, 'wants_sort')} "
                                   f"{g.attr(c, 'wants_label') or ''}`".rstrip(),)))
            continue
        failed, read = [], False
        for bound in matches:
            why_not = _rejections(g, c, bound)
            if why_not:
                failed.extend(why_not)
            else:
                read = True
        out.append((c, read, () if read else tuple(dict.fromkeys(failed))))
    return tuple(out)


# --- selection, and what the winner produces --------------------------------------------------------------
def run_reading(g: Graph, c: str, bound: dict):
    """Run the construction's consequent — the call that authors the goal. Returns the node it built.

    The bindings are references in the criterion reference language (`head`, `theme.denotes`, a drawn
    name), resolved against this binding. What comes back is whatever the named microfunction returns,
    which for an interpretation is a goal — but nothing here insists on that, because **not every
    utterance makes the engine run**. Stating a fact records facts and has succeeded; asking triggers an
    answer; only a directive plans. A pass that demanded machinery of every utterance would fire on most
    of the language."""
    from . import function as fn
    act = CQ.of(g, c)
    if not act:
        return None
    act = act[0]
    args = {}
    for a in g.targets(act, "arg"):
        got = CR.resolve_ref(g, g.attr(a, "ref"), bound, None, under="root")
        if got is None:
            return None
        args[g.attr(a, "param")] = got
    return fn.invoke(g, g.attr(act, "function"), args, retain=False)[1].get("result")


def interpret(g: Graph, u: str) -> dict:
    """Read an utterance: propose, select, run the winner, and keep the record.

    Returns `{read, construction, built, rivals}`. `read` is False when nothing addressed it, which is
    an **ordinary outcome and not an error** — see the module note. The reading is minted as a node
    pointing at the construction that produced it and the thing it built, so *how did you read that?* is
    answered from the graph rather than from this call's return value."""
    got = readings(g, u)
    r = g.mint(READING, read=bool(got))
    g.link(u, "read", r)
    if not got:
        # The elsewhere case. The utterance stays exactly what `discourse.py` made it — a world event
        # with a speaker — which loses nothing and claims nothing.
        return {"read": False, "construction": None, "built": None, "rivals": 0, "reading": r}
    c, bound = got[0]
    built = run_reading(g, c, bound)
    g.link(r, "by_construction", c)
    if built is not None:
        g.link(r, "built", built)
    for rival, _b in got[1:]:
        g.link(r, "rival", rival)                  # the roads not taken, kept as data
    return {"read": True, "construction": c, "built": built,
            "rivals": len(got) - 1, "reading": r}


def describe(g: Graph, u: str) -> str:
    """The reading and its rivals, for a reader."""
    lines = [f"{g.attr(u, 'text')!r}"]
    for c, read, reasons in why(g, u):
        mark = "READ" if read else "no  "
        lines.append(f"  {mark} {g.attr(c, 'label')!r}"
                     + ("" if read else " — " + "; ".join(reasons)))
    return "\n".join(lines)


__all__ = ["KINDS", "CONSTRUCTION", "TOKEN", "READING", "HEAD",
           "utter", "tokens", "denote", "denoted",
           "open_construction", "addresses", "draw", "test", "builds", "constructions",
           "readings", "why", "run_reading", "interpret", "describe"]

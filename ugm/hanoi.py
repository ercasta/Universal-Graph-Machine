"""Hanoi: the fixture that isolates BINDING choice, and a recursion that transfers.

    python -m ugm.hanoi

Every other fixture here measures which RULE to reach for. None could measure
which BINDING, and `ugm.workload` -- the one built for scale -- has exactly ONE
individual (`item`), so it cannot measure it even in principle. That gap is why
the binding conclusions drawn from the dungeon were worth so little: it has
three combatants.

Hanoi has one action, and every step of the puzzle is a choice of binding for
it. Rule selection contributes nothing. That is the whole reason to have it.

## It can fail, and four earlier versions did

A benchmark that cannot fail is worse than none, because it reads as evidence.
This one failed four times before it worked, and each failure is a finding:

| what was written | what happened |
|---|---|
| a free-standing `<move>` | only LEGAL moves, and `d1` shuttles for ever: 155 moves, never solved |
| the decomposition under `goal(...)` | the bundle's backward reader took **153 of 200 ticks** while `<move>` had one live application -- the correct one -- and never got a turn |
| `built`/`at`/`site` as derived facts | the engine does not retract (§12), so `built(d2, d3)` still stood after d2 had moved to `y`, and the want was met by a memory |
| the recursion guarded on WORLD STATE | `on(d2, d3)` holds again on the way back, so `<unstack>` re-fired and recreated a want it had already met |

⭐⭐⭐ **The fourth is the one that matters, and it is why the phase exists.**
Hanoi's recursion is depth-first and ORDERED -- unstack, then place, then
restack -- and world state cannot say which of the three you are in: `at(d1, x)`
is equally true on the way out and on the way back. Guards read off the world
are therefore ambiguous by construction, and no number of them fixes it.

So a call is a NODE, minted per occasion, carrying its own pegs and its own
PHASE. *Which step of this call am I on* becomes a fact. That is
`docs/HANDOFF.md`'s *a multi-tick plan is a NODE, not a string* -- reached from
the other direction, by writing the alternative and watching it fail.

⚠ Minted per OCCASION and not per parameters, which matters here rather than in
principle: `solve(d1, x, z, y)` occurs TWICE in a three-disk solution, so a call
node keyed on its arguments would collide with itself and refraction would block
the second. `+call` mints one node per application, which is exactly right.

## The stack is the bundle's; the strategy is Hanoi's

⭐⭐⭐ **The plumbing is three bundled rules and mentions no domain at all**:
`<call-spawn>`, `<call-advance>`, `<call-return>`. What makes them shareable is
that a call carries its parameters as ONE node -- `call(?c, tower(?d,?f,?t,?s))`
rather than five arguments -- so the arity is the domain's business and the
stack never sees it. The stage ORDER is data a corpus deposits
(`advances(unstacking, placing)`, `closes(waiting)`), because the order of the
steps is exactly what differs between one recursive plan and the next.

⚠ **One domain cannot show that a mechanism is general**, so there are two.
`COUNTDOWN` below shares nothing with Hanoi -- no disks, no pegs, no `want`, no
action -- and runs on the same three rules. Before the split, `<unstacked>` and
`<restacked>` were rules in this file; they are now the bundle's `<call-advance>`
and `<call-return>` plus two facts.

⚠ And this is NOT a second planner. `<expand>` in the bundle is a STRATEGY --
means-ends, decompose a goal by some rule's antecedents -- and it stays exactly
what it was. What is shared here is what any strategy needs underneath it.

## What it establishes

    disks   optimal   moves made        rules naming a disk or peg
    3         7         7  identical                 0
    4        15        15  identical                 0
    5        31        31  identical                 0
    6        63        63  identical                 0
    7       127       127  identical                 0

Not *close to* optimal: the move sequence is identical to the recursive solution
at every size. And the transfer result is the strongest form there is -- **the
same rules, unchanged, are optimal at every size, and not one of them names an
individual.** Nothing was retuned, and there is nothing in them that could be.

## ...and the recursion is LEARNED, not only authored

Watching the authored solve on 3 and 4 disks and anti-unifying each rule's own
firings recovers **10 of the 12 rules exactly**, modulo what a person called a
variable -- including the two that matter:

    <descend>  parent tower(?d,?f,?t,?s)  spawns  tower(?e,?f,?s,?t)
    <ascend>   parent tower(?d,?f,?t,?s)  spawns  tower(?e,?s,?t,?f)

That permutation IS Hanoi. Nothing here searches: `generalise` is the dual of
`unify` and it reads the mapping straight off two examples.

**The learned rules alone -- nothing authored but the puzzle itself -- solve 5,
6 and 7 disks in the optimal sequence, having seen only 3 and 4.**

⚠⚠⚠ **Two demonstrations, and ONE is not enough** -- which is what makes the
result mean anything. Taught on 3 alone, two rules fire once and are declined
outright, and what is induced does not solve even the size it was taught on.
Taught on 3 and 4, nothing is declined. The repo already had this as *experience
means more than one fight*; here it is a pass/fail rather than a degradation.

⚠ **The two rules it does NOT recover are the sharp finding.** `<base>` and
`<leaf>` keep `d1` where a person wrote `?d`, and no number of SIZES fixes it:
the smallest disk is called `d1` at every size, so varying `n` never varies that
argument. Varying the size does not vary everything, and what a demonstration
holds constant is what a learner will believe is necessary. They still solve --
`d1` is genuinely the smallest in every puzzle this generator makes -- so the
defect is invisible in the outcome and visible only in the diff against what a
person wrote. Which is the reason to compare against the authored rule at all,
rather than only against the behaviour.

⚠ What is NOT learned is the plumbing: `<call-spawn>`, `<call-advance>` and
`<call-return>` are the bundle's, and the demonstration teaches the domain.

⚠ And the teacher demonstrates CALLS, not only moves. Inferring the call tree
from a bare move trace is program induction and is not attempted here -- stated
because the difference is the whole of what this result claims.

⚠ The recursion below is AUTHORED, and learning it is measured against it. What this fixture provides is the
target: a corpus whose knowledge is entirely structural, on a task where an
identity-keyed version cannot work at all, and a teacher that CAN supervise a
binding -- which `ugm.teaching`'s cannot, because `arbitrate` keys on
`(score(rule), rules.index(rule))`, so two applications of one rule tie and the
first in walk order wins. Asked where the table took a binding it would not
have, it answered 0 times in 148 dungeon moves.
"""

import re
from typing import Dict, List, Tuple

PEGS = ("x", "y", "z")

# The knowledge. Nothing here mentions a disk, a peg, or a size -- `main`
# checks that rather than trusting it, because it is the whole experiment.
RULES = """
# ⭐ The palette: one action, declared. Two rules RESOLVE it -- onto a peg that
# has a top disk, and onto an empty one -- which is the point of separating the
# declaration from the resolution: what the agent may ask for is one thing, and
# what happens when it asks is several.
action move(?d, ?p)

fact +advances(unstacking, placing)
fact +closes(waiting)

rule <bigger> = implies( { +smaller(?a,?b), +smaller(?b,?c) }, { +smaller(?a,?c) } )
rule <fits-peg>  = implies( { +disk(?d), +peg(?p) }, { +fits(?d, ?p) } )
rule <fits-disk> = implies( { +smaller(?d, ?e) }, { +fits(?d, ?e) } )

# -- the strategy. The STACK is the bundle's; this is what is Hanoi's ---------

# A call on the smallest disk has nothing to unstack: place it.
rule <base> = implies( { +stage(?c, start), +call(?c, tower(?d, ?f, ?t, ?s)),
                         +smallest(?d) },
                       { -stage(?c, start), +stage(?c, placing) } )

# Otherwise a sub-call moves the sub-tower to the spare peg, and the pegs
# rotate exactly as the recursive definition rotates them.
rule <descend> = implies( { +stage(?c, start), +call(?c, tower(?d, ?f, ?t, ?s)),
                            +next(?e, ?d) },
                          { -stage(?c, start), +stage(?c, unstacking),
                            +spawn(?c, tower(?e, ?f, ?s, ?t), start) } )

# Placing is the only stage that asks for an action.
rule <ask> = implies( { +stage(?c, placing), +call(?c, tower(?d, ?f, ?t, ?s)) },
                      { +attempt(move(?d, ?t)) } )

rule <placed> = implies( { +stage(?c, placing), +call(?c, tower(?d, ?f, ?t, ?s)),
                           +at(?d, ?t) },
                         { -stage(?c, placing), +stage(?c, restacking) } )

rule <ascend> = implies( { +stage(?c, restacking), +call(?c, tower(?d, ?f, ?t, ?s)),
                           +next(?e, ?d) },
                         { -stage(?c, restacking), +stage(?c, waiting),
                           +spawn(?c, tower(?e, ?s, ?t, ?f), start) } )

rule <leaf> = implies( { +stage(?c, restacking), +call(?c, tower(?d, ?f, ?t, ?s)),
                          +smallest(?d) },
                        { -stage(?c, restacking), +returned(?c) } )

# -- the action. Licensed by a want, never free-standing, and it keeps `at`
# true -- which is cheap because only a CLEAR disk ever moves, so nothing
# above it has to be updated.

rule <move> = causes( { +attempt(move(?d, ?p)), +peg(?p), +on(?d, ?from),
                         +at(?d, ?was), +clear(?d), +clear(?to),
                         +fits(?d, ?to), +at(?to, ?p) },
                       { +on(?d, ?to), -on(?d, ?from), +clear(?from),
                         -clear(?to), -attempt(move(?d, ?p)),
                         +at(?d, ?p), -at(?d, ?was) } )

rule <move-bare> = causes( { +attempt(move(?d, ?p)), +peg(?p), +clear(?p),
                              +on(?d, ?from), +at(?d, ?was), +clear(?d),
                              +fits(?d, ?p) },
                            { +on(?d, ?p), -on(?d, ?from), +clear(?from),
                              -clear(?p), -attempt(move(?d, ?p)),
                              +at(?d, ?p), -at(?d, ?was) } )

# ⭐⭐⭐ ...and the world model DECLINES an illegal one, out loud. Before this,
# an attempt to move a covered disk simply matched nothing, and *nothing
# happened* is indistinguishable from *nothing was wrong* -- the silence this
# whole design is against. `-clear(?d)` is sayable here because a move DENIES
# what it lands on, so *an entry denies this* is exactly the case (§9).
rule <covered> = implies( { +attempt(move(?d, ?p)), -clear(?d) },
                         { +declined(move(?d, ?p), covered),
                           -attempt(move(?d, ?p)) } )

rule <finished> = implies( { +returned(whole) }, { +enough(solved) } )
"""


# A SECOND domain over the same stack, and it is here rather than in a file of
# its own because the claim it settles is about `ugm.hanoi`: that
# `<call-spawn>`, `<call-advance>` and `<call-return>` are the bundle's and not
# Hanoi's. Two domains sharing them is the only thing that shows it -- one
# domain cannot tell a general mechanism from a specific one.
#
# It shares NOTHING with Hanoi: no disks, no pegs, no `want`, no action at all.
COUNTDOWN = """
fact +advances(waiting, resuming)
fact +closes(resuming)

rule <bottom> = implies( { +stage(?c, start), +call(?c, count(0)) },
                        { -stage(?c, start), +returned(?c) } )
rule <step> = implies( { +stage(?c, start), +call(?c, count(?n)), +pred(?n, ?m) },
                      { -stage(?c, start), +stage(?c, waiting),
                        +spawn(?c, count(?m), start) } )
rule <resumed> = implies( { +stage(?c, resuming) },
                         { -stage(?c, resuming), +returned(?c) } )
rule <counted-down> = implies( { +returned(whole) }, { +enough(counted) } )
"""


def countdown(n: int) -> str:
    L = ["fact +pred(%d, %d)" % (i, i - 1) for i in range(1, n + 1)]
    L.append("fact +call(whole, count(%d))" % n)
    L.append("fact +stage(whole, start)")
    return chr(10).join(L) + chr(10) + COUNTDOWN


def count(n: int, limit: int = 3000) -> dict:
    """Run the second domain. Same three bundled rules, nothing else in common."""
    from .attention import run
    from .chain import PLUS
    from .machine import Machine
    from .text import load

    m = Machine()
    kb = load(m, countdown(n))
    depth = []

    def watch(mm, table, window, chosen, tick, step=None):
        if chosen.rule.name == "step":
            depth.append(tick)

    report = run(m, limit=limit, watch=watch)
    return {"depth": len(depth), "done": m.holds(kb.term("enough(counted)")) == PLUS,
            "ticks": report.ticks}


def facts(n: int, pegs: Tuple[str, ...] = PEGS, target: str = "z") -> str:
    """The puzzle itself: n disks, three pegs, the tower on the first.

    Everything size-dependent is HERE, and nothing size-dependent is in
    `RULES`. That split is the experiment.
    """
    spare = [p for p in pegs if p not in (pegs[0], target)][0]
    L = ["# %d disks. Generated by `ugm.hanoi`." % n]
    for p in pegs:
        L.append("fact +peg(%s)" % p)
    for i in range(1, n + 1):
        L.append("fact +disk(d%d)" % i)
        L.append("fact +at(d%d, %s)" % (i, pegs[0]))
    for i in range(1, n):
        L.append("fact +next(d%d, d%d)" % (i, i + 1))
        L.append("fact +smaller(d%d, d%d)" % (i, i + 1))
        L.append("fact +on(d%d, d%d)" % (i, i + 1))
    L.append("fact +on(d%d, %s)" % (n, pegs[0]))
    L.append("fact +clear(d1)")
    L.append("fact +smallest(d1)")
    # ⚠⚠⚠ **Stated, not left absent.** `-clear(?d)` means *an entry denies
    # this*, never *there is no entry* (§9) -- so a world model that merely
    # omits `clear(d2)` cannot be asked whether d2 is covered, and the rule that
    # declines a move onto a covered disk matches nothing until something has
    # denied it. A complete initial state is what makes the question askable at
    # tick 0 rather than only after the first move.
    for i in range(2, n + 1):
        L.append("fact -clear(d%d)" % i)
    L.append("fact -clear(%s)" % pegs[0])
    for p in pegs[1:]:
        L.append("fact +clear(%s)" % p)
    # `whole` rather than `root`: `root` is a RESERVED name, so an argument
    # written with it is the machine's own node and not a fresh atom of ours.
    # The load-time census says so, and it is the twin trap in its cheapest form.
    L.append("fact +call(whole, tower(d%d, %s, %s, %s))" % (n, pegs[0], target, spare))
    L.append("fact +stage(whole, start)")
    return chr(10).join(L) + chr(10)


def corpus(n: int, without: str = "") -> str:
    """The puzzle and the knowledge. `without` drops one rule, for the ablation."""
    rules = RULES
    if without:
        kept, skip = [], False
        for line in RULES.splitlines():
            if line.startswith("rule <"):
                skip = line.startswith("rule <%s>" % without)
            if not skip:
                kept.append(line)
        rules = chr(10).join(kept)
    return facts(n) + rules


def optimal(n: int, a: str = "x", c: str = "z", b: str = "y") -> List[Tuple]:
    """The shortest solution as (disk, from, to): 2**n - 1 moves, optimal by
    construction rather than by search."""
    if n == 0:
        return []
    return optimal(n - 1, a, b, c) + [("d%d" % n, a, c)] + optimal(n - 1, b, c, a)


def solve(n: int, without: str = "", limit: int = 20000) -> dict:
    """Run it. No teacher, no chooser, no learned table -- the corpus alone."""
    from .attention import run
    from .chain import PLUS
    from .machine import Machine
    from .text import load

    m = Machine()
    kb = load(m, corpus(n, without))
    moves: List[Tuple[str, str]] = []

    def watch(mm, table, window, chosen, tick, step=None):
        if chosen.rule.name in ("move", "move-bare"):
            b = {mm.g.show(k): mm.g.show(v) for k, v in chosen.bindings.items()}
            moves.append((b["?d"], b["?p"]))

    report = run(m, limit=limit, watch=watch)
    return {
        "moves": moves,
        "solved": m.holds(kb.term("enough(solved)")) == PLUS,
        "optimal": [(d, t) for d, _f, t in optimal(n)],
        "ticks": report.ticks,
        "end": report.steps[-1].state if report.steps else "?",
    }



# -- learning the recursion from watching it -------------------------------
#
# ⭐⭐⭐ **What is learned is the PERMUTATION**, and it is the whole insight of
# Hanoi: a parent call `tower(?d, ?f, ?t, ?s)` spawns `tower(?e, ?f, ?s, ?t)` on
# the way down and `tower(?e, ?s, ?t, ?f)` on the way back. Anti-unification --
# `generalise`, the dual of `unify`, which this repository already had -- reads
# both straight off two demonstrations.
#
# ⚠ **Examples cross as TEXT.** A node id means nothing outside the graph that
# minted it, so two demonstrations on two machines cannot share one, and this is
# the repo's own rule for what may cross (`ugm/table.py`) arriving on the
# learning side.
#
# ⚠⚠⚠ **A minted node has no name, and the whole call stack is minted**, so
# every example about `stage(?c, ...)` was unsayable -- which is every example
# about the recursion. `_sayable` gives one a placeholder, and the placeholder
# has to be UNIQUE PER EXAMPLE: the same within an example so `?c` co-refers,
# and different across them, or two unrelated calls anti-unify to a constant and
# the rule is about one call for ever.

# What is not the corpus's own: the apparatus, and the stack the bundle now
# supplies. A demonstration teaches the domain, and the plumbing was never the
# domain's to learn.
# Rules the SOLVE cannot exercise, because correct play never needs them. They
# are ablated against `misbehave` instead. A rule no fixture can kill is a rule
# the fixture is not testing -- and the first run of this gate caught exactly
# that about `<covered>`.
DECLINING = ("covered",)

NOT_THE_DOMAIN = frozenset({
    "plan", "relevant", "call-spawn", "call-advance", "call-return",
    "deviation-+-contradicted", "deviation---contradicted", "intake",
    "assert-act", "taken", "did", "denial", "resuming", "give-up",
    "ask-fit", "ask-check", "expand", "settle-doubt",
})


def _sayable(m, node, names, tag: str) -> str:
    """Render a proposition so the surface can read it back, minting a
    placeholder for anything that has no name of its own."""
    from .teaching import _say
    if node not in names and m.g.relation_of(node) is None and not m.g.members(node):
        shown = m.g.show(node)
        if not shown or shown.startswith("#"):
            names[node] = "n%s_%d" % (tag, len(names))
    if node in names:
        return names[node]
    members = m.g.members(node)
    if not members:
        return _say(m, node)
    rel = m.g.relation_of(node)
    return "%s(%s)" % (_sayable(m, rel, names, tag) if rel is not None else "?",
                       ", ".join(_sayable(m, x, names, tag) for x in members))


def demonstrate(sizes: Tuple[int, ...] = (3, 4)) -> Tuple[dict, List[str]]:
    """Watch authored solves, and write down what each rule did."""
    from .attention import run
    from .chain import PLUS
    from .machine import Machine
    from .teaching import _say
    from .text import load

    out: dict = {}
    data: set = set()
    for n in sizes:
        m = Machine()
        load(m, corpus(n))

        def watch(mm, table, window, chosen, tick, step=None):
            # The strategy as DATA, read off every move -- including the
            # stack's own, which is where `advances`/`closes` are consumed.
            for e in chosen.consumed:
                txt = _say(mm, e.proposition)
                if txt.startswith("advances(") or txt.startswith("closes("):
                    data.add(txt)
            if chosen.rule.name in NOT_THE_DOMAIN:
                return
            tag, names = "%d_%d" % (n, tick), {}
            prem = [_sayable(mm, e.proposition, names, tag)
                    for e in chosen.consumed]
            conc = [(e.sign, _sayable(mm, e.proposition, names, tag))
                    for e in (step.wrote or ())]
            if prem and conc:
                out.setdefault(chosen.rule.name, []).append(
                    (chosen.rule.connective, prem, conc))

        run(m, limit=20000, watch=watch)
    return out, sorted(data)


def induce(examples: dict) -> Tuple[dict, dict]:
    """Anti-unify each rule's own firings into a rule. One scope for every
    example, so two demonstrations share variables; ONE mapping across premises
    and conclusions, which is what makes the conclusion about what the premises
    bound rather than about something nothing binds."""
    from .chain import PLUS
    from .machine import Machine
    from .rules import generalise
    from .text import Loader, ParseError

    m = Machine()
    ldr = Loader(m)
    g = m.g
    learned: dict = {}
    declined: dict = {}
    for name, ex in sorted(examples.items()):
        if len(ex) < 2:
            declined[name] = "one firing -- an example generalises to itself"
            continue
        if len({(len(p), len(c)) for _k, p, c in ex}) > 1:
            declined[name] = "arity varies between firings"
            continue
        try:
            packed = [ldr.term("q(%s)" % ", ".join(
                p + ["s%s(%s)" % ("p" if sg == PLUS else "m", t) for sg, t in cs]))
                for _k, p, cs in ex]
        except ParseError:
            declined[name] = "the example cannot be written down"
            continue
        mapping: dict = {}
        lgg = packed[0]
        for other in packed[1:]:
            lgg = generalise(g, lgg, other, mapping)
        if g.is_var(lgg):
            declined[name] = "generalised to a bare variable"
            continue
        members = list(g.members(lgg))
        cut = len(ex[0][1])
        ant, con = members[:cut], members[cut:]
        if any(g.is_var(x) for x in ant):
            declined[name] = "a premise generalised to a bare variable"
            continue
        parts = [("+" if g.show(g.relation_of(t)) == "sp" else "-")
                 + g.show(g.member(t, 0)) for t in con]
        learned[name] = "rule <%s> = %s( { %s }, { %s } )" % (
            name, ex[0][0], ", ".join("+" + g.show(x) for x in ant),
            ", ".join(parts))
    return learned, declined


def solve_learned(n: int, learned: dict, data: List[str],
                  limit: int = 20000) -> dict:
    """Run a machine that has ONLY what was learned."""
    from .attention import run
    from .chain import PLUS
    from .machine import Machine
    from .text import load

    src = (facts(n) + chr(10).join("fact +" + d for d in data) + chr(10)
           + chr(10).join(learned[k] for k in sorted(learned)) + chr(10))
    m = Machine()
    kb = load(m, src)
    moves: List[Tuple[str, str]] = []

    def watch(mm, table, window, chosen, tick, step=None):
        # ⚠ Read off what the move DEPOSITED, never off its bindings: a learned
        # rule's variables are `?g47`, so nothing outside it can name them.
        # `at(?d, ?p)` says the same thing in the corpus's own vocabulary, which
        # is the only part that survives being learned.
        for e in (step.wrote or ()):
            if e.sign == PLUS and mm.g.show(mm.g.relation_of(e.proposition)) == "at":
                d, p = mm.g.members(e.proposition)
                moves.append((mm.g.show(d), mm.g.show(p)))

    report = run(m, limit=limit, watch=watch)
    return {"moves": moves, "solved": m.holds(kb.term("enough(solved)")) == PLUS,
            "optimal": [(d, t) for d, _f, t in optimal(n)],
            "ticks": report.ticks}


def _canonical(text: str) -> str:
    """A rule with its variables renamed in order of first appearance, so two
    rules that differ only in what a person called a variable compare equal."""
    seen: dict = {}
    def sub(mo):
        v = mo.group(0)
        if v not in seen:
            seen[v] = "?v%d" % len(seen)
        return seen[v]
    flat = " ".join(text.split())
    # ⚠ Spacing is not a difference. A person writes `?a,?b` and the renderer
    # writes `?g6, ?g7`; comparing those as strings reported two rules as
    # DIFFERING from themselves.
    for ch in ",(){}":
        flat = flat.replace(" " + ch, ch).replace(ch + " ", ch)
    return re.sub(r"\?[A-Za-z_][A-Za-z0-9_]*", sub, flat)


def misbehave(n: int = 3, without: str = "", limit: int = 400) -> dict:
    """Two bad attempts, and what becomes of them.

    ⭐⭐⭐ The whole of what step 2 buys. Before it, an attempt to move a covered
    disk simply matched nothing -- and *nothing happened* is indistinguishable
    from *nothing was wrong*. Now:

        covered      the world model declines it, and says why
        unafforded   the MACHINERY declines it, because no such action exists

    ⚠⚠⚠ **The decline is LATE.** The attempt stands from tick 0 and is not
    declined until tick ~101, because `<covered>` sits at the floor and the
    shortlist is busy with the recursion. Correct, and slow: a refusal the agent
    only learns about after it has finished is a poor thing to learn from. That
    is the concrete argument for attending to what a move just wrote -- an
    attempt is a fresh fact, and nothing currently lifts the rules about it.

    ⚠ The two are declined by different things on purpose. What is LEGAL is the
    world model's business and a rule says it; what EXISTS is the palette's, and
    only the machinery can check it, because subsumption runs the pattern
    against the entry and here the entry is the generic one.
    """
    from .attention import run
    from .chain import PLUS
    from .machine import Machine
    from .text import load

    m = Machine()
    kb = load(m, corpus(n, without)
              + "fact +attempt(move(d%d, y))" % n      # d(n) is covered
              + chr(10)
              + "fact +attempt(teleport(d1, z))" + chr(10))
    run(m, limit=limit)
    return {
        "covered": m.holds(kb.term("declined(move(d%d, y), covered)" % n)) == PLUS,
        "unafforded": m.holds(
            kb.term("declined(teleport(d1, z), unafforded)")) == PLUS,
    }


def _authored() -> Dict[str, str]:
    """The authored rules, by name.

    ⚠ Split rather than matched. A regex over `rule <...> = ... } )` silently
    missed two of the twelve -- one written with two spaces before the `=` and
    one spanning lines -- and a comparison that quietly drops what it cannot
    parse reports agreement it never checked.
    """
    out: Dict[str, str] = {}
    for chunk in RULES.split("rule <")[1:]:
        name = chunk.split(">", 1)[0]
        body = chunk
        cut = body.rfind("} )")
        if cut != -1:
            body = body[:cut + 3]
        out[name] = "rule <" + body
    return out


def main() -> int:
    import re
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(__doc__.split("## It can fail")[0].strip())
    print()
    bad = 0

    # The claim the whole fixture rests on, checked rather than asserted: a
    # corpus that solves any size is one that mentions no size.
    named = sorted(set(re.findall(r"\bd\d+\b|\b[xyz]\b", RULES)))
    print("  rules naming a disk or a peg: %s" % (named or "none"))
    if named:
        print("    FAIL  a rule names an individual, so nothing here transfers")
        bad += 1

    print()
    print("  %5s %8s %7s %12s %7s  end" %
          ("disks", "optimal", "moves", "sequence", "ticks"))
    for n in (3, 4, 5, 6, 7):
        r = solve(n)
        same = "identical" if r["moves"] == r["optimal"] else "DIFFERS"
        print("  %5d %8d %7d %12s %7d  %s" %
              (n, len(r["optimal"]), len(r["moves"]), same, r["ticks"], r["end"]))
        if not r["solved"]:
            print("    FAIL  %d disks not solved" % n)
            bad += 1
        elif r["moves"] != r["optimal"]:
            print("    FAIL  %d disks solved, but not by the optimal sequence" % n)
            bad += 1

    # ⭐⭐⭐ **Delete each rule and report any the fixture cannot kill.** Three
    # checks in this project reported success while unable to fail, and this is
    # what caught them each time. A rule the puzzle solves without is a rule
    # this fixture is not measuring.
    # ⭐⭐⭐ The claim that the stack is the BUNDLE's and not Hanoi's, which one
    # domain cannot show. This one shares no relation with Hanoi at all.
    print()
    print("  a second domain over the same three bundled rules:")
    for k in (3, 5, 8):
        c = count(k)
        print("      countdown from %d: returned=%-5s depth %d, %d ticks"
              % (k, c["done"], c["depth"], c["ticks"]))
        if not c["done"] or c["depth"] != k:
            print("    FAIL  the countdown did not recurse to the bottom")
            bad += 1

    # ⭐ What becomes of a bad attempt -- the whole of what the palette buys.
    print()
    print("  two bad attempts:")
    bad_attempts = misbehave(3)
    print("      a covered disk        declined by the WORLD MODEL:  %s"
          % bad_attempts["covered"])
    print("      an action that is not declined by the MACHINERY:    %s"
          % bad_attempts["unafforded"])
    if not (bad_attempts["covered"] and bad_attempts["unafforded"]):
        print("    FAIL  a bad attempt was met with silence, which is the one "
              "thing this is against")
        bad += 1

    print()
    print("  the ablation -- each rule removed in turn, on 4 disks:")
    survivors = []
    for name in re.findall(r"rule <([^>]+)>", RULES):
        if name in DECLINING:
            # ⚠ Ablated against the exercise that NEEDS it. Hanoi's own play
            # never makes an illegal move -- the recursion is correct -- so
            # solving cannot kill a rule that only declines, and the gate said
            # so the first time it ran.
            gone = misbehave(3, without=name)
            mark = ("STILL DECLINES" if gone["covered"]
                    else "fails, as it must")
            print("      without <%-11s> %14s  %s" % (name, "", mark))
            if gone["covered"]:
                survivors.append(name)
            continue
        r = solve(4, without=name, limit=4000)
        if r["solved"]:
            mark = "STILL SOLVED"
        elif r["moves"] == r["optimal"]:
            # ⭐ The one that is worth telling apart. Without `<finished>` the
            # tower is built, optimally, and the agent never NOTICES -- so it
            # goes on running with nothing to do. *Solved* and *knows it is
            # solved* are two claims, and only the second is what `enough` is.
            mark = "builds it, never notices"
        else:
            mark = "fails, as it must"
        print("      without <%-11s> %4d moves  %s" % (name, len(r["moves"]), mark))
        if r["solved"]:
            survivors.append(name)
    if survivors:
        print("    FAIL  solved without %s -- not load-bearing, so this fixture "
              "is not measuring them" % survivors)
        bad += 1

    # ⭐⭐⭐ **And now the recursion is LEARNED rather than authored.**
    print()
    print("  learned by watching the authored solves on 3 and 4 disks:")
    examples, data = demonstrate((3, 4))
    learned, declined = induce(examples)
    print("      %d rules induced, %d declined; the strategy as data: %s"
          % (len(learned), len(declined), data))
    if declined:
        for k, why in sorted(declined.items()):
            print("      declined <%s>: %s" % (k, why))

    # Which of them is what a person wrote, modulo what they called a variable.
    authored = _authored()
    same = [k for k in learned
            if k in authored and _canonical(learned[k]) == _canonical(authored[k])]
    differs = sorted(set(learned) & set(authored) - set(same))
    print("      %d of %d match the authored rule exactly (modulo variable names)"
          % (len(same), len(set(learned) & set(authored))))
    for k in differs:
        print("      <%s> differs: %s" % (k, learned[k]))

    print()
    print("  the LEARNED rules alone -- nothing authored but the puzzle:")
    for n in (3, 4, 5, 6, 7):
        r = solve_learned(n, learned, data)
        tag = "identical" if r["moves"] == r["optimal"] else "DIFFERS"
        seen = "demonstrated" if n in (3, 4) else "NEVER SEEN"
        print("  %5d %8d %7d %12s %7d  %s"
              % (n, len(r["optimal"]), len(r["moves"]), tag, r["ticks"], seen))
        if not r["solved"] or r["moves"] != r["optimal"]:
            print("    FAIL  learned rules did not solve %d disks optimally" % n)
            bad += 1

    # ⚠ And the gate can fail: ONE demonstration is not experience.
    print()
    print("  ...and one demonstration is not enough, which is what makes the "
          "two-demonstration result mean anything:")
    for sizes in ((3,), (4,)):
        ex1, d1 = demonstrate(sizes)
        l1, dec1 = induce(ex1)
        r = solve_learned(5, l1, d1, limit=8000) if l1 else {"solved": False}
        print("      taught on %s only: %d rules, %d declined, solves 5 disks: %s"
              % (sizes, len(l1), len(dec1), r["solved"]))
        if r["solved"]:
            print("    FAIL  one demonstration sufficed, so the second proves "
                  "nothing")
            bad += 1
    return bad


if __name__ == "__main__":
    raise SystemExit(main())

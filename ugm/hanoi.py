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

⚠ The recursion here is AUTHORED, not learned. What this fixture provides is the
target: a corpus whose knowledge is entirely structural, on a task where an
identity-keyed version cannot work at all, and a teacher that CAN supervise a
binding -- which `ugm.teaching`'s cannot, because `arbitrate` keys on
`(score(rule), rules.index(rule))`, so two applications of one rule tie and the
first in walk order wins. Asked where the table took a binding it would not
have, it answered 0 times in 148 dungeon moves.
"""

from typing import List, Tuple

PEGS = ("x", "y", "z")

# The knowledge. Nothing here mentions a disk, a peg, or a size -- `main`
# checks that rather than trusting it, because it is the whole experiment.
RULES = """
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
                      { +want(on(?d, ?t)) } )

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

rule <move> = causes( { +want(on(?d, ?p)), +peg(?p), +on(?d, ?from),
                         +at(?d, ?was), +clear(?d), +clear(?to),
                         +fits(?d, ?to), +at(?to, ?p) },
                       { +on(?d, ?to), -on(?d, ?from), +clear(?from),
                         -clear(?to), -want(on(?d, ?p)),
                         +at(?d, ?p), -at(?d, ?was) } )

rule <move-bare> = causes( { +want(on(?d, ?p)), +peg(?p), +clear(?p),
                              +on(?d, ?from), +at(?d, ?was), +clear(?d),
                              +fits(?d, ?p) },
                            { +on(?d, ?p), -on(?d, ?from), +clear(?from),
                              -clear(?p), -want(on(?d, ?p)),
                              +at(?d, ?p), -at(?d, ?was) } )

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

    print()
    print("  the ablation -- each rule removed in turn, on 4 disks:")
    survivors = []
    for name in re.findall(r"rule <([^>]+)>", RULES):
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
    return bad


if __name__ == "__main__":
    raise SystemExit(main())

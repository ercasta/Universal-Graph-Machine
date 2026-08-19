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
rule <bigger> = implies( { +smaller(?a,?b), +smaller(?b,?c) }, { +smaller(?a,?c) } )
rule <fits-peg>  = implies( { +disk(?d), +peg(?p) }, { +fits(?d, ?p) } )
rule <fits-disk> = implies( { +smaller(?d, ?e) }, { +fits(?d, ?e) } )

# -- a call, as a state machine over one minted node ------------------------

# A call on the smallest disk has nothing to unstack: place it.
rule <base> = implies( { +phase(?c, start), +call(?c, ?d, ?f, ?t, ?s),
                         +smallest(?d) },
                       { -phase(?c, start), +phase(?c, placing) } )

# Otherwise a CHILD call moves the sub-tower to the spare peg, and the pegs
# rotate exactly as the recursive definition rotates them.
rule <descend> = implies( { +phase(?c, start), +call(?c, ?d, ?f, ?t, ?s),
                            +next(?e, ?d) },
                          { -phase(?c, start), +phase(?c, unstacking),
                            +call(+k, ?e, ?f, ?s, ?t), +phase(+k, start),
                            +child(?c, +k) } )

rule <unstacked> = implies( { +phase(?c, unstacking), +child(?c, ?k), +done(?k) },
                            { -phase(?c, unstacking), +phase(?c, placing),
                              -child(?c, ?k) } )

# Placing is the only phase that asks for an action.
rule <ask> = implies( { +phase(?c, placing), +call(?c, ?d, ?f, ?t, ?s) },
                      { +want(on(?d, ?t)) } )

rule <placed> = implies( { +phase(?c, placing), +call(?c, ?d, ?f, ?t, ?s),
                           +at(?d, ?t) },
                         { -phase(?c, placing), +phase(?c, restacking) } )

rule <ascend> = implies( { +phase(?c, restacking), +call(?c, ?d, ?f, ?t, ?s),
                           +next(?e, ?d) },
                         { -phase(?c, restacking), +phase(?c, waiting),
                           +call(+k, ?e, ?s, ?t, ?f), +phase(+k, start),
                           +child(?c, +k) } )

rule <leaf> = implies( { +phase(?c, restacking), +call(?c, ?d, ?f, ?t, ?s),
                          +smallest(?d) },
                        { -phase(?c, restacking), +done(?c) } )

rule <restacked> = implies( { +phase(?c, waiting), +child(?c, ?k), +done(?k) },
                            { -phase(?c, waiting), +done(?c) } )

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

rule <finished> = implies( { +done(whole) }, { +enough(solved) } )
"""


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
    L.append("fact +call(whole, d%d, %s, %s, %s)" % (n, pegs[0], target, spare))
    L.append("fact +phase(whole, start)")
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

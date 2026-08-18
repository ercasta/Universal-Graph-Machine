"""A walker is a position on a NODE, and it is an ordinary fact.

    python -m ugm.walkers

The design has three positions already and none of them is this one:

| | differs in | mechanism |
|---|---|---|
| agents (`ugm.table`) | what they **believe** | separate graphs |
| experts (`ugm.experts`) | what they **know how to do** | a rule pool |
| frames (`gate.Frame`) | **when**, and under what supposition | seat and topic, both moments |
| **walkers** | **where in the structure** | `at(<w>, <node>)` -- this file |

A frame is not the missing one, and the confusion is worth naming because it
cost an hour: `frame(seat, topic)` is a position in the CHAIN. Both members are
moments. It answers *as of when*, never *about what*. So a walker needs no
frame, no register and no engine change: its whole state is a fact.

    at(<walker>, <node>)        where it stands
    child(<walker>, <node>)     a walker it spawned, minted from bound variables

Both are ordinary. `child(?w, ?y)` is a compound term over BOUND variables, so
the gate accepts it -- what a rule may not do is conclude about a variable
nothing binds, and this binds both. That is the whole of spawning.

## A walker SPAWNS rather than MOVES, and the reason is a measurement

The obvious design has a walker step from node to node, denying its old
position. It loses branches, silently:

    <step> = causes( { +at(?w,?x), +door(?x,?y) }, { -at(?w,?x), +at(?w,?y) } )
    <fork> = causes( { +at(?w,?x), +door(?x,?y) }, { +at(child(?w,?y), ?y) } )

Both want `at(w, r2)`. Whichever applies first denies it, and the other is not
refused -- it is DEFERRED until its premise no longer exists. Arbitration
decided the shape of the search, and nothing said so. On the maze below that run
finds nothing at all, and it is the cheapest-looking of the three:

    spawn (no move)        ticks   7   max window 1   tried 146   found 1
    move + fork            ticks   4   max window 2   tried  88   found 0
    move + fork, ordered   ticks   7   max window 1   tried 152   found 1

**The run that fails is the one that looks efficient.** Fewer ticks, less work,
no error, no diagnostic. That is this repository's standing failure mode
arriving in a new place, and it is why the check below asserts the absence of a
find rather than the presence of one.

The third row is the repair that is not one. `overrides(<fork>, <step>)` was
meant to order the two; what it actually does is make `<step>` undead -- its
positions are IDENTICAL to spawn-only, so it never applied once, and the extra
six `tried` is the price of carrying a rule that cannot fire. `overrides` is per
RULE, and what a walker wants is *fork before stepping AT THIS NODE* -- narrower
than a rule, wider than one instantiation. `overrides` is too broad and
`supersedes` too narrow; both were measured before, and this is a third case
where neither grain fits.

So: spawning has no premise to contend over, and the design question disappears
rather than being solved.

## What the spawn design buys, stated as numbers

**The option set per move is ONE.** Every window in the spawn run has size 1 --
a walker never weighs two moves, because the branching lives in the walker
POPULATION rather than in any walker's choice. That is the whole argument for a
walker having a small action space: *which move was good* is answerable when
there is one option and hopeless when there are forty, so credit assignment
becomes possible at all. Nothing here learns yet; this is the property that
makes learning worth attempting.

**A walker's identity is its path.** `child(child(w1, r2), r4)` is not a label,
it is the route: r1, then r2, then r4. Provenance falls out of minting identity
from bound variables, and nothing records it.

## What this does not do

**Cycles are unbounded.** `child(child(child(...)))` grows without limit on a
maze with a loop, and the guard a corpus would reach for -- *do not go where you
have been* -- is a negation over entries, where `-` means DENIED rather than
absent. The first version of this file was written with `-seen(?w, ?y)` and
matched nothing at all. The honest fix is the stratum-0 bridge `ugm.interpret`
uses, and it is deliberately not done here: this file is about position, and
that is about negation.

**Nothing is scheduled.** The walkers run under the ordinary loop, in whatever
order arbitration picks. A declared-order scheduler is `ugm.table`'s problem
already solved, and only speculative walkers -- ones at different SEATS -- would
need it, because only those have separate materialised states.

**Nothing waits.** A walker that parks until a subgoal completes is `dormant`
until something claims `due`, which is shipped and untouched here.
"""

from typing import Dict, List, Tuple

from .attention import run as loop
from .machine import Machine
from .text import load

# The world: a maze with one branch that matters. `r4` is reachable only by
# taking the second door out of `r2`, so a design that loses a branch loses the
# treasure -- which is the only reason this fixture has the shape it has.
MAZE = """
fact +door(r1, r2)
fact +door(r1, r5)
fact +door(r2, r3)
fact +door(r2, r4)
fact +treasure(r4)
fact +at(w1, r1)

rule <grab> = implies( { +at(?w, ?x), +treasure(?x) }, { +found(?w, ?x) } )
"""

SPREAD = """
rule <spread> = implies( { +at(?w, ?x), +door(?x, ?y) },
                         { +at(child(?w, ?y), ?y) } )
"""

MOVE = """
rule <step> = causes( { +at(?w, ?x), +door(?x, ?y) },
                      { -at(?w, ?x), +at(?w, ?y) } )
rule <fork> = causes( { +at(?w, ?x), +door(?x, ?y) },
                      { +at(child(?w, ?y), ?y) } )
"""

ORDERED = MOVE + "\nfact overrides(<fork>, <step>)\n"


def _run(extra: str, limit: int = 300) -> Dict[str, object]:
    m = Machine()
    kb = load(m, MAZE + extra, None, None)
    rep = loop(m, limit=limit)
    seen: Dict[str, str] = {}
    for mo in m.chain.moments:
        for e in mo.delta:
            seen[m.g.show(e.proposition)] = e.sign
    return {
        "at": sorted(k for k in seen if k.startswith("at(") and seen[k] == "+"),
        "found": sorted(k for k in seen if k.startswith("found(") and seen[k] == "+"),
        "ticks": len(rep.steps),
        "window": max(rep.windows or [0]),
        "tried": rep.tried,
    }


def main() -> int:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    failing, ran = 0, 0

    def gate(name: str, ok: bool) -> None:
        nonlocal failing, ran
        ran += 1
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
        if not ok:
            failing += 1

    print(__doc__)

    spawn = _run(SPREAD)
    move = _run(MOVE)
    order = _run(ORDERED)

    print("  three designs, one maze:\n")
    for label, r in (("spawn (no move)", spawn), ("move + fork", move),
                     ("move + fork, ordered", order)):
        print(f"    {label:22} ticks {r['ticks']:3}  max window {r['window']}  "
              f"tried {r['tried']:4}  walkers {len(r['at'])}  "
              f"found {len(r['found'])}")
    print("\n  where the spawn design left its walkers:\n")
    for w in spawn["at"]:
        print(f"    {w}")
    print()

    gate("a walker SPAWNS and the treasure is found -- the branch that leads to "
         "it is taken as well as the one that does not",
         len(spawn["found"]) == 1)
    gate("every reachable node ends up with a walker on it, and the maze has "
         f"five ({len(spawn['at'])})",
         len(spawn["at"]) == 5)
    gate("a walker's IDENTITY IS ITS PATH -- the finder is named by the route "
         "it took, and nothing recorded that",
         spawn["found"] == ["found(child(child(w1, r2), r4), r4)"])
    gate("ONE option is weighed per move: the branching is in the walker "
         "population, not in any walker's choice, which is what makes credit "
         f"assignment tractable (max window {spawn['window']})",
         spawn["window"] == 1)

    # The failure that motivated the design, asserted as an ABSENCE. A check
    # written the other way round -- *spawn finds it* -- passes without ever
    # noticing that the obvious design does not.
    gate("MOVING LOSES A BRANCH, SILENTLY: `<step>` and `<fork>` contend for the "
         "same position, whichever applies first denies it, and the treasure is "
         f"never found -- in FEWER ticks and less work than the run that "
         f"succeeds ({move['ticks']} vs {spawn['ticks']} ticks, "
         f"{move['tried']} vs {spawn['tried']} tried)",
         len(move["found"]) == 0 and move["ticks"] < spawn["ticks"]
         and move["tried"] < spawn["tried"])
    gate("...and the contention is visible as a window of two, where the spawn "
         "design never weighs more than one",
         move["window"] > spawn["window"])

    # And the repair that is not one.
    gate("`overrides(<fork>, <step>)` does not ORDER the two rules, it removes "
         "one: the ordered run's positions are identical to spawn-only, so "
         "`<step>` never applied once, and the extra work is a rule that cannot "
         f"fire ({order['tried']} vs {spawn['tried']} tried)",
         order["at"] == spawn["at"] and order["tried"] > spawn["tried"])

    print(f"\n{ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())

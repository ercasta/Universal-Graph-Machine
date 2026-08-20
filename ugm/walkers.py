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

    spawn (no move)        ticks   8   per walker 1   tried 192   found 1
    move + fork            ticks   4   per walker 2   tried 100   found 0
    move + fork, ordered   ticks   8   per walker 1   tried 200   found 1

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

**The option set per WALKER is ONE.** No walker in the spawn run ever has two
applications weighed about it -- the branching lives in the walker POPULATION
rather than in any walker's choice. That is the whole argument for a walker
having a small action space: *which move was good* is answerable when there is
one option and hopeless when there are forty, so credit assignment becomes
possible at all. Nothing here learns yet; this is the property that makes
learning worth attempting.

⚠⚠⚠ **Per walker, and it used to be measured per WINDOW, which is not the same
claim and broke the day something unrelated moved.** A window holds every
application the agent weighed across ALL walkers, so two walkers with one option
each make a window of two while nothing about any walker's choice has changed.
It read 1 by luck: scores are equal at the floor, so which rules reach a
shortlist is decided by declaration rank, and adding three rules to the bundle --
rules that never match in this file at all -- shifted every corpus rule by three
and made it 2. The measurement was of the table's layout, not of this design.
The distinction it now draws is sharper as well as sounder: `move + fork` weighs
two options ABOUT ONE WALKER, which is exactly the contention this file is
about.

**A walker's identity is its path.** `child(child(w1, r2), r4)` is not a label,
it is the route: r1, then r2, then r4. Provenance falls out of minting identity
from bound variables, and nothing records it.

## What goes in the identity term is the deduplication policy

Two routes into one room. `child(?w, ?y)` names a walker by the PATH it took, so
two arrivals at the same node are two walkers -- and each explores the subtree
below it again. Chained diamonds, measured:

    1 diamond(s),  4 rooms:  by-path    5   by-node    4
    2 diamond(s),  7 rooms:  by-path   13   by-node    7
    3 diamond(s), 10 rooms:  by-path   29   by-node   10

`2^(n+2) - 3` against `3n + 1`. Nothing errors, the treasure is still found, and
the run simply does exponentially more of the same work: the third case for
running out of everything before anything says so.

`walker(?y)` fixes it in one word, and the fix is INTERNING rather than a guard:
`g.rel` returns the same node for the same relation and members, so two arrivals
at `r4` mint one walker and the second is not a new fact at all. No visited set,
no negation -- which matters, because the negation a visited set wants is over
entries, where `-` means DENIED rather than absent, and the first draft of this
file matched nothing for exactly that reason.

The general term is `walker(<node>, <purpose>)`, and both designs are its special
cases: drop the purpose and arrivals merge, make the purpose the path and they
never do. So the identity term IS the policy, stated where a reader can see it.

**And deduplicating is not forgetting.** Identity is WHERE a walker is;
provenance is HOW it got there, and provenance is plural. One walker at `r4`,
both routes recorded:

    at(walker(r4), r4)
    came(walker(r4), via(walker(r2), r2))
    came(walker(r4), via(walker(r3), r3))

## An expert is a PREMISE, not a pool

`ugm.experts` gives a rule set read off the graph -- `knows(<e>, <r>)`,
`extends(<e>, <f>)`, inheritance as one ordinary rule -- and hands it to a run as
`pool`. That is one rule set for a whole run, so it cannot say *this rule applies
to walkers running E*, which is what a swarm needs.

Scoping by PREMISE can, and costs nothing:

    fact +knows(scout, moving)         fact +extends(raider, scout)
    fact +knows(looter, grabbing)      fact +extends(raider, looter)

    rule <extend> = implies( { +extends(?e,?f), +knows(?f,?c) }, { +knows(?e,?c) } )
    rule <equip>  = implies( { +runs(?w,?e),    +knows(?e,?c) }, { +can(?w,?c)   } )

    rule <grab>   = implies( { +at(?w,?x), +can(?w, grabbing), +treasure(?x) },
                             { +found(?w,?x) } )

Multiple inheritance falls out: two `extends` facts both match, so `raider` has
`moving` from one parent and `grabbing` from the other, through one rule and no
resolution order. And a SPAWNING rule chooses the child's expert, which is what
*spawn an expert at a node* means here -- pass `?e` down and the child inherits
the role, name another and it does not. Measured: with children spawned as
`scout`, the treasure is never taken, because a scout cannot loot.

## Termination is a DENIAL, and it is not retroactive

Every walker-relative rule needs `at(?w, ?x)`, so denying that one fact removes
the walker from all of them at once:

    rule <done> = implies( { +found(?w,?x) }, { -at(?w,?x) } )

No scheduler, no registry, no removal step -- there is nothing holding the walker
except the fact that it is somewhere.

What it does NOT do is undo. The looted walker spread to the next room BEFORE it
was terminated, and which of the two happened first was decided by arbitration
with nothing saying so.

## Precedence only bites when the loser's PREMISE CAN BE DESTROYED

Four attempts to order rules in this file behaved four different ways, and the
rule behind all of them is one sentence.

    <fork> vs <step>        the loser's premise is DENIED by the winner
                            -> ordering decides the outcome, silently
    <spread> vs <done>      same, and the ordering that decides it is the
                            order the rules were DECLARED IN: spread first and
                            the walker reaches the next room, spread last and
                            it never does
    overrides(fork, step)   the winner matches wherever the loser does
                            -> the loser never gets a tick at all
    overrides(grab, spread) the winner matches only where treasure is
                            -> the loser is suppressed there and nowhere else
    two corridors           monotone rules, nothing destroyed
                            -> B is fully explored either way, 17 ticks vs 21

`overrides` suppresses per TICK and per RULE, whenever the defeater matches
anywhere. Because the loop runs to quiescence, a merely-deferred rule applies on
some later tick and the final state is the same -- *ordering is not
defeasibility*, this design's own line, arriving from a fourth direction. The
only time order changes what is CONCLUDED is when the winner destroys what the
loser needed.

So the spawn design does more than keep branches: **nothing is consumed, so
ordering is irrelevant, so the per-position precedence a moving walker wanted is
not needed at all.** The missing mechanism was missing because of the other
design.

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


# Two routes into one room, and n of them in series. The walker count is the
# whole measurement, so the maze is generated rather than written out: a fixture
# with one diamond cannot show a growth rate.
def _diamonds(n: int) -> str:
    lines, node = [], "r0"
    for i in range(n):
        a, b, j = f"a{i}", f"b{i}", f"j{i}"
        lines += [f"fact +door({node}, {a})", f"fact +door({node}, {b})",
                  f"fact +door({a}, {j})", f"fact +door({b}, {j})"]
        node = j
    lines += ["fact +at(w1, r0)", f"fact +treasure({node})"]
    return chr(10).join(lines) + chr(10)


BY_PATH = """
rule <spread> = implies( { +at(?w, ?x), +door(?x, ?y) },
                         { +at(child(?w, ?y), ?y) } )
"""

BY_NODE = """
rule <spread> = implies( { +at(?w, ?x), +door(?x, ?y) },
                         { +at(walker(?y), ?y) } )
"""

# ...and the same, keeping the routes. `came` is plural by construction: two
# arrivals are two entries about one walker, which is the honest record.
BY_NODE_TRACKED = """
rule <spread> = implies( { +at(?w, ?x), +door(?x, ?y) },
                         { +at(walker(?y), ?y), +came(walker(?y), via(?w, ?x)) } )
"""


def _population(src: str, limit: int = 2000) -> Dict[str, List[str]]:
    m = Machine()
    load(m, src, None, None)
    loop(m, limit=limit)
    seen: Dict[str, str] = {}
    for mo in m.chain.moments:
        for e in mo.delta:
            seen[m.g.show(e.proposition)] = e.sign
    return {
        "at": sorted(k for k in seen if k.startswith("at(") and seen[k] == "+"),
        "came": sorted(k for k in seen if k.startswith("came(") and seen[k] == "+"),
        "found": sorted(k for k in seen if k.startswith("found(") and seen[k] == "+"),
    }


# Experts scoped by premise. `raider` inherits from two parents, so the
# inheritance rule has to cope with multiple `extends` facts -- which it does by
# matching both, with no resolution order to declare.
EXPERTS = """
fact +knows(scout,  moving)
fact +knows(looter, grabbing)
fact +extends(raider, scout)
fact +extends(raider, looter)

rule <extend> = implies( { +extends(?e, ?f), +knows(?f, ?c) }, { +knows(?e, ?c) } )
rule <equip>  = implies( { +runs(?w, ?e), +knows(?e, ?c) },    { +can(?w, ?c) } )

rule <grab>   = implies( { +at(?w, ?x), +can(?w, grabbing), +treasure(?x) },
                         { +found(?w, ?x) } )
rule <done>   = implies( { +found(?w, ?x) }, { -at(?w, ?x) } )
"""

# The spawning rule CHOOSES the child's expert. `?e` passes the parent's role
# down; a literal would hand the child a different one.
INHERIT_ROLE = """
rule <spread> = implies( { +at(?w, ?x), +runs(?w, ?e), +can(?w, moving),
                           +door(?x, ?y) },
                         { +at(walker(?y), ?y), +runs(walker(?y), ?e) } )
"""

AS_SCOUTS = """
rule <spread> = implies( { +at(?w, ?x), +can(?w, moving), +door(?x, ?y) },
                         { +at(walker(?y), ?y), +runs(walker(?y), scout) } )
"""

# A raider with both capabilities directly, so the DECLARATION-ORDER fixture
# varies only the thing it is about. Written out rather than reusing `EXPERTS`,
# which would drag the inheritance rules into the comparison.
FLAT_EQUIP = """
fact +knows(raider, moving)
fact +knows(raider, grabbing)
rule <equip> = implies( { +runs(?w, ?e), +knows(?e, ?c) }, { +can(?w, ?c) } )
"""

FLAT_GRAB = """
rule <grab> = implies( { +at(?w, ?x), +can(?w, grabbing), +treasure(?x) },
                       { +found(?w, ?x) } )
rule <done> = implies( { +found(?w, ?x) }, { -at(?w, ?x) } )
"""


CORRIDOR = """
fact +door(r1, r2)
fact +door(r2, r3)
fact +treasure(r2)
fact +at(w1, r1)
fact +runs(w1, raider)
"""

# Two disconnected corridors, treasure in one. A single-corridor fixture cannot
# show whether suppressing a rule stalls an UNRELATED walker.
TWO_CORRIDORS = """
fact +door(a1, a2)
fact +door(a2, a3)
fact +door(b1, b2)
fact +door(b2, b3)
fact +treasure(a2)
fact +at(wa, a1)
fact +runs(wa, raider)
fact +at(wb, b1)
fact +runs(wb, raider)
fact +knows(raider, moving)
fact +knows(raider, grabbing)
"""


def _walk(src: str, limit: int = 800) -> Dict[str, object]:
    m = Machine()
    load(m, src, None, None)
    rep = loop(m, limit=limit)
    seen: Dict[str, str] = {}
    for mo in m.chain.moments:
        for e in mo.delta:
            seen[m.g.show(e.proposition)] = e.sign
    return {
        "live": sorted(k for k in seen if k.startswith("at(") and seen[k] == "+"),
        "dead": sorted(k for k in seen if k.startswith("at(") and seen[k] == "-"),
        "found": sorted(k for k in seen if k.startswith("found(") and seen[k] == "+"),
        "knows": sorted(k for k in seen if k.startswith("knows(raider")
                        and seen[k] == "+"),
        "ticks": len(rep.steps),
    }


def _run(extra: str, limit: int = 300) -> Dict[str, object]:
    m = Machine()
    kb = load(m, MAZE + extra, None, None)
    # ⚠⚠⚠ **Per WALKER, not per window, and the difference is the whole claim.**
    # This read `max(rep.windows)` and called it *one option is weighed per
    # move*. It is not the same measurement: a window holds every application
    # the agent weighed, across ALL walkers, so two walkers with one option each
    # make a window of two and nothing about any walker's choice has changed.
    #
    # It read 1 for a long time by luck. Scores are equal at the floor, so which
    # rules reach a shortlist is decided by declaration RANK -- and adding three
    # rules to the bundle, which never match here at all, shifted every corpus
    # rule by three and made it 2. A check that an unrelated change can break
    # was measuring the table's layout, not this file's design.
    #
    # The claim is *the branching lives in the walker POPULATION rather than in
    # any walker's choice*, so the measurement is: group each window by the
    # walker its applications are about, and take the largest group.
    per_walker = []

    def watch(mm, table, window, chosen, tick, step=None):
        by: Dict[object, int] = {}
        for a in window:
            for var, val in a.bindings.items():
                if mm.g.show(var) == "?w":
                    by[val] = by.get(val, 0) + 1
        per_walker.append(max(by.values()) if by else 1)

    rep = loop(m, limit=limit, watch=watch)
    seen: Dict[str, str] = {}
    for mo in m.chain.moments:
        for e in mo.delta:
            seen[m.g.show(e.proposition)] = e.sign
    return {
        "at": sorted(k for k in seen if k.startswith("at(") and seen[k] == "+"),
        "found": sorted(k for k in seen if k.startswith("found(") and seen[k] == "+"),
        "ticks": len(rep.steps),
        "window": max(per_walker or [0]),
        "weighed": max(rep.windows or [0]),
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

    # -- what the identity term decides ------------------------------------
    print("\n  two routes into one room, n diamonds in series:\n")
    growth = []
    for n in (1, 2, 3):
        by_path = _population(_diamonds(n) + BY_PATH)
        by_node = _population(_diamonds(n) + BY_NODE)
        growth.append((n, 1 + 3 * n, len(by_path["at"]), len(by_node["at"])))
        print(f"    {n} diamond(s), {1 + 3 * n:2} rooms:   "
              f"by-path {len(by_path['at']):4}   by-node {len(by_node['at']):4}")
    print()

    gate("naming a walker by its PATH duplicates it wherever routes converge, "
         "and each duplicate explores the subtree below AGAIN -- exponential "
         f"against linear ({[g[2] for g in growth]} vs {[g[3] for g in growth]})",
         [g[2] for g in growth] == [5, 13, 29]
         and [g[3] for g in growth] == [4, 7, 10])
    gate("...and it is SILENT: nothing errors and the treasure is still found, "
         "so the only symptom is doing exponentially more of the same work",
         len(_population(_diamonds(2) + BY_PATH)["at"])
         > len(_population(_diamonds(2) + BY_NODE)["at"]))
    gate("naming it by the NODE deduplicates by INTERNING rather than by a "
         "guard: two arrivals mint one walker, so there is no visited set and "
         "no negation to get wrong",
         [g[3] for g in growth] == [g[1] for g in growth])

    tracked = _population(_diamonds(1) + BY_NODE_TRACKED)
    print("  deduplicating is not forgetting:\n")
    for k in tracked["came"]:
        print(f"    {k}")
    print()
    joins = [k for k in tracked["came"] if k.startswith("came(walker(j0)")]
    gate("one walker per room, and BOTH routes into the join recorded -- "
         "identity is WHERE it is, provenance is HOW it got there, and "
         f"provenance is plural ({len(tracked['at'])} walkers, "
         f"{len(joins)} routes into the join)",
         len(tracked["at"]) == 4 and len(joins) == 2)


    # -- experts as premises, and termination ------------------------------
    role = _walk(CORRIDOR + EXPERTS + INHERIT_ROLE)
    scouts = _walk(CORRIDOR + EXPERTS + AS_SCOUTS)
    print("\n  a raider that inherits from two experts:\n")
    for k in role["knows"]:
        print(f"    {k}")
    print(f"\n    live {role['live']}\n    dead {role['dead']}\n"
          f"    found {role['found']}\n")

    gate("MULTIPLE INHERITANCE through one ordinary rule: `raider` extends two "
         "experts and has a capability from each, with no resolution order to "
         f"declare ({role['knows']})",
         role["knows"] == ["knows(raider, grabbing)", "knows(raider, moving)"])
    gate("the SPAWNING rule chooses the child's expert -- pass `?e` down and "
         "the child loots, spawn it as a `scout` and the treasure is never "
         "taken, because a scout cannot",
         len(role["found"]) == 1 and len(scouts["found"]) == 0)
    gate("TERMINATION IS A DENIAL: one `-at(?w, ?x)` removes the walker from "
         "every relative rule at once, because they all need it -- no "
         "scheduler, no registry, nothing else holding it",
         role["dead"] == ["at(walker(r2), r2)"])
    # ...and the sharper form of the same finding. `<done>` DENIES the
    # position, so it can destroy what `<spread>` needed -- and which of them
    # gets there first is decided by the order the rules were DECLARED IN.
    # Same rules, same facts, different conclusion, no diagnostic.
    first = _walk(CORRIDOR + FLAT_EQUIP + INHERIT_ROLE + FLAT_GRAB)
    last = _walk(CORRIDOR + FLAT_EQUIP + FLAT_GRAB + INHERIT_ROLE)
    print(f"  the same rules, declared in two orders:\n\n"
          f"    spread declared FIRST   live {first['live']}\n"
          f"    spread declared LAST    live {last['live']}\n")

    gate("...and TERMINATION IS NOT RETROACTIVE, which shows up as the authored "
         "ORDER OF RULES changing what is concluded: declare `<spread>` before "
         "`<done>` and the walker reaches the next room before it is "
         "terminated, declare it after and it never does -- same rules, same "
         "facts, no diagnostic",
         "at(walker(r3), r3)" in first["live"]
         and "at(walker(r3), r3)" not in last["live"])

    # -- what precedence actually does -------------------------------------
    plain = _walk(TWO_CORRIDORS + EXPERTS.replace(
        "fact +knows(scout,  moving)\nfact +knows(looter, grabbing)\n"
        "fact +extends(raider, scout)\nfact +extends(raider, looter)\n", "")
        + INHERIT_ROLE)
    ordered = _walk(TWO_CORRIDORS + EXPERTS.replace(
        "fact +knows(scout,  moving)\nfact +knows(looter, grabbing)\n"
        "fact +extends(raider, scout)\nfact +extends(raider, looter)\n", "")
        + INHERIT_ROLE + "\nfact overrides(<grab>, <spread>)\n")
    b_plain = [k for k in plain["live"] if "(b" in k]
    b_order = [k for k in ordered["live"] if "(b" in k]
    print(f"  two corridors, treasure in one:\n\n"
          f"    no precedence      ticks {plain['ticks']:3}  B reached {len(b_plain)}\n"
          f"    grab over spread   ticks {ordered['ticks']:3}  B reached {len(b_order)}\n")

    # ⚠⚠⚠ **THE TICK COUNT IS NOT ASSERTED, and that is the third time this
    # fixture has been moved by an edit somewhere else.** It read
    # `ordered["ticks"] != plain["ticks"]` -- *ordering changed WHEN* -- and the
    # two counts now coincide at 18, because retiring `<relevant>` made the
    # bundle one rule shorter and declaration RANK is what breaks the tie when
    # scores are equal at the floor. The call-stack rules did the same in 20e,
    # and a bundled `<unattended>` did it again.
    #
    # > **A check on a tick count in this fixture is measuring the size of the
    # > bundle, not the thing it names.**
    #
    # What the claim is actually about survives untouched and is what is gated:
    # nothing was destroyed, so the unrelated corridor is fully explored either
    # way. The counts are printed above, where a drift is visible without being
    # load-bearing.
    gate("PRECEDENCE ONLY BITES WHEN THE LOSER'S PREMISE CAN BE DESTROYED: with "
         "monotone rules the unrelated corridor is explored either way, so "
         f"ordering changed nothing about WHAT ({plain['ticks']} ticks vs "
         f"{ordered['ticks']}, both reaching {len(b_plain)} rooms in B)",
         b_plain == b_order and len(b_plain) == 2)


    print(f"\n{ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())

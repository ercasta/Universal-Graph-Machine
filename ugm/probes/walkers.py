"""A walker is a position on a NODE, and it is an ordinary fact.

    python -m ugm.probes.walkers

The design already had three kinds of position -- what agents believe, what
experts know how to do, and when/under-what-supposition a frame stands -- and
none of them is *where in the structure*. That is `at(<w>, <node>)`, and it is
this file.

⚠ A frame is not the missing one. `frame(seat, topic)` is a position in the
CHAIN, and confusing the two cost an hour.

See docs/design/walkers.md.
"""

from typing import Dict, List, Tuple

from ..core.attention import run as loop
from ..core.machine import Machine
from ..core.text import load

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
    # ⚠⚠⚠ Per WALKER, not per window, and the difference is the whole claim.
    # This read max(rep.windows) and called it *one option is weighed per
    # move*.
    # → docs/design/walkers.md#per-walker-not-per-window-and-the-differ
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

    # ⚠⚠⚠ THE TICK COUNT IS NOT ASSERTED, and that is the third time this
    # fixture has been moved by an edit somewhere else.
    # → docs/design/walkers.md#the-tick-count-is-not-asserted-and-that-i
    gate("PRECEDENCE ONLY BITES WHEN THE LOSER'S PREMISE CAN BE DESTROYED: with "
         "monotone rules the unrelated corridor is explored either way, so "
         f"ordering changed nothing about WHAT ({plain['ticks']} ticks vs "
         f"{ordered['ticks']}, both reaching {len(b_plain)} rooms in B)",
         b_plain == b_order and len(b_plain) == 2)


    print(f"\n{ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())

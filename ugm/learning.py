"""Does an episode teach the next one anything? (§19, §20)

Learning here is offline and it is a **corpus**: an episode ends, `review` and
`blame` walk the trail, and `learned()` writes surface text the next episode
loads. Nothing about the loop changes. So the question this instrument asks is
the only one that matters about it -- **run the same world twice and see whether
the second run is better** -- and its gate is that the answer can be no.

    python -m ugm.learning

The world is the one `forgoing2` built, because it is the only kind that can
measure a chooser: two ways to get water, and one of them breaks a jug another
goal needs. Everything upstream of forgoing was measured in a world where the
agent took the good route AND the bad one, so *choose the better rule* had no
content and an exact recall table bought nothing (`experience`). It has content
now, and the arena is a single line of authored order:

    <use-jug> written first  ->  the jug is smashed
    <use-tap> written first  ->  the jug survives

Nothing else in the corpus differs. Two thirds of this agent's arbitrations are
settled by typing order, and this is one of them, with a cost attached.

⭐⭐⭐ **What it measured, and the reason this file exists.** Blame alone does not
close the loop. An episode that smashed the jug blames the smasher and drops it
from what it recommends -- and then **smashes the jug again**, because omitting a
rule leaves it exactly where it was, first in authored order.

> **Suppression is not a decision.** It says *do not recommend this*. It cannot
> say *do that instead*, and only the second changes a run.

The missing half was already on the trail. `forgone(A, w)` records that `A` was a
live way of getting `w` and something else was taken, licensed by
`applied(<winner>)` -- so a blamed winner names its own alternatives. Joining the
two needs no new bookkeeping, which is the third time credit assignment has come
out that way. `Machine._instead_of` is the join and `SUPPRESSION_ONLY` below is
the control that shows it is load-bearing.
"""

from typing import Dict, List, Optional, Tuple

from .machine import Machine
from .text import load

BASE = [
    "rule <eff> = implies( { +did(?a), +achieves(?a, ?y) }, { +?y } )",
    "rule <cost> = implies( { +did(smash(?j)) }, { -intact(?j) } )",
    "rule <squeeze> = implies( { +fruit(?f), +jug(?j), +intact(?j) }, { +juice(?j) } )",
]
TAP = ("rule <use-tap> = implies( { +goal(water(?w)), +tap(?t), +under(?w, ?t) },"
       " { +doing(fill(?w)) } )")
JUG = ("rule <use-jug> = implies( { +goal(water(?w)), +jug(?j), +holds(?j, ?w) },"
       " { +doing(smash(?j)) } )")


def world(vessel: str = "kettle", jug: str = "jug1", jug_first: bool = True) -> str:
    """Two routes to water, one of which costs a jug a second goal needs.

    Parameterised on the objects rather than hard-coded, because what an episode
    carries forward is keyed on a goal's RELATION -- so whether it transfers is a
    question about a different `vessel` and `jug`, and a fixture that cannot vary
    them would report generalisation it never tested.
    """
    routes = [JUG, TAP] if jug_first else [TAP, JUG]
    return "\n".join(routes + BASE + [
        f"fact +achieves(fill({vessel}), water({vessel}))",
        f"fact +achieves(smash({jug}), water({vessel}))",
        "fact +tap(sink)", f"fact +under({vessel}, sink)",
        f"fact +jug({jug})", f"fact +holds({jug}, {vessel})", f"fact +intact({jug})",
        "fact +fruit(orange)",
        f"fact +goal(water({vessel}))",
        f"fact +goal(juice({jug}))",
        "",
    ])


class Episode:
    """One run, and what it has to say to the next."""

    def __init__(self, src: str, vessel: str = "kettle", jug: str = "jug1") -> None:
        self.m = Machine()
        self.m.actuator("hands")
        self.kb = load(self.m, src)
        self.steps = self.m.run(limit=4000)
        self.acts = [self.m.g.show(n) for n in self.m.emitted]
        self.intact = self.m.holds(self.kb.term(f"intact({jug})"))
        self.water = self.m.holds(self.kb.term(f"water({vessel})"))
        self.juice = self.m.holds(self.kb.term(f"juice({jug})"))
        self.blamed = sorted({r.name for r, _ in self.m.blame()})
        self.rows = self.m.learned()

    @property
    def harmed(self) -> bool:
        """Did this run destroy something it also wanted? The whole outcome
        measure, and deliberately about a LOST subgoal rather than a failed
        episode -- §9's distinction is what makes it attributable at all."""
        return self.intact == "-"


def run(jug_first: bool = True, rounds: int = 3, carry: str = "") -> List[Episode]:
    """Play the same world `rounds` times, each one loading what the last wrote."""
    out: List[Episode] = []
    for _ in range(rounds):
        ep = Episode(world(jug_first=jug_first) + carry)
        out.append(ep)
        carry = "\n".join(ep.rows) + "\n" if ep.rows else ""
    return out


def _no_promotion():
    """The control: blame still suppresses, but nothing promotes an alternative.

    This is the state of the code before this session, and it is what makes the
    headline falsifiable -- take the join away and the second episode must go
    wrong again, or the join was never what fixed it.
    """
    original = Machine._instead_of
    Machine._instead_of = lambda self, harmed: []  # type: ignore[assignment]
    return original


def main() -> int:
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    failing = 0

    def gate(name: str, ok: bool) -> None:
        nonlocal failing
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
        if not ok:
            failing += 1

    print(__doc__.strip().split("\n")[0])
    print()

    # -- the arena, before anything is learned ----------------------------
    print("The choice, and what settles it -- one line of authored order:\n")
    print(f"  {'authored first':<16} {'emitted':<16} {'jug':<6} {'water':<6} {'juice':<6}")
    first = {}
    for jug_first in (False, True):
        ep = Episode(world(jug_first=jug_first))
        first[jug_first] = ep
        label = "<use-jug>" if jug_first else "<use-tap>"
        print(f"  {label:<16} {ep.acts[0] if ep.acts else '-':<16} "
              f"{'broken' if ep.harmed else 'intact':<6} {str(ep.water):<6} {str(ep.juice):<6}")
    print()
    gate("a wrong choice costs something, so there is something to learn",
         first[True].harmed and not first[False].harmed)
    gate("...and only one act leaves the agent, so it IS a choice (forgoing)",
         len(first[True].acts) == 1 and len(first[False].acts) == 1)
    gate("the damage is attributed to the decision, not just to the physics",
         "use-jug" in first[True].blamed)

    # -- the loop ---------------------------------------------------------
    print("\nThe same world, three times, each loading what the last wrote:\n")
    print(f"  {'episode':<9} {'emitted':<16} {'jug':<8} {'blamed':<26} rows")
    eps = run(jug_first=True, rounds=3)
    for i, ep in enumerate(eps, 1):
        names = ",".join(n for n in ep.blamed) or "-"
        print(f"  {i:<9} {ep.acts[0] if ep.acts else '-':<16} "
              f"{'broken' if ep.harmed else 'intact':<8} {names:<26} {len(ep.rows)}")
    print()
    for r in eps[0].rows:
        print(f"    {r}")
    print()

    gate("the first episode does the damage", eps[0].harmed)
    gate("⭐ the second does not -- an episode taught the next one something",
         not eps[1].harmed)
    gate("and it stays taught: the third does not regress", not eps[2].harmed)
    gate("what it learned names the alternative it passed up, not just the "
         "rule it stopped recommending",
         any("<use-tap>" in r for r in eps[0].rows)
         and not any("<use-jug>" in r for r in eps[0].rows))
    gate("the repaired run achieves BOTH goals, so it is not merely doing less",
         eps[1].water == "+" and eps[1].juice == "+")

    # -- the control ------------------------------------------------------
    print("\nThe control -- blame suppresses, nothing promotes:\n")
    original = _no_promotion()
    try:
        ctrl = run(jug_first=True, rounds=2)
    finally:
        Machine._instead_of = original  # type: ignore[assignment]
    for i, ep in enumerate(ctrl, 1):
        print(f"  {i:<9} {ep.acts[0] if ep.acts else '-':<16} "
              f"{'broken' if ep.harmed else 'intact':<8} rows={len(ep.rows)}")
    print()
    gate("⭐⭐⭐ suppression alone does NOT fix it -- the agent blames the "
         "smasher, stops recommending it, and smashes the jug again",
         ctrl[0].harmed and ctrl[1].harmed)
    gate("...and it is not that it learned nothing: it wrote rows, they were "
         "just about the wrong half of the choice",
         bool(ctrl[0].rows) and not any("<use-tap>" in r for r in ctrl[0].rows))

    # -- transfer ---------------------------------------------------------
    print("\nTransfer -- what was learned about one kettle, applied to another:\n")
    taught = run(jug_first=True, rounds=1)[0].rows
    fresh = Episode(world("pot", "jug2", jug_first=True), "pot", "jug2")
    carried = Episode(world("pot", "jug2", jug_first=True) + "\n".join(taught) + "\n",
                      "pot", "jug2")
    print(f"  {'pot/jug2, no experience':<28} {fresh.acts[0] if fresh.acts else '-':<16} "
          f"{'broken' if fresh.harmed else 'intact'}")
    print(f"  {'pot/jug2, taught by kettle':<28} {carried.acts[0] if carried.acts else '-':<16} "
          f"{'broken' if carried.harmed else 'intact'}")
    print()
    gate("the fresh world still does the damage, so the fixture can fail",
         fresh.harmed)
    gate("⭐ and the key GENERALISES: a row keyed on the relation `water` saves "
         "a jug it was never told about",
         not carried.harmed)

    print(f"\n{failing} failing")
    print("""
  ⚠ WHAT THIS DOES NOT SHOW. The promoted alternative is recommended because it
  was passed up by something that harmed -- not because it is good. In a world
  where every route does damage, `learned` recommends none of them, which is
  right, and it has nothing to offer instead, which is the same gap `blame`
  has: *how badly* is unsayable while the table's numerals are non-negative.

  ⚠ And the signal is one episode deep. Nothing here weighs a route that
  usually works against one that worked once, because a second `prefer` row for
  the same rule and key does not accumulate -- restating is not revising (§8).
  That is the next thing to measure, not to assume.""")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())

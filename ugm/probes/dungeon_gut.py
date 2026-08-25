"""The dungeon, step 3: `dungeon_micro.ugm` plus a judge lane, a reflex
lane, and two main-lane rules that act on what they noticed.

    python -m ugm.probes.dungeon_gut

`judge` writes `fear(hero, $v)` when hero's own hp runs low and
`wary(hero, $e)` when a present monster outweighs hero on hp; `reflex`
auto-attends what they are about once the magnitude clears a threshold.
Two `standing` main-lane rules close the loop: `<hero-targets-threat>`
retargets onto whatever is attended as a threat, `<hero-flees>` leaves the
fight outright once hero is desperate (hp <= 3). Divergence from the plain
microprogram port's outcome is now the INTERESTING result, not a bug to
avoid -- it means the reaction fired. `dungeon_gut.ugm`'s own header has
the full account, including which seeds trade a winnable fight for safety.
"""

import random
from typing import List, Optional

from .. import corpora as _corpora
from ..core.machine import Machine
from ..core.text import load, load_file
from . import dungeon as control

CORPUS = _corpora.path("dungeon_gut.ugm")


def danger(h):
    """Hero's own hp, banded into a fear score -- close to nothing worth
    naming above 6, sharper below 3."""
    if not h.isdigit():
        return None
    h = int(h)
    if h <= 3:
        return 8
    if h <= 6:
        return 4
    return None


def scary(v):
    """A fear score loud enough to flee over -- the DESPERATE band only
    (hp <= 3), not the merely-worried one. `<hero-flees>` is gated on this,
    so the threshold here is the threshold for leaving the fight."""
    return "yes" if v.isdigit() and int(v) >= 8 else None


def stronger(enemy_hp, hero_hp):
    """Does this enemy currently outweigh hero on hp?"""
    if not (enemy_hp.isdigit() and hero_hp.isdigit()):
        return None
    return "yes" if int(enemy_hp) > int(hero_hp) else None


def fight(seed: Optional[int] = 7, limit: int = 4000):
    m = Machine()
    pre = load(m, "", scope="dungeon")
    rng = random.Random(seed)
    asked: List[str] = []

    def dice(mach, prop):
        die, _what = mach.g.members(prop)
        sides = control.DICE.get(mach.g.show(die))
        if sides is None:
            return None
        asked.append(mach.g.show(prop))
        return pre.atom(str(rng.randint(1, sides)))

    pre.answerer("dice", "roll", dice)

    def calc(op, a, b):
        if not (a.isdigit() and b.isdigit()):
            return None
        if op == "sub":
            return max(0, int(a) - int(b))
        return None

    def beats(a, b):
        if not (a.isdigit() and b.isdigit()):
            return None
        return "yes" if int(a) >= int(b) else None

    pre.computator("calc", calc)
    pre.computator("beats", beats)
    pre.computator("danger", danger)
    pre.computator("scary", scary)
    pre.computator("stronger", stronger)

    kb = load_file(m, CORPUS, scope="dungeon")
    # `turn(hero)` is background until something is asked to take care of
    # it (§20) -- the fight's own kickoff, kept here rather than in the
    # corpus (see `ugm/probes/dungeon.py`'s own comment).
    m._attend(kb.term("turn(hero)"))
    steps = m.run(limit=limit)
    return m, kb, asked, steps


def main() -> int:
    # Wider than the other probes' 14 seeds on purpose: `<hero-targets-
    # threat>` and `<hero-flees>` are independent triggers (an enemy
    # outweighing hero on hp vs. hero's own hp alone), and 1-14 happens to
    # show fleeing every time wariness fires. A standalone retarget --
    # wary without ever going desperate -- first turns up at seed 18.
    diverged = 0
    fled = 0
    retargeted = 0
    for seed in range(1, 31):
        m1, kb1, _asked1, _steps1 = control.fight(seed=seed, limit=4000)
        m2, kb2, _asked2, steps2 = fight(seed=seed, limit=4000)
        over1 = [p for p in m1.pad.believed() if m1.g.relation_of(p) is kb1.atom("over")]
        over2 = [p for p in m2.pad.believed() if m2.g.relation_of(p) is kb2.atom("over")]
        r1 = m1.g.show(over1[0]) if over1 else "UNRESOLVED"
        r2 = m2.g.show(over2[0]) if over2 else "UNRESOLVED"
        same = r1 == r2
        if not same:
            diverged += 1
        did_flee = m2.holds(kb2.term("fled(hero)"))
        targeted = [p for p in m2.pad.believed()
                    if m2.g.relation_of(p) is kb2.atom("attack")
                    and m2.g.show(m2.g.member(p, 0)) == "hero"]
        # A retarget leaves no belief of its own to point at directly --
        # what it changed is WHICH monster `attack(hero, ...)` names, read
        # off the wary/eyeing trail instead.
        eyed = [p for p in m2.pad.believed() if m2.g.relation_of(p) is kb2.atom("eyeing")]
        if did_flee:
            fled += 1
        elif eyed:
            retargeted += 1
        print(f"seed={seed:3d}  {'same' if same else 'DIVERGED':8s}  "
              f"fled={str(did_flee):5s}  eyeing={len(eyed)}  "
              f"control={r1:20s} gut={r2}")
    print(f"\n{diverged}/30 fights the outcome diverged from the plain "
          f"microprogram port")
    print(f"{fled}/30 fights hero fled outright; {retargeted}/30 more "
          f"noticed a threat without fleeing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

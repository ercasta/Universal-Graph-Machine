"""The dungeon, step 2: the SAME fight as `ugm.probes.dungeon`, run against
`ugm/rules/dungeon_micro.ugm` -- the microprogram-shaped port -- and
compared outcome for outcome across the same seeds.

    python -m ugm.probes.dungeon_micro

`calc` and `beats` are COMPUTATORS here, not tools -- only `<dice>` is
registered as an answerer, which is the whole of what the port changed
about the tool seam. See `dungeon_micro.ugm`'s own header for what else
changed and why.
"""

import random
from typing import List, Optional

from .. import corpora as _corpora
from ..core.machine import Machine
from ..core.text import load, load_file
from . import dungeon as control

CORPUS = _corpora.path("dungeon_micro.ugm")


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

    kb = load_file(m, CORPUS, scope="dungeon")
    steps = m.run(limit=limit)
    return m, kb, asked, steps


def main() -> int:
    mismatches = 0
    for seed in range(1, 15):
        m1, kb1, _asked1, steps1 = control.fight(seed=seed, limit=4000)
        m2, kb2, _asked2, steps2 = fight(seed=seed, limit=4000)
        over1 = [p for p in m1.pad.believed() if m1.g.relation_of(p) is kb1.atom("over")]
        over2 = [p for p in m2.pad.believed() if m2.g.relation_of(p) is kb2.atom("over")]
        r1 = m1.g.show(over1[0]) if over1 else "UNRESOLVED"
        r2 = m2.g.show(over2[0]) if over2 else "UNRESOLVED"
        wasted2 = sum(1 for s in steps2 if s.applied is not None and not s.wrote)
        same = r1 == r2
        if not same:
            mismatches += 1
        print(f"seed={seed:3d}  control={r1:20s} micro={r2:20s}  "
              f"{'OK' if same else 'MISMATCH'}  "
              f"micro: quiescent={steps2[-1].state == 'quiescent'} "
              f"wasted={wasted2}")
    print(f"\n{mismatches} mismatch(es) across 14 seeds")
    return 0 if mismatches == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

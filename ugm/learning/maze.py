"""How far does a lesson transfer? A number per region -- and the theory

    python -m ugm.learning.maze

predicts the VARIANCE, not the mean. ugm.lifting shows that a lesson
generalises: contains(_, :solid) covers k5, which holds pebbles and was never
heated. ⚠ The regions are authored (in_region), not derived from the doors.

See docs/design/maze.md.
"""

import re
from typing import Dict, List

from ..core.machine import Machine
from .surprise import common, features, learn
from ..core.text import load

# Four heated kettles: two boil, two do not. This is `ugm.lifting`'s corpus and
# deliberately unchanged -- the lesson under test has to be the lesson that
# instrument already measured, or this is grading a different learner.
TRAINING = """
fact +heating(k1)
fact +contains(k1, water)
fact +heating(k2)
fact +contains(k2, sand)
fact +heating(k3)
fact +contains(k3, gravel)
fact +heating(k4)
fact +contains(k4, milk)

rule <boils> = causes( { +heating($k) }, { +boiling($k) } )
rule <trust> = implies( { +says(world, $p, minus) }, { -$p } )

say world: -boiling(k2)
say world: -boiling(k3)
"""

# The maze. Doors are here so a region is a place rather than a label, and
# nothing reads them -- see the note above.
MAZE = """
fact +door(home, north)
fact +door(home, south)
fact +door(south, east)

fact +in_region(n1, north)
fact +in_region(n2, north)
fact +in_region(n3, north)
fact +in_region(n4, north)
fact +contains(n1, pebbles)
fact +contains(n2, grit)
fact +contains(n3, ash)
fact +contains(n4, slag)

fact +in_region(s1, south)
fact +in_region(s2, south)
fact +in_region(s3, south)
fact +in_region(s4, south)
fact +contains(s1, juice)
fact +contains(s2, oil)
fact +contains(s3, brine)
fact +contains(s4, syrup)

fact +in_region(e1, east)
fact +in_region(e2, east)
fact +in_region(e3, east)
fact +in_region(e4, east)
fact +contains(e1, chalk)
fact +contains(e2, tar)
fact +contains(e3, flint)
fact +contains(e4, resin)
"""

# `stuff` is the kind everything has, and it is what an over-general learner
# would reach for. The real learner refuses it for the reason `ugm.lifting`
# already checks -- it holds of the successes too -- so it is present here to be
# the baseline that scores BEST on the mean.
ONTOLOGY = """
fact +is_a(water, liquid)
fact +is_a(milk, liquid)
fact +is_a(sand, solid)
fact +is_a(gravel, solid)

fact +is_a(pebbles, solid)
fact +is_a(grit, solid)
fact +is_a(ash, solid)
fact +is_a(slag, solid)
fact +is_a(juice, liquid)
fact +is_a(oil, liquid)
fact +is_a(brine, liquid)
fact +is_a(syrup, liquid)
fact +is_a(chalk, solid)
fact +is_a(tar, liquid)
fact +is_a(flint, solid)
fact +is_a(resin, liquid)

fact +is_a(water, stuff)
fact +is_a(milk, stuff)
fact +is_a(sand, stuff)
fact +is_a(gravel, stuff)
fact +is_a(pebbles, stuff)
fact +is_a(grit, stuff)
fact +is_a(ash, stuff)
fact +is_a(slag, stuff)
fact +is_a(juice, stuff)
fact +is_a(oil, stuff)
fact +is_a(brine, stuff)
fact +is_a(syrup, stuff)
fact +is_a(chalk, stuff)
fact +is_a(tar, stuff)
fact +is_a(flint, stuff)
fact +is_a(resin, stuff)
"""

# One claim removed, exactly as `ugm.lifting` does it: gravel stops being known
# as a solid, and nothing else changes.
MAIMED = ONTOLOGY.replace("fact +is_a(gravel, solid)\n", "")

CASES = [f"{p}{i}" for p in "nse" for i in range(1, 5)]
OVER_GENERAL = "contains(_, :stuff)"


def _mean(xs: List[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _variance(xs: List[float]) -> float:
    """Population variance. The point is whether it is ZERO, so which convention
    is used changes nothing that is read."""
    if not xs:
        return 0.0
    mu = _mean(xs)
    return sum((x - mu) ** 2 for x in xs) / len(xs)


def _coverage(m: Machine, kb, lesson: str) -> Dict[str, float]:
    """For each region, the fraction of its cases the lesson covers.

    A case's region is read out of `features` -- the same function that produced
    the lesson and that `ugm.lifting` uses for its held-out test. A second way of
    asking would degrade separately and agree with the first while both were
    wrong.
    """
    hits: Dict[str, List[float]] = {}
    for name in CASES:
        fs = features(m, kb, kb.term(name), lift=True)
        region = next((f.split(", ")[1].rstrip(")")
                       for f in fs if f.startswith("in_region(_, ")), None)
        if region is None:
            continue
        hits.setdefault(region, []).append(1.0 if lesson in fs else 0.0)
    return {r: _mean(v) for r, v in hits.items()}


def _run(src: str, lift: bool):
    m = Machine()
    kb = load(m, src, None, None)
    m.run(limit=800)
    found = learn(m, kb, lift=lift)
    return m, kb, found, common(found)


def _held_out() -> List[str]:
    """Terms the held-out regions contain that ALSO occur in training. Must be
    empty, or the memoriser is being graded on cases it has seen."""
    # ⚠ Word boundaries, not `in`. The first version asked `term in TRAINING`
    # and reported `oil` as shared -- because it is a substring of `boiling`.
    # A held-out check that fires on a false sharing is exactly as useless as
    # one that misses a real one, and this is the half that fails loudly.
    words = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", TRAINING))
    return sorted({line.split(",")[1].strip().rstrip(")")
                   for line in MAZE.splitlines()
                   if line.startswith("fact +contains(")} & words)


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

    src = TRAINING + MAZE + ONTOLOGY
    _, _, raw, raw_lesson = _run(src, lift=False)
    m, kb, lifted, lesson = _run(src, lift=True)
    _, _, maimed, maimed_lesson = _run(TRAINING + MAZE + MAIMED, lift=True)

    cover = _coverage(m, kb, lesson[0]) if lesson else {}
    over = _coverage(m, kb, OVER_GENERAL)
    regions = sorted(cover) or sorted(over)

    print("  coverage per region, held-out cases only:\n")
    print(f"    {'learner':22}" + "".join(f"{r:>9}" for r in regions)
          + f"{'mean':>9}{'variance':>10}")
    rows = [
        ("memoriser (no lift)", {r: 0.0 for r in regions} if not raw_lesson
         else _coverage(m, kb, raw_lesson[0])),
        ("lifted", cover),
        ("over-general", over),
    ]
    stats = {}
    for label, c in rows:
        vals = [c.get(r, 0.0) for r in regions]
        stats[label] = (_mean(vals), _variance(vals))
        print(f"    {label:22}" + "".join(f"{c.get(r, 0.0):9.2f}" for r in regions)
              + f"{_mean(vals):9.2f}{_variance(vals):10.4f}")
    print()

    gate("TERMS ARE HELD OUT, NOT ONLY RELATIONS: nothing the regions contain "
         "occurs in the training corpus, so recognising a training term in a "
         f"new room cannot score as transfer ({_held_out() or 'none shared'})",
         _held_out() == [])

    gate("the memoriser has NOTHING to transfer: two failures, two answers, "
         "nothing in common -- so the question *how far does it reach* has no "
         "subject",
         len(raw) == 2 and raw_lesson == [])

    gate(f"the lifted learner has one lesson, and it is about a kind ({lesson})",
         lesson == ["contains(_, :solid)"])

    gate("...which covers the solid region entirely, the liquid region not at "
         f"all, and the mixed one half ({ {r: round(cover.get(r, 0.0), 2) for r in regions} })",
         cover.get("north") == 1.0 and cover.get("south") == 0.0
         and cover.get("east") == 0.5)

    m_mem, v_mem = stats["memoriser (no lift)"]
    m_lift, v_lift = stats["lifted"]
    m_over, v_over = stats["over-general"]

    gate("THE MEAN RANKS THE WORST LEARNER FIRST: the over-general lesson "
         f"covers every case in every region ({m_over:.2f}) and beats the lesson "
         f"that is right ({m_lift:.2f})",
         m_over > m_lift > m_mem)

    gate("THE VARIANCE SEPARATES THEM, AND IT IS THE ONLY ONE THAT DOES: both "
         f"failures are FLAT -- transfers nothing everywhere ({v_mem:.4f}), "
         f"transfers everything everywhere ({v_over:.4f}) -- and only a lesson "
         f"about a kind discriminates between regions ({v_lift:.4f})",
         v_mem == 0.0 and v_over == 0.0 and v_lift > 0.0)

    maimed_cover = _coverage(m, kb, maimed_lesson[0]) if maimed_lesson else {}
    maimed_var = _variance([maimed_cover.get(r, 0.0) for r in regions])
    gate("KILL-PROBE: THE WORLD MODEL IS DOING THE WORK. Delete one `is_a` fact "
         "-- gravel stops being known as a solid -- and there is no lesson, so "
         f"the variance collapses to zero with nothing else changed "
         f"({maimed_lesson}, variance {maimed_var:.4f})",
         maimed_lesson == [] and len(maimed) == 2 and maimed_var == 0.0)

    print(f"\n{ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())

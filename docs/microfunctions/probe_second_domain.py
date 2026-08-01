"""PROBE — does the `wants` binding trick survive a SECOND domain?

Everything in `expert_judgement.md` was measured on blocks world: three operators, and goals that are
`a on b` — a **link** constraint naming a subject and an object, which happen to be exactly the
individuals that must move. The design's load-bearing assumption is:

> **A criterion's variables come from an unmet goal constraint.**

Two domains already in `selftest.py` attack that from different sides:

* **the GARAGE** — goal `car is a washed_car`, a **type** constraint: one subject, **no object**. Any
  knowledge relating two individuals should be inexpressible here. Ordering knowledge (service before
  wash) needs only the subject, so it should survive; the question is what else does not.
* **the WAREHOUSE** — goal `wh contains+ parcel`, plus `never touch wh`. The right action puts the parcel
  in the **box**, which the goal never names. So the criterion must reach a **third individual** that
  `wants` cannot bind — the sharpest test of the assumption available.
"""
from __future__ import annotations
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from microfunctions import criterion as CR, driver as D, intake as I, path as P, thread as T
from microfunctions.selftest import _garage, _warehouse


def _lines(*ls):
    return "\n".join(ls)


def report(name, g, goal, world, texts, *, plain_first=True, max_steps=200, max_depth=6):
    for t in texts:
        I.read(g, t)
    got = D.pursue(g, goal, T.open_thread(g), world, max_steps=max_steps, max_depth=max_depth,
                   propose=CR.decide(g, goal, world))
    print(f"  {name:34} found={got['found']} imagined={got.get('steps'):>3} "
          f"plan={D.plan_steps(g, got) if got['found'] else ()}")
    return got


# --- DOMAIN 1: the garage. A TYPE goal — subject only, no object ---------------------------------------
def garage():
    print("\n=== GARAGE — goal is a TYPE constraint (subject, no object) ===")
    g, car = _garage()
    g.put(car, label="car")
    goal = I.read_goal(g, _lines("goal clean it:", "    car is a washed_car"))

    plain = D.pursue(g, goal, T.open_thread(g), car, max_steps=200, max_depth=6)
    print(f"  {'relevance only':34} found={plain['found']} imagined={plain.get('steps'):>3} "
          f"plan={D.plan_steps(g, plain) if plain['found'] else ()}")

    return report("with criteria", g, goal, car, [
        _lines("criterion service it before washing:",
               "    wants type washed_car",
               "    unless subject is a serviced_car",
               "    do service c = subject",
               "    because wash only applies to a car that has been serviced"),
        _lines("criterion then wash it:",
               "    wants type washed_car",
               "    when subject is a serviced_car",
               "    do wash c = subject"),
    ])


# --- DOMAIN 2: the warehouse. The right action names a THIRD individual --------------------------------
def warehouse(text, label):
    g, world, wh, box, parcel = _warehouse(nested=False)
    goal = I.read_goal(g, _lines("goal stow it:", "    wh contains+ parcel", "    never touch wh"))
    got = report(label, g, goal, world, [text])
    if got["found"]:
        # ⚠ `pursue` only PLANS. The first version of this probe read the real world straight after it and
        # reported the parcel as not in the warehouse — of course it was not, nothing had been done. The
        # plan has to be carried out before reality can be asked anything.
        from microfunctions import execution as X
        X.execute(g, got["workbench"], got["frame"])
        print(f"     {'carried out ->':>32} in the warehouse: {P.reaches(g, wh, 'contains', parcel)}, "
              f"and NOT directly: {parcel not in g.targets(wh, 'contains')}, "
              f"via the box: {parcel in g.targets(box, 'contains')}")
    return got


if __name__ == "__main__":
    garage()

    print("\n=== WAREHOUSE — the action names a THIRD individual the goal never mentions ===")
    g0, world0, wh0, box0, parcel0 = _warehouse(nested=False)
    goal0 = I.read_goal(g0, _lines("goal stow it:", "    wh contains+ parcel", "    never touch wh"))
    plain = D.pursue(g0, goal0, T.open_thread(g0), world0, max_steps=200, max_depth=6)
    print(f"  {'relevance only':34} found={plain['found']} imagined={plain.get('steps'):>3} "
          f"plan={D.plan_steps(g0, plain) if plain['found'] else ()}")

    # ⚠ THE NAIVE CRITERION, and it should be REFUSED: `box = subject` is the warehouse itself, which
    # `never touch wh` forbids. A criterion may not launder a guess into overruling a plan constraint.
    print("\n  -- naive: put it straight in the warehouse --")
    try:
        warehouse(_lines("criterion stow it directly:",
                         "    wants link contains",
                         "    do put_in t = object, box = subject"), "box = subject")
    except D.Undecidable as e:
        print(f"  >> REFUSED (correctly): {e}")

    # ⭐ Reaching the third individual by a PATH from the subject.
    print("\n  -- reaching the box by a path from the subject --")
    warehouse(_lines("criterion stow it in something already inside:",
                     "    wants link contains",
                     "    do put_in t = object, box = subject.contains",
                     "    because a thing inside the warehouse is inside it at any depth"),
              "box = subject.contains")

    # ⚠⚠ TWO containers, and only one is allowed. `subject.contains` denotes the FIRST — the criterion
    # can REACH a third individual but cannot CHOOSE among several, and there is no form for saying which.
    print("\n  -- TWO containers, the first one forbidden --")
    g, world, wh, box, parcel = _warehouse(nested=False)
    crate = g.mint("thing", kind_of="thing", label="crate", held=True)
    g.link(world, "thing", crate)
    g.link_at(wh, "contains", 0, crate)                     # ahead of the box, so `.contains` finds it
    goal = I.read_goal(g, _lines("goal stow it:", "    wh contains+ parcel",
                                 "    never touch wh", "    never touch crate"))
    I.read(g, _lines("criterion stow it in something already inside:",
                     "    wants link contains",
                     "    do put_in t = object, box = subject.contains"))
    try:
        got = D.pursue(g, goal, T.open_thread(g), world, max_steps=200, max_depth=6,
                       propose=CR.decide(g, goal, world))
        print(f"  {'box = subject.contains':34} found={got['found']} "
              f"plan={D.plan_steps(g, got) if got['found'] else ()}")
    except D.Undecidable as e:
        print(f"  >> THE RESIDUE: {e}")
        print("     `subject.contains` denotes the FIRST container. The criterion can REACH a third")
        print("     individual but cannot SELECT among several — no `some x such that …` form exists.")
        print("     `nearest/furthest … by <link>` selects over a TRAVERSAL, never by a CONDITION.")

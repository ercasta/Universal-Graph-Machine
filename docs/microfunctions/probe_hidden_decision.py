"""PROBE — what is deciding this search? Ask the graph.

`islands.md` G says `criterion.decide` is a Python loop *"invisible to the agenda because it is a
`propose=` hook parameter — the same hidden Python channel `plural_step.md` invoked to reject a `view=`
argument."* Two complaints are folded together there, and they are not equally tractable:

  (a) it is a Python control loop;
  (b) it arrives through a **hook parameter**, so it is not part of the search's state.

This probes **(b)**, because `search.open_search`'s own docstring already concedes it —
*"Everything a step needs **that is not a Python callable** lives HERE"* — and because (b) has a
consequence (a) does not: **the outer loop could not resume a guided search.** `loop.advance` forwards
`**hooks` from whoever called `tick`, so guidance was a property of the CALLER, not of the search.

⚠⚠ **The control is the whole probe.** Guided and unguided must differ **measurably**, or both "the loop
lost the guidance" and "the loop got it back" are unfalsifiable. Measured before the fix: **3** imagined
states via `pursue(propose=…)`, **52** for the identical search node ticked by the outer loop.

⚠ A first attempt rolled its own blocks world and produced `found=False` with 4 imagined states either
way — it would have reported CONTROL DARK for a world that simply did not work. It uses the fixture the
suite already pins at (3, 52) instead.
"""
from __future__ import annotations
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from microfunctions import criterion as CR, driver as D, intake, loop as L, thread as T
from microfunctions.selftest import CRITERIA_TEXT, _blocks, _sussman


def build():
    """The fixture `check_EXPERT_JUDGEMENT_can_be_AUTHORED_AS_TEXT` uses: Sussman's anomaly, three
    authored criteria."""
    g, world = _blocks()
    goal, _abc = _sussman(g, world)
    for t in CRITERIA_TEXT:
        intake.read(g, t)
    return g, world, goal


def run_on_loop(g, search):
    lp = L.open_loop(g)
    L.schedule(g, lp, search, why="plan it")
    L.run(g, lp, max_ticks=2000)
    return g.attr(search, "steps")


print("=" * 78)
print("  1. GUIDED — the criteria reach the search through a Python keyword argument")
print("=" * 78)
g1, w1, goal1 = build()
got1 = D.pursue(g1, goal1, T.open_thread(g1), w1, max_steps=400, max_depth=7,
                propose=CR.decide(g1, goal1, w1))
print(f"  found={got1['found']}  imagined={got1['steps']}")

print()
print("=" * 78)
print("  2. THE SAME SEARCH, ticked by the OUTER LOOP, guidance taken FROM THE GRAPH")
print("=" * 78)
g2, w2, goal2 = build()
s2 = D.open_planning(g2, goal2, T.open_thread(g2), w2, max_steps=400, max_depth=7,
                     decider=CR.decider(g2, goal2, w2))
looped = run_on_loop(g2, s2)
print(f"  found={g2.attr(s2, 'found')}  imagined={looped}")

# WARN THE VACUITY GUARD. Asserting 3 == 3 would pass for an engine that always answered 3, so the
# control is the SAME search with NO decider on it: it must fall back to enumeration and cost far more.
g3, w3, goal3 = build()
s3 = D.open_planning(g3, goal3, T.open_thread(g3), w3, max_steps=400, max_depth=7)
plain = run_on_loop(g3, s3)

print()
print(f"  {'++ FIXED      ' if looped == got1['steps'] else '!! STILL LOST '}loop-ticked {looped} vs "
      f"pursue-guided {got1['steps']} — the outer loop reproduces the guided search")
print(f"  {'++ CONTROL    ' if plain > looped else '!! CONTROL DARK '}same search with NO decider: "
      f"{plain} imagined — so the match above is guidance, not a constant")

print()
print("=" * 78)
print("  3. What is deciding it, asked of the graph")
print("=" * 78)
dec = g2.target(s2, "decided_by")
for lbl in ("goal", "workbench", "thread", "subject"):
    print(f"  ++ the search says its {lbl:10}-> {g2.target(s2, lbl) is not None}")
print(f"  ++ ...and WHAT IS DECIDING IT     -> {dec}, how={g2.attr(dec, 'how')!r}")
print(f"  ++ naming the goal and subject it decides for -> "
      f"{g2.target(dec, 'goal') is not None and g2.target(dec, 'subject') is not None}")
print(f"  ++ everything the search points at-> {', '.join(g2.labels(s2))}")

print()
print("  >> Before this slice `decided_by` was absent and case 2 cost 52 imagined states: guidance was a")
print("     property of the PYTHON CALLER, not of the search. That is `islands.md` G's complaint (b).")
print("  >> STILL OPEN — complaint (a): `criterion.decide` is still a Python loop over the criteria. It is")
print("     reachable from the graph now instead of handed in as a closure, which is what made the search")
print("     resumable; it is not yet data. See `kernel_boundary.md` §5.")

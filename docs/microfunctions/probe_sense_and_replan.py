"""PROBE — can a pursuit ACT on an unfinished plan, and then replan?

The user's specification, 2026-08-02:

> Sometimes, to solve a goal, you genuinely need to perform an action. That only means the planning
> procedure can propose, as the next candidate step for the outer loop, not more planning but **executing
> an action** — and this is possible now that we have an outer loop. ⚠ *"we won't resume searching for
> the plan, because the information we acquired might require replanning altogether."*

The gap: a search reports `found=False` for two very different reasons, and `_phase_planning` read both
as defeat — so *"I cannot plan this until I go and look"* settled the pursuit.

⚠⚠ The world here is built so the planner is **structurally blind**: `scan_dir`'s whole effect is on the
far side of a `DISPATCH` and it has **no mock**, so `establishes` reads nothing and means-ends can never
select it. That is what makes sensing a distinct capability rather than a shortcut for planning.
"""
from __future__ import annotations
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from microfunctions import asm, dispatch as DP, driver as D, goal as G, loop as L, thread as T
from microfunctions.graph import UNKNOWN, new_graph
from microfunctions.types import declare_type

REAL_FILES = 3


def look(g, target):
    for i in range(REAL_FILES):
        f = g.mint("chunk", kind_of="file", label=f"f{i}")
        g.link(target, "file", f)
    g.put(target, count=REAL_FILES)
    return REAL_FILES


DP.register("probe_look", look, observes=True)


def world():
    g = new_graph()
    declare_type(g, "folder", attrs={"kind_of": "folder"})
    declare_type(g, "file", attrs={"kind_of": "file"})
    asm.load_text(g, "\n".join((
        "# Its whole effect is behind a DISPATCH and it has NO mock, so `establishes` reads nothing",
        "# and the planner can never select it. Only sensing can.",
        "fn scan_dir(d: folder) -> folder:",
        '    DISPATCH R(out) "probe_look" F(d)',
    )))
    folder = g.mint("chunk", kind_of="folder", label="src", count=UNKNOWN)
    g.link("root", "has", folder)
    goal = G.open_goal(g, label="know how many files")
    G.require_attr(g, goal, folder, "count", REAL_FILES)
    return g, folder, goal


print("=" * 78)
print("  the planner is blind: what does it see?")
print("=" * 78)
g, folder, goal = world()
eff, unk = D.establishes(g, "scan_dir")
print(f"  scan_dir establishes {set(eff)} unknown={set(unk)}  <- nothing to select on")
print(f"  goal bottoms out in ignorance: {G.blocked_on_ignorance(g, goal)}")

print()
print("=" * 78)
print("  RUN IT on the outer loop")
print("=" * 78)
p = D.open_pursuit(g, goal, T.open_thread(g), folder)
lp = L.open_loop(g)
L.schedule(g, lp, p, why="pursue it")
out = L.run(g, lp, max_ticks=200)
verbs = [r["verb"] for r in out["did"]]
print(f"  ticks={out['ticks']}  verbs={verbs}")
print(f"  sensed with: {g.attr(p, 'sensed')}")
print(f"  folder.count is now {g.attr(folder, 'count')!r}")
print(f"  GOAL SATISFIED: {G.satisfied(g, goal, under=folder)}")

print()
print("=" * 78)
print("  CONTROLS")
print("=" * 78)
# 1. Without sensing the pursuit must fail — otherwise the scenario proves nothing.
g2, folder2, goal2 = world()
s2 = D.open_planning(g2, goal2, T.open_thread(g2), folder2, max_steps=200, max_depth=6)
lp2 = L.open_loop(g2)
L.schedule(g2, lp2, s2, why="plan only")
L.run(g2, lp2, max_ticks=200)
print(f"  ++ CONTROL   planning ALONE: found={g2.attr(s2, 'found')} — so the plan really was unreachable")

# 2. The old search must be DISCARDED, not resumed.
print(f"  ++ CONTROL   searches opened during the pursuit: "
      f"{len([n for n in g.nodes if g.kind(n) == 'search'])} (a fresh one after sensing, not a resume)")

# 3. A goal NOT blocked on ignorance must not sense at all.
g3 = new_graph()
declare_type(g3, "folder", attrs={"kind_of": "folder"})
f3 = g3.mint("chunk", kind_of="folder", label="src", count=1)
g3.link("root", "has", f3)
goal3 = G.open_goal(g3, label="already true")
G.require_attr(g3, goal3, f3, "count", 1)
p3 = D.open_pursuit(g3, goal3, T.open_thread(g3), f3)
lp3 = L.open_loop(g3)
L.schedule(g3, lp3, p3, why="pursue")
L.run(g3, lp3, max_ticks=100)
print(f"  ++ CONTROL   a goal NOT blocked on ignorance sensed: {g3.attr(p3, 'sensed')} (must be None)")

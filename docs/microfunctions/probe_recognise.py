"""PROBE — can a recognised rule be EXECUTED by the outer loop, with no second Python channel?

The proposal (the user's, 2026-08-02): make *"decide what to do next"* an ISA **primitive** —
`NATIVE R(c) "recognise" …`. Recognition is opaque and atomic, and **deliberately hands back no `why`**:
System 1 does not explain itself, and an explanation *recorded* at decision time would be privileged over
one *re-derived* later by `governing`, which is two sources of truth about the same act. Once a rule is
identified, applying it is ordinary interruptible work on the ordinary agenda.

⭐ The motivating capability is NOT speed. Guidance is already measured at 3-vs-52 imagined states and
6.6x at sixty blocks, and those wins exist today through `propose=`. What does *not* exist is acting on
recognition **without opening a search at all** — nothing in the engine consults a criterion outside the
planner. That is what "System 1" names.

**So the one question that makes or breaks the shape:**

> Given a rule that has spoken, is there a NODE form of what to do, and can something on the agenda run it
> — or does executing it require a Python object handed through a side channel?

Three things are measured, in order of how badly each would hurt:

  (1) can recognition even happen without imagining? (`speaks` takes a `frame`)
  (2) is the thing it returns a node, or a Python value?
  (3) is there a task kind the outer loop can advance to carry it out?
"""
from __future__ import annotations
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from microfunctions import (consequent as CQ, criterion as CR, driver as D, execution as X,
                            intake as I, loop as L, thread as T, workbench as W)
from microfunctions.selftest import CRITERIA_TEXT, _blocks, _sussman


def verdict(tag, detail=""):
    print(f"  >> {tag:14} {detail}")


def control(ok, detail=""):
    print(f"  {'++ CONTROL     ' if ok else '!! CONTROL DARK'} {detail}")


g, world = _blocks()
goal, _abc = _sussman(g, world)
for t in CRITERIA_TEXT:
    I.read(g, t)
c = CR.criteria(g)[0]

print("=" * 78)
print("  1. Can a rule be recognised WITHOUT imagining?")
print("=" * 78)
# ⚠ `speaks(g, c, goal, frame, subject)` — the `frame` is not optional. Passing "root" in its place does
# NOT raise; it runs and comes back SILENT, which is the more dangerous answer.
call, blocked = CR.speaks(g, c, goal, "root", world)
verdict("SILENT", f"against the REAL graph: call={call} blocked={blocked}")

wb = W.open_workbench(g, world, label="recognising")
frame = W.root_frame(g, wb)
call, blocked = CR.speaks(g, c, goal, frame, world)
control(call is not None,
        f"the SAME rule against a workbench frame: {call.function if call else None} "
        f"— so the rule is fine and case 1 is about the frame, not the rule")

# ⭐⭐ And it is not this criterion's navigation. The SIMPLEST possible rule — one role, no walking —
# fails the same way, and the message names the cause.
g2, world2 = _blocks()
goal2, _ = _sussman(g2, world2)
I.read(g2, "\n".join(("criterion simplest:",
                      "    wants attr height",
                      "    do unstack b = subject, floor = the ground")))
c2 = CR.criteria(g2)[0]
flat, why = CR.speaks(g2, c2, goal2, "root", world2)
verdict("SAME CAUSE", f"a rule with NO navigation, against reality: "
                      f"{'SPOKE' if flat else 'SILENT'} | {why}")
real_ok = flat is not None

print()
print("=" * 78)
print("  2. Is what it hands back a NODE, or a Python value?")
print("=" * 78)
verdict("PYTHON", f"type={type(call).__name__}  fields={getattr(call, '_fields', None)}")
verdict("PYTHON", f"bindings are {type(call.bindings).__name__} of "
                  f"{ {k: type(v).__name__ for k, v in call.bindings.items()} }")
cq = CQ.of(g, c)[0]
verdict("NODE", f"the rule's CONSEQUENT is a node: {cq} kind={CQ.kind(g, cq)} "
                f"-> {CQ.describe(g, cq)}")
verdict("BUT", f"...and it is GENERIC: its bindings are unresolved text {CQ.bindings_of(g, cq)}")

print()
print("=" * 78)
print("  3. Is there a task the outer loop can advance to CARRY IT OUT?")
print("=" * 78)
kinds = []
for k in ("activation", "search", "replay", "forgetting", "pursuit"):
    kinds.append(k)
verdict("AGENDA KINDS", ", ".join(kinds))
lp = L.open_loop(g)
try:
    L.schedule(g, lp, cq, why="do what was recognised")
    L.run(g, lp, max_ticks=5)
    verdict("RUNS", "the loop advanced a consequent node directly")
except Exception as e:
    verdict("NO TASK", f"{type(e).__name__}: {e}")

# What DOES carry out a call today: a replay over frames, which needs a workbench and a path.
import inspect                                                                    # noqa: E402
sig = inspect.signature(X.open_replay)
verdict("TODAY", f"the only executor of a real call is `execution.open_replay{sig}` — "
                 f"it replays FRAMES, so it needs a workbench and a planned path")

print()
print("=" * 78)
print("  WHAT THIS MEANS FOR THE SHAPE")
print("=" * 78)
print("  >> (1) ⚠⚠ RECOGNITION CANNOT MATCH AGAINST REALITY, AND FAILS SILENTLY. `driver.check_call`")
print("     requires every binding to be a MAPPING IN A FRAME, so outside a workbench every rule is")
print("     refused with *'not in the world being imagined here'* — even one with no navigation at all.")
print("     'Act without planning' is blocked before the loop question is reached.")
print("  >> ⭐⭐ AND THIS IS ISLANDS.MD ITEM J, FROM THE OTHER SIDE — the same `check_call` line, the")
print("     same silence. A real node outside the imagined world cannot be bound; reality IS outside the")
print("     imagined world. One fix unblocks both.")
print("  >> (2) The bound call is a PYTHON NamedTuple. The rule's consequent IS a node, but a GENERIC")
print("     one — unresolved text bindings. Neither is 'a bound action, as data'.")
print("  >> (3) No agenda kind carries out a call; `replay` executes a PATH OF FRAMES, not an action.")

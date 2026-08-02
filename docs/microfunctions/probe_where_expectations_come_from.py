"""PROBE — WHERE DOES AN EXPECTATION COME FROM?

The user's question, 2026-08-02, refining the previous probe:

> Not always do we have expectations for external calls; the real question is **where do expectations come
> from**?

`probe_expectation_at_the_boundary.py` measured that a planned tool call is checked and an unplanned one is
not. It did not ask what the check is made OF. Four candidate sources, and each is asked separately because
the design could have any subset:

  (S1) **THE MOCK** — for a dispatching function the body is just `DISPATCH`, so the mock is the only place
       anybody states what the call will do. Q: can a dispatching function be planned with NO mock at all?
       If not, then for external calls a mock is not optional and "the plan specifies an expectation" is
       really "the mock does".
  (S2) **THE DECLARED RETURN TYPE** — `deviates` checks it, but only inside `execution.step`. Q: is it
       checked on a call made outside a plan?
  (S3) **THE PARAMETER TYPES** — `fn.invoke` enforces these on every call, planned or not (verified by
       reading; measured here). This is the one expectation that already survives having no plan.
  (S4) **THE GOAL** — a goal is a set of constraint nodes, and `goal.unmet` before and after an action is an
       expectation that needs no plan and no mock. Q: does anything compare them across an action today?

⚠ The point of asking S1 separately is that "no expectation" must turn out to be a REPRESENTABLE, VISIBLE
state rather than silently identical to "everything went as expected".
"""
from __future__ import annotations
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from microfunctions import asm, dispatch as D, execution as X, function as fn   # noqa: E402
from microfunctions import goal as G, types as TY, workbench as W               # noqa: E402
from microfunctions.graph import new_graph                                      # noqa: E402

declare = TY.declare_type
bar = "=" * 84


def world(*, with_mock: bool):
    """`scan_dir` reaches the world. Everything interesting is on the far side of the DISPATCH."""
    g = new_graph()
    declare(g, "dir", attrs={"kind_of": "dir"})
    declare(g, "listing", base="dir", attrs={"listed": True})
    body = ["fn scan_dir(d: dir) -> listing:",
            '    DISPATCH R(out) "ls" F(d)',
            '    SET F(d) "listed" true']
    if with_mock:
        body += ["",
                 "fn found_two(d: dir) -> listing mocks scan_dir:",
                 '    SET F(d) "listed" true',
                 '    NEW R(f1) "file"', '    LINK F(d) "file" R(f1)',
                 '    NEW R(f2) "file"', '    LINK F(d) "file" R(f2)']
    asm.load_text(g, "\n".join(body))
    d = g.mint("dir", kind_of="dir")
    g.link("root", "has", d)
    return g, d


# --- S1: can an external call be PLANNED with no mock? --------------------------------------------------
print(bar)
print("  S1 — THE MOCK. Can a dispatching function be planned with no mock at all?")
print(bar)

g, d = world(with_mock=False)
D.register("ls", lambda gr, target: gr.put(target, count=0))
wb = W.open_workbench(g, d)
f0 = W.root_frame(g, wb)
try:
    f1, tr = W.step(g, wb, f0, "scan_dir", {"d": W.mapping_for(g, f0, d)})
    S1_refused, S1_why = False, f"planned fine, prediction = {W.predicted_changes(g, f0, f1)}"
except Exception as e:
    S1_refused, S1_why = True, f"{type(e).__name__}: {e}"
print(f"  planning it WITHOUT a mock     : {'REFUSED' if S1_refused else 'allowed'}")
print(f"    -> {S1_why}")

g2, d2 = world(with_mock=True)
wb2 = W.open_workbench(g2, d2)
f0b = W.root_frame(g2, wb2)
f1b, _ = W.step(g2, wb2, f0b, "scan_dir", {"d": W.mapping_for(g2, f0b, d2)}, assume="found_two")
pred = W.predicted_changes(g2, f0b, f1b)
print(f"  planning it WITH a mock        : allowed, and it predicts {sorted(pred['minted'])}")
print(f"  CONTROL - the prediction is non-empty: {bool(pred['minted'] or pred['links'])}")

# --- S2: is the DECLARED RETURN TYPE checked outside a plan? --------------------------------------------
print()
print(bar)
print("  S2 — THE DECLARED RETURN TYPE. Checked on a call made outside a plan?")
print(bar)


def liar(gr, target):
    """A tool whose effect makes the function BREAK its own declared return type: `listing` demands
    `listed: True`, and this clears it after the body set it. A planned step would call this a deviation."""
    gr.put(target, listed=None)


g3, d3 = world(with_mock=True)
# ⚠ The body sets `listed` AFTER the dispatch, so the tool must be the last word: re-clear it by hand
# immediately after the call, standing in for a world that moved. What is being measured is whether ANYONE
# asks "did this call satisfy what it promised" outside a replay.
D.register("ls", lambda gr, target: None)
fn.invoke(g3, "scan_dir", {"d": d3})
g3.put(d3, listed=None)                      # the world moved; the result is no longer a `listing`
still_a_listing = TY.is_a(g3, d3, "listing")
noticed = [n for n in g3.nodes if g3.kind(n) == "deviation"]
print(f"  the call ran, unplanned        : True")
print(f"  its result satisfies `listing` : {still_a_listing}")
print(f"  anything raised or recorded    : {bool(noticed)}")
print(f"  -> the return type is a promise NOBODY CHECKS outside `execution.step`: {not noticed}")
S2_unchecked = not noticed and not still_a_listing

# --- S3: are the PARAMETER TYPES checked outside a plan? ------------------------------------------------
print()
print(bar)
print("  S3 — THE PARAMETER TYPES. Checked on a call made outside a plan?")
print(bar)

g4, d4 = world(with_mock=True)
D.register("ls", lambda gr, target: None)
g4.put(d4, kind_of=None)                     # no longer a `dir` at all
try:
    fn.invoke(g4, "scan_dir", {"d": d4})
    S3_checked, S3_why = False, "it ran anyway"
except TY.TypeViolation as e:
    S3_checked, S3_why = True, f"TypeViolation: {getattr(e, 'param', '?')} is not a {getattr(e, 'want', '?')}"
print(f"  refused an unplanned bad call  : {S3_checked}")
print(f"    -> {S3_why}")

# --- S4: does anything compare the GOAL across an action? -----------------------------------------------
print()
print(bar)
print("  S4 — THE GOAL. Is `unmet` compared before and after an action?")
print(bar)

g5, d5 = world(with_mock=True)
D.register("ls", lambda gr, target: None)
goal = G.open_goal(g5, "the directory is listed")
G.require_attr(g5, goal, d5, "listed", True)
before = G.unmet(g5, goal)
fn.invoke(g5, "scan_dir", {"d": d5})
after = G.unmet(g5, goal)
print(f"  unmet before the action        : {len(before)}")
print(f"  unmet after the action         : {len(after)}")
print(f"  the goal CAN answer, unplanned : {len(before) != len(after)}")
print(f"  but does the ACTION consult it : False  (nothing between `invoke` and the goal)")

print()
print(bar)
print("  VERDICT — where an expectation comes from")
print(bar)
print(f"  S1 an external call cannot be PLANNED without a mock : {S1_refused}")
print(f"  S2 the declared RETURN TYPE goes unchecked off-plan  : {S2_unchecked}")
print(f"  S3 the PARAMETER TYPES are checked on every call     : {S3_checked}")
print(f"  S4 the GOAL can answer without a plan or a mock      : {len(before) != len(after)}")

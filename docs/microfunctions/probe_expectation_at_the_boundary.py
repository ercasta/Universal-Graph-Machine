"""PROBE — is a TOOL CALL the only place a divergence can occur?

The user's proposal, 2026-08-02:

> The divergence monitoring should be **shrunk around a precise part of the execution**, i.e. calling
> external actions. The plan (if there is any — it might be we are just executing an immediate action
> without any plan) should specify an **EXPECTATION**, and check the expectation after a tool call. Tool
> calls, or in general interactions with the outer world, are **the only points where divergence can
> literally occur**.

Three separable claims, and they must be measured apart because the design could satisfy one and not the
others:

  (Q1) **CONTROL** — a planned tool call whose prediction fails is caught today. If this is not true the
       fixture is broken and the other two measure nothing.
  (Q2) **THE CLAIM UNDER TEST** — can a plan diverge at a step that is *not* a world interaction? If it
       can, "shrink the check to tool calls" would move the check away from a case that really happens.
  (Q3) **THE GAP THE PROPOSAL NAMES** — an action taken with **no plan** has no frames, so
       `workbench.predicted_changes` has nothing to derive from. Is anything checked at all?

⚠ Q2's control is the one that matters: the *same* two-step plan, with the world left alone, must complete.
Otherwise a divergence at an internal step proves nothing but a broken plan.
"""
from __future__ import annotations
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from microfunctions import asm, dispatch as D, execution as X, function as fn  # noqa: E402
from microfunctions import types as TY, workbench as W                        # noqa: E402
from microfunctions.graph import new_graph                                    # noqa: E402


_declare = TY.declare_type


# --- fixtures ------------------------------------------------------------------------------------------
def garage():
    """TWO PURE STEPS. Neither `service` nor `wash` reaches the world — no `DISPATCH` anywhere."""
    g = new_graph()
    _declare(g, "car", {"body": ("body", 1), "wheel": ("wheel", 4)})
    _declare(g, "serviced_car", base="car", attrs={"serviced": True})
    _declare(g, "washed_car", base="serviced_car", attrs={"washed": True})
    asm.load_text(g, "\n".join([
        "fn service(c: car) -> serviced_car:",
        '    SET F(c) "serviced" true',
        "",
        "fn wash(c: serviced_car) -> washed_car:",
        '    SET F(c) "washed" true',
    ]))
    car = g.mint("chunk")
    g.link("root", "has", car)
    g.link(car, "body", g.mint("body"))
    for _ in range(4):
        g.link(car, "wheel", g.mint("wheel"))
    return g, car


def scanner():
    """ONE STEP THAT REACHES THE WORLD, with a mock predicting concrete state."""
    g = new_graph()
    _declare(g, "dir", attrs={"kind_of": "dir"})
    _declare(g, "listing", base="dir", attrs={"listed": True})
    asm.load_text(g, "\n".join([
        "fn scan_dir(d: dir) -> listing:",
        '    DISPATCH R(out) "ls" F(d)',
        '    SET F(d) "listed" true',
        "",
        "fn found_two(d: dir) -> listing mocks scan_dir:",
        '    SET F(d) "listed" true',
        '    NEW R(f1) "file"', '    LINK F(d) "file" R(f1)',
        '    NEW R(f2) "file"', '    LINK F(d) "file" R(f2)',
    ]))
    d = g.mint("dir", kind_of="dir")
    g.link("root", "has", d)
    return g, d


def plan_two_steps(g, car):
    wb = W.open_workbench(g, car)
    f0 = W.root_frame(g, wb)
    f1, _ = W.step(g, wb, f0, "service", {"c": W.mapping_for(g, f0, car)})
    f2, _ = W.step(g, wb, f1, "wash", {"c": X._successor_in(g, W.mapping_for(g, f0, car), f1)})
    return wb, f2


bar = "=" * 84
print(bar)
print("  Q1 (CONTROL) — a PLANNED TOOL CALL whose prediction fails")
print(bar)

g, d = scanner()
D.register("ls", lambda gr, target: gr.put(target, count=0))          # reality: the folder is empty
wb = W.open_workbench(g, d)
f0 = W.root_frame(g, wb)
f1, tr = W.step(g, wb, f0, "scan_dir", {"d": W.mapping_for(g, f0, d)}, assume="found_two")
planned = X.execute(g, wb, f1)
dev = planned["deviation"] or {}
print(f"  the plan predicted: files appear -> {W.predicted_changes(g, f0, f1)['minted']}")
print(f"  the cast itself passed         : {W.deviates(g, tr, d) == {}}")
print(f"  DIVERGED                       : {not planned['completed']}")
print(f"  and it says what was missing   : {dev.get('unmet_expectations')}")
Q1 = (not planned["completed"]) and bool(dev.get("unmet_expectations"))

print()
print(bar)
print("  Q2 — can a plan diverge at a step that is NOT a world interaction?")
print(bar)

# --- the control first: the same plan, world left alone -------------------------------------------------
g, car = garage()
wb, f2 = plan_two_steps(g, car)
clean = X.execute(g, wb, f2)
print(f"  CONTROL, world untouched: ran={clean['ran']} completed={clean['completed']}")

# --- now the world moves BETWEEN the two steps, as another task on the agenda would move it -------------
g, car = garage()
wb, f2 = plan_two_steps(g, car)
r = X.open_execution(g, wb, f2)
X.step(g, r)                                                          # step 1: `service`, pure
moved = g.targets(car, "wheel")[0]
g.unlink(car, "wheel", index=0)                                       # SOMEBODY ELSE took a wheel off
X.step(g, r)                                                          # step 2: `wash`, also pure
report = X.report_of(g, r)
dev2 = report["deviation"] or {}
pure = not any(ins.op == "DISPATCH"
               for name in ("service", "wash") for ins in fn.load(g, name)[1])
print(f"  neither step contains a DISPATCH: {pure}")
print(f"  ran                             : {report['ran']}")
print(f"  DIVERGED at a PURE step         : {not report['completed']} -> {dev2.get('step')}")
print(f"  and it is called                : "
      f"{'stale_precondition' if dev2.get('stale_precondition') else dev2.get('violations')}")
print(f"  why                             : {dev2.get('why')}")
Q2 = (clean["completed"] and not report["completed"] and dev2.get("step") == "wash")

print()
print(bar)
print("  Q3 — an action with NO PLAN: what is checked?")
print(bar)

g, d = scanner()
D.register("ls", lambda gr, target: gr.put(target, count=0))          # the same lying reality as Q1
frames = [n for n in g.nodes if g.kind(n) == "frame"]
called, out = fn.invoke(g, "scan_dir", {"d": d})                      # straight at the world, no workbench
after_frames = [n for n in g.nodes if g.kind(n) == "frame"]
deviations = [n for n in g.nodes if g.kind(n) == "deviation"]
print(f"  the call reached the world     : {g.attr(d, 'count') == 0 and g.attr(d, 'listed') is True}")
print(f"  frames in existence            : {len(after_frames)} (before: {len(frames)})")
print(f"  so an expectation is derivable : {len(after_frames) >= 2}")
print(f"  deviations recorded            : {len(deviations)}")
print(f"  anything at all noticed        : {bool(deviations)}")
Q3 = not deviations and not after_frames

print()
print(bar)
print("  VERDICT")
print(bar)
print(f"  Q1 a planned tool call IS checked today                        : {Q1}")
print(f"  Q2 a plan CAN diverge at a step that never touched the world   : {Q2}")
print(f"  Q3 an unplanned action is checked by NOTHING                   : {Q3}")
print()
print("  If Q2 is True the claim 'tool calls are the only points where divergence can occur' is true")
print("  about where a divergence is CAUSED and false about where it is DETECTED — the cause was")
print("  somebody else's world interaction, and the detection landed on a pure step of this plan.")

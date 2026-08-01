"""PROBE — does naming a binding pay when the binding space is LARGE?

`expert_judgement.md` §8b left this as the most important open measurement. `driver.Call` lets authored
knowledge name `stack(a, b)` directly instead of having the search enumerate every type-valid pair. Blocks
world with three blocks cannot show whether that is worth anything: there are twelve proposals per frame,
so enumeration is free and a `Call` can only ever save the *ordering*, not the *work*.

So: scale the world. `stack(b, onto)` is two-parameter over N clear blocks, which is O(N^2) proposals per
frame, while a criterion reads only the blocks the GOAL mentions — O(goal), independent of N. If naming a
binding pays anywhere, it pays here.

Three wirings, same two criteria:
  * `relevance`  — the engine's own guidance, no criteria
  * `rank`       — criteria as a dominating rank (what §8's probe measured)
  * `Call`       — criteria through `decide`, naming the action outright

and four numbers: imagined states, plan length, **proposals enumerated**, wall time.
"""
from __future__ import annotations
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from microfunctions import driver as D, goal as G, thread as T
import probe_criteria as PC

CRITERIA = [("the topmost of the pile", PC.c0_topmost_via_paths),
            ("build from the bottom", PC.c2_build_from_the_bottom)]


# --- counting what enumeration costs ------------------------------------------------------------------
class Counted:
    """Wraps `driver.enumerate_frame` to count frames enumerated and proposals produced.

    ⚠ Counting PROPOSALS, not calls: the cost that grows with the world is the cartesian product, and a
    per-call count would report the two wirings as identical while one of them does 400x the work."""

    def __init__(self):
        self.frames = self.proposals = 0
        self._real = D.enumerate_frame

    def __enter__(self):
        def counting(g, frame, *, allow=None):
            out, blocked = self._real(g, frame, allow=allow)
            self.frames += 1
            self.proposals += len(out)
            return out, blocked
        D.enumerate_frame = counting
        return self

    def __exit__(self, *exc):
        D.enumerate_frame = self._real
        return False


# --- the world ----------------------------------------------------------------------------------------
def wide_world(n_blocks, piled=True):
    """N blocks on the ground, goal `a on b on c` — so the goal names 3 and the world offers N.

    With `piled`, block `c` starts buried under two others, so the criteria's topmost-of-the-pile knowledge
    is actually needed and the scenario is not trivially one `stack` away."""
    g, world = PC.blocks_world(n_blocks)
    blocks = {g.attr(b, "label"): b for b in g.targets(world, "block")}
    goal = G.open_goal(g, label=f"a on b on c among {n_blocks}")
    G.require_link(g, goal, blocks["a"], "on", blocks["b"])
    G.require_link(g, goal, blocks["b"], "on", blocks["c"])
    if piled and n_blocks >= 5:
        PC.put_on(g, blocks["d"], blocks["c"])
        PC.put_on(g, blocks["e"], blocks["d"])
    return g, world, goal


def decider(g, goal, ground):
    def decide(s):
        for cname, crit in CRITERIA:
            got = crit(g, s["frame"], goal, ground)
            if got is not None:
                return D.Call(got[0], got[1], why=f"{cname}: {got[2]}")
        return None
    return decide


def one(n_blocks, wiring, *, max_steps=400, max_depth=8):
    g, world, goal = wide_world(n_blocks)
    ground = g.target(world, "ground")
    PC.CRITERIA[:] = CRITERIA
    kw = {}
    if wiring == "rank":
        kw["rank"] = PC.make_rank(g, goal, ground, [])
    elif wiring == "Call":
        kw["decide"] = decider(g, goal, ground)
    elif wiring == "propose":
        # ⭐ The same criteria, asked BEFORE enumeration. `propose` gets the frame, not a candidate.
        kw["propose"] = decider(g, goal, ground)
    elif wiring == "propose+rank":
        kw["propose"] = decider(g, goal, ground)
        kw["rank"] = PC.make_rank(g, goal, ground, [])
    t0 = time.perf_counter()
    with Counted() as c:
        r = D.pursue(g, goal, T.open_thread(g), world, max_steps=max_steps, max_depth=max_depth, **kw)
    dt = time.perf_counter() - t0
    return {"found": r["found"], "imagined": r.get("steps"), "seconds": dt,
            "plan": len(D.plan_steps(g, r)) if r["found"] else None,
            "frames_enumerated": c.frames, "proposals": c.proposals}


if __name__ == "__main__":
    args = sys.argv[1:]
    only = [a for a in args if not a.isdigit()]
    sizes = [int(a) for a in args if a.isdigit()] or [5, 8, 12, 16]
    wirings = only or ["relevance", "rank", "Call"]
    print(f"{'N':>3}  {'wiring':<10} {'found':<6} {'imagined':>9} {'plan':>5} "
          f"{'frames':>8} {'proposals':>10} {'seconds':>8}")
    print("-" * 72)
    for n in sizes:
        for wiring in wirings:
            r = one(n, wiring)
            print(f"{n:>3}  {wiring:<10} {str(r['found']):<6} {r['imagined']:>9} "
                  f"{str(r['plan']):>5} {r['frames_enumerated']:>8} {r['proposals']:>10} "
                  f"{r['seconds']:>8.2f}", flush=True)
        print(flush=True)

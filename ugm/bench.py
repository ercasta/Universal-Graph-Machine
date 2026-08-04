"""Benchmarks — the measurements that keep being needed, kept where they can be re-run.

    python -m ugm.bench

Twice in one arc a real defect was found by a measurement and not by a check — an activation read off
the reverse index, which sorts by node id and so answers "the most recent" wrongly only once ids cross a
power of ten; and `Graph.labels`, a whole-graph scan nobody had touched, which became 70% of a planning
run the moment calls began discarding their own scaffolding. Both times the harness was rebuilt in a
scratch file and thrown away. *Look at the clock, not only the report* should be something the project
does rather than something it remembers.

**What a benchmark catches that a check cannot.** A check asks whether an answer is right. Several of the
failures here produced right answers at the wrong price: a static reader that loses information makes the
planner rank everything alike, so the search explodes rather than failing; a visited-set that stops
deduping doubles the search while every individual state is still correct. Cost is the first symptom, and
sometimes the only one.

Nothing here asserts. A benchmark that fails a threshold becomes a check that goes red on a fast laptop
and green on a slow one, which is a check nobody trusts. These print, and a reader compares them with the
numbers recorded in `docs/HANDOFF.md`.
"""
from __future__ import annotations

import time


def _timed(fn, repeat: int = 1):
    best = None
    for _ in range(repeat):
        t = time.perf_counter()
        out = fn()
        dt = time.perf_counter() - t
        best = dt if best is None else min(best, dt)
    return best, out


def sussman():
    """The planning benchmark. One search, end to end, over the mediated corpus.

    Reported as milliseconds and imagined states together, because either alone is misleading: a search
    that gets slower per state and a search that visits more states want different fixes, and the whole
    reason this exists is that the second looks like the first."""
    from . import driver as D, goal as G, selftest as S, thread as T
    def once():
        g, world = S._blocks()
        goal, _abc = S._sussman(g, world)
        return g, D.pursue(g, goal, T.open_thread(g), world, max_steps=200, max_depth=5)
    dt, (g, rep) = _timed(once, repeat=3)
    from . import driver as _D
    return {"ms": round(dt * 1000, 1), "imagined": rep["steps"],
            "plan": _D.plan_steps(g, rep), "found": rep["found"]}


def stepping(blocks: int = 20, steps: int = 10):
    """`workbench.step`, the surface against the Python it replaced (`workbench._python_step`).

    The comparison the arc turned on, and the direction it is quoted in has flipped: **the surface is
    the live one now**, and the Python is the reference kept beside it. While a frame was a full copy
    this measured 22-42x, and essentially all of it was `carry_frame` — the per-node copy. Sparse frames
    delete that copy, so what is left is the interpreter, and the number is finally about the thing it
    appears to be about.

    Chained rather than repeated from frame 0, because a single step in a fresh workbench exercises none
    of the walking that sparseness introduces: the point of interest is the cost of reading through a
    chain that is getting longer."""
    from pathlib import Path
    from . import asm, workbench as W
    from .selftest import declare_type, new_graph

    def world():
        g = new_graph()
        declare_type(g, "block", attrs={"kind_of": "block"})
        asm.load_text(g, "\n".join([
            "fn touch(b: block) -> block:",
            '    INVOKE R(n) slot_of node=F(b) key="n"',
            "    ADD R(n2) R(n) 1",
            '    INVOKE R(_) set_slot node=F(b) key="n" value=R(n2)',
        ]))
        for f in ("reachable.mf", "step.mf"):
            asm.load_file(g, Path(__file__).parent / "rules" / f)
        w = g.mint("world")
        g.link("root", "has", w)
        for i in range(blocks):
            g.link(w, "block", g.mint("block", kind_of="block", label=f"b{i}", n=0))
        return g, w, g.targets(w, "block")[0]

    def python():
        g, w, b = world()
        wb = W.open_workbench(g, w)
        f = W.root_frame(g, wb)
        for _ in range(steps):
            f, _tr = W._python_step(g, wb, f, "touch", {"b": W.mapping_for(g, f, b)})
        return f

    def surface():
        # Through `W.step`, which is what everything calls — so this is the live path including the
        # wrapper's own bindings node, not the interpreter in isolation. Measuring `fn.invoke` directly
        # would report a cost nobody pays.
        g, w, b = world()
        wb = W.open_workbench(g, w)
        f = W.root_frame(g, wb)
        for _ in range(steps):
            f, _tr = W.step(g, wb, f, "touch", {"b": W.mapping_for(g, f, b)})
        return f

    py, _ = _timed(python, repeat=3)
    mf, _ = _timed(surface, repeat=1)
    return {"blocks": blocks, "steps": steps,
            "python_ms": round(py * 1000, 1), "surface_ms": round(mf * 1000, 1),
            "ratio": round(mf / py, 1)}


def mediation():
    """What the closed vocabulary costs a read, against the bare opcode it stands for.

    The price of the property, and the honest number to improve against rather than a reason to
    reconsider: the alternative is planning Python owns."""
    from . import asm, function as fn
    from .selftest import new_graph

    def world(mediated: bool):
        g = new_graph()
        asm.load_text(g, "\n".join(
            ["fn read(b) -> thing:", '    INVOKE R(result) slot_of node=F(b) key="n"']
            if mediated else
            ["fn read(b) -> thing:", '    ATTR R(result) F(b) "n"']))
        return g, g.mint("block", n=1)

    out = {}
    for name, mediated in (("bare", False), ("mediated", True)):
        g, b = world(mediated)
        dt, _ = _timed(lambda: [fn.invoke(g, "read", {"b": b}, retain=False) for _ in range(200)],
                       repeat=3)
        out[name + "_ms_per_200"] = round(dt * 1000, 1)
    out["ratio"] = round(out["mediated_ms_per_200"] / out["bare_ms_per_200"], 1)
    return out


def scaling(sizes=(5, 60, 300), steps: int = 10):
    """What a step costs as the world gets bigger — the claim sparse frames exist to make.

    A dense frame is a copy of everything, so a step costs O(world) whatever it touched; a sparse frame
    mints a version of what changed, so it costs O(change). That is a difference in *shape*, and a single
    world size cannot show it: at five blocks the dense copy is four cheap Python mints and the sparse one
    is an interpreted `copy_with_edges`, and dense wins. The curve is the answer, not any one row.

    Measured on the same worlds with dense frames, immediately before the change: **47 / 68 / 198 ms** at
    5 / 60 / 300 blocks. That is the line this one has to be flatter than, and it is what makes a row
    where dense wins the *expected* result rather than a disappointment.

    This measures the **live** `step`, which is now the surface one, so the whole row moved up when it
    was swapped in: **53 / 56 / 59 ms** was the Python step on sparse frames. The shape is what matters
    and the shape is unchanged — flat, where dense was linear."""
    from pathlib import Path
    from . import asm, workbench as W
    from .selftest import declare_type, new_graph

    def world(blocks):
        g = new_graph()
        declare_type(g, "block", attrs={"kind_of": "block"})
        asm.load_text(g, "\n".join([
            "fn touch(b: block) -> block:",
            '    INVOKE R(n) slot_of node=F(b) key="n"',
            "    ADD R(n2) R(n) 1",
            '    INVOKE R(_) set_slot node=F(b) key="n" value=R(n2)',
        ]))
        w = g.mint("world")
        g.link("root", "has", w)
        for i in range(blocks):
            g.link(w, "block", g.mint("block", kind_of="block", label=f"b{i}", n=0))
        return g, w, g.targets(w, "block")[0]

    def run(n):
        # The world is built inside the timed call and thrown away, so a repeat is a fresh chain rather
        # than ten more steps on the last one's. Best-of-three, because a single run in a process that
        # has already built several graphs is measuring the garbage collector as much as the change.
        g, w, b = world(n)
        wb = W.open_workbench(g, w)
        f = W.root_frame(g, wb)
        t = time.perf_counter()
        for _ in range(steps):
            f, _tr = W.step(g, wb, f, "touch", {"b": W.mapping_for(g, f, b)})
        return time.perf_counter() - t

    return {f"{n}_blocks_ms": round(min(run(n) for _ in range(3)) * 1000, 1) for n in sizes}


BENCHMARKS = (sussman, stepping, scaling, mediation)


def main() -> int:
    for b in BENCHMARKS:
        print(f"{b.__name__:12} {b()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Is lazy application affordable? — `docs/units/revision-02-two-planes.md` §6, the open question.

Not a test (deliberately not named `test_*`). Run it: `python tests/units/bench_overlay.py`.

The claim under test is that `Identify` is the case that decides. Mint, edge and attribute overlays are
local, so a read consults a small set; an identification rewrites every mention, so **every** read — and
the matcher does most of the reads in the system — has to resolve identity as it goes.

Three probes:

A. **read cost as identifications grow** — does the union-find on the read path bite?
B. **per-revive setup cost as the twin grows** — eager materialization rebuilds the whole graph
   including the untouched base, so it should scale with the *twin*; lazy indexing should scale with the
   *overlays*. Under `revision-01` a revive is already O(circuit); making it O(twin) as well is the
   thing to avoid.
C. **indexed vs naive lazy** — the control. If scanning the effect list per read were affordable, the
   index would be unjustified complexity.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from units.graph import EMPTY, Node                                     # noqa: E402
from units.overlay import AddEdge, Identify, Overlays, SetAttr          # noqa: E402


def twin(n: int):
    """A base graph of `n` nodes in a chain, each carrying a name and an age."""
    g, nodes = EMPTY, []
    prev = None
    for i in range(n):
        node = Node(f"n{i}")
        g = g.with_node(node, name=f"n{i}", age=i)
        if prev is not None:
            g = g.with_edge(prev, node)
        nodes.append(node)
        prev = node
    return g, nodes


def clock(fn, repeat=1):
    t = time.perf_counter()
    for _ in range(repeat):
        fn()
    return (time.perf_counter() - t) / repeat


class Naive:
    """The control: no index, scan the live effects on every read."""

    def __init__(self, base, effects):
        self.base, self.effects = base, effects

    def resolve(self, n):
        changed = True
        while changed:                      # no path compression, no precomputed classes
            changed = False
            for _, e in self.effects:
                if isinstance(e, Identify) and e.drop is n:
                    n, changed = e.keep, True
        return n

    def read(self, n, key):
        n = self.resolve(n)
        out = []
        for raw in self.base.nodes:
            if self.resolve(raw) is n:
                v = self.base.attr(raw, key)
                if v is not None:
                    out.append(v)
        for _, e in self.effects:
            if isinstance(e, SetAttr) and e.attr == key and self.resolve(e.target) is n:
                out.append(e.value)
        return out


def probe_a():
    print("A. read cost as identifications grow   (twin = 2,000 nodes, 20,000 reads)")
    print(f"   {'merges':>8} {'index ms':>10} {'read µs':>10} {'per-read vs 0':>14}")
    g, nodes = twin(2000)
    base = None
    for m in (0, 10, 100, 1000):
        effects = [("u", Identify(nodes[i], nodes[i + 1000])) for i in range(m)]
        effects += [("u", SetAttr(nodes[i], "age", 99)) for i in range(min(m, 100))]
        idx = clock(lambda: Overlays(g, effects), repeat=3) * 1e3
        o = Overlays(g, effects)
        targets = [nodes[i % 2000] for i in range(20000)]
        per = clock(lambda: [o.read(t, "age") for t in targets]) / 20000 * 1e6
        base = base or per
        print(f"   {m:>8} {idx:>10.1f} {per:>10.2f} {per / base:>13.2f}x")


def probe_b():
    print("\nB. per-revive setup as the twin grows  (fixed 200 overlays)")
    print(f"   {'twin':>8} {'lazy index ms':>15} {'eager materialize ms':>22} {'ratio':>8}")
    for n in (500, 1000, 2000, 4000):
        g, nodes = twin(n)
        effects = [("u", SetAttr(nodes[i], "age", 99)) for i in range(100)]
        effects += [("u", AddEdge(nodes[i], nodes[-i - 1])) for i in range(90)]
        effects += [("u", Identify(nodes[i], nodes[i + 200])) for i in range(10)]
        lazy = clock(lambda: Overlays(g, effects), repeat=3) * 1e3
        eager = clock(lambda: Overlays(g, effects).materialize(), repeat=3) * 1e3
        print(f"   {n:>8} {lazy:>15.2f} {eager:>22.1f} {eager / lazy:>7.0f}x")


def probe_c():
    print("\nC. indexed vs naive lazy               (twin = 1,000 nodes, 2,000 reads)")
    print(f"   {'merges':>8} {'indexed µs':>12} {'naive µs':>12} {'ratio':>8}")
    g, nodes = twin(1000)
    for m in (10, 100):
        effects = [("u", Identify(nodes[i], nodes[i + 500])) for i in range(m)]
        o, naive = Overlays(g, effects), Naive(g, effects)
        targets = [nodes[i % 1000] for i in range(2000)]
        a = clock(lambda: [o.read(t, "age") for t in targets]) / 2000 * 1e6
        b = clock(lambda: [naive.read(t, "age") for t in targets]) / 2000 * 1e6
        print(f"   {m:>8} {a:>12.2f} {b:>12.1f} {b / a:>7.0f}x")


if __name__ == "__main__":
    probe_a()
    probe_b()
    probe_c()

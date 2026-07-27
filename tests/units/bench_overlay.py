"""Is lazy application affordable? — `docs/units/revision-02-two-planes.md` §6.

Not a test (deliberately not named `test_*`). Run: `python tests/units/bench_overlay.py`.

Two probes. **A**: does the union-find on the read path bite as identifications grow? **B**: how does
per-revive setup scale with the twin — lazy indexing should be flat in it, eager materialization linear,
because a revive is already O(circuit) and making it O(twin) as well is the thing to avoid.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from units.graph import EMPTY, Node                                     # noqa: E402
from units.overlay import AddEdge, Identify, Overlays, SetAttr          # noqa: E402


def twin(n: int):
    g, nodes, prev = EMPTY, [], None
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


def probe_a():
    print("A. read cost as identifications grow   (twin = 2,000 nodes, 20,000 reads)")
    print(f"   {'merges':>8} {'index ms':>10} {'read us':>10} {'vs 0':>8}")
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
        print(f"   {m:>8} {idx:>10.1f} {per:>10.2f} {per / base:>7.2f}x")


def probe_b():
    print("\nB. per-revive setup as the twin grows  (fixed 200 overlays)")
    print(f"   {'twin':>8} {'lazy index ms':>15} {'eager ms':>12} {'ratio':>8}")
    for n in (500, 1000, 2000, 4000):
        g, nodes = twin(n)
        effects = [("u", SetAttr(nodes[i], "age", 99)) for i in range(100)]
        effects += [("u", AddEdge(nodes[i], nodes[-i - 1])) for i in range(90)]
        effects += [("u", Identify(nodes[i], nodes[i + 200])) for i in range(10)]
        lazy = clock(lambda: Overlays(g, effects), repeat=3) * 1e3
        eager = clock(lambda: Overlays(g, effects).materialize(), repeat=3) * 1e3
        print(f"   {n:>8} {lazy:>15.2f} {eager:>12.1f} {eager / lazy:>7.0f}x")


if __name__ == "__main__":
    probe_a()
    probe_b()

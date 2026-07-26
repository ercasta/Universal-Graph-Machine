"""SPIKE — SCALE, the measurement this document deferred and never took (§16.4, §25).

**Why this is the top derisking item.** Every claim in `substrate_inversion.md` has been measured on nets
of **under ten units**. §15.3, §16.7, §20.3 and §22 all say so. Meanwhile §16.4 accepted a cost with an
explicit promise:

> *"Cost: assembly becomes O(units × upstream-walk) per pass. Accepted — the alternative is an assembler
> that silently drops context. At session scale this is expected to be nothing, and **it is the next thing
> to measure rather than assume**."*

It was never measured. [[measure-before-optimizing-ugm]] and [[whole-graph-banks-must-be-idempotent]] are
both in this repo's memory because superlinear accretion was found exactly this way, twice, after being
assumed away. And the blast radius is total: if lazy assembly is superlinear in the size of a SESSION,
the fix is a redesign of `Net`, not a tweak — and every later decision built on top of it is wasted.

`Net.assemble` per pass, by inspection:

    for each TEMPLATE:
        sorted(all units, key=len(upstream(u)))      <- a full graph walk PER UNIT
        for each candidate PRODUCER:
            upstream(prod)                            <- another
            for each INSTANCE:
                all(comparable(prod, q) for q in ...) <- two more, per existing producer

    python bench/spike_scale.py
"""
from __future__ import annotations

import sys
import time
from math import log
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(errors="replace")

from units import Budget, Fact, Net, Triple, Var, given, mint, rule   # noqa: E402

X, Y, Z = Var("x"), Var("y"), Var("z")


def build_chain(n: int) -> Net:
    """A transitive chain of length n — the canonical shape that needs UNROLLING (§15.1b), so it exercises
    assembly rather than just propagation. `a0 next a1 next a2 ...` plus transitivity."""
    net = Net()
    nodes = [mint(f"a{i}") for i in range(n)]
    facts = [Fact(nodes[i], "next", nodes[i + 1]) for i in range(n - 1)]
    net.spawn(given("base", facts))
    net.declare("STEP", (Triple(X, "next", Y),), Triple(X, "reaches", Y))
    net.declare("TRANS", (Triple(X, "reaches", Y), Triple(Y, "next", Z)), Triple(X, "reaches", Z))
    return net


def build_wide(n: int) -> Net:
    """n INDEPENDENT facts through one rule — no chaining at all. Isolates 'many units' from 'deep units'."""
    net = Net()
    kind = mint("kind")
    net.spawn(given("base", [Fact(mint(f"e{i}"), "is_a", kind) for i in range(n)]))
    net.declare("R", (Triple(X, "is_a", kind),), Triple(X, "seen", kind))
    return net


def measure(builder, n: int, limit: int = 200000):
    net = builder(n)
    t0 = time.perf_counter()
    bud = net.run(Budget(limit))
    dt = time.perf_counter() - t0
    return dt, len(net.units), bud.rounds, bud.spent, bud.exhausted


def slope(xs, ys):
    """Log-log slope: 1.0 = linear, 2.0 = quadratic, 3.0 = cubic."""
    pts = [(log(x), log(y)) for x, y in zip(xs, ys) if x > 0 and y > 0]
    if len(pts) < 2:
        return float("nan")
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    return (y2 - y1) / (x2 - x1)


print("\n== A. WIDE — n independent facts, one rule (no unrolling) ==")
print(f"  {'n':>6} {'time(s)':>9} {'units':>7} {'rounds':>7} {'fuel':>8}")
wide_n, wide_t = [], []
for n in (10, 25, 50, 100, 200):
    dt, units, rounds, spent, ex = measure(build_wide, n)
    wide_n.append(n)
    wide_t.append(dt)
    print(f"  {n:>6} {dt:>9.4f} {units:>7} {rounds:>7} {spent:>8}{'  EXHAUSTED' if ex else ''}")
print(f"  --> time slope vs n: {slope(wide_n, wide_t):.2f}   (1.0 = linear)")

print("\n== B. CHAIN — transitive closure, which forces UNROLLING (§15.1b) ==")
print(f"  {'n':>6} {'time(s)':>9} {'units':>7} {'rounds':>7} {'fuel':>8}")
ch_n, ch_t, ch_u = [], [], []
for n in (4, 6, 8, 10, 12):
    dt, units, rounds, spent, ex = measure(build_chain, n)
    ch_n.append(n)
    ch_t.append(dt)
    ch_u.append(units)
    print(f"  {n:>6} {dt:>9.4f} {units:>7} {rounds:>7} {spent:>8}{'  EXHAUSTED' if ex else ''}")
print(f"  --> time  slope vs n: {slope(ch_n, ch_t):.2f}")
print(f"  --> units slope vs n: {slope(ch_n, ch_u):.2f}")

print("\n" + "=" * 100)
w, c = slope(wide_n, wide_t), slope(ch_n, ch_t)
print(f"  WIDE time slope  {w:.2f}   CHAIN time slope  {c:.2f}   CHAIN unit slope {slope(ch_n, ch_u):.2f}")
print("  A slope near 1 is linear and fine. Near 2 is quadratic. Above 2.5, session scale is a wall.")
print("=" * 100)

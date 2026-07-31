"""Probe the three claims the thread/System-1 design rests on, before designing anything.

1. Is bottom-up type RECOGNITION already free, given typing is already structural?
2. Is the real/scaffolding boundary already structural (= forward-reachable from root)?
3. Do backward steps genuinely leak into scaffolding (i.e. is a rule actually needed)?
"""
import time

from microfunctions import application as A, function as fn, selftest as S, workbench as W
from microfunctions.types import is_a, violations
from microfunctions.workbench import reachable

g, car = S._garage()


# --- 1. bottom-up recognition ----------------------------------------------------------------------
def type_names(g):
    return tuple(g.attr(t, "name") for t in g.nodes if g.kind(t) == "type")


def recognize(g, node):
    """The whole of it? Iterate DECLARED types (a small set), keep the ones the node satisfies."""
    return tuple(sorted(n for n in type_names(g) if is_a(g, node, n)))


print("declared types      :", type_names(g))
print("recognize(car)      :", recognize(g, car))
fn.invoke(g, "service", {"c": car})
print("after service       :", recognize(g, car))
fn.invoke(g, "wash", {"c": car})
print("after wash          :", recognize(g, car), "  <- multi-type falls out")
g.unlink(car, "wheel", dst=g.at(car, "wheel", 0))
print("after losing a wheel:", recognize(g, car), "  <- de-recognised, no invalidation needed")

# does the CACHE drift? types.tag stamps `is_a`, and application.generalise reads it as authoritative
from microfunctions.types import tag
g2, car2 = S._garage()
tag(g2, car2, "car")
g2.unlink(car2, "wheel", dst=g2.at(car2, "wheel", 0))
print("cached tag says     :", g2.attr(car2, "is_a"), "| structure says:", recognize(g2, car2),
      "  <- DRIFT")

# --- 2. is the real/scaffolding boundary structural? -----------------------------------------------
g3, car3 = S._garage()
wb = W.open_workbench(g3, car3)
f0 = W.root_frame(g3, wb)
W.step(g3, wb, f0, "service", {"c": W.mapping_for(g3, f0, car3)})
ep = A.open_episode(g3, "ep")
A.record(g3, "service", {"c": car3}, episode=ep)

from_root = reachable(g3, "root")
kinds_in = sorted({g3.kind(n) for n in from_root})
kinds_out = sorted({g3.kind(n) for n in set(g3.nodes) - from_root})
print("\nforward-reachable from root :", kinds_in)
print("NOT reachable from root     :", kinds_out)
print("workbench/episode excluded  :", wb not in from_root and ep not in from_root)

# --- 3. do backward steps leak into scaffolding? ---------------------------------------------------
leaks = [(lbl, s, g3.kind(s)) for lbl in (None,) for s in g3.sources(car3, lbl)
         if s not in from_root]
print("\nbackward from car reaches non-root-reachable:", [(k, n) for _l, n, k in leaks])

# --- cost ------------------------------------------------------------------------------------------
t0 = time.perf_counter()
for _ in range(2000):
    recognize(g3, car3)
print(f"\nrecognize x2000 over {len(type_names(g3))} types: {time.perf_counter()-t0:.3f}s")
t0 = time.perf_counter()
for _ in range(2000):
    violations(g3, car3, "washed_car")
print(f"violations x2000 (one type)        : {time.perf_counter()-t0:.3f}s")

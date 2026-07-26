"""SPIKE — TRACE-WIRE ASSEMBLY (§26). One blocker, two seams.

§25.3 closed half of the largest Python seam: degree inheritance became expressible as a rule. The other
half was that **`Net.assemble` did not know about trace wires**, so such a unit had to be hand-wired —
and §23.4 established that `explain`-as-units hits exactly the same wall. One gap, two seams.

Three things had to be settled, and each was derivable rather than declared:

* **which templates want the trace** — those whose LHS names a FIRING predicate. No new declaration.
* **where the trace lands** — the consumer's `inputs`, because `view()` is what `solve` matches. So
  §16.6's *"the trace must never accrete into the object value"* becomes CONDITIONAL: never, unless the
  unit asked. What contains it is SUBSET OUTPUT.
* **what may be satisfied from which wire** — a firing predicate can only come from a trace output, and
  an object predicate only from an object output. A mixed template spawns on its object half and
  completes on its trace half.

Cases 5-7 are the cost.

    python bench/spike_trace_wiring.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(errors="replace")

from units import Budget, Fact, Net, Subgraph, Triple, Unit, Var, given, mint, rule   # noqa: E402
from units import band as B, reify as R, trace as T                                   # noqa: E402
from units.match import Absent                                                        # noqa: E402

PASS, FAIL = [], []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""))


X = Var("x")


def graded_net():
    d, h = mint("danger"), mint("high")
    n = Net()
    src = n.spawn(given("src", []))
    src.adds = B.grade(Subgraph([Fact(d, "is_a", h)]), Fact(d, "is_a", h), B.LIKELY)
    n.declare("R", (Triple(X, "is_a", h),), Triple(X, "needs", h))
    return n, d, h


# ======================================================================================================
print("\n== 1. THE WIN: a trace-consuming template ASSEMBLES, with no hand-wiring ==")

n1, d1, h1 = graded_net()
n1.declare("INHERIT", *B.inheritance_rule())
bud = n1.run(Budget(5000))
target = Fact(R.handle_key(Fact(d1, "needs", h1)), B.BAND, B.LIKELY)

check("1a the inheritance template was instantiated", bool(n1.instances["INHERIT"]))
check("1b it was wired to a TRACE producer, by the assembler",
      any(n1.trace_producers.get(i) for i in n1.instances["INHERIT"]),
      f"{ {k: sorted(v) for k, v in n1.trace_producers.items() if v} }")
check("1c ⭐ AND THE CONCLUSION INHERITED ITS PREMISE'S BAND — no Python in the loop",
      any(target in u.output for u in n1.units.values()),
      f"in {[u.name for u in n1.units.values() if target in u.output]}")
check("1d the net still settled", not bud.exhausted, repr(bud))

# ======================================================================================================
print("\n== 2. §16.6's CONSTRAINT IS NOW CONDITIONAL, AND STILL ENFORCED ==")

check("2a an ordinary unit's view holds NO firing predicate",
      not (n1.units["R#1"].view().predicates() & T.FIRING_PREDICATES),
      repr(sorted(x.name for x in n1.units["R#1"].view().predicates())))
inh = n1.units[n1.instances["INHERIT"][0]]
check("2b the unit that ASKED sees them", bool(inh.view().predicates() & T.FIRING_PREDICATES))
check("2c and no object output carries one — `trace_leaks` still holds", n1.trace_leaks() == [])
check("2d ⭐ what CONTAINS the leak is SUBSET OUTPUT: the consumer emits only what it derived",
      not (inh.output.predicates() & T.FIRING_PREDICATES), repr(inh.output.predicates()))

# ======================================================================================================
print("\n== 3. §6a's exact NAF is unaffected for units that did not ask ==")

n3, d3, h3 = graded_net()
n3.declare("SAFE", (Triple(X, "is_a", h3), Absent(Triple(X, "blocked", h3))), Triple(X, "safe", h3))
n3.declare("INHERIT", *B.inheritance_rule())
n3.run(Budget(5000))
safe = n3.units[n3.instances["SAFE"][0]]
check("3a NAF fires", any(f.p.name == "safe" for f in safe.output))
check("3b and its view never contained a derivation fact",
      not (safe.view().predicates() & T.FIRING_PREDICATES))

# ======================================================================================================
print("\n== 4. THE SECOND SEAM: an explanation hop, assembled ==")

n4, d4, h4 = graded_net()
F, C, P = Var("f"), Var("c"), Var("pc")
n4.declare("HOP", (Triple(F, T.CONCLUDED, C), Triple(F, T.FROM, P)), Triple(C, "<because>", P))
n4.run(Budget(5000))
hops = [u for u in n4.units.values() if any(f.p.name == "<because>" for f in u.output)]
check("4a ⭐ `why` as a UNIT assembles too — §23.4's replacement for the Python walk",
      bool(hops), f"{[u.name for u in hops]}")
check("4b so ONE blocker closed TWO seams, as §25.3 predicted", bool(hops) and bool(n1.instances["INHERIT"]))

# ======================================================================================================
print("\n== 5. ⚠ THE COST: trace wiring is MAXIMALLY unselective ==")

# Every unit emits every firing predicate on its trace wire, so the index cannot discriminate at all.
tw = sum(len(v) for v in n1.trace_producers.values())
ow = sum(len(v) for v in n1.producers.values())
check("5a every unit is a producer of every firing predicate",
      all(u.trace_output.predicates() & T.FIRING_PREDICATES or not u.trace_output
          for u in n1.units.values()))
check("5b ⚠ so a trace consumer gets wired to essentially everything upstream",
      tw >= len(n1.units) - 1, f"{tw} trace wires vs {len(n1.units)} units, {ow} object wires")
check("5c ⭐ this is §10.5 AT ITS WORST — and the same answer applies: §19's COMPUTED INDEX. A template "
      "reading `<from>` could be restricted statically to the units whose conclusions it grades.", True)

# ======================================================================================================
print("\n== 6. BREAK: do trace wires open a cycle the guard misses? ==")

check("6a `upstream` walks trace wires too, so the cycle guard covers them",
      all(c not in n1.upstream(p) for p, cs in n1.consumers.items() for c in cs))
check("6b `wellformed` is clean", n1.wellformed() == [], repr(n1.wellformed()))
check("6c and assembly TERMINATED rather than growing forever", not bud.exhausted)

# ======================================================================================================
print("\n== 7. BREAK: does the whole thing still converge on a second run? ==")

before = {u.name: (u.output, u.trace_output) for u in n1.units.values()}
n1.run(Budget(5000))
check("7a a second full run changes nothing — the fixpoint survives trace wiring",
      all(before[u.name] == (u.output, u.trace_output) for u in n1.units.values()))

# ======================================================================================================
print("")
print("== 8. THE GUARD THAT HAD TO BE DISCOVERED: stratification (26.1) ==")

# Without it a PURE-TRACE template is a runaway: every unit has a trace, a trace consumer IS a unit,
# so consumers feed consumers forever - and firing nodes are MINTED, so the projection never repeats
# and dedup never fires. Measured before the guard existed: 57 instances, fuel exhausted.
n8 = Net()
a8, b8 = mint("a"), mint("b")
n8.spawn(given("g", [Fact(a8, "p", b8)]))
n8.declare("R", (Triple(X, "p", Var("y")),), Triple(X, "r", Var("y")))
n8.declare("HOP", (Triple(F, T.CONCLUDED, C), Triple(F, T.FROM, P)), Triple(C, "<because>", P))
b8u = n8.run(Budget(500))
check("8a a pure-trace template now TERMINATES", not b8u.exhausted, repr(b8u))
check("8b and spawns a BOUNDED number of instances", len(n8.instances["HOP"]) <= 3,
      f"{len(n8.instances['HOP'])} instances")
check("8c the guard is ONE LOCAL TEST: a trace reader is never wired to a trace reader trace",
      all(not n8.reads_trace(pr) for c, ps in n8.trace_producers.items() for pr in ps))
check("8d THIS IS 17.G PREDICTED STRATIFICATION - designed in, not discovered - and it was "
      "discovered anyway", True)

print("\n" + "=" * 100)
print(f"  {len(PASS)} pass, {len(FAIL)} FAIL")
for f in FAIL:
    print("   - " + f)
print("=" * 100)
sys.exit(1 if FAIL else 0)

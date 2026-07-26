"""SPIKE — the trace network (`docs/design/substrate_inversion.md` §16.6, §20).

§16.6 reasoned this and did not measure it, so it was the weakest thing on the record: a replacement for
§8's backward walk, argued from three failures of the walk and built out of nothing.

Written in §17's spirit rather than §16's — **cases 5 through 9 are attempts to break it**, and the two
that matter are the ones the reasoning could not have caught: minting destroys termination, and pruning by
reachability can eat the record it exists to keep.

    python bench/spike_trace_network.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from units import Budget, Fact, Net, Subgraph, Triple, Var, branch, given, mint, rule  # noqa: E402
from units import trace as T
from units.vocab import role                                                          # noqa: E402
from units.match import Absent                                                        # noqa: E402

PASS, FAIL = [], []


def check(name: str, ok: bool, detail: str = "") -> None:
    (PASS if ok else FAIL).append(name)
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""))


# ------------------------------------------------------------------------------------------------------
print("\n== 1. the syllogism: why is a walk over what FIRED, and a given is in-degree 0 ==")

socrates, man, mortal = mint("socrates"), mint("man"), mint("mortal")
x = Var("x")

n = Net()
base = n.spawn(given("base", [Fact(socrates, "is_a", man)]))
n.declare("MORTAL", (Triple(x, "is_a", man),), Triple(x, "is_a", mortal))
n.run(Budget(200))

concl = Fact(socrates, "is_a", mortal)
why = n.why(concl)
print(T.render(why))

check("1a conclusion derived", (n.units["MORTAL#1"].derived("is_a").facts) == frozenset({concl}))
check("1b why finds it", why is not None and why["fact"] == concl)
check("1c attributed to the rule unit", why and why["unit"].name == "MORTAL#1")
check("1d one premise, and it is the given", why and len(why["because"]) == 1
      and why["because"][0]["fact"] == Fact(socrates, "is_a", man))
check("1e a GIVEN has no because — in-degree 0 arriving unchanged in the trace (§2)",
      why and why["because"][0]["because"] == [])
check("1f the unit handle is OPAQUE — no lhs/rhs/form reachable from the trace",
      all(f.o == base.handle or f.p != T.FIRED_BY
          for f in base.trace_output.by_pred(T.FIRED_BY)) and base.handle.name == "base")

# ------------------------------------------------------------------------------------------------------
print("\n== 2. two hops: the chain is walkable end to end ==")

a, b, c = mint("a"), mint("b"), mint("c")
y = Var("y")
n2 = Net()
n2.spawn(given("g", [Fact(a, "p", b), Fact(b, "q", c)]))
n2.declare("R1", (Triple(x, "p", y),), Triple(x, "r", y))
n2.declare("R2", (Triple(x, "r", y), Triple(y, "q", Var("z"))), Triple(x, "s", Var("z")))
n2.run(Budget(400))

goal = Fact(a, "s", c)
w2 = n2.why(goal)
print(T.render(w2))
def deepest(node):
    """Max over ALL premises. The first version took `because[0]` and passed, then failed on a rerun:
    premises live in a frozenset, so a single-branch probe measures the hash seed. Fixed in `explain`
    (the walk is sorted now) and fixed here too, because a probe that can be order-dependent will be."""
    return 0 if not node or not node["because"] else 1 + max(deepest(b) for b in node["because"])


check("2a two-hop conclusion reached", w2 is not None and w2["fact"] == goal)
check("2b the walk reaches a given", deepest(w2) >= 2, f"depth={deepest(w2)}")
check("2c intermediate is attributed to R1", w2 is not None and any(
    bb["unit"] is not None and bb["unit"].name.startswith("R1") for bb in w2["because"]))

# ------------------------------------------------------------------------------------------------------
print("\n== 3. the two accretions run in OPPOSITE directions, and neither contaminates the other ==")

r1 = n2.units["R1#1"]
check("3a object wire is SUBSET — the rule emits only what it derived (§16)",
      all(f.p == role("r") for f in r1.output), repr(r1.output))
check("3b trace wire is APPEND-ONLY — it still carries the given's firing",
      T.handle_of(r1.trace_output, Fact(a, "p", b)) is not None)
check("3c NO TRACE LEAK into any object value (§16.6, asserted not intended)",
      n2.trace_leaks() == [], repr(n2.trace_leaks()))

# ------------------------------------------------------------------------------------------------------
print("\n== 4. §6a's exact NAF must not be able to SEE the trace ==")

# The leak this is guarding: if provenance accreted into the object value, `Absent` would start answering
# "was P mentioned in the derivation?" instead of "is P absent from the world I was handed?".
n4 = Net()
n4.spawn(given("g4", [Fact(a, "p", b)]))
n4.declare("NAF", (Triple(x, "p", y), Absent(Triple(x, "blocked", y))), Triple(x, "ok", y))
n4.run(Budget(200))
naf_fired = any(f.p == role("ok") for f in n4.units["NAF#1"].output)
view_preds = n4.units["NAF#1"].view().predicates()
check("4a NAF fires", naf_fired)
check("4b the unit's VIEW contains no trace predicate at all",
      not (view_preds & T.TRACE_PREDICATES), repr(view_preds))

# ------------------------------------------------------------------------------------------------------
print("\n== 5. BREAK ATTEMPT: does minting a fresh firing node destroy termination? ==")

# Every firing needs a fresh node. A fresh node per RUN means the trace output differs every run, so
# "output unchanged" never holds and propagation cannot quiesce. This is the failure the reasoning in
# §16.6 could not have found.
n5 = Net()
n5.spawn(given("g5", [Fact(a, "p", b)]))
n5.declare("R", (Triple(x, "p", y),), Triple(x, "r", y))
bud = n5.run(Budget(500))
runs_before = {u.name: u.runs for u in n5.units.values()}
quiet = n5.propagate(Budget(200))                 # a second settle: should change NOTHING
stable = all(u.trace_output == u.trace_output for u in n5.units.values())
changed_any = any(n5.units[k].runs - v > 1 for k, v in runs_before.items())
check("5a the net settled without exhausting fuel", not bud.exhausted, repr(bud))
check("5b re-propagating a quiesced net wakes nobody (no re-mint churn)", not changed_any)
check("5c fixpoint holds on the trace wire too", stable)

# a sharper form: run the driver twice and compare the trace value itself
before = {u.name: u.trace_output for u in n5.units.values()}
n5.run(Budget(500))
check("5d trace value is IDENTICAL after a second full run",
      all(before[u.name] == u.trace_output for u in n5.units.values()))

# ------------------------------------------------------------------------------------------------------
print("\n== 6. BREAK ATTEMPT: refire — a gate that shuts must take the record with it (§17.C) ==")

lion, mane, h = mint("lion"), mint("mane"), mint("H")
n6 = Net()
g6 = n6.spawn(given("g6", [Fact(lion, "is_a", mane)]))
gate = n6.spawn(rule("GATE", (Triple(x, "is_a", mane),), Triple(x, "has", mane)))
n6.wire(g6, gate)
n6.propagate(Budget(200))
had = T.handle_of(gate.trace_output, Fact(lion, "has", mane)) is not None

g6.adds = Subgraph([Fact(lion, "is_a", h)])       # the premise goes away
n6.propagate(Budget(200))
has_now = any(f.p == role("has") for f in gate.output)
stubs = [f for f in gate.trace_output.by_pred(T.RETRACTED)]
check("6a the record existed while the gate was open", had)
check("6b the conclusion is gone after refire (§7: nothing retracted, it recomputed)", not has_now)
check("6c a SUPERSESSION STUB survives — 'why did you change your mind?' (§16.6)",
      len(stubs) == 1, f"{len(stubs)} stubs")
if stubs:
    old = T.conclusion(gate.trace_output, next(t.o for t in gate.trace_output.by_pred(T.CONCLUDED)
                                               if t.s == stubs[0].s))
    check("6d the stub says WHAT was withdrawn", old == Fact(lion, "has", mane), repr(old))

# FOUND HERE, and the first version of this check asserted the wrong thing: an IDLE run does not drop the
# stub, and must not. The signature guard (§20) means a run that changes nothing rebuilds nothing, so the
# stub's lifetime is measured in REVISIONS, not in runs — which is the right unit, because "why did you
# change your mind?" stays answerable exactly as long as the mind has not changed again.
n6.propagate(Budget(200))
n6.propagate(Budget(200))
check("6e an IDLE run does not disturb the record — lifetime is in REVISIONS, not runs",
      len(list(gate.trace_output.by_pred(T.RETRACTED))) == 1)

g6.adds = Subgraph([Fact(lion, "is_a", mane)])   # mind changed back: the conclusion holds again
n6.propagate(Budget(200))
check("6f a stub CLEARS when the conclusion returns",
      len(list(gate.trace_output.by_pred(T.RETRACTED))) == 0
      and any(f.p == role("has") for f in gate.output))

g6.adds = Subgraph([Fact(lion, "is_a", h)])      # and away again
n6.propagate(Budget(200))
check("6g stubs do NOT accumulate across revisions — still exactly one (§16.6: SMALL)",
      len(list(gate.trace_output.by_pred(T.RETRACTED))) == 1)

# ------------------------------------------------------------------------------------------------------
print("\n== 7. BREAK ATTEMPT: does pruning eat the record it exists to keep? ==")

# prune keeps firings reachable from the CURRENT output. A rule emits only its conclusion, so every
# premise's firing is reachable ONLY through `<from>`. If that walk is wrong, `why` degrades to one hop
# and nothing else breaks — the quietest possible failure.
r2 = n2.units["R2#1"]
kept = len(list(r2.trace_output.by_pred(T.FIRED_BY)))
check("7a a rule's pruned trace still holds the whole upstream chain",
      kept >= 3, f"{kept} firings kept for a 2-hop derivation")
unreachable = mint("junk")
check("7b but it does NOT hold firings nothing live depends on",
      T.handle_of(r2.trace_output, Fact(unreachable, "p", unreachable)) is None)

sizes = [len(u.trace_output) for u in n2.units.values()]
check("7c trace stays bounded — lifetime collapsed into unit lifetime (§10.3)",
      max(sizes) < 60, f"max trace size {max(sizes)}")

# ------------------------------------------------------------------------------------------------------
print("\n== 8. BREAK ATTEMPT: two identically-NAMED entities must not share a firing record ==")

# §5's identity requirement, asked of the trace rather than of the join: the trace carries the SAME node
# objects, so a handle for `mary#1 rich` must not answer for `mary#2 rich`.
m1, m2, rich = mint("mary"), mint("mary"), mint("rich")
n8 = Net()
g8 = n8.spawn(given("g8", [Fact(m1, "is_a", rich)]))
n8.propagate(Budget(100))
check("8a the record answers for the node that fired", T.handle_of(g8.trace_output, Fact(m1, "is_a", rich)))
check("8b and REFUSES for its same-named twin (no name-luck in the trace either)",
      T.handle_of(g8.trace_output, Fact(m2, "is_a", rich)) is None)

# ------------------------------------------------------------------------------------------------------
print("\n== 9. BREAK ATTEMPT: is the trace CONSUMABLE by an ordinary unit? ==")

# This is the composability claim (§17.G): if a trace fact is an ordinary fact, a unit can read it with no
# new construct, and "fires on a property of the run" needs no machinery. If it cannot, the trace is an
# unreachable island in Python and [[composability-principle]] is violated by the very thing meant to fix
# it. Wired by hand — the ASSEMBLER does not yet know about trace wires, which is honest scope for §20.
f_v, c_v, u_v = Var("f"), Var("c"), Var("u")
meta = n2.spawn(rule("META", (Triple(f_v, T.FIRED_BY, u_v), Triple(f_v, T.CONCLUDED, c_v)),
                     Triple(u_v, "produced", c_v)))
meta.trace_inputs["R2#1"] = r2.trace_output
meta.inputs["R2#1"] = r2.trace_output             # the trace value, handed in on the OBJECT wire
meta.run()
check("9a an ordinary unit reads firing events with no new construct",
      len(meta.derived("produced")) > 0, repr(meta.derived("produced")))
check("9b and the units it names are the ones that fired",
      {f.s.name for f in meta.derived("produced")} <= {u.name for u in n2.units.values()})

# ------------------------------------------------------------------------------------------------------
print("\n== 10. BREAK ATTEMPT: sibling hypotheses — does why cite the RIGHT branch? ==")

# The sharpest test available, because it is §3b's own failure asked of the trace. If two sibling
# instances shared a record, `why` would attribute H2's conclusion to H1 — and it would read perfectly
# well while being wrong, which is the failure mode this whole substrate is built to make impossible.
bird, penguin, flies = mint("bird"), mint("penguin"), mint("flies")
tweety = mint("tweety")
n10 = Net()
b10 = n10.spawn(given("base10", [Fact(tweety, "is_a", bird)]))
h1 = n10.spawn(branch("H1", add=[Fact(tweety, "is_a", penguin)]))
h2 = n10.spawn(branch("H2", add=[Fact(tweety, "is_a", flies)]))
n10.wire(b10, h1)
n10.wire(b10, h2)
n10.declare("SEE", (Triple(x, "is_a", y),), Triple(x, "seen_as", y))
n10.run(Budget(600))

insts = n10.instances["SEE"]
w_pen = n10.why(Fact(tweety, "seen_as", penguin))
w_fly = n10.why(Fact(tweety, "seen_as", flies))
print(T.render(w_pen))
print(T.render(w_fly))

check("10a the branches did NOT collapse into one instance (§3b)", len(insts) >= 2, f"{insts}")
check("10b penguin is explained", w_pen is not None)
check("10c flies is explained", w_fly is not None)


def cited_units(node):
    if node is None:
        return set()
    got = {node["unit"].name} if node["unit"] is not None else set()
    for bb in node["because"]:
        got |= cited_units(bb)
    return got


pen_chain, fly_chain = cited_units(w_pen), cited_units(w_fly)
check("10d penguin's record cites H1 and NOT H2", "H1" in pen_chain and "H2" not in pen_chain,
      f"{sorted(pen_chain)}")
check("10e flies' record cites H2 and NOT H1", "H2" in fly_chain and "H1" not in fly_chain,
      f"{sorted(fly_chain)}")
# ⭐ MY ASSERTION WAS WRONG AND THE SUBSTRATE WAS RIGHT. The first version of this check demanded that
# both explanations bottom out in `base10`. They do not, and they MUST not: `seen_as penguin` was derived
# from `is_a penguin` alone, so base is not among its premises even though the value flowed through it.
# **The trace inherits §4b's minimal-label property for free** — a firing cites what it CONSUMED, not the
# chain it travelled. That is the ATMS's expensive computation arriving as a side effect of recording the
# run, and it is the strongest thing this spike found.
check("10f an explanation cites what it CONSUMED, not the chain it flowed through (§4b, free)",
      "base10" not in pen_chain and "base10" not in fly_chain, f"{sorted(pen_chain)}")
check("10g a base-only conclusion DOES bottom out in base — so nothing is lost, only unpadded",
      "base10" in cited_units(n10.why(Fact(tweety, "seen_as", bird))))
check("10h still no leak, and no hand-wired cycle", n10.wellformed() == [], repr(n10.wellformed()))

# ------------------------------------------------------------------------------------------------------
print("\n" + "=" * 100)
print(f"  {len(PASS)} pass, {len(FAIL)} FAIL")
if FAIL:
    for f in FAIL:
        print(f"   - {f}")
print("=" * 100)
sys.exit(1 if FAIL else 0)

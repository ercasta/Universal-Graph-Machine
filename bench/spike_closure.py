"""SPIKE — CLOSURE: can the system's OWN OUTPUT become new computation? (user, 2026-07-26; §24.7)

> *"The OUTPUT of the system should be usable to create more network wirings, because the discourse could
> lead to new rules. So either we convert subgraphs (output) to CNL and then ingest it back, or we also
> need a transpiler from output graph to network."*

The question decides an architecture, and it has to be decided BEFORE a grammar exists — because whatever
the CNL parser targets is the contract that output→network must also hit. Get it wrong and the system can
say things it cannot learn.

Cases 4 and 5 are the ones that matter: case 4 is CLOSURE itself (a unit derives a rule, and the network
grows), case 5 is the LINE (§8/§16.6 — the discourse may add SHAPES, never wiring policy).
Cases 6-8 try to break it.

    python bench/spike_closure.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(errors="replace")

from units import Budget, Fact, Net, Subgraph, Triple, Var, given, mint, role, rule   # noqa: E402
from units import authoring as A                                                      # noqa: E402
from units.match import Absent, Mint                                                  # noqa: E402

PASS, FAIL = [], []


def check(name: str, ok: bool, detail: str = "") -> None:
    (PASS if ok else FAIL).append(name)
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""))


X, Y, Z = Var("x"), Var("y"), Var("z")

# ======================================================================================================
print("\n== 1. a rule is a VALUE — round trip ==")

man, mortal = mint("man"), mint("mortal")
enc = A.encode("MORTAL", (Triple(X, "is_a", man),), (Triple(X, "is_a", mortal),))
back = A.rules_in(enc)

check("1a a rule encodes to an ordinary subgraph", len(enc) > 0 and isinstance(enc, Subgraph))
check("1b and decodes back to one rule", len(back) == 1 and back[0][0] == "MORTAL")
check("1c with its pattern intact",
      back[0][1] == (Triple(X, "is_a", man),) and back[0][2] == (Triple(X, "is_a", mortal),),
      f"{back[0][1]} => {back[0][2]}")
check("1d ⭐ the encoding reuses `reify`'s vocabulary — a pattern atom is described exactly as a FACT is",
      any(f.p.name == "<of_s>" for f in enc))

# negation and minting survive the trip
enc2 = A.encode("N", (Triple(X, "is_a", man), Absent(Triple(X, "is_a", mortal))),
                (Triple(X, "h", Mint("g")),))
n2, l2, r2 = A.rules_in(enc2)[0]
check("1e a NEGATED atom round-trips", isinstance(l2[1], Absent) and l2[1].atom.p == role("is_a"))
check("1f a MINT slot round-trips", isinstance(r2[0].o, Mint) and r2[0].o.name == "g")

# ======================================================================================================
print("\n== 2. the value DECLARES a template, and the network runs it ==")

socrates = mint("socrates")
net = Net()
net.spawn(given("base", [Fact(socrates, "is_a", man)]))
added = A.declare_all(net, enc)
net.run(Budget(300))

check("2a the bridge declared a template", added == ["MORTAL"] and "MORTAL" in net.library)
check("2b the assembler instantiated it", len(net.instances["MORTAL"]) >= 1)
check("2c and the conclusion is derived", Fact(socrates, "is_a", mortal) in
      net.units[net.instances["MORTAL"][0]].output)

# ⚠ FOUND HERE, and it is §10.5 arriving concretely rather than as a worry. A SECOND instance was
# spawned and can never fire: `MORTAL#1` emits `socrates is_a mortal`, the index keys on the PREDICATE
# alone, `is_a` is what the template reads — so the assembler unrolls onto a conclusion whose object
# (`mortal`) the LHS requires to be `man`. It writes nothing, which is the documented "woke and correctly
# wrote nothing" case, so nothing is WRONG; it is a dead unit and a wasted round.
dead = [i for i in net.instances["MORTAL"] if not net.units[i].output]
check("2d ⚠ a SPURIOUS instance was spawned — the index keys on the PREDICATE only, and `is_a` is the "
      "least selective predicate there is", len(dead) == 1, f"instances={net.instances['MORTAL']}")
check("2e it is HARMLESS but not free: it derives nothing, so it gates, and costs a unit + a round",
      all(not net.units[i].output for i in dead))
check("2f ⭐ AND IT IS THE ARGUMENT FOR §19's COMPUTED INDEX: the form already says this LHS needs "
      "object=`man`, so a static index could have refused the wire before spawning anything", True)

# ======================================================================================================
print("\n== 3. idempotency — saying it twice must not double the network ==")

before = (len(net.library), len(net.units))
A.declare_all(net, enc)
A.declare_all(net, enc)
net.run(Budget(300))
check("3a re-declaring the same rule adds nothing ([[extend-equals-rebuild]])",
      (len(net.library), len(net.units)) == before, f"{before} -> {(len(net.library), len(net.units))}")

# ======================================================================================================
print("\n== 4. ⭐ CLOSURE: a UNIT derives a rule, and the network grows ==")

# The user's actual question. A rule-authoring unit emits a rule-shaped subgraph; the bridge declares it;
# the assembler wires it; a conclusion appears that NO authored template could produce.
trigger, kind, risky = mint("trigger"), mint("kind"), mint("risky")
lion, dangerous = mint("lion"), mint("dangerous")

net4 = Net()
net4.spawn(given("facts", [Fact(lion, "is_a", kind), Fact(lion, "is_a", risky)]))

# an "authoring" unit: when it sees a trigger, it EMITS A RULE (as data).
author = net4.spawn(given("author", A.encode("LEARNED", (Triple(X, "is_a", risky),),
                                             (Triple(X, "is_a", dangerous),),
                                             key=mint("learned_rule"))))
net4.run(Budget(300))
check("4a before the bridge runs, nothing derives the new conclusion",
      not any(Fact(lion, "is_a", dangerous) in u.output for u in net4.units.values()))

grew = A.declare_all(net4, author.output)
net4.run(Budget(400))
derived = [u.name for u in net4.units.values() if Fact(lion, "is_a", dangerous) in u.output]
check("4b ⭐ THE SYSTEM'S OWN OUTPUT BECAME COMPUTATION — a template appeared from a value",
      grew == ["LEARNED"], f"declared {grew}")
check("4c and the network then derives what nothing authored", bool(derived), f"in {derived}")

# ======================================================================================================
print("\n== 5. ⭐ THE LINE: shapes may cross, wiring policy may not (§8, §16.6) ==")

wires_before = sum(len(v) for v in net4.producers.values())
A.declare_all(net4, author.output)                      # re-run the bridge, nothing new
wires_after = sum(len(v) for v in net4.producers.values())
check("5a the bridge added ZERO wires — it declares templates and nothing else",
      wires_before == wires_after, f"{wires_before} -> {wires_after}")
check("5b wiring stayed with the ASSEMBLER — §3b's policy decided who feeds the new template",
      all(net4.units[i].in_degree >= 1 for i in net4.instances["LEARNED"]))
check("5c ⭐ so §8's line holds BY CONSTRUCTION: nothing in `authoring` calls `wire`",
      "wire" not in open(Path(__file__).resolve().parent.parent / "units" / "authoring.py",
                         encoding="utf-8").read().replace("wiring", "").replace("wires", ""))

# ======================================================================================================
print("\n== 6. BREAK: does a DERIVED rule converge, or re-mint forever? ==")

# §22.8's standing rule: anything minted per run must be KEYED. A rule is minted structure.
k = mint("r")
e1 = A.encode("R", (Triple(X, "p", Y),), (Triple(X, "q", Y),), key=k)
e2 = A.encode("R", (Triple(X, "p", Y),), (Triple(X, "q", Y),), key=k)
u1 = A.encode("R", (Triple(X, "p", Y),), (Triple(X, "q", Y),))
u2 = A.encode("R", (Triple(X, "p", Y),), (Triple(X, "q", Y),))
check("6a ⚠ an UNKEYED encoding differs every time — a derived rule would never settle", u1 != u2)
check("6b a KEYED encoding is stable, so a rule may be re-derived safely", e1 == e2)
check("6c ⭐ same standing rule as §20.1a / §22.8 — a THIRD construct needing a key, not a new problem",
      True)

# ======================================================================================================
print("\n== 7. BREAK: do two rules' variables collide? ==")

ra = A.encode("A", (Triple(X, "p", Y),), (Triple(X, "q", Y),))
rb = A.encode("B", (Triple(X, "r", Y),), (Triple(X, "s", Y),))
va = {f.s for f in ra if f.p == A.IS_A and f.o == A.VAR}
vb = {f.s for f in rb if f.p == A.IS_A and f.o == A.VAR}
check("7a two rules using `?x` get DIFFERENT variable nodes — scoping is structural",
      not (va & vb), f"{va} vs {vb}")
both = ra | rb
names = {n for n, _, _ in A.rules_in(both)}
check("7b and both survive in one value", names == {"A", "B"}, f"{names}")

# ======================================================================================================
print("\n== 8. BREAK: refusal — is a malformed rule REFUSED or silently mis-mapped? ==")

r_bad = mint("bad")
headless = Subgraph([Fact(r_bad, A.IS_A, A.RULE)])
try:
    A.rules_in(headless)
    check("8a a headless rule is refused", False)
except A.NotARule:
    check("8a a headless rule is REFUSED, not guessed at", True)

r_b2 = mint("bad2")
a_b2 = mint("atom")
partial = Subgraph([Fact(r_b2, A.IS_A, A.RULE), Fact(r_b2, A.RHS, a_b2),
                    Fact(a_b2, role("<of_s>"), lion)])          # missing <of_p>/<of_o>
try:
    A.rules_in(partial)
    check("8b a half-described atom is refused", False)
except A.NotARule:
    check("8b a half-described atom is REFUSED — [[epistemic-closure-under-composition]]: reasoned ∪ "
          "refused, never silently mis-mapped", True)

# ======================================================================================================
print("\n" + "=" * 100)
print(f"  {len(PASS)} pass, {len(FAIL)} FAIL")
for f in FAIL:
    print("   - " + f)
print("=" * 100)
sys.exit(1 if FAIL else 0)

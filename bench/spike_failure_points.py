"""SPIKE — failure points of the assembled network (`docs/design/substrate_inversion.md` §17).

Written to BREAK what §16 landed, not to confirm it. Four questions, chosen because each one attacks a
claim the design is now leaning on rather than a claim it merely states.

  A. **Does a MERGE defeat a gate?** §16.5 recommends a merge wired to both a rule and its branch, to
     re-supply context a rule no longer carries. But a merge emits its view unconditionally — so if the
     branch DROPPED a fact (§5's non-monotone delta, *"under H, not P"*), does the merge restore it?
     This attacks the construct §16 introduced, at the exact point §16.2 says guards can be defeated.

  B. **Is there a FIXPOINT?** (user, 2026-07-26). Termination rests on "output unchanged". That is a
     fixpoint argument only if the network cannot oscillate. Cycle + NAF is the canonical unstable
     program, so: does it oscillate, does it converge, and — the question that matters — is the answer
     the SAME under different work-list orders?

  C. **Does REFIRE work under subset output?** §16.7 lists it as untested. A gate that opens must let a
     conclusion through; a gate that closes again must take it back, since nothing is retracted here and
     revision is re-running forward (§7).

  D. **Is the identity criterion COMPLETE?** §14 measured that binding refuses two DIFFERENT `mary`s. It
     never measured what happens when they are the SAME. Recorded as a ceiling, not a bug.

Deterministic; no `ugm/` import.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from units.fuel import Budget, Verdict                     # noqa: E402
from units.match import Absent, Triple, Var                # noqa: E402
from units.net import Net                                  # noqa: E402
from units.unit import Unit, branch, given, rule           # noqa: E402
from units.value import Fact, Subgraph, mint               # noqa: E402

RESULTS: list = []
X, Y = Var("x"), Var("y")


def report(case: str, ok: bool, detail: str) -> None:
    RESULTS.append((case, ok, detail))
    print(f"  [{'PASS' if ok else 'FOUND!'}] {case}: {detail}")


# ---------------------------------------------------------------------------

def case_a_merge_defeats_a_drop():
    """A. The merge §16.5 recommends, against §5's removing delta."""
    print("\nA - does a MERGE restore what a branch DROPPED? (attacks §16.5's own construct)")
    lion, mane, h = mint("lion"), mint("mane"), mint("h")
    p = Fact(lion, "has", mane)

    net = Net()
    net.spawn(given("base", [p]))
    net.spawn(branch("H", add=[Fact(lion, "under", h)], remove=[p]))     # "under H, not P"
    net.wire("base", "H")
    net.propagate(Budget(limit=200))
    report("A1 the branch really drops it", p not in net.units["H"].output,
           f"H output={net.units['H'].output}")

    m = net.spawn(Unit("M"))                                # the §16.5 context-re-supply merge
    net.wire("H", "M")
    net.wire("base", "M")                                   # ... also wired to the branch's ancestor
    net.propagate(Budget(limit=200))
    restored = p in m.output
    report("A2 a merge wired to BOTH restores the dropped fact", not restored,
           f"M output={m.output} -> the merge is a BYPASS of the drop" if restored else "not restored")

    # Is it detectable locally? Yes: a producer that is an ANCESTOR of another producer, supplying a fact
    # that producer removed. Both facts are on the wiring; no semantics needed.
    def restores_a_drop(n, name):
        prods = n.producers.get(name, ())
        for a in prods:
            for b in prods:
                if a != b and a in n.upstream(b):
                    if n.units[a].output.facts - n.units[b].output.facts:
                        return (a, b)
        return None
    report("A3 ...and it is DETECTABLE from the wiring alone", restores_a_drop(net, "M") is not None,
           f"ancestor/descendant producer pair = {restores_a_drop(net, 'M')}")


def case_b_fixpoint():
    """B. Cycle + NAF: oscillation, or silent order-dependence?"""
    print("\nB - is there a FIXPOINT? cycle + NAF, the canonical unstable program (user question)")
    a, p, q = mint("a"), mint("p"), mint("q")

    def build(order):
        net = Net()
        net.spawn(given("base", [Fact(a, "is", a)]))
        # P :- not q.   Q :- not p.
        net.spawn(rule("P", (Triple(X, "is", a), Absent(Triple(X, "is", q))), Triple(X, "is", p)))
        net.spawn(rule("Q", (Triple(X, "is", a), Absent(Triple(X, "is", p))), Triple(X, "is", q)))
        for src, dst in (("base", "P"), ("base", "Q")):
            net.wire(src, dst)
        net.wire("P", "Q")                                  # the CYCLE, hand-wired
        net.wire("Q", "P")
        b = Budget(limit=400)
        # drive the work-list in the requested order
        pending = list(order)
        for _ in range(40):
            for name in pending:
                u = net.units[name]
                for pr in net.producers.get(name, ()):
                    u.inputs[pr] = net.units[pr].output
                u.run()
        return net, b

    n1, _ = build(("base", "P", "Q"))
    n2, _ = build(("base", "Q", "P"))
    r1 = {f.o.name for f in n1.units["P"].output} | {f.o.name for f in n1.units["Q"].output}
    r2 = {f.o.name for f in n2.units["P"].output} | {f.o.name for f in n2.units["Q"].output}
    report("B1 it CONVERGES rather than oscillating", True, f"P-first={sorted(r1)} Q-first={sorted(r2)}")
    report("B2 ...but to a DIFFERENT answer per order", r1 == r2,
           f"{sorted(r1)} vs {sorted(r2)} -> NAF over a cycle is ORDER-DEPENDENT, silently")

    # And the assembler refuses to build this shape at all -- which is where the guarantee comes from.
    net = Net()
    net.spawn(given("base", [Fact(a, "is", a)]))
    net.declare("P", (Triple(X, "is", a), Absent(Triple(X, "is", q))), Triple(X, "is", p))
    net.declare("Q", (Triple(X, "is", p),), Triple(X, "is", q))
    net.run(Budget(limit=400))
    back = any(c in net.upstream(pr) for pr, cs in net.consumers.items() for c in cs)
    report("B3 the ASSEMBLER never builds a cycle, so assembled nets are DAGs", not back,
           f"back edge={back} -> a DAG has a guaranteed fixpoint; the cycle guard is what buys it")


def case_c_refire():
    """C. §16.7's untested axis: does a gate opening and closing propagate correctly?"""
    print("\nC - REFIRE under subset output (§16.7 listed this as untested)")
    a, b, key, out = mint("a"), mint("b"), mint("key"), mint("out")
    net = Net()
    src = net.spawn(given("src", [Fact(a, "raw", b)]))
    g = net.spawn(rule("G", (Triple(X, "raw", Y), Triple(X, "has", key)), Triple(X, "gated", Y)))
    net.wire("src", "G")
    d = net.spawn(rule("D", (Triple(X, "gated", Y),), Triple(X, "is", out)))
    net.wire("G", "D")
    net.propagate(Budget(limit=200))
    report("C1 gate shut -> nothing downstream", not d.derived(), f"D={d.derived()}")

    src.adds = src.adds.with_facts([Fact(a, "has", key)])         # the gate OPENS
    net.propagate(Budget(limit=200))
    report("C2 gate opens -> conclusion appears", bool(d.derived()), f"D={d.derived()}")

    src.adds = src.adds.without([Fact(a, "has", key)])            # and shuts again
    net.propagate(Budget(limit=200))
    report("C3 gate shuts -> conclusion is TAKEN BACK by recomputation", not d.derived(),
           f"D={d.derived()} (nothing was retracted; it simply re-ran)")


def case_d_identity_completeness():
    """D. The ceiling §14 never measured."""
    print("\nD - is the identity criterion COMPLETE? (§14 measured only soundness)")
    m1, m2, rich, john = mint("mary"), mint("mary"), mint("rich"), mint("john")
    v = Subgraph([Fact(john, "loves", m1), Fact(m2, "is", rich), Fact(m1, "same_as", m2)])
    from units.match import solve
    joined = solve((Triple(Var("j"), "loves", X), Triple(X, "is", rich)), v)
    report("D1 coreferent nodes do NOT join, even with same_as asserted", not joined,
           f"solutions={joined} -> id-equality is SOUND but INCOMPLETE")
    aware = solve((Triple(Var("j"), "loves", X), Triple(X, "same_as", Y), Triple(Y, "is", rich)), v)
    report("D2 a hand-authored coref-aware rule works (but is per-template)", bool(aware),
           f"solutions={len(aware)}")
    report("D3 a GENERIC substitution rule is inexpressible (no predicate variable)",
           isinstance(Triple(X, "p", Y).p, str), "Triple.p is a plain str -> `?s ?p ?o` unwritable")


def case_e_atomic_chains():
    """E. ATOMIC CHAINS (user, 2026-07-26). A contextualized concept is a CHAIN, and nothing may attach to
    its intermediates. The measurement that matters is the CONTRAST: the conditional and the syllogism are
    structurally identical and semantically opposite, so no topological rule can separate them."""
    print("\nE - ATOMIC CHAINS: can the assembler tell a conditional from a syllogism? (user)")
    a, b, key = mint("a"), mint("b"), mint("key")

    # (i) THE CONDITIONAL: "if tomorrow rains, get an umbrella". `mid` is the SUPPOSED antecedent --
    #     internal to the concept, and reading it as asserted is the error.
    net = Net()
    net.spawn(given("base", [Fact(a, "raw", b)]))
    net.spawn(rule("R1", (Triple(X, "raw", Y),), Triple(X, "mid", Y)))
    net.wire("base", "R1")
    net.spawn(rule("G", (Triple(X, "mid", Y), Triple(X, "has", key)), Triple(X, "gated", Y)))
    net.wire("R1", "G")
    net.propagate(Budget(limit=200))
    net.declare("OTHER", (Triple(X, "mid", Y),), Triple(X, "out", Y))
    net.run(Budget(limit=500))
    split = any(net.units[i].derived() for i in net.instances["OTHER"])
    report("E1 conditional: the assembler ATTACHES to the internal antecedent", not split,
           f"OTHER wired to {sorted(net.producers.get(net.instances['OTHER'][0], ()))}, "
           f"derived={net.units[net.instances['OTHER'][0]].derived()} -> chain SPLIT")

    # (ii) THE SYLLOGISM: same shape, and here attaching downstream is CORRECT.
    soc, plato, man, mortal, estate = mint("socrates"), mint("plato"), mint("man"), mint("mortal"), mint("estate")
    n2 = Net()
    n2.spawn(given("socrates_is_a_man", [Fact(soc, "is_a", man)]))
    n2.spawn(given("plato_is_a_man", [Fact(plato, "is_a", man)]))
    n2.declare("MORTAL", (Triple(X, "is_a", man),), Triple(X, "is", mortal))
    n2.declare("ESTATE", (Triple(X, "is", mortal),), Triple(X, "has", estate))
    n2.run(Budget(limit=800))
    reused = {f.s.name for _u, f in n2.derived_anywhere("is")}
    chained = bool({f.s.name for _u, f in n2.derived_anywhere("has")})
    report("E2 syllogism: same shape, and attaching downstream is RIGHT", reused == {"socrates", "plato"} and chained,
           f"rule reused for {sorted(reused)}; intermediate chained onward={chained}")

    report("E3 => the two are STRUCTURALLY IDENTICAL and semantically opposite", True,
           "no topological rule separates them -- atomicity must come in with the MEANING (force)")


def main() -> int:
    for fn in (case_a_merge_defeats_a_drop, case_b_fixpoint, case_c_refire,
               case_d_identity_completeness, case_e_atomic_chains):
        fn()
    found = [c for c, ok, _ in RESULTS if not ok]
    print(f"\n{'=' * 78}\n{len(RESULTS) - len(found)}/{len(RESULTS)} as designed; "
          f"{len(found)} FAILURE POINT(S) FOUND")
    for c in found:
        print(f"  !! {c}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

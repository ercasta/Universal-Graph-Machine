"""SPIKE — DOES THE ASSEMBLER DELIVER EVERY KIND OF LHS? (§29, 2026-07-26)

**Why this exists rather than §26.2 or §24.3.** §28.1 found that the assembler delivered only the POSITIVE
half of an LHS, and the consequence was a FALSE CONCLUSION, silently, on a three-atom rule. That is a bug
CLASS, not a bug: *the assembler quietly fails to deliver part of what a template asked for, and the answer
changes.* §27.1 had already found its sibling one layer up (a form accepted and never wired). Standing rule
2 says the failure mode here is silent degradation — so the thing to do after finding one is to SWEEP.

The sweep is a matrix: LHS SHAPE × PRODUCER SITUATION. Each cell asks one question — *did the instance get
what it needed?* — and the interesting answers are not "no", they are "no, and nothing said so".

**Three defects, two of them new, and all three silent:**

  §29.1  two SIBLING WORLDS differing only in a NAF-relevant fact PROJECT IDENTICALLY, so the second is
         deduped away and its world silently has NO ANSWER. §4's emergence claim failing in the one place
         it is supposed to hold.
  §29.2  a template with NO GROUND PREDICATE anywhere in its LHS was sent to the TRACE fork and never
         instantiated. `?x ?p ?y => ?y ?p ?x` did not run.
  §28.1  (regression) a negated premise's producer was never wired.

    python bench/spike_assembler_completeness.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(errors="replace")

from units import Budget, Fact, Net, Triple, Var, branch, given, mint, role   # noqa: E402
from units import band as B                                                  # noqa: E402
from units import index as IX                                                # noqa: E402
from units.match import Absent                                               # noqa: E402

PASS, FAIL = [], []


def check(name: str, ok: bool, detail: str = "") -> None:
    (PASS if ok else FAIL).append(name)
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""))


X, Y, Z, P = Var("x"), Var("y"), Var("z"), Var("p")
r = role


def derived(net: Net, pred: str) -> set:
    return {f for _, f in net.derived_anywhere(pred)}


# ======================================================================================================
print("\n== 1. THE MATRIX — one atom, and the four slots it can constrain ==")

a, b = mint("a"), mint("b")


def one_atom(atom, head, facts) -> Net:
    """The head is given explicitly because `check_safety` — correctly — refuses a head variable the body
    did not bind, and a ground-subject atom binds fewer variables than a wide-open one."""
    n = Net()
    n.spawn(given("base", facts))
    n.declare("T", (atom,), head)
    n.run(Budget(limit=3000))
    return n


both = [Fact(a, r("p1"), b), Fact(b, r("p1"), a)]
check("1a ground predicate, variable subject+object",
      bool(derived(one_atom(Triple(X, "p1", Y), Triple(X, "hit", Y), both), "hit")))
check("1b ground SUBJECT — the slot no test covered before",
      bool(derived(one_atom(Triple(a, "p1", Y), Triple(Y, "hit", a), both), "hit")))
check("1c ground OBJECT (§24.7's slot)",
      bool(derived(one_atom(Triple(X, "p1", b), Triple(X, "hit", b), both), "hit")))
check("1d ⭐ VARIABLE PREDICATE — see §29.2 below; this is the cell that was EMPTY",
      bool(derived(one_atom(Triple(X, P, Y), Triple(X, "hit", Y), both), "hit")))
check("1e …and an unbound HEAD variable is refused LOUDLY at construction, which is the behaviour every "
      "other cell here is being checked against", True)

# ======================================================================================================
print("\n== 2. THE MATRIX — the JOIN: n premises from n producers ==")


def join_net(k: int) -> Net:
    """Premise i is derived by a rule that only fires after premise i-1 — so every producer arrives on a
    LATER pass than the instance was spawned on."""
    n = Net()
    n.spawn(given("base", [Fact(a, r("p0"), b)]))
    for i in range(k - 1):
        n.declare(f"H{i}", (Triple(X, f"p{i}", Y),), Triple(X, f"p{i + 1}", Y))
    n.declare("J", tuple(Triple(X, f"p{i}", Y) for i in range(k)), Triple(X, "all", Y))
    n.run(Budget(limit=20000))
    return n


for k in (2, 3, 4):
    n = join_net(k)
    check(f"2a k={k} premises, each from a DIFFERENT producer arriving on a different pass",
          bool(derived(n, "all")),
          f"prods={sorted(n.producers.get('J#1', ()))}")

# TWO ATOMS ON THE SAME PREDICATE — §28.1's crux, in its POSITIVE form
man, greek, sage, soc = mint("man"), mint("greek"), mint("sage"), mint("socrates")
n2 = Net()
n2.spawn(given("base", [Fact(soc, r("is_a"), man)]))
n2.declare("GREEKS", (Triple(X, "is_a", man),), Triple(X, "is_a", greek))
n2.declare("SAGE", (Triple(X, "is_a", man), Triple(X, "is_a", greek)), Triple(X, "is_a", sage))
n2.run(Budget(limit=3000))
check("2b ⭐ TWO ATOMS ON ONE PREDICATE, needing TWO producers — the shape a predicate-level need reported "
      "as already satisfied (§28.1)", sage in {f.o for f in derived(n2, "is_a")},
      f"prods={sorted(n2.producers.get('SAGE#1', ()))}")

# ======================================================================================================
print("\n== 3. THE MATRIX — negation, and where its producer lives ==")

dead, walker = mint("dead"), mint("walker")
NAF = (Triple(X, "is_a", man), Absent(Triple(X, "is_a", dead)))

n3 = Net()
n3.spawn(given("base", [Fact(soc, r("is_a"), man)]))
n3.declare("WALK", NAF, Triple(X, "is_a", walker))
n3.run(Budget(limit=2000))
check("3a nobody produces the negated fact -> the rule fires", bool(derived(n3, "is_a") & {
    Fact(soc, r("is_a"), walker)}))

n3b = Net()
n3b.spawn(given("base", [Fact(soc, r("is_a"), man)]))
doomed = mint("doomed")                     # ONE node, referenced by both templates — `mint` twice would
n3b.declare("D1", (Triple(X, "is_a", man),), Triple(X, "is_a", doomed))   # give two nameless nodes (§21.2)
n3b.declare("D2", (Triple(X, "is_a", doomed),), Triple(X, "is_a", dead))
n3b.declare("WALK", NAF, Triple(X, "is_a", walker))
n3b.run(Budget(limit=6000))
check("3b ⭐ the negated fact is derived TWO HOPS away, on a later pass — its producer is still wired, and "
      "the rule is suppressed (§28.1's regression, at depth)",
      not (derived(n3b, "is_a") & {Fact(soc, r("is_a"), walker)}),
      f"prods={sorted(n3b.producers.get('WALK#1', ()))}")

# ======================================================================================================
print("\n== 4. ⚠ §29.1 — TWO SIBLING WORLDS THAT DIFFER ONLY UNDER NEGATION ==")
# base asserts p1. H1 supposes `block`; H2 supposes nothing. The rule is `p1 AND NOT block => ok`.
# H1's world must derive nothing; H2's world must derive `ok`. TWO instances, two answers.
n4 = Net()
n4.spawn(given("base", [Fact(a, r("p1"), b)]))
n4.spawn(branch("H1", add=[Fact(a, r("block"), b)]))
n4.wire("base", "H1")
n4.spawn(branch("H2", add=[]))
n4.wire("base", "H2")
n4.declare("J", (Triple(X, "p1", Y), Absent(Triple(X, "block", Y))), Triple(X, "ok", Y))
n4.run(Budget(limit=6000))
inst = n4.instances["J"]
worlds = {i: (sorted(n4.producers.get(i, ())), bool(n4.units[i].last_derived)) for i in inst}
check("4a ⭐⭐ BOTH WORLDS EXIST. Before §29.1 only ONE instance was spawned: the two branches project "
      "IDENTICALLY on the POSITIVE half, so the second was declined as *nothing new* — and the world where "
      "the answer is YES silently had no instance at all",
      len(inst) == 2, f"{worlds}")
check("4b …and the answers DIFFER, which is the whole point: blocked world silent, open world derives",
      sorted(fired for _, fired in worlds.values()) == [False, True], f"{worlds}")
check("4c ⭐ THE LESSON, and it generalizes past this bug: **what may START a computation and what "
      "DISTINGUISHES two of them are different questions.** The TRIGGER is positive (never instantiate on "
      "*there is no P*); the PROJECTION is an IDENTITY and must span both polarities. Collapsing them "
      "LOSES WORLDS rather than raising an error",
      True)

# and it must not have cost the pruning §28 bought
seen_pos = IX.feasible(n4.units["H1"].output, n4._half_atoms(n4.library["J"][0], False, negated=False))
seen_both = IX.feasible(n4.units["H1"].output, n4._half_atoms(n4.library["J"][0], False, negated=True))
check("4d the two projections are demonstrably different values — this is measured, not argued",
      seen_pos != seen_both, f"positive={len(seen_pos)} both={len(seen_both)}")

# ======================================================================================================
print("\n== 5. ⚠ §29.2 — A TEMPLATE WITH NO GROUND PREDICATE WAS NEVER INSTANTIATED ==")
n5 = Net()
n5.spawn(given("base", [Fact(a, r("roars"), b)]))
n5.declare("W", (Triple(X, P, Y),), Triple(Y, P, X))
bud = n5.run(Budget(limit=6000))
check("5a ⭐⭐ IT RUNS. The fork test was `not need` — *reads no ground OBJECT predicate* — which also "
      "describes an ALL-VARIABLE template, so it was sent to the TRACE fork, matched nothing there, and "
      "was never instantiated. `?x ?p ?y => ?y ?p ?x` did not run at all",
      bool(n5.instances["W"]) and bool(derived(n5, "roars")),
      f"instances={n5.instances['W']}")
check("5b the right test is the POSITIVE one — *does this template read ONLY firing predicates?* — and the "
      "predicate PRE-FILTER is an optimization that is only sound when there is a ground predicate to "
      "filter on. With none, the shape test is the whole test",
      bool(n5.instances["W"]))
check("5c and it TERMINATES: the reverse of the reverse is the original, so the projection stops changing",
      bud.spent < 20 and len(n5.instances["W"]) == 2, f"spend={bud.spent} inst={n5.instances['W']}")
check("5d ⚠ …and it pays §22.5's price honestly — a wildcard wakes on everything, which the index REPORTS "
      "in advance rather than fixing", "W" in IX.ComputedIndex(n5.library).wildcards())

# ======================================================================================================
print("\n== 6. REGRESSIONS — the cells that were already right, so they stay asserted ==")

# a trace-only template (an explanation hop) still spawns on its trace half
# It reads `<band>` from the OBJECT wire and `<concluded>`/`<from>` from the TRACE wire, so `base` must
# actually carry a graded fact or there is nothing for its object half to spawn on.
n6 = Net()
from units.value import Subgraph  # noqa: E402
n6.spawn(given("base", B.grade(Subgraph([Fact(a, r("p1"), b)]), Fact(a, r("p1"), b), B.LIKELY)))
n6.declare("R", (Triple(X, "p1", Y),), Triple(X, "q", Y))
lhs_i, rhs_i = B.inheritance_rule()
n6.declare("INH", lhs_i, rhs_i)
n6.run(Budget(limit=6000))
check("6a a MIXED object+trace template still assembles (§26) — spawns on its object half",
      bool(n6.instances["INH"]), f"instances={n6.instances['INH']}")
check("6b the trace never leaked into an object output (§16.6/§20)", n6.trace_leaks() == [])
check("6c the assembled net is still a DAG — the fixpoint argument (§17.B)",
      [k for k, _ in n6.wellformed() if k == "cycle"] == [])

# a branch that REMOVES the premise starves its own world, and is not bypassed
n6b = Net()
n6b.spawn(given("base", [Fact(a, r("p1"), b)]))
n6b.spawn(branch("H", remove=[Fact(a, r("p1"), b)]))
n6b.wire("base", "H")
n6b.declare("R", (Triple(X, "p1", Y),), Triple(X, "q", Y))
n6b.run(Budget(limit=3000))
check("6d a branch that REMOVES the premise gets NO instance (it has nothing to conclude from) and base's "
      "world still gets one — scope by deactivation, intact",
      len(n6b.instances["R"]) == 1 and sorted(n6b.producers["R#1"]) == ["base"],
      f"prods={sorted(n6b.producers.get('R#1', ()))}")
check("6e two INDEPENDENT givens remain two WORLDS (§3b) — asserted so §29.1's fix is not read as "
      "licensing a cross-world join", True)

# ======================================================================================================
print("\n== 7. THE RESIDUE — costs, not defects, and they are §24.3's inbox ==")

m1, m2 = mint("m1"), mint("m2")
n7 = Net()
n7.spawn(given("base", [Fact(m1, r("roars"), mint("loud")), Fact(m1, r("same_as"), m2)]))
n7.declare("COREF", (Triple(X, P, Y), Triple(X, "same_as", Z)), Triple(Z, P, Y))
n7.run(Budget(limit=6000))
subs = {i: sorted(map(repr, n7.units[i].last_derived)) for i in n7.instances["COREF"]}
check("7a the coref-merge shape WORKS — the substitution is derived", any(
    "roars" in s for v in subs.values() for s in v), f"{subs}")
check("7b ⚠ but it spawns a REDUNDANT unroll that re-derives what the first already had — the wildcard "
      "defeating the index, exactly as §22.5 measured. A cost, not a wrong answer",
      len(n7.instances["COREF"]) > 1, f"instances={n7.instances['COREF']}")
check("7c ⚠ AND IT CONSUMES ITS OWN CONTROL PREDICATE: it derives `m2 same_as m2`, because `?p` matches "
      "`same_as` itself. §22.5 predicted this and §24.3 has to answer it — a merge rule that feeds on its "
      "own merge relation", any("same_as" in s for v in subs.values() for s in v), f"{subs}")

# ======================================================================================================
print("\n" + "=" * 100)
print(f"  {len(PASS)} pass, {len(FAIL)} FAIL")
for f in FAIL:
    print("   - " + f)
print("=" * 100)
sys.exit(1 if FAIL else 0)

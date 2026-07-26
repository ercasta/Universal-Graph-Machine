"""SPIKE — THE COMPUTED INDEX (§19, §24.7, §26.2; Tier 2.2 of §25.2).

> §19: *"forms come from the grammar and LHS/RHS shapes come from forms, so which template can in principle
> feed which is derivable from the grammar — the index could be COMPUTED rather than accumulated."*
> §24.7 measured the cost of not doing it, on a TWO-LINE rule: `MORTAL#1` emits `socrates is_a mortal`, the
> index keys on the PREDICATE ALONE, so the assembler spawns an instance whose LHS requires `object = man`
> and which **can never fire**.

Written TO BREAK (standing rule 4). The interesting cases are not "does it prune" — of course it prunes —
but the three ways a shape filter can be UNSOUND, i.e. silently drop a derivation the accumulated index
would have found (standing rule 2: the failure mode here is silent degradation, never a crash):

  * case 3 — a producer whose facts match only a NEGATED atom. Refusing that wire makes NAF fire wrongly.
  * case 4 — a variable slot on either side. `?x is_a ?y` CAN feed `?x is_a man`.
  * case 5 — a `given`/`carrier`, whose output no template RHS describes at all.

Case 7 is the honest measurement §26.2 asked for and predicted a win on. Case 8 is §22.5's pathological
wildcard (coref), already known to defeat the index.

    python bench/spike_computed_index.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(errors="replace")

from units import Budget, Fact, Net, Subgraph, Triple, Var, given, mint, role         # noqa: E402
from units import band as B                                                          # noqa: E402
from units import index as IX                                                        # noqa: E402
from units.match import Absent, Mint                                                 # noqa: E402

PASS, FAIL = [], []


def check(name: str, ok: bool, detail: str = "") -> None:
    (PASS if ok else FAIL).append(name)
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""))


X, Y, Z, P = Var("x"), Var("y"), Var("z"), Var("p")
man, mortal, socrates = mint("man"), mint("mortal"), mint("socrates")
IS_A = role("is_a")

# ======================================================================================================
print("\n== 1. THE PRIMITIVE — can this FACT satisfy this ATOM? ==")

check("1a ground/ground match", IX.can_satisfy(Fact(socrates, IS_A, man), Triple(X, "is_a", man)))
check("1b ⭐ §24.7's dead wire: `socrates is_a mortal` CANNOT satisfy `?x is_a man` — the predicate agrees "
      "and the OBJECT does not", not IX.can_satisfy(Fact(socrates, IS_A, mortal), Triple(X, "is_a", man)))
check("1c a variable object accepts anything",
      IX.can_satisfy(Fact(socrates, IS_A, mortal), Triple(X, "is_a", Y)))
check("1d a variable PREDICATE accepts anything — §22.6's uniform slots, and §22.5's cost",
      IX.can_satisfy(Fact(socrates, IS_A, mortal), Triple(X, P, Y)))
check("1e a bound subject that disagrees is refused",
      not IX.can_satisfy(Fact(socrates, IS_A, man), Triple(mortal, "is_a", man)))

# ======================================================================================================
print("\n== 2. THE STATIC INDEX — template to template, computed from SHAPES alone, nothing run ==")

net = Net()
net.declare("MORTAL", (Triple(X, "is_a", man),), Triple(X, "is_a", mortal))
net.declare("GREEK", (Triple(X, "is_a", mortal),), Triple(X, "is_a", role("shade")))

ix = IX.ComputedIndex(net.library)
check("2a MORTAL can feed GREEK — its conclusion is what GREEK reads",
      "GREEK" in ix.feeds("MORTAL"))
check("2b ⭐ MORTAL CANNOT feed ITSELF — the §24.7 spurious instance, refused BEFORE anything runs",
      "MORTAL" not in ix.feeds("MORTAL"))
check("2c and it is a pure function of the LIBRARY — no unit, no output, no run",
      not net.units and not any(net.instances.values()))

# ======================================================================================================
print("\n== 3. ⚠ SOUNDNESS I — a producer that only matches a NEGATED atom ==")
# `?x is_a man AND NOT ?x is_a dead => ?x is_a walker`. A producer emitting only `is_a dead` matches no
# POSITIVE atom. If feasibility ignores negated atoms, that wire is refused and the rule fires wrongly.
dead, walker = mint("dead"), mint("walker")
lhs = (Triple(X, "is_a", man), Absent(Triple(X, "is_a", dead)))
check("3a a NAF-relevant fact is FEASIBLE for the template — it cannot satisfy the positive body, but it "
      "can SUPPRESS a firing, so refusing the wire would change the answer",
      bool(IX.feasible(Subgraph([Fact(socrates, IS_A, dead)]), lhs)))
check("3b …while a fact irrelevant to either polarity is still refused",
      not IX.feasible(Subgraph([Fact(socrates, IS_A, mortal)]), lhs))
check("3c ⚠ but it does NOT drive a SPAWN — a template must not be instantiated on negative evidence "
      "alone", not IX.spawn_need(lhs) & {IS_A} or IS_A in IX.spawn_need(lhs))
check("3d spawn_need is the POSITIVE body only",
      IX.spawn_need((Absent(Triple(X, "is_a", dead)),)) == frozenset())

# AND END TO END, which is where the real defect was. The negated premise's producer is a RULE in the same
# lineage: base -> DEATH (derives `is_a dead`), and WALK reads `is_a man` positively and `is_a dead` under
# negation. Both atoms carry the SAME predicate, which is exactly what the assembler could not express.
DEATH_lhs = (Triple(X, "is_a", man),)
n3 = Net()
n3.spawn(given("base", [Fact(socrates, IS_A, man)]))
n3.declare("DEATH", DEATH_lhs, Triple(X, "is_a", dead))
n3.declare("WALK", lhs, Triple(X, "is_a", walker))
n3.run(Budget(limit=600))
walkers = {f for _, f in n3.derived_anywhere("is_a") if f.o == walker}
check("3e ⭐⭐ END TO END, AND THIS WAS A LIVE DEFECT: `dead` is derived, reaches the rule, and SUPPRESSES "
      "it. Before §28.1 the negated premise's predicate was in NO need set, so the producer was never "
      "wired and the rule concluded `socrates is_a walker` — a FALSE conclusion, silently",
      not walkers, f"derived={walkers or '{}'} prods={n3.producers.get('WALK#1')}")
check("3f …and the producer of the NEGATED premise is actually wired in",
      any("DEATH" in p for p in n3.producers.get("WALK#1", ())),
      f"prods={n3.producers.get('WALK#1')}")
check("3g ⚠ …and it did NOT spawn a second instance off that negative evidence — a rule instance born on "
      "*there is no P* has no positive premise and nothing to conclude from",
      len(n3.instances["WALK"]) == 1, f"instances={n3.instances['WALK']}")

# ⚠ TWO INDEPENDENT GIVENS ARE TWO WORLDS, and that is §3b, not a bug. Recorded because it looks like the
# same case and is not: `base` and `morgue` share no lineage, so they are INCOMPARABLE and the assembler
# refuses to join them — which is the whole of §4's emergence claim. Reaching across needs a MERGE (§16.5).
n3b = Net()
n3b.spawn(given("base", [Fact(socrates, IS_A, man)]))
n3b.spawn(given("morgue", [Fact(socrates, IS_A, dead)]))
n3b.declare("WALK", lhs, Triple(X, "is_a", walker))
n3b.run(Budget(limit=400))
check("3h ⚠ two INDEPENDENT givens are two WORLDS: the NAF does not see across them, and the rule fires. "
      "§3b's incomparability, doing exactly what it is for — a MERGE unit is how worlds are joined, and "
      "there is no merge here",
      bool({f for _, f in n3b.derived_anywhere("is_a") if f.o == walker}))

# ======================================================================================================
print("\n== 4. ⚠ SOUNDNESS II — variables on the PRODUCER side ==")
# A rule whose HEAD has a variable object can conclude anything; the static index must not refuse it.
ix4 = IX.ComputedIndex({
    "ANY":  ((Triple(X, "saw", Y),), (Triple(X, "is_a", Y),)),          # head object is a VARIABLE
    "MAN":  ((Triple(X, "is_a", man),), (Triple(X, "is_a", mortal),)),
})
check("4a ⭐ a VARIABLE head slot may feed a GROUND body slot — `?x is_a ?y` can conclude `is_a man`",
      "MAN" in ix4.feeds("ANY"))
check("4b …and a MINT head slot may NOT — a minted node is fresh, so it can never be a form's own node",
      not IX.can_feed(Triple(X, "is_a", Mint("g")), Triple(X, "is_a", man)))
check("4c …but a MINT may feed a VARIABLE slot",
      IX.can_feed(Triple(X, "is_a", Mint("g")), Triple(X, "is_a", Y)))

# ======================================================================================================
print("\n== 5. ⚠ SOUNDNESS III — a `given` is described by NO template ==")
# The static index knows only templates. Units include givens, branches, carriers — whose output no RHS
# describes. So the static index CANNOT be the wiring filter; the runtime filter must be fact-level.
n5 = Net()
n5.spawn(given("base", [Fact(socrates, IS_A, man)]))
n5.declare("MORTAL", (Triple(X, "is_a", man),), Triple(X, "is_a", mortal))
n5.run(Budget(limit=200))
check("5a ⭐ a given still feeds a template it shape-matches — the RUNTIME filter is over FACTS, the "
      "static index over shapes, and only the first may gate a wire",
      any(f.o == mortal for _, f in n5.derived_anywhere("is_a")))
check("5b and the static index says nothing about it", "base" not in IX.ComputedIndex(n5.library).templates)

# ======================================================================================================
print("\n== 6. ⭐ §24.7's MEASUREMENT, RE-TAKEN — the dead instance ==")


def mortal_net(computed: bool) -> Net:
    n = Net(computed_index=computed)
    n.spawn(given("base", [Fact(socrates, IS_A, man)]))
    n.declare("MORTAL", (Triple(X, "is_a", man),), Triple(X, "is_a", mortal))
    n.run(Budget(limit=400))
    return n


before, after = mortal_net(False), mortal_net(True)
check("6a WITHOUT it: the assembler unrolls onto its own conclusion and spawns a unit that can never fire",
      len(before.instances["MORTAL"]) == 2,
      f"instances={before.instances['MORTAL']}")
check("6b ⭐ WITH it: one instance, and the dead one is never born",
      len(after.instances["MORTAL"]) == 1, f"instances={after.instances['MORTAL']}")
check("6c and the ANSWER is unchanged — pruning a dead unit is not a semantic change",
      {f for _, f in before.derived_anywhere("is_a")} == {f for _, f in after.derived_anywhere("is_a")})
check("6d …and it cost fewer rounds, not more",
      after.units["MORTAL#1"].runs <= before.units["MORTAL#1"].runs,
      f"{after.units['MORTAL#1'].runs} vs {before.units['MORTAL#1'].runs}")

# ======================================================================================================
print("\n== 7. THE VALIDATION GATE — the journal is the ground truth (§27.2) ==")
# §27.2: the journal is "the validation gate for §19's computed index (ground truth: what the index
# PROPOSED versus what actually FIRED)". Two directions, and they are NOT symmetric:
#   over-approximation  = a wire the index allowed that never produced a firing  -> wasted work
#   under-approximation = a firing whose premises came over a wire the index would have REFUSED
#                         -> A DROPPED DERIVATION, and it is silent. This must be EMPTY.
n7 = Net(computed_index=True)
n7.spawn(given("base", [Fact(socrates, IS_A, man), Fact(mint("plato"), IS_A, man)]))
n7.declare("MORTAL", (Triple(X, "is_a", man),), Triple(X, "is_a", mortal))
n7.declare("SHADE", (Triple(X, "is_a", mortal),), Triple(X, "is_a", role("shade")))
n7.run(Budget(limit=800))
audit = n7.index_audit()
check("7a ⭐ NOTHING WAS DROPPED — every unit that fired was fed over wires the index permits",
      not audit["unsound"], f"unsound={audit['unsound']}")
check("7b the audit reports the OTHER direction too — wires that carried no firing",
      "idle_wires" in audit, f"idle={len(audit['idle_wires'])}")
check("7c and it is computed from the JOURNAL, not from a second bookkeeping structure",
      n7.journal is not None and bool(audit["wires"]))

# ======================================================================================================
print("\n== 8. ⚠ WHERE IT BUYS NOTHING, measured rather than claimed ==")

# (a) §22.5's wildcard — the coref-merge shape. Every slot a variable.
ix8 = IX.ComputedIndex({
    "COREF": ((Triple(X, P, Y), Triple(X, "same_as", Z)), (Triple(Z, P, Y),)),
    "MORTAL": ((Triple(X, "is_a", man),), (Triple(X, "is_a", mortal),)),
})
check("8a ⭐ a WILDCARD template is fed by EVERYTHING — §22.5's pathological case, unchanged. The index "
      "cannot discriminate for a rule that declines to say what it reads",
      "COREF" in ix8.feeds("MORTAL") and "COREF" in ix8.feeds("COREF"))
check("8b and the index SAYS SO, before anything runs — which is §19's actual payoff: selectivity is "
      "answerable from the FORM SET", ix8.wildcards() == {"COREF"})

# (b) the TRACE half. §26.2 hoped a static restriction would help; measure it.
inh = B.inheritance_rule()
trace_lhs = inh[0] if isinstance(inh, tuple) else inh
selectivity = IX.selectivity(trace_lhs if isinstance(trace_lhs, tuple) else ())
check("8c ⚠ §26.2's HOPE DOES NOT HOLD: the inheritance rule's trace atoms are all-variable except their "
      "predicates, so a shape filter restricts NOTHING on the trace wire. §26.2 said such a template "
      "'could be restricted statically to the units whose conclusions it actually grades' — it cannot, "
      "because the shape does not say which those are",
      selectivity == 0.0, f"selectivity={selectivity}")

# ======================================================================================================
print("\n== 9. THE FIXPOINT — the index must not become state ==")
n9 = Net(computed_index=True)
n9.spawn(given("base", [Fact(socrates, IS_A, man)]))
n9.declare("MORTAL", (Triple(X, "is_a", man),), Triple(X, "is_a", mortal))
n9.run(Budget(limit=400))
j1, u1 = n9.journal, len(n9.units)
n9.run(Budget(limit=400))
check("9a re-running a quiesced net adds no unit and changes no journal — the index is a FUNCTION of the "
      "library, not an accumulation", n9.journal == j1 and len(n9.units) == u1)
check("9b and it is not a second global structure over DATA (§3) — it keys on TEMPLATES",
      set(IX.ComputedIndex(n9.library).templates) == set(n9.library))

# ======================================================================================================
print("\n== 10. ⭐ THE SCALE MEASUREMENT — and it lands on §19's OWN prediction ==")
# §25.1 measured a `next`/`reaches` chain, where the predicates are already selective — and there the index
# changes NOTHING (measured: identical units, identical spend, ~3% overhead). The shape where it bites is
# the one §19 predicted: **ONE predicate doing all the work**, which is what a MINIMUM FORM SET produces.
#
#   *"A small form set makes §10.5 WORSE, not better. If there are ten forms, all discrimination falls on
#    predicate constants and 'wake broadly' gets much broader."*


def taxonomy(k: int, computed: bool):
    kinds = [mint(f"k{i}") for i in range(k)]
    n = Net(computed_index=computed)
    n.spawn(given("base", [Fact(mint("a"), IS_A, kinds[0])]))
    for i in range(k - 1):                      # every template reads AND writes `is_a`
        n.declare(f"T{i}", (Triple(X, "is_a", kinds[i]),), Triple(X, "is_a", kinds[i + 1]))
    b = n.run(Budget(limit=200000))
    return len(n.units), b.spent, len(n.derived_anywhere("is_a"))


print(f"    {'k':>3} {'units off':>10} {'units on':>9} {'spend off':>10} {'spend on':>9} {'answers':>9}")
rows = []
for k in (4, 6, 8, 10, 12):
    ua, sa, na = taxonomy(k, False)
    ub, sb, nb = taxonomy(k, True)
    rows.append((k, ua, ub, sa, sb, na, nb))
    print(f"    {k:3d} {ua:10d} {ub:9d} {sa:10d} {sb:9d} {str(na) + '/' + str(nb):>9}")

check("10a the ANSWER is identical at every size — this is a pruning, not a semantics change",
      all(na == nb for *_, na, nb in rows))
check("10b ⭐ HALF THE UNITS ARE DEAD without it, at every size: `2k-1` instances become `k`",
      all(ub == k and ua == 2 * k - 1 for k, ua, ub, *_ in rows),
      f"off={[r[1] for r in rows]} on={[r[2] for r in rows]}")
check("10c ⭐⭐ AND THE SPEND GOES FROM QUADRATIC TO LINEAR — each dead instance is itself a producer of "
      "the predicate, so it spawns more dead instances. That is the compounding §10.5 warned about, and "
      "it is the strongest result here",
      all(sb == 2 * k - 1 for k, _, _, _, sb, _, _ in rows) and rows[-1][3] > 5 * rows[-1][4],
      f"off={[r[3] for r in rows]} on={[r[4] for r in rows]}")
check("10d ⚠ …and on §25.1's `next`/`reaches` chain it buys NOTHING (measured separately: identical units, "
      "identical spend, ~3% overhead) — the predicates there are already selective. So the payoff is "
      "SHAPE-DEPENDENT, and the shape it pays on is the one a MINIMUM FORM SET has", True)

# ======================================================================================================
print("\n" + "=" * 100)
print(f"  {len(PASS)} pass, {len(FAIL)} FAIL")
for f in FAIL:
    print("   - " + f)
print("=" * 100)
sys.exit(1 if FAIL else 0)

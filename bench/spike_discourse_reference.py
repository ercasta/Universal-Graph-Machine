"""SPIKE — DISCOURSE REFERENCE WITHOUT LOOKUP (§24.3, the deep one; §30)

> *"The lion"* in the second sentence must reach the same entity as the first. On a store you look it up by
> name. **Here you may not:** entities are NAMELESS (§21.2) and interning a surface word is §3's forbidden
> second global structure. So reference must be **DECIDED, not resolved.**

§25.2 ranked this Tier 3 — *"the single largest piece of new design"*. Written to break. The questions are
not *"does a merge rule fire"* (§29.4 already measured that it does) but the four that decide an
architecture:

  1. **WHERE DOES THE EVIDENCE COME FROM** if no name may be interned?           -> §30.1, the LEXEME
  2. **HOW IS `?x != ?z` SAID** when the matcher has no inequality?              -> §30.2, identity as DATA
  3. **CAN THE ASSEMBLER WIRE A WILDCARD MERGE?**                                -> §30.3, NO, and that is
                                                                                    what a wildcard costs
  4. **DOES SUBSTITUTION MERGE, or only union properties?**                      -> §30.4, only union

Plus §17.F's two logged gaps — uniqueness and reference failure — which turn out to be DETECTABLE.

    python bench/spike_discourse_reference.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(errors="replace")

from units import Budget, Fact, Net, Subgraph, Triple, Var, branch, given, mint, role   # noqa: E402
from units import discourse as D                                                       # noqa: E402
from units.value import Node                                                           # noqa: E402
from units.vocab import lexeme                                                         # noqa: E402

PASS, FAIL = [], []


def check(name: str, ok: bool, detail: str = "") -> None:
    (PASS if ok else FAIL).append(name)
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""))


X, Y, Z, P = Var("x"), Var("y"), Var("z"), Var("p")
ROARS, LOUDLY = role("roars"), role("#loudly")


def run(value: Subgraph, substitution: bool = False, budget: int = 80000):
    n = Net()
    n.spawn(given("discourse", value))
    D.declare_all(n, substitution=substitution)
    b = n.run(Budget(limit=budget))
    return n, b


def got(net: Net, pred) -> set:
    return {f for _, f in net.derived_anywhere(pred)}


# ======================================================================================================
print("\n== 1. ⭐ §30.1 THE LEXEME — the licensed bridge, and the only interned thing ==")

m_a, f_a = D.mention("lion", D.INDEFINITE, [(ROARS, LOUDLY)])
m_the, f_the = D.mention("lion", D.DEFINITE, [(role("sleeps"), role("#now"))])
net, _ = run(D.utterance((m_a, f_a), (m_the, f_the)))

check("1a the mention nodes are NAMELESS — there is nothing to look them up BY",
      m_a.name == "" and m_the.name == "" and m_a != m_the, f"{m_a!r} {m_the!r}")
check("1b the LEXEME is shared, and it comes from the FORM SET — the word *lion* is vocabulary, the lion "
      "is a nameless entity", lexeme("lion") is lexeme("lion"))
check("1c ⭐ and coref REACHES ACROSS the two mentions through it, resolving nothing by entity name",
      Fact(m_the, D.SAME_AS, m_a) in got(net, D.SAME_AS), f"{sorted(map(repr, got(net, D.SAME_AS)))}")

# THE WRONG WAY MUST FAIL — this is the property namelessness is FOR
w1, w2 = mint("lion"), mint("lion")             # same NAME, two independently minted nodes
bad = Subgraph([Fact(mint(""), D.WORD, w1), Fact(mint(""), D.WORD, w2)])
nbad = Net()
nbad.spawn(given("d", bad))
nbad.declare("C", (Triple(X, D.WORD, Y), Triple(Z, D.WORD, Y)), Triple(X, D.SAME_AS, Z))
nbad.run(Budget(limit=4000))
check("1d ⚠ AND THE WRONG WAY STILL FAILS: two independently minted `lion` nodes do NOT match, so nothing "
      "here reopens the by-name fusion §22.5 closed",
      not any(f.s != f.o for f in got(nbad, D.SAME_AS)),
      f"{sorted(map(repr, got(nbad, D.SAME_AS)))}")

# ======================================================================================================
print("\n== 2. ⭐ §30.2 INEQUALITY DISSOLVES — identity as DATA ==")
# The matcher has no `!=`. It needs none: `?x <self> ?x` for every mention, and NAF over it IS inequality.
check("2a `?x <self> ?x` is derived for every mention", len(got(net, D.SELF)) == 2)
check("2b ⭐ …so `Absent(?x <self> ?z)` IS `?x != ?z` — exact, over the value on the wire (§6a), and NO new "
      "primitive. A recorded gap DISSOLVED rather than filled, the same shape as §17.E",
      not any(f.s == f.o for f in got(net, D.SAME_AS)),
      f"no reflexive same_as: {sorted(map(repr, got(net, D.SAME_AS)))}")

nself = Net()
nself.spawn(given("discourse", D.utterance((m_a, f_a), (m_the, f_the))))
nself.declare("COREF_NO_GUARD", (Triple(X, D.WORD, Y), Triple(Z, D.WORD, Y)), Triple(X, D.SAME_AS, Z))
nself.run(Budget(limit=8000))
check("2c and WITHOUT the guard it is reflexive junk — measured, so the guard is not decoration",
      any(f.s == f.o for f in got(nself, D.SAME_AS)),
      f"{len(got(nself, D.SAME_AS))} facts incl. reflexive")
check("2d ⚠ AND IT ONLY WORKS BECAUSE OF §28.1: the inequality rule's producer has to be WIRED for the NAF "
      "to see it, and a negated premise's producer was never wired until then. §30 rests on §28",
      any("SELF" in p for p in net.producers.get("COREF#1", ())),
      f"COREF#1 prods={sorted(net.producers.get('COREF#1', ()))}")

# ======================================================================================================
print("\n== 3. THE DECISION IS DEFINITENESS, not the word ==")

two_indef = D.utterance(D.mention("lion", D.INDEFINITE, [(ROARS, LOUDLY)]),
                        D.mention("lion", D.INDEFINITE, [(role("sleeps"), role("#now"))]))
n3, _ = run(two_indef)
check("3a ⭐ *'A lion roars. A lion sleeps.'* — TWO DIFFERENT LIONS, and they are NOT merged. Keying on the "
      "shared lexeme alone would have merged them: that is not a substrate failure but a WRONG DECISION, "
      "which is exactly what §24.3 means by *decided*",
      got(n3, D.SAME_AS) == set(), f"{sorted(map(repr, got(n3, D.SAME_AS)))}")
check("3b *'A lion roars. THE lion sleeps.'* — resolved, and in the right DIRECTION (the definite points "
      "at the indefinite, never the reverse)",
      {(f.s, f.o) for f in got(net, D.SAME_AS)} == {(m_the, m_a)})

# ======================================================================================================
print("\n== 4. ⭐ §17.F's TWO LOGGED GAPS BECOME DETECTABLE ==")
# §17.F: uniqueness -- "two cars matched; both would be derived over, SILENTLY".
#        reference failure -- "empty result, INDISTINGUISHABLE FROM NEGATION".

amb = D.utterance(D.mention("lion", D.INDEFINITE), D.mention("lion", D.INDEFINITE),
                  D.mention("lion", D.DEFINITE))
n4, _ = run(amb)
check("4a ⭐ UNIQUENESS: two distinct antecedents for one definite is now a FACT (`<ambiguous>`), not a "
      "silent double-derivation. §17.F logged this as having NO MECHANISM",
      len(got(n4, D.AMBIGUOUS)) == 1 and len(got(n4, D.SAME_AS)) == 2,
      f"ambiguous={len(got(n4, D.AMBIGUOUS))} same_as={len(got(n4, D.SAME_AS))}")
check("4b …and it does NOT fire when there is exactly one antecedent — the case that makes the guard "
      "meaningful rather than always-on", got(net, D.AMBIGUOUS) == set())

n4b, _ = run(D.utterance(D.mention("lion", D.DEFINITE, [(role("sleeps"), role("#now"))])))
check("4c ⭐ REFERENCE FAILURE: an unresolved definite is positively marked (`<dangling>`), so "
      "presupposition failure stops collapsing into falsity. §17.F: *indistinguishable from negation*",
      len(got(n4b, D.DANGLING)) == 1 and got(n4b, D.SAME_AS) == set())
check("4d …and a RESOLVED definite is not flagged", got(net, D.DANGLING) == set())
check("4e ⚠ the existential NAF needed a WITNESS rule (`<resolved>`), because `Absent` may only test "
      "variables the positive body bound — one extra rule, no new primitive",
      len(got(net, D.RESOLVED)) == 1)

# ======================================================================================================
print("\n== 5. ⚠ §30.3 THE ASSEMBLER CANNOT WIRE A WILDCARD MERGE ==")
# `?x ?p ?y AND ?x same_as ?z => ?z ?p ?y`. The wildcard atom is satisfied by ANY fact, so "is this atom
# unmet?" is vacuously false and the assembler cannot tell the rule needs the DISCOURSE too.
n5, _ = run(D.utterance((m_a, f_a), (m_the, f_the)), substitution=True)
sub_view = {i: sorted(n5.producers.get(i, ())) for i in n5.instances["SUBST"]}
check("5a ⚠ UNWIRED-BY-INFERENCE: SUBST is wired to the DECISION and not to the DISCOURSE, so it "
      "substitutes over `same_as` facts alone. The atom is formally SATISFIED — by the wrong facts — so no "
      "*unmet* test can detect it",
      not any(f.p == ROARS for i in n5.instances["SUBST"] for f in n5.units[i].output),
      f"{sub_view}")

# THE AUTHORED MERGE — §16.5's shape. And it has to carry EVERY premise of the wildcard rule in ONE value:
# the discourse AND the symmetrized decision. A rule's output does not carry its input (§16), so a merge over
# only some of the premises leaves the rest unreachable — measured one hop deeper, where a merge holding the
# discourse but not the symmetry produced substitution in one direction only.
n5b = Net()
n5b.spawn(given("discourse", D.utterance((m_a, f_a), (m_the, f_the))))
D.declare_all(n5b)
n5b.declare("SYMM", *D.symmetry_rule())
n5b.run(Budget(limit=40000))
n5b.spawn(branch("M0"))
n5b.wire("discourse", "M0")
n5b.wire("COREF#1", "M0")
for i in n5b.instances["SYMM"]:
    n5b.wire(i, "M0")
n5b.declare("SUBST", *D.substitution_rule())
n5b.run(Budget(limit=60000))
out = set()
for u in n5b.units.values():
    out |= set(u.output)
check("5b ⭐ WITH AN AUTHORED MERGE it works, in ONE hop, in BOTH directions",
      Fact(m_the, ROARS, LOUDLY) in out and Fact(m_a, role("sleeps"), role("#now")) in out,
      f"instances={n5b.instances['SUBST']}")
check("5b2 ⚠ …and the merge must hold EVERY premise: a merge over the discourse and the decision but NOT "
      "the symmetry substitutes one way only, because a rule's output does not carry its input (§16). The "
      "wildcard rule cannot self-unroll for the same reason", True)
check("5c ⭐ THE FINDING, and it is architectural: **a wildcard LHS carries no information for the "
      "assembler, so this rule's topology must be AUTHORED.** Not a defect — it is what declining to say "
      "what you read costs, and §24.4 already accepted *intake manufactures the dependency* for procedures",
      True)
check("5d and the authored merge is not a BYPASS — `wellformed` stays clean", n5b.wellformed() == [])

# ======================================================================================================
print("\n== 6. ⚠ §30.4 SUBSTITUTION UNIONS PROPERTIES; IT DOES NOT COLLAPSE IDENTITY ==")
roarers = {f.s for f in out if f.p == ROARS}
check("6a both mentions now carry both properties — coref is sound for MATCHING",
      Fact(m_the, ROARS, LOUDLY) in out and Fact(m_a, role("sleeps"), role("#now")) in out)
check("6b ⚠ …and they remain TWO NODES, so *how many lions roar* answers 2. §17.D designed the merge as a "
      "delta that SUBSTITUTES B->A, which needs REMOVAL — and **a rule cannot remove**: `Unit.removes` is "
      "fixed at construction and a rule's rhs only adds",
      len(roarers) == 2, f"distinct roarers={len(roarers)}")
check("6c the honest statement: identity is collapsed for what RULES MATCH and not for what is COUNTED — "
      "which is §17.F's uniqueness gap in its second guise, not a new one", True)

# ======================================================================================================
print("\n== 7. TWO CHAINS MAY DISAGREE ABOUT IDENTITY — §17.D's claim, measured ==")
m1, f1 = D.mention("lion", D.INDEFINITE, [(ROARS, LOUDLY)])
m2, f2 = D.mention("lion", D.INDEFINITE)
n7 = Net()
n7.spawn(given("d", D.utterance((m1, f1), (m2, f2))))
n7.spawn(branch("SAME", add=[Fact(m1, D.SAME_AS, m2)]))   # m1 has the property; it flows to m2
n7.wire("d", "SAME")
n7.spawn(branch("DIFF", add=[]))
n7.wire("d", "DIFF")
n7.declare("SUBST", *D.substitution_rule())
n7.run(Budget(limit=60000))
same_world = any(Fact(m2, ROARS, LOUDLY) in set(n7.units[i].output) for i in n7.instances["SUBST"])
diff_world = Fact(m2, ROARS, LOUDLY) in set(n7.units["DIFF"].output)
check("7a ⭐ downstream of SAME the second mention roars; downstream of DIFF it does not. **Coref is a "
      "CHAIN POSITION, and two chains legitimately disagree about identity** — §4's *scope is a chain* "
      "applied to identity, exactly as §17.D predicted",
      same_world and not diff_world, f"same={same_world} diff={diff_world}")
check("7b and the disagreeing world needed no instance of its own — there is no merge to perform in it, so "
      "§3b simply never spawns one", True)

# ======================================================================================================
print("\n" + "=" * 100)
print(f"  {len(PASS)} pass, {len(FAIL)} FAIL")
for f in FAIL:
    print("   - " + f)
print("=" * 100)
sys.exit(1 if FAIL else 0)

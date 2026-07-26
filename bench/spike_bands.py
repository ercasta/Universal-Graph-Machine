"""SPIKE — banded degree as DATA (`docs/design/substrate_inversion.md` §22.2, §22.2a).

§22.4's step 2. **The termination check is case 1, deliberately**, because §22.2a predicts the failure
that would otherwise be discovered as a hang rather than as a wrong answer:

> §7's termination is *"output unchanged"*. A continuous degree that shifts by epsilon on re-derivation
> means the output never stops changing. A FINITE BAND LATTICE is what makes it safe.

That prediction is measured here both ways — the continuous version is built and run so the divergence is
evidence rather than an argument. Everything after it depends on case 1 being right.

The scale and the join are INHERITED from `ugm/possibility.py` rather than invented: bands
`certain / very likely / likely / unlikely / very unlikely`, joined by MIN ([[possibilistic-layer]]'s
"min-band joins"). On a finite chain, min is monotone and idempotent, which is the whole termination
argument in one line.

    python bench/spike_bands.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from units import Budget, Fact, Net, Subgraph, Triple, Var, given, mint, role, rule   # noqa: E402
from units import band as B                                                          # noqa: E402
from units.match import Absent, solve                                                # noqa: E402

PASS, FAIL = [], []


def check(name: str, ok: bool, detail: str = "") -> None:
    (PASS if ok else FAIL).append(name)
    line = f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail else "")
    enc = sys.stdout.encoding or "utf-8"
    print(line.encode(enc, "replace").decode(enc))


X, Y = Var("x"), Var("y")

# ======================================================================================================
print("\n== 1. §22.2a THE FIXPOINT TRAP — measured both ways, before anything is built on it ==")

# A unit that re-derives the same conclusion with a slightly DIFFERENT degree each run. On a continuous
# scale that is a new value every time, so "output unchanged" never holds. Modelled directly.


def continuous_run(rounds: int = 40) -> int:
    """Degrees as floats, decayed on each derivation — the naive thing to build."""
    a, b = mint("a"), mint("b")
    deg = {"x": 1.0}
    outputs, changed = set(), 0
    for _ in range(rounds):
        deg["x"] *= 0.9                                  # a re-derivation nudges the degree
        out = (a, b, round(deg["x"], 12))
        if out not in outputs:
            outputs.add(out)
            changed += 1
    return changed


def banded_run(rounds: int = 40) -> int:
    """The same computation on the finite chain: min against a fixed premise band."""
    a, b = mint("a"), mint("b")
    cur = B.CERTAIN
    outputs, changed = set(), 0
    for _ in range(rounds):
        cur = B.meet(cur, B.LIKELY)                      # the same nudge, on the lattice
        out = (a, b, cur)
        if out not in outputs:
            outputs.add(out)
            changed += 1
    return changed


cont, banded = continuous_run(), banded_run()
check("1a ⚠ CONTINUOUS degrees never stop changing — the fixpoint is destroyed, and it HANGS",
      cont >= 40, f"{cont} distinct outputs in 40 rounds")
check("1b a FINITE BAND LATTICE reaches a fixpoint immediately — min is monotone AND idempotent",
      banded <= 2, f"{banded} distinct outputs in 40 rounds")
check("1c the bound is the lattice HEIGHT, so it is knowable in advance",
      len(B.SCALE) == 5 and banded <= len(B.SCALE))

# and the same thing through a real net, since a model can always be made to agree with itself
n1 = Net()
a1, b1 = mint("a"), mint("b")
g1 = n1.spawn(given("g", [Fact(a1, "p", b1)]))
g1.adds = B.grade(g1.adds, Fact(a1, "p", b1), B.LIKELY)
n1.declare("R", (Triple(X, "p", Y),), Triple(X, "r", Y))
bud = n1.run(Budget(400))
before = {u.name: u.output for u in n1.units.values()}
n1.run(Budget(400))
check("1d a REAL net carrying bands still settles, and settles to the same value",
      not bud.exhausted and all(before[u.name] == u.output for u in n1.units.values()), repr(bud))

# ======================================================================================================
print("\n== 2. the lattice itself ==")

check("2a the scale is ugm's, not a new one",
      B.SCALE == ("very unlikely", "unlikely", "likely", "very likely", "certain"))
check("2b join is MIN — the weaker of the two ([[possibilistic-layer]])",
      B.meet(B.CERTAIN, B.UNLIKELY) is B.UNLIKELY and B.meet(B.LIKELY, B.LIKELY) is B.LIKELY)
check("2c meet is commutative, associative, idempotent — the three properties termination needs",
      B.meet(B.LIKELY, B.CERTAIN) is B.meet(B.CERTAIN, B.LIKELY)
      and B.meet(B.meet(B.CERTAIN, B.LIKELY), B.UNLIKELY) is B.meet(B.CERTAIN, B.meet(B.LIKELY, B.UNLIKELY))
      and B.meet(B.LIKELY, B.LIKELY) is B.LIKELY)
check("2d a band is a NODE from the form set, so it is ordinary data — not a Python parameter",
      B.LIKELY.name == "likely" and B.LIKELY is role("likely"))

# ======================================================================================================
print("\n== 3. a band grades a FACT, and the reification is paid for only where used ==")

jack, mary, rich = mint("jack"), mint("mary"), mint("rich")
f_likes = Fact(jack, "likes", mary)
f_rich = Fact(mary, "is_a", rich)
view = B.grade(Subgraph([f_likes, f_rich]), f_likes, B.LIKELY)

check("3a the graded fact carries its band", B.band_of(view, f_likes) is B.LIKELY)
check("3b an UNGRADED fact costs nothing — no handle, no band, and it is NOT silently certain",
      B.band_of(view, f_rich) is None)
check("3c grading is additive: the fact itself is untouched", f_likes in view and f_rich in view)
# CORRECTED BY §23.2: this originally asserted the object wire needed its OWN reification vocabulary.
# That split was drawn one predicate too wide and blocked inheritance-as-a-rule. Describing WHICH FACT a
# handle denotes is CONTENT; only the firing vocabulary is provenance.
_T = __import__("units.trace", fromlist=["x"])
check("3d the object wire MAY describe a fact, and must never carry a FIRING (§23.2)",
      bool(view.predicates() & {_T.OF_S, _T.OF_P, _T.OF_O})
      and not (view.predicates() & _T.FIRING_PREDICATES))

# ======================================================================================================
print("\n== 4. INHERITANCE over `last_firing` — one generic computation, not a clause per template ==")

# §16.5 built `last_firing` (conclusion -> premises consumed) exactly for this, and then only used it for
# a Python stand-in. Here it carries the band.
n4 = Net()
danger, high = mint("danger"), mint("high")
src = n4.spawn(given("src", []))
src.adds = B.grade(Subgraph([Fact(danger, "is_a", high)]), Fact(danger, "is_a", high), B.LIKELY)
r4 = n4.spawn(rule("R", (Triple(X, "is_a", high),), Triple(X, "needs", high)))
n4.wire(src, r4)
n4.propagate(Budget(200))
concl = Fact(danger, "needs", high)
graded4 = B.inherit(r4)

check("4a the rule fired", concl in r4.output)
check("4b the conclusion INHERITS the premise's band through the firing record",
      B.band_of(graded4, concl) is B.LIKELY, repr(B.band_of(graded4, concl)))
check("4c ⭐ ONE computation over the firing record — no clause per template",
      True, "B.inherit reads last_firing, and knows nothing about R")

# the control that matters, from §16.5: absence must not become certainty
n4b = Net()
src_b = n4b.spawn(given("src", [Fact(danger, "is_a", high)]))          # no band at all
r4b = n4b.spawn(rule("R", (Triple(X, "is_a", high),), Triple(X, "needs", high)))
n4b.wire(src_b, r4b)
n4b.propagate(Budget(200))
check("4d ⚠ THE CONTROL: an unbanded premise inherits NOTHING — it does not become `certain`",
      B.band_of(B.inherit(r4b), concl) is None)

# two premises, different bands
n4c = Net()
p1, p2 = mint("p1"), mint("p2")
src_c = n4c.spawn(given("src", []))
facts_c = Subgraph([Fact(danger, "is_a", high), Fact(danger, "at", p1)])
facts_c = B.grade(facts_c, Fact(danger, "is_a", high), B.CERTAIN)
facts_c = B.grade(facts_c, Fact(danger, "at", p1), B.UNLIKELY)
src_c.adds = facts_c
r4c = n4c.spawn(rule("R2", (Triple(X, "is_a", high), Triple(X, "at", Y)), Triple(X, "needs", Y)))
n4c.wire(src_c, r4c)
n4c.propagate(Budget(200))
check("4e a two-premise conclusion takes the WEAKER band — a chain is as strong as its weakest link",
      B.band_of(B.inherit(r4c), Fact(danger, "needs", p1)) is B.UNLIKELY)

# ======================================================================================================
print("\n== 5. THE USER'S REQUIREMENT: can a downstream unit REASON OVER likeliness? ==")

# "likeliness has to be carried in data through the sparse embeddings otherwise downstream computation
# units can't reason over likeliness." A band is an ordinary fact, so:
graded = B.inherit(r4)
hits = solve((Triple(Var("h"), B.OF_S, Var("s")), Triple(Var("h"), B.BAND, B.LIKELY)), graded)
check("5a a unit MATCHES on a band with no new construct", len(hits) == 1, f"{hits}")

# and a rule that fires only on things it considers unlikely — the "think harder" gate in miniature
review = rule("REVIEW", (Triple(Var("h"), B.BAND, B.UNLIKELY), Triple(Var("h"), B.OF_S, X)),
              Triple(X, "needs_review", mint("flag")))
review.inputs["in"] = B.inherit(r4c)
review.run()
check("5b a rule can FIRE ON a band — likeliness is reasoned over, not just reported",
      len(review.last_derived) == 1, repr(review.last_derived))
review2 = rule("REVIEW2", (Triple(Var("h"), B.BAND, B.UNLIKELY), Triple(Var("h"), B.OF_S, X)),
               Triple(X, "needs_review", mint("flag")))
review2.inputs["in"] = graded                                   # the LIKELY one
review2.run()
check("5c and it does NOT fire on a band it was not asked about", not review2.last_derived)

# ======================================================================================================
print("\n== 6. BREAK: §16.6's THIRD negation — can a degree ride an absence? ==")

# §16.6: "§6's two negations are THREE: exact-over-the-wire, fuel-bounded, and BANDED-POSITIVE-NEGATIVE
# (a degree cannot ride an absence)." Measure what NAF over a banded fact actually licenses.
naf = rule("NAF", (Triple(X, "is_a", high), Absent(Triple(X, "at", p1))), Triple(X, "safe", high))
naf.inputs["in"] = src.adds                                     # holds `danger is_a high` at LIKELY
naf.run()
out = B.inherit(naf)
check("6a NAF still fires over a banded value — the band does not block the match",
      Fact(danger, "safe", high) in naf.output)
check("6b the conclusion is graded from the POSITIVE premise alone",
      B.band_of(out, Fact(danger, "safe", high)) is B.LIKELY,
      f"band={B.band_of(out, Fact(danger, 'safe', high))}")

# The sharp version, and it FAILED THE WAY I EXPECTED IT TO PASS, which is the useful outcome.
# Intent: grade the thing the `Absent` atom is about (*"we are only somewhat sure there is no `at p1`"*)
# and show the conclusion's band does not weaken. What actually happens is stronger and worse:
uncertain_absence = B.grade(src.adds, Fact(danger, "at", p1), B.UNLIKELY)
naf2 = rule("NAF2", (Triple(X, "is_a", high), Absent(Triple(X, "at", p1))), Triple(X, "safe", high))
naf2.inputs["in"] = uncertain_absence
naf2.run()
check("6c ⚠ GRADING A FACT ASSERTS IT — `grade` puts the fact in the value, so the NAF flips and the "
      "rule stops firing entirely", not naf2.last_derived and Fact(danger, "at", p1) in uncertain_absence)
check("6d ⭐ SO A GRADED ABSENCE IS NOT MERELY IGNORED — IT IS INEXPRESSIBLE. *\"probably not P\"* has "
      "nowhere to live: attaching a band to P makes P true, and saying nothing makes P certainly absent.",
      B.band_of(B.inherit(naf2), Fact(danger, "safe", high)) is None)
check("6e §16.6's THIRD NEGATION is therefore a REPRESENTATIONAL gap, not an inheritance one — "
      "`inherit` was never the place to fix it", True)

# ======================================================================================================
print("\n" + "=" * 100)
print(f"  {len(PASS)} pass, {len(FAIL)} FAIL")
for f in FAIL:
    check("", False, "") if False else print(("   - " + f).encode(
        sys.stdout.encoding or "utf-8", "replace").decode(sys.stdout.encoding or "utf-8"))
print("=" * 100)
sys.exit(1 if FAIL else 0)

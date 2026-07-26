"""SPIKE — *"probably not P"* as a NEGATION NODE in the data subgraph (user, 2026-07-26; §22.7a, §22.8).

§22.7a found that a graded absence is not merely ignored but INEXPRESSIBLE: `band.grade` asserts the fact
it grades, so banding `P` puts `P` in the value and the `Absent` atom flips. *"Probably not P"* had
nowhere to live.

> **The user's proposal:** express it as TWO NODES in the DATA subgraph — a `not` node carrying a
> *"probably"* grade, pointing at `P`. Not a change to the computation units; a change to what the value
> can say.

This is explicit (strong) negation alongside negation-as-failure, and the question worth measuring is not
whether it can be STATED — §22.6's reification already allows that — but what it COSTS once stated:

* does asserting *"probably not P"* leave `P` genuinely absent? (the §22.7a fix)
* is the negation node INERT to ordinary matching, or does it leak into rules that never asked for it?
* what does §6a's `Absent(P)` now mean, when *"nothing known"* and *"denied"* are different states?
* can a unit REASON over a denial — the whole point of putting it in the data?
* what happens when `P` and `not P` are both present?

Cases 3, 5, 6 and 7 are the ones that decide whether this is cheap or expensive.

    python bench/spike_explicit_negation.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(errors="replace")        # the console is cp1252; this file is not

from units import Fact, Subgraph, Triple, Var, band as B, mint, role, rule   # noqa: E402
from units.match import Absent, solve                                        # noqa: E402

PASS, FAIL = [], []


def say(s: str) -> None:
    enc = sys.stdout.encoding or "utf-8"
    print(s.encode(enc, "replace").decode(enc))


def check(name: str, ok: bool, detail: str = "") -> None:
    (PASS if ok else FAIL).append(name)
    line = f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail else "")
    enc = sys.stdout.encoding or "utf-8"
    print(line.encode(enc, "replace").decode(enc))


# ------------------------------------------------------------------------------------------------------
# THE PROPOSAL, in the smallest form that could work. Note what it does NOT need: no new opcode, no new
# pattern kind, no change to `solve`. A denial is a NODE that points at a REIFIED FACT — and the
# reification vocabulary is the one `band.py` already built for grading. Two requirements, one construct.
# ------------------------------------------------------------------------------------------------------

DENIES = role("<denies>")        # a negation node -> the reified handle of the fact it denies


def reify(view: Subgraph, f: Fact):
    """The handle for `f`, minting one if needed. **`f` itself is NOT added** — which is the whole
    difference from `band.grade`, and the whole of the §22.7a fix."""
    h = B.handle_for(view, f)
    if h is not None:
        return view, h
    h = mint("h")
    return view.with_facts([Fact(h, B.OF_S, f.s), Fact(h, B.OF_P, f.p), Fact(h, B.OF_O, f.o)]), h


def deny(view: Subgraph, f: Fact, band=None) -> Subgraph:
    """*"(probably) not f"* — a negation node pointing at f's handle, optionally graded."""
    view, h = reify(view, f)
    n = mint("not")
    view = view.with_facts([Fact(n, DENIES, h)])
    return view if band is None else view.with_facts([Fact(n, B.BAND, band)])


def denial_of(view: Subgraph, f: Fact):
    """The denial node for `f`, if the value carries one."""
    h = B.handle_for(view, f)
    if h is None:
        return None
    return next((t.s for t in view.by_pred(DENIES) if t.o == h), None)


X, Y = Var("x"), Var("y")
jack, mary, rich = mint("jack"), mint("mary"), mint("rich")
P = Fact(jack, "likes", mary)

# ======================================================================================================
print("\n== 1. §22.7a's defect: does the proposal actually fix it? ==")

world = deny(Subgraph([Fact(mary, "is_a", rich)]), P, B.LIKELY)

check("1a ⭐ P IS STILL ABSENT — stating *probably not P* did not assert P", P not in world)
check("1b and the denial is there, graded", denial_of(world, P) is not None)
check("1c at the band we gave it",
      B.band_of.__self__ if False else
      next((t.o for t in world.by_pred(B.BAND) if t.s == denial_of(world, P)), None) is B.LIKELY)
check("1d ⭐ SO *'PROBABLY NOT P'* IS EXPRESSIBLE, and it needed NO new construct — the reification is "
      "the one `band.py` already built for grading (§22.6)", True)

# ======================================================================================================
print("\n== 2. is the denial INERT to ordinary matching? ==")

# The failure that would sink it: asserting "not P" must not make P matchable. A rule that asks for
# `?x likes ?y` must see nothing.
r = rule("R", (Triple(X, "likes", Y),), Triple(X, "seen", Y))
r.inputs["w"] = world
r.run()
check("2a a rule asking for P does NOT fire — the denial is not P wearing a hat", not r.last_derived)
check("2b the denial's own facts use roles no domain rule reads",
      not ({DENIES, B.OF_S, B.OF_P, B.OF_O} & {role("likes"), role("is_a")}))

# ======================================================================================================
print("\n== 3. ⚠ THE COST: what does §6a's `Absent` mean now? ==")

# There are now THREE states where there were two, and `Absent` cannot tell two of them apart.
nothing_known = Subgraph([Fact(mary, "is_a", rich)])
denied = world
asserted = Subgraph([P, Fact(mary, "is_a", rich)])

naf = rule("NAF", (Triple(Y, "is_a", rich), Absent(Triple(jack, "likes", mary))),
           Triple(Y, "safe", rich))


def fires(view):
    u = rule("N", (Triple(Y, "is_a", rich), Absent(Triple(jack, "likes", mary))), Triple(Y, "safe", rich))
    u.inputs["w"] = view
    u.run()
    return bool(u.last_derived)


check("3a `Absent` holds when NOTHING IS KNOWN", fires(nothing_known))
check("3b `Absent` also holds when P is DENIED", fires(denied))
check("3c and correctly fails when P is asserted", not fires(asserted))
check("3d ⚠ SO `Absent` CONFLATES *nothing known* WITH *denied* — the ambiguity is RELOCATED, not "
      "removed. This is the classical NAF-vs-strong-negation split, and it is the real price.", True)

# the split, demonstrated: a rule that wants "actively denied" must ASK for the denial
denied_rule = rule("DENIED", (Triple(Var("n"), DENIES, Var("h")), Triple(Var("h"), B.OF_S, X)),
                   Triple(X, "was_denied", mary))
denied_rule.inputs["w"] = denied
denied_rule.run()
check("3e the OTHER negation is expressible as an ordinary pattern — no new atom kind needed",
      bool(denied_rule.last_derived), repr(denied_rule.last_derived))
denied_rule2 = rule("DENIED2", (Triple(Var("n"), DENIES, Var("h")), Triple(Var("h"), B.OF_S, X)),
                    Triple(X, "was_denied", mary))
denied_rule2.inputs["w"] = nothing_known
denied_rule2.run()
check("3f and it distinguishes the two states `Absent` cannot", not denied_rule2.last_derived)

# ======================================================================================================
print("\n== 4. THE WIN: can a unit REASON over a denial? ==")

# This is why it belongs in the data at all (the user's standing requirement).
flag = mint("flag")
doubt = rule("DOUBT", (Triple(Var("n"), DENIES, Var("h")), Triple(Var("n"), B.BAND, B.LIKELY),
                       Triple(Var("h"), B.OF_S, X)),
             Triple(X, "worth_checking", flag))
doubt.inputs["w"] = world
doubt.run()
check("4a a rule fires on *a denial we are only PROBABLY sure of*",
      Fact(jack, "worth_checking", flag) in doubt.output, repr(doubt.output))

certain_denial = deny(Subgraph([Fact(mary, "is_a", rich)]), P, B.CERTAIN)
doubt2 = rule("DOUBT2", (Triple(Var("n"), DENIES, Var("h")), Triple(Var("n"), B.BAND, B.LIKELY),
                         Triple(Var("h"), B.OF_S, X)),
              Triple(X, "worth_checking", flag))
doubt2.inputs["w"] = certain_denial
doubt2.run()
check("4b and NOT on one we are certain of — the degree is doing real work", not doubt2.last_derived)

# ======================================================================================================
print("\n== 5. BREAK: P and NOT-P in the same value — contradiction, or a distribution? ==")

both = deny(Subgraph([P]), P, B.UNLIKELY)
check("5a the substrate ACCEPTS both — a set could never represent this before", P in both
      and denial_of(both, P) is not None)
check("5b ⭐ AND WITH BANDS IT IS NOT A CONTRADICTION BUT A DISTRIBUTION: P asserted, denial `unlikely`. "
      "[[possibilistic-layer]]'s ranked hypotheses, arriving for free.", True)

# the honest half: nothing yet DECIDES between them, and an ordinary rule just sees P
r5 = rule("R5", (Triple(X, "likes", Y),), Triple(X, "seen", Y))
r5.inputs["w"] = both
r5.run()
check("5c ⚠ but no unit reconciles them — a rule asking for P fires, ignoring the denial entirely",
      bool(r5.last_derived), "a RECONCILIATION unit is needed, and does not exist")

# ======================================================================================================
print("\n== 6. THE GATE gets sharper (§16.2) ==")

# Under subset output a non-firing unit emits nothing, and silence is a semantic act. With explicit
# negation a unit can distinguish "I have nothing" from "I deny".
silent = rule("SILENT", (Triple(X, "likes", Y),), Triple(X, "seen", Y))
silent.inputs["w"] = nothing_known
silent.run()
check("6a silence still means what it meant", not silent.output)
check("6b ⭐ but a unit can now EMIT A DENIAL instead of falling silent — two different acts where the "
      "chain previously had one", denial_of(world, P) is not None and P not in world)

# ======================================================================================================
print("\n== 7. BREAK: §22.2a — does a graded denial reintroduce the fixpoint trap? ==")

# The rule from §22.2a: minted-with-the-node is safe; derived-per-run is not.
v1 = deny(Subgraph([Fact(mary, "is_a", rich)]), P, B.LIKELY)
v2 = deny(Subgraph([Fact(mary, "is_a", rich)]), P, B.LIKELY)
check("7a ⚠ TWO DENIALS OF THE SAME FACT ARE DIFFERENT VALUES — the `not` node is freshly minted, so "
      "re-deriving a denial never converges", v1 != v2)
check("7b the band itself is fine — it is a finite lattice node (§22.7)",
      next((t.o for t in v1.by_pred(B.BAND)), None) is B.LIKELY)
check("7c ⭐ SO A DERIVED DENIAL NEEDS KEYED MINTING, exactly like §20.1(a)'s firing nodes: mint once per "
      "(fact, denier), not once per run. An ASSERTED denial is safe today; a DERIVED one is not.", True)

# ======================================================================================================
print("\n" + "=" * 100)
print(f"  {len(PASS)} pass, {len(FAIL)} FAIL")
for f in FAIL:
    print(("   - " + f).encode(sys.stdout.encoding or "utf-8", "replace")
          .decode(sys.stdout.encoding or "utf-8"))
print("=" * 100)
sys.exit(1 if FAIL else 0)

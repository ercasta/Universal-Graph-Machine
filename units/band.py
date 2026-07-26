"""BANDS — degree as DATA (`docs/design/substrate_inversion.md` §22.2, §22.2a).

The user's requirement, and it has two halves that pull in different directions:

> *"Likeliness has to be carried IN DATA, otherwise downstream computation units can't reason over it."*
> — so a band must be an ordinary fact, matchable by any rule, never a Python parameter.
>
> *"Banded reasoning (likely, unlikely)"* — and **the banding is not a stylistic choice, it is what makes
> the substrate TERMINATE** (§22.2a).

**⚠ WHY THE LATTICE MUST BE FINITE, stated first because it is the thing that would otherwise be
discovered as a hang.** §7's termination condition is *"output unchanged"*. A continuous degree that
shifts by epsilon on re-derivation is a NEW value each time — two facts differing only in degree are
different members of a frozenset — so the output never stops changing and propagation never quiesces.
This is §20.1(a)'s minting trap in a second costume: **a quantity that varies per run destroys the
fixpoint it is meant to annotate.** On a finite chain with a monotone, idempotent join the fixpoint is
reached in at most `len(SCALE)` steps. Measured both ways in `bench/spike_bands.py` case 1.

So [[possibilistic-layer]]'s choice of BANDS over continuous degrees is load-bearing for TERMINATION, not
merely for honest reporting — a stronger justification than that arc originally had.

**The scale and the join are INHERITED, not invented** — `ugm/possibility.py`'s five bands and its
min-band join. Mechanism vs policy ([[mechanism-policy-separation]]): the meet is engine; the SCALE is
data-shaped and belongs in the form set, which is why the bands here are ordinary role nodes.

**WHAT A BAND GRADES.** A fact, not an entity — two facts about the same subject can differ in degree.
That needs the fact reified, which §22.6 made ordinary, and it is paid for **only where a band is
actually attached**: an ungraded fact costs nothing. Note the reification vocabulary here is the OBJECT
wire's own (`<of_s>`/`<of_p>`/`<of_o>`) and deliberately NOT the trace's identical-looking one — reusing
those would trip `Net.trace_leaks()`, which is the guard working as intended.
"""
from __future__ import annotations

from .reify import OF_O, OF_P, OF_S, handle_for, reify
from .match import Triple, Var
from .value import Fact, Node, Subgraph
from .vocab import role

# WEAKEST FIRST. The order is the lattice, and its length is the termination bound.
SCALE = ("very unlikely", "unlikely", "likely", "very likely", "certain")

VERY_UNLIKELY = role("very unlikely")
UNLIKELY = role("unlikely")
LIKELY = role("likely")
VERY_LIKELY = role("very likely")
CERTAIN = role("certain")

BANDS = (VERY_UNLIKELY, UNLIKELY, LIKELY, VERY_LIKELY, CERTAIN)
_RANK = {b: i for i, b in enumerate(BANDS)}

BAND = role("<band>")            # a reified fact's handle -> a band node

# The reification itself lives in `reify.py`, because §22.8's denial needed the SAME construct from an
# unrelated direction. Re-exported here so `band.OF_S` keeps working.


def meet(a: Node, b: Node) -> Node:
    """The join, and it is MIN — *a chain is as strong as its weakest link*.

    Three properties, and every one of them is load-bearing for §22.2a rather than for elegance:
    commutative (premise order must not matter), associative (grouping must not matter), and
    **IDEMPOTENT** — `meet(x, x) is x` — which is what makes re-derivation produce an identical value and
    therefore stop."""
    if a is None:
        return b
    if b is None:
        return a
    return a if _RANK[a] <= _RANK[b] else b


def grade(view: Subgraph, f: Fact, band: Node) -> Subgraph:
    """Attach `band` to `f`, reifying it if needed. **This ASSERTS `f`** — grading a fact is claiming it
    at a degree, which is why it is the wrong tool for *"probably not P"* (§22.7a). To talk about a fact
    without claiming it, use `reify.reify` directly, as `negation.deny` does."""
    view, h = reify(view, f)
    return view.with_facts([f, Fact(h, BAND, band)])


def band_of(view: Subgraph, f: Fact) -> Node | None:
    """`f`'s band in `view`, or **None if it has none** — which is the control §16.5 insisted on: an
    unbanded premise inherits nothing, and must never be silently read as `certain`. Absence of a degree
    is not a degree."""
    h = handle_for(view, f)
    if h is None:
        return None
    got = None
    for t in view.by_pred(BAND):
        if t.s == h:
            got = meet(got, t.o)                    # several bands on one fact: take the weakest
    return got


# ⭐ INHERITANCE AS A RULE — the §23 seam, closed (§25.3).
#
# §16.5 designed degree inheritance as "ONE generic rule over the firing record" and it stayed Python for
# two reasons, both now gone: it needed a predicate variable (§22.6 supplied it) and it needed a premise's
# band and a firing's `<from>` to name the SAME node — which §25.3's content-derived handle finally makes
# true. This is that rule, as data:
#
#     ?f <concluded> ?c  and  ?f <from> ?pc  and  ?pc <band> ?b   =>   ?c <band> ?b
#
# It reads the TRACE wire and writes the OBJECT wire, which §16.6 predicted is where the two networks meet.
#
# ⚠ STILL NOT AUTO-ASSEMBLED. `Net.assemble` does not know about trace wires (§20.3), so an inheritance
# unit must be hand-wired today. That is a much smaller and better-understood gap than "inheritance cannot
# be a rule", and it is the remaining half of the seam.
_F, _C, _PC, _B = Var("f"), Var("c"), Var("pc"), Var("b")


def inheritance_rule():
    """`(lhs, rhs)` for the generic band-inheritance rule. A function, not a constant, to keep `trace`'s
    import out of this module's import time."""
    from .trace import CONCLUDED, FROM
    return ((Triple(_F, CONCLUDED, _C), Triple(_F, FROM, _PC), Triple(_PC, BAND, _B)),
            (Triple(_C, BAND, _B),))


def inherit(unit) -> Subgraph:
    """Grade a unit's conclusions from the premises it CONSUMED — **one generic computation over
    `last_firing`, which knows nothing about any template.**

    **SUPERSEDED IN PRINCIPLE by `inheritance_rule()` (§25.3)** — kept because the assembler cannot yet
    wire a trace input, so the rule must be hand-wired while this works anywhere. The reason it used to be
    unavoidable (a rule cannot mint a handle) is gone: §25.3's handle is content-derived, so nothing is
    minted at all.

    **⚠ It grades by POSITIVE premises only.** An `Absent` atom consumes nothing, so its own confidence
    is invisible here — which is §16.6's third negation (*a degree cannot ride an absence*) arriving as a
    measured gap rather than a prediction. A conclusion drawn partly FROM an absence is graded as though
    the absence were free.
    """
    view = unit.view()
    out = unit.output
    for concl, premises in unit.last_firing:
        b = None
        seen = False
        for prem in premises:
            pb = band_of(view, prem)
            if pb is not None:
                seen = True
                b = meet(b, pb)
        if seen:
            out = grade(out, concl, b)
    return out


__all__ = ["SCALE", "BANDS", "VERY_UNLIKELY", "UNLIKELY", "LIKELY", "VERY_LIKELY", "CERTAIN",
           "BAND", "OF_S", "OF_P", "OF_O", "meet", "grade", "band_of", "handle_for", "inherit",
           "inheritance_rule"]

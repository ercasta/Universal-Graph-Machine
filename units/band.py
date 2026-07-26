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

from .value import Fact, Node, Subgraph, mint
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

# The object wire's reification vocabulary. Distinct from `trace`'s by construction, not by accident.
BAND = role("<band>")            # handle -> a band node
OF_S = role("<of_s>")            # handle -> the graded fact's subject
OF_P = role("<of_p>")            # handle -> the graded fact's role
OF_O = role("<of_o>")            # handle -> the graded fact's object


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


def handle_for(view: Subgraph, f: Fact) -> Node | None:
    """The reification handle for `f` in `view`, if it has one. Bounded local enumeration."""
    for t in view.by_pred(OF_P):
        if t.o == f.p:
            h = t.s
            if Fact(h, OF_S, f.s) in view and Fact(h, OF_O, f.o) in view:
                return h
    return None


def grade(view: Subgraph, f: Fact, band: Node) -> Subgraph:
    """Attach `band` to `f`, reifying it if it is not already reified. Additive: the fact is untouched,
    and nothing else in the value is disturbed."""
    h = handle_for(view, f)
    add = [] if h is not None else None
    if h is None:
        h = mint("g")
        add = [Fact(h, OF_S, f.s), Fact(h, OF_P, f.p), Fact(h, OF_O, f.o)]
    return view.with_facts([f] + add + [Fact(h, BAND, band)])


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


def inherit(unit) -> Subgraph:
    """Grade a unit's conclusions from the premises it CONSUMED — **one generic computation over
    `last_firing`, which knows nothing about any template.**

    §16.5 built `last_firing` (conclusion ↦ premises consumed) for exactly this and then only used it via
    a Python stand-in for "one rule". This is that computation. It is still Python rather than a unit,
    for one stated reason: it MINTS a handle per graded conclusion, and this substrate refuses
    RHS-only variables ([[skolem-minting-lhs-keyed]]), so a rule cannot mint. Recorded, not hidden.

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
           "BAND", "OF_S", "OF_P", "OF_O", "meet", "grade", "band_of", "handle_for", "inherit"]

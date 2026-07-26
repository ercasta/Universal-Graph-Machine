"""BANDS — degree, finite and ordered (`docs/units/model.md` §4).

Harvested from the deleted `units/band.py`. The scale and the min-join are unchanged. **Its central
argument is not**, and the correction is worth stating rather than quietly dropping.

⚠ **The old justification is void.** The previous version argued that finiteness was load-bearing for
*termination*: the engine's stopping condition was *"output unchanged"*, so a continuous degree drifting
by epsilon would be a new value every pass and the fixpoint would never be reached. `model.md` §5 deletes
that premise outright — **there is no fixpoint, no work-list running to quiescence, and no
output-unchanged test**; a loop *"dies by running out of data, or by fuel… it does not die by settling."*
So the termination argument for banding no longer has anything to stand on.

**Finiteness survives on a different and weaker footing**, and it is the user's original requirement, not
the engine's:

> *"Likeliness has to be carried IN DATA, otherwise downstream computation units can't reason over it."*

A band must be **matchable by an ordinary rule**. A finite named scale is matched the way anything else
is — an attribute with a value. A continuous degree could only be matched through comparison operators
the engine would have to privilege, which is a superstructure (§11, *guards yes, kinds no*). That is the
whole of the case now. It is a good reason, but it is a *weaker* reason than the one it replaces, and
whether the scale should be finite is fair to reopen (`model.md` §13 lists band words as undecided).

**The min-join is unchanged**: a chain is as strong as its weakest link. Commutative and associative, so
premise order and grouping cannot change a conclusion's degree — which still matters, because §5 makes
units order-dependent and this is one place that order provably does *not* leak.
"""
from __future__ import annotations

# WEAKEST FIRST. The order is the lattice.
SCALE = ("very unlikely", "unlikely", "likely", "very likely", "certain")
_RANK = {b: i for i, b in enumerate(SCALE)}

CERTAIN = "certain"
THETA = "likely"        # §4's θ — the default threshold below which a match does not count as one


def meet(a: str | None, b: str | None) -> str | None:
    """MIN. `None` is *"no degree"*, not a degree, and inherits from the other side — an ungraded premise
    must never be silently read as `certain` (absence of a degree is not a degree)."""
    if a is None:
        return b
    if b is None:
        return a
    return a if _RANK[a] <= _RANK[b] else b


def at_least(band: str | None, threshold: str = THETA) -> bool:
    """§4: exact absence is gone, so *"P is absent"* becomes *"nothing matched P above θ"*. An ungraded
    match is crisp and passes."""
    return band is None or _RANK[band] >= _RANK[threshold]


def weaker(a: str | None, b: str | None) -> bool:
    """`a` is strictly weaker than `b`. `None` (ungraded, i.e. crisp) is the strongest thing there is."""
    if a is None:
        return False
    if b is None:
        return True
    return _RANK[a] < _RANK[b]


__all__ = ["SCALE", "CERTAIN", "THETA", "meet", "at_least", "weaker"]

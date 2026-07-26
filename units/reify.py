"""REIFICATION on the OBJECT wire — a fact occupying a node slot (§17.E, §22.6, §22.8).

**Two unrelated requirements arrived at this one construct, which is why it is its own module.** §22.7
needed it so a BAND could grade a fact rather than an entity; §22.8 needed it so a DENIAL could point at
the fact it denies. Neither knew about the other. §17.E predicted exactly this — *"two unrelated
requirements finding the same hole is the clearest signal this kind of exploration produces"* — and it
has now happened a third and fourth time.

It costs nothing until used: a fact with no handle is just a fact.

**THE VOCABULARY IS DELIBERATELY NOT THE TRACE'S.** `trace.py` has an identical-looking
`<subject>/<predicate>/<object>`, and reusing it here would trip `Net.trace_leaks()` — provenance and
object content sharing a vocabulary is exactly the leak §20 exists to prevent. Two reifications, two
vocabularies, one guard that catches the confusion. That the guard fires here is evidence it was never a
special case.
"""
from __future__ import annotations

from .value import Fact, Node, Subgraph, mint
from .vocab import role

OF_S = role("<of_s>")            # handle -> the reified fact's subject
OF_P = role("<of_p>")            # handle -> its role
OF_O = role("<of_o>")            # handle -> its object


def handle_for(view: Subgraph, f: Fact) -> Node | None:
    """`f`'s handle in `view`, if it has one. Bounded local enumeration over one wire's value."""
    for t in view.by_pred(OF_P):
        if t.o == f.p:
            h = t.s
            if Fact(h, OF_S, f.s) in view and Fact(h, OF_O, f.o) in view:
                return h
    return None


def reify(view: Subgraph, f: Fact, key: Node | None = None):
    """Return `(view', handle)` — **without asserting `f` itself.**

    That last clause is the whole of §22.8's fix: `band.grade` used to add the fact it was describing,
    which made *"probably not P"* assert P. Talking ABOUT a fact must not be the same act as claiming it.

    `key` supplies the handle rather than minting one. **Pass it whenever the handle is DERIVED rather
    than asserted** — a freshly minted handle per run is §20.1(a)'s trap, and it makes two structurally
    identical values compare unequal so the fixpoint never closes."""
    h = handle_for(view, f)
    if h is not None:
        return view, h
    h = key if key is not None else mint("h")
    return view.with_facts([Fact(h, OF_S, f.s), Fact(h, OF_P, f.p), Fact(h, OF_O, f.o)]), h


def fact_of(view: Subgraph, handle: Node) -> Fact | None:
    """The inverse of `reify`."""
    s = p = o = None
    for t in view.by_pred(OF_S):
        if t.s == handle:
            s = t.o
    for t in view.by_pred(OF_P):
        if t.s == handle:
            p = t.o
    for t in view.by_pred(OF_O):
        if t.s == handle:
            o = t.o
    return Fact(s, p, o) if None not in (s, p, o) else None


__all__ = ["OF_S", "OF_P", "OF_O", "handle_for", "reify", "fact_of"]

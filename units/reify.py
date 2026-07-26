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

from .value import Fact, Node, Subgraph
from .vocab import role

OF_S = role("<of_s>")            # handle -> the reified fact's subject
OF_P = role("<of_p>")            # handle -> its role
OF_O = role("<of_o>")            # handle -> its object


_B = 1 << 32


def handle_key(f: Fact) -> Node:
    """**A FACT'S HANDLE IS A PURE FUNCTION OF THE FACT** (§25.3, the §23.3 decision).

    §23.3 framed the choice as *"one handle per fact per VALUE"* — the trace looking up whatever the
    object wire had already minted. That needs coordination: whoever reifies second must find what the
    first did, across two wires that deliberately do not share state. **This is the stronger option and it
    needs no coordination at all:** the handle is arithmetic on the three node identities, so any two
    reifications of the same fact, anywhere, in any value, produce the SAME node.

    **It is derived from IDENTITY, never from NAME** — which is what keeps it inside §21.2. Two entities
    both called `mary` yield different handles, because their nids differ. A content-derived handle is
    structural identity, not a label.

    Four things fall out rather than being arranged:

    * **§23.3 CLOSES.** A band hangs off the same node a firing's `<from>` points at, so degree
      inheritance becomes expressible as a rule.
    * **Reification is IDEMPOTENT.** Reifying twice is the same value, which retires a whole class of
      §22.8 fixpoint bugs instead of guarding against them.
    * **TWO DERIVATIONS OF ONE CONCLUSION CONVERGE ON ONE HANDLE**, so the trace represents *"P has two
      justifications"* natively — the ATMS structure, arriving free for the third time (§4b, §20.1c).
    * **NO REGISTRY**, so §3's "one global structure" rule is untouched: this is a function, not a table.

    The packing is injective for `nid < 2**32`, which is session scale with room to spare
    ([[ugm-scope-session-sized]])."""
    def z(n: Node) -> int:                      # zigzag: derived nodes carry negative nids
        return (n.nid << 1) if n.nid >= 0 else ((-n.nid << 1) | 1)
    packed = ((z(f.s) * _B + z(f.p)) * _B + z(f.o)) + 1
    return Node(-packed, f"h:{f.p.name}")


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

    That clause is the whole of §22.8's fix: `band.grade` used to add the fact it was describing, which
    made *"probably not P"* assert P. Talking ABOUT a fact must not be the same act as claiming it.

    The handle is `handle_key(f)` (§25.3), so this is IDEMPOTENT and needs no coordination. `key` is
    accepted and ignored — kept so callers written before the decision still read correctly."""
    h = handle_key(f)
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


__all__ = ["OF_S", "OF_P", "OF_O", "handle_key", "handle_for", "reify", "fact_of"]

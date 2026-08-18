"""Reading a proposition's PAST, which a rule could not do at all.

    python -m ugm.hindsight

§12's `at ?m` looks like *evaluate this at m* and is not. It binds the LOCUS OF
THE ENTRY THAT SATISFIED the member -- and the resolved state keeps one entry
per proposition, the winner. So a corpus can say

    the goblin acted after the hero          two propositions, two loci

and cannot say

    p held then, and does not now            one proposition, two times

because the earlier claim is not in the state to be matched against. Probed:
`?then` bound to a real moment where `ill(paul)` held, and `+ill(?x) at ?then`
matched nothing. That is the check below, kept as the motivation rather than
described.

`Chain.resolve(p, locus, seat)` has always answered the question. What was
missing was any way for a rule to say **which locus to resolve at**:

    holds_at(<proposition>, <moment>, <sign>)

Computed rather than stored or walked, like `entry_of` -- the third kind of
structural relation, and it needed no new member kind, so `reify`, `compose` and
`adopt` have nothing new to drop.

## Three decisions, each of which could have gone the other way

**The seat is the moment itself.** So the answer is *as believed AT that moment*
rather than *as believed now about that moment*. That is the situation reading --
what the world looked like from there -- and it is the only one available,
because a structural walker is handed no seat. The other question is a different
relation, and it should say so in its name rather than quietly meaning something
else.

**An unanchored moment finds nothing**, for `_stored`'s reason: asking about
every moment there is would walk the whole history, and containment holds
compositionally -- `?m` can only be bound by a walk the frame could make, so a
sibling branch's moment is unreachable to bind in the first place.

**Nothing is minted.** Building the answer as a node and unifying against it
would intern it, so the harness's question would afterwards be findable as its
own answer -- the interning trap's fourth face, which `ugm.quiescence` records
paying for. Only the sign slot can need binding, so it is bound by hand, and the
check below asserts the graph stayed clean.
"""

from typing import Dict, List

from .machine import Machine
from .text import load

WORLD = """
fact +ill(paul)
rule <heal> = causes( { +ill(?x) }, { -ill(?x), +healthy(?x) } )
"""

# What a corpus would reach for, and what it actually means.
BY_LOCUS = """
rule <recovered> = implies(
    { +healthy(?x) at ?now, anc(?now, ?then), +ill(?x) at ?then },
    { +recovered(?x) } )
"""

BY_RESOLVE = """
rule <recovered> = implies(
    { +healthy(?x) at ?now, anc(?now, ?then), holds_at(ill(?x), ?then, plus) },
    { +recovered(?x) } )
"""

# The sign left open, so the walker has to bind it rather than check it.
BINDS_SIGN = """
rule <how> = implies(
    { +healthy(?x) at ?now, anc(?now, ?then), holds_at(ill(?x), ?then, ?s) },
    { +was(?x, ?s) } )
"""

# No moment bound: this would ask about the whole history.
UNANCHORED = """
rule <any> = implies( { +healthy(?x), holds_at(ill(?x), ?m, plus) },
                      { +ever(?x) } )
"""

# The proposition still generic, so there is nothing to resolve.
GENERIC = """
rule <vague> = implies(
    { +healthy(?x) at ?now, anc(?now, ?then), holds_at(ill(?y), ?then, plus) },
    { +someone(?x) } )
"""


def _run(extra: str) -> Dict[str, object]:
    m = Machine()
    kb = load(m, WORLD + extra, None, None)
    m.run(limit=400)
    seen: Dict[str, str] = {}
    for mo in m.chain.moments:
        for e in mo.delta:
            seen[m.g.show(e.proposition)] = e.sign
    return {
        "seen": seen,
        "ground_holds_at": [m.g.show(n)
                            for n in m.g.instances_of(m.chain.HOLDS_AT)
                            if not m.g.has_var(n)],
        "resolves": kb.atoms.get("holds_at") == m.chain.HOLDS_AT
        if "holds_at" in kb.atoms else None,
    }


def main() -> int:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    failing, ran = 0, 0

    def gate(name: str, ok: bool) -> None:
        nonlocal failing, ran
        ran += 1
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
        if not ok:
            failing += 1

    print(__doc__)

    locus = _run(BY_LOCUS)
    resolve = _run(BY_RESOLVE)
    signed = _run(BINDS_SIGN)
    loose = _run(UNANCHORED)
    vague = _run(GENERIC)

    print("  paul was ill, and is not any more:\n")
    for label, r, key in (("`+ill(?x) at ?then`   ", locus, "recovered(paul)"),
                          ("`holds_at(..., plus)` ", resolve, "recovered(paul)"),
                          ("sign left open        ", signed, "was(paul, +)")):
        print(f"    {label} -> {key:18} {r['seen'].get(key)}")
    print()

    gate("THE MOTIVATION, kept as a check: `at ?m` does not evaluate at m -- it "
         "binds the locus of the entry that satisfied the member, and the state "
         "holds only the winner, so the past claim is not there to match",
         locus["seen"].get("recovered(paul)") is None)
    gate("...and the control that makes that mean something: the earlier state "
         "really was `+ill(paul)`, and the later one really is a denial",
         locus["seen"].get("ill(paul)") == "-"
         and locus["seen"].get("healthy(paul)") == "+")

    gate("`holds_at` RESOLVES AT A NAMED MOMENT, so a rule can compare a "
         "proposition with its own past -- which is the thing that could not be "
         "written at all",
         resolve["seen"].get("recovered(paul)") == "+")
    gate("...and it BINDS the sign when the slot is open, rather than only "
         f"checking one that was given ({signed['seen'].get('was(paul, +)')})",
         signed["seen"].get("was(paul, +)") == "+")

    gate("AN UNANCHORED MOMENT FINDS NOTHING: without a bound `?m` this would "
         "ask about every moment there is, so it declines rather than walking "
         "the history",
         loose["seen"].get("ever(paul)") is None)
    gate("A GENERIC PROPOSITION FINDS NOTHING: `holds_at(ill(?y), ...)` with "
         "`?y` unbound has nothing to resolve, and answering would be inventing "
         "a subject",
         vague["seen"].get("someone(paul)") is None)

    gate("NOTHING IS MINTED: the walker computes its answer instead of building "
         "it as a node, so the graph holds no ground `holds_at` instance "
         "afterwards -- the interning trap's fourth face, avoided rather than "
         f"survived ({resolve['ground_holds_at']})",
         resolve["ground_holds_at"] == [])
    gate("and the NAME resolves to the chain's own node, without which the "
         "member is a fresh atom, the rule parses, and it silently matches "
         "nothing",
         resolve["resolves"] is True)

    print(f"\n{ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())

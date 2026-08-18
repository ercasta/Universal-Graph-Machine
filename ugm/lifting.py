"""Does a lesson survive a second example? Only through the world model.

    python -m ugm.lifting

`ugm.surprise` learns from one failed prediction by contrasting it with a
success: heating boiled the water and not the sand, so *sand* is what
distinguishes them. That works, and it does not transfer.

## The measurement that motivates this

Two kettles fail — one of sand, one of gravel — and the raw contrast gives two
different answers with nothing in common:

    lift=False   boiling(k2)  ['contains(_, sand)']
                 boiling(k3)  ['contains(_, gravel)']
                 COMMON  ->   []

So an agent learning this way memorises a value, then another value, for ever.
Every failure is its own case and nothing is ever concluded about a kind.

With the world model consulted — `is_a(sand, solid)`, `is_a(gravel, solid)` —
each feature is offered abstracted as well as raw, and the two failures share
one thing:

    lift=True    boiling(k2)  ['contains(_, :solid)', 'contains(_, sand)']
                 boiling(k3)  ['contains(_, :solid)', 'contains(_, gravel)']
                 COMMON  ->   ['contains(_, :solid)']

> **The ontology is not decoration. It is the difference between a lesson about
> a thing and a lesson about a kind**, and therefore between memorising and
> generalising.

## Transfer, measured on a case the learner never saw

`k5` holds pebbles. It is never heated, so it is neither a success nor a
failure and contributed nothing. The lesson covers it anyway, because pebbles
are a solid — and does not cover `k6`, which holds juice.

That is the whole claim of generalisation, and it is one lookup: does the
learned feature hold of a case that was not in the evidence?

## What decides it is the world model, not this code

The kill-probe is the check that matters. Delete one `is_a` fact — gravel stops
being a solid — and the common lesson collapses to nothing, while everything
else is unchanged. The generalisation is being done by what the corpus knows,
not by the learner being clever, and a learner that still generalised without
the ontology would be inventing the kind.

## What this does not do

**It does not promote the lesson.** The output is still a candidate. Whether
`contains(_, :solid)` should become a premise of `<boils>` is an authoring act,
and nothing here performs it.

**And one kind is not a taxonomy.** The lift is one level and one argument at a
time. A corpus rule making `is_a` transitive widens it with no change here,
which is the right place for that decision — but nothing here has measured what
a deep taxonomy costs.
"""

from typing import Dict, List

from .machine import Machine
from .surprise import common, features, learn
from .text import load

TRAINING = """
fact +heating(k1)
fact +contains(k1, water)
fact +heating(k2)
fact +contains(k2, sand)
fact +heating(k3)
fact +contains(k3, gravel)
fact +heating(k4)
fact +contains(k4, milk)

# ...and two the learner never sees act: neither heated, so neither a success
# nor a failure, and neither contributes a feature to the contrast.
fact +contains(k5, pebbles)
fact +contains(k6, juice)

rule <boils> = causes( { +heating(?k) }, { +boiling(?k) } )
rule <trust> = implies( { +says(world, ?p, minus) }, { -?p } )

say world: -boiling(k2)
say world: -boiling(k3)
"""

ONTOLOGY = """
fact +is_a(water, liquid)
fact +is_a(milk, liquid)
fact +is_a(juice, liquid)
fact +is_a(sand, solid)
fact +is_a(gravel, solid)
fact +is_a(pebbles, solid)
"""

# The same world with one claim removed: gravel is no longer known to be a
# solid. Nothing else changes.
MAIMED = ONTOLOGY.replace("fact +is_a(gravel, solid)\n", "")


def _run(src: str, lift: bool):
    m = Machine()
    kb = load(m, src, None, None)
    m.run(limit=800)
    found = learn(m, kb, lift=lift)
    return m, kb, found, common(found)


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

    src = TRAINING + ONTOLOGY
    _, _, raw, raw_common = _run(src, lift=False)
    m, kb, lifted, lift_common = _run(src, lift=True)
    _, _, maimed, maimed_common = _run(TRAINING + MAIMED, lift=True)

    print("  two kettles failed, holding different things:\n")
    for label, fs, c in (("raw   ", raw, raw_common), ("lifted", lifted, lift_common)):
        for f in fs:
            print(f"    {label}  {f.proposition:14} {f.discriminators}")
        print(f"    {label}  COMMON -> {c}\n")

    gate("THE RAW LESSON DOES NOT SURVIVE A SECOND EXAMPLE: two failures, two "
         "different answers, nothing in common -- so an agent learning this way "
         "memorises one value after another and never concludes about a kind",
         len(raw) == 2 and raw_common == []
         and sorted(d for f in raw for d in f.discriminators)
         == ["contains(_, gravel)", "contains(_, sand)"])

    gate("THROUGH THE WORLD MODEL THEY SHARE ONE THING: `contains(_, :solid)` "
         f"discriminates BOTH failures ({lift_common})",
         lift_common == ["contains(_, :solid)"])
    gate("...and the liquid kind is not proposed, because it holds of the "
         "successes -- so lifting widens what can be said without widening what "
         "is claimed",
         not any(":liquid" in d for f in lifted for d in f.discriminators))
    gate("...nor is `heating(_)`, which the rule already has and which holds of "
         "every case either way",
         "heating(_)" not in lift_common)

    # Transfer: a case that contributed nothing to the evidence.
    held_solid = features(m, kb, kb.term("k5"), lift=True)
    held_liquid = features(m, kb, kb.term("k6"), lift=True)
    print(f"  held out: k5 (pebbles) -> covered {lift_common[0] in held_solid}; "
          f"k6 (juice) -> covered {lift_common[0] in held_liquid}\n")

    gate("IT TRANSFERS: the lesson covers `k5`, which holds pebbles, was never "
         "heated, and contributed nothing to the contrast -- generalisation, "
         "measured on a case outside the evidence",
         lift_common and lift_common[0] in held_solid)
    gate("...and does NOT cover `k6`, which holds juice -- without this the "
         "transfer check would pass for a lesson that covered everything",
         lift_common and lift_common[0] not in held_liquid)

    gate("KILL-PROBE: THE WORLD MODEL IS DOING THE WORK. Delete one `is_a` fact "
         "-- gravel stops being known as a solid -- and the common lesson "
         f"collapses, with nothing else changed ({maimed_common})",
         maimed_common == [] and len(maimed) == 2)

    print(f"\n{ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())

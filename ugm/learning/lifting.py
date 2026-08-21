"""Does a lesson survive a second example? Only through the world model.

    python -m ugm.learning.lifting

ugm.surprise learns from one failed prediction by contrasting it with a
success: heating boiled the water and not the sand, so *sand* is what
distinguishes them. That works, and it does not transfer.

See docs/design/lifting.md.
"""


from ..core.machine import Machine
from .surprise import common, features, learn
from ..core.text import load

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

"""Deciding what a mention denotes -- intake, as rules.

    python -m ugm.probes.intake

ugm/rules/intake.ugm is the corpus. This runs it and holds it to the claims it
is here to make. ## Why this exists Identity in this engine has always been
decided by CONSTRUCTION. ⚠ Asked at quiet, because a count is true of a moment
-- the same reason unsupported waits for it.

See docs/design/intake.md.
"""

import sys

from ..core.machine import Machine
from ..core.text import load_file


def _read(path: str = "ugm/rules/intake.ugm", limit: int = 400):
    m = Machine()
    kb = load_file(m, path)
    m.run(limit=limit)
    return m, kb


def _holding(m, kb, rel: str):
    """Every instance of `rel` the corpus believes, as rendered text."""
    if rel not in kb.atoms:
        return []
    return sorted(m.g.show(n) for n in m.g.instances_of(kb.atoms[rel])
                  if m.holds(n) == "+")


def main() -> int:
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
    print("Four mentions, two goblins\n")

    m, kb = _read()
    for rel in ("denotes", "counted", "resolved", "unclear", "corefer"):
        for line in _holding(m, kb, rel):
            print(f"    {line}")
    print()

    resolved = _holding(m, kb, "resolved")
    denotes = _holding(m, kb, "denotes")

    # -- the reading -------------------------------------------------------
    gate("⭐⭐⭐ a COMPOUND description denotes an entity -- *the goblin you "
         "attacked three turns ago* is read through the event it describes, "
         "and the composition is ordinary rules",
         "resolved(m1, gob_a)" in resolved)
    gate("⭐ ...and a different time in the same shape of description picks a "
         "different goblin, so the reading is doing work rather than matching "
         "one fixture",
         "resolved(m2, gob_b)" in resolved)

    # -- the definite article, as a count ----------------------------------
    gate("⭐⭐⭐ *the* is EXACTLY ONE SATISFIES THIS, answered by `count` -- a "
         "claim about the set of readings, which no rule can make",
         "counted(count(denotes(m1, $g)), 1)" in _holding(m, kb, "counted"))
    gate("⭐⭐⭐ ...and a description with no time in it is satisfied by BOTH "
         "goblins, so the corpus reports an ambiguity",
         "unclear(m3)" in _holding(m, kb, "unclear"))
    gate("⚠⚠⚠ ...and NOTHING PICKS ONE. The engine deposits the number and the "
         "corpus says what it means; choosing a reading is a decision, and a "
         "silent choice here is how a front end acts on the wrong goblin",
         not any(x.startswith("resolved(m3") for x in resolved))

    # -- a name is a mention ----------------------------------------------
    gate("⭐⭐ a PROPER NAME denotes through the same relation as a description "
         "-- so no way of picking a thing out is privileged over another",
         "resolved(m4, gob_a)" in resolved)
    gate("⭐⭐⭐ ...and a name and a description COREFER, with nothing merged: "
         "two mentions, one entity, and retracting it is denying one fact",
         "corefer(m1, m4)" in _holding(m, kb, "corefer"))

    # -- the measurement the identity work was waiting for ------------------
    #
    # ⭐ The point of building this was to find out how often coreference
    # actually needs the engine's `merge`. Every coreference above is two
    # `denotes` facts about one entity: no merge, no repoint, no cascade, and
    # nothing irreversible.
    merges = m.g._merges
    gate("⭐⭐⭐ ...and the WHOLE corpus resolved four mentions, two of them "
         "coreferring, with ZERO identity merges -- so merge is for two "
         "entities turning out to be one, not for coreference",
         merges == 0)

    # -- could this have failed? -------------------------------------------
    #
    # A corpus that denoted everything to one goblin would pass most of the
    # above. Three mentions, three different answers, is what says otherwise.
    answers = {x.split(", ", 1)[1].rstrip(")") for x in resolved}
    gate("⚠ can this gate fail? -- the four mentions do not all resolve to one "
         "thing, so the reading is discriminating rather than constant",
         len(answers) > 1 and len(denotes) > len(resolved))

    # -- the labelless probe ----------------------------------------------
    #
    # ⭐⭐⭐ **The claim is that an entity needs no name, and this is what makes
    # it checkable rather than rhetorical.** A node with no name is minted, a
    # mention is pointed at it by the same rules, and the corpus resolves it
    # exactly as it resolves a named one. If anything reasoned from the name,
    # this is where it would show.
    m2, kb2 = _read()
    g = m2.g
    anon = g.entity()                       # an entity with no label at all
    for prop in (g.rel(kb2.atoms["is"], anon, kb2.atoms["goblin"]),
                 g.rel(kb2.atoms["attacked"], anon, kb2.atoms["hero"],
                       kb2.atoms["4"]),
                 g.rel(kb2.atoms["named"], anon, kb2.atoms["grish"])):
        m2.gate.write(prop, "+",
                      licence=g.rel(m2.LOADED, prop), source=m2.KB)
    m2.run(limit=400)
    anon_reads = [x for x in _holding(m2, kb2, "denotes") if "#" in x]
    print()
    print(f"    a labelless entity: {g.show(anon)}")
    for line in anon_reads:
        print(f"    {line}")
    gate("⭐⭐⭐ an entity with NO NAME is denoted, read and reasoned about "
         "exactly as a named one -- which is the check that a name is a "
         "mention rather than a privileged part of the thing",
         bool(anon_reads))

    print()
    print(f"  {ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())

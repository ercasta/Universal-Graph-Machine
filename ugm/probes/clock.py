"""A wall clock, off by default, and what turning it on actually costs.

    python -m ugm.probes.clock

Moments are ordered, not measured. pred and anc say which came first, exactly;
depth is a position rather than a duration.

See docs/design/clock.md.
"""

from typing import Dict

from ..core.machine import Machine
from ..core.text import load

CORPUS = """
fact +a(x)
rule <step> = causes( { +a($x) }, { +b($x) } )
"""

# Reads the clock and concludes STRUCTURE -- every antecedent member is
# structural, so §6's test lands it in the skeleton.
READS = """
rule <when> = implies( { asking($s), time($s, $t) }, { started($t) } )
"""

# ...and reads it into an ENTRY, which needs one member that is not structural.
# That is the version whose conclusions can differ between runs.
RECORDS = """
rule <mark> = implies( { asking($s), time($s, $t), +a($x) },
                       { +began($x, $t) } )
"""


def _run(clock: bool, extra: str = "") -> Dict[str, object]:
    m = Machine(clock=clock)
    kb = load(m, CORPUS + extra, None, None)
    m.run(limit=200)
    return {
        "entries": [(m.g.show(e.proposition), e.sign)
                    for mo in m.chain.moments for e in mo.delta],
        # ⚠ Variable-bearing instances are the RULE'S OWN PATTERN, which
        # `instances_of` returns like any other node. Counting them as stamps
        # made the moment count disagree, and reading one as a number raised.
        "stamps": [m.g.show(n) for n in m.g.instances_of(m.chain.TIME)
                   if not m.g.has_var(n)],
        "moments": len(m.chain.moments),
        "started": sorted(m.g.show(n) for n in m.g.instances_of(kb.term("started"))
                          if not m.g.has_var(n)) if "started" in kb.atoms else [],
        "resolves": kb.atoms.get("time") == m.chain.TIME if "time" in kb.atoms else None,
        "times": [int(m.g.show(m.g.member(n, 1)))
                  for n in m.g.instances_of(m.chain.TIME)
                  if not m.g.has_var(n)],
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

    off_a, off_b = _run(False), _run(False)
    on_a, on_b = _run(True), _run(True)

    print("  the same corpus, twice each way:\n")
    for label, a, b in (("clock off", off_a, off_b), ("clock on ", on_a, on_b)):
        print(f"    {label}:  moments {a['moments']}  stamps {len(a['stamps'])}  "
              f"entries identical {a['entries'] == b['entries']}  "
              f"stamps identical {a['stamps'] == b['stamps']}")
    print()

    gate("OFF BY DEFAULT: a clockless run stamps nothing, so a corpus asking "
         "for a time finds none -- which is the honest answer rather than a zero",
         off_a["stamps"] == [] and Machine().chain.clock is False)
    gate("ON: every moment carries exactly one stamp, because a moment is born "
         f"in two places and a chain stamped in one has a hole in it "
         f"({len(on_a['stamps'])} stamps, {on_a['moments']} moments)",
         len(on_a["stamps"]) == on_a["moments"])
    gate("...and the stamps do not go backwards along the chain",
         on_a["times"] == sorted(on_a["times"]))

    gate("THE CLOCK IS INERT UNTIL ASKED FOR: with it on, two runs still agree "
         "entry for entry -- a stamp is structural, not an entry, so it "
         "disturbs nothing that was reproducible before",
         on_a["entries"] == on_b["entries"] and off_a["entries"] == on_a["entries"])
    gate("...while the stamps themselves differ, so it really is a clock and "
         "not a counter dressed as one",
         on_a["stamps"] != on_b["stamps"])

    # What it costs, shown rather than asserted: a corpus that reads the clock
    # into an entry is no longer reproducible, and that is the whole price.
    rec_a, rec_b = _run(True, RECORDS), _run(True, RECORDS)
    began_a = [p for p, s in rec_a["entries"] if p.startswith("began(")]
    began_b = [p for p, s in rec_b["entries"] if p.startswith("began(")]
    gate("AND THAT IS THE PRICE: a corpus that reads the clock INTO AN ENTRY "
         f"stops being reproducible, which is the cost the default exists to "
         f"keep opt-in ({began_a} vs {began_b})",
         began_a and began_b and began_a != began_b)

    read = _run(True, READS)
    # ⚠ One per SEAT, not one per run. `asking` is minted at every seat the
    # register occupies, so a two-moment corpus reads two stamps -- and the
    # first version of this check asserted one, which is the fixture being
    # misread rather than the rule misbehaving.
    stamped = {t for t in read["times"]}
    gate("a rule can READ the clock: a stratum-0 antecedent anchored at "
         "`asking($s)` binds the seat's stamp, once per seat, and every value "
         f"it concluded is a stamp the chain actually made ({read['started']})",
         read["started"]
         and all(int(v.split("(")[1].rstrip(")")) in stamped
                 for v in read["started"]))

    # The trap, as the check that would have caught it. `atom` does not intern,
    # so the corpus's `time` and the chain's are one node only because the
    # machine's reserved-name table says so.
    gate("THE NAME RESOLVES TO THE CHAIN'S OWN NODE: without the reserved-name "
         "entry a corpus's `time` is a fresh atom, the rule parses, "
         "`is_stratum0` quietly answers no, the member matches nothing and "
         "nothing raises -- the name-identity trap, on its fifth outing",
         read["resolves"] is True)

    print(f"\n{ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())

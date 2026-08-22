"""A rule, as a fact, applied by rules. The first step of the interpretation arc.

    python -m ugm.probes.interpret

agreement writes the READ as rules and holds it to Chain.resolve. quiescence
writes *this would change nothing* as rules and holds it to
Machine._would_change.

See docs/design/interpret.md.
"""

from typing import Dict

from ..core import rules as R
from ..core.machine import Machine
from ..core.text import load

# The system layer. Provided here as a bootstrap, which is the whole claim about
# it: nothing below is privileged, and a learned one would be compared with it.
SYSTEM = """
rule <said>  = implies( { asking($s), anc($s, $d), in_delta($d, $e),
                          entry_of($e, $p, $sg) },
                        { said($p, $sg) } )

rule <unmet> = implies( { said(implies($a, $c), plus),
                          said(member($a, $p, $sg), plus),
                          -said($p, $sg) },
                        { unmet($a) } )

rule <met>   = implies( { said(implies($a, $c), plus), -unmet($a) },
                        { met($a) } )

rule <fire>  = implies( { met($a), said(member($c, $q, plus), plus),
                          +implies($a, $c) },
                        { +$q } )

rule <deny>  = implies( { met($a), said(member($c, $q, minus), plus),
                          +implies($a, $c) },
                        { -$q } )
"""

# Two rules-as-facts. The second is deliberately unsatisfiable -- `rich(anna)`
# is never claimed -- because an interpreter that ignored its premises entirely
# would pass every other check in this file.
AS_FACTS = """
fact +hungry(anna)
fact +awake(anna)

fact +implies(a1, c1)
fact +member(a1, hungry(anna), plus)
fact +member(a1, awake(anna), plus)
fact +member(c1, eats(anna), plus)
fact +member(c1, bored(anna), minus)

fact +implies(a2, c2)
fact +member(a2, hungry(anna), plus)
fact +member(a2, rich(anna), plus)
fact +member(c2, buys(anna), plus)
"""

# The same content, authored the way the engine already reads it. This is the
# gate: two representations, one answer.
NATIVE = """
fact +hungry(anna)
fact +awake(anna)

rule <n1> = implies( { +hungry(anna), +awake(anna) },
                     { +eats(anna), -bored(anna) } )
rule <n2> = implies( { +hungry(anna), +rich(anna) },
                     { +buys(anna) } )
"""

# What the two sides are compared about. Named rather than diffed whole: the
# interpreted run also concludes `said`, `met` and the convention facts, and a
# whole-state comparison would report those as a disagreement about the answer
# when they are a difference in the machinery.
WATCHED = ("eats(anna)", "bored(anna)", "buys(anna)", "hungry(anna)",
           "awake(anna)", "rich(anna)")


def _run(src: str, limit: int = 600) -> Dict[str, object]:
    m = Machine()
    kb = load(m, src, None, None)
    m.run(limit=limit)
    return {t: m.holds(kb.term(t)) for t in WATCHED}


def _old_narrowed(g, rel, want, bindings):
    """`_narrowed` as it was before the arc, so the fix can be killed.

    Byte-identical behaviour rather than a paraphrase: it treats any argument
    that is not itself a variable as a bound value, including a structure that
    carries one.
    """
    best = None
    for i, a in enumerate(g.members(want.pattern)):
        node = R.walk(g, a, bindings) if g.is_var(a) else a
        if g.is_var(node):
            continue
        bucket = g.instances_with(rel, i, node)
        if best is None or len(bucket) < len(best):
            best = bucket
    return g.instances_of(rel) if best is None else list(best)


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

    got = _run(SYSTEM + AS_FACTS)
    want = _run(NATIVE)
    print("  a rule written as facts, applied by rules:\n")
    for t in WATCHED:
        print(f"    {t:16} interpreted {str(got[t]):5}   native {str(want[t]):5}")
    print()

    gate("a rule-as-fact APPLIES: its antecedent was met and its plus "
         "conclusion is believed",
         got["eats(anna)"] == "+")
    gate("...and a MINUS conclusion is denied, so the sign in the convention "
         "is the sign in the deposit",
         got["bored(anna)"] == "-")
    gate("a rule whose antecedent is NOT met does not apply -- `rich(anna)` was "
         "never claimed, and without this check an interpreter that ignored "
         "premises altogether passes everything else here",
         got["buys(anna)"] is None)
    gate("the two representations agree, proposition for proposition",
         got == want)

    # The kill-probe. The fix is one condition in `_narrowed`, and the suite is
    # 518/0 with it and 518/0 without it -- so it is unmeasured by everything
    # that existed before this file. Reverting it here is what makes it covered.
    #
    # Restored in a `finally`, because a module-level swap that leaked would
    # make every later import of this package wrong in a way nothing prints.
    live = R._narrowed
    try:
        R._narrowed = _old_narrowed
        killed = _run(SYSTEM + AS_FACTS)
    finally:
        R._narrowed = live

    gate("KILL-PROBE: with `_narrowed` reverted, the interpreter concludes "
         f"NOTHING -- a variable-bearing structure read as an index pivot makes "
         f"every member match nothing, silently ({killed['eats(anna)']})",
         killed["eats(anna)"] is None and killed["bored(anna)"] is None)
    gate("...and the revert is the only thing that changed: the facts the "
         "corpus asserted are unaffected either way",
         killed["hungry(anna)"] == "+" and got["hungry(anna)"] == "+")

    print(f"\n{ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())

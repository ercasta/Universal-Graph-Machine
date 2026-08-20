"""A rule, as a fact, applied by rules. The first step of the interpretation arc.

    python -m ugm.probes.interpret

`agreement` writes the READ as rules and holds it to `Chain.resolve`.
`quiescence` writes *this would change nothing* as rules and holds it to
`Machine._would_change`. This is the third of that family and the one they were
building towards: **apply**, as rules, held to the loop that already applies.

## The convention

A rule-as-fact is written in the open class, and nothing here is a notation the
engine knows about:

    +implies(<ant>, <con>)              the rule
    +member(<set>, <proposition>, plus|minus)   one premise, or one conclusion

Membership rather than a moment with the entries inside it, because §5 refuses a
shape whose arity varies with how much is known about it. `plus` and `minus`
resolve to the engine's own sign nodes -- the loader says so, and that is wanted
rather than tolerated: the convention and the reification agree about what a
sign is.

## The five system rules, and what each one costs

    <said>   every proposition anything ever claimed, as STRUCTURE
    <unmet>  a premise that was never said -- so the antecedent fails
    <met>    an antecedent with no unmet premise
    <fire>   a met rule's plus conclusions, deposited
    <deny>   ...and its minus conclusions

`<said>` is the whole trick. The interpreter needs *this premise was never
claimed*, and over ENTRIES a `-` member says only *something denies it*, never
*for no `?x`* -- open-world, deliberate, and correct. `<said>` is stratum 0
(every antecedent member is structural), so §6's test lands its conclusion in
the SKELETON, and a `-` on a structural member can only mean *not derived*.
That is the same line `agreement`'s `<best>` and `quiescence`'s `<quiet>` both
rely on, reached from a third direction.

So `<unmet>` and `<met>` are stratum 0 too, and the derived strata are
`said(0) -> unmet(1) -> met(2)` -- computed, not assigned, and `strata()` would
refuse the set aloud if it were not stratifiable.

`<fire>` and `<deny>` each carry ONE entry-level member (`+implies(?a, ?c)`),
and that is not decoration. A rule whose antecedent is entirely structural
concludes structure, and structure has no sign and cannot be taken back -- so an
interpreter written wholly in stratum 0 could not deposit a belief at all. The
entry member is what buys the right to make a claim, and it is the honest price:
the rule reads an assertion, so it may make one.

## What this does not do, stated rather than discovered

**`causes` is not interpretable here.** Applying one advances the register, and
moving the register is the one irreducible part of the design (§4 item 3):
finding where to write requires a read, and a read requires somewhere to stand.
A rule is generic and a frame is anchored, so no rule can reseat. `implies`
needs no such move, which is why it is the whole of this step.

**Premises must be ground.** Unifying a pattern against the state is what the
matcher is for, and `unifies` was retired on the grounds that the matcher IS the
coverage test. A rule-as-fact carrying variables therefore needs the matcher,
not another copy of it -- which is `adopt`, not this file.

**No defeat, no preference, no refraction.** An interpreted rule is invisible to
`overrides`, to the attention table, and to `forgone`, because the loop sees only
`<fire>`. That is the standing argument against interpreting rather than
adopting, and this file is the measurement of what it costs, not a refutation.

## The defect this found, which 518 checks could not

`_narrowed` picks an index pivot from any argument that is "a value already --
an atom or a structure written in the pattern". A structure that still carries a
VARIABLE is not a value: `said(implies(?a, ?c))` asked the argument index for
the bucket of the pattern node `implies(?a, ?c)` itself, which nothing is ever
an instance against, so the bucket was empty and the member matched **nothing**.
No error and no scan -- the rule is well formed, every other member is fine, and
it silently never applies.

A corpus that only writes atoms in argument positions cannot reach it. Every
member of this interpreter has that shape, which is why the arc found it in its
first hour. `main` runs the check with the fix reverted, so the fix is covered
rather than merely made.
"""

from typing import Dict, List, Tuple

from ..core import rules as R
from ..core.machine import Machine
from ..core.text import load

# The system layer. Provided here as a bootstrap, which is the whole claim about
# it: nothing below is privileged, and a learned one would be compared with it.
SYSTEM = """
rule <said>  = implies( { asking(?s), anc(?s, ?d), in_delta(?d, ?e),
                          entry_of(?e, ?l, ?p, ?sg) },
                        { said(?p, ?sg) } )

rule <unmet> = implies( { said(implies(?a, ?c), plus),
                          said(member(?a, ?p, ?sg), plus),
                          -said(?p, ?sg) },
                        { unmet(?a) } )

rule <met>   = implies( { said(implies(?a, ?c), plus), -unmet(?a) },
                        { met(?a) } )

rule <fire>  = implies( { met(?a), said(member(?c, ?q, plus), plus),
                          +implies(?a, ?c) },
                        { +?q } )

rule <deny>  = implies( { met(?a), said(member(?c, ?q, minus), plus),
                          +implies(?a, ?c) },
                        { -?q } )
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

"""Composition, measured (§4, §19, §21).

Compilation makes a step cheaper. Composition makes the step unnecessary.

See docs/design/compose.md.
"""

from typing import List, Tuple

from ..core.chain import PLUS
from ..core.machine import Machine
from ..core.rules import CAUSES
from ..core.text import load


def _chain_corpus(n: int) -> str:
    """`s0 -> s1 -> ... -> sn`, one rule per link."""
    lines = [f"rule <r{i}> = implies( {{ +s{i}($x) }}, {{ +s{i + 1}($x) }} )" for i in range(n)]
    lines.append("fact +s0(a)")
    lines.append("")
    return chr(10).join(lines)


def _run(n: int, compose: bool) -> Tuple[int, str]:
    m = Machine()
    kb = load(m, _chain_corpus(n))
    if compose:
        # Fold the chain into one rule, left to right. Each step is a genuine
        # pattern-against-pattern unification: `s1($x')` against `s1($x'')`.
        rules = [next(r for r in m.rules.rules if r.name == f"r{i}") for i in range(n)]
        folded = rules[0]
        scaffolding = []
        for nxt in rules[1:]:
            scaffolding.append(folded)
            folded = m.rules.compose(folded, nxt)
        # Retire the constituents AND the intermediate folds. Composing left to
        # right leaves `r0+r1`, `r0+r1+r2` ... in the rule set, and each of them
        # applies: the first measurement of this showed n-1 selections instead of
        # 1, which reads exactly like composition not working.
        dead = set(rules) | set(scaffolding)
        m.rules.rules = [r for r in m.rules.rules if r not in dead]
    steps = m.run(limit=400)
    selections = sum(1 for s in steps if s.state == "applied")
    return selections, m.holds(kb.term(f"s{n}(a)"))


def _guard_inherited(where: str) -> bool:
    """A guard on either constituent must bind the composition (§21).

    The guard half of guard inheritance, which §21 recorded as missing because
    `unless` was thought to be missing. It is not: a guard is a negated
    antecedent member, and composition takes the union of the antecedents.

     Checked as BEHAVIOUR rather than as structure. A member carried into the
    composite's antecedent and not obeyed is `adopt`'s own defect -- a thing
    recorded and not acted on -- and it would read as success here.
    """
    m = Machine()
    a = "{ +p($x), -stop($x) }" if where == "first" else "{ +p($x) }"
    b = "{ +q($x) }" if where == "first" else "{ +q($x), -stop($x) }"
    kb = load(m, chr(10).join([
        f"rule <a> = implies( {a}, {{ +q($x) }} )",
        f"rule <b> = implies( {b}, {{ +r($x) }} )",
        "fact +p(guarded)", "fact +p(free)",
        "fact +stop(guarded)",   # the guard holds, so the composite must decline
        "fact -stop(free)",      # ...and is denied here, so it must apply
        "",
    ]))
    A = next(r for r in m.rules.rules if r.name == "a")
    B = next(r for r in m.rules.rules if r.name == "b")
    composed = m.rules.compose(A, B)
    if composed is None:
        return False
    m.rules.rules = [r for r in m.rules.rules if r not in (A, B)]
    m.run(limit=40)
    return (m.holds(kb.term("r(free)")) == PLUS
            and m.holds(kb.term("r(guarded)")) != PLUS)


def _dormancy_survives() -> bool:
    """A constituent that is out of the running takes the composition with it,
    or composing would be a way past it."""
    m = Machine()
    kb = load(m, chr(10).join([
        "rule <a> = implies( { +p($x) }, { +q($x) } )",
        "rule <b> = implies( { +q($x) }, { +r($x) } )",
        "fact +p(thing)",
        "",
    ]))
    A = next(r for r in m.rules.rules if r.name == "a")
    B = next(r for r in m.rules.rules if r.name == "b")
    # Dormancy is a CLAIM, deposited like any other: nothing seeds a table,
    # and the loop reads what the graph says.
    out = lambda r: m.gate.write(
        m.g.rel(m.DORMANT, r.node), "+",
        licence=m.g.rel(m.REIFIED, r.node), source=m.KB, mention=True)
    out(B)
    m.rules.inherit = []
    composed = m.rules.compose(A, B)
    if composed is None:
        return False
    # ...and the composition inherits it, which `RuleSet.compose` works out and
    # the caller deposits, because only the caller has a world to write in.
    for r in getattr(m.rules, "inherit", []):
        out(r)
    m.rules.rules = [r for r in m.rules.rules if r not in (A, B)]
    m.run(limit=40)
    # `<b>` was out; the composition must not slip past that.
    return m.holds(kb.term("r(thing)")) != PLUS


def _causes_boundary() -> Tuple[bool, bool]:
    """Is the unsound composition refused, and is the refusal exact? (§4, §14)

     A causes consequent lands in a SUCCESSOR, so the second rule's other
    premises are read where the first rule's effect holds -- one moment after
    the first rule's own premises.

    See docs/design/compose.md#causes-boundary.
    """
    src = chr(10).join([
        "rule <a> = causes(  { +p($x) },         { +q($x) } )",
        "rule <b> = implies( { +q($x), +r($x) }, { +s($x) } )",
        "rule <late> = implies( { +q($x) }, { +r($x) } )",
        "fact +p(t)", ""])
    m = Machine(); kb = load(m, src)
    by = {r.name: r for r in m.rules.rules if r.name}
    refused = m.rules.compose(by["a"], by["b"], name="ab") is None
    # ...and the derivation itself does reach it, or the fixture proves nothing.
    m.run(limit=60)
    reached = m.holds(kb.term("s(t)")) == PLUS

    m2 = Machine(); load(m2, chr(10).join([
        "rule <a> = causes(  { +p($x) }, { +q($x) } )",
        "rule <b> = implies( { +q($x) }, { +s($x) } )", ""]))
    b2 = {r.name: r for r in m2.rules.rules if r.name}
    ok = m2.rules.compose(b2["a"], b2["b"], name="ok")
    return (refused and reached), (ok is not None and ok.connective == CAUSES)


def run() -> int:
    print("composition -- steps removed, not made cheaper")
    print()
    print("    n     uncomposed    composed    same conclusion")
    failures: List[str] = []
    checked = 0
    for n in (2, 4, 8, 16):
        plain, got_plain = _run(n, compose=False)
        comp, got_comp = _run(n, compose=True)
        agree = got_plain == got_comp == PLUS
        print(f"   {n:>2}     {plain:>10}    {comp:>8}    {'yes' if agree else 'NO'}")
        checked += 1
        if not agree:
            failures.append(f"n={n}: {got_plain} vs {got_comp}")

    print()
    boundary, legal = _causes_boundary()
    print("  ...and it must not compose ACROSS a `causes`, because the second")
    print("  rule's other premises are read one moment later than the first's:")
    print(f"    a world where the derivation reaches its conclusion and a")
    print(f"    flattened rule could not:  refused = {'yes' if boundary else 'NO'}")
    print(f"    a second rule that is only the seam, so nothing moves:"
          f"  composed = {'yes' if legal else 'NO'}")
    checked += 2
    if not boundary:
        failures.append("composed across a `causes` and lost a conclusion")
    if not legal:
        failures.append("refused a sound composition across a `causes`")

    print()
    survives = _dormancy_survives()
    print(f"  a constituent that is out takes the composition with it: "
          f"{'yes' if survives else 'NO'}")
    checked += 1
    if not survives:
        failures.append("a composed rule escaped a dormancy that bound its parts")

    print()
    # ⭐⭐⭐ This used to PRINT that `unless` is not implemented, so only the
    # precedence half of guard inheritance is carried. That was false, and the
    # error was a name: `unless` is *if not*, and *if not* is an ordinary
    # negated antecedent member. Composition takes the union of the antecedents,
    # so the guard half is inherited by CONSTRUCTION. An instrument printing a
    # limitation it never tested is the same defect as a check that cannot fail.
    for where in ("first", "second"):
        got = _guard_inherited(where)
        print(f"  a guard in the {where:6} constituent binds the composition: "
              f"{'yes' if got else 'NO'}")
        checked += 1
        if not got:
            failures.append(f"a composed rule escaped its {where} constituent's guard")
    print()
    for f in failures:
        print(f"  FAIL  {f}")
    #  The COUNT, not only the failures. `0 failing` is the same output
    # whether this ran thirty checks or none -- which is how ten of them
    # were deleted by an edit and nothing noticed. `ugm.selftest` has
    # printed `291 checks` all along and is the only one that could have
    # said so.
    print(f"{checked} checks, {len(failures)} failing")
    return len(failures)


if __name__ == "__main__":
    raise SystemExit(1 if run() else 0)

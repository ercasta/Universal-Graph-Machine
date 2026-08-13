"""Composition, measured (§4, §19, §21).

    Compilation makes a step cheaper. Composition makes the step unnecessary.

§4 argues composition is the larger lever because it is **algorithmic** where
compilation is a constant factor, and because the artifact is a node rather than
an opaque blob. This runs it.

    python -m ugm.compose

Two things are measured and one is checked:

* how many selections a chain of length n costs, composed against uncomposed;
* whether the composed rule concludes the same thing;
* whether a rule that **defeats** a constituent still defeats the composition --
  §21's *a shortcut that has outlived its guards*, which here arrives at once
  rather than after a context change.
"""

from typing import List, Tuple

from .chain import PLUS
from .machine import Machine
from .rules import IMPLIES, Member
from .text import load


def _chain_corpus(n: int) -> str:
    """`s0 -> s1 -> ... -> sn`, one rule per link."""
    lines = [f"rule <r{i}> = implies( {{ +s{i}(?x) }}, {{ +s{i + 1}(?x) }} )" for i in range(n)]
    lines.append("fact +s0(a)")
    lines.append("")
    return chr(10).join(lines)


def _run(n: int, compose: bool) -> Tuple[int, str]:
    m = Machine()
    kb = load(m, _chain_corpus(n))
    if compose:
        # Fold the chain into one rule, left to right. Each step is a genuine
        # pattern-against-pattern unification: `s1(?x')` against `s1(?x'')`.
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


def _defeat_survives() -> bool:
    """A rule that defeats a constituent must defeat the composition."""
    m = Machine()
    kb = load(m, chr(10).join([
        "rule <a> = implies( { +p(?x) }, { +q(?x) } )",
        "rule <b> = implies( { +q(?x) }, { +r(?x) } )",
        "rule <veto> = implies( { +p(?x) }, { -r(?x) } )",
        "fact +p(thing)",
        "",
    ]))
    A = next(r for r in m.rules.rules if r.name == "a")
    B = next(r for r in m.rules.rules if r.name == "b")
    veto = next(r for r in m.rules.rules if r.name == "veto")
    # ⚠ The precedence is a CLAIM, deposited like any other -- it used to be a
    # Python call into a table. Nothing seeds a table any more: the arbitrator
    # reads what the graph says.
    order = lambda h, l: m.gate.write(
        m.focus, m.g.rel(m.OVERRIDES, h.node, l.node), "+",
        licence=m.g.rel(m.REIFIED, h.node), source=m.KB, mention=True)
    order(veto, B)
    composed = m.rules.compose(A, B)
    if composed is None:
        return False
    # ...and the composition inherits them, which `RuleSet.compose` works out
    # and the caller deposits, because only the caller has a world to write in.
    for higher, lower in getattr(m.rules, "inherit", []):
        order(higher, lower)
    m.rules.rules = [r for r in m.rules.rules if r not in (A, B)]
    m.run(limit=40)
    # `veto` overrode `b`; the composition must not slip past it.
    return m.holds(kb.term("r(thing)")) != PLUS


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
    survives = _defeat_survives()
    print(f"  a rule that defeats a constituent still defeats the composition: "
          f"{'yes' if survives else 'NO'}")
    checked += 1
    if not survives:
        failures.append("a composed rule escaped a defeat that bound its parts")

    print()
    print("  `unless` is not implemented in this engine, so only the precedence")
    print("  half of guard inheritance is carried. §21 records the rest.")
    print()
    for f in failures:
        print(f"  FAIL  {f}")
    # ⚠ The COUNT, not only the failures. `0 failing` is the same output
    # whether this ran thirty checks or none -- which is how ten of them
    # were deleted by an edit and nothing noticed. `ugm.selftest` has
    # printed `291 checks` all along and is the only one that could have
    # said so.
    print(f"{checked} checks, {len(failures)} failing")
    return len(failures)


if __name__ == "__main__":
    raise SystemExit(1 if run() else 0)

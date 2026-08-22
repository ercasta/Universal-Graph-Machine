"""Is every bundled rule -- and every shipped answerer -- load-bearing? (§20)

Every gate must delete each rule of the thing it checks, one at a time, and
report any rule the fixture cannot kill. A rule no fixture can kill is a rule
the fixture is not testing.

See docs/design/bundle.md.
"""

import contextlib
import io
from typing import Callable, List, Optional

from ..core.chain import PLUS
from ..core.machine import Machine


def _failures(mutate: Optional[Callable[[Machine], None]] = None) -> int:
    """Run the whole selftest against a mutated machine, and count failures.

    ⚠ A count of -1 means the runner RAISED rather than failing, and it is
    reported as `raised` rather than folded into a number. The mutation is still
    load-bearing -- more so -- but the count would be a lie: the run stopped at
    the first check that could not survive the absence, and every check after it
    went unreported. §20's own lesson from the other side, where three checks
    crashed the runner and the repair was that a runner has to be able to say
    False about an absence.
    """
    from .. import selftest

    original = Machine.__init__

    def patched(self) -> None:  # type: ignore[no-untyped-def]
        original(self)
        if mutate is not None:
            mutate(self)

    Machine.__init__ = patched  # type: ignore[method-assign]
    selftest._results.clear()
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            selftest.main()
    except Exception:
        return -1
    finally:
        Machine.__init__ = original  # type: ignore[method-assign]
    return sum(1 for _, _, ok in selftest._results if not ok)


def _drop_rule(name: str) -> Callable[[Machine], None]:
    def mutate(m: Machine) -> None:
        m.rules.rules = [r for r in m.rules.rules if r.name != name]
    return mutate


def _remove_answerer(name: str) -> Callable[[Machine], None]:
    def mutate(m: Machine) -> None:
        m.answerers = [a for a in m.answerers if a.name != name]
    return mutate


def _obeyed_when_denied(name: str) -> bool:
    """What a CORPUS can do: `fact -answers(<M>, ask)`. Was it obeyed?

    ⚠ Measured LOCALLY, on one fixture, and the first version measured it by
    running the whole selftest with the binding denied -- which reported every
    answerer as costly and meant nothing. The suite contains checks that merely
    *inspect* the bindings, so denying any of them fails those checks whether or
    not the agent lost anything. **A mutation instrument can only read a
    mutation the fixture does not already talk about.**

    The direct question needs no fixture knowledge: a denial that was refused
    leaves `refused(answers(<M>, ask), -, standing(<M>))` on the record, and one
    that was obeyed leaves nothing. So this reports whether the carve-out held,
    which is the property, rather than what it happened to cost here.
    """
    from ..core.text import load

    m = Machine()
    a = next(x for x in m.answerers if x.name == name)
    load(m, chr(10).join([
        "rule <boil> = implies( { +heat($x, $w), +water($w) }, { +boiling($w) } )",
        "rule <ask-root> = implies( { +goal($w) }, { +root($w) } )",
        "fact standing(<ask-root>)",
        f"fact -answers(<{name}>, {m.g.show(a.request)})",
        "fact +water(kettle)", "fact +goal(boiling(kettle))", ""]))
    m.run(limit=400)
    binding = m.g.rel(m.ANSWERS, a.node, a.request)
    return not any(
        m.holds(n) == PLUS and m.g.member(n, 0) == binding
        for n in m.g.instances_of(m.REFUSED)
    )


def run() -> int:
    proto = Machine()
    names = [r.name for r in proto.bundle]
    answerers = [
        (a.name, bool(proto._claims(proto.g.rel(proto.STANDING, a.node))))
        for a in proto.answerers
    ]

    baseline = _failures()
    print("§20 -- is every bundled rule load-bearing?")
    print(f"  baseline        {baseline} failing")
    if baseline:
        print("  the selftest is not green; fix that before reading anything below")
        return baseline

    blind: List[str] = []
    for name in names:
        n = _failures(_drop_rule(name))
        shown = "raised" if n < 0 else f"{n} failing"
        print(f"    {name:28} {shown:>10}" + ("" if n else "   <-- BLIND"))
        if n == 0:
            blind.append(name)

    # -- and the same question of the apparatus's own answerers ------------
    # Two columns, because they are two questions.
    # → docs/design/bundle.md#and-the-same-question-of-the-apparatus-s-own
    print()
    print("§21 -- and every shipped ANSWERER? (its binding is a fact, so a corpus")
    print("       can ask this too -- `answers(<M>, ask)`)")
    print(f"    {'':12} {'removed':>9}   {'-answers(...)':13}  intended")
    wrong: List[str] = []
    show = lambda n: "raised" if n < 0 else str(n)
    for name, standing in answerers:
        removed = _failures(_remove_answerer(name))
        obeyed = _obeyed_when_denied(name)
        print(f"    {name:12} {show(removed):>9}   "
              f"{'obeyed' if obeyed else 'REFUSED':13}  "
              f"{'a corpus may retire it' if not standing else 'standing'}")
        if removed == 0:
            wrong.append(f"{name} (removing it costs nothing -- BLIND)")
        if standing and obeyed:
            wrong.append(f"{name} (standing, but a corpus turned it off)")
        if not standing and not obeyed:
            wrong.append(f"{name} (retirable, but the denial was refused)")

    print()
    for w in wrong:
        print(f"  ⚠ {w}")
    print(f"{len(names)} bundled rules, {len(names) - len(blind)} exercised; "
          f"{len(answerers)} answerers, {len(wrong)} anomalies")
    return len(blind) + len(wrong)


if __name__ == "__main__":
    raise SystemExit(1 if run() else 0)

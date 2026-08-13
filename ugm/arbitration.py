"""Does the chooser agree with the list it replaced?

`Machine._choose` is an optimisation of a semantics, and §20's floor gate is
this design's standing answer to that: the slow definition stays, so the fast
one can be **held to it** rather than trusted. `stratum0` does it for the read;
this does it for the move.

The slow definition is `Machine._materialise` -- every live application,
defeated, filtered by `_passed_up` and `_would_change`, in the order arbitration
read them -- followed by `rules.arbitrate`. Nothing in the loop calls it.

Three things are compared on **every tick of every fixture in the suite**, and
they are three because agreeing about the move is not the same as agreeing about
the record:

    move      the application `arbitrate` would have chosen
    doubt     the rival RULES recorded as `close` to it
    forgone   the rules recorded as passed up, and for which want

⚠ What this cannot check is the fixtures it is given. A chooser that is wrong
only where two rules tie under `supersedes`, or only inside a supposition, is
wrong invisibly if nothing here does that -- so the tally prints how many ticks
had a real choice to make, and a run where that is small is a run that measured
very little. That is the homogeneous-fixture trap, and the count is the only
defence against it.
"""

import contextlib
import io

from .machine import Machine
from .rules import Situation, arbitrate

_tally = {
    "ticks": 0,
    "with_a_choice": 0,
    "with_a_rival": 0,
    "move": 0,
    "doubt": 0,
    "forgone": 0,
}
_examples = []


def _slow(machine, proposed, keys):
    """The move, the doubt and the forgone, computed the long way."""
    state = Situation(machine.g, machine._state())
    everything = machine._materialise(proposed, state)
    rank = lambda r: machine._rank(r, keys)
    chosen = arbitrate(machine.rules, everything, rank)
    if chosen is None:
        return None, frozenset(), frozenset()
    best = rank(chosen.rule)
    doubt = frozenset()
    if best[0] != 0:
        doubt = frozenset(
            a.rule.node for a in everything
            if a.rule is not chosen.rule and machine._close(rank(a.rule), best)
        )
    wants = machine._wants(chosen)
    forgone = frozenset()
    if wants and not machine._claims(
        machine.g.rel(machine.STANDING, chosen.rule.node)
    ):
        forgone = frozenset(
            (a.rule.node, w)
            for a in everything
            if a.rule is not chosen.rule
            and not machine._claims(machine.g.rel(machine.STANDING, a.rule.node))
            for w in wants & machine._wants(a)
        )
    return chosen, doubt, forgone


def _fast_record(machine, chosen, rivals, sharing, keys):
    """The same three, read off what `_choose` returned."""
    if chosen is None:
        return None, frozenset(), frozenset()
    rank = lambda r: machine._rank(r, keys)
    best = rank(chosen.rule)
    doubt = frozenset()
    if best[0] != 0:
        doubt = frozenset(
            a.rule.node for a in rivals
            if a.rule is not chosen.rule and machine._close(rank(a.rule), best)
        )
    wants = machine._wants(chosen)
    forgone = frozenset()
    if wants and not machine._claims(
        machine.g.rel(machine.STANDING, chosen.rule.node)
    ):
        forgone = frozenset(
            (a.rule.node, w)
            for a in sharing
            if a.rule is not chosen.rule
            and not machine._claims(machine.g.rel(machine.STANDING, a.rule.node))
            for w in wants & machine._wants(a)
        )
    return chosen, doubt, forgone


def install() -> None:
    original = Machine._choose

    def compared(self, proposed, keys):
        chosen, rivals, sharing = original(self, proposed, keys)
        _tally["ticks"] += 1
        # ⚠ The slow path is run AFTER the fast one and reads the same state,
        # which is only legitimate because neither writes: `_materialise`,
        # `_passed_up` and `_would_change` are reads, and `_would_change`'s
        # cache is keyed on what it read. If any of them ever deposits, this
        # instrument stops being an observer and starts being a second agent.
        s_chosen, s_doubt, s_forgone = _slow(self, proposed, keys)
        f_chosen, f_doubt, f_forgone = _fast_record(
            self, chosen, rivals, sharing, keys
        )
        if s_chosen is not None:
            _tally["with_a_choice"] += 1
        if s_doubt or s_forgone:
            _tally["with_a_rival"] += 1
        if f_chosen is not s_chosen:
            _tally["move"] += 1
            if len(_examples) < 4:
                _examples.append(
                    "move: fast="
                    + (f_chosen.rule.name if f_chosen else "None")
                    + " slow="
                    + (s_chosen.rule.name if s_chosen else "None")
                )
        if f_doubt != s_doubt:
            _tally["doubt"] += 1
        if f_forgone != s_forgone:
            _tally["forgone"] += 1
        return chosen, rivals, sharing

    Machine._choose = compared


def main() -> int:
    import sys

    # ⚠ Section signs and warning marks on a cp1252 console. An instrument that
    # dies printing its own prose reports nothing, and this repo has thrown away
    # a turn's work to exactly that.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    install()
    from . import selftest

    with contextlib.redirect_stdout(io.StringIO()) as buf:
        selftest.main()
    suite = buf.getvalue().strip().splitlines()[-1]

    print(__doc__)
    print(f"  the suite, under the comparison: {suite}")
    print()
    print(f"  {_tally['ticks']:6} ticks compared")
    print(f"  {_tally['with_a_choice']:6} of them made a move")
    print(f"  {_tally['with_a_rival']:6} had a rival to record -- doubt or forgone")
    print()
    disagreed = _tally["move"] + _tally["doubt"] + _tally["forgone"]
    for what in ("move", "doubt", "forgone"):
        print(f"  {_tally[what]:6} disagreements about the {what}")
    for e in _examples:
        print(f"         {e}")
    print()
    if _tally["with_a_rival"] == 0:
        print("  ⚠ NOTHING had a rival: this run compared a chooser with nothing to choose.")
        return 1
    print(f"  {disagreed} disagreements")
    return 1 if disagreed else 0


if __name__ == "__main__":
    raise SystemExit(main())

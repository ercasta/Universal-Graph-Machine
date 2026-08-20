"""Does what the agent keeps agree with what the walk says?

Machine._kept is an optimisation of a semantics, and §20's floor gate is this
design's standing answer to that: the slow definition stays, so the fast one
can be held to it rather than trusted. ⚠ What this cannot check is the fixtures
it is given -- the homogeneous-fixture trap, recorded twice in this repo.

See docs/design/state.md.
"""

import contextlib
import io

from ..core.chain import PLUS
from ..core.machine import Machine
from ..core.rules import Situation, current_state


_tally = {
    "looks": 0,
    "with_a_supersession": 0,
    "with_a_goal": 0,
    "state": 0,
    "index": 0,
    "mentions": 0,
}
_examples = []


def _slow_state(m):
    """§4's walk, filtered by what is out of mind. Newest-first."""
    hidden = m._out_of_mind()
    return [
        e
        for e in current_state(m.chain, m.focus.topic, m.focus.seat)
        if e.source not in hidden
    ]


def _note(what, detail):
    _tally[what] += 1
    if len(_examples) < 6:
        _examples.append(f"{what}: {detail}")


def install() -> None:
    original = Machine._kept
    def compared(self):
        cache = original(self)
        # ⚠ The comparison reads the state, and reading the state is what is
        # being compared, so the instrument stands aside while it is running or
        # it is measuring its own recursion.
        if _tally.get("inside"):
            return cache
        _tally["inside"] = 1
        try:
            compare(self, cache)
        finally:
            _tally["inside"] = 0
        return cache

    def compare(self, cache):
        _tally["looks"] += 1
        slow = _slow_state(self)
        fast = cache["sit"].entries
        # A supersession is the case the maintained state has to get right and
        # an append-only fixture cannot exercise: fewer entries than claims made
        # about this seat means something replaced something.
        if len(slow) < len({e.proposition for e in self.focus.seat.delta}):
            _tally["with_a_supersession"] += 1
        if any(
            e.sign == PLUS and self.g.relation_of(e.proposition) is self.GOAL
            for e in slow
        ):
            _tally["with_a_goal"] += 1

        if [e.node for e in fast] != [e.node for e in slow]:
            _note(
                "state",
                f"kept {len(fast)} entries, the walk says {len(slow)}"
                if len(fast) != len(slow)
                else "same entries, different order",
            )
        # The index, asked of every key either side has an opinion about -- the
        # bare-variable bucket, the per-relation ones, and the per-argument
        # ones a join narrows to. ⚠ Asked through bucket, never off _by, and
        # the difference is the whole value of the column: a first version
        # compared the dicts directly and could not see one...
        # →
        # docs/design/state.md#the-index-asked-of-every-key-either-side-has-an
        reference = Situation(self.g, slow)
        for k in set(cache["sit"]._by) | set(reference._by):
            a = [e.node for e in cache["sit"].bucket(k)]
            b = [e.node for e in reference.bucket(k)]
            if a != b:
                _note("index", f"bucket {k[:2]}: kept {len(a)}, walk {len(b)}")
                break

        # The fourth, and it is the quietest of the four: relations_of is read
        # to LIFT a rule, so a stale count makes a worse shortlist and never a
        # wrong conclusion. ⚠ The COUNTS, not the relations, and the difference
        # is whether this column measures anything at all.
        # → docs/design/state.md#the-fourth-and-it-is-the-quietest-of-the-four
        for node, held in list(cache["sit"]._rels.items()):
            walk = reference._rels.get(node, {})
            if held != walk:
                rel = next((r for r in set(held) | set(walk)
                            if held.get(r) != walk.get(r)), None)
                _note("mentions",
                      f"{self.g.show(node)} under {self.g.show(rel)}: kept "
                      f"{held.get(rel, 0)}, the walk says {walk.get(rel, 0)}")
                break
        else:
            for node in reference._rels:
                if node not in cache["sit"]._rels:
                    _note("mentions", f"{self.g.show(node)}: kept nothing, "
                                      "the walk says it is spoken of")
                    break

        return cache

    Machine._kept = compared


def main() -> int:
    import sys

    # ⚠ Section signs and warning marks on a cp1252 console. An instrument that
    # dies printing its own prose reports nothing.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    install()
    from .. import selftest

    with contextlib.redirect_stdout(io.StringIO()) as buf:
        selftest.main()
    suite = buf.getvalue().strip().splitlines()[-1]

    print(__doc__)
    print(f"  the suite, under the comparison: {suite}")
    print()
    print(f"  {_tally['looks']:6} looks at the state compared")
    print(f"  {_tally['with_a_supersession']:6} of them after something was superseded")
    print(f"  {_tally['with_a_goal']:6} of them with a live goal")
    print()
    disagreed = _tally["state"] + _tally["index"] + _tally["mentions"]
    for what in ("state", "index", "mentions"):
        print(f"  {_tally[what]:6} disagreements about the {what}")
    for e in _examples:
        print(f"         {e}")
    print()
    if _tally["with_a_supersession"] == 0 or _tally["with_a_goal"] == 0:
        print("  ⚠ A column had nothing to measure: this run compared very little.")
        return 1
    print(f"  {disagreed} disagreements")
    return 1 if disagreed else 0


if __name__ == "__main__":
    raise SystemExit(main())

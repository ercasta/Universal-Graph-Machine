"""Does what the agent keeps agree with what the walk says?

`Machine._kept` is an optimisation of a semantics, and §20's floor gate is this
design's standing answer to that: the slow definition stays, so the fast one can
be **held to it** rather than trusted. `stratum0` does it for the read,
`ugm.arbitration` for the move; this does it for the state.

The slow definition is §4's walk -- `rules.current_state`, every proposition the
chain has ever claimed on this branch, each one `resolve`d, newest-first --
filtered by what is out of mind. Nothing in the loop calls it any more.

Three things are compared on **every look at the state, in every fixture in the
suite**, and they are three because a state can be right while what is read off
it is wrong:

    state     the entries, IN ORDER -- §18's *the most recent wins* rests on it
    index     what `Situation.candidates` answers, per sign and relation
    keys      `_in_play`: what the situation is about, which orders arbitration

⚠ The three fail in different ways and only the first is loud. A wrong state
concludes from a premise that was denied; a wrong index silently stops a rule
applying; wrong keys only make a worse choice, which no fixture asserting an
outcome can see. That is why the keys are compared here rather than left to the
checks that read them.

⚠ What this cannot check is the fixtures it is given -- the homogeneous-fixture
trap, recorded twice in this repo. A state that is wrong only after a denial is
wrong invisibly if nothing denies anything, so the tally prints how many looks
followed a supersession and how many had a live goal, and a run where either is
small is a run that measured very little.

Kill-probed five ways, and each lands in its own column. The last row is the
one that justifies the instrument existing at all:

| break | the suite | state | index | keys |
|---|---|---|---|---|
| never drop a superseded entry | 2 | 806 | 806 | 0 |
| never decrement a goal's key | 1 | 0 | 0 | 8 |
| never invalidate a bucket's read | 29 | 0 | 3,884 | 0 |
| rebuild the state newest-first | 6 | 6,456 | 6,456 | 0 |
| **one key cache for every seat** | **0** | 0 | 0 | **1,597** |

⭐ The suite cannot see the last one, and that is not a gap in the fixtures: a
wrong key set makes a worse choice, and every fixture here asserts an outcome
that the loop reaches anyway. Nothing that asserts what the agent concluded can
see what it was thinking about while it concluded it.
"""

import contextlib
import io

from .chain import PLUS
from .machine import Machine
from .rules import Member, Situation, current_state


class _Ask:
    """A stand-in graph, so a bucket can be asked for through the read path.

    `candidates` takes the pattern's two properties off the graph, and this
    instrument has a bucket rather than a pattern. Minting a variable to ask
    with would be an instrument depositing in the graph it is measuring -- node
    identities are the arbitration stamps -- so it answers the two questions
    directly and touches nothing.
    """

    def __init__(self, is_var: bool, rel) -> None:
        self._var, self._rel = is_var, rel

    def is_var(self, pattern) -> bool:
        return self._var

    def relation_of(self, pattern):
        return self._rel

_tally = {
    "looks": 0,
    "with_a_supersession": 0,
    "with_a_goal": 0,
    "state": 0,
    "index": 0,
    "keys": 0,
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


def _slow_keys(m, state):
    """What `_in_play` said before it was accumulated: a scan of the seat's
    whole delta, and a scan of the whole state for live goals."""
    out = set()
    for e in m.focus.seat.delta:
        rel = m.g.relation_of(e.proposition)
        if rel is not None:
            out.add(rel)
    for s in state:
        if s.sign == PLUS and m.g.relation_of(s.proposition) is m.GOAL:
            wanted = m.g.member(s.proposition, 0)
            out.add(wanted)
            rel = m.g.relation_of(wanted)
            if rel is not None:
                out.add(rel)
    return out


def _note(what, detail):
    _tally[what] += 1
    if len(_examples) < 6:
        _examples.append(f"{what}: {detail}")


def install() -> None:
    original = Machine._kept
    # ⚠⚠⚠ **The SHIPPED `_in_play`, captured now.** The suite contains a check
    # that measures `_in_play` five ways by swapping the method out, and read
    # through `self`, this instrument compared each deliberate mutant against
    # the definition -- 90 disagreements, every one of them a fixture doing its
    # job. `ugm.bundle`'s trap from the other side: *a comparison instrument
    # cannot read a mutation the fixture already talks about.*
    in_play = Machine._in_play

    def compared(self):
        cache = original(self)
        # ⚠ The comparison reads the state, and reading the state is what is
        # being compared: `_in_play` asks for the keys off this very cache. So
        # the instrument stands aside while it is running, or it is measuring
        # its own recursion.
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
        # The index, asked of every key either side has an opinion about --
        # including the bare-variable bucket, which is the one a rule reading a
        # channel's report uses and the one an index is most tempted to skip.
        #
        # ⚠ Asked through `candidates`, never off `_by`, and the difference is
        # the whole value of the column: a first version compared the buckets
        # directly and could not see an index read back in the wrong ORDER --
        # which is exactly the mistake §18's tiebreak makes expensive, and
        # exactly what a comparison against internals is blind to.
        reference = Situation(self.g, slow)
        for k in set(cache["sit"]._by) | set(reference._by):
            sign, rel = k
            ask = _Ask(rel is Situation.ANY, rel)
            want = Member(sign, None)
            a = [e.node for e in cache["sit"].candidates(ask, want)]
            b = [e.node for e in reference.candidates(ask, want)]
            if a != b:
                _note("index", f"bucket {sign}{rel}: kept {len(a)}, walk {len(b)}")
                break

        f, sl = in_play(self), _slow_keys(self, slow)
        if f != sl:
            _note("keys", "extra=%s missing=%s" % (
                sorted(self.g.show(k) for k in f - sl),
                sorted(self.g.show(k) for k in sl - f)))
        return cache

    Machine._kept = compared


def main() -> int:
    import sys

    # ⚠ Section signs and warning marks on a cp1252 console. An instrument that
    # dies printing its own prose reports nothing.
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
    print(f"  {_tally['looks']:6} looks at the state compared")
    print(f"  {_tally['with_a_supersession']:6} of them after something was superseded")
    print(f"  {_tally['with_a_goal']:6} with a live goal, so the keys say something")
    print()
    disagreed = _tally["state"] + _tally["index"] + _tally["keys"]
    for what in ("state", "index", "keys"):
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

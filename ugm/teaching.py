"""Bootstrapping the table from use. (the author's design)

    python -m ugm.teaching

> A human is the first, manual user of the KB.

Not a labelling task run beside the system: the ordinary first use of a corpus,
by a person who steps it and picks the next rule. They are doing exactly what
the table will later do, so what they leave behind is the table. The learning is
the residue of the use, which is this repo's recurring shape.

Two signals come out of that use and only one of them is calibration:

    the wrong order        a buff -- this rule should have come first here
    none of these fits     a MISSING RULE, which no calibration can supply

The second is the more valuable one early, and only manual use surfaces it. This
file is about the first.

## Why there is a teacher here that is not a human

The reflex experiment in `ugm.attention` settled what a demonstration may
produce: damping every rule that was tried and missed cost 125 conclusions,
because *tried and missed* is not evidence a rule is unimportant -- it is
evidence it did not apply **in that state**. So a demonstration has to produce
something conditional, and the smallest conditional thing that carries a
sequence is a bigram on the rule that just applied:

    rule <A> = ...
      after => boost(<R>, n)          after A, prefer R

...with a query added later, by anti-unification, when the same `A` is taught
towards different `R` in different situations.

**And the mechanism can be validated with no human at all.** The shipped loop's
arbitration already picks a move at every step, deterministically, over the full
option set. Let it teach; then ask whether the table loop, calibrated from its
sequence, makes the same moves it does. If bootstrapping cannot imitate a
teacher that is right by construction, it will not learn from a person either.

Three things are measured, and they are the three claims:

    agreement    does the table pick what the teacher picked
    matched/move does the cost claim move (29.6 uncalibrated)
    conclusions  does anything get lost
"""

import os
from typing import Dict, List, Optional, Tuple

from .attention import (
    SETTLE, Table, _fight, _load, _state, run,
)
from .machine import Machine
from .rules import Application, Situation, arbitrate
from .text import load


def teacher(m: Machine, table: Table, window, state: Situation):
    """The shipped arbitration, as a gold teacher.

    It chooses over the FULL option set -- `_materialise` is the slow definition
    `ugm.arbitration` holds the fast one to -- rather than over the window, so
    it is a genuine teacher and not a re-ranking of what the table already
    liked. Offline cost, which is what a teacher is allowed.
    """
    everything = m._materialise(m.rules.rules, state)
    if not everything:
        return window[0] if window else None
    keys = m._in_play()
    chosen = arbitrate(m.rules, everything, lambda r: m._rank(r, keys))
    return chosen or (window[0] if window else None)


class Lesson:
    """What the use left behind: which rule was picked after which."""

    def __init__(self) -> None:
        self.pairs: Dict[Tuple[str, str], int] = {}
        self.agreed = 0
        self.moves = 0
        self.last: Optional[str] = None

    def watching(self, m: Machine, table: Table, window, chosen, tick: int):
        self.moves += 1
        # By RULE, not by application identity: the teacher builds its own
        # `Application` objects from `_materialise`, so `is` compares two
        # objects that describe the same move and answers no every time. It
        # reported 0/149 before this line was fixed, which reads as *the table
        # is never right* and meant *the comparison cannot be right*.
        if window and chosen.rule is window[0].rule:
            self.agreed += 1
        name = chosen.rule.name or "?"
        if self.last is not None:
            self.pairs[(self.last, name)] = self.pairs.get((self.last, name), 0) + 1
        self.last = name

    def posts(self, m: Machine, weight: int = 3):
        """The bigrams, as postconditions on the rule that ran first.

        No query, deliberately: this is stage one, and a bigram that turns out
        to be wrong in some situations is what earns a query. Attached to the
        rule rather than kept beside it, so the calibration is in the corpus and
        `ugm.attention` needs to know nothing about learning.
        """
        by_name = {r.name: r for r in m.rules.rules if r.name}
        added = 0
        for (first, then), seen in self.pairs.items():
            a, r = by_name.get(first), by_name.get(then)
            if a is None or r is None or a is r:
                continue
            a.posts = tuple(a.posts) + (((), ((r.node, weight * min(seen, 3)),), False),)
            added += 1
        return added


def _machine(name: str) -> Machine:
    m = _fight(False) if name == "dungeon" else _load(name)
    load(m, SETTLE)
    return m


def measure(name: str, limit: int = 400) -> dict:
    """One teacher run gives both the lesson and the target; then the table
    loop runs twice, uncalibrated and calibrated, against it."""
    gold_m = _machine(name)
    lesson = Lesson()
    gold = run(gold_m, limit=limit, chooser=teacher, watch=lesson.watching)

    out = {
        "corpus": name, "pairs": len(lesson.pairs),
        "gold_moves": gold.ticks, "gold_state": gold.state,
        # How often the teacher wanted what the table's own order offered
        # first. This is the ceiling the calibration is trying to reach, and if
        # it is already high the corpus has nothing to teach.
        "teacher_took_the_top": lesson.agreed,
    }
    for label, learn in (("before", False), ("after", True)):
        m = _machine(name)
        added = lesson.posts(m) if learn else 0
        r = run(m, limit=limit)
        same = sum(1 for a, b in zip(r.applied, gold.applied) if a == b)
        out[label] = {
            "posts": added,
            "moves": r.ticks,
            "matched_per_move": r.tried / max(1, len(r.windows)),
            "prefix_agreement": same,
            "conclusions": len(r.state),
            "lost": len(gold.state - r.state),
            "doubts": r.doubts,
        }
    return out


def main() -> int:
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(__doc__.split("## Why there is a teacher")[0].strip())
    print()
    bad = 0
    for name in ("quest-p1.ugm", "dungeon"):
        c = measure(name)
        print(f"  {c['corpus']}  -- {c['pairs']} bigrams from one taught run; "
              f"the teacher took the table's top choice "
              f"{c['teacher_took_the_top']}/{c['gold_moves']} times")
        for label in ("before", "after"):
            d = c[label]
            print(f"    {label:6} {d['moves']:>4} moves  "
                  f"{d['matched_per_move']:>6.1f} matched/move  "
                  f"{d['prefix_agreement']:>4} moves agree with the teacher  "
                  f"{d['conclusions']:>4} conclusions, {d['lost']} lost  "
                  f"{d['doubts']} doubts")
        if c["after"]["lost"] > c["before"]["lost"]:
            bad += 1
    return bad


if __name__ == "__main__":
    raise SystemExit(main())

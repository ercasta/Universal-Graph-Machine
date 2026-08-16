"""A fight where the players are their own agents. (the author's design)

    python -m ugm.melee

`ugm.dungeon` is one machine that plays everybody. This is the same fight with
the players outside it: a DM that adjudicates and a player that decides, two
chains, nothing shared, and what crosses between them is an **utterance** --
rendered text re-read in the hearer's own name scope, which is `ugm/table.py`'s
whole design.

## Why this exists, and it is not multi-agent for its own sake

`ugm.teaching` reached a wall that was the corpus rather than the mechanism. A
fight is a **pipeline** -- swing, to-hit, damage, wound -- so the previous move
nearly determines the next one, a lesson keyed on the predecessor is almost
sufficient, and the ranking-time triggers had nothing left to say: 93
reorderings that changed no outcome.

A player is not a pipeline. Every rule in `melee-p1.ugm` is triggered by the
same thing -- *the DM just told me something* -- and which of them is right
depends on the state: how hurt I am, whether I still have a potion, whether the
goblin is bleeding. `<quaff>` and `<run>` differ by one fact. That is the shape a
reranker exists for and the shape a bigram cannot express, so this is the
fixture the last measurement was missing.

## What is asymmetric here, deliberately

The DM plays the goblin. A monster has no agent of its own, and that is not a
shortcut: it is the difference between a participant and a device, and it means
the two corpora have genuinely different jobs -- one adjudicates, one chooses.
The claim worth testing is that the same machinery, taught from the same play,
ends up with differently shaped attention in the two of them.
"""

import os
import random
import sys
from typing import Dict, List, Tuple

from .table import Spec, TOOLS, Table

DICE = {"d4": 4, "d6": 6, "d20": 20}
HERE = os.path.dirname(__file__)


def _corpus(name: str) -> str:
    with open(os.path.join(HERE, "rules", name), "r", encoding="utf-8") as fh:
        return fh.read()


# The dice are the DM's, and the seed is on the record: a fight nobody can
# replay is a fight nobody can argue about. ⚠ Module level, because a Spec
# crosses a process boundary and a closure would not arrive.
_RNG = random.Random(7)


def _roll(mach, frame, e):
    die, _what, _when = mach.g.members(e.proposition)
    sides = DICE.get(mach.g.show(die))
    if sides is None:
        return None
    return mach.g.atom(str(_RNG.randint(1, sides)))


def _calc(op, a, b):
    op, a, b = str(op), str(a), str(b)
    if not (a.isdigit() and b.isdigit()):
        return None
    if op == "add":
        return int(a) + int(b)
    if op == "sub":
        # The clamp, and it is a rule of the game stated in Python because the
        # surface cannot write a negative numeral -- `ugm.dungeon` records the
        # same debt.
        return max(0, int(a) - int(b))
    return None


def _beats(a, b):
    a, b = str(a), str(b)
    if not (a.isdigit() and b.isdigit()):
        return None
    return "yes" if int(a) >= int(b) else "no"


TOOLS["roll"] = _roll
TOOLS["calc"] = _calc
TOOLS["beats"] = _beats

DM_TOOLS = (("dice", "roll", "roll"),)
DM_COMPUTES = (("calc", "calc"), ("beats", "beats"))
# The player gets the comparisons and no dice: it may weigh what it was told,
# and it may not roll. Whose dice they are is the whole of a DM's authority.
P1_COMPUTES = (("beats", "beats"), ("calc", "calc"))


# What a coach would say, written by hand -- the target (3) has to hit.
#
# ⚠ BOTH HALVES of the removed guard have to move into the score, and the first
# draft of this only had one. Boosting `<quaff>` when nearly dead says nothing
# about full health: with every arm at the floor, declaration order still put
# `<quaff>` first and the coached player drank at 10 hit points exactly like the
# untaught one. A guard was a condition AND its complement; a score has to be
# told both.
COACHING = """
when { +yours(?n), beats(?n, 5) as yes } => boost(<trade>, 8), damp(<quaff>, 4), damp(<run>, 6)
when { +yours(?n), beats(4, ?n) as yes } => boost(<quaff>, 8)
when { +bleeding(?foe) } => boost(<press>, 8), damp(<run>, 4)
after <guard> { +whiffed(p1, ?foe) } => boost(<trade>, 4)
"""

# The doubt-settling rule the table loop needs: when two candidates are close,
# the doubt is deposited and this is what answers it.
SETTLING = """
rule <settle-doubt> = implies( { +close(?a, ?b) }, { +settled(?a, ?b) } )
frozen after <settle-doubt> => boost(?a, 1)
"""


def scenario(loop: str = "shipped", coaching: bool = False) -> Tuple[Spec, ...]:
    return (
        # ⚠ A bounded limit, not the default 2000. An agent that loops runs to
        # its limit before the round ends, so a runaway in one corpus stalls the
        # whole table -- and this corpus had three of them before the locus
        # discipline was applied consistently.
        Spec("dm", _corpus("melee-dm.ugm"), DM_TOOLS, limit=300,
             computes=DM_COMPUTES),
        Spec("p1",
             _corpus("melee-p1.ugm")
             + (SETTLING + COACHING if loop == "table" and coaching
                else SETTLING if loop == "table" else ""),
             limit=300, computes=P1_COMPUTES, loop=loop),
    )


def play(rounds: int = 24, loop: str = "shipped", coaching: bool = False):
    t = Table(scenario(loop, coaching))
    quiet = t.play(rounds=rounds)
    return t, quiet


# -- (3) learning the coaching from play -------------------------------------


def demonstrate(fights: int = 6, seed0: int = 7):
    """Watch a well-played fight, several times over.

    The teacher is the COACHED player: however the good play was produced, what
    is learned from is the play itself. That is gold-episode fitting with the
    gold being a game rather than a rig, and it is the honest test -- can the
    policy that used to be guards be recovered from behaviour alone?

    Several fights, because generalising over one keeps whatever that fight
    happened to contain. Different dice, same corpus.
    """
    from . import teaching

    lesson = teaching.Lesson()
    last = None
    for i in range(fights):
        _RNG.seed(seed0 + i)
        t = Table(scenario("table", True))
        t.wire.by_name["p1"].watch = lesson.watching
        t.play(rounds=30)
        last = t.wire.by_name["p1"]
        t.close()
    return lesson, last


def learn(fights: int = 6) -> Tuple[str, dict]:
    """The demonstrations, as a trigger document."""
    from . import teaching

    lesson, teacher_agent = demonstrate(fights)
    learned = lesson.recognisers(teacher_agent.m, teacher_agent.kb)
    lines = []
    for name, (text, weight) in sorted(learned["rules"].items()):
        try:
            whole = teacher_agent.kb.term(text)
        except Exception:
            learned["unspeakable"] = learned.get("unspeakable", 0) + 1
            continue
        members = ", ".join("+" + teacher_agent.m.g.show(x)
                            for x in teacher_agent.m.g.members(whole))
        lines.append("when { %s } => boost(<%s>, %d)" % (members, name, weight))
    return "\n".join(lines) + "\n", learned


def taught(text: str) -> Tuple[Spec, ...]:
    """The same scenario, with the LEARNED triggers instead of the written
    ones. Nothing else differs: same corpus, same tools, same loop."""
    return (
        Spec("dm", _corpus("melee-dm.ugm"), DM_TOOLS, limit=300,
             computes=DM_COMPUTES),
        Spec("p1", _corpus("melee-p1.ugm") + SETTLING + text,
             limit=300, computes=P1_COMPUTES, loop="table"),
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(__doc__.split("## Why this exists")[0].strip())
    print()
    t, quiet = play()
    for r, u in t.transcript:
        print(f"    round {r:>2}  {u.speaker} -> {u.hearer}: {u.text}")
    print(f"    (quiet in round {quiet})")
    print()
    for name, held in sorted(t.beliefs().items()):
        # ⚠ `standing` is filtered out: the bundle deposits one per rule, so
        # a belief list dominated by twenty of them says nothing about a fight.
        interesting = [
            p for p in held
            if p.split("(")[0] in ("hp", "down", "fled", "ran", "bloodied",
                                   "potion", "enough", "guarding", "round")
        ]
        print(f"    {name} believes: {', '.join(interesting) or '--'}")
    if t.refused:
        print()
        for r in t.refused:
            print(f"    refused: {r}")
    t.close()
    # A fight in which nobody said anything is a scenario that did not happen,
    # and it would otherwise read as a pass.
    return 0 if t.transcript else 1


if __name__ == "__main__":
    raise SystemExit(main())

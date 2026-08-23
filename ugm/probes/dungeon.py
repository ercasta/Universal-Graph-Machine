"""A fight, run by rules. Can a corpus nobody designed the engine around play?

    python -m ugm.probes.dungeon

Recovered from `15d0ed2` (deleted at `4c69f0a`) and re-run as the CONTROL
step of `docs/new_substrate.md`'s two-step plan: port to today's syntax and
confirm it still resolves, before porting to the new microprogram shape and
comparing. `ugm/rules/dungeon.ugm` carries the two mechanical fixes
(`causes` -> `implies`, `-present(...)` -> `no present(...)`); this file is
a fresh probe against today's `Machine`/`load`/`answerer` API rather than a
port of the old one, which named things (`Loader(m, scope=...)`,
`e.proposition`, `..core.chain.PLUS`) that no longer exist.

This is an expressibility test, in the shape `ugm.bundle` used: take a
domain the design was not built for, author it in the surface, and see what
cannot be said.
"""

import random
import sys
from typing import List, Optional

from .. import corpora as _corpora
from ..core.machine import Machine
from ..core.text import load, load_file

CORPUS = _corpora.path("dungeon.ugm")

# The dice the corpus names. A die the corpus asks for and this does not
# know is a DECLINE -- *I have nothing to say* -- and not a crash, which is
# the one honest thing a tool can do about a question outside its
# competence.
DICE = {"d4": 4, "d6": 6, "d20": 20}


def fight(seed: Optional[int] = 7, limit: int = 4000):
    """One fight. Returns the machine, its name scope, and the log of what
    each tool was asked."""
    m = Machine()
    # Tools are registered on the MACHINE (`Loader.answerer` -> `m.answerer`
    # -> `m.answerers`), and a Loader seeds its own `<name>` table from that
    # list at CONSTRUCTION time -- so the corpus, which names `<dice>` etc.
    # in its own text, has to be loaded AFTER the tools exist, through a
    # throwaway loader that shares the same scope.
    pre = load(m, "", scope="dungeon")
    rng = random.Random(seed)
    asked: List[str] = []

    def dice(mach, prop):
        die, _what = mach.g.members(prop)
        sides = DICE.get(mach.g.show(die))
        if sides is None:
            return None  # decline: a die this tool does not carry
        asked.append(mach.g.show(prop))
        return pre.atom(str(rng.randint(1, sides)))

    def arith(mach, prop):
        op, a, b = (mach.g.show(x) for x in mach.g.members(prop))
        if not (a.isdigit() and b.isdigit()):
            return None
        # `sub`, not `minus` -- `Machine.reserved` binds `plus`/`minus` to
        # the sign atoms, and a corpus's own operator name has to stay clear
        # of them or the tool resolves the wrong thing silently.
        if op == "sub":
            asked.append(mach.g.show(prop))
            return pre.atom(str(max(0, int(a) - int(b))))
        return None

    def compare(mach, prop):
        a, b = (mach.g.show(x) for x in mach.g.members(prop))
        if not (a.isdigit() and b.isdigit()):
            return None
        asked.append(mach.g.show(prop))
        return pre.atom("yes" if int(a) >= int(b) else "no")

    pre.answerer("dice", "roll", dice)
    pre.answerer("arith", "calc", arith)
    pre.answerer("compare", "beats", compare)

    # NOW the corpus, with the tools it names already resolvable.
    kb = load_file(m, CORPUS, scope="dungeon")

    steps = m.run(limit=limit)
    return m, kb, asked, steps


def main() -> int:
    m, kb, asked, steps = fight()
    over = [p for p in m.pad.believed() if m.g.relation_of(p) is kb.atom("over")]
    applied = sum(1 for s in steps if s.applied is not None)
    print(f"ticks: {len(steps)}  applied: {applied}  asked: {len(asked)}")
    if over:
        print("resolved:", m.g.show(over[0]))
    else:
        print("UNRESOLVED -- neither side won inside the run limit")
    hero_hp = [m.g.show(p) for p in m.pad.believed()
               if m.g.relation_of(p) is kb.atom("hp")
               and m.g.member(p, 0) == kb.atom("hero")]
    print("hero hp:", hero_hp)
    return 0 if over else 1


if __name__ == "__main__":
    raise SystemExit(main())

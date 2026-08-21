"""A fight, run by rules. Can a corpus nobody designed the engine around play?

    python -m ugm.probes.dungeon

This is an expressibility test, in the shape ugm.bundle used: take a domain the
design was not built for, author it in the surface, and see what cannot be
said. ⚠ The two things the corpus had to work around, and both are honest
findings rather than defects of the demo: 1.

See docs/design/dungeon.md.
"""

from .. import corpora as _corpora
import time
import random
from typing import List, Optional

from ..core.chain import PLUS
from ..core.machine import Machine
from ..core.text import Loader

CORPUS = _corpora.path("dungeon.ugm")

# The dice the corpus names. A die the corpus asks for and this does not know is
# a decline -- *I have nothing to say* -- and not a crash, which is the one
# honest thing a tool can do about a question outside its competence.
DICE = {"d4": 4, "d6": 6, "d20": 20}


def fight(seed: Optional[int] = 7, limit: int = 4000, extra: str = "",
          predictive: bool = False):
    """One fight. Returns the machine, the corpus's name scope, and the log of

    what each tool was asked. ⭐⭐ predictive is the connective, and it is the
    corpus's most expensive decision. A wound is an event, so §8 says causes:
    it lands in a later moment and it persists. ⚠ And the first version of this
    note said 660x, which was false.

    See docs/design/dungeon.md#fight.
    """

    m = Machine()
    kb = Loader(m, scope="dungeon")
    rng = random.Random(seed)
    asked: List[str] = []

    def dice(mach, e):
        # Two members, not three. The third used to be the round, carried so
        # that the round-2 ask was a different node from the round-1 one -- and
        # the corpus now spends the request instead, which is its own first law
        # rather than an extra argument. See the corpus header.
        die, _what = mach.g.members(e.proposition)
        sides = DICE.get(mach.g.show(die))
        if sides is None:
            return None
        asked.append(mach.g.show(e.proposition))
        return kb.atom(str(rng.randint(1, sides)))

    def arith(mach, e):
        op, a, b = (mach.g.show(x) for x in mach.g.members(e.proposition))
        if not (a.isdigit() and b.isdigit()):
            return None
        asked.append(mach.g.show(e.proposition))
        # ⚠ add/sub, and NOT plus/minus: Machine.reserved binds those two names
        # to the SIGN atoms, and the loader seeds every corpus's table from it
        # -- so calc(minus, 5, 2) resolved its operator to the minus sign,
        # printed as calc(-, 5, 2), and the tool declined a request it should
        # have answered.
        # → docs/design/dungeon.md#add-sub-and-not-plus-minus-machine
        if op == "sub":
            # ⚠ THE CLAMP. A rule of the game, stated in Python, because the
            # surface cannot write a negative numeral. See the module docstring.
            return kb.atom(str(max(0, int(a) - int(b))))
        return None

    def compare(mach, e):
        a, b = (mach.g.show(x) for x in mach.g.members(e.proposition))
        if not (a.isdigit() and b.isdigit()):
            return None
        asked.append(mach.g.show(e.proposition))
        return kb.atom("yes" if int(a) >= int(b) else "no")

    # ⚠⚠⚠ Through the LOADER, never Machine.answerer with a bare string: a
    # request relation minted beside the corpus's table is a request nobody can
    # write, and an answer built with g.atom is a node no rule can name.
    # → docs/design/dungeon.md#through-the-loader-never-machine-answerer
    kb.answerer("dice", "roll", dice)
    kb.answerer("arith", "calc", arith)
    kb.answerer("compare", "beats", compare)

    with open(CORPUS, "r", encoding="utf-8") as fh:
        src = fh.read()
    if not predictive:
        src = src.replace("= causes(", "= implies(")
    kb.load(src + "\n" + extra)
    if seed is not None:
        kb.load(f"fact +seeded(<dice>, {seed})\n")
    m.run(limit=limit)
    return m, kb, asked


# -- reading the fight back -------------------------------------------------
#
# Rendered from the graph, not from a journal kept beside it. The fight is the
# chain; anything else is a second account of it that can disagree.


def narrate(m, kb) -> List[str]:
    """What happened, in the order it was deposited."""
    g, out = m.g, []
    watch = {
        kb.atom(n) for n in
        ("attack", "hits", "missed", "dead", "fled", "over", "answered")
    }
    # ⭐ The round is COUNTED HERE, by an observer, and no longer computed by the
    # corpus. `follows` is a cycle, so the baton returning to the hero is the
    # next round -- which is the same event the corpus used to notice with
    # `wraps`, `<tick>`, `<wrap>` and an `add` operator on the arithmetic tool.
    # A reader wanting a number can count; nothing in the fight needs one.
    turn, hero = kb.atom("turn"), kb.atom("hero")
    rnd = 0
    for mo in m.chain.moments:
        for e in mo.delta:
            rel = g.relation_of(e.proposition)
            if (rel is turn and e.sign == PLUS
                    and g.member(e.proposition, 0) is hero):
                rnd += 1
            if rel not in watch or e.sign != PLUS:
                continue
            if rel is kb.atom("answered"):
                who = g.member(e.proposition, 0)
                if who is not kb.rule_nodes["dice"]:
                    continue
                req, said = g.member(e.proposition, 1), g.member(e.proposition, 2)
                die, what = g.members(req)
                out.append(f"    round {rnd:<2} {g.show(what):<22}"
                           f" {g.show(die)} -> {g.show(said)}")
                continue
            out.append(f"    round {rnd:<2} {g.show(e.proposition)}")
    return out


def state_of(m, kb, who: str):
    """What the game says about one combatant, now."""
    for n in range(0, 21):
        if m.holds(kb.term(f"hp({who}, {n})")) == PLUS:
            hp = n
            break
    else:
        hp = None
    present = m.holds(kb.term(f"present({who})"))
    return hp, present


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
    print("A fight, seed 7\n")

    m, kb, asked = fight(seed=7)
    for line in narrate(m, kb):
        print(line)
    print()
    for who in ("hero", "goblin1", "goblin2"):
        hp, present = state_of(m, kb, who)
        print(f"    {who:<9} hp={hp}  {'standing' if present == PLUS else 'down or gone'}")
    print()

    # ⚠ Every check below asks its OWN fight through its OWN loader. A node is
    # identified by being the node it is, and two machines that loaded the same
    # corpus hold two disjoint graphs -- so `kb.term("over(hero_wins)")` asked of
    # a different fight's machine is a node that fight never heard of, and the
    # answer would have been a confident `None` every time.

    # -- did it run at all -------------------------------------------------
    gate("the fight ended, and the corpus said how",
         holds(m, kb, "over(hero_wins)") or holds(m, kb, "over(hero_falls)"))
    # ⭐ **The baton came back.** This used to ask for `turn(hero, 2)` -- a round
    # integer the corpus computed with an `add` operator that existed for nothing
    # else. `follows` is a cycle now, so the clock turning IS the hero being
    # handed the turn a second time, and that is what the check observes:
    # several `+turn(hero)` entries, one per round, with nothing counted.
    gate("the clock turned: the baton came back round to the hero",
         _times_granted(m, kb, "hero") > 1)
    gate("every combatant swung at least once -- the monsters are not scenery",
         all(any(f"hit({who}," in a for a in asked)
             for who in ("hero", "goblin1", "goblin2")))
    gate("⭐ nobody acts after they are down -- the acting rules are gated on "
         "being present, which a dead hero taught this corpus the hard way",
         not _acted_after_falling(m))

    # ⚠⚠⚠ The clock, and this check exists because everything else missed it.
    # → docs/design/dungeon.md#the-clock-and-this-check-exists-because-e
    turned = _turns_after_the_end(m)
    gate("⭐⭐⭐ the CLOCK stops when the fight does -- and this is the only "
         "check here that can see it, measured by putting the bug back",
         not turned)

    # -- the state is the chain -------------------------------------------
    gate("⭐ a combatant has exactly ONE hit point total -- an update denies "
         "its own old value, since nothing in the design knows about keys",
         all(sum(1 for n in range(0, 21)
                 if m.holds(kb.term(f"hp({w}, {n})")) == PLUS) == 1
             for w in ("hero", "goblin1", "goblin2")))

    # -- a tool proposes, never concludes ----------------------------------
    mr, kr, ar = fight(seed=7, extra="fact -answers(<dice>, roll)")
    gate("⭐⭐⭐ retire the dice and no blow is ever struck -- a corpus can take "
         "a tool away, which is what a Python-registered hook could never be",
         not ar and not holds(mr, kr, "over(hero_wins)")
         and not holds(mr, kr, "over(hero_falls)"))

    mp, kp, ap = fight(seed=7, extra="fact -says(player, declares(attack(goblin1), 1), plus)")
    gate("the player speaks through a channel, and it is <trust-player> that "
         "makes a declaration an intention -- deny the arrival and round one "
         "falls through to the standing policy instead",
         bool(ap))

    # -- reproducibility ---------------------------------------------------
    a, b = fight(seed=7)[0], fight(seed=7)[0]
    gate("the same seed replays the same fight, entry for entry",
         [x.node for x in _all(a)] == [x.node for x in _all(b)])
    c = fight(seed=99)[0]
    gate("...and a different seed is a different fight",
         _rolls(c) != _rolls(a))

    # -- the trail ---------------------------------------------------------
    dead = [w for w in ("hero", "goblin1", "goblin2") if holds(m, kb, f"dead({w})")]
    gate("⚠ the trail check has something to measure: somebody died", bool(dead))
    if dead:
        e = m.chain.resolve(kb.term(f"dead({dead[0]})"))
        trail = {m.g.show(x.proposition) for x in m.chain.trail(e)}
        gate(f"⭐⭐ why did {dead[0]} die: the trail reaches the roll that killed "
             f"it, because a tool's answer is a premise like any other",
             any(s.startswith("answered(dice") for s in trail))

    # -- is any of this dead? ----------------------------------------------
    #
    # ⚠ A rule that never applies is a rule whose checks cannot fail, and one
    # fight exercises maybe two thirds of this corpus. Asked of the apparatus's
    # own `exercised(<R>)` fact rather than of a census written beside it.
    seeds = (7, 11, 13, 21, 42, 99, 123)
    fights = [fight(seed=s) for s in seeds]
    authored = _authored_rules()
    ever = set()
    for mm, _kk, _aa in fights:
        ever |= _exercised(mm)
    print(f"\n  {len(authored)} authored rules over {len(seeds)} seeds:")
    print(f"    never applied: {sorted(authored - ever) or 'none'}")
    gate("⭐ no rule in this corpus is dead -- every one of them applies in at "
         "least one fight, so no check here is guarded by a rule that never runs",
         not (authored - ever))

    # -- preemption --------------------------------------------------------
    fled = [(s, mm, kk) for (s, (mm, kk, _)) in zip(seeds, fights)
            if any(holds(mm, kk, f"fled({w})") for w in ("goblin1", "goblin2"))]
    gate("⚠ the preemption check has something to measure: a goblin ran",
         bool(fled))
    if fled:
        s, mm, kk = fled[0]
        who = next(w for w in ("goblin1", "goblin2") if holds(mm, kk, f"fled({w})"))
        gate(f"⭐⭐ preemption is one authored fact: at 1 hp {who} ran instead of "
             f"swinging (seed {s}), and never swung again -- `overrides` DEFEATS "
             f"<gob-acts> rather than merely beating it to the tick, which is "
             f"what stops the attack undoing the flight on the next one",
             holds(mm, kk, f"hp({who}, 1)")
             and not any(a.startswith(f"attack({who},")
                         for a in _acted_after_falling(mm)))

    # -- what the connective costs ----------------------------------------
    t0 = time.time()
    mc, kc, _ = fight(seed=7, limit=1200, predictive=True)
    slow = time.time() - t0
    t0 = time.time()
    mi, ki, _ = fight(seed=7, limit=1200)
    fast = time.time() - t0
    print(f"\n  the connective, same seed and same corpus:")
    for label, mm, kk, secs in (("causes", mc, kc, slow), ("implies", mi, ki, fast)):
        print(f"    {label:8} {secs:5.2f}s  {len(_all(mm)):5} entries  "
              f"{len(mm.chain.moments):4} moments  finished: "
              f"{bool(holds(mm, kk, 'over(hero_wins)') or holds(mm, kk, 'over(hero_falls)'))}")
    gate("⭐⭐ both connectives reach the same verdict -- so the difference "
         "between them is cost, not outcome, and the choice can be argued on "
         "what a prediction is FOR rather than on whether the fight works",
         (holds(mc, kc, "over(hero_falls)") == holds(mi, ki, "over(hero_falls)"))
         and (holds(mc, kc, "over(hero_wins)") == holds(mi, ki, "over(hero_wins)")))
    gate("⭐⭐ `causes` deposits a predicted moment per event, and a game's "
         "rules are never wrong -- the surprise apparatus is real work here "
         "with nothing to find",
         len(mc.chain.moments) > 10 * len(mi.chain.moments))

    print(f"\n{ran} checks, {failing} failing")
    return 1 if failing else 0


def holds(m, kb, term: str) -> bool:
    return m.holds(kb.term(term)) == PLUS


def _authored_rules() -> set:
    """The names the corpus declares, read from the corpus rather than listed
    here -- a list beside the file is a census that goes stale on the next rule."""
    import re
    with open(CORPUS, "r", encoding="utf-8") as fh:
        return set(re.findall(r"^rule <([^>]+)>", fh.read(), re.M))


def _turns_after_the_end(m) -> List[str]:
    """Turns granted after the fight was declared over, in deposit order."""
    over, out = False, []
    for mo in m.chain.moments:
        for e in mo.delta:
            if e.sign != PLUS:
                continue
            shown = m.g.show(e.proposition)
            if shown.startswith("over("):
                over = True
            elif over and shown.startswith("turn("):
                out.append(shown)
    return out


def _exercised(m) -> set:
    """Which rules applied, off the apparatus's own `exercised(<R>)` fact."""
    out = set()
    for mo in m.chain.moments:
        for e in mo.delta:
            shown = m.g.show(e.proposition)
            if e.sign == PLUS and shown.startswith("exercised(<"):
                out.add(shown[len("exercised(<"):-2])
    return out


def _times_granted(m, kb, who: str) -> int:
    """How many times this combatant was handed the turn.

    ⭐ The round counter's replacement, and it is a COUNT OVER THE TRAIL rather
    than a new relation -- which is this repo's standing check before adding
    one. `follows` closes into a cycle, so the baton returning is the next
    round; nothing in the corpus computes a number, and anything that wants one
    counts these.
    """
    turn, actor = kb.atom("turn"), kb.atom(who)
    return sum(1 for mo in m.chain.moments for e in mo.delta
               if e.sign == PLUS
               and m.g.relation_of(e.proposition) is turn
               and m.g.member(e.proposition, 0) is actor)


def _acted_after_falling(m) -> List[str]:
    """Any attack DEPOSITED after its attacker was recorded dead.

    ⚠ Read off the chain in deposit order rather than off the tool's call log:
    the log has no position in the history, so a check written against it could
    only ever compare a count with itself. This repo has a file about the check
    that stopped being able to fail; the first draft of this one could not.
    """
    down, out = set(), []
    for mo in m.chain.moments:
        for e in mo.delta:
            if e.sign != PLUS:
                continue
            shown = m.g.show(e.proposition)
            if shown.startswith(("dead(", "fled(")):
                down.add(shown[shown.index("(") + 1:-1])
            elif shown.startswith("attack("):
                who = shown[len("attack("):].split(",")[0]
                if who in down:
                    out.append(shown)
    return out


def _all(m) -> List:
    return [e for mo in m.chain.moments for e in mo.delta]


def _rolls(m) -> List[str]:
    g = m.g
    out = []
    for mo in m.chain.moments:
        for e in mo.delta:
            if g.show(e.proposition).startswith("answered(dice"):
                out.append(g.show(e.proposition))
    return out


if __name__ == "__main__":
    raise SystemExit(main())

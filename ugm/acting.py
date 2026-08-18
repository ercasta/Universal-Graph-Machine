"""An action is a rule, its bindings, and a free marker -- tried on the dungeon.

    python -m ugm.acting

The shape an agent's action should have, if a policy is ever to be learned over
it, is one triple:

    a rule          which of the authored rules to use
    bindings        what to use it on
    a marker        free structure, meaning whatever rules make of it

The first two make the action; the third makes the CONTEXT sayable. Without it,
two situations that are identical in the world but differ in what the agent was
doing are indistinguishable, and no policy can tell them apart. With it the
number of distinguishable situations is unbounded while the action's SHAPE stays
fixed -- which is what keeps the learner's job small.

## `ugm.dungeon` already has the shape, so this needed no new format

    say player: +declares(attack(goblin1), 1)

    rule <trust-player> = implies( { +says(player, declares(?act, ?r), plus) },
                                   { +intends(hero, ?act, ?r) } )

`attack(goblin1)` is the act with its binding. `?r` is the marker, and the
corpus's own header calls it *a label the player utters* -- carried to the
decision point and interpreted by nothing. So the triple was authored long
before anyone asked for it, which is the strongest evidence available that the
shape is natural rather than imposed.

## What the marker buys, measured

The corpus does not read the marker, so it may be anything. A rule that DOES
read it can pick a different binding for the same declared act:

    rule <focus> = causes(
        { +turn(hero), +may(hero), +present(hero),
          +intends(hero, attack(?d), focus(?e)), +present(?e) },
        { -may(hero), -intends(hero, attack(?d), focus(?e)), +attack(hero, ?e) } )

    marker 1                first hero swing: hit(hero, goblin1)   18 rounds
    marker focus(goblin2)   first hero swing: hit(hero, goblin2)   14 rounds

Same declared act, same bindings, different marker, different target -- and both
fights run to a verdict. That is state-to-action with the state carried in a slot
the domain never had to know about.

## Control flow stays with the loop

The marker is READ by rules and never FOLLOWED by machinery. Nothing in Python
dereferences it, so the loop remains the only thing that decides what applies and
the marker is an ordinary premise. The moment a Python function walks a marker to
decide what happens next, one-interpreter is broken and phases are back -- which
is what `stratum0.py` was deleted for.

## Two ways this fails silently, both checked below

**A marker nothing matches is not an error.** Name a target that is not there and
the discriminating rule simply does not apply; the declared act goes through
unchanged and the fight looks entirely normal. A mistyped marker is a policy that
quietly stops steering, which is the mishearing problem `ugm/table.py` found at
the agent boundary, arriving inside one agent.

**A marker-keyed rule that spends the turn without feeding the clock freezes the
fight.** The first version of the rule here concluded `held(hero, ?d)` instead of
an attack: the hero holds, the turn is consumed, and nothing ever passes the
baton. The result was zero rounds with every combatant alive -- which reads as a
peaceful encounter rather than a stall, and passed the check it was written for.
The check below asserts the stall, so the shape stays visible.

## What this does not do

**Nothing is learned.** The marker is authored here. What it establishes is that
the representation a learned policy would need already works end to end on a
corpus written for something else -- an action whose shape is fixed, whose
context is unbounded, and which selects a BINDING rather than merely a rule.
"""

from typing import Dict

from .dungeon import fight

# The corpus declares three attacks on goblin1. Denying them leaves the player
# silent, so a single declaration of ours is the only thing the hero hears.
DENY = "".join(
    f"fact -says(player, declares(attack(goblin1), {i}), plus)\n" for i in (1, 2, 3)
)

# Reads the marker, and concludes what `<hero-acts>` concludes -- an attack --
# so the clock keeps turning. See the stall note above for the version that did
# not.
FOCUS = """
rule <focus> = causes(
    { +turn(hero), +may(hero), +present(hero),
      +intends(hero, attack(?d), focus(?e)), +present(?e) },
    { -may(hero), -intends(hero, attack(?d), focus(?e)), +attack(hero, ?e) } )
fact overrides(<focus>, <hero-acts>)
"""

# The one that freezes the fight, kept as a fixture rather than as a warning.
HOLD = """
rule <careful> = causes(
    { +turn(hero), +may(hero), +present(hero),
      +intends(hero, attack(?d), careful(?d)) },
    { -may(hero), -intends(hero, attack(?d), careful(?d)), +held(hero, ?d) } )
fact overrides(<careful>, <hero-acts>)
fact overrides(<careful>, <hero-holds>)
"""


def _fight(policy: str, marker: str, seed: int = 7) -> Dict[str, object]:
    extra = DENY + policy + f"\nsay player: +declares(attack(goblin1), {marker})\n"
    m, kb, asked = fight(seed=seed, extra=extra)
    seen: Dict[str, str] = {}
    for mo in m.chain.moments:
        for e in mo.delta:
            seen[m.g.show(e.proposition)] = e.sign
    swings = [a for a in asked if "hit(hero" in a]
    return {
        "first": swings[0] if swings else None,
        "swings": len(swings),
        "rounds": len([a for a in asked if "roll(d20" in a]),
        "intends": sorted(k for k in seen if k.startswith("intends(")),
        "held": sorted(k for k in seen if k.startswith("held(")),
        "hero": seen.get("present(hero)"),
    }


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

    plain = _fight(FOCUS, "1")
    focused = _fight(FOCUS, "focus(goblin2)")
    missing = _fight(FOCUS, "focus(goblin9)")
    stalled = _fight(HOLD, "careful(goblin1)")

    print("  one declared act, four markers:\n")
    for label, r in (("1", plain), ("focus(goblin2)", focused),
                     ("focus(goblin9)", missing), ("careful(goblin1)", stalled)):
        print(f"    {label:18} first swing {str(r['first']):34} "
              f"rounds {r['rounds']:2}  swings {r['swings']:2}")
    print()

    # The control has to be able to fail, or the discrimination check below is
    # about nothing: an arm that never attacks the declared target would make
    # "the other arm attacks someone else" true for free.
    gate("the CONTROL attacks the declared target: with a plain marker the hero "
         f"swings at goblin1 ({plain['first']})",
         plain["first"] == "roll(d20, hit(hero, goblin1))" and plain["swings"] > 1)
    gate("...and the MARKER selects a different binding for the same declared "
         "act -- `attack(goblin1)` in both, and the hero swings at goblin2 "
         f"({focused['first']})",
         focused["first"] == "roll(d20, hit(hero, goblin2))")
    gate("both fights still reach a verdict, so the marker changed WHAT WAS "
         f"DONE rather than whether anything was ({plain['rounds']} rounds vs "
         f"{focused['rounds']})",
         plain["rounds"] > 5 and focused["rounds"] > 5)
    gate("a COMPOUND marker rides through `<trust-player>` untouched: the corpus "
         "interprets nothing, so context may be arbitrary structure",
         any("focus(goblin2)" in k for k in focused["intends"]))

    gate("A MARKER NOTHING MATCHES IS NOT AN ERROR: name an absent target and "
         "the discriminating rule simply does not apply -- the declared act "
         "goes through and the fight looks entirely normal, so a mistyped "
         "policy quietly stops steering",
         missing["first"] == "roll(d20, hit(hero, goblin1))"
         and missing["rounds"] > 5)

    gate("A MARKER-KEYED RULE THAT SPENDS THE TURN WITHOUT FEEDING THE CLOCK "
         "FREEZES THE FIGHT: zero rounds with every combatant alive, which "
         "reads as a peaceful encounter rather than a stall (rounds "
         f"{stalled['rounds']}, hero present {stalled['hero']}, "
         f"held {stalled['held']})",
         stalled["rounds"] == 0 and stalled["hero"] == "+"
         and stalled["held"] == ["held(hero, goblin1)"])

    print(f"\n{ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())

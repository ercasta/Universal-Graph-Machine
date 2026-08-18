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

## Which lever actually steers, measured

`overrides` is authored defeat. The point of the marker is that a LEARNED
policy could steer instead, so the four levers were run against one another on
the same fight, all trying to make the hero take the marker's target:

    overrides(<focus>, <hero-acts>)                   goblin2   authored defeat
    standing(<focus>)                                 goblin2   authored floor-raise
    after <trust-player> { ...pre-tick query... }      goblin2   a BUFF, and it fades
    after <trust-player> { ...its own conclusion... }  goblin1   never fires, silently
    when { ... } => boost(<focus>, 8)                  goblin1   cannot lift off the floor

The third row is the one that matters, because a buff is what a calibration
process writes. It fires once, saturates from 20 to `MAX_LIFT`, steers the
choice, and is back at the floor by the end of the fight:

    Spend(tick=4, by='trust-player', target='focus', delta=12, frozen=False)
    final score <focus>: 1

That is the whole learnable path working end to end: a marker carried by the
action, a postcondition keyed on it, a lift that decides which rule applies, and
a trace that rebuilds the table afterwards.

**The fourth row cost four probes and is the finding to keep.** A
postcondition's query is matched against the state as of the START of the tick,
so **it cannot see what its own rule just concluded**. `after <trust-player>
{ +intends(hero, ?act, focus(?e)) }` asks about the very fact `<trust-player>`
writes, and the answer is always no -- the buff never fires, the table never
moves, nothing is logged and nothing raises. `_spend_posts` says the query is
matched with *the application's own bindings substituted in*, which is true and
is about BINDINGS; its EFFECTS are a tick away.

**And the fifth is the documented limit arriving in practice.** A `when` trigger
is ephemeral and shortlist-only, so it cannot bring a rule into consideration --
`<focus>` sits at `FLOOR` and is never in a shortlist for a reranker to reorder.
A learned preference written as a reranker can only reorder what attention had
already selected.

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
FOCUS_RULE = """
rule <focus> = causes(
    { +turn(hero), +may(hero), +present(hero),
      +intends(hero, attack(?d), focus(?e)), +present(?e) },
    { -may(hero), -intends(hero, attack(?d), focus(?e)), +attack(hero, ?e) } )
"""

FOCUS = FOCUS_RULE + "fact overrides(<focus>, <hero-acts>)" + chr(10)

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


# The four levers, each trying to make the marker's target the one attacked.
BY_OVERRIDE = "fact overrides(<focus>, <hero-acts>)\n"
BY_STANDING = "fact standing(<focus>)\n"

# Keyed on what held BEFORE the tick -- the arrival, not the intention the rule
# concludes from it. See the docstring: the other way round never fires.
BY_BUFF = ("after <trust-player> { +says(player, declares(?act, focus(?e)), plus) }"
           " => boost(<focus>, 20)\n")

# The same buff, asking about its own rule's conclusion. Kept as a fixture
# because it fails in complete silence.
BY_BUFF_BLIND = ("after <trust-player> { +intends(hero, ?act, focus(?e)) }"
                 " => boost(<focus>, 20)\n")

BY_RERANK = "when { +intends(hero, attack(?d), focus(?e)) } => boost(<focus>, 8)\n"


def _traced(policy: str, marker: str, seed: int = 7):
    """A fight, plus the attention table's trace.

    `Machine.run` returns only the steps, so the Report -- and with it the
    trace that says whether a buff was ever spent -- is discarded. Swapped for
    the duration and restored in a `finally`, because a module-level patch that
    leaked would make every later run in this process report someone else's
    table.
    """
    from . import attention as A
    from . import machine as MM

    reps = []
    live_run, live_method = A.run, MM.Machine.run

    def capture(m, *a, **k):
        rep = live_run(m, *a, **k)
        reps.append((m, rep))
        return rep

    try:
        A.run = capture
        MM.Machine.run = lambda self, limit=100: capture(self, limit=limit).steps
        got = _fight(policy, marker, seed=seed)
    finally:
        A.run, MM.Machine.run = live_run, live_method
    mach, rep = reps[-1] if reps else (None, None)
    got["spends"] = list(rep.table.trace) if rep else []
    got["score"] = (
        {mach.g.show(k): v for k, v in rep.table.score.items()
         if "focus" in mach.g.show(k)} if rep else {}
    )
    return got


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

    # -- which lever steers ------------------------------------------------
    levers = (
        ("overrides", BY_OVERRIDE), ("standing", BY_STANDING),
        ("after-buff", BY_BUFF), ("after-buff blind", BY_BUFF_BLIND),
        ("when-reranker", BY_RERANK),
    )
    got = {name: _traced(FOCUS_RULE + lever, "focus(goblin2)")
           for name, lever in levers}
    print("  five levers, one fight, all trying to take the marker's target:\n")
    for name, _ in levers:
        r = got[name]
        target = "goblin2" if r["first"] and "goblin2" in r["first"] else "goblin1"
        print(f"    {name:18} -> {target:8} spends {len(r['spends'])}  "
              f"final score {r['score']}")
    print()

    gate("a BUFF steers the choice, which is the whole learnable path: a marker "
         "carried by the action, a postcondition keyed on it, and a lift that "
         f"decides which rule applies ({got['after-buff']['spends']})",
         "goblin2" in (got["after-buff"]["first"] or "")
         and len(got["after-buff"]["spends"]) == 1)
    gate("...and the lift SATURATES and FADES -- a boost of 20 spends 12, and "
         "the rule is back at the floor by the end, because a lift is about "
         f"what is going on now ({got['after-buff']['score']})",
         got["after-buff"]["spends"][0].delta == 12
         and list(got["after-buff"]["score"].values()) == [1])

    gate("A POSTCONDITION CANNOT SEE WHAT ITS OWN RULE JUST CONCLUDED: the same "
         "buff, keyed on the intention `<trust-player>` writes instead of on "
         "the arrival it read, never fires -- no spend, no lift, no steering, "
         "and nothing anywhere raises",
         got["after-buff blind"]["spends"] == []
         and "goblin1" in (got["after-buff blind"]["first"] or ""))
    gate("A RERANKER CANNOT LIFT A RULE OFF THE FLOOR, which is the documented "
         "limit arriving in practice: `<focus>` is never in a shortlist for a "
         "`when` trigger to reorder, so a learned preference written that way "
         "can only reorder what attention had already selected",
         got["when-reranker"]["spends"] == []
         and "goblin1" in (got["when-reranker"]["first"] or ""))
    gate("...while both AUTHORED levers work, so the fixture can tell a lever "
         "that fails from a fight that cannot be steered at all",
         "goblin2" in (got["overrides"]["first"] or "")
         and "goblin2" in (got["standing"]["first"] or ""))


    print(f"\n{ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""A goal one agent cannot reach alone. Three minds, and the ask that closes it.

    python -m ugm.probes.quest

`ugm.table` is the wire; this is a corpus written on it, and it exists to answer
the standing request in `docs/dungeon-reply.md`: **author a goal.** `fit`,
`check`, `verdict`, `subgoal`, `blocked` and `<give-up>` had never been exercised
by a corpus written outside the ugm repository, and the dungeon authored zero
goals because a fight is entirely forward.

A table makes a goal natural rather than contrived. p1 wants the door open, needs
a key it does not have, and **runs out of ways to get there** — at which point
backward reading writes `blocked`, and *that* is the occasion to ask somebody
else. Cooperation is not a feature here; it is what a blocked goal is FOR.

    p1: goal(open(door1))          -- and no key
        `-> blocked(have(p1, key1))
             `-> tell(dm, want(p1, key1))
                  dm knows who holds it   -> tell(p2, asked(p1, key1))
                       p2 hands it over   -> tell(dm, gives(p2, p1, key1))
                            dm narrates   -> tell(p1, have(p1, key1))
    p1: open(door1)                -- the goal, reached by asking

⭐ **The whole loop is driven by a goal nothing local could satisfy.** Delete p2
and p1 stays blocked for ever, which is the control below.

⚠⚠⚠ **AN ARRIVAL CANNOT BE SPENT, and this inverts `docs/authoring.md` §0.**
§0 says an occasion is consumed and a rule must deny what it consumes. At a
channel that is exactly wrong, and it cost two hangs to find out.

The DM's routing rule re-fired once the key changed hands -- `wants(p1, key1)`
was still true and `holds(p1, key1)` had become true, so the DM told p1 it had
been asked for the key it had just been given. Applying §0, the rule was made to
deny what it consumed. **Both attempts ran for ever**, and the trace says why:

    150  + says(p1, want(p1, key1), +)
    149  - says(p1, want(p1, key1), +)
    149  + wants(p1, key1)

`<intake>` is a BUNDLED rule -- `arrived(?c, ?said, ?sign) ⟹ says(...)` -- and
`arrived` is the unarguable record of a boundary event, which nothing retracts.
So `says` is re-derived the moment it is denied, and so is anything derived from
it. **Deny something an arrival implies and the bundle restores it, for ever.**

What works instead is not consumption but a **gate that legitimately closes**:

    rule <route> = implies( { +wants(?who, ?k), -holds(?who, ?k),
                              +holds(?keeper, ?k) }, { ... } )
    fact -holds(p1, key1)

The DM asserts the denial up front (§1, *write your negatives*); the transfer's
`+holds(p1, key1)` supersedes it; the member stops matching and the rule goes
quiet with nothing retracted. So the two rules of thumb divide cleanly:

> **Consume what you concluded. Never consume what you were told.**

⚠⚠⚠ **`blocked` reports the rule's antecedent member AS WRITTEN, ungrounded**,
and that decided how this corpus had to be shaped. Probed three ways:

    { +have(?w, ?k), +opens(?k, ?d) }   -> blocked(have(?w, ?k))
    { +opens(?k, ?d), +have(?w, ?k) }   -> blocked(have(?w, ?k))   (order is not it)
    { +opens(?k, ?d), +me(?w), +have(?w, ?k) } with `fact +me(p1)`
                                        -> blocked(have(?w, ?k))   (nor a ground sibling)

`achieved(opens(key1, door1))` is written in every one of those runs, so the
sibling premise *was* satisfied and its binding did **not** reach `have`. So a
blocked subgoal is generic unless the rule's member is ground -- and **a generic
term cannot be uttered**, because an arrival may not contain a variable. An agent
that wants to ask for help must therefore ask about something it named itself.
`<unlock>` is written with `have(p1, key1)` ground for exactly that reason, and
that is a real constraint on cooperative corpora rather than a stylistic choice.
"""

from .. import corpora as _corpora
import pathlib
import sys
from typing import List

from .table import Local, Processes, Spec, Table, Utterance

# -- the three corpora -------------------------------------------------------

# ⭐ **In files, beside `dungeon.ugm`, and not in this one.** They were string
# literals here, which put a corpus in `ugm/*.py` next to the engine -- and the
# cost is not only that a reader cannot tell which is which. **Nothing that
# checks a corpus can read a Python string**: `python -m ugm.probes.atlas` maps a file,
# the load-time note about names nothing writes fires on a file, and this corpus
# was invisible to both while `dungeon.ugm` was not. Same team, same repository,
# two conventions.
RULES = pathlib.Path(_corpora.DIR)


def corpus(name: str) -> str:
    with open(RULES / f"quest-{name}.ugm", "r", encoding="utf-8") as fh:
        return fh.read()


DM = corpus("dm")
P1 = corpus("p1")
P2 = corpus("p2")
DM_ALONE = corpus("dm-alone")

QUEST = (Spec("dm", DM), Spec("p1", P1), Spec("p2", P2))
LONELY = (Spec("dm", DM_ALONE), Spec("p1", P1))


def main() -> int:
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
    print("A goal, three minds\n")

    t = Table(QUEST)
    quiet = t.play()
    for r, u in t.transcript:
        print(f"    round {r}  {u.speaker} -> {u.hearer}: {u.text}")
    print(f"    (quiet in round {quiet})")
    if t.refused:
        print(f"    refused: {t.refused}")
    print()

    b = t.beliefs()
    print(f"    p1 open(door1)      {'+' if 'open(door1)' in b['p1'] else '-'}")
    print(f"    p1 have(p1, key1)   {'+' if 'have(p1, key1)' in b['p1'] else '-'}")
    print(f"    p2 holds(p2, key1)  {'+' if 'holds(p2, key1)' in b['p2'] else '-'}")
    print(f"    dm holds(p1, key1)  {'+' if 'holds(p1, key1)' in b['dm'] else '-'}")
    print()

    # -- the goal, and that it was the goal that drove it -------------------
    gate("⭐⭐⭐ THE GOAL IS REACHED, and only by asking: p1 opens the door with "
         "a key it did not have, could not make, and had to be given",
         "open(door1)" in b["p1"])
    gate("⭐⭐⭐ backward reading ran in a corpus written outside the ugm repo -- "
         "the goal produced a subgoal, and the subgoal it could not reach is on "
         "the record as `blocked`",
         "blocked(have(p1, key1))" in b["p1"])
    gate("⭐ and `blocked` is what triggered the ask -- the request is licensed "
         "by the agent having run out of its own ways to get there",
         any(u.text.startswith("want(p1,") for _, u in t.transcript))

    # ⚠⚠⚠ This check exists because the transcript showed the bug and eight
    # checks did not. A request that is never spent is re-routed whenever the
    # world moves, and nothing about the OUTCOME can see it -- the goal is still
    # reached, every belief is still right, and the table still goes quiet.
    asked = [u for _, u in t.transcript if u.text.startswith("asked(")]
    gate("⭐⭐⭐ the request is routed EXACTLY ONCE -- an arrival never stops "
         "being true, so a rule keyed straight off `says` re-fires every time "
         f"the world moves: {[u.hearer for u in asked]}",
         len(asked) == 1 and asked[0].hearer == "p2")

    # -- the control: no key in the world ----------------------------------
    lone = Table(LONELY)
    lq = lone.play()
    lb = lone.beliefs()
    gate("⚠ the control has something to measure: p1 asked here too",
         any(u.text.startswith("want(p1,") for _, u in lone.transcript))
    gate("⭐⭐ delete the agent that holds the key and p1 stays blocked for "
         "ever -- the goal is not reached, the ask is not answered, and the "
         "table goes quiet rather than spinning",
         "open(door1)" not in lb["p1"]
         and "blocked(have(p1, key1))" in lb["p1"] and lq < 12)

    # -- the world moved, and everyone's account of it agrees ---------------
    gate("⭐⭐ the key CHANGED HANDS in three separate heads: p2 gave it up, the "
         "DM recorded the transfer, p1 has it -- three chains that never "
         "touched, agreeing because each was told",
         "holds(p2, key1)" not in b["p2"]
         and "holds(p1, key1)" in b["dm"]
         and "have(p1, key1)" in b["p1"])

    # -- fog of war, still ---------------------------------------------------
    gate("⭐⭐⭐ and p2 never learns what it was FOR: it handed over a key and "
         "holds nothing about a door, a goal, or p1's plan -- it was asked for "
         "an object, not told a story",
         not any(s.startswith(("open(", "goal(", "blocked(", "opens("))
                 for s in b["p2"]))

    # -- and across processes ------------------------------------------------
    p = Table(QUEST, transport=Processes)
    try:
        pq = p.play()
        pt = [(r, tuple(u)) for r, u in p.transcript]
        pb = p.beliefs()
    finally:
        p.close()
    gate("the same quest across three OS processes: identical transcript and "
         "identical beliefs",
         pt == [(r, tuple(u)) for r, u in t.transcript] and pq == quiet
         and all(pb[n] == b[n] for n in ("dm", "p1", "p2")))

    print(f"\n{ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())

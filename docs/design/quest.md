# `quest.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

A goal one agent cannot reach alone. Three minds, and the ask that closes it.

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

 **AN ARRIVAL CANNOT BE SPENT, and this inverts `docs/authoring.md` §0.**
§0 says an occasion is consumed and a rule must deny what it consumes. At a
channel that is exactly wrong, and it cost two hangs to find out.

The DM's routing rule re-fired once the key changed hands -- `wants(p1, key1)`
was still true and `holds(p1, key1)` had become true, so the DM told p1 it had
been asked for the key it had just been given. Applying §0, the rule was made to
deny what it consumed. **Both attempts ran for ever**, and the trace says why:

    150  + says(p1, want(p1, key1), +)
    149  - says(p1, want(p1, key1), +)
    149  + wants(p1, key1)

`<intake>` is a BUNDLED rule -- `arrived($c, $said, $sign) ⟹ says(...)` -- and
`arrived` is the unarguable record of a boundary event, which nothing retracts.
So `says` is re-derived the moment it is denied, and so is anything derived from
it. **Deny something an arrival implies and the bundle restores it, for ever.**

What works instead is not consumption but a **gate that legitimately closes**:

    rule <route> = implies( { +wants($who, $k), -holds($who, $k),
                              +holds($keeper, $k) }, { ... } )
    fact -holds(p1, key1)

The DM asserts the denial up front (§1, *write your negatives*); the transfer's
`+holds(p1, key1)` supersedes it; the member stops matching and the rule goes
quiet with nothing retracted. So the two rules of thumb divide cleanly:

> **Consume what you concluded. Never consume what you were told.**

 **`blocked` reports the rule's antecedent member AS WRITTEN, ungrounded**,
and that decided how this corpus had to be shaped. Probed three ways:

    { +have($w, $k), +opens($k, $d) }   -> blocked(have($w, $k))
    { +opens($k, $d), +have($w, $k) }   -> blocked(have($w, $k))   (order is not it)
    { +opens($k, $d), +me($w), +have($w, $k) } with `fact +me(p1)`
                                        -> blocked(have($w, $k))   (nor a ground sibling)

`achieved(opens(key1, door1))` is written in every one of those runs, so the
sibling premise *was* satisfied and its binding did **not** reach `have`. So a
blocked subgoal is generic unless the rule's member is ground -- and **a generic
term cannot be uttered**, because an arrival may not contain a variable. An agent
that wants to ask for help must therefore ask about something it named itself.
`<unlock>` is written with `have(p1, key1)` ground for exactly that reason, and
that is a real constraint on cooperative corpora rather than a stylistic choice.

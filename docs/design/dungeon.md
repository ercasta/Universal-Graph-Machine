# `dungeon.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

A fight, run by rules. Can a corpus nobody designed the engine around play?

    python -m ugm.probes.dungeon

This is an **expressibility test**, in the shape `ugm.bundle` used: take a domain
the design was not built for, author it in the surface, and see what cannot be
said. D&D is a good adversary precisely because it is the three things this
engine is weakest at -- arithmetic, randomness and turn structure -- and because
the mechanics and the monsters are visibly different KINDS of thing to a person
while the design claims they are the same kind of thing to it.

What is a rule and what is a tool is decided by one question, and the same one
§21 uses: is this a search, or a function? Hit resolution, initiative, death,
fleeing and victory are searches over what is claimed, so they are rules. Three
things are not, and each becomes an answerer:

    <dice>     roll(die, what)         the world; we do not control it
    <arith>    calc(op, a, b)          the surface has no arithmetic
    <compare>  beats(a, b)             ...and no ordering either

⭐ **A tool proposes, never concludes.** Every one of them lands `answered(...)`
-- a record -- and a corpus rule turns it into a claim about the fight. That is
not fastidiousness here either: `why(dead(goblin1))` walks back through the roll
that killed it, because the roll is on the trail like any other premise.

 **The two things the corpus had to work around**, and both are honest
findings rather than defects of the demo:

  1. **A functional attribute retracts its own old value.** `hp(g1, 5)` and
     `hp(g1, 2)` are different propositions, so asserting the second leaves the
     first standing. There is no notion of a key in this design, so `<wound>`
     writes the denial and the assertion as an authored pair.

  2. **The occasion is the request being SPENT** -- and this row said something
     else for a long time, so the correction is the more useful half of it.

     A request is a fact, and quiescence drops an application that restates what
     the chain already says. So `roll(d20, hit(goblin1, hero))` asked twice is
     one node, and the goblin swings once and then stands still for the rest of
     the fight. The corpus's first answer was to put the ROUND in every request,
     which worked and cost a round counter threaded through 65 member positions.

     `docs/dungeon-reply.md` proposed that `at $m` would collapse that, since a
     round integer is a moment ordinal re-implemented in the corpus.
      **Probed, and it does not**: the read INHERITS, so depositing the same
     request at a later moment changes nothing the chain answers and quiescence
     drops it -- correctly. Measured on a three-beat fixture: one ask, not three.

     What does work is this corpus's own first law, which it was already
     applying to everything except its requests: **an occasion is consumed, and
     a fact is not.** Deny the request and its answer in the same breath as
     consuming them, and the next ask is a genuine change. Same fixture: three
     asks, no round argument and no locus.

     So the round was never carrying the occasion -- the DENIAL was missing --
     and what is left of `$r` is a label the player utters, because an agent
     cannot utter a moment.

**Kill-probed seven ways, one mutation at a time against one seed-7 fight.** Each
lands in its own column, which is what says the checks are measuring different
things rather than the same thing seven times:

| break | finished | entries | turns after the end | acted while down | two hp totals |
|---|---|---|---|---|---|
| baseline | yes | 872 | 0 | 0 | -- |
| `<halt>` writes `+done` | yes | 8,127 | **1,008** | 0 | -- |
| `<hero-holds>` ungated on `present(hero)` | **no** | 12,495 | 0 | **1** | -- |
| `<wound>` keeps the attack | **no** | 11,508 | 0 | 0 | -- |
| `<wound>` keeps the hit | **no** | 15,236 | 0 | 0 | -- |
| **`<miss>` keeps its dice request** | **no** | **17,293** | 0 | 0 | -- |
| **`<wound>` keeps its dice requests** | yes | **530** | 0 | 0 | -- |
| `hp` asserted without denying the old | yes | 753 | 0 | 0 | **hero, goblin1** |
| no `overrides(<gob-flees>, <gob-acts>)` | yes | 735 | 0 | 0 | -- |

 **Rows 2–5 and 8–9 were measured against the previous corpus**, the one with
the round counter, and are carried rather than re-run. The baseline and the two
dice-request rows are today's.

⭐⭐ **The two new rows are the round's replacement, kill-probed -- and they land
in DIFFERENT columns, which is what says spending is doing two jobs rather than
one.** Take the spend out of `<miss>` and the fight never finishes: the stale
roll re-answers the miss for ever, 17,293 entries against the limit. Take it out
of `<wound>` and the fight finishes and is WRONG: 530 entries, 9 rolls, because
`<hit>` re-fires on a to-hit roll nobody re-asked for and a goblin is beaten to
death by one d20. The second is the more dangerous shape, and it is the same one
this corpus already records for `-hits` -- a run that ends, with a verdict, and
nothing about the outcome to say it is nonsense.

 **The last row is the honest one.** At seed 7 no goblin ever reaches 1 hp, so
that fight cannot measure preemption at all and the mutation moves one entry.
What catches it is the seven-seed census below -- *no rule in this corpus is
dead* -- and nothing else here would have. A homogeneous fixture cannot measure
a discriminator, recorded in this repo before and re-earned here.

 **And the row above `<halt>` is the one that justifies the clock check.**
With `+done` the fight is decided correctly, the verdict is right, every check
about the outcome is green -- and the agent turns an empty room over to round
417. Nothing that asserts what the agent concluded can see it still working
afterwards.

 **And one judgement is inside a tool, where nothing can argue with it.** The
clamp: `calc(minus, 3, 5)` answers `0`, because a numeral is an atom whose name
reads as a number and `-2` is not a name the surface can write. So *hit points
do not go negative* -- a rule of the game -- is stated in Python. It is the
smallest example of the thing tools are dangerous for, it is measured below, and
it is left in view rather than hidden.

## `fight`

One fight. Returns the machine, the corpus's name scope, and the log of
    what each tool was asked.

    ⭐⭐ **`predictive` is the connective, and it is the corpus's most expensive
    decision.** A wound is an event, so §8 says `causes`: it lands in a later
    moment and it persists. What §18 then does with it is deposit a PREDICTED
    moment for every consequent member, so a later observation can disagree with
    it -- exactly right for an agent heating a kettle, and dead weight for a game
    whose rules are never wrong. Measured, same seed, same corpus, best of three,
    one connective changed:

        causes    2.08s   1,073 entries   74 moments   392 expects/deviates/close
        implies   0.17s     737 entries    1 moment     57

    12x the time for 1.5x the entries: the cost is not the entries, it is the
    74 predicted moments and the traffic that checks them. So the demo runs on
    `implies` and the corpus keeps `causes` as authored, because which connective
    is CORRECT is a separate question from which is affordable.

     **And the first version of this note said 660x, which was false.** That
    measurement was taken while the corpus still had a clock that never stopped
    -- `<skip>` and `<pass>` turning an empty room over for ever -- so what it
    compared was a runaway loop against a terminating one, and the connective
    was barely involved. Both runs above now finish. A measurement taken across a
    bug measures the bug; this one is left in because the number was quotable,
    the story it told was tidy, and it was wrong.

## add/sub, and NOT plus/minus: Machine.

 `add`/`sub`, and NOT `plus`/`minus`: `Machine.reserved` binds those
two names to the SIGN atoms, and the loader seeds every corpus's table
from it -- so `calc(minus, 5, 2)` resolved its operator to the minus
sign, printed as `calc(-, 5, 2)`, and the tool declined a request it
should have answered. The twin trap from the far side: not two nodes
with one name, but one node with two meanings.
⭐ **`add` is gone, and its absence is the measurement.**
`docs/dungeon-feedback.md` reported the operator as existing SOLELY to
count rounds, and asked whether collapsing the clock would remove its
only customer. It did: over four seeds the fight asks this tool for
`sub` and nothing else. Adding is not arithmetic the game needs; it was
arithmetic the SCAFFOLD needed.

## Through the LOADER, never Machine.answerer

 Through the LOADER, never `Machine.answerer` with a bare string: a
request relation minted beside the corpus's table is a request nobody can
write, and an answer built with `g.atom` is a node no rule can name. Both
are the twin trap and both are silent.
`seed` goes on the record as a fact, so a fight is reproducible and `why`
can reach the roll. §3 forbids reading a derived result out of an unseeded
source; a die is not derived -- it is the world speaking, which is the
user's own framing and the right one -- but a fight nobody can replay is a
fight nobody can argue about, and the seed costs one line. `seed=None` is
the genuinely external die.

## The clock, and this check exists because e

 **The clock, and this check exists because everything else missed it.**
Give `<halt>` the obvious consequent -- `+done`, the same thing `<skip>`
writes -- and the fight ends while the clock does not: `<pass>` moves the
baton, `<wrap>` counts the round, and an empty room is turned over to round
417 for 8,072 entries. Every other check here stayed green through it,
because the fight really had been decided and everything asserted about the
outcome was still true. **Nothing that asserts what the agent concluded can
see it still working afterwards** -- which is `ugm.state`'s finding about
the key set, arriving from a corpus.

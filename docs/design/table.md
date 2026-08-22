# `table.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

Several agents, each with its own beliefs, talking. The layer BELOW the machine.

    python -m ugm.probes.table

An agent's beliefs are its own chain. Nothing is shared: two machines hold two
graphs, and a node in one names nothing in the other. What crosses is an
**utterance** -- rendered text, re-read in the receiver's own name scope -- and
what the receiver does with it is a trust rule in its corpus, never anything
here. That is §13 read end to end, and both ends already existed:

    actuator   a channel that carries intents OUT   -- `+doing(tell(p1, x))`
    channel    a channel that carries the world IN  -- `says(dm, x, plus)`

**So this module is only the wire.** It renders what one machine emitted, hands
the text to another machine's channel, and decides whose turn it is. It does not
decide what anyone believes.  Keep it that way: the moment this file decides
which utterances are worth believing, §13's hard-wired intake is back and the
corpus cannot argue with it.

## Why separate machines rather than frames

An earlier draft of this design used one machine and several frames, and argued
*against* separate machines because they share no node identity. That was
backwards. **Two minds are two scopes**, and the design decides identity at
intake, by construction, in a scope -- so `sword` in the DM's head and `sword`
in a player's head SHOULD be different nodes. Separate machines give belief
separation structurally; frames would have needed a floor change, because a
frame branched off a trunk cannot see the trunk advance.

## Determinism, which is the property this costs the most to keep

§3 forbids reading a derived result out of an unordered source, and the repo
measures byte-for-byte reproducibility. A table of agents has three orderings
that would otherwise be incidental, and all three are declared here:

    agents run in the order they were added
    an agent's utterances keep the order the machine emitted them
    deliveries are applied speaker-by-speaker in that same agent order

A round is a **barrier**: every agent runs to quiescence, and only then is
anything delivered. So an utterance made in round N is heard in round N+1, never
mid-thought. ⭐ That is what makes a process-backed table produce the identical
transcript to a single-process one, and `main()` asserts exactly that.

## What cannot cross, measured rather than assumed

| | |
|---|---|
| a proposition -- `locked(door1)` | re-reads fine |
| a moment -- `moment()` | **refused** by the parser, and every moment renders alike |
| an entry -- `entry(moment(), locked(door1), +)` | **refused** |
| a rule -- `<r>` | **refused** |
| anything containing a variable | **refused** -- `_say` checks |

So an agent cannot utter **a time, an act of claiming, or a rule**. No agent can
teach another a rule, and none can say *this happened before that* -- which is
`docs/authoring.md` §6's missing member kind, arriving from a second direction.

 **And never compare node ids across machines.** Two graphs built in the same
order assign the same integers, so a cross-machine identity test is accidentally
right often enough to pass. Probed: equal in one case here, unequal in another.
Compare rendered text.

## `hear_or_refuse`

Hear it, or say why it could not be heard.

         **An agent really will try to say the unsayable, and the wire must
        not die of it.** `blocked($g)` reports the rule's antecedent member *as
        written*, so a blocked subgoal is generic far more often than not — and
        an arrival may not contain a variable. Left to raise, one over-eager
        rule in one corpus takes the whole table down.

        Swallowed silently it would be worse, so the refusal is RETURNED and the
        table records it: §5's *a silence is the defect*, at the one boundary
        where the speaker cannot know whether it was understood.

         **And a refusal is not the only way to mishear.** `Loader.term`
        parses ONE term and ignores whatever follows it, so `a(b)(c)` -- a node
        whose relation is itself a structure, which the substrate builds happily
        -- comes back as `a(b)` with the `(c)` dropped and **no exception at
        all**. The hearer then believes something the speaker did not say, and
        every check in this module would have called that a successful delivery.

        So the text is re-rendered from what was actually understood and compared
        with what was sent: an utterance that does not round-trip is refused.
         That makes `show` and the parser each other's check at the one place it
        matters, which is cheap here and would not be if the wire were hot.

## And the engine now refuses it at the sourc

⭐⭐⭐ **And the engine now refuses it at the source, so this check changed
what it is watching.** It asserted the round-trip guard's own message
(`heard as a`), because `Loader.term` silently returned `a` for `a b` and
this guard was the only thing between a mishearing and a clean delivery.
`docs/quest-feedback.md` §5 reported that, and `term` now raises instead:
what one agent says is what another believes, or the wire is a lie.

 So the assertion is *refused, and nothing was believed* rather than
*refused by this particular layer* -- otherwise the check fails the moment
the defect it was written against is fixed, which is the wrong way round.
The guard stays: it is now defence in depth rather than the only line, and
it still catches anything that parses cleanly into the wrong node.

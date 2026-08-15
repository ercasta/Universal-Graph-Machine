# A table of agents: the layer below the machine

For the ugm team. `ugm/table.py`, commit `73dc260`, 14 checks. Everything below
was run against `f4631e3`, not recalled. `ugm.dungeon` 17/0 and the suite 529/0
are unaffected — **this needs nothing from the engine.**

## What it is

Several agents, each a `Machine` with its own name scope, its own chain and its
own corpus. Nothing is shared. What crosses between them is an **utterance** —
rendered text, re-read through `Loader.say` in the hearer's own scope — and what
the hearer does with it is a trust rule in its corpus.

```
    dm ── +doing(tell(p1, locked(door1))) ──▶ actuator ──▶ [wire] ──▶ channel ──▶ says(dm, locked(door1), plus) ── p1
```

A round is a barrier: every agent runs to quiescence, then everything said is
delivered. So an utterance made in round N is heard in round N+1, never
mid-thought.

⭐ **The wire turned out to be only a wire, because both ends already existed.**
`actuator` is documented as *a channel that carries intents OUT … acting is the
same relation read the other way*, and `Loader.say` is the scoped door for
arrivals. Between them there was nothing left to design: this module renders,
routes, and decides whose turn it is. It does not decide what anyone believes,
and we would ask that it never be allowed to — the moment the wire picks which
utterances are worth believing, §13's hard-wired intake is back and no corpus can
argue with it.

## Two machines, not two frames — and we had it backwards first

The first draft used one machine and several frames, arguing *against* separate
machines on the grounds that they share no node identity. That was the wrong way
round. **Two minds are two scopes**, and this design already decides identity at
intake, by construction, in a scope — so `sword` in the DM's head and `sword` in
a player's head *should* be different nodes. Separate machines give belief
separation structurally.

It also dissolves a problem frames could not solve without a floor change: a
frame branched off a shared trunk cannot see the trunk advance, so the shared
world stops being shared at the moment it changes. With separate machines there
is no trunk — the DM's world is simply the DM's beliefs, and everything else
learns of it by being told.

## Measured

**Startup is not a constraint.** 6ms per machine, **17 bundle rules per machine**
(we had misread `ugm.shapes`' 3,686 as per-machine; it is the total across the
217 machines the suite builds — 3686/217 ≈ 17). Six agents cost 37ms.

**What cannot cross**, probed rather than assumed — all refused at the hearer's
parser, none silently mangled:

| | |
|---|---|
| a proposition — `locked(door1)` | re-reads fine |
| a moment — `moment()` | **refused**, and every moment renders identically |
| an entry — `entry(moment(), locked(door1), +)` | **refused** |
| a rule — `<narrate>` | **refused** |
| anything containing a variable | **refused** — `_say` checks |

**Processes are equivalent.** One OS process per agent over `multiprocessing`
queues produces the identical transcript and the identical beliefs, round for
round. Because crossing is already text, the queue carries the same payload the
in-process wire does — the transport is a swap, not a redesign.

⚠ **Never compare node ids across machines.** Two graphs built in the same order
assign the same integers. Probed twice: equal in one case, unequal in another. A
cross-machine identity test is accidentally right often enough to pass a check.
Compare rendered text.

## Three things for you

**1. An agent cannot utter a time, and this is a second and different argument
for the missing member kind.** `docs/authoring.md` §6 sizes *the goblin acts
after the hero* as the cheap half, and `at ?m` has shipped. But that is
intra-agent. Between agents, a moment cannot cross at all: every moment renders
as `moment()`, so even a parser that accepted it would lose identity. **Two
agents can never refer to the same time.** If a table is ever to agree on
sequence — *you attacked before I did* — a moment needs a renderable, re-readable
name. We are not asking for it yet; we are flagging that spans-as-loci solved the
intra-agent half of a problem whose inter-agent half is untouched, and that the
two will look like one requirement when someone hits them.

**2. No agent can teach another a rule.** It falls out of *a fact may not contain
a variable*, so it is presumably deliberate — but it means a DM can say *the door
is locked* and can never say *locked doors need keys*. Is that a position or an
accident? For a table of agents it is a real ceiling, and we would rather know
which it is before designing around it.

**3. `m.emitted` is cumulative and carries no dispatched marker.** Anything
integrating acts has to keep its own cursor, and getting that wrong is silent:
shipping the whole list each round re-tells everything, every round, for ever —
and it is quiescence-proof, because each arrival is a fresh entry. We keep the
cursor in `Agent.think`. A `taken`-style marker, or a line in the docs, would
save the next caller the same bug.

## An instrument lesson, since your traps file collects these

⚠⚠⚠ **An A/B between two implementations is blind to any bug they share.**

We built `Local` and `Processes` and checked they agree — nine checks, all green.
Two real bugs were invisible to every one of them, because both live in `Agent`,
which both transports use: shipping the whole cumulative `emitted` list, and
delivering every utterance to every agent. The comparison could not see either,
and neither could anything else, because the comparison *was* the instrument.

The fix was checks that pin the behaviour rather than compare the arms — *nobody
repeats themselves and the table goes quiet*, *an utterance is directed and the
third agent has no record of the speaker*. Both were written by putting the bug
in first.

⚠⚠ **And one check was worse than useless as first written.** The transcript
comparison catches arrival-order collection only when the OS scheduler *happens*
to reorder replies — green on most runs with the bug present. The ordering is now
a pure function handed a deliberately reversed dict, so it fails every run. A
check whose sensitivity depends on a race reports green while the bug is there,
which is worse than not having written it.

## What we are doing next

The DM and two players, with **goals** — which is your standing ask, and the
thing a table makes natural rather than contrived: a player whose goal it cannot
reach alone runs to quiescence, `<give-up>` writes `blocked`, and *that* is the
occasion to ask another agent for help. If it works it exercises `fit`, `check`,
`verdict`, `subgoal` and `blocked` from a corpus written outside your repository,
which you have said is the largest single unknown in the project.

We will also want a **disagreement report** — what does `p1` believe that the DM
does not — because with disjoint graphs that comparison is over rendered text and
it is the natural measure of fog of war, and of a DM that lies.

# Several agents

Everything so far has been one mind. Chapter 21 gave it channels — a way for
the world to speak to it.

Point two of those at each other and you have a second thing entirely: **a
table of agents**, each with its own beliefs, talking.

```
dm.g.show(locked_door1) --text--> p1.channels.deliver(dm_channel, reparsed)
```

An agent's beliefs are **its own graph**. Nothing is shared: two `Machine`
instances hold two graphs, and a node in one names nothing in the other.
What crosses is **rendered text**, re-parsed in the receiver's own name
scope — and what the receiver does with it is a trust rule in its own
corpus, exactly like Chapter 21's `<trust_user>`.

```python
dm, p1 = Machine(), Machine()
load_file(dm, "dm.ugm")
kb1 = load_file(p1, "p1.ugm")   # p1.ugm has: rule <trust_dm> = implies(
                                 #   { +says(dm, $p), no believed_it($p) },
                                 #   { +$p, +believed_it($p) } )
dm.run(limit=10)

locked = dm.g.rel(dm.g.atom("locked"), dm.g.atom("door1"))
kb1.say("dm", dm.g.show(locked))   # "locked(door1)" -- literally the rendered text
p1.run(limit=10)
```

```
p1 believes:
  ['arrived(dm, locked(door1))', 'believed_it(locked(door1))',
   'locked(door1)', 'says(dm, locked(door1))']
```

`dm.g.show(locked)` is nothing but `str(node)`, and `p1`'s only route back
in is `kb1.say`, the same door Chapter 21 uses for a human or a sensor. Two
machines that already existed, talking through a door that already existed.
Nothing new had to be built for this to work.

## The wire is only a wire

That's the whole of it, and it must stay that way:

> The moment something decides which utterances are worth believing on the
> receiver's behalf, hard-wired intake is back and no corpus can argue with
> it.

Whatever relays text between two `Machine`s renders what one emitted, hands
it to the other's channel, and decides whose turn it is. It does not decide
what anyone believes — that's still `<trust_dm>`'s business, an ordinary
rule the receiving corpus wrote and can revise.

## Two minds are two scopes

`sword` in the DM's graph and `sword` in a player's graph are different
nodes, minted independently, and that's a feature: belief separation is
**structural**, not something a corpus has to be careful about. There is no
shared trunk either machine could accidentally read past — the DM's world is
simply the DM's beliefs, and everything else learns of it by being told.

## Fog of war is structural

Before anyone tells a player about the locked door, the player's graph holds
**nothing** about it — not because the corpus was careful, but because the
fact lives in a graph the player's `Machine` cannot reach at all.

Two more, checked directly against the two-machine sketch above:

- **Delete the trust rule and the player is told, and still believes
  nothing.** `arrived(dm, locked(door1))` still lands; `locked(door1)`
  never does.
- **What it was told stays on its own record regardless.** `arrived` is an
  unconditional deposit — it happens the instant `channels.deliver` runs,
  before any rule gets a turn to decide what it means.

An utterance is also **directed**: the DM spoke on a channel named `dm`, and
a third machine that was never handed that text has no record of the DM
speaking at all. Broadcasting to every machine would leak the world to an
agent no rule ever told.

## What crosses, and what doesn't

Probed against the current parser, not assumed from an older one:

| | |
|---|---|
| a proposition — `locked(door1)` | re-reads fine |
| an atom of any shape — `moment(m1)` | re-reads fine; nothing is special about the word `moment` any more |
| a rule's **name** — `<narrate>` | re-reads fine, as an ordinary term |
| anything containing a variable | **refused**, at the receiver's parser |

That table is shorter than it used to be, on purpose. `moment` and `entry`
were refused once because they named a locus and an entry — real,
structural things a corpus could not be allowed to fabricate. Neither
exists any more (Chapter 19), so there is nothing special left to refuse:
`moment(m1)` crosses exactly like `kettle(m1)` would, because as far as the
parser is concerned that's all it now is.

What *is* still refused, and for the same reason it always was: a fact may
not contain an unbound variable, on either side of the wire. `say ch:
+locked($x)` fails to parse before it ever reaches a channel.

## Two real ceilings

Both fall out of rules you already know.

**Two agents can never refer to the same time.** There is no shared
ordering left even *within* one agent (Chapter 23) — every corpus keeps its
own round counters, its own `next(...)` facts, entirely locally. Between
agents there is not even that: nothing renders a round number that means
the same thing on both sides unless the two corpora agree on the convention
by hand, which is a fact about the corpora, never something the engine
arbitrates.

**No agent can teach another a rule.** A fact may not contain a variable, so
a DM can say *the door is locked* and can never say *locked doors need
keys* — that's `implies({+door($x)}, {+needs_key($x)})`, and it has a
variable in it. The wrinkle worth naming: a rule's bare **name**, `<r>`,
crosses the wire fine as an ordinary atom, the same way `moment(m1)` does.
What can't cross is the rule's *body* — its antecedent and consequent — so
receiving `<r>` tells the other agent nothing about what `<r>` does unless
it already has a rule by that name of its own.

## The other axis: experts

There's a second way to have more than one mind, and it is the opposite
axis from agents:

| | **agents** | **experts** |
|---|---|---|
| what differs | what they **believe** | what they **know how to do** |
| the graph | one each, disjoint | **one, shared** |
| what crosses | rendered text, re-read in the hearer's own scope | nothing — a conclusion is simply there |
| fog of war | structural | none, by construction |

Two agents can disagree about whether the door is locked. Two experts
cannot, because there is one graph and one answer. What an expert has of
its own is which rules apply — ordinary facts, reasoned with by one ordinary
rule, inheritance included:

```
rule <extend> = implies( { +extends($e,$f), +knows($f,$c), no knows($e,$c) },
                         { +knows($e,$c) } )
rule <equip>  = implies( { +runs($w,$e), +knows($e,$c), no can($w,$c) },
                         { +can($w,$c) } )
rule <grab>   = implies( { +at($w,$x), +can($w, grabbing), +treasure($x),
                           no found($w,$x) },
                         { +found($w,$x) } )

fact +knows(scout, moving)     fact +knows(looter, grabbing)
fact +extends(raider, scout)   fact +extends(raider, looter)
fact +runs(w1, raider)         fact +at(w1, r3)   fact +treasure(r3)
```

```
$ python -m ugm expert.ugm --ask "found(w1, r3)"
found(w1, r3): believed
```

A `raider` that extends both `scout` and `looter` gets `moving` from one
and `grabbing` from the other, through one ordinary rule with no
resolution order to declare — multiple inheritance falls out for free. The
honest definition of the difference from a tool (Chapter 22):

> A **tool** is a request answered by a function rather than by a search.
> An **expert** is a request answered by a *search* rather than by a
> function.

**What it costs, stated rather than discovered.** An expert's conclusions
are not contained. One graph was the whole point, so a rule that concludes
nonsense has concluded it for everybody. That's the price of sharing
beliefs, and it's exactly why the agents above exist for the other case.

## A third axis: walkers

There is a third way to have more than one of something: **where in the
structure** it is, tracked as nothing but a fact.

```
at($w, $x)          where a walker stands
child($w, $y)        one it spawned
```

`child($w, $y)` is a compound over already-bound variables, which is legal
in a consequent: a rule may introduce a *reference* to something as long as
every part of it is denoted. What a rule may not do is conclude about a
variable nothing binds.

**A walker spawns rather than moves.** Two doors out of one room, and a
walker that tries to both step *and* fork wants to be in two places built
from the same fact — whichever rule wins denies the premise the other
needed, and the loser is deferred, never refused, so the run keeps trying
it. Spawning avoids the collision outright: nothing is denied, so nothing
is contended.

```
rule <fork> = implies( { +at($w,$x), +door($x,$y), no done($w),
                         no at(child($w,$y), $y) },
                       { +at(child($w,$y), $y) } )
rule <grab> = implies( { +at($w,$x), +treasure($x), no found($w,$x) },
                       { +found($w,$x) } )
rule <done> = implies( { +found($w,$x), no done($w) },
                       { +done($w) } )
```

```
$ python -m ugm walker.ugm --ask "found(child(child(w0, r2), r3), r3)"
walker.ugm: 5 ticks, ended quiescent
found(child(child(w0, r2), r3), r3): believed
```

!!! warning "Termination is a denial — and under the scratchpad, that's now wrong"
    The obvious way to write `<done>` is to erase the walker's position once
    it succeeds: `implies({+found($w,$x)}, {-at($w,$x)})`. Under the old
    chain that was safe — a denied claim stayed on the record, so nothing
    downstream could be fooled into thinking it had never happened.

    Under the scratchpad it is a bug, and a genuinely instructive one:
    `<fork>`'s own guard is `no at(child($w,$y), $y)` — *absence*, checked
    against the state as it stands right now. Erase `at(child(w0,r2), r3)`
    once the walker is done with it, and that absence guard is satisfied
    again on the very next tick. `<fork>` fires again, `<done>` erases
    again, forever:

    ```
    0  fork  at(child(w0, r2), r2)
    1  fork  at(child(child(w0, r2), r3), r3)
    2  grab  found(child(child(w0, r2), r3), r3)
    3  done  at(child(child(w0, r2), r3), r3)     -- erased
    4  fork  at(child(child(w0, r2), r3), r3)      -- and re-spawned
    5  done  ...                                    -- and erased again
    ```

    The fix is the same one Chapter 21 landed on for arrivals: a denial and
    an absence guard are not partners, they're the same trap with a
    different name. **Terminate additively.** `<done>` writes `done($w)`
    rather than erasing `at($w,$x)`, and every other walker rule guards on
    `no done($w)` instead. Nothing here is ever un-concluded; the walker is
    simply marked finished, and finished stays finished because nothing
    erases it.

    > **A fact that's been erased is exactly as absent as one that was
    > never asserted.** Anything that reads absence to know when to stop
    > has to be told to stop by something that only ever grows.

This reverses the old chapter's own conclusion (*"termination is a denial,
and it is not retroactive"*) — which was correct for the chain it was
written against and is a real trap for the scratchpad that replaced it.

**What this doesn't do.** Cycles are still unbounded — a maze with a loop
grows `child(child(child(…)))` without a limit, and *do not go where you
have been* needs a negation over the walker's own path, which nobody built
here. The comparative measurements the old chapter carried (spawn-versus-
move tick counts, by-path-versus-by-node dedup counts) came from probes
that no longer exist in this repo, so they aren't repeated — a number this
book won't stand behind is a number it doesn't print. What's verified above
is the corrected mechanism, run for real against the current engine.

## Why this is the natural home for `blocked`

A player whose goal it cannot reach alone runs to quiescence, a `<give-up>`
rule writes `blocked(...)`, and a corpus can key on it directly:

```
rule <ask-for-it> = implies( { +blocked(have(p1, $k)) },
                             { +wants(dm, give(p1, $k)) } )
```

With one agent that's a little contrived. With several it is the whole
point: `blocked` is the occasion where another mind is worth anything at
all.

---

That's Part 5. The machine now handles stretches, indefinite patterns,
other people's words, numbers, and other minds — all of it, now, without a
history to lean on.

The remaining parts are optional. They turn the machine around to look at
itself.

**Next:** the agent's own commitments, as ordinary facts.
[The agent's own state →](../watching/25-own-state.md)

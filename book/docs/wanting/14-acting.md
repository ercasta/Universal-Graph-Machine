# Acting

**An action is not a new kind of thing.**

An action is an event; an event is a moment; and `heat(anna, kettle)` is a fact
that holds over an interval. So an action enters a rule's antecedent as an
ordinary member, and *to execute* means **make this event-fact true**.

There is no action construct, no operator schema, and no plan-step type
alongside the rules.

## The whole thing, working

```
rule <boil> = causes( { +heat(anna, kettle), +water(kettle) },
                      { +boiling(kettle) } )

rule <use-hob> = implies( { +blocked(heat(anna, kettle)), +has(anna, hob) },
                          { +doing(heat(anna, kettle)) } )

fact +water(kettle)
fact +has(anna, hob)
fact +goal(boiling(kettle))
```

```
20 ticks, ended quiescent

asked for:
  boiling(kettle)  [held]  via <boil>
    water(kettle)  [held]
    heat(anna, kettle)  [held]
did:
  heat(anna, kettle)
```

Read what happened. The goal was expanded backwards; heating came out as a
subgoal; nothing could derive it, so it was reported `blocked`; the corpus's own
rule saw that occasion and concluded `+doing(...)`; the machinery carried the
intent out past the boundary; and the water boiled.

The trail, top to bottom:

```
why boiling(kettle)?
  +boiling(kettle) @M1, licensed by applied(<boil>)
    because +heat(anna, kettle) @M0, licensed by applied(<assert-act>)
    because +water(kettle) @M0, licensed by loaded(water(kettle))
    because +did(heat(anna, kettle)) @M0, licensed by applied(<did>)
    because +emitted(heat(anna, kettle)) @M0, licensed by utterance(kb, heat(anna, kettle))
    because +doing(heat(anna, kettle)) @M0, licensed by applied(<use-hob>)
    because +blocked(heat(anna, kettle)) @M0, licensed by verdict(heat(anna, kettle))
```

Four rules you never wrote appear in there — `<assert-act>`, `<did>`,
`<give-up>`, `<expand>`. They ship with the machine, as ordinary rules, in the
same language. You can read them, and you can drop them.

## Acting is a channel read the other way

Channels carry the world **in** (Chapter 21). Acting carries an intent **out**,
and needs no new construct for the same reason an action needs none: a rule
concludes `+doing(p)` like any other fact, and the machinery carries it past the
boundary because a boundary is anchored and a rule is generic.

Three things about the write that follows, each found by building it.

### The agent asserts the act

*To execute means make this event-fact true.* So having acted, the agent writes
`+heat(anna, kettle)` — licensed by the doing, not by any report from the world.

That is **not** a claim about the world's response. It's what gives the rules
something to apply to, and it's what gives an expectation something to be
disappointed by. Without it, the agent emits an intent into silence and nothing
downstream ever happens.

And it is a **rule**, `<assert-act>` — the first place in this design where a
strategy written as code became a claim. An agent that should *not* assume its
acts succeed is now expressible by dropping one rule, and it still acts and
still knows it acted.

### A description cannot be acted on

`+doing(heat(?a, ?w))` is refused. An intent with an unbound member names no
particular act.

This is Chapter 12's achievability question arriving where it belongs — not as a
mark on a rule's member, but as a condition at the one place effects leave the
agent.

### And that refusal has a consequence nobody intended

A rule node is generic by construction, because it holds the variables of its
own patterns. So `+doing(ask(<hot>))` — *ask the author about the rule that
lost* — is refused for the same reason.

Which means **every clarification request about a rule is decided on and never
emitted.** That's the use/mention distinction of Chapter 10 arriving at the
boundary, where the entry already carries the information needed to tell the two
apart and nothing reads it.

Chapter 34 records it as an open defect, because it is one.

## An action is a rule, its bindings, and a free marker

Everything above is about the boundary. This is about the **shape** of what
crosses it, and it is the shape a learned policy would have to be written over:

```
a rule          which of the authored rules to use
bindings        what to use it on
a marker        free structure, meaning whatever rules make of it
```

The first two make the action. The third makes the **context sayable** — without
it, two situations identical in the world but different in what the agent was
doing are indistinguishable, and no policy can tell them apart. With it the
number of distinguishable situations is unbounded while the action's *shape*
stays fixed, which is what keeps a learner's job small.

Nothing had to be added for this. The dungeon corpus had been writing the triple
for a long time:

```
say player: +declares(attack(goblin1), 1)

rule <trust-player> = implies( { +says(player, declares(?act, ?r), plus) },
                               { +intends(hero, ?act, ?r) } )
```

`attack(goblin1)` is the act with its binding, and `?r` is the marker — which the
corpus's own header calls *a label the player utters* and which nothing then
interprets. That the slot was authored before anyone asked for it is the best
evidence available that the shape is natural rather than imposed.

A rule that **does** read the marker picks a different binding for the same
declared act. One fight, four markers:

```
1                  first swing  hit(hero, goblin1)   rounds 18  swings 8
focus(goblin2)     first swing  hit(hero, goblin2)   rounds 14  swings 6
focus(goblin9)     first swing  hit(hero, goblin1)   rounds 18  swings 8
careful(goblin1)   first swing  none                 rounds  0  swings 0
```

Row two is the point: same act, same bindings, a different marker, a different
**target**, and the fight still reaches a verdict — so the marker changed what
was done rather than whether anything was. The marker may be arbitrary structure,
because it rides through `<trust-player>` untouched.

> **The marker is read by rules and never followed by machinery.** The moment a
> host-language function dereferences one to decide what happens next, the loop
> has stopped being the only thing that decides, and Chapter 32's phases are
> back.

Rows three and four are the two silent failures, and both are worth knowing:

**A marker nothing matches is not an error.** Name a target that is not there and
the discriminating rule simply does not apply. The declared act goes through and
the fight looks entirely normal — so a mistyped policy **quietly stops steering**,
and a policy that has stopped steering is indistinguishable from one that had
nothing to say. Chapter 13's rule about silences, arriving inside one agent.

**A rule that spends the turn without feeding the clock freezes everything.** The
first version of the marker rule concluded *hold* instead of an attack: the turn
is consumed and nothing passes the baton. Zero rounds with every combatant alive,
which reads as a peaceful encounter rather than a stall — and it passed the check
it was written for. The check now asserts the stall.

Which lever should carry a learned steer is a separate question, and it has a
measured answer: Chapter 28.

## Supposing something must not bring it about

One more boundary rule, and it's the one that would be a genuine safety problem
if it were wrong.

Chapter 16's containment says no *entry* leaves a frame. That is a claim about
the **chain** — a walk from the real world can't reach into a hypothesis.

**Effects are not in the chain.** An intent concluded inside a supposition would
otherwise be carried out for real, and imagining would become doing.

Structure isn't in the chain either, and there the same argument has no muting
rule behind it: a stratum-0 conclusion drawn inside a hypothesis is visible from
everywhere. Chapter 16 measures it. Acting is the case somebody thought about;
it is worth knowing that it was the only one.

So the boundary is muted inside a supposition. The general form:

> Conclusions stay at their locus. What crosses out of a frame is a claim
> *about* the frame, made from outside it.

What planning needs from an act is the **decision** — that this is what I would
do — and the decision is a conclusion, which crosses. The doing does not.

The same muting applies to replaying a saved session: the agent remembers
acting, and nothing leaves twice.

---

That's Part 3. The machine can now want something, work backwards to what would
bring it about, report honestly when it can't, and act.

**Next:** everything so far has been stated flatly. Time to say things you're
not sure about.
[How strongly →](../unsure/15-how-strongly.md)

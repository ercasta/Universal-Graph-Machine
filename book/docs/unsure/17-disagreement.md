# When two rules disagree

*The wounded heal. The poisoned do not.*

```
rule <regen>  = implies( { +wounded($x) },                { +heals($x) } )
rule <poison> = implies( { +wounded($x), +poisoned($x) }, { -heals($x) } )
```

`a` is wounded and poisoned. `b` is only wounded. What should happen is obvious.
Getting there is where most people's first attempt goes wrong.

## The attempt that looks right

The machine has one way to take a rule out of the running: say it is dormant.
So reach for it — poison is in the room, put regeneration to sleep.

```
fact +dormant(<regen>)
```

Run it:

```
$ python3 -m ugm quarantine.ugm --ask "heals(a)" --ask "heals(b)"
heals(a): not believed
heals(b): not believed
```

Both come back `not believed`, and that is flatter than it should be: there is
no derivation trail any more (no `--why`, nothing a rule can read that says
*this came from a denial* versus *this came from nothing at all*), so the two
reasons collapse into one printed line. The reasons are still different —
`<poison>` still runs for `a` and has something to say; `<regen>` never runs
for `b` at all, because a dormant rule doesn't run for anyone — but nothing
short of reading the rules themselves shows you which is which any more.
**`b` gets nothing at all,** and it's collateral, not correct.

`dormant` is **per rule**. A rule that is out is out for everybody, so `b` — whom
nobody poisoned — stops healing too. And it stays that way, because nothing here
ever claims `due(<regen>)`.

> **Taking a rule out is per rule. It does not carve out cases.**

Put the case where the case lives — in the antecedent:

```
rule <regen> = implies( { +wounded($x), no poisoned($x) }, { +heals($x) } )
```

```
$ python3 -m ugm regen.ugm --ask "heals(a)" --ask "heals(b)"
heals(a): not believed
heals(b): believed
```

Nothing had to be written about `b` at all. `no poisoned($x)` asks whether
anything anywhere claims poison, positively or negatively — and for `b`
nothing does, so the premise holds on its own.

| how it's written | `heals(a)` | `heals(b)` | |
|---|---|---|---|
| `dormant(<regen>)` | not believed | not believed | b is collateral damage |
| the exception as a **premise** | not believed | **believed** | correct |

That's `unless`, written where the rule's variables live (Chapter 10) — and it
costs nothing for `b`, which is the point. `no poisoned($x)` is a check, not a
binder: it asks *does anything say this*, and for `a` the answer is `+poisoned(a)`
sitting in the graph, so the check fails and `<regen>` doesn't apply. Absence
is not denial, and here that's what makes the premise cheap: nobody had to
assert `b`'s innocence for it to hold.

## There's no precedence relation

Nothing in this design ranks one rule over another. There is no `overrides`,
no `supersedes` — check the machine's own vocabulary and neither name means
anything to it. Write `fact overrides(<poison>, <regen>)` into the corpus
above and nothing changes: it's an ordinary, uninterpreted proposition,
exactly as inert as any other name a corpus never wires a rule to read.

> **There's no precedence relation. The exception goes inside the rule.**

There is no relation to name `<poison>` and `<regen>` together, no matter how
that relation is spelled. The exception goes **inside the losing rule**, as a
negated member, because the antecedent of `<regen>` is the only place it can
live and still see the variable it's about — a fact naming the exception
separately, from outside the rule, can't reach `<regen>`'s own `$x`.

## When taking a rule out *is* the right answer

`dormant` stays, and it is the right tool for a different question. Not *this
individual is an exception* — that is a premise — but *this rule should not be
considered at all right now*.

A rule can conclude it, which means the agent can settle a conflict between two
of its own rules by deciding which one is out. And `due(<R>)` puts it back, so
it is a claim like any other rather than a configuration:

```
rule <hot>      = implies( { +sensor },   { +alarm } )
rule <referee>  = implies( { +override }, { +dormant(<hot>), -override } )
fact standing(<referee>)

fact +override
fact +sensor
```

```
$ python3 -m ugm referee.ugm --ask "dormant(<hot>)" --ask "alarm"
referee.ugm: 2 ticks, ended quiescent

dormant(<hot>): believed
alarm: not believed
```

Two moves, and the run reaches quiescence. What makes that safe is the same
thing that makes a premise the right tool for an individual exception: the
loser here has genuinely stopped being considered, rather than being ranked
low and applying later anyway.

## Arbitration is scheduling, not decision

Here's the reframing that makes the whole area easier to think about.

> **A loser is deferred, not rejected.**

When two applications compete and one wins, the other doesn't vanish. It's still
there next tick, and if its situation still holds it will get its turn. The
machine runs to quiescence, so **ordering alone is not defeasibility** — a low
score delays a rule and never removes one.

That is exactly why authored order can't do the job a premise does: order is a
tiebreak among rules that both apply, not a way to take one out of
consideration. Only a premise — or `dormant`, wholesale — does that.

Which has a consequence that took a while to see, and it's a nice one:

> **What turns an order into a default is stopping.**

Ask, take the first rule that matches, act. So *completion is the output of a
rule* isn't a detail of the design; it's what makes a preference mean anything
at all. Chapter 26.

## When your negatives are not enumerable

The one case that genuinely resisted a premise: *the hero attacks by default
when the player has declared nothing this round.* You cannot write
`-declares(hero, $what)`, because absence is not denial and you don't know what
might have been said.

There are two answers now, and it is worth knowing which applies.

`no p($x)` asks about absence directly — *nothing currently asserts this* — and
it is a check rather than a binder, so every variable in it has to arrive bound
from an earlier premise. `no hp($x, 1)` works because `$x` is bound. *The player
said nothing about anything* does not: it would mean *for no `$what`*, which is
a negative existential and a member cannot mean that.

The second answer is the one the dungeon actually uses, and it is a corpus's own
discipline rather than a feature: **an occasion is consumed.** The two acting
rules spend `may(hero)`, so when a declaration is live one of them takes the
tick and the standing policy has no right left to act on. Nothing has to defeat
anything.

## What the machinery knows, it writes down

Whatever settles a disagreement between rules should be something a rule can
read, never something only the machinery holds internally:

> **Something the machinery knows and no rule can ask about is a defect, and the
> repair is always to deposit the record.**

In the `<referee>` example above, the claim that takes `<hot>` out is the
corpus's own: a rule concluded `dormant(<hot>)`, dated and attributable, and
any rule can read it. There is nothing left for the machinery to track on a
corpus's behalf.

The pattern itself is stable enough to use as a search: **anything the loop
computes per tick and does not write down is a candidate.** A run still
working when the tick limit bites deposits `bounded(ticks)`, so a corpus can
notice its own runaway rather than a human watching the console for it. The
strength of a claim is a wrapping term (Chapter 15). And the newest one: when
a trigger changes what a rule concluded, that is `rewrote(<T>, old, new)`
(Chapter 16), because a conclusion that is not what the rule said it concluded
cannot be reported as the rule's alone.

---

**Next:** the one thing that is *not* argued about.
[What it may never do →](18-norms.md)

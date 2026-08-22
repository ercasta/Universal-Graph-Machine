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
rule <quarantine> = implies( { +outbreak }, { +dormant(<regen>) } )
fact standing(<quarantine>)
```

Run it:

```
heals(a):  −
heals(b):  nothing concluded it
```

`a` is correct. **`b` gets nothing at all.**

`dormant` is **per rule**. A rule that is out is out for everybody, so `b` — whom
nobody poisoned — stops healing too. And it stays that way, because nothing here
ever claims `due(<regen>)`.

> **Taking a rule out is per rule. It does not carve out cases.**

Put the case where the case lives — in the antecedent:

```
rule <regen> = implies( { +wounded($x), -poisoned($x) }, { +heals($x) } )
```

```
why heals(b)?
  +heals(b), licensed by applied(<regen>)
    because +wounded(b)
    because -poisoned(b)
```

| how it's written | `heals(a)` | `heals(b)` | |
|---|---|---|---|
| `dormant(<regen>)` | `−` | **nothing** | b is collateral damage |
| the exception as a **premise** | `−` | `+` | correct |

That's `unless`, written where the rule's variables live (Chapter 10) — and
remember from Chapter 3 that you must then say `-poisoned(b)` outright, or
derive it. Absence is not denial.

## The machine used to have more than this, and it was worse

For most of this design's life there were two precedence relations, and the
chapter you are reading was about choosing between them.

- **`overrides(A, B)`** — if A applied at all this tick, B does not. Per tick,
  per rule.
- **`supersedes(A, B)`** — A defeats B where the two consumed the same entry.

Neither survived. Pointed at the case above, `overrides` did exactly what
`dormant` does: `a` correct, `b` collateral damage, permanently, because `a`
stays poisoned so poison matches every tick. `supersedes` did nothing at all
here — these two applications consumed `poisoned(a)` and `wounded(a)`, which
have nothing in common — so both rules applied and the ordinary read decided it:
`<poison>` wrote second, later supersedes earlier, and `b` healed by accident
rather than by anything anyone wrote.

> **Precedence ordered rules. It never carved out cases, and the exception is
> always a case.**

What finally retired them was going through every precedence in the repository
and asking what it was really saying. There were seven, and not one of them
needed a precedence relation:

| what it said | what it says now |
|---|---|
| `overrides(<gob-flees>, <gob-acts>)` | `no hp($x, 1)` — a premise about the state |
| `overrides(<hero-acts>, <hero-holds>)` | nothing: acting spends `may(hero)`, so the loser has no right left to act on |
| `overrides(<halt>, …)` ×4 | nothing: each actor already requires its combatants present |
| `supersedes(<outcome>, <assert-act>)` | `no substituted($what)` in the bundled rule, per act |

Four of the seven were doing no work at all. The rest were premises wearing a
mechanism's clothes.

## When taking a rule out *is* the right answer

`dormant` stays, and it is the right tool for a different question. Not *this
individual is an exception* — that is a premise — but *this rule should not be
considered at all right now*.

A rule can conclude it, which means the agent can settle a conflict between two
of its own rules by deciding which one is out. And `due(<R>)` puts it back, so
it is a claim like any other rather than a configuration:

```
rule <referee> = implies( { +p($x) }, { +dormant(<hot>) } )
```

Two moves, and the run reaches quiescence. What makes that safe is the same
thing that made precedence unnecessary: the loser here has genuinely stopped
being considered, rather than being ranked low and applying later anyway.

## Arbitration is scheduling, not decision

Here's the reframing that makes the whole area easier to think about.

> **A loser is deferred, not rejected.**

When two applications compete and one wins, the other doesn't vanish. It's still
there next tick, and if its situation still holds it will get its turn. The
machine runs to quiescence, so **ordering alone is not defeasibility** — a low
score delays a rule and never removes one.

That is exactly why a score could not have replaced precedence, and why the
thing that replaced it was premises rather than ranking.

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

While precedence existed, every defeat was deposited: `defeated(<loser>,
<winner>)`. Not because someone wanted a log, but because the machinery knew
something and no rule could ask about it — the recurring defect this project
names explicitly:

> **Something the machinery knows and no rule can ask about is a defect, and the
> repair is always to deposit the record.**

That record went with the relation, and the reason is worth having: the claim
that takes a rule out is now the corpus's own. A rule concluded `dormant(<R>)`,
dated and attributable, and a rule can read it — so there is nothing left for
the machinery to write down on its behalf.

The pattern itself is stable enough to use as a search: **anything the loop
computes per tick and does not write down is a candidate.** Which rule was
applied became `exercised`. What an entry rested on became `rests_on`. The
effort counters became `widened` / `reached` / `bounded`. The strength of a
claim became a wrapping term (Chapter 15). And the newest one: when a trigger
changes what a rule concluded, that is `rewrote(<T>, old, new)`, because a
conclusion that is not what the rule said it concluded cannot be reported as
the rule's.

---

**Next:** the one thing that is *not* argued about.
[What it may never do →](18-norms.md)

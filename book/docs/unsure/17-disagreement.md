# When two rules disagree

*The wounded heal. The poisoned do not.*

```
rule <regen>  = implies( { +wounded(?x) },                { +heals(?x) } )
rule <poison> = implies( { +wounded(?x), +poisoned(?x) }, { -heals(?x) } )
```

`a` is wounded and poisoned. `b` is only wounded. What should happen is obvious.
Getting there is where most people's first attempt goes wrong.

## The attempt that looks right

```
fact overrides(<poison>, <regen>)
```

Run it:

```
why heals(a)?
  -heals(a), licensed by applied(<poison>)
    because +wounded(a), +poisoned(a)

why heals(b)?
  nothing concluded it
```

`a` is correct. **`b` gets nothing at all.**

`overrides` is **per tick and per rule**. If poison matched *anywhere* this
step, regeneration does not apply — to anyone. `b` is collateral damage, and it
is permanent, because `a` stays poisoned, so the poison rule matches every tick
and regeneration is defeated every tick, for ever.

The sibling relation doesn't help either. `supersedes(<poison>, <regen>)` needs
a **shared consumed entry**, and these two applications consumed
`poisoned(a)` and `wounded(a)` respectively, which have nothing in common — so
nothing is defeated at all, and `b` and `a` both heal.

| how it's written | `heals(a)` | `heals(b)` | |
|---|---|---|---|
| `fact overrides(<poison>, <regen>)` | `−` | **nothing** | b is collateral damage |
| `fact supersedes(<poison>, <regen>)` | **`+`** | `+` | nothing is defeated at all |
| the exception as a **premise** | `−` | `+` | correct |

> **Precedence orders rules. It does not carve out cases.**

Put the case in the antecedent:

```
rule <regen> = implies( { +wounded(?x), -poisoned(?x) }, { +heals(?x) } )
```

That's `unless`, written where the rule's variables live (Chapter 10) — and
remember from Chapter 3 that you must then say `-poisoned(b)` outright, or
derive it.

## When precedence *is* the right answer

Collateral damage is survivable or permanent depending on the **winner**, and
that distinction is the refinement worth carrying:

> **`overrides` is survivable when the winning rule's situation is transient,
> and permanent damage when it is not.**

One goblin fleeing defeats another's attack for a step; then the goblin is gone
and normal service resumes. That's a one-tick deferral, and it's fine.

The two look identical when you write them, and only one of them is a bug.

Precedence is also the answer when **your negatives are not enumerable**. *The
hero attacks by default when the player has declared nothing this round* — you
can't write `-declares(hero, ?what)`, because absence is not denial and you
don't know what might have been said.

Though even that one turns out to be sayable, once you make it precise: *nothing
arrived on this channel over this stretch* is bounded and checkable, and
Chapter 19 shows how.

## Arbitration is scheduling, not decision

Here's the reframing that makes the whole area easier to think about.

> **A loser is deferred, not rejected.**

When two applications compete and one wins, the other doesn't vanish. It's still
there next tick, and if its situation still holds it will get its turn. The
machine runs to quiescence, so **ordering alone is not defeasibility** — a low
score delays a rule and never removes one.

Which has a consequence that took a while to see, and it's a nice one:

> **What turns an order into a default is stopping.**

Ask, take the first rule that matches, act. So *completion is the output of a
rule* isn't a detail of the design; it's what makes a preference mean anything
at all. Chapter 26.

## Precedence is read, not kept

This design used to maintain a table of which rule beats which. It doesn't any
more, and the deletion is instructive.

The table was a **cache of `overrides` facts**. Those facts are already in the
graph. Reading them at the position the agent is standing is:

- correct in a way the cache wasn't — precedence can be *concluded by a rule*,
  including about a rule that didn't exist when the claim was written;
- deniable, dateable and attributable, like any other claim;
- and free. Deleting the table cost the suite **6.42s against 6.38s**.

> **Precedence is read from the graph at the position the agent is standing. It
> is not kept anywhere.**

The only thing that broke was a test fixture that had been calling Python
directly.

!!! note "Deep dive: two relations, two intents"
    `overrides` and `supersedes` are not two spellings of one idea, and the
    difference was measured rather than argued:

    - **`overrides(A, B)`** — if A applied at all this tick, B does not. Per
      tick, per rule. Too broad: it takes out cases A says nothing about.
    - **`supersedes(A, B)`** — A defeats B where they consumed the same entry.
      Narrow, precise, and it runs away in a corpus where two rules rarely share
      a premise.

    Neither expresses *this individual is the exception*, and a negated member
    does. That's why the guard belongs inside the rule and the precedence
    relations belong outside it.

## A defeat goes on the record

When one rule defeats another, that fact is deposited:

```
defeated(<loser>, <winner>)
```

Not because someone wanted a log, but because the machinery knew something and
no rule could ask about it — the recurring defect this project names explicitly:

> **Something the machinery knows and no rule can ask about is a defect, and the
> repair is always to deposit the record.**

Eleven separate instances of it are recorded in this design's history. Which rule
was applied became `exercised`. A defeat became `defeated`. What an entry rested
on became `rests_on`. The effort counters became `widened` / `reached` /
`bounded`. And the two largest: the strength of a claim became a wrapping term
(Chapter 15), and the precedence table became a claim read from the graph.

The pattern is stable enough to use as a search: **anything the loop computes
per tick and does not write down is a candidate.**

---

**Next:** the one thing that is *not* argued about.
[What it may never do →](18-norms.md)

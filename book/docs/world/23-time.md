# When things happened

Time shows up in three places here, and it's worth being explicit that this is
**not three time systems**.

| | what it is | where it lives |
|---|---|---|
| **about-when** | the stretch a claim concerns | the entry's **locus** |
| **believed-since** | when the agent came to think so | the entry's **deposit moment** |
| **event description** | *afternoon*, *Tuesday*, *morning* | **members of a proposition** |

The first two are Chapter 5's two indices. The third is the one that needs
discipline, because it's already in use — `cloudy(?day, morning)` — and left
unexamined it would become a second ordering competing with succession.

It isn't one, and the rule is:

> **Calendar terms denote. The chain orders.**

*Afternoon* is a **name for a stretch of the chain**, resolved against a clock
stamp. It is not an ordering relation, and nothing may compare two calendar
terms directly. To ask which came first is to resolve both to spans and compare
endpoints — which Chapter 19 already provides.

A vocabulary that ordered calendar terms among themselves would be two orderings
that agree by convention and drift apart without anything noticing.

## Ordering two moments

A rule can bind the loci of two matched entries and relate them:

```
rule <hero>   = causes( { +ready(hero) }, { +acts(hero), -ready(hero) } )
rule <goblin> = causes( { +acts(hero) },  { +acts(goblin) } )

rule <after> = implies( { +acts(?p) at ?mp, +acts(?q) at ?mq, sanc(?mq, ?mp) },
                        { +acted_after(?q, ?p) } )
```

```
why acted_after(goblin,hero)?
  +acted_after(goblin, hero) @M2, licensed by applied(<after>)
    because +acts(hero) @M1, licensed by applied(<hero>)
    because +acts(goblin) @M2, licensed by applied(<goblin>)
```

The matcher had the locus all along — every entry carries one. What was missing
was a **pattern** for it.

That got built because a foreign corpus measured what its absence cost: **24% of
its rules were clock scaffold**, a round counter re-implementing a moment
ordinal, plus a token threaded through six acting rules and an arithmetic
operator that existed only to count rounds.

### It is ancestry, never depth

Unrelated moments get no answer rather than a false one. That's Chapter 5's
warning again, and it's why the ordering test walks the predecessor relation
rather than comparing numbers.

There's a pleasant result here. **A rule can only ever bind moments on its own
walk** — a rule matches the state resolved at its own locus, so every entry it
binds has a locus at-or-before that locus, and two such moments are both on one
path.

Measured on a chain forking 31 times: 145 orderings requested, **every pair
related**. Containment was already guaranteeing the thing that makes ordering
well defined.

### What it does not buy — and the limit is exact

A matcher sees the **resolved** state: one entry per proposition. So two
*different* facts at different moments are relatable, and **a single fact's own
history is not**.

*It was on, then it was not* finds nothing, because the superseded entry isn't
in the state.

Reaching it means matching over the **raw chain**, which is what the structural
stratum is for (Chapter 29), and it takes two rules: one to see it, one to say
it. The corpus that asked for moment ordering needed only the first half and
never once wanted the second.

## Saying *five minutes later*

Expressing *…and it boils five minutes later* takes three decisions, and each
one is a small lesson.

**1. Say which endpoints.** *The heating takes five minutes*, *boiling starts
five minutes after heating starts*, and *boiling starts five minutes after
heating stops* are three different rules that plan differently. So the timing
member relates **named endpoints**, never a bare scalar:

```
<t> = timing(<R1>, end(<A>), start(<B>))
      bound(<t>, 4min, 7min)
```

**2. It's a constraint, not a number.** A closed interval, a lower bound alone,
*eventually*, and *unknown* must all be sayable — or precision-by-silence
returns one level up. **Absent timing means unknown timing**, and that's both
legal and readable.

**3. It's a fact about the rule, not a third member of the connective.**

| | timing as a connective member | timing as a fact about the rule |
|---|---|---|
| not leaking | an absent delay defaults to something nobody stated | absent means absent |
| not lossy | one delay per rule, no provenance | several claims, each attributed |
| readable | — | *which rules are slower than five minutes* is a query |
| composable | the connective's arity varies | timing joins independently of the connective |

That third row is the real one: *the manual says five, I measured seven* is a
thing people actually say, and it's unsayable if the delay is a slot.

## Timing is read both ways

**Forwards**, it says when to expect the effect — and therefore when its absence
is a **deviation** rather than merely patience. Chapter 24 is what matches
against that.

**Backwards**, it's a **filter**: needing boiling water within two minutes rules
this rule out of the plan.

A rule with no timing expresses neither, and that's the honest answer rather
than a default.

And because **waiting is an action**, this is also how a precondition the agent
cannot *make* true gets planned for. *It must be a Tuesday* is achievable at a
price of up to seven days, and the price is a timing constraint — sayable,
absent when unknown, and comparable against a deadline. That's what Chapter 12
leans on when it refuses to mark a member unachievable.

---

That's Part 5. The machine now handles stretches, indefinite patterns, other
people, numbers, and clocks.

The remaining parts are optional. They turn the machine around to look at
itself.

**Next:** the agent's own commitments, as ordinary facts.
[The agent's own state →](../watching/24-own-state.md)

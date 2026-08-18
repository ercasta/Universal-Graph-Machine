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

!!! note "Deep dive: and then it did not remove the scaffold"
    The obvious next step was that `at ?m` would collapse that scaffold, since a
    round integer is a moment ordinal re-implemented in a corpus. That was
    proposed in writing, and it is **wrong** — which is worth showing, because
    the reason is a property of the read you already know.

    A request is a fact. Asking `roll(d20, hit(a, b))` twice is one node, so the
    second ask restates what the chain already says and quiescence drops it —
    which is why the corpus put the round in the request in the first place.

    Deposit that request at a *later locus* instead, and nothing changes: **the
    read inherits**, so the chain already answers `+` there, the application
    changes nothing, and quiescence drops it again. Measured on a three-beat
    fixture: one ask, not three.

    > **A locus cannot make a proposition fresh, because silence means
    > unchanged.** Chapter 3, arriving somewhere nobody expected it.

    What does work is Chapter 7's law, which the corpus was applying to
    everything *except* its requests: **an occasion is consumed, and a fact is
    not.** Deny the request and its answer in the same breath as consuming them
    and the next ask is a genuine change — three asks, no argument and no locus.

    So the round was never carrying the occasion. The **denial** was missing.
    Collapsing it took the corpus from 21 rules to 19, from 65 member positions
    carrying a round to 6, and removed the arithmetic operator entirely.

    What survives is one job: `?r` on the *player's declaration*, because an
    agent cannot utter a moment (Chapter 24). A round label is the only
    vocabulary a channel carries.

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

### What `at ?m` does not buy — and it is not what it looks like

A matcher sees the **resolved** state: one entry per proposition. So two
*different* facts at different moments are relatable, and **a single fact's own
history is not**.

*It was on, then it was not* finds nothing through `at ?m`. The reason is worth
getting exactly right, because the obvious explanation is the wrong one.

`at ?m` is **not** *evaluate this member at m*. It binds **the locus of the
entry that satisfied the member** — and the entry that satisfies `+ill(?x)` is
the one the state kept, which is the denial. So naming a moment at which the
fact did hold changes nothing at all:

```
fact +ill(paul)
rule <heal> = causes( { +ill(?x) }, { -ill(?x), +healthy(?x) } )

rule <recovered> = implies(
    { +healthy(?x) at ?now, anc(?now, ?then), +ill(?x) at ?then },
    { +recovered(?x) } )
```

```
+ill(?x) at ?then                -> recovered(paul) = None
```

`?then` really is a moment at which Paul was ill. The member still matches
nothing, and nothing anywhere says so.

### `holds_at` asks the other question

```
rule <recovered> = implies(
    { +healthy(?x) at ?now, anc(?now, ?then), holds_at(ill(?x), ?then, plus) },
    { +recovered(?x) } )
```

```
holds_at(ill(?x), ?then, plus)   -> recovered(paul) = +
```

`holds_at(p, m, sign)` **resolves p at m** — the question Chapter 5's walk has
always answered and no rule could ask, because the locus it resolved at was
always the frame's own. The seat is the moment itself, so the answer is *as
believed at that moment*: what the world looked like from there, not what the
agent thinks now about back then. Those are different questions and a relation
that meant one while being named for the other would be worse than an absent
one.

Three things it declines, each for a reason you already know. An **unbound**
moment finds nothing, because asking about every moment there is would walk the
whole history (Chapter 5's anchoring discipline). A **generic** proposition
finds nothing, because there is nothing to resolve and answering would be
inventing a subject. And it **mints nothing** — building its answer as a node
would intern it, and the question would afterwards be findable as its own
answer.

And the trail shows what was confusing all along:

```
why recovered(paul)?
  +recovered(paul) @M1, via kb, licensed by applied(<recovered>)
    because +healthy(paul) @M1, via kb, licensed by applied(<heal>)
    because +ill(paul) @M0, via kb, licensed by loaded(ill(paul))
```

> **The superseded claim was never lost. It was never in the *state*** — which
> is a different thing, and `at ?m` reads the state.

## Moments are ordered, not measured

Everything so far is **ordering**. `pred` and `anc` say which came first, and
they say it exactly. What none of them says is *how long ago* — `depth` is a
position in the chain, not a duration — so until a clock exists, the chapter's
own title is only two-thirds honest.

The clock is one structural relation, stamped where a moment is born:

    time(<moment>, <milliseconds since the epoch>)

Structural, like `pred`: nobody asserted it, and nothing can deny it. A rule
reads it by anchoring at the seat.

```
fact +kettle(k1)
fact +heating(k1)
rule <boil>  = causes(  { +heating(?k) }, { -heating(?k), +boiling(?k) } )
rule <began> = implies( { asking(?s), time(?s, ?t), +kettle(?k) },
                        { +seen_at(?k, ?t) } )
```

```
clock=False -> (nothing: the chain was never stamped)
clock=True  -> ['seen_at(k1, 1787077545120)', 'seen_at(k1, 1787077545131)']
```

Two readings, because there are two seats: the stamp is per **moment**, and
`asking` is minted wherever the register stands. A clockless run finds nothing
at all, which is the honest answer rather than a zero.

### Off by default, and the reason is measured

Determinism here is byte-for-byte — Chapter 21's fight replays entry for entry
on the same seed. So the first version of this section said a stamp per moment
makes two runs differ by construction. **That is false**, and the correction is
the more useful half:

| | clock off | clock on |
|---|---|---|
| entries identical across two runs | yes | **yes** |
| stamps identical across two runs | — | **no** |

A stamp is not an entry, so it disturbs nothing that was reproducible before.
What *does* diverge is a corpus that **reads** the clock: its conclusions are
ordinary entries carrying a number that was different last time.

> **The clock is inert until asked for**, and off by default because a source of
> nondeterminism should be requested rather than inherited.

It also does not replace ordering, and should not be asked to. `pred` and `anc`
are exact; a wall clock is monotone if nothing adjusts it. Two moments are
ordered by succession, and *how far apart* is what the stamps are for.

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
is a **deviation** rather than merely patience. Chapter 25 is what matches
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

**Next:** point two agents' channels at each other, and something else appears.
[Several agents →](24-several-agents.md)

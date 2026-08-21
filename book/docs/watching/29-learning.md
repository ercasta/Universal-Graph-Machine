# Learning

Everything up to here takes the rule set as given. A corpus is authored, the
bundle ships, and the agent's cleverness is entirely in what it does with what
it was handed.

This chapter is the other half, and it's Part 2's claim taken seriously:

> **A rule is a node. So a rule can be the conclusion of a rule.**

Nothing new is needed for the agent to author one, and everything already true
of rules is true of what it authors.

## Three ways a rule gets made

### Composition — collapsing a derivation

Having derived `e` from `a` by way of `b`, `c` and `d`, mint the rule `a → e`
and use it directly next time.

Measured, over a chain of length *n*:

| n | uncomposed | composed |
|---|---|---|
| 2 | 2 | **1** |
| 4 | 4 | **1** |
| 8 | 8 | **1** |
| 16 | 16 | **1** |

*n* steps become one, for any *n*, with the same conclusion.

This is easily confused with compilation, and the two behave oppositely:

| | **compilation** | **composition** |
|---|---|---|
| produces | a host-language artifact | **a rule — an ordinary node** |
| reduces | the cost of one step | **the number of steps** |
| the gain | a constant factor | algorithmic |
| inspectable | no | yes |
| interruptible | at rule boundaries | it *is* a rule boundary |
| defeasible | no | yes |
| lives | outside the graph | in the graph |

> **Compilation makes a step cheaper. Composition makes the step unnecessary.**

A composed rule violates nothing: it's data, askable, attributable, defeasible
like any other rule, and it carries a licence naming the rules it collapses — so
the trail is recoverable one hop deeper rather than lost.

**Two things it must inherit, and both do.** Anything that overrides a
constituent overrides the composition — without that, a shortcut escapes a
defeat that bound its parts. And a **guard** is inherited by construction:
composition takes the union of the antecedents, and a guard is an ordinary
negated member, so it comes along without a mechanism.

**And composing across `causes` is refused.** A chain of `implies` collapses
soundly because every step is read in one moment. A `causes` deposits into a
*successor*, so the second rule's other premises are read a moment later than
the first rule's — and flattening them into one antecedent demands them all at
once. Measured, that loses conclusions. So it's refused.

What composition costs is epistemic rather than structural: intermediate
conclusions stop being deposited, so **nothing can be surprised inside a
shortcut**.

### Adoption — a rule concludes a rule

```
adopt(<R>)
```

**A door, not a question.** It belongs with entering a supposition and
dispatching an intent, rather than with the answerers. What decides that a rule
is worth having is a corpus concluding `adopt(?r)`; what happens then is not a
judgement, and there's no verdict for a rule to reach.

Two constraints, both found by building:

**Refused inside a supposition, and that is containment.** A frame's conclusions
are unreadable from outside by construction — but the rule set is one list
shared by every frame. A rule adopted while supposing would apply after the
frame is discharged, and to everything. **Supposing would change what the agent
believes**, which is the one thing supposing must not do.

(And the refusal is written *inside* the frame, so asking the root whether it
holds answers nothing however well it worked. Containment caught the check
before the check caught anything.)

The refusal is worth reading beside Chapter 16's defect, because they are one
situation with two outcomes. A rule set shared by every frame was noticed, and is
guarded. The **stratum-0 index** is shared by every frame in exactly the same way
and is not, so there supposing does change what the agent believes.

**The adopted rule must be the node the graph describes.** Minting a fresh one
makes the live rule a **twin** of the described one: everything a corpus said
about the described rule goes to a node that is not a rule, and everything the
machinery says about the live one names a node no corpus can reach.

This is the **twin trap**, and it has been found seven separate times in this
project's history:

> **Anything that binds a name has to go through the table that resolves it.**

It was found here only when a standing policy tried to order a learned rule and
quietly did nothing.

### Learning from examples — anti-unification

Given two things that happened, what pattern do they already agree about?

That's the **dual of unification**, and it completes a family:

| operation | asks | answers with |
|---|---|---|
| **match** | does this pattern fit that thing? | a substitution |
| **unification** | can these two patterns be made the same? | a substitution over both |
| **anti-unification** | what do these two things already agree about? | **a pattern** |

The thing that makes it learning rather than noise is small and absolute:

> **One mapping across premise and conclusion.**

Generalise the premise and the conclusion with *separate* dictionaries and you
get a rule whose conclusion mentions things its premise never bound — which is
either vacuous or wrong. One dictionary across both is the difference.

Two riders. What the two examples **agree** about is kept — otherwise the result
isn't the *least* general generalisation. And the tool **declines** when they
share no structure at all, rather than returning something vacuous.

## Why the composer has to be a tool

A corpus cannot write a new rule's insides. Three separate refusals say so, each
clean rather than silent:

- a `fact` may not contain a variable at all, so a corpus cannot write a rule's
  patterns;
- a statement's variables are scoped to it, so parts written on separate lines
  could not share a `?x` even if it could;
- a rule's consequent may carry only variables its antecedent binds — and a rule
  being *built* has no antecedent yet.

So the corpus never names the new rule's insides. It reaches them by
**binding** — *reference is binding*, arriving where it is load-bearing.

Composing a rule is a function, and a request answered by a function is a
**tool** (Chapter 22). Learning from examples shares the same seam, for the same
reason.

## The other input: a prediction that failed

Composition needs a derivation and anti-unification needs two examples. Both
start from something that went **right**. The third input is the one an agent
produces by itself, for nothing, every time its model of the world is wrong.

The apparatus is already there. A `causes` rule deposits what it predicts —
`expects(p, +)` — and four bundled rules turn a contradicted prediction into
`deviates(p)` (Chapter 25). `dungeon` runs it **392 times and finds nothing**,
because a game's rules are never wrong, which is why the fixture for this is a
world where the model *is* wrong:

```
fact +heating(k1)     fact +contains(k1, water)
fact +heating(k2)     fact +contains(k2, sand)
rule <boils> = causes( { +heating(?k) }, { +boiling(?k) } )
say world: -boiling(k2)
```

```
why deviates(boiling(k2))?
  +deviates(boiling(k2)), licensed by applied(<deviation-+-contradicted>)
    because +expects(boiling(k2), +), licensed by applied(<boils>)
    because -boiling(k2), licensed by applied(<trust>)
    because +says(world, boiling(k2), -), licensed by applied(<intake>)
    because +arrived(world, boiling(k2), -), via world
```

Everything a learner needs is on that trail, and none of it was instrumented to
put it there:

```
which prediction failed      deviates(p)
which rule made it           the expects entry's licence, applied(<R>)
about what                   the members of p
and what did NOT fail        the same relation, holding, about something else
```

> **A trail kept for explaining is a training set nobody had to collect.**

### A discriminator, not a repair

Abstract every fact about the failing subject by replacing the subject with a
hole, do the same for the subjects the rule got **right**, and subtract:

```
k2 (failed)      heating(_), contains(_, sand)
k1 (succeeded)   heating(_), contains(_, water)
difference       contains(_, sand)
```

The negative half is the half worth checking. `heating(_)` is true of the failure
and of the success, so it discriminates nothing — and it is the premise `<boils>`
already has. **A learner that proposes the rule's own premise is proposing
noise.**

And with nothing to contrast against it declines, which is not politeness:

> **A difference against the empty set is not a difference.**

Given one kettle and no success, *every* fact about the failure reads as an
explanation of it — so the learner would be most confident exactly where it knew
least. Two kettles that both hold sand, only one of which failed, are refused for
the same reason from the other side.

What it emits is one line:

```
fact +likely(prevents(contains(_, sand), <boils>))
```

Ground, because a fact may not contain a variable — so the candidate names the
distinguishing **argument** rather than a pattern. And wrapped, which is the
section below.

### The ontology is what turns a value into a kind

One lesson from one failure is not learning, because it does not survive a
second example. Two kettles fail, one of sand and one of gravel, and the raw
contrast gives two answers with nothing in common:

```
raw     boiling(k2)  ['contains(_, sand)']
raw     boiling(k3)  ['contains(_, gravel)']
raw     COMMON  ->   []
```

An agent learning this way memorises a value, then another value, for ever. With
the corpus's own world model consulted — `is_a(sand, solid)`, `is_a(gravel,
solid)` — every feature is offered abstracted as well as raw, and the two
failures share exactly one thing:

```
lifted  boiling(k2)  ['contains(_, :solid)', 'contains(_, sand)']
lifted  boiling(k3)  ['contains(_, :solid)', 'contains(_, gravel)']
lifted  COMMON  ->   ['contains(_, :solid)']
```

> **The ontology is not decoration. It is the difference between a lesson about a
> thing and a lesson about a kind** — and therefore between memorising and
> generalising.

The claim is testable in one lookup, on a case that was never part of the
evidence. `k5` holds pebbles and was never heated, so it is neither a success nor
a failure and contributed nothing. The lesson **covers it anyway**, and does not
cover `k6`, which holds juice.

And the kill-probe is what says who is doing the work. Delete a single `is_a`
fact — gravel stops being known as a solid — and the common lesson collapses to
nothing with everything else unchanged. **The generalising is done by what the
corpus knows, not by the learner being clever**; a learner that generalised
without the ontology would be inventing the kind.

Two limits, stated rather than discovered. The lift is **one level and one
argument** at a time — a corpus rule making `is_a` transitive widens it with no
change here, which is the right place for that decision. And nothing here
**promotes** anything: whether `contains(_, :solid)` should become a premise of
`<boils>` is an authoring act, and adoption is a door somebody walks through on
purpose.

## What a learned rule may conclude

This turned out to need nothing new.

A learned rule concludes **wrapped**: `likely(p)` rather than `p`.

> **A learned rule that concludes wrapped cannot fight what the agent was told.**

Which means acquisition's normal conflict — a rule the agent invented
contradicting a rule it was given — needs **no new precedence at all**.
`likely(p)` and `−p` are not rivals; they're different claims, and a corpus that
wants to act on the first has to cross it deliberately (Chapter 16).

## The agent harmonizes itself

Once rules can be authored, rules about rules become useful — and the first
fixture that made all of this meet broke in **two** places at once, neither
visible from inside any of the four pieces built separately.

> **Two conventions that have never met are two conventions that have not been
> tested.**

That's not a maxim. It's the measured behaviour of this design's own
construction, and it's why the acceptance gates run against a moving target
rather than a fixture.

What broke:

- **A concluded precedence was never read.** A rule said something and the
  machinery ignored it — the recurring defect, seen from the far side.
- **The adopted rule was a twin of the described one.** The eighth instance.

And one thing worked that shouldn't have been obvious: **a precedence claim
about a rule that did not exist when the claim was written**. That's what
`reference is binding` and *precedence is read, not kept* buy together.

## Retiring is not defeating

One last distinction, and it's the humane one:

> **Losing an argument is not being wrong.**

A rule that is right about a thousand cases and loses to a more specific one in
five is not a bad rule. Retiring it on `defeated` throws away every case it was
right about.

What ships is the **occasion** — `defeated(<loser>, <winner>)` — and what to do
about a rule that keeps losing is a corpus's decision: ask its author, raise a
precedence, mark it dormant.

And before adding any new relation for this sort of thing, there's a check worth
running first:

> **Before adding a relation, check whether the one you want is a count over the
> trail.**

Usually it is.

## Experience: where the table's numbers come from

Chapter 28 left one thing open. The postconditions are *what a learning process
calibrates* — so what is the learning process?

Three answers have been built, and they are genuinely different.

### 1. Being taught — the residue of ordinary use

> A human is the first, manual user of the knowledge base.

Not a labelling task run beside the system. The ordinary first use of a corpus,
by a person who steps it and picks the next rule. **They are doing exactly what
the table will later do**, so what they leave behind *is* the table.

Two signals come out of that use, and only one of them is calibration:

| | |
|---|---|
| **the wrong order** | a lesson — *what mattered here was this* |
| **none of these fits** | a **missing rule**, which no calibration can supply |

The second is the more valuable one early, and **only manual use surfaces it**.
No amount of tuning finds a rule nobody wrote.

And a demonstration cannot produce a flat opinion about a rule. The reflex
experiment settled it: damping every rule that was *tried and missed* cost **125
conclusions**, because

> **tried and missed is not evidence a rule is unimportant — it is evidence it
> did not apply in that state.**

So a lesson has to be **conditional**. And it has to name something that
outlives the episode, which is what settled the *form* a lesson takes: it
attends a **thing**, under a condition, hung off the rule that just ran —

```
learned after <move> { +covered(?d) } => attend(?d, 3)
```

— rather than nudging a rule's score. A lesson written against a rule id goes
stale the moment a rule is adopted, composed or renamed, and a corpus of
experience that has gone stale stops *loading* rather than going quietly wrong.
Chapter 28 has the retirement in full.

### 2. Reviewing — offline, and it is a corpus

An episode ends; the trail is walked; what was learned is written as **surface
text the next episode loads**. Nothing about the loop changes.

Which makes the only question worth asking about it obvious: **run the same
world twice and see whether the second run is better** — with a gate that allows
the answer to be *no*.

The finding that made the file exist:

> **Suppression is not a decision.**

An episode that smashed a jug blames the smasher and drops it from what it
recommends — and then **smashes the jug again**, because omitting a rule leaves
it exactly where it was, first in authored order. *Do not recommend this* cannot
say *do that instead*, and only the second changes a run.

!!! note "Deep dive: an ensemble's agreement is invisible"
    Preferences are scores that sum (Chapter 27), so several learned rows behave
    as an ensemble. But two **identical** rows are one proposition — restating is
    not revising — so `3` and `3` scores **3**, while two **distinct** rows sum,
    so `3` and `4` scores **7** and outweighs a single `5`.

    > **An ensemble's agreement is invisible, and only its disagreement adds.**

    That was filed as a known limitation in one place and as an unexplained
    failure in another, for a while, before anyone noticed they were the same
    fact.

### 3. Practising — goals the agent sets itself

Reviewing has a cost it cannot pay off: *exploration still pays for the
knowledge* — the bad start had to take the costly route once to find out what it
cost. It paid in a broken vase.

The proposal is **one rule and no machinery**:

```
rule <practise> = implies( { +achieves(?a, ?y) }, { +suppose(goal(?y), certain) } )
```

A corpus already says what its acts bring about. Read that fact the other way
round and it names something the agent **knows how to want**. So the goals come
out of the corpus's own vocabulary, and nobody wrote a curriculum.

What makes it safe was already built, which is why this is five rules of fixture
rather than a subsystem: the supposition boundary keys on `doing` (Chapter 14).
Inside a frame entered by supposing, deciding to act deposits `taken(x)` instead
of `emitted(x)`, and the reasoning is carried past the act by its assumed effect.

So a rehearsal runs to the end — routes taken, jugs broken, goals lost — with
**nothing leaving the agent**. And it is kill-probed: propose the goal bare
instead of supposing it, and the vase really shatters.

## Where this stands, honestly

The instruments are green on their own terms. The comparison is not, and it
would be dishonest to leave that out of a chapter about learning.

Teaching a table from one demonstration, gated against the **uncalibrated** table
on the same corpus:

| corpus | teacher took the table's top choice | what calibration cost |
|---|---|---|
| `quest-p1.ugm` | **21 of 21** | 9 conclusions lost by three of four lesson kinds |
| `dungeon` | **16 of 149** | occasion-keyed lessons lose **173**; both kinds together, **213** |

Read those two rows together, because separately each is misleading.

On `quest-p1` the teacher agreed with the table's own ordering **every single
time** — so there was nothing to teach, and everything a lesson changed was a
change for the worse. *A corpus with nothing to teach cannot measure a teacher*,
which is the same shape as Chapter 18's census finding.

On `dungeon` there was plenty to teach — the teacher and the table disagreed on
133 of 149 moves — and the lessons cost conclusions anyway.

So the honest statement is: **calibration currently buys fewer moves and costs
answers**, and the mechanism for spending attention is built while the process
that should be calibrating it is not yet working. Chapter 34 lists it where it
belongs.

!!! note "Deep dive: a gate that crashes reports the same thing as a gate that passes"
    That comparison had not been run for some time. The gate read two keys the
    measurement had stopped producing, so it raised on the first corpus of two —
    **every run**, loudly enough that nobody read the rest.

    Which means `dungeon`, the only corpus of the pair with anything to teach,
    was never measured at all.

    Chapter 32 has this project's list of instruments that lied. This is a new
    entry in it, and a new variety: not a check that could not fail, but a check
    that could not *finish*.

---

That's Part 6. Parts 7 and 8 are the last two, and they go underneath.

**Next:** the five things that genuinely could not be taught.
[What cannot be a convention →](../floor/30-the-floor.md)

# Rules — a design

This document specifies how an agent represents rules, states, claims and uncertainty on a single
graph substrate, and what the engine that runs them must provide. It is self-contained: every term it
uses is defined here, and every decision is argued from the requirements stated in §1 rather than
from precedent.

## Contents

- [1. Requirements](#1-requirements)
- [2. Evaluation criteria](#2-evaluation-criteria)
- [3. The substrate](#3-the-substrate)
- [4. Moments](#4-moments)
- [5. Propositions and entries](#5-propositions-and-entries)
- [6. Signs](#6-signs)
- [7. Spans](#7-spans)
- [8. Rules](#8-rules)
- [9. Connectives](#9-connectives)
- [10. Time](#10-time)
- [11. Modality](#11-modality)
- [12. The division of labour](#12-the-division-of-labour)
- [13. The engine floor](#13-the-engine-floor)
- [14. Recall](#14-recall)
- [15. Surprise, commitment and reflection](#15-surprise-commitment-and-reflection)
- [16. Acceptance](#16-acceptance)
- [17. What this design does not settle](#17-what-this-design-does-not-settle)
- [Appendix A. Glossary](#appendix-a-glossary)
- [Appendix B. Alternatives considered](#appendix-b-alternatives-considered)

Concepts are introduced in dependency order: no section relies on a construct defined below it,
except that §4 forward-references *entries*, whose definition is §5.

---

## 1. Requirements

The system is an agent that plans, acts, observes and explains itself. Rules are how it knows what
follows from what. Seven requirements shape everything below.

**R1 — Two readings of one statement.** Planning reads a rule **backwards** (*what would make this
goal true?*); execution reads it **forwards** (*what follows from this state?*). Both readings must
come from the same statement. Two statements, one per direction, would drift apart with no way to
detect the disagreement, because neither is the premise of the other.

**R2 — The reading must be recoverable.** Reading a rule backwards is reading its converse. *Four
wheels ⇒ car*, run backwards, licenses *a cart is a car*. That is legitimate as a hypothesis and
catastrophic if a planner treats it as entailment, so the representation must record which kind of
step a given inference was.

**R3 — Rules are subjects.** *A rule the boss gave beats one the vice gave* requires a rule to be a
thing other facts can be about. So must *this rule is about assembly*, *this rule takes four to seven
minutes*, *this rule does not apply at altitude*.

**R4 — Rules are askable, not merely runnable.** *Which rules are about time? Which disturb position?
Which come from the boss?* must be ordinary queries. A rule whose content is a program is data you
can run but cannot ask about, so those questions become impossible.

**R5 — Every conclusion carries its support.** The agent must be able to answer *why do you believe
that, and on whose word?* The trace a piece of reasoning leaves behind is not a debugging aid; §11
makes it load-bearing for correctness.

**R6 — Partial knowledge must be sayable.** *Pouring raises the level, by an unknown amount* must be
expressible as such. A representation in which the only options are *states a value* and *says
nothing* forces the agent to claim precision it does not have, or silence that means the wrong thing.

**R7 — The agent's own state is in the world it reasons about.** Expectations, commitments and
in-progress procedures must be facts on the graph, not variables in an interpreter. Otherwise the
agent cannot notice that an expectation failed, cannot be asked why it abandoned a plan, and cannot
have a strategy overridden by a statement in its knowledge base.

---

## 2. Evaluation criteria

Every representation decision below is scored against four criteria, in a table, before the decision
is taken. The cost is written down even when the choice is obvious.

| criterion | the question |
|---|---|
| **not leaking** | Can this shape state something the author did not intend? Does a consumer that ignores part of it silently get a stronger claim than was made? |
| **not lossy** | Is everything the author knew recoverable from what was stored — including what they *didn't* know? |
| **readable** | Can the obvious questions about this be asked as ordinary queries, without a special mechanism? |
| **composable** | Do two independently authored instances of this combine without either being rewritten? |

The most common leak has an innocent shape: a two-hop path through a shared node, which no one
authored and which nothing forbids reading as a claim.

---

## 3. The substrate

The design assumes only this much:

* There are **nodes** and **directed edges**. Edges carry no information beyond connecting.
* A node may have **ordered members**: an edge to a target at a known position.
* Nothing else. In particular, edges have no labels, no attributes and no truth values; anything you
  want to say about a connection must be a node.

A **relation instance** — what would elsewhere be a labelled edge — is therefore a node with a
relation and ordered members:

```
on(a, b)        a node whose members are, in order, a and b
```

This is why the rest of the design can attach facts to anything: rules, claims, moments and time
spans are all nodes, so all of them can be spoken about without introducing a new kind of thing.

**Ordering is the one thing that is not itself structure.** *The second member* is not a relation
between two things in the world; it is a fact about how a node is built. That is why the substrate
provides ordered targets natively, and why it is the only such provision.

---

## 4. Moments

A **moment** is the design's only construct for a state of affairs. A state in time, a hypothetical, a
supposition and a rule's antecedent are all moments; there is no separate "frame", "world" or
"context" object.

A moment has three parts and nothing else:

```
<M> = a signed delta      +  a predecessor          +  a licence
      (entries, §5)          (an edge to a moment)     (an edge to a node)
```

The delta is what changed. The predecessor says what it changed *from*. The licence says what
authorised the difference. Only the licence varies by reading:

| the moment is | its predecessor is | its licence says |
|---|---|---|
| a state in **time** | the previous state | *an event happened* |
| an **imagined state** | the imagined state before it | *I applied this rule in supposition* |
| an **assumption** | where I was standing when I made it | *I decided to suppose this* |
| a rule's antecedent or consequent | **none** | — |

### Anchored and generic

The distinction that carries weight is not between kinds of moment but between:

* an **anchored** moment — individuals, and a predecessor;
* a **generic** moment — variables, and no predecessor.

A rule's two members are generic. Everything else is anchored. Because this distinction is
structural, it is checkable rather than maintained by convention, and it gives the engine's central
operation a one-line definition:

> **To match is to unify a generic moment against an anchored one.**

**Nesting needs no mechanism.** A supposition inside a supposition is a path in the predecessor tree.
There is no depth limit, no stack and no scope object.

### Reading through the chain

Because a moment stores only what changed, a moment does not contain its state; **the state is what
the chain answers.** To find out whether `on(a, b)` holds at `M12`, walk back from `M12` through
predecessors until an entry naming that proposition is found. Reading is a walk, not a lookup. This
is the single most consequential cost in the design, and it is accepted deliberately: it is what makes
supposition free, history immutable, and every claim dated.

### Time and derivation share a core

Two orderings could easily become unrelated: succession in time, and succession in a derivation.
Under one construct they are **one relation with two licences**. Succession is the shared core; time
adds a clock stamp above it, derivation adds a licensing rule above it.

The invariant that must survive this sharing: **supposing takes no time.** A derivation step is
succession without duration. If the shared core carried a clock, the two would have been collapsed
rather than related, and every hypothetical would falsely advance the world.

---

## 5. Propositions and entries

A relation instance is a **proposition**. It claims nothing. `on(a, b)` is the *idea* that a is on b,
not the assertion that it is.

The claim is a separate node, the **entry**:

```
<e> = entry(<M7>, <f>, +)          three members: locus, proposition, sign
```

An entry has exactly three members:

* **locus** — the moment (§4) or span (§7) the claim is about;
* **proposition** — what is claimed;
* **sign** — how it is claimed (§6).

Everything else is an ordinary fact *about* the entry:

```
licensed_by(<e>, <application>)    grade(<e>, likely)    said_by(<e>, anna)    at(<e>, 09:14)
```

### Why two levels are forced

To say *`on(a, b)` is false at M12*, you must be able to point at `on(a, b)` — so the proposition
must exist in order to be denied. If the proposition node were itself the assertion, then minting a
node in order to negate it would assert it. Two levels are what negation costs. In exchange, nothing
in the system has to remember that a bare proposition means nothing: it structurally cannot be
mistaken for a claim, because it has no locus and no sign.

### Where the regress stops

An entry is itself a fact. Does it need an entry of its own? No: **an entry names its locus, so it is
located by being one.** A proposition needs an entry to be placed in a moment; an entry places itself.
The recursion terminates at depth one, structurally.

### Exactly three members

Grade, licence, speaker and clock stamp are facts about the entry, never a fourth member. The
discipline matters: with optional slots, an entry becomes a node of variable arity whose members mean
different things depending on how many there are, which is the same shape carrying several membership
semantics — unreadable and uncomposable. The same discipline keeps the connective in §8 binary, with
timing as an adjunct fact.

### What the two levels buy

The world changing and the agent having been wrong become **different operations**:

| | what happened | how it is written |
|---|---|---|
| they stopped being on each other | the world moved | a **new entry**: opposite sign, later locus |
| I was mistaken that they ever were | my record was wrong | a **fact about the old entry**; the entry is unchanged |

If truth were a value stored on the proposition node, these would be indistinguishable — both are
*change it* — and a system that cannot distinguish them quietly rewrites its own history.

| | (A) truth as a value on the proposition | (B) proposition + entry |
|---|---|---|
| not leaking | ❌ minting a node to deny it asserts it | ✅ a proposition with no entry claims nothing |
| not lossy | ❌ correction overwrites the record it corrects | ✅ correction is a new fact; the original survives |
| readable | ⚠ one hop | ⚠ two hops, but *who claimed this, when, on what grounds* are ordinary queries |
| composable | ❌ two sources disagreeing means one overwrites the other | ✅ two entries, two attributions, arbitration by rule |

### The cost, stated

**Resolving a read is a privileged operation.** *Does `on(a, b)` hold here?* means *walk the chain for
entries naming this proposition and take the most recent*. The engine must know what `entry` means;
it cannot be ordinary vocabulary. This is one of the very few relations the engine dispatches on, and
that set should be declared in one place rather than accumulating.

**Contradiction is permitted and undetected.** Two entries in one locus with opposite signs is a
shape the substrate allows. This is correct: consistency is a **question you ask**, not an invariant
the substrate maintains — the alternative is checking every write against every other claim. But it
means *is this moment consistent?* is a query somebody must run, and the design does not say who.

---

## 6. Signs

An entry's sign says how the proposition is claimed at its locus. There are three signs plus the
absence of an entry, and their meaning differs between anchored and generic moments — because a
generic moment has no predecessor to inherit from.

| sign | in an **anchored** moment | in a **generic** moment |
|---|---|---|
| `+` | holds here | must hold |
| `−` | does not hold here | must not hold |
| `?` | **held before; does not now; I cannot say what does** | — |
| *no entry* | **unchanged — inherit from the predecessor** | don't care / not constrained |

### No entry means inherit, not unknown

This follows from §4: the chain walk continues past a moment with no entry and finds an older one. In
an anchored moment, silence is therefore a positive claim — *this is as it was*.

That is why `?` must exist as a distinct sign. Requirement R6's example — *pouring raises the level by
an unknown amount* — cannot be written by writing nothing, because writing nothing means the chain
returns the **old** level. Without `?`, the one thing the author was trying to say is the one thing
that could not be said. `?` **invalidates without replacing**: it stops the walk and reports ignorance.

The generic `?` (*I don't constrain this*) and the anchored `?` (*this was invalidated and I cannot
say what replaced it*) are different claims. They share a symbol because the anchored/generic split
already distinguishes them structurally, but they are not the same thing and a reader is owed the
distinction.

---

## 7. Spans

Some claims are not about a moment at all. *They are taking turns* is not true of any instant; its
subject is a **stretch of the chain**. So is *it rained throughout*, and so is any constraint on the
order in which things happen.

A **span** is a node with exactly two members: a start moment and an end moment.

```
<s> = span(<M7>, <M12>)                        position 0 = start, position 1 = end
<e> = entry(<s>, taking_turns(anna, bo), +)    the locus of this entry is the span
```

Spans are loci. Nothing else about the entry changes.

### Membership is not stored

The moments a span contains are **not** listed, and the reason is structural: **the predecessor
relation is single-valued.** A moment has one parent; forking produces several successors, never
several parents. So the walk back from `M12` is unique, and if `M7` lies on it the span's contents are
fully determined by the chain.

| | (A) endpoints only | (B) enumerate the moments | (C) a description of the stretch |
|---|---|---|---|
| not leaking | ✅ contents derived from the chain, so they cannot disagree with it | ❌ two answers to *what is in this span* | ✅ |
| not lossy | ✅ | ⚠ records the extent, not why those | ✅ |
| readable | ✅ fixed 2-ary | ❌ an extent claim wearing positional clothes; arity varies with duration | ⚠ |
| composable | ✅ interval relations compare two pairs of endpoints | ⚠ comparing spans means comparing lists | ❌ comparing descriptions is not expressible |

### Two things stay out of the span

**Participants.** `anna` and `bo` are members of the proposition, never of the span. This is what lets
one span host several unrelated recognitions — *they took turns* and *it rained throughout* — over the
same stretch.

**Disjunction.** *On Monday and on Wednesday* is two spans plus a fact relating them, never one span
with a hole in it. A span with holes would smuggle disjunction into the substrate, where nothing can
consume it.

### Recognition and prescription are one predicate read twice

A **generic** span, with variables for its endpoints, is a constraint to be satisfied — *do these in
this order*. An **anchored** span is a recognition that a pattern held. Same predicate, same shape;
the anchored/generic split of §4, one level up.

### Costs

* Spans are **directional**, so equality of content must be normalised by chain order, not by member
  order — otherwise two spans over the same stretch can fail to be equal.
* Any two moments form a span, so the population is quadratic. Spans are therefore **minted by
  recognisers, never enumerated**.
* Nothing prevents constructing a span whose start is not an ancestor of its end. Such a span is
  meaningless, so the ancestry check belongs at the **minting site**, where it is cheap and where the
  mistake is still attributable.

---

## 8. Rules

A rule is a **fact relating two moments**.

```
<R> = causes( <A>, <B> )
```

`<A>` and `<B>` are generic moments (§4): variables, no predecessor. `<A>` is the antecedent. `<B>` is
the consequent, and because a moment is a signed delta, `<B>` is a delta **relative to** `<A>` without
being a second kind of object.

Because `<R>` is a node, everything else about it is an ordinary fact — which is requirement R3:

```
by(R, boss)                 overrides(R, R2)              about(R, assembly)
timing(R, end→start, [4min, 7min])                        unless(R, +altitude(?w, high))
```

And because the rule's content is data rather than a program, R4's questions are ordinary queries:
*which rules are about time* is a query over `about`; *which rules disturb position* is a query over
the consequent's members.

### The three readings

| reading | what it does |
|---|---|
| **forward** | match `<A>` against the current moment; apply `<B>`'s signs into a successor moment |
| **backward** | unify a wanted fact against `<B>`'s `+`/`−` entries; `<A>`'s achievable members become subgoals |
| **`?` entries, backward** | *this rule disturbs that and cannot say how* — a **want**, not a failure, and not a false *it stays as it was* |

Direction is a **query over the rule**, never a field in it. This is R1: one statement, two readings.
R2 is met because each reading cites `<R>`, and the licence recorded on the resulting entry says which
reading produced it — so a hypothesis formed by reading backwards is distinguishable, permanently,
from a conclusion drawn forwards.

### Antecedent members are not alike

A flat antecedent is unusable backwards. *To unbolt it, it must be on the bench — and you may put it
there; it must be a Tuesday, and you may not make it one.* Each antecedent member therefore carries
one mark:

* `+` **achievable** — read backwards, this becomes a subgoal;
* `~` **given** — read backwards, this may only be *tested*.

Without the distinction, a backward reader plans to make it Tuesday. A forward reader is unaffected
either way, which is exactly why the mark must be authored rather than inferred: the reading that
needs it is not the reading that would notice its absence.

### Worked

```
<R1> = causes(
    { +heat(?a, ?w),  +water(?w),  ~open(?vessel) },
    { +boiling(?w) @certain,  −liquid(?w) @certain,  ?volume(?w) } )

timing(R1, end→start, [4min, 7min])
unless(R1, +altitude(?w, high))
```

```
<R2> = implies(
    { +cloudy(?day, morning) },
    { +rain(?day, afternoon) @likely } )
```

### Scoring the form

| | (A) guard → program body | (B) one rule per direction | (C) `connective(moment, moment)` |
|---|---|---|---|
| not leaking | ❌ the backward read is hypothesis wearing entailment's clothes, with nowhere to record it | ❌ two statements drift; neither is the other's premise | ✅ one statement; each reading cites `R`, whose licence says what the citation is worth |
| not lossy | ❌ what it makes true is recoverable only by running it | ⚠ the pair coheres only by convention | ✅ `<B>` **is** the postcondition; `?` preserves a gap instead of erasing it |
| readable | ❌ runnable, not askable — fails R4 | ⚠ readable, doubled | ✅ every question about a rule is a query over its members and adjuncts |
| composable | ❌ two bodies cannot be joined | ❌ n directions means 2ⁿ statements | ✅ join on signed membership; no-entry survives composition as no-entry, so two partial rule sets merge without lying |

(A) fails an additional test outright: `overrides(R1, R2)` has no subject when a rule is a program.
Nothing can be said *about* it, so R3 is unreachable.

---

## 9. Connectives

The reserved vocabulary of the whole design:

| layer | closed set | size |
|---|---|---|
| connective | `implies`, `causes` | **2** |
| entry sign | `+`, `−`, `?`, no entry | 4 |
| antecedent mark | achievable, given | 2 |
| grade | `certain > likely > possible > unlikely > unknown` | ordinal, ~5 |
| timing | one relation over the two moments' endpoints | 1 |
| locus resolution | `entry` — the relation the engine dispatches on (§5) | 1 |

Everything else — `heat`, `cloudy`, `boss`, `overrides`, `by`, `about`, `unless` — is open-class
vocabulary and reserves nothing. Authors may coin freely.

### The membership test

> **A connective earns its place only if it licenses a different (forward, backward) reading pair.**

If two candidates read the same way in both directions, they are one connective, and the difference
between them belongs in a member. Applying the test eliminates the obvious candidates:

* `prevents(A, B)` is `causes(A, {−B})`. Consequents are signed, so prevention is already sayable.
* `enables(A, B)` is `causes(A, {+B @possible})`. Read backwards, the two are told apart by the
  grade: `certain` means doing `A` achieves `B`; `possible` means `A` is a precondition and something
  else must still happen.

### Why the remaining two do not collapse

The distinction is not *logical versus worldly*. It is mechanical:

> **Retract the antecedent. Does the consequent go with it?**
> **Yes → `implies`.** The entry is *derived*. It lands in the **same** moment.
> **No → `causes`.** The entry is *asserted*. It persists, and lands in a **later** moment.

Water you have stopped heating stays boiled. That is inertia, and it is why a zero-delay cause is
still not an implication: the two cannot be merged by setting the delay to zero.

`<R2>` above is the argument for keeping both. *Cloudy morning likely implies rainy afternoon* passes
the persistence test as `implies` — learn it was not cloudy and the rain claim goes with it — but the
surface wording reads just as easily as causal, and clouds do not cause the afternoon's rain; a front
causes both. Written as `causes`, the backward reader produces **a plan to make it rain by making it
cloudy**. The two-connective split is precisely what makes that plan unwritable.

### What is not a connective

Interval relations — *before*, *during*, *overlaps* — are ordinary facts about moments and spans,
which are already nodes. Adding them to the closed set would buy nothing and would start the
multiplicative growth §10 and §11 are designed to avoid.

---

## 10. Time

**An action is not a new kind of thing.** An action is an event; an event is a moment; and
`heat(?a, ?w)` is a fact that holds over an interval. An action therefore enters a rule's antecedent
as an ordinary member, and *to execute* means **make this event-fact true**. There is no action
construct, no operator schema and no plan-step type alongside the rules.

Expressing *…and it boils five minutes later* takes three decisions.

**1. Say which endpoints.** *The heating takes five minutes*, *boiling starts five minutes after
heating starts* and *boiling starts five minutes after heating stops* are three different rules that
plan differently. The timing member therefore relates **named endpoints** — `end(A) → start(B)` —
never a bare scalar.

**2. It is a constraint, not a number.** `[4min, 7min]`, `≥5min`, *eventually* and *unknown* must all
be sayable, or R6's problem returns one level up as precision-by-silence. Absent timing means unknown
timing, and that is both legal and readable.

**3. It is a fact about the rule, not a third member of the connective.** This keeps the connective
binary; lets the delay be genuinely absent rather than defaulted; and lets two timing claims coexist
with different sources — *the manual says five, I measured seven* — which is real and unsayable if
the delay is a slot.

| | timing as a connective member | timing as a fact about the rule |
|---|---|---|
| not leaking | ❌ an absent delay defaults to something nobody stated | ✅ absent means absent |
| not lossy | ❌ one delay per rule, no provenance | ✅ several claims, each attributed |
| readable | ⚠ | ✅ *which rules are slower than five minutes* is a query |
| composable | ❌ the connective's arity varies | ✅ timing joins independently of the connective |

Timing is read in both directions, which is the payoff. **Forward**, it says when to expect the
effect, and therefore when its absence is a **deviation** rather than merely patience — this is what
§15 matches against. **Backward**, it is a **filter**: needing boiling water within two minutes rules
this rule out of the plan. A rule with no timing expresses neither.

---

## 11. Modality

Three different things get called *possibility*, and they must not share a slot.

| | what it is | where it goes |
|---|---|---|
| **strength** | how often the effect actually follows | a grade on the **entry** |
| **confidence** | how sure the agent is of the rule itself | a grade on the **rule**; moves with evidence |
| **defeasibility** | what would cancel it | **not a number** — a relation to other rules: `unless`, `overrides` |

Collapsed into one number, `0.6` means three things at once, and combining two such numbers is
arithmetic nonsense. Defeasibility is the load-bearing one for reasoning — *unless the front has
already passed* — and it needs **no numeric apparatus at all**: it is the same precedence machinery
that makes the boss's rule beat the vice's.

**Grades are per-entry, not per-rule.** One rule has consequences of different strength: heating boils
the water (certain) and scorches the pan (unlikely). A rule-level grade cannot express that; it is at
best shorthand for *all entries the same*.

**Grades are ordinal, not probabilistic.** Real probabilities require independence assumptions that
cannot be stated in the graph, so multiplying them leaks silently — the product looks like a
measurement and is an artefact. Ordinal grades compose by **weakest link**. A numeric member may sit
*beside* the grade where its own provenance is a member — *from 300 observations* — but never in
place of it.

The honest cost: two independent *likely*s ought to amount to more than *likely*, and taking the
minimum says they do not. Ordinal grades do not accumulate evidence. The right place to fix that is
**counting over episodes**, not arithmetic over grades; §17 records it as unsettled.

Grade is orthogonal to the `?` sign. `?volume` is *this changed and I cannot say to what*;
`+rain @possible` is *this might become true*. Different ignorance, different slot.

### Where the grade lives

Not on the proposition node — and not for reasons of cost.

> A grade stored on a proposition node is **a cache of a derived value**. *Rain is likely* holds only
> given the support that produced it, so when the support changes the tag must be invalidated. General
> invalidation over a web of dependencies is a truth-maintenance system: a second machinery, with its
> own consistency problem, running underneath the first. **An index over what was asserted is
> storage; a cache of what was derived is a truth-maintenance system.**

A second, independent reason: **a tag is ignorable.** Reading a fact and reading its grade are two
reads, so a consumer that performs the first and forgets the second produces a conclusion with no
grade at all — and unmarked conclusions read as certain. That is the leak criterion failing by
discipline, where the whole point of putting relations in nodes was to get structure instead.

**Every fact already has a node that records where it came from — the entry of §5. The grade goes
there.**

| the fact came from | the node that already exists | it carries |
|---|---|---|
| a rule applying | the application | the rule's per-entry grade |
| someone saying so | the utterance | how firmly they said it, and their authority |
| observing | the sighting | sensor confidence |
| a supposition | the moment's licence | the grade of what was supposed |

The entry had to exist anyway, because the **sign** has nowhere else to live — edges carry no facts.
So the grade slot costs nothing structurally. A shape that absorbs a new requirement without growing
is a shape that was right rather than convenient.

### Superseded, not invalidated

If a stored grade is a cache, is a stored derived *fact* not also a cache? No — and the difference is
the reason the whole design is dated.

> **A dated derived fact needs no invalidation.** At `M7` the agent recognised that they were taking
> turns. At `M12` something writes the opposite. The `M7` entry stays true **of `M7`**. Nothing is
> retracted, nothing propagates, and *are they taking turns?* resolves through the chain to the most
> recent entry.

One line covers modality and recognition together:

> **Store it on the entry — dated, signed, attributed, superseded.
> Never on the node — timeless, and therefore requiring invalidation.**

### Supposition and weak connection are different problems

The word *likely* covers two things, which is why *tag it or guard it* feels like a forced choice:

| | *I am supposing this — what follows?* | *this generally holds, weakly* |
|---|---|---|
| shape | a **moment** you enter and leave (§4) | a **grade**, recorded on the entry when the rule applies |
| how many | few, deliberate | many, independent |
| nesting | free — a path in the predecessor tree | does not nest; composes by weakest link |
| isolation | already enforced — a read cannot reach into a moment except through the chain | not an isolation problem at all |

Keeping these apart is what prevents combinatorial explosion: twenty independently uncertain facts
would be a million moments if uncertainty were modelled as supposition. **Use moments where the agent
*chooses* to suppose; use grades where the world is merely weakly connected.**

### Scoring

| | (A) grade on the proposition node | (B) a guard node per uncertain fact | (C) moments + graded entries, weakest link computed |
|---|---|---|---|
| not leaking | ❌ ignorable by default; a consumer that skips it invents certainty | ✅ crossing the guard is forced… | ✅ a conclusion drawn in a moment **is** in it; the grade is recomputed from support |
| not lossy | ❌ a number with no premise | ⚠ says *that* it is uncertain, not on whose word | ✅ speaker, rule and sighting all survive |
| readable | ⚠ readable and stale | ⚠ | ✅ *which conclusions rest on something merely possible* is a walk |
| composable | ❌ two tagged facts combine to *what?* | ❌ every consumer must handle both shapes, guarded and bare | ✅ weakest link over the support chain |

(B)'s failure has no middle setting, which is why it is worth naming: **optional guards mean consumers
handle two shapes and forgetting returns; mandatory guards mean an extra node and an extra hop for
every certain fact in the system.**

But the guard instinct is right about one thing — **forcing the handling**. A computed grade compels
nothing, and *do not act on a merely-possible fact without acknowledging it* is a real requirement. It
belongs at **the one place effects leave the agent**: check the grade of what licenses an **action**
at the dispatch point, where the set is small and known, rather than making a million reads cross a
guard in order to catch the one that matters.

### What (C) costs

* *How likely is this?* becomes a **walk, not a read** — the same shape and the same cost as reading
  a fact at all (§4). Accepted as a consequence of dating everything, not paid separately.
* **The support trail becomes load-bearing for correctness, not only for explanation.** A write that
  loses its attribution does not merely become unexplainable — it becomes **falsely confident**,
  because a missing support link removes a weak link from the minimum. This is what promotes R5 from
  a nicety to a soundness condition, and it is why §12's write monopoly exists.
* Cycles in the support chain need the same termination care as any walk over derived structure.

### Does the design run out of dimensions?

The worry behind every new distinction is that it needs a new dimension of the representation. It does
not. Everything spent so far:

| | why it could not be a node |
|---|---|
| **identity** | *this node is that node* is not a relation between two things; it is the precondition for there being two things |
| **connection** | an edge |
| **order among connections** | *the second member* — position is not a thing in the world |

Everything added since — type, sign, licence, grade, time, authority, span, commitment — is a
**member of a node**, and cost no dimension.

> **You run out of dimensions only if you try to say something that is not about anything.**

If a candidate distinction can be phrased as *X stands in relation R to Y*, it is structure, and
structure is nodes. Order is the one thing that genuinely cannot be, which is why the substrate
provides it and nothing else.

---

## 12. The division of labour

Every claim is made through an entry (§5). So: are rules **augmented** to speak about entries, or does
the **machinery** apply rules to entries? The machinery — and the alternative is not merely costly, it
cannot be written.

### Augmentation is a category error

```
+on(a, b)      ⟶      entry( <the moment I am in> , on(a, b), + )
                             ^^^^^^^^^^^^^^^^^^^^
```

**The locus is an indexical.** A rule is generic: variables, no predecessor. An entry is anchored. A
rule that named a locus would be about that one occasion and could not be reused. So augmentation
cannot produce a whole entry — only one with a hole in it. And **a hole that the machinery fills at
run time is the machinery doing the work anyway.**

It buys nothing, and costs four things:

1. **It is a translation, and translations must commute.** Every explanation would show the rewritten
   rule rather than the rule the author wrote. Since the trail *is* the explanation (R5), this is the
   expensive loss.
2. **One fact in two shapes.** Authored and augmented forms must be kept in sync, and answering *why*
   means un-augmenting.
3. **It freezes the resolution policy into every rule.** The property being bought here is that *the
   machinery can change what a read means without editing a single rule*. Augment, and a policy change
   means rewriting the corpus.
4. Every rule triples in size in plumbing, which makes R4's questions harder to answer, not easier.

### The split

| the rule says | the machinery supplies |
|---|---|
| `+on(?x, ?y)` in the antecedent | walk the chain for entries naming that proposition; return those signed `+` |
| `+boiling(?w)` in the consequent | mint the entry in the successor moment; stamp locus, licence and grade from this application |

> **The rule's members are what the author knows. The entry's members are what the application knows.**

Locus, licence, speaker and grade-at-this-application do not exist until the rule runs. That is the
whole split, and it is why `entry` is engine vocabulary rather than something an author writes.

| | (A) augment the rules | (B) authors write entries natively | (C) the machinery absorbs it |
|---|---|---|---|
| not leaking | ❌ explanations show the rewrite, not the rule | ⚠ an author can name a locus, so provenance is forgeable | ✅ every entry is stamped by the write that made it |
| not lossy | ❌ two shapes; *why* must un-augment | ✅ | ✅ |
| readable | ❌ three times the plumbing per rule | ❌ every rule is plumbing | ✅ the rule reads as written |
| composable | ❌ resolution policy frozen at augmentation time | ⚠ | ✅ resolution can change without touching a rule |

(A) additionally cannot be written at all, per the indexical above.

### The asymmetry that must be enforced

An entry is both a mechanism and a node a rule can point at. That is safe in **one direction only**:

> **Rules may READ entries. Only the machinery may WRITE them.**

Reading is how *a claim Anna made outranks one Bo made* gets stated at all — an ordinary rule about
entries. Writing is how a rule would forge provenance: an entry licensed by nothing, or one backdated
into an earlier locus.

This matters more than it looks, because §11 makes the support trail load-bearing for soundness. If a
rule could mint entries directly, attribution would stop being merely fragile and become
**forgeable**, and the agent's confidence could be raised by writing one unlicensed entry. So the
write primitive is the only minter of entries, and it **stamps** the licence from the current
application rather than accepting one as an argument.

### Costs

* **A bug in the write primitive is systemic** — every fact in the system gets the same wrong
  provenance. Mitigated by it being one place, which makes it one check.
* **Matching becomes a chain walk rather than a lookup**, and that walk now sits on the rule-matching
  path, not only on reads.
* **Matching must record which entries it matched.** Otherwise *because a was on b, on Anna's word*
  has no answer. This is not overhead: it is half the trail, and it is what makes a misbehaving rule
  distinguishable from a misresolving chain.

---

## 13. The engine floor

If the meaning of `causes` is given by rules, and those rules use connectives whose meaning is given
by rules, the tower never reaches ground. **The reserved set cannot be empty.** What it can be is *not
the connectives*.

Four primitives:

1. **recall** — which rules come to mind here. **Never complete**, by design (§14).
2. **match** — unify a **generic** moment against an **anchored** one, over what recall offered. It
   records which entries it matched (§12).
3. **write** — mint signed entries into a moment. **The only minter of entries**; it stamps the
   licence from the current application.
4. **arbitrate** — among the rules that matched, choose one. **Total**: table-driven, always answers.

> **Recall proposes. Match filters. Arbitrate commits. Only the last is total.**

Arbitration is the one that is easy to get wrong. A meta-rule that decides which rule to apply must
itself be selected, and that regress happens *at run time*, not at design time. Therefore:

> **The bottom-most arbitrator is a lookup over an authored precedence table that always returns and
> never searches.**

Reflection may be arbitrarily deep; the final tiebreak may not be reflective. That is the
stratification condition, and it is what keeps the tower finite in practice rather than merely in
principle.

### A connective is a table entry, not a branch

Given the four primitives, the connectives themselves are data:

```
<F> = causes( { +rule(?r), +conn(?r, causes), +matches(?s, ant(?r)) },
              { +succ(?s, ?s'), +applied(?r, ?s, ?s') } )

<B> = causes( { +want(?f), +conn(?r, causes), +member(+?f, con(?r)) },
              { +candidate(?r, ?f) } )
```

Matching is primitive; everything above it is rules.

> **The test that the floor is in the right place: adding a connective adds rows, not branches.**

If a new connective requires editing the engine, then the connective set is not data and §9's budget
is fiction.

### One interpreter

Meta-rules buy nothing if the interpreter special-cases them. The interpreter's step is *select a
rule, apply it*, and object-rules and meta-rules must be indistinguishable to it — a flat tower, not a
stacked one. If, standing inside the interpreter, you cannot answer *which level am I on?*, that is
the sign it is built correctly.

---

## 14. Recall

Recall is not an optimisation of an exhaustive search. It is a distinct primitive with distinct
properties, and it is where the agent's experience lives: the right rules coming to mind at the right
moment is what expertise consists of.

The three selection steps have **opposite requirements**, which is why they are three:

| | **recall** | **match** | **arbitrate** |
|---|---|---|---|
| job | which rules come to mind | do they actually fit | which one, now |
| complete? | **never**, by design | over what recall offered | over what matched |
| total? | — | — | **must always answer** |
| authored or learned? | **learned** | mechanical | **authored** — precedence |
| failure mode | a rule you needed never surfaced | — | dithering, or a hang |
| cost of being wrong | recoverable: a worse plan, or a surprise later | — | a wrong action |

### Why experience belongs in recall specifically

Two structural reasons, neither of which is an appeal to cognitive plausibility:

1. **It is the only step where being wrong is recoverable.** A missed rule costs a worse plan or a
   later surprise — both of which the machinery already handles. A wrong arbitration costs a wrong
   *action*. Put learning where errors are survivable.
2. **It is the only step with no authored ground truth.** *Which rules should have come to mind?* has
   no answer other than *the ones that turned out to matter*, so it can only be learned. Arbitration
   has the opposite property: `by(R, boss)` and `overrides(R1, R2)` **are** the ground truth, and
   learning them instead of reading them would be wrong.

### What incompleteness costs immediately

Once recall may miss, **"no rule applies" is ambiguous**: either nothing applies, or nothing came to
mind. That is §6's distinction between *absent* and *no entry*, one level up, landing on the machinery
that reads it.

> **Recall returns a set plus a state, never a set.**

The state is cheap to compute from the wrong thing (*did I find anything?*) and expensive from the
right thing (*is this situation familiar?*). Unfamiliar-and-empty is a different event from
familiar-and-empty, and only the first should escalate.

### What recall is keyed by

Not the situation alone, but **the situation and the active goal**. The same world brings different
rules to mind depending on what is being attempted; recall keyed only on world features surfaces the
same set forever regardless of intent.

The mechanism is an index over shared terms: rules are linked to other rules by the members they have
in common, and recall is spreading activation over that web, seeded from both the current moment and
the current goal.

### Deliberate reasoning is not a second mechanism

Slow, exhaustive reasoning is **recall with the budget removed** — same match, same arbitrate, an
exhaustive proposal step. The fast/slow distinction therefore needs no architectural fork: a budget
parameter, and an escalation rule that is itself *a rule*:

```
<E> = causes( { +decision_point(?d), +recalled(?d, ∅), ~familiar(?s) },
              { +goal(exhaustive_recall(?d)) } )
```

The escalation triggers are exactly the impasses: nothing came to mind; what came to mind conflicts
irreducibly; or what came to mind was **surprising**, which is §15 feeding this rule.

### What trains it, and the trap

The training signal is already deposited by the machinery: which rule was applied where, and whatever
explanation a surprise produced. Recall learns from its own outputs that survived.

That has one failure mode which must be designed against rather than discovered:

> **Training recall on its own accepted outputs narrows it monotonically.** A rule that never
> surfaces is never applied, never reinforced, and becomes permanently invisible.

The exhaustive pass is therefore **not a fallback**. It is the only thing that injects candidates
recall would never have produced, so it must fire on novelty or on a schedule — not only on impasse.
Otherwise the agent calcifies precisely in the domains where it is performing well, and nothing
reports it.

### The carve-out

> **Recall may be incomplete about what to do. It may not be incomplete about what you must not do.**

A prohibition that fails to come to mind is a forbidden act that nothing notices. The repair is not to
make recall complete for norms — that reintroduces the exhaustive search this primitive exists to
avoid. It is to take prohibitions **off the recall path entirely**: check them at the write primitive,
indexed by the entries about to be written. That set is small and known, so the check is cheap and
exhaustive.

> **A prohibition is a gate on application, not a competitor in recall.**

### Scoring and price

| | one undifferentiated `select` | **recall + match + arbitrate** |
|---|---|---|
| not leaking | ❌ an incomplete step reports as authoritative; *nothing applies* asserts more than was checked | ✅ the two silences are distinguishable, and only one escalates |
| not lossy | ❌ *did you consider R?* is unanswerable | ✅ recalled, matched and rejected are three separate records |
| readable | ⚠ | ✅ *which rules does this situation bring to mind?* is a query, askable without applying anything |
| composable | ❌ learning and authority contend for one slot | ✅ learned proposal, authored arbitration, no contest |

The price is three records per decision instead of one, and an index that must be maintained as
episodes accumulate. The second is the real cost, and it is a **rebuild from the episode record, never
a patch of the previous index** — an index patched incrementally drifts from the history it claims to
summarise, and nothing detects it.

---

## 15. Surprise, commitment and reflection

> **Surprise is a match.** It is an *expected* entry and an *observed* entry that disagree.

That is the entire mechanism, and it is the sharpest illustration of requirement R7. If the agent's
expectations live in interpreter variables, an expectation is unmatched not because the rule is weak
but because there is nothing there to match. Three obligations follow.

**1. Forward application deposits a predicted moment.** Applying `causes(A, B)` at `M3` mints a moment
whose predecessor is `M3` and whose licence is *R applied, predicted*, carrying `B`'s entries, plus a
due-time derived from §10's timing member. Without the deposit there is nothing to be surprised
against.

Note what this avoids: a bespoke relation like `expected(+boiling(w), by t+7)` is not writable in this
vocabulary at all, because it puts a **sign inside a proposition**, and a sign is a member of an
entry. The moment form is not a workaround for that restriction — it is better, because it makes
surprise a **comparison of two moments**, which is an operation the design already needs.

**2. The continuation is a moment.** What the agent is doing, where it is in it, and what it is
waiting for are signed entries — not a stack frame.

**3. Surprise is an ordinary rule that wins on precedence:**

```
<S> = causes( { +predicted(?p, from ?m), +due(?p, by ?t), +now(?t'), after(?t', ?t),
                +deviates(?p, ?actual) },
              { +goal(explain_failure(?p)), −committed(?proc) } )
```

**There is no interrupt mechanism.** Preemption is `<S>` outranking the rule that would have continued
what the agent was doing — which is possible only because *continue what you were doing* was itself a
selectable rule. That is exactly what a stack frame is not.

### Procedures as data

A procedure is a committed order, and a committed order is precisely the thing that cannot be
preempted midway: if *to find an answer, look for causes* is control flow, step three owns the agent
until it returns.

> **Procedures exist, but as data that biases selection — never as control flow that owns the loop.**

`committed(?proc, step_3)` is an entry in the current moment that raises the precedence of continuing.
It does not remove the alternatives. So commitment is real — the agent does not dither — it stays
preemptable, and *dropping* it is a **write**, which means the agent can be asked why it abandoned
something.

### Strategies are defeasible

```
<M> = causes( { +goal(?g, explain(?f)) },
              { +goal(find(?r)), +constraint(?r, causes(_, {+?f})) } )
```

Because that is a rule, `overrides(M, M2)` and `unless(M, +domain(?f, social))` are sayable, and **a
strategy becomes defeasible like any other claim**. A strategy written as code cannot be overridden
by a statement in the knowledge base, and that asymmetry — not interruptibility — is the larger cost
of putting machinery outside the world the agent reasons about.

### Reflection is demanded, not continuous

Meta-rules are consulted only at **named decision points the interpreter already reaches**: which rule
to apply, what to do on failure, what to do on surprise. Never between arbitrary steps. Each decision
point either receives a meta-answer or falls through to the total table (§13), so no decision hangs.
Without this discipline, meta-cost is paid on every step and the tower never bottoms out in practice
even though it does in principle.

### Scoring, and the price

| | (A) connectives and strategy in the engine | (B) all rules, no floor | (C) rules + four primitives + total arbitrator |
|---|---|---|---|
| not leaking | ❌ engine decisions have no premise and appear in no explanation | ❌ regress; never grounds | ✅ every step cites its rule; the floor is four named things |
| not lossy | ❌ *why did you stop?* has no answer | ⚠ | ✅ deposits, commitments and abandonments are all entries |
| readable | ❌ strategy invisible to a query, undefeatable by data | ✅ | ✅ *which strategies are about explanation?* is a query |
| composable | ❌ two authors cannot add a connective | ⚠ meta-rules cannot be ordered | ✅ new connective means new rows; ordering means precedence |

**(C)'s price, named:** every step costs a selection, and a badly authored precedence table produces
dithering that reads as a bug in the rules rather than in the table. Both are measurable —
**selections per useful write**, and **commitments dropped per commitment made**. Those two counters
belong in the interpreter from the first version, not added after the symptom appears.

---

## 16. Acceptance

The gate is behavioural, not representational. It is not *can the system reproduce this text*; it is
**commutation**:

> For every rule `R` and every moment `s`:
> reading backwards from a goal proposes `R` at `s`
> **if and only if**
> reading `R` forwards at `s` yields a moment satisfying that goal.

Run it as a property over the whole rule set. A rule whose two readings disagree is a rule whose
consequent is lying about what it does.

The check is available **only because** there is one statement with two readings. With one rule per
direction it is untestable by construction — the two rules are simply different statements. With
program bodies it is undefined, because there is no backward reading to compare against.

Secondary gates, each following from a requirement:

* **R2** — for any conclusion, the agent can say whether it was reached forwards or backwards.
* **R5** — every entry in the graph has a licence, and no entry has a licence the write primitive did
  not stamp.
* **R6** — *the level rises by an unknown amount* is expressible, and reading the level afterwards
  reports ignorance rather than the old value.
* **R7** — a procedure in progress can be preempted by a surprise without any interrupt mechanism,
  and afterwards the agent can say why it stopped.

---

## 17. What this design does not settle

* **Cardinality.** *Made of four wheels* is a count claim in positional clothing. Backward matching
  needs cardinality declared per relation position, alongside arity and whether the position is
  ordered.
* **Constrained-not-bound values.** *The level rises by an unknown amount* wants a value member that
  is constrained rather than bound. Note the boundary §7 draws: **recognising** an ongoing pattern
  does not need this — a span superseded by a longer span is ordinary versioning — only **predicting
  that it continues** wants an unbound endpoint.
* **Consistency within a moment** (§5). Two entries with opposite signs in one locus is permitted and
  undetected. That is the right default, since consistency is a question rather than an invariant, but
  the design does not say who asks it or when.
* **Span normalisation** (§7). Equality of span content must be normalised by chain order rather than
  member order; the normalisation is not specified.
* **Speech time versus event time.** *Anna said it might rain this afternoon* has its **locus** at the
  moment of saying, and its **event time** as a member of the proposition. Both are needed and both
  are right, but §10 speaks only of timing between a rule's two moments and never says that a
  proposition may carry temporal members of its own. These two must share the moment vocabulary, or
  they become two more unrelated orderings.
* **Negation versus a false value.** *The stove is not lit* and *the stove has the attribute lit,
  false* are both expressible and mean different things — a claim about the moment versus a claim
  about the stove. Nothing guides the choice, and nothing detects the two being used interchangeably
  within one corpus.
* **Enforcing the write monopoly** (§12). *Rules may read entries; only the machinery may write them*
  is stated but has no enforcement mechanism. Until it has one, §11's soundness argument rests on
  convention.
* **Evidence accumulation** (§11). Counting over episodes, with no arithmetic on grades. The counting
  scheme is unspecified.
* **Familiarity** (§14). The escalation trigger needs *have I seen moments like this?*, which is a
  measure over the episode record and is not the same as *did recall return anything*.
* **The exploration schedule** (§14). When the exhaustive pass fires in the absence of an impasse.
  What is open is the *rate*, not the requirement; without one, recall calcifies silently.

---

## Appendix A. Glossary

| term | definition |
|---|---|
| **anchored** | of a moment: has individuals and a predecessor. The opposite of *generic*. |
| **arbitrate** | choose one rule among those that matched. Total, table-driven, always answers. |
| **connective** | `implies` or `causes`; the relation between a rule's two moments. |
| **entry** | a node with three members — locus, proposition, sign. The unit of assertion. |
| **generic** | of a moment: has variables and no predecessor. A rule's two members are generic. |
| **grade** | an ordinal modality on an entry: certain, likely, possible, unlikely, unknown. |
| **licence** | the node that says what authorised a moment's delta, or what produced an entry. |
| **locus** | an entry's first member: the moment or span the claim is about. |
| **match** | unify a generic moment against an anchored one, recording which entries matched. |
| **moment** | a signed delta, a predecessor and a licence. The only state construct. |
| **proposition** | a relation instance. Claims nothing until an entry places it. |
| **recall** | propose which rules come to mind. Learned; never complete. |
| **rule** | a fact whose two members are generic moments, related by a connective. |
| **sign** | `+`, `−`, `?`, or the absence of an entry. See §6. |
| **span** | a node with two members, a start and an end moment. A locus for trajectory claims. |
| **write** | mint signed entries into a moment. The only minter; stamps the licence. |

## Appendix B. Alternatives considered

Each was scored in the section named; this table is the index.

| decision | rejected alternative | why |
|---|---|---|
| rule form (§8) | guard plus a program body | the backward reading is a hypothesis wearing entailment's clothes with nowhere to record it; and a program has no subject, so nothing can be said about the rule |
| rule form (§8) | one rule per direction | two statements drift, neither is the other's premise, and the disagreement is undetectable |
| assertion (§5) | truth as a value on the proposition node | minting a node in order to deny it asserts it; correction overwrites the record it corrects |
| timing (§10) | a third member of the connective | the connective's arity varies, an absent delay silently defaults, and two sources cannot disagree |
| timing, modality (§9, §11) | fused connectives such as `likely_causes` | fuses strength with defeasibility and records neither; the name set grows multiplicatively |
| modality (§11) | grade on the proposition node | ignorable by default, and a cache of a derived value — which is a truth-maintenance system |
| modality (§11) | a guard node per uncertain fact | optional guards mean two shapes for every consumer; mandatory guards mean a node and a hop per certain fact |
| modality (§11) | probabilities instead of ordinal grades | independence assumptions cannot be stated in the graph, so the product looks like a measurement and is an artefact |
| entries (§12) | augment rules to speak of entries | cannot be written: the locus is an indexical, and a rule is generic |
| entries (§12) | authors write entries natively | every rule becomes plumbing, and provenance becomes forgeable |
| the floor (§13) | connectives implemented in the engine | engine decisions have no premise and appear in no explanation; a new connective means editing the engine |
| the floor (§13) | no floor at all — rules all the way down | infinite regress; the tower never grounds |
| selection (§14) | one undifferentiated `select` step | an incomplete step reports as authoritative, and learning contends with authority for one slot |
| span (§7) | enumerate a span's moments | two answers to what the span contains; arity varies with duration |
| surprise (§15) | an interrupt mechanism in the interpreter | what is interrupted must be a selectable rule, or preemption cannot be represented, explained or overridden |

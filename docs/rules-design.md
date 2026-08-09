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
- [9. Shapes](#9-shapes)
- [10. Connectives](#10-connectives)
- [11. Time](#11-time)
- [12. Modality](#12-modality)
- [13. The division of labour](#13-the-division-of-labour)
- [14. The engine floor](#14-the-engine-floor)
- [15. Recall](#15-recall)
- [16. Surprise, commitment and reflection](#16-surprise-commitment-and-reflection)
- [17. Acceptance](#17-acceptance)
- [18. What this design does not settle](#18-what-this-design-does-not-settle)
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
that, and on whose word?* The trace a piece of reasoning leaves behind is not a debugging aid; §12
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

REVIEW NOTE: "Not Leaking" means the SHAPE does not leak, if a reader ignores part of the shape, it's a reader's problem


| criterion | the question |
|---|---|
| **not leaking** | Can this shape state something the author did not intend? |
| **not lossy** | Is everything the author knew recoverable from what was stored — including what they *didn't* know? |
| **readable** | Can the obvious questions about this be asked as ordinary queries, without a special mechanism? |
| **composable** | Do two independently authored instances of this combine without either being rewritten? |

The most common leak has an innocent shape: a two-hop path through a shared node, which no one
authored and which nothing forbids reading as a claim.

**Leaking is a property of the shape alone.** A reader that drops part of a shape and concludes too
much is not a leak; the unauthored claim is in the reader, not in the graph. That failure is real, but
it is a question about the machinery — *why did the machinery return part of a structure?* — and the
machinery has exactly two places where it can be asked: **match**, which is what returns entries, and
**write**, which is what deposits them. A criterion that charged shapes for reader behaviour would
score the same shape differently depending on who read it, which is not a property of a
representation.

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
| a rule's antecedent or consequent | **none**, or another generic moment | — |

### Anchored and generic

The distinction that carries weight is not between kinds of moment but between:

* an **anchored** moment — individuals, and a predecessor in the history;
* a **generic** moment — variables, and no *anchored* predecessor.

A generic moment may have a **generic** predecessor. This is what lets a pattern say *and then*: a
pattern is a chain, not a point, and the same construct serves whether the chain is one link or many.
What a generic moment may not do is point into the history, because a pattern that named a particular
past would be about that one occasion.

A rule's two members are generic. Everything else is anchored. Because this distinction is
structural, it is checkable rather than maintained by convention, and it gives the engine's central
operation a one-line definition:

> **To match is to unify a generic chain against an anchored one.**

The one-link case is the common one, and reads as the older, narrower rule: unify a generic moment
against an anchored one.

**Nesting needs no mechanism.** A supposition inside a supposition is a path in the predecessor tree.
There is no depth limit and no scope object. *Scope* nesting is ancestry, and ancestry is derived —
there is nothing to push. This says nothing about **control**, which is a separate structure and §13's
subject: which reasoning invoked which, and where an answer is owed. Control is not scope, and the
absence of a scope stack does not mean the absence of the other.

### A moment is a belief state

A moment's delta is entries, and an entry names the moment it is **about** (§5). Those need not be the
same moment. An entry deposited in `M12` may have `M7` as its locus — *I now think it was raining
then* — and that is the ordinary form of learning something about the past.

So a moment carries two things at once, and the design needs no separate construct for the second:

| | |
|---|---|
| the world at a point | the entries in the delta whose locus is the moment itself |
| **what the agent believes here, about any time** | the delta entire |

**There is no belief-set object.** A moment already is one. What would be *the current beliefs* is the
chain read at the moment you are standing in, and belief revision is ordinary succession — the same
relation, with a licence saying *I came to think otherwise*. Introducing a second membership structure
for beliefs would create a second ordering beside succession, which is precisely what the next
subsection refuses.

### Reading through the chain

Because a moment stores only what changed, a moment does not contain its state; **the state is what
the chain answers.** Reading is a walk, not a lookup. This is the single most consequential cost in
the design, and it is accepted deliberately: it is what makes supposition free, history immutable, and
every claim dated.

Because an entry has both a locus and a deposit moment, the walk uses **two indices, and they do
different jobs**:

> **Locus filters. Chain position orders.**

To ask *does `on(a, b)` hold at `M7`, as far as I now know?*, walk back from where you are standing,
keep the entries whose locus is `M7`, and take the one deposited latest. To ask *what did I think at
`M7`?*, walk back from `M7` instead. Both questions are answerable, they are different questions, and
in the common case — an entry deposited at its own locus — they coincide, which is why the
distinction can be missed.

This is what makes the two temporal readings of §12 available without a second mechanism, and it is
what settles the collision §5 would otherwise leave open when two entries share a locus.

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

**When the claim was made is not a fourth member.** An entry is in some moment's delta, and that is
its deposit moment — *believed since here*. It is already structure, so it costs nothing and cannot be
omitted. The locus says **what the claim is about**; the delta membership says **when it was made**.
Keeping them apart is what lets the agent revise its view of the past without rewriting it, and
conflating them is what would force every claim to be about the moment it occurred to someone.

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

The claim is narrow, and the narrowness is what makes it survive. An entry needs no entry **to be
located**. It may freely be the **subject** of another entry's proposition, and it has to be, or the
design loses three things it depends on:

```
mistaken(<e>)                     §5's correction — my record was wrong
outranks(<e1>, <e2>)              §13's arbitration — a claim Anna made beats one Bo made
supposed(<e>, <S>)                a belief held about a belief
```

Those are ordinary entries with ordinary propositions that happen to point at entry nodes, and each
locates itself. **Locus and member are different relations to an entry, and only the first would
regress.**

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
entries naming this proposition at the locus asked about, and take the one deposited latest*. The
engine must know what `entry` means; it cannot be ordinary vocabulary. This is one of the very few
relations the engine dispatches on, and that set should be declared in one place rather than
accumulating.

*Deposited latest*, not *nearest along the walk* — §4's two indices. Two entries may share a locus,
and when they do the later deposit is the agent's current view; the earlier one is what it used to
think, still readable and still true of when it was thought. Resolving by proximity instead would make
the answer depend on where the reader happened to start.

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

The moments an **anchored** span contains are **not** listed, and the reason is structural: **the
predecessor relation is single-valued.** A moment has one parent; forking produces several successors,
never several parents. So the walk back from `M12` is unique, and if `M7` lies on it the span's
contents are fully determined by the chain.

The table below therefore scores anchored spans, where the chain is available to settle the question.

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

### A generic span's interior must be described

A generic span has no chain, so nothing determines what lies between its endpoints. Endpoints alone
say only *start before end*; enumerating an interior would invent a length nobody claimed. **For a
generic span, option (C) is not a rejected alternative but the only one available** — the interior is
given by a *description*, and §9 is what descriptions are made of. The ❌ in (C)'s composability
column is the bill that comes with it, and §9 states what it costs.

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

`<A>` and `<B>` are generic (§4): variables, no anchored predecessor. `<A>` is the antecedent. `<B>` is
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
| **forward** | match `<A>` against the current chain; apply `<B>`'s signs into a successor moment |
| **backward** | unify a wanted fact against `<B>`'s `+`/`−` entries; `<A>`'s unsatisfied members become subgoals, as far as the agent can discharge them |
| **`?` entries, backward** | *this rule disturbs that and cannot say how* — a **want**, not a failure, and not a false *it stays as it was* |

Direction is a **query over the rule**, never a field in it. This is R1: one statement, two readings.
R2 is met because each reading cites `<R>`, and the licence recorded on the resulting entry says which
reading produced it — so a hypothesis formed by reading backwards is distinguishable, permanently,
from a conclusion drawn forwards.

### An antecedent has two kinds of member

An entry names its own locus (§5). So an antecedent is not *entries at one moment*; it is **signed
entries whose loci are variables**, together with the **skeleton** that relates those variable loci:

```
where    ?n = succ(?m),   ?s = span(?m, ?e)       skeleton — how the loci connect
given    +on(?x, ?y) @ ?m,  +acts(?a) @ ?n        entries — what is claimed, and where
```

The one-locus case, where every entry sits at the same moment and the skeleton is empty, is the common
one and is written without either keyword.

The two kinds do not merge, because a skeleton member is **not a claim**. `?n = succ(?m)` has no sign,
no locus and no licence; nobody asserted it, and it cannot be denied, dated or attributed. §3 says why:
ordering is a fact about how a node is built, not a relation in the world. The skeleton is the part of
the antecedent that match settles by unifying structure, rather than by walking a chain for entries —
§13's split, applied to the antecedent itself.

Distinctness belongs in the skeleton for the same reason. `?a ≠ ?b` is a condition on the binding, not
a dated claim that two individuals differ.

### A consequent may name its locus, when the locus is bound

An antecedent binds variable loci; a consequent may use them. §9's shape rules already depend on this —
`then +taking_turns(?a, ?b) @ ?s`, where `?s` came from the skeleton — and without it a recognition
about a stretch could only ever be deposited as a claim about the instant it was noticed.

This does not weaken §13's argument that a rule cannot name a locus, because the two say different
things. A rule may not name **a particular** locus; that is what makes it generic. It may name a
**variable** one that match bound, because a variable is exactly what does not commit the rule to an
occasion. Where a consequent names no locus at all, the frame supplies it (§13), and that is the
common case.

### Achievability is not a mark

Read backwards, an antecedent member becomes a subgoal — but not every member should. *To unbolt it,
it must be on the bench, and you may put it there; it must be a Tuesday.*

That difference is **not a property of the member**, and cannot be marked on it, because achievability
is relative to four things the rule's author does not know:

| relative to | *make it Tuesday* is |
|---|---|
| **who is planning** | out of reach for me, in reach for whoever can move the meeting |
| **the deadline** | achievable if I have a week, not if I need it within the hour |
| **the situation** | already true, on a Tuesday |
| **the rules known** | achievable exactly when `wait` is among them |

A mark authored once, at rule-writing time, is relative to none of them — and it is the wrong shape
besides. Achievability is *derived* from capabilities, budget and the rule set; stored on the rule it
is a cache of a derived value, invalidated by learning a rule or gaining an authority, which is the
defect §12 names when it refuses to store a grade on a proposition.

What the mark would have been doing is three things, each with a home already:

| the work | where it belongs |
|---|---|
| *don't expand this, you will thrash* | **recall** (§15) — learned, incomplete, and the one step where being wrong is recoverable |
| *achievable, but only by waiting, or only for the boss* | a **claim**, attributed and defeasible, with its cost as §11 timing |
| *you could, and you must not* — seeding clouds to make it rain | a **prohibition** (§15), gated at the write primitive |

The third is the reason to insist. A mark lets a norm masquerade as a physical impossibility, and
those must not share a slot.

So every antecedent member is simply a required entry, and *is this one worth planning for* is asked
of the agent, not read off the rule. **Waiting is an action**, so a precondition that takes time is
achievable at a price — which §11's timing already states in a form that may be absent, attributed and
compared against a deadline:

```
+tuesday(?d)                              an ordinary requirement
timing(WAIT, start→end, [0, 7days])       what discharging it costs
```

The bill is that backward search loses a static bound: *make it Tuesday* is now a subgoal a planner may
genuinely expand. §9 states the discipline that replaces it — bounded expansion returns a result **and a
state**, so *I found no way* stays distinguishable from *there is no way*.

### Worked

```
<R1> = causes(
    { +heat(?a, ?w),  +water(?w),  +open(?vessel) },
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

## 9. Shapes

Some things are known by their **shape** rather than by their extent. *Anna and Bo are taking turns*
can be said having watched a sequence, and it can be said having watched nothing — *imagine they are
taking turns* — and it is the same claim either way. The second reading is the demanding one: there is
no sequence to point at, and materialising one would state a number of turns nobody claimed.

Two kinds of indefiniteness need this, and they are not one construct:

| | *taking turns* | *some files* |
|---|---|---|
| indefinite in | **extent along the chain** | **multiplicity within a moment** |
| composes by | succession — ordered, and the elements are moments | membership — unordered, and the elements are individuals |
| leak if materialised | invents a number of turns | invents a number of files |

They share one principle, which §7 already applies to spans and which this section generalises:

> **Describe the extent. Never enumerate it.**

### A shape is a definition, not a term

Given §8's antecedent, a shape needs no new construct: it is a **recursive definition over spans**,
written as ordinary rules in open-class vocabulary. *Taking turns* needs at least two turns, so that
is the base case, and the step case consumes one turn and defers the rest:

```
<TT-base> = implies(
    where    ?n = succ(?m),  ?p = succ(?n),  ?s = span(?m, ?p),  ?a ≠ ?b
    given    +acts(?a) @ ?n,   +acts(?b) @ ?p
    then     +taking_turns(?a, ?b) @ ?s )

<TT-step> = implies(
    where    ?n = succ(?m),  ?s = span(?m, ?e),  ?s' = span(?n, ?e)
    given    +acts(?a) @ ?n,   +taking_turns(?b, ?a) @ ?s'
    then     +taking_turns(?a, ?b) @ ?s )
```

`acts` is an entry rather than anything special, because §11 already settles that an action is an
ordinary fact holding over an interval.

**The alternation is the argument swap** — `?a, ?b` in the head, `?b, ?a` in the recursive member.
Remove it and the definition says *someone acts repeatedly*. That swap is a back-reference, and it is
the reason a shape is a definition rather than a pattern term: see below.

The two readings of §8 are what make one definition serve both cases. **Forwards** it recognises an
observed stretch. **Backwards** it generates a hypothetical one, expanded only as far as a goal
demands, each step an imagined moment with its own licence (§4). So *they took turns* and *imagine they
are taking turns* are R1 one level up: one statement, two readings.

### These definitions are already a grammar

`<TT-step>` threads a start, a middle and an end through its members. That is a difference list, and a
rule consuming a chain between two endpoints is a grammar production over the moment chain. Spans are
the difference lists; §7 built them. So the question is never *grammar or not* — it is whether the
grammar is reserved or open-class, which is §10's membership test one level up.

Reserved would buy exactly one thing: **decidable equivalence**, the ❌ in §7's (C) column. It does not
survive contact with what shapes are actually for:

* *the same actor does not go twice running* — a back-reference;
* *each turn touches a different file* — inequality across an unbounded set;
* *at most five times, **unless** interrupted* — defeasibility, which needs `unless` and precedence
  **inside** the parser.

Each leaves the class that made equivalence decidable, and the last is not a grammar question at all:
a production cannot carry `unless` or `overrides` without re-deriving precedence inside a second
engine. A reserved formalism buys decidability and then spends it on its first three extensions.

### Bounds are facts about the shape

A shape needs a subject — something for a bound and a provenance to attach to, since neither belongs to
the base rule or the step rule alone. That subject is one open-class relation:

```
<TT> = shape( taking_turns(?a, ?b) )
repeats(TT, [0, 5])                       absent means unbounded
by(TT, boss)     about(TT, protocol)      unless(TT, +interrupted(?s))
```

This is §11's timing member, exactly: a constraint on an extent, sayable as an interval, absent meaning
unknown, and permitted to disagree with another source. It reads in both directions the same way —
**forwards**, exceeding the bound is a deviation, so §16's surprise rule applies unchanged;
**backwards**, the bound is a filter, and therefore the termination discipline for expansion.

Counting costs nothing structurally. Every entry carries a licence naming its application (§13), so
*how many times did this shape step here* is a walk over the trail — derived, dated, never stored,
which is the discipline §12 states for grades. §12's refusal of numbers does not transfer: it was
specifically that probabilities need independence assumptions unstatable in the graph, and a count of
applications is an exact observation of the trail, where comparison is not composition.

### Two bounds, which must not share a slot

| | *they take at most five turns* | *expand this at most five times* |
|---|---|---|
| what it is | a **claim about the world** | a **budget on the agent's effort** |
| where it lives | `repeats`, on the shape — attributed, gradeable, defeasible | §15's budget |
| can it be wrong | yes; a sixth turn is a **surprise** | no — it is not about anything |
| exhausting it yields | *no* | ***I don't know*** |

Fuse them and *the shape ended at five* becomes indistinguishable from *I stopped at five*. That is
§6's `−` against *no entry*, and §15's *nothing applies* against *nothing came to mind*, arriving a
third time, so it takes the same answer:

> **Bounded expansion returns a result and a state, never a result.**

### Plurality is a group, and its membership is not stored

*Some files were copied* has the same defect under materialisation and takes the same principle. Mint
**one** node for the plurality and do not enumerate it; what is known about its size is an ordinary
fact about that node:

```
<fs> = files                 a group; members not stored
atleast(fs, 2)               absent means unknown
+copied(fs) @ ?m
```

This is §7's move — *membership is not stored* — over membership instead of over a chain. It also
disposes of counting-in-positional-clothing: *made of four wheels* is a claim about a group's size, not
a four-place relation, and it is then attributable and defeasible like any other claim.

Whether the claim distributes — *each file was copied* against *the files together filled the disk* —
is a fact about the **entry**, not a new construct. Same slot discipline as the grade in §12.

### Scoring

| | (A) materialise a witness sequence | (B) a reserved grammar with counters | (C) recursive definitions, bounds as facts |
|---|---|---|---|
| not leaking | ❌ states a length nobody claimed; a consumer reads three turns as *the* number | ⚠ a production's reading pair is fixed by the engine, so it has no premise and appears in no explanation | ✅ only the shape is asserted; every expansion step is licensed and dated as supposition |
| not lossy | ❌ *how many?* answered by an artefact | ⚠ the parse is recoverable only by running the parser, unless the chart is deposited as entries — which is the trail again | ✅ the definition **is** the shape; ignorance of length is recorded by there being no length |
| readable | ✅ trivially | ⚠ *which shapes bound repetition* needs a walk over production terms — a second query language | ✅ shapes are rules and bounds are facts, so R4's questions stay ordinary queries |
| composable | ❌ two witness sequences of different length are not the same claim | ❌ a second closed set, and a production cannot carry `unless` or `overrides` | ✅ definitions compose as rules; `repeats`, `by` and `unless` attach unchanged |

### Costs

* **Shape equivalence is undecidable.** §7 named this as (C)'s price and this is where it is paid: with
  recursion you can say *taking turns*, and you can no longer decide in general whether two definitions
  describe the same shape.
* **§17's commutation gate runs per instance, to a depth**, rather than as a property over the whole
  rule set.
* **Backward expansion can mint unboundedly.** §7's discipline — spans are minted by recognisers, never
  enumerated — becomes the stronger requirement that expansion is demand-driven and budgeted, with the
  cycle care §12 asks of any walk over derived structure.
* **A shape is two rules where an author expects one.** Recall is keyed by shared terms (§15), so
  nothing guarantees that a base case and its step case surface together.

---

## 10. Connectives

The reserved vocabulary of the whole design:

| layer | closed set | size |
|---|---|---|
| connective | `implies`, `causes` | **2** |
| entry sign | `+`, `−`, `?`, no entry | 4 |
| skeleton | succession, and membership position | 2 |
| grade | `certain > likely > possible > unlikely > unknown` | ordinal, ~5 |
| timing | one relation over the two moments' endpoints | 1 |
| locus resolution | `entry` — the relation the engine dispatches on (§5) | 1 |
| the frame register | *which node the machinery is currently reasoning in* (§13) | 1 |

Everything else — `heat`, `cloudy`, `boss`, `overrides`, `by`, `about`, `unless`, `shape`, `repeats`,
`taking_turns` — is open-class vocabulary and reserves nothing. Authors may coin freely.

### The machine is made of open class, and must be

§13 introduces processes, frames, seats, topics and channels. None of them appear in the table above,
and that is not an oversight to be corrected by adding five rows. **It is what R7 requires.** If the
machinery's own state were reserved vocabulary, *the agent's own state is in the world it reasons
about* would be false in the one place it matters most, and no rule could override a strategy, notice
a stalled process or prefer one channel to another.

What keeps this from being an unbounded reserved set is a distinction §5 asks for and does not draw:

| | |
|---|---|
| what the engine **dispatches on** | must be declared, and is the table above |
| what is written in **open-class vocabulary and merely read by rules** | unbounded, and includes almost all of the machine |

A frame is `frame(seat, topic)` — a node with two ordered members, structurally identical to §7's
`span(start, end)`. Ordered members are already reserved by §3, so the engine learns no new relation
name. What it needs is **one register**: which node is the current frame. That is the row above, and
it is a pointer rather than a vocabulary item.

`process`, `channel`, `committed`, `waiting_for` and the rest are then ordinary open-class relations,
authored and overridable, which is the property §16 depends on when it makes a strategy defeasible.

> **The machinery is written in the language it interprets. Only the register is privileged.**

The skeleton row costs nothing new. Succession and membership position are §3's and §4's provisions,
which the substrate has always reserved; listing them makes an existing cost visible rather than adding
one. What an antecedent may not carry is a *third* kind of member.

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
multiplicative growth §11 and §12 are designed to avoid.

---

## 11. Time

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
§16 matches against. **Backward**, it is a **filter**: needing boiling water within two minutes rules
this rule out of the plan. A rule with no timing expresses neither.

Because waiting is an action like any other, this is also how a precondition the agent cannot *make*
true gets planned for. *It must be a Tuesday* is achievable at a price of up to seven days, and the
price is a timing constraint — sayable, absent when unknown, and compared against the deadline. That
is what §8 leans on when it refuses to mark a member unachievable.

### Three times, and only one ordering

Time shows up in three places, and it is worth being explicit that this is not three time systems.

| | what it is | where it lives |
|---|---|---|
| **about-when** | the stretch a claim concerns | the entry's **locus** |
| **believed-since** | when the agent came to think so | the entry's **deposit moment** (§5) |
| **event description** | *afternoon*, *Tuesday*, *morning* | **members of a proposition** |

The first two are §4's two indices. The third is the one that needs discipline, because it is already
in use — `+cloudy(?day, morning)` in `<R2>`, and `+tuesday(?d)` in §8 — and left unexamined it would
be a second ordering competing with succession.

It is not one, and the rule is:

> **Calendar terms denote. The chain orders.**

*Afternoon* is a **name for a stretch of the chain**, resolved against the clock stamp §4 puts above
succession. It is not an ordering relation and nothing may compare two calendar terms directly; to ask
which came first is to resolve both to spans and compare endpoints, which §7 already provides. A
vocabulary that ordered calendar terms among themselves would be §4's warning realised — two orderings
that agree by convention and drift without detection.

This is what makes reported speech expressible, which the timing member alone could not do:

```
<e1> = entry( <M9>,      says(anna, <p>),   + )      Anna spoke, at the moment of speaking
<e2> = entry( <afternoon>, rain,            + )      graded @possible, licensed by <e1>
```

`<e2>` is deposited now, is about the afternoon, and is believed on Anna's word — three different
times and one authority, none of which needs a construct that does not already exist.

---

## 12. Modality

Four different things get called *possibility*, and they must not share a slot.

| | what it is | where it goes |
|---|---|---|
| **strength** | how often the effect actually follows | a grade on the **entry** |
| **confidence** | how far the agent trusts where this came from | a grade on the **source** (§13); moves with evidence |
| **defeasibility** | what would cancel it | **not a number** — a relation to other rules: `unless`, `overrides` |
| **achievability** | whether *this* agent can bring it about, now, within budget | **nowhere** — derived at read time from capabilities, budget and the rule set (§8) |

The fourth is the one with no storage at all, and that is the point: it is relative to the reader, so
any place to put it is a cache of a derived value.

Collapsed into one number, `0.6` means three things at once, and combining two such numbers is
arithmetic nonsense. Defeasibility is the load-bearing one for reasoning — *unless the front has
already passed* — and it needs **no numeric apparatus at all**: it is the same precedence machinery
that makes the boss's rule beat the vice's.

**Grades are per-entry, not per-rule.** One rule has consequences of different strength: heating boils
the water (certain) and scorches the pan (unlikely). A rule-level grade cannot express that; it is at
best shorthand for *all entries the same*.

**Confidence is a property of the source, not of the rule.** *How sure am I of this rule* and *how
sure am I of this sensor* and *how far do I trust this speaker* are one question asked of three
sources, and §13 makes every entry name the source it arrived through. Rule-confidence is then the
case where the source is the knowledge base. One mechanism covers all three; a grade slot on rules
would cover only the first and would have to be reinvented for the other two.

**Grades are ordinal, not probabilistic.** Real probabilities require independence assumptions that
cannot be stated in the graph, so multiplying them leaks silently — the product looks like a
measurement and is an artefact. Ordinal grades compose by **weakest link**. A numeric member may sit
*beside* the grade where its own provenance is a member — *from 300 observations* — but never in
place of it.

**Weakest link is sound down a chain and silent across a convergence**, and the two cases must not be
confused:

| | shape | what min does |
|---|---|---|
| **chain** — a source I half-trust, reporting a rule that only usually holds | sequential attenuation | correct, and correct as an *upper bound*: no conclusion is surer than the weakest step that produced it |
| **convergence** — two sources independently reporting the same thing | corroboration | **wrong**: belief should rise, and min holds it flat |

The honest cost is the second row. Two independent *likely*s ought to amount to more than *likely*.
Ordinal grades do not accumulate evidence, and the right place to fix that is **counting over
episodes**, not arithmetic over grades; §18 records it as unsettled. What the design must not do
meanwhile is let the chain case silently stand in for both.

**The grade a rule authors is a contribution, not a verdict.** §8's consequents carry per-entry grades
— `+boiling(?w) @certain` — and those are one link in the chain, never the answer. The grade of the
deposited entry is `min(authored, support)`. Without that, a rule that says `@certain` on the strength
of a source graded *possible* launders a weak input into a strong output, and the weak link vanishes
from exactly the walk §12 relies on. **A rule states how strongly it would conclude, given its
premises. What its premises were worth is not its to say.**

Grade is orthogonal to the `?` sign. `?volume` is *this changed and I cannot say to what*;
`+rain @possible` is *this might become true*. Different ignorance, different slot.

### Where the grade lives

Not on the proposition node — and not for reasons of cost.

> A grade stored on a proposition node is **a cache of a derived value**. *Rain is likely* holds only
> given the support that produced it, so when the support changes the tag must be invalidated. General
> invalidation over a web of dependencies is a truth-maintenance system: a second machinery, with its
> own consistency problem, running underneath the first. **An index over what was asserted is
> storage; a cache of what was derived is a truth-maintenance system.**

A second, independent reason: **a tag is a separate read.** Reading a fact and reading its grade are
two operations, so the grade can be obtained without the fact or the fact without the grade — and an
ungraded conclusion reads as certain.

This is **not** a leak. Nothing unauthored is in the graph: the fact was asserted and the grade is
attached, and the extra content — *certainly* — is manufactured by a reader's convention. §2 says why
that is the machinery's question rather than the shape's. But it is still the machinery's question,
and it has an answer here: **the grade must ride the node that match already has to return.** An entry
cannot be matched without its sign, because the sign is a member; put the grade there and it cannot be
matched without its grade either. One read, or none.

That is the difference between a discipline and a structure, and it is available only because the
entry exists anyway.

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

The demanding case is not the world changing but the agent changing its mind about a time that has
already passed — *at `M12` I conclude they were not taking turns at `M7` after all*. That is a second
entry with the **same locus** `M7` and a **later deposit**, and the property still holds:

| the question | the walk | the answer |
|---|---|---|
| what do I now think about `M7`? | from `M12`, locus `M7`, latest deposit | the revision |
| what did I think at `M7`? | from `M7` | the original |

Nothing was invalidated, nothing propagated, and both answers survive — which is what makes *why did
you change your mind?* a query rather than an archaeology. **The property is a consequence of the two
indices, not of writes always landing at now.** A design with a single index would have to choose
which of those two questions to keep.

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
| not leaking | ❌ a grade on a timeless node is *likely* said of no occasion and every occasion at once; the author meant *likely given this support* | ⚠ the guard says uncertain-in-general, so it leaks the same way, more loudly | ✅ a conclusion drawn in a moment **is** in it; the grade is recomputed from support |
| not lossy | ❌ a number with no premise | ⚠ says *that* it is uncertain, not on whose word | ✅ speaker, rule and sighting all survive |
| readable | ⚠ readable and stale | ⚠ | ✅ *which conclusions rest on something merely possible* is a walk |
| composable | ❌ two tagged facts combine to *what?* | ❌ every consumer must handle both shapes, guarded and bare | ✅ weakest link over the support chain |

Separately from the scoring — because it is not a property of these shapes but of the machinery that
reads them — (A) and (B) differ in whether the grade **can be obtained without the fact**. Under (A)
it can, and an ungraded read is the default one. Under (C) it cannot, because the grade is a member of
the node match already returns. That is the argument above about tags and structures, and it is why
(C) wins by more than the table shows.

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
  a nicety to a soundness condition, and it is why §13's gate exists.
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

## 13. The division of labour

Every claim is made through an entry (§5). So: are rules **augmented** to speak about entries, or does
the **machinery** apply rules to entries? The machinery — and the alternative is not merely costly, it
cannot be written.

### Augmentation is a category error

```
+on(a, b)      ⟶      entry( <the moment I am in> , on(a, b), + )
                             ^^^^^^^^^^^^^^^^^^^^
```

**The locus is an indexical.** A rule is generic: variables, and no anchored predecessor. An entry is
anchored. A rule that named a locus would be about that one occasion and could not be
reused. So augmentation
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
| `+boiling(?w)` in the consequent | mint the entry; stamp locus, licence, source and grade from the frame and this application |

> **The rule's members are what the author knows. The entry's members are what the application knows.**

Locus, licence, source and grade-at-this-application do not exist until the rule runs. That is the
whole split, and it is why `entry` is engine vocabulary rather than something an author writes.

| | (A) augment the rules | (B) authors write entries natively | (C) the machinery absorbs it |
|---|---|---|---|
| not leaking | ❌ explanations show the rewrite, not the rule | ❌ an author supplying a deposit stamp can date a claim to when it was not held | ✅ every entry is stamped by the write that made it |
| not lossy | ❌ two shapes; *why* must un-augment | ✅ | ✅ |
| readable | ❌ three times the plumbing per rule | ❌ every rule is plumbing | ✅ the rule reads as written |
| composable | ❌ resolution policy frozen at augmentation time | ⚠ | ✅ resolution can change without touching a rule |

(A) additionally cannot be written at all, per the indexical above.

### The gate

An entry is both a mechanism and a node a rule can point at. Reading is how *a claim Anna made
outranks one Bo made* gets stated at all. Writing is where soundness lives, because §12 makes the
support trail load-bearing: a write that loses its attribution does not merely become unexplainable,
it becomes **falsely confident**, since a missing support link removes a weak link from the minimum.

The requirement that follows is narrower than it first appears:

> **No write bypasses the stamp.**

*Only the machinery may write entries* is one way to achieve that, and it is stronger than necessary.
What must be impossible is an entry whose provenance is **absent or false**. What need not be
impossible is an entry a rule caused to exist — every such entry arrives through the gate and leaves
it stamped with the rule that caused it, which is not forgery but the ordinary record.

Two things this distinction rescues, which the stronger prohibition forbids by accident:

**Backdating is not the same as claiming about the past.** Backdating is lying about when a claim was
made — a false stamp. Writing now, honestly, about an earlier time is a **past locus with a present
deposit**, and the record reads *at `M12`, by this rule, I came to think it rained at `M7`*. §4's two
indices make the second sayable and the first still impossible, because the deposit is structure and
not an argument.

**Trust is a rule, not a hard-wired intake.** *The user says it is raining* becomes *it is raining* by
an ordinary rule that the agent can be asked about, argue with and override. An intake path that wrote
the second directly would be the genuinely unsafe design, and it is what a blanket rules-may-not-write
encourages.

### Channel is not authority

Every entry names where it arrived from, and that has two layers which must not be fused:

| | what it is | can it be wrong |
|---|---|---|
| **channel** | the intake path — this socket, this sensor, the knowledge base | no: mechanically observed, like a sensor that cannot misreport its own reading |
| **authority** | who is taken to have spoken, and what their word is worth | **yes** — an ordinary claim, gradeable and defeasible |

The knowledge base is a channel like any other. Reading it faithfully is guaranteed; what it **says**
is as contestable as ever, which is what §8's `by(R, boss)` and `overrides(R1, R2)` depend on. Fusing
the two would make authority unforgeable by fiat, so that anyone reaching the right socket would
thereby be the boss.

### Frames

A rule cannot name a locus, and the machinery must supply one. **The frame is what it supplies it
from.** A frame is the reasoning in progress — a process node, and therefore a fact on the graph,
which is R7 discharged for the machinery itself.

A frame carries two things:

| | |
|---|---|
| **seat** | the moment its writes are deposited in — *where I am standing* |
| **topic** | the locus its writes are stamped with — *what I am reasoning about* |

Normally they coincide, and that is the case §5 describes. They come apart exactly twice: reasoning
about the past, where the topic is an earlier moment and the seat is now; and reasoning under a
supposition, where the seat is inside the supposition.

That gives the whole of what the gate does:

> **Proposition and sign come from the rule. Locus, licence, source and deposit come from the frame
> and the clock. A rule may not name the second four.**

| stamped | taken from |
|---|---|
| **locus** | the consequent's bound locus if it has one (§8), otherwise the frame's topic |
| **deposit** | the frame's seat |
| **licence** | this application: the rule, and the entries match consumed |
| **source** | the channel this arrived through |

Two properties fall out rather than being enforced. **Hypothetical containment is structural** — a
conclusion drawn inside a supposition cannot land outside it, because the locus was never the rule's to
give. And **forgery stops being a category**: nothing is prohibited, everything is stamped.

### Entering and inspecting

Two operations look like they need primitives and neither does.

**Inspecting is matching.** §14's match unifies a generic chain against an anchored one, and nothing
requires the anchored chain to be the one you are standing in. Reading another frame's conclusions is
match with an explicit anchor, and it changes nothing.

**Entering is writing.** Moving the seat is writing a fact about a process node, stamped and dated
like any other write, so the trail reads *this reasoning moved to `M7` and then concluded*. A rule can
therefore relocate its own seat — which is not a hole but the mechanism by which deliberate reasoning
about the past happens at all, and it is auditable precisely because the move is itself an entry.

One requirement is load-bearing:

> **Reading never moves the seat. Inspecting a frame is not entering it.**

Otherwise weighing two hypotheses would adopt both.

### Frames form a forest, and nothing leaves one

Frames are not a stack. A stack assumes one live frame and a return to the caller, and the case that
breaks it is the ordinary one: **two hypotheses under comparison are siblings, both alive, neither the
caller of the other.** Frames form a forest; what looks like a stack is the ancestor path of whichever
frame is in focus, and ancestry is derived, so there is nothing to maintain. This is §4's *nesting
needs no mechanism*, one level up.

A frame ends when its goal is discharged, its budget is spent, or arbitration moves on — and it ends
the way every bounded thing in this design ends, with **a result and a state**: discharged, exhausted
or abandoned. That is §6's `−` against no-entry, §9's bound, and §15's two silences, arriving a fourth
time.

What does a conclusion look like on the way out? It does not come out.

> **Conclusions stay at their locus. What crosses is a claim *about* the frame, made outside it.**

Copying a conclusion out and re-qualifying it is the alternative, and it fails on this design's own
terms: it makes one fact exist in two shapes, which is the objection to augmentation above, and it
needs invalidation the moment the supposition is discharged differently, which is what §12's dating
exists to avoid. So a caller that has learned something from a scenario writes a **new** entry at its
own seat whose proposition is about the scenario — `yields(S1, +boiling(w))`, or `preferable(S1, S2)`.

Comparing two hypotheses is then inspecting both and writing a preference; neither is adopted.
**Adopting** one is a separate, deliberate, licensed write — the same shape as deciding to trust a
channel, which is the point at which *the user says it is raining* became *it is raining*.

### Costs

* **A bug in the gate is systemic** — every fact in the system gets the same wrong provenance.
  Mitigated by it being one place, which makes it one check.
* **Matching becomes a chain walk rather than a lookup**, and that walk now sits on the rule-matching
  path, not only on reads.
* **Matching must record which entries it matched.** Otherwise *because a was on b, on Anna's word*
  has no answer. This is not overhead: it is half the trail, and it is what makes a misbehaving rule
  distinguishable from a misresolving chain.
* **Every seat move is a write**, so deliberate reasoning about the past leaves a trail proportional to
  how often the agent shifts its attention, not to what it concludes.
* **Nothing stops a frame being seated somewhere useless.** A seat that is not an ancestor of its topic
  is as meaningless as §7's inverted span, and takes the same remedy: check it where the frame is
  minted, while the mistake is still attributable.

---

## 14. The engine floor

If the meaning of `causes` is given by rules, and those rules use connectives whose meaning is given
by rules, the tower never reaches ground. **The reserved set cannot be empty.** What it can be is *not
the connectives*.

Four primitives:

1. **recall** — which rules come to mind here. **Never complete**, by design (§15).
2. **match** — unify a **generic** chain against an **anchored** one, over what recall offered. It
   settles the antecedent's skeleton by unifying structure and its entries by walking the chain, and it
   records which entries it matched (§13).
3. **write** — mint signed entries. **The gate**: it stamps locus, deposit, licence and source from
   the frame and the clock (§13), and no write bypasses it.
4. **arbitrate** — among the rules that matched, choose one. **Total**: table-driven, always answers.

> **Recall proposes. Match filters. Arbitrate commits. Only the last is total.**

Backward reading is not a fifth primitive. It is rules over these four, expanded on demand under a
budget, and per §9 it returns a result **and a state** — because a search that stopped is not a search
that found nothing.

Neither is anything §13 added. **Inspecting** another frame is match with an explicit anchor.
**Entering** one is a write against a process node. **Scheduling** — which process runs next — is
arbitration, and it must be arbitration rather than a mechanism beside it, or the design acquires a
second selection step lacking the stratification condition below.

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

If a new connective requires editing the engine, then the connective set is not data and §10's budget
is fiction.

### One interpreter

Meta-rules buy nothing if the interpreter special-cases them. The interpreter's step is *select a
rule, apply it*, and object-rules and meta-rules must be indistinguishable to it — a flat tower, not a
stacked one. If, standing inside the interpreter, you cannot answer *which level am I on?*, that is
the sign it is built correctly.

---

## 15. Recall

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

Judgements of what is worth attempting live here too. *Don't plan to make it Tuesday* is not a fact
about the rule (§8) and not a prohibition (below); it is a learned bias about which subgoals are worth
expanding — which is to say, about which rules come to mind when reading backwards. It belongs in the
step where being wrong costs a worse plan rather than a wrong action.

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
irreducibly; or what came to mind was **surprising**, which is §16 feeding this rule.

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

## 16. Surprise, commitment and reflection

> **Surprise is a match.** It is an *expected* entry and an *observed* entry that disagree.

That is the entire mechanism, and it is the sharpest illustration of requirement R7. If the agent's
expectations live in interpreter variables, an expectation is unmatched not because the rule is weak
but because there is nothing there to match. Three obligations follow.

**1. Forward application deposits a predicted moment.** Applying `causes(A, B)` at `M3` mints a moment
whose predecessor is `M3` and whose licence is *R applied, predicted*, carrying `B`'s entries, plus a
due-time derived from §11's timing member. Without the deposit there is nothing to be surprised
against.

Note what this avoids: a bespoke relation like `expected(+boiling(w), by t+7)` is not writable in this
vocabulary at all, because it puts a **sign inside a proposition**, and a sign is a member of an
entry. The moment form is not a workaround for that restriction — it is better, because it makes
surprise a **comparison of two moments**, which is an operation the design already needs.

**2. The continuation is a moment.** What the agent is doing, where it is in it, and what it is
waiting for are signed entries — not a stack frame.

*Stack frame* here means the interpreter's: opaque, owned by the runtime, and unreachable by a rule.
§13's frames are the opposite of that in every respect — process nodes, readable, writable, and
selectable — which is why they can be preempted and an interpreter's cannot. The word is unfortunate;
the distinction is the whole of §16.

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
point either receives a meta-answer or falls through to the total table (§14), so no decision hangs.
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

## 17. Acceptance

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

Over a recursive shape (§9) the property cannot be run to exhaustion, so it is run per instance to a
depth. That is a weaker gate, and it is the price of being able to state the shape at all.

Secondary gates, each following from a requirement:

* **R2** — for any conclusion, the agent can say whether it was reached forwards or backwards.
* **R5** — every entry in the graph has a licence and a source, and no entry has a stamp the gate did
  not set.
* **R6** — *the level rises by an unknown amount* is expressible, and reading the level afterwards
  reports ignorance rather than the old value.
* **R7** — a procedure in progress can be preempted by a surprise without any interrupt mechanism,
  and afterwards the agent can say why it stopped.

Three more follow from §13, and they are the ones a first implementation is most likely to get wrong:

* **Two indices.** After revising a belief about an earlier moment, *what do I now think about `M7`?*
  and *what did I think at `M7`?* both answer, and answer differently.
* **Containment.** Nothing concluded inside a supposition is readable as current belief. The only way
  a scenario's content reaches the agent's own seat is an explicit write whose proposition is about
  the scenario.
* **No laundering.** For every derived entry, its grade is no stronger than the weakest grade among
  the entries match consumed — checkable directly over the trail, without running anything.

---

## 18. What this design does not settle

* **Cardinality in backward matching.** §9 says where a count lives — a fact about a group node, not a
  relation position. What is unsettled is how a backward reader *uses* one: unifying a wanted fact
  against a group of unknown size needs cardinality declared per relation position, alongside arity and
  whether the position is ordered.
* **Shape equivalence** (§9). Undecidable in general, so *are these two definitions the same shape* has
  no answer and duplicate shapes will accumulate undetected. What is open is whether a decidable
  fragment is worth carving out for the shapes that fall inside it.
* **Structure against claims** (§8). An antecedent carries two kinds of member and nothing structurally
  stops an author writing a claim where a skeleton constraint belongs, or the reverse. The distinction
  is stated and unenforced.
* **Distribution** (§9). *Each file was copied* against *the files together filled the disk* is a fact
  about the entry, but which entries need it, and what a read that does not ask for it should return,
  is not specified.
* **Constrained-not-bound values.** *The level rises by an unknown amount* wants a value member that
  is constrained rather than bound. Note the boundary §7 draws: **recognising** an ongoing pattern
  does not need this — a span superseded by a longer span is ordinary versioning — only **predicting
  that it continues** wants an unbound endpoint.
* **Consistency within a moment** (§5). Two entries with opposite signs in one locus is permitted and
  undetected. That is the right default, since consistency is a question rather than an invariant, but
  the design does not say who asks it or when.
* **Span normalisation** (§7). Equality of span content must be normalised by chain order rather than
  member order; the normalisation is not specified.
* **Resolving calendar terms.** §11 settles that calendar terms denote and the chain orders, so
  *afternoon* names a stretch resolved against the clock. What is unsettled is the resolution itself —
  who computes it, against whose clock, and what happens when a term denotes a stretch the chain does
  not reach, as *next Tuesday* does.
* **Negation versus a false value.** *The stove is not lit* and *the stove has the attribute lit,
  false* are both expressible and mean different things — a claim about the moment versus a claim
  about the stove. Nothing guides the choice, and nothing detects the two being used interchangeably
  within one corpus.
* **Enforcing the gate** (§13). *No write bypasses the stamp* is a property of one place rather than a
  prohibition on rules, which makes it checkable — but the check is not written, and until it is,
  §12's soundness argument rests on the gate having no second door.
* **Seat discipline across processes** (§13). Frames form a forest and any of them may be in focus.
  Nothing says whether two processes may hold seats in the same moment at once, what it means if they
  do, or whether one process may move another's seat.
* **When a revision is warranted** (§4). The two indices make *I now think otherwise about `M7`*
  sayable, and say nothing about when an agent should write one. Left alone, a system that revises the
  past freely can rewrite its way out of any surprise, which is §16's mechanism defeated by §4's
  permission.
* **Evidence accumulation** (§12). Counting over episodes, with no arithmetic on grades. The counting
  scheme is unspecified.
* **Familiarity** (§15). The escalation trigger needs *have I seen moments like this?*, which is a
  measure over the episode record and is not the same as *did recall return anything*.
* **The exploration schedule** (§15). When the exhaustive pass fires in the absence of an impasse.
  What is open is the *rate*, not the requirement; without one, recall calcifies silently.

---

## Appendix A. Glossary

| term | definition |
|---|---|
| **anchored** | of a moment: has individuals and a predecessor in the history. The opposite of *generic*. |
| **arbitrate** | choose one rule among those that matched. Total, table-driven, always answers. |
| **channel** | the intake path an entry arrived through. Mechanically observed, so it cannot be wrong. Distinct from *authority*, which can. |
| **connective** | `implies` or `causes`; the relation between a rule's two moments. |
| **deposit** | the moment whose delta an entry sits in — when the claim was made. Distinct from *locus*, which is what it is about. |
| **entry** | a node with three members — locus, proposition, sign. The unit of assertion. |
| **frame** | a reasoning in progress, as a process node. Carries a *seat* and a *topic*. Frames form a forest, not a stack. |
| **gate** | the write primitive, considered as the one place a stamp is applied. No write bypasses it. |
| **generic** | of a moment: has variables and no *anchored* predecessor. May have a generic one, so a pattern is a chain. A rule's two members are generic. |
| **grade** | an ordinal modality on an entry: certain, likely, possible, unlikely, unknown. |
| **group** | a node standing for a plurality. Its membership is not stored; its size is a fact about it. |
| **licence** | the node that says what authorised a moment's delta, or what produced an entry. |
| **locus** | an entry's first member: the moment or span the claim is about. |
| **match** | unify a generic chain against an anchored one, recording which entries matched. |
| **moment** | a signed delta, a predecessor and a licence. The only state construct. |
| **proposition** | a relation instance. Claims nothing until an entry places it. |
| **recall** | propose which rules come to mind. Learned; never complete. |
| **rule** | a fact whose two members are generic, related by a connective. |
| **seat** | a frame's first part: the moment its writes are deposited in. Where the reasoning is standing. |
| **shape** | a pattern of indefinite extent, defined by recursive rules over spans. A node, so bounds and provenance attach to it. |
| **sign** | `+`, `−`, `?`, or the absence of an entry. See §6. |
| **skeleton** | the part of an antecedent that relates its variable loci — succession, span endpoints, distinctness. Carries no sign, and claims nothing. |
| **span** | a node with two members, a start and an end moment. A locus for trajectory claims. |
| **topic** | a frame's second part: the locus its writes are stamped with. Equals the seat except when reasoning about another time. |
| **write** | mint signed entries. The gate; stamps locus, deposit, licence and source. |

## Appendix B. Alternatives considered

Each was scored in the section named; this table is the index.

| decision | rejected alternative | why |
|---|---|---|
| rule form (§8) | guard plus a program body | the backward reading is a hypothesis wearing entailment's clothes with nowhere to record it; and a program has no subject, so nothing can be said about the rule |
| rule form (§8) | one rule per direction | two statements drift, neither is the other's premise, and the disagreement is undetectable |
| assertion (§5) | truth as a value on the proposition node | minting a node in order to deny it asserts it; correction overwrites the record it corrects |
| timing (§11) | a third member of the connective | the connective's arity varies, an absent delay silently defaults, and two sources cannot disagree |
| timing, modality (§10, §12) | fused connectives such as `likely_causes` | fuses strength with defeasibility and records neither; the name set grows multiplicatively |
| modality (§12) | grade on the proposition node | *likely* said of no occasion and every occasion at once, and a cache of a derived value — which is a truth-maintenance system |
| modality (§12) | confidence as a grade on the rule | the same question is asked of sensors and speakers, so it belongs on the source; a rule slot covers one case and is reinvented for the rest |
| belief (§4) | a belief-set node beside the moment chain | a moment already is one; a second membership structure for beliefs is a second ordering beside succession |
| entries (§13) | only the machinery may write entries | stronger than the requirement, which is that no write bypasses the stamp; it forbids honest past-directed claims and pushes trust into hard-wired intake |
| frames (§13) | a stack of frames | two hypotheses under comparison are siblings, both alive, neither the caller of the other |
| frames (§13) | copy conclusions out of a frame, re-qualified | one fact in two shapes, and it needs invalidation the moment the supposition is discharged differently |
| modality (§12) | a guard node per uncertain fact | optional guards mean two shapes for every consumer; mandatory guards mean a node and a hop per certain fact |
| modality (§12) | probabilities instead of ordinal grades | independence assumptions cannot be stated in the graph, so the product looks like a measurement and is an artefact |
| entries (§13) | augment rules to speak of entries | cannot be written: the locus is an indexical, and a rule is generic |
| entries (§13) | authors write entries natively | every rule becomes plumbing, and provenance becomes forgeable |
| the floor (§14) | connectives implemented in the engine | engine decisions have no premise and appear in no explanation; a new connective means editing the engine |
| the floor (§14) | no floor at all — rules all the way down | infinite regress; the tower never grounds |
| selection (§15) | one undifferentiated `select` step | an incomplete step reports as authoritative, and learning contends with authority for one slot |
| antecedent (§8) | a per-member achievable/given mark | achievability is relative to the planner, the deadline, the situation and the rule set, none of which the author knows; and it lets a prohibition masquerade as an impossibility |
| shapes (§9) | a reserved grammar with counters | it buys decidable equivalence and then spends it on back-references, cross-element constraints and `unless`; and a production has no subject, so it cannot be overridden |
| shapes (§9) | a counter as a member of the recursion | a count in positional clothing; an absent counter defaults to something nobody stated, and bounded and unbounded become different predicates |
| shapes (§9) | materialise a witness sequence | states a length nobody claimed |
| span (§7) | enumerate a span's moments | two answers to what the span contains; arity varies with duration |
| surprise (§16) | an interrupt mechanism in the interpreter | what is interrupted must be a selectable rule, or preemption cannot be represented, explained or overridden |

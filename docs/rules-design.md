# Rules — design

**Status: a design, not a description of the engine.** Where it disagrees with what is built, the
engine has not been changed yet. The reasoning trail, including the alternatives that were scored and
rejected and the drafts that were corrected, is in [rules.md](rules.md); the worked examples that
found several of the corrections are in [rules-worked.md](rules-worked.md). This document states the
design in the order the concepts depend on each other.

## Contents

1. [The problem](#1-the-problem)
2. [Moments](#2-moments) — the one state construct
3. [Propositions and entries](#3-propositions-and-entries) — how anything is claimed
4. [Signs](#4-signs) — what an entry can say
5. [Spans](#5-spans) — claims whose subject is a stretch of chain
6. [Rules](#6-rules) — a fact relating two moments
7. [Connectives](#7-connectives) — `implies` and `causes`, and why only those two
8. [Time](#8-time)
9. [Modality](#9-modality)
10. [The division of labour](#10-the-division-of-labour) — rules speak of propositions, machinery of entries
11. [The engine floor](#11-the-engine-floor) — recall, match, write, arbitrate
12. [Recall](#12-recall) — where experience lives
13. [Surprise, commitment and reflection](#13-surprise-commitment-and-reflection)
14. [Acceptance](#14-acceptance)
15. [Open questions](#15-open-questions)

Terms are introduced in order: nothing in a section depends on a section below it, except that §2
forward-references entries (defined in §3) as the content of a moment.

---

## 1. The problem

[passes.md](passes.md) drafted a rule as `guard → MINT/LINK program`. Planning must read a rule
**backwards** (*what would make this goal true?*) and execution must read it **forwards** (*what
follows from this state?*). A program body supports only the second, for three reasons:

1. **A program is not a description of what becomes true.** Answering *what would make `is_a(?x,
   car)` hold?* would mean symbolically executing every body. Operations-as-data is write-only: data
   you can run, not data you can ask about.
2. **`MINT` has no backward unifier.** A wanted fact cannot unify against a node that does not exist
   yet, unless minting is keyed by the left-hand binding.
3. **Backward reading is the converse, and the converse is a leak.** *Four wheels ⇒ car* run
   backwards licenses *a cart is a car*. That is legitimate as abduction and catastrophic if a
   planner mistakes it for entailment, so *which reading this is* must be recoverable — and a
   program body has nowhere to record it.

Authoring one rule per direction is worse than either: two statements drift, neither is the premise
of the other, and the disagreement is undetectable. The design therefore keeps **one statement with
two readings**, which is also what makes the acceptance check of §14 possible at all.

The whole design in five lines:

> A rule is a **fact relating two moments**. Direction is a *query* over it, never a field in it.
> Time and possibility are **members**, never connectives. A hub is a **proposition** and an **entry**
> is the assertion, so modality and recognition live on the entry — dated and superseded — never on
> the node, where they would need invalidating. **Rules speak of propositions and never of entries**;
> the machinery supplies what only the application knows. The engine's floor is **four primitives** —
> recall, match, write, arbitrate — of which only the last is complete.

---

## 2. Moments

*Frame*, *moment*, *hypothesis* and *imagined state* are **one construct**. A moment has three parts
and nothing else:

```
<M> = a signed delta   +  a predecessor        +  what licensed the difference
      (entries, §3)       (an edge to another M)   (an edge to a node)
```

Only the third edge varies:

| reading | predecessor | the licence says |
|---|---|---|
| a moment in **time** | the previous moment | *an event happened* |
| an **imagined state** | the previous imagined state | *I applied this rule in supposition* |
| an **assumption** | where I was standing | *I decided to suppose this* |
| a rule's antecedent or consequent | **none** | — |

### Anchored and generic

The distinction that carries weight is not frame-versus-moment but:

* an **anchored** moment has individuals and a predecessor;
* a **generic** moment has variables and no predecessor.

A rule's two members are generic; everything else is anchored. The distinction is structural, so it
is checkable rather than maintained by discipline, and it makes the first engine primitive precise:

> **`match` is: unify a generic moment against an anchored one.**

Nested supposition needs no mechanism: **nesting is a path in the predecessor tree**, which is what
sparse frames already are.

### Two of the five orders share a core

`next` (derivation over frames) and `before` (time over moments) are recorded in
[HANDOFF.md](HANDOFF.md) as two of the unrelated orders. Under one construct they are **one relation
with two licences**: succession is the shared core, time adds a clock stamp above it, derivation adds
a licensing rule above it.

This is the sanctioned relaxation, not the forbidden collapse: the standing rule is that orders *may*
share a core provided it is literally the same nodes and each adds modality, a scalar or a derivation
above it. The invariant that must survive is that **supposing takes no time** — a derivation step is
succession without duration, so the shared core must not itself carry a clock.

---

## 3. Propositions and entries

A hub is a **proposition**; it claims nothing. The **entry** is the claim.

```
<e> = entry(<M7>, <f>, +)          members: locus, proposition, sign
licensed_by(<e>, <application>)    grade(<e>, likely)    said_by(<e>, anna)
```

An entry is an ordinary hub whose relation happens to be `entry` — no new construct.

**Why two levels are forced.** To say *`on(a, b)` is false in M12* you must be able to point at
`on(a, b)`, so the proposition must exist in order to be denied. If the hub were itself the
assertion, minting a negation would assert its positive. Two levels are what negation costs; in
exchange, nothing has to remember that a bare hub means nothing.

**Where the regress stops.** An entry is a fact — does it need its own entry? No: **an entry names
its locus, so it is located by being one.** A proposition needs an entry to be placed; an entry places
itself.

**Exactly three members: locus, proposition, sign.** Grade, licence, speaker and clock stamp are
facts *about* the entry, never a fourth member — the same discipline that keeps `causes` binary with
`timing` as an adjunct. Without it the entry becomes an n-ary node with a bag of optional slots.

### What the two levels buy

The world changing and my having been wrong become **different operations**:

| | what happened | how it is written |
|---|---|---|
| they stopped being on each other | the world moved | a **new entry**, opposite sign, later locus |
| I was mistaken that they ever were | my record was wrong | a **fact about the old entry** — same locus, unchanged |

Under a value stored on the node these are indistinguishable — both are *change it* — which is how a
system quietly rewrites its own history.

### Cost

`entry` is a member of the **closed class**: resolving a read means *walk the predecessor chain for
entries naming this proposition*, so the engine dispatches on it. That is the one mechanism §2
already counts, not a new one, and it should be declared the way `precedence.STAGES` declares itself.

Two entries in one locus with opposite signs is a contradiction the shape permits and does not
detect. That is correct — consistency is a **question you ask**, not a substrate invariant — but it
makes *is this moment consistent?* somebody's job (§15).

---

## 4. Signs

An entry's sign means different things in an anchored and a generic moment, because a generic moment
has no predecessor to inherit from.

| sign | in an **anchored** moment | in a **generic** moment |
|---|---|---|
| `+` | holds here | must hold |
| `−` | does not hold here | must not hold |
| `?` | **held before, does not now, and I cannot say what does** | — |
| *no entry* | **unchanged — inherit from the predecessor** | don't care / unknown |

**No entry means inherit, not unknown.** The chain walk continues past a moment with no entry and
finds an older one. This is why `?` exists as a distinct sign: *the volume changes, I cannot say to
what* cannot be written by writing nothing, because writing nothing returns the old volume — the one
thing the operator was trying to say would be the one thing unsayable. `?` invalidates without
replacing.

The generic `?` (don't care) and the anchored `?` (invalidated, unknown) are different claims. They
share a symbol because the anchored/generic split disambiguates them structurally, but they are not
the same thing.

---

## 5. Spans

Some claims are not true *of a moment*. `taking_turns(anna, bo)` has as its subject a **stretch of
the chain** — [limits.md](limits.md)'s *"a sequencing constraint's subject is a path through worlds
rather than a world."*

A span is a node with **exactly two members**:

```
<s> = span(<M7>, <M12>)                        position 0 = start, position 1 = end
<e> = entry(<s>, taking_turns(anna, bo), +)    licensed by the recogniser, over the trajectory
```

**Membership is not stored, for a structural reason: predecessor is single-valued.** A moment has one
parent; forking yields several *successors*, never several parents. The walk back from `M12` is
therefore unique, and if `M7` lies on it the contents are fully determined. Enumerating the moments
between would store what the chain already answers — and would give two answers to *what is in this
span*, which is the leak.

**Two things stay out of the span.** The **participants**: `anna` and `bo` are members of the
proposition, never of the span, which is what lets one span host several recognitions (*they took
turns* and *it rained throughout*). And **disjunction**: *"on Monday and on Wednesday"* is two spans
plus a fact relating them, never one span with a hole — otherwise disjunction is smuggled into the
substrate where nothing can consume it.

**Recognition and prescription are one predicate read two ways**: a **generic** span with variables
is a constraint you are planning to satisfy; an **anchored** span is a recognition that it held. That
is §2's anchored/generic split, one level up. See [advice-over-sequences.md](advice-over-sequences.md)
§3.

**Costs.** The span is directional, so content-equality must normalise by chain order, not member
order. Spans are **minted by recognisers, never enumerated** — any two moments form one, so the
population is quadratic. And nothing checks that `M7` is an ancestor of `M12`, so the check belongs
**at the minting site**, where it is cheap and where the violation is still detectable.

---

## 6. Rules

A rule is a fact whose two members are moments:

```
<R> = causes( <A>, <B> )
```

`<A>` is generic. `<B>` is signed *relative to* `<A>`, which makes it a delta without being a second
kind of object. Everything else is an ordinary fact **about** `<R>` — possible only because `<R>` is
a node:

```
by(R, boss)        overrides(R, R2)       about(R, assembly)
timing(R, end→start, [4min, 7min])        unless(R, +altitude(?w, high))
```

### The three readings

| | |
|---|---|
| **forward** | match `<A>`; apply `<B>`'s signs into a successor moment |
| **backward** | unify a wanted fact against `<B>`'s `+`/`−` entries; `<A>`'s achievable members become subgoals |
| **`?` entries** | backward, *this rule disturbs position and cannot say how* — a **want**, not a failure, and not a false *it stays put* |

### Antecedent members are not alike

A flat guard is unusable backwards. *To unbolt it, it must be on the bench — and you may put it
there; it must be a Tuesday, and you may not make it one.* Each antecedent member therefore carries
one mark:

* `+` **achievable** — backward, this becomes a subgoal
* `~` **given** — backward, this may only be *tested*

Without the distinction a backward reader plans to make it Tuesday, and a forward reader notices no
difference at all.

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

---

## 7. Connectives

| layer | closed set | size |
|---|---|---|
| connective | `implies`, `causes` | **2** |
| entry sign | `+`, `−`, `?`, no entry | 4 |
| antecedent mark | achievable, given | 2 |
| grade | `certain > likely > possible > unlikely > ?` | ordinal, ~5 |
| timing | one relation over the two moments' endpoints | 1 |

Everything else — `heat`, `cloudy`, `boss`, `overrides`, `by`, `about` — is open-class vocabulary and
reserves nothing.

### The membership test

> **A connective earns its place only if it licenses a different (forward, backward) reading pair.**

If two candidates read the same, they are one connective and the difference belongs in a member. The
test shrinks the set:

* `prevents(A, B)` = `causes(A, {−B})`. Consequents are signed, so prevention is already sayable.
* `enables(A, B)` = `causes(A, {+B @possible})`. Backward, the reader distinguishes them by grade:
  `certain` → doing `A` achieves `B`; `possible` → `A` is a precondition and something else must
  still happen.

### Why `implies` and `causes` do not collapse

Not *one is logical, one is worldly*. The test is mechanical:

> **Retract the antecedent. Does the consequent go with it?**
> Yes → `implies`. The entry is **derived** and lands in the **same** moment.
> No → `causes`. The entry is **asserted**, persists, and lands in a **later** moment.

Water you stopped heating stays boiled. That is inertia, and it is why a zero-delay cause is still not
an implication: you cannot merge the two by setting the delay to zero.

`<R2>` above is the argument for keeping both. The persistence test says `implies` — learn it was not
cloudy and the rain claim goes with it — but the surface wording reads as causal, and clouds do not
cause the afternoon's rain; a front causes both. Written as `causes`, the backward reader produces **a
plan to make it rain by making it cloudy**. The two-connective split is what makes that plan
unwritable.

Allen relations (`before`, `during`, `overlaps`) are **not** connectives. They are ordinary facts
about moments, which are already nodes.

---

## 8. Time

**An action is not a new kind of thing.** An action is an event, an event is a moment, and
`heat(?a, ?w)` is a fact holding over an interval. An action enters the antecedent as an ordinary
member, and *execute* means **make this event-fact true**. There is no action construct and no
operator table beside the rules.

*"…causes it to boil in 5 minutes"* takes three decisions:

1. **Say which endpoints.** *The heating takes 5 minutes* / *boiling starts 5 minutes after heating
   starts* / *5 minutes after it stops* are three different rules that plan differently. The timing
   member relates named endpoints — `end(A) → start(B)` — never a bare scalar.
2. **It is a constraint, not a number.** `[4min, 7min]`, `≥5min`, *eventually* and *unknown* must all
   be sayable, or precision-by-silence returns. Absent timing means unknown timing, and that is legal
   and readable.
3. **It is a fact *about* the rule, not a third member of `causes`.** That keeps the connective
   binary, lets the delay be genuinely absent, and lets two timing claims coexist with different
   sources — *the manual says 5, I measured 7* — which is real and unsayable if the delay is a slot.

Timing is read in both directions: **forward** it says when to expect the effect, and therefore when
its absence counts as a **deviation** rather than as patience (§13); **backward** it is a **filter** —
needing boiling water in two minutes rules this rule out. A delay-less rule expresses neither.

---

## 9. Modality

Three different things get called *possibility*, and they must not share a slot:

| | what it is | where it goes |
|---|---|---|
| **strength** | how often the effect actually follows | grade on the **entry** |
| **confidence** | how sure I am of the rule | grade on the **rule**; moves with evidence |
| **defeasibility** | what would cancel it | **not a number** — a relation to other rules (`unless`, `overrides`) |

Collapsed into one number, `0.6` means three things at once and combining them is arithmetic
nonsense. Defeasibility is the load-bearing one for reasoning — *unless the front has already
passed* — and it needs **no numeric apparatus at all**: it is the same precedence machinery as
boss-beats-vice.

**Per-entry, not per-rule.** One rule has consequences of different strength: heating boils the water
(certain) and scorches the pan (unlikely). A rule-level grade is shorthand for *all entries the same*.

**Ordinal, not probabilistic.** Real probabilities need independence assumptions that cannot be
stated in the graph, so multiplying leaks silently. Ordinal grades compose by **weakest link**. A
numeric member may sit *beside* the grade when its own provenance is a member (*"from 300
observations"*), never in place of it. The honest cost: two independent *likely*s ought to be more
than *likely*, and `min` says they are not. Ordinal grades do not accumulate evidence; the right fix
is **counting over episodes**, not arithmetic over grades (§15).

Grade is orthogonal to `?`. `?volume` is *changes, magnitude unknown*; `+rain @possible` is *might
become true*. Different ignorance, different slot.

### Why the grade lives on the entry

Not because tagging every node is expensive:

> A grade stored on a **fact node** is a cache of a derived value. `rain @likely` holds only given the
> support that produced it, so when the support changes the tag must be invalidated — and invalidation
> over a dependency web is a **TMS**, deleted twice here and declined again. The standing line applies
> verbatim: **an index over what was asserted is storage; a cache of what was derived is a TMS.**

A second, independent reason: **a tag is ignorable.** Reading a fact and reading its grade are two
reads, so a consumer that forgets produces a conclusion with no grade at all — the leak criterion
failing by discipline where the edges-as-nodes arc bought structure.

Every fact already has a provenance node — the entry of §3 — so put the grade there:

| the fact came from | the node that already exists | carries |
|---|---|---|
| a rule applying | the application / transformation | the rule's per-entry grade |
| someone saying so | the utterance (speaker, authority) | how firmly they said it |
| observing | the sighting | sensor confidence |
| an assumption | the moment's licence | the grade of what was supposed |

The entry had to exist anyway — the **sign** has nowhere else to live, since edges carry no facts —
so the grade slot costs nothing.

### Superseded, not invalidated

If a stored grade is a cache, is a stored derived *fact* not also one? No:

> **A dated derived fact needs no invalidation.** At M7 you recognised taking-turns; at M12 something
> writes `−taking_turns(a, b)`. The M7 entry stays true **of M7**. Nothing is retracted, nothing
> propagates, and *are they taking turns?* resolves through the chain to the most recent entry.

One line covers modality and recognition together:

> **Store on the entry — dated, signed, attributed, superseded.
> Never on the node — timeless, and therefore requiring invalidation.**

### Moments and grades solve different problems

| | *"I am supposing this — what follows?"* | *"this generally holds, weakly"* |
|---|---|---|
| shape | a **moment** you enter and leave (§2) | a **grade**, recorded on the entry at application |
| count | few, deliberate, **nested** | many, independent |
| nesting | free — a path in the predecessor tree | does not nest; composes by weakest link |
| crossing | **already mandatory** — a read cannot reach into a moment except through the chain | not a crossing at all |

Keeping them apart is what avoids the ATMS this project deleted: twenty independently-uncertain facts
would be 2²⁰ moments. **Use moments where you choose to suppose; use grades where the world is merely
weakly connected.**

### Forcing the handling

A computed grade compels nothing, and *don't act on a merely-possible fact without acknowledging it*
is a real requirement. It belongs at **the one place effects leave** — check the grade of what
licenses an **action** at the dispatch door, where the set is small and known, rather than making a
million reads cross a guard to catch the one that matters. This is the same placement as prohibitions
in §12.

### What this costs

* *How likely* becomes a **walk, not a read** — the same shape as `holds`, already measured and
  accepted at 2.35×.
* **The residue becomes load-bearing for correctness, not only for explanation.** A write that loses
  its attribution does not merely become unexplainable, it becomes **falsely confident**, because a
  missing support link removes a weak link from the `min`. That promotes `ugm.leak`'s invariant from
  hygiene to soundness.
* Cycles in the support chain need the same termination care as any derivation walk.

### Do we run out of dimensions?

The dimensions actually spent, in the whole system:

| | why it cannot be structure |
|---|---|
| **identity** | *this node is that node* is not a relation between two things; it is the precondition for there being things |
| **connection** | an edge |
| **order among connections** | *the 2nd member* — position is not a thing in the world, so it cannot be a node |
| *(a mechanism, not a dimension)* | **how a read resolves** — the predecessor chain of §2, named and reachable |

Everything added since — type, sign, licence, grade, time, force, authority, span — is a **member of
a node**, and costs no dimension.

> **You run out of dimensions only if you try to say something that is not about anything.**

If a candidate can be phrased as *X stands in relation R to Y* it is structure. **Order is the one
that genuinely could not**, which is why the substrate has ordered targets and why `step[i+1]`
remains hard.

---

## 10. The division of labour

If everything is asserted through entries, are business rules **augmented** to mention them, or does
the **machinery** apply them to entries? The machinery.

### Augmentation cannot be written

```
+on(a, b)      ⟶      entry( <the moment I am in> , on(a, b), + )
                             ^^^^^^^^^^^^^^^^^^^^
```

**The locus is an indexical.** A rule is generic (§2: variables, no predecessor); an entry is
anchored. A rule that named a locus would be about that occasion and could not be reused. So
augmentation can only produce an entry with a hole — and **a hole the machinery fills at run time is
the machinery doing it.** It buys nothing and costs four things:

1. **It is a translation, and translations must commute.** Every `why` would show the rewrite rather
   than the rule the author wrote. The residue is the claim, so this is the expensive loss.
2. **One fact in two shapes.** Authored and augmented need syncing, and `why` must un-augment to
   answer — the recorded blocker on every swap this project has done.
3. **It freezes the resolution policy into every rule.** The property being bought is *the machinery
   can change what a read means without editing a single rule*; augment, and a policy change means
   re-augmenting the corpus.
4. Every rule triples in size in plumbing, so *which rules are about time?* gets harder.

This is not a new decision. The mediated-access arc faced it one level down and answered it the same
way: a rule names the identity, the ambient context resolves it, and `slot_of` inside a frame reads
that frame's version without `holds.mf` containing one word about frames.

### The split

| the rule says | `match` / `write` supply |
|---|---|
| `+on(?x, ?y)` in `<A>` | walk the chain for entries naming that proposition; return those signed `+` |
| `+boiling(?w)` in `<B>` | mint the entry in the successor moment; stamp locus, licence and grade from the application |

> **The rule's members are what the author knows. The entry's members are what the application
> knows.**

Locus, licence, speaker and grade-at-this-application do not exist until the rule runs. That is why
`entry` is a member of the closed class rather than vocabulary an author writes.

### The asymmetry that must be enforced

`entry` is both a mechanism and a node a rule can point at, and that is safe in one direction only:

> **Rules may READ entries. Only the machinery may WRITE them.**

Reading is how *"a claim Anna made outranks one Bo made"* gets written at all — an ordinary rule
*about* entries. Writing is how a rule would forge provenance: an entry licensed by nothing, or one
backdated into an earlier locus. Because §9 makes the residue load-bearing for soundness, a rule that
could mint entries directly could raise its own confidence by writing one unlicensed entry. So
`write` is the only minter, and it **stamps** the licence from the current application rather than
accepting one as an argument.

**Costs.** A bug in `write` is systemic — every fact gets the same wrong provenance — mitigated by it
being one place, hence one check. `match` becomes a chain walk rather than a lookup, and now sits on
the rule-matching path rather than only on reads. And `match` **must record which entries it
matched**, or *"because `on(a,b)` held, on Anna's word"* has no answer; that is half the residue, and
it is what makes a misbehaving rule distinguishable from a misresolving chain.

---

## 11. The engine floor

If `causes`' meaning is given by rules, and those rules use connectives whose meaning is given by
rules, the tower never grounds. **The closed class cannot be empty.** What it can be is *not the
connectives*:

1. **recall** — which rules come to mind here. **Never complete**, by design (§12).
2. **match** — unify a **generic** moment against an **anchored** one, over what recall offered. It
   records which entries it matched (§10).
3. **write** — mint signed entries into a moment. **The only minter of entries**; it stamps the
   licence from the current application.
4. **arbitrate** — among the rules that matched, pick one. **Total**, table-driven, always answers.

**Recall proposes, match filters, arbitrate commits. Only the last is total.**

The fourth is the one that is easy to get wrong. A meta-rule deciding which rule to apply must itself
be selected, and that regress happens *at run time*. **The bottom-most arbitrator is a lookup over an
authored precedence table that always returns and never searches.** Reflection may be arbitrarily
deep; the final tiebreak may not be reflective. That is the stratification condition, and it is the
same one [reflection.md](reflection.md)'s *last stage must be total* already names.

### A connective is a table entry, not a branch

```
<F> = causes( { +rule(?r), +conn(?r, causes), +matches(?s, ant(?r)) },
              { +succ(?s, ?s'), +applied(?r, ?s, ?s') } )

<B> = causes( { +want(?f), +conn(?r, causes), +member(+?f, con(?r)) },
              { +candidate(?r, ?f) } )
```

`matches` is primitive; everything above it is data.

> **The test that the floor is in the right place: adding a connective adds rows, not branches.**

If a new connective requires touching the engine, the connective set is not data and §7's budget is
fiction.

**One interpreter, or none of this counts.** Meta-rules buy nothing if a Python loop special-cases
them. The interpreter's step is *select a rule, apply it*, and object-rules and meta-rules are
indistinguishable to it — a flat tower, not a stacked one. If you cannot answer *which level am I
on?*, that is the sign it is right.

---

## 12. Recall

> *"It doesn't offer any guarantee of finding all applicable rules — that would be computationally
> too heavy — but I think that's where experience lies: the right rules come to my mind at the
> correct moment."*

Recall, match and arbitration have **opposite requirements**, which is why they are separate
primitives:

| | **recall** | **match** | **arbitrate** |
|---|---|---|---|
| job | which rules come to mind | do they actually fit | which one now |
| complete? | **never**, by design | over what recall offered | over what matched |
| total? | — | — | **must always answer** |
| authored or learned? | **learned** | mechanical | **authored** (precedence) |
| failure mode | a rule you needed never surfaced | — | dithering, or a hang |
| cost of being wrong | recoverable — a worse plan, or a surprise later | — | a wrong action |

### Why experience belongs in recall specifically

1. **It is the only step where being wrong is recoverable.** A missed rule costs a worse plan or a
   later surprise, both of which the machinery already handles. A wrong arbitration costs a wrong
   *action*. Put learning where errors are survivable.
2. **It is the only step with no authored ground truth.** *Which rules should have come to mind?* has
   no answer but *the ones that turned out to matter*. Arbitration has the opposite property —
   `by(R, boss)` and `overrides(R1, R2)` **are** the ground truth, and learning them would be wrong.

### What incompleteness costs immediately

Once recall may miss, **"no rule applies" is ambiguous**: nothing applies, or nothing came to mind.
That is §4's present / absent / no-entry discipline landing on the machinery that reads it. **Recall
returns a set plus a state, never a set.** The state is cheap to compute from the wrong thing (*did I
find anything?*) and expensive from the right one (**is this situation familiar?**) —
unfamiliar-and-empty is a different event from familiar-and-empty, and only the first should
escalate.

### What recall is keyed by

Not the situation alone — **the situation *and* the active goal**. The same world brings different
rules to mind depending on what is being attempted; a recall keyed only on world features surfaces
the same set forever regardless of intent.

[passes.md](passes.md):50 already has the mechanism — *"the engine shall maintain an index (a web) of
what passes are linked to others, the connective is the same terms"* — filed under **optimization**.
It is not an optimization: spreading activation over the shared-member web **is** the recall
substrate.

### System 2 is not a second mechanism

It is **recall with the budget removed** — same match, same arbitrate, exhaustive proposal. The
fast/slow split needs no architectural fork: a budget parameter, and an escalation rule that is *a
rule*:

```
<E> = causes( { +decision_point(?d), +recalled(?d, ∅), ~familiar(?s) },
              { +goal(exhaustive_recall(?d)) } )
```

The escalation triggers are exactly the impasses — nothing came to mind, what came to mind conflicts
irreducibly, or what came to mind was **surprising** (§13).

### What trains it, and the trap

The signal is already deposited: `applied(R, s, s')`, plus whatever explanation a surprise produced.
Recall learns from its own outputs that survived — chunking. Chunking has one failure that must be
designed against rather than discovered:

> **Training recall on its own accepted outputs narrows it monotonically.** A rule that never
> surfaces is never applied, never reinforced, and becomes permanently invisible.

The exhaustive pass is therefore **not a fallback — it is the only thing that injects candidates
recall would never have produced**, so it must fire on novelty or on a schedule, not only on impasse.
Otherwise the system calcifies precisely in the domains where it is doing well, and nothing reports
it.

### The carve-out

> **Recall may be incomplete about what to do. It may not be incomplete about what you must not do.**

A prohibition that fails to come to mind is a forbidden act that nothing notices. The repair is not
*make recall complete for norms*; it is to take prohibitions off the recall path entirely: check them
at **write**, indexed by the entries about to be written. That set is small and known, so the check is
cheap and exhaustive. **A prohibition is a gate on application, not a competitor in recall.**

### Price

Three residues per decision instead of one — recalled, matched, rejected — and recall's index must be
rebuilt as episodes accumulate. The second is the real cost, and per the standing line it is a
**rebuild from the episode record, never a patch of the previous index**.

---

## 13. Surprise, commitment and reflection

> **Surprise is a match.** It is an *expected* entry and an *observed* entry that disagree.

That is the whole mechanism, and it names the real cost of machinery written in Python: not opacity,
not speed, but that **the agent's own state is not in the world it reasons about**. An expectation
held in a local variable is unmatched not because the rule is weak but because there is nothing there
to match. Three obligations follow.

**1. Forward application deposits a predicted moment, not a special fact.** Applying `causes(A, B)`
at `M3` mints `P1 = moment(M3, <predicted: R applied>)` carrying `B`'s entries, plus `due(P1, …)`
from §8's timing member. Without the deposit there is nothing to be surprised against. A bespoke
`expected(+boiling(w), by t+7)` relation is not writable in this vocabulary — it puts a sign inside a
proposition, and a sign is a member of an entry. The moment form is strictly better anyway: surprise
becomes a **comparison of two moments**, which `deviates` already is.

**2. The continuation is a moment.** *What I am doing, where I am in it, what I am waiting for* —
signed entries, not a stack frame.

**3. Surprise is an ordinary rule that wins on precedence:**

```
<S> = causes( { +predicted(?p, from ?m), +due(?p, by ?t), +now(?t'), after(?t', ?t),
                +deviates(?p, ?actual) },
              { +goal(explain_failure(?p)), −committed(?proc) } )
```

**There is no interrupt mechanism.** Preemption is `<S>` outranking the rule that would have continued
the procedure — possible only because *continue the procedure* was itself a selectable rule, which is
exactly what a stack frame is not.

### Procedures as data

A procedure is a committed order, which is precisely the thing that cannot be preempted mid-way: if
*to find an answer, look for causes* is a procedure, step 3 owns the agent until it returns.

> **Procedures exist, but as data that biases selection, never as control flow that owns the loop.**

`committed(?proc, step_3)` is a moment entry that raises the precedence of continuing; it does not
remove the alternatives. Commitment is real (the agent does not dither), it stays preemptable
(surprise outranks it), and *dropping* it is a **write** — so the agent can be asked why it abandoned
something.

### Strategies are defeasible

```
<M> = causes( { +goal(?g, explain(?f)) },
              { +goal(find(?r)), +constraint(?r, causes(_, {+?f})) } )
```

With `overrides(M, M2)` and `unless(M, +domain(?f, social))`, **a strategy becomes defeasible like any
other claim.** A Python strategy cannot be overridden by a KB statement, and that asymmetry is the
larger cost of machinery-in-code — larger than interruptibility.

### Reflection is demanded, not continuous

Consult meta-rules only at **named decision points the interpreter already reaches** — which rule to
apply, what to do on failure, what to do on surprise — never between arbitrary steps. Each decision
point either gets a meta-answer or falls through to the total table, so no decision hangs. This is
Soar's impasse discipline; without it you pay meta-cost on every step and the tower never bottoms out
in practice.

**Price, named:** every step costs a selection, and a wrong precedence table produces dithering that
reads as a bug in the rules. Both are measurable — **selections per useful write** and **commitments
dropped per commitment made**. Build those two counters *with* the interpreter, not after it.

---

## 14. Acceptance

Not *can the system reconstruct the masked text* — that is representational, and the standing rule is
behavioural. The gate is **commutation**:

> for every rule `R` and every moment `s`: backward(`goal`) proposes `R` at `s`
> **iff** forward(`R`, `s`) yields a moment satisfying `goal`.

Run it as a property over the whole rule set. A rule where the two readings disagree is one whose
consequent is lying about what it does. The check exists *only because* there is one statement and two
readings: with one rule per direction it is untestable by construction, and with program bodies it is
undefined.

---

## 15. Open questions

* **Cardinality.** `made_of(?x, wheel×4)` is a count claim in positional clothing; backward matching
  needs cardinality declared per relation position, beside arity, ordered/unordered and converse.
* **Constrained-not-bound values.** *The level rises by an unknown amount* wants a value member
  constrained rather than bound — the same unbuilt capability as the order core. Note §5's boundary:
  **recognising an ongoing pattern does not need this** (`span(M7, M12)` superseded by `span(M7, M13)`
  is ordinary versioning); only **predicting that it continues** wants an unbound end member.
* **Consistency within a moment** (§3) — two entries with opposite signs in one locus is permitted and
  undetected. Correct, since consistency is a question rather than an invariant, but it is currently
  nobody's job.
* **Span normalisation** (§5) — content-equality must order by the chain, not by member order.
* **Speech time vs event time.** *Anna said it might rain this afternoon* has its **locus** at the
  moment of saying and its **event time** as a member of the proposition. Both are needed and both
  are right, but §8 speaks only of timing between a rule's two moments and never says a proposition
  may carry temporal members of its own. The hazard: locus-time and event-time must share the moment
  vocabulary, or they become the sixth and seventh unrelated orders.
* **Negation vs a false value.** `entry(M, lit(stove), −)` and `entry(M, attribute(stove, lit,
  false), +)` are both expressible and mean different things — *a claim about the moment* vs *a claim
  about the stove*. Nothing guides the choice, and nothing detects the two being used interchangeably
  in one corpus.
* **Enforcing the entry write-monopoly** (§10) — stated, with no mechanism. It is the same shape as
  `access.offenders`, which already measures corpus compliance with the mediated vocabulary, so the
  instrument exists and is pointed at the wrong thing. Until it is enforced, §9's soundness claim
  rests on convention.
* **Evidence accumulation** (§9) — counting over episodes, with no arithmetic on grades.
* **Familiarity** (§12) — the escalation trigger needs *have I seen moments like this?*, a measure
  over the episode record, which is not the same as *did recall return anything*.
* **The exploration schedule** (§12) — when the exhaustive pass fires absent an impasse. What is open
  is the *rate*, not the requirement; without one, recall calcifies silently.
* **Signed frame membership**, on which both readings depend, and which this design inherits as a
  prerequisite from [facts-as-nodes.md](facts-as-nodes.md).

---

## Appendix: alternatives considered

Scored per [harmony.md](harmony.md). Full scoring tables and the expressiveness pass are in
[rules.md](rules.md) §7 and §10.

| decision | rejected | why |
|---|---|---|
| rule form (§6) | guard → program | backward read is abduction in deduction's clothes, with nowhere to record that; `overrides(R1, R2)` has no subject when the rule is a program |
| rule form (§6) | one rule per direction | two statements drift; neither is the other's premise; composition is 2ⁿ |
| time, modality (§8, §9) | connectives (`likely_causes`) | fuses strength with defeasibility; *which rules are uncertain?* becomes a name census; the name set grows multiplicatively |
| grade (§9) | on the fact node | ignorable by default; a cache of a derived value, hence a TMS |
| grade (§9) | a guard node per modalised fact | optional guards mean consumers handle two shapes; mandatory guards mean a node and a hop for every certain fact |
| entries (§10) | augment rules to mention entries | cannot be written — the locus is an indexical |
| entries (§10) | authors write entry-talk natively | every rule becomes plumbing, and provenance becomes forgeable |
| the floor (§11) | connectives in the engine | engine decisions have no premise and appear in no explanation; two authors cannot add a connective |
| the floor (§11) | all rules, no floor | regress; never grounds |
| selection (§12) | one `select` step | an incomplete step reports as authoritative; *did you consider R?* is unanswerable; learning and authority contend for one slot |

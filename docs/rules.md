# Rules — one form, two readings

**Status: a design, taken fresh.** It does not describe what is built; where it disagrees with the
engine, the engine has not been changed yet. It is the answer to a question
[passes.md](passes.md) left open — *what is a rule, such that planning can read it backwards and
execution can read it forwards* — and the review findings there are its starting point.

The short version:

> A rule is a **fact relating two moments**. Direction is a *query* over it, never a field in it.
> Time and possibility are **members**, never connectives. A hub is a **proposition** and an **entry**
> is the assertion, so modality and recognition are stored on the entry — dated and superseded —
> never on the node, where they would need invalidating. **Rules speak of propositions and never of
> entries**; the machinery supplies what only the application knows. The engine's floor is **four
> primitives** — recall, match, write, arbitrate — of which **only the last is complete**; everything
> else, including what the connectives mean, is rules.

## 1. Why not a rule-shaped construct

The drafted pass form in [passes.md](passes.md) is `guard → MINT/LINK program`. Three things block
reading it backwards, and they are worth keeping written down because every "just add a rule
construct" proposal fails the same way:

1. **A program is not a description of what becomes true.** Asking *what would make `is_a(?x, car)`
   hold?* means symbolically executing every body. That is **B3** — operations-as-data is
   *write-only*: data you can run, not data you can ask about.
2. **`MINT` has no backward unifier.** A wanted fact cannot unify against a node that does not exist
   yet, unless minting is keyed by the left-hand binding.
3. **Backward *is* the converse, and the converse is the leak.** [passes.md](passes.md)'s review
   finding 1 caught this going forwards — masking teaches *four wheels ⇒ car*, and a cart has four
   wheels. Reading a rule backwards is that same converse, on purpose. Legitimate as abduction;
   catastrophic when a planner mistakes it for entailment. So *which reading this is* must be
   recoverable, and a program body has nowhere to put it.

⚠ And the obvious repair — author one rule per direction — is worse: two statements drift, neither
is the premise of the other, and the disagreement is undetectable. See §7.

## 2. The form

A rule is a fact whose two members are **moments**, in the sense of
[facts-as-nodes.md](facts-as-nodes.md) §*Frames* — signed membership, three states:
**present / absent / no entry**.

```
<R> = causes( <A>, <B> )
```

`<A>` is generic (contains variables). `<B>` is signed *relative to* `<A>`, which is what makes it a
delta without being a second kind of object. Everything else is an ordinary fact **about** `<R>`,
which is possible only because `<R>` is a node:

```
by(R, boss)        overrides(R, R2)       about(R, assembly)
timing(R, end→start, [4min, 7min])        unless(R, +altitude(?w, high))
```

Three readings fall out, and they are the whole argument:

| | |
|---|---|
| **forward** | match `<A>`; apply `<B>`'s signs into a successor moment |
| **backward** | unify a wanted fact against `<B>`'s `+`/`-` entries; `<A>`'s achievable members become subgoals |
| **no-entry** | `?position(?x)` backward means *this rule disturbs position and cannot say how* — a **want**, not a failure, and not a false *it stays put* |

### Antecedent members are not alike

⭐ A flat guard is unusable backwards. *To unbolt it, it must be on the bench — and you may put it
there; it must be a Tuesday, and you may not make it one.* Each antecedent member carries one mark:

* `+` **achievable** — backward, this becomes a subgoal
* `~` **given** — backward, this may only be *tested*

Without the distinction a backward reader will plan to make it Tuesday, and a forward reader will
not notice the difference at all.

### 2.1 ⭐⭐⭐ What a moment is — and there is no such thing as a "frame"

*Frame*, *moment*, *hypothesis*, *imagined state* are **one construct** under four names, which is the
*one relation under four names* failure this project keeps catching. Three parts, nothing else:

```
<M> = a signed delta        +  a predecessor      +  what licensed the difference
      (entries — see 2.2)      (an edge to another M)  (an edge to a node)
```

Only the third edge varies:

| reading | predecessor | the licence says |
|---|---|---|
| a moment in **time** | the previous moment | *an event happened* |
| an **imagined state** | the previous imagined state | *I applied this rule in supposition* |
| an **assumption** | where I was standing | *I decided to suppose this* |
| a rule's `<A>` / `<B>` | **none** | — |

⭐⭐⭐ **The distinction that matters is ANCHORED vs GENERIC, not frame vs moment.** A rule's two
members have **variables and no predecessor**; everything else has **individuals and a predecessor**.
That is structural, so it is checkable rather than maintained by discipline — and it makes §8's first
primitive precise:

> **`match` is: unify a generic moment against an anchored one.**

Everything previously called a frame is an anchored moment. **Nested assumptions are a path in the
predecessor tree**, which is what sparse frames already are — no nesting mechanism is owed.

⭐⭐⭐ **And this gives two of the five orders a shared core.** `next` (frames — derivation) and
`before` (moments — time) are recorded in [HANDOFF.md](HANDOFF.md) as two of the unrelated orders,
and the matrix says cause–effect and time are *exactly the pair with nothing between them*. Under one
construct they are **one relation with two licences**: succession is the shared core, time adds a
clock stamp above it, derivation adds a licensing rule above it.

⚠ This is the **sanctioned** relaxation, not the forbidden collapse. The standing warning is *do not
collapse five orders into one label*; the prescription is *"they must share a core that is literally
the same nodes, and may each add modality, a scalar or a derivation above it."* This is that, for two
of them, arriving from the modality question rather than from the order work.
⚠⚠ And the thing that must survive: **supposing takes no time.** A derivation step is succession
without duration. A shared core carrying a clock would be the collapse.

### 2.2 ⭐⭐⭐ An entry — a hub is a proposition, an entry is an assertion

An entry is an ordinary hub whose relation happens to be `entry`. No new construct:

```
<e> = entry(<M7>, <f>, +)      members: locus, proposition, sign
licensed_by(<e>, <application>)     grade(<e>, likely)     said_by(<e>, anna)
```

> *"A fact is a node"* was half a sentence. A node is the **proposition** `on(a, b)`; it claims
> nothing. **The entry is the claim** — this proposition, here, with this sign.

⭐ It is forced rather than chosen: to say *`on(a,b)` is false in M12* you must be able to point at
`on(a, b)`, so the proposition must exist in order to be denied. The hub therefore cannot be the
assertion, or minting a negation would assert its positive. **Two levels are what negation costs**,
and in exchange nothing has to remember that a bare hub means nothing.

**Where the regress stops.** An entry is a fact, so does it need its own entry? No — **an entry names
its locus, so it is located by being one.** A proposition needs an entry to be placed; an entry places
itself. ⚠ The cost, stated rather than smuggled: `entry` is a member of the **closed class** — one of
the very few relations the engine dispatches on, because *resolve a read* means *walk the chain for
entries naming this proposition*. That is the one mechanism §2.1 already counts, not a new one, and it
should be declared the way `precedence.STAGES` declares itself.

⚠ **Three members, fixed: locus, proposition, sign.** Grade, licence, speaker, clock stamp are facts
*about* the entry, never a fourth member — the same discipline that keeps `causes` binary with
`timing` as an adjunct. Without it the entry becomes a 3-ary node with a bag of optional slots, which
is *one shape, several membership semantics* by another route.

⭐ **What falls out free: the world changing and my having been wrong become different operations.**

| | what happened | how it is written |
|---|---|---|
| they stopped being on each other | the world moved | a **new entry**, opposite sign, later locus |
| I was mistaken that they ever were | my record was wrong | a **fact about the old entry** — same locus, unchanged |

Under a value on the node those are indistinguishable — both are *change it* — which is how a system
quietly rewrites its own history.

⚠ Two entries in one locus with opposite signs is a contradiction the shape permits and does not
detect. That is correct — consistency is a **question you ask**, not a substrate invariant — but it
means *is this moment consistent?* is somebody's job, and today it is nobody's.

### 2.3 Spans — the locus of a trajectory claim

`taking_turns(anna, bo)` is not true *of a moment*. Its subject is a **stretch of the chain**, which
is [limits.md](limits.md)'s *"a sequencing constraint's subject is a path through worlds rather than a
world."* A span is a node with **exactly two members**:

```
<s> = span(<M7>, <M12>)                  position 0 = start, position 1 = end
<e> = entry(<s>, taking_turns(anna, bo), +)   licensed by the recogniser, over the trajectory
```

⭐ **Membership is not stored, and the reason is structural: predecessor is single-valued.** A moment
has one parent; forking yields several *successors*, never several parents. So the walk back from
`M12` is **unique**, and if `M7` is on it the contents are fully determined. Enumerating the moments
between would store what the chain already answers.

| | (A) endpoints | (B) enumerate the moments | (C) a description |
|---|---|---|---|
| not leaking | ✅ contents derived from the chain, so they cannot disagree with it | ❌ two answers to *what is in this span* | ✅ |
| not lossy | ✅ | ⚠ records extent, not *why those* | ✅ |
| readable | ✅ 2-ary, fixed | ❌ **`made_of(?x, wheel, wheel, wheel, wheel)` again** — an extent claim in positional clothes | ⚠ |
| composable | ✅ Allen relations over two pairs of endpoints | ⚠ comparing spans means comparing lists | ❌ not expressible — the *describe rather than name* gap |

**Two things stay out of the span.** The **participants** — `anna` and `bo` are members of the
proposition, never of the span, which is what lets one span host several recognitions (*they took
turns* **and** *it rained throughout*). And **disjunction** — *"on Monday and on Wednesday"* is two
spans plus a fact relating them, never one span with a hole, or disjunction is smuggled into the
substrate where nothing can consume it.

⭐ **Recognition and prescription are one predicate read two ways**, as
[advice-over-sequences.md](advice-over-sequences.md) §3 argues: a **generic** span with variables is a
rule you are planning to satisfy; an **anchored** span is a recognition that it held. Same
anchored/generic split as §2.1, one level up.

⚠ **Costs.** The span is **directional**, so content-equality must normalise by chain order, not by
member order, or two equal spans fail to be equal. Spans are **minted by recognisers, never
enumerated** — any two moments form one, so the population is quadratic; the same rule that stops
`instances` scanning. And nothing checks that `M7` is an ancestor of `M12`: a span over two unrelated
moments is constructible and meaningless, so it wants a check **at the minting site**, where it is
cheap and where it is still detectable.

### 2.4 ⭐⭐⭐ Rules speak of propositions; the machinery speaks of entries

If everything is asserted through entries, are business rules **augmented** to mention them, or does
the **machinery** apply them to entries? The machinery — and this is not a new decision. The
mediated-access arc faced it one level down and answered it: a rule names the identity, the ambient
context resolves it, and `slot_of` inside a frame reads that frame's version **without `holds.mf`
containing one word about frames**. Nothing has changed that would owe a different answer here.

#### Augmentation is a category error, not a costly option

Try to write it and it stops on its own:

```
+on(a, b)      ⟶      entry( <the moment I am in> , on(a, b), + )
                             ^^^^^^^^^^^^^^^^^^^^
```

**The locus is an indexical.** A rule is **generic** (§2.1: variables, no predecessor); an entry is
**anchored**. A rule that named a locus would be about that occasion and could not be reused — the
same reason a method step may only speak of roles and a type schema may not name a target. So
augmentation cannot produce a whole entry, only one with holes; and **a hole the machinery fills at
run time is the machinery doing it.** It buys nothing, and costs four things:

1. **It is a translation, and translations must commute.** *A translation is an island with a bridge
   that appears in every explanation crossing it* — every `why` would show the rewrite rather than
   the rule the author wrote. The residue is the claim, so this is the expensive loss.
2. **One fact in two shapes.** Authored and augmented need syncing, and `why` must un-augment to
   answer. That is the recorded blocker on every swap this project has done.
3. ⭐ **It freezes the resolution policy into every rule.** The property being bought is *the
   machinery can change what a read means without editing a single rule*; augment, and a policy change
   means re-augmenting the corpus.
4. **B3** — *which rules are about time?* gets harder when every rule is three times its size in
   plumbing.

#### The split

| the rule says | `match` / `write` supply |
|---|---|
| `+on(?x, ?y)` in `<A>` | walk the chain for entries naming that proposition; return those signed `+` |
| `+boiling(?w)` in `<B>` | mint the entry in the successor moment; stamp locus, licence and grade from the application |

> **The rule's members are what the author knows. The entry's members are what the application
> knows.**

Locus, licence, speaker and grade-at-this-application do not exist until the rule runs. That is the
whole split, and it is why `entry` is a member of the closed class rather than vocabulary an author
writes.

| | (A) augment the rules | (B) authors write entry-talk natively | (C) machinery absorbs it |
|---|---|---|---|
| not leaking | ❌ explanations show the rewrite, not the rule | ⚠ an author can name a locus, so provenance is forgeable | ✅ every entry is stamped by the write that made it |
| not lossy | ❌ two shapes; `why` must un-augment | ✅ | ✅ |
| readable | ❌ 3× plumbing per rule | ❌ every rule is plumbing | ✅ `causes({+on(a,b)}, …)` reads as written |
| composable | ❌ policy frozen at augmentation time | ⚠ | ✅ resolution changes without touching a rule |

(A) additionally **cannot be written**, per the indexical above.

#### ⚠⚠ The asymmetry that must be enforced

`entry` is both a mechanism and a node a rule can point at, and that is safe **in one direction
only**:

> **Rules may READ entries. Only the machinery may WRITE them.**

Reading is how *"a claim Anna made outranks one Bo made"* gets written at all — an ordinary rule
*about* entries. Writing is how a rule would forge provenance: an entry licensed by nothing, or one
backdated into an earlier locus.

⭐ This matters more than it looks, because §5.1 makes the residue **load-bearing for soundness** — a
missing support link inflates the weakest-link grade. If a rule can mint entries directly, attribution
stops being fragile and becomes **forgeable**, and confidence can be raised by writing one unlicensed
entry. So `write` is the only minter, and it **stamps** the licence from the current application
rather than accepting one as an argument.

#### Costs

* ⚠ **A bug in `write` is systemic** — every fact in the system gets the same wrong provenance.
  Mitigated by it being one place, which makes it one check: `ugm.leak`'s invariant, promoted from
  hygiene to the guard on soundness.
* ⚠ **`match` is a chain walk, not a lookup**, and it now sits on the rule-matching path rather than
  only on reads. The sparse-frame cost, moved somewhere hotter.
* ⭐ **`match` must record which entries it matched** — otherwise *"because `on(a,b)` held, on Anna's
  word"* has no answer. Not overhead: it is half the residue, and it is what makes a misbehaving rule
  distinguishable from a misresolving chain. The mediated-access arc hit exactly this — *binding a
  rule to an identity makes an unmediated rule loudly wrong instead of accidentally right.*

## 3. The keyword budget

| layer | closed set | size |
|---|---|---|
| connective | `implies`, `causes` | **2** |
| entry sign | `+`, `-`, `?` (no entry) | 3 |
| antecedent mark | achievable, given | 2 |
| grade | `certain > likely > possible > unlikely > ?` | ordinal, ~5 |
| timing | one relation over the two moments' endpoints | 1 |

Everything else — `heat`, `cloudy`, `boss`, `overrides`, `by`, `about` — is open-class vocabulary
and reserves nothing.

### The membership test for the closed set

**A connective earns its place only if it licenses a different (forward, backward) reading pair.**
If two candidates read the same, they are one connective and the difference belongs in a member.
Run it and the set shrinks:

* `prevents(A, B)` = `causes(A, {-B})`. Consequents are signed, so prevention is already sayable.
  **Drop it.**
* `enables(A, B)` = `causes(A, {+B @possible})`. Backward, the reader tells them apart by the
  grade: `certain` → doing `A` achieves `B`; `possible` → `A` is a precondition and something else
  must still happen. **Drop it.**

### ⭐⭐⭐ Why `implies` and `causes` do not collapse

Not *one is logical and one is worldly*. The test is mechanical:

> **Retract the antecedent. Does the consequent go with it?**
> Yes → `implies`. The entry is **derived**, and lands in the **same** moment.
> No → `causes`. The entry is **asserted**, persists, and lands in a **later** moment.

Water you stopped heating stays boiled. That is inertia, and it is why *a zero-delay cause is still
not an implication* — you cannot merge the two by setting the delay to zero.

⚠ Allen relations (`before`, `during`, `overlaps`) are **not** connectives. They are ordinary facts
about moments, which are already nodes.

## 4. Time

**An action is not a new kind of thing.** An action is an event, an event is a moment, and
`heat(?a, ?w)` is a fact holding over an interval. An action therefore enters the antecedent as an
ordinary member, and *execute* means **make this event-fact true**. No action construct, no operator
table beside the rules.

*"…causes it to boil in 5 minutes"* needs three decisions:

1. **Say which endpoints.** *The heating takes 5 minutes* / *boiling starts 5 minutes after heating
   starts* / *5 minutes after it stops* are three different rules that plan differently. The timing
   member relates named endpoints — `end(A) → start(B)` — never a bare scalar.
2. **It is a constraint, not a number.** `[4min, 7min]`, `≥5min`, *eventually*, and *unknown* must
   all be sayable, or precision-by-silence returns one level up. Absent timing = unknown timing, and
   that is legal and readable.
3. **It is a fact *about* the rule, not a third member of `causes`.** That keeps the connective
   binary, lets the delay be genuinely absent, and lets two timing claims coexist with different
   sources — *the manual says 5, I measured 7* — which is real and unsayable if the delay is a slot.

⭐ The payoff is that timing is read in both directions: **forward** it says when to *expect* the
effect, and therefore when its absence counts as a **deviation** rather than as patience;
**backward** it is a **filter** — needing boiling water in two minutes rules this rule out. A
delay-less rule expresses neither.

## 5. Possibility

⚠⚠⚠ **Three different things are called this, and they must not share a slot.**

| | what it is | where it goes |
|---|---|---|
| **strength** | how often the effect actually follows | grade on the **entry** |
| **confidence** | how sure I am of the rule | grade on the **rule**; moves with evidence |
| **defeasibility** | what would cancel it | **not a number** — a relation to other rules (`unless`, `overrides`) |

Collapsed, `0.6` means three things at once and combining them is arithmetic nonsense. The third is
the load-bearing one for reasoning — *unless the front has already passed* — and it needs **no
numeric apparatus at all**: it is the same precedence machinery as boss-beats-vice.

**Per-entry, not per-rule.** One rule has consequences of different strength: heating boils the
water (certain) and scorches the pan (unlikely). A rule-level grade cannot say that; it is shorthand
for *all entries the same*.

**Ordinal, not probabilistic.** Real probabilities need independence assumptions that cannot be
stated in the graph, so multiplying leaks silently. Ordinal grades compose by weakest link. A
numeric member may sit *beside* the grade when its own provenance is a member (*"from 300
observations"*), never in place of it.

⚠ **The honest cost:** two independent *likely*s ought to be more than *likely*, and `min` says they
are not — ordinal grades do not accumulate evidence. The right place to fix that is **counting over
episodes**, not arithmetic over grades. Recorded rather than papered over.

⚠ Grade is orthogonal to `?`. `?volume` is *changes, magnitude unknown*; `+rain @possible` is *might
become true*. Different ignorance, different slot.

### 5.1 ⭐⭐⭐ Where `@likely` actually lives — on the entry, never on the node

*Do I tag every node?* **No — and not because it is expensive.**

> A grade stored on a **fact node** is a cache of a derived value. `rain @likely` holds only given the
> support that produced it, so when the support changes the tag must be invalidated — and invalidation
> over a dependency web is a **TMS**, deleted twice here and declined again under *no settling, no
> interning*. The standing line applies verbatim: **an index over what was asserted is storage; a
> cache of what was derived is a TMS.**

A second, independent reason: **a tag is ignorable.** Reading a fact and reading its grade are two
reads, so a consumer that forgets produces a conclusion with no grade at all. That is the leak
criterion failing by *discipline* where the whole edges-as-nodes arc bought **structure**.

**Every fact already has a provenance node — the entry of §2.2. Put the grade there.**

| the fact came from | the node that already exists | carries |
|---|---|---|
| a rule applying | the application / transformation | the rule's per-entry grade |
| someone saying so | the utterance (speaker, authority) | how firmly they said it |
| observing | the sighting | sensor confidence |
| an assumption | the moment's licence | the grade of what was supposed |

⭐ The entry had to exist anyway — the **sign** has nowhere else to live, since edges carry no facts.
So the grade slot costs nothing; it is a member of a node the design was already forced to mint. That
is the sign of a shape being right rather than convenient.

#### Superseded, not invalidated — which is why storing it is *not* a TMS

The obvious objection: if a stored grade is a cache, is a stored derived *fact* not also one?

> **A dated derived fact needs no invalidation.** At M7 you recognised taking-turns; at M12 something
> writes `−taking_turns(a, b)`. The M7 entry stays true **of M7**. Nothing is retracted, nothing
> propagates, and *are they taking turns?* resolves through the chain to the most recent entry.

That is exactly what the arc was for — *a fact must not become timelessly true just because it was
written*. So the rule is one line and it covers modality and recognition together:

> **Store on the entry — dated, signed, attributed, superseded.
> Never on the node — timeless, and therefore requiring invalidation.**

#### Frames and grades are two different problems

The word *likely* covers two things, which is why *tag or guard* felt like a forced choice:

| | *"I am supposing this — what follows?"* | *"this generally holds, weakly"* |
|---|---|---|
| shape | a **moment** you enter and leave (§2.1) | a **grade on the rule**, recorded on the entry at application |
| count | few, deliberate, **nested** | many, independent |
| nesting | free — a path in the predecessor tree | does not nest; composes by weakest link |
| crossing | ✅ **already mandatory** — a read cannot reach into a moment except through the chain | not a crossing at all |

⚠ Keep them apart or you get the ATMS this project deleted: twenty independently-uncertain facts is
2²⁰ moments. **Use moments where you *choose* to suppose; use grades where the world is merely weakly
connected.**

#### Guard nodes — scored, and what they were right about

| | (A) grade on the fact node | (B) a guard node per modalised fact | (C) moments + graded entries, weakest link computed |
|---|---|---|---|
| not leaking | ❌ ignorable by default; a consumer that skips it invents certainty | ✅ crossing is forced… | ✅ a conclusion derived in a moment **is** in it; the grade is recomputed from support |
| not lossy | ❌ a number with no premise | ⚠ says *that* it is uncertain, not *on whose word* | ✅ speaker, rule and sighting all survive |
| readable | ⚠ readable and stale | ⚠ | ✅ *which conclusions rest on something merely possible* is a walk |
| composable | ❌ two tagged facts combine to *what?* | ❌ **every consumer must handle both shapes** — guarded and bare | ✅ weakest link over the support chain |

⚠⚠ (B)'s failure is worth naming because it has no middle setting: **optional guards mean consumers
handle two shapes and forgetting returns; mandatory guards mean a node and a hop for every certain
fact in the system.**

⭐ **But the guard instinct was right about one thing** — *forcing handling*. A computed grade compels
nothing, and *don't act on a merely-possible fact without acknowledging it* is a real requirement. It
belongs at **the one place effects leave**, exactly as prohibitions do in §9: check the grade of what
licenses an **action** at the dispatch door, where the set is small and known, rather than making a
million reads cross a guard to catch the one that matters.

#### ⚠⚠ What (C) costs

* *How likely* becomes a **walk, not a read** — the same shape as `holds`, already a measured and
  accepted 2.35×. The `step` precedent: a cost that is a decision, not a veto.
* ⚠⚠ **The residue becomes load-bearing for correctness, not only for explanation.** A write that
  loses its attribution does not merely become unexplainable — it becomes **falsely confident**,
  because a missing support link removes a weak link from the `min`. That promotes `ugm.leak`'s
  invariant from hygiene to soundness.
* Cycles in the support chain need the same termination care as any derivation walk.

### 5.2 Do we run out of dimensions?

The fear behind *"another dimension"* deserves a test rather than reassurance. The dimensions actually
spent, in the whole system:

| | why it cannot be structure |
|---|---|
| **identity** | *this node is that node* is not a relation between two things; it is the precondition for there being things |
| **connection** | an edge |
| **order among connections** | *the 2nd member* — position is not a thing in the world, so it cannot be a node |
| *(a mechanism, not a dimension)* | **how a read resolves** — the predecessor chain of §2.1, named and reachable |

Everything else added since — type, sign, licence, grade, time, force, authority, span — is a
**member of a node**. None cost a dimension.

> ⭐⭐⭐ **You run out of dimensions only if you try to say something that is not about anything.**

Every distinction so far has been a relation between two things, and a relation is a node: modality
relates a claim to its support, a sign relates a proposition to a locus, time relates a moment to its
predecessor. If a candidate can be phrased as *X stands in relation R to Y* it is structure. **Order
is the one that genuinely could not** — which is why the substrate has ordered targets, and why
`step[i+1]` is still the hard one.

## 6. Worked

```
<R1> = causes(
    { +heat(?a, ?w),  +water(?w),  ~open(?vessel) },
    { +boiling(?w) @certain,  -liquid(?w) @certain,  ?volume(?w) } )

timing(R1, end→start, [4min, 7min])
unless(R1, +altitude(?w, high))
```

```
<R2> = implies(
    { +cloudy(?day, morning) },
    { +rain(?day, afternoon) @likely } )
```

⭐⭐⭐ **The second one is the argument for the whole section 3.** *"Cloudy morning likely implies
rainy afternoon"* — the persistence test agrees it is `implies` (learn it was not cloudy and the
rain claim goes with it), but the surface wording reads just as easily as causal, and clouds do not
cause the afternoon's rain: a front causes both.

That is not bookkeeping. Written as `causes`, the backward reader produces **a plan to make it rain
by making it cloudy**. The two-connective split is what makes that plan unwritable, and it earned
its keep on the first example anyone offered.

## 7. Harmony

Scored per [harmony.md](harmony.md), and the expressiveness pass first, per that document's own
§*Expressiveness is PRIOR to the table*.

### Expressiveness — write the sentence

| sentence | what it demands |
|---|---|
| *heating water causes it to boil* | the base case |
| *pouring raises the level, by an unknown amount* | a **no-entry** slot inside the consequent |
| *a rule the boss gave beats one the vice gave* | the rule is a **node other facts take as a member** |
| *seeing a dog chase a cat causes…* | nesting, no new shape |
| *it must be on the bench (you may put it there); it must be a Tuesday (you may not)* | antecedent members are **not alike** |

### The form

| | (A) guard → program | (B) one rule per direction | (C) `connective(moment, moment)` |
|---|---|---|---|
| not leaking | ❌ backward read is abduction in deduction's clothes; no licensing statement | ❌ two statements drift; neither is the other's premise | ✅ one statement; each reading cites `R`, and its licence says what the citation is worth |
| not lossy | ❌ what it makes true is recoverable only by running it | ⚠ the pair coheres only by convention | ✅ `<B>` **is** the postcondition; `?` preserves the gap instead of erasing it |
| readable | ❌ write-only | ⚠ readable, doubled | ✅ *which rules are about time / disturb position / come from the boss* are ordinary queries |
| composable | ❌ two bodies cannot join | ❌ 2ⁿ | ✅ join on signed membership; **no-entry survives composition as no-entry**, which is what lets two partial rule sets merge without lying |

(A) also fails outright on *speakability*: `overrides(R1, R2)` has no subject when the rule is a
program.

### Time and possibility

| | as connectives | as members |
|---|---|---|
| not leaking | ❌ `likely_causes` fuses strength with defeasibility; nothing records which | ✅ three separate members, each attributable |
| not lossy | ❌ *how likely*, *how long* unrecoverable from a name | ✅ both askable, both allowed to be absent |
| readable | ❌ *which rules are uncertain?* becomes a name census | ✅ ordinary query over members |
| composable | ❌ the set grows multiplicatively; two authors will not share names | ✅ grade and timing join independently of the connective |

## 8. The floor — what the engine must actually build

If `causes`' meaning is given by rules, and those rules use connectives whose meaning is given by
rules, the tower never grounds. **The closed class cannot be empty.** What it can be is *not the
connectives*:

1. **recall** — which rules come to mind here. **Never complete**; see §9
2. **match** — unify a **generic** moment against an **anchored** one (§2.1), over what recall
   offered. ⭐ It **records which entries it matched**, per §2.4 — that is half the residue, not
   bookkeeping
3. **write** — mint signed entries into a moment. ⚠ **The only minter of entries**, and it *stamps*
   the licence from the current application rather than accepting one (§2.4)
4. **arbitrate** — among the rules that matched, pick one; **total**, table-driven, always answers

⭐⭐⭐ The fourth is the one that is easy to get wrong. A meta-rule deciding which rule to apply must
itself be selected, and that regress is now happening *at run time*. **The bottom-most arbitrator is
a lookup over an authored precedence table that always returns and never searches.** Reflection may
be arbitrarily deep; the final tiebreak may not be reflective. That is the stratification condition,
and it is the same one [precedence](reflection.md)'s *last stage must be total* already names.

⚠ **An earlier draft of this section had three primitives and called the last one `select`.** That
conflated two steps with opposite requirements, and it did so by quietly assuming `match` runs
against *every* rule — a RETE-shaped assumption that does not scale and is not how recognition
works. **Recall proposes, match filters, arbitrate commits.** Only the last is total. §9 is the
consequence.

### A connective is a table entry, not a branch

```
<F> = causes( { +rule(?r), +conn(?r, causes), +matches(?s, ant(?r)) },
              { +succ(?s, ?s'), +applied(?r, ?s, ?s') } )

<B> = causes( { +want(?f), +conn(?r, causes), +member(+?f, con(?r)) },
              { +candidate(?r, ?f) } )
```

`matches` is primitive; everything above it is data. ⭐ **The test that the floor is in the right
place: adding a connective adds rows, not branches.** If a new connective requires touching the
engine, the connective set is not data and §3's budget is fiction.

⚠ **One interpreter, or none of this counts.** Meta-rules bought nothing if a Python loop
special-cases them. The interpreter's step is *select a rule, apply it*, and object-rules and
meta-rules are indistinguishable to it — a flat tower, not a stacked one. If you cannot answer
*which level am I on?*, that is the sign it is right.

## 9. ⭐⭐⭐ Recall is System 1, and experience lives there

> *"It doesn't offer any guarantee of finding all applicable rules — that would be computationally
> too heavy — but I think that's where experience lies: the right rules come to my mind at the
> correct moment."*

Correct, and it fixes §8. Recall and arbitration are two jobs with **opposite requirements**:

| | **recall** | **match** | **arbitrate** |
|---|---|---|---|
| job | which rules come to mind | do they actually fit | which one now |
| complete? | ❌ **never**, by design | ✅ over what recall offered | ✅ over what matched |
| total? | — | — | ✅ **must always answer** |
| authored or learned? | **learned** | mechanical | **authored** (precedence) |
| failure | a rule you needed never surfaced | — | dithering, or a hang |
| cost of being wrong | recoverable — a worse plan, or a surprise later | — | a wrong action |

### Why experience belongs in recall specifically

Two structural reasons, neither of which is an appeal to cognitive plausibility:

1. **It is the only step where being wrong is recoverable.** A missed rule costs a worse plan or a
   later surprise, both of which the machinery already handles. A wrong arbitration costs a wrong
   *action*. Put learning where errors are survivable.
2. **It is the only step with no authored ground truth.** *Which rules should have come to mind?*
   has no answer but *the ones that turned out to matter*, so it can only be learned. Arbitration
   has the opposite property — `by(R, boss)`, `overrides(R1, R2)` **are** the ground truth, and
   learning them would be wrong.

### ⚠ What incompleteness costs immediately

Once recall may miss, **"no rule applies" is ambiguous**: nothing applies, or nothing *came to
mind*. That is `present / absent / no-entry` again, one level up — §2's discipline landing on the
machinery that reads it. So recall returns a **set plus a state**, never a set.

⚠ And the state is cheap to compute from the wrong thing (*did I find anything?*) and expensive from
the right thing (**is this situation familiar?**). Unfamiliar-and-empty is a different event from
familiar-and-empty, and only the first should escalate.

### System 2 is not a second mechanism

It is **recall with the budget removed** — same match, same arbitrate, exhaustive proposal. The
fast/slow split therefore needs no architectural fork: a budget parameter, and an escalation rule
that is *a rule*.

```
<E> = causes( { +decision_point(?d), +recalled(?d, ∅), ~familiar(?s) },
              { +goal(exhaustive_recall(?d)) } )
```

The escalation triggers are exactly the impasses — nothing came to mind, what came to mind conflicts
irreducibly, or what came to mind was **surprising**, which is §10's rule feeding this one.

### What trains it, and the trap

The signal is already deposited: `applied(R, s, s')`, plus whatever explanation a surprise produced.
Recall learns from its own outputs that survived — chunking. And chunking has one well-known failure
that must be designed against rather than discovered:

⚠⚠ **Training recall on its own accepted outputs narrows it monotonically.** A rule that never
surfaces is never applied, never reinforced, and becomes permanently invisible. The exhaustive pass
is therefore **not a fallback — it is the only thing that injects candidates recall would never have
produced**, so it must fire on novelty or on a schedule, not only on impasse. ⭐ Otherwise the system
calcifies precisely in the domains where it is doing well, and nothing reports it.

### What recall is keyed by

Not the situation alone — **the situation *and* the active goal**. The same world brings different
rules to mind depending on what is being attempted; a recall keyed only on world features surfaces
the same set forever regardless of intent.

⭐ [passes.md](passes.md):50 already has the mechanism — *"the engine shall maintain an index (a web)
of what passes are linked to others, the connective is the same terms"* — filed under
**optimization**. It is not an optimization. Spreading activation over the shared-member web **is**
the recall substrate, and it was in the first draft under the wrong heading.

### ⚠⚠ The carve-out — incompleteness has a boundary

**Recall may be incomplete about what to do. It may not be incomplete about what you must not do.**
A prohibition that fails to come to mind is a forbidden act that nothing notices.

The repair is not *make recall complete for norms*. It is to take prohibitions off the recall path
entirely: check them at **write**, indexed by the entries about to be written. That set is small and
known, so the check is cheap and exhaustive. **A prohibition is a gate on application, not a
competitor in recall.**

### Harmony on the split

| | one `select` | **recall + arbitrate** |
|---|---|---|
| not leaking | ❌ an incomplete step reports as authoritative; *nothing applies* asserts more than was checked | ✅ the two silences are distinguishable, and only one escalates |
| not lossy | ❌ *did you consider R?* is unanswerable | ✅ recalled / matched / rejected are three separate residues |
| readable | ⚠ | ✅ *which rules does this situation bring to mind?* is a query, askable without applying anything |
| composable | ❌ learning and authority contend for one slot | ✅ learned proposal, authored arbitration, no contest |

⚠ Price: three residues per decision instead of one, and recall's index must be rebuilt as episodes
accumulate. The second is the real cost, and per the standing line it is a **rebuild from the episode
record, never a patch of the previous index**.

## 10. ⭐⭐⭐ Surprise, and why machinery-in-Python forecloses it

> **Surprise is a match.** It is an *expected* entry and an *observed* entry that disagree.

That is the whole mechanism, and it explains the real cost of machinery written in Python: not
opacity, not speed, but that **the agent's own state is not in the world it reasons about**. An
expectation held in a local variable is unmatched not because the rule is weak but because there is
nothing there to match. Three obligations follow:

1. **Forward application deposits expectations, not just facts.** Applying `causes(A, B)` at `t`
   writes `expected(+boiling(w), by t+7)` into the world. §4's timing member is what makes that
   entry *writable*; without the deposit there is nothing to be surprised against.
2. **The continuation is a moment.** *What I am doing, where I am in it, what I am waiting for* —
   signed entries, not a stack frame.
3. **Surprise is an ordinary rule that wins on precedence:**

```
<S> = causes( { +expected(?f, by ?t), +now(?t'), after(?t', ?t), -?f },
              { +goal(explain_failure(?f)), -committed(?proc) } )
```

**There is no interrupt mechanism.** Preemption is `<S>` outranking the rule that would have
continued the procedure — possible only because *continue the procedure* was itself a selectable
rule, which is exactly what a stack frame is not.

### ⚠ Rules, not a procedure — and what commitment then is

*"The machinery described with rules **in a procedure**"* pulls two ways. A procedure is a committed
order, which is precisely the thing that cannot be preempted mid-way: if *to find an answer, look
for causes* is a procedure, step 3 owns the agent until it returns.

**Procedures exist, but as data that biases selection, never as control flow that owns the loop.**
`committed(?proc, step_3)` is a moment entry that raises the precedence of continuing; it does not
remove the alternatives. So commitment is real (the agent does not dither), it stays preemptable
(surprise outranks it), and *dropping* it is a **write** — which means the agent can be asked why it
abandoned something.

### The strategy example, as data

```
<M> = causes( { +goal(?g, explain(?f)) },
              { +goal(find(?r)), +constraint(?r, causes(_, {+?f})) } )
```

⭐⭐⭐ And now the thing no other arrangement gives: `overrides(M, M2)`, `unless(M, +domain(?f,
social))`. **A strategy becomes defeasible like any other claim.** A Python strategy cannot be
overridden by a KB statement, and that asymmetry is the larger cost of machinery-in-code —
larger than interruptibility, which is what the question started from.

### Reflection is demanded, not continuous

⚠ Consult meta-rules only at **named decision points** the interpreter already reaches — which rule
to apply, what to do on failure, what to do on surprise — never between arbitrary steps. Each
decision point either gets a meta-answer or falls through to the total table, so no decision hangs.
This is Soar's impasse discipline; without it you pay meta-cost on every step and the tower never
bottoms out in practice.

### Harmony on the floor

| | (A) connectives in the engine | (B) all rules, no floor | (C) rules + 4 primitives + total arbitrator |
|---|---|---|---|
| not leaking | ❌ engine decisions have no premise and appear in no explanation | ❌ regress; never grounds | ✅ every step cites its rule; the floor is 3 named things |
| not lossy | ❌ *why did you stop?* has no answer | ⚠ | ✅ deposits, commitments and abandonments are all entries |
| readable | ❌ strategy invisible to a query, undefeatable by data | ✅ | ✅ *which strategies are about explanation?* is a query |
| composable | ❌ two authors cannot add a connective | ⚠ meta-rules cannot be ordered | ✅ new connective = rows; ordering = precedence |

⚠ **(C)'s price, named:** every step costs a selection, and a wrong precedence table produces
dithering that reads as a bug in the rules. Both are measurable — **selections per useful write**,
and **commitments dropped per commitment made**. Build those two counters *with* the interpreter,
not after it.

## 11. The acceptance gate

Not *can the system reconstruct the masked text* — that is representational, and the standing rule
is behavioural. The gate is **commutation**:

> for every rule `R` and every moment `s`: backward(`goal`) proposes `R` at `s`
> **iff** forward(`R`, `s`) yields a moment satisfying `goal`.

Run it as a property over the whole rule set. A rule where the two readings disagree is one whose
consequent is lying about what it does. ⭐ The check exists *only because* there is one statement and
two readings: under (B) it is untestable by construction, and under (A) it is undefined.

## What this leaves open

* **Cardinality.** `made_of(?x, wheel×4)` is a count claim in positional clothing; backward matching
  needs cardinality declared per relation position, beside arity, ordered/unordered and converse.
* **Constrained-not-bound values.** *The level rises by an unknown amount* wants a value member
  constrained rather than bound — the same unbuilt capability as the order core. ⭐ Note the boundary
  §2.3 draws: **recognising an ongoing pattern does not need this** (`span(M7, M12)` superseded by
  `span(M7, M13)` is ordinary versioning); only **predicting that it continues** wants an unbound end
  member. Those two were merged in an earlier draft and are not the same claim.
* **Consistency within a moment**, per §2.2 — two entries with opposite signs in one locus is
  permitted and undetected. Correct, since consistency is a question rather than an invariant, but it
  is currently nobody's job.
* **Span normalisation**, per §2.3 — content-equality must order by the chain, not by member order.
* **Enforcing the entry write-monopoly**, per §2.4 — *rules may read entries, only the machinery may
  write them* is stated but has no mechanism. It is the same shape as `access.offenders`, which
  already measures corpus compliance with the mediated vocabulary, so the instrument exists and is
  pointed at the wrong thing. ⚠ Until it is enforced, §5.1's soundness claim rests on convention.
* **Evidence accumulation**, per §5 — counting over episodes, with no arithmetic on grades.
* **Familiarity**, per §9 — the escalation trigger needs *have I seen moments like this?*, which is a
  measure over the episode record and is not the same as *did recall return anything*.
* **The exploration schedule**, per §9 — when the exhaustive pass fires absent an impasse. Left open
  is the *rate*, not the requirement; without one, recall calcifies silently.
* **Signed frame membership**, on which both directions depend, and which is the prerequisite the
  whole of this document inherits from [facts-as-nodes.md](facts-as-nodes.md).

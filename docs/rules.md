# Rules — one form, two readings

**Status: a design, taken fresh.** It does not describe what is built; where it disagrees with the
engine, the engine has not been changed yet. It is the answer to a question
[passes.md](passes.md) left open — *what is a rule, such that planning can read it backwards and
execution can read it forwards* — and the review findings there are its starting point.

The short version:

> A rule is a **fact relating two moments**. Direction is a *query* over it, never a field in it.
> Time and possibility are **members**, never connectives. The engine's floor is **four
> primitives** — recall, match, write, arbitrate — of which **only the last is complete**;
> everything else, including what the connectives mean, is rules.

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
2. **match** — a pattern against a moment's signed membership, over what recall offered
3. **write** — signed entries into a moment
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
  constrained rather than bound — the same unbuilt capability as the order core.
* **Evidence accumulation**, per §5 — counting over episodes, with no arithmetic on grades.
* **Familiarity**, per §9 — the escalation trigger needs *have I seen moments like this?*, which is a
  measure over the episode record and is not the same as *did recall return anything*.
* **The exploration schedule**, per §9 — when the exhaustive pass fires absent an impasse. Left open
  is the *rate*, not the requirement; without one, recall calcifies silently.
* **Signed frame membership**, on which both directions depend, and which is the prerequisite the
  whole of this document inherits from [facts-as-nodes.md](facts-as-nodes.md).

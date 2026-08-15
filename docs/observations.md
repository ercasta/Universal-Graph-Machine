# Observations and audit findings

A running notebook. Not a design document and not a plan — a place to put things that have been
**looked at** but not yet decided, so a decision can later be made against a record rather than
against a memory.

The repository's conventions apply: a claim with a measurement behind it says so, a claim without one
is marked as an opinion, and a claim that was checked and turned out wrong is corrected **in place
with the correction visible**, not deleted.

Baseline for everything below: `python -m ugm.selftest` → **537 checks, 0 failing**, on branch
`restart` at `bb55eb5`.

---

# Part 1 — The Python audit

> **The question.** *We have moved too many things into Python code.* Starting from `chain`: why do
> Entries and Moments need to exist in Python at all?

Method: enumerate every instance attribute of every class in the engine modules, ask of each whether
the graph holds the same thing, then trace who reads it.

## 1.1 What is in Python, by role

| role | where | verdict |
|---|---|---|
| **Floor** (§20) | `graph.py`, `sexpr.py`, `text.py`, the gate's write path, `machine.tick` / `_apply` / `_deliver` / `_conclude_at` | ✅ correct |
| **Index / cache** (§7) | `Situation`, `Chain._claims` / `_by_node` / `_moment_by_node`, `RuleSet.by_conclusion`, `Rule.walk_order`, `Graph._has_var` / `_by_rel` / `_interned`, `Machine._match_cache` / `_state_cache` / `_play_cache` / `_verdicts` | ✅ correct — every one is gated (`ugm.state`, `ugm.agreement`, `ugm.arbitration`, `_has_var_slow`) |
| **Instrument** | `harmony`, `vocabulary`, `bundle`, `workload`, `modality`, `shapes`, `atlas`, `compose`, `backward`, `forest`, `learning`, `state`, `agreement`, `arbitration` | ✅ correct — measuring is not reasoning |
| **Corpus-as-fixture** | `dungeon`, `quest`, `practice`, `artefact`, `table`, `tools` | ✅ correct |
| **Leak** | §1.2 | ❌ |

⭐ **So the answer to the opening question is: the mirror half of `Entry` and `Moment` is not the
problem.** `Entry.locus/proposition/sign` are members 0/1/2 of the entry node; `Moment.predecessor`
is `pred`; `Moment.delta` is `in_delta` + `delta_next`; `Span` is entirely `span(start, end)`. All of
it is a cache of graph content maintained where the state is, which is §7's own rule, and all of it is
a measured win (`_has_var` was **91%** of the rule-level read; `Situation.__init__` was the single
largest cost in the loop). Deleting the mirrors buys a slower engine and nothing else.

⚠ **Two things this audit got wrong on its first pass, corrected here rather than removed:**

* **Knobs are not leaks.** `_knob` (`machine.py:1758`) reads `depth`, `budget`, `hypotheses` and
  `tolerance` off the graph; `max_depth = 8`, `supposition_budget = 32` and `recall_budget = None`
  are *defaults*, not the values in force.
* **`Frame.purpose` and `Frame.wrap` hold NodeIds**, not strings — `purpose` is
  `supposing(<assumption>)`, a real graph node. The defect there is narrower than first stated: the
  value is representable, but no *fact* ever relates a live frame to its purpose.

## 1.2 The leak inventory

A **leak** is: read to make a decision · no counterpart in the graph · unreachable to any rule.

### Chain (§4, §5, §13, §14)

| | site | note |
|---|---|---|
| `Entry.licence` | `chain.py:61` | the class docstring calls licence and source "ordinary facts about the entry (§5)". They are not facts. |
| `Entry.source` | `chain.py:62` | §13's channel |
| `Entry.mention` | `chain.py:67` | §14's use/mention |
| `Moment.licence` | `chain.py:86` | §4: *"which of the two this is, is said by the licence and by nothing else"* — ⚠⚠⚠ **assigned once and read nowhere in the repository** |

### Rules (§8, §14, §21)

| | site | note |
|---|---|---|
| `Rule.mentions` | `rules.py:78` | `Entry.mention` one layer up |
| `Rule.connective` | `rules.py:67` | branched on **as a Python string** at `machine.py:3141,3176` — §8's `causes`/`implies` distinction. `conn(<R>, causes)` *is* reified, so a rule can read it; the engine reads the Python copy, and nothing holds the two to each other |
| `RuleSet.composed_from` | `rules.py:180` | half-closed: the `composed` answerer (`machine.py:446`) makes it askable, but the fact stays a Python dict |

### Gate (§17)

| | site | note |
|---|---|---|
| `Frame.state` | `gate.py:62` | `discharged / exhausted / abandoned` — a **bare Python string**, set at `machine.py:2711`. The outcome of a supposition. |
| frame ⟶ purpose, parent | `gate.py:49,50` | ⭐ `gate.py:145` *states the requirement itself*: "§17 needs each to be a node other facts can be about — **a purpose, a parent, a state**". No such fact is ever deposited. |
| `Frame.carried` | `gate.py:63` | what crossed out (§17) |
| `Gate.reseat` | `gate.py:151` | already noted in-file as §21 debt: "every seat move is a write, and this one is not yet recorded as an entry". ⚠ **It also re-mints `frame.node`**, so a frame's identity is not stable across its life. Currently harmless *only* because everything written about a frame (`left`, `concluded` — `machine.py:1569,2707`) happens at discharge. That is a coincidence of timing, not a guarantee. |

### Machine

| | site | note |
|---|---|---|
| `Step.state` | `machine.py:61` | what a tick did; `workload.py`, `compose.py` and `__main__.py:67` all branch on the string |
| `_bookkeeping` | `machine.py:660` | a **50-name Python set** deciding what crosses out of a frame (§17) and what counts as a circumstance (§19). ⚠ The comment admits it: *"the closed set of §10 growing by one, and it is a real cost"*. A corpus can neither add to it nor take from it. |
| `_harm` | `machine.py:4408` | credit-assignment tallies |

### Minor

`_tolerance` (`machine.py:1777`) is an exact surviving duplicate of `_knob(TOLERANCE, 0)` — the
generalisation landed and the special case was never deleted.

## 1.3 The contagion — measured

*If something is only in Python, it is very easy that this caused other things to be in Python too.*
Counting the methods that read each leaked field:

| leak | reader methods | lines in those methods |
|---|---|---|
| `_bookkeeping` | `__init__`, `_settle`, `discharge`, `_circumstances`, `report` | 1,048 |
| `Entry.source` | `_applications`, `_kept`, `_line`, `_rendered` | 545 |
| `Entry.consumed` | `_applications`, `_apply`, `_is_mention`, `_line`, `_revive`, `_wants` | 495 |
| `Entry.licence` | `review`, `blame`, `_choosers`, `_instead_of`, `discharge`, `_line`, `_rendered` | 470 |
| `mention` / `mentions` | `_again`, `_is_mention`, `discharge`, `_rendered` | 284 |
| `Frame.state` | `discharge`, `run` | 134 |

⚠ Method size **overstates** — not every line of `discharge` exists because of `_bookkeeping`. Read
the column as blast radius, not as debt.

Three contagions worth naming, in order of severity:

1. ⭐⭐⭐ **Credit assignment is Python because `licence` is Python.** `review`, `blame`, `harm_of`,
   `_support`, `_choosers`, `_instead_of` all walk `e.licence`. *Why did that go well* is the agent's
   most important question about itself and no rule can take part in answering it.
   **The proof is already in the tree**: `machine.py:90-92` mints `EXERCISED` as *"the same claim as
   `applied(<R>)`, but as a proposition a rule can match rather than a licence only Python can
   read."* The leak was hit, diagnosed correctly, and mirrored around instead of fixed.

2. ⭐ **`chain.trail()` still walks `Entry.consumed`** (`chain.py:421`) although `chain.rests_on()`
   (`chain.py:477`) already reads the graph. The fix arrived and the consumer did not move to it, so
   `why()` remains a native walk over a Python tuple and everything downstream inherits that.

3. **`discharge` reads three leaks at once** — `_bookkeeping`, `e.mention`, `frame.state` — which is
   why §17's crossing decision, the one a corpus most obviously ought to be able to argue with, is a
   93-line Python method.

## 1.4 The pattern

⭐⭐⭐ **Every leak is about the agent's own act** — what licensed a claim, which channel it came
through, use or mention, how a supposition ended, what crosses out of it, what a tick did, what a
rule is a shortcut for.

That is precisely the bucket `ugm.vocabulary` measured: 48 of 101 reserved names are the agent's own
deliberation. **The engine reserves its vocabulary for deliberation and then keeps deliberation's own
record in Python fields.** The world-facing half of the design is clean; the self-reflective half is
where everything leaked — and that is also where §21's defect has now been counted ten times.

## 1.5 The decision that has to come before any fix

The same defect has been closed **three incompatible ways** already:

| remedy | example | what it gives |
|---|---|---|
| **skeleton relation** | `rests_on` | matchable by a stratum-0 rule; unarguable, undated, cannot be denied |
| **occasion** | `defeated(<loser>, <winner>)` | an entry — dated, attributed, deniable |
| **answerer / door** | `composed(<R>)` | askable, but the fact stays in Python |

Nothing says which remedy a given leak gets, and they are not interchangeable. `Frame.state` forces
the question: is *this supposition was abandoned* structure (nobody asserted it) or a claim (deniable)?
`Entry.licence` is clearly skeleton by `rests_on`'s own argument. `_bookkeeping` is neither — it is a
closed set, and its shape is probably a **standing fact per name**, the way bundled rules became
`standing`.

⚠ Writing that rule down first is the whole point. Otherwise ten fixes arrive in four shapes and the
next audit finds a fifth.

---

# Part 2 — Open proposals

## 2.1 State markers instead of consumption, and a two-step notice/listen convention

> **The proposal.** `authoring.md` §0 tells an author to *consume* an occasion — to deny something so
> it stops being true. Replace that with a **state change**: a thing is not removed, it is
> substituted. A message from a channel carries a state marker, and a rule changes the marker.
> Generalised: rule A **notices** something and **marks** it with a starting state; rule B **listens**
> on that state. Decoupled, and more robust.

### What the proposal gets right

⭐⭐⭐ **It dissolves §0's exception, which is currently the sharpest edge in the whole authoring
document.** §0 has to say two opposite things:

> Consume what you concluded. **Never** consume what you were told.

The second half exists because `arrived` is an unarguable boundary record and `<intake>` is a bundled
rule, so denying `says(...)` merely licenses `<intake>` to re-derive it — the hang traced in
`quest-feedback.md` §4:

```
150  + says(p1, want(p1, key1), +)
149  - says(p1, want(p1, key1), +)
149  + wants(p1, key1)
```

A marker fixes this **exactly**, and the mechanism is worth being precise about: with a marker
nothing is denied, so `<intake>`'s re-conclusion of `says(...)` is **not new**, so quiescence stops
it where today it does not. The boundary rule and the interior rule become the same rule. One
convention replaces a rule and its exception.

⭐ **It is not a new idea in this repo — it is the generalisation of one that already works.**
§0's third row is `may(x, r)`: *turn* is a standing fact, and what acting spends is not the fact but a
**right**. `may` is already a state marker; the proposal is to stop treating that as a trick for
turn-taking and make it the shape.

⭐ **It makes the lifecycle a fact**, which is the same remedy Part 1 argues for everywhere else:
dated, attributed, deniable, inspectable. The round-417 eternal clock
(`dungeon-feedback.md` §7 — 8,072 entries with every outcome check green) was invisible *because
there was no state to look at*. With a marker there is something to print, something to assert about,
and something a watchdog rule can notice.

⭐⭐⭐ **It is a candidate answer to the design's own worst-marked open question**, which neither the
proposal nor this note went looking for. `rules-design.md`'s open list carries, at ⚠⚠⚠:

> **A HALF-FINISHED CHANGE IS INDISTINGUISHABLE FROM A FINISHED ONE, AND AN AGENT WILL ACT ON IT.**
> […] The design has a name for two entries that disagree, and **no name for a state that is halfway
> through a change.**

A transfer is necessarily two applications when a tool computes the amounts, and between them the
world holds twelve gold and never did — internally consistent, false, and **actionable**: an ordinary
economy rule reads the total and the agent emits `refuse_service(hero)`, measured, and §19 says an
emitted act cannot be forgone. A marker is exactly a name for *halfway through a change*. That does
not make it correct, but it means the proposal is answering a question the design already asked and
could not answer, which is a much stronger position than a preference about style.

⭐ **It may repair `supersedes`.** `HANDOFF.md:770` records it as too narrow: it defeats only
applications sharing a **consumed entry**, and two rules reaching one conclusion from different
premises share none — `<secret>` consumes `sealed(vault)`, the learned rule consumes `hinged(vault)`,
nothing is defeated, and the two oscillate forever. Two rules that both listen on the same marker
**do** share a consumed entry. That is a testable prediction, not a claim.

### ⚠⚠⚠ The technical trap that has to be settled first

**UGM has no functional dependency, so a state marker does not supersede its own predecessor.**

`resolve` (`chain.py:367`) is keyed on the **proposition node**, and `g.rel` interns by
`(relation, members)`. So `stage(<m>, new)` and `stage(<m>, handled)` are two different propositions,
and depositing the second leaves the first standing. *Both* hold. "Substituting" a node is not
something the floor does for you — the same lesson as §0's *nothing spends a premise for you*, one
construct along.

Three ways out, and they are not equally good:

| how | cost |
|---|---|
| write the denial in the same consequent — `{ -stage(?m, new), +stage(?m, handled) }` | ✅ works today, no engine change; ⚠ the author must remember, and forgetting fails **silently** — both states hold and both listeners fire |
| one relation per state — `noticed(<m>)` / `handled(<m>)`, listener guards on `-handled` | ✅ works today; ⚠ needs the negative written up front (§1's *write your negatives*), and the state space is now spread over N relations with nothing tying them together |
| declare the relation **functional in an argument** — `functional(stage, 2)` | a real engine feature; per §20 the declaration must be data and per Part 1 it must be a fact a rule can read. Buys automatic supersession and a place to hang a check |

⚠ **So the proposal does not repeal §0 — it relocates it.** You still must spend something; what
changes is that the thing you spend is always something you concluded, never something you were told,
so §0's dangerous half never comes up. That is a genuine improvement and it should be stated that way
rather than as *consumption is gone*.

### ⚠ The risks, stated plainly

1. ⚠⚠ **It re-creates phases by convention.** `nophases` deleted the interpreter's phases and
   `phases-to-rules` is recorded as load-bearing. A mandatory notice→mark→listen doubles the rule
   count and puts an ordering back — a corpus-level ordering rather than an engine one, and
   arbitration already orders, but the cost is real. **§20's test applies and should be run: does
   this add rows, or branches?**
2. ⚠⚠⚠ **The state names must not become engine vocabulary.** `ugm.vocabulary`'s central result is
   that all 101 reserved names are about the chain, the surface, rules-as-data, the agent's own
   deliberation, or the seam — **and not one is about a world**. `new` / `pending` / `handled` are
   world-shaped. If the engine ships them, that result is lost. The convention must be something a
   corpus authors, and the engine's contribution can only be the mechanism (functionality, if it goes
   that way).
3. ⚠ **Cost.** Two entries per event instead of one, and `resolve` is per proposition. The state gets
   bigger in exactly the dimension `ugm.state` measures. Worth a number before, not after.
4. ⚠ **"More robust" is currently an opinion.** It is a good one, and it is unmeasured. The fixture
   for it exists: `ugm.dungeon` — 21 rules, 3 tools, and the corpus that hit all three of §0's rows.
   Re-author it two-step and report rules, ticks, entries, and whether a round-417-class runaway
   becomes *detectable* rather than merely absent.

### Where this lands

**Opinion, marked as one:** the two-step is right and the engine change is the part to be slow about.
The convention can be written and tested with no engine change at all (row two of the table above),
and doing that first is what would tell us whether `functional` is worth building or whether the
guard-on-a-negative is simply enough. That order also matches this repository's own record — the
`unless` finding, where the feature turned out to be a name for something already built, and the
`precedence` finding, where the table was deleted because reading the graph cost 6.42s against 6.38s.

**Open questions, not yet answered:**

* Does the marker belong on the message, or is it the *entry* that has a state? The entry is already
  the unit of assertion and already lacks a readable licence (Part 1) — these may be one problem.
* Does `<intake>` itself deposit the starting state, and if so is that state engine vocabulary again
  (risk 2), or does the bundle name it and a corpus rename it?
* Two listeners on one marker is a conflict. Is that `supersedes` finally working, or is it a new
  conflict class for harmonization?

## 2.2 Negative conditions stated positively — a small state machine per property

> **The proposal.** Every negative condition should be marked explicitly. *Not poisoned* is not the
> absence of poison and not a denial of it — it is a **relationship a rule adds**. What you get is a
> small state machine for poisoning, and rules operate on that.

### What it gets right

⭐⭐⭐ **It attacks the failure `authoring.md` calls the most expensive one there is**, and the
document's own words are the argument for the proposal:

> §1 — `−` means *denied*, never *absent*. **This is the one that will cost you the most, because it
> fails silently — the rule simply never applies, and nothing anywhere says why.**

Today the remedy is either `fact -poisoned(b)` written by hand for every entity, or a rule that
derives the default. The proposal makes the second one the convention and swaps the denial for a
positive name, which is the same move as 2.1 one construct along.

⭐ **The transition becomes a place to hang rules, and a sign is not.** `-poisoned(x)` records that
poison does not hold; it cannot say *how it stopped*, so *cured* and *never afflicted* are the same
claim. A state machine distinguishes them, and that distinction is what a corpus about poison actually
wants to reason from. **This is the strongest argument for the proposal** and it is independent of
everything else here.

⭐ **Hypothesis, testable with an instrument that already exists.** A missing `-poisoned` is invisible
to static analysis because `+poisoned` and `-poisoned` are the same relation name — `ugm.atlas` maps
*which relations can ever be grounded*, and the sign is not in the name. A positive state vocabulary
puts the sign **into the name**, so `healthy` with no producer becomes an ordinary ungrounded relation
that atlas already reports. If that holds, the proposal converts §1's silent failure into an existing
instrument's existing output, at zero engine cost. ⚠ Not yet checked — atlas may or may not key on
sign; check before relying on it.

⭐ **It does not fight inheritance, it uses it.** Silence means *inherit from the predecessor*, so
`healthy(b)` carries forward until something supersedes it, exactly as `-poisoned(b)` would. Nothing
about the frame problem gets worse.

### ⚠⚠ What it costs

1. ⚠⚠ **Two ways to say one thing.** After this there are two surfaces for *b is not poisoned* —
   `-poisoned(b)` and `+healthy(b)` — and this design refuses that elsewhere on principle: a
   degenerate span is rejected because *two ways to say one locus is exactly the ambiguity the read
   cannot afford*. The three signs of §9 are a floor primitive; a convention that makes corpora stop
   using `-` does not remove it, it leaves it as a second, unused, still-matchable channel. **That is
   a real cost and the proposal should own it rather than route around it.**
2. ⚠ The same goes for `?`. *Unknown poison status* is `?poisoned(x)` today and would become a state,
   so §9's third sign gets the same treatment as the second.
3. ⚠ Population. Every property becomes a pair or a family, and every entity needs its starting state
   asserted. That is `-poisoned(b)` written by hand again under a different name — **unless** the
   starting state is derived by a rule, which is the version of the proposal worth testing.

### ⚠⚠⚠ And it hits the same wall as 2.1, harder

`poisoned(b)` and `healthy(b)` are two propositions, so **concluding the second does not retract the
first** — `resolve` is keyed on the proposition node and `g.rel` interns by `(relation, members)`.
Both hold. A state machine whose states can all hold at once is not a state machine.

So the convention needs, per transition, either an explicit `-poisoned(?x)` in the same consequent —
which is the denial the proposal set out to replace, now written twice — or the missing engine
notion. That is not a reason to reject the proposal. It is the reason both proposals are one
proposal.

## 2.3 What 2.1 and 2.2 add up to

⭐⭐⭐ **Both reduce to a gap the design has already named three times, under a name that already
existed: `refutes`.**

| where | what it says |
|---|---|
| `rules-design.md` §8 | "⚠ **And there is no vocabulary for incompatibility.** You can deny a proposition; you cannot say that two propositions cannot both hold. That is a real gap, noticed when an older engine's `refutes` had nothing to port to." |
| `rules-design.md` open questions | the same, listed as outstanding |
| `harmony.py:13-15` | "the one incompatibility the floor can already express: `-p` IS the negation of `p`, and what cannot be said is that two *distinct* propositions are incompatible (`sitting(x)` against `standing(x)`). That relation — `refutes` — did not survive the restart." |

`refutes` was in the pre-restart engine and was deliberately not ported, because nothing in the new
floor had a place for it. These two proposals are the first concrete demand for it that comes from
**authoring** rather than from tidiness — and they arrive with a fixture (`ugm.dungeon`), a measured
failure mode (round 417 / the two channel hangs), and an open design question it would close
(half-finished change).

⚠ That does **not** mean *build `refutes`*. It means the next step is to decide which of these three
the demand is actually for, because they are not the same feature:

| candidate | says | reach |
|---|---|---|
| `refutes(p, q)` | these two propositions cannot both hold | general, symmetric, and needs a policy for what happens when both are asserted anyway |
| `functional(<rel>, <arg>)` | this relation has one value in this position, so a new one supersedes the old | narrower, exactly fits both proposals, and is a **declaration** rather than a claim about the world |
| nothing — write the denial | ✅ works today, no engine change | costs an author a member they can silently forget |

⚠ And per Part 1 §1.5, whichever is chosen must be a **fact a rule can read**, not a Python
registry — or this audit gets a new entry the day it ships.

**Opinion, marked as one:** row three first. Author the convention in the dungeon with the denial
written out, measure it, and see whether the forgettable member actually gets forgotten. This
repository has twice found that the feature was already built and only needed a name (`unless`) or
that the kept table was buying nothing (`precedence`, 6.42s against 6.38s). It is cheap to find out
which this is.

## 2.4 Closure as a layer — rules that close the world, then rules that act on it

> **The proposal.** There must always be rules that **close** the world, and then *separate* rules
> that act on the explicitly closed world.

This is 2.2 generalised into a discipline, and it is the strongest of the three, because it names the
thing the other two only imply: **a corpus should be two layers, and the boundary should be visible.**

### ⭐ First, what it is not

⚠⚠⚠ **This is not the closed-world assumption, and the difference has to be stated before anything
else, because reading it as CWA would destroy the design's central property.** The floor stays open —
`−` still means denied and never absent, `?` is still a claim and not a silence, and
`ugm.vocabulary`'s result stands: you can write a proposition before you can give it meaning, and the
price is that a proposition awaiting meaning is indistinguishable from a typo. What the proposal
closes is **a corpus's own world, explicitly, by writing the rules that do it** — so closure becomes a
dated, attributable, deniable set of claims instead of a semantics. That is strictly the design's own
move: the free thing becomes the arguable thing (grades → `likely`, spans → `during`, precedence →
read from the graph).

### ⭐⭐⭐ The engine already knows why this is right, and already paid for the lesson

`RuleSet.strata()` (`rules.py:291`) carries it, about the skeleton layer:

> ⚠⚠⚠ **Negation makes the ORDER load-bearing, and structure cannot be taken back.** `best` is *a
> candidate nothing beats*. Applied before `beaten` has finished deriving, it mints a fact that is
> wrong and that nothing can deny — a skeleton fact has no sign, which is the whole point of it. An
> entry would merely be superseded; this is permanent.

That is the proposal's failure mode exactly, one layer down and already measured: **an action rule
that runs before closure completes acts on a world that is not yet closed.** For structure the result
is a permanent wrong fact; for ordinary rules it is a `causes` conclusion or — worse, and already
recorded at ⚠⚠⚠ — an **emitted act**, which §19 says cannot be forgone. Same shape as the
half-finished-change finding in 2.1.

⭐ And §6's stratification is **derived, not assigned** — *every antecedent member is structural* is a
property computed by inspecting antecedents, a fixpoint from below. So this design's answer to "which
layer is this rule in" is already *compute it, do not declare it*, and any closure discipline should
be held to the same standard before it is allowed to be a declaration.

### ⚠ The gap this exposes

**The engine stratifies structure and does not stratify anything else.** `strata()` orders stratum-0
rules into layers that must run in order. Ordinary rules have no such notion — they are ordered by
arbitration (preference, `_priority`, `_choose`), and defeated by `overrides` / `supersedes`, and
`authoring.md` §2 measured both of those as the wrong instrument for this: `overrides` is per tick and
per rule, so it takes out every entity at once, and `supersedes` needs a shared consumed entry.

**So today a corpus cannot say *finish closing before you start acting*.** That is the concrete gap
the third proposal opens, and it is a better-specified request than either of the first two.

### ⭐⭐⭐ …except that it may already be authorable, with no engine change

`dormant(<rule>)` / `due(<rule>)` (`machine.py:318`, read from the graph at `machine.py:1458,2907`,
surface-named at `machine.py:519`) gate **recall**: a rule claimed dormant is not proposed at all
until something claims it due. Both are ordinary corpus facts — askable, defeasible, attributable.
That is a per-rule gate on whether a rule is even considered, which is precisely the lever the
proposal needs:

```
fact dormant(<act-rule>)                       -- the action layer starts closed off
rule <opened> = implies( { +closed(poison) }, { +due(<act-rule>) } )
```

⭐ And it is known to be cheap: `dormant` is on record as **14.5× from one corpus line**.

⚠ What is *not* supplied is the antecedent of that rule — **what concludes `closed(poison)`**. It
cannot be quiescence: quiescence is global and it is the machinery's, and §0 already warns that
quiescence catches none of the runaway cases. It has to be a corpus predicate — *every creature has a
poison state* — which means the corpus must be able to quantify over its own extent.

### ⚠⚠ What the proposal therefore requires and does not yet say

1. **An extent to close over.** *If not bitten then healthy* is only writable for a `?x` drawn from
   somewhere; the corpus has to name its universe (`creature(?x)`) and keep it complete. Closure is
   bounded quantification, and the bound is the corpus's to supply and to be wrong about.
2. **A completeness claim, and it is a claim.** `closed(poison)` asserted by a rule is defeasible and
   can be wrong — which is correct and is the point, but it means *the world is closed* joins the list
   of things this design makes arguable rather than free.
3. **The word "always".** Every property acquiring a closure rule is a real cost in corpus size, and
   the honest version is probably *always for anything an action rule reads negatively* — which is
   checkable statically, and is the kind of thing `ugm.atlas` or a new gate could report rather than
   an author remembering.

**Opinion, marked as one:** this is the proposal to test first, ahead of 2.1 and 2.2, because
`dormant`/`due` means it can be tested with **no engine change at all** and it is the one that
subsumes the others — a marker (2.1) and a positive state (2.2) are both just what a closure layer
writes. The experiment is the dungeon: split its 21 rules into a closure layer and an action layer,
gate the second on `due`, and report rule count, ticks, entries, and whether the §0 failures become
impossible or merely unlikely.

## 2.5 The unifying claim — everything has an implicit state machine

> **Put another way: EVERYTHING has an implicit state machine.**

2.1, 2.2 and 2.4 are one proposal, and this is it. The claim is not that state machines should be
added; it is that **they are already there, and the only question is whether they are written down.**

### ⭐⭐⭐ The audit is the evidence, and it was collected before the claim was made

Part 1 went looking for Python-only fields with no idea this framing was coming. Look at what it
found:

| leak | states | where the state machine lives today |
|---|---|---|
| `Frame.state` | `discharged` / `exhausted` / `abandoned` | ⚠⚠⚠ **a bare Python string** |
| `Step.state` | `applied` / `supposed` / `widened` / `quiet` / `quiescent` / `nothing-matched` | a bare Python string |
| `Rule.connective` | `causes` / `implies` | a Python string, branched on at `machine.py:3141,3176` |
| `Entry.mention` | use / mention | a Python bool |
| `Moment.licence` | time / derivation | a Python field, ⚠ **never read** |

Every single one is a state machine. Not one of them is in the graph. **The claim predicted the
inventory.** That is the strongest thing that can be said for a design heuristic — it found things
before anyone was looking for them.

⭐⭐⭐ And `_bookkeeping` (`machine.py:660`) is the engine's own admission: a **50-name Python set** of
propositions that are about process state rather than about a world — `goal` / `achieved` / `blocked`,
`open` / `enough` / `stopped`, `dormant` / `due`, `pursued`, `defeated`, `unsupported`, `excluded`,
`forbidden`, `reified`. That list *is* the engine's state machines, enumerated, in Python, as a closed
set no corpus may extend.

### ⭐⭐⭐ The other half of the evidence: the ones that are in the graph all work

| in the graph | outcome on record |
|---|---|
| `dormant` / `due` | **14.5× from one corpus line** |
| `may(x, r)` — a right that acting spends | the fix for §0's third and hardest row |
| `standing` | made *which rules always come to mind* a query a corpus can edit |
| `defeated(<loser>, <winner>)` | closed §21's defect for the tenth time |
| `goal` / `achieved` / `blocked` | the whole backward reader, after the phase was deleted |

**Wherever this engine has put a state machine in the graph it works and is cheap. Wherever it has
left one in Python it is an entry in Part 1's inventory.** That is not a proof — it is a correlation
across about a dozen cases with no counterexample yet found, which in this repository is enough to
act on and not enough to stop measuring.

### ⭐⭐ It reframes the signs, and dissolves 2.2's worst cost

§9's three signs — `+`, `−`, `?` — are **a built-in, universal, three-state machine over every
proposition**. Seen that way, 2.2 is not adding a second way to say *b is not poisoned* next to the
first; it is **refining the built-in machine into a corpus-defined one with more states and named
transitions**. `-poisoned(b)` and `+healthy(b)` are not rivals — the second says which of several ways
the first came about, which is exactly the thing 2.2 identified as its own strongest argument.

⚠ This weakens 2.2's ⚠⚠ cost but does not delete it: two surfaces still exist, and a corpus that
uses both inconsistently still gets an ambiguity. What changes is that the remedy is a **convention
about refinement**, not a prohibition.

### ⭐⭐⭐ And it answers the question Part 1 §1.5 left open

§1.5 asked which of three remedies each leak should get and said the decision had to be made before
any code was touched. This framing decides it:

> **Make the state machine explicit in the graph. Then the remedy follows from the transition: if the
> transition is *asserted*, it is an occasion (an entry — dated, deniable). If it is *structural* —
> nobody asserted it, it could not have been otherwise — it is a skeleton relation. An answerer is
> neither and is only ever a door onto a machine that is still in Python.**

Applied to the inventory: `Entry.licence` and `Entry.source` are structural (nobody asserted that this
rule licensed this entry; it is how the entry was made) → **skeleton**, `rests_on`'s shape.
`Frame.state` is asserted (the agent *decided* to abandon that supposition) → **occasion**.
`RuleSet.composed_from` is structural → skeleton, and its answerer is revealed as the half-measure it
was. That is a rule that decides all ten cases, and it comes from the proposal rather than from
taste.

### ⚠⚠ The limits, stated

1. ⚠⚠ **"Everything" is unfalsifiable as written.** A heuristic that cannot fail cannot be tested, and
   this repository has a standing finding about checks that stopped being able to fail. The
   falsifiable version is narrower and better: *wherever this codebase branches on a Python string or
   bool, there is a state machine that belongs in the graph.* That is checkable — grep — and §1.2 is
   the first pass of it.
2. ⚠⚠ **§20's test has not been run on it.** The design's standing test is that a new construct adds
   **rows, not branches**. Making state machines explicit plausibly adds rows everywhere; it must be
   confirmed it adds no branches, and the closure discipline of 2.4 is exactly where a branch would
   hide.
3. ⚠ **It is a modelling discipline, not a representation.** Nothing here says every proposition needs
   a state node — the signs already are its state machine. The claim is about where the *transitions*
   are written, and conflating the two would produce an enormous and useless state space.
4. ⚠ It is not novel, and per the repository's standing convention that is worth saying rather than
   discovering later: explicit fluents with named transitions against implicit negation is the
   situation-calculus/event-calculus argument, and *make the lifecycle a first-class object* is the
   ordinary advice of state-chart modelling. **The discipline is the claim, not the idea** — the same
   sentence `ugm.vocabulary` had to write about the open class.

### Where all four proposals now stand

| | proposal | engine change needed | test that would settle it |
|---|---|---|---|
| 2.4 | closure layer, then action layer | ⭐ **none** — `dormant` / `due` | split the dungeon in two; count rules, ticks, entries |
| 2.2 | negatives stated positively | none (write the denial) | does the forgettable member get forgotten? does `ugm.atlas` catch it? |
| 2.1 | state markers instead of consumption | none (write the denial) | does §0's channel exception disappear? does `supersedes` start working? |
| 2.5 | all of the above, as one discipline | — | §20: rows, not branches |
| — | `functional(<rel>, <arg>)` or `refutes(p, q)` | **yes** | only after the three above show the denial actually gets forgotten |

⭐ The order is the same one this repository has been right with twice: author the convention, measure
it, and only then decide whether the engine owes it a primitive. `unless` turned out to be a name for
something already built; the precedence table turned out to be buying nothing (6.42s against 6.38s).
The cheapest possible next step — 2.4 in the dungeon, no engine change — would tell us a great deal
about all four.

## 2.6 MOST, not everything — mutually exclusive families, and default completion. **Measured.**

> **The refinement.** Take "everything" with caution. **Most** of the world is mutually exclusive
> states (`poisoned` / `healthy`) that a dedicated cluster of rules can manage, and we should leverage
> that for **completion** and **silence detection**. We missed it because we take it for granted: a
> person without legs cannot walk, and when talking about a person we **assume** legs unless stated
> otherwise. People unconsciously complete information in the most probable way, and the agent should
> too — **without the fuss and paranoia of a theorem prover tracking every assumption.**

⚠ Terminology: "island" here means a cluster of rules governing one exclusive family. That is *not*
the sense in `islands-not-parsing-gaps.md`, where an island is a code seam created by the second
caller. Two meanings, one word — worth keeping apart before either gets written into a design.

### The stance is already this design's stance

`agent-not-theorem-prover` is a standing finding; monotonicity was dropped on purpose; `−` is a claim
and not a failure to prove. So *complete in the most probable way and get on with it* is not a
departure — it is what the floor was built for.

⭐⭐⭐ **And the paranoia the proposal wants to avoid is not the tracking.** Provenance is already
recorded for free, by the machinery, at no cost to an author: every entry carries what it consumed,
and `rests_on` is in the graph. What makes a system paranoid is not recording support — it is
**acting** on it automatically, TMS-style, retracting everything downstream the moment a premise goes.
This design already refused that: `unsupported(p)` is an **occasion**, and what to do about it is a
corpus's business — *losing your reason is not acquiring a counter-reason*. So the agent can have
full provenance and zero fuss simultaneously, and that is built, not proposed.

### ⚠⚠⚠ But the default itself does not work today. Three runs.

The proposal's own example, written the obvious way:

```
rule <legs> = implies( { +person(?x) }, { +has_legs(?x) } )
rule <walk> = implies( { +has_legs(?x) }, { +can_walk(?x) } )
fact +person(ann)
fact +person(bob)
fact -has_legs(bob)                        # the exception, stated outright
```

| | result |
|---|---|
| ticks | 6, **ended quiescent** |
| `has_legs(ann)` | `+` ✅ |
| `has_legs(bob)` | **`+`** ❌ |
| `can_walk(bob)` | **`+`** ❌ |

⚠⚠⚠ **The default silently ate the stated exception**, and the agent concluded a legless person can
walk. The entries show exactly why:

```
-  has_legs(bob)   licensed by loaded(has_legs(bob))
+  has_legs(bob)   licensed by applied(<legs>)
```

`resolve` breaks ties by **latest deposit**, and a derived conclusion is always deposited after a
loaded fact. So **a default rule beats a stated exception, always.** Note this is not oscillation and
not the runaway of §0 — it is quiescent in 6 ticks with nothing to see. It is the same class as the
half-finished-change finding: *internally consistent, false, and actionable.*

⚠ And it is the **reverse** of the failure `authoring.md` §1 warns about. §1 says the rule you wrote
will silently never apply. This one silently applies and eats the exception. **The document warns
about one direction and the other is just as available.**

Adding the closure layer of 2.4 naively does not help — it reproduces the defect one level up:

```
rule <close> = implies( { +person(?x) }, { -amputee(?x) } )
rule <legs>  = implies( { +person(?x), -amputee(?x) }, { +has_legs(?x) } )
fact +amputee(bob)
```

→ `amputee(bob)` = **`-`**. 6 ticks, quiescent. The closure rule ate the stated exception in turn.

### ✅ What does work — and it is the proposal, exactly

```
fact -veteran(ann)                                            # the leaf, stated by hand
fact +veteran(bob)
rule <close> = implies( { +person(?x), -veteran(?x) }, { -amputee(?x) } )
rule <hurt>  = implies( { +veteran(?x) },              { +amputee(?x) } )
rule <legs>  = implies( { +person(?x), -amputee(?x) }, { +has_legs(?x) } )
```

| | |
|---|---|
| ticks | 5, quiescent |
| `amputee(ann)` / `amputee(bob)` | `-` / `+` ✅ |
| `has_legs(ann)` | `+` ✅ |
| `has_legs(bob)` | `None` ✅ — *unknown*, not *denied*: the right silence |

⭐⭐⭐ **So default completion is writable today, and it is writable only under this proposal's
discipline.** The default rule must be guarded by the exception; the exception vocabulary must itself
be closed; and the regress bottoms out in hand-written negatives at the leaves. That is a much
stronger result than "the proposal would be tidier" — **without the explicit closure, defaults are
not merely inelegant, they are wrong and silent.**

### ⚠⚠ And it names the real cost, which is exactly what the proposal set out to remove

The working version needs `fact -veteran(ann)` — **one explicit negative per entity per exception
vocabulary**. That is O(entities × exceptions) of hand-written closure, and it is the fuss the
proposal wanted to avoid. The proposal is right that people do not do this; what the measurement adds
is that the engine currently requires it.

⚠⚠⚠ **CORRECTED IN §2.7 — read that before relying on the paragraph below.** What follows names
`root`/`blocked` as the engine's only pattern for a negative existential. That is wrong: negation as
failure already exists on **structural** members, and `rules-design.md` carries a measured example of
a default over an open domain built from it. The paragraph is kept because the correction is the
finding.

⭐⭐⭐ **What is actually missing is a negative existential, and the engine already has exactly one
pattern for it.** *Nothing says ann is a veteran* is not `-veteran(ann)`; it is *for no entry*. §12 is
explicit that a `−` member cannot express this, and `machine.py:93-98` records the engine's own
remedy when it hit the same wall for root goals:

> a root goal is a `goal(?w)` with **no** `subgoal(?p, ?w)`, which is a negative existential, and a
> `-` member says *an entry denies this*, never *for no ?p*. So it gets the treatment `blocked` got —
> **a REQUEST the machinery answers by looking**, because an aggregate over what the rules produced is
> the machinery's business and not a rule's.

`root` / `rooted` and `blocked` are that pattern, shipped and working. **Default completion and
silence detection are the same shape**: an aggregate over what the rules produced, which the
machinery can answer and a rule cannot ask. That is a third candidate primitive alongside `refutes`
and `functional`, it is the one with a working precedent in this codebase, and it is the one that
would delete the hand-written leaves rather than merely organise them.

⚠ It also inherits that pattern's known price: an answer from an aggregate is only as good as the
moment it was asked at, and §6's quiescence rules govern when it may be asked. That is not an
objection — it is where the next measurement goes.

### ⚠ The exclusive family is still the missing declaration

Nothing above needed `refutes`, because the working corpus used the sign for exclusion — `+amputee` vs
`-amputee` is the built-in two-state machine of §9. The declaration becomes necessary at **three or
more** states (`poisoned` / `healthy` / `immune`), which is where the proposal is aimed and where the
2.1/2.2 wall bites: three propositions, all of which can hold at once. ⭐ A **partition**
declaration — this family is exclusive *and* exhaustive — would close both gaps with one construct:
exclusivity fixes 2.1 and 2.2, and exhaustiveness is what makes `closed(poison)` derivable rather
than asserted in 2.4.

**Opinion, marked as one:** partition is now the most promising engine-level candidate of the three,
ahead of `refutes` (too general, needs a policy for what happens when both are asserted anyway) and
`functional` (right shape, but says nothing about completion). It should still be tested last — after
2.4 in the dungeon, and after somebody tries to write a three-state family by hand and reports what
broke.

## 2.7 Closed **by defaults** — and the two kinds of "all"

> **The refinement.** Neither CWA nor OWA: what people actually operate on is **closed by defaults**.
> The assumptions are defeasible, but they are so common that the system should be built around them.
> *People have legs* is really *people USUALLY have legs*; *triangles have 3 sides* is *ALL triangles
> ALWAYS have 3 sides*. So **exceptions should be a first-class concept** — a rule that applies to the
> default, with `unless` in its antecedent.

### ✅ The mechanism is built, and this is the third time that has been the answer

`unless` in the antecedent **is** a negated member. `unless-was-a-name-not-a-gap` recorded it —
*"unless is if not"*, built since there were members, zero engine written — and §2.6's working corpus
is it: `implies( { +person(?x), -veteran(?x) }, { -amputee(?x) } )`. `rules-design.md` says the same
in one line: *"if not over a proposition the corpus can name is a negated member."*

⭐ So the proposal's mechanism needs nothing. What it needs is everything around it, below.

### ⭐⭐⭐ The design already contains **both** assumptions. It partitions them by LAYER, not by relation.

This is the correction to §2.6 and it is the most important thing in this section.
`rules-design.md`, on a default over an open domain:

> ⭐⭐⭐ **AND IT IS NOT MISSING EITHER — it needed a STRETCH, not a negation.** […] **A `-` on a
> structural member has meant *not derived* since the matchers merged, so negation as failure was
> never the missing piece.**

with a measured corpus — `round_span` / `silent` / `hero-acts`, layers derived and not assigned —
where *the player declared nothing this round* is a real default over an open domain, and the rule
withdraws the moment one word is said.

So:

| layer | `−` means | assumption |
|---|---|---|
| **structural** (§6 stratum 0 — `pred`, `anc`, `in_delta`, and anything a stratum-0 rule concludes) | *not derived* | ⭐ **closed world** |
| **entries** (everything a corpus asserts) | *denied* | **open world** |

⭐⭐⭐ **Both assumptions already ship. The engine chooses between them by asking what a rule reads.**
"Closed by defaults" is asking for the same choice to be made **per relation, or per exclusive family,
by the corpus** — which is a far smaller request than adding a semantics, and a far better-posed one
than anything in 2.1–2.6.

### ⭐⭐ And *usually* vs *always* maps onto the same partition

The proposal's two kinds of universal are already two things in this engine:

| | | |
|---|---|---|
| *ALL triangles ALWAYS have 3 sides* | definitional; it cannot be denied, and denying it is an error rather than a claim | **structural** — `strata()`: *"structure cannot be taken back"* |
| *people USUALLY have legs* | a claim; dated, attributed, deniable, and the exception is ordinary | **an entry** |

⚠ **The limit, and the design states it itself**: stratum membership is *derived* from what a rule
reads, not chosen — and *"a corpus relation cannot be structural"*, because reading one stops a rule
being stratum 0. So a corpus can write the *usually* half and **cannot** write the *always* half. That
is the gap, stated more precisely than "make exceptions first-class": **the corpus can author
defeasible rules and cannot author definitions.**

### ⚠⚠⚠ The gap §2.6 measured is still real, and it is now diagnosable

`<legs>` beat `fact -has_legs(bob)` because both are entries and `resolve` breaks the tie on **latest
deposit**. §4 says why that ordering exists:

> among claims about the same time, **the agent's current view wins over what it used to think**.

That is *revision*, and it is right for revision. **A default is not a later view — it is a weaker
view that happened to be computed later.** With grades deleted there is no notion of weaker, so
**timing stands in for strength, and it gets it backwards**: the derived default is always deposited
after the stated fact, so the default always wins. That single sentence explains all three §2.6 runs.

### ⚠⚠ The tempting fix is the one this repo already deleted

Marking a rule *defeasible* is `@likely` returning. `there-are-no-grades` deleted `GRADES`, `weaker`
and `effective_grade` and the finding was that the grade was **carried, composed, printed and never
obeyed** — this repository's own *read and not obeyed* defect arriving at the floor. Any new
rule-level strength annotation has to answer that, and *"this time it will be obeyed"* is not an
answer. ⭐ The design-consistent forms are the two the partition already offers: **wrap the
conclusion** (`likely(p)`, a proposition a corpus can argue with), or **lift the definition into the
structural layer** (unarguable by construction, which is what a definition is).

### ⚠ Not novel, and worth saying now rather than discovering later

This is defeasible logic — strict rules against defeasible rules, with defeaters — and Reiter's
default logic, where the *justification* of a default is literally `unless`. Both are well worked out,
and both have a standard answer to default-vs-exception that this design has not considered:
**specificity** — the more specific rule wins, computed rather than declared (birds fly, penguins do
not, nobody writes a precedence). ⭐ *Derived, not assigned* is exactly this repository's stated
preference for §6's strata, so specificity deserves scoring against `unless`-by-hand before either is
built. Per the standing convention: **the discipline is the claim, not the idea.**

### The one thing to measure next

A prediction worth falsifying, cheap: **take §2.6's failing corpus and lift the default into the
structural layer instead of guarding it.** If a stratum-0 rule can conclude the default, then `-` on
it means *not derived*, the stated exception is visible to it, and the hand-written leaf
(`fact -veteran(ann)`) disappears. If it cannot — because `person(?x)` is an entry and reading it
drops the rule out of stratum 0 — then the gap is exactly *a corpus cannot author a definition*, and
that, not `refutes` and not `functional`, is the engine change these five sections have been
circling.

## 2.8 `usually` unmarked, `always` marked — and no hypothesis per default

> **The proposal.** Specificity makes some contradictions unsolvable, and it is **not a total order** —
> sometimes you cannot say which rule is more specific. So: treat **all affirmations as *usually* by
> default**, and use **`always`** to mark universally valid truths. And genuinely do **not** create an
> explicit hypothesis or assumption for every *usually* — unless stated otherwise, a *usually* rule is
> simply **what we believe to be true**.

### ✅ The objection to specificity is correct

It is a **partial** order. Two rules whose antecedents are incomparable have no specificity relation
at all — the standard case is the Nixon diamond (*Quakers are pacifists*, *Republicans are not*, and
Nixon is both), where nothing is more specific than anything and the formalism gives no answer. §2.7
floated specificity as *derived not assigned* and this is the right rebuttal: derived is worthless if
the derivation is undefined on the cases that matter. Struck.

### ⭐⭐⭐ "Do not create a hypothesis per default" is the load-bearing half, and it is right

This is the part to keep even if everything else in the section is dropped.

* It refuses the wrapper. `likely(has_legs(bob))` for every defaulted conclusion means every
  downstream rule matches through a wrapper, every conclusion nests
  (`likely(likely(…))` — the cost `there-are-no-grades` accepted knowingly), and the state roughly
  doubles in the dimension `ugm.state` measures.
* ⭐ It is **already this design's posture**. The agent does not eagerly track what rests on what in
  order to retract it: `unsupported(p)` is an **occasion**, and *losing your reason is not acquiring a
  counter-reason*. Believing a default plainly, and dealing with the exception when it arrives, is the
  same stance one construct up. The provenance is still recorded — free, by the machinery — it is
  simply not **acted on** automatically. That is the whole of "without fuss or paranoia", and it is
  built.
* ⚠ And it is what makes the proposal cheap rather than a second semantics: the unmarked case gets
  **no syntax at all**. `always` is one new name — `ugm.vocabulary` counts 102 reserved today, and
  both `always` and `usually` are free.

### ⭐⭐ `always` marked / `usually` unmarked also inverts the burden the right way

Definitions are rare; defaults are the bulk. Marking the rare one means an author writes nothing for
the common case and cannot get it wrong by omission — which is the opposite of `authoring.md` §1,
where the silent failure comes precisely from what an author did not write.

### ⚠⚠⚠ But the proposal alone does **not** fix §2.6, and it is worth seeing why

If every rule is *usually*, then `<legs>`'s `+has_legs(bob)` and the stated `fact -has_legs(bob)` are
the **same strength**, so deposit order still decides and the default still eats the exception. The
conflict in §2.6 is not *default against definition*. It is **derived against told**.

⭐⭐⭐ **And the discriminator already exists on every entry — as Part 1's number-one leak.** The probe
printed it:

```
-  has_legs(bob)   licensed by loaded(has_legs(bob))
+  has_legs(bob)   licensed by applied(<legs>)
```

`Entry.licence` is exactly *told* versus *inferred*, it is recorded on every entry at no cost to
anyone, and **no rule can read it** (§1.2, §1.3). So the audit and the proposal meet: the top finding
of Part 1 is the blocker for the top proposal of Part 2. *What I was told outranks what I worked out*
is a one-line arbitration rule that cannot be written today, and could be the day `licence` becomes a
skeleton relation.

⚠ **It is not universally right, and must not be built as a law.** An agent told something stale, that
then infers something from fresher evidence, wants §4's ordering and not this one. Which is the real
shape of the problem:

> ⭐⭐⭐ **There is one axis doing two jobs.** `resolve` orders by time, and time is being asked to
> carry both **revision** (my current view beats my former view — correct) and **strength** (a stated
> fact beats a derived default — currently backwards). Grades were the second axis and were deleted
> for never being obeyed. The question this proposal actually raises is whether the second axis comes
> back, and in what shape.

### ⭐⭐ What shape survives the grades objection

`there-are-no-grades` killed an **ordinal that composed on every write and was never obeyed**. The
proposal's `always` is not that: it is a **binary kind, consulted at defeat**, with nothing to compose
and no weakest-link arithmetic. That is the shape that survives — and it points at where it belongs:

⚠ **`always` should mean *this rule cannot be defeated while its premises hold* — not *its conclusion
is permanent*.** The distinction matters and it is the one thing this section is most confident about:

* *All triangles always have 3 sides* is permanent.
* *`a` has 3 sides* is **contingent on `a` being a triangle**, and must stay deniable by denying that.

So `always` cannot mean "conclude into the structural layer" as §2.7 suggested, tempting as that was —
a skeleton conclusion resting on a deniable premise is precisely `strata()`'s ⚠⚠⚠ (*a fact that is
wrong and that nothing can deny*), and §2.7 walked into it. **Corrected here.** `always` is
defeat-immunity, so it belongs in **arbitration**, beside `overrides` and `supersedes`, and not in the
chain.

⚠ Which also means it inherits arbitration's known problems rather than escaping them:
`authoring.md` §2 measured `overrides` as per-tick and per-rule and `supersedes` as needing a shared
consumed entry. An `always` that is per-rule-per-tick would take out every entity at once, exactly as
`overrides` does. **That is the first thing to test, not the last.**

### Where this leaves the five sections

| | claim | status |
|---|---|---|
| `unless` in the antecedent | ✅ built, three sources agree | nothing to do |
| no hypothesis per default | ✅ right, and already the design's posture | adopt as stated policy |
| `usually` unmarked | ✅ right, and free | adopt |
| specificity | ❌ partial order, undefined where it is needed | struck |
| `always` = structural | ❌ skeleton resting on a deniable premise | struck (§2.7's suggestion, corrected here) |
| `always` = defeat-immunity in arbitration | ⭐ the surviving candidate | ⚠ test against `overrides`' per-tick collateral **first** |
| told-beats-inferred | ⭐ one line, unwritable today | blocked on `Entry.licence` — **Part 1, finding 1** |

⭐ The two cheapest experiments are unchanged and now better aimed: **(a)** make `licence` readable and
see whether *told beats inferred* fixes §2.6 in one rule; **(b)** §2.4's closure split in the dungeon.
Neither needs `refutes`, `functional`, partitions, or grades.

## 2.9 Settling ordering vs authority

> **The decision.** Authority is the **first** criterion. Within the same authority, **order** applies.
> Order of arrival is the only thing that allows **clarifications**.

### ⭐⭐⭐ This is already the design's rule — and only for rules

`rules-design.md` states the arbitration order outright:

| | |
|---|---|
| **authority** | `overrides`, **applied first as defeat** — a claim about who decides, and no amount of *this usually works* may outrank it |
| **apparatus** | a `standing` rule keeps its authored place |
| **helpfulness** | what the situation recommends |
| **authoring** | the order they were written in |

Authority first, order last. **The proposal is not a new principle — it is the design's settled
principle, and the observation is that it was only ever applied in one of the two places a conflict
can be decided.**

### ⭐⭐⭐ The finding: there are two orderings in this engine and they disagree

| | decides between | ordering |
|---|---|---|
| `arbitrate` (§14) | two **rule applications** | ⭐ authority → apparatus → helpfulness → authoring |
| `resolve` (§4) | two **entries about one proposition** | ⚠ locus, then deposit, then position — **time only** |

§2.6's defect falls entirely to the second. A loaded fact against a derived entry is **not two rule
applications**, so arbitration never sees it, and the only arbiter is `resolve` — which has no notion
of authority and never did.

> **Restated precisely: give `resolve` the ordering `arbitrate` already has.**

That is a much smaller and better-grounded request than a new axis. It is not *add authority to the
design*; it is *stop having two answers to the same question.*

### ✅ "Order allows clarifications" is exactly what the design already relies on

§4's second ordering is *among claims about the same time, the agent's current view wins over what it
used to think* — which is clarification, stated as the reason. And arbitration's last row is
`authoring`, the same idea for rules. ⭐ **The proposal preserves both and subordinates them**, which
is why it is a refinement rather than a reversal: nothing that works today stops working, a case that
is currently decided by accident starts being decided on purpose.

### ⚠ What must not be re-fused: channel is not authority

Already settled, and worth restating because *authority* will tempt an implementation toward `source`:

| | can it be wrong |
|---|---|
| **channel** — the intake path, socket, sensor, KB | **no** — mechanically observed |
| **authority** — who is taken to have spoken, and what their word is worth | **yes** — an ordinary claim, defeasible |

> Fusing the two would make authority **unforgeable by fiat**, so that anyone reaching the right
> socket would thereby be the boss.

So authority may not be read off `source`. It is a *claim about* a source, and it has to stay
deniable. ⚠ Note the design names `by(<R>, boss)` for this and **the engine does not have it** — `by`
is not in `Machine.reserved`; only the already-derived `overrides` / `supersedes` pairs exist. That
gap is now load-bearing rather than cosmetic.

### ⚠⚠ The proposal's own objection applies to the proposal

§2.8 struck specificity for being a **partial** order, undefined exactly where it is needed. Authority
is partial too: two channels, two speakers, two rules with no declared relation between them. So the
rule needs a third row, or it has an undefined case:

> authority, **then order — for claims of the same authority *and* for claims whose authorities are
> incomparable**.

"Same" is not enough. Most pairs will be incomparable, not equal, and that is the common path rather
than a corner.

### ⚠⚠⚠ And authority-first **still does not fix §2.6** on its own

Run the corpus against the proposed rule. `-has_legs(bob)` arrived from the KB; `+has_legs(bob)` is
licensed by `applied(<legs>)`. Nothing claims an authority for either. So they are incomparable →
order applies → **the default still wins**.

⭐⭐⭐ **The missing piece is §2.8's `usually`, and it fits here as the same axis rather than a second
one.** *Usually* is not a strength annotation on a conclusion — it is **a low authority claim about a
rule**. Put rules and speakers on one authority order and the whole thing collapses to one mechanism:

| source of a claim | authority |
|---|---|
| an `always` rule | maximal — *no amount of "this usually works" may outrank it* (the design's own words) |
| a named speaker | whatever the corpus claims for them, defeasibly |
| direct assertion through a channel | the speaker's |
| a `usually` rule — **the unmarked default** | lowest |

Then §2.6 resolves correctly for a stated reason: **a thing you were told outranks a thing a default
rule guessed**, because the default rule is the lowest authority there is. And `always`, from §2.8,
stops needing its own mechanism in arbitration — it is just the top of this order.

### ⭐ The shape that survives the grades objection

`there-are-no-grades` killed an ordinal **carried on every entry and composed on every write**.
Authority as proposed is neither: it is **read at decision time from the graph**, which is exactly the
shape `precedence-is-read-not-kept` established — the precedence table was deleted, read from the
graph instead, and the whole suite ran **6.42s against 6.38s**. Nothing is carried, nothing composes,
there is no weakest-link arithmetic, and an authority claim is dated and deniable like everything
else.

### ⚠⚠ The cost is the one thing that could kill it, and it is not the same cost

`precedence()` is read **once per tick**. `resolve` is §4's *most consequential cost* — it was
measured at **70% of the engine's runtime** before the deposit-side index — and it runs per
proposition, per candidate entry. An authority lookup on that path is a different proposition
entirely from an authority lookup on the arbitration path.

⭐ The fast path is what to preserve: `precedence()` opens with *"empty when nothing claims one, which
is the common case… `instances_of` on a relation nobody has written is empty, so this costs a dict
lookup before it costs anything else."* Any authority read inside `resolve` must have that same
property — **zero cost when no corpus has made an authority claim** — or it taxes every corpus for a
feature few use.

### ⚠ And it is blocked on the same thing, for the third time

An entry's authority has to be derived from **what licensed it** — `loaded(p)` versus `applied(<R>)`,
and for a told fact, which speaker. Both `Entry.licence` and `Entry.source` are Python-only
(Part 1, §1.2). ⭐⭐⭐ **Part 1's finding 1 has now blocked three separate proposals**: told-beats-inferred
(§2.8), experiment (a) (§3.1), and this. That is no longer an audit item — it is the critical path.

### What this settles and what it opens

| | |
|---|---|
| ✅ **settled** | authority first, then order; order is what permits clarification; this is the design's existing arbitration rule applied one construct down |
| ⭐ **consolidated** | `always` / `usually` are positions on the authority order, not a separate mechanism |
| ⚠ **needs a third row** | incomparable authorities, not just equal ones, fall back to order |
| ⚠⚠ **must be measured** | an authority read inside `resolve`, with a zero-cost path when nobody claims one |
| ⚠⚠⚠ **blocked** | on `licence` / `source` becoming readable |

---

# Part 3 — The experiments, run

Both experiments from §2.8 were run. **Neither answered its own question, and both found something
better.** Baseline before and after: `python -m ugm.selftest` → **537 checks, 0 failing**.

## 3.1 Experiment (a): make `licence` readable, write *told beats inferred*

**The change** — three lines, the shape `rests_on` already has:

| file | |
|---|---|
| `chain.py` | mint `LICENSED_BY`; in `deposit`, `g.rel(self.LICENSED_BY, node, licence)` |
| `rules.py` | register `chain.LICENSED_BY: _stored` in `structural_relations` |
| `machine.py` | `"licensed_by"` in `reserved`, beside `"rests_on"` |

**The corpus** — lift *told* into stratum 0, then guard the default on it. `-` on a structural member
is negation as failure (§2.7), so this should read *nothing was told about this*:

```
rule <told> = implies( { licensed_by(?e, loaded(?p)) }, { told(?p) } )
rule <legs> = implies( { +person(?x), -told(has_legs(?x)) }, { +has_legs(?x) } )
fact +person(ann)
fact +person(bob)
fact -has_legs(bob)
```

`told` is classified structural, `<told>` is stratum 0, `<legs>` is not — all as intended, all
verified. **And the guard did not fire**: `has_legs(bob)` = `+`, exactly as in §2.6.

### ⚠⚠⚠ Finding 1 — a negated structural member is evaluated once, and the application is cached

The trace is the whole argument:

| tick | `told` instances | cached `<legs>` applications |
|---|---|---|
| 0 | `told(person(ann))` | **`{?x: bob}`, `{?x: ann}`** |
| 1 | + `told(person(bob))` | `{?x: bob}`, `{?x: ann}` |
| 2 | + **`told(has_legs(bob))`** | `{?x: bob}`, `{?x: ann}` |
| 3 | — | `<legs>` **applies**, writes `+has_legs(bob)` |

`<legs>` was matched at tick 0, when `told(has_legs(bob))` did not yet exist, and the application was
put in `_match_cache` by the delta-matching optimisation (`machine.py:3684`, `cache["rule_pos"]`).
The blocking fact arrives at tick 2. **Nothing re-evaluates the negation, and the stale application
applies at tick 3.**

⭐⭐⭐ `match`'s own docstring states the precondition this violates:

> ⚠⚠⚠ Safe only because the strata are **ORDERED**. §6's fixpoint is built from below, so a negated
> member names a relation whose derivation is **finished before this rule is reached** […] Negating a
> relation still being derived would answer from a half-built extension, which is the one way a
> rule-level read could disagree with the walk non-deterministically.

**That precondition is false for any structural relation that grows during the run** — and
`in_delta`, `delta_next`, `rests_on` and now `licensed_by` all do, because they are deposited on
every write. The strata are ordered *among themselves*; they are not ordered against the ordinary
loop that keeps feeding them. So the guarantee holds for the chain's *shape* and not for the chain's
*contents*, and the difference had not been drawn.

⚠ This is **pre-existing**, not introduced here: both mechanisms — delta-match caching and
negation-as-failure on structural members — were untouched by the three-line change, which only added
a relation to a dict. What the change did was make the interaction reachable from an ordinary corpus.

### ⭐⭐⭐ Diagnosed exactly: the invalidation machinery is present, correct, and cannot help

`_applications` step 0 (`machine.py:3615`) already does the right thing:

> *Structure derived since the last look. It sits in no delta, so the incremental path cannot see it:
> a rule reading a structural relation that has grown must be matched in FULL again, which is what
> dropping its cursor asks for.*

Instrumented, it fires every tick as designed:

| tick | grown | `<legs>` cursor before | cached `<legs>` applications |
|---|---|---|---|
| 0 | — | None | `{?x: bob}`, `{?x: ann}` |
| 1 | `told` | 121 → dropped | `{?x: bob}`, `{?x: ann}` |
| 2 | `told` | 123 → dropped | `{?x: bob}`, `{?x: ann}` |
| 3 | `told` | 124 → dropped | `{?x: bob}`, `{?x: ann}` |

`told` is detected as grown, the cursor **is** dropped, the rule **is** re-matched in full — and the
stale application survives anyway, because the merge is **add-only**:

```python
for a in found:
    k = (r.node, frozenset(a.bindings.items()))
    if k in cache["apps"]:
        continue          # ⚠ a re-match that no longer yields {?x: bob} cannot remove it
    cache["apps"][k] = a
```

> ⭐⭐⭐ **A full re-match can only ever ADD. Nothing in the engine can retract an application that
> the world stopped supporting.**

Step 1 retires applications when a later *entry* unsettles them (`cache["by_prop"]`). A structural
fact has no entry and sits in no delta, so that path never sees it. **The fix is therefore narrow and
locatable: when a rule's cursor is dropped for grown structure, its previously cached applications
must be dropped with it rather than merged into.** ⚠ And it needs a check, because 537 pass with the
defect live.

⚠ It is also invisible to the suite: 537 checks green with the defect live. Consistent with
`a-check-that-stopped-being-able-to-fail` — nothing asserts that a negated structural member is
re-read when its relation grows.

### ⚠⚠ Finding 2 — `_stored`'s anchor test asks `is_var` where it means `has_var`

`_stored` (`rules.py:1326`) refuses an unbound pattern, and says why: *"unbounded: this would
enumerate the history, so it finds nothing."* The test is

```python
if not any(not g.is_var(walk(g, a, bindings)) for a in args):
```

Measured on `licensed_by(?e, loaded(?p))`:

| arg | `is_var` | `has_var` |
|---|---|---|
| `?e` | True | True |
| `loaded(?p)` | **False** | True |

So a **partially generic structure counts as an anchor**, the test passes, and the walk enumerates
every `licensed_by` instance in the history — precisely the leak the docstring exists to prevent.
`Graph.has_var` is the predicate that draws this distinction and is used for exactly this purpose
elsewhere. ⚠ Any corpus writing `rests_on(?e, foo(?p))` or `in_delta(?m, bar(?x))` gets a full history
scan today, silently.

### Status of experiment (a)

**Its question is unanswered and now blocked.** *Told beats inferred* cannot be evaluated until
Finding 1 is fixed, because the guard it needs is the thing that does not re-fire. ⚠ The three-line
`licensed_by` change is **uncommitted, unexercised by any check, and therefore debt by `ugm.bundle`'s
own standard** — a relation no fixture can kill is a relation nothing is testing. It should either
get a check or be reverted; it should not sit there green and unused.

## 3.2 Experiment (b): `dormant` / `due` as a corpus-authored layer gate

✅ **The mechanism works exactly as §2.4 predicted, with no engine change.**

```
fact dormant(<legs>)                                   # action layer, shut
rule <legs>  = implies( { +person(?x), -amputee(?x) }, { +has_legs(?x) } )
rule <close> = implies( { +person(?x), -veteran(?x) }, { -amputee(?x) } )
rule <hurt>  = implies( { +veteran(?x) },              { +amputee(?x) } )
rule <open>  = implies( { -amputee(ann), +amputee(bob) }, { +due(<legs>) } )
```

| tick | applied | wrote |
|---|---|---|
| 0 | `<close>` | `-amputee(ann)` |
| 1 | `<hurt>` | `+amputee(bob)` |
| 2 | `<open>` | `+due(<legs>)` |
| 3 | `<legs>` | `+has_legs(ann)` |
| 4–5 | — | quiet, quiescent |

`<legs>` was matchable from tick 0 and **did not apply until the corpus opened it**. Closure before
action, authored, dated and deniable, in the corpus.

⚠ **But be exact about what it bought.** The answers are identical to §2.6's ungated working corpus,
which reached them in 5 ticks without any gate. What the gate adds is not a different result — it is
the *guarantee* that the action rule cannot run against a half-closed world. That guarantee is
unfalsifiable on this fixture, which is the trap `guard-address-probe` recorded: **a homogeneous
fixture cannot measure a discriminator.** A fixture where interleaving genuinely produces the wrong
answer is what would make this a measurement rather than a demonstration.

### ⚠ And it does **not** fix the §2.6 defect — decisive negative

§2.6's original failing corpus, with the action layer gated:

```
fact dormant(<legs>)
rule <legs> = implies( { +person(?x) }, { +has_legs(?x) } )
rule <open> = implies( { +person(ann) }, { +due(<legs>) } )
fact -has_legs(bob)
```

→ `has_legs(bob)` = **`+`**. 5 ticks, quiescent.

⭐ **This cleanly separates the two problems, which had been running together since §2.4.** Ordering
is a *layering* problem and `dormant`/`due` solves it. Default-eats-exception is a *deposit-order*
problem and no amount of layering touches it — it needs the second axis of §2.8, and the only
discriminator available is still `Entry.licence`.

## 3.3 Refusal **is** deferral — and my first measurement of it was wrong

> **The position.** *Refusal is not deferral* is not an engine issue. It is a limitation that more
> rules can solve: rules that react to a withdrawal.

Tested on machinery that exists today, because the gate already refuses (`_forbid`, §19's veto) and
already records the refusal as `refused(<proposition>, <sign>, <what forbade it>)`.

### ⚠⚠⚠ First run: a false negative caused by the probe, not the engine

```
rule <act> = implies( { +person(?x) }, { +greets(?x) } )
fact <no-greet> = forbidden(greets(ann))
fact +person(ann)
```
→ refused. Then `load(m, "fact -forbidden(greets(ann))")` → `greets(ann)` still `None`, and I
reported *refusal is not deferral, confirmed*.

**It was confirmed of my probe.** The withdrawal was loaded into a **second name scope**, so
`greets(ann)` there was a different node and the prohibition was never actually withdrawn — the twin
trap, which this repository has now recorded a dozen times, walked into by someone who had just
finished writing about it. ⚠ The tell was available and I did not read it: a companion rule matching
`-forbidden(greets(ann))` derived nothing, while one matching `refused(?p, plus, ?w)` derived fine.
One member failing and its neighbour succeeding is a *naming* symptom, not a semantics one.

### ✅ Re-run in one scope — and the answer is stronger than the proposal

Same corpus, withdrawal loaded into the same scope, **and no recovery rule anywhere**:

| | |
|---|---|
| with the prohibition | `greets(ann)` = `None`, 1 refusal recorded |
| after the withdrawal | `greets(ann)` = **`+`**, in 2 ticks |
| what applied | **`<act>`** — the original rule |

⭐⭐⭐ **Refusal already behaves as deferral, with zero extra rules.** The blocked application is not
discarded: once the prohibition is denied, `_would_change` sees the proposition would change, the
rule is re-proposed, and it applies. `arbitration-is-scheduling`'s *a loser is deferred, not
rejected* holds at the gate as well as in the chooser, and nothing had to be built for it.

So the position is right that it is not an engine issue, and understates the case: **it is not a
limitation either, and needs no rules at all.** What rules are for here is *reacting* to a refusal —
noticing it, reporting it, choosing something else — and that half is measured working:
`refused(?p, plus, ?w)` matches and a corpus can read every refusal, its sign, and what forbade it.

⚠ **What this does not yet show.** The recovery was measured for the **norm veto**, which is the only
refusal path that exists today. An authority check at intake (§2.9) would be a *second* vetoer on the
same `gate.veto` list, so it inherits this behaviour by construction rather than by luck — but that is
an argument, not a measurement, until the vetoer exists.

⚠ And one real limit is now visible: the prohibition was revisable only because its pattern is
**ground**. `_forbid`'s docstring says so — a generic norm cannot be revised from the surface, because
`-forbidden(doing(harm(?x)))` written twice denies a different node (§8 scopes variables to a
statement). Ground norms are revisable; generic ones are not. §21.

## 3.4 What the experiments changed

| §2.8's table | now |
|---|---|
| (a) make `licence` readable → *told beats inferred* | ⚠⚠⚠ **blocked** by Finding 1; produced two engine defects instead |
| (b) closure layer via `dormant`/`due` | ✅ **works**, no engine change — but the fixture cannot yet show it mattering |
| `always` = defeat-immunity in arbitration | untested; unaffected |
| one axis doing two jobs | ⭐ **confirmed by 3.2's negative** — layering cannot substitute for strength |

**The order of work has changed.** Before Finding 1 is fixed, *nothing that relies on a negated
structural member can be trusted* — which includes `rules-design.md`'s own `round_span`/`silent`
default-over-an-open-domain example, the one §2.7 cited as proof that negation as failure was never
missing. ⚠ That example may be sound only because its structural relations happen to be settled before
the ordinary rule is reached; whether that is guaranteed or accidental is now an open question about
already-shipped behaviour, and it should be checked before anything is built on top of it.

---

### Minor, found while probing

⚠ `authoring.md`'s snippets use `--` for inline comments. The tokeniser (`text.py:82`) accepts only
`#`; `--` is a parse error on the first line that carries one. Copy-pasteable snippets are that
document's stated promise, so this is a real defect in it.

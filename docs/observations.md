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

**So the answer to the opening question is: the mirror half of `Entry` and `Moment` is not the
problem.** `Entry.locus/proposition/sign` are members 0/1/2 of the entry node; `Moment.predecessor`
is `pred`; `Moment.delta` is `in_delta` + `delta_next`; `Span` is entirely `span(start, end)`. All of
it is a cache of graph content maintained where the state is, which is §7's own rule, and all of it is
a measured win (`_has_var` was **91%** of the rule-level read; `Situation.__init__` was the single
largest cost in the loop). Deleting the mirrors buys a slower engine and nothing else.

**Two things this audit got wrong on its first pass, corrected here rather than removed:**

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
| `Moment.licence` | `chain.py:86` | §4: *"which of the two this is, is said by the licence and by nothing else"* — **assigned once and read nowhere in the repository** |

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
| frame ⟶ purpose, parent | `gate.py:49,50` | `gate.py:145` *states the requirement itself*: "§17 needs each to be a node other facts can be about — **a purpose, a parent, a state**". No such fact is ever deposited. |
| `Frame.carried` | `gate.py:63` | what crossed out (§17) |
| `Gate.reseat` | `gate.py:151` | already noted in-file as §21 debt: "every seat move is a write, and this one is not yet recorded as an entry". **It also re-mints `frame.node`**, so a frame's identity is not stable across its life. Currently harmless *only* because everything written about a frame (`left`, `concluded` — `machine.py:1569,2707`) happens at discharge. That is a coincidence of timing, not a guarantee. |

### Machine

| | site | note |
|---|---|---|
| `Step.state` | `machine.py:61` | what a tick did; `workload.py`, `compose.py` and `__main__.py:67` all branch on the string |
| `_bookkeeping` | `machine.py:660` | a **50-name Python set** deciding what crosses out of a frame (§17) and what counts as a circumstance (§19). The comment admits it: *"the closed set of §10 growing by one, and it is a real cost"*. A corpus can neither add to it nor take from it. |
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

Method size **overstates** — not every line of `discharge` exists because of `_bookkeeping`. Read
the column as blast radius, not as debt.

Three contagions worth naming, in order of severity:

1. **Credit assignment is Python because `licence` is Python.** `review`, `blame`, `harm_of`,
   `_support`, `_choosers`, `_instead_of` all walk `e.licence`. *Why did that go well* is the agent's
   most important question about itself and no rule can take part in answering it.
   **The proof is already in the tree**: `machine.py:90-92` mints `EXERCISED` as *"the same claim as
   `applied(<R>)`, but as a proposition a rule can match rather than a licence only Python can
   read."* The leak was hit, diagnosed correctly, and mirrored around instead of fixed.

2. **`chain.trail()` still walks `Entry.consumed`** (`chain.py:421`) although `chain.rests_on()`
   (`chain.py:477`) already reads the graph. The fix arrived and the consumer did not move to it, so
   `why()` remains a native walk over a Python tuple and everything downstream inherits that.

3. **`discharge` reads three leaks at once** — `_bookkeeping`, `e.mention`, `frame.state` — which is
   why §17's crossing decision, the one a corpus most obviously ought to be able to argue with, is a
   93-line Python method.

## 1.4 The pattern

**Every leak is about the agent's own act** — what licensed a claim, which channel it came
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

Writing that rule down first is the whole point. Otherwise ten fixes arrive in four shapes and the
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

**It dissolves §0's exception, which is currently the sharpest edge in the whole authoring
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

**It is not a new idea in this repo — it is the generalisation of one that already works.**
§0's third row is `may(x, r)`: *turn* is a standing fact, and what acting spends is not the fact but a
**right**. `may` is already a state marker; the proposal is to stop treating that as a trick for
turn-taking and make it the shape.

**It makes the lifecycle a fact**, which is the same remedy Part 1 argues for everywhere else:
dated, attributed, deniable, inspectable. The round-417 eternal clock
(`dungeon-feedback.md` §7 — 8,072 entries with every outcome check green) was invisible *because
there was no state to look at*. With a marker there is something to print, something to assert about,
and something a watchdog rule can notice.

**It is a candidate answer to the design's own worst-marked open question**, which neither the
proposal nor this note went looking for. `rules-design.md`'s open list carries, at :

> **A HALF-FINISHED CHANGE IS INDISTINGUISHABLE FROM A FINISHED ONE, AND AN AGENT WILL ACT ON IT.**
> […] The design has a name for two entries that disagree, and **no name for a state that is halfway
> through a change.**

A transfer is necessarily two applications when a tool computes the amounts, and between them the
world holds twelve gold and never did — internally consistent, false, and **actionable**: an ordinary
economy rule reads the total and the agent emits `refuse_service(hero)`, measured, and §19 says an
emitted act cannot be forgone. A marker is exactly a name for *halfway through a change*. That does
not make it correct, but it means the proposal is answering a question the design already asked and
could not answer, which is a much stronger position than a preference about style.

**It may repair `supersedes`.** `HANDOFF.md:770` records it as too narrow: it defeats only
applications sharing a **consumed entry**, and two rules reaching one conclusion from different
premises share none — `<secret>` consumes `sealed(vault)`, the learned rule consumes `hinged(vault)`,
nothing is defeated, and the two oscillate forever. Two rules that both listen on the same marker
**do** share a consumed entry. That is a testable prediction, not a claim.

### The technical trap that has to be settled first

**UGM has no functional dependency, so a state marker does not supersede its own predecessor.**

`resolve` (`chain.py:367`) is keyed on the **proposition node**, and `g.rel` interns by
`(relation, members)`. So `stage(<m>, new)` and `stage(<m>, handled)` are two different propositions,
and depositing the second leaves the first standing. *Both* hold. "Substituting" a node is not
something the floor does for you — the same lesson as §0's *nothing spends a premise for you*, one
construct along.

Three ways out, and they are not equally good:

| how | cost |
|---|---|
| write the denial in the same consequent — `{ -stage(?m, new), +stage(?m, handled) }` | ✅ works today, no engine change; the author must remember, and forgetting fails **silently** — both states hold and both listeners fire |
| one relation per state — `noticed(<m>)` / `handled(<m>)`, listener guards on `-handled` | ✅ works today; needs the negative written up front (§1's *write your negatives*), and the state space is now spread over N relations with nothing tying them together |
| declare the relation **functional in an argument** — `functional(stage, 2)` | a real engine feature; per §20 the declaration must be data and per Part 1 it must be a fact a rule can read. Buys automatic supersession and a place to hang a check |

**So the proposal does not repeal §0 — it relocates it.** You still must spend something; what
changes is that the thing you spend is always something you concluded, never something you were told,
so §0's dangerous half never comes up. That is a genuine improvement and it should be stated that way
rather than as *consumption is gone*.

### The risks, stated plainly

1. **It re-creates phases by convention.** `nophases` deleted the interpreter's phases and
   `phases-to-rules` is recorded as load-bearing. A mandatory notice→mark→listen doubles the rule
   count and puts an ordering back — a corpus-level ordering rather than an engine one, and
   arbitration already orders, but the cost is real. **§20's test applies and should be run: does
   this add rows, or branches?**
2. **The state names must not become engine vocabulary.** `ugm.vocabulary`'s central result is
   that all 101 reserved names are about the chain, the surface, rules-as-data, the agent's own
   deliberation, or the seam — **and not one is about a world**. `new` / `pending` / `handled` are
   world-shaped. If the engine ships them, that result is lost. The convention must be something a
   corpus authors, and the engine's contribution can only be the mechanism (functionality, if it goes
   that way).
3. **Cost.** Two entries per event instead of one, and `resolve` is per proposition. The state gets
   bigger in exactly the dimension `ugm.state` measures. Worth a number before, not after.
4. **"More robust" is currently an opinion.** It is a good one, and it is unmeasured. The fixture
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

**It attacks the failure `authoring.md` calls the most expensive one there is**, and the
document's own words are the argument for the proposal:

> §1 — `−` means *denied*, never *absent*. **This is the one that will cost you the most, because it
> fails silently — the rule simply never applies, and nothing anywhere says why.**

Today the remedy is either `fact -poisoned(b)` written by hand for every entity, or a rule that
derives the default. The proposal makes the second one the convention and swaps the denial for a
positive name, which is the same move as 2.1 one construct along.

**The transition becomes a place to hang rules, and a sign is not.** `-poisoned(x)` records that
poison does not hold; it cannot say *how it stopped*, so *cured* and *never afflicted* are the same
claim. A state machine distinguishes them, and that distinction is what a corpus about poison actually
wants to reason from. **This is the strongest argument for the proposal** and it is independent of
everything else here.

**Hypothesis, testable with an instrument that already exists.** A missing `-poisoned` is invisible
to static analysis because `+poisoned` and `-poisoned` are the same relation name — `ugm.atlas` maps
*which relations can ever be grounded*, and the sign is not in the name. A positive state vocabulary
puts the sign **into the name**, so `healthy` with no producer becomes an ordinary ungrounded relation
that atlas already reports. If that holds, the proposal converts §1's silent failure into an existing
instrument's existing output, at zero engine cost. Not yet checked — atlas may or may not key on
sign; check before relying on it.

**It does not fight inheritance, it uses it.** Silence means *inherit from the predecessor*, so
`healthy(b)` carries forward until something supersedes it, exactly as `-poisoned(b)` would. Nothing
about the frame problem gets worse.

### What it costs

1. **Two ways to say one thing.** After this there are two surfaces for *b is not poisoned* —
   `-poisoned(b)` and `+healthy(b)` — and this design refuses that elsewhere on principle: a
   degenerate span is rejected because *two ways to say one locus is exactly the ambiguity the read
   cannot afford*. The three signs of §9 are a floor primitive; a convention that makes corpora stop
   using `-` does not remove it, it leaves it as a second, unused, still-matchable channel. **That is
   a real cost and the proposal should own it rather than route around it.**
2. The same goes for `?`. *Unknown poison status* is `?poisoned(x)` today and would become a state,
   so §9's third sign gets the same treatment as the second.
3. Population. Every property becomes a pair or a family, and every entity needs its starting state
   asserted. That is `-poisoned(b)` written by hand again under a different name — **unless** the
   starting state is derived by a rule, which is the version of the proposal worth testing.

### And it hits the same wall as 2.1, harder

`poisoned(b)` and `healthy(b)` are two propositions, so **concluding the second does not retract the
first** — `resolve` is keyed on the proposition node and `g.rel` interns by `(relation, members)`.
Both hold. A state machine whose states can all hold at once is not a state machine.

So the convention needs, per transition, either an explicit `-poisoned(?x)` in the same consequent —
which is the denial the proposal set out to replace, now written twice — or the missing engine
notion. That is not a reason to reject the proposal. It is the reason both proposals are one
proposal.

## 2.3 What 2.1 and 2.2 add up to

**Both reduce to a gap the design has already named three times, under a name that already
existed: `refutes`.**

| where | what it says |
|---|---|
| `rules-design.md` §8 | "**And there is no vocabulary for incompatibility.** You can deny a proposition; you cannot say that two propositions cannot both hold. That is a real gap, noticed when an older engine's `refutes` had nothing to port to." |
| `rules-design.md` open questions | the same, listed as outstanding |
| `harmony.py:13-15` | "the one incompatibility the floor can already express: `-p` IS the negation of `p`, and what cannot be said is that two *distinct* propositions are incompatible (`sitting(x)` against `standing(x)`). That relation — `refutes` — did not survive the restart." |

`refutes` was in the pre-restart engine and was deliberately not ported, because nothing in the new
floor had a place for it. These two proposals are the first concrete demand for it that comes from
**authoring** rather than from tidiness — and they arrive with a fixture (`ugm.dungeon`), a measured
failure mode (round 417 / the two channel hangs), and an open design question it would close
(half-finished change).

That does **not** mean *build `refutes`*. It means the next step is to decide which of these three
the demand is actually for, because they are not the same feature:

| candidate | says | reach |
|---|---|---|
| `refutes(p, q)` | these two propositions cannot both hold | general, symmetric, and needs a policy for what happens when both are asserted anyway |
| `functional(<rel>, <arg>)` | this relation has one value in this position, so a new one supersedes the old | narrower, exactly fits both proposals, and is a **declaration** rather than a claim about the world |
| nothing — write the denial | ✅ works today, no engine change | costs an author a member they can silently forget |

And per Part 1 §1.5, whichever is chosen must be a **fact a rule can read**, not a Python
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

### First, what it is not

**This is not the closed-world assumption, and the difference has to be stated before anything
else, because reading it as CWA would destroy the design's central property.** The floor stays open —
`−` still means denied and never absent, `?` is still a claim and not a silence, and
`ugm.vocabulary`'s result stands: you can write a proposition before you can give it meaning, and the
price is that a proposition awaiting meaning is indistinguishable from a typo. What the proposal
closes is **a corpus's own world, explicitly, by writing the rules that do it** — so closure becomes a
dated, attributable, deniable set of claims instead of a semantics. That is strictly the design's own
move: the free thing becomes the arguable thing (grades → `likely`, spans → `during`, precedence →
read from the graph).

### The engine already knows why this is right, and already paid for the lesson

`RuleSet.strata()` (`rules.py:291`) carries it, about the skeleton layer:

> **Negation makes the ORDER load-bearing, and structure cannot be taken back.** `best` is *a
> candidate nothing beats*. Applied before `beaten` has finished deriving, it mints a fact that is
> wrong and that nothing can deny — a skeleton fact has no sign, which is the whole point of it. An
> entry would merely be superseded; this is permanent.

That is the proposal's failure mode exactly, one layer down and already measured: **an action rule
that runs before closure completes acts on a world that is not yet closed.** For structure the result
is a permanent wrong fact; for ordinary rules it is a `causes` conclusion or — worse, and already
recorded at — an **emitted act**, which §19 says cannot be forgone. Same shape as the
half-finished-change finding in 2.1.

And §6's stratification is **derived, not assigned** — *every antecedent member is structural* is a
property computed by inspecting antecedents, a fixpoint from below. So this design's answer to "which
layer is this rule in" is already *compute it, do not declare it*, and any closure discipline should
be held to the same standard before it is allowed to be a declaration.

### The gap this exposes

**The engine stratifies structure and does not stratify anything else.** `strata()` orders stratum-0
rules into layers that must run in order. Ordinary rules have no such notion — they are ordered by
arbitration (preference, `_priority`, `_choose`), and defeated by `overrides` / `supersedes`, and
`authoring.md` §2 measured both of those as the wrong instrument for this: `overrides` is per tick and
per rule, so it takes out every entity at once, and `supersedes` needs a shared consumed entry.

**So today a corpus cannot say *finish closing before you start acting*.** That is the concrete gap
the third proposal opens, and it is a better-specified request than either of the first two.

### …except that it may already be authorable, with no engine change

`dormant(<rule>)` / `due(<rule>)` (`machine.py:318`, read from the graph at `machine.py:1458,2907`,
surface-named at `machine.py:519`) gate **recall**: a rule claimed dormant is not proposed at all
until something claims it due. Both are ordinary corpus facts — askable, defeasible, attributable.
That is a per-rule gate on whether a rule is even considered, which is precisely the lever the
proposal needs:

```
fact dormant(<act-rule>)                       -- the action layer starts closed off
rule <opened> = implies( { +closed(poison) }, { +due(<act-rule>) } )
```

And it is known to be cheap: `dormant` is on record as **14.5× from one corpus line**.

What is *not* supplied is the antecedent of that rule — **what concludes `closed(poison)`**. It
cannot be quiescence: quiescence is global and it is the machinery's, and §0 already warns that
quiescence catches none of the runaway cases. It has to be a corpus predicate — *every creature has a
poison state* — which means the corpus must be able to quantify over its own extent.

### What the proposal therefore requires and does not yet say

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

### The audit is the evidence, and it was collected before the claim was made

Part 1 went looking for Python-only fields with no idea this framing was coming. Look at what it
found:

| leak | states | where the state machine lives today |
|---|---|---|
| `Frame.state` | `discharged` / `exhausted` / `abandoned` | **a bare Python string** |
| `Step.state` | `applied` / `supposed` / `widened` / `quiet` / `quiescent` / `nothing-matched` | a bare Python string |
| `Rule.connective` | `causes` / `implies` | a Python string, branched on at `machine.py:3141,3176` |
| `Entry.mention` | use / mention | a Python bool |
| `Moment.licence` | time / derivation | a Python field, **never read** |

Every single one is a state machine. Not one of them is in the graph. **The claim predicted the
inventory.** That is the strongest thing that can be said for a design heuristic — it found things
before anyone was looking for them.

And `_bookkeeping` (`machine.py:660`) is the engine's own admission: a **50-name Python set** of
propositions that are about process state rather than about a world — `goal` / `achieved` / `blocked`,
`open` / `enough` / `stopped`, `dormant` / `due`, `pursued`, `defeated`, `unsupported`, `excluded`,
`forbidden`, `reified`. That list *is* the engine's state machines, enumerated, in Python, as a closed
set no corpus may extend.

### The other half of the evidence: the ones that are in the graph all work

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

### It reframes the signs, and dissolves 2.2's worst cost

§9's three signs — `+`, `−`, `?` — are **a built-in, universal, three-state machine over every
proposition**. Seen that way, 2.2 is not adding a second way to say *b is not poisoned* next to the
first; it is **refining the built-in machine into a corpus-defined one with more states and named
transitions**. `-poisoned(b)` and `+healthy(b)` are not rivals — the second says which of several ways
the first came about, which is exactly the thing 2.2 identified as its own strongest argument.

This weakens 2.2's cost but does not delete it: two surfaces still exist, and a corpus that
uses both inconsistently still gets an ambiguity. What changes is that the remedy is a **convention
about refinement**, not a prohibition.

### And it answers the question Part 1 §1.5 left open

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

### The limits, stated

1. **"Everything" is unfalsifiable as written.** A heuristic that cannot fail cannot be tested, and
   this repository has a standing finding about checks that stopped being able to fail. The
   falsifiable version is narrower and better: *wherever this codebase branches on a Python string or
   bool, there is a state machine that belongs in the graph.* That is checkable — grep — and §1.2 is
   the first pass of it.
2. **§20's test has not been run on it.** The design's standing test is that a new construct adds
   **rows, not branches**. Making state machines explicit plausibly adds rows everywhere; it must be
   confirmed it adds no branches, and the closure discipline of 2.4 is exactly where a branch would
   hide.
3. **It is a modelling discipline, not a representation.** Nothing here says every proposition needs
   a state node — the signs already are its state machine. The claim is about where the *transitions*
   are written, and conflating the two would produce an enormous and useless state space.
4. It is not novel, and per the repository's standing convention that is worth saying rather than
   discovering later: explicit fluents with named transitions against implicit negation is the
   situation-calculus/event-calculus argument, and *make the lifecycle a first-class object* is the
   ordinary advice of state-chart modelling. **The discipline is the claim, not the idea** — the same
   sentence `ugm.vocabulary` had to write about the open class.

### Where all four proposals now stand

| | proposal | engine change needed | test that would settle it |
|---|---|---|---|
| 2.4 | closure layer, then action layer | **none** — `dormant` / `due` | split the dungeon in two; count rules, ticks, entries |
| 2.2 | negatives stated positively | none (write the denial) | does the forgettable member get forgotten? does `ugm.atlas` catch it? |
| 2.1 | state markers instead of consumption | none (write the denial) | does §0's channel exception disappear? does `supersedes` start working? |
| 2.5 | all of the above, as one discipline | — | §20: rows, not branches |
| — | `functional(<rel>, <arg>)` or `refutes(p, q)` | **yes** | only after the three above show the denial actually gets forgotten |

The order is the same one this repository has been right with twice: author the convention, measure
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

Terminology: "island" here means a cluster of rules governing one exclusive family. That is *not*
the sense in `islands-not-parsing-gaps.md`, where an island is a code seam created by the second
caller. Two meanings, one word — worth keeping apart before either gets written into a design.

### The stance is already this design's stance

`agent-not-theorem-prover` is a standing finding; monotonicity was dropped on purpose; `−` is a claim
and not a failure to prove. So *complete in the most probable way and get on with it* is not a
departure — it is what the floor was built for.

**And the paranoia the proposal wants to avoid is not the tracking.** Provenance is already
recorded for free, by the machinery, at no cost to an author: every entry carries what it consumed,
and `rests_on` is in the graph. What makes a system paranoid is not recording support — it is
**acting** on it automatically, TMS-style, retracting everything downstream the moment a premise goes.
This design already refused that: `unsupported(p)` is an **occasion**, and what to do about it is a
corpus's business — *losing your reason is not acquiring a counter-reason*. So the agent can have
full provenance and zero fuss simultaneously, and that is built, not proposed.

### But the default itself does not work today. Three runs.

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

**The default silently ate the stated exception**, and the agent concluded a legless person can
walk. The entries show exactly why:

```
-  has_legs(bob)   licensed by loaded(has_legs(bob))
+  has_legs(bob)   licensed by applied(<legs>)
```

`resolve` breaks ties by **latest deposit**, and a derived conclusion is always deposited after a
loaded fact. So **a default rule beats a stated exception, always.** Note this is not oscillation and
not the runaway of §0 — it is quiescent in 6 ticks with nothing to see. It is the same class as the
half-finished-change finding: *internally consistent, false, and actionable.*

And it is the **reverse** of the failure `authoring.md` §1 warns about. §1 says the rule you wrote
will silently never apply. This one silently applies and eats the exception. **The document warns
about one direction and the other is just as available.**

Adding the closure layer of 2.4 naively does not help — it reproduces the defect one level up:

```
rule <close> = implies( { +person(?x) }, { -amputee(?x) } )
rule <legs>  = implies( { +person(?x), -amputee(?x) }, { +has_legs(?x) } )
fact +amputee(bob)
```

→ `amputee(bob)` = **`-`**. 6 ticks, quiescent. The closure rule ate the stated exception in turn.

### What does work — and it is the proposal, exactly

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

**So default completion is writable today, and it is writable only under this proposal's
discipline.** The default rule must be guarded by the exception; the exception vocabulary must itself
be closed; and the regress bottoms out in hand-written negatives at the leaves. That is a much
stronger result than "the proposal would be tidier" — **without the explicit closure, defaults are
not merely inelegant, they are wrong and silent.**

### And it names the real cost, which is exactly what the proposal set out to remove

The working version needs `fact -veteran(ann)` — **one explicit negative per entity per exception
vocabulary**. That is O(entities × exceptions) of hand-written closure, and it is the fuss the
proposal wanted to avoid. The proposal is right that people do not do this; what the measurement adds
is that the engine currently requires it.

**CORRECTED IN §2.7 — read that before relying on the paragraph below.** What follows names
`root`/`blocked` as the engine's only pattern for a negative existential. That is wrong: negation as
failure already exists on **structural** members, and `rules-design.md` carries a measured example of
a default over an open domain built from it. The paragraph is kept because the correction is the
finding.

**What is actually missing is a negative existential, and the engine already has exactly one
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

It also inherits that pattern's known price: an answer from an aggregate is only as good as the
moment it was asked at, and §6's quiescence rules govern when it may be asked. That is not an
objection — it is where the next measurement goes.

### The exclusive family is still the missing declaration

Nothing above needed `refutes`, because the working corpus used the sign for exclusion — `+amputee` vs
`-amputee` is the built-in two-state machine of §9. The declaration becomes necessary at **three or
more** states (`poisoned` / `healthy` / `immune`), which is where the proposal is aimed and where the
2.1/2.2 wall bites: three propositions, all of which can hold at once. A **partition**
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

### The mechanism is built, and this is the third time that has been the answer

`unless` in the antecedent **is** a negated member. `unless-was-a-name-not-a-gap` recorded it —
*"unless is if not"*, built since there were members, zero engine written — and §2.6's working corpus
is it: `implies( { +person(?x), -veteran(?x) }, { -amputee(?x) } )`. `rules-design.md` says the same
in one line: *"if not over a proposition the corpus can name is a negated member."*

So the proposal's mechanism needs nothing. What it needs is everything around it, below.

### The design already contains **both** assumptions. It partitions them by LAYER, not by relation.

This is the correction to §2.6 and it is the most important thing in this section.
`rules-design.md`, on a default over an open domain:

> **AND IT IS NOT MISSING EITHER — it needed a STRETCH, not a negation.** […] **A `-` on a
> structural member has meant *not derived* since the matchers merged, so negation as failure was
> never the missing piece.**

with a measured corpus — `round_span` / `silent` / `hero-acts`, layers derived and not assigned —
where *the player declared nothing this round* is a real default over an open domain, and the rule
withdraws the moment one word is said.

So:

| layer | `−` means | assumption |
|---|---|---|
| **structural** (§6 stratum 0 — `pred`, `anc`, `in_delta`, and anything a stratum-0 rule concludes) | *not derived* | **closed world** |
| **entries** (everything a corpus asserts) | *denied* | **open world** |

**Both assumptions already ship. The engine chooses between them by asking what a rule reads.**
"Closed by defaults" is asking for the same choice to be made **per relation, or per exclusive family,
by the corpus** — which is a far smaller request than adding a semantics, and a far better-posed one
than anything in 2.1–2.6.

### And *usually* vs *always* maps onto the same partition

The proposal's two kinds of universal are already two things in this engine:

| | | |
|---|---|---|
| *ALL triangles ALWAYS have 3 sides* | definitional; it cannot be denied, and denying it is an error rather than a claim | **structural** — `strata()`: *"structure cannot be taken back"* |
| *people USUALLY have legs* | a claim; dated, attributed, deniable, and the exception is ordinary | **an entry** |

**The limit, and the design states it itself**: stratum membership is *derived* from what a rule
reads, not chosen — and *"a corpus relation cannot be structural"*, because reading one stops a rule
being stratum 0. So a corpus can write the *usually* half and **cannot** write the *always* half. That
is the gap, stated more precisely than "make exceptions first-class": **the corpus can author
defeasible rules and cannot author definitions.**

### The gap §2.6 measured is still real, and it is now diagnosable

`<legs>` beat `fact -has_legs(bob)` because both are entries and `resolve` breaks the tie on **latest
deposit**. §4 says why that ordering exists:

> among claims about the same time, **the agent's current view wins over what it used to think**.

That is *revision*, and it is right for revision. **A default is not a later view — it is a weaker
view that happened to be computed later.** With grades deleted there is no notion of weaker, so
**timing stands in for strength, and it gets it backwards**: the derived default is always deposited
after the stated fact, so the default always wins. That single sentence explains all three §2.6 runs.

### The tempting fix is the one this repo already deleted

Marking a rule *defeasible* is `@likely` returning. `there-are-no-grades` deleted `GRADES`, `weaker`
and `effective_grade` and the finding was that the grade was **carried, composed, printed and never
obeyed** — this repository's own *read and not obeyed* defect arriving at the floor. Any new
rule-level strength annotation has to answer that, and *"this time it will be obeyed"* is not an
answer. The design-consistent forms are the two the partition already offers: **wrap the
conclusion** (`likely(p)`, a proposition a corpus can argue with), or **lift the definition into the
structural layer** (unarguable by construction, which is what a definition is).

### Not novel, and worth saying now rather than discovering later

This is defeasible logic — strict rules against defeasible rules, with defeaters — and Reiter's
default logic, where the *justification* of a default is literally `unless`. Both are well worked out,
and both have a standard answer to default-vs-exception that this design has not considered:
**specificity** — the more specific rule wins, computed rather than declared (birds fly, penguins do
not, nobody writes a precedence). *Derived, not assigned* is exactly this repository's stated
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

### The objection to specificity is correct

It is a **partial** order. Two rules whose antecedents are incomparable have no specificity relation
at all — the standard case is the Nixon diamond (*Quakers are pacifists*, *Republicans are not*, and
Nixon is both), where nothing is more specific than anything and the formalism gives no answer. §2.7
floated specificity as *derived not assigned* and this is the right rebuttal: derived is worthless if
the derivation is undefined on the cases that matter. Struck.

### "Do not create a hypothesis per default" is the load-bearing half, and it is right

This is the part to keep even if everything else in the section is dropped.

* It refuses the wrapper. `likely(has_legs(bob))` for every defaulted conclusion means every
  downstream rule matches through a wrapper, every conclusion nests
  (`likely(likely(…))` — the cost `there-are-no-grades` accepted knowingly), and the state roughly
  doubles in the dimension `ugm.state` measures.
* It is **already this design's posture**. The agent does not eagerly track what rests on what in
  order to retract it: `unsupported(p)` is an **occasion**, and *losing your reason is not acquiring a
  counter-reason*. Believing a default plainly, and dealing with the exception when it arrives, is the
  same stance one construct up. The provenance is still recorded — free, by the machinery — it is
  simply not **acted on** automatically. That is the whole of "without fuss or paranoia", and it is
  built.
* And it is what makes the proposal cheap rather than a second semantics: the unmarked case gets
  **no syntax at all**. `always` is one new name — `ugm.vocabulary` counts 102 reserved today, and
  both `always` and `usually` are free.

### `always` marked / `usually` unmarked also inverts the burden the right way

Definitions are rare; defaults are the bulk. Marking the rare one means an author writes nothing for
the common case and cannot get it wrong by omission — which is the opposite of `authoring.md` §1,
where the silent failure comes precisely from what an author did not write.

### But the proposal alone does **not** fix §2.6, and it is worth seeing why

If every rule is *usually*, then `<legs>`'s `+has_legs(bob)` and the stated `fact -has_legs(bob)` are
the **same strength**, so deposit order still decides and the default still eats the exception. The
conflict in §2.6 is not *default against definition*. It is **derived against told**.

**And the discriminator already exists on every entry — as Part 1's number-one leak.** The probe
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

**It is not universally right, and must not be built as a law.** An agent told something stale, that
then infers something from fresher evidence, wants §4's ordering and not this one. Which is the real
shape of the problem:

> **There is one axis doing two jobs.** `resolve` orders by time, and time is being asked to
> carry both **revision** (my current view beats my former view — correct) and **strength** (a stated
> fact beats a derived default — currently backwards). Grades were the second axis and were deleted
> for never being obeyed. The question this proposal actually raises is whether the second axis comes
> back, and in what shape.

### What shape survives the grades objection

`there-are-no-grades` killed an **ordinal that composed on every write and was never obeyed**. The
proposal's `always` is not that: it is a **binary kind, consulted at defeat**, with nothing to compose
and no weakest-link arithmetic. That is the shape that survives — and it points at where it belongs:

**`always` should mean *this rule cannot be defeated while its premises hold* — not *its conclusion
is permanent*.** The distinction matters and it is the one thing this section is most confident about:

* *All triangles always have 3 sides* is permanent.
* *`a` has 3 sides* is **contingent on `a` being a triangle**, and must stay deniable by denying that.

So `always` cannot mean "conclude into the structural layer" as §2.7 suggested, tempting as that was —
a skeleton conclusion resting on a deniable premise is precisely `strata()`'s (*a fact that is
wrong and that nothing can deny*), and §2.7 walked into it. **Corrected here.** `always` is
defeat-immunity, so it belongs in **arbitration**, beside `overrides` and `supersedes`, and not in the
chain.

Which also means it inherits arbitration's known problems rather than escaping them:
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
| `always` = defeat-immunity in arbitration | the surviving candidate | test against `overrides`' per-tick collateral **first** |
| told-beats-inferred | one line, unwritable today | blocked on `Entry.licence` — **Part 1, finding 1** |

The two cheapest experiments are unchanged and now better aimed: **(a)** make `licence` readable and
see whether *told beats inferred* fixes §2.6 in one rule; **(b)** §2.4's closure split in the dungeon.
Neither needs `refutes`, `functional`, partitions, or grades.

## 2.9 Settling ordering vs authority

> **The decision.** Authority is the **first** criterion. Within the same authority, **order** applies.
> Order of arrival is the only thing that allows **clarifications**.

### This is already the design's rule — and only for rules

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

### The finding: there are two orderings in this engine and they disagree

| | decides between | ordering |
|---|---|---|
| `arbitrate` (§14) | two **rule applications** | authority → apparatus → helpfulness → authoring |
| `resolve` (§4) | two **entries about one proposition** | locus, then deposit, then position — **time only** |

§2.6's defect falls entirely to the second. A loaded fact against a derived entry is **not two rule
applications**, so arbitration never sees it, and the only arbiter is `resolve` — which has no notion
of authority and never did.

> **Restated precisely: give `resolve` the ordering `arbitrate` already has.**

That is a much smaller and better-grounded request than a new axis. It is not *add authority to the
design*; it is *stop having two answers to the same question.*

### "Order allows clarifications" is exactly what the design already relies on

§4's second ordering is *among claims about the same time, the agent's current view wins over what it
used to think* — which is clarification, stated as the reason. And arbitration's last row is
`authoring`, the same idea for rules. **The proposal preserves both and subordinates them**, which
is why it is a refinement rather than a reversal: nothing that works today stops working, a case that
is currently decided by accident starts being decided on purpose.

### What must not be re-fused: channel is not authority

Already settled, and worth restating because *authority* will tempt an implementation toward `source`:

| | can it be wrong |
|---|---|
| **channel** — the intake path, socket, sensor, KB | **no** — mechanically observed |
| **authority** — who is taken to have spoken, and what their word is worth | **yes** — an ordinary claim, defeasible |

> Fusing the two would make authority **unforgeable by fiat**, so that anyone reaching the right
> socket would thereby be the boss.

So authority may not be read off `source`. It is a *claim about* a source, and it has to stay
deniable. Note the design names `by(<R>, boss)` for this and **the engine does not have it** — `by`
is not in `Machine.reserved`; only the already-derived `overrides` / `supersedes` pairs exist. That
gap is now load-bearing rather than cosmetic.

### The proposal's own objection applies to the proposal

§2.8 struck specificity for being a **partial** order, undefined exactly where it is needed. Authority
is partial too: two channels, two speakers, two rules with no declared relation between them. So the
rule needs a third row, or it has an undefined case:

> authority, **then order — for claims of the same authority *and* for claims whose authorities are
> incomparable**.

"Same" is not enough. Most pairs will be incomparable, not equal, and that is the common path rather
than a corner.

### And authority-first **still does not fix §2.6** on its own

Run the corpus against the proposed rule. `-has_legs(bob)` arrived from the KB; `+has_legs(bob)` is
licensed by `applied(<legs>)`. Nothing claims an authority for either. So they are incomparable →
order applies → **the default still wins**.

**The missing piece is §2.8's `usually`, and it fits here as the same axis rather than a second
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

### The shape that survives the grades objection

`there-are-no-grades` killed an ordinal **carried on every entry and composed on every write**.
Authority as proposed is neither: it is **read at decision time from the graph**, which is exactly the
shape `precedence-is-read-not-kept` established — the precedence table was deleted, read from the
graph instead, and the whole suite ran **6.42s against 6.38s**. Nothing is carried, nothing composes,
there is no weakest-link arithmetic, and an authority claim is dated and deniable like everything
else.

### The cost is the one thing that could kill it, and it is not the same cost

`precedence()` is read **once per tick**. `resolve` is §4's *most consequential cost* — it was
measured at **70% of the engine's runtime** before the deposit-side index — and it runs per
proposition, per candidate entry. An authority lookup on that path is a different proposition
entirely from an authority lookup on the arbitration path.

The fast path is what to preserve: `precedence()` opens with *"empty when nothing claims one, which
is the common case… `instances_of` on a relation nobody has written is empty, so this costs a dict
lookup before it costs anything else."* Any authority read inside `resolve` must have that same
property — **zero cost when no corpus has made an authority claim** — or it taxes every corpus for a
feature few use.

### And it is blocked on the same thing, for the third time

An entry's authority has to be derived from **what licensed it** — `loaded(p)` versus `applied(<R>)`,
and for a told fact, which speaker. Both `Entry.licence` and `Entry.source` are Python-only
(Part 1, §1.2). **Part 1's finding 1 has now blocked three separate proposals**: told-beats-inferred
(§2.8), experiment (a) (§3.1), and this. That is no longer an audit item — it is the critical path.

### What this settles and what it opens

| | |
|---|---|
| ✅ **settled** | authority first, then order; order is what permits clarification; this is the design's existing arbitration rule applied one construct down |
| **consolidated** | `always` / `usually` are positions on the authority order, not a separate mechanism |
| **needs a third row** | incomparable authorities, not just equal ones, fall back to order |
| **must be measured** | an authority read inside `resolve`, with a zero-cost path when nobody claims one |
| **blocked** | on `licence` / `source` becoming readable |

## 2.10 *Throughout* — and what a "procedure" may be here

> **The observation.** `authoring.md`'s span recogniser is *a very unnatural way of unfolding it*. I
> could not formally decompose the meaning of *throughout* myself. What I would actually do is either
> install **triggers** — *this buff applies throughout the battle* = *battle starts → add the buff;
> battle ends → remove it* — or, if I had to **check** whether something held throughout, walk the
> moments of the battle and look for one where it did not. I would convert *throughout* into what I
> would **do**, and I would explain it to other people that way: my opinionated interpretation. What
> would it take for the engine to do the same? A previous version had **procedures**.

### First: the doc conflates two different shapes under one heading

`authoring.md` §13 introduces the span with three examples — *they took turns*, *it rained
throughout*, *he was poisoned for three rounds* — and the rule it then shows does only the first:

```
rule <r> = implies( { +acts(?p) at ?mp, +acts(?q) at ?mq, sanc(?mq, ?mp),
                      span_of(?s, ?mp, ?mq) },
                   { +took_turns(?p, ?q) at ?s } )
```

That is a **recogniser**: it finds two events and mints the stretch they bound. It checks nothing
about what held in between — and *throughout* is precisely a claim about what held in between. So
part of why the encoding reads as unnatural is that **it is not an encoding of `throughout` at all**.
The two shapes are:

| | |
|---|---|
| **recognition over a stretch** | a pattern of events bounds a span — `took_turns` ✅ what `<r>` does |
| **universal over a stretch** | a property held at **every** moment of a span — *poisoned throughout* ❌ not shown, and not directly writable |

### Interpretation 1 — triggers — is already cheap, and is your own §2.1 proposal

*Battle starts → add the buff; battle ends → remove it* is the **state marker with named
transitions**. No span, no stratum-0 rule, no recursion. Measured, three ordinary rules:

```
rule <begin> = causes( { +battle_starts(?b) },
                       { -battle_starts(?b), +in_battle(?b), +buffed(hero) } )
rule <end>   = causes( { +battle_ends(?b), +in_battle(?b) },
                       { -in_battle(?b), -buffed(hero) } )
rule <swing> = causes( { +buffed(hero), +may(hero) }, { -may(hero), +strong_hit(hero) } )
```

| | |
|---|---|
| mid-battle | `buffed(hero)` = `+`, `strong_hit(hero)` = `+` |
| after `+battle_ends(b1)` | `buffed(hero)` = `-`, `in_battle(b1)` = `-` |

**Silence-means-inherit is doing the work of *throughout*.** The buff holds at every moment between
the transitions because nothing said otherwise — which is the same property spans were reached for,
obtained without them. Note the consequents spend what they consume (`-battle_starts`, `-may`) —
§2.1's discipline, and §0's.

### Interpretation 2 — check for a counterexample — is the one that is genuinely missing

*Walk the moments and see whether it failed somewhere* is a **bounded universal quantifier over a
stretch**, and the engine has no way to say it. `Chain.Span`'s own docstring says why, and says it was
deliberate:

> a denial in the middle of the stretch is exactly what the read cannot see, because `resolve` returns
> **one winner rather than scanning an interval**. That would be a leak of the worst kind: free,
> unarguable, and wrong only sometimes.

So the recursion-over-spans encoding is a **workaround for a missing universal**, and that is the real
source of the unnaturalness: you are asked to express *for every moment* as a recursion, because
*for every moment* cannot be written.

And note the asymmetry that is already built: negation as failure exists over the **structural**
layer (§2.7), which is a bounded universal over derived facts. It does not exist over **entries in an
interval**, which is what `throughout` needs.

### What "procedures" may be here — and the shape already exists

The previous engine's procedures went with its ISA floor and should not come back as control flow. But
the design already has the admissible form, and it is exactly *a request answered by doing rather than
by searching*:

> `answerer(name, request, fn)` — *a request answered by a function rather than a search* […] the
> binding is a fact, `answers(<M>, ask)`, deposited like any other, queryable and **deniable**.
> Retiring a tool is `fact -answers(<oracle>, guess)`.

So `throughout(<span>, <p>)` as a **request the machinery answers by walking the chain** is a
procedure that survives every constraint this design has:

* it is **bounded** — the span's endpoints are known, so the walk is O(length), not O(history)
* it is **data** — `answers(<throughout>, holds_throughout)` is a fact, so a corpus can ask which
  interpretation is installed, and **deny it**
* it **proposes, never concludes** (`a-tool-is-data`) — so the corpus decides what the answer means,
  which is precisely *the opinionated interpretation*, kept where it belongs
* it has precedent for exactly this reason: `root`/`rooted` and `blocked` are already *"an aggregate
  over what the rules produced is the machinery's business and not a rule's"*

### The deeper point, and it is the design's own thesis

*I would give my opinionated interpretation* is not a concession — it is what this design has been
choosing on purpose every time. Grades became `likely`; span containment became `during`; the
precedence table became a read. Each time the free, automatic, unarguable thing was replaced by a
claim a corpus makes and can be argued with. **There is no canonical decomposition of *throughout*,
and there should not be one.**

So the defect is not that interpretation is required. It is that **only one interpretation is
currently cheap, and it is the least natural of the three**:

| interpretation | cost today |
|---|---|
| triggers — a state with two transitions | ✅ three ordinary rules, measured above |
| check for a counterexample over the stretch | ❌ not writable; needs a universal the read refuses |
| recognise a pattern that bounds a stretch | writable, three rules, two of them stratum 0 |

**Fix the economics, not the semantics.** An answerer for row two, and `authoring.md` §13 rewritten
to present all three as choices with their costs rather than the span as *the* answer.

**Open, and it is the price of row two**: an aggregate answer is only as good as the moment it was
asked at, and it is not re-asked when the interval later acquires a counterexample. That is finding 1
of §3.1 arriving in a new place — an answer computed once, from a world that then changed — and it
should be checked against the retraction fix rather than assumed to be covered by it.

## 2.11 What an answerer is, and whether it could be a subgoal

> **The question.** What *is* an answerer? Couldn't we model it as a **subgoal of finding out
> something**? (Noted as probably another opinionated view.)

### What it is, mechanically

1. A rule concludes a **request**: `+advice(depth)`.
2. At the **write**, the machinery looks for something whose `answers(<M>, advice)` fact currently
   holds — read from the graph, every time.
3. It calls `fn(machine, frame, entry)`, which returns a node, or `None` for *I have nothing to say*.
4. It deposits `answered(<M>, advice(depth), deep)`, licensed by `applied(<M>)` — **the same licence a
   rule's conclusion carries**.

Three properties it deliberately has (`_answer`): **not a conclusion** — what lands is *M said so*,
and turning that into a belief is an authored rule, so a confident tool cannot launder a weak answer
into a strong claim. **Not unconditional** — `fact -answers(<oracle>, advice)` silences it
immediately and on the record. **Not invisible** — `review` and `blame` walk through a tool without
knowing it is one.

### The proposal is right for half of them, and the split is principled

`fit` is an answerer. `_fit`: *"a rule concludes `+fit(<R>, goal)` — could this rule produce this? —
and the machinery answers, because deciding that a ground goal corresponds to a stored generic
pattern is `match`, and match is floor."* Backward reading **is rules now**, and it works by asking
`fit`.

So if asking were modelled as a subgoal: finding out whether a rule fits your goal would require
setting a goal to find out — and answering *that* requires `fit`. **Infinite regress.** That is §5's
wall, and the answerer is precisely what stops it: *a request answered by a function rather than a
search*.

| ask | may it become a subgoal? |
|---|---|
| `fit`, `verdict`, `recall`, `root` — the machinery's own | **no** — they are the regress-stopper |
| `advice`, `roll`, `throughout` — a corpus's | **yes**, and there is a case that they should |

### For the corpus half, the proposal buys something real

Today a request has no **why**. `+advice(depth)` is written and nothing records what it was for. As a
subgoal it would gain: a purpose it can be **abandoned** with, **prioritisation** through arbitration
instead of firing whenever its rule matches, `blocked` when nothing can answer instead of silence, and
**credit** — `blame` attributing the cost of having asked.

Two costs. Everything would go through recall, arbitration and expansion; `dice.roll` is called
constantly in the dungeon, and that is a deliberative cost where there is now a dispatch. And §19:
dispatch must stay **at the write**, with the veto, because a tool call can be an effect leaving the
agent and an emitted act cannot be forgone — goals are abandonable, effects are not. So goal-driven
asking layers *above* the write; it does not move it.

### And the composition already works, with no engine change — measured

```
rule <seek> = implies( { +goal(know(?p)) },                        { +advice(?p) } )
rule <take> = implies( { +answered(?who, advice(?p), ?y) },        { +believes(?p, ?y) } )
fact +goal(know(depth))
```

```
+ advice(depth)                         licensed by applied(<seek>)
+ answered(oracle, advice(depth), deep) licensed by applied(oracle)
+ believes(depth, deep)                 licensed by applied(<take>)
```

**The goal is the reason; the answerer is the means.** They are at different layers and they
compose — and note the licence chain is uniform: `applied(oracle)` has the same shape as
`applied(<seek>)`, which is the *one credit walk reaches both* property, working.

So the proposal is testable as a **corpus convention** before anything is built — the same conclusion
§2.4 reached, for the same reason.

### On "injecting my opinionated view"

That is the move §2.10 concluded is correct, so it needs no apology. The only question is **where
the opinion lives**: as a corpus convention it stays dated, attributed and arguable; baked into the
engine's shape it becomes free and unarguable, which is what this design has refused every time it
had the choice.

## 2.12 `all(moments)` — and why nothing prevents it

> **The question.** What prevents us from writing `all(moments)` and again having an **opinionated**
> — maybe operative — version of `all`?

### Nothing prevents the enumeration. It already works, with no engine change — measured

There is no need for a collection term, because **the span already is one**: a node with two ordered
members. And the moments inside it are reachable with structural relations that already ship:

```
span_of(<S>, ?a, ?b),  sanc(?b, ?m),  anc(?m, ?a)
```

Run against a six-moment chain with `<S>` = `S1..4`:

| | |
|---|---|
| bindings for `?m` | **M3, M2, M1** |

So a rule can bind every moment of a stretch today. `sanc` is strict, so the end moment is
excluded — `anc(?b, ?m)` includes it; which you want is already an authoring choice, which is the
section's point arriving early.

### What is missing is only the **aggregation**, and the design has already said whose job that is

*For every such binding, p holds* is a negative existential — *no binding where `-p`* — and §12 is
explicit that a `-` member says *an entry denies this*, never *for no `?m`*. The engine's own remedy,
stated for `root` and `blocked`:

> **a REQUEST the machinery answers by looking**, because an aggregate over what the rules produced is
> the machinery's business and not a rule's.

So `all` is not blocked by the floor. It is one answerer away, and every ingredient — the stretch as a
node, the walk, `resolve` at each moment — is already built and already bounded.

### And "opinionated" is not a hedge here: the variants give **different answers**

There is no single `all`, and this is demonstrable rather than arguable. On a chain where `p` is
asserted at M1 and nothing further is said about it:

| reading of *`p` throughout S1..4* | answer | why |
|---|---|---|
| held at **every** moment — an entry at each | **false** | only M1 has one |
| **never denied** at any moment | **true** | silence is not denial |
| held at the **start** and never denied since | **true** | the inheritance reading |
| held wherever anything was **said** about it | **true** | sampling |

Four readings, two answers, one chain — and the divergence follows directly from silence-means-inherit
(§9), so it is not a corner case. **That is the argument against `all` ever being floor semantics**:
a primitive would have to pick one and make it free and unarguable, which is the leak §2.10 names.

### What it should be instead

An **installable interpretation**, in §2.11's shape: `answers(<strictly>, all)` deposited as a fact,
so a corpus can ask which reading is in force, install a different one, and **deny** the one it has.
The name is admissible under `ugm.vocabulary`'s test — `all` is about the chain, not about any world.

Two prices, both already on the record rather than new:

* **Re-asking.** An aggregate is only as good as the moment it was asked at. Over a **completed** span
  that is safe — `Chain.Span` says a stretch is at-or-before once *complete*, so the answer is
  finished. Over an **open** stretch it is not, and a later moment can falsify it. That distinction is
  already drawn in the code and should be what decides whether an `all` answer may be cached.
* **§3.1's finding 1, in a third place** — an answer computed once from a world that then changed. It
  should be checked against the retraction fix rather than assumed covered by it.

## 2.13 Heuristics that may fail — and what the design is actually chasing

> **The objection.** The same error keeps being made: trying to **close** open-class concepts, when we
> know *characteristica universalis* failed. We chase **correctness** everywhere, and correctness may
> not even be fully defined in an open-class world. Even *subgoals might never terminate* — fine! Then
> we bail out or apply heuristics, and **declare** that the system works with heuristics and **can
> fail**, like any classifier or regressor.

### Correction: §2.11's regress argument was stronger than the facts support

I wrote that `fit` cannot become a subgoal because the regress is infinite. **Termination is not a
prohibition in this engine — it is a budget**, and the engine already declares it can fail and
deposits a fact saying so:

```
bounded(ticks)   bounded(depth)   bounded(hypotheses)
rule <panic> = implies( { +bounded(ticks) }, { +goal(diagnose(myself)) } )
```

So *it might not terminate* is the one objection this design has already answered everywhere else.
Withdrawn as a prohibition.

What survives is a difference of **degree, not kind**, and it should be stated as such. A budget
converts non-termination into **failure**. For a corpus's `throughout` the failure is **local** — one
question goes unanswered, the agent notices and does something else. For `fit` it is **total**: the
planner needs `fit` to plan how to obtain `fit`, so there is no base case a search can reach, and
bounding it means nothing is ever planned about anything. That is an engineering argument about blast
radius, not a proof — and the objection is right that I dressed it as one.

### But the reframe is the real point: this design is not chasing correctness. It is chasing accountability.

Its own standard, read off what it actually enforces, is three things — and **none of them is
correctness**:

1. the agent can **say** what it means (expressibility)
2. when it guesses, the guess is **on the record** — dated, attributed, deniable
3. when it gives up, it **deposits a fact saying so** — `bounded`, `blocked`, `refused`, `quiet`,
   `unsupported`, `defeated`

All three are compatible with *it works by heuristics and can fail*. And the check is that **every
defect found in this session is a violation of 1, 2 or 3 — not one is a violation of correctness**:

| finding | what was actually wrong |
|---|---|
| §2.6 the default ate the stated exception | quiescent, 0 failing, **no record** — the author's exception was inexpressible |
| §3.1 the stale cached application | 537 checks green with it live — **silent** |
| §3.1 `is_var` anchor | a full history scan, **silently** |
| §1.2 the leaks | the state machine exists and **nothing can read it** |
| round 417 | every outcome check green — **silent** |
| the half-finished transfer | internally consistent, false, and **actionable** |

Not one of these would be fixed by a better notion of truth. Every one is fixed by the system being
able to *say* something it currently cannot. **So the objection and the design agree, and the word
"correctness" was mine, not the design's.**

### Where the analogy imposes obligations rather than removing them

*Like any classifier* is the right stance and it is not a free pass — it comes with the discipline
that makes classifiers usable:

* **A classifier reports when it is unsure.** Here that is already available and unused: an entry's
  licence distinguishes told from inferred, and §2.8's `usually` would mark a guess as a guess. Both
  are still Part 1 leaks.
* **A classifier has a measured error rate.** This design has no held-out set and no error rate;
  `ugm.learning` is the nearest thing. *Declaring* that it can fail is cheap; **measuring how often
  is the part that makes the declaration mean anything**, and that is unbuilt.
* And the analogy is imperfect in a way that matters: a classifier fails **stochastically and
  measurably**; a rule engine with a heuristic fails **systematically** — the same input fails the
  same way every time. That is better for debugging and worse for confidence, and it means
  *calibration* is not available as a borrowed idea.

### The one line worth holding

**Heuristic and fallible: yes. Silent and inexpressible: no.** A wrong answer the agent can state,
date, attribute and be argued out of is this design working. A wrong answer nothing can see is the
only failure mode every finding in this document actually shares.

And the standing convention applies to the objection too: *characteristica universalis failed* is
correct and `ugm.vocabulary` already says so from the other side — this is the Prolog/RDF/Cyc
position, and **the discipline is the claim, not the idea.**

## 2.14 The web, and following the white rabbit

> **The observation.** Open-class concepts are a **web**, and we cannot avoid following the white
> rabbit.

*Web* is already this repository's own word for it. `ugm.vocabulary` **asks whether a name has a
web**; `ugm.atlas` asks it of a whole corpus; `Machine.unwebbed` reports names read but never written,
to the author, at load.

### The design never tries to bottom out definitions — grounding here is pragmatic

`atlas.reachable` is the answer, and it is already built and already measured:

> Monotone and built from **BELOW** […] a relation is reachable only because something already
> grounded makes it so, **so a ring of rules concluding about each other adds nothing and cannot
> bootstrap itself into looking live.**

with the base case `grounded_by_facts(m) | set(m.reserved)`.

That is the white-rabbit problem answered without solving it: **grounded does not mean *reduced to
primitives*, it means *reachable from what was asserted*.** A web of concepts that only refer to each
other is not an error and not a paradox — it is **dead**, and the instrument says so. The rabbit hole
is permitted; what is not permitted is mistaking it for ground.

Three more places the same acceptance is already built: the chase is **bounded and the bound is a
fact** (`bounded(depth)`, `_knob`, so a corpus can argue about how far to follow); stopping is a
**claim** rather than exhaustion (`enough(x)`); and unwebbed names are **reported** rather than left
silently inert.

### But there IS a bottom, it is 102 names, and that is where the objection would land

`atlas` treats `m.reserved` as ground. So the engine's reserved vocabulary **is** the floor of the
web — a small characteristica: not universal, but ~100 names deep.

And what keeps that from being Leibniz's project is exactly `ugm.vocabulary`'s measured finding:
**not one of them is about a world.** They are about the chain, the surface, rules-as-data, the
agent's own deliberation, and the seam where a world reaches it.

### The invariant was written down and then fired on the next commit — mine

`python -m ugm.vocabulary`, run immediately after this section was written:

```
  every reserved name is classified exactly once: NO
  reserved names that are about a WORLD: 1
  FAIL  the classification is not the vocabulary: 1 unclassified ['licensed_by']
  FAIL  a reserved name turned out to be a domain word
```

`licensed_by` is the relation added for experiment (a) in §3.1. It is **not** a world word — *what
produced this entry* is a fact about the chain's own construction — but it had not been classified,
and the census counts an unclassified name as a domain word rather than letting it vanish. That is
`ugm.vocabulary`'s own stated design: *a name nobody classified would otherwise vanish from the count
and flatter whichever bucket it belonged in.*

Classified into **the chain**, beside `rests_on` and for its reason:

| | |
|---|---|
| reserved names | **103** (the chain: 10 → 11) |
| classified exactly once | ✅ yes |
| about a world | ✅ **0** |
| `ugm.vocabulary` | 18 checks, 0 failing |
| `ugm.selftest` | 543 checks, 0 failing |

Worth stating plainly rather than filing as routine: **the gate this section proposed caught the
only new reserved name in this session, on the first run, and the offender was the author of the
section.** An instrument that fires on its own writer is the one kind worth trusting — and it is the
opposite of `a-check-that-stopped-being-able-to-fail`.

> **So the objection converts into a maintainable invariant with an instrument that already exists:
> the day a world concept is reserved, this design becomes the thing the objection is against.**

Which puts a gate on every proposal in Part 2. `always` / `usually` (§2.8), `all` (§2.12),
`throughout` (§2.10), an authority relation (§2.9) — each is admissible only because it is about the
chain or about rules-as-data. `poisoned` / `healthy` / `new` / `handled` (§2.2, §2.1) would **not**
be, and that is why those must stay corpus conventions. `ugm.vocabulary` should be run after any
of them ships, not as a formality but as the one check that this document's whole direction has not
quietly inverted its own premise.

## 2.15 Is the reserved list the ENGINE, or the BUNDLED RULES?

> **The question.** The list of concepts is too wide. It is fine as an **opinionated** list — but let
> us confirm we are talking about the **engine** and not about the **bundled rules**.

First, `Machine.reserved` is **a surface namespace, not a dependency list.** Its stated job is to
stop a corpus minting a twin of a name the machinery uses — being in it says only *this name is
spoken for*. So the question is right to be asked and the census does not answer it.

### Measured, by who actually touches each name

The partition below is **approximate** and the mis-fits are named rather than hidden: `causes` lands
in *offered* because the connectives live in `rules.py` which the probe did not scan, and the knobs
(`depth`, `budget`, `hypotheses`, `ticks`) land there because `_knob` receives its relation as a
parameter. Both are engine. The *shape* survives the noise; the exact counts should not be quoted.

| | n | |
|---|---|---|
| the engine **writes** it | 42 | `achieved` `bounded` `close` `concluded` `defeated` `harmed` `helped` `left` `open` `quiet` `reached` `recalled` `refused` `stopped` `unmet` `unsupported` `widened` … |
| the engine **reads or walks** it | 25 | `anc` `pred` `in_delta` `entry_of` `rests_on` `span_of` `licensed_by` `asking` `dormant` `due` `standing` `forbidden` `prefer` `enough` … |
| the **bundle** authors it | 12 | `blocked` `check` `deviates` `did` `doing` `expands` `fit` `resume` `says` … |
| offered only | 24 | 10 numerals (which the file itself calls *"not vocabulary at all"*) + the mis-fits above |

**So the answer is: it is the engine, not the bundle.** Roughly two thirds of the list is
constructed or consulted by the machinery itself; the bundle's own share is small, and the census's
own borrow-rate table already showed the bundle borrowing **25 of 25** rather than inventing.

### But the "too wide" instinct is right, in a way the census cannot see

The width is concentrated in the **42 names the engine WRITES**, and every one of them is an
**occasion** — a fact the machinery deposits so that a corpus can react. `blocked`, `quiet`,
`unsupported`, `defeated`, `bounded`, `refused`, `open`, `stopped`. That is §2.13's third obligation
made concrete: *when it gives up, it deposits a fact saying so.*

> **The width is not ontology creep. It is the engine narrating itself, and that narration is the
> price of accountability.**

**And there is no gate on it.** `ugm.bundle` kill-probes every bundled rule — *a rule no fixture
can kill is a rule the fixture is not testing* — and **nothing does the equivalent for a reserved
name.** Nothing asks: *if this occasion stopped being deposited, would any check notice?* Given this
session found `Moment.licence` written and never read, and `_tolerance` surviving its own
generalisation, the prior that all 42 are load-bearing is not good.

That converts *too wide* from a matter of taste into a measurement, with an existing instrument to
copy. Proposed: **a kill-probe over reserved names** — suppress each occasion in turn, run the suite,
and report every name no check can kill. `ugm.vocabulary` says what the names are *for*; this would
say which of them are *doing anything*.

## 2.16 The criterion: speakable ⟹ bundle; unspeakable ⟹ engine

> **The parallel.** Everything we can **speak about** must be open class — part of the **bundle**.
> Anything we cannot speak about — an index over nodes, a cache, a RETE algorithm — is **engine**: the
> chemistry and physics of the brain.

This is the first thing in this document that is a **test** rather than a proposal, and it should be
adopted as one. Applied to §2.15's measurement it does real work immediately — and it needs one more
row than it states.

### The missing row: spoken about, but not deniable

The skeleton (`pred`, `anc`, `in_delta`, `entry_of`, `rests_on`, `licensed_by`, `span_of`) **is spoken
about** — §12 made it matchable on purpose — and is **not** a corpus's to author. §6's own words:
*no sign, no locus, no licence; nobody asserted them.* Speaking about the shape of the chain does not
make the shape a claim.

So the criterion needs a second axis, and the design already has both words for it:

| | speakable | deniable | |
|---|---|---|---|
| index, cache, heap, match strategy | ❌ | — | **engine — chemistry** |
| the skeleton | ✅ | ❌ | **engine's shape, exposed — anatomy, not chemistry** |
| a raw record only the machinery can witness | ✅ | ✅ | **engine deposits the minimum** |
| an interpretation of one | ✅ | ✅ | **bundle** |

### And the last split is not invented here — the design already made it once, and named it

> **Splitting a phase shrinks it rather than relocating it**, and intake is the demonstration: the
> boundary became the smallest unarguable record — `arrived(channel, proposition, sign)`, sourced to
> the channel — and **what a report means became a rule.**

`arrived` is the record; `says` is the interpretation. So the test for every one of §2.15's 42
engine-written names is: **record, or interpretation?**

**And the measurement already confirms the test on two pairs it did not know were pairs:**

| | engine writes | bundle authors |
|---|---|---|
| intake | `arrived` — the raw event | `says` — what it meant |
| exhaustion | `quiet` — the loop stopped | `blocked` — nothing can be done |

Both split exactly along record/interpretation, in code written before the criterion existed. That is
two independent confirmations, and it is why this is a test and not a preference.

### The criterion unifies the whole audit into one line

> **The engine may keep only what a corpus could never have an opinion about.**

Both halves of this document are the same violation, in opposite directions:

| | |
|---|---|
| **Part 1's leaks** | the engine **keeps** what a corpus *should* have an opinion about — `licence`, `source`, use/mention, `Frame.state`, `_bookkeeping` |
| **§2.15's 42** | the engine **authors** interpretations a corpus should own |

Neither is a correctness failure (§2.13). Both are the engine holding an opinion that is not its to
hold — silently in the first case, by fiat in the second.

**What the criterion does not license**: moving an occasion to the bundle cannot mean *a rule
deposits it*. A rule cannot know the loop ran out of work. It means the **name and its meaning** are a
corpus's, and the machinery supplies only the raw event — exactly what intake did. Any triage of the
42 has to produce, for each, the smallest unarguable record it should have deposited instead.

And that is what the reserved-name kill-probe (§2.15) is for: it would find the ones nothing reacts
to, which are the cheapest to move first because moving them breaks nothing.

## 2.17 *Three turns ago* — operational, not unrolled. **Measured, twice.**

> **The requirement.** *Attack the goblin that attacked you three turns ago* means: look at turns,
> count backwards, check which goblin attacked, select it. The engine's computation must be the same
> shape as that sentence — some rule or procedure, manageable by **both** the engine and the bundle,
> that expresses *three turns ago* **operationally**, in terms of other open-class concepts (counting
> backwards, turns, which) — **not an unrolled formal definition**.

Both readings run today. Neither unrolls.

### In the corpus's own unit, with a computator

*Three turns ago* is arithmetic **in the corpus's unit**, not a walk over the engine's moments. The
`3` is a **datum inside the rule**, not three chained members:

```
rule <revenge> = implies( { +turn(?now), back(?now, 3) as ?then,
                            +attacked(?g, hero, ?then) },
                          { +doing(attack(?g)) } )
fact +turn(7)   fact +attacked(gob_a, hero, 4)   fact +attacked(gob_b, hero, 5)
```

→ 5 ticks, **`emitted: attack(gob_a)`**. One rule, and the sentence's four steps map onto its four
members in order.

But `back` is a Python computator, so *counting* escaped to Python — which is exactly the half the
requirement says must also be the bundle's.

### …and as pure rules, with no Python at all

**Recursion is not unrolling.** Written once, it handles any n:

```
rule <b0> = implies( { +turn(?t) },                                       { +back(?t, 0, ?t) } )
rule <bn> = implies( { +back(?t, ?n, ?u), +prev(?v, ?u), +succ(?n, ?m) }, { +back(?t, ?m, ?v) } )
rule <revenge> = implies( { +turn(?now), +back(?now, 3, ?then),
                            +attacked(?g, hero, ?then) }, { +doing(attack(?g)) } )
```

| | |
|---|---|
| derived | `back(7,0,7)` `back(7,1,6)` `back(7,2,5)` **`back(7,3,4)`** |
| emitted | **`attack(gob_a)`** |
| ticks | 9 |

Nothing is unrolled and nothing is in Python. `back` is defined **once**, in terms of `prev` and
`succ` — two other open-class concepts the corpus owns — and *three* is data. That is the requirement,
met.

### What this says about the pattern this document keeps finding

This is §2.10's conclusion for the third time: **the capability was there and the documentation
presented the least natural encoding as the canonical one.** *Throughout* was shown as a span
recursion when triggers were three ordinary rules; *three turns ago* looks like a `pred` chain only
because the corpus was not given its own ordinal to count in.

And there is a recorded warning that points the same way, read backwards: `Member.locus`'s comment
says a foreign corpus *"spent 24% of itself re-implementing a moment ordinal as a round counter"* —
noted as waste, and `at ?m` was added to remove it. The measurement above suggests the round counter
was not waste at all: **turns are the corpus's unit and moments are the engine's, and the two should
not be collapsed.** `at ?m` is the right feature; *use it instead of your own counter* would be the
wrong advice.

### What is still genuinely missing

Nothing in the goblin case — but it is worth being exact about why it was easy, because §2.12's case
was not. *Three turns ago* is an **existential**: find the one turn, find who attacked in it. *Held
throughout* is a **universal** over a stretch, and that is the shape the read still refuses. The
requirement is met wherever counting is the operation; it is not met where **checking every** is.

## 2.18 Can the bundle build the program at runtime, from the utterance?

> **The question.** Do we have rules that **build the program at runtime from the utterance** — so
> that saying *attack the goblin that attacked you three turns ago* is turned by the bundle into
> something executable?

Four layers, and they are not equally built. Measured.

### 1. Utterance → **parameters** for standing rules. Works now.

**You do not need to build a rule to build a program.** The utterance deposits a *fact*, and a
pre-existing rule reads it:

```
rule <heard>   = implies( { +says(?who, revenge(?n), plus) }, { +policy(revenge, ?n) } )
rule <revenge> = implies( { +policy(revenge, ?n), +turn(?now), +back(?now, ?n, ?then),
                            +attacked(?g, hero, ?then) }, { +doing(attack(?g)) } )
```

| | |
|---|---|
| before the utterance | `emitted: []` |
| after `deliver(user, revenge(3), +)` | **`emitted: ['attack(gob_a)']`** |

The `3` came from the utterance and the *how far back* is data. This is `ugm.shapes`'s standing
question — *whether a corpus needs the rule language at all, or whether most knowledge could be facts
filling a small set of bundled schema rules* — answered in favour of facts for this whole class of
instruction.

### 2. Utterance → a **goal**. Works now.

`+goal(...)` is an ordinary fact, so a rule over `says` concludes one, and backward reading takes it
from there. This is the **one-shot command** reading of the sentence, where layer 1 is the **standing
instruction** reading. Two readings again, both cheap — §2.10's pattern for the fourth time.

### 3. Utterance → a **new rule**. `adopt` is built; constructing the patterns is the wall.

`adopt(<R>)` reads a rule back out of the graph and makes it live, and the suite checks the round trip
survives. But a corpus cannot **build** what `adopt` would read. Tested directly:

```
rule <build> = implies( { +wanted_rule(?n) },
                        { +rule(?n), +conn(?n, implies), +ant(?n, attacked(?g, hero, ?t), plus, 0) } )
```

```
ParseError: rule 'build' concludes about a variable its antecedent never binds
            -- the gate would refuse to deposit it (§13)
```

A rule's *pattern* is generic structure, and a corpus's conclusion may not be generic — §13 refuses
it, and the parser catches it at load with a clear message rather than at runtime with silence, which
is the right failure. This is already on the record: *the composer must be a **tool** — three walls
stop a corpus writing a rule's patterns*, which is why `compose` and the example-learner are tools and
not rules.

### 4. Natural language → structure. Not built, and per §2.16 it should not be engine.

Nothing here parses English; `says(user, revenge(3), +)` is already structured, and the parser did
that work offline. And the criterion says where it belongs: turning an utterance into structure is
an **interpretation**, not a raw record, so it is the bundle's or a **tool's** — never the floor's.
That is also exactly where `an-advisor-at-recall-can-only-lose` says to put a model: *where there is
no algorithm.*

### Where that leaves the question

| layer | status |
|---|---|
| utterance parameterises a standing rule | ✅ measured working |
| utterance becomes a goal | ✅ ordinary fact |
| utterance becomes a **new rule** | `adopt` works; **pattern construction needs a tool** |
| language becomes structure | ❌ absent by design; belongs to a tool |

So the honest answer is **yes for the executable half and no for the linguistic half** — and the
seam between them is a single, already-named thing: **a tool that emits rule patterns.** It is the
same seam `compose` and learn-from-examples already sit on, which means building it once serves three
callers rather than one.

## 2.19 …and the question was narrower than that: **interpret and execute**, building nothing

> **The clarification.** Not corpus building. At **runtime**, when we do **not** build a rule, but
> rather **interpret** and **execute** a command.

**This runs today. Nothing is authored, nothing is in Python.** The command arrives on a channel as
an ordinary structured term and is walked by an interpreter that is **one rule per constructor**:

```
rule <trust>  = implies( { +says(?who, command(?c), plus) },  { +command(?c) } )
rule <i-cmd>  = implies( { +command(attack(?ref)) },          { +need_ref(?ref) } )
rule <i-the>  = implies( { +need_ref(the(?kind, ?spec)) },    { +need_kind(?kind), +need_spec(?spec) } )
rule <i-that> = implies( { +need_spec(attacked_at(?when)) },  { +need_when(?when) } )
rule <i-ago>  = implies( { +need_when(ago(?n)), +turn(?now), +back(?now, ?n, ?then) },
                        { +when_is(?then) } )
rule <i-pick> = implies( { +when_is(?t), +need_kind(?k), +attacked(?g, hero, ?t), +is(?g, ?k) },
                        { +ref_is(?g) } )
rule <i-run>  = implies( { +command(attack(?ref)), +ref_is(?g) }, { +doing(attack(?g)) } )
```

Delivered at runtime: `command(attack(the(goblin, attacked_at(ago(3)))))`

| | |
|---|---|
| `when_is(4)` | `+` — counted back 3 from turn 7 |
| `need_kind(goblin)` | `+` |
| `ref_is(gob_a)` | `+` |
| `ref_is(rat_c)` | **`None`** — the rat attacked at turn 4 too, and is not a goblin |
| **emitted** | **`attack(gob_a)`**, 11 ticks |

The discrimination is real, not staged: `rat_c` satisfies *attacked you three turns ago* and fails
*the goblin*, so `the(goblin, …)` did work rather than decorating.

### This is what "procedures" should have been

The interpreter **is** the procedure — and because it is rules rather than control flow, every step of
it is a fact: dated, attributed, deniable, inspectable in the trail, and **overridable by a corpus one
step at a time**. `ref_is(gob_a)` is a claim the agent can be argued out of; a stack frame in the
deleted engine was not. That is the whole difference between this and what went with the ISA floor.

And it passes §20's own test: adding a command form adds **a row** — one more `<i-...>` rule — not
a branch anywhere in Python.

### The one real limit

Every rule above matches a **known** constructor. A command language that is open in its *forms*, not
just its vocabulary, would need `?r(?x, ?y)` — a variable relation — and §3's index has no bucket for
one, so it degrades to a scan. Whether that matters depends on a question this document has not
measured: **command forms are a much smaller open class than concepts**, and it may be that a corpus
adding a row per form is the right answer rather than a limitation. That is the next thing to test if
this direction is pursued.

And one authoring trap, hit while writing the fixture: an arrival lands as `says(who, p, sign)`,
never as `p`. The first version of the interpreter matched `command(?c)` directly and sat inert for
2 ticks with nothing saying why — §1's silent-failure shape, from the channel side.

### …and with the compositional form, unchanged

`attack(turns(3, ago, attack(goblin, you)))` — where the referent is the **subject of a described
event** — needs five interpreter rules and one new relation, `denotes`:

```
rule <i-need>  = implies( { +command(attack(?d)) },        { +need(?d) } )
rule <i-turns> = implies( { +need(turns(?n, ago, ?ev)), +turn(?now), +back(?now, ?n, ?then) },
                         { +ev_at(?ev, ?then), +via(turns(?n, ago, ?ev), ?ev) } )
rule <i-ev>    = implies( { +ev_at(attack(?kind, ?whom), ?t), +refers(?whom, ?target),
                           +attacked(?g, ?target, ?t), +is(?g, ?kind) },
                         { +denotes(attack(?kind, ?whom), ?g) } )
rule <i-lift>  = implies( { +via(?d, ?ev), +denotes(?ev, ?g) },   { +denotes(?d, ?g) } )
rule <i-run>   = implies( { +command(attack(?d)), +denotes(?d, ?g) }, { +doing(attack(?g)) } )
fact +refers(you, hero)
```

| | |
|---|---|
| derived | `denotes(attack(goblin, you), gob_a)` → `denotes(turns(3, ago, attack(goblin, you)), gob_a)` |
| emitted | **`attack(gob_a)`**, 10 ticks |

Three things fall out that were not designed for:

* **`attack` is both the imperative and the event description, disambiguated by position alone** —
  outer argument of `command`, versus inside `turns(…, ago, …)`. No use/mention machinery, no
  disambiguation pass.
* **`you` is an ordinary fact**: `refers(you, hero)`. Indexicals are open class like everything
  else, and a different addressee is a different fact rather than a different interpreter.
* **`denotes` IS the semantics, and it is a claim.** Composition threads through `via`, and the
  whole reading is on the record.

### Which makes the interpretation accountable — asked, and answered

```
why denotes(turns(3, ago, attack(goblin, you)), gob_a)?
  because +back(7, 3, 4)          licensed by applied(<bn>)
  because +back(7, 2, 5)          licensed by applied(<bn>)
  because +prev(4, 5)             licensed by loaded(prev(4, 5))
  …
  because +command(attack(turns(3, ago, attack(goblin, you))))  licensed by applied(<trust>)
  because +says(user, command(…), +)                            licensed by applied(<intake>)
  because +arrived(user, command(…), +)  via user, licensed by utterance(user, command(…))
```

The trail runs from the reading of a referring expression **back to the utterance that caused it**,
through the arithmetic that located the turn. That is §2.13's thesis on the objection's own example:
not *the interpretation is correct*, but **the interpretation is sayable, attributable, and arguable**
— and if it picked the wrong goblin, there is a specific step to disagree with.

## 2.20 The walkthrough: engine, bundle and corpus on one command

Traced live. `command(attack(turns(3, ago, attack(goblin, you))))` delivered on the `user` channel to
an agent already quiescent.

| | who | what happened |
|---|---|---|
| — | ⚙ **ENGINE** | `channels.deliver` → `gate.write` deposits `+arrived(user, command(…), +)`, licensed by `utterance(user, …)` |
| 0 | 📦 **BUNDLE** `<intake>` | `+says(user, command(…), +)` |
| 1 | 📄 corpus `<trust>` | `+command(attack(turns(3, ago, attack(goblin, you))))` |
| 2 | 📄 corpus `<i-need>` | `+need(turns(3, ago, attack(goblin, you)))` |
| 3 | 📄 corpus `<i-turns>` | `+ev_at(attack(goblin, you), 4)` · `+via(turns(…), attack(goblin, you))` |
| 4 | 📄 corpus `<i-ev>` | `+denotes(attack(goblin, you), gob_a)` |
| 5 | 📄 corpus `<i-lift>` | `+denotes(turns(3, ago, attack(goblin, you)), gob_a)` |
| 6 | 📄 corpus `<i-run>` | `+doing(attack(gob_a))` → ⚙ **ENGINE `_dispatch` fires AT THE WRITE** → `+emitted(attack(gob_a))`, **actuator called** |
| 7 | 📦 **BUNDLE** `<did>` | `+did(attack(gob_a))` |
| 8 | 📦 **BUNDLE** `<assert-act>` | `+attack(gob_a)` |
| 9 | — | quiescent |

### What each layer actually did

**The engine touches the command exactly three times**: to record the arrival, to stamp every
write, and to dispatch the act. Everything between `arrived` and `emitted` is rules. There is no
interpreter loop in Python for any of the language above.

📦 **The bundle is thin and lives at the boundary** — three rules, all of them about the seam:
`<intake>` (an arrival becomes something said), `<did>` and `<assert-act>` (an act becomes a fact
about the world). Not one bundled rule is about *commands*, *reference* or *time*: the whole
middle of the trace is the corpus's.

📄 **The corpus is the program**, six rules, and each writes exactly one step of the reading.

### Three things the trace shows that the rules do not

* **Dispatch happens inside tick 6, not on tick 7.** `+doing(attack(gob_a))` and
  `+emitted(attack(gob_a))` are in the same delta, and the actuator ran between them. That is §16 and
  §19 being structural rather than promised: *the one place effects leave the agent* is the write, so
  the loop never gets a turn in which the decision exists and the act has not happened. The
  half-finished-change defect (§2.1) is exactly the case where this guarantee does **not** extend, and
  the contrast is visible here.
* **Every application deposits `exercised(<R>)`** — visible on all nine ticks. That is Part 1's
  mirror proposition earning its keep: it exists because `Entry.licence` is Python-only, and it is
  what lets a rule ask *which rules have run*.
* **The counting was already done.** `back(7, 3, 4)` was derived at load, before the command
  arrived; the command only looked it up. The "program" is not rebuilt per utterance — the corpus's
  standing rules had already computed what *three turns ago* could mean, and interpretation consumed
  it. Which is also a cost worth naming: `back` derives every reachable n eagerly, and on a long
  game that is the whole history. A corpus wanting it lazily would gate `<bn>` on `dormant`/`due`
  (§2.4).

One asymmetry worth noting rather than filing: `+emitted(attack(gob_a))` is licensed by
`utterance(kb, attack(gob_a))` — **an utterance licence, not `applied(<i-run>)`**. The act is recorded
as the agent speaking, not as the rule concluding, which is right for §13's provenance and means
credit for an act reaches the rule only through `rests_on` rather than directly.

## 2.21 Assembling the backbone — flood-fill over the web

> **The idea.** Maybe this is not goal-driven over many ticks. Maybe it is an **instantaneous** attempt
> by the engine to leverage open-class concepts and expert knowledge to **assemble the executable
> definition of the command** — navigating the web, like a **flood fill**, to find the most plausible
> **backbone** connecting all the elements of the command.

### Not novel, and naming it is useful rather than dismissive

This is **interpretation as abduction** (Hobbs), and the flood fill is **spreading activation /
marker passing** over a semantic network (Quillian; Charniak; Cyc's SBHL). *Most plausible backbone*
is *cheapest abductive proof*. All of it is worked out, including the failure mode — see below.

### "Instantaneous, by the engine" contradicts the criterion from §2.16

Two messages ago the test was: **anything we can speak about is bundle; only what we cannot speak
about is engine.** A backbone connecting `attack`, `turns`, `3`, `ago`, `goblin`, `you` is
*exactly* the thing a corpus should be able to disagree with — so the engine may not decide it. And
`Machine.answerer` already states the same in its own words:

> **a search the agent cannot inspect is not reasoning it can be held to.**

It also collides with `nophases`: a dedicated assembly step before the loop is a phase, and phases
were deleted for reasons that would apply again.

### The resolution the design already has: the search is chemistry, the backbone is a claim

Split it exactly where intake was split (§2.16):

| | |
|---|---|
| **the flood fill** | ⚙ engine or **tool** — unspeakable, an index walk, no more inspectable than a heap |
| **the backbone it returns** | 📄 **a proposition** — dated, attributed, deniable, and the thing `why` explains |

`a-tool-is-data`'s rule makes this exact shape available: **a tool proposes, never concludes.** So the
assembler is an **answerer** — `backbone(<command>)` — whose answer a corpus turns into a reading, and
whose reading can be argued with step by step, as §2.19's `denotes` chain already is.

And the ingredients are not missing: `ugm.atlas` already runs a reachability fixpoint over a
corpus's rules; `fit`/`need` already expands one step backwards over *any* rule that could conclude a
goal; `_choose` already carries a heap and a preference score for ranked candidates.

### "Most plausible" is the ML seam, arriving from the language side

`gradable-quantities-are-the-ml-seam` says the missing thing is the **pair** — a score (*how good*)
beside a grade (*how sure*) — and `an-advisor-at-recall-can-only-lose` says to put a model
**where there is no algorithm**. Ranking candidate backbones is precisely that: there is no algorithm
for *which reading did they mean*. So this is the same seam already identified at recall, reached
from interpretation instead, which is an argument for building one mechanism rather than two.

### The known failure mode, and the discipline that answers it

Abduction **explains too much**: an unconstrained flood fill finds a backbone for almost any input,
including nonsense, and reports it with the same confidence as a good one. §2.13's obligations are
what keep that honest, and one of them is still unbuilt:

* the reading is **stated** — `denotes` already is
* when it gives up it says so — `blocked`, `bounded`
* **no measured error rate.** *It can fail like any classifier* is only meaningful with a number,
  and nothing here produces one.

### The cheap experiment that would tell us whether this is worth building

§2.19's generic interpreter needed one lexicon fact — `past(attack, attacked)` — to link the event
*description* to the event *record*. A flood fill would **discover** that link instead of being told
it.

> **So the testable question is not *can we assemble a whole command*. It is: can the engine find
> `attack → attacked` without being told?**

If lexicon facts are cheap to author, the flood fill buys little and the generic interpreter already
wins. If they are the bottleneck — one per verb pair, per corpus, forever — it buys everything. That
is a measurement, and it is much smaller than the holy grail it would justify.

## 2.22 Measured: the flood fill's motivating problem does not exist

§2.21 proposed the cheap test — *can the engine find `attack → attacked` without being told?* — on the
grounds that lexicon facts might be the bottleneck. **They are not, and the reason is that the
bottleneck was invented by the fixture.**

### The census: three real corpora, 39 own relations, **zero** pairs to link

| corpus | own relations | morphological pairs |
|---|---|---|
| a D&D fight | 20 | **0** |
| passenger rights | 13 | **0** |
| the design's worked examples | 6 | **0** |

The dungeon's own vocabulary says why at a glance:

```
ac, attack, beats, calc, dead, die, done, fled, follows, hits, hp,
intends, may, missed, monster, over, present, roll, turn, wraps
```

**One name per concept.** No author writes both `attack` and `attacked`. The description/record
split that made `past(attack, attacked)` necessary in §2.19 was **an artifact of my own fixture**, not
a phenomenon any corpus exhibits.

### Confirmed by deletion — the interpreter works with **no lexicon at all**

Same generic interpreter, one member changed, and the corpus authored the way real ones are:

```
rule <i-ev> = implies( { +ev_at(?v(?kind, ?whom), ?t), +refers(?whom, ?target),
                         +?v(?g, ?target, ?t), +is(?g, ?kind) },
                       { +denotes(?v(?kind, ?whom), ?g) } )
fact +attack(gob_a, hero, 4)     fact +insult(elf_e, hero, 5)
```

```
emitted, with NO lexicon facts at all -> ['attack(gob_a)', 'mock(elf_e)']
```

**Zero lexicon facts. Two different commands. The description relation *is* the record relation.**

### And the deeper reason the web is already navigated

`attack` and `hits` in the dungeon *are* related — **by a rule**, not by a lexicon link. That is how
every corpus connects its own concepts, and it means a flood fill would be searching a web the rules
already make explicit, one step at a time, through machinery that exists: `fit`/`need` expands
backwards over any rule that could conclude a goal.

> **The web is not a thing to be discovered underneath the corpus. The corpus's rules ARE the web.**

This is `an-advisor-at-recall-can-only-lose` for the third time in this repository: **an ideal table
buys zero when there is nothing to look up, and a wrong one costs more as knowledge grows.**

### The honest limits of this measurement

* The stemmer catches **morphology, not synonymy**. `attack`/`hits` are a synonym pair and were not
  counted — but they are connected by a rule, which is the point.
* These corpora were authored **without a command interpreter**. Real natural language may reintroduce
  the split through tense or nominalisation (*the attacker*, *having attacked*), and nothing here
  measures that.
* But the burden has moved, and that is the useful outcome: **the flood fill now needs a corpus
  that demonstrably requires it.** Until one exists, it would be an advisor with nothing to advise.

## 2.23 Trying to break it — one real gap, one under-general rule

Two adversarial commands against §2.22's interpreter. Both broke it. **They broke it in different
ways, and only one is the engine's fault.**

### A — the definite article silently becomes a universal, and it is an ACT

Two goblins attacked at turn 4. *Attack **the** goblin that attacked you three turns ago*:

```
command(attack(turns(3, ago, attack(goblin, you))))
   -> emitted ['attack(gob_b)', 'attack(gob_a)']
```

**Both.** Nothing failed, nothing was reported, and the agent attacked twice.

**This is the worst class this document has a name for**: silent, and **actionable** — §19 says
an emitted act cannot be forgone, so the second attack cannot be taken back. It is the
half-finished-transfer shape arriving through language instead of through arithmetic.

And §18's *a description resolves to the most recent* does **not** cover it. That rule is about
several **entries about one proposition** and which one `resolve` returns. Here there are two
**different** propositions, both true, and a rule matching both simply applies twice.

> **Selecting one individual from several that satisfy a description is an AGGREGATE OVER BINDINGS,
> and §12 says a rule cannot express one.**

That is the **third** distinct place in this document where the missing thing is the same
thing — an aggregate over what the rules produced, which `root` and `blocked` already establish as
*the machinery's business and not a rule's*:

| | what is missing |
|---|---|
| §2.6 | *nothing was told about this* — a negative existential |
| §2.12 | *held at every moment of this stretch* — a universal |
| §2.23 | *exactly one thing satisfies this description* — uniqueness |

All three are aggregates; all three have the same shipped precedent; none is built. **If one
mechanism is built for the whole document, it is this one**, and that is a stronger case than any
individual feature in Part 2 has.

### B — a referent in object position: my rule's fault, not the engine's

*Attack the elf **you attacked** three turns ago* — the referent is argument 1, not argument 0:

```
command(attack(turns(3, ago, attack(you, elf))))    -> emitted []
```

Silent again, but for an ordinary reason: `<i-subj>` fixes the referent at argument 0. Adding one
more rule for the other position:

```
rule <i-obj> = implies( { +ev_at(?v(?whom, ?kind), ?t), +refers(?whom, ?target),
                          +?v(?target, ?g, ?t), +is(?g, ?kind) },
                        { +denotes(?v(?whom, ?kind), ?g) } )
   -> emitted ['attack(elf_e)']
```

**One row, no engine change** — §20's test passing on exactly the kind of extension that would
otherwise be a branch. B is not a gap; it is an interpreter that was written for one grammatical role
and asked about two.

### The obvious fix makes it worse — and that is what identifies the real gap

§0 says an occasion must be consumed, so the first attempt was to spend the command:

```
rule <i-run> = causes( { +command(?verb(?d)), … }, { -command(?verb(?d)), +doing(?verb(?g)) } )
   -> attack(gob_b) × 250+   -- a runaway
```

§0's own exception, exactly: `says(user, command(…), +)` is **standing and never retracted**, so
denying `command` licenses `<trust>` to re-derive it, forever. *Consume what you concluded, never what
you were told* — and `command` is one hop from a channel, which makes it the trap rather than the
remedy.

The stable shape §0 prescribes is a guard — `-handled(?d)` — and that is where it stops:

> **`-handled(?d)` must be *denied* for a description that has not been seen yet, and §9 says `−`
> means denied and never absent. There is no way to state it in advance, because the set of
> descriptions is unbounded.**

So both halves of A reduce to the same missing thing, and it is the one §2.6, §2.12 and this
section already named:

| | the aggregate that is missing |
|---|---|
| choosing **one** goblin | *exactly one thing satisfies this description* |
| acting **once** | *nothing has handled this description yet* |

Four independent routes in this document, one mechanism. And note what is **not** missing: the
engine already behaved correctly at every step. Two goblins satisfy the description, so two
applications apply — `arbitration-is-scheduling`'s *a loser is deferred, not rejected* working as
designed. Nothing is broken; something is **unsayable**.

### And the honest note about §2.22

§2.22's conclusion stands — the corpus's rules *are* the web, and no lexicon was needed. But the
interpreter used to demonstrate it **had a live, silent, actionable defect the whole time**, and
nothing in this document would have caught it: there is no check over an interpreter, and quiescence
is reached happily with two attacks emitted. A working demonstration is not a tested one, which is
this repository's oldest lesson arriving at the newest thing in it.

---

# Part 4 — The aggregate: what is missing, stated once

## 4.1 The gap, precisely

**A rule's antecedent is existential.** Each member matches *an entry*, so a rule says *there is an
entry such that…* and a `−` member says *there is an entry that denies…*. §12 states the limit
outright: a `−` member says *an entry denies this*, **never** *for no `?x`*.

**And a rule sees one binding at a time.** To know that no *other* binding exists you must have
enumerated them all — and enumeration happens inside `match`, which is the floor. The fact *there are
two matches* exists only in the matcher and never reaches a rule.

So three things cannot be said, and they are one thing:

| | wanted | shape |
|---|---|---|
| §2.6 | *nothing was told about `veteran(ann)`* | **no** match |
| §2.12 | *`p` held at every moment of this span* | no **counterexample** |
| §2.23 | ***the*** goblin — exactly one satisfies this | exactly **one** match |
| §2.23 | *nothing has handled this description yet* | **no** match |

> **All four are claims about the SET of matches, not about any match.**

## 4.2 The shipped precedent — this has been solved twice already

`machine.py:93-98`, on root goals:

> a root goal is a `goal(?w)` with **no** `subgoal(?p, ?w)`, which is a negative existential, and a
> `-` member says *an entry denies this*, never *for no ?p*. So it gets the treatment `blocked` got —
> **a REQUEST the machinery answers by looking**, because an aggregate over what the rules produced is
> the machinery's business and not a rule's.

`root`/`rooted` and `blocked` are both **asks**: a rule writes the request, the machinery answers by
enumerating, the answer lands as an ordinary fact. **The mechanism exists twice as a special case.
What is missing is the general one.**

## 4.3 The unifying primitive: count the matches of a pattern

All four rows reduce to one question — *how many ground matches does this pattern have here?* — and
then an ordinary comparison:

| | as a count |
|---|---|
| nothing was told | `0` |
| held throughout | counterexamples `= 0` |
| **the** goblin | `1` |
| not yet handled | `0` |

One request, four uses, and the comparison is a corpus's own rule rather than four bundled
meanings. That is *rows, not branches* at the level of the feature itself.

## 4.4 What falls out — four constraints, none optional

1. **The answer is a dated fact, not a return value.** `counted(<pattern>, 2)` is an entry with a
   locus, so it is deniable, attributable, and `why`-able like everything else — and superseded when
   the count changes, by §4's ordinary read. Nothing new is needed for that.
2. **It is not monotone, by construction.** A count is true of a moment and can be falsified by
   the next entry. This is §3.1's finding 1 in a third place — *an answer computed once, from a world
   that then changed* — except here it is inherent rather than a bug. The retraction fix built in
   §3.1 is what a cached count must ride on, and that must be **checked, not assumed**.
3. **The ask is generic, and the gate refuses generic propositions.** `count(veteran(?x))`
   contains a free variable, so both the parser's binding check and §13's gate refuse it — as they
   should. The precedent is `forbidden`: a corpus already writes
   `fact forbidden(doing(harm(?x)))`, a **mentioned** generic fact the machinery unifies against.
   The count ask takes that shape, which means Part 1's `Entry.mention` stops being an audit item and
   becomes load-bearing.
4. **Cost is the matcher, on demand.** Counting means running the pattern against the state. Bounded
   by the state, paid per ask — so the fast path matters: no corpus that never counts should pay.

## 4.5 …and it is what makes the *done* marker work

§2.1's state-machine programme and this are the **same requirement**, which was not visible until the
interpreter broke.

The simplest implicit state machine is *mark it done, and never work on done things*. Written the
obvious way it fails, and §2.23 measured how: the guard is `-handled(?d)`, `−` means **denied and
never absent**, and the set of `?d` is unbounded, so the negative cannot be stated in advance.
Written with a count it needs no negative at all:

```
-handled(?d)                    requires a denial nobody can write
counted(handled(?d), 0)         a claim about the set of matches
```

**And that repairs §2.1's other wall too.** §2.1 found that a state marker does not supersede its
predecessor — `stage(m, new)` and `stage(m, handled)` are different propositions, so both hold, and a
state machine whose states can all hold at once is not one. §2.1 concluded that a declared
**functionality** was needed. It is not:

| §2.1 wanted | as a count |
|---|---|
| `functional(stage, 2)` — one value in this position | `counted(stage(m, ?s), 1)` |
| an exclusive family | `counted(state(x, ?s), 1)` over the family |
| *not yet handled* | `counted(handled(d), 0)` |

So **functionality stops being a declaration and becomes a claim** — dated, attributed, deniable,
and arguable, which is the trade this design has taken every previous time (grades → `likely`, span
containment → `during`, precedence → read from the graph).

**`refutes` is NOT subsumed**, and saying so keeps the claim honest. *`sitting(x)` and `standing(x)`
cannot both hold* is about two **named, distinct** propositions, not about the size of a match set. It
remains the open item `rules-design.md` §8 records — but it is now the *only* one of Part 2's
candidate primitives that the aggregate does not cover.

## 4.6 The decisions to take before writing code

* **Where does it run?** At the write (like `_forbid` and `_answer`), or as a structural relation the
  matcher walks? The first is the `root`/`blocked` precedent; the second would make a count matchable
  directly and negatable, but puts a search inside matching.
* **What is counted — entries, or bindings?** *Nothing was told* is about **entries**; *the goblin* is
  about **bindings of a variable**. These are different questions and may need different asks.
* **What settles the aggregate's own moment?** A count over a still-growing derivation is the
  half-built-extension problem §3.1 found. `root`/`blocked` are asked at quiescence for this reason,
  and the general form needs the same discipline or an explicit locus.
* **Does it conclude, or propose?** Per `a-tool-is-data`, an answerer proposes. A count is a fact
  about the agent's own state rather than about a world, which argues it may conclude — but that is
  an argument to make, not to assume.

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

### Finding 1 — a negated structural member is evaluated once, and the application is cached

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

`match`'s own docstring states the precondition this violates:

> Safe only because the strata are **ORDERED**. §6's fixpoint is built from below, so a negated
> member names a relation whose derivation is **finished before this rule is reached** […] Negating a
> relation still being derived would answer from a half-built extension, which is the one way a
> rule-level read could disagree with the walk non-deterministically.

**That precondition is false for any structural relation that grows during the run** — and
`in_delta`, `delta_next`, `rests_on` and now `licensed_by` all do, because they are deposited on
every write. The strata are ordered *among themselves*; they are not ordered against the ordinary
loop that keeps feeding them. So the guarantee holds for the chain's *shape* and not for the chain's
*contents*, and the difference had not been drawn.

This is **pre-existing**, not introduced here: both mechanisms — delta-match caching and
negation-as-failure on structural members — were untouched by the three-line change, which only added
a relation to a dict. What the change did was make the interaction reachable from an ordinary corpus.

### Diagnosed exactly: the invalidation machinery is present, correct, and cannot help

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
        continue          # a re-match that no longer yields {?x: bob} cannot remove it
    cache["apps"][k] = a
```

> **A full re-match can only ever ADD. Nothing in the engine can retract an application that
> the world stopped supporting.**

Step 1 retires applications when a later *entry* unsettles them (`cache["by_prop"]`). A structural
fact has no entry and sits in no delta, so that path never sees it. **The fix is therefore narrow and
locatable: when a rule's cursor is dropped for grown structure, its previously cached applications
must be dropped with it rather than merged into.** And it needs a check, because 537 pass with the
defect live.

It is also invisible to the suite: 537 checks green with the defect live. Consistent with
`a-check-that-stopped-being-able-to-fail` — nothing asserts that a negated structural member is
re-read when its relation grows.

### Finding 2 — `_stored`'s anchor test asks `is_var` where it means `has_var`

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
elsewhere. Any corpus writing `rests_on(?e, foo(?p))` or `in_delta(?m, bar(?x))` gets a full history
scan today, silently.

### Status of experiment (a)

**Its question is unanswered and now blocked.** *Told beats inferred* cannot be evaluated until
Finding 1 is fixed, because the guard it needs is the thing that does not re-fire. The three-line
`licensed_by` change is **uncommitted, unexercised by any check, and therefore debt by `ugm.bundle`'s
own standard** — a relation no fixture can kill is a relation nothing is testing. It should either
get a check or be reverted; it should not sit there green and unused.

## 3.2 Experiment (b): `dormant` / `due` as a corpus-authored layer gate

**The mechanism works exactly as §2.4 predicted, with no engine change.**

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

**But be exact about what it bought.** The answers are identical to §2.6's ungated working corpus,
which reached them in 5 ticks without any gate. What the gate adds is not a different result — it is
the *guarantee* that the action rule cannot run against a half-closed world. That guarantee is
unfalsifiable on this fixture, which is the trap `guard-address-probe` recorded: **a homogeneous
fixture cannot measure a discriminator.** A fixture where interleaving genuinely produces the wrong
answer is what would make this a measurement rather than a demonstration.

### And it does **not** fix the §2.6 defect — decisive negative

§2.6's original failing corpus, with the action layer gated:

```
fact dormant(<legs>)
rule <legs> = implies( { +person(?x) }, { +has_legs(?x) } )
rule <open> = implies( { +person(ann) }, { +due(<legs>) } )
fact -has_legs(bob)
```

→ `has_legs(bob)` = **`+`**. 5 ticks, quiescent.

**This cleanly separates the two problems, which had been running together since §2.4.** Ordering
is a *layering* problem and `dormant`/`due` solves it. Default-eats-exception is a *deposit-order*
problem and no amount of layering touches it — it needs the second axis of §2.8, and the only
discriminator available is still `Entry.licence`.

## 3.3 Refusal **is** deferral — and my first measurement of it was wrong

> **The position.** *Refusal is not deferral* is not an engine issue. It is a limitation that more
> rules can solve: rules that react to a withdrawal.

Tested on machinery that exists today, because the gate already refuses (`_forbid`, §19's veto) and
already records the refusal as `refused(<proposition>, <sign>, <what forbade it>)`.

### First run: a false negative caused by the probe, not the engine

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
finished writing about it. The tell was available and I did not read it: a companion rule matching
`-forbidden(greets(ann))` derived nothing, while one matching `refused(?p, plus, ?w)` derived fine.
One member failing and its neighbour succeeding is a *naming* symptom, not a semantics one.

### Re-run in one scope — and the answer is stronger than the proposal

Same corpus, withdrawal loaded into the same scope, **and no recovery rule anywhere**:

| | |
|---|---|
| with the prohibition | `greets(ann)` = `None`, 1 refusal recorded |
| after the withdrawal | `greets(ann)` = **`+`**, in 2 ticks |
| what applied | **`<act>`** — the original rule |

**Refusal already behaves as deferral, with zero extra rules.** The blocked application is not
discarded: once the prohibition is denied, `_would_change` sees the proposition would change, the
rule is re-proposed, and it applies. `arbitration-is-scheduling`'s *a loser is deferred, not
rejected* holds at the gate as well as in the chooser, and nothing had to be built for it.

So the position is right that it is not an engine issue, and understates the case: **it is not a
limitation either, and needs no rules at all.** What rules are for here is *reacting* to a refusal —
noticing it, reporting it, choosing something else — and that half is measured working:
`refused(?p, plus, ?w)` matches and a corpus can read every refusal, its sign, and what forbade it.

**What this does not yet show.** The recovery was measured for the **norm veto**, which is the only
refusal path that exists today. An authority check at intake (§2.9) would be a *second* vetoer on the
same `gate.veto` list, so it inherits this behaviour by construction rather than by luck — but that is
an argument, not a measurement, until the vetoer exists.

And one real limit is now visible: the prohibition was revisable only because its pattern is
**ground**. `_forbid`'s docstring says so — a generic norm cannot be revised from the surface, because
`-forbidden(doing(harm(?x)))` written twice denies a different node (§8 scopes variables to a
statement). Ground norms are revisable; generic ones are not. §21.

## 3.4 What the experiments changed

| §2.8's table | now |
|---|---|
| (a) make `licence` readable → *told beats inferred* | **blocked** by Finding 1; produced two engine defects instead |
| (b) closure layer via `dormant`/`due` | ✅ **works**, no engine change — but the fixture cannot yet show it mattering |
| `always` = defeat-immunity in arbitration | untested; unaffected |
| one axis doing two jobs | **confirmed by 3.2's negative** — layering cannot substitute for strength |

**The order of work has changed.** Before Finding 1 is fixed, *nothing that relies on a negated
structural member can be trusted* — which includes `rules-design.md`'s own `round_span`/`silent`
default-over-an-open-domain example, the one §2.7 cited as proof that negation as failure was never
missing. That example may be sound only because its structural relations happen to be settled before
the ordinary rule is reached; whether that is guaranteed or accidental is now an open question about
already-shipped behaviour, and it should be checked before anything is built on top of it.

---

### Minor, found while probing

`authoring.md`'s snippets use `--` for inline comments. The tokeniser (`text.py:82`) accepts only
`#`; `--` is a parse error on the first line that carries one. Copy-pasteable snippets are that
document's stated promise, so this is a real defect in it.

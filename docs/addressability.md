# Addressability — the through-line, and what it re-orders

**A design note. Nothing here is built.** It records the conclusions of one long design session, the
probes they imply, and the places where a conclusion is a *prior* that can still come out wrong.

Read [harmony.md](harmony.md) and [facts-as-nodes.md](facts-as-nodes.md) first; this note sits on top of
both and changes how one of them is used.

## ⭐⭐⭐ The through-line

Every gap examined in this session — `step[i+1]`, disjunction, negation, *why*, partiality, taking turns
— turned out to be **sayable in some medium and unreachable by a rule**. `[i+1]` is trivial in Python.
So is a rules-as-data engine with a search that explains itself; that is what `ugm/` *is*.

> **Every expressiveness problem in this project is an addressability problem in disguise.**

Which means the frontier is not *can it be represented*. Encoding is free and buys nothing — that is
already the reason Turing completeness was ruled the wrong analogue, and *without encoding* the stated
criterion. The frontier is everything downstream: can a rule ask for it, can another author's KB consume
it, can the answer cite it, can the gap be named.

⚠ **The honest form of the claim, which is weaker than it is tempting to state.** The bet was never that
Python cannot do this. A sufficiently careful Python program has rules as data, a resolver, and
derivations — Greenspun's rule in its serious form. The bet is that **these specific commitments are worth
making once, in a substrate, rather than re-made ad hoc per program**, and it is won or lost on exactly
one test: *a question nobody designed for.* See §*The probes*, item 3.

## Findings that change the plan

### 1. ⭐⭐⭐ Bridges reconcile NAMING, not COVERAGE

From `../pystrider/docs/vocabulary_bridge.md`, which ran the probe:

| gap | the two authors disagree about | who can fix it |
|---|---|---|
| **naming** | what to *call* a thing | a bridge — 2 lines, no author moves |
| **coverage** | what *exists* | only the vocabulary's author |

**Both look identical from outside: a question returns nothing.** That settles *grow or bridge* —
bridging fixes naming, growing fixes coverage, and neither substitutes for the other.

⭐⭐ **The load-bearing consequence is `not_modelled`.** Without an audited marker naming the coverage gap
out loud, every coverage gap *looks* bridgeable and somebody bridges it, the bridge does nothing, and
nobody can say why. That is the three-state stance at the **vocabulary** level — same shape as signed
membership, same shape as UNKNOWN, same reason.

⭐ The methodology transfers too: the probe pins the two vocabularies **disjoint** (so the demo cannot
quietly become convergence) and removes the bridge to confirm the pattern then answers nothing. Positive
and negative control on one probe.

### 2. ⭐⭐⭐ The shared vocabulary is shaped by QUESTIONS, not entities

> The neutral question vocabulary … should describe **questions about code**, not either side's mechanics.

This is why the hub escapes the upper-ontology failure. DOLCE/BFO/SUMO index by **entity kinds**, which
forces every domain to distort its content to fit; a question vocabulary asks each author only for a
mapping into *the questions* and leaves their mechanics untouched. O(N) bridges, and a third author edits
no existing rule.

⭐⭐ **In ugm terms: the neutral layer is the matrix's COLUMNS, not its rows.** What two independently
authored domains must agree on is *the questions that can be asked of them*, not the entities they
contain. That re-points the coverage pass: a category is covered iff it can answer the neutral questions,
and a category that relates to nothing is one nothing can ask about.

⚠ **What the probe does NOT establish.** pystrider's vocabularies are **co-referential by construction** —
write-side and read-side describe the same Python program; business, UX and Textual describe the same app.
A neutral layer is guaranteed to exist because a common referent underwrites it. Two independently
authored *business* domains have no shared artifact. So O(N) bridges is **proven for layered views of one
thing and assumed for unrelated domains**, and the scope statement wants the second. See §*The probes*,
item 6.

### 3. ⭐⭐ Partiality has one shape, and it is already on the build list

A partial model is the operator set. Partiality is separable into three axes, and they reduce to one
shape:

| axis | *"I don't know…"* | the three states |
|---|---|---|
| **coverage** | …what happens here at all | present / absent / **no entry → UNKNOWN** |
| **precision** | …how much, how far, how long | bound / refuted / **unconstrained → UNKNOWN** |
| **confidence** | …how firmly, on whose word | outranks / outranked / **incomparable → UNKNOWN** |

The recorded failure is identical on all three: *a deterministic arbitrary order looks like an answer.*

**Obligation is closed; content is open**, and the split is per axis:

| axis | obligation (machinery) | content (KB) |
|---|---|---|
| coverage | the three states exist; silence ≠ no | which entries exist |
| precision | a member may be unbound, and reading it **refuses** | the constraints on it |
| confidence | the final comparison is **total** (`seal_rule`) | `overrides`, authority, the force categories |

⭐ So there is **no interval type, no qualitative algebra, no deontic vocabulary** in the machinery.
Precision needs *constrainable unbound members* — the same unbuilt capability as the order core and
`has 0 <label>`, not a fourth thing. Qualitative physics becomes a KB, not a feature.

⭐⭐ **The migration mechanism is table dispatch**, and it has already run once on this axis:
`python -m ugm.horizon` reports precedence stages and strengths at **zero** dispatchers, because the
ranking is authored data dispatched through `precedence._COMPARE`. *A closed set becomes revisable when
its dispatch becomes a table.* `consequent.KINDS` is still a Python tuple; that is the named target.

⚠ **The floor, said out loud.** Totality cannot come from the KB, or a comparator is needed to compare
comparators. The irreducible machinery on every axis is an **asking** capability, not a vocabulary —
*is this pair comparable, is this member bound, does the chain have an entry* — which is the `VKIND`
pattern generalised: **a program that cannot catch must be able to ask.**

⚠ And *learned from the KB* and *read from the KB instead of hardcoded* are one build apart. The second
is the prerequisite; theory revision on top of an authored seed is the first.

### 4. ⭐⭐⭐ Procedures are compiled searches — which leaves the forward direction open

An expert-authored `method`/`procedure` **is a means-ends search that a human already ran and froze** —
the same thing a Python program is, written in your language rather than theirs. `compile_episode` is the
other source of the same artifact.

That closes the *compilation* item and exposes a conflation:

| | question | state |
|---|---|---|
| **backward** — goals, procedures, HTN | *what would make this true?* | ✅ |
| **forward execution** | *what's the next step of this sequence?* | ✅ — the procedure running |
| **forward chaining** | ***what does this make true?*** | ❌ |

**A purely backward agent cannot be surprised.** The choice point handles *I cannot fill this guard*,
which is backward. It does not handle *something happened that nobody asked about* — the 1990 vacuum
cleaner, the near-miss at the edge of the KB, a standing constraint broken by a step. `deviates` and
`unmet_expectations` are recognition, but they are **called by the driver at fixed points** rather than
triggered, so the capability exists as one hardcoded moment rather than as a direction.

⭐ **And the cheap form is not RETE.** RETE assumes one working memory and this engine branches, and the
`_covers` probe measured matching at 0.6 ms across the whole suite. What is wanted is a **bounded sweep at
declared moments** — *what just became true, and which rules almost matched* — which serves **three jobs
at once**: near-miss boundary detection, noticing-unasked, and delta-triggered constraint violation. One
mechanism, three uses; that is the argument for building it.

⭐ If forward evaluation ever needs to be general rather than bounded, **magic sets** is the standard way
to keep it goal-directed — and this engine already has the idea: **the guard address IS the magic
predicate**, found by measurement (bindings 11 → 1153) and promoted from an optimisation to a requirement.
The difference is that ugm's is authored per rule and the textbook version is a systematic rewriting.
⚠ It must be **derived at query time, not stored**, or it is the dormant-twin problem at corpus scale.

### 5. ⭐⭐ The closed-class axes compose as a PATH, and the map collapses

The proposal was an N-dimensional map over closed axes (certainty, force, polarity, logical relation).
⚠ **A flat coordinate cannot express scope**, and scope is where the meaning is: `not(ask(p))` and
`ask(not(p))` share all three coordinates and mean different things. The right structure is **nested
hubs** — operators over propositions — which the encoding already gives for free at any depth.

Formally: a **non-commutative monoid**, presented by generators (the axes) and **relations** (which swaps
preserve meaning). The relations are the knowledge.

⭐ **Only unary operators form a path.** `not`, `likely`, `ask`, `must` are path steps; `and`/`or` are
**branch points**. So *logical relation* is two different things, and the split lands exactly on the
cheap/expensive line: **disjunction over a closed axis is finite set membership; disjunction over
propositions is reasoning by cases.** Most disjunctions a rule wants are the first kind and are
affordable today.

⭐⭐⭐ **And if the axes stratify, the whole thing collapses.** Cinque's hierarchy of functional
projections is the empirical result — operators fall into blocks with a *fixed* relative order, and an
outer operator is transparent to what is inside. Then:

* **within a block** — several orders, different meanings → **table entry required**
* **across blocks** — one legal order → **no entry**, and illegal orders `REFUSE`

The map becomes **one linear stack order plus a few small within-block tables**. O(Σ kᵢ²) rather than
O(n²), and nowhere near the O(∏ values) of flattening into distinct primitives.

⭐⭐ **The table's shape validates its own generators.** Block-diagonal → the axes are real. Dense → the
axes are cut wrong. And a **row that is irregular across its partners** means the operator is overloaded —
`next`-over-three-relations arriving in the closed class rather than the open one. Expect `not` to be the
messy one; negation genuinely occupies several strata, and *that* is where splitting into distinct
primitives is right (deontic logic takes O, P, F as primitives and derives `F(p) ≡ O(¬p)` as a theorem).

⚠ **Flattening the closed class is name mangling.** `forbid_likely` and `likely_forbid` encode the same
interaction *inside an identifier*, where no rule can ask what they have in common — B3 one level down,
and the argument `predicate-dispatch.md` already made.

⚠ **The gate still governs.** Every *doesn't commute* entry owes two situations in which the agent acts
differently. If you cannot produce them, the honest entry is *commutes, as far as we act*.

⭐ **A place where the graph beats NL**, and they have been rare: scope ambiguity is a defect of **linear**
form. The graph has explicit nesting, so scope is unambiguous by construction. ⚠ At the cost of having to
**commit** to it even where the author was indifferent.

### 6. ⭐⭐ Asking is cheaper than deferring

Three ways to handle a choice that cannot currently be made:

* **defer** → fork a frame; branches multiply, and there is no mechanism to reason across them (the ATMS
  was deliberately deleted). Affordable for a handful.
* **guess** → what an LLM does. Hides the branch, no residue, silently wrong.
* **ask** → **collapses the branch to one world for the price of one question.**

That is an *architectural* justification for the choice-point protocol rather than an ergonomic one. It
also sharpens the asking policy: **ask iff the answer would change what you do** — imagine both branches
on the workbench; if the plans differ, ask; if not, pick either and **record that it did not matter**. The
discrimination pair as a runtime test, producing residue an LLM cannot: *I did not ask about the colour
because both readings planned identically.*

⭐ **A choice point is a hole in a sketch, at runtime instead of at synthesis time** — which unifies three
threads that were being treated separately: the learning formulation (*fix the forms, search the
fillers*), the partial model (present/absent/unknown), and the middle-ground design. Same shape.

⭐ It also **localises relevance instead of solving it**: at a declared choice point the missing
information is exactly *the guard's addresses that could not be resolved* — finite and computable, where
*what don't I know* is unbounded.

⚠ The named blocker is **predicate dispatch slice 4** (a gap becomes a want, not a refusal), which is now
the third independent thread to require it. Prior art: **Soar impasses** plus **chunking** — the same
protocol *with the memory half*, in a working architecture for forty years.

⭐⭐ **Choice points are not disjunctions**, and the difference is dual: a disjunction is nondeterminism of
*nature* and needs every disjunct to support the conclusion (∀-shaped, multiplies worlds); a choice point
is nondeterminism of the *agent* and needs one branch to work (∃-shaped, ordinary search). ⚠ But
**deferring a choice converts it into a disjunction**, which is when the cheap thing becomes the expensive
one. Invariant worth writing down: **a fact in the world is never "p or q"** — uncertainty lives in frames
and in claims, never in the assertion.

⚠ Housekeeping: the residue item recorded as *disjunction, sayable but unconsumable* is misnamed. The
engine branches fine. It is **reasoning by cases over disjunctive knowledge**.

### 7. ⭐⭐ `why` is opinionated, and the fix is a parameter

ugm's `why` is **derivational** — the chain of rule applications — which is roughly Hempel's
deductive-nomological account and has the tell of an implementation artifact: it is the theory of
explanation that falls out of how the machinery happens to work.

| account | *why is this customer overdue?* answers with |
|---|---|
| **derivational** (Hempel) — what ugm does | the rules and facts it followed |
| **interventionist** (Woodward) | what would have had to be different |
| ⭐ **contrastive** (van Fraassen, Lipton) | why *this* one and **not that one** |
| **pragmatic** (van Fraassen) | there is no context-free answer |

⭐⭐⭐ **The substrate does not remove the opinion; it moves it from a procedure to a rule.** In ad-hoc
Python the theory of explanation is implicit in the search code; here a different theory should be a
different *reading* of the same residue, i.e. predicate dispatch. **The probe is: can a second theory of
`why` be written as a rule, without touching the engine?** If not, the residue is a differently-shaped
hardcoding.

⭐ **Apply the admissibility rule to `why` itself.** *Something may be a primitive iff every decision it
embodies can be an argument* — and a `why` that hardcodes its contrast class fails that test. So
`why(P)` becomes **`why(P, against: Q)`**, with the derivational reading as the degenerate case where the
contrast is nothing at all. That is how the literature says the derivational account relates to the
contrastive one: a special case that mistook itself for the general one.

⭐⭐ **Contrastive why is the discrimination pair read backwards.** The standing test is *two situations in
which the agent acts differently*; contrastive why is *two situations — why did it act differently*. Half
the instrument exists.

### 8. ⭐⭐ Counterfactuals need no new machine — and the do-calculus distinction is already made

**Counterfactual explanation is planning with the goal *make the answer different*.** Frames are modified
worlds, `step` recomputes, comparison is `deviates`. Same means-ends search, new constraint; what you want
back is the plan's first step rather than the plan. Same shape as *recognition and prescription are the
same predicate read two ways*.

⭐⭐⭐ **Frame = intervention; hypothesis = supposition.** Pearl's `do(X)` cuts X's incoming causes where
observation propagates backward, and getting that wrong gives the observational reading of an
explanatory question. The engine already separates them — *a technical frame is not a logical frame* —
so the hard part of causal counterfactuals is paid for, by a distinction made for unrelated reasons.

What is genuinely new is small: **minimality** (a preference over interventions — `precedence`, authored
data, `run <fn>` covers it) and **cost** (*which of these twenty facts would flip the answer* is twenty
searches).

⚠ **The gap that bites: forward counterfactuals are free, backward ones are not.** *What if we had sent
the reminder last month* needs the world to be a **history**, and the recorded gap says it is not — *the
world graph is a single mutable state; frames are imagined futures rather than recorded pasts.* And that
is exactly where the business use case lives. The near-term honest shape is **counterfactuals over the
derivation** (`application.py` has the record) with world-history named as a limit rather than
approximated.

## Gaps newly named

| gap | note |
|---|---|
| **goals over trajectories** | *taking turns* cannot be confirmed because `holds` evaluates a **state** and turn-taking is a property of a **sequence**. The protocol/order blank row reached from a new direction — and the reason PDDL needed trajectory constraints in 3.0. ⚠ **Reifying the turns does not close this** — see below |
| **the forward direction** | procedures do not supply it; recognition is the weak column *because* of this |
| **backward counterfactuals** | blocked by the world-history gap |
| **cross-domain composition without a shared referent** | pystrider proved it for **co-referential** views of one thing; unproven for unrelated domains |
| **contrastive `why`** | and its fix is a parameter, not a mechanism |
| **`why` as a rule** | operations-as-data is write-only (B3); a second theory of explanation currently means editing the engine |

⭐ **And one gap that turned out already solved.** *Did my plan achieve this, or did it happen anyway?* is
answered by `ugm.leak`'s invariant read as credit assignment: **an achievement not attributable to the
frame's transformation IS "by accident."** No new machinery.

### ⚠ Why reifying the turns is not enough

The obvious objection: *reify the turns, then checking "taking turns" is an ordinary procedure over the
reified representation.* That is **right for the `check` column** — with the order reified, `step[i+1]`
stops being a literal and the successor is a node reached by an edge, so the sentence becomes a constraint
over two related nodes. `facts-as-nodes.md` already claims that payoff, and it holds.

Three things survive it, and only the first is small.

1. ⭐⭐ **The goal's SUBJECT is not addressable.** Reifying the elements does not make the *sequence* a
   thing a constraint can point at. `holds` evaluates against a frame — a state — and *taking turns* is a
   property of the plan or the history. Saying *these two steps have different agents* is now easy; saying
   *the plan has the property that every adjacent pair does* needs the plan to be a node.
   [defining-terms.md](defining-terms.md) already reached this: **it is a TYPE whose subject is the PLAN**,
   and the three hardcoded plan sorts should collapse into *the plan is a node you can constrain.*
2. ⭐ **Quantification over the sequence.** The constraint is universally quantified over adjacent pairs,
   not a conjunction of two. Whether the constraint language expresses that is an open question, and
   *is `has 0 <label>` expressible* is on the probe list for the same reason.
3. ⚠⚠⚠ **WHICH successor, and who reified.** Reification does not say which of the five orders the `+1`
   is — that is the relatability requirement, and it needs the **shared core**, not a sixth relation. And
   more sharply: if the turns are *already* reified, the recognition has already happened. `taking turns`
   over a trajectory of raw actions is an **interpretation**, and this document's own warning applies —
   *a recognizer that writes `taking_turns` as a plain fact has laundered an interpretation into an
   observation.* So the objection is sound where turns are what literally occurred, and assumes the answer
   where "turn" is a reading imposed on lower-level events.

**Net: reification closes `stated in` and `check`. It leaves `recognise` (nobody asked) and `plan` (no
causal model) exactly where they were** — which is consistent with the matrix, where the weak column was
never `check`.

## The probes, in order

Each must be able to come out badly, and each entry says what a red would change.

**1. Shuffle mode.** Randomise iteration order wherever the substrate hands back a collection, checks
only. Nearly free, no design, tests the whole substrate at once, and it is the only reliable detector of
*storage masquerading as content*. ⚠ **Urgent before the hub conversion** — the inverted copy boundary has
no order at all (`Graph.inc` is a `set`), so latent order-dependence gets worse the moment it starts.
*Red → order is leaking; fix before converting.*

**2. The commutation table.** Enumerate **adjacent pairs** of closed-class operators — O(n²), not the
v^n cross-product — and ask of each: *does swapping preserve meaning?* Four answers, all informative:
commutes / doesn't-and-both-meaningful / one-order-meaningless (a `REFUSE` rule) / idempotent.
⭐ Prediction, recorded so it can be wrong: **mostly transcription.** Several entries are already forced by
decisions on record — `not × likely` cannot commute given the three-state stance, because *"not likely he
came"* is sayable with no evidence either way while *"likely he didn't come"* claims evidence for absence.
*Red (dense table) → the axes are cut wrong; rethink before building on them.*

**3. ⭐ The unanticipated-question probe.** Write *overdue customers* twice — straightforward Python with
rules-as-data and a search, and on the substrate. Same rules, same answers. Then ask questions **neither
author designed for**:

* *Which other conclusions rest on this same invoice?*
* *If we changed the grace period, which answers would change?* (an interventionist why)
* *Was this customer ever not overdue, and what made it flip?*
* *Anna overrode this last month — what else did she override for the same reason?*

Count how many each answers **without new code**. ⚠ **This is the first probe that tests the thesis rather
than a mechanism**, and its failure condition should be written down first: *if the substrate version also
needs new code per question, the substrate bought nothing.*

**4. The bounded post-step sweep.** *What just became true, and which rules almost matched.* Bounded by
the frame's delta, which is already sparse and already computed. Three jobs in one instrument.
*Red → the forward direction needs more than a sweep, which is worth knowing before designing one.*

**5. `find_function` resolving through the context.** One native, already owed, and it unblocks *can a
workbench step call a function whose body the frame changed* — which the machinery-description thread
rests on entirely.

**6. The cross-domain probe.** Two KBs with **no common referent** — one physical/causal/economic (vacuum
repair), one abstract/rule-governed (a chess opening repertoire, or harmony rules). ⚠ **The fixture trap
is specific**: the obvious pairs secretly share structure — a repair shop and a hospital rota are both
*jobs assigned to people over time*, which is a shared referent smuggled in.

Controls, neither optional: **pystrider's own business/UX/Textual triple** as the positive control (the
procedure must rediscover a bridge known to exist), and a **planted coverage gap** — ask the chess
repertoire *what does this cost* — which must return `not_modelled` rather than a failed bridge.

⚠ **Fix the question list before authoring the KBs**, derived from the matrix columns and the closed class,
or you will author questions you already know both can answer. Measure three things: surviving questions,
**bridge size** (pystrider's are two lines; if these are two hundred, the O(N) claim is true and dead), and
the two pins reused verbatim.

⭐ **Prediction, recorded so it can be wrong: the surviving questions will be almost entirely
closed-class** — which would mean the *shared core* and the *question vocabulary* are one object, not two.

**7. The rulebook probe.** Take a rulebook written for humans and enumerate what it **assumes** rather
than states. That list is a candidate closed class, **derived rather than authored**, and it can be scored
against the two existing criteria to see whether they agree. ⭐ Blocks world already supplies one finding
for free: it assumes single-support and never says so — and `clear(a)` is a **lexicalized negation**, which
makes it the free positive control for the orthogonality audit below.

**8. The masking probe** ([passes.md](passes.md)). Mask parts of a KB and ask whether the system
reconstructs them. ⚠ With a behavioural gate — reconstruction is a representational criterion, and the
standing rule is *would the agent act differently* — and a positive control, since a run that recovers
nothing and one that cannot see are the same report.

## The orthogonality audit

Cheap, derived, and it does two jobs.

The closed-class axes are supposed to be indifferent to open-class content. **They leak exactly where an
open-class term lexicalizes a closed-class combination** — `prevent` carries a negation, `forbid` carries
force plus polarity, `fail` carries negation plus result, `clear` is a negated existential. Natural
languages do this constantly, and `prevent` does not *decompose* into `cause(not(p))` while *behaving* as
though it has a negation in it for scope purposes.

> **Take each commutation entry. Test it across many open-class terms. A term where the entry fails is
> carrying hidden axis content.**

⭐ And the same output answers a second question — *composition or overloading?* An operator that applies
uniformly to arbitrary new content is composing; one that only works for particular content is an idiom
wearing composition's clothes. Same probe, read twice.

⚠ Orthogonality is a property you **defend**, not one you have — every new axis and every convenient verb
erodes it, so this re-runs, in the species of `access.offenders`.

## Two things to hold onto

⚠⚠ **Three separate questions landed on the same architecture** — *what is closed class*, *how do KBs
compose*, *grow or bridge*. That is either the architecture being right or one idea wearing three hats,
and the way to tell them apart is to **find a case where they give different answers**. If none exists,
they are one claim and it should be written down once.

⚠⚠ **The KB is written NL with no author present**, which is the *degenerate* case for natural language,
not the good one. NL is not island-free — it is island-**tolerant**, with a repair protocol (ask, clarify,
negotiate). Remove the loop and NL composes *worse* than a formal language: law, exegesis and historical
linguistics are industries built on that failure. So copying NL's shape inherits none of what was doing
the work.

⭐⭐⭐ **What composes structurally is the closed class; the open class composes only by repair.** The
Semantic Web tried to buy the second at the first's price — `owl:sameAs` between open-class terms, which
is not a bridge but a collapse — and that is the prohibition `harmonization.md` already writes down from
first principles. The three pieces of the repair loop are all named and mostly unbuilt: **noticing** (the
grain-boundary report from the episode record), **asking** (slice 4), **the bridge** (conditioned
substitution = slice 3, never `same_as`), with the record as *a claim with a speaker*.

## What is NOT concluded here

* ⚠ **Nothing here is measured.** Every ⭐ above is an argument; the probes are what would make any of it
  a finding. Two predictions are recorded explicitly so that they can fail.
* ⚠ **No feature named here is novel**, and that bound is already on record in
  [comparison.md](comparison.md): CLOS, ATMS, Datomic, 3-Lisp, effect handlers, BDI — and now Soar
  impasses, magic sets, well-founded semantics, Cinque's hierarchy and Pearl's `do()`. What would be new
  is the residue carried on them, which stays a hypothesis until the system reasons differently *through
  ordinary reasoning*.
* ⚠ **Cyclic open-class knowledge is not stratifiable in the Datalog sense.** A web with cycles through
  negation has no stratification, and the answer is **well-founded semantics** (Van Gelder, Ross &
  Schlipf), which is *total* and assigns **UNKNOWN** where stratification rejects. That is
  `unknown_is_not_no_unless_you_say_so` arrived at independently — but **it has not been checked that this
  engine actually behaves that way on a planted cycle through negation.** If it silently picks an order
  instead, that is *a deterministic arbitrary order looks like an answer* in the semantics rather than in
  the storage.
* ⚠ Three stratifications are in play and they do **three different jobs**: Cinque for well-formedness of
  the operator stack, Datalog/WFS for evaluability over the cyclic web, and the choice point for what WFS
  leaves undefined. Only the third is this project's to invent.

## On external libraries

Asked and answered, because the answer is mostly *no* and the reason is structural. Three kinds of thing
get called a library:

| | brings | island? |
|---|---|---|
| **data** — Ludii/GDL descriptions, PDDL domains, rulebooks, PROV-O as vocabulary | nothing that runs | ✅ no |
| **substrate** — RPython, Truffle/Graal | speed for *your* semantics, no opinion about meaning | ✅ no, but expensive |
| **reasoning** — clingo, Popper, ILASP, Z3, a planner, CLIPS | its own machinery **and its own semantics** | ❌ always |

**Bring in data freely, substrate carefully, reasoning never — as a component.** An external reasoner
returns an answer whose by-products are in *its* vocabulary and get discarded, which is the residue lost at
the seam. The discipline that rescues it is the one already settled for LLMs: **every external reasoner is
a boundary tool whose output arrives as an attributed proposal**, verified or re-derived internally. And it
only pays where **finding is expensive and checking is cheap** — which is true of exactly one item on the
list, harmonization's set-search, because its commit gate is already specified.

⭐⭐ Worth knowing regardless: **Ludii and GDL are the largest existing body of machinery-described-as-data**
— domain-independent runners over ~a thousand declarative game descriptions — and their **B3 failure is
free evidence**: a GGP player can run the rules and cannot explain them. Read the descriptions; never run
the engine.

## See also

* [harmony.md](harmony.md) — the four criteria, and §*Expressiveness is prior* which this note added
* [facts-as-nodes.md](facts-as-nodes.md) — the shape; signed membership is finding 3's mechanism
* [passes.md](passes.md) — the review findings this session produced
* [harmonization.md](harmonization.md) — the repair loop's three pieces
* [expressiveness-and-uniformity.md](expressiveness-and-uniformity.md) — requirements 1–3
* `../pystrider/docs/vocabulary_bridge.md` — finding 1, with the probe and the pins

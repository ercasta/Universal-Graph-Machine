# Forms — the closed class, and what makes it compose (the discussion)

**Status: design + reasoning trail, 2026-07-27.** Supersedes `docs/design/form_inventory.md`, which predates the
substrate inversion (that document is 07-20/22; the inversion is 07-26) and whose every *mechanism* column refers
to the retired `ugm` engine. What survives from it is carried here explicitly (§12); nothing else should be read
from it.

> **⚠ This is the ARGUMENT, not the specification.** It records how the positions were reached, including the
> wrong turns, because that is what makes them re-derivable. Two documents were split out of it, and if you want
> to *do* something rather than understand why, read those instead:
>
> | you want | read |
> |---|---|
> | **to shape the CNL, or to build** — principles, criteria, entry format, tests, build order | **`forms_cnl.md`** |
> | what this implies about LLMs, and what may be asked of the translator | **`forms_llm.md`** (expands §3.5) |
> | *why* any of it is believed, and what was rejected on the way | this document |
>
> The other two are derived from this one and must not contradict it. Where they do, this document is wrong and
> should be corrected — the reasoning is the asset.

Written from a working session with you. Your framing drove it, and the questions that moved it are marked where
they land: *"what are the categories?"* (§2), *"is there a catalog in the literature?"* (§6), *"how does 'the
closed class is small' coexist with 350 years of failure?"* (§3.2 — the result the document is now organised
around), *"is the boundary arbitrary?"* (§3.6), *"could embeddings encode the closed class?"* (§3.5), *"has
anything that works been built on harmony?"* (§4.5), and *"should the CNL mark the factorization?"* (§5.3).

> **⚠ Unfamiliar with the linguistics vocabulary? Read §15 first.** It is a glossary written for readers who
> know software engineering and not linguistics, with the compiler/type-system analogy for each term, plus
> entry points for further reading. Terms like FORCE, closed class, harmony and grammaticalization are all
> defined there.

---

## 1. The claim

> **The system holds the CLOSED class exactly and the OPEN class opaquely. Every form is an entry in the closed
> class, and every entry specifies what structure it contributes, what writes it, and what reads it.**

Three consequences, each argued below:

- **There is no catalog of categories to write.** Categories are a *product* of orthogonal axes, not a list (§2).
  Question, procedure and hypothesis — the three you named — dissolve into points in that product, and only one
  of them turned out to need anything new.
- **The closed/open line is not a convenience.** It is where 350 years of reduction succeeded and where it
  failed, and the failure has a name (§3). The same result that ended the reduction programme is the reason
  embeddings are the right tool for the other half.
- **Composition is the hard part, not enumeration** (§4). Fifty forms is a small list and 1,225 pairs. The
  literature's answer — *harmony* — is a **local, per-form check that buys global closure**, which is the only
  reason a set this size is tractable at all.

---

## 2. Categories are a product, not a list

### 2.1 The question, and why the obvious answer is the wrong one

Your statement of the problem:

> *"Even BEFORE we define the CNL, we need to define the correct in-graph representations, in a way that's
> consistent and composable. Only THEN can we target this representation as a compilation from CNL."*

The ordering is right and is adopted (§11). The word **categories** is where it goes wrong, and it goes wrong
against a position this project has already taken three times.

**Guards yes, kinds no** (`model.md` §11): when a distinction is needed it becomes a *fact something asserts*,
never a new kind of thing. A superstructure makes a distinction **unstatable**; uniformity makes it *statable but
unstated*, and only the second is recoverable. The design has already refused categories in three places, each
doing real work:

| | |
|---|---|
| `cnl.md` §4 | *"There is **no rule syntax**… being a rule is a conclusion an interpretation rule reaches"* |
| `cnl.md` §2 | *"There is **no force syntax**. No `?`, no `!`… a rule concludes it asks"* — **a question is not a kind** |
| `model.md` §8 | *"Plan, step, subgoal, and expectation are all the same shape"* — **a procedure is not a kind** |

So enumerating question/procedure/hypothesis as kinds would reverse all three.

**But the worry underneath the framing is correct and unanswered.** *If everything is an occurrence, what keeps
interpretation consistent and composable?* "The rules will sort it out" is not an answer. Something must be fixed
in advance. The rest of this document is what.

### 2.2 The three axes — carried over from `form_inventory` §4, and they are the answer

A commitment has three independent dimensions. This is `form_inventory`'s single most durable result and it
survives the inversion untouched, because it is a claim about *commitments*, not about mechanism:

| axis | question it answers | values |
|---|---|---|
| **CONTENT** | *what is claimed?* | degree, negation, conditionality, identity, quantification, tense, causation |
| **FORCE** | *what is being DONE with the claim?* | assert, deny, ask, command, author, retract, … |
| **LEVEL** | *what is the claim ABOUT?* | the world, the theory, the language |

**They are orthogonal, and that is the whole argument for keeping them apart:** any content can carry any force
at any level. *The lion generally has a mane* / *does the lion generally have a mane?* / *assume the lion
generally has a mane* differ only in force. **Three axes enumerate the sum where one list would have to
enumerate the product.**

> A "category" is therefore a **point** in CONTENT × FORCE × LEVEL, never an entry in a list. There is no
> catalog of categories to write, and writing one is the specific error `guards yes, kinds no` names.

### 2.3 The decision procedure this yields

For any candidate category, ask: **which axis value does it need, and does one already exist?** If it needs
nothing new, it was never a category.

Run on your three:

| candidate | verdict |
|---|---|
| **question** | FORCE = ASK. Already demonstrated: `cnl.md` §6 transcribes *"Should Paul get the discount?"* as ordinary content with `modality: should`, and a rule concludes it asks. **Not a category, needs nothing.** |
| **procedure** | FORCE = AUTHOR, LEVEL = theory. `model.md` §8 already collapses plan/step/subgoal/expectation into one shape. **Not a category, needs nothing.** |
| **hypothesis** | **Does not factor.** It is on no axis. See §4.4 — this is the one real finding, and the answer is that it is not a force at all. |

Two dissolved, one sharpened into a structural question. That is a better yield than a list would have given, and
it is the procedure to run on every future candidate.

### 2.4 What must be fixed in advance is the closed ROLE inventory

`cnl.md` §2 already decided **roles are a closed class while content vocabulary is open**, and it decided it on
measured evidence rather than taste — twice:

- **Retrieval stopped discriminating.** A pattern reaching a participant through a role matches `name = "agent"`
  explicitly, so `"agent"` enters its vocabulary, and every world containing any agent resembles every rule with
  an agent role.
- **Default coreference nearly ate the graph.** A rule merging *"two nodes with the same name"* fused every role
  node called `"agent"` into one, destroying every occurrence's participants.

Both are one fact: **role names already behave as a shared vocabulary whether or not one is declared.**

`cnl.md` §7 then leaves the inventory's *contents* open. That is the real form of your question — not *"is a
question a category?"* but *"which roles are in the inventory?"* A role is the genuinely composable,
surface-independent unit: `when:` means the same thing at any depth, in any statement, under any surface.

The inventory is **tiered**, and the current flat list of ten conflates the tiers (§9).

---

## 3. The central result: closed class exact, open class opaque

### 3.1 The two classes are different kinds of thing

| | **closed class** | **open class** |
|---|---|---|
| what it is | **structure** | **content** |
| how it works | composition | association |
| size | small, bounded | unbounded |
| how it is obtained | **designed** | **learned** |
| failure mode | **leaks** (disharmony) | **drifts** (approximation) |
| who holds it | the engine, exactly | the LLM, opaquely |

They are not two halves of one thing divided for convenience. They are structure and content, and the reason the
architecture works is that only one of them has to be got exactly right.

### 3.2 How "the closed class is small" coexists with 350 years of failure — *your question*

The reduction programme was real and serious: Leibniz's *characteristica universalis* (a catalog of primitive
concepts) plus a *calculus ratiocinator* (rules for combining them), so disputes end in *"let us calculate."*
That is this project's ambition, stated in 1679. The line runs Wilkins → Leibniz → Frege → logical atomism →
Carnap.

It attempted the **total** reduction — open class included. NSM still does: ~65 primes, everything else by
reductive paraphrase.

**Scored by halves, the result is lopsided, and that is the answer:**

| | outcome |
|---|---|
| **closed class** | **largely succeeded.** Logical connectives with harmony (proof theory, settled); grammatical categories — tense, aspect, number, case, modality (descriptive linguistics); thematic roles (FrameNet / PropBank / VerbNet, engineered and in production); speech acts (Searle, dialogue-act standards); aspectual classes (Vendler) |
| **open class** | **no successes.** Not one agreed decomposition of an ordinary noun, after 2,500 years |

So *"350 years of failure"* was imprecise. **The failure was concentrated entirely in the half already outsourced
to the translator.** That is the same line `cnl.md` §2 drew from retrieval evidence and `form_inventory` §2(a)
drew from the translator argument — reached a third time, from the history of a different discipline.

**Three caveats, so this is not oversold:**

1. **Membership is contested, and getting it wrong is the normal outcome.** `form_inventory` §3 records **five
   for five wrong** when classification was done by intuition. Determiners look closed; genericity turned out
   fundamental. *Small* does not mean *obvious*, and §12's probe discipline is not optional.
2. **"Small" is per-specification.** English does not grammaticalize evidentiality; some languages do. Others
   grammaticalize shape, social status, mirativity. The closed class is small *once you have decided what the
   system must be able to commit to* — `form_inventory` §6's point that **the inventory is a specification, not
   a survey**. That is a design responsibility, not a discovery.
3. **⚠ The difficulty moved from enumeration to composition, and this is the one that matters.** Listing ~50
   forms is mechanical — the residue log does it. Fifty forms is **1,225 pairs and unbounded nestings**, and
   that space is where the one measured leak lives (`degree ∘ negation`, `form_inventory` §9). A small closed
   class still has a large composition space. §4 is the answer to this and the reason harmony is worth
   transplanting.

### 3.3 What the open class is made of — *your question*

Not vocabulary that maps onto the closed class. **If it were, it would be decomposable, and that is exactly the
programme that failed.**

The accounts on offer, and note where they converge:

| account | open-class content is… |
|---|---|
| **informational atomism** (Fodor) | **nothing** — concepts are primitive; content is fixed by a causal/lawlike link to the world. There is no inside |
| **prototype / exemplar** (Rosch) | similarity to a central tendency or to stored instances; graded, no definition |
| **theory-theory** (Murphy & Medin) | a role in a folk theory |
| **inferential role / holism** (Quine, Brandom) | a **position in a web of inferences** |
| **distributional** (Firth, Harris) | **co-occurrence structure** — what embeddings implement |

The last two are one claim, stated philosophically and computationally. Which gives:

> **The open class is made of RELATIONS, not of parts.**

That is why it has no small basis — there is no basis, there is a web. It is why it is unbounded — relations to
everything. And it is why a high-dimensional relational encoding is the natural representation rather than a
lucky hack.

**⭐ The convergence, and it is the strongest single result of the session.** Quine's confirmation holism — the
result that *killed* the reduction programme, by denying that meaning factors into atoms — is the very same claim
that says a learned relational encoding is right for that half. **The negative result and the engineering
solution are one fact seen twice.**

### 3.4 ⭐ The boundary is a factorization, not a partition

The instinct that open-class words reduce is not wrong, only not *exhaustive*. The surviving decompositional
result is that an open-class word has a **closed-class skeleton and an irreducible remainder** — which means:

> **The closed/open boundary does not run BETWEEN words. It runs THROUGH them.** It is not a partition of the
> vocabulary; it is a **factorization of every lexical item**.

This matters because it dissolves a question that keeps getting asked in the wrong form. *"Is `near` closed or
open?"* has no answer, because it is both:

| *near*, from *"park the car near the theater"* | |
|---|---|
| **closed-class skeleton** | a binary spatial relation, **gradable**, taking a figure and a ground |
| **open-class remainder** | how near counts as near — context-dependent, unbounded, no definition |

The engine needs the first exactly — two roles, a degree, and the elimination rule (*from near(a,b), a spatial
relation holds to some band*). It needs nothing about the second and could not have it. Same for *park*:

- argument structure (agent, patient, location), aspectual class (accomplishment), change-of-state pattern —
  **all closed class**;
- what distinguishes *park* from *stop*, *leave*, *abandon* — **not closed class, not decomposable**.

Fodor's objection (§7.2) is the proof that the remainder is real. And this is what FrameNet / VerbNet / PropBank
*are*: the skeleton catalogued, the flesh left as a lexeme label.

⚠ **The practical consequence is §5.3's:** because the factorization is per-item and the skeleton is
*lexeme-invariant*, the skeleton belongs in a lexicon rather than being re-marked on every utterance.

**The design consequence, and it is concrete:**

> An open-class lexeme enters the graph as **an opaque name plus a link to closed-class structure** — its roles,
> its aspect, its intro/elim pair. The engine never needs to know what a car is. It needs to know that *park*
> takes a `patient:` and licenses a change-of-position conclusion.
>
> The open class supplies **identity and similarity**. The closed class supplies **structure**.

`form_inventory` §8 conceded the first half as a limitation — *"PROPOSITIONAL understanding, not grounding:
`has(lion, mane)` maps correctly while `mane` stays an uninterpreted token."* **It is not a limitation. It is the
architecture, stated accidentally.**

### 3.5 What this predicts about LLMs, stated at the strength the evidence supports

The tempting stronger claim — *base concepts are the dimensions of embeddings, which is why LLMs reason* — is
false as stated, for three reasons that are reasonably settled:

1. **Concepts are directions, not dimensions.** The basis is arbitrary; nothing privileges the coordinate axes.
2. **Superposition.** Networks represent far more features than they have dimensions, in near-orthogonal
   directions — so there is no dimension-to-concept correspondence even in principle.
3. **The counts are off by orders of magnitude in both directions.** A base-concept catalog is ~14 (Schank) to
   ~65 (NSM). An embedding has 10³–10⁴ dimensions and, under superposition, plausibly far more features — and the
   features recovered are a long tail of specific detectors, not a compositional basis.

**⚠ But the neighbouring claim, about DIRECTIONS rather than dimensions and about the CLOSED class
specifically, is defensible and probably true.** An earlier draft of this section said embeddings are simply
*bad at* the closed class. That is wrong, and the evidence points the other way:

- **structural probes** recover dependency parse trees from transformer representations by a *linear*
  transformation — syntactic structure in a linear subspace;
- part of speech, number, tense, gender and definiteness are all linearly decodable from contextual embeddings;
- sparse-autoencoder work finds structural features alongside content ones;
- and the **functional argument** is strong: if the closed class governs how everything else composes, a model
  optimized for prediction *must* encode it, because getting scope or tense wrong is expensive in loss.

**So the correct claim is not that the closed class is absent. It is that encoding is not composing.**

> A thermometer encodes temperature. It does not do thermodynamics.

A direction that *represents* negation is not a mechanism that *applies* negation correctly under scope, at
depth, through a chain. Three reasons the gap survives good directions:

1. **A direction has no intro/elim structure** (§4.2). It is an association, not a rule — so there is nothing
   to check for harmony, and nothing prevents the elimination outrunning the introduction, which is what a
   scope error *is*.
2. **Superposition means it is not a clean symbol.** Directions interfere and shift with context, so
   approximately-negation composed with approximately-quantification degrades multiplicatively.
3. **No inspection, no statement, no repair.** A direction cannot say what it commits to, and cannot be fixed.

This predicts the observed profile exactly: **LLMs recognise negation fine and fail at composing it** — nested
negation, negation interacting with quantifiers, negation surviving a long chain. Recognition without inference
discipline.

**⭐ And it gives the architecture a better justification than deficiency.** The engine is not supplying missing
concepts; the model probably has them. It supplies an **evaluation discipline** — exact composition, statable
commitments, and a harmony check that makes leaks impossible rather than unlikely. That argument does not
depend on LLMs being weak in a way they might stop being: scaling can improve the approximation, but **it
cannot turn an association into a rule with a matched elimination.**

**Two consequences that are good news for the boundary.** If the closed class is genuinely encoded, the
translator can be *asked* about closed-class structure and will often be right — *"is this a conditional?"*,
*"what is negated here?"* are closed-class judgements, and the evidence says the model can make them. It also
makes `cnl.md` §1's **refusal contract** meaningful rather than hopeful: a translator can be asked to refuse
when unsure precisely because it has a representation to be unsure about.

⚠ Caveats. A probe finding information shows it is *decodable*, not that the model *uses* it; causal
interventions are better evidence and are more mixed. And *why* LLMs do what they do is not settled — this
document claims the split, not a theory of them.

**A testable prediction, from §3.6's level 2.** If the closed class draws from a small, cross-linguistically
recurrent pool, then in a multilingual model **closed-class directions should align across languages more than
open-class ones do**. Either result is informative: if they do not, the bounded-shared-pool claim is in
trouble, and that claim is currently carrying the argument that the closed class is small enough to design.
**Unverified, and worth actually checking rather than filing as a lead** (§13).

### 3.6 Is the boundary arbitrary? — three levels, and the answer differs

The question is sharp because §3.2 says the split is real while §3.4 and §9 both allow membership to *change*.
Those are consistent, but only once three levels are separated. ⚠ An earlier draft ran two different mechanisms
together — **grammaticalization** (a historical process happening to a language) and **promotion** (a design
decision we make) — which made the position look incoherent.

| level | | arbitrary? |
|---|---|---|
| **1 · the architecture** — that there are two systems at all, one small/structural/exact and one large/associative/approximate | **No.** §3.2's diagnostics, and the aphasia double dissociation especially. A fact about minds, not a convention |
| **2 · the candidate pool** — what *can* be closed-class | **No, and this is the load-bearing level.** Grammaticalization is strongly **directional** (open → closed; the reverse is rare and contested), its **paths recur across unrelated languages** (motion verb → future marker; body part → spatial preposition; possession → perfect), and what gets grammaticalized clusters in a small semantic space: **time, space, causation, quantity, modality, evidence, discourse status**. Nobody anywhere grammaticalizes *cheese* |
| **3 · the selection** — which subset *this* system takes | **Chosen.** Language-particular, mutable, dated |

**Level 2 is what makes *"the closed class is small"* a substantive claim rather than a definition.** Languages
do not pick their closed class from the whole vocabulary; they pick from a small shared pool, and that pool is
roughly the list of things a reasoner needs. It is also what §3.5's cross-lingual prediction tests.

### ⭐ Chosen is not arbitrary

> **Arbitrary means the choice has no consequence.** Ours has a determinate, asymmetric one.

| error | consequence |
|---|---|
| **too closed** — the engine holds what the translator could have | the engine grows and gets brittle; you can only say what was designed. Expensive, **visible, recoverable** |
| **too open** — the translator holds what needed exact composition | **silent mis-mapping.** The system reports success and represents nothing — §12's measured LEAK, §8's *recognized-not-understood*. **Unrecoverable** |

Same asymmetry as `guards yes, kinds no`: conflation is the recoverable failure. So the operating rule is
**when in doubt, closed** — which is also `form_inventory` §9's *"minimality and composability are in tension,
and composability wins; the closure constraint can legitimately force the set larger."*

A choice with a cost function is a **design decision**, not an arbitrary one. Boiling point varies with
pressure without being arbitrary; a language's keyword list varies by language without being arbitrary — a
keyword is exactly a token the parser must know in order to parse anything else, which is criterion 1 below.

**The three criteria for level 3, which should agree** (disagreement is a signal to probe):

1. **Composition** — *does anything else's meaning depend on this?* **Operators must be closed; operands may be
   open.** Negation is closed because negation *over X* changes what X commits you to; *car* is open because
   nothing's meaning depends on what a car is.
2. **Learnability** (`form_inventory` §2(b)) — a baroque form is learnable because it desugars and can be
   checked against the core form; a fundamental one has no target to check against. **If it cannot be verified
   by desugaring, it must be closed.**
3. **Harmony** — a form is closed-class iff it *needs* an intro/elim pair, i.e. iff something follows from it
   that does not follow from its parts. Trivial elimination means open class.

**And revision is evidence-driven, not free.** A form is promoted when the residue log shows it carrying weight
the translator keeps dropping. `form_inventory` §7 measured the signal: a missing form does not lose content at
random, it loses the **marked** cases, which are disproportionately the exceptions. So the boundary moves **in
one direction, on evidence, with a record** — a specification under revision control, not a matter of taste.

---

## 4. Composition: harmony is the discipline

### 4.1 The catalog and the composition theory are different traditions

There is **no single source** that gives both. The catalogs (NSM, Searle, FrameNet, dialogue acts) and the
composition theories (Montague/type theory, DRT merge, proof-theoretic harmony) largely do not cite each other.
Composition is universal and engine-independent; the catalog is a specification (§3.2, caveat 2).

So: **borrow the discipline, decide the catalog.** Use the literature's catalogs as coverage checks, never as
authorities.

### 4.2 Harmony, and why it transplants

The criterion starts with **Prior's "tonk"**: a connective whose introduction and elimination rules do not fit,
letting you derive anything. **Belnap's answer** was the constraint, and Prawitz and Dummett built the semantics
on it.

> A form is well-defined iff its **introduction rule** (what licenses writing it) and its **elimination rule**
> (what may be inferred from it) *fit* — neither stronger than the other. Introduction without elimination is
> **inert**. Elimination outrunning introduction **leaks**.

Mapped onto this engine it stops being philosophy:

> **An introduction rule is a unit that writes the form. An elimination rule is a unit that reads it. A form
> ships with both, or it does not ship.**

**It retro-diagnoses the one measured leak.** `degree ∘ negation` failed because negation had a write path (the
fold) and hedge had a *different* write path (the interpretation layer), **and no shared read**. That is precisely
disharmony — two introductions, no matching elimination for the composite. `form_inventory` §9 called this
*"closure-at-depth ⟺ ONE uniform evaluation mechanism"*; harmony is the same claim with an older name and,
crucially, **a criterion applicable per form before building** rather than a probe run after.

**This is what makes a 50-form set tractable.** Checking 50 intro/elim pairs is linear. Probing 1,225 pairwise
compositions and unbounded nestings is not.

### 4.3 Harmony is not the last word — what came after

Prawitz/Dummett is not the end of the line. Ranked by relevance here:

| | why it matters |
|---|---|
| **① dynamic / update semantics** — Heim's File Change Semantics, Groenendijk & Stokhof's DPL, **Veltman's update semantics** | *Meaning is context-change potential*: a sentence's meaning is a **function from information state to information state**, not a truth condition. Veltman handles *might*, defaults, non-monotonicity natively. **This is the frame §5 adopts** — it is literally what an interpretation rule producing wiring does |
| **② inquisitive semantics** — Ciardelli, Groenendijk, Roelofsen | **One algebra covering assertions and questions.** Assertions provide information, questions raise issues, both fall out of one structure. Directly answers §2.3's question row *without* adding a kind — the right shape for the FORCE axis |
| **③ Brandom, inferentialism** | Meaning *is* inferential role; understanding is mastery of a claim's commitments and entitlements. His **deontic scorekeeping** — who is committed to what, who is entitled to what — reads as a specification for an agent's epistemic bookkeeping. The most developed post-Dummett answer to *"what does it mean to understand"* |
| **④ linear logic** (Girard) | Premises are **resources that get consumed** — the logic of state change, i.e. the tense/action block `form_inventory` §9.2 calls hardest. Relevant if actions come into scope |
| **⑤ Martin-Löf type theory / Curry–Howard** | Harmony mechanized: intro/elim rules *are* type formation, a proof *is* a program |
| **⑥ game semantics, Ludics** | Meaning as interaction pattern. Radical; apt for a dialogic agent |
| **⑦ DisCoCat** (Coecke, Sadrzadeh, Clark) | Composes **distributional** meanings with grammatical structure. The only serious attempt at a composition algebra whose atoms are *learned rather than designed* — i.e. this architecture's exact situation |

### 4.4 ⭐ SUPPOSE is the introduction rule for the conditional

`form_inventory` §4b lists nine forces — assert, deny, hedge, ask, goal, command, author, retract, norm. **There
is no SUPPOSE.** And the omission is not incidental: §4's orthogonality argument is *built on it* —

> *the lion generally has a mane* (hedged assertion) vs *does the lion generally have a mane?* (hedged question)
> vs ***assume** the lion generally has a mane* (hedged supposition)

Supposition establishes that the axes are orthogonal and then never enters the table. It is the one of your three
candidates with no home (§2.3), and the document half-knew it.

**Harmony says it is not a force at all:**

> **Supposition is the introduction rule for the conditional.** Assume P, derive Q, discharge to P → Q.

That is why it feels structural where ASK does not. And it is already built: `rev-02` §3 has a supposition open a
context, everything derived downstream carry it as **support**, and discharge be a read under a configuration.
**That is natural deduction's hypothesis-discharge, implemented as wiring.**

**Consequence for the inventory:** `when:` / `then:` and `suppose` are **one form seen from its two sides** —
elimination and introduction. They belong in one entry, not on different axes.

**And it is falsifiable.** If they are one form, the same units serve both. If the build needs two mechanisms,
the form was factored wrong.

### 4.5 Harmony is battle-tested — but not where you would look

*"Has anything that works been built on it?"* Yes, at very large scale, and none of it in linguistics. The
discipline migrated into computer science via **Curry–Howard**.

**Proof assistants.** In Martin-Löf type theory a type former is *given* by four things — formation,
**introduction**, **elimination**, computation. That is harmony not as a criterion but as the **construction
principle**: add a former whose elimination outruns its introduction and normalization breaks. That is tonk,
and the system rejects it. Built on it and working: **CompCert** (a C compiler with a machine-checked proof
that compilation preserves semantics) and the four-colour and Feit–Thompson theorems in Coq/Rocq; **seL4** (a
microkernel with full functional-correctness proof) in Isabelle/HOL; **mathlib** in Lean. Verified compilers,
verified kernels, formalized mathematics at the million-line scale.

**⭐ Logical frameworks — the closest structural match to what is being built here.** In **LF/Twelf**, and in
**Isabelle/Pure** as a generic framework, you *declare a logic by giving its inference rules as data* and the
framework supplies checking. That is "a catalog of forms plus a composition mechanism, where forms are data" —
existing and working. The mapping is close enough to be worth stating:

| logical framework | `units/` |
|---|---|
| an inference rule, declared | a `StandingUnit` |
| a form's intro/elim pair | two units |
| the framework's checker | the assembler + the engine |
| rules as declared data, not framework code | the wiring register (§11) |

⚠ The catch is the one §3 predicts: **it works for logics, whose forms are designed. Nobody has it for natural
language, whose forms must be discovered.** For harmony applied to natural language specifically the name is
**Francez** — fragments, not deployed.

**Bidirectional typing** is the everyday descendant, and it maps straight onto §5.2's entry format:
**introduction rules correspond to *checking*, elimination rules to *synthesis*** — which is exactly *which
unit writes it* / *which unit reads it*.

**The NL side is thinner and instructive.** CCG and its semantic pipelines (Boxer, the Groningen Meaning Bank),
Glue semantics in LFG, type-logical parsers, `ccg2lambda` and LangPro on FraCaS/SICK — these genuinely ran.
They did not reach open-domain robustness, and the reason is §3's: the composition machinery was fine, **the
lexicon was the wall.** That is the open class failing again, and that half is now covered by something that
did not exist when those systems were built.

**Two limits, both of which matter for how this document uses harmony:**

1. **It is a gate, not a generator.** It certifies that a form will not corrupt the others. It says nothing
   about *which* forms are needed or how to get them from text. §4.2 uses it correctly; it must not be
   mistaken for a source of the catalog.
2. **"Harmony" is not one crisp criterion.** There are competing formulations (Dummett's, Prawitz's, Read's
   general-elimination harmony), and the sore point is that **classical negation is not harmonious** —
   double-negation elimination outruns its introduction. This is a live dispute, not a settled definition.

**⭐ And limit 2 lands well here, which is worth recording as evidence rather than luck.** This design's
negation is already weak — `starved` ≠ underivable, absence is *"nothing matched above θ"*, and `review-01`
§3.2 grades that deliberate weakening one of the two genuinely novel commitments. **Constructive negation is
exactly the kind harmony can certify.** The epistemic position and the composition discipline want the same
logic.

---

## 5. The frame for an entry: what it does to the state

### 5.1 Meaning is state change

Adopted from §4.3 ①. Each form is specified by **what it does to the information state**, because that is what
this engine literally computes and because it makes the surface-independence requirement checkable:

> **Two surfaces express the same form iff they effect the same state change.** Not iff they transcribe to the
> same graph — they will not.

This resolves the requirement you opened with. `cnl.md` §5's transcription is **structure-preserving, not
normalizing**: *"a customer gets the discount when…"* and *"the discount is given to customers who…"* land as
different graphs, and nothing normalizes them.

**The normalization cannot live in the transcriber.** That would be Python — `model.md` §11's *"the front end
targets data, never an engine API,"* and therefore **unlearnable**. It lives in the **interpretation rules**,
which are data.

> Which turns the UX goal into an asset: **a new surface variant is a new rule, not a transcriber edit.** The
> system can learn a paraphrase.

### 5.2 The entry format

Every form in the inventory carries these fields. `introduction` / `elimination` are harmony made operational
(§4.2); `surface carrier` is §5.3 made systematic.

| field | meaning |
|---|---|
| **name** | |
| **axis** | content / force / level |
| **commits** | what believing it commits the system to |
| **introduction** | what licenses writing it — *which unit* |
| **elimination** | what may be read from it — *which unit* |
| **state change** | what it does to the information state |
| **surface carrier** | how it enters: **marked** at the boundary / **looked up** in the lexicon / **concluded** by a rule. If marked, whether the mark is refusable |
| **known compositions** | verified pairs; and known leaks |
| **status** | built / designed / gap |

An entry missing **introduction** or **elimination** is not an entry. That is the whole check.

**And `surface carrier` gives a completeness check on the role inventory:** every form whose carrier is
*marked* must have a role in tier 1 or 2 to carry it. A form needing a mark with no role to carry it means the
inventory (§9) is incomplete — mechanically checkable, rather than noticed later.

### 5.3 What the boundary marks, and what it must not

If a closed-class distinction is not marked at the boundary, can it be recovered afterwards? **For one kind,
no** — and that is the argument for marking. But the CNL cannot mark everything, because `model.md` §9 says the
boundary transcribes and never interprets, and `cnl.md` §5 says explicitly that nothing in transcription
decides force, reference, truth, applicability or scope.

**Half of this is already resolved in the shipped design.** `cnl.md` §5's list already marks a great deal of
closed-class structure: roles, number (`+`), degree (`~band`), coindexing (`x/`), nesting, delimitation. What
is *not* marked is the lexeme's own contribution — `park` enters as `name = "park"`, carrying none of its
skeleton.

**The principle, and `cnl.md` §6 is already the worked example:**

```
g0: [ get | agent: Paul | patient: the loyalty discount | modality: should ]
```

The translator marked `modality: should` — a closed-class **carrier**. It did not decide whether that is
deontic or epistemic, and did not decide the force; interpretation rules conclude *that it asks*.

> **Mark the carrier. Let a rule decide the reading.**

Nothing is lost and nothing is interpreted. `when:` marks a conditional carrier while whether the statement
*functions* as a rule stays a conclusion (`cnl.md` §4).

**Where English has no carrier** — bare generics, scope ambiguity — there is a third move that is neither
deciding nor dropping: **mark the ambiguity explicitly**. That is `form_inventory` §8's own requirement
(*unambiguous makes a two-reading parse not-yet-understood — hence ask, never pick*) and `cnl.md` §1's refusal
contract. Preserving *"this is one of these two"* keeps the information recoverable without the boundary
deciding anything.

**⭐ The asymmetry that answers the recoverability question**, and it follows directly from §3.4's
factorization — because the skeleton is lexeme-*invariant* while the rest is utterance-*specific*:

| | where it belongs | why |
|---|---|---|
| **utterance-specific** — force carrier, negation, scope, degree, coindexing, which role a filler fills, an unresolved ambiguity | **the boundary. Mark it** | it exists only in this utterance; drop it and it is gone |
| **lexeme-invariant** — aspect class, argument structure, intro/elim pair | **a lexicon, as KB data** | identical for every use of *park*. Recoverable by lookup, so per-utterance marking is redundant **and invites the translator to contradict itself between utterances** |

**The test:** *would two uses of this word ever differ in this respect?* No → lexicon. Yes → boundary.

The lexicon is authored in CNL as ordinary data, so nothing hides in Python — `cnl.md` §4's *"forms-as-data
stops being one feature and becomes the whole game."* It is FrameNet/VerbNet's content, held the way this
system holds everything else.

**⚠ Over-marking is not free, and naturalness is not the price.** `cnl.md` §5 already traded that away
(*"verbose and unpleasant to read, which is acceptable because a human is not the author"*). The real costs are
two: **auditability**, already flagged there with the mitigation (a prose renderer) undesigned; and — the
serious one — **every mark is a place the translator can be silently wrong.** More marks means more surface for
silent mis-mapping, which is §3.6's unrecoverable failure. Marking trades *unrecoverable loss* for *silent
mis-marking*.

> **So: mark only what is genuinely unrecoverable, and make every mark refusable.** A translator that can
> answer *ambiguous* or *cannot-express* on a mark converts a silent mis-map into a reportable one, which is
> the whole point of the four-outcome contract (§9).

---

## 6. The catalog — what to borrow, per axis

⚠ Read §13 before using any of this. These are **leads**, not verified citations.

| axis | borrow from | note |
|---|---|---|
| **FORCE** | **inquisitive semantics** first; **Searle & Vanderveken's F(p)** second; **dialogue-act taxonomies** (DIT++, ISO SemAF) for engineering coverage | Inquisitive semantics is preferred because it gives an *algebra* unifying assertion and question, which is what is needed; Searle's five types are *descriptive*. F(p) — a force applied to propositional content — is `form_inventory` §4's two axes, independently arrived at, and its decomposition of a force into direction-of-fit / sincerity / preparatory conditions is a principled membership test |
| **CONTENT** | **NSM** as a *bound* on minimality, not as a method | It is a definitional reduction, not an inference algebra. Useful for "how small could this get"; it does not tell you the set composes |
| **ROLES** (tier 3) | **AMR**, **FrameNet**, **PropBank**, **VerbNet** | The one to actually raid. AMR is a *graph* meaning representation with a settled role inventory built by people who had to make it work at scale. Do not invent thematic roles from scratch |
| **ASPECT** | **Vendler's four classes**; Levin & Rappaport Hovav's event templates | If bounded tense returns |
| **REFERENCE** | **DRT** (Kamp), and SDRT for discourse relations | Representations that compose by merge, designed around anaphora — the hole in §10.3 |
| **COMPOSITION** | **harmony** (§4.2); update semantics (§5) | The universal half |

**Not** upper ontologies (DOLCE, BFO, SUMO). Those catalog *what exists*, not *what is committed to*.

---

## 7. Definitions as equivalences

Your proposal: *"park the car near the movie theater"* → *"change the position of the car so that its new
position is close to the movie theater."*

### 7.1 It has a name, and the example is nearly verbatim

CAUSE(x, GO(car, TO(PLACE(near, theater)))) is almost literally **Jackendoff's Conceptual Semantics** (primitives
GO, BE, STAY, CAUSE, PATH, PLACE), and in AI it is **Schank's Conceptual Dependency** — ~11–14 primitive acts
(PTRANS, ATRANS, MTRANS, PROPEL, INGEST), where parking a car is a PTRANS.

The programme is **decompositional lexical semantics**; its high-water mark was **Generative Semantics** (Lakoff,
McCawley, Ross, Postal), whose canonical case is *kill* = CAUSE(x, BECOME(NOT(ALIVE(y)))).

### 7.2 ⚠ Fodor's objection is `form_inventory` §1's own test, in the wild

> *"John caused Bill to die on Sunday by stabbing him on Saturday"* is fine.
> *"John killed Bill on Sunday by stabbing him on Saturday"* is not.

So *kill* ≠ *cause to die*: **the decomposition licenses inferences the original does not.** That is exactly
*paraphrasable without changing what the system believes?* — answered **no**, so the decomposition was a lie.

In this document's terms it is a **disharmony**: the elimination rule for the definiens outruns the introduction
rule for the definiendum. **Harmony is therefore the check on every proposed equivalence**, which turns "is this
definition safe?" from a judgement call into a criterion.

### 7.3 The other wall: the frame problem

*"Change the position of the car"* — what else changed? Fuel, the driver's location, the parking space's
occupancy, and **nothing else in the universe**. Enumerating what does *not* change is the **frame problem**
(McCarthy & Hayes), and it is why STRIPS simply assumes it away. Any change-of-state form walks into this; name
it before designing one.

### 7.4 The rule that falls out

> **A definition is a rule, never a transcription.**

If the boundary expands *park* into CAUSE/GO/PLACE, the boundary is doing semantics and `model.md` §9 forbids it.
If a **rule** does it, it is an ordinary rule — inspectable, replaceable, learnable. Equivalences are welcome on
exactly that condition, and each ships an intro/elim pair that must match (§5).

---

## 8. Understanding, defined

Carried from `form_inventory` §8, unchanged — it is epistemological and survives the inversion:

> **X is understood iff its CONTENT maps onto held forms, unambiguously and status-preservingly, AND its FORCE is
> recognised** — what the utterance is *doing*, not merely what it is about.

Both qualifiers are load-bearing: **unambiguous** makes a two-reading parse *not-yet-understood* (hence ask, never
pick); **status-preserving** makes a distorting paraphrase a failure to understand rather than a lossy success.

The distinctions it buys:

- **Understanding ≠ parsing.** A sentence can parse, route as a fact, and commit nothing.
- **Understanding ≠ truth.** Understanding *some naturalists consider the lion a cat* does not require lions to
  be cats.
- **Misunderstanding is a MIS-MAPPING, not an absence** — *resembles a cat in his mode of stealing* → *is a cat*
  maps identity where the source said resemblance. A diagnosis, not a "wrong".
- **Force alone can sink it.** Map *is the lion dangerous?* to the proposition perfectly, then assert it: every
  content check passes and the utterance has been comprehensively misunderstood.

⚠ Two limits, restated: it is **indexed to a repertoire** (understanding is relative to the form set held), and
it is **propositional, not grounded** — which §3.4 reframes from limitation to architecture.

---

## 9. The inventory is tiered

`cnl.md` §2 ships ten role names as one flat class: `agent: patient: destination: time: means: of: member:
when: then: content:`. That conflates four tiers with different consumers and different stability requirements —
`cnl.md` §7's second open item, unresolved.

| tier | roles | consumer | may grow? | when to design |
|---|---|---|---|---|
| **0 · wiring** | `pattern:` `gate:` `out:` `from:` `to:` | the **assembler** | no | **first** — the bootstrap depends on it (§11) |
| **1 · structural** | `content:` `member:` `of:` | interpretation rules | no | second |
| **2 · logical** | `when:` `then:` | interpretation rules | no | second |
| **3 · thematic** | `agent:` `patient:` `destination:` `time:` `means:` | domain rules | **the only tier that could be** | last; raid AMR/FrameNet (§6) |

**Why the split is not cosmetic.** Tiers 1–2 are what interpretation rules read in order to *produce* wiring;
tier 3 is what domain rules match on. Tier 0 is read by the assembler and by nothing else.

⚠ **Containment direction is decided and load-bearing:** container → contained, because a pattern atom has `out`
and no backward traversal, so *"find something containing both of these"* is only expressible if the container is
the source (`units/graph.py::contains`).

### The methodological split — resolving a real tension

`form_inventory` §5 says entries are **corpus-derived, never designed a priori**. Your proposal is design-first.
Both are right, for different tiers:

| | method |
|---|---|
| **tier 0** | **designed a priori.** There is no corpus of wirings, and the bundled interpretation rules must ship written in this register before anything can be observed |
| **tiers 1–2** | designed, validated against what interpretation rules actually need |
| **tier 3** | **corpus-derived**, keeping the residue log and the four-outcome translation contract |

⚠ **Attenuation must never be silent**, and the reason is not bookkeeping: dropping *the guzerat lion has no
mane* is safe for deduction but poisons induction — **to a learner, absence looks like confirmation**. The residue
is evidence the learner needs, not a to-do list.

---

## 10. Gaps found

### 10.1 SUPPOSE — resolved, §4.4

Absent from the force axis; resolved as the conditional's introduction rule. Not a gap any more, but it was one.

### 10.2 Activity structure — open

The three axes classify an **utterance**. They say nothing about multi-turn shapes: a plan under execution, a
hypothesis under test, a goal pursued across turns. `model.md` §8 asserts plan/step/subgoal/expectation are one
shape; there is no entry for it. **"Hypothesis formulation and verification" is half-answered** — formulation is
§4.4; verification is here, and unaddressed.

### 10.3 Reference and identity — open, and it has a measured obstacle

Absent from `form_inventory` §4a entirely, though identity is plainly a fundamental commitment. `rev-02` §4
covers denotation, and a session probe found its flagship example unreachable on the current engine:

> **Measured 2026-07-27.** `rev-02` §4 says a denotational expression is inert and resolved by ordinary rules
> with *"no chain the engine sees."* If nothing is assembled per description, depth comes from **iterating one
> unit** (`model.md` §5). That is a cycle, and `rev-01` §4 burns cycles at `SURGE_AT = 3`. Wiring exactly that —
> one narrowing unit, self-looped, over an inert nested description — **depth 4 produces a complete and correct
> resolution and is still reported as a runaway loop; depth ≥ 5 is also silently partial** (resolution caps at 5
> nodes). *"The red car parked at the third floor of the garage near the movie"* is four narrowing steps.

The general result is worse than a bad constant: **the surge detector cannot distinguish converging recursion
over a finite description from a runaway cycle.** Raising `SURGE_AT` moves the depth at which comprehension
breaks; it does not fix it. `review-01` §3.1 calls the detector *"a witness, not a decision procedure"* and sound
in one direction only — this is the other direction, costing a real answer.

**⭐ 2026-07-29, `cnl_engine_goal_plan.md` Phase D — the "cannot distinguish" half confirmed, not fixed; the
"silently partial" half fixed.** Verified against the running code, not just against this write-up: traced a
powered `ping_pong` cycle and every genuine self-loop this engine can express mints a **fresh node on every
pass** (`Emit`'s effect payload always names a brand-new `Mint`), so no two passes' values are ever equal, a
subset of each other, or a superset of each other. That is not a gap in the detector's cleverness — it is a
structural fact about what a value on a wire *can be* here, and it means **no local, content-blind check can
ever tell a converging four-step narrowing from a non-converging one**; `_grew`'s monotonicity theorem (growth
only) already covers the one shape that *is* decidable, and there is no dual "shrank monotonically" shape to
extend it with, because shrinking would require reusing a node across passes, which nothing does. The plan's
prior framing — implying a smarter detector was the target — was the wrong frame; there isn't one to build.

What *was* fixable, and is now fixed (`units/engine.py`, `Network._unit_burned` + `_live()`): the two symptoms
named above are not one bug, they're two. Reporting a correct depth-4 answer as a runaway loop is a **false
positive** — wasteful but honest, since the answer is discarded rather than trusted. Silently returning a
truncated depth-5 answer as if it were complete is a **false negative**, and that is the dangerous one — it is
the exact failure `forms_llm.md` §7 names as the whole justification for building this instead of trusting an
LLM's forward pass, reproduced inside the thing meant to prevent it. The fix does not try to detect which case
it is (impossible, per the above); it removes the silence instead. A burned unit's `cell.held` is now excluded
from every read (`_live()`), on the same footing as the *"0 matches ≠ reference failure"* argument two
paragraphs up: a burned unit reads as **absent**, not as whatever partial value it happened to be holding when
its gate stopped delivering, while `SURGED` remains on its node (`_drain`) for whatever downstream rule or
caller wants to ask why. Paired with widening `SURGE_AT` (3 → 6, `units/engine.py`) so the common, shallow case
(the four-step example above) doesn't trip it at all — cheap, since a genuine cycle is still caught a few
passes later at negligible fuel cost, per the same fresh-mint argument. Neither change is a termination proof;
together they mean the engine never again reports a wrong answer as if it were a right one, which is what
ingredient 3 of `cnl_engine_goal.md` §3 actually asked for. Test: `test_a_burned_units_stale_value_does_not_
leak_into_a_read` (`tests/units/test_engine.py`).

Two further arguments against `rev-02` §4's cardinality table, unmeasured:

- **0 matches ≠ reference failure.** `model.md` §7–8's commitment is that *nothing matched* never means *not
  derivable*. The honest outcome at zero is `starved`, and §8's table already writes it for a descendant goal:
  *"I understood you; nothing came to mind."*
- **n matches ≠ ambiguity.** Under *create, never merge*, match rows count **nodes**; reference cardinality counts
  **things**. They diverge exactly while coreference is unresolved — which is always, at the moment of resolving,
  since the *product* of resolution is the identification. The available construct is counting **equivalence
  classes under the union-find** (`overlay.resolve()`), not match rows.

### 10.4 The wiring register — the one that blocks everything

`cnl.md` §7's first open item. Also a live engine defect, and the two are the same hole seen from two sides.

---

## 11. What must be built first — tier 0

**The assembler has nothing to read and nowhere to write.** Wiring today is a Python list of Python objects:

```python
# units/engine.py:287
self.wires: list = []              # (Cell, StandingUnit, gate)   ← plane 2, Python
```

Nothing in `units/` ever reads wiring from the graph. Every test wires by calling `Network.wire(...)` — so **the
front end's target is currently an engine API**, the one thing `model.md` §11 forbids.

| | status |
|---|---|
| **invariant 18** — *plane 2 holds nothing across a revive that plane 1 does not describe* | **violated outright.** `self.wires` survives every `revive()`; plane 1 describes none of it |
| **invariant 15's `[R2]` gloss** — *"now literally true: wiring is plane-1 data, not Python objects that happen to survive"* | **false about the build.** The invariant itself holds; the justification does not. `review-01` §4 already flagged invariant 15 as the nearest thing to a semantics |
| **`rev-02` §5** — *a wire is a 3-place relation; it cannot be an edge at all* | **designed, unbuilt.** No such node exists |

And the bootstrap depends on it: `cnl.md` §4 says the bundled interpretation rules **ship pre-written in the
wiring register**, which cannot happen until that register has a form. Today the bundle is
`bundled_silence_rule()` — a Python function constructing a `StandingUnit`.

**The build, and it self-tests:** wires become occurrence nodes; `Network` *derives* its topology from
`self.asserted` instead of owning it; `wire()` stops being an API and becomes a fact. Writing the bundled
interpretation rules *in* that register is what proves the vocabulary sufficient.

⚠ One thing to re-test on the way: `form_inventory` §4d put L0 in a **register, never as graph facts**, because
as facts it **leaked** (`?y is meta when ?y is a relation` derived `produces is meta`). That decision is now
reversed by homoiconicity (§10 below), so the leak needs the new answer — invariant 19, *a pattern that does not
name machinery never matches machinery*, for the ordinary reason that nothing matches implicitly. **Untested
against this specific leak.**

---

## 12. What carries over from `form_inventory.md`, and what does not

### Survives

| | |
|---|---|
| **§1's test** — *paraphrasable without changing what the system believes?* | the definition of baroque vs fundamental, and now also the check on equivalences (§7.2) |
| **§4's three axes and the orthogonality argument** | §2.2 — the answer to "what are the categories" |
| **§3's probe discipline** — never assign by intuition | five for five wrong; §3.2 caveat 1 |
| **§5's residue log** and the four-outcome contract | tier 3 only (§9) |
| **§6's evidentiality caution** — the inventory is a specification, not a survey | §3.2 caveat 2 |
| **§7** — the repertoire bounds reasoning, and the bound **skews** toward dropping marked (exceptional) content | still true, still the argument for the residue log |
| **§8's definition of understanding** | §8, unchanged |
| **§9's closure requirement** and *closure-at-depth ⟺ one uniform evaluation mechanism* | §4.2 — harmony is the per-form form of it |

### Dead

| | why |
|---|---|
| every **mechanism** column — ink/pencil, forks, `has_not`, `check`, `chain_sip`, `load_machine_rules`, intake routes, banks | superseded engine |
| **§4d: "L0 lives in a REGISTER, never as graph facts"**, and its schema/structure/vocabulary tier table | **reversed.** `rev-02` §5 makes wires and units plane-1 data with no privileged partitions; the composability principle says a mechanism hardcoded in Python is an unreachable island. The register *was* that island. ⚠ The leak it was protecting against is real — see §11 |
| **§4b: force is a VERB** | **reversed** by `cnl.md` §2 — *there is no force syntax*; a rule concludes it asks |
| **§9.3: scope generalization** as the one missing primitive | dissolved by `rev-02` §3 — scope is **support**, not containment, so there is no scope object to relativize |
| **§9.1–9.2's binder analysis** | measured against the retired engine; the *questions* may survive, the verdicts do not |

---

## 13. ⚠ Citations are LEADS, not verified

`form_inventory` §6 carries this warning and it applies with equal force here: everything in §§3–7 is LLM recall,
none of it checked against a source. The failure mode is specific — plausible author, plausible title, plausible
year, claim subtly or entirely wrong. **Treat every name and date below as a search query.**

**Substance I would stake:** the closed/open split and its scorecard; Quine's holism and its role in ending the
reduction programme; Fodor's kill/cause-to-die objection and the atomism thesis; Jackendoff's and Schank's
primitive inventories; harmony as intro/elim fit, and tonk as its origin; Montague/type-theoretic composition;
DRT as Kamp's and about anaphora; update semantics as meaning-is-context-change; inquisitive semantics unifying
assertion and question; Searle's five types and F(p); the frame problem as McCarthy & Hayes; FrameNet as
Fillmore's; Vendler's four aspectual classes; features-as-superposed-directions.

**Would not stake without checking:** exact titles and years throughout, and specifically — (a) **Searle &
Vanderveken's illocutionary algebra**, load-bearing for §6's force row; (b) the **generative semantics** timeline
and which objection landed when; (c) **Veltman**, **Heim**, **DPL** dates; (d) the **inquisitive semantics**
publication history.

**Verify before any of this is cited outward.** Nothing here depends on a date being right, which is why drafting
went first — but §6's recommendation to prefer inquisitive semantics over Searle for the force axis is the one
place where a wrong reading of the literature would change a design decision.

---

## 14. Open

- **Activity structure** (§10.2) — the multi-turn shapes have no entry, and "hypothesis verification" lives here.
- **Reference and identity** (§10.3) — no entry, plus a measured engine obstacle that blocks the flagship case.
- **Tier 3's contents** — deliberately deferred to the residue log, but nothing has been logged against the new
  model yet.
- **Does the L0 leak recur under homoiconicity?** (§11) — invariant 19 is the claimed answer; untested.
- **How many forms is it, actually?** The claim that the closed class is small is inherited, not measured here.
  The first honest count comes out of tier 0 + tiers 1–2 once written.
- **Is the entry format sufficient?** §5.2's nine fields are designed, not validated. The test is writing ten
  real entries and seeing which field is always empty or always fudged.

---

## 15. Glossary, for readers who know software engineering and not linguistics

Each term gets the definition and, where one exists, the compiler/type-system analogy. Analogies are
**illustrative, not exact** — they are here to get you to the right intuition quickly, not to be defended.

### 15.1 The three axes (§2.2)

| term | meaning | SE analogy |
|---|---|---|
| **CONTENT** | *what is claimed* — the proposition itself | the **payload** of a message |
| **FORCE** (*illocutionary force*) | *what is being done with the claim* — asserting it, asking it, commanding it, retracting it. Asking is **not** a weaker asserting: it commits to nothing and changes no beliefs | the **verb**, in CQRS terms. `GET /discount` and `POST /discount` carry the same resource and do completely different things. Same content, different force |
| **LEVEL** | *what the claim is about* — the world, the theory, or the language itself | runtime data vs. your program vs. the **language spec**. *"produces is a relation"* is a claim at the third level |
| **orthogonal** | any value on one axis combines with any value on the others | three independent enum parameters, not one big enum of their product |

### 15.2 The two classes (§3)

| term | meaning | SE analogy |
|---|---|---|
| **closed class** | the small, fixed set of structural items: determiners, prepositions, conjunctions, tense/aspect markers, negation, quantifiers. You cannot coin new ones on demand | a language's **keywords and operators**. `if`, `&&`, `return`. Small, fixed, and the parser must know all of them |
| **open class** | nouns, verbs, adjectives — tens of thousands, unbounded, new ones daily | **identifiers**. The parser needs to know *that* something is an identifier, never *which* |
| **lexeme** | a word considered as a dictionary entry (*run*, *ran*, *running* are one lexeme) | a symbol, as opposed to its occurrences |
| **grammaticalization** | the historical process by which open-class items become closed-class — *will* was a verb meaning "want"; *going to* became a future marker | a widely-used library function being absorbed into the language as a keyword across versions |
| **holism** (*confirmation holism*, Quine) | meanings do not factor into independent atoms; the unit of meaning is the whole theory | a symbol's meaning in a large codebase is fixed by **all its call sites**, not by a local declaration |
| **distributional semantics** | meaning derived from co-occurrence patterns — *"you shall know a word by the company it keeps"* | embeddings. This is what they implement |

### 15.3 Composition and proof theory (§4)

| term | meaning | SE analogy |
|---|---|---|
| **introduction rule** | what licenses *asserting* a form — how you build one | a **constructor** |
| **elimination rule** | what may be *inferred from* a form — how you consume one | an **accessor / pattern match / destructor** |
| **harmony** | intro and elim must fit: neither stronger than the other. Intro without elim is **inert**; elim outrunning intro **leaks** | your serializer and deserializer must round-trip. A destructor that hands back more than the constructor put in is a soundness bug |
| **tonk** | Prior's joke connective whose intro and elim do not fit, letting you derive anything. The origin of the harmony criterion | an unchecked cast that lets you produce a value of any type. One of these and your type system proves nothing |
| **Curry–Howard** | propositions are types; proofs are programs. The bridge by which proof theory became type theory | why Coq and Agda are simultaneously proof assistants and programming languages |
| **natural deduction** | a proof system built from intro/elim rules per connective, rather than from axioms | |
| **hypothesis discharge** | assume P, derive Q, then *discharge* the assumption to conclude P → Q. §4.4: this is what `suppose` is | entering a scope with an extra binding, then closing the scope and returning a function of it |
| **normalization / consistency** | that proofs reduce to canonical form / that not everything is derivable. What harmony protects | type soundness. Break it and every program typechecks, which means typechecking tells you nothing |
| **bidirectional typing** | intro rules correspond to *checking*, elim rules to *synthesis* | how essentially every modern typechecker is structured |
| **constructive / intuitionistic negation** | *"not P"* means *"P leads to absurdity"*, not *"P is false in the world"*. Weaker than classical negation, and the kind harmony certifies (§4.5) | `Option`/`Result` rather than null-and-hope. This design's `starved` ≠ underivable is in this family |

### 15.4 Linguistic terms used in the argument

| term | meaning | SE analogy |
|---|---|---|
| **thematic role** | the part a participant plays: agent, patient, destination, instrument | **named parameters**, as opposed to positional ones |
| **argument structure** | which roles a verb requires and permits | a **function signature** |
| **aspect / aspectual class** (Vendler) | whether an event is a state, an activity, an accomplishment (has a natural completion) or an achievement (instantaneous) | fire-and-forget vs. long-running-with-progress vs. has-a-terminal-state |
| **tense** | location in time, as opposed to internal shape (that is aspect) | timestamps, as opposed to job semantics |
| **modality** | possibility, necessity, obligation — *must*, *may*, *should*. **Deontic** = about obligation; **epistemic** = about knowledge. *"You must be tired"* is epistemic; *"you must leave"* is deontic | |
| **genericity / generic** | *"the lion is dangerous"* — a claim about the kind, not about a lion | class vs. instance. English marks this badly, which is why §5.3 wants it carried |
| **definite description** | *"the red car parked at the third floor"* — a phrase that picks out a thing by describing it | a query that should return exactly one row. Zero rows and *n* rows are both errors |
| **referential vs attributive** (Donnellan) | referential = it names *that* thing and keeps naming it; attributive = it names whoever currently fits the description | a captured value vs. a live query. `rev-02` §4 derives this from evaluation discipline |
| **anaphora / coreference** | a later expression referring back to an earlier one (*"he"*, *"that car"*) | a pointer to an earlier binding — and the resolution problem is aliasing |
| **evidentiality** | grammatically marking your information source — direct, hearsay, inference. Obligatory in some languages, absent in English | a required provenance field on every record |
| **speech act** | an utterance considered as an action performed. Searle's five types are the standard taxonomy | |
| **monotonicity** | adding information never removes a conclusion | append-only. Non-monotonic reasoning is the mutable case, and it is why §4.5's negation caveat matters |
| **scope** | which operator governs which material — *"not everyone came"* vs. *"everyone didn't come"* | operator precedence and binding, and the ambiguity is exactly the same problem |
| **figure / ground** | in a spatial relation, the located thing and the reference thing. *"the car near the theater"*: car = figure, theater = ground | |

### 15.5 Repo-internal terms that are **not** standard usage

⚠ These mean something specific here and will mislead if read as the field's terminology.

| term | meaning here |
|---|---|
| **baroque / fundamental** | this project's split: baroque = paraphrasable without changing what the system believes; fundamental = not. §1's test in `form_inventory` |
| **occurrence** | a node standing for an event or relation instance, with role nodes hanging off it. `model.md` §3 |
| **unit / gate / wire** | a standing computation node, its inputs, and the topology connecting them. `model.md` §5 |
| **plane 1 / plane 2** | inert data vs. the running circuit. `rev-02` §1 |
| **band / θ** | a discrete degree of match strength, and the threshold below which a match does not count. `model.md` §4 |
| **starved** | *nothing came to mind*, which is emphatically **not** *underivable*. `model.md` §8 |
| **residue log** | the record of what a translation had to drop. `form_inventory` §5 |
| **carrier** | the surface item that marks a closed-class distinction without deciding its reading. §5.3 |

### 15.6 Entry points for further reading

`form_inventory` §6 and §13 above carry the full lists with confidence markings. If you are starting cold,
these four are the ones that pay back fastest, in order:

1. **A proof-assistant tutorial** (Lean's *Natural Number Game*, or Software Foundations for Coq) — the fastest
   way to *feel* intro/elim discipline rather than read about it. Two hours gets you the whole intuition
   behind §4.
2. **Radul & Sussman, *The Art of the Propagator*** — not about forms at all, but the closest existing system
   to this engine (`review-01` §2.1), and short.
3. **Any introduction to dynamic/update semantics** — for §5.1's *meaning is state change*, which is the frame
   the whole inventory is organised on.
4. **Searle on speech acts** — for the FORCE axis, read for the taxonomy rather than the algebra (§6 prefers
   inquisitive semantics for the latter).

# Expressiveness and uniformity — can we SAY it, and can two representations RELATE?

**Status: findings and probes, nothing built.** This document exists because three requirements on
[language-semantics-reasoning.md](language-semantics-reasoning.md)'s frame turned out to be entangled,
and the shortest way to see how is to try to write one sentence.

The three, stated first:

1. ⭐⭐⭐ **The syntax and the substrate must be expressive enough to carry the semantics.** A category
   the matrix claims is covered but that nothing can *say* is not covered. The test is not *is there a
   mechanism* — it is **write the sentence**.
2. ⭐⭐⭐ **The representations must be uniform, in the sense that they can RELATE to each other.** A
   cause–effect relation containing a before-after cannot represent before-after inconsistently with the
   representation of **time**, or the two can never be reasoned about together. ⚠ This is **prior to**
   the composition claim rather than part of it: the frame says the *operations* compose; this says the
   **representations** must, and operations only compose over representations that already do.

   ⭐⭐⭐ **And this is the project's one stated nice-to-have, not internal hygiene.** The scope is a
   **narrow domain with rules and experience authored into KBs**, and the thing wanted on top is
   **composing knowledge from different domains**. Two independently authored KBs will use different
   names for one relation and one name for different relations — so *representations that cannot relate*
   is precisely the failure mode of the feature. ⭐⭐ It also gives the horizon a sharper admissibility
   test than *every decision can be an argument*: **something is closed class iff two independently
   authored domains must agree on it to compose.** Order passes (two domains that speak of sequences must
   share it); `friend_of` does not (only one domain cares).
3. ⭐⭐ **The set of real operations should stay finite as coverage grows**, which is what
   *operations as data* buys — and it is the strongest justification the reflection arc has.

⭐⭐⭐ **They are one requirement seen three ways**, and §§2–3 show it: you cannot add expressiveness
without answering uniformity, and reifying the operations **inherits** uniformity rather than escaping
it.

## 1. ⚠ The wrong analogue: Turing completeness

The natural question — *is there a Turing completeness for representations?* — has an instructive
negative answer. Turing completeness asks which **functions** you can compute. This substrate has it
already; it has an instruction set. It was never the question, and it is the wrong target for a deeper
reason: Turing completeness is exactly the property **"you can encode anything"**, and encoding is what
must not happen. Encode *taking turns* as a bespoke predicate with a private index scheme and you have
maximal power and zero relatability — an island, reached by being *too* expressive.

⭐ **So the criterion is never *can it express X*. It is *can it express X without encoding* —**
directly, in structure other things already reach. Every section below is a consequence of that.

### ⚠⚠⚠ Borrow the formal tradition's FACTS, never its CRITERIA

The neighbours worth knowing — **definability** and Ehrenfeucht–Fraïssé games (first-order logic cannot
express transitive closure, which is why `path.reaches` is a primitive here and not a definition);
**descriptive complexity** (Immerman–Vardi's FO+LFP = PTIME **on ordered structures** — the order caveat
is §3's problem arriving as a theorem); the **knowledge compilation map** (Darwiche & Marquis), whose
*shape* is this project's matrix — languages × operations, and no language wins; the description-logic
tradition, which enumerated constructors against reasoning services; **institutions** (Goguen & Burstall)
for translation; **Brachman & Levesque** for what path composition costs.

⚠⚠⚠ **Every one of those aimed at guarantees — decidability, completeness, tractable subsumption. This
project does not, and never did.** That is not a criticism of them; they answered a question well and it
is a different question. ⭐ **Nothing here is rejected for failing to offer proofs** — the lineage this
project actually belongs to offers none: Soar's impasses, PRS's meta-KAs, Maes' computational reflection,
Smith's 3-Lisp, Bowen & Kowalski's amalgamation, Hobbs' interpretation as abduction. See
[reflection.md](reflection.md), where those are already the named lineage. **Bounded and defeasible is
the design, not a shortfall.**

⭐⭐⭐ **So take the facts and refuse the criteria, because importing a criterion with a fact has already
cost this document once.** The discrimination test in §7 was first written as *can the representation
distinguish these two structures* — an Ehrenfeucht–Fraïssé question — when the question that matters here
is **would the agent act differently**. The formal results are useful the way a chart of rocks is useful:
they say where the hull breaks. They do not say where to sail, and they were never asked to.

⭐ **And the agent tradition's own answer to "is my representation good enough" is task competence plus
graceful degradation** — does it handle the case, and when it fails does it fail *visibly and
recoverably*? Already this project's stated position: *silent failure is acceptable; unrecorded failure
is not*; *blocked-on-ignorance is a third search outcome*; *"UNKNOWN — I did not finish looking within
fuel" is an honest first-class answer.*

### ⭐⭐⭐ The benchmark is an LLM doing agentic work, on two axes

Which is what finally makes *expressive enough* answerable, because it names the thing to be better than.
**The goal is improvement over an LLM as an agent in INSPECTABILITY and COMPUTATIONAL COST — not
guarantees, which were never the goal.**

* **Inspectability** — an LLM's account of its reasoning is a token stream produced *alongside* the
  computation, not the computation itself, so it cannot be addressed, queried or held to. This engine's
  residue **is** the computation, as nodes. That is [comparison.md](comparison.md)'s thesis, and its
  comparison class is an LLM rather than a prover.
* **Computational cost** — an LLM re-derives everything on every call and keeps nothing. Here a plan
  found once is a node, a construction learned once is data, an order declared once is read by everything.
  **Reasoning that has been done stays done.**

⚠⚠ **The consequence for everything below is a re-ranking, and it is uncomfortable in one place.** An LLM
already knows friendship is symmetric, for free, from pretraining — so §4 buys little *capability* and
buys auditability and cost. What an LLM cannot do at all is hold a persistent, addressable, cheaply
re-read structure. ⭐ **So the machinery that beats the benchmark is the machinery about STRUCTURE AND
REUSE, not the machinery about knowing things** — and where the need really is world knowledge, *an LLM
is a boundary tool* remains the right answer rather than an admission.

## 2. Try to write it: *"let's plant this nail by taking turns hammering"*

### What is already there, and it is most of it

* **The substrate has ordered targets** — `(src, label) -> [dst, …]`, ordered, journaled. Order is a
  substrate primitive here, not something a module invents.
* **The trajectory is recorded.** A workbench keeps the whole movie — frames in order, each with a `via`
  transformation naming the function applied and the bindings it took. A predicate over a trajectory has
  something to read **today**.
* **The type language already expresses the right SHAPE**: `wheel[0].rim is not wheel[1].rim` — two
  positions in an ordered sequence not being the same node. That *is* alternation.

### The one thing missing, and it is small and precise

`path.Hop.index` is `int | None`. **A literal.**

```cnl
type taking_turns:
    step[0].agent is not step[1].agent      # ✅ sayable
    step[i].agent is not step[i+1].agent    # ❌ not sayable — there is no `i`
```

⭐ **You can describe taking turns for a sequence of known length and for no other**, which is not
describing it. The gap is not a mechanism and not a CNL family: it is a **variable, relative position**
in the reference language.

⚠⚠⚠ **This was first written as "one addition to `path.py`'s hop", and that is wrong** — see
[defining-terms.md](defining-terms.md) §1–2. A hop needs an **index and an order**, because `Hop.index`
indexes the substrate's *insertion* order, which is a storage artefact: **a sixth unrelated order, and
the only one with no name.** And `i+1` presupposes a **discrete, total** order with a successor, while
`clock.py`'s moments are explicitly **partial** — so indexing is always over a *linearisation*, and an
unstated one is the `visible` bug rebuilt with better syntax. ⭐ The consequence for the plan: **the
shared core (§5) comes BEFORE the index**, because the index cannot be specified without naming an order.

⚠ Do not reach for a new CNL family. The standing budget applies — *a new way of saying something is an
interpretation rule in the web, never a new verb in `intake.py`* — and this is not a new way of saying
an existing thing. It is the reference language failing to reach a position it reaches happily when the
position is written as a number.

## 3. The uniformity defect, which arrives the moment you write `[i+1]`

**`+1` names a successor, and the substrate makes you say WHICH one.** So expressiveness cannot be added
without answering uniformity first. What the engine currently means by *comes after*:

| where | label | what it orders | kind |
|---|---|---|---|
| `clock.py` | `before` | moments; a partial order read with `path.reaches` | **temporal** |
| `goal.py` (`sequence`) | `then` | the step order a goal *requires* | **prescriptive** |
| `search.py` | `after` | the step order a plan *has* | **descriptive** |
| `execution.py`, `rules/step.mf` | `next` | frames, and mappings | **derivational** |
| `construction.py` | `next` | tokens in an utterance | **form** |
| `method.py` | *(no edge)* | steps — *"declaration order is the `then` order, free"* | **prescriptive, positional** |
| `locate.py` | `before`/`after`/`equal` | the answers a question comes back with | a **rendering** |

⚠⚠⚠ **Four names and one no-name for one relation, in a system where a name is where meaning lives.** A
rule that knows `before` cannot see a plan's `after`. Nothing joins any pair. *"They took turns before
lunch"* has no reading, because the order in *took turns* and the order in *before lunch* are unrelated
structures that share an English word.

⭐ **The engine noticed half of this and stopped.** `clock.py`: *"that makes this the third ranking in
the engine read by the same traversal, alongside authority for discourse and norms, and containment for
reach."* Three rankings sharing `path.reaches` is **mechanism** uniformity, which this project has.
Sharing a traversal is not sharing a representation — the three share **no nodes**, and relating is what
nodes are for. Under Quine, meaning is relation; structures that share nothing mean nothing to each
other.

## 4. ⚠⚠ Uniformity is not one label — that would be Fodor's error at scale

The tempting fix is to rename all five to `before`. [harmonization.md](harmonization.md) already records
why not: **a synonym is a knowledge claim, and collapsing is Fodor's error at scale.** These are
genuinely different relations:

* **prescriptive** (`then`) — must hold; violating it is a defect.
* **descriptive** (`after`) — did hold; a record, and cannot be violated.
* **temporal** (`before`) — a partial order over moments, scalar or purely relative.
* **derivational** (`next` on frames) — *this state came from that one*, unrelated to when either was
  imagined.
* **form** (`next` on tokens) — word order, which the frame puts on the **language** layer. ⭐ It must
  **not** become temporal, or form has been smuggled into semantics — the one move the frame is against.

## 5. ⭐⭐⭐ The relaxation that works: a shared CORE, not a translation

The obvious weakening is *keep n representations and define translations between them*. It is a real
technique — **institutions** (Goguen & Burstall) are its mathematics, **distributed description logics**
and **E-connections** its applied form — but the condition is far stronger than it looks, and three costs
land badly here.

⚠ **Round-tripping is the wrong condition.** `g(f(a)) = a` says the *data* survives. What is needed is
that translation **commutes with the operations**: *translate then reason* = *reason then translate*
(an institution's satisfaction condition). A translation can round-trip perfectly and be wrong for every
inference — **`then` and `after` are the example.** You can map a required order onto an actual order and
back losslessly, and the translation is still false, because one is violable and the other is a record.
Bidirectionality cannot see modality; only commutation can, because **check** behaves differently on the
two sides.

The three costs:

* **k(k−1) translations**, and this codebase has already ruled on it at the mechanism level: *carrying
  one fact in two shapes is what blocks a swap*, and the recorded lesson says explicitly that **the
  tempting wrong fix was the translation** — a wrapper minting the missing shape per call, "which makes
  two things that must agree and lets them drift".
* **Materialise or derive**, and both have a recorded failure: eagerly, *a dormant twin rots*; lazily,
  every composed operation pays it — and *recognition during planning* means paying it inside the search.
* ⭐⭐⭐ **Translation destroys the residue, and the residue is the thesis.** A derivation crossing a
  translation has a step in the middle that means nothing in the domain, so *why* becomes "…and then I
  translated…". **A translation is an island with a bridge, and the bridge appears in every explanation
  that crosses it.** For a system whose product is the record, that is damage rather than tax.
* ✅ **The exception, already the practice: translation at the EDGE is fine.** `_UNMET_PHRASE`,
  `_DEVIATION_PHRASE` — facts on nodes, rendering in a table beside the reader. What to refuse is a
  translation between two internal representations that **both feed reasoning**.

⭐⭐ **And the argument that settles it: if `f` commutes with every operation, its image is a common
subrepresentation — so name it.** Conversely, any operation `f` fails to commute with is exactly the
operation you cannot compose across that boundary. A translation is therefore either *secretly a shared
representation*, or *a documented list of things that cannot be reasoned about jointly*.

So the useful relaxation is neither uniformity nor translation. It is **factoring**:

> **The five orders need not be one relation. They must share a core that is literally the same nodes
> and edges, and may each add what they need above it.**

All five are a strict partial order over nodes — that is the core. Above it: `before` adds an optional
scalar, `then` adds prescriptive modality, `after` adds *this happened*, frame `next` adds
*derived-from*, and token `next` relates to none of them — **stated, not omitted**. A rule reasoning
about order alone then works across all five, and *"they took turns before lunch"* has a reading,
without any of the five pretending to be another.

⭐ **`clock.py` is one step from this and stopped at the wrong place**: shared traversal, unshared nodes.
Sharing the nodes is the whole move, and it is smaller than either alternative.

## 6. ⭐⭐ Operations as data — necessary, and not sufficient

*If operations are data, the number of REAL operations shrinks — that is what compiling does.* True, and
it is this project's own premise. The formal content is **partial evaluation** and the **Futamura
projections**: an interpreter makes operations data, specialising it against a program *is* compilation,
and specialising the specialiser yields a compiler. It is also the principled answer to the interpretation
tax this arc keeps paying (`holds` at 2.35× on Sussman) — buy the cost back by specialising, rather than
by reverting a swap.

⭐ **It is the strongest justification the reflection arc has**, better than inspectability: it is *how
the operation set stays finite while coverage grows*. Without it, each new semantic category risks a new
module, and *"a finite set of reasonings"* stops being a property of the design and becomes a promise
kept by hand. Its most direct payoff is the matrix's weakest column, **recognition**: recognising
taking-turns from a trajectory becomes an authored rule rather than a module, and
[advice-over-sequences.md](advice-over-sequences.md) already argues recognition and prescription are one
predicate read two ways.

⚠ **But it relocates the obligation rather than discharging it.** *Does planning explicitly support
cause–effect semantics?* does not become vacuous when planning is a rule; it becomes a question about the
**rule**. This is the horizon result from the other side — *closed is a rate, not a kind; the closed
class is closed by **answerers**, not by prohibition.*

Three things it does not buy:

* **Kernel expressiveness.** §2's `[i+1]` gap survives any amount of reification, because the data is
  built from the same primitives. Reification reduces the *count* of operations; it does not extend the
  *reach* of what they are made of.
* **Relatability of the categories.** Reifying `plan` does not make `before` and `after` relate.
* ⚠ **The regress, which has a floor above zero.** When `rank` becomes a rule, selecting which `rank`
  applies requires ranking. The floor already exists here — `precedence.seal_rule`'s *the last stage must
  be total* — see [reflection.md](reflection.md). Finding the bound is the design work; there is no
  reduction to zero.

⭐⭐ **And reducing to ONE operation is achievable and useless, for §1's reason.** `eval` over encoded
descriptions has all the power and no relations. So the target is not *minimise the operation count*:

> **Minimise operations subject to each remaining one being relatable to what it operates on.**

Which means operations-as-data **inherits** requirement 2 rather than escaping it. An operation reified
as an opaque instruction blob is an island with extra steps; an operation reified as nodes sharing
structure with what they operate on is the win.

### ⭐⭐⭐ And by that test, this engine's operations-as-data is WRITE-ONLY

The distinction is checkable here today, and it fails. Operations *are* data — `rules/step.mf`,
`execute.mf`, `holds.mf`, all in the graph. But **nothing in the surface can read one.** From the phase
table in [HANDOFF.md](HANDOFF.md):

> **B3** — `_looker_for` / `_looker_on` scan a rule **body** for a `DISPATCH` whose tool only observes.
> ⚠ *a capability gap: nothing in the surface reads a body's instructions.*

So the reification was done for **execution** and not for **relating**. A rule can *run* an operation; it
cannot ask *which operations read time*, *which establish an order*, *is this operation about the
category I care about*. `access.bare_touches` reads bodies in Python and `reach.py` reads bytecode — the
surface reads nothing. ⭐ **That one line is the difference between operations-as-data paying off and
being ceremony**, and it sat in the audit as a minor seam because nothing had a reason to want it. This
is the reason. It is also the smallest of the reflection items.

## 7. How to know whether it is expressive enough — the discrimination pair

There is no single number, but there is a procedure:

> **For each semantic category, produce two situations in which the agent should ACT differently. Does
> it?**

⚠⚠⚠ **This was first written as a definability test — *can the representation distinguish them* — and
that is a theorem prover's question.** The correction matters because the two come apart in both
directions: a representation can distinguish two worlds while nothing in the agent's behaviour changes
(an idle distinction, bought and never spent), and an agent can behave correctly on a distinction its
representation only half makes, because a **preference** settled it rather than a proof.
**This project is a bounded agent, not a solver** — see the standing position in *How to work on this*
— so the deliverable is better conduct, never coverage of a model class.

⭐ **The engine's own probes already had this right.** The guard-address probe did not report *L1 cannot
express the distinction*; it reported a **worse plan at one off-topic constraint and no plan at two.**
That is the behavioural form, and it is why the result was believable.

If the pair cannot be constructed, the category is out of scope. If it can and the agent does the same
thing in both, the distinction is not earning its place — either the representation cannot carry it, or
nothing consults it, and **which of those it is, is the next question rather than a detail.**

⭐ **This project already runs this test under another name.** *A homogeneous fixture cannot measure a
discriminator*; *when a planted bug stays green the cause is a world that cannot express the defect*. The
guard-address probe is the model, and note what it reported: on Sussman the three levels produced **the
same plan** — nothing to tell apart — and once a second sort was added they produced **a worse plan, and
then no plan at all.** Behaviour throughout. The methodology exists; it has never been pointed at the
**semantic categories**.

Two conditions turn it into a criterion:

* **Closure** — can operation B consume operation A's output? That is requirement 2, checkable per pair.
* **No encoding** — does saying it introduce a name nothing else reaches? That is `reach.py`'s question
  asked of representations instead of code.

## 8. What this says about the matrix

* The **protocol / order** row is blank for a now-precise reason: not *nobody built it* but **the
  reference language cannot name a relative position**, and **there is no one order for it to be about.**
* A cell is ✅ only if the category is **statable** *and* its representation **relates** to the categories
  it must be reasoned about alongside. By that standard the existing ✅s want re-checking — cause–effect
  and time are the pair the requirement was raised about, and they are exactly the pair with nothing
  between them.
* ⭐ The derived **coverage pass** therefore has three halves, not one: per category, which operations
  name it; **per pair of categories, what nodes do their representations share**; and **which operations
  the surface can read** (§6). A category that relates to nothing is an island, and this codebase already
  knows what an island costs.

# Harmonization

A design thread. **Nothing here is built**, and the first thing it asks for is two measurements rather
than a mechanism.

The question it answers is one the project has been circling from two directions. The note behind
[advice-over-sequences.md](advice-over-sequences.md) asked whether planning should explore *synonyms and
expansions* — whether *taking turns* can be recognised as a shorthand for something that takes more
words. And [concepts.md](concepts.md)'s horizon says the web above it is Quinean: meaning is position in
a network of mutually supporting rules, and there is no definition to reduce a term to.

Put those together and a problem appears that neither raises on its own. **A web that grows only ever
grows apart.** Every corpus loaded, every episode compiled, every rule authored by a different hand adds
vocabulary, and nothing in the system pulls it back together. The machinery underneath speaks a fixed
terminology; the web above it drifts away from that terminology one authored rule at a time.

Harmonization is the proposal that the answer is not to learn, but to **reorganize** — offline, against a
target that already exists.

## Why it is not learning, and where it is

Learning has no fixed target, so it is validated by prediction. Harmonization has one — the terminology
the machinery already speaks — so it is validated by **invariance**:

> **The harmonized web must answer every question the un-harmonized one did, identically.**

That single sentence is what makes this tractable where "make the system learn vocabulary" is not. It
converts an open-ended problem into a normal-form problem, and normal-form problems have the questions
this project knows how to ask: does the rewrite terminate, is it confluent, and what does it cost.

Note what success is *not*. It is not "fewer terms". A static reader that loses information gets slower
before it gets wrong — `access.as_opcode` proved that, seven red checks and a suite that went from
59 seconds to minutes — so the honest measure of a harmonization is **cost**: fewer dispatch candidates
and fewer resolution calls for the same answers.

One honesty note on the framing. This *is* learning in the one respect that matters: it acquires a
disposition from experience, and future behaviour differs because of it. What it is not is *statistical*
learning. Every step is a rewrite justified by a **citation to a recorded episode** rather than by a
weight, which is why it can be audited at all — and auditability is the whole reason to prefer it.

## Offline is the load-bearing word

"What happens when humans sleep" is the right frame, and it is worth being precise about what it buys,
because it is not merely *when there is time*.

Offline means **no ambient goal and a world that is not changing**. Three things follow, and each is
something the system may not do online:

* **It may rewrite the web.** Online, a rule rewriting the rule library while a search reads it is a
  race. Offline there is no reader to race.
* **It may run the expensive check.** The invariance criterion above means re-answering the corpus. That
  is minutes, which is fine at rest and impossible on the hot path.
* **It may work without a goal.** Everything the planner does today is means-ends from an `unmet`
  constraint. There is no form for *tidy up*, and offline is exactly the regime where the absence of a
  goal is the point rather than a gap.

⭐ **The precedent already exists and is named.** `access.offenders` is a whole-corpus pass, enumerated
by reflection rather than from a list, that runs over every corpus the self-test builds and reports which
rules reach the graph unmediated. That is an offline reorganization pass in everything but the rewriting.
Harmonization is a second one of the same species, and it should be built the same way — by reflection
over what is there, never from a list somebody maintains.

### What sleep decomposes into, and how much of it exists

The metaphor survives inspection, which is the reason to keep it. Consolidation is usually described as
replay, abstraction, and pruning. Three of the four pieces are already here as separate mechanisms:

| | mechanism | state |
|---|---|---|
| **replay** — what did I actually do | `application.py`: an episode holds applications in order, each naming its function, bindings and outcome | ✅ built |
| **abstract** — turn the specific into the general | `compile_episode` / `generalise` | ✅ built |
| **prune** — drop what is not worth keeping | forgetting is the default; retention is a call-site choice | ✅ built |
| **harmonize** — make the vocabulary converge | — | **nothing** |

That table is the argument for the thread. Harmonization is not a new faculty bolted onto the side; it is
the missing sibling of `compile_episode`. Episode compilation generalises *a sequence of actions* into a
reusable one. Harmonization generalises *a vocabulary* into a canonical one. Same record, same offline
regime, same shape of output — a rewrite that must be checked before it is kept.

## The subject of the workbench is the rule library

Here is where the de-Pythonization arc stops being background and becomes the enabling condition.

The workbench is the system's one mechanism for *imagine a change, check it, then commit or discard*.
Harmonization is precisely that, with the rule library as the subject instead of the world. So the
question is whether a frame can hold a changed **function**, and the answer is that nothing in the
current design forbids it:

* Bodies are data — `function.define` writes instructions as ordered `instr` edges, `function.load`
  lifts them back.
* **An edge names an identity, never a version, and resolution happens on the target.** That is the rule
  the sparse-frame model rests on, and it says nothing about the target being a block rather than a
  function.
* A call resolves its callee by *name*, at run time, which is exactly the property mediated access was
  built to have: *"the machinery can change what a read means without editing a single rule."*

So **a harmonization is an imagined rewrite of the web, stepped on a workbench, checked against the
corpus, and committed or discarded like any other plan.** That is a real payoff of the arc rather than a
rhetorical one: before `step` was in the surface and rules were bound to identities, "imagine a different
rule" was not a representable thought.

⚠ **This is a claim to probe, not a design to build on.** `find_function` is a native
(`function.py:572`) and it does **not** resolve through the context — it is on the list of natives that
must, beside `plan` and `plan_step`, in [mediated-access.md](mediated-access.md). Until it does, a frame
cannot hold a different version of a function and the paragraph above is aspiration. The probe is small
and it should be run before anything else here: **can a workbench step call a function whose body the
frame changed?** If it cannot, that is one native, and it is a native that was already owed.

## The trap: a synonym is a knowledge claim

Collapsing two surfaces onto one is not bookkeeping. It asserts **substitutability** — and in a Quinean
web, meaning is position, so two terms sitting in different positions of the network are not the same
term however alike a human would gloss them.

This is **Fodor's decomposition error in a new costume**. *kill = cause to die* fails as a definition
because that relation lives above the horizon; it is a network relation, not a reduction. A harmonizer
that rewrites `X` to `Y` because the two co-occur is making exactly that mistake, mechanically and at
scale. And [limits.md](limits.md) says the same thing three separate times, about disjunction, about
scoped authority, and about modelling gaps generally: **the nearest available form is a different claim,
and a near-miss must not pass as a paraphrase.**

⚠⚠⚠ **Convergence is a loss operator.** Reaching a normal form is precisely the destruction of
distinctions. A system that always prefers its own dialect will, given enough sleep, become unable to
represent a distinction it has not yet had a use for — and it will do so silently, because a distinction
that no longer exists cannot report that it is missing.

## The safe form: mediate, do not collapse

The answer is the one this codebase keeps arriving at from other directions.

**Do not rewrite the corpus. Resolve at the seam.** A read goes through the closed eight, each of which
asks the ambient context how to resolve and calls the resolver **by name**. A harmonizing resolver is a
resolver, and the authored form is therefore **never destroyed** — the web keeps its diversity, the
machinery sees the canon, and an audit can always ask what was actually written.

### The substitution is CONDITIONED, and that is predicate dispatch

Fodor's argument is not that near-synonyms have exceptions. It is that two terms substitute in some
contexts and not others, and *which* contexts is not listable — which is why the decomposition was never
a decomposition. Any harmonizer that admits an unconditional rewrite has already lost that argument.

So a substitution carries a **condition**, exactly as every other judgement in this system does. And that
costs nothing new: **a conditioned substitution is predicate dispatch.** One name, several bodies,
`when` / `unless` guards, `fn.select` taking the most specific applicable one, `precedence._covers`
ordering them, declaration order breaking what the partial order cannot. A resolver with several bodies
*is* conditional substitution.

⚠ **This supersedes an earlier draft of this page**, which proposed a directed *scoped edge* — *`X` reads
as `Y` for the purposes of `M`* — and observed that it inherits the scoped-authority problem from
[limits.md](limits.md): the edge must name what it is about, so every reader must carry the subject
matter it is asking about, which is a change to readers rather than to one edge. The dispatch form does
not have that cost at all. The condition lives in a guard, where it can say anything, and no reader
changes.

⚠ **The cost it does have is a dependency, and a precise one.** The condition Fodor's argument demands is
about the **context of use** — *when planning a route* versus *when counting participants* — not about the
argument. That is a condition speaking of the ambient goal, reached by walking the activation chain, which
is predicate dispatch **slice 3**, and slice 3 is not built. The dependency is therefore sharper than "this
thread wants slices 3–4": **it wants slice 3 specifically, for exactly the reason Fodor gives.**

### Over-conditioning is the other failure, and it needs the second criterion

Condition a substitution finely enough and the guard becomes a restatement of the difference between the
two terms. Nothing has been explained: it is a **lookup table wearing a rule's clothes**, which is what
[baroque-vs-fundamental](concepts.md) already names.

So there are two acceptance criteria and they pull against each other:

> **Invariance says the rewrite is safe. Compression says it is worth having.**

Checkable: does the guard mention fewer things than the cases it covers? A guard with as many clauses as
there are supporting episodes has memorised rather than harmonised. Neither criterion alone is enough —
invariance alone permits the lookup table, compression alone permits the collapse.

## The criterion is behavioral, and the record already exists

This is the part that makes harmonization auditable instead of plausible.

> **Two surfaces may be harmonized only if no recorded application ever distinguished them.**

Not a gloss, not co-occurrence, not a similarity score. If the two ever led to different behaviour, they
are not synonyms, whatever a dictionary says — and if they never did, the rewrite is safe *by the only
evidence the system actually has*.

`application.py` is the record and it is already ordinary graph data: an application names its function,
its bindings and its outcome; an episode holds them in order; a binding is itself a node, so *what if
this had been applied to that* is already expressible. Its own docstring lists four capabilities that
depend on the record existing, and the fourth is "learning has something to read". This is that reading,
one level up from `compile_episode`.

⚠ **A correction of scope worth stating.** The obvious version of this criterion asks the *world's* past
— *were these two ever true of different things* — and that is squarely inside the documented gap: the
world graph is a single mutable state, frames are imagined futures rather than recorded pasts, and
observation records sightings of attributes only. Harmonization does **not** need that. It needs the
**derivation** record, which is kept. Building on episodes rather than on world history is the difference
between a thread that is blocked on the largest gap on the limits page and one that is not.

## Crystallization — the unit is a set, and the process is annealing

Once substitutions are conditioned, their guards mention terms whose own substitutions have guards
mentioning terms. The set is mutually constraining, which is Quine's holism arriving as a mechanical
property rather than a philosophical one. The consequence is stronger than *recheck downstream*:

> **A substitution can be invariance-breaking alone and invariance-preserving in company.**

Any procedure that accepts one rule at a time rejects exactly those. **Greedy per-rule acceptance is
therefore wrong**, and provably so under the holism being assumed — the unit of harmonization is a
**set**, not a rule.

The physical metaphor is worth taking literally rather than as decoration, because it carries four
things the set-formulation does not.

**The closed class is the seed crystal.** Free crystallization finds an arrangement; this one has a
template. The canon is the nucleus the web orders itself around, which is the same fact as *the target is
fixed* and a more faithful picture of it: order propagates outward from the canon and weakens with
distance, rather than being imposed uniformly.

⭐⭐ **Annealing is the answer to greedy.** A quenched crystal is full of defects; a slowly annealed one
reaches a lower-energy arrangement because it is allowed to accept locally worse moves while hot. That is
exactly what a substitution which only pays off once its neighbours move too requires. Search over sets is
combinatorial; annealing is the cheap, **anytime** way to do it, and anytime matters for an offline pass
that may be interrupted. The energy is the compression criterion above, with invariance as a hard
constraint.

⚠ **And it forces a two-tier cost structure.** Annealing wants many objective evaluations; the invariance
check is minutes, because it re-answers the corpus. So the search runs on a **cheap local energy**
evaluated against the episode record — *which recorded applications does this substitution touch* — and
the whole-corpus invariance check is the **commit gate**, not the objective. A pass that puts the
expensive check inside the loop will not run at all.

⭐⭐⭐ **Real solids are polycrystalline, and that is the desirable outcome.** Matter rarely forms one
crystal; it forms **grains** — locally ordered, mismatched at the boundaries. Harmonization will not
produce one global canon either, and the seams will fall where two corpora, two authors, two loaded
domains meet. **Forcing a single global canon is the collapse failure.** A grain boundary is where the
distinction genuinely lives: two near-synonyms conditioned differently by two domains, which is the scoped
condition discovered empirically instead of authored. So **the pass reports its boundaries as findings
rather than eliminating them** — and that report is available from the episode record *before* anything is
rewritten, which makes it the cheapest useful output this thread has.

**A defect is information about the canon.** A term that resists harmonization is a distinction the
episode record supports and the terminology lacks — evidence that the **canon** is wrong rather than the
web. That is the horizon's third answer, *expand the closed class*, reached empirically instead of by
argument.

⚠ Which stays a **report to a person, always.** The closed class is the target, not the subject; a pass
that normalizes the canon has dissolved the fixed point that made this not-learning. And the CNL cannot
grow itself on purpose — a form with nothing that runs it is worse than no form — so *expand the closed
class* is a decision with an executor attached, never an automatic move.

### What this is not: a TMS

Read as **propagation** — an adoption travelling along dependency edges, maintaining consistency as it
goes — crystallization would be a truth maintenance system, and this project deleted all of its
retraction/TMS machinery once, deliberately. The note behind
[advice-over-sequences.md](advice-over-sequences.md) proposed "crystal edges" in that sense and §5 there
ruled against them.

**The lattice reading is not that**, and the distinction is the whole point: mutual accommodation under a
global objective is **re-derivation**, not message-passing. So each offline pass **rebuilds** the
harmonization from the episode record rather than patching the previous one — idempotent, consistent with
*extend ≡ rebuild*, and it honours the interdependence by re-deriving the whole set, which is what the
search does anyway. Caching stays what it always is here: a measured optimisation, decided by
`python -m ugm.bench`.

⚠ **Where the set-search meets a known open question.** Comparing rival arrangements is recorded in
[HANDOFF.md](HANDOFF.md) as missing — *"today the only way to compare two interpretations is to run both.
That is a probe, not a build."* A search over sets of substitutions is that question in its third
appearance, and this page does not close it.

## Two problems, not one

The original note bundles them and they have different homes.

**(a) Surface synonymy** — different words, one referent. This is the mediation seam above. A scoped
resolver, a behavioral criterion, no new mechanism obviously required.

**(b) Route convergence** — *"use expansion and deduction rules not randomly, but to converge"*. This is
not synonymy at all; it is **search bias**. Several rules reach one conclusion by different routes, and
the want is that the routes landing in canonical vocabulary are preferred. That already has a home:
`precedence` is authored data with a `run <fn>` escape into the web, so this is a **stage that scores a
candidate by whether its conclusion lands in the canon** — no new machinery, and it inherits the
constraints already recorded there. ⚠ The last stage must be **total**, and a function stage must be a
**consistent** comparator.

Keeping (b) in `precedence` also keeps it honest in a way that a rewrite cannot be: a preference changes
which route is *tried first* and never which conclusions are *reachable*, so it cannot destroy a
distinction. Where a choice exists between doing something as (a) or as (b), **prefer (b)**.

## What must not happen

* **No rewrite of authored text.** The `.mf` a person wrote is the audit trail. Harmonization adds
  resolution, it does not edit sources.
* **No unconditional substitution, and no unscoped equivalence.** A symmetric `same_as` between two
  open-class terms is the collapse this whole page exists to refuse, and an unconditional rewrite has
  already conceded Fodor's argument.
* **No greedy acceptance.** A substitution is accepted as part of an arrangement or not at all.
* **No harmonization of the closed class.** The eight names, `consequent.KINDS`, `precedence.STAGES`, the
  constraint forms — these are the target, not the subject. A pass that normalizes the canon has removed
  the fixed point that made it not-learning.
* **No Python.** *Anything expressible is in scope; the question is never whether but how, and the how
  must be data.* An offline pass written in Python is an unreachable island with a whole-corpus blast
  radius — the worst possible place for one.
* **No silent commit.** A harmonization that runs unattended and is kept without a check is the failure
  mode this project has already met twice under a different name, where **cost was the only symptom**.

## Acceptance is the benchmark, not only the suite

⭐⭐ Worth stating separately because it is the non-obvious operational requirement. The failure mode of a
bad harmonization is not a red check. It is a planner that ranks everything alike because a reader lost
information, and that shows up as **minutes instead of seconds** with every individual answer still
correct. Both `relate` storing a version and disabling `access.as_opcode` failed exactly that way.

So a harmonization pass is accepted by `python -m ugm.bench` as well as `python -m ugm.selftest`, and
⚠ measured against the tree it changed, in the same minutes.

## Harmonization as training — the learning formulation

A sharper way to pose the whole thing, and it turns harmonization from a rewriting procedure into a
*learning* one: **fix the forms of the rules, and let the system search only for (a) which tokens fill
the slots in the criteria and (b) the ordering of rules** — until the rules produce the output needed,
which for language means *the data that activates the goal machinery when an utterance asks for
something*. Trained layer by layer, since each layer has a checkable target.

### It has a name, in fact several

| the piece | what it is called |
|---|---|
| fixed rule forms, learn the slot fillers | **Meta-Interpretive Learning** (Muggleton; `Metagol`) — *metarules* are second-order templates and the learner finds the predicates. Also **sketch-based synthesis** (Solar-Lezama): fix the skeleton, synthesise the holes |
| constraining what may fill a slot | ILP **mode declarations** / declarative bias (Progol, Aleph, Popper) |
| learning the **ordering** | **decision-list learning** (Rivest); ordered theories in ILP |
| supervising on the *output* rather than the rule | **learning from denotations** (Clarke et al. 2010; Liang 2011) — the world's response is the signal |
| layer by layer | staged supervision; **predicate invention** is MIL's hierarchical form |

So not a new kind of machine learning — but a well-motivated instance of a known one. Evolutionary search
would *work* and is probably the wrong tool: the space is discrete and highly structured, so constraint
solving (Popper is ASP-based) or annealing beats blind variation. ⭐ And this document already argued for
annealing over **sets** on holism grounds — the search method it specifies is the right one for the
learning problem, arrived at independently.

### Three things make the setting unusually favourable

1. ⭐⭐ **Credit assignment is free.** The standing nightmare in learning rule systems is knowing which
   rule to blame. Here the derivation is recorded — which rule applied, why it was preferred, what it
   rested on — so blame is a graph read rather than an inference.
2. ⭐ **Layer-by-layer is only possible because intermediate states carry meaning.** A target can be
   defined at each layer instead of only at the end. In a system whose intermediate representations were
   engine state there would be nothing to supervise but the final answer.
3. ⭐ **The learning target is a defined slot, not open program space** — the *addressing* half of a
   guard, which `criterion.py` already has (`wants <sort> <label>`) and function guards lack. That is a
   far smaller hypothesis space than "synthesise a program".

### Effort is a dial, and the learned order does double duty

⭐⭐⭐ **How many rules are tried is a budget, not a constant.** Dispatch does not have to evaluate every
applicable body; it can try them **in learned-preference order and stop when effort runs out** — which
makes interpretation *anytime*: an answer at any budget, a better one with more. That converts the
measured cost (`fn.select` at 63 ms with 100 applicable bodies, see
[predicate-dispatch.md](predicate-dispatch.md)) from a wall into a parameter, and it is the same
*think-harder* dial the rest of the system already exposes as `max_steps` and `max_depth`.

And the two halves of the problem collapse into one artifact: **the learned order is simultaneously the
disambiguation preference and the search order that makes it affordable.** One thing to learn, two jobs.

The architecture for it is already declared. `precedence.STAGES` composes lexicographically —
`by authority`, `by force`, `by specificity`, `by random` — with the rule that **the last stage must be
total**. Subsumption (`_covers`) supplies a *partial* order for free, so **only incomparable pairs need
learning**, which is a large reduction taken before any search starts. ⚠ Note what does *not* yet exist:
`EXPERIENCE` in `precedence.py` is only the default *attributor* — an unattributed rule is credited to
`experience` — and there is **no `by experience` comparator**. Adding one is the designed extension point
(`STAGES` is a closed vocabulary whose entry cost is "write its comparator", with `run <fn>` as the
escape), and `application.py` already holds the behavioural record it would read.

### Ambiguity is rarer than the combinatorics suggest — and the excess is an artifact

The number of sentences with genuinely competing readings *that change what to do* is low. Most ambiguity
is either settled trivially by the world or makes no difference to the action, and an agent in a bounded
domain meets little of the rest.

⭐⭐ The sharper form: **local ambiguity is an artifact of parsing, not of interpretation.** A chart must
materialise every locally-possible constituent precisely because it cannot know which will be used —
that is what a forest is *for*. An effort-bounded interpreter that proposes and selects never builds the
readings it does not try. So the combinatorial fear is inherited from the architecture being replaced,
and it is one more argument for replacing it.

### What is genuinely hard

* **The objective.** Targets have to come from somewhere: hand-authored pairs (expensive, and the corpus
  is small), an LLM at the boundary, or **task success** — the most attractive signal and the sparsest.
* **Overfitting**, in its classic inductive form: too specific and a rule fires only on the sentence it
  was learned from; too general and it overgenerates. ILP's answer is a compression / MDL criterion, and
  this would want one. It is the same failure this document already names as **over-conditioning**.
* **Evaluation cost.** Every candidate rule set must be *run*. The effort dial bounds a single
  interpretation; it does not bound the search over rule sets, so the `_covers` precompute matters before
  any of this rather than after.

### The cheap probe that decides it

Take a handful of existing CNL utterances whose target goal-structure is already known, blank out the
**address** half of the relevant guards, and ask whether search over candidate attributes recovers them —
and how the space grows with the number of blanked slots. That answers *is this tractable at all* for the
price of an afternoon, and it is the same discipline as measuring the blast radius before building an
enforcement. Do it before designing anything.

## Probes before any of it

Per the standing discipline — *test the claim before building the fix for it*, and *measure the blast
radius before building the enforcement*, which last time expected many and found one.

1. **Is there anything to harmonize?** Instrument resolution across the whole corpus; count distinct
   surfaces that land on one identity, and distinct rules whose conclusions differ only in vocabulary.
   **If this is near zero the thread is premature and should stay a thread.** This is the same
   instrumentation `step` already carried for the mediation sweep.
2. **Is there route divergence?** Count distinct derivation routes reaching the same conclusion across
   the suite. This is what (b) would bias, and if the corpus has one route per conclusion there is
   nothing to prefer between.
3. **Can a frame hold a changed rule?** The `find_function` probe above. One check: step a workbench
   whose frame carries a different body for a called function, and see whether the call reaches it.
4. **Does the record support the criterion?** Take two terms in the corpus that a human would gloss
   alike, and ask the episode record whether anything ever distinguished them. If the record cannot
   answer, the criterion is not yet implementable and *that* is the finding.
5. **Where are the grain boundaries?** Report, from the episode record alone, the places where two
   corpora use different terms for what behaves alike. This rewrites nothing, needs no dispatch and no
   annealing, and is useful on its own — which makes it the one to run first if any of these are run at
   all.

## What capability, if any, is genuinely new

The invitation was to create one if it is needed. The disciplined answer, per *decompose before believing
something is primitive* — which turned six proposed natives into five opcodes and two edge reads — is
**probably not an opcode**:

* The rewrite is a program. `function.define` writes rules, `ATTEMPT` answers without raising, `REFUSE`
  declines with a reason, reflection reads bodies back.
* The conditioning is **predicate dispatch**, which exists.
* The preference is a `precedence` stage, which is authored data by design.
* The record is `application.py`, which is already ordinary nodes.
* The one native that is owed — `find_function` resolving through the context — was already owed for
  another reason.

⭐ What it does need, and this is the one hard prerequisite rather than a nice-to-have: **predicate
dispatch slice 3**. A substitution conditioned on the argument is not what Fodor's argument asks for; a
substitution conditioned on the *context of use* is, and that is a guard speaking of the ambient goal.
Without it the conditioning collapses back to the unconditional rewrite this page refuses.

What *is* new is a **totality obligation**, and it is the same one `VKIND` was just added to discharge one
level down. `compare` could not catch a `TypeError`, so it had to **ask first** what category a value was.
A normalizer has the identical shape: it must answer for **every** term, including *I have no
normalization for this*, and it cannot raise. ⭐ The pattern generalises and is worth naming, because it
has now appeared twice: **a program that cannot catch must be able to ask.** Whether the asking here needs
a category opcode over *terms* the way `VKIND` is one over *values*, or whether an edge read suffices, is
exactly the decomposition probe to run rather than the assumption to build on.

And the honest remaining blocker is not a capability at all. **A gap should become a want, not a
refusal** — when the machinery meets a term it cannot consume, the right outcome is a subgoal, so finding
the normalization becomes something the system can *plan* toward, closable by asking a person, by
deduction from the web, or by observation. That is predicate dispatch **slice 4**, and it is already the
prize named at the end of [HANDOFF.md](HANDOFF.md) for two other reasons. This is the third.

# Revision 01 — standing circuits

**Status: design revision, adopted 2026-07-27.** This revises `model.md` and replaces
`docs/units/attachment.md`, which is folded in below and deleted. Nothing here is built.

`model.md` said computation is scaffolding built over the data, used, and **thrown away**. That is now half
wrong. The scaffolding is built over the data and **stays**; what is thrown away each turn is not the circuit
but the *values in it*, which are re-established from the axioms at the start of every turn.

This document records the revision, what it retires, and what it opens.

---

## 1. The claim

> Some rules fire and change asserted data. Others become **standing units** wired into the graph, and the
> facts they produce exist for exactly as long as the unit is powered.

*Socrates is a man*, *all men are mortal*. The deduction is physically connected to both premises and produces
*Socrates is mortal* at its output. Change either premise and the conclusion is not retracted — it simply is
not produced on the next revive.

Three things fall out immediately, and they are the reason to adopt this.

**Provenance is free and is not data.** The derivation is not written back and stored; it *is* the wiring. A
conclusion is attached to what produced it, so *"why do you believe this"* is a walk, not a lookup, and it costs
nothing beyond the circuit that computed it.

**Accretion stops.** The spike found conclusions accreting superlinearly across steps, because every step wrote
its conclusions *and* their derivations as new data. A standing unit holds one output. Re-deriving does not
re-write.

**Retraction machinery is unnecessary** — see §3, which is where most of the simplification actually lands.

---

## 2. Two dispositions

A unit's output is either **applied** or **held**, and this is structural.

| disposition | behaviour |
|---|---|
| **mutating** | the unit fires, its output changes asserted data at write-back, and that is the end of it |
| **materializing** | the unit stands, and its output is part of the graph for as long as it is powered |

Mutating rules are how axioms change. Materializing rules are how everything else exists. A materialized fact
is never edited and never deleted; it appears and disappears with its support.

*Note, not an objection:* the disposition is structural rather than a fact about the unit, so a rule cannot
conclude which one applies and the CNL must mark it syntactically.

---

## 3. Revive from axioms

**A turn begins by firing from the axioms** — the facts with no predecessors — and letting the circuit
stabilize. Materialized facts are therefore **recomputed each turn, not maintained**.

This is the decision that retires the most machinery, and it is worth being explicit about how much:

| would have been needed under incremental maintenance | why it is not needed |
|---|---|
| retraction propagation / cascade delete | nothing is retracted. The next revive does not reach it |
| justification sets, in-lists, multiple support | two units producing the same content are two live outputs. **Create, never merge** already guarantees they are structurally distinct, so killing one leaves the other standing with no bookkeeping |
| well-founded support checking | support is a value that arrived on a wire, not a label computed by a solver. Nearly everything hard about truth maintenance is an artifact of labelling, and there is no labelling here |
| detection of ungrounded cycles | a cycle not reachable from an axiom is never powered, so it never fires and never produces anything. It is structurally silent, not detected-and-suppressed |
| delta tracking, invalidation bookkeeping | the graph state is a pure function of *(axioms, wiring)*. There is nothing to invalidate |

The last two rows are the ones to keep in view: **unpoweredness is structural.** That is the property that
makes the whole scheme cheap, and it is what a labelling-based TMS has to pay for with a solver.

**The cost, stated plainly.** Every turn is O(circuit), and the circuit grows monotonically as standing units
accumulate. This is `model.md` §13's *retention* question arriving in a new form: not *"the graph grows"* but
*"the revive gets slower."* Incremental revive — firing only from axioms that changed — is available later as a
pure optimisation, and is deliberately not taken now, because it reintroduces exactly the bookkeeping the table
above deletes. **Measure before taking it.**

**§1 needs one amendment.** *"Nothing happens unbidden"* is breached by a revive that fires with no goal
asking. The line that keeps this from growing back into an evaluator:

> **No *reasoning* happens unbidden. Re-establishing conclusions already drawn is maintenance, not reasoning.**

---

## 4. Cycles: grow on revisit, and burn

A powered cycle still runs forever. It is bounded by **energy**.

- Every value carries an energy. It **grows**, and only **on revisit** — when a value returns to a unit it has
  already passed through.
- Crossing the threshold is a **surge**. The detector **burns** an arbitrary element of the loop, breaking it,
  and emits `surged` as a positive fact naming the units the energy travelled through.

**Growth rather than decay**, for three reasons. It fails *loudly* — a surge is an event at a definite moment,
where a decay to zero has to be detected as an absence, which is exactly what §8 exists to forbid. It *names
the loop*, because the units just traversed are the cycle, where a decayed value cannot say whether it was deep
or looping. And it cannot cause a **false absence**: decay pushes a live fact toward θ, so a still-supported
conclusion could drop below threshold and read as *absent* under §4, firing negation-dependent rules on a
purely mechanical artifact. Growth pushes away from θ.

**On revisit rather than per hop**, because no scalar accumulated per hop can separate depth from cycling —
they are the same quantity. Charging per hop makes a long sound derivation indistinguishable from a loop, and
with bands finite (§4) the chain-length limit would be the number of bands. Charging on revisit leaves acyclic
chains at full strength however deep.

**Energy is plumbing.** It carries no epistemic content, it is not a band, and it is **never consulted by the θ
test**. It is the sibling of `model.md` §11's *"IDs are plumbing."* Deduction is not lossy: a certain premise
through a certain rule yields a certain conclusion, at any depth.

**No static cycle check.** Detecting cycles in the wiring at assembly time was considered and **rejected**: on a
large graph it is a global scan, and it is redundant against a runtime detector that catches dynamically formed
loops anyway. §3 already makes unpowered cycles free.

**Open — does the burn persist?** If it is transient, every revive pays the surge cost again for the same loop.
If it persists, engine policy has made a durable edit to structure the author never authorized. Recommendation
on record: **transient burn, persistent `surged` fact**, so the author can see it and a rule can conclude a
real fix. Not yet decided.

---

## 5. Attention binds dangling gates

A unit may stand **partially wired**. An unconnected input is not an error and not a pending assembly step; it
is a stable state in which the unit holds, does not fire, and produces nothing. This is what dissolves
`attachment.md`'s crux — see §7.

> **A dangling gate holds attention on its region.**

This is the second decision worth as much as §3, because it *derives* something `model.md` currently
stipulates. §7 asserts as a hard requirement that *"a pending goal must stay attended"*, pinned or refreshed by
its own pendency. Under this rule it is not a requirement at all: a pending goal **is** an unsatisfied
satisfaction condition, which is a dangling gate, which holds attention. Goal-pinning stops being a special
case and becomes a consequence.

Four things collapse into one shape:

| | |
|---|---|
| an unwired premise | a gate with nothing on it |
| a pending tool call (§9) | a gate that will be filled later |
| a starved gate emitting a miss (§9) | the same gate, asking |
| a pinned pending goal (§7) | the same gate, holding attention |

And System 1's job widens accordingly: it proposes **wirings**, not only rules. That needs no amendment —
`model.md` invariant 4 already reserves the slot: *units never wire anything; if routing is ever learned, units
propose wirings as facts.*

### A dangling gate is also a trigger

The same structure, read from the other end, is a **standing watch**. A unit wired to fire on a condition that
has not occurred sits attended with an empty gate; if the condition ever arises, the gate fills and it fires.
*"Tell me when the price drops"* and *"watch out not to do this while you proceed"* are the same object, and
they need no monitor mechanism, no subscription, and no periodic check.

`model.md` §9 already lists a standing watch as one of the four cases suspension covers. This says why they are
one case: a pending tool call and a standing prohibition are both *a gate that has not been filled*, and the
only difference is whether anyone expects it to be.

The prohibition reading is worth singling out because §4 removed cheap exact negation. *"Do not do X"* is not
implemented by testing that X is absent — a test that is now a θ threshold and can be wrong. It is implemented
by **waiting for X to be present** and firing an alarm. A negative constraint becomes a positive trigger, which
is the same move §8 makes for outcomes: never an absence, always a fact.

This also supplies the counterweight to the attention leak below. Not every long-lived dangling gate is
abandoned business — some are deliberately standing, and a decay policy that cannot tell a forgotten subgoal
from an active prohibition will silently drop guardrails. That distinction is **data**: a rule concludes that
something is to be kept attended, exactly as it concludes anything else. Which means the decay policy has to
consult attention-holding facts, not just age.

### The Zeigarnik correspondence

Lewin's account of the Zeigarnik effect is that an incomplete task maintains a *tension system* that keeps it
accessible, and that completing the task discharges the tension. The mapping is close enough to be worth
recording: an unfilled gate exerts attentional pull; the gate fills, the unit fires, there is no longer a
dangling gate, and the pull ends. Discharge is not a separate mechanism — it is the disappearance of the thing
that was holding.

Two honest qualifications. The empirical effect replicates unevenly and is moderated by involvement and by
expectation of completion, so it is a *correspondence*, not evidence — the mechanism stands on the §7
unification regardless. And the correspondence is imperfect in a way that points at a real problem: people do
eventually forget uncompleted tasks, whereas a dangling gate as specified holds attention **forever**.

**Open — attention leak.** As standing units accumulate, so do dangling gates, and attention is progressively
consumed by ancient unfinished business. Something must decay or reap them. Note where this puts decay: on the
**attention** axis, which is where it belongs, and not on the energy axis, where §4 rejects it. §7's existing
warning applies — uniform decay drifts off the goal — but a goal is a dangling gate too, so the interaction
needs designing rather than assuming.

---

## 6. What this changes in `model.md`

| § | change |
|---|---|
| 1 | computation is not thrown away; the **wiring** persists and the **values** are re-established. Maintenance ≠ reasoning |
| 2 | *"not a fixpoint engine"* → the revive **is** a run to stabilization, bounded by surge detection |
| 4 | energy is non-epistemic and never consulted by the θ test |
| 5 | units stand across turns; gates hold across turns; a partially wired unit is a stable state |
| 7 | attention binds dangling gates; goal-pinning becomes a consequence rather than a requirement |
| 8 | `surged` joins the outcome facts; energy is fuel, localized to a wire rather than counted per step |
| 9 | derivations are **not** written back — the wiring is the derivation. Write-back happens after stabilization, never during |
| 13 | *homoiconicity* stops being deferred and becomes **required**; *what a step costs* is answered; *retention* is reshaped; *attachment* is closed |

**Homoiconicity is now load-bearing.** §1's claim that data is the substrate survives only if standing units
are themselves graph data. Otherwise there are two substrates — a graph, and a live circuit beside it — and the
claim is simply false. §13 listed homoiconicity as *"tempting; not yet"*; it is now a precondition.

---

## 7. `attachment.md`, folded

That document proposed grafting rules onto the nodes they apply to, firing there, and **dissolving**. This
revision is the same graft with the opposite ending: graft and **stand**. Its five stated problems resolve as
follows.

| problem | resolution |
|---|---|
| **multi-premise anchoring** — *"if x is a bird and not a penguin"* attaches where? | **dissolved.** A partially wired unit is a stable state (§5). It attaches where it can, holds, produces nothing, and its empty gate both asks (§9's miss) and holds attention (§5). Anchoring is incremental, not a precondition |
| **defining *neighbourhood* without smuggling the projection back in** | not needed. A unit reaches only what is wired to it; nothing walks a neighbourhood |
| **dissolution versus reuse** | there is no dissolution. Attachment is per-(rule, position) and it stands |
| **ordering and termination** | §4. Surge detection replaces the attachment policy that would have had to bound re-attachment |
| **retrieval becomes attachment** — a strictly larger question | accepted, and it is where the remaining cost is. System 1 proposes wirings as well as rules; whether attention bounds gate-matching the way it bounds rule recall is open (§8) |

Its cooldown table — with the declared *"scheduling policy leaks into semantics"* breach — is **deleted
outright**. *"This rule already fired here"* is not a cache entry and not an absence of attachment; the unit is
simply still standing, holding its output.

Its §4 acceptance harness survives and remains the specification any build must meet, with two changes: the two
cooldown rows go, and one row is added.

| behaviour | note |
|---|---|
| the same rule fires inside and outside a hypothesis, and no rule pattern names a scope | unchanged |
| two sibling hypotheses in one circuit do not contaminate each other | unchanged |
| a conclusion cannot leave a tunnel unless something attached to the end marker | unchanged |
| a general rule chains onto a conclusion made under an assumption | unchanged |
| …and that chained conclusion stays **inside** the assumption | unchanged |
| the base world cannot see into an assumption, but can see that it exists | unchanged |
| ~~conclusions do not accrete without bound across steps~~ | **retired** — §1, there is nothing to accrete |
| ~~a change to a node makes the rule applicable again~~ | **retired** — §3, every revive re-establishes from the axioms |
| **changing an axiom makes a fact derived from it absent on the next revive, with nothing retracted** | **new** — the central claim of this revision |
| **a powered cycle surges, is burned, and reports the loop it found** | **new** — §4 |
| **a long acyclic chain does not surge and does not weaken** | **new** — §4, the reason revisit-counting beats hop-counting |

---

## 8. Spike results — `units/standing.py`, 16 green

Built 2026-07-27 as a separate module, per `attachment.md` §5's own advice not to retrofit. Every claim
in §§1–5 has a test, and every test was **mutation-checked**: the mechanism it claims to test was broken
on purpose to confirm the test fails. Six probes, six kills.

| mutation | result |
|---|---|
| energy counts hops instead of revisits | kills the long-chain test — the discrimination is real |
| surge detection disabled | kills the cycle test, and **hung** before a fuel backstop existed |
| revive does not clear cells (maintained, not recomputed) | kills the fade test |
| scope ignored, cells pooled | kills the seal test |
| carry-forward output instead of subset output | kills the positioning test |
| fuel backstop removed | kills the budget test |

**Three findings.**

**1. The first version of the headline test was vacuous, and mutation testing is what caught it.** It
asserted that a conclusion lives at its producer and nowhere else — which **carry-forward also
satisfies**, because carry-forward pollutes the *conclusion's* cell with the premises rather than the
other way round. The claim that actually separates positioning from a pool-on-a-wire is `0008` **subset
output**: a cell holds what its unit derived and *nothing else*. So positioning does not merely coexist
with `0008` — it is the thing that makes `0008` correct, reversing the carry-forward `unit.rule` adopted
for the tunnel and settling the tension its docstring flagged.

**2. Surge detection is the *only* termination guarantee, and that is dangerous.** With the surge check
mutated out, the revive does not terminate — it hangs. This is the fail-dangerous asymmetry of growth
over decay showing up in practice rather than in argument: a decaying cycle dies whether or not anyone
is watching; a growing one stops only because a detector fired. `model.md` §8's inner budget is
therefore **not belt-and-braces here, it is load-bearing**, and `revive()` takes fuel with
`out_of_fuel` recorded as a fact.

**3. The seal leaked in the direction nobody was testing.** Nesting a *conclusion* under a supposition
is not enough: the supposition's own cell sat at base level, so the base world could read the
**antecedent** even though it could not read the consequent. Fixed with `Cell.scope` — a cell that *is*
a containment holds its own content — which is `model.md` §6's *"you can see that a supposition exists
without seeing inside it"* made structural. Worth noting because it is exactly the class of defect
`STATUS.md` records seven of: it does not crash, it degrades quietly.

**What the spike did *not* test:** retrieval, attention, the outer loop, graded band propagation through
a chain, and revive cost at scale. It tests the substrate claims only.

---

## 9. Hypotheses, contradiction, and elimination

Revive-from-axioms has a consequence worth stating on its own, because it removes a mechanism rather
than adding one.

> **There are no overlays.** Everything a unit derives is discarded at the next revive, so a derived
> claim needs no special "temporary" status. There is one kind of derived thing.

An earlier draft of this section invented an `Overlay` distinct from an ordinary conclusion, and a
composition rule for reading a node "relative to a cell" — inner values shadowing outer ones, lexical
scoping. Both were wrong. Shadowing is a **precedence policy hardcoded in the engine**, which is exactly
the judgement §11 says must stay authored, and the temporary-vs-permanent distinction is a *kind*
(§11 again) that revive already provides for free.

**And the simplification goes one step further than it first appears.** If a unit is itself a node
(homoiconicity, §6 — already a precondition), then a derived fact **hanging off its producing unit** is
both "in the graph" and "positioned", with no `Cell` as a separate species of thing. Position is an
edge from the unit that produced it; provenance is that edge; discarding the derived layer is dropping
what hangs off units. The spike's `Cell` is scaffolding for a type that should not survive.

### Alternatives are not contradictions

Several hypotheses may be live at once, and their conclusions **coexist physically in the graph**.
*"Paul is a man"* and *"Paul is a woman"* under two suppositions are two alternatives, not a conflict.
This is what makes contradiction detection an ordinary rule: the conflicting claims are *there*, to be
matched.

### A contradiction refutes the configuration that powered it

Reductio is the main case, not a special one. A detector wired to a **single** hypothesis that derives
both *P* and *¬P* refutes that hypothesis — there is no "wired to both".

The general statement, which covers both:

> A contradiction condemns **whatever configuration fed the detector**. That configuration is not
> something a rule asks about — it is read off the wiring by walking backwards.

So no rule names a scope (invariant 1) and blame assignment is provenance doing real work. Feeding one
detector from two suppositions asserts their *conjunction*, and reporting a contradiction there is
correct. Which of the blamed assumptions to discard is a further **rule's** judgement, not the engine's
— base axioms simply are not discardable, so in the ordinary case only one candidate remains.

### The enumerator

Round-robin over hypotheses, one powered per turn, gives search — and abduction — with no new mechanism.
Two things it depends on:

- **Its cursor must be asserted data**, advanced by a mutating rule at write-back. A cursor held as a
  derived fact resets to the first hypothesis on every revive. This is the canonical case for the two
  dispositions in §2: search *state* is asserted, search *consequences* are materialized.
- **A refutation must cross to an axiom.** Concluded inside the hypothesis it refutes, it dies with it
  the moment the enumerator moves on, and the search becomes amnesiac.

⚠ **Elimination proves nothing unless the enumeration is exhaustive**, and the engine cannot know that
— it is a knowledge claim (§11). The survivor of an elimination is **un-refuted**, never **proven**: the
same weak, honest claim as `starved` ≠ underivable.

### Checkpointing — scoping what is *mutated*

Positioning scopes what is **derived** and does nothing for what is **mutated**. Materialized facts are
recomputed every revive, so a hypothesis's conclusions are free — but a mutating rule firing under a
hypothesis writes to the shared asserted layer, permanently. Any hypothesis whose exploration takes more
than one turn therefore corrupts the base world, precisely because its state has to survive the revive
that discards everything else.

> **A checkpoint is the asserted layer, nested inside a supposition.** Mutation under the hypothesis
> lands there. `commit` merges it back; `discard` drops it. Those are the only two exits, one explicit
> act each — the same shape as §6's crossing.

**Deliberate, never automatic.** The machine supports checkpointing; it never decides to checkpoint.
Branching the world is an operation a rule concludes, exactly as it concludes a deletion — a judgement
in the data, inspectable and revisable, not a policy in the engine (§11).

This is `ugm`'s [[derivation-frame-consolidation]] finding re-derived from the other side: the fix is a
materialized **copy with merge-back at one boundary**, never a read-projection, because a projection
isolates reads and not writes. Two independent routes to the same answer.

⚠ **Search state lives outside the checkpoints it controls.** The enumerator's cursor and its
refutations are exactly what must survive a branch being abandoned; checkpointed, a `discard` would roll
them back and the search would loop forever on the hypothesis it just refuted.

⚠ **Abandoned checkpoints are a leak.** Nothing reclaims one on its own — a refuted hypothesis whose
checkpoint is never discarded persists, and writing that rule is the author's job (§11).

### Attention: think-harder as random restart

Fixation (§5's attention leak, and `model.md` §13's self-reinforcement) is answered by allowing
**randomised refocus when thinking harder**. This is PageRank's random-surfer damping, which exists to
solve the identical pathology, and it is the same *diversity rather than top-k* mitigation §7 already
asks for — triggered by effort level rather than run continuously, so it costs nothing when nobody
asked. Two constraints: sample **outward from what is attended**, a hop or two, never uniformly over the
twin (uniform sampling is the thing attention exists to prevent); and **record what was granted**, or a
turn becomes unexplainable, which is the one thing provenance-as-wiring was supposed to guarantee. Not
spiked — the spike tests substrate claims only, not retrieval.

### Spike results — `units/tests/test_hypotheses.py`, 8 green (102 total)

**The finding that changed the design: a derived claim must be a node, not an attribute write.**
`Graph.union` merges attributes *by node*, so two live derivations disagreeing about one `(node, attr)`
silently collapsed to whichever was unioned last — and the contradiction became invisible **exactly when
it mattered**. Two values for one attribute are not representable as attributes at all. This is §3's
argument for occurrence nodes arriving one level down: an attribution is a thing that is asserted, so it
is a node. Mutation-checked: reverting to an attribute write kills the contradiction test.

**Second finding: a checkpoint is copy-on-write for free.** The first implementation deep-copied the
asserted layer, on the assumption that exploring *n* hypotheses would otherwise cost O(twin × n) and
kill the enumerator on a real twin. Mutation testing showed the copy makes **no semantic difference**:
`Graph` is immutable, so a mutating rule *replaces* a cell's value rather than editing it, and
divergence happens only where a write lands. A checkpoint costs one cell per asserted cell. This is
`graph.py`'s immutability decision — *"load-bearing, not hygiene"* — paying for something it was not
adopted for, and it is what makes multi-turn hypothesis exploration affordable at all.

**Third finding: asserted and derived facts must wear one shape.** Once a derived claim is a reified
attribution, an asserted fact written as a plain attribute is no longer comparable with it, and a rule
would have to match both forms. The boundary must transcribe into the same shape rules conclude in.

Also pinned: overlaid values do not touch what they overlay and fade with their support; a derived
**edge** is powered identically; a detector wired to one hypothesis stays silent while the same detector
wired to both reports (the positive control that keeps the silence honest); blame walks back to exactly
the suppositions involved; a refutation dies with its hypothesis unless written back; and three-way
round-robin elimination across turns leaves exactly one survivor.

---

## 10. Open

Carried forward, plus what this revision raised.

- **Does the burn persist, or is it redone each revive?** (§4)
- **Attention leak from accumulated dangling gates**, and where decay goes without drifting off the goal (§5).
  Constrained by the trigger case: decay must not drop a standing prohibition, so it consults attention-holding
  facts rather than age alone
- **Does attention bound gate-matching** the way it bounds rule recall? A dangling gate wanting *a man* is a
  standing query against the twin, and the population of such gates now contributes to outer-loop work
  independently of the goal
- **Revive cost** as the circuit grows (§3) — the reshaped retention question, and the first thing to measure
- **Latched cycles after ungrounding.** `model.md` §5 says gates latch; if a cycle loses its external input,
  latched values could sustain it. §3 answers this for the revive case — nothing is latched across a revive —
  but not within a single stabilization run. Interacts with §13's standing question of whether in-circuit
  cycles are needed at all
- **The surge threshold**, and whether it is global or per-branch. The short-circuit analogy argues per-branch:
  a breaker is rated on the branch that faults, and does not watch total current and guess
- **How wide subset output forces the wiring.** §8 finding 1 settles that `0008` is right, but an emitted
  occurrence carries its filler *nodes* without their *attributes*, so a downstream unit that needs to read a
  name must be wired to where the name is. There is no ambient store to fall back on — which is the intended
  discipline, and also the number to watch: if most units end up wired back to the axiom cell, the pool has
  been re-created by convention
- **Dissolving `Cell` into the graph** (§9). The spike keeps cells as a separate Python type; under
  homoiconicity a derived fact should simply hang off its producing unit's node. This is the next
  simplification and it removes a kind
- **One shape for asserted and derived facts** (§9). Decides what the boundary transcribes into
- **Whether the old engine goes now.** The spike reproduces the six surviving harness rows with no
  `visible_at`, no `ScopePointer` and no `cooldown.py`. Deleting those is the payoff, and it reds most of the
  78 tests written against the superseded model

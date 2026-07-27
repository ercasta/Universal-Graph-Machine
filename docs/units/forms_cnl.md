# CNL — principles, criteria, and how to test them

**Status: specification, 2026-07-27.** The working document for shaping the CNL and turning it into something
that runs. Derived from `forms_discourse.md`, which carries the argument for every position taken here; where
this document states a rule, that one says why.

**How to use this.** §2 is the principles, numbered `P1`–`P10` so they can be cited in code and in review. §3–4
are the two decision procedures you will actually run. §5–6 are the formats. §8 is the test suite. Nothing here
is argued — if a rule looks wrong, the argument is in `forms_discourse.md` and that is where to attack it.

| | |
|---|---|
| **`forms_discourse.md`** | why any of this is believed; what was rejected |
| **`forms_llm.md`** | what may be asked of the translator, and what may not |
| **`cnl.md`** | the surface itself — brackets, roles, nesting. Still current; this document constrains it |
| **`model.md` / `revision-01` / `revision-02`** | the engine these forms run on |

---

## 1. The pipeline

```
prose ──[boundary: TRANSCRIBE]──► PROSE REGISTER        inert graph; cnl.md §5's closed list
                                        │
                            ┌───────────┴────────────┐
                            │  interpretation rules  │  ◄── A TURN OF THE ENGINE
                            │       in the loop      │      (model.md §10 step 0)
                            └───────────┬────────────┘
                                        ▼
                                 WIRING REGISTER        data: units, gates, wires
                                        │
                                  [ASSEMBLER]
                                        ▼
                          standing units + wires — the thing that runs
```

**⚠ There is no compiler, and this is a constraint rather than an observation.** `model.md` §11 pins both ends
out of the job: the assembler may not unroll a statement (the driver would be doing semantics on day one), and
the boundary may not either (choosing a chain is judgement). So the middle stage **is the engine running**. Any
design that introduces a CNL→graph *compiler* has violated this, whatever it is called.

**Three stages, three different obligations:**

| stage | may it decide anything? | fixed how |
|---|---|---|
| **transcribe** | **No.** Mechanical, `cnl.md` §5's closed list, exhaustive | designed; `T8` |
| **interpret** | **Yes — this is where all judgement lives.** Force, reference, applicability, scope | rules, i.e. data |
| **assemble** | **No.** Wires only what the wiring register describes; never sees a statement | designed; tier 0 |

---

## 2. The principles

### ⚠ P1 is under measurement — read §11 first

`units/sieve.py` probes the axis space rather than assuming it, and the seed of seven forms already
splits `CONTENT` in two on evidence. The principles below are stated as they were designed; **§11
records what running them produced**, and P1 and P8 are the two that did not survive intact.

### P1 · Categories are a product, not a list

A "category" is a point in **CONTENT × FORCE × LEVEL**, never an entry in an enumeration.

- **CONTENT** — what is claimed (degree, negation, conditionality, identity, quantity, time, cause)
- **FORCE** — what is being done with it (assert, deny, ask, command, author, retract)
- **LEVEL** — what it is about (the world, the theory, the language)

They are orthogonal: any content carries any force at any level. **Three axes enumerate the sum; one list would
have to enumerate the product.**

> **Never add a kind.** A needed distinction becomes a *fact a rule concludes*, never a new sort of thing
> (`model.md` §11, *guards yes, kinds no*). There is no question-kind, no rule-kind, no procedure-kind.

### P2 · The closed class is held exactly; the open class opaquely

And the boundary between them is **a factorization of every lexeme, not a partition of the vocabulary**. *near*
contributes a gradable binary spatial relation (closed) **and** an unbounded notion of how-near (open); *park*
contributes argument structure and accomplishment aspect (closed) **and** whatever distinguishes it from *stop*
(open).

> An open-class lexeme enters the graph as **an opaque name plus a link to closed-class structure**. The engine
> never needs to know what a car is.

### P3 · Meaning is state change

A form is specified by **what it does to the information state**. This makes surface-independence checkable:

> **Two surfaces express the same form iff they effect the same state change.** Not iff they transcribe to the
> same graph — they will not, and must not be expected to.

### P4 · Normalization lives in the interpretation rules, never in the transcriber

`cnl.md` §5's transcription is structure-preserving, not normalizing. Two paraphrases land as different graphs
and **rules** conclude the same thing from both.

> A transcriber that normalizes is Python, therefore **unlearnable**. A rule that normalizes is data, therefore
> a new surface variant is a new rule — and the system can learn a paraphrase.

### P5 · Interpretation is a turn of the engine

See §1. Comprehension is ordinary reasoning; what it produces is the wiring.

### P6 · Mark the carrier; let a rule decide the reading

The boundary may mark a closed-class **carrier**. It may not mark a **conclusion**.

```
g0: [ get | agent: Paul | patient: the loyalty discount | modality: should ]
```

`modality: should` is a carrier — transcribed, not interpreted. Whether it is deontic or epistemic, and whether
the utterance asks, are rules' conclusions. Likewise `when:` marks a conditional carrier while *being a rule*
stays a conclusion.

**Where English has no carrier** (bare generics, scope ambiguity), there is a third move that is neither
deciding nor dropping: **mark the ambiguity explicitly**. *"This is one of these two"* keeps the information
recoverable without the boundary deciding anything — and `ask, never pick` then applies.

### P7 · Utterance-specific → boundary. Lexeme-invariant → lexicon

| | goes | why |
|---|---|---|
| force carrier, negation, scope, degree, coindexing, which role a filler fills, an unresolved ambiguity | **marked at the boundary** | exists only in this utterance; drop it and it is unrecoverable |
| aspect class, argument structure, intro/elim pair | **looked up in a lexicon** | identical for every use; per-utterance marking is redundant **and lets the translator contradict itself between utterances** |

The lexicon is CNL data like everything else. Nothing hides in Python.

### P8 · Every form ships a matched intro/elim pair

**Harmony.** Introduction = what licenses writing it = *a unit*. Elimination = what may be read from it =
*a unit*.

- introduction without elimination → the form is **inert**;
- elimination outrunning introduction → the form **leaks**.

> **A form with only one of the two is not a form.** This is a local, per-form check that buys global closure —
> the only reason a ~50-form set (= 1,225 pairs, unbounded nestings) is tractable at all.

### P9 · When in doubt, closed

The error is asymmetric:

| | consequence |
|---|---|
| **too closed** | engine grows, gets brittle, coverage wall. **Visible, recoverable** |
| **too open** | **silent mis-mapping** — reports success, represents nothing. **Unrecoverable** |

Same shape as *guards yes, kinds no*. Minimality and composability are in tension and **composability wins**;
closure may legitimately force the set larger.

### P10 · Every mark must be refusable

Each mark is a place the translator can be silently wrong, so marking trades *unrecoverable loss* for *silent
mis-marking*. The mitigation is not accuracy, it is **refusability**: a mark answerable as `ambiguous` or
`cannot-express` turns a silent mis-map into a reportable one.

> **Mark only what is genuinely unrecoverable, and make every mark refusable.**

---

## 3. Criterion A — is this closed class?

Run all three. **They should agree; disagreement is a signal to probe, not to pick.**

| # | test | closed if |
|---|---|---|
| **A1 · composition** | *Does anything else's meaning depend on this?* | **yes.** Operators must be closed; operands may be open. Negation is closed because negation *over X* changes what X commits you to. *Car* is open because nothing depends on what a car is |
| **A2 · learnability** | *Can it be verified by desugaring into existing forms?* | **no.** A baroque form is learnable because you can check it against the core form; a fundamental one has no target to check against, so it must be designed in |
| **A3 · harmony** | *Does something follow from it that does not follow from its parts?* | **yes.** Trivial elimination means open class |

**The underlying test, from which A2 derives:** *can it be paraphrased without changing what the system
believes?* Yes → baroque, desugar it. No → fundamental, represent it. Losing **detail** is attenuation and keeps
it baroque; changing **epistemic status** means it was fundamental and the paraphrase was a lie.

⚠ **Classify by probe, never by intuition.** The prior effort was **wrong five times out of five** on candidates
it could have measured. Both directions occur: things that look fundamental turn out baroque, and the cheap
baroque-shaped fix for a genuinely epistemic distinction produces confident garbage.

---

## 4. Criterion B — does it go at the boundary?

### 4.1 The gate

**Never mark a conclusion** (P6). The translator being *capable* of deciding force is not a reason to let it —
`model.md` §9 stands regardless of how good the translator gets.

### 4.2 The test

> **Would two uses of this word ever differ in this respect?**
>
> **No** → lexicon (P7). **Yes** → boundary.

### 4.3 The cost, so it is not paid absentmindedly

Naturalness is **not** the price — `cnl.md` §5 already traded that away (*"verbose and unpleasant to read, which
is acceptable because a human is not the author"*). The real costs:

1. **Auditability** — role-slotted CNL is hard for a human to review. A prose renderer is the mitigation and is
   **undesigned**.
2. **Silent mis-marking** — more marks, more surface for the unrecoverable failure. Hence P10.

---

## 5. The form entry format

Every entry in the inventory carries these nine fields.

| field | meaning |
|---|---|
| **name** | |
| **axis** | content / force / level |
| **commits** | what believing it commits the system to |
| **introduction** | what licenses writing it — **which unit** |
| **elimination** | what may be read from it — **which unit** |
| **state change** | what it does to the information state (P3) |
| **surface carrier** | **marked** at the boundary / **looked up** in the lexicon / **concluded** by a rule. If marked: is the mark refusable? |
| **known compositions** | verified pairs, and known leaks |
| **status** | built / designed / gap |

**Two mechanical checks fall out of the format:**

- an entry missing **introduction** or **elimination** is not an entry (P8);
- every form whose carrier is **marked** must have a role in tier 1 or 2 to carry it — a form needing a mark
  with no role to carry it means the role inventory is incomplete (`T5`).

⚠ **The format is designed, not validated.** The test is writing ten real entries and seeing which field is
always empty or always fudged. Do this **before** tier 3.

---

## 6. The role inventory, tiered

`cnl.md` §2 settled that **roles are a closed class and content vocabulary is open** — on measured evidence,
twice: retrieval stopped discriminating once `"agent"` entered every pattern's vocabulary, and a
same-name coreference rule fused every role node called `"agent"` and nearly ate the graph. **Role names behave
as a shared vocabulary whether or not one is declared**, so declaring and bounding it is strictly better.

It ships as a flat list of ten. It is **four tiers**, with different consumers and different stability:

| tier | roles | consumer | may grow? | method |
|---|---|---|---|---|
| **0 · wiring** | `pattern:` `gate:` `out:` `from:` `to:` | the **assembler** | no | **designed a priori** — there is no corpus of wirings, and the bootstrap depends on it |
| **1 · structural** | `content:` `member:` `of:` | interpretation rules | no | designed, validated against what those rules need |
| **2 · logical** | `when:` `then:` | interpretation rules | no | designed |
| **3 · thematic** | `agent:` `patient:` `destination:` `time:` `means:` | domain rules | **the only tier that could** | **corpus-derived** — residue log; raid AMR / FrameNet / PropBank rather than inventing |

⚠ **Containment runs container → contained.** Not taste: a pattern atom has `out` and no backward traversal, so
*"find something containing both of these"* is only expressible if the container is the source
(`units/graph.py::contains`).

⚠ **A translator emitting a role outside the set must refuse, never invent** (P10).

---

## 7. The translation contract

Four outcomes, exhaustive. **Anything else appearing in a translator is a defect.**

| outcome | when | what it means |
|---|---|---|
| **CNL** | complete capture | understood |
| **CNL + RESIDUE** | attenuated — emit, and **record what was dropped** | partially understood, and *which* part is known |
| **CANNOT-EXPRESS** | capturing anything would distort | not understood, and *why* is known |
| **NOTHING-TO-ASSERT** | the source asserts nothing | nothing to understand |

Plus, from P6: **ambiguous** → emit the alternatives, and *ask, never pick*.

**⚠ Attenuation must never be silent, and the reason is not bookkeeping.** Attenuation is safe for deduction —
the KB merely knows less. It is **not safe for induction**: dropping a counterexample lets a learner generalize
with its only refutation removed. **To a learner, absence looks like confirmation.** The residue is evidence the
learner needs, not a to-do list.

**And the residue log is how the closed class grows** (P9's revision path): a form is promoted when the log
shows it carrying weight the translator keeps dropping. The signal is real — a missing form does not lose
content at random, it loses the **marked** cases, which are disproportionately the exceptions.

### Understanding, operationally

> **X is understood iff its CONTENT maps onto held forms, unambiguously and status-preservingly, AND its FORCE
> is recognised.**

Both qualifiers are load-bearing. **Unambiguous** makes a two-reading parse *not-yet-understood*.
**Status-preserving** makes a distorting paraphrase a failure to understand rather than a lossy success. And
force alone can sink it: map *"is the lion dangerous?"* to its proposition perfectly, then assert it — every
content check passes and the utterance has been comprehensively misunderstood.

---

## 8. How to test

The suite that makes the principles enforceable rather than aspirational. **`T1`–`T3` are the ones that catch
the failures this design actually has.**

| # | test | enforces | how | status |
|---|---|---|---|---|
| **T1** | **Harmony, per form.** Assert via the introduction unit; read via the elimination unit; assert that **nothing beyond what introduction established is derivable** | P8 | per-entry probe | buildable now |
| **T2** | **Surface independence.** Two surfaces of one form → **same readable state**, not same graph | P3, P4 | `engine.readable()` on both, compare | buildable now |
| **T3** | **Pairwise closure.** For each pair of forms: assert the composite, ask a query that **cannot be answered without reasoning over both**, classify **PASS / REFUSED / LEAK**. Refusal is closed and fine. **LEAK never is** | P8, P9 | port of the epistemic-closure spike | buildable now |
| **T4** | **Depth closure.** `T3` at depth ≥ 3 — pairwise closure does **not** imply depth-*n* closure | P8 | as `T3`, nested | ⚠ **blocked** — see §9 |
| **T5** | **Carrier completeness.** Every form whose carrier is *marked* has a tier-1/2 role to carry it | §5 | walk the inventory | buildable now |
| **T6** | **Idempotency.** The same surface ingested twice routes identically | levels | round-trip | buildable now |
| **T7** | **Refusal.** A role outside the inventory is **refused, not invented**; an ambiguous surface yields alternatives, not a pick | P10 | adversarial surfaces | buildable now |
| **T8** | **Boundary purity.** Transcription is a **pure function of the surface** — no KB access, no rule firing, nothing outside `cnl.md` §5's list | §1, P6 | mechanical: transcribe with an empty KB and with a full one, compare | buildable now |
| **T9** | **Machinery isolation.** ~~A pattern that does not name machinery never matches machinery~~ → **machinery is unreachable unless something wires it** | homoiconicity | ~~invariant 19~~ `model.md` §5 | ⚠ **run, and invariant 19 FAILED** — restated; see §9 |
| **T10** | **Order independence.** Graph state is a pure function of (axioms, wiring) | invariant 15 | two revives, compare `readable()` | exists (`test_engine.py`) |

**Two discipline notes.** A trace that confirms the hypothesis is the one to distrust — **run a negative control
for every PASS** (drop the premise; it must fail). And **closure is the gating half, not a validation step**:
a representation that cannot compose is the wrong representation even if it covers its concept perfectly alone.

---

## 9. Build order

**1 · Tier 0 — the wiring register.** ✅ **BUILT, 2026-07-27** — `units/engine.py`, 52 green. Everything else
is downstream.

*Was:* the assembler had nothing to read and nowhere to write. Wiring was `self.wires: list` of Python tuples,
nothing read topology from the graph, and every test wired by calling `Network.wire(...)` — so **the front
end's target was an engine API**, the one thing `model.md` §11 forbids.

*Is:* a wire is a `<wire>` occurrence with `from:` `to:` `gate:` role nodes; `Network.wires` is **derived** by
`assemble()` matching an ordinary pattern over `self.asserted`; `wire()` writes that fact and nothing else.
Pinned: a circuit wired **by writing graph data alone**, a wire **concluded by a mutating rule** (invariant 4
cashed), removing the fact un-wiring the circuit, and a second `Network` assembling the same circuit from the
graph. **`pattern:` is the one tier-0 role still unbuilt** — a unit's pattern and effects are still Python, so
the assembler is handed unit objects and resolves them by node.

**It self-tested, and three things fell out** — all invisible until the bundled rule could actually fire:

1. **`bundled_silence_rule` had never fired.** Its pattern was `surged=None`, and `attr` answers `None` for an
   attribute that is **absent** — so it matched every node *except* its target. The matcher has no
   *"present, any value"* atom; `AttrVar` **is** one, because it fails when the attribute is missing.
2. **A report written only into the read layer reaches no rule.** A unit sees only its gates
   (invariant 3), so `surged` appearing in `graph()` was unreachable whatever the pattern said. The report is
   now a **cell** (`Network.reports`) and travels on a wire like every other value. This is §9's *plane
   interface* question answered: the crossing is where every other value already crosses.
3. **The corrector burned itself.** The report accumulates, so each surge after the first was a *change* on the
   corrector's one gate, and at `SURGE_AT` the detector burned the corrector — leaving the last loop
   uncorrected. That is counting **growth** as cycling. `rev-02` §6's own monotonicity theorem says growth is
   not evidence of a cycle; applying it to the value on the wire is the fix. The price is that
   monotone-but-infinite is now squarely fuel's job, which `rev-02` §9 already says it is.

⚠ **`T9` was re-run against the known leak, and it leaks — invariant 19 is false as written.** *"A pattern
that does not name machinery never matches machinery"* does not hold: a wire occurrence has an outgoing edge
like anything else, so a **generic structural** pattern (*anything with an outgoing edge* — the exact shape
that once derived `produces is meta`) matches it without naming anything. What holds is weaker and more
useful: **machinery has to be delivered to a gate before any pattern can see it**, and delivering it is a
deliberate act. So the barrier is `model.md` §5, not invariant 7. Recorded rather than patched — a partition
is what `rev-02` §5 rejected, and the mechanism `rev-02` §9 nominates here is attention.

**2 · The surge detector.** Measured 2026-07-27: a self-looped narrowing unit over an inert nested description
resolves **correctly at depth 4 and is still burned as a runaway loop**; at depth ≥ 5 it is **silently partial**.
The detector cannot distinguish converging recursion over a finite description from a runaway cycle, and raising
`SURGE_AT` only moves the depth at which comprehension breaks. **This blocks `T4` and it blocks any description
deeper than three narrowing steps** — *"the red car parked at the third floor of the garage near the movie"* is
four.

**3 · Tiers 1–2**, validated against what the bundled interpretation rules actually need.

**4 · Ten real entries** in §5's format, to validate the format before it is used at scale.

**5 · Tier 3**, corpus-derived, on the residue log.

---

## 10. Undecided

- **Activity structure.** The three axes classify an *utterance*. Multi-turn shapes — a plan under execution, a
  hypothesis under **verification**, a goal pursued across turns — have no entry. (Hypothesis *formulation* is
  settled: supposition is the conditional's introduction rule, not a force.)
- **Reference and identity.** No entry, and `rev-02` §4's cardinality discipline is wrong at both ends: 0 matches
  is `starved`, not reference failure (nothing-matched never means not-derivable); and *n* matches counts
  **nodes** where reference needs **things** — under create-never-merge those diverge exactly while resolving.
  The available construct is counting **equivalence classes under the union-find**, not match rows.
- **Tier 3's contents.** Deferred to the residue log; nothing logged against the new model yet.
- **Is the entry format sufficient?** §5's ⚠.
- **How many forms is it, actually?** *The closed class is small* is inherited, not measured — and §11
  now shows the count is not designable at all: the sum of the axis inventories is a **floor**, the
  product a **ceiling**, and the true number is the sum plus however many *interactions* need their own
  entry. Interactions are discovered, not predicted.
- **Who decided three axes?** Nobody: `forms_discourse` §12 carries them over as *"the single most
  durable result"*, and the argument actually made is for **orthogonality**, never for completeness.
  Measured, the seed gives **four** slots (§11).
- **A prose renderer**, for auditability (§4.3). Needed, unspecified.
- **A grammar for the CNL itself.** The surface is regular enough to parse trivially — which is the point, and
  *trivially* should be demonstrated rather than asserted.


---

## 11. What the sieve measured

**`units/forms.py` + `units/sieve.py`, 2026-07-27. 19 tests, every finding mutation-checked.** Seven
seed forms written as executable entries — `introduce` / `eliminate` / `commits` — swept over every
combination and classified. No prose and no CNL surface: the translator is not under test, so every form
decorates one **claim occurrence**, and the content is an opaque predicate (`P2` — the open class is not
under test either).

**The oracle needs no ground truth**, which is what makes this automatable: a form declares what must
never be concluded, and a leak is that happening.

### The three results

**1 · The declared axes are not the measured ones.** Two forms occupy one slot iff they **exclude** each
other — the standard derivation in feature theory, and the only evidence available about how many axes
there are. The seed gives **four slots against three declared axes**: `CONTENT` splits into *polarity*
(positive ⊕ negation, which exclude) and *strength* (degree, which combines with both).

> ⚠ **And the declared assignment actively prevents the cells from being built.** Framing a cell by
> declared axis treats a graded claim as already having its `content` axis filled, so it never receives a
> polarity — and any elimination that consults polarity is handed nothing to read. The probe only works
> when it frames by **measured slot**. That is the sharpest single piece of evidence that `content` is
> not one axis.

**2 · Local harmony buys nothing here.** `forms_discourse` §4.2's tractability argument is that checking
~50 intro/elim pairs covers 1,225 compositions. Measured:

| | leaks | passes |
|---|---|---|
| **naive** eliminations — each written thinking only about its own form | **13 of 20 cells (65%)**; over pairs that can co-occur, **53%** | 0 |
| **guarded** — every elimination rewritten to consult its neighbours | 0 | **0** |
| **guarded + one pair entry** | 0 | **1** |

> ⚠ **Guarding removes every leak and composes nothing.** It converts a leak into an **inert** composite
> — `P8`'s other failure. *"Not very dangerous"* stops asserting the predicate and starts meaning
> exactly *"not dangerous"*: the band is dropped rather than carried. Silence is not closure.

What actually composed it was an entry for the **pair** — and one pair entry bought exactly one cell,
with nothing generalizing to the others. That is the O(n²) the local check was supposed to make
unnecessary, and it is the answer to *sum or product*: **the sum is a floor, the product a ceiling, and
the real count is the sum plus the interactions that need their own entry.**

**3 · The entry format does not survive contact, in two places.**

- **`commits` is one field doing two opposite jobs.** `P8` already distinguishes them — elimination
  outrunning introduction (**leaks**) and introduction without elimination (**inert**) — but a single
  predicate cannot report which, so the classifier cannot tell a form that leaked from one that
  correctly went quiet. It has to be split into `commits` (must hold) and `forbids` (must not).
- **A commitment cannot be stated in its own axis's terms.** `positive` commits you to the predicate only
  when *asserted* at the *world* level; `degree` has to name force, level **and** polarity. If the axes
  were orthogonal this count would be zero. The composability problem is in the **specification**, not
  only in the implementation.

### What this cannot do, stated up front

It explores the space **as parameterized**. It can *split* a declared axis, because refusal is evidence;
it can never discover a form or an axis nobody wrote down. The consolation is Mendeleev-shaped and weak
— `geometry()` reports where failures sit, and clustering the slots do not explain would be a hint.

⚠ **Two limits on the seed itself.** Seven forms is small, and the eliminations are hand-written by one
author who knew what was being measured — the naive ones are naive *on purpose*, as the realistic
failure mode. The guarded/naive/pair-entry comparison is the result; no single column is.

⚠ **The `degree ∘ negation` leak reproduces**, and this was the control: it was measured on the retired
`ugm` engine with mechanisms that no longer exist, so it was a phenomenon to re-probe rather than a bug
to reproduce. It is still there, and it is worse than it was recorded — the graph holds the claim **and**
its denial at once.

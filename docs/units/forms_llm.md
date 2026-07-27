# Forms and LLMs — what the closed/open split predicts, and what may be asked of the translator

**Status: design, 2026-07-27.** Split out of `forms_discourse.md` §3.5, which it expands. Read
`forms_discourse.md` §3 first for the closed/open split itself; this document only asks *what that split implies
about the component sitting at the boundary*.

**⚠ What this document does not claim.** It offers **no theory of why LLMs do what they do**. That is not
settled, and nothing here depends on it. What is claimed is narrower: a split, a prediction about where the
failures fall, and — the load-bearing part — an argument about **how** they fail that survives whether or not
the mechanism story is right.

---

## 1. The claim under test

> *"Could it be that these base concepts are just the dimensions of embeddings, and this explains why LLMs
> appear to reason?"* — you, 2026-07-27

Two questions in one, with different answers: a **representational** one (do LLMs hold the closed class?) and a
**mechanistic** one (why do they fail where they fail?). §2–3 take the first, §4–6 the second.

---

## 2. Dimensions: false, for three settled reasons

1. **Concepts are directions, not dimensions.** The basis is arbitrary; nothing privileges the coordinate axes.
2. **Superposition.** Networks represent far more features than they have dimensions, in near-orthogonal
   directions — so there is no dimension-to-concept correspondence even in principle.
3. **The counts are off by orders of magnitude, in both directions.** A base-concept catalog is ~14 (Schank) to
   ~65 (NSM). An embedding has 10³–10⁴ dimensions and, under superposition, far more features — and the features
   recovered are a long tail of specific detectors (*"DNA sequences"*, *"the Golden Gate Bridge"*), not a
   compositional basis.

---

## 3. Directions, and the closed class specifically: probably true

**⚠ This corrects an earlier position.** A first draft of `forms_discourse.md` §3.5 said embeddings are simply
*bad at* the closed class. That is wrong, and it made the architecture rest on a deficiency claim that scaling
could erase.

The evidence points the other way:

- **structural probes** recover dependency parse trees from transformer representations by a **linear**
  transformation — syntactic structure living in a linear subspace;
- part of speech, number, tense, gender and definiteness are linearly decodable from contextual embeddings;
- sparse-autoencoder work finds structural features (syntax, quotation, code constructs) alongside content ones;
- and the **functional argument** is strong on its own: if the closed class governs how everything else composes,
  a model optimized for next-token prediction **must** encode it, because getting scope or tense wrong is
  expensive in loss.

⚠ **Methodological caveat, standard and load-bearing:** a probe finding information shows it is *decodable*, not
that the model *uses* it. Causal interventions are the better evidence and are more mixed than the probing
literature alone suggests.

**So: the closed class is almost certainly present.** Which relocates the entire question.

---

## 4. ⭐ Encoding is not composing

> A thermometer encodes temperature. It does not do thermodynamics.

A direction that *represents* negation is not a mechanism that *applies* negation correctly under scope, at
depth, through a chain. Three reasons the gap survives good directions:

| | |
|---|---|
| **1. A direction has no intro/elim structure** | It is an **association, not a rule**. There is nothing to check for harmony (`forms_discourse.md` §4.2), so nothing prevents the elimination outrunning the introduction — which is what a scope error *is* |
| **2. Superposition means it is not a clean symbol** | Directions interfere and shift with context, so approximately-negation composed with approximately-quantification degrades **multiplicatively** |
| **3. No inspection, no statement, no repair** | A direction cannot say what it commits to, and cannot be corrected when wrong |

**This predicts the observed profile exactly.** LLMs recognise negation fine and fail at *composing* it — nested
negation, negation interacting with quantifiers, negation surviving a long chain. Long chains, counting,
quantifier nesting, tracking who committed to what. **That is not a random failure list; it is the closed class,
failing under composition rather than under recognition.**

---

## 5. The depth hypothesis

> *"Is it possible that LLMs learned to perform approximate operations on the approximate representation of
> directions, and fail because their operations can only have a finite depth and some situations require them to
> go just over what they can perform?"* — you, 2026-07-27

**Substantially right, and for the no-chain-of-thought case it is provable.**

A transformer with *L* layers performs at most **L sequential steps** per forward pass. That is architectural,
not a training deficiency. The theory work here (Merrill & Sabharwal; Hahn; Chiang) places fixed transformers
without CoT in a constant-depth circuit class, roughly **TC⁰** — so there are problems a fixed transformer
*cannot* solve in one pass however well trained.

**The strongest evidence is that chain-of-thought helps at all.** CoT converts serial depth into sequence
length: computation that will not fit in the layer stack is spread across tokens. If the failures were purely
representational, writing out the steps would not help. It does.

---

## 6. Two failure modes, separable, with an empirical discriminator

§4 and §5 are **different** hypotheses, and they predict different curves:

| | mechanism | signature | fixable by scale? |
|---|---|---|---|
| **depth-bound** | the operation is correct; you run out of steps | near-perfect below threshold, **collapse above it** — a cliff | **yes** — more layers, or CoT |
| **approximation** | every step is approximate; errors compound | **smooth decay** with depth, no cliff | no |

**This is measurable**, and the measurement is worth having because the two license different conclusions. My
read is that observed degradation looks more like smooth decay than a cliff, which would mean both are operating
with compounding approximation the more stubborn one — **but I am not confident, and it should be measured
rather than asserted.**

---

## 7. ⭐ The decisive point: it does not matter which, because both fail *silently*

Suppose the depth hypothesis is entirely right, and CoT plus more layers closes the gap. **That still does not
supply what the engine supplies**, because of *how* the failure presents:

> **A depth-bound failure is silent.** The model does not know it ran out of depth. It emits a confident answer.

That is precisely the conflation `model.md` §8 exists to prevent — a **budget exhaustion reported as an answer**.
The four outcomes (`satisfied` / `starved` / `out_of_fuel` / `awaiting` / `surged`) exist so that *"I couldn't
work it out"* never collapses into *"no."*

And §8 already draws the analogy one level up:

> *"The reason the API grew distinct stop reasons (`end_turn`, `max_tokens`, `pause_turn`, `refusal`) is
> precisely that finished, truncated, paused and declined need to be told apart. A loop that tests only 'no tool
> call' silently conflates all four."*

**The depth hypothesis is that same lesson one level down, inside the forward pass.** A transformer running out
of layers is `max_tokens` with no way to report it.

| | depth | on exhaustion |
|---|---|---|
| transformer | **fixed** | **silent** — a confident wrong answer |
| this engine | **unbounded** (a cycle iterates) | **budgeted and reported** — a positive fact something can be wired to |

**This is a better justification for the architecture than deficiency**, because it does not depend on LLMs being
weak in a way they might stop being. Scaling can improve the approximation and add depth. **It cannot turn an
association into a rule with a matched elimination, and it cannot make a silent exhaustion announce itself.**

The engine is therefore not supplying missing *concepts* — the model probably has them. It supplies an
**evaluation discipline**: exact composition, statable commitments, reported exhaustion, and a harmony check that
makes leaks impossible rather than unlikely.

---

## 8. ⚠ The same failure, in our own house

`forms_discourse.md` §10.3, **measured 2026-07-27**: one self-looped narrowing unit over an inert nested
description resolves correctly at depth 4 and is **still burned as a runaway loop**; at depth ≥ 5 it returns a
**silently partial** answer.

So **the engine has a depth limit too** (`SURGE_AT = 3`). The difference is meant to be that ours *reports* it.
Except it reports it wrongly: the surge detector cannot distinguish converging recursion over a finite
description from a runaway cycle, and the depth-≥5 case is exactly the silent-partial-answer failure this
document just credited the engine with avoiding.

**Honest scoreboard:** the *architecture* has the right shape — arbitrary depth, budgeted, reported. The
*current build* leaks in the same way it criticises. That is a sharper statement of why the surge-detector fix
belongs in the queue alongside tier 0, and it should not be softened.

---

## 9. What the translator may therefore be asked to do

If the closed class is genuinely encoded (§3), the boundary gets **two capabilities it would otherwise have to
assume**:

1. **Closed-class judgements are askable.** *"Is this a conditional?"*, *"what is negated here?"*, *"which role
   does this filler fill?"*, *"is this generic or referential?"* are closed-class questions, and the evidence
   says the model can answer them. This is what makes `forms_cnl.md`'s **mark the carrier** discipline viable
   rather than hopeful.
2. **Refusal is meaningful.** `cnl.md` §1 requires the translator be able to refuse. A model can be asked to
   refuse *when unsure* precisely because it has a representation to be unsure about — which is what turns the
   four-outcome contract from a wish into a mechanism.

⚠ **And the corresponding limit.** Both capabilities are *approximate and unguaranteed*. So every mark the
translator makes is a place it can be silently wrong (`forms_cnl.md` §4.3), and the mitigation is not accuracy
but **refusability**: a mark that can be answered *ambiguous* or *cannot-express* converts a silent mis-map into
a reportable one.

---

## 10. Testable predictions

Recorded so this document can be wrong.

| prediction | what it tests | status |
|---|---|---|
| **Closed-class directions align across languages more than open-class ones** in a multilingual model | `forms_discourse.md` §3.6's **level 2** — that the closed class draws from a small, cross-linguistically recurrent pool. **This claim currently carries the argument that the closed class is small enough to design.** If closed-class directions do *not* align cross-lingually, level 2 is in trouble | **unverified — worth actually checking**, not filing as a lead |
| **Degradation with composition depth is a cliff, not a slope** | §6 — depth-bound vs approximation | unmeasured |
| **CoT closes composition failures but not scope failures** | §4 vs §5 — if CoT fixes everything, approximation is not the issue | unmeasured |

---

## 11. What this does **not** license

- **Not** *"LLMs cannot reason."* They compose approximately, without guarantee, and without reporting
  exhaustion. That is a different and more precise claim.
- **Not** *"the engine is needed because LLMs are weak."* §7 — the argument is about **discipline and
  reporting**, and survives arbitrary improvement in LLM capability.
- **Not** a mechanistic account. §6's discriminator is unmeasured; §5's theory results bound the no-CoT case and
  say much less about the practical one.
- **Not** grounds for the boundary to interpret. `model.md` §9 stands regardless of how good the translator is:
  the translator being *able* to decide force is not a reason to let it (`forms_cnl.md` §4.1).

---

## 12. Confidence

**Would stake:** the dimensions/directions distinction and superposition; linear decodability of grammatical
features; structural probes recovering parse structure; the probing-vs-causality caveat; bounded serial depth per
forward pass; CoT converting depth into sequence length.

**Would not stake without checking:** the exact complexity-class results and their authors (§5); the
cross-lingual alignment claim (§10) — **and that one is load-bearing**, so it should be checked rather than
cited; the shape of observed degradation curves (§6).

⚠ Same discipline as `form_inventory` §6: this is recall, not verified citation. Treat every name as a search
query.

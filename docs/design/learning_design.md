# Learning — rules and forms from ingestion, observation, and discrepancy

> **Status: DESIGNED, NOT BUILT (2026-07-18). Empirical base: `bench/spike_rule_learning.py`
> (runnable; prints its findings). The spike establishes that a rule CAN write a rule the
> engine then runs — L3 learns `?x flies yes when ?x is_a bird` from two observations and L4
> fires it on an entity never observed flying. One primitive is missing (§4) and one encoding
> field is absent (§6.2); everything else composes from parts already built.**
>
> Vision §2 promised that homoiconicity makes "self-modification and learning ordinary graph
> rewriting rather than a special subsystem". This design cashes that cheque and finds the
> promise essentially correct — with one substrate fact (predicates are keys, not nodes) standing
> in the way, and one licensing question (what makes a learned rule believable) that the
> possibilistic layer and the reconsider arc already answer between them.

## 1. What "learning" means here

Three loops, one mechanism. Each is triggered by a signal that ALREADY EXISTS AS A FACT:

| loop | trigger | learns | status of trigger |
|---|---|---|---|
| **rule learning** | `discrepancy` (`corpus/procedure.cnl:40`) | a domain rule | fact today |
| **rule revision** | `broken_assumption` (reconsider arc) | retract/replace a learned rule | fact today |
| **form learning** ("Caveman CNL") | recognition failure + the user's REPHRASING | a `form KEY :` recognition form | **computed but stranded** (§7.1) |

Not in scope as "learning": statistical parameter fitting. The PCFG/EM path was rejected in
vision §10 and stays rejected — see §6 for what replaces counting.

## 2. What the spike established (the empirical base)

Run `python bench/spike_rule_learning.py`. Findings, in the order they bind the design:

- **L0 — the landing pad exists.** Rules are graph data in the same graph as the facts
  (one-graph fold), and lift-and-run works. A learned rule needs no separate bank, and
  `intake.py:451` (`rules.extend(new_rules)`, behind a stratification-conflict accept) is
  already the place mid-session rules enter.
- **L1 — pattern variables are free.** A control node NAMED `?x`, reached by a `pat_var`
  marker, is bindable by a rule. The learner refers to a pattern variable without ever writing
  `?x` as a token (which the engine would read as a variable, not a name).
- **L2 — the fact-shaped reification is a WALL.** See §3.
- **L3 — the flat reification works.** A learner rule wrote rule structure; `expand_rules`
  lifted it into an executable `Rule`.
- **L4 — the loop closes.** The learned rule derived `robin flies`, never observed.
- **L5 — one primitive is missing.** See §4.

Two incidental findings worth keeping:

- **Anchored skolems mint per match** (distinct node ids per firing, verified by id — the
  `derived_triples` NAME view renders them identically, which is a readability trap when
  debugging a learner, not a correctness one). One learner therefore emits many rules.
- **`add_node` always mints.** Calling it twice for `"bird"` makes two distinct nodes and a
  literal pattern then matches only one. This bit the spike twice. Any learner that writes
  token nodes MUST intern them (§5.3) or learned rules will silently fail to match.

## 3. Decision: learn into the FLAT reification

There are two rule reifications in the repo. They differ exactly on whether an RHS can write them.

**A. Fact-shaped** — `rule_graph.write_rule` / `rules_in_graph`. A pattern atom is the 2-hop
path `subj --> [rel node keyed by pred] --> obj`, and the role edge points at the MIDDLE node.
This is the more beautiful encoding (the rule is literally in the shape of the facts it
rewrites) and it is **not learner-writable**: an RHS has no way to NAME the relation node it
creates, so it cannot wire `rule --lhs--> thatRelNode`. The spike's L2 confirms both halves —
the RHS *can* write the role edge, and the result is unreadable.

**B. Flat** — `authoring.expand_rules`, the CNL fold's own schema. A pattern atom is a `<cond>`
node with three ordinary edges `k_subj` / `k_pred` / `k_obj`. Learner-writable, because
`<cond>` is a nameable skolem and each edge is a plain triple.

**DECISION: learning targets (B).** Consequences, both good:

1. It sidesteps the RHS variable-predicate deferral (`Unlowerable: RHS non-plain predicate …
   is a later slice`) entirely, because in (B) the learned predicate sits in an **object**
   position (`<cond> k_pred TOK`), never a predicate position. No engine change needed for it.
2. Learning and CNL authoring converge on ONE target schema. A learned rule and an authored
   rule are the same structure, so `stratify`, `active_rules`, disable, provenance, and
   explanation all apply to learned rules with no special-casing — the "no privileged
   partitions" discipline holds by construction.

(A) is not deprecated by this; it stays the homoiconic showcase and the one-graph parity
subject. But it is not the learning target.

## 4. THE MISSING PRIMITIVE — predicate reification

**The fact.** A predicate is a graded KEY on a relation node
(`{'is_a': Attr(kind='graded', value=1.0)}`), not a node. `nodes_named('is_a')` is empty. This
is deliberate — the `name` dual-write was retired in the name-demotion work, and predicates
became keys so that predicate identity is a key-presence seed/test (`lowering.py:150–170`).

**The consequence.** A learner has nothing to point `k_pred` at for a predicate it OBSERVED.
The spike's L3 learner had to PRE-INTERN a node per predicate, which makes it a learner only
over a vocabulary fixed at authoring time — i.e. not a learner.

**The requirement.** From a matched relation node, obtain a nameable, INTERNED token node whose
name is that relation's predicate.

### Options

**A. Store it — an edge per relation.** On `add_relation`, also wire
`relnode --pred_of--> [interned control node named p]`. Learner matches it directly. Simple,
matcher unchanged. Cost: +1 node-and-edge per fact, on the hot path, forever — for a capability
used by a handful of learner rules. Rejected on cost.

**B. Compute it — a calculator.** A `<call>` calculator `pred_tok` that takes **an ENTITY** and
interns a token for each predicate that entity participates in, minting on first demand.
**RECOMMENDED — and validated by spike (`bench/spike_predicate_reification.py`), which also
CORRECTED this section's original signature: see §4.1.**
Rationale:
- It is in the grain: "capabilities/semantics live in the ISA (programs / `<call>` modes run by
  the interpreter), NEVER Python helpers poking the substrate."
- Zero storage cost; paid only where a learner runs.
- It works on the FORWARD path, which is where a learner runs: `run_rules` services sync
  `<call>`s at each stratum via the existing dispatch (`intake.py:246`). No new control path.
- Interning is the calculator's job, which puts the `add_node`-always-mints hazard (§2) in
  exactly one place instead of in every learner.

**C. Make predicates nodes again.** Reverses name-demotion. Rejected — large, and against a
settled decision.

**Open sub-question for the build:** whether the token is `control=True`. It must not pollute
the fact view or `recall.profile` (which already excludes `<…>` scaffolding but would see a
plain node named `is_a`). Provisional answer: control-marked, `PATTERN_MARK`-attributed, same
as every other pattern-space node.

### 4.1 What the spike changed (2026-07-18, `bench/spike_predicate_reification.py`)

**The original signature `pred_tok(relation)` is a NON-TERMINATION WALL, not a preference.**

A rule that writes a bound RELATION NODE as an object never reaches fixpoint. A pattern's
subject is reached by FOLLOW-in from its relation node, so once `<call> --arg--> R` exists, that
new `arg` relation ALSO points at `R` and therefore binds as the SUBJECT of the very pattern
that produced it — one extra binding per round, forever. `max_rounds` is the only thing that
stops it, so the rule silently produces garbage rather than failing. Fixed by neither
`control_preds` nor `provenance=True` (both measured).

This is **not specific to learning**: it is a general consequence of reified relations —
pointing at a relation node makes the pointer indistinguishable from a subject. It deserves
attention on its own account.

**The resulting discipline, binding on every learner:** READ relation nodes freely (a
free-variable predicate on the LHS is fine and terminates), but NEVER write one as the object of
a rule-minted relation. The calculator takes an ENTITY and enumerates that entity's own
relations itself; a TOOL write does not re-enter the match loop as a subject.

**Two further findings that constrain the build:**

- **Tools are serviced only at QUIESCENCE** (`lowering.run_bank`, `if not pending:`). A
  non-terminating rule STARVES the dispatcher — during the wall above the calculator was never
  invoked at all. So a guard that depends on a tool's own output cannot fix a runaway that
  precedes it (chicken-and-egg, measured); **termination must be structural.**
- **The tool's write still pollutes the OBJECT position** — a milder residue of the same
  phenomenon. `rel --pred_tok--> token` gives the relation node an out-edge, so a pattern
  reading `?s ?p ?o` binds `?o` to the unnamed `pred_tok` relation node as well as to the real
  object, silently yielding learned rules with EMPTY tokens. Which raises §9.1.

**Validated end to end regardless:** with the corrected signature, a learner keyed off an
OBSERVED predicate learns a rule that derives `robin flies` — an entity never observed flying —
and learner + learned coexist in ONE bank in a single stratum with no cycle and no runaway.

## 5. Brick 1 — the learner

### 5.1 Shape

A learner is an ORDINARY RULE. No new rule type, no engine mode. Its LHS reads observations plus
the pattern-vocabulary markers; its RHS writes `rl_key` / `rl_lhs` / `rl_head` and the `<cond>`
atoms. `bench/spike_rule_learning.py`'s `LEARNER` is the working template.

### 5.2 Keying — and why dedupe solves itself

Key the learned rule by **what it generalizes**, not by the instance that prompted it. The spike
keyed on `?k` (the category), and both observations (tweety, polly) produced key `bird` with
identical bodies. `form_authoring.merge_forms` semantics then apply unchanged: same key +
identical rule = idempotent no-op; same key + DIFFERENT rule = loud conflict. Two observations
supporting the same generalization collapse for free; two observations supporting CONFLICTING
generalizations under one key become a loud, inspectable event rather than a silent last-writer-wins.

This is the whole dedupe story. It is a consequence of the keying choice, not a mechanism.

### 5.3 The pattern vocabulary

Learners need interned, marked nodes for: pattern variables (`?x`, `?y`, …) and predicate tokens
(§4). Both are ordinary control data. Both MUST be interned by name (§2). The variable pool is
finite and small — a learner that needs a third variable is generalizing more aggressively than
this design licenses (§6).

### 5.4 Where learned rules land

`intake.py:451`, the existing path, behind the existing `_stratify_conflict` gate (§8).

## 6. Licensing — what makes a learned rule believable

**DECIDED: born hedged, promoted by survival.** Not counting, not frequency.

Rationale: counting was rejected for the grammar (vision §10) and the same objection applies —
it imports an opaque quantity the system cannot explain. Meanwhile the substrate already has an
instrument that IS explainable: a band.

### 6.1 The lifecycle

1. **Birth.** One observation licenses a rule at a hedged prior. Its conclusions arrive wearing
   a band, so `check` renders them as `no (assumed)` / the banded verdict words rather than as
   asserted fact. A learned rule is *visibly* a guess, in the surface the user already reads.
2. **Promotion.** Surviving uses raise the prior. (Exact schedule: §11 open.)
3. **Death.** `broken_assumption` → the reconsider cascade retracts the conclusions;
   the rule itself is `disable`d through `rule_control`, not deleted, so the event stays
   explicable. Retraction machinery is copy-on-delete and already built.

The learned rule's provenance is the discrepancy (or observation) that spawned it, so
"why do you believe this rule?" is answerable in words — the same `why` surface that renders
"standing on the likely world where: …".

### 6.2 The encoding gap

`Rule.probability` exists (`production_rule.py:212`, "prior; flows into derived confidence") but
**neither reification encodes it** — `rule_graph.py:34` names it as a deliberate deferral, and
the flat schema has no `rl_prob` role. `rl_graded` is NOT this: it is a per-condition α-cut
(`GradedCondition`), not the rule's own prior.

**Required:** an `rl_prob` role in the flat schema, read by `expand_rules` into
`Rule.probability`. Small and local, but it is a real prerequisite for §6.1 and must not be
discovered during the build.

### 6.2b k>=2 by ELIMINATION — measured (`bench/spike_k2_intersection.py`)

Two axes, and conflating them was the muddle in the first draft of this section:

- **examples narrow the HYPOTHESIS SPACE** (by refutation — symbolic, exact, each death carries
  a printed reason);
- **the band carries CONFIDENCE** (§6.1).

Measured on the directional ambiguity that birds-that-fly leaves open:

| condition | well-formed distinct rules | survive |
|---|---|---|
| k=1 (birds only) | 2 | **2** — `is_a bird => flies` and `flies => is_a bird` equally supported |
| k=2 (+ one thing that flies and is not a bird) | 2 | **1** — the reverse is REFUTED |

Refutation uses the substrate's OWN machinery — declare `bird disjoint_from vehicle`, run the
candidate, read `contradictions()` — so a refutation arrives explained ("predicted a
contradiction about [plane] violating [bird|vehicle]") in the author's vocabulary. **No frequency
is counted anywhere.**

**Correction to this design's own earlier claim.** The reported "32 rules from 2 observations"
was mostly NOISE, not over-generalization: 24 of the 32 are malformed (empty tokens, §9.1/finding
E) and the rest dedupe to two. The genuine over-generalization is small and specific — the
DIRECTION of the regularity — and k=2 halves it. Real, but far less dramatic than the raw count
suggested, and it does not on its own justify a statistical apparatus.

**THE BOOTSTRAPPING PARADOX (the important negative result).** With NO disjointness declared,
NOTHING is refuted — `plane is_a bird` is simply derived and sits there, false and undetectable.
So elimination is strongest when the KB already carries constraints and weakest when it is
sparse, which is exactly the bootstrapping case this arc exists to serve. Counting would not
rescue it either: the bad rule has the SAME support as the good one. The missing ingredient is
not evidence WEIGHT but a DISCRIMINATOR.

**Consequence for the design:** when a learner's hypotheses are under-determined, the system
should ASK the discriminating question — "does anything fly without being a bird?" — rather than
wait for an example. It knows precisely which hypothesis is open, so the question is derivable,
and the existing `can_ask` wait-set already carries it. This is the highest-value active-learning
move available here and it needs no new machinery. It also reunites this half of the arc with
§7.1's dialogue: both halves bottom out in "ask the one question that would settle it".

### 6.2c The DISCRIMINATING QUESTION — derivable (`bench/spike_discriminating_question.py`)

The bootstrapping paradox above says the missing ingredient is a discriminator. **The system can
derive one itself**, mechanically, from the candidate set alone — validated by spike.

**The derivation.** A hypothesis is BODY => HEAD. Instantiate each candidate's BODY with a fresh
individual — the CRITICAL INSTANCE, the minimal situation that triggers it — then evaluate every
candidate on that instance. Where predictions DIFFER, the instance discriminates and the disputed
prediction is the question. No hypothesis-space search and no probabilities: the question falls
out of running the candidates against each other's trigger conditions.

From the birds-only candidate set, the two derived questions are exactly:

```
Q1  Given `something is_a bird` — is it the case that `something flies yes`?
Q2  Given `something flies yes` — is it the case that `something is_a bird`?
```

**Eliminative power is ASYMMETRIC**, and the design should exploit it: `no` REFUTES whoever
asserted the prediction; `yes` separates nothing (the others were silent, not contradicted). So a
question is worth asking exactly to the extent its `no` branch is live — which is also the right
ranking function when several questions are available. Answering Q2 with a counterexample kills
precisely the hypothesis Q2 targeted (measured).

**Production home: `suppose(commit=False)`** — it agrees with the forward run exactly
(`confirmed` vs `inconclusive`, matching asserts vs silent), so the derivation runs read-only,
scoped and explainable, with no scratch graphs. **Constraint:** `suppose` is demand-driven and
must be used as a CHECK of an already-known candidate head, never as "enumerate the
consequences" — with `predictions=[]` it derives NOTHING and returns a vacuous `confirmed`. The
algorithm knows each candidate's head, so this costs nothing.

*(Minor API note found in passing: `suppose`'s `assumptions` are `(SUBJECT, pred, object)` while
its `predictions` are `(PRED, subject, object)`.)*

**Why this is the linchpin.** It makes bootstrapping tractable in exactly the case where §6.2b
was weakest — a sparse KB with no constraints to collide with. The system does not wait for a
discriminating example to arrive; **it names the example it needs.** And it reunites the two
halves of the arc: form learning asks "say it another way" (§7.1 T3), rule learning asks "is
there a counterexample?" — both bottom out in asking the one question that would settle it,
on the `can_ask` wait-set that already exists.

### 6.3 What licenses the GENERALIZATION (not the confidence)

Confidence says how much to trust a rule; this says which slots may abstract. Use
`recall.profile` / `Hit.shared` (`ugm/recall.py`): the shared dimensions of two instances ARE
their anti-unification, expressed in the author's own vocabulary (`is:in_stock`, `is_a:shop`).
A slot abstracts when the instances share the dimension; it stays ground otherwise. This reuses
the recall arc, keeps the generalization explicable (`Hit.shared` is literally the reason), and
needs no imported concept table.

Constraint from `recall.py`'s own findings: similarity here is RELATIONAL. Entity nodes carry no
graded attrs, so generalization is over `pred:object` participation, not over entity attributes.

## 7. The trigger loops

### 7.1 Form learning — "Caveman CNL"

> **REVISED 2026-07-18 after a correct objection from the user: the first version of this
> section designed an ALIAS mechanism and called it form learning.** `_nearest_forms` can only
> ever propose shapes ALREADY in the grammar, so "did you mean `… gives … to …`?" mints a form
> whose RHS is COPIED from the existing form — a new surface for identical semantics. The set of
> expressible meanings is unchanged. That is habitability repair, not learning. The tiers below
> separate what that mechanism actually buys (T1) from what genuinely extends the grammar (T3).

Today: recognition fails, `_nearest_forms` (`intake.py:213`) computes the closest declared
surfaces from the form banks' OWN bound literals, and the result is returned in
`Outcome.nearest` (`intake.py:50`) — *stranded in a Python return value*, where no rule can
react to it.

**Change 1 (the enabler for all three tiers):** land the recognition failure and its nearest
candidates in the GRAPH as facts, the way `discrepancy` already is. Vision §1(b): failure is DATA.

#### T1 — alias (new surface, existing semantics)

The `nearest`-confirmation dialogue. The learned form's RHS is copied from the matched form.
Buys word order, dropped articles, synonyms — the "caveman" ergonomics, and genuinely useful,
because the shipped surface is narrow (measured: `bob likes alice` is UNRECOGNIZED with a bare
rule set — arbitrary binary verbs need a declared relation, cf. the `load_corpus` custom-relation
work). But it adds **no expressive power**, and the design must not claim otherwise.

#### T2 — authored (new semantics, no learning)

Already ships: `form KEY : HEAD when BODY` accepts an arbitrary RHS (`form_authoring.py`). Full
expressive power, zero induction — the user writes the mapping. Dialogue's honest role here is to
SCAFFOLD this, not to replace it.

#### T3 — induced from a rephrasing (new semantics, learned) — **the real Caveman CNL**

```
user: bob give alice book              -> unrecognized
sys:  I don't understand. Say it another way?
user: bob gives a book                 -> structure S1
      the book goes to alice           -> structure S2
sys:  align the ORIGINAL tokens against S1 u S2; mint a form
```

The RHS comes from **the user's rephrasing, not from the nearest form**, so it is bounded only by
what the user can express. Crucially the rephrasing may be SEVERAL sentences producing a
multi-relation structure that **no single existing form produces** — so the minted form has an
RHS nothing in the grammar had. That is real new expressive power: one utterance shape now folds
to a structure that previously took three sentences.

**Capturing the target structure** is a solved problem: a before/after diff over the graph
isolates exactly what a recognized utterance produced (verified: `bob is a person` yields
`('bob','is_a','person')` and nothing else). `_derivations_since` (`intake.py:107`) is the
richer provenance-based version where derivations, not just recognition, are wanted.

**Alignment** — which original tokens become variable slots — is tractable because content words
PERSIST across the rephrasing: `bob`, `alice`, `book` appear in both. Shared mentions become
slots; the remaining original tokens become fixed keywords. Forms already work over exactly this
token-chain vocabulary, so the minted form is an ordinary form.

**The honest ceiling.** T3 cannot invent semantics the user cannot already express. This is not a
defect to engineer away: a system that invented relational semantics unprompted would be
fabricating, the same discipline as recall's "proposes, never concludes". The user supplies the
MEANING; the system learns the SURFACE MAPPING to it.

**The open risk** (settle by spike before designing further): one example under-determines the
slot/keyword split, especially under word-order variation — and a wrong split yields a form that
over-fires on unrelated utterances. Candidate resolutions: confirm the split in dialogue, require
a second example, or mint the form hedged (§6) so a mis-generalized form is retractable by the
same machinery as a mis-learned rule. `lint_recognition_safe` and `merge_forms` apply unchanged
throughout.

T1 needs neither §4 nor §6.2. T3 needs neither either, but does need the alignment spike.

### 7.2 Rule learning from discrepancy

`discrepancy` is already a fact, and already drives replan (`corpus/procedure.cnl:40–78`). The
addition: alongside recovering, GENERALIZE — learn a rule that predicts the failure next time,
born hedged (§6), generalized by shared dimensions (§6.3).

Gated on §4: a discrepancy is *about* an observed predicate, so a learner over it cannot use a
predicate vocabulary fixed at authoring time. (This corrects an earlier reading in which this
loop looked independent of the primitive.)

### 7.3 Rule revision from broken assumptions

Already-built machinery, new subject: when `broken_assumption` fires on a conclusion whose
support includes a LEARNED rule, the rule is the suspect. Demote its prior or disable it, and
let monotone re-derivation recover whatever is still supported ("over-forget and re-derive",
the reconsider arc's ratified stance).

## 8. Safety gates (none optional)

- **Stratification at LEARN time.** A learned rule can trivially create a negative cycle. Reject
  at birth via `_stratify_conflict` (`intake.py:65`), not at run. The gate exists; learning must
  route through it rather than around it.
- **`lint_recognition_safe` for learned FORMS.** An induced form whose conditions read fact
  structure is a domain rule firing at recognition time.
- **`reject_rhs_only_head_vars` for learned RULES.** A learner that abstracts a head slot not
  bound in the body has produced an unsound rule; the existing check catches it.
- **Focus-reachability GC must reach learned rules**, or a long session accretes dead grammar.
- **Loudness.** See §9.

## 9. Loudness — three real defects found by the spike (BUILT, S1)

> **Status: BUILT 2026-07-18** — `_atom_defect` in `ugm/cnl/rule_graph.py`,
> `tests/test_rule_fragment_loudness.py` ×6, suite 639 green.

Reading a malformed rule fragment failed three ways, all quiet or unhelpful. Only the first was
in the original write-up; **investigating it turned up two worse ones**, both silent:

1. **missing endpoint** → bare `IndexError: list index out of range` (naming no rule)
2. **duplicated endpoint** → silently kept the first and DROPPED the rest, so the rule's meaning
   depended on edge insertion order
3. **non-relation middle node** → silently yielded `Pat('', '', '')`, a rule matching nothing

All three now raise a `ValueError` naming the rule and the role, and ALL defects in a graph are
reported in one raise (a learner emits many fragments at once; raise-fix-raise would be its own
usability failure).

### 9.1 S1b — the FLAT reader still needs it (prerequisite, not polish)

**S1 hardened the wrong reader for learning's purposes.** `rules_in_graph` reads the FACT-SHAPED
schema; the learning target is the FLAT schema, whose reader `expand_rules` has no equivalent
validation. The §4.1 spike produced learned rules with EMPTY pattern tokens
(`('?x','flies','')`, empty keys) and `expand_rules` emitted them without complaint.

Required before a learner ships, for the same reason S1 was: once learning exists, malformed
fragments are ordinary, and every learner bug would otherwise surface as a silently-empty token
rather than a diagnostic. Minimum bar: an unnamed/empty S, P, or O in a folded clause, and an
empty `rl_key`, are loud.

**Correction to an earlier claim.** This section previously asserted that the unanchored-skolem
spelling "silently writes NOTHING at all". That was wrong — an artefact of a broken spike fixture
(the duplicate-`add_node` hazard of §2, which stopped the learner's LHS from matching at all).
The RHS writes perfectly well and mints one fragment PER MATCH. Its real limitation is narrower
and is exactly §3's: it cannot build the 2-hop atom the role edge must point at.

## 10. Slices

Ordered so each lands green and nothing waits on an unbuilt primitive:

- **S1 — Loudness fix (§9). DONE 2026-07-18** (suite 639 green). Independent, small,
  prerequisite for debugging every later slice.
- **S2 — Caveman CNL (§7.1).** Recognition failure as a fact (Change 1) + the T1 alias dialogue.
  No new primitive. Most visible payoff, but T1 only — it does NOT extend the grammar.
- **S2b — T3 alignment spike (§7.1).** Given an unrecognized utterance and the structure its
  rephrasing produced, can shared-mention alignment mint a correct form? This is the slice that
  makes form learning real rather than cosmetic; spike the alignment before designing it.
- **S1b — loudness for the FLAT reader (§9.1).** Prerequisite for S5, same argument as S1.
- **S2c — the discriminating question (§6.2c).** De-risked by spike: derivation works and
  `suppose(commit=False)` is the home. This is the BOOTSTRAPPING engine and serves both halves
  of the arc; rank candidate questions by whether their `no` branch is live.
- **S3 — Predicate reification (§4, option B).** The `pred_tok(ENTITY)` calculator + interning.
  De-risked by spike: buildable, with the §4.1 discipline.
- **S4 — `rl_prob` (§6.2).** The encoding gap for born-hedged.
- **S5 — The learner (§5).** Flat-schema learner rules, keyed by generalization, gated by
  stratification. Promote the spike's L3/L4 into `tests/test_learning.py`.
- **S6 — Discrepancy → learned rule (§7.2)** and **revision (§7.3).** The loop closes.

## 11. Open (named, not forgotten)

- **Promotion schedule** (§6.1 step 2): what raises a prior, and by how much. Deliberately
  unspecified — it should be settled by watching S5 behave, not decided in advance.
- **Variable-pool size** (§5.3): how many pattern variables to intern, and whether exhausting
  the pool should be a loud refusal to generalize (probably yes).
- **Predicate-token control marking** (§4, open sub-question): interaction with `recall.profile`.
- **Learned-rule interaction with `suppose`**: a learned rule inside a supposition scope is
  untested territory.
- **When NOT to learn.** No design here for suppressing a learner that fires on every
  observation. §6.3 constrains the generalization's SHAPE but not its RATE.

## 12. Cost model

Learning runs on the forward path at intake, not in the demand chain — it is bounded by
observations per utterance, not by graph size, consistent with the session-sized scope
(per-utterance/session scale, not data scale). The `pred_tok` calculator is O(1) per distinct
predicate after interning. The one super-linear risk is a learner whose LHS is not anchored
enough to be selective; the existing `Unlowerable: no ground anchor` check already refuses the
worst case (spike L5 hit it).

## 13. Test plan

- Promote spike L1/L3/L4 to contract tests (variable pool binds; rule writes rule;
  learned rule fires on unseen data).
- Malformed learned fragment → loud diagnostic, never `IndexError`, never silence (§9).
- Learned rule that would create a negative cycle → refused at learn time (§8).
- Two observations, one generalization → ONE rule (§5.2 idempotent merge).
- Two observations, conflicting generalizations under one key → loud conflict (§5.2).
- A learned rule's conclusions wear a band; `broken_assumption` retracts them and demotes the
  rule (§6.1).
- Caveman CNL: unrecognized → nearest-as-fact → confirmed alignment → a form that then
  recognizes the originally-unrecognized utterance (§7.1).
- Forward/demand parity for learned rules (they are ordinary rules; the sweep must cover them).

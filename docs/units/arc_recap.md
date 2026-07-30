# The arc, recapped — where this came from and where it's going

**Status: living recap, started 2026-07-30.** This document is deliberately different from every other
file in `docs/units/`: those are each a narrow, self-contained investigation (one design question, one
worked example, one probe). This one is the through-line — what problem started this, what turned out to
matter, and what we're actually doing right now. Update the "Where we are now" section as work continues;
add a new "Act" only when a genuinely new phase starts, not for every incremental finding (those belong in
their own document and get a line added to the table in §0).

## 0. Map — one line per document, in the order they matter for understanding the arc

| when | document | what it settled |
|---|---|---|
| 07-23–07-26 | `model.md` (+ its superseded predecessors, see its own header) | substrate inversion: data is the substrate, computation a transient circuit; two planes; scope is support, not containment |
| 07-26 | `cnl.md` | the CNL surface: create-never-merge, roles as a closed vocabulary, rules unroll a statement |
| 07-27 | `forms_discourse.md` | closed class exact / open class opaque; the Leibniz question answered; harmony as the composition discipline; CONTENT×FORCE×LEVEL |
| 07-27 | `units/sieve.py`, `forms.py` | the closed class **measured**, not argued: guards silence rather than compose; discharge structurally impossible |
| 07-27 | `computation_units.md` | the tunnel, precisely: a computation unit's output doesn't persist; a unit sees only its own gates |
| 07-27 | rule-writes-a-rule (RHS local names) | a rule can mint structure connecting nodes it just made — the precondition for "a rule writes a rule" |
| 07-29 | `goal_machinery.md`, `units/goal_experiment.py`, `system1_experiment.py` | goal/subgoal lineage, outcome-as-fact, additive rewriting, first System 1 retrieval prototype |
| 07-30 | `planning_meta_concepts_arc.md` | planning ⇒ the open middle tier ⇒ meta-concept unification (goal/procedure/question/prohibition are one shape) |
| 07-30 | `closed_class_rechallenged.md` | the stage-1 closed class itself rechallenged; 5 probes; the real closed class is ~5 substrate-level things |

Read `closed_class_rechallenged.md` and `planning_meta_concepts_arc.md` for the connective narrative of the
most recent phase, in full, including the wrong turns. This document only summarizes.

## 1. Act I — substrate inversion (the ground everything else stands on)

The starting reversal: **data is the substrate; computation is a transient circuit over it**, not the other
way round. A `StandingUnit` (a rule) is itself just more graph data until an assembler wires it and a
revive powers it — "being expressible as a subgraph is not the same as being a unit" (`model.md` §6). Two
planes: plane 1 (inert — nodes, edges, attributes, and the *descriptions* of units) and plane 2 (running —
units, gates, wires, revive).

The load-bearing consequence for everything downstream: **scope is support, not containment.** A
supposition doesn't put a fact "inside a box" — it powers whichever units are wired downstream of it, and
`Network.powering()` walks the wiring backward to find what a unit's output rests on. "The world" is a
filter (what's derived by units powered by no supposition), never a place. This is what lets conditional
reasoning happen **without ever tagging data with a hypothesis label** — the same mechanism that later made
`suppose()`/`supposing()` safe for the exploration-vs-execution planning work (§4 below).

A companion finding, precise and worth keeping distinct from scope-as-support: **the tunnel** is a *unit*
property — a `StandingUnit` sees only what its own gates deliver, never the ambient graph. A computation
unit's output (as opposed to a mutating rule's) is recomputed fresh every revive and never persists — which
is what makes a defeasible conclusion revisable for free, with no retraction machinery. Both of these —
scope-as-support and the tunnel — are what "computing under a hypothesis" cashes out to mechanically.

## 2. Act II — the CNL surface, forms, and the first closed/open question (Leibniz, 07-27)

Designing the CNL surface raised: *what are the "categories" a statement can belong to — question,
procedure, hypothesis?* The answer dissolved the question rather than answering it: a category is a point
in **CONTENT × FORCE × LEVEL**, not an entry in a list, and two of the three named candidates (question,
procedure) turned out to need nothing beyond an existing axis value. That produced the claim: **the system
holds the closed class exactly and the open class opaquely** — closed class is structure, composed;
open class is content, associated (embeddings).

This raised the objection that gives this thread its name: **if the closed class is small, how does that
square with 350 years of failed reduction programmes** — Leibniz's *characteristica universalis* (a catalog
of primitive concepts) plus a *calculus ratiocinator* (rules for combining them), the line running
Wilkins → Leibniz → Frege → Carnap? The answer, scored by halves: **the failure was entirely on the open
class side.** Not one agreed decomposition of an ordinary noun in 2,500 years — but the closed-class half of
that same programme *succeeded*: logical connectives with harmony, grammatical categories, thematic roles
(FrameNet/PropBank/VerbNet) are all engineered and in production. Quine's confirmation holism (the result
that *killed* the total reduction programme) and the case for learned/embedded representation of open-class
content are the same fact seen twice.

**Composition, not enumeration, is the hard part**, and the answer transplanted from proof theory: **harmony**
(Prior's tonk, Belnap/Prawitz/Dummett) — a form is well-defined iff its introduction rule and elimination
rule fit. Mapped onto the engine: a form ships with both a unit that writes it and a unit that reads it, or
it does not ship. This is what makes a form set of this size tractable at all (checking intro/elim pairs is
linear; probing all pairwise compositions is not) — and it retro-diagnosed the one measured leak
(`degree ∘ negation`: two introductions, no shared elimination).

`units/sieve.py` then **measured** the closed class instead of arguing it, the same week: 65% of naively
authored cells leaked; guards silence rather than compose (a composed pair doesn't combine, it goes silent);
composition needs an entry *per pair*, not automatically; and conditionality's discharge was found
**structurally impossible** — falsifying an earlier design assumption outright. `SUPPOSE` was reinterpreted,
correctly, as the conditional's own introduction rule rather than a fifth "force."

## 3. Act III — the middle-tier discovery (planning, 07-30)

The next thread started from a narrow, mechanical question: *how does an agent go from exploring a plan to
actually executing it?* Working through it surfaced something that didn't fit either side of the Act II
split. A causal fact ("doing X causes Y") or a business norm ("orders over 500k must ship early") is
**content** — open-ended, unbounded — but it is not the *same kind* of open content as an ordinary noun's
meaning. It doesn't compose by association (embeddings); it **expands, at authoring time, into a fixed
conventional shape**, and a generic meta-rule reads that shape and mints something (a plan step, a
`requires` fact) — never executing the content directly, the way a `StandingUnit`'s `pattern:`/`effect:`
would. That's a **third species**: not the closed, executable class; not the opaque, embedded open class;
a subset of open content that composes **procedurally**, through declared shape plus generic meta-rules,
rather than through either boolean-logic-style unbounded nesting or associative similarity.

Working through several of these (causal facts, business norms, standing prohibitions, procedures, goals,
questions) side by side raised the real worry: **do independently-authored middle-tier meta-rules combine
safely**, the way an agent (not a scripted chatbot) needs — a procedure whose step is a question, a
question about a procedure, an action blocked by a standing prohibition? Zave's telecom feature-interaction
literature is the right precedent, and instructively so: that field's *first* approach tried to prove no
combination of features could interact badly (tractable only while the feature vocabulary was small and
fixed — exactly this project's original closed-class hope); as the feature set grew unboundedly, the field
moved to **detecting interactions at runtime and arbitrating them**, not re-proving soundness from scratch.
That is the answer adopted here, and the good news was that the detection half already existed —
`detect_conflicts()`, built for an unrelated reason (the "umbrella" supposition-safety case) — surfacing
two disagreeing conclusions as an ordinary fact on a wire. **What's still missing, honestly: a declared
arbitration convention** ("this norm overrides that one") — detected conflicts currently stay honestly
unresolved rather than silently decided, and that's a real, open gap, not a solved problem.

This was then checked, not just argued: `units/meta_concept_unification_experiment.py` (3 green) showed a
procedure is a goal decomposition plus one sequencing edge; a question is a goal wanting a knowledge-claim
instead of a world-state claim; a standing trigger needs nothing new (a wired `StandingUnit` already is
one); a prohibition is the closed-world-stance-fact pattern generalized. **Four apparently different
architectures turned out to be one shape wearing different surfaces** — the goal/subgoal machinery
`goal_machinery.md` had already built.

## 4. Act IV — the closed class, rechallenged (07-30, same day)

Naming the causal-fact-as-meta-rule pattern surfaced something that had been sitting unreconciled for over
a week: `causation-core-was-sugar` (a finding from 07-22, in the *old* `ugm` engine) had already shown
causation resolves as a generic propagation schema plus one declared fact — never a new primitive — and
`closed_class_inventory.md` still listed it as closed-class content "awaiting formalization." That
contradiction was the trigger for going back and **rechallenging the Act II closed class itself**, not just
adding new middle-tier content beside it.

The sharper dividing line that emerged: not CONTENT vs. FORCE vs. LEVEL, but **single-claim modifier**
(negation, degree — true of any claim, looks genuinely substrate-level) vs. **multi-occurrence relation**
(conditional's relational core, causation, quantification's open case, force/level's routing, procedures,
plans, business norms). Every relational form checked, without exception, resolved to open content read by
a meta-rule. Two independent external checks converged on the same line: linguistic closed-class
inventories (~40-60 categories) answer a *parsing* question (what gets a dedicated surface marker), not an
*execution* question; and Datalog's fifty years of practice — its whole closed algebra is conjunction,
stratified negation-as-failure, and recursion to a fixpoint, with causation as an ordinary predicate and
propagation an ordinary recursive rule — is the sharper, formal version of the same finding.

**Five relational forms were then actually probed, not just argued, against the running `units/` engine:**

| form | result |
|---|---|
| causation | confirmed sugar (prior finding, old engine) |
| quantification's open case | confirmed sugar (goal machinery, prior finding) |
| force | confirmed sugar, `units/force_probe_experiment.py` — ask/command routing is two near-identical meta-rules minting a goal |
| level | confirmed sugar, `units/level_probe_experiment.py` — world/theory routing is the same shape; a theory-level claim is satisfied by an ordinary rule reading another rule's own conclusion |
| identity/merge | confirmed sugar, `units/identity_merge_probe_experiment.py` — one generic rule, quantifying over both concept kind and key value via two `AttrVar`s, emits the engine's already-built `Merge` effect |
| **transitivity** | confirmed, **but not sugar** — reading transfers free via `AttrVar`; writing needed a real, small engine extension (below) |

**⭐ Transitivity is the one exception, and it's the reason "probe first" is a discipline and not a
formality.** Every other item above needed *zero* engine change — declare it as data, read it with an
unmodified engine. Transitivity's write side genuinely couldn't be authored: every RHS effect template
(`Attribute`, `Link`) only accepted literal attribute/role names, so a rule could not conclude "x relates to
z under whichever relation the match just found." `units/engine.py` was extended — `Attribute.value` and
`Link.role` now also accept an already-bound `AttrVar`, symmetric to how node fillers already read match
bindings — pinned in `tests/units/test_engine.py`, checked in `units/transitivity_probe_experiment.py`
(4 green), gated on a declared `relation_kind(..., transitive=True)` fact per relation exactly as planned.

A sixth, adjacent risk — not a new relational form, but a worry about how the middle tier's additive
rewriting interacts with the engine's conflict machinery — was checked the same day:
`units/definitional_coexistence_experiment.py` (3 green) confirmed that two independently-authored rules
reaching the identical conclusion via two coexisting forms of the same fact do **not** spuriously register
as a conflict (`Overlays.conflicts()` dedupes by value, not by source), while a genuinely different
conclusion still is caught. This is a narrower, mechanical confirmation — separate from §3's still-open
arbitration-convention gap, which is about *resolving* a real conflict, not about avoiding a fake one.

**The resulting, checked closed algebra:** conjunctive matching, θ-gated negation-as-failure, a
meet-semilattice for gradedness, the five raw substrate effects, and modus ponens understood as the
substrate's own execution semantics (not a meta-rule at all — any `StandingUnit` firing already *is* modus
ponens). Everything else this project has needed for an agent — goals, procedures, questions, prohibitions,
causal reasoning, force, level, identity, transitivity, business policy — is open content read by a
comparatively small number of generic meta-rules, all sharing one representational shape, with exactly one
of them (transitivity's write side) needing a genuinely new, small piece of substrate.

## 5. Where we are now, and current direction

Every item on `closed_class_rechallenged.md` §9's probe list is checked. `closed_class_inventory.md`,
`composition_grammar.md`, `agentic_scenario_catalog.md`, and `cnl_engine_goal.md` have all been revised in
place to match (2026-07-30 hygiene pass — see `README.md`'s "Verification" section for what changed in
each; `composition_grammar.md` also survives narrowed to `conditional` specifically, the one genuinely
relational closed-class form it was ever for). `docs/units/attic/` gained two entries
(`forms_extra_considerations.md`, `planning_example.md`) whose ideas are fully absorbed elsewhere.

**The one concrete next step:** design the causal-fact→plan meta-rule and the norm→requirement→satisfies
chain — the piece of planning-support work that started Act III in the first place, now with a settled
answer about which parts are load-bearing engine primitives (the small `Attribute`/`Link` extension) and
which are ordinary meta-rules over open data (everything else).

**Genuinely open, not yet resolved, and worth naming so it doesn't get silently dropped:**

- **The arbitration convention** (§3/§4) — detecting a middle-tier conflict is built; deciding it ("norm A
  overrides norm B", as declared data) is not.
- **Recursion/termination for the newly-confirmed recursive schemas** (transitivity composed with itself,
  a defined equivalence unfolding) — flagged in `closed_class_rechallenged.md` §8, connects to Phase D's
  pre-existing, still-unfinished termination work (`forms_discourse.md` §10.3), not yet connected to these
  specific schemas.
- Lower-priority items already on record in `STATUS.md` (`COMMAND`'s real semantics, `past`/`evidential`/
  `mirative`'s open-hypothesis status).

Update this section, not the Acts above, as work continues. When the inventory-revision and
plan-meta-rule work actually happens, it earns its own Act V here — a one-paragraph summary with a pointer
to its own document, the same discipline every earlier Act follows.

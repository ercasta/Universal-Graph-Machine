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

**Then the CNL boundary's first real slice got built, 2026-07-30 (same day) — the current active thread.**
Full detail: `README.md`'s "The CNL boundary" section, `STATUS.md`. `units/cnl.py` is the first actual CNL
parser this project has (everything before it was design only); `goal_rules.py`, `author_rules.py`,
`prohibition_rules.py`, `identity_rules.py` are real, growing modules, not throwaway probes. Checked end to
end: natural-language prompts, translated by hand into CNL text, parsed, and run on the real engine —
question/command routing (reusing `goal_rules.py` unmodified) and a full "don't do anything dangerous"
scenario (a KB-authored `dangerous` fact vetoing an unrelated later command, order-independent). Two real
bugs surfaced and were fixed in the process, both instructive (a rule-constructor called twice building
disconnected object sets; a relational CNL role matched as if it were a crisp attribute, passing against
hand-built test graphs that shared the same wrong assumption while silently never matching real parsed
text) — recorded in the relevant modules' docstrings, not smoothed over. `author`'s harder case (compiling
an authored conditional into a genuinely new rule — "a rule writes a rule") is deliberately deferred as a
separate, bigger compiler task, not built ahead of a need.

**Then structural planning, and a real architectural resolution about the tunnel itself — same day,
current frontier.** `units/structural_choice_experiment.py`: a genuine choice among KB-declared candidates
(two wiper kits, one incompatible with the car's declared windshield), resolved by *actually committing* to
the real graph, honestly detecting the conflict against already-declared data, retracting, and trying the
next declared alternative — zero Python, zero supposition, three checks green. This led to a sharper
question — does the tunnel/supposition mechanism matter at all, given this? — and a real, load-bearing
resolution, **not yet built, but reasoned through precisely**: genuine counterfactual exploration doesn't
need Python or content-duplicating "bubbles" either. A meta-rule can read a declared business rule's own
`pattern:`/`effect:` data (already proven possible,
`test_a_rule_writes_a_whole_rule_with_nothing_authored_in_python`) and mint a **second, supposition-wired
instance** of it to explore hypothetically; confirming the hypothesis needs no crossing at all, because
confirming just means the antecedent becomes *really* true, at which point a separate, always-real-wired
instance of the same declared rule fires naturally. Full reasoning, including where my first objection to
this was wrong: `handoff_ugm_reversion_evaluation.md` §2 — **read that document now if picking this up
cold**, it also carries the open strategic question below.

**RESOLVED 2026-07-30 (same day) — the foundation question, and it did not resolve the way the handoff's
own §4.3 guessed.** The question raised above (revert to `ugm/` or keep building `units/`?) turned out to
have a third answer, found by reading `ugm/production_rule.py` and `ugm/machine.py` directly rather than
only their docstrings: `ugm/`'s `Rule` is ALREADY data (LHS/RHS/NAC as `Pat` lists, no Python closures),
and `ugm/machine.py` is ALREADY a real register-based ISA over a genuine substrate (`attrgraph.py`) —
mature, tested, two-phase match-then-apply, with the no-fact-deletion invariant built into the opcode set
itself. "Rules as data over a substrate" is not something `units/` has that `ugm/` lacks. `ugm/`'s actual
weakness sits one layer up, in `ugm/lowering.run_bank`/`run_to_fixpoint` — a Python driver that
aggressively forward-chains every declared rule bank to fixpoint over the WHOLE graph, every pass. That is
the thing to replace, not the substrate or the ISA underneath it.

**The decision: build forward on `ugm/`'s substrate + ISA + rule-lowering, not on `units/engine.py`.**
Replace `run_bank`'s blind whole-graph driver with an outer-loop metaprocedure — the "a rule writes a rule"
mechanism `units/` validated (`test_a_rule_writes_a_whole_rule_with_nothing_authored_in_python`) and the §2
tunnel resolution above, both hosted on `ugm/`'s substrate instead of a third from-scratch one. Concretely:
a meta-rule reads one declared `ugm` `Rule`'s own `lhs`/`rhs`, and mints a live instance of it — wired to a
real axiom, or to a supposition's cell (the §2 bubble mechanism) — in a targeted region, instead of
`run_bank` running every rule everywhere. `units/`'s own substrate and everything validated on it (this
whole Act) stand as the FINDINGS this rests on, not a rival implementation to keep maintaining in parallel.
Full audit, the `Rule`/`machine.py` reading that produced this resolution, and what's still open (`ugm/`'s
`suppose.py` family vs. §2, `focus.py` as the region-selection seed, whether `revision-01`'s
no-retraction argument transfers): `attic/handoff_ugm_reversion_evaluation.md`, filed with the resolution
recorded at its own top.

**Naming the source of the advantage, so it isn't lost under the "agentic" vocabulary (2026-07-30):**
"metaprocedure + goal-oriented + recovery rules + tool usage" describes a real computation model, but it is
not a new one — it's the classical production-system lineage (Soar/ACT-R/BDI), which has goal stacks,
repair, and procedural attachment with no LLM anywhere. The thing this project has that lineage doesn't is
homoiconicity: a rule is data, so another rule can read a declared rule's own pattern/effect and mint a live
instance of it — that's what the metaprocedure above and §2's tunnel-as-wiring resolution both actually run
on. An LLM is a tool a rule can dispatch to at the boundary (§9 of `model.md`), not part of the computation
model. Recorded in full as a standing position in `model.md` §11 — read it there before writing any future
document that frames this project as "agentic," to avoid crediting the wrong mechanism.

**Next, in order, now that the foundation question is resolved:** (1) read `ugm/suppose.py`,
`scope_crossing.py`, `scope_kinds.py` against the §2 resolution — does `ugm/`'s existing supposition
machinery already support wiring a minted rule-instance to a scope's cell; (2) probe a first outer-loop
metaprocedure directly on `ugm/`'s substrate, targeted rather than run via `run_bank`; (3) check
`ugm/focus.py`'s demand-derived attention register as the seed for "which region" the metaprocedure
applies to; (4) decide whether `units/`'s no-retraction argument transfers to this model, or whether
`ugm/retraction.py`/`reconsider.py` are still needed; (5) once the metaprocedure shape is validated on
`ugm/`, return to the causal-fact→plan meta-rule and norm→requirement→satisfies chain that started Act III,
now on the new foundation.

**Multi-turn context probed and resolved, same day (2026-07-30) — `units/history_recall_experiment.py`, 5
checks green.** A design question about how a running conversation reaches back into earlier turns —
"should `focus`/attention grow into a materialized breadcrumb structure plus a dedicated metaprocedure that
walks it, auto-triggered by a recall subgoal?" — turned out to need no new kind, same discipline as the
foundation decision above. A turn is an ordinary standing node linked to the previous one by an ordinary
`follows` edge (§1's "data is the substrate" already means nothing needs archiving); a recall subgoal is an
ordinary act of attention (§7); and picking *which* prior turn is a second, differently-authored resemblance
score over a small turn-root index, topic-driven rather than recency-driven. Full writeup:
`model.md` §7's new subsection, "Multi-turn context needs no new kind."

**Genuinely open, not yet resolved, and worth naming so it doesn't get silently dropped:**

- **The arbitration convention** (§3/§4) — detecting a middle-tier conflict is built; deciding it ("norm A
  overrides norm B", as declared data) is not.
- **Recursion/termination for the newly-confirmed recursive schemas** (transitivity composed with itself,
  a defined equivalence unfolding) — flagged in `closed_class_rechallenged.md` §8, connects to Phase D's
  pre-existing, still-unfinished termination work (`forms_discourse.md` §10.3), not yet connected to these
  specific schemas.
- Lower-priority items already on record in `STATUS.md` (`COMMAND`'s real semantics, `past`/`evidential`/
  `mirative`'s open-hypothesis status).
- **Real coreference beyond lexically-identical bare words** (`identity_rules.py`) and **real action
  dispatch** (`prohibition_rules.py`'s `executed` is a stand-in, not a real `<call>`) — both concretely
  surfaced building the CNL boundary, both deliberately narrow first cuts, neither a general solution yet.

Update this section, not the Acts above, as work continues. When the inventory-revision and
plan-meta-rule work actually happens, it earns its own Act V here — a one-paragraph summary with a pointer
to its own document, the same discipline every earlier Act follows.

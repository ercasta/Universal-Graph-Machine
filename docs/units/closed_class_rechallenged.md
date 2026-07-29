# The closed class, rechallenged — surface recognition vs. executable algebra

**Status: design note, 2026-07-30. Raised in conversation while designing plan composition
(`goal_machinery.md`'s planning thread); not yet probed the way `causation-core-was-sugar` was probed —
read §6 before treating any of this as settled.** This note does not replace
`closed_class_inventory.md` — it proposes a different, sharper question underneath it, and names what's
confirmed vs. hypothesized so the next session doesn't have to re-derive the distinction.
`planning_meta_concepts_arc.md` tells the full story this note is extracted from, in prose, including the
meta-concept unification (`units/meta_concept_unification_experiment.py`) that came after it — read that
first if the compressed version here doesn't carry enough context.

---

## 1. The conflation this note corrects

Building the plan-composition design surfaced a conflation that had been sitting underneath several
worked examples this session without being named: the **representation** of a relationship ("doing X
causes Y," "orders over 500k must ship early") is not the same thing as a mechanism the engine
**executes**. A `StandingUnit`'s `pattern:`/`effect:` (`units/engine.py:140-197`) is a small, fixed,
engine-native convention for *how to physically manipulate the substrate* — mint a node, add an edge, set
an attribute, merge, drop. A causal claim or a business norm is **content** — open-ended, unbounded,
domain-specific — and it should never be hand-transposed directly into that convention as if the engine
itself understood causation or obligation. It should be **read**, by an ordinary meta-rule (itself using
the closed pattern:/effect: convention) whose left-hand side matches the claim's *conventional shape*, not
its content.

## 2. Prior evidence, already in this project, not yet reconciled

Three findings, made independently at different times, all point the same direction and were not
previously connected:

- **`causation-core-was-sugar`** (2026-07-22): the entire causation core, when actually built in the old
  `ugm` engine, resolved as a generic `propagates` meta-schema plus one declared fact
  (`causes propagates has`) — never a new engine primitive. *"The cores really are native; what was
  missing was surface and declared meaning, not mechanism."*
- **`force-is-the-missing-axis`**: FORCE (assert/ask/command/author/retract) was already described as
  *"intake ROUTES not FORM"* — i.e., never claimed to generate content directly, only to decide which
  downstream machinery an utterance is handed to.
- **`closed_class_inventory.md`** itself flags `conditional` as *"the first form whose real home is a UNIT
  rather than a field... a relation between two occurrences,"* and quantification's hardest case (an
  open/unbounded domain) resolves via goal machinery, not a new primitive (§8).

`closed_class_inventory.md` still lists `causation` under **CONTENT**, alongside negation and
conditionality, marked "not yet formalized" — as if it were awaiting the same Phase-A treatment those
get. That row is stale; the finding that would correct it predates this session by over a week.

## 3. The sharper dividing line

Not CONTENT vs. FORCE vs. LEVEL. **Single-claim modifier vs. multi-occurrence relation.**

- **Single-claim modifiers** — a property a *single* claim can carry, true of any claim regardless of
  domain: can it be negated, can it be graded. These look genuinely substrate-level.
- **Multi-occurrence relations** — anything connecting two or more occurrences: conditional's relational
  core, causation, quantification's open case, force/level's routing, procedures, plans, business norms.
  Every one of these, once actually built and checked, has resolved to open content read by a meta-rule —
  without exception so far.

## 4. External grounding

**Linguistic closed-class inventories (~40-60 grammaticalized categories) answer a different question.**
Grammaticalization studies (cited already in `forms_discourse.md` §332: *time, space, causation, quantity,
modality, evidence, discourse status*) catalog which functions a language gives a **dedicated marker** —
a *surface/recognition* inventory. That causation reliably grammaticalizes (causative morphology exists
in many languages) means it belongs in the closed class **as something the parsing layer recognizes**
(`cnl.md`'s grammar, a separate concern) — it says nothing about whether the *content* processing behind
that marker is engine-native. Conflating "what the parser recognizes" with "what the engine executes
without deferring to open content" is, I think, the root of the original mistake.

**Datalog's fifty years of practice is the independent, formal check, and it already settled this.**
Vanilla Datalog's whole closed algebra is conjunction (a rule body), stratified negation-as-failure, and
recursion to a fixpoint. `causes(X,Y)` is an ordinary predicate; propagation is an ordinary recursive rule
(`has(Y,Z) :- causes(X,Y), has(X,Z)`), never a new construct. `units/`'s `pattern:`/`effect:` is the direct
analog of a Horn clause; `absent(...)` plus `band.py`'s `at_least` is the direct analog of stratified NAF.
Datalog never needed a causation primitive for the same reason this engine doesn't.

**Gradedness is the one place worth extending past vanilla Datalog, and there's real precedent for doing
it as an algebraic annotation rather than a new logical primitive.** Semiring-annotated Datalog
(provenance semirings — Green/Karvounarakis/Tannen) generalizes Datalog so every derivation carries a
value from a commutative semiring; a bounded lattice with min/max is exactly possibilistic logic
programming's move. `band.py`'s finite ordered scale with `meet` (min-join, `units/band.py:38-45`) **is**
that semiring, already built, already load-bearing in `match.py`'s `solve()`.

## 5. The (tentative) closed algebra, restated

Conjunctive matching (`solve()`) + θ-gated negation-as-failure (`absent()` + `band.py`'s `at_least`) + a
meet-semilattice for gradedness (`band.py`'s `meet`) + the five raw substrate effects (`Emit`, `Attribute`,
`Link`, `Merge`, `Drop`). That's the proposed executable closed class — full stop. Everything else —
force, level, conditional's relational core, quantification's open case, causation, procedures, plans,
business norms — is open content, read by meta-rules that are themselves ordinary `StandingUnit`s using
this same small algebra as their *output* convention, never their *input* convention.

A meta-rule reading open content has two legitimate destinations (both already proven buildable,
`test_a_rule_writes_a_whole_rule_with_nothing_authored_in_python`): mint **more open, inert data** (a plan
— one-shot, nothing persists as a new rule), or **compile a genuinely new closed-class rule** (a standing
policy watch — for recurring business norms, where re-deriving the same requirement from scratch every
time would be the "rediscovering rules" waste `system1_experiment.py` already flagged).

## 6. Confirmed vs. hypothesized — do not treat these the same way

| status | items |
|---|---|
| **Empirically confirmed** (actually built, checked against running code) | causation = sugar (old `ugm`, propagation schema); quantification's open case = goal machinery, not a new primitive; **force = sugar, `units/force_probe_experiment.py` (3 green)** — "ask"/"command" routing is two near-identical meta-rules minting a goal, resolved by the ordinary, force-blind `achieved`/`diverged` machinery; ⭐ **level = sugar, 2026-07-30, `units/level_probe_experiment.py` (3 green)** — "world"/"theory" routing is the same meta-rule shape, and a theory-level claim ("has the engine's own `vip_rule` concluded X") is satisfied by an ordinary rule reading another rule's conclusion as data — provenance already free, no introspection primitive needed — while staying honestly unresolved through a turn where only the *world* question gets answered; goal/procedure/question/prohibition unification — `units/meta_concept_unification_experiment.py` (3 green) |
| **Structurally implied, not yet probed** | identity/merge (Datalog has no analog at all — unification handles same-constant, not "these two different constants denote the same thing"; this project's own "identity is decided, not interned" stance already smells open); transitivity's predicate-variable mechanism (built in the old engine, unconfirmed in `units/`) |
| **Believed genuinely closed** | negation, degree/band, modus ponens (the substrate's own execution semantics, not a meta-rule — see §8), the raw substrate mechanics (mint/edge/attribute/merge/drop, `solve()`) |

**Force and level are no longer claims — they're findings, checked the same way causation was.** The
middle row is still a claim for what remains in it. `causation-core-was-sugar`'s own stated lesson still
applies to identity/merge and transitivity: *"for the next agentic core, expect a surface/declared-data
slice, not engine — probe first every time."* The pattern has now held for four relational forms in a row
without exception,
which is good reason to expect the rest resolve the same way — but betting on a pattern is still not the
same as checking it.

## 7. What this means for the planning design, concretely

Plans and procedures are **open concepts**, not new closed-class forms awaiting their own intro/elim
proof — `agentic_scenario_catalog.md`/`composition_grammar.md`'s framing of *"quantification, causation —
future `RelationalClaim`-shaped siblings, each needing their own design"* needs revising alongside the
causation row. A causal fact ("doing X usually causes Y") is authored in a fixed, conventional shape
(likely piggybacking on `conditional`'s existing relational shape, banded per `band.py`'s scale for
"usually"); a generic meta-rule reads *any* fact of that shape and mints a plan step. A norm ("orders over
500k must ship early") is authored in its own fixed shape (condition → obligation); one meta-rule mints a
`requires` fact from it, a second matches `requires` against separately-authored `satisfies` facts to mint
the actual action. Neither meta-rule is hand-written per business rule — each is written **once**,
generically, over the conventional shape, exactly like every other worked example this session.

## 8. Further observations, 2026-07-30 (same day) — modus ponens, transitivity, definition

Three more candidates raised in conversation, worth separating carefully rather than lumping into "more
relational forms."

**Modus ponens is not middle-tier — it is the substrate's own execution semantics, not a meta-rule.**
Every `StandingUnit`, matching its pattern and firing its effect, *is* an instance of modus ponens; that
is simply what `solve()` + `instantiate_all` do for any authored rule. What *is* middle-tier is the
adjacent, different step of getting from an openly-authored conditional *claim* (data — an antecedent and
a consequent connected by a `when:` role, `forms_cnl.md`) to something the substrate can execute — a
meta-rule that either applies it directly (if its content is already closed-class) or compiles it into a
real `pattern:`/`effect:` rule (`test_a_rule_writes_a_whole_rule...`, again). `closed_class_inventory.md`'s
*"modus ponens works"* was already talking about the post-compilation case, not a claim that business
conditionals need no meta-rule.

**Transitivity is middle-tier, and the old engine already found the mechanism — generic
predicate-variable matching, not one rule per relation.** `facts-as-truth-bearers-built` (2026-07-22,
`ugm`): transitivity written *once*, over a predicate variable (`?x ?r ?z when ?x ?r ?y and ?y ?r ?z`),
"works on demand" for whichever relation the query supplies. Applied unconditionally to any `?r` this is
simply wrong (my mother's mother is not my mother), so the safe version needs a declared `is_transitive`
fact per relation — the same "declare it, don't hardcode which ones get it" discipline as causation's
`propagates` and this session's stance facts. The *mechanism* (predicate-variable matching) was built in
the old engine; whether `units/` has or needs it is unconfirmed — added to the probe list below.

**Definition/substitution does not run into Fodor's paradox, and the reason is precise, not hand-wavy.**
Fodor's argument (`forms_discourse.md` line 199, informational atomism: *"concepts are primitive; content
is fixed by a causal/lawlike link to the world. There is no inside"*) is against using decompositional
definition as the *universal* mechanism for concept meaning — his case is that ordinary concepts reliably
resist clean definitions. This project already adopted the practical consequence of his alternative:
ordinary open-class words are never given explicit definitions here — they are embedding-absorbed,
holistic, exactly Quine's confirmation holism, exactly what [[baroque-vs-fundamental]] calls content an
LLM already carries. `define` was never proposed as a general theory of word meaning; it is a narrow,
explicit, opt-in mechanism for *stipulated* equivalences (paraphrasable without changing what the system
believes — textbook baroque). Fodor's target was a claim this project never made.

**Checking composition of these is the same runtime-detection answer as §7's Zave discussion, sharpened
by one new risk: these specific schemas are recursive.** Transitivity composed with itself derives longer
chains; a defined equivalence combined with transitivity or a business rule could keep unfolding. Not a
new risk in kind — exactly what Phase D's termination work (burned-unit exclusion, the widened surge
threshold, `forms_discourse.md` §10.3) already made honest for cycles generally, just not yet connected to
these specific schemas. One risk that *is* specific to definition: since additive rewriting keeps both the
old and new form of a fact alive (`goal_experiment.py`'s `check_rewrite_via_addition`), a rule reacting to
each form of the same defined equivalence could produce two representations of "the same" conclusion that
look different enough to register as a spurious conflict rather than genuine agreement — worth checking
directly, not assumed away.

## 9. Next actions

1. **Probe force before building anything further on top of it** — check directly whether "ask"/"command"
   recognition needs anything beyond parsing (already separate machinery) plus one meta-rule minting a
   goal, the same way causation was checked.
2. **Probe identity/merge** — same treatment, separately, not assumed.
3. **Probe predicate-variable matching for transitivity** — does `units/` have or need it; if built,
   gate it on a declared `is_transitive` fact per relation, never applied unconditionally.
4. **Check the definitional-coexistence risk** — build the smallest case where a rule reacts to each form
   of one defined equivalence and confirm the engine's conflict-detection reads it as agreement, not a
   spurious disagreement.
5. **Only then**, return to the causal-fact → plan meta-rule and the norm → requirement → satisfies chain,
   now confident about which parts of the design are load-bearing engine primitives and which are
   ordinary meta-rules over open data.
6. **Revise `closed_class_inventory.md`, `composition_grammar.md`, and `agentic_scenario_catalog.md`**
   once items 1-4 are actually probed, not before — matching this project's own "probe first" discipline
   rather than rewriting the inventory off a pattern alone.

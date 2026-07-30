# Handoff: should the project return to `ugm/`'s foundation, given this session's findings?

**RESOLVED 2026-07-30 — see `docs/units/arc_recap.md`'s current Act for the decision and its rationale.
Filed here (not deleted) because §§1–4's audit and the tunnel/metaprocedure resolution in §2 are still the
correct reference material — only the recommendation in §4.3 was superseded.**

**The actual resolution, stated plainly (differs from §4.3 below):** neither "don't revert" nor "revert
wholesale." `ugm/production_rule.py`'s `Rule` is already DATA (LHS/RHS/NAC as `Pat` lists, not Python
closures) and `ugm/machine.py` is already a real register-based ISA over a genuine substrate
(`attrgraph.py`) — so "rules as data over a substrate" is not something `units/` has that `ugm/` lacks.
`ugm/`'s actual weakness is one layer up: `ugm/lowering.py`'s `run_bank`/`run_to_fixpoint` is a Python
driver that blindly forward-chains every declared rule bank to fixpoint over the WHOLE graph, every pass —
that is "aggressively applying rules," not the substrate or the ISA, and it is the piece worth replacing.

**The decision: keep `ugm/`'s substrate (`attrgraph.py`), ISA (`machine.py`), and the rule→program
lowering/compiler itself — do NOT rebuild a third substrate. Replace `run_bank`'s blind whole-graph
fixpoint driver with an outer-loop metaprocedure** built from the already-validated "a rule writes a rule"
mechanism (§2 below): the metaprocedure decides which declared `Rule` to mint a live instance of, in what
region, and whether that instance is wired to a real axiom or to a supposition's cell (the §2 bubble
mechanism) — replacing `units/`'s tunnel/computation-unit apparatus entirely, hosted on `ugm/`'s substrate
instead of on a new one.

**What this leaves open, concretely, for whoever picks this up next:**
- `ugm/focus.py`'s demand-derived attention register (widen-only, extent never declared — see its own
  docstring) is a plausible seed for "which region the metaprocedure applies to" (§4.1's row 2 question),
  but this has not been checked, only noticed as plausible.
- `ugm/suppose.py`, `scope_crossing.py`, `scope_kinds.py` predate the §2 resolution and must be checked
  against it directly: does `ugm/`'s existing supposition machinery already support "wire a minted
  rule-instance to a scope's cell," or does that specific piece need building fresh on `ugm/`'s substrate?
  Not yet investigated — the single most concrete next step.
- `ugm/retraction.py`/`reconsider.py` (TMS-style retraction) — `units/`'s `revision-01` deleted this
  category on the argument "circuits stand, values revive from axioms each turn." Whether that argument
  transfers to a metaprocedure-outer-loop built on `ugm/`'s substrate, or whether `ugm/`'s retraction is
  still needed there, is a real open question, not automatically resolved by the decision above.
- `ugm/`'s 79 pre-existing test failures (§4.1) were never triaged against which modules this new direction
  actually touches (`production_rule.py`, `machine.py`, `lowering.py`, `focus.py`, `suppose.py` family) —
  worth doing before treating any of them as a clean base to build on.

---

**Everything below this line is the ORIGINAL handoff, unmodified, kept for the audit and the §2 reasoning
trail. Its own §4.3 recommendation ("don't revert wholesale... treat `ugm/`'s CNL grammar and
`focus.py`/`scope_tree.py` as harvesting targets") is SUPERSEDED by the resolution above — it correctly
identified the harvesting targets but wrongly assumed `units/`'s substrate would remain the foundation.**

---

**Status: handoff note, written 2026-07-30 because the conversation that produced it is about to run out of
context.** Written so a fresh session — with no memory of this conversation — can pick up the actual
strategic question rather than re-derive it. Read `arc_recap.md` first for the full narrative this session
sits on top of; this document only covers what's new since that document's last update and the one open
strategic question it raises.

---

## 1. Why this document exists

Working through a design question about complex structural goals ("build a car with a windshield, a
wiper, four wheels") led to a real, sharpened debate about whether this engine's tunnel/supposition
machinery is necessary at all, versus materializing hypothetical exploration directly as graph data. That
debate reached a real resolution (§2) that changes how "planning as rule-search" should be built. It also
surfaced a much bigger, adjacent question: `ugm/` (the retired, previous-generation engine, still living in
this same repo at `ugm/`) already has substantial, mature machinery for several things `units/` either
lacks entirely or has only a first slice of — a full CNL grammar/intake pipeline, procedures/tool dispatch,
attention/working-set (`focus.py`, `scope_tree.py`), retraction. The user asked, directly: given everything
learned this session, would it be a better route to revert to `ugm/`'s foundation rather than continue
building `units/` up to parity? This document is the evaluation material for that question — not the
answer, which needs a decision, not just an audit.

---

## 2. The tunnel/metaprocedure debate, and its resolution — read this even if you skip everything else

**The question that started it:** given "rules as data" and the structural-choice mechanism just validated
(`units/structural_choice_experiment.py` — commit a real candidate, detect a real conflict, exclude,
retry the next declared alternative, entirely as ordinary mutating rules, no supposition at all), do we
still need computation units and the tunnel/supposition mechanism? Could hypothetical exploration just be
materialized directly as graph data instead?

**Where this landed, precisely, because the reasoning matters more than the conclusion:**

1. `structural_choice_experiment.py` needed no tunnel because nothing in it was ever *unconfirmed* — "we
   tried kit_a" and "kit_a conflicts" are permanently, honestly true the instant they're derived. Nothing
   needed undoing. This is a real, large, validated slice of "hypothetical-shaped" reasoning that turns out
   to need zero hypothesis machinery — not a minor point, arguably the most practically valuable finding of
   this whole thread.
2. Genuine counterfactual reasoning (deriving consequences of an assumption that must not become real
   unless confirmed) is a *different* case, and the user proposed materializing it as an isolated
   "bubble" subgraph rather than using supposition/scope-as-support. My first objection — that a bubble
   can't stay isolated because `Merge`/`Identify` rewrite graph-wide, and a real counterfactual needs to
   reference real entities — was correct as far as it went, but it was answered by a sharper version of the
   proposal, and the sharper version wins.
3. **The winning resolution:** the "machinery" doesn't need to duplicate *content* (no duplicate sensor
   node, no duplicate evacuation-concept node). It duplicates *wiring* of one declared rule — using the
   already-validated "a rule writes a rule" mechanism
   (`tests/units/test_engine.py::test_a_rule_writes_a_whole_rule_with_nothing_authored_in_python`): a
   meta-rule reads the real business rule's own `pattern:`/`effect:` data and mints a **second instance**
   of the identical declared logic, wired to a supposition's cell instead of the real axiom. That second
   instance explores freely — fire and forget, its conclusions genuinely hypothetical, powered by the
   supposition per ordinary `powering()` semantics.
4. **Confirming the hypothesis needs no crossing at all**, which is the part I originally got wrong. I had
   been assuming "confirm" means taking the hypothesis-powered instance's output and forcing it into the
   real world — genuinely impossible, since `powering()`'s backward wire-walk taints anything downstream of
   a supposition unconditionally, by construction. But confirming a hypothesis actually just means *its
   antecedent becomes really true*, through ordinary means. The moment that happens, a **separate instance
   of the same declared rule**, wired to the real axiom from the start (sitting there the whole time, simply
   never firing because its real antecedent was never true), fires naturally and derives the same
   conclusion for real. Two independent firings of one piece of declared logic — one exploratory, one
   operative — never one derivation needing to cross a boundary.
5. **The "bulkhead" property the user asked for (no rule accidentally bridges the two) was never something
   to build** — `model.md`'s invariant 3 ("a unit sees only its own gates") already guarantees it. An
   ordinary business rule that the metaprocedure never deliberately rewires to a supposition's cell simply
   cannot see hypothetical content, full stop. The metaprocedure (the meta-rule minting the exploratory
   instance) *is* the bulkhead, and it's ordinary data, not a new kind of thing.

**What this means concretely:** the entire "explore, then commit" cycle — including genuine counterfactual
reasoning, not just the structural-choice case — looks buildable with **zero Python**, using only mechanisms
already validated in isolation (rule-writes-a-rule, scope-as-support, invariant 3), just never combined this
way and never exercised *repeatedly* as part of an ongoing exploration loop (every existing use of
rule-writes-a-rule is a one-shot, static compile).

**What is still genuinely unchecked, named rather than assumed:**

- A meta-rule that *repeatedly* mints fresh supposition-wired instances (not a one-shot compile) as part of
  an ongoing exploration — never built or probed.
- **"We still need to keep applying the meta rules in specific regions of the graph, not randomly"** — the
  user's own words, and a real, unresolved problem. Minting an exploratory instance of *every* declared
  business rule against *every* possible supposition is not tractable; something has to decide which rules
  and which region of the graph are relevant to a given exploration. `units/system1_experiment.py` already
  has a first, toy answer (attention as BFS from a seed, resemblance as attribute-key overlap, wiring
  proposed by score) — but it has never been connected to this metaprocedure idea, and `ugm/`'s `focus.py`
  (264 lines) and `scope_tree.py` (178 lines) are an already-built, more mature attention/working-set
  mechanism for exactly this problem, in the *other* engine. This is the single most concrete point of
  comparison for §4's decision, and worth reading side by side before building anything further.

---

## 3. What's new in `units/` this session that a fresh reader needs, beyond `arc_recap.md`

`arc_recap.md`'s own §5 was last updated after the CNL boundary's first slice. Since then, in this same
session:

- **`units/structural_choice_experiment.py`** — commit-detect-retract-retry for structural choice, no
  supposition, no Python, validated (3 checks green). Full writeup in its own docstring and in the prior
  conversation turn.
- **The tunnel/metaprocedure resolution above** — not yet built, but a real, load-bearing design
  conclusion: the "explore, then commit" cycle for genuine counterfactuals is very likely buildable with
  zero Python, via dynamic rule-instance minting. This changes what "planning as rule-search" should look
  like going forward, in `units/` specifically.
- **148 tests green** as of this session's last full run (144 + the structural-choice probe has its own
  `report()`-style checks, not yet ported to pytest — see `README.md`'s convention: probes stay standalone
  scripts, pytest coverage is added when a probe graduates into a reusable module, the way
  `force_probe_experiment.py` → `goal_rules.py` did).

---

## 4. The actual decision: revert to `ugm/`, keep building `units/`, or something between

### 4.1 What `ugm/` already has, concretely, that `units/` doesn't yet

| `ugm/` module | what it is | `units/` equivalent |
|---|---|---|
| `ugm/cnl/` (17 files: `grammar.py`, `grammar_intake.py`, `forms.py`, `procedure_surface.py`, `query.py`, `rule_graph.py`, `suppose_surface.py`, `surface.py`, `uncertainty.py`, `universal.py`, `why_surface.py`, `cause_surface.py`, `comparative.py`, `define_surface.py`, `authoring.py`, `form_authoring.py`, `machine_rules.py`) | a full CNL grammar/intake pipeline, years (in project-time) more developed | `units/cnl.py` — one file, ~180 lines, first real slice, deliberately minimal (no labels, no degree, no refusal yet) |
| `ugm/focus.py`, `ugm/scope_tree.py` | attention / working-set management — deciding what's "in scope" for retrieval and reasoning | `units/system1_experiment.py` — a toy prototype (BFS + attribute-overlap resemblance), never connected to planning |
| `ugm/production_rule.py`, `ugm/rule_control.py` | rule execution/control machinery | `units/engine.py`'s `StandingUnit`/`Network`, architecturally different (data-is-the-substrate vs. this being a more classical production-system control layer) |
| `ugm/retraction.py`, `ugm/reconsider.py` | TMS-style retraction and demand-driven revision of stale NAF conclusions | **deliberately deleted** in `units/`'s foundational design (`revision-01`: "circuits stand, values revive from axioms each turn... deletes ALL retraction/TMS machinery") — this is not a gap, it's a rejected approach, on the record |
| `ugm/suppose.py`, `ugm/scope_crossing.py`, `ugm/scope_kinds.py` | the previous generation's hypothesis/scope handling | superseded by `units/`'s scope-as-support (`revision-02`), which this session's tunnel debate (§2) just extended further |
| procedures/tool dispatch (referenced repeatedly across this arc as *"the old engine's already-validated suspend-and-dispatch mechanism"*) | real side-effecting tool calls, suspend/resume | **not built at all in `units/`** — `units/prohibition_rules.py`'s `executed` attribute is an explicit stand-in, named as such |
| `ugm/possibility.py` | the possibilistic/band layer | **already harvested** — `units/band.py`'s own header: *"Harvested from the deleted `units/band.py`. The scale and the min-join are unchanged... its central argument is not."* This is the precedent for "port the finding, not the code," already done once |
| causation (`ugm`'s propagation-schema finding) | — | **already harvested as a finding**, not code — `causation-core-was-sugar`, reconfirmed via `closed_class_rechallenged.md` this session |
| transitivity (`facts-as-truth-bearers-built`'s predicate-variable matching) | — | **already harvested as a finding, with a genuine new extension** — `units/transitivity_probe_experiment.py`, needed a small, real `units/engine.py` change (`Attribute.value`/`Link.role` reading a bound `AttrVar`) that `ugm`'s own mechanism (`key_reg`, a dynamic-key Python object) doesn't have an equivalent of |

**`ugm/`'s test status, re-verified this session** (the run was backgrounded for its ~9-minute duration,
result checked after this document's first draft): **79 failed, 983 passed** (1062 total). This exactly
matches the count memory already recorded from an earlier point in this project's history ("the `grammar`
branch has 79 pre-existing failures") — the failure count has been stable, not drifting, which is worth
knowing either way: it means `ugm/`'s 983 passing tests are a real, standing baseline, not a stale number,
but the 79 failures are also a known, long-standing, unaddressed debt, not new breakage from this session.
Which 79, and whether any bear on the specific mechanisms this handoff cares about (the CNL grammar,
`focus.py`/`scope_tree.py`), was not investigated — worth doing before treating any specific `ugm/` module
as "ready to harvest from" rather than "worth reading for the finding."

### 4.2 The actual tradeoff, stated plainly

**`units/` is not behind `ugm/` by accident.** Every one of `units/`'s foundational bets —
substrate-inversion (data is the substrate, computation a transient circuit), scope-as-support (no
hypothesis labels, the tunnel), "a rule is data, a rule writes a rule," the small confirmed closed algebra
— was arrived at by finding `ugm/`'s corresponding mechanism fragile, over-general, or an unreachable
Python island, and deliberately rejecting it (`revision-01`, `revision-02`, `causation-core-was-sugar`, this
session's whole closed-class rechallenge). Reverting to `ugm/`'s codebase wholesale would mean either (a)
giving up those bets — reintroducing retraction/TMS, Python-hosted business-rule banks
(`assemble_facts`/`run_bank`), and losing the tunnel-as-wiring mechanism this very session extended
further — or (b) re-porting all of `units/`'s foundational mechanisms *onto* `ugm/`'s substrate, which is
close to rebuilding `units/` a third time, just started from the other codebase.

**But `ugm/` clearly has real, mature machinery worth having** — the CNL grammar especially. `units/cnl.py`
is a genuine first slice; `ugm/cnl/`'s 17 files represent a much more complete answer to problems `units/`
hasn't even reached yet (labels/coindexing, degree, negation marking, refusal, a real procedure surface).
Rebuilding all of that from scratch, the way `units/cnl.py` was just built from scratch, is real, avoidable
cost if `ugm/`'s grammar findings (not necessarily its code) can be harvested the way causation, band, and
transitivity already were.

### 4.3 Recommendation, offered as a starting position for the next session to weigh in on, not a decision

**Don't revert wholesale.** The foundational bets are validated, load-bearing, and this session's tunnel
resolution (§2) is a direct, positive result of them, not despite them. Reverting would discard exactly the
things this arc has spent the most effort confirming.

**Do treat `ugm/`'s CNL grammar and `focus.py`/`scope_tree.py` as the next, concrete harvesting targets** —
the same discipline already applied to `band.py`, causation, and transitivity: read `ugm/`'s mechanism,
identify what's a genuine *finding* (a shape, a distinction, a worked example) versus what's an artifact of
its Python-hosted architecture, and port the finding onto `units/`'s foundation, probing it the same way
every other port in this arc was probed rather than assumed to transfer.

**Concretely, in priority order, regardless of which way this decision goes:**

1. Probe the tunnel/metaprocedure resolution from §2 directly — a meta-rule minting a fresh
   supposition-wired instance of a declared business rule, repeatedly, as part of an exploration, with
   confirmation as a separately-wired real firing. This is the most load-bearing unchecked claim in this
   handoff.
2. Read `ugm/focus.py` and `ugm/scope_tree.py` side by side with `units/system1_experiment.py` and decide
   whether "which region of the graph the metaprocedure applies to" is a finding worth porting, or a
   different problem than it looks like from the `units/` side.
3. Read `ugm/cnl/grammar.py` and `ugm/cnl/procedure_surface.py` specifically (not the whole `cnl/`
   directory at once) against `units/cnl.py`'s current, deliberately-minimal scope, and decide whether the
   next CNL-boundary growth step (labels/coindexing, refusal, or the `author` rule-compiling case already
   deferred in `units/author_rules.py`) has a directly portable `ugm/` finding behind it.

---

## 5. Pointers

- `arc_recap.md` — the full narrative up to the CNL boundary's first slice. Read first.
- `STATUS.md` — granular current-work tracker.
- `README.md` — the document/code map, including the CNL-boundary section.
- This document's own future: once the decision in §4 is actually made, fold the outcome into
  `arc_recap.md`'s §5 as the next Act, and retire this document to `attic/` with a row in `attic/README.md`
  saying which way it went and why — the same discipline every other resolved question in this project
  follows.

# Agentic scenario catalog — the completeness check, complementing the sieve

**Status: Phase A working document, 2026-07-28; scenarios 1/3/10 and §11 revised, §12 added, 2026-07-29.**
References `closed_class_inventory.md` (the soundness-side
check: does the declared set compose without leaking, via `sieve.py`) and `cnl_engine_goal_plan.md`. This
document is the other check — completeness: does the declared set cover what an agent doing real work actually
needs to say. Neither check substitutes for the other.

**Updated 2026-07-30.** Two things changed since this catalog was last revised (07-29) and are folded in
below rather than flagged separately: (1) `closed_class_rechallenged.md` confirmed causation, identity, and
quantification's cursor case are open content read by a generic meta-rule, not closed-class mechanisms
needing their own design (scenarios 2, 7, 10, §11); (2) the goal/subgoal machinery §11 used to list as
"designed, not built" is now **built** (`goal_machinery.md`, `units/goal_experiment.py`,
`units/quantification_cursor_experiment.py`, `units/meta_concept_unification_experiment.py`) — every
verdict that depended on it is upgraded accordingly. The scenarios themselves are unchanged; only the
verdicts move.

## 0. Why this document exists

`closed_class_inventory.md` asks, of each proposed grammatical building block (**form** — see `glossary.md`),
whether it combines with the others without breaking. It never asks whether the *set of forms itself* is big
enough. A form nobody has thought to write yet can't leak, and won't show up in that document's tables at all —
so a second, independent check is needed: pick real tasks an agent would actually need to do, write out in plain
English what each one needs to *say*, and see whether the current closed class has the pieces for it.

That's what this document does. Each of the ten scenarios below is a short, realistic agent task (e.g. *"if a
customer is VIP and spent over $500, apply a 10% discount"*). For each, the method is: **state the need in one
line → break it down into what CONTENT/FORCE/LEVEL commitments it actually requires (see `glossary.md` for what
those three mean) → look up each requirement's current status in `closed_class_inventory.md` → verdict.** A
scenario's verdict is one of: the pieces it needs already exist and are confirmed (**COVERED**), some pieces
exist and some don't (**PARTIAL**), or a genuinely new form is needed and hasn't been written yet (**GAP**).

Concretely: scenario 1 below needs *conditionality* ("if... then..."), which `closed_class_inventory.md` §5
records as **STRUCTURALLY BLOCKED** — so this scenario's decomposition is what turns an abstract inventory gap
into a concrete "yes, real agent work actually needs this, here's the sentence that needs it." That's the value
this document adds that the inventory alone can't: it prioritizes which gaps matter, using actual tasks instead
of guessing. §11 at the bottom rolls all ten scenarios up into one ranked list of what to build next.

⚠ **This is a synthetic corpus, not real usage**, and carries the same caveat `form_inventory.md` §3 puts on
intuition-based form selection: five for five wrong, historically, when judged by guessing rather than measuring.
Treat every "gap" below as a hypothesis to prioritize, not a proven requirement — and replace or supplement this
catalog with real usage the moment any exists, the same discipline the residue log (`forms_discourse.md` §9)
already applies to tier 3.

**Method, per scenario:** describe the need in one line → decompose into what CONTENT/FORCE/LEVEL/relational
commitments it requires → check against `closed_class_inventory.md`'s current status per form → verdict.

---

## 1. Conditional business-rule evaluation

*"If a customer is VIP and spent over $500, apply a 10% discount."*

| requires | status |
|---|---|
| conditionality (`when`/`then`) | **STRUCTURALLY BLOCKED** — discharge has no mechanism (`cnl_engine_goal_plan.md` §3) |
| degree/threshold (`>$500`) | CONFIRMED |
| negation (exceptions) | CONFIRMED |
| quantification (implicit — *every* VIP customer) | **worked out 2026-07-29** (`closed_class_inventory.md` §8) — this is case (a), universal-as-application, and is **free**: an ordinary rule with a free variable already fires once per match, no new form. The *implicit* open-domain claim ("is it true every VIP customer gets it") is case (d) — a genuine, likely-permanent epistemic limit, not a form gap |
| roles (agent/patient for the discount action) | tier 3, already supported |

**Verdict: PARTIAL, revised 2026-07-29.** Conditional discharge is still a real blocker. Quantification, once
decomposed, turned out **not** to be one — the discount-application reading this scenario actually needs is
already free; only asking "is it true for *every* customer" (which the scenario doesn't actually require) would
hit the open-domain limit.

---

## 2. Multi-step procedure execution

*"Onboard a customer: verify identity, then create the account, then send the welcome email."*

| requires | status |
|---|---|
| sequencing/ordering | **free, not a form** — a procedure is a goal decomposition plus one `then:` sequencing edge among the children (`units/meta_concept_unification_experiment.py`), confirmed built, not merely likely |
| goal/subgoal/expectation structure | **built** — `goal_machinery.md`, `units/goal_experiment.py`; a procedure/question/prohibition all reduce to this one shape (`units/meta_concept_unification_experiment.py`) |
| causation ("this step enables the next") | **resolved as sugar** — a generic `propagates` meta-schema plus one declared fact, zero engine primitive (`causation-core-was-sugar`; reconfirmed as part of `closed_class_rechallenged.md`) |
| tool-call outcome (success/failure/error) | **covered without a new form** — `positive`/`negation` over a `succeeded`-shaped predicate |

**Verdict: COVERED.** All four requirements resolved — none needed a new closed-class form; two (sequencing,
goal/subgoal structure) needed the goal machinery, now built.

---

## 3. Aggregation / computation offload

*"What's the average order value for VIP customers this month?"*

| requires | status |
|---|---|
| quantification (over the customer set) | **resolved 2026-07-29** (`closed_class_inventory.md` §8) — gathering "VIP customers' orders this month" is case (b), free via `solve()` already returning every current match at once (confirmed against the real engine's `assemble()`), **provided the month is already complete** (a closed set checkable in one revive). An ongoing month is case (d)'s hedge, not a hard fact |
| bounded reference ("this month", "VIP customers") | open, and specifically **Phase D blocked** — `forms_discourse.md` §10.3's flagship reference case is already known unmeasurable until the surge detector is fixed. Worth rechecking against Phase D's 2026-07-29 partial closure rather than assuming still fully stuck |
| aggregation itself (average, sum, count) | **resolved 2026-07-29 — delegated tool call, no new form.** The engine's role is gather (case (b), free) and read-back; the arithmetic is ordinary computation with no epistemic content, handed to the already-designed procedure/tool-call arc. One real, small mechanism gap found doing this, not specific to aggregation: ordinary units fire once per match, aggregation wants one firing over the *whole* current match set — worth a small addition (a unit disposition/effect consuming `solve()`'s whole result), not a new form (`closed_class_inventory.md` §8) |

**Verdict: PARTIAL, revised 2026-07-29 — no longer the most unresolved of the ten.** Both of the two content gaps
(quantification, aggregation) dissolved into either "already free" or "tool-call glue, one small mechanism gap."
What's left is genuinely just the bounded-reference/Phase-D dependency, and worth rechecking now that Phase D got
a partial closure — this scenario may be closer to COVERED than GAP.

---

## 4. Refusal / clarification on ambiguity

*"The rule doesn't specify what happens at exactly $500 — ask."*

| requires | status |
|---|---|
| force = ask | CONFIRMED |
| degree/threshold, specifically boundary inclusivity | CONFIRMED, though boundary handling (`≥` vs `>`) may need a closer look |
| ambiguity marking | already designed at the CNL/translator boundary (`cnl.md` §1's refusal contract) — not itself a closed-class content form |

**Verdict: MOSTLY COVERED.** No new form needed; this scenario is a check that existing mechanisms interoperate
correctly, not a gap-finder.

---

## 5. Honest exhaustion reporting

*"I can't tell if this customer qualifies — their order history is incomplete."*

| requires | status |
|---|---|
| the four-outcome contract (`satisfied`/`starved`/`out_of_fuel`/`awaiting`/`surged`) | designed (`model.md` §7-8), a systemic engine property rather than a CONTENT/FORCE/LEVEL form |
| honest depth/exhaustion reporting specifically | **known broken** — this scenario's failure mode is exactly the surge detector bug (`forms_discourse.md` §10.3, Phase D) |

**Verdict: COVERED IN DESIGN, BROKEN IN IMPLEMENTATION.** No inventory gap — this is a pure Phase D item, and
this scenario is the clearest possible statement of why Phase D matters for real agentic use, not just as an
abstract architecture concern.

---

## 6. Escalation to a human

*"Escalate if the discount would exceed $1000."*

| requires | status |
|---|---|
| command/author force | CONFIRMED — `command` resolved as a genuine force value (`closed_class_inventory.md` §3) |
| conditionality | **same Phase-B blocker as scenario 1** |
| degree/threshold | CONFIRMED |

**Verdict: PARTIAL**, for the same reason as scenario 1 — a second, independent confirmation that the
conditional's discharge mechanism is the single highest-leverage blocker across this catalog so far (appears in
2 of 6 scenarios reviewed to this point).

---

## 7. Drift detection → recovery

*"The outcome doesn't match what the plan expected — flag it and trigger recovery."*

Worked through in full in the preceding discussion. Decomposes into:

| requires | status |
|---|---|
| identity/equality (expected vs. observed) | **resolved as sugar, 2026-07-30** — `units/identity_merge_probe_experiment.py`: the engine's `Merge` effect plus one generic rule keyed on a declared identity slot, no new form. What's still open is the *unrelated*, still-cited depth-4/5 obstacle for definite-description resolution generally (`forms_discourse.md` §10.3, Phase D) — deciding this specific scenario's expected-vs-observed identity does not hit it |
| expectation structure | already exists (`model.md` §8), and its goal/subgoal shape is now built, not just designed |
| a new force value (`flag`/`alert`, parallel to `ask`'s `raised`) | **proposed, not yet built or sieved** |

*Not* mirativity — the linguistic category was the wrong vehicle for a real need it correctly pointed at; see
the discussion preceding this catalog for the full reasoning.

**Verdict: PARTIAL, revised 2026-07-30.** Identity resolved. What remains is authoring one new force value —
small, well-specified, not yet built.

---

## 8. Explaining a conclusion / audit trail

*"Why did you decide X?"*

| requires | status |
|---|---|
| level = language (a claim about a prior claim/derivation) | CONFIRMED — `LANGUAGE` already exists and fits this well |
| provenance/source marking | **`evidential`'s `sourced` marker — re-tested here, and unlike `mirative`, it survives.** This scenario gives evidentiality a genuine agentic use (tracking whether a fact came from a direct tool query, an inference, or a stated assumption) that mirativity never got in scenario 7 |
| reference to a specific prior derivation | open, tied to §10.3 |

**Verdict: PARTIAL, and a positive result worth flagging explicitly** — this is the scenario-driven method
working as intended in both directions: it killed `mirative` in scenario 7 and it **rescues** `evidential` here,
which is exactly the discriminating power a linguistic catalog alone couldn't provide.

---

## 9. Recovering from a failed tool call

*"The API call failed — retry, or escalate."*

Composes almost entirely from scenarios 5 (outcome reporting) and 7 (flag/recovery) rather than introducing a
new requirement.

**Verdict: LIKELY COVERED once 5 and 7 are built** — useful primarily as a composition test case for whether
those two mechanisms actually interoperate, not as an independent source of gaps.

---

## 10. Batch evaluation across a set

*"Evaluate this rule for every customer in the queue."*

| requires | status |
|---|---|
| quantification | **built, 2026-07-29 — this is case (c)** (`closed_class_inventory.md` §8): checking each queue member needs more than one revive (real per-member work, possibly a tool call), so it needs a cursor that survives across revives. `units/quantification_cursor_experiment.py` built exactly that, using `model.md` §8's goal/subgoal/procedure shape — not a quantification-specific mechanism |
| roles for iteration | tier 3, already supported |

**Verdict: COVERED, revised 2026-07-30 — the gap that moved in 07-29's revision is now closed.** Both
requirements resolved; the goal/subgoal cursoring machinery this scenario needed is built and this scenario
is its worked example.

---

## 11. Priority ranking, read off the ten scenarios

**Revised 2026-07-30 — goal/subgoal machinery built; causation and identity/merge resolved as sugar.** Three
of this table's four live rows from the 07-29 revision are now closed. What's left is genuinely narrower.

| gap | appears in | priority signal |
|---|---|---|
| **conditional discharge (Phase B)** | scenarios 1, 6 (2 of 10) | the one remaining real, structural blocker — shelved, not fixed, and still the highest-leverage open item in this whole catalog |
| **bounded/definite reference generally** (Phase D — a *different*, broader problem than scenario 7's now-resolved identity/merge) | scenarios 3, 8 | still gated behind the surge detector; genuinely unresolved, not reclassified this round |
| **new `flag`/`alert` force** | scenario 7 (and 9 by composition) | well-specified, ready to author |
| **`evidential` (rescued)** | scenario 8 | keep — do not drop, unlike `mirative` |
| **`mirative`** | none of the ten | drop from active priority |
| ~~goal/subgoal machinery~~ | scenario 10; justification (§12); System 1 (`computation_units.md` §5) | **built** — `goal_machinery.md`, `units/goal_experiment.py`, `units/quantification_cursor_experiment.py`, `units/meta_concept_unification_experiment.py` |
| ~~identity/equality (narrow sense — same referent)~~ | scenario 7 | **resolved, not a gap** — `units/identity_merge_probe_experiment.py`. Distinct from the broader bounded-reference row above, which is still open |
| ~~causation~~ | scenario 2 | **resolved, not a gap** — confirmed sugar |
| ~~quantification~~ | scenarios 1, 3, 10 | **resolved, not a gap** — every case built or dissolved; only case (d)'s open-domain limit remains, and it's an epistemic fact, not a form gap |
| ~~aggregation (scoping question)~~ | scenario 3 | **resolved, not a gap** — delegated tool call |

**Recommended next step:** conditional discharge is now the single clearest remaining structural blocker in
this catalog, unchanged in status since 07-28 while everything that used to compete with it for priority has
resolved. The broader bounded/definite-reference problem (Phase D) is the other genuinely open item, and it
is a systemic engine fix, not a per-scenario content gap. Both are already tracked outside this document —
the concrete next step for the *project*, not this catalog specifically, is `arc_recap.md` §5's item 2: the
causal-fact→plan and norm→requirement→satisfies meta-rule design this whole rechallenge was in service of.

---

## 12. Considered and dissolved, 2026-07-29: "justification" as its own need

Raised in conversation, checked rather than assumed: does an agent ever need to *justify* a goal ("pursue X
because Y")? `model.md` §8 already has this — goals form a lineage, and "that lineage is what carries the
explanation... an ordinary relation between ordinary goals." Justifying a goal is just stating its parent in
that lineage, the same move as provenance-is-free (`model.md` §1) one plane up. **Not a new scenario, not a new
form** — full writeup in `closed_class_inventory.md` §10. Left open there: justifying a *belief* rather than a
goal is a different, likely `causation`-shaped question.

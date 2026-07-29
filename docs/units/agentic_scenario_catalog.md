# Agentic scenario catalog — the completeness check, complementing the sieve

**Status: Phase A working document, 2026-07-28; scenarios 1/3/10 and §11 revised, §12 added, 2026-07-29.**
References `closed_class_inventory.md` (the soundness-side
check: does the declared set compose without leaking, via `sieve.py`) and `cnl_engine_goal_plan.md`. This
document is the other check — completeness: does the declared set cover what an agent doing real work actually
needs to say. Neither check substitutes for the other.

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
| sequencing/ordering | **likely free, not a form** — `model.md` §5 realizes ordering as wiring topology (unit A's output feeds unit B), so "before/after" may not need its own CONTENT entry at all. Worth confirming rather than assuming, but this looks like a case where the architecture already supplies it structurally |
| goal/subgoal/expectation structure | designed (`model.md` §8), not yet run through the sieve as a form — it lives at a different tier (procedure/activity structure, `forms_discourse.md` §10.2, still open) |
| causation ("this step enables the next") | NOT YET FORMALIZED |
| tool-call outcome (success/failure/error) | **likely covered without a new form** — probably just `positive`/`negation` over a `succeeded`-shaped predicate, not a new axis |

**Verdict: PARTIAL.** One genuine gap (causation); one place where the architecture may already supply the need
for free (sequencing) — worth confirming, not assuming, before spending design effort there.

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
| identity/equality (expected vs. observed) | NOT YET FORMALIZED — now concretely motivated rather than a citation from an old catalog row |
| expectation structure | already exists (`model.md` §8) |
| a new force value (`flag`/`alert`, parallel to `ask`'s `raised`) | **proposed, not yet built or sieved** |

*Not* mirativity — the linguistic category was the wrong vehicle for a real need it correctly pointed at; see
the discussion preceding this catalog for the full reasoning.

**Verdict: GAP**, but an unusually well-specified one — two concrete, ready-to-author candidates.

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
| quantification | **resolved 2026-07-29 — this is case (c)** (`closed_class_inventory.md` §8): checking each queue member likely needs more than one revive (real per-member work, possibly a tool call), so it needs a cursor that survives across revives. That's `model.md` §8's goal/subgoal/procedure shape, already designed, **not yet built** — not a quantification-specific mechanism |
| roles for iteration | tier 3, already supported |

**Verdict: GAP, revised 2026-07-29 — but the gap moved.** Not "quantification is unformalized" any more; it's
"goal/subgoal machinery (`model.md` §8) is designed but not built," which this scenario needs and cases (a)/(b)
above do not. That's a sharper, smaller, more buildable gap than the one originally recorded here.

---

## 11. Priority ranking, read off the ten scenarios

**Revised 2026-07-29 — quantification and aggregation resolved, not just prioritized.** Both were worked out
against the real engine and the design docs (`closed_class_inventory.md` §8) rather than left as "check this
next." Neither turned out to be a missing closed-class form.

| gap | appears in | priority signal |
|---|---|---|
| **goal/subgoal machinery (`model.md` §8), unbuilt** | scenario 10's quantification case (c); also justification (§12 below) and System 1's associative wiring (`computation_units.md` §5) | **new highest-leverage item** — three independent findings now converge on this one piece of unbuilt design |
| **conditional discharge (Phase B)** | scenarios 1, 6 (2 of 10) | already tracked, now independently reconfirmed twice |
| **identity/equality** | scenarios 3, 7, 8 (3 of 10) | now the clearest remaining cross-cutting content gap — quantification no longer ties with it |
| **causation** | scenario 2 (1 of 10) | real, but singly-attested so far in this catalog |
| **new `flag`/`alert` force** | scenario 7 (and 9 by composition) | well-specified, ready to author |
| **`evidential` (rescued)** | scenario 8 | keep — do not drop, unlike `mirative` |
| **`mirative`** | none of the ten | drop from active priority — the scenario that motivated re-examining it (drift detection) turned out not to need it |
| ~~quantification~~ | scenarios 1, 3, 10 | **resolved, not a gap** — splits into free/application, free/bounded-closed, needs-goal-machinery/multi-turn, and open-domain-hedge-limit. See `closed_class_inventory.md` §8 |
| ~~aggregation (scoping question)~~ | scenario 3 | **resolved, not a gap** — delegated tool call, no intro/elim pair needed. One small mechanism gap found (an aggregating unit disposition), tracked in `closed_class_inventory.md` §8, not a scoping question any more |

**Recommended next step, revised:** identity/equality is now the clearest remaining cross-cutting content gap.
But goal/subgoal machinery is arguably higher-leverage — it's no longer just scenario 10's problem, it's also
what justification (§12, "considered and dissolved") and the substitution experiment's wiring-cost fix
(`computation_units.md` §5) both depend on. Worth weighing that convergence against identity/equality's own
three-scenario cross-cutting signal before picking.

---

## 12. Considered and dissolved, 2026-07-29: "justification" as its own need

Raised in conversation, checked rather than assumed: does an agent ever need to *justify* a goal ("pursue X
because Y")? `model.md` §8 already has this — goals form a lineage, and "that lineage is what carries the
explanation... an ordinary relation between ordinary goals." Justifying a goal is just stating its parent in
that lineage, the same move as provenance-is-free (`model.md` §1) one plane up. **Not a new scenario, not a new
form** — full writeup in `closed_class_inventory.md` §10. Left open there: justifying a *belief* rather than a
goal is a different, likely `causation`-shaped question.

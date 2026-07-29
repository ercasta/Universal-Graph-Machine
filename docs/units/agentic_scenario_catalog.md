# Agentic scenario catalog — the completeness check, complementing the sieve

**Status: Phase A working document, 2026-07-28.** References `closed_class_inventory.md` (the soundness-side
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
| quantification (implicit — *every* VIP customer) | NOT YET FORMALIZED |
| roles (agent/patient for the discount action) | tier 3, already supported |

**Verdict: PARTIAL.** The pieces that exist are solid; the two blockers (conditional discharge, quantification)
are both already-tracked gaps, and this scenario is independent confirmation that both matter, not new news.

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
| quantification (over the customer set) | NOT YET FORMALIZED |
| bounded reference ("this month", "VIP customers") | open, and specifically **Phase D blocked** — `forms_discourse.md` §10.3's flagship reference case is already known unmeasurable until the surge detector is fixed |
| aggregation itself (average, sum, count) | **⚠ genuinely unresolved scoping question, not just a gap** |

**The scoping question is the real finding here.** It's not obvious "average" belongs in the closed class at
all — arithmetic aggregation is a well-defined operation, not vague/open-class content, but it's also not
obviously a linguistic form the way negation or conditionality are. This may be better modeled as a delegated
tool-call (the engine hands the operation to an external, ordinary computation and reasons about the *result*)
rather than as something requiring its own intro/elim pair. **This needs a decision, not more sieving** —
recommend resolving it before writing any entry.

**Verdict: GAP, and the most unresolved of the ten** — one real content gap (quantification), one Phase-D
dependency, and one open architectural question about scope.

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
| quantification | same gap as scenarios 1 and 3 |
| roles for iteration | tier 3, already supported |

**Verdict: GAP**, and the third of ten scenarios needing quantification — the strongest signal in this catalog
for where to prioritize next.

---

## 11. Priority ranking, read off the ten scenarios

| gap | appears in | priority signal |
|---|---|---|
| **quantification** | scenarios 1, 3, 10 (3 of 10) | highest — cross-cutting, no known Phase B blocker yet identified, should be checked next |
| **conditional discharge (Phase B)** | scenarios 1, 6 (2 of 10) | already tracked, now independently reconfirmed twice |
| **identity/equality** | scenarios 3, 7, 8 (3 of 10) | tied with quantification — equally cross-cutting |
| **causation** | scenario 2 (1 of 10) | real, but singly-attested so far in this catalog |
| **aggregation (scoping question)** | scenario 3 | needs a decision, not more inventory |
| **new `flag`/`alert` force** | scenario 7 (and 9 by composition) | well-specified, ready to author |
| **`evidential` (rescued)** | scenario 8 | keep — do not drop, unlike `mirative` |
| **`mirative`** | none of the ten | drop from active priority — the scenario that motivated re-examining it (drift detection) turned out not to need it |

**Recommended next step:** quantification and identity/equality are tied as the highest-leverage gaps — both
cross-cutting, both currently unblocked by any known Phase B issue. Suggest picking one to draft an entry for
next, sieve it, and use that as the template for the other.

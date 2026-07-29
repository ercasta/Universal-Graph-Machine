# The closed-class inventory, consolidated — Phase A working document

**Status: Phase A in progress, 2026-07-28.** This is `cnl_engine_goal_plan.md` Phase A: finalize the closed-class
inventory, abstractly. It consolidates what is scattered across `forms_discourse.md` §2.2/§6/§9,
`docs/design/form_inventory.md` (superseded except for the surviving findings named in `forms_discourse.md` §12),
and `units/forms.py`/`units/sieve.py` (the runnable probe) into one table with one status per entry.

## 0. Why this document exists

The system understands language through a small, fixed vocabulary of grammatical building blocks — a **closed
class** (see the glossary linked below) — plus an unbounded set of ordinary words ("customer," "discount,"
"park") that it never tries to define, only names. The closed class is what actually does the reasoning: it's
how the engine knows that *"the customer did NOT qualify"* forbids also concluding *"the customer qualified,"*
or that *"spent over $500"* is a different, comparable kind of claim from *"spent exactly $500."* Get the closed
class wrong — missing a piece, or with two pieces that quietly contradict each other when combined — and the
engine either can't say something a real request needs, or worse, reasons its way to a wrong answer without
anyone noticing.

This document is that class's **soundness check**: for every proposed building block ("form"), does it combine
with every other one *without silently letting the engine conclude something false*? It does not ask whether the
class is *big enough* — that's `agentic_scenario_catalog.md`'s job, the completeness-side check. A
form can pass this document's test and still be missing from the class entirely, if nobody's written it yet; and
a form can be written and even useful, and still fail here, because combined with some other form it produces a
**leak** (concludes something it should never be allowed to conclude — see glossary). The tool that actually runs
these combinations is `units/sieve.py`, hence "the sieve" throughout.

**Worked example, to make "form" and "leak" concrete before the tables below get abstract.** Take the sentence
*"the customer did not qualify."* `negation` is a form: it's what licenses writing "not," and what forbids you
from also concluding the unnegated claim ("the customer qualified") while it holds. Now take *"the customer
barely qualified."* `degree` is a different form — it doesn't flip true/false, it says *how much*. These two
forms turn out to write different fields (`negation` writes `polarity`, `degree` writes `strength`), so in
principle they should be freely combinable: *"the customer did not barely qualify"* should behave sensibly. The
sieve actually tried this combination and found it **did not** — `degree ∘ negation` was the one measured leak
in the confirmed baseline (§2 below) before it was fixed. That's what this whole document is doing, form by
form: not debating in the abstract whether the inventory *seems* complete, but running every pair through the
engine and recording what actually happened.

If the vocabulary above (**closed class**, **form**, **slot**, **leak**, **CONTENT/FORCE/LEVEL**, **SEED** /
`CANDIDATES`) is unfamiliar, read `glossary.md` first — every term below is used exactly as defined there, and
this document does not redefine them inline.

**This is the soundness-side check only.** `agentic_scenario_catalog.md` is the complementary completeness-side
check — does this inventory cover what an agent doing real work needs to say — and it has already reprioritized
this document's own open items (mirative dropped, quantification and identity promoted). Read both together. Numbers
below are from a **live run against the current `units/` code**, not recalled from memory — memory's own
`sieve-measures-the-axes.md` cites slightly different counts (8 slots vs 3 axes for candidates; this run measures
9 vs 3), which is itself the expected behavior of a growing `CANDIDATES` tuple, not a contradiction. Re-run
`axis_audit()` before trusting any number here past the next code change.

---

## 1. Status legend

| status | meaning |
|---|---|
| **CONFIRMED** | in `SEED`, sieve-tested, its own hypothesis (if it had one) resolved |
| **RESOLVED HYPOTHESIS** | in `CANDIDATES`, sieve-tested, the code comment's open question has a measured answer |
| **OPEN HYPOTHESIS** | in `CANDIDATES`, sieve-tested, but nothing yet competes with it, so its slot assignment is unconfirmed by exclusion |
| **STRUCTURALLY BLOCKED** | passes as a *form* but its Phase B realizability check failed — `cnl_engine_goal_plan.md` §3 |
| **NOT YET FORMALIZED** | named in prose across the docs, no `Form` entry exists to sieve at all |

---

## 2. CONFIRMED — `SEED`

| name | example | declared axis | measured slot | entry-format completeness | note |
|---|---|---|---|---|---|
| `positive` | "the customer qualified" | content | `positive` (shared with `negation`) | intro / elim / commits — no `forbids` (nothing to forbid for the baseline) | the reference cell; `seed_is_sound()` depends on this being clean |
| `negation` | "the customer did **not** qualify" | content | `positive` slot | intro / elim / commits / forbids — full | "the operator case for A1"; the one form with a real `forbids` from day one |
| `degree` | "the customer **barely** qualified" | content | its own slot | intro / elim / commits / forbids — full | **the form the one measured leak (`degree ∘ negation`) was found on** |
| `assert` | "the customer qualified." (a statement) | force | `assert` slot (shared with `ask`) | intro / elim (none — default) | the default force |
| `ask` | "**did** the customer qualify?" | force | `assert` slot | intro / elim / commits / forbids — full | `forms_discourse.md` §8's worked failure lives here (map the question, then assert it) |
| `world` | a claim about the customer | level | `world` slot (shared with `language`) | intro only | the default level |
| `language` | "**that rule** about VIP customers is wrong" — a claim about a claim, not about the world | level | `world` slot | intro / elim / commits / forbids — full | the use/mention test of whether LEVEL is a real axis |

**Measured (this run):** `axis_audit(SEED)` → **4 slots vs 3 declared axes.** `content` splits into `{positive, negation}` and `{degree}` — confirming `forms_discourse.md`'s own §2.2 three-axis table cannot be taken as one slot per row; `positive`/`negation` compete (same field, `polarity`) while `degree` writes a different field (`STRENGTH`) and so gets its own slot. This matches `sieve-measures-the-axes.md`'s prior finding exactly.

**Also independently confirmed via `units/smt_sieve.py`** (`cnl_engine_goal_plan.md` §4): the `degree ∘ negation` leak and its guarded fix are now proven over the entire symbolic domain via Z3, not just sampled — the first use of a decision procedure rather than enumeration anywhere in this project's form verification.

---

## 3. RESOLVED HYPOTHESES — `CANDIDATES \ SEED`, where the sieve settled the code's own open question

Every one of these carries a `⚠ HYPOTHESIS` note in `units/forms.py` written by whoever added it. The live run
resolves four of them. Concretely: someone proposed `deny` ("the customer **refuses to say** they qualify") as
its own force value, distinct from `assert`+`negation` combined ("the customer **is not** qualified"). The sieve
tested whether the two actually behave differently once wired into the engine — they don't, so `deny` is retired
as a duplicate of `negation`, not entered as a new form.

| name | code's own question | measured answer | resolution |
|---|---|---|---|
| `deny` | *"is `deny` = negation ∘ assert, i.e. not a force at all?"* | **groups into the `positive`/`negation` slot** — and `factorization_audit(CANDIDATES)` independently confirms `deny` factors into `{negation}` alone (and vice versa: `negation` factors into `{deny}`) | **yes — `deny` IS `negation`.** It should not carry its own force-axis entry; it is the same slot as `negation`, filed under the wrong axis |
| `hedge` | *"is `hedge` = degree at another band?"* | **groups into `degree`'s slot** | **yes.** `hedge` is not a force; it is degree at a different band value, confirming the code's own suspicion |
| `norm` | *"is `norm` deontic modality, i.e. CONTENT, not force?"* | **groups into the same slot as `modality`** | **yes.** `norm` and `modality` are one slot; neither belongs on the force axis as declared |
| `command` | *(control form, no open question stated)* | **groups into the `assert`/`ask` slot** | as expected — a third force value competing with the other two, confirming `force` is a real, if under-elaborated, slot |

**What this leaves of the original nine-force list (`form_inventory.md` §4b):** once `deny` (= negation) and `norm` (= content) are removed, and `hedge` (= degree) is removed, the force axis's actual membership is `{assert, ask, command, …}` plus whatever `author`/`retract` turn out to be once entered and sieved — **half the originally declared force list was never a force**, exactly the finding recorded in `sieve-measures-the-axes.md`, now reproduced from a live run rather than recalled.

---

## 4. OPEN HYPOTHESES — sieve-tested, but nothing yet excludes or shares a field with them

| name | example | declared axis | measured slot | why it's still open |
|---|---|---|---|---|
| `past` | "the customer **had** qualified" | content | singleton | nothing else in `CANDIDATES` writes the `time` field or competes with `past`, so its slot membership is unconfirmed by exclusion — it could turn out to share a slot with a future `future`/`present`/aspect form, or genuinely stand alone |
| `evidential` | "the customer qualified, **according to the order log**" | content | singleton | same limit. The code's own note calls it *"fits NO declared axis"* — a fourth axis candidate, not yet testable because nothing else occupies a `source` field to compete with it |
| `mirative` | "the customer **surprisingly** qualified" | content | singleton | same limit — *"also fits no axis"* per the code |

**Action needed to close these out, not just leave them open:** each needs at least one more form written that plausibly competes with it (a `future`/aspect form for `past`; a second evidential-source value for `evidential`; a second surprise-marking form for `mirative`) before `slots()` can say anything about them. Singleton-slot status is **not** a finding — it is the absence of one, and should not be read as "confirmed independent."

---

## 5. STRUCTURALLY BLOCKED — passes as a form, fails the realizability gate or the composition proof

Both rows below are about `conditional` — *"if a customer is VIP and spent over $500, apply a 10% discount."*
That one sentence actually needs two separate mechanisms: **detachment** (given the "if" and the fact it depends
on, correctly conclude the discount for *this* customer — ordinary modus ponens) and **discharge** (turn "if a
customer is VIP..." into a standing, unconditional rule the engine can reuse for the *next* customer, without
re-deriving it from scratch). Detachment now works. Discharge does not — see the row below for why.

| name | status | why |
|---|---|---|
| `conditional` / `unmet` — **discharge, ⚠ SHELVED 2026-07-28** | measured **one slot**, and `_conditional_forbids` is, per the code's own comment, *"the only commitment here with real teeth"* — but `forms_discourse.md` §4.4's discharge half is **not buildable on this engine as it stands**. **No longer being worked on**: checked against `agentic_scenario_catalog.md`'s ten scenarios, none need the agent to derive a new rule from a hypothetical — every scenario only ever *applies* already-authored rules. Diagnosis kept below for the record; not on the critical path unless a real "agent learns its own rules" scenario is added | `cnl_engine_goal_plan.md` §3, verified against `tests/units/test_engine.py:682-706`. Modus ponens (elimination) works; hypothesis-discharge (introduction of `→` itself, as an unconditional world fact) has no mechanism, because `powering()`'s backward wire-walk taints any unit downstream of a supposition regardless of what it mints |
| `conditional` / `unmet` — **detachment, ⭐ FIXED IN CODE 2026-07-28** | Was: `guard_density(CANDIDATES)["still_leaking"]` contained `positive ∘ assert ∘ world ∘ unmet` and seven siblings — guarding never fixed it. **Diagnosis, corrected**: this wasn't a property of `unmet` composing with content forms in general — `frame()`/`cells()` were auto-attaching the default bare `positive` onto `unmet`'s node even when nobody asked for it, and *that unrequested addition* was what detached. Fixed via `Form.excludes_defaults` (`units/forms.py`, `units/sieve.py`): a form can now declare that a default must not be auto-attached because it already supplies its own, incompatible way of reaching the same conclusion. **After the fix**: `still_leaking` is empty; `interactions(CANDIDATES, guarded=True)`'s leak rate dropped to 0.008, with exactly one leaking pair remaining — `positive ∘ unmet`, **explicitly requested**, which still leaks correctly, because that combination genuinely is a contradiction (`tests/units/test_sieve.py::test_explicitly_combining_unmet_with_a_bare_positive_still_leaks`) | This is the bare/relational split from `composition_grammar.md` landing in running code for the first time, rather than staying at the design/SMT-proof stage. The guard-authoring cost (`forms_discourse.md` §4.2's O(n²) worry) turned out to be smaller than feared for this case: the fix was one field + two small changes to cell-generation, not a rewrite of every other form's elimination rule |

**Note for Phase A specifically:** `conditional` is flagged in `units/forms.py`'s own comment as *"the first form whose real home is a UNIT rather than a field"* — i.e. the first candidate that isn't a claim decoration but a relation between two occurrences. That is exactly the shape every item in §6 below also has, which is why §6 should not be entered into the sieve's claim-decoration harness naively — see the action item in §7.

---

## 6. NOT YET FORMALIZED — named in prose, no `Form` entry exists

None of these have been through the sieve at all; they exist only as prose claims across the docs. Listed with
where they're named and what shape they'd need:

| form / category | example | named in | shape |
|---|---|---|---|
| **quantification** | "**every** VIP customer gets the discount," not just one named customer | `forms_discourse.md` §2.2 CONTENT list, `form_inventory.md` §4a | relational, like `conditional` — binds a variable across occurrences, not a single-claim decoration |
| **causation** | "creating the account **enables** sending the welcome email" | same | relational — at minimum a two-occurrence link; `form_inventory.md` flagged this as "NO MECHANISM" even under the retired engine |
| **identity / reference** | "the **observed** total doesn't match the **expected** total" — are these two occurrences the same thing or not? | `forms_discourse.md` §10.3 (open, with the measured depth-4/5 engine obstacle already blocking the flagship case) | relational, and specifically flagged as depending on a *separate* fix (the surge detector, `cnl_engine_goal_plan.md` Phase D) before it can even be tested, since resolution is iterated over a cycle |
| **tense, if bounded returns** | distinguishing "the customer **qualified**" from "the customer **had been qualifying**" | `forms_discourse.md` §6 catalog row (Vendler's aspect classes) | `past` (§4 above) is a start; a full tense/aspect treatment needs the aspectual-class dimension too, currently absent |
| **tier-3 thematic roles** | who is the *agent* and who is the *patient* in "send the customer the welcome email" | `forms_discourse.md` §9 | not a "form" in the CONTENT/FORCE/LEVEL sense at all — a different, corpus-derived tier, deliberately out of this sieve's scope |
| **activity structure** (plan/step/subgoal/hypothesis-verification) | `forms_discourse.md` §10.2, open | multi-turn, not classifiable as a single utterance's CONTENT×FORCE×LEVEL point at all — needs its own treatment before it's even a sieve-shaped question |

---

## 7. Next actions for Phase A

1. **Do not naively add quantification/causation to `units/forms.py`'s claim-decoration harness.** `conditional` already proved that a relational form needs a second occurrence and a role (`when:`), which the sieve's `Ctx`/`claim_pattern` scaffold was not built for generically — it was extended once, ad hoc, for `conditional`. Before writing `Form` entries for quantification or causation, decide whether the harness itself needs a generic "second occurrence + role" capability, or whether each relational form keeps getting a bespoke extension the way `conditional` did.
2. **Close out §4's open hypotheses** by writing one competing form each for `past`, `evidential`, `mirative` — otherwise their slot status stays uninformative indefinitely.
3. **Route `conditional`'s Phase B blocker (§5) to the plan**, not to more Phase A work — no amount of additional inventory entries fixes a discharge mechanism that doesn't exist. This is already tracked in `cnl_engine_goal_plan.md` §3/§4.
4. **`identity`/reference (§6) is gated behind Phase D**, not Phase A — don't spend inventory-writing effort on it until the surge detector is fixed, since the flagship test case is already known to be unmeasurable on the current engine.
5. **Re-run `axis_audit`/`factorization_audit`/`impure_slots` after every inventory change** and update this document's tables from the live output — the numbers here are a snapshot, not a citation.

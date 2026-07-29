# The engine's goal, stated precisely: a CNL that soundly composes at unlimited depth

**Status: north star, 2026-07-28; §2 note added 2026-07-29.** Distilled from a working-session thread that pressure-tested
`forms_discourse.md`, `forms_llm.md` and `forms_extra_considerations.md` down to a single, checkable target.
Supersedes nothing; it is the crisp restatement those three documents were circling. Read them first for the
argument; this is the destination stated as a claim with a scope and a status.

---

## 1. The goal, stated as a claim

> **Build a CNL whose closed-class composition machinery is proven sound to unlimited nesting depth, so an
> agent can offload composition-heavy and procedure-following reasoning to it, carrying opaque domain content
> through that machinery without ever composing over the content itself.**

This is deliberately **not** "reason soundly about arbitrary business content." That version is impossible —
the open class is made of relations, not parts, has no basis, and is unbounded (`forms_discourse.md` §3.3);
no engine can prove closure over it, ever, regardless of effort. The claim above is scoped to exactly the half
that *can* be proven closed: the small, fixed, designed closed class.

---

## 2. Whose job this is, precisely

Two responsibilities that must not be conflated (this is the load-bearing distinction the thread arrived at):

| | scope | provable once? | owner |
|---|---|---|---|
| **the engine's job** | closed-class connectives (negation, degree, quantification, conditionality, tense, causation, force, roles) composing with **each other**, to unlimited nesting | **yes, in principle** — the closed class is fixed and small, so this is a bounded, finite, one-time task, the same shape as proving `AND`/`OR`/`NOT` closed under Boolean algebra, just requiring more cases because the closed-class forms are not all instances of one clean algebra | the engine builder |
| **not the engine's job, ever** | open-class domain predicates (business terms — `VIP`, `orders`, `spend`) interacting with **each other** in ways their authors didn't anticipate | **no, not even in principle** — open-class content has no basis to prove closed over (`forms_discourse.md` §3.3); this is a permanent structural fact, not a gap that more engineering closes | KB/ruleset governance — a different layer, possibly using engine-adjacent tooling, but not covered by the engine's contract |

**Note, 2026-07-29 — normalization is a rules job, never the boundary's, and the CNL should have room for
synonyms because of it.** A session pressure-testing several closed-class forms (`deny`, `ask`, sequencing,
quantification-as-application) found each collapses into an existing mechanism rather than needing its own —
`deny` into `negation`, `ask` into `command` targeting a report-shaped claim, and so on (`closed_class_inventory.md`
§3, §9). None of this touches the boundary: the LLM still recognizes surface English as CNL-keyword `ask` or
`deny` exactly as before (job 1, judgment about intent — stays the LLM's) and a **rule**, never the LLM, expands
that keyword into whichever internal mechanism it turns out to share (job 2, mechanical and deterministic — never
the LLM's, per `forms_llm.md`'s findings on where depth-bound LLMs fail silently at exactly this kind of
compositional rewriting). Consequence worth keeping deliberately: **the CNL surface should keep multiple keywords
for the same underlying mechanism** (`ask` and `deny` staying distinct, natural surface forms even once their
internal realizations are shared or reduced) — better UX for a human author, and it also makes the LLM's own job
easier, since more valid surface phrasings for the same target give it more ways to land on something correct
rather than one brittle, canonical phrasing it must hit exactly.

**Why pure `AND`/`OR` gets unlimited depth for free, and why the rest of the closed class doesn't automatically:**
Boolean algebra is associative, commutative, and closed under its own operations by construction — one structural
induction proves every possible nesting, forever, the reason SQL's `WHERE` clause (minus `NULL`) composes to
arbitrary depth with no per-query verification. Degree, quantification, tense etc. don't automatically inherit
this because each introduces its **own value type** (a scalar band, a bound variable, a temporal order) that
Boolean algebra's proof says nothing about. Composing across them (`degree ∘ negation`) is a cross-algebra
operation whose closure has to be established **separately** — that separate establishment, done once for the
whole fixed inventory, is still categorically an engine-level, bounded, one-time job. It is not a lesser version
of the `AND`/`OR` guarantee; it is the same guarantee, costing more cases because the domain is less uniform.

---

## 3. Three ingredients, and current status against each

**1. Algebra closure — do all closed-class forms compose soundly with each other, to arbitrary nesting?**

| finding | status |
|---|---|
| pairwise composition sieved | **partial**, but now provable rather than only samplable — 65% of naive cells leak (`sieve-measures-the-axes.md`); `units/smt_sieve.py` proves the guarded fix for several of these over the whole symbolic domain rather than sampling it (`cnl_engine_goal_plan.md` §4) |
| n ≥ 3 nesting | **⭐ closed as a design requirement, 2026-07-28** — not by sampling more depths, but by an induction: nesting one conditional inside another is proven safe at unbounded depth *conditional on* one specific wiring discipline ("gated," not "naive" — `composition_grammar.md` §5a). No longer an open measurement question |
| `SUPPOSE`'s discharge (the conditional's own introduction rule, §4.4) | **⚠ measured structurally impossible, and SHELVED, 2026-07-28** — falsifies §4.4 outright, but checked against `agentic_scenario_catalog.md`'s ten scenarios, none need the agent to derive a new rule from a hypothetical (only to *apply* already-authored ones, which already works via modus ponens). Not on the critical path unless a real "agent learns its own rules" scenario is added; diagnosis kept on record (`cnl_engine_goal_plan.md` §3) |

**2. Machinery conformance — does the running engine actually realize the proven algebra, with no plumbing bugs?**

| finding | status |
|---|---|
| `degree ∘ negation` | **known leak** — two write paths (fold vs. interpretation layer), no shared read; an implementation defect, not an algebra defect |
| guards (the current mitigation) | **⭐ found to silence rather than compose** (0 leaks, 0 passes) — today's "no leaks" is partly achieved by refusing risky compositions outright, not by soundly executing them. Reaching the goal needs guards that **admit** the sound cases, not just block everything |

**3. Honest depth/exhaustion reporting in the runtime — does deep composition terminate or honestly report that it hasn't?**

| finding | status |
|---|---|
| depth is realized as an iterating computation (a self-looped unit), not static term-nesting | by design (`model.md` §5) |
| the surge detector (`SURGE_AT`, now 6) | **⭐ reframed and partly closed, 2026-07-29** (`forms_discourse.md` §10.3, `cnl_engine_goal_plan.md` Phase D) — verified, not just measured: it genuinely **cannot** distinguish converging recursion from a runaway cycle, because every self-loop mints a fresh node each pass, leaving no content-blind signal to build a smarter check from. What *was* fixable — a burned unit's stale value silently reading as a finished answer — is fixed: burned units are now excluded from every read, so the failure this row worried about (`forms_llm.md` §7's silent-exhaustion-as-answer) no longer happens, even though the detector itself stays unable to tell the two cases apart |

---

## 4. Why the goal is realistic rather than open-ended

Each of the three ingredients above is a **specific, already-diagnosed defect with a clear next action**, not an
unbounded research question:

1. ~~Fix or replace `SUPPOSE`'s discharge so conditionals actually compose~~ — **shelved**; nested-conditional
   *evaluation* (modus ponens applied to already-authored rules) needed the "gated" wiring discipline instead,
   and that's done (§3's `4.4` finding kept on record, no longer a roadmap item).
2. Turn guards from "silence the risky case" into "certify and admit the sound case" (§3's guard finding).
3. Fix the surge detector so depth exhaustion is reported rather than silently truncated (§10.3).

None of these require solving the open-class problem — all three are contained entirely within the closed class,
which is exactly what makes this goal tractable where "reason soundly about business content" is not. The
closed class is fixed in size; each of these three fixes is a bounded, scoped engineering task; and once done,
**every** ruleset built purely from closed-class forms inherits the guarantee for free, to unlimited depth, with
no re-verification per ruleset — which is the entire point of drawing the engine/ruleset boundary where §2 draws
it.

---

## 5. What this does **not** license

- **Not** a claim that business rules built on top of this CNL are correct, wise, or bug-free. Composition
  soundness and business correctness are orthogonal audits with different owners (`forms_extra_considerations.md`
  would be the place to record KB-governance tooling, if that gets designed — it is explicitly **not** part of
  this goal).
- **Not** a claim that open-class predicate interactions (two business terms colliding unexpectedly) are
  covered. They structurally cannot be, by anyone, ever — that is a permanent fact about the open class, not a
  gap this roadmap closes.
- **Not** a claim that any of §3's three fixes is small. Each is flagged in its source document as a real,
  measured problem; this document's contribution is only to name them as the complete, closed list standing
  between the current build and the stated goal.

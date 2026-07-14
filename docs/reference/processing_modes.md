# Processing Modes — the closed inventory of ISA computation

> **Status: CANONICAL (2026-07-07, ratified in conversation with the user).** Companion to
> `logic_fragment.md` (which fixes WHAT can be expressed) — this document fixes HOW the machine
> is allowed to compute: a **closed inventory of processing modes**, each grounded in what
> human/animal system-2 deliberation actually does, plus an acceptance test that any proposed
> new mode must pass. Purpose: prevent extra, useless, or unnatural computation modes from
> being implemented by reflex ("academic memories" — trails, agendas, unification stacks),
> and guarantee the mechanisms we DO owe the user: explainability, hypothesis
> formulation/verification, and try-per-plan → check → replan.

## 1. The grounding: what deliberate reasoning actually is

The design mimics system-2 deliberation as observed, not logic as axiomatized:

- **Serial and working-memory-bounded.** One thing at a time, a handful of bindings held at
  once. → Firmware is serial token-passing; frames are small; fuel bounds everything.
- **It iterates over reified collections.** Animals and humans run *lists*: check each cache,
  count each item, try each candidate. The list is a THING in memory, not a quantifier. →
  Collections are first-class graph structure (member nodes on a `next`-chain — the same shape
  as token chains), and iteration is a cursor gadget, not recursion.
- **It runs remembered procedures.** "How to compute" is *knowledge*: a recipe learned, named,
  and recalled ("to check eligibility: gather the accounts, total them, compare to the
  limit"). → **Procedures are KB content**, authored in CNL (`to NAME: step then step` — the
  surface already exists for planner ops, `decision-nac-grouping`; extending it to general
  procedures is a listed TODO of the TUI arc). Procedures run ON the ISA as control-token
  programs. Two tiers, one machine:
  - **Universal firmware** = the modes below (domain-blind, shipped, small).
  - **KB procedures** = *named compositions of modes* authored per domain. A procedure is
    never a new mode; it is a recipe over the existing verbs.
- **It is expectation-driven.** Deliberation constantly predicts and compares: form a
  hypothesis, look for the evidence; act on a plan, check the result. → Verification and
  plan-checking are modes, and the pencil/ink layer split (§5 of the vision) is what makes
  them safe.

## 2. The closed mode inventory (nine verbs)

Every computation the system performs must be one of these, or a KB-authored composition of
these. Each row: the mode, its cognitive analogue, its ISA realization, and the trap it must
not grow into.

| # | Mode | Cognitive analogue | ISA realization | The trap (do NOT become) |
|---|------|--------------------|-----------------|--------------------------|
| 1 | **SATURATE** | automatic association: "what follows immediately" | monotone forward closure within a demand scope (`run_to_fixpoint`); `<fresh>` markers = semi-naive | global eager closure of the whole KB; Rete agenda with salience |
| 2 | **ITERATE** | walking a list: check each one in turn | cursor gadget: `<current>` token advancing a reified `next`-chain; the domino/forall pattern | recursion with hidden depth; Python `for` loops over engine state |
| 3 | **CHAIN** | deliberate inference: "what would make that true" | demand-driven rule application: `<demand>` nodes + APPLY over reified rules | SLD resolution with a trail; unbounded backward search |
| 4 | **CHECK** | looking for something and possibly not finding it | bounded completion: enumerate the demanded extension, mark the outcome; absence → defeasible `assumed-no` (CWA) | negation-as-failure by exhaustion; proof by refutation |
| 5 | **CHOOSE** | comparing options and picking | enumerate candidates into frames, graded comparison, α-cut, deterministic stable pick (PREFER/SELECT) | optimization loops, argmax over scored search trees |
| 6 | **SUPPOSE** | "what if" — entertain before believing | a `<hypothesis>` scope: assumed facts written as CONTROL (pencil) nodes; reasoning proceeds inside the scope; on confirmation EMIT to fact layer (ink) with provenance; on refutation DROP_CTRL the scaffold | possible-worlds machinery; backtrackable fact-layer writes; truth-maintenance by deletion |
| 7 | **WALK** | scanning / scouting at distance | fueled walkers carrying demand across long range; discoveries materialize as shortcut facts | unbounded graph search; all-pairs precomputation |
| 8 | **CALL** | using a tool: fingers, paper, calculator | reified `<call>` node with argument slots, serviced at fixpoint, result folded back (arithmetic, aggregation, temporal, clingo, SLM, external acts) | re-implementing arithmetic/aggregation as rules; hidden Python helpers |
| 9 | **RECORD** | remembering what you did and why | provenance journaling woven through every mode (`<j:…>` MINT/EMIT); not optional, not a debug flag | a separate logging subsystem; explanation as post-hoc template text |

Notes:

- Modes 1–8 all consume **fuel** (the metareasoning layer prices effort; "think harder" =
  more fuel). Mode 9 is free and mandatory.
- **Counting and totaling**: building/filtering the collection is ITERATE; the arithmetic on
  it is CALL. This split matches the cognition (people enumerate; they compute totals with a
  tool or slowly and badly) and keeps the rule layer arithmetic-free.
- **Elimination** (the riddles mechanism) is a composition: ITERATE over the closed candidate
  list × CHECK each × the last-standing rule — not a tenth mode.

## 3. The three owed mechanisms, as compositions

**Explainability = RECORD, rendered.** Every firing journals which rule, which bindings,
which facts. An explanation is a *replay* of the derivation tree rendered from the CNL nodes
themselves — in the Horn fragment the journal IS the proof object (`logic_fragment.md`).
Bounded CHECK additionally makes *negative* answers explainable in a way exhaustive systems
cannot: "assumed no — I looked at X and Y within budget and found nothing" is an honest,
renderable trace of WHERE the completion searched, not a claim about the universe.

**Hypothesis formulation and verification = SUPPOSE + CHAIN + CHECK.** Mint a `<hypothesis>`
scope; write the supposition in pencil; CHAIN its consequences inside the scope; CHECK each
predicted consequence against the fact layer (or post an evidence-gathering `<call>` — the
CWA escalation, `decision-cwa-default`). Verdict: consequences found → EMIT the hypothesis to
ink with provenance "confirmed by …"; contradiction or budget exhausted → DROP_CTRL the whole
scope. The fact layer stays monotone throughout — no retraction, because nothing unconfirmed
ever touched ink. This is the pencil/ink split doing exactly the job it was designed for.

**Try-per-plan → check → replan = PLAN's loop, which is hypothesis-checking applied to
action.** A plan step carries its *expected effects* (already the operator `adds` in the
planning banks). Execute = CALL (or a rule firing). Then ITERATE over the expected-effect
list × CHECK each against observed facts. All present → advance the `<current>` step token.
Mismatch → the discrepancy is a fact; replanning rules match it and rewrite the remaining
plan (the plan→act→replan loop already differential-tested in the ISA arc). No new mode: the
same SUPPOSE/CHECK machinery, pointed at the world instead of the KB. This also gives honest
partial-failure narration for free: RECORD holds which expectation failed.

## 4. The acceptance test for any proposed new mode

A new mode may be added ONLY if all five hold — otherwise it is either a KB procedure
(composition) or an academic import (reject):

1. **Nameable by a KB author in plain language** ("look for", "try each", "suppose") — if it
   needs a logic textbook to explain, it does not belong.
2. **Fully visible state**: every intermediate lives as control-layer graph structure a trace
   renderer can show. No hidden Python dicts, stacks, or trails.
3. **Fuel-boundable**: it degrades gracefully into "best effort so far" when the budget runs
   out. A mode that must run to completion to be meaningful is wrong here.
4. **Journals natively**: its RECORD trace renders as a CNL explanation.
5. **Not a composition**: if it can be written as a KB procedure over existing modes, it MUST
   be — that is the whole point of having procedures in the KB.

## 5. Rejected modes (the academic-memories list)

Each rejection names the reflex and what to use instead:

| Reflex | Why rejected | Use instead |
|---|---|---|
| Backtracking search with trail/undo (SLD, WAM) | hidden state, world-undo violates monotone ink | serial ITERATE over candidates + SUPPOSE scopes in pencil |
| Unification / mgu machinery | no function terms exist; matching is attribute tests binding node instances | FOLLOW/TEST over attr patterns |
| Rete agenda + conflict-resolution salience | ordering policy hidden in the engine | token-gated control; ordering is graph data |
| Exhaustive completion / model enumeration | forfeits boundedness; unexplainable negatives | bounded CHECK + CWA defeasible-no |
| Belief propagation / probabilistic loops | normalization loops, hidden convergence state | possibilistic grades + α-cut (CHOOSE); no posterior claims |
| Value iteration / RL-style scoring | learned policy inside the engine | declared graded preference in banks; learning stays at the SLM boundary |
| Continuations, higher-order rules, lambdas | invisible control flow | the call/return frame gadget; procedures are first-order recipes |
| Concurrent actors / blackboard opportunism | destroys serial explainability and determinism | serial deliberation; parallelism ONLY as a semantics-invisible accelerator (F-track) |
| Deep recursion | unbounded hidden stack | ITERATE over reified collections; frames + fuel where nesting is real |
| Clever join planners / cost-based optimizers in the semantics | psychology leaking into physics | df seed-from-rarest is the ONLY built-in heuristic; anything smarter is metareasoning data or an accelerator gated by firmware equivalence |

## 6. Consequences for the firmware arc

- Phase 4 of `../implementation_plan.md` gains the **collection conventions** (member
  `next`-chains + the ITERATE cursor gadget) and Phases 4–5 gain the **`<hypothesis>` scope
  conventions** (pencil writes, confirm-EMIT, refute-DROP) as named deliverables.
- The **KB procedure surface** (`to NAME: …` beyond planner ops) is promoted from TUI-arc
  leftover to a firmware-arc deliverable: procedures are how domains compose modes, so the
  authoring form must land with firmware v2. New CNL forms → SLM surface ledger
  (`handoff_slm_surface_track.md`).
- The trace renderer (Phase C gate) must render all nine modes — in particular SUPPOSE scopes
  and CHECK's "where I looked" — since they carry the explainability promise.

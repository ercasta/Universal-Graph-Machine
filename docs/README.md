# UGM documentation — the single entry point

> **Status: CANONICAL INDEX (reorganized 2026-07-14, replacing the old `reference.md`).** ONE page
> that states what the system is, which decisions are in force, and what every other doc is. When
> this index and an older doc disagree about *status*, this index wins; when two live docs disagree
> about *content*, the precedence chain (§4) wins.

## 1. What the system is (one paragraph)

One substrate: a graph of **label-less nodes** (opaque identity + a bundle of graded/valued
attributes under a closed key vocabulary) and **untyped directed edges**. Facts, rules, goals,
plans, and the CNL source itself are all nodes in that one graph. Computation is graph rewriting
driven **goal-directed** (demand nodes — magic-sets made literal) over a **monotone fact layer**
plus freely-mutated control state. Reasoning is a small set of universal, iterative, fuel-bounded
**"system-2" firmware procedures** expressed as **programs over a tiny opcode ISA** with a data path
*and* a control path (`Machine` + `ControlMachine`); domain knowledge and policy live ONLY in CNL
banks; Python is physics (the interpreter, the store, content-blind indexes, tools, and the
authoring/lowering compilers). An SLM sits at exactly one boundary (user intent → CNL). The official
semantics is **bounded-defeasible** — answers are the best of current knowledge under a
metareasoning effort budget, not theorems. The system is an **agent, not a theorem prover**: it is
session-sized, judged per-utterance, and decides negation by asking the positive on demand.

## 2. Decisions in force (the ratified stack, newest first)

| Decision | One-liner | Where |
|---|---|---|
| **Firmware over ISA / no privileged partitions** (2026-07-14) | The demand solver's work = ISA programs (one matcher, register bindings, compiler-emitted visibility guards); what a node "is" is emergent from attributes + use — no kind-flags, no matcher modes, no separate rule graph (one-graph fold, `rules=` optional) | `reference/firmware_reference.md`; history `attic/firmware_over_isa_design.md` |
| **The ISA control machine, forward-only** (2026-07-14) | Control flow is instructions (`BRANCH/CALL/RET/SUSPEND/PRIM`), not Python drivers; the control plane is forward-only — demand solving is an above-plane program, not a reverse plane; instruction set = contract, interpreter = swappable | `reference/isa_reference.md` §control path; history `attic/isa_control_machine.md` |
| **Machine semantics are ISA programs** (2026-07-13) | Every capability/semantic (interning, dedup, reads, thresholds) is an instruction or program run by the one interpreter; `add_node`/`add_relation` are the dumb loader — never a home for semantics | CHANGELOG (feedback #8b); `reference/firmware_reference.md` |
| **Mechanism/policy: two homes** (2026-07-14) | GRAPH = facts + explanation (matchable, reasoned-over; the demand trace is a negative's provenance and stays a node); REGISTERS (`AttrGraph.registers`, `State.regs`) = execution state; depth never forces graph materialization — being explanation does | `attic/mechanism_policy_separation.md`, `attic/axis_b_control_registers.md` |
| **ISA value operands are regular nodes** (2026-07-14) | Registers hold only node-pointers; a value like `ada` is a regular node carrying `<isa_operand_value>="ada"`, interpreted by instructions | `attic/isa_value_operands_design.md` |
| **Rust = port the interpreter only** (2026-07-14) | Procedures were made firmware first, so the Rust core is one fetch-decode-execute loop; measured constant ~381×; magic-set rewrite REJECTED | `design/rust_engine_plan.md` |
| **Same-name interning at the CNL reader** (2026-07-13) | Same-named `<mention>` entities coalesce to ONE node at ingest (hardcoded reader policy); the demand-driven coref alternative was CORRECT but 3–6× slower — rejected | `attic/indexing_and_coalescing_design.md`, `attic/demand_driven_coref_plan.md` |
| **S-P-O is a directed 2-hop path** (2026-07-12) | Direction carries the roles; role-labeled / Davidsonian edges REJECTED | memory `spo-directed-path-no-labeled-edges` |
| **Coreference as declared rules; anaphora off-roadmap** (2026-07-12) | Asserted/derived identity (`same_as`) is core reasoning; same-name linking is a boundary policy (now interning); anaphora belongs to the SLM via exposed `focus.top_centers` | `attic/coreference_as_rules_design.md` |
| **Client = agent loop + TUI over seamless CNL intake** (2026-07-12) | The utterance's own structure drives the loop — no intent dispatcher; seed-from-focus is the accretion answer (bounded attention) | `design/cnl_intake_design.md` |
| **Agent, not theorem prover / demand-driven negation** (2026-07-11) | Negation decided on demand by NAF (ask the positive, absence decides); fuel→UNKNOWN is honest; no eager exhaustive completion | `attic/demand_driven_negation_design.md` |
| **No equivalence with the previous generation** (2026-07-10) | The rewriter/name-based generation is NOT a correctness target; judged on sensible bench answers | `implementation_plan.md` |
| **The logic fragment** (2026-07-07) | Horn + stratified completion + defeasible priorities + reified deontics + declared congruence + labelled-null existentials + possibilistic grades + calculators; NO sequent calculus / general disjunction / refutation | `reference/logic_fragment.md` |
| **Processing modes** (2026-07-07) | CLOSED inventory of nine modes (SATURATE, ITERATE, CHAIN, CHECK, CHOOSE, SUPPOSE, WALK, CALL, RECORD); acceptance test blocks academic imports | `reference/processing_modes.md` |
| **CWA-default, OWA opt-in** (2026-07-07) | Unprovable → defeasible `assumed-no`; `X is open world` per predicate → `unknown`+gather; entailed `is_not` is the hard no | `ugm/policy.py` |
| **Label-less substrate / rule ISA / one substrate** (2026-06/07-05) | Node = opaque identity + attrs; relations reify; rules compile to opcodes; everything in one graph, tools as calculators | `vision.md`, `attic/rule_isa_design.md` |

Standing feedback (always in force): **no commits by the assistant**; **no domain logic in Python**
(banks only); **no hardcoded engine policy** (strategies are declared data); **correctness before
raw performance**; **delete superseded code aggressively**.

## 3. The doc map

**Top level — the living documents:**
- `README.md` — this index.
- `CHANGELOG.md` — reverse-chronological log of everything landed, plus the phase-by-phase appendix
  (the absorbed historical implementation plan).
- `implementation_plan.md` — THE active plan: remaining work only.
- `architecture.md` — the as-built layering, generic → opinionated.
- `vision.md` — the design philosophy (why the system is shaped this way).
- `related_work.md` — positioning against the literature.
- `critique.md` — external-eye assessment (deliberately an outside voice).
- `feedback_from_pystrider.md` — living ledger of consumer-feedback items from the `../pystrider`
  spike (each with repro + fix status).
- `engine_user_guide.md` — consuming UGM as a library.
- `engine_developer_guide.md` — extending the engine (instructions, tools, firmware, stances).

**`reference/` — detailed reference documentation:**
- `isa_reference.md` — the ISA: opcode semantics (data path + control path), machine state, the
  two-phase model, lowering, goal-directed evaluation.
- `firmware_reference.md` — the reasoning firmware as built: the demand solver, registers,
  visibility guards, live-sets, modes, provenance, retraction, the public API.
- `cnl_reference.md` — the CNL surface, form by form (facts, rules, questions, declarations,
  session control) — the SLM's target surface, doubling as the retraining spec.
- `logic_fragment.md` — the semantics contract (what can be expressed).
- `processing_modes.md` — the computation contract (how the machine may compute).
- `glossary.md` — the project vocabulary, one sentence per term.
- `measurements.md` — the load-bearing numbers (constants, curves, landed speedups, negative
  results), each with date + runnable source; update rows when a bench is re-run.

**`design/` — active designs (not yet built, or partially built):**
- `cnl_intake_design.md` — the agent-loop client spec (Phase 8; spine built, tail remains).
- `rust_engine_plan.md` — Phase 7b (Rust interpreter port; deferred until perf bites).
- `consistency_design.md` — universal conflict-lint / constraint schemas (sketch).
- `validation_experiments.md` — proposed value-and-risk experiments (not ratified).

**`attic/` — honest historical records, never authoritative.** Design docs for work that is now
built (their as-built status headers are the record), superseded plans, and explorations. See
`attic/README.md` for what each was and how it ended.

## 4. Content precedence chain (for live docs)

`README.md` (status) → `vision.md` (philosophy) → `reference/logic_fragment.md` +
`reference/processing_modes.md` (contracts) → `reference/isa_reference.md` +
`reference/firmware_reference.md` (machine as built) → `architecture.md` (layering) →
`design/*` (active designs) → guides.

## 5. Reading order for a fresh session

`README.md` → `vision.md` → `reference/logic_fragment.md` → `reference/processing_modes.md` →
`reference/isa_reference.md` → `reference/firmware_reference.md` → `architecture.md` →
`implementation_plan.md` (then the design doc for whatever track you're on). Keep
`reference/glossary.md` at hand for the vocabulary; check `reference/measurements.md` before
making or trusting a performance claim. Log landed work in `CHANGELOG.md`.

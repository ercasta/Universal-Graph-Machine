# The reasoning firmware — reference (as built)

> **Status: AS-BUILT REFERENCE (2026-07-14, written at the docs reorganization).** What the
> reasoning layer *is* today, distilled from the design docs that built it (rationale trails:
> `../attic/firmware_over_isa_design.md`, `../attic/isa_control_machine.md`,
> `../attic/mechanism_policy_separation.md`, `../attic/axis_b_control_registers.md`,
> `../attic/isa_value_operands_design.md`, `../attic/demand_driven_negation_design.md`). The opcode
> semantics live in `isa_reference.md`; the layering in `../architecture.md`; how to *use* this from
> a consumer in `../engine_user_guide.md`. When this doc and the code disagree, the code + its tests
> win — update this doc.

## 1. What "firmware" means here

Four layers, bottom-up:

1. **The interpreter** — `Machine` (data path: match-then-apply) and `ControlMachine` (control path:
   PC over labeled basic blocks) in `ugm/machine.py`. Fixed Python; executes a fixed instruction
   vocabulary. A new instruction = one small class + one interpreter branch.
2. **The instruction set (ISA)** — the vocabulary (`SEED`/`SET`/`FOLLOW`/`TEST`/`GRADE`/`VMATCH`/
   `DISTINCT`/`MEMBER`/`OVERLAY`/`ITERATE`/`MINT`/`EMIT`/`RETIRE`/… + the control transfers
   `BRANCH`/`BRANCH_IF`/`CALL`/`RET`/`SUSPEND`/`HALT`/`SETI`/`DEC`/`PRIM`). See `isa_reference.md`.
3. **Firmware programs** — DATA: lists of instruction instances produced by lowering compilers
   (`ugm/lowering.py` for rule banks; inline builders like `chain._facts_matching_isa` and
   `chain._frame_program` for the demand path). Ephemeral compilation artifacts, never graph nodes.
4. **Drivers** — thin Python orchestration that loops rounds and manages agendas: `run_bank`
   (forward), `chain_sip` (demand). Legitimately Python; they contain no matching, binding, or
   threshold logic of their own.

**The invariant (no privileged partitions):** a node is just a node — what it "is" (fact, rule,
mention, provenance, operand) is emergent from **attributes + which rules/programs select it**. The
machine has NO mode and NO privileged category (`skip_inert` is retired; `control`/`inert` are
marker ATTRIBUTES, the old flags are derived read-properties). Safety without privilege comes from
**compiler-emitted guards** (§4).

**The two homes** (mechanism/policy separation): the **GRAPH** holds facts and *explanation* —
anything reasoning or `why` must be able to match (including the `<demand>` trace: a NAF negative's
provenance). **REGISTERS** hold execution state: `State.regs` (per-match binding file),
`AttrGraph.registers` (the control-register file — e.g. the focus stack — carried by `copy()`,
invisible to matching and `derived_triples`). The boundary rule: *depth never forces graph
materialization — being explanation does.*

## 2. The demand solver — `chain_sip` (`ugm/chain.py`)

`chain_sip(fact_g, goal, *, rules=None, fuel=…, scope=…, focus_scope=…, provenance=…)` solves a
bound tuple goal `(pred, subj|None, obj|None)` demand-driven:

- **Demands are literal magic sets:** a bound `<demand>` node (tuple grain — predicate + bound
  endpoints) is minted per subgoal; rules relevant to a demand are found through the `<head-index>`
  (graph structure, `apply.build_head_index`). Sideways information passing (`_sideways_order`)
  orders body atoms so bound endpoints propagate.
- **Each goal-closure frame is a `ControlMachine` program** (`_frame_program`): `SETI budget` →
  `PRIM(advance)` (run one round via the `_round` generator — the mid-round continuation the PRIM
  parks) → `BRANCH_IF` fixpoint/budget, with fuel exhaustion falling through to an `exhaust` PRIM —
  **fuel→UNKNOWN is the honest verdict**, not an error. Agenda/policy state lives in a driver-owned
  `_Frame`; scalars in control registers.
- **Negation is demand-driven NAF:** a NAC subgoal raises a nested *positive* closure and absence
  decides (`_nac_blocks`). The subgoal is a machine `SUSPEND` — the request travels in a control
  register onto the `Continuation`, and `chain_sip` is a thin driver over a stack of suspended
  machines (no Python recursion; proven by a 601-deep stratification under `setrecursionlimit(200)`).
  Stratification is enforced at LOAD (`authoring.lint_stratifiable`); cycles are the stance's call
  (`FirmwarePolicy.on_cycle`: raise or degrade).
- **Endpoints are names or ids:** `ById(node_id)` pins a demand seed / write target to a specific
  node (stale pin raises via `validate_ids`); a name resolving to >1 genuinely distinct entity warns
  before the `[0]`-pick (`resolve_write_node` is the single write-target chokepoint).
- **Derived heads EMIT into the graph** (monotone ink), with `<j:rulekey>` justification nodes when
  `provenance=True`. Skolem heads (§5) re-find their witness before minting so check-before-derive
  converges.

## 3. The fact read is a self-contained program

A single-atom fact lookup (`_facts_matching_isa`) is an ephemeral ISA program — the same `Machine`
the forward path runs, with zero Python post-filters:

- `SET` the bound endpoint (or `SEED` from the predicate key) → `FOLLOW` to the rel →
  predicate-key `TEST` → `FOLLOW` to the other endpoint; a free slot's register natively yields the
  node (wraps `ById`).
- **Visibility guards are compiler-emitted**, never hand-written per rule and never a matcher mode:
  `TEST(..., absent=True)` on the `<inert>`/control marker attributes after every bind
  (`lowering.guard_inert` on the forward path; the inline builder on the demand path). A
  provenance-aware rule (`rule_touches_provenance`) is lowered WITHOUT the guard — that is the
  authoring layer's call, which is allowed to know conventions.
- **Live-sets:** `MEMBER` restricts candidates to a register-pointed set (focus attention — contents
  in `AttrGraph.registers` are POLICY, the membership test is MECHANISM); `OVERLAY` extends the base
  with a set (SUPPOSE scope pencils, derived per lookup from `SCOPE` tags by `_scope_pencils` — the
  tag stays the pencil's persistent explanation). With no set parked both degenerate to the plain
  guard, so ONE program shape serves scoped and unscoped reads.
- The bespoke topology walk (`_facts_matching_walk`) survives ONLY as the `_CROSSCHECK` differential
  oracle.

## 4. Bindings, values, and thresholds

- **Registers hold node-pointers only** (`State.regs`). A literal value like `ada` is a REGULAR
  interned node carrying `<isa_operand_value>="ada"` — distinct from an entity *named* ada,
  differentiated by attribute + use. Instructions interpret operand nodes; a name stays a reference
  to a coref class, and aggregation over the class happens INSIDE the instructions
  (`Machine._operand_nodes`).
- **Graded thresholds** (`dog >= 0.7`, α-cuts) run as ephemeral `GRADE` programs; **value matches**
  (`?x same NAME as ?y`, graded closeness) as `VMATCH`; **distinctness** (`?a != ?b`, declared
  `Distinct` conditions) as `DISTINCT` — on BOTH engines (forward lowering + demand pass). No Python
  threshold checks remain.

## 5. Skolems (minting under a rule head)

RHS-only head variables are rejected at load (unsound). The supported minting primitive is the
**LHS-keyed bound-literal skolem** (`foo?` fact / `<foo>?` control): a skolem FUNCTION of the match.
On the demand chain a skolem head is **re-found structurally** before minting
(`_find_skolem_witness`: re-identify by defining relations to the LHS-bound anchors), so
check-before-derive is idempotent and agrees with forward.

## 6. The verdict layer — modes over the chain

- **CHECK** (`ugm/check.py`): 4-status verdict — POSITIVE / ENTAILED_NEG (derived `is_not`, the hard
  no) / ASSUMED_NO (CWA default) / UNKNOWN (open-world predicate or fuel exhausted) — plus
  `explain_check` ("where I looked"). `collapse()` folds to yes/no/unknown.
- **CHOOSE** (`ugm/choose.py`): graded α-cut argmax over candidate frames; monotone (losers
  retained, ties → all win).
- **SUPPOSE** (`ugm/suppose.py`): `<hypothesis>` scopes as the pencil/ink split — pencil writes in a
  scope, `chain_sip` reads in-scope via `OVERLAY`, CONFIRM→ink / REFUTE→drop-scope; ink stays
  monotone. `suppose(g, assumptions, predictions, *, rules=, commit=False)` is read-only and returns
  in-scope derived consequences. `ask_goal(..., commit=False)` rides the same pencil mechanism.
- **The stance is data** (`ugm/policy.py` `FirmwarePolicy`): `negation_default` closed/open +
  `open_preds`/`closed_preds`; `on_cycle` raise/degrade. No opinion is hardcoded in the engine.
- **Modes as `<call>` calculators** (`ugm/mode_calls.py`): CHECK/CHOOSE/SUPPOSE are serviced by the
  generic `<call>` loop (`dispatch.py`) — rules emit mode-calls, the dumb dispatcher services them,
  verdicts fold back as nodes. Sync tools run inline; async tools ride `SUSPEND`/`RESUME`
  continuations (`dispatch.service_calls_cm`).

## 7. Provenance, retraction, history

- **Provenance**: every APPLY/CHAIN emit can mint `<j:rulekey>` justification nodes (`proves`/`uses`
  wiring, `ugm/provenance.py`); `why`/`explain` and the trace event stream read this record — the
  trace renderer is an OBSERVER of the substrate, never a control-flow hook. The demand/subgoal
  chain is the analogous record for negatives.
- **A `why` over an already-materialized fact BACKFILLS its support**: check-before-derive suppresses
  the re-EMIT, so the chain records the justification onto the existing rel node instead (guarded by
  "no rule support yet"). This is what makes structure built by an earlier pass explainable.
- **CAPTURE PROVENANCE FORWARD FOR A SELF-EXTINGUISHING RULE.** The backfill can only record what the
  chain can RE-DERIVE. A rule whose own effect falsifies its body cannot be re-derived — the shape
  every REPAIR rule has: it fires *because* something is wrong, and its effect makes it right, so the
  NAC no longer holds and `why` collapses to `(given)`. Run those banks with
  `run_bank(..., provenance=True)` (or `run_rules`, which defaults it on), which journals the
  justification at firing time, while the body still held. The resulting trace threads back through
  the minted structure to the originating facts, with a conjunctive NAC rendered jointly
  (`assumed not: … (together)`).
- **Retraction is copy-on-delete** (`ugm/retraction.py`): **decide** (CASCADE rules, read-only) →
  **record** (`record_history`: copy the pre-image into an inert, meta-visible `<history>` record,
  redirecting `proves`/`uses` so explanation survives) → **retire** (the privileged `RETIRE` opcode,
  assembled only by this driver — ordinary rule lowering structurally cannot emit it). `resurrect`
  re-materializes from history. Monotonicity is MECHANISM within a pass, POLICY between passes.

## 8. One graph, optional rule bank — the public API

Rules are graph data; by default they live IN the knowledge graph (`PATTERN_MARK`, an ordinary
attribute stamped by `write_rule`/`build_head_index` and selected by `derived_triples`, keeps
pattern-space out of the fact view). A separate bank is a consumer's *choice*:

```python
chain_sip(g, goal)                      # rules in g
check(g, goal)
suppose(g, assumptions, predictions)
ask_goal(g, "is ada guilty")            # CNL surface over check/chain
chain_sip(g, goal, rules=bank)          # explicit separate rule graph (e.g. a bank per hypothesis)
```

Fact authoring is itself a program: `lowering.assemble_facts` → `MINT` program → `Machine.run`
(`load_fact_triples`); interning belongs to `MINT(intern=True)`, never to a substrate helper.

## 9. What stays Python forever (the surface)

CNL (forms, `load_corpus`, `ask_goal` rendering, recognition grammar), the AUTHORING/LOWERING
compilers (`write_rule`, `lower_conj` — they PRODUCE programs), `policy`, and the
intake/focus/streaming drivers (`ugm/intake.py`, `ugm/focus.py`, `converse`). These author programs
and call the interpreter; they are the surface, not the core.

## 10. The primitives ledger (A5 — what is genuinely not data-path + control-flow)

Named ops: **TEST-absent** (the fact-read guard), **MEMBER** (live-set restrict), **OVERLAY**
(live-set extend). Still Python, candidates to pin down: **skolem re-finding**
(`_find_skolem_witness`) and **sub-demand raising** (a driver step in `_round`). Keep this list
closed and small; additions go through the processing-modes acceptance test
(`processing_modes.md`).

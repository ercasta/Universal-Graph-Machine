# REFERENCE — the single entry point

> **Status: CANONICAL INDEX (2026-07-07, ratified with the user).** ONE page that states what
> the system is, which decisions are in force, which arcs are active, and what every other doc
> is (live / historical / stale). When this index and an older doc disagree about *status*,
> this index wins; when two live docs disagree about *content*, the precedence chain (§5) wins.
> Cleanup applied 2026-07-07 (user-ratified, post-rehost-session): stale docs deleted,
> historical records moved to `docs/attic/`, and the active plan consolidated into
> `implementation_plan.md`.

## 1. What the system is (one paragraph)

One substrate: a graph of **label-less nodes** (opaque identity + a bundle of graded/valued
attributes under a closed key vocabulary) and **untyped directed edges**. Facts, rules, goals,
plans, and the CNL source itself are all nodes in that one graph. Computation is graph
rewriting, driven **goal-directed** (demand nodes, magic-sets made literal) over a **monotone
fact layer** (facts are never deleted) plus a **non-monotone control layer** (tokens, frames,
scaffolding — freely mutated). Reasoning strategies are a small set of universal, iterative,
fuel-bounded **"system-2" firmware procedures** compiled to a tiny opcode ISA; domain knowledge
and policy live ONLY in CNL banks; Python is physics (opcodes, store, content-blind indexes,
tools). An SLM sits at exactly one boundary (user intent → CNL). The official semantics is
**bounded-defeasible** — answers are the best of current knowledge under a metareasoning
effort budget, not theorems.

## 2. Decisions in force (the ratified stack, newest first)

| Decision | One-liner | Where |
|---|---|---|
| **No backward compatibility** (2026-07-07) | Prior semantics are NOT a constraint; the system is a stratification of research generations — divergences are classified (ratified vs bug), never preserved for their own sake | this doc |
| **Brain-firmware arc** (2026-07-07) | Universal ISA procedures (APPLY, CHAIN, CHECK, CHOOSE, SUPPOSE…) over **reified rules-as-data** replace Python solver psychology; firmware = reference semantics, all fast paths differentially gated | `implementation_plan.md` Phases 4–6 |
| **Attribute-native namelessness** (2026-07-07) | Computation runs on attribute operations; predicates become graded KEYS (`{chase:1.0}`), not node names; `name` is one ordinary valued attr; accelerator indexes only over KB-declared discriminating keys | `implementation_plan.md` Phase 2 |
| **The logic fragment** (2026-07-07) | Horn + stratified completion + defeasible priorities (no contraposition) + reified deontics + declared congruence + labelled-null existentials + possibilistic grades + first-class aggregation/temporal calculators. NO sequent calculus, general disjunction, refutation | `logic_fragment.md` |
| **Processing modes** (2026-07-07) | CLOSED inventory of nine computation modes (SATURATE, ITERATE, CHAIN, CHECK, CHOOSE, SUPPOSE, WALK, CALL, RECORD); procedures = KB-authored compositions running on the ISA; 5-point acceptance test blocks academic imports; hypothesis-verify and plan-check-replan are compositions, not new modes | `processing_modes.md` |
| **AttrGraph re-host** (2026-07-07, LANDED except final peels) | Substrate unified (one label-less AttrGraph); ISA = production answer path + recognition; remaining `rewriter` peels absorbed as Phase 0 of the plan | `implementation_plan.md` Phase 0; history `attic/handoff_attrgraph_rehost.md` |
| **CWA-default, OWA opt-in** (2026-07-07) | Unprovable → defeasible `assumed-no`; `X is open world` per predicate → `unknown`+gather; entailed `is_not` (disjointness) is the hard no | memory `decision-cwa-default` |
| **INTERPOSE opcode** (2026-07-07, design) | Reversible fact-edge interposition as the sole fact-edge operation — TMS becomes ISA-native | `graph low level machine/isa-reference.md` |
| **Label-less substrate** (2026-07-05) | Node = opaque identity + attr bundle; relations reify; goal-direction = demand-forward | `graph low level machine/rule-isa-design.md`, vision amendment |
| **Rule ISA** (2026-07-05) | Rules compile to a small opcode set; purely positive matching core | `graph low level machine/rule-isa-design.md` |
| **Agentic loop inversion** (2026-07-04) | The SUBSTRATE owns trigger→plan→act→observe; the SLM is one scoped `<call>` | `vision_agentic.md` |
| **Planner in CNL** (2026-06-30..07-06) | Entire planner = machine-rule CNL; operator/goal surface merged | `planning_design.md`, `operator_goal_cnl.md` |
| **Walkers & locality** (2026-06-30) | Seed-from-ground df matching; long range = fueled walkers; radius retired | `walkers_and_locality.md` |
| **Metareasoning layer** (2026-06-30) | Content-blind effort policy (fuel, α-cut, radius) — the third layer | memory `decision-metareasoning-layer` |
| **One substrate** (2026-06-28) | Untyped edges, CNL-as-substrate, monotone+control layers, tools as calculators | `vision.md` |

Standing feedback (always in force): **no commits by the assistant**; **no domain logic in
Python** (banks only); **no hardcoded engine policy** (strategies are declared data).

## 3. Target architecture (after the active arcs land)

```
KNOWLEDGE   CNL banks: facts, rules, defaults+priorities, deontics, declarations
            (discriminating keys, open-world predicates, transitivity, coref propagation)
PSYCHOLOGY  Firmware in machine-rule CNL, compiled to ISA: APPLY, CHAIN, COMPLETE,
            PREFER/SELECT, PLAN — serial, fuel-bounded, system-2; all state visible
            as control-layer graph structure (<demand>, <frame>, <fresh>, <current>)
PHYSICS     Opcode machine (SEED/FOLLOW/TEST/MINT/EMIT/DROP_CTRL/INTERPOSE) + AttrGraph
            store + content-blind indexes (by-key df; by-value only for declared keys)
            + tools seam (<call>: tokenizer, arithmetic, aggregation, temporal, clingo, SLM)
ACCELERATORS (optional, differentially gated against firmware): per-rule AOT codegen
            (partial evaluation of APPLY), Rust inner loop, interned/CSR layouts
```

Engine paths: forward `run_to_fixpoint` (recognition + control) and demand-driven solving —
the latter migrating from Python `GoalSolver` to firmware per the firmware arc.

## 4. The active plan

**`implementation_plan.md` is the ONE plan** (2026-07-07). Phases: 0 one-engine (finish the
`rewriter` peel: `run_bank` perf gate → loader swaps → `DROP_CTRL` → `propagate→EMIT` →
delete) → 1 stabilize the oracle → 2 attribute-native conventions → 3 rules-as-data +
collections → 4 firmware v1 (APPLY/CHAIN + trace renderer) → 5 firmware v2 (CHECK/CHOOSE/
SUPPOSE, declared strategies, KB procedures) → 6 demote GoalSolver → 7 performance track.

Ongoing ledgers: `handoff_slm_surface_track.md` (every new CNL form = SLM retrain debt) and
`handoff_joern_arc.md` (code-reasoning corpus).

## 5. Content precedence chain (for live docs)

`reference.md` (status) → `vision.md` + amendments (philosophy; explicitly supersedes all of
`spec/`) → `logic_fragment.md` (semantics contract) + `processing_modes.md` (computation
contract) → `graph low level machine/rule-isa-design.md`
+ `isa-reference.md` (machine design; supersede `comparison-to-current-system.md`'s first
framing) → active handoffs (current state) → design docs (`planning_design.md`,
`operator_goal_cnl.md`, `walkers_and_locality.md`, `graded_means_selection_design.md`,
`depythonization_design.md` (supersedes `coreference_design.md`'s provenance framing),
`coref_as_rules_design.md` (supersedes its implementation)) → guides
(`developer_guide.md`, `kb_authoring_guide.md`, `user_guide.md`, `onboarding.md`).

Critical external eye: `system_critique.md` (2026-07-07 snapshot — reads against the claims).

## 6. Doc map (post-cleanup, 2026-07-07)

**LIVE** (listed in §5, plus): `vision_agentic.md`, `related_work.md`, `architecture.md`
(as-built reference — accurate for the PRE-rehost engine; must be rewritten when the rehost
lands), `consistency_design.md` (plan; gains importance — the fragment makes conflict-lint a
core feature, `logic_fragment.md` Amendment 2), `slm_from_scratch_vs_finetune.md`,
`learning_resources.md`, `CHANGELOG.md`, `graph low level machine/harneskills-foundations*.md`,
`isa-card-trader-coverage.md`, `learning notes/formal_logic_reference.md`.

**DELETED** (2026-07-07 cleanup; recoverable from git — they actively misled):
`cnl_spec.md`, `harness_arch_spec.md`, `corpus_authoring_guide.md`,
`plan_graph_reasoning_refactor.md`, `icecream_demo.md`, `nonconformance_audit.md`,
`file_index.md`, `handoff_firmware_migration.md` (absorbed into `implementation_plan.md`).

**ATTIC** (`docs/attic/` — honest historical records, never authoritative; see its README):
`spec/*`, `discussion/*`, `coreference_design.md`, `handoff_redesign.md`,
`handoff_attrgraph_rehost.md` (remaining items absorbed into the plan's Phase 0),
`isa_origin_conversation.md`.

**Single-role owners:** plan = `implementation_plan.md`; architecture reference =
`architecture.md` (as-built, pre-rehost in places — rewritten at plan Phase 6.2); authoring
guide = `kb_authoring_guide.md`; semantics = `logic_fragment.md` + `processing_modes.md`.

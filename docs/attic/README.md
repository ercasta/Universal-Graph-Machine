# Attic — honest historical records, never authoritative

Design docs, plans, and explorations whose work is **finished, superseded, or rejected**. They are
kept because they hold the *rationale trails* — why a decision went the way it did, what was tried
and reverted — but **nothing in here is a source of truth about the current system**. For that, read
`../README.md` (index), `../reference/` (as-built reference), and `../CHANGELOG.md` (what landed
when). Some docs carry stale status headers ("not started", "design") that predate their build; the
table below is the final word on each.

| Doc | What it was | How it ended |
|---|---|---|
| `firmware_over_isa_design.md` | The locked design for the demand solver as firmware + no privileged partitions | **BUILT 2026-07-14** — the whole arc landed the same day (see its §7 rollout log and CHANGELOG); distilled into `../reference/firmware_reference.md` |
| `isa_control_machine.md` | Design for a control path (PC, CALL/RET, SUSPEND, PRIM) on the ISA | **BUILT 2026-07-14** — all §9 bricks; header's "not started" is stale; now in `../reference/isa_reference.md` §control path |
| `isa_value_operands_design.md` | Value operands as regular `<isa_operand_value>` nodes | **BUILT 2026-07-14** (§7 rollout complete, swapped structural) |
| `mechanism_policy_separation.md` | The two-homes thesis; Probe 1 = copy-on-delete retraction (`RETIRE` + `<history>`) | **BUILT 2026-07-14** (Axis A); Axis B in its companion doc |
| `axis_b_control_registers.md` | Control state → `AttrGraph.registers`; focus stack lift; `ITERATE` | **BUILT 2026-07-14**; the demand-trace lift was tried and REVERTED (it is explanation → stays a graph node) — the probe's sharpest finding |
| `phase_a_demand_firmware.md` | A1 first increment: demand lookup on the shared ISA matcher (additive, cross-checked) | **LANDED 2026-07-14**, then the production swap was taken by the firmware-over-ISA arc; its visibility fork was resolved by dissolution |
| `demand_driven_negation_design.md` | Firmware v3: negation decided on demand by NAF | **BUILT 2026-07-11** + perf follow-on 2026-07-12 (see its AS-BUILT §§) |
| `goalsolver_retirement_design.md` | Phase 6.1: delete GoalSolver + reference Walker | **DONE 2026-07-11** — note the build inverted the design's demand-driven assumption (decided negation is inherently forward) |
| `coreference_as_rules_design.md` | Coref as declared rules over a universal `<mention>` marker; forward `VMATCH` | **BUILT 2026-07-12** (all 5 stages); the same-name DEFAULT was later replaced by reader interning (below) |
| `demand_driven_coref_plan.md` | Make coref fully demand-driven | **REJECTED on perf 2026-07-13** — correct but 3–6× slower (897K EMITs/query); kept for the measurements; superseded by interning |
| `indexing_and_coalescing_design.md` | Hardcoded same-name interning in the CNL reader (`intern_mentions`) | **BUILT 2026-07-13** — the major simplification that closed the coref perf saga |
| `name_demotion_design.md` | Phase 2.3: `name` → ordinary valued attr; declared discriminating-key indexes | **BUILT 2026-07-11** |
| `vocabulary_declaration_design.md` | Phase 2.5: substrate vocabulary consolidated into `ugm/vocabulary.py` | **BUILT 2026-07-11** (crux ratified "consolidate") |
| `walkers_and_locality.md` | The connection model: seed-from-ground, fueled walkers, radius retirement | **PARTLY SUPERSEDED** — seed-from-ground df matching lives on in the matcher; the Python `Walker` was deleted (Phase 6.1) and long-range demand is now the demand chain + focus attention |
| `graded_means_selection_design.md` | Graded preference among competing means (the CHOOSE slice) | **BUILT** as the CHOOSE firmware (`ugm/choose.py`, Phase 5.2); references pre-split docs |
| `rule_isa_design.md` | The original "low-level machine below the rules" design conversation | **BUILT** — the data path 2026-07-05, extended with the control path 2026-07-14; operational truth is `../reference/isa_reference.md` |
| `comparison_to_current_system.md` | The register-machine idea vs the pre-ISA harneskills system | Historical exploration (2026-07-05); its first framing was superseded by `rule_isa_design.md` |
| `isa_card_trader_coverage.md` | Phase-0 coverage map: card-trader banks vs the opcode set | Historical migration record (2026-07-06) |

Docs deleted outright in earlier cleanups (2026-07-07: `cnl_spec.md`, `harness_arch_spec.md`,
`vision_agentic.md`, `planning_design.md`, `operator_goal_cnl.md`, `depythonization_design.md`, and
others) are recoverable from git history; a few code comments still point at them — that is expected.
The pre-split `docs/attic/` of the harneskills era (spec/, discussion/, handoff records) lives in
that repo's history, not here.

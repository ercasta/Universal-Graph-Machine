# ISA value operands as regular nodes — the `<isa_operand_value>` convention

> **Status: LOCKED DESIGN (2026-07-14).** The substrate enabler that must land BEFORE the demand-solver
> firmware-ification (`docs/attic/firmware_over_isa_design.md`, "(X)"). Ratified with the user over discussion. It
> is deliberately NARROW now and GENERAL later (§6).
>
> Prerequisite reading: `docs/attic/firmware_over_isa_design.md` (the no-privileged-partitions principle + (X)),
> `docs/attic/mechanism_policy_separation.md` + `docs/attic/axis_b_control_registers.md` (registers as a home for control
> state), `ugm/machine.py` (the register file `State.regs`, the `SEED`-on-`NAME` accelerator), `ugm/chain.py`
> (`_solve_demand_rule` — the `env` dict this replaces).
>
> Standing rules: no assistant commits; correctness before performance; every step differential-gated against
> the current engine (the reasoning suite + the `chain._CROSSCHECK` harness are the oracle); additive-first,
> nothing deleted until parity.

---

## 0. Why this exists — the blocker it removes

The firmware-ification of the demand solver (`(X)`) needs the per-derivation `env` (a Python `dict[str, str]`)
to become the machine's REGISTER FILE (`State.regs`). The blocker: a demand endpoint is a NAME (e.g. `ada`),
and a name is not a single node — it is a *reference to the coref class of all same-named mentions*, over
which operations aggregate (a fact read unions the mentions; an α-cut takes the max degree over them; a write
picks the canonical `[0]`). So a register cannot simply hold the resolved node — resolving would either fork
(losing the aggregate) or collapse (losing coref). Carrying the raw name STRING in the register instead is an
ugly value/pointer hybrid.

**The resolution (user's design): a register holds ONLY a node-pointer; a name is a REGULAR node carrying a
conventional attribute, which instructions interpret.** No index structure, no new node kind — the crux
dissolves (§3).

## 1. The principle — regular nodes + a convention + instruction interpretation

This is the §2 "no privileged partitions" rule of `firmware_over_isa_design.md`, applied to OPERANDS:

- A **data value** an operand needs (a name, a literal) is a **regular node** carrying the conventional
  attribute **`<isa_operand_value>="ada"`**.
- It is a node like any other. It is NOT a new category/kind and carries NO flag. It is distinguished from an
  entity named `ada` (which carries `name="ada"`) ONLY by **which attribute it carries** and **which
  instructions select it** — differentiation by attribute + use, never a privileged partition.
- **Instructions are defined to interpret such nodes**: an instruction whose operand is a value-node follows
  the pointer and reads `<isa_operand_value>`. The "meaning" lives entirely in the convention + the
  instruction, not in the substrate.

Consequence: **the register file holds only node-pointers** — no raw strings, no scalars-as-data. An operand
becomes a node REFERENCE, so the program's operands are graph data (the homoiconic direction, §6).

## 2. The model

- **Value-node.** A regular node carrying `<isa_operand_value>=V`. **Interned / canonical per distinct value
  V** (one value-node per value), so a register consistently references "the value `ada`". Distinct from any
  entity named `ada`.
- **Registers** bind rule vars to node-pointers: a value-node (for an unresolved name/literal endpoint), an
  entity node (for a matched endpoint), or a pinned node (`ById`). Uniform — always a pointer.
- **Instruction interpretation.** An operation that needs the *entities named ada* reads the value-node's
  `<isa_operand_value>` and matches it against entities' `name` (the current `nodes_named` logic, with the
  TARGET value now sourced from a node instead of a Python string / a register string). The resolution
  MECHANICS are unchanged — only where the operand value LIVES changes.

**Value-nodes do not leak into fact reads** (the attribute convention keeps them out, by construction): a
value-node has no `name` attribute (it carries `<isa_operand_value>`), so `nodes_named` never returns it, and
it participates in no fact relations, so `derived_triples` never sees it. No "hide this kind" filter is needed
— it is invisible to fact reasoning because of *what attributes it carries*, exactly the principle.

## 3. Why this dissolves the fork-vs-aggregate crux

When a var binds to the demand endpoint `ada`, the register points at the **value-node** for `ada` — we do
**NOT** resolve it to entity-mentions at bind time. The same-named resolution and the max-over-mentions
aggregation stay EXACTLY as today, but they happen INSIDE the instructions that interpret the value-node
(reading `<isa_operand_value>`, matching against entities' `name`), instead of a raw string in a dict. So:

- coref-class semantics are preserved for free — no fork, no collapse, no index;
- registers are pure pointers;
- the change is behaviour-neutral by construction and thus differentiable (the `_CROSSCHECK` harness + the
  reasoning suite are the oracle).

The earlier "reify a name-index with member edges" idea (a class node whose edges group same-named mentions)
is REJECTED — that WOULD be a special structure/category, and it forced a fork-vs-aggregate choice. The
value-node carries no member edges; resolution stays value-matching inside the instruction.

## 4. Why it is the enabler for (X)

With value-nodes, the `env`→`State.regs` conversion is CLEAN: every var binds to a node-pointer (value-node /
entity / `ById`), so the register file is uniform and the demand solver's per-atom join threads `State`s, not
a dict. The name-in-register hybrid — the one thing that blocked (X) — is gone. So this lands FIRST, then (X)
sits on it.

(Note: this does NOT by itself delete the `SEED`-on-`NAME` accelerator — a name still resolves to entities by
value-matching `<isa_operand_value>` against `name`. The simplification is the uniform pointer register model,
not the removal of name resolution. Removing/relocating the accelerator is a later, separate question.)

## 5. Control scalars stay scalar (for now)

Axis B deliberately made loop counters / the agenda SCALAR control-register values (control state, ephemeral,
not graph). Those STAY scalars for now. Only DATA values become value-nodes. Making counters value-nodes too
(full "everything is a node-pointer" uniformity) is a possible later unification, not part of this.

## 6. Scope — narrow now, general later (progressive)

- **Now:** value-nodes for the demand solver's register bindings (the (X) enabler). The lowering that builds
  the demand read/body program emits value-node references where it currently embeds names.
- **Later (progressive, ratified):** move MORE inline instruction operands (a `SEED`/`TEST` value, etc.) onto
  value-node references — "**just a matter of changing the lowering program**" — until the whole program is
  graph-native. That is the deferred **meta-circular / program-as-data homoiconicity** milestone
  (`implementation_plan.md` Phase 3 note); this convention is its concrete first step. It also overlaps
  **Phase 7a interning** (a value interned to a canonical node) and the **id-addressed core** (operands as
  node references, not surface names). None of that generality is built now — the convention is designed so it
  *can* be, by changing lowering, without re-touching the interpreter.

## 7. Rollout (additive, differential-gated)

1. **Value-node substrate.** Interned value-nodes carrying `<isa_operand_value>` (get-or-create per value),
   with the read paths able to source an operand value from a value-node. Additive — the existing `name`
   attribute + `nodes_named` stay; value-nodes are new, invisible to fact reads (§2).
   **BUILT 2026-07-14**: `AttrGraph.value_node` (interned via a lazily-declared discriminating index on
   the key — the same facility as `name`) + `AttrGraph.operand_value` (the read half).
2. **Demand-solver bindings → value-nodes.** Where `_solve_demand_rule`/`_facts_matching` carry a name
   endpoint, carry a value-node pointer; interpret it identically (read `<isa_operand_value>`). Differential-
   gate against the current name path (the `_CROSSCHECK` harness).
   **BUILT 2026-07-14**, behind `chain._VALUE_OPERANDS` (default OFF — the swap is the user's gate, the A1
   precedent). With the flag on, `chain_sip` converts NAME goal endpoints to value-node pointers at its
   boundary and the solver converts literal/NAC endpoints at use (`_operand`), so every carried endpoint is
   a `ById` node-pointer; the interpretation lives in the shared endpoint helpers (`_operand_value_of` feeding
   `_candidate_nodes`/`_endpoint_matches`/`_scope_key`/`_endpoint_name`/`_bound_entity_nodes`/
   `resolve_write_node`/`_demand_endpoint` — resolve/match/write/trace by the carried VALUE, never on the
   value-node itself). Gate: `tests/test_isa_value_operands.py` — every scenario runs flag-OFF (oracle) then
   flag-ON with `_CROSSCHECK` also on, asserting identical derivations, `<demand>` traces, and verdicts;
   plus the pointer claim itself (no bare string reaches `_facts_matching`; value-nodes stay nameless and
   relation-free after runs). Suite 407 green; flag-off path proven byte-identical under fixed hash seeds.
3. **Then (X):** `env`→`State.regs` on the now-uniform pointer register model; the demand read/body a program;
   `GRADE`/`VMATCH` for thresholds; interleaving kept.
   **BUILT 2026-07-14** (with the step-2 swap ratified the same day, making the pointer model STRUCTURAL —
   the flag and the name path are retired): per-derivation bindings are `State.regs` (var → node id;
   `chain._ptr`/`_bind_state` replace `_tok_name`/`_bind`); the α-cut and value-join run as EPHEMERAL
   `GRADE`/`VMATCH` programs on the shared machine (`_grades_pass`/`_vmatches_pass` replace
   `_graded_ok`/`_value_matches_ok`), with the coref-class aggregation moved INSIDE the instructions
   (`Machine._operand_nodes`: a value-node register denotes the entities named its value — §1's
   "instructions interpret value-nodes", landed). The A1 production swap also ratified: `_facts_matching`
   runs the shared ISA matcher; the bespoke walk survives only as the `_CROSSCHECK` oracle. Interleaving
   (per-atom sub-demands, NAC generator/control-stack) untouched. Suite 408 green.
4. **Later:** progressive generalization (§6); revisit the `NAME` accelerator; counters-as-nodes (§5).

## 8. Open / deferred

- The `NAME`-`SEED` accelerator's fate once operands are value-nodes (keep as an optimization vs. relocate).
- Counters / control scalars as value-nodes (full pointer uniformity) — deferred (§5).
- Full program-as-data (every instruction + operand a node) — the homoiconicity milestone this seeds (§6).

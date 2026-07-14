# Firmware over ISA (Python) — the demand solver as firmware, and the end of privileged partitions

> **Status: LOCKED DESIGN (2026-07-14).** The ratified plan for finishing the "machine-semantics-are-ISA-
> programs" thesis in **Python** (Rust explicitly deferred — see §11). Supersedes the visibility "fork (a)
> vs (b)" framing in `docs/attic/phase_a_demand_firmware.md` §2: that fork is RESOLVED by dissolution (§5). The
> landed A1 first increment (the ISA-matcher demand lookup, differential-gated) is described in
> `docs/attic/phase_a_demand_firmware.md` and stands.
>
> Prerequisite reading: `docs/attic/isa_control_machine.md` (the control path), `docs/attic/mechanism_policy_separation.md`
> + `docs/attic/axis_b_control_registers.md` (registers as the second home), `docs/vision.md` (§5/§6 homoiconicity,
> no-seam), `ugm/chain.py` (`chain_sip`/`_solve_demand_rule`/`_facts_matching` — the procedure to firmware-ify),
> `ugm/lowering.py` (`lower_conj`/`run_bank` — the forward path already IS firmware), `ugm/machine.py` (the
> interpreter + instruction set).
>
> Standing rules: no commits by the assistant; correctness before performance; every step differential-gated
> against the current engine (the reasoning suite is the oracle); nothing deleted until parity + a swap gate.

---

## 0. Framing — why, now that Rust is deferred

Perf is NOT the driver (bound query ~14 ms, ingest ~12 ms). The goal is **conceptual unification and code
clarity**: the forward path already expresses a rule as an ISA PROGRAM and runs it on one interpreter; the
demand path does the same work in bespoke Python (a second matcher, a dict environment, hand-coded threshold
checks, a hand-coded join). Finishing "firmware over ISA" makes forward and demand share ONE matcher, ONE
binding model (the register file), and ONE control model — the payoff Phase A was always about, independent
of any Rust port. Two things came out of the design discussion: the concrete work (**(X)**, §4), and a
deeper principle it forced into the open (**no privileged partitions**, §2).

## 1. The layers — what "lives where"

1. **The interpreter** — `Machine` / `ControlMachine` (Python, fixed). Executes a fixed instruction vocabulary.
2. **The instruction set (ISA)** — the vocabulary: `SEED`/`FOLLOW`/`TEST`/`GRADE`/`VMATCH`/`MINT`/`BRANCH_IF`/
   `CALL`/`PRIM`/… — each a small Python class. **A "new instruction" = one class + one interpreter branch.**
3. **Firmware programs** — DATA: a list of instruction *instances*, produced by a **lowering compiler**
   (Python) and executed by layer 1. Ephemeral compilation artifacts, not graph nodes.
4. **Drivers** — thin Python orchestration (loop rounds, manage the agenda): `run_bank`, `chain_sip`.

**"Firmware over ISA" = shrink layer 4 by moving its logic into layer 3** (programs built from layer-2
vocabulary, run by layer 1). The forward path already lives here (`lower_conj` emits a program; `run_bank`
only loops). The demand path does not yet — that is the work.

## 2. The guiding principle — no privileged partitions

A node is just a node. **What a node "is" — fact, rule, mention, provenance — is EMERGENT: which attributes
it carries and which rules select it** (the label-less, homoiconic, no-seam substrate). Three current
"partitions" are the SAME anti-pattern — a privileged split baked into the substrate — and all are to be
dissolved:

- **The separate rule graph (`rule_g`).** Not a principle; a convenience. Rules are graph data in the SAME
  graph as facts (homoiconicity). Retiring it is the "one-graph fold" (Phase 3.1 step 2).
- **Kind-flags (`is_control` / `is_inert`).** Not a substrate blessing. They become ordinary ATTRIBUTES that
  rules select on (§3), with no hardcoded matcher behavior.
- **"Special categories" (`<mention>`, an "explanation umbrella").** `<mention>` is just a named node (or an
  attribute) coref rules select; provenance is just nodes carrying an attribute that `why`/meta rules select.
  They "are explanation" ONLY because those rules use them so — not because the substrate privileges them.

Consequence: **differentiation is by ATTRIBUTE + USE**, never by a privileged partition. This is the truest
reading of the vision, and it is what makes the one-graph fold and the kind-flag removal the same move.

## 3. The honest constraint — safe defaults via COMPILER-emitted guards

To read facts and NOT bind to provenance/scaffolding, a program must be able to tell them apart. Two truths
hold together:

1. The distinguisher is an **ordinary attribute** (a `role` key, or a structural convention like "an entity
   endpoint carries a `name`") — **no privileged matcher behavior**; any rule can select it. Its "specialness"
   is emergent (which rules use it), exactly the §2 model.
2. There is a real reason the flag existed: a **safe default**. Purely per-rule guards mean one rule that
   FORGETS the guard silently binds a provenance node as a fact endpoint (a live bug `skip_inert` prevents
   today — else `?s` binds to the `uses` node that justified a relation).

Resolution that keeps BOTH purity and safety: **the guard is emitted by the LOWERING COMPILER, uniformly** —
not hand-written per rule, not hardwired in the substrate. The convention ("a fact read selects entity nodes,
excludes role-marked ones") lives in the **authoring/lowering layer** (Python surface, which is ALLOWED to
know conventions); the substrate stays kind-less and dumb. So authors never repeat it, a forgotten guard
can't happen, and the machine has no privileged category. `inert`/`control` degrade from substrate flags to
**an attribute + a compiler-emitted guard**.

(Primitive to watch, for A5: the guard is a `TEST`-shaped op; if pure has-key `TEST` is insufficient we add a
minimal "test attribute value / test-absent" primitive — a class + an interpreter branch, decided when we
lower the first real read.)

## 4. Decision 2 = (X) — the demand solver's WORK becomes firmware

**Current bespoke Python:** `_facts_matching` (a second matcher — a topology walk), the `env` dict
(`_bind`/`_tok_name`), the threshold checks (`_graded_ok`/`_value_matches_ok`), and the per-atom join loop in
`_solve_demand_rule`.

**Target:** at query time the lowering compiler turns each demanded rule's read+body into an EPHEMERAL program
(the same `lower_conj` the forward path uses), seeded with the demand's bound endpoints. Bindings live in
`State.regs` (not a dict). Threshold/value checks are `GRADE`/`VMATCH` instructions IN the program. The head
is `MINT`. A thin demand DRIVER loops rounds and manages the agenda — legitimately, exactly as `run_bank`
loops the forward path.

**Composability contract (the guardrails that make (X) preserve composability):**
- (i) **user rules are never rewritten or specialized** — only lowered (contrast the magic-set rewrite, §11,
  which mints query-specific rules that accumulate — rejected);
- (ii) **lowered programs stay EPHEMERAL** — never graph-materialized, so NOTHING accumulates in the graph
  (only the `<demand>` trace we already mint, which is the negative's explanation and is swept/GC'd as now);
- (iii) **the interleaving is kept** — the per-atom loop still raises each atom's scoped sub-demand (the magic
  set), and nested NAC subgoals use the control machine's existing register-window save/restore (CALL/RET is
  caller-saved), so a subgoal cannot clobber its parent's bindings. NOT a single monolithic whole-body match
  (that would raise no sub-demands and break the demand closure).

**What dies:** `_facts_matching`'s bespoke walk, the `env` dict, the Python threshold checks. **What stays
Python:** the interpreter, the lowering compiler, and the thin demand driver (round loop + agenda).

> **Note on "the same `lower_conj`" (2026-07-14, as built):** the landed (X) lowers each atom's read to
> an ephemeral program built inline in `chain._facts_matching_isa` (SET/SEED/FOLLOW + the compiler-emitted
> guard + MEMBER/OVERLAY), not through `lower_conj` itself — guardrail (iii) FORBIDS the whole-body
> single-program match `lower_conj` produces (it would raise no per-atom sub-demands and break the demand
> closure). The design's intent — one matcher, one binding model, compiler-emitted visibility — is met;
> literally routing the per-atom program through `lower_conj` would add a call, not unification. Closed.

## 5. Decision 1 — dissolves into (X)

With no kinds, there is no "fact-view mode" on the matcher and no explanation/control umbrella. A **"fact read"
IS a lowered program**: `SEED`/`FOLLOW` + the §3 attribute guard + optional live-set membership. That is the
same mechanism as (X). So Decision 1 is not a separate feature — it folds into the lowering.

- The matcher stays maximally dumb: `SEED`/`FOLLOW`/`TEST` + **one membership op** for live-sets.
- **Focus and scope are register-pointed LIVE-SETS** — a register points at a set of nodes/rels in the graph;
  **focus RESTRICTS** candidates to it, a **scope overlay EXTENDS** the base with it. Membership test =
  machine MECHANISM; set contents = driver POLICY (the mechanism/policy split). Focus + scope unify into one
  concept. A NAC subgoal can inherit or narrow the live-set by pointing at a different register.

## 6. Decision 3 — the demand round-loop becomes firmware

The demand driver's "iterate to fixpoint" becomes a `PRIM` round + `BRANCH_IF`-back program, exactly as
`run_bank`'s fixpoint already is (`docs/attic/isa_control_machine.md` §9.5). New instructions: none (those control
blocks exist). Value: uniformity. Sequenced AFTER (X)'s work (else the `PRIM` just wraps the same Python).

**BUILT 2026-07-14.** Each goal-closure frame is a `ControlMachine` program (`chain._frame_program`):
`SETI budget` → `PRIM(advance)` (run/continue one round) → `BRANCH_IF` fixpoint/budget branches, with the
fuel→UNKNOWN honesty as the budget branch falling through to an `exhaust` PRIM. The NAC subgoal, which was a
Python generator yield at the frame boundary, is now a machine `SUSPEND` (brick #4): the request travels in a
control register onto the `Continuation`, and `chain_sip` is a thin driver over a stack of suspended machines
(push a child frame program per subgoal, `resume` the parent mid-round when it completes). Round internals
(`_round`/`_solve_demand_rule`) remain generators — the mid-round continuation the `advance` PRIM parks — and
the agenda/policy state lives in a driver-owned `_Frame`, scalars in the machine's control registers (Axis B).
Suite 423 green; behaviour identical (same DFS order, same stratification stack).

## 7. Sequencing (pure-shape from the start; don't boil the ocean)

Full de-privileging touches many modules (machine, attrgraph, apply, provenance, retraction, run_bank). We
lock the PRINCIPLE and move (X) already in the target shape, rather than rip out flags globally first:

0. **[BUILT 2026-07-14, swapped structural — see the rollout log in its doc]**
   **ISA value operands as regular nodes** (`docs/attic/isa_value_operands_design.md`) — the SUBSTRATE ENABLER that
   lands BEFORE (X). A demand endpoint NAME cannot cleanly become a register binding, because a name is a
   reference to a coref class (over which operations aggregate), not a single node. Resolution (user's design):
   a register holds only a NODE-POINTER; a value like `ada` is a REGULAR node carrying `<isa_operand_value>=
   "ada"` (interned, distinct from an entity named `ada`, differentiated by attribute + use — no new kind),
   which instructions interpret. This dissolves the fork-vs-aggregate crux (the name stays a reference-as-node;
   resolution/aggregation stay inside the instructions, unchanged) and makes the `env`→`regs` conversion of
   step 1 clean (uniform pointer register file). Narrow now (demand-solver bindings), general later ("just
   change the lowering program" → the program-as-data homoiconicity milestone).
1. **(X) core, pure-shape.** Lower each demand read+body to an ephemeral program — `SEED`/`FOLLOW` + the
   attribute guard (transitionally testing the existing inert/control markers AS attributes, via the compiler,
   not a privileged matcher skip) + live-set membership; `env`→`State.regs` (on the step-0 pointer model);
   `GRADE`/`VMATCH` for thresholds; interleaving kept; differential-gated (the `_CROSSCHECK` harness). This
   lands the design in the target shape WITHOUT needing the migrations first.
   **[LARGELY BUILT 2026-07-14]** Landed: the A1 production swap (`_facts_matching` = the shared ISA
   matcher's `SET`/`FOLLOW` program; the bespoke walk is only the `_CROSSCHECK` oracle now);
   `env`→`State.regs` (bindings are the machine's register file, `_ptr`/`_bind_state`); thresholds as
   EPHEMERAL `GRADE`/`VMATCH` programs, with coref-class aggregation inside the instructions
   (`Machine._operand_nodes`); interleaving + NAC control-stack untouched; `_graded_ok`/
   `_value_matches_ok`/`_bind`/`_tok_name` deleted. Suite 408 green. STILL OPEN from this step: the
   visibility filters (`_rel_matches_pred`, control/inert endpoint skips, focus `keep()`) are Python
   POST-filters on the matched states, not compiler-emitted guard ops in the program — that is the §3
   guard work, folded into step 2/3 (live-sets + de-privileged markers give it its vocabulary).
   **[GUARDS IN-PROGRAM 2026-07-14 — the remainder landed]** The read is now a SELF-CONTAINED program:
   control/inert are dual-written as MARKER ATTRIBUTES (`CONTROL_MARK`/`INERT_MARK`, lockstep with the
   legacy flags at the `add_node`/`set_control`/`set_inert` chokepoints — the §3 transitional form) and
   the §3 guard is compiler-emitted `TEST(..., absent=True)` ops; a bound second endpoint is in-program
   (`TEST` on NAME / `SET`+`SAME` for a pin); focus is the register-pointed `MEMBER` live-set op (§5 —
   contents in `AttrGraph.registers["<focus>"]` = policy, the membership test = mechanism). New A5
   primitives: TEST-absent, MEMBER. The ONE Python post-filter left is the SUPPOSE scope-pencil
   disjunction (`pencil_ok`) — §8's "scope pencils → register-pointed scope overlay". Also removed:
   `Machine._inert_cache` (nid-keyed across graphs — a cold≠warm hazard, pystrider #10). Suite 419.
2. **Live-set mechanism** (register-pointed) → migrate **focus** onto it (already a register), then **scope
   pencils** onto a scope overlay.
   **[BUILT for the demand read 2026-07-14]** `MEMBER` (restrict, by name — focus) and `OVERLAY` (extend,
   by id — the scope's pencils; degenerates to the plain absent-test with no set parked, so ONE program
   shape serves scoped and unscoped reads). The overlay set is derived transitionally from the `SCOPE`
   tags per lookup (`chain._scope_pencils` — the tag stays the pencil's persistent explanation); end-state:
   the suppose/chain WRITERS maintain it incrementally. The forward path (`apply._fact_relnodes` etc.)
   still reads tags directly — its migration rides the one-graph fold.
3. **De-privilege the markers** — `inert`/`control` flags → plain attributes; `<mention>` → attribute /
   named-node; the guard reads attributes, not flags.
   **[control/inert DONE 2026-07-14]** `AttrNode.control`/`inert` are no longer dataclass fields: the
   MARKER ATTRIBUTE is the single source of truth, and the old flags are derived read-properties kept for
   call-site compatibility (every `is_control`/`node.inert` reader now reads attributes through them).
   `set_control`/`set_inert` write only the marker; `copy`/`absorb`/`to_dict` carry markers in `attrs`
   (which also fixed `to_dict` silently dropping inert-ness). `<mention>` → attribute still open.
   **[`Machine.skip_inert` RETIRED 2026-07-14 — the last privileged matcher mode.]** The FORWARD path's
   inert visibility now rides IN the lowered program: `lowering.guard_inert` emits `TEST(..., absent=True)`
   on the `<inert>` marker after every `SEED`/`FOLLOW` bind (exactly what the mode used to skip), applied
   per rule by the bank compiler — a provenance-aware rule (`rule_touches_provenance`, an authoring-layer
   convention read §3 permits) is lowered WITHOUT it, and a fresh provenance-free graph gets guard-free
   programs (the mode's zero-cost OFF path, preserved). `run_bank` runs ONE mode-less machine; the
   `Machine(skip_inert=)`/`ControlMachine(skip_inert=)` params are deleted. The machine now has NO
   privileged category and NO mode. Also fixed (audit item 2): `write_rule` now REJECTS an inverted
   graded condition loudly instead of silently reifying the rule without it. Suite 430.
4. **One-graph fold** — retire `rule_g`; rules join the fact graph, guarded by the same attribute discipline
   (Phase 3.1 step 2's hazard — "pattern nodes must not match as facts" — is exactly what this guard handles).
   **[SUPPORTED 2026-07-14]** `rule_g` may BE `fact_g`: the marker-attribute guards already kept pattern
   nodes out of fact reads; the last gap was the fact VIEW, closed by `PATTERN_MARK` — an ordinary
   attribute `write_rule`/`build_head_index` stamp on rule wiring and `derived_triples` selects on
   (authoring-written, view-selected, never machine-privileged; control-plane derivations like
   `<goal> reached <plan>` are untouched). Parity split-vs-folded gated by `tests/test_one_graph_fold.py`
   (joins, NAF, shared literal names, value-match, skolems, SUPPOSE). Callers still pass two graphs —
   MIGRATING the public API to one graph (retiring the parameter) is the remaining, user-gated step.
   **[API MIGRATED 2026-07-14, user-ratified.]** `chain_sip(g, goal)` / `check(g, goal)` /
   `suppose(g, assumptions, predictions)` — the rules live in the graph itself by default; a SEPARATE
   rule graph remains available as the explicit `rules=` keyword (a consumer's choice — e.g. a fresh
   bank per hypothesis, the pystrider layout — no longer a requirement). All ~104 call sites migrated
   mechanically (tokenizer-based, defs/strings skipped); suite 429 green, no old-form call remains.
5. **Decision 3** (round loop → firmware) + **A5** (write down the irreducible primitives).
   **[Decision 3 BUILT 2026-07-14 — see §6.]** A5 so far: TEST-absent (the fact-read guard), MEMBER
   (live-set restrict), OVERLAY (live-set extend), skolem re-finding (`_find_skolem_witness`, still a
   Python helper), sub-demand raising (`mint` — a driver step in the `_round` generator).

## 8. Migration backlog (so it is not lost)

- `<mention>` → node attribute (or plain named node) selected by coref rules.
  **[RESOLVED 2026-07-14 — already de-privileged.]** `<mention>` is a plain NAMED NODE and the marker is
  an ordinary `is_a` RELATION the universal coref rule selects (`?x is_a <mention> and …`) — it MUST stay
  a matchable relation for that rule to exist, so "→ attribute" would be a regression. The only special-
  casing is view-level (`derived_triples` hides the handle), not matcher privilege. Nothing to do.
- SUPPOSE pencils → register-pointed **scope overlay** (retires the pencil half of the transitional guard).
- `<call>` / dispatch state → registers / ephemeral (confirm none is a persisted fact-graph node).
- `is_control` / `is_inert` → ordinary attributes; the fact-read guard tests attributes, not flags.
- `rule_g` → folded into the one fact graph (the one-graph fold).

## 9. What stays Python forever (the surface) — never firmware

CNL (forms, `load_corpus`, `ask_goal`, `render`, recognition grammar), the AUTHORING/LOWERING compilers
(`write_rule`, `lower_conj` — they PRODUCE programs), `policy`, and the intake/focus/streaming drivers. These
author programs and call the interpreter; they are the surface, not the core.

## 10. Primitives to name (A5 — the minimal irreducible set)

What genuinely is NOT data-path opcodes + control flow, to be written down as a small named set:
- the fact-read **attribute guard** op (test attribute value / test-absent), if has-key `TEST` is insufficient;
- **live-set membership** (the register-pointed restrict/extend op);
- **skolem re-finding** (`_find_skolem_witness` — structural re-identification of a minted node by its
  defining relations);
- **sub-demand raising** (mint a `<demand>` trace) — likely a driver step, but pin down whether it is an op.

## 11. Explicitly deferred / rejected

- **Rust port (Phase B, `docs/design/rust_engine_plan.md`).** Deferred. This document is its Phase A, minus the Rust
  framing and minus the "freeze the instruction set" pressure — in Python we are free to ADD clean primitives.
- **Magic-set rewrite ("(Y)").** REJECTED for the demand solver: it would recompile per query and mint
  query-specific rules that accumulate as graph structure (fighting monotonicity / composability), and
  re-deriving stratified-NAF soundness + the fuel→UNKNOWN honesty under the rewrite is research-grade risk.
  (X) keeps the user's rules stable and the graph monotone.

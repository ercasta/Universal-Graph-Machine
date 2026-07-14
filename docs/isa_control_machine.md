# The ISA Control Machine — control flow as instructions, not procedures

> **Status:** DESIGN / ALIGNED, not started (2026-07-14). ⚠**Foundational** — this touches the machine's
> control model (the deepest layer), so it needs vision-judgment, not mechanical execution. Produced from
> the design conversation that followed Axis B (`docs/axis_b_control_registers.md`): building `ITERATE` as
> a §8 exemplar surfaced a **seam** — a loop can't contain a subgoal — which unwound into the realization
> that the ISA has a data path but no **control** path. The crux (§10) is now **resolved**: the control
> plane is **forward-only** (backward/demand reasoning is an above-plane tabled-solver *program*, not a
> reverse plane), evaluation model **A** (two programs on one forward plane, no backtracking), interpret-by-
> default with compilation as a rule-version-keyed optimization. **Ready to implement in a fresh session;
> start at §9 brick #1.** Standing rules: no commits by the assistant; correctness before performance; the
> reference interpreter stays naive + differential-tested.
>
> **PROGRESS (2026-07-14):** bricks **#1 (PC + BRANCH/BRANCH_IF/SETI/DEC, ITERATE-as-primitives)**,
> **#2 (CALL/RET + control stack)**, the **`PRIM` interpreter step (§10 two-levels)** and brick
> **#4's SUSPEND/RESUME continuation mechanism** are BUILT — see §9. `ugm/machine.py` gains a
> `ControlMachine` layered on the untouched two-phase `Machine`; `tests/test_isa_control_machine.py`
> (23 tests) covers the loop differential-test, subgoal/recursion via the stack, PRIM fixpoint-as-
> branch-back, and suspend/resume (incl. the internal-subgoal service-loop shape brick #3 uses).
> **KEY FINDING (§9.3):** chain_sip's ONLY Python recursion is the NAC negative subgoal (`_nac_blocks`),
> a *synchronous mid-solve* call → its faithful de-recursion needs a CONTINUATION (brick #4's
> SUSPEND/RESUME), which is why #4's mechanism was built before #3. SUSPEND/RESUME is realized as a
> resumable `Continuation` (full control state) + a driver `resume`; the service-loop over suspensions
> carries arbitrary subgoal depth with no Python recursion. **Brick #3 (chain_sip port) is now DONE**
> (§9.3): the NAC subgoal descent is de-recursed onto an explicit control stack (generator-based, the
> yield = the CALL, the driver stack = the control stack), behaviour-identical (whole reasoning suite
> the oracle), proven by a 601-deep NAF stratification that runs under a recursion limit of 200. Suite:
> **ALL SLICES DONE (2026-07-14): the arc is complete.** #5 (run_bank fixpoint → control-machine program:
> round-counter for-guard + a `PRIM` collect-then-apply round + branch-back over a `changed?` flag + a
> final drop-GC `PRIM`) and #4-slice (dispatch → a control-machine program; sync inline, async via
> `SUSPEND`/`RESUME` with a simulated `AsyncTool` exercising suspend→host-answers→resume→fold end-to-end).
> Every Python control driver named in §1 (`ITERATE`'s hidden `for`, `chain_sip`'s recursion, `run_bank`'s
> fixpoint, `dispatch`'s loop) now runs as control-machine instructions; the seam is closed and the async
> tool wait — the last piece with no prior consumer — has one. Suite: **385 passed** (355 baseline + 30).
>
> **Prerequisite reading:** `ugm/machine.py` (the match-then-apply interpreter + its docstring's
> "reference vs optimized" note), `ugm/chain.py` (`chain_sip` — subgoals as Python recursion),
> `ugm/lowering.py` (`run_bank` — the fixpoint driver), `ugm/dispatch.py` (`<call>` servicing),
> `docs/mechanism_policy_separation.md` §8 + `docs/axis_b_control_registers.md` (the register file this
> builds on).

---

## 1. The problem: procedures masked as instructions

Some UGM "instructions" are **procedures with hidden control flow**, and that hidden control flow is
exactly what kills composability:

- **`ITERATE` is a loop procedure, not an instruction.** Its iteration is a Python `for` *inside* the
  opcode (`machine.py`: `for i in range(count): yield …`). Nothing can interleave with it — so a loop
  whose body needs a **subgoal** (raise a demand, reason, use the result) is inexpressible. *That is the
  seam.*
- The **genuine** procedures aren't even masked: `run_bank` (fixpoint loop), `chain_sip` (recursive
  subgoal descent), `service_calls` (dispatch loop) are Python **drivers**. They *are* the control flow,
  living entirely **outside** the ISA.
- A match-then-apply "program" has **no internal control flow at all** — no program counter, no branch.
  It is a single straight-line **basic block**.

So the ISA today is: *straight-line basic blocks + Python for every control transfer.* Control cannot
compose because it is not in the machine; the ops that *do* surface control into the ISA (`ITERATE`) hide
it inside themselves. Bulk ops are fine — but they must be **straight-line**; the moment an op hides a
loop that might subgoal, composability breaks.

---

## 2. Diagnosis: a data path with no control path

The machine has the **data path** of a real machine — a WAM-style register file (`State.regs` +
`AttrGraph.registers`), a matcher, monotone effects — but not its **control path**. The result is that
control flow is faked in **two split homes**:

1. **Python** — `run_bank`/`chain_sip`/`dispatch` hold the loops, the recursion (the subgoal stack *is*
   the Python call stack), and the dispatch agenda.
2. **`<…>` graph nodes** — `<frame>` (activation record), `<current-atom>` (cursor), the `<demand>`
   agenda, `<call>` (pending request) materialize control state as data-graph nodes.

Both are symptoms of the same missing thing: an **explicit control machine**. This is also why
"machine-semantics-are-ISA-programs" is only half-true today — the *reasoning* control (subgoals,
fixpoint, dispatch) is Python, not ISA.

---

## 3. The parallel to a real ISA

UGM has the data column and is missing the **entire control column**:

| Concept | Real ISA (x86/ARM/RISC-V) | UGM today |
|---|---|---|
| Instruction pointer | **PC / IP** | **absent** — a program runs once, no PC |
| Sequential step | `PC += 1` | implicit list walk in `Machine.run` |
| Unconditional jump | `JMP addr` | **absent** → Python loops |
| Conditional branch | `JZ/JNZ` (test flags) | **absent** → NAC/decide in Python |
| Call subroutine | `CALL` (push retaddr→SP; PC=addr) | **absent** → subgoal = Python recursion (`chain_sip`) |
| Return | `RET` (pop SP→PC) | **absent** → Python `return` |
| Stack pointer | **SP** + call stack in memory | **split**: Python call stack + `<frame>`/`<demand>` nodes |
| Registers | finite named regs | `State.regs` (ephemeral) + `AttrGraph.registers` (persistent) ✓ |
| Condition codes | flags from `CMP` | **absent** — `TEST`/`GRADE` prune the state stream |
| Bulk / vector | `REP`, SIMD | `ITERATE`, bulk `MINT`/`RETIRE` ✓ |

The `registers` half already landed (Axis B). The missing half is **PC, branch, CALL/RET, and an
explicit stack pointer** — the control machine. (machine.py's docstring already says "WAM-style register
file": we have the WAM's registers, not its *control*. The WAM's whole point is that a subgoal is a
`CALL` and an explicit **stack** carries arbitrary-depth nesting.)

---

## 4. The proposed control layer

Add the missing control machinery as **primitive, composable** instructions — "explicit instructions for
setting the control pointer" — beneath the current match-then-apply data ops.

1. **A control pointer (PC)** on the machine, indexing an **addressable program**: a list of **labeled
   basic blocks**. A basic block is a straight-line match-then-apply program (today's `Machine.run` unit)
   ending in a **terminator** (fall-through / branch / call / ret).
2. **Control-transfer instructions** (the new primitives):
   - `BRANCH label` — `PC = label`.
   - `BRANCH_IF reg[, cmp, value], label` — conditional; loops are branch-back.
   - `CALL label` — push a **frame** {return-PC, saved register window} onto the **control stack**;
     `PC = label`. Subgoals compose to any depth via the stack.
   - `RET` — pop a frame; restore PC + window.
   - `SUSPEND` / `RESUME` — save/restore the whole control stack + PC as a **continuation** (for a tool
     `<call>` / an `ask_user` wait — the streaming suspend/resume the intake design wants).
   - Counter arithmetic on the control registers: `SETI reg,int`, `DEC reg` (minimal loop kit).
3. **The control stack (SP)** — the growable heap stack held in a register (`AttrGraph.registers` or a
   machine-level control context — the growable-heap-in-a-register-slot from the Axis B boundary
   discussion). Frames hold return-PC + local bindings/agenda. This is where arbitrary-depth subgoals
   live — the WAM environment stack.
4. **`Machine.run` becomes fetch-decode-execute** over the PC: run the block at PC, then its terminator
   sets the next PC (or CALL/RET move the stack).

Everything composes:
- **loop** = `SETI i,N; L: <body block>; DEC i; BRANCH_IF i>0, L` — and the body block may `CALL` a
  subgoal. `ITERATE`-with-subgoal is now trivially expressible (the seam is gone).
- **subgoal** = `CALL solve_goal`, which itself loops and `CALL`s recursively; the control stack nests to
  any depth. This is `chain_sip` — *in the machine*.
- **dispatch** = `CALL tool` + `SUSPEND`/`RESUME`. `<call>` becomes the `CALL` instruction, not a node.
- **`ITERATE` / bulk ops stay** — like `REP`/SIMD, straight-line conveniences layered *on* the primitives
  for the data-parallel common case. They are no longer the *only* loop, and anything that must subgoal
  uses the primitive loop.

---

## 5. Why this unifies the open threads

The missing control machine is the root of nearly every live issue:
- **The seam** → gone (loops + subgoals compose in-machine).
- **"Procedures masked as instructions"** → `ITERATE` decomposes; the Python drivers become ISA programs
  — finally realizing "machine-semantics-are-ISA-programs".
- **The `<…>` control tokens** (Axis B) → the control-*mechanics* ones are the materialized stand-ins for
  the absent PC/stack; they move into the control stack/registers. The *explanation* ones stay in the
  graph (§6).
- **`<call>`/dispatch** → reframed: not "lift a token to a register," but **"add the `CALL` instruction"**
  — the first real brick of the control machine.

---

## 6. The `<…>` triage — explanation (graph) vs control-mechanics (machine)

The recurring pattern (proven by `<demand>` and `<call>`): a token's **record** is explanation → stays a
matchable graph node; its **mechanics** → the control machine. Applying the discriminator to the full
inventory:

- **Explanation / reasoned-over → stays MATERIALIZED in the graph:** `<j:…>` + `<axiom>` (provenance),
  `<demand>` *record* (the negative's provenance — the subgoal chain), `<history>` (retraction),
  `<check>`/`<suppose>` *verdicts* (rules branch on them), `<hypothesis>` *scope facts*, `<mention>`
  (coref), `<contradiction>`/`<error>`, `<graded>`.
- **Control-mechanics → the control machine (PC/stack/regs), NOT graph nodes, NOT ad-hoc Python:** the
  demand **agenda** (vs. its record), `<frame>` (activation record), `<current-atom>` (cursor), `<call>`
  **return/resume + pending agenda** (vs. the call record), `<suppose>`/`<hypothesis>` **active-scope
  pointer**, `<last-rule>` cursor, `<retract>` request.
- **Pure cache / memo → register/sidecar, invisible:** `<head-index>`.
- **Parse / reification IR (compile-time, GC'd) → scratch/ephemeral:** `<sentence>`, `<query>`,
  `<qevent>`, `<wh>`, `<atom>`, `<rule>`, `<fresh>`, `<focus-op>`, `<rule-op>`, `<bank>`.

Most tokens **split** (like `<demand>`/`<call>`): the record is explanation (graph), the mechanics go to
the machine.

---

## 7. Performance strategy: instruction set = contract, interpreter = swappable

Decomposing bulk procedures into primitives **multiplies instruction dispatch** — in Python that gets
*slower* (measured: planning.cnl recognition is already 6.1M `isinstance` dispatches ≈ 1s; `ITERATE×N` as
N×`(body+DEC+BRANCH_IF)` multiplies it). This is acceptable because the **instruction set is the stable
contract and the interpreter is a swappable implementation** (machine.py's "reference vs optimized" split):

1. **Get the semantics right in the naive Python reference**, differential-tested. Do **not** prematurely
   optimize the Python interpreter for the finer stream.
2. **Cash in Rust when perf is the long-pole.** In a compiled machine the opcode is an `enum`, dispatch is
   a `match` (jump table, no isinstance), states/graph are structs/CSR — per-instruction cost drops 1–2
   orders of magnitude. The finer instruction stream is exactly what compiled dispatch eats cheaply, so
   decomposed-in-Rust can be **net faster** than coarse-Python.
3. **The control-machine redesign is what makes the Rust port CLEAN.** Today a Rust "machine" would have
   to re-port the Python drivers too (the seam). Once control lives in the ISA, the port is one bounded
   fetch-decode-execute loop + register/stack/graph ops. Abstraction-correctness *enables* the perf port.
4. **Rust buys the CONSTANT, not the CURVE.** Rust attacks per-instruction overhead. It does **not** fix
   algorithmic super-linearity — the #1 measured risk, session-accretion NAF going **267ms → 11.7s** as a
   bound query's KB accretes (274 → 1424 nodes), is super-linear in KB size. That needs **seed-from-focus**
   (the flat 64 → 87ms line — a 133× gap at case 10), the Axis B register work, not a faster interpreter.
   **Rust for the constant, focus-scoping for the curve** — two levers, two costs.

---

## 8. Seed-from-focus: the attention scope of a `CALL` (the curve lever)

Seed-from-focus is where the whole arc closes — Axis A (retraction), Axis B (registers), and this control
machine compose into one story. It is the **algorithmic** lever for the accretion curve (§7.4 — the
measured 133× gap), complementary to Rust's constant-factor lever.

**What it is (already built — Phase 8.3b, `chain._facts_matching`).** Bounded, opt-in attention: when a
caller selects `attention="focus"`, the demand chain sees a fact **iff either endpoint touches the working
set** (the top focus frame's centers). Reasoning follows edges out of focus entities but cannot start from
or jump to an entity disconnected from focus — so per-utterance cost tracks the **focus closure**, not the
accreted session (the flat 64→87ms vs. super-linear 267ms→11.7s). It is a **semantic** scope, not a neutral
tweak: off-focus facts leave the agent's attention (the agent-not-theorem-prover reading).

**Its place in the control machine — the SCOPE of a subgoal `CALL`.** The demand *agenda* is control-machine
mechanics (§6: agenda → control stack). Seed-from-focus is precisely **the scope that bounds that agenda's
fact-view**: a top-level `CALL solve_goal` is scoped to the focus centers (a fact is visible iff it touches
them; the goal itself is typically a center — `ingest` widens focus with the question's subject first). The
three pieces slot together cleanly:
- the **focus register** (`registers["focus"]`, Axis B) is the attention scope — a register read;
- the **`CALL`** (this doc) is the mechanism — how a subgoal descends;
- **seed-from-focus** is the **policy** that bounds the `CALL`'s fact-view to the focus closure.

Mechanism/policy stays clean: `CALL` is mechanism; the focus-scope is policy (caller-selected
`attention="focus"|"global"` — the engine never picks scope for the user). The control machine simply admits
a **seed scope** on a subgoal `CALL`; the focus register supplies it under the focus policy.

**Slice implication.** When `chain_sip` ports onto `CALL`/`RET` (§9.3), the bounded-attention filter must be
**preserved by construction** — a subgoal `CALL` carries its seed scope, so a focus-scoped query stays
bounded through the port. The control-machine decomposition is about composability + the constant-factor
Rust story (§7); the *curve* is held by this section, unchanged. Both levers, kept distinct.

---

## 9. Slices (executable order — §10 resolved; brick #1 is the entry point)

1. ✅ **Brick #1 — PC + `BRANCH`, and `ITERATE` re-expressed as primitives.** *(BUILT 2026-07-14,
   `ugm/machine.py` + `tests/test_isa_control_machine.py`.)* Added the control pointer and
   `BRANCH`/`BRANCH_IF`/`SETI`/`DEC`, plus `Block`/`ControlMachine` (fetch-decode-execute over a
   PC-indexed program of labeled basic blocks). A bounded loop is now `SETI/…/DEC/BRANCH_IF` over a
   basic block; a differential test confirms it reproduces `ITERATE`'s graph effects exactly (node
   counts + `derived_triples`), including the zero-trip case. The `ControlMachine` LAYERS ON the
   untouched two-phase `Machine` (the basic-block primitive) — no existing opcode changed, suite green.
   Loop counters are SCALAR control registers (`ControlMachine.ctrl`, a machine-level control context —
   §4.3's sanctioned alternative to `AttrGraph.registers` for ephemeral per-run state). `ITERATE` stays
   as the REP/SIMD convenience.
2. ✅ **`CALL`/`RET` + the control stack.** *(BUILT 2026-07-14, same files.)* `CALL`/`RET` are block
   TERMINATORS (§10) that push/pop `ControlMachine.stack` — frames of (return-PC, saved register window
   = state stream + control snapshot). The callee gets a fresh window and the SHARED graph, so its fact
   writes persist and the caller reads them after `RET` (the subgoal model); the control snapshot is
   caller-saved (a counter passes an argument down, restored on return). Tests cover subroutine call +
   return, caller-window preservation, depth-3 nesting, and bounded RECURSION carried by the explicit
   stack (not Python) — the WAM environment stack `chain_sip` fakes today, ready for brick #3.
3. ✅ **Port `chain_sip` (subgoals) onto `CALL`/`RET`.** *(BUILT 2026-07-14, `ugm/chain.py` +
   `tests/test_isa_naf.py`.)* The ONLY Python recursion in the demand solver was the NAC negative subgoal
   (`_nac_blocks` → `chain_sip`), a synchronous mid-solve call. Ported via a GENERATOR de-recursion:
   `_nac_blocks`/`_solve_demand_rule` are now generators that YIELD `("subgoal", neg_goal, child_neg_stack)`
   instead of recursing; `chain_sip` became a DRIVER over an EXPLICIT control stack of `_close_goal`
   frames — the WAM environment stack — that pushes a child frame per subgoal and resumes the parent on
   completion (same DFS order → behaviour-identical, the whole reasoning suite is the differential oracle,
   379 green). `neg_stack` (stratification) IS the control stack; the demand *record* stays a `<demand>`
   graph node (explanation, §6); the per-frame agenda stays a local register. Proven de-recursed by a
   601-deep NAF stratification that completes with Python's recursion limit set to 200 (the old recursive
   descent, ~4 frames/stratum, would `RecursionError`). This realizes the continuation via Python
   generators — the yield IS the `CALL`, the driver stack IS the control stack; a machine-level
   `SUSPEND`/`RESUME` (brick #4 mechanism) is the same shape one level down.
4. ✅ **Port `dispatch` (`<call>`) onto `CALL` + `SUSPEND`/`RESUME`.** *(BUILT 2026-07-14, `ugm/dispatch.py`
   + `tests/test_isa_dispatch_async.py`.)* The dispatcher is now a control-machine PROGRAM
   (`_dispatch_program`/`service_calls_cm`): a `find_next` `PRIM` branches on call KIND (none/sync/async),
   a sync tool runs inline (a `PRIM` reusing the `service_calls` helpers) and branches back, an ASYNC tool
   computes its request, `SUSPEND`s (handing it to the host), and on resume folds the response and branches
   back. Two host protocols: an `answer` callback drives the suspend/resume loop internally, or (omitted)
   the dispatcher returns a `Continuation` on the first async call so the CALLER owns the wait — the true
   streaming boundary. A simulated async tool (`AsyncTool`, a `request`/`fold` pair around the `SUSPEND`)
   exercises it end-to-end: suspend → host answers → resume → fold, incl. mixed sync+async batches and a
   fold that spawns a downstream call (serviced by the re-scan loop). The `<call>` RECORD stays a graph
   node (§6); only the return/resume mechanics became instructions. `service_calls` (the flat loop) stays
   as `run_bank`'s in-fixpoint sync servicing; `service_calls_cm`'s sync path is differential-tested to
   match it.
5. ✅ **Port `run_bank`'s fixpoint** onto the control machine. *(BUILT 2026-07-14, `ugm/lowering.py`.)*
   The Python `for _ in range(max_rounds)` driver loop is now a control-machine program: a round-counter
   (the `for` bound), a for-guard `BRANCH_IF`, a ROUND block whose `PRIM` runs one collect-then-apply
   round and reports a `changed?` flag, a branch-back while it changed, and a final `PRIM` for the
   drop-orphan GC. `run_bank` ASSEMBLES the program and runs it — it no longer HOLDS the loop.
   Behaviour-identical (the recognition/planning/reasoning banks that pervade the suite are the
   differential oracle: **379 green**). The tool-service `continue`/`break` map to the round's
   `changed`=1/0; the `max_rounds` bound is faithfully the round counter.
6. **(Later, perf) the Rust interpreter** over the now-stable instruction set, differential-tested against
   the Python reference.

---

## 10. Resolved — the evaluation model (2026-07-14 discussion)

The crux is settled; the design is ready to build.

**The control plane is FORWARD-ONLY — we do NOT need reverse execution.** Demand-driven ("backward")
reasoning lives ABOVE a forward-only plane, as a program. Three reasons:
- **Magic-sets is a theorem** that backward reduces to forward: it rewrites a goal-directed query into
  ordinary forward rules (+ demand/"magic" predicates) whose BOTTOM-UP evaluation yields exactly the
  demanded answers. Backward is a source/scheduling property, compilable away — the plane underneath is
  strictly forward.
- **Every resolution step is forward:** look up producing rules (head-index), push a frame + recurse
  (`CALL`), iterate to fixpoint, read/write the answer table, return. "Backward" is the DATA-DEPENDENCY
  direction (conclusion→premises), NOT the execution direction — like a compiler's backward dataflow
  analysis running on a forward CPU.
- **Nothing to undo:** UGM is monotone / tabled / set-at-a-time (breadth over all producing rules), so
  there are NO choice points and NO backtracking — the one "reverse-ish" bit of classical logic
  programming (trail unwind) never arises.

**Evaluation model = A, refined: two PROGRAMS on one forward plane, not two planes/modes.**
- forward (bottom-up fixpoint) = a `BRANCH`-back-to-fixpoint block;
- backward (demand) = a tabled-solver block that `CALL`s sub-goals and consults a memo table.
Neither is privileged; the core stays tiny; the set-at-a-time matcher stays the basic-block primitive.
Value between blocks is a set of states; loop counters + control stack are scalar control registers. **B
(tuple-at-a-time backtracking WAM) is REJECTED** — wrong paradigm for a tabled, monotone, set-at-a-time
engine.

**`CALL` has two flavors, no new opcode.** A forward `CALL` is an x86-style subroutine (a tool
`<call>`/dispatch). A `DEMAND` is just a `CALL` to the tabled-solve ROUTINE, the table an ordinary data
structure the routine reads/writes (`BRANCH_IF already-tabled`). Tabling is a PROGRAM over a memo table,
not a primitive — "machine-semantics-are-ISA-programs" applied to the reasoner itself.

**Two levels of program.** ISA control (PC/BRANCH/CALL over basic blocks) = the ENGINE's procedures. The
reified rule graph = the REASONING program, interpreted on top (data-directed). The control machine RUNS
the rule-graph interpreter; it does not replace demand-driven reasoning.

**Interpret vs compile = an above-ISA OPTIMIZATION, not an ISA question.** Because the "program" is MUTABLE
DATA (user utterances rewrite rules via `ingest`), compilation is never AOT-once — it is a
cache-invalidated optimization:
- the **interpreted tabled solver is the robust default** (re-reads the rule graph each demand → immune to
  rule churn, always current);
- **magic-sets / clause→basic-block compilation is opt-in**, keyed on a rule-set version. FACTS do not
  invalidate it (it rewrites rules/IDB, not facts/EDB — and facts churn far more than rules), so a
  recompile amortizes over the whole stretch between rule edits. ADDITIVE rule edits are monotonic (the
  artifact stays sound → patch incrementally); RETRACTING/editing a rule is the non-monotonic hard case
  (the same TMS problem Axis A solves).

**Minor calls (do NOT gate brick #1):**
- `CALL` is a block TERMINATOR phase (neither match nor effect); two-phase match-then-apply stays WITHIN a
  block.
- The memo table + control stack live in `AttrGraph.registers` (travels with the graph, deep-copied → free
  suspend/resume persistence).

---

## 11. What this is NOT

- Not a rewrite of the matcher (§10 keeps set-at-a-time matching as the basic-block primitive).
- Not backtracking search (monotone fixpoint reasoning — no choice points).
- Not a perf project (correctness-first; Rust is the reserved escape hatch, §7).
- Not the retirement of `is_control`/`<…>` wholesale — that follows once the control-mechanics tokens have
  moved (§6), as a later cleanup.

# Rust Engine Plan — procedures as ISA firmware, then port one interpreter (Phase 7b)

> **Status: PLAN (2026-07-14), NOT STARTED.** The path to a Rust core with Python as the surface. The
> KEY STRATEGY (ratified with the user 2026-07-14): **do NOT reimplement the engine's procedures in Rust.**
> Instead, first finish expressing them as **ISA PROGRAMS (firmware over the control machine)** in Python,
> so the only thing left to port is the **ISA interpreter** — the procedures come along as DATA (programs)
> that a Python and a Rust interpreter run identically. This is the whole point of the control machine
> (`docs/isa_control_machine.md` §7.3: "Once control lives in the ISA, the port is one bounded
> fetch-decode-execute loop") and the "machine-semantics-are-ISA-programs" thesis.
>
> Written for a FRESH session (autonomous, multi-hour capable). **Prerequisite reading:** `docs/isa_control_machine.md`
> (the control path — what firmware-ification builds on), `docs/graph low level machine/isa-reference.md`
> (the instruction-set CONTRACT), `ugm/chain.py` (`chain_sip`/`_solve_demand_rule`/`_facts_matching` — the
> procedure to firmware-ify), `ugm/lowering.py` (`run_bank`, `lower_conj` — the ISA matcher already used by
> the forward path), `ugm/attrgraph.py` (the substrate to port), `bench/rust_pilot/` (the 381× pilot).
>
> **STANDING RULES:** no commits by the assistant; correctness before performance; the Python engine STAYS
> the reference oracle — every step DIFFERENTIAL-TESTED against it, nothing deleted until parity + a swap
> gate; determinism is a hard requirement (§2); incremental, no big-bang rewrite.

---

## 0. The strategy in one screen

Two phases. **The hard, valuable work is Phase A (Python); Phase B (Rust) becomes bounded because of it.**

- **Phase A — "procedures as ISA firmware" (Python).** Today the control machine carries the CONTROL of the
  engine's procedures (loops, subgoals, fixpoints — bricks #1–5), but some per-step WORK is still bespoke
  Python. Finish pushing that work onto the ISA so each procedure is an ISA PROGRAM + a small set of
  irreducible PRIMITIVES. Payoff EVEN WITHOUT RUST: forward and demand reasoning unify on ONE matcher; the
  duplicate bespoke matcher dies; the "machine-semantics-are-ISA-programs" thesis is complete.
- **Phase B — port the ISA interpreter to Rust.** Substrate + matcher + control machine + the minimal
  primitive set. The rules AND the reified solver procedures are DATA both interpreters run identically. The
  Rust port is ONE fetch-decode-execute loop, not N reimplemented procedures.

**Why this and not "port chain_sip to Rust":** reimplementing `chain_sip`'s subtle semantics (NAF
stratification, skolem re-finding, coref fan-out) in Rust is the highest-risk work imaginable. If instead
`chain_sip` IS an ISA program, there is nothing procedure-specific to port — Rust interprets the same
instruction set Python does, and the solver is portable data. The control machine was built for exactly this.

**The measured prize (Phase B).** Match inner loop: 111 ms Python vs 0.29 ms native Rust ≈ **381×**
(`bench/rust_pilot/`). Amdahl-bounded end-to-end (the loop is ~78% of recognition → ~4.5× there unless all of
it is ISA-interpreted — which is exactly what Phase A ensures). Rust buys the CONSTANT; seed-from-focus (built)
holds the CURVE — orthogonal.

**Preconditions / honest guardrails:**
- Perf is NOT the current bottleneck (bound query ~14 ms, ingest ~12 ms, demos ~1 s). This plan is READY for
  when a real target-scale workload is measurably too slow; it is not a mandate to start now.
- FREEZE the instruction set first (the control path landed 2026-07-14; let it settle via Phase 8 client use).
  Phase A may ADD a few irreducible primitives (that is expected — it discovers the minimal set); once Phase A
  settles, the instruction set is the frozen contract Phase B ports.
- The cheap PURE-PYTHON rung (Phase 7a: dispatch-table for `_match_step`, int-interned keys, array register
  states) is the near-zero-risk 2–3× if perf bites before either phase is justified.

---

## 1. Current state — how far firmware-ification already got

- **`run_bank` (forward):** already largely ISA firmware — it runs LOWERED rules (`lower_conj` →
  SEED/FOLLOW/TEST/JOIN/GRADE/VMATCH) through the ISA matcher, and its fixpoint is now a control-machine
  program (a PRIM round + BRANCH_IF-back, brick #5). Remaining: the round PRIM's collect-then-apply body is
  Python glue.
- **`chain_sip` (demand):** control skeleton is on the machine (brick #3 — subgoal descent = the control
  stack), BUT the WORK is bespoke Python: `_facts_matching` topology-walks from bound endpoints (a SECOND
  matcher, not the ISA one), the env is a Python dict (not the register file), and `_solve_demand_rule`
  raises/reads sub-demands in Python. THIS is the main Phase-A target. **UPDATE 2026-07-14:** the
  single-atom lookup half now HAS an ISA-matcher implementation, differential-proven equal (see A1's
  first-increment note in §2); the env-dict + interleaved sub-demand raising (A2) is the remaining half.
- **`dispatch`:** `service_calls_cm` is a control-machine program already (brick #4-slice); sync inline,
  async via SUSPEND/RESUME. Little left.

So Phase A is mostly about the **demand solver's WORK layer**.

---

## 2. Phase A — finish the firmware-ification (Python; the real work)

Express `chain_sip`'s per-step work as ISA, isolating the irreducible primitives. In dependency order, each
step DIFFERENTIAL-TESTED against today's `chain_sip` (behaviour-identical — the whole reasoning suite +
randomized sweeps are the oracle):

- **A1 — demand body-matching via the ISA matcher.** Replace `_facts_matching`'s bespoke topology walk with
  `Machine.match` over the lowered rule body, seeding the demand's BOUND endpoints into the initial
  `State.regs` (SIP = the lowered join order, which `lower_conj` already derives from bound endpoints). This
  RETIRES the duplicate matcher and unifies forward + demand on one. Preserve the focus-scope filter by
  construction (it becomes a seed-set on the matcher). ⚠ the subtle part: `ById` free-slot binding + coref
  fan-out semantics must survive the switch.
  - **▶ FIRST INCREMENT LANDED 2026-07-14** (`docs/phase_a_demand_firmware.md`). The single-atom demand
    lookup now has a shared-ISA-matcher implementation (`chain._facts_matching_isa`: SET the bound endpoint
    → FOLLOW to the rel → predicate-key TEST → FOLLOW to the other endpoint, through the ONE `Machine.match`;
    free slots wrap `ById` natively — the register holds the node id). ADDITIVE: the bespoke walk
    (`_facts_matching_walk`) stays the reference oracle; `chain._CROSSCHECK` makes every `_facts_matching`
    call assert the two agree (order-insensitive). Proven equal across the WHOLE reasoning suite with the
    gate globally ON (391 green) + a targeted differential test (`tests/test_isa_demand_matcher_differential.py`,
    9) covering every shape (bound-subj/wildcard, bound-obj/wildcard, both-bound, whole-predicate, nested-NAF,
    coref `same_as`, SUPPOSE scope pencils, focus attention, `ById`). KEY FINDING (feeds A5): the walk
    decomposes into (a) an ISA-structural topology walk (moved to the shared matcher) + (b) THREE irreducible
    visibility filters that are runtime POLICY, not graph structure — fact-layer endpoint/rel visibility
    (skip control/inert scaffolding), SUPPOSE scope-pencil visibility, focus attention. The FORK for where
    (b) lives after the swap (a Machine `visible(nid)` predicate vs. driver post-filter) is documented as the
    user's ratified gate; this increment takes the conservative fork (b) (post-filter), which touches nothing
    in the to-be-frozen contract and is valid under either outcome. REMAINING A1: flip production to the ISA
    path + delete the walk (user gate), then A2 (the per-atom SIP join loop → whole-body `Machine.match`, the
    harder half where the interleaved magic-set raising must survive).
- **A2 — the env IS the register file.** The per-derivation Python env (`dict[str,str]`) becomes `State.regs`;
  bindings flow through the matcher's register file, not a side dict.
- **A3 — graded / value-match / coref → existing opcodes.** `GRADE` (α-cut), `VMATCH` (value-JOIN), and the
  coref `same_as` rules already exist as ISA; route the demand path through them instead of `_graded_ok`/
  `_value_matches_ok` Python.
- **A4 — the demand loop + NAC as a control-machine program.** The agenda fixpoint is a PRIM round +
  BRANCH_IF-back (like run_bank); the NAC negative subgoal is the CALL/RET already in place (brick #3),
  reading absence as an empty match.
- **A5 — isolate the irreducible PRIMITIVES.** What genuinely cannot be expressed as data-path opcodes +
  control flow (candidate: `_find_skolem_witness` structural re-finding; possibly parts of coref) becomes a
  small, NAMED set of PRIM steps. This set is the ONLY procedure-specific thing Phase B must port beyond the
  interpreter — keep it MINIMAL and documented.

**Exit gate for Phase A:** `chain_sip` is an ISA program + a documented handful of primitives; the bespoke
`_facts_matching` is gone; the whole reasoning suite is green + differential sweeps pass. The engine now has
ONE matcher and its procedures are programs.

---

## 3. Phase B — port the ISA interpreter to Rust

Now the port is bounded: implement the INTERPRETER, not the procedures.

- **B0 — scaffolding + the boundary + the differential harness.** PyO3 crate (`maturin`), `ugm._engine`
  importable, the graph LIVES in Rust (a `#[pyclass]`; Python holds a handle — NOT serialize-per-call), and a
  harness that runs the Python reference and the Rust interpreter on the SAME program, asserting identical
  output. Resolve the §4 traps here.
- **B1 — AttrGraph in Rust** (order-preserving; full public API to Python). *Gate:* build every test's graph
  both ways, compare.
- **B2 — the matcher (17 data-path opcodes)** over the Rust graph (enum + `match` dispatch, array-register
  states — the pilot's shape). *Gate:* `Machine.run` differential vs Python; MEASURE recognition speedup.
- **B3 — the control machine** (PC/BRANCH/CALL/RET/SUSPEND/PRIM + stack/registers). *Gate:*
  `test_isa_control_machine` differential.
- **B4 — the minimal PRIMITIVE set from A5** (skolem re-finding, etc.) in Rust. Small + differential-gated.
- **B5 — run the procedures (as ISA programs) on the Rust interpreter.** Because Phase A made `chain_sip`/
  `run_bank`/`dispatch` PROGRAMS, this is loading + interpreting data — NOT porting procedures. *Gate:* the
  WHOLE shipped suite through the Rust interpreter.
- **B6 — swap + two-tier.** Backend selector; whole suite through Rust; measure end-to-end. "Make it the
  DEFAULT" is a SEPARATE, later gate after full parity + real-workload battle-testing (Python reference
  retained as oracle).

---

## 4. Design traps (nail in B0)

1. **Graph lives in Rust; Python holds a handle** — not serialize-per-call. Surface = `attrgraph.py`'s public
   API. Matcher runs entirely Rust-side.
2. **Determinism / iteration order MUST match Python** (`nodes`/`succ`/`nodes_named` insertion order — the
   `[0]`-pick, provenance order, `derived_triples`, differential tests depend on it). `IndexMap`/`Vec` + id
   counter, NEVER `HashMap` in a semantic path. The #1 correctness trap.
3. **VALUED representation** — `GRADED`=f64; `VALUED`= enum of primitives + `PyObject` fallback (audit the KB).
   Comparators match `machine._cmp` EXACTLY (incl. `~=` tolerance and the `<`/`>` added for `BRANCH_IF`).
4. **PRIM boundary** — after Phase A the PRIM set is small + named (A5); port those to Rust (B4). No per-round
   Rust→Python callback once B4 lands.

---

## 5. What STAYS Python (the surface) — never ported

CNL (forms, `load_corpus`, `ask_goal`, `render`, recognition grammar), firmware (`check`/`choose`/`suppose`),
authoring (`write_rule`, `lowering` — the Rule→program COMPILER), `policy`, intake/focus/streaming. These
AUTHOR programs and CALL the interpreter; they are the surface, not the core.

---

## 6. Risks & non-goals

- **Non-goal:** reimplementing procedures in Rust (the whole point is to avoid it via Phase A).
- **Phase A risk** concentrates in A1 (switching the demand path to the ISA matcher — coref/`ById`/focus
  semantics) — gate hard, differential sweeps. This is where the intellectual care goes.
- **Phase B** is bounded by construction, but the determinism + VALUED traps (§4) are real.
- **Amdahl:** don't promise 381× end-to-end; report realized per-slice numbers. Rust = constant; focus = curve.
- **Reference:** `bench/rust_pilot/` — the measured constant + a working cargo example of the B2 representation
  (enum jump-table dispatch, `Vec` CSR, array-register states). It is a hot-loop microbenchmark, not a skeleton.

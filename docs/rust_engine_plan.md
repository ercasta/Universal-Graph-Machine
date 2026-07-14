# Rust Engine Plan — Python surface, Rust core (Phase 7b)

> **Status: PLAN (2026-07-14), NOT STARTED.** A dedicated, execution-ready build plan for porting UGM's
> HOT CORE to Rust with Python as the surface — the "cash in Rust when perf is the long-pole"
> step (`docs/graph low level machine/isa-reference.md` §"reference vs optimized"; `docs/isa_control_machine.md`
> §7). Written to be picked up COLD by a fresh session (autonomous, multi-hour capable).
>
> **Prerequisite reading (in order):** `docs/graph low level machine/isa-reference.md` (the data path +
> control path — the instruction-set CONTRACT the Rust engine must implement), `docs/isa_control_machine.md`
> §7 (the perf strategy: instruction set = contract, interpreter = swappable), `ugm/attrgraph.py` (the
> substrate to port — its PUBLIC API is the Rust surface), `ugm/machine.py` (the matcher + control machine
> to port), `docs/implementation_plan.md` §"Phase 7" (where this sits), `bench/rust_pilot/` (the measured
> pilot — the 381× evidence + a working cargo example of the target representation).
>
> **STANDING RULES (do not break):**
> - **No commits by the assistant.**
> - **Correctness before performance** — every Rust component is DIFFERENTIAL-TESTED against the Python
>   engine, which STAYS the reference oracle. Nothing Python is deleted until full parity + a swap gate.
>   NOTE: the "equivalence-with-rewriter is not a target" ratification does NOT apply here — Rust must match
>   the CURRENT Python ISA engine EXACTLY (it is the same engine, faster).
> - **Determinism is a hard requirement** — the substrate is deterministic (plain ordered containers); the
>   Rust engine must preserve iteration order everywhere a semantic depends on it (see §2).
> - **Incremental, differential-gated at every slice. No big-bang rewrite.**

---

## 0. Why — and the honest scope (read before starting)

**The measured constant.** The match inner loop is **111 ms (Python `Machine.match`) vs 0.29 ms (native
Rust) ≈ 381×** on a synthetic SEED→FOLLOW→TEST fold (30k final states); see `bench/rust_pilot/`. That is the
data-path hot loop the profile flagged as ~78% of a recognition load (opcode dispatch + `State` alloc +
stream fold).

**Amdahl bounds the whole-system win — the value is FRONT-LOADED.** Even infinite speedup on the match loop
caps *recognition* at ~4.5× (it is ~78% of that load) unless everything else ports too; *reasoning*
(`chain_sip`) has MORE Python outside the match loop (env dicts, topology walks, skolem/coref), so its
ceiling is lower. Therefore: porting the **substrate + matcher** captures most of the recognition constant
at the LOWEST risk; porting the **drivers + `chain_sip`** is diminishing returns at rising risk. **Stage the
port so the first shippable win is substrate+matcher, then STOP-AND-ASSESS before the demand solver.**

**Preconditions (do not start the port until these hold):**
1. **The instruction set is FROZEN** — the 17 data-path opcodes + the control path (PC/BRANCH/BRANCH_IF/
   CALL/RET/SUSPEND/HALT/PRIM + control stack/registers). The control path landed 2026-07-14; let it settle
   through real client (Phase 8) use first. **No ISA changes mid-port** (a moving contract means porting a
   moving target).
2. **The cheap Python rung (Phase 7a) is the lower-risk first option.** The profile's costs — `isinstance`
   (1.0 s) and dict-`bind` (0.8 s) — are attackable WITHOUT leaving Python: a method/dispatch-table instead
   of the `isinstance` chain in `_match_step`, int-interned keys + array/`__slots__` register states, CSR
   adjacency, bitset candidate sets. Likely 2–3× at near-zero risk. **Do this first if perf bites before the
   Rust investment is justified; Rust is the reserved escape hatch for when Python-side tuning is exhausted.**

**When this plan is warranted:** when a real workload AT THE TARGET SCALE (session-sized, per-utterance) is
measurably too slow AND Python-side tuning (7a) is exhausted. **Today it is NOT** — bound queries ~14 ms,
ingest ~12 ms, demos ~1 s (2026-07-14 measurements). This plan is READY for that moment; it is not a mandate
to start now.

---

## 1. Architecture — Python surface, Rust engine

```
  PYTHON SURFACE (stays)      CNL (forms · load_corpus · ask_goal · render) · firmware (check/choose/
                             suppose/mode_calls) · authoring (write_rule · lowering) · policy · intake/
                             focus/streaming
  ───────────────────────────────────────────────────────────────────────────────────────────────────
        PyO3 boundary        a thin handle: Python holds an opaque reference to the Rust engine; calls
                             cross at CLOSURE granularity (run a whole match / run_bank / chain_sip),
                             NEVER per-opcode (FFI overhead would eat the win)
  ───────────────────────────────────────────────────────────────────────────────────────────────────
  RUST ENGINE (new)          AttrGraph substrate · the matcher (17 data-path opcodes) · the control
                             machine (PC/BRANCH/CALL/RET/SUSPEND/PRIM) · [later] the drivers (run_bank,
                             chain_sip)
```

Python stays the AUTHORING + FIRMWARE surface; Rust owns the HOT CORE. The graph **lives in Rust** (§2); the
Python `AttrGraph` becomes a thin PyO3 handle whose methods delegate to Rust, so existing Python code that
pokes the graph is source-compatible.

---

## 2. Critical design decisions (nail these in Slice 0 before writing engine code)

1. **The graph LIVES in Rust; Python holds a handle.** NOT serialize-per-call (that kills the win — the
   matcher must run entirely Rust-side over the Rust graph). The Rust `AttrGraph` is a `#[pyclass]`; its
   PUBLIC surface = `ugm/attrgraph.py`'s public methods (`add_node`/`add_edge`/`set_attr`/`get_attr`/`succ`/
   `pred`/`nodes`/`nodes_named`/`has_key`/`name`/`predicate`/`get_embedding`/`registers`/`copy`/`version`/…).
   Audit `attrgraph.py` for the EXACT method set + semantics before porting.
2. **Determinism / iteration order MUST match Python EXACTLY.** `nodes()`, `succ()`, `pred()`, `nodes_named()`
   are insertion-ordered in Python, and semantics depend on it (`nodes_named(nm)[0]` write-target picks,
   provenance emission order, `derived_triples` sets, differential tests). Use `IndexMap`/`Vec` + a monotone
   id counter — **never** `HashMap` iteration in a semantic path. This is the #1 correctness trap.
3. **VALUED attribute representation.** `GRADED` = `f64`. `VALUED` is open-domain (strings/ints/floats today;
   audit the KB for what actually occurs). Store as a Rust enum of primitives (`Str`/`Int`/`Float`/`Bool`)
   plus a `PyObject` fallback if any non-primitive VALUED exists. The comparators (`=`, `<`, `>`, `<=`, `>=`,
   `~=` — note `<`/`>` were added 2026-07-14 for `BRANCH_IF`) must match `machine._cmp` semantics bit-for-bit
   (incl. the `~=` numeric tolerance / else-equality fallback).
4. **The PRIM / callback boundary (controls the staging).** The control machine's `PRIM` runs upper-level
   interpreter steps (Python callables). If the drivers move to Rust but PRIM steps stay Python, you pay a
   Rust→Python callback per round. RESOLUTION: the first target keeps the drivers (`run_bank`/`chain_sip`) in
   PYTHON, calling the Rust MATCHER at closure granularity — no per-op FFI, no per-round callback. Only Slice
   4/5 (if justified) move drivers fully into Rust so PRIM steps become Rust.
5. **Score / t-norm, skip_inert, inert flag** — the matcher carries a `score` (t-norm min/product), a
   `skip_inert` mode, and reads a per-node `inert` flag. Port these faithfully (they gate provenance-aware
   matching).
6. **Build / packaging.** `maturin` (PyO3) → a `ugm._engine` extension module; `maturin develop` for dev,
   wheels per platform for release. A backend selector in `ugm` imports the extension when chosen. Keep
   `target/` out of git (`.gitignore`).

---

## 3. The differential harness (Slice 0 — build this FIRST, it gates everything)

A harness that runs the Python reference AND the Rust engine on the SAME input and asserts IDENTICAL output:
- graph equality (nodes' attrs, edges, `derived_triples`), match-state equality (register bindings + score),
  derived-fact equality after a closure.
- Drive it from the EXISTING suites (`test_isa_machine` conformance programs, lowered rules, the reasoning
  suite) plus RANDOMIZED sweeps (the model is `test_isa_goal_semi_naive`'s >1000-goal random-program sweep).
- The Python engine is the ORACLE. A divergence is a Rust bug, always.

---

## 4. Slices (executable order; each differential-gated; STOP-AND-ASSESS before Slice 5)

- **Slice 0 — scaffolding + boundary + harness.** PyO3 crate builds, `ugm._engine` imports, an empty Rust
  `AttrGraph` handle Python can construct, and the §3 differential harness comparing a trivially-built graph
  both ways. Resolve §2.1–2.3 here (marshalling, order, VALUED). *Gate:* harness green on a hand graph.
- **Slice 1 — AttrGraph in Rust.** Full substrate: nodes/attrs (GRADED/VALUED)/directed edges, the `key→{nid}`
  index, the `nodes_named` accelerator, `registers`, `copy`, `version`, the `inert` flag — order-preserving,
  the full public API exposed to Python. *Gate:* build every test's graph both ways; compare `nodes()`/
  `edges()`/`derived_triples()`/`nodes_named` order.
- **Slice 2 — the matcher (THE hot loop, biggest win).** The 17 data-path opcodes + `Machine.match`/`apply`
  over the Rust graph (enum + `match` dispatch, array-register states — the pilot's shape). *Gate:*
  `Machine.run` differential vs Python on `test_isa_machine` + all lowered rules; MEASURE the speedup on real
  recognition (`planning.cnl`) and confirm the Amdahl-bounded end-to-end number. **This is the primary
  shippable win — a Rust matcher behind the Python drivers.**
- **Slice 3 — the control machine.** PC/BRANCH/BRANCH_IF/CALL/RET/SUSPEND/HALT/PRIM + control stack/registers
  in Rust; PRIM calls back into Python (acceptable here). *Gate:* `test_isa_control_machine` differential.
- **Slice 4 — the forward drivers.** `run_bank`/`run_to_fixpoint` as Rust control-machine programs (most of
  it falls out of Slice 3). *Gate:* recognition + planning suites; re-measure recognition end-to-end.
- **⏸ STOP-AND-ASSESS.** Recompute the realized end-to-end speedup vs the effort remaining. Slice 5 is where
  correctness risk concentrates; only proceed if the reasoning-path win justifies it.
- **Slice 5 — `chain_sip` (the demand solver).** env/SIP/skolem/NAC-as-control-stack/coref/graded/value-match
  — the hardest, most subtle port (NAF stratification, `_find_skolem_witness`, coref fan-out). *Gate:* the
  WHOLE reasoning suite + randomized differential sweeps + the demand-driven-NAF differential.
- **Slice 6 — swap + two-tier.** A backend selector routes the Python firmware through the Rust engine; run
  the ENTIRE shipped suite through Rust; measure end-to-end at session scale. **"Make it the default" is a
  SEPARATE, LATER gate** — only after full parity across the suite AND real-workload battle-testing, with the
  Python reference retained as the oracle.

---

## 5. What STAYS Python (the surface — do NOT port)

CNL (forms, `load_corpus`, `ask_goal`, `render`, recognition grammar), firmware (`check`/`choose`/`suppose`/
`mode_calls`), authoring (`write_rule`, `lowering` — the Rule→program compiler), `policy`, intake/focus/
streaming (`intake.py`/`focus.py`/`rule_control.py`). These CALL INTO the Rust engine; they are the surface,
not the core.

---

## 6. Risks, traps, non-goals

- **Non-goal: a big-bang rewrite.** Incremental, differential-gated, Python-reference-preserved, stop-and-
  assess before the demand solver.
- **Trap: determinism/order** (§2.2) — a `HashMap` in a semantic path silently breaks `[0]`-picks + provenance
  order + differential tests. Ordered structures only.
- **Trap: VALUED/PyObject marshalling** (§2.3) — comparator + tolerance semantics must match `_cmp` exactly.
- **Risk concentrates in Slice 5** (`chain_sip`): NAF stratification soundness, skolem structural re-finding,
  coref `same_as` fan-out. Gate hard, or stop at Slice 4 if the recognition win suffices.
- **Amdahl** (§0) — do not promise 381× end-to-end; it is the hot-loop constant. Report realized end-to-end
  numbers per slice.
- **Seed-from-focus is the CURVE, orthogonal** — Rust does not replace it; the accretion fix stays focus.

---

## 7. Reference — the pilot (`bench/rust_pilot/`)

The measured evidence + a working cargo example of the target representation: an opcode `enum` with `match`
(jump-table) dispatch, `Vec<Vec<u32>>` CSR-lite adjacency, `[u32; NREG]` array-register states (no dict, no
`isinstance`). `py_bench.py` is the identical-workload Python baseline (real `Machine.match`). Reproduce:
`cargo run --release -- 3000 10 60` vs `python py_bench.py 3000 10 60` → ~0.29 ms vs ~111 ms/run, identical
30k final states. It is a hot-loop MICROBENCHMARK, not an engine skeleton — Slice 2 is the real matcher.

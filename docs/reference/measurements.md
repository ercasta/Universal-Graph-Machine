# Measurements — the load-bearing numbers, in one place

> **Status: LEDGER (started 2026-07-14 at the docs reorganization).** Every performance claim the
> project leans on, with its date, the bench/test that produced it, and what it licenses. Numbers
> go stale as the code moves — **when you re-run a bench, update the row and keep the old value in
> the history column**. A number without a runnable source doesn't belong here. Scale reminder:
> UGM is judged at SESSION scale (per-utterance, 2–3 banks), not data scale
> (memory `ugm-scope-session-sized`).

## 1. The two axes (the frame for every number below)

- **The CONSTANT** — per-instruction interpreter overhead. Attacked by Phase 7 (pure-Python
  tightening, then the Rust interpreter port). Rust buys the constant.
- **The CURVE** — how per-utterance cost grows with session/KB size. Attacked by seed-from-focus
  (bounded attention). Focus holds the curve.

They are orthogonal; conflating them was explicitly rejected in the Rust plan
(`../design/rust_engine_plan.md`).

## 2. Current steady-state (2026-07-14)

| Quantity | Value | Source |
|---|---|---|
| Test suite | 442 passed, ~14 s | `.venv/Scripts/python.exe -m pytest -q` |
| Per-utterance `ingest` | median ~12 ms (8–16 ms) | Axis B timing pass (CHANGELOG 2026-07-14) |
| Corpus load | 2–49 ms/line (`planning.cnl` the ~49 ms outlier) | same |
| Bound query, 12 accreted cases | ~29 ms global / ~14 ms focus | `bench/session_accretion.py` `suspend_resume_probe` |
| `ITERATE` | ~13–17 µs/iter, linear | `tests/test_isa_iterate.py` timing pass |
| `load_machine_rules` re-load (memoized) | ~19 ms → ~6 µs | feedback #9 (CHANGELOG 2026-07-14) |

## 3. The constant

| Finding | Value | Date | Source |
|---|---|---|---|
| Match inner loop, Python vs native Rust (SEED→FOLLOW→TEST fold, 30k final states) | 111 ms vs 0.29 ms ≈ **381×** | 2026-07-14 | `bench/rust_pilot/` (enum jump-table dispatch, `Vec` CSR, array-register states; also captures the dict→array state win) |

Licenses: Phase 7b is real and large — but start only when a real workload is too slow AND the
pure-Python rung (7a) is exhausted.

## 4. The curve (focus / session accretion)

| Finding | Value | Date | Source |
|---|---|---|---|
| Focus flattens accretion (original probe) | global 0.5 s → 5.5 s → 31 s → 112 s (super-linear cliff) vs focus 23 → 29 → 65 → 83 ms (**flat**); ratio → 1361× | 2026-07-12 | `bench/session_accretion.py` `focus_probe` (bound `is s<k>_0 thief` as cases accrete) |
| Re-run post control-machine port | global ~48 → 168 ms over 8 cases (~3.5×, tracks KB size) vs focus flat ~40–55 ms; ratio 1.1 → 3.9× | 2026-07-14 | same probe — the engine got much faster in between (NAF fix), the SHAPE holds |
| Warm re-entry (wildcard goals) | warm ≈ cold (1.01×) — `chain_sip` re-entry redoes the closure; bites ONLY for wildcard/whole-session goals (bound queries cheap, see §2) | 2026-07-14 | `suspend_resume_probe` |

Licenses: seed-from-focus is the accretion answer for the interactive client; the wildcard-redo
fix (persistent tabled frontier across calls) is deferred until wildcard-streaming latency
matters (plan, Phase 8 tail).

## 5. Landed speedups (history — what got us here)

| Fix | Before → after | Date |
|---|---|---|
| NAC existence check endpoint-driven (NAF hot path) | bound query m=6: 13.8 s → 0.34 s (**40×**); suite 54 s → 35 s | 2026-07-12 |
| Demand-negation lever (a): endpoint-driven `_facts_matching` | cProfile 12 suspects/6 aliases: 6.18 s → 0.565 s (calls 9.9 M → 0.98 M); suite ~90 s → ~54 s | 2026-07-12 |
| Firmware v3 (demand-driven NAF + closure memo + local agenda) | wildcard query 129 s → 7.5 s; suite 26 min → 90 s | 2026-07-11 |
| `run_bank` df-seeding + bound-endpoint join driving (Phase 0.1) | 34× on recognition; `planning.cnl` 89× → 2.6× vs the old rewriter | 2026-07-07 |

## 6. Negative results (measured, and that's why they were rejected)

| Attempt | Result | Date | Record |
|---|---|---|---|
| Fully demand-driven coreference | correct but **3–6× slower** (~897 K EMITs/query — rules-based propagation over the dense `same_as` clique is super-linear) | 2026-07-13 | `../attic/demand_driven_coref_plan.md` (branch `demand-driven-coref-wip`); superseded by reader interning |

## 7. Open perf items (tracked in the plan)

Phase 7a pure-Python rung (dispatch table, int-interned keys, `__slots__` states — est. 2–3×);
perf levers (b) semi-naive demand re-servicing and (c) coref demand fan-out (bounded by focus in
practice); 8.6 incremental head-index extend; the wildcard tabled frontier (§4).

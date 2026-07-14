# Rust pilot — the match inner-loop constant-factor (Phase 7b evidence)

A throwaway microbenchmark measuring the CONSTANT a native (Rust) implementation buys on the ISA's data-path
hot loop — the profile's ~78%-of-recognition inner loop (opcode dispatch + `State` alloc + state-stream fold).
It is NOT an engine skeleton; the real matcher port is Slice 2 of `docs/rust_engine_plan.md`.

Both sides do IDENTICAL logical work (same graph, same `SEED → FOLLOW → TEST` program, same 30k final-state
count), so the wall-clock ratio is honest.

```
# Python baseline — the REAL engine inner loop (ugm.machine.Machine.match)
python bench/rust_pilot/py_bench.py 3000 10 60

# Rust — enum + match jump-table dispatch, Vec<Vec<u32>> CSR-lite adjacency, [u32; N] array-register states
cd bench/rust_pilot && cargo run --release -- 3000 10 60
```

**Measured (2026-07-14):** Python **111 ms/run** vs Rust **0.29 ms/run** ≈ **381×** (both 30 000 final states).
Above the doc's 1–2 orders estimate because it also captures the dict→array state-representation win. Remember
Amdahl: this is the hot-loop constant, not the end-to-end system speedup — see `docs/rust_engine_plan.md` §0.

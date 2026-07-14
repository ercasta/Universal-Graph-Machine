"""
Rust-vs-Python pilot — Python baseline, using the REAL engine inner loop (`Machine.match`).

Workload = the recognition hot pattern the profile flagged (SEED -> FOLLOW-expand -> TEST over a
fanned-out graph): M hub nodes carrying key 'k', each with `b` leaf out-neighbours carrying key
'leaf'. The match program SEEDs the hubs, FOLLOWs to leaves (the state-stream fan-out — the
expensive `_match_step`/`bind`/`extend` the profile is dominated by), and TESTs the leaf key.
Final state count = M*b. Timed over R repetitions, graph build excluded. The Rust pilot does the
identical logical work (same final count) so the ratio is an honest hot-loop constant-factor.
"""
import sys, time, json
sys.path.insert(0, ".")
from ugm.attrgraph import AttrGraph, graded
from ugm.machine import Machine, SEED, FOLLOW, TEST

M = int(sys.argv[1]) if len(sys.argv) > 1 else 3000     # hubs
B = int(sys.argv[2]) if len(sys.argv) > 2 else 10       # leaves per hub
R = int(sys.argv[3]) if len(sys.argv) > 3 else 60       # repetitions


def build():
    g = AttrGraph()
    hubs = [g.add_node({"k": graded(1.0)}) for _ in range(M)]
    for h in hubs:
        for _ in range(B):
            leaf = g.add_node({"leaf": graded(1.0)})
            g.add_edge(h, leaf)
    return g


def main():
    g = build()
    prog = [SEED("r", "k"), FOLLOW("o", "r", "out"), TEST("o", "leaf")]
    m = Machine()
    # warmup + correctness
    n = len(m.match(g, prog))
    assert n == M * B, (n, M * B)
    t0 = time.perf_counter()
    for _ in range(R):
        states = m.match(g, prog)
    dt = time.perf_counter() - t0
    out = {"lang": "python", "M": M, "B": B, "R": R, "final_states": len(states),
           "total_s": dt, "per_run_ms": dt / R * 1000,
           "per_run_states": M * B, "runs_per_s": R / dt}
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

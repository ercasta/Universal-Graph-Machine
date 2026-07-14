// Rust-vs-Python pilot — native reimplementation of the match INNER LOOP the profile flagged as
// ~90% of a recognition load (opcode dispatch + state-stream fold). Identical LOGICAL work to
// py_bench.py (same graph, same SEED->FOLLOW->TEST program, same final state count = M*B), so the
// wall-clock ratio is an honest hot-loop constant-factor. This is the doc's "enum + match jump-table,
// CSR/struct states" representation — NOT a full PyO3 port, just the constant-factor measurement.

use std::env;
use std::time::Instant;

#[derive(Clone, Copy)]
enum Op {
    Seed { reg: usize, key: u8 },     // key: 0='k', 1='leaf'
    Follow { dst: usize, src: usize },
    Test { reg: usize, key: u8 },
}

const NREG: usize = 2;
type State = [u32; NREG];

struct Graph {
    adj: Vec<Vec<u32>>,   // out-neighbours (CSR-lite)
    has_k: Vec<bool>,
    has_leaf: Vec<bool>,
    seed_k: Vec<u32>,     // precomputed nodes-with-key 'k' (the SEED candidate list)
}

fn run(g: &Graph, prog: &[Op]) -> usize {
    let mut states: Vec<State> = vec![[0u32; NREG]];      // one empty state, like Machine.match
    for op in prog {
        match *op {
            Op::Seed { reg, .. } => {                     // only 'k' is seeded in this workload
                let mut next: Vec<State> = Vec::with_capacity(states.len() * g.seed_k.len());
                for st in &states {
                    for &n in &g.seed_k {
                        let mut s = *st;
                        s[reg] = n;
                        next.push(s);
                    }
                }
                states = next;
            }
            Op::Follow { dst, src } => {
                let mut next: Vec<State> = Vec::with_capacity(states.len());
                for st in &states {
                    for &nb in &g.adj[st[src] as usize] {
                        let mut s = *st;
                        s[dst] = nb;
                        next.push(s);
                    }
                }
                states = next;
            }
            Op::Test { reg, key } => {
                let flags = if key == 0 { &g.has_k } else { &g.has_leaf };
                states.retain(|st| flags[st[reg] as usize]);
            }
        }
    }
    states.len()
}

fn main() {
    let a: Vec<String> = env::args().collect();
    let m: u32 = a.get(1).and_then(|s| s.parse().ok()).unwrap_or(3000);
    let b: u32 = a.get(2).and_then(|s| s.parse().ok()).unwrap_or(10);
    let r: u32 = a.get(3).and_then(|s| s.parse().ok()).unwrap_or(60);

    let n = (m + m * b) as usize;
    let mut g = Graph { adj: vec![Vec::new(); n], has_k: vec![false; n], has_leaf: vec![false; n], seed_k: Vec::with_capacity(m as usize) };
    for h in 0..m {
        g.has_k[h as usize] = true;
        g.seed_k.push(h);
        let base = m + h * b;
        for j in 0..b {
            let leaf = base + j;
            g.adj[h as usize].push(leaf);
            g.has_leaf[leaf as usize] = true;
        }
    }

    let prog = [
        Op::Seed { reg: 0, key: 0 },      // SEED r key='k'
        Op::Follow { dst: 1, src: 0 },    // FOLLOW o <- r (out)
        Op::Test { reg: 1, key: 1 },      // TEST o key='leaf'
    ];

    let check = run(&g, &prog);
    assert_eq!(check, (m * b) as usize, "final state count mismatch");

    let t0 = Instant::now();
    let mut last = 0usize;
    for _ in 0..r {
        last = run(&g, &prog);
    }
    let dt = t0.elapsed().as_secs_f64();
    println!(
        "{{\"lang\":\"rust\",\"M\":{},\"B\":{},\"R\":{},\"final_states\":{},\"total_s\":{:.6},\"per_run_ms\":{:.6},\"per_run_states\":{},\"runs_per_s\":{:.3}}}",
        m, b, r, last, dt, dt / (r as f64) * 1000.0, m * b, (r as f64) / dt
    );
}

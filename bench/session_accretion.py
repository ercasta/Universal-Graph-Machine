"""
Phase 8.0 probe — session accretion + suspend/resume (docs/design/cnl_intake_design.md §7).

The first UGM client is an agent loop with a TUI: a LONG, topical CNL session where facts (and rules)
accrete monotonically with the transcript. The critique's real perf risk for this client is NOT total-KB
size (Phase 7a interning) but SESSION ACCRETION (docs/critique.md §4.1a): the graph grows with the
transcript even when each domain is tiny, so per-utterance latency can creep with the SESSION rather
than with the utterance's own consequences.

The design's answer is SEED-FROM-FOCUS (§3): a demand seeds from the current focus centers, so
per-utterance cost tracks the closure from those centers, not the accumulated session. Seed-from-focus is
not built yet (Phase 8.3) — so this probe does two honest things BEFORE we build on the premise:

  (1) MEASURE THE BASELINE — does whole-graph per-utterance latency grow as the transcript accretes?
      (`whole_graph_ms`, answering over the entire accreted KB, today's behaviour.)
  (2) QUANTIFY THE HEADROOM — how flat would an ideal focus scope be? (`focus_ideal_ms`, answering the
      same question against a FRESH graph holding only the current turn's own facts — the lower-bound a
      perfect seed-from-focus would approach.)

If whole_graph grows ~linearly while focus_ideal stays ~flat, the accretion problem is real and
seed-from-focus is worth building, and the ratio is the win it should recover.

Plus a SUSPEND/RESUME micro-probe: the streaming design (§5) suspends the loop at an `ask_user`
wait-point and RESUMES by re-entering the demand-driven chain on the same graph. The open question is
whether re-entry PRESERVES the demand frontier (cheap continuation) or REDOES the closure. We measure a
cold run vs. a warm re-entry vs. an incremental re-entry after one new fact.

Run:  python bench/session_accretion.py
"""
from __future__ import annotations

import time

import ugm as h


# The reasoning is shared (global rules); each "case" is an INDEPENDENT batch of suspects, so a
# question about case k has a bounded relevant closure (case k's facts) while the whole-graph reasoner
# scans every accreted case — exactly the accretion-vs-focus contrast.
RULES_TEXT = """
?x is innocent when ?x in library
?x is cleared when ?x is innocent
?x is cleared when ?x is alibied
?x is thief when ?x is a suspect and ?x is not cleared
"""


def case_facts(k: int, m: int = 6) -> str:
    """One case = m suspects; suspect 0 is the thief (uncleared), the rest are cleared
    (alibied or in library). Names are case-tagged so cases never interact."""
    lines = []
    for i in range(m):
        s = f"s{k}_{i}"
        lines.append(f"{s} is a suspect")
        if i == 0:
            continue                       # the thief: neither alibied nor in library
        if i % 2 == 0:
            lines.append(f"{s} is alibied")
        else:
            lines.append(f"{s} in library")
    return "\n".join(lines)


def _time(fn) -> float:
    t0 = time.perf_counter()
    fn()
    return (time.perf_counter() - t0) * 1000.0


def accretion_probe(turns: int = 40, m: int = 6, sample_every: int = 5) -> None:
    """Grow a session `turns` cases deep, timing each turn's question two ways."""
    kb, rules = h.load_corpus(RULES_TEXT)          # whole-graph KB: accretes across turns
    print(f"\n=== accretion probe: {turns} turns, {m} suspects/case ===")
    print(f"{'turn':>5} {'kb_nodes':>9} {'whole_ms':>10} {'focus_ms':>10} {'ratio':>7}")
    for k in range(turns):
        facts = case_facts(k, m)
        h.load_facts(kb, facts)                    # the transcript grows (monotone)

        # (1) whole-graph: answer over the ENTIRE accreted KB (today's behaviour).
        whole_ms = _time(lambda: h.ask_goal(kb, "who is thief", rules))

        # (2) focus-ideal: the same question against ONLY this turn's own facts (the lower bound a
        # perfect seed-from-focus would approach — no cross-turn scan).
        fresh, fresh_rules = h.load_corpus(RULES_TEXT)
        h.load_facts(fresh, facts)
        focus_ms = _time(lambda: h.ask_goal(fresh, "who is thief", fresh_rules))

        if k % sample_every == 0 or k == turns - 1:
            ratio = whole_ms / focus_ms if focus_ms else float("nan")
            print(f"{k:>5} {len(kb.nodes()):>9} {whole_ms:>10.2f} {focus_ms:>10.2f} {ratio:>7.1f}",
                  flush=True)

    print("\nReading: if whole_ms climbs while focus_ms stays flat, accretion is real and seed-from-focus"
          "\n(Phase 8.3) should recover ~the ratio. If whole_ms is already flat, the premise is softer than"
          "\nthe critique feared and 8.3 can be lighter.")


def suspend_resume_probe(cases: int = 30, m: int = 6) -> None:
    """Cold closure vs. warm re-entry vs. incremental re-entry on the SAME graph — the streaming
    resume question (does re-entry preserve the frontier or redo the closure?)."""
    from ugm.chain import chain_sip
    from ugm.cnl.rule_graph import write_rule
    from ugm.world_model import Graph

    kb, rules = h.load_corpus(RULES_TEXT)
    for k in range(cases):
        h.load_facts(kb, case_facts(k, m))
    rule_g = Graph()
    for r in rules:
        write_rule(rule_g, r)

    goal = ("is", None, "thief")                   # wildcard-subject thief goal
    cold = _time(lambda: chain_sip(kb, rule_g, goal))          # first closure (facts get derived)
    warm = _time(lambda: chain_sip(kb, rule_g, goal))          # re-enter: everything already derived
    h.load_facts(kb, case_facts(cases, m))                     # one NEW case appears
    incr = _time(lambda: chain_sip(kb, rule_g, goal))          # re-enter after a relevant fact

    print(f"\n=== suspend/resume micro-probe: {cases} cases warmed ===")
    print(f"cold closure      : {cold:8.2f} ms")
    print(f"warm re-entry     : {warm:8.2f} ms   ({warm / cold:.2f}x cold)")
    print(f"incremental (+1)  : {incr:8.2f} ms   ({incr / cold:.2f}x cold)")
    print("Reading: warm≈cold means re-entry REDOES the closure (the documented per-run `fired`/local-"
          "\nagenda caveat) — resume needs an explicit persisted frontier before streaming (§5 caveat)."
          "\nwarm≪cold means the graph-resident derivations already make resume cheap.")


def focus_probe(cases: int = 25, m: int = 6, sample_every: int = 5) -> None:
    """Phase 8.3b validation: does BOUNDED ATTENTION (focus_scope) keep a bound question's cost flat as
    independent cases accrete, where whole-graph reasoning grows (the coref fan-out over the whole KB)?"""
    kb, rules = h.load_corpus(RULES_TEXT)
    print(f"\n=== focus probe: bound 'is s<k>_0 thief', global vs focus, {cases} cases ===")
    print(f"{'case':>5} {'kb_nodes':>9} {'global_ms':>10} {'focus_ms':>10} {'ratio':>7}")
    for k in range(cases):
        h.load_facts(kb, case_facts(k, m))
        subj = f"s{k}_0"
        glob = _time(lambda: h.ask_goal(kb, f"is {subj} thief", rules))
        foc = _time(lambda: h.ask_goal(kb, f"is {subj} thief", rules, focus_scope=frozenset({subj})))
        if k % sample_every == 0 or k == cases - 1:
            ratio = glob / foc if foc else float("nan")
            print(f"{k:>5} {len(kb.nodes()):>9} {glob:>10.2f} {foc:>10.2f} {ratio:>7.1f}", flush=True)
    print("\nReading: if global_ms climbs with accreted cases while focus_ms stays flat, bounded attention"
          "\n(Phase 8.3b) makes per-utterance cost track the focus, not the session — the accretion fix.")


if __name__ == "__main__":
    import sys
    which = sys.argv[1] if len(sys.argv) > 1 else "focus"
    if which == "accretion":
        accretion_probe(turns=12, sample_every=1)
        suspend_resume_probe(cases=12)
    else:
        focus_probe()

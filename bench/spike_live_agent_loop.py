"""LIVE-AGENT-LOOP PROBE — the reflexive stack (flare -> governor -> authoritativeness -> recovery) meeting
a REAL reasoning session with a REAL <call>/ask_user boundary (docs/implementation_plan.md ▶ CURRENT ARC).

Everything below the reactive core was proven with HAND-DRIVEN `fire()` in tests. The plan's open unknowns
were about the LIVE loop: does the stack light up when the flare comes from the REAL ask path? does the
governor escalate ACROSS TURNS? and — the crux — when a recovery is chosen, does it actually ACT?

FINDINGS THIS PROBE SURFACED (why probe-first mattered):
  1. The stack DOES fire through the real committed-ask gate: repeated fuel exhaustion -> flares accumulate,
     the governor escalates a severity ladder and abandons at the declared rung, and the recovery bank picks
     `escalate` BY AUTHORITY (the higher-authority advisor).
  2. A pathology only a live budget exposes: if the object goal's `max_rounds` is SO small the GOVERNANCE
     derivation itself can't finish, the recovery reasoning starves and flares on ITSELF. At an adequate
     governance budget (>= a few rounds) it is clean. (A robustness note; the ladder is a few hops.)
  3. THE GAP (now CLOSED by this arc): `recovery escalate` was an inert FACT. This probe drives the
     side-effect reaction — `recovery is actionable` -> the chosen action becomes a `<call>` the driver
     services as an `Event("call")` — so the recovery ACTS: it escalates to a (simulated) human.

The scenario: an agent repeatedly asked a question whose derivation never settles within the round budget
(a 20-hop cascade under a tight budget). Driven through the REAL non-blocking `converse` loop, turn by turn,
answering the async recovery tool's suspension. We show (a) the answer is honest UNKNOWN, (b) the governor
abandons and recovery=escalate materializes by authority, (c) a real `escalate` <call> SUSPENDS to the host
and is serviced — the recovery acted — and (d) flipping the ONE authority fact makes `giveup` act instead,
with no code change: the composability principle, live.
"""
from __future__ import annotations

import warnings
from pathlib import Path

from ugm import AttrGraph, AsyncTool
from ugm.dispatch import call_arg
from ugm.intake import converse, ingest, load_kb
from ugm.cnl.machine_rules import load_machine_rules
from ugm.chain import _facts_matching

warnings.simplefilter("ignore")

CORPUS = Path(__file__).resolve().parent.parent / "corpus"
NHOPS, BUDGET, TURNS = 20, 6, 6                            # 20-hop chain, starved at budget 6; governance fits


def _recovery_tools(log):
    """Async recovery tools — the WORLD side of the boundary. Each SUSPENDs (a real human/service round-trip)
    and, on the host's answer, records that the recovery acted. Named after the recovery ACTIONS, so the
    `<call> tool escalate` the bridge emits routes to `escalate` here — no dispatch table, just the name."""
    def mk(label):
        return AsyncTool(request=lambda g, c: (label, g.name(call_arg(g, c, "arg"))),
                         fold=lambda g, c, resp: (log.append((label, resp)) or set()))
    return {"escalate": mk("escalate"), "giveup": mk("giveup")}


def build(authority: str):
    """A KB whose object goal never settles in budget, plus the governor + recovery banks and ONE authority
    datum (`authority`, e.g. 'ops more_important_than policy') that decides which recovery wins."""
    preds = [chr(ord("a") + i) for i in range(NHOPS)]
    kb, rules = AttrGraph(), []
    kb.add_relation(kb.add_node("x"), "a", kb.add_node("y"))          # the base fact the cascade starts from
    for lo, hi in zip(preds, preds[1:]):
        rules += load_machine_rules(f"?x {hi} ?y when ?x {lo} ?y")
    load_kb(kb, rules, (CORPUS / "governor.cnl").read_text())
    load_kb(kb, rules, (CORPUS / "recovery.cnl").read_text())
    ingest(kb, rules, authority)                                      # the AUTHORITY order (session-supplied)
    return kb, rules, preds[-1]


def run(authority: str, human_answer: str = "acknowledged"):
    """Drive TURNS asks of the never-settling question through the REAL non-blocking `converse` loop,
    answering any recovery `<call>` with `human_answer`. Returns (per-turn trace, the recovery-action log)."""
    kb, rules, last = build(authority)
    tools = _recovery_tools(log := [])
    trace = []
    for turn in range(1, TURNS + 1):
        gen, send = converse(kb, rules, f"does x {last} y", async_tools=tools, max_rounds=BUDGET), None
        answer, calls = None, []
        try:
            while True:
                ev = gen.send(send); send = None
                if ev.kind == "answer":
                    answer = ev.data["answer"]
                elif ev.kind == "call":                              # the recovery SUSPENDED to the world
                    calls.append(ev.data["tool"])
                    send = human_answer                             # the human/service answers -> resume
        except StopIteration:
            pass
        recovery = sorted(str(kb.name(o.node_id) if hasattr(o, "node_id") else o)
                          for _s, o in _facts_matching(kb, "recovery", None, None))
        trace.append((turn, answer, recovery, calls))
    return trace, log


def main():
    print(f"  scenario: repeatedly ask 'does x <last> y' — a {NHOPS}-hop cascade, budget={BUDGET} "
          f"(never settles) — over {TURNS} turns, driven through the REAL `converse` loop\n")

    for authority, expect in [("ops more_important_than policy", "escalate"),
                              ("policy more_important_than ops", "giveup")]:
        print(f"  AUTHORITY = '{authority}'  (expect the recovery to be '{expect}')")
        trace, log = run(authority)
        for turn, answer, recovery, calls in trace:
            acted = f"  ACTED-> <call>{calls}" if calls else ""
            print(f"    turn {turn}: answer={answer!s:<14} recovery={recovery}{acted}")
        print(f"    recovery-tool log (world side): {log}")
        ok = any(c == expect for _t, _a, _r, cs in trace for c in cs) and log and log[0][0] == expect
        print(f"    -> {'GO' if ok else 'GAP'}: the chosen recovery '{expect}' ACTED "
              f"through a real <call>/ask_user suspension\n")

    print("=" * 92)
    print("  RESULT: the reflexive stack meets a live session — a governed failure ESCALATES for real, and")
    print("  the SAME banks pick a different action from ONE flipped authority fact (composability, live).")


if __name__ == "__main__":
    main()

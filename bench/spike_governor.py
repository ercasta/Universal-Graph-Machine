"""REFLEXIVE GOVERNOR PROBE — flare + accumulator + threshold + recovery = heuristic termination.

We cannot decide halting, so we do not try (agent-not-theorem-prover). Instead the reactive core WATCHES its
own resource consumption and RECOVERS heuristically:

  exhaustion  --raises-->  FLARE (reactable fact)                       [validated: probe_help_flare]
  flare       --increments--> ACCUMULATOR (a register counter per goal) [stepping state, Axis B]
  accumulator --crosses--> THRESHOLD (a declared bound)  --materializes--> a recovery-trigger fact
  trigger     --fires-->  RECOVERY RULE (a reactive rule: abandon / escalate / raise budget)

Headline claim: a goal that would otherwise be RE-ATTEMPTED FOREVER is bounded by the accumulator+threshold
and RECOVERED (abandoned, honestly) — a real non-termination turned into a bounded give-up. The probe shows
the CONTRAST: ungoverned retry runs the full act budget; governed retry stops at the threshold.
"""
from __future__ import annotations

import warnings

from ugm import AttrGraph
from ugm.attrgraph import valued
from ugm.machine import Machine, MINT, State
from ugm.cnl.machine_rules import load_machine_rules
from ugm.cnl.query import _reify_rules
from ugm.reconsider import mark_dirty
from ugm.chain import chain_sip, _facts_matching, _Exhaustion

warnings.simplefilter("ignore")

FLARE_PRED, ABANDONED, YES = "unresolved", "abandoned", "yes"
ACCUM_REG = "flare_counts"        # kb.registers: dict[goal_key -> int]  (an ACCUMULATOR — stepping state)


# --- flare (from the prior probe) -------------------------------------------------------------------
def _goal_node(kb, goal):
    p, s, o = (x if x is not None else "*" for x in goal)
    nm = f"goal:{p}:{s}:{o}"
    for n in kb.nodes_named(nm):
        return n
    return Machine().apply(kb, [MINT("_g", attrs={"name": valued(nm)})], State({})).regs["_g"]


def _has_fact(kb, node, pred):
    return any(kb.predicate(r) == pred for r in kb.out(node))


def raise_flare(kb, goal):
    g = _goal_node(kb, goal)
    yes = (kb.nodes_named(YES) or [None])[0] or kb.add_node(YES)
    if not _has_fact(kb, g, FLARE_PRED):
        kb.add_relation(g, FLARE_PRED, yes); mark_dirty(kb, [(FLARE_PRED, YES)])
    return g


# --- accumulator + threshold gate (the NEW governor) ------------------------------------------------
def bump_accumulator(kb, goal_key):
    acc = kb.registers.setdefault(ACCUM_REG, {})
    acc[goal_key] = acc.get(goal_key, 0) + 1
    return acc[goal_key]


def govern(kb, goal, *, threshold):
    """The THRESHOLD GATE: if a goal's accumulator has crossed the declared bound and it is not already
    abandoned, materialize the recovery-trigger fact `<goal> abandoned yes` (the heuristic give-up) and mark
    its grain — a recovery rule then reacts. Monotone (abandon stays), so it fires at most once per goal."""
    g = _goal_node(kb, goal)
    key = kb.name(g)
    if kb.registers.get(ACCUM_REG, {}).get(key, 0) >= threshold and not _has_fact(kb, g, ABANDONED):
        yes = (kb.nodes_named(YES) or [None])[0] or kb.add_node(YES)
        kb.add_relation(g, ABANDONED, yes); mark_dirty(kb, [(ABANDONED, YES)])
        return True
    return False


def is_abandoned(kb, goal):
    return _has_fact(kb, _goal_node(kb, goal), ABANDONED)


# --- one act: attempt the goal unless recovery has abandoned it --------------------------------------
def act(kb, goal, rules, *, budget, threshold, governed):
    """Returns 'attempted' | 'skipped(abandoned)'. RECOVERY guard: a governed agent does not re-attempt an
    abandoned goal (the recovery rule's NAF `not abandoned`)."""
    if governed and is_abandoned(kb, goal):
        return "skipped(abandoned)"                        # recovery fired -> the retry loop terminates
    fuel = _Exhaustion()
    chain_sip(kb, goal, rules=rules, max_rounds=2, _fuel=fuel)   # a hard goal: always exhausts
    if fuel.exhausted:
        raise_flare(kb, goal)
        bump_accumulator(kb, kb.name(_goal_node(kb, goal)))
        if governed:
            govern(kb, goal, threshold=threshold)
    return "attempted"


def _hard_kb_and_rules():
    kb = AttrGraph()
    x, y = kb.add_node("x"), kb.add_node("y")
    kb.add_relation(x, "a", y)
    preds = ["a", "b", "c", "d", "e", "f", "g", "h"]           # an 8-hop cascade starved at max_rounds=2
    rules = _reify_rules([r for lo, hi in zip(preds, preds[1:])
                          for r in load_machine_rules(f"?x {hi} ?y when ?x {lo} ?y")])
    return kb, rules, ("h", "x", "y")


def run(governed, *, acts, threshold):
    kb, rules, goal = _hard_kb_and_rules()
    outcomes = [act(kb, goal, rules, budget=2, threshold=threshold, governed=governed) for _ in range(acts)]
    attempts = sum(o == "attempted" for o in outcomes)
    return attempts, is_abandoned(kb, goal), kb.registers.get(ACCUM_REG, {}).get("goal:h:x:y", 0)


def main():
    ACTS, THRESH = 10, 3
    un_attempts, un_aband, un_count = run(governed=False, acts=ACTS, threshold=THRESH)
    gv_attempts, gv_aband, gv_count = run(governed=True, acts=ACTS, threshold=THRESH)

    print(f"  UNGOVERNED: {un_attempts} attempts over {ACTS} acts, abandoned={un_aband} (retries forever)")
    print(f"  GOVERNED  : {gv_attempts} attempts over {ACTS} acts, abandoned={gv_aband}, "
          f"accumulator peaked at {gv_count}")
    print("=" * 66)
    ok = (un_attempts == ACTS and not un_aband           # ungoverned: burns every act, never recovers
          and gv_attempts == THRESH and gv_aband)        # governed: bounded at the threshold, recovered
    print(f"GOVERNOR: {'GO — heuristic bound turns endless retry into a bounded, honest give-up' if ok else 'GAP'}"
          + f"  (governed stopped at {gv_attempts}, ungoverned ran {un_attempts})")


if __name__ == "__main__":
    main()

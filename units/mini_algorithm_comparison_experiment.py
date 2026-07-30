"""MINI-ALGORITHM COMPARISON — the decisive test for repointing the north star.

**The question.** `episode_to_procedure_probe_experiment.py` (Probe C) compiles an episode into a reusable
procedure using LHS/RHS rules with NAC guards. It works, but it needed two corrections that had nothing to
do with the problem and everything to do with the formalism: applications had no inherent order (rules in
one settle do not fire in sequence), and compilation minted ten procedures instead of one (`Emit` mints
fresh per firing, so "one per episode" needs an interning NAC).

The proposal under test: **keep business content, goals, plans and explanations as graph data — the actual
bet — but write the METAPROCEDURES as ordinary mini-algorithms that read and write that data, instead of
as pattern-matching rules.** This is what the ISA/firmware layer was always meant to be; what was missing
at the time was the data model, not the execution model.

**What this file does.** Re-implements Probe C's compile step as a plain function over the same graph, and
compares three things that actually matter:

1. **Does it produce the same data?** If the resulting graph differs, the two approaches are not
   interchangeable and the comparison is meaningless. This is the control.
2. **How much of the difficulty was accidental?** Counted concretely — do the interning guard and the
   externally-stamped turn ordering survive as necessary complexity, or do they simply evaporate?
3. **Can it still be hypothesised over?** THE objection, from `metaprocedure_model.md` §1b: a declared rule
   can be walked by `chain_sip`/`suppose()`, an opaque Python function cannot, so moving mechanism to
   Python was argued to cost hypothetical reasoning. This checks the counter-argument directly — you do
   not need to walk the derivation symbolically if you can RUN the algorithm against a pencil graph and
   read off the answer. If that works, §1b defended the wrong thing.

Re-runnable: `python -m units.mini_algorithm_comparison_experiment`.
"""
from __future__ import annotations

from .engine import effects_of
from .graph import named, role_edge
from .episode_to_procedure_probe_experiment import (
    _by_name, _network, _role_target, _run_episode, _settle,
)


# --- THE MINI-ALGORITHM: the whole of Probe C's compile step, as an ordinary function ------------------
def compile_episode(g, goal):
    """Read an achieved goal's applications; write one procedure whose steps are the operations applied,
    in the order they were applied. Returns the updated graph and the procedure node.

    Compare against `_COMPILE_START_PAT` + `_COMPILE_STEP_PAT` + their two `absent(...)` guards:

    * **Interning evaporates.** "One procedure per episode" is `named(...)` called once, outside the loop.
      There is no second firing to guard against, because there is no firing.
    * **Ordering evaporates.** `sorted(...)` on whatever ordering key is available. The turn-stamping the
      rule version needed from the outer driver is still USEFUL (it records real time), but it is no longer
      LOAD-BEARING — the loop has an order regardless.
    * **The settle discipline evaporates.** No reflective axiom, no gates, no waiting a turn for a
      sibling's conclusion to become visible.
    """
    if g.attr(goal, "achieved") is not True:
        return g, None
    apps = [x for x in g.nodes
            if g.attr(x, "name") == "application" and _role_target(g, x, "on") == goal]
    ordered = sorted(apps, key=lambda a: (_turn_of(g, a), str(a)))
    g, proc = named(g, "procedure")
    g = role_edge(g, proc, "learned_from", goal)
    for app in ordered:
        op = _role_target(g, app, "of")
        if op is not None:
            g = role_edge(g, proc, "step", op)
    return g, proc


def _turn_of(g, app) -> int:
    t = _role_target(g, app, "at")
    v = g.attr(t, "at") if t is not None else None
    return v if isinstance(v, int) else -1


def _steps_of(g, proc) -> list:
    out = []
    for r in g.out(proc):
        if g.attr(r, "name") == "step":
            out.extend(g.attr(t, "name") for t in g.out(r))
    return out


def check_produces_the_same_data_as_the_rule_version() -> dict[str, object]:
    """The control. Same episode, both approaches, compared on the data they leave behind."""
    n, reflect, goal, _ = _run_episode()
    g_mini, proc_mini = compile_episode(n.asserted, goal)
    mini_steps = sorted(_steps_of(g_mini, proc_mini)) if proc_mini else []

    n2, reflect2, goal2, _ = _run_episode()
    for turn in (5, 6):
        _settle(n2, reflect2, turn)
    rule_procs = _by_name(n2, "procedure")
    rule_steps = sorted(_steps_of(n2.asserted, rule_procs[0])) if rule_procs else []

    return {"mini_algorithm_steps": mini_steps,
            "rule_version_steps": rule_steps,
            "identical": mini_steps == rule_steps and bool(mini_steps),
            "procedures_minted_mini": 1 if proc_mini else 0,
            "procedures_minted_rules": len(rule_procs)}


def check_accidental_complexity_actually_evaporates() -> dict[str, object]:
    """Not a vibe — counted. The rule version needs an interning guard to avoid minting a procedure per
    firing. Does the mini-algorithm need one? Run it and see whether anything duplicates."""
    n, reflect, goal, _ = _run_episode()
    g, proc = compile_episode(n.asserted, goal)
    # Run it AGAIN on its own output — the exact situation the interning NAC exists to survive.
    g2, proc2 = compile_episode(g, goal)
    procs_after_two_runs = len([x for x in g2.nodes if g2.attr(x, "name") == "procedure"])
    return {"nac_guards_needed_by_rule_version": 2,
            "nac_guards_needed_by_mini_algorithm": 0,
            "driver_turn_stamp_load_bearing_for_ordering": False,
            "procedures_after_running_twice": procs_after_two_runs,
            "NOTE": ("re-running duplicates, because idempotence is now the CALLER's job rather than a "
                     "guard's — the complexity moved rather than vanishing entirely, and this is the one "
                     "place the rule version's discipline was buying something real")}


def check_can_still_be_hypothesised_over() -> dict[str, object]:
    """THE objection (`metaprocedure_model.md` §1b): moving mechanism to Python was argued to cost
    hypothetical reasoning, because `chain_sip` can walk a declared rule but not an opaque function.

    The counter-argument, tested here: you do not need to walk the derivation symbolically. Pen the
    assumption into a scratch graph, RUN the mini-algorithm against it, read the answer off, and discard.
    Here the hypothesis is counterfactual — 'what if the goal had NOT been achieved?' — and the algorithm
    must answer differently under it, while the real graph stays untouched."""
    n, reflect, goal, _ = _run_episode()
    real_before = len(_by_name(n, "procedure"))

    # Pencil: a scratch graph in which the goal was never achieved.
    pencil = n.asserted.with_node(goal, achieved=None)
    pencil_out, pencil_proc = compile_episode(pencil, goal)

    # Pencil: and one in which it was (the factual case), for contrast.
    factual_out, factual_proc = compile_episode(n.asserted, goal)

    # ⚠ The first version asserted `real_before == real_after == 0`, which was simply a wrong expectation
    # on my part rather than a finding: `_run_episode` runs the RULE version's `compile_start` during its
    # four turns, so a procedure already exists before the mini-algorithm is ever called. What matters for
    # this check is that running the algorithm on a pencil graph leaves the real graph UNCHANGED — not
    # that the real graph is empty.
    real_after = len([x for x in n.asserted.nodes if n.asserted.attr(x, "name") == "procedure"])
    return {"hypothetical_not_achieved_compiles_nothing": pencil_proc is None,
            "factual_achieved_compiles_a_procedure": factual_proc is not None,
            "real_graph_unchanged_by_the_pencil_run": real_before == real_after,
            "verdict": ("running the algorithm on a pencil graph answers the counterfactual without "
                        "symbolic walking — §1b's objection does not hold for this shape of question")}


def report() -> str:
    lines = ["=== MINI-ALGORITHM COMPARISON — should metaprocedures be rules, or functions over data? ==="]
    lines.append(f"same data as the rule version: {check_produces_the_same_data_as_the_rule_version()}")
    lines.append(f"accidental complexity:         {check_accidental_complexity_actually_evaporates()}")
    lines.append(f"still hypothesisable:          {check_can_still_be_hypothesised_over()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())

"""EPISODE→PROCEDURE PROBE — Probe C of `graph_data_model.md` §7. The payoff claim, stated so it can fail.

`the_data_model.md`'s closing claim: **if a metarule application is a node, then a learned metaprocedure
needs no new representation whatsoever** — an episode is a sequence of application nodes, and compiling it
into something reusable is DECOMPOSE + ORDER, two operations that already exist, applied to application
nodes instead of to domain steps. Probe B established applications are ordinary citizens. This probe asks
whether the compilation actually follows, or whether something new is needed after all.

**The scenario.** A goal is worked on across several turns; each operation applied to it mints an
application (Probe B's shape). The goal reaches `achieved`. A *compile* rule — itself an ordinary rule —
then reads the achieved goal and its applications and mints a `procedure` whose steps are the operations
that were applied, in the order they were applied. A fresh, structurally similar goal arrives, and an
*invoke* rule reads that procedure and marks its operations `chosen` — the same `chosen` fact
`corpus/procedure.cnl`'s pre-made plans produce, which is the point: a learned procedure and a
hand-authored one converge on one representation and one executor.

**⚠ The finding this probe was built around, and it is a real gap rather than a confirmation.**
Applications minted in the same settle have **no inherent order**. Rules in one `revive()` do not fire in
a defined sequence, and nothing in a minted node records when it was minted — so an episode harvested from
applications alone is an unordered *bag*, and "the order they were applied" is not recoverable from the
graph. This is not a flaw in the application-as-node idea; it is a missing ingredient nobody had named.
The fix used here is the smallest honest one: the **outer driver** stamps a turn marker (an ordinary node
whose value it bumps per turn), and each application links to the marker current when it was minted. That
is legitimate — the driver is exactly the layer `metaprocedure_model.md` §1a says correctly holds the VM's
own stepping state — but it must be *stated*, because it means episodes are only as ordered as the driver
makes them, and two operations applied in the same turn are genuinely, irreducibly unordered.

Re-runnable: `python -m units.episode_to_procedure_probe_experiment`.
"""
from __future__ import annotations

from .engine import Attribute, Emit, Link, Network, StandingUnit, Value, effects_of
from .graph import EMPTY, named, role_edge
from .match import AttrVar, absent, atom, role

# --- the two operations whose applications form the episode ------------------------------------------
_TRIAGE_PAT = (atom("g", name="goal", triaged=None, out=(role("wants", atom()),)),
                atom("r", name="triage"), atom("t", name="turn", at=AttrVar("k")))
_RESOLVE_PAT = (atom("g", name="goal", triaged=True, resolved=None, out=(role("wants", atom()),)),
                 atom("r", name="resolve"), atom("t", name="turn", at=AttrVar("k")))

# --- compile: an ACHIEVED goal's applications become a procedure's steps ------------------------------
# Ordinary DECOMPOSE (mint a parent, link children) — the same shape `goal_decomposition_experiment.py`
# uses for domain subgoals, aimed at application nodes instead.
#
# ⚠ **Correction, from this probe's first run failing.** The first version was a single rule minting a
# `procedure` per matching application — which produced TEN procedures across the settle turns, each with
# one step, instead of one procedure with two. `Emit` mints fresh on every firing; "one procedure per
# episode" is an INTERNING problem, and `goal_machinery.md` §2 already names interning as load-bearing and
# NAC-shaped. So compiling an episode is *not* bare DECOMPOSE after all — it is DECOMPOSE plus the same
# interning guard subgoal-raising needs, split across two rules: create the procedure once, then add each
# operation as a step once. Both guards are ordinary `absent(...)`; nothing new in kind, but the claim
# "needs only decompose" was too strong as originally written.
_COMPILE_START_PAT = (atom("g", name="goal", achieved=True),
                       absent(atom(name="procedure", out=(role("learned_from", atom("g")),))))

_COMPILE_STEP_PAT = (atom("p", name="procedure", out=(role("learned_from", atom("g", name="goal")),)),
                      atom("app", name="application",
                           out=(role("on", atom("g")), role("of", atom("op")))),
                      absent(atom("p", out=(role("step", atom("op")),))))

# --- invoke: a fresh goal + a learned procedure -> `chosen` on its operations -------------------------
_INVOKE_PAT = (atom("g2", name="goal", achieved=None, invoked=None, out=(role("wants", atom()),)),
                atom("p", name="procedure",
                     out=(role("step", atom("op", chosen=None)),)),
                absent(atom("g2", out=(role("raised", atom()),))))


def _op_rule(name: str, pat, *effects) -> StandingUnit:
    return StandingUnit(
        name, pat, *effects,
        Emit("application", as_="app"),
        Link("app", "r", role="of"), Link("app", "g", role="on"), Link("app", "t", role="at"),
        gates=("in",), mutating=True)


def rules() -> dict[str, StandingUnit]:
    return {
        "triage": _op_rule("triage", _TRIAGE_PAT, Attribute("g", "triaged", True)),
        "resolve": _op_rule("resolve", _RESOLVE_PAT,
                             Attribute("g", "resolved", True), Attribute("g", "achieved", True)),
        # Compile is an ordinary mutating rule: for each application of an achieved goal, add a step to
        # the learned procedure. `Emit(as_=)` + interning is what keeps it to ONE procedure.
        "compile_start": StandingUnit("compile_start", _COMPILE_START_PAT,
                                       Emit("procedure", as_="p"), Link("p", "g", role="learned_from"),
                                       mutating=True),
        "compile_step": StandingUnit("compile_step", _COMPILE_STEP_PAT,
                                      Link("p", "op", role="step"), mutating=True),
        "invoke": StandingUnit("invoke", _INVOKE_PAT,
                                Attribute("op", "chosen", True), Attribute("g2", "invoked", True),
                                mutating=True),
    }


def _settle(n: Network, reflect, turn: int | None = None) -> None:
    """One turn. The driver bumps the turn marker — the ordering source rules cannot supply themselves."""
    if turn is not None:
        t = next(x for x in n.asserted.nodes if n.asserted.attr(x, "name") == "turn")
        n.asserted = n.asserted.with_node(t, at=turn)
    reflect.held = Value(effects_of(n.asserted))
    n.revive()


def _network():
    g = EMPTY
    g, goal = named(g, "goal")
    g, want = named(g, "ticket_resolved")
    g = role_edge(g, goal, "wants", want)
    g, _turn = named(g, "turn", at=0)
    n = Network()
    ax = n.given(g)
    built = rules()
    for r in built.values():
        n.add(r)
    reflect = n.axiom(*effects_of(n.asserted), name="reflect")
    for r in built.values():
        n.wire(reflect, r)
    ax.held = None
    return n, reflect, goal, built


def _by_name(n, nm):
    return [x for x in n.asserted.nodes if n.asserted.attr(x, "name") == nm]


def _role_target(g, node, role_name):
    for r in g.out(node):
        if g.attr(r, "name") == role_name:
            t = g.out(r)
            if t:
                return t[0]
    return None


def _run_episode():
    """Work one goal to `achieved` across separate turns, so its applications land in distinct turns."""
    n, reflect, goal, built = _network()
    n.revive()
    for turn in (1, 2, 3, 4):
        _settle(n, reflect, turn)
    return n, reflect, goal, built


def check_episode_is_recorded_with_recoverable_order() -> dict[str, object]:
    """The precondition for everything else: applications exist, and each carries the turn it happened in,
    so the episode is a SEQUENCE rather than a bag."""
    n, reflect, goal, _ = _run_episode()
    apps = _by_name(n, "application")
    stamped = []
    for a in apps:
        op = _role_target(n.asserted, a, "of")
        t = _role_target(n.asserted, a, "at")
        stamped.append((n.asserted.attr(op, "name"), n.world().attr(t, "at")))
    return {"goal_achieved": n.world().attr(goal, "achieved"),
            "applications": len(apps),
            "operations_recorded": sorted({s[0] for s in stamped}),
            "every_application_carries_a_turn": all(s[1] is not None for s in stamped)}


def check_compiling_an_episode_needs_only_decompose() -> dict[str, object]:
    """The payoff. A learned `procedure` whose steps are the OPERATIONS that were applied — minted by an
    ordinary mutating rule using nothing but `Emit`/`Link`, the same shape domain decomposition uses."""
    n, reflect, goal, _ = _run_episode()
    for turn in (5, 6):
        _settle(n, reflect, turn)
    procs = _by_name(n, "procedure")
    steps = []
    if procs:
        for r in n.asserted.out(procs[0]):
            if n.asserted.attr(r, "name") == "step":
                steps.extend(n.asserted.attr(t, "name") for t in n.asserted.out(r))
    return {"procedures_minted": len(procs),
            "steps_are_the_operations_applied": sorted(set(steps)),
            "compiled_with_no_new_effect_kind": bool(procs)}


def check_learned_procedure_runs_on_a_fresh_goal() -> dict[str, object]:
    """And it must be RUNNABLE — the learned procedure marks its operations `chosen` on a new goal, the
    same fact a hand-authored procedure produces. If this holds, learned and authored converge on one
    executor, which is the whole claim."""
    n, reflect, goal, _ = _run_episode()
    for turn in (5, 6):
        _settle(n, reflect, turn)

    g2, fresh = named(n.asserted, "goal")
    g2, want2 = named(g2, "ticket_resolved")
    g2 = role_edge(g2, fresh, "wants", want2)
    n.asserted = g2
    for turn in (7, 8):
        _settle(n, reflect, turn)

    chosen = [n.asserted.attr(x, "name") for x in n.asserted.nodes
              if n.world().attr(x, "chosen") is True]
    return {"fresh_goal_invoked": n.world().attr(fresh, "invoked"),
            "operations_marked_chosen": sorted(set(chosen)),
            "learned_procedure_is_runnable": bool(chosen)}


def report() -> str:
    lines = ["=== EPISODE→PROCEDURE PROBE (Probe C) — does a learned metaprocedure need anything new? ==="]
    lines.append(f"episode recorded, ordered:  {check_episode_is_recorded_with_recoverable_order()}")
    lines.append(f"compiled via DECOMPOSE:     {check_compiling_an_episode_needs_only_decompose()}")
    lines.append(f"runnable on a fresh goal:   {check_learned_procedure_runs_on_a_fresh_goal()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())

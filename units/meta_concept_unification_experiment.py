"""META-CONCEPT UNIFICATION EXPERIMENT — do goal, procedure, question, and prohibition reduce to one
representational shape, or does a seam appear once they're actually combined?

Raised in conversation while designing plan composition: goal/subgoal machinery, procedures, question
answering, and standing prohibitions were each discussed as if they might need their own architecture —
the worry being that without one common computation model, each "meta-concept" lives in isolation and
can't genuinely combine (a procedure whose steps require answering a question; an action blocked by a
standing "never do this" fact). The claim under test: all four are the **same** shape — a goal
(node + `wants:` + `raised:`) — with only surface differences (whether children are ordered; whether the
wanted condition is a knowledge-claim or a world-state claim; a stance fact consulted as a veto), and
every mechanism involved (achieved/diverged, the reflective-axiom-lifecycle discipline, closure-before-NAC,
AttrVar-linked NAC checks, the consumption-marker discipline) is already built and tested individually —
this experiment is the first place they're combined in one scenario.

**The scenario:** a `procedure` goal ("resolve a support ticket") decomposes, one-shot, into two ORDERED
steps (`then:`, `goal_decomposition_experiment.py`'s exact shape plus one sequencing edge):

1. A **question** step — `kind="question"`, wants to know the customer's account tier. Resolved the same
   way any goal is: a positive `wants->true` fact, `achieved`/`diverged` exactly as `goal_machinery.md` §2.
2. An **action** step — `kind="action"`, wants to be routed to an agent — but can only be *attempted*
   once the question step has `achieved` (sequencing, checked via an ordinary `then:`-edge premise) **and**
   no standing `forbidden` fact matches the specific agent it names (a prohibition, expressed exactly as
   `nac_verification_experiment.py` §9's stance fact — an ordinary `absent(...)` NAC, linked to the
   concrete candidate agent via `AttrVar`, not hardcoded).

Three checks, all against the real engine:

1. **The procedure decomposes into ordered, differently-kinded steps** — `check_decomposes_into_ordered_
   steps`. Confirms a "procedure" needs nothing beyond `goal_decomposition_experiment.py`'s decompose
   shape plus one `then:` edge — no new mint kind, no new gate.
2. **Unblocked: the question resolves, and only then does the action step execute — never before, and
   the whole procedure's own `achieved` only lands once both steps genuinely have** —
   `check_question_then_action_reaches_achieved_in_order`. Confirms sequencing is an ordinary premise (not
   a special construct) and confirms `goal_decomposition_experiment.py` §8's closure-before-NAC discipline
   (the parent's `achieved` needs a positive existence premise, not a bare NAC) still holds one layer
   deeper.
3. **Blocked: the same question resolves, but a standing prohibition matching the chosen agent means the
   action step never executes, ever — and the procedure honestly never reaches `achieved`** —
   `check_prohibition_blocks_action_step_indefinitely`. Confirms a prohibition composes with everything
   else without needing its own machinery: it's one more `absent(...)` premise on the rule that would
   otherwise act, using `AttrVar` to tie the veto to *this* candidate's specific content rather than a
   hardcoded name.

Re-runnable: `python -m units.meta_concept_unification_experiment`.
"""
from __future__ import annotations

from .engine import Attribute, Emit, Link, Network, StandingUnit, Value, effects_of
from .graph import EMPTY, named, role_edge
from .match import AttrVar, absent, atom, role

_DECOMPOSE_PAT = (atom("g", name="procedure", out=(role("wants", atom()),)),
                   absent(atom("g", out=(role("raised", atom()),))))

_QUESTION_ACHIEVED_PAT = (atom("sg", name="step", kind="question", achieved=None,
                                out=(role("wants", atom("c", true=True)),)),)
_QUESTION_DIVERGED_PAT = (atom("sg", name="step", kind="question", diverged=None,
                                out=(role("wants", atom("c", true=False)),)),)

# Sequencing (`then:`) and the prohibition veto (`AttrVar`-linked `absent(forbidden)`) are both ordinary
# premises on the SAME rule — nothing separates "check the order" from "check the veto."
_ATTEMPT_ACTION_PAT = (
    atom("sg1", name="step", kind="question", achieved=True,
         out=(role("then", atom("sg2", name="step", kind="action", executed=None,
                                 out=(role("action", atom("act", name="route_to_agent",
                                                           agent=AttrVar("ag"))),))),)),
    absent(atom("f", name="forbidden", agent=AttrVar("ag"))),
)

_PROC_ACHIEVED_PAT = (atom("g", name="procedure", out=(role("raised", atom()),)),
                       absent(atom("g", out=(role("raised", atom(achieved=None)),))),
                       absent(atom("g", out=(role("raised", atom(diverged=True)),))))


def _decompose_rule() -> StandingUnit:
    return StandingUnit(
        "decompose", _DECOMPOSE_PAT,
        Emit("step", as_="sg1"), Attribute("sg1", "kind", "question"),
        Emit("tier_known", as_="c1"), Link("sg1", "c1", role="wants"),
        Emit("step", as_="sg2"), Attribute("sg2", "kind", "action"),
        Emit("routed", as_="c2"), Link("sg2", "c2", role="wants"),
        Emit("route_to_agent", as_="act"), Attribute("act", "agent", "agent_x"),
        Link("sg2", "act", role="action"),
        Link("sg1", "sg2", role="then"),
        Link("g", "sg1", role="raised"), Link("g", "sg2", role="raised"),
        mutating=True)


def _rules() -> dict[str, StandingUnit]:
    return {
        "decompose": _decompose_rule(),
        "question_achieved": StandingUnit("question_achieved", _QUESTION_ACHIEVED_PAT,
                                           Attribute("sg", "achieved", True), mutating=True),
        "question_diverged": StandingUnit("question_diverged", _QUESTION_DIVERGED_PAT,
                                           Attribute("sg", "diverged", True), mutating=True),
        "attempt_action": StandingUnit("attempt_action", _ATTEMPT_ACTION_PAT,
                                        Attribute("sg2", "executed", True),
                                        Attribute("sg2", "achieved", True), mutating=True),
        "proc_achieved": StandingUnit("proc_achieved", _PROC_ACHIEVED_PAT,
                                       Attribute("g", "achieved", True), mutating=True),
    }


def _find(g, name: str):
    return next(n for n in g.nodes if g.attrs.get(n, {}).get("name") == name)


def _settle(n: Network, reflect) -> None:
    reflect.held = Value(effects_of(n.asserted))
    n.revive()


def _build(with_prohibition: bool):
    g = EMPTY
    g, proc = named(g, "procedure")
    g, trigger = named(g, "ticket_resolved")
    g = role_edge(g, proc, "wants", trigger)
    if with_prohibition:
        g, _ = named(g, "forbidden", agent="agent_x")
    return g, proc


def _network(with_prohibition: bool):
    g, proc = _build(with_prohibition)
    n = Network()
    ax = n.given(g)
    rules = _rules()
    for r in rules.values():
        n.add(r)
    reflect = n.axiom(*effects_of(n.asserted), name="reflect")
    for r in rules.values():
        n.wire(reflect, r)
    ax.held = None
    return n, reflect, proc


def check_decomposes_into_ordered_steps() -> dict[str, object]:
    """A procedure needs no new mint kind — `goal_decomposition_experiment.py`'s decompose shape plus one
    `then:` edge, checked directly for the ordering and the kind split."""
    n, reflect, proc = _network(with_prohibition=False)
    n.revive()
    steps = [x for x in n.asserted.nodes if n.asserted.attr(x, "name") == "step"]
    by_kind = {n.asserted.attr(s, "kind"): s for s in steps}
    question_step, action_step = by_kind["question"], by_kind["action"]
    then_roles = [r for r in n.asserted.out(question_step) if n.asserted.attr(r, "name") == "then"]
    then_target = n.asserted.out(then_roles[0])[0] if then_roles else None
    return {"two_steps_minted": len(steps) == 2,
            "question_step_then_edges_to_action_step": then_target == action_step}


def check_question_then_action_reaches_achieved_in_order() -> dict[str, object]:
    """The question resolves; the action step must stay `executed=None` until it genuinely does, never
    before; the procedure's own `achieved` must wait for both, never fire early."""
    n, reflect, proc = _network(with_prohibition=False)
    n.revive()
    _settle(n, reflect)  # decompose's own output now visible

    c1 = _find(n.asserted, "tier_known")
    n.asserted = n.asserted.with_node(c1, true=True)
    _settle(n, reflect)  # question_achieved fires this turn (first-level, same-turn visible)
    action_step = next(s for s in n.asserted.nodes if n.asserted.attr(s, "name") == "step"
                        and n.asserted.attr(s, "kind") == "action")
    executed_right_after_question_resolves = n.world().attr(action_step, "executed")

    _settle(n, reflect)  # attempt_action sees SG1.achieved via refreshed reflect, fires
    _settle(n, reflect)  # proc_achieved sees SG2.achieved via refreshed reflect, fires

    return {"action_step_not_executed_before_its_own_turn":
                executed_right_after_question_resolves is None,
            "action_step_executed_eventually": n.world().attr(action_step, "executed"),
            "procedure_achieved": n.world().attr(proc, "achieved")}


def check_prohibition_blocks_action_step_indefinitely() -> dict[str, object]:
    """Same scenario, but a standing `forbidden` fact matches the chosen agent from the start. The
    question still resolves (unrelated to the veto) but the action step must never execute, across many
    idle settle turns, and the procedure must never reach `achieved`."""
    n, reflect, proc = _network(with_prohibition=True)
    n.revive()
    _settle(n, reflect)

    c1 = _find(n.asserted, "tier_known")
    n.asserted = n.asserted.with_node(c1, true=True)
    _settle(n, reflect)

    action_step = next(s for s in n.asserted.nodes if n.asserted.attr(s, "name") == "step"
                        and n.asserted.attr(s, "kind") == "action")
    executed_per_idle_turn = []
    for _ in range(4):
        _settle(n, reflect)
        executed_per_idle_turn.append(n.world().attr(action_step, "executed"))

    return {"executed_per_idle_turn": executed_per_idle_turn,
            "procedure_achieved": n.world().attr(proc, "achieved")}


def report() -> str:
    lines = ["=== META-CONCEPT UNIFICATION EXPERIMENT: goal / procedure / question / prohibition ==="]
    lines.append(f"decomposes into ordered, kinded steps: {check_decomposes_into_ordered_steps()}")
    lines.append(f"unblocked -> ordered, honest achieved: "
                 f"{check_question_then_action_reaches_achieved_in_order()}")
    lines.append(f"blocked by a prohibition, indefinitely: "
                 f"{check_prohibition_blocks_action_step_indefinitely()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())

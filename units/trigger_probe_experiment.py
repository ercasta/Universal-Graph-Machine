"""TRIGGER PROBE — the check `north_star.md` §5 needs before any code is written against the repoint.

**What the repoint costs, precisely.** Under ambient rule matching a prohibition works without anybody
wiring it to what it guards: a standing rule fires whenever the world matches it, so a `forbidden` fact
recorded *before* a command blocks that command, and one recorded *after* the command was proposed blocks
it too. `prohibition_rules.py` verified exactly that order-independence. Mini-algorithms do not get this
for free — a function nobody calls never runs — so §5 proposes recovering it the way databases do: a
write-triggered check at the single choke point where a proposal becomes a real effect.

**This probe exists to find out whether that recovery is actually equivalent, or merely plausible.** Four
checks that could each fail, plus one deliberate negative result:

1. `check_dangerous_action_is_vetoed_at_the_choke_point` — the basic case.
2. `check_prohibition_recorded_AFTER_the_proposal_still_blocks` — **the one that matters.** This is the
   order-independence ambient matching gave away free, and the property most likely to be quietly lost when
   moving to called code. If this fails, §5 is wrong and the repoint needs rethinking.
3. `check_completed_work_is_not_retroactively_undone` — the gate stops the NEXT action, never reaches back.
4. `check_a_later_authored_action_cannot_bypass_the_gate` — a proposal minted by a code path that has never
   heard of prohibitions still passes the same check, because there is structurally one executor. This is
   the argument for a choke point over per-caller checks, tested rather than asserted.
5. `check_a_state_no_write_announced_is_NOT_caught` — the honest residue. Write-triggering catches acts,
   not states. A danger that arises without any write to trigger on is genuinely missed, and needs a
   scheduled sweep. Recorded as a demonstrated limitation, not hidden.

Everything here is ordinary functions over the graph — no `StandingUnit`, no matching, no settle loop —
because that is the thing under test.

Re-runnable: `python -m units.trigger_probe_experiment`.
"""
from __future__ import annotations

from .graph import EMPTY, named, role_edge

# The one reserved marker the executor is allowed to know about — a name, never a value it interprets.
# `metaprocedure_model.md` §4: this costs the dispatcher one bit of content-awareness, the same bit every
# other VM-level mechanism already carries.
_VETO = "forbidden"


# --- THE CHOKE POINT ----------------------------------------------------------------------------------
def veto_reason(g, proposal):
    """The BEFORE trigger. Consults graph-resident veto data; returns the blocking fact or None.

    Content-blind in the way that matters: it does not know what `route_to_agent` or `wire_funds` mean, only
    that a `forbidden` fact naming the same target exists."""
    target = _role_target(g, proposal, "on")
    if target is None:
        return None
    for n in g.nodes:
        if g.attr(n, "name") == _VETO and _role_target(g, n, "on") == target:
            return n
    return None


def service(g):
    """THE one executor. Every proposal in the graph becomes a real effect here or nowhere. A proposal is
    checked immediately before it is applied — not when it was minted, which is what makes a prohibition
    recorded later still count."""
    executed, blocked = [], []
    for p in [x for x in g.nodes if g.attr(x, "name") == "proposal"]:
        if g.attr(p, "done") or g.attr(p, "blocked"):
            continue
        reason = veto_reason(g, p)
        if reason is not None:
            g = g.with_node(p, blocked=True)
            blocked.append(p)
        else:
            g = g.with_node(p, done=True)
            executed.append(p)
    return g, executed, blocked


def _role_target(g, node, role_name):
    for r in g.out(node):
        if g.attr(r, "name") == role_name:
            t = g.out(r)
            if t:
                return t[0]
    return None


def _world(with_prohibition: bool = False):
    # ⚠ The first version took `with_prohibition_on=None` and tested `is not None` — so `False` (the whole
    # point of the parameter) still added the prohibition, and two checks silently tested the wrong world.
    # Caught because `no_prohibition_when_proposal_was_minted` came back False when it had to be True.
    g = EMPTY
    g, agent = named(g, "agent_x")
    g, prop = named(g, "proposal")
    g = role_edge(g, prop, "on", agent)
    if with_prohibition:
        g = _forbid(g, agent)
    return g, prop, agent


def _forbid(g, target):
    g, f = named(g, _VETO)
    return role_edge(g, f, "on", target)


def check_dangerous_action_is_vetoed_at_the_choke_point() -> dict[str, object]:
    g, prop, agent = _world(with_prohibition=True)
    g, executed, blocked = service(g)
    return {"executed": len(executed), "blocked": len(blocked),
            "proposal_done": g.attr(prop, "done"), "proposal_blocked": g.attr(prop, "blocked")}


def check_prohibition_recorded_AFTER_the_proposal_still_blocks() -> dict[str, object]:
    """THE decisive check. The proposal is minted first, with no prohibition anywhere. Only then is the
    prohibition recorded. Ambient matching handled this for free; a called check handles it only if the
    check happens at APPLY time rather than at MINT time."""
    g, prop, agent = _world(with_prohibition=False)
    minted_with_no_prohibition_present = veto_reason(g, prop) is None
    g = _forbid(g, agent)                      # recorded later, by something that never saw the proposal
    g, executed, blocked = service(g)
    return {"no_prohibition_when_proposal_was_minted": minted_with_no_prohibition_present,
            "blocked_anyway": bool(blocked),
            "never_executed": g.attr(prop, "done") is None,
            "order_independence_preserved": bool(blocked) and g.attr(prop, "done") is None}


def check_completed_work_is_not_retroactively_undone() -> dict[str, object]:
    """A gate stops the next action; it must never reach back into one already applied."""
    g, first, agent = _world(with_prohibition=False)
    g, executed_first, _ = service(g)
    g, second = named(g, "proposal")
    g = role_edge(g, second, "on", agent)
    g = _forbid(g, agent)
    g, executed_second, blocked = service(g)
    return {"first_executed_before_prohibition": bool(executed_first),
            "first_still_done_afterwards": g.attr(first, "done") is True,
            "second_blocked": bool(blocked),
            "second_never_executed": g.attr(second, "done") is None}


def check_a_later_authored_action_cannot_bypass_the_gate() -> dict[str, object]:
    """A proposal minted by a code path that knows nothing about prohibitions. It is still checked,
    because there is structurally one executor — the argument for a choke point over per-caller checks."""
    g, _prop, agent = _world(with_prohibition=True)

    def some_future_feature(graph, target):        # deliberately ignorant of `_VETO`
        graph, p = named(graph, "proposal")
        return role_edge(graph, p, "on", target), p

    g, newcomer = some_future_feature(g, agent)
    g, executed, blocked = service(g)
    return {"newcomer_authored_with_no_veto_awareness": True,
            "newcomer_blocked": newcomer in blocked,
            "nothing_executed": len(executed) == 0}


def check_a_state_no_write_announced_is_NOT_caught() -> dict[str, object]:
    """THE HONEST RESIDUE, and a deliberate negative result. Write-triggering catches ACTS. A dangerous
    condition that arises with no write to trigger on is genuinely missed — nothing fired because nothing
    happened. Recovering it needs a scheduled sweep, which is ordinary but must be scheduled, and is the
    real cost of leaving ambient matching behind."""
    g, prop, agent = _world(with_prohibition=False)
    g, executed, _ = service(g)                    # nothing forbidden yet: it runs
    g = _forbid(g, agent)                          # danger becomes true AFTER the fact, no proposal pending

    g_after, executed_after, blocked_after = service(g)
    caught_by_trigger = bool(blocked_after)

    def sweep(graph):                              # the scheduled residue
        return [x for x in graph.nodes
                if graph.attr(x, "name") == "proposal" and graph.attr(x, "done")
                and veto_reason(graph, x) is not None]

    return {"trigger_caught_the_standing_danger": caught_by_trigger,
            "a_scheduled_sweep_finds_it": len(sweep(g_after)) == 1,
            "CONCLUSION": ("write-triggering is complete for guarding ACTS and structurally cannot cover "
                           "states nothing announced — a sweep is required, exactly as north_star.md §5 "
                           "states rather than assumes")}


def report() -> str:
    lines = ["=== TRIGGER PROBE — does write-triggered interception preserve what ambient matching gave? ==="]
    lines.append(f"vetoed at the choke point:      {check_dangerous_action_is_vetoed_at_the_choke_point()}")
    lines.append(f"prohibition recorded LATER:     {check_prohibition_recorded_AFTER_the_proposal_still_blocks()}")
    lines.append(f"completed work not undone:      {check_completed_work_is_not_retroactively_undone()}")
    lines.append(f"later-authored cannot bypass:   {check_a_later_authored_action_cannot_bypass_the_gate()}")
    lines.append(f"residue (deliberate negative):  {check_a_state_no_write_announced_is_NOT_caught()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())

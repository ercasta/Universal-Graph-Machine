"""QUANTIFICATION CURSOR EXPERIMENT — `closed_class_inventory.md` §8 case (c), built.

Case (c) is the one quantification case that isn't free: *"did every queue member get evaluated, but
checking each member needs more than one revive (e.g. a tool call per member)."* `model.md` §8 names the
shape needed — *"the cursor must be asserted data, advanced by a mutating rule (a cursor held as a derived
fact resets to the first hypothesis every revive)"* — and `goal_machinery.md` §3 settled how a turn works
in this engine. This is the worked example putting both together.

**The scenario:** a goal wants every member of a bounded set to be `eligible`. Whether a given member is
eligible cannot be computed in one revive — it arrives from outside, one member per turn (a stand-in for a
tool call per member). A `checked` marker is the cursor: a positive fact, minted by a mutating rule once a
member's result has arrived, and it must **survive** across turns or the same member would be re-asked
forever. The universal claim resolves the same way `goal_machinery.md` §2 already established for
outcomes — `achieved` / `diverged` are positive facts, concluded only once no unchecked member remains,
never read off an absence directly by a caller.

**Reuses, doesn't reinvent:** the axiom-lifecycle discipline (`goal_machinery.md` §3) for letting the
`achieved`/`diverged` rules see the accumulated `checked` state across turns — one reused reflective `Cell`,
refreshed in place, exactly as `system1_experiment.py` settled on. The per-turn "tool result" is written
directly into `self.asserted` (skipping `given()`'s own axiom bookkeeping, since nothing needs to be wired
to that event individually — only the shared reflective snapshot does) — a fair simplification for a test
harness standing in for a real external event.

⚠ **Correction, 2026-07-30: the second "same-turn" gate this section originally described has been removed
— it wasn't required, and it was inconsistent with how the rest of this engine treats fresh conclusions.**
The original reasoning was that `reflect.held`, refreshed *before* `revive()` runs, lags one turn behind
`check_member`'s own write-back for *that same* turn, so `achieved`/`diverged` would see the last member's
result one turn late unless wired directly to `check_member.cell`. Checked against `Network._drain()`
(`units/engine.py:801`): that reasoning about *why* a second source is sometimes needed was right in
general (a snapshot taken before a firing can't contain that firing's own output) — but the fix of a
dedicated "same_turn" gate was heavier than necessary for *this* file, and inconsistent with
`test_a_rule_writes_a_whole_rule_with_nothing_authored_in_python`'s own precedent, whose docstring says
plainly of freshly-produced structure: *"on the next turn it runs."* `achieved`/`diverged` now use the
plain reused-reflective-snapshot ("in") gate only, and the one-turn lag is accepted and traced explicitly
as a `settle` step rather than engineered away. A unit that can't yet conclude because its gate is empty
isn't failing silently either way — it's `dangling()` (`engine.py:569`), which `model.md` §7 names as the
honest "still waiting" signal.

Re-runnable: `python -m units.quantification_cursor_experiment`.
"""
from __future__ import annotations

from .engine import Attribute, Network, StandingUnit, Value, effects_of
from .graph import EMPTY, named
from .match import AttrVar, absent, atom

_CHECK_MEMBER_PAT = (atom("m", is_member=True, checked=None, eligible=AttrVar("v")),)

_ACHIEVED_PAT = (atom("g", name="goal"),
                  absent(atom(is_member=True, checked=None)),
                  absent(atom(is_member=True, eligible=False)))

_DIVERGED_PAT = (atom("g", name="goal"),
                  absent(atom(is_member=True, checked=None)),
                  atom("m", is_member=True, eligible=False))


def _build_goal(member_names: tuple) -> tuple:
    g = EMPTY
    g, goal = named(g, "goal")
    members = {}
    for nm in member_names:
        g, node = named(g, nm, is_member=True)
        members[nm] = node
    return g, goal, members


def _rules() -> tuple:
    check_member = StandingUnit("check_member", _CHECK_MEMBER_PAT,
                                 Attribute("m", "checked", True), mutating=True)
    # One gate, like every other rule in this file: the reused reflective snapshot. `achieved`/`diverged`
    # see a member's result one turn after `check_member` concludes it — accepted lag, traced explicitly
    # via `_settle`, not engineered away with a second gate.
    achieved = StandingUnit("achieved", _ACHIEVED_PAT, Attribute("g", "achieved", True), mutating=True)
    diverged = StandingUnit("diverged", _DIVERGED_PAT, Attribute("g", "diverged", True), mutating=True)
    return check_member, achieved, diverged


def _settle(n: Network, reflect) -> None:
    """No new external input — re-expose what the last turn wrote back, one turn later. The honest,
    precedented lag (`test_a_rule_writes_a_whole_rule_with_nothing_authored_in_python`'s "on the next turn
    it runs"), not hidden behind extra wiring."""
    reflect.held = Value(effects_of(n.asserted))
    n.revive()


def _run(member_names: tuple, eligibility: dict) -> list:
    """One member's result delivered per turn, in `member_names` order, each followed by an explicit
    settle turn. Returns the (achieved, diverged) read after *every* turn — including the settle turns —
    so both the honest "not yet decided" middle states and the one-turn lag itself are visible."""
    g, goal, members = _build_goal(member_names)
    n = Network()
    n.given(g)
    check_member, achieved, diverged = _rules()
    n.add(check_member)
    n.add(achieved)
    n.add(diverged)

    reflect = n.axiom(*effects_of(n.asserted), name="reflect")
    n.wire(reflect, check_member)                    # fan-out: three consumers, one shared source
    n.wire(reflect, achieved)
    n.wire(reflect, diverged)

    trace = []
    for nm in member_names:
        n.asserted = n.asserted.with_node(members[nm], eligible=eligibility[nm])  # the "tool result"
        reflect.held = Value(effects_of(n.asserted))                              # refresh in place
        n.revive()
        trace.append({"turn": f"{nm}_result",
                       "achieved": n.world().attr(goal, "achieved"),
                       "diverged": n.world().attr(goal, "diverged")})
        _settle(n, reflect)
        trace.append({"turn": f"settle_after_{nm}",
                       "achieved": n.world().attr(goal, "achieved"),
                       "diverged": n.world().attr(goal, "diverged")})
    return trace


def check_all_eligible_reaches_achieved_only_at_the_end() -> dict[str, object]:
    """Three members, all eligible. `achieved` must stay `None` through every middle turn — concluding it
    early would be exactly the false-completeness `model.md` §8 exists to prevent — and become `True`
    only on the settle turn after the third (last) member's result has arrived."""
    trace = _run(("m1", "m2", "m3"), {"m1": True, "m2": True, "m3": True})
    return {"trace": trace}


def check_one_ineligible_member_reaches_diverged_not_achieved() -> dict[str, object]:
    """Same shape, one member fails. `diverged` (not `achieved`) lands on the settle turn after every
    member has been checked — the universal claim is honestly false, stated as a positive fact, not
    silently absent."""
    trace = _run(("m1", "m2", "m3"), {"m1": True, "m2": False, "m3": True})
    return {"trace": trace}


def check_cursor_survives_because_it_is_asserted_not_derived() -> dict[str, object]:
    """The point `model.md` §8 makes explicit: `checked` is a mutating rule's conclusion, so it is real
    data in `self.asserted` and is still there on the next turn even before that turn's own revive touches
    it — unlike a computation unit's overlay, which would vanish and re-ask the same, already-answered
    member every turn."""
    g, goal, members = _build_goal(("m1", "m2"))
    n = Network()
    n.given(g)
    check_member = n.add(StandingUnit("check_member", _CHECK_MEMBER_PAT,
                                       Attribute("m", "checked", True), mutating=True))
    reflect = n.axiom(*effects_of(n.asserted), name="reflect")
    n.wire(reflect, check_member)

    n.asserted = n.asserted.with_node(members["m1"], eligible=True)
    reflect.held = Value(effects_of(n.asserted))
    n.revive()
    checked_after_turn_one = n.asserted.attr(members["m1"], "checked")

    # Turn two: m2's result arrives. m1 gets NO new tool result this turn -- if `checked` were a
    # computation unit's overlay instead of a mutating rule's conclusion, it would vanish here.
    n.asserted = n.asserted.with_node(members["m2"], eligible=True)
    reflect.held = Value(effects_of(n.asserted))
    n.revive()
    return {"m1_checked_after_turn_one": checked_after_turn_one,
            "m1_still_checked_after_turn_two_with_no_new_input_for_it":
                n.asserted.attr(members["m1"], "checked")}


def report() -> str:
    lines = ["=== QUANTIFICATION CURSOR EXPERIMENT: closed_class_inventory.md §8 case (c) ==="]
    lines.append(f"all eligible -> achieved only at the end: "
                 f"{check_all_eligible_reaches_achieved_only_at_the_end()}")
    lines.append(f"one ineligible -> diverged, not achieved: "
                 f"{check_one_ineligible_member_reaches_diverged_not_achieved()}")
    lines.append(f"cursor survives because it's asserted, not derived: "
                 f"{check_cursor_survives_because_it_is_asserted_not_derived()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())

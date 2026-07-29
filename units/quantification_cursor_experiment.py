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

⚠ **One new wrinkle, found and fixed while building this: the reflective snapshot alone lags one turn on
the *very same* revive that finishes the job.** `reflect.held` is refreshed *before* `revive()` runs, which
is *before* `check_member`'s own write-back for *this* turn has happened — so `achieved`/`diverged`, wired
only to `reflect`, see last member's result one turn late (measured: `achieved` only became `True` on an
extra, otherwise-pointless settle turn after the last member). Fix: give `achieved`/`diverged` a **second**
gate, fed directly by `check_member.cell` — that unit's own output from *this* firing, which write-back
hasn't applied to `self.asserted` yet but which is already sitting in its cell. `view()` composes both gates,
so the same turn that checks the last member also concludes the outcome. This is the same "wire the single
axiom that's a superset" lesson from `goal_machinery.md` §4, one layer sharper: sometimes no single existing
snapshot *is* a superset within one revive, and the fix is a second, narrower source (a sibling rule's own
cell) rather than a bigger snapshot.

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
    # Two gates each, not one: "in" carries the last-known-synced state (the reflective snapshot,
    # refreshed at the *start* of this turn — see the module docstring's "same-turn lag" note); "same_turn"
    # carries `check_member`'s own output from *this* firing, which write-back hasn't applied to
    # `self.asserted` yet when the reflective snapshot was taken. Without the second gate, `achieved`/
    # `diverged` see last member's result one turn late.
    achieved = StandingUnit("achieved", _ACHIEVED_PAT,
                             Attribute("g", "achieved", True), mutating=True, gates=("in", "same_turn"))
    diverged = StandingUnit("diverged", _DIVERGED_PAT,
                             Attribute("g", "diverged", True), mutating=True, gates=("in", "same_turn"))
    return check_member, achieved, diverged


def _run(member_names: tuple, eligibility: dict) -> list:
    """One member's result delivered per turn, in `member_names` order. Returns the (achieved, diverged)
    read after *every* turn, so the honest "not yet decided" middle turns are visible, not just the end."""
    g, goal, members = _build_goal(member_names)
    n = Network()
    n.given(g)
    check_member, achieved, diverged = _rules()
    n.add(check_member)
    n.add(achieved)
    n.add(diverged)

    reflect = n.axiom(*effects_of(n.asserted), name="reflect")
    n.wire(reflect, check_member)                    # fan-out: three consumers, one shared source
    n.wire(reflect, achieved, gate="in")
    n.wire(reflect, diverged, gate="in")
    n.wire(check_member.cell, achieved, gate="same_turn")   # this turn's own delta, same-turn visible
    n.wire(check_member.cell, diverged, gate="same_turn")

    trace = []
    for nm in member_names:
        n.asserted = n.asserted.with_node(members[nm], eligible=eligibility[nm])  # the "tool result"
        reflect.held = Value(effects_of(n.asserted))                              # refresh in place
        n.revive()
        trace.append({"member_just_checked": nm,
                       "achieved": n.world().attr(goal, "achieved"),
                       "diverged": n.world().attr(goal, "diverged")})
    return trace


def check_all_eligible_reaches_achieved_only_at_the_end() -> dict[str, object]:
    """Three members, all eligible. `achieved` must stay `None` through the middle turns — concluding it
    early would be exactly the false-completeness `model.md` §8 exists to prevent — and become `True`
    only once the third (last) member's result has arrived."""
    trace = _run(("m1", "m2", "m3"), {"m1": True, "m2": True, "m3": True})
    return {"trace": trace}


def check_one_ineligible_member_reaches_diverged_not_achieved() -> dict[str, object]:
    """Same shape, one member fails. `diverged` (not `achieved`) lands once every member is checked —
    the universal claim is honestly false, stated as a positive fact, not silently absent."""
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

"""APPLICATION-NODE PROBE — Probe B of `graph_data_model.md` §7, and the one that decides whether §6.3's
whole cascade is a small gap or an architectural one.

`the_data_model.md` ends by naming exactly one thing missing: **the system keeps no record of its own
reasoning steps.** Nothing anywhere says *this operation was applied, to this goal, at this moment.* Four
capabilities fail on that single absence — choosing among metarules (no candidate to point at), non-greedy
lookahead (nothing to hypothesise about), recording episodes, and learned metaprocedures. The claim under
test is that closing it needs **no engine work at all**: an application can be an ordinary minted node, and
everything else follows from rules that already exist in kind.

**Why this is not trivially true, and what would refute it.** It would be easy to mint a node called
"application" and declare victory — a log line in graph clothing. The probe is built to demand more than
that, and each check is chosen because a plausible design fails it:

1. **`check_application_is_matchable_by_an_ordinary_rule`** — a *generic* audit rule, which knows nothing
   about which operation was applied, matches any application and acts on it. If applications needed
   bespoke handling per operation they would be records, not citizens.
2. **`check_of_points_at_the_real_rule_node`** — the application's `of:` edge lands on the node
   `Network.add` describes for the `StandingUnit` itself (*"the unit AS DATA — homoiconicity"*,
   `engine.py:538`), NOT on a name string. This is the check that makes the whole thing homoiconic rather
   than a parallel logging vocabulary: an application points at the rule the way it points at the goal,
   both being ordinary nodes. If this fails, applications are metadata *about* the system rather than data
   *in* it, and `the_data_model.md`'s "same representation" claim does not extend to reasoning steps.
   Note the rule matches its OWN node in its own pattern to do this — the reflective axiom already carries
   it, since `add()` writes it into `asserted` like anything else.
3. **`check_two_applications_on_one_goal_are_distinguishable`** — two different operations applied to the
   same goal must yield two applications distinguishable by what they are applications *of*. Without this
   an episode is an unordered bag and nothing can be learned from it.
4. **`check_a_prospective_application_can_be_supposed`** — the lookahead case, and the sharpest one. An
   application that has NOT happened is penned in a supposition; a rule reasoning over applications must
   see it in-scope, and the real world must be untouched. This is what non-greedy selection needs: asking
   "what would follow if I applied this operation" before applying it. A design where applications are
   minted only as a side effect of really firing would fail this outright.

Re-runnable: `python -m units.application_node_probe_experiment`.
"""
from __future__ import annotations

from .engine import Attribute, Emit, Link, Network, StandingUnit, Value, effects_of
from .graph import EMPTY, named, role_edge
from .match import absent, atom, role

# Each operation matches its OWN describing node (`atom("r", name=…)`) alongside its ordinary trigger, so
# it can link the application it mints to the rule-as-data node rather than to a string. Nothing about
# this is privileged — a unit's node is in `asserted` like any other node (`engine.py:683`).
_DECOMPOSE_PAT = (atom("g", name="goal", out=(role("wants", atom()),)),
                   atom("r", name="decompose"),
                   absent(atom("g", out=(role("raised", atom()),))))

_ANNOTATE_PAT = (atom("g", name="goal", triaged=None, out=(role("wants", atom()),)),
                  atom("r", name="annotate"))

# The generic consumer: knows nothing about WHICH operation ran. If this matches, applications are
# ordinary citizens rather than per-operation records.
_AUDIT_PAT = (atom("app", name="application", audited=None,
                    out=(role("on", atom("g", name="goal")),)),)


def _decompose_rule() -> StandingUnit:
    return StandingUnit(
        "decompose", _DECOMPOSE_PAT,
        Emit("subgoal", as_="sg"), Link("g", "sg", role="raised"),
        Emit("application", as_="app"), Link("app", "r", role="of"), Link("app", "g", role="on"),
        mutating=True)


def _annotate_rule() -> StandingUnit:
    return StandingUnit(
        "annotate", _ANNOTATE_PAT,
        Attribute("g", "triaged", True),
        Emit("application", as_="app"), Link("app", "r", role="of"), Link("app", "g", role="on"),
        mutating=True)


def _audit_rule() -> StandingUnit:
    """Two gates, and the second one is load-bearing rather than decorative.

    ⚠ **Correction, found by this probe producing a FALSE GREEN.** The first version gave `audit` one gate
    and wired both the reflective axiom and the supposition to it. The check "did the consumer reason over
    the prospective application" then passed — but inspecting the cell showed both output targets were the
    two REAL applications, and the hypothetical had never matched at all. Two sources delivered to ONE gate
    do not compose; the later delivery replaces the earlier (`latched[gate]` is a single `Value`), so the
    reflective axiom simply overwrote the supposition. `goal_machinery.md` §4's "wire every source that's
    needed" is necessary but not sufficient — each source needs its OWN gate, or the wiring silently
    discards one. `view()` composes across gates, never within one."""
    return StandingUnit("audit", _AUDIT_PAT, Attribute("app", "audited", True),
                         gates=("in", "hyp"), mutating=True)


def rules() -> dict[str, StandingUnit]:
    return {"decompose": _decompose_rule(), "annotate": _annotate_rule(), "audit": _audit_rule()}


def _settle(n: Network, reflect) -> None:
    reflect.held = Value(effects_of(n.asserted))
    n.revive()


def _network():
    g = EMPTY
    g, goal = named(g, "goal")
    g, want = named(g, "ticket_resolved")
    g = role_edge(g, goal, "wants", want)
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


def _applications(n: Network) -> list:
    return [x for x in n.asserted.nodes if n.asserted.attr(x, "name") == "application"]


def _role_target(g, node, role_name: str):
    for r in g.out(node):
        if g.attr(r, "name") == role_name:
            targets = g.out(r)
            if targets:
                return targets[0]
    return None


def check_application_is_matchable_by_an_ordinary_rule() -> dict[str, object]:
    """A generic rule, ignorant of which operation ran, matches applications and acts on them."""
    n, reflect, goal, _ = _network()
    n.revive()
    _settle(n, reflect)            # applications minted last turn become visible to `audit`
    _settle(n, reflect)
    apps = _applications(n)
    return {"applications_minted": len(apps),
            "all_audited_by_the_generic_rule": bool(apps) and
                all(n.world().attr(a, "audited") for a in apps)}


def check_of_points_at_the_real_rule_node() -> dict[str, object]:
    """THE homoiconicity check. `of:` must land on the `StandingUnit`'s own describing node — the same
    node `add()` wrote — not on a name string. Compared by identity against `rule.node`."""
    n, reflect, goal, built = _network()
    n.revive()
    _settle(n, reflect)
    apps = _applications(n)
    of_targets = {a: _role_target(n.asserted, a, "of") for a in apps}
    real_rule_nodes = {r.node for r in built.values()}
    return {"applications": len(apps),
            "every_of_target_is_a_real_rule_node":
                bool(of_targets) and all(t in real_rule_nodes for t in of_targets.values()),
            "of_targets_named": sorted(str(n.asserted.attr(t, "name")) for t in of_targets.values()
                                        if t is not None)}


def check_two_applications_on_one_goal_are_distinguishable() -> dict[str, object]:
    """Two operations, one goal, two applications — distinguishable by what they are applications of.
    Without this an episode is an unordered bag."""
    n, reflect, goal, _ = _network()
    n.revive()
    _settle(n, reflect)
    apps = _applications(n)
    on_targets = {_role_target(n.asserted, a, "on") for a in apps}
    of_named = [n.asserted.attr(_role_target(n.asserted, a, "of"), "name") for a in apps]
    return {"applications": len(apps),
            "all_on_the_same_goal": on_targets == {goal},
            "distinct_operations": sorted(set(of_named)),
            "distinguishable": len(set(of_named)) == len(apps)}


def check_a_prospective_application_can_be_supposed() -> dict[str, object]:
    """LOOKAHEAD. Pen an application that has NOT happened into a supposition, wire it to the generic
    consumer, and confirm two things: the consumer reasons over it in-scope, and the real world never
    sees it. This is what choosing non-greedily requires."""
    n, reflect, goal, _ = _network()
    n.revive()
    _settle(n, reflect)
    real_apps_before = set(_applications(n))

    # A hypothetical application: minted in pencil, never asserted.
    hyp = n.suppose(*effects_of(_hypothetical_application(goal)), name="what_if")
    audit = next(u for u in n.units if u.name == "audit")
    n.wire(hyp, audit, "hyp")          # its OWN gate — see `_audit_rule`'s correction note
    n.revive()

    # ⚠ The confound this check exists to avoid: `audit` also has the two REAL applications on its other
    # gate, so a merely non-empty output would pass while proving nothing. The prospective application is
    # identified positively — a target that is NOT one of the real ones and is NOT in the store at all.
    out = audit.cell.held.effects if audit.cell.held else ()
    targets = {getattr(e, "target", None) for e in out} - {None}
    prospective = {t for t in targets if t not in real_apps_before and t not in n.asserted.nodes}
    real_apps_after = set(_applications(n))
    return {"audit_output_targets": len(targets),
            "of_which_are_real_applications": len(targets & real_apps_before),
            "reasoned_over_the_PROSPECTIVE_one": len(prospective) == 1,
            "world_unchanged": real_apps_before == real_apps_after,
            "hypothetical_never_asserted":
                not any(n.asserted.attr(x, "hypothetical") for x in n.asserted.nodes)}


def _hypothetical_application(goal):
    g = EMPTY
    g, app = named(g, "application", hypothetical=True)
    g = role_edge(g, app, "on", goal)
    return g


def report() -> str:
    lines = ["=== APPLICATION-NODE PROBE (Probe B) — is a reasoning step an ordinary citizen? ==="]
    lines.append(f"matchable by a generic rule: {check_application_is_matchable_by_an_ordinary_rule()}")
    lines.append(f"`of:` is the real rule node:  {check_of_points_at_the_real_rule_node()}")
    lines.append(f"two applications distinguish: {check_two_applications_on_one_goal_are_distinguishable()}")
    lines.append(f"prospective one can be supposed: {check_a_prospective_application_can_be_supposed()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())

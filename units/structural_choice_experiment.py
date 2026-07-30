"""STRUCTURAL CHOICE, LIVE — not STRIPS, not supposition-based search: a genuine choice among competing
KB-declared candidates, resolved by *actually committing* to the real graph, honestly detecting a
conflict, retracting, and trying the next declared alternative — entirely as `StandingUnit`s, zero Python
in the decision loop.

**Why not supposition-based exploration.** `planning_meta_concepts_arc.md` §1 already found that a rule
reading a supposition's output inherits that supposition's taint unconditionally (`powering()`'s backward
wire-walk) — so a rule structurally *cannot* explore several real hypothetical branches and then commit the
winner; only Python, which has no tunnel of its own, was ever shown able to do that crossing. Building the
metaprocedure in rules therefore means never needing that crossing at all, not routing around it.

**The trade this makes, deliberately.** Real STRIPS-style search tries a branch, and if it dead-ends
several steps later, backtracks through everything decided since. This does not do that — it does exactly
what `planning_meta_concepts_arc.md` §4 already committed this project to: commit to the best *available*
guess for real, and if it's wrong, notice *immediately* (the conflict is checked against declared data, not
discovered by executing further) and move to the next declared alternative. No search tree, no
undo-multiple-steps. That is a real limitation — a conflict only visible several steps downstream would not
be caught this way — named honestly, not hidden.

**The scenario.** A car needs a windshield (declared `flat`) and "a wiper" — an open requirement, not
naming which kit. Two wiper kits are declared in the KB, in an explicit preference chain (`first`, then
`fallback:` — the same kind of ordinary sequencing edge `goal_decomposition_experiment.py` already
validated for procedure steps, not a new construct): `wiper_kit_a` requires a `curved` windshield;
`wiper_kit_b`, its declared fallback, requires `flat`. Against a `flat` car, `kit_a` is a genuine, live
dead end — not filtered in advance, not explored under a hypothesis, actually tried, actually found
incompatible, actually excluded, actually recovered from.

Four small rules, each doing one job, each an ordinary mutating `StandingUnit`:

- **`try_first_rule`** — if nothing is being attempted yet, attempt the declared-first, not-yet-excluded
  candidate.
- **`reject_incompatible_rule`** — if the thing currently being attempted requires a windshield type that
  does not match the car's actual, declared type, exclude it. A real, permanent fact — not a retraction of
  the attempt (the attempt itself stays on record, honestly, as a rejected mention), consistent with
  `create-never-merge`.
- **`commit_matching_rule`** — if the thing currently being attempted *does* match, install it for real and
  mark the requirement achieved.
- **`try_fallback_rule`** — if the current attempt was excluded and it declares a fallback, attempt that
  fallback next.

Three checks, all against the real engine:

1. **The first, incompatible candidate is genuinely tried, and genuinely rejected** —
   `check_first_candidate_tried_and_rejected`.
2. **The fallback is tried next, matches, and is committed — the requirement is honestly achieved only
   once a real, compatible part is installed** — `check_fallback_tried_and_committed`.
3. **Honesty when nothing works**: with *no* compatible candidate declared at all, the requirement stays
   unachieved indefinitely, never silently guessed at — `check_stays_honestly_unresolved_when_nothing_
   fits`.

Re-runnable: `python -m units.structural_choice_experiment`.
"""
from __future__ import annotations

from .engine import Attribute, Link, Network, StandingUnit, Value, effects_of
from .graph import EMPTY, named, role_edge
from .match import AttrVar, absent, atom, role

TRY_FIRST_PAT = (
    atom("wn", name="wiper_needed", achieved=None),
    absent(atom("wn", out=(role("attempting", atom()),))),
    atom("cand", name="wiper_kit", first=True, excluded=None),
)

TRY_FALLBACK_PAT = (
    atom("wn", name="wiper_needed", achieved=None,
         out=(role("attempting", atom("prev", excluded=True,
                                       out=(role("fallback", atom("cand", excluded=None)),))),)),
)

REJECT_PAT = (
    atom("car", name="car", windshield_type=AttrVar("wt")),
    atom("wn", name="wiper_needed",
         out=(role("attempting", atom("cand", excluded=None)),)),
    absent(atom("cand", requires_windshield_type=AttrVar("wt"))),
)

COMMIT_PAT = (
    atom("car", name="car", windshield_type=AttrVar("wt")),
    atom("wn", name="wiper_needed", achieved=None,
         out=(role("attempting", atom("cand", requires_windshield_type=AttrVar("wt"))),)),
)


def _rules() -> dict[str, StandingUnit]:
    return {
        "try_first": StandingUnit("try_first", TRY_FIRST_PAT,
                                   Link("wn", "cand", role="attempting"), mutating=True),
        "try_fallback": StandingUnit("try_fallback", TRY_FALLBACK_PAT,
                                      Link("wn", "cand", role="attempting"), mutating=True),
        "reject_incompatible": StandingUnit("reject_incompatible", REJECT_PAT,
                                             Attribute("cand", "excluded", True), mutating=True),
        "commit_matching": StandingUnit("commit_matching", COMMIT_PAT,
                                         Attribute("cand", "installed", True),
                                         Attribute("wn", "achieved", True), mutating=True),
    }


def _settle(n: Network, reflect) -> None:
    reflect.held = Value(effects_of(n.asserted))
    n.revive()


def _network(g):
    n = Network()
    ax = n.given(g)
    rule_set = _rules()
    for r in rule_set.values():
        n.add(r)
    reflect = n.axiom(*effects_of(n.asserted), name="reflect")
    for r in rule_set.values():
        n.wire(reflect, r)
    ax.held = None
    return n, reflect


def _build(second_candidate_compatible: bool):
    g = EMPTY
    g, car = named(g, "car", windshield_type="flat")
    g, wn = named(g, "wiper_needed")
    g = role_edge(g, car, "wants", wn)
    g, kit_a = named(g, "wiper_kit", first=True, requires_windshield_type="curved")
    g, kit_b = named(g, "wiper_kit", requires_windshield_type=(
        "flat" if second_candidate_compatible else "curved"))
    g = role_edge(g, kit_a, "fallback", kit_b)
    return g, car, wn, kit_a, kit_b


def check_first_candidate_tried_and_rejected() -> dict[str, object]:
    g, car, wn, kit_a, kit_b = _build(second_candidate_compatible=True)
    n, reflect = _network(g)
    n.revive()
    attempted_first_turn = [d for r in n.asserted.out(wn) for d in n.asserted.out(r)]
    _settle(n, reflect)   # reject_incompatible sees kit_a's mismatch
    return {"kit_a_was_actually_attempted": kit_a in attempted_first_turn,
            "kit_a_rejected_not_merely_ignored": n.world().attr(kit_a, "excluded") is True}


def check_fallback_tried_and_committed() -> dict[str, object]:
    g, car, wn, kit_a, kit_b = _build(second_candidate_compatible=True)
    n, reflect = _network(g)
    n.revive()
    _settle(n, reflect)   # kit_a excluded
    _settle(n, reflect)   # try_fallback attempts kit_b
    _settle(n, reflect)   # commit_matching sees kit_b matches

    attempted = [d for r in n.asserted.out(wn) for d in n.asserted.out(r)]
    return {"kit_b_was_attempted_after_kit_a_excluded": kit_b in attempted,
            "kit_b_installed": n.world().attr(kit_b, "installed") is True,
            "requirement_achieved": n.world().attr(wn, "achieved") is True}


def check_stays_honestly_unresolved_when_nothing_fits() -> dict[str, object]:
    g, car, wn, kit_a, kit_b = _build(second_candidate_compatible=False)
    n, reflect = _network(g)
    n.revive()
    achieved_per_idle_turn = []
    for _ in range(4):
        _settle(n, reflect)
        achieved_per_idle_turn.append(n.world().attr(wn, "achieved"))
    return {"kit_a_excluded": n.world().attr(kit_a, "excluded") is True,
            "kit_b_excluded_too": n.world().attr(kit_b, "excluded") is True,
            "never_silently_achieved": achieved_per_idle_turn == [None, None, None, None]}


def report() -> str:
    lines = ["=== STRUCTURAL CHOICE, LIVE: commit, detect, retract, retry the next declared alternative —",
             "    zero Python, zero supposition ==="]
    lines.append(f"first candidate genuinely tried and rejected: "
                 f"{check_first_candidate_tried_and_rejected()}")
    lines.append(f"fallback tried and committed: {check_fallback_tried_and_committed()}")
    lines.append(f"honest when nothing fits: {check_stays_honestly_unresolved_when_nothing_fits()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())

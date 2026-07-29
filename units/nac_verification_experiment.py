"""NAC VERIFICATION EXPERIMENT — does "actively push a subgoal to find out, before trusting a NAC"
need new engine machinery, or is it an authoring pattern over what already exists?

Two concepts, same graph, same engine, deliberately different stances:

- `mild` (default, not flagged): a bare NAC concludes `assumed_safe` the instant nothing contradicts
  it — cheap, immediate, exactly today's closed-world-assumption default.
- `hazmat` (flagged `actively_verify=True`, a plain stance fact on the KIND node — no new fact
  *kind*, just a fact): absence of `dangerous` is never trusted at all. Instead, a rule fires that
  raises a subgoal (`goal_machinery.md`'s own shape) wanting the real answer, and only that
  subgoal's own `achieved`/`diverged` — genuine evidence, not an assumption — ever concludes anything
  about the chemical. There is no `assumed_safe` path for a flagged concept; there's only "still
  pending" or "confirmed," never a defeasible guess in between.

**The finding: no new engine primitive was needed.** The "generator" is not a meta-rule that inspects
another rule's `<absent>` node and rewrites it (the heavier mechanism sketched in conversation, itself
buildable — `units/engine.py:151-197` shows `Absent` is already fully homoiconic data, so it wasn't
ruled out, just not needed here). It's simpler: the investigate rule's pattern just includes the stance
fact as an ordinary **positive** premise (`out=(role("kind", atom("k", actively_verify=True)))`), so it
naturally only fires for flagged concepts — the same way any other guard restricts a rule. "Configurable
per concept" is just which fact happens to be true of a given kind node; nothing about matching, wiring,
or write-back needed to change. What's new is a *pattern to author rules by*, not a capability the
engine lacked.

**How this composes with everything already built:** the investigate rule reuses
`goal_experiment.py`'s exact subgoal shape (`Emit("subgoal", ...)`, `Link(..., role="wants")`); the
resolution reuses `achieved`/`diverged` verbatim (`goal_machinery.md` §2's positive-fact discipline —
never an absence read directly). The only genuinely new piece is the *shape of the contrast*: for a
flagged concept, `achieved`/`diverged` themselves become the terminal facts (`confirmed_safe` /
`confirmed_dangerous`) — there's no separate "assumed" step downstream of them, because once real
evidence exists, an assumption would be strictly weaker than what's already known.

Re-runnable: `python -m units.nac_verification_experiment`.
"""
from __future__ import annotations

from .engine import Attribute, Emit, Link, Network, StandingUnit, Value, effects_of
from .graph import EMPTY, named, role_edge
from .match import absent, atom, role

_ASSUMED_SAFE_PAT = (atom("x", name="chemical", assumed_safe=None,
                           out=(role("kind", atom("k", actively_verify=None)),)),
                      absent(atom("x", dangerous=True)))

_INVESTIGATE_PAT = (atom("x", name="chemical", investigated=None,
                          out=(role("kind", atom("k", actively_verify=True)),)),)

_SUBGOAL_ACHIEVED_PAT = (atom("sg", name="subgoal", achieved=None,
                               out=(role("wants", atom("c", true=True)),)),)
_SUBGOAL_DIVERGED_PAT = (atom("sg", name="subgoal", diverged=None,
                               out=(role("wants", atom("c", true=False)),)),)

_CONFIRMED_SAFE_PAT = (atom("x", name="chemical",
                             out=(role("raised", atom("sg", achieved=True)),)),)
_CONFIRMED_DANGEROUS_PAT = (atom("x", name="chemical",
                                  out=(role("raised", atom("sg", diverged=True)),)),)


def _rules() -> dict[str, StandingUnit]:
    return {
        "assumed_safe": StandingUnit("assumed_safe", _ASSUMED_SAFE_PAT,
                                      Attribute("x", "assumed_safe", True), mutating=True),
        "investigate": StandingUnit(
            "investigate", _INVESTIGATE_PAT,
            Emit("subgoal", as_="sg"), Emit("danger_check", as_="c"),
            Link("sg", "c", role="wants"), Link("x", "sg", role="raised"),
            Attribute("x", "investigated", True), mutating=True),
        "sub_achieved": StandingUnit("sub_achieved", _SUBGOAL_ACHIEVED_PAT,
                                      Attribute("sg", "achieved", True), mutating=True),
        "sub_diverged": StandingUnit("sub_diverged", _SUBGOAL_DIVERGED_PAT,
                                      Attribute("sg", "diverged", True), mutating=True),
        "confirmed_safe": StandingUnit("confirmed_safe", _CONFIRMED_SAFE_PAT,
                                        Attribute("x", "confirmed_safe", True), mutating=True),
        "confirmed_dangerous": StandingUnit("confirmed_dangerous", _CONFIRMED_DANGEROUS_PAT,
                                             Attribute("x", "confirmed_dangerous", True), mutating=True),
    }


def _find(g, name: str):
    return next(n for n in g.nodes if g.attrs.get(n, {}).get("name") == name)


def _build():
    g = EMPTY
    g, hazmat = named(g, "hazmat", actively_verify=True)   # the stance fact: an ordinary attribute
    g, mild = named(g, "mild")                              # no stance fact at all -> default CWA
    g, chem_a = named(g, "chemical")
    g = role_edge(g, chem_a, "kind", hazmat)
    g, chem_b = named(g, "chemical")
    g = role_edge(g, chem_b, "kind", mild)
    return g, chem_a, chem_b


def _read(n: Network, chem) -> dict[str, object]:
    return {"assumed_safe": n.world().attr(chem, "assumed_safe"),
            "confirmed_safe": n.world().attr(chem, "confirmed_safe"),
            "confirmed_dangerous": n.world().attr(chem, "confirmed_dangerous")}


def _settle(n: Network, reflect) -> None:
    reflect.held = Value(effects_of(n.asserted))
    n.revive()


def _network():
    g, chem_a, chem_b = _build()
    n = Network()
    n.given(g)
    rules = _rules()
    for r in rules.values():
        n.add(r)
    reflect = n.axiom(*effects_of(n.asserted), name="reflect")
    for r in rules.values():
        n.wire(reflect, r)
    return n, reflect, chem_a, chem_b


def check_default_concept_gets_immediate_assumed_safe() -> dict[str, object]:
    """`mild` has no stance fact at all — the bare NAC fires on the very first revive, exactly today's
    closed-world default. No subgoal, no investigation, cheapest possible path."""
    n, reflect, chem_a, chem_b = _network()
    n.revive()
    return _read(n, chem_b)


def check_flagged_concept_never_assumes_before_investigating() -> dict[str, object]:
    """`hazmat` never gets `assumed_safe` at all — not on the first revive, not ever. The only rule
    that can conclude anything about it is downstream of the subgoal's own real resolution."""
    n, reflect, chem_a, chem_b = _network()
    n.revive()
    _settle(n, reflect)
    return _read(n, chem_a)


def check_flagged_concept_confirmed_safe_after_investigation() -> dict[str, object]:
    """The investigation resolves positively (`danger_check.true=True`) -> `confirmed_safe`, a hard
    fact backed by evidence, never `assumed_safe`."""
    n, reflect, chem_a, chem_b = _network()
    n.revive()
    _settle(n, reflect)
    c = _find(n.asserted, "danger_check")
    n.asserted = n.asserted.with_node(c, true=True)
    _settle(n, reflect)
    _settle(n, reflect)   # one settle to see the subgoal's own achieved, one more for confirmed_safe
    return _read(n, chem_a)


def check_flagged_concept_confirmed_dangerous_after_investigation() -> dict[str, object]:
    """The investigation resolves negatively (`danger_check.true=False`) -> `confirmed_dangerous`, not
    a silent absence and not an assumption either way."""
    n, reflect, chem_a, chem_b = _network()
    n.revive()
    _settle(n, reflect)
    c = _find(n.asserted, "danger_check")
    n.asserted = n.asserted.with_node(c, true=False)
    _settle(n, reflect)
    _settle(n, reflect)
    return _read(n, chem_a)


def report() -> str:
    lines = ["=== NAC VERIFICATION EXPERIMENT: default assumption vs. actively-verified concepts ==="]
    lines.append(f"default concept (mild) -> immediate assumed_safe: "
                 f"{check_default_concept_gets_immediate_assumed_safe()}")
    lines.append(f"flagged concept (hazmat) -> never assumed, stays pending: "
                 f"{check_flagged_concept_never_assumes_before_investigating()}")
    lines.append(f"flagged concept, investigation confirms safe: "
                 f"{check_flagged_concept_confirmed_safe_after_investigation()}")
    lines.append(f"flagged concept, investigation confirms dangerous: "
                 f"{check_flagged_concept_confirmed_dangerous_after_investigation()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())

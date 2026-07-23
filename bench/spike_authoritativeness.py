"""AUTHORITATIVENESS PROBE — reified attributed advice + a priority order + a meta-preference, resolved by
authority, ALL AS DATA + RULES (no Python policy). And the payoff test: the SAME authority mechanism composes
with the flare/governor, because everything lives on the one substrate.

Scenario (user, 2026-07-23):
  "John says: when alarm, do evacuate"   (advice a1: source john, trigger alarm, action evacuate)
  "Jack says: when alarm, do shelter"    (advice a2: source jack, trigger alarm, action shelter)
  "Jack is more important than John"      (jack more_important_than john)
  "better to follow the most important"   (the meta-rule, below)
  -> the system does SHELTER (Jack's), not evacuate (John's).

The meta-preference is DEFEASIBLE OVERRIDE via NAF: an action is chosen if some applicable advice advises it
and there is NO applicable advice from a MORE IMPORTANT source (which would beat it). Reified advice (data) +
`more_important_than` (a comparative fact) + a NAF guard (a rule) — nothing hardcoded, so it composes.
"""
from __future__ import annotations

import warnings

from ugm import AttrGraph
from ugm.cnl.machine_rules import load_machine_rules
from ugm.cnl.query import ask_goal

warnings.simplefilter("ignore")

# The meta-reasoning bank — reads REIFIED advice, lifts source-importance to advice-precedence, and chooses
# the action that no more-important applicable advice overrides. Pure data-driven; no rule names a source.
GOVERN = "\n".join([
    "?d applicable yes when ?d trigger ?t and ?t active yes",
    "?e beats ?d when ?e source ?se and ?d source ?sd and ?se more_important_than ?sd",
    "?d overridden yes when ?e applicable yes and ?e beats ?d",
    "?a chosen yes when ?d applicable yes and ?d action ?a and not ?d overridden yes",
])


def _advice_kb(authority):
    """Build the world as DATA: the situation, two reified attributed advices, and the authority fact."""
    kb = AttrGraph()
    def n(x):
        got = kb.nodes_named(x)
        return got[0] if got else kb.add_node(x)
    def fact(s, p, o):
        kb.add_relation(n(s), p, n(o))
    fact("alarm", "active", "yes")                                  # the situation holds
    for adv, src, act in [("a1", "john", "evacuate"), ("a2", "jack", "shelter")]:
        fact(adv, "trigger", "alarm"); fact(adv, "source", src); fact(adv, "action", act)
    fact(authority[0], "more_important_than", authority[1])         # <-- the ONLY thing that changes
    return kb


def _chosen(kb, rules):
    return sorted(a.split(" ")[0] for a in ask_goal(kb, "who chosen yes", rules) if a != "(no answer)")


def check_A_authority_decides_the_action():
    rules = load_machine_rules(GOVERN)
    jack_first = _chosen(_advice_kb(("jack", "john")), rules)       # Jack more important
    john_first = _chosen(_advice_kb(("john", "jack")), rules)       # FLIP the authority fact (data only)
    ok = jack_first == ["shelter"] and john_first == ["evacuate"]
    print(f"  A authority decides the action   -> {ok}")
    print(f"      jack>john -> {jack_first}   (want [shelter], NOT evacuate)")
    print(f"      john>jack -> {john_first}   (want [evacuate], flipped by DATA alone, no code change)")
    return ok


def check_B_composes_with_the_flare_recovery():
    # THE COMPOSITION PAYOFF: the SAME authority mechanism chooses a RECOVERY for a flare. A flare is just a
    # fact (`unresolved`), advice about how to recover is reified data, authority breaks the tie — so two
    # mechanisms (flare + authoritativeness) combine with ZERO new machinery, only shared substrate.
    rules = load_machine_rules("\n".join([
        # the flare is the trigger (modelled directly as the active situation here):
        "?d applicable yes when ?d trigger ?t and ?t active yes",
        "?e beats ?d when ?e source ?se and ?d source ?sd and ?se more_important_than ?sd",
        "?d overridden yes when ?e applicable yes and ?e beats ?d",
        "?r recover yes when ?d applicable yes and ?d action ?r and not ?d overridden yes",
    ]))
    kb = AttrGraph()
    def n(x):
        got = kb.nodes_named(x); return got[0] if got else kb.add_node(x)
    def fact(s, p, o): kb.add_relation(n(s), p, n(o))
    fact("stuck_goal", "active", "yes")                            # a goal has flared (the situation)
    for adv, src, act in [("r_john", "john", "retry"), ("r_jack", "jack", "abandon")]:
        fact(adv, "trigger", "stuck_goal"); fact(adv, "source", src); fact(adv, "action", act)
    fact("jack", "more_important_than", "john")
    recovery = sorted(a.split(" ")[0] for a in ask_goal(kb, "who recover yes", rules) if a != "(no answer)")
    ok = recovery == ["abandon"]                                   # Jack (more important) says abandon -> so
    print(f"  B composes with flare recovery   -> {ok}  (chosen recovery = {recovery}, want [abandon])")
    return ok


if __name__ == "__main__":
    a = check_A_authority_decides_the_action()
    b = check_B_composes_with_the_flare_recovery()
    print("=" * 66)
    print(f"AUTHORITATIVENESS: {'GO — reified advice + priority + NAF override, all data+rules, composable'
                                if (a and b) else 'GAP'}")

"""REACTIVE-FRAME PROBE (STEP C.2, 2026-07-23) — do the two reaction halves fire into the STEP-A frame?

STEP A made `_facts_matching` canonical (union a bound endpoint over its `denotes`-class) + guarded (exclude
control/inert scaffolding). STEP C.2 asks whether a REACTION reasons over that frame, so it cannot fire on a
token or scaffolding. Three checks against a REAL token/entity dual-store (a `denotes` split, both "wolf"):

  A. DERIVE on a TOKEN-resident trigger -> consequence materialized, readable under the ENTITY's identity.
  B. RETRACT: the `_positive_now` recheck sees a token-resident breaker (across the split) and withdraws.
  C. GUARD: a scaffolding (control) node carrying a content edge is NOT reacted upon.

RESULT (2026-07-23) — GO, by construction (no new code): every belief-read routes through the canonical +
guarded `_facts_matching`/`chain_sip`, and grains/assumption-goals are name-keyed (name-union). Locked by
`tests/test_reactive.py::test_{derive_fires_on_a_token_resident_trigger,retract_sees_a_token_resident_breaker,
no_reaction_fires_on_control_scaffolding}`.
"""
from __future__ import annotations

import ugm as h
from ugm import AttrGraph
from ugm.vocabulary import DENOTES
from ugm.cnl.authoring import run_rules
from ugm.lowering import load_fact_triples
from ugm.cnl.machine_rules import load_machine_rules
from ugm.cnl.query import ask_goal
from ugm.reconsider import mark_dirty, reconsider
from ugm.reactive import declare_reactive
from ugm.chain import _facts_matching

RULE = "?x endangers ?y when ?x hunts ?y"


def _mat(kb, p, s, o):
    return bool(_facts_matching(kb, p, s, o))


def check_A_derive_token_trigger():
    kb = AttrGraph()
    ent, tok, sheep = kb.add_node("wolf"), kb.add_node("wolf"), kb.add_node("sheep")
    kb.add_relation(tok, DENOTES, ent)              # token --denotes--> entity
    kb.add_relation(tok, "hunts", sheep)            # TRIGGER authored on the TOKEN
    rules = load_machine_rules(RULE)
    declare_reactive(kb, "endangers")
    mark_dirty(kb, [("hunts", "sheep")])
    assert not _mat(kb, "endangers", "wolf", "sheep")
    ask_goal(kb, ("yesno", "wolf", "hunts", "sheep"), rules)   # committed act fires the gate
    got = _mat(kb, "endangers", "wolf", "sheep")
    print(f"  A derive(token-trigger)  endangers materialized under entity name -> {got}")
    return got


def check_B_retract_token_makes_absent_derivable():
    R_end = h.Rule(key="endangers.hunts", lhs=[h.Pat("?x", "hunts", "?y")],
                   rhs=[h.Pat("?x", "endangers", "?y")])
    R_safe = h.Rule(key="safe.near", lhs=[h.Pat("?x", "near", "?y")],
                    nac=[h.Pat("?x", "endangers", "?y")], rhs=[h.Pat("?x", "safe", "?y")])
    g = h.Graph()
    ent, tok = g.add_node("wolf"), g.add_node("wolf")
    g.add_relation(tok, DENOTES, ent)
    load_fact_triples(g, [("wolf", "near", "sheep")])
    run_rules(g, [R_end, R_safe], provenance=True)
    assert _mat(g, "safe", "wolf", "sheep"), "forward NAF derivation should materialize `safe`"
    g.add_relation(tok, "hunts", g.nodes_named("sheep")[0])    # TOKEN-resident breaker
    mark_dirty(g, [("hunts", "sheep")])
    n = reconsider(g, [R_end, R_safe])
    withdrawn = (n == 1) and not _mat(g, "safe", "wolf", "sheep")
    print(f"  B retract(token-makes-derivable)  stale `safe` withdrawn -> {withdrawn} (n={n})")
    return withdrawn


def check_C_guard_no_react_on_scaffolding():
    kb = AttrGraph()
    ghost, sheep = kb.add_node("ghost", control=True), kb.add_node("sheep")
    kb.add_relation(ghost, "hunts", sheep)
    rules = load_machine_rules(RULE)
    declare_reactive(kb, "endangers")
    mark_dirty(kb, [("hunts", "sheep")])
    ask_goal(kb, ("yesno", "sheep", "is", "sheep"), rules)
    ok = not _mat(kb, "endangers", "ghost", "sheep")
    print(f"  C guard(no-react-on-scaffolding)  endangers NOT on ghost -> {ok}")
    return ok


def main():
    a = check_A_derive_token_trigger()
    b = check_B_retract_token_makes_absent_derivable()
    c = check_C_guard_no_react_on_scaffolding()
    print("=" * 60)
    print(f"VERDICT: {'GO - both halves fire into the STEP-A frame' if (a and b and c) else 'GAP FOUND'}")


if __name__ == "__main__":
    main()

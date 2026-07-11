"""
Regression harness for the coverage / composition audit (bench/coverage_audit.py) — the top open
experiment from docs/handoff_redesign.md, testing docs/vision_agentic.md §6/§12: does a small set of
MECHANISM-level rules COMPOSE to cover real bugs, or does the absent-premise long tail dominate (the
Cyc-shaped risk)? These tests pin the audit's headline findings so a rule/engine change can't silently
move them, and they assert the two claims the audit exists to make: composition WORKS (novel
manifestations of an encoded mechanism are caught with no dedicated rule, near-misses stay silent), and
the miss tail is REAL and splits cleanly into cheap (composable-but-unencoded) vs fundamental
(absent-premise).

They also lock two silent-failure FINDINGS surfaced while building the audit, so the fix (or the
regression) is visible:
  1. the machine-rule body parser SILENTLY DROPS a body clause whose predicate is a reserved
     provenance name (`uses`) — same family as the `is a X` rule-head silent-drop already in the
     handoff's NL-surface gaps;
  2. a provenance predicate-concept node (`proves`) spuriously inherits a derived type when provenance
     is on — invisible to the public `ask` surface, but a raw hazard scan must exclude it.
"""
import ugm as h
from ugm.cnl.machine_rules import load_machine_rules

from bench import coverage_audit as ca


# --- the rule bank is well-formed -------------------------------------------



# --- the audit is well-formed: the engine behaves as every scenario predicts -



# --- headline metric 1: composition works (§6) ------------------------------







# --- headline metric 2: the miss tail is real and splits cleanly (§12) -------



# --- headline metric 3: the premise-class import generalizes and beats baseline (the experiment) ---









# --- finding 1: reserved provenance predicate silently drops a body clause ---

def test_finding_reserved_predicate_silently_dropped_from_body():
    # FIXED (Phase 2.1/2.2): `uses` is a provenance predicate (h.USES), and the machine-rule body
    # parser USED to drop the clause `?u uses ?r` without error, collapsing the rule to its first
    # clause (which is why the audit's access frame historically used `accesses`, not `uses`).
    # Removing name-based predicate reservation (predicates became graded KEYS) made the drop go
    # away as a side effect. Pin the FIXED behavior: the provenance-named clause is now RETAINED.
    rule = load_machine_rules("?u is_a hazard when ?u is_a access and ?u uses ?r "
                              "and ?rel releases ?r and ?rel happens_before ?u")[0]
    clauses = {p.tokens() for p in rule.lhs}
    assert ("?u", "uses", "?r") in clauses            # the provenance-named clause survives
    # the non-colliding vocabulary the audit actually uses keeps all four body clauses:
    ok = load_machine_rules("?u is_a hazard when ?u is_a access and ?u accesses ?r "
                            "and ?rel releases ?r and ?rel happens_before ?u")[0]
    ok_clauses = {p.tokens() for p in ok.lhs}
    assert ("?u", "accesses", "?r") in ok_clauses
    assert ("?rel", "releases", "?r") in ok_clauses
    assert ("?rel", "happens_before", "?u") in ok_clauses


# --- finding 2: provenance node leaks a derived type; scan must exclude it ---

def test_finding_provenance_node_excluded_from_hazard_scan():
    g = h.Graph()
    ca.iteration(g, "loop1", "qs")
    ca.mutation(g, "mut1", "qs", "loop1")
    h.run_rules(g, ca.RULES)
    # The `proves` predicate-concept node spuriously carries `is_a hazard` after a derivation, but the
    # measured hazard set is exactly the domain node — provenance vocabulary is filtered out.
    assert ca._hazards(g) == {"mut1"}
    assert h.PROVES not in ca._hazards(g)

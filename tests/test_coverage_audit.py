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
import ugm as hh
import ugm as h
from ugm.cnl.machine_rules import load_machine_rules

from bench import coverage_audit as ca


# --- the rule bank is well-formed -------------------------------------------

def test_mechanism_bank_is_lint_clean_and_stratifies():
    assert hh.lint_rules(ca.RULES) == [], hh.format_smells(hh.lint_rules(ca.RULES))
    h.stratify(ca.RULES)                              # composes without a negation cycle
    # 2 closure + 8 mechanism + 2 cheap-fix + 3 taint-premise + 5 concurrency-premise rules, all
    # machine-rule CNL (DATA).
    assert len(ca.RULES) == 20
    assert len(ca.MECHANISM_GLOSS) == 8
    assert len(ca.CHEAP_GLOSS) == 2 and len(ca.TAINT_GLOSS) == 3
    assert len(ca.CONCURRENCY_GLOSS) == 5


# --- the audit is well-formed: the engine behaves as every scenario predicts -

def test_no_engine_vs_prediction_mismatch():
    # Each scenario's category encodes a PREDICTION about engine behavior (positive->caught,
    # near-miss->silent, miss->present-but-uncaught). If any diverges, the audit's model of the
    # engine is wrong and every downstream number is suspect.
    _, m = ca.measure()
    assert m["mismatches"] == []


# --- headline metric 1: composition works (§6) ------------------------------

def test_encoded_mechanism_recall_is_total_including_novel_manifestations():
    _, m = ca.measure()
    # Every direct positive AND every NOVEL manifestation (recursion-as-iteration, mutation-through-
    # alias, nested-loop containment, mutable-default recognizer, the two now-encoded cheap fixes, the
    # taint family, and the concurrency family) is caught with NO scenario-specific rule.
    assert m["encoded_recall"] == 1.0
    assert m["n_encoded_pos"] == 16


def test_novel_manifestations_are_caught_with_no_dedicated_rule():
    # The §6 claim, scenario by scenario: these are not enumerated patterns — each falls out of the
    # SAME mechanism rules composing over a differently-shaped frame graph.
    rows = {s["name"]: r for s, r, _ in ca.measure()[0]}
    for novel in ("mdi_recursion", "mdi_via_alias", "mdi_nested_loop",
                  "leak_on_exception_path", "use_after_release_via_alias",
                  "taint_command_injection", "taint_path_traversal_multihop",
                  "race_read_write", "race_distinct_locks"):
        assert rows[novel]["caught"], novel


def test_near_misses_stay_silent_no_over_generation():
    # Compositional rules OVER-generate before they under-generate; the 8 adversarial near-misses
    # prove the recall above was not bought with false positives.
    _, m = ca.measure()
    assert m["false_positives"] == []
    assert m["n_near"] == 13


# --- headline metric 2: the miss tail is real and splits cleanly (§12) -------

def test_miss_taxonomy_splits_cheap_vs_fundamental():
    _, m = ca.measure()
    # Overall real-bug recall is deliberately BELOW 100% — the honest coverage number. After both cheap
    # misses were encoded and taint AND concurrency were imported, the residual is exactly the ONE
    # still-UNIMPORTED premise class (arithmetic/bounds) — not an open-ended pattern tail.
    assert m["real_recall"] < 1.0
    assert set(m["cheap_misses"]) == set()                       # both cheap misses now encoded
    assert set(m["fundamental_misses"]) == {"off_by_one_index"}
    # 16 of 17 real bugs caught; the 1 residual is an absent premise CLASS, closable by import.
    assert round(m["real_recall"] * m["n_buggy"]) == 16
    assert m["n_buggy"] == 17


# --- headline metric 3: the premise-class import generalizes and beats baseline (the experiment) ---

def test_premise_class_import_beats_baseline():
    _, m = ca.measure()
    # The original 8 mechanism rules catch 8/17 on this expanded suite; the 2 cheap rules + the taint
    # class + the concurrency class lift it to 16/17. The exact set that flipped miss->caught is the
    # experiment's payload.
    assert round(m["baseline_real_recall"] * m["n_buggy"]) == 8
    assert set(m["newly_caught_vs_baseline"]) == {
        "leak_on_exception_path", "use_after_release_via_alias",
        "taint_sql_injection", "taint_command_injection", "taint_path_traversal_multihop",
        "race_condition_shared_state", "race_read_write", "race_distinct_locks"}


def test_concurrency_premise_class_isolated_delta():
    _, m = ca.measure()
    # The concurrency import measured in ISOLATION (prior = mechanism+cheap+taint): 13/17 -> 16/17, the
    # direct analog of taint's 53.3%->86.7%. Only the three concurrency bugs flip, and nothing else
    # regresses — the class is additive, not a global re-tune.
    assert round(m["pre_concurrency_real_recall"] * m["n_buggy"]) == 13
    assert set(m["newly_caught_vs_pre_concurrency"]) == {
        "race_condition_shared_state", "race_read_write", "race_distinct_locks"}


def test_taint_premise_class_is_kind_agnostic_and_sanitizer_discriminates():
    # The load-bearing claim: ONE kind-agnostic taint bank catches structurally-distinct sinks with no
    # per-pattern rule — a DIFFERENT sink kind (command) and MULTI-HOP dataflow, not just the direct SQL
    # it was written against — and the sanitizer NAC keeps the sanitized flow silent. Generality
    # without over-generation, exactly as the native mechanisms behaved (§6).
    rows = {s["name"]: r for s, r, _ in ca.measure()[0]}
    for caught in ("taint_sql_injection", "taint_command_injection", "taint_path_traversal_multihop"):
        assert rows[caught]["caught"] and not rows[caught]["false_pos"], caught
    for silent in ("taint_sanitized", "taint_untainted_sink"):
        assert not rows[silent]["actual"], silent


def test_concurrency_premise_class_is_kind_agnostic_and_lock_discriminates():
    # The same load-bearing claim for the concurrency class: ONE kind-agnostic bank catches
    # structurally-distinct races with no per-pattern rule — a READ/WRITE conflict (via the kind-
    # agnostic `touches`, not just the write-write it was written against) and a DISTINCT-LOCK race
    # (the guard NAC demands a *shared* lock, not merely some lock) — while the discriminating near-
    # misses stay silent: a COMMON lock serializes the access, ORDERED writes are not concurrent, and
    # DISJOINT state shares no object. Generality without over-generation, exactly as taint behaved.
    rows = {s["name"]: r for s, r, _ in ca.measure()[0]}
    for caught in ("race_condition_shared_state", "race_read_write", "race_distinct_locks"):
        assert rows[caught]["caught"] and not rows[caught]["false_pos"], caught
    for silent in ("race_common_lock", "race_not_concurrent", "race_disjoint_state"):
        assert not rows[silent]["actual"], silent


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

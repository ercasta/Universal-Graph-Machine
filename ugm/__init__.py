"""Universal Graph Machine — label-less attribute graph substrate with ISA engine and CNL surface."""
from importlib import import_module
import sys

from .world_model import Graph, Node, WorldModel
from .production_rule import Pat, Rule, GradedCondition
from .attrgraph import AttrGraph, AttrNode, Attr, GRADED, VALUED
from .machine import (
    Machine, State, run_program,
    SEED, FOLLOW, JOIN, TEST, GRADE, FUZZY, MINT, EMIT, DROP_CTRL, SET, DUP, SAME,
    INTERPOSE, RESTORE,
    Instr, ControlEdgeError, ProgramError, SchemaError,
    T_MIN, T_PROD,
)
from .lowering import (
    to_attrgraph, lower_conj, lower_lhs, lower_graded, lower_rhs,
    lower_propagate, lower_drop, lower_rewire,
    lower_rule, lower_nac_programs, run_bank, match_pats, run_to_fixpoint,
    derived_triples, Unlowerable, rule_touches_provenance,
)
from .goal import Goal, GoalSolver, solve_goal, solve_all, NonStratifiable
from .solve import derive_plan, Plan, run_to_goal, DEFAULT_TOOLS
from .apply import apply_rule, apply_to_fixpoint, build_head_index, rules_producing
from .chain import (
    chain, demand_closure, relevant_rules, demanded_preds,
    chain_sip, bound_demands, render_demands,
)
from .check import (
    check, collapse, explain_check,
    POSITIVE, ENTAILED_NEG, ASSUMED_NO, UNKNOWN,
)
from .choose import (
    choose, set_candidate, candidates, winners_of, fit_of, explain_choice, SATISFIED_BY,
)
from .suppose import (
    suppose, explain_suppose, scope_members, SupposeResult,
    CONFIRMED, REFUTED, INCONCLUSIVE, HYPOTHESIS,
)
from .walker import Walker, WalkResult, walk_to_goal
from .cnl.rewriter import (
    run, match, match_with_premises, delta_matches,
    nac_blocks, graded_degree, Firing, Rewriter, near_rules,
)
from .provenance import (
    PROVES, USES, AXIOM, j_name, is_justification, rule_of_j,
    support_js, rule_support_j, premises_of, proven_of, justifications_using,
    derived_facts, axiomatize,
)
from .retraction import (
    RETRACT, TARGETS, RETRACTED, RETRACT_RULES, seed_retract, retract,
    record_rejection, is_rejected,
)
from .demand import DEMAND, seed_demand, DEMAND_TRANSITIVITY, DEMAND_COREF
from .decide import (
    CWA, COPULA, NEG_COPULA,
    declare_closed_world, is_closed_world, closed_predicates,
    positive_holds, negative_holds, completion_rule, DEFEAT_SEED,
)
from .dispatch import (
    CALL, TOOL, Tool, emit_call, call_tool, call_arg, call_args, pending_calls, consume_call,
    service_calls,
)
from .coref_walk import resolve_coref, coref_request_handler
from .mode_calls import (
    check_tool, choose_tool, mode_registry, service_modes, check_results, choice_results,
    CHECK_TOOL, CHOOSE_TOOL, CHECK_RESULT, STATUS,
)
from .cnl.forms import (
    tokenize, load_text, canonicalize, FORM_RULES, relation_forms, declared_relations,
    expand_universals, wire_same_as, coref_in_context, relation_predicates, propagate_embeddings,
    nary_forms, declared_verbs, declared_prepositions, nary_question_forms, WH,
    form_keywords, declared_determiners, DEFAULT_DETERMINERS, DEFAULT_ARTICLES,
    declared_pronouns, declared_definites, DEFAULT_PRONOUNS, subject_name, surface_forms, normalize_surface,
    expand_pronouns_text, SURFACE_TAGS,
    declared_rule_variables, declared_auxiliaries, declared_univ_nouns, rule_var_name,
)
from .cnl.universal import UNIVERSAL_RULES, SAME_AS_RULES, entailed_negation_rules, same_as_rules
from .cnl.rule_graph import (
    write_rule, rules_in_graph, ROLE_NAMES,
    expand_relation_properties, RELATION_PROPERTY_FORMS, PROPERTY_REL,
    DISJOINT_FORMS, CONSTRAINT_FORMS, DISJOINT_REL, CONTRADICTION,
    contradictions, is_consistent,
)
from .cnl.authoring import (
    FACT_FORMS, GRADED_RULES, load_facts,
    DEGREE_CNL, degree_thresholds, graded_rules, degree_grammar_forms,
    RULE_FORMS, IF_THEN_FORMS, PLURAL_UNIVERSAL_FORMS, plural_universal_forms, verb_neg_forms,
    expand_rules, load_rules, load_universal_rules, stratify, run_rules,
    TRANSLATION_FORMS, parse_lexicon, expand_loose, load_loose_rules,
    LEXICON_FORMS, RULE_SOURCE_FORMS, BODY_SPINE_FORMS, _ALL_FORMS,
    frames_in_graph, expand_loose_from_graph, load_corpus,
)
from .cnl.surface import render_relation, narrate, explain
from .cnl.query import QUESTION_FORMS, ask, ask_goal, recognize
from .cnl.machine_rules import MACHINE_RULE_FORMS, load_machine_rules
from .cnl.walker import (
    WALKER, WALK_REQUEST, REACHED, FUEL, ORIGIN, TARGET, REFUEL, AMOUNT,
    spawn_walker, walk_rules, DEMAND_WALK, SPAWN_RULES, walk_on_demand,
    refuel_tool, WALK_TOOLS, load_walker_rules,
)
from . import external, provenance, retraction, decide, dispatch, coref_walk, asp
from .cnl import rewriter, forms, surface, authoring, universal, machine_rules, query, rule_graph
from .external import (
    ARG, request, pending, consume_request,
    emit_result, emit_error, results_for, result_value, is_superseded,
    lookup_handler, request_hub,
)


def _alias(name: str, target: str) -> None:
    module = import_module(target)
    sys.modules[f"{__name__}.{name}"] = module
    globals()[name] = module


for _name, _target in {
    "rewriter": "ugm.cnl.rewriter",
    "forms": "ugm.cnl.forms",
    "surface": "ugm.cnl.surface",
    "authoring": "ugm.cnl.authoring",
    "universal": "ugm.cnl.universal",
    "machine_rules": "ugm.cnl.machine_rules",
    "query": "ugm.cnl.query",
    "rule_graph": "ugm.cnl.rule_graph",
}.items():
    _alias(_name, _target)



def __getattr__(name: str):
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Graph", "Node", "WorldModel",
    "Pat", "Rule", "GradedCondition",
    "AttrGraph", "AttrNode", "Attr", "GRADED", "VALUED",
    "Machine", "State", "run_program",
    "SEED", "FOLLOW", "JOIN", "TEST", "GRADE", "FUZZY", "MINT", "EMIT",
    "DROP_CTRL", "SET", "DUP", "SAME", "INTERPOSE", "RESTORE",
    "Instr", "ControlEdgeError", "ProgramError", "SchemaError", "T_MIN", "T_PROD",
    "to_attrgraph", "lower_conj", "lower_lhs", "lower_graded", "lower_rhs",
    "lower_propagate", "lower_drop", "lower_rewire", "lower_rule", "lower_nac_programs",
    "run_bank", "match_pats", "run_to_fixpoint", "derived_triples", "Unlowerable",
    "rule_touches_provenance",
    "Goal", "GoalSolver", "solve_goal", "solve_all", "NonStratifiable",
    "derive_plan", "Plan", "run_to_goal", "DEFAULT_TOOLS",
    "apply_rule", "apply_to_fixpoint", "build_head_index", "rules_producing",
    "chain", "demand_closure", "relevant_rules", "demanded_preds", "chain_sip", "bound_demands",
    "render_demands",
    "check", "collapse", "explain_check", "POSITIVE", "ENTAILED_NEG", "ASSUMED_NO", "UNKNOWN",
    "choose", "set_candidate", "candidates", "winners_of", "fit_of", "explain_choice", "SATISFIED_BY",
    "suppose", "explain_suppose", "scope_members", "SupposeResult",
    "CONFIRMED", "REFUTED", "INCONCLUSIVE", "HYPOTHESIS",
    "Walker", "WalkResult", "walk_to_goal",
    "run", "match", "match_with_premises", "delta_matches", "nac_blocks", "graded_degree",
    "Firing", "Rewriter", "near_rules",
    "PROVES", "USES", "AXIOM", "j_name", "is_justification", "rule_of_j",
    "support_js", "rule_support_j", "premises_of", "proven_of", "justifications_using",
    "derived_facts", "axiomatize",
    "RETRACT", "TARGETS", "RETRACTED", "RETRACT_RULES", "seed_retract", "retract",
    "record_rejection", "is_rejected",
    "DEMAND", "seed_demand", "DEMAND_TRANSITIVITY", "DEMAND_COREF",
    "CWA", "COPULA", "NEG_COPULA", "declare_closed_world", "is_closed_world", "closed_predicates",
    "positive_holds", "negative_holds", "completion_rule", "DEFEAT_SEED",
    "CALL", "TOOL", "Tool", "emit_call", "call_tool", "call_arg", "call_args", "pending_calls",
    "consume_call", "service_calls",
    "resolve_coref", "coref_request_handler",
    "check_tool", "choose_tool", "mode_registry", "service_modes", "check_results", "choice_results",
    "CHECK_TOOL", "CHOOSE_TOOL", "CHECK_RESULT", "STATUS",
    "tokenize", "load_text", "canonicalize", "FORM_RULES", "relation_forms", "declared_relations",
    "expand_universals", "wire_same_as", "coref_in_context", "relation_predicates", "propagate_embeddings",
    "nary_forms", "declared_verbs", "declared_prepositions", "nary_question_forms", "WH",
    "form_keywords", "declared_determiners", "DEFAULT_DETERMINERS", "DEFAULT_ARTICLES",
    "declared_pronouns", "declared_definites", "DEFAULT_PRONOUNS", "subject_name", "surface_forms",
    "normalize_surface", "expand_pronouns_text", "SURFACE_TAGS",
    "declared_rule_variables", "declared_auxiliaries", "declared_univ_nouns", "rule_var_name",
    "UNIVERSAL_RULES", "SAME_AS_RULES", "entailed_negation_rules", "same_as_rules",
    "write_rule", "rules_in_graph", "ROLE_NAMES", "expand_relation_properties",
    "RELATION_PROPERTY_FORMS", "PROPERTY_REL", "DISJOINT_FORMS", "CONSTRAINT_FORMS",
    "DISJOINT_REL", "CONTRADICTION", "contradictions", "is_consistent",
    "FACT_FORMS", "GRADED_RULES", "load_facts", "DEGREE_CNL", "degree_thresholds", "graded_rules",
    "degree_grammar_forms", "RULE_FORMS", "IF_THEN_FORMS", "PLURAL_UNIVERSAL_FORMS",
    "plural_universal_forms", "verb_neg_forms", "expand_rules", "load_rules", "load_universal_rules",
    "stratify", "run_rules", "TRANSLATION_FORMS", "parse_lexicon", "expand_loose", "load_loose_rules",
    "LEXICON_FORMS", "RULE_SOURCE_FORMS", "BODY_SPINE_FORMS", "_ALL_FORMS",
    "frames_in_graph", "expand_loose_from_graph", "load_corpus",
    "render_relation", "narrate", "explain",
    "QUESTION_FORMS", "ask", "ask_goal", "recognize",
    "MACHINE_RULE_FORMS", "load_machine_rules",
    "WALKER", "WALK_REQUEST", "REACHED", "FUEL", "ORIGIN", "TARGET", "REFUEL", "AMOUNT",
    "spawn_walker", "walk_rules", "DEMAND_WALK", "SPAWN_RULES", "walk_on_demand",
    "refuel_tool", "WALK_TOOLS", "load_walker_rules",
    "external", "provenance", "retraction", "decide", "dispatch", "coref_walk", "asp",
    "rewriter", "forms", "surface", "authoring", "universal", "machine_rules", "query", "rule_graph",
    "ARG", "request", "pending", "consume_request",
    "emit_result", "emit_error", "results_for", "result_value", "is_superseded",
    "lookup_handler", "request_hub",
]

"""Universal Graph Machine — label-less attribute graph substrate with ISA engine and CNL surface."""
from importlib import import_module
import sys

from .vocabulary import (
    COPULA, NEG_COPULA, NEG_SUFFIX, IS_A, IS_A_NOT, SAME_AS, DISJOINT,
    CLOSES, CWA, REL_PROPERTY, TRANSITIVE, EVERY_IS_A, IS_UNIQUE, TARGET, TYPE,
    SUBSTRATE_COREF_PREDS, neg_pred, is_neg_pred,
)
from .world_model import Graph, Node, WorldModel
from .production_rule import Pat, Rule, GradedCondition, ValueMatch
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
from .apply import apply_rule, apply_to_fixpoint, build_head_index, rules_producing
from .chain import (
    chain, demand_closure, relevant_rules, demanded_preds,
    chain_sip, bound_demands, render_demands, NonStratifiable,
    ById, resolve_write_node, validate_ids,
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
from .provenance import (
    PROVES, USES, AXIOM, j_name, is_justification, rule_of_j,
    support_js, rule_support_j, premises_of, proven_of, justifications_using,
    derived_facts, axiomatize,
)
from .retraction import (
    RETRACT, TARGETS, RETRACTED, RETRACT_RULES, seed_retract, retract,
    record_rejection, is_rejected,
)
from .dispatch import (
    CALL, TOOL, Tool, emit_call, call_tool, call_arg, call_args, pending_calls, consume_call,
    service_calls, merge_tools,
)
from .policy import FirmwarePolicy, DEFAULT_POLICY
from .mode_calls import (
    check_tool, choose_tool, suppose_tool, mode_registry, service_modes,
    check_results, choice_results, suppose_results,
    CHECK_TOOL, CHOOSE_TOOL, SUPPOSE_TOOL, CHECK_RESULT, SUPPOSE_RESULT, STATUS,
    ASSUME, PREDICT, LABEL, K_SUBJ, K_PRED, K_OBJ,
)
from .cnl.forms import (
    tokenize, load_text, FORM_RULES, relation_forms, declared_relations,
    expand_universals, mark_mentions, relation_predicates, propagate_embeddings,
    nary_forms, declared_verbs, declared_prepositions, nary_question_forms, WH,
    form_keywords, declared_determiners, DEFAULT_DETERMINERS, DEFAULT_ARTICLES,
    declared_pronouns, declared_definites, DEFAULT_PRONOUNS, subject_name, surface_forms, normalize_surface,
    expand_pronouns_text, SURFACE_TAGS,
    declared_rule_variables, declared_auxiliaries, declared_univ_nouns, rule_var_name,
)
from .cnl.universal import (UNIVERSAL_RULES, SAME_AS_RULES, entailed_negation_rules, same_as_rules,
                            same_name_coref_rules)
from .cnl.rule_graph import (
    write_rule, rules_in_graph, ROLE_NAMES,
    expand_relation_properties, RELATION_PROPERTY_FORMS, PROPERTY_REL,
    DISJOINT_FORMS, CONSTRAINT_FORMS, DISJOINT_REL, CONTRADICTION,
    contradictions, is_consistent,
)
from .cnl.authoring import (
    FACT_FORMS, GRADED_RULES, load_facts, anchor_has_content_fact,
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
from .intake import ingest, converse, Outcome, Event
from . import external, provenance, retraction, dispatch
from . import intake, focus, rule_control
from .cnl import forms, surface, authoring, universal, machine_rules, query, rule_graph
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
    "Pat", "Rule", "GradedCondition", "ValueMatch",
    "AttrGraph", "AttrNode", "Attr", "GRADED", "VALUED",
    "Machine", "State", "run_program",
    "SEED", "FOLLOW", "JOIN", "TEST", "GRADE", "FUZZY", "MINT", "EMIT",
    "DROP_CTRL", "SET", "DUP", "SAME", "INTERPOSE", "RESTORE",
    "Instr", "ControlEdgeError", "ProgramError", "SchemaError", "T_MIN", "T_PROD",
    "to_attrgraph", "lower_conj", "lower_lhs", "lower_graded", "lower_rhs",
    "lower_propagate", "lower_drop", "lower_rewire", "lower_rule", "lower_nac_programs",
    "run_bank", "match_pats", "run_to_fixpoint", "derived_triples", "Unlowerable",
    "rule_touches_provenance",
    "apply_rule", "apply_to_fixpoint", "build_head_index", "rules_producing",
    "chain", "demand_closure", "relevant_rules", "demanded_preds", "chain_sip", "bound_demands",
    "NonStratifiable",
    "render_demands", "ById", "resolve_write_node", "validate_ids",
    "check", "collapse", "explain_check", "POSITIVE", "ENTAILED_NEG", "ASSUMED_NO", "UNKNOWN",
    "choose", "set_candidate", "candidates", "winners_of", "fit_of", "explain_choice", "SATISFIED_BY",
    "suppose", "explain_suppose", "scope_members", "SupposeResult",
    "CONFIRMED", "REFUTED", "INCONCLUSIVE", "HYPOTHESIS",
    "PROVES", "USES", "AXIOM", "j_name", "is_justification", "rule_of_j",
    "support_js", "rule_support_j", "premises_of", "proven_of", "justifications_using",
    "derived_facts", "axiomatize",
    "RETRACT", "TARGETS", "RETRACTED", "RETRACT_RULES", "seed_retract", "retract",
    "record_rejection", "is_rejected",
    "CWA", "COPULA", "NEG_COPULA", "NEG_SUFFIX", "IS_A", "IS_A_NOT", "SAME_AS", "DISJOINT",
    "CLOSES", "REL_PROPERTY", "TRANSITIVE", "EVERY_IS_A", "IS_UNIQUE", "TARGET", "TYPE",
    "SUBSTRATE_COREF_PREDS", "neg_pred", "is_neg_pred",
    "CALL", "TOOL", "Tool", "emit_call", "call_tool", "call_arg", "call_args", "pending_calls",
    "consume_call", "service_calls", "merge_tools",
    "FirmwarePolicy", "DEFAULT_POLICY",
    "ingest", "converse", "Outcome", "Event", "intake", "focus", "rule_control",
    "check_tool", "choose_tool", "suppose_tool", "mode_registry", "service_modes",
    "check_results", "choice_results", "suppose_results",
    "CHECK_TOOL", "CHOOSE_TOOL", "SUPPOSE_TOOL", "CHECK_RESULT", "SUPPOSE_RESULT", "STATUS",
    "ASSUME", "PREDICT", "LABEL", "K_SUBJ", "K_PRED", "K_OBJ",
    "tokenize", "load_text", "FORM_RULES", "relation_forms", "declared_relations",
    "expand_universals", "mark_mentions", "relation_predicates", "propagate_embeddings",
    "nary_forms", "declared_verbs", "declared_prepositions", "nary_question_forms", "WH",
    "form_keywords", "declared_determiners", "DEFAULT_DETERMINERS", "DEFAULT_ARTICLES",
    "declared_pronouns", "declared_definites", "DEFAULT_PRONOUNS", "subject_name", "surface_forms",
    "normalize_surface", "expand_pronouns_text", "SURFACE_TAGS",
    "declared_rule_variables", "declared_auxiliaries", "declared_univ_nouns", "rule_var_name",
    "UNIVERSAL_RULES", "SAME_AS_RULES", "entailed_negation_rules", "same_as_rules",
    "same_name_coref_rules",
    "write_rule", "rules_in_graph", "ROLE_NAMES", "expand_relation_properties",
    "RELATION_PROPERTY_FORMS", "PROPERTY_REL", "DISJOINT_FORMS", "CONSTRAINT_FORMS",
    "DISJOINT_REL", "CONTRADICTION", "contradictions", "is_consistent",
    "FACT_FORMS", "GRADED_RULES", "load_facts", "anchor_has_content_fact",
    "DEGREE_CNL", "degree_thresholds", "graded_rules",
    "degree_grammar_forms", "RULE_FORMS", "IF_THEN_FORMS", "PLURAL_UNIVERSAL_FORMS",
    "plural_universal_forms", "verb_neg_forms", "expand_rules", "load_rules", "load_universal_rules",
    "stratify", "run_rules", "TRANSLATION_FORMS", "parse_lexicon", "expand_loose", "load_loose_rules",
    "LEXICON_FORMS", "RULE_SOURCE_FORMS", "BODY_SPINE_FORMS", "_ALL_FORMS",
    "frames_in_graph", "expand_loose_from_graph", "load_corpus",
    "render_relation", "narrate", "explain",
    "QUESTION_FORMS", "ask", "ask_goal", "recognize",
    "MACHINE_RULE_FORMS", "load_machine_rules",
    "external", "provenance", "retraction", "dispatch",
    "forms", "surface", "authoring", "universal", "machine_rules", "query", "rule_graph",
    "ARG", "request", "pending", "consume_request",
    "emit_result", "emit_error", "results_for", "result_value", "is_superseded",
    "lookup_handler", "request_hub",
]

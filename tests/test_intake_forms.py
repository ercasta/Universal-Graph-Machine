"""Phase 9 Slice B — form authoring through intake + KB-file loading.

The FORM route (routed by the header form firing, §D.2), RHS-structure bank placement (D3:
question forms join recognition/answering, declarative forms join fact recognition),
nearest-forms/disable coverage of authored forms, key-conflict as conversation, and `load_kb`
(the multi-KB-file model with strict declare-before-use). Design:
docs/design/form_authoring_design.md §2/§3/§5 Slice B.
"""
import pytest

from ugm.intake import ingest, load_kb
from ugm.cnl.authoring import load_corpus


RULES = """
?x is watched when ?x is a suspect
"""

# A new yes/no question surface over is_a: `whether S is a O` (no shipped form covers it).
WHETHER = ("form ask.whether.is_a : "
           "<query>? qtype yesno and <query>? q_s ?qs and <query>? q_p is_a and <query>? q_o ?qo "
           "when ?s first whether? and whether? next ?qs and ?qs next is? and is? next a? "
           "and a? next ?qo")

# A new DECLARATIVE surface: `X likes Y` (undeclared verbs don't parse without it).
LIKES = ("form fact.likes : ?x likes ?y "
         "when ?s first ?x and ?x next likes? and likes? next ?y")


def _fresh():
    return load_corpus(RULES)


# ---------------------------------------------------------------------------
# The FORM route
# ---------------------------------------------------------------------------

def test_form_utterance_routes_to_form():
    kb, rules = _fresh()
    out = ingest(kb, rules, WHETHER)
    assert out.kind == "form"
    assert [r.key for r in out.added_rules] == ["ask.whether.is_a"]


def test_unknown_shape_unrecognized_before_declaration():
    kb, rules = _fresh()
    ingest(kb, rules, "bo is a suspect")
    out = ingest(kb, rules, "whether bo is a suspect")
    assert out.kind == "unrecognized"


# ---------------------------------------------------------------------------
# D3 placement — question form joins recognition/answering
# ---------------------------------------------------------------------------

def test_authored_question_form_answers_end_to_end():
    kb, rules = _fresh()
    ingest(kb, rules, "bo is a suspect")
    ingest(kb, rules, WHETHER)
    out = ingest(kb, rules, "whether bo is a suspect")
    assert out.kind == "answer"
    assert out.answer == ["yes"]
    # ... and it reasons (rule-derived goal), not just reads ink
    out2 = ingest(kb, rules, "is bo watched")
    assert out2.answer == ["yes"]


# ---------------------------------------------------------------------------
# D3 placement — declarative form joins fact recognition
# ---------------------------------------------------------------------------

def test_authored_declarative_form_lands_facts():
    kb, rules = _fresh()
    assert ingest(kb, rules, "alice likes bob").kind == "unrecognized"   # before: no verb
    ingest(kb, rules, LIKES)
    out = ingest(kb, rules, "alice likes bob")
    assert out.kind == "fact"
    ans = ingest(kb, rules, "who likes bob")          # the generic shipped who-form reads it back
    assert ans.answer == ["alice likes bob"]


# ---------------------------------------------------------------------------
# Habitability + disable coverage
# ---------------------------------------------------------------------------

def test_nearest_forms_include_authored_shapes():
    kb, rules = _fresh()
    ingest(kb, rules, WHETHER)
    out = ingest(kb, rules, "whether bo suspect nonsense trailing words")
    assert out.kind == "unrecognized"
    assert any("whether" in tpl for tpl in out.nearest)


def test_disable_that_rule_covers_the_authored_form():
    kb, rules = _fresh()
    ingest(kb, rules, "bo is a suspect")
    ingest(kb, rules, WHETHER)
    out = ingest(kb, rules, "disable that rule")
    assert out.kind == "rule-disable"
    assert out.disabled_keys == ["ask.whether.is_a"]
    assert ingest(kb, rules, "whether bo is a suspect").kind == "unrecognized"


# ---------------------------------------------------------------------------
# Key semantics at intake — idempotent redeclare, conflict as conversation
# ---------------------------------------------------------------------------

def test_identical_redeclaration_is_idempotent():
    kb, rules = _fresh()
    ingest(kb, rules, "bo is a suspect")
    ingest(kb, rules, WHETHER)
    out = ingest(kb, rules, WHETHER)                  # normal under multi-file loading
    assert out.kind == "form"
    assert ingest(kb, rules, "whether bo is a suspect").answer == ["yes"]


def test_key_conflict_rejected_by_default():
    kb, rules = _fresh()
    ingest(kb, rules, "bo is a suspect")
    ingest(kb, rules, WHETHER)
    conflicting = WHETHER.replace("whether?", "izit?")   # same key, different keyword
    out = ingest(kb, rules, conflicting)                 # no on_conflict handler => reject
    assert out.kind == "form" and out.added_rules == []
    assert ingest(kb, rules, "whether bo is a suspect").answer == ["yes"]   # original stands
    assert ingest(kb, rules, "izit bo is a suspect").kind == "unrecognized"


def test_key_conflict_accepted_replaces():
    kb, rules = _fresh()
    ingest(kb, rules, "bo is a suspect")
    ingest(kb, rules, WHETHER)
    conflicting = WHETHER.replace("whether?", "izit?")
    out = ingest(kb, rules, conflicting, on_conflict=lambda detail: True)
    assert out.kind == "form" and out.added_rules
    assert ingest(kb, rules, "izit bo is a suspect").answer == ["yes"]      # new definition wins
    assert ingest(kb, rules, "whether bo is a suspect").kind == "unrecognized"


# ---------------------------------------------------------------------------
# load_kb — the multi-KB-file model, declare-before-use
# ---------------------------------------------------------------------------

KB_FILE = f"""
# a KB file: facts, a rule, a grammar extension, all through the one route
bo is a suspect
?x is risky when ?x is a suspect
{WHETHER}
{LIKES}
alice likes bob
"""


def test_load_kb_loads_in_order_and_grammar_extends():
    kb, rules = _fresh()
    outs = load_kb(kb, rules, KB_FILE)
    assert [o.kind for o in outs] == ["fact", "rule", "form", "form", "fact"]
    assert ingest(kb, rules, "whether bo is a suspect").answer == ["yes"]
    assert ingest(kb, rules, "is bo risky").answer == ["yes"]
    assert ingest(kb, rules, "who likes bob").answer == ["alice likes bob"]


def test_load_kb_declare_before_use_is_loud():
    kb, rules = _fresh()
    out_of_order = "alice likes bob\n" + LIKES        # use before declaration
    with pytest.raises(ValueError, match="declare-before-use"):
        load_kb(kb, rules, out_of_order)


def test_load_kb_conflict_is_loud():
    kb, rules = _fresh()
    conflicting = WHETHER.replace("whether?", "izit?")
    with pytest.raises(ValueError, match="conflict"):
        load_kb(kb, rules, WHETHER + "\n" + conflicting)


def test_load_kb_reload_of_forms_is_idempotent():
    kb, rules = _fresh()
    load_kb(kb, rules, WHETHER)
    load_kb(kb, rules, WHETHER)                       # loading the same file again is fine
    ingest(kb, rules, "bo is a suspect")
    assert ingest(kb, rules, "whether bo is a suspect").answer == ["yes"]

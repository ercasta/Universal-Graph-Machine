"""Phase 9 Slice A — form authoring: `form KEY : HEAD when BODY` (form_authoring.py).

A recognition form authored in rule-source CNL, carrying a stable key, linted to read only the
token chain, with idempotent/loud key-merge semantics — and immediately usable through the
EXISTING `extra_forms=` hook (`recognize`/`ask`), proving the capability with zero new plumbing.
Design: docs/design/form_authoring_design.md §2/§3/§5.
"""
import pytest

from ugm import load_forms, merge_forms, lint_recognition_safe, load_machine_rules
from ugm.cnl.query import ask, recognize
from ugm.production_rule import Pat, Rule
from ugm.world_model import Graph


# A new yes/no interrogative surface (`whether S P O`) — not covered by any shipped form.
WHETHER = ("form ask.whether : "
           "<query>? qtype yesno and <query>? q_s ?qs and <query>? q_p ?qp and <query>? q_o ?qo "
           "when ?s first whether? and whether? next ?qs and ?qs next ?qp and ?qp next ?qo")

# A new wh surface (`whom P O` — subject unknown), mirroring `ask.who`.
WHOM = ("form ask.whom : "
        "<query>? qtype who and <query>? q_p ?qp and <query>? q_o ?qo "
        "when ?s first whom? and whom? next ?qp and ?qp next ?qo")


def _kb() -> Graph:
    g = Graph()
    a, b = g.add_node("alice"), g.add_node("bob")
    g.add_relation(a, "likes", b)
    return g


# ---------------------------------------------------------------------------
# The naming surface + key round-trip
# ---------------------------------------------------------------------------

def test_authored_key_round_trips():
    (rule,) = load_forms(WHETHER)
    assert rule.key == "ask.whether"
    # the folded shape is the real question-form shape: chain LHS, <query> RHS
    assert Pat("?s", "first", "whether?") in rule.lhs
    assert Pat("?qs", "next", "?qp") in rule.lhs
    assert Pat("<query>?", "qtype", "yesno") in rule.rhs
    assert Pat("<query>?", "q_s", "?qs") in rule.rhs


def test_line_without_header_is_loud():
    # a plain machine rule (no `form KEY :`) must not slip in as a digest-keyed form
    with pytest.raises(ValueError, match="form KEY"):
        load_forms("?x reachable <yes> when ?x at ?p")


def test_unseparated_colon_is_loud():
    # `form KEY: …` (colon glued to the key) is not the header — loud, never silent
    with pytest.raises(ValueError):
        load_forms(WHETHER.replace("ask.whether :", "ask.whether:"))


# ---------------------------------------------------------------------------
# End-to-end through the EXISTING extra_forms hook — the capability itself
# ---------------------------------------------------------------------------

def test_authored_yesno_form_answers():
    forms = load_forms(WHETHER)
    g = _kb()
    q = recognize("whether alice likes bob", extra_forms=forms)
    assert q == {"qtype": "yesno", "s": "alice", "p": "likes", "o": "bob"}
    assert ask(g, "whether alice likes bob", extra_forms=forms) == ["yes"]
    assert ask(g, "whether bob likes alice", extra_forms=forms) == ["no"]


def test_authored_wh_form_answers():
    forms = load_forms(WHOM)
    g = _kb()
    assert ask(g, "whom likes bob", extra_forms=forms) == ["alice likes bob"]


def test_shipped_grammar_still_wins_on_its_own_shapes():
    # authored forms EXTEND recognition; the shipped shapes are untouched
    forms = load_forms(WHETHER)
    g = _kb()
    assert ask(g, "who likes bob", extra_forms=forms) == ["alice likes bob"]


# ---------------------------------------------------------------------------
# The recognition-safety lint
# ---------------------------------------------------------------------------

def test_lint_rejects_fact_reading_condition():
    bad = ("form bad.spy : <query>? qtype yesno and <query>? q_s ?qs "
           "when ?s first snoop? and snoop? next ?qs and ?qs likes ?qo")
    with pytest.raises(ValueError, match="likes"):
        load_forms(bad)


def test_lint_rejects_variable_predicate_condition():
    bad = ("form bad.free : <query>? qtype yesno and <query>? q_s ?qs "
           "when ?s first snoop? and ?qs ?p ?qo")
    with pytest.raises(ValueError, match="VARIABLE predicate"):
        load_forms(bad)


def test_lint_is_importable_for_slice_b():
    # the lint is a standalone gate the intake route (Slice B) will call on live-authored forms
    ok = Rule(key="k", lhs=[Pat("?s", "first", "x?")], rhs=[Pat("<query>?", "qtype", "yesno")])
    lint_recognition_safe([ok])
    bad = Rule(key="k", lhs=[Pat("?a", "owns", "?b")], rhs=[Pat("<query>?", "qtype", "yesno")])
    with pytest.raises(ValueError, match="owns"):
        lint_recognition_safe([bad])


# ---------------------------------------------------------------------------
# Key-merge semantics (D5) — idempotent on identity, loud on conflict
# ---------------------------------------------------------------------------

def test_redeclaring_identical_form_is_idempotent():
    first = load_forms(WHETHER)
    merged = merge_forms(first, load_forms(WHETHER))
    assert [r.key for r in merged] == ["ask.whether"]


def test_same_key_different_rule_is_a_conflict():
    other = load_forms(WHETHER.replace("whether?", "if?"))   # same key, different keyword
    with pytest.raises(ValueError, match="ask.whether"):
        merge_forms(load_forms(WHETHER), other)


def test_conflict_within_one_text_is_loud():
    two = WHETHER + "\n" + WHETHER.replace("whether?", "if?")
    with pytest.raises(ValueError, match="ask.whether"):
        load_forms(two)


def test_duplicate_within_one_text_folds_to_one():
    merged = load_forms(WHETHER + "\n" + WHETHER)
    assert [r.key for r in merged] == ["ask.whether"]


# ---------------------------------------------------------------------------
# The machine grammar is unchanged outside `load_forms`
# ---------------------------------------------------------------------------

def test_machine_rules_unaffected_by_header_nac():
    # the mrule.start NAC is inert where the header stratum never ran — including a rule whose
    # leading subject happens to be named `form`
    (r,) = load_machine_rules("form has_field ?f when ?f is_a field and ?f of form")
    assert any(p == Pat("form", "has_field", "?f") for p in r.rhs)

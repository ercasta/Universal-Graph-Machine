"""Phase 8.1 — unified intake routing (docs/design/cnl_intake_design.md §1, §D).

One entry `ingest(kb, rules, utterance)`; the route EMERGES from which forms fire, not a string sniff.
"""
import pytest

from ugm.intake import ingest
from ugm.world_model import Graph


RULES = """
?x is innocent when ?x in library
?x is cleared when ?x is innocent
?x is thief when ?x is a suspect and ?x is not cleared
"""


def _fresh():
    from ugm.cnl.authoring import load_corpus
    return load_corpus(RULES)          # (kb, rules)


def test_assertion_routes_to_fact():
    kb, rules = _fresh()
    out = ingest(kb, rules, "bo is a suspect")
    assert out.kind == "fact"


def test_question_routes_to_answer():
    kb, rules = _fresh()
    ingest(kb, rules, "bo is a suspect")
    out = ingest(kb, rules, "is bo thief")
    assert out.kind == "answer"
    assert out.answer == ["yes"]       # bo is a suspect, not cleared -> thief


def test_question_negative():
    kb, rules = _fresh()
    ingest(kb, rules, "bo is a suspect")
    ingest(kb, rules, "bo in library")     # -> innocent -> cleared
    out = ingest(kb, rules, "is bo thief")
    assert out.kind == "answer"
    assert out.answer == ["no (assumed)"]


def test_rule_routes_to_rule_and_reasons_immediately():
    kb, rules = _fresh()
    ingest(kb, rules, "ada is a suspect")
    # a rule supplied mid-session must drive reasoning right away
    out = ingest(kb, rules, "?x is watched when ?x is a suspect")
    assert out.kind == "rule"
    assert out.added_rules
    ans = ingest(kb, rules, "is ada watched")
    assert ans.answer == ["yes"]


# --- 8.6: runtime rule authoring — conflict-lint AS CONVERSATION (design §6) ----------------------

CYCLE_BASE = "?x is q when ?x is not p"          # a lone rule; adding p<-not q closes a negation cycle
CYCLE_NEW = "?x is p when ?x is not q"


def test_conflicting_rule_rejected_by_default():
    # No conflict handler wired: a cycle-forming rule is REJECTED (not raised, not admitted).
    from ugm.cnl.authoring import load_corpus
    kb, rules = load_corpus(CYCLE_BASE)
    before = len(rules)
    out = ingest(kb, rules, CYCLE_NEW)
    assert out.kind == "rule"
    assert out.added_rules == []                 # discarded
    assert len(rules) == before                  # theory untouched — the trial list never mutated `rules`


def test_conflicting_rule_accepted_on_verdict():
    from ugm.cnl.authoring import load_corpus
    kb, rules = load_corpus(CYCLE_BASE)
    before = len(rules)
    seen = []
    out = ingest(kb, rules, CYCLE_NEW, on_conflict=lambda detail: seen.append(detail) or True)
    assert seen                                  # the cycle detail was surfaced to the handler
    assert out.added_rules                       # accepted despite the cycle (run_rules will degrade)
    assert len(rules) == before + len(out.added_rules)   # committed to the live theory


def test_clean_rule_does_not_conflict_ask():
    # A well-formed, non-cyclic mid-session rule adds with NO rule-conflict event.
    from ugm.cnl.authoring import load_corpus
    kb, rules = load_corpus(CYCLE_BASE)
    ev = []
    out = ingest(kb, rules, "?x is watched when ?x is a suspect", on_event=ev.append)
    assert out.added_rules
    assert [e.kind for e in ev] == ["rule"]      # no "rule-conflict"


# --- 8.6: runtime rule authoring — DISABLE via `<disabled>` marker (design §6) --------------------

def test_forget_that_rule_disables_last_rule():
    from ugm.cnl.authoring import load_corpus
    kb, rules = load_corpus("")
    ingest(kb, rules, "ada is a suspect")
    ingest(kb, rules, "?x is watched when ?x is a suspect")     # a rule derives `watched`
    assert ingest(kb, rules, "is ada watched").answer == ["yes"]   # control: the rule fires

    ingest(kb, rules, "bo is a suspect")                        # a FRESH subject, never queried yet
    out = ingest(kb, rules, "forget that rule")                 # the §6 disable move
    assert out.kind == "rule-disable"
    assert out.disabled_keys                                    # the last-added rule key was marked
    # the disabled rule no longer fires for a NOT-yet-derived subject -> CWA-default no. (Monotone: `ada
    # watched`, materialized by the earlier query, persists — disable stops future derivations, §5 no
    # retraction.) The rule OBJECT still lives in `rules`; only the `<disabled>` marker excludes it.
    assert ingest(kb, rules, "is bo watched").answer == ["no (assumed)"]


def test_forget_that_rule_is_not_focus_drop():
    # `forget that` (focus) and `forget that rule` (disable) are distinct FORMS — the trailing token routes.
    from ugm.cnl.authoring import load_corpus
    kb, rules = load_corpus("")
    ingest(kb, rules, "ada is happy")
    assert ingest(kb, rules, "forget that").kind == "focus"     # focus drop, not rule-disable

    ev = []
    ingest(kb, rules, "forget that rule", on_event=ev.append)
    assert [e.kind for e in ev] == ["rule-disable"]


def test_the_disable_and_focus_forms_are_mutually_exclusive():
    """⭐ THE RECOGNIZERS DISAGREE ON STRUCTURE, so intake's check ORDER carries no meaning.

    `test_forget_that_rule_is_not_focus_drop` above goes through `ingest`, so it passes whether the
    forms are exclusive or whether ladder POSITION is silently picking the winner — it cannot see
    this property. Until 2026-07-20 both forms fired on `forget that rule` and only the order
    decided; `focus.drop`'s NAC ("nothing follows `that`") is what makes them genuinely exclusive.

    Asserted at the RECOGNIZER level, which is the only place the difference is visible."""
    from ugm.focus import recognize_focus_op
    from ugm.rule_control import recognize_rule_op

    # the more specific surface: ONLY the rule form fires
    assert recognize_rule_op("forget that rule") == "disable"
    assert recognize_focus_op("forget that rule") is None, (
        "the focus drop form still fires on `forget that rule` — routing depends on ladder order")

    # the general surface: ONLY the focus form fires, and the NAC did not over-reach
    assert recognize_rule_op("forget that") is None
    assert recognize_focus_op("forget that") == ("drop", None)

    # and no surface is claimed by both
    for text in ("forget that", "forget that rule", "disable that rule",
                 "focus on ada", "back to ada"):
        fired = [n for n, hit in (("rule", recognize_rule_op(text)),
                                  ("focus", recognize_focus_op(text))) if hit]
        assert len(fired) <= 1, f"{text!r} is claimed by both recognizers: {fired}"


#: One representative surface per intake route, plus plain facts. Extend it when a route is added.
ROUTER_SURFACES = [
    "forget that rule",                          # rule-disable
    "disable that rule",                         # rule-disable
    "forget that",                               # focus (drop)
    "focus on ada",                              # focus (push)
    "back to ada",                               # focus (reenter)
    "be cautious",                               # stance
    "to build : get wood",                       # procedure
    "run build",                                 # procedure run
    "is ada watched",                            # question
    "?x is watched when ?x is a suspect",        # rule
    "ada is a suspect",                          # fact
    "ada is happy",                              # fact
]


def _recognizers_firing(text):
    """Which of the router's recognizers claim `text`. One entry per route it dispatches on."""
    from ugm import focus as focus_mod, rule_control
    from ugm.cnl import form_authoring, procedure_surface
    from ugm.cnl.authoring import load_rules
    from ugm.cnl.query import recognize
    from ugm.policy import recognize_stance

    def _try(fn):
        try:
            return fn()
        except Exception:
            return None          # a malformed surface for THIS route is not a claim on it

    fop = _try(lambda: focus_mod.recognize_focus_op(text))
    checks = {
        "rule-disable": _try(lambda: rule_control.recognize_rule_op(text)),
        "focus": fop[0] if fop else None,
        "stance": _try(lambda: recognize_stance(text)),
        "form": _try(lambda: form_authoring.parse_form_line(text)),
        "procedure": _try(lambda: procedure_surface.parse_define(text)),
        "run": _try(lambda: procedure_surface.parse_run(text)),
        "question": _try(lambda: recognize(text)),
        "rule": _try(lambda: load_rules(text, lint=False)),
    }
    return sorted(n for n, hit in checks.items() if hit)


@pytest.mark.parametrize("text", ROUTER_SURFACES)
def test_at_most_one_router_recognizer_claims_a_surface(text):
    """⭐ THE §D.1 PROPERTY FOR THE WHOLE ROUTER: routing is decided by WHICH FORM FIRED, so no
    surface may be claimed by two routes — otherwise the answer comes from the order of the checks
    rather than from the declarations, and reordering the router silently changes behaviour.

    Held for every surface here EXCEPT `forget that rule` until 2026-07-20, which is exactly why
    that pair needed a structural fix rather than a comment. This is the standing guard that the
    next route added does not quietly reintroduce an ordered ladder."""
    fired = _recognizers_firing(text)
    assert len(fired) <= 1, f"{text!r} is claimed by {fired} — routing would depend on check order"


def test_forget_that_rule_with_no_rule_authored_is_noop():
    from ugm.cnl.authoring import load_corpus
    kb, rules = load_corpus("")
    out = ingest(kb, rules, "forget that rule")                 # nothing authored yet
    assert out.kind == "rule-disable" and out.disabled_keys == []


def test_gibberish_is_unrecognized():
    kb, rules = _fresh()
    out = ingest(kb, rules, "asdf qwer zzz")
    assert out.kind == "unrecognized"


def test_empty_is_unrecognized():
    kb, rules = _fresh()
    assert ingest(kb, rules, "   ").kind == "unrecognized"

"""
Universals -> laws — parsing a natural-language universal `if BODY then HEAD` into an executable
rule (docs/handoff_redesign.md "universals->laws"). The bound variable's NL surface is a
quantifier + anaphor pair (`someone ... they`, `something ... it`), which
decision_quantification_coreference says QUANTIFIES (binds all witnesses by name) rather than
refers — so the two words unify to ONE rule variable with no coreference, and `expand_rules` maps
them (`rule_var_name`). These tests lock the parse (batch `load_universal_rules`) and the
end-to-end Session behaviour (assert a rule, reason, explain).

FIRST-SLICE scope: COPULA laws (`is [not] O`). n-ary verb clauses (`the lion eats the dog`) are
the separate undeclared-verb gap; `is not` PARSES to a NAC but its runtime is limited by the
coarse copula stratification (see test_negation_universal_parses_to_a_nac).
"""
import warnings

import ugm as h
from ugm.cnl.authoring import load_universal_rules


def _shape(rule):
    role = lambda pats: sorted(p.tokens() for p in pats)
    return (role(rule.lhs), role(rule.rhs), role(rule.nac))


# ---------------------------------------------------------------------------
# Parsing — `if BODY then HEAD` -> a Rule with the quantifier words as variables
# ---------------------------------------------------------------------------

def test_single_condition_person_universal():
    # The handoff's canonical target: `someone`/`they` unify to ONE variable `?x`.
    [r] = load_universal_rules("if someone is rough then they are young")
    assert _shape(r) == ([("?x", "is", "rough")], [("?x", "is", "young")], [])


def test_thing_universal_uses_a_distinct_variable():
    # `something`/`it` -> `?y` (the thing class), distinct from the person class.
    [r] = load_universal_rules("if something is red then it is nice")
    assert _shape(r) == ([("?y", "is", "red")], [("?y", "is", "nice")], [])


def test_conjunctive_body_shares_the_variable():
    # `someone ... they ... they` all denote the same witness -> one `?x` joins all three clauses.
    [r] = load_universal_rules("if someone is happy and they are calm then they are nice")
    assert _shape(r) == ([("?x", "is", "calm"), ("?x", "is", "happy")],
                         [("?x", "is", "nice")], [])


def test_elliptical_conjunction_reuses_subject_and_copula():
    # `is round and big` — the second conjunct is a bare modifier that reuses the clause's SUBJECT
    # (`someone` -> ?x) and its copula (`is`): `?x is round and ?x is big`. The full-clause conjunct
    # (`... and they are calm`) already works via the generic clause; this is the SHARED-subject
    # ellipsis the generic clause cannot fold from a lone token.
    [r] = load_universal_rules("if someone is round and big then they are young")
    assert _shape(r) == ([("?x", "is", "big"), ("?x", "is", "round")], [("?x", "is", "young")], [])


def test_elliptical_negation_reuses_subject_and_copula():
    # `and not rough` after a copula clause -> a NAC on `?x is rough` (the elliptical counterpart of
    # the `is not` sugar), reusing the subject + copula.
    [r] = load_universal_rules("if someone is young and not rough then they are calm")
    assert _shape(r) == ([("?x", "is", "young")], [("?x", "is", "calm")], [("?x", "is", "rough")])


def test_elliptical_chains_and_mixes_polarity():
    # An ellipsis chains: each modifier reuses the ORIGINAL subject+copula, positive or negated,
    # off either a positive or a NAC prior conjunct (found by its object, role-blind).
    [r] = load_universal_rules("if someone is round and big and small then they are young")
    assert _shape(r) == ([("?x", "is", "big"), ("?x", "is", "round"), ("?x", "is", "small")],
                         [("?x", "is", "young")], [])
    [m] = load_universal_rules("if someone is young and not rough and big then they are calm")
    assert _shape(m) == ([("?x", "is", "big"), ("?x", "is", "young")],
                         [("?x", "is", "calm")], [("?x", "is", "rough")])


def test_elliptical_conjunction_in_the_prose_when_grammar():
    # The ellipsis is in the SHARED body spine, so the native `HEAD when BODY` grammar folds it too
    # (here the elliptical modifier ends the chain rather than preceding a `then`).
    from ugm.cnl.authoring import load_rules
    [r] = load_rules("?x is young when ?x is round and big")
    assert _shape(r) == ([("?x", "is", "big"), ("?x", "is", "round")], [("?x", "is", "young")], [])
    [n] = load_rules("?x is calm when ?x is young and not rough")
    assert _shape(n) == ([("?x", "is", "young")], [("?x", "is", "calm")], [("?x", "is", "rough")])


def test_elliptical_conjunction_reasons_end_to_end():
    s = h.Session()
    assert s.submit("if someone is round and big then they are young").recognized
    s.submit("dave is round")
    s.submit("dave is big")
    assert s.submit("is dave young").answer == ["yes"]
    # a witness missing one conjunct does NOT derive the head
    s.submit("erin is round")
    assert s.submit("is erin young").answer != ["yes"]


def test_literal_subject_reflects_a_ground_rule():
    # No quantifier word -> the subject stays a literal, so the law is a GROUND conditional over
    # that named entity (correct for ProofWriter's `if the lion ... then the lion ...` rules).
    [r] = load_universal_rules("if the lion is angry then the lion is loud")
    assert _shape(r) == ([("lion", "is", "angry")], [("lion", "is", "loud")], [])


def test_are_is_normalized_to_is():
    # `they are young` and `they is young` parse identically (copula morphology is lexical).
    [a] = load_universal_rules("if someone is rough then they are young")
    [b] = load_universal_rules("if someone is rough then they is young")
    assert _shape(a) == _shape(b)


def test_plural_noun_universal():
    # `Cold things are kind` = "all things that are cold are kind" -> `?y is kind when ?y is cold`.
    # The plural noun is the bound variable (things->?y, people->?x), the leading adjective the
    # body, the copula predicate the head.
    [t] = load_universal_rules("cold things are kind")
    assert _shape(t) == ([("?y", "is", "cold")], [("?y", "is", "kind")], [])
    [p] = load_universal_rules("cold people are green")
    assert _shape(p) == ([("?x", "is", "cold")], [("?x", "is", "green")], [])


def test_plural_noun_universal_reasons_end_to_end():
    s = h.Session()
    assert s.submit("cold things are kind").recognized
    s.submit("ice is cold")
    assert s.submit("is ice kind").answer == ["yes"]


def test_is_not_copula_universal_reasons_after_object_aware_stratification():
    # Object-aware copula stratification: `is young and not rough -> calm` no longer false-cycles
    # through the overloaded `is` (a NAC on `is rough` used to depend on ALL `is` producers,
    # incl. `goal.satisfied`), so the NAC rule FIRES instead of being dropped by degradation.
    s = h.Session()
    with warnings.catch_warnings():
        warnings.simplefilter("error")                 # a stratification degradation would warn
        s.submit("if someone is young and they are not rough then they are calm")
        s.submit("bob is young")                        # young, and no `bob is rough` -> calm
    assert s.submit("is bob calm").answer == ["yes"]


def test_negation_universal_parses_to_a_nac():
    # `is not` in a body folds to a NAC (the copula sugar), just like the native `when` grammar.
    # (Its RUNTIME is limited by the coarse copula stratification — all `is X` share predicate
    # `is`, so an `is`-NAC can false-cycle with other `is` producers and degrade; the fix is the
    # tracked object-aware copula stratification. Parsing is correct regardless.)
    [r] = load_universal_rules("if someone is young and they are not rough then they are calm")
    assert _shape(r) == ([("?x", "is", "young")], [("?x", "is", "calm")], [("?x", "is", "rough")])


# ---------------------------------------------------------------------------
# End-to-end through the Session — the raw-NL surface actually carries
# ---------------------------------------------------------------------------

def test_lexicon_is_data_declared_variable_word():
    # The function-word lexicon is DATA, not a frozen Python list: a domain can declare its own
    # variable word (`critters is a variable`), which then works as a rule variable AND a plural
    # universal noun (`?critters`), exactly like the built-in `things`/`someone`.
    s = h.Session()
    s.submit("critters is a variable")
    [r] = load_universal_rules("cold things are kind")   # built-in still fine
    assert s.submit("cold critters are kind").recognized
    [rule] = [x for x in s.rules if x.key.startswith("rule.")]
    assert _shape(rule) == ([("?critters", "is", "cold")], [("?critters", "is", "kind")], [])
    s.submit("ice is cold")
    assert s.submit("is ice kind").answer == ["yes"]


def test_lexicon_is_data_declared_auxiliary():
    # A domain can declare its own do-support auxiliary (`doth is an auxiliary`), extending the
    # built-in does/do/did — the verb-negation forms are generated from the declaration.
    s = h.Session()
    s.submit("like is a relation")
    s.submit("doth is an auxiliary")
    r = s.submit("if someone is young and they doth not like the cow then the cow is sad")
    assert r.recognized
    [rule] = [x for x in s.rules if x.key.startswith("rule.")]
    assert [p.tokens() for p in rule.nac] == [("?x", "like", "cow")]


def test_verb_negation_folds_to_a_nac():
    # `S does/do not V O` -> a NAC on the relation `S V O` (the verb-negation counterpart of the
    # copula `is not` sugar). Needs the verb declared (a keyword) so the head/clause don't
    # mis-decompose — so this is a Session test with a catalog.
    s = h.Session()
    for line in ["eat is a relation", "chase is a relation"]:
        s.submit(line)
    r = s.submit("if someone is young and they do not eat the cow then the cow chase the lion")
    assert r.recognized
    [rule] = [x for x in s.rules if x.key.startswith("rule.")]
    assert ("?x", "is", "young") in {p.tokens() for p in rule.lhs}
    assert [p.tokens() for p in rule.nac] == [("?x", "eat", "cow")]
    assert [p.tokens() for p in rule.rhs] == [("cow", "chase", "lion")]


def test_verb_negation_reasons_under_cwa():
    s = h.Session()
    for line in ["eat is a relation", "chase is a relation",
                 "if someone is young and they do not eat the cow then the cow chase the lion",
                 "dave is young"]:                      # dave young, no `dave eat cow` -> NAC holds
        s.submit(line)
    assert s.submit("does the cow chase the lion").answer == ["yes"]


def test_session_derives_through_a_universal():
    s = h.Session()
    assert s.submit("dave is rough").recognized
    assert s.submit("if someone is rough then they are young").recognized
    assert s.submit("is dave young").answer == ["yes"]


def test_session_rule_before_fact_and_multi_step():
    s = h.Session()
    with warnings.catch_warnings():
        warnings.simplefilter("error")           # positive chains must NOT trip degradation
        s.submit("if someone is rough then they are young")
        s.submit("if someone is young then they are kind")
        s.submit("anne is rough")
    assert s.submit("is anne young").answer == ["yes"]   # QDep 1
    assert s.submit("is anne kind").answer == ["yes"]    # QDep 2 (chained)


def test_explanation_traces_the_derivation():
    s = h.Session()
    s.submit("if someone is young then they are kind")
    s.submit("anne is young")
    s.submit("is anne kind")
    trace = s.explain("anne", "is", "kind")
    assert any("anne is kind" in ln and "rule." in ln for ln in trace)   # derived by the universal
    assert any("anne is young" in ln for ln in trace)                    # its premise, indented


def test_rule_pronoun_is_a_variable_not_the_discourse_subject():
    # `they` in a rule must NOT resolve to the last asserted subject (`bob`): it is a bound
    # variable. If it wrongly resolved, the rule would become ground on `bob` and never fire for
    # `carol`.
    s = h.Session()
    s.submit("bob is rough")
    s.submit("if someone is rough then they are young")
    s.submit("carol is rough")
    assert s.submit("is carol young").answer == ["yes"]


def test_procedure_then_still_sequences_outside_a_rule():
    # The `if_ctx` guard must not break the `X then Y -> X before Y` sequencing form: a bare
    # `then` (no leading `if`) still sequences.
    s = h.Session()
    r = s.submit("wake then work")
    assert r.recognized and "wake before work" in s.facts()

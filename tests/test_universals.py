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


def test_negation_universal_parses_to_a_nac():
    # `is not` in a body folds to a NAC (the copula sugar), just like the native `when` grammar.
    # (Its RUNTIME is limited by the coarse copula stratification — all `is X` share predicate
    # `is`, so an `is`-NAC can false-cycle with other `is` producers and degrade; the fix is the
    # tracked object-aware copula stratification. Parsing is correct regardless.)
    [r] = load_universal_rules("if someone is young and they are not rough then they are calm")
    assert _shape(r) == ([("?x", "is", "young")], [("?x", "is", "calm")], [("?x", "is", "rough")])

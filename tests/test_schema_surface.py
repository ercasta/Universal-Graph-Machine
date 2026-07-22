"""META-PATTERN surface — `define schema <trigger> : <template>` (docs/design/meaning_surfaces_audit.md
§4/§5). A user defines what a relation-PROPERTY means (`transitive`, `symmetric`, …) as a rule TEMPLATE
parameterised over a relation, IN THE LANGUAGE — a rule that writes a rule, enabled by the quote token.
The in-language replacement for the Python relation-property expanders.
"""
from ugm.attrgraph import AttrGraph
from ugm.cnl.define_surface import parse_schema, compile_schema
from ugm.intake import ingest
from ugm.cnl.query import ask_goal
from ugm import assemble_facts
from ugm.machine import Machine


# --- the compiler: trigger vars are bound params, template-only vars are quoted -------------------

def test_compile_quotes_template_vars_and_binds_the_parameter():
    meta = compile_schema("?r is transitive", "?a ?r ?c when ?a ?r ?b and ?b ?r ?c")
    assert [p.tokens() for p in meta.lhs] == [("?r", "is", "transitive")]      # trigger
    rhs = {p.tokens() for p in meta.rhs}
    # the parameter ?r is BOUND (k_pred points at it, unquoted); template vars are QUOTED literals
    assert ("<c0>?", "k_subj", "'?a") in rhs and ("<c0>?", "k_pred", "?r") in rhs
    assert ("<ch0>?", "k_subj", "'?a") in rhs and ("<ch0>?", "k_obj", "'?c") in rhs

def test_parse_schema_recognizes_the_surface():
    assert parse_schema("alice is a suspect") is None                          # not a schema
    assert parse_schema("define ?x foo ?z as ?x bar ?z") is None               # ordinary define, not schema
    meta = parse_schema("define schema ?r is transitive : ?a ?r ?c when ?a ?r ?b and ?b ?r ?c")
    assert meta is not None and [p.tokens() for p in meta.lhs] == [("?r", "is", "transitive")]

def test_schema_without_colon_raises():
    import pytest
    with pytest.raises(ValueError, match="':'"):
        parse_schema("define schema ?r is transitive ?a ?r ?c when ?a ?r ?b")


# --- end-to-end through intake: define, declare, use ----------------------------------------------

def _kb():
    kb = AttrGraph(); rules = []
    return kb, rules

def test_transitive_defined_declared_and_used():
    kb, rules = _kb()
    ingest(kb, rules, "define schema ?r is transitive : ?a ?r ?c when ?a ?r ?b and ?b ?r ?c")
    Machine().run(kb, assemble_facts([("alice", "ancestor", "bob"), ("bob", "ancestor", "carol"),
                                      ("carol", "ancestor", "dave")]))
    ingest(kb, rules, "ancestor is transitive")                                # a plain fact fires it
    assert ask_goal(kb, ("yesno", "alice", "ancestor", "dave"), rules) == ["yes"]
    assert ask_goal(kb, ("yesno", "dave", "ancestor", "alice"), rules) != ["yes"]   # not symmetric

def test_one_schema_serves_many_relations():
    kb, rules = _kb()
    ingest(kb, rules, "define schema ?r is transitive : ?a ?r ?c when ?a ?r ?b and ?b ?r ?c")
    Machine().run(kb, assemble_facts([("a", "ancestor", "b"), ("b", "ancestor", "c"),
                                      ("x", "before", "y"), ("y", "before", "z")]))
    ingest(kb, rules, "ancestor is transitive")
    ingest(kb, rules, "before is transitive")
    assert ask_goal(kb, ("yesno", "a", "ancestor", "c"), rules) == ["yes"]
    assert ask_goal(kb, ("yesno", "x", "before", "z"), rules) == ["yes"]

def test_a_second_property_symmetric():
    kb, rules = _kb()
    ingest(kb, rules, "define schema ?r is symmetric : ?b ?r ?a when ?a ?r ?b")
    Machine().run(kb, assemble_facts([("alice", "sibling", "bob")]))
    ingest(kb, rules, "sibling is symmetric")
    assert ask_goal(kb, ("yesno", "bob", "sibling", "alice"), rules) == ["yes"]

def test_declaration_before_the_schema_still_generates():
    """Order-independence: a relation declared transitive BEFORE the schema is defined is still served
    — the schema is applied against the already-present declaration when it lands."""
    kb, rules = _kb()
    Machine().run(kb, assemble_facts([("a", "ancestor", "b"), ("b", "ancestor", "c")]))
    ingest(kb, rules, "ancestor is transitive")                                # no schema yet
    assert ask_goal(kb, ("yesno", "a", "ancestor", "c"), rules) != ["yes"]     # nothing derives it yet
    ingest(kb, rules, "define schema ?r is transitive : ?a ?r ?c when ?a ?r ?b and ?b ?r ?c")
    assert ask_goal(kb, ("yesno", "a", "ancestor", "c"), rules) == ["yes"]     # now it does

def test_generation_is_idempotent_across_turns():
    """Re-asserting the declaration does not pile up duplicate generated rules."""
    kb, rules = _kb()
    ingest(kb, rules, "define schema ?r is transitive : ?a ?r ?c when ?a ?r ?b and ?b ?r ?c")
    Machine().run(kb, assemble_facts([("a", "ancestor", "b"), ("b", "ancestor", "c")]))
    ingest(kb, rules, "ancestor is transitive")
    n1 = len(rules)
    ingest(kb, rules, "ancestor is transitive")                                # again
    assert len(rules) == n1                                                    # no new rule harvested
    assert ask_goal(kb, ("yesno", "a", "ancestor", "c"), rules) == ["yes"]

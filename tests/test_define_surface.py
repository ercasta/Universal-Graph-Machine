"""The DEFINITION surface — `define H as B` / `define H iff B`
(docs/design/meaning_surfaces_audit.md §4). A definition is a rule; `iff` additionally emits the
NECESSARY direction (a shared-skolem existential witness), so both directions of meaning come from one
statement — the "define meaning and use it" capability, wired into the main intake (not a new loader).
"""
import pytest

from ugm.attrgraph import AttrGraph
from ugm.cnl.define_surface import parse_definition
from ugm.cnl.rule_graph import write_rule
from ugm.cnl.query import ask_goal
from ugm.check import check, POSITIVE, ASSUMED_NO
from ugm.intake import ingest
from ugm import assemble_facts
from ugm.machine import Machine


# --- parse_definition: as → 1 rule, iff → sufficient + necessary ----------------------------------

def test_as_yields_the_sufficient_rule_only():
    defs = parse_definition("define ?x grandparent ?z as ?x parent ?y and ?y parent ?z")
    assert len(defs) == 1
    r = defs[0]
    assert sorted(p.tokens() for p in r.lhs) == [("?x", "parent", "?y"), ("?y", "parent", "?z")]
    assert [p.tokens() for p in r.rhs] == [("?x", "grandparent", "?z")]

def test_iff_yields_sufficient_and_necessary():
    defs = parse_definition("define ?x grandparent ?z iff ?x parent ?y and ?y parent ?z")
    assert len(defs) == 2
    suff, nec = defs
    assert [p.tokens() for p in suff.rhs] == [("?x", "grandparent", "?z")]      # body ⇒ head
    assert [p.tokens() for p in nec.lhs] == [("?x", "grandparent", "?z")]       # head ⇒ body …
    # … with the non-head var ?y existentially witnessed by a SHARED bound-literal skolem `y?`
    assert [p.tokens() for p in nec.rhs] == [("?x", "parent", "y?"), ("y?", "parent", "?z")]

def test_non_define_line_returns_none():
    assert parse_definition("alice is a suspect") is None
    assert parse_definition("define with no connective here") is None          # falls through, no raise

def test_a_define_with_a_connective_but_unparseable_body_raises():
    """A clear define intent (a connective is present) whose head/body will not parse RAISES loudly,
    via the shared rule parser — a definition that silently does nothing is worse than a loud one.
    (`define as`, with no head OR body, is not clear intent → falls through, tested above.)"""
    with pytest.raises(ValueError):
        parse_definition("define ?x as ?y")


# --- semantics: both directions reason ------------------------------------------------------------

def _kb(defs, facts):
    g = AttrGraph()
    Machine().run(g, assemble_facts([tuple(f.split()) for f in facts]))
    for r in defs:
        write_rule(g, r)
    return g

def test_sufficient_direction_reasons():
    g = _kb(parse_definition("define ?x grandparent ?z as ?x parent ?y and ?y parent ?z"),
            ["alice parent bob", "bob parent carol"])
    assert check(g, ("grandparent", "alice", "carol")) == POSITIVE

def test_as_gives_no_necessary_direction():
    """`as` is one-directional: knowing X is a grandparent does NOT (with `as`) entail a parent chain."""
    g = _kb(parse_definition("define ?x grandparent ?z as ?x parent ?y and ?y parent ?z"),
            ["xavier grandparent zoe"])
    assert check(g, ("parent", "xavier", None)) == ASSUMED_NO

def test_iff_gives_both_directions():
    g = _kb(parse_definition("define ?x forebear ?z iff ?x parent ?y and ?y parent ?z"),
            ["alice parent bob", "bob parent carol", "xavier forebear zoe"])
    assert check(g, ("forebear", "alice", "carol")) == POSITIVE                # sufficient
    assert check(g, ("parent", "xavier", None)) == POSITIVE                    # necessary: ∃ w xavier parents
    assert check(g, ("parent", None, "zoe")) == POSITIVE                       # necessary: ∃ w parents zoe


# --- wired into the main intake (not a new loader) ------------------------------------------------

def test_intake_routes_define_and_reasons_with_it():
    kb = AttrGraph(); rules = []
    Machine().run(kb, assemble_facts([("alice", "parent", "bob"), ("bob", "parent", "carol")]))
    out = ingest(kb, rules, "define ?x grandparent ?z as ?x parent ?y and ?y parent ?z")
    assert out.kind == "define"
    assert len(out.added_rules) == 1
    # the rule reasons immediately on the accumulated `rules` (the intake contract)
    assert ask_goal(kb, ("yesno", "alice", "grandparent", "carol"), rules) == ["yes"]

def test_intake_iff_adds_both_and_the_necessary_direction_answers():
    kb = AttrGraph(); rules = []
    Machine().run(kb, assemble_facts([("xavier", "forebear", "zoe")]))
    out = ingest(kb, rules, "define ?x forebear ?z iff ?x parent ?y and ?y parent ?z")
    assert out.kind == "define" and len(out.added_rules) == 2
    assert ask_goal(kb, ("yesno", "xavier", "parent", None), rules) == ["yes"]

def test_a_non_define_line_still_routes_normally():
    kb = AttrGraph(); rules = []
    out = ingest(kb, rules, "define something with no connective")
    assert out.kind == "unrecognized"                          # fell through the define route cleanly

"""The QUOTE token `'X` (docs/design/meaning_surfaces_audit.md §5) — the metalinguistic escape that
lets a rule NAME a variable as a literal, so a rule can WRITE a rule (and a user can author a
meta-pattern) IN THE LANGUAGE, not only through the interned-pool indirection.

`'?a` = "the symbol ?a": a plain literal whose NAME is `?a`, even though `?a` bare is a variable.
"""
from ugm.attrgraph import AttrGraph
from ugm.production_rule import Pat, Rule, is_var, is_bound_literal, is_symbol, literal_name, binder
from ugm.lowering import run_bank, assemble_facts
from ugm.cnl.authoring import expand_rules
from ugm.cnl.rule_graph import write_rule
from ugm.check import check, POSITIVE, ASSUMED_NO
from ugm.machine import Machine


# --- classification: a quoted token is a plain literal named by its unquoted rest -----------------

def test_quoted_token_is_a_plain_literal_named_by_its_rest():
    assert is_symbol("'?a") is True
    assert is_var("'?a") is False            # the whole point: NOT read as a variable
    assert is_bound_literal("'?a") is False
    assert binder("'?a") is None             # a plain literal binds nothing
    assert literal_name("'?a") == "?a"       # its NAME is the unquoted rest

def test_bare_variable_is_unchanged():
    assert is_var("?a") is True
    assert is_symbol("?a") is False
    assert literal_name("is_a") == "is_a"    # ordinary literals untouched
    assert literal_name("paul?") == "paul"   # bound literals untouched

def test_pat_slot_classification():
    p = Pat("'?a", "ancestor", "?b")
    assert p.s_kind == 0 and p.s_name == "?a"   # subject: quoted plain literal, name '?a'
    assert p.o_kind == 1 and p.o_name == "?b"   # object: an ordinary variable


# --- the capability: a rule writes a variable-bearing rule, in-language ---------------------------

def _meta_transitive():
    """Given `?R rel_property transitive`, WRITE the transitivity rule for ?R — variables quoted."""
    return Rule(key="meta.transitive",
        lhs=[Pat("?R", "rel_property", "transitive")],
        rhs=[Pat("<r>?", "rl_lhs", "<c1>?"),
             Pat("<c1>?", "k_subj", "'?a"), Pat("<c1>?", "k_pred", "?R"), Pat("<c1>?", "k_obj", "'?b"),
             Pat("<r>?", "rl_lhs", "<c2>?"),
             Pat("<c2>?", "k_subj", "'?b"), Pat("<c2>?", "k_pred", "?R"), Pat("<c2>?", "k_obj", "'?c"),
             Pat("<r>?", "rl_head", "<ch>?"),
             Pat("<ch>?", "k_subj", "'?a"), Pat("<ch>?", "k_pred", "?R"), Pat("<ch>?", "k_obj", "'?c")])


def _written_transitivity(g):
    return [r for r in expand_rules(g) if "?a" in {t for p in r.lhs for t in p.tokens()}]


def test_a_rule_writes_a_variable_bearing_rule():
    g = AttrGraph()
    Machine().run(g, assemble_facts([("ancestor", "rel_property", "transitive")]))
    run_bank(g, [_meta_transitive()])
    written = _written_transitivity(g)
    assert len(written) == 1
    r = written[0]
    assert sorted(p.tokens() for p in r.lhs) == [("?a", "ancestor", "?b"), ("?b", "ancestor", "?c")]
    assert [p.tokens() for p in r.rhs] == [("?a", "ancestor", "?c")]


def test_the_written_rule_reasons_correctly():
    g = AttrGraph()
    Machine().run(g, assemble_facts([
        ("ancestor", "rel_property", "transitive"),
        ("alice", "ancestor", "bob"), ("bob", "ancestor", "carol"), ("carol", "ancestor", "dave")]))
    run_bank(g, [_meta_transitive()])
    for r in _written_transitivity(g):
        write_rule(g, r)
    assert check(g, ("ancestor", "alice", "dave")) == POSITIVE     # 3-deep transitive closure
    assert check(g, ("ancestor", "dave", "alice")) == ASSUMED_NO   # not symmetric


def test_the_quote_parameterizes_over_the_relation():
    """The SAME meta-rule writes DIFFERENT transitivity rules per declared relation — the payoff of a
    rule-writing rule over a per-relation Python expander."""
    g = AttrGraph()
    Machine().run(g, assemble_facts([
        ("before", "rel_property", "transitive"),
        ("t1", "before", "t2"), ("t2", "before", "t3")]))
    run_bank(g, [_meta_transitive()])
    written = [r for r in expand_rules(g) if r.rhs and r.rhs[0].p == "before"]
    assert written and written[0].rhs[0].tokens() == ("?a", "before", "?c")
    for r in written:
        write_rule(g, r)
    assert check(g, ("before", "t1", "t3")) == POSITIVE


# --- RE-BREAK: without the quote, the meta-rule captures the variables as ITS OWN --------------

def test_rebreak_without_the_quote_the_meta_rule_is_malformed():
    """Bare `?a` in the meta-rule's RHS is the meta-rule's OWN variable (RHS-only, unbound), NOT the
    literal `?a` for the written rule. Firing it mints fresh UNNAMED nodes for the k_subj/k_obj targets,
    so the written fragment resolves to no token and `expand_rules` RAISES LOUDLY. The quote is
    load-bearing: with it the fragment is a clean rule (proven above), without it a loud error — never
    a silently-wrong rule."""
    import pytest
    g_b = AttrGraph()
    Machine().run(g_b, assemble_facts([("ancestor", "rel_property", "transitive")]))
    bare = Rule(key="meta.bare",
        lhs=[Pat("?R", "rel_property", "transitive")],
        rhs=[Pat("<r>?", "rl_lhs", "<c1>?"),
             Pat("<c1>?", "k_subj", "?a"), Pat("<c1>?", "k_pred", "?R"), Pat("<c1>?", "k_obj", "?b"),
             Pat("<r>?", "rl_head", "<ch>?"),
             Pat("<ch>?", "k_subj", "?a"), Pat("<ch>?", "k_pred", "?R"), Pat("<ch>?", "k_obj", "?c")])
    run_bank(g_b, [bare])
    with pytest.raises(ValueError, match="silently-broken|no token"):
        expand_rules(g_b)

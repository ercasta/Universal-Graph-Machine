"""`units/cnl.py` — the CNL surface's first real slice, tested against `docs/units/cnl.md` §5's
transcription table directly: each row gets a test named after it, not a generic round-trip check."""
import pytest

from units.cnl import CNLSyntaxError, parse
from units.graph import EMPTY


def test_a_bare_word_head_mints_an_occurrence_with_a_name_attribute():
    g, occ = parse("[eligible]")
    assert g.attr(occ, "name") == "eligible"


def test_a_role_mints_a_fresh_role_node_with_an_edge_from_the_occurrence():
    g, occ = parse("[eligible | agent: paul]")
    (role_node,) = g.out(occ)
    assert g.attr(role_node, "name") == "agent"


def test_a_bare_word_filler_mints_a_fresh_node_with_a_name_attribute():
    g, occ = parse("[eligible | agent: paul]")
    (role_node,) = g.out(occ)
    (filler,) = g.out(role_node)
    assert g.attr(filler, "name") == "paul"


def test_nesting_is_containment_the_inner_occurrence_is_the_filler():
    g, occ = parse("[utterance | content: [eligible | agent: paul]]")
    (content_role,) = g.out(occ)
    (content,) = g.out(content_role)
    assert g.attr(content, "name") == "eligible"
    (agent_role,) = g.out(content)
    (agent,) = g.out(agent_role)
    assert g.attr(agent, "name") == "paul"


def test_two_roles_with_the_same_name_are_two_distinct_role_nodes():
    """`graph.py`'s `role_edge` docstring: plurality without a set node — call it twice, get two role
    nodes. `[went | agent: paul | agent: mary]` for "Paul and Mary went"."""
    g, occ = parse("[went | agent: paul | agent: mary]")
    role_nodes = g.out(occ)
    assert len(role_nodes) == 2
    assert role_nodes[0] is not role_nodes[1]
    fillers = {g.attr(n, "name") for r in role_nodes for n in g.out(r)}
    assert fillers == {"paul", "mary"}


def test_force_is_a_crisp_attribute_on_the_occurrence_not_a_role_node():
    g, occ = parse("[utterance | force: ask]")
    assert g.attr(occ, "force") == "ask"
    assert g.out(occ) == ()          # no role node minted for it


def test_level_is_a_crisp_attribute_the_same_way_as_force():
    g, occ = parse("[utterance | level: theory]")
    assert g.attr(occ, "level") == "theory"
    assert g.out(occ) == ()


def test_force_and_an_ordinary_role_combine_on_one_occurrence():
    g, occ = parse("[utterance | force: ask | content: eligible]")
    assert g.attr(occ, "force") == "ask"
    (role_node,) = g.out(occ)
    assert g.attr(role_node, "name") == "content"


def test_force_must_be_a_bare_word_not_a_nested_statement():
    with pytest.raises(CNLSyntaxError):
        parse("[utterance | force: [ask]]")


def test_several_statements_can_share_one_growing_graph():
    g, u1 = parse("[eligible | agent: paul]")
    g, u2 = parse("[eligible | agent: mary]", into=g)
    assert u1 is not u2
    assert g.attr(u1, "name") == g.attr(u2, "name") == "eligible"


# -- refusal: a translator emitting something outside the grammar must be caught, not guessed at --------

def test_unrecognized_character_raises_rather_than_being_silently_dropped():
    with pytest.raises(CNLSyntaxError):
        parse("[eligible | agent: paul?]")


def test_missing_closing_bracket_raises():
    with pytest.raises(CNLSyntaxError):
        parse("[eligible | agent: paul")


def test_trailing_tokens_after_a_complete_statement_raise():
    with pytest.raises(CNLSyntaxError):
        parse("[eligible] [ineligible]")


def test_empty_input_raises_rather_than_returning_an_empty_graph():
    with pytest.raises(CNLSyntaxError):
        parse("")

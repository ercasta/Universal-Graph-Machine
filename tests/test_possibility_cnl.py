"""
Possibilistic CNL surface SLICE 1 (docs/possibilistic.md S7.5): the hedge-on-a-fact form, the first
disjunctive `either…or` form, and banded yes/no verdicts. See `ugm/cnl/uncertainty.py`.
"""
from ugm.attrgraph import AttrGraph
from ugm.apply import SCOPE
from ugm.possibility import possibility
from ugm.cnl.uncertainty import (
    parse_hedge_fact, parse_hedge_decl, hedge_bands, parse_either, load_uncertain, ask,
)


def _scope_of(g: AttrGraph, subj: str, obj: str):
    """The fork-scope id holding the pencil `subj is obj`, or None — for the correlation check."""
    for s_id in g.nodes_named(subj):
        for r in g.out(s_id):
            if g.is_control(r) and any(g.name(o) == obj for o in g.out(r)):
                a = g.get_attr(r, SCOPE)
                return a.value if a is not None else None
    return None


# --- form 1: hedge on a fact ------------------------------------------------

def test_hedge_parse():
    assert parse_hedge_fact("cy is likely a thief") == ("cy", "is_a", "thief", 0.6)
    assert parse_hedge_fact("x is unlikely male") == ("x", "is", "male", 0.3)
    assert parse_hedge_fact("x is very likely male") == ("x", "is", "male", 0.85)
    assert parse_hedge_fact("x is very unlikely male") == ("x", "is", "male", 0.15)


def test_degree_adverb_is_not_a_hedge():
    """DISAMBIGUATION: a membership degree adverb is never routed as a hedge (the crisp/degree
    surface is untouched)."""
    assert parse_hedge_fact("x is very urgent") is None
    assert parse_hedge_fact("alice is somewhat urgent") is None
    assert parse_hedge_fact("alice is slightly cold") is None


def test_hedge_load_and_ask():
    g = AttrGraph()
    rest = load_uncertain(g, "cy is likely a thief\nx is very unlikely male")
    assert rest == []
    assert ask(g, "is cy a thief") == "likely"
    assert ask(g, "is x male") == "very unlikely"
    assert ask(g, "is x female") == "assumed-no"                 # unmentioned, closed
    assert ask(g, "is x female", closed=False) == "unknown"


def test_load_uncertain_returns_plain_lines():
    """Plain facts are NOT intercepted — they come back for the ordinary loader."""
    g = AttrGraph()
    rest = load_uncertain(g, "cy is likely a thief\nbob likes mary\nx is unlikely tall")
    assert rest == ["bob likes mary"]
    assert ask(g, "is cy a thief") == "likely"
    assert possibility(g, "is", "x", "tall") == 0.3             # `unlikely tall` -> a fork, not a degree


# --- the hedge lexicon is KB data (backlog item 2) ---------------------------

def test_hedge_decl_parse():
    assert parse_hedge_decl("probable means 0.7") == ("probable", 0.7)
    assert parse_hedge_decl("almost certain means 0.9") == ("almost certain", 0.9)   # two-word hedge
    assert parse_hedge_decl("likely means 0.8") == ("likely", 0.8)                   # override a default
    assert parse_hedge_decl("probable means 1.5") is None                            # out of (0, 1]
    assert parse_hedge_decl("x means well") is None                                  # not a number
    assert parse_hedge_decl("a b c means 0.5") is None                               # hedge ≤ 2 words


def test_declared_hedge_extends_the_lexicon():
    """`probable means 0.7` is an INK fact; the hedge then parses like a shipped one — the scale is
    KB data, exactly like the degree adverbs (`very is 0.8`)."""
    g = AttrGraph()
    rest = load_uncertain(g, "probable means 0.7\nalmost certain means 0.9\n"
                             "cy is probable a thief\nx is almost certain male")
    assert rest == []
    assert hedge_bands(g)["probable"] == 0.7
    assert possibility(g, "is_a", "cy", "thief") == 0.7
    assert possibility(g, "is", "x", "male") == 0.9
    assert ask(g, "is cy a thief") == "likely"
    assert ask(g, "is x male") == "very likely"


def test_declared_hedge_overrides_a_default():
    g = AttrGraph()
    load_uncertain(g, "likely means 0.8\ncy is likely a thief")
    assert possibility(g, "is_a", "cy", "thief") == 0.8            # not the shipped 0.6
    g2 = AttrGraph()
    load_uncertain(g2, "cy is likely a thief")                     # untouched elsewhere
    assert possibility(g2, "is_a", "cy", "thief") == 0.6


# --- form 2: the first disjunctive form -------------------------------------

def test_either_parse():
    assert parse_either("x is either male and tall or female and short") == (
        "x", ["male", "tall"], ["female", "short"], None)
    assert parse_either("x is either male and tall or more likely female and short") == (
        "x", ["male", "tall"], ["female", "short"], "more")
    assert parse_either("x is either male or less likely female") == (
        "x", ["male"], ["female"], "less")


def test_either_or_makes_two_correlated_forks():
    g = AttrGraph()
    load_uncertain(g, "x is either male and tall or female and short")
    # both alternatives visible at the even band
    for attr in ("male", "tall", "female", "short"):
        assert possibility(g, "is", "x", attr) == 0.5
    # CORRELATION (the point of the form): male∧tall share ONE fork; female∧short another.
    assert _scope_of(g, "x", "male") == _scope_of(g, "x", "tall")
    assert _scope_of(g, "x", "female") == _scope_of(g, "x", "short")
    assert _scope_of(g, "x", "male") != _scope_of(g, "x", "female")


def test_ranked_either_or():
    """`or more likely` / `or less likely` rank the alternatives: the favoured one carries the
    `likely` rung, the other the `unlikely` rung — ordinal, so what matters is order + the θ-cut."""
    g = AttrGraph()
    load_uncertain(g, "x is either male and tall or more likely female and short")
    assert possibility(g, "is", "x", "female") == 0.6
    assert possibility(g, "is", "x", "short") == 0.6              # correlation preserved
    assert possibility(g, "is", "x", "male") == 0.3
    assert ask(g, "is x female") == "likely"
    assert ask(g, "is x male") == "unlikely"
    # still one exclusive choice: male∧short remains an impossible combination
    assert _scope_of(g, "x", "male") != _scope_of(g, "x", "female")
    g2 = AttrGraph()
    load_uncertain(g2, "x is either male or less likely female")
    assert possibility(g2, "is", "x", "male") == 0.6
    assert possibility(g2, "is", "x", "female") == 0.3


def test_ranked_either_uses_the_declared_lexicon():
    """The ranked rungs come from the lexicon IN SCOPE, so `likely means 0.8` re-scales a ranked
    either too (the scale is KB data everywhere, not a constant)."""
    g = AttrGraph()
    load_uncertain(g, "likely means 0.8\nx is either male or more likely female")
    assert possibility(g, "is", "x", "female") == 0.8

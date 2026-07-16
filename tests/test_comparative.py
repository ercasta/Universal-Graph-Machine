"""
Gradable COMPARATIVES (docs/possibilistic.md decisions 1–3 + open points G/H): the decomposed
comparison node (dimension = the predicate, direction = more/less), demand-driven transitivity as a
generated per-dimension rule, the degree bridge (rungs make incomparables comparable), honest
UNKNOWN for genuine incomparability, and the conflict LINTER (defeat, never ⊥).
"""
import time

from ugm.attrgraph import AttrGraph
from ugm.cnl.comparative import (
    parse_comparative, load_comparative, add_comparison, comparison_dims, comparison_rules,
    ask_comparative, lint_comparisons, COMPARISON,
)


def _kb(text: str) -> AttrGraph:
    g = AttrGraph()
    rest = load_comparative(g, text)
    assert rest == []
    return g


# --- decision 1: the decomposed comparison ------------------------------------------------------

def test_parse_and_direction_carries_more_less():
    assert parse_comparative("x is more beautiful than y") == ("x", "beautiful", "y")
    assert parse_comparative("y is less beautiful than x") == ("x", "beautiful", "y")   # reversed arrow
    assert parse_comparative("x likes y") is None
    assert parse_comparative("x is very beautiful") is None                # a degree, not a comparison


def test_comparison_is_a_marked_relation_with_the_dimension_as_predicate():
    g = AttrGraph()
    rel = add_comparison(g, "x", "beautiful", "y")
    assert g.predicate(rel) == "beautiful"                 # the dimension stays first-class
    assert g.get_attr(rel, COMPARISON) is not None         # class-marked
    assert comparison_dims(g) == {"beautiful"}
    assert [r.key for r in comparison_rules(g)] == ["cmp.trans.beautiful"]


# --- transitivity, demand-driven; incomparability = honest UNKNOWN (decisions 1+3) ---------------

def test_transitive_chain_answers_and_the_partial_order_stays_partial():
    """The doc's opening example: x > y > z and t > z. The transitive x > z is derivable; y vs t is
    GENUINELY incomparable — `unknown`, a first-class answer, never completed, never a CWA no."""
    g = _kb("x is more beautiful than y\n"
            "y is more beautiful than z\n"
            "t is more beautiful than z")
    assert ask_comparative(g, "is x more beautiful than y") == "yes"       # direct
    assert ask_comparative(g, "is x more beautiful than z") == "yes"       # transitive
    assert ask_comparative(g, "is z more beautiful than x") == "no"        # the reverse is entailed
    assert ask_comparative(g, "is z less beautiful than x") == "yes"       # less = the reversed ask
    assert ask_comparative(g, "is y more beautiful than t") == "unknown"   # incomparable — honest
    assert ask_comparative(g, "is t more beautiful than y") == "unknown"


def test_asking_leaks_no_facts():
    """The transitive closure runs demand-driven in an ephemeral pencil scope — asking must not
    accrete derived comparison FACTS into the KB. (Value-node operand interning may add carrier
    nodes — the documented #12-style boundary — so the invariant is over visible facts.)"""
    from ugm.chain import _facts_matching
    g = _kb("a is more tall than b\nb is more tall than c")
    assert len(_facts_matching(g, "tall", None, None)) == 2
    assert ask_comparative(g, "is a more tall than c") == "yes"
    assert len(_facts_matching(g, "tall", None, None)) == 2            # the derived a>c was swept


# --- decision 2: the degree bridge --------------------------------------------------------------

def test_rungs_make_incomparables_comparable():
    """The 'if I use very/little I CAN compare' insight: no declared path between x and y, but both
    hold rungs on the dimension — the ordinal compare answers."""
    g = AttrGraph()
    x, y = g.add_node("x"), g.add_node("y")
    g.set_embedding(x, {"beautiful": 0.8})                 # `x is very beautiful`
    g.set_embedding(y, {"beautiful": 0.3})                 # `y is slightly beautiful`
    assert ask_comparative(g, "is x more beautiful than y") == "yes"
    assert ask_comparative(g, "is y more beautiful than x") == "no"
    assert ask_comparative(g, "is x as beautiful as y") == "no"


def test_equal_rungs_are_honest_for_the_strict_question():
    """Same rung: `as beautiful as` is yes, but the STRICT `more` stays unknown — the rungs are
    coarse, and a finer difference within a rung is not ruled out."""
    g = AttrGraph()
    x, y = g.add_node("x"), g.add_node("y")
    g.set_embedding(x, {"beautiful": 0.5})
    g.set_embedding(y, {"beautiful": 0.5})
    assert ask_comparative(g, "is x as beautiful as y") == "yes"
    assert ask_comparative(g, "is x more beautiful than y") == "unknown"


def test_declared_path_beats_the_bridge():
    """A declared comparison refines WITHIN a rung: equal degrees, but x > y is declared — the
    partial order answers first."""
    g = _kb("x is more beautiful than y")
    for n, name in ((g.nodes_named("x")[0], "x"), (g.nodes_named("y")[0], "y")):
        g.set_embedding(n, {"beautiful": 0.5})
    assert ask_comparative(g, "is x more beautiful than y") == "yes"


def test_degrees_via_the_real_cnl_pipeline():
    """End-to-end with the EXISTING degree surface: `beautiful is gradable` + adverb facts author
    the rungs through the ordinary loader; the comparative layer reads them — nothing re-implemented
    (the two surfaces compose line-by-line, exactly like the possibilistic loader)."""
    import ugm as h
    kb, _rules = h.load_corpus("beautiful is gradable\n"
                               "x is very beautiful\n"
                               "z is slightly beautiful")
    load_comparative(kb, "x is more beautiful than w")     # comparisons author INTO the loaded KB
    assert ask_comparative(kb, "is x more beautiful than z") == "yes"      # bridge: 0.8 > 0.3
    assert ask_comparative(kb, "is x more beautiful than w") == "yes"      # declared
    assert ask_comparative(kb, "is z more beautiful than w") == "unknown"  # neither path nor rungs


# --- H: the linter — conflicts are defeat/lint, never ⊥ ------------------------------------------

def test_lint_reports_a_cycle():
    g = _kb("x is more beautiful than y\n"
            "y is more beautiful than z\n"
            "z is more beautiful than x")
    warnings = lint_comparisons(g)
    assert len(warnings) == 1 and "cycle" in warnings[0] and "beautiful" in warnings[0]


def test_lint_reports_comparative_vs_degree_conflict():
    g = _kb("x is more beautiful than y")
    g.set_embedding(g.nodes_named("x")[0], {"beautiful": 0.3})
    g.set_embedding(g.nodes_named("y")[0], {"beautiful": 0.8})
    warnings = lint_comparisons(g)
    assert len(warnings) == 1 and "conflict" in warnings[0]
    # equal rungs do NOT conflict (the comparative refines within a rung)
    g2 = _kb("a is more tall than b")
    g2.set_embedding(g2.nodes_named("a")[0], {"tall": 0.5})
    g2.set_embedding(g2.nodes_named("b")[0], {"tall": 0.5})
    assert lint_comparisons(g2) == []


def test_lint_clean_kb_is_silent():
    g = _kb("x is more beautiful than y\ny is more beautiful than z")
    assert lint_comparisons(g) == []


# --- G: the perf posture — demand-driven transitive closure on a long chain ---------------------

def test_long_chain_is_answered_demand_driven_in_reasonable_time():
    """Open point G, measured 2026-07-16: the 2-body transitivity rule asked END TO END costs
    0.07s @ 10 links, 0.7s @ 20, 3.3s @ 30, 10.5s @ 40 — SUPERLINEAR (the round loop re-serves
    every standing demand each round; the `demand-coref-perf-wall` shape). Session-sized chains
    are comfortably sub-second; the wall is recorded in docs/possibilistic.md. This pins
    correctness at 20 links plus a generous ceiling so a regression to a worse curve is caught."""
    n = 20
    lines = "\n".join(f"a{i} is more tall than a{i + 1}" for i in range(n))
    g = _kb(lines)
    t0 = time.perf_counter()
    assert ask_comparative(g, f"is a0 more tall than a{n}") == "yes"
    elapsed = time.perf_counter() - t0
    assert ask_comparative(g, f"is a{n} more tall than a0") == "no"
    assert elapsed < 10.0, f"end-to-end 20-chain took {elapsed:.1f}s"

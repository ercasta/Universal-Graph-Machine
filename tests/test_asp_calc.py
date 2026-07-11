"""
clingo scoped-calculator spike — constructive disjunction / exactly-one (docs/vision_agentic.md §3,
the RECOMMENDED NEXT in docs/handoff_redesign.md). This is the ONE reasoning capability the
stratified single-fixpoint engine cannot express (no head-disjunction, no model enumeration), so it
is DELEGATED to clingo behind the §8 materialized-`<call>` boundary (harneskills/asp.py).

The driving case is the gap the riddles pinned (memory `finding_riddles_probe`): a puzzle whose
answer must be derived POSITIVELY by ruling out alternatives ("exactly one door hides the prize; not
door1; not door2; therefore door3"). Closed-world elimination (`decide`) CANNOT do this — it would
wrongly conclude `not door3` too, since door3 is unproven. Reasoning by cases over the disjunction
forces door3; clingo's unique stable model entails it.

Three levels, cheapest first (Stage-1 de-risk discipline):
  1. the handler forces a unique winner from an exhausted disjunction (projection + solve + fold);
  2. it forces NOTHING when the disjunction is still ambiguous (soundness — no guessing);
  3. it composes IN the engine loop: `run(..., tools=asp.TOOLS)` services the call at rule
     quiescence and the folded-back winner re-seeds ordinary reasoning.
"""
import pytest

pytest.importorskip("clingo")   # the ASP calculator is the opt-in `asp` extra (pyproject.toml)

import ugm as h
from ugm import asp
from ugm.dispatch import _ensure, service_calls


def _rel(g, s, p, o):
    si = g.nodes_named(s)[0] if g.nodes_named(s) else g.add_node(s)
    oi = g.nodes_named(o)[0] if g.nodes_named(o) else g.add_node(o)
    g.add_relation(si, p, oi)


def _relation_exists(g, s_id, pname, o_id):
    """Does the raw edge  s_id -[pname]-> o_id  exist? (ported from the retired rewriter.py)."""
    for r in g.succ(s_id):
        if g.has_key(r, pname) and o_id in g.succ(r):
            return True
    return False


def _has(g, s, p, o):
    return any(_relation_exists(g, si, p, oi)
               for si in g.nodes_named(s) for oi in g.nodes_named(o))


def _doors(ruled_out):
    """Three doors, exactly one hides the prize (`holds`), with `ruled_out` forbidden. Returns the
    graph with an `asp_solve` call materialized (unserviced)."""
    g = h.Graph()
    for d in ("door1", "door2", "door3"):
        _rel(g, d, "is_a", "door")
    atoms = [g.nodes_named(d)[0] for d in ("door1", "door2", "door3")]
    outs = [g.nodes_named(d)[0] for d in ruled_out]
    pred = g.add_node("holds")
    asp.emit_exactly_one_call(g, atoms, outs, pred)
    return g


def test_exhausted_disjunction_forces_positive_winner():
    # not door1, not door2 -> the calculator FORCES door3 (a positive conclusion by exhaustion that
    # the stratified engine + CWA cannot reach).
    g = _doors(ruled_out=["door1", "door2"])
    service_calls(g, asp.TOOLS)
    assert _has(g, "door3", "holds", "<yes>")
    assert not _has(g, "door1", "holds", "<yes>")
    assert not _has(g, "door2", "holds", "<yes>")


def test_ambiguous_disjunction_forces_nothing():
    # only door1 ruled out -> door2 and door3 both remain live -> NO unique winner is entailed, so
    # the calculator soundly emits nothing (it never guesses among true alternatives).
    g = _doors(ruled_out=["door1"])
    service_calls(g, asp.TOOLS)
    assert not any(_has(g, d, "holds", "<yes>") for d in ("door1", "door2", "door3"))


def test_contradiction_forces_nothing():
    # everything ruled out -> unsatisfiable -> nothing forced (a contradiction yields no conclusion,
    # not an arbitrary one).
    g = _doors(ruled_out=["door1", "door2", "door3"])
    service_calls(g, asp.TOOLS)
    assert not any(_has(g, d, "holds", "<yes>") for d in ("door1", "door2", "door3"))


def test_engine_services_call_and_result_feeds_reasoning():
    # The real integration property: the call is serviced INSIDE the fixpoint loop (at rule
    # quiescence), and the folded-back winner re-seeds ordinary reasoning — a consumer rule fires on
    # the calculator's output. This is disjunction delegated to clingo, composed with native rules.
    g = _doors(ruled_out=["door1", "door2"])
    consumer = h.Rule(key="prize",
                      lhs=[h.Pat("?d", "holds", "<yes>")],
                      rhs=[h.Pat("?d", "is_a", "prize")])
    h.run_rules(g, [consumer], tools=asp.TOOLS)
    assert _has(g, "door3", "holds", "<yes>")     # calculator fired in the loop
    assert _has(g, "door3", "is_a", "prize")      # and its output drove further deduction


# --- rule-driven aggregation: RULES build the call from domain facts (no driver) ---

def _decision(ruled_out):
    """A DECISION declared as ordinary facts (no `emit_*` driver): exactly one `door` gets `holds`,
    with `ruled_out` forbidden. `asp.DISJUNCTION_RULES` build the call from these facts."""
    g = h.Graph()
    for d in ("door1", "door2", "door3"):
        _rel(g, d, "is_a", "door")
    dec = g.add_node("prize")
    g.add_relation(dec, "pred_of", _ensure(g, "holds"))
    g.add_relation(dec, "domain_of", _ensure(g, "door"))
    for d in ruled_out:
        g.add_relation(g.nodes_named(d)[0], "ruled_out", _ensure(g, "holds"))
    return g


def test_rules_build_the_call_and_force_winner():
    # No driver seeds the call: the aggregation rules materialize ONE call, accrete every door as an
    # atom and the ruled-out ones as `out`, and the calculator folds the winner back — the disjunction
    # calculator composed into pure rule-driven reasoning.
    g = _decision(ruled_out=["door1", "door2"])
    h.run_rules(g, asp.DISJUNCTION_RULES, tools=asp.TOOLS)
    assert _has(g, "door3", "holds", "<yes>")
    assert not _has(g, "door1", "holds", "<yes>")
    assert not _has(g, "door2", "holds", "<yes>")


def test_rules_driven_ambiguous_forces_nothing():
    # two doors still live -> no unique winner entailed -> nothing forced, same soundness as the
    # driver-seeded path, now through rule-built aggregation.
    g = _decision(ruled_out=["door1"])
    h.run_rules(g, asp.DISJUNCTION_RULES, tools=asp.TOOLS)
    assert not any(_has(g, d, "holds", "<yes>") for d in ("door1", "door2", "door3"))

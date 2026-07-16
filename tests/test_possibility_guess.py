"""
DEFEASIBLE GUESS — the positive-assumption sibling of `assumed-no` (docs/possibilistic.md decisions
5/6/8; open point D). A guess collapses to the most-possible disjunct WITHOUT opening branches: it
mints a visible `<guess>` record (pick + band + basis + every competitor NOT ruled out) and adopts
the picked WORLD (joints included) in its own pencil scope, so downstream reasoning is plain crisp
in-scope chaining. Wrong → retract: pencils swept, the record stays (marked), ink never touched.
"""
from ugm.attrgraph import AttrGraph
from ugm.production_rule import Rule, Pat
from ugm.cnl.rule_graph import write_rule
from ugm.chain import chain_sip, _facts_matching
from ugm.possibility import guess, retract_guess, render_guess, possibility
from ugm.cnl.uncertainty import load_uncertain


def _surgeon() -> AttrGraph:
    """Ink: x is a surgeon. One CHOICE, two correlated exclusive forks: male∧tall (0.7) /
    female∧short (0.3) — competitors must be genuinely EXCLUSIVE worlds (a shared `<choice>`),
    exactly what the `either…or` loader authors."""
    g = AttrGraph()
    g.add_relation(g.add_node("x"), "is_a", g.add_node("surgeon"))
    from ugm.possibility import add_fork
    choice = g.add_node("<choice>", control=True)
    add_fork(g, 0.7, [("x", "is", "male"), ("x", "is", "tall")], choice=choice)
    add_fork(g, 0.3, [("x", "is", "female"), ("x", "is", "short")], choice=choice)
    return g


def test_clear_max_guess_records_pick_and_competitors():
    """The gender-bias jump, made INSPECTABLE: the pick is the most-possible disjunct, and the
    record names the alternatives that were NOT ruled out — an assumption, not a derivation."""
    g = _surgeon()
    rec = guess(g, ("is", "x", None))
    assert rec["picked"] == "male" and rec["band"] == 0.7 and rec["basis"] == "clear-max"
    assert ("female", 0.3) in rec["alternatives"]          # the competitor is ON the record
    assert rec["node"] is not None                         # a visible, matchable epistemic act


def test_adoption_brings_the_joints_and_stays_pencil():
    """Adopting `male` enters the male∧tall WORLD: the co-scoped `tall` comes along (correlation),
    visible in the guess scope, invisible outside — and ink is untouched (nothing non-control)."""
    g = _surgeon()
    rec = guess(g, ("is", "x", None))
    scope = rec["node"]
    assert _facts_matching(g, "is", "x", "male", scope=scope)          # in-scope: the pick
    assert _facts_matching(g, "is", "x", "tall", scope=scope)          # in-scope: its joint
    assert not _facts_matching(g, "is", "x", "short", scope=scope)     # the OTHER world stayed out
    assert not _facts_matching(g, "is", "x", "male")                   # out of scope: still silent


def test_downstream_reasoning_is_crisp_in_the_guessed_world():
    """After the collapse there is ONE world, no bands: a plain crisp rule chains off the guess
    inside its scope — 'collapse without opening branches', on the existing scope machinery."""
    g = _surgeon()
    rec = guess(g, ("is", "x", None))
    rg = AttrGraph()
    write_rule(rg, Rule(key="d", lhs=[Pat("?p", "is", "male")], rhs=[Pat("?p", "is", "dangerous")]))
    chain_sip(g, ("is", "x", "dangerous"), rules=rg, scope=rec["node"])
    assert _facts_matching(g, "is", "x", "dangerous", scope=rec["node"])
    assert not _facts_matching(g, "is", "x", "dangerous")              # nothing leaked to ink


def test_tie_guesses_among_equals_and_says_so():
    """Decision 8: no unique max required — a tie still picks (deterministically), and the
    provenance does the heavier lifting: basis = tie, both equals on the record."""
    g = AttrGraph()
    load_uncertain(g, "x is either male or female")                    # even: 0.5 / 0.5
    rec = guess(g, ("is", "x", None))
    assert rec["basis"] == "tie"
    assert rec["picked"] == "female"                                   # deterministic: band, then name
    assert set(rec["alternatives"]) == {("female", 0.5), ("male", 0.5)}
    assert "guessed among equals" in render_guess(g, rec)


def test_certain_answer_is_a_read_not_a_guess():
    g = AttrGraph()
    g.add_relation(g.add_node("x"), "is", g.add_node("male"))          # ink
    rec = guess(g, ("is", "x", None))
    assert rec["basis"] == "certain" and rec["node"] is None           # nothing minted, nothing penned
    assert "a read, not a guess" in render_guess(g, rec)


def test_nothing_reachable_is_not_guess_territory():
    g = AttrGraph()
    g.add_node("x")
    assert guess(g, ("is", "x", None)) is None                         # assumed-no/unknown is check's job


def test_retract_sweeps_the_world_but_keeps_the_record():
    """Wrong jump → take it back: the adopted pencils go, the RECORD stays (marked retracted), and
    ink was never touched, so there is nothing else to undo."""
    g = _surgeon()
    rec = guess(g, ("is", "x", None))
    retract_guess(g, rec["node"])
    assert not _facts_matching(g, "is", "x", "male", scope=rec["node"])   # the world is swept
    assert g.has(rec["node"])                                             # the act is remembered
    assert "[RETRACTED]" in render_guess(g, rec)
    assert possibility(g, "is", "x", "male") == 0.7                       # the FORKS are untouched —
    assert possibility(g, "is", "x", "female") == 0.3                     # only the adoption was undone


def test_render_names_the_alternatives():
    g = _surgeon()
    rec = guess(g, ("is", "x", None))
    line = render_guess(g, rec)
    assert "x is male" in line and "female (unlikely)" in line
    assert "not ruled out" in line and "assumption, not a derivation" in line

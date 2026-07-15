"""
Possibilistic layer — assumption-relative NAF (docs/possibilistic.md S6).

Pins the spike finding: the SUPPOSE pencil/scope machinery ALREADY gives assumption-relative
negation-as-failure, with correlation (joints) via co-scoping and monotone-ink safety — so the
possibilistic layer needs NO new NAF/branching mechanism, only the graded-band increment (S5).

The correlated scenario `either male∧tall or female∧short` is modelled as two pencil scopes:
each world reasons over ink + its OWN pencil, so `not P` is decided per world. Visibility is
BINARY (in-scope / invisible-out), which is exactly the "silent until assumed" default; the
remaining work (a likeliness BAND on visibility) is deliberately NOT covered here.
"""
import ugm as h
from ugm import AttrGraph, Pat, Rule, chain_sip, HYPOTHESIS
from ugm.chain import _facts_matching
from ugm.suppose import _pencil


def _present(g, pred, s, o, scope) -> bool:
    """Is `s pred o` visible under `scope`? (the exact primitive `_nac_blocks` consults, chain.py:758:
    a NAC `not (s pred o)` BLOCKS iff this is True, so `not P` HOLDS iff this is False)."""
    return bool(_facts_matching(g, pred, s, o, scope=scope))


def _scenario():
    """Ink: x is a surgeon (certain). Two pencil forks off x: male∧tall / female∧short.
    Returns (graph, male_world_scope, female_world_scope)."""
    g = AttrGraph()
    x = g.add_node("x")
    g.add_relation(x, "is_a", g.add_node("surgeon"))            # ink / certain core

    male_world = g.add_node(HYPOTHESIS, control=True)
    female_world = g.add_node(HYPOTHESIS, control=True)
    male, tall = g.add_node("male"), g.add_node("tall")
    female, short = g.add_node("female"), g.add_node("short")
    _pencil(g, male_world, x, "is", male)                      # correlated -> co-scoped behind ONE fork
    _pencil(g, male_world, x, "is", tall)
    _pencil(g, female_world, x, "is", female)
    _pencil(g, female_world, x, "is", short)
    return g, male_world, female_world


def test_naf_is_scope_relative():
    """`not (x is <t>)` is decided per world: certain-world is agnostic (both forks absent), each
    fork blocks only its own attributes. This IS assumption-relative NAF, from the pencil machinery."""
    g, male_world, female_world = _scenario()

    # certain world: neither fork is visible -> `not male` AND `not female` both HOLD (honestly agnostic)
    assert not _present(g, "is", "x", "male", None)
    assert not _present(g, "is", "x", "female", None)

    # male-world: male present (NAC `not male` blocked), female still absent
    assert _present(g, "is", "x", "male", male_world)
    assert not _present(g, "is", "x", "female", male_world)

    # female-world: mirror image
    assert _present(g, "is", "x", "female", female_world)
    assert not _present(g, "is", "x", "male", female_world)


def test_correlation_is_joint_and_forks_do_not_leak():
    """male∧tall are joint (co-scoped: both visible in male-world) and the female fork never leaks
    into the male fork — joints via co-scoping, exclusivity via separate scopes (S1)."""
    g, male_world, female_world = _scenario()
    assert _present(g, "is", "x", "male", male_world)
    assert _present(g, "is", "x", "tall", male_world)          # co-scoped with male
    assert not _present(g, "is", "x", "short", male_world)     # the other fork's partner
    assert not _present(g, "is", "x", "female", male_world)    # no cross-contamination


def test_ink_stays_certain_under_every_scope():
    """The certain core is visible from inside any fork and is never disturbed (monotone ink)."""
    g, male_world, female_world = _scenario()
    for scope in (None, male_world, female_world):
        assert _present(g, "is_a", "x", "surgeon", scope)


def test_nac_in_a_rule_respects_scope_end_to_end():
    """The RULE path (not just the matcher): `?p is flagged when ?p is_a surgeon and not ?p is female`
    fires wherever `female` is not visible and is suppressed only inside the female fork. Same rule,
    world-dependent verdict — the NAC seeing scope-local facts is the whole mechanism (and the concrete
    shape of the gender-bias jump: absence-of-female drives the conclusion where the fork is unentered)."""
    rule = Rule(key="flag",
                lhs=[Pat("?p", "is_a", "surgeon")],
                rhs=[Pat("?p", "is", "flagged")],
                nac=[Pat("?p", "is", "female")])

    def flagged_under(scope) -> bool:
        g, male_world, female_world = _scenario()
        rg = AttrGraph()
        h.write_rule(rg, rule)
        run_scope = {None: None, "male": male_world, "female": female_world}[scope]
        chain_sip(g, ("is", "x", "flagged"), rules=rg, scope=run_scope)
        return _present(g, "is", "x", "flagged", run_scope)

    assert flagged_under(None) is True         # certain world: female absent -> NAC holds -> flagged
    assert flagged_under("male") is True        # male fork: female still absent -> flagged
    assert flagged_under("female") is False     # female fork: female visible -> NAC blocks -> NOT flagged

"""DISCOURSE REFERENCE — §24.3/§30, the Tier-3 item.

Spike: `bench/spike_discourse_reference.py` (25/25). Asserted here: the two things that make reference
sayable at all (the LEXEME bridge, inequality-as-data), the DECISION being definiteness rather than the
word, §17.F's two gaps becoming detectable, and the two honest limits (a wildcard merge must be authored;
substitution unions properties without collapsing identity).
"""
from __future__ import annotations

from units import Budget, Fact, Net, Subgraph, Triple, Var, branch, given, mint, role
from units import discourse as D
from units.vocab import lexeme

X, Y, Z = Var("x"), Var("y"), Var("z")
ROARS, LOUDLY = role("roars"), role("#loudly")
SLEEPS, NOW = role("sleeps"), role("#now")


def _run(value: Subgraph, substitution: bool = False):
    net = Net()
    net.spawn(given("discourse", value))
    D.declare_all(net, substitution=substitution)
    net.run(Budget(80000))
    return net


def _got(net: Net, pred) -> set:
    return {f for _, f in net.derived_anywhere(pred)}


def _scene():
    m_a, f_a = D.mention("lion", D.INDEFINITE, [(ROARS, LOUDLY)])
    m_the, f_the = D.mention("lion", D.DEFINITE, [(SLEEPS, NOW)])
    return m_a, m_the, D.utterance((m_a, f_a), (m_the, f_the))


# -- §30.1 the lexeme is the licensed bridge -------------------------------------------------------

def test_mentions_are_nameless_and_corefer_through_a_shared_lexeme():
    """⭐ The word *lion* is the FORM SET's; the lion is a nameless mention. So coref reaches across two
    utterances without resolving anything about the ENTITY by name."""
    m_a, m_the, value = _scene()
    assert m_a.name == "" and m_the.name == "" and m_a != m_the
    assert lexeme("lion") is lexeme("lion")
    net = _run(value)
    assert Fact(m_the, D.SAME_AS, m_a) in _got(net, D.SAME_AS)


def test_two_independently_minted_word_nodes_still_refuse_to_match():
    """⚠ The property namelessness is FOR — nothing in §30 reopens the by-name fusion §22.5 closed."""
    w1, w2 = mint("lion"), mint("lion")
    net = Net()
    net.spawn(given("d", Subgraph([Fact(mint(""), D.WORD, w1), Fact(mint(""), D.WORD, w2)])))
    net.declare("C", (Triple(X, D.WORD, Y), Triple(Z, D.WORD, Y)), Triple(X, D.SAME_AS, Z))
    net.run(Budget(4000))
    assert not any(f.s != f.o for f in _got(net, D.SAME_AS))


# -- §30.2 inequality dissolves --------------------------------------------------------------------

def test_inequality_is_naf_over_derived_identity():
    """⭐ `?x <self> ?x` + `Absent` IS `?x ≠ ?z` — no new primitive. And it only works because §28.1 made
    the negated premise's producer actually get WIRED."""
    m_a, m_the, value = _scene()
    net = _run(value)
    assert len(_got(net, D.SELF)) == 2
    assert not any(f.s == f.o for f in _got(net, D.SAME_AS))
    assert any("SELF" in p for p in net.producers["COREF#1"])


def test_without_the_inequality_guard_it_is_reflexive_junk():
    """So the guard is measured, not decorative."""
    _, _, value = _scene()
    net = Net()
    net.spawn(given("discourse", value))
    net.declare("C", (Triple(X, D.WORD, Y), Triple(Z, D.WORD, Y)), Triple(X, D.SAME_AS, Z))
    net.run(Budget(8000))
    assert any(f.s == f.o for f in _got(net, D.SAME_AS))


# -- the decision is definiteness ------------------------------------------------------------------

def test_two_indefinites_of_the_same_word_are_not_merged():
    """⭐ *'A lion roars. A lion sleeps.'* — two different lions. Keying on the lexeme alone would merge
    them: not a substrate failure but a WRONG DECISION, which is what §24.3 means by *decided*."""
    net = _run(D.utterance(D.mention("lion", D.INDEFINITE, [(ROARS, LOUDLY)]),
                           D.mention("lion", D.INDEFINITE, [(SLEEPS, NOW)])))
    assert _got(net, D.SAME_AS) == set()


def test_the_definite_points_at_the_indefinite_and_not_the_reverse():
    m_a, m_the, value = _scene()
    net = _run(value)
    assert {(f.s, f.o) for f in _got(net, D.SAME_AS)} == {(m_the, m_a)}


# -- §17.F's two logged gaps become detectable -----------------------------------------------------

def test_two_antecedents_for_one_definite_is_a_fact():
    """⭐ §17.F logged uniqueness as having NO MECHANISM (*"two cars matched; both would be derived over,
    silently"*). It is now `<ambiguous>` — sayable, though still not resolved."""
    net = _run(D.utterance(D.mention("lion", D.INDEFINITE), D.mention("lion", D.INDEFINITE),
                           D.mention("lion", D.DEFINITE)))
    assert len(_got(net, D.AMBIGUOUS)) == 1
    assert len(_got(net, D.SAME_AS)) == 2


def test_one_antecedent_is_not_flagged_ambiguous():
    _, _, value = _scene()
    assert _run(value).derived_anywhere("<ambiguous>") == set()


def test_an_unresolved_definite_is_positively_marked():
    """⭐ §17.F: reference failure was *indistinguishable from negation*. Presupposition failure no longer
    collapses into falsity."""
    net = _run(D.utterance(D.mention("lion", D.DEFINITE, [(SLEEPS, NOW)])))
    assert len(_got(net, D.DANGLING)) == 1
    assert _got(net, D.SAME_AS) == set()


def test_a_resolved_definite_is_not_dangling():
    _, _, value = _scene()
    net = _run(value)
    assert _got(net, D.DANGLING) == set()
    assert len(_got(net, D.RESOLVED)) == 1


# -- §30.3 / §30.4 the two honest limits -----------------------------------------------------------

def test_a_wildcard_merge_is_not_wired_by_inference():
    """⚠ §30.3. The wildcard atom is satisfied by ANY fact — including the rule's own control facts — so no
    *unmet* test can detect that it needs the discourse. Wiring for a wildcard LHS must be AUTHORED."""
    _, _, value = _scene()
    net = _run(value, substitution=True)
    assert not any(f.p == ROARS for i in net.instances["SUBST"] for f in net.units[i].output)


def _authored_merge():
    m_a, m_the, value = _scene()
    net = Net()
    net.spawn(given("discourse", value))
    D.declare_all(net)
    net.declare("SYMM", *D.symmetry_rule())
    net.run(Budget(40000))
    net.spawn(branch("M0"))
    net.wire("discourse", "M0")
    net.wire("COREF#1", "M0")
    for i in net.instances["SYMM"]:
        net.wire(i, "M0")               # EVERY premise in ONE value — a rule's output never carries its input
    net.declare("SUBST", *D.substitution_rule())
    net.run(Budget(60000))
    out = set()
    for u in net.units.values():
        out |= set(u.output)
    return net, m_a, m_the, out


def test_an_authored_merge_substitutes_in_both_directions():
    net, m_a, m_the, out = _authored_merge()
    assert Fact(m_the, ROARS, LOUDLY) in out          # needs `symmetry_rule` — the decision is asymmetric
    assert Fact(m_a, SLEEPS, NOW) in out
    assert net.wellformed() == []


def test_substitution_unions_properties_without_collapsing_identity():
    """⚠ §30.4. §17.D designed the merge as a delta that SUBSTITUTES B→A, which needs REMOVAL — and a rule
    cannot remove. So both mentions survive: sound for MATCHING, silent for COUNTING."""
    _, _, _, out = _authored_merge()
    assert len({f.s for f in out if f.p == ROARS}) == 2


def test_two_chains_may_disagree_about_identity():
    """⭐ §17.D's prediction, measured: downstream of the merge they are one, upstream they remain two."""
    m1, f1 = D.mention("lion", D.INDEFINITE, [(ROARS, LOUDLY)])
    m2, f2 = D.mention("lion", D.INDEFINITE)
    net = Net()
    net.spawn(given("d", D.utterance((m1, f1), (m2, f2))))
    net.spawn(branch("SAME", add=[Fact(m1, D.SAME_AS, m2)]))
    net.wire("d", "SAME")
    net.spawn(branch("DIFF", add=[]))
    net.wire("d", "DIFF")
    net.declare("SUBST", *D.substitution_rule())
    net.run(Budget(60000))
    same = any(Fact(m2, ROARS, LOUDLY) in set(net.units[i].output) for i in net.instances["SUBST"])
    assert same
    assert Fact(m2, ROARS, LOUDLY) not in set(net.units["DIFF"].output)


def test_only_what_a_carrier_actually_received_counts_as_a_drop():
    """⚠ §30.3's second defect. `restores_a_drop` compared *facts the ancestor has and the descendant does
    not*, which under subset output is most of them — so an ordinary merge downstream of a rule was flagged
    as a bypass. The drop is what ARRIVED and did not leave."""
    net, *_ = _authored_merge()
    assert net.restores_a_drop("M0") is None
    assert net.wellformed() == []

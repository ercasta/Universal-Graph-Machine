"""
The reference ISA machine's own derivations on the positive, monotone, non-graded fragment
(docs/reference/isa_reference.md "Next slice").

For each rule + fact set: lower the `Rule` to an ISA program, bridge the graph to the label-less
`AttrGraph`, run the reference machine to fixpoint, and assert the derived relation SET against a
FIXED expected value (computed by hand from the rule + facts). Equivalence with the previous
(rewriter / name-based) generation is NOT a correctness target (implementation_plan.md, 2026-07-10
ratification) — these pin the ISA machine's own behavior directly.

Note on triple extraction: `derived_triples` structurally over-approximates a "relation" (any node
that sits between a predecessor and a successor), so the expected sets below include that noise
(e.g. `(can_get, vanilla, in_stock)` alongside the intended `(alice, can_get, vanilla)`) — pinned
as observed. We ALSO assert membership of the intended triple, for legibility.
"""
import pytest

import ugm as h
from ugm import Pat, Rule, GradedCondition
from ugm import to_attrgraph, lower_rule, run_to_fixpoint, derived_triples
from ugm.lowering import lower_lhs, lower_graded, Unlowerable
from ugm.machine import Machine


# ---------------------------------------------------------------------------
# Helpers — build a KB graph, run the ISA machine, extract derived relation triples
# ---------------------------------------------------------------------------

def _build(facts: list[tuple[str, str, str]]) -> h.Graph:
    """One node per distinct name (a loaded KB), one relation per fact."""
    g = h.Graph()
    ids: dict[str, str] = {}

    def node(name: str) -> str:
        if name not in ids:
            ids[name] = g.add_node(name)
        return ids[name]

    for s, p, o in facts:
        g.add_relation(node(s), p, node(o))
    return g


def _machine_derived(g, rule) -> set[tuple[str, str, str]]:
    ag, _ = to_attrgraph(g)
    init = derived_triples(ag)
    program = lower_rule(rule)
    run_to_fixpoint(ag, program, rule.bound_names())
    return derived_triples(ag) - init


# ---------------------------------------------------------------------------
# Rule A — a 2-clause conjunction (non-recursive), with a literal object
# ---------------------------------------------------------------------------

CAN_GET = Rule(
    key="can_get",
    lhs=[Pat("?c", "wants", "?f"), Pat("?f", "in_stock", "yes")],
    rhs=[Pat("?c", "can_get", "?f")],
)


def test_conjunction_with_literal_object_agrees():
    facts = [
        ("alice", "wants", "vanilla"), ("vanilla", "in_stock", "yes"),
        ("bob", "wants", "kale"),                       # kale not in stock -> no derivation
    ]
    derived = _machine_derived(_build(facts), CAN_GET)
    # Phase 2.3: the spurious `("can_get", "vanilla", "in_stock")` (entity `vanilla` mis-read as a
    # relation by the old name-based `derived_triples`) is gone — a relation is now its predicate key.
    assert derived == {("alice", "can_get", "vanilla")}
    assert ("alice", "can_get", "vanilla") in derived
    assert not any(t[1] == "can_get" and t[0] == "bob" for t in derived)


# ---------------------------------------------------------------------------
# Rule B — transitivity (RECURSIVE): the fixpoint driver + fired-suppression
# ---------------------------------------------------------------------------

TRANS = Rule(
    key="trans",
    lhs=[Pat("?a", "isa", "?b"), Pat("?b", "isa", "?c")],
    rhs=[Pat("?a", "isa", "?c")],
)


def test_transitive_closure_agrees():
    facts = [("x", "isa", "y"), ("y", "isa", "z"), ("z", "isa", "w")]
    derived = _machine_derived(_build(facts), TRANS)
    assert derived == {("x", "isa", "z"), ("x", "isa", "w"), ("y", "isa", "w")}
    # the closure beyond the three base edges
    assert ("x", "isa", "z") in derived
    assert ("x", "isa", "w") in derived
    assert ("y", "isa", "w") in derived


# ---------------------------------------------------------------------------
# Rule C — a 4-clause join where the last clause has BOTH endpoints bound (SAME)
# ---------------------------------------------------------------------------

HAZARD = Rule(
    key="hazard",
    lhs=[
        Pat("?m", "kind", "mutation"),
        Pat("?m", "mutate", "?c"),
        Pat("?loop", "contain", "?m"),
        Pat("?loop", "consume", "?c"),          # ?loop and ?c both already bound -> SAME
    ],
    rhs=[Pat("?loop", "hazard", "?m")],
)

_HAZARD_FACTS = [
    ("del", "kind", "mutation"),
    ("loop", "contain", "del"),
    ("loop", "consume", "qs"),
]


def test_four_clause_join_with_same_fires_and_agrees():
    facts = _HAZARD_FACTS + [("del", "mutate", "qs")]   # mutates the consumed collection
    derived = _machine_derived(_build(facts), HAZARD)
    # Phase 2.3: the spurious `("hazard", "del", "kind")`/`("hazard", "del", "mutate")` (the entity
    # `del` mis-read as a relation by the old name-based `derived_triples`) are gone — only the real
    # HAZARD head remains, a relation identified by its predicate key.
    assert derived == {("loop", "hazard", "del")}
    assert ("loop", "hazard", "del") in derived


def test_four_clause_join_near_miss_agrees():
    facts = _HAZARD_FACTS + [("del", "mutate", "other")]  # mutates a DIFFERENT collection
    derived = _machine_derived(_build(facts), HAZARD)
    assert derived == set()                               # the machine derives nothing
    assert not any(t[1] == "hazard" for t in derived)


# ---------------------------------------------------------------------------
# Graded α-cut — GRADE reproduces `rewriter.graded_degree` (gate AND degree)
# ---------------------------------------------------------------------------

# A graded rule over plain relations: a customer whose `urgency` clears the α-cut is fast-tracked
# for an in-stock want. (Plain-relation RHS between bound vars — the graded SEMANTICS is the point;
# literal/concept RHS endpoints are a separate deferred item.)
FAST = Rule(
    key="fast",
    lhs=[Pat("?c", "wants", "?f"), Pat("?f", "in_stock", "yes")],
    rhs=[Pat("?c", "fast", "?f")],
    graded=[GradedCondition("?c", {"urgency": 1.0}, 0.5)],
)


def _graded_graph():
    g = _build([
        ("alice", "wants", "vanilla"), ("vanilla", "in_stock", "yes"),
        ("bob", "wants", "choc"), ("choc", "in_stock", "yes"),
    ])
    # embeddings: alice clears the α-cut (0.9 ≥ 0.5), bob does not (0.3 < 0.5)
    g.set_embedding(g.nodes_named("alice")[0], {"urgency": 0.9})
    g.set_embedding(g.nodes_named("bob")[0], {"urgency": 0.3})
    return g


def test_graded_alpha_cut_gate_and_degree_match_engine():
    g = _graded_graph()

    # the lowered program's match phase (structure + GRADE): score per surviving state, gated by
    # the α-cut (bob's 0.3 < the 0.5 threshold so he never appears).
    ag, _ = to_attrgraph(g)
    match_ops = lower_lhs(FAST) + lower_graded(FAST)
    machine: dict[str, float] = {}
    for st in Machine().match(ag, match_ops):
        name = ag.get_attr(st.regs["?c"], "name").value
        machine[name] = st.score

    assert set(machine) == {"alice"}                       # only alice clears the cut
    assert machine["alice"] == pytest.approx(0.9)          # degree == alice's raw urgency score


def test_graded_rule_derivation_agrees():
    # end-to-end: the derived relation SET, pinned directly (the α-cut gates which fire)
    derived = _machine_derived(_graded_graph(), FAST)
    # Phase 2.3: `derived_triples` identifies a relation by its domain predicate KEY, so the old
    # spurious `("fast", "vanilla", "in_stock")` — an artifact of mis-reading the ENTITY `vanilla`
    # (which gained the `fast` rel node as a predecessor) as a relation — is gone.
    assert derived == {("alice", "fast", "vanilla")}
    assert ("alice", "fast", "vanilla") in derived
    assert not any(t[0] == "bob" for t in derived)


# ---------------------------------------------------------------------------
# The lowering still refuses what is outside the fragment (explicit, never silent)
# ---------------------------------------------------------------------------

def test_lowering_refuses_inverted_graded_and_nac():
    inverted = Rule(key="g", lhs=[Pat("?c", "wants", "?f")], rhs=[Pat("?c", "vip", "?f")],
                    graded=[GradedCondition("?c", {"urgency": 1.0}, 0.5, inverted=True)])
    with pytest.raises(Unlowerable):
        lower_rule(inverted)

    nac = Rule(key="n", lhs=[Pat("?c", "wants", "?f")], rhs=[Pat("?c", "vip", "?f")],
               nac=[Pat("?c", "banned", "?f")])
    with pytest.raises(Unlowerable):
        lower_rule(nac)


# ---------------------------------------------------------------------------
# Variable RHS predicates — the dynamic-key MINT (`predicates-are-keys`, first slice)
# ---------------------------------------------------------------------------

DYN_FACTS = [("utt1", "says", "barks"), ("utt1", "about", "rex"),
             ("utt2", "says", "purrs"), ("utt2", "about", "tom")]

#: The predicate comes from the MATCHED node, not from the rule text.
DYN_RULE = Rule(key="dyn", lhs=[Pat("?p", "says", "?w"), Pat("?p", "about", "?o")],
                rhs=[Pat("?o", "?w", "yes")])


def test_a_variable_rhs_predicate_writes_the_matched_word_as_the_predicate():
    derived = _machine_derived(_build(DYN_FACTS), DYN_RULE)
    assert ("rex", "barks", "yes") in derived
    assert ("tom", "purrs", "yes") in derived


def test_a_dynamic_key_head_still_dedups():
    """`dedup` must resolve the DYNAMIC key, or a variable-predicate rule mints a fresh relation
    node on every firing and the graph never reaches a fixpoint -- exactly the accretion `dedup`
    exists to prevent, reintroduced through the back door."""
    ag, _ = to_attrgraph(_build(DYN_FACTS))
    program = lower_rule(DYN_RULE)
    run_to_fixpoint(ag, program, DYN_RULE.bound_names())
    settled = len(list(ag.nodes()))
    for _ in range(3):
        run_to_fixpoint(ag, program, DYN_RULE.bound_names())
    assert len(list(ag.nodes())) == settled, "re-running a variable-predicate rule must add nothing"


def test_an_rhs_only_predicate_variable_is_still_rejected():
    """Predicate INVENTION stays out: with no LHS binding there is no node to take a name from."""
    with pytest.raises(Unlowerable, match="not bound by the LHS"):
        lower_rule(Rule(key="bad", lhs=[Pat("?s", "is", "?o")], rhs=[Pat("?s", "?w", "?o")]))


# ---------------------------------------------------------------------------
# `Band` — the declared RHS effect that authors a possibilistic fork FROM A RULE
# ---------------------------------------------------------------------------

def _banded_rule(degree=0.7):
    from ugm.production_rule import Band
    return Rule(key="hedge", lhs=[Pat("?s", "hedged_has", "?o")], rhs=[Pat("?s", "has", "?o")],
                bands=[Band(var="<hypothesis>?", key="<likeliness>", degree=degree, scope=("?s",))])


def _seeded():
    from ugm import AttrGraph
    g = AttrGraph()
    g.add_relation(g.add_node("lion"), "hedged_has", g.add_node("mane"))
    return g


def test_a_rule_can_author_a_banded_fork():
    """THE POINT OF `Band`: a rule RHS is triples, so it could not write the GRADED attribute a
    possibilistic fork is made of — hedged facts were reachable only from a Python driver.

    The acceptance criterion is PARITY, not merely 'a band appears': the rule must land the SAME
    representation `possibility.add_fork` does, so the banded readers cannot tell them apart. A
    parallel-but-different encoding would be worse than no feature."""
    from ugm import AttrGraph
    from ugm.lowering import run_bank
    from ugm.possibility import add_fork, possibility, all_fork_bands

    authored = AttrGraph()
    add_fork(authored, 0.7, [("lion", "has", "mane")])

    derived = _seeded()
    run_bank(derived, [_banded_rule()])

    assert sorted(all_fork_bands(derived).values()) == sorted(all_fork_bands(authored).values())
    assert possibility(derived, "has", "lion", "mane") == possibility(authored, "has", "lion", "mane")
    assert possibility(derived, "has", "lion", "mane") == 0.7


def test_a_penned_head_is_control_and_scope_tagged():
    """A hedged claim must not be INK. The penned relation is a CONTROL node carrying the `<scope>`
    tag pointing at the fork — `suppose._pencil`'s shape, reached declaratively."""
    from ugm.apply import SCOPE
    from ugm.lowering import run_bank
    g = _seeded()
    run_bank(g, [_banded_rule()])
    rel = next(n for n in g.nodes() if g.has_key(n, "has"))
    assert g.get_attr(rel, SCOPE) is not None, "a penned head must carry its scope tag"
    scope = g.get_attr(rel, SCOPE).value
    assert g.get_attr(scope, "<likeliness>").value == 0.7


def test_emit_value_reg_is_valued_only():
    """A node id is DATA, never a degree — the guard exists so a graded misuse fails loudly rather
    than coercing an id into a float."""
    from ugm import AttrGraph
    from ugm.machine import EMIT, State, ProgramError
    g = AttrGraph()
    n = g.add_node("x")
    with pytest.raises(ProgramError):
        Machine().apply(g, [EMIT("_a", "<likeliness>", "", value_reg="_b")],
                        State({"_a": n, "_b": n}))


def test_a_band_scope_naming_no_rhs_subject_is_unlowerable():
    """Loud rather than silent: penning behind a token the RHS never writes would quietly author a
    fork holding nothing."""
    from ugm.production_rule import Band
    r = Rule(key="bad", lhs=[Pat("?s", "hedged_has", "?o")], rhs=[Pat("?s", "has", "?o")],
             bands=[Band(var="<hypothesis>?", key="<likeliness>", degree=0.5, scope=("?nope",))])
    with pytest.raises(Unlowerable):
        lower_rule(r)


def test_a_band_is_idempotent_across_runs():
    """A bank that re-runs must not accrete — and `Band` mints a SCOPE, which has neither of the two
    existing identities (no NAME to intern by, no subject/object edges to dedup on).

    This was the family's FIFTH instance (`<span>?`, the remint mark, `intern_described`,
    `<contradiction>?`): the scope skolem minted fresh per firing and orphaned one node per pass
    (5 -> 6 -> 7 -> 8). It was SILENT — the penned head deduped, so the fork count stayed right and
    every band reader still answered correctly. It mattered because the grammar fold re-runs its
    banks over the whole graph on every utterance.

    Fixed at the source by `MINT(reuse_attr_of=)`: the scope's identity is the `<scope>` tag its own
    penned fact already carries, so a found head yields a found scope. (This test previously pinned
    the defect and said to invert it once fixed — this is that inversion.)"""
    from ugm.lowering import run_bank
    from ugm.possibility import all_fork_bands, possibility
    g = _seeded()
    counts = []
    for _ in range(4):
        run_bank(g, [_banded_rule()])
        counts.append(len(list(g.nodes())))
    assert len(set(counts)) == 1, f"re-running a band rule must be FLAT; got {counts}"
    assert len(all_fork_bands(g)) == 1
    assert possibility(g, "has", "lion", "mane") == 0.7, "and still answers after N runs"


def test_a_band_can_pen_without_a_degree():
    """GENERALIZATION (2026-07-20): the degree is an optional DECORATION on "pen these heads behind
    this node" — the pencil SCOPE is the primitive.

    Attribution is the second user and the reason this came off before it landed: *some naturalists
    consider the lion a cat* wants the same scope MINUS the degree, plus an ordinary `held_by`
    triple. Had `key`/`degree` stayed mandatory, attribution would have had to invent a degree it has
    no basis for — a fabricated 0.5, which is precisely the silent default the hedge path refuses to
    make (an undeclared band is SKIPPED there, never defaulted).

    Pins BOTH halves: the head is penned (control + `<scope>`-tagged, so it is not ink), and NO
    graded attribute is written onto the scope node."""
    from ugm import AttrGraph
    from ugm.apply import SCOPE
    from ugm.lowering import run_bank
    from ugm.production_rule import Band

    g = _seeded()
    run_bank(g, [Rule(key="attrib", lhs=[Pat("?s", "hedged_has", "?o")],
                      rhs=[Pat("?s", "has", "?o")],
                      bands=[Band(var="<attribution>?", scope=("?s",))])])

    penned = [(r, o) for n in g.nodes_named("lion") for r, o in g.relations_from(n)
              if g.predicate(r) == "has"]
    assert penned, "the head was not written at all"
    rel, _o = penned[0]
    assert g.is_control(rel), "an ungraded Band must still PEN — a penned fact is not ink"
    assert g.has_key(rel, SCOPE), (
        "the penned head carries no `<scope>` tag, so it belongs to no scope")

    scope_node = g.nodes_named("<attribution>")
    assert scope_node, "no scope node was minted"
    from ugm.possibility import LIKELINESS
    assert not g.has_key(scope_node[0], LIKELINESS), (
        "an ungraded Band fabricated a degree on its scope node")


# ---------------------------------------------------------------------------
# SEMI-NAIVE ROUNDS — the fixpoint must be identical, only cheaper
# ---------------------------------------------------------------------------

def _cascade_bank():
    """A bank that genuinely CASCADES: each rule's premise is the previous rule's head, so reaching
    the fixpoint REQUIRES several rounds. This is the shape semi-naive must not truncate — a version
    that simply stopped re-matching would pass any single-round test."""
    return [
        Rule(key="c1", lhs=[Pat("?x", "a", "?y")], rhs=[Pat("?x", "b", "?y")]),
        Rule(key="c2", lhs=[Pat("?x", "b", "?y")], rhs=[Pat("?x", "c", "?y")]),
        Rule(key="c3", lhs=[Pat("?x", "c", "?y")], rhs=[Pat("?x", "d", "?y")]),
        Rule(key="c4", lhs=[Pat("?x", "d", "?y")], rhs=[Pat("?x", "e", "?y")]),
    ]


def _seeded_cascade():
    from ugm import AttrGraph
    g = AttrGraph()
    for n in ("p", "q"):
        g.add_relation(g.add_node(n), "a", g.add_node(f"{n}_o"))
    return g


def test_semi_naive_reaches_the_same_fixpoint_as_the_naive_loop():
    """⭐ THE DIFFERENTIAL GATE for the round-level optimization.

    `run_bank` re-matched EVERY rule in EVERY round. Profiled on the grammar fold: the slot bank ran
    5.1 rounds x 59 rules = ~301 match calls to produce ~20 firings. The rounds are legitimate (slot
    percolation cascades); re-matching every rule in each is not. Semi-naive re-matches only rules
    whose LHS mentions a predicate something actually wrote.

    SOUNDNESS rests on MONOTONICITY: adding facts can only make a NAC's witness more likely, so a NAC
    can never ENABLE a rule it previously blocked. A bank with `drop` breaks that and opts out.

    This asserts the FIXPOINT, not the speed: the full cascade must be derived either way."""
    from ugm.lowering import run_bank, derived_triples
    a, b = _seeded_cascade(), _seeded_cascade()
    fa = run_bank(a, _cascade_bank(), semi_naive=False)
    fb = run_bank(b, _cascade_bank(), semi_naive=True)
    assert sorted(derived_triples(a)) == sorted(derived_triples(b)), "semi-naive changed the fixpoint"
    assert fa == fb, f"firing counts differ: naive {fa} vs semi {fb}"
    # ... and the cascade really did run to the end (guards the test itself).
    assert ("p", "e", "p_o") in derived_triples(b), "the cascade did not reach its fixpoint"


def test_semi_naive_still_fires_a_rule_whose_premise_appears_later():
    """The precise failure a naive 'only match once' optimization would have: a rule whose premise
    predicate is written by a LATER rule in bank order. It must still fire, which means the dirty-set
    has to survive across rounds rather than being consulted only on the first pass."""
    from ugm.lowering import run_bank, derived_triples
    from ugm import AttrGraph
    g = AttrGraph()
    g.add_relation(g.add_node("p"), "a", g.add_node("o"))
    # deliberately REVERSED bank order: the consumer is listed before its producer
    bank = [Rule(key="consumer", lhs=[Pat("?x", "mid", "?y")], rhs=[Pat("?x", "final", "?y")]),
            Rule(key="producer", lhs=[Pat("?x", "a", "?y")], rhs=[Pat("?x", "mid", "?y")])]
    run_bank(g, bank, semi_naive=True)
    assert ("p", "final", "o") in derived_triples(g), (
        "a consumer listed before its producer never re-ran — the dirty set is not surviving rounds")

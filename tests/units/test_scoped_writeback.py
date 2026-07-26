"""SCOPED WRITE-BACK — *"assuming x, Paul is eligible"* (`model.md` §6, §12 invariant 2).

**The bug this closes.** The circuit honoured the tunnel: a conclusion reached inside a supposition
could not leave except through the end marker. But the loop then unioned every recalled statement's
output into the world, so the hypothetical conclusion was written back **flatly** — the persistent graph
asserted *"Paul is eligible, certain"*, true only under a hypothesis nobody recorded.

**Why that was a design gap rather than a slip.** §6 keeps scope in two places and says why neither is
redundant — the circuit holds the tunnel, the graph holds the nesting — and then states the bridge:
*"each turn re-derives the tunnel from the graph's nesting, and write-back maps a tunnel position back
into nesting."* Only the first direction had been built. This is the second.

**What it is not.** It does not make rules aware of scope. A chain guard does not discard the context,
and it does not hand the context to anyone who could match on it — it **moves the assembler's pointer**
one level deeper, so a conclusion minted downstream is placed under a containment node. No pattern in
any rule here mentions a scope, which is §12 invariant 1 and is asserted below.
"""
from __future__ import annotations

from units import Description, assemble, atoms, turn
from units.assemble import decode_pattern, roles_of
from tests.units.test_loop import world_and_goal


def scoped_library() -> Description:
    """The §10 walkthrough's shape: a rule that concludes in the base world, and the same rule again
    inside an explicit supposition that declares the containment it establishes."""
    d = Description()

    def verdict_unit():
        return d.unit("verdict",
                      (d.atom("st", name="standing", graded="good"),),
                      (d.mint("gets", args=(("about", "st"),), graded="eligible"),))

    d.statement("standing-rule", d.unit(
        "standing-rule",
        (d.atom("lp", name="late-payment", graded="minor",
                out=(d.role("agent", d.atom("p")),)),),
        (d.mint("standing", args=(("agent", "p"),), graded="good"),)))

    d.statement("verdict-plain", verdict_unit())

    settle = d.statement("settle", d.unit(
        "settle", (d.atom("s", name="standing", graded="good"),),
        (d.stamp("s", "good", "certain"),)))
    d.statement("suppose-settled", settle, d.statement("verdict-inner", verdict_unit()),
                scope="assuming-payments-settled")
    return d


def verdicts(g):
    return [n for n in g.nodes if g.attr(n, "name") == "gets"]


def members_of(g, scope_name):
    """Everything physically under the named scope node."""
    scope = [n for n in g.nodes if g.attr(n, "name") == scope_name]
    if not scope:
        return []
    return roles_of(g, scope[0], "member")


# --------------------------------------------------------------------------------------------
# 1. The conclusion lands under the assumption
# --------------------------------------------------------------------------------------------

def test_a_hypothetical_conclusion_is_physically_under_the_assumption():
    world, _ = world_and_goal()

    result = turn(world, scoped_library().g, max_steps=6)

    inside = members_of(result.world, "assuming-payments-settled")
    assert len(inside) == 1
    assert result.world.attr(inside[0], "name") == "gets"
    assert result.world.degree(inside[0], "eligible") == "certain"


def test_the_base_world_conclusion_is_not_under_it():
    """The contrast that makes it meaningful: the marginal verdict, reached without any supposition, is
    not a member of the assumption."""
    world, _ = world_and_goal()

    result = turn(world, scoped_library().g, max_steps=6)

    inside = set(members_of(result.world, "assuming-payments-settled"))
    outside = [v for v in verdicts(result.world) if v not in inside]

    assert len(outside) == 1
    assert result.world.degree(outside[0], "eligible") == "unlikely"


def test_nothing_is_asserted_flatly_that_was_only_true_under_an_assumption():
    """The bug, stated as the property it violated. Every `certain` verdict must be contained; only the
    unconditioned one may float free."""
    world, _ = world_and_goal()

    result = turn(world, scoped_library().g, max_steps=6)
    inside = set(members_of(result.world, "assuming-payments-settled"))

    for v in verdicts(result.world):
        if result.world.degree(v, "eligible") == "certain":
            assert v in inside, "a hypothetical conclusion escaped into the world as fact"


def test_a_scope_that_concludes_nothing_leaves_no_node_behind():
    """The pointer mints lazily. A supposition nobody reached inside should not litter the graph with
    an empty containment."""
    world, _ = world_and_goal()
    d = Description()
    d.statement("idle", d.unit("idle", (d.atom("x", name="unicorn"),),
                               (d.mint("sighting", args=(("of", "x"),)),)),
                scope="assuming-unicorns")

    result = turn(world, d.g, max_steps=3)

    assert not any(result.world.attr(n, "name") == "assuming-unicorns" for n in result.world.nodes)


# --------------------------------------------------------------------------------------------
# 2. Nesting: the guard moves the pointer, it does not reset it
# --------------------------------------------------------------------------------------------

def test_a_supposition_inside_a_supposition_lands_two_levels_down():
    """*"Assuming x, and then assuming y, …"* — the inner containment is itself a member of the outer
    one, so the nesting in the graph mirrors the nesting in the description."""
    world, _ = world_and_goal()
    d = Description()
    inner = d.statement("inner", d.unit(
        "inner-rule", (d.atom("lp", name="late-payment", graded="minor"),),
        (d.mint("note", args=(("about", "lp"),)),)),
        scope="assuming-inner")
    d.statement("outer", inner, scope="assuming-outer")

    result = turn(world, d.g, max_steps=3)

    outer_members = members_of(result.world, "assuming-outer")
    inner_members = members_of(result.world, "assuming-inner")

    # Exactly one inner assumption, held by exactly one outer one — scope identity is stable across
    # steps even though the circuit is rebuilt each time.
    assert [result.world.attr(n, "name") for n in outer_members] == ["assuming-inner"]
    assert len([n for n in result.world.nodes if result.world.attr(n, "name") == "assuming-inner"]) == 1
    # The conclusion is two levels down. (Its *multiplicity* is the separate accretion issue — no
    # cooldown here — so the names are what this test is about, not the count.)
    assert {result.world.attr(n, "name") for n in inner_members} == {"note"}


def test_an_unscoped_statement_inherits_the_context_it_was_reached_in():
    """A guard does not discard the context. `verdict-inner` declares no scope of its own, yet its
    conclusion still lands inside the supposition that contains it."""
    world, _ = world_and_goal()
    d = scoped_library()

    asm = assemble(d.g)

    assert "assuming-payments-settled" in asm.scopes
    assert asm.scopes["assuming-payments-settled"].parent is None


# --------------------------------------------------------------------------------------------
# 3. CHAINING UNDER AN ASSUMPTION — the case that motivated all of this
# --------------------------------------------------------------------------------------------

def wings_library() -> Description:
    """*"Assuming x has wings, x is a bird."* / *"If x is a bird, x can fly."*

    The second rule declares no scope: it is a general truth, and it must apply **wherever its premise
    holds** — including inside an assumption it knows nothing about."""
    d = Description()
    d.statement("wings-bird", d.unit(
        "wings-bird",
        (d.atom("x", name="thing", graded="winged"),),
        (d.mint("bird", args=(("of", "x"),)),)),
        scope="assuming-wings")
    d.statement("bird-flies", d.unit(
        "bird-flies",
        (d.atom("b", name="bird", out=(d.role("of", d.atom("y")),)),),
        (d.mint("can-fly", args=(("of", "y"),)),)))
    return d


def winged_world():
    from units import EMPTY, named
    g, thing = named(EMPTY, "thing")
    g = g.with_degree(thing, "winged", "likely")
    d = Description()
    d.goal("can-it-fly", d.atom(name="can-fly"))
    return g.union(d.g), thing


def test_a_general_rule_chains_onto_a_conclusion_made_under_an_assumption():
    """The derivation runs *"has wings"* → (under the assumption) *"is a bird"* → *"can fly"*, and the
    second rule was never told about the assumption.

    It works because a rule that declares no scope is **instantiated once per active context**, each
    instance fed only what is visible there (`graph.visible_at`). The instance running inside
    `assuming-wings` sees the supposed bird; the one running in the base world does not."""
    world, _ = winged_world()

    result = turn(world, wings_library().g, max_steps=6)

    flying = [n for n in result.world.nodes if result.world.attr(n, "name") == "can-fly"]
    assert flying, "the chain did not complete"


def test_and_the_chained_conclusion_stays_inside_the_assumption():
    """⚠ The half that was broken. Recording containment is not enough: if every rule can still *see*
    into an assumption, a base-world rule matches the supposed bird and concludes flatly that it flies.
    Then the graph asserts *"it can fly"* about a thing whose birdhood was never established."""
    world, _ = winged_world()

    result = turn(world, wings_library().g, max_steps=6)

    inside = set(members_of(result.world, "assuming-wings"))
    flying = [n for n in result.world.nodes if result.world.attr(n, "name") == "can-fly"]

    assert flying
    for f in flying:
        assert f in inside, "a conclusion chained under an assumption escaped into the world"


def test_the_base_world_never_sees_the_supposed_bird():
    """The mechanism, isolated: the projection at base hides the assumption's contents, so there is
    nothing for the general rule to match there."""
    world, _ = winged_world()
    from units.graph import visible_at

    result = turn(world, wings_library().g, max_steps=6)
    base_view = visible_at(result.world, None)

    assert any(result.world.attr(n, "name") == "bird" for n in result.world.nodes)
    assert not any(base_view.attr(n, "name") == "bird" for n in base_view.nodes)
    # …but the assumption itself is visible from outside: you can see that a supposition exists
    # without seeing inside it, which is the seal (§6).
    assert any(base_view.attr(n, "name") == "assuming-wings" for n in base_view.nodes)


def test_neither_rule_mentions_the_assumption():
    """Both rules are ordinary. `bird-flies` in particular is the same description that would run in a
    world with real birds in it."""
    d = wings_library()
    for unit in [n for n in d.g.nodes if d.g.attr(n, "name") == "unit"]:
        pattern = tuple(decode_pattern(d.g, p) for p in roles_of(d.g, unit, "pattern"))
        written = {str(v).lower() for a in atoms(pattern) for _, v in a.attrs}
        assert "assuming-wings" not in written and "scope" not in written


# --------------------------------------------------------------------------------------------
# 4. …and no rule mentions any of it  (§12 invariant 1)
# --------------------------------------------------------------------------------------------

def test_no_rule_in_the_scoped_library_names_a_scope():
    """The whole point. Conclusions are placed by the **assembler**; the rules are the same rules that
    run in the base world, and none of them can see the containment."""
    d = scoped_library()
    forbidden = {"assuming-payments-settled", "scope", "member", "assuming", "context"}

    for unit in [n for n in d.g.nodes if d.g.attr(n, "name") == "unit"]:
        pattern = tuple(decode_pattern(d.g, p) for p in roles_of(d.g, unit, "pattern"))
        written = {str(v).lower() for a in atoms(pattern) for _, v in a.attrs}
        written |= {k.lower() for a in atoms(pattern) for k, _ in a.attrs}
        assert not (written & forbidden), f"{d.g.attr(unit, 'label')} names a scope: {written & forbidden}"


def test_the_same_rule_object_runs_inside_and_outside():
    """`verdict` is described twice and decodes to the same pattern both times — the containment is
    supplied entirely from outside the rule."""
    d = scoped_library()
    units = [n for n in d.g.nodes
             if d.g.attr(n, "name") == "unit" and d.g.attr(n, "label") == "verdict"]

    assert len(units) == 2
    decoded = [tuple(decode_pattern(d.g, p) for p in roles_of(d.g, u, "pattern")) for u in units]
    assert decoded[0] == decoded[1]

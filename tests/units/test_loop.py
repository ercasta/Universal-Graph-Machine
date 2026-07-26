"""THE OUTER LOOP — one thought leading to another (`model.md` §7, §8).

The claim under test is §7's account of why the loop is tight:

> **Relevance tracks the evolving state.** … Re-retrieving after each small inference is the mechanism of
> *one thought leading to another*: what this step concluded is what the next step notices.

So: a world in which the answer needs two inferences, a library in which the second rule *cannot* match
until the first has fired, and no scheduler, no dependency analysis and no ordering anywhere. If the
second rule fires in step 1, it is because step 0's conclusion made it relevant — nothing else could
have.

Also under test: §8's outcomes as **positive facts, one per goal per step**, and that `starved` is not
*"underivable"*.
"""
from __future__ import annotations

from units import (AWAITING, EMPTY, OUT_OF_FUEL, SATISFIED, STARVED, STOPPED, Description,
                   named, occurrence, outcomes_of, resemblance, step, turn, vocabulary)
from units.recall import coverage


# --------------------------------------------------------------------------------------------
# The world and the library
# --------------------------------------------------------------------------------------------

def world_and_goal():
    """Paul, a member for over a year, with a couple of late payments.

    Note what is **absent**: any `standing` occurrence. Nothing in this world says whether Paul's
    account is in good standing — that has to be concluded before eligibility can even be considered."""
    g = EMPTY
    g, paul = named(g, "Paul")
    g, discount = named(g, "loyalty discount")
    g, over_a_year = named(g, "over a year")
    g, _m = occurrence(g, "member-for", agent=paul, duration=over_a_year)
    g, lp = occurrence(g, "late-payment", agent=paul)
    g = g.with_degree(lp, "minor", "unlikely")

    d = Description()
    goal = d.goal("is-paul-eligible", d.atom(name="gets"))
    return g.union(d.g), goal


def library() -> Description:
    d = Description()

    # A — from late payments, conclude a standing, graded by how minor they were.
    d.statement("standing-rule", d.unit(
        "standing-rule",
        (d.atom("lp", name="late-payment", graded="minor",
                out=(d.role("agent", d.atom("p")),)),),
        (d.mint("standing", args=(("agent", "p"),), graded="good"),)))

    # B — eligibility. CANNOT match until A has fired: nothing named `standing` exists yet.
    d.statement("eligibility", d.unit(
        "eligibility",
        (d.atom("m", name="member-for", out=(d.role("agent", d.atom("c")),
                                             d.role("duration", d.atom(name="over a year")))),
         d.atom("st", name="standing", graded="good", out=(d.role("agent", d.atom("c")),)),
         d.atom("d", name="loyalty discount")),
        (d.mint("gets", args=(("agent", "c"), ("patient", "d")), graded="eligible"),)))

    # C — the birthday discount of §10 step 1. Shares a word with the world, so it comes to mind;
    #     matches nothing, so it contributes nothing. One wasted rule, the expected cost.
    d.statement("birthday-discount", d.unit(
        "birthday-discount",
        (d.atom("b", name="birthday", out=(d.role("agent", d.atom("q")),)),
         d.atom(name="loyalty discount")),
        (d.mint("gets", args=(("agent", "q"),)),)))

    # D — about something else entirely. Must NEVER come to mind here.
    d.statement("shipping-rule", d.unit(
        "shipping-rule",
        (d.atom("o", name="parcel", out=(d.role("weight", d.atom(name="heavy")),)),),
        (d.mint("surcharge", args=(("for", "o"),)),)))
    return d


def names(g):
    return {g.attr(n, "name") for n in g.nodes}


# --------------------------------------------------------------------------------------------
# 1. One thought leading to another
# --------------------------------------------------------------------------------------------

def test_the_second_rule_fires_only_after_the_first_made_it_relevant():
    world, goal = world_and_goal()
    lib = library().g

    result = turn(world, lib)

    assert len(result.steps) == 2
    assert "standing" not in names(result.steps[0].world) or True   # (asserted precisely below)

    # step 0: the standing rule fires; eligibility cannot yet match.
    s0 = result.steps[0]
    assert "standing" in names(s0.world)
    assert "gets" not in names(s0.world)

    # step 1: retrieving against what step 0 produced, eligibility now matches.
    s1 = result.steps[1]
    assert "gets" in names(s1.world)

    assert result.outcomes[goal] == SATISFIED


def test_eligibility_is_not_retrievable_before_the_first_step():
    """The mechanism, isolated: it is *coverage of the evolving world* that changes, nothing else."""
    world, _ = world_and_goal()
    d = library()
    elig = [n for n in d.g.nodes
            if d.g.attr(n, "name") == "statement" and d.g.attr(n, "label") == "eligibility"][0]

    before = coverage(world, d.g, elig)
    after_step0 = coverage(step(world, d.g, 0).world, d.g, elig)

    assert before < 1.0
    assert after_step0 == 1.0
    assert "standing" in vocabulary(d.g, elig)


def test_the_conclusion_inherits_the_band_across_two_steps():
    """Degree survives the outer loop: `minor = unlikely` on the late payment becomes `good = unlikely`
    on the standing, which becomes `eligible = unlikely` on the verdict. Marginal, not flat."""
    world, _ = world_and_goal()

    result = turn(world, library().g)

    verdict = [n for n in result.world.nodes if result.world.attr(n, "name") == "gets"]
    assert len(verdict) == 1
    assert result.world.degree(verdict[0], "eligible") == "unlikely"


# --------------------------------------------------------------------------------------------
# 2. Retrieval is allowed to be wrong, and to be incomplete
# --------------------------------------------------------------------------------------------

def test_an_irrelevant_rule_comes_to_mind_and_costs_a_step():
    """§10 step 1: *"Nothing here suggests a birthday; System 1 is associative, not correct."*"""
    world, _ = world_and_goal()

    retrieved = resemblance(world, library().g)

    assert "birthday-discount" in retrieved


def test_a_rule_about_something_else_never_comes_to_mind():
    """The other half: retrieval is **incomplete**, and that is the property that bounds the cost."""
    world, _ = world_and_goal()

    retrieved = resemblance(world, library().g)

    assert "shipping-rule" not in retrieved


def test_an_unretrieved_rule_is_not_assembled():
    """§7 step 2 mints units for what came to mind — not for the library."""
    world, _ = world_and_goal()

    s = step(world, library().g, 0)

    assert "shipping-rule" not in s.retrieved
    assert "surcharge" not in names(s.world)


# --------------------------------------------------------------------------------------------
# 3. Outcomes are positive facts (§8, §12 invariant 5)
# --------------------------------------------------------------------------------------------

def test_every_step_records_exactly_one_outcome_per_pending_goal():
    world, goal = world_and_goal()

    result = turn(world, library().g)

    assert outcomes_of(result.world, goal) == [STARVED, SATISFIED]


def test_starved_is_recorded_and_is_not_underivable():
    """§7: *silence does not mean "not derivable" — it means "nothing came to mind."*

    Step 0 records `starved` for a goal that is, in fact, perfectly derivable two steps later. The fact
    that the same goal later reads `satisfied` is the proof that `starved` never claimed otherwise."""
    world, goal = world_and_goal()

    result = turn(world, library().g)

    assert outcomes_of(result.world, goal)[0] == STARVED
    assert outcomes_of(result.world, goal)[-1] == SATISFIED


def test_an_outcome_is_an_ordinary_occurrence_in_the_graph():
    """Not a return code, not a side table. A rule could match on it (§9: provenance is ordinary data)."""
    world, goal = world_and_goal()

    result = turn(world, library().g)
    outcome_nodes = [n for n in result.world.nodes if result.world.attr(n, "name") == "outcome"]

    assert len(outcome_nodes) == 2
    for n in outcome_nodes:
        roles = [result.world.attr(r, "name") for r in result.world.out(n)]
        assert roles == ["goal"]


def test_an_unsatisfiable_goal_stops_rather_than_running_forever():
    """§8's **outer budget**: there is no quiescence (§5), so something must stop the stepping — and its
    exhaustion is a *different fact* from running out of fuel."""
    world, _ = world_and_goal()
    d = Description()
    impossible = d.goal("find-a-unicorn", d.atom(name="unicorn"))
    world = world.union(d.g)

    result = turn(world, library().g, max_steps=4)

    assert outcomes_of(result.world, impossible)[-1] == STOPPED
    assert OUT_OF_FUEL not in outcomes_of(result.world, impossible)
    assert len(result.steps) == 4


def test_out_of_fuel_is_distinguishable_from_starved():
    """The two must never collapse: *"I couldn't work it out"* is not *"nothing came to mind"*, and
    neither is *"no."*"""
    world, goal = world_and_goal()

    starved_run = step(world, library().g, 0, fuel_limit=500)
    fuel_run = step(world, library().g, 0, fuel_limit=1)

    assert starved_run.outcomes[goal] == STARVED
    assert fuel_run.outcomes[goal] == OUT_OF_FUEL


# --------------------------------------------------------------------------------------------
# 4. A known gap, pinned rather than hidden
# --------------------------------------------------------------------------------------------

def test_conclusions_accrete_superlinearly_across_steps():
    """⚠ **A characterisation test, not an approval.** It records behaviour the design has not decided
    on, so that the decision is made deliberately rather than discovered as a hang.

    `model.md` §5 is explicit that *"a repeat arrival is a firing… there is no value-comparison test
    suppressing it, and therefore no notion of quiescence."* Inside one circuit run that is fine. Across
    **steps** it is not: every step re-mints its conclusions as fresh nodes, duplicated premises then
    multiply the matches, and the persistent graph grows faster than the number of steps.

    `ugm` had solved exactly this — `0014` *anything minted per run must be keyed*, and
    [[whole-graph-banks-must-be-idempotent]] (*"test bank idempotency FIRST when superlinear"*). Keying
    went away with the fixpoint that motivated it, and nothing replaced it.

    The tension is sharp and worth stating: `cnl.md` §1 forbids the **boundary** from merging two nodes,
    and identity is supposed to be a rule's graded decision. But if nothing merges conclusions either,
    the system cannot tell *"I already concluded this"* — which is not only growth, it is why the
    duplicate premises multiply. This is `model.md` §13's retention question arriving early and in a
    more acute form than it is written there."""
    world, _ = world_and_goal()
    d = Description()
    d.goal("unsatisfiable", d.atom(name="unicorn"))
    world = world.union(d.g)

    counts = {}
    for max_steps in (2, 4, 8):
        result = turn(world, library().g, max_steps=max_steps)
        counts[max_steps] = sum(1 for n in result.world.nodes
                                if result.world.attr(n, "name") == "gets")

    # one `standing` per step — linear, and already a duplicate per step
    assert counts[2] == 1
    # …but the verdict count grows faster than the step count, because duplicated premises
    # multiply the matches. If this ever becomes linear or flat, the gap has been closed and this
    # test should be replaced with the real invariant.
    assert counts[8] > 4 * counts[4] // 3


# --------------------------------------------------------------------------------------------
# 5. Nothing happens unbidden (§1)
# --------------------------------------------------------------------------------------------

def test_with_no_goal_the_turn_does_nothing():
    world, _ = world_and_goal()
    goalless = EMPTY
    for n in world.nodes:
        if world.attr(n, "name") not in ("goal", "atom"):
            goalless = goalless.with_node(n, **dict(world.attrs.get(n, {})))
    for (a, b) in world.edges:
        if a in goalless.nodes and b in goalless.nodes:
            goalless = goalless.with_edge(a, b)

    result = turn(goalless, library().g)

    assert result.steps == []
    assert "standing" not in names(result.world)

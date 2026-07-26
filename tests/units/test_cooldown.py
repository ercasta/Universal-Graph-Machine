"""COOLDOWN — bounded suppression of re-derivation, and what it costs.

A deliberate approximation (see `units/cooldown.py`). These tests establish three things: that it
actually fixes the accretion, that it does **not** break the tunnel, and that its approximations are
visible rather than silent.
"""
from __future__ import annotations

from units import Description, turn
from units.cooldown import Cooldown
from tests.units.test_loop import library, names, world_and_goal


def unsatisfiable_world():
    world, _ = world_and_goal()
    d = Description()
    d.goal("unsatisfiable", d.atom(name="unicorn"))
    return world.union(d.g)


def count(g, name: str) -> int:
    return sum(1 for n in g.nodes if g.attr(n, "name") == name)


# --------------------------------------------------------------------------------------------
# 1. It fixes the accretion
# --------------------------------------------------------------------------------------------

def test_without_cooldown_conclusions_multiply():
    world = unsatisfiable_world()
    r4 = turn(world, library().g, max_steps=4)
    r8 = turn(world, library().g, max_steps=8)

    assert count(r8.world, "gets") > 4 * count(r4.world, "gets")


def test_with_cooldown_each_conclusion_is_derived_once():
    world = unsatisfiable_world()

    r8 = turn(world, library().g, max_steps=8, cooldown=Cooldown())

    assert count(r8.world, "standing") == 1
    assert count(r8.world, "gets") == 1


def test_growth_becomes_flat_in_the_number_of_steps():
    """The property that matters: running longer stops costing more."""
    world = unsatisfiable_world()

    sizes = []
    for max_steps in (4, 8, 16):
        r = turn(world, library().g, max_steps=max_steps, cooldown=Cooldown())
        sizes.append(count(r.world, "gets") + count(r.world, "standing"))

    assert sizes == [2, 2, 2]


def test_the_answer_is_unchanged_when_the_goal_is_reachable():
    """Suppression must not cost a conclusion the system would otherwise have reached."""
    world, goal = world_and_goal()

    plain = turn(world, library().g)
    cooled = turn(world, library().g, max_steps=12, cooldown=Cooldown())

    assert "gets" in names(plain.world)
    assert "gets" in names(cooled.world)
    verdict = [n for n in cooled.world.nodes if cooled.world.attr(n, "name") == "gets"]
    assert cooled.world.degree(verdict[0], "eligible") == "unlikely"     # band preserved


# --------------------------------------------------------------------------------------------
# 2. It must NOT break the tunnel
# --------------------------------------------------------------------------------------------

def tunnel_library() -> Description:
    """The same rule applies in the base world and inside a supposition. **The bound nodes are
    identical in both** — a supposition changes a degree, not an identity — so a cooldown keyed on
    `(rule, nodes)` alone would suppress the hypothetical conclusion. This is the case that decides
    whether the key is right."""
    d = Description()
    d.statement("standing-rule", d.unit(
        "standing-rule",
        (d.atom("lp", name="late-payment", graded="minor",
                out=(d.role("agent", d.atom("p")),)),),
        (d.mint("standing", args=(("agent", "p"),), graded="good"),)))

    def verdict_unit():
        """Two descriptions of the *same rule* — same name, same pattern, same effect. One runs in the
        base world, one inside the supposition, and they bind the same `standing` node."""
        return d.unit("verdict",
                      (d.atom("st", name="standing", graded="good"),),
                      (d.mint("gets", args=(("about", "st"),), graded="eligible"),))

    d.statement("verdict-plain", verdict_unit())            # root: runs in the base world
    settle = d.statement("settle", d.unit(
        "settle", (d.atom("s", name="standing", graded="good"),),
        (d.stamp("s", "good", "certain"),)))
    d.statement("suppose-settled", settle,
                d.statement("verdict-inner", verdict_unit()))
    return d


def test_a_change_to_a_bound_node_cancels_the_cooldown():
    """**A cooldown on a thing, not a timer.** The key carries a fingerprint of the bound nodes' state,
    so a rule that fired on a node is spent on it only *while it stays as it was*.

    This is what makes the physical-instance framing hold up under scoping. A supposition changes a
    degree and not an identity, so the same rule re-run inside a tunnel binds exactly the same nodes —
    and a state-blind key suppressed the hypothetical conclusion, losing it entirely, with retrieval
    order deciding which of the two survived. Fingerprinting fixes that as a *consequence* rather than
    by special-casing bands, which is the sign the cut is in the right place."""
    world, _ = world_and_goal()

    plain = turn(world, tunnel_library().g, max_steps=6)
    cooled = turn(world, tunnel_library().g, max_steps=6, cooldown=Cooldown())

    def bands(r):
        return sorted(r.world.degree(n, "eligible")
                      for n in r.world.nodes if r.world.attr(n, "name") == "gets")

    assert bands(plain) == ["certain", "unlikely"]
    assert bands(cooled) == ["certain", "unlikely"]     # both survive: the state differed


def test_an_unchanged_node_stays_in_cooldown():
    """The other half — otherwise the fingerprint would simply disable suppression. Re-running over a
    world nothing touched must still be suppressed."""
    world = unsatisfiable_world()
    cd = Cooldown()

    turn(world, library().g, max_steps=8, cooldown=cd)

    assert cd.suppressed > 0
    assert count(turn(world, library().g, max_steps=8, cooldown=Cooldown()).world, "gets") == 1


def test_an_undeclared_scope_writes_hypothetical_conclusions_back_flatly():
    """⚠ **The residual hazard, after the scoped write-back landed** (`test_scoped_writeback.py`).

    A statement that *declares* the containment it establishes has its conclusions placed under it. A
    statement that behaves like a supposition but **declares no scope** does not — its conclusions are
    written back flatly, and the world ends up asserting *"Paul is eligible, certain"*, which is true
    only under a hypothesis nobody recorded.

    That is no longer an engine bug; it is the description's omission. But it is **silent**, which is
    the part worth pinning: there is no `supposition` kind for the engine to notice a missing scope on
    — *guards yes, kinds no* (§11) cuts both ways. A rule that stamps a premise into a different value
    and declares no containment is indistinguishable, to the assembler, from an ordinary inference.

    The candidate fix is a **lint over the description**, not an engine check: a statement whose units
    `stamp` a node they did not mint is changing the world rather than reading it, and almost certainly
    wants a scope. Unbuilt."""
    world, _ = world_and_goal()

    result = turn(world, tunnel_library().g, max_steps=6)      # tunnel_library declares no scope

    flat = [n for n in result.world.nodes
            if result.world.attr(n, "name") == "gets"
            and result.world.degree(n, "eligible") == "certain"]

    assert len(flat) == 1
    # Nothing contains it: it reads as an unconditional fact about the world.
    containers = [n for n in result.world.nodes
                  for r in result.world.out(n)
                  if result.world.attr(r, "name") == "member"
                  and flat[0] in result.world.out(r)]
    assert containers == []


# --------------------------------------------------------------------------------------------
# 3. The approximations are visible, not silent
# --------------------------------------------------------------------------------------------

def test_a_full_list_evicts_and_says_so():
    """Bounded means suppressed derivations come back. That is acceptable; being unable to *tell* would
    not be — `evictions` is what makes the approximation declared rather than discovered."""
    world = unsatisfiable_world()
    tiny = Cooldown(size=1)

    r = turn(world, library().g, max_steps=8, cooldown=tiny)

    assert tiny.evictions > 0
    assert count(r.world, "gets") > 1               # eviction let it re-derive


def test_the_list_reports_what_it_suppressed():
    world = unsatisfiable_world()
    cd = Cooldown()

    turn(world, library().g, max_steps=8, cooldown=cd)

    assert cd.suppressed > 0
    assert cd.evictions == 0
    assert len(cd) <= cd.size


def test_the_size_changes_the_answer_which_is_the_declared_cost():
    """⚠ Scheduling policy leaking into semantics, demonstrated rather than asserted. Two runs of the
    same world and the same library, differing only in a cache size, reach different graphs."""
    world = unsatisfiable_world()

    big = turn(world, library().g, max_steps=8, cooldown=Cooldown(size=512))
    small = turn(world, library().g, max_steps=8, cooldown=Cooldown(size=1))

    assert count(big.world, "gets") != count(small.world, "gets")

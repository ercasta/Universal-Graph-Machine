"""MERGE-COREF BY DEFAULT, unless explicitly told they are distinct.

The shape asked for: two similar nodes merge **by default**; the only thing that stops it is a
`distinct-from` occurrence physically connecting them, which arises from an explicit discourse statement
— *"no, that is a different Paul"* — rather than from any standing policy.

**Why this is allowed to exist at all**, given `cnl.md` §1's *create, never merge*: that rule governs
the **boundary**, which must never identify two things because identification is judgement. It does not
forbid identification — it says a **rule** must be the one making it, gradedly and revisably. So the
default merge is exactly the right shape: a rule, in the loop, that can be wrong and can be overruled by
a fact.

**Four authored choices, in the rule and not in the engine** (§4 — similarity is authored, per pattern,
inspectable and overridable):

1. *similar* means **same `name`**, expressed with an `AttrVar` so the rule never names a name;
2. only nodes asserting `mention = True` are candidates — otherwise the rule would merge every role node
   called `"agent"` into one and destroy the graph (measured below);
3. both must be **members of the same parent**, so two mentions in different scopes — one inside a
   hypothesis, say — are never fused;
4. a `distinct-from` between them blocks it, as an `absent` guard.

None of that is engine policy; a different KB could author all four differently.

⚠ **Clause (3) is the closest anything has come to `model.md` §12 invariant 1** (*no rule pattern names
a scope*). It does not name one — it asks whether *something* contains both nodes, which is a relation
between the two, not a question about which scope the rule is running in. But it is worth flagging
rather than glossing: this is a rule reading the nesting, and the invariant's boundary is now being
tested rather than merely respected.

⚠ **Merging is physical and there is no undo.** `Graph.merge` rewrites the graph, and recovering from a
wrong merge has to be an explicit statement that re-separates them. Nothing here does that yet.
"""
from __future__ import annotations

from units import Description, assemble, named, occurrence, turn
from units.graph import EMPTY, Node, contains, role_edge
from units.loop import apply_merges
from units.match import AttrVar


# --------------------------------------------------------------------------------------------
# The rule, as data
# --------------------------------------------------------------------------------------------

def coref_library() -> Description:
    d = Description()
    a = d.atom("a", mention=True, name=AttrVar("who"))
    b = d.atom("b", mention=True, name=AttrVar("who"))
    same_parent = d.atom("s", out=(d.role("member", d.atom("a")),
                                   d.role("member", d.atom("b"))))
    guard = d.absent(d.atom(name="distinct-from",
                            out=(d.role("of", d.atom("a")), d.role("of", d.atom("b")))))
    d.statement("coref", d.unit("coref", (a, b, same_parent, guard), (d.same("a", "b"),)))
    return d


def mention(g, name, scope):
    n = Node(name)
    g = g.with_node(n, name=name, mention=True)
    return contains(g, scope, n), n


def discourse(*, distinct: bool = False, second_scope: bool = False):
    """Two mentions of "Paul" and one of "Mary", all inside one scope. Optionally an explicit statement
    that the two Pauls are different, or a second scope holding the second Paul."""
    g = EMPTY
    g, here = named(g, "here")
    g, there = named(g, "there")
    g, p1 = mention(g, "Paul", here)
    g, p2 = mention(g, "Paul", there if second_scope else here)
    g, mary = mention(g, "Mary", here)
    g, _ = occurrence(g, "likes", agent=p1, patient=mary)
    g, _ = occurrence(g, "owes", agent=p2, patient=mary)
    if distinct:
        g, occ = occurrence(g, "distinct-from", of=p1)
        g = role_edge(g, occ, "of", p2)

    d = Description()
    d.goal("sort-out-who-is-who", d.atom(name="same-as"))
    return g.union(d.g), p1, p2, mary


def mentions_named(g, name):
    return [n for n in g.nodes if g.attr(n, "name") == name and g.attr(n, "mention")]


# --------------------------------------------------------------------------------------------
# 1. It merges by default
# --------------------------------------------------------------------------------------------

def test_two_mentions_of_the_same_name_merge_by_default():
    world, p1, p2, _ = discourse()

    result = turn(world, coref_library().g, max_steps=2)

    assert len(mentions_named(result.world, "Paul")) == 1


def test_the_merged_node_keeps_both_sets_of_edges():
    """The point of merging rather than just noting sameness: one node that both facts hang off."""
    world, p1, p2, mary = discourse()

    result = turn(world, coref_library().g, max_steps=2)
    paul = mentions_named(result.world, "Paul")[0]

    reached = set()
    for occ in result.world.nodes:
        for r in result.world.out(occ):
            if paul in result.world.out(r):
                reached.add(result.world.attr(occ, "name"))
    assert {"likes", "owes"} <= reached


def test_a_lone_mention_is_left_alone():
    world, _, _, _ = discourse()

    result = turn(world, coref_library().g, max_steps=2)

    assert len(mentions_named(result.world, "Mary")) == 1


# --------------------------------------------------------------------------------------------
# 2. `distinct-from` blocks it — and must come from discourse
# --------------------------------------------------------------------------------------------

def test_an_explicit_distinct_from_blocks_the_merge():
    world, p1, p2, _ = discourse(distinct=True)

    result = turn(world, coref_library().g, max_steps=2)

    assert len(mentions_named(result.world, "Paul")) == 2


def test_the_block_is_a_fact_in_the_graph_not_a_flag():
    """`distinct-from` is an ordinary occurrence with two `of` roles — §3's encoding, nothing special.
    That is what lets it arise from a discourse statement rather than from configuration, and what lets
    a later step retract or doubt it."""
    world, p1, p2, _ = discourse(distinct=True)

    blocks = [n for n in world.nodes if world.attr(n, "name") == "distinct-from"]
    assert len(blocks) == 1
    targets = [t for r in world.out(blocks[0]) for t in world.out(r)]
    assert set(targets) == {p1, p2}


def test_distinctness_is_specific_to_the_pair_it_names():
    """Saying *these* two Pauls differ must not stop a third mention from merging with one of them."""
    world, p1, p2, _ = discourse(distinct=True)
    here = [n for n in world.nodes if world.attr(n, "name") == "here"][0]
    world, _p3 = mention(world, "Paul", here)

    result = turn(world, coref_library().g, max_steps=2)

    # p3 merges with one of them, so three mentions become two — not one, and not three.
    assert len(mentions_named(result.world, "Paul")) == 2


# --------------------------------------------------------------------------------------------
# 3. Scope: mentions under different parents never fuse
# --------------------------------------------------------------------------------------------

def test_two_mentions_in_different_scopes_do_not_merge():
    """The reason clause (3) exists. Two nodes named `"Paul"` under different parents may well be two
    different Pauls — one of them inside a hypothesis, an attributed belief, or another speaker's
    utterance — and fusing them would silently destroy the distinction §6 exists to keep.

    Note that nothing declares these to be *scopes*: they are just nodes that happen to have members.
    The nesting is ordinary structure (§6, graph side), and the rule reads it as such."""
    world, p1, p2, _ = discourse(second_scope=True)

    result = turn(world, coref_library().g, max_steps=2)

    assert len(mentions_named(result.world, "Paul")) == 2
    assert not any(result.world.attr(n, "name") == "same-as" for n in result.world.nodes)


def test_same_scope_is_what_makes_the_difference():
    """The controlled comparison: identical discourse, one node moved to another parent."""
    together, _, _, _ = discourse(second_scope=False)
    apart, _, _, _ = discourse(second_scope=True)

    r_together = turn(together, coref_library().g, max_steps=2)
    r_apart = turn(apart, coref_library().g, max_steps=2)

    assert len(mentions_named(r_together.world, "Paul")) == 1
    assert len(mentions_named(r_apart.world, "Paul")) == 2


def test_containment_must_run_parent_to_child_or_the_rule_is_unwritable():
    """⚠ **The direction of containment is forced, not conventional.**

    A pattern atom has `out` and no backward traversal (`match.Pat`). *"Find something that contains
    both of these"* — the only way a rule can ask about co-membership — therefore requires the
    **container to be the source**. Written the other way (`x in y`, edge from the member), the same
    question cannot be expressed at all: you would have to walk an edge backwards.

    Demonstrated rather than asserted: build the identical discourse with the edges reversed, and the
    coref rule stops matching — not because the two Pauls are in different scopes, but because the
    pattern can no longer find the scope."""
    world, p1, p2, _ = discourse()
    reversed_world = EMPTY
    for n in world.nodes:
        reversed_world = reversed_world.with_node(n, **dict(world.attrs.get(n, {})))
    for (a, b) in world.edges:
        # flip only the containment edges: role node named "member"
        if world.attr(a, "name") == "member":
            reversed_world = reversed_world.with_edge(b, a)
        elif world.attr(b, "name") == "member":
            reversed_world = reversed_world.with_edge(b, a)
        else:
            reversed_world = reversed_world.with_edge(a, b)

    forward = turn(world, coref_library().g, max_steps=2)
    backward = turn(reversed_world, coref_library().g, max_steps=2)

    assert len(mentions_named(forward.world, "Paul")) == 1       # container → contained: works
    assert len(mentions_named(backward.world, "Paul")) == 2      # reversed: unmatchable


def test_a_merge_is_physical_and_has_no_undo():
    """Requested explicitly: merging rewrites the graph, and recovery must be an explicit act. This
    records that there is currently **no** recovery path — `drop` is gone from the graph entirely, so
    nothing can refer to it to argue about it afterwards.

    The `same-as` occurrence survives as the record of *why*, which is the only thread back."""
    world, p1, p2, _ = discourse()

    result = turn(world, coref_library().g, max_steps=2)

    survivors = mentions_named(result.world, "Paul")
    assert len(survivors) == 1
    assert p1 not in result.world.nodes or p2 not in result.world.nodes
    assert any(result.world.attr(n, "name") == "same-as" for n in result.world.nodes)


# --------------------------------------------------------------------------------------------
# 4. The authored guard that keeps it from destroying the graph
# --------------------------------------------------------------------------------------------

def test_without_the_mention_guard_the_rule_would_collapse_the_scaffolding():
    """⚠ The reason clause (2) is in the rule. Role nodes all carry `name = "agent"` (§4 — a role is
    identified by matching its name), so *"merge two nodes with the same name"* without a guard fuses
    every agent role in the graph into one, and every occurrence loses its participants.

    This is `model.md` §13's *role node sharing* worry again: role names behave like a shared vocabulary
    whether or not one was declared. Here it would be catastrophic rather than merely imprecise."""
    world, _, _, _ = discourse()

    d = Description()
    a, b = d.atom("a", name=AttrVar("w")), d.atom("b", name=AttrVar("w"))
    d.statement("greedy", d.unit("greedy", (a, b), (d.same("a", "b"),)))

    asm = assemble(d.g)
    out = asm.feed("greedy", world).circuit.units[0].output
    merged = apply_merges(out)

    agents_before = sum(1 for n in world.nodes if world.attr(n, "name") == "agent")
    agents_after = sum(1 for n in merged.nodes if merged.attr(n, "name") == "agent")
    assert agents_before == 2
    assert agents_after == 1                 # both agent roles fused: the graph is wrecked


# --------------------------------------------------------------------------------------------
# 5. Merging is an application, not a decision
# --------------------------------------------------------------------------------------------

def test_the_rule_records_its_decision_before_anything_is_applied():
    """A `same-as` occurrence exists in the graph, so *why* two things were merged is ordinary data a
    later rule can match on (§9: provenance is ordinary data)."""
    world, _, _, _ = discourse()

    result = turn(world, coref_library().g, max_steps=2)

    assert any(result.world.attr(n, "name") == "same-as" for n in result.world.nodes)


def test_applying_merges_is_idempotent():
    world, _, _, _ = discourse()

    once = turn(world, coref_library().g, max_steps=2).world
    twice = apply_merges(apply_merges(once))

    assert len(mentions_named(twice, "Paul")) == 1
    assert len(twice.nodes) == len(apply_merges(once).nodes)

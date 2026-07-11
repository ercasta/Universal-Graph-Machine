"""
Stage-1 code-reasoning probe — the go/no-go for the agentic-coding arc (docs/vision_agentic.md
§10, RECOMMENDED NEXT in docs/handoff_redesign.md). It decouples the two risks the arc carries:
"is the substrate expressive/tractable enough to reason over code" vs. "can I build a reliable
CPG extractor that produces it". This tests ONLY the first — with ZERO extraction, no Joern, no
Neo4j — by hand-authoring the frames AS IF a CPG recognizer had already run, then reasoning over
them with the existing engine (`run_rules`).

The canonical case is the **queryset-mutation-during-iteration hazard** (Django): consuming a
collection in a loop while mutating that same collection is unsafe. Two vision claims are under
test:

  - §6 COVERAGE-BY-COMPOSITION: the hazard is NOT one hand-enumerated pattern. It is DERIVED by
    composing two mechanism-level rules — "iterating a collection consumes it" and "mutating a
    collection while it is consumed in the same loop is a hazard". Nobody wrote a
    "queryset-mutated-inside-its-own-loop" rule; it falls out of the composition. The intermediate
    `consumes` fact is asserted directly so the composition is visible, not just its endpoint.

  - §5 FRAMES ARE THE JOIN (many-to-one): a `for`-loop and a recursion are structurally different
    CPG shapes but both materialize the SAME `Iteration` frame. So the ONE mechanism rule fires on
    a recursion-shaped iteration with no recursion-specific rule — the paraphrase-collapse property,
    applied to code shapes.

Stage 2 (adversarial near-misses) is the failure mode that actually matters early: compositional
rules OVER-generate before they under-generate. Each near-miss is structurally close to the hazard
but must NOT fire — if one does, the rule needs another role constraint, learned here for free with
no extraction code written.

The frame ontology is authored the vision-§5 way: `is_a`-typed frame nodes
(`Iteration`, `Mutation`) with named-predicate role edges (`iterates`, `mutates`, `within`) that
point at OTHER nodes. The mechanism rules are authored in the machine-rule CNL (multi-variable,
multi-clause `H when B1 and B2 ...`), so nothing here is Python domain logic — the rules are DATA.
"""
import ugm as h
from ugm.cnl.machine_rules import load_machine_rules


# --- substrate helpers (same idiom as tests/test_new_core.py) ---------------

def _rel(g, s, p, o):
    """Assert the fact `s p o`, minting subject/object nodes by name on first mention."""
    si = g.nodes_named(s)[0] if g.nodes_named(s) else g.add_node(s)
    oi = g.nodes_named(o)[0] if g.nodes_named(o) else g.add_node(o)
    g.add_relation(si, p, oi)


def _has(g, s, p, o):
    from ugm.cnl import rewriter
    return any(rewriter._relation_exists(g, si, p, oi)
               for si in g.nodes_named(s) for oi in g.nodes_named(o))


# --- the frame ontology, hand-authored as if CPG extraction had run ---------

def _iteration_frame(g, loop, collection):
    """An `Iteration` frame: a loop node typed `iteration`, with the `iterates` role edge to the
    collection it consumes (a `queryset`). This is what a CPG-side recognizer for a `for`/`while`/
    comprehension/recursion would materialize — the roles point at real code regions (here, nodes)."""
    _rel(g, loop, "is_a", "iteration")
    _rel(g, loop, "iterates", collection)
    _rel(g, collection, "is_a", "queryset")


def _mutation_frame(g, mut, target, loop):
    """A `Mutation` frame inside a loop body: a node typed `mutation`, with `mutates` -> its target
    and `within` -> the enclosing loop (the body-containment role)."""
    _rel(g, mut, "is_a", "mutation")
    _rel(g, mut, "mutates", target)
    _rel(g, mut, "within", loop)


# --- the mechanism-level rules (vision §6), authored in machine-rule CNL -----
#
# Rule A composes UP from raw frame structure to a mechanism fact; Rule B composes the hazard from
# it. Neither mentions "queryset" or any surface pattern — they are stated over frame TYPES and
# ROLES, so they fire on every matching instance, including shapes authored after them.
MECHANISM_RULES = load_machine_rules(
    "?loop consumes ?c when ?loop is_a iteration and ?loop iterates ?c\n"
    "?m is_a hazard when ?m is_a mutation and ?m mutates ?c "
    "and ?m within ?loop and ?loop consumes ?c"
)




# --- the positive case: the hazard is DERIVED by composition ----------------

def test_queryset_mutation_hazard_derived_by_composition():
    # A loop consuming `qs` while a mutation inside it targets that same `qs` -> hazard.
    g = h.Graph()
    _iteration_frame(g, "loop1", "qs")
    _mutation_frame(g, "mut1", "qs", "loop1")

    h.run_rules(g, MECHANISM_RULES)

    # the composition is visible: Rule A derived the intermediate mechanism fact...
    assert _has(g, "loop1", "consumes", "qs")
    # ...and Rule B composed the hazard on top of it. Nobody wrote a "queryset-mutated-in-loop"
    # rule; it fell out of the two mechanism rules.
    assert _has(g, "mut1", "is_a", "hazard")


# --- Stage 2: adversarial near-misses that must NOT fire --------------------

def test_near_miss_collection_consumed_but_not_mutated():
    # The loop consumes `qs`, but the only mutation targets a DIFFERENT collection -> no hazard.
    g = h.Graph()
    _iteration_frame(g, "loop1", "qs")
    _mutation_frame(g, "mut1", "other", "loop1")     # mutates `other`, not `qs`

    h.run_rules(g, MECHANISM_RULES)

    assert _has(g, "loop1", "consumes", "qs")         # consumption still derived...
    assert not _has(g, "mut1", "is_a", "hazard")      # ...but no hazard (target disjoint)


def test_near_miss_mutation_outside_the_loop():
    # A mutation targets `qs`, but it is NOT within the loop that consumes `qs` (it is in a sibling
    # loop) -> no hazard. This is the `within` role constraint doing its job.
    g = h.Graph()
    _iteration_frame(g, "loop1", "qs")
    _iteration_frame(g, "loop2", "other")
    _mutation_frame(g, "mut1", "qs", "loop2")         # within loop2, which does not consume qs

    h.run_rules(g, MECHANISM_RULES)

    assert not _has(g, "mut1", "is_a", "hazard")


def test_near_miss_read_only_iteration_is_safe():
    # A loop consuming `qs` with NO mutation inside it at all -> safe, no hazard. (The most common
    # real case; the rule must stay silent on it.)
    g = h.Graph()
    _iteration_frame(g, "loop1", "qs")

    h.run_rules(g, MECHANISM_RULES)

    assert _has(g, "loop1", "consumes", "qs")
    assert not any(g.name(o) == "hazard"
                   for n in g.nodes() for r in g.out(n) if g.name(r) == "is_a"
                   for o in g.out(r))


# --- §5 many-to-one: a recursion-shaped iteration triggers the SAME rule -----

def test_recursion_shaped_iteration_triggers_the_same_mechanism_rule():
    # A recursive function walking a collection is structurally NOTHING like a `for` loop in the
    # CPG (a self-call, no back-edge), but a CPG-side recursion recognizer materializes the SAME
    # `Iteration` frame. So the one mechanism rule fires with no recursion-specific rule — the
    # frame is the join (§5), and coverage came from rule generality, not from enumerating shapes.
    g = h.Graph()
    _iteration_frame(g, "walk_recursively", "qs")     # frame emitted by a *recursion* recognizer
    _mutation_frame(g, "del_call", "qs", "walk_recursively")

    h.run_rules(g, MECHANISM_RULES)

    assert _has(g, "del_call", "is_a", "hazard")      # same rule, structurally different source


# --- QA over code frames is a separate axis (§10): ask + explain end-to-end --

def test_hazard_is_queryable_and_explainable():
    g = h.Graph()
    _iteration_frame(g, "loop1", "qs")
    _mutation_frame(g, "mut1", "qs", "loop1")
    journal = h.run_rules(g, MECHANISM_RULES)

    # retrieval: the derived hazard answers a yes/no `is X a Y` question over the frame graph
    assert h.ask(g, "is mut1 a hazard") == ["yes"]
    assert h.ask(g, "is mut1 a queryset") == ["no"]

    # derivation: the why-trace names the hazard rule and bottoms out at the given frame facts,
    # passing through the composed `consumes` mechanism fact.
    why = "\n".join(h.ask(g, "why mut1 is a hazard", journal=journal, rules=MECHANISM_RULES))
    assert "mut1 is_a hazard" in why
    assert "consumes" in why                          # the composition step appears in the trace

"""
On-demand (demand-driven) evaluation — derive a fact only when a demand needs it
(docs/coreference_design.md §1/§2).

Every blow-up we hit came from EAGER forward chaining (close the whole transitive
relation, link every same-name mention). On-demand flips it: a query/goal emits a
`<demand>` node, demand-propagation rules push the demand backward into rule bodies, and
demand-GATED derivation rules fire only where their head is demanded. This is the Datalog
magic-sets / demand transformation — goal-direction WITHOUT abandoning forward chaining,
and with NO engine change (demands are just more control tokens, vision §6; propagation is
literally planning phase A generalized).

A demand for "does `a` is_a `c`?" is a node `<demand>` with `--d_subj--> a`,
`--d_obj--> c`. The two rules below realize transitivity-on-demand:

  - SPAWN (backward): demand(a,c) + a is_a b  =>  demand(b,c)   (use the fact to bind the
    intermediate, exactly the magic-set rewrite).
  - DERIVE (gated): a is_a b, b is_a c, demand(a,c)  =>  a is_a c.

The payoff is selectivity: only the demanded endpoints' chains are closed — `a is_a c` is
NOT derived unless `(a,c)` was demanded. The same skeleton bounds coreference (coref.py):
link only the queried entity's mentions, so equality classes stay tiny.
"""
from __future__ import annotations

from .production_rule import Pat, Rule
from .world_model import Graph

DEMAND = "<demand>"


def seed_demand(graph: Graph, subject: str, obj: str) -> str:
    """Emit `<demand> --d_subj--> subject`, `--d_obj--> obj` (a query for `subject is_a
    obj`). Nodes are located/created by name. Returns the demand node id."""
    def node(name: str) -> str:
        found = graph.nodes_named(name)
        return found[0] if found else graph.add_node(name)

    d = graph.add_node(DEMAND)
    graph.add_relation(d, "d_subj", node(subject))
    graph.add_relation(d, "d_obj", node(obj))
    return d


# Transitivity-on-demand: spawn sub-demands backward, derive only where demanded.
DEMAND_TRANSITIVITY: list[Rule] = [
    # SPAWN: demand(a,c) + a is_a b  =>  demand(b,c)   (no duplicate demand)
    Rule(
        key="demand.is_a.spawn",
        lhs=[Pat("?d", "d_subj", "?a"), Pat("?d", "d_obj", "?c"), Pat("?a", "is_a", "?b")],
        nac=[Pat("?d2", "d_subj", "?b"), Pat("?d2", "d_obj", "?c")],
        rhs=[Pat("<demand>?", "d_subj", "?b"), Pat("<demand>?", "d_obj", "?c")],
    ),
    # DERIVE (gated on the demand): a is_a b, b is_a c, demand(a,c)  =>  a is_a c
    Rule(
        key="demand.is_a.derive",
        lhs=[Pat("?a", "is_a", "?b"), Pat("?b", "is_a", "?c"),
             Pat("?d", "d_subj", "?a"), Pat("?d", "d_obj", "?c")],
        nac=[Pat("?a", "is_a", "?c")],
        rhs=[Pat("?a", "is_a", "?c")],
    ),
]


# Demand -> coreference: a demand that NAMES an entity (in either role) requests that the
# entity's mentions be coreferred. This is how "ask about X" pulls coreference of X's
# mentions, and ONLY X's — the selectivity (small classes, no quadratic saturation). The
# decision to corefer is a RULE firing on a demand token; the request is a MATERIALIZED TOOL
# CALL `<call> --tool--> coref --arg--> X` (dispatch.py), serviced by the same engine-managed
# dispatcher as every other tool (vision §6). No dedup NAC: a NAC on the `<call>`'s own
# `tool`/`arg` slots would make the rule NAC a predicate it produces (a self negation cycle the
# linter rejects). A coref demand has subject == object, so the two rules emit two coref calls
# for the same entity; `resolve_coref` is idempotent (rejected pairs stay rejected via
# `not_same_as`, kept pairs already linked — the materializer's `skip`), so the duplicate is
# harmless — the small cost of the uniform call shape.
DEMAND_COREF: list[Rule] = [
    Rule(
        key="demand.coref.subj",
        lhs=[Pat("?d", "d_subj", "?x")],
        rhs=[Pat("<call>?", "tool", "coref"), Pat("<call>?", "arg", "?x")],
    ),
    Rule(
        key="demand.coref.obj",
        lhs=[Pat("?d", "d_obj", "?x")],
        rhs=[Pat("<call>?", "tool", "coref"), Pat("<call>?", "arg", "?x")],
    ),
]

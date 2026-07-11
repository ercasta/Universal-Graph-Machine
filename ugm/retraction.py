"""
Reversible retraction — a truth-maintenance layer over the in-graph support, AS RULES
(docs/depythonization_design.md §4; the earlier `<quarantine>`-relocation driver is deleted).

A withdrawn fact and everything derived from it must go, reversibly. This is done entirely by
RULES over the (now matchable) provenance graph: seed `<retract> targets ?rel`; the CASCADE rule
propagates the marker along `proves`/`uses` to every dependent fact (aggressive/single-support
form, §11-stratifiable); the INTERPOSE rule HIDES each targeted fact by `rewire`-splicing an inert
`<retracted>` node into its 2-hop path — the matcher is untouched and the fact is resurrectable by
the inverse splice. The active graph stays clean (vision §11) and consumer rules need no guard tax.

The cascade is the existential support check of coreference_design §4b, now a rule rather than a
Python driver: a justification that USES a retracted fact loses its footing (except an `<axiom>`
proof). Base (asserted) facts have no justification and are never cascade candidates.

Marked `meta=True` (provenance-silent) so the truth-maintenance rules coexist in ONE `run()` with
prov-on reasoning without a regress. `coref` no longer retracts (it is additive), so this is the
sole TMS mechanism; `decide` defeat also seeds `<retract>` here.
"""
from __future__ import annotations

from . import provenance as prov
from .production_rule import Pat, Rule
from .world_model import Graph

NOT_SAME_AS = "not_same_as"     # the recorded rejection (resurrection = re-derive on demand)
RETRACT = "<retract>"           # a request marker: relation node ?rel is to be retracted
TARGETS = "targets"
RETRACTED = "<retracted>"       # the interposer spliced into a fact's path to hide it (inert)


def _ensure(graph: Graph, name: str) -> str:
    found = graph.nodes_named(name)
    return found[0] if found else graph.add_node(name)


# ---------------------------------------------------------------------------
# Retraction AS RULES — the cascade over now-matchable provenance (docs/depythonization_design.md)
# ---------------------------------------------------------------------------
#
# This replaced the earlier Python `cascade_retract` driver (quarantine-relocation), now DELETED:
# with provenance matchable by meta-rules and the `rewire` interposition primitive, the cascade is
# expressed as RULES. `coref` no longer retracts at all (it is additive, check-before-commit), so
# the rule path below is the sole truth-maintenance mechanism. Two facts about the shape decided
# the form:
#
#   * The EXACT cascade — "retract f iff ALL its justifications lose support" — needs "no live
#     support remains", i.e. recursion through negation (defeat <-> retract), which is
#     NON-STRATIFIABLE; vision §11 forbids non-stratified negation. So the exact form is not
#     plain rules.
#   * The AGGRESSIVE cascade — "retract f if SOME justification proving it uses a retracted fact,
#     unless f is an axiom" — is POSITIVE recursion on `targets` + negation only on the BASE
#     `<axiom>` predicate, hence STRATIFIED. It is exactly correct for SINGLE-SUPPORT derivations
#     (the decide/completion case and most chains). A MULTI-support fact it over-retracts is
#     recovered by monotone RE-DERIVATION (re-run the domain rules; a surviving derivation brings
#     it back) — sound, all rules, no non-stratified negation. Re-derivation is the caller's
#     existing run loop; not wired here yet (single-support is the current need).
#
# The action (hiding) is a `rewire` interposition: splice `<retracted>` into the fact's path so it
# stops matching, keeping the relation node (its `proves` provenance survives for the cascade).
# These rules are META rules (they name `proves`/`uses`, so the matcher lets them bind `<j:>` nodes)
# and are marked `meta=True` so they fire PROVENANCE-SILENT even inside a prov-on run — a firing
# that minted its own `<j:>` would be re-matched by `?j proves ?f` and regress. The `meta` flag is
# what lets them coexist in ONE run with prov-on reasoning (docs/coref_as_rules_design.md).

# CASCADE: a fact proved by a justification that USES a retracted fact is itself retracted
# (unless it is an asserted axiom — the base facts a cascade must never withdraw).
CASCADE_RULE = Rule(
    key="tms.cascade",
    lhs=[Pat(f"{RETRACT}?", TARGETS, "?rel"),        # ?rel is retracted
         Pat("?j", prov.USES, "?rel"),               # a justification uses it ...
         Pat("?j", prov.PROVES, "?f")],              # ... and proves ?f
    rhs=[Pat(f"{RETRACT}?", TARGETS, "?f")],         # -> ?f is retracted too
    nac=[Pat(prov.AXIOM, prov.PROVES, "?f")],        # unless ?f is an asserted base fact
    meta=True,                                       # provenance-silent (regress guard; may run in a prov-on run)
)

# INTERPOSE: hide a retracted fact by splicing `<retracted>` into its object edge. `?rel` is the
# relation node (bound by the demand); `?s ?rel ?o` binds its subject/object (the LHS names no
# provenance, so ?s/?o cannot bind the inert `proves` predecessor or an already-interposed edge).
INTERPOSE_RULE = Rule(
    key="tms.interpose",
    lhs=[Pat(f"{RETRACT}?", TARGETS, "?rel"),
         Pat("?s", "?rel", "?o")],
    rhs=[],
    rewire=[("cut", "?rel", "?o"),
            ("link", "?rel", f"{RETRACTED}?"),
            ("link", f"{RETRACTED}?", "?o")],
    meta=True,                                       # provenance-silent (creates nothing, but explicit)
)

RETRACT_RULES: list[Rule] = [CASCADE_RULE, INTERPOSE_RULE]


def seed_retract(graph: Graph, rel: str) -> str:
    """Mark relation node `rel` for retraction (`<retract> targets rel`). The cascade rules
    propagate the marker along provenance and the interpose rule hides each targeted fact."""
    r = graph.add_node(RETRACT)
    graph.add_relation(r, TARGETS, rel)
    return r


def retract(graph: Graph, rel: str) -> list:
    """Retract relation node `rel` and cascade its consequences, all by rules. Seeds
    `<retract> targets rel`, then runs `RETRACT_RULES` to a fixpoint. The rules are `meta=True`
    (provenance-silent), so this is safe whether or not the caller's run emits provenance; here we
    pass `provenance=False` since a standalone retraction needs none. Returns the firing journal.
    Hiding is by interposition, so it is reversible (a resurrect rule can splice the fact back).

    Runs on the ISA forward driver: the CASCADE rule (`proves`/`uses` meta-match, seen
    via run_bank's per-rule inert-visibility) propagates the marker, and the INTERPOSE rule's `rewire`
    lowers to the `INTERPOSE` opcode (implementation_plan.md Phase 0.5, isa-reference.md
    "Reserved: INTERPOSE / RESTORE")."""
    from .cnl.authoring import run_rules
    seed_retract(graph, rel)
    return run_rules(graph, RETRACT_RULES, provenance=False)


def record_rejection(graph: Graph, a: str, b: str) -> None:
    """Stash the rejection so the same wrong link is not re-hypothesized (the resurrection
    lean: remember only the rejection, re-derive the rest on demand)."""
    if not any(graph.has_key(r, NOT_SAME_AS) and b in graph.out(r)
               for r in graph.out(a)):
        graph.add_relation(a, NOT_SAME_AS, b)


def is_rejected(graph: Graph, a: str, b: str) -> bool:
    return (any(graph.has_key(r, NOT_SAME_AS) and b in graph.out(r) for r in graph.out(a))
            or any(graph.has_key(r, NOT_SAME_AS) and a in graph.out(r) for r in graph.out(b)))

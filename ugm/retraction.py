"""
Retraction — a truth-maintenance layer over the in-graph support, as COPY-ON-DELETE
(docs/mechanism_policy_separation.md, Probe 1; supersedes the earlier interpose-hiding driver).

A withdrawn fact and everything derived from it must go. Three cleanly-separated phases — the
mechanism/policy split made concrete:

  1. DECIDE (reasoning, read-only): the CASCADE rule finds the full set to retract by traversing
     `proves`/`uses` provenance — still RULES over the (now matchable) provenance graph. Seed
     `<retract> targets ?rel`; the cascade propagates the marker to every dependent fact
     (aggressive/single-support form, §11-stratifiable). This is the "what to delete" question and
     touches nothing.
  2. RECORD (policy): for each rel in the set, copy its pre-image (subject/predicate/object + its
     provenance) into an in-graph, meta-visible HISTORICAL RECORD (`record_history`) BEFORE it is
     deleted — copy-on-delete's "copy". The history NEVER leaves the graph (the HARD CONSTRAINT of
     the design: explanation is DATA, matchable, so the system can reason about its own reasoning);
     it is inert, so ordinary reasoning no longer sees the retracted fact but meta-reasoning still can.
  3. RETIRE (privileged mechanism): really delete the live relation edges + the rel node via the
     `RETIRE` opcode — real fact deletion, replacing the old `<retracted>` splice. `RETIRE` is NOT
     in the rule->program lowering vocabulary; only THIS driver assembles it (the privilege gate),
     so ordinary reasoning rules structurally cannot delete a fact.

Deletion is a BETWEEN-passes operation (retract runs its own fixpoint, separate from reasoning), so
monotonicity stays MECHANISM within a reasoning pass and becomes POLICY between passes. Resurrection
(`resurrect`) re-materializes a fact from its in-graph historical record (the RESTORE role, now
archive->live).

The cascade is the existential support check of coreference_design §4b, as a rule: a justification
that USES a retracted fact loses its footing (except an `<axiom>` proof). Base (asserted) facts have
no justification and are never cascade candidates. `CASCADE_RULE` is `meta=True` (provenance-silent)
so it coexists in ONE `run()` with prov-on reasoning without a regress.
"""
from __future__ import annotations

from . import provenance as prov
from .production_rule import Pat, Rule
from .world_model import Graph
from .attrgraph import valued
from .machine import Machine, RETIRE, State

NOT_SAME_AS = "not_same_as"     # the recorded rejection (resurrection = re-derive on demand)
RETRACT = "<retract>"           # a request marker: relation node ?rel is to be retracted
TARGETS = "targets"
RETRACTED = "<retracted>"       # legacy interpose marker (opcode kept; UNUSED by this TMS, see below)

# --- the in-graph historical record (copy-on-delete's archive, meta-visible / inert) ---------
HISTORY = "<history>"           # singleton root grouping retracted-fact records
RECORDS = "records"             # <history> -[records]-> <rec>
WAS_SUBJ = "was_subj"           # <rec> -[was_subj]-> the (surviving) subject entity
WAS_OBJ = "was_obj"             # <rec> -[was_obj]-> the (surviving) object entity
WAS_PRED = "was_pred"           # VALUED attr on <rec>: the retracted relation's predicate name


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
# The cascade only DECIDES the set; the ACTION (delete) is the driver's privileged RETIRE step, no
# longer a rule (copy-on-delete replaced the `<retracted>` interpose splice). CASCADE_RULE is a META
# rule (it names `proves`/`uses`, so the matcher lets it bind `<j:>` nodes) marked `meta=True` so it
# fires PROVENANCE-SILENT even inside a prov-on run — a firing that minted its own `<j:>` would be
# re-matched by `?j proves ?f` and regress. The `meta` flag lets it coexist in ONE run with prov-on
# reasoning (docs/coref_as_rules_design.md).

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

# NOTE — INTERPOSE_RULE is GONE. Retraction no longer HIDES a fact by splicing a `<retracted>`
# marker into its path; it DELETES the fact (copy-on-delete, below). The `INTERPOSE`/`RESTORE`
# opcodes + `lower_rewire` stay in the ISA for their own direct tests, just unused by the TMS
# (docs/mechanism_policy_separation.md §7 defers their removal to a post-probe cleanup).

RETRACT_RULES: list[Rule] = [CASCADE_RULE]


def seed_retract(graph: Graph, rel: str) -> str:
    """Mark relation node `rel` for retraction (`<retract> targets rel`). The cascade rule
    propagates the marker along provenance; the driver then retires each targeted fact."""
    r = graph.add_node(RETRACT)
    graph.add_relation(r, TARGETS, rel, control=True)   # control scaffolding (as the cascade's is),
    return r                                             # so it is never mistaken for rel's subject


def _retract_targets(graph: Graph) -> set[str]:
    """The rel nodes the DECIDE phase marked `<retract> targets ?rel` — the objects of every
    `targets` relation (the seed + everything the cascade added). Read into a set BEFORE any
    retire, so the decided set is fixed before the graph is mutated."""
    out: set[str] = set()
    for tn in graph.nodes_with_key(TARGETS):
        out.update(graph.out(tn))
    return out


def _obj_via(graph: Graph, node: str, key: str) -> str | None:
    """The object of the first `node -[key]-> obj` relation, walking raw edges (the record is inert,
    so `relations_from` — which short-circuits on an inert subject — cannot be used to read it)."""
    for rn in graph.out(node):
        if graph.has_key(rn, key):
            return next(iter(graph.out(rn)), None)
    return None


def _history_root(graph: Graph) -> str:
    found = graph.nodes_named(HISTORY)
    return found[0] if found else graph.add_node(HISTORY, inert=True)


def record_history(graph: Graph, rel: str) -> str:
    """RECORD phase (copy-on-delete's "copy"): archive relation `rel`'s pre-image into an in-graph,
    meta-visible HISTORICAL RECORD before it is retired, and redirect its provenance onto the record
    so the justification graph survives the delete. Returns the record node id.

    The record is a fresh INERT node carrying the retracted predicate (`was_pred`) and inert
    `was_subj`/`was_obj` edges to the (surviving) endpoint entities, grouped under the `<history>`
    root. Being inert, it is invisible to ordinary reasoning (so the retracted fact stops matching)
    yet visible to meta-reasoning — the HARD CONSTRAINT: explanation stays matchable DATA in the SAME
    graph, so `why`/reflection can still answer "what did we believe, and why was it retracted?"
    (docs/mechanism_policy_separation.md §1). The endpoint ENTITIES are NOT deleted (only the relation
    is retracted), so the record references them directly; a distinct meta-predicate (`was_subj` etc.)
    means the archive does not alias the live fact a raw 2-hop walk would re-see."""
    # the subject/object are the DOMAIN endpoints (non-inert AND non-control) — this excludes the
    # inert `proves`/`uses` provenance predecessors and the control `targets` scaffolding node that
    # also points AT rel (a `<retract> targets rel` marker), which would otherwise be misread as subj.
    subj = next((s for s in graph.into(rel) if not graph.is_inert(s) and not graph.is_control(s)), None)
    obj = next((o for o in graph.out(rel) if not graph.is_inert(o) and not graph.is_control(o)), None)
    pred = graph.predicate(rel)
    rec = graph.add_node(inert=True)
    graph.set_attr(rec, WAS_PRED, valued(pred))
    if subj is not None:
        graph.add_relation(rec, WAS_SUBJ, subj, inert=True)
    if obj is not None:
        graph.add_relation(rec, WAS_OBJ, obj, inert=True)
    graph.add_relation(_history_root(graph), RECORDS, rec, inert=True)
    # Retain provenance: redirect the inert proves/uses relation nodes that pointed AT `rel` to point
    # at the record instead, so `<j:> proves rec` / `<axiom> proves rec` / `<j:> uses rec` survive the
    # retire (the entity subject — non-inert — is left for RETIRE to drop with the rel node).
    for pv in list(graph.into(rel)):
        if graph.is_inert(pv):
            graph.remove_edge(pv, rel)
            graph.add_edge(pv, rec)
    return rec


def retract(graph: Graph, rel: str) -> list:
    """Retract relation node `rel` and its dependents — copy-on-delete over the ONE graph
    (docs/mechanism_policy_separation.md, Probe 1). Three cleanly-separated phases:

      DECIDE  — seed `<retract> targets rel` and run `RETRACT_RULES` (the CASCADE) to a fixpoint,
                accumulating the full set of rel nodes to retract (read-only reasoning; the rule is
                `meta=True`, so `provenance=False` is passed — a standalone retraction needs none).
      RECORD  — for each target, `record_history` copies its pre-image into the in-graph, meta-visible
                history (finished for the WHOLE set before any retire, so every pre-image is captured
                from still-live structure — the cascade's footing is never pulled mid-run).
      RETIRE  — for each target, run a `RETIRE(rel)` program: the PRIVILEGED deletion of the live
                relation. `RETIRE` is assembled ONLY here (the privilege gate — no rule lowering emits
                it), so ordinary reasoning rules cannot delete a fact.

    Returns [] (back-compat with callers that unpack a journal). The retracted fact's live relation
    is really GONE (no `<retracted>` splice); resurrect it from history with `resurrect`."""
    from .cnl.authoring import run_rules
    seed_retract(graph, rel)
    run_rules(graph, RETRACT_RULES, provenance=False)      # DECIDE (cascade to fixpoint)
    targets = _retract_targets(graph)
    for t in targets:                                       # RECORD (copy every pre-image first)
        if graph.has(t):
            record_history(graph, t)
    prog, m = [RETIRE(rel="r")], Machine()                 # RETIRE (privileged; assembled only here)
    for t in targets:
        if graph.has(t):
            m.apply(graph, prog, State({"r": t}))
    return []


def resurrect(graph: Graph, rec: str) -> str | None:
    """Re-materialize a retracted fact from its in-graph historical record `rec` back into the live
    graph (the RESTORE role, now archive->live). Reads the recorded subject/predicate/object and
    re-asserts the fact via the ISA authoring path (`load_fact_triples`), re-interning the surviving
    endpoint entities by name so the fact matches again. Because the history never left the graph,
    this is a read-of-history + re-assert, not a cross-structure copy. Returns the re-asserted rel
    node id, or None if the record is incomplete."""
    from .lowering import load_fact_triples
    subj = _obj_via(graph, rec, WAS_SUBJ)
    obj = _obj_via(graph, rec, WAS_OBJ)
    pred_attr = graph.get_attr(rec, WAS_PRED)
    if subj is None or obj is None or pred_attr is None:
        return None
    s_name, o_name, pred = graph.name(subj), graph.name(obj), str(pred_attr.value)
    load_fact_triples(graph, [(s_name, pred, o_name)])
    for r in graph.out(subj):
        if graph.has_key(r, pred) and obj in graph.out(r):
            return r
    return None


def record_rejection(graph: Graph, a: str, b: str) -> None:
    """Stash the rejection so the same wrong link is not re-hypothesized (the resurrection
    lean: remember only the rejection, re-derive the rest on demand)."""
    if not any(graph.has_key(r, NOT_SAME_AS) and b in graph.out(r)
               for r in graph.out(a)):
        graph.add_relation(a, NOT_SAME_AS, b)


def is_rejected(graph: Graph, a: str, b: str) -> bool:
    return (any(graph.has_key(r, NOT_SAME_AS) and b in graph.out(r) for r in graph.out(a))
            or any(graph.has_key(r, NOT_SAME_AS) and a in graph.out(r) for r in graph.out(b)))

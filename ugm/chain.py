"""
Phase 4.3 — CHAIN (firmware v0): demand-driven rule application over reified rules.

CHAIN is `processing_modes.md` mode 3 ("what would make that true"): a goal raises a `<demand>`;
the in-graph HEAD INDEX (Phase 3.3) selects only the rules whose head could produce it; each such
rule's body predicates raise SUB-demands; the demand set closes; then APPLY runs only the demanded
(relevant) rules to quiescence. The point vs. a forward rush (`run_bank`/`apply` over the whole
bank) is DEMAND-SCOPING: a rule that produces nothing the goal needs is never applied — the magic
set, made of visible `<demand>` control nodes rather than a hidden agenda.

v0 SCOPE (differentially gated against `run_bank` over the full bank):
  - demand is at the PREDICATE grain (a `<demand>` per relation name), not per bound goal tuple —
    so CHAIN restricts WHICH RULES run, not yet which tuples (bound-arg SIP is the v1 refinement,
    the GoalSolver already does the tuple grain). Completeness for the goal predicate is exact.
  - positive rules only (inherited from APPLY v0); the applied rules run forward to fixpoint.
"""
from __future__ import annotations

import warnings
from collections import Counter
from dataclasses import dataclass

from .attrgraph import AttrGraph
from .attrgraph import valued, GRADED, VALUED, NAME, CONTROL_MARK, INERT_MARK
from .apply import (
    _read_atoms, _fact_relnodes, _endpoints, _fact_exists, _find_fact_relnode, _record,
    _rel_in_scope, build_head_index, rules_producing, SCOPE,
)
from .machine import (Machine, SEED, FOLLOW, SET, TEST, SAME, MEMBER, OVERLAY, OVERLAY_BAND,
                      GRADE, VMATCH, DISTINCT, State)
from .machine import (ControlMachine, Continuation, Block, PRIM, SETI, DEC,
                      BRANCH, BRANCH_IF, SUSPEND, HALT)
from .production_rule import is_var, is_bound_literal, literal_name
from .vocabulary import SAME_AS

DEMAND = "<demand>"
# AXIS B BOUNDARY (ratified 2026-07-14): the demand/subgoal CHAIN stays IN THE GRAPH — it is NOT
# mechanical stepping. Distinguish two things the chain produces:
#   * the AGENDA / worklist / iteration order — "what to try next, in what order" — is mechanical
#     stepping. It is (and always was) a Python-LOCAL set (`chain_sip`'s `agenda`), a register. Correct.
#   * the SUBGOAL CHAIN — "to answer X I needed Y, which needed Z" — is the negative's EXPLANATION: an
#     assumed-no / UNKNOWN is justified by the searched closure (NAF: "I looked for P over its closure and
#     found nothing"), the negative-side analog of a `<j:>` proof tree. Explanation is reasoned-over, so
#     it stays a MATCHABLE graph node — the same reason provenance does, even though only META rules
#     touch either. (An earlier probe wrongly lifted this to a register; reverted — it was explanation,
#     not stepping.) The visible `<demand>` node is that subgoal record. The LINKED chain (built
#     2026-07-16, axis_b doc §5.4): under `provenance=True`, `<subgoal>` nodes in the FACT graph carry
#     parent -[raised]-> child pointers — the chain STRUCTURE, not just the flat set — so `explain`
#     can walk a negative's decomposition (see `subgoal_decomposition`).

# The linked subgoal chain's vocabulary. The chain is EXPLANATION, so it lives in the FACT graph (the
# Axis A hard constraint — where provenance `<j:>` nodes and `why` live), NOT in the rule graph the flat
# `<demand>` magic set inhabits (which `ask_goal` reifies fresh per call and discards). Endpoints are
# stored as NAMES (`_endpoint_name` — same grain as `on_subgoal` records and `<assumed>` provenance
# records), so an `assumed not:` line joins its decomposition by simple attr equality. `raised` rels are
# provenance-INERT (like `proves`/`uses`): visible to meta reads, never to ordinary fact matching.
SUBGOAL = "<subgoal>"
RAISED = "raised"


@dataclass(frozen=True)
class ById:
    """An explicit node-ID endpoint for a bound-tuple goal (Phase 8 NEXT STEP C — id-addressed goal path).

    A goal endpoint is normally a NAME: a VALUE the matcher resolves to candidate nodes via the
    label-less value-accelerator (`nodes_named` — iterate ALL same-named candidates, reason by topology,
    NEVER identity). That is the right default for CNL, but it forces a consumer holding legitimately
    DISTINCT same-named nodes (created directly, not via CNL) into global name-uniqueness, because the
    WRITE/seed side silently takes `nodes_named(...)[0]`. Wrapping a raw node id in `ById` PINS the
    endpoint to exactly that node: the demand seeds from it, matches walk out of it, and derived/assumed
    facts land on it — so identity is the consumer's to manage. Additive: only the id-addressed path
    constructs these; the name path is untouched (CNL consumers unaffected)."""
    node_id: str


def validate_ids(fact_g: AttrGraph, *endpoints) -> None:
    """Silent->loud (Phase 8 C): a `ById` endpoint pinning a node that is NOT in the graph is a caller
    bug (a stale/typo'd id), so raise at the boundary rather than seed an empty demand or write a phantom
    node. Names are untouched (a name may legitimately be new — it mints)."""
    for ep in endpoints:
        if isinstance(ep, ById) and not fact_g.has(ep.node_id):
            raise ValueError(f"ById({ep.node_id!r}) addresses a node that is not in the graph.")


# --- ISA VALUE OPERANDS (docs/attic/isa_value_operands_design.md §7 step 2, STRUCTURAL since (X)) --------
#
# The uniform POINTER model for demand-solver bindings: a register holds only a node-pointer; a NAME
# endpoint (`"ada"`) is carried as a pointer to its INTERNED value-node (a regular node carrying
# `<isa_operand_value>="ada"`, `AttrGraph.value_node`), and the operations that consume an endpoint
# INTERPRET the pointer — a value-node means "the entities named ada" (resolved exactly as the name was:
# `nodes_named`, max-over-mentions, write-by-name), any other node pins (`ById` semantics). Coref-class
# aggregation is untouched — it happens INSIDE the consuming operation (`Machine._operand_nodes`, the
# endpoint helpers below), which is what dissolves the fork-vs-aggregate crux (§3). Ratified + swapped
# 2026-07-14; with (X) (env -> `State.regs`) the pointer model is structural, no name path remains.


def _operand(fact_g: AttrGraph, endpoint):
    """A PUBLIC goal endpoint as carried by the solver: a bare NAME becomes the pointer to its interned
    value-node (the register file holds only node-pointers); a wildcard (None) and an already-pointing
    `ById` pass through. The boundary conversion `chain_sip` applies to its goal."""
    if isinstance(endpoint, str):
        return ById(fact_g.value_node(endpoint))
    return endpoint


def _operand_value_of(fact_g: AttrGraph, endpoint):
    """The VALUE a pointer endpoint references, when it points at a value-node — else None (an entity
    pin, a missing node, or a plain name, which is not a pointer). The single interpretation hook the
    endpoint helpers share: a pointer is a value endpoint iff its node CARRIES `<isa_operand_value>`
    (differentiation by attribute + use, never a kind)."""
    if isinstance(endpoint, ById) and fact_g.has(endpoint.node_id):
        return fact_g.operand_value(endpoint.node_id)
    return None


def _candidate_nodes(fact_g: AttrGraph, endpoint) -> list[str]:
    """The candidate node ids for a BOUND endpoint (read side): a `ById` PINS to exactly its node (empty
    if that node is absent — the pin is honest, never a silent fall-through to a same-named other) —
    UNLESS it points at a value-node, which resolves like the value it carries; a name resolves via the
    value-accelerator to every same-named node."""
    if isinstance(endpoint, ById):
        v = _operand_value_of(fact_g, endpoint)
        if v is not None:                                  # value-node pointer: resolve by name value
            return fact_g.nodes_named(v)
        return [endpoint.node_id] if fact_g.has(endpoint.node_id) else []
    return fact_g.nodes_named(endpoint)


def _endpoint_matches(fact_g: AttrGraph, node: str, endpoint) -> bool:
    """Does `node` satisfy a bound endpoint — id-identity for a `ById` (value-equality when it points
    at a value-node), name-equality for a name?"""
    if isinstance(endpoint, ById):
        v = _operand_value_of(fact_g, endpoint)
        if v is not None:
            return fact_g.name(node) == v
        return node == endpoint.node_id
    return fact_g.name(node) == endpoint


def _scope_key(fact_g: AttrGraph, endpoint) -> str:
    """The NAME used for a focus-scope membership test on an endpoint (focus frames hold names): a
    `ById` contributes its node's name (a value-node pointer its VALUE), a name contributes itself."""
    if isinstance(endpoint, ById):
        v = _operand_value_of(fact_g, endpoint)
        return v if v is not None else fact_g.name(endpoint.node_id)
    return endpoint


def _demand_endpoint(fact_g: AttrGraph, endpoint):
    """The plain string a `<demand>` trace node records for an endpoint (a value-node pointer shows its
    VALUE — the trace is identical to the name path's; an entity `ById` shows its id)."""
    if isinstance(endpoint, ById):
        v = _operand_value_of(fact_g, endpoint)
        return v if v is not None else endpoint.node_id
    return endpoint


def _same_as_neighbors(fact_g: AttrGraph, n: str) -> set[str]:
    """The nodes directly `same_as`-linked to `n`, either edge direction (the link is a declared
    congruence and its symmetric closure may not have fired yet — treat it undirected)."""
    out: set[str] = set()
    for rel in fact_g.succ(n):
        if fact_g.has_key(rel, SAME_AS):
            out |= fact_g.succ(rel)
    for rel in fact_g.pred(n):
        if fact_g.has_key(rel, SAME_AS):
            out |= fact_g.pred(rel)
    out.discard(n)
    return out


def _is_fact_entity(fact_g: AttrGraph, n: str) -> bool:
    """True iff `n` participates as a real fact-layer entity — it has at least one relation whose OTHER
    endpoint is non-control. This excludes a node that exists ONLY as reified rule/call-clause vocabulary
    (its sole attachment is a control `<t>`/`<call>`/pattern node): such a node carries a NAME but is not
    an entity a write competes for, so it must not inflate the same-named ambiguity count."""
    for rel in (*fact_g.succ(n), *fact_g.pred(n)):
        for other in (*fact_g.succ(rel), *fact_g.pred(rel)):
            # `other` is an EDGE endpoint, which is not guaranteed to be a MINTED node: a consumer that
            # passes a raw label where a node id is expected (`add_relation(a, "premium", "yes")`) wires an
            # edge to an unregistered id, and a shared literal like `yes` is exactly the object reused across
            # many triples (feedback #14). Such a phantom endpoint is not a fact entity a write competes for
            # (it isn't a node at all), so skip it — this is a read-only DIAGNOSTIC guard and must never
            # crash the query on `is_control`'s `self._nodes[nid]` KeyError.
            if other != n and fact_g.has(other) \
                    and not fact_g.is_control(other) and not fact_g.is_inert(other):
                return True
    return False


def _one_identity(fact_g: AttrGraph, nodes: list[str]) -> bool:
    """True iff every node in `nodes` is `same_as`-connected to the first — ONE coref identity (repeated
    mentions of the same name, the value-accelerator's intended case), where an EMIT `[0]`-pick composes
    across the link and is correct. False = GENUINELY DISTINCT same-named identities (the case a consumer
    should be warned about, and pin with `ById`). Undirected BFS over `same_as`, bounded to the small
    same-named candidate set."""
    if len(nodes) <= 1:
        return True
    seen = {nodes[0]}
    frontier = [nodes[0]]
    while frontier:
        for nb in _same_as_neighbors(fact_g, frontier.pop()):
            if nb not in seen:
                seen.add(nb)
                frontier.append(nb)
    return set(nodes) <= seen


def resolve_write_node(fact_g: AttrGraph, endpoint, *, where: str) -> str:
    """Resolve a WRITE/seed endpoint to a node id — the SINGLE discipline for turning a goal endpoint
    into a write target (EMIT, ask-user materialize, SUPPOSE pencil). A `ById` PINS to its node; a name
    reuses an existing same-named node or mints one. SILENT->LOUD (Phase 8 C): when a name resolves to
    GENUINELY DISTINCT same-named nodes (>1 identity, NOT merely coref mentions of one — `_one_identity`),
    the `[0]`-pick is now a WARNING naming `where`, with the fix (pass `ById`). Coref duplicates (same
    entity, multiple mentions, `same_as`-linked) do NOT warn — there the `[0]`-pick composes correctly.
    A VALUE-NODE pointer writes by its VALUE (the same reuse-or-mint discipline as the name it carries)
    — never onto the value-node itself, which is operand data, not an entity."""
    if isinstance(endpoint, ById):
        v = _operand_value_of(fact_g, endpoint)
        if v is None:
            return endpoint.node_id
        endpoint = v                                       # fall through to the name write path
    # FACT-LAYER only: `nodes_named` also returns control/inert scaffolding (reified rule/call args,
    # provenance) that the matcher already skips — a write must land on a real entity node.
    ex = [n for n in fact_g.nodes_named(endpoint)
          if not (fact_g.is_control(n) or fact_g.is_inert(n))]
    # AMBIGUITY is judged over genuine fact-layer ENTITIES (a node only reachable through control clause
    # vocabulary carries the name but is not an entity a write competes for), and only when they are not
    # one coref identity — so repeated mentions (`same_as`-linked) and reified call args stay quiet.
    entities = [n for n in ex if _is_fact_entity(fact_g, n)]
    if len(entities) > 1 and not _one_identity(fact_g, entities):
        warnings.warn(
            f"{where}: name {endpoint!r} resolves to {len(entities)} distinct nodes; writing to the "
            f"first ({ex[0]}). Pass ById(node_id) to target a specific node.", stacklevel=2)
    return ex[0] if ex else fact_g.add_node(endpoint)


class _Exhaustion:
    """A shared flag threaded through a demand-driven closure AND its nested negative sub-demands: set
    when any closure hits its round budget WITHOUT reaching fixpoint. NAF soundness needs the negated
    positive EXHAUSTED — a truncated closure means the absence read is not trustworthy, so the honest
    verdict is UNKNOWN ("I did not finish looking"), never a decided no (§14 fuel). This is the
    agent-not-theorem-prover payoff the forward exhaustive model cannot express — it always claims
    completeness. `check.py` reads the flag to distinguish a fuel-exhausted UNKNOWN from a fully-closed
    ASSUMED_NO."""
    __slots__ = ("exhausted",)

    def __init__(self) -> None:
        self.exhausted = False


# STRATIFICATION — where wrong answers hide. NAF is only sound on a STRATIFIED program (the negated
# positive must be fully resolvable BEFORE the negation is decided). The arbiter is the OBJECT-AWARE
# static `authoring.lint_stratifiable`, run at BANK LOAD (`load_corpus`/`load_rules`) — it accepts a
# bank like THIEF (`thief` depends on `not cleared`; `cleared` depends on nothing negative -> no cycle)
# and REJECTS a genuine negative cycle (`p :- not q`, `q :- not p`) with a `ValueError`.
#
# A RUNTIME ground-goal cycle guard (the ported `GoalSolver._completing`) is DELIBERATELY NOT used as
# the raising authority: it fires SPURIOUSLY on stratifiable banks. Closing the positive of a negative
# sub-goal can transiently re-demand that same negative through a HIGHER-stratum, non-productive rule —
# e.g. closing `cleared(bo)` runs the coref rule `?s is ?b when ?a same_as ?b and ?s is ?a`, which
# raises a wildcard `is(bo, ?)` demand that pulls in the `is`-producing `thief` rule, whose NAC
# re-demands `not cleared(bo)`. That is not a real cycle (object-aware analysis puts `thief` strictly
# ABOVE `cleared`); it is a demand-path artifact. So the chain PRUNES-and-CONTINUES on re-entry (below):
# a re-entered NAC blocks its (higher-stratum) rule and the closure proceeds, which is exactly correct
# under stratification — the higher-stratum rule cannot legitimately contribute to the lower stratum.
# Soundness rests on the load-time lint; a genuinely non-stratifiable bank never reaches the chain.


class NonStratifiable(Exception):
    """A genuine negative cycle. RAISED BY `authoring.lint_stratifiable`'s counterpart is a `ValueError`
    at load; this type is retained for callers that want to detect a non-stratifiable bank explicitly.
    The chain itself does NOT raise it at runtime (see the module note above — a runtime ground-goal
    guard fires spuriously on stratifiable banks with coref propagation)."""


# --- BOUND-TUPLE SIP (magic sets) — the demand-driven solver `chain_sip` --------------------------
#
# A demand is a bound tuple `(pred, subj|None, obj|None)` (a name or a wildcard), carried on a VISIBLE
# `<demand>` control node as `for=/subj=/obj=`. `chain_sip` restricts WHICH TUPLES are derived: a goal
# `is_a(socrates, ?)` demands only derivations ABOUT socrates, passing the bound subject sideways (SIP)
# down each rule body. Evaluation INTERLEAVES demand-raising with evaluation (a sub-demand for a body
# atom is raised while walking that body under a partial env, so a join variable bound by an earlier
# atom grounds the next atom's demand) and iterates to a fixpoint.
#
# (A predicate-GRAIN precursor, `chain`/`demand_closure`, was retired 2026-07-14 — superseded by this
# tuple-grain solver, which prunes not only WHICH RULES but WHICH TUPLES run.)
#
# SCOPE (differentially gated vs `run_bank`): positive rules, plain-literal predicates; names are
# unique-noded (an EMIT resolves a head name to its node, minting if absent — same as APPLY's
# `_resolve_head`); the per-derivation body bindings live in the machine's REGISTER FILE (`State.regs`,
# (X) — one binding model shared with the forward path).


def _mint_bound_demand(fact_g: AttrGraph, rule_g: AttrGraph,
                       demand: tuple[str, str | None, str | None]) -> str:
    """Materialize a bound-tuple demand as a VISIBLE `<demand>` node carrying `for=pred` and, when bound,
    `subj=`/`obj=` — a subgoal record (the negative's explanation, matchable in the graph): "I need `pred`
    about this subject". Endpoints are stringified (a `ById` shows its id, a value-node pointer its VALUE
    — `fact_g` is where the pointer resolves; the trace itself is written into `rule_g`)."""
    pred, subj, obj = demand
    d = rule_g.add_node(DEMAND, control=True)
    rule_g.set_attr(d, "for", valued(pred))
    if subj is not None:
        rule_g.set_attr(d, "subj", valued(_demand_endpoint(fact_g, subj)))
    if obj is not None:
        rule_g.set_attr(d, "obj", valued(_demand_endpoint(fact_g, obj)))
    return d


def _intern_subgoal(fact_g: AttrGraph, demand: tuple[str, str | None, str | None]) -> str:
    """The `<subgoal>` chain node for `demand` — INTERNED (get-or-create): a repeated provenance query
    over the same live KB reuses the tuple's existing node, so the chain never duplicates and every
    query's `raised` edges land on ONE node per goal. The node carries `for=pred` and, when bound,
    `subj=`/`obj=` as NAMES (`_endpoint_name` — the grain `<assumed>` records and `on_subgoal` speak,
    so explanation joins by equality). Control-marked like every trace node; the parent -[raised]->
    child edges are added by the chain_sip `visible` hook."""
    pred, subj, obj = demand
    s = _endpoint_name(fact_g, subj)
    o = _endpoint_name(fact_g, obj)
    existing = _subgoal_node(fact_g, pred, s, o)
    if existing is not None:
        return existing
    d = fact_g.add_node(SUBGOAL, control=True)
    fact_g.set_attr(d, "for", valued(pred))
    if s is not None:
        fact_g.set_attr(d, "subj", valued(s))
    if o is not None:
        fact_g.set_attr(d, "obj", valued(o))
    return d


def _raised_edge_exists(fact_g: AttrGraph, parent: str, child: str) -> bool:
    """Whether parent -[raised]-> child is already in the graph (the cross-query edge dedupe the
    per-call `chain_edges` set cannot see)."""
    return any(fact_g.has_key(rn, RAISED) and child in fact_g.out(rn)
               for rn in fact_g.out(parent))


def _subgoal_node(fact_g: AttrGraph, pred: str, subj: str | None, obj: str | None) -> str | None:
    """The `<subgoal>` chain node recording goal `(pred, subj, obj)` (names; None = wildcard), or None
    when no chain was recorded (a run without `provenance=True`, or a goal never demanded)."""
    for n in fact_g.nodes_named(SUBGOAL):
        f = fact_g.get_attr(n, "for")
        if f is None or str(f.value) != pred:
            continue
        s = fact_g.get_attr(n, "subj")
        o = fact_g.get_attr(n, "obj")
        if ((None if s is None else str(s.value)) == subj
                and (None if o is None else str(o.value)) == obj):
            return n
    return None


def subgoal_decomposition(fact_g: AttrGraph, pred: str, subj: str | None = None,
                          obj: str | None = None) -> list[tuple[str, str | None, str | None]]:
    """The sub-demands closing goal `(pred, subj, obj)` RAISED — one step of the linked subgoal chain
    (recorded under `provenance=True`): the `raised`-children of the goal's `<subgoal>` node, as
    `(pred, subj|None, obj|None)` NAME tuples, deterministically ordered. Empty when no chain exists.
    This is what lets `explain` walk a negative's decomposition ("assumed not L — deciding L looked
    for M and N") instead of only listing the flat magic set; recurse on each child for the full tree
    (`surface._searched_lines` does, cycle-guarded)."""
    n = _subgoal_node(fact_g, pred, subj, obj)
    if n is None:
        return []
    out: set[tuple[str, str | None, str | None]] = set()
    for rn in fact_g.out(n):                     # raw edges: `raised` rels are inert (provenance-style)
        if fact_g.has_key(rn, RAISED):
            for c in fact_g.out(rn):
                f = fact_g.get_attr(c, "for")
                if f is None:
                    continue
                s = fact_g.get_attr(c, "subj")
                o = fact_g.get_attr(c, "obj")
                out.add((str(f.value),
                         None if s is None else str(s.value),
                         None if o is None else str(o.value)))
    return sorted(out, key=lambda d: (d[0], d[1] or "", d[2] or ""))


def bound_demands(rule_g: AttrGraph) -> set[tuple[str, str | None, str | None]]:
    """The bound-tuple demands read back from the visible `<demand>` nodes (the magic set)."""
    out: set[tuple[str, str | None, str | None]] = set()
    for d in rule_g.nodes_named(DEMAND):
        f = rule_g.get_attr(d, "for")
        if f is None:
            continue
        s = rule_g.get_attr(d, "subj")
        o = rule_g.get_attr(d, "obj")
        out.add((str(f.value),
                 None if s is None else str(s.value),
                 None if o is None else str(o.value)))
    return out


def _ptr(fact_g: AttrGraph, st: State, tok: str):
    """The POINTER endpoint a rule token resolves to under the REGISTER FILE `st` ((X), docs/
    firmware_over_isa_design.md §4 — bindings live in `State.regs`, the machine's binding model, not a
    dict): a bound var -> its register's node (an entity pin a free slot bound, or a value-node pointer
    it was seeded with); a literal -> its interned value-node's pointer; an UNBOUND var -> None (a
    wildcard demand endpoint, an open slot to be bound by a fact). Consumers (`_facts_matching`,
    `_node_for_name`, `_bound_entity_nodes`) interpret the pointer by its node's attributes."""
    if is_var(tok):
        nid = st.regs.get(tok)
        return None if nid is None else ById(nid)
    return ById(fact_g.value_node(literal_name(tok)))


def _endpoint_name(fact_g: AttrGraph, endpoint):
    """The NAME an endpoint denotes: a `ById` -> its node's name (a value-node pointer -> its VALUE);
    a name -> itself; a wildcard (None) stays None. Used where a rule LITERAL (matched by name) meets
    a `ById` env/demand endpoint (matched by id), by `on_subgoal` records, and by the `<subgoal>`
    chain nodes — one name grain for everything explanation-facing. (A duplicate id-grain def that
    this one silently shadowed was deleted 2026-07-16.)"""
    if isinstance(endpoint, ById):
        v = _operand_value_of(fact_g, endpoint)
        return v if v is not None else fact_g.name(endpoint.node_id)
    return endpoint


def _bind_state(fact_g: AttrGraph, st: State, tok: str, ep) -> State | None:
    """Extend the register file binding `tok` to the pointer endpoint `ep` ((X): the solver carries
    ONLY `ById` node-pointers — an entity pin from a free slot, or an interned value-node, so pointer
    identity IS agreement: a distinct same-named node has a different id and correctly fails to unify,
    and interning makes the same value the same pointer). A literal must equal the endpoint BY NAME
    (its own echoed value-node unwraps via `_endpoint_name`; a free slot, which alone yields an entity
    pin, is by construction a var, never a literal). Returns the extended State, or None on conflict."""
    if is_var(tok):
        if not isinstance(ep, ById):                       # a name reaching here is a solver bug: every
            raise AssertionError(f"non-pointer endpoint {ep!r} for {tok!r}")   # carried endpoint points
        held = st.regs.get(tok)
        if held is not None:
            return st if held == ep.node_id else None
        return st.bind(tok, ep.node_id)
    return st if literal_name(tok) == _endpoint_name(fact_g, ep) else None


def _unify_head_with_demand(fact_g: AttrGraph, demand: tuple[str, str | None, str | None],
                            hs: str, hp: str, ho: str) -> State | None:
    """The REGISTER FILE a head atom `(hs, hp, ho)` inherits from a demand it can serve ((X): bindings
    live in `State.regs`): the predicates must match, and the demand's bound endpoint POINTERS seed the
    head's slots (a wildcard demand endpoint leaves the head slot open). None if the head can't produce
    the demanded tuple. A head VAR takes the pointer verbatim (a value-node for a name goal, an entity
    pin for an id-addressed one); a head LITERAL is matched against the pointer's name/value."""
    pred, dsubj, dobj = demand
    if hp != pred:
        return None
    st = State()
    for slot, ep in ((hs, dsubj), (ho, dobj)):
        if ep is None:
            continue
        nxt = _bind_state(fact_g, st, slot, ep)
        if nxt is None:
            return None
        st = nxt
    return st


def _rel_matches_pred(g: AttrGraph, rel: str, pred: str, scope: str | None) -> bool:
    """The per-rel half of `_fact_relnodes`, applied to a rel reached by TOPOLOGY (from a bound
    endpoint) rather than by the predicate index: `rel` is a VISIBLE fact relation for `pred` iff it
    carries the `pred` key, is not inert, and is not control — UNLESS it is the active SUPPOSE scope's
    pencil. Keeps the endpoint-driven paths behaviour-identical to the whole-predicate scan."""
    if not g.has_key(rel, pred) or g.is_inert(rel):
        return False
    if g.is_control(rel):
        return scope is not None and _rel_in_scope(g, rel, scope)
    return True


def _facts_matching_walk(fact_g: AttrGraph, pred: str,
                         subj_name: str | None, obj_name: str | None,
                         *, scope: str | None = None,
                         focus_scope: frozenset[str] | None = None) -> list[tuple[str, str]]:
    """The `(subj_name, obj_name)` of every FACT `pred` whose bound endpoints match the demand (a
    None endpoint is a wildcard). The bound-tuple analog of APPLY's whole-predicate scan — SIP
    prunes to the demanded subject/object. Within a SUPPOSE `scope`, this scope's pencil is visible too.

    ENDPOINT-DRIVEN (Phase-7-adjacent perf, the demand-driven-negation weak spot): when an endpoint is
    BOUND, reach the matching facts THROUGH that endpoint's node — the bound name resolves to candidate
    nodes via the `name` value-accelerator (a candidate SET to test, never identity — the label-less
    discipline holds), then local topology gives the (pred,subj)/(pred,obj) facts directly. SIP makes a
    bound endpoint almost always available, so the whole-predicate scan (which recomputed every `pred`
    fact's endpoint names to discard all but one subject) is the fallback ONLY for a fully-unbound demand.
    Behaviour-identical to the old scan; it just stops touching off-goal tuples.

    FOCUS-SCOPE (Phase 8.3b, docs/design/cnl_intake_design.md §3) — BOUNDED ATTENTION, opt-in and caller-selected
    (default None = whole-graph, behaviour-identical). When `focus_scope` is a set of in-play entity names
    (the top focus frame's centers), a fact is visible iff it TOUCHES the working set (either endpoint in
    scope). Reasoning then follows edges out of focus entities but cannot start from / jump to an entity
    disconnected from focus — so per-utterance cost tracks the focus closure, not the accreted session, and
    the coref fan-out is bounded to what is in play. This is a SEMANTIC scope, not a neutral perf tweak:
    off-focus facts leave the agent's attention (the agent-not-theorem-prover reading of §14)."""
    out: list[tuple[str, str]] = []

    def keep(s: str, o: str) -> bool:                     # bounded-attention: a fact is in scope iff it
        return focus_scope is None or s in focus_scope or o in focus_scope   # touches the working set

    # A BOUND slot returns its GIVEN endpoint (a name, or a `ById` — so a var bound to an id stays
    # pinned through `_bind`/EMIT); a FREE slot returns the discovered node's `ById` (the id-addressed
    # core, Stage 3 — so two DISTINCT same-named nodes bind to DISTINCT vars, which is what lets a
    # same-name value-match relate them instead of collapsing to one binding). The focus-scope test
    # always uses names (`_scope_key` unwraps a `ById`; free nodes read `fact_g.name` for the keep()).
    if subj_name is not None:                              # (pred, subj, ?) — walk OUT of the subject
        subj_key = _scope_key(fact_g, subj_name)
        for s in _candidate_nodes(fact_g, subj_name):
            if fact_g.is_control(s) or fact_g.is_inert(s):
                continue
            for rel in fact_g.succ(s):
                if not _rel_matches_pred(fact_g, rel, pred, scope):
                    continue
                for o in fact_g.succ(rel):
                    if fact_g.is_control(o) or fact_g.is_inert(o):
                        continue
                    if obj_name is not None and not _endpoint_matches(fact_g, o, obj_name):
                        continue
                    on = fact_g.name(o)
                    if keep(subj_key, on):
                        out.append((subj_name, obj_name if obj_name is not None else ById(o)))
        return out
    if obj_name is not None:                               # (pred, ?, obj) — walk INTO the object
        obj_key = _scope_key(fact_g, obj_name)
        for o in _candidate_nodes(fact_g, obj_name):
            if fact_g.is_control(o) or fact_g.is_inert(o):
                continue
            for rel in fact_g.pred(o):
                if not _rel_matches_pred(fact_g, rel, pred, scope):
                    continue
                for s in fact_g.pred(rel):
                    if fact_g.is_control(s) or fact_g.is_inert(s):
                        continue
                    sn = fact_g.name(s)
                    if keep(sn, obj_key):
                        out.append((ById(s), obj_name))
        return out
    for rel in _fact_relnodes(fact_g, pred, scope=scope):  # (pred, ?, ?) — the whole-predicate scan
        for s, o in _endpoints(fact_g, rel):
            sn, on = fact_g.name(s), fact_g.name(o)
            if keep(sn, on):
                out.append((ById(s), ById(o)))
    return out


# --- A1 + firmware §3/§5: the demand lookup as a SELF-CONTAINED ISA program ------------------------
#
# The bespoke `_facts_matching_walk` above is a SECOND matcher (a hand-written topology walk). A1's
# thesis: that walk IS the ISA matcher's walk — SET the bound endpoint node, FOLLOW to the rel, TEST
# the predicate key, FOLLOW to the other endpoint. `_facts_matching_isa` does exactly that through the
# ONE `Machine.match`. The VISIBILITY that used to be Python post-filters is now IN the program:
#   * the fact-read guard — control/inert as MARKER ATTRIBUTES (`CONTROL_MARK`/`INERT_MARK`, dual-
#     written with the legacy flags), tested by compiler-emitted `TEST(..., absent=True)` ops (§3:
#     uniform, never per-rule, never a privileged matcher skip);
#   * a bound second endpoint — `TEST` on the NAME value (a name/value-pointer goal) or `SET`+`SAME`
#     (an entity pin);
#   * focus attention — the register-pointed `MEMBER` live-set op (§5: the working set's CONTENTS are
#     driver policy, parked in `AttrGraph.registers[_FOCUS_LIVE]`; the membership TEST is mechanism);
#   * SUPPOSE scope-pencil visibility — the register-pointed `OVERLAY` op (§5's 'extend' face): a rel
#     must lack the control marker (the base) OR be in the active scope's pencil set (the overlay,
#     parked in `registers[_SCOPE_OVERLAY]`, derived transitionally from the `SCOPE` tags — the tag
#     stays the pencil's persistent explanation; the set is the read mechanism). With no scope the op
#     degenerates to the plain absent-test, so ONE program shape serves scoped and unscoped reads.
# NO Python post-filter remains — the read is entirely the program.
# A free slot wraps to `ById(node)` — native here, since the register already holds the node id.

_ISA_READER = Machine()   # skip_inert OFF: visibility lives in the PROGRAM (marker-attribute guards),
# never in a privileged machine mode — the walk (the oracle) applies the same skips by flag.

_CROSSCHECK = False   # A1 differential gate: when True, every `_facts_matching` asserts the ISA path
# agrees with the bespoke walk on that call (order-insensitive). The reference oracle (the walk) is
# retained; the production SWAP to the ISA path is the user's ratified gate (doc §4). Tests flip it on.

_FOCUS_LIVE = "<focus>"           # the live-set register the read program's MEMBER op points at
_SCOPE_OVERLAY = "<scope-overlay>"   # the live-set register the read program's OVERLAY op points at
_BAND_OVERLAY = "<fork-bands>"    # the {rel_id -> band} map register OVERLAY_BAND points at (banded mode)

# --- BANDED (marker-mode) reading — the possibilistic fold (docs/possibilistic.md S7.5 step 6) -----
#
# When the firmware stance is `uncertainty="banded"` (`FirmwarePolicy`, the GLOBAL opt-in — never a
# per-call switch), the demand read swaps its binary OVERLAY for OVERLAY_BAND: the overlay map holds
# EVERY fork's pencils at their `<likeliness>` band, and (inside a SUPPOSE scope) the active scope's
# pencils at CERTAIN — so the one map subsumes the binary scope overlay, and banded reasoning composes
# with SUPPOSE for free. The band rides the match SCORE (min t-norm ⇒ weakest-link, multi-hop free);
# the ENVIRONMENT (which fork-scopes a fact rests on) is read off the matched rel's `SCOPE` tag
# (transitively for a derived fork). Silent mode (`"silent"`, the default) never enters these paths —
# the crisp read is byte-identical. The fork/env vocabulary lives in `possibility.py`; imports are
# lazy (possibility → suppose → check → chain would otherwise cycle).

_CERTAIN = 1.0
_NO_ENV: frozenset = frozenset()


def _band_overlay(fact_g: AttrGraph, scope: str | None) -> dict[str, float]:
    """The OVERLAY_BAND map for a banded read: every fork pencil at its scope band, plus the active
    SUPPOSE scope's pencils at CERTAIN (in-scope pencil is crisp-in-scope, exactly the binary read)."""
    from .possibility import all_fork_bands
    bands = all_fork_bands(fact_g)
    if scope is not None:
        overlay = _scope_pencils(fact_g, scope)
        if overlay:
            bands.update((r, _CERTAIN) for r in overlay)
    return bands


def _rel_env(fact_g: AttrGraph, rel: str) -> frozenset:
    """The assumption ENVIRONMENT the matched rel rests on: ∅ for ink (and for an active-scope pencil —
    a SUPPOSE assumption is a stance already taken, not a weighed fork), else the fork's env
    (`_scope_env`: itself for a base fork, its stored parents for a derived one)."""
    from .possibility import _fork_scope_of, _scope_env, LIKELINESS
    fork = _fork_scope_of(fact_g, rel)
    if fork is None or fact_g.get_attr(fork, LIKELINESS) is None:
        return _NO_ENV
    return _scope_env(fact_g, fork)


def _env_ok(fact_g: AttrGraph, env: frozenset) -> bool:
    """Is the combined environment consistent (no two exclusive forks — shared `<choice>` or declared
    `disjoint_from` claims)? `possibility._env_consistent`, imported lazily."""
    from .possibility import _env_consistent
    return _env_consistent(fact_g, env)


def _find_banded_relnode(fact_g: AttrGraph, s_id: str, pred: str, o_id: str,
                         *, scope: str | None = None) -> str | None:
    """The rel node of `s -[pred]-> o` for a banded firing's PREMISE record: ink (or the active
    SUPPOSE scope's pencil) first, else any FORK pencil — a banded body may have matched through a
    fork, and provenance should point at the actual pencil fact so the proof tree can show its band."""
    rel = _find_fact_relnode(fact_g, s_id, pred, o_id, scope=scope)
    if rel is not None:
        return rel
    for r in fact_g.succ(s_id):
        if fact_g.has_key(r, pred) and not fact_g.is_inert(r) \
                and fact_g.get_attr(r, SCOPE) is not None and o_id in fact_g.succ(r):
            return r
    return None


def _record_assumptions(fact_g: AttrGraph, j: str,
                        assumed: list[tuple[str, str, str, float]]) -> None:
    """Journal the ABSENCES a banded firing leaned on: one inert `<assumed>` node per surviving NAC
    (`a_pred`/`a_subj`/`a_obj` + `a_pi` = how possible the counter-evidence was), wired
    `J --assumes--> <assumed>`. The positive-assumption half of the explanation (decision 6): a
    proof tree can now say "assumed not (cy is alibied) — counter-evidence only unlikely", not just
    show the positive premises. Inert, like all provenance — invisible to reasoning."""
    from .provenance import ASSUMES, ASSUMED
    for np, ns, no, pi in assumed:
        a = fact_g.add_node({NAME: valued(ASSUMED)}, inert=True)
        fact_g.set_attr(a, "a_pred", valued(np))
        fact_g.set_attr(a, "a_subj", valued(ns if ns is not None else "anyone"))
        fact_g.set_attr(a, "a_obj", valued(no if no is not None else "anything"))
        fact_g.set_attr(a, "a_pi", valued(pi))
        fact_g.add_relation(j, ASSUMES, a, inert=True)


def _guard(reg: str) -> list:
    """The compiler-emitted fact-read guard (§3): a fact endpoint/rel must carry NEITHER marker
    attribute. Uniform — an author can never forget it; the substrate stays kind-less."""
    return [TEST(reg, CONTROL_MARK, absent=True), TEST(reg, INERT_MARK, absent=True)]


def _scope_pencils(fact_g: AttrGraph, scope: str | None) -> frozenset[str] | None:
    """The OVERLAY live-set for the active SUPPOSE scope: the ids of ITS pencil rels (control rels
    tagged `SCOPE=scope`) — visible in-scope although control-marked. None (no overlay — the base
    absent-test alone) outside any scope. Transitional derivation from the persistent tags; the §5
    end-state has the suppose/chain WRITERS maintain the set incrementally as they pencil."""
    if scope is None:
        return None
    return frozenset(r for r in fact_g.nodes_with_key(SCOPE)
                     if (a := fact_g.get_attr(r, SCOPE)) is not None and a.value == scope)


def _bound_endpoint_ops(fact_g: AttrGraph, reg: str, endpoint) -> list:
    """The in-program test that register `reg` matches a BOUND second endpoint: an entity pin
    unifies registers (`SET` the pin + `SAME`); a name / value-node pointer tests the NAME value."""
    v = _operand_value_of(fact_g, endpoint)
    if isinstance(endpoint, ById) and v is None:           # entity pin -> register unification
        return [SET(reg + "'", endpoint.node_id), SAME(reg, reg + "'")]
    return [TEST(reg, NAME, cmp="=", value=v if v is not None else endpoint)]


def _facts_matching_isa(fact_g: AttrGraph, pred: str,
                        subj_name: str | None, obj_name: str | None,
                        *, scope: str | None = None,
                        focus_scope: frozenset[str] | None = None,
                        bands: bool = False) -> list[tuple]:
    """The single-atom demand fact lookup as a self-contained ephemeral ISA program (see the module
    note above). Behaviour-identical to `_facts_matching_walk` (differentially gated by
    `_CROSSCHECK`). With `bands=True` (marker mode, the possibilistic fold) the rel-guard's OVERLAY
    becomes OVERLAY_BAND over the merged fork/scope map and every result grows to
    `(s, o, band, env)`: `band` IS the match score (min t-norm), `env` the fork assumption-set."""
    out: list[tuple] = []
    prev_live = fact_g.registers.get(_FOCUS_LIVE)          # park the live-sets (policy) for the ops
    prev_overlay = fact_g.registers.get(_SCOPE_OVERLAY)    # (mechanism); transitional: derived from
    prev_bands = fact_g.registers.get(_BAND_OVERLAY)       # the parameters here, per call — later the
    fact_g.registers[_FOCUS_LIVE] = focus_scope            # drivers own them per run
    fact_g.registers[_SCOPE_OVERLAY] = _scope_pencils(fact_g, scope)
    if bands:
        fact_g.registers[_BAND_OVERLAY] = _band_overlay(fact_g, scope)
    try:
        rel_guard = [TEST("r", pred), TEST("r", INERT_MARK, absent=True),
                     OVERLAY_BAND("r", CONTROL_MARK, _BAND_OVERLAY) if bands
                     else OVERLAY("r", CONTROL_MARK, _SCOPE_OVERLAY)]

        def emit(st: State, s_val, o_val) -> None:
            if bands:
                out.append((s_val, o_val, st.score, _rel_env(fact_g, st.regs["r"])))
            else:
                out.append((s_val, o_val))

        if subj_name is not None:                          # (pred, subj, ?) — walk OUT of the subject
            prog = [SET("s", ""), *_guard("s"),
                    FOLLOW("r", "s", "out"), *rel_guard,
                    FOLLOW("o", "r", "out"), *_guard("o"),
                    *(_bound_endpoint_ops(fact_g, "o", obj_name) if obj_name is not None else ()),
                    MEMBER(("s", "o"), _FOCUS_LIVE)]
            for s in _candidate_nodes(fact_g, subj_name):
                prog[0] = SET("s", s)
                for st in _ISA_READER.match(fact_g, prog):
                    emit(st, subj_name,
                         obj_name if obj_name is not None else ById(st.regs["o"]))
            return out
        if obj_name is not None:                           # (pred, ?, obj) — walk INTO the object
            prog = [SET("o", ""), *_guard("o"),
                    FOLLOW("r", "o", "in"), *rel_guard,
                    FOLLOW("s", "r", "in"), *_guard("s"),
                    MEMBER(("s", "o"), _FOCUS_LIVE)]
            for o in _candidate_nodes(fact_g, obj_name):
                prog[0] = SET("o", o)
                for st in _ISA_READER.match(fact_g, prog):
                    emit(st, ById(st.regs["s"]), obj_name)
            return out
        prog = [SEED("r", pred, cmp=None), *rel_guard,     # (pred, ?, ?) — the whole-predicate scan
                FOLLOW("s", "r", "in"), *_guard("s"),
                FOLLOW("o", "r", "out"), *_guard("o"),
                MEMBER(("s", "o"), _FOCUS_LIVE)]
        for st in _ISA_READER.match(fact_g, prog):
            emit(st, ById(st.regs["s"]), ById(st.regs["o"]))
        return out
    finally:
        fact_g.registers[_FOCUS_LIVE] = prev_live
        fact_g.registers[_SCOPE_OVERLAY] = prev_overlay
        fact_g.registers[_BAND_OVERLAY] = prev_bands


def _facts_matching(fact_g: AttrGraph, pred: str,
                    subj_name: str | None, obj_name: str | None,
                    *, scope: str | None = None,
                    focus_scope: frozenset[str] | None = None,
                    bands: bool = False) -> list[tuple]:
    """The single-atom demand fact lookup (SIP) — on the SHARED ISA matcher (`_facts_matching_isa`,
    A1; production swap ratified 2026-07-14): forward and demand walk topology through the ONE
    `Machine.match`. The bespoke walk (`_facts_matching_walk`) is retained ONLY as the independent
    parity oracle: when `_CROSSCHECK` is set, every call asserts it agrees (order-insensitive).
    `bands=True` is the marker-mode read (results grow to `(s, o, band, env)`); the walk oracle is
    crisp-only, so the crosscheck applies to the silent read."""
    out = _facts_matching_isa(fact_g, pred, subj_name, obj_name, scope=scope,
                              focus_scope=focus_scope, bands=bands)
    if _CROSSCHECK and not bands:
        walk = _facts_matching_walk(fact_g, pred, subj_name, obj_name, scope=scope, focus_scope=focus_scope)
        if Counter(out) != Counter(walk):
            raise AssertionError(
                f"A1 demand-matcher divergence for ({pred!r},{subj_name!r},{obj_name!r}) "
                f"scope={scope!r} focus_scope={focus_scope!r}:\n  walk={walk!r}\n  isa ={out!r}")
    return out


def _node_for_name(fact_g: AttrGraph, name) -> str:
    """The node an EMIT writes to for a head endpoint. A `ById` head endpoint (an id-addressed goal that
    threaded a pin into the head var) pins to its node; a name reuses an existing same-named node or
    mints one — WARNING on an ambiguous name (`resolve_write_node`, the silent->loud [0]-pick)."""
    return resolve_write_node(fact_g, name, where="chain EMIT")


def _sideways_order(body: list[tuple[str, str, str]], bound: set[str]) -> list[tuple[str, str, str]]:
    """Order the body atoms SIDEWAYS-SAFE from the initially-`bound` variables: at each step take an
    atom that already has a pruning endpoint — a literal, or a variable bound by the head-unify or an
    earlier atom — so its sub-demand carries a bound endpoint and SIP prunes. (A df sort by predicate
    selectivity would instead front-load the most-selective atom, which — if its join var is not yet
    bound — raises an UNBOUND sub-demand `(pred, None, None)` that floods in every off-goal tuple; the
    binding order, not raw selectivity, is what keeps the magic set scoped.) A disconnected remainder
    (no bound/literal endpoint) falls back to input order — an unavoidable full scan, still correct."""
    def ready(tok: str) -> bool:
        return (not is_var(tok)) or (tok in bound)          # a literal prunes; a var only once bound

    bound = set(bound)
    remaining = list(body)
    order: list[tuple[str, str, str]] = []
    while remaining:
        idx = next((i for i, (s, _p, o) in enumerate(remaining) if ready(s) or ready(o)), 0)
        s_tok, p, o_tok = remaining.pop(idx)
        order.append((s_tok, p, o_tok))
        for t in (s_tok, o_tok):
            if is_var(t):
                bound.add(t)
    return order


def _read_graded(rule_g: AttrGraph, rule_node: str) -> list[tuple[str, str, float]]:
    """The reified graded conditions of `rule_node` as `(var, dim, threshold)` — the α-cut filters
    `rule_graph.write_rule` accreted (`<rule> -[graded]-> <graded>`), read back for match-time use."""
    out: list[tuple[str, str, float]] = []
    for rel, gc in rule_g.relations_from(rule_node):
        if not rule_g.has_key(rel, "graded"):
            continue
        v, d, t = (rule_g.get_attr(gc, "gc_var"), rule_g.get_attr(gc, "gc_dim"),
                   rule_g.get_attr(gc, "gc_threshold"))
        if v is not None and d is not None and t is not None:
            out.append((str(v.value), str(d.value), float(t.value)))
    return out


def _grades_pass(fact_g: AttrGraph, graded: list[tuple[str, str, float]], st: State) -> bool:
    """The α-cut DURING matching, as FIRMWARE ((X)): the reified graded conditions lower to an
    EPHEMERAL `GRADE` program run by the shared machine over the match's register file — the SAME op
    the forward path lowers to, no bespoke Python check. A value-node register aggregates
    max-over-mentions INSIDE the instruction (`Machine._operand_nodes`, the §3 coref-class semantics —
    any coreferent mention may carry the propagated degree). An unbound graded var is out of slice ->
    fail (never fire on an unevaluable α-cut)."""
    if any(var not in st.regs for var, _dim, _thr in graded):
        return False
    prog = [GRADE(var, dim, threshold=thr) for var, dim, thr in graded]
    return bool(_ISA_READER.match(fact_g, prog, init=[st]))


def _read_value_matches(rule_g: AttrGraph, rule_node: str) -> list[tuple[str, str, str, float | None]]:
    """The reified value-match conditions of `rule_node` as `(var_a, var_b, dim, threshold|None)` — the
    declared value-JOINs `rule_graph.write_rule` accreted (`<rule> -[value_match]-> <value_match>`), read
    back for match-time use (mirrors `_read_graded`)."""
    out: list[tuple[str, str, str, float | None]] = []
    for rel, vn in rule_g.relations_from(rule_node):
        if not rule_g.has_key(rel, "value_match"):
            continue
        a, b, d = (rule_g.get_attr(vn, "vm_a"), rule_g.get_attr(vn, "vm_b"), rule_g.get_attr(vn, "vm_dim"))
        t = rule_g.get_attr(vn, "vm_threshold")
        if a is not None and b is not None and d is not None:
            out.append((str(a.value), str(b.value), str(d.value),
                        None if t is None else float(t.value)))
    return out


def _bound_entity_nodes(fact_g: AttrGraph, bound) -> list[str]:
    """The fact-layer node(s) a bound env value denotes: a `ById` -> exactly its node (a value-node
    pointer -> the nodes named its VALUE, the coref-class aggregate the name denoted); a name -> the
    same-named fact-layer nodes (control/inert scaffolding skipped). Used to read an ENDPOINT's attribute
    value for a value-match."""
    if isinstance(bound, ById):
        v = _operand_value_of(fact_g, bound)
        if v is None:
            return [bound.node_id] if fact_g.has(bound.node_id) else []
        bound = v
    return [n for n in fact_g.nodes_named(bound)
            if not (fact_g.is_control(n) or fact_g.is_inert(n))]


def _vmatches_pass(fact_g: AttrGraph, vms: list[tuple[str, str, str, float | None]],
                   st: State) -> bool:
    """The DECLARED value-JOIN during matching, as FIRMWARE ((X)): the reified `ValueMatch`es lower to
    an EPHEMERAL `VMATCH` program — the SAME op the forward path lowers to, run by the shared machine
    over the match's register file. Exact mode (threshold None): equal VALUED `dim` values; graded
    mode: `1 - |deg_a - deg_b| >= threshold`; a value-node register aggregates over its coref class
    inside the instruction. An unbound var, or a missing value on either side, fails (never fire on an
    unevaluable join)."""
    if any(v not in st.regs for va, vb, _d, _t in vms for v in (va, vb)):
        return False
    prog = [VMATCH(va, vb, dim, threshold=thr) for va, vb, dim, thr in vms]
    return bool(_ISA_READER.match(fact_g, prog, init=[st]))


def _read_distincts(rule_g: AttrGraph, rule_node: str) -> list[tuple[str, str]]:
    """The reified distinctness conditions of `rule_node` as `(var_a, var_b)` — the declared
    inequalities `rule_graph.write_rule` accreted (`<rule> -[distinct]-> <distinct>`, feedback #11),
    read back for match-time use (mirrors `_read_value_matches`)."""
    out: list[tuple[str, str]] = []
    for rel, dn in rule_g.relations_from(rule_node):
        if not rule_g.has_key(rel, "distinct"):
            continue
        a, b = rule_g.get_attr(dn, "dn_a"), rule_g.get_attr(dn, "dn_b")
        if a is not None and b is not None:
            out.append((str(a.value), str(b.value)))
    return out


def _distincts_pass(fact_g: AttrGraph, dcs: list[tuple[str, str]], st: State) -> bool:
    """The DECLARED distinctness condition during matching, as FIRMWARE: the reified `Distinct`s lower
    to an EPHEMERAL `DISTINCT` program — the SAME op the forward path lowers to, run by the shared
    machine over the match's register file. Distinct = disjoint denotations (the instruction resolves a
    value-node pointer to its named entities, so a head-seeded name and a body-bound entity pin of the
    same entity correctly fail). An unbound var fails (never fire on an unevaluable condition)."""
    if any(v not in st.regs for va, vb in dcs for v in (va, vb)):
        return False
    prog = [DISTINCT(va, vb) for va, vb in dcs]
    return bool(_ISA_READER.match(fact_g, prog, init=[st]))


def _nac_blocks(fact_g: AttrGraph, rule_g: AttrGraph, nac_atoms: list[tuple[str, str, str]],
                st: State, *, scope: str | None, provenance: bool,
                focus_scope: frozenset[str] | None = None,
                neg_stack: frozenset[tuple[str, str | None, str | None]],
                fuel: "_Exhaustion | None", max_rounds: int, closed: set,
                policy=None, env: frozenset = _NO_ENV, parent_demand=None
                ) -> tuple[float, list[tuple[str, str, str, float]]] | None:
    """Decide the rule's NAC clauses by DEMAND-DRIVEN NEGATION-AS-FAILURE (firmware v3): return None
    iff some `not L(bound)` clause's POSITIVE holds — i.e. the rule must NOT fire for this match —
    else `(necessity, assumed)`: the NECESSITY the conjunction contributes to the conclusion
    (CERTAIN in silent mode; see the BANDED paragraph) and, in banded mode, the ASSUMPTIONS the
    firing leans on — one `(pred, subj, obj, Π)` per surviving NAC, so provenance can journal "this
    conclusion assumed `not L`, whose counter-evidence was Π-possible" (the inspectable-jump story,
    decision 6; empty in silent mode). Each NAC `L` is a NESTED NEGATIVE DEMAND: bind it by the register file, demand the positive `L` and run
    it to CLOSURE (a self-contained nested `chain_sip`, so "the positive failed" is read from L's
    COMPLETE extension — the goal-directed analog of stratifying L's producers BELOW this consumer),
    then read ABSENCE. Any matching L-fact -> the NAC fails -> block; none -> `not L` holds. NOTHING is
    materialized for the negative (monotone, §5-safe): the verdict is computed from the (empty) demand-
    closure — the SAME move CHECK makes at top level, pushed inside the rule body.

    BANDED (marker mode — `policy.banded`, docs/possibilistic.md S7.3): the absence read is graded.
    `Π(L)` = the best band L is reachable at over worlds COMPATIBLE with the rule body's `env`
    (a fork exclusive with the body's own assumptions can neither block nor weaken). `Π ≥ θ`
    (`policy.theta`, the bias-vs-decisiveness dial) blocks; a surviving clause contributes
    `N(¬L) = 1 − Π(L)` (possibility/necessity duality — the scale involution, not probability
    arithmetic), min-combined across clauses, so a NAF conclusion is only as strong as its
    counter-evidence is unlikely.

    STRATIFICATION (see the module note): the negative goal is pushed on `neg_stack` before its positive
    closure. A re-entry (`neg_goal in neg_stack`) is a HIGHER-stratum rule reached via a demand-path
    artifact — on a stratifiable bank (guaranteed by the load-time lint) it cannot legitimately fire in
    this lower stratum, so the chain PRUNES it: block this env and DO NOT recurse (returning "blocked"
    for the re-entered rule, continuing the outer closure). A wildcard endpoint (a NAC var the positive
    body left unbound) is an EXISTENTIAL NAC — `not L(x, ·)` holds iff NO `L(x, anything)` exists, which
    the wildcard `_facts_matching` reads directly.

    GENERATOR (brick #3, docs/attic/isa_control_machine.md §9.3): this is now a GENERATOR — instead of RECURSING
    into `chain_sip` to close a negative's positive, it YIELDS a subgoal request `("subgoal", neg_goal,
    child_neg_stack, parent_demand)` and the driver (`chain_sip`) closes it on an EXPLICIT control stack, then resumes
    here. The yield IS the `CALL`; the driver's stack IS the control stack — the subgoal descent lives in
    the machine's stack, not Python's. Operation order is unchanged (the driver services each yield
    synchronously before resuming), so the demand-driven NAF semantics are identical. Returns the block
    verdict via the generator's return value (`yield from` surfaces it)."""
    banded = policy is not None and policy.banded
    nec = _CERTAIN
    assumed: list[tuple[str, str, str, float]] = []
    for ns, np, no in nac_atoms:
        neg_goal = (np, _ptr(fact_g, st, ns), _ptr(fact_g, st, no))
        if neg_goal in neg_stack:
            return None                        # re-entry: prune the higher-stratum rule (block env)
        if neg_goal not in closed:             # MEMO: a negative's positive is closed ONCE per session.
            # `parent_demand` rides the request so the child frame's goal links into the SUBGOAL CHAIN
            # (a memoized re-encounter yields nothing — no new search happened, so no new chain link).
            yield ("subgoal", neg_goal, neg_stack | {neg_goal}, parent_demand)   # driver closes, resumes
            closed.add(neg_goal)               # facts are monotone + stratified -> the closure is stable,
        # so re-demands (the round loop re-services this env each round) just READ absence, never re-close.
        if banded:                                         # graded absence: θ gates, necessity weighs
            pi = max((b for _s, _o, b, e in
                      _facts_matching(fact_g, np, neg_goal[1], neg_goal[2],
                                      scope=scope, focus_scope=focus_scope, bands=True)
                      if not e or _env_ok(fact_g, env | e)),   # only worlds compatible with the body
                     default=0.0)
            if pi >= policy.theta:
                return None                                # L is too possible to negate -> block
            nec = min(nec, 1.0 - pi)                       # N(¬L) = 1 − Π(L)
            assumed.append((np, _endpoint_name(fact_g, neg_goal[1]),
                            _endpoint_name(fact_g, neg_goal[2]), pi))
        elif _facts_matching(fact_g, np, neg_goal[1], neg_goal[2], scope=scope, focus_scope=focus_scope):
            return None                                    # L holds -> the NAC fails -> block this env
        if fuel is not None and fuel.exhausted:
            return None             # the positive is not EXHAUSTED -> the NAC is UNDECIDED; do not fire
    return nec, assumed                                    # (the `fuel.exhausted` flag makes it UNKNOWN)


def _head_skolems(body: list[tuple[str, str, str]],
                  heads: list[tuple[str, str, str]]) -> set[str]:
    """The RHS-introduced SKOLEM tokens of a rule: a bound-literal (`<succ>?`) that appears in a head
    endpoint slot but NOWHERE in the body. These are the label-less substrate's genuine value invention —
    the skolem FUNCTION `f(args)` the forward path mints one-per-firing (`lowering.lower_rhs`). A plain
    RHS literal is NOT a skolem (it interns to its graph-wide node); an RHS-only VARIABLE is not one either
    (it is unsound — rejected at authoring, `reject_rhs_only_head_vars`). Only the bound-literal binder is."""
    body_toks = {t for atom in body for t in atom}
    return {t for hs, _hp, ho in heads for t in (hs, ho)
            if is_bound_literal(t) and t not in body_toks}


def _anchor_node(fact_g: AttrGraph, st: State, tok: str) -> str | None:
    """The already-bound fact-layer node a NON-skolem head endpoint denotes under the register file
    (an LHS-bound var or a plain literal) — the ARGUMENT a skolem is a function OF. None if the token
    is unbound. Never mints (a witness search must not create the very node it is looking for)."""
    ep = _ptr(fact_g, st, tok)
    if ep is None:
        return None
    nodes = _bound_entity_nodes(fact_g, ep)
    return nodes[0] if nodes else None


def _find_skolem_witness(fact_g: AttrGraph, sk_name: str,
                         constraints: list[tuple[str, str, bool]]) -> str | None:
    """The existing node that IS this firing's skolem `f(args)`, or None. A witness is a node NAMED
    `sk_name` that already stands in EVERY defining relation the skolem's head atoms assert against the
    firing's bound arguments (`constraints`: (pred, anchor_node, skolem_is_subject)). This is the demand
    counterpart of the forward path's per-firing identity — re-finding the skolem STRUCTURALLY, by its
    defining relations (the user's law: a minted node is identified by how it relates to the LHS match, not
    by a raw id or a fabricated name). Reusing it (instead of re-minting) is what lets check-before-derive
    trip on a re-served demand, so the closure CONVERGES instead of minting a fresh node every round.
    The `sk_name` restriction keeps the witness to a PRIOR SKOLEM of this name, never a coincidental real
    neighbour that happens to fill the functional role."""
    cand: set[str] | None = None
    for pred, anchor, sk_is_subj in constraints:
        if sk_is_subj:                                     # skolem -[pred]-> anchor (skolem is subject)
            here = {s for rel in fact_g.pred(anchor) if fact_g.has_key(rel, pred)
                    for s in fact_g.pred(rel) if fact_g.name(s) == sk_name}
        else:                                              # anchor -[pred]-> skolem (skolem is object)
            here = {o for rel, o in fact_g.relations_from(anchor)
                    if fact_g.has_key(rel, pred) and fact_g.name(o) == sk_name}
        cand = here if cand is None else (cand & here)
        if not cand:
            return None
    return sorted(cand)[0] if cand else None


def _resolve_skolems(fact_g: AttrGraph, heads: list[tuple[str, str, str]],
                     st: State, skolems: set[str]) -> dict[str, str]:
    """Bind each head skolem to ONE node id for this firing (shared across all its head atoms, like the
    forward path's per-firing `reg_of`): reuse the structural witness of its defining relations, or MINT a
    fresh node when none exists yet (round 1). Keyed on the LHS-bound anchors, so the SAME firing re-served
    next round re-finds the SAME node — the fix for the demand-path skolem blowup (feedback #2)."""
    out: dict[str, str] = {}
    for sk in skolems:
        constraints: list[tuple[str, str, bool]] = []
        for hs, hp, ho in heads:
            if hs == sk and ho != sk and (a := _anchor_node(fact_g, st, ho)) is not None:
                constraints.append((hp, a, True))
            elif ho == sk and hs != sk and (a := _anchor_node(fact_g, st, hs)) is not None:
                constraints.append((hp, a, False))
        node = _find_skolem_witness(fact_g, literal_name(sk), constraints) if constraints else None
        out[sk] = node if node is not None else fact_g.add_node(literal_name(sk))
    return out


def _head_endpoint_id(fact_g: AttrGraph, st: State, tok: str,
                      sk_ids: dict[str, str]) -> str | None:
    """The node id a head endpoint EMITs to: this firing's skolem node if `tok` is a skolem, else the
    bound var / literal pointer resolved to its write node (`_node_for_name` — a value-node pointer
    writes by its value). None for an unbound non-skolem slot."""
    if tok in sk_ids:
        return sk_ids[tok]
    ep = _ptr(fact_g, st, tok)
    return None if ep is None else _node_for_name(fact_g, ep)


def _solve_demand_rule(fact_g: AttrGraph, rule_g: AttrGraph, rule_node: str,
                       demand: tuple[str, str | None, str | None], mint,
                       *, provenance: bool = False, scope: str | None = None,
                       focus_scope: frozenset[str] | None = None,
                       neg_stack: frozenset[tuple[str, str | None, str | None]] = frozenset(),
                       fuel: "_Exhaustion | None" = None, max_rounds: int = 1000,
                       closed: set = frozenset(), policy=None) -> int:
    """Serve `demand` with the reified rule at `rule_node` (SIP): seed the env from the demand via
    head-unification, walk the body in SIDEWAYS-SAFE order raising a BOUND sub-demand per atom (bound
    by the env so far), read facts matching each sub-demand, DECIDE any NAC clauses by nested negative
    demand (`_nac_blocks`, NAF), and EMIT the head with check-before-derive. `mint(sub_demand)` records
    the sub-demand as a visible node. `provenance=True` journals each firing (RECORD, mode 9). Within a
    SUPPOSE `scope`, the scope's pencil facts are visible to the body match and each EMIT is written in
    PENCIL (a control rel node tagged `scope`), so nothing touches ink. `neg_stack` carries the negative
    goals being resolved up-stack (the NAF cycle guard). Returns #facts EMITted this call.

    GENERATOR (brick #3): a generator — its NAC decision `yield from`s `_nac_blocks`, so a nested negative
    subgoal is a request the driver (`chain_sip`) services on the explicit control stack rather than Python
    recursion. With no NAC it yields nothing and returns the fired count (still a generator; `yield from`
    reads its return value).

    BANDED (marker mode — `policy.banded`, docs/possibilistic.md S7.5 step 6): the body walk threads a
    `(state, band, env)` triple per partial match — the band MIN-composes across atoms (weakest link),
    the env UNIONs the fork assumption-sets and PRUNES an inconsistent combination (two exclusive
    forks, ATMS); the NAC folds its necessity into the band; and the EMIT is graded: a CERTAIN,
    assumption-free head writes exactly as today (ink, or scope pencil), an uncertain one writes a
    DERIVED FORK at its band carrying its env, re-emitted only at a STRICTLY better band (monotone-up
    on a finite lattice, so the round loop still converges). Silent mode threads the constant
    (CERTAIN, ∅) and is behaviour-identical."""
    body = _read_atoms(rule_g, rule_node, "lhs")
    heads = _read_atoms(rule_g, rule_node, "rhs")
    # A NAC atom IDENTICAL to a head atom is an IDEMPOTENCY memo (`?a rel ?c when … and not ?a rel ?c`,
    # the check-before-derive guard on a recursive/transitive rule), NOT epistemic negation. The monotone
    # chain already refuses to re-derive an existing fact (`_fact_exists` before EMIT), so it is subsumed
    # — and treating it as NAF would (correctly, but uselessly) flag the rule's head as depending
    # negatively on itself. Drop it; only GENUINE NACs (on another tuple) get the nested-negative-demand.
    nac = [n for n in _read_atoms(rule_g, rule_node, "nac") if n not in heads]
    skolems = _head_skolems(body, heads)   # RHS-introduced value invention (feedback #2), keyed per firing
    graded = _read_graded(rule_g, rule_node)
    value_matches = _read_value_matches(rule_g, rule_node)
    distincts = _read_distincts(rule_g, rule_node)
    rule_key = rule_g.name(rule_node) if provenance else ""

    seeds: list[State] = []                                # (X): bindings live in the REGISTER FILE
    for hs, hp, ho in heads:
        st0 = _unify_head_with_demand(fact_g, demand, hs, hp, ho)
        if st0 is not None and st0 not in seeds:
            seeds.append(st0)

    banded = policy is not None and policy.banded

    fired = 0
    for st0 in seeds:
        states = [(st0, _CERTAIN, _NO_ENV)]                # (register file, band, environment)
        for s_tok, bp, o_tok in _sideways_order(body, set(st0.regs)):   # SIP: each atom demanded
            nxt: list[tuple[State, float, frozenset]] = [] # under the register file so far
            for st, band, env in states:
                s_ep = _ptr(fact_g, st, s_tok)             # the endpoints as CARRIED: node-pointers
                o_ep = _ptr(fact_g, st, o_tok)             # (a literal -> its interned value-node)
                mint((bp, s_ep, o_ep))
                for m in _facts_matching(fact_g, bp, s_ep, o_ep, scope=scope,
                                         focus_scope=focus_scope, bands=banded):
                    if banded:
                        fs, fo, fb, fe = m
                    else:
                        (fs, fo), fb, fe = m, _CERTAIN, _NO_ENV
                    st1 = _bind_state(fact_g, st, s_tok, fs)
                    if st1 is None:
                        continue
                    st2 = _bind_state(fact_g, st1, o_tok, fo)
                    if st2 is None:
                        continue
                    if fe:
                        ne = env | fe                      # ATMS: an env uniting exclusive forks is an
                        if not _env_ok(fact_g, ne):        # impossible world — prune the join branch
                            continue
                    else:
                        ne = env
                    nxt.append((st2, band if fb >= band else fb, ne))   # min-band: weakest link
            states = nxt
        for st, band, env in states:                       # EMIT every head atom per full match
            if graded and not _grades_pass(fact_g, graded, st):           # α-cut: ephemeral GRADE prog
                continue
            if value_matches and not _vmatches_pass(fact_g, value_matches, st):   # ephemeral VMATCH prog
                continue
            if distincts and not _distincts_pass(fact_g, distincts, st):   # ?a != ?b: ephemeral DISTINCT
                continue
            assumed: list[tuple[str, str, str, float]] = []
            if nac:
                res = yield from _nac_blocks(fact_g, rule_g, nac, st, scope=scope,   # NAF: absence
                                             focus_scope=focus_scope,                # decides — the
                                             provenance=provenance, neg_stack=neg_stack,  # subgoal is
                                             fuel=fuel, max_rounds=max_rounds, closed=closed,  # a yield
                                             policy=policy, env=env, parent_demand=demand)
                if res is None:                            # a NAC's positive holds (or cleared θ)
                    continue
                nec, assumed = res
                band = band if nec >= band else nec        # graded negation: fold in N(¬L)
            sk_ids = _resolve_skolems(fact_g, heads, st, skolems) if skolems else {}
            for hs, hp, ho in heads:
                s_id = _head_endpoint_id(fact_g, st, hs, sk_ids)
                o_id = _head_endpoint_id(fact_g, st, ho, sk_ids)
                if s_id is None or o_id is None:           # unbound non-skolem head slot — out of slice
                    continue
                if banded and (band < _CERTAIN or env):
                    # BANDED EMIT: an uncertain conclusion is a DERIVED FORK at its band, carrying its
                    # assumption env — never ink. Idempotence is graded: re-emit only STRICTLY better.
                    have = max((b for _s, _o, b, _e in
                                _facts_matching(fact_g, hp, ById(s_id), ById(o_id),
                                                scope=scope, focus_scope=focus_scope, bands=True)),
                               default=0.0)
                    if have >= band:
                        continue
                    from .possibility import fork_fact
                    head_node = fork_fact(fact_g, band, s_id, hp, o_id, derived_env=env)
                    fired += 1
                    if provenance:                         # RECORD (mode 9): journal the firing —
                        j = _record(fact_g, rule_key, head_node,   # premises found through the forks
                                    [_find_banded_relnode(fact_g,
                                                          _node_for_name(fact_g, _ptr(fact_g, st, bs)),
                                                          bp2,
                                                          _node_for_name(fact_g, _ptr(fact_g, st, bo)),
                                                          scope=scope)
                                     for bs, bp2, bo in body])
                        _record_assumptions(fact_g, j, assumed)   # "what was assumed" (decision 6)
                    continue
                if not _fact_exists(fact_g, s_id, hp, o_id, scope=scope):
                    # EMIT: an ink fact normally, but PENCIL (control + scope tag) inside a SUPPOSE scope
                    head_node = fact_g.add_relation(s_id, hp, o_id, control=(scope is not None))
                    if scope is not None:
                        fact_g.set_attr(head_node, SCOPE, valued(scope))
                    fired += 1
                    if provenance:                         # RECORD (mode 9): journal the firing
                        _record(fact_g, rule_key, head_node,
                                [_find_fact_relnode(fact_g, _node_for_name(fact_g, _ptr(fact_g, st, bs)),
                                                    bp2, _node_for_name(fact_g, _ptr(fact_g, st, bo)),
                                                    scope=scope)
                                 for bs, bp2, bo in body])
    return fired


class _Frame:
    """The driver-owned POLICY state of one goal-closure frame (the control machine owns the LOOP):
    the frame's local agenda (its demand sub-tree), the running derivation count, and `gen` — the
    mid-round continuation (the round generator parked while a NAC subgoal is being closed). The
    scalars the LOOP branches on (round budget, progress, pending-subgoal flag) live in the machine's
    CONTROL REGISTERS, not here (Axis B: stepping state is a register)."""
    __slots__ = ("agenda", "total", "gen")

    def __init__(self, goal) -> None:
        self.agenda: set[tuple] = {goal}
        self.total = 0
        self.gen = None


def _round(fact_g: AttrGraph, rule_g: AttrGraph, frame: _Frame, *, neg_stack, provenance,
           scope, focus_scope, fuel, max_rounds, closed, visible, policy=None):
    """ONE fixpoint round over the frame's agenda, as a GENERATOR (brick #3): serve every standing
    demand with the rules that produce it (raising bound sub-demands and EMITting); a NAC's negative
    subgoal is YIELDed up (the `advance` PRIM turns the yield into a machine `SUSPEND`). Returns
    `(fired, newly)` — the progress the loop's `BRANCH_IF` tests."""
    newly: set[tuple] = set()

    fired = 0
    for demand in frame.agenda:
        def mint(d, _parent=demand):                       # the serving demand is the sub-demand's PARENT
            if d not in frame.agenda and d not in newly:
                newly.add(d)
                visible(d, neg_stack, _parent)             # visible magic-set node (trace), minted once
            elif provenance:                               # already-minted: the chain may still owe this
                visible(d, neg_stack, _parent)             # parent a `raised` edge (multi-parent DAG)

        for rn in rules_producing(rule_g, demand[0]):
            fired += (yield from _solve_demand_rule(
                fact_g, rule_g, rn, demand, mint,
                provenance=provenance, scope=scope, focus_scope=focus_scope,
                neg_stack=neg_stack, fuel=fuel, max_rounds=max_rounds, closed=closed,
                policy=policy))
    return fired, newly


def _frame_program(fact_g: AttrGraph, rule_g: AttrGraph,
                   goal: tuple[str, str | None, str | None], *, neg_stack, provenance, scope,
                   focus_scope, fuel, max_rounds, closed, visible, policy=None, parent=None):
    """Close ONE goal's positive to fixpoint — the per-goal round-loop as a CONTROL-MACHINE PROGRAM
    (Decision 3, docs/attic/firmware_over_isa_design.md §6): a `PRIM` runs (or, after a serviced subgoal,
    CONTINUES) one round; `BRANCH_IF` loops it to fixpoint under a `SETI`/`DEC` round budget — the
    same block shape as `run_bank`'s fixpoint (docs/attic/isa_control_machine.md §9.5); fuel exhaustion is
    the budget branch falling through (fuel→UNKNOWN honesty). A pending NAC subgoal leaves the
    machine as a `SUSPEND` whose `Continuation` the driver (`chain_sip`) services (brick #4 — what
    was a Python generator yield at the frame boundary is now a machine suspension). Returns
    `(program, frame)`; the frame carries the driver-owned policy state (`_Frame`)."""
    visible(goal, neg_stack, parent)      # parent = the demand whose NAC spawned this frame (None: root)
    frame = _Frame(goal)

    def advance(g, stream, ctrl):
        # one upper-interpreter step: run/continue the round generator. flag 1 = a subgoal request is
        # parked in ctrl["req"] (the SUSPEND payload); flag 0 = the round completed (progress set).
        gen = frame.gen
        if gen is None:
            gen = _round(fact_g, rule_g, frame, neg_stack=neg_stack, provenance=provenance,
                         scope=scope, focus_scope=focus_scope, fuel=fuel,
                         max_rounds=max_rounds, closed=closed, visible=visible, policy=policy)
        try:
            req = gen.send(None)
        except StopIteration as e:
            fired, newly = e.value
            frame.agenda |= newly
            frame.total += fired
            frame.gen = None
            ctrl["progress"] = 1 if (fired or newly) else 0
            return stream, 0
        frame.gen = gen                                    # park the mid-round continuation
        ctrl["req"] = req                                  # ("subgoal", neg_goal, child_neg_stack, parent)
        return stream, 1

    def exhaust(g, stream, ctrl):
        if fuel is not None:                               # budget spent short of fixpoint -> the
            fuel.exhausted = True                          # closure is not EXHAUSTED (fuel->UNKNOWN)
        return stream, 0

    program = [
        Block(control=[SETI("budget", max_rounds)]),
        Block(label="round", prim=PRIM(advance, out="ev"),
              term=BRANCH_IF("ev", ">", 0, "wait")),          # NAC subgoal pending -> suspend
        Block(term=BRANCH_IF("progress", "=", 0, "done")),    # quiet round -> fixpoint (converged)
        Block(control=[DEC("budget")],
              term=BRANCH_IF("budget", ">", 0, "round")),     # budget left -> next round
        Block(prim=PRIM(exhaust), term=BRANCH("done")),       # progress but no budget -> fuel
        Block(label="wait", term=SUSPEND(request_reg="req")),
        Block(term=BRANCH("round")),                          # resumed -> continue the SAME round
        Block(label="done", term=HALT()),
    ]
    return program, frame


def chain_sip(fact_g: AttrGraph, goal: tuple[str, str | None, str | None], *,
              rules: AttrGraph | None = None, max_rounds: int = 1000,
              provenance: bool = False, scope: str | None = None,
              focus_scope: frozenset[str] | None = None, on_subgoal=None, policy=None,
              _neg_stack: frozenset[tuple[str, str | None, str | None]] = frozenset(),
              _fuel: "_Exhaustion | None" = None, _closed: set | None = None) -> int:
    """Answer a BOUND-TUPLE goal `(pred, subj|None, obj|None)` demand-driven with SIP: raise the goal
    as a bound `<demand>`, then repeatedly serve every standing demand with the rules that produce it
    (each service raises the bound sub-demands its body needs and EMITs), to a fixpoint. Returns
    #facts derived. Complete for the goal tuple (derives every goal-matching fact the full closure
    does) while pruning to demanded TUPLES — a rule is skipped not only when its predicate is
    irrelevant but when its subject/object is (the grain finer than v0's `chain`). The magic set is
    the visible bound `<demand>` nodes. Inside a SUPPOSE `scope` (Phase 5.3) the chain reasons over the
    scope's pencil facts as well as ink and EMITs its derivations back in PENCIL — same-graph, not a
    branch.

    CONTROL-MACHINE PORT (brick #3 §9.3 + Decision 3, firmware doc §6). Each goal-closure frame is a
    CONTROL-MACHINE PROGRAM (`_frame_program`: PRIM round + BRANCH_IF fixpoint loop + SETI/DEC budget —
    run_bank's §9.5 shape), and `chain_sip` is a DRIVER over an EXPLICIT STACK of suspended machines:
    when a frame's NAC needs a negative closed, its program SUSPENDs with the subgoal as the
    `Continuation.request`; the driver pushes a child frame program (with `neg_stack | {neg_goal}`, so
    the stratification stack IS the control stack), runs it to completion (mutating the SHARED,
    monotone graph), then RESUMEs the parent's continuation mid-round — the same DFS order as the old
    recursion, so behaviour is identical (the reasoning suite is the differential oracle). What was a
    Python generator yield at the frame boundary is now a machine suspension (brick #4).

    The agenda stays LOCAL to each frame (seeded from its goal, grown only by the sub-demands its own
    rules raise), and the visible flat `<demand>` trace is minted ONLY for the top-level goal (`neg_stack`
    empty) — a nested negative frame mints no flat trace. Under `provenance=True` the LINKED SUBGOAL
    CHAIN is additionally recorded at EVERY depth: `<subgoal>` nodes in the FACT graph with parent
    -[raised]-> child pointers (in-frame sub-demands link under the demand being served; a NAC child
    frame's goal links under the demand whose rule raised the NAC), so `subgoal_decomposition` /
    `explain` can walk an assumed-no's search structure. Self-containment (a NAC closes ONLY its
    negated positive `L`, never re-entering the consumer whose NAC is being decided) is preserved: each
    frame is a distinct goal-closure on the stack; the `_closed`/`neg_stack` memo + prune keep NAF's
    'the positive failed' read from L's COMPLETE extension.

    ONE-GRAPH DEFAULT (the fold, firmware doc §7 step 4): the reified rules live in `rules` — by
    default the FACT GRAPH ITSELF (rules are graph data like any other, segregated only by the
    control/pattern marker attributes). Passing a separate graph keeps the classic split layout — a
    consumer's choice (e.g. a fresh rule bank per hypothesis), no longer a requirement.

    `on_subgoal` (an OBSERVER, never a control hook — like `trace`, it cannot perturb reasoning) fires
    once per goal-closure FRAME as it is entered and again as it resolves, with a record
    `{pred, subj, obj, depth, phase, found}`: `depth` is the negation-stack depth (0 = the top goal;
    ≥1 = a NAF check the machine raised to decide a `not L` clause), `phase` is `"enter"`/`"resolve"`,
    and `found` (on resolve) is whether any fact matched. Because a frame is spawned ONLY for the top
    goal and for NAC negatives (positive sub-demands and same_as coref are in-frame demand nodes, not
    frames), the callback stream is exactly "the questions the machine asked itself" — the ordered
    subgoal chain, free of coref noise. This is the demand-side companion to the provenance `derive`
    trace (which records what was concluded); together they explain a demand-driven answer.

    `policy` (the possibilistic fold, docs/possibilistic.md S7.5): a `FirmwarePolicy` whose
    `uncertainty="banded"` turns on MARKER-MODE reasoning for the whole run (the global stance —
    reads see every fork at its band, joins min-accumulate + track environments, NAF is the θ-cut
    with graded necessity, uncertain conclusions emit as derived forks). None (or `"silent"`) is
    today's behaviour, byte-identical — forks stay silent-until-assumed."""
    rule_g = rules if rules is not None else fact_g        # the fold: one graph unless split by choice
    validate_ids(fact_g, goal[1], goal[2])                 # id-addressed pins must exist (silent->loud)
    # §7.2 (value operands): the goal's NAME endpoints become value-node POINTERS at this boundary, so
    # everything the solver carries downstream (env seeds, sub-demands, NAC goals) is a node-pointer.
    goal = (goal[0], _operand(fact_g, goal[1]), _operand(fact_g, goal[2]))
    build_head_index(rule_g)                               # idempotent
    if _closed is None:
        _closed = set()                                    # NAC-closure MEMO, shared across all frames
    # The VISIBLE `<demand>` trace is minted lazily and ONLY at the top level (`neg_stack` empty), deduped
    # by ONE set shared across frames (only the root frame ever mints — nested frames pass a non-empty
    # neg_stack, so the flat half no-ops). A nested negative closure needs no flat trace.
    minted: set[tuple[str, str | None, str | None]] = set()
    # The LINKED SUBGOAL CHAIN (axis_b §5.4) — EXPLANATION, so it is (a) recorded only under
    # `provenance=True` (the RECORD stance, like `<j:>` nodes), (b) written into the FACT graph (where
    # `why` reads — the flat set's rule_g is discarded by `ask_goal` per call), and (c) minted at EVERY
    # depth (a NAC child frame's goal links under the demand whose NAC spawned it), so an assumed-no's
    # decomposition is walkable. Deduped per tuple (a demand raised by two parents is a DAG node with
    # two `raised` in-edges); a self-raising recursive demand adds no self-edge.
    chain_nodes: dict[tuple, str] = {}
    chain_edges: set[tuple] = set()

    def visible(d, ns, parent=None):
        if not ns and d not in minted:                     # top-level magic set only (the flat trace)
            minted.add(d)
            _mint_bound_demand(fact_g, rule_g, d)
        if not provenance:
            return
        node = chain_nodes.get(d)
        if node is None:
            node = chain_nodes[d] = _intern_subgoal(fact_g, d)
        if parent is not None and parent != d and (parent, d) not in chain_edges:
            pn = chain_nodes.get(parent)
            if pn is not None:
                chain_edges.add((parent, d))
                if not _raised_edge_exists(fact_g, pn, node):       # interned: dedupe across queries too
                    fact_g.add_relation(pn, RAISED, node, inert=True)   # provenance-style: inert edge

    def _observe(g, ns, phase, found=None, band=None):     # OBSERVER only (§ on_subgoal); never mutates
        if on_subgoal is None:
            return
        on_subgoal({"pred": g[0],
                    "subj": _endpoint_name(fact_g, g[1]),
                    "obj": _endpoint_name(fact_g, g[2]),
                    "depth": len(ns), "phase": phase, "found": found,
                    "band": band})                         # banded resolve: the BEST band the goal was
                                                           # found at (None crisp / enter / not found)

    def start(g, ns, parent=None):
        _observe(g, ns, "enter")
        cm = ControlMachine()
        program, fr = _frame_program(fact_g, rule_g, g, neg_stack=ns, provenance=provenance,
                                     scope=scope, focus_scope=focus_scope, fuel=_fuel,
                                     max_rounds=max_rounds, closed=_closed, visible=visible,
                                     policy=policy, parent=parent)
        return cm, fr, cm.run(fact_g, program), g, ns

    # THE CONTROL STACK: DFS over suspended frame machines. A resumed parent reads the child's result
    # from the SHARED graph (like `CALL`/`RET` where callee graph writes persist), never a return value.
    # Only the ROOT frame's `total` is returned (nested closures count toward their own frame — the old
    # nested `chain_sip` return was discarded).
    stack = [start(goal, _neg_stack)]
    root_total = 0
    while stack:
        cm, fr, res, g, ns = stack[-1]
        if isinstance(res, Continuation):                  # SUSPENDed on a NAC subgoal request
            _kind, neg_goal, child_neg_stack, parent = res.request   # ("subgoal", goal, ns|{goal}, parent)
            stack.append(start(neg_goal, child_neg_stack, parent))   # push the child closure; parent waits
        else:                                              # HALT — this frame's closure is complete
            stack.pop()
            if policy is not None and policy.banded:       # did the closure derive/find the goal —
                rows = _facts_matching(fact_g, g[0], g[1], g[2], scope=scope,   # and how POSSIBLY?
                                       focus_scope=focus_scope, bands=True)
                _observe(g, ns, "resolve", found=bool(rows),
                         band=max((b for _s, _o, b, _e in rows), default=None) if rows else None)
            else:
                _observe(g, ns, "resolve",
                         found=bool(_facts_matching(fact_g, g[0], g[1], g[2], scope=scope,
                                                    focus_scope=focus_scope)))
            if not stack:
                root_total = fr.total
            else:
                pcm, pfr, pres, pg, pns = stack[-1]        # continue the parent mid-round, exactly
                stack[-1] = (pcm, pfr, pcm.resume(fact_g, pres), pg, pns)   # where its SUSPEND paused it
    return root_total


def query_goal(fact_g: AttrGraph, goal: tuple[str, str | None, str | None], *,
               rules=None, commit: bool = False,
               focus_scope: frozenset[str] | None = None,
               max_rounds: int = 1000, policy=None) -> list[tuple]:
    """Answer a BOUND-TUPLE goal and return the MATCHING FACTS — the low-fixed-overhead sibling of
    `ask_goal` (feedback #13): no CNL question parse or answer render (the ~half of `ask_goal`'s
    per-call floor the question-string layer cost), READ-ONLY by default, and the answers come back
    as data instead of rendered strings. The hot inner loop of a consumer that runs MANY small
    checks (a per-composition soundness rule, a per-hypothesis probe) belongs here; `ask_goal`
    stays the CNL conversation surface.

    `goal` is `(pred, subj|None, obj|None)` — a `None` slot is the queried variable (`chain_sip`'s
    grain); an endpoint may be a name or a `ById` pin (id-addressed, collision-free). `rules` is a
    rule bank as a `list[Rule]` (reified fresh per call, exactly `ask_goal`'s discipline — no
    demand-trace accretion across queries) or an already-reified `AttrGraph` (reify once and reuse,
    the caller's choice); `None` reasons over `fact_g` itself (the one-graph fold).

    Returns the goal-matching facts as `(subj, pred, obj)` triples: a bound endpoint echoes the
    goal's; a free slot comes back as a `ById` pin naming the witness NODE (render it with
    `fact_g.name(pin.node_id)`). Both-endpoints-bound is the yes/no shape: `[]` means not derivable
    (plain absence — for the OWA/CWA verdict distinction use `check`, which this does not replace).

    `commit=False` (the default) runs the derivation in an ephemeral PENCIL scope and sweeps it —
    the graph is untouched, mirroring `ask_goal(commit=False)`/`suppose(commit=False)`; the #12
    boundary applies here too (a skolem-minting rule still mints its witness entity node — only
    derived RELATIONS are pencil). `commit=True` materializes the derivations (monotone, §5).

    `policy` (the possibilistic fold): under a BANDED policy the closure reasons marker-mode and
    the answers grow a fourth element — `(subj, pred, obj, band)`, band = the fact's BEST
    possibility (CERTAIN for ink). Opt-in: the shape only changes for a caller that passed a banded
    policy. Note the read-only sweep covers the `<query>` pencils; a banded run's DERIVED FORKS
    persist (monotone + idempotent — the known slice edge)."""
    rule_g = rules
    if rules is not None and not isinstance(rules, AttrGraph):
        from .cnl.rule_graph import write_rule
        rule_g = AttrGraph()
        for r in rules:
            write_rule(rule_g, r)
    banded = policy is not None and policy.banded
    scope = fact_g.add_node("<query>", control=True) if not commit else None
    try:
        chain_sip(fact_g, goal, rules=rule_g, scope=scope,
                  focus_scope=focus_scope, max_rounds=max_rounds, policy=policy)
        if banded:
            return [(s, goal[0], o, band) for s, o, band, _e in
                    _facts_matching(fact_g, goal[0], goal[1], goal[2],
                                    scope=scope, focus_scope=focus_scope, bands=True)]
        return [(s, goal[0], o) for s, o in
                _facts_matching(fact_g, goal[0], goal[1], goal[2],
                                scope=scope, focus_scope=focus_scope)]
    finally:
        if scope is not None:
            from .suppose import _drop_scope
            _drop_scope(fact_g, scope)


def render_demands(rule_g: AttrGraph) -> list[str]:
    """Render the bound-tuple magic set (the visible `<demand>` nodes) as CNL 'what I looked for'
    lines — the demand half of the trace renderer (Phase 4.4). A wildcard endpoint reads as `anyone`.
    Deterministic order. (CHECK's 'where I looked' negative trace extends this in Phase 5.)"""
    def key(d):
        return (d[0], d[1] or "", d[2] or "")
    lines: list[str] = []
    for pred, subj, obj in sorted(bound_demands(rule_g), key=key):
        lines.append(f"{subj or 'anyone'} {pred} {obj or 'anyone'}")
    return lines

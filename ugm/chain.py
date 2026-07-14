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
from .attrgraph import valued, GRADED, VALUED
from .apply import (
    _read_atoms, _fact_relnodes, _endpoints, _fact_exists, _find_fact_relnode, _record,
    _rel_in_scope, build_head_index, rules_producing, SCOPE,
)
from .machine import Machine, SEED, FOLLOW, SET
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
#     not stepping.) The visible `<demand>` node is that subgoal record; a later refinement links parent
#     -> child demands with in-graph POINTERS to carry the chain STRUCTURE, not just the flat set.


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


# --- ISA VALUE OPERANDS (docs/isa_value_operands_design.md §7 step 2) ------------------------------
#
# The uniform POINTER model for demand-solver bindings: a register/env slot holds only a node-pointer;
# a NAME endpoint (`"ada"`) is carried as a pointer to its INTERNED value-node (a regular node carrying
# `<isa_operand_value>="ada"`, `AttrGraph.value_node`), and the operations that consume an endpoint
# INTERPRET the pointer — a value-node means "the entities named ada" (resolved exactly as the name was:
# `nodes_named`, max-over-mentions, write-by-name), any other node pins (`ById` semantics). Coref-class
# aggregation is untouched — it happens INSIDE the consuming operation, which is what dissolves the
# fork-vs-aggregate crux (§3). Behaviour-identical by construction; differential-gated (the reasoning
# suite + `_CROSSCHECK` run green with the flag on before any swap).

_VALUE_OPERANDS = False   # §7.2 gate: default OFF (the shipped name path). Tests flip it on; the
# production swap is the user's ratified gate, exactly as A1's `_CROSSCHECK` precedent.


def _operand(fact_g: AttrGraph, endpoint):
    """The endpoint as CARRIED by the demand solver: under `_VALUE_OPERANDS` a bare NAME becomes the
    pointer to its interned value-node; a wildcard (None) and an already-pointing `ById` pass through.
    Flag off = identity (the name path, unperturbed)."""
    if _VALUE_OPERANDS and isinstance(endpoint, str):
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
            if other != n and not fact_g.is_control(other) and not fact_g.is_inert(other):
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
# `_resolve_head`); the per-env body bindings stay a Python env.


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


def _tok_name(env: dict[str, str], tok: str):
    """The ENDPOINT a rule token resolves to under `env` — a NAME or, since the id-addressed core
    (Stage 3), a `ById`: a bound var -> its env value (a name it was seeded with, or a `ById` a free
    slot bound it to — see `_facts_matching`); a literal -> its name; an UNBOUND var -> None (a wildcard
    demand endpoint, an open slot to be bound by a fact). Consumers (`_facts_matching`, `_node_for_name`,
    `_bound_entity_nodes`) are `ById`-aware, so a var can carry a node id through the whole chain."""
    return env.get(tok) if is_var(tok) else literal_name(tok)


def _endpoint_name(fact_g: AttrGraph, endpoint) -> str:
    """The NAME an endpoint denotes: a `ById` -> its node's name (a value-node pointer -> its VALUE);
    a name -> itself. Used where a rule LITERAL (matched by name) meets a `ById` env/demand endpoint
    (matched by id)."""
    if isinstance(endpoint, ById):
        v = _operand_value_of(fact_g, endpoint)
        return v if v is not None else fact_g.name(endpoint.node_id)
    return endpoint


def _bind(fact_g: AttrGraph, env: dict[str, str], tok: str, val) -> dict[str, str] | None:
    """Extend `env` binding `tok` to `val` (a name or a `ById`): a var binds (or must already agree by
    equality — a `ById` is agreement-safe: a distinct same-named node has a DIFFERENT id and correctly
    fails to unify, and a value-node pointer is INTERNED so the same value is the same pointer), a
    literal must equal `val` BY NAME (under `_VALUE_OPERANDS` a literal meets its own echoed value-node
    pointer, unwrapped by `_endpoint_name`; a free slot, which alone yields an entity `ById`, is by
    construction a var, never a literal). Returns the extended env, or None on conflict."""
    if is_var(tok):
        if tok in env:
            return env if env[tok] == val else None
        e = dict(env)
        e[tok] = val
        return e
    return env if literal_name(tok) == _endpoint_name(fact_g, val) else None


def _unify_head_with_demand(fact_g: AttrGraph, demand: tuple[str, str | None, str | None],
                            hs: str, hp: str, ho: str) -> dict[str, str] | None:
    """The env binding a head atom `(hs, hp, ho)` inherits from a demand it can serve: the predicates
    must match, and the demand's bound endpoints seed the head's slots (a wildcard demand endpoint
    leaves the head slot open). None if the head can't produce the demanded tuple. A demand endpoint may
    be a `ById` (an id-addressed goal, or a sub-demand raised from a free var the body bound to a node);
    a head VAR takes it verbatim (id-addressed seed), a head LITERAL is matched against the id's NAME."""
    pred, dsubj, dobj = demand
    if hp != pred:
        return None
    env: dict[str, str] = {}
    for slot, ep in ((hs, dsubj), (ho, dobj)):
        if ep is None:
            continue
        nxt = _bind(fact_g, env, slot, ep if is_var(slot) else _endpoint_name(fact_g, ep))
        if nxt is None:
            return None
        env = nxt
    return env


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

    FOCUS-SCOPE (Phase 8.3b, docs/cnl_intake_design.md §3) — BOUNDED ATTENTION, opt-in and caller-selected
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


# --- A1: the demand lookup on the SHARED ISA matcher (docs/phase_a_demand_firmware.md) -------------
#
# The bespoke `_facts_matching_walk` above is a SECOND matcher (a hand-written topology walk). A1's
# thesis: that walk IS the ISA matcher's walk — SET the bound endpoint node, FOLLOW to the rel, TEST
# the predicate key, FOLLOW to the other endpoint. `_facts_matching_isa` does exactly that through the
# ONE `Machine.match`, so forward and demand unify on one matcher (the precondition for a single Rust
# interpreter, Phase B). The three demand-specific VISIBILITY filters that are NOT ISA-structural stay
# as post-filters — the irreducible demand policy A5 isolates (fork (b), see the doc §2): fact-layer
# endpoint/rel visibility (skip control/inert scaffolding), SUPPOSE scope-pencil visibility
# (`_rel_matches_pred`), and focus attention (`keep`). A free slot wraps to `ById(node)` — native
# here, since the matcher's register already holds the specific node id.

_ISA_READER = Machine()   # skip_inert OFF: the post-filters below skip inert AND control, exactly the
# walk (so the ISA path and the walk see the identical candidate set — provable parity, not near-parity)

_CROSSCHECK = False   # A1 differential gate: when True, every `_facts_matching` asserts the ISA path
# agrees with the bespoke walk on that call (order-insensitive). The reference oracle (the walk) is
# retained; the production SWAP to the ISA path is the user's ratified gate (doc §4). Tests flip it on.


def _facts_matching_isa(fact_g: AttrGraph, pred: str,
                        subj_name: str | None, obj_name: str | None,
                        *, scope: str | None = None,
                        focus_scope: frozenset[str] | None = None) -> list[tuple[str, str]]:
    """The single-atom demand fact lookup with the TOPOLOGY WALK done by the shared ISA matcher (A1).
    Behaviour-identical to `_facts_matching_walk` (differentially gated by `_CROSSCHECK`); see the
    module note above and `docs/phase_a_demand_firmware.md`."""
    out: list[tuple[str, str]] = []

    def keep(s: str, o: str) -> bool:
        return focus_scope is None or s in focus_scope or o in focus_scope

    if subj_name is not None:                              # (pred, subj, ?) — walk OUT of the subject
        subj_key = _scope_key(fact_g, subj_name)
        prog = [SET("s", ""), FOLLOW("r", "s", "out"), FOLLOW("o", "r", "out")]
        for s in _candidate_nodes(fact_g, subj_name):
            if fact_g.is_control(s) or fact_g.is_inert(s):
                continue
            prog[0] = SET("s", s)
            for st in _ISA_READER.match(fact_g, prog):
                rel, o = st.regs["r"], st.regs["o"]
                if not _rel_matches_pred(fact_g, rel, pred, scope):
                    continue
                if fact_g.is_control(o) or fact_g.is_inert(o):
                    continue
                if obj_name is not None and not _endpoint_matches(fact_g, o, obj_name):
                    continue
                if keep(subj_key, fact_g.name(o)):
                    out.append((subj_name, obj_name if obj_name is not None else ById(o)))
        return out
    if obj_name is not None:                               # (pred, ?, obj) — walk INTO the object
        obj_key = _scope_key(fact_g, obj_name)
        prog = [SET("o", ""), FOLLOW("r", "o", "in"), FOLLOW("s", "r", "in")]
        for o in _candidate_nodes(fact_g, obj_name):
            if fact_g.is_control(o) or fact_g.is_inert(o):
                continue
            prog[0] = SET("o", o)
            for st in _ISA_READER.match(fact_g, prog):
                rel, s = st.regs["r"], st.regs["s"]
                if not _rel_matches_pred(fact_g, rel, pred, scope):
                    continue
                if fact_g.is_control(s) or fact_g.is_inert(s):
                    continue
                if keep(fact_g.name(s), obj_key):
                    out.append((ById(s), obj_name))
        return out
    for st in _ISA_READER.match(fact_g, [SEED("r", pred, cmp=None)]):   # (pred, ?, ?) — predicate scan
        rel = st.regs["r"]
        if not _rel_matches_pred(fact_g, rel, pred, scope):
            continue
        for s, o in _endpoints(fact_g, rel):
            sn, on = fact_g.name(s), fact_g.name(o)
            if keep(sn, on):
                out.append((ById(s), ById(o)))
    return out


def _facts_matching(fact_g: AttrGraph, pred: str,
                    subj_name: str | None, obj_name: str | None,
                    *, scope: str | None = None,
                    focus_scope: frozenset[str] | None = None) -> list[tuple[str, str]]:
    """The single-atom demand fact lookup (SIP). Currently the bespoke topology walk
    (`_facts_matching_walk`, the reference oracle); when `_CROSSCHECK` is set it asserts the shared
    ISA-matcher path (`_facts_matching_isa`, A1 — `docs/phase_a_demand_firmware.md`) agrees on every
    call, the differential gate for retiring the second matcher (the swap is the user's ratified gate)."""
    out = _facts_matching_walk(fact_g, pred, subj_name, obj_name, scope=scope, focus_scope=focus_scope)
    if _CROSSCHECK:
        isa = _facts_matching_isa(fact_g, pred, subj_name, obj_name, scope=scope, focus_scope=focus_scope)
        if Counter(out) != Counter(isa):
            raise AssertionError(
                f"A1 demand-matcher divergence for ({pred!r},{subj_name!r},{obj_name!r}) "
                f"scope={scope!r} focus_scope={focus_scope!r}:\n  walk={out!r}\n  isa ={isa!r}")
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


def _graded_ok(fact_g: AttrGraph, graded: list[tuple[str, str, float]], env: dict[str, str]) -> bool:
    """True iff every graded condition passes under `env` — the α-cut DURING matching (the CHAIN analog
    of the forward `GRADE` op): the bound var's node must carry the dimension as a GRADED membership
    `>= threshold` (and `> 0`). Node-agnostic (any coreferent mention may carry the propagated degree).
    An unbound graded var is out of slice -> fail (never fire on an unevaluable α-cut). The bound value
    may be a name OR (id-addressed core, Stage 3) a `ById`, so resolve it through `_bound_entity_nodes`
    (id -> its node; name -> the same-named entities — any coreferent mention may carry the degree)."""
    for var, dim, thr in graded:
        bound = env.get(var)
        if bound is None:
            return False
        deg = max((float(a.value) for n in _bound_entity_nodes(fact_g, bound)
                   if (a := fact_g.get_attr(n, dim)) is not None and a.kind == GRADED), default=0.0)
        if not (deg >= thr and deg > 0.0):
            return False
    return True


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


def _value_matches_ok(fact_g: AttrGraph, vms: list[tuple[str, str, str, float | None]],
                      env: dict[str, str]) -> bool:
    """True iff every value-match passes under `env` — the DECLARED value-JOIN applied DURING matching
    (`ValueMatch`). Both vars must be bound; then, on `dim`:
      * EXACT (threshold None): the two bound nodes carry EQUAL VALUED values (e.g. the same `name`).
      * GRADED ('close enough'): both carry a GRADED degree on `dim` and `1 - |deg_a - deg_b| >= threshold`.
    An unbound var, or a missing value on either side, fails (never fire on an unevaluable join)."""
    def valued_of(bound, dim):
        for n in _bound_entity_nodes(fact_g, bound):
            a = fact_g.get_attr(n, dim)
            if a is not None and a.kind == VALUED:
                return a.value
        return None

    def graded_of(bound, dim):
        return max((float(a.value) for n in _bound_entity_nodes(fact_g, bound)
                    if (a := fact_g.get_attr(n, dim)) is not None and a.kind == GRADED), default=None)

    for va, vb, dim, thr in vms:
        ba, bb = env.get(va), env.get(vb)
        if ba is None or bb is None:
            return False
        if thr is None:                                   # exact VALUED equality
            xa, xb = valued_of(ba, dim), valued_of(bb, dim)
            if xa is None or xb is None or xa != xb:
                return False
        else:                                             # graded 'close enough'
            da, db = graded_of(ba, dim), graded_of(bb, dim)
            if da is None or db is None or (1.0 - abs(da - db)) < thr:
                return False
    return True


def _nac_blocks(fact_g: AttrGraph, rule_g: AttrGraph, nac_atoms: list[tuple[str, str, str]],
                env: dict[str, str], *, scope: str | None, provenance: bool,
                focus_scope: frozenset[str] | None = None,
                neg_stack: frozenset[tuple[str, str | None, str | None]],
                fuel: "_Exhaustion | None", max_rounds: int, closed: set) -> bool:
    """Decide the rule's NAC clauses under `env` by DEMAND-DRIVEN NEGATION-AS-FAILURE (firmware v3):
    return True iff some `not L(bound)` clause's POSITIVE holds — i.e. the rule must NOT fire for this
    env. Each NAC `L` is a NESTED NEGATIVE DEMAND: bind it by `env`, demand the positive `L` and run
    it to CLOSURE (a self-contained nested `chain_sip`, so "the positive failed" is read from L's
    COMPLETE extension — the goal-directed analog of stratifying L's producers BELOW this consumer),
    then read ABSENCE. Any matching L-fact -> the NAC fails -> block; none -> `not L` holds. NOTHING is
    materialized for the negative (monotone, §5-safe): the verdict is computed from the (empty) demand-
    closure — the SAME move CHECK makes at top level, pushed inside the rule body.

    STRATIFICATION (see the module note): the negative goal is pushed on `neg_stack` before its positive
    closure. A re-entry (`neg_goal in neg_stack`) is a HIGHER-stratum rule reached via a demand-path
    artifact — on a stratifiable bank (guaranteed by the load-time lint) it cannot legitimately fire in
    this lower stratum, so the chain PRUNES it: block this env and DO NOT recurse (returning "blocked"
    for the re-entered rule, continuing the outer closure). A wildcard endpoint (a NAC var the positive
    body left unbound) is an EXISTENTIAL NAC — `not L(x, ·)` holds iff NO `L(x, anything)` exists, which
    the wildcard `_facts_matching` reads directly.

    GENERATOR (brick #3, docs/isa_control_machine.md §9.3): this is now a GENERATOR — instead of RECURSING
    into `chain_sip` to close a negative's positive, it YIELDS a subgoal request `("subgoal", neg_goal,
    child_neg_stack)` and the driver (`chain_sip`) closes it on an EXPLICIT control stack, then resumes
    here. The yield IS the `CALL`; the driver's stack IS the control stack — the subgoal descent lives in
    the machine's stack, not Python's. Operation order is unchanged (the driver services each yield
    synchronously before resuming), so the demand-driven NAF semantics are identical. Returns the block
    verdict via the generator's return value (`yield from` surfaces it)."""
    for ns, np, no in nac_atoms:
        neg_goal = (np, _operand(fact_g, _tok_name(env, ns)), _operand(fact_g, _tok_name(env, no)))
        if neg_goal in neg_stack:
            return True                        # re-entry: prune the higher-stratum rule (block env)
        if neg_goal not in closed:             # MEMO: a negative's positive is closed ONCE per session.
            yield ("subgoal", neg_goal, neg_stack | {neg_goal})   # driver closes the positive, then resumes
            closed.add(neg_goal)               # facts are monotone + stratified -> the closure is stable,
        # so re-demands (the round loop re-services this env each round) just READ absence, never re-close.
        if _facts_matching(fact_g, np, neg_goal[1], neg_goal[2], scope=scope, focus_scope=focus_scope):
            return True                                    # L holds -> the NAC fails -> block this env
        if fuel is not None and fuel.exhausted:
            return True             # the positive is not EXHAUSTED -> the NAC is UNDECIDED; do not fire
    return False                                           # (the `fuel.exhausted` flag makes it UNKNOWN)


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


def _anchor_node(fact_g: AttrGraph, env: dict[str, str], tok: str) -> str | None:
    """The already-bound fact-layer node a NON-skolem head endpoint denotes under `env` (an LHS-bound var
    or a plain literal) — the ARGUMENT a skolem is a function OF. None if the token is unbound. Never mints
    (a witness search must not create the very node it is looking for)."""
    name = _tok_name(env, tok)
    if name is None:
        return None
    nodes = _bound_entity_nodes(fact_g, name)
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
                     env: dict[str, str], skolems: set[str]) -> dict[str, str]:
    """Bind each head skolem to ONE node id for this firing (shared across all its head atoms, like the
    forward path's per-firing `reg_of`): reuse the structural witness of its defining relations, or MINT a
    fresh node when none exists yet (round 1). Keyed on the LHS-bound anchors, so the SAME firing re-served
    next round re-finds the SAME node — the fix for the demand-path skolem blowup (feedback #2)."""
    out: dict[str, str] = {}
    for sk in skolems:
        constraints: list[tuple[str, str, bool]] = []
        for hs, hp, ho in heads:
            if hs == sk and ho != sk and (a := _anchor_node(fact_g, env, ho)) is not None:
                constraints.append((hp, a, True))
            elif ho == sk and hs != sk and (a := _anchor_node(fact_g, env, hs)) is not None:
                constraints.append((hp, a, False))
        node = _find_skolem_witness(fact_g, literal_name(sk), constraints) if constraints else None
        out[sk] = node if node is not None else fact_g.add_node(literal_name(sk))
    return out


def _head_endpoint_id(fact_g: AttrGraph, env: dict[str, str], tok: str,
                      sk_ids: dict[str, str]) -> str | None:
    """The node id a head endpoint EMITs to: this firing's skolem node if `tok` is a skolem, else the
    bound var / literal resolved to its write node (`_node_for_name`). None for an unbound non-skolem slot."""
    if tok in sk_ids:
        return sk_ids[tok]
    name = _tok_name(env, tok)
    return None if name is None else _node_for_name(fact_g, name)


def _solve_demand_rule(fact_g: AttrGraph, rule_g: AttrGraph, rule_node: str,
                       demand: tuple[str, str | None, str | None], mint,
                       *, provenance: bool = False, scope: str | None = None,
                       focus_scope: frozenset[str] | None = None,
                       neg_stack: frozenset[tuple[str, str | None, str | None]] = frozenset(),
                       fuel: "_Exhaustion | None" = None, max_rounds: int = 1000,
                       closed: set = frozenset()) -> int:
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
    reads its return value)."""
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
    rule_key = rule_g.name(rule_node) if provenance else ""

    seeds: list[dict[str, str]] = []
    for hs, hp, ho in heads:
        env0 = _unify_head_with_demand(fact_g, demand, hs, hp, ho)
        if env0 is not None and env0 not in seeds:
            seeds.append(env0)

    fired = 0
    for env0 in seeds:
        envs = [env0]
        for s_tok, bp, o_tok in _sideways_order(body, set(env0)):   # SIP: each atom demanded under env
            nxt: list[dict[str, str]] = []
            for env in envs:
                # the endpoints as CARRIED (§7.2): a literal's name becomes its value-node pointer
                # under `_VALUE_OPERANDS` (a bound var already holds a pointer); flag off = the names
                s_ep = _operand(fact_g, _tok_name(env, s_tok))
                o_ep = _operand(fact_g, _tok_name(env, o_tok))
                mint((bp, s_ep, o_ep))
                for fs, fo in _facts_matching(fact_g, bp, s_ep, o_ep, scope=scope,
                                              focus_scope=focus_scope):
                    e1 = _bind(fact_g, env, s_tok, fs)
                    if e1 is None:
                        continue
                    e2 = _bind(fact_g, e1, o_tok, fo)
                    if e2 is not None:
                        nxt.append(e2)
            envs = nxt
        for env in envs:                                   # EMIT every head atom per full match
            if graded and not _graded_ok(fact_g, graded, env):             # α-cut DURING matching
                continue
            if value_matches and not _value_matches_ok(fact_g, value_matches, env):   # declared value-JOIN
                continue
            if nac and (yield from _nac_blocks(fact_g, rule_g, nac, env, scope=scope,   # NAF: absence
                                               focus_scope=focus_scope,                 # decides — the
                                               provenance=provenance, neg_stack=neg_stack,  # subgoal is
                                               fuel=fuel, max_rounds=max_rounds, closed=closed)):  # a yield
                continue
            sk_ids = _resolve_skolems(fact_g, heads, env, skolems) if skolems else {}
            for hs, hp, ho in heads:
                s_id = _head_endpoint_id(fact_g, env, hs, sk_ids)
                o_id = _head_endpoint_id(fact_g, env, ho, sk_ids)
                if s_id is None or o_id is None:           # unbound non-skolem head slot — out of slice
                    continue
                if not _fact_exists(fact_g, s_id, hp, o_id, scope=scope):
                    # EMIT: an ink fact normally, but PENCIL (control + scope tag) inside a SUPPOSE scope
                    head_node = fact_g.add_relation(s_id, hp, o_id, control=(scope is not None))
                    if scope is not None:
                        fact_g.set_attr(head_node, SCOPE, valued(scope))
                    fired += 1
                    if provenance:                         # RECORD (mode 9): journal the firing
                        _record(fact_g, rule_key, head_node,
                                [_find_fact_relnode(fact_g, _node_for_name(fact_g, _tok_name(env, bs)),
                                                    bp2, _node_for_name(fact_g, _tok_name(env, bo)),
                                                    scope=scope)
                                 for bs, bp2, bo in body])
    return fired


def _close_goal(fact_g: AttrGraph, rule_g: AttrGraph,
                goal: tuple[str, str | None, str | None], *, neg_stack, provenance, scope,
                focus_scope, fuel, max_rounds, closed, visible):
    """Close ONE goal's positive to fixpoint — the per-goal round-loop, as a GENERATOR (brick #3). It
    serves every standing demand with the rules that produce it (raising bound sub-demands and EMITting)
    until no new fact and no new demand. When a rule's NAC needs a negative subgoal closed, the delegated
    `_solve_demand_rule`/`_nac_blocks` YIELD a `("subgoal", neg_goal, child_neg_stack)` request up to the
    driver (`chain_sip`), which pushes a child `_close_goal` on the explicit control stack and resumes
    this frame once it completes — so the subgoal descent is the machine's stack, not Python recursion.
    Returns #facts EMITted in THIS goal's closure (nested-negative derivations count toward their OWN
    frame, exactly as the old nested `chain_sip` return was discarded). `visible(d, neg_stack)` mints the
    top-level magic-set trace (only when `neg_stack` is empty)."""
    visible(goal, neg_stack)
    agenda: set[tuple[str, str | None, str | None]] = {goal}   # this frame's own demand sub-tree
    total = 0
    converged = False
    for _ in range(max_rounds):
        newly: set[tuple[str, str | None, str | None]] = set()

        def mint(d, _agenda=agenda, _new=newly, _ns=neg_stack):
            if d not in _agenda and d not in _new:
                _new.add(d)
                visible(d, _ns)                            # visible magic-set node (trace), minted once

        fired = 0
        for demand in agenda:
            for rn in rules_producing(rule_g, demand[0]):
                fired += (yield from _solve_demand_rule(
                    fact_g, rule_g, rn, demand, mint,
                    provenance=provenance, scope=scope, focus_scope=focus_scope,
                    neg_stack=neg_stack, fuel=fuel, max_rounds=max_rounds, closed=closed))
        agenda |= newly
        total += fired
        if fired == 0 and not newly:                       # no new fact AND no new demand -> fixpoint
            converged = True
            break
    if not converged and fuel is not None:                 # hit the round budget short of fixpoint ->
        fuel.exhausted = True                              # the closure is not EXHAUSTED (fuel->UNKNOWN)
    return total


def chain_sip(fact_g: AttrGraph, rule_g: AttrGraph,
              goal: tuple[str, str | None, str | None], *, max_rounds: int = 1000,
              provenance: bool = False, scope: str | None = None,
              focus_scope: frozenset[str] | None = None,
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

    CONTROL-MACHINE PORT (brick #3, docs/isa_control_machine.md §9.3). `chain_sip` is now a DRIVER over
    an EXPLICIT CONTROL STACK of `_close_goal` frames — the WAM environment stack — replacing the Python
    recursion the NAC negative subgoal used (`_nac_blocks` used to CALL `chain_sip`). Each frame closes
    one goal; when its NAC needs a negative closed it YIELDS a subgoal request, the driver pushes a child
    frame for it (with `neg_stack | {neg_goal}`, so the stratification stack IS the control stack), runs
    the child to completion (mutating the SHARED, monotone graph), then resumes the parent — the same DFS
    order as the old recursion, so behaviour is identical (the reasoning suite is the differential oracle).
    The subgoal descent now lives in the machine's stack, not Python's — the seam-crossing §9.3 promises.

    The agenda stays LOCAL to each frame (seeded from its goal, grown only by the sub-demands its own
    rules raise), and the visible `<demand>` trace is minted ONLY for the top-level goal (`neg_stack`
    empty). A nested negative frame needs no trace and mints none. Self-containment (a NAC closes ONLY its
    negated positive `L`, never re-entering the consumer whose NAC is being decided) is preserved: each
    frame is a distinct goal-closure on the stack; the `_closed`/`neg_stack` memo + prune keep NAF's
    'the positive failed' read from L's COMPLETE extension."""
    validate_ids(fact_g, goal[1], goal[2])                 # id-addressed pins must exist (silent->loud)
    # §7.2 (value operands): the goal's NAME endpoints become value-node POINTERS at this boundary, so
    # everything the solver carries downstream (env seeds, sub-demands, NAC goals) is a node-pointer.
    goal = (goal[0], _operand(fact_g, goal[1]), _operand(fact_g, goal[2]))
    build_head_index(rule_g)                               # idempotent
    if _closed is None:
        _closed = set()                                    # NAC-closure MEMO, shared across all frames
    # The VISIBLE `<demand>` trace is minted lazily and ONLY at the top level (`neg_stack` empty), deduped
    # by ONE set shared across frames (only the root frame ever mints — nested frames pass a non-empty
    # neg_stack, so `visible` no-ops). A nested negative closure needs no trace and never re-scans the graph.
    minted: set[tuple[str, str | None, str | None]] = set()

    def visible(d, ns):
        if not ns and d not in minted:                     # top-level magic set only (trace)
            minted.add(d)
            _mint_bound_demand(fact_g, rule_g, d)

    def frame(g, ns):
        return _close_goal(fact_g, rule_g, g, neg_stack=ns, provenance=provenance, scope=scope,
                           focus_scope=focus_scope, fuel=_fuel, max_rounds=max_rounds,
                           closed=_closed, visible=visible)

    # THE CONTROL STACK: DFS over goal-closure frames. `send` is always None — a resumed parent reads the
    # child's result from the SHARED graph (like `CALL`/`RET` where callee graph writes persist), not a
    # return value. Only the ROOT frame's `total` is returned (nested closures count toward their own
    # frame — the old nested `chain_sip` return was discarded).
    stack = [frame(goal, _neg_stack)]
    root_total = 0
    while stack:
        try:
            req = stack[-1].send(None)                     # advance the deepest frame to its next subgoal
        except StopIteration as e:                         # ... or to completion
            stack.pop()
            if not stack:
                root_total = e.value if e.value is not None else 0
            continue
        _kind, neg_goal, child_neg_stack = req             # ("subgoal", neg_goal, neg_stack|{neg_goal})
        stack.append(frame(neg_goal, child_neg_stack))     # push the child closure (the control stack)
    return root_total


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

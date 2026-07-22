"""
Shared REIFIED-RULE readers + the head index (what remains of firmware v0 APPLY).

The frame-based forward matcher that lived here (`apply_rule`/`apply_to_fixpoint` — visible
`<frame>` bindings, the `<current-atom>` cursor itinerary, the semi-naive delta driver) was
DELETED 2026-07-16: it was the Phase-4.2 reference implementation, superseded on the forward
side by `lowering.run_bank` (the lowered-program engine) and on the demand side by
`chain.chain_sip` (the SIP closure over these same readers). Nothing in the engine called it —
only its own differential tests did (deleted with it; delete-old-code rule). Forward-over-
reified-rules, if the homoiconicity frontier ever needs it again, is a rebuild over these
readers, not a resurrection.

What remains, and who uses it:
  - `rule_nodes` / `build_head_index` / `rules_producing` — the in-graph HEAD INDEX (Phase 3.3)
    the demand engine consults per goal predicate;
  - `_read_atoms` — the reified rule's body/head/nac atoms, read from `write_rule`'s shape;
  - `_fact_relnodes` / `_endpoints` / `_fact_exists` / `_find_fact_relnode` / `_rel_in_scope` —
    the scope-aware fact readers (SUPPOSE pencil visibility rides on `SCOPE`);
  - `_record` — RECORD (mode 9), delegating to the ONE justification-minting program
    (`provenance.record_firing`).
"""
from __future__ import annotations

from .attrgraph import AttrGraph, valued, graded, NAME, PATTERN_MARK
from .production_rule import is_var, is_bound_literal, literal_name

HEAD_INDEX = "<head-index>"
# A rule whose HEAD predicate is a VARIABLE (`?s ?p ?o`, facts-as-truth-bearers dereify) can produce
# ANY predicate, so it is catalogued under this wildcard key and `rules_producing` returns it for every
# concrete demand (the demand-path analog of the forward "variable predicate resolved at apply time").
HEAD_VAR_PRED = "<var-pred-head>"
ROLES = ("lhs", "rhs", "nac", "drop")

# Phase 5.3 (SUPPOSE): a VALUED tag on a pencil / scope-derived rel node naming the `<hypothesis>` scope
# it belongs to. A pencil fact is a CONTROL rel node (so it is invisible to ordinary fact matching and
# never touches ink) carrying `scope=<hypothesis-id>`; the scope-aware fact readers below make exactly
# that scope's pencil visible WITHIN it (`scope=` passed) and nothing extra when no scope is active.
SCOPE = "scope"

# Slice 2 part (b) — scope-variable rules (docs/design/scope_generalization.md §6). A rule ATOM may
# carry a RELATIVIZER token `@?t`: the atom is matched/written RELATIVIZED to the scope KEYED to `?t`
# (a temporal index), so a rule can bind and relate scopes (`has(x,y)@?t1 ∧ ?t1 before ?t2 ⇒
# has(x,y)@?t2`). Stored as a VALUED attr on the atom's reified predicate node (write_rule); read back
# by `_read_atoms_rel`. Absent ⇒ the ordinary un-relativized atom (ink / run-level scope), unchanged.
ATOM_REL = "<atom-rel>"


def rule_nodes(rule_g: AttrGraph) -> list[str]:
    """The reified rule nodes in `rule_g`: a rule node is the subject of any role relation
    (lhs/rhs/nac/drop) — the same identification `rule_graph.rules_in_graph` uses."""
    out: list[str] = []
    for nid in rule_g.nodes():
        if any(rule_g.predicate(rel) in ROLES for rel, _ in rule_g.relations_from(nid)):
            out.append(nid)
    return out


# --- Phase 3.3: the head index as graph structure ------------------------------------------------

def build_head_index(rule_g: AttrGraph) -> str:
    """Wire the HEAD INDEX (catalog-key → rule nodes) as graph structure: a `<head-index>` hub with,
    per rule, a relation `hub -[headPred]-> rule` for each of the rule's head (rhs) predicates. CHAIN
    (4.3) queries it — given a demanded goal predicate, which rules could produce it — through the
    substrate itself (`rules_producing`), no Python dict. Idempotent: an entry already present is not
    duplicated. Returns the hub id."""
    hubs = rule_g.nodes_named(HEAD_INDEX)
    hub = hubs[0] if hubs else rule_g.add_node(HEAD_INDEX, control=True)
    existing = {(rule_g.predicate(rel), obj) for rel, obj in rule_g.relations_from(hub)}
    for rn in rule_nodes(rule_g):
        for _hs, hp, _ho in _read_atoms(rule_g, rn, "rhs"):
            key = HEAD_VAR_PRED if is_var(hp) else hp   # a variable head predicate -> the wildcard bucket
            if (key, rn) not in existing:
                rel = rule_g.add_relation(hub, key, rn, control=True)   # hub -[headPred]-> rule
                rule_g.set_attr(rel, PATTERN_MARK, graded(1.0))   # rule wiring: out of the fact view
                existing.add((key, rn))
    return hub


def rules_producing(rule_g: AttrGraph, pred: str) -> list[str]:
    """The reified rule nodes whose head derives `pred`, read from the in-graph head index (built by
    `build_head_index`). Deduped, since a rule with two same-predicate head atoms indexes once here."""
    out: list[str] = []
    for hub in rule_g.nodes_named(HEAD_INDEX):
        for rel, obj in rule_g.relations_from(hub):
            # a concrete match, OR any variable-predicate-head rule (it can produce `pred`)
            if (rule_g.has_key(rel, pred) or rule_g.has_key(rel, HEAD_VAR_PRED)) and obj not in out:
                out.append(obj)
    return out


# --- reading the reified rule (Phase 3.1 shape) --------------------------------------------------

def _read_atoms(rule_g: AttrGraph, rule_node: str, role: str) -> list[tuple[str, str, str]]:
    """The `(s_tok, pred, o_tok)` atoms of `rule_node`'s `role` (e.g. "lhs"/"rhs"), read from the
    reified shape: `rule -[role]-> patom`, where `patom` is the pattern atom's predicate node with
    the subject slot as its (non-role) predecessor and the object slot as its successor."""
    atoms: list[tuple[str, str, str]] = []
    for role_rel, patom in rule_g.relations_from(rule_node):
        if not rule_g.has_key(role_rel, role):
            continue
        subj_slots = [n for n in rule_g.pred(patom) if n != role_rel]
        obj_slots = list(rule_g.succ(patom))
        atoms.append((rule_g.name(subj_slots[0]), rule_g.predicate(patom), rule_g.name(obj_slots[0])))
    return atoms


def _read_atoms_rel(rule_g: AttrGraph, rule_node: str, role: str) -> list[tuple[str, str, str, str]]:
    """`_read_atoms` plus each atom's RELATIVIZER token (`ATOM_REL` on the atom's predicate node), as
    `(s_tok, pred, o_tok, rel_tok)` — `rel_tok` is "" for an ordinary un-relativized atom. Same order
    as `_read_atoms`, so the two stay aligned. The demand chain uses this; the un-relativized callers
    keep `_read_atoms` (3-tuples) unchanged."""
    atoms: list[tuple[str, str, str, str]] = []
    for role_rel, patom in rule_g.relations_from(rule_node):
        if not rule_g.has_key(role_rel, role):
            continue
        subj_slots = [n for n in rule_g.pred(patom) if n != role_rel]
        obj_slots = list(rule_g.succ(patom))
        a = rule_g.get_attr(patom, ATOM_REL)
        atoms.append((rule_g.name(subj_slots[0]), rule_g.predicate(patom),
                      rule_g.name(obj_slots[0]), a.value if a is not None else ""))
    return atoms


# --- fact reading + EMIT -------------------------------------------------------------------------

def _rel_in_scope(g: AttrGraph, rel: str, scope: str) -> bool:
    """Does this control rel node belong to the active `<hypothesis>` `scope`? (its pencil tag matches)."""
    a = g.get_attr(rel, SCOPE)
    return a is not None and a.value == scope


def _fact_relnodes(g: AttrGraph, pred: str, *, scope: str | None = None):
    """The FACT relation nodes for predicate `pred`: keyed by `pred`, never inert. A CONTROL rel node
    is normally invisible (so a reified-rule/frame/provenance node can never be mistaken for a fact) —
    UNLESS `scope` is the active `<hypothesis>` scope and this control rel is that scope's pencil
    (SUPPOSE, Phase 5.3): then it is visible WITHIN the scope. `scope=None` (the default everywhere but
    in-scope reasoning) reproduces the original fact-only behavior exactly — behavior-neutral."""
    for rel in g.nodes_with_key(pred):
        if g.is_inert(rel):
            continue
        if g.is_control(rel):
            if scope is not None and _rel_in_scope(g, rel, scope):
                yield rel
            continue
        yield rel


def _endpoints(g: AttrGraph, rel: str):
    """The (subject, object) of a fact rel node, skipping control/inert endpoints."""
    subs = [s for s in g.pred(rel) if not (g.is_control(s) or g.is_inert(s))]
    objs = [o for o in g.succ(rel) if not (g.is_control(o) or g.is_inert(o))]
    for s in subs:
        for o in objs:
            yield s, o


def _fact_exists(g: AttrGraph, s: str, pred: str, o: str, *, scope: str | None = None) -> bool:
    """Check-before-derive: does the fact `s -[pred]-> o` already exist? (the memo table). Within a
    SUPPOSE scope, this scope's pencil counts as present too, so an in-scope re-derivation terminates."""
    return _find_fact_relnode(g, s, pred, o, scope=scope) is not None


def _find_fact_relnode(g: AttrGraph, s: str, pred: str, o: str, *, scope: str | None = None) -> str | None:
    """The fact rel node for `s -[pred]-> o` (the memo entry / the premise node RECORD `uses`); within a
    SUPPOSE scope, also the scope's matching pencil rel node.

    ENDPOINT-DRIVEN (Phase-7-adjacent perf, the same lever `chain._facts_matching` got). Both endpoints
    are BOUND node ids here (it is a specific-fact existence check), and `rel in g.succ(s)` is exactly
    `s in g.pred(rel)` — so reach the candidate rels THROUGH the subject's local topology (bounded by the
    subject's degree) instead of scanning every `pred` fact (`nodes_with_key(pred)`, which grows with the
    whole bank for a high-frequency predicate like the copula `is` — the NAC-path hot spot the profile
    named). The per-rel filter is `_fact_relnodes`' exactly (keyed by `pred`, not inert, not control
    unless this scope's pencil), so it stays behaviour-identical to the whole-predicate scan."""
    for rel in g.succ(s):                                  # rels where s is the SUBJECT (s in g.pred(rel))
        if not g.has_key(rel, pred) or g.is_inert(rel):
            continue
        if g.is_control(rel) and not (scope is not None and _rel_in_scope(g, rel, scope)):
            continue
        if o in g.succ(rel):                               # o is the OBJECT
            return rel
    return None


# --- RECORD (mode 9): journal a firing as in-graph provenance ------------------------------------

def _record(g: AttrGraph, rule_key: str, head_node: str, body_relnodes: list[str]) -> str:
    """RECORD (`processing_modes.md` mode 9, not optional): mint a `<j:rulekey>` justification —
    `proves -> head_node`, `uses -> each body fact node` — in the SAME inert substrate shape
    `GoalSolver._justify`/`rewriter` write, so `surface.explain` replays a firmware derivation as a
    CNL proof tree with no firmware-specific renderer. Provenance nodes are INERT (invisible to
    matching, `relations_from`, `derived_triples`-as-fact)."""
    from .provenance import record_firing
    return record_firing(g, rule_key, [head_node],
                         [pnode for pnode in body_relnodes if pnode is not None])

"""
Phase 4.2 — APPLY (firmware v0): match a REIFIED rule's body against the facts and EMIT its head,
with the binding environment held as VISIBLE graph structure instead of a hidden Python dict.

This is the first slice of the universal firmware (`processing_modes.md` mode 3 CHAIN uses
"APPLY over reified rules"; `implementation_plan.md` Phase 4.2). Its point — the thing that makes
it firmware rather than just another matcher — is that the working state is INSPECTABLE:

  - a partial match is a `<frame>` control node, and each binding is a reified control relation
    `<frame> -[?var]-> boundNode` (a trace renderer can show exactly what is bound, mid-match);
  - the rule is read from its REIFIED in-graph form (`rule_graph.write_rule`'s shape, Phase 3.1):
    body/head atoms are `subj -> [pred node keyed by the predicate] -> obj`, walked from the graph,
    not a Python `Rule`;
  - candidate seeding is df-driven (rarest predicate first) — the ONLY built-in heuristic
    (`processing_modes.md` §5); nothing smarter lives in the engine;
  - EMIT is monotone with CHECK-BEFORE-DERIVE (an existing head fact is the memo — a re-derivation
    is skipped), which is also what makes a recursive rule terminate under `apply_to_fixpoint`;
  - everything is FUEL-BOUNDED (`processing_modes.md` §1: "fuel bounds everything").

v0 SCOPE (deliberately small; differentially gated against `run_bank`):
  - positive rules only — `lhs` body + `rhs` head; NAC/drop/graded/rewire are Phase-5 modes.
  - plain-literal predicates (a variable predicate is out of slice).
  - head slots must resolve to a bound variable or a literal (fresh-RHS-node MINT is a later slice).
  - the driver is Python (the ratified reference style — `goal.py`/`walker.py` are Python drivers
    over graph state); the BINDINGS are the visible graph structure. The body-atom cursor is the
    driver's loop position; promoting it to a `<current-atom>` token is v1.
"""
from __future__ import annotations

from .attrgraph import AttrGraph, valued, graded, NAME
from .production_rule import is_var, is_bound_literal, literal_name

FRAME = "<frame>"
CURRENT_ATOM = "<current-atom>"
ATOM_STEP = "<atom>"
FRESH = "<fresh>"
HEAD_INDEX = "<head-index>"
ROLES = ("lhs", "rhs", "nac", "drop")

# Phase 5.3 (SUPPOSE): a VALUED tag on a pencil / scope-derived rel node naming the `<hypothesis>` scope
# it belongs to. A pencil fact is a CONTROL rel node (so it is invisible to ordinary fact matching and
# never touches ink) carrying `scope=<hypothesis-id>`; the scope-aware fact readers below make exactly
# that scope's pencil visible WITHIN it (`scope=` passed) and nothing extra when no scope is active.
SCOPE = "scope"


def rule_nodes(rule_g: AttrGraph) -> list[str]:
    """The reified rule nodes in `rule_g`: a rule node is the subject of any role relation
    (lhs/rhs/nac/drop) — the same identification `rule_graph.rules_in_graph` uses."""
    out: list[str] = []
    for nid in rule_g.nodes():
        if any(rule_g.name(rel) in ROLES for rel, _ in rule_g.relations_from(nid)):
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
    existing = {(rule_g.name(rel), obj) for rel, obj in rule_g.relations_from(hub)}
    for rn in rule_nodes(rule_g):
        for _hs, hp, _ho in _read_atoms(rule_g, rn, "rhs"):
            if (hp, rn) not in existing:
                rule_g.add_relation(hub, hp, rn, control=True)   # hub -[headPred]-> rule
                existing.add((hp, rn))
    return hub


def rules_producing(rule_g: AttrGraph, pred: str) -> list[str]:
    """The reified rule nodes whose head derives `pred`, read from the in-graph head index (built by
    `build_head_index`). Deduped, since a rule with two same-predicate head atoms indexes once here."""
    out: list[str] = []
    for hub in rule_g.nodes_named(HEAD_INDEX):
        for rel, obj in rule_g.relations_from(hub):
            if rule_g.name(rel) == pred and obj not in out:
                out.append(obj)
    return out


# --- reading the reified rule (Phase 3.1 shape) --------------------------------------------------

def _read_atoms(rule_g: AttrGraph, rule_node: str, role: str) -> list[tuple[str, str, str]]:
    """The `(s_tok, pred, o_tok)` atoms of `rule_node`'s `role` (e.g. "lhs"/"rhs"), read from the
    reified shape: `rule -[role]-> patom`, where `patom` is the pattern atom's predicate node with
    the subject slot as its (non-role) predecessor and the object slot as its successor."""
    atoms: list[tuple[str, str, str]] = []
    for role_rel, patom in rule_g.relations_from(rule_node):
        if rule_g.name(role_rel) != role:
            continue
        subj_slots = [n for n in rule_g.pred(patom) if n != role_rel]
        obj_slots = list(rule_g.succ(patom))
        atoms.append((rule_g.name(subj_slots[0]), rule_g.name(patom), rule_g.name(obj_slots[0])))
    return atoms


# --- the visible frame (bindings as graph structure) ---------------------------------------------

def _bindings(g: AttrGraph, frame: str) -> dict[str, str]:
    """Read a frame's bindings — `<frame> -[?var]-> node` — back into a dict for local decisions.
    The authoritative, inspectable state is the graph relations; this is just a read of them."""
    return {g.name(rel): obj for rel, obj in g.relations_from(frame)}


def _extend_frame(g: AttrGraph, frame: str | None, new: dict[str, str], created: list[str]) -> str:
    """A FRESH `<frame>` node carrying `frame`'s bindings plus `new` (one per added variable) — the
    monotone, no-overwrite discipline (a partial match never mutates; it forks a longer one).
    Every node it mints — the frame AND each binding rel node — is recorded in `created` so the
    whole scaffolding is GC'd afterwards: a binding `<frame> -[?var]-> factNode` adds an INCOMING
    edge to `factNode`, which would otherwise make an entity look like a rel node to a fact reader,
    so the ephemeral working memory must be swept cleanly, edges included."""
    nf = g.add_node(FRAME, control=True)
    created.append(nf)
    if frame is not None:
        for rel, obj in g.relations_from(frame):
            created.append(g.add_relation(nf, g.name(rel), obj, control=True))
    for var, node in new.items():
        created.append(g.add_relation(nf, var, node, control=True))
    return nf


def _match_slot(g: AttrGraph, bind: dict[str, str], tok: str, node: str) -> dict[str, str] | None:
    """The binding this slot adds when matched against `node`, or None if it is inconsistent.
    `{}` = matched with no new binding (a literal, or an already-bound variable that agrees)."""
    if is_var(tok):
        if tok in bind:
            return {} if bind[tok] == node else None
        return {tok: node}
    # plain or bound literal: match by name (a bound literal ALSO binds, but v0 needs no head use of it)
    return {} if g.name(node) == literal_name(tok) else None


# --- the visible body-atom cursor (the last hidden driver state -> graph structure) --------------
#
# The df-sorted body is materialized as a VISIBLE ITINERARY in the working graph: a `next`-linked
# chain of `<atom>` step nodes (each carrying its atom's tokens), with a `<current-atom>` cursor at
# the head. APPLY reads the atom to match FROM the cursor and ADVANCES the cursor along `next` —
# so "which body atom is current" (and the whole df-sorted sequence, the driver's one heuristic
# choice) is graph structure a trace renderer can read, not a Python loop index. The itinerary
# lives on FRESH control nodes only — it never touches the reified rule's atoms (an edge into a
# patom would corrupt `_read_atoms`) — and is GC'd with the frames when the pass ends.


def _build_itinerary(g: AttrGraph, body: list[tuple[str, str, str]], created: list[str],
                     delta_pos: int | None = None) -> str:
    """Materialize the (already df-sorted) `body` as a visible itinerary + a `<current-atom>` cursor
    at its head; return the cursor. Each step carries its atom's `(subj, pred, obj)` tokens as VALUED
    attrs (inspectable, and read back to drive the match); steps are chained by a control `next`
    relation; the cursor points `at` the first step. Everything minted lands in `created` for GC.

    `delta_pos` marks one step `<fresh>` — the semi-naive delta atom, whose candidate facts are
    restricted to the previous round's newly-derived delta (see `_apply_pass`). Marking it on the
    itinerary makes the delta position VISIBLE structure, not a hidden driver flag."""
    steps: list[str] = []
    for i, (s_tok, pred, o_tok) in enumerate(body):
        st = g.add_node(ATOM_STEP, control=True)
        created.append(st)
        g.set_attr(st, "subj", valued(s_tok))
        g.set_attr(st, "pred", valued(pred))
        g.set_attr(st, "obj", valued(o_tok))
        if i == delta_pos:
            g.set_attr(st, FRESH, graded(1.0))   # this atom draws only from the previous round's delta
        steps.append(st)
    for a, b in zip(steps, steps[1:]):
        created.append(g.add_relation(a, "next", b, control=True))
    cur = g.add_node(CURRENT_ATOM, control=True)
    created.append(cur)
    if steps:
        created.append(g.add_relation(cur, "at", steps[0], control=True))
    return cur


def _cursor_step(g: AttrGraph, cur: str) -> tuple[str, str] | None:
    """The cursor's current `(at_relnode, step)`, or None once the itinerary is exhausted."""
    for rel, step in g.relations_from(cur):
        if g.name(rel) == "at":
            return rel, step
    return None


def _cursor_atom(g: AttrGraph, cur: str) -> tuple[str, str, str] | None:
    """The atom the cursor is currently on, read back as `(s_tok, pred, o_tok)`, or None if done."""
    at = _cursor_step(g, cur)
    if at is None:
        return None
    _rel, step = at
    return (str(g.get_attr(step, "subj").value),
            str(g.get_attr(step, "pred").value),
            str(g.get_attr(step, "obj").value))


def _cursor_is_fresh(g: AttrGraph, cur: str) -> bool:
    """True iff the cursor's current step is the `<fresh>` (semi-naive delta) atom."""
    at = _cursor_step(g, cur)
    return at is not None and g.has_key(at[1], FRESH)


def _advance_cursor(g: AttrGraph, cur: str, created: list[str]) -> tuple[str, str, str] | None:
    """Move the cursor to the next step (follow the current step's `next`), rewriting its `at` edge;
    return the new current atom or None at end of chain. The cursor is a moving POINTER (not a
    monotone frame), so the stale `at` relation is dropped as it advances."""
    at = _cursor_step(g, cur)
    if at is None:
        return None
    at_rel, step = at
    nxt = next((obj for rel, obj in g.relations_from(step) if g.name(rel) == "next"), None)
    g.remove_node(at_rel)
    if nxt is not None:
        created.append(g.add_relation(cur, "at", nxt, control=True))
    return _cursor_atom(g, cur)


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
    SUPPOSE scope, also the scope's matching pencil rel node."""
    for rel in _fact_relnodes(g, pred, scope=scope):
        if s in g.pred(rel) and o in g.succ(rel):
            return rel
    return None


# --- RECORD (mode 9): journal a firing as in-graph provenance ------------------------------------

def _record(g: AttrGraph, rule_key: str, head_node: str, body_relnodes: list[str]) -> str:
    """RECORD (`processing_modes.md` mode 9, not optional): mint a `<j:rulekey>` justification —
    `proves -> head_node`, `uses -> each body fact node` — in the SAME inert substrate shape
    `GoalSolver._justify`/`rewriter` write, so `surface.explain` replays a firmware derivation as a
    CNL proof tree with no firmware-specific renderer. Provenance nodes are INERT (invisible to
    matching, `relations_from`, `derived_triples`-as-fact)."""
    from .provenance import PROVES, USES, j_name
    j = g.add_node({NAME: valued(j_name(rule_key))}, inert=True)
    g.add_relation(j, PROVES, head_node, inert=True)
    for pnode in body_relnodes:
        if pnode is not None:
            g.add_relation(j, USES, pnode, inert=True)
    return j


def _resolve_head(g: AttrGraph, bind: dict[str, str], tok: str) -> str | None:
    """Resolve a head slot to a node: a bound variable -> its node; a literal -> the graph's node of
    that name (minted if absent). An UNBOUND head variable is out of v0 slice (fresh MINT) -> None."""
    if is_var(tok):
        return bind.get(tok)
    name = literal_name(tok)
    existing = g.nodes_named(name)
    return existing[0] if existing else g.add_node(name)


# --- APPLY ---------------------------------------------------------------------------------------

def _apply_pass(fact_g: AttrGraph, rule_g: AttrGraph, rule_node: str, *, fuel: int,
                fresh: set[tuple[str, str, str]] | None = None,
                delta_pos: int | None = None,
                body: list[tuple[str, str, str]] | None = None,
                provenance: bool = False) -> set[tuple[str, str, str]]:
    """One APPLY pass of the reified rule at `rule_node` over the facts in `fact_g`: walk the body
    atoms serially (rarest predicate first — the df seed) via the visible `<current-atom>` cursor,
    extending a stream of visible `<frame>` bindings, then EMIT the head per full match with
    check-before-derive. Returns the set of `(s_id, pred, o_id)` facts newly EMITted this pass.
    The transient `<frame>`/itinerary scaffolding is GC'd at the end (working memory is ephemeral).

    SEMI-NAIVE delta (when `delta_pos` is a body index and `fresh` the previous round's new facts):
    the body atom at position `delta_pos` — marked `<fresh>` on the itinerary — matches ONLY facts in
    `fresh`, the others full. A new derivation needs at least one new body fact, so summing this over
    every position (in `apply_to_fixpoint`) covers exactly the fixpoint's new work without re-joining
    the whole body every round. `body` overrides the atom order — the fixpoint FREEZES one df order per
    round so `delta_pos` names the same atom across the round's passes (each atom gets exactly one turn
    as the delta); a full pass (`body=None`) df-sorts internally."""
    if body is None:
        body = _read_atoms(rule_g, rule_node, "lhs")
        # df seed-from-rarest: solve the most selective body atom first (the ONLY built-in heuristic).
        body.sort(key=lambda a: fact_g.key_count(a[1]))
    head = _read_atoms(rule_g, rule_node, "rhs")

    created: list[str] = []
    def frame(new_bindings: dict[str, str], base: str | None) -> str:
        return _extend_frame(fact_g, base, new_bindings, created)

    # The body-atom cursor is VISIBLE graph structure (`<current-atom>` over a `next`-chain itinerary),
    # not a Python loop index — the driver reads the current atom from it and advances it in the graph.
    cursor = _build_itinerary(fact_g, body, created, delta_pos=delta_pos)

    frames = [frame({}, None)]                        # one empty frame
    out_of_fuel = False
    atom = _cursor_atom(fact_g, cursor)
    while atom is not None:
        s_tok, pred, o_tok = atom
        delta_atom = fresh is not None and _cursor_is_fresh(fact_g, cursor)
        nxt: list[str] = []
        for fr in frames:
            bind = _bindings(fact_g, fr)
            for rel in _fact_relnodes(fact_g, pred):
                for s, o in _endpoints(fact_g, rel):
                    if delta_atom and (s, pred, o) not in fresh:
                        continue                      # this atom draws only from the delta
                    add_s = _match_slot(fact_g, bind, s_tok, s)
                    if add_s is None:
                        continue
                    add_o = _match_slot(fact_g, {**bind, **add_s}, o_tok, o)
                    if add_o is None:
                        continue
                    nxt.append(frame({**add_s, **add_o}, fr))
                    fuel -= 1
                    if fuel <= 0:
                        out_of_fuel = True
                        break
                if out_of_fuel:
                    break
            if out_of_fuel:
                break
        frames = nxt
        if out_of_fuel:
            break
        atom = _advance_cursor(fact_g, cursor, created)

    rule_key = rule_g.name(rule_node) if provenance else ""
    # RECORD walks the AUTHORED body order (not the df-sorted `body`) so the `uses` edges are inserted in
    # the same order `run_bank`/`GoalSolver` insert them (they iterate `rule.lhs`) — the support graph is
    # structurally identical. (Render order of sibling premises is still set-dependent, since `premises_of`
    # reads `graph.out`; explanations are therefore compared order-independently.)
    authored = _read_atoms(rule_g, rule_node, "lhs") if provenance else []
    emitted: set[tuple[str, str, str]] = set()
    for fr in frames:
        bind = _bindings(fact_g, fr)
        for hs, hp, ho in head:
            s = _resolve_head(fact_g, bind, hs)
            o = _resolve_head(fact_g, bind, ho)
            if s is None or o is None:                # unbound head var (fresh MINT) — out of v0 slice
                continue
            if not _fact_exists(fact_g, s, hp, o):
                head_node = fact_g.add_relation(s, hp, o)   # EMIT (monotone fact)
                emitted.add((s, hp, o))
                if provenance:                        # RECORD (mode 9): journal the firing
                    _record(fact_g, rule_key, head_node,
                            [_find_fact_relnode(fact_g, _resolve_head(fact_g, bind, bs), bp,
                                                _resolve_head(fact_g, bind, bo))
                             for bs, bp, bo in authored])

    for nf in created:                                # GC the ephemeral working frames + itinerary
        if fact_g.has(nf):
            fact_g.remove_node(nf)
    return emitted


def apply_rule(fact_g: AttrGraph, rule_g: AttrGraph, rule_node: str, *, fuel: int = 100_000,
               provenance: bool = False) -> int:
    """One FULL APPLY pass of the reified rule at `rule_node` over the facts; returns #facts derived
    (see `_apply_pass` for the mechanics). `provenance=True` journals each firing (RECORD, mode 9)."""
    return len(_apply_pass(fact_g, rule_g, rule_node, fuel=fuel, provenance=provenance))


def apply_to_fixpoint(fact_g: AttrGraph, rule_g: AttrGraph, rule_node: str,
                      *, fuel: int = 1_000_000, max_rounds: int = 500,
                      provenance: bool = False) -> int:
    """SATURATE (mode 1) over APPLY, SEMI-NAIVE: full-join the body once (the seed), then each round
    re-derive only from the previous round's DELTA (`<fresh>`) — for each body position in turn, that
    atom draws from the delta while the others stay full. Check-before-derive makes a recursive (e.g.
    transitive) rule terminate: a round that derives nothing new empties the delta and stops. Returns
    the total #facts derived — identical to the naive full-re-join fixpoint (differentially gated),
    only the per-round work drops from re-joining the whole closure to joining against the frontier."""
    def sorted_body() -> list[tuple[str, str, str]]:
        b = _read_atoms(rule_g, rule_node, "lhs")
        b.sort(key=lambda a: fact_g.key_count(a[1]))              # df seed, refreshed per round
        return b

    delta = _apply_pass(fact_g, rule_g, rule_node, fuel=fuel, body=sorted_body(),   # round 0: full seed
                        provenance=provenance)
    total = len(delta)
    for _ in range(max_rounds - 1):
        if not delta:
            break
        body = sorted_body()                                     # FROZEN for this round's passes
        new: set[tuple[str, str, str]] = set()
        for pos in range(len(body)):                             # delta-substitution, one atom at a time
            new |= _apply_pass(fact_g, rule_g, rule_node, fuel=fuel,
                               fresh=delta, delta_pos=pos, body=body, provenance=provenance)
        total += len(new)
        delta = new
    return total

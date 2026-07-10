"""
The engine — subgraph matching and rule application over the untyped substrate.

Matching binds rule binding-keys (variables '?x' and bound-literals 'paul?') to
node INSTANCES. A pattern (s, p, o) matches the 2-hop path  s --> p --> o, where
p is a node (relations are nodes, edges are bare). Triple-patterns sharing a
binding-key are joined into one subgraph (see production_rule.py).

Matching strategy (walkers doc §1/§6, refining vision §11): SEED-FROM-GROUND. Every
pattern is seeded at its most-selective GROUND anchor (a literal or an already-bound
variable) via the lexical index; free variables are destinations, never origins. There is
NO hop-radius neighbourhood any more — `within`/`radius` is RETIRED as the matching scope
(it was redundant with seed-from-ground and wrong when too small). The "think harder" knob
for deliberate long-range / iterative work is a WALKER's FUEL (walker.py), not a radius;
the eager-matching effort signal is df-selectivity (which anchor is rarest).

Firing (vision §4, §13): every enabled match fires (no branch selection). NAC
blocks a fire; graded conditions α-cut it and set a degree; the derived nodes take
confidence = rule.probability ⊗ graded-degree ⊗ matched-confidence. `drop` removes
matched relations (control layer only). Re-firing the same (rule, bindings) is
suppressed, giving termination for monotone rules.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..dispatch import service_calls
from ..production_rule import (
    Pat, Rule, binder, is_var, is_bound_literal, literal_name,
)
from ..provenance import PROVES, USES, j_name
from ..world_model import Graph, _is_inert


# ---------------------------------------------------------------------------
# Subgraph matching
# ---------------------------------------------------------------------------

def _try_bind(
    graph: Graph, tok: str, nid: str, bindings: dict[str, str],
    match_inert: bool = False,
) -> dict[str, str] | None:
    """Attempt to match token `tok` to node `nid` under current bindings.

    Returns new bindings on success, None on failure. Plain literals match by
    name and bind nothing. Variables / bound-literals bind their key. Matching is
    HOMOMORPHIC: distinct keys may bind the same node (needed for self-relations
    and token-passing; consistent with Datalog join semantics).

    PROVENANCE IS MATCHABLE ONLY BY PROVENANCE-AWARE RULES (`match_inert`, docs/
    depythonization_design.md §2). A justification's `proves`/`uses` edge points INTO a fact
    relation node, so `into(rel)` (used to find a pattern's subject) would offer the `proves` node
    as a spurious subject. An ordinary (reasoning) rule never names provenance, so we refuse to
    bind any of its tokens to a provenance node (proves/uses/unless/<j:...>/<axiom>/<quarantine>).
    A META/TMS rule that DOES name a provenance predicate is `match_inert=True`, and the refusal is
    lifted so its variables may bind the `<j:…>` nodes reached through the named provenance edge —
    this is what lets truth-maintenance (retraction, completion-defeat) be RULES, not a Python
    driver. The opt-in is computed per rule from its patterns (`_pats_touch_prov`)."""
    if not match_inert and _is_inert(graph.name(nid)):
        return None
    if not is_var(tok) and graph.name(nid) != literal_name(tok):
        return None
    key = binder(tok)
    if key is None:                      # plain literal: name matched, no binding
        return bindings
    if key in bindings:
        return bindings if bindings[key] == nid else None
    nb = dict(bindings); nb[key] = nid
    return nb


def _pat_refs_prov(pat: Pat) -> bool:
    """True if `pat` names a provenance name as a LITERAL (predicate or node) — proves/uses/unless
    or a `<j:`/`<axiom>`/`<quarantine>` literal. Such a pattern is a provenance-aware (meta/TMS)
    pattern: its match lifts the inert-bind refusal (see `_try_bind`). A free-variable token is not
    a reference — only an explicit literal opts a rule in, so a reasoning rule (which never names
    provenance) can never accidentally match it. The linter flags a reasoning rule that does."""
    return any(not is_var(t) and _is_inert(literal_name(t)) for t in pat.tokens())


def _pats_touch_prov(pats: list[Pat]) -> bool:
    """Is this pattern set provenance-aware? (any pattern names a provenance literal.)"""
    return any(_pat_refs_prov(p) for p in pats)


_INF = float("inf")
_FREE, _BOUND, _LIT = 0, 1, 2


def _pos(graph: Graph, tok: str, bindings: dict[str, str]) -> tuple[float, int, str | None]:
    """(selectivity, kind, value) for one pattern position — computed WITHOUT materializing any
    candidate list. `kind` is _BOUND (value=node id, df 1), _LIT (value=name, df via the index),
    or _FREE (value=None, df infinite). The df is the seed-selection key (§11/§14); a stopword
    literal like `is_a` reports its huge df in O(1) but is never enumerated unless it is the
    rarest — that is the fix for the seed-from-ground cost being O(graph) on a stopword anchor."""
    key = binder(tok)
    if key is not None and key in bindings:
        return 1, _BOUND, bindings[key]
    if is_var(tok):
        return _INF, _FREE, None
    name = literal_name(tok)
    return graph.name_count(name), _LIT, name


def _pos_ok(graph: Graph, kind: int, val: str | None, nid: str) -> bool:
    """Does node `nid` satisfy a NON-seed position? Free accepts anything; bound must equal the
    bound id; literal must match by name (O(1)) — so a non-seed anchor filters per-candidate
    instead of being materialized into a list."""
    if kind == _FREE:
        return True
    if kind == _BOUND:
        return nid == val
    return graph.name(nid) == val


def _triples(graph: Graph, pat: Pat, bindings: dict[str, str]):
    """Yield (s_id, p_id, o_id) along the path  s --> p --> o  for `pat`, SEEDED FROM GROUND.

    SEED-FROM-GROUND (docs/walkers_and_locality.md §1, refining vision §11): seed only from a
    GROUND position — a literal or an already-bound variable — never from a free variable (the
    unknown we are solving for). Among the ground positions, seed from the MOST SELECTIVE: the
    lowest live `df` (a bound key has 1 candidate; an absent literal has 0 -> the pattern fails
    fast — free dead-rule elimination subsuming anchor-delta activation). A pattern with NO
    ground position yields nothing (reachable only by a join binding a var, or a demand walker).

    Only the SEED position is materialized (via the index); the other two positions filter each
    candidate by name/identity (`_pos_ok`, O(1)). So a stopword predicate (`is_a`, df ~ |edges|)
    that is NOT the seed costs O(1) to weigh and is never enumerated — the matching-bound cost
    the WordNet probe surfaced. (There is no `scope` set any more: `within`/radius was retired
    as the matching neighbourhood, §11, so matching is over the whole graph; the index seed keeps
    it cheap. Final binding/consistency, incl. repeated vars within a Pat, is `_try_bind` in
    `_match` — `_triples` only proposes triples.)"""
    s = _pos(graph, pat.s, bindings)
    p = _pos(graph, pat.p, bindings)
    o = _pos(graph, pat.o, bindings)

    # Pick the ground position with the lowest df. Ties keep p > s > o order (preserving the
    # previous predicate-first behaviour when only the predicate is ground).
    which = min((p[0], 0), (s[0], 1), (o[0], 2))
    if which[0] == _INF:                                      # no ground anchor — never scan
        return
    seed = which[1]

    def cands(pos: tuple[float, int, str | None]) -> list[str]:
        return [pos[2]] if pos[1] == _BOUND else graph.nodes_named(pos[2])  # seed is never _FREE

    if seed == 0:                                             # seed from the predicate node
        for p_id in cands(p):
            for s_id in graph.pred(p_id):
                if not _pos_ok(graph, s[1], s[2], s_id):
                    continue
                for o_id in graph.succ(p_id):
                    if _pos_ok(graph, o[1], o[2], o_id):
                        yield s_id, p_id, o_id
    elif seed == 1:                                           # seed from the subject node
        for s_id in cands(s):
            for p_id in graph.succ(s_id):
                if not _pos_ok(graph, p[1], p[2], p_id):
                    continue
                for o_id in graph.succ(p_id):
                    if _pos_ok(graph, o[1], o[2], o_id):
                        yield s_id, p_id, o_id
    else:                                                     # seed from the object node
        for o_id in cands(o):
            for p_id in graph.pred(o_id):
                if not _pos_ok(graph, p[1], p[2], p_id):
                    continue
                for s_id in graph.pred(p_id):
                    if _pos_ok(graph, s[1], s[2], s_id):
                        yield s_id, p_id, o_id


def _match(
    graph: Graph, pats: list[Pat], idx: int,
    bindings: dict[str, str],
    out: list[dict[str, str]], first_only: bool = False,
    prem: list[str] | None = None, prem_out: list[list[str]] | None = None,
    match_inert: bool = False,
) -> None:
    if idx == len(pats):
        out.append(dict(bindings))
        if prem_out is not None:
            prem_out.append(list(prem))
        return
    pat = pats[idx]
    for s_id, p_id, o_id in _triples(graph, pat, bindings):
        b1 = _try_bind(graph, pat.s, s_id, bindings, match_inert)
        if b1 is None:
            continue
        b2 = _try_bind(graph, pat.p, p_id, b1, match_inert)
        if b2 is None:
            continue
        b3 = _try_bind(graph, pat.o, o_id, b2, match_inert)
        if b3 is None:
            continue
        if prem is not None:
            prem.append(p_id)                # the matched relation node (a premise)
        _match(graph, pats, idx + 1, b3, out, first_only, prem, prem_out, match_inert)
        if prem is not None:
            prem.pop()
        if first_only and out:
            return


def match(graph: Graph, pats: list[Pat], scope: set[str] | None = None) -> list[dict[str, str]]:
    """All variable/bound-literal bindings of the subgraph `pats`. `scope` is vestigial
    (`within`/radius was retired as the matching neighbourhood, §11): matching is over the
    whole graph, kept cheap by the index seed. Accepted for back-compat, ignored."""
    out: list[dict[str, str]] = []
    _match(graph, pats, 0, {}, out, match_inert=_pats_touch_prov(pats))
    return out


def match_with_premises(
    graph: Graph, pats: list[Pat], scope: set[str] | None = None,
) -> list[tuple[dict[str, str], list[str]]]:
    """Like `match`, but each result pairs the bindings with the PREMISE relation nodes
    it matched (the relation node per Pat, in order). The engine wires these as `uses`
    edges of the firing's justification (see provenance.py). `scope` is vestigial (see `match`)."""
    out: list[dict[str, str]] = []
    prem_out: list[list[str]] = []
    _match(graph, pats, 0, {}, out, False, [], prem_out, match_inert=_pats_touch_prov(pats))
    return list(zip(out, prem_out))


def _looks_like_relation(graph: Graph, nid: str) -> bool:
    """A relation node lies on a path subject -> [rel] -> object, so it has both a
    predecessor and a successor (used to pick delta relation nodes for a variable predicate)."""
    return bool(graph.pred(nid)) and bool(graph.succ(nid))


def delta_matches(
    graph: Graph, pats: list[Pat], scope: set[str] | None, delta: set[str],
) -> list[tuple[dict[str, str], list[str]]]:
    """Semi-naive matching (vision §11): all (bindings, premises) of `pats` that use AT LEAST
    ONE relation node in `delta` (the change frontier). `scope` is vestigial (see `match`).

    A genuinely NEW monotone match must bind some new relation node (a fresh entity has no
    relations, so it completes no s->p->o pattern), and new relation nodes are in `delta`.
    So we anchor EACH pattern to a delta relation node in turn and join the rest; a match that
    touches delta in several positions is found once per position, deduped by its bindings.
    This avoids re-scanning the old x old combinations every round — the cost the profiler
    flagged for transitive closures. NOT used for graded rules (a pure embedding change has no
    relation node in the delta) — those fall back to the full matcher.
    """
    results: list[tuple[dict[str, str], list[str]]] = []
    seen: set[frozenset] = set()
    mi = _pats_touch_prov(pats)              # provenance-aware match? (computed over the FULL rule)
    for i, pat_i in enumerate(pats):
        rest = pats[:i] + pats[i + 1:]
        if is_var(pat_i.p):
            cands = [d for d in delta if _looks_like_relation(graph, d)]
        else:
            # Filter the (small) delta by name — NOT `nodes_named(pred) ∩ delta`, which
            # materializes every node of that name (84k for the `is_a` stopword; the WordNet
            # probe's residual after the `_triples` fix). delta is the change frontier, so
            # iterating it is O(|delta|), independent of the predicate's df.
            pname = literal_name(pat_i.p)
            cands = [d for d in delta if graph.name(d) == pname]
        for p_id in cands:
            b_p = _try_bind(graph, pat_i.p, p_id, {}, mi)
            if b_p is None:
                continue
            for s_id in graph.pred(p_id):
                b_s = _try_bind(graph, pat_i.s, s_id, b_p, mi)
                if b_s is None:
                    continue
                for o_id in graph.succ(p_id):
                    b3 = _try_bind(graph, pat_i.o, o_id, b_s, mi)
                    if b3 is None:
                        continue
                    out: list[dict[str, str]] = []
                    prem_out: list[list[str]] = []
                    _match(graph, rest, 0, b3, out, False, [], prem_out, match_inert=mi)
                    for b, prem in zip(out, prem_out):
                        bk = frozenset(b.items())
                        if bk in seen:                      # touched delta in >1 position
                            continue
                        seen.add(bk)
                        results.append((b, [p_id] + prem))
    return results


# ---------------------------------------------------------------------------
# NAC and graded conditions
# ---------------------------------------------------------------------------

def _nac_existence_only_pat(pat: Pat, bindings: dict[str, str]) -> bool:
    """True if `pat` has no FREE binders (every var/bound-literal token is already bound by the
    LHS). Then it is a fixed existence check — no node scan needed."""
    for tok in pat.tokens():
        key = binder(tok)
        if key is not None and key not in bindings:
            return False
    return True


def _nac_existence_only(rule: Rule, bindings: dict[str, str]) -> bool:
    """True if the NAC has no FREE binders (every var/bound-literal token is already bound by
    the LHS). Then the NAC is a fixed conjunction of existence checks — no node scan needed."""
    return all(_nac_existence_only_pat(pat, bindings) for pat in rule.nac)


def _bound_pat_exists(graph: Graph, pat: Pat, bindings: dict[str, str]) -> bool:
    """Does `pat` hold under fixed `bindings`? Bound tokens resolve to their node; plain
    literals range over all nodes of that name (homomorphic, as `_match` would). O(degree)."""
    def cands(tok: str) -> list[str]:
        key = binder(tok)
        if key is not None:
            return [bindings[key]]
        return graph.nodes_named(literal_name(tok))
    pk = binder(pat.p)
    for s in cands(pat.s):
        for o in cands(pat.o):
            if pk is not None:
                p = bindings[pk]
                if p in graph.succ(s) and o in graph.succ(p):
                    return True
            elif _relation_exists(graph, s, literal_name(pat.p), o):
                return True
    return False


def _nac_groups(rule: Rule, bindings: dict[str, str]) -> list[list[Pat]]:
    """Partition `rule.nac` into INDEPENDENT negation groups, connected by shared NAC-local
    free variables (binders not already bound by the LHS).

    This is the difference between `not (A and B)` and `not A and not B`. Two NAC clauses that
    SHARE a free var are one existential conjunction — `not ?x chosen and not ?x add ?c` means
    "no ?x that is BOTH chosen AND adds ?c" (commitment's one-per-need guard). Two clauses with
    NO shared free var are SEPARATE negations — `not unmet ?anyp and not done` means "no unmet
    precondition" AND (independently) "not done", the readiness gate. Treating the whole `nac`
    list as one conjunction (the old behaviour) silently made a multi-clause readiness NAC
    cosmetic: `ready` fired unless EVERY clause held at once. Grouping by shared free var gives
    both readings correctly — the bound subject (`?o`/`?x`) does not connect groups, only a
    genuinely free NAC-local var does."""
    def free(pat: Pat) -> set[str]:
        return {b for t in pat.tokens() if (b := binder(t)) is not None and b not in bindings}

    groups: list[tuple[set[str], list[Pat]]] = []
    for pat in rule.nac:
        fv = free(pat)
        merged: list[tuple[set[str], list[Pat]]] = []
        cur_vars, cur_pats = set(fv), [pat]
        for gv, gp in groups:                      # absorb any existing group sharing a free var
            if fv and gv & fv:
                cur_vars |= gv
                cur_pats = gp + cur_pats
            else:
                merged.append((gv, gp))
        merged.append((cur_vars, cur_pats))
        groups = merged
    return [pats for _, pats in groups]


def nac_blocks(graph: Graph, rule: Rule, bindings: dict[str, str]) -> bool:
    """True if ANY independent NAC group matches under the LHS bindings (blocks the rule).

    Each group (`_nac_groups`) is an existential conjunction; the rule is blocked if any one
    of them is satisfiable — `not A and not B` is `¬A ∧ ¬B`, so either alone suffices to block.

    Fast path per group (the common case — transitivity's `?a is_a ?c`, goal's `?g is
    satisfied`): when the group has no free binders it is a fixed conjunction, so we
    existence-check each pattern (O(degree)) instead of seeding `_match` over
    `set(graph.nodes())` — the latter rebuilt the whole node population on every candidate
    match (profiling 2026-06-30 flagged it as the 2nd-biggest cost). Otherwise (NAC-only
    existential vars) fall back to the scan, scoped to that group's patterns."""
    if not rule.nac:
        return False
    for group in _nac_groups(rule, bindings):
        if all(_nac_existence_only_pat(pat, bindings) for pat in group):
            if all(_bound_pat_exists(graph, pat, bindings) for pat in group):
                return True
        else:
            out: list[dict[str, str]] = []
            _match(graph, group, 0, dict(bindings), out, first_only=True,
                   match_inert=_pats_touch_prov(group))
            if out:
                return True
    return False


def graded_degree(graph: Graph, rule: Rule, bindings: dict[str, str]) -> float | None:
    """Degree in (0, 1] for the graded conditions, or None if the α-cut fails."""
    if not rule.graded:
        return 1.0
    degs: list[float] = []
    for c in rule.graded:
        nid = bindings.get(c.var)
        if nid is None:
            return None
        emb = graph.get_embedding(nid)
        scores = [emb.get(d, 0.0) for d in c.embedding]
        score = min(scores) if scores else 0.0
        if c.inverted:
            if score > (1.0 - c.threshold):
                return None
            degs.append(1.0 - score)
        else:
            if score < c.threshold:
                return None
            degs.append(score)
    return min(degs) if degs else 1.0


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def _relation_exists(graph: Graph, s_id: str, pname: str, o_id: str) -> bool:
    for r in graph.succ(s_id):
        if graph.name(r) == pname and o_id in graph.succ(r):
            return True
    return False


def _remove_relation(graph: Graph, s_id: str, pname: str, o_id: str) -> bool:
    for r in list(graph.out(s_id)):
        if graph.name(r) == pname and o_id in graph.out(r):
            graph.remove_node(r)
            return True
    return False


# ---------------------------------------------------------------------------
# Embedding effects — rule-driven writes to the graded layer (vision §13)
# ---------------------------------------------------------------------------
#
# Reading embeddings is already a rule mechanism (graded conditions); WRITING them
# must be too, or domain logic leaks into a bolt-on Python pass (a seam). A rule
# declares its embedding effect declaratively in `rule.propagate` — parameters on
# the rule, mechanism in the engine (never a Python closure, per §13). Supported:
#   {"op": "set", "var": "?x", "dim": "?adj", "value": 0.8}
#       set ?x.embedding[name(?adj)] = value  (dim may be a bound var or a literal)
# This is the one local computation; more ops (weighted_sum/shift for bottom-up
# propagation) slot into the same dispatch.

def _propagate_ops(rule: Rule) -> list[dict]:
    p = rule.propagate
    if p is None:
        return []
    return p if isinstance(p, list) else [p]


def _resolve_bound(
    graph: Graph, tok: str, bindings: dict[str, str], fresh: dict[str, str],
) -> str | None:
    """A bound/fresh node id for `tok`, or the first node so named, else None."""
    key = binder(tok)
    if key is None:
        named = graph.nodes_named(literal_name(tok))
        return named[0] if named else None
    return bindings.get(key) or fresh.get(key)


def _token_name(
    graph: Graph, tok: str, bindings: dict[str, str], fresh: dict[str, str],
) -> str:
    """The node NAME a token resolves to (e.g. a bound '?adj' -> 'urgent')."""
    nid = _resolve_bound(graph, tok, bindings, fresh)
    return graph.name(nid) if nid is not None and graph.has(nid) else literal_name(tok)


def apply_rule(
    graph: Graph, rule: Rule, bindings: dict[str, str], degree: float,
    premises: list[str] | None = None,
) -> tuple[set[str], set[str]]:
    """Fire `rule` under `bindings`. Returns (created_ids, changed_ids).

    When `premises` (the matched LHS relation nodes) is given, the firing materializes
    an in-graph justification `J --proves--> Ci`, `J --uses--> Pj` (provenance.py). The
    J/proves/uses nodes are NOT returned in created/changed: they are provenance, inert
    to reasoning and to the change frontier.
    """
    confs = [graph.get_confidence(n) for n in bindings.values() if graph.has(n)]
    conf = _clamp01(rule.probability * degree * (min(confs) if confs else 1.0))

    created: set[str] = set()
    changed: set[str] = set()
    made_facts: list[str] = []                   # relation instances created this firing
    fresh: dict[str, str] = {}

    def resolve_so(tok: str) -> str:
        """Resolve a subject/object token to a node id (bound, fresh, or concept)."""
        key = binder(tok)
        if key is not None and key in bindings:
            return bindings[key]
        if key is not None:                         # RHS-only var / bound-literal → fresh
            if key in fresh:
                return fresh[key]
            name = literal_name(tok) if is_bound_literal(tok) else ""
            nid = graph.add_node(name, confidence=conf)
            fresh[key] = nid
            created.add(nid)
            return nid
        nm = literal_name(tok)                       # plain literal → shared concept node
        existing = graph.nodes_named(nm)
        if existing:
            return existing[0]
        nid = graph.add_node(nm)
        created.add(nid)
        return nid

    for pat in rule.rhs:
        s_id = resolve_so(pat.s)
        o_id = resolve_so(pat.o)
        pkey = binder(pat.p)
        if pkey is not None:                         # predicate is a (possibly fresh) node
            if pkey in bindings:
                p_id = bindings[pkey]
            elif pkey in fresh:
                p_id = fresh[pkey]
            else:
                p_id = graph.add_node(literal_name(pat.p) if is_bound_literal(pat.p) else "",
                                      confidence=conf)
                fresh[pkey] = p_id
                created.add(p_id)
            graph.add_edge(s_id, p_id)
            graph.add_edge(p_id, o_id)
            made_facts.append(p_id)
        else:                                        # plain-literal predicate → fresh relation
            pname = literal_name(pat.p)
            if not _relation_exists(graph, s_id, pname, o_id):
                p_id = graph.add_relation(s_id, pname, o_id, confidence=conf)
                created.add(p_id)
                made_facts.append(p_id)
        changed.add(s_id)
        changed.add(o_id)

    for pat in rule.drop:                            # control-layer deletion
        s_id = bindings.get(binder(pat.s)) if binder(pat.s) else _concept(graph, pat.s)
        o_id = bindings.get(binder(pat.o)) if binder(pat.o) else _concept(graph, pat.o)
        pkey = binder(pat.p)
        pname = bindings.get(pkey) and graph.name(bindings[pkey]) if pkey else literal_name(pat.p)
        if s_id and o_id and pname and _remove_relation(graph, s_id, pname, o_id):
            changed.add(s_id)
            changed.add(o_id)

    for op, ta, tb in rule.rewire:                   # control-layer raw-edge surgery (§4 / rewiring)
        a, b = resolve_so(ta), resolve_so(tb)        # bound nodes (or a fresh interposer literal)
        if op == "cut":
            graph.remove_edge(a, b)
        elif op == "link":
            graph.add_edge(a, b)
        else:
            raise ValueError(f"unknown rewire op {op!r} (expected 'cut' or 'link')")
        changed.add(a)
        changed.add(b)

    for op in _propagate_ops(rule):                  # embedding effects (vision §13)
        tgt = _resolve_bound(graph, op["var"], bindings, fresh)
        if tgt is None or not graph.has(tgt):
            continue
        if op.get("op") == "set":
            emb = graph.get_embedding(tgt)
            emb[_token_name(graph, op["dim"], bindings, fresh)] = float(op["value"])
            graph.set_embedding(tgt, emb)
            changed.add(tgt)

    if premises is not None and made_facts:          # in-graph justification (provenance.py)
        # `inert=True` (Phase 2.2): `relations_from`/`within` now filter provenance scaffolding by
        # this dedicated flag, not the old name-string `_is_inert` sniff — a justification minted
        # here without it is invisible to NOTHING (readers see straight through `proves`/`uses` as
        # if they were domain edges), e.g. `expand_relation_properties` misreading a `<j> --proves-->
        # (rel_property reification)` as "the justification node itself has a `rel_property`".
        j = graph.add_node(j_name(rule.key), inert=True)
        for c in made_facts:
            graph.add_relation(j, PROVES, c, inert=True)
        for pr in premises:
            if graph.has(pr):
                graph.add_relation(j, USES, pr, inert=True)

    return created, created | changed


def _concept(graph: Graph, tok: str) -> str | None:
    named = graph.nodes_named(literal_name(tok))
    return named[0] if named else None


# ---------------------------------------------------------------------------
# The stupid scheduler — fire enabled rules in the frontier until fixpoint
# ---------------------------------------------------------------------------

# `Firing` now lives in `production_rule` (an engine-neutral home, so the journal consumers do not
# import this reference engine). Re-exported here for back-compat (tests import `rewriter.Firing`).
from ..production_rule import Firing  # noqa: E402


# ---------------------------------------------------------------------------
# Anchor-delta rule activation (vision §11 — the incremental half of the Rete)
# ---------------------------------------------------------------------------
#
# Profiling (2026-06-30, memory finding-matcher-is-matching-bound) showed run() is
# MATCHING-bound: each step re-matches EVERY rule over the locality scope, even rules
# the latest change could not possibly have enabled. Anchor-delta activation skips
# those: a rule is *attempted* in a step only if the change frontier could enable a
# NEW match of it.
#
# SOUNDNESS. A new monotone match needs a new RELATION node in the delta (a bare entity
# with no relations completes no s->p->o pattern). That relation node carries the
# predicate's NAME, so a rule with a literal predicate `p` can have a new match only if
# a node named `p` is in the delta. Hence: skip a rule iff none of its LHS literal
# predicate names appears among the delta node names. Conservative carve-outs that must
# always be woken (else we could wrongly skip):
#   - a Pat with a VARIABLE predicate (`?p`) matches relations of ANY name -> wildcard;
#   - a rule with GRADED conditions can flip from blocked to firing on a pure embedding
#     change (no structural delta) -> wildcard (graded rules are few);
#   - any step that DELETED a relation (control `drop`) can unblock a NAC non-locally
#     -> the whole next step disables filtering (the monotone "additions only" argument
#     fails under deletion). The reasoning layer never deletes, so this only ever
#     loosens the control layer.
# With these carve-outs the set of newly-fired (rule, bindings) per step is identical to
# the unfiltered engine — only redundant match attempts are removed. The identical-journal
# test (filter on vs off) is the standing guard.
#
# The Rewriter object also OWNS the place for future supporting machinery that must NOT
# live in the graph (it is a cache, rebuildable from the rules, invisible to rules — like
# Graph._by_name): e.g. a persistent per-rule "locality fires" counter for ordering /
# adaptive-radius. Not built yet — the profile shows the cost is redundant re-scanning,
# not bad iteration ORDER, so a counter is premature.

def _anchor_names(rule: Rule) -> set[str]:
    """Every GROUND anchor NAME in `rule`'s LHS — the names the lexical index can seed this
    rule from (literal predicates/subjects/objects and bound-literals; free variables are not
    anchors). E.g. walk.step's anchors include its walker token name, `reached`, `fuel`, and
    the relation literal."""
    return {literal_name(t) for pat in rule.lhs for t in pat.tokens() if not is_var(t)}


def near_rules(graph: Graph, rules: list[Rule], locus: str) -> list[Rule]:
    """The rules NEAR a ground locus (vision §11 / walkers doc §7): those the lexical index
    would seed from this node — i.e. whose LHS has a ground anchor matching the node's NAME.

    This is the concrete "rules anchored at the active loci" of §7. A walker is a persistent,
    moving ground locus (its token); calling this on the token gives its near-rule set, and
    TWO walkers with different tokens get DIFFERENT near-rules automatically — concurrent
    control flows, each firing only its own rules, for free (no per-walker rule-set is frozen;
    the near-set is recomputed from position via the index). It is content-blind (it reads only
    node names + rule anchors, §14), so it never decides WHICH inference to make — only which
    rules this position could seed."""
    nm = graph.name(locus)
    return [r for r in rules if nm in _anchor_names(r)]


def _rule_anchors(rule: Rule) -> tuple[frozenset[str], bool]:
    """(literal predicate names of `rule.lhs`, is_wildcard). Wildcard = a variable
    predicate or graded conditions => the rule must be woken on any delta."""
    preds: set[str] = set()
    wildcard = bool(rule.graded)
    for pat in rule.lhs:
        if is_var(pat.p):
            wildcard = True
        else:
            preds.add(literal_name(pat.p))
    return frozenset(preds), wildcard


class Rewriter:
    """The stateful engine. Holds per-rule anchor predicates (supporting machinery — NOT
    in the graph; a rebuildable cache, like Graph._by_name) so a step can wake only the
    rules a change could have enabled. Results are identical to the unfiltered engine."""

    def __init__(self, rules: list[Rule], *, activation: bool = True,
                 semi_naive: bool = True, tools: dict | None = None) -> None:
        self.rules = sorted(rules, key=lambda r: r.priority, reverse=True)
        self.activation = activation
        self.semi_naive = semi_naive
        self.tools = tools or {}              # name -> Tool; serviced at each rule-fixpoint
        self._anchors: dict[int, frozenset[str]] = {}
        self._wildcard: set[int] = set()
        self._graded: set[int] = set()            # full-match carve-out (embedding flips)
        for r in self.rules:
            preds, wild = _rule_anchors(r)
            self._anchors[id(r)] = preds
            if wild:
                self._wildcard.add(id(r))
            if r.graded:
                self._graded.add(id(r))

    def _relevant(self, rule: Rule, delta_names: set[str]) -> bool:
        return id(rule) in self._wildcard or bool(self._anchors[id(rule)] & delta_names)

    def run(
        self, graph: Graph, *,
        max_steps: int = 200,
        seeds: list[str] | None = None, provenance: bool = True,
    ) -> list[Firing]:
        changed: set[str] = set(seeds) if seeds is not None else set(graph.nodes())
        fired: set[tuple[str, frozenset]] = set()
        journal: list[Firing] = []
        force_all = True            # first step always considers all rules (no prior delta)

        for _ in range(max_steps):
            # Matching is UNBOUNDED (walkers doc §6 — the `within`/hop-radius matching
            # neighbourhood is retired): seed-from-ground (§1) starts every pattern at its
            # rarest GROUND anchor via the index, and control self-bounds on its low-df token
            # (§2), so a hop-radius cap is redundant — and was actively WRONG when too small (a
            # 40-hop transitive chain closed incompletely under a 3-hop cap). Long-range /
            # iterative work is a WALKER's fuel now, not a matching radius. There is no `scope`
            # set: rebuilding `set(graph.nodes())` every step was itself O(graph) per step (the
            # WordNet probe's second cost); the index seed makes a whole-graph match cheap.
            delta_names = {graph.name(n) for n in changed if graph.has(n)}
            filtering = self.activation and not force_all

            pending: list[tuple[Rule, dict[str, str], tuple[str, frozenset], float, list[str]]] = []
            for rule in self.rules:
                if filtering and not self._relevant(rule, delta_names):
                    continue
                # Delta-restricted matching once we have a real frontier (semi-naive),
                # except graded rules (an embedding change leaves no relation in the delta).
                if (self.semi_naive and not force_all and id(rule) not in self._graded):
                    matches = delta_matches(graph, rule.lhs, None, changed)
                else:
                    matches = match_with_premises(graph, rule.lhs)
                for b, prem in matches:
                    sig = (rule.key, frozenset(b.items()))
                    if sig in fired:
                        continue
                    if nac_blocks(graph, rule, b):
                        continue
                    deg = graded_degree(graph, rule, b)
                    if deg is None:
                        continue
                    pending.append((rule, b, sig, deg, prem))

            new_changed: set[str] = set()
            deleted = False
            for rule, b, sig, deg, prem in pending:
                if sig in fired:
                    continue
                fired.add(sig)
                # `rule.meta` rules (TMS/retraction) fire PROVENANCE-SILENT even when the run
                # emits provenance — the regress guard: a meta-rule naming proves/uses would else
                # re-match the <j:> it just minted (docs/coref_as_rules_design.md). This lets
                # reasoning (prov on) and TMS rules coexist in one run.
                emit_prov = provenance and not rule.meta
                created, touched = apply_rule(graph, rule, b, deg,
                                              premises=prem if emit_prov else None)
                journal.append(Firing(rule.key, b, created, deg))
                new_changed |= touched
                if rule.drop or rule.rewire:      # deletion (drop) / edge cut (rewire) can unblock a NAC non-locally
                    deleted = True

            if not new_changed:
                # Rules have quiesced this step. Service any materialized tool calls
                # (vision §6/§12.5): a rule emitted a <call>, the engine routes it to its
                # tool, and the nodes the tool emits become the next change frontier — so
                # reasoning resumes on the tool's output. When neither rules nor tools
                # produce anything new, we are at the true fixpoint.
                if self.tools:
                    touched = service_calls(graph, self.tools)
                    if touched:
                        changed = touched
                        force_all = True        # tool output: reconsider all rules, unfiltered
                        continue
                break
            changed = new_changed
            # A deletion can unblock a NAC non-locally; the additions-only soundness
            # argument fails, so the next step must consider all rules.
            force_all = deleted

        return journal


def run(
    graph: Graph,
    rules: list[Rule],
    *,
    max_steps: int = 200,
    seeds: list[str] | None = None,
    provenance: bool = True,
    activation: bool = True,
    semi_naive: bool = True,
    tools: dict | None = None,
) -> list[Firing]:
    """Apply `rules` to `graph` (in place) until fixpoint or `max_steps`.

    Returns the append-only journal of firings. Matching is seed-from-ground and UNBOUNDED
    (walkers doc §6 — the hop-radius matching neighbourhood is retired). `seeds` is the
    initial change frontier for semi-naive matching (defaults to the whole graph).

    `provenance` (default True) emits in-graph justifications per firing (provenance.py)
    so explanation/retraction/coreference can read the support from the graph. It is
    turned OFF for the non-monotone CONTROL layer (the planning loop), where the
    scaffolding churns for many cycles and accumulated J nodes would only slow matching —
    control flow is not explained, so it needs no provenance.

    `activation` (default True) enables anchor-delta rule activation: each step wakes
    only the rules the change frontier could have enabled. `semi_naive` (default True)
    additionally restricts each woken rule's matching to bindings that use a relation node
    from the change frontier (vision §11 semi-naive evaluation). Both are off on the first
    step and after a deleting step. Set either False to force the unfiltered engine (used
    by the identical-results regression test).

    `tools` (default None) is a registry {tool-name -> handler} of materialized tool calls
    (dispatch.py): whenever the rules reach a fixpoint, the engine services any pending
    `<call>` nodes against this registry and folds the tools' output back into reasoning,
    until BOTH rules and tools quiesce. With no registry the loop behaves exactly as before.
    """
    return Rewriter(rules, activation=activation, semi_naive=semi_naive, tools=tools).run(
        graph, max_steps=max_steps, seeds=seeds, provenance=provenance,
    )

"""Causation crossing over the scope-tree — the Step-2 production home (scope_reframe_audit.md §6 Step 2).

Propositional causation (`that A causes that B`) as the SCOPE REFRAME realizes it: each proposition is a
SCOPE NODE holding its statement as scoped members; a base `causes` fact relates the two scopes; and the
crossing is DECLARED RULES over the `@?h` scope-tree relativized read (`chain._relativized_st_matching`) —
NO `prop:` content-key handle, NO orphan participant refs. This replaces `cnl/cause_surface.py`'s stringly
re-implementation of interning (audit row 6).

THE MODEL (crystallized in `bench/spike_scopetree_rel_read.py`, GO end-to-end):
  * `holds_base(scope)` is the UNIVERSAL verdict "this scope's content is true in base". Per-relativizer
    rules DERIVE it — causation via modus ponens (`?b holds_base when ?a holds_base and ?a causes ?b`); a
    trusted-holder attribution rule would derive it identically. The meaning lives in the DERIVATION.
  * `reify` is the base case: a scope holds in base when its member, dereferenced, holds in base.
  * `promote` is ONE uniform, relativizer-agnostic rule: a held scope's members ARE true in base.
The `@?h` read binds `(subject, predicate, object, scope)` from a member relation and DEREFERENCES the
participants to their base referents (identity via `denotes`, node not name), so the rule bodies read
ordinary base nodes — not blocked by base-vantage scope isolation.

The ONE non-rule mechanism is `materialize_held` (mint a base referent for a held scope's member lacking
one — audit primitive ③/④ "materialize base referent on cross"); a follow-on folds it into a reactive
skolem-minting rule (needs the `denotes`-visibility exemption).
"""
from __future__ import annotations

from .attrgraph import AttrGraph, NAME, valued
from .chain import ById, chain_sip, _facts_matching
from .cnl.machine_rules import load_machine_rules
from .scope_tree import put_under, scope_of
from .vocabulary import DENOTES

Triple = tuple[str, str, str]

# ── the declared crossing rules ───────────────────────────────────────────────
# DECIDE — reify (base case) + causal MP. `holds_base(scope)` is the universal "true in base" verdict.
_DECIDE_CNL = (
    "?scope holds_base yes when ?s ?p ?o @?scope and ?s ?p ?o\n"
    "?b holds_base yes when ?a holds_base yes and ?a causes ?b"
)
# PROMOTE — the uniform materialization: a held scope's members are true in base (variable-predicate head).
_PROMOTE_CNL = "?s ?p ?o when ?scope holds_base yes and ?s ?p ?o @?scope"


def decide_rules():
    """The reify + causal-MP rules (which scopes hold in base)."""
    return load_machine_rules(_DECIDE_CNL)


def promote_rules():
    """The uniform promote/dereify rule (a held scope's members land in base)."""
    return load_machine_rules(_PROMOTE_CNL)


# ── minting the scope structure ───────────────────────────────────────────────
_N = [0]


def mint_scope(g: AttrGraph) -> str:
    """An ORDINARY scope node (a fact BETWEEN scopes — `S causes S'`, `S holds_base yes` — must be readable,
    so a scope cannot be `<hypothesis>` control), UNIQUELY named so the demand engine's name-union never
    merges two distinct scopes. A scope's identity is the node, never a shared name."""
    _N[0] += 1
    return g.add_node({NAME: valued(f"<scope:{_N[0]}>".replace("<", "scope_").replace(">", ""))})


def _member(g: AttrGraph, name: str, scope: str) -> str:
    n = g.add_node({NAME: valued(name)})
    put_under(g, n, scope)
    return n


def mint_proposition(g: AttrGraph, triple: Triple) -> str:
    """A proposition as a SCOPE holding its statement: mint a scope, place the triple's `(subj, pred, obj)`
    as a member born UNDER it (scoped copies, isolated from base by default). Returns the scope node."""
    s, p, o = triple
    sc = mint_scope(g)
    g.add_relation(_member(g, s, sc), p, _member(g, o, sc))
    return sc


def mint_causal_link(g: AttrGraph, antecedent: Triple, consequent: Triple) -> tuple[str, str]:
    """`that A causes that B`: two proposition scopes related by a base `causes` fact. Returns `(s_a, s_b)`.
    Idempotent per statement is the caller's concern (a re-stated link re-mints; interning is future work)."""
    s_a = mint_proposition(g, antecedent)
    s_b = mint_proposition(g, consequent)
    g.add_relation(s_a, "causes", s_b)
    return s_a, s_b


# ── the crossing driver (decide → materialize) ────────────────────────────────

def reconcile_scopes(g: AttrGraph) -> None:
    """Identity union (audit primitive ④): draw `denotes` from each scoped entity to the UNAMBIGUOUS base
    referent of its name (node identity, not name), which the `@?h` read dereferences through.

    GRAMMAR-ROUTE token/entity duality (the derivation-frame identity boundary): a name like `door1` may
    resolve to a base TOKEN *and* a base ENTITY it `denotes` — that is ONE identity, not two. So the base
    candidates are collapsed by `chain._canon_class` (the denotes-coref class): unambiguous iff they form a
    SINGLE class, and the scoped copy links to a representative (the class union lets the base read find the
    entity's content whichever member it binds). Two GENUINELY-disjoint same-name base entities still refuse
    (disambiguation preserved)."""
    from .chain import _canon_class
    for n in [x for x in g.nodes() if scope_of(g, x) is not None and g.name(x)]:
        if any(g.has_key(r, DENOTES) and scope_of(g, o) is None for r, o in g.relations_from(n)):
            continue
        base = [b for b in g.nodes_named(g.name(n)) if scope_of(g, b) is None]
        if not base:
            continue
        # The representative is the base node with the LARGEST canonical class — the established discourse
        # entity that every token/coref-mention denotes into (a fresh query token `door1` has a small class;
        # the entity carrying the facts has the whole coref cloud). Unambiguous iff EVERY base candidate is
        # in that class (else two genuinely-disjoint same-name entities → refuse). Links to the content-
        # bearing entity, which the `@?h` read's base check then reads.
        rep = max(base, key=lambda b: len(_canon_class(g, b)))
        rep_cls = _canon_class(g, rep)
        if all(b in rep_cls for b in base):
            g.add_relation(n, DENOTES, rep)


def _base_ref(g: AttrGraph, node: str) -> str | None:
    if scope_of(g, node) is None:
        return node
    for rel, obj in g.relations_from(node):
        if g.has_key(rel, DENOTES) and scope_of(g, obj) is None:
            return obj
    return None


def _held_scopes(g: AttrGraph, banded: bool) -> list[str]:
    """The scope ids with a `holds_base` verdict — read BANDED when the policy is banded (a banded verdict is
    a FORK a crisp read would miss)."""
    ms = _facts_matching(g, "holds_base", None, None, bands=banded)
    out = []
    for row in ms:
        s = row[0]
        if isinstance(s, ById):
            out.append(s.node_id)
    return out


def materialize_held(g: AttrGraph, *, banded: bool = False) -> int:
    """The generic 'materialize base referent on cross' mechanism (audit §5 primitive ③/④): for every scope
    that HOLDS in base, ensure each member participant has a base referent (mint + `denotes` if absent,
    reuse if present). Content-blind — no domain logic. Returns the number of referents minted. A follow-on
    folds this into a reactive skolem-minting rule."""
    minted = 0
    held = _held_scopes(g, banded)
    for sc in held:
        for ent in [n for n in g.nodes() if scope_of(g, n) == sc]:
            for rel, obj in list(g.relations_from(ent)):
                if g.is_control(rel) or g.is_inert(rel) or g.has_key(rel, DENOTES):
                    continue
                for node in (ent, obj):
                    if scope_of(g, node) is not None and _base_ref(g, node) is None:
                        g.add_relation(node, DENOTES, g.add_node({NAME: valued(g.name(node))}))
                        minted += 1
    return minted


def _scope_nodes(g: AttrGraph) -> set[str]:
    """Every scope node (the target of some `<under>` edge — a node with members born under it)."""
    return {sc for n in g.nodes() if (sc := scope_of(g, n)) is not None}


def _causal_scopes(g: AttrGraph) -> set[str]:
    """The SCOPE nodes that are an endpoint of a base `causes` fact — the ONLY scopes causation may cross.
    Filters out entity-level `causes` (`hunger causes aggression`, whose endpoints are not scopes) and
    leaves non-causal scope-tree scopes (an attribution `John says …`, an isolation-test scope) untouched:
    causation promotes its consequent, it does not blanket-promote every scoped fact that holds in base."""
    scopes = _scope_nodes(g)
    out: set[str] = set()
    for a, b in _facts_matching(g, "causes", None, None):
        for ep in (a, b):
            nid = ep.node_id if isinstance(ep, ById) else (g.nodes_named(ep) or [None])[0]
            if nid in scopes:
                out.add(nid)
    return out


def _members(g: AttrGraph, scope: str):
    """The `(subj, pred, obj)` member relations born under `scope` (skips `<under>`/`denotes`/control)."""
    for ent in [n for n in g.nodes() if scope_of(g, n) == scope]:
        for rel, obj in list(g.relations_from(ent)):
            if g.is_control(rel) or g.is_inert(rel) or g.has_key(rel, DENOTES):
                continue
            yield ent, g.predicate(rel), obj


def _promote_held(g: AttrGraph, promote_g, *, policy=None) -> None:
    """Write every HELD scope's members to BASE (dereferenced), by demanding each member's base fact through
    the promote rule (`?s ?p ?o when ?scope holds_base yes and ?s ?p ?o @?scope`). Interleaving this in the
    fixpoint is what lets links CHAIN: a promoted consequent is a base fact the next link's reify reads.
    Under a BANDED `policy` the demand carries the band the antecedent rode in on (DEGREE composition — a
    hedged antecedent promotes a banded consequent)."""
    held = _held_scopes(g, bool(policy is not None and policy.banded))
    for sc in held:
        for ent, p, obj in _members(g, sc):
            bs, bo = _base_ref(g, ent), _base_ref(g, obj)
            if bs is not None and bo is not None:
                chain_sip(g, (p, ById(bs), ById(bo)), rules=promote_g, policy=policy)


def resolve_crossings(g: AttrGraph, rules=None, *, policy=None, max_passes: int = 8) -> None:
    """Drive every CAUSAL crossing to a fixpoint: reconcile → DECIDE (demand `holds_base` for the scopes in a
    `causes` link, so reify + causal MP run) → MATERIALIZE base referents for newly-held scopes → PROMOTE
    held members to base. Repeat until stable (a promotion can satisfy another antecedent — so links CHAIN).
    Leaves every crossed proposition as an ordinary base fact, so a plain query answers it. NO-OP when the
    graph has no causal scope link — an attribution / isolation scope is never touched.

    DEGREE composition: under a BANDED `policy` the reify/MP/promote demands run banded, so a hedged
    antecedent's band rides `holds_base` (min t-norm through MP) into a banded consequent fork."""
    causal = _causal_scopes(g)
    if not causal:
        return
    rules = rules if rules is not None else decide_rules()
    from .cnl.query import _reify_rules
    rule_g = _reify_rules(rules)
    promote_g = _reify_rules(promote_rules())
    banded = bool(policy is not None and policy.banded)
    prev = -1
    for _ in range(max_passes):
        reconcile_scopes(g)
        for sc in _causal_scopes(g):
            chain_sip(g, ("holds_base", ById(sc), "yes"), rules=rule_g, policy=policy)
        materialize_held(g, banded=banded)
        _promote_held(g, promote_g, policy=policy)
        now = len(_held_scopes(g, banded))
        if now == prev:                                        # fixpoint: no new scope crossed this pass
            break
        prev = now

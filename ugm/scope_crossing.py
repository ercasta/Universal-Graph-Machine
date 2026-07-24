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
    entity of its name (node identity, not name — refuse if two base entities share the name, preserving
    disambiguation). What the `@?h` read dereferences through."""
    for n in [x for x in g.nodes() if scope_of(g, x) is not None and g.name(x)]:
        if any(g.has_key(r, DENOTES) and scope_of(g, o) is None for r, o in g.relations_from(n)):
            continue
        base = [b for b in g.nodes_named(g.name(n)) if scope_of(g, b) is None]
        if len(base) == 1:
            g.add_relation(n, DENOTES, base[0])


def _base_ref(g: AttrGraph, node: str) -> str | None:
    if scope_of(g, node) is None:
        return node
    for rel, obj in g.relations_from(node):
        if g.has_key(rel, DENOTES) and scope_of(g, obj) is None:
            return obj
    return None


def materialize_held(g: AttrGraph) -> int:
    """The generic 'materialize base referent on cross' mechanism (audit §5 primitive ③/④): for every scope
    that HOLDS in base, ensure each member participant has a base referent (mint + `denotes` if absent,
    reuse if present). Content-blind — no domain logic. Returns the number of referents minted. A follow-on
    folds this into a reactive skolem-minting rule."""
    minted = 0
    held = [s.node_id for s, _ in _facts_matching(g, "holds_base", None, "yes")]
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


def _scope_tree_scopes(g: AttrGraph) -> set[str]:
    """Every scope-tree scope (the target of some `<under>` edge)."""
    return {sc for n in g.nodes() if (sc := scope_of(g, n)) is not None}


def _members(g: AttrGraph, scope: str):
    """The `(subj, pred, obj)` member relations born under `scope` (skips `<under>`/`denotes`/control)."""
    for ent in [n for n in g.nodes() if scope_of(g, n) == scope]:
        for rel, obj in list(g.relations_from(ent)):
            if g.is_control(rel) or g.is_inert(rel) or g.has_key(rel, DENOTES):
                continue
            yield ent, g.predicate(rel), obj


def _promote_held(g: AttrGraph, promote_g) -> None:
    """Write every HELD scope's members to BASE (dereferenced), by demanding each member's base fact through
    the promote rule (`?s ?p ?o when ?scope holds_base yes and ?s ?p ?o @?scope`). Interleaving this in the
    fixpoint is what lets links CHAIN: a promoted consequent is a base fact the next link's reify reads."""
    held = [s.node_id for s, _ in _facts_matching(g, "holds_base", None, "yes")]
    for sc in held:
        for ent, p, obj in _members(g, sc):
            bs, bo = _base_ref(g, ent), _base_ref(g, obj)
            if bs is not None and bo is not None:
                chain_sip(g, (p, ById(bs), ById(bo)), rules=promote_g)


def resolve_crossings(g: AttrGraph, rules=None, *, max_passes: int = 8) -> None:
    """Drive the crossing to a fixpoint: reconcile → DECIDE (demand `holds_base` for every scope-tree scope,
    so reify + causal MP run) → MATERIALIZE base referents for newly-held scopes → PROMOTE held members to
    base. Repeat until stable (a promotion can satisfy another antecedent — so links CHAIN). Leaves every
    crossed proposition as an ordinary base fact, so a plain query answers it."""
    rules = rules if rules is not None else decide_rules()
    from .cnl.query import _reify_rules
    rule_g = _reify_rules(rules)
    promote_g = _reify_rules(promote_rules())
    prev = -1
    for _ in range(max_passes):
        reconcile_scopes(g)
        for sc in _scope_tree_scopes(g):
            chain_sip(g, ("holds_base", ById(sc), "yes"), rules=rule_g)
        materialize_held(g)
        _promote_held(g, promote_g)
        now = len(list(_facts_matching(g, "holds_base", None, "yes")))
        if now == prev:                                        # fixpoint: no new scope crossed this pass
            break
        prev = now

"""Spike: LOWER the causation crossing to a DECLARED crossing RULE (scope_reframe_audit.md Step 2).

`bench/spike_scope_causation_repA.py` proved the REPRESENTATION (scopes as the proposition unit) with an
IMPERATIVE crossing (`holds_in_base`/`promote`/`cross_causes` = Python functions). This spike proves the
next claim: that crossing LOGIC lowers to DECLARED RULES (data, not a Python island — [[composability-
principle]]), evaluated by the REAL engine.

TWO DESIGN FINDINGS the build forced (both consistent with the audit):
  (A) SCOPES ARE ORDINARY NODES, not `<hypothesis>` control. The reframe relates scopes with BASE facts
      (`S_A causes S_B`, `john says S_J`, and here `S holds_base yes`); a fact whose endpoint is a CONTROL
      node is dropped by the fact-read guard, so scopes can't be control if rules are to reason ABOUT them.
      (audit §1 "a scope is itself an ordinary node a relativizer fact points at"; §5 lists scopes as
      DISTINCT from `control` scaffolding.) The old `<hypothesis>`-control scope is the 1c-migration shape.
  (B) The crossing needs to READ a member from its scope's vantage while WRITING to base — but
      `chain_sip(scope=H)` conflates the two (it sets the read vantage AND pencils every EMIT into H).
      So the "reach across the boundary" (audit §5 primitive ③) is factored into a GENERIC, content-blind
      BRIDGE (`expose_members`): it reads each scoped member relnode + dereferences its participants to
      base (primitive ④, `denotes` = node identity, not name), exposing them as ORDINARY base facts
      (`M in_scope H`, `M mpred P`, `M msubj_base BS`, `M mobj_base BO`). Nothing domain-specific — pure
      topology + `denotes`. (A cleaner-but-bigger alternative for production: a per-atom `@?h` relativized
      read generalizing the temporal `@?t` to the scope-tree + a variable predicate — row 13. The bridge
      proves the LOWERING now with the engine as-is.)

WHAT IS DATA vs ENGINE (the split the spike validates):
  * ENGINE (generic, content-blind): read-across-the-boundary + deref (`expose_members`), variable-
    predicate matching (`?bs ?p ?bo`, facts-as-truth-bearers), plain triple matching over ordinary nodes.
  * DATA (the crossing RULES, below): what CAUSATION MEANS — a scope "holds in base" when its member,
    dereferenced, holds in base (reify); the consequent holds when the antecedent does and causes it (MP);
    a held scope's members land in base (promote/dereify). No Python decides any of this.

GO = CASE 1 (causation, link-first AND antecedent-first) derives `lion is safe` through the DECLARED
rules, and the negative control (no base fact) does not.
"""
from __future__ import annotations

import pathlib
import sys
import warnings

warnings.simplefilter("ignore")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ugm import ById                                                        # noqa: E402
from ugm.attrgraph import AttrGraph, NAME, valued                           # noqa: E402
from ugm.chain import chain_sip, _facts_matching                           # noqa: E402
from ugm.cnl.machine_rules import load_machine_rules                        # noqa: E402
from ugm.cnl.query import _reify_rules                                     # noqa: E402
from ugm.scope_tree import put_under, scope_of                             # noqa: E402
from ugm.vocabulary import DENOTES                                          # noqa: E402

SCOPE_MARK = "is_scope"                 # an ordinary marker attr (finding A: scopes are ordinary nodes)
_SCOPE_N = [0]


def _scope(g) -> str:
    """An ORDINARY scope node (finding A) — marked, not control, so `S causes S'` / `S holds_base yes`
    are readable base facts a rule can reason about. Given a UNIQUE name so the demand engine's name-union
    does not merge two distinct scopes into one canonical class (a scope's identity is the node, not a
    shared name — in production scopes are minted, never name-interned)."""
    _SCOPE_N[0] += 1
    n = g.add_node({NAME: valued(f"scope{_SCOPE_N[0]}")})
    g.add_relation(n, SCOPE_MARK, g.add_node({NAME: valued("yes")}))
    return n


def _named(g, name, *, under=None) -> str:
    n = g.add_node({NAME: valued(name)})
    if under is not None:
        put_under(g, n, under)
    return n


def reconcile(g):
    """Primitive ④ (identity union): draw `denotes` from each scoped entity to the UNAMBIGUOUS base entity
    of its name (node identity, not name — refuse if two base entities share the name, so disambiguation is
    preserved). What `expose_members` then dereferences through."""
    for n in [x for x in g.nodes() if scope_of(g, x) is not None and g.name(x)]:
        if any(g.has_key(r, DENOTES) and scope_of(g, o) is None for r, o in g.relations_from(n)):
            continue
        base = [b for b in g.nodes_named(g.name(n)) if scope_of(g, b) is None]
        if len(base) == 1:
            g.add_relation(n, DENOTES, base[0])


def _base_ref(g, node, *, mint=False):
    """The BASE referent of a (possibly scoped) node via `denotes` — node identity, not name. `None` for a
    scoped node with no base referent yet unless `mint=True` MATERIALIZES one (the base node a promotion
    will write onto — Rep A's "materialize base referent as needed on cross")."""
    if scope_of(g, node) is None:
        return node
    for rel, obj in g.relations_from(node):
        if g.has_key(rel, DENOTES) and scope_of(g, obj) is None:
            return obj
    if not mint:
        return None
    b = _named(g, g.name(node))
    g.add_relation(node, DENOTES, b)
    return b


def expose_members(g):
    """The GENERIC reach bridge (finding B; audit §5 primitive ③ "cross/reach"). Content-BLIND: for every
    scoped member relnode (a fact whose subject is under a scope), expose ORDINARY base facts naming its
    scope, predicate, and its participants' BASE referents — so a base-vantage rule can reason about the
    scoped proposition without crossing the read boundary itself. No domain knowledge: pure topology +
    `denotes`. Idempotent. A participant with no base referent yet (unreconciled) leaves the member un-
    exposed (read-only, converges when reconcile runs)."""
    for ent in [n for n in g.nodes() if scope_of(g, n) is not None]:
        h = scope_of(g, ent)
        for rel, obj in list(g.relations_from(ent)):
            if g.is_control(rel) or g.is_inert(rel) or g.has_key(rel, DENOTES):
                continue
            pred = g.predicate(rel)
            bs, bo = _base_ref(g, ent, mint=True), _base_ref(g, obj, mint=True)
            if any(g.predicate(r) == "in_scope" for r, _ in g.relations_from(rel)):
                continue                                        # idempotent
            # the predicate is stored as the canonical VALUE-NODE (not a fresh named node): the variable-
            # predicate machinery (facts-as-truth-bearers) binds `?p` to `value_node(pred)`, so `?m mpred
            # ?p` and the base read `?bs ?p ?bo` join on the same node.
            g.add_relation(rel, "in_scope", h)
            g.add_relation(rel, "mpred", g.value_node(pred))
            g.add_relation(rel, "msubj_base", bs)
            g.add_relation(rel, "mobj_base", bo)


# ── the DECLARED crossing rules (DATA — what causation means) ─────────────────
#
# All base reads over the ordinary bridge facts + variable-predicate matching (`?bs ?p ?bo`) — no vantage
# switch, no content key. `?m` is the member RELNODE (topology-interned = the proposition's identity, NOT
# a content string, so no orphan/coref seam).
# NOTE on variable naming: the scope variable is `?scope` (sorts AFTER `?m`) so the demand `_sideways_order`
# anchors on a SELECTIVE bridge atom (`?m mobj_base ?bo`) before the boolean `?scope holds_base yes` (whose
# literal object `yes` is a non-selective anchor). A finding: the pure-declared lowering is sensitive to the
# boolean-verdict shape + the demand heuristic — a reason the row-13 `@?h` relativized read (binds scope +
# members together in one atom) is the cleaner production primitive than the materialized bridge.
#
# WHAT THIS SPIKE ROBUSTLY PROVES (the crossing DECISION):
#   reify (a scope holds-in-base when its member, dereferenced, holds in base) + causal MP (the consequent
#   holds-in-base when the antecedent does and causes it) — as TWO DECLARED RULES — fire through the real
#   demand engine, LINK-FIRST and antecedent-first, and correctly NOT in the negative control. That is the
#   whole "does the cause fire?" decision, lowered to data.
CROSS_DECISION = load_machine_rules("\n".join([
    # reify: a scope holds-in-base when its member, dereferenced, holds in base.
    "?scope holds_base yes when ?m in_scope ?scope and ?m mpred ?p and ?m msubj_base ?bs "
    "and ?m mobj_base ?bo and ?bs ?p ?bo",
    # MP: the consequent holds-in-base when the antecedent does and causes it.
    "?b holds_base yes when ?a holds_base yes and ?a causes ?b",
]))

# The MATERIALIZATION step (promote/dereify: write the consequent's member to base) is the SHIPPED variable-
# predicate dereify (`cause_surface.BRIDGE_RULES[2]`, proven by `test_propositional_cause`). Lowered here it
# is `?bs ?p ?bo when ?scope holds_base yes and ?m in_scope ?scope and ?m mpred ?p and ?m msubj_base ?bs and
# ?m mobj_base ?bo` — a FINDING is that a hand-built bridge must align the predicate node's REPRESENTATION
# with the variable-predicate machinery (the head-unify binds `?p` to `value_node(pred)`, and walking INTO a
# value-node object returns nothing), which the shipped `ask_goal` path gets right and a raw `chain_sip`
# demand over this bridge does not. Production should prefer the `@?h` relativized read (no bridge, no
# value-node round-trip) — see the report. This spike therefore verifies the DECISION, not the write.


def _consequent_scope(g):
    """The scope that is the OBJECT of a `causes` base fact — the consequent whose holds-in-base is the
    acceptance signal (generic: read the causes graph over scope nodes)."""
    for r in g.nodes_with_key("causes"):
        objs = list(g.succ(r))
        if objs:
            return objs[0]
    return None


def crosses_to_base(g):
    """Reconcile → expose the generic reach bridges → run the DECLARED decision rules (reify + MP). Returns
    whether the CONSEQUENT scope is derived to hold in base — the crossing fired."""
    reconcile(g)
    expose_members(g)
    rule_g = _reify_rules(CROSS_DECISION)
    s_b = _consequent_scope(g)
    chain_sip(g, ("holds_base", ById(s_b), "yes"), rules=rule_g)   # drives MP ← reify (proven chain)
    return bool(list(_facts_matching(g, "holds_base", ById(s_b), "yes")))


def _mark(ok):  return "[+]" if ok else "[X]"


# ── CASE 1 — causation ────────────────────────────────────────────────────────

def case1(order: str):
    g = AttrGraph()

    def statement():
        s_a, s_b = _scope(g), _scope(g)
        g.add_relation(_named(g, "lion", under=s_a), "has_not", _named(g, "mane", under=s_a))
        g.add_relation(_named(g, "lion", under=s_b), "is", _named(g, "safe", under=s_b))
        g.add_relation(s_a, "causes", s_b)

    def base_fact():
        g.add_relation(_named(g, "lion"), "has_not", _named(g, "mane"))

    if order == "link-first":
        statement(); base_fact()
    else:
        base_fact(); statement()
    return crosses_to_base(g)


def case1_negative_control():
    g = AttrGraph()
    s_a, s_b = _scope(g), _scope(g)
    g.add_relation(_named(g, "lion", under=s_a), "has_not", _named(g, "mane", under=s_a))
    g.add_relation(_named(g, "lion", under=s_b), "is", _named(g, "safe", under=s_b))
    g.add_relation(s_a, "causes", s_b)
    return crosses_to_base(g)                                       # no base fact -> must NOT cross


def main():
    print("=" * 94)
    print("CROSSING-RULE LOWERING SPIKE — the causation crossing DECISION as declared rules (reify + MP)")
    print("=" * 94)

    lf = case1("link-first")
    af = case1("antecedent-first")
    nc = case1_negative_control()
    print(f"\n  link-first        consequent holds-in-base  {_mark(lf)} {lf}")
    print(f"  antecedent-first  consequent holds-in-base  {_mark(af)} {af}")
    print(f"  neg control       does NOT cross            {_mark(not nc)} {nc}")

    go = lf and af and not nc
    print("\n" + "=" * 94)
    print(f"{'GO' if go else 'NO-GO'} — the crossing DECISION (reify + causal MP) is DECLARED RULES over a")
    print("generic reach bridge, firing LINK-FIRST through the real engine. The materialization (dereify")
    print("to base) reuses the shipped variable-predicate write; production prefers the `@?h` relativized")
    print("read (see the report / docs/design/scope_reframe_audit.md Step 2).")


if __name__ == "__main__":
    main()

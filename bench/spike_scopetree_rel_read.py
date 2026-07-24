"""Spike: the SCOPE-TREE relativized read `@?h` — the load-bearing Step-2 primitive (row 13).

The crossing-decision spike (`spike_crossing_rule_lowering.py`) got a GO but found the materialized reach
BRIDGE fragile (value-node round-trips, `_sideways_order` boolean-verdict sensitivity) and concluded
production should prefer the `@?h` relativized read. This spike DE-RISKS that: it generalizes the temporal
`@?t` relativized read to the SCOPE-TREE (`ugm/chain._relativized_st_matching`, additive + gated by
`reframe_active`) so ONE atom `?s ?p ?o @?h` reaches into a scope and binds (subject, PREDICATE, object,
scope) TOGETHER — with the participants ALREADY DEREFERENCED to base (the crossing dereferences, audit §5
primitive ④). The crossing then needs NO bridge, NO content-key handle, NO value-node round-trip: reify is
a single clean declared rule read through the REAL `chain_sip`.

  reify:  ?scope holds_base yes  when  ?s ?p ?o @?scope  and  ?s ?p ?o
          └ reach into ?scope; bind base s/p/o + the scope ┘   └ does it hold in BASE? ┘
  MP:     ?b holds_base yes      when  ?a holds_base yes  and  ?a causes ?b

GO = CASE 1 (causation) derives the consequent scope's holds-in-base LINK-FIRST and antecedent-first,
through the declared rules + `@?scope` read, with the negative control (no base fact) NOT crossing. The
promote/materialization (writing the consequent to base) is the shipped variable-predicate dereify + a
base-referent mint — out of scope here; this spike proves the READ that makes the decision a clean rule.
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
from ugm.cnl.query import _reify_rules, ask_goal                           # noqa: E402
from ugm.scope_tree import put_under, scope_of                             # noqa: E402
from ugm.vocabulary import DENOTES                                          # noqa: E402

_SCOPE_N = [0]


def _scope(g) -> str:
    """An ORDINARY scope node (a fact between scopes / `S holds_base yes` must be readable), uniquely named
    so the demand engine's name-union never merges two scopes."""
    _SCOPE_N[0] += 1
    return g.add_node({NAME: valued(f"scope{_SCOPE_N[0]}")})


def _named(g, name, *, under=None) -> str:
    n = g.add_node({NAME: valued(name)})
    if under is not None:
        put_under(g, n, under)
    return n


def reconcile(g):
    """Identity union (primitive ④): draw `denotes` from each scoped entity to the UNAMBIGUOUS base entity
    of its name — what the `@?h` read dereferences through."""
    for n in [x for x in g.nodes() if scope_of(g, x) is not None and g.name(x)]:
        if any(g.has_key(r, DENOTES) and scope_of(g, o) is None for r, o in g.relations_from(n)):
            continue
        base = [b for b in g.nodes_named(g.name(n)) if scope_of(g, b) is None]
        if len(base) == 1:
            g.add_relation(n, DENOTES, base[0])


# ── the DECLARED crossing rules ───────────────────────────────────────────────
# DECIDE — reify (base case) + causal MP: which scopes hold in base. `holds_base(scope)` is the UNIVERSAL
# "this scope's content is true in base" verdict; per-relativizer rules derive it (causation = MP; a
# trusted-holder attribution rule would derive it the same way). All DATA.
CROSS = load_machine_rules("\n".join([
    "?scope holds_base yes when ?s ?p ?o @?scope and ?s ?p ?o",
    "?b holds_base yes when ?a holds_base yes and ?a causes ?b",
]))
# PROMOTE — the uniform materialization: a held scope's members ARE true in base. `?s ?p ?o @?scope` yields
# the member DEREFERENCED to base (post-materialize), and the variable-predicate head writes it. One rule,
# relativizer-agnostic — the meaning lived entirely in what derived `holds_base`.
PROMOTE = load_machine_rules("?s ?p ?o when ?scope holds_base yes and ?s ?p ?o @?scope")


def _consequent_scope(g):
    for r in g.nodes_with_key("causes"):
        objs = list(g.succ(r))
        if objs:
            return objs[0]
    return None


def _base_ref(g, node):
    if scope_of(g, node) is None:
        return node
    for rel, obj in g.relations_from(node):
        if g.has_key(rel, DENOTES) and scope_of(g, obj) is None:
            return obj
    return None


def materialize(g):
    """The generic 'materialize base referent on cross' mechanism (audit §5 primitive ③/④): for every scope
    that HOLDS in base, ensure each member participant has a base referent (mint + `denotes` if absent, reuse
    if present). Content-blind — no domain logic. This is the ONE non-rule step; production folds it into a
    reactive skolem-minting rule (which needs the `denotes`-visibility exemption — a follow-on)."""
    held = [s.node_id for s, _ in _facts_matching(g, "holds_base", None, "yes")]
    for sc in held:
        for ent in [n for n in g.nodes() if scope_of(g, n) == sc]:
            for rel, obj in list(g.relations_from(ent)):
                if g.is_control(rel) or g.is_inert(rel) or g.has_key(rel, DENOTES):
                    continue
                for node in (ent, obj):
                    if scope_of(g, node) is not None and _base_ref(g, node) is None:
                        g.add_relation(node, DENOTES, _named(g, g.name(node)))


def crosses_to_base(g):
    reconcile(g)
    s_b = _consequent_scope(g)
    chain_sip(g, ("holds_base", ById(s_b), "yes"), rules=_reify_rules(CROSS))
    return bool(list(_facts_matching(g, "holds_base", ById(s_b), "yes")))


def answer(g, s, p, o):
    """End-to-end: DECIDE (reify + MP) → MATERIALIZE base referents for held scopes → PROMOTE (the query
    demand drives the promote rule, which reads held members via `@?scope` and writes them to base)."""
    reconcile(g)
    s_b = _consequent_scope(g)
    chain_sip(g, ("holds_base", ById(s_b), "yes"), rules=_reify_rules(CROSS))   # decide
    materialize(g)                                                              # mint base refs
    return ask_goal(g, ("yesno", s, p, o), list(PROMOTE))                       # promote answers the query


def _mark(ok):  return "[+]" if ok else "[X]"


# ── CASE 1 — causation ────────────────────────────────────────────────────────

def _case(order: str, base: bool):
    g = AttrGraph()

    def statement():
        s_a, s_b = _scope(g), _scope(g)
        g.add_relation(_named(g, "lion", under=s_a), "has_not", _named(g, "mane", under=s_a))
        g.add_relation(_named(g, "lion", under=s_b), "is", _named(g, "safe", under=s_b))
        g.add_relation(s_a, "causes", s_b)

    def base_fact():
        g.add_relation(_named(g, "lion"), "has_not", _named(g, "mane"))

    if order == "link-first":
        statement()
        if base:
            base_fact()
    else:
        if base:
            base_fact()
        statement()
    return g


def main():
    print("=" * 94)
    print("SCOPE-TREE `@?h` RELATIVIZED READ SPIKE — the crossing as declared rules, end to end")
    print("=" * 94)

    # DECISION (reify + MP): does the consequent scope hold in base?
    lf = crosses_to_base(_case("link-first", base=True))
    af = crosses_to_base(_case("antecedent-first", base=True))
    nc = crosses_to_base(_case("link-first", base=False))
    print("\n-- crossing DECISION (holds_base derived through reify + causal MP) " + "-" * 24)
    print(f"  link-first        consequent holds-in-base  {_mark(lf)} {lf}")
    print(f"  antecedent-first  consequent holds-in-base  {_mark(af)} {af}")
    print(f"  neg control       does NOT cross            {_mark(not nc)} {nc}")

    # END TO END: does `lion is safe` become true in base (decide → materialize → promote)?
    e_lf = answer(_case("link-first", base=True), "lion", "is", "safe")
    e_af = answer(_case("antecedent-first", base=True), "lion", "is", "safe")
    e_nc = answer(_case("link-first", base=False), "lion", "is", "safe")
    print("\n-- END TO END (`ask lion is safe`: decide -> materialize -> promote) " + "-" * 23)
    print(f"  link-first        {_mark(e_lf == ['yes'])} {e_lf}")
    print(f"  antecedent-first  {_mark(e_af == ['yes'])} {e_af}")
    print(f"  neg control       {_mark(e_nc != ['yes'])} {e_nc}")

    go = (lf and af and not nc and e_lf == ["yes"] and e_af == ["yes"] and e_nc != ["yes"])
    print("\n" + "=" * 94)
    print(f"{'GO' if go else 'NO-GO'} — the causation crossing is DECLARED RULES end to end: `@?h` reify +")
    print("causal MP DECIDE (data), a generic materialize copies held members to base, PROMOTE reads via")
    print("`@?scope` and writes — `lion is safe` becomes true in base LINK-FIRST, no bridge, no handle.")


if __name__ == "__main__":
    main()

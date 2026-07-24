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
from ugm.cnl.query import _reify_rules                                     # noqa: E402
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


# ── the DECLARED crossing rules — ONE clean reify over `@?scope`, plus causal MP ──────────────
CROSS = load_machine_rules("\n".join([
    "?scope holds_base yes when ?s ?p ?o @?scope and ?s ?p ?o",
    "?b holds_base yes when ?a holds_base yes and ?a causes ?b",
]))


def _consequent_scope(g):
    for r in g.nodes_with_key("causes"):
        objs = list(g.succ(r))
        if objs:
            return objs[0]
    return None


def crosses_to_base(g):
    reconcile(g)
    rule_g = _reify_rules(CROSS)
    s_b = _consequent_scope(g)
    chain_sip(g, ("holds_base", ById(s_b), "yes"), rules=rule_g)
    return bool(list(_facts_matching(g, "holds_base", ById(s_b), "yes")))


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
    return crosses_to_base(g)


def main():
    print("=" * 94)
    print("SCOPE-TREE `@?h` RELATIVIZED READ SPIKE — the crossing as ONE clean declared rule")
    print("=" * 94)

    lf = _case("link-first", base=True)
    af = _case("antecedent-first", base=True)
    nc = _case("link-first", base=False)
    print(f"\n  link-first        consequent holds-in-base  {_mark(lf)} {lf}")
    print(f"  antecedent-first  consequent holds-in-base  {_mark(af)} {af}")
    print(f"  neg control       does NOT cross            {_mark(not nc)} {nc}")

    go = lf and af and not nc
    print("\n" + "=" * 94)
    print(f"{'GO' if go else 'NO-GO'} — `?s ?p ?o @?scope` reaches into a scope, binds base s/p/o + the")
    print("scope, and the crossing is ONE declared rule through the real engine (no bridge, no handle).")


if __name__ == "__main__":
    main()

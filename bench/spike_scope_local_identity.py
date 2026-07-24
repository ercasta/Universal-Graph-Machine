"""Spike: is IDENTITY UNION SCOPE-LOCAL? (scope_reframe_audit.md point 1 / Trap A, 2026-07-24)

THE DECISION UNDER TEST. Under the scope reframe, a scoped fact is born UNDER a relativizer scope
(`John says …`, `under H`, `at T`) and reached only by CROSSING; a reference to an entity denotes the
base entity by an IDENTITY link so coreference still works. Trap A: that identity link must NOT also grant
VISIBILITY — a base read of `lion` must not pull in facts asserted only inside `John says …`, or isolation
is gone. The proposed rule: **`_canon_class` unions two nodes only when they are CO-SCOPED; across a
relativizer boundary identity holds but facts do not flow.**

THE CRUX A SPIKE MUST RESOLVE (can't be settled by reasoning). Today `_canon_class` unions GLOBALLY via
`denotes`, and the DERIVATION FRAME depends on it to fuse a surface TOKEN with its interpretation ENTITY
(docs/design/derivation_frame.md). If "scope-local" naively blocks EVERY cross-scope union it kills that.
So the question is whether scope-local union can (a) ISOLATE base from a relativizer scope while (b)
PRESERVING the token/entity fusion — which works iff the derivation frame operates WITHIN one scope (both
token and entity in base), so its union is intra-scope and a relativizer boundary is the only thing blocked.

MECHANISM. Isolate the union question with `ById` pins (which route through `_canon_class`, NOT the
same-name accelerator) and `denotes` as the identity link. `scope_of(node)` = the scope it is under
(attr `<under>`), or None for base. Monkeypatch `chain._canon_class` to a scope-local variant and compare
against the shipped global one on the SAME graph.

GO / NO-GO:
  CASE 1 (isolation)      — a fact under scope S does not leak to a BASE read (global LEAKS, scope-local
                            ISOLATES → assumed-no).
  CASE 2 (within-scope)   — reading FROM inside S still fuses the reference to its scoped content (coref
                            preserved within a scope).
  CASE 3 (crossing)       — an explicit base assertion (the promotion a crossing rule would make) is seen
                            by the base read (crossing works; isolation is not a wall).
  CASE 4 (NON-REGRESSION) — the derivation-frame token->entity fusion (both in BASE) STILL unions under
                            scope-local, so the shipped coref survives. THE decisive one.
"""
from __future__ import annotations

import pathlib
import sys
import warnings

warnings.simplefilter("ignore")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import ugm.chain as chain                                                  # noqa: E402
from ugm import ById                                                       # noqa: E402
from ugm.attrgraph import AttrGraph, NAME, valued, graded                  # noqa: E402
from ugm.cnl.query import ask_goal                                         # noqa: E402
from ugm.vocabulary import DENOTES                                         # noqa: E402

UNDER = "<under>"                         # spike-local: the scope a node is born under (None = base)
_GLOBAL_CANON = chain._canon_class        # the shipped global-union reference


def _named(g: AttrGraph, name: str, *, under: str | None = None) -> str:
    n = g.add_node({NAME: valued(name)})
    if under is not None:
        g.set_attr(n, UNDER, valued(under))
    return n


def _scope_of(g: AttrGraph, node: str) -> str | None:
    a = g.get_attr(node, UNDER)
    return a.value if a is not None else None


def _scope_local_canon(active_scope):
    """A `_canon_class` that unions a node with a `denotes`-neighbour ONLY when they are CO-SCOPED with
    the ACTIVE reading scope — the reframe rule. `active_scope` is the vantage the read is taken from
    (None = base). A member in a DIFFERENT scope is dropped: identity holds, visibility does not."""
    def canon(fact_g: AttrGraph, node: str) -> set[str]:
        full = _GLOBAL_CANON(fact_g, node)                 # the shipped one-hop denotes class
        return {m for m in full if _scope_of(fact_g, m) == active_scope}
    return canon


def _ask(g: AttrGraph, subj_id: str, obj: str) -> list[str]:
    return ask_goal(g, ("yesno", ById(subj_id), "has", obj), [])


def _use(canon):
    chain._canon_class = canon


def _restore():
    chain._canon_class = _GLOBAL_CANON


def _mark(ok: bool) -> str:
    return "[+]" if ok else "[X]"


# ---------------------------------------------------------------------------

def build_scoped():
    """Base entity L (a lion) + a REFERENCE L' to it under scope S, with the scoped fact `L' has mane`.
    L' --denotes--> L is the identity link. mane is a shared base node (so the OBJECT matches by name and
    the only path to the scoped fact is the SUBJECT union L->L')."""
    g = AttrGraph()
    L = _named(g, "lion")                                  # base entity
    S = g.add_node({NAME: valued("<hypothesis>")}, control=True)
    Lp = _named(g, "lion", under=S)                        # a reference to the lion, born under S
    mane = _named(g, "mane")                               # shared base object
    g.add_relation(Lp, "has", mane)                        # the SCOPED fact: L' has mane
    g.add_relation(Lp, DENOTES, L)                         # identity: L' denotes L
    return g, L, Lp, S, mane


def build_token_entity():
    """The DERIVATION-FRAME shape, both in BASE: token T (name lion) --denotes--> entity E, and the fact
    `E has mane` lands on the ENTITY (as the grammar fold writes it). A read pinned to the TOKEN must fuse
    to the entity to see the fact — the shipped coref that scope-local union must NOT break."""
    g = AttrGraph()
    T = _named(g, "lion")                                  # surface token
    E = _named(g, "lion")                                  # interpretation entity
    mane = _named(g, "mane")
    g.add_relation(T, DENOTES, E)                          # token denotes entity
    g.add_relation(E, "has", mane)                         # fact on the entity
    return g, T, E


def main() -> None:
    print("=" * 96)
    print("SCOPE-LOCAL IDENTITY UNION SPIKE — isolation vs derivation-frame coref (scope_reframe_audit §7.1)")
    print("=" * 96)

    # CASE 1 — isolation: base read of L must NOT see the fact under S.
    print("\n-- CASE 1: a fact under scope S must not leak to a BASE read " + "-" * 33)
    g, L, Lp, S, mane = build_scoped()
    _use(_GLOBAL_CANON)
    leak = _ask(g, L, "mane")
    _use(_scope_local_canon(active_scope=None))            # base vantage
    iso = _ask(g, L, "mane")
    _restore()
    print(f"  GLOBAL union      base sees scoped fact {_mark(leak == ['yes'])} {str(leak):16} (want yes = the LEAK)")
    print(f"  SCOPE-LOCAL union base isolated          {_mark(iso != ['yes'])} {str(iso):16} (want NOT yes)")
    case1 = leak == ["yes"] and iso != ["yes"]

    # CASE 2 — within-scope: reading FROM S, the reference fuses to its content.
    print("\n-- CASE 2: reading from INSIDE S still fuses the reference to its content " + "-" * 20)
    g, L, Lp, S, mane = build_scoped()
    _use(_scope_local_canon(active_scope=S))               # vantage = inside S
    within = _ask(g, Lp, "mane")
    _restore()
    print(f"  in-scope read of L' sees `L' has mane`   {_mark(within == ['yes'])} {within}")
    case2 = within == ["yes"]

    # CASE 3 — crossing: an explicit base assertion (what a promotion rule writes) is seen by base.
    print("\n-- CASE 3: crossing — a promoted base fact IS seen by the base read " + "-" * 26)
    g, L, Lp, S, mane = build_scoped()
    g.add_relation(L, "has", mane)                         # the promotion: `lion has mane` in BASE
    _use(_scope_local_canon(active_scope=None))
    crossed = _ask(g, L, "mane")
    _restore()
    print(f"  base read after promotion                {_mark(crossed == ['yes'])} {crossed}")
    case3 = crossed == ["yes"]

    # CASE 4 — NON-REGRESSION: token->entity fusion (both base) survives scope-local union.
    print("\n-- CASE 4: derivation-frame token->entity coref survives (THE decisive one) " + "-" * 17)
    g, T, E = build_token_entity()
    _use(_GLOBAL_CANON)
    shipped = _ask(g, T, "mane")
    _use(_scope_local_canon(active_scope=None))
    reframed = _ask(g, T, "mane")
    _restore()
    print(f"  GLOBAL (shipped)  token read fuses entity {_mark(shipped == ['yes'])} {shipped}")
    print(f"  SCOPE-LOCAL       token read fuses entity {_mark(reframed == ['yes'])} {reframed} (must stay yes)")
    case4 = shipped == ["yes"] and reframed == ["yes"]

    print("\n" + "=" * 96)
    go = case1 and case2 and case3 and case4
    print(f"CASE 1 isolation {_mark(case1)}   CASE 2 within-scope {_mark(case2)}   "
          f"CASE 3 crossing {_mark(case3)}   CASE 4 non-regression {_mark(case4)}")
    print(f"\n{'GO' if go else 'NO-GO'} — scope-local union "
          f"{'isolates base from a relativizer scope WHILE preserving token/entity fusion.' if go else 'FAILED a case; read the marks.'}")


if __name__ == "__main__":
    main()

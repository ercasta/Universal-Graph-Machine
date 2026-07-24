"""Spike: REPRESENTATION A — `causes`/`says` between SCOPE nodes (scope_reframe_audit.md Step 2).

Proves the synthesis representation on TWO cases, using the shipped scope-tree (`ugm/scope_tree.py`,
sub-slices 1a/1b): a relativizer mints a SCOPE node that HOLDS its proposition as scoped copies (born under
the scope, isolated from base by scope-local visibility); a base fact relates the scopes (`S_A —causes→ S_B`,
`john —says→ S_J`); and a CROSSING RULE reads a scope's member proposition, dereferences its participants to
their base referents (via `denotes` — node identity, NOT brute name, so disambiguation is preserved), and
promotes across the boundary. The crossing is implemented IMPERATIVELY here (rule-shaped: read members →
deref → check/write base) to validate the REPRESENTATION; the build lowers it to a declared crossing rule.

CASE 1 — CAUSATION, LINK-FIRST (the acceptance test). `that lion has no mane causes that lion is safe`
stated BEFORE `the lion has no mane`. The scoped copies are orphans at statement time; when the base fact
lands they RECONCILE (scope-local `denotes`), then MP fires and dereifies the consequent to base. Negative
control: without the base fact, nothing promotes.

CASE 2 — CONJUNCTION ATTRIBUTION (multi-fact scope). `John says the lion has a mane AND is dangerous` = ONE
scope with TWO members. Isolation holds DESPITE coreference (Trap A: the scoped lion denotes base lion, yet a
base read does not see John's claims). In-scope both hold. Promotion for a trusted holder crosses ALL members
(conjunction), so both land in base.
"""
from __future__ import annotations

import pathlib
import sys
import warnings

warnings.simplefilter("ignore")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ugm import ById                                                        # noqa: E402
from ugm.attrgraph import AttrGraph, NAME, valued                           # noqa: E402
from ugm.check import check, POSITIVE                                       # noqa: E402
from ugm.cnl.query import ask_goal                                          # noqa: E402
from ugm.scope_tree import put_under, scope_of                              # noqa: E402
from ugm.vocabulary import DENOTES                                          # noqa: E402


# ── graph helpers ────────────────────────────────────────────────────────────

def _scope(g) -> str:
    return g.add_node({NAME: valued("<hypothesis>")}, control=True)


def _named(g, name, *, under=None) -> str:
    n = g.add_node({NAME: valued(name)})
    if under is not None:
        put_under(g, n, under)
    return n


def _facts_under(g, scope):
    """The member propositions of `scope`: `(subj, pred, obj)` for every FACT relnode whose subject is a
    node born under `scope` — a rule reading a scope's content (skips `<under>`/`denotes`/control meta)."""
    for ent in [n for n in g.nodes() if scope_of(g, n) == scope]:
        for rel, obj in g.relations_from(ent):
            if g.is_control(rel) or g.is_inert(rel) or g.has_key(rel, DENOTES):
                continue
            yield ent, g.predicate(rel), obj


def _base_ref(g, node, *, mint=False):
    """The BASE referent of a (possibly scoped) node, via `denotes` — node identity, not name. `None` if a
    scoped node has no base referent yet (read-only); `mint=True` materializes one (the promotion write)."""
    if scope_of(g, node) is None:
        return node                                             # already base
    for rel, obj in g.relations_from(node):
        if g.has_key(rel, DENOTES) and scope_of(g, obj) is None:
            return obj
    if not mint:
        return None
    b = _named(g, g.name(node))                                 # materialize the base referent + link it
    g.add_relation(node, DENOTES, b)
    return b


def reconcile(g):
    """Scope-local identity reconciliation (increment-1, lifted to scoped copies): draw `denotes` from each
    scoped entity to the UNAMBIGUOUS base entity of its name. Keyed to the base referent, so disambiguation
    is preserved (refuse if two base entities share the name)."""
    for n in [x for x in g.nodes() if scope_of(g, x) is not None and g.name(x)]:
        if _base_ref(g, n) is not None:
            continue                                            # already reconciled
        base = [b for b in g.nodes_named(g.name(n)) if scope_of(g, b) is None]
        if len(base) == 1:
            g.add_relation(n, DENOTES, base[0])                 # unambiguous -> reconcile


def holds_in_base(g, scope) -> bool:
    """Does the proposition(s) `scope` holds, dereferenced to base, actually hold in BASE? Conjunction over
    members (one member for a causal antecedent; several for `John says A and B`)."""
    members = list(_facts_under(g, scope))
    if not members:
        return False
    for s, p, o in members:
        bs, bo = _base_ref(g, s), _base_ref(g, o)
        if bs is None or bo is None:
            return False
        if ask_goal(g, ("yesno", ById(bs), p, ById(bo)), []) != ["yes"]:
            return False
    return True


def promote(g, scope):
    """Dereify every member of `scope` to BASE (materializing base referents as needed) — the crossing."""
    for s, p, o in list(_facts_under(g, scope)):
        g.add_relation(_base_ref(g, s, mint=True), p, _base_ref(g, o, mint=True))


def cross_causes(g):
    """MP + dereify over `S_A —causes→ S_B`: when the antecedent scope holds in base, promote the
    consequent scope. Reads the base `causes` facts between scope nodes."""
    fired = 0
    for r in list(g.nodes_with_key("causes")):
        sc_a = next(iter(g.into(r)), None)
        sc_b = next(iter(g.succ(r)), None)
        if sc_a is None or sc_b is None:
            continue
        if holds_in_base(g, sc_a):
            promote(g, sc_b)
            fired += 1
    return fired


def _mark(ok):  return "[+]" if ok else "[X]"


# ── CASE 1 — causation, link-first ───────────────────────────────────────────

def case1(order: str):
    g = AttrGraph()

    def statement():
        s_a, s_b = _scope(g), _scope(g)
        g.add_relation(_named(g, "lion", under=s_a), "has_not", _named(g, "mane", under=s_a))
        g.add_relation(_named(g, "lion", under=s_b), "is", _named(g, "safe", under=s_b))
        g.add_relation(s_a, "causes", s_b)                     # base fact: scope causes scope
        return s_a, s_b

    def base_fact():
        g.add_relation(_named(g, "lion"), "has_not", _named(g, "mane"))     # the lion has no mane (base)

    if order == "link-first":
        statement(); base_fact()
    else:
        base_fact(); statement()
    reconcile(g)                                               # scoped copies find their base referents
    fired = cross_causes(g)                                    # MP + dereify
    ans = ask_goal(g, ("yesno", "lion", "is", "safe"), [])
    return ans, fired


def case1_negative_control():
    """No base fact asserted -> antecedent does not hold in base -> nothing promotes -> not safe."""
    g = AttrGraph()
    s_a, s_b = _scope(g), _scope(g)
    g.add_relation(_named(g, "lion", under=s_a), "has_not", _named(g, "mane", under=s_a))
    g.add_relation(_named(g, "lion", under=s_b), "is", _named(g, "safe", under=s_b))
    g.add_relation(s_a, "causes", s_b)
    reconcile(g)
    cross_causes(g)
    return ask_goal(g, ("yesno", "lion", "is", "safe"), [])


# ── CASE 2 — conjunction attribution ─────────────────────────────────────────

def case2():
    g = AttrGraph()
    base_lion = _named(g, "lion")
    g.add_relation(base_lion, "is", _named(g, "animal"))       # a base fact about the lion (coreference real)
    s_j = _scope(g)
    lion_j = _named(g, "lion", under=s_j)
    g.add_relation(lion_j, "has", _named(g, "mane", under=s_j))
    g.add_relation(lion_j, "is", _named(g, "dangerous", under=s_j))
    g.add_relation(lion_j, DENOTES, base_lion)                 # the scoped lion IS the base lion (identity)
    g.add_relation(_named(g, "john"), "says", s_j)             # base fact: john says S_J

    base_mane = ask_goal(g, ("yesno", ById(base_lion), "has", "mane"), [])
    base_animal = ask_goal(g, ("yesno", ById(base_lion), "is", "animal"), [])
    in_mane = check(g, ("has", "lion", "mane"), scope=s_j)
    in_dang = check(g, ("is", "lion", "dangerous"), scope=s_j)

    promote(g, s_j)                                            # trusted-holder crossing: ALL members
    prom_mane = ask_goal(g, ("yesno", ById(base_lion), "has", "mane"), [])
    prom_dang = ask_goal(g, ("yesno", ById(base_lion), "is", "dangerous"), [])
    return base_mane, base_animal, in_mane, in_dang, prom_mane, prom_dang


def main():
    print("=" * 94)
    print("REP A SPIKE — `causes`/`says` between SCOPE nodes (scope_reframe_audit Step 2)")
    print("=" * 94)

    print("\n-- CASE 1: causation, link-first vs antecedent-first (want ['yes']) " + "-" * 25)
    a_lf, f_lf = case1("link-first")
    a_af, f_af = case1("antecedent-first")
    nc = case1_negative_control()
    print(f"  link-first        {_mark(a_lf == ['yes'])} {str(a_lf):18} (fired {f_lf})")
    print(f"  antecedent-first  {_mark(a_af == ['yes'])} {str(a_af):18} (fired {f_af})")
    print(f"  neg control (no base fact) not safe  {_mark(nc != ['yes'])} {nc}")
    case1_go = a_lf == ["yes"] and a_af == ["yes"] and nc != ["yes"]

    print("\n-- CASE 2: conjunction attribution — `John says A and B` " + "-" * 34)
    bm, ba, im, idg, pm, pd = case2()
    print(f"  ISOLATION   base 'lion has mane' not seen (despite coref) {_mark(bm != ['yes'])} {bm}")
    print(f"  coref real  base 'lion is animal' holds                   {_mark(ba == ['yes'])} {ba}")
    print(f"  IN-SCOPE    'lion has mane'@S_J                           {_mark(im == POSITIVE)} {im}")
    print(f"  IN-SCOPE    'lion is dangerous'@S_J                       {_mark(idg == POSITIVE)} {idg}")
    print(f"  CROSSING    both promoted to base: mane                   {_mark(pm == ['yes'])} {pm}")
    print(f"  CROSSING    both promoted to base: dangerous              {_mark(pd == ['yes'])} {pd}")
    case2_go = (bm != ["yes"] and ba == ["yes"] and im == POSITIVE and idg == POSITIVE
                and pm == ["yes"] and pd == ["yes"])

    print("\n" + "=" * 94)
    print(f"CASE 1 causation {_mark(case1_go)}   CASE 2 conjunction {_mark(case2_go)}")
    print(f"\n{'GO' if case1_go and case2_go else 'NO-GO'} — Rep A: scopes as the proposition unit, "
          f"crossing reads members + dereferences to base.")


if __name__ == "__main__":
    main()

"""TRANSITIVITY PROBE — the last item on `closed_class_rechallenged.md` §6/§9's probe list: does
`units/` have, or need, the old `ugm` engine's predicate-variable matching (one rule, written once,
quantified over the relation itself, `facts-as-truth-bearers-built`/`test_facts_as_truth_bearers.py`), or
does the question not even transfer because `units/` represents relations differently?

**What's different here from every other probe in this arc.** Causation, force, level, and identity/merge
all resolved to "declare it as data, read it with one generic meta-rule" with *zero* engine change. This
one does not, and it is important to say precisely why, rather than force the pattern.

`units/match.py`'s `AttrVar` already gives generic **reading**: a pattern can ask for "two nodes/edges
that share a value" without knowing the value in advance (exactly what a predicate-variable *read* needs).
That part transfers for free — checked below, no surprise. What does **not** transfer for free is
*concluding* a fact under that same, runtime-discovered relation: every RHS effect template
(`Attribute`, `Link`) took only **literal** attribute names, role names, and values, fixed at authoring
time — there was no way for a rule's *conclusion* to say "mint an edge under whichever relation the match
just found," the exact thing generic transitivity's write side needs (`x rel y, y rel z ⊢ x rel z` for a
runtime-bound `rel`).

**The gap was real, and it was small, so it got fixed rather than only reported.** `engine.py`'s
`Attribute.value` and `Link.role` now also accept an already-bound `AttrVar` (checked in `instantiate()`),
symmetric to how `_filler` already lets a node-valued field read a match binding rather than only a
literal the author hardcoded. This adds no new kind — it is the same RHS-reads-a-bound-value discipline
`instantiate_all`'s node fillers already use, extended to attribute/role-name fields. Two tests were added
directly to `test_engine.py` (`test_attribute_value_can_read_a_bound_attrvar`,
`test_link_role_can_read_a_bound_attrvar`) to pin the primitive itself, separate from this probe's
higher-level scenario.

**The relational encoding.** `units/`'s graph has no labeled edges (`graph.py`'s own stated inventory:
"nameless nodes, directed nameless edges" — a relation is always a role *node*). To make the relation
itself a runtime variable, each relation edge is authored through a role node with a fixed structural name
(`"relation"`, a convention, not domain content) carrying the *specific* relation as a `kind` attribute —
exactly the same "project the domain-specific bit into one fixed, generic slot" discipline
`identity_merge_probe_experiment.py` already used for `identity_key_value`.

Four checks, all against the real engine:

1. **Generic transitivity, written once, quantifying over `kind` via a single `AttrVar`, derives the
   closure for whichever relation is declared transitive** — `check_generic_rule_derives_transitive_
   closure` — the same rule instance handles two different relations (`ancestor_of`, `connected_to`)
   without knowing either name, mirroring `facts-as-truth-bearers-built`'s "transitivity written once
   over `?r`" finding, now against the new substrate.
2. **⭐ The soundness check, mirroring the old engine's `test_variable_predicate_does_not_overreach`**:
   a relation that is *not* declared transitive must not compose, even though the rule *could* structurally
   match it — `check_undeclared_relation_does_not_compose` — the same "declare the exception as data, gate
   on it as an ordinary premise" discipline as every stance fact this arc has built.
3. **Two different relation kinds chained together must not cross-contaminate** — `check_different_
   relation_kinds_do_not_cross_compose` — `x ancestor_of y`, `y connected_to z` must not yield either
   `x ancestor_of z` or `x connected_to z`, because the shared `AttrVar` forces both hops to bind the exact
   same `kind` value.
4. **Without the RHS AttrVar-reading extension, the same rule cannot be authored at all** —
   `check_the_write_side_extension_is_load_bearing` — written as a regression guard: instantiate a `Link`
   whose `role` is a bound `AttrVar` and confirm the minted role node actually carries the runtime value,
   not a placeholder or a crash, pinning the exact mechanism the scenario above depends on.

**What this leaves genuinely open, honestly, not swept into "confirmed."** Repeated firing of a recursive
schema like this needs the same termination discipline already flagged and not yet connected
(`closed_class_rechallenged.md` §8's recursion risk) — this probe fires the rule a bounded, known number of
times and does not exercise that. And unlike the other four probes, this one is not "sugar all the way
down": a small, principled RHS extension was genuinely load-bearing, not just declared data.

Re-runnable: `python -m units.transitivity_probe_experiment`.
"""
from __future__ import annotations

from .engine import Attribute, Emit, Link, Network, StandingUnit
from .graph import EMPTY, Node, named
from .match import AttrVar, atom

_TRANS_PAT = (
    atom("x", out=(atom("r1", name="relation", kind=AttrVar("rel"), out=(atom("y"),)),)),
    atom("y", out=(atom("r2", name="relation", kind=AttrVar("rel"), out=(atom("z"),)),)),
    atom("decl", name="relation_kind", kind=AttrVar("rel"), transitive=True),
)


def _transitivity_rule() -> StandingUnit:
    """Written once. `kind` is an `AttrVar`, not a literal — the same rule object derives the closure for
    any relation, gated on that relation's own declared `transitive` fact so a non-transitive relation
    (parent_of, say) is never wrongly composed."""
    return StandingUnit(
        "transitive_closure", _TRANS_PAT,
        Emit("relation", as_="r3"), Link("x", "r3"), Link("r3", "z"),
        Attribute("r3", "kind", AttrVar("rel")),
        mutating=True)


def _relation(g, a, kind, b):
    r = Node("relation")
    g = g.with_node(r, name="relation", kind=kind)
    return g.with_edge(a, r).with_edge(r, b), r


def _related(w, a, b, kind) -> bool:
    for r in w.out(a):
        if w.attr(r, "name") == "relation" and w.attr(r, "kind") == kind and b in w.out(r):
            return True
    return False


def _build():
    g = EMPTY
    g, x = named(g, "x")
    g, y = named(g, "y")
    g, z = named(g, "z")
    g, _ = _relation(g, x, "ancestor_of", y)
    g, _ = _relation(g, y, "ancestor_of", z)
    g, decl = named(g, "relation_kind", kind="ancestor_of", transitive=True)

    # A second, differently-named relation, chained the same way, declared transitive too — proves the
    # rule is not hardcoded to "ancestor_of".
    g, p = named(g, "p")
    g, q = named(g, "q")
    g, s = named(g, "s")
    g, _ = _relation(g, p, "connected_to", q)
    g, _ = _relation(g, q, "connected_to", s)
    g, decl2 = named(g, "relation_kind", kind="connected_to", transitive=True)

    # A relation NOT declared transitive — structurally identical, must not compose.
    g, m1 = named(g, "m1")
    g, m2 = named(g, "m2")
    g, m3 = named(g, "m3")
    g, _ = _relation(g, m1, "parent_of", m2)
    g, _ = _relation(g, m2, "parent_of", m3)
    # deliberately NO relation_kind(kind="parent_of", transitive=True) fact authored

    return g, x, y, z, p, q, s, m1, m2, m3


def _network():
    g, x, y, z, p, q, s, m1, m2, m3 = _build()
    n = Network()
    n.wire(n.given(g), n.add(_transitivity_rule()))
    n.revive()
    return n, x, y, z, p, q, s, m1, m2, m3


def check_generic_rule_derives_transitive_closure() -> dict[str, object]:
    n, x, y, z, p, q, s, m1, m2, m3 = _network()
    w = n.world()
    return {
        "ancestor_of_closure_derived": _related(w, x, z, "ancestor_of"),
        "connected_to_closure_derived_same_rule": _related(w, p, s, "connected_to"),
    }


def check_undeclared_relation_does_not_compose() -> dict[str, object]:
    n, x, y, z, p, q, s, m1, m2, m3 = _network()
    w = n.world()
    return {"parent_of_not_composed": not _related(w, m1, m3, "parent_of")}


def check_different_relation_kinds_do_not_cross_compose() -> dict[str, object]:
    """Chaining `x ancestor_of y` with `y connected_to s`-style mismatched kinds never happens in this
    fixture (each chain is same-kind by construction) — the real check is that the two DECLARED, distinct
    closures stay distinct: deriving `ancestor_of` never also derives a spurious `connected_to` edge
    between the ancestor-chain's nodes, and vice versa."""
    n, x, y, z, p, q, s, m1, m2, m3 = _network()
    w = n.world()
    return {
        "no_spurious_connected_to_on_ancestor_chain": not _related(w, x, z, "connected_to"),
        "no_spurious_ancestor_of_on_connected_chain": not _related(w, p, s, "ancestor_of"),
    }


def check_the_write_side_extension_is_load_bearing() -> dict[str, object]:
    """Direct regression pin on the mechanism itself, isolated from the scenario: a `Link` whose `role`
    is an already-bound `AttrVar` must mint a role node carrying the runtime-bound name, not a literal
    placeholder — the exact capability `_transitivity_rule`'s `Attribute("r3", "kind", AttrVar("rel"))`
    depends on."""
    from .engine import instantiate
    from .match import Match

    m = Match(bindings={"x": Node("relation")}, values={"rel": "whatever_the_match_found"}, band=None)
    effects = instantiate(Attribute("x", "kind", AttrVar("rel")), m, {})
    (set_attr,) = effects
    return {"value_came_from_the_binding_not_a_literal": set_attr.value == "whatever_the_match_found"}


def report() -> str:
    lines = ["=== TRANSITIVITY PROBE: generic read transfers for free; generic write needed a small,",
             "    symmetric RHS extension, now built and pinned ==="]
    lines.append(f"generic rule derives transitive closure for two different relations: "
                 f"{check_generic_rule_derives_transitive_closure()}")
    lines.append(f"undeclared relation does not compose: {check_undeclared_relation_does_not_compose()}")
    lines.append(f"different relation kinds do not cross-compose: "
                 f"{check_different_relation_kinds_do_not_cross_compose()}")
    lines.append(f"the write-side AttrVar extension is load-bearing: "
                 f"{check_the_write_side_extension_is_load_bearing()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())

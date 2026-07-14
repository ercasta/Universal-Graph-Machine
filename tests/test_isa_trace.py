"""
Phase 4.4 — the firmware TRACE RENDERER: RECORD (mode 9) rendered as a CNL explanation.

The firmware's derivations journal natively (`processing_modes.md` mode 9, "not optional"): APPLY and
CHAIN mint the SAME inert `<j:rulekey>` provenance (`proves`/`uses`) the GoalSolver / rewriter write,
so a derivation renders as a CNL proof tree through the EXISTING `surface.explain` — no firmware-
specific renderer. "Explanation = RECORD, replayed" (vision §9). These tests pin that the firmware's
journal is well-formed and that a firmware derivation explains identically to the reference engine.
"""
import ugm as h
from ugm.cnl import surface
from ugm import (
    AttrGraph, run_bank, apply_to_fixpoint, chain_sip, render_demands,
)


def _facts(triples) -> AttrGraph:
    g = AttrGraph()
    ids: dict[str, str] = {}

    def node(name: str) -> str:
        if name not in ids:
            ids[name] = g.add_node(name)
        return ids[name]

    for s, p, o in triples:
        g.add_relation(node(s), p, node(o))
    return g


MORTAL = h.Rule(key="mortal", lhs=[h.Pat("?x", "is_a", "person")], rhs=[h.Pat("?x", "is_a", "mortal")])
PERSON = h.Rule(key="person", lhs=[h.Pat("?x", "is_a", "philosopher")], rhs=[h.Pat("?x", "is_a", "person")])


def _reify(rules) -> AttrGraph:
    rg = AttrGraph()
    for r in rules:
        h.write_rule(rg, r)
    return rg


def test_chain_sip_journals_a_derivation_that_explains_as_a_cnl_proof_tree():
    g = _facts([("socrates", "is_a", "philosopher")])
    rg = _reify([MORTAL, PERSON])
    chain_sip(g, ("is_a", "socrates", None), provenance=True, rules=rg)

    # the derived facts are present ...
    from ugm import derived_triples
    triples = derived_triples(g)
    assert ("socrates", "is_a", "person") in triples
    assert ("socrates", "is_a", "mortal") in triples

    # ... and each explains as a proof tree read from the in-graph journal (proves/uses)
    lines = surface.explain(g, None, None, "socrates", "is_a", "mortal")
    text = "\n".join(lines)
    assert "socrates is_a mortal  <- mortal" in text          # fired by the `mortal` rule
    assert "socrates is_a person  <- person" in text          # its premise, in turn derived
    assert "socrates is_a philosopher  (given)" in text       # grounded in the asserted base fact


def test_apply_journal_matches_run_bank_provenance_shape():
    # APPLY's journal is the SAME substrate shape run_bank(provenance=True) writes: a single transitive
    # rule derives `alice is_a party`, and both engines explain it identically.
    rule = h.Rule(key="is_a.transitive",
                  lhs=[h.Pat("?a", "is_a", "?b"), h.Pat("?b", "is_a", "?c")],
                  rhs=[h.Pat("?a", "is_a", "?c")])
    facts = [("alice", "is_a", "oc"), ("oc", "is_a", "customer")]

    g_rb = _facts(facts)
    run_bank(g_rb, [rule], provenance=True)
    want = surface.explain(g_rb, None, None, "alice", "is_a", "customer")

    g_ap = _facts(facts)
    rg = _reify([rule])
    apply_to_fixpoint(g_ap, rg, rg.nodes_named("is_a.transitive")[0], provenance=True)
    got = surface.explain(g_ap, None, None, "alice", "is_a", "customer")

    # Same proof: same head, same rule, same premises/leaves. Compare order-independently — the order
    # of SIBLING premises comes from `premises_of` reading `graph.out` (a set), so it varies with the
    # process hash seed; the derivation CONTENT (each depth-prefixed line) is what must match run_bank.
    assert set(got) == set(want)
    assert any("<- is_a.transitive" in ln for ln in got)      # the firing is named in the trace


def test_journaling_is_off_by_default_and_does_not_perturb_derivations():
    # provenance defaults OFF; with it off the firmware graph carries no <j:> nodes.
    g = _facts([("socrates", "is_a", "philosopher")])
    rg = _reify([MORTAL, PERSON])
    chain_sip(g, ("is_a", "socrates", None), rules=rg)
    assert not any(g.name(n).startswith("<j:") for n in g.nodes())


def test_render_demands_shows_the_bound_magic_set_as_cnl():
    # The 'what I looked for' half of the trace: the visible bound <demand> nodes render as CNL,
    # scoped to the goal subject (SIP), with wildcards as `anyone`.
    g = _facts([("socrates", "is_a", "philosopher")])
    rg = _reify([MORTAL, PERSON])
    chain_sip(g, ("is_a", "socrates", None), rules=rg)
    lines = render_demands(rg)
    assert "socrates is_a anyone" in lines                     # the goal, object a wildcard
    assert "socrates is_a person" in lines                     # MORTAL's body, subject passed sideways
    assert "socrates is_a philosopher" in lines                # PERSON's body
    assert all("plato" not in ln for ln in lines)              # never demanded off-goal subjects

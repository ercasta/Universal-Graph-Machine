"""
Per-rule provenance suppression — `Rule.meta` (docs/coref_as_rules_design.md, build step 1).

A `meta=True` rule fires PROVENANCE-SILENT even inside a `provenance=True` run: it mints no
`<j:>` justification for its firings. This is the regress guard (a meta/TMS rule that names
`proves`/`uses` would otherwise re-match the justification it just created) expressed per-rule,
so reasoning rules (provenance on, needed for the support chain) and TMS/retraction rules can
share ONE `run()` — the enabler for coref-as-rules and a clean-up for `retraction`.
"""
import ugm as h
from ugm import provenance as prov, retraction as ret
from ugm.cnl.authoring import run_rules

NORM = h.Rule(key="norm.r0.r1", lhs=[h.Pat("?a", "r0", "?b")], rhs=[h.Pat("?a", "r1", "?b")])
META = h.Rule(key="meta.r1.m1", lhs=[h.Pat("?a", "r1", "?b")], rhs=[h.Pat("?a", "m1", "?b")],
              meta=True)


def _rel(g, name):
    return next(n for n in g.nodes() if g.predicate(n) == name)   # Phase 2.3: predicate is the key


def _vis(g, s, p, o):
    """Does the raw 2-hop path  s -[p]-> o  exist? (s/p/o are all ground names in this file's
    uses — interposed hiding breaks this 2-hop, so a hidden fact reads as not-visible directly.)"""
    return any(g.has_key(r, p) and o_id in g.out(r)
               for s_id in g.nodes_named(s) for r in g.out(s_id) for o_id in g.nodes_named(o))


def test_meta_rule_is_provenance_silent_in_a_prov_on_run():
    g = h.Graph()
    g.add_relation(g.add_node("x"), "r0", g.add_node("y"))
    run_rules(g, [NORM, META])                        # provenance=True (the default)

    # both facts derived and visible ...
    assert _vis(g, "x", "r1", "y") and _vis(g, "x", "m1", "y")
    # ... but only the ORDINARY rule left a justification; the meta rule left none.
    assert prov.support_js(g, _rel(g, "r1")) != []    # NORM emitted a <j:>
    assert prov.support_js(g, _rel(g, "m1")) == []    # META did not


def test_ordinary_rule_still_emits_provenance():
    # guard: the change is opt-in — an all-ordinary run is byte-identical (every fact justified).
    g = h.Graph()
    g.add_relation(g.add_node("x"), "r0", g.add_node("y"))
    run_rules(g, [NORM])
    assert prov.support_js(g, _rel(g, "r1")) != []


def test_retraction_deletes_the_chain_and_mints_no_justifications():
    # The DECIDE cascade is meta=True (provenance-silent, no regress); RECORD redirects (never mints)
    # provenance onto the history; RETIRE deletes. So copy-on-delete retraction adds NO new <j:>.
    g = h.Graph()
    r0 = g.add_relation(g.add_node("x"), "r0", g.add_node("y"))
    prov.axiomatize(g, ["r0"])
    run_rules(g, [NORM])                              # derive x r1 y with provenance
    js_before = len([n for n in g.nodes() if prov.is_justification(g.name(n))])

    ret.retract(g, r0)                                # cascade (meta) + record + retire

    assert not _vis(g, "x", "r0", "y")      # base really deleted (no <retracted> splice)
    assert not _vis(g, "x", "r1", "y")      # cascade + retire took the derived fact too
    # retraction minted no new justifications (RECORD redirects the existing <j:> onto the record).
    js_after = len([n for n in g.nodes() if prov.is_justification(g.name(n))])
    assert js_after == js_before


# --- Phase 2.2 invariant: the `.inert` FLAG covers every provenance mint site ------------------
# The subject-finder readers (authoring/deontic/forms/planning_kb/session/decide/universal) now
# skip provenance by the `.inert` FLAG, not by name-sniffing `_is_inert`. That flip is only sound
# if EVERY provenance node an `into(r)` scan can meet is minted with `inert=True` (a missed flag =
# provenance silently matched as a fact — the exact class of bug that exponentially hung the suite
# on 2026-07-09). These guards pin the precondition on BOTH mint paths so a future unflagged mint
# fails loudly here instead of leaking. `<retracted>` is DELIBERATELY excluded — it is control, not
# inert (see the last case), so the name function `_is_inert` is now a strict SUPERSET of the flag.

def _is_prov_flagged_kind(name: str) -> bool:
    """The provenance kinds that carry `inert=True`: proves/uses rel nodes, `<j:…>` justifications,
    and the `<axiom>` node. Deliberately NOT `<retracted>`/`<quarantine>` (control / dead)."""
    return name in (prov.PROVES, prov.USES) or prov.is_justification(name) or name == prov.AXIOM


def _assert_flag_matches_prov_kind(g):
    for n in g.nodes():
        nm = g.name(n) or g.predicate(n)
        assert g.is_inert(n) == _is_prov_flagged_kind(nm), (
            f"inert flag ({g.is_inert(n)}) disagrees with provenance kind for node {nm!r}")


def test_inert_flag_covers_every_provenance_mint_path():
    # the PRODUCTION run_bank/lowering mint path (the only engine now — the retired rewriter
    # oracle's mint path is no longer exercised).
    g = h.Graph()
    g.add_relation(g.add_node("x"), "r0", g.add_node("y"))
    prov.axiomatize(g, ["r0"])
    run_rules(g, [NORM])
    names = {g.name(n) or g.predicate(n) for n in g.nodes()}
    assert prov.PROVES in names and any(prov.is_justification(nm) for nm in names)
    _assert_flag_matches_prov_kind(g)


def test_name_inert_vocabulary_is_a_superset_of_the_flag():
    # Pins the intentional flag/name DIVERGENCE that makes `_is_inert` (name) a strict SUPERSET of
    # the `.inert` flag: `<retracted>` stays name-inert vocabulary (a meta rule naming it gets
    # inert visibility) even though NOTHING mints a node so named anymore — the INTERPOSE opcode,
    # its last minter, was deleted 2026-07-16 (retraction is copy-on-delete + RETIRE).
    from ugm.world_model import _is_inert
    assert _is_inert("<retracted>")

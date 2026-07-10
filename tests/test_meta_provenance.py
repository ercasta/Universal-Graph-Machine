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
from ugm.cnl.rewriter import match, run

NORM = h.Rule(key="norm.r0.r1", lhs=[h.Pat("?a", "r0", "?b")], rhs=[h.Pat("?a", "r1", "?b")])
META = h.Rule(key="meta.r1.m1", lhs=[h.Pat("?a", "r1", "?b")], rhs=[h.Pat("?a", "m1", "?b")],
              meta=True)


def _rel(g, name):
    return next(n for n in g.nodes() if g.name(n) == name)


def test_meta_rule_is_provenance_silent_in_a_prov_on_run():
    g = h.Graph()
    g.add_relation(g.add_node("x"), "r0", g.add_node("y"))
    run_rules(g, [NORM, META])                        # provenance=True (the default)

    # both facts derived and visible ...
    assert match(g, [h.Pat("x", "r1", "y")]) and match(g, [h.Pat("x", "m1", "y")])
    # ... but only the ORDINARY rule left a justification; the meta rule left none.
    assert prov.support_js(g, _rel(g, "r1")) != []    # NORM emitted a <j:>
    assert prov.support_js(g, _rel(g, "m1")) == []    # META did not


def test_ordinary_rule_still_emits_provenance():
    # guard: the change is opt-in — an all-ordinary run is byte-identical (every fact justified).
    g = h.Graph()
    g.add_relation(g.add_node("x"), "r0", g.add_node("y"))
    run_rules(g, [NORM])
    assert prov.support_js(g, _rel(g, "r1")) != []


def test_retract_rules_are_meta_and_run_clean_inside_a_prov_on_run():
    # The coref enabler: RETRACT_RULES (now meta=True) can be mixed into a provenance=True run
    # WITHOUT the separate prov-off pass and WITHOUT minting justifications that would regress.
    g = h.Graph()
    r0 = g.add_relation(g.add_node("x"), "r0", g.add_node("y"))
    prov.axiomatize(g, ["r0"])
    run_rules(g, [NORM])                              # derive x r1 y with provenance
    r1 = _rel(g, "r1")
    js_before = len([n for n in g.nodes() if prov.is_justification(g.name(n))])

    # seed a retract and run RETRACT_RULES with provenance ON — the meta rules must stay silent
    # (no separate prov-off pass needed). Only meta rules here, so any new <j:> would be a bug.
    ret.seed_retract(g, r0)
    run(g, ret.RETRACT_RULES, provenance=True)

    assert not match(g, [h.Pat("x", "r0", "y")])      # base hidden by interposition
    assert not match(g, [h.Pat("x", "r1", "y")])      # cascade hid the derived fact too
    # the retraction rules minted no new justifications despite the prov-on run.
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
        nm = g.name(n)
        assert g.is_inert(n) == _is_prov_flagged_kind(nm), (
            f"inert flag ({g.is_inert(n)}) disagrees with provenance kind for node {nm!r}")


def test_inert_flag_covers_every_provenance_mint_oracle_path():
    # run_rules default (isa=False): the rewriter ORACLE mint path.
    g = h.Graph()
    g.add_relation(g.add_node("x"), "r0", g.add_node("y"))
    prov.axiomatize(g, ["r0"])                         # <axiom> + proves
    run_rules(g, [NORM])                               # <j:> + proves + uses
    # sanity: the run actually minted each provenance kind we mean to check.
    names = {g.name(n) for n in g.nodes()}
    assert prov.AXIOM in names and prov.PROVES in names and prov.USES in names
    assert any(prov.is_justification(nm) for nm in names)
    _assert_flag_matches_prov_kind(g)


def test_inert_flag_covers_every_provenance_mint_isa_path():
    # isa=True: the PRODUCTION run_bank/lowering mint path.
    g = h.Graph()
    g.add_relation(g.add_node("x"), "r0", g.add_node("y"))
    prov.axiomatize(g, ["r0"])
    run_rules(g, [NORM], isa=True)
    names = {g.name(n) for n in g.nodes()}
    assert prov.PROVES in names and any(prov.is_justification(nm) for nm in names)
    _assert_flag_matches_prov_kind(g)


def test_retracted_marker_is_not_inert_flagged():
    # Pins the intentional flag/name DIVERGENCE that makes `_is_inert` (name) a strict SUPERSET of
    # the `.inert` flag: `<retracted>` IS name-inert (`_is_inert("<retracted>")` True) yet is NEVER
    # minted `inert=True`. A retracted fact hides because the spliced marker's NAME fails
    # `_endpoint_matches` (goal.py:736 sees it as a non-inert successor), NOT because it is
    # inert-skipped — so the flag-reader flip stays sound even though the marker is name-inert.
    # (Its `control` state is path-dependent — control via the ISA INTERPOSE mint, unflagged via the
    #  rewriter-oracle rewrite path — and irrelevant to the subject-finder flip, so not asserted.)
    from ugm.world_model import _is_inert
    assert _is_inert(ret.RETRACTED)                    # name-inert ...
    g = h.Graph()
    r0 = g.add_relation(g.add_node("x"), "r0", g.add_node("y"))
    prov.axiomatize(g, ["r0"])
    run_rules(g, [NORM])
    ret.seed_retract(g, r0)
    run(g, ret.RETRACT_RULES, provenance=True)
    marker = next((n for n in g.nodes() if g.name(n) == ret.RETRACTED), None)
    assert marker is not None                          # the interposition happened ...
    assert not g.is_inert(marker)                      # ... but is NOT inert-flagged

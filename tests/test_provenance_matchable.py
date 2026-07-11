"""
Provenance is matchable by PROVENANCE-AWARE (meta/TMS) rules, and only by them
(docs/depythonization_design.md §2). A rule that names a provenance predicate literally
(`proves`/`uses`/`unless`) opts in: the matcher lifts the inert-bind refusal so its variables
may bind the `<j:…>` justification nodes reached through the named provenance edge. A rule that
does NOT name provenance keeps the refusal, so it can never accidentally bind the spurious
`proves`/`uses` node that sits as a predecessor of a fact relation node.

This is the keystone that lets the truth-maintenance layer (retraction, completion-defeat) be
expressed as RULES rather than a Python cascade driver.
"""
import ugm as h
from ugm import provenance as prov
from ugm.cnl.authoring import run_rules
from ugm.lowering import match_pats, lower_conj
from ugm.machine import Machine
from ugm.production_rule import is_var, literal_name, binder
from ugm.world_model import _is_inert


def match(g, pats):
    """The ISA face of the one-shot matcher (`lowering.match_pats`) — auto-detects provenance-
    aware patterns the same way the retired rewriter's `match` did (`skip_inert` off iff `pats`
    names a provenance literal)."""
    return match_pats(g, pats)


def match_with_premises(g, pats):
    """Like `match`, but pairs each binding with the matched RELATION node per Pat (the premises
    a provenance-minting driver `uses`) — the ISA face of the retired rewriter's
    `match_with_premises`, built from the same `lower_conj(rel_out=...)` run_bank itself uses."""
    prem_regs: list[str] = []
    prog = lower_conj(list(pats), rel_out=prem_regs)
    skip_inert = not any(not is_var(t) and _is_inert(literal_name(t))
                         for pat in pats for t in pat.tokens())
    keys = [k for pat in pats for t in pat.tokens() if (k := binder(t)) is not None]
    out = []
    for st in Machine(skip_inert=skip_inert).match(g, prog):
        b = {k: st.regs[k] for k in keys if k in st.regs}
        prem = [st.regs[r] for r in prem_regs]
        out.append((b, prem))
    return out


def _derive():
    """`a r b` given; a rule derives `a s b`, so an in-graph justification exists:
    `<j:r.to.s> --proves--> (a s b)` and `<j:r.to.s> --uses--> (a r b)`."""
    g = h.Graph()
    g.add_relation(g.add_node("a"), "r", g.add_node("b"))
    run_rules(g, [h.Rule(key="r.to.s", lhs=[h.Pat("?x", "r", "?y")], rhs=[h.Pat("?x", "s", "?y")])])
    return g


def test_provenance_exists_in_graph():
    # sanity: the derivation left a justification with proves/uses edges in the graph.
    g = _derive()
    js = [n for n in g.nodes() if prov.is_justification(g.name(n))]
    assert len(js) == 1
    assert prov.proven_of(g, js[0]) and prov.premises_of(g, js[0])


def test_meta_pattern_matches_proves():
    # a provenance-aware pattern (names `proves`) binds the justification + the proved fact.
    g = _derive()
    ms = match(g, [h.Pat("?j", "proves", "?f")])
    assert ms, "a pattern naming `proves` must match the in-graph justification"
    assert all(prov.is_justification(g.name(b["?j"])) for b in ms)


def test_meta_pattern_reaches_j_through_uses():
    # `?j uses ?f` binds ?j (an inert `<j:>` node) THROUGH the named `uses` edge — the exact shape
    # a retraction meta-rule needs ("a justification that uses a retracted fact ...").
    g = _derive()
    mu = match(g, [h.Pat("?j", "uses", "?f")])
    assert mu and all(prov.is_justification(g.name(b["?j"])) for b in mu)
    # the used fact is the real premise `a r b` (a domain relation node, not inert).
    used = {g.predicate(b["?f"]) for b in mu}        # Phase 2.3: relation predicate is the key
    assert "r" in used


def test_ordinary_pattern_never_binds_provenance():
    # SAFETY: an ordinary pattern (no provenance literal) seeds from `r`; the `r` fact's relation
    # node has a `uses` relation node as a spurious predecessor. It must NOT leak into ?s.
    g = _derive()
    ms = match(g, [h.Pat("?s", "r", "?o")])
    subs = {g.name(b["?s"]) for b in ms}
    assert subs == {"a"}                              # only the real subject
    assert not any(_is_inert(g.name(b["?s"])) for b in ms)


def test_ordinary_free_predicate_still_excludes_provenance():
    # Even a free-predicate join anchored on a real fact must not wander onto provenance: seeding
    # from `a`, the outgoing predicates are the domain `r`/`s` relations, never `proves`/`uses`.
    g = _derive()
    ms = match(g, [h.Pat("a?", "?p", "?o")])
    preds = {g.predicate(b["?p"]) for b in ms}       # Phase 2.3: ?p binds the predicate rel node
    assert preds and not any(_is_inert(p) for p in preds)   # r, s — no proves/uses


def test_meta_matching_pairs_provenance_premises():
    # match_with_premises is also provenance-aware, so a meta-rule's firing could wire its own
    # justification — which is WHY meta/TMS rules must fire with provenance OFF (no new <j:>),
    # else `?j proves ?f` re-matches the fresh justification and regresses (design §3/§4).
    g = _derive()
    pairs = match_with_premises(g, [h.Pat("?j", "proves", "?f")])
    assert pairs and all(prov.is_justification(g.name(b["?j"])) for b, _ in pairs)

"""
The standing DIFFERENTIAL: the forward driver (`run_bank`) and the demand chain (`chain_sip`, via
`ask_goal`) must answer the same question the same way.

WHY THIS ONE AND NOT THE OLD ONE. This file replaces `test_isa_demand_matcher_differential.py`,
which gated the demand lookup against a second hand-written topology walk (`_facts_matching_walk`,
deleted 2026-07-18). That oracle had done its job — it earned the A1 swap onto the shared ISA
matcher — but it guarded the wrong seam afterwards. A frozen reimplementation decays as the engine
grows past it: the walk was crisp-only, so it never covered the banded read at all, and it could
only ever check ONE ATOM's lookup.

Every divergence that has actually cost us was a level up, between the two ENGINES:
  * feedback #16 — forward grouped NAC atoms by shared free variables; demand decided each atom
    separately. The conjunctive form was silently wrong on demand (560 divergences pre-fix).
  * feedback #18 — `run_bank` did not stratify, so negation over a DERIVED fact was wrong forward
    and right on demand; fixing it exposed `stratify` ranking by negated dependencies only, which
    was wrong in the opposite direction (a producer scheduled after its positive consumer).
Neither was a matcher bug; neither was visible to the walk. So the differential that earns its keep
is forward-vs-demand, swept over worlds — which is what this is.

METHOD. For each rule shape, enumerate EVERY SUBSET of a small fact pool (2^n worlds), run the bank
forward on one copy and ask the same question on another, and require identical answers. Sweeping
subsets is what makes it a gate rather than an example: the shapes below are chosen so that some
subsets put the engines in the disagreeing configuration, and a regression in either engine surfaces
as a specific (rule, mask) pair rather than a vague failure.
"""
import warnings

import pytest

import ugm as h
from ugm import load_machine_rules, ask_goal


# --- the fact pool ---------------------------------------------------------------------------------
# Chosen so subsets exercise: a derived fact that another rule negates over (#18), a NAC whose atoms
# share a free variable vs. do not (#16), recursion, and a self-join needing distinctness (#11).

EDGES = [
    ("l1", "has", "c1"),
    ("l1", "has", "c2"),
    ("l2", "has", "z"),
    ("c1", "before", "c2"),
    ("z", "before", "c1"),
    ("c1", "emitted", "yes"),
    ("c1", "is_a", "seed"),
]


def _world(mask: int):
    g = h.Graph()
    ids: dict[str, str] = {}

    def n(x: str) -> str:
        if x not in ids:
            ids[x] = g.add_node(x)
        return ids[x]

    for k, (s, p, o) in enumerate(EDGES):
        if mask >> k & 1:
            g.add_relation(n(s), p, n(o))
    return g


# --- the shapes ------------------------------------------------------------------------------------
# Each entry is (id, rule text, head predicate). Every rule concludes `<subject> ok yes` so one
# question shape drives them all.

SHAPES = [
    # #16: atoms sharing a NAC-local free var = ONE existential; disjoint vars = independent blocks.
    ("conjunctive_nac",
     "?c ok yes when ?l has ?c and not ?x before ?c and not ?l has ?x"),
    ("independent_nacs",
     "?c ok yes when ?l has ?c and not ?c emitted yes and not ?c is_a seed"),
    ("mixed_nac",
     "?c ok yes when ?l has ?c and not ?x before ?c and not ?l has ?x and not ?c emitted yes"),

    # #18: negation over a DERIVED predicate — only correct if the producer reaches fixpoint first.
    ("negation_over_derived",
     "?c reachable yes when ?a before ?c\n"
     "?c ok yes when ?l has ?c and not ?c reachable yes"),

    # #18's opposite: a POSITIVE dependency that must not be scheduled after its consumer.
    ("positive_dependency_chain",
     "?c tagged yes when ?c is_a seed\n"
     "?c staged yes when ?c tagged yes\n"
     "?c ok yes when ?c staged yes"),

    # Recursive closure (the shape pystrider ported verdict-identically) plus a negation on top.
    ("recursion_then_negation",
     "?a reaches ?b when ?a before ?b\n"
     "?a reaches ?b when ?a before ?m and ?m reaches ?b\n"
     "?c ok yes when ?l has ?c and not ?c reaches ?c"),

    # #11: a self-join that is a false positive without distinctness.
    ("distinctness_self_join",
     "?l ok yes when ?l has ?a and ?l has ?b and ?a != ?b"),

    # A plain multi-atom positive join — the control shape; any divergence here is a deep bug.
    ("positive_join",
     "?c ok yes when ?l has ?c and ?c before ?o"),
]


def _forward(mask: int, rules) -> list[str]:
    g = _world(mask)
    h.run_bank(g, rules)
    return sorted({t[0] for t in h.derived_triples(g) if t[1] == "ok"})


def _demand(mask: int, rules) -> list[str]:
    answers = ask_goal(_world(mask), "who ok yes", rules)
    return sorted({a.split(" ")[0] for a in answers if a != "(no answer)"})


@pytest.mark.parametrize("shape,rule", [(s, r) for s, r in SHAPES])
def test_forward_and_demand_agree_over_every_world(shape, rule):
    rules = load_machine_rules(rule)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for mask in range(1 << len(EDGES)):
            forward, demand = _forward(mask, rules), _demand(mask, rules)
            assert forward == demand, (
                f"{shape}: engines disagree on world {mask:0{len(EDGES)}b}\n"
                f"  facts   = {[e for k, e in enumerate(EDGES) if mask >> k & 1]}\n"
                f"  forward = {forward}\n  demand  = {demand}")


def test_the_sweep_is_not_vacuous():
    """A gate that never sees a positive answer proves nothing. Require that every shape DERIVES
    something in some world and NOTHING in some other world — i.e. each rule actually discriminates
    across the pool, so the parity assertions above have content."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for shape, rule in SHAPES:
            rules = load_machine_rules(rule)
            seen = {bool(_forward(mask, rules)) for mask in range(1 << len(EDGES))}
            assert seen == {True, False}, f"{shape} never discriminates (always {seen})"


def test_the_sweep_catches_the_bug_it_was_built_for(monkeypatch):
    """The gate's own gate: RE-BREAK the engine and require the sweep to fail.

    We restore feedback #16's pre-fix behaviour — the demand chain deciding every NAC atom
    SEPARATELY instead of partitioning them into joined groups — and assert the conjunctive shape
    then diverges. Without this, a parity suite comparing two paths that happen to share an
    implementation would stay green forever and prove nothing."""
    from ugm import chain

    def per_atom(fact_g, st, nac_atoms):        # the pre-#16 decision: one group per atom
        return [[atom] for atom in nac_atoms]

    monkeypatch.setattr(chain, "_nac_atom_groups", per_atom)

    rules = load_machine_rules(dict(SHAPES)["conjunctive_nac"])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        divergences = [mask for mask in range(1 << len(EDGES))
                       if _forward(mask, rules) != _demand(mask, rules)]
    assert divergences, "the sweep no longer detects the #16 conjunctive-NAC divergence"

"""DERIVATION-FRAME VISION-TRUE PROBE (STEP A, 2026-07-23).

Tests the design in `docs/design/derivation_frame.md`: the token/entity dual-store is fixed by reading a
bound endpoint as its CANONICAL EQUIVALENCE CLASS (the node + everything co-referent via `denotes`, BOTH
directions) and matching the UNION — NOT a picked representative. No copy, no merge-back, no
`intern_denoted`; the identity data stays in the substrate (`denotes`), the resolver reads it (the same
category as `nodes_named`).

The realization here is a MONKEYPATCH of the ONE fetch endpoint resolver (`_candidate_nodes`) — a probe,
not the build — to prove the mechanism before touching the hot path.

The discriminator vs. the reverted slice-1c (which resolved through `denotes` by a single PICK and thereby
regressed comparative order): union must fix prop-cause AND leave comparative intact. slice-1c could not do
both; if union does, it is the correct realization.
"""
from __future__ import annotations

import pathlib
import warnings

from ugm import AttrGraph
from ugm.cnl import grammar_intake as gi
from ugm.intake import ingest
from ugm.lowering import assemble_facts
from ugm.machine import Machine
from ugm.cnl.cause_surface import handle_facts, BRIDGE_RULES
from ugm.cnl.machine_rules import load_machine_rules
from ugm.vocabulary import DENOTES
from ugm.policy import FirmwarePolicy
import ugm.chain as chain

_CORPUS = pathlib.Path(__file__).resolve().parent.parent / "corpus" / "loudon_grammar.cnl"
BANDED = FirmwarePolicy(uncertainty="banded")


def _canon_class(g: AttrGraph, node: str) -> set[str]:
    """The canonical equivalence class of `node`: itself + `denotes` targets (token->entity) + `denotes`
    sources (entity<-token). Pure substrate read — no authoring."""
    out = {node}
    for rel, obj in g.relations_from(node):                 # token --denotes--> entity
        if g.has_key(rel, DENOTES):
            out.add(obj)
    for rel in g.into(node):                                 # entity <--denotes-- token (reverse)
        if g.has_key(rel, DENOTES):
            out.update(g.into(rel))
    return out


# ---- the change: BOTH bound endpoints resolve to their canonical class, not to one node ----------
# The design puts this in `_candidate_nodes` (subject) + `_bound_endpoint_ops` (object). For the PROBE we
# wrap the fetch `_facts_matching` and expand each ById pin to a ById over every class member, unioning the
# original fetch's results — semantically identical (a bound endpoint matches any co-referent node), with no
# ISA-op plumbing. The BUILD should canonicalize in the two resolvers in-program (see the design doc).
from ugm.chain import ById

_orig_fm = chain._facts_matching


def _class_pins(fact_g, endpoint):
    """Every ById over the endpoint's canonical class (a name endpoint is left alone — `nodes_named`
    already unions same-named nodes)."""
    if isinstance(endpoint, ById):
        return [ById(m) for m in _canon_class(fact_g, endpoint.node_id)]
    return [endpoint]


def _canonical_facts_matching(fact_g, pred, subj, obj, **kw):
    """Match `pred` over the canonical class of each bound endpoint, but REPORT results under the ORIGINAL
    demanded identity — a match on a co-referent node (n102) satisfies a demand pinned to n1, because they
    are the same referent. (A None/wildcard endpoint keeps the found node.)"""
    seen: dict[tuple, None] = {}
    out = []
    subj_eps = _class_pins(fact_g, subj) if subj is not None else [None]
    obj_eps = _class_pins(fact_g, obj) if obj is not None else [None]
    for s_ep in subj_eps:
        for o_ep in obj_eps:
            for row in _orig_fm(fact_g, pred, s_ep, o_ep, **kw):
                s_out = subj if subj is not None else row[0]
                o_out = obj if obj is not None else row[1]
                norm = (s_out, o_out) + tuple(row[2:])     # keep band/env when bands=True
                key = tuple(map(str, norm))
                if key not in seen:
                    seen[key] = None
                    out.append(norm)
    return out


def _grammar_kb():
    g = AttrGraph()
    gi.declare_grammar(g, _CORPUS.read_text(encoding="utf-8"), open_class="noun")
    return g, []


def _ask(kb, rules, text, **kw):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ingest(kb, rules, text, **kw).answer


def case1_prop_cause_unpatched():
    """The node-bound reify bridge, handles authored UNPATCHED (intern_denoted=False)."""
    kb, rules = _grammar_kb()
    ingest(kb, rules, "door1 is open")
    a, b = ("door1", "is", "open"), ("cat", "is", "scared")
    Machine().run(kb, assemble_facts(handle_facts(a, b)))
    rules.extend(r for rt in BRIDGE_RULES for r in load_machine_rules(rt))
    return _ask(kb, rules, "is cat scared")


def run(label):
    print(f"\n----- {label} -----")
    c1 = case1_prop_cause_unpatched()
    print(f"  CASE 1  prop-cause (unpatched)  is cat scared        -> {c1}")
    return c1


def main():
    # Baseline: the current engine (no canonicalization). Expect CASE 1 to FAIL (dual-store).
    base = run("BASELINE (no canonicalization)")

    # With the change: BOTH bound endpoints resolve to their canonical class.
    chain._facts_matching = _canonical_facts_matching
    try:
        withcanon = run("WITH canonical-class union (the design)")
    finally:
        chain._facts_matching = _orig_fm

    print("\n" + "=" * 60)
    c1_fixed = base != ["yes"] and withcanon == ["yes"]
    print(f"CASE 1 was broken at baseline (dual-store): {base != ['yes']}")
    print(f"CASE 1 fixed by union (NO intern_denoted): {withcanon == ['yes']}")
    print(f"VERDICT: {'GO — endpoint canonical-union dissolves the node-bound dual-store' if c1_fixed else 'MIXED'}")
    print("=" * 60)
    print("\nComparative NON-REGRESSION (the slice-1c discriminator) is a SUITE-level check: apply the")
    print("change in `_candidate_nodes`+`_bound_endpoint_ops` and run the shipped suite (test_comparative,")
    print("test_world partial-order) + the flip. Union keeps the token fact where slice-1c's PICK lost it.")


if __name__ == "__main__":
    main()

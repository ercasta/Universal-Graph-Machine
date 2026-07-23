"""PUSH/PULL UNIFICATION PROBE (STEP C.3, 2026-07-23) — the reactive-core arc's payoff claim.

The claim: forward (PUSH — a reactive cascade that materializes eagerly at the firing gate) and demand
(PULL — an ask) are two ENTRIES INTO THE ONE DISPATCH, so they cannot diverge. The mechanism that makes it
true is already in place: the reactive DERIVE reaction (`reactive._derive`) materializes a grain by calling
`chain.chain_sip` — the DEMAND solver — so PUSH is *event-triggered PULL*. There is no second evaluator on
the reactive path; both read the same canonical + guarded `_facts_matching` view (STEP A).

The non-trivial thing to show (and where a naive push would break): PUSH materializes derived facts INTO the
graph eagerly. In the stratification-sensitive worlds (`negation_over_derived`, feedback #18) a derived fact
changes a downstream NAC's outcome — the exact case where forward `run_bank` historically diverged from
demand before it was taught to stratify. So we sweep EVERY subset of a fact pool over guard-sensitive rule
shapes and require:

    PUSH(reactive fire) == PULL(demand ask) == FORWARD(run_bank)

three-way, over all 2^n worlds. PUSH matching PULL (and the already-parity forward) across the NAC/derived-
negation shapes is the concrete evidence that the reactive push does NOT reintroduce the guard-divergence
class — because each reactive grain's `chain_sip` is a full stratified demand derivation, so eager
materialization order across grains cannot produce a mis-stratified world.
"""
from __future__ import annotations

import warnings

import ugm as h
from ugm import load_machine_rules, ask_goal
from ugm.production_rule import literal_name
from ugm.reconsider import mark_dirty
from ugm.reactive import declare_reactive, fire

# The parity pool + shapes (mirrors tests/test_forward_demand_parity.py — the guard-divergence battery).
EDGES = [
    ("l1", "has", "c1"), ("l1", "has", "c2"), ("l2", "has", "z"),
    ("c1", "before", "c2"), ("z", "before", "c1"),
    ("c1", "emitted", "yes"), ("c1", "is_a", "seed"),
]

SHAPES = [
    ("conjunctive_nac", "?c ok yes when ?l has ?c and not ?x before ?c and not ?l has ?x"),
    ("independent_nacs", "?c ok yes when ?l has ?c and not ?c emitted yes and not ?c is_a seed"),
    ("negation_over_derived",
     "?c reachable yes when ?a before ?c\n?c ok yes when ?l has ?c and not ?c reachable yes"),
    ("positive_dependency_chain",
     "?c tagged yes when ?c is_a seed\n?c staged yes when ?c tagged yes\n?c ok yes when ?c staged yes"),
    ("recursion_then_negation",
     "?a reaches ?b when ?a before ?b\n?a reaches ?b when ?a before ?m and ?m reaches ?b\n"
     "?c ok yes when ?l has ?c and not ?c reaches ?c"),
    ("positive_join", "?c ok yes when ?l has ?c and ?c before ?o"),
]


def _world(mask: int) -> h.Graph:
    g = h.Graph()
    ids: dict[str, str] = {}
    def n(x):
        if x not in ids:
            ids[x] = g.add_node(x)
        return ids[x]
    for k, (s, p, o) in enumerate(EDGES):
        if mask >> k & 1:
            g.add_relation(n(s), p, n(o))
    return g


def _forward(mask, rules):
    g = _world(mask)
    h.run_bank(g, rules)
    return sorted({t[0] for t in h.derived_triples(g) if t[1] == "ok"})


def _demand(mask, rules):
    answers = ask_goal(_world(mask), "who ok yes", rules)
    return sorted({a.split(" ")[0] for a in answers if a != "(no answer)"})


def _push(mask, rules):
    """The PUSH entry: declare every head predicate reactive, mark the base facts as the landed events,
    fire the gate ONCE, and read what materialized. No query for `ok` — the DATA drove the cascade."""
    g = _world(mask)
    heads = {literal_name(pat.p) for r in rules for pat in r.rhs}
    for hp in heads:
        declare_reactive(g, hp)
    mark_dirty(g, [(p, o) for k, (s, p, o) in enumerate(EDGES) if mask >> k & 1])
    fire(g, rules)                                   # the reactive cascade materializes eagerly
    return sorted({t[0] for t in h.derived_triples(g) if t[1] == "ok"})


def main():
    total = agree = discriminating = 0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for shape, text in SHAPES:
            rules = load_machine_rules(text)
            saw_pos = saw_neg = False
            for mask in range(1 << len(EDGES)):
                fwd, dem, psh = _forward(mask, rules), _demand(mask, rules), _push(mask, rules)
                total += 1
                if fwd == dem == psh:
                    agree += 1
                else:
                    print(f"  DIVERGE {shape} world {mask:0{len(EDGES)}b}: "
                          f"forward={fwd} demand={dem} push={psh}")
                saw_pos |= bool(psh); saw_neg |= not psh
            if saw_pos and saw_neg:
                discriminating += 1
            print(f"  {shape:26s} swept {1 << len(EDGES)} worlds, discriminates={saw_pos and saw_neg}")
    print("=" * 66)
    print(f"three-way agreement (push==pull==forward): {agree}/{total} worlds")
    print(f"shapes that actually discriminate: {discriminating}/{len(SHAPES)}")
    go = agree == total and discriminating == len(SHAPES)
    print(f"VERDICT: {'GO - PUSH is event-triggered PULL; no divergence, no third engine' if go else 'GAP'}")


if __name__ == "__main__":
    main()

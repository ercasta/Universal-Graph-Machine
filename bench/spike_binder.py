"""BINDER SPIKE — does the SHARED cross-fact primitive need a FUNDAMENTAL engine change?

WHY THIS EXISTS. `form_inventory.md` §9.1 reduced the three unbuilt binding blocks (tense,
causation, quantification) to ONE question: can the machine BIND/RANGE across a dimension? §9.2 put
the agentic CORE of each in scope. The user's de-risking instinct: attack the shared primitive FIRST,
so if it needs a fundamental engine change that would ripple to all three, we learn it now — and
attack the PRIMITIVE, not the hardest block (tense), because tense entangles the shared risk with its
own idiosyncratic costs (ontological scope, reopened decisions).

So this spike tests the binder at the MACHINE layer (no intake), decomposed into the capabilities the
agentic cores actually need, and classifies each:

  NATIVE    — works today with existing primitives, unchanged.
  ADAPTABLE — works by composing existing primitives differently (no new engine mechanism).
  GAP       — needs a mechanism the engine does not have (a FUNDAMENTAL change; this is what ripples).

THE HYPOTHESIS UNDER TEST (stated so the run can refute it): the binder's RANGING + WITNESS machinery
is native — existential = the LHS-keyed skolem (`k?`) that `chain._resolve_skolems` re-finds on
demand; ordered = recursive traversal over a relational order (`before`), both already in the engine.
The ONE fundamental wall is RELATIVIZING A FACT to an index/context — because a fact is already the
3 slots of S-P-O, so a fact-at-t is 4-place and cannot be written without reification (rejected) or a
scope (epistemic-only today). If that holds, the shared rippling primitive is NOT "the binder" but
SCOPE generalization — which converges with the negative-band fix (a band IS a scope) and attribution.

READ THE OUTPUT AS: where is the wall, and does it ripple.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ugm import assemble_facts, derived_triples                          # noqa: E402
from ugm.apply import _fact_relnodes                                     # noqa: E402
from ugm.attrgraph import AttrGraph                                      # noqa: E402
from ugm.check import ASSUMED_NO, POSITIVE, UNKNOWN, check              # noqa: E402
from ugm.cnl.machine_rules import load_machine_rules                    # noqa: E402
from ugm.cnl.rule_graph import write_rule                               # noqa: E402
from ugm.machine import Machine                                         # noqa: E402

NATIVE, ADAPTABLE, GAP = "NATIVE", "ADAPTABLE", "GAP"


def kb(facts, rules_text=""):
    """One-graph fold: facts by the ISA fact-writer, rules written into the SAME graph.
    `facts` are 3-token strings (`"s p o"`) or triples."""
    g = AttrGraph()
    triples = [tuple(f.split()) if isinstance(f, str) else f for f in facts]
    if triples:
        Machine().run(g, assemble_facts(triples))
    for rule in load_machine_rules(rules_text):
        write_rule(g, rule)
    return g


def _pos(verdict) -> bool:
    return verdict == POSITIVE


# ---------------------------------------------------------------------------
# E — EXISTENTIAL: a witness exists (unnamed), resolved on demand
# ---------------------------------------------------------------------------

def probe_E1_existential_witness():
    """"Every locked door has SOME key that opens it" — the witness is minted on demand by the
    LHS-keyed skolem `k?`, then an existential query (`does anything open door1?`, subject unbound)
    must find it. This is the agent's normal condition: a thing exists without a name."""
    g = kb(["door1 is_a locked"], "k? opens ?d when ?d is_a locked")
    v = check(g, ("opens", None, "door1"))          # None subject = existential over the opener
    return (NATIVE if _pos(v) else GAP,
            f"exists-opener(door1) -> {v}  (skolem witness minted+found on demand)")


def probe_E2_witness_composes_downstream():
    """The unnamed witness must PARTICIPATE in further reasoning ("some key opens it, therefore it is
    accessible") — i.e. the existential binds into a downstream rule, not just answers one query."""
    g = kb(["door1 is_a locked"],
           "k? opens ?d when ?d is_a locked\n"
           "?d is_a accessible when ?k opens ?d")
    v = check(g, ("is_a", "door1", "accessible"))
    return (NATIVE if _pos(v) else GAP,
            f"accessible(door1) via the minted witness -> {v}")


# ---------------------------------------------------------------------------
# O — ORDERED: bind across an ordered index
# ---------------------------------------------------------------------------

def probe_O1_ordered_traversal():
    """The ORDER itself as relational content, traversed by a RECURSIVE rule — the ranging capability
    tense needs, tested without any fact being relativized yet. If this is native, an ordered domain
    needs no new primitive: the order is facts, traversal is recursion."""
    g = kb(["t0 before t1", "t1 before t2", "t2 before t3"],
           "?a precedes ?b when ?a before ?b\n"
           "?a precedes ?c when ?a before ?b and ?b precedes ?c")
    v = check(g, ("precedes", "t0", "t3"))
    return (NATIVE if _pos(v) else GAP,
            f"t0 precedes t3 (recursive over the order) -> {v}")


def probe_O2a_unary_state_tense():
    """A UNARY state relativized to time FITS 3-place (`lion hungry_at t1` = (lion, hungry_at, t1)),
    so a cross-index frame axiom is expressible with only entities + a rule. Tests the frame-axiom
    shape where the arity happens to fit."""
    g = kb(["lion hungry_at t1", "t1 before t2"],
           "?x dangerous_at ?u when ?x hungry_at ?t and ?t before ?u")
    v = check(g, ("dangerous_at", "lion", "t2"))
    return (NATIVE if _pos(v) else GAP,
            f"dangerous_at(lion,t2) from hungry_at(lion,t1) & t1<t2 -> {v}  "
            f"(unary-state tense fits S-P-O)")


def probe_O2b_binary_fact_relativization():
    """⭐ THE SUSPECTED FUNDAMENTAL WALL. Relativize a BINARY fact `has(lion,mane)` to time. S-P-O is
    already spent on (lion, has, mane); the index has no 4th slot. The ONLY non-reifying encoding is
    to fold the index into the object (`mane_at_t1`) or the predicate — which DESTROYS the join a rule
    needs (the rule cannot see that `mane_at_t1` and `mane_at_t2` are the same `mane` at different t,
    nor that t1<t2). This probe shows the wall by trying the object-folding encoding and asking the
    cross-index question a rule SHOULD answer.

    A GAP here is the finding that RIPPLES: relativizing a fact needs a mechanism (scope
    generalization or reification) the S-P-O substrate does not have — the same relativization the
    band already rides a scope for."""
    # object-folding: the only 3-place encoding of "has mane at t" — and it opacifies the index
    g = kb(["lion has mane_at_t1", "t1 before t2"],
           # a rule that WANTS to say: if had-mane at t and t<u then had-mane at u (persistence)
           # but it cannot bind the folded index out of `mane_at_t1`, so it cannot even be written
           # faithfully. We approximate with the naive rule and show it does not carry the index.
           "?x has mane_at_t2 when ?x has mane_at_t1")
    v = check(g, ("has", "lion", "mane_at_t2"))
    note = (f"persistence to t2 -> {v}. NOTE: this 'works' ONLY by hard-coding the two indices as "
            f"opaque objects; the rule cannot RANGE over time (no `t1<t2` join, no generality). "
            f"The faithful frame axiom over a binary fact is UNWRITABLE in 3-place.")
    # It is a GAP regardless of this verdict: even when the opaque encoding answers POSITIVE, the
    # index is not BOUND — the capability (range over the relativizing index) is absent.
    return (GAP, note)


def probe_O2c_scope_ranging_rule():
    """The other candidate encoding: relativize by SCOPE (put the fact in a time-scope), then a rule
    binds the scope as a variable and relates two scopes. Tests whether the rule language can BIND a
    scope at all. There is no scope-variable syntax in machine rules, so this is expected GAP — and it
    is the SAME missing primitive as O2b seen from the scope side."""
    # There is no way to author `fact IN ?scope` as a rule pattern — scopes are contexts the fold
    # reasons WITHIN (suppose/fork/check(scope=...)), never variables a rule ranges over.
    return (GAP, "no scope-variable in the rule language: a rule reasons WITHIN a scope, cannot BIND "
                 "one — so cross-context (cross-time, cross-holder) inference is not expressible")


# ---------------------------------------------------------------------------
# C — CAUSATION: an edge relating conditions (core) vs relating FACTS (completion)
# ---------------------------------------------------------------------------

def _relnode(g, s, p, o):
    """The nameless rel-node of the fact `s p o` (a fact is `s -[relnode:p]-> o`)."""
    for r in _fact_relnodes(g, p):
        if any(g.name(x) == s for x in g.into(r)) and any(g.name(x) == o for x in g.succ(r)):
            return r
    return None


def probe_C1_entity_level_causation():
    """CAUSATION'S CORE (§9.2): a `causes` edge between CONDITIONS/entities, reasoned over by the
    existing binder — forward inference (cause present ⇒ effect). This is the plan/diagnose-at-
    condition-level an agent needs, and it is just an ordinary relation + a rule."""
    g = kb(["lion has hunger", "hunger causes aggression"],
           "?x has ?effect when ?x has ?cause and ?cause causes ?effect")
    v = check(g, ("has", "lion", "aggression"))
    return (NATIVE if _pos(v) else GAP,
            f"has(lion,aggression) via `?cause causes ?effect` -> {v}  (condition-level cause)")


def probe_C2_facts_as_endpoints_structural():
    """Can a FACT be an endpoint of another relation (`factA causes factB`)? Structurally the fact is
    a rel-node, so an edge between two rel-nodes should be addable. But being STORED is not being
    REASONED-OVER: a causal edge invisible to the fact view is inert."""
    g = kb(["door1 is open", "cat fled yes"])
    ra, rb = _relnode(g, "door1", "is", "open"), _relnode(g, "cat", "fled", "yes")
    g.add_relation(ra, "causes", rb)
    reaches = any(o == rb and g.predicate(r) == "causes" for r, o in g.relations_from(ra))
    visible = any(t[1] == "causes" for t in derived_triples(g))
    # ADAPTABLE: the substrate PERMITS it, but it does not enter the fact view — so on its own it is
    # not yet reasoned-over. The gap is the reasoning (C3), not the storage.
    return (ADAPTABLE if reaches else GAP,
            f"factA-[causes]->factB stored={reaches}, but in the FACT VIEW={visible} (inert as-is)")


def probe_C3_propositional_modus_ponens():
    """⭐ THE CAUSATION WALL: propositional modus ponens over facts — "A holds and A causes B ⇒ B
    holds". It needs a fact to be a first-class TRUTH-BEARER (bind its 'holding', and DEREIFY it back
    to its edge to assert B). Two hard stops: the rule grammar requires every clause to be exactly
    `S P O` (so `?b holds` is unwritable), and there is no dereify operator. A DIFFERENT primitive
    from scope generalization — facts-as-truth-bearers — needed only for the causation COMPLETION.

    ⚠ SUPERSEDED 2026-07-22 — this verdict's TWO HARD STOPS were both wrong-as-stated (a 3-token
    `?s ?p ?o` clause authors fine; dereify already fires forward via MINT.key_reg). The real, narrower
    wall was PREDICATE-VARIABLE MATCHING, now BUILT: see bench/spike_facts_as_truth_bearers.py."""
    try:
        load_machine_rules("?b holds when ?a causes ?b")
        authored = True
    except ValueError:
        authored = False
    return (GAP, f"'?b holds when ?a causes ?b' authorable={authored} (rejected: clauses must be "
                 f"S-P-O). No fact-truth predicate, no dereify -> propositional cause is UNWRITABLE")


PROBES = [
    ("E1  existential witness on demand", "existential", probe_E1_existential_witness),
    ("E2  witness composes downstream", "existential", probe_E2_witness_composes_downstream),
    ("O1  ordered traversal (recursion)", "ordered-range", probe_O1_ordered_traversal),
    ("O2a unary-state tense (fits 3-place)", "relativize", probe_O2a_unary_state_tense),
    ("O2b binary-fact relativization", "relativize", probe_O2b_binary_fact_relativization),
    ("O2c scope-ranging rule", "relativize", probe_O2c_scope_ranging_rule),
    ("C1  entity-level causation (core)", "cause-entity", probe_C1_entity_level_causation),
    ("C2  facts-as-endpoints (structural)", "cause-propositional", probe_C2_facts_as_endpoints_structural),
    ("C3  propositional modus ponens", "cause-propositional", probe_C3_propositional_modus_ponens),
]


def main() -> None:
    results = [(name, cap, *fn()) for name, cap, fn in PROBES]

    print("=" * 92)
    print("BINDER SPIKE — where is the fundamental wall, and does it ripple?")
    print("=" * 92)
    mark = {NATIVE: "[+]", ADAPTABLE: "[~]", GAP: "[X]"}
    for name, cap, verdict, note in results:
        print(f"  {mark[verdict]} {verdict:9} {name:38} ({cap})")
        print(f"        {note}")
    print()

    by_cap: dict[str, list[str]] = {}
    for _n, cap, verdict, _note in results:
        by_cap.setdefault(cap, []).append(verdict)
    print("-" * 92)
    print("  CAPABILITY VERDICTS (a capability is NATIVE only if ALL its probes are):")
    for cap, vs in by_cap.items():
        overall = GAP if GAP in vs else (ADAPTABLE if ADAPTABLE in vs else NATIVE)
        print(f"      {cap:16} {overall:9}  ({', '.join(vs)})")
    print()
    gaps = [name for name, _c, v, _n in results if v == GAP]
    print("=" * 92)
    print(f"  FUNDAMENTAL GAPS (ripple risk): {len(gaps)}")
    for name, cap, v, _n in results:
        if v == GAP:
            print(f"      - {name}  [{cap}]")
    print("  Read: if the gaps cluster in ONE capability, THAT is the shared rippling primitive to")
    print("  redesign — and the other capabilities are already affordable.")


if __name__ == "__main__":
    main()

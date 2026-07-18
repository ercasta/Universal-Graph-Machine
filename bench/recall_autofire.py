"""
Probe — should RECALL fire AUTOMATICALLY on a lookup miss, or only where a rule asks for it?

THE PREMISE UNDER TEST. Associative recall is attractive as an invisible safety net: when a demand
for `cleared(cy)` finds nothing, quietly look for something *like* cy and use that instead. This
probe asks, BEFORE we build on that premise, what an automatic net actually does to answers.

WHY IT SHOULD BE SUSPECTED. UGM decides negation by negation-as-failure: a miss is not a failure
to be rescued, it IS the answer ("I looked over the closure and found nothing"). Auto-fire re-reads
every miss as "found something close enough", so any miss reached through a rule's NAC flips that
rule's firing — on evidence nobody asserted.

WHAT THIS MEASURES. The THIEF bank (tests/test_contract.py) decided by elimination: ada and bo are
cleared, so cy is the thief. We run it twice — once as the engine ships, once with `_facts_matching`
wrapped so a miss escalates to RECALL — and compare the ANSWERS. The similarity that drives the
escalation is not contrived: ada, bo and cy are all suspects, which is the strongest signal in the
bank. That is the sharp point — auto-fire is most destructive exactly where recall is most useful,
because entities worth recalling between are entities a negation is trying to distinguish.

WHAT THIS DELIBERATELY DOES NOT MEASURE. An earlier version tried to compute a corpus-wide FREQUENCY
("what share of real misses would auto-fire rescue?"). That question is not answerable from corpus/:
those banks are rule libraries, not fact bases — icecream.cnl asserts 10 facts, planning.cnl none —
so there is no population of real misses to count over. Facts arrive per session (UGM is
session-sized by design). The frequency question is left open and honest rather than answered with a
number manufactured from grammar machinery, which is what the first version accidentally did.

Run:  python bench/recall_autofire.py
"""
from __future__ import annotations

import ugm as h
from ugm import chain, near
from ugm.recall import profile


THIEF = """
    ada is a suspect
    bo is a suspect
    cy is a suspect
    bo in library
    ada is alibied
    cleared is closed world
    ?x is innocent when ?x in library
    ?x is cleared when ?x is innocent
    ?x is cleared when ?x is alibied
    ?x is thief when ?x is a suspect and ?x is not cleared
"""

QUESTIONS = ["who is thief", "is cy thief", "is ada thief", "is bo thief"]

# Similarity floor for the hypothetical auto-fire. Generous on purpose: a low bar is the most
# favourable case auto-fire could ask for, so a failure here is not a tuning problem.
THRESHOLD = 0.5


def autofire(threshold: float = THRESHOLD):
    """Wrap the shared demand lookup so a MISS escalates to associative recall: if nothing satisfies
    `pred(subj, ?)`, find nodes similar to subj that DO satisfy it, and answer as if subj did too.
    This is the throwaway implementation of the design we are testing — it exists to be measured,
    not to be kept."""
    original = chain._facts_matching
    fired: list[str] = []

    def wrapper(fact_g, pred, subj_name, obj_name, **kw):
        out = original(fact_g, pred, subj_name, obj_name, **kw)
        if out or subj_name is None:
            return out
        try:
            probes = chain._candidate_nodes(fact_g, subj_name)
        except Exception:
            return out
        for p in probes:
            for hit in near(fact_g, p, threshold=threshold):
                borrowed = original(fact_g, pred, fact_g.name(hit.nid), obj_name, **kw)
                if borrowed:
                    fired.append(f"{pred}({fact_g.name(p)}) borrowed from "
                                 f"{fact_g.name(hit.nid)} @ {hit.score:.2f} via {hit.shared}")
                    # Re-point each borrowed row at the ORIGINAL subject: the caller binds these
                    # endpoints as pointers, so the donor's own endpoint cannot be handed back.
                    return [(subj_name,) + tuple(row[1:]) for row in borrowed]
        return out

    chain._facts_matching = wrapper
    return fired, (lambda: setattr(chain, "_facts_matching", original))


def answers() -> dict[str, list[str]]:
    kb, rules = h.load_corpus(THIEF)
    return {q: h.ask_goal(kb, q, rules) for q in QUESTIONS}


def main() -> None:
    print("RECALL auto-fire probe — THIEF bank, decided by elimination\n")

    kb, _ = h.load_corpus(THIEF)
    print("  Similarity among the suspects (why auto-fire would find anything at all):")
    for name in ("cy",):
        for nid in kb.nodes_named(name):
            if profile(kb, nid):
                print(f"    profile({name}) = {profile(kb, nid)}")
                for hit in near(kb, nid, threshold=THRESHOLD):
                    print(f"      near: {kb.name(hit.nid):6} {hit.score:.2f}  {hit.shared}")
    print()

    shipped = answers()

    fired, restore = autofire()
    try:
        auto = answers()
    finally:
        restore()

    print("  ANSWERS                     as-shipped            with auto-fire")
    flips = 0
    for q in QUESTIONS:
        same = shipped[q] == auto[q]
        flips += (not same)
        mark = "  " if same else "<-- FLIPPED"
        print(f"    {q:<24} {str(shipped[q]):<21} {str(auto[q]):<21} {mark}")

    print(f"\n  escalations fired: {len(fired)}")
    for f in dict.fromkeys(fired):
        print(f"    {f}")

    print(f"\n  ANSWERS CHANGED: {flips}/{len(QUESTIONS)}")
    if flips:
        print("  Auto-fire is unsafe by construction here: the recall that fires is a TRUE similarity\n"
              "  (fellow suspects), and it still destroys the elimination. No threshold fixes this —\n"
              "  the bug is reading a miss as a failure when the miss IS the answer. RECALL stays\n"
              "  explicitly invoked.")
    else:
        print("  No answer changed — the hazard did not reproduce on this bank.")


if __name__ == "__main__":
    main()

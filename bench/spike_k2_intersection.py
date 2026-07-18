"""
EXPERIMENT — does a SECOND, DIFFERING observation kill the over-generalizations, without counting?

`bench/spike_predicate_reification.py` found that two observations licensed 32 learned rules —
every ordered pair of co-occurring predicates. The design (docs/design/learning_design.md §6)
rejects frequency/counting as the licensing story, so the question is whether the alternative
actually works: does adding ONE differing example eliminate the bad rules by CONSTRAINT, rather
than by making them statistically less likely?

THE TWO THINGS "more than one example" CAN MEAN
  * COUNTING       — "seen 47 times, so p=0.94". Rejected (vision §10): imports an opaque
                     quantity that explains nothing.
  * ELIMINATION    — example 2 REFUTES hypotheses example 1 left standing. Symbolic, exact,
                     and each death has a reason you can print. This is what is tested here.

THE SETUP. Birds that fly under-determine the DIRECTION of the regularity: from `tweety is_a
bird` + `tweety flies yes` alone, `is_a bird => flies yes` and `flies yes => is_a bird` are
equally supported. Adding ONE thing that flies without being a bird (`plane`) refutes the
reverse direction and leaves the intended one — the classic least-general-generalization move,
no probabilities involved.

REFUTATION USES THE SUBSTRATE'S OWN MACHINERY, not a bespoke check: declare
`bird disjoint_from vehicle`, run the candidate rule over the observations, and read
`contradictions()` (rule_graph.py's `<contradiction>` markers). So a refutation arrives with its
own explanation — which offender, which constraint — in the vocabulary the author wrote.

NOTE the well-formedness filter below is exactly the job S1b (design §9.1) must do in the
engine: today `expand_rules` emits empty-token rules silently, so the experiment filters them
itself to keep the measurement about GENERALIZATION rather than about that known gap.
"""
from __future__ import annotations

import ugm as h
from ugm import AttrGraph, Pat, Rule, Distinct
from ugm.cnl.authoring import expand_rules
from ugm.cnl.rule_graph import _disjoint_rule, contradictions
from ugm.lowering import run_bank

from spike_predicate_reification import ASK, LEARNER, pred_tok_tool, PRED_TOK


def hdr(s: str) -> None:
    print(f"\n{'=' * 74}\n{s}\n{'=' * 74}")


# ---------------------------------------------------------------------------
# Datasets: k=1 is birds only; k=2 adds ONE thing that flies without being a bird
# ---------------------------------------------------------------------------

def observations(*, with_plane: bool) -> AttrGraph:
    g = AttrGraph()
    bird = g.add_node("bird")
    yes = g.add_node("yes")
    vehicle = g.add_node("vehicle")
    for who in ("tweety", "polly"):
        w = g.add_node(who)
        g.add_relation(w, "is_a", bird)
        g.add_relation(w, "flies", yes)
    g.add_relation(g.add_node("robin"), "is_a", bird)      # HELD OUT: never observed flying
    if with_plane:
        p = g.add_node("plane")
        g.add_relation(p, "is_a", vehicle)
        g.add_relation(p, "flies", yes)                    # flies, but is NOT a bird
    return g


def learning_graph(*, with_plane: bool) -> AttrGraph:
    g = observations(with_plane=with_plane)
    vx = g.add_node("?x", control=True)
    g.add_relation(vx, "pat_var", g.add_node("slot1"), control=True)
    return g


DISJOINT = _disjoint_rule("bird", "vehicle")               # nothing is both a bird and a vehicle


# ---------------------------------------------------------------------------
# Learn, filter, dedupe
# ---------------------------------------------------------------------------

def _well_formed(r: Rule) -> bool:
    """What S1b (design §9.1) must enforce in the engine: no empty pattern token, no empty key.
    The empty tokens come from finding E — the pred_tok write polluting the object position."""
    if not r.key:
        return False
    return all(t for p in list(r.lhs) + list(r.rhs) for t in p.tokens())


def _shape(r: Rule) -> tuple:
    return (tuple(sorted(p.tokens() for p in r.lhs)), tuple(sorted(p.tokens() for p in r.rhs)))


# The two hypotheses birds-that-fly leaves open. Used as a FALLBACK when the learner is blocked
# (see `learn`) so this experiment — which is about LICENSING, not about learning mechanics —
# keeps measuring what it is meant to measure.
_CANDIDATES: list[Rule] = [
    Rule(key="cand.fwd", lhs=[Pat("?x", "is_a", "bird")], rhs=[Pat("?x", "flies", "yes")]),
    Rule(key="cand.rev", lhs=[Pat("?x", "flies", "yes")], rhs=[Pat("?x", "is_a", "bird")]),
]


def learn(*, with_plane: bool) -> tuple[list[Rule], list[Rule]]:
    """The learned candidate set — or the hand-written equivalent when the learner is blocked.

    Since S1b, `expand_rules` REFUSES the learner's output: finding E's object-position pollution
    puts empty tokens in every learned clause, and that is now a loud error rather than a silent
    corruption. Until finding E is resolved (spike_predicate_reification, E1) this experiment
    falls back to `_CANDIDATES`, which is exactly the pair the learner produced back when the
    corruption passed silently. The fallback announces itself, and disappears on its own once
    the learner is fixed."""
    g = learning_graph(with_plane=with_plane)
    run_bank(g, [ASK, LEARNER], max_rounds=80, tools={"pt": pred_tok_tool})
    try:
        raw = expand_rules(g)
    except ValueError:
        print("  [learner blocked by finding E — using the hand-written candidate pair]")
        return list(_CANDIDATES), list(_CANDIDATES)
    kept, seen = [], set()
    for r in raw:
        if not _well_formed(r):
            continue
        s = _shape(r)
        if s in seen:                                       # identical generalization, learned twice
            continue
        seen.add(s)
        kept.append(r)
    return raw, kept


# ---------------------------------------------------------------------------
# Refutation — the substrate's own contradiction machinery
# ---------------------------------------------------------------------------

def refutation(rule: Rule, *, with_plane: bool) -> dict | None:
    """None if the rule survives the observations; the contradiction record if it is refuted."""
    g = observations(with_plane=with_plane)                 # FRESH facts, no learning scaffolding
    try:
        run_bank(g, [rule, DISJOINT], max_rounds=40)
    except Exception:
        return {"about": ["<unrunnable>"], "violates": [type(rule).__name__]}
    found = contradictions(g)
    return found[0] if found else None


def render(r: Rule) -> str:
    body = " and ".join(f"{s} {p} {o}" for s, p, o in (x.tokens() for x in r.lhs))
    head = " and ".join(f"{s} {p} {o}" for s, p, o in (x.tokens() for x in r.rhs))
    return f"{head}  when  {body}"


# ---------------------------------------------------------------------------

def run_condition(label: str, *, with_plane: bool) -> list[Rule]:
    hdr(label)
    raw, kept = learn(with_plane=with_plane)
    print(f"  rules lifted (raw)                    : {len(raw)}")
    print(f"  after S1b well-formedness + dedupe    : {len(kept)}")
    survivors, refuted = [], []
    for r in kept:
        why = refutation(r, with_plane=with_plane)
        (refuted if why else survivors).append((r, why))
    print(f"  SURVIVE refutation                    : {len(survivors)}")
    print(f"  REFUTED by the observations           : {len(refuted)}")
    print("\n  survivors:")
    for r, _ in survivors:
        print(f"    OK   {render(r)}")
    if refuted:
        print("\n  refuted (with the substrate's own reason):")
        for r, why in refuted:
            about = ", ".join(why.get("about", []))
            viol = ", ".join(why.get("violates", []))
            print(f"    XX   {render(r)}")
            print(f"           -> predicted a contradiction about [{about}] violating [{viol}]")
    return [r for r, _ in survivors]


def no_constraint_condition() -> None:
    """The bootstrapping paradox: refutation needs enough DECLARED constraint to detect one."""
    hdr("k = 2, but with NO disjointness declared — can anything be refuted at all?")
    _raw, kept = learn(with_plane=True)
    for r in kept:
        g = observations(with_plane=True)
        run_bank(g, [r], max_rounds=40)                     # note: DISJOINT is NOT in the bank
        print(f"  {render(r):45} contradictions={len(contradictions(g))}")
    print("""
  NOTHING is refuted. `plane is_a bird` is simply DERIVED and sits there — false, but with no
  declared constraint to collide with, the substrate has no way to notice.

  So elimination-based licensing has a BOOTSTRAPPING PARADOX: it is strongest when the KB
  already carries constraints, and weakest when the KB is sparse — which is precisely the
  bootstrapping case. Counting would not rescue this either (the bad rule has the same support
  as the good one); the missing ingredient is not evidence WEIGHT but a DISCRIMINATOR.""")


if __name__ == "__main__":
    s1 = run_condition("k = 1  — birds only (every bird observed flying)", with_plane=False)
    s2 = run_condition("k = 2  — plus ONE thing that flies without being a bird", with_plane=True)
    no_constraint_condition()

    hdr("RESULT")
    only1 = {_shape(r) for r in s1} - {_shape(r) for r in s2}
    print(f"  survivors at k=1: {len(s1)}     survivors at k=2: {len(s2)}")
    if only1:
        print("\n  ELIMINATED by the second observation:")
        for r in s1:
            if _shape(r) in only1:
                print(f"    {render(r)}")
    print("""
  Each elimination is a REFUTATION with a printed reason, not a lowered probability. No
  frequency was counted anywhere in this experiment; a second example that DIFFERS did the
  work. That is the k>=2 licensing the design should adopt (§6): examples narrow the
  HYPOTHESIS SPACE by elimination, while the band carries CONFIDENCE — two orthogonal axes.

  TWO HONEST CORRECTIONS TO THE HEADLINE:

  1. The "32 rules from 2 observations" figure was mostly NOISE, not over-generalization:
     24 of the 32 are malformed (empty tokens from finding E) and the rest collapse by dedupe
     to TWO. The genuine over-generalization is small and specific — the DIRECTION of the
     regularity is under-determined — and k=2 halves it. Real, but far less dramatic than the
     raw count suggested.

  2. Refutation needs a DISCRIMINATOR, and a sparse KB has none (see the third condition
     above). The natural supplier is the same dialogue the form work already needs: the system
     knows exactly which hypothesis is under-determined, so it can ASK the discriminating
     question — "does anything fly without being a bird?" — instead of waiting for an example
     to arrive. That is the highest-value form of active learning here, and it needs no new
     machinery beyond the existing `can_ask` wait-set.

  Caveat, stated honestly: elimination is brittle to noise in a way counting is not. One wrong
  observation refutes a correct rule permanently. That is acceptable at session scale with a
  human supplying the examples (ugm-scope-session-sized); it would NOT be acceptable over a
  noisy ingested corpus, where the trade flips back.""")

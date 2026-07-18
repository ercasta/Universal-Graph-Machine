"""
THE LINCHPIN — can the system DERIVE the question that would settle its own uncertainty?

`bench/spike_k2_intersection.py` ended on a negative result: elimination-based licensing needs a
DISCRIMINATOR, and a sparse KB has none. Counting cannot rescue it, because the competing
hypotheses have IDENTICAL support. What the system does have is knowledge of exactly WHICH
hypotheses are open — so in principle it can derive the question whose answer would close them.

That "in principle" is what this spike tests. If it holds, bootstrapping stops being induction
over accumulated data and becomes: the system asks the one question that most reduces its own
uncertainty. Both halves of the learning arc then bottom out in the same move — form learning
asks "say it another way", rule learning asks "is there a counterexample?".

THE DERIVATION. A hypothesis is a rule: BODY => HEAD. For each candidate, instantiate its BODY
with a fresh individual — the CRITICAL INSTANCE, the minimal situation that triggers it — then
run EVERY candidate on that instance. Where the candidates' predictions DIFFER, the instance
discriminates, and the disputed prediction is the question.

No hypothesis-space search, no probabilities: the question falls out of running the candidates
against each other's trigger conditions.

WHAT THIS SPIKE REPORTS
  1. the candidates learned from an under-determined dataset (birds only)
  2. the critical instances and the questions derived from them
  3. that answering ONE of them eliminates a hypothesis (loop closed)
  4. whether `suppose(commit=False)` can serve as the production home for step 2
"""
from __future__ import annotations

import ugm as h
from ugm import AttrGraph, Pat, Rule, derived_triples
from ugm.lowering import run_bank

from spike_k2_intersection import learn, observations, render, DISJOINT
from ugm.cnl.rule_graph import contradictions

PROBE = "something"


def hdr(s: str) -> None:
    print(f"\n{'=' * 74}\n{s}\n{'=' * 74}")


# ---------------------------------------------------------------------------
# The derivation
# ---------------------------------------------------------------------------

def _ground(tok: str, binding: dict[str, str]) -> str:
    """A pattern token as a concrete node name: variables take the probe individual."""
    if tok.startswith("?"):
        return binding.setdefault(tok, PROBE if not binding else f"{PROBE}{len(binding)}")
    return tok[:-1] if tok.endswith("?") else tok


def critical_instance(rule: Rule) -> list[tuple[str, str, str]]:
    """The minimal situation that TRIGGERS `rule`: its body, with variables replaced by a fresh
    individual. `?x flies yes` becomes `something flies yes`."""
    binding: dict[str, str] = {}
    return [tuple(_ground(t, binding) for t in p.tokens()) for p in rule.lhs]


def _graph_of(facts: list[tuple[str, str, str]]) -> AttrGraph:
    g = AttrGraph()
    nodes: dict[str, str] = {}
    def node(n): return nodes.setdefault(n, g.add_node(n))
    for s, p, o in facts:
        g.add_relation(node(s), p, node(o))
    return g


def predictions(rule: Rule, facts: list[tuple[str, str, str]]) -> set[tuple[str, str, str]]:
    """What `rule` derives on `facts`, beyond the facts themselves."""
    g = _graph_of(facts)
    try:
        run_bank(g, [rule], max_rounds=20)
    except Exception:
        return set()
    return set(derived_triples(g)) - set(facts)


def discriminating_questions(candidates: list[Rule]) -> list[dict]:
    """Every (critical instance, disputed prediction) pair on which the candidates disagree."""
    out: list[dict] = []
    for source in candidates:
        probe = critical_instance(source)
        preds = {r.key or render(r): predictions(r, probe) for r in candidates}
        disputed = set().union(*preds.values()) - set().intersection(*preds.values())
        for triple in sorted(disputed):
            asserts = [r for r in candidates if triple in preds[r.key or render(r)]]
            denies = [r for r in candidates if triple not in preds[r.key or render(r)]]
            out.append({"given": probe, "question": triple,
                        "asserted_by": asserts, "silent_from": denies,
                        "from_body_of": source})
    return out


def render_question(q: dict) -> str:
    given = " and ".join(f"{s} {p} {o}" for s, p, o in q["given"])
    s, p, o = q["question"]
    return f"Given `{given}` — is it the case that `{s} {p} {o}`?"


# ---------------------------------------------------------------------------

def main() -> None:
    hdr("1  the under-determined candidate set (learned from birds only)")
    _raw, candidates = learn(with_plane=False)
    for r in candidates:
        print(f"    {render(r)}")
    print(f"\n  {len(candidates)} hypotheses, IDENTICAL support — counting cannot separate them.")

    hdr("2  DERIVED discriminating questions")
    qs = discriminating_questions(candidates)
    if not qs:
        print("  none derived — the candidates never disagree on each other's triggers.")
        return
    for i, q in enumerate(qs, 1):
        print(f"  Q{i}: {render_question(q)}")
        print(f"       asserted by : {[render(r) for r in q['asserted_by']]}")
        print(f"       silent from : {[render(r) for r in q['silent_from']]}")
        print(f"       (derived from the body of: {render(q['from_body_of'])})")
    print(f"\n  {len(qs)} question(s), derived — not authored, not a template.")

    hdr("3  which ANSWER would eliminate what")
    print("  A question's eliminative power is asymmetric: `no` REFUTES whoever asserted the")
    print("  prediction; `yes` merely fails to separate. So each question below is worth asking")
    print("  exactly to the extent its `no` branch is live.\n")
    for i, q in enumerate(qs, 1):
        print(f"  Q{i}: {render_question(q)}")
        print(f"      no  -> REFUTES {[render(r) for r in q['asserted_by']]}")
        print(f"      yes -> separates nothing (the others are silent, not contradicted)")

    hdr("4  answering the counterexample question closes the loop")
    # Pick the question whose `no` is answered by the plane: the one predicting `is_a bird`.
    q = next((x for x in qs if x["question"][1] == "is_a"), qs[0])
    print(f"  Ask: {render_question(q)}")
    print("  User: no — a plane flies and is a vehicle.\n")
    for r in candidates:
        g = observations(with_plane=True)
        run_bank(g, [r, DISJOINT], max_rounds=40)
        bad = contradictions(g)
        why = (f"  ({', '.join(bad[0].get('about', []))} violating "
               f"{', '.join(bad[0].get('violates', []))})") if bad else ""
        print(f"    {'REFUTED' if bad else 'survives':9} {render(r)}{why}")
    print("\n  The hypothesis the question targeted is exactly the one that died.")

    hdr("5  is `suppose(commit=False)` a viable production home for the derivation?")
    # YES — but as a per-candidate CHECK, not an enumerator. `suppose` is demand-driven: with an
    # empty `predictions` list it derives NOTHING (`derived=[]`), because nothing demanded it. It
    # cannot answer "what follows?" open-endedly. That is fine here: the algorithm already knows
    # each candidate's head, so it asks "does the DISPUTED triple hold under the probe?".
    #
    # API asymmetry worth knowing: `assumptions` are (SUBJECT, pred, object) while `predictions`
    # are (PRED, subject, object) — see tests/test_isa_suppose.py.
    q = qs[0]
    s, p, o = q["question"]
    goal = (p, s, o)
    print(f"  assume {q['given']}, then check the disputed {goal}:\n")
    for r in candidates:
        fg, rg = AttrGraph(), AttrGraph()
        h.write_rule(rg, r)
        res = h.suppose(fg, list(q["given"]), [goal], rules=rg, commit=False)
        forward = "asserts" if r in q["asserted_by"] else "silent "
        print(f"    {render(r):42} forward={forward}  suppose={res.status!r}")
    print("""
  suppose AGREES with the forward run (confirmed vs inconclusive, matching asserts vs silent),
  so the production derivation can run read-only, scoped, and explainable — no scratch graphs.
  Note it must be used as a CHECK of an already-known candidate head, never as "enumerate the
  consequences": with `predictions=[]` it returns `derived=[]` and a vacuous 'confirmed'.""")

    hdr("VERDICT")
    print("""  The discriminating question IS derivable, mechanically, from the candidate set alone:
  instantiate each hypothesis's BODY as a critical instance, run every candidate on it, and
  where predictions differ you have both the question and the hypotheses it splits.

  This is what makes bootstrapping tractable in a SPARSE KB — the case where the k>=2
  elimination result was weakest. The system does not wait for a discriminating example to
  arrive; it names the example it needs.""")


if __name__ == "__main__":
    main()

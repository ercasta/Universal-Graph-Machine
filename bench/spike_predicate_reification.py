"""
WALL-FINDING SPIKE — predicate reification via a `<call>` calculator, and whether a learner
and the rule it learns can coexist in one bank. (Learning arc S3/S5 risk, docs/design/learning_design.md §4.)

Investigation script (`python bench/spike_predicate_reification.py`), not a test.

THE QUESTION. `learning_design.md` §4 recommends reifying a predicate — a graded KEY on a
relation node — into a nameable token node via a `<call>` calculator, so a learner can point
`k_pred` at a predicate it merely OBSERVED. That was a recommendation on architectural grounds
(zero storage, in the ISA's grain) and had never been executed. This spike executes it.

FINDINGS
  A. THE WALL. A rule that WRITES A BOUND RELATION NODE AS AN OBJECT never reaches fixpoint.
     Mechanism (isolated in `wall_isolation`): a pattern's subject is reached by FOLLOW-in from
     its relation node, so once `<call> --arg--> R` exists, that new `arg` relation ALSO points
     at R and therefore binds as the SUBJECT of the very pattern that produced it. One extra
     binding per round, forever. Fuel (`max_rounds`) is the only thing that stops it, so the
     rule silently produces garbage rather than failing.
     NOT fixed by `control_preds`, and NOT fixed by `provenance=True` (both tried).
     This is NOT specific to learning: it is a general consequence of reified relations —
     pointing at a relation node makes the pointer indistinguishable from a subject.

  B. THE WORKAROUND (and therefore the design change). The calculator must take an ENTITY and
     enumerate that entity's own relations, writing `rel --pred_tok--> token` itself. A tool
     write is not a rule write, so nothing re-enters the match loop as a subject. Terminates
     flat, and yields exactly what §4 wanted: nodes NAMED after observed predicates.
     => §4's `pred_tok(relation)` signature is WRONG; it must be `pred_tok(entity)`.

  C. A learner can then key `k_pred` off an OBSERVED predicate (`learner`), and the resulting
     rules lift and run. Learner + learned COEXIST in one bank without a stratification cycle,
     but see the printed caveat about how many rules one observation licenses.

  D. TOOLS ARE SERVICED ONLY AT QUIESCENCE (`lowering.run_bank`: `if not pending:`). So a
     non-terminating rule STARVES the dispatcher — during the wall above the calculator was
     never invoked at all. Any guard that depends on a tool's output therefore cannot fix a
     runaway that precedes it (chicken-and-egg); the termination has to be structural.

  E. THE TOOL'S OWN WRITE POLLUTES THE OBJECT POSITION — a MILDER instance of A, and the
     residue the workaround leaves behind. `rel --pred_tok--> token` gives the relation node an
     out-edge, so `g.out(is_a_rel)` becomes {bird, pred_tok_rel} and any pattern reading
     `?s ?p ?o` binds `?o` to the (unnamed) pred_tok relation node as well as to `bird`.
     Bounded, not runaway — but it silently yields learned rules with EMPTY tokens
     (`('?x','flies','')`), visible in section C's output.

     And `expand_rules` emits those without complaint. **S1 hardened `rules_in_graph` (the
     FACT-SHAPED reader) but the learning target is the FLAT schema, whose reader has no
     equivalent validation.** The loudness work is therefore only half done; the flat reader
     needs the same treatment (call it S1b) BEFORE a learner ships, or every learner bug will
     surface as a silently-empty pattern token.
"""
from __future__ import annotations

import ugm as h
from ugm import AttrGraph, Pat, Rule, Distinct, derived_triples
from ugm.cnl.authoring import expand_rules
from ugm.dispatch import call_arg
from ugm.lowering import run_bank
from ugm.production_rule import stratify

PRED_TOK = "pred_tok"


def hdr(s: str) -> None:
    print(f"\n{'=' * 74}\n{s}\n{'=' * 74}")


def observations() -> AttrGraph:
    g = AttrGraph()
    bird, yes = g.add_node("bird"), g.add_node("yes")       # intern once (add_node always mints)
    for who in ("tweety", "polly"):
        w = g.add_node(who)
        g.add_relation(w, "is_a", bird)
        g.add_relation(w, "flies", yes)
    g.add_relation(g.add_node("robin"), "is_a", bird)
    vx = g.add_node("?x", control=True)                     # the pattern-variable pool
    g.add_relation(vx, "pat_var", g.add_node("slot1"), control=True)
    return g


# ---------------------------------------------------------------------------
# A — the wall, isolated
# ---------------------------------------------------------------------------

def wall_isolation() -> None:
    hdr("A  THE WALL: writing a bound RELATION NODE as an object never reaches fixpoint")
    cases = {
        "var-pred LHS, plain RHS       ": Rule(
            key="a", lhs=[Pat("?x", "is_a", "bird"), Pat("?x", "?p", "?o")],
            rhs=[Pat("?x", "touched", "yes")]),
        "var-pred LHS, writes ?p (REL) ": Rule(
            key="b", lhs=[Pat("?x", "is_a", "bird"), Pat("?x", "?p", "?o")],
            rhs=[Pat("<call>?", "tool", "t"), Pat("<call>?", "arg", "?p")]),
        "var-pred LHS, writes ?x (ent) ": Rule(
            key="c", lhs=[Pat("?x", "is_a", "bird"), Pat("?x", "?p", "?o")],
            rhs=[Pat("<call>?", "tool", "t"), Pat("<call>?", "arg", "?x")]),
        "no var-pred, writes ?x        ": Rule(
            key="d", lhs=[Pat("?x", "is_a", "bird")],
            rhs=[Pat("<call>?", "tool", "t"), Pat("<call>?", "arg", "?x")]),
    }
    for label, r in cases.items():
        fires = [run_bank(observations(), [r], max_rounds=mr) for mr in (1, 3, 10)]
        verdict = "RUNAWAY" if fires[2] > fires[1] else "terminates"
        print(f"  {label} firings@rounds(1,3,10)={fires}  {verdict}")
    print("\n  Only the case that writes a RELATION NODE runs away. Neither guard helps:")
    r = cases["var-pred LHS, writes ?p (REL) "]
    cp = frozenset({"tool", "arg"})
    for label, kw in (("control_preds", dict(control_preds=cp)),
                      ("provenance   ", dict(provenance=True)),
                      ("both         ", dict(control_preds=cp, provenance=True))):
        fires = [run_bank(observations(), [r], max_rounds=mr, **kw) for mr in (1, 3, 10)]
        print(f"    with {label}: firings@(1,3,10)={fires}")
    print("\n  => and because tools are serviced only at QUIESCENCE (run_bank `if not pending:`),")
    print("     the calculator is never invoked at all while this runs. Finding D.")


# ---------------------------------------------------------------------------
# B — the calculator that works: entity in, tokens out
# ---------------------------------------------------------------------------

def pred_tok_tool(graph, call_id):
    """`pred_tok(entity)` — mint/intern a node NAMED after each predicate the entity participates
    in, and wire `rel --pred_tok--> token`. Takes an ENTITY, never a relation node (finding A).

    The interning matters: `add_node` always mints, so without the reuse scan every call would
    make a fresh `is_a` node and learned rules would not converge on one token."""
    ent = call_arg(graph, call_id, "arg")
    if ent is None:
        return set()
    touched: set[str] = set()
    for rel, _obj in list(graph.relations_from(ent)):
        pred = graph.predicate(rel)
        if not pred or pred == PRED_TOK:
            continue
        existing = [n for n in graph.nodes_named(pred) if graph.is_control(n)]
        tok = existing[0] if existing else graph.add_node(pred, control=True)
        touched |= {tok, graph.add_relation(rel, PRED_TOK, tok, control=True)}
    return touched


ASK = Rule(key="ask.predtok",
           lhs=[Pat("?x", "is_a", "bird")],
           rhs=[Pat("<call>?", "tool", "pt"), Pat("<call>?", "arg", "?x")])


def calculator_works() -> AttrGraph:
    hdr("B  THE WORKAROUND: pred_tok(ENTITY) reifies observed predicates and terminates")
    for mr in (3, 10, 30):
        g = observations()
        fires = run_bank(g, [ASK], max_rounds=mr, tools={"pt": pred_tok_tool})
        toks = sorted({g.name(o) for s in g.nodes() for rel, o in g.relations_from(s)
                       if g.predicate(rel) == PRED_TOK})
        print(f"  rounds={mr:3} firings={fires:3} predicate TOKENS reified={toks}")
    print("  => `is_a` and `flies` are now NODES, discovered from the graph, not pre-interned.")
    return g


# ---------------------------------------------------------------------------
# C — a learner keyed off an OBSERVED predicate
# ---------------------------------------------------------------------------

# Reads relation nodes (safe), writes only TOKEN nodes (the discipline finding A imposes).
LEARNER = Rule(
    key="learn.observed",
    lhs=[Pat("?s", "is_a", "?k"),                       # ground anchor
         Pat("?s", "?p1", "?k1"), Pat("?p1", PRED_TOK, "?t1"),
         Pat("?s", "?p2", "?o"), Pat("?p2", PRED_TOK, "?t2"),
         Pat("?v", "pat_var", "slot1")],
    distinct=[Distinct("?p1", "?p2")],
    rhs=[Pat("<lrule>?", "rl_key", "?k1"),
         Pat("<lrule>?", "rl_lhs", "<cbody>?"),
         Pat("<cbody>?", "k_subj", "?v"),
         Pat("<cbody>?", "k_pred", "?t1"),              # <- an OBSERVED predicate
         Pat("<cbody>?", "k_obj", "?k1"),
         Pat("<lrule>?", "rl_head", "<chead>?"),
         Pat("<chead>?", "k_subj", "?v"),
         Pat("<chead>?", "k_pred", "?t2"),              # <- an OBSERVED predicate
         Pat("<chead>?", "k_obj", "?o")],
)


def learner_runs() -> list[Rule]:
    hdr("C  a learner keyed off OBSERVED predicates")
    g = observations()
    fires = run_bank(g, [ASK, LEARNER], max_rounds=50, tools={"pt": pred_tok_tool})
    print(f"  bank firings (ask + learner, one bank): {fires}")
    try:
        lifted = expand_rules(g)
    except Exception as e:
        print(f"  expand_rules RAISED {type(e).__name__}: {e}")
        return []
    print(f"  expand_rules lifted {len(lifted)} rule(s):")
    for r in lifted:
        print(f"    key={r.key!r}  {[p.tokens() for p in r.lhs]} -> {[p.tokens() for p in r.rhs]}")
    print("\n  CAVEAT — note how many rules ONE observation licenses: the learner generalizes")
    print("  every ordered pair of co-occurring predicates. This is the over-generalization the")
    print("  design's §6.3/§11 flags, and it is the concrete argument for requiring k>=2 examples")
    print("  as CONSTRAINT INTERSECTION (which of these survive a second, differing observation?).")
    return lifted


def stratification_coexistence(lifted: list[Rule]) -> None:
    hdr("C2  do learner and learned rule coexist in ONE bank?")
    if not lifted:
        print("  (nothing lifted)")
        return
    bank = [ASK, LEARNER] + lifted
    try:
        strata = stratify(bank)
        print(f"  stratify OK: {len(strata)} stratum/strata, sizes={[len(s) for s in strata]}")
        for i, s in enumerate(strata):
            print(f"    stratum {i}: {[r.key for r in s]}")
    except ValueError as e:
        print(f"  stratify REFUSED (negation cycle): {e}")
        return
    g = observations()
    fires = run_bank(g, bank, max_rounds=50, tools={"pt": pred_tok_tool})
    print(f"  combined bank ran to fixpoint: {fires} firings (no runaway)")
    facts = sorted(t for t in derived_triples(g) if t[0] == "robin")
    print(f"  facts about robin (never observed flying): {facts}")


if __name__ == "__main__":
    wall_isolation()
    calculator_works()
    lifted = learner_runs()
    stratification_coexistence(lifted)
    hdr("VERDICT")
    print("""  S3 is BUILDABLE, but §4 of the design needs one correction:
    * `pred_tok` takes an ENTITY, not a relation node. The relation-node signature is a
      NON-TERMINATION wall, not a preference (finding A).
    * General discipline for every learner: READ relation nodes freely, but NEVER write one
      as the object of a rule-minted relation.
    * Tools are serviced only at quiescence, so termination must be structural, never a
      guard that depends on the tool's own output (finding D).
    * The tool's own write still pollutes the OBJECT position (finding E), producing learned
      rules with empty tokens that `expand_rules` accepts silently. S1's loudness work covered
      the fact-shaped reader; the FLAT reader — the one learning actually targets — still
      needs it. That is a prerequisite, not a polish item.""")

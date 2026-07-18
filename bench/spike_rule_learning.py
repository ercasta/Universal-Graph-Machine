"""
SPIKE — can a RULE write a RULE that the engine then runs? (rule learning, Brick 1)

Investigation script in the `bench/` tradition (cf. recall_autofire.py): it answers a design
question empirically and prints its findings. Not a test — nothing here is asserted as a
contract; `python bench/spike_rule_learning.py` and read the output.

THE QUESTION. Learning a rule from observation needs the RHS of some rule to write structure
that a lifter turns back into an executable `Rule`. This repo has TWO rule reifications, and
the spike's central finding is that they differ exactly on whether a learner can write them:

  A. FACT-SHAPED  (rule_graph.write_rule / rules_in_graph)
     a pattern atom is the 2-hop path  subj --> [rel node keyed by pred] --> obj,
     and the role edge points at the MIDDLE node.
     -> NOT learner-writable: an RHS has no way to NAME the relation node it just created,
        so it cannot wire `rule --lhs--> thatRelNode`.

  B. FLAT  (authoring.expand_rules, the CNL fold's own schema)
     a pattern atom is a `<cond>` node with three ORDINARY edges k_subj / k_pred / k_obj.
     -> IS learner-writable: `<cond>` is a nameable skolem and each edge is a plain triple.

So rule learning should be built on (B). Layers below establish that step by step.

WHAT IS ALREADY THERE (spike says yes):
  L0  the round-trip landing pad: write a rule as graph data, lift it, run it (one-graph fold)
  L1  pattern VARIABLES: a control node NAMED "?x" is bindable by a rule through a marker,
      so a learner refers to a pattern variable without ever writing "?x" as a token
  L2  the fact-shaped schema is a wall (and fails BADLY — see the loudness note)
  L3  the flat schema works: a rule writes a rule and `expand_rules` lifts it
  L4  ...and the learned rule FIRES on unseen data, once its predicate token exists

WHAT IS MISSING (the one new primitive):
  L5  PREDICATE REIFICATION. A predicate is a graded KEY on a relation node
      ({'is_a': Attr(graded, 1.0)}), not a node — `nodes_named('is_a')` is empty. A learner
      therefore has nothing to point `k_pred` at for a predicate it OBSERVED rather than one
      an author interned in advance. Bridging this is what makes a learner general.
"""
from __future__ import annotations

import ugm as h
from ugm import AttrGraph, Pat, Rule, check, derived_triples
from ugm.cnl.authoring import expand_rules
from ugm.lowering import run_bank


def hdr(s: str) -> None:
    print(f"\n{'=' * 72}\n{s}\n{'=' * 72}")


def observations(g: AttrGraph) -> AttrGraph:
    """Two birds observed flying, and a third bird we have said nothing about.

    NOTE `add_node` always MINTS — calling it twice for "bird" makes two distinct nodes and a
    literal pattern then matches only one of them. Intern shared objects once (this bit us
    twice while writing the spike; it is a fixture discipline, not an engine defect)."""
    bird, yes = g.add_node("bird"), g.add_node("yes")
    for who in ("tweety", "polly"):
        w = g.add_node(who)
        g.add_relation(w, "is_a", bird)
        g.add_relation(w, "flies", yes)
    g.add_relation(g.add_node("robin"), "is_a", bird)
    return g


# The rule we want the system to LEARN:  ?x flies yes  when  ?x is_a bird
TARGET = Rule(key="learned.birds_fly",
              lhs=[Pat("?x", "is_a", "bird")],
              rhs=[Pat("?x", "flies", "yes")])


# ---------------------------------------------------------------------------
def L0_landing_pad() -> None:
    """Rules ARE graph data already, in the same graph as the facts, and they run."""
    hdr("L0  landing pad: write_rule -> rules_in_graph -> fires  (one-graph fold)")
    g = observations(AttrGraph())
    h.write_rule(g, TARGET)
    lifted = h.rules_in_graph(g)
    print(f"  lifted: {[(r.key, [p.tokens() for p in r.lhs], [p.tokens() for p in r.rhs]) for r in lifted]}")
    # goal tuple is (PREDICATE, subject, object) — not S-P-O
    print(f"  check(flies robin yes) = {check(g, ('flies', 'robin', 'yes'))}")
    print("  => a learned rule has somewhere to land, and needs no separate bank.")


# ---------------------------------------------------------------------------
def L1_variable_pool() -> None:
    """A pattern VARIABLE the learner can refer to without typing '?x' as a token."""
    hdr("L1  pattern variables: an interned control node NAMED '?x'")
    g = observations(AttrGraph())
    vx = g.add_node("?x", control=True)
    g.add_relation(vx, "pat_var", g.add_node("slot1"), control=True)
    run_bank(g, [Rule(key="probe", lhs=[Pat("?v", "pat_var", "slot1")],
                      rhs=[Pat("?v", "reached", "yes")])])
    hit = [s for s, p, o in derived_triples(g) if p == "reached"]
    print(f"  a rule bound the pattern-var node: {hit}")
    print("  => variables are ordinary (control) data; the learner binds them via a marker.")


# ---------------------------------------------------------------------------
def L2_fact_shaped_wall() -> None:
    """The fact-shaped schema cannot be written by an RHS — and fails badly when tried."""
    hdr("L2  WALL: the fact-shaped schema (write_rule / rules_in_graph)")
    g = observations(AttrGraph())
    # An RHS *can* write the role edge...
    run_bank(g, [Rule(key="learn.naive", lhs=[Pat("?x", "is_a", "bird")],
                      rhs=[Pat("mynewrule", "lhs", "myatom")])])
    print(f"  RHS wrote the role edge: {('mynewrule', 'lhs', 'myatom') in derived_triples(g)}")
    # ...but the role edge must point at a 2-hop pattern ATOM, and the RHS cannot build one,
    # because it has no handle on the relation node it creates.
    try:
        h.rules_in_graph(g)
        print("  rules_in_graph: (unexpectedly fine)")
    except Exception as e:
        print(f"  rules_in_graph RAISED {type(e).__name__}: {str(e)[:100]}...")
        print("  (S1, BUILT: this is now a loud ValueError naming the rule and role. Before the")
        print("   fix it was a bare `IndexError: list index out of range` from _read_pat.)")
    # The skolem spelling writes PERFECTLY WELL — the fragment is just not readable as a rule.
    g2 = observations(AttrGraph())
    n0 = set(g2.nodes())
    run_bank(g2, [Rule(key="learn.skolem", lhs=[Pat("?x", "is_a", "bird")],
                       rhs=[Pat("<newrule>?", "lhs", "<atom>?")])])
    minted = set(g2.nodes()) - n0
    print(f"  the skolem spelling minted {len(minted)} nodes and wrote its role edge:"
          f" {('<newrule>', 'lhs', '<atom>') in derived_triples(g2)}")
    print("  So the RHS is not powerless — it writes fine, and mints one fragment PER MATCH.")
    print("  What it cannot do is build the 2-hop atom the role edge must point at, because it")
    print("  has no handle on the relation node it creates. => use the FLAT schema instead.")


# ---------------------------------------------------------------------------
# The LEARNER, as an ordinary rule over the FLAT schema.
#   observed:  ?s is_a ?k   and   ?s flies yes
#   learn:     ?x flies yes  when  ?x is_a ?k
#
# `<lrule>?` / `<cbody>?` / `<chead>?` are bound-literal skolems ANCHORED to the LHS match,
# so they mint one node per firing (verified: distinct ids per match, not one shared node).
LEARNER = Rule(
    key="learn.generalize",
    lhs=[Pat("?s", "is_a", "?k"),
         Pat("?s", "flies", "yes"),
         Pat("?v", "pat_var", "slot1"),          # the pattern variable node ("?x")
         Pat("?isa", "pred_tok", "is_a_slot"),   # token nodes NAMED after the predicates
         Pat("?fl", "pred_tok", "flies_slot")],  # (L5: today these must be pre-interned)
    rhs=[Pat("<lrule>?", "rl_key", "?k"),        # key the learned rule by what it generalizes
         Pat("<lrule>?", "rl_lhs", "<cbody>?"),
         Pat("<cbody>?", "k_subj", "?v"),
         Pat("<cbody>?", "k_pred", "?isa"),
         Pat("<cbody>?", "k_obj", "?k"),
         Pat("<lrule>?", "rl_head", "<chead>?"),
         Pat("<chead>?", "k_subj", "?v"),
         Pat("<chead>?", "k_pred", "?fl"),
         Pat("<chead>?", "k_obj", "yes")],
)


def _learner_graph() -> AttrGraph:
    g = observations(AttrGraph())
    vx = g.add_node("?x", control=True)
    g.add_relation(vx, "pat_var", g.add_node("slot1"), control=True)
    # L5's workaround: intern a NODE named after each predicate, because the substrate stores
    # predicates as graded KEYS on relation nodes and offers no node to point `k_pred` at.
    for pred, slot in (("is_a", "is_a_slot"), ("flies", "flies_slot")):
        g.add_relation(g.add_node(pred, control=True), "pred_tok",
                       g.add_node(slot, control=True), control=True)
    return g


def L3_rule_writes_rule() -> list[Rule]:
    """THE RESULT: a rule writes a rule, and expand_rules lifts it into an executable Rule."""
    hdr("L3  a rule writes a rule (flat schema) and expand_rules lifts it")
    g = _learner_graph()
    run_bank(g, [LEARNER])
    lifted = expand_rules(g)
    print(f"  expand_rules lifted {len(lifted)} rule(s):")
    for r in lifted:
        print(f"    key={r.key!r}  {[p.tokens() for p in r.lhs]} -> {[p.tokens() for p in r.rhs]}")
    print("  NOTE the learner fired once per observation (tweety, polly), so an identical rule")
    print("  is learned twice. Dedupe/merge is a design decision, not an engine limit — cf.")
    print("  form_authoring.merge_forms (same key + identical rule = no-op; different = loud).")
    return lifted


# ---------------------------------------------------------------------------
def L4_learned_rule_fires(lifted: list[Rule]) -> None:
    """The loop closes: the LEARNED rule generalizes to an entity never observed flying."""
    hdr("L4  the learned rule fires on unseen data")
    if not lifted:
        print("  (nothing lifted)")
        return
    g = AttrGraph()
    g.add_relation(g.add_node("robin"), "is_a", g.add_node("bird"))
    run_bank(g, lifted[:1])
    print(f"  facts about robin after running the LEARNED rule: {sorted(derived_triples(g))}")
    print("  => 'robin flies' was never observed; the learned rule derived it.")


# ---------------------------------------------------------------------------
def L5_the_missing_primitive() -> None:
    """The one thing that must be built: predicates are keys, not nodes."""
    hdr("L5  THE GAP: predicate reification")
    g = AttrGraph()
    rel = g.add_relation(g.add_node("tweety"), "is_a", g.add_node("bird"))
    print(f"  relation node {rel}: predicate()={g.predicate(rel)!r} name()={g.name(rel)!r}")
    print(f"  attrs: {dict(g._nodes[rel].attrs)}")
    print(f"  nodes_named('is_a') = {g.nodes_named('is_a')}")
    try:
        run_bank(g, [Rule(key="refl", lhs=[Pat("?s", "?p", "?o")], rhs=[Pat("?p", "is_rel", "yes")])])
    except Exception as e:
        print(f"  reflecting a rel node RAISED {type(e).__name__}: {e}")
    print("  Also, writing a variable predicate on the RHS is an explicit deferral:")
    g2 = observations(AttrGraph())
    try:
        run_bank(g2, [Rule(key="varpred", lhs=[Pat("?x", "is_a", "bird"), Pat("?x", "?p", "?o")],
                           rhs=[Pat("copycat", "?p", "?o")])])
    except Exception as e:
        print(f"    {type(e).__name__}: {e}")
    print()
    print("  => L3's learner had to PRE-INTERN a node per predicate. To learn a rule about a")
    print("     predicate it merely OBSERVED, the learner needs a way to get from a matched")
    print("     relation to a nameable token for its predicate. That is the new primitive.")


if __name__ == "__main__":
    L0_landing_pad()
    L1_variable_pool()
    L2_fact_shaped_wall()
    lifted = L3_rule_writes_rule()
    L4_learned_rule_fires(lifted)
    L5_the_missing_primitive()
    hdr("VERDICT")
    print("""  Rule learning does NOT need a new subsystem. It needs:
    1. the FLAT reification as the learning target (already the CNL fold's own schema)
    2. an interned pattern-variable pool  (works today, L1)
    3. PREDICATE REIFICATION               (the one missing primitive, L5)
    4. dedupe/merge semantics for learned keys (design choice; merge_forms is the precedent)
    5. loud diagnostics for malformed learned fragments  (S1 — BUILT, see
       tests/test_rule_fragment_loudness.py)""")

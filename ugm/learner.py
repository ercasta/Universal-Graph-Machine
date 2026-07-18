"""
Rule learning — a rule that writes a rule (learning arc S5, docs/design/learning_design.md).

Promoted from `bench/spike_rule_learning.py` and `bench/spike_predicate_reification.py`, which
established the shape empirically. The pieces and why each is the way it is:

THE TARGET IS THE FLAT SCHEMA (§3). A learned rule is written as `<rule> -rl_head/rl_lhs-> <cond>`
with `k_subj`/`k_pred`/`k_obj`, the CNL fold's own schema, and lifted by `expand_rules`. The
fact-shaped schema (`write_rule`/`rules_in_graph`) is NOT writable by a rule at all — an RHS has no
way to name the relation node it creates — so learning could never have targeted it.

PATTERN VARIABLES ARE INTERNED DATA (§5.3). A control node literally NAMED `?x`, reached through a
`pat_var` marker, so the learner refers to a pattern variable without ever writing `?x` as a token
(which the engine would read as a variable, not a name).

PREDICATES ARE REIFIED BY A CALCULATOR, ENTITY-KEYED (§4.1). A predicate is a graded KEY on a
relation node, not a node, so a learner has nothing to point `k_pred` at for a predicate it merely
OBSERVED. `pred_tok_tool` interns one. It takes an ENTITY, never a relation node: passing a
relation node makes the rule non-terminating (an `<call> --arg--> R` edge also points at R, so it
binds as the SUBJECT of the pattern that produced it — one extra binding per round, forever).

THE PREDICATE TOKEN IS JOINED BY VALUE, NOT BY EDGE (§9.1a). Linking `rel --pred_tok--> token` with
an edge is readable-and-polluting or (inert) invisible-to-the-learner-too; no flag setting works.
Instead both the relation and its token carry the same VALUED `pred_name`, joined by a declared
`ValueMatch`. An attribute is not an edge, so `FOLLOW` never traverses it — the join cannot pollute
by construction. GENERAL RULE, worth remembering beyond this module: to associate metadata with a
RELATION node, use a valued attribute plus a declared join, never an edge.

LEARNING IS INVOKED, NOT AMBIENT. Only entities marked `observe` are generalized from — the
agent-not-theorem-prover stance. Which predicates are learnable is likewise controlled in ONE
place: `pred_tok_tool` interns tokens only for domain predicates, so the learner's value-join
simply finds nothing for scaffolding and no post-filter is needed.

WHAT IS NOT HERE. Nothing decides whether a learned rule is any GOOD — that is licensing, and it
lives elsewhere on purpose: elimination by counterexample and the derived discriminating question
(§6.2b/§6.2c, `bench/spike_k2_intersection.py`, `bench/spike_discriminating_question.py`), plus
query-time provisionality (`ugm/learned.py`). This module only proposes.
"""
from __future__ import annotations

from .attrgraph import AttrGraph, valued
from .cnl.authoring import expand_rules
from .dispatch import call_arg
from .lowering import run_bank
from .production_rule import Distinct, Pat, Rule, ValueMatch, stratify

# --- the learning vocabulary (all ordinary control data, no engine privilege) ---------------
OBSERVE = "observe"         # marker: generalize from this entity
PRED_NAME = "pred_name"     # VALUED join dimension, carried by BOTH a relation and its token
PAT_TOK = "pat_tok"         # marker relation putting a predicate token in the bindable pool
TOK_POOL = "<tokpool>"      # the node every predicate token is marked against
PAT_VAR = "pat_var"         # marker relation putting a pattern variable in the pool
VAR_SLOT = "<varslot>"      # the node every pattern variable is marked against
PATTERN_VAR = "?x"          # the interned pattern variable (a node NAMED "?x")
TOOL_NAME = "pred_tok"

# Scaffolding predicates are never reified, so the learner's value-join finds no token for them and
# they cannot appear in a learned rule. ONE place decides what is learnable.
SCAFFOLD = frozenset({OBSERVE, PAT_TOK, PAT_VAR, PRED_NAME})


# ---------------------------------------------------------------------------
# The calculator: entity in, interned predicate tokens out
# ---------------------------------------------------------------------------

def pred_tok_tool(graph, call_id):
    """`pred_tok(entity)` — for each domain predicate the entity participates in, tag the relation
    with a VALUED `pred_name` and intern a control node NAMED that predicate carrying the same
    `pred_name`, so a rule can join them by `ValueMatch`.

    NO EDGE IS EVER ADDED TO A RELATION NODE (see module docstring). Interning matters too:
    `add_node` always mints, so without the reuse scan each call would make a fresh `is_a` node and
    learned rules would not converge on one token."""
    ent = call_arg(graph, call_id, "arg")
    if ent is None:
        return set()
    pool = _intern(graph, TOK_POOL)
    touched: set[str] = set()
    for rel, _obj in list(graph.relations_from(ent)):
        pred = graph.predicate(rel)
        if not pred or pred in SCAFFOLD:
            continue
        graph.set_attr(rel, PRED_NAME, valued(pred))
        existing = [n for n in graph.nodes_named(pred) if graph.is_control(n)]
        if existing:
            tok = existing[0]
        else:
            tok = graph.add_node(pred, control=True)
            graph.set_attr(tok, PRED_NAME, valued(pred))
            graph.add_relation(tok, PAT_TOK, pool, control=True)
        touched |= {tok, rel}
    return touched


def _intern(graph: AttrGraph, name: str) -> str:
    """Get-or-create a control node by name (`add_node` always mints, so reuse must be explicit)."""
    existing = [n for n in graph.nodes_named(name) if graph.is_control(n)]
    return existing[0] if existing else graph.add_node(name, control=True)


# ---------------------------------------------------------------------------
# The rules
# ---------------------------------------------------------------------------

REIFY = Rule(
    key="learn.reify",
    lhs=[Pat("?x", OBSERVE, "?m")],
    rhs=[Pat("<call>?", "tool", TOOL_NAME), Pat("<call>?", "arg", "?x")],
)

# Generalize a co-occurrence: an observed entity standing in TWO different relations yields
# "?x <p2> <o> when ?x <p1> <k>". Both predicates come from the graph, not from this source file.
COOCCURRENCE = Rule(
    key="learn.cooccurrence",
    lhs=[Pat("?s", OBSERVE, "?om"),
         Pat("?s", "?p1", "?k"), Pat("?t1", PAT_TOK, "?pm1"),
         Pat("?s", "?p2", "?o"), Pat("?t2", PAT_TOK, "?pm2"),
         Pat("?v", PAT_VAR, "?vm")],
    value_matches=[ValueMatch("?p1", "?t1", PRED_NAME),      # the token OF relation ?p1
                   ValueMatch("?p2", "?t2", PRED_NAME)],
    distinct=[Distinct("?p1", "?p2")],
    rhs=[Pat("<lrule>?", "rl_key", "?k"),                    # keyed by what it generalizes (§5.2)
         Pat("<lrule>?", "rl_learned", "?om"),               # the learner stamps its own output
         Pat("<lrule>?", "rl_lhs", "<cbody>?"),
         Pat("<cbody>?", "k_subj", "?v"),
         Pat("<cbody>?", "k_pred", "?t1"),
         Pat("<cbody>?", "k_obj", "?k"),
         Pat("<lrule>?", "rl_head", "<chead>?"),
         Pat("<chead>?", "k_subj", "?v"),
         Pat("<chead>?", "k_pred", "?t2"),
         Pat("<chead>?", "k_obj", "?o")],
)

LEARNER_BANK: list[Rule] = [REIFY, COOCCURRENCE]


# A DISCREPANCY invokes learning on the step that failed (S6). `discrepancy` is already a fact the
# planner derives (corpus/procedure.cnl) — "this step reported done but its effect never
# materialized" — so failure becomes a learning trigger with one rule and no new signal.
#
# THIS IS A TRIGGER, NOT A LEARNER, AND ON ITS OWN IT IS NOT ENOUGH. Measured: generalizing from a
# failed step ALONE yields 12 candidates, all junk ("anything done has a discrepancy"), because one
# failure has no CONTRAST — everything true of the failed step looks equally implicated. Contrast
# with a succeeded step refutes a third of them (`ugm/licensing.py`), and the remainder are
# genuinely undecidable on that evidence: closing THAT gap is the discriminating question. So use
# this with `licensing.refute` and expect to still be asking.
DISCREPANCY_TRIGGER = Rule(
    key="learn.on_discrepancy",
    lhs=[Pat("?o", "discrepancy", "?e")],
    rhs=[Pat("?o", OBSERVE, "<observed>?")],
)


# ---------------------------------------------------------------------------
# The entry point
# ---------------------------------------------------------------------------

def prepare(graph: AttrGraph) -> None:
    """Intern the pattern-variable pool. Idempotent; safe to call per learn."""
    slot = _intern(graph, VAR_SLOT)
    var = _intern(graph, PATTERN_VAR)
    if not any(graph.predicate(r) == PAT_VAR for r, _o in graph.relations_from(var)):
        graph.add_relation(var, PAT_VAR, slot, control=True)


def observe(graph: AttrGraph, *entity_names: str) -> None:
    """Mark entities as learning subjects. Learning is INVOKED, never ambient."""
    marker = _intern(graph, "<observed>")
    for name in entity_names:
        for nid in graph.nodes_named(name):
            if not any(graph.predicate(r) == OBSERVE for r, _o in graph.relations_from(nid)):
                graph.add_relation(nid, OBSERVE, marker, control=True)


def learn(graph: AttrGraph, *, max_rounds: int = 80, dedupe: bool = True) -> list[Rule]:
    """Generalize from the entities marked `observe`, returning the learned rules.

    Runs the reification pass and the learner over ONE bank (they stratify together — verified),
    lifts through `expand_rules` (which since S1b REFUSES a fragment that would reflect to a
    silently-broken rule), and returns rules already marked `learned=True` via `rl_learned`.

    `dedupe` collapses rules with an identical pattern shape: keying by what a rule GENERALIZES
    means two observations supporting the same generalization produce the same rule, so folding
    them is idempotent rather than lossy (§5.2)."""
    prepare(graph)
    run_bank(graph, LEARNER_BANK, max_rounds=max_rounds, tools={TOOL_NAME: pred_tok_tool})
    rules = [r for r in expand_rules(graph) if r.learned and not _touches_scaffolding(r)]
    if not dedupe:
        return rules
    out, seen = [], set()
    for r in rules:
        shape = (tuple(sorted(p.tokens() for p in r.lhs)),
                 tuple(sorted(p.tokens() for p in r.rhs)))
        if shape in seen:
            continue
        seen.add(shape)
        out.append(r)
    return out


def _touches_scaffolding(rule: Rule) -> bool:
    """Does any slot of `rule` mention a reserved `<…>` token?

    The SCAFFOLD predicate list is not sufficient on its own, and real data is what showed it: the
    coreference layer marks entities `is_a <mention>`, whose PREDICATE (`is_a`) is perfectly
    ordinary and whose scaffolding lives in the OBJECT. Learning over a graph built by `ingest`
    therefore proposed `?x is_a <mention> when …` until this filter existed. The toy fixtures never
    caught it because they were built with raw `add_relation` and never went through intake —
    a reminder that hand-built fixtures agree with whatever you assumed while building them."""
    return any(t.startswith("<") and t.endswith(">")
               for p in list(rule.lhs) + list(rule.rhs) for t in p.tokens())


def accept(existing: list[Rule], learned: list[Rule]) -> tuple[list[Rule], list[Rule]]:
    """Split `learned` into (accepted, refused) against the stratification gate (§8).

    A learned rule can trivially create a negative cycle, and that must be caught AT LEARN TIME
    rather than surfacing later as a dropped-NAF degradation warning. Candidates are tried one at
    a time so ONE bad rule does not refuse the whole batch."""
    accepted, refused = list(existing), []
    for r in learned:
        try:
            stratify(accepted + [r])
        except ValueError:
            refused.append(r)
            continue
        accepted.append(r)
    return accepted[len(existing):], refused

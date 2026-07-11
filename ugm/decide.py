"""
Forcing a decision — negation decided-on-demand, per tuple (memory
`decision_forcing_a_decision`; vision §11, refining stratified negation).

The static `stratify` schedule + a NAC is the old way to negate: a rule with `not urgent` is
delayed until every producer of `urgent` has quiesced, then reads the ABSENCE of `urgent`. This
module is the other way — negation MATERIALIZED as an explicit, defeasible `is_not` fact that
consumers match POSITIVELY:

  1. COMPLETION. A closed-world `is not P` clause reflects (authoring.expand_rules) to a positive
     `?c is_not P` consumer condition PLUS a generated COMPLETION rule — a NAC rule
     (`completion_rule`): `?c is_not P  when  <positive residual>  and  P closes <closed_world>,
     NOT ?c is P`. The NAC on `?c is P` forces the rule into a stratum AFTER P's producers (that
     IS the sound "producers first" timing, for free), so it materializes `?c is_not P` exactly for
     the demanded, closed-world tuples whose positive could not be derived. No tool, no `<decide>`
     token — completion is an ordinary stratified rule.

  2. DEFEAT (defeasible). The materialized negative is CONTROL: new information can make `?c is P`
     derivable, which must withdraw `?c is_not P` and everything it fed. When a positive coexists
     with a stale completed negative, `DEFEAT_SEED` fires and seeds `<retract> targets` on the
     negative; `retraction.RETRACT_RULES` then cascade-hides it (by `rewire` interposition) — the
     truth-maintenance layer, itself expressed as meta-rules over matchable provenance. `solve`
     runs derivation+completion (provenance ON) then, if any defeat was seeded, the retraction
     pass (provenance OFF, the regress guard).

Why COMPLETION is load-bearing (not just an optimization): forcing the POSITIVE is
completeness-under-laziness (matching before a producer ran only MISSES a derivation — monotone,
never wrong); forcing the NEGATIVE is SOUNDNESS (materializing `is_not P` before the producers
finished would be a WRONG answer). So completion is licensed only for a CLOSED-WORLD predicate
(per-predicate DATA: `P closes <closed_world>`; open-world exhaustion is UNKNOWN — never
materialize the negative) and only at the producers' fixpoint (the NAC-induced stratum boundary).

Scope: the decided predicate is a UNARY copula property — `P(c) == c is P` (positive `is`, negative
`is_not`). Generalizing to an arbitrary binary relation `R(c, o)` is a mechanical extension (mirror
the object). No domain predicate name is hardcoded; the closed-world marker and the residual are
read from the graph.
"""
from __future__ import annotations

from . import provenance as prov
from . import retraction as ret
from .production_rule import Pat, Rule
from .world_model import Graph

# Substrate copula/CWA vocabulary — single source of truth in `ugm.vocabulary` (Phase 2.5);
# re-exported here so existing `decide.COPULA`/`decide.CWA`/… references stay valid.
from .vocabulary import CWA, CLOSES, COPULA, NEG_COPULA


def _ensure(graph: Graph, name: str) -> str:
    found = graph.nodes_named(name)
    return found[0] if found else graph.add_node(name)


# ---------------------------------------------------------------------------
# CLOSED_WORLD — per-predicate policy, stored as DATA
# ---------------------------------------------------------------------------

def declare_closed_world(graph: Graph, prop: str) -> str:
    """Record that property `prop` is CLOSED-WORLD: completion may license `is_not prop` when
    `is prop` cannot be derived. Wires `prop --closes--> <closed_world>` onto the shared concept
    node named `prop`. Idempotent. (Normally authored in CNL: `prop is closed world`.)"""
    concept = _ensure(graph, prop)
    marker = _ensure(graph, CWA)
    if not _rel_exists(graph, concept, CLOSES, marker):
        graph.add_relation(concept, CLOSES, marker)
    return concept


def is_closed_world(graph: Graph, prop: str) -> bool:
    """Is property `prop` declared closed-world? (Open-world -> completion never fires.)"""
    return any(node_is_closed_world(graph, c) for c in graph.nodes_named(prop))


def closed_predicates(graph: Graph) -> frozenset[str]:
    """Every concept/predicate name declared CLOSED-WORLD (`name --closes--> <closed_world>`). Under
    CWA-DEFAULT (`decision-cwa-default`, reversing the earlier OWA-default) closed-world is now the
    QUERY default, so `ask_goal` no longer reads this for the yes/no verdict — it reads `open_preds`
    (the OWA opt-in). This marker now drives only the REASONING-side aggressive `is_not` COMPLETION
    (`decide.solve`'s elimination riddles), i.e. it says "this predicate's extension is KB-determined,
    so complete its negation," distinct from the query default."""
    return frozenset(graph.name(n) for n in graph.nodes()
                     if node_is_closed_world(graph, n) and not graph.is_inert(n))


def node_is_closed_world(graph: Graph, node: str) -> bool:
    """Does THIS concept node carry the closed-world marker (`node --closes--> <closed_world>`)?
    What the CNL reflection reads to decide whether a rule's `is not P` clause is a closed-world
    negation (→ a completion rule) or ordinary NAF (a stratified NAC)."""
    for r in graph.out(node):
        if graph.has_key(r, CLOSES):
            if any(graph.name(o) == CWA for o in graph.out(r)):
                return True
    return False


# ---------------------------------------------------------------------------
# Positive / negative atom existence (readers)
# ---------------------------------------------------------------------------

def _rel_exists(graph: Graph, s: str, pred: str, o: str) -> bool:
    for r in graph.succ(s):
        if graph.has_key(r, pred) and o in graph.succ(r):
            return True
    return False


def _holds(graph: Graph, subj: str, pred: str, prop_name: str) -> bool:
    """Does `subj --[pred]--> (some live node named prop_name)` exist?"""
    for r in graph.succ(subj):
        if graph.has_key(r, pred):
            for o in graph.succ(r):
                if graph.name(o) == prop_name:
                    return True
    return False


def positive_holds(graph: Graph, subj: str, prop_name: str) -> bool:
    return _holds(graph, subj, COPULA, prop_name)


def negative_holds(graph: Graph, subj: str, prop_name: str) -> bool:
    return _holds(graph, subj, NEG_COPULA, prop_name)


# ---------------------------------------------------------------------------
# COMPLETION — the generated NAC rule that materializes the negative (the sound step)
# ---------------------------------------------------------------------------

def completion_rule(subject: str, prop: str, trigger: list[Pat], key: str) -> Rule:
    """The completion rule for a closed-world `is not prop` clause on variable `subject`.

    Materializes `subject is_not prop` for every tuple matching the consumer's positive residual
    `trigger` (which binds `subject`) where `prop` is closed-world. It is AGGRESSIVE and MONOTONE —
    NO NAC on `subject is prop`. A NAC would be the natural "unless the positive is derivable" guard,
    but it makes completion depend negatively on the copula `is`, which the consumer also produces
    (`?x is thief`) — an object-blind stratification FALSE-CYCLE through the overloaded copula (the
    "predicate-NAME granularity" gotcha, and the reason `decide` originally used a Python fixpoint).

    So instead: complete unconditionally, then let DEFEAT repair. Where the positive IS derivable,
    `is prop` and this `is_not prop` coexist -> `DEFEAT_SEED` seeds a retract and `RETRACT_RULES`
    cascade-hides the over-completed negative and anything it fed (the mirror of aggressive-retract
    + re-derive). Correct final state, monotone completion, no stratification cycle. The CWA marker
    clause gates it on the closed-world declaration and anchors matching on the rare `closes`
    predicate."""
    return Rule(
        key=key,
        lhs=[*trigger, Pat(f"{prop}?", CLOSES, CWA)],       # positive residual + CWA gate
        rhs=[Pat(subject, NEG_COPULA, prop)],               # materialize the explicit negative
    )


# ---------------------------------------------------------------------------
# DEFEAT — a positive that coexists with a completed negative defeats it (defeasible TMS)
# ---------------------------------------------------------------------------
#
# A completion holds by the ABSENCE of the positive. If new information later makes `?c is ?p`
# derivable while a stale `?c is_not ?p` from an earlier round survives, the negative is DEFEATED.
# This seed rule detects the coexistence and marks the negative RELATION node for retraction; the
# generic `retraction.RETRACT_RULES` cascade-hide it and everything it fed. The negative fact is
# the visible completion (the inert `unless` bookkeeping is retired) — a live `?c is ?p` next to a
# live `?c is_not ?p` for the same tuple is exactly "a defeater now holds".

DEFEAT_SEED = Rule(
    key="decide.defeat.seed",
    lhs=[Pat("?c", COPULA, "?p"),                           # the positive is derivable ...
         Pat("?c", f"{NEG_COPULA}?", "?p")],                # ... and a completed negative coexists
    rhs=[Pat(f"{ret.RETRACT}?", ret.TARGETS, f"{NEG_COPULA}?")],   # -> retract the negative relation node
)


# ---------------------------------------------------------------------------
# The reasoning driver — derivation + completion, then (if defeated) retraction
# ---------------------------------------------------------------------------

def solve(graph: Graph, rules: list, *, tools: dict | None = None, strict: bool = False) -> list:
    """Run `rules` to a combined fixpoint of monotone deduction and decided negation.

    Phase 1 (provenance ON): the domain rules, the generated COMPLETION rules (already in `rules`,
    from the reflection), and `DEFEAT_SEED` run stratified — producers derive, completion
    materializes the negatives, and a defeat is SEEDED where a positive coexists with a stale
    negative. Phase 2 (provenance OFF, the regress guard): iff a `<retract>` was seeded, the
    retraction meta-rules (`retraction.RETRACT_RULES`) cascade-hide the defeated negatives (and
    their consequences) by interposition.

    In a fresh single solve of a consistent theory NO defeat is seeded — completion and its
    positive are mutually exclusive (the completion NAC blocks where the positive holds) — so
    phase 2 is a no-op and this behaves as a single `run_rules`. Returns the firing journal."""
    from .cnl.authoring import run_rules

    journal = run_rules(graph, [*rules, DEFEAT_SEED], tools=tools, strict=strict)
    if graph.nodes_named(ret.RETRACT):                      # a defeat was seeded -> retract
        # Phase 2 on the ISA forward driver (INTERPOSE opcode); phase 1's provenance
        # is read by run_bank's per-rule inert-visible CASCADE match (Phase 0.5).
        journal += run_rules(graph, ret.RETRACT_RULES, provenance=False)
    return journal

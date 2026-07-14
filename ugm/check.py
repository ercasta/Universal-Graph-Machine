"""
Phase 5.1 — CHECK (firmware v2, `processing_modes.md` mode 4): "looking for something and possibly
not finding it." A bounded, demand-driven completion that returns one of FOUR statuses under the
CWA-default query model (`decision-cwa-default`), with a renderable "where I looked" trace.

CHECK runs CHAIN (`chain_sip`, the bounded demand-driven prover) for the goal, then reads the outcome:

  - POSITIVE     — the goal is derivable (`yes`).
  - ENTAILED_NEG — the goal is NOT derivable but its NEGATIVE (`pred_not`) IS: a HARD `no`, as
                   trustworthy as a `yes` (e.g. from disjointness — `universal.entailed_negation`).
  - ASSUMED_NO   — neither is derivable and the concept is CLOSED-WORLD (the default): a DEFEASIBLE
                   "no, to the best of current knowledge" (CWA). Revisable; NOTHING is materialized
                   or retracted for it (§5-safe), it is a verdict computed from the demand closure.
  - UNKNOWN      — neither is derivable and the concept is OPEN-WORLD (the per-predicate opt-in,
                   `open_preds`): absence is not taken as false — gather evidence instead.

This is the firmware realization of `query.ask_goal`'s verdict (which uses `GoalSolver` and COLLAPSES
the three negatives to `no`/`no`/`unknown`); CHECK keeps the KIND distinct — the signal the
metareasoning/escalation layer needs — and renders the completion's "where I looked" from the visible
`<demand>` magic set (`chain.render_demands`), which is exactly what makes an assumed-no explainable
in a way exhaustive systems cannot (`processing_modes.md` §3).

v1 SCOPE (positive core + copula negation): the negative predicate is `pred + "_not"` (`is`->`is_not`,
the established `decide.NEG_COPULA` convention; general `R_not` mirrors it); ENTAILED_NEG fires only
where the bank actually has negative-producing rules/facts (in a purely-positive bank, goals resolve
POSITIVE or ASSUMED_NO). Bounded by `chain_sip`'s fuel/round budget.
"""
from __future__ import annotations

from dataclasses import replace

from .attrgraph import AttrGraph
from .chain import chain_sip, _facts_matching, render_demands, _Exhaustion
from .policy import FirmwarePolicy, DEFAULT_POLICY

# The four CHECK statuses (decision-cwa-default's 4-status model).
POSITIVE = "positive"          # derivable -> yes
ENTAILED_NEG = "entailed-no"   # the negative is derivable -> a HARD no
ASSUMED_NO = "assumed-no"      # CWA default: closed-world, unprovable -> a DEFEASIBLE no
UNKNOWN = "unknown"            # open-world, unprovable -> gather

# Substrate copula/negation vocabulary — single source of truth in `ugm.vocabulary` (Phase 2.5).
# `_neg_pred` (the `is`->`is_not`; `R`->`R_not` convention) is re-exported here so `suppose.py`'s
# `from .check import _neg_pred` stays valid.
from .vocabulary import COPULA, neg_pred as _neg_pred


def _present(fact_g: AttrGraph, goal: tuple[str, str | None, str | None], *,
             scope: str | None = None) -> bool:
    """Is any fact matching the (possibly wildcarded) `goal` present? (∃ for a free endpoint.)
    Within a SUPPOSE/read-only `scope`, that scope's pencil facts count as present too."""
    pred, subj, obj = goal
    return bool(_facts_matching(fact_g, pred, subj, obj, scope=scope))


def _concept_key(pred: str, obj: str | None) -> str:
    """Openness is a property of the CONCEPT: for a copula goal `is(S, C)` it is the object concept C
    (`C is open world`), not the shared copula; for a relational goal it is the predicate. Mirrors
    `query.ask_goal`'s `concept_key` so the firmware verdict matches the reference exactly."""
    return obj if (pred == COPULA and obj is not None) else pred


def check(fact_g: AttrGraph, goal: tuple[str, str | None, str | None], *,
          rules: AttrGraph | None = None,
          policy: FirmwarePolicy = DEFAULT_POLICY, open_preds: frozenset[str] | None = None,
          provenance: bool = False, max_rounds: int = 1000, on_subgoal=None,
          focus_scope: frozenset[str] | None = None, scope: str | None = None) -> str:
    """CHECK `goal` and return one of POSITIVE / ENTAILED_NEG / ASSUMED_NO / UNKNOWN. Runs CHAIN for
    the positive (bounded); if absent, runs CHAIN for the negative; if that too is absent, the
    `policy`'s negation default holds — ASSUMED_NO (closed-world) unless the concept is OPEN under the
    policy (`unknown`). Only the derivable facts are materialized (monotone, §5-safe); the assumed-no
    is a computed verdict, not a write.

    STANCE AS DATA (`policy.py`): the closed-vs-open reading of absence is the firmware's OPINION, not
    the engine's — carried on `policy` (`FirmwarePolicy`), swappable for an alternative firmware.
    `open_preds=` is kept as a convenience: it folds into the default closed-world policy as the OWA
    exception set (so every existing caller behaves identically).

    FUEL → UNKNOWN (firmware v3): the closures are bounded by `max_rounds`. If the POSITIVE closure did
    not reach fixpoint within budget (or a NAC's nested negative demand didn't — the `_Exhaustion` flag
    bubbles up), absence is NOT trustworthy, so the honest verdict is UNKNOWN ("I did not finish
    looking"), NOT a decided no. This is the distinction the forward exhaustive model cannot make; it
    is why demand-driven NAF is the agent-not-theorem-prover model, not merely an optimization.

    `scope` (feedback #12): reason inside a pencil scope — derivations are scope-tagged control
    (visible in-scope, never ink), the same mechanism SUPPOSE uses. This is what `ask_goal`'s
    read-only mode threads through."""
    rule_g = rules if rules is not None else fact_g        # one-graph default (the fold)
    if open_preds is not None:
        policy = replace(policy, open_preds=frozenset(open_preds))
    pred, subj, obj = goal
    fuel = _Exhaustion()
    chain_sip(fact_g, goal, rules=rule_g, provenance=provenance,    # demand-driven positive
              max_rounds=max_rounds, _fuel=fuel, focus_scope=focus_scope, scope=scope,
              on_subgoal=on_subgoal)
    if _present(fact_g, goal, scope=scope):
        return POSITIVE
    if fuel.exhausted:                                              # ran out of fuel before closure ->
        return UNKNOWN                                             # honest "didn't finish", not a no
    neg = (_neg_pred(pred), subj, obj)
    chain_sip(fact_g, neg, rules=rule_g, provenance=provenance,    # is the HARD negative entailed?
              max_rounds=max_rounds, _fuel=fuel, focus_scope=focus_scope, scope=scope,
              on_subgoal=on_subgoal)
    if _present(fact_g, neg, scope=scope):
        return ENTAILED_NEG
    if fuel.exhausted:
        return UNKNOWN
    return UNKNOWN if policy.is_open(_concept_key(pred, obj)) else ASSUMED_NO


def collapse(status: str) -> str:
    """The yes/no/unknown an actor acts on — `query.ask_goal`'s verdict. The KIND (hard ENTAILED_NEG
    vs defeasible ASSUMED_NO) is the finer signal the metareasoning/escalation layer reads; both are
    `no` to a caller that only needs the decision."""
    return {POSITIVE: "yes", ENTAILED_NEG: "no", ASSUMED_NO: "no", UNKNOWN: "unknown"}[status]


def explain_check(status: str, rule_g: AttrGraph) -> list[str]:
    """RECORD the CHECK as CNL: the verdict plus 'where I looked' (the visible `<demand>` magic set the
    completion explored). This is what makes a NEGATIVE answer honest and renderable — "assumed no: I
    looked for X and Y within budget and found nothing" — not a claim about the universe."""
    head = {
        POSITIVE: "yes — derivable",
        ENTAILED_NEG: "no — the negative is entailed (a hard no)",
        ASSUMED_NO: "assumed no — closed-world default, and the goal was not derivable",
        UNKNOWN: "unknown — open-world, and neither the goal nor its negative was derivable",
    }[status]
    return [head, "  looked for:"] + [f"    {ln}" for ln in render_demands(rule_g)]

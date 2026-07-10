"""
Phase 5.5 (slice 1) — firmware MODES as §8 `<call>` calculators (the "run as control-token programs"
primitive KB procedures compose). A composition/bridge layer (like `procedure.py`): it couples the
`isa` firmware modes with the engine's `<call>` boundary (`dispatch.py`), so it lives at this level,
not inside the `isa` core (importing `dispatch` from inside `isa` would close an import cycle through
`world_model`).

A reasoning MODE (CHECK/CHOOSE/… — the firmware-v2 verbs) is invoked the SAME way a tool is: a rule
(or a KB procedure step) MATERIALIZES a `<call>` control node naming the mode, with argument slots,
and the engine's dumb dispatcher (`dispatch.service_calls`) services it — runs the mode, folds its
verdict back as a node, consumes the call. This is `decision-agentic-direction`'s "tools as
calculators" applied to the modes themselves: a mode is a calculator the substrate invokes at the
point a verdict is needed; WHICH mode fires and WHEN is decided by the rules/procedure that emit the
call (DATA), never by the dispatcher (which stays content-blind).

Why this and not a bespoke Python driver: the plan's §5.5 says "run as control-token programs … the
loop already exists — reuse, don't rebuild." The `<call>` boundary IS that loop (`dispatch.py`,
`decision-materialized-tool-calls`); a mode-call is just another token in it. A procedure that
composes CHECK/CHOOSE steps (slice 2) lays down these calls; plan→act→check→replan (ITERATE×CHECK)
reads as a loop that emits a CHECK call per expected effect and branches on the `<check>` verdict.

SLICE 1 SCOPE: the CHECK mode as a call (goal in → a `<check>` verdict node out). The verdict is a
CONTROL node (reserved `<check>` syntax) carrying the goal + one of the four CHECK statuses as VALUED
attrs, so a downstream control rule can branch on it while it stays invisible to fact matching. The
mode handler CLOSES OVER the rule bank (`rule_g`) — the calculator's fixed knowledge — and reads the
goal from the call's slots (the per-invocation arguments). CHOOSE/SUPPOSE calls + the procedure CNL
surface that emits them are the next slices.
"""
from __future__ import annotations

from .dispatch import call_arg, service_calls, Tool
from .attrgraph import AttrGraph, valued
from .check import check, COPULA
from .choose import choose, winners_of, SATISFIED_BY

# Tool names (the `<call> --tool--> NAME` object). One per firmware mode.
CHECK_TOOL = "check"
CHOOSE_TOOL = "choose"

# Argument slots a mode-call carries (slot -> a name node). A CHECK goal is (pred, subj, obj); subj/obj
# may be omitted for a wildcard endpoint. A CHOOSE call names a GOAL node (its candidates already
# registered via `set_candidate`) and an optional ALPHA cut.
PRED, SUBJ, OBJ = "pred", "subj", "obj"
GOAL, ALPHA = "goal", "alpha"

# The verdict node a CHECK call emits: a CONTROL `<check>` token carrying the goal + status. Two
# VIEWS, one node: (a) VALUED attrs (`pred`/`subj`/`obj`/`status`) for the Python reader
# (`check_results`); (b) CONTROL RELATIONS `<check> -[status]-> STATUS` and `<check> -[of]-> SUBJ`
# so a downstream forward RULE can MATCH the verdict and react (the plan→act→check feedback, 3a) —
# control-stamped, so they drive control rules but stay invisible to fact reasoning.
CHECK_RESULT = "<check>"
STATUS = "status"
OF = "of"


def _slot_name(g: AttrGraph, call_id: str, slot: str) -> str | None:
    """The NAME in argument `slot` of the call (goal endpoints are names), or None if absent."""
    nid = call_arg(g, call_id, slot)
    return g.name(nid) if nid is not None else None


def _ensure(g: AttrGraph, name: str) -> str:
    found = g.nodes_named(name)
    return found[0] if found else g.add_node(name)


def _control_rel(g: AttrGraph, subj: str, pred: str, obj: str) -> str:
    """Mint `subj -[pred]-> obj` and CONTROL-stamp it — verdict scaffolding a control rule matches
    but fact reasoning ignores (the `<check>` verdict emanates from control, so its edges are control)."""
    rid = g.add_relation(subj, pred, obj)
    g.set_control(rid, True)
    return rid


def check_tool(rule_g: AttrGraph, *, open_preds: frozenset[str] = frozenset(),
               provenance: bool = False) -> Tool:
    """A `<call>`-serviceable CHECK calculator over the fixed rule bank `rule_g`. Reads the goal
    (`pred`/`subj`/`obj` slots) from the call, runs the firmware `check`, and EMITS a `<check>`
    verdict node carrying the goal + status. Returns the emitted node id so the engine re-seeds."""
    def handler(g: AttrGraph, call_id: str) -> set[str]:
        # The goal PREDICATE defaults to the COPULA (`is`) when the call omits a `pred` slot —
        # ergonomics for the common copula check. A RELATIONAL predicate carried as a literal
        # (`<call> -[pred]-> eats`) is now sound: the key-aware INTERN fix (machine.py,
        # finding-interning-aliases-predicate-literals) keeps that literal from aliasing the `eats`
        # predicate rel node, so a rule may carry any goal predicate (slice 3b).
        subj_id = call_arg(g, call_id, SUBJ)
        pred = _slot_name(g, call_id, PRED) or COPULA
        obj = _slot_name(g, call_id, OBJ)
        subj = g.name(subj_id) if subj_id is not None else None
        status = check(g, rule_g, (pred, subj, obj), open_preds=open_preds, provenance=provenance)
        res = g.add_node(CHECK_RESULT)                     # reserved `<…>` -> a CONTROL token
        g.set_attr(res, PRED, valued(pred))                # VALUED view (the Python reader)
        if subj is not None:
            g.set_attr(res, SUBJ, valued(subj))
        if obj is not None:
            g.set_attr(res, OBJ, valued(obj))
        g.set_attr(res, STATUS, valued(status))
        touched = {res, _control_rel(g, res, STATUS, _ensure(g, status))}   # matchable verdict relation
        if subj_id is not None:                            # correlate the verdict to the goal subject
            touched.add(_control_rel(g, res, OF, subj_id))
        return touched
    return handler


def choose_tool(*, default_alpha: float = 0.0) -> Tool:
    """A `<call>`-serviceable CHOOSE calculator. Reads the GOAL node (its candidates already registered
    via `set_candidate`) and an optional ALPHA cut from the call, runs the firmware `choose` (α-cut +
    argmax), and marks the winner(s) `goal -[satisfied_by]-> winner` in the graph (choose's own output,
    read back via `winners_of` / `choice_results`). Needs no rule bank — CHOOSE is a pure graded
    comparison over candidate fits. Returns the winner node ids so the engine re-seeds."""
    def handler(g: AttrGraph, call_id: str) -> set[str]:
        goal = call_arg(g, call_id, GOAL)                  # a NODE id (not a name — CHOOSE goal is a node)
        if goal is None:
            return set()
        a = _slot_name(g, call_id, ALPHA)
        try:
            alpha = float(a) if a is not None else default_alpha
        except ValueError:
            alpha = default_alpha
        return set(choose(g, goal, alpha=alpha))
    return handler


def mode_registry(rule_g: AttrGraph, *, open_preds: frozenset[str] = frozenset(),
                  provenance: bool = False) -> dict[str, Tool]:
    """The firmware-mode tool registry for `dispatch.service_calls` — the modes a control-token
    program may invoke, over the fixed rule bank `rule_g`. CHECK (goal→verdict) + CHOOSE (goal→winner).
    SUPPOSE is a PROCEDURE construct, not a single call (its assumptions/predictions are variable-length
    lists — a scope the CNL surface lays down, slice 3), so it is deliberately not registered here. The
    dispatcher routes a `<call>` to the named mode and consumes it (content-blind)."""
    return {
        CHECK_TOOL: check_tool(rule_g, open_preds=open_preds, provenance=provenance),
        CHOOSE_TOOL: choose_tool(),
    }


def check_results(g: AttrGraph) -> list[dict[str, str]]:
    """Read every `<check>` verdict currently in `g` as `{pred, subj?, obj?, status}` dicts — the
    'what the program checked and found' view a procedure step / the plan-act-check loop branches on."""
    out: list[dict[str, str]] = []
    for res in g.nodes_named(CHECK_RESULT):
        rec: dict[str, str] = {}
        for k in (PRED, SUBJ, OBJ, STATUS):
            a = g.get_attr(res, k)
            if a is not None:
                rec[k] = str(a.value)
        if PRED in rec and STATUS in rec:
            out.append(rec)
    return out


def choice_results(g: AttrGraph) -> dict[str, list[str]]:
    """Read every CHOOSE outcome (`goal -[satisfied_by]-> winner`) as `{goal_name: [winner_names]}` —
    the 'what the program chose' view, the CHOOSE analog of `check_results`. Winners are sorted for a
    stable read (a tie yields several)."""
    out: dict[str, list[str]] = {}
    for rel in g.nodes_named(SATISFIED_BY):
        goal = next((n for n in g.into(rel) if not g.is_inert(n)), None)
        winner = next((n for n in g.out(rel) if not g.is_inert(n)), None)
        if goal is not None and winner is not None:
            out.setdefault(g.name(goal), []).append(g.name(winner))
    return {k: sorted(v) for k, v in out.items()}


def service_modes(fact_g: AttrGraph, rule_g: AttrGraph, *,
                  open_preds: frozenset[str] = frozenset(), provenance: bool = False) -> set[str]:
    """Service every pending mode `<call>` in `fact_g` over `rule_g` (convenience wrapper around
    `dispatch.service_calls` with the mode registry). Returns the touched node ids."""
    return service_calls(fact_g, mode_registry(rule_g, open_preds=open_preds, provenance=provenance))

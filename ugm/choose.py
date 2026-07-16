"""
Phase 5.2 — CHOOSE (firmware v2, `processing_modes.md` mode 5): "comparing options and picking."
Enumerate candidate options for a goal, α-cut by graded fit, and select the best by graded comparison
— the deterministic stable pick (PREFER/SELECT).

This realizes the LOCKED means-selection design (`docs/attic/graded_means_selection_design.md`, mechanism 1b
"RETAINED / RANKED, MONOTONE — no retraction"), which was designed but never built:

  - candidates are OPTION nodes reachable from the goal by a `candidate` relation, each carrying a
    graded `fit` degree (a VALUED float in [0,1] — however produced: an authored `has_fit`, or the
    α-cut/embedding degree a graded rule condition yields, `GoalSolver._graded_degree`);
  - the winner is the argmax = the candidate NOTHING BEATS (a candidate is BEATEN iff another eligible
    candidate has STRICTLY greater fit) — exactly the design's `?goal satisfied_by ?c when ?x chose ?c
    for ?goal and not ?c beaten`, computed by the firmware driver instead of a `<compare>` tool (fit is
    a real float here, so the comparison is direct — no number-named-node parsing needed);
  - MONOTONE: losers STAY (marked `beaten`, auditable for the why-trace), the winner is marked
    `satisfied_by`; nothing is retracted (§5);
  - TIES (equal max fit) → ALL tied candidates win (design §Ties — a genuine tie is offered, not
    broken arbitrarily); a caller needing ONE applies its own deterministic tiebreak.

α-cut and selection COMPOSE as two distinct filters: α-cut prunes candidates below `alpha` BEFORE the
argmax (a candidate pruned by α-cut is ineligible, NOT `beaten` — it never entered the comparison).

v0 SCOPE: the fit is an INPUT (authored or graded-rule-derived); computing it from a rule's graded
condition DURING matching (the α-cut in the APPLY/CHAIN body, `_graded_degree`) is the companion slice
that lifts APPLY/CHAIN off positive-only on the graded axis. Integrating the planner's `chosen` operator
pick (`solve._mint_chosen`) as a declared CHOOSE is the follow-on within 5.2.
"""
from __future__ import annotations

from .attrgraph import AttrGraph, VALUED, graded
from .machine import Machine, MINT, EMIT, State

FIT = "fit"                      # a candidate's fit degree — a VALUED float in [0,1] (NOT an embedding dim)
CANDIDATE = "candidate"          # goal -[candidate]-> option
SATISFIED_BY = "satisfied_by"    # goal -[satisfied_by]-> winner  (the PREFER result — nothing beats it)
BEATEN = "beaten"                # option -[beaten]-> goal        (an eligible candidate with strictly better fit exists)


_MACHINE = Machine()


def set_candidate(g: AttrGraph, goal: str, option: str, fit: float) -> str:
    """Register `option` as a candidate for `goal` with graded `fit` (a VALUED float in [0,1]). Stored
    VALUED (not GRADED) so the fit is a selection score, invisible to the embedding/similarity view.
    The writes run as an ISA program; re-registering is idempotent (`MINT(dedup=)`), the fit updates."""
    st = _MACHINE.apply(g, [
        EMIT("_o", FIT, float(fit), kind=VALUED),
        MINT("_c", attrs={CANDIDATE: graded(1.0)}, in_edges=["_g"], edges=["_o"], dedup=True),
    ], State({"_g": goal, "_o": option}))
    return st.regs["_c"]


def fit_of(g: AttrGraph, option: str) -> float:
    """The candidate's fit degree (0.0 if unset — an unfit candidate, pruned by any positive α-cut)."""
    a = g.get_attr(option, FIT)
    return float(a.value) if a is not None else 0.0


def candidates(g: AttrGraph, goal: str) -> list[str]:
    """The option nodes registered as candidates for `goal` (`goal -[candidate]-> option`)."""
    return [opt for rel, opt in g.relations_from(goal) if g.has_key(rel, CANDIDATE)]


def _rel_exists(g: AttrGraph, s: str, pred: str, o: str) -> bool:
    for rel, obj in g.relations_from(s):
        if g.has_key(rel, pred) and obj == o:
            return True
    return False


def choose(g: AttrGraph, goal: str, *, alpha: float = 0.0) -> list[str]:
    """CHOOSE (mode 5): among `goal`'s candidates, α-cut below `alpha`, then select the argmax by fit —
    the candidate(s) NOTHING beats. Marks each winner `goal -[satisfied_by]-> winner` and each eligible
    loser `loser -[beaten]-> goal` (monotone — no retraction, losers stay auditable). Idempotent.
    Returns the winners (all tied maxima); a caller needing a single pick applies its own tiebreak."""
    eligible = [(opt, fit_of(g, opt)) for opt in candidates(g, goal)]
    eligible = [(opt, d) for opt, d in eligible if d >= alpha]     # α-cut prunes BEFORE the comparison
    if not eligible:
        return []
    top = max(d for _opt, d in eligible)
    winners: list[str] = []
    ops, regs = [], {"_g": goal}                                   # the MISSING marks as ONE ISA program
    for i, (opt, d) in enumerate(eligible):                        # (the exists-read stays a driver read,
        if d >= top:                                               # so a re-CHOOSE assembles nothing)
            winners.append(opt)                                    # nothing beats it (== the max) -> winner
            if not _rel_exists(g, goal, SATISFIED_BY, opt):
                regs[f"_o{i}"] = opt
                ops.append(MINT(f"_w{i}", attrs={SATISFIED_BY: graded(1.0)},
                                in_edges=["_g"], edges=[f"_o{i}"]))
        elif not _rel_exists(g, opt, BEATEN, goal):                # strictly beaten -> stays, marked
            regs[f"_o{i}"] = opt
            ops.append(MINT(f"_b{i}", attrs={BEATEN: graded(1.0)},
                            in_edges=[f"_o{i}"], edges=["_g"]))
    if ops:
        _MACHINE.apply(g, ops, State(regs))
    return winners


def winners_of(g: AttrGraph, goal: str) -> list[str]:
    """The chosen candidate(s) for `goal` read back from the `satisfied_by` markers."""
    return [opt for rel, opt in g.relations_from(goal) if g.has_key(rel, SATISFIED_BY)]


def explain_choice(g: AttrGraph, goal: str) -> list[str]:
    """RECORD the CHOOSE as CNL: the winner(s) and the beaten alternatives with their fits — the
    auditable why-trace the monotone (losers-retained) mechanism exists to give."""
    gname = g.name(goal)
    lines: list[str] = []
    for w in winners_of(g, goal):
        lines.append(f"{gname} satisfied_by {g.name(w)}  (fit {fit_of(g, w):.3g})")
    for opt in candidates(g, goal):
        if _rel_exists(g, opt, BEATEN, goal):
            lines.append(f"  beaten: {g.name(opt)}  (fit {fit_of(g, opt):.3g})")
    return lines

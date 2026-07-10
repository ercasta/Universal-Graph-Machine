"""Goal-directed planning driver — the ISA arc, Phase 3 (the payoff).

The forward planner (`harneskills.planning`) is the fixpoint of a rule bank, driven by
`plan()`'s repeat-`run_rules`-until-stable loop: it SATURATES — every candidate/viable/best
marker for every operator, whether or not the goal needs it. This module drives the SAME bank
DEMAND-FORWARD via `GoalSolver`: a goal PULLS only the derivations on its own AND-OR chain
(magic-sets + tabling + the ¬∃ existential NACs of Phase 2), so an operator irrelevant to the
goal is never marked. Goal-direction is the arc INVARIANT (`docs/handoff_redesign.md`, the
direction-preservation gate), not a late optimization — this is where it lands on a non-toy bank.

**Everything except `chosen` lowers to completion.** Phase 1 (predicate-NAC → `R_not`
completion) and Phase 2 (existential ¬∃ NACs as demand-driven emptiness checks + `DROP_CTRL`
subsumed) already cover the whole planner bank — `candidate`/`reachable`/`blocked_by`/`viable`/
`cost_settled`/`dominated`/`best`/`before`, and the executor's `unmet`/`waits_for`/`ready`
(two independent ¬∃ groups) and `<replan>`. The ONE non-completion rule is `chosen`: its grouped
NAC references its OWN head (`not ?x chosen …`), a non-stratified SELECTION `GoalSolver` rejects.
So the driver owns exactly the selection, and nothing else.

**The `chosen` selection is a resolution CHAIN, most of it already CNL** (the design the user
ratified): for each needed `?c`, among the `best` operators that `add ?c`,
  1. PREFERENCES resolve it first — the `dominated`/`best`/`cost_settled` machinery (+ a
     preference bank like `corpus/preference.cnl`) already eliminates dominated operators. When a
     unique `best` op remains per need, `chosen` is DETERMINISTIC — pure completion, no choice
     (the common case; the "selection" is mostly subsumed, as `DROP_CTRL` was);
  2. a genuine TIE → a KB-PRESCRIBED tool — if several co-best ops remain and the KB delegates the
     tie-break to a `<call>` (`tie_break`), the choice is a calculator OUTSIDE the machine (the §8
     seam, like clingo for disjunction / `decide.py` for negation);
  3. a genuine tie with NOTHING prescribed → a DETERMINISTIC-ARBITRARY pick — the ops are
     interchangeable for the goal, so any is sound; we pick by stable node order (NOT RNG, which
     would break determinism / provenance / resume — the substrate is deterministic-ids by design).
No operational choice is hidden in the driver: (1) is CNL, (2) is a KB-directed tool, (3) is an
explicit indifferent tiebreak.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .production_rule import Rule
from .attrgraph import AttrGraph, valued
from .goal import Goal, GoalSolver
from .lowering import derived_triples


CHOSEN = "chosen"
YES = "<yes>"
NEED = "<need>"


# ---------------------------------------------------------------------------
# Graph helpers — pure graph operations on the planning vocabulary
# ---------------------------------------------------------------------------

def _hub(graph, name: str) -> str:
    """Get-or-create the single node named `name` (the planning control hubs)."""
    existing = graph.nodes_named(name)
    return existing[0] if existing else graph.add_node(name)


def _has_rel(graph, subj: str, rel: str, obj_name: str) -> bool:
    return any(graph.name(r) == rel and graph.name(o) == obj_name
               for r, o in graph.relations_from(subj))


def _drop_rel(graph, subj: str, rel: str, obj_name: str) -> None:
    for r, o in graph.relations_from(subj):
        if graph.name(r) == rel and graph.name(o) == obj_name:
            graph.remove_node(r)
            return


def simulate_effects(graph, op_id: str) -> None:
    """Materialize an operator's declared effects into `<now>` (the default act)."""
    now = _hub(graph, "<now>")
    for r, c in graph.relations_from(op_id):
        if graph.name(r) == "add" and not _has_rel(graph, now, "true", graph.name(c)):
            graph.add_relation(now, "true", c)
        elif graph.name(r) == "del":
            _drop_rel(graph, now, "true", graph.name(c))


def _perform_op(graph, o: str, actions: dict, failures: dict) -> None:
    """Act/observe boundary for one operator."""
    oname = graph.name(o)
    if oname in actions:
        actions[oname](graph, o)
    elif failures.get(oname, 0) > 0:
        failures[oname] -= 1
    else:
        simulate_effects(graph, o)


def goal_satisfied(graph) -> bool:
    """True once every `<goal> --want--> C` has `<now> --true--> C`."""
    for goal in graph.nodes_named("<goal>"):
        for r, c in graph.relations_from(goal):
            if graph.name(r) == "want" and not _has_rel(graph, _hub(graph, "<now>"),
                                                        "true", graph.name(c)):
                return False
    return True

# A KB-prescribed tie-break: given the tied co-best ops (stable-sorted) and the need they serve,
# return the ONE to commit. None => fall through to the deterministic-arbitrary pick (stable first).
TieBreak = Callable[[list[str], str], str]


@dataclass
class Plan:
    """A derived plan: the committed operators and their ordering (the goal-directed analog of
    the `chosen`/`before` markers a forward `plan()` saturates into the graph)."""
    chosen: set[str] = field(default_factory=set)                 # operator names committed
    before: set[tuple[str, str]] = field(default_factory=set)     # (earlier, later) op-name pairs
    ties: dict[str, list[str]] = field(default_factory=dict)      # need -> co-best ops, when a tie was broken


def _is_call_rule(r: Rule) -> bool:
    """A tool-materialization rule (head emits a `<call>` token — rank/act/price). The §8 tool
    boundary is serviced by the DRIVER (or a registered tool), NOT demanded as reasoning, so these
    are excluded from the goal-directed bank (the coverage map's ⬛ rows stay outside the machine)."""
    return any("<call>" in hp.s or "<call>" in hp.p for hp in r.rhs)


def _reasoning_rules(rules: list[Rule]) -> list[Rule]:
    """The bank the goal solver evaluates: everything MINUS the `chosen` selection rule (the one
    non-completion rule the driver owns) and the `<call>` tool-materialization rules (driver-
    serviced). Every remaining rule lowers to Phase-1/2 completion / existential-NAC."""
    return [r for r in rules if not any(hp.p == CHOSEN for hp in r.rhs) and not _is_call_rule(r)]


def _adds(ag: AttrGraph, op: str) -> set[str]:
    """What operator `op` adds — read from the monotone facts (`op --add--> c`)."""
    return {o for (s, r, o) in derived_triples(ag) if s == op and r == "add"}


def rank_cheaper_than(ag: AttrGraph) -> None:
    """The §8 rank CALCULATOR, AttrGraph-native (the goal-directed twin of `planning.rank_by_cost`):
    read operator `cost` facts, parse them to floats, and MINT `o1 --cheaper_than--> o2` for every
    strictly-cheaper pair. The rule layer cannot compare two opaque cost names — comparison is a
    calculator's job (§8) — so this materializes the comparison RESULT as facts the positive
    `dominated` rule then selects over. Registered as a tool-backed relation (`cheaper_than`) so it
    runs ONCE, DEMAND-DRIVEN, the first time a `dominated` subgoal demands the ordering. Idempotent
    (mint skips existing), so equal costs stay an honest tie (no `cheaper_than`, no fabricated pick)."""
    costs: dict[str, float] = {}
    for (s, r, o) in derived_triples(ag):
        if r == "cost":
            try:
                costs[s] = float(o)
            except ValueError:
                continue
    for o1, c1 in costs.items():
        for o2, c2 in costs.items():
            if c1 < c2:
                _mint_marker(ag, o1, "cheaper_than", o2)


# The default tool registry: cost comparison behind the `cheaper_than` relation. A cost-based
# preference (chain step 1) is thus resolved by the §8 calculator, not the arbitrary tiebreak.
DEFAULT_TOOLS = {"cheaper_than": rank_cheaper_than}


def derive_plan(ag: AttrGraph, rules: list[Rule], *, tie_break: TieBreak | None = None,
                tools: dict | None = None) -> Plan:
    """Derive the plan for the goal seeded in `ag`, demand-forward. Pulls `best` (which transitively
    demands need/candidate/viable/cost_settled/dominated — only along the goal's chain), then runs
    the `chosen` SELECTION per need (the resolution chain above), commits `chosen` facts, and
    demands `before` over them. Materializes `chosen` into `ag` (so the executor's demand-driven
    `ready` can read it) and returns the `Plan`.

    Note the selection reproduces the forward `chosen` rule's "one committed op per need" exactly:
    for each needed `?c`, if no already-committed op adds `?c`, pick one best op that does. On a
    UNIQUE best per need this equals `plan()`; on a genuine tie both are arbitrary, so the driver's
    deterministic-arbitrary (or a KB tie-break) is a sound, reproducible representative."""
    tools = DEFAULT_TOOLS if tools is None else tools
    plan_rules = _reasoning_rules(rules)
    solver = GoalSolver(ag, plan_rules, tools=tools)
    best = {s for (s, _o) in solver.solve(Goal("best", None, YES))}
    needs = [o for (_s, o) in solver.solve(Goal("for", NEED, None))]

    plan = Plan()
    covered: set[str] = set()                         # needs already met by a committed op
    for c in sorted(needs):                           # stable need order (deterministic)
        if c in covered:
            continue
        winners = sorted(op for op in best if c in _adds(ag, op))   # best ops that add this need
        if not winners:
            continue
        if len(winners) == 1:
            pick = winners[0]                         # preferences left a unique best -> deterministic
        elif tie_break is not None:
            pick = tie_break(winners, c)              # KB-prescribed tie-break tool (the §8 seam)
            plan.ties[c] = winners
        else:
            pick = winners[0]                         # deterministic-arbitrary (stable order), no RNG
            plan.ties[c] = winners
        plan.chosen.add(pick)
        covered |= _adds(ag, pick)                    # this op covers every need it adds (idempotent)

    # commit the selection as monotone facts, then demand the ordering over them.
    for op in plan.chosen:
        _mint_chosen(ag, op)
    order_solver = GoalSolver(ag, plan_rules, tools=tools)
    plan.before = set(order_solver.solve(Goal("before", None, None)))
    return plan


# ---------------------------------------------------------------------------
# The full solve loop — plan -> act/observe -> (replan) -> goal
# ---------------------------------------------------------------------------

def _mint_marker(ag: AttrGraph, subj: str, rel: str, obj: str = YES) -> None:
    """Materialize `subj --rel--> obj` into `ag` if absent (a reified control marker read
    positively by the bank — `chosen`/`done`, injected per cycle from driver state)."""
    if (subj, rel, obj) in derived_triples(ag):
        return
    ids = {str(a.value): nid for nid in ag.nodes()
           if (a := ag.get_attr(nid, "name")) is not None}
    s_id = ids.get(subj) or ag.add_node({"name": valued(subj)})
    o_id = ids.get(obj) or ag.add_node({"name": valued(obj)})
    ag.add_relation(s_id, rel, o_id)  # Phase 2.1: predicate key (dual-write bridge), not a hand-mint


def _ephemeral_ag(graph, chosen: set[str], done: set[str]):
    """A FRESH `AttrGraph` for one cycle: the persistent monotone facts (`to_attrgraph(graph)`) plus
    the driver's current CONTROL state (`chosen`/`done`) injected as markers. The bank's executor
    rules read `chosen`/`done` positively, so they must be present to demand `ready`; but they live
    in DRIVER state, not the persistent graph, so a replan just resets them — the persistent graph
    stays purely monotone and there is NOTHING to tear down (teardown fully subsumed)."""
    from .lowering import to_attrgraph
    ag, _ = to_attrgraph(graph)
    for op in chosen:
        _mint_marker(ag, op, CHOSEN)
    for op in done:
        _mint_marker(ag, op, "done")
    return ag


def _observe_simulated(graph, ag, op: str, reasoning: list[Rule], tools: dict) -> None:
    """Simulate op `op`'s effects into `<now>`, observing its FULL add-set — base effects AND those
    DERIVED by reasoning rules (the value→plan bridge `?o add have_valuable when ?o acts_on ?c and ?c
    is valuable` extends an operator's effects from a derived property). The forward engine sees the
    derived add because the bridge rule materializes it into the graph; here we read it demand-forward
    by demanding `add(op, ?)` over the reasoning bank on this cycle's `ag` (base facts + the bridge
    lower identically). `del` effects are read from base facts (derived retractions are out of scope)."""
    now = _hub(graph, "<now>")
    adds = {o for (_s, o) in GoalSolver(ag, reasoning, tools=tools).solve(Goal("add", op, None))}
    for c in adds:
        if not _has_rel(graph, now, "true", c):
            graph.add_relation(now, "true", _hub(graph, c))
    oid = graph.nodes_named(op)[0]
    for r, c in graph.relations_from(oid):
        if graph.has_key(r, "del"):  # Phase 2.1: predicate key, not name
            _drop_rel(graph, now, "true", graph.name(c))


def _diverged(graph, done: set[str]) -> bool:
    """A performed op whose DECLARED effect was not OBSERVED — the divergence the forward engine's
    `<replan>` rule detects (`?o done and ?o add ?c and not <now> true ?c`). Read from the
    persistent graph: for each done op, every `add ?c` must appear as `<now> true ?c`."""
    now = _hub(graph, "<now>")
    for op in done:
        oid = graph.nodes_named(op)[0]
        for r, c in graph.relations_from(oid):
            if graph.has_key(r, "add") and not _has_rel(graph, now, "true", graph.name(c)):  # Phase 2.1
                return True
    return False


def run_to_goal(graph, rules: list[Rule], *, actions: dict | None = None,
                failures: dict[str, int] | None = None, tie_break: TieBreak | None = None,
                tools: dict | None = None, max_cycles: int = 100) -> str:
    """Drive goal -> plan -> act/observe -> replan to a result, DEMAND-FORWARD (the goal-directed
    twin of `planning.solve`). Returns "done" (goal reached) or "stuck" (quiesced short of it).

    `graph` is the persistent MONOTONE name-`Graph`: operators + goal + the OBSERVED `<now> true`
    effects, and NOTHING else. The plan (`chosen`) and execution bookkeeping (`done`) are CONTROL,
    held in DRIVER state and injected into a fresh per-cycle `AttrGraph` (`_ephemeral_ag`) over
    which `ready` is demanded. So replanning is just RESETTING that driver state and re-deriving
    from the current observations — the forward engine's whole control-teardown bank
    (`planning_teardown.cnl`, 15 gated drops) is SUBSUMED, exactly as `DROP_CTRL` was in Phase 2:
    nothing control-layer is ever written to the persistent state, so there is nothing to retract.

    On DIVERGENCE (a performed op whose declared effect was not observed — `failures`, or a real
    action tool that acted differently), the driver resets `chosen`/`done` and re-derives the plan
    from the new observations, then re-executes (an op whose effect is already observed re-runs
    idempotently). Acting reuses `planning._perform_op` (real `actions[name]` tool / withheld
    `failures` effect / simulated declared effects)."""
    tools = DEFAULT_TOOLS if tools is None else tools
    reasoning = _reasoning_rules(rules)

    def _replan() -> set[str]:
        return derive_plan(_ephemeral_ag(graph, set(), set()), rules,
                           tie_break=tie_break, tools=tools).chosen

    chosen = _replan()
    done: set[str] = set()

    for _ in range(max_cycles):
        if goal_satisfied(graph):
            return "done"
        ag = _ephemeral_ag(graph, chosen, done)
        ready = {op for (_ex, op)
                 in GoalSolver(ag, reasoning, tools=tools).solve(Goal("ready", "<exec>", None))}
        if ready:
            for op in sorted(ready):                      # perform the domino (stable order)
                if op in done:
                    continue
                oid = graph.nodes_named(op)[0]
                if (actions and op in actions) or (failures and failures.get(op, 0) > 0):
                    # a real action tool (observes its own effects) or a withheld effect (divergence)
                    _perform_op(graph, oid, actions or {}, failures if failures is not None else {})
                else:
                    _observe_simulated(graph, ag, op, reasoning, tools)   # base + DERIVED adds
                done.add(op)
            continue
        if _diverged(graph, done):                        # stuck by a divergence -> replan
            chosen = _replan()
            done = set()
            continue
        return "stuck"                                    # quiesced short of the goal, no divergence
    return "stuck"


def _mint_chosen(ag: AttrGraph, op: str) -> None:
    """Materialize `op --chosen--> <yes>` into `ag` if absent (the driver's committed choice, read
    positively by the ordering + the executor exactly like any other derived marker)."""
    if (op, CHOSEN, YES) in derived_triples(ag):
        return
    ids = {str(a.value): nid for nid in ag.nodes()
           if (a := ag.get_attr(nid, "name")) is not None}
    op_id = ids.get(op) or ag.add_node({"name": valued(op)})
    yes_id = ids.get(YES) or ag.add_node({"name": valued(YES)})
    ag.add_relation(op_id, CHOSEN, yes_id)  # Phase 2.1: predicate key (dual-write bridge)

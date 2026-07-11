"""
Walkers — variable-length graph traversal as control token-passing
(docs/walkers_and_locality.md §4-§6, vision §6).

The fixed-arity pattern language cannot say "A connected to Z via *some* path" — a
single `Pat` is one hop. The §6 way around it is a **walker**: a control token that
carries an ORIGIN (where it started — one extreme), a REACHED set (where it has got to),
a TARGET (the other extreme it is looking for), and a FUEL budget (how far it may still
explore). Each step is an ordinary fixed-arity rule, self-bounding because it is *seeded
on the rare walker token* (§2: control low-df) and binds the next fact parametrically:

    walker reached ?x , ?x rel ?y      =>  walker reached ?y     (consume 1 fuel)

When the reached set finally contains the TARGET, a second rule fires the connection
`A rel T` — and **both extremes are in hand** because the walker carried the origin the
whole way (a plain "here" marker could not do this — carrying `origin` is the point, §4).

REALIZATION CHOICE. The doc speaks of "moving the frontier"; we keep the reached set
*additive* (a retained BFS wavefront) rather than a single moving frontier. One node, once
reached, both (a) seeds further steps and (b) **is the visited marker** that blocks
re-entry — so `reached` unifies §4's frontier and visited marker. This is simpler than a
moving frontier + separate visited set, finds *any* path (not just the first branch), and
— the decisive reason — gives clean **compositional provenance**: each `reached ?y` is
justified by `J --uses--> [reached ?x] , [path ?x->?y]`, so the chain of step-firings
records, edge by edge, the compressed path the shortcut bypasses (§5 requirement #1). The
semi-naive matcher (default) restricts each step to *newly* reached nodes, so retaining the
set costs no re-scan of old frontier — it behaves like a moving frontier for free.

SHORTCUTS (§5). The arrival rule materializes an ORDINARY `A rel T` fact — identical in
kind to any other relation, only shorter (no new edge type, vision §1). Because it hangs
off `reached(T)` (a permanent, justified node), the shortcut's provenance chains back
through every `reached` hop to every path edge: explanation is a traversal, and retraction
cascades — withdraw any path edge and `retraction.retract` (RETRACT_RULES) unwinds the shortcut
(test_walker_shortcut_is_retractable). Path/derived-fact shortcuts are monotone → permanent.

TERMINATION (§4). The `reached`-NAC is the correctness guarantee: a node already reached is
never re-added, so a *cyclic* `rel` cannot loop forever (finite node set). FUEL is the §14
"think harder" backstop budget on top of that: a SINGLE counter node (`<walker> --fuel--> "N"`,
the count in the node's name) whose presence gates each step; the step materializes a `dec`
tool-call, and `dec_tool` writes the predecessor count, removing the fuel edge at zero so the
walk halts even if more is reachable. More fuel = explore further; a materialized shortcut
means fewer hops next time (§6). (Earlier the counter was N unary `fuel` edges and the step
bound a fuel *unit*, so each step enumerated every remaining unit — cost quadratic in the
budget; the single-node counter is O(1) per step.) NOTE: `service_calls` runs only when the
rules quiesce, so within ONE `run()` the visited-NAC closes the whole reachable set BEFORE the
`dec` calls fire — on a finite relation fuel bounds total advances post-hoc, not mid-wave; it
genuinely truncates only across runs / on relations large enough to matter. Synchronous
mid-walk gating would need a step-by-step service cycle (not built — the visited-NAC already
guarantees termination here).

EVERYTHING IS RULES + TOOLS, NO BESPOKE PYTHON ORCHESTRATION (vision §6/§12.5).
  - Spawning a walker is a RULE (`SPAWN_RULES`): a `<walk-request>` carrying the fuel
    `amount` materializes the walker token AND a `refuel` tool-call.
  - FUEL is a budget OWNED by metareasoning (the `amount` the driver attaches to the demand,
    §14) but COMPILED to the low-level control machinery (the `fuel` edges) by a TOOL
    (`refuel_tool`), invoked through the materialized-call mechanism (dispatch.py) — not a
    hardcoded Python loop. Decrement stays a pure rule (the step rule's `drop`). The amount
    rides the connected demand -> request -> call chain (the PATH channel, §3 of the doc) so
    it is always in the locality scope — a free-floating policy node would fall outside it.
  - The whole thing runs in ONE `run(graph, rules, tools=WALK_TOOLS)`: the engine interleaves
    rule-firing and tool-dispatch to fixpoint. `walk_on_demand` no longer drives a bespoke
    seed -> run -> service -> run loop; it just seeds the demand and the budget and runs.

DEMAND-SPAWNED (§4). Walkers are never spawned eagerly for all pairs (that is the same
blow-up as eager transitivity); they run ON DEMAND. `walk_on_demand` reuses `demand.py`:
a `<demand>` becomes a `<walk-request>` token (DEMAND_WALK, a rule, §6), SPAWN_RULES turns
that into a walker + a refuel call, and the walker rules run. First target: on-demand
transitivity (a fuelled walk along `is_a`).
"""
from __future__ import annotations

import pathlib

from ..demand import seed_demand
from ..dispatch import call_arg, emit_call
from ..lowering import run_bank
from .machine_rules import load_machine_rules
from ..production_rule import Pat, Rule
from ..world_model import Graph

_WALKER_CNL = pathlib.Path(__file__).resolve().parents[2] / "corpus" / "walker.cnl"

# Walker vocabulary — all ordinary nodes/relations (nothing typed). `<walker>` /
# `<walk-request>` / `<budget>` are keyword nodes (canonicalize skips them) but NOT inert,
# so the matcher sees them — that is what lets a step rule seed on the rare walker token (§2).
WALKER = "<walker>"
WALK_REQUEST = "<walk-request>"
REFUEL = "refuel"        # the tool that sets the single `fuel` counter node from a budget number
DEC = "dec"              # the tool that decrements the single `fuel` counter by one

ORIGIN = "origin"
TARGET = "target"
REACHED = "reached"      # doubles as §4's frontier-source AND visited marker
FUEL = "fuel"
AMOUNT = "amount"        # budget / refuel-call slot carrying the count
SUBJ = "subj"
OBJ = "obj"

DEFAULT_FUEL = 64


def _ensure(graph: Graph, name: str) -> str:
    found = graph.nodes_named(name)
    return found[0] if found else graph.add_node(name)


# ---------------------------------------------------------------------------
# The fuel tools — a budget number on a single counter node, decremented by tool (§8/§14)
# ---------------------------------------------------------------------------

def _fuel_edge(graph: Graph, w: str) -> tuple[str, str] | None:
    """The walker's single `(fuel_rel_node, count_node)` pair, or None if it has no fuel."""
    for r, o in graph.relations_from(w):
        if graph.has_key(r, FUEL):
            return r, o
    return None


def refuel_tool(graph: Graph, call_id: str) -> set[str]:
    """Tool for a `refuel` call: read `target` (a walker) and `amount` (a node whose NAME is
    the budget number — the §8 opaque-name parse), and set the walker's SINGLE `fuel` counter
    node to that number. One edge `walker --fuel--> "N"`, not N unary edges: the count lives in
    the node's NAME, and `dec_tool` decrements it. (The unary representation made each STEP
    enumerate every remaining unit — cost quadratic in the budget; this is O(1) per step.)"""
    w = call_arg(graph, call_id, TARGET)
    amt = call_arg(graph, call_id, AMOUNT)
    if w is None or amt is None or not graph.has(w):
        return set()
    try:
        n = int(graph.name(amt))
    except ValueError:
        return set()
    existing = _fuel_edge(graph, w)
    if existing is not None:
        graph.remove_node(existing[0])
    fnode = _ensure(graph, str(max(0, n)))
    graph.add_relation(w, FUEL, fnode)
    return {w, fnode}


def dec_tool(graph: Graph, call_id: str) -> set[str]:
    """Tool for a `dec` call: decrement the `target` walker's single `fuel` counter by one
    (parse the opaque count name, write the predecessor; §8). At zero the fuel edge is REMOVED,
    so the STEP rule's `<walker>? fuel ?u` premise fails and the walk halts. `service_calls`
    runs queued `dec` calls SEQUENTIALLY, so K advances in a wavefront decrement the counter by
    K with no race."""
    w = call_arg(graph, call_id, TARGET)
    if w is None or not graph.has(w):
        return set()
    edge = _fuel_edge(graph, w)
    if edge is None:
        return {w}
    rel, count = edge
    try:
        n = int(graph.name(count))
    except ValueError:
        return {w}
    graph.remove_node(rel)                       # drop the old counter edge
    touched = {w}
    if n - 1 > 0:                                # at zero, leave the walker fuel-less (halts)
        f = _ensure(graph, str(n - 1))
        graph.add_relation(w, FUEL, f)
        touched.add(f)
    return touched


# The walker tool registry — pass to `run(..., tools=WALK_TOOLS)`.
WALK_TOOLS: dict = {REFUEL: refuel_tool, DEC: dec_tool}


# ---------------------------------------------------------------------------
# Spawning — a RULE materializes the walker + a refuel call (no Python loop)
# ---------------------------------------------------------------------------

# `<walk-request> subj ?a, obj ?c, amount ?n` => a fresh walker (origin/target/reached) AND a
# refuel `<call>` carrying the fuel amount; consume the request. Multi-triple head + a
# materialized tool-call in the consequent — pure rule, no Python. The `amount` arrives on the
# request (carried from the demand by DEMAND_WALK) so it is always in the locality scope.
SPAWN_RULES: list[Rule] = [
    Rule(
        key="walk.spawn",
        lhs=[Pat(f"{WALK_REQUEST}?", SUBJ, "?a"), Pat(f"{WALK_REQUEST}?", OBJ, "?c"),
             Pat(f"{WALK_REQUEST}?", AMOUNT, "?n")],
        rhs=[Pat(f"{WALKER}?", ORIGIN, "?a"), Pat(f"{WALKER}?", TARGET, "?c"),
             Pat(f"{WALKER}?", REACHED, "?a"),
             Pat("<call>?", "tool", REFUEL), Pat("<call>?", TARGET, f"{WALKER}?"),
             Pat("<call>?", AMOUNT, "?n")],
        drop=[Pat(f"{WALK_REQUEST}?", SUBJ, "?a"), Pat(f"{WALK_REQUEST}?", OBJ, "?c"),
              Pat(f"{WALK_REQUEST}?", AMOUNT, "?n")],
    ),
]


def spawn_walker(graph: Graph, origin_id: str, target_id: str, *,
                 fuel: int, rel: str = "is_a", token: str = WALKER) -> str:
    """Driver helper: materialize a walker token directly (origin/target/reached) plus a
    `refuel` tool-call for `fuel` units. The fuel is NOT seeded here — running the walker
    with `tools=WALK_TOOLS` lets the engine service the refuel call, setting the single fuel
    counter node. `token` types the walker (pair it with `walk_rules(rel, token=token)`);
    `rel` is baked into the rules. For tests / direct use; the demand path uses SPAWN_RULES."""
    w = graph.add_node(token)
    graph.add_relation(w, ORIGIN, origin_id)
    graph.add_relation(w, TARGET, target_id)
    graph.add_relation(w, REACHED, origin_id)         # the origin is reached at step 0
    emit_call(graph, REFUEL, {TARGET: w, AMOUNT: _ensure(graph, str(fuel))})
    return w


# ---------------------------------------------------------------------------
# The walker rules — one step rule + one shortcut-on-arrival rule, per relation
# ---------------------------------------------------------------------------

def walk_rules(rel: str = "is_a", *, token: str = WALKER) -> list[Rule]:
    """The two-rule walker gadget for traversing relation `rel` (parameterised like
    `same_as_rules`): a STEP rule that advances the reached set one hop and burns a fuel
    unit, and an ARRIVE rule that materializes the shortcut when the target is reached.

    Both seed from the rare `token` (default `<walker>`) as a bound-literal: every pattern
    binds the SAME walker instance, so a single instance never cross-wires. `token` TYPES the
    walker by its control flow — give a different relation its own token (e.g. `<walker:is_a>`
    vs `<walker:part_of>`) and the index routes each STEP rule ONLY to its own walkers, so two
    walkers on different relations run FULLY concurrently without interference (§7). Matching
    is bounded to one walker's own edges, never a global scan of `reached`/`rel` (§1/§2)."""
    w = f"{token}?"
    step = Rule(
        key=f"walk.step.{token}.{rel}",
        # reached(?x) is the chaining premise (permanent -> survives into provenance);
        # fuel(?u) is the SINGLE counter node — its mere presence gates the step (checked O(1),
        # never enumerated); ?x rel ?y is the actual hop. The advance also materializes a `dec`
        # call so the `dec` tool decrements the counter (removing it at zero to halt).
        lhs=[Pat(w, REACHED, "?x"), Pat(w, FUEL, "?u"), Pat("?x", rel, "?y"), Pat(w, TARGET, "?t")],
        # Two INDEPENDENT NACs (no shared free var, so `_nac_groups` keeps them separate):
        # `reached ?y` is the per-node visited guard (cyclic rel can't loop); `reached ?t` is
        # STOP-ON-ARRIVAL — once the target is reached the whole walk halts, so a positive query
        # costs the target's BFS distance, not the full reachable component/height.
        nac=[Pat(w, REACHED, "?y"), Pat(w, REACHED, "?t")],
        rhs=[Pat(w, REACHED, "?y"),                  # advance (additive wavefront)
             Pat("<call>?", "tool", DEC), Pat("<call>?", TARGET, w)],
    )
    arrive = Rule(
        key=f"walk.arrive.{token}.{rel}",
        lhs=[Pat(w, ORIGIN, "?a"), Pat(w, TARGET, "?t"), Pat(w, REACHED, "?t")],
        nac=[Pat("?a", rel, "?t")],                  # don't redo an existing connection
        rhs=[Pat("?a", rel, "?t")],                  # the materialized shortcut (a fact)
    )
    return [step, arrive]


# ---------------------------------------------------------------------------
# Demand -> walk-request (a rule, §6) — reuse demand.py's <demand> token
# ---------------------------------------------------------------------------
#
# A `<demand>` for "does subj rel obj?" (demand.py) becomes a `<walk-request>` carrying the
# two endpoints. This mirrors DEMAND_COREF: a rule turns the query into a request token, and
# SPAWN_RULES + the engine's tool dispatch fulfil it. The endpoints ride on `subj`/`obj` (a
# walk needs BOTH extremes, unlike the one-arg `want` lookups in external.py).

DEMAND_WALK: list[Rule] = [
    Rule(
        key="demand.walk",
        lhs=[Pat("?d", "d_subj", "?a"), Pat("?d", "d_obj", "?c"), Pat("?d", AMOUNT, "?n")],
        nac=[Pat("?w", SUBJ, "?a"), Pat("?w", OBJ, "?c")],     # one request per (a,c)
        rhs=[Pat(f"{WALK_REQUEST}?", SUBJ, "?a"), Pat(f"{WALK_REQUEST}?", OBJ, "?c"),
             Pat(f"{WALK_REQUEST}?", AMOUNT, "?n")],           # carry the fuel budget along
    ),
]


_CNL_RULES: list[Rule] | None = None


def load_walker_rules() -> list[Rule]:
    """The walker ruleset (demand -> request -> spawn -> step -> arrive) loaded from
    `corpus/walker.cnl` — the CANONICAL authoring, no Python rule literals. Cached. This is
    the `is_a` instance (on-demand transitivity); the Python `walk_rules(rel)` / SPAWN_RULES /
    DEMAND_WALK remain for the relation-parameterised path (e.g. a cyclic `r`)."""
    global _CNL_RULES
    if _CNL_RULES is None:
        _CNL_RULES = load_machine_rules(_WALKER_CNL.read_text(encoding="utf-8"))
    return _CNL_RULES


def walk_on_demand(graph: Graph, subj: str, obj: str, *,
                   fuel: int = DEFAULT_FUEL, rel: str = "is_a") -> None:
    """Resolve "is `subj` connected to `obj` via `rel`?" by a demand-spawned, fuelled walk.

    Reuses `demand.py`: seed a `<demand>` carrying the metareasoning fuel amount (§14), then
    run ONE fixpoint over the walker rules with the walker TOOLS. The engine interleaves
    rule-firing and tool-dispatch — demand becomes a walk-request, the spawn rule materializes
    a walker + refuel call, the refuel tool sets the single fuel counter node, the walker
    steps, and the shortcut `subj rel obj` is materialized (with provenance) iff a `rel`-path
    within the budget reaches `obj`. No bespoke orchestration: the engine manages the tool
    calls. Selective — ONLY the demanded connection (§4).

    For `is_a` the rules come from `corpus/walker.cnl` (the canonical CNL authoring); for any
    other relation they come from the parameterised Python factories."""
    d = seed_demand(graph, subj, obj)
    graph.add_relation(d, AMOUNT, _ensure(graph, str(fuel)))   # metareasoning's budget (§14)
    rules = load_walker_rules() if rel == "is_a" else DEMAND_WALK + SPAWN_RULES + walk_rules(rel)
    # Seed the run from the demand's locality, NOT the whole graph: `run` otherwise sets the
    # first-step frontier to `set(graph.nodes())` (O(graph) per query — the WordNet probe's
    # residual linear term). Step 1 is `force_all` (matches every rule fully regardless of the
    # frontier), so a small seed is correctness-neutral; later steps ride the rules' own output.
    seeds = [d, *graph.within([d], 1)]
    run_bank(graph, rules, tools=WALK_TOOLS, provenance=True)

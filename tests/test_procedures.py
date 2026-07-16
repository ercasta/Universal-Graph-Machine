"""
Procedures — a named step-sequence run as a PRE-MADE plan, executed through the EXISTING planner
gate, gap-filled by the planner where a precondition is unmet (docs/design/procedures_design.md §2).

This is also the first IN-REPO end-to-end exercise of the real planner banks (`corpus/planning.cnl`
+ `corpus/planning_execution.cnl`) — the `needs`/`produces` problem surface lives harness-side, so
here operators are authored directly in the core planner vocabulary (`pre`/`add`/`<now> true`).

The stepping bank (`corpus/procedure.cnl`) is three content-blind rules: INVOKE (mark a run
procedure's steps `chosen`), ORDER (lift `step_before` into the planner's `before`), and GAP-FILL
(an unmet precondition becomes a `<need>` the planner synthesizes a filler for). Everything domain
is KB data; nothing procedure-specific is in Python — the act tool is the only §8 world boundary.
"""
import pathlib

import ugm as h
from ugm import AttrGraph, derived_triples
from ugm.cnl.authoring import run_rules
from ugm.dispatch import call_arg

CORPUS = pathlib.Path(__file__).resolve().parent.parent / "corpus"


def _solve(g, rules, tools, order, max_cycles=50):
    """The stratified solve loop (the harness's `plan.solve` driver, here in-test): run the whole
    bank stratum-by-stratum (`run_rules` — stratified negation, servicing `<call>` tools at each
    fixpoint), and REPEAT until the graph stops changing. Iteration is essential: acting changes
    the `<now>` state, and both the drop-rules that clear a step's `unmet`/`waits_for` and the
    act-emit that lags `ready` by a stratum only re-fire on the next whole-bank pass. Quiescence =
    a full cycle that derived no new (deduplicated) triple."""
    prev = None
    for _ in range(max_cycles):
        run_rules(g, rules, tools=tools, provenance=False)
        cur = frozenset(derived_triples(g))
        if cur == prev:                              # a cycle that changed nothing -> converged
            return
        prev = cur
    raise AssertionError(f"solve did not converge in {max_cycles} cycles (order={order})")


def _load(*names):
    text = "\n".join((CORPUS / n).read_text(encoding="utf-8") for n in names)
    return h.load_machine_rules(text)


def _ensure(g, name):
    found = g.nodes_named(name)
    return found[0] if found else g.add_node(name)


def _op(g, name, *, pre=(), add=()):
    """A planner operator authored in the core vocabulary: `op pre P`, `op add E`."""
    o = _ensure(g, name)
    for p in pre:
        g.add_relation(o, "pre", _ensure(g, p))
    for e in add:
        g.add_relation(o, "add", _ensure(g, e))
    return o


def _procedure(g, name, steps):
    """A procedure as an ordered collection: `name step S` per step, `A step_before B` per
    adjacent pair (the shape the `to NAME : A then B …` surface will generate)."""
    proc = _ensure(g, name)
    for s in steps:
        g.add_relation(proc, "step", _ensure(g, s))
    for a, b in zip(steps, steps[1:]):
        g.add_relation(_ensure(g, a), "step_before", _ensure(g, b))
    return proc


def _run(g, name):
    """The invocation request: `<run> proc NAME`."""
    g.add_relation(_ensure(g, "<run>"), "proc", _ensure(g, name))


def _now_true(g, *facts):
    now = _ensure(g, "<now>")
    for f in facts:
        g.add_relation(now, "true", _ensure(g, f))


def _act_tool(order):
    """The §8 act/observe boundary (`planning_execution.cnl`'s `act` call): materialize the ready
    op's declared `add` effects into `<now> true`, mark it `done`, and log the op name in execution
    order. Content-blind on WHICH op — the rules that emitted the call decided that."""
    def handler(g, call_id):
        op = call_arg(g, call_id, "arg")            # `<call>? arg ?o`
        if op is None:
            return set()
        if any(g.has_key(r, "done") for r, _ in g.relations_from(op)):
            return set()                            # an op acts ONCE — the `ready` token persists
            # across solve cycles (monotone), so guard on `done` (a world action isn't repeated).
        order.append(g.name(op))
        touched = set()
        now, yes = _ensure(g, "<now>"), _ensure(g, "<yes>")
        for r, e in list(g.relations_from(op)):
            if g.has_key(r, "add"):
                touched.add(g.add_relation(now, "true", e))
        touched.add(g.add_relation(op, "done", yes))
        return touched
    return handler


def _rank_noop():
    """A no-op `rank` tool: mark the ranked op `ranked <yes>` (planning.cnl emits a rank call per
    cost-settled op; with a single candidate there is nothing to compare, so this just closes the
    call). `ranked` is tool-set, never a rule — no stratification cycle."""
    def handler(g, call_id):
        op = call_arg(g, call_id, "arg")
        if op is None:
            return set()
        return {g.add_relation(op, "ranked", _ensure(g, "<yes>"))}
    return handler


# ---------------------------------------------------------------------------
# 1. Ordered execution — the pure-sequencing case (the waits_for gate)
# ---------------------------------------------------------------------------

def test_procedure_runs_its_steps_in_declared_order():
    """Two independent steps (no shared precondition) run in the DECLARED order — the order comes
    ONLY from `step_before` lifted to `before`, honoured by planning_execution.cnl's waits_for
    gate. Without the ORDER rule both would be ready at once and the order undetermined."""
    rules = _load("procedure.cnl", "planning_execution.cnl")
    g = AttrGraph()
    _op(g, "greet", add=["greeted"])
    _op(g, "serve", add=["served"])
    _procedure(g, "welcome", ["greet", "serve"])
    _run(g, "welcome")

    order = []
    _solve(g, rules, {"act": _act_tool(order)}, order)

    assert order == ["greet", "serve"]                       # declared sequence honoured
    assert ("<now>", "true", "greeted") in _now(g)
    assert ("<now>", "true", "served") in _now(g)


# ---------------------------------------------------------------------------
# 2. Gap-fill — a missing precondition is synthesized by the planner
# ---------------------------------------------------------------------------

def test_unmet_precondition_is_gap_filled_by_the_planner():
    """`heat` needs `water`, which no procedure step produces and isn't in the state. The gap-fill
    rule turns it into a `<need>`; the planner (planning.cnl) synthesizes `get_water`, commits it,
    and orders it BEFORE `heat` (producer/consumer). Procedure steps + synthesized filler run
    through ONE gate. `get_water` is NOT a declared step — the planner invented it."""
    rules = _load("procedure.cnl", "planning.cnl", "planning_execution.cnl")
    g = AttrGraph()
    _op(g, "add_beans", add=["beans_in"])
    _op(g, "heat", pre=["water"], add=["hot_coffee"])
    _op(g, "get_water", add=["water"])                       # the filler — NOT a brew step
    _procedure(g, "brew", ["add_beans", "heat"])
    _run(g, "brew")

    order = []
    _solve(g, rules, {"act": _act_tool(order), "rank": _rank_noop()}, order)

    assert "get_water" in order                              # the planner SYNTHESIZED the filler
    assert order.index("get_water") < order.index("heat")    # ordered before its consumer
    assert "add_beans" in order and "heat" in order          # the pre-made steps ran too
    assert ("<now>", "true", "hot_coffee") in _now(g)        # the goal effect materialized
    assert ("<now>", "true", "water") in _now(g)             # the gap-filler's effect


def _now(g):
    """The `<now> true X` state as (name, 'true', name) triples — read straight off the graph
    (the state hub is a control node, so it's outside the fact VIEW; read it structurally)."""
    now = g.nodes_named("<now>")
    if not now:
        return set()
    return {("<now>", "true", g.name(o))
            for r, o in g.relations_from(now[0]) if g.has_key(r, "true")}

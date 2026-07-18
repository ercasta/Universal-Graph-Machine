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

Slice 2 routes the whole arc through the REAL intake driver: `to NAME : A then B …` AUTHORS the
procedure, `run NAME` INVOKES it, and the stratified `_act_loop` (not an in-test solve crutch)
drives execution. Operators still author in the core planner vocab (`pre`/`add`) — that problem
surface is harness-side.
"""
import pathlib

import ugm as h
from ugm import AttrGraph
from ugm.dispatch import call_arg

CORPUS = pathlib.Path(__file__).resolve().parent.parent / "corpus"


def _load(*names):
    text = "\n".join((CORPUS / n).read_text(encoding="utf-8") for n in names)
    return h.load_machine_rules(text)


def _ensure(g, name):
    found = g.nodes_named(name)
    return found[0] if found else g.add_node(name)


def _op(g, name, *, pre=(), add=(), cost=None):
    """A planner operator authored in the core vocabulary: `op pre P`, `op add E`, `op cost C`."""
    o = _ensure(g, name)
    for p in pre:
        g.add_relation(o, "pre", _ensure(g, p))
    for e in add:
        g.add_relation(o, "add", _ensure(g, e))
    if cost is not None:
        g.add_relation(o, "cost", _ensure(g, str(cost)))
    return o


def _act_tool(order, fail=()):
    """The §8 act/observe boundary (`planning_execution.cnl`'s `act` call): materialize the ready
    op's declared `add` effects into `<now> true`, mark it `done`, and log the op name in execution
    order. Content-blind on WHICH op — the rules that emitted the call decided that. An op in `fail`
    is marked `done` but emits NO effect — a step that ran yet did not achieve its expected result
    (the world action's real-life failure mode), which the DISCREPANCY rule then detects."""
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
        if g.name(op) not in fail:                  # a failed action still finishes, but achieves nothing
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


def _rank_by_cost():
    """A REAL `rank` calculator (the §8 comparison boundary): costs are staged as `?o cost ?c`
    KNOWLEDGE, the tool only does the arithmetic — deriving the `cheaper_than` FACTS the banks
    select on. A TOTAL order (ties broken by name), which is what keeps commitment to one op:
    `dominated`/`best` and REPLAN's `outranked_by` narrow on `cheaper_than` and nothing else."""
    def cost_of(g, op):
        for r, o in g.relations_from(op):
            if g.has_key(r, "cost"):
                try:
                    return float(g.name(o))
                except (TypeError, ValueError):
                    return None
        return None

    def handler(g, call_id):
        op = call_arg(g, call_id, "arg")
        if op is None:
            return set()
        touched, c = set(), cost_of(g, op)
        if c is not None:
            for other in list(g.nodes()):
                oc = None if other == op else cost_of(g, other)
                if oc is None:
                    continue
                near, far = (op, other) if (c, g.name(op)) < (oc, g.name(other)) else (other, op)
                touched.add(g.add_relation(near, "cheaper_than", far))
        touched.add(g.add_relation(op, "ranked", _ensure(g, "<yes>")))
        return touched
    return handler


# ---------------------------------------------------------------------------
# 1. Ordered execution — the pure-sequencing case (the waits_for gate)
# ---------------------------------------------------------------------------

def test_procedure_runs_its_steps_in_declared_order():
    """Two independent steps (no shared precondition) run in the DECLARED order — the order comes
    ONLY from `step_before` lifted to `before`, honoured by planning_execution.cnl's waits_for
    gate. Without the ORDER rule both would be ready at once and the order undetermined. Authored
    and invoked through the real intake surface (`to …` / `run …`)."""
    rules = _load("procedure.cnl", "planning_execution.cnl")
    g = AttrGraph()
    _op(g, "greet", add=["greeted"])
    _op(g, "serve", add=["served"])
    h.ingest(g, [], "to welcome : greet then serve")         # AUTHOR

    order = []
    h.ingest(g, rules, "run welcome", tools={"act": _act_tool(order)})   # INVOKE + run (stratified _act_loop)

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
    h.ingest(g, [], "to brew : add_beans then heat")         # AUTHORED, not hand-staged

    order = []
    h.ingest(g, rules, "run brew", tools={"act": _act_tool(order), "rank": _rank_noop()})   # INVOKE + run

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


# ---------------------------------------------------------------------------
# 3. The authoring surface — `to NAME : A then B then C` (Slice 2, piece 1)
# ---------------------------------------------------------------------------

def _out_edges(g, subj):
    """Domain relations OUT of the named node `subj` as (rel_name, obj_name) pairs."""
    n = g.nodes_named(subj)
    return {(g.predicate(r), g.name(o)) for r, o in g.relations_from(n[0])} if n else set()


def test_to_form_authors_a_procedure_through_ingest():
    """`to brew : add_beans then heat` routes as a PROCEDURE and stages exactly the stepping bank's
    vocabulary: `step` membership + `step_before` order + the `is_a procedure` marker. Crucially the
    order is `step_before` (procedure-scoped, lifted to `before` only on `<run>`), NOT the planner's
    global `before` — so a step name shared by two procedures is not ordered globally by one."""
    from ugm.intake import ingest
    g = AttrGraph()
    events = []
    out = ingest(g, [], "to brew : add_beans then heat", on_event=events.append)

    assert out.kind == "procedure"
    assert events[-1].kind == "procedure" and events[-1].data["steps"] == ["add_beans", "heat"]
    assert _out_edges(g, "brew") >= {("step", "add_beans"), ("step", "heat"), ("is_a", "procedure")}
    assert ("step_before", "heat") in _out_edges(g, "add_beans")
    assert not any(rel == "before" for rel, _ in _out_edges(g, "add_beans"))   # NOT the global planner order


def test_run_surface_tolerates_noise_words():
    """The invocation recognizer accepts the natural variants an SLM/user might produce; all seed the
    same `<run> proc NAME` request. (Execution through `run …` is covered end-to-end by tests 1 & 2.)"""
    from ugm.cnl.procedure_surface import parse_run
    assert parse_run("run brew") == "brew"
    assert parse_run("run the brew") == "brew"
    assert parse_run("run procedure brew") == "brew"
    assert parse_run("run brew procedure") == "brew"
    assert parse_run("brew") is None                         # not a command — no `run` keyword


# ---------------------------------------------------------------------------
# 4. Discrepancy + replan — a step ran but did not achieve its effect (Slice 3)
# ---------------------------------------------------------------------------

def test_discrepancy_replans_to_an_alternative():
    """A step FINISHES but its effect never materializes (an action that ran and failed). The
    DISCREPANCY rule detects the mismatch (`done` but the effect not in `<now>`), REPLAN excludes the
    failed means and re-needs the effect, and the planner commits + runs an ALTERNATIVE producer
    through the one gate — failure folds to facts and the rules recover, no exception control flow."""
    rules = _load("procedure.cnl", "planning.cnl", "planning_execution.cnl")
    g = AttrGraph()
    _op(g, "warm", add=["hot_coffee"])                       # the procedure step — but its action FAILS
    _op(g, "microwave", add=["hot_coffee"])                  # an alternative producer the planner can find
    h.ingest(g, [], "to brew : warm")                        # a one-step procedure

    order = []
    h.ingest(g, rules, "run brew",
             tools={"act": _act_tool(order, fail={"warm"}), "rank": _rank_noop()})

    assert order == ["warm", "microwave"]                    # tried the step, then recovered via the alternative
    assert ("<now>", "true", "hot_coffee") in _now(g)        # the effect was achieved in the end
    # the failed means is recorded (data for reflection / a domain retry policy) and not retried
    warm = g.nodes_named("warm")[0]
    assert any(g.predicate(r) == "excluded" for r, _ in g.relations_from(warm))


def test_successful_step_has_no_discrepancy():
    """The mismatch detector must not false-positive: a step whose effect IS observed produces no
    discrepancy, no exclusion, no replan — the ordinary path stays a single clean run."""
    rules = _load("procedure.cnl", "planning.cnl", "planning_execution.cnl")
    g = AttrGraph()
    _op(g, "warm", add=["hot_coffee"])
    _op(g, "microwave", add=["hot_coffee"])
    h.ingest(g, [], "to brew : warm")

    order = []
    h.ingest(g, rules, "run brew",                           # no failures this time
             tools={"act": _act_tool(order), "rank": _rank_noop()})

    assert order == ["warm"]                                 # the alternative was never needed
    assert ("<now>", "true", "hot_coffee") in _now(g)
    warm = g.nodes_named("warm")[0]
    assert not any(g.predicate(r) == "excluded" for r, _ in g.relations_from(warm))


# ---------------------------------------------------------------------------
# 5. Cost governs RECOVERY too — "try the smallest edit first" as authored knowledge
# ---------------------------------------------------------------------------

def _brew_with_alternatives(costs, fail):
    """One failing procedure step (`warm`) plus several rival producers of its effect, each with
    staged `cost` knowledge. Returns the ACT order — which ops the world actually ran."""
    rules = _load("procedure.cnl", "planning.cnl", "planning_execution.cnl")
    g = AttrGraph()
    _op(g, "warm", add=["hot_coffee"], cost=1)
    for name, c in costs.items():
        _op(g, name, add=["hot_coffee"], cost=c)
    h.ingest(g, [], "to brew : warm")

    order = []
    h.ingest(g, rules, "run brew",
             tools={"act": _act_tool(order, fail=set(fail)), "rank": _rank_by_cost()})
    return order, g


def test_replan_tries_the_cheapest_alternative_not_the_first_staged():
    """The recovery path is COST-RANKED, not staging-ordered. Proven by INVERTING the declared costs
    and observing the choice invert — staging order is identical in both runs, so only the `cost`
    knowledge can explain the difference (agreement between cost and staging order proves nothing)."""
    order, _ = _brew_with_alternatives({"alt_a": 5, "alt_b": 3, "alt_c": 9}, fail=["warm"])
    assert order == ["warm", "alt_b"]                        # cheapest, though staged second

    order, _ = _brew_with_alternatives({"alt_a": 9, "alt_b": 7, "alt_c": 1}, fail=["warm"])
    assert order == ["warm", "alt_c"]                        # costs inverted -> choice inverts

    # and ONLY the chosen one ran: recovery commits one alternative, not every untried producer
    assert len(order) == 2


def test_replan_falls_through_to_the_next_cheapest_when_the_cheapest_also_fails():
    """`outranked_by` is a BLOCK, retracted once the blocking rival has been tried — so a cheaper
    alternative that itself fails does not strand the next-cheapest. Without the drop rules the
    block is monotone and the effect would silently stay unachieved."""
    order, g = _brew_with_alternatives({"alt_a": 5, "alt_b": 3, "alt_c": 9}, fail=["warm", "alt_b"])

    assert order == ["warm", "alt_b", "alt_a"]               # cheapest first, then the next cheapest
    assert ("<now>", "true", "hot_coffee") in _now(g)        # the effect was achieved in the end
    assert "alt_c" not in order                              # the dearest was never needed


def test_replan_without_cost_knowledge_commits_every_untried_producer():
    """The documented LIMIT, pinned honestly: `cheaper_than` is the bank's only narrowing criterion,
    so with no cost staged the alternatives are unordered and every untried producer commits. This
    is why a rank calculator should impose a TOTAL order (see corpus/planning.cnl's commit note)."""
    rules = _load("procedure.cnl", "planning.cnl", "planning_execution.cnl")
    g = AttrGraph()
    _op(g, "warm", add=["hot_coffee"])                       # no `cost` anywhere
    for name in ("alt_a", "alt_b", "alt_c"):
        _op(g, name, add=["hot_coffee"])
    h.ingest(g, [], "to brew : warm")

    order = []
    h.ingest(g, rules, "run brew",
             tools={"act": _act_tool(order, fail={"warm"}), "rank": _rank_by_cost()})

    assert order == ["warm", "alt_a", "alt_b", "alt_c"]      # unordered -> all of them run

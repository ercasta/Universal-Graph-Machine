"""
Materialized tool calls — the engine-managed §8 boundary (vision §6/§12.5).

The hard rule stays absolute: **a rule never calls a tool, a tool never rewrites; they
couple only through nodes.** What changes here is that the coupling becomes *first-class
and engine-driven* instead of bespoke per-domain Python orchestration.

A tool call is an ordinary control node a rule MATERIALIZES, exactly like any other token:

    <call> --tool--> T          (T is a node named the tool, e.g. `refuel`)
    <call> --SLOT--> A          (named argument slots the tool understands)

The engine (`rewriter.run`, given a `tools` registry) services pending `<call>` nodes at
each rule-fixpoint: it looks up the named tool, runs it, and consumes the call — then folds
whatever nodes the tool emitted back into the change frontier and keeps reasoning. So tool
invocation is just more token-passing in the one fixpoint loop; the driver stays dumb ("for
any pending call whose tool is registered, run it"), and WHICH tools fire, and WHEN, is
decided by the rules that emit the calls, at the point a value is needed.

A tool is `handler(graph, call_id) -> set[str]`: it reads its call's argument slots (opaque
node names — the §1/§8 calculator discipline), emits result/control nodes, and RETURNS the
set of node ids it touched (so the engine can re-seed). It must NOT do arbitrary reasoning
rewrites — only emit nodes. The engine consumes the call afterwards, so a handler cannot
forget to.

`<call>` is a keyword node (canonicalize skips it) but NOT inert, so rules see it. This is
the generalization of `external.py`'s `<kind-request>`/`service_requests` pattern: same
discipline, lifted into the engine loop and given a uniform call shape.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .world_model import Graph

CALL = "<call>"
TOOL = "tool"

# A tool: reads its call's slots, emits nodes, returns the touched node ids.
Tool = Callable[[Graph, str], "set[str]"]


@dataclass
class AsyncTool:
    """A tool that CANNOT answer synchronously — it needs the outside world (a network round-trip, an
    `ask_user` prompt). Two halves around a `SUSPEND` (docs/attic/isa_control_machine.md §9.4):
      * `request(graph, call_id) -> payload` — what the world must answer (an opaque payload the host
        services); computed from the call's argument slots (the §1/§8 calculator discipline).
      * `fold(graph, call_id, response) -> set[str]` — apply the world's answer as result/control nodes
        and return the touched ids (exactly a sync `Tool`'s return).
    The control-machine dispatcher SUSPENDs between the two: it hands the request to the host, the host
    does the wait, and `resume` folds the response — the streaming suspend/resume the intake design wants.
    The `<call>` RECORD stays a graph node (§6); only the return/resume MECHANICS are control instructions."""
    request: Callable[[Graph, str], object]
    fold: Callable[[Graph, str, object], "set[str]"]


def merge_tools(*registries: dict[str, Tool]) -> dict[str, Tool]:
    """Compose several tool registries into one, RAISING on a name collision. The extension point for
    a consumer (e.g. harneskills) that layers its own tools onto the firmware's: instead of the silent
    `{**a, **b}` dict merge — where a later registry shadows an earlier tool of the same name — this
    fails loudly, so two subsystems can never quietly claim the same `<call> --tool--> NAME`. Order-
    independent (collision is symmetric). See the engine developer guide, 'Extension point: a tool'."""
    out: dict[str, Tool] = {}
    for reg in registries:
        for name, tool in reg.items():
            if name in out:
                raise ValueError(f"tool name collision: {name!r} is registered by two registries")
            out[name] = tool
    return out


def _ensure(graph: Graph, name: str) -> str:
    # TODO(vision-cleanup, see docs/implementation_plan.md): get-or-create pokes the substrate directly —
    # a Python twin of `MINT(intern=True)`. Should emit that instruction, not reimplement it.
    found = graph.nodes_named(name)
    return found[0] if found else graph.add_node(name)


def _objs(graph: Graph, subj: str, rel: str) -> list[str]:
    return [o for r, o in graph.relations_from(subj) if graph.has_key(r, rel)]


def emit_call(graph: Graph, tool_name: str, slots: dict[str, str]) -> str:
    """Materialize a `<call>` for `tool_name` with the given argument `slots`
    (slot-name -> node id). Driver/test helper; normally a RULE materializes a call."""
    c = graph.add_node(CALL)
    graph.add_relation(c, TOOL, _ensure(graph, tool_name))
    for slot, node_id in slots.items():
        graph.add_relation(c, slot, node_id)
    return c


def call_tool(graph: Graph, call_id: str) -> str | None:
    """The name of the tool a call requests (the object of its `tool` slot)."""
    objs = _objs(graph, call_id, TOOL)
    return graph.name(objs[0]) if objs else None


def call_arg(graph: Graph, call_id: str, slot: str) -> str | None:
    """The node id in argument `slot` of `call_id` (first if several), or None."""
    objs = _objs(graph, call_id, slot)
    return objs[0] if objs else None


def call_args(graph: Graph, call_id: str, slot: str) -> list[str]:
    """All node ids in argument `slot` of `call_id`."""
    return _objs(graph, call_id, slot)


def pending_calls(graph: Graph) -> list[str]:
    """Every materialized `<call>` node currently in the graph."""
    return list(graph.nodes_named(CALL))


def consume_call(graph: Graph, call_id: str) -> None:
    """Delete a serviced call: its argument relation nodes, then the call node itself
    (control deletion is legal, vision §5)."""
    for rel, _o in graph.relations_from(call_id):
        graph.remove_node(rel)
    graph.remove_node(call_id)


def service_calls(graph: Graph, registry: dict[str, Tool]) -> set[str]:
    """Run every pending call whose tool is registered, consuming each after; return the
    union of touched node ids (the engine re-seeds the frontier from them).

    The dumb dispatcher (vision §6): it never inspects what a tool does — it routes a call
    to its handler and consumes it. Calls whose tool is not registered are left untouched
    (some other registry may service them); they never busy-loop, since servicing them
    yields nothing and the engine stops when nothing new is produced."""
    touched: set[str] = set()
    for c in pending_calls(graph):
        if not graph.has(c):                         # a prior handler removed it
            continue
        name = call_tool(graph, c)
        handler = registry.get(name) if name else None
        if handler is None:
            continue
        res = handler(graph, c)
        if res:
            touched |= res
        if graph.has(c):                             # auto-consume (handler needn't)
            consume_call(graph, c)
    return touched


# ---------------------------------------------------------------------------
# The dispatcher AS A CONTROL-MACHINE PROGRAM (docs/attic/isa_control_machine.md §9.4)
# ---------------------------------------------------------------------------
#
# The §9.4 port: the `<call>` servicing MECHANICS become control instructions. `service_calls` above is
# the flat synchronous loop (still used by `run_bank`'s in-fixpoint tool servicing). This dispatcher
# runs the same servicing as a control-machine PROGRAM, and — the piece the flat loop cannot express —
# handles an ASYNC tool by SUSPENDing to the host and RESUMing with the answer. Sync tools run inline
# (a `PRIM` step reusing the helpers above); async tools are a `SUSPEND` return/resume pair. The `<call>`
# RECORD stays a graph node (a rule materializes it); only the return/resume mechanics moved (§6).


def _dispatch_program(graph: Graph, sync_tools: dict[str, Tool],
                      async_tools: dict[str, AsyncTool]) -> list:
    """Build the control-machine program that services every pending `<call>`: find the next serviceable
    call and branch on its KIND (none/sync/async); a sync tool runs inline and loops; an async tool
    computes its request, SUSPENDs (handing it to the host), and on resume folds the response and loops."""
    from .machine import Block, PRIM, SUSPEND, BRANCH, BRANCH_IF, HALT

    def _touch(ctrl, res):
        ctrl.setdefault("touched", set()).update(res or ())

    def find_next(g, stream, ctrl):
        # the next pending call with a REGISTERED tool; stash (call_id, tool, is_async) and report KIND
        # (0 none / 1 sync / 2 async). Loops re-scan, so a call a handler CREATED is serviced too.
        for c in pending_calls(g):
            if not g.has(c):
                continue
            name = call_tool(g, c)
            if name in sync_tools:
                ctrl["call_id"], ctrl["tool"] = c, name
                return stream, 1
            if name in async_tools:
                ctrl["call_id"], ctrl["tool"] = c, name
                return stream, 2
        return stream, 0

    def run_sync(g, stream, ctrl):
        c, name = ctrl["call_id"], ctrl["tool"]
        _touch(ctrl, sync_tools[name](g, c))
        if g.has(c):
            consume_call(g, c)
        return stream, 0

    def make_request(g, stream, ctrl):
        c, name = ctrl["call_id"], ctrl["tool"]
        ctrl["req"] = (name, c, async_tools[name].request(g, c))    # the payload the host services
        return stream, 0

    def fold_response(g, stream, ctrl):
        c, name = ctrl["call_id"], ctrl["tool"]
        _touch(ctrl, async_tools[name].fold(g, c, ctrl.get("response")))
        if g.has(c):
            consume_call(g, c)
        return stream, 0

    return [
        Block(label="LOOP", prim=PRIM(find_next, out="kind"),
              term=BRANCH_IF("kind", "<=", 0, "DONE")),            # nothing serviceable -> done
        Block(term=BRANCH_IF("kind", ">=", 2, "ASYNC")),          # kind 2 = async; else fall to sync
        Block(prim=PRIM(run_sync), term=BRANCH("LOOP")),          # sync: run inline, re-scan
        Block(label="ASYNC", prim=PRIM(make_request),
              term=SUSPEND(request_reg="req")),                   # hand the request to the host, wait
        Block(prim=PRIM(fold_response), term=BRANCH("LOOP")),     # resumed: fold the answer, re-scan
        Block(label="DONE", term=HALT()),
    ]


def service_calls_cm(graph: Graph, sync_tools: dict[str, Tool],
                     async_tools: dict[str, AsyncTool] | None = None, *,
                     answer: Callable[[object], object] | None = None):
    """Service pending `<call>`s via the control-machine dispatcher (§9.4). Sync tools run inline; async
    tools SUSPEND to the host, which supplies the answer and resumes.

    Two host protocols:
      * `answer` GIVEN — a `request -> response` callback (the async world). This drives the suspend/
        resume loop internally and returns the touched-id `set` when every call is serviced. The
        convenience form (tests, a synchronous simulation of the async world).
      * `answer` OMITTED — returns a `Continuation` on the FIRST async call so the CALLER owns the wait
        (the true streaming boundary: run something else, then `ControlMachine.resume(graph, cont,
        response={'response': ...})`); returns the touched-id `set` if there was no async call.

    With `async_tools` empty and `answer` omitted this is a control-machine equivalent of `service_calls`
    (sync only), reusing the same helpers — behaviour matches (the mode-call tests are the oracle)."""
    from .machine import ControlMachine, Continuation
    async_tools = async_tools or {}
    cm = ControlMachine()
    result = cm.run(graph, _dispatch_program(graph, sync_tools, async_tools))
    if answer is None:
        return result if isinstance(result, Continuation) else cm.ctrl.get("touched", set())
    while isinstance(result, Continuation):
        result = cm.resume(graph, result, response={"response": answer(result.request)})
    return cm.ctrl.get("touched", set())

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

from typing import Callable

from .attrgraph import intern_node
from .world_model import Graph

CALL = "<call>"
TOOL = "tool"

# A tool: reads its call's slots, emits nodes, returns the touched node ids.
Tool = Callable[[Graph, str], "set[str]"]


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


def _objs(graph: Graph, subj: str, rel: str) -> list[str]:
    return [o for r, o in graph.relations_from(subj) if graph.has_key(r, rel)]


def emit_call(graph: Graph, tool_name: str, slots: dict[str, str]) -> str:
    """Materialize a `<call>` for `tool_name` with the given argument `slots`
    (slot-name -> node id). Driver/test helper; normally a RULE materializes a call."""
    c = graph.add_node(CALL)
    graph.add_relation(c, TOOL, intern_node(graph, tool_name))
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

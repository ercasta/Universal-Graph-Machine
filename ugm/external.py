"""
External knowledge — request tokens, a generic tool dispatcher, and freshness.

This is the substrate's boundary to the outside world (prices, distances, inventory,
weather, …): knowledge the KB does NOT hold, fetched on demand from an external source.
It is the §8 calculator pattern applied to *lookups*, and it follows the §12.5 hard
rule absolutely: **a rule never calls a tool, and a tool never rewrites.** They are
coupled ONLY through nodes — a token-passing handshake, exactly like the planning
loop's `<exec> --ready--> O` / `act` boundary, generalized:

    a RULE emits a REQUEST token  ──▶  the DISPATCHER runs the registered TOOL  ──▶
    the tool emits RESULT nodes (or an error)  ──▶  RULES fire on the results.

So tool invocation itself becomes demand-driven token-passing (vision §6): the driver
stays a dumb dispatcher — "for any pending request, run its handler" — and which lookups
happen, and when, is decided by rules at the actual point a value is needed.

A request is now a MATERIALIZED TOOL CALL (dispatch.py): `<call> --tool--> KIND --arg--> ARG`,
serviced by the same engine-managed dispatcher as every other tool (`service_calls`). This
replaces the old bespoke `<kind-request> --want--> ARG` board + `service_requests` — external
lookups are no longer a parallel mechanism, they are one kind of materialized call (vision §6).

CONVENTIONS (all nodes + relations, nothing typed):
  request (CONTROL)   `<call> --tool--> KIND --arg--> ARG`  a rule's demand for a lookup
  result  (FACT)      `R --of--> ARG`, `R --val--> "v"`  the tool's answer (R named KIND)
  freshness (FACT)    `Rnew --supersedes--> Rold`        a newer result hides an older one
  error   (FACT)      `<error> --about--> ARG`, `--reason--> "…"`; `<kind-request> --failed--> ARG`
                      (`<kind-request>` survives only as the per-kind FAILURE/status board)

FRESHNESS IS §5, NOT DELETION. The fact layer never deletes (vision §5): a changed value
is a NEW result node, and the old one is hidden by an *added* `supersedes` marker read
through a guarded filter. "Current" = the result that nothing supersedes; consumers read
it with a NAC `?x supersedes R`. The tool wires `supersedes` because time/ordering lives
in the tool (the graph has no clock). Only the CONTROL request token is ever deleted
(consumed when serviced) — legal, it is control, not fact.

The request KEY (which external record to fetch) is OPAQUE content the tool dereferences
(here: the arg node's name); rules only ever match it as a label (vision §1/§8).
"""
from __future__ import annotations

from .dispatch import (
    call_arg, call_tool, consume_call, emit_call, pending_calls, service_calls,
)
from .world_model import Graph

ARG = "arg"          # the single-argument slot of a request <call> (the looked-up key)
OF = "of"
VAL = "val"
SUPERSEDES = "supersedes"
FAILED = "failed"
ABOUT = "about"
REASON = "reason"
ERROR = "<error>"

# The default lookup kind for a human-in-the-loop clarification (see interaction.py):
# the result is named `clarify`; the request <call>'s tool is `clarify`.
CLARIFY_DEFAULT_KIND = "clarify"


# ---------------------------------------------------------------------------
# Small graph helpers (no name index — get-or-create over nodes_named)
# ---------------------------------------------------------------------------

def _hub(graph: Graph, name: str) -> str:
    existing = graph.nodes_named(name)
    return existing[0] if existing else graph.add_node(name)


def _objs(graph: Graph, subj: str, rel: str) -> list[str]:
    return [o for r, o in graph.relations_from(subj) if graph.has_key(r, rel)]


def request_hub(kind: str) -> str:
    """The per-kind status/FAILURE board node (e.g. 'price' -> '<price-request>'). Requests
    now ride on `<call>` (dispatch.py); this node survives only as the stable place
    `emit_error` records `--failed--> arg`, which domain rules read (e.g. planning's
    failed-yields-to-priced)."""
    return f"<{kind}-request>"


# ---------------------------------------------------------------------------
# Freshness — supersedes + the guarded "current" read (vision §5)
# ---------------------------------------------------------------------------

def is_superseded(graph: Graph, result_id: str) -> bool:
    """True if some node points `--supersedes--> result_id` (a newer result hides it).

    A relation `Rnew --supersedes--> result_id` is the 2-hop path Rnew -> [supersedes
    node] -> result_id, so `result_id`'s direct predecessor IS the `supersedes` rel node.
    """
    return any(graph.has_key(pred, SUPERSEDES) for pred in graph.into(result_id))


def results_for(graph: Graph, kind: str, arg_id: str, *, current_only: bool = True) -> list[str]:
    """Result nodes (named `kind`) whose `of` points at `arg_id`. `current_only` filters
    out superseded ones — the §5 guarded read ("current" = nothing supersedes it)."""
    out = []
    for rnode in graph.nodes_named(kind):
        if arg_id in _objs(graph, rnode, OF):
            if not current_only or not is_superseded(graph, rnode):
                out.append(rnode)
    return out


def result_value(graph: Graph, result_id: str) -> str | None:
    vals = _objs(graph, result_id, VAL)
    return graph.name(vals[0]) if vals else None


def emit_result(graph: Graph, kind: str, arg_id: str, value: str) -> str:
    """Emit a fresh result FACT `R --of--> arg`, `R --val--> value` (R named `kind`).

    If a current (non-superseded) result for the same (kind, arg) already exists, the new
    result is wired to SUPERSEDE it — an *added* marker (monotone, §5), never a deletion.
    Returns the new result node id.
    """
    prior = results_for(graph, kind, arg_id, current_only=True)
    r = graph.add_node(kind)
    graph.add_relation(r, OF, arg_id)
    graph.add_relation(r, VAL, _hub(graph, value))
    for old in prior:
        graph.add_relation(r, SUPERSEDES, old)
    return r


def emit_error(graph: Graph, kind: str, arg_id: str, reason: str) -> str:
    """Emit an `<error>` FACT about `arg_id` (examined by rules) + a `failed` marker on
    the request hub, so domain rules (generic or specific) can react and the planner
    does not stall waiting for a result that will never arrive."""
    e = graph.add_node(ERROR)
    graph.add_relation(e, ABOUT, arg_id)
    graph.add_relation(e, REASON, _hub(graph, reason))
    graph.add_relation(_hub(graph, request_hub(kind)), FAILED, arg_id)
    return e


# ---------------------------------------------------------------------------
# Requests + the generic dispatcher (vision §6 — the dumb driver)
# ---------------------------------------------------------------------------

def request(graph: Graph, kind: str, arg_id: str) -> None:
    """Emit a request as a materialized tool-call `<call> --tool--> kind --arg--> arg`
    (deduped). Normally a RULE emits this directly; the helper is for tests/driver seeding."""
    for c in pending_calls(graph):
        if call_tool(graph, c) == kind and call_arg(graph, c, ARG) == arg_id:
            return
    emit_call(graph, kind, {ARG: arg_id})


def pending(graph: Graph, kind: str) -> list[str]:
    """Arg ids with an outstanding request `<call>` for tool `kind`."""
    return [a for c in pending_calls(graph)
            if call_tool(graph, c) == kind and (a := call_arg(graph, c, ARG)) is not None]


def consume_request(graph: Graph, kind: str, arg_id: str) -> None:
    """Consume the request `<call>` for (kind, arg) (control deletion, §5). Rarely needed —
    `service_calls` auto-consumes a serviced call; kept for driver-side use."""
    for c in list(pending_calls(graph)):
        if call_tool(graph, c) == kind and call_arg(graph, c, ARG) == arg_id:
            consume_call(graph, c)


# The dispatcher is now the engine-managed `service_calls` (dispatch.py), imported above so
# existing callers read `ext.service_calls(graph, registry)`. There is no separate external
# dispatcher any more — that unification is the point of this migration.


def lookup_handler(source) -> "callable":
    """Build a tool that answers a lookup from an external `source` (a dispatch.py Tool:
    `handler(graph, call_id) -> touched ids`).

    `source` is the opaque outside world — a dict `{name: value}` or a callable
    `name -> value-or-None` (a real DB query / web call would go here). The KB holds none
    of it. For the call's arg, the handler dereferences the arg's NAME against `source` (the
    opaque key, §1), emits a `val` result FACT on hit (superseding any current one — §5
    freshness), or an `<error>` on miss. `service_calls` consumes the call afterwards.
    """
    get = source.get if isinstance(source, dict) else source

    def handler(graph: Graph, call_id: str) -> set[str]:
        kind = call_tool(graph, call_id)
        arg = call_arg(graph, call_id, ARG)
        if arg is None or kind is None:
            return set()
        value = get(graph.name(arg))
        if value is None:
            return {arg, emit_error(graph, kind, arg, "not_found")}
        return {arg, emit_result(graph, kind, arg, str(value))}

    return handler

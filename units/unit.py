"""UNITS, GATES, AND FIRING — `docs/units/model.md` §5.

A unit holds a pattern and a transformation, has input gates and one output, and **sees only what its
gates deliver** (§12 invariant 3). There is no ambient store to read — `Graph` is a value, so isolation
costs nothing and forbids nothing.

**Gates latch**, and a repeat arrival is a firing: there is no value-comparison suppressing it and
therefore no notion of quiescence. A unit is consequently *stateful and order-dependent* — `output =
f(inputs)` is false — which §5 states as a cost rather than hiding.

**Units never wire anything** (§12 invariant 4). Nothing in this module touches topology.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .graph import EMPTY, Graph, Node, role_edge
from .match import Match, solve


@dataclass(frozen=True)
class Emit:
    """What a firing writes: one occurrence node, its roles, and — if the rule says so — a gradable
    attribute stamped with the **firing's own match strength**.

    That stamp is §4's *"a firing may inherit its match strength"*: degree propagates from premise to
    conclusion, which is what lets *"a little bird"* conclude *not really a bird*."""

    name: str
    roles: tuple = ()              # ((role_name, var_name), …)
    graded: str | None = None      # gradable attr on the conclusion, valued at the match band


@dataclass
class Miss:
    """A gate that was never fed, carrying what it wanted (§9). The natural signal for reaching outside:
    something wired to a miss goes and looks. Same shape as the out-of-fuel handler."""

    unit: str
    gate: str
    wanted: str = ""


class Unit:
    """One unit. `fn(inputs) -> Graph` is the transformation; `gates` names its inputs."""

    def __init__(self, name: str, gates: tuple, fn: Callable, *, pattern=()) -> None:
        self.name = name
        self.gates = tuple(gates)
        self.fn = fn
        self.pattern = pattern          # kept for inspection (invariant 1), never consulted by the engine
        self.latched: dict = {g: None for g in gates}
        self.output: Graph | None = None
        self.firings: int = 0

    # -- the circuit calls these; nothing else does ------------------------------------------

    def deliver(self, gate: str, value: Graph) -> Graph:
        """A value arrives. The gate latches it and the unit fires **using the latched values of the
        others** — it does not block waiting for the rest."""
        if gate not in self.latched:
            raise KeyError(f"{self.name} has no gate {gate!r} (gates: {self.gates})")
        self.latched[gate] = value
        return self.fire()

    def fire(self) -> Graph:
        self.firings += 1
        inputs = {g: (v if v is not None else EMPTY) for g, v in self.latched.items()}
        self.output = self.fn(inputs)
        return self.output

    def misses(self) -> list:
        return [Miss(self.name, g, _wanted(self.pattern)) for g, v in self.latched.items() if v is None]

    def __repr__(self) -> str:
        return f"<Unit {self.name} gates={self.gates} fired={self.firings}>"


def _wanted(pattern) -> str:
    return ", ".join(sorted({v for p in _walk(pattern) for k, v in p.attrs if k == "name"}))


def _walk(pattern):
    stack = list(pattern) if isinstance(pattern, (tuple, list)) else [pattern]
    while stack:
        p = stack.pop()
        yield p
        stack.extend(p.out)


# -- constructors -----------------------------------------------------------------------------

def rule(name: str, pattern: tuple, emit: Emit, *, gate: str = "in", theta: str | None = None) -> Unit:
    """A rule unit: match `pattern` on the gate's value, write `emit` for each match.

    ⚠ **The output carries its input forward**, conclusions added. `0008` (*subset output — a rule emits
    only what it derived*) was not on `model.md`'s contradicted list, but the tunnel needs carry-forward:
    §6 says everything downstream of a chain computes *within the scope that chain establishes*, and a
    unit that emitted only its conclusions would drop the scope's data at the first link. Flagged rather
    than settled — it may instead be that a tunnel wants an explicit data wire alongside."""

    def fn(inputs: dict) -> Graph:
        g = inputs[gate]
        out = g
        for m in solve(g, pattern, theta):
            out = _write(out, emit, m)
        return out

    return Unit(name, (gate,), fn, pattern=pattern)


def _write(g: Graph, emit: Emit, m: Match) -> Graph:
    occ = Node(emit.name)
    g = g.with_node(occ, name=emit.name)
    for role_name, var in emit.roles:
        g = role_edge(g, occ, role_name, m[var])
    if emit.graded is not None and m.band is not None:
        g = g.with_degree(occ, emit.graded, m.band)
    return g


def transform(name: str, fn: Callable[[Graph], Graph], *, gate: str = "in") -> Unit:
    """A graph-to-graph unit. **This is all a supposition is** (§6): it takes the enclosing value and
    emits the value as it would be under the supposition. Nothing marks it as hypothetical, because
    nothing needs to — the scope *is* the value on the wire, and no rule downstream will ever ask."""
    return Unit(name, (gate,), lambda inputs: fn(inputs[gate]))


__all__ = ["Unit", "Emit", "Miss", "rule", "transform"]

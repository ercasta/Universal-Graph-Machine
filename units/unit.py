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

from .graph import EMPTY, Graph, Node, contains, role_edge
from .match import Match, solve


@dataclass(frozen=True)
class Emit:
    """Mint an occurrence: one node, its roles, and — if the rule says so — a gradable attribute
    stamped with the **firing's own match strength**.

    That stamp is §4's *"a firing may inherit its match strength"*: degree propagates from premise to
    conclusion, which is what lets *"a little bird"* conclude *not really a bird*."""

    name: str
    roles: tuple = ()              # ((role_name, var_name), …)
    graded: str | None = None      # gradable attr on the conclusion, valued at the match band


@dataclass(frozen=True)
class Same:
    """Conclude that two bound nodes are the same thing.

    **A decision, not an application.** The effect writes a `same-as` occurrence into the graph; the
    actual rewriting happens at write-back (`loop`), exactly as a concluded deletion would (§9). Keeping
    those apart is what lets `cnl.md` §1 hold: no machinery ever decides identity, and the decision that
    is applied is one a rule reached and can be argued with."""

    left: str
    right: str


@dataclass(frozen=True)
class Stamp:
    """Set a gradable attribute on an **already-bound** node, at a stated band.

    This exists so that a supposition is a *rule* rather than a Python callable. *"Suppose he pays them
    off"* is *"the standing occurrence is good, at `certain`"* — a pattern and an effect, like anything
    else. Without it the spike had an escape hatch exactly where `model.md` §11 says there must not be
    one: the front end would be targeting Python, not data."""

    target: str                    # a variable bound by the pattern
    attr: str
    band: str


class ScopePointer:
    """Where conclusions land in the **graph's** nesting — the return leg of `model.md` §6.

    §6 keeps scope in two places and says why neither is redundant: the *circuit* holds the tunnel,
    which is free during a computation and gone after it; the *graph* holds the nesting, which is what
    survives across turns. And then the sentence that had not been built: *"write-back maps a tunnel
    position back into nesting."*

    This is that map. A statement that establishes a scope carries one of these; every unit assembled
    inside it mints its conclusions **under** the scope node, so *"Paul is eligible"* concluded inside
    a supposition is physically a member of *"assuming the payments are settled"* rather than a flat
    assertion about the world.

    **A chain guard does not discard the context, it moves the pointer.** A nested statement inherits
    the innermost pointer, so a supposition inside a supposition lands two levels down. The circuit
    still carries no scope — the pointer belongs to the assembler, and no rule can see it or match it
    (§12 invariant 1). The one thing that reads it is the placement of a minted node, which is
    mechanism, not judgement.

    The node is minted **lazily, once per run**: a scope that never concludes anything leaves nothing
    behind."""

    __slots__ = ("label", "parent", "node")

    def __init__(self, label: str, parent: "ScopePointer | None" = None,
                 node: Node | None = None) -> None:
        self.label = label
        self.parent = parent
        self.node = node                # already bound: an assumption that exists in the world

    def ensure(self, g: Graph) -> tuple:
        """The scope node, minting it (and its ancestors) on first use.

        **An existing scope with the same label is reused.** The circuit is rebuilt every step, so
        minting unconditionally gave a fresh `assuming-x` per step and the assumption lost its identity
        across the turn. A scope label is a plumbing ID (§11), and this is the assembler recognising its
        own bookkeeping — not the boundary identifying two things (`cnl.md` §1)."""
        if self.node is not None:
            return g, self.node
        existing = [n for n in g.nodes
                    if g.attr(n, "scope") and g.attr(n, "name") == self.label]
        if existing:
            self.node = existing[0]
            return g, self.node
        self.node = Node(self.label)
        g = g.with_node(self.node, name=self.label, scope=True)
        if self.parent is not None:
            g, up = self.parent.ensure(g)
            g = contains(g, up, self.node)
        return g, self.node

    def reset(self) -> None:
        self.node = None

    def __repr__(self) -> str:
        return f"<Scope {self.label}{' →' + self.parent.label if self.parent else ''}>"


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

def rule(name: str, pattern: tuple, *effects, gate: str = "in", theta: str | None = None,
         cooldown=None, under=None) -> Unit:
    """A rule unit: match `pattern` on the gate's value and apply each effect per match.

    **A supposition is one of these** (§6), which is the whole reason effects are data: it takes the
    enclosing value and emits the value as it would be under the supposition. Nothing marks it as
    hypothetical, because nothing needs to — the scope *is* the value on the wire, and no rule
    downstream will ever ask.

    ⚠ **The output carries its input forward**, conclusions added. `0008` (*subset output — a rule emits
    only what it derived*) was not on `model.md`'s contradicted list, but the tunnel needs carry-forward:
    §6 says everything downstream of a chain computes *within the scope that chain establishes*, and a
    unit that emitted only its conclusions would drop the scope's data at the first link. Flagged rather
    than settled — it may instead be that a tunnel wants an explicit data wire alongside."""

    def fn(inputs: dict) -> Graph:
        g = inputs[gate]
        out = g
        for m in solve(g, pattern, theta):
            if cooldown is not None and cooldown.fired(cooldown.key(name, m, g)):
                continue        # already derived this, recently — see `cooldown.py` for the trade
            for e in effects:
                out = _apply(out, e, m, under)
        return out

    return Unit(name, (gate,), fn, pattern=pattern)


def _apply(g: Graph, effect, m: Match, under=None) -> Graph:
    if isinstance(effect, Emit):
        occ = Node(effect.name)
        g = g.with_node(occ, name=effect.name)
        if under is not None:
            # The conclusion is placed IN the scope it was reached in, not asserted flatly (§6).
            g, scope_node = under.ensure(g)
            g = contains(g, scope_node, occ)
        for role_name, var in effect.roles:
            g = role_edge(g, occ, role_name, m[var])
        if effect.graded is not None and m.band is not None:
            g = g.with_degree(occ, effect.graded, m.band)
        return g
    if isinstance(effect, Stamp):
        return g.with_degree(m[effect.target], effect.attr, effect.band)
    if isinstance(effect, Same):
        a, b = m[effect.left], m[effect.right]
        if a is b:
            return g                                  # a node is trivially itself; write nothing
        occ = Node("same-as")
        g = g.with_node(occ, name="same-as")
        g = role_edge(g, occ, "of", a)
        return role_edge(g, occ, "of", b)
    raise TypeError(f"unknown effect {effect!r}")


def transform(name: str, fn: Callable[[Graph], Graph], *, gate: str = "in") -> Unit:
    """An arbitrary graph-to-graph unit. **Kept only for tests and probes** — a real one would be a
    `rule`, because anything expressed as a Python callable is invisible to the data (§11)."""
    return Unit(name, (gate,), lambda inputs: fn(inputs[gate]))


__all__ = ["Unit", "Emit", "Stamp", "Same", "Miss", "ScopePointer", "rule", "transform"]

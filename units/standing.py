"""STANDING CIRCUITS — `docs/units/revision-01-standing-circuits.md`.

A spike, deliberately separate from `circuit.py`/`loop.py`, which implement the superseded model. It
exists to test five claims and to find out what they cost:

1. a derived fact is **positioned** — it lives in the cell of the unit that produced it, never in a pool;
2. **revive from axioms** — values are recomputed each turn, so nothing is ever retracted;
3. **energy grows on revisit**, and a surge burns the loop;
4. a **partially wired** unit is a stable state;
5. positioning gives the tunnel **for free** — no `visible_at`, no `ScopePointer`.

## The one thing that is genuinely different from Rete / Datalog / dataflow

Those systems all put derived facts back into an undistinguished working memory. The network is a
*matching accelerator*: it is authored for the computation, and results land in a pool. Here the network
is grafted onto the **domain** graph, so a derived fact's position is a position in the world model.
That is what makes scope free (§5 below) and provenance free (the wiring *is* the derivation).

## The cost this spike is meant to expose

`0008` — *subset output: a rule emits only what it derived* — becomes **right after all** under
positioning, reversing the carry-forward that `unit.rule` adopted for the tunnel. But subset output has
a bite: an emitted occurrence carries its filler *nodes* (identity-shared) and **not their attributes**,
so a downstream unit that wants to read `name` must be **wired to where the name is**. There is no
ambient store to fall back on. That is the intended discipline, not a defect — but it means chains are
wired wider than they look, and that is the number worth watching.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

from .graph import EMPTY, Graph, Node, role_edge
from .match import Match, solve
from .unit import Emit, Stamp, _apply

SURGE_AT = 3            # revisits of one unit before the loop is burned


@dataclass(frozen=True)
class Value:
    """What travels on a wire.

    `path` is the list of units this value has passed through, and it is the whole of the cycle
    machinery: energy is `path.count(unit)`, so it **grows only on revisit** and a long acyclic chain
    accumulates nothing (`revision-01` §4). This is BGP's AS-path rather than IP's TTL, chosen for the
    same reason — a hop counter cannot tell depth from looping.

    `band` is epistemic and **never** interacts with `path`. Energy is plumbing (§4, invariant 12)."""

    graph: Graph
    band: str | None = None
    path: tuple = ()

    def through(self, unit: str) -> "Value":
        return replace(self, path=self.path + (unit,))

    def revisits(self, unit: str) -> int:
        return self.path.count(unit)


class Cell:
    """A **position**, and the only place a derived fact ever lives.

    `within` is physical nesting (`model.md` §6): a cell inside a hypothesis's cell is inside the
    hypothesis, full stop. There is no world identifier, no comparability test, and nothing computes a
    projection — a unit sees a cell only if it is wired to it, so the seal is a fact about topology.

    `axiom=True` marks a fact with no predecessors. Those are the only cells a revive does not clear.

    `scope=True` marks a cell that **is** a containment rather than merely sitting in one — a
    supposition. Its own content belongs to *itself*, which is what makes the seal hold in the direction
    that actually matters: the base world can see **that** a supposition exists, and cannot see the
    premise inside it (§6). Without this the antecedent leaks even though the conclusion does not."""

    __slots__ = ("name", "within", "axiom", "scope", "held")

    def __init__(self, name: str, *, within: "Cell | None" = None, axiom: bool = False,
                 scope: bool = False) -> None:
        self.name = name
        self.within = within
        self.axiom = axiom
        self.scope = scope
        self.held: Value | None = None

    def home(self) -> "Cell | None":
        """Which containment this cell's *content* is at. A scope holds its own content."""
        return self if self.scope else self.within

    def inside(self, other: "Cell | None") -> bool:
        c = self
        while c is not None:
            if c is other:
                return True
            c = c.within
        return other is None

    def __repr__(self) -> str:
        return f"<Cell {self.name}{' axiom' if self.axiom else ''}{'' if self.held else ' empty'}>"


class StandingUnit:
    """A unit that **stands**. It is not rebuilt per step and not thrown away.

    Its gates latch, it matches over the **union of its gates** — a join that is local to the unit and
    reaches nothing else — and it writes what it derived into its own `cell`. It never touches topology
    (invariant 4) and never sees a scope (invariant 1)."""

    def __init__(self, name: str, pattern: tuple, *effects, gates: tuple = ("in",),
                 theta: str | None = None, within: "Cell | None" = None) -> None:
        self.name = name
        self.pattern = pattern
        self.effects = effects
        self.gates = tuple(gates)
        self.theta = theta
        self.latched: dict = {g: None for g in self.gates}
        self.cell = Cell(f"{name}:out", within=within)
        self.firings = 0

    # -- revive ---------------------------------------------------------------------------------

    def clear(self) -> None:
        """A revive throws away *values*, never wiring. This is the whole of §3: no retraction, no
        invalidation, no in-lists — the conclusion is simply not reproduced if its support is gone."""
        self.latched = {g: None for g in self.gates}
        self.cell.held = None
        self.firings = 0

    def deliver(self, gate: str, value: Value) -> Value | None:
        if gate not in self.latched:
            raise KeyError(f"{self.name} has no gate {gate!r} (gates: {self.gates})")
        self.latched[gate] = value
        return self.fire()

    def fire(self) -> Value | None:
        """Match and emit. Returns `None` when nothing was derived — which is *not* an error and not a
        miss; it is a unit that had nothing to say."""
        self.firings += 1
        seen = [v for v in self.latched.values() if v is not None]
        if not seen:
            return None
        g = EMPTY
        for v in seen:
            g = g.union(v.graph)

        derived = EMPTY
        band = None
        for m in solve(g, self.pattern, self.theta):
            for e in self.effects:
                derived = _apply(derived, e, m, None)
            band = m.band if band is None else band

        if not derived.nodes:
            return None
        path = ()
        for v in seen:
            if len(v.path) > len(path):
                path = v.path
        out = Value(derived, band, path).through(self.name)
        self.cell.held = out
        return out

    # -- §5: a partially wired unit is a stable state --------------------------------------------

    def dangling(self) -> tuple:
        """Gates with nothing on them. Not an error, not garbage: the unit holds, produces nothing, and
        this is what asks (§9's miss), what holds attention (§7), and what makes a standing watch."""
        return tuple(g for g, v in self.latched.items() if v is None)

    def __repr__(self) -> str:
        return f"<Standing {self.name} fired={self.firings} dangling={self.dangling()}>"


@dataclass
class Surge:
    """A powered cycle crossed the threshold. A **positive fact** naming the loop it found (§8) — never
    an absence to be noticed, which is the reason energy grows rather than decays."""

    unit: str
    loop: tuple
    burned: tuple           # (cell name, unit name, gate) — the wire that was cut


class Network:
    """Standing units, standing wiring, and cells. `revive()` is the turn."""

    def __init__(self) -> None:
        self.units: list = []
        self.axioms: list = []
        self.wires: list = []           # (Cell, StandingUnit, gate)
        self.surges: list = []
        self.out_of_fuel: bool = False

    # -- construction ---------------------------------------------------------------------------

    def axiom(self, g: Graph, *, name: str = "axiom", within: Cell | None = None,
              scope: bool = False) -> Cell:
        c = Cell(name, within=within, axiom=True, scope=scope)
        c.held = Value(g)
        self.axioms.append(c)
        return c

    def suppose(self, g: Graph, *, name: str, within: Cell | None = None) -> Cell:
        """A supposition: an axiom cell that is its own containment. *"Suppose it rains."*"""
        return self.axiom(g, name=name, within=within, scope=True)

    def add(self, unit: StandingUnit) -> StandingUnit:
        self.units.append(unit)
        return unit

    def wire(self, src: Cell, dst: StandingUnit, gate: str = "in") -> None:
        """The **only** way a unit reaches anything. Wiring into a hypothesis's cell from outside is
        exactly `model.md` §6's crossing: one explicit act, no permission rule, no crossing predicate."""
        self.wires.append((src, dst, gate))

    # -- the turn -------------------------------------------------------------------------------

    def revive(self, fuel: int = 10_000) -> "Network":
        """Fire from the axioms and stabilize.

        Everything derived is recomputed here from *(axioms, wiring)* alone — invariant 15. An
        unpowered cycle is never reached, so it is **structurally silent** rather than detected and
        suppressed (§3).

        ⚠ **`fuel` is a backstop, and the spike proved it is needed.** Mutating out the surge check makes
        this loop run forever, so surge detection is the *only* termination guarantee the design supplies.
        That is exactly the fail-dangerous asymmetry of growth over decay: a decaying cycle dies whether
        or not anyone is watching, a growing one stops only because a detector fired. `model.md` §8's
        inner budget is therefore not optional here — it is the thing that holds when the detector is
        misconfigured. Exhaustion is recorded as a fact, never as a silent truncation (§8)."""
        for u in self.units:
            u.clear()
        self.surges = []
        self.out_of_fuel = False
        burned: set = set()

        queue = [(c, c.held) for c in self.axioms if c.held is not None]
        while queue:
            if fuel <= 0:
                self.out_of_fuel = True
                break
            fuel -= 1
            cell, value = queue.pop(0)
            for (src, unit, gate) in self.wires:
                if src is not cell:
                    continue
                key = (src.name, unit.name, gate)
                if key in burned:
                    continue
                revisits = value.revisits(unit.name)
                if revisits >= SURGE_AT:
                    loop = value.path[value.path.index(unit.name):]
                    self.surges.append(Surge(unit.name, tuple(dict.fromkeys(loop)), key))
                    burned.add(key)
                    continue
                out = unit.deliver(gate, value)
                if out is not None:
                    queue.append((unit.cell, out))
        return self

    # -- reads ----------------------------------------------------------------------------------

    def world(self) -> Graph:
        """The base world: axioms plus everything derived at base level. A conclusion reached inside a
        hypothesis is in a nested cell and is simply **not here** — no projection was computed and no
        rule was asked which world it was in."""
        return self.at(None)

    def at(self, scope: Cell | None) -> Graph:
        g = EMPTY
        for c in self.axioms + [u.cell for u in self.units]:
            if c.held is None:
                continue
            if c.home() is scope:
                g = g.union(c.held.graph)
        return g

    def cells(self) -> list:
        return self.axioms + [u.cell for u in self.units]

    def dangling(self) -> list:
        return [(u.name, g) for u in self.units for g in u.dangling()]


def holds(g: Graph, name: str) -> bool:
    """Is there an occurrence of `name` here? A content question, answered by looking — there is no
    index, because there is no pool to index."""
    return any(g.attr(n, "name") == name for n in g.nodes)


__all__ = ["Value", "Cell", "StandingUnit", "Network", "Surge", "holds", "SURGE_AT"]

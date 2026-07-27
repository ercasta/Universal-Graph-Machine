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
from typing import Any

from .graph import EMPTY, Graph, Node, role_edge
from .match import Match, solve

SURGE_AT = 3            # revisits of one unit before the loop is burned


# -- effects: everything a unit can conclude ----------------------------------------------------
#
# **Every effect is an overlay.** A unit never writes to the asserted layer — it produces a thought,
# which stands while the unit is powered and is gone when it is not. Only the boundary writes the base
# layer, and only with what came from outside (`model.md` §9). This is what makes hypothesis exploration
# safe without any checkpoint, copy or merge-back: a supposition's consequences are retractable because
# *all* consequences are.


@dataclass(frozen=True)
class Emit:
    """Mint an occurrence: one node, its roles, and — if the rule says so — a gradable attribute stamped
    with the firing's own match strength (§4, *"a firing may inherit its match strength"*)."""

    name: str
    roles: tuple = ()              # ((role_name, var_name), …)
    graded: str | None = None


@dataclass(frozen=True)
class Stamp:
    """Set a gradable attribute on an already-bound node, at a stated band. This is what lets a
    supposition be a *rule* rather than a Python callable (§11)."""

    target: str
    attr: str
    band: str


@dataclass(frozen=True)
class Same:
    """Conclude that two bound nodes are the same thing — **a decision, not an application.** The
    identification itself happens at write-back, so no machinery ever decides identity
    (`cnl.md` §1, *create, never merge*)."""

    left: str
    right: str


ATTRIBUTION = "attribution"


@dataclass(frozen=True)
class Overlay:
    """An attribute **derived onto a node that lives somewhere else** — as a *reified attribution*, not
    as a write.

    The overlay materialises in its producing unit's cell; the target is untouched wherever it actually
    lives. So *"Paul is 43"* from a birthday rule never edits the asserted *"Paul is 42"* — it stands
    beside it, powered by whatever powered the rule, and is gone on the next revive if that support
    goes.

    ⚠ **Reification is forced, and the spike is what forced it.** The first version wrote the attribute
    straight onto the shared node. `Graph.union` merges attributes *by node*, so two overlays disagreeing
    about one `(node, attr)` silently collapsed to whichever was unioned last — and the contradiction
    became invisible **exactly when it mattered**. Two live values for one attribute are not
    representable as attributes at all; they have to be two nodes. This is §3's argument for occurrence
    nodes arriving one level down: an attribution is a thing that is asserted, so it is a node.

    ⚠ **Overlays do not shadow and are not resolved.** Two live overlays disagreeing about one attribute
    are two readings, both present, and telling *"a man under H1, a woman under H2"* from *"a man and a
    woman"* is a **rule's** job, never the engine's (§9: contradiction handling is authored). An earlier
    draft had inner overlays shadowing outer ones, lexical-scoping style — a precedence policy hardcoded
    in the engine, which is the judgement `model.md` §11 says must stay authored."""

    target: str
    attr: str
    value: Any


@dataclass(frozen=True)
class Link:
    """An **edge** derived between two nodes that live elsewhere — optionally through a role node, which
    is how §3 requires a participant to hang off an occurrence."""

    src: str
    dst: str
    role: str | None = None


@dataclass(frozen=True)
class Merge:
    """Identify two nodes — the **applied** coreference decision, and the effect that proves a
    contribution is not confined to its producer.

    Minting a node, adding an edge and setting an attribute can all be *described* as a local fragment.
    Merging cannot: it rewrites every mention of the dropped node, anywhere in the graph. So a unit's
    output is not "a fragment that lives in a box" — it is a **revertable mutation of the whole graph**,
    and the box was a modelling error.

    It is still revertable for the same reason everything else is: the mutation is re-applied from the
    asserted layer on each revive, so a merge whose unit stops being powered simply does not happen
    again. Nothing is un-merged; the identification is not re-made.

    ⚠ The *decision* is a rule's (`cnl.md` §1, create-never-merge — no machinery may identify two nodes
    on its own). This is only its application."""

    left: str
    right: str


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
    merges: tuple = ()          # (keep, drop) pairs — mutations that are NOT local to a fragment

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
    reaches nothing else — and it records what it derived in its own `cell`. It never touches topology
    (invariant 4) and never sees a scope (invariant 1).

    ## The one flag that matters: `mutating`

    Two dispositions, and they are **not** the same thing wearing different clothes:

    | | |
    |---|---|
    | `mutating=False` — a **computation unit** | stands in the graph permanently and produces **overlays**: effects that are a function of its inputs, recomputed every revive, gone the moment its input goes. This is a *thought* |
    | `mutating=True` — a **regular rule** | fires and **applies**. Its effect is merged into the asserted layer at write-back and stays there. This is an *act* |

    Both are needed, and the split is what makes multi-turn search work at all. Hypothesis exploration
    uses computation units, so a supposition's consequences revert by the ordinary revive with no
    checkpoint, no copy and no merge-back. Search *state* — the enumerator's cursor, a recorded
    refutation — is written by a regular rule, so it survives the revive that discards everything else.

    ⚠ Firing a **mutating** rule underneath a hypothesis writes to the asserted layer for real, and the
    engine will let you. That is the same hazard as a tool call during exploration: an authoring
    problem, the one a lab has when an experiment cannot be undone (§11, the engine is
    knowledge-agnostic)."""

    def __init__(self, name: str, pattern: tuple, *effects, gates: tuple = ("in",),
                 theta: str | None = None, within: "Cell | None" = None,
                 mutating: bool = False) -> None:
        self.mutating = mutating
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
        merges: list = []
        band = None
        for m in solve(g, self.pattern, self.theta):
            for e in self.effects:
                if isinstance(e, Merge):
                    # Cannot be expressed as a fragment — it rewrites every mention, graph-wide.
                    merges.append((m[e.left], m[e.right]))
                else:
                    derived = _apply_here(derived, e, m)
            band = m.band if band is None else band

        if not derived.nodes and not merges:
            return None
        path = ()
        for v in seen:
            if len(v.path) > len(path):
                path = v.path
        out = Value(derived, band, path, tuple(merges)).through(self.name)
        self.cell.held = out
        return out

    # -- §5: a partially wired unit is a stable state --------------------------------------------

    def dangling(self) -> tuple:
        """Gates with nothing on them. Not an error, not garbage: the unit holds, produces nothing, and
        this is what asks (§9's miss), what holds attention (§7), and what makes a standing watch."""
        return tuple(g for g, v in self.latched.items() if v is None)

    def __repr__(self) -> str:
        return f"<Standing {self.name} fired={self.firings} dangling={self.dangling()}>"


def _apply_here(g: Graph, effect, m: Match) -> Graph:
    """Apply one effect into the **producing cell's** fragment. Nothing here ever writes outside it —
    that is subset output (`0008`), and it is what makes a fact's position mean something."""
    if isinstance(effect, Overlay):
        a = Node(f"{effect.attr}={effect.value}")
        g = g.with_node(a, name=ATTRIBUTION, attr=effect.attr, value=effect.value)
        return role_edge(g, a, "of", m[effect.target])
    if isinstance(effect, Link):
        if effect.role is None:
            return g.with_edge(m[effect.src], m[effect.dst])
        return role_edge(g, m[effect.src], effect.role, m[effect.dst])
    if isinstance(effect, Emit):
        occ = Node(effect.name)
        g = g.with_node(occ, name=effect.name)
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
        self.applied: bool = False
        self.record = Cell("asserted-by-rules", axiom=True)
        self.record.held = Value(EMPTY)
        self.axioms.append(self.record)

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

    def add(self, unit: "StandingUnit") -> "StandingUnit":
        self.units.append(unit)
        return unit

    def wire(self, src: Cell, dst: "StandingUnit", gate: str = "in") -> None:
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
        applied = False
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

        # WRITE-BACK, after stabilization and never during (§9). A mutating rule's effect becomes
        # asserted here and survives every subsequent revive; a computation unit's does not.
        for u in self.units:
            if u.mutating and u.cell.held is not None:
                self.record.held = Value(self.record.held.graph.union(u.cell.held.graph))
                for keep, drop in u.cell.held.merges:
                    self.record.held = Value(self.record.held.graph.merge(keep, drop))
                u.cell.held = None
                applied = True
        self.applied = applied
        return self

    # -- reads ----------------------------------------------------------------------------------

    def world(self) -> Graph:
        """The base world: axioms plus everything derived at base level. A conclusion reached inside a
        hypothesis is in a nested cell and is simply **not here** — no projection was computed and no
        rule was asked which world it was in."""
        return self.at(None)

    def at(self, scope: Cell | None) -> Graph:
        return self._assemble([c for c in self.cells() if c.home() is scope])

    def graph(self) -> Graph:
        """**The** graph: the asserted layer plus every live contribution, with graph-wide mutations
        applied.

        A contribution is not a box a fact lives in — it is a *revertable mutation*, and `Merge` is the
        one that proves it, because identifying two nodes rewrites every mention of them anywhere. So
        contributions are recorded per unit (which is what makes provenance a walk) and **applied to one
        graph** (which is what makes them mutations rather than fragments)."""
        return self._assemble(self.cells())

    def _assemble(self, cells: list) -> Graph:
        g, merges = EMPTY, []
        for c in cells:
            if c.held is None:
                continue
            g = g.union(c.held.graph)
            merges.extend(c.held.merges)
        for keep, drop in merges:
            g = g.merge(keep, drop)
        return g

    def cells(self) -> list:
        return self.axioms + [u.cell for u in self.units]

    def readings(self, node: Node, attr: str) -> list:
        """Every live value for `node.attr`, with the cell that holds it.

        A query returns **several**, and that is not a defect to be resolved — §4 already says a match
        has a strength rather than a verdict. *"Paul is a man under H1, a woman under H2"* is two
        readings, and nothing collapses them."""
        out = []
        for c in self.cells():
            if c.held is None:
                continue
            g = c.held.graph
            v = g.attr(node, attr)
            if v is not None:
                out.append((v, c))
            for n in g.nodes:                       # …and every derived attribution about it
                if g.attr(n, "name") != ATTRIBUTION or g.attr(n, "attr") != attr:
                    continue
                if any(node in g.out(r) for r in g.out(n)):
                    out.append((g.attr(n, "value"), c))
        return out

    def _owner(self, cell: Cell):
        for u in self.units:
            if u.cell is cell:
                return u
        return None

    def powering(self, unit: "StandingUnit") -> set:
        """The suppositions this unit's output rests on — walked **backwards over the wiring**.

        This is what makes blame assignment possible without any rule naming a scope (invariant 1). A
        contradiction refutes *the configuration that powered it*; the configuration is not something a
        detector is told, it is something the wiring already records. Provenance doing real work."""
        scopes, seen, stack = set(), set(), [unit]
        while stack:
            u = stack.pop()
            if id(u) in seen:
                continue
            seen.add(id(u))
            for cell in [u.cell] + [s for (s, d, _) in self.wires if d is u]:
                c = cell.home()
                while c is not None:
                    if c.scope:
                        scopes.add(c)
                    c = c.within
                owner = self._owner(cell)
                if owner is not None:
                    stack.append(owner)
        return scopes

    def dangling(self) -> list:
        return [(u.name, g) for u in self.units for g in u.dangling()]


def holds(g: Graph, name: str) -> bool:
    """Is there an occurrence of `name` here? A content question, answered by looking — there is no
    index, because there is no pool to index."""
    return any(g.attr(n, "name") == name for n in g.nodes)


__all__ = ["Value", "Cell", "StandingUnit", "Network", "Surge",
           "Emit", "Stamp", "Same", "Overlay", "Link", "holds", "SURGE_AT"]

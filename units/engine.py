"""THE ENGINE — one machine.

Supersedes `standing.py` (propagating, fragment-union reads, `Cell.within`/`Cell.scope`) and `turn.py`
(fixpoint iteration, no matching). Those were three partial machines that did not compose; this is the
consolidation, and it implements `model.md` as revised by `revision-01` and `revision-02`.

## What the consolidation actually joins

`revision-02` §3 said *scope is support* and both halves were built without ever meeting: `overlay.py`
took a configuration as **declared**, and `standing.py` computed one by **walking the wiring**. Here they
meet, and the join turns out to need less than expected:

> **A unit needs no configuration at all.** It sees only what its gates delivered (`model.md` §5), and a
> supposition's contributions reach exactly the units wired downstream of it. Scope is not read, it is
> *wiring* — the tunnel, free, as §6 always promised.

Configurations are needed only for **reads of the assembled whole**, where `powering()` says which
suppositions each unit's output rests on. So `under` appears in `Network.graph()` and never in a unit.

## Power is plane 2; readability is plane 1

The distinction that decides this module's shape. A value arriving on a wire is what makes a unit fire;
what a unit can *read* is the overlay composition of its gates. A deletion changes readability. It does
**not** un-deliver anything, so it cannot withdraw the power that produced it.

⚠ `turn.py` conflated the two — it recomputed every unit's premise from the current view each round, so a
deletion could unpower its own producer, and the self-undermining case oscillated. That oscillation is a
property of *that* evaluation strategy, not of deletion. See `test_engine.py`.

## What each piece is

| | plane | |
|---|---|---|
| `Graph` (asserted) | 1 | what came from outside, plus what mutating rules applied |
| effects on a wire | 1 | proposals — overlays, composed lazily by `Overlays` |
| `Cell` | 2 | a *record of what a unit contributed*, not a box a fact lives in |
| `StandingUnit`, wires, gate energy | 2 | the running circuit |
| `unit.node` | 1 | the unit **as data**, so a fact can be about it (homoiconicity) |
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .graph import EMPTY, Graph, Node, role_edge
from .match import AttrVar, Match, atom, role, solve
from .overlay import (BASE, AddEdge, Grade, Identify, Mint, Overlays, Retract, SetAttr, View)

SURGE_AT = 3            # times one gate's input may CHANGE before the loop is burned
SILENCED = "silenced"   # a unit carrying this produces nothing — see `bundled_silence_rule`
SURGED = "surged"       # the engine's only write: it reports, and a rule decides (`rev-02` §7)
ENGINE = "<engine>"     # the only source the engine contributes under

# -- tier 0: the wiring register's vocabulary (`forms_cnl.md` §6) ---------------------------------
#
# The whole of it. `pattern:` is tier 0 too and is not yet used here — a unit's *pattern* is still a
# Python object, which is the next thing this register has to swallow.

WIRE = "<wire>"         # the occurrence: a 3-place relation, source × target × gate (`rev-02` §5)
FROM = "from"
TO = "to"
GATE = "gate"
OUT = "out"             # a unit → the cell its output is held in


# -- effect templates: what a rule says, before a match instantiates it --------------------------
#
# A rule is written against *variables*; `overlay.py`'s effects name *nodes*. These are the templates,
# and `instantiate` is the only place the two meet.

@dataclass(frozen=True)
class Emit:
    """Mint an occurrence: a node, its role nodes, and optionally a band from the firing's own match
    strength (§4, *a firing may inherit its match strength*)."""

    name: str
    roles: tuple = ()              # ((role_name, var_name), …)
    graded: str | None = None


@dataclass(frozen=True)
class Attribute:
    """A crisp attribute derived onto a bound node. Applies as a **reified attribution**, never a write
    (`rev-02` §6) — which is what keeps two live disagreeing derivations visible as a conflict."""

    target: str
    attr: str
    value: Any


@dataclass(frozen=True)
class Stamp:
    """A gradable attribute at a stated band. Bands **meet** rather than conflict (`overlay.Grade`)."""

    target: str
    attr: str
    band: str


@dataclass(frozen=True)
class Link:
    target: str
    dst: str
    role: str | None = None


@dataclass(frozen=True)
class Merge:
    """Identify two bound nodes — the *applied* coreference decision. The decision is a rule's
    (`cnl.md` §1, create-never-merge); this is only its application."""

    left: str
    right: str


@dataclass(frozen=True)
class Drop:
    """Remove something. A **computation unit**'s drop hides while powered; a **mutating rule**'s is
    applied to the asserted layer at write-back and is real (`rev-01` §2)."""

    target: str
    attr: str | None = None
    source: str | None = None


BOUND = "<bound>"       # in a premise-bound rule, the node the premise matched


def effects_of(g: Graph) -> tuple:
    """A graph, expressed as the proposals that would produce it.

    This is what makes *"a turn begins by firing from the axioms"* literal (`rev-01` §3): the asserted
    layer is not an ambient store units dip into, it is a set of contributions **with no predecessors**,
    delivered on wires like everything else. A unit that wants to read `name` must be wired to where the
    name is — subset output (`0008`), and the discipline the whole design rests on."""
    out: list = []
    for n in g.nodes:
        out.append(Mint(n, tuple(sorted(g.attrs.get(n, {}).items()))))
        for k, b in g.degrees.get(n, {}).items():
            out.append(Grade(n, k, b))
    out += [AddEdge(a, b) for a, b in g.edges]
    return tuple(out)


def instantiate(template, m: Match) -> tuple:
    """One template plus one match becomes zero or more overlay effects."""
    if isinstance(template, Emit):
        occ = Node(template.name)
        out = [Mint(occ, (("name", template.name),))]
        for role_name, var in template.roles:
            r = Node(role_name)
            out += [Mint(r, (("name", role_name),)), AddEdge(occ, r), AddEdge(r, m[var])]
        if template.graded is not None and m.band is not None:
            out.append(Grade(occ, template.graded, m.band))
        return tuple(out)
    if isinstance(template, Attribute):
        return (SetAttr(m[template.target], template.attr, template.value),)
    if isinstance(template, Stamp):
        return (Grade(m[template.target], template.attr, template.band),)
    if isinstance(template, Link):
        if template.role is None:
            return (AddEdge(m[template.target], m[template.dst]),)
        r = Node(template.role)
        return (Mint(r, (("name", template.role),)),
                AddEdge(m[template.target], r), AddEdge(r, m[template.dst]))
    if isinstance(template, Merge):
        a, b = m[template.left], m[template.right]
        return () if a is b else (Identify(a, b),)
    if isinstance(template, Drop):
        return (Retract(m[template.target], template.attr, template.source),)
    raise TypeError(f"unknown effect template {template!r}")


# -- what travels, and what records ---------------------------------------------------------------

@dataclass(frozen=True)
class Value:
    """What travels on a wire: **effects**, not a graph.

    ⚠ `standing.py` carried `graph: Graph` *and* `merges: tuple` beside it, because `Merge` rewrites
    every mention and could not be expressed as a fragment. One effect type not fitting the container was
    the container being wrong (`rev-02` §6). Here every effect is the same kind of thing.

    ⚠ There is no `path`. Energy lives at the **gate** as a count of input *changes*, so a long acyclic
    chain costs nothing and no history is carried."""

    effects: tuple = ()
    band: str | None = None


class Cell:
    """A **record of what a unit contributed** — plane 2, holding plane-1 content.

    ⚠ `within` and `scope` are gone (`rev-02` §3). They made containment a second axis of *position*,
    when scope is **support**: not a place a fact sits but which configuration powers it. That mistake is
    also what `revision-01` §8's "seal leak" really was.

    `node` is the cell **as data** — what a wire's `from:` names. Without it the wiring register has
    nothing to point at and topology stays a Python list."""

    __slots__ = ("name", "axiom", "supposes", "held", "node", "owner")

    def __init__(self, name: str, *, axiom: bool = False, supposes: str | None = None) -> None:
        self.name = name
        self.axiom = axiom
        self.supposes = supposes        # this cell IS a supposition, named
        self.held: Value | None = None
        self.node = Node(name)
        self.owner: "StandingUnit | None" = None

    def __repr__(self) -> str:
        return f"<Cell {self.name}{' axiom' if self.axiom else ''}{'' if self.held else ' empty'}>"


class StandingUnit:
    """A unit that stands. It matches over the composition of its gates and records what it derived.

    **It sees only its gates** (invariant 3). There is no ambient store, and therefore no configuration
    to be in: a supposition's contributions arrive because something wired them here, or they do not
    arrive at all. That is the tunnel, and it costs nothing."""

    def __init__(self, name: str, pattern: tuple, *effects, gates: tuple = ("in",),
                 theta: str | None = None, mutating: bool = False,
                 bind: str | None = None) -> None:
        self.name = name
        self.pattern = pattern
        self.effects = effects
        self.gates = tuple(gates)
        self.theta = theta
        self.mutating = mutating
        self.bind = bind                # premise variable a BOUND effect refers to
        self.node = Node(name)          # the unit AS DATA — homoiconicity (`rev-02` §§1, 5)
        self.latched: dict = {g: None for g in self.gates}
        self.changes: dict = {g: 0 for g in self.gates}
        self.cell = Cell(f"{name}:out")
        self.cell.owner = self
        self.firings = 0

    def clear(self) -> None:
        """A revive throws away *values*, never wiring (`rev-01` §3)."""
        self.latched = {g: None for g in self.gates}
        self.changes = {g: 0 for g in self.gates}
        self.cell.held = None
        self.firings = 0

    def view(self) -> View:
        """Everything this unit can see: its gates, composed. Nothing else exists for it."""
        effects: list = []
        for v in self.latched.values():
            if v is not None:
                effects.extend((self.name, e) for e in v.effects)
        return Overlays(EMPTY, effects).view()

    def deliver(self, gate: str, value: Value) -> Value | None:
        if gate not in self.latched:
            raise KeyError(f"{self.name} has no gate {gate!r} (gates: {self.gates})")
        self.latched[gate] = value
        return self.fire()

    def fire(self) -> Value | None:
        """Match and emit. `None` is *a unit that had nothing to say* — not an error and not a miss."""
        self.firings += 1
        if not any(v is not None for v in self.latched.values()):
            return None
        produced: list = []
        band = None
        for m in solve(self.view(), self.pattern, self.theta):
            for t in self.effects:
                produced.extend(instantiate(t, m))
            band = m.band if band is None else band
        if not produced:
            return None
        out = Value(tuple(produced), band)
        self.cell.held = out
        return out

    def dangling(self) -> tuple:
        """Gates with nothing on them. Not an error: this is what asks (§9's miss), what holds attention
        (§7), and what makes a standing watch (`rev-01` §5)."""
        return tuple(g for g, v in self.latched.items() if v is None)

    def __repr__(self) -> str:
        return f"<Unit {self.name} fired={self.firings} dangling={self.dangling()}>"


# The register's whole grammar, as an ordinary pattern over ordinary data. Nothing privileged: it finds
# wires because it *names* `<wire>`, `from`, `to` and `gate` — invariant 19, and the reason machinery
# needs no partition. The gate arrives as an attribute value, not a node, via `AttrVar`.
_WIRE_PATTERN = (atom("w", name=WIRE, out=(role(FROM, atom("src")),
                                           role(TO, atom("dst")),
                                           role(GATE, atom("g", name=AttrVar("gate"))))),)


def _grew(prior: Value, value: Value) -> bool:
    """Did this input only **gain** effects? Then it is not energy.

    `rev-02` §6's monotonicity theorem, applied one level down. That argument — *mint, edge and
    attribute only ever make more things readable, so a gate going present → absent is proof a
    non-monotone effect fired* — is about a gate's **readable set**; the same reasoning holds of the
    value on the wire, and without it a value that merely accumulates registers as a change.

    ⚠ **Found by the corrector burning itself.** Once `bundled:silence` could fire at all, a network
    with four loops surged four times, and each surge extended the report on the rule's one gate — so
    at the third the detector burned the *corrector*, and the fourth loop went uncorrected. That is
    counting growth as cycling, which is `model.md` §5's per-hop mistake in new clothes.

    ⚠ **The cost is that monotone-but-infinite is now even more squarely fuel's job** — a `rev-02` §9
    open item, and this narrows the detector's remit onto the case its theorem actually covers."""
    try:
        return set(prior.effects) <= set(value.effects)
    except TypeError:                   # an unhashable effect payload: no claim, so no exemption
        return False


@dataclass(frozen=True)
class Surge:
    """A gate whose input kept changing. A **positive fact** naming the unit, the gate and the loop —
    never an absence to be noticed, which is why energy grows rather than decays."""

    unit: str
    gate: str
    loop: tuple
    flips: int


class Network:
    """Asserted data, standing units, standing wiring. `revive()` is the turn.

    ⚠ **The wiring is not a field.** `self.wires` used to be a Python list of tuples, which made
    invariant 18 false (*everything persistent is plane 1*) and made the front end's target an **engine
    API** — the one thing `model.md` §11 forbids. Topology is now **derived** from `self.asserted` by
    `assemble()`, and `wire()` is a convenience that writes the fact `assemble()` reads. Anything that
    can write a graph can wire — including a mutating rule, which is invariant 4's *units propose
    wirings as facts* actually cashed."""

    def __init__(self, asserted: Graph = EMPTY) -> None:
        self.asserted = asserted
        self.units: list = []
        self.axioms: list = []
        self.surges: list = []
        self.out_of_fuel = False
        self.applied: tuple = ()
        self._built: dict = {}          # plane-1 node → the plane-2 object it describes
        self._wiring: tuple = ()
        self._wiring_of: Graph | None = None
        # The engine's report, as a cell — see `reports`.
        self.reports = Cell(ENGINE)
        self._describe(self.reports.node, self.reports, name=ENGINE)

    # -- construction -----------------------------------------------------------------------------

    def axiom(self, *effects, name: str = "axiom", supposes: str | None = None) -> Cell:
        c = Cell(name, axiom=True, supposes=supposes)
        c.held = Value(tuple(effects))
        self.axioms.append(c)
        self._describe(c.node, c, name=name)
        return c

    def given(self, g: Graph, *, name: str = "given") -> Cell:
        """Assert a graph. It joins the store **and** becomes an axiom that delivers it onto wires."""
        self.asserted = self.asserted.union(g)
        return self.axiom(*effects_of(g), name=name)

    def supposing(self, g: Graph, *, name: str) -> Cell:
        """*"Suppose it rains."* Delivered on wires like an axiom, but **not** joined to the store — a
        supposition is not a thing that happened."""
        return self.axiom(*effects_of(g), name=name, supposes=name)

    def suppose(self, *effects, name: str) -> Cell:
        """*"Suppose it rains."* An axiom whose contributions carry its own name as support, so anything
        downstream of it is inside it — and nothing else can see it, because nothing else is wired."""
        return self.axiom(*effects, name=name, supposes=name)

    def add(self, unit: StandingUnit) -> StandingUnit:
        self.units.append(unit)
        # Units are plane-1 data: the node goes in the same graph as everything else, with no machinery
        # partition (`rev-02` §5). Ordinary rules do not match it for the ordinary reason — nothing
        # matches implicitly (invariant 19).
        self._describe(unit.node, unit, name=unit.name)
        self._describe(unit.cell.node, unit.cell, name=unit.cell.name)
        # …and the unit's `out:` role, so a wire can be written naming only the unit.
        self.asserted = role_edge(self.asserted, unit.node, OUT, unit.cell.node)
        return unit

    def wire(self, src: Cell, dst: StandingUnit, gate: str = "in") -> None:
        """The only way a unit reaches anything. Wiring out of a supposition's cell is `model.md` §6's
        crossing: one explicit act, no permission rule, no crossing predicate.

        ⚠ **This is not where wiring lives.** It writes a `<wire>` occurrence — source, target and gate,
        each through its own role node, because an edge is nameless and a 3-place relation cannot be one
        (`rev-02` §5). `assemble()` reads it back. Write the same occurrence by hand, or conclude it from
        a rule, and the circuit is wired just the same."""
        w, gate_node = Node(WIRE), Node(gate)
        g = self.asserted.with_node(w, name=WIRE).with_node(gate_node, name=gate)
        g = role_edge(g, w, FROM, src.node)
        g = role_edge(g, w, TO, dst.node)
        self.asserted = role_edge(g, w, GATE, gate_node)

    def _describe(self, node: Node, obj, **crisp) -> Node:
        """Put a plane-2 object's description in the graph and record the crossing.

        This map is **the assembler**, and it is the only place plane 1 and plane 2 meet. It holds
        nothing invariant 18 forbids: it is rebuilt by construction, never carried across a revive."""
        self.asserted = self.asserted.with_node(node, **crisp)
        self._built[node] = obj
        return node

    # -- the wiring register ------------------------------------------------------------------------

    def assemble(self) -> tuple:
        """**Read the topology out of the graph.** `forms_cnl.md` §1's assembler: it wires what the
        register describes and never sees a statement.

        A description naming something that was never built is **skipped, not an error** — the same
        stance as a dangling gate (invariant 14). Ordered by the wire node's mint order so a run is
        reproducible; nothing semantic rests on it (invariant 15)."""
        found: list = []
        for m in solve(self.asserted, _WIRE_PATTERN):
            src, dst = self._built.get(m["src"]), self._built.get(m["dst"])
            if not isinstance(src, Cell) or not isinstance(dst, StandingUnit):
                continue
            found.append((m["w"].nid, src, dst, m.values["gate"]))
        return tuple((s, d, g) for _nid, s, d, g in sorted(found, key=lambda t: t[0]))

    @property
    def wires(self) -> tuple:
        """Derived, and cached against the graph value it was derived from. `Graph` is immutable, so an
        identity check is exact: a new graph is a new value, and re-assembly is due."""
        if self._wiring_of is not self.asserted:
            self._wiring_of = self.asserted
            self._wiring = self.assemble()
        return self._wiring

    # -- the turn ---------------------------------------------------------------------------------

    def revive(self, fuel: int = 10_000) -> "Network":
        """Fire from the axioms and stabilize. Everything derived is recomputed from *(axioms, wiring)*
        alone — invariant 15."""
        for u in self.units:
            u.clear()
        self.surges = []
        self.reports.held = None
        self.out_of_fuel = False
        burned: set = set()
        reported: set = set()

        queue = [(c, c.held) for c in self.axioms if c.held is not None]
        while queue:
            if fuel <= 0:
                self.out_of_fuel = True
                break
            fuel -= 1
            cell, value = queue.pop(0)
            for (src, unit, gate) in self.wires:
                if src is not cell or (src.name, unit.name, gate) in burned:
                    continue
                # Energy at the gate: has this input CHANGED again? A first arrival is not a change, so
                # a chain — which delivers once per gate — costs nothing at any depth.
                prior = unit.latched.get(gate)
                if prior is not None and prior != value and not _grew(prior, value):
                    unit.changes[gate] += 1
                    if unit.changes[gate] >= SURGE_AT:
                        key = (src.name, unit.name, gate)
                        if key not in reported:
                            self.surges.append(
                                Surge(unit.name, gate, self.loop_through(unit), unit.changes[gate]))
                            reported.add(key)
                            queue.append(self.report(SetAttr(unit.node, SURGED, gate)))
                        burned.add(key)
                        continue
                if self.silenced(unit):
                    continue
                out = unit.deliver(gate, value)
                if out is not None:
                    queue.append((unit.cell, out))

        self.write_back()
        return self

    def report(self, *effects) -> tuple:
        """The engine's **only** contribution, and it now travels like everything else.

        ⚠ A report the engine merely *writes into the read layer* is one no rule can act on, because a
        unit sees only its gates (invariant 3). That is the shape the surge correction was in: `surged`
        appeared in `graph()` and reached no unit, so `bundled:silence` could not fire whatever its
        pattern said. Reporting on a **cell** puts the plane-1 → plane-2 interface where every other
        value already crosses, and costs no new mechanism.

        Accumulative within a turn: `rev-02` §6's *"a report must persist for the turn; a conclusion
        must not"*."""
        prior = self.reports.held.effects if self.reports.held is not None else ()
        self.reports.held = Value(prior + tuple(effects))
        return (self.reports, self.reports.held)

    def write_back(self) -> tuple:
        """Apply what **mutating rules** concluded to the asserted layer — after stabilization, never
        during (`model.md` §9). A computation unit's output is never applied; it is recomputed.

        ⚠ **Not after a turn that failed to settle.** A surge means no answer was reached, so applying
        a partial one would let an unstable configuration edit the world a little on every attempt.

        ⚠ **Identifications are applied last, deliberately.** `revision-02` §6 finding 4: applying a
        merge eagerly rewrites only the mentions that exist *at that moment*, so a later effect naming
        the dropped node re-introduces it. Reads avoid this by being lazy; the store cannot, because it
        is a `Graph`. Ordering identifications last is the narrowest fix, and it is the one place in the
        design where effect order still matters."""
        if self.surges or self.out_of_fuel:
            return ()
        applied: list = []
        for u in self.units:
            # ⚠ **A rule inside a supposition has not acted.** `rev-02` §6 argued scoping is free —
            # *"a deletion inside a supposition does not reach the base world, with no extra
            # machinery"* — and that is true of **overlays**, which are read under a configuration. It
            # was never true of write-back, which applies to the store with no configuration at all. So
            # *"suppose it rains"* wired to a mutating rule really took the umbrella.
            #
            # Support is the filter, exactly as it is on the read path (§3). Measured 2026-07-27 while
            # probing whether `suppose` can discharge; this was the other half of that probe.
            if u.mutating and u.cell.held is not None and not self.powering(u):
                applied.extend(u.cell.held.effects)
        merges = [e for e in applied if isinstance(e, Identify)]
        for e in [x for x in applied if not isinstance(x, Identify)] + merges:
            if isinstance(e, Mint):
                self.asserted = self.asserted.with_node(e.node, **dict(e.attrs))
            elif isinstance(e, AddEdge):
                self.asserted = self.asserted.with_edge(e.src, e.dst)
            elif isinstance(e, SetAttr):
                self.asserted = self.asserted.with_node(e.target, **{e.attr: e.value})
            elif isinstance(e, Grade):
                self.asserted = self.asserted.with_degree(e.target, e.attr, e.band)
            elif isinstance(e, Retract):
                self.asserted = self.asserted.without(e.target, e.attr)
            elif isinstance(e, Identify):
                self.asserted = self.asserted.merge(e.keep, e.drop)
        self.applied = tuple(applied)
        return self.applied

    def silenced(self, unit: StandingUnit) -> bool:
        """Has a rule concluded that this unit should stop? Read from the graph, because the correction
        is *a rule's conclusion* and rules conclude facts (invariant 4, *units propose wirings as
        facts*)."""
        return self.graph().attr(unit.node, SILENCED) is not None

    # -- reads ------------------------------------------------------------------------------------

    def _live(self) -> tuple:
        held = self.reports.held
        effects = [(ENGINE, e) for e in (held.effects if held is not None else ())]
        support = {ENGINE: frozenset()}
        for c in self.axioms:
            if c.held is None:
                continue
            effects += [(c.name, e) for e in c.held.effects]
            support[c.name] = frozenset({c.supposes} if c.supposes else ())
        for u in self.units:
            if u.cell.held is not None:
                effects += [(u.name, e) for e in u.cell.held.effects]
            support[u.name] = self.powering(u)
        return tuple(effects), support

    def overlays(self) -> Overlays:
        effects, support = self._live()
        return Overlays(self.asserted, list(effects), support)

    def graph(self, under: frozenset | None = None) -> View:
        """**The** graph in a configuration. `under=None` means *everything live*, which is the
        debugging view; `world()` is the honest one."""
        o = self.overlays()
        if under is None:
            under = frozenset(c.supposes for c in self.axioms if c.supposes)
        return o.view(under)

    def world(self) -> View:
        """The base world: what is derived by units **not powered by any supposition**.

        ⚠ Not a place — a *filter*. A conclusion reached inside a hypothesis is simply not here, and
        nothing computed a projection to exclude it (`rev-02` §3)."""
        return self.overlays().view(frozenset())

    def powering(self, unit: StandingUnit) -> frozenset:
        """The suppositions this unit's output rests on — walked **backwards over the wiring**.

        This is scope, and it is the reason no rule ever names one (invariant 1). A contradiction
        condemns whatever configuration fed the detector, and the configuration is not something a
        detector is told: it is what the wiring already records."""
        found, seen, stack = set(), set(), [unit]
        while stack:
            u = stack.pop()
            if id(u) in seen:
                continue
            seen.add(id(u))
            for (src, dst, _g) in self.wires:
                if dst is not u:
                    continue
                if src.supposes:
                    found.add(src.supposes)
                owner = self._owner(src)
                if owner is not None:
                    stack.append(owner)
        return frozenset(found)

    def loop_through(self, unit: StandingUnit) -> tuple:
        """The cycle this unit sits on, read off the **wiring** by walking backwards. The loop was never
        in the value; it is in the topology, and provenance here is the wiring."""
        def back(u, seen):
            for (src, dst, _g) in self.wires:
                if dst is not u:
                    continue
                owner = self._owner(src)
                if owner is None:
                    continue
                if owner is unit:
                    return seen
                if owner.name in seen:
                    continue
                found = back(owner, seen + [owner.name])
                if found:
                    return found
            return None
        return tuple(dict.fromkeys(back(unit, [unit.name]) or [unit.name]))

    def _owner(self, cell: Cell):
        return cell.owner

    def _unit_named(self, name: str):
        return next(u for u in self.units if u.name == name)

    def dangling(self) -> list:
        return [(u.name, g) for u in self.units for g in u.dangling()]


def bundled_silence_rule(net: Network) -> StandingUnit:
    """**The surge correction, shipped as an ordinary rule** — *anything that surged: stop its output.*

    No privileged status and no engine hook. It is written *about units*, which it can only be because a
    unit is plane-1 data with a node of its own. Shipping it as a rule rather than as engine policy is
    the composability principle: a governance mechanism hardcoded in Python is an unreachable island.

    ⚠ **Two defects were found here by trying to make it fire**, and both were invisible to a test that
    only checked the engine's half:

    1. the pattern was `surged=None`, which reads as *"`surged` equals `None`"* — and `attr` returns
       `None` for an attribute that is **absent**, so it matched every node **except** the surged one.
       The matcher has no *"present, any value"* atom; `AttrVar` **is** one, because it fails when the
       attribute is missing. That is this rule's whole fix, and it is also the general answer;
    2. it was wired to whatever the author happened to wire it to, and `surged` was never on a wire at
       all. It is wired to `net.reports` here, which is the only place it can see one."""
    u = net.add(StandingUnit("bundled:silence", (atom("s", **{SURGED: AttrVar("gate")}),),
                             Attribute("s", SILENCED, True)))
    net.wire(net.reports, u)
    return u


def readable(view: View, nodes) -> dict:
    """Every crisp attribute readable about these nodes, as a plain dict.

    A comparison surface for order-independence testing (invariant 15). It reads *content*, not node
    identity, because `Emit` mints a fresh node per firing — so two runs that agree perfectly still hold
    different `Node` objects, and identity comparison would report a difference that is not one."""
    out: dict = {}
    for n in nodes:
        keys = set(view._o.base.attrs.get(n, {}))
        keys |= {a for a, _v, _s in view._o._attribs.get(view._o.resolve(n), ())}
        for k in keys:
            v = view.attr(n, k)
            if v is not None:
                out[(n.nid, k)] = v
    return out


__all__ = ["Emit", "Attribute", "Stamp", "Link", "Merge", "Drop", "instantiate", "effects_of",
           "Value", "Cell", "StandingUnit", "Surge", "Network", "bundled_silence_rule", "readable",
           "SURGE_AT", "SILENCED", "SURGED", "ENGINE", "BOUND",
           "WIRE", "FROM", "TO", "GATE", "OUT"]

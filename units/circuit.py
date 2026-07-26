"""STATEMENTS, SEALS, TUNNELS — `docs/units/model.md` §6, and the assembler of §7 step 2.

This is the module the whole paradigm flip exists for, so the claims it is meant to make true are worth
naming before the code:

1. **A statement is logically atomic but physically a chain**, reconciled by explicit markers — and
   **only the end marker is attachable** (§12 invariant 9). Here that is mechanical rather than checked:
   a wire's source must be a `Port`, and the only way to obtain a `Port` is `Statement.end`. There is no
   accessor that yields a port for an interior unit, so a sealed span cannot be wired into by anyone who
   stays inside the API. `wire()` refuses a raw `Unit` with `SealBreach` for the people who don't.

2. **The tunnel is the value on the wire.** A supposition is an ordinary graph-to-graph unit (see
   `unit.transform`), so everything wired downstream of it receives the supposed graph and computes in
   that scope *without knowing it exists*. Isolation is not enforced by a check; it is a consequence of
   what is wired to what.

3. **No rule ever matches a scope** (§12 invariant 1). Nothing in this module puts a scope marker into a
   graph, so there is nothing for a pattern to match even if an author wanted to.

4. **Getting out is one explicit act.** A conclusion is stuck in the tunnel until something attaches to
   the end marker. No permission rule, no crossing predicate, no data — someone attached, or they didn't.

**The assembler does no semantics** (§7). It wires what it is told and runs; it does not match, decide,
scope, or interpret. It also does not *unroll* — a statement's chain arrives already described
(`cnl.md` §4), and here that description is hand-written, which is exactly the part a spike stubs.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .graph import EMPTY, Graph
from .unit import Miss, Unit


class SealBreach(Exception):
    """Raised on an attempt to wire into or out of a statement's interior (§6)."""


@dataclass(frozen=True)
class Port:
    """A statement's **end marker** — its one output port, and the only place a new wire may attach or a
    result may be written back."""

    statement: "Statement"

    def __repr__(self) -> str:
        return f"<Port end-of:{self.statement.label}>"


class Statement:
    """A sealed span: a begin marker, a chain of steps, an end marker.

    A step is a `Unit` or another `Statement` — **nesting is physical** (§6), and that is the whole of
    what hypotheses, embedded clauses, attributed beliefs and counterfactual worlds are. There is no
    scope object, no world identifier, and no comparability test."""

    def __init__(self, label: str, steps: tuple) -> None:
        if not steps:
            raise ValueError("a statement needs at least one step")
        self.label = label
        self.steps = tuple(steps)

    @property
    def end(self) -> Port:
        """The output port. Deliberately the *only* public handle on this statement's insides."""
        return Port(self)

    @property
    def _first(self) -> Unit:
        s = self.steps[0]
        return s._first if isinstance(s, Statement) else s

    @property
    def _last(self) -> Unit:
        s = self.steps[-1]
        return s._last if isinstance(s, Statement) else s

    def _interior(self) -> list:
        out = []
        for s in self.steps:
            out.extend(s._interior() if isinstance(s, Statement) else [s])
        return out

    def __repr__(self) -> str:
        return f"<Statement {self.label} steps={len(self.steps)}>"


@dataclass
class Fuel:
    """§5: a loop dies by running out of data, or by fuel — **it does not die by settling.**

    Only the *inner* budget. §8's outer budget (*"I stopped thinking about this"*, as distinct from
    *"this computation didn't converge"*) is not built here."""

    limit: int = 500
    spent: int = 0

    def burn(self) -> bool:
        self.spent += 1
        return self.spent < self.limit

    @property
    def exhausted(self) -> bool:
        return self.spent >= self.limit


class Circuit:
    """The assembled, transient network. Built each step, used, and thrown away (§1)."""

    def __init__(self) -> None:
        self.wires: dict = {}          # producer Unit -> [(consumer Unit, gate)]
        self.units: list = []
        self.statements: list = []
        self.sinks: dict = {}          # Port -> [Graph, …] collected at write-back
        self.fuel = Fuel()

    # -- assembly ------------------------------------------------------------------------

    def statement(self, label: str, *steps) -> Statement:
        """Mint a sealed statement and wire its interior. The interior wiring happens **here and only
        here** — which is why nothing outside can reach into it afterwards."""
        st = Statement(label, steps)
        for s in steps:
            if isinstance(s, Unit) and s not in self.units:
                self.units.append(s)
        for a, b in zip(steps, steps[1:]):
            producer = a._last if isinstance(a, Statement) else a
            consumer = b._first if isinstance(b, Statement) else b
            self._connect(producer, consumer, consumer.gates[0])
        self.statements.append(st)
        return st

    def wire(self, src, dst, gate: str | None = None) -> None:
        """Attach `src` to `dst`. **`src` must be a `Port`**; `dst` may be a unit or a statement.

        The asymmetry is the seal, and it is worth saying out loud: you may attach **to** a statement —
        at its begin marker, which is how anything is fed at all — but you may only attach **from** its
        end. A statement's interior is reachable in neither direction.

        This is scope-crossing (§6), and it needs no permission rule, no crossing predicate and no data:
        it is simply whether someone attached to the end marker."""
        if isinstance(src, Unit):
            raise SealBreach(
                f"cannot wire from the unit {src.name!r}: only a statement's end marker is attachable "
                f"(model.md §6, §12 invariant 9). Use <statement>.end.")
        if not isinstance(src, Port):
            raise TypeError(f"wire source must be a Port, got {type(src).__name__}")
        consumer = dst._first if isinstance(dst, Statement) else dst
        self._connect(src.statement._last, consumer, gate or consumer.gates[0])

    def _connect(self, producer: Unit, consumer: Unit, gate: str) -> None:
        self.wires.setdefault(producer, []).append((consumer, gate))

    def write_back(self, port: Port) -> None:
        """Attach a collector to a port. Conclusions arriving here leave the circuit and become data
        (§9). Without one, whatever the tunnel concluded stays in the tunnel."""
        self.sinks.setdefault(port.statement._last, []).append(port)

    # -- running -------------------------------------------------------------------------

    def feed(self, target, value: Graph, gate: str | None = None) -> "Run":
        """Deliver a value at a statement's begin marker (or a bare unit's gate) and propagate.

        Nothing happens unbidden (§1): absent this call the circuit is silent."""
        unit = target._first if isinstance(target, Statement) else target
        run = Run(self)
        run._propagate([(unit, gate or unit.gates[0], value)])
        return run


class Run:
    """One pass of a circuit, and the outcomes it produced."""

    def __init__(self, circuit: Circuit) -> None:
        self.circuit = circuit
        self.collected: dict = {}      # Port -> Graph
        self.out_of_fuel = False

    def _propagate(self, queue: list) -> None:
        c = self.circuit
        while queue:
            if not c.fuel.burn():
                self.out_of_fuel = True     # §8: a positive fact, never silence
                return
            unit, gate, value = queue.pop(0)
            out = unit.deliver(gate, value)
            for port in c.sinks.get(unit, ()):
                self.collected[port] = out
            for consumer, g in c.wires.get(unit, ()):
                queue.append((consumer, g, out))

    # -- outcomes ------------------------------------------------------------------------

    def written_back(self, port: Port) -> Graph:
        """What crossed out of `port`. `EMPTY` if nothing was ever attached — which is the honest
        report: the conclusion exists, it just never left the tunnel."""
        return self.collected.get(port, EMPTY)

    def misses(self) -> list:
        return [m for u in self.circuit.units for m in u.misses()]


__all__ = ["Circuit", "Statement", "Port", "Run", "Fuel", "SealBreach"]

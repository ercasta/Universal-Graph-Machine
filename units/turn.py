"""THE TURN, minimally — `docs/units/revision-02-two-planes.md` §6, the deletion dynamics.

A spike with one question: **what happens when a unit deletes its own power source?**

Deletion is the only effect that can subtract a unit's own premise. Mint, edge, attribute and identify
only ever add, so under revive-from-axioms a unit can never undermine itself. A deletion can, and that
is a dynamic behaviour none of the other four introduce.

## Deliberately smaller than the real thing

Matching is not exercised here — a unit's premise is *one readable slot*, not a pattern. Gates do not
latch and there is no energy. All of that is `standing.py`'s job. Stripping it is the point: what is
left is only the interaction between **what is readable** and **what is powered**, which is exactly the
thing in question. Adding latching or partial wiring would let a result be explained by them instead.

## The one thing it does model faithfully

Units read through `Overlays`, so a unit sees the graph *as it stands including other units' deletions*
— the same view System 1 recalls against (`model.md` §7). If reads did not go through the overlays there
would be no question to ask.

`turn()` iterates to a fixpoint rather than propagating once, because a fixpoint is what **exposes**
instability instead of hiding it behind an arbitrary evaluation order. An oscillation is reported as a
positive fact, never as a silent truncation (`model.md` §8).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .graph import EMPTY, Graph, Node
from .overlay import BASE, Overlays, Retract


@dataclass(frozen=True)
class Unit:
    """A unit reduced to what this spike needs: a premise, effects, and a disposition.

    `premise` is `(node, attr)` — the unit fires while that slot is **readable**. `mutating=True` is
    `revision-01` §2's regular rule: its effects are applied to the asserted layer at write-back and
    stay. `mutating=False` is a computation unit: its effects are overlays and are gone the moment it
    stops firing."""

    name: str
    premise: tuple
    effects: tuple
    mutating: bool = False


@dataclass
class TurnResult:
    """What a turn concluded, and how it ended. Every ending is a **positive fact** (`model.md` §8) —
    there is no "it just stopped"."""

    fired: tuple = ()
    effects: tuple = ()
    stable: bool = False
    oscillating: tuple = ()          # the effect-set states it cycled between
    out_of_fuel: bool = False
    applied: tuple = ()              # what write-back did to the asserted layer

    def ended(self) -> str:
        if self.oscillating:
            return "oscillating"
        if self.out_of_fuel:
            return "out_of_fuel"
        return "stable"


class Machine:
    """Asserted data, standing units, and a turn.

    The asserted layer changes **only** at write-back and only by a mutating rule (or from outside).
    Everything a computation unit does is an overlay, recomputed from scratch at the start of every
    turn — invariant 15, in the smallest form that can be tested."""

    def __init__(self, asserted: Graph = EMPTY, units: tuple = ()) -> None:
        self.asserted = asserted
        self.units = list(units)
        self.history: list = []

    def view(self, effects=()) -> Overlays:
        """The graph as it stands — asserted data plus the **overlays**.

        ⚠ A **mutating** rule's effects are *not* here, and that is `model.md` §9 rather than a
        convenience: *"the circuit never mutates the store — a deletion is a proposal on a wire, applied
        at write-back, so nothing inside a step reasons over a store that changes under it."* The two
        dispositions again, and this is where the difference bites: a computation unit's deletion **is**
        a read-time effect and is its whole nature; a mutating rule's deletion is an **act on the
        world**, and an act has not happened until write-back performs it.

        Removing this distinction makes the self-undermining mutating rule oscillate — which is how the
        spike found it."""
        mutating = {u.name for u in self.units if u.mutating}
        return Overlays(self.asserted, [(s, e) for s, e in effects if s not in mutating])

    def turn(self, fuel: int = 50) -> TurnResult:
        """Revive from the asserted layer, stabilize, then write back.

        ⚠ **Nothing is carried in from the previous turn.** `effects` starts empty every time, which is
        what makes a materialized fact *recomputed rather than maintained*. If a unit's premise is gone
        from the asserted layer, the unit does not fire — and nothing had to be retracted for that to be
        true (`revision-01` §3)."""
        effects: list = []
        seen: list = []
        result = TurnResult()

        for _ in range(fuel):
            key = tuple(sorted((s, repr(e)) for s, e in effects))
            if key in seen:
                # A state we have already been in: the fixpoint does not exist. Reported, not hidden.
                result.oscillating = tuple(seen[seen.index(key):])
                break
            seen.append(key)

            view = self.view(effects)
            fresh: list = []
            fired: list = []
            for u in self.units:
                if view.read(*u.premise) is not None:
                    fired.append(u.name)
                    fresh.extend((u.name, e) for e in u.effects)
            if fresh == effects:
                result.stable = True
                result.fired = tuple(fired)
                break
            effects = fresh
            result.fired = tuple(fired)
        else:
            result.out_of_fuel = True

        # ⚠ An oscillating turn reports **no effects**. Whichever phase the detector happened to stop in
        # is an artifact of where the scan began, and reporting it would make the turn's output depend
        # on that. There is no answer here; saying so is the honest report (`model.md` §8).
        result.effects = () if result.oscillating else tuple(effects)

        # WRITE-BACK. Only a mutating rule reaches the asserted layer, and only here (`model.md` §9:
        # after stabilization, never during). This is the one place the next turn's revive can differ.
        applied: list = []
        mutating = {u.name for u in self.units if u.mutating}
        if result.stable:                       # never after a truncated or oscillating turn
            for src, e in result.effects:
                if src not in mutating:
                    continue
                if isinstance(e, Retract):
                    self.asserted = self.asserted.without(e.target, e.attr)
                    applied.append((src, e))
        result.applied = tuple(applied)
        self.history.append(result)
        return result


__all__ = ["Unit", "Machine", "TurnResult"]

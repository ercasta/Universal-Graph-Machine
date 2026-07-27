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
instability instead of hiding it behind an arbitrary evaluation order. Failure to reach one is reported
as a positive fact, never as a silent truncation (`model.md` §8).

## Why a flipping gate is the detector

An earlier version found oscillation by comparing whole effect-set states for a repeat. That is a
**global** comparison, and `model.md` §2 refuses exactly that: *"no work-list running to quiescence, no
output-unchanged termination test."* It is replaced by a local one, on the following argument:

> Mint, edge and attribute only ever make more things readable, so within a run the readable set grows
> **monotonically** and a gate can only go absent → present. **A gate going present → absent is
> therefore proof that a non-monotone effect fired.**

The two non-monotone effects are `Retract` and `Identify` — the second because merging two nodes that
disagree produces a conflict, which reads as absent. Both are *mutations* of what is already there,
which is what makes a flipping input a signal rather than a heuristic.

**One flip is normal**: a deletion landed and a downstream unit correctly lost its premise. A *repeated*
flip means no fixpoint exists, so the threshold is on the count, and — like θ — it is a threshold you
can be wrong about.

⚠ **`revision-01` §4's energy is blind to this.** It grows when a value *returns to a unit it already
passed through*, an AS-path on a wire. A self-deleting unit has no wiring cycle at all: its path is
`[U]` and never revisits. The feedback runs through the readable state instead. Same shape — energy on a
repeated event, local, surging — but a second trigger, not an instance of the first.

Fuel remains the backstop, which is what `revision-01` §8's second finding established it as.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .graph import EMPTY, Graph, Node
from .overlay import BASE, Overlays, Retract, SetAttr

ANY = "<any>"                        # premise node position: match every node carrying the attribute
BOUND = "<bound>"                    # effect target: whatever the premise bound
ENGINE = "<engine>"                  # the only source the engine itself contributes under


SILENCED = "silenced"                # a unit carrying this produces nothing. See `bundled_silence_rule`


@dataclass(frozen=True)
class Unit:
    """A unit reduced to what this spike needs: a premise, effects, and a disposition.

    `premise` is `(node, attr)` — the unit fires while that slot is **readable**. `node` may be `ANY`,
    which binds every node carrying the attribute and instantiates the effects once per binding; that is
    the least a rule needs in order to be *about* something it was not written against.

    `node` is the unit's **own node in the graph** — homoiconicity (`revision-02` §§1, 5). A unit is
    plane-1 data, so a fact can be *about* it, which is what lets the surge correction be an ordinary
    rule instead of engine code.

    `mutating=True` is `revision-01` §2's regular rule: its effects are applied to the asserted layer at
    write-back and stay. `mutating=False` is a computation unit: its effects are overlays and are gone
    the moment it stops firing."""

    name: str
    premise: tuple
    effects: tuple
    mutating: bool = False
    node: Node = field(default_factory=lambda: Node("unit"))


SURGE_AT = 3                         # presence transitions on one gate before it is called a cycle


@dataclass(frozen=True)
class Surge:
    """A gate whose input kept switching on and off. A **positive fact** naming the unit and the slot —
    never an absence to be noticed, which is why energy grows rather than decays (`revision-01` §4).

    The engine's involvement ends here: it reports, and a bundled rule decides the correction (§7)."""

    unit: str
    gate: tuple                      # (node, attr)
    flips: int

    def __repr__(self) -> str:
        return f"<surge {self.unit} {self.gate[1]} ×{self.flips}>"


@dataclass
class TurnResult:
    """What a turn concluded, and how it ended. Every ending is a **positive fact** (`model.md` §8) —
    there is no "it just stopped"."""

    fired: tuple = ()
    effects: tuple = ()
    stable: bool = False
    surges: tuple = ()               # gates that flipped past the threshold
    out_of_fuel: bool = False
    applied: tuple = ()              # what write-back did to the asserted layer

    def ended(self) -> str:
        """⚠ A surge is an **event, not an ending**. A turn whose surge was corrected by a rule ends
        `stable`; one whose surge nobody handled runs until the budget and ends `out_of_fuel`. Making
        the surge itself an ending would be the engine deciding to stop, which is the judgement §7 says
        it must not make."""
        return "out_of_fuel" if self.out_of_fuel else "stable"


class Machine:
    """Asserted data, standing units, and a turn.

    The asserted layer changes **only** at write-back and only by a mutating rule (or from outside).
    Everything a computation unit does is an overlay, recomputed from scratch at the start of every
    turn — invariant 15, in the smallest form that can be tested."""

    def __init__(self, asserted: Graph = EMPTY, units: tuple = ()) -> None:
        self.units = list(units)
        # **Units are plane-1 data** (`revision-02` §§1, 5). Each one's node goes into the same graph as
        # everything else — no machinery partition — which is what makes a fact *about* a unit
        # expressible, and therefore what makes the surge correction an ordinary rule.
        #
        # They are invisible to ordinary rules for the ordinary reason (invariant 19): nothing matches
        # implicitly, so a premise wanting `age` does not find a unit. Nothing is hidden; it simply does
        # not match.
        for u in self.units:
            asserted = asserted.with_node(u.node, name=u.name)
        self.asserted = asserted
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

    def _bindings(self, view, u: "Unit") -> tuple:
        """Which nodes this unit's premise is about. A concrete node binds itself; `ANY` binds every
        node carrying the attribute, which is the least a rule needs to be *about* something it was not
        written against."""
        node, attr = u.premise
        if node is not ANY:
            return (node,)
        return tuple(n for n in view.nodes() if view.read(n, attr) is not None)

    @staticmethod
    def _instantiate(effect, bound: Node):
        """Substitute the premise's binding into an effect written with `BOUND`."""
        if isinstance(effect, SetAttr) and effect.target is BOUND:
            return SetAttr(bound, effect.attr, effect.value)
        if isinstance(effect, Retract) and effect.target is BOUND:
            return Retract(bound, effect.attr, effect.source)
        return effect

    def turn(self, fuel: int = 50) -> TurnResult:
        """Revive from the asserted layer, stabilize, then write back.

        ⚠ **Nothing is carried in from the previous turn.** `effects` starts empty every time, which is
        what makes a materialized fact *recomputed rather than maintained*. If a unit's premise is gone
        from the asserted layer, the unit does not fire — and nothing had to be retracted for that to be
        true (`revision-01` §3)."""
        effects: list = []
        result = TurnResult()
        was: dict = {}               # (unit, bound node) -> last observed presence
        flips: dict = {}             # (unit, bound node) -> presence transitions so far
        surges: list = []
        reported: set = set()
        # ⚠ What the engine reports persists for the rest of the turn. Effects are rebuilt from scratch
        # each round, so without this the `surged` fact evaporates on the very next round and no rule
        # can ever match it — found by the bundled rule failing to fire. A report of something that
        # *happened* is not a conclusion that has to keep being re-derived.
        reports: list = []

        for _ in range(fuel):
            view = self.view(effects)
            fresh: list = list(reports)
            fired: list = []
            for u in self.units:
                for bound in self._bindings(view, u):
                    key = (u.name, bound)
                    now = view.read(bound, u.premise[1]) is not None
                    if key in was and was[key] != now:
                        flips[key] = flips.get(key, 0) + 1
                        if flips[key] >= SURGE_AT and key not in reported:
                            surges.append(Surge(u.name, (bound, u.premise[1]), flips[key]))
                            reported.add(key)
                            # The engine's ENTIRE involvement: say so, as a fact on the unit's own
                            # node, where a rule can match it (`revision-02` §7). It does not stop, it
                            # does not unwire, and it does not silence. If nobody handles it, fuel ends
                            # the turn — which is what makes the bundled rule load-bearing.
                            reports.append((ENGINE, SetAttr(u.node, "surged", u.premise[1])))
                            fresh.append(reports[-1])
                    was[key] = now
                    if now and view.read(u.node, SILENCED) is None:
                        fired.append(u.name)
                        fresh.extend((u.name, self._instantiate(e, bound)) for e in u.effects)
            if fresh == effects:
                result.stable = True
                result.fired = tuple(fired)
                break
            effects = fresh
            result.fired = tuple(fired)
        else:
            result.out_of_fuel = True

        result.surges = tuple(surges)
        # ⚠ A turn that never settled reports **no effects**. Whichever round the budget happened to cut
        # it off in is an artifact, and reporting it would make the turn's output depend on that. There
        # is no answer here; saying so is the honest report (`model.md` §8). A turn that surged and was
        # then *corrected* does settle, and reports normally.
        result.effects = () if result.out_of_fuel else tuple(effects)

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


def bundled_silence_rule() -> Unit:
    """**The surge correction, shipped as an ordinary rule.**

    *"Anything that surged: stop its output."* It is a `Unit` like any other — no privileged status, no
    engine hook — and it is written **about units**, which it can only be because a unit is plane-1 data
    with a node of its own (`revision-02` §§1, 5). This is the first thing in the design that needs
    homoiconicity for something other than tidiness.

    Shipping it as a rule rather than as engine policy is [[composability-principle]]: a governance
    mechanism hardcoded in Python is an unreachable island that later has to be dug out. Here the cost
    of doing it right on day one is one function.

    Remove it and the surge stands unhandled — the engine reports and keeps going until fuel, because
    stopping would itself be a judgement (§7). That is what makes this rule load-bearing rather than
    decorative, and it is what `test_without_the_bundled_rule_nothing_fixes_the_surge` pins."""
    return Unit("bundled:silence", (ANY, "surged"), (SetAttr(BOUND, SILENCED, True),))


__all__ = ["Unit", "Machine", "TurnResult", "Surge", "bundled_silence_rule",
           "ANY", "BOUND", "ENGINE", "SILENCED", "SURGE_AT"]

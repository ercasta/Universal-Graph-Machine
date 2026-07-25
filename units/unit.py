"""THE UNIT — the substrate (`docs/design/substrate_inversion.md` §2, §2b, §5, §7).

A unit holds a whole subgraph as its state, fires when its input matches its LHS, and emits a new subgraph.
It is not a node in a graph that something else walks; it is the thing that computes, and the graph is what
flows between units.

**THERE IS NO FACT/RULE DISTINCTION — ONLY IN-DEGREE** (§2). An axiom is a unit with no input and a fixed
output; a constant is a nullary function, a given is a nullary computation. The spike found this by force
rather than design: "a source" and "a hypothesis branch" turned out to be the same construct at different
in-degree, so there is exactly one class here and `kind` merely reports what the wiring already says.

**THE STORE IS BOUNDED, NOT ABOLISHED** (§2b — a correction the original design did not state). A unit
joins over the UNION of its inputs, so it HAS a store: precisely what its in-edges deliver. "No blackboard"
means no UNBOUNDED SHARED store. **A unit's IN-DEGREE is what bounds its epistemic reach** — it is the
analogue of a scope, and every wire added is a deliberate widening of what this unit may conclude.

**CACHING IS NOT AN OPTIMIZATION** (§7). The cached output is what makes three things work at once:
refire without recomputing upstream; change propagation (push only when the output differs); and
termination, since "output unchanged" IS the stopping condition. That last one is the same idempotence
result the queue-topology spike reached from an unrelated direction — the third independent derivation.
Because of it, revision here is re-running forward, never retraction: `retraction.py`, the cascade,
copy-on-delete and the broken-assumption stamps are all artifacts of mutable shared state and have no work
to do on this substrate.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .match import Absent, Triple, check_safety, ground, solve
from .value import EMPTY, Fact, Subgraph


@dataclass
class Unit:
    """One computation unit.

    * `delta` — facts this unit contributes UNCONDITIONALLY. At in-degree 0 this is an axiom; at in-degree
      1 it is a hypothesis branch adding its claim to what it carries through. Same construct.
    * `lhs` / `rhs` — the rule, if any. Empty means the unit only carries and contributes.
    * `drop` — facts this unit REMOVES from what it carries (§5). Required, not incidental: *"under H,
      not P"* against a base that holds P cannot be said without it.
    """
    name: str
    lhs: tuple = ()
    rhs: tuple = ()
    delta: Subgraph = EMPTY
    drop: frozenset = frozenset()
    inputs: dict = field(default_factory=dict)      # producer name -> that producer's last output
    output: Subgraph = EMPTY
    last_derived: frozenset = frozenset()           # what THIS unit concluded on its last run
    runs: int = 0                                   # times recomputed
    fired: int = 0                                  # times it DERIVED something (never equal by luck)

    def __post_init__(self) -> None:
        if isinstance(self.rhs, Triple):
            self.rhs = (self.rhs,)
        check_safety(self.lhs, self.rhs)            # loud at construction, not mid-run

    # -- the taxonomy is by degree, so it is read off the wiring ------------

    @property
    def in_degree(self) -> int:
        return len(self.inputs)

    @property
    def kind(self) -> str:
        """`given` | `rule` | `carrier` — reported, never declared (§2)."""
        if self.in_degree == 0:
            return "given"
        return "rule" if self.rhs else "carrier"

    # -- the computation ----------------------------------------------------

    def view(self) -> Subgraph:
        """Everything this unit can see: its inputs, plus its own delta, minus what it drops. THE BOUND on
        its epistemic reach (§2b) — there is no other address it could read from."""
        v = EMPTY
        for val in self.inputs.values():
            v = v | val
        v = v.union(self.delta)
        return v.without(self.drop) if self.drop else v

    def run(self) -> bool:
        """Recompute from the current inputs. Output = the view carried through, PLUS what was derived
        (§5 accretion — and accretion is safe here only because the topology forks: what accumulates is
        one value PER PATH, which is what a context IS).

        Returns whether the output CHANGED, which is the whole of the termination story."""
        self.runs += 1
        view = self.view()
        derived = set()
        if self.rhs:
            for b in solve(self.lhs, view):
                for head in self.rhs:
                    derived.add(ground(head, b))
        fresh = frozenset(f for f in derived if f not in view)
        new = view.with_facts(fresh) if fresh else view
        if fresh:
            self.fired += 1
        self.last_derived = fresh
        changed = new != self.output
        self.output = new
        return changed

    def derived(self, pred: str | None = None) -> Subgraph:
        """What THIS unit concluded, RECORDED at run time rather than recovered by subtracting the view.

        The difference is not stylistic. Subtraction silently reports nothing whenever a unit's own
        conclusion can reach its own input — which is what an accidental cycle in the wiring produces, and
        which is exactly how this was first found. A derivation is a fact about a RUN, so it is recorded
        when the run happens."""
        return Subgraph(f for f in self.last_derived if pred is None or f.p == pred)

    def __repr__(self) -> str:
        return f"<{self.kind} {self.name} in={self.in_degree} out={len(self.output)}>"


def given(name: str, facts) -> Unit:
    """An axiom — a unit with no input and a fixed output (§2). `given("base", [f1, f2])`."""
    return Unit(name, delta=facts if isinstance(facts, Subgraph) else Subgraph(facts))


def rule(name: str, lhs: tuple, rhs) -> Unit:
    """A rule unit. Its in-edges are supplied later, by the assembler."""
    return Unit(name, lhs=tuple(lhs), rhs=rhs)


def branch(name: str, add=(), remove=()) -> Unit:
    """A hypothesis branch: carries its input through, adds `add`, removes `remove`. Identical machinery
    to `given` — the only difference is that something will be wired INTO it."""
    return Unit(name, delta=Subgraph(add), drop=frozenset(remove))


__all__ = ["Unit", "given", "rule", "branch", "Triple", "Absent", "Fact", "Subgraph"]

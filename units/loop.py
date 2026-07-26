"""THE OUTER LOOP — `docs/units/model.md` §7 and §8.

A turn is a sequence of **steps**, each of which is:

```
1. RETRIEVE   given the current data (including the goal), which rules come to mind?   [System 1]
2. ASSEMBLE   mint units for them, wire them by the ordinary policy
3. RUN        the circuit runs to completion, bounded by fuel                          [System 2]
4. WRITE BACK conclusions and derivations become data
```

…and the next step retrieves against the data step 3 produced. **That is the mechanism of one thought
leading to another**: what this step concluded is what the next step notices.

**Nothing happens unbidden** (§1). Absent a goal, nothing here runs.

**The driver does no semantics** (§7). Read this module looking for a judgement — a decision about
relevance, meaning, scope, or truth — and there should not be one. It retrieves (by delegating), wires
(by delegating), runs, and writes. Every judgement lives inside a unit. Erode that and the central
machine is back.

**Done is a positive fact, never an absence** (§8). Four outcomes, one per goal per step, and the fact
that they are *facts in the graph* is the point — a later step, or a person, can read them.

⚠ **`out_of_fuel` must never collapse into a negative answer.** §8 flags this as one step away from the
conflation the section exists to prevent: the surface must say *"I couldn't work it out"*, never *"no."*
Nothing here converts an outcome into a truth value, and nothing downstream may either.

**Not built:** suspension and resume (§9) — `awaiting` is recorded but nothing services it; derivations
(only conclusions are written back); and deletions.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .assemble import assemble, decode_pattern, kind_of, roles_of
from .graph import Graph, Node, active_scopes, visible_at
from .match import solve
from .recall import resemblance
from .unit import ScopePointer

# §8's four outcomes, plus the one the outer budget needs.
SATISFIED = "satisfied"
STARVED = "starved"
OUT_OF_FUEL = "out_of_fuel"
AWAITING = "awaiting"
STOPPED = "stopped"
"""§8 requires the outer budget's exhaustion to be *a different fact* from fuel's — *"I stopped thinking
about this"* versus *"this computation didn't converge"* — but does not name it. This is that name."""

TERMINAL = (SATISFIED, STOPPED)


# -- goals, read off the graph ------------------------------------------------------------------

def goals(world: Graph) -> list:
    """Every goal in the world — identified by **what it has, not what it is called**.

    ⚠ This read was `name == "goal"` and that was wrong, in a way worth recording because it is the
    standing hazard of this design rather than a slip. §4 gives `name` no privilege, so occurrence names
    and *role* names live in one namespace: writing an outcome mints a role node named `"goal"`, which
    then read back as a goal. Each step minted another, none of them satisfiable, so the turn never
    settled and ran to the outer budget every time.

    The fix is the one `model.md` §11 prescribes — **guards yes, kinds no**. A goal is not a *kind* of
    node to be recognised; it is a node that asserts a satisfaction condition. Ask for the condition."""
    return [n for n in world.nodes if roles_of(world, n, "satisfied-by")]


def satisfaction(world: Graph, goal: Node):
    """A goal's satisfaction condition, decoded as an ordinary pattern. **Checking a goal is an ordinary
    rule match** (§8) — there is no separate goal-checking mechanism."""
    conds = roles_of(world, goal, "satisfied-by")
    return tuple(decode_pattern(world, c) for c in conds)


def outcomes_of(world: Graph, goal: Node) -> list:
    """Every outcome recorded for `goal`, oldest first."""
    got = []
    for n in world.nodes:
        if kind_of(world, n) != "outcome":
            continue
        if goal in roles_of(world, n, "goal"):
            got.append((world.attr(n, "step"), world.attr(n, "kind")))
    got.sort(key=lambda p: p[0])
    return [kind for _, kind in got]


def settled(world: Graph, goal: Node) -> bool:
    return any(k in TERMINAL for k in outcomes_of(world, goal))


def _record(world: Graph, goal: Node, kind: str, step: int) -> Graph:
    """Write one outcome fact. Encoded as an ordinary occurrence with role nodes (§3) — an outcome is
    not a special kind of thing."""
    from .graph import role_edge
    occ = Node("outcome")
    world = world.with_node(occ, name="outcome", kind=kind, step=step)
    world = role_edge(world, occ, "goal", goal)
    return world


def _declares_scope(library: Graph, label: str) -> bool:
    for n in library.nodes:
        if kind_of(library, n) == "statement" and library.attr(n, "label") == label:
            return library.attr(n, "scope") is not None
    return False


# -- write-back: applying decisions ---------------------------------------------------------------

def _declared_distinct(world: Graph, a: Node, b: Node) -> bool:
    for occ in world.nodes:
        if kind_of(world, occ) != "distinct-from":
            continue
        ts = roles_of(world, occ, "of")
        if len(ts) == 2 and {ts[0], ts[1]} == {a, b}:
            return True
    return False


def apply_merges(world: Graph) -> Graph:
    """Apply every `same-as` a rule concluded, and honour every `distinct-from` that forbids one.

    **The split is the whole point.** A rule *decides* two nodes are the same (`unit.Same`); write-back
    *applies* it. `cnl.md` §1's create-never-merge governs the boundary — nothing may identify two
    things without a judgement — and this is that judgement being carried out, not made.

    ⚠ **Why `distinct-from` is consulted here, and not only in the rule that produced the merge.** A
    guard in the rule sees the world as it was at the *start* of the step (§9: a deletion — and equally
    a merge — is invisible within its own step). So a step can conclude `a = c` and `b = c` while
    holding `a ≠ b`, and applying both would fuse two nodes that discourse explicitly separated. That
    is not a merge the system decided; it is one nobody decided.

    Checking here catches it because merges are applied **one at a time** and the graph is rewritten in
    between: once `c` has become `a`, the second decision reads as `b = a` and the declared distinctness
    refuses it. Which of the two survives depends on order — the declared cost — but the *count* does
    not, and no explicitly-separated pair is ever fused.

    `same-as` and `distinct-from` are the two **identity** primitives, and write-back is where identity
    decisions land. That keeps this from being domain vocabulary leaking into the boundary: it is the
    same category of thing as a concluded deletion, which §9 already applies here.

    Idempotent: once `a` and `b` are one node the occurrence points twice at the same node and
    `Graph.merge` is a no-op."""
    for occ in [n for n in world.nodes if kind_of(world, n) == "same-as"]:
        targets = roles_of(world, occ, "of")
        if len(targets) != 2 or targets[0] is targets[1]:
            continue
        if _declared_distinct(world, targets[0], targets[1]):
            continue
        world = world.merge(targets[0], targets[1])
    return world


# -- one step -----------------------------------------------------------------------------------

@dataclass
class StepResult:
    index: int
    retrieved: list
    world: Graph
    outcomes: dict = field(default_factory=dict)     # goal Node -> kind
    misses: list = field(default_factory=list)
    out_of_fuel: bool = False


def step(world: Graph, library: Graph, index: int = 0, *, pinned: tuple = (),
         fuel_limit: int = 500, cooldown=None) -> StepResult:
    """One step. Retrieve, assemble, run, write back."""
    pending = [g for g in goals(world) if not settled(world, g)]

    # 1. RETRIEVE — System 1. Allowed to be incomplete, allowed to be wrong.
    labels = resemblance(world, library, pinned=pinned)

    # 2. ASSEMBLE — only what came to mind, and **once per context it could apply in**.
    result = StepResult(index=index, retrieved=list(labels), world=world)
    if labels:
        produced = world
        units_seen: list = []
        # Resolved against the FULL world, never a projection — see `assemble`'s `known_scopes`.
        known = {kind_of(world, n): n for n in active_scopes(world)}

        # A general rule applies wherever its premises hold — including inside an assumption. So it is
        # instantiated once per active scope, each instance fed only what is visible there. This is how
        # *"if x is a bird, x can fly"* reaches a bird that exists only under *"assuming x has wings"*,
        # and how its conclusion lands under that same assumption rather than in the world.
        #
        # A statement that DECLARES a scope is not re-instantiated: it establishes its own context, and
        # running it inside every other one would nest assumptions nobody made.
        for ctx in [None] + active_scopes(world):
            here = tuple(l for l in labels
                         if ctx is None or not _declares_scope(library, l))
            if not here:
                continue
            view = visible_at(world, ctx)
            asm = assemble(library, only=here, cooldown=cooldown, known_scopes=known,
                           under=ScopePointer(kind_of(world, ctx), node=ctx) if ctx else None)
            asm.circuit.fuel.limit = fuel_limit

            # 3. RUN — §7's grain: a step fires whatever sealed statements came to mind.
            for label in here:
                stmt = asm.by_label.get(label)
                if stmt is None:
                    continue
                run = asm.circuit.feed(stmt, view)
                result.out_of_fuel |= run.out_of_fuel
                produced = produced.union(stmt._last.output or view)
            units_seen.extend(asm.circuit.units)

        # Misses are collected ONCE, after every recalled statement has been fed. Collecting them
        # per-feed reported every not-yet-fed unit as a starved gate, which made `awaiting` universal
        # and hid `starved` entirely — the outcomes are only meaningful at the step's boundary.
        result.misses = [m for u in units_seen for m in u.misses()]

        # 4. WRITE BACK — including applying the identity decisions rules reached this step.
        result.world = apply_merges(produced)

    # Outcomes: one positive fact per goal worked on (§12 invariant 5), never an absence.
    for g in pending:
        result.outcomes[g] = _classify(result, g)
        result.world = _record(result.world, g, result.outcomes[g], index)

    return result


def _classify(result: StepResult, goal: Node) -> str:
    """The one place an outcome is decided. Deliberately ordered: satisfaction first, because a step
    that both concluded the answer and left a gate unfed has *succeeded*."""
    if solve(result.world, satisfaction(result.world, goal)):
        return SATISFIED
    if result.out_of_fuel:
        return OUT_OF_FUEL
    if result.misses:
        return AWAITING
    return STARVED           # nothing came to mind, or nothing matched — NOT "underivable" (§7)


# -- a turn -------------------------------------------------------------------------------------

@dataclass
class TurnResult:
    steps: list
    world: Graph

    @property
    def outcomes(self) -> dict:
        """Each goal's last outcome."""
        return {g: outcomes_of(self.world, g)[-1]
                for g in goals(self.world) if outcomes_of(self.world, g)}


def turn(world: Graph, library: Graph, *, pinned: tuple = (), max_steps: int = 12,
         fuel_limit: int = 500, cooldown=None) -> TurnResult:
    """Step until every goal is settled, or the **outer budget** runs out (§8).

    The outer budget is not a nicety: System 1 will keep offering rules and steps will keep happening,
    and there is no quiescence to stop them (§5). Its exhaustion is recorded as `STOPPED`, which is a
    different fact from `OUT_OF_FUEL`."""
    steps, current = [], world
    for i in range(max_steps):
        pending = [g for g in goals(current) if not settled(current, g)]
        if not pending:
            break
        result = step(current, library, i, pinned=pinned, fuel_limit=fuel_limit,
                      cooldown=cooldown)
        steps.append(result)
        current = result.world
    else:
        for g in goals(current):
            if not settled(current, g):
                current = _record(current, g, STOPPED, max_steps)

    return TurnResult(steps, current)


__all__ = ["step", "turn", "StepResult", "TurnResult", "goals", "satisfaction", "outcomes_of",
           "settled", "SATISFIED", "STARVED", "OUT_OF_FUEL", "AWAITING", "STOPPED", "TERMINAL"]

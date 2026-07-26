"""THE NETWORK — index, assembler, propagation (`docs/design/substrate_inversion.md` §3, §3b, §7).

Two responsibilities, and they are deliberately separate because only one of them is allowed to be global:

**THE INDEX** — over unit LHS and RHS PREDICATES. It indexes COMPUTATION, never data; the subgraph values
still travel only along wires. §1's falsifiable test forbids global enumeration over DATA, and this is the
one permitted exception. **If a second global structure appears here, something has leaked back into being
a store.**

**THE ASSEMBLER** — spawn and wire. §3b is the correction that makes it work at all: the index ALONE
collapses the chains. Wire every producer of a matching predicate into one instance and that instance sees
every hypothesis at once and derives all of them, taking §4's emergence claim with it. What separates the
chains is a purely local test over the topology that already exists, and it names no scope:

    A producer joins an existing instance only if it is COMPARABLE — ancestor, descendant, or identical —
    with EVERY producer already wired into that instance. Two sibling branches are incomparable, so the
    second SPAWNS A NEW INSTANCE of the rule instead of adding a wire.

The quantifier is load-bearing: `base` is an ancestor of BOTH branches, so an any-test lets the second
branch join the instance already holding the first, and the chains collapse regardless.

And the policy is only half a mechanism. **Accretion is the other half** (§5): a freshly spawned sibling
instance is wired to one branch only, and sees base solely because that branch CARRIES IT THROUGH. Without
accretion a spawned instance is starved and derives nothing — which is exactly how the spike failed on its
first run. Neither feature works alone.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .fuel import Budget
from .match import Triple
from .unit import Unit
from .value import EMPTY, Node


@dataclass
class Net:
    units: dict = field(default_factory=dict)               # name -> Unit
    producers: dict = field(default_factory=dict)           # consumer name -> set of producer names
    consumers: dict = field(default_factory=dict)           # producer name -> set of consumer names
    lhs_index: dict = field(default_factory=dict)           # predicate -> set of unit names
    rhs_index: dict = field(default_factory=dict)           # predicate -> set of unit names
    library: dict = field(default_factory=dict)             # template name -> (lhs, rhs)
    instances: dict = field(default_factory=dict)           # template name -> [instance names]
    consumed: dict = field(default_factory=dict)            # template name -> {value already fed to it}

    # -- structure ----------------------------------------------------------

    def spawn(self, u: Unit) -> Unit:
        if u.name in self.units:
            raise ValueError(f"duplicate unit name {u.name!r}")
        self.units[u.name] = u
        self.producers.setdefault(u.name, set())
        self.consumers.setdefault(u.name, set())
        # A VARIABLE role contributes no index key: `?s ?p ?o` is a WILDCARD, and §22.5 measured what
        # that costs — it wakes on everything. Recorded rather than papered over; the index cannot
        # discriminate for a rule that declines to say what it reads.
        for a in u.lhs:
            if isinstance(a, Triple) and isinstance(a.p, Node):
                self.lhs_index.setdefault(a.p, set()).add(u.name)
        for h in u.rhs:
            if isinstance(h.p, Node):
                self.rhs_index.setdefault(h.p, set()).add(u.name)
        for p in u.adds.predicates():
            self.rhs_index.setdefault(p, set()).add(u.name)
        return u

    def wire(self, producer, consumer) -> None:
        p = producer.name if isinstance(producer, Unit) else producer
        c = consumer.name if isinstance(consumer, Unit) else consumer
        if p == c:
            raise ValueError(f"refusing to wire {p!r} to itself")
        self.producers.setdefault(c, set()).add(p)
        self.consumers.setdefault(p, set()).add(c)

    def upstream(self, name) -> set:
        """Transitive producers, walked over the topology — the only structure there is. Note what this
        does NOT consult: no scope, no context, no vantage. Reachability is the whole mechanism."""
        n = name.name if isinstance(name, Unit) else name
        seen, frontier = set(), [n]
        while frontier:
            for p in self.producers.get(frontier.pop(), ()):
                if p not in seen:
                    seen.add(p)
                    frontier.append(p)
        return seen

    def comparable(self, a: str, b: str) -> bool:
        """One lineage? — `a` is `b`, or an ancestor of it, or a descendant."""
        return a == b or a in self.upstream(b) or b in self.upstream(a)

    def restores_a_drop(self, consumer: str, extra: str | None = None) -> tuple | None:
        """Would this consumer's producers RESTORE a fact one of them deliberately removed? (§17.A)

        §5 as amended: a unit is a REWRITE, so its output may simply omit what its input held — *"under
        H, not P"* (§21.1). §16.5 recommends a merge wired to both a rule and
        its branch, to re-supply context. Put those together and the merge hands back the very fact the
        branch dropped: **the ancestor is a bypass of the descendant's drop.** Found by spiking the
        recommendation rather than the design (`bench/spike_failure_points.py` case A).

        It needs no semantics to detect: an ancestor producer supplying facts its own descendant does not.
        Returns the offending `(ancestor, descendant)` pair, or None."""
        prods = set(self.producers.get(consumer, ()))
        if extra:
            prods.add(extra)
        for a in prods:
            for b in prods:
                if a != b and a in self.upstream(b):
                    if self.units[a].output.facts - self.units[b].output.facts:
                        return (a, b)
        return None

    def wellformed(self) -> list:
        """Problems a HAND-WIRED net can have that the assembler would never build. Returns a list of
        `(kind, detail)`; empty means the guarantees below hold.

        **`cycle` — this is where the FIXPOINT guarantee comes from** (§17.B). Termination rests on
        "output unchanged", which is a fixpoint argument only if the network cannot oscillate. The
        assembler refuses back edges, so an ASSEMBLED net is a DAG and a fixpoint is guaranteed. A
        hand-wired cycle plus NAF does not oscillate here — measured — it CONVERGES to a different answer
        depending on work-list order, which is worse, because it is silent. §6's warning that scheduling
        policy must not leak into semantics, realized.

        **NOTE THE JUSTIFICATION MOVED.** The cycle guard was built to contain accretion's runaway wiring
        (§15.1a). §16 removed that need — and the guard must stay anyway, because it is now the only thing
        standing between NAF and an order-dependent answer. Deleting it as dead weight would be a mistake.
        """
        out = []
        for p, cs in self.consumers.items():
            for c in cs:
                if c in self.upstream(p):
                    out.append(("cycle", f"{p} -> {c}, but {c} is already upstream of {p}"))
        for name in self.units:
            hit = self.restores_a_drop(name)
            if hit:
                out.append(("restores_a_drop", f"{name}: {hit[0]} is an ancestor of {hit[1]} and "
                                               f"re-supplies what it dropped"))
        out.extend(self.trace_leaks())
        return out

    def trace_leaks(self) -> list:
        """**§16.6's constraint, made mechanical rather than documented** (§20).

        The trace is carried on its own wire and must never accrete into the object value. If it does,
        §6a's exact NAF starts seeing provenance facts: `Absent` stops asking *"is P absent from the
        world I was handed?"* and starts asking *"was P mentioned in the derivation?"* — two different
        questions with the same syntax, which is the worst kind of leak.

        Same spirit as the no-import rule: this is exactly the sort of thing that is right on paper and
        wrong in the build, so it is asserted rather than intended."""
        from .trace import is_trace
        return [("trace_leak", f"{u.name}: object output carries {f!r}")
                for u in self.units.values() for f in u.output if is_trace(f)]

    # -- assembly -----------------------------------------------------------

    def declare(self, name: str, lhs, rhs) -> None:
        """Add a rule to the LIBRARY — NOT instantiated. The KB is a library of units, and a template
        becomes real only when a producer arrives that could feed it (§3, lazy spawn)."""
        rhs = (rhs,) if isinstance(rhs, Triple) else tuple(rhs)
        self.library[name] = (tuple(lhs), rhs)
        self.instances.setdefault(name, [])

    def assemble(self, budget: Budget | None = None) -> int:
        """One pass of lazy assembly. For every library template and every unit whose CURRENT OUTPUT could
        feed it, apply the §3b policy. Returns the number of wires added (spawns included).

        Driven by what has actually been produced, not by what could be — which is why this must be
        interleaved with `propagate` (see `run`) and why rules nobody needed are never materialized
        ([[agent-not-theorem-prover]], structurally rather than by policy).

        THREE GUARDS, and two of them were found by running this rather than by designing it:

        * **NO CYCLES.** Accretion (§5) means every downstream unit carries its ancestors' facts through,
          so it looks like a producer of every upstream predicate. Left alone, the assembler therefore
          wires a consumer back into its own producer and closes a loop — not as a corner case but as the
          DEFAULT. A wire is refused whenever the target is already upstream of the producer.
        * **UNROLLING IS NOT A CYCLE, and the distinction is the whole of §0's depth claim.** A unit may
          feed a NEW instance of a template it is itself an instance of — that is how recursion acquires
          depth here, since a rule unit's output never re-enters its own view and so it cannot iterate on
          its own. Forbid this and transitive closure becomes inexpressible.
        * **PROJECTION DEDUP terminates the unrolling.** A producer is fed to a template only if its
          output, RESTRICTED TO THE PREDICATES THAT TEMPLATE READS, is one no instance has consumed. Once
          a chain stops growing, the projection stops changing and assembly stops — the same idempotence
          condition that terminates propagation, applied one level up. Projecting (rather than comparing
          whole values) is what keeps a downstream unit from re-spawning every upstream rule it happens to
          be carrying facts for.
        """
        budget = budget or Budget()
        added = 0
        for tname, (lhs, rhs) in self.library.items():
            need = {a.p for a in lhs if isinstance(a, Triple) and isinstance(a.p, Node)}
            seen = self.consumed.setdefault(tname, set())
            # FRONTIER FIRST, and it is a correctness requirement rather than a preference (§16). Two
            # producers in one lineage can project identically while the deeper one carries strictly more
            # context — a hypothesis marker, a time index, an attribution. Taking the first one found
            # wires the SHALLOWEST, which silently drops that context and is precisely a BYPASS.
            cands = sorted(self.units.values(), key=lambda u: len(self.upstream(u.name)), reverse=True)
            for prod in cands:
                if not (prod.output.predicates() & need):
                    continue                                # nothing it emits could match this LHS
                projection = frozenset(f for f in prod.output if f.p in need)
                if any(projection == pj for pj, _ in seen):
                    continue                                # nothing NEW for this template to read
                if any(prod.name in self.producers.get(i, ()) for i in self.instances[tname]):
                    continue                                # already wired somewhere — idempotence guard
                if not budget.spend(1, f"assemble {tname}<-{prod.name}"):
                    return added
                up = self.upstream(prod.name)
                target = None
                for iname in self.instances[tname]:
                    if iname == prod.name or iname in up:
                        continue                            # self-wire, or would close a CYCLE
                    if all(self.comparable(prod.name, q) for q in self.producers.get(iname, ())):
                        target = iname                      # ONE LINEAGE -> add a wire
                        break
                if target is None:                          # INDEPENDENT BRANCH, or DEPTH -> new instance
                    n = len(self.instances[tname]) + 1
                    target = f"{tname}#{n}"
                    self.spawn(Unit(target, lhs=lhs, rhs=rhs))
                    self.instances[tname].append(target)
                    budget.spawns += 1
                self.wire(prod.name, target)
                seen.add((projection, prod.name))
                added += self._complete_lhs(target, need) + 1
        return added

    def _complete_lhs(self, iname: str, need: set) -> int:
        """Wire whatever else this instance needs to satisfy its LHS — the JOIN, made automatic.

        **Why this exists at all is the cost of subset output** (§16). A rule now emits only its
        conclusion, so an instance wired to one producer sees only that producer's predicates. A
        two-premise rule like *`?x reaches ?y` and `?y next ?z`* gets `reaches` from the chain and must get
        `next` from somewhere else; under accretion the upstream unit carried it along and the assembler
        never had to notice. Here it does, and the noticing is what a MERGE unit is for.

        **AND THIS IS A JOIN, NOT A BYPASS — the distinction is load-bearing** (user, 2026-07-26). A chain
        represents scope by DEACTIVATION: a unit that matches nothing emits nothing and starves everything
        downstream. Routing around such a unit defeats that guard and is a semantic change, never a
        shortcut. The line between the two is checkable and is exactly the test applied below:

            a wire supplying a predicate NO UNIT IN THE CHAIN PRODUCES is a join;
            a wire supplying a predicate A CHAIN UNIT GATES is a bypass, and is refused.

        So `base -> T2#2` is legal (nothing in the chain produces `next`), while re-wiring `base` for a
        predicate the chain's own rule emits is not — that would route around the gate.
        """
        inst = self.units[iname]
        added = 0
        for _ in range(len(need)):                          # at most one pass per needed predicate
            prods = self.producers.get(iname, set())
            supplied: set = set()
            for p in prods:
                supplied |= self.units[p].output.predicates()
            missing = need - supplied
            if not missing:
                break
            gated = {h.p for q in self.upstream(iname) for h in self.units[q].rhs
                     if isinstance(h.p, Node)}
            cands = [u for u in self.units.values()
                     if u.name != iname
                     and (u.output.predicates() & missing)
                     and u.name not in prods
                     and iname not in self.upstream(u.name)          # would close a cycle
                     and not (u.output.predicates() & missing & gated)  # BYPASS -> refuse
                     and all(self.comparable(u.name, q) for q in prods)]
            if not cands:
                break
            cands.sort(key=lambda u: len(self.upstream(u.name)), reverse=True)  # frontier first
            self.wire(cands[0].name, iname)
            inst.inputs[cands[0].name] = cands[0].output
            added += 1
        return added

    # -- propagation --------------------------------------------------------

    def propagate(self, budget: Budget | None = None) -> int:
        """Run to quiescence over a WORK-LIST: refresh a unit's inputs, recompute, and re-enqueue its
        consumers only if its output CHANGED. That last clause is the termination argument and it is not a
        separate mechanism — it is the same idempotence result the queue-topology spike found (§7).

        A cycle therefore quiesces rather than spinning, PROVIDED the units are monotone in the sense that
        matters: a re-derivation that produces the same facts changes nothing and wakes nobody."""
        budget = budget or Budget()
        pending = list(self.units)
        seen = set(pending)
        rounds = 0
        while pending:
            if not budget.spend(1, "propagate"):
                break
            name = pending.pop(0)
            seen.discard(name)
            u = self.units[name]
            for p in self.producers.get(name, ()):
                u.inputs[p] = self.units[p].output
                u.trace_inputs[p] = self.units[p].trace_output   # the SECOND wire, same topology (§20)
            rounds += 1
            if u.run():
                for c in self.consumers.get(name, ()):
                    if c not in seen:
                        seen.add(c)
                        pending.append(c)
        budget.rounds += rounds
        return rounds

    def run(self, budget: Budget | None = None) -> Budget:
        """The driver: propagate, assemble, repeat until neither changes anything or the budget is spent.

        **This alternation IS "arbitrary depth by dynamic assembly"** (§0): recursion is not a back edge,
        it is another instance wired on. Which also means the loop cannot be bounded by the topology — it
        is bounded by FUEL, and an exhausted budget must surface as UNKNOWN rather than as a negative
        answer (`fuel.Budget.verdict`)."""
        budget = budget or Budget()
        while not budget.exhausted:
            self.propagate(budget)
            if self.assemble(budget) == 0:
                break
        return budget

    # -- reads --------------------------------------------------------------

    def output_of(self, name: str):
        return self.units[name].output if name in self.units else EMPTY

    def why(self, f, at: str | None = None, depth: int = 8):
        """`why P?` — a SINK ON THE TRACE WIRES, which is where the two networks meet (§16.6).

        `at` names the vantage: an explanation is read from the trace value some unit actually holds, not
        from a global record, because there is no global record. Left unset it takes the frontier unit
        whose trace can describe `f` — the deepest, by the same frontier-first reasoning as §16.4."""
        from .trace import explain, handle_of
        if at is not None:
            return self.units[at].why(f, depth)
        cands = sorted(self.units.values(), key=lambda u: len(self.upstream(u.name)), reverse=True)
        for u in cands:
            if handle_of(u.trace_output, f) is not None:
                return explain(u.trace_output, f, depth)
        return None

    def derived_anywhere(self, pred: str) -> set:
        """Every conclusion of `pred` DERIVED by some unit, tagged with the unit that derived it. A
        debugging read, and note it is not a query: it walks the units this Net happens to hold, which is
        computation, not a global enumeration over data."""
        return {(u.name, f) for u in self.units.values() for f in u.derived(pred)}

    def __repr__(self) -> str:
        return (f"<Net units={len(self.units)} wires="
                f"{sum(len(v) for v in self.producers.values())} templates={len(self.library)}>")

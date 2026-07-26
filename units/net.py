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

from . import journal as J
from .fuel import Budget
from .journal import template_node as _tn
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
    _up: dict = field(default_factory=dict)                 # memoized `upstream`, dropped on any rewire.
    #                                                         `assemble` sorts every unit by upstream size
    #                                                         on every pass, so an unmemoized walk is
    #                                                         O(units x walk) per pass (§25.1).
    trace_producers: dict = field(default_factory=dict)     # consumer -> producers feeding it their TRACE
    #                                                         (§26). A separate channel because a trace
    #                                                         value must reach the consumer's VIEW — that
    #                                                         is what `solve` matches — while ordinary
    #                                                         units must never see one.
    journal: object = None                                  # the ASSEMBLER'S RECORD (§27) — a `Unit`
    #                                                         with a pinned trace, so its decisions are
    #                                                         readable by ordinary trace-consuming units.
    #                                                         Observable, never writable (§8 intact).
    dirty: set = field(default_factory=set)                 # units whose inputs changed since last pass —
    #                                                         the SEED for propagation (§25.1). Without it
    #                                                         `run` re-propagates the WHOLE net after every
    #                                                         assemble pass, which is quadratic in depth.

    # -- structure ----------------------------------------------------------

    def spawn(self, u: Unit) -> Unit:
        if u.name in self.units:
            raise ValueError(f"duplicate unit name {u.name!r}")
        self.units[u.name] = u
        self.dirty.add(u.name)
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
        self.dirty.add(c)
        self._up.clear()                                    # the topology changed; every walk is stale

    JOURNAL = "<assembler>"

    def _log(self, facts) -> None:
        """Append to the assembly journal.

        **The journal is NOT a unit**, deliberately. Making it one put it in `Net.units`, where it
        polluted every count, every `wellformed` walk and every `upstream` — the assembler's record is
        not part of the computation it records. It is a value with a reserved producer name, delivered
        by `propagate` to whoever asked for it."""
        if facts:
            self.journal = (self.journal or EMPTY).with_facts(facts)

    def reads_trace(self, name) -> bool:
        """Does this unit consume firing events? — a purely local test over its own LHS (§26.1)."""
        from .trace import FIRING_PREDICATES
        if name == self.JOURNAL:
            return False                                # the record itself reads nothing
        u = self.units[name] if isinstance(name, str) else name
        return any(isinstance(a, Triple) and a.p in FIRING_PREDICATES for a in u.lhs)

    def wire_trace(self, producer, consumer) -> None:
        """Deliver `producer`'s TRACE to `consumer`'s view (§26).

        **⚠ STRATIFIED, and the stratification was DISCOVERED rather than designed** (§26.1). A trace
        consumer is itself a unit, so it has a trace of its own; left alone the assembler wires one trace
        consumer to another and the regress never terminates — measured at 57 instances and fuel
        exhausted before the guard existed. §17.G predicted exactly this (*"firing on stability
        DESTABILISES… requires stratification, and must be designed in, not discovered"*) and it was
        discovered anyway. The guard is one local test: **a unit that reads the trace may not be wired to
        the trace of a unit that reads the trace.** Level 0 units are the world; level 1 units are about
        level 0. Level 2 needs a deliberate act, and there is not one.

        **§16.6's constraint becomes conditional rather than absolute, and the wording matters:** the trace
        must never accrete into an ordinary unit's value — but a unit whose LHS names a firing predicate
        has ASKED for it, and refusing would make metareasoning unsayable. What keeps the leak contained is
        SUBSET OUTPUT (§16): such a unit emits only what it derived, so nothing downstream sees the trace
        unless it too asked. `Net.trace_leaks()` still catches a unit that re-emits one."""
        pn = producer.name if isinstance(producer, Unit) else producer
        cn = consumer.name if isinstance(consumer, Unit) else consumer
        if pn == cn:
            raise ValueError(f"refusing to wire {pn!r} to itself")
        self.trace_producers.setdefault(cn, set()).add(pn)
        self.consumers.setdefault(pn, set()).add(cn)
        self.dirty.add(cn)
        self._up.clear()

    def upstream(self, name) -> set:
        """Transitive producers, walked over the topology — the only structure there is. Note what this
        does NOT consult: no scope, no context, no vantage. Reachability is the whole mechanism."""
        n = name.name if isinstance(name, Unit) else name
        hit = self._up.get(n)
        if hit is not None:
            return hit
        seen, frontier = set(), [n]
        while frontier:
            cur = frontier.pop()
            for p in set(self.producers.get(cur, ())) | set(self.trace_producers.get(cur, ())):
                if p not in seen and p in self.units:
                    seen.add(p)
                    frontier.append(p)
        self._up[n] = seen
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
            from .trace import FIRING_PREDICATES
            allneed = {a.p for a in lhs if isinstance(a, Triple) and isinstance(a.p, Node)}
            # A firing predicate cannot be satisfied from an OBJECT output — every unit emits firings on
            # its trace wire and none on its object wire. Splitting here is what makes a mixed template
            # (§26: inheritance reads `<band>` from the object wire and `<from>` from the trace) spawn on
            # its object half and complete on its trace half.
            need = allneed - FIRING_PREDICATES
            # A template reading ONLY firing predicates (an explanation hop, a stability watcher) has an
            # empty object need, so the object-driven spawn below would never trigger. It spawns on its
            # TRACE half instead. A MIXED template still spawns on its object half, which is more
            # selective — §26.
            on_trace = not need
            spawn_need = allneed if on_trace else need
            seen = self.consumed.setdefault(tname, set())
            # FRONTIER FIRST, and it is a correctness requirement rather than a preference (§16). Two
            # producers in one lineage can project identically while the deeper one carries strictly more
            # context — a hypothesis marker, a time index, an attribution. Taking the first one found
            # wires the SHALLOWEST, which silently drops that context and is precisely a BYPASS.
            cands = sorted(self.units.values(), key=lambda u: len(self.upstream(u.name)), reverse=True)
            # THE JOURNAL AS A SPAWN CANDIDATE (§27). It is not a unit, so the loop below cannot see
            # it — and a template that reads ONLY assembly events (*"which templates were never wired?"*)
            # has nowhere else to come from.
            if on_trace and self.journal and (self.journal.predicates() & spawn_need):
                proj = frozenset(f for f in self.journal if f.p in spawn_need)
                if not any(proj == pj for pj, _ in seen) and not any(
                        self.JOURNAL in self.trace_producers.get(i, ()) for i in self.instances[tname]):
                    n = len(self.instances[tname]) + 1
                    target = f"{tname}#{n}"
                    self.spawn(Unit(target, lhs=lhs, rhs=rhs))
                    self.instances[tname].append(target)
                    budget.spawns += 1
                    self.trace_producers.setdefault(target, set()).add(self.JOURNAL)
                    self.units[target].inputs[f"<trace>{self.JOURNAL}"] = self.journal
                    self.dirty.add(target)
                    seen.add((proj, self.JOURNAL))
                    added += 1

            for prod in cands:
                if on_trace and self.reads_trace(prod):
                    self._log(J.declined(prod.get_handle(), _tn(tname), J.STRATIFIED, True))
                    continue                                # STRATIFICATION (§26.1) — see `reads_trace`
                source = prod.trace_output if on_trace else prod.output
                if not (source.predicates() & spawn_need):
                    continue                                # nothing it emits could match this LHS
                projection = frozenset(f for f in source if f.p in spawn_need)
                # ORDER MATTERS: an ALREADY-WIRED producer is skipped silently. Logging it as
                # "nothing new" would make the journal grow on every re-run of a quiesced net, and the
                # journal rides a trace wire — so a growing journal destroys the fixpoint that
                # `output unchanged` depends on. §22.8's standing rule, reaching the RECORD of assembly.
                if any(prod.name in self.producers.get(i, ()) for i in self.instances[tname])                         or any(prod.name in self.trace_producers.get(i, ()) for i in self.instances[tname]):
                    continue                                # already wired somewhere — idempotence guard
                if any(projection == pj for pj, _ in seen):
                    self._log(J.declined(prod.get_handle(), _tn(tname), J.SEEN, on_trace))
                    continue                                # nothing NEW for this template to read
                if not budget.spend(1, f"assemble {tname}<-{prod.name}"):
                    return added
                up = self.upstream(prod.name)
                target = None
                for iname in self.instances[tname]:
                    if iname == prod.name or iname in up:
                        self._log(J.declined(prod.get_handle(), self.units[iname].get_handle(), J.CYCLE))
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
                    self._log(J.spawned(self.units[target].get_handle(), tname))
                (self.wire_trace if on_trace else self.wire)(prod.name, target)
                self._log(J.wired(prod.get_handle(), self.units[target].get_handle(), on_trace))
                seen.add((projection, prod.name))
                added += self._complete_lhs(target, need, allneed - need) + 1
            # RE-COMPLETE existing instances: a trace producer spawned in an earlier pass had no trace
            # output when its consumer was wired, so the trace half must stay open across passes.
            for iname in self.instances[tname]:
                added += self._complete_lhs(iname, set(), allneed - need)
        return added

    def _complete_lhs(self, iname: str, need: set, trace_need: set = frozenset()) -> int:
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

        # TRACE HALF (§26). A firing predicate is satisfied from a producer's TRACE output. The gate test
        # below does not apply: a trace wire supplies provenance, and provenance is not something an
        # object-wire chain GATES, so it cannot be a bypass of one. The CYCLE test still does.
        if trace_need:
            already = self.trace_producers.get(iname, set())
            cands = [u for u in self.units.values()
                     if u.name != iname and u.name not in already
                     and (u.trace_output.predicates() & trace_need)
                     and iname not in self.upstream(u.name)
                     and not self.reads_trace(u)]           # STRATIFICATION (§26.1)
            if (self.journal and self.JOURNAL not in already
                    and (self.journal.predicates() & trace_need)):
                self.trace_producers.setdefault(iname, set()).add(self.JOURNAL)
                inst.inputs[f"<trace>{self.JOURNAL}"] = self.journal
                added += 1
            cands.sort(key=lambda u: len(self.upstream(u.name)), reverse=True)   # frontier first (§16.4)
            # ALL of them, not just the deepest. A trace consumer is asking about FIRINGS, and a firing it
            # was not wired to is simply invisible — there is no "deepest one carries the rest" here,
            # because the trace wire does not accrete across units the way a branch carries its ancestor.
            # ⚠ The cost is §10.5 at its worst: EVERY unit emits every firing predicate, so this cannot
            # discriminate at all. Measured in §26 and recorded rather than hidden.
            for u in cands:
                self.wire_trace(u.name, iname)
                self._log(J.wired(u.get_handle(), inst.get_handle(), trace=True))
                inst.inputs[f"<trace>{u.name}"] = u.trace_output
                added += 1

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
            self._log(J.wired(cands[0].get_handle(), inst.get_handle()))
            inst.inputs[cands[0].name] = cands[0].output
            added += 1
        return added

    # -- propagation --------------------------------------------------------

    def propagate(self, budget: Budget | None = None, seed=None) -> int:
        """Run to quiescence over a WORK-LIST: refresh a unit's inputs, recompute, and re-enqueue its
        consumers only if its output CHANGED. That last clause is the termination argument and it is not a
        separate mechanism — it is the same idempotence result the queue-topology spike found (§7).

        A cycle therefore quiesces rather than spinning, PROVIDED the units are monotone in the sense that
        matters: a re-derivation that produces the same facts changes nothing and wakes nobody."""
        budget = budget or Budget()
        # `seed` is the SET OF UNITS WHOSE INPUTS CHANGED. Omitted, every unit is re-run — which is what a
        # caller reaching for `propagate` directly means, and what the first pass needs. `run` supplies a
        # seed after the first pass, because re-propagating the whole net after every assemble is
        # quadratic in chain depth (§25.1, measured: slope 2.50 -> 1.1).
        pending = list(self.units) if seed is None else [n for n in self.units if n in seed]
        seen = set(pending)
        self.dirty.clear()
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
            for p in self.trace_producers.get(name, ()):
                # A TRACE-CONSUMING unit gets the trace on its OBJECT channel, because `view()` is what
                # `solve` matches against. Distinct key so it cannot collide with an ordinary input.
                u.inputs[f"<trace>{p}"] = (self.journal if p == self.JOURNAL
                                           else self.units[p].trace_output)
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
        first = True
        while not budget.exhausted:
            self.propagate(budget, seed=None if first else set(self.dirty))
            first = False
            if self.assemble(budget) == 0:
                # ORPHANS are only knowable once assembly has quiesced — a template with no instances
                # might still get one on the next pass. But logging them CHANGES THE JOURNAL, and a
                # journal-consuming template ("which forms were never used?") can only assemble against
                # what the journal already says. So: log, and go round again if that told anyone anything.
                before = self.journal
                self._log(J.orphans(self).facts)
                if self.journal == before:
                    break
        # ⚠ `<unused>` is a CURRENT-STATE claim, not a firing, so a stale one is a false report — and the
        # watcher flags ITSELF, because at the pass where orphans were computed it had no instance yet.
        # Firings accrete (§20); a state claim must be withdrawn. Same shape as §16.6's supersession stub,
        # reached from the journal side.
        if self.journal:
            stale = [f for f in self.journal.by_pred(J.UNUSED)
                     if any(J.template_node(tn) == f.s and insts
                            for tn, insts in self.instances.items())]
            if stale:
                self.journal = self.journal.without(stale)
                # and REFIRE whoever read it — §7: nothing is retracted, downstream recomputes.
                readers = {c for c, ps in self.trace_producers.items() if self.JOURNAL in ps}
                if readers:
                    self.propagate(budget, seed=readers)
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

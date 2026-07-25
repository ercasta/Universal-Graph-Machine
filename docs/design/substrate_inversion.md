# Substrate Inversion — computation units as the substrate, graphs as the datum

> **Status: 🔭 ADOPTED AS THE ACTIVE LINE OF EXPLORATION, 2026-07-26.** This document records a proposal
> that CONTRADICTS the project's foundational substrate claim, deliberately and in the open, so that
> adopting or rejecting it is a decision rather than a drift. **It has now been taken deliberately.**
>
> The user's call, on the record and against this document's own first recommendation: *"I want to explore
> this design, not the old ugm."* The recommendation to finish 1c first (§13, earlier revisions) was
> conditional on being UNDECIDED — 1c and the scope reframe exist to serve a substrate this proposal
> replaces, so finishing them to enable a head-to-head comparison is only worth the weeks if the
> comparison might go the other way. It has been decided that it will not. The guard against arc-hopping
> was against drifting UNINTENTIONALLY; a stated re-point is the thing that guard exists to permit.
>
> **What that does and does not license.** Exploration, on this substrate, in this repo, behind the
> no-import rule (§14). It does NOT license retiring anything in `ugm/` — the old substrate stays working
> and untouched until this one answers a real question end to end, at which point deletion is the honest
> move ([[delete-old-code-aggressively]]) and archiving is not.
>
> **TRIPWIRE — and it trips.** `execution_topology.md`'s rule is that a design which cannot be stated
> without rewriting the commitments beneath it is a NORTH STAR, not a refinement. This one rewrites the
> substrate claim itself ("one uniform representation — a label-less attribute graph"), which is the
> commitment every other document in `docs/design/` inherits. It is therefore recorded HERE, as its own
> north-star candidate, and NOT folded into the execution topology it would supersede.
>
> **SPIKED 2026-07-26 — `bench/spike_substrate_inversion_binding.py`. BINDING SURVIVES (§14).** The one
> case worth spending a spike on per §13.2 — NETL's documented failure mode — does not recur, and the
> reason is mechanical: a unit's state is a subgraph, so a binding is carried structurally. Three findings
> amend this document in place: the store is BOUNDED rather than abolished (§2b), the index is NOT
> sufficient to assemble the topology (§3b), and structural sharing is load-bearing for CORRECTNESS rather
> than cost (§5). This result is what made the re-point defensible rather than speculative.
>
> **AMENDED 2026-07-26 BY §16 — SUBSET OUTPUT.** A rule now emits only what it derived; only branches and
> merges carry a view through. That splits accretion in two, retires both guards §15.1 invented, makes a
> non-firing unit a REAL GATE, and fixes a live assembler defect that was bypassing context-carrying
> chains. §3b's *"either alone is broken"* and §15.1(a)'s *"cycles are the default"* are corrected there.
>
> **§17 SPIKED IT BACK, 2026-07-26 — and found 2 failure points, both inside §16.** A merge can restore
> what a branch DROPPED (§16.5's own recommendation is a bypass); and NAF over a hand-wired cycle converges
> to a different answer per work-list order, silently. Assembled nets are DAGs, so the fixpoint is
> guaranteed — **which means the cycle guard's justification MOVED and it must not be retired.**
>
> **§18 ATOMIC CHAINS (user), RECORDED NOT BUILT.** A contextualized concept is a chain that must not be
> split, and the assembler splits it — measured. The conditional and the syllogism are STRUCTURALLY
> IDENTICAL and semantically opposite, so no topological rule separates them: **the criterion is FORCE**
> (atomic exactly where intermediates carry no assertoric commitment), which makes chain identity fall out
> of form instantiation with no new declaration. §19 carries the session's remaining reasoned residue.
>
> **What it is NOT.** Not the queue topology (`execution_topology.md`), which schedules access to a shared
> graph. Not the cell-network amendment (§13 there), which indexes rules over a shared graph. Both of those
> keep ONE store and make computation better-behaved around it. **This proposal deletes the store.**
>
> Companions, all of which it would partly retire: `execution_topology.md`, `scope_reframe_audit.md`,
> `reactive_core.md`, `reconsider_design.md`, `../attic/isa_control_machine.md`.
>
> **Honest status of the arc, kept rather than deleted.** [[execution-topology-ratified]] was ratified
> 2026-07-25, its §13 amendment landed 2026-07-26, and this document was written the same day — the exact
> pattern §12 there names as this repo's characteristic failure mode. That observation was the argument
> against acting, it was made, and it was overruled on the merits above. It stays on the record because
> the honest test of a deliberate re-point is not that the objection was absent but that it was answered:
> if this line stalls, the pattern is the first place to look, not the last.

---

## 0. The claim, in one paragraph

> **We started from a substrate that is ONLY data (a graph) and bolted computation onto it. Invert it:
> make COMPUTATION UNITS the substrate, let each unit hold its own state — a whole subgraph — and let the
> connections between units be DYNAMIC, so that the rules in the KB and the events of the discourse
> physically modify the topology. A unit fires when its input subgraph matches its LHS, producing a new
> subgraph that flows on to whatever the topology says consumes it.** The advantage over the biological
> analogy is exactly the thing biology cannot do: neurons must be physically wired, whereas units can be
> assembled on demand — so depth is not bounded by what was grown.

Facts do not live anywhere, because there is no anywhere. What used to be "the graph" is not the store;
it is **the value flowing on a wire**.

---

## 1. The inversion, named precisely

In architecture terms the change has a standard name in both directions:

| | today | proposed |
|---|---|---|
| shape | **blackboard** — one shared structure, knowledge sources reading and writing it | **pipeline / dataflow** over graph-valued streams |
| the graph is | the STORE (mutable, global, accumulated) | the DATUM (a value on a wire, produced by a unit) |
| a rule is | a transformation applied TO the store | a UNIT the value flows THROUGH |
| finding data | search — match the LHS against everything | none — the data is already in the unit |
| isolation | POLICED (`is_visible`, write discipline, crossing rules) | STRUCTURAL — there is no address for what wasn't piped in |
| history | lost (mutation), reconstructed via provenance | inherent — every intermediate value has a producer and a name |

The last two rows are the substance. **Isolation stops being enforced and becomes a calling convention**:
a unit cannot see what it was not given, not because a predicate forbids it but because no address exists.
And the "unrolling" of a sequence of transformations into named intermediate values is the difference
between mutable accumulation and SSA — which is why provenance becomes free rather than bolted on.

**The falsifiable test of whether this is a real inversion rather than a graph in costume:**

> **There is NO GLOBAL ENUMERATION over data.** `AttrGraph.nodes_with_key` — whose own docstring says
> "this is the ONLY index" — is what makes today's substrate a store. If any part of the design must scan
> all units to find candidate *facts*, the inversion has not happened.

The design passes this, but only just, and §3 states the one exception carefully.

---

## 2. What a unit is — and the taxonomy is BY DEGREE

A unit holds **a whole subgraph**, not an activation. Its input is a subgraph; it matches its LHS against
that input; if it matches it emits an output subgraph. Its output flows to whatever the topology connects.

The consequence worth stating first, because it is the cleanest result in the proposal:

> **There is no fact/rule distinction. There is only IN-DEGREE.** An axiomatic fact — *"jack is tall"* — is
> a unit with NO INPUT whose output is a fixed subgraph. A constant is a nullary function; a given is a
> nullary computation.

| in-degree | out-degree | what it is |
|---|---|---|
| 0 | ≥1 | a **given** — an asserted fact, a source. Fires once; its value sits on its out-wires. |
| ≥1 | ≥1 | a **rule** — the ordinary case. |
| ≥1 | observed by the asker | a **query / goal** — a sink whose output is the answer. |

So intake, assertion, and asking are all one act: **spawn a unit**. The KB is not a store of facts plus a
store of rules; it is a library of units, and the difference between its members is how many wires they
have. `why` for a base fact falls straight out — in-degree 0, *"you told me"* — which is exactly the
`(given)` that `provenance` answers today, arrived at structurally instead of by a special case.

Force, attribution, and band all ride INSIDE the emitted subgraph, so a source unit can carry *who said
it, when, and how strongly* with no extra mechanism ([[force-is-the-missing-axis]], [[possibilistic-layer]]).

**Confirmed by the spike, and it collapsed one more distinction than expected.** The spike's first draft
kept "a source" and "a hypothesis branch" as separate constructs; they turned out to be the same unit with
different in-degree — a `delta` the unit contributes unconditionally, plus whatever its inputs carry
through. An axiom is that construct at in-degree 0. There is no separate notion of "a fact" anywhere in
the implementation, which is the taxonomy above arrived at by force rather than by design.

### 2b. The store is BOUNDED, not abolished — and this is a correction

A finding the design did not state, and the sharper form of the whole claim:

> **A unit joins over the UNION of its inputs. So it HAS a store — one consisting of exactly what its
> in-edges deliver.** "No blackboard" does not mean "no store"; it means **no UNBOUNDED SHARED store.**

The distinction is not pedantic, because it relocates the thing that has to be got right. A unit's
**IN-DEGREE is what bounds its epistemic reach** — it is the analogue of a scope, and it is the quantity
to reason about when asking what a unit could possibly conclude. §1's table row "isolation is structural"
should be read as: isolation is *a property of in-degree*, and every wire added is a deliberate widening
of what a unit may know.

**What survives from the current ISA, and it is more than expected.** `SEED`/`FOLLOW`/`TEST`/`JOIN` ARE
"match a subgraph"; `MINT`/`EMIT` ARE "produce one". The opcodes are nearly intact — what changes is their
ADDRESS SPACE: a bounded input value rather than a global graph. That materially lowers the cost of this
proposal versus the first estimate, and it means [[machine-semantics-are-isa-programs]] and
[[firmware-over-isa-design]] are preserved rather than discarded.

---

## 3. Wiring — the index, and the one global structure

When a unit emits, the system decides who consumes it. When a unit is SPAWNED, the system decides who
feeds it. Both are index lookups, and they run in opposite directions:

- **forward** — *whose LHS could take this output?* Needs an index over unit **inputs** (LHS heads).
- **reverse, at spawn time** — *who could feed this new unit?* Needs an index over unit **outputs** (RHS).

So: a bidirectional index keyed on predicate. This is the same computation as `reconsider._affected`'s
body→head closure over the active bank, which is a known quantity in this codebase.

**Three disciplines, each load-bearing:**

1. **The index is a CHEAP NECESSARY CONDITION, never exact.** Deciding "could this output match that LHS?"
   exactly *is* performing the match, which would move the matcher into the router. It keys on something
   coarse (predicates present, key constants present) and yields CANDIDATES; the unit itself decides
   whether it fires. Wake broadly, fire narrowly — the distinction the §13 spike found load-bearing
   (`bench/spike_cell_network.py`, cases 4a and 5: a unit that woke and correctly wrote nothing).
2. **Filtering is CONSUMER-SIDE.** A's output is attached to B, C and D; each takes the part it cares about
   and discards the rest. The unit's LHS is then the single source of truth for what it needs, and the
   router stays dumb. Costs bytes on the wire; buys the absence of a second place where "what B needs" is
   written down.
3. **THE UNIT INDEX IS THE ONLY GLOBAL STRUCTURE IN THE SYSTEM.** It indexes COMPUTATION, not data —
   the subgraphs still travel only along wires. This is the sole exception to §1's test, and it is a
   principled one. **If a second global structure appears, something has leaked back into being a store.**

**Spawn is LAZY.** A unit is instantiated when an output arrives that could feed a rule not yet
instantiated — never eagerly from the whole KB. The network therefore grows along the path reasoning
actually takes, and rules nobody needed are never materialized. [[agent-not-theorem-prover]] becomes
structural rather than a policy, and §4 shows laziness is doing much heavier work than tidiness.

### 3b. CORRECTION (spiked 2026-07-26) — the index is NOT sufficient to assemble the topology

As written above, §3 reads as though predicate-level indexing determines the wiring. **It does not, and
the failure is total rather than partial.** Spike case 6 ran the assembler on the index alone: every
producer of a matching predicate was wired into one instance of the rule, so a single unit saw BOTH
hypothesis branches and derived both conclusions. **The chains collapse completely** — which would take
§4's entire emergence claim with them.

What separates them is a SPAWN POLICY, and the spike found a purely local one that works:

> **A producer joins an existing instance only if it is COMPARABLE — ancestor, descendant, or identical —
> with EVERY producer already wired into that instance. Two sibling branches are incomparable, so the
> second one SPAWNS A NEW INSTANCE of the rule instead of adding a wire.**

Three things about it are worth recording:

- **It names no scope, context or vantage.** It is reachability over the wiring, walked with the topology
  that is already there. So §4's claim survives: scope stays emergent — but it is emergent *from an
  assembly policy*, not from the index, and the difference between those two statements is the difference
  between the design working and not.
- **The quantifier is load-bearing.** "Comparable with EVERY existing input", not "with ANY". `base` is an
  ancestor of both branches, so an any-test lets H2 join the instance already holding H1 and the chains
  collapse regardless. One quantifier.
- **Accretion is what makes the new instance viable.** A fresh instance wired only to H2 still sees base,
  because H2 carries it through (§5). Without accretion a spawned sibling instance is starved and derives
  nothing — which is exactly how the spike failed on its first run, when the branches were mis-modelled as
  independent sources. **Accretion and the spawn policy are not two features; either alone is broken.**

---

## 4. Scope is NOT a primitive here — it is a chain, and that is the point

The temptation (and the author of this document's first three attempts) is to re-import scope as a key:
"unit identity = (rule, context)". **That is a superimposition and it is unnecessary.** Two instances of
the same rule differ because they have DIFFERENT IN-EDGES. The wiring already carries the context; nothing
needs to name it.

> A scope is just a chain. An `E` wired to both a hypothesis chain and the base chain gets input from both,
> and nothing about that is special — it is what having two in-edges means.

**How does anything downstream know it is reasoning under a hypothesis?** Because hypothesis-ness is IN THE
CARRIED SUBGRAPH, as an ordinary fact, and a unit changes only the part of its input it touches — the rest
is carried as-is. So a fork produces several deltas that are applied at the join points, and the marker
travels with the value. A rule can therefore match on being-under-a-hypothesis exactly as it matches on
anything else, which is [[composability-principle]] satisfied by construction rather than by discipline.

**And the same rule exists in several places at once.** One `E` wired only to base facts; another wired to
base plus two hypothesis chains. Same rule, different units.

### 4b. What that costs, stated honestly: it is the ATMS's exponential, relocated

This is the price tag, and it should not be discovered later:

> **Instantiating one unit per combination of chains is COMPUTING ATMS LABELS BY TOPOLOGY INSTEAD OF BY
> ALGEBRA.** de Kleer's ATMS attaches to each datum the set of environments in which it holds; the
> expensive part is computing those labels minimally. Here the same information is carried as INSTANCES —
> three environments in which E's conclusion holds means three E-units producing it. Same content, and the
> same worst case: exponential in the number of hypotheses. That is the documented cost of the ATMS, and
> the reason JTMS (one context at a time) survived in practice.

The exponential is not avoided. It is moved into the topology, where it is at least VISIBLE — you can
count units. **What keeps it unrealized is LAZY SPAWN**: only environments reasoning actually explores get
instantiated. That makes §3's laziness an INVARIANT rather than a default, and it is the single most
important thing to preserve if this is ever built.

**A consequence worth noticing, because it is free.** Merging a hypothesis chain with base marks the
output hypothetical, which over-marks any conclusion that did not actually depend on the hypothesis. That
would be a defect in a labelling scheme — here it is harmless, because the base-only conclusion is derived
anyway, by the base-only instance. The topology computes the minimal label by having one instance per
environment, rather than by minimizing a label.

---

## 5. What flows — accretion PER PATH, and deltas that can remove

A unit's output is its input plus what it changed; the untouched remainder is carried through. On a single
shared store, accretion destroys isolation. **On a forking topology it creates it**: what accretes is one
accumulated subgraph PER PATH, and a per-path accumulated subgraph is precisely what a context is.

Two things follow that must be designed rather than assumed:

- **The delta must be able to REMOVE and OVERRIDE, not only add.** *"Under H, not P"* against a base that
  holds P is most of what a hypothesis is for, and additive-only cannot express it. Note this makes the
  VALUE on the wire non-monotone while each unit remains a pure function — which is safe here in a way it
  never was on a blackboard (§7).
- **Forks duplicate the value, and chains grow it.** A deep chain with several forks copies a lot. This is
  the OR-parallel Prolog trade-off with thirty years of measurement attached (Aurora/Muse: binding arrays,
  hash windows, version vectors, copying — Muse chose copying, as did
  [[derivation-frame-consolidation]]). **Structural sharing (persistent graph, HAMT-style) is what makes it
  affordable, and it is far easier to design in than to retrofit.** This is the difference between
  "elegant" and "runs".

  **UPGRADED BY THE SPIKE from a cost question to a CORRECTNESS requirement.** Case 2 joins a variable
  across two wires and shows the join must be by **node IDENTITY, never by name** — two independently
  minted nodes both called `mary` produce a false conclusion under name-matching and none under identity
  ([[node-identity-is-not-a-semantic-proxy]], and the reason there is no `nodes_named` in this substrate).
  Identity must therefore be **INHERITED through the pipeline**, which means the same node object has to
  survive every fork and union unchanged. A copy that re-mints nodes is not slow — it is WRONG. So
  structural sharing is not an optimization to add later; it is what makes cross-wire binding mean anything,
  and it belongs in the first line of any implementation.

---

## 6. Negation — there are TWO, and only one of them is hard

The single largest simplification in the proposal, and it comes from immutability rather than from any
negation machinery.

**(a) NAF over the value on a wire is EXACT, IMMEDIATE, and needs no fuel.** The subgraph that arrived is a
FINISHED value — whatever upstream produced. "P is absent from this input" is decidable the moment it
arrives: no drain, no fixpoint, no "is it done yet". Compare the three previous framings, every one of
which needed a global or tree-scoped completion condition.

**(b) NAF over the OPEN DERIVATION — "P is not derivable at all" — is semi-decidable, and the answer is
FUEL.** You are not done until you stop adding units, and adding is fuel-bounded. This is not a regression:
the blackboard hid the same fact behind "run to fixpoint", which terminates only because the rule set is
finite and stratified. Fuel makes the implicit explicit, and it is the same knob as
[[think-harder-chapter]].

**The two must be MARKED DIFFERENTLY on the conclusions they license**, because (a) is stable and (b) is
provisional-pending-more-fuel. Collapsing them is how a resource limit silently becomes a claim about
the world.

**The caveat, stated because it is a genuine cost.** Fuel-bounded NAF lets SCHEDULING POLICY LEAK INTO
SEMANTICS — how much fuel, spent in what order, determines what the system believes. `execution_topology.md`
§8 forbids exactly this in its own domain ("focus selects which queue drains, never what a rule does").
It is defensible here only because (b) is irreducibly resource-bounded in ANY system — but it must be
DECLARED rather than discovered, and (a) should be preferred wherever the design can arrange it.

### 6b. The one remaining unbounded-arrival hazard, precisely located

Not in the queue, not in the network, not in negation generally:

> **Lazy spawn can wire a NEW PRODUCER into a unit that has ALREADY FIRED.** So a unit's in-degree is not
> stable, so "I have all my inputs" is never final, so an NAF conclusion taken at that unit is revocable
> by a wire that appears later.

The fix is already in the design and is better than anything a blackboard can offer: **REFIRE.** A
late-wired producer invalidates the consumer's cached output and it recomputes. NAF conclusions become
revisable BY RECOMPUTATION rather than needing to be right first time.

---

## 7. Revision — the retraction apparatus DISSOLVES

Each unit caches its last OUTPUT (not "a copy of the graph" — that reading would re-create global shared
state N times over with a consistency problem). A wire holds a value. Three things follow at once:

- **refire without recomputing upstream** — re-run from the changed unit forward, using cached inputs;
- **change propagation** — push only when the new output differs from the cached one;
- **termination** — "output unchanged" IS the stopping condition. This is the idempotence result the §13
  spike found (cases 4a vs 4b), arriving here from an unrelated direction. Third independent derivation.

And therefore:

> **`retraction.py`, the cascade, copy-on-delete, `broken_assumption` stamps, and most of
> `reconsider.py` are artifacts of MUTABLE SHARED STATE. Here they have no work to do.** Nothing is
> retracted because nothing was ever shared; downstream simply recomputes. Nanopass compilers never undo
> a pass — they re-run from the pass whose input changed.

Which also means **non-monotonic reasoning without a TMS**: defaults, overrides and counterfactuals are
just a different value flowing down a different chain. [[monotonicity-claim-dropped]] stops being a
concession and becomes a non-issue. What survives is POLICY — deciding WHICH unit to re-run from — a far
smaller problem than unwinding a world, and the surviving content of [[reconsider-arc]].

---

## 8. Introspection — the trace IS the program

Because the network is assembled as it runs and every intermediate value is named and cached:

- **`why` is a backward walk along wires.** No separate provenance subsystem
  ([[structural-addressing-bydesc]]'s backfill, the justification nodes) — the structure already is the
  explanation.
- **"Let me think again — we said X, then Y…" is re-running a subpath**, at a chosen point, with the
  upstream values still in hand.
- **System-2 self-talk is observing what is currently flowing**, and "think harder" is literally
  ASSEMBLE MORE — spend more fuel extending the network (§6b). The metaphor and the mechanism are the
  same thing, which is the strongest form of the claim.

**Where the §8-style line falls, unchanged in location:** the flowing SUBGRAPHS are content and are fair
game for a unit to observe; **the assembler's choice of what to wire next is policy and is not.** Cross
that and dynamic scoping returns wearing a new costume.

Note also that this makes METAREASONING cheap — Phase 9 cut full bank reification as too expensive on a
blackboard ([[forms-as-kb-data]]). On this substrate it may be worth reopening, deliberately.

Debuggability is not a nicety here but a REQUIREMENT: a dynamically-wired system cannot be statically
checked, so the trace is the only thing there is to inspect. Fortunately it is also free.

---

## 9. What it would cost this codebase — the honest inventory

| survives | mostly retired | genuinely new |
|---|---|---|
| the ISA data path (`SEED`/`FOLLOW`/`TEST`/`JOIN`/`MINT`/`EMIT`), re-addressed to a bounded input | `AttrGraph` as a global store (`nodes_with_key` as a data index) | the bidirectional unit index (§3) |
| `ControlMachine`, `Continuation`, `SUSPEND` (a unit's suspension is unchanged) | `scope_tree.py` — `<under>`, `is_visible`, `scope_chain`, the crossing rules (§4 makes them emergent) | the assembler: spawn + bidirectional wiring + fuel (§3, §6) |
| `reconsider._affected`'s body→head closure — becomes the index | `retraction.py`, the cascade, copy-on-delete, most of `reconsider.py` (§7) | structural sharing for graph values (§5) |
| the lowering compiler (rules → ISA programs) — now compiles a UNIT | `chain.py`'s global match/demand loop | per-unit output caching + change propagation (§7) |
| intake, CNL, the form inventory — unchanged, they produce units instead of facts | `reactive.py`'s dirty-grain queue (subsumed by wiring) | |

**The scope reframe is the interesting entry.** It is not ported and not discarded — it becomes EMERGENT.
Everything `scope_reframe_audit.md` builds by construction (composition = nesting, isolation = default,
crossing = a data rule) falls out of chains, in-edges, and carried values. If this substrate is right, that
document's *conclusions* are right and its *mechanisms* were the shape a store forced on them.

---

## 10. Open questions, in order of cost-if-wrong

1. ~~**Structural sharing.**~~ **CLOSED as a question, OPEN as a requirement** (§5, spike case 2). Not a
   cost trade-off: identity must be inherited through the pipeline or cross-wire binding is unsound. It is
   a first-line implementation constraint, not a later optimization.
2. ~~**Cycles.**~~ **CLOSED 2026-07-26 — and it was DISCOVERED, not decided** (§15.1). This entry said
   "decide it; do not discover it", and the opposite happened: the first two-rule chain built produced a
   cycle immediately. Accretion means every downstream unit carries its ancestors' facts through, so it
   looks like a producer of every UPSTREAM predicate — cycles are the assembler's DEFAULT behaviour, not
   an accident it might stumble into. Settled: **refuse cycles, allow unrolling**, and the two are
   distinguishable locally (§15.1).
3. **Unit lifetime.** Units persist so refire works — that is their value. But they are then the session's
   working set and something must end them. At session scale ([[ugm-scope-session-sized]]) it may simply
   not matter, which would be the cheapest possible answer and should be checked before machinery is built.
4. **Where the discourse's own rules enter.** "The KB and the discourse physically modify the topology" is
   the central claim and the least specified part: a rule authored mid-conversation must become a unit and
   be wired, which is [[forms-as-kb-data]] on this substrate.
5. **Whether the LHS index can stay coarse under real grammar.** §3.1's necessary-condition discipline is
   what stops the router becoming the matcher; whether predicate-level keys are selective enough on real
   CNL is an empirical question, and [[measure-before-optimizing-ugm]] says measure rather than assume.

---

## 11. Prior art

**The tradition this belongs to is not the one the previous documents were in.** `execution_topology.md`
§11 catalogues contexts/TMS, tabling, OR-parallel logic programming, and dataflow; §13.5 adds production
match networks. This proposal's ancestors are elsewhere and are mostly forgotten, which is weak evidence
that the direction is genuinely different rather than a re-description.

- **NETL (Fahlman, 1979)** — a semantic network in which every node AND link is a processing element with
  state, inference by marker passing. Almost exactly this substrate. **Its documented failure is the one to
  watch**: it handled inheritance beautifully and foundered on VARIABLES AND BINDING, which is precisely
  this project's known weak axis ([[binding-is-the-missing-axis]]).
- **Minsky's K-lines** — memory as a dynamically assembled set of connections that reconstitutes a mental
  state. "The discourse physically modifies the topology", stated in 1980.
- **Copycat's Slipnet (Hofstadter & Mitchell)** — a network whose link lengths change with what is
  happening, driven by active codelets. The closest thing to a working system in this shape.
- **Flow-based programming (Morrison)** — pipes and filters with typed information packets; the direct
  ancestor of §3's consumer-side filtering.
- **Nanopass compilers** — a pipeline of small passes, each producing a fresh IR, adopted precisely for
  isolation and traceability. **The closest successful engineering analogue, and the source of §7's
  "re-run, don't undo".**
- **Graph rewriting systems** (double-pushout; GrGen, Groove) for "a unit is a graph transformation", and
  **Stratego** for assembling the rewrite strategy dynamically.
- **ATMS (de Kleer 1986)** — not as an analogue but as the COST MODEL (§4b).
- **Actors (Hewitt)** — state plus dynamic creation, but notably no joins, which is the half this design
  has to supply itself.

**The blackboard tradition (Hearsay-II, BB1) is what is being REJECTED**, and its virtue should be named
rather than dismissed: a blackboard is good at OPPORTUNISM — any knowledge source can notice anything,
including what nobody anticipated. A pipeline gives that up; a unit sees exactly what it was wired to see.
§3's index is the answer (wire broadly on a cheap condition), but it is an answer that must keep working,
and *"watch out for X"* is the standing test case.

---

## 12. Risks

- **Arc-hopping, and this document is an instance of the pattern.** See the status header. The topology was
  ratified yesterday; §13 landed today; this was written today. Nothing here should be acted on before 1c
  ships and the ratified model has met real data.
- **The ATMS exponential** (§4b). Visible, countable, and contained only by lazy spawn.
- **Copying** (§5). The one place where "perf is not the motivation" does not excuse a decision.
- ~~**Binding.**~~ **RETIRED 2026-07-26 — spiked, does not recur** (§14). NETL's failure was that a marker
  carries no binding; a unit whose state is a subgraph carries it structurally. What replaces this risk is
  narrower and stated above: identity inheritance (§5) is the thing that can still make binding unsound.
- **Opportunism lost** (§11). Structural, not incidental.
- **Policy leaking into semantics** (§6). Fuel-bounded NAF is the breach; declared is survivable,
  discovered is not.
- **The seduction of elegance.** Almost every section above reports a simplification. That is either
  because the inversion is right, or because a design with nothing built has not yet met the cases that
  complicate it. The four previous north stars in this repo's memory each read this well on paper.

---

## 13. The exploration plan

**SUPERSEDED 2026-07-26** — this section was written as a deferral ("if it were ever taken up"). The
re-point has been taken; it is now the actual plan. Ordered by WHICH CLAIM, IF FALSE, KILLS THE DESIGN —
not by what is easiest or most fun to build.

1. **Finish the current arc first.** 1c, then the ratified queue topology against real data. This document
   is worthless as a reason to stop that and valuable only as a thing to compare against afterwards.
2. **Spike BINDING, not plumbing.** The plumbing (§3 index, §5 flow, §7 caching) is well-trodden and will
   work. A unit whose LHS binds variables across two inputs, in two hypothesis chains, is the case NETL
   failed at and the only one worth spending a spike on.
3. **Then the falsifiable test** (§1): build the smallest end-to-end thing that answers a real question
   with NO global enumeration over data. If it needs one, the inversion did not happen.
4. **Then decide**, with both models standing and measurable, which is the substrate.

---

## 14. SPIKED 2026-07-26 — binding survives (`bench/spike_substrate_inversion_binding.py`)

§13.2 said: spike BINDING, not plumbing, because NETL is the closest ancestor of this substrate and
variables are the documented place it broke — which is also this project's known weak axis
([[binding-is-the-missing-axis]]). Run under an agreed **no-import rule**: the spike may not import from
`ugm/` (asserted mechanically), so anything it needs is copied, and what gets copied is evidence about
what is genuinely shared rather than a store-shaped assumption riding along.

| case | result |
|---|---|
| 1 — the NETL diagnosis: marker passing vs subgraph passing on a two-place join | **PASS** — markers answer 4, of which 2 are false; the unit answers exactly 2 |
| 2 — cross-wire binding by IDENTITY, not name | **PASS** — name-matching fabricates a conclusion from two distinct `mary`s; identity does not |
| 3 — legitimate cross-chain join (base + hypothesis) | **PASS** |
| 4 — sibling isolation at binding level | **PASS** — and nothing in the implementation is named scope, context or vantage |
| 5 — §1's falsifiable test: no global enumeration over data | **PASS** — the one global is the unit index, keyed by predicate |
| 6 — can the topology be ASSEMBLED rather than hand-wired? | **PASS, but only with §3b's spawn policy** — the index alone collapses the chains entirely |

**VERDICT: GO on binding.**

### 14.1 Why it does not recur, stated mechanically

NETL propagates a MARKER — one bit at a node. Inheritance works perfectly, because inheritance needs no
correlation. A two-place join fails, because there is nowhere to record WHICH `?y` a given `?x` went with,
so `jack likes mary, bob likes sue, mary is rich, sue is poor` yields the CROSS-PRODUCT: four answers,
two of them false. That is the whole of NETL's difficulty, reproduced in eight lines.

**A unit whose state is a SUBGRAPH carries the binding structurally — the value of `?y` is simply a node
in the value.** So the join is exact, and it is exact for a reason that cannot decay: there is no separate
binding mechanism that could be got wrong, because the binding IS the datum. This is the single most
important difference between this substrate and its closest ancestor, and it is not a matter of degree.

### 14.2 The three amendments this forced, all made in place

1. **§2b — the store is BOUNDED, not abolished.** A unit joins over the union of its inputs, so it has a
   local store: exactly what its in-edges deliver. "No blackboard" means no *unbounded shared* store. The
   quantity that now bounds a unit's epistemic reach is its **in-degree**.
2. **§3b — the index is NOT sufficient to assemble the topology.** On the index alone the chains collapse
   completely: one instance sees both hypotheses and derives both conclusions. A local spawn policy fixes
   it (comparable-with-EVERY-existing-input; the quantifier is load-bearing), and it names no scope — so
   emergence holds, but from an assembly policy rather than from the index, which §3 did not say.
3. **§5 — structural sharing is a CORRECTNESS requirement, not a cost trade-off.** Cross-wire binding must
   join by node identity; a copy that re-mints nodes is not slow, it is wrong.

### 14.3 What the spike deliberately did NOT test, and what it therefore cannot claim

Fuel, refire, lifetime, cycles, negation, and any question of scale. It is a binding spike and it answers
a binding question. In particular it does **not** show that this substrate works — it shows that the one
thing that historically killed this substrate does not kill this one. Every simplification claimed in
§§6–8 remains unbuilt and untested, and §12's last risk (*the seduction of elegance*) is not discharged by
a spike that only ever had six units in it.

**What it licensed.** Not a claim that the substrate works — a claim that the obvious objection to it is
answered, and does not have to be re-litigated. That was enough to make the re-point in the status header
a decision on evidence rather than on taste. The exploration plan is §13.

---

## 15. BUILT 2026-07-26 — the `units/` package

The exploration is under way. `units/` is a sibling of `ugm/`, behind the no-import rule (enforced by
`tests/units/test_no_ugm_import.py`, statically and by a subprocess check for transitive imports). `ugm/`
is untouched and still working; nothing is retired until this substrate answers a real question end to end.

| module | what it owns |
|---|---|
| `value.py` | `Node`, `Fact`, `Subgraph` — the immutable value on a wire, with a per-value predicate index (bounded local enumeration, which §1 permits) and identity-preserving `union`/`with_facts`/`without` |
| `match.py` | `Var`, `Triple`, `Absent`, `solve` — binding, and §6a's exact NAF over the wire value; safety checked at construction |
| `unit.py` | `Unit` — delta + inputs → output, output caching, change detection; `given`/`rule`/`branch` are the same class at different in-degree |
| `net.py` | the LHS/RHS index, the §3b spawn policy, wiring, work-list propagation, and the assemble/propagate driver |
| `fuel.py` | `Budget` and the three-valued `Verdict` — §6b's honest UNKNOWN, which refuses to be truthy so it cannot collapse into NO |

29 tests, all green, written as the document's own claims rather than as unit tests of the code:
`test_binding.py` (the spike, promoted), `test_assembly.py` (§3b including its negative case),
`test_negation_and_fuel.py` (§6's two negations, §7's revision-by-rerun, and §6b's identified hole).

### 15.1 Three things building it found that designing it did not

**(a) CYCLES ARE THE DEFAULT, and §10.2 was wrong to expect otherwise.** The first two-rule chain — `R1`
feeding `R2` — wired `R2`'s instance straight back into `R1`'s. The cause is accretion (§5): a downstream
unit carries its ancestors' facts through, so its output contains the UPSTREAM predicates, so the index
correctly identifies it as a producer for the upstream rule. This is not an edge case the assembler might
hit; it is what it does unless told not to.

**(b) UNROLLING AND CYCLING ARE THE SAME MOVE UNTIL YOU DISTINGUISH THEM — and §0's depth claim depends on
getting it right.** A rule unit's output never re-enters its own view, so **a unit cannot iterate on its
own**: transitive closure is impossible without either a back edge or a chain of instances. The design
already chose the chain ("you don't add a cycle, you unroll"), and the mechanical form of that choice is:

> A producer may feed a **NEW** instance of a template it is itself an instance of (that is depth). It may
> never feed one that is already **upstream** of it (that is a cycle).

Both are local tests over the wiring, which is the only structure there is. Forbid the first and
transitivity becomes inexpressible; permit the second and a unit's own conclusion re-enters its own input.

**(c) TERMINATION OF ASSEMBLY NEEDED A THIRD GUARD: PROJECTION DEDUP.** With (a) and (b) in place,
assembly still ran forever — every downstream unit kept re-spawning every upstream rule whose predicates it
was carrying. The fix is to feed a template a producer only when that producer's output **restricted to the
predicates the template actually reads** is one no instance has consumed. Projecting rather than comparing
whole values is the whole trick, and it makes assembly stop by the same idempotence condition that
terminates propagation — one level up. **Fuel is therefore the bound on pathological cases, not the
mechanism by which ordinary assembly ends**, which is the right division and was not obvious beforehand.

### 15.2 A correction to `Unit.derived`, and why it is worth recording

The first implementation recovered "what did this unit conclude?" by subtracting its view from its output.
That is silently wrong whenever a unit's own conclusion can reach its own input — i.e. in exactly the
cyclic case above — and it reported *nothing derived* rather than failing. It is now RECORDED at run time
(`last_derived`), because **a derivation is a fact about a run, not a property recoverable from the
values afterwards.** The bug was found only because a test asserted a conclusion that a human could see
was there; a subtraction-based probe is exactly the kind that agrees with itself while both sides are
wrong.

### 15.3 Honest scope of what now exists

It is a substrate, not a system. There is no intake, no CNL, no query surface, no `why`, no structural
sharing beyond what Python's frozensets give (the spine is copied per union — §5's HAMT is recorded and
not done), and nothing has been run at any scale. Every claim in §§6–8 that is not in the test list above
remains unbuilt. **§12's last risk stands undiminished**: the simplifications keep reporting themselves,
and 29 green tests over a few dozen facts is not evidence against a design being too clean to survive
contact.

---

## 16. SUBSET OUTPUT — accretion split in two (user proposal, SPIKED AND LANDED 2026-07-26)

> **The proposal (user):** *"what if each node only outputs a subset of the graph, and there are nodes
> dedicated to merging?"* Measured in `bench/spike_subset_output.py` (27/27), landed in `units/`
> (37 green), promoted to `tests/units/test_subset_output.py`.

`units/unit.py`'s `new = view.with_facts(fresh)` was the entire accretion decision. Replacing it with
**a rule emits only what it derived; everything else emits its view** turned out to separate two things
this document had treated as one — and only one of them was ever load-bearing.

| | kept or lost | consequence |
|---|---|---|
| **BRANCH accretion** — a `branch`/`carrier` passes its view through | **KEPT** | §3b's spawn policy still works: a sibling instance wired only to H2 sees base because H2 carries it. Sibling isolation re-measured, unchanged. |
| **RULE accretion** — a rule re-emits everything it read | **GONE** | both guards §15.1 invented are no longer needed |

**This CORRECTS §3b's closing sentence.** *"Accretion and the spawn policy are not two features; either
alone is broken"* is too strong. The policy depends on **branch** accretion only, and rule accretion was
buying nothing it did not also cost.

### 16.1 Measured: two guards stop being necessary

| | cycle guard OFF | projection dedup OFF |
|---|---|---|
| accretion | **cycle forms** (5 taken) | **runs away** — 121 spawns, fuel exhausted |
| subset output | no cycle | **terminates on its own** — 2 spawns |

Both of §15.1's discoveries were consequences of rule accretion, not properties of the substrate. A rule's
output no longer contains its premises' predicates, so the index cannot mistake a consumer for a producer
of what it consumed. §15.1(a) — *"cycles are the assembler's DEFAULT"* — was true only of the accreting
variant; **it is no longer the default, and the guards are now belt-and-braces rather than load-bearing.**

One methodological note, because it nearly went unrecorded: testing the cycle guard alone measures
nothing, because **projection dedup was already masking the cycle.** The §15.1(a) claim is only testable
with both guards off. A guard that is never reached looks exactly like a guard that works.

### 16.2 ⭐ THE GATE — a chain expresses scope by DEACTIVATION (user, and it is the deepest of the three)

> *"A chain of rules can represent context by simply deactivating its output along the chain, because its
> input does not match. This would mean that we must NEVER bypass a node along the chain, otherwise we
> lose this natural guard."*

Correct, and it is an argument for subset output that neither the proposal nor this document had made:

- **Under accretion the guard LEAKED.** A rule that matched nothing still returned its whole view, so
  everything downstream saw the input anyway. Scope-by-deactivation was decorative.
- **Under subset output the guard is REAL.** A non-firing rule emits nothing and downstream is starved.

So a chain is a sequence of gates, silence is a semantic act, and **a bypass wire is a semantic change
rather than a shortcut** (case 7d: the bypassed consumer revives a conclusion the chain had silenced).
This retires the "skip connections for think-harder mode" idea explored earlier in the same session:
widening what a unit may see is not free compute, it is **defeating a guard**.

**The distinction that makes it operational**, since some extra wires are legitimate:

> A wire supplying a predicate **NO UNIT IN THE CHAIN PRODUCES** is a **JOIN**.
> A wire supplying a predicate **A CHAIN UNIT GATES** is a **BYPASS**, and is refused.

Both are local tests over the wiring. `Net._complete_lhs` implements exactly this.

### 16.3 The cost, and it is a real one: the assembler must now satisfy the whole LHS

Subset output broke two existing tests, and the cause is the honest price. `?x reaches ?y ∧ ?y next ?z`
needs `reaches` from the chain and `next` from base; **accretion carried `next` along, so the assembler
could wire one producer and hope.** It cannot now. `_complete_lhs` wires the remaining producers, subject
to the join/bypass test above — which is **the merge node the proposal asked for, made automatic.** A
merge is not a new construct either: it is `kind == "carrier"` at in-degree ≥ 2, the cell §2's degree
taxonomy already had and nobody had filled.

### 16.4 A LIVE DEFECT the spike found, unrelated to the proposal: the assembler was bypassing

Identical under both modes, so it was pre-existing in `units/net.py`:

> Projection dedup compares producers on **the predicates the template reads**. A context marker is by
> definition a predicate the template does NOT read. So `base` and a branch carrying `<at> t1` project
> identically, dedup skips the branch, and the rule instance is wired to `base` — **the marker never
> reaches the rule.**

This breaks relativization at ASSEMBLY rather than at representation: the value can hold the marker, and
the assembler declines to wire the chain that carries it. It is §4's emergent scope failing quietly.

**Lineage-scoped dedup was the wrong fix** (`base` and the branch are comparable — same lineage; skipping
is correct). **The fix is ordering: consider the DEEPEST producer first.** Two producers in one lineage can
project identically while the deeper one carries strictly more context, and taking the first found wires
the shallowest — which is precisely a bypass by §16.2. So *frontier-first* is a **correctness requirement**,
not the policy dial an earlier part of this session took it for.

Cost: assembly becomes O(units × upstream-walk) per pass. Accepted — the alternative is an assembler that
silently drops context. At session scale ([[ugm-scope-session-sized]]) this is expected to be nothing, and
it is the next thing to measure rather than assume ([[measure-before-optimizing-ugm]]).

### 16.5 What accretion was silently buying — and a surprise about the band

`composition_architecture.md` closes by noting that band and scope are threaded as **Python parameters**,
so a new annotation axis means editing `chain_sip`/`_facts_matching` — *"a separate, larger arc"*. On this
substrate annotations are ordinary facts, so that arc is free. But the spike found the arc was already
broken in a way accretion was hiding:

> **Under accretion the premise's band is carried forward and NEVER ATTACHED TO THE CONCLUSION.** A reader
> finds it *somewhere in the value*, by luck.

That is [[derived-facts-must-land-in-the-interpretation]] in new clothes. **Subset output does not lose
annotation inheritance; it makes an existing loss visible** — which is the third independent argument for
it. What it requires is one field: `Unit.last_firing`, recording *conclusion ↦ the premises consumed*.
`last_derived` recorded conclusions only, and once a rule emits nothing but its conclusion there is no
afterwards in which to recover the premises. Same lesson as §15.2 — **a derivation is a fact about a RUN**
— reached from the inheritance side rather than the cycle side.

With it, annotation inheritance is **one generic rule over the firing record**, not a clause per template
(which is the combinatorial explosion `form_inventory.md` §9 warns against). Measured, with the control
that matters: a premise carrying no band inherits NOTHING rather than becoming certain.

**And it does NOT solve context markers** (case 5c): a marker was never a premise, so consumed-premise
inheritance cannot carry it. That is what merge units are for (case 5d), and it is why the answer is not
a content/frame partition — which [[firmware-over-isa-design]] forbids anyway.

### 16.6 REASONED BUT NOT SPIKED — recorded so the distinction stays visible

Reached by argument in the same session, unmeasured, and therefore weaker than everything above:

- **§8's backward walk is WRONG, by this document's own §15.2.** Wires say what COULD have fed a unit, not
  what did; refire keeps only the last output; and §6b's late wiring means the topology at explanation time
  is not the topology at derivation time — so a backward walk explains a derivation that may never have
  happened. The replacement is a **parallel, forward-built, append-only network over FIRING EVENTS** (one
  unit, many firings), carried on its OWN wire — it must not accrete into the object value, or §6a's exact
  NAF starts seeing provenance facts.
- **Keep only the LAST firing per unit**, plus any firing still referenced by a kept one (reachability GC
  from current outputs), plus a small **supersession stub** at refire so *"why did you change your mind?"*
  survives. This collapses trace lifetime into unit lifetime — one question, not two (§10.3).
- **METARULES ARE NOT NEEDED.** The assembler's four decisions are all queries over the wiring history, so
  it is already a trace-consumer; and §10.4 (*"the discourse modifies the topology"*) is satisfied by
  templates alone — the discourse adds SHAPES, not wiring policy. Dropping them keeps §8's line absolute:
  **units never touch wiring.** Parked honestly: a *policy* authored mid-conversation has nowhere to land.
- **Three instantiation stages, and they are `form_inventory.md` §4d's levels**: FORM (fixed at load, L0) →
  TEMPLATE (an authored rule, L1) → UNIT (wired to producers, L2). The form set IS the index, which is
  §4d's "L0 lives in a register" satisfied structurally. **Constraint:** a firing record may name its form
  only as an OPAQUE HANDLE, or the L0 leak returns through the trace.
- **FORCE (§4b) becomes unit SHAPE, not a router** — in-degree, out-degree, and whether the unit suspends.
  ASK is a sink; `is P?` is a sink on object wires and `why P?` a sink on trace wires, which is where the
  two networks meet.
- **§6's two negations are THREE**: exact-over-the-wire, fuel-bounded-over-the-open-derivation, and
  **banded-positive-negative** (a degree cannot ride an absence). §6 currently conflates the third with
  the first, and they license different conclusions.

### 16.7 Honest scope

Networks of under ten units. No refire/revision interaction with any of this, no scale, no fuel pressure.
The inheritance rule is Python standing in for "one rule", so case 1 shows the firing record is
SUFFICIENT, not that the rule is expressible as a unit. §12's last risk — *the seduction of elegance* —
is undiminished: this section reports three simplifications and one cost, which is the same ratio every
previous section reported.

---

## 17. FAILURE POINTS — spiked against §16 rather than for it (2026-07-26)

`bench/spike_failure_points.py`, 12 checks, **2 FOUND** — and both were in constructs §16 had just landed,
which is the argument for writing a spike to break your own work rather than to demonstrate it. Promoted
to `tests/units/test_wellformed.py` (43 green).

### 17.A ⚠ A MERGE CAN RESTORE WHAT A BRANCH DROPPED — §16.5's own recommendation is a bypass

§16.5 says: wire a merge to both a rule and its branch, to re-supply context the rule no longer carries.
§5 says: a delta must be able to REMOVE, because *"under H, not P"* is most of what a hypothesis is for.
Put them together:

> The merge is wired to the branch AND to the branch's ANCESTOR. The ancestor still holds `P`. **The merge
> hands back the very fact the branch dropped.** Measured: `M output={lion has mane, lion under h}`.

This is §16.2's bypass, arriving through the construct §16 introduced to fix a different problem. It is
the sharpest instance so far of the pattern §12 warns about — a simplification that reports itself as
clean and is not.

**It needs no semantics to detect** (unlike §16.4's chain-splitting, which does): an ancestor producer
supplying facts its own descendant does not. `Net.restores_a_drop` returns the offending pair, and
`Net.wellformed()` reports it. **Not auto-refused**, because a merge wired to an ancestor is legitimate
whenever nothing was dropped — the check is on the FACTS, not on the shape.

### 17.B THE FIXPOINT (user question) — assembled nets are DAGs, and that is the whole guarantee

Termination rests on *"output unchanged"* (§7). That is a fixpoint argument **only if the network cannot
oscillate**, so the question is exact: cycle + NAF, the canonical unstable program.

- **It does not oscillate. It CONVERGES — to a different answer depending on work-list order.** `P` first
  yields `p`; `Q` first yields `q`. Silently. That is worse than oscillation, because oscillation is
  visible and this is not: it is §6's *"scheduling policy leaking into semantics"*, realized and measured.
- **The assembler never builds that shape.** It refuses back edges, so **an assembled net is a DAG, and a
  DAG has a guaranteed fixpoint.** Every oscillation risk in this substrate lives in hand-wiring.

> **⭐ THE CYCLE GUARD'S JUSTIFICATION HAS MOVED, and this matters because §16 nearly retired it.** It was
> built to contain accretion's runaway wiring (§15.1a). §16.1 removed that need and downgraded it to
> "belt-and-braces". **It must stay anyway — it is now the only thing standing between NAF and an
> order-dependent answer.** A guard whose original reason disappears is exactly the kind that gets deleted
> as dead weight.

`Net.wellformed()` reports hand-wired cycles rather than tolerating them silently.

### 17.C REFIRE WORKS — §16.7's untested axis, now tested

A gate that opens lets the conclusion through; a gate that shuts **takes it back**, by recomputation.
Nothing is retracted, nothing cascades, no `broken_assumption` stamp — §7's claim that the retraction
apparatus dissolves, measured on the gate case rather than asserted.

### 17.D IDENTITY IS SOUND BUT NOT COMPLETE — a ceiling §14 never measured

§14 measured that two DIFFERENT `mary`s refuse to join, and called binding survived. It never measured two
**coreferent** `mary`s: with `same_as` asserted, the join **still refuses**. So:

> **Id-equality is SUFFICIENT for sameness and not NECESSARY.** §14's verdict should be read as *binding
> survives UNSOUNDNESS*; completeness was never on the test list, which makes it an asymmetric probe of
> exactly the kind this repo's rule says to distrust.

**The reconciliation with §5, and it is the user's own framing:** nothing may conclude "same entity" FROM
an id. A **coref-merge unit** decides; the ids downstream merely record that decision. On this substrate
that has an unusually clean home — the merge's delta substitutes B→A, so **coref becomes a CHAIN POSITION
rather than a global fact**: downstream of it they are one, upstream they remain two. Which also answers
*"the same entity could follow different paths"* — two chains may legitimately disagree about identity,
and that is §4's "scope is a chain" applied to identity rather than a defect.

**Blocked today:** that unit needs a GENERIC substitution, which needs a predicate variable. `Triple.p` is
a plain `str`, so `?s ?p ?o` is inexpressible. The only workaround measured is authoring every rule
coref-aware (`?x same_as ?y` as an explicit atom) — a clause per template, i.e. `form_inventory.md` §9's
combinatorial explosion.

### 17.E THE PREDICATE VARIABLE — two independent requirements, one hole

Recorded together because the coincidence is the evidence:

| requirement | what it needs |
|---|---|
| entity boundaries as data (head + membership over reified facts) | facts occupying node slots |
| coref-merge as a unit (substitute B→A everywhere) | a predicate variable |

Both bottom out in the same primitive, which `ugm/` has and [[facts-as-truth-bearers-built]] calls *"the
ONE genuinely-fundamental non-sugar primitive"*, and which `units/` was deliberately built without. Two
unrelated requirements finding the same hole in two days is the clearest signal this kind of exploration
produces. **Recommended: build it** — not because either use is urgent, but because designing around it
twice is how a substrate acquires the shape of what it cannot say.

### 17.F DEFINITE DESCRIPTIONS — size was never the problem

Measured against *"the car parked at the third floor of the garage near the movie theater"*: a 6-atom
conjunctive pattern matches without strain, so **arbitrary size is not the difficulty**. What S-P-O cannot
say is the three things *"the"* claims:

| claim | measured |
|---|---|
| **uniqueness** | two cars matched; both would be derived over, silently |
| **reference failure** | empty result — **indistinguishable from negation**. Presupposition failure collapses into falsity. |
| **termhood** | a description can be USED in an LHS; it cannot be stored, passed, or referred to unresolved |

**And a description IDENTIFIES rather than CONSTITUTES.** Read constitutively, *"1 subgraph = 1 entity"*
means the car ceases to exist when it moves to the second floor. So the entity stays a node and the
subgraph is the **constraint set on it** — with an unresolved description minting a witness, which
`form_inventory.md` §9.3 already measured as NATIVE. This also dissolves the entity-boundary worry that
motivated a head node: **boundaries SHOULD overlap**, because descriptions share structure, and what is
actually lost at a merge is *which utterance contributed what* — provenance, which §16.6 already houses.

Uniqueness and reference-failure are residue-log entries for `form_inventory.md` §4a; termhood is a new
one.

### 17.G OPEN — units that fire on STABILITY or INSTABILITY (user, 2026-07-26)

Not built, and it should not be built before the trace network is, because it is the same mechanism:

- **A stability event is a fact about a RUN**, so it belongs on the TRACE wire (§16.6), and a unit that
  fires on it is an ordinary trace-consuming unit. No new construct.
- **It is what §6b's fuel-bounded NAF actually needs.** *"P is not derivable at all"* is licensed exactly
  when the network stopped growing — today that judgement lives in the Python driver, i.e. an unreachable
  island by [[composability-principle]]. A stability unit makes it sayable in-language.
- **Firing on stability DESTABILISES**, which is the whole difficulty: the unit's output changes the
  network. Requires stratification — stability at level *n* triggers units at level *n+1* — which is the
  same shape as [[stratification-both-engines]] and must be designed in, not discovered.
- **Firing on INSTABILITY is the direct answer to §17.B.** Order-dependence there is silent; a unit that
  fires on detected instability is precisely what would make it loud, and it is the honest home for
  "I keep changing my mind about this" as a reportable state rather than a hang.

---

## 18. ATOMIC CHAINS — a contextualized concept must not be split (user, 2026-07-26; NOT BUILT)

> *"When we want to represent a contextualized concept, we shall never split its chain by allowing other
> nodes to attach to intermediate outputs. But at the end of this chain, we can attach multiple chains."*
>
> *"'If tomorrow rains, get an umbrella' is an atomic chain — an `if` rule and a `get the umbrella` rule —
> and nothing can connect to the intermediate `if`, it would make no sense. While 'All men die',
> 'Socrates is a man', 'Socrates will die' are three different chains."*

§16.2 established that a bypass is a semantic change. This section is the harder half: **which wires are
bypasses.** Recorded now, built later — `units/` has no mechanism for it, and the section says why.

### 18.1 ⚠ MEASURED: the assembler splits atomic chains, and cannot be blamed

`bench/spike_failure_points.py` case E, promoted to `tests/units/test_wellformed.py`:

| | intermediate attached? | verdict |
|---|---|---|
| conditional — `base → R1(mid) → G(gate)`, second template reads `mid` | yes, `OTHER ← R1` | **WRONG** — reads a supposition as an assertion |
| syllogism — `MORTAL → ESTATE` | yes, `ESTATE#1 ← MORTAL#1` | **RIGHT** — and the rule is correctly reused for Plato |

> **The two are STRUCTURALLY IDENTICAL and semantically opposite.** No topological rule separates them.

That is the whole justification for this section existing: atomicity cannot be discovered from the wiring,
so it must arrive with the meaning. §16.4's frontier-first fix does not help — it chooses *which* producer,
not *whether* the chain may be entered at all.

### 18.2 The end-node problem, and why a purely topological answer self-undermines

The natural derivable candidate is *"attachable iff no rule unit is downstream of it"* — attach only at the
tail. It handles the conditional correctly and subsumes frontier-first as a hard rule rather than a sort
preference. **It fails on the user's own objection:**

> Attach consumer D to tail E, and now E has a downstream rule — so **E is no longer attachable for a
> second consumer.** The first attachment destroys the ability to make a second.

Topological "internal" is self-undermining. Chain identity cannot be read off the wiring.

### 18.3 Mark the CHAIN, not the node — the end is then derivable

The user's proposal was an "endnode" marker. One level up is strictly better:

> Given **which units form one atomic structure**, *internal* means **"has a gate downstream of it WITHIN
> that set"** — which is stable, because attaching an external consumer adds nothing to the set. The **end
> node is derivable**: the member with no downstream member inside the set.

One marker instead of two, no drift between them, and it survives unrolling cleanly — §15.1(b)'s new
instances land *inside* the set, so the chain grows internally and its interface does not move.

**And attaching many consumers at the end is safe for a statable reason**, which is the criterion rather
than the permission: at the end, **every consumer has inherited every gate in the chain**, so none of them
can revive what deactivation silenced. It does not matter whether the end is a rule or a merge.

### 18.4 ⭐ THE CRITERION IS FORCE — and it is already an axis

What actually differs between the two rows of 18.1: *"tomorrow rains"* inside the conditional **is not
asserted**. It is supposed. Attaching to it reads a supposition as a commitment. *"Socrates is mortal"*
**is** asserted — the system commits to it, and anything may use it.

> **A chain is atomic exactly over the span where its intermediates carry NO ASSERTORIC FORCE.**

That is `form_inventory.md` §4b, not a new declaration. It discriminates every case raised in the session:
a *derived* intermediate is assertable, so it stays attachable (which is why the syllogism must compose and
why an internal helper predicate should be reusable rather than hidden).

**CONSEQUENCE — chain identity needs no new surface:**

> **One FORM = one FORCE = one ATOMIC STRUCTURE.** The units a single form lowers to share one commitment,
> which is exactly why their intermediates are not assertable.

Umbrella: one form → one atomic chain. Syllogism: three forms → three chains. This also retires an
objection raised and dropped in the session — that form-instantiation would be too fine-grained for *"the
lion under H at t1"*, which spans several forms. It would not: a branch's output **is** assertable-under-H,
so its intermediates are legitimately attachable and it was never atomic. Nothing is named, nothing is
declared, and §4's emergence survives.

### 18.5 The tension with §4, and why it passes

§4 records that scope must stay emergent, and that this document's author re-imported it as a key three
times before getting it right. A chain boundary is a named boundary, so it deserves the test:

- §4 forbade naming context as a **key on unit identity** (`unit = (rule, context)`), which would enter
  MATCHING.
- A chain marker enters nothing but **ATTACHMENT** — assembly policy, which §8's line already assigns to
  the mechanism side, where units cannot touch it.

Different object, right side of the line. **But the first implementation should assert mechanically that
the marker never reaches `solve`** — the same shape as the no-import rule, because this is exactly the
kind of thing that is right on paper and wrong in the build.

### 18.6 The known edge, stated before it is discovered

*"Assertable"* is not always crisp. A branch carrying `<at> t1` is assertable **relative to t1** — force
and relativization interact, and 18.4 quietly assumes force is absolute. That is the seam
`form_inventory.md` §9.3 already found from the relativization side, arriving here from the force side. It
is where the first counterexample should be expected.

### 18.7 Status

**NOT BUILT.** `units/` has no notion of force — nothing in `Unit`, `Triple` or `Net` distinguishes an
asserted output from a supposed one, so 18.4's criterion is currently unimplementable and 18.1's defect
stands recorded rather than fixed. The two tests in `test_wellformed.py` pin both halves: the split (which
must eventually fail differently) and the syllogism (the negative control any fix must not break).

---

## 19. SESSION RESIDUE — reasoned in conversation, not otherwise recorded

Points raised while reasoning toward §§16–18 that belong on the record but did not earn a section. All
REASONED, none measured.

- **Grammar TYPES the network; the RUN wires it.** The strong claim — that the CNL determines the
  topology — is contradicted by §3b and §15.1: the wiring is decided at run time by index + spawn policy +
  dedup, and is not in the text. What survives is better than it sounds: forms come from the grammar and
  LHS/RHS shapes come from forms, so **which template can in principle feed which is derivable from the
  grammar** — the index could be COMPUTED rather than accumulated, making §10.5's selectivity question
  answerable before anything is built.
- **A small form set makes §10.5 WORSE, not better.** If there are ten forms, all discrimination falls on
  predicate constants and "wake broadly" gets much broader. Minimality and index selectivity pull against
  each other.
- **Why §9.3's relativization gap dissolves here, stated properly.** A binary fact plus a time index is
  4-place and S-P-O is spent. On this substrate the index is not in the fact — it is a marker fact **in the
  value** — and because a value is BOUNDED, one marker relativizes everything in it at once. That is
  impossible on a global store, where the index must ride each fact. The price is one chain per index, i.e.
  §4b's exponential wearing the frame problem's clothes.
- **Exclusivity / "only" gets a small genuine win.** `form_inventory.md` §4a lists it as *no mechanism, no
  way to say only*. A value on a wire is FINISHED (§6a), so "only these" is decidable over it — a claim
  that could not be made about an open store.
- **Entity boundaries survive exactly ONE HOP** (measured, and the reason §17.F concludes what it does):
  recoverable at a merge, because `inputs` keeps each producer's value separately; gone one hop later,
  because only the merged value flows on. Boundaries are lost precisely when subgraphs OVERLAP. The general
  form: **structure gives you boundaries for free but they do not travel; data makes them travel but needs
  reification** (§17.E).
- **`composition_architecture.md`'s actual leak is substrate-independent.** Its finding is that the
  evaluator composes and the PRODUCERS leak (hedge × negation drops at intake). §9 keeps intake unchanged,
  so that leak would recur here identically. What this substrate fixes is the arc that document DEFERRED —
  an open annotation set — not the leak it diagnosed.

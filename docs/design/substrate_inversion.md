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

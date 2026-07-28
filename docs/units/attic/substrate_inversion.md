> ## ⚠ THIS DOCUMENT IS HISTORY, NOT A REFERENCE
>
> It is the **lab notebook** for the `units` substrate: an append-only trail of what was tried, what broke, and
> what was reasoned, in the order it happened. It is kept because the trail is evidence — several decisions here
> were reversed, and knowing why matters. **It is no longer maintained, and it should not be read to find out
> how the system works.** As a reference it had become a changelog that explained each choice in terms of other
> entries in itself, with almost no worked examples.
>
> Superseded, as of 2026-07-26, by three documents with three jobs:
>
> | you want | read |
> |---|---|
> | what the system **is** | [`docs/units/model.md`](../model.md) — the old `reference.md` is deleted; its annotated form is [here](reference-annotated.md) |
> | **why** a decision was taken, and the evidence | [`decisions/`](decisions/README.md) — mostly contradicted since; each file says which |
> | what is being worked on **now** | [`docs/units/STATUS.md`](../STATUS.md) |
>
> Section numbers here (§16.6, §22.8, …) are still cited by the decision records as sources. That is the only
> role this file has now.

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
> **§20 TRACE NETWORK BUILT 2026-07-26 (60 green).** §16.6's reasoned replacement for §8's backward walk
> is measured: two wires accreting in OPPOSITE directions (object = subset, trace = append-only), the
> no-leak constraint asserted mechanically, and `why` reading what FIRED. Four findings, one of them
> sharp: **a record of a fixpoint can destroy the fixpoint** (minting), and **§4b's minimal ATMS label
> arrives free a second time** — a firing cites what it CONSUMED, not the chain it travelled. Closes the
> composability complaint: a trace fact is an ordinary fact, so §17.G is unblocked. §20.4 records the ISA
> question — in-node ISA DEFERRED (proven retrofit, cost not soundness), assembler ISA REFUSED (§8's line).
>
> **§21 CORRECTIONS (user, 2026-07-26).** ⚠ **THERE ARE NO DELTAS** — a unit is a graph REWRITE, input
> subgraph in / output subgraph out, and §16 had already made the delta language obsolete without anyone
> noticing. §5's *"the delta must be able to remove"* loses its mechanism: a rewrite that omits a fact is
> just a rewrite. Landed as `Unit.adds`/`removes`. **And three inherited principles are now a standing
> audit (§21.2): nameless data nodes (HELD, asserted by `Net.symbol_leaks`), labelled edges (HELD — and it
> DIVERGES from `ugm/attrgraph.py`'s own unlabeled-edge claim, recorded not smoothed), sparse embeddings
> (⚠ ABSENT — the real gap, and `vision.md` §13 calls the graded layer defining, not an add-on).**
>
> **§22 THE GRADED SUBSTRATE (user, 2026-07-26) — REASONED, NOT BUILT.** Banded likelihood steers ASSEMBLY
> PRIORITY (safe because §17.B makes assembled nets DAGs — order cannot change the answer, only where you
> stop; and the UNBUILT FRONTIER becomes enumerable, so *"what didn't you consider?"* rides the trace wire).
> Likelihood must also be DATA — the carrier already exists (`last_firing`, §16.5). **⚠ 22.2a: continuous
> degrees DESTROY THE FIXPOINT — §20.1(a) in a new costume — so a finite BAND LATTICE is load-bearing for
> TERMINATION, not just for honest reporting.** And **role nodes replace labelled edges** (superseding
> §21.2a): this DISSOLVES §17.E's predicate variable and retires `sym`, at the price of five
> predicate-keyed mechanisms going graded — of which **only the JOIN/BYPASS test (§16.2) is dangerous**.
> **§22.5 SPIKED IT (26/26): GO, and §17.E is DISSOLVED — `?s ?p ?o` falls out, coref-merge is ONE generic
> rule, reification is the shape `trace.py` already uses. And the five mechanisms STAY CRISP** (a role node
> is an identity), so role-nodes and similarity-matching are SEPARABLE and the dangerous half is
> deferrable. Roles must be minted by the FORM SET (interning per utterance = §3's forbidden second
> global). ⚠ New cost: a wildcard rule **consumes its own control predicate** — the trace-leak class on the
> object wire, fixed by §20's own answer (control gets its own wire), not by a new inequality primitive.
> **§22.6 LANDED IT (71 green): `Fact.p` is a node, `units/vocab.py` holds the form set's roles, and
> `value.sym` + `Net.symbol_leaks` are RETIRED — the carve-out they policed no longer exists.** The build's
> one defect was again a SILENT degradation (`why` returning None) rather than a crash, which is now three
> for three. **§22.7 BUILT BANDS (84 green): §22.2a CONFIRMED both ways — continuous 40 distinct outputs
> in 40 rounds vs banded 1 — so the finite lattice is what makes the substrate terminate; degree is DATA
> and a unit FIRES on it; inheritance is ONE computation over `last_firing`. ⭐ §22.7a: a GRADED ABSENCE
> is not ignored but INEXPRESSIBLE — `grade` asserts what it grades, so "probably not P" has nowhere to
> live. A representational gap, and §16.6 pointed at the wrong layer.**
> **⭐ §22.8 FIXED IT THE SAME DAY (user): "probably not P" = TWO NODES in the DATA subgraph — a
> graded `not` node pointing at a reified P. NEEDED NO NEW CONSTRUCT (§22.6's reification + §22.7's
> vocabulary), 94 green. Buys: units reason over denials AND their degree; P and not-P become a
> DISTRIBUTION rather than a contradiction; the gate can DENY instead of falling silent. ⚠ Price:
> `Absent` conflates *unknown* with *denied* — the NAF/strong-negation split, relocated not removed.
> ⚠ And §20.1(a)'s trap a THIRD time ⇒ STANDING RULE: ANYTHING MINTED PER RUN MUST BE KEYED.**
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

---

## 20. THE TRACE NETWORK — BUILT 2026-07-26 (`units/trace.py`, spike 40/40, suite 60 green)

§16.6 reasoned this and did not measure it, which made it the weakest thing on the record: a replacement
for §8's backward walk, argued from three failures of the walk and built out of nothing. It is now built —
`units/trace.py`, `bench/spike_trace_network.py` (40/40, stable across hash seeds), promoted to
`tests/units/test_trace.py`. **Written in §17's spirit rather than §16's**: six of the ten cases are
attempts to break it, and the four findings in §20.1 all come from those.

**THE TWO ACCRETIONS RUN IN OPPOSITE DIRECTIONS, and that is the design rather than an inconsistency:**

| wire | accretion | why |
|---|---|---|
| **OBJECT** | SUBSET output (§16) | a non-firing unit is a real gate; silence is a semantic act |
| **TRACE** | APPEND-ONLY | a firing cites the firings that produced its premises; history does not gate, it accumulates |

Which is exactly why they must be separate wires, and why §16.6's constraint — *the trace must never
accrete into the object value* — is **asserted mechanically** (`Net.trace_leaks()`), in the same spirit as
the no-import rule. The leak it prevents is precise: with provenance in the object value, §6a's `Absent`
silently changes question, from *"is P absent from the world I was handed?"* to *"was P mentioned in the
derivation?"* — two different questions wearing the same syntax.

**Shape.** A firing event is a minted node carrying `<fired_by>` (the unit's OPAQUE handle — §16.6's L0
constraint, tested), `<concluded>` (a conclusion handle described by `<subject>`/`<predicate>`/`<object>`),
and one `<from>` per premise consumed, pointing at the conclusion handle upstream produced. It is built
forward at run time from `last_firing`, pruned by reachability from the unit's current output, and read by
`explain`. **A given has no `<from>`** — so *"you told me"* is not a special case in `why`, it is §2's
in-degree taxonomy showing through the trace.

**One primitive was needed and it is small:** `value.sym(name)` — a node equal by name, `nid=0`, because a
predicate has to occupy a node slot in a firing record. **The boundary is exact and load-bearing:** `mint`
makes ENTITIES, never equal by name (§5); `sym` makes SYMBOLS from the predicate space, which `Fact.p` and
`Net`'s index already share globally. Crucially it introduces **no registry** — equality falls out of the
dataclass — because a predicate table would be the second global structure §3 forbids.

### 20.1 Four things building it found that reasoning it did not

**(a) MINTING A FIRING NODE ALMOST DESTROYED TERMINATION.** Every firing needs a fresh node; a fresh node
per RUN means the trace output differs on every run, so *"output unchanged"* — the whole of §7's
termination story — never holds and propagation cannot quiesce. **The fix is the same idempotence
condition one level down:** rebuild the trace only when the FIRING RECORD or the INCOMING TRACE changed.
Note what is compared — `last_firing`, i.e. *conclusion + premises consumed*, not the output: two runs
reaching the same conclusion from the same premises are the same derivation and must not be re-minted;
the same conclusion from different premises is a different derivation and must be. **A record of a
fixpoint can destroy the fixpoint**, and nothing in §16.6's reasoning could have surfaced that.

**(b) STUB LIFETIME IS MEASURED IN REVISIONS, NOT IN RUNS** — and the first test asserted the opposite and
failed, correctly. An idle run rebuilds nothing, so the supersession stub stays; that is right, because
*"why did you change your mind?"* stays answerable exactly as long as the mind has not changed again. What
must not happen is ACCUMULATION, and it does not: a rebuild starts from the incoming trace, so last
generation's stubs are gone and only conclusions withdrawn at THIS revision get one. §16.6's *"a small
stub"* is thus a property of the rebuild, not of a collector.

**(c) ⭐ §4b's MINIMAL LABEL ARRIVES FREE — the strongest result here.** The sibling-hypothesis test first
asserted that both explanations bottom out in `base`. They do not, and they must not: `seen_as penguin`
was derived from `is_a penguin` alone, so base is not among its premises **even though the value flowed
through it**. A firing cites what it CONSUMED, not the chain it travelled. §4b said the topology computes
the minimal ATMS label by having one instance per environment; the trace turns out to compute it a second
way, per CONCLUSION, as a side effect of recording the run. The expensive part of de Kleer's algorithm,
twice over, from two unrelated mechanisms.

**(d) EXPLANATION ORDER WAS HASH-SEED DEPENDENT.** Premises live in a frozenset, so the walk's SHAPE
varied per run — [[perf-hash-seed-sensitivity]] in a new place, found the way that lesson says it is
always found: a probe that passed and then did not. `explain` sorts; the suite runs clean under several
seeds. An explanation a user reads twice must read the same twice.

### 20.2 What it closes, and it is the composability complaint

**A trace fact is an ordinary fact, so an ordinary unit reads firing events with NO NEW CONSTRUCT** —
measured. That is the claim §17.G rests on: a stability event is a fact about a run, so a unit firing on
one is just a trace-consuming unit, and §6b's *"P is not derivable at all"* stops living in the Python
driver as an unreachable island ([[composability-principle]]). §17.G is now unblocked, and it should be
built next or not at all — a stability unit DESTABILISES, so it needs stratification designed in rather
than discovered ([[stratification-both-engines]]).

It also retires §8's backward walk as the answer to `why`, in favour of a forward record, and closes the
`why` entry in §9's *genuinely new* column.

### 20.3 Honest scope

`why P?` is a Python reader (`explain`), not yet a sink unit — §16.6 places it as a sink on trace wires,
and expressing the recursive walk as units needs unrolling, which is real work and is not done. **The
ASSEMBLER does not know about trace wires**: they follow the object topology exactly, which is right for
every case measured but is an assumption, not a result. No scale (nets under ten units), no interaction
with fuel pressure, and the supersession stub has been exercised over three revisions rather than a
session. §12's last risk stands where it always does: this section reports one primitive, four findings,
and no new mechanism, which is the same ratio every section before it reported.

### 20.4 THE ISA QUESTION — asked and answered, so it is not re-raised as an oversight

Raised by the user, 2026-07-26: should `units/` keep `ugm/`'s discipline of ISA + firmware rather than
Python — an ISA for in-node computation, and separate machinery for assembling the network? **The two
halves get opposite answers, and the second is the interesting one.**

**IN-NODE ISA — right, and safe to defer.** §2b already found the opcodes nearly intact
(`SEED`/`FOLLOW`/`TEST`/`JOIN` are *match a subgraph*, `MINT`/`EMIT` are *produce one*), and §9 lists the
lowering compiler under *survives*. But there is **no unreachable island in the in-node path today**: a
`Triple`/`Absent` LHS is already authored DATA, and `solve` is a pure function of it over a bounded value,
so nothing about a unit's semantics is hardcoded in a way a rule could not say. **The discriminator is on
the record in this very document:** §5's structural sharing was upgraded from cost to correctness because
retrofitting it would be WRONG; the ISA is the opposite case, and [[lowering-compliance-pass]] is a proven
retrofit in this repo. **Deferring risks cost, not soundness — so defer**, with the trigger written down:
the first unit that must observe or emit another unit's PROGRAM (metareasoning, §8), or the first
`SUSPEND` ([[procedures-tool-boundary]]). Until then, keep `solve` a pure function of pattern-as-data over
a bounded value, which is what makes the later lowering a compiler rather than a rewrite.

**ASSEMBLER ISA — refused, and not on grounds of cost.** §8 draws the line: flowing subgraphs are content
and units may observe them; **the assembler's choice of what to wire next is policy and units may not**.
§16.6 then dropped metarules deliberately to keep that line absolute. An assembler ISA is therefore not
deferred work, it is re-crossing a line drawn a day earlier — dynamic scoping in a new costume, exactly as
§8 predicts. **And the composability worry behind the question is real and was already recorded** (§17.G:
the fuel judgement living in the Python driver). Its answer is this section's own subject: make the
assembler **OBSERVABLE, not writable** — its decisions become firing events on the trace wire, and a unit
that reads them is ordinary. Read-only reflection closes the island while §8's line stays intact.

Parked honestly, unchanged from §16.6: a *policy* authored mid-conversation still has nowhere to land. If
that ever bites for real, reopening the assembler ISA is a deliberate crossing of §8's line — not the
correction of an oversight.

---

## 21. CORRECTIONS AND INHERITED PRINCIPLES (user, 2026-07-26)

### 21.1 ⚠ THERE ARE NO DELTAS — a unit is a graph REWRITE

> **The user's correction:** *"our doc states computation units output deltas. It's not true. Computation
> units output a rewritten subgraph, there is no 'delta' to manage."*

Correct, and the framing was already obsolete rather than merely loose. §4 said *"a fork produces several
deltas that are applied at the join points"* and §5 was titled *"deltas that can remove"* — but **§16
settled this without anyone noticing the older language had stopped applying**: a rule emits a FRESH
subgraph (what it derived), a carrier emits its REWRITTEN VIEW. **Input subgraph in, output subgraph out.
Nothing on a wire is a delta, and there is nothing to apply.**

**The consequence is a deletion, not a rename.** §5's *"the delta must be able to REMOVE and OVERRIDE, not
only add"* named a requirement that no longer needs a mechanism: a rewrite whose output does not carry an
input fact forward is just a rewrite. *"Under H, not P"* is expressible **because the output is a whole
graph**, not because a delta learned to subtract. Read §5 that way; the paragraph stands, its reason
changes, and one construct disappears.

This also puts the design where §11 already said its ancestors were — **graph rewriting** (double-pushout,
GrGen, Groove) — rather than in the delta/patch family it had been drifting toward in the prose.

**Landed in the code**, because a correction that lives only in prose is how the drift happened: `Unit`'s
fields are now `adds`/`removes` and are documented as **this unit's rewrite spec — how it computes its
view — not something that travels** (61 green). What remains genuinely a delta is nowhere.

### 21.2 THE INHERITED SUBSTRATE PRINCIPLES — and `units/` is 1½ of 3

> **The user's directive:** *"Let's not lose the good principles from ugm: nodes in the data graph must be
> nameless, edges must be labelled, and sparse embeddings are used."*

A standing constraint on this substrate, audited honestly rather than assumed:

| principle | `units/` today | |
|---|---|---|
| **nameless data nodes** | **HELD, and now asserted** | `Node.nid` is identity; `name` is a debug label that no matcher reads (`_bind` compares identity — §5). The one name-equal construct, `value.sym`, exists only for predicates in firing records, and `Net.symbol_leaks()` now refuses it in any object value. |
| **labelled edges** | **HELD — and it DIVERGES from `ugm/`, see below** | `Fact(s, p: str, o)` puts the predicate on the edge. |
| **sparse embeddings** | ⚠ **ABSENT — the real gap** | `units/` has no graded layer at all: no degrees on facts, no embedding dimensions on nodes, no α-cut, no similarity. |

**(a) The edge-label divergence is real and should not be smoothed over.** `ugm/attrgraph.py`'s own
docstring says the opposite of the directive: *"a node carries NO label and NO name… **Edges are directed
and unlabeled**. All discrimination that used to live in node-names and edge-predicates now lives in
`(attributes + directed topology)`"* — with relations reified neo-Davidsonian, the predicate living as a
graded attribute on an event node. `units/` has never worked that way: it is S-P-O with the predicate ON
the edge, which is also what [[spo-directed-path-no-labeled-edges]] preserved (that memory rejects
ROLE-labelled edges, not predicates). **So the directive matches what `units/` does and departs from what
`ugm/attrgraph.py` says it does.** Recorded as the deliberate divergence it is, and worth noting it is
also what makes §3's index cheap: a predicate on the edge is exactly what the LHS/RHS index keys on. What
`ugm/` bought with reification — n-ary facts, roles, facts-in-slots — is the same capability §17.E already
flags as the missing primitive, reached from a third direction.

**(b) Sparse embeddings are the substantive gap, and it is bigger than an add-on.** `docs/vision.md` §13
calls the graded layer *"one of the system's defining features, not an add-on"*, and
[[possibilistic-layer]] is a completed arc in `ugm/`: banded reasoning, θ dial, gradable comparatives,
defeasible guess. `units/` matches crisply and derives crisply. Three specific things are missing, and
they are separable:

1. **A degree on a fact**, and the semiring `vision.md` §13 already specifies — derived confidence =
   `(matched confidences) ⊗ (rule prior) ⊗ (embedding match degree)`. On this substrate that has an
   unusually clean home: it is exactly what `Unit.last_firing` records (§16.5 built it for band
   inheritance and then only used it for annotations), so the semiring is **one generic computation over
   the firing record**, not a clause per template.
2. **Sparse embeddings on nodes** + `recall.py`'s cosine — note `profile()` there builds a node's vector
   from its `pred:object` relations, which is *bounded local enumeration over a value* here and needs no
   global index. It may port almost unchanged.
3. **Graded matching** (α-cut / t-norm) in `solve` — the one place it touches the matcher, and therefore
   the one to design rather than bolt on.

**Not built, and deliberately not started in the same turn as the correction that revealed it.** The
honest sequencing question is whether the graded layer comes before or after §17.G (stability units), and
they are independent. Recorded as the next substantive slice.

---

## 22. THE GRADED SUBSTRATE — banded reasoning, role nodes, fuzzy matching (user, 2026-07-26; REASONED)

> **The user's three moves, and they are one move:** (1) banded likelihood must steer **which units get
> built first** — unlikely chains enumerated but not built until thinking harder; (2) likelihood must be
> **carried in the data via sparse embeddings**, or downstream units cannot reason OVER it; (3) **edges
> need no labels after all** — predicates become **role nodes characterized by embeddings**, and the
> uniformity of the data substrate is what makes graded reasoning easy.

This supersedes §21.2(a)'s labelled-edge divergence: `units/` moves TOWARD `ugm/attrgraph.py`'s
label-less, reified shape rather than away from it. All REASONED, none measured.

### 22.1 Likelihood as ASSEMBLY PRIORITY — safe, and the reason is already proved

§6 forbids scheduling policy leaking into semantics, so this deserves the objection before the agreement.
It survives, and **§17.B is why**:

> An assembled net is a **DAG**, so it has a guaranteed fixpoint. **Order of assembly therefore cannot
> change the answer — only how much of the answer you have reached when you stop.** Priority is a pure
> scheduling choice over a confluent process; the only semantic content is WHERE YOU STOP, and that is
> already `fuel.Verdict`, which refuses to collapse UNKNOWN into NO.

So this is not a new hazard, it is the existing one with a better policy attached. §4b said lazy spawn is
*"the single most important thing to preserve"* for containing the ATMS exponential; **priority-ordered
assembly is strictly stronger containment** — not merely "don't build unexplored environments" but
"explore them in order of expected payoff". §4b's cost model should be updated to say so.

**⭐ AND IT BUYS A CAPABILITY NO BLACKBOARD CAN OFFER: the unbuilt frontier is ENUMERABLE.** *"Enumerate
them but don't build them"* means the assembler holds a set of wires it COULD make and declined. That set
is a first-class answer to *"what did you not consider?"* — and it belongs on the **trace wire** (§20),
where *"why didn't you think about X?"* is answered by the same mechanism as *"why do you believe P?"*.
One network, two questions. This is the strongest argument for the proposal and it was not among the
reasons given for it.

**Two cautions, both real:**

- **NAF taken early is provisional.** A unit doing exact NAF over its wire (§6a) can fire before a
  low-priority producer is assembled. §6b already identified this shape and §7's REFIRE already fixes it —
  but priority-ordered assembly moves MANY more conclusions into the provisional class, so §6's *"the two
  negations must be MARKED DIFFERENTLY"* stops being a nicety and becomes the load-bearing part.
- **⚠ PRIORITY BY DERIVED DEGREE IS A FEEDBACK LOOP.** If the assembler reads likelihood off values, and
  likelihood is itself derived by units, then units influence assembly — indirectly, but they do. That is
  the same shape as §17.G's *"firing on stability DESTABILISES"*, and it needs the same answer:
  stratification, designed in ([[stratification-both-engines]]). It does not cross §8's line (units still
  never touch wiring) but it stands right next to it.

### 22.2 Likelihood as DATA — the carrier already exists, and the trap is the fixpoint

Right, and half of it is built. §16.5 found that **the premise's band was carried forward and never
attached to the conclusion** — a reader found it *somewhere in the value*, by luck — and built
`Unit.last_firing` (conclusion ↦ premises consumed) precisely so annotation inheritance could be **one
generic rule over the firing record** rather than a clause per template. Degree inheritance is that rule.
What is missing is the degree itself.

**Keep `vision.md` §13's two channels distinct; collapsing them loses the semiring.**

| channel | what it is | where it lives |
|---|---|---|
| **quantitative** | confidence/probability; the SEMIRING `(matched confidences) ⊗ (rule prior) ⊗ (match degree)` | computed at firing, from `last_firing` |
| **qualitative** | *likely*, *urgent*, *fairly tall* — directions in a sparse named space | embedding dimensions on nodes |

The user's *"otherwise downstream units can't reason over likeliness"* is about the SECOND: a band must be
an ordinary graded dimension so a unit matches on *likely* exactly as it matches on *tall*. That is
[[composability-principle]] applied to degree, and it is what
`composition_architecture.md` deferred as *"a separate, larger arc"* because band and scope were threaded
as **Python parameters**. On this substrate they are ordinary facts, so the arc is free — §16.5 already
banked that argument.

**Mechanism vs policy** ([[mechanism-policy-separation]]): the ⊗ at firing time is ENGINE; **which**
semiring, the priors, and which dimensions exist are DATA.

> ### ⚠ 22.2a THE FIXPOINT TRAP — and it is §20.1(a) again, in a new costume
>
> §7's termination is *"output unchanged"*. **A continuous degree that shifts by ε on re-derivation means
> the output never stops changing, and propagation never quiesces.** Two facts differing only in degree are
> different members of a frozenset, so equality — the entire termination story — silently stops holding.
> This is the exact class of bug the trace network hit when every run minted a fresh firing node: **a
> quantity that varies per run destroys the fixpoint it is recording.** It will bite, and it will look like
> a hang rather than like a wrong answer.
>
> **A FINITE BAND LATTICE is what makes it safe**, because a monotone map on a finite lattice reaches a
> fixpoint in bounded steps. So [[possibilistic-layer]]'s choice of BANDS over continuous degrees should
> now be read as **load-bearing for TERMINATION**, not merely as honest reporting — which is a stronger
> justification than that arc originally had. Continuous embeddings stay safe only where they do NOT
> participate in the value compared for change: minted-with-the-node is fine, derived-per-run is not.

### 22.3 Role nodes — the cost is five mechanisms, and the payoff is a primitive DISSOLVED

Accepted, and it is a bigger win than the argument given for it.

**⭐ IT DISSOLVES §17.E's PREDICATE VARIABLE — the hole hit three times independently.** If a predicate is
a NODE, then `?s ?p ?o` needs no new primitive: `?p` is an ordinary node variable. Coref-merge as a unit
(§17.D) and entity boundaries as data (§17.E) both become expressible, and `form_inventory.md` §9's
combinatorial explosion — a coref-aware clause per template — is avoided. §17.E recommended BUILDING that
primitive; **this proposal removes the need for it instead**, which is the better outcome and was not
among the reasons offered.

**It also retires `value.sym` and §21.2's guard.** The `nid=0` name-equal symbol existed only because a
predicate had to occupy a node slot in a firing record. With role nodes there is no exception to guard:
the data graph is nameless *uniformly*, and `Net.symbol_leaks()` becomes vacuous rather than necessary.
Three constructs removed by one change is the shape of a correct simplification rather than a clever one.

**THE PRICE, stated precisely: five mechanisms key on PREDICATE IDENTITY and every one becomes graded.**

| # | mechanism | today | under role nodes |
|---|---|---|---|
| 1 | `Subgraph.by_pred` — the bounded local index | dict lookup | similarity over role embeddings |
| 2 | `Net.lhs_index` / `rhs_index` — the ONE global structure (§3) | keyed by predicate string | an α-cut over role similarity |
| 3 | projection dedup (§15.1c) — *the predicates the template READS* | set intersection | graded projection |
| 4 | `_complete_lhs`'s `need` / `supplied` | set difference | graded satisfaction |
| 5 | **the JOIN/BYPASS test (§16.2)** | *does a chain unit GATE this predicate?* | **a graded semantic guard** |

> **⚠ THIS TABLE IS CORRECTED BY §22.5, which measured it.** All five stay CRISP when predicates become
> nodes, because a role node is an IDENTITY. They go graded only when SIMILARITY MATCHING arrives — a
> separate, later decision. Read the right-hand column as *"under similarity matching"*, not *"under role
> nodes"*. The distinction is the difference between one free change and one dangerous one.

Rows 1–4 are fine and arguably better: §3.1 already demands the index be **a cheap NECESSARY CONDITION,
never exact** — *wake broadly, fire narrowly* — and a cosine threshold is exactly that. §10.5 asked
whether predicate-level keys stay selective under real grammar; this replaces that question with a
measurable one (what α?), which is progress, and §19's *"a small form set makes selectivity WORSE"* now
has a dial rather than a wall.

**Row 5 is the sharp risk and should not be waved through.** §16.2 established that a bypass is a
**semantic change**, not a shortcut — the whole of scope-by-deactivation rests on it. Making that test
graded means *"is this a bypass?"* becomes a matter of degree, and a guard that is 0.6 sure it is being
defeated is not obviously a guard. **This is the one place where the uniformity argument may cost more
than it pays**, and it should be measured before it is adopted, not after.

### 22.4 Why the three are ONE move, and the sequencing that follows

They are not three features. **Role nodes make the substrate uniformly graded; a uniformly graded
substrate is what lets a band be ordinary data; and a band as ordinary data is what an assembler can read
to prioritise.** Do them in the other order and each one needs a special case: band as a Python parameter
(what `composition_architecture.md` is stuck with), priority as a privileged channel, similarity as an
exception in the index. **The user's *"uniformity makes it easier"* is the load-bearing claim, not a
motivation for it.**

Proposed order, cheapest-decisive first:

1. **Spike the predicate-as-node dissolution** (§22.3) — ~30 lines, a yes/no, and it unblocks §17.D/E.
   If `?s ?p ?o` does not fall out, the rest of this section is built on sand.
2. **Bands as a finite lattice + degree inheritance over `last_firing`** (§22.2) — with 22.2a's
   termination check as the FIRST test written, not the last.
3. **Sparse embeddings + graded matching** (§21.2b) — α-cut in `solve`, `ugm/recall.py`'s cosine ported.
4. **Graded index + assembly priority** (§22.1, §22.3 rows 1–4), with the unbuilt frontier on the trace
   wire — and **row 5 measured separately** before the bypass test is allowed to go graded.

**Honest status: §§22.1–22.4 are REASONED, and §22.5 is the first of them measured**, which by this
document's own standard leaves the rest the weakest material in the file — the same standing §16.6 had
before §20 tested it and found four things the reasoning had missed. The ratio held: see below.

### 22.5 SPIKED 2026-07-26 — predicate-as-node (`bench/spike_predicate_as_node.py`, 26/26)

§22.4's step 1, run first because if `?s ?p ?o` did not fall out the rest of §22 was built on sand. A
standalone model: **`units/match.solve` with the special case for `p` DELETED**, and nothing else changed.

**VERDICT: GO — and §17.E is DISSOLVED rather than deferred.**

| | measured |
|---|---|
| `?s ?p ?o` expressible | **yes** — `?p` is an ordinary node variable; safety is the SAME rule (an unbound head predicate is still refused, by the check that already exists) |
| coref-merge as one generic unit (§17.D) | **yes** — subject and object substitution, two atoms each, no clause per template |
| facts in node slots (§17.E) | **yes** — and it is **the same shape `units/trace.py` already uses** for a conclusion handle (`describe`: subject/predicate/object over a minted handle) |

That last row is the third independent arrival at one construct: the trace network built reification
without calling it that, and §17.E's *"entity boundaries as data"* needs exactly it.

**⭐ CORRECTION TO §22.3 — the two changes are SEPARABLE, and the dangerous one is DEFERRABLE.** §22.3
assumed all five predicate-keyed mechanisms go graded the moment predicates become nodes. **They do not.**
A role node is an IDENTITY, so `by_pred` still indexes crisply (measured: 50 candidates from 100 facts),
and the join/bypass test is still a crisp set operation over node identities. **The five mechanisms go
graded only when SIMILARITY MATCHING arrives — which is a later and separate decision.** So §22.3's one
real risk (row 5: a graded *semantic* guard) does not have to be taken to get §17.E's payoff, and it
should not be. The two halves of the user's edge proposal are independent, and this one is free.

**⭐ ROLE IDENTITY MUST COME FROM THE FORM SET.** Two independently minted `likes` nodes do not match —
namelessness applied to roles, exactly as §21.2 requires of entities. So roles cannot be interned per
utterance: **a registry keyed on the surface word would be §3's forbidden second global structure.** Roles
are minted by the FORM SET at load (§16.6's L0), and templates reference them. Which locates the job for
embeddings far more precisely than §22 did: **not "everything becomes graded", but "a NOVEL role must be
related to the roles the form set already has"**. That is the whole of it, and it is a much smaller claim.

**⚠ THE NEW COST, and it is the trace-leak class arriving on the object wire.** A `?s ?p ?o` rule has no
predicate to key on, so it matched the very `same_as` fact that LICENSES it and derived a reflexive
`mary same_as mary` from nothing. Generalised:

> **A generic rule cannot tell the object language from the control vocabulary that drives it.**

Two fixes, and the choice matters. An inequality guard (`?p != same_as`) works — measured — but is **a new
primitive the substrate does not have**, and it puts the control vocabulary into every generic rule by
hand. **The other fix is the one §20 already built and justified: put control on its OWN WIRE.** That is
the same argument as `Net.trace_leaks()` — provenance on the object wire makes `Absent` change question;
control vocabulary on the object wire makes a wildcard rule consume its own licence. One mechanism, two
uses, and the second is evidence the first was not a special case.

**Two smaller findings, both about the wildcard:**

- **It defeats the index** (measured: a `?s ?p ?o` rule binds *everything*). §10.5's selectivity question,
  made concrete and uncomfortable: **the generic rule that avoids `form_inventory.md` §9's combinatorial
  explosion is the same rule that makes "wake broadly" mean "wake always".** Those pull against each other
  exactly as §19 said minimality and selectivity do.
- **It can trip §17.A from any producer.** A wildcard consumer wired to both a branch and its ancestor
  re-supplies whatever the branch dropped, for every predicate at once. `restores_a_drop` and
  `wellformed()` therefore become MORE load-bearing under predicate variables, not less.

**Revised order for the rest of §22**, given the above: take predicate-as-node NOW (it is free, and it
dissolves a recorded blocker), keep the index crisp, and treat similarity matching as a separate arc whose
first job is novel-role relating rather than a wholesale move to fuzzy matching.

### 22.6 LANDED 2026-07-26 — `Fact.p` is a node (`units/vocab.py`, 71 green)

Promoted to `tests/units/test_roles.py`. `ugm/` untouched, no-import rule intact.

| | |
|---|---|
| **new** | `units/vocab.py` — `Vocabulary`, the roles ONE FORM SET supplies. A `str` in a predicate slot resolves through it at construction, so call sites read unchanged. |
| **retired** | `value.sym` and `Net.symbol_leaks` — **both existed only because a predicate needed a node slot in a firing record.** With roles as real nodes, namelessness (§21.2) is UNIFORM and there is no carve-out left to police. |
| **uniform** | `Triple`'s three slots, `_bind`, `ground`, `matched`, `_holds` — each lost its predicate special case rather than gaining a branch. The diff is a DELETION. |
| **explicit** | a variable role contributes NO index key, in `spawn`, `need` and `gated` alike. The wildcard's cost is visible in the code, not hidden by a default. |

**The discipline `vocab.py` exists to state**, since a `Vocabulary` looks like the registry §22.5 forbids:
**a FORM may mint a role; an UTTERANCE may not.** Interning surface words at intake would fuse two
utterances of *"likes"* by name — the abolished label, returning through the one door left open. There is
no intake here yet, so the rule is documented and not yet assertable; it is the first thing to make
mechanical when intake arrives.

**⚠ ONE DEFECT IN THE BUILD, and it is this file's recurring shape.** The trace vocabulary was left as
strings while `Fact.p` became a node, so `prune` compared a node against a string constant, matched
nothing, and kept nothing — and `why` **silently returned None** rather than failing. Same class as
§15.2's subtraction-based `derived` and §20.1(a)'s minting trap: **the failure mode of this substrate is
consistently a quiet degradation, never a crash.** The fix was to make the trace vocabulary role nodes
outright, which is also what makes a trace fact ordinary (§20.2).

**What did NOT change, and it is the point of §22.5's correction:** the index, projection dedup,
`_complete_lhs`, and §16.2's join/bypass test are all still crisp identity tests. Similarity matching
remains unbuilt and unneeded so far.

### 22.7 BANDS — BUILT 2026-07-26 (`units/band.py`, spike 25/25, suite 84 green)

§22.4's step 2, with **the termination check written first** rather than last, because §22.2a predicted a
failure that presents as a hang. Promoted to `tests/units/test_bands.py`.

**§22.2a IS CONFIRMED, and measured BOTH WAYS so it is evidence rather than argument.** The continuous
version was built and run: 40 distinct outputs in 40 rounds — every re-derivation a new value, so
*"output unchanged"* never holds and propagation could never quiesce. The banded version: **1 distinct
output**, and the bound is the lattice HEIGHT, so it is knowable in advance. `meet` is min, and its three
properties are load-bearing for termination rather than for elegance — commutative (premise order must
not matter), associative (grouping must not matter), **idempotent** (re-derivation produces an identical
value and therefore stops).

So [[possibilistic-layer]]'s bands, and `ugm/possibility.py`'s scale and min-join, are **inherited rather
than invented** — and they now rest on a stronger justification than that arc had.

**Degree is DATA, which was the user's actual requirement.** A band is an ordinary role node; a graded
fact is reified and carries `<band>`; a downstream unit **fires on a band** with no new construct
(measured, both positively and negatively). `composition_architecture.md`'s deferred arc — band threaded
as a Python parameter, so a new annotation axis means editing the evaluator — does not exist here.

**Inheritance is ONE generic computation over `last_firing`.** §16.5 built that record for exactly this
and then used only a Python stand-in; `band.inherit` is the real thing, and it knows nothing about any
template. §16.5's control holds: **an unbanded premise inherits NOTHING and does not become `certain`** —
absence of a degree is not a degree. A two-premise conclusion takes the weaker band.

Two honest limits:

- **`inherit` is still Python, and for a stated reason:** it MINTS a handle per graded conclusion, and
  this substrate refuses RHS-only variables ([[skolem-minting-lhs-keyed]]), so a rule cannot mint. That
  is the remaining obstacle to it being a unit — not the predicate variable, which §22.6 supplied.
- **The object wire needed its OWN reification vocabulary** (`<of_s>/<of_p>/<of_o>`), because reusing the
  trace's identical-looking `<subject>/<predicate>/<object>` trips `Net.trace_leaks()`. The guard working
  as intended, and incidental evidence that §20's separation was not a special case.

> ### ⭐ 22.7a A GRADED ABSENCE IS NOT IGNORED — IT IS INEXPRESSIBLE
>
> §16.6 predicted a THIRD negation: *banded-positive-negative — a degree cannot ride an absence*. The
> spike set out to measure that `inherit` grades by positive premises only and quietly ignores the absent
> atom's confidence. **It failed the way it was expected to pass, which is the useful outcome.**
>
> **`grade` ASSERTS the fact it grades.** Attaching a band to `P` puts `P` in the value, so the `Absent`
> atom stops holding and **the rule stops firing entirely**. Measured.
>
> So *"probably not P"* has nowhere to live: grade `P` and `P` becomes true; say nothing and `P` is
> certainly absent. There is no third state. **This is a REPRESENTATIONAL gap, not an inheritance one —
> `inherit` was never the place to fix it**, and §16.6's framing pointed at the wrong layer. It is the
> same shape as §17.F's *reference failure is indistinguishable from negation*: this substrate has one
> way of not containing something, and it is being asked to carry two meanings.
>
> Recorded as a live limitation. **⭐ FIXED THE SAME DAY by §22.8, and neither candidate fix above was
> the answer.**

### 22.8 EXPLICIT NEGATION — *"probably not P"* in the data subgraph (user, BUILT 2026-07-26)

> **The user's proposal:** *"Can't we express 'probably not P' as two nodes — `not` with a 'probably'
> grade, then node P? Note we are now talking about the DATA subgraph, not the computation units."*

Yes. `bench/spike_explicit_negation.py` (22/22), landed as `units/negation.py` + `units/reify.py`,
promoted to `tests/units/test_negation.py`, **94 green**.

**It needed NO new construct**, which is the striking part. §22.6 made a fact able to occupy a node slot;
§22.7 built the reification vocabulary to attach a band. A denial is a node pointing at that same handle.
**Talking ABOUT a fact and CLAIMING it finally come apart** — and that separation is the entire fix, so
`reify.py` now exists as its own module because two unrelated requirements arrived at it. §17.E predicted
that signal; this is its fourth occurrence.

**The state space, which is what actually changed:**

| value contains | means |
|---|---|
| `P` | P holds |
| P absent, no denial | nothing is known about P |
| P absent, denial at band *b* | **P is believed false, to degree *b*** — the state that did not exist |

**⚠ THE PRICE: §6a's `Absent` cannot tell the last two apart** (measured). This is the classical
negation-as-failure vs strong-negation split, and the honest statement is that the proposal **RELOCATES
the ambiguity rather than removing it**. `Absent(P)` stays a syntactic test over the value; a rule meaning
*"actively denied"* must ASK for the denial. That is bounded — an ordinary pattern, no new atom kind, no
second matcher — but **the rule author now has to choose which negation is meant**, and nothing checks
that they chose right. That is the real cost of the proposal and it should not be discovered later.

**Three things it buys beyond the fix:**

- **A unit reasons over a denial AND over how sure it is** — measured firing on *probably-denied* and
  correctly not firing on *certainly-denied*. §22.7 did this for degree; this does it for negation, and
  the user's standing requirement is now satisfied on both axes.
- **⭐ `P` and `not P` in one value are not a contradiction but a DISTRIBUTION.** A set could never
  represent this before. With bands it is competing degrees — [[possibilistic-layer]]'s ranked hypotheses
  arriving for free. **The honest half: nothing reconciles them.** A rule asking for `P` fires and ignores
  the denial entirely. A RECONCILIATION unit is what is missing, and it does not exist.
- **§16.2's gate gets sharper**: a unit can EMIT A DENIAL instead of falling silent, so *"I have nothing"*
  and *"I deny"* stop being the same act. Under subset output that was one act; now it is two.

**⚠ AND §20.1(a)'S TRAP FOR THE THIRD TIME.** `deny` mints a `not` node, so two denials of one fact are
different values and a re-derived denial never converges. Asserted denials are safe; a DERIVED one must
pass `key=`. After the trace's firing nodes and the band's handles, the pattern is firm enough to state as
a standing rule:

> **Anything minted per run must be KEYED, or it destroys the fixpoint it is annotating.**

---

## 23. THE PYTHON SEAMS — audited, and one of them is a keystone (user, 2026-07-26)

> **The user's question:** *"You started implementing things in Python that might be computation in the
> substrate. Shall we fix it before we start creating a stack of seams that will be difficult to sanitize
> later?"*

Right to ask, and the audit says it is **three seams, not a stack** — which changes the answer.

| Python | verdict |
|---|---|
| `match.solve`, `Unit.run`, `Net.assemble/propagate`, `band.meet` | **MECHANISM.** The evaluator, the assembler (§20.4 refused making it substrate, deliberately), and the semiring's ⊗ (`vision.md` §13 assigns it to the engine). Not seams. |
| `trace.firing_facts`, `prune`, `supersession_stub` | **BRIDGES.** A run event becoming facts is exactly the *"minimal event→fact bridge"* [[composability-principle]] permits as irreducible. |
| `band.band_of`, `negation.denial_of/denied`, `reify.handle_for/fact_of` | **READS**, each a pattern a rule could express. Harmless as helpers — they become seams only if reasoning depends on them, which is the next row. |
| **`band.inherit`** | ⚠ **SEAM.** Degree propagation IS reasoning, and §16.5 designed it as *one generic rule*. |
| **`trace.explain`** | ⚠ **SEAM.** §16.6 places `why` as a SINK UNIT; it is a Python walk (already recorded, §20.3). |
| **`vocab.FORMS`** | ⚠ **SEAM-IN-WAITING.** A module-level registry that resolves any string. It is only not §22.5's forbidden interning registry because nothing calls it from an utterance — and nothing calls it from an utterance because there is no intake. |

### 23.1 BUILT — `match.Mint`, keyed skolem minting

Three separate things were blocked on the same missing primitive, which is the argument for building it:
`band.inherit` mints a handle per graded conclusion; a DERIVED denial mints a `not` node (§22.8); the
trace's firing nodes hit it first (§20.1a) and were fixed by hand. **`Mint` makes §22.8's standing rule a
CONSTRUCT rather than a discipline** — the node is a function of (unit, head position, binding), so
re-running on the same match yields the same node and the output settles. An RHS-only `Var` stays refused;
a `Mint` is not a variable, it names a function of the binding ([[skolem-minting-lhs-keyed]]'s supported
form). Memo is the unit's own state, never global.

### 23.2 ⭐ §20's LEAK GUARD WAS DRAWN ONE PREDICATE TOO WIDE — corrected

Trying to close the `inherit` seam hit a wall that turned out to be a real defect. The trace described a
conclusion with a private `<subject>/<predicate>/<object>`; `reify.py` describes a graded fact with
`<of_s>/<of_p>/<of_o>`. **Two vocabularies for one construct, forced apart by `trace_leaks()`** — and that
split is precisely what made inheritance unexpressible as a rule: a premise's band hangs off a REIFY
handle while a firing's `<from>` points at a TRACE handle, denoting the same fact without being joinable.

> **The correction is to the GUARD, not a workaround. Saying WHICH FACT a handle denotes is CONTENT; only
> *"firing F concluded c"* and *"F came from c'"* are provenance.** So `is_trace` now tests the FIRING
> vocabulary alone, and the description is shared with the object wire.

§16.6's constraint is unchanged in force — §6a's `Absent` must still never see a derivation fact. It was
simply over-drawn, and a test that pinned the old claim (`test_the_object_wire_needs_its_own_reification_
vocabulary`) has been rewritten to state the new one.

### 23.3 ⚠ AND THE SEAM STILL DOES NOT CLOSE — which is the useful result

Sharing the vocabulary was necessary and **not sufficient**. Measured: the object-wire handle for a
premise and the trace-wire handle for the same premise are **different nodes**. The description is now
joinable in principle and the handles still are not.

Closing it means **one handle per fact per value** — the trace reifying its conclusions into the OBJECT
value so a band and a firing can name the same node. That is not a bug fix; it is a decision with a real
cost: *every* conclusion becomes reified, whether or not anything grades it, which is the opposite of
§22.7's *"paid for only where used"*.

**So the honest answer to the user's question is: fix the seams, but not first.** Two of the three
(`inherit`'s handle unification, `FORMS`) bottom out in a representation decision that **intake also
makes** — what gets reified, and who may mint a role. Settling them before the discourse path exists means
settling them twice. `Mint` and §23.2 were worth doing now because they are unconditional; the rest is
recorded debt with a named blocker, which is the difference between debt and a mess.

### 23.4 WHERE EXPLANATION LIVES — the record is eager, the narrative is lazy (user, 2026-07-26)

> **The user's question:** *"Could we translate `explain` to growing a parallel chain that points to
> computation units, when the request of explaining arises? Shall we bake explainability into the DATA
> produced by the unit, or as units that point to other units to produce an explanation subgraph? Or units
> that attach to intermediate outputs to build the trace in a parallel subgraph?"*

Three options, and **they are not alternatives — they split along a line the existing measurements already
force.** Probed directly rather than argued:

| probe | result |
|---|---|
| can ONE ordinary rule take an explanation hop over the trace? | **yes, today** — `(?f <concluded> ?c, ?f <from> ?p) ⇒ (?c <because> ?p)` derived 3 steps |
| can a rule say WHAT a step is about? | **yes — and only since §23.2** shared the description vocabulary. That correction was made an hour earlier for an unrelated reason (band inheritance) and turns out to be what unblocks this |
| can a unit DOWNSTREAM of a producer reconstruct that producer's firing? | **NO.** A consumer of `R1` sees `{a r b}` and nothing else; the premises consumed are engine state on no wire |

**⭐ THE THIRD ROW DECIDES THE ARCHITECTURE.** Subset output (§16) means a downstream unit sees only the
conclusion, so a trace-building unit tapping intermediate outputs **cannot know which premises were
consumed** — it would have to re-derive the match, and could recover a DIFFERENT binding that yields the
same conclusion. It would be guessing, and guessing that reads as provenance. Add §16.6's three reasons a
demand-time reconstruction fails (refire keeps only the last output; late wiring changes the topology; a
unit that woke and correctly wrote nothing looks like one that fired) and the rule is:

> **The RECORD must be EAGER and must come from the unit itself. The NARRATIVE can be LAZY and should be
> units.** You cannot defer the recording; you can defer the explaining.

So option (a) stays, minimally — a firing record is the smallest possible bridge (conclusion handle,
premise handles, opaque unit handle) and §20's `prune` already bounds it. Options (b) and (c) are the same
thing and they are the right shape for everything ABOVE that record: the walk, the narrative, *"why did
you change your mind"*, §17.G's stability units. **The user's phrase — a parallel chain that points to
computation units — is exactly right for that layer**, and §15.1(b)'s unrolling is the mechanism: one
instance per hop, growing backward along `<from>` until it reaches a firing with none (a given).

**What that buys, and the first item is the strongest thing in this section:**

- **EXPLANATION DEPTH BECOMES ASSEMBLY DEPTH, WHICH IS FUEL.** *"Explain more"* stops being a different
  operation from *"think more"* — it is the same operation (§8's claim that the metaphor and the mechanism
  are one thing, finally realized rather than asserted). Today `explain(depth=8)` **silently truncates**,
  which is this session's recurring failure mode a fourth time; as units it is an honest `UNKNOWN`.
- **It closes a §23 seam without touching the blocked decision.** `trace.explain` becomes units;
  `band.inherit` cannot yet, because it needs the handle unification §23.3 parks. **Of the three seams,
  this one is now cheap and unblocked** — which is a real difference, not a preference.
- **An explanation becomes a subgraph a unit can reason OVER** — metareasoning, which §8 said to reopen
  deliberately on this substrate.

**One constraint, from §23.2's own principle:** *"P was derived from Q"* is a derivation fact, so the
explanation chain rides the **TRACE wire**, not the object wire. Put it on the object wire and §6a's
`Absent` starts seeing explanations — the leak §20 exists to prevent, re-entering through the door §23.2
just narrowed.

---

## 24. DISCOURSE → NETWORK — the survey before the build (user, 2026-07-26)

> *"A perfect computation model that we can't build from discourse and KB is useless."* — and §10.4 has
> always agreed: *"where the discourse's own rules enter"* is named there as **the central claim and the
> least specified part**. §15.3's honest scope still stands: no intake, no CNL, no query surface.

Deliberately a SURVEY, not a plan. The point is to find what will matter — including what bites THIS
substrate rather than intake in general — before committing to a shape.

### 24.1 What `units/` actually lacks, which is more than "intake"

Three constructors exist: `given`, `rule`, `branch`. That is the whole inventory.

| absent | why it is structural, not cosmetic |
|---|---|
| **FORCE** | §16.6 concluded *force is unit SHAPE, not a router* — and §18.7 records that nothing in `Unit`, `Triple` or `Net` distinguishes an asserted output from a supposed one. So §18's atomic chains are unimplementable, and intake has nothing to map onto. |
| **A SINK** | §2's taxonomy has *"query = a sink whose output is the answer"* and nothing implements it. `Net.why` is a Python reader (§23.4). |
| **SUSPEND** | No continuation machinery of any kind. [[procedures-tool-boundary]] needs it, and §20.4 named *"the first SUSPEND"* as a trigger to build the in-node ISA. |

### 24.2 Force → topology, and the mapping is more interesting than a switch

Each force is a **different act on the network**, which is §16.6's claim made concrete:

| force | the act |
|---|---|
| ASSERT | spawn a `given` (in-degree 0) |
| AUTHOR a rule | `declare` a TEMPLATE — **the library, not a unit.** Nothing is instantiated until a producer arrives (§3, lazy spawn) |
| ASK | spawn a SINK on the object wire; `why` a sink on the trace wire (§16.6: where the two networks meet) |
| SUPPOSE | spawn a `branch` — already supported, and the most natural fit in the inventory |
| COMMAND / act | a unit that SUSPENDS (§24.4) |
| **RETRACT** | ⭐ **delete the `given` unit.** Not a data operation at all — downstream simply recomputes (§7). The retraction apparatus dissolved once; here retraction stops being an operation on facts and becomes an operation on TOPOLOGY. |

That last row is the cleanest thing in this section and it was not designed — it falls out.

### 24.3 ⭐ DISCOURSE REFERENCE IS NOT LOOKUP, and this is the deep one

*"The lion"* in the second sentence must reach the same node as the first. On a store you look it up by
name. **Here you may not:** §21.2 makes entities nameless, and §22.5 rules that interning a surface word
into a node is §3's forbidden second global structure — it would fuse two utterances *by name*, which is
the abolished label returning through intake.

So discourse reference must be **decided, not resolved**: intake mints a FRESH node per mention, and a
**coref-merge unit** (§17.D) decides which mentions are the same entity. That was blocked until §22.6 gave
predicate variables, and is now expressible — *"coref becomes a CHAIN POSITION rather than a global fact:
downstream of the merge they are one, upstream they remain two"*, which also means two chains may
legitimately disagree about identity.

**This is the single largest piece of new design**, it is [[coref-stays-cnl-not-engine]] and
[[demand-coref-perf-wall]] arriving on a substrate that makes the wrong answer unrepresentable rather than
merely discouraged, and §17.F's definite descriptions are the same problem wearing a determiner.

### 24.4 PROCEDURES — the user's example, and it forces two deferred decisions

*"A series of steps"* is the sharpest test, because **a dataflow network has no notion of "next".** Order
comes only from data dependency, so if step 2 does not consume step 1's output, nothing sequences them.
Three shapes, and the choice is real:

| shape | consequence |
|---|---|
| **(i) a CHAIN of step units**, intake manufacturing the dependency (each step consumes the previous one's output) | keeps every step traceable (§20), gated (§16.2), and individually refirable. Most units-native. |
| **(ii) ONE unit with an internal PROGRAM** | this is [[machine-semantics-are-isa-programs]] and §20.4's deferred in-node ISA. Handles sequencing and suspend natively — and makes the procedure OPAQUE: no per-step trace, no per-step gate. |
| (iii) steps as units + a scheduler | reintroduces a control plane the substrate deleted. |

**⭐ Two convergences make (i) look right, and both were reached for other reasons:**

- **§18.4's force criterion predicts procedure atomicity.** It was written for conditionals — *a chain is
  atomic exactly over the span where its intermediates carry NO ASSERTORIC FORCE*. A step of a procedure
  is a COMMAND, not an assertion, so its intermediates are not assertable and the chain is atomic. *"One
  FORM = one FORCE = one ATOMIC STRUCTURE"* covers `to make tea: …` with nothing added.
- **`match.Mint` (§23.1) is what threads the state token** — the manufactured dependency must be keyed on
  the procedure instance, or every run re-mints it and the fixpoint dies.

**But (i) does not dodge SUSPEND.** A step that touches the world must suspend, and the unit that suspends
is a step unit either way. So **procedures are the trigger event §20.4 named** — the in-node ISA question
reopens here, on schedule, for the stated reason rather than as drift.

### 24.5 The constraints intake will have to honour, gathered

- **IDEMPOTENCY.** [[extend-equals-rebuild]]: saying the same thing twice must not double the network.
  `Net.spawn` refuses duplicate unit names, and §23.1's `Mint` keys minted nodes — so **the key is the
  UTTERANCE**, and intake must supply one. Concrete, and cheap if designed in.
- **⭐ `define` IS THE LICENSED MINTING SITE.** §22.5's line — *a form may mint a role, an utterance may
  not* — is currently a docstring `vocab.py` cannot enforce. Form-authoring ([[forms-as-kb-data]]'s
  `form KEY : HEAD when BODY`, [[meaning-surfaces-audit]]'s `define`) is exactly where minting is allowed,
  which makes the rule operational instead of aspirational **and makes `vocab.FORMS` stop being §23's
  seam-in-waiting.**
- **REFUSAL IS FIRST-CLASS.** [[book-corpus-experiment]]: partial intake systematically drops exceptions,
  so learning goes optimistically biased. [[epistemic-closure-under-composition]]: reasoned ∪ refused,
  never silently mis-mapped. On this substrate a refusal can be a UNIT — *"I could not represent this"* as
  an ordinary fact that other units can see, which no store-based intake could offer.
- **THE INDEX COULD BE COMPUTED, NOT ACCUMULATED** (§19). Forms arrive at load and LHS/RHS shapes come
  from forms, so which template can in principle feed which is derivable from the form set. That answers
  §10.5's selectivity question BEFORE anything runs — worth doing while the form set is being built,
  because retrofitting it later means the index has already been accumulated.
- **THE PRODUCER LEAK RECURS UNCHANGED** (§19). `composition_architecture.md`'s finding is that the
  evaluator composes and the PRODUCERS leak (hedge × negation dropped at intake). §9 keeps intake
  unchanged, so it would recur here — except that §22.7 and §22.8 now make band and denial ordinary data,
  so intake has somewhere to put them. **The fix is available for the first time; it still has to be taken.**

### 24.6 What is genuinely new versus what is already answered

**Already answered, and should not be re-litigated:** CNL in with an LLM translating prose, not a prose
parser ([[minimum-form-set]], [[raw-prose-0-of-50]] — verbatim prose measured at 0/50, the gap 100%
constructional). Force as an axis. Forms as KB data. The tool boundary.

**Genuinely new on this substrate:** force as unit SHAPE; retract as topology; **discourse reference
without lookup** (§24.3, the big one); procedure sequencing without a scheduler (§24.4); and the sink,
which is the smallest of them and the natural first probe — an ASK is a unit with in-degree ≥1 whose
output is the answer, and building it exercises force, wiring and `Verdict` at once without committing to
any of the above.

### 24.7 ⭐ CLOSURE — and it decides the architecture BEFORE the grammar (user, BUILT 2026-07-26)

> **The user's observation:** *"The OUTPUT of the system should be usable to create more network wirings,
> because the discourse could lead to new rules. So either we convert subgraphs (output) to CNL and then
> ingest it back, or we also need a transpiler from output graph to network."*

`units/authoring.py`, `bench/spike_closure.py` (26/26), `tests/units/test_closure.py`, **105 green.**

**THE CNL ROUND-TRIP IS NOT MERELY EXPENSIVE — IT IS UNSOUND HERE.** Rendering a subgraph to text means
NAMING its nodes; re-ingesting means RESOLVING those names. That is exactly §22.5's forbidden
interning-by-name and §24.3's *"discourse reference is not lookup"* — two independently minted `mary`s
would fuse, and §5 records identity inheritance as a CORRECTNESS requirement rather than a cost. **Text is
a lossy channel for identity, so the loop must not pass through it.**

So the answer is the second option — and the important part is that **it is not a SECOND transpiler, it is
the ONLY one:**

    CNL text ──parse──▶ rule-shaped SUBGRAPH ──declare──▶ template in the library
    a unit's output ─────────────────────────▶ (same path from here)

> **⭐ THE DECISION, and this is why it had to be taken before a grammar exists: THE CNL FRONT-END MUST
> TARGET A SUBGRAPH, NEVER THE `Net` API.** Target `Net` directly and output→network needs a second
> implementation; the two drift; and **the system becomes able to SAY things it cannot LEARN.** Pinning
> the contract first costs nothing now and is near-impossible to retrofit.

**Measured:**

| | |
|---|---|
| a rule round-trips through a value (incl. negation and `Mint` slots) | **yes**, and the encoding reuses `reify`'s `<of_s>/<of_p>/<of_o>` — a pattern atom is described exactly as a fact is, which is [[learning-arc]]'s *"only the FLAT reification is learner-writable"* arriving as a consequence |
| **CLOSURE: a unit emits a rule, the bridge declares it, the network derives what nothing authored** | **yes** — the system's own output became computation |
| **THE LINE HOLDS** (§8, §16.6) | the bridge added **zero wires**; §3b's spawn policy still decided who feeds the new template. Asserted behaviourally AND by the absence of any `.wire(` in the module |
| idempotency, variable scoping across rules, refusal of a malformed rule | all hold; refusal RAISES rather than guessing ([[epistemic-closure-under-composition]]) |

**⚠ THE STANDING RULE REACHES A THIRD CONSTRUCT.** A rule is minted structure, so an unkeyed encoding
differs every time and a DERIVED rule would never settle. `encode(key=)` derives every structural node
from the rule key. After the trace's firing nodes (§20.1a) and the band's handles (§22.8), *anything
minted per run must be keyed* is no longer an observation — it is the shape of this substrate.

**⚠ AND §10.5 ARRIVED CONCRETELY, in the smallest possible example.** `MORTAL#1` emits
`socrates is_a mortal`; the index keys on the PREDICATE ALONE; `is_a` is what the template reads — so the
assembler unrolls onto a conclusion whose object the LHS requires to be `man`, and **spawns an instance
that can never fire.** Harmless (it is the documented *woke and correctly wrote nothing* case, and it
gates) but not free: a dead unit and a wasted round, on a two-line rule.

> **This is the argument for §19's COMPUTED INDEX, made concrete rather than predicted.** The form already
> says the LHS needs `object = man`; a static index built from the form set could have refused the wire
> before spawning anything. §19 said the index *could* be computed rather than accumulated; this says it
> *should* be, and that the cost of not doing it shows up on the very first rule rather than at scale.

**What this does NOT settle.** A grammar is still needed eventually — but it is now a front-end onto a
fixed contract rather than a thing the architecture waits on. Nothing here touches force, sinks, suspend,
or §24.3's reference problem: this is the *rule* half of intake, and the *fact* half (an utterance's
entities, and which of them are the same entity) is where §24.3 lives.

---

## 25. DERISKING — ranked by what forces a REDESIGN if found late (user, 2026-07-26)

> *"Let's prioritize things that derisk hitting walls later."*

The ranking is not by size or by interest. It is by **blast radius × probability, divided by cost to
probe** — what invalidates already-built work if it turns out badly.

### 25.1 ⭐ TIER 1, TAKEN — SCALE, the measurement this document promised and skipped

Every claim in this file has been measured on nets of **under ten units** (§15.3, §16.7, §20.3, §22.7
all say so). Meanwhile §16.4 accepted a cost with an explicit promise: *"assembly becomes O(units ×
upstream-walk) per pass. Accepted… **it is the next thing to measure rather than assume**."* It was never
measured, and [[measure-before-optimizing-ugm]] and [[whole-graph-banks-must-be-idempotent]] are both in
this repo's memory because superlinear accretion was found exactly this way, twice, after being assumed
away. Blast radius: total — a superlinear assembler is a redesign of `Net`, not a tweak.

`bench/spike_scale.py`. **Two defects found, both fixed, both mine rather than the design's:**

| defect | fix | effect |
|---|---|---|
| **`propagate` re-ran EVERY unit on every call**, and `run` calls it after each assemble pass — so depth cost a full re-propagation per unrolled instance | `Net.dirty` seeds propagation from the units whose inputs actually changed | rounds for a 12-chain: **92 → 14**, i.e. quadratic → linear |
| **`trace.handle_of` is a linear scan, called once per premise** — O(n²) in the size of the value, and the dominant cost on a wide net | `handle_index`, built once per call | wide-net time roughly halved |
| (`upstream` re-walked per unit per template per pass) | memoized, invalidated on any rewire | included above |

**And the result that matters, after the fixes:**

| measurement | slope | reading |
|---|---|---|
| units vs chain depth | **0.87** | **LINEAR.** §4b's ATMS exponential does not appear on this shape — one instance per hop, as designed |
| propagation rounds vs depth | **linear** | was quadratic |
| the ANSWER's own size (transitive closure) | 2.16 | inherent — a chain of *n* has ~n²/2 reachable pairs |
| wall time | 2.83 | ⇒ **machinery overhead ≈ n^0.67 on top of the answer's own size** |

> **The substrate is not the wall.** The dominant term is the size of the answer being computed, which no
> design avoids. The residual n^0.67 is value copying — §5's **known and deliberately deferred** HAMT: *"the
> frozenset spine IS copied on each union… the one optimization that would change nothing semantically."*
> So the remaining scale risk is a recorded optimization, not a design flaw, which is the best outcome
> this probe could have had.

Honest limits: two shapes only (wide and chain), no branching/hypothesis fan-out, and **§4b's exponential
is precisely what a chain does NOT exercise** — sibling hypotheses are the shape that could still blow up,
and they are the obvious next measurement.

### 25.2 The ranking that follows

**TIER 2 — cheap, compounding, and now top of the list:**

1. **⭐ THE REIFICATION DECISION (§23.3).** One handle per fact per value, or not. **Intake will reify** —
   mentions, utterances, entity boundaries — and if it invents a THIRD scheme on top of `trace`'s and
   `reify`'s, that is precisely the *"stack of seams difficult to sanitize later"* the user warned about.
   Cheap to decide now, expensive to unpick once intake depends on it. It also unblocks `band.inherit`,
   the largest remaining Python seam.
2. **THE COMPUTED INDEX (§19, §24.7).** Measured as needed on a two-line rule, not at scale — the index
   keys on the predicate alone and spawns dead instances. It must be built **while the form set is built**,
   because retrofitting means the index has already been accumulated.

**TIER 3 — high blast radius, expensive, and de-risked by Tier 2:**

3. **§24.3 DISCOURSE REFERENCE / COREF.** The deep one, and note it is *already measured* as the
   pathological case for the index: §22.5 found a wildcard `?s ?p ?o` rule both **defeats the index** and
   **consumes its own control predicate**. Coref-merge is exactly that rule. So doing the computed index
   first is not a detour — it is the thing that makes this affordable.

**TIER 4 — cost, not risk:** force, the sink, suspend/procedures, the grammar. Each is work, and each has
a decided shape (§16.6, §24.2, §24.4). Building them early derisks nothing; building them late costs the
same. **The sink was my earlier recommendation as a first probe and this ranking demotes it** — it is the
cheapest, not the most derisking, and those are different questions.

### 25.3 ⭐ TIER 2.1 TAKEN — a fact's handle is a PURE FUNCTION of the fact (109 green)

§23.3 framed the decision as *"one handle per fact per VALUE"* — the trace looking up whatever the object
wire had already minted. **There is a stronger option, and it is strictly better on every axis:**

> **The handle is arithmetic on the three node IDENTITIES.** Any two reifications of the same fact,
> anywhere, in any value, on any wire, produce the SAME node — with no lookup, no coordination between
> wires that deliberately share no state, and **no registry**, so §3's one-global-structure rule is
> untouched: it is a function, not a table.

**It stays inside §21.2 because it is derived from IDENTITY, never from NAME.** Two entities both called
`mary` yield different handles, because their nids differ. A content-derived handle is structural
identity, not a label — which is the distinction that has to hold, and does.

**Four consequences, and only the first was the goal:**

1. **§23.3 CLOSES.** A band now hangs off the same node a firing's `<from>` points at (measured).
2. **⭐ DEGREE INHERITANCE IS A RULE** — `band.inheritance_rule()`, three atoms:
   `?f <concluded> ?c ∧ ?f <from> ?pc ∧ ?pc <band> ?b ⇒ ?c <band> ?b`. §16.5 designed it as *"one generic
   rule over the firing record"* and it stayed Python for two reasons, both now gone: it needed a
   predicate variable (§22.6) and a shared handle (this). **The largest Python seam in §23's audit is
   closed**, and it reads the TRACE wire while writing the OBJECT wire — §16.6's *"where the two networks
   meet"*, arriving as an implementation rather than a prediction.
3. **Reification is IDEMPOTENT**, which retires a class of §22.8 fixpoint bugs instead of guarding them.
   `negation`'s private key-derivation and `reify`'s `key=` parameter both became dead weight.
4. **Two derivations of one conclusion now converge on one handle**, so the trace natively represents *"P
   has two justifications"* — the ATMS structure, free for the third time (§4b, §20.1c).

**⚠ What remains, and it is the smaller half:** `Net.assemble` still does not know about trace wires
(§20.3), so an inheritance unit must be hand-wired. The Python `band.inherit` is kept for that reason
alone and is superseded in principle. *"Inheritance cannot be a rule"* has become *"the assembler cannot
yet wire a trace input"*, which is a much better-shaped problem — and it is the same gap §23.4's
explanation-as-units will hit, so it is now one blocker for two seams rather than two blockers.

---

## 26. TRACE-WIRE ASSEMBLY — one blocker, two seams (BUILT 2026-07-26)

§25.3 made degree inheritance expressible as a rule and left one thing: **`Net.assemble` did not know
about trace wires**, so such a unit had to be hand-wired. §23.4 had already established that
`explain`-as-units hits the same wall. `bench/spike_trace_wiring.py` (23/23),
`tests/units/test_trace_wiring.py`, **115 green.**

Three questions, each answered from what was already there rather than by a new declaration:

| question | answer |
|---|---|
| which templates want the trace? | those whose LHS names a FIRING predicate — derivable, `Net.reads_trace` |
| where does the trace land? | the consumer's **`inputs`**, because `view()` is what `solve` matches |
| what may be satisfied from which wire? | a firing predicate only from a trace output, an object predicate only from an object output. **A mixed template spawns on its object half and completes on its trace half** — which is more selective than the reverse |

**⭐ §16.6's CONSTRAINT BECOMES CONDITIONAL, AND STAYS ENFORCED.** *"The trace must never accrete into the
object value"* becomes **never, unless the unit ASKED** — a unit whose LHS names a firing predicate has
asked, and refusing would make metareasoning unsayable. **What contains it is SUBSET OUTPUT (§16):** such
a unit emits only what it derived, so nothing downstream sees the trace unless it too asked. Measured
three ways: an ordinary unit's view holds no firing predicate, the consumer's does, and its *output* does
not. `trace_leaks()` still holds, and §6a's NAF is unaffected for units that did not ask.

**Both seams close.** Inheritance assembles itself; an explanation hop assembles itself. `band.inherit`
and `trace.explain` are now superseded in fact, not only in principle.

### 26.1 ⚠ THE GUARD THAT HAD TO BE DISCOVERED — stratification

A template reading ONLY firing predicates (an explanation hop, §17.G's stability watcher) has an empty
object need, so it must spawn on its trace half. And then:

> **Every unit has a trace. A trace consumer IS a unit. So consumers feed consumers, forever.** And
> because firing nodes are MINTED, the projection never repeats and §15.1(c)'s dedup never fires.
> **Measured before the guard existed: 57 instances, fuel exhausted.**

The guard is one local test: **a unit that reads the trace is never wired to the trace of a unit that
reads the trace.** Level 0 is the world; level 1 is about level 0; level 2 needs a deliberate act, and
there is not one. Bounded to 1 instance, measured.

> **⭐ §17.G PREDICTED THIS EXACTLY** — *"firing on stability DESTABILISES… requires stratification, which
> is the same shape as [[stratification-both-engines]] and must be designed in, not discovered."* It was
> discovered. The prediction was right about the mechanism and wrong about who would find it first, which
> is the honest record: this document has now predicted a wall and still walked into it.

### 26.2 The cost, unchanged and now acute

**Trace wiring is maximally unselective.** Every unit emits every firing predicate on its trace wire, so
the index cannot discriminate at all — a trace consumer is wired to essentially everything upstream of it
(measured: 4 trace wires for 4 units, against 3 object wires). This is §10.5 at its worst, and it has the
same answer as everywhere else: **§19's COMPUTED INDEX.** A template reading `<from>` could be restricted
statically to the units whose conclusions it actually grades. That remains Tier 2.2 of §25.2 and this
makes it more urgent, not less.

---

## 27. THE ASSEMBLY JOURNAL — the assembler's decisions as data (user, BUILT 2026-07-26)

> **The user's proposal, from the biological framing:** the brain has a *"network configuration network"*
> that, given discourse, activates the neurons that compute — gating rather than rewiring, because
> topology is fixed at millisecond scale. *"If we create this network-building network, we would have a
> way to recreate the explanation chain, or at least the rule chain."*

`units/journal.py`, `tests/units/test_journal.py`, **123 green.**

**Three things were separated before building, and the separation is the substance:**

1. **The stated payoff was already delivered.** §20's trace gives the explanation chain, and §23.4
   *measured* why wires are the wrong source (they say what COULD have fed a unit; refire keeps only the
   last output; late wiring changes the topology). A configuration network would reproduce the source
   §23.4 rejected.
2. **Fixed topology is a CONSTRAINT the brain has and we do not.** §0 claims that difference as the
   advantage — *"neurons must be physically wired, whereas units can be assembled on demand."* Importing
   the mechanism would cost assembled depth.
3. **But GATING and REWIRING are different acts, and only one is §8's line.** Deciding what *flows* on a
   wire is what every unit already does (§16.2: a non-firing unit is a real gate). Deciding what wires
   *exist* is policy. The functional insight — *routing decisions should be first-class and inspectable* —
   is separable from the fixed-topology mechanism, and that is what got built.

**⚠ 27.1 THE FAILURE MODE IT CLOSES, and it is the one that matters for intake.** Measured: **a form can
be accepted, become a well-formed template, and never be wired — silently.** `wellformed()` stays clean,
the budget is untouched, nothing anywhere says so. That is [[book-corpus-experiment]]'s *"partial intake
systematically drops exceptions, so learning goes optimistically biased"* **one layer below the parser**:
the parse succeeded and the assembler quietly declined. Its mirror image — §24.7's spurious instance that
can never fire — was equally silent. Both are now facts.

**And §8's requirement becomes true rather than aspirational.** §8 says a dynamically-wired system *cannot
be statically checked, so the trace is the only thing there is to inspect* — and then left the assembler,
the part doing the dynamic wiring, entirely outside the trace.

**What is recorded:** `<spawned>` (which template an instance came from), `<wire_from>`/`<wire_to>`/
`<wire_kind>`, `<declined>` with a reason (`<would_cycle>`, `<would_bypass>`, `<nothing_new>`,
`<stratified>`), and `<unused>` for a template accepted and never instantiated. **A refusal is a fact** —
the assembler always made these decisions and never recorded one, so *"what did you not consider?"* had no
answer at all.

**OBSERVABLE, NEVER WRITABLE** (§20.4, §22.1). Nothing here lets a unit wire anything. A unit may READ why
a wire exists exactly as it may read why a conclusion holds — measured: a rule over `<unused>` flags the
silently-dropped form. §8's line is untouched.

**These are PROVENANCE** by §23.2's own test (*which fact a handle denotes* is content; *how it came
about* is provenance — and how the NETWORK came about is the same kind of thing). So journal predicates
join `FIRING_PREDICATES`, which means §26.1's stratification covers them for free and an ordinary unit
still cannot see them.

### 27.1a Three things building it found

- **THE JOURNAL MUST NOT BE A UNIT.** It was one, briefly, and polluted every unit count, every
  `wellformed` walk and every `upstream`. **The assembler's record is not part of the computation it
  records.** It is a value with a reserved producer name.
- **§22.8'S STANDING RULE, A FOURTH CONSTRUCT.** A wire's identity must be a function of its endpoints,
  not a fresh mint. And an already-wired producer must be skipped **silently**: logging it as *nothing
  new* made the journal grow on every re-run of a quiesced net — and the journal rides a trace wire, so a
  growing journal destroys the fixpoint that `output unchanged` depends on.
- **⚠ `<unused>` IS A STATE CLAIM, NOT A FIRING — so it must be WITHDRAWN.** Firings accrete (§20); a
  current-state claim that stops holding is a false report. The watcher flagged **itself**, because at the
  pass where orphans were computed it had no instance yet. It is now withdrawn and its readers refire
  (§7: nothing is retracted, downstream recomputes) — §16.6's supersession stub, reached from the journal
  side rather than the firing side.

### 27.2 What it does and does not do for §24

**Does:** it is the INSTRUMENT for building the network from discourse — it turns the dominant intake
failure from silence into a fact, and it is the validation gate for §19's computed index (ground truth:
what the index proposed versus what actually fired), which is this repo's own pattern
([[flip-default-blocked-by-greedy-grammar]]: build the gate first).

**Does not:** §24.3 (reference without lookup) and §24.4 (procedure sequencing) are REPRESENTATION
problems. Assembly events determine whether you can SEE it working, not whether it works.

**If routing should ever be LEARNED**, gating cannot supply that and it does require crossing §8. The safe
shape, recorded but not built: **units may PROPOSE wirings as facts; the assembler stays the only thing
that wires.** Proposals become inspectable, refusable and traceable, and *"units never touch wiring"*
survives literally — a unit emits a proposal, never an edge.

## 28. THE COMPUTED INDEX — selectivity from SHAPES (BUILT 2026-07-26)

`units/index.py`, `bench/spike_computed_index.py` (37/37), `tests/units/test_index.py`, **138 green.**
Tier 2.2 of §25.2, and §27.2's journal is what validated it.

§19 said the index *could* be computed rather than accumulated; §24.7 said it *should* be, and measured the
cost of not doing it on a **two-line rule**. The build takes it, and the honest headline is that the
mechanism is smaller than the section it closes: **the wire test stops being *"do these share a predicate"*
and becomes *"could any fact on this wire satisfy any ATOM of this LHS"*.**

### 28.0 ⭐ THERE ARE TWO INDEXES, AND CONFLATING THEM WOULD BE UNSOUND

This was the design decision, and it was forced by case 5 rather than reasoned:

| | over | may it gate a wire? |
|---|---|---|
| the **STATIC** index (`ComputedIndex`) | TEMPLATES — which can in principle feed which, a pure function of the library | **NO** |
| the **RUNTIME** filter (`feasible`) | FACTS — can this value satisfy any atom of this LHS | yes, and it is exact |

The reason is not stylistic: **a `given`, a `branch` and a `carrier` are units whose output NO template RHS
describes.** Gate on the template relation and every hand-supplied fact is cut off from the rules that read
it — §19's *"which template can feed which is derivable from the form set"* is true and is *not* the wiring
test. So the static index's job is DIAGNOSIS, not dispatch: `wildcards()` names, from the form set alone and
before a unit exists, the rules nothing will restrict.

### 28.1 ⚠ TWO LIVE DEFECTS, and the first one produced a FALSE CONCLUSION

Both were found by spiking to break (standing rule 4), and both were **pre-existing** — the index only made
them reachable. Neither would have crashed (standing rule 2, five for five now).

> **⭐ THE ASSEMBLER DELIVERED ONLY THE POSITIVE HALF OF AN LHS.** A negated premise's predicate was in no
> need set, so a producer of it was **never wired.** Under SUBSET OUTPUT that means §6a's NAF was evaluated
> against a value the fact never reached — so *`?x is_a man ∧ ¬ ?x is_a dead ⇒ ?x is_a walker`* concluded
> `walker` **with `dead` derived and sitting one wire away.** A wrong answer, silently, on a three-atom rule.

Two things had to change, and the second is the more general:

- **A negated atom may COMPLETE an instance and must never SPAWN one.** An instance born on *"there is no
  P"* has no positive premise and nothing to conclude from — and getting this backwards spawns a rule
  instance off the very evidence that will silence it. `_half_atoms(negated=…)` is that distinction.
- **⭐ THE JOIN IS OVER ATOMS, NOT PREDICATES.** A predicate-level need cannot say *"another producer of
  `is_a`, but for a different atom of it"* — and it reported the need as already satisfied. That is not a
  corner case: it is what a negated premise on a predicate the positive body also reads looks like, which is
  the normal shape in a taxonomy. Atom-level need is also what makes the filter and the join agree instead
  of each working at its own granularity.

The second defect was in the guard I reached for to contain the first: **`restores_a_drop` read every
ordinary JOIN as a bypass.** Under §16 a rule emits its conclusion and nothing else, so *every* rule lacks
*all* of its ancestor's facts — that is subset output, not a deliberate omission. Harmless while it was only
a `wellformed` report; wrong the moment it became a wiring decision. **Only a CARRIER can drop**, because
only a carrier emits its view. §17.A's guard was right about the phenomenon and untyped about the producer.

> **⚠ AND ONE PIECE OF §3b GOT CONFIRMED BY LOOKING LIKE A BUG.** Two INDEPENDENT `given`s are two WORLDS:
> they share no lineage, so they are incomparable and the assembler refuses to join them — a NAF does not see
> across them and the rule fires. That is §4's emergence claim doing its job, and joining worlds is what a
> MERGE unit is for. Recorded because it presents identically to the defect above and is the opposite of one.

### 28.2 WHAT IT BUYS — measured, and it is SHAPE-DEPENDENT

| shape | effect |
|---|---|
| §25.1's `next`/`reaches` chain | **nothing.** Identical units, identical spend, ~3% overhead — those predicates were already selective |
| **one predicate doing all the work** (a taxonomy: every template reads and writes `is_a`) | **units `2k-1` → `k`; budget spend QUADRATIC → LINEAR** (265 → 23 at k=12) |

**The compounding is the point:** a dead instance is itself a producer of the predicate, so it spawns more
dead instances. §10.5's warning was not about waste, it was about a multiplier.

> **⭐ AND THE SHAPE IT PAYS ON IS THE ONE A MINIMUM FORM SET HAS.** §19 predicted exactly this and filed it
> as a tension — *"a small form set makes §10.5 WORSE, not better; if there are ten forms, all
> discrimination falls on predicate constants"*. It is the same prediction, now with a number on it, and the
> resolution is that the discrimination does not have to come from the predicate at all.

### 28.3 WHERE IT BUYS NOTHING, and §26.2's hope does not survive

§26.2 hoped a trace consumer *"could be restricted statically to the units whose conclusions it actually
grades."* **It cannot.** `band.inheritance_rule()`'s trace atoms are all-variable except their predicates,
so `selectivity` is **0.0** — the shape does not say which units those are, and no shape could. Trace wiring
stays maximally unselective. Asserted as a test so the hope is not re-raised as an oversight.

The same applies to §22.5's wildcard, which is §24.3's coref-merge shape: fed by everything, unchanged. What
is new is only that **the index says so in advance**, which is worth having and is not a speedup.

### 28.4 THE GATE — `Net.index_audit()`, and it is a DIFFERENTIAL

§27.2 named the journal as the validation gate (*what the index proposed versus what actually fired*) and
the two directions are not symmetric:

    over-approximation   a wire the index permitted whose consumer never fired    -> wasted work
    under-approximation  a premise actually CONSUMED, over a wire the index would
                         REFUSE                                                  -> A DROPPED DERIVATION

`unsound` must be empty and is checked against **consumed premises**, not against the filter's own
decisions — asking a filter whether it agrees with itself measures nothing (standing rule 3, which is why
this is written to work with `computed_index=False` too: run without the index and the audit reports what
switching it on *would* have lost).

A refusal is a fact: `<no_shape_match>` joins §27's journal reasons, so §24.7's silent spurious instance
became a recorded refusal rather than a spawned unit — the mirror of §27.1's silent unwired form, closed
from the other side.

### 28.5 What this does and does not change for §24

**Does:** the form set can now be audited for selectivity *as it is written*, which is why this had to come
before the grammar — retrofitting means the index has already accumulated. And §24.3's coref work is
affordable in the sense §25.2 meant: the pathological rule is still pathological, but everything around it
is no longer paying a quadratic multiplier for sharing a predicate with it.

**Does not:** the wildcard is undiminished, and §24.3 is still the deep one. The next thing is
DISCOURSE REFERENCE — reference DECIDED, not resolved: a fresh node per mention plus a coref-merge unit,
so coref becomes a chain position and two chains may legitimately disagree about identity.

## 29. THE ASSEMBLER-COMPLETENESS SWEEP — two more silent defects (BUILT 2026-07-26)

`bench/spike_assembler_completeness.py` (27/27), `tests/units/test_index.py`, **143 green.**

**Why this rather than §26.2 or §24.3.** §28.1 found the assembler delivering only the POSITIVE half of an
LHS, and the consequence was a **false conclusion, silently, on a three-atom rule**. §27.1 had already found
its sibling one layer up (a form accepted and never wired). That is a bug CLASS, not a bug — *the assembler
quietly fails to deliver part of what a template asked for, and the answer changes* — and standing rule 2
says to assume quiet. So the response to finding one was to SWEEP the matrix: **LHS shape × producer
situation**, each cell asking *did the instance get what it needed?*

The interesting answers were never "no". They were **"no, and nothing said so"** — twice more.

### 29.1 ⭐⭐ TWO SIBLING WORLDS THAT DIFFER ONLY UNDER NEGATION COLLAPSED INTO ONE

`base` asserts `p1`; `H1` supposes `block`; `H2` supposes nothing; the rule is `p1 ∧ ¬block ⇒ ok`. H1's world
must stay silent and H2's must derive `ok`.

> **Only ONE instance was spawned.** The two branches project **identically on the positive half** — both
> offer exactly `p1` — so the second was declined as *nothing new*. **The world where the answer is YES had
> no instance at all**, and nothing anywhere said so.

This is §4's emergence claim failing in the one place it is supposed to hold, and §28.1 caused it: separating
the trigger from the projection, I made *both* positive.

> **⭐ THE GENERAL LESSON, and it is worth more than the fix: WHAT MAY START A COMPUTATION AND WHAT
> DISTINGUISHES TWO OF THEM ARE DIFFERENT QUESTIONS.**
>
> * the **TRIGGER** is POSITIVE — a template must never be instantiated on *"there is no P"*;
> * the **PROJECTION** is an **IDENTITY** and must span BOTH POLARITIES — two offers differing only in a
>   NAF-relevant fact are DIFFERENT OFFERS.
>
> Collapsing them **loses worlds** rather than raising an error. `_offer` now returns `None` for *nothing to
> trigger on* and the both-polarity projection otherwise, so the two roles cannot be confused again.

### 29.2 ⚠ A TEMPLATE WITH NO GROUND PREDICATE WAS NEVER INSTANTIATED

`?x ?p ?y ⇒ ?y ?p ?x` **did not run.** The object/trace fork was `on_trace = not need` — *"reads no ground
OBJECT predicate"* — which also describes an **all-variable** template. Such a template went to the trace
fork, where its (empty) ground need matched nothing, and no instance was ever born. `wellformed()` clean,
budget untouched; §27's journal did flag it as `<unused>` and `wildcards()` named it, which is the instrument
working, but the behaviour was still wrong.

Two corrections, and the second is the reusable one:

- **The fork test must be POSITIVE:** *does this template read ONLY firing predicates?* Not *does it fail to
  read a ground object predicate?* Two different questions with the same answer on every shape built so far.
- **The predicate PRE-FILTER is an optimization, and it is only sound when there is a ground predicate to
  filter on.** With none, the shape test is the whole test. A wildcard then pays §22.5's price honestly — it
  wakes on everything — instead of silently not existing.

It terminates: the reverse of the reverse is the original, so the projection stops changing (2 instances,
5 budget).

### 29.3 THE CELLS THAT WERE ALREADY RIGHT

Asserted rather than assumed, because a guard that is never reached looks exactly like one that works
(standing rule 3): ground SUBJECT and ground OBJECT slots; an `n`-premise join where every producer arrives
on a **later pass** than the spawn (k=2,3,4 — the spawn loop, not `_complete_lhs`, is what completes these);
two atoms on ONE predicate needing two producers; a negated premise derived TWO HOPS away; a mixed
object+trace template; a branch that REMOVES its own premise, which starves its own world and is **not**
bypassed; and two independent `given`s remaining two worlds, asserted specifically so §29.1's fix is not
read as licensing a cross-world join.

### 29.4 THE RESIDUE — §24.3's inbox, and it is cost rather than defect

The coref-merge shape (`?x ?p ?y ∧ ?x same_as ?z ⇒ ?z ?p ?y`) **works**, and it exhibits both things §22.5
predicted:

- it spawns a **redundant unroll** that re-derives what the first instance already had — the wildcard
  defeating the index, a cost and not a wrong answer;
- it **consumes its own control predicate**: `?p` matches `same_as`, so it derives `m2 same_as m2`.

Those are now measured facts sitting in front of §24.3 rather than predictions about it.

> **⚠ AND THE SCORE ON THIS BUG CLASS IS NOW FOUR FOR FOUR SILENT, THREE OF THEM ANSWER-CHANGING**
> (§27.1's unwired form, §28.1's undelivered negated premise, §29.1's collapsed world, §29.2's uninstantiated
> template). The pattern is sharper than "assume quiet": **every one of them was a question asked at the
> wrong granularity** — predicate where an atom was meant, positive where both polarities were meant, absence
> of one thing taken as presence of another. The assembler decides by *set intersection over predicates*, and
> each defect was a place where that abstraction was one level too coarse for what was being asked.

## 30. DISCOURSE REFERENCE — decided, not resolved (§24.3 TAKEN, 2026-07-26)

`units/discourse.py`, `vocab.lexeme`, `bench/spike_discourse_reference.py` (25/25),
`tests/units/test_discourse.py`, **158 green.**

§25.2 ranked this Tier 3 — *"the single largest piece of new design"* — and §24.3 stated the constraint that
makes it hard: *"the lion"* must reach the same entity as the first mention, and it may **not** be looked up
by name, because entities are nameless (§21.2) and interning a surface word is §3's forbidden second global.

**Everything built here is DATA.** Seven declared rules and one node-minting convention; no engine change was
needed for the representation. Every engine change in this section is a DEFECT FIX, which is the outcome
§24.3 could most have hoped for.

### 30.1 ⭐ THE LEXEME IS THE LICENSED BRIDGE, and the distinction was already being made

> **The word *lion* belongs to the FORM SET. THE LION is a nameless mention.**

That one line resolves the whole apparent paradox. `vocab.Vocabulary` already interns ROLES, licensed by
*a form may mint, an utterance may not* (§22.5). A **lexeme** is the same kind of thing: supplied at load,
shared across every utterance, namespaced `#word` so it cannot collide with a role. A mention carries
`m <word> lexeme("lion")`, and coref becomes a rule over **lexeme** identity — so nothing about the ENTITY is
resolved by name, and both rules survive literally.

Measured both ways: two mentions in different utterances corefer through the shared lexeme, and two
independently MINTED `lion` nodes still refuse to match. The by-name fusion §22.5 closed stays closed.

### 30.2 ⭐ INEQUALITY DISSOLVES — identity as DATA

Coref needs `?x ≠ ?z` and the matcher has no such primitive. **It needs none:** `?x <word> ?y ⇒ ?x <self> ?x`
makes identity a FACT, and `Absent(?x <self> ?z)` **is** `?x ≠ ?z` — exact, over the value on the wire (§6a),
no fuel. Without the guard it is measurably reflexive junk, so the guard is not decoration.

That is the second recorded gap to dissolve rather than be filled (§17.E's predicate variable was the first),
and the pattern is worth naming: **on this substrate a missing relation between terms is usually a missing
FACT, not a missing operator.**

> **⚠ AND §30 RESTS ON §28.** The inequality rule's producer has to be WIRED for the NAF to see it — and
> until §28.1 a negated premise's producer was **never wired**. The whole of §30.2 would have silently
> reported "everything is unequal to everything". Doing §28/§29 first was not a detour: §30 is unbuildable on
> the assembler that existed two sections ago.

### 30.3 ⚠ THE ASSEMBLER CANNOT WIRE A WILDCARD MERGE, and that is what a wildcard costs

`?x ?p ?y ∧ ?x same_as ?z ⇒ ?z ?p ?y` (§17.D's generic substitution) gets wired to the coref rule and **not
to the discourse**, so it substitutes over `same_as` facts and nothing else. And this one cannot be fixed by a
better need computation:

> **The wildcard atom is satisfied by ANY fact — including the rule's own control facts — so *"is this atom
> unmet?"* is vacuously false.** The atom is formally satisfied, by the wrong facts. No test at this
> granularity could notice.

**So the topology for a wildcard rule must be AUTHORED, not inferred** — a merge carrier over the discourse
and the decision. That is not a defect; it is the price of declining to say what you read, and §24.4 already
accepted *"intake manufactures the dependency"* as the shape for procedures. It is the first place in this
document where wiring is genuinely not inferable, and it lands exactly where §22.5 predicted.

**And the merge must hold EVERY premise in ONE value.** A rule's output does not carry its input (§16), so a
merge over the discourse and the decision but *not* the symmetry substitutes one way only — and the wildcard
rule cannot self-unroll for the same reason: hop *n+1* reads hop *n*'s conclusions, which contain no
discourse. Measured.

**Two defects fell out, both in the bypass guard, both pre-existing:**

- **`gated` treated a unit as a bypass of ITSELF.** Under subset output an intermediate rule never carries an
  upstream unit's predicate, so a direct wire from that unit is the ONLY route — and the guard refused it. A
  template whose negated premise is produced two units back was denied its own producer and **its NAF went
  vacuously true.** A unit cannot be a bypass of itself.
- **`restores_a_drop` counted facts the carrier NEVER RECEIVED as facts it dropped** — which under subset
  output is most of them, so ordinary merges downstream of a rule were flagged as bypasses. **A drop is what
  ARRIVED and did not leave.** (`view()` already applies `removes`, so `view - output` was vacuously empty;
  the comparison has to be against the pre-removal union.) §17.A's real bypass is still caught.

### 30.4 ⚠ SUBSTITUTION UNIONS PROPERTIES; IT DOES NOT COLLAPSE IDENTITY

Both mentions end up carrying both properties, and **remain two nodes** — so *"how many lions roar"* answers
2. §17.D designed the merge as *"a delta that substitutes B→A"*, and that needs REMOVAL:

> **A RULE CANNOT REMOVE.** `Unit.removes` is fixed at construction and a rule's `rhs` only adds. §21.1's
> claim that *"a unit is a graph REWRITE"* is true of the STATIC spec and **false of the rule** — a derived
> rewrite, one whose removals depend on the match, is inexpressible. Coref is the first thing to want it.

So coref here is **sound for what rules MATCH and silent for what is COUNTED**, which is §17.F's uniqueness
gap in a second guise rather than a new one. **Whether to add derived removal is an open DECISION, not an
oversight** — it would give a rule non-monotone output, and §7's *"revision dissolves, downstream
recomputes"* is built on rules only ever adding. Recorded, not taken.

### 30.5 THE DECISION, and one thing that fell out of getting it wrong

The rule is **definiteness**, not the word: a DEFINITE mention corefers with an INDEFINITE mention of the
same lexeme. Keying on the shared lexeme alone merges *"a lion roars. A lion sleeps."* — two different lions.
That is not a substrate failure but a **wrong decision**, which is precisely what §24.3 means by *decided*.
Recency, salience and description-matching are further premises on the same rule shape and need no new
machinery.

> **⭐ AND THE ASYMMETRY THAT MAKES THE DECISION RIGHT MAKES THE SUBSTITUTION ONE-DIRECTIONAL.** Substitution
> follows the arrow, so it carries the definite mention's properties to the antecedent and not the reverse:
> what is said about *"the lion"* reaches the entity, while what was already known about the entity never
> reaches the mention. **Sameness is an equivalence and the decision is not**, so the two must be separated —
> decide asymmetrically, then symmetrize (`symmetry_rule`). Found by getting the direction wrong in the spike
> and reading what came out.

### 30.6 ⭐ §17.F's TWO LOGGED GAPS BECOME DETECTABLE

`form_inventory.md` §4a has carried both as *no mechanism*; both are now ordinary facts:

| §17.F's finding | now |
|---|---|
| **uniqueness** — *"two cars matched; both would be derived over, silently"* | `?x same_as ?z ∧ ?x same_as ?z2 ∧ ?z ≠ ?z2 ⇒ ?x <ambiguous> ?x` — two antecedents is a FACT other units can read |
| **reference failure** — *"empty result, indistinguishable from negation"* | a `<resolved>` witness plus NAF ⇒ `<dangling>`; presupposition failure stops collapsing into falsity |

Neither RESOLVES anything — they make the failure **sayable**, which is what was missing, and it is
[[epistemic-closure-under-composition]]'s *reasoned ∪ refused, never silently mis-mapped* reaching discourse
reference. The existential needed one extra rule (a witness) because `Absent` may only test variables the
positive body bound; no new primitive.

### 30.7 TWO CHAINS MAY DISAGREE ABOUT IDENTITY — §17.D's prediction, measured

Downstream of a merge branch the two mentions are one; downstream of a sibling that declines the merge they
remain two. **Coref is a CHAIN POSITION** — §4's *"scope is a chain"* applied to identity, and it needed
nothing new: the world that declines the merge simply never spawns a substitution instance, because §3b has
nothing to trigger on there.

### 30.8 WHAT §24.3 LEAVES

**Closed:** the evidence question (the lexeme), inequality, the decision shape, uniqueness and
reference-failure detection, chain-relative identity, and the substitution's real topology.

**Open, and now precisely stated rather than vague:**

1. **DERIVED REMOVAL** (§30.4) — the one thing that would make substitution a true merge. A decision about
   the computation model, not a missing feature.
2. **Wildcard cost** — §29.4's redundant unrolls are undiminished, and §28.3 already established that no
   shape can restrict them.
3. **Intake proper** — an utterance's boundary, the idempotency key (§24.5), and FORCE. None of which this
   section needed, which is itself the useful news.

## 31. THE EXPRESSION BUILDS THE NETWORK — selector chains (user proposal, BUILT 2026-07-26)

`bench/spike_selector_chain.py` (21/21), `tests/units/test_selector.py`, **172 green.**

> **The user's proposal:** *"'wash the car that is parked at the third floor of the garage near the movie
> theater' builds a network of chained selectors, and at the end of it places a tool call to `wash` on whatever
> entity it gets. The network derives from the expression."*

This lands directly on §30.3's wall: a pattern that declines to say what it reads cannot have its topology
inferred, so it must be **authored**. If the syntactic nesting *is* the wiring, the expression authors it.

### 31.0 What a selector outputs — the user's crux, answered from a decision already in force

> **A reference, keyed on the selector STEP. Not the subgraph, and not a mark on the entity.**
>
>     <s3> <refers_to> car        NOT   car <selected> yes
>     <s3> <narrows>   <s2>             (so the unfolded expression is walkable off the graph)

§17.F had already settled the substance: **a description IDENTIFIES rather than CONSTITUTES.** Read
constitutively, *"one subgraph = one entity"* means the car stops existing when it moves to the second floor. So
the entity stays a node and the subgraph is the **constraint set** on it. Three further reasons, all from
decisions in force:

- **§16.** A rule emits only what it derived; emitting the subgraph is re-emitting the input, which is the
  accretion §16 removed. A reference fact is tiny.
- **§19, measured.** Entity boundaries survive exactly one hop — recoverable at a merge because a unit keeps
  each producer's value separately, gone one hop later. Emit subgraphs and you cannot tell which selector
  contributed what.
- **§25.3.** A handle is a pure function of the fact, so a step can name its result stably without a registry.

**Keying on the STEP rather than the entity** is the one refinement added to the proposal: it keeps derivational
marks off the entity, lets two chains disagree about the same entity, and is what makes the chain readable.

**And the output is a SET of references, not one.** A selector may match several; *"the"* is a separate
uniqueness demand layered on top (§31.3). Designing for exactly-one would make ambiguity inexpressible.

### 31.1 ⭐ THE ANSWER TO §30.3 — and selector chains are ASSEMBLABLE

The five units for the sentence, innermost first, with step nodes supplied by the parse:

```
s1: ?e <word> #movie_theater                                       ⇒ <s1> <refers_to> ?e
s2: <s1> <refers_to> ?p ∧ ?e <word> #garage ∧ ?e <near> ?p          ⇒ <s2> <refers_to> ?e
s3: <s2> <refers_to> ?p ∧ ?e <word> #floor ∧ ?e <of> ?p
                                           ∧ ?e <ordinal> #third   ⇒ <s3> <refers_to> ?e
s4: <s3> <refers_to> ?p ∧ ?e <word> #car ∧ ?e <parked_at> ?p        ⇒ <s4> <refers_to> ?e
c : <s4> <refers_to> ?e                                            ⇒ <call> <verb> #wash, <call> <target> ?e
```

> **⭐ THE ASSEMBLER WIRED ALL OF IT BY ITSELF.** Every selector received its predecessor *and* a world-carrying
> producer, with **no authored merge and no hand wiring** — because **every selector atom names its
> predicate**. That is the precise contrast with §30.3's coreference merge, whose wildcard atom is satisfied by
> any fact including its own control facts.

**And it is still a contrast, not an artifact.** §31.4's comparability fix might have explained it away; it does
not — re-measured, the coreference substitution *still* needs an authored merge. **The two obstructions have
different causes:** one is about *what satisfies an atom*, the other was about *which units may be joined*.

**The expression contributes DATA, never wires** (§8's line untouched): ground step nodes and `<narrows>` links,
as facts. The ordinary spawn policy does the rest. So *"the expression authors the topology"* is true **without**
anything acquiring the power to wire.

### 31.2 IT IS A TREE, NOT POSTFIX — and the correction matters

*"Postfix"* implies a linear stack order. What the expression supplies is **nesting**, and the network is a DAG:
*"wash the car **and the truck** that are parked at ⟨s3⟩"* gives one step with **two consumers**, measured. The
linear chain is the special case where each modifier attaches to the previous noun. Baking in a pipeline
assumption would have foreclosed conjunction.

### 31.3 GATING, FAILURE AND AMBIGUITY — all three for free

| | how |
|---|---|
| **gating** | a selector is a rule, and §16's rule that matches nothing emits nothing. The chain starves; no *"reference failed"* path exists or is needed |
| **which hop failed** | `<unresolved>` names the *first* step that found nothing, and only the steps at or after it. A starved chain alone does not say where |
| **ambiguity** | `<step_ambiguous>` names the step with two referents, **and only that step** |

The last two reuse §30.6's shapes exactly — a witness plus NAF for failure, an inequality for ambiguity.
**Nothing new was required for selectors**, which is the strongest evidence that reference and selection are one
problem rather than two.

### 31.4 ⚠ TWO DEFECTS, and the second is a correction to §3b

**(a) THE UTTERANCE MUST ENTER DOWNSTREAM OF THE KB, not as a sibling `given`.** Two independent givens are two
*worlds* (§3b), so a rule needing the parse's facts *and* a derived fact cannot be assembled — and when the
missing premise is negated, **its NAF goes vacuously true**: every step was reported unresolved, including the
ones that had resolved. Entering the parse as a **carrier wired below the world** makes it a descendant, hence
joinable, and keeps the utterance distinguishable from the KB (which merging them into one given would lose).
Third time this rule has bitten, and the first time it produced a false report.

**(b) ⭐ ONLY A CARRIER CAN FORK A WORLD.** The comparability test judged worlds by raw reachability, so two
**sibling rules** over the same carrier were called incomparable:

> Under SUBSET OUTPUT, computing anything non-trivial *means* several sibling rules over one carrier — that is
> the normal shape, not an exotic one. **So a rule needing premises from two sibling rules was unassemblable**,
> and if one of those premises was negated its NAF went vacuously true. Measured: the ambiguity rule reported
> *every* step ambiguous, because it never received the inequality facts.

The fix is `Net.carriers` — compare **carrier lineage**, not raw reachability. A carrier emits its view, so it
can add or remove what flows and therefore constitutes a world; a rule emits only its conclusion, so it derives
something new *in* a world without making a new one.

**Every case §3b exists for survives, asserted:** sibling hypotheses still have incomparable carrier sets, and
two independent givens still do. §3b's *"every, not any"* quantifier is untouched — what changed is which units
count as different worlds.

### 31.5 ⚠ SURFACE-SENSITIVITY — the probe that could have sunk it

The hazard: if the expression determines the network, phrasing could determine belief.

- **Belief is INVARIANT under atom order.** Permuting a selector's atoms — same antecedent — gives the identical
  referent. Measured.
- **Meaning changes only under RE-ATTACHMENT.** The naive re-ordering *"the car that is red, parked at…"* →
  *"the car parked at… that is red"* moves which step each `?p` refers to, so it asks for *a car parked at a
  car* and correctly resolves to nothing. **A selector chain is not commutative, because the chain IS the
  attachment structure.**

> **So the line holds, and it can be stated precisely: the expression fixes the TOPOLOGY, the topology computes
> a REFERENT, and the referent is what is believed.** The chain itself is derivational — provenance about a
> reference, not a claim about the world.

### 31.6 THE DUALITY — a reflection with a one-way valve

The chain is **walkable**: following `<narrows>` from the call back to the anchor reads the unfolded expression
off the graph, and each step on that walk carries its own referent, so the walk is an explanation of the
reference hop by hop. Both directions of the mirror already existed — the journal is the network as facts (§27),
authoring is facts as network (§24.7) — and selector chains are where they meet.

**But it is not an isomorphism, and should not be made one.** Instance identity (`SEL#1` vs `SEL#2`) is what
carries scope (§4) and has no counterpart in the graph, so many networks produce one graph and one graph can be
produced by many networks — which is *why* provenance needed its own wire rather than being recoverable from
structure. And the asymmetry is load-bearing: **the assembler reads the parse; the parse never wires.**

### 31.7 What this leaves

- **The terminal call is a REQUEST, as a fact** (`<call> <verb> #wash`, `<call> <target> ?e`), which is the
  recorded shape for a work request. **SUSPEND is still not built**, so nothing executes it — and §20.4 named
  the first suspend as the trigger to revisit the in-node ISA.
- **The parse is hand-written here.** A grammar producing these steps is exactly the front-end §24.7's contract
  was pinned for, and it now has a concrete target: ground step nodes, `<narrows>` links, one template per
  syntactic position.
- **§30.4's derived-removal question is untouched** by any of this and remains the one open decision.

## 32. UNIFORMITY — the principle, its price, and the one exception (user, 2026-07-26)

`bench/spike_selector_chain.py` (26/26), ADRs 0039–0041, **174 green.**

The user asked whether `units/` uses **labelled edges**, and then stated the standing reason for insisting it
should not:

> *"The moment we start creating superstructures — and labelled edges are one — we incur the risk of getting
> into things that do not compose. You might object the reverse is also true: the uniform substrate might create
> the risk of merging things that should be separated."*

### 32.1 THE ANSWER, and both risks are real

**The conflation risk is not hypothetical — this document contains seven instances of it.** Every silent
assembler defect was one mechanism answering two questions: `comparable` answering *lineage* and *world*; the
projection answering *may-this-instantiate* and *what-identifies-this-offer*; predicate where **atom** was meant;
reachability where **world** was meant; *"my chain derives it"* where *"my chain carries it"* was meant. And
`Absent` still conflates *unknown* with *denied*.

**But the two failures are not symmetric, and that is what decides it:**

| | how it fails | how you find it | cost to fix |
|---|---|---|---|
| superstructure | the new mechanism **cannot reach** the old one | when you try to compose — too late | rewrite |
| uniform conflation | the mis-asked question returns a **well-typed answer** | only if you write the probe | one predicate, one atom, one changed test |

Seven silent defects, three or four answer-changing, and **every fix was small.** None was a rewrite; none
invalidated anything already built.

> **A superstructure makes a distinction UNSTATABLE in the substrate. Uniformity makes it STATABLE BUT
> UNSTATED.** The second is recoverable; the first is not.

**And uniformity has repeatedly paid rather than merely broken even:** the uniform predicate slot dissolved three
recorded problems at once (§22.3); inequality dissolved into a derived fact with no new operator (§30.2);
selector chains needed **no new code**, and gating, failure-location and ambiguity came free by reusing the
reference rules unchanged (§31.3); the retraction apparatus dissolved (§7).

**So the answer to *"uniformity risks merging things"* is not *add a superstructure*. It is: MAKE THE DISTINCTION
A FACT AND ASSERT IT** — the same move that dissolved inequality. Which gives a usable line:

> **⭐ GUARDS YES, KINDS NO.** A guard is a check over the uniform substrate and composes with everything. A kind
> is a thing every other mechanism must be taught about, and does not.

The price is specific and has to be paid: **every distinction relied on must be stated in the data and
checkable.** Where that was done it held — the trace/object separation is asserted by a test, the band lattice is
finite by construction, pattern safety is checked at construction. Where it was not, it bit.

### 32.2 ⚠ THE HONEST ANSWER ABOUT FACTS — layout edge-labelled, semantics path-faithful

`Fact(s, p, o)` is stored **atomically**: a 3-tuple, not two adjacency links through an intermediate node. Drawn
on a whiteboard it *is* a labelled edge. An earlier docstring claiming *"S-P-O as a directed path survives
unchanged"* was too generous, and has been corrected in place.

What does survive, in full: roles carried by **position**; the predicate an **ordinary node**, so no separate
label namespace and `?p` a plain variable; and no role-labelled edges on any fact about the world.

**The exception is kept, for DECIDABILITY.** A fact is a single set member, so `Absent` is a *membership test* —
exact, immediate, no fuel (§6a). As a traversable 2-path, *"is P absent"* becomes *"is there no 2-path"*, which
is a join, and the cheap exact negation the whole design leans on would be gone. Value equality and hashing are
trivial for the same reason, and the fixpoint depends on that.

> **AND THE EXCEPTION SHIPS WITH ITS DECOMPOSITION.** The inside of a fact is reachable as ordinary facts through
> `reify` (`<of_s>/<of_p>/<of_o>`). **That is the rule for any future exception: if you break uniformity, ship the
> decomposition with it** — without the escape hatch this would be precisely the island §32.1 forbids.

### 32.3 ⚠ WHERE THE REJECTED SHAPE HAD CREPT BACK — the call node

Three places hang two or more role edges off one node: reification (`<of_s>/<of_p>/<of_o>`), the assembly journal
(`<wire_from>/<wire_to>/<wire_kind>`), and **the terminal call** (`<verb>`/`<target>`).

The first two are *about* facts and wires — structural data, where the flat reification is what makes a derived
rule learner-writable. **The third was different and was mine, not recorded:** a `<call>` node was the recorded
design, its internal shape was not, and a call is **content**, produced by the discourse.

**And n-ary calls are where the pressure genuinely returns** — *"wash the car **with the sponge**"* needs a second
argument, which is the case the original rejection was really about, arriving for COMMANDS rather than for facts.

**THE USER'S DECISION — POSITIONAL ARGUMENTS.** A call is just another discourse node:

```
<call>  <word>  #wash          the lexeme, through the same predicate a mention carries
<call>  <arg1>  <s4>           positional; the argument IS a selector step
<call>  <arg2>  <s7>
```

Measured for two arguments: both resolve, each through its own selector chain, numbered — no `<instrument>`, no
`<patient>`. **`<argN>` names a POSITION, so *direction carries the role* holds one level up:** nothing has to be
taught a role vocabulary, and arity is the only thing anyone must know. Pointing at the **step** rather than the
entity keeps the chain walkable and makes a failed or ambiguous argument visible to the call.

Rejected: **verb-as-predicate** (`<call> #wash ?e`) is path-shaped but strictly binary, and finding all calls
regardless of verb needs a wildcard `?c ?v ?e` — the one pattern the index cannot restrict (§28.3).

**⚠ The honest limit:** `<argN>` is still a label, just a positional one. What it buys is that the label set is
**fixed and content-free**.

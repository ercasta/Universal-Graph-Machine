# Revision 02 — the two planes

**Status: design, 2026-07-27. §6 is BUILT and green — `units/overlay.py`, 10 tests, 40 total.** The rest is
design. This revises `model.md` §6 substantially and amends `revision-01` in three places. `standing.py` still
implements `revision-01` and carries the `Value.graph` + `merges` error §6 corrects; where the two disagree,
the code is wrong.

`model.md` §6 called the **tunnel** the section the architecture exists for. It was doing three unrelated jobs
under one name, and separating them deletes most of it: the seal, the begin/end markers, and the round-trip
invariant all go. What survives of the tunnel is smaller and more honest — the internal decomposition of a
**referring expression** — and it turns out not to be computation at all.

The organising claim underneath is that there are **two planes**, and only one of them is data.

---

## 1. The claim

> **Plane 1 is inert.** Nodes, edges, attributes. Denotational expressions. Also the *descriptions* of
> units — LHS and RHS as subgraphs. Nothing on this plane does anything; it sits there.
>
> **Plane 2 runs.** Units, gates, wires, latched values, energy, the revive. It is wired to plane 1, it
> reads plane 1 at its gates, and its output is applied to plane 1.

The line that carries the weight:

> **Being expressible as a subgraph is not the same as being a unit.**

A unit's LHS and RHS *can* be written as graph structure, and must be, or homoiconicity is false. But that
structure sitting inert in the graph is a **description of** a unit, the way source is not a process. It
becomes a unit when the assembler wires it and the revive powers it.

This is what makes homoiconicity affordable rather than merely required. `model.md` §13 promoted it from
*deferred* to *precondition* on the grounds that "data is the substrate" is false if a live circuit sits beside
the graph. The two planes answer that without collapsing them: everything **persistent** is plane 1, including
the wiring; plane 2 is the running of it.

⚠ **Two framings tried and rejected on the way here**, recorded because both are natural and both are wrong.

- *"A derived fact hangs off its producing unit's node."* This was `revision-01` §9's proposed next
  simplification and it is a **conflation of position with support** — see §3. It also re-commits the error
  §9 itself recorded under *"a contribution is not confined to its producer"*.
- *"A denotation chain is a second species of unit."* Wrong axis. It is not a kind of unit; it is not on
  plane 2 at all.

---

## 2. §6 was three jobs

| what the tunnel was used for | where it goes |
|---|---|
| a statement is **atomic** — nothing may ask *"does the lion see the gazelle?"* | **dissolves.** The antecedent is a unit's LHS **pattern**, and a pattern is not graph data. Nothing to seal, because nothing to observe |
| **scope** — hypotheses, attributed belief, counterfactuals | **support** (§3). A conclusion is inside H because the units producing it are powered by H |
| **unbounded composability** of *"the red car parked at the third floor of the garage near the movie"* | **the tunnel survives here, and only here** — and it is denotation, not scope (§4) |

The seal existed to prevent something from wiring into the middle of a statement and consuming its antecedent
alone. That hazard is real only while the antecedent is *structure in the graph that something could attach
to*. Under `revision-01` it is a standing unit's pattern. A pattern is matched against, never attached to, and
it asserts nothing — so there is no interior to protect.

**What this deletes outright:** begin and end markers, *"only the end marker is attachable"*, the end marker as
output port, and invariant 9. The `model.md` §11 note that *"the price is that the seal is the only thing
making a statement atomic"* is void — the LHS/RHS boundary is what makes it atomic, and it always was.

⚠ **What does not come back:** a rule may freely *match* the inner part of a description (§4), and that is not
a seal violation. Matching is not attaching, and it makes no claim about what the whole expression denotes,
because denotation is now something a rule concludes rather than something position implies. An author can
still write a rule that draws the wrong referent out of a sub-description. That is `model.md` §11 — the engine
is knowledge-agnostic — not a hole where the seal used to be.

---

## 3. Scope is support, not containment

Three things were welded together in `Cell`, and separating them is what makes the rest of this document
possible.

| | what it is | where it lives |
|---|---|---|
| **position** | *where the derived structure is* — the edge goes between the Paul node and the discount node | specified by the **RHS**, in the one graph, at the positions the LHS bound |
| **support** | *what keeps it alive* — powered ⇒ present, unpowered ⇒ absent on the next revive | a relation between the unit and what it produced. **Not a location** |
| **internal structure** | the relationships among the derived nodes themselves — an occurrence, its roles, its fillers | plane 1, built by the RHS |

`Cell` currently serves as position *and* support, and `Cell.within` / `Cell.scope` add containment as a second
axis of position. The correction:

> **A derived fact's position is a position in the world model, specified by the RHS. Scope is not a place it
> sits — it is which configuration powers it.**

The code already computes this: `Network.powering()` walks backwards over the wiring to find the suppositions a
unit's output rests on. `revision-01` §9 already relies on it for blame assignment (*"a contradiction condemns
whatever configuration fed the detector"*), and already states the reason a fact cannot be confined to a box —
`Merge` rewrites every mention graph-wide, so contributions are **recorded per unit and applied to one graph**.
Containment was the leftover.

**This explains a defect rather than merely replacing a mechanism.** `revision-01` §8's third finding — the seal
leaking the *antecedent* to the base world, fixed by adding `Cell.scope` — was not a bug in the seal. It was
scope being represented as a containment field when it is a support relation, and `Cell.scope` was the patch
that made a containment field behave like one.

**Consequences.**

- **`world()` stops being a place and becomes a filter**: what is derived by units not powered by any
  supposition. Arguably more honest, and it costs a backward walk where it used to cost a field read.
- **Invariant 1 (*no rule pattern names a scope*) holds for free**, and more strongly than before: there is no
  scope object for a pattern to name.
- **Invariant 2 (*nesting → tunnel → nesting round-trips*) is deleted.** It was `model.md`'s nomination for
  where silent drift would happen. There is no tunnel to round-trip through, and no mapping to drift.
- `Cell.within` and `Cell.scope` are marked for deletion.

---

## 4. A denotational expression is inert

*"The red car parked at the third floor of the garage near the movie"* is a **subgraph**. It is not a chain of
units, it does not run, and it has no output.

It exists because there cannot be a flat inventory of describable things, so an arbitrarily deep description has
to be **built out of parts** — the practical composability argument, which is a *data-shape* problem, not a
computation problem. Subgraphs nest arbitrarily; that is the whole of what was wanted.

**What resolves it is ordinary rules.** The narrowing — find the movie, the garage near it, its third floor, the
cars parked there, the red one — is computation units matching over inert structure, which is exactly `model.md`
§9's *there is no interpretation stage*. Nothing about it is privileged, and there is no chain the engine sees.

**Its product is an identification, which is an act.** `model.md` §11: deciding that a mental node refers to a
particular real thing is a rule's decision, graded and revisable. `cnl.md` §1: *create, never merge* — the
decision persists and is applied at write-back. So a resolved reference is written by a **regular rule**
(`revision-01` §2), the same disposition as the enumerator's cursor and a recorded refutation.

**And this settles referential vs attributive without new machinery.** The question of whether *"the red car"*
stays that car after it is repainted (referential, Donnellan) or tracks whoever currently satisfies the
description (attributive) is **not a property of the description** — the subgraph is just there. It is decided
by which units are wired to it and which disposition their product has:

| | |
|---|---|
| **referential** | a mutating rule concludes the identification; it is asserted and stays fixed |
| **attributive** | a computation unit holds the reading; it fades and is recomputed when the world changes |

A standing watch (*"tell me when the price drops"*) is the second, which is consistent with `revision-01` §5
already treating a watch as a dangling gate.

**The cardinality discipline is what distinguishes reference from deduction**, and it is worth stating because
it is inverted between them:

| | 0 matches | n matches |
|---|---|---|
| **a unit deducing** | silent, and correctly so — *"a unit that had nothing to say"*, the same silence as `starved` | *n* firings. Normal, nothing to report |
| **resolving a reference** | **reference failure** — reportable | **ambiguity** — reportable |

This is not a second mechanism. It is a property of the *rules that do reference*, which must conclude
positively about failure and ambiguity, exactly as `model.md` §8 requires done-ness to be a positive fact rather
than an absence. `ugm` measured this shape already: gating, failure-location and ambiguity came free from the
selector chains, and *"belief is invariant under atom order — only re-attachment changes meaning."* That was
always a statement about **reference**; `model.md` §6 lifted it into a statement about **scope**, and that lift
is the error this revision unwinds.

**One thing the superseded model got right.** *"Computation is a transient circuit, assembled and thrown
away"* is true of a resolution — it belongs to one utterance. It was over-generalised to everything, and
`revision-01` corrected the generalisation. This recovers the case it was drawn from.

---

## 5. Wires are ordinary occurrences

A wire is a **3-place relation**: source, target, and *which gate*. Under `model.md` §3 an edge is nameless and
carries nothing, so a wire **cannot be an edge at all**. It has to be an occurrence node with role nodes hanging
off it, exactly like `went`.

So there is no separate universe of machinery edges to build. The reified `<wire_input>` node is not a
concession made in order to get homoiconicity; it is the only encoding the substrate permits.

**Invisibility is then free rather than enforced.** `model.md` §4: *nothing is matched implicitly, including
names.* A rule patterning `name = "agent"` does not match `name = "wire_input"` for the same reason it does not
match `name = "likes"` — not because machinery is hidden, but because nothing matches unless a rule says so.
Full homoiconicity becomes the default rather than an opt-in, and it costs nothing until someone writes the rule
that looks.

⚠ **A machinery partition invisible to matching was considered and rejected.** It is a privileged partition, and
`ugm`'s firmware work landed on **no privileged partitions** for reasons that transfer directly. Same trap, one
layer down.

**Separation survives as an index, not as semantics.** Not scanning wire occurrences while matching world
patterns is a perf decision and can be taken without a semantic partition — mechanism, not policy. Semantically
one graph; physically indexed apart if measurement says so.

**This makes plane 2 describable, which is the point.** Units, wires and gates are all plane-1 structure, so
*(axioms, wiring)* in `revision-01`'s invariant 15 is entirely data. The circuit persists because its
**description** persists.

---

## 6. Output is an overlay applied to the graph, read lazily

A unit's output is **not a graph**. It is an **overlay** — a revertable mutation applied to the one graph:
mint a node, add an edge, set an attribute, merge two nodes.

**The current code shows where this went wrong.** `Value` carries `graph: Graph` *and* `merges: tuple` beside
it. `Merge` could not be expressed as a fragment — it rewrites every mention graph-wide — so it was carried
out-of-band and re-applied at read time in `Network._assemble`. **One effect type not fitting the container is
the container being wrong.** `revision-01` §9 argued this in prose and the spike kept the fragment in the type.

Under overlays-as-mutations: `Merge` stops being exceptional, the side channel disappears, and the
union-of-fragments in `_assemble` goes with it.

### Two live values, and the constraint that must survive

⚠ **Applying an overlay must never mean writing the attribute.** `Graph.union` merges attributes *by node*, so
two live derivations disagreeing about one `(node, attr)` collapsed silently — the contradiction vanished
exactly when it mattered. This was `revision-01` §9's design-changing spike finding and this section could
quietly undo it. An overlay that sets an attribute applies a **reified attribution node**. That keeps both
things: one graph, and *"a man under H1, a woman under H2"* coexisting as two nodes rather than one winning.

### Apply on read — the CSS analogy, half of it

CSS does two separable things. It **collects** every declaration matching an element, materializing nothing;
and it **resolves** them to one computed value by specificity. The first is the right implementation strategy.
The second is a precedence policy hardcoded in the engine, which is the judgement `model.md` §11 says must stay
authored — and `revision-01` §9 already rejected it once, as inner overlays shadowing outer ones.

> The test for which half you have built is **what a read returns when two overlays disagree.** A **set** is
> lazy application. A **winner** is the cascade, and the engine has made a judgement.

`Network.readings()` is already the good half: it walks live cells and returns every value with the cell holding
it, deliberately uncollapsed.

What the analogy does buy: CSS's cascade is well-defined because specificity is **declared in the language**.
The composable form of that is a rule concluding precedence — *this overlay overrides that one* — so resolution
is ordinary reasoning. Same shape, authored.

**`Merge` is the case that decides whether lazy is affordable**, and it is the case to benchmark. Mint, edge and
attribute overlays are local, so a read consults a small set. A merge rewrites every mention, so *every* read —
including every read the matcher does, which is most of the inner loop — must consult the merge set and rewrite
as it goes: effectively a union-find on the read path. The same operation that proved fragments wrong is the one
that stresses laziness, which is decent evidence it is the real load-bearing operation in this design.

### Spike results — `units/overlay.py`, 10 green (40 total)

Built 2026-07-27. Every test mutation-checked; four semantic mutations, four kills, and the one perf-only
mutation correctly killed nothing.

| mutation | result |
|---|---|
| `read()` returns the last value — the cascade | kills 4, including the two-live-readings test. **Invariant 16 is discriminating** |
| overlay edges indexed by raw rather than resolved node | kills the every-mention test |
| the root omitted from its own equivalence class | kills the gather-across test — and this was a **live defect**, found by the test rather than planted |
| `SetAttr` applied as a write shadowing the base value | kills 2 — the reified-attribution constraint holds |
| path compression removed | **no kill**, correctly: perf only |

**1. Lazy is affordable, and the margin is not close.** Read cost on a 2,000-node twin as identifications
grow: 0 → 2.21 µs, 100 → 1.99 µs, 1,000 → 3.71 µs. **Merging half the graph costs 1.68× on the read path**,
and the residual is gathering over 2-member classes — inherent to having merged, not to being lazy. The
union-find is effectively free. The open question is closed: **build it lazy.**

**2. The real result is the setup cost, and it is a difference in *order*, not in constant.** Per-revive cost
at a fixed 200 overlays:

| twin | lazy index | eager materialize |
|---|---|---|
| 500 | 0.13 ms | 270 ms |
| 1,000 | 0.13 ms | 508 ms |
| 2,000 | 0.13 ms | 1,050 ms |
| 4,000 | 0.14 ms | 2,566 ms |

**Lazy indexing is flat in twin size; eager materialization is linear in it and still climbing.** That is the
argument made concrete: a revive is already O(circuit) under `revision-01`, and eager application would make
it O(twin) *as well* — the whole persistent world re-walked every turn, whether or not anything touched it.
Some of eager's constant is `Graph`'s immutability (copy-per-effect makes it O(twin × effects) rather than
O(twin + effects)), so a batched eager path would close much of the gap — but not the scaling, which is the
part that matters. Reported honestly: the 18,000× is implementation, the *slope* is design.

**3. The index is load-bearing, not gratuitous.** Naive lazy — scan the live effects on each read, no
precomputed classes — is 547× slower at 10 merges and 3,599× at 100, and diverging. So "read lazily" alone is
not the design; **"index once per revive, read lazily"** is. The index holds nothing across a revive that the
effects do not describe, so this costs invariant 18 nothing.

**4. A correctness argument for laziness that was not anticipated.** Eager application is **order-dependent**:
an `Identify` rewrites only the mentions existing when it is applied, so any later effect naming the dropped
node re-introduces it, and the graph ends up holding a node the system has already decided does not exist
separately. Reversing two effects gives a different graph. Lazy cannot have this bug — there is no moment at
which the rewrite happens. This matters more here than in an ordinary store: effect order within a revive is a
scheduling artifact, and `model.md` invariant 8 explicitly declines to promise reproducibility, so an
order-sensitive application would make the *graph* depend on the scheduler. Pinned by
`test_eager_application_is_order_dependent_and_lazy_is_not`.

**What the spike did *not* test:** overlays produced by actual units (it drives effects directly), the
matcher reading through `Overlays` rather than a `Graph`, and nesting/support. Those are §3's job and are
untouched.

---

## 7. Burns persist, as an authored correction

`revision-01` §4 left this open with a recommendation for **transient** burns, on the grounds that a persistent
burn is engine policy making a durable edit the author never authorized. **Decided the other way**, on a
stronger argument than the one it was weighed against:

> A transient burn means the system re-runs the same pathological loop on **every** turn, surges, burns, and
> forgets — paying for the identical pathology forever. That is not a safe default; it is a guaranteed
> recurring cost.

Persistence stays inside invariant 15: the revive is a pure function of *(axioms, wiring)*, and an unwiring
changes the wiring, so the next revive legitimately differs.

**The authorization objection is answered by where the correction lives, not by making it transient.**

1. the engine only ever **reports** — a surge emits `surged`, a positive fact naming the loop and the wire
   (`model.md` §8);
2. a **rule** wired to `surged` concludes the unwiring;
3. since wires are ordinary occurrences (§5), an unwiring is an ordinary mutation, applied at write-back by a
   **mutating rule** (`revision-01` §2);
4. that rule **ships in the bundle**, the way the always-attended interpretation rules do.

**Build it as a bundled rule now, not as engine policy to be made authored later.** A surge correction is a
reflexive/governance mechanism, which is exactly the class the composability principle says must live on the
substrate — hardcoded in Python it is an unreachable island that later has to be dug out. It costs nothing
extra today, since the engine must emit `surged` either way.

The target state — *reasoning aware of the surge, applying a correction* — is then the day-one architecture
rather than a migration, and the safety mechanism is inspectable and overridable from the start. A wrongly
burned wire is recoverable: `surged` records what happened, and re-wiring is another authored act.

**This is the first instance of something `model.md` already reserved.** Invariant 4 says units never wire
anything and *"if routing is ever learned, units propose wirings as facts."* The burn rule is that slot being
used. Invariant 4 needs the amendment stated in §8 below rather than a repeal.

---

## 8. What this changes

### In `model.md`

| section | change |
|---|---|
| §6 entire | rewritten. Seal, markers, *"only the end is attachable"*, end-marker-as-output-port: **deleted**. Nesting-is-physical becomes support (§3). The tunnel survives only as §4's inert description |
| §5 | a unit's output is an **overlay**, not a graph |
| §11 *"the seal is the only thing making a statement atomic"* | void — the LHS/RHS boundary is |
| §12 invariant 1 | holds, and for free: there is no scope object to name |
| §12 invariant 2 | **deleted** — no tunnel to round-trip through |
| §12 invariant 4 | **amended**: units never wire anything *directly*; a wiring change is a mutating rule's conclusion applied at write-back, and the engine never edits wiring on its own |
| §12 invariant 9 | **deleted** with the seal |
| §13 homoiconicity | **closed** — §1 and §5. It is the default, not an opt-in, and it costs nothing until a rule looks |

### In `revision-01`

| section | change |
|---|---|
| §4, *does the burn persist* | **closed** — yes, and as a bundled rule (§7) |
| §8 finding 3, the seal leak | reinterpreted — not a seal bug; scope was mis-represented as containment (§3) |
| §9, *"a derived fact hangs off its producing unit"* | **withdrawn.** It conflates position with support (§3) |
| §9, *"every effect is an overlay"* | **strengthened and made structural** — the type must carry it (§6) |
| §10, *dissolving `Cell`* | reshaped. `Cell` is a plane-2 record holding plane-1 content, which is why it read as a container. `Cell.within` and `Cell.scope` go; what remains is a runtime record, not a species of data |

### New invariants

16. **A read returns a set, never a winner.** Two live overlays disagreeing about one attribute are two
    readings. If the engine collapses them, the cascade has been built.
17. **No engine code mutates wiring.** Every wiring change — including a burn — is a mutating rule's
    conclusion applied at write-back.
18. **Everything persistent is plane 1.** Plane 2 holds nothing across a revive that plane 1 does not
    describe. Latched values and energy live *within* one stabilization run and do not survive it.
19. **A pattern that does not name machinery never matches machinery** — and for the ordinary reason of
    invariant 7, not because of a partition.

---

## 9. Open

- ~~**Is lazy application affordable?**~~ ✅ **Closed by the §6 spike — yes, and eager is what is not.**
  Merging half a 2,000-node twin costs 1.68× on the read path; eager materialization is linear in twin size
  where lazy indexing is flat. Build it lazy, and **index once per revive** — naive scanning is 3,599× worse.
- **Does the matcher survive reading through `Overlays`?** The spike drives effects directly and never runs
  `solve()` against them. `_solve` iterates `g.nodes` and calls `g.attr`/`g.out`, so the surface is small —
  but a read now returns a *set* of values where the matcher expects one, and what an atom means when a node
  has two live values for the attribute it constrains is **not decided**. Likely the honest answer is that it
  matches under each reading separately and the strength differs, which would make this §4's graded matching
  meeting invariant 16. First thing to build on top of this spike.
- **What a `surged`-triggered correction should actually do.** Unwiring an arbitrary loop element is what the
  detector does today. A rule can be cleverer, and there is no evidence yet about what cleverer means.
- **Does a resolution stand or is it thrown away?** §4 says it is per-utterance and its product is asserted.
  Whether the *resolving units* stand afterwards is not settled, and it feeds the revive-cost question
  directly: an agent that resolves many references accumulates many units that will never fire usefully again.
- **Revive cost**, unchanged from `revision-01` §10 and still the first thing to measure.
- **What the assembler reads.** Plane 1 holds descriptions of units; the assembler builds plane 2 from them.
  The crossing is now the only crossing, which makes it worth specifying exactly — and it is where the
  *"front end targets data, never an engine API"* contract (`model.md` §11) is actually cashed.
- **Attention over machinery.** If wires are ordinary occurrences, they are in principle retrievable by
  System 1. Almost certainly undesirable by default, and the mechanism that prevents it is attention, not a
  partition — but nothing currently says so.

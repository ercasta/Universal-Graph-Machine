# Revision 02 — the two planes

**Status: 2026-07-27. CONSOLIDATED and green — `units/engine.py` + `units/overlay.py`, 52 tests.**
`standing.py` and `turn.py` are **deleted** (§8b); §§3, 5 and 6 are built, §§2 and 4 remain design.
⚠ **Invariant 19 has since been tested and FAILED** — see the invariant, restated. §5's wiring register is
built (`forms_cnl.md` §9 step 1), and building it found §6's bundled rule had never fired. This
revises `model.md` §6 substantially and amends `revision-01` in three places.

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
- `Cell.within` and `Cell.scope` are **deleted** (§8b).

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

What the analogy does buy is narrower than it first looks. CSS's cascade is well-defined because specificity is
**declared in the language** — but the composable form of that is *not* authored precedence.

> **A rule concludes how to solve the conflict.**

⚠ **Not *"a rule concludes precedence."*** That was the first phrasing and it is the cascade smuggled back in
with the specificity function moved into the KB: it presupposes that resolving a conflict means **ranking**,
and it leaves a precedence claim in the graph that something has to consult at read time. Resolution is not
ranking. A rule may conclude that one claim should go, that a third value holds, that the goal should suspend
and ask, or that both stand and the disagreement is itself the answer.

Two things fall out, and the second is the reason to insist on the wording:

- **The engine's entire involvement is reporting the conflict.** It has no resolution mechanism to parameterise
  — not even an authored one.
- **The invariant-7 tension disappears.** Authored precedence would need the read path to consult a
  `supersedes`-shaped relation *by name*, which is a privileged name and invariant 7 gone. If the rule simply
  concludes, nothing is consulted, and the resolution is an overlay like any other.

This is the same shape as §7's burn: **the engine reports, a rule decides what to do about it.** That the two
arrived independently is the evidence the shape is right.

### ⚠ A read yields one value. The first version of this section said "a set", and that was wrong

There are **three** options here, not two, and the draft that shipped to the spike took the wrong one of the
three:

| | |
|---|---|
| pick a winner | CSS's cascade. Engine-hardcoded precedence. Correctly rejected |
| **return a set** | what the spike first built. Also wrong: it *looks* like the principled refusal to pick, but a caller takes the first element and the contradiction disappears exactly as quietly as it did under `Graph.union` — now with the engine's blessing |
| **one value, or a reported conflict** | doesn't pick, doesn't hide |

> **Not picking is not the same as handing the caller a set.**

**And the set was an artifact of ignoring §3.** Scope is *support*, so a read is always relative to a
**configuration** — which units are powered. Two overlays resting on different suppositions are never both live
in one read, so *"a man under H1, a woman under H2"* is not a conflict and never presents as one: reading the
base world sees neither, reading under H1 sees one. Once that is in place, two values in **one** configuration
is exactly what it looks like — an inconsistency.

**A conflicted read is absent, and the conflict is a positive fact.** That is `model.md` §8's discipline (an
outcome is a fact, never an absence) and §9's (contradiction handling is authored). Absent-on-conflict is safe
here in a way it would not be under strong negation: §4 already weakened absence to *"nothing matched above
θ"*, so a conflicted value reading as absent corrupts no claim that was ever made.

**Two independent arguments arrive at the same place**, which is why this is worth being firm about:

- **System 1 reads the overlaid graph.** Retrieval next turn recalls against the graph as it stands after
  stabilization — derived structure present, retracted structure gone. Associative recall over a *set-valued*
  graph is not coherent.
- **The matcher.** `_solve` calls `g.attr` and `g.out`; an atom constrains one value. A set-valued read would
  have forced a decision about what an atom means when a node has two values for it — a question that
  evaporates once a read is configuration-relative.

### Deletion is an overlay

A unit may conclude that something should be **removed**, and that is the fifth effect, not a separate
mechanism. It is also what makes the conflict loop close:

> conflict → a rule matches it → the rule concludes a **retraction** → the next revive reads cleanly.

The engine contributed the *report* and nothing else. Which side goes is authored, which is `model.md` §9's
*"a rule concludes that the stale age fact should go, exactly as a rule concludes anything else"* — and this
settles `decisions/0032` in the form it was actually asked.

The two dispositions apply unchanged: a **computation unit**'s retraction *hides while powered* — no data is
lost and it reverts by the ordinary revive — while a **mutating rule**'s retraction is applied to the asserted
layer at write-back and is real. And a retraction is scoped by its support like any other overlay, so a
deletion inside a supposition does not reach the base world, with no extra machinery.

### Deletion is the only effect that can undermine its own support

Mint, edge, attribute and identify only ever *add*, so a unit can never subtract its own premise. A
deletion can, and that is the one dynamic deletion introduces that the other four do not. Spiked in
`units/turn.py` (9 tests, 54 total), and the answer splits **exactly along the two dispositions**:

| | what happens when a unit deletes its own premise |
|---|---|
| **computation unit** | **oscillates, and surges.** Fires → premise unreadable → does not fire → premise readable again. There is no fixpoint, and the turn reports `surged` naming the unit and the gate |
| **mutating rule** | **self-extinguishes**, as predicted. Turn 1 fires and write-back removes the premise; turn 2 has nothing to fire from, *and nothing was retracted to make that true* |

**The prediction on record — "if the unit deletes its power source, at the next turn it does not
revive" — is right for the mutating rule and wrong for the computation unit**, and the reason is the
write-back boundary. `model.md` §9's *"a deletion is invisible within its own step"* is not merely a
convenience for reasoning hygiene: **it is what makes the self-undermining mutating case terminate.**
Within the turn the deletion is a proposal, the premise stays readable, the fixpoint is reached, and
only then is anything applied. Remove that and the mutating rule oscillates too — which is how the
spike found it, because the first version of the machine let mutating effects into the read view.

So the disposition split is doing load-bearing work a third time: a computation unit's deletion **is** a
read-time effect and is its whole nature; a mutating rule's deletion is an **act on the world**, and an
act has not happened until write-back performs it.

**Three supporting results, each mutation-checked.**

- **A surged turn writes nothing back, and reports no effects.** Whichever phase the detector
  halts on is an artifact of where the scan began. Tested against a cycle whose phases are *both*
  non-empty, because the simple case always halts on the empty phase and cannot tell a principled
  answer from a lucky one.
- **A truncated turn writes nothing back either** — it has conclusions in hand and applies none of
  them. `model.md` §9: write-back happens after stabilization, never during.
- **A computation unit's deletion never reaches the asserted layer.** It hides while powered and is
  re-hidden from scratch every turn.

#### The detector is a flipping gate, and it is local

An earlier version of the machine found the oscillation by comparing whole effect-set states for a repeat.
That is a **global** comparison and `model.md` §2 refuses exactly that — *no work-list running to quiescence,
no output-unchanged termination test*. It is replaced by a local detector on an argument that is a theorem
rather than a heuristic:

> Mint, edge and attribute only ever make more things readable, so within a stabilization run the readable
> set grows **monotonically** and a gate can only go absent → present. **A gate going present → absent is
> therefore proof that a non-monotone effect fired.**

**And the non-monotone effects are two, not one.** `Retract` is the obvious one. **`Identify` is the other**
— merging two nodes that disagree produces a conflict, and a conflict reads as absent (§6). A self-undermining
identification surges by the identical mechanism, which is the evidence that a flipping gate is the *general*
signal rather than a deletion-shaped special case. Pinned by
`test_the_detector_is_not_deletion_specific_identify_surges_too`.

**One flip is normal** — a deletion landed and a downstream unit correctly lost its premise — so the threshold
is on the *count*, and like θ it is a threshold you can be wrong about.

#### They are one mechanism: energy moves from the value to the gate

`revision-01` §4's energy was an **AS-path riding on the value** — the list of every unit it had passed
through, with energy as `path.count(unit)`. That was the answer to a question which only arises when energy
*travels*: a scalar accumulated per hop cannot separate depth from cycling, so the whole history had to be
carried.

**Energy now lives at the gate**, as a count of how many times that gate's input *changed* within the run.
`Value.path` is deleted. The discrimination survives intact, because it was never really about the value:

| | gate energy |
|---|---|
| long acyclic chain (30 deep) | every gate is delivered **once**, so no input ever changes — **zero** energy, whatever the depth |
| powered wiring cycle | one gate's input keeps changing — surges |
| self-undermining deletion | one gate's input keeps flipping — surges, by the identical counter |

So the two triggers were never two. The wiring cycle and the readable-state cycle are the same event seen at
the same place, and a self-deleting unit's invisibility to the old detector was an artifact of energy being
attached to a value that never went round a wire.

**Two things this had to keep, both now pinned:**

- **Count *changes*, not arrivals.** `model.md` §5 — *a repeat arrival is a firing* — so four wires from one
  source fire the unit four times and that is legitimate, not a loop. Counting arrivals is the per-hop
  mistake in new clothes; only counting changes avoids it.
- **Count per *gate*, not per unit.** A unit with one input on a cycle and one on a stable axiom must burn
  the cycling wire. Summing across the unit still surges but makes the quiet input an equally eligible
  victim — `model.md` §8's *"energy on a wire says which chain was expensive"*, holding in the choice of
  what to cut.

**And naming the loop survives without the path.** `revision-01` §4 credited growth-on-revisit with naming
the loop, where a decayed value could not. The loop was never in the value — it is in the topology, and it is
recovered by **walking the wiring backwards**, the same walk `powering()` does. Provenance is the wiring
(`revision-01` §1), so this is that principle paying for something it was not adopted for.

What this buys structurally: **surge is the detector, fuel is the backstop** (`revision-01` §8's second
finding), and the global state-repeat scan is deleted. Pinned by `test_there_is_no_global_quiescence_test`,
which reads the source, because this is the kind of thing that grows back.

#### The correction is a bundled rule, and it is the first thing that *needs* homoiconicity

⚠ **This section said "Built" and it was not — the rule had never fired once.** Found 2026-07-27 while
building the wiring register, which is what §9's build order predicted the register would self-test. Two
independent defects, either of which alone was fatal, and the test that "covered" it asserted only the
engine's half — that `surged` was reported — never that anything acted on it:

1. **the pattern was `surged=None`**, which `Graph.attr` answers for every node that *lacks* the attribute,
   so it matched everything except its target. The matcher has no *"present, any value"* atom; **`AttrVar`
   is one**, because it fails when the attribute is missing. That is the general answer, not a local patch;
2. **`surged` was never on a wire.** The engine wrote it into the read layer, and a unit sees only its gates
   (invariant 3) — so no rule could reach it however good its pattern. The report is now a **cell**
   (`Network.reports`), and it crosses where every other value crosses.

⚠ **And once it fired, it burned itself.** The report accumulates within a turn, so each surge after the
first is a *change* on the corrector's single gate; at `SURGE_AT` the detector burned the corrector, and the
last loop went uncorrected. That is counting **growth** as cycling — the per-hop mistake this section
otherwise avoids. The fix is this section's own monotonicity theorem applied to the value on the wire: **a
strictly larger input is not energy.** It narrows the detector onto the case the theorem covers and pushes
monotone-but-infinite further onto fuel, which §9 already names as fuel's job.

Now genuinely built. The engine's entire involvement is one line: on surge it writes `surged` as a fact **on
the unit's own node** and delivers the report. It does not stop, does not unwire, and does not silence. A
bundled rule matches that fact and concludes the correction; the turn then reaches a fixpoint and completes.

> `bundled:silence` — *anything that surged: stop its output.*

**Three things fell out that were not obvious in advance.**

**1. It needs a unit to be plane-1 data for a reason other than tidiness.** Without a node for the unit there
is nothing for `surged` to be *about*, and the correction has to be engine code. This is §1's homoiconicity
being **used** rather than merely justified — and the first place in the design where it earns its keep.
Removing unit nodes from the graph kills two tests.

**2. There is no new effect kind, and the attempt to add one failed usefully.** `Silence` was first built as a
sixth effect, and it broke immediately: `Overlays` had never heard of it, because **a control decision is not
a graph overlay**. The fix was not to teach the overlay layer about it but to notice `model.md` invariant 4
had already specified the shape — *units **propose** wirings as facts*. Taken literally, the rule concludes
an ordinary attribute on the unit's node and the machine reads it. Effect count stays at five.

**3. A report must persist for the turn; a conclusion must not.** Effects are rebuilt from scratch each round,
so the first version's `surged` fact evaporated on the very next round and no rule could ever match it —
found by the bundled rule silently failing to fire. **A report of something that *happened* is not a
conclusion that has to keep being re-derived**, and the two need different lifetimes inside one turn. This is
the two dispositions appearing at a third scale, within a single stabilization run.

**And the claim is falsifiable rather than decorative.** Remove the bundled rule and the behaviour changes:
the engine reports, nothing handles it, and the turn runs to the budget. If the engine silenced on its own,
the turn would still complete and the rule would be decoration — mutating the engine to do exactly that kills
six tests.

⚠ **The plane interface has a vocabulary, and that is an unresolved tension with invariant 7.** The machine
writes one name (`surged`) and reads one name (`silenced`). Nothing matches implicitly for *rules*, but the
engine itself must know these two words to report and to act on a proposal. This is the same question as
§9's *what the assembler reads* — the plane-1 → plane-2 crossing needs a vocabulary — arriving concretely and
much earlier than expected. It is a small, named, documented interface rather than magic, but it is not
nothing.

⚠ **Two deletions cannot build a cycle between them.** A first attempt at the non-empty oscillation used
two units deleting each other's premises; it **converged**, because deletions only subtract and one unit
falling silent is a self-consistent state. Self-deletion is the only genuine 2-cycle available. That is
worth knowing: the pathology this section is about is *narrow*, not a general instability of deletion.

⚠ **The spike walked into an open question from the other side here.** *Retract Paul's age* is ambiguous
between *that claim* and *that slot*, and a rule resolving a conflict always means the first. The spike names
the **source** — expressible today, and exactly as expressive as what the rule can see, since what it matched
was a conflict naming readings by source. But the only reason a source has to be named at all is that
**asserted and derived facts do not yet wear one shape** (`revision-01` §9's third finding, still open). Once a
base fact is a node like a derived one, this collapses into naming that node.

**`Merge` is the case that decides whether lazy is affordable**, and it is the case to benchmark. Mint, edge and
attribute overlays are local, so a read consults a small set. A merge rewrites every mention, so *every* read —
including every read the matcher does, which is most of the inner loop — must consult the merge set and rewrite
as it goes: effectively a union-find on the read path. The same operation that proved fragments wrong is the one
that stresses laziness, which is decent evidence it is the real load-bearing operation in this design.

### Spike results — `units/overlay.py`, 15 green (45 total)

Built 2026-07-27, then corrected the same day when the set-valued read was rejected. Every test
mutation-checked; nine semantic mutations, nine kills, and the one perf-only mutation correctly killed
nothing.

| mutation | result |
|---|---|
| `read()` picks the last value — the cascade | kills 3 |
| support ignored — scope not read as support | kills 2, including the alternatives-never-meet test |
| `conflicts()` reports across configurations | kills the alternatives test — **the configuration filter is what makes the conflict report meaningful** |
| retraction ignored on the read path | kills the hides-while-powered test |
| retraction ignored for node removal | kills the overlaid-graph test |
| overlay edges indexed by raw rather than resolved node | kills the every-mention test |
| the root omitted from its own equivalence class | kills the gather-across test — and this was a **live defect**, found by the test rather than planted |
| `SetAttr` applied as a write shadowing the base value | kills 2 — the reified-attribution constraint holds |
| path compression removed | **no kill**, correctly: perf only |

**1. Lazy is affordable, and the margin is not close.** Read cost on a 2,000-node twin as identifications
grow: 0 → 3.01 µs, 100 → 3.41 µs, 1,000 → 4.80 µs. **Merging half the graph costs 1.60× on the read path**,
and the residual is gathering over 2-member classes — inherent to having merged, not to being lazy. The
union-find is effectively free. The open question is closed: **build it lazy.** (Adding the configuration
check and the retraction filter cost 36% on the baseline read and did not move the slope — the scaling claim
is about identity resolution, and nothing else on the read path touches it.)

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

**5. A read is 36% dearer once it is configuration-relative, and that is the price of §3.** Support is checked
per candidate. It does not scale with anything, so it is a constant, but it is worth recording that
*scope-as-support is not free* — it moved a cost from a field read on a cell into the read path itself. Cheap,
and paid on every read.

**What the spike did *not* test:** overlays produced by actual units (it drives effects directly), the matcher
reading through `Overlays` rather than a `Graph`, and support computed by walking the wiring rather than
declared. The last is the real gap — `Network.powering()` exists in `standing.py` and the spike takes
configurations as given.

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

16. **A read is relative to a configuration, and yields one value or reports a conflict.** Never a winner
    (the cascade) and never a set (the quieter failure — a caller takes the first element and the
    contradiction vanishes anyway). A conflicted read is **absent**; the disagreement is a positive
    `conflict` fact a rule can match and resolve. See §6.
    *(This list said "a read returns a set" until `review-01` §6 caught it standing against its own §6.)*
17. **No engine code mutates wiring.** Every wiring change — including a burn — is a mutating rule's
    conclusion applied at write-back.
18. **Everything persistent is plane 1.** Plane 2 holds nothing across a revive that plane 1 does not
    describe. Latched values and energy live *within* one stabilization run and do not survive it.
19. ⚠ ~~**A pattern that does not name machinery never matches machinery**~~ — **FALSE, tested
    2026-07-27.** A wire occurrence has an outgoing edge like anything else, so a *generic structural*
    pattern matches it while naming nothing. Invariant 7 buys nothing here. **Restated: machinery has
    to be delivered to a gate before any pattern can see it, and delivering it is a deliberate act** —
    so the barrier is `model.md` §5 (a unit sees only its gates), not naming. Pinned both ways by
    `test_machinery_is_unreachable_unless_something_wires_it` and
    `test_invariant_19_is_false_as_written_and_the_barrier_is_the_wiring`.

---

## 8b. The consolidation — one machine

Three partial machines had accumulated while the design converged, and they did not compose: `standing.py`
(propagating, but reading by unioning graph fragments, with `Cell.within`/`Cell.scope`), `overlay.py`
driven directly with no units, and `turn.py` (fixpoint iteration, no matching). `units/engine.py`
replaces all three. What it settled:

**§3's two halves finally met.** `overlay.py` took a configuration as *declared*; `standing.py` computed
one by *walking wiring*. Joined, the join needs **less** than expected:

> **A unit needs no configuration at all.** It sees only what its gates delivered, and a supposition's
> contributions reach exactly the units wired downstream of it. Scope is not *read* — it is **wiring**.

So `under` appears in `Network.graph()` and never in a unit. `powering()` is what a read filters by; the
tunnel is free, as §6 always promised. `Cell.within` and `Cell.scope` are gone.

**The matcher needed no change.** `match.solve()` touches exactly four members — `nodes`, `attr`,
`degree`, `out` — so `Overlays.view()` exposes those and the matcher runs against overlays unmodified.
A conflicted attribute simply does not match, which needed no special case: a conflicted read is absent.

⚠ **A `turn.py` result is REVERSED, and this is the finding of the consolidation.** §6 recorded that a
computation unit deleting its own premise *oscillates*. It does not — in a **propagating** engine. That
oscillation was an artifact of `turn.py` recomputing every unit's premise from the current view each
round, which conflates the two planes:

> **Power is plane 2; readability is plane 1.** A value that arrived on a wire cannot be un-delivered by
> an overlay that changes what is *readable*. So a deletion cannot withdraw the power that produced it.

`model.md` §5 specifies the propagating engine (*"it sees only what its gates deliver"*), so the
propagating result is the one that counts. The flip detector remains correct and remains needed — for
genuine wiring cycles — and the monotonicity argument behind it is untouched. What is withdrawn is only
the claim that deletion introduces a *new* pathology. Pinned by
`test_deletion_cannot_undermine_its_own_support_in_a_propagating_engine`.

**Two further gaps the port exposed**, both now closed: write-back was never implemented (`mutating`
existed on the unit and `revive()` ignored it), and a node *mentioned* by a live effect was not visible
in a view — so a downstream unit handed only `SetAttr(paul, …)` could not see Paul and the matcher never
tried him.

⚠ **Write-back is the one place effect order still matters.** Reads are lazy and therefore
order-independent (§6 finding 4), but the store is a `Graph` and must be materialized. Identifications
are applied **last**, which is the narrowest fix for the re-introduced-node bug; it is not a general
argument that write-back is order-free.

### Invariant 15, meant literally

`review-01` §4 named the one structural gap: *"if invariant 15 is meant literally, it needs an argument
that latching cannot make a stabilization result order-dependent, and the docs do not have one."*

**Tested, across 144 orderings of a diamond network with a two-gate join** — every permutation of unit
order and wire order — and the readable content is identical in all of them. This is not trivial: the
join fires *repeatedly*, once per arrival, with different partial inputs depending on order (pinned by a
control test). What does not vary is where it settles. Mutating the engine so a unit reads only its most
recently delivered gate breaks it immediately, so the test discriminates.

That is the nearest this design gets to a semantics, and it is now a property rather than a hope.

---

## 9. Open

- ~~**Is lazy application affordable?**~~ ✅ **Closed — yes, and eager is what is not.** Merging half a
  2,000-node twin costs ~1.4–1.7× on the read path; eager materialization is linear in twin size where
  lazy indexing is flat (0.14 ms vs 431→4,222 ms as the twin grows). Build it lazy, and **index once per
  revive**. `tests/units/bench_overlay.py`.
- ~~**Does the matcher survive reading through `Overlays`?**~~ ✅ **Yes, unmodified** (§8b).
- **Does the matcher survive reading through `Overlays`?** The spike drives effects directly and never runs
  `solve()` against them. `_solve` iterates `g.nodes` and calls `g.attr`/`g.out`, so the surface is small, and
  a single-valued configuration-relative read is the shape it already expects — but it must be threaded with
  `under`, and a match must therefore carry the configuration it was made in. **First thing to build on top of
  this spike.**
- **Where does `under` come from?** In the spike it is declared. In the engine it is `Network.powering()`,
  walked backwards over the wiring — so the two halves of §3 have both been built and never yet joined.
- ~~**Are revisit-energy and flip-energy one mechanism or two?**~~ ✅ **One.** Energy moved to the gate,
  `Value.path` is deleted, and the same counter catches both (§6).
- **Monotone-but-infinite is caught only by fuel.** A rule minting a fresh node every round grows forever
  without any gate ever flipping, so no local detector sees it. That makes fuel the *sole* mechanism for a
  real pathology rather than only a backstop for a misconfigured detector — worth stating explicitly,
  because `revision-01` §8 justified fuel on the weaker ground.
- ~~**What should the bundled rule do about a surged gate?**~~ ✅ **Silence the output** — built (§6).
  Minimal, touches no authored wiring, and can only remove claims. ⚠ **Fail-safe, not safe**: a vanished
  conclusion can fire negation-dependent rules on a mechanical absence, the same hazard as invariant 12.
  It is a **containment** that lets the turn complete and report, never a repair.
- **The plane interface's vocabulary.** ✅ **Settled in shape, 2026-07-27.** The engine writes `surged`,
  reads `silenced`, and the assembler reads `<wire>` / `from` / `to` / `gate` / `out`. Five words plus two,
  all constants in one module, none of them privileged in the matcher. What changed is that the report now
  **travels on a wire** rather than being written into the read layer — so the crossing is where every other
  value already crosses, and no new mechanism carries it.
- ~~**What the assembler reads.**~~ ✅ **Closed — it reads the graph.** `Network.assemble()` matches an
  ordinary pattern over `self.asserted`; `wire()` writes the fact rather than owning a list. A circuit can be
  wired by writing graph data alone, and a mutating rule can conclude a wire — invariant 4's *units propose
  wirings as facts*, cashed. ⚠ **`pattern:` is still Python**: the assembler is handed unit objects and
  resolves them by node, so a unit's LHS/RHS is the one part of plane 2 plane 1 does not yet describe. That
  is the remaining half of `forms_cnl.md` §9 step 1.
- **Does a persistent correction differ from a within-turn one?** §7 says burns persist. Silencing as built
  is per-turn containment; the persistent variant is the authored unwiring, and it is unbuilt.
- **Does a conflict need a band?** `Conflict` is currently crisp. Two readings at different strengths is not
  obviously the same event as two readings at equal strength, and §4 says a match has a strength rather than
  a verdict. Undecided, and it is the seam where graded matching meets invariant 16.
- **What a `surged`-triggered correction should actually do.** Unwiring an arbitrary loop element is what the
  detector does today. A rule can be cleverer, and there is no evidence yet about what cleverer means.
- **Does a resolution stand or is it thrown away?** §4 says it is per-utterance and its product is asserted.
  Whether the *resolving units* stand afterwards is not settled, and it feeds the revive-cost question
  directly: an agent that resolves many references accumulates many units that will never fire usefully again.
- **Revive cost**, unchanged from `revision-01` §10 and still the first thing to measure.
- **Attention over machinery.** If wires are ordinary occurrences, they are in principle retrievable by
  System 1. Almost certainly undesirable by default, and the mechanism that prevents it is attention, not a
  partition — but nothing currently says so.

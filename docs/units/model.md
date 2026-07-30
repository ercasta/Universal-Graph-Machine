# The computation model

**Status: current, 2026-07-28.** This is the model as it now stands. It consolidates the original `model.md`
(2026-07-26) with `revision-01-standing-circuits.md` and `revision-02-two-planes.md` (both 2026-07-27), which
now live in `attic/` as the reasoning trail. Nothing here carries `[R1]`/`[R2]` marks any more — where the
three disagreed, this document states only what survived.

**Section numbers are unchanged from the original**, so existing citations in `units/*.py` and in the other
design documents still resolve. §6 is the one that changed subject: it was *statements, seals and tunnels*, and
it is now *the two planes*, because that is what replaced it.

**What is built.** `units/` — `graph.py`, `match.py`, `band.py`, `engine.py`, `overlay.py` — implements
§§1–6, §8's energy and burn, and §9's write-back; 113 tests. §§7 and 10 (the two loops, attention, retrieval)
and the goal machinery in §8 are **design, not code**. Section headers say which.

**How to read it.** Sections are in dependency order; §6 cannot be understood without §5, and §5 cannot be
understood without §3. §10 is a worked example if you would rather see it move first.

| if you want | read |
|---|---|
| why a position was reached, including the wrong turns | `attic/model-superseded.md`, `attic/revision-01-*.md`, `attic/revision-02-*.md` |
| where this sits in the literature | `review-01-prior-art.md` |
| the CNL surface this targets | `cnl.md`, then `forms_cnl.md` |
| what is being worked on now | `STATUS.md` |

---

## 1. The claim  · BUILT

The system holds a **graph of data that persists**, and computes over it by **assembling a circuit that
stands**.

> Data is the substrate. Computation is scaffolding built over it — and the scaffolding **stays**. What is
> thrown away each turn is not the circuit but the **values in it**.
>
> Persistent data is itself the **digital twin** of something outside the system — a real Paul, a real
> codebase, a real invoice. Being stale or wrong is a normal condition, not a fault.

A turn begins by firing from the **axioms** — the facts with no predecessors — and letting the circuit
stabilize. A materialized fact is therefore **recomputed, never maintained**, and it exists for exactly as long
as its unit is powered. Change a premise and the conclusion is not retracted; it simply is not produced next
time.

Three things fall out immediately, and they are the reason to adopt this shape.

**Provenance is free, and it is not data.** The derivation is not written back and stored; it **is** the
wiring. A conclusion is attached to what produced it, so *"why do you believe this"* is a walk, not a lookup.

**Accretion stops.** An early spike found conclusions accreting superlinearly across steps, because every step
wrote its conclusions *and* their derivations as new data. A standing unit holds one output. Re-deriving does
not re-write.

**Retraction machinery is unnecessary.** Here is how much that deletes:

| would have been needed under incremental maintenance | why it is not needed |
|---|---|
| retraction propagation / cascade delete | nothing is retracted. The next revive does not reach it |
| justification sets, in-lists, multiple support | two units producing the same content are two live outputs. *Create, never merge* already guarantees they are structurally distinct, so killing one leaves the other standing with no bookkeeping |
| well-founded support checking | support is a value that arrived on a wire, not a label computed by a solver. Nearly everything hard about truth maintenance is an artifact of labelling, and there is no labelling here |
| detection of ungrounded cycles | a cycle not reachable from an axiom is never powered, so it never fires and never produces anything. It is structurally silent, not detected-and-suppressed |
| delta tracking, invalidation bookkeeping | the graph state is a pure function of *(axioms, wiring)*. There is nothing to invalidate |

The last two rows are the ones to keep in view: **unpoweredness is structural.** That is the property that
makes the whole scheme cheap, and it is what a labelling-based TMS has to pay for with a solver.

**The cost, stated plainly.** Every turn is O(circuit), and the circuit grows monotonically as standing units
accumulate. Incremental revive — firing only from axioms that changed — is available later as a pure
optimisation, and is deliberately **not** taken now, because it reintroduces exactly the bookkeeping the table
above deletes. **Measure before taking it** (§13).

Two further things shape everything else.

**Nothing happens unbidden.** An external event — an utterance, a schedule firing, a tool result — starts a
turn. A goal fires. Absent a goal, the system is silent. There is no drive toward closure, no completion of the
derivable, nothing that runs because it *could*. Sharpened, because the revive fires with no goal asking:

> **No *reasoning* happens unbidden. Re-establishing conclusions already drawn is maintenance, not reasoning.**

That line is what keeps maintenance from growing back into an evaluator.

**Reasoning has two loops, and they are System 1 and System 2** (§7). An associative outer loop retrieves the
rules that *come to mind*; a deliberate inner loop applies them exactly. The outer loop is allowed to be wrong
about relevance. The inner loop is not allowed to be wrong about consequence.

---

## 2. What a unit is not  · BUILT

Two disclaimers, because both are natural readings of "network of computations" and both are wrong here.

**It is not event-driven, and there is no scheduler.** A unit is not a subscriber woken by a message bus. The
assembled network is a **circuit**: values enter at an input, each unit transforms what arrives at its gates,
and output falls out the far end. Closer to ETL, or to logic gates, than to actors.

**It is not a fixpoint engine in the work-list sense.** A revive *is* a run to stabilization, but
**stabilization is bounded by construction**, not by comparing outputs: a gate's energy grows when its input
changes, and crossing the threshold is a **surge** that burns an element of the loop and reports it (§8).
Termination has an argument rather than an assertion — which matters, since an early spike found `band.py`'s
termination argument was void. Acyclicity is not required.

What stays refused is a **global quiescence test**: nothing compares outputs to decide the network is done. An
earlier machine found oscillation by comparing whole effect-set states for a repeat, which is exactly that.
Pinned by `test_there_is_no_global_quiescence_test`, which reads the source, because this is the kind of thing
that grows back.

---

## 3. Data  · BUILT

Everything persistent is one graph:

- **Nodes** are nameless. Identity is the node; there is no lookup by name.
- **Edges** are directed and nameless. An edge says only *this connects to that, in this direction*.
- **Attributes** hang on nodes. Two sorts: **crisp valued** (`age = 42`, `name = "Paul"`) and **gradable**
  (`beautiful`, `little`, `likely`), which carry a degree.

That is the whole inventory. There are no node *kinds* — no `Role` type, no `Lexeme` type, no `Mention` type.
When a distinction is needed it is an attribute something asserts, never a new species of thing other
mechanisms must be taught about.

### Relations are occurrence nodes; roles are intermediate nodes

Because edges are nameless, a relation cannot be an edge — it is a **node**, and each participant hangs off it
through an **intermediate role node**. Role nodes are fresh per occurrence, exactly as two integer variables
holding `7` are still two variables.

Worked, since this is the case that decides the encoding:

> *"Yesterday Paul and Mary went to the park riding bicycles."*

```
e1{name:"went"} ──▶ r1{name:"agent"}       ──▶ n1{name:"Paul"}
                ──▶ r2{name:"agent"}       ──▶ n2{name:"Mary"}
                ──▶ r3{name:"destination"} ──▶ n3{name:"park"}
                ──▶ r4{name:"time"}        ──▶ t1{name:"yesterday"}
                ──▶ r5{name:"means"}       ──▶ n4{name:"bicycle", number:plural}
```

Four things this buys:

- **Arity is unbounded and roles are recoverable.** Adding *"with Sue"* adds a node and two edges. Nothing
  about the existing structure changes.
- **Plurality needs no set node.** *"Paul and Mary"* is two agent role nodes, not a conjunction object. `r1`
  and `r2` are distinct nodes that happen to share `name = "agent"`.
- **Gradability has somewhere to attach.** *"Paul sort-of likes Mary"* grades the `likes` occurrence node.
  *"a very quick trip"* grades `e1`. No edge ever needs to carry a degree.
- **The machinery does not fork.** Nodes and edges are the only two things, so nothing has to be implemented
  twice — once over nodes and once over edges. This is what makes §6 cheap.

⚠ **This reverses an earlier position.** `ugm` held that *direction carries the roles* (subject → predicate →
object) and rejected role labels as engine complexity. That works for arity 2 and fails at 3. Direction now
carries only *outward from the occurrence*; the role node carries which role. The reason for the reversal is
uniformity of machinery, not expressive parsimony.

**A derived claim must be a node, not an attribute write.** Merging attributes *by node* means two live
derivations disagreeing about one `(node, attr)` silently collapse to whichever was applied last — and the
contradiction becomes invisible **exactly when it matters**. Two values for one attribute are not representable
as attributes at all. So an attribution is a thing that is asserted, and therefore a node. Mutation-checked:
reverting to an attribute write kills the contradiction test.

⚠ **Asserted and derived facts must wear one shape, and they do not yet.** Once a derived claim is a reified
attribution, an asserted fact written as a plain attribute is no longer comparable with it, and a rule would
have to match both forms. The boundary must transcribe into the shape rules conclude in. Still open (§13).

---

## 4. Matching  · BUILT

A pattern is matched against the graph by comparing **topology and attributes**, with **graded** comparison
where attributes are gradable. A match therefore has a **strength**, not a boolean verdict.

**Nothing is matched implicitly, including names.** `name` is an ordinary crisp attribute with no privileged
status. Two nodes both named `"Paul"` do *not* match by virtue of that; they match because a rule says
name-equality counts here. This is deliberate: people share names, and *"what is usually true"* must never be
baked into the engine. There is no global similarity metric — similarity is **authored**, per pattern, and
therefore inspectable and overridable.

Three consequences:

- **A firing may inherit its match strength.** *"a little bird"* can conclude *not really a bird*, because
  degree propagates from premise to conclusion. Bands are finite, not continuous.
- **Cheap exact negation is gone.** *"P is absent"* becomes *"nothing matched P above θ"* — a threshold, and a
  threshold you can be wrong about. There is no free set-membership test any more. This is a correction, not a
  loss: the bird case *needs* it.
- **Identifying a role means matching a role name explicitly.** A rule about destinations matches
  `name = "destination"` on the role node. Every such rule says so. The front end (§9) generates the
  boilerplate; the engine grants no shortcut.

**Energy is not a band, and θ never sees it.** A gate carries an energy for cycle detection (§8). It is
plumbing with no epistemic content — the sibling of §11's *"IDs are plumbing"* — and it must never be consulted
by the θ test, or a still-supported conclusion will read as *absent* and fire negation-dependent rules on a
purely mechanical artifact. Deduction is not lossy: a certain premise through a certain rule yields a certain
conclusion, at any depth.

**There is no *"present, any value"* atom, and `AttrVar` is the answer.** A pattern written `surged=None`
matches every node that *lacks* the attribute — which is how a bundled rule once matched everything except its
target (§8). `AttrVar` binds the value and fails when the attribute is missing. That is the general answer, not
a local patch.

---

## 5. Units, gates, firing, and what a unit produces  · BUILT

A **unit** holds a pattern and a transformation. It has **input gates** and one **output**. It sees only what
its gates deliver — there is no ambient store to read, so isolation costs nothing and forbids nothing.

**Units stand across turns, and a partially wired unit is a stable state.** An unconnected gate is not an error
and not an unfinished assembly step: the unit holds, does not fire, and produces nothing. That empty gate does
three jobs at once — it asks (§9's miss), it holds attention (§7), and it is a standing trigger, since a
condition that has not occurred is exactly a gate that has not been filled.

**Gates latch.** A gate retains the last value that arrived on it. When something new arrives on any gate, the
unit fires using the latched values of the others. It does not block waiting for the rest. Latching lives
*within* one stabilization run; nothing latches across a revive.

**A repeat arrival is a firing.** The same value arriving twice fires the unit twice. There is no
value-comparison test suppressing it, and therefore no notion of quiescence.

### The two dispositions

They are not the same thing wearing different clothes, and conflating them is the single easiest way to lose
the design. Both are needed, and the CNL must mark which.

| | what it is | what its effects do |
|---|---|---|
| **computation unit** | stands in the graph permanently, wired to its inputs | produces **overlays** — a function of its inputs, recomputed every revive, gone the moment the input goes. A **thought** |
| **mutating rule** | fires and applies | its effect is merged into the asserted layer at write-back and stays there. An **act** |

> A computation unit does not *do* anything. It **holds** something true for as long as its input holds.
> A mutating rule changes the world and is finished.

**This split is what makes multi-turn search work.** Hypothesis exploration uses computation units, so a
supposition's consequences revert by the ordinary revive — no checkpoint, no copy, no merge-back, and no
problem with nesting. Search *state* — an enumerator's cursor, a recorded refutation — is written by a mutating
rule, so it survives the revive that discards everything else. Neither half works alone. Pinned by
`test_a_mutating_rule_persists_across_revives_and_a_computation_unit_does_not` and
`test_search_state_survives_because_a_regular_rule_wrote_it`.

⚠ **Two dead ends, both argued for and one built.** *"The disposition should be a fact a rule concludes, not a
structural flag"* — rejected; both kinds are needed and the distinction is what the CNL marks. *"Everything is
an overlay, so the asserted layer only grows from outside"* — wrong, and it invents an accumulation problem out
of nothing: it makes the cursor reset every turn and refutations vanish, which is exactly what mutating rules
exist to prevent.

⚠ **Firing a mutating rule underneath a hypothesis writes to the asserted layer for real**, subject to the
write-back support filter (§9). Same hazard as a tool call during exploration: an authoring problem, the one a
lab has when an experiment cannot be undone (§11, the engine is knowledge-agnostic). Not something the engine
should pretend to solve.

### The output is an overlay, not a graph

A unit's output is a **revertable mutation applied to the one graph**. Five effects, and no more: mint a node,
add an edge, set an attribute, identify two nodes, retract something.

**One effect type not fitting the container is the container being wrong.** An earlier version carried a graph
fragment plus an out-of-band merge list, because identification rewrites every mention graph-wide and could not
be expressed as a fragment. Under overlays-as-mutations, identification stops being exceptional and the side
channel disappears.

⚠ **Applying an overlay must never mean writing the attribute** — that is §3's collapse, one level down. An
overlay that sets an attribute applies a **reified attribution node**. That keeps both things: one graph, and
*"a man under H1, a woman under H2"* coexisting as two nodes rather than one winning.

#### A read yields one value, or reports a conflict

There are **three** options here, not two, and the middle one is the trap:

| | |
|---|---|
| pick a winner | CSS's cascade. Engine-hardcoded precedence. Rejected |
| **return a set** | *looks* like the principled refusal to pick, but a caller takes the first element and the contradiction disappears exactly as quietly as before — now with the engine's blessing |
| **one value, or a reported conflict** | doesn't pick, doesn't hide |

> **Not picking is not the same as handing the caller a set.**

**And the set was an artifact of ignoring scope-as-support** (§6). A read is always relative to a
**configuration**. Two overlays resting on different suppositions are never both live in one read, so *"a man
under H1, a woman under H2"* is not a conflict and never presents as one. Once that is in place, two values in
**one** configuration is exactly what it looks like — an inconsistency.

Two independent arguments arrive at the same place. **System 1 reads the overlaid graph** (§7), and associative
recall over a set-valued graph is not coherent. And **the matcher** constrains one value per atom; a set-valued
read would have forced a decision about what an atom means when a node has two values.

**A conflicted read is absent, and the conflict is a positive fact.** That is §8's discipline (an outcome is a
fact, never an absence) and §9's (contradiction handling is authored). Absent-on-conflict is safe here in a way
it would not be under strong negation: §4 already weakened absence to *"nothing matched above θ"*, so a
conflicted value reading as absent corrupts no claim that was ever made.

#### The engine reports; a rule decides

CSS does two separable things. It **collects** every declaration matching an element, materializing nothing;
and it **resolves** them to one computed value by specificity. The first is the right implementation strategy.
The second is engine-hardcoded precedence, which is the judgement §11 says must stay authored.

> **A rule concludes how to solve the conflict.**

⚠ **Not *"a rule concludes precedence."*** That is the cascade smuggled back in with the specificity function
moved into the KB: it presupposes that resolving a conflict means **ranking**, and it leaves a precedence claim
in the graph that something must consult at read time. Resolution is not ranking. A rule may conclude that one
claim should go, that a third value holds, that the goal should suspend and ask, or that both stand and the
disagreement is itself the answer. Two things fall out:

- **The engine's entire involvement is reporting the conflict.** It has no resolution mechanism to
  parameterise — not even an authored one.
- **The invariant-7 tension disappears.** Authored precedence would need the read path to consult a
  `supersedes`-shaped relation *by name*. If the rule simply concludes, nothing is consulted.

⚠ **"A rule can match it" was false until it was fixed.** Conflict detection was a **read-layer** method and
nothing ever put a conflict on a wire, so no unit could see one — identically to `surged` in the other
governance path (§8). Conflicts are now detected after the queue drains and delivered on `Network.reports`, and
the report carries the **names** of the units whose readings disagree, because mentioning a node is not
delivering it. Closing that also needed a drop-by-source effect: a rule must drop *the reading it matched*, not
one its author knew about in advance. Pinned by `test_the_conflict_resolution_loop_closes_in_one_turn`.

#### Deletion is an overlay, and it is the one non-monotone effect

A unit may conclude that something should be **removed**. That is the fifth effect, not a separate mechanism,
and it is what closes the conflict loop:

> conflict → a rule matches it → the rule concludes a **retraction** → the next revive reads cleanly.

The two dispositions apply unchanged: a **computation unit**'s retraction *hides while powered* — no data is
lost and it reverts by the ordinary revive — while a **mutating rule**'s retraction is applied to the asserted
layer at write-back and is real. A retraction is scoped by its support like any other overlay.

**Deletion cannot undermine its own support.** A propagating engine settles this:

> **Power is plane 2; readability is plane 1.** A value that arrived on a wire cannot be un-delivered by an
> overlay that changes what is *readable*.

An earlier fixpoint-style machine recomputed every unit's premise from the current view each round and
concluded that a self-deleting computation unit *oscillates*. It does not, in a propagating engine — that was
an artifact of conflating the two planes. The mutating case terminates for a different reason: within the turn
a deletion is a *proposal*, the premise stays readable, the fixpoint is reached, and only then is anything
applied. **§9's *"a deletion is invisible within its own step"* is not merely reasoning hygiene — it is what
makes the self-undermining mutating case terminate.** Pinned by
`test_deletion_cannot_undermine_its_own_support_in_a_propagating_engine`.

#### Lazy, indexed once per revive

Measured on a 2,000-node twin. Read cost as identifications grow: 0 → 3.01 µs, 100 → 3.41 µs, 1,000 → 4.80 µs
— **merging half the graph costs 1.60× on the read path**, and the residual is gathering over 2-member classes,
inherent to having merged rather than to being lazy.

The real result is the **setup** cost, and it is a difference in *order*, not in constant. Per-revive at a fixed
200 overlays:

| twin | lazy index | eager materialize |
|---|---|---|
| 500 | 0.13 ms | 270 ms |
| 1,000 | 0.13 ms | 508 ms |
| 2,000 | 0.13 ms | 1,050 ms |
| 4,000 | 0.14 ms | 2,566 ms |

**Lazy indexing is flat in twin size; eager materialization is linear in it and still climbing.** A revive is
already O(circuit); eager application would make it O(twin) *as well* — the whole persistent world re-walked
every turn, whether or not anything touched it. Some of eager's constant is `Graph`'s immutability, so a
batched eager path would close much of the gap — but not the scaling. Reported honestly: the 18,000× is
implementation, the **slope** is design.

**The index is load-bearing, not gratuitous.** Naive lazy — scan the live effects on each read — is 547× slower
at 10 merges and 3,599× at 100, and diverging. So *"read lazily"* alone is not the design; **"index once per
revive, read lazily"** is. The index holds nothing across a revive that the effects do not describe, so it
costs invariant 18 nothing.

**A correctness argument for laziness that was not anticipated.** Eager application is **order-dependent**: an
identification rewrites only the mentions existing when it is applied, so any later effect naming the dropped
node re-introduces it, and the graph ends up holding a node the system has already decided does not exist
separately. Lazy cannot have this bug — there is no moment at which the rewrite happens. This matters more here
than in an ordinary store, because effect order within a revive is a scheduling artifact and invariant 8
explicitly declines to promise reproducibility. Pinned by
`test_eager_application_is_order_dependent_and_lazy_is_not`.

**Identification is the case that decides whether lazy stays affordable**, and it is the case to keep
benchmarking: every read the matcher does must consult the merge set, effectively a union-find on the read
path. The same operation that proved fragments wrong is the one that stresses laziness — decent evidence it is
the real load-bearing operation in this design.

**The matcher needed no change.** It touches exactly four members — `nodes`, `attr`, `degree`, `out` — so the
overlay view exposes those and the matcher runs unmodified. A conflicted attribute simply does not match, which
needed no special case: a conflicted read is absent.

### Consequences, stated plainly because two of them are costs

- A cycle is legitimate and iterates. Depth is assembled, not pre-wired. ⚠ But see §7 — because the outer loop
  is tight, **cycles inside a circuit may turn out to be nearly unnecessary**, and if that holds, latching and
  refire-on-repeat stop being load-bearing and this section gets simpler. A prediction to test, not a settled
  requirement.
- **A unit is stateful and order-dependent within a run.** Because gates latch, a firing depends on the order
  arrivals came in, so `output = f(inputs)` is false per firing. What does *not* vary is where the run settles
  — tested across 144 orderings of a diamond network with a two-gate join, every permutation of unit order and
  wire order, identical readable content in all of them. The join fires *repeatedly*, once per arrival, with
  different partial inputs depending on order, and a control test pins that; what does not vary is where it
  lands. Mutating the engine so a unit reads only its most recently delivered gate breaks it immediately, so
  the test discriminates. **That is the nearest this design gets to a semantics, and it is a property rather
  than a hope** (invariant 15).
- **A loop dies by running out of data, by fuel, or by surging.** It does *not* die by settling. A monotone
  rule fed the same value forever produces the same conclusion forever, quite happily.

---

## 6. The two planes, and scope as support  · BUILT

This section replaces the original §6, which called the **tunnel** the thing the architecture existed for. It
was doing three unrelated jobs under one name, and separating them deletes most of it.

> **Plane 1 is inert.** Nodes, edges, attributes. Denotational expressions. Also the *descriptions* of units —
> pattern, effects and wiring, as subgraphs. Nothing on this plane does anything; it sits there.
>
> **Plane 2 runs.** Units, gates, wires, latched values, energy, the revive. It is wired to plane 1, it reads
> plane 1 at its gates, and its output is applied to plane 1.

The line that carries the weight:

> **Being expressible as a subgraph is not the same as being a unit.**

A unit's pattern and effects *can* be written as graph structure, and must be, or homoiconicity is false. But
that structure sitting inert in the graph is a **description of** a unit, the way source is not a process. It
becomes a unit when the assembler wires it and the revive powers it.

This is what makes homoiconicity affordable rather than merely required. It is not optional: §1's claim that
data is the substrate is false if a live circuit sits beside the graph. The two planes answer that without
collapsing them — everything **persistent** is plane 1, including the wiring; plane 2 is the running of it.

⚠ **Two framings tried and rejected on the way here.** *"A derived fact hangs off its producing unit's node"* —
a conflation of position with support, below. *"A denotation chain is a second species of unit"* — wrong axis;
it is not a kind of unit, it is not on plane 2 at all.

### What the tunnel was, and where each job went

| job | where it goes |
|---|---|
| a statement is **atomic** — nothing may ask *"does the lion see the gazelle?"* | **dissolves.** The antecedent is a unit's **pattern**, and a pattern is matched against, never attached to. Nothing to seal, because nothing to observe |
| **scope** — hypotheses, attributed belief, counterfactuals | **support**, below. A conclusion is inside H because the units producing it are powered by H |
| **unbounded composability** of *"the red car parked at the third floor of the garage near the movie"* | the tunnel survives here and only here — and it is **denotation**, not scope (§9) |

**Deleted outright:** begin and end markers, *"only the end marker is attachable"*, the end marker as output
port, the seal, and invariants 2 and 9. The old note that *"the price is that the seal is the only thing making
a statement atomic"* is void — the pattern/effect boundary is what makes it atomic, and it always was.

⚠ **What does not come back:** a rule may freely *match* the inner part of a description, and that is not a
seal violation. Matching is not attaching, and it makes no claim about what the whole expression denotes,
because denotation is something a rule concludes rather than something position implies. An author can still
write a rule that draws the wrong referent out of a sub-description. That is §11 — the engine is
knowledge-agnostic — not a hole where the seal used to be.

### Scope is support, not containment

Three things were welded together in the old `Cell`, and separating them is what makes the rest possible.

| | what it is | where it lives |
|---|---|---|
| **position** | *where the derived structure is* — the edge goes between the Paul node and the discount node | specified by the **effects**, in the one graph, at the positions the pattern bound |
| **support** | *what keeps it alive* — powered ⇒ present, unpowered ⇒ absent on the next revive | a relation between the unit and what it produced. **Not a location** |
| **internal structure** | the relationships among the derived nodes themselves | plane 1, built by the effects |

> **A derived fact's position is a position in the world model. Scope is not a place it sits — it is which
> configuration powers it.**

`Network.powering()` walks backwards over the wiring to find the suppositions a unit's output rests on. A fact
cannot be confined to a box in any case: identifying two nodes rewrites every mention of them graph-wide, so
contributions are **recorded per unit and applied to one graph**. Containment was the leftover.

**And a unit needs no configuration at all.** It sees only what its gates delivered, and a supposition's
contributions reach exactly the units wired downstream of it.

> **Scope is not *read* — it is wiring.**

So `under` appears in the read path and never in a unit, and the tunnel is free.

**Consequences.**

- **The world stops being a place and becomes a filter**: what is derived by units not powered by any
  supposition. More honest, and it costs a backward walk where it used to cost a field read. Measured at 36% on
  the baseline read — *scope-as-support is not free*, but it is a constant and does not scale with anything.
- **Invariant 1 (*no rule pattern names a scope*) holds for free**, and more strongly than before: there is no
  scope object for a pattern to name.
- **Invariant 2 (*nesting → tunnel → nesting round-trips*) is deleted.** It was the original model's nomination
  for where silent drift would happen. There is no tunnel to round-trip through, and no mapping to drift.

**This explains a defect rather than merely replacing a mechanism.** An early spike found the seal leaking the
*antecedent* to the base world, and fixed it by adding a containment field. That was not a bug in the seal — it
was scope being represented as containment when it is a support relation, and the field was the patch that made
containment behave like support.

### Alternatives are not contradictions

Several hypotheses may be live at once, and their conclusions **coexist physically in the graph**. *"Paul is a
man"* and *"Paul is a woman"* under two suppositions are two alternatives, not a conflict. This is what makes
contradiction detection an ordinary rule: the conflicting claims are *there*, to be matched.

### A contradiction refutes the configuration that powered it

Reductio is the main case, not a special one. A detector wired to a **single** hypothesis that derives both *P*
and *¬P* refutes that hypothesis — there is no "wired to both".

> A contradiction condemns **whatever configuration fed the detector**. That configuration is not something a
> rule asks about — it is read off the wiring by walking backwards.

So no rule names a scope and blame assignment is provenance doing real work. Feeding one detector from two
suppositions asserts their *conjunction*, and reporting a contradiction there is correct. Which of the blamed
assumptions to discard is a further **rule's** judgement, not the engine's — base axioms simply are not
discardable, so in the ordinary case only one candidate remains.

⭐ **Reductio needs no support-breaking machinery.** A conflict arising only under H is reported with an
`under:` role naming H — while the report itself travels on `reports`, whose support is **empty**. So a rule
wired to it is in the **base world** and its conclusion stays there. That is right rather than a loophole:
*"H leads to a contradiction"* is a fact about the reasoning, not a fact inside the hypothesis. `powering()` is
untouched.

### The enumerator

Round-robin over hypotheses, one powered per turn, gives search — and abduction — with no new mechanism. Two
things it depends on, both instances of §5's split: **the cursor must be asserted data**, advanced by a
mutating rule (a cursor held as a derived fact resets to the first hypothesis every revive); and **a refutation
must cross to an axiom**, or it dies with the hypothesis it refutes and the search becomes amnesiac.

**A checkpoint is copy-on-write for free**, incidentally — `Graph` is immutable, so a mutating rule *replaces*
a cell's value rather than editing it, and divergence happens only where a write lands. That immutability
decision was adopted as *load-bearing, not hygiene*, and it pays here for something it was not adopted for.

⚠ **Elimination proves nothing unless the enumeration is exhaustive**, and the engine cannot know that — it is
a knowledge claim (§11). The survivor of an elimination is **un-refuted**, never **proven**: the same weak,
honest claim as `starved` ≠ underivable.

### Wires are ordinary occurrences

A wire is a **3-place relation**: source, target, and *which gate*. Under §3 an edge is nameless and carries
nothing, so a wire **cannot be an edge at all**. It has to be an occurrence node with role nodes hanging off
it, exactly like `went`.

So there is no separate universe of machinery edges to build. The reified wire node is not a concession made in
order to get homoiconicity; it is the only encoding the substrate permits.

**Invisibility is free rather than enforced.** A rule patterning `name = "agent"` does not match
`name = "wire_input"` for the same reason it does not match `name = "likes"` — not because machinery is hidden,
but because nothing matches unless a rule says so (§4).

⚠ **A machinery partition invisible to matching was considered and rejected.** It is a privileged partition,
and `ugm`'s firmware work landed on **no privileged partitions** for reasons that transfer directly. Same trap,
one layer down. Separation survives as an **index**, not as semantics: not scanning wire occurrences while
matching world patterns is a perf decision, taken without a semantic partition. Semantically one graph;
physically indexed apart if measurement says so.

### A unit is describable entirely

The assembler reads the graph. `Network.assemble()` matches an ordinary pattern over the asserted layer, and
`wire()` writes the fact rather than owning a list — so a circuit can be wired by writing graph data alone, and
a **mutating rule can conclude a wire**. That is invariant 4's *units propose wirings as facts*, cashed.

Three registers, all read from the graph each revive, each falling back to what was authored in Python when
nothing describes it:

| register | holds | encoding |
|---|---|---|
| **wiring** | what feeds what | `<wire>` occurrence with `from` / `to` / `gate` |
| **`pattern:`** | what a unit looks for | `<pattern>` holding conjuncts; `<atom>` holding constraints and sub-atoms; `<constraint>` carrying `key` plus one of `value` / `attrvar` / `graded`; `<absent>` for a negative conjunct |
| **`effect:`** | what a unit concludes | one node per template, `name` says which (`<emit>` `<attribute>` `<stamp>` `<link>` `<merge>` `<drop>`), attributes carry the fields, an `<emit>`'s roles hang off `out:` |

`out:` is the one containment relation throughout, and what a described node **is** comes from its `name`,
matched explicitly like every other fact — so the register bought two whole sub-languages for one role.

**Derived, not owned.** Without the fallback, deleting a description would leave the last pattern read still
running — the defect the wiring register exists to remove, one level in. So *(axioms, wiring)* in invariant 15
now includes the units' patterns and effects.

⭐ **A rule could not connect two nodes it minted, and that was the real blocker.** Every filler in every effect
template was a node the *pattern* had found, so a rule could point at anything the match discovered and at
nothing it had just created — two emissions produced two disconnected occurrences. That is on the critical path
twice: a pattern as data needs atom →`out:`→ atom, and both atoms are minted by the rule writing it; and a
conditional needs the `when:` link between two claims, neither of which exists until the interpretation rule
mints it. So *a rule writes a rule* was impossible **independently of** how patterns are reified — reification
would have produced an inventory of parts with nothing able to assemble them.

**The fix adds no kind and no privileged namespace.** The pattern has variables; give the effects **names**.
Binding a minted occurrence as `as_="a1"` makes it nameable by any later effect of *that firing*, which needs
the effects of a firing to be instantiated **together**, sharing one binding map, instead of one template at a
time. One namespace per firing, and three ways to get it wrong **raise** rather than resolve: an `as_`
shadowing a pattern variable, an `as_` minted twice, and a forward reference. The alternative in every case is
a rule that silently builds half a structure, or points the second half at the first.

⚠ **Reading refuses where assembling skips, and the asymmetry is the point.** `assemble()` skips a wire naming
something unbuilt, because a missing wire is a *smaller* circuit — visible, and it fails safe. A dropped
constraint is the opposite: the pattern matches **more** than its author wrote, silently. So an unreadable
member raises, two descriptions on one unit raise rather than conjoin, and a described conjunction with **no**
conjuncts raises — an empty pattern matches vacuously, so a truncated description would fire its unit on
everything. An authored `()` stays legal: a Python author can mean it, a half-written description cannot. Same
on the effect side, and sharper: a dropped emission makes a unit conclude *less*, a dropped deletion makes the
graph read **more**, because deletion is the one non-monotone effect (§5). A truncated template raises.

⚠ **Order is load-bearing for effects in a way it is not for patterns.** Conjunct order matters only to a
negative conjunct; effect order decides whether a name resolves at all. Mint order carries it, and a described
right-hand side read out of order is a *different rule* — for a forward reference, one that raises.

⭐ `test_a_rule_writes_a_whole_rule_with_nothing_authored_in_python` starts from a shell — a name and a gate,
no pattern, no effects — and a mutating rule concludes its pattern, its effects and its wire; next turn it runs
and concludes about the world. **There is no longer any part of a unit that only Python can say.**

⚠ **Tier 0 grew from five roles to six, and that is the finding.** `forms_cnl.md` §6 declares tier 0 closed at
five, designed a priori. The five describe *wiring*; describing a whole **unit** was a job the register was
never sized for. Recorded rather than absorbed, because it is the cheapest kind of evidence there is: *designed
a priori* means designed before anything used it, and the first real use added a role. What did **not** grow is
the encoding underneath.

⚠ **The plane interface has a vocabulary, and it is an unresolved tension with invariant 7.** The engine writes
`surged`, reads `silenced`, and the assembler reads `<wire>` / `from` / `to` / `gate` / `out`. Nothing matches
implicitly for *rules*, but the engine itself must know these words to report and to act on a proposal. A
small, named, documented interface rather than magic — but not nothing.

⚠ **Machinery is not protected by naming.** A wire occurrence has an outgoing edge like anything else, so a
*generic structural* pattern matches it while naming nothing. The barrier is that machinery must be
**delivered to a gate** before any pattern can see it, and delivering it is a deliberate act (invariant 19,
restated).

---

## 7. The two loops  · DESIGN; a first RETRIEVE prototype built — `units/system1_experiment.py`

A turn is a sequence of **steps**. Each step is:

```
1. RETRIEVE   given the current data (including the goal), which rules come to mind?
2. ASSEMBLE   mint units for them, wire them by the ordinary policy
3. RUN        the circuit revives and stabilizes, bounded by fuel
4. WRITE BACK mutating conclusions become asserted data
```

and then the next step retrieves against the data step 3 produced. This is the outer loop.

**Step 1 is System 1.** Associative, approximate, not rationally controlled. Subgraph similarity — the same
graded matcher of §4, doing recall instead of application — or any other associative mechanism. It is allowed
to be incomplete and allowed to be wrong; the cost of a wrong suggestion is a wasted step. `units/system1_experiment.py`
is a first, minimal prototype: attribute-key-overlap resemblance, scoped to an attended region (BFS outward from
a seed), proposing wires directly (not a new engine mechanism — `Network.wire()`, decided by score instead of by
hand). Confirms "allowed to be wrong" concretely — a candidate can be wired on a crude resemblance and then
simply fail to fire once matched exactly, which is the wasted-step cost stated above, not a wrong *answer*. Also
surfaced that the outer driver has no tunnel of its own: unlike a `StandingUnit` (which only ever sees its
gates), the retrieval code reads `Network.wires`/`.asserted` directly, so avoiding re-wiring an already-wired
candidate is a plain Python check — none of `goal_machinery.md` §3's axiom-lifecycle discipline is needed at
this layer, only inside units.

**It is also non-deterministic, deliberately.** The same data and the same goal may bring different rules to
mind on different occasions, so two runs of the same turn may reason differently and reach different places.
This is not a defect to be engineered out — it is what happens to people, and it is acceptable in an agent. It
does mean nothing downstream may assume reproducibility (invariant 8).

**Step 3 is System 2.** Deliberate, exact, bounded.

> **Retrieval may be approximate; application must be exact.**

This is also what dissolves the apparent regress. Deciding *which* rules are relevant looks like it needs
reasoning, which would need a network, which would need deciding which rules are relevant. It doesn't:
relevance is **retrieved by resemblance**, not computed. And if a genuinely deliberate choice about relevance
is wanted, it happens as an ordinary step whose output is data — *"use rule R for goal G"* — which the next
step's retrieval reads. No meta-level.

**The outer driver does no semantics.** It retrieves, wires, runs, and writes. It does not match, decide,
scope, or interpret. Every judgement lives inside a unit. That line is load-bearing: erode it — make the driver
"smart about relevance" — and you have rebuilt the central machine this design exists to escape.

### The price: no completeness

Fuzzy, non-exhaustive retrieval means **a rule that would have applied may simply never come to mind.** That is
correct for an agent and it is what bounds the cost, but it changes what silence means:

> Silence does not mean *"not derivable."* It means *"nothing came to mind."*

The system must say the second, in the data, so that a later step — or a person — can answer *"what about R?"*,
which is then a retrieval hint: ordinary data, no new mechanism.

### Attention bounds retrieval, and a dangling gate is what holds it

Application is bounded by wiring — a unit sees only its gates. Retrieval has no such bound: associative recall
against the whole twin is exactly what cannot be afforded.

> **Attention bounds retrieval, not application.** System 1 recalls against the attended region of the graph,
> never the whole of it.

This does two jobs. It makes retrieval tractable, and it makes retrieval's incompleteness *principled* rather
than a shrug — *"I only considered what I was attending to"* is a statable reason, the same shape as the
`starved` fact. Attention is data, so a rule can conclude *attend to X*, and a retrieval hint is just an act of
attention.

> **A dangling gate holds attention on its region.**

This *derives* what would otherwise be stipulated. A pending goal **is** an unsatisfied satisfaction condition,
which is a dangling gate, which holds attention — so goal-pinning stops being a special case. Four things
collapse into one shape:

| | |
|---|---|
| an unwired premise | a gate with nothing on it |
| a pending tool call (§9) | a gate that will be filled later |
| a starved gate emitting a miss (§9) | the same gate, asking |
| a pinned pending goal | the same gate, holding attention |

System 1's job widens accordingly: it proposes **wirings**, not only rules. That needs no amendment —
invariant 4 already reserves the slot.

**Read from the other end, the same structure is a standing watch.** *"Tell me when the price drops"* and
*"watch out not to do this while you proceed"* are units wired to a condition that has not occurred, needing no
monitor mechanism, no subscription, and no periodic check. The prohibition reading matters because §4 removed
cheap exact negation: *"do not do X"* is **not** implemented by testing that X is absent — a θ threshold that
can be wrong — but by **waiting for X to be present** and firing an alarm. Negative constraint, positive
trigger; the same move §8 makes for outcomes.

**The Zeigarnik correspondence.** Lewin's account is that an incomplete task maintains a tension system that
keeps it accessible, and completing it discharges the tension. An unfilled gate exerts pull; the gate fills,
the unit fires, there is no longer a dangling gate, and the pull ends — discharge is not a separate mechanism,
it is the disappearance of the thing that was holding. Two honest qualifications: the empirical effect
replicates unevenly and is moderated by involvement and by expectation of completion, so this is a
*correspondence*, not evidence — the mechanism stands on the unification regardless. And the correspondence is
imperfect in a way that points at a real problem: people eventually forget uncompleted tasks, whereas a
dangling gate as specified holds attention **forever** (§13, the attention leak).

**Linguistic competence must be attended even when nothing is.** At the start of a turn attention holds almost
nothing: a transcribed utterance and a fresh goal. System 1 has to surface the interpretation rules out of that
near-empty state or comprehension stalls before it begins. So the bundled interpretation rules are
always-attended in a way domain knowledge is not — a principled asymmetry, not a hack, and the same asymmetry
people have.

**Decay must consult attention-holding facts, not age.** Not every long-lived dangling gate is abandoned
business — some are deliberately standing prohibitions, and a decay policy that cannot tell a forgotten subgoal
from an active guardrail will silently drop the guardrail. That distinction is **data**: a rule concludes that
something is to be kept attended, exactly as it concludes anything else.

⚠ **This reverses a `ugm` finding, and the reversal is the point.** `ugm` built associative recall and
concluded it must be **explicit, never auto-fired**: auto-firing on a demand miss flipped negation-as-failure
and was self-reinforcing. Here recall fires automatically on every step. The hazard is the same; the fix is
opposite. `ugm` banned auto-fire to protect a strong negation; this design **weakens the negation instead**, so
there is no longer a strong claim for recall to corrupt. The self-reinforcement half is *not* resolved (§13).

### Why the loop is tight

Steps are fine-grained — one step fires whatever came to mind, not a phase of work. Three consequences are
load-bearing:

- **Relevance tracks the evolving state.** Coarse steps judge relevance once and then derive a great deal under
  that judgement, by which time the data it was judged against is gone. Re-retrieving after each small
  inference is the mechanism of *one thought leading to another*: what this step concluded is what the next
  step notices.
- **Control lives outside the circuit.** Coarse steps force branching and iteration *into* the network. Fine
  steps supply control from outside — the sequence of what gets retrieved next *is* the control flow. This is
  what makes the circuit small.
- **Interruptibility.** Step granularity *is* responsiveness granularity: new input can only be taken into
  account at a step boundary, so a coarse step is an opaque block the agent cannot be steered out of.

**The cost, stated plainly.** Fine grain trades inner-loop work for outer-loop work, and the outer loop is the
expensive one: retrieval runs on every step. Attention is the mitigation, but where the optimum sits is
empirical and worth measuring early — because if retrieval proves expensive the pressure will be to coarsen
steps, and coarsening gives back all three gains. Second-order: each step contributes a non-deterministic
retrieval, so a long chain of fine steps has more variance in where it lands than a short chain of coarse ones.
Goal-pinning is what keeps that from becoming a wander.

**Think-harder is random restart.** Fixation — the attention leak, and self-reinforcing recall — is answered by
allowing **randomised refocus when thinking harder**. This is PageRank's random-surfer damping, which exists to
solve the identical pathology, and it is the same *diversity rather than top-k* mitigation, triggered by effort
level rather than run continuously, so it costs nothing when nobody asked. Two constraints: sample **outward
from what is attended**, a hop or two, never uniformly over the twin (uniform sampling is the thing attention
exists to prevent); and **record what was granted**, or a turn becomes unexplainable, which is the one thing
provenance-as-wiring was supposed to guarantee.

**Recorded, not yet built — asynchronous System 1.** Retrieval can run concurrently, keeping a buffer of
candidate rules filled ahead of the step that needs them, taking it off the critical path. This is *licensed*
rather than merely fast: a stale buffer trades away no property that was ever claimed, because retrieval is
already incomplete and non-deterministic. The same trick is forbidden for System 2, where application must be
exact — a useful check that the asymmetry is cut in the right place. Four notes for when it is built: **age
candidates** (each carries the attention state it was retrieved under) rather than invalidating on a threshold;
keep the buffer **diverse rather than top-k**, which is also the mitigation for self-reinforcement; **record
the buffer's contents in the derivation**, so a timing-dependent turn stays explainable even though it cannot
be replayed; and if it prefetches *data*, **speculate reads, never actions** — that line belongs in the
boundary, not in a rule's judgement. Do not build it before synchronous retrieval exists and is measurably
slow: every parameter in it depends on measurements that cannot be taken yet.

---

## 8. Goals, termination, energy and the burn  · PARTLY BUILT (energy and the burn are; goal lineage is
designed and worked-example-verified, not yet a standing rule bank — see `goal_machinery.md`)

### A goal is data

A goal is a node carrying a description of **what would satisfy it**. It has to be data: it is persisted across
a suspension, and rules must be able to produce subgoals.

Plan, step, subgoal, and expectation are all the same shape — a description of a satisfaction condition — which
is why *"fix the `computeAccrual` function"* decomposes uniformly: rules turn the goal into a plan, the plan's
steps are goals, each step's expectation is that step's satisfaction condition, and checking one is an ordinary
rule match. Nothing about "plan" is a new kind of thing.

### Done is a fact, never an absence

The temptation is to say a step ends when the network stops producing. That conflates five different outcomes.
Each is a **positive fact**:

| fact | meaning | next |
|---|---|---|
| `satisfied` | a rule matched the goal's own satisfaction condition | stop; the answer is in the data |
| `starved` | nothing came to mind, or nothing matched | *not* "underivable" — see §7 |
| `out_of_fuel` | the inner budget was exhausted | a handler unit can be wired to it |
| `awaiting` | a value must come from outside | suspend (§9) |
| `surged` | a powered cycle crossed the energy threshold | the loop was burned; the fact names it |

**An outcome attaches to a goal, never to a step.** A tight step may advance several pending goals, so each
gets its own outcome fact.

**Goals form a lineage** — a goal produces subgoals — and that lineage is what carries the explanation. It is
an ordinary relation between ordinary goals; a goal with no parent is just a goal with no parent, not a
different kind of thing. `goal_machinery.md` works this lineage relation out concretely (interning via an NAC
guard, verified against the running engine) and states the general turn mechanism it depends on. Combined with
the outcomes above it distinguishes four states that would otherwise collapse:

| | on the **first** goal of a turn | on a **descendant** |
|---|---|---|
| `starved` | *"I couldn't read it"* — nothing came to mind about how to interpret this | *"I understood you; nothing came to mind"* |
| `out_of_fuel` | *"I gave up trying to read it"* | *"I understood you; I couldn't work it out"* |

Read off chain position, with no new mechanism. Note what this does **not** need: no distinguished
interpretation goal, no comprehension flag, and no positive *"understood"* fact — comprehension succeeded iff
the first goal advanced at all. And the system never concludes an utterance is *meaningless*, only that it
could not read it — the same weak, honest claim as `starved` ≠ underivable.

⚠ Leaning on fuel for *"couldn't work it out"* is one step away from the conflation this section exists to
prevent. It stays clean only while `out_of_fuel` is reported as budget exhaustion and never collapses into a
negative answer: the surface must say *"I couldn't work it out"*, never *"no."*

An LLM agentic loop is the same shape and is worth the comparison: the loop continues while the stop reason is
`tool_use`, and `end_turn` is an **emitted** signal — the model's positive act of stopping. The reason the API
grew *distinct* stop reasons (`end_turn`, `max_tokens`, `pause_turn`, `refusal`) is precisely that finished,
truncated, paused, and declined need to be told apart. A loop that tests only "no tool call" silently conflates
all four. Same lesson, one level up.

### Two budgets

Fuel bounds the **inner** loop — one circuit's run. The **outer** loop needs its own budget, because System 1
will keep offering rules and steps will keep happening. Their exhaustion is not the same fact: *"this
computation didn't converge"* versus *"I stopped thinking about this."* An agent needs to be able to say the
second. Both are values something can be wired to, not return codes.

### Energy is fuel, localized to a gate

A powered cycle still runs forever. It is bounded by **energy**, which lives **at the gate** as a count of how
many times that gate's input *changed* within the run. A global counter says the step was expensive; energy on
a gate says *which chain* was, so exhaustion attaches to the specific conclusion that ran out.

| | gate energy |
|---|---|
| long acyclic chain, 30 deep | every gate is delivered **once**, so no input ever changes — **zero** energy, whatever the depth |
| powered wiring cycle | one gate's input keeps changing — surges |
| self-undermining deletion | one gate's input keeps flipping — surges, by the identical counter |

**So the two triggers were never two.** An earlier design carried energy on the *value* as an AS-path — the
list of every unit it had passed through — because a scalar accumulated per hop cannot separate depth from
cycling: charging per hop makes a long sound derivation indistinguishable from a loop, and with bands finite
the chain-length limit would be the number of bands. Moving energy to the gate deletes the path and keeps the
discrimination, which was never really about the value: a self-deleting unit's invisibility to the old detector
was an artifact of energy riding a value that never went round a wire.

**Two things this had to keep, both pinned.** **Count *changes*, not arrivals** — §5 says a repeat arrival is a
firing, so four wires from one source fire the unit four times and that is legitimate; counting arrivals is the
per-hop mistake in new clothes. And **count per *gate*, not per unit** — a unit with one input on a cycle and
one on a stable axiom must burn the cycling wire; summing across the unit still surges but makes the quiet
input an equally eligible victim.

**Growth, never decay.** It fails *loudly* — a surge is an event at a definite moment, where a decay to zero
has to be detected as an absence, which is exactly what this section forbids. And it cannot cause a **false
absence**: decay pushes a live fact toward θ, so a still-supported conclusion could drop below threshold and
read as absent under §4, firing negation-dependent rules on a purely mechanical artifact. Growth pushes away
from θ.

**The underlying theorem.** Mint, edge and attribute effects only ever make more things readable, so within a
stabilization run the readable set grows **monotonically** and a gate can only go absent → present.

> **A gate going present → absent is proof that a non-monotone effect fired.**

**And the non-monotone effects are two, not one.** Retraction is the obvious one. **Identification is the
other** — merging two nodes that disagree produces a conflict, and a conflict reads as absent (§5). A
self-undermining identification surges by the identical mechanism, which is the evidence that a flipping gate
is the *general* signal rather than a deletion-shaped special case. Pinned by
`test_the_detector_is_not_deletion_specific_identify_surges_too`. **One flip is normal** — a deletion landed
and a downstream unit correctly lost its premise — so the threshold is on the *count*, and like θ it is a
threshold you can be wrong about.

**No static cycle check.** Detecting cycles in the wiring at assembly time was rejected: on a large graph it is
a global scan, and it is redundant against a runtime detector that catches dynamically formed loops anyway.
Unpowered cycles are already free (§1).

**And naming the loop survives without the path.** The loop was never in the value — it is in the topology, and
it is recovered by walking the wiring backwards, the same walk `powering()` does. Provenance is the wiring, so
this is that principle paying for something it was not adopted for.

**Surge is the detector; fuel is the backstop.** With the surge check mutated out, the revive does not
terminate — it hangs. That is the fail-dangerous asymmetry of growth over decay showing up in practice rather
than in argument: a decaying cycle dies whether or not anyone is watching; a growing one stops only because a
detector fired. So the inner budget is **load-bearing, not belt-and-braces**, and `out_of_fuel` is recorded as
a fact.

⚠ **Monotone-but-infinite is caught only by fuel.** A rule minting a fresh node every round grows forever
without any gate ever flipping, so no local detector sees it. Fuel is the *sole* mechanism for a real pathology
there, not merely a backstop for a misconfigured detector.

⚠ **Two deletions cannot build a cycle between them.** A first attempt at a non-empty oscillation used two
units deleting each other's premises; it **converged**, because deletions only subtract and one unit falling
silent is a self-consistent state. Self-deletion is the only genuine 2-cycle available. The pathology is
*narrow*, not a general instability of deletion.

### The correction is a bundled rule, and it is the first thing that *needs* homoiconicity

The engine's entire involvement is one line: on surge it writes `surged` on the unit's own node and delivers
the report. It does not stop, does not unwire, and does not silence. A bundled rule matches the fact and
concludes the correction; the turn then reaches a fixpoint and completes.

> `bundled:silence` — *anything that surged: stop its output.*

**Burns persist**, decided against an earlier recommendation for transient burns on a stronger argument than
the one it was weighed against: a transient burn re-runs the identical pathological loop on **every** turn,
surges, burns, and forgets — a guaranteed recurring cost, not a safe default. Persistence stays inside
invariant 15, because an unwiring changes the wiring and the next revive legitimately differs. The
authorization objection is answered by **where the correction lives**, not by making it transient: the engine
reports, a rule concludes the unwiring, wires are ordinary occurrences (§6) so that is an ordinary mutation
applied at write-back, and the rule **ships in the bundle** the way the always-attended interpretation rules
do. A wrongly burned wire is recoverable — `surged` records what happened, and re-wiring is another authored
act.

Building it as a bundled rule *now* rather than as engine policy to be made authored later is the composability
principle: a surge correction is a reflexive/governance mechanism, and hardcoded in Python it is an unreachable
island that later has to be dug out. The target state — *reasoning aware of the surge, applying a correction* —
is then the day-one architecture rather than a migration.

**Three things fell out that were not obvious in advance.**

1. **It needs a unit to be plane-1 data for a reason other than tidiness.** Without a node for the unit there
   is nothing for `surged` to be *about*, and the correction has to be engine code. This is homoiconicity being
   **used** rather than merely justified — the first place in the design where it earns its keep. Removing unit
   nodes from the graph kills two tests.
2. **There is no new effect kind, and the attempt to add one failed usefully.** Silencing was first built as a
   sixth effect and broke immediately, because **a control decision is not a graph overlay**. The fix was not
   to teach the overlay layer about it but to notice that invariant 4 had already specified the shape — *units
   **propose** wirings as facts*. Taken literally, the rule concludes an ordinary attribute on the unit's node
   and the machine reads it. Effect count stays at five.
3. **A report must persist for the turn; a conclusion must not.** Effects are rebuilt from scratch each round,
   so the first version's `surged` fact evaporated on the very next round and no rule could ever match it. **A
   report of something that *happened* is not a conclusion that has to keep being re-derived**, and the two
   need different lifetimes inside one turn — the two dispositions appearing at a third scale, within a single
   stabilization run.

⚠ **This section said "Built" once when it was not — the rule had never fired.** Two independent defects,
either fatal alone, and the test that "covered" it asserted only the engine's half (that `surged` was reported)
and never that anything acted on it. The pattern was `surged=None`, which matches every node *lacking* the
attribute (§4); and `surged` was never on a wire, so the report never crossed to a gate and no rule could reach
it however good its pattern. It is now a cell on `Network.reports`, and it crosses where every other value
crosses. ⚠ **And once it fired, it burned itself** — the report accumulates within a turn, so each surge after
the first was a *change* on the corrector's single gate, and at the threshold the detector burned the corrector
and the last loop went uncorrected. The fix is this section's own monotonicity theorem applied to the value on
the wire: **a strictly larger input is not energy.** That narrows the detector onto the case the theorem covers
and pushes monotone-but-infinite further onto fuel.

**The claim is falsifiable rather than decorative.** Remove the bundled rule and the behaviour changes: the
engine reports, nothing handles it, and the turn runs to the budget. If the engine silenced on its own, the
turn would still complete and the rule would be decoration — mutating the engine to do exactly that kills six
tests.

⚠ **Silencing as built is per-turn containment, and it is fail-safe rather than safe**: a vanished conclusion
can fire negation-dependent rules on a mechanical absence, the same hazard as invariant 12. It lets the turn
complete and report; it is never a repair. The persistent variant — the authored unwiring — is unbuilt.

**A surged turn writes nothing back, and reports no effects.** Whichever phase the detector halts on is an
artifact of where the scan began — tested against a cycle whose phases are *both* non-empty, because the simple
case always halts on the empty phase and cannot tell a principled answer from a lucky one. **A truncated turn
writes nothing back either**: it has conclusions in hand and applies none of them.

---

## 9. The boundary  · PARTLY BUILT (write-back is; transcription and pull are not)

### The boundary transcribes; it never interprets

An LLM translates prose into the CNL, which is unambiguous by construction. The boundary then does as close to
nothing as possible: it **transcribes** CNL into graph structure and mints a goal. Every interpretive judgement
— what this utterance is *about*, whether it asserts or asks or commands, where one statement ends, what refers
to what — happens **inside the loop, as rules.**

> **There is no interpretation stage.** Wherever a seam is placed it becomes brittle and stops composing, so it
> is placed nowhere.

The engine trusts the grammar, and that trust is about *syntax fidelity only*: the boundary carries the
surface's marks across as ordinary graph data without knowing what they mean. Rules decide that.

**Four things this buys:**

- **Interpretation is revisable.** A seam commits irrevocably before any reasoning has happened. As rules, a
  mis-parse or a wrong boundary or a wrong scope can be reconsidered by a later step — it is data, and
  deletions apply at write-back. This is the endpoint of the surface/interpretation split: structure immutable,
  judgements discardable, contradiction → re-interpret without re-reading.
- **Interpretation composes.** Hypothetical, attributed (*"Paul says X"*), graded, and attention-dependent
  interpretation are all free, because none of it is a pipeline stage that must be taught about hypotheses.
- **Force stops being a router.** Assertion, question, command, authoring, retraction are conclusions rules
  reach, not branches a dispatcher takes.
- **It is learnable.** Interpretation expressed as rules can be authored and revised in-language. A seam in
  Python cannot.

**The seam shrinks but does not reach zero.** Three things cannot move inside, and naming them keeps them from
reappearing informally: **transcription** (CNL text → graph, mechanical, no judgement); **minting the goal**
(something outside must create the thing that makes the loop run); and **the actual reads and writes** to the
outside world. One function, one node, and an I/O edge. Everything else moves in.

**Two costs.** Comprehension is no longer free — understanding an utterance costs many steps of the expensive
loop, which is where performance pressure will land first. And it depends on linguistic competence being
attended when almost nothing is (§7).

⚠ **`ugm`'s intake routing does not carry over — it *is* the seam.** What survives is thinner: the refusal
discipline (now the translator's honesty, since a well-formed but wrongly-bounded translation is worse than a
refusal — it is silently confident), and forms-as-data, which stops being one feature and becomes the whole
game.

### A denotational expression is inert

*"The red car parked at the third floor of the garage near the movie"* is a **subgraph**. It is not a chain of
units, it does not run, and it has no output. It exists because there cannot be a flat inventory of describable
things, so an arbitrarily deep description has to be **built out of parts** — the practical composability
argument, which is a *data-shape* problem, not a computation problem. Subgraphs nest arbitrarily; that is the
whole of what was wanted.

**What resolves it is ordinary rules.** The narrowing — find the movie, the garage near it, its third floor,
the cars parked there, the red one — is computation units matching over inert structure, which is exactly
*there is no interpretation stage*. Nothing about it is privileged, and there is no chain the engine sees.

**Its product is an identification, which is an act.** Deciding that a mental node refers to a particular real
thing is a rule's decision (§11), graded and revisable, and *create, never merge* means the decision persists
and is applied at write-back — so a resolved reference is written by a **mutating rule**, the same disposition
as the enumerator's cursor.

**And this settles referential vs attributive without new machinery.** Whether *"the red car"* stays that car
after it is repainted (referential, Donnellan) or tracks whoever currently satisfies the description
(attributive) is **not a property of the description** — the subgraph is just there. It is decided by which
units are wired to it and which disposition their product has:

| | |
|---|---|
| **referential** | a mutating rule concludes the identification; it is asserted and stays fixed |
| **attributive** | a computation unit holds the reading; it fades and is recomputed when the world changes |

A standing watch is the second, consistent with §7 already treating a watch as a dangling gate.

**The cardinality discipline is what distinguishes reference from deduction**, and it is inverted between them:

| | 0 matches | n matches |
|---|---|---|
| **a unit deducing** | silent, and correctly so — *"a unit that had nothing to say"*, the same silence as `starved` | *n* firings. Normal, nothing to report |
| **resolving a reference** | **reference failure** — reportable | **ambiguity** — reportable |

This is not a second mechanism. It is a property of the *rules that do reference*, which must conclude
positively about failure and ambiguity, exactly as §8 requires done-ness to be a positive fact rather than an
absence. `ugm` measured this shape already: gating, failure-location and ambiguity came free from the selector
chains, and *"belief is invariant under atom order — only re-attachment changes meaning."* That was always a
statement about **reference**; the original §6 lifted it into a statement about **scope**, and that lift was
the error.

**One thing the superseded model got right.** *"Computation is a transient circuit, assembled and thrown
away"* is true of a *resolution* — it belongs to one utterance. It was over-generalised to everything.

### Pull

The event that starts a turn brings data in — an utterance interpreted, a schedule firing, a tool result. But
retrieval mid-turn is real too: a subgoal can reach outside, and activating a tool is exactly that. So the
boundary is bidirectional and live, not a load-then-compute phase. A starved gate is the natural signal: it
emits a **miss**, and something wired to the miss goes and looks — the same shape as the out-of-fuel handler,
which is a good sign the mechanism is the right size.

### Suspend is a gate that hasn't been filled

A tool call means a gate will be filled later — maybe seconds, maybe after this turn is over. So:

> **Suspension is not continuation machinery.** It is a pending demand, represented as data: *this goal awaits
> a value of this description*.

The turn can end. Resume is then not a special path — it is an ordinary turn whose triggering event happens to
match a pending demand. One mechanism covers four cases: a tool call, fuel exhaustion, a question put to the
user, and a standing watch. Blocking and holding the circuit in memory remains available as a pure optimisation
for fast calls, but nothing may depend on it.

Two rules make the rebuild sound. **Resume continues; it does not replay** — everything already concluded
arrives as data, so the rebuilt circuit does not have to re-reach those conclusions, or reach them the same
way. And **suspension is a write-back point**, not only turn-end.

The staleness worry answers itself: if the rebuilt network differs, it differs *because the data changed* — in
which case resuming into the old network would be the wrong behaviour. A stale trigger is reconsideration
arriving between turns instead of within one.

### Write-back

Derivations are **not** written back — the wiring is the derivation. **Write-back happens after stabilization,
never during**, because the circuit transiently holds wrong values while a revive propagates.

**It is filtered by `powering()`.** ⚠ This was a live leak: write-back has no configuration of its own, so it
applied every mutating rule's effects to the store regardless of what powered them, and *"suppose it rains"*
wired to a mutating rule really took the umbrella. The filter is the same one the read path already uses.
Pinned by `test_a_mutating_rule_inside_a_supposition_does_not_act_on_the_world`.

Mutating conclusions are written back — and so are **deletions**. Two consequences worth having explicit:

- **The circuit never mutates the store.** A deletion is a *proposal* on a wire, applied at write-back, so
  nothing inside a step reasons over a store that changes under it.
- **A deletion is invisible within its own step.** The step that concluded it still sees the old data; the
  *next* step sees it gone. Which also means contradiction handling is **authored**, not engine policy: a rule
  concludes that the stale age fact should go, exactly as a rule concludes anything else. (This settles
  `attic/decisions/0032`.)

⚠ **Write-back is the one place effect order still matters**, because the store must be materialized. Reads are
lazy and therefore order-independent (§5); identifications are applied **last**, which is the narrowest fix for
the re-introduced-node bug and is not a general argument that write-back is order-free.

---

## 10. Walkthrough: one goal, comprehension to answer

A small case, end to end. Note where the **turn** boundaries fall — they are not the same as step boundaries,
and that is the point. This exercises §§7 and 10's loop, which are design; it is what the built substrate is
*for*.

> **Utterance:** *"Should Paul get the loyalty discount?"*

An LLM turns that into CNL; the boundary transcribes it into graph structure and mints one goal — *make sense
of this*. It interprets nothing (§9).

### Step 0 — comprehension is steps too

**Retrieve.** Attention holds only the transcribed utterance and the fresh goal, so the always-attended
interpretation rules are what come to mind (§7).

**Run.** Over one or more steps, rules conclude what the utterance is doing: it *asks*; it concerns a person
named Paul; the thing asked is about discount eligibility. A fresh mention node is minted for Paul with
`name = "Paul"` — whether it is *the real Paul* is not decided yet, and a rule will decide it, gradedly, and
can be wrong.

**Write back.** A **subgoal** whose satisfaction condition is *a fact about this Paul-node stating discount
eligibility, or its denial.*

**Outcome:** `satisfied` on the first goal. There is no *understood* flag anywhere — comprehension succeeded
because the first goal advanced and produced a subgoal. Had nothing come to mind, the first goal would have
`starved`, and that is what *"I couldn't read it"* is (§8).

Everything from here is the same loop; only the goal is different.

### Step 1 — retrieve, and starve

**Retrieve.** System 1 offers two rules. One is *"a customer gets the loyalty discount when they have been a
member for over a year and their account is in good standing."* The other is a **birthday discount** rule.
Nothing here suggests a birthday; System 1 is associative, not correct.

**Assemble.** The eligibility statement becomes units with two open gates: one wanting a membership date, one
wanting an account standing. The birthday rule gets its own unit.

**Run.** The birthday unit matches nothing and emits nothing — it **starves**. Both eligibility gates are
unfed, so each emits a **miss** carrying the description of what it wanted.

**Write back.** Two pending demands, one per miss. The birthday rule's silence is recorded too: *nothing came
to mind past this point* — which is `starved`, **not** *"Paul has no birthday discount."*

**Outcome:** `awaiting` ×2. One wasted rule, and that is the expected cost of associative retrieval.

### Step 2 — the boundary reaches out

The pending demands are visible to the boundary, which activates two tools: the membership system and the
accounts system. Both gates will be filled later.

**The turn ends here.** No circuit is held in memory. What persists is the graph: the goal, the units and their
wiring, and the two pending demands.

### Step 3 — a tool result resumes the work *(new turn)*

The membership result arrives. That external event starts a turn exactly like the utterance did — resume is not
a special path.

**Retrieve.** The goal is still open, so the eligibility statement comes to mind again. So does a date rule for
*over a year*.

**Run.** `member_since = 2019-03` now feeds the first gate. The duration sub-conclusion fires. The second gate
is still unfed and still starves.

**Outcome:** still `awaiting` — one demand, not two.

⚠ Note what did **not** happen: step 3 revived the circuit, but it did not re-*reason* to anything it already
had. **Resume continues; it does not replay.**

### Step 4 — a graded match, and satisfaction *(new turn)*

The accounts result arrives: **two payments late**.

**Retrieve.** The eligibility statement, plus a graded rule: *an account with a few late payments is marginally
in good standing*.

**Run.** The standing rule matches at reduced strength. The conclusion **inherits the band**, so eligibility
fires — but marginally, not flatly. The goal's satisfaction condition matches the conclusion.

**Outcome:** `satisfied`. The answer is in the graph, and it is explainable next week because the wiring that
produced it is still standing.

### Step 5 — a hypothetical *(new turn)*

> **Follow-up:** *"What if he pays them off?"*

**Assemble.** A supposition node, and units wired downstream of it. Everything they produce is supported by it.
No rule anywhere matches on "am I in a hypothesis" — the rules are the same rules as step 4.

**Run.** Under that support, standing is clean, so eligibility fires unqualified.

**Read.** The base world reads none of it: those units are powered by the supposition, and a read is relative
to a configuration (§5). The conclusion is not stuck behind a gate someone must open — it is simply supported
by something the base configuration does not include.

**Write back.** If a mutating rule concluded anything under the supposition, the `powering()` filter keeps it
out of the store. What is recorded of this turn is conditional, not asserted flatly.

**Outcome:** `satisfied`.

### What the walkthrough demonstrates

| | where |
|---|---|
| comprehension is ordinary reasoning, not a stage | step 0 |
| understanding needs no flag — the first goal advanced | step 0 |
| nothing runs unbidden — the goal fires everything | steps 1, 3, 4 |
| retrieval is allowed to be wrong; the cost is a step | step 1, the birthday rule |
| `starved` ≠ *"underivable"* | step 1 |
| a starved gate is how the system reaches outside | steps 1→2 |
| suspend is a gate that hasn't been filled; the turn ends | step 2 |
| resume continues from data rather than replaying | step 3 |
| degree flows from match strength into the conclusion | step 4 |
| done is a positive fact matching a stated condition | steps 4, 5 |
| a hypothesis is support, and no rule mentions it | step 5 |
| the same rules ran inside and outside the hypothesis | steps 4 vs 5 |

---

## 11. Standing positions

**Guards yes, kinds no.** When a distinction is needed it becomes a fact something asserts, never a new kind of
thing. A superstructure makes a distinction *unstatable*; uniformity makes it *statable but unstated*, and only
the second is recoverable.

**The engine is knowledge-agnostic — garbage in, garbage out.** Loops that don't terminate, gradedness leaking
into a recursion, self-referential provenance: these are the author's responsibility, exactly as a
non-terminating Python loop is the programmer's. The engine does not protect against bad knowledge, and adding
guards for it is how superstructures start.

**The front end is a controlled natural language, and the boundary is shallow.** An LLM handles construction
and ambiguity, producing CNL that is unambiguous by construction; the boundary transcribes and interprets
nothing (§9). This division is what makes parsing-as-rules viable — the in-loop grammar only ever parses an
unambiguous language, so the coverage wall that stopped `ugm`'s grammar (real prose at 0/50, the gap ~100%
constructional) is not in the way.

**The front end targets data, never an engine API** — otherwise the system can *say* things it cannot *learn*.
Everything about a unit is describable in plane 1 (§6), so this is now literally true rather than aspirational.

**The CNL grants the shortcut the engine refuses.** Nothing matches by name implicitly (§4), so a rule about
destinations must explicitly match `name = "destination"` — intolerable to write by hand. Role names are
therefore a *surface convention* the grammar expands into explicit matching. The privileged treatment lives in
the front end, where it is inspectable and replaceable, and never in the matcher.

**IDs are plumbing.** Pointers to instances are a technical device with no semantic content. Deciding that a
mental node refers to a particular real thing is a *rule's* decision, and can be graded and wrong.

**The engine reports; a rule decides.** Surge (§8) and conflict (§5) arrived at this independently, which is
the evidence the shape is right. The engine has no resolution mechanism to parameterise — not even an authored
one.

**The computation model is not an LLM architecture, and the two must not be allowed to blur together.**
Goal-orientation, recovery/repair, and tool dispatch are old — classical production systems (OPS5, Soar,
ACT-R, BDI agents) already have goal stacks, conflict resolution, and procedural attachment, with no LLM
anywhere. Those pieces are necessary scaffolding here too, but they are not where this project's advantage
over that lineage comes from, and stating them as if they were is how the advantage gets quietly lost. The
actual source is **homoiconicity as an engine-level property**: a rule is data (§1, §3), so another rule can
read a declared rule's own pattern/effect and mint a live instance of it — the metaprocedure that replaces a
blind fixpoint driver, and the mechanism behind §6's tunnel-as-wiring resolution, both depend on this and
nothing else. Soar's productions are not data other productions can restructure at runtime; that is the
concrete difference, not "it has goals" or "it recovers from failure." An LLM's place in this picture is as
one possible **tool a rule dispatches to** (construction, ambiguity resolution, prose-to-CNL translation,
per §9) — an attachment at the boundary, never a component of the computation model itself. Keep this
distinction explicit in every future document that describes "agentic" behavior here: name the mechanism
that buys composability, don't reach for the goal/recovery/tool vocabulary as if reciting it were the
explanation.

---

## 12. Invariants worth testing

Each is the kind of thing that is obviously right on paper and quietly wrong in a build. Numbering is preserved
from the originals so existing citations resolve; 2 and 9 are deleted, and 19 is false as written and restated.

1. **No rule pattern names a scope.** Holds for free: scope is support, so there is no scope object to name.
2. ~~Nesting → tunnel → nesting round-trips.~~ **DELETED** — no tunnel to round-trip through.
3. **A unit reads only its gates.** No ambient access, ever.
4. **Units never wire anything *directly*.** A wiring change — including a burn — is a mutating rule's
   conclusion applied at write-back; the engine never edits wiring on its own. If routing is ever learned,
   units *propose* wirings as facts.
5. **Every goal worked on in a step receives exactly one positive outcome fact.** Per goal, not per step, and
   never an absence.
6. **The boundary interprets nothing.** Transcription, minting a goal, and I/O only.
7. **Nothing matches by name unless a rule says so** — `name` has no privileged status anywhere in the engine.
8. **A turn is *resumable* from persisted data alone — not reproducible.** No hidden in-memory state may be
   load-bearing. Re-running a turn need not reach the same place, because System 1 is non-deterministic (§7).
   The test is that work can *continue*, never that it replays identically.
9. ~~Only end markers are attachable.~~ **DELETED** with the seal. A rule may match any part of an inert
   description; matching is not attaching, and it claims nothing about what the whole expression denotes.
10. `units/` imports nothing from `ugm/`.
11. **Changing an axiom makes everything derived from it absent on the next revive, with nothing retracted.**
    If any retraction, cascade-delete or invalidation code appears, the design has regressed to maintenance.
12. **Energy never reaches the θ test.** A conclusion's readability as present or absent must be independent of
    how far it travelled or how many times it was revisited.
13. **A long acyclic chain neither surges nor weakens.** The test that distinguishes revisit-counting from
    hop-counting; hop-counting passes 11 and 12 and fails this one.
14. **A partially wired unit is stable** — it holds, produces nothing, raises no error, and is not garbage.
15. **The graph state is a pure function of (axioms, wiring).** Literally true: wiring, patterns and effects
    are all plane-1 data. Tested across 144 orderings of a diamond network (§5).
16. **A read is relative to a configuration, and yields one value or reports a conflict.** Never a winner (the
    cascade) and never a set — a caller takes the first element and the contradiction vanishes anyway. A
    conflicted read is **absent**; the disagreement is a positive `conflict` fact a rule can match and resolve.
17. **No engine code mutates wiring.**
18. **Everything persistent is plane 1.** Plane 2 holds nothing across a revive that plane 1 does not describe.
    Latched values and energy live *within* one stabilization run and do not survive it.
19. ⚠ ~~A pattern that does not name machinery never matches machinery~~ — **FALSE, tested.** A wire occurrence
    has an outgoing edge like anything else, so a *generic structural* pattern matches it while naming nothing.
    Invariant 7 buys nothing here. **Restated: machinery has to be delivered to a gate before any pattern can
    see it, and delivering it is a deliberate act** — the barrier is invariant 3, not naming. Pinned both ways
    by `test_machinery_is_unreachable_unless_something_wires_it` and
    `test_invariant_19_is_false_as_written_and_the_barrier_is_the_wiring`.

---

## 13. Open questions

Genuinely undecided, not oversights. Grouped by what they block.

### Blocking the next build

- ⭐ **Discharge has no mechanism, and it is structural.** `powering()` walks backwards over the wiring, so
  support propagates forwards through every wire: anything reachable from a supposition is inside it, by
  construction. Natural deduction's →-introduction is precisely the step that must leave the hypothesis behind,
  so `forms_discourse.md` §4.4's *"suppose is the introduction rule for the conditional"* is **not buildable
  here**. Either discharge becomes a declared, support-breaking unit — which costs the purity of
  scope-as-backward-walk — or conditionals are simply **authored wirings** and supposition is for hypothetical
  reasoning only. See `forms_cnl.md` §13. *(Shelved per `STATUS.md`: no current scenario needs the agent to
  derive a new rule from a hypothesis.)*
- **One shape for asserted and derived facts** (§3). Decides what the boundary transcribes into. It is also
  what makes *"retract Paul's age"* unambiguous between *that claim* and *that slot*: a rule naming the source
  is only necessary because a base fact is not yet a node like a derived one.
- **The `when:`-to-wired-unit slice.** Everything about a unit is now describable (§6), but that does not
  decide what an interpretation rule *should* conclude. A forms question, not a mechanism one.
- **Revive cost** as the circuit grows — the reshaped retention question, and the first thing to measure.
  Incremental revive is available as a pure optimisation and deliberately not taken (§1). **Measure first.**

### Retrieval and attention (all of §7 is unbuilt)

- **The retrieval mechanism, concretely.** Settled in *kind*: associative, non-deterministic, no completeness
  guarantee. Open in *choice* — subgraph similarity, activation spreading from the goal's nodes, or something
  learned. And whether the similarity function is authored data like every other similarity judgement, or the
  one thing the engine fixes.
- **Attention leak from accumulated dangling gates**, and where decay goes without drifting off the goal.
  Constrained by the trigger case: decay must not drop a standing prohibition, so it consults attention-holding
  facts rather than age alone.
- **Does attention bound gate-matching** the way it bounds rule recall? A dangling gate wanting *a man* is a
  standing query against the twin, and the population of such gates contributes to outer-loop work
  independently of the goal. This is where the cost of dissolving the anchoring problem actually landed.
- **Self-reinforcing recall.** Retrieval that surfaces what resembles what is already attended will keep
  confirming itself. Randomised refocus (§7) is the candidate, unbuilt. The unresolved half of the `ugm`
  auto-fire finding.
- **Attention over machinery.** If wires are ordinary occurrences, they are in principle retrievable by System
  1. Almost certainly undesirable by default, and the mechanism that prevents it is attention, not a partition
  — but nothing currently says so.
- **What comprehension costs.** Every utterance takes many steps of the expensive loop before any domain
  reasoning starts. Acceptable in principle; unmeasured, and the first place performance pressure will land.
- **The outer budget's shape.** Steps, wall clock, or something the goal itself carries.

### Governance and correction

- ⚠ **The surge detector cannot distinguish convergent recursion from a runaway cycle**
  (`forms_discourse.md` §10.3). This is the mechanism behind honest exhaustion reporting, and it is currently
  **broken**, not merely missing — `STATUS.md` nominates it as the next thing to fix.
- **Does a persistent correction differ from a within-turn one?** Burns persist (§8); silencing as built is
  per-turn containment, and the persistent variant — the authored unwiring — is unbuilt.
- **What a `surged`-triggered correction should actually do.** Unwiring an arbitrary loop element is what the
  detector does today. A rule can be cleverer, and there is no evidence yet about what cleverer means.
- **The surge threshold**, and whether it is global or per-branch. The short-circuit analogy argues per-branch:
  a breaker is rated on the branch that faults, and does not watch total current and guess.
- **Does a conflict need a band?** Conflict is currently crisp. Two readings at different strengths is not
  obviously the same event as two readings at equal strength, and §4 says a match has a strength rather than a
  verdict. The seam where graded matching meets invariant 16.

### Structure, surface, and cost

- **Whether in-circuit cycles are needed at all** (§5). If the tight outer loop supplies all iteration that
  requires new data, the only cycles left inside walk a fixed structure to a known end — and latching stops
  being load-bearing. Interacts with latched cycles after ungrounding: nothing latches *across* a revive, but
  within one stabilization run a cycle that loses its external input could be sustained by latched values until
  it surges.
- **How wide subset output forces the wiring.** An emitted occurrence carries its filler *nodes* without their
  *attributes*, so a downstream unit that needs to read a name must be wired to where the name is. There is no
  ambient store to fall back on — the intended discipline, and also the number to watch: if most units end up
  wired back to the axiom cell, the pool has been re-created by convention.
- **Does a resolution stand or is it thrown away?** §9 says a resolution is per-utterance and its product is
  asserted. Whether the *resolving units* stand afterwards is not settled, and it feeds revive cost directly:
  an agent that resolves many references accumulates many units that will never fire usefully again.
- **Role node sharing.** Role nodes are per-occurrence and match by declared name-equality. Is that equality
  rule loaded once as ordinary KB data, or restated per rule? The first risks becoming a de-facto vocabulary
  through the back door. (`cnl.md` §2 argues the surface settles this; not yet confirmed against the engine.)
- **The CNL surface's remaining open items** — the wiring register's vocabulary, where role names come from,
  band words, quantification, and a prose renderer. See `cnl.md` and `forms_cnl.md`.

---

## Appendix — what carries over from `ugm`

The top-level shape converged back onto `ugm` — one persistent graph, goals driving demand, a CNL front end
targeting data, suspend for external calls, provenance and fuel as data, bands, write-back. That convergence
re-derived itself from first principles without being steered for, which is evidence the top level was right
the first time. **What was wrong was one layer down.** Four differences, and they are not equal:

| # | difference | retrofittable onto `ugm`? |
|---|---|---|
| 1 | The inner loop is a circuit, so **no rule ever matches a scope** | **No** — this is what was blocking, and what drove the flip |
| 2 | Matching is **graded and authored**; degree is intrinsic, not a layer alongside | Yes, painfully |
| 3 | Retrieval **admits incompleteness**, so NAF weakens to *"didn't come to mind"* | Yes |
| 4 | Identity is **decided**, not interned — no vocabulary, no lexeme bridge | Yes |

So the flip is justified by (1) alone, and the practical consequence is that **it replaces the evaluator, not
the system.** Mechanism by mechanism:

| `ugm` mechanism | here |
|---|---|
| focus / working set | **changes job** — bounds System 1 instead of the evaluator (§7) |
| RECALL | *becomes* System 1; the explicit-only ban lifts (§7) |
| intake routing (assert / ask / author / command) | **does not carry over — it *is* the seam** (§9). Force becomes a conclusion rules reach |
| refusal discipline / nearest-forms rejection | survives as *design*, relocated to the translator's honesty |
| homoiconic grammar spike (token-passing ≡ chart parsing) | **becomes load-bearing** — evidence that parsing-as-rules works |
| suspend + call | survives, simplified to a gate that hasn't been filled plus a pending demand |
| fuel / budget | survives, and gains a sibling: the outer budget (§8) |
| band lattice + θ | survives, and moves *into* matching rather than sitting alongside it |
| provenance | survives as **the wiring**; stratification is dropped |
| coref as declared rules | survives, and gets easier — graded matching is what it always wanted |
| forms / rules as data | survives, and is what the CNL emits |
| reconsider (revising stale NAF conclusions) | **largely absorbed** — every step re-retrieves and write-back can delete |
| focus-reachability GC | **does not transfer** — see revive cost, §13 |
| the central matcher / demand chain | **replaced** — this is the flip |

**Where the failure mode went.** The original model warned that `ugm` died of every rule juggling scope, and
that the *assembler* would inherit it — one place instead of every rule, but the same class of bug relocated.
That warning is **retired**: scope is support (§6), the assembler owns no nesting→tunnel→nesting mapping, and
invariant 2 was deleted because there is nothing left to drift.

## Appendix — superseded decision records

`attic/decisions/` holds 41 records from the pre-inversion design. Each file now carries its own current-status
header; `attic/decisions/README.md` has the table. Seven survive and are in force: **0003** (the store is
bounded, not abolished), **0005** (the index indexes computation, never data), **0008** (subset output —
strengthened, since positioning is what makes it correct), **0010** (units never touch wiring), **0019**
(revision is recomputing forward), **0031** (`units/` may not import from `ugm/`), and **0039** (guards yes,
kinds no). One — **0032**, *can a rule remove?* — is settled by §9: yes, as an authored conclusion applied at
write-back.

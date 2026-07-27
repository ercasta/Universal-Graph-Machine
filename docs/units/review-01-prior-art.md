# Review 01 — the computation model against prior art

**Status: review, 2026-07-27.** Not a revision. Nothing here changes a decision; it locates
`model.md` + `revision-01` + `revision-02` in the literature, grades what is actually new, and names the
places where a known result answers an open question or predicts a cost.

**Method.** Read the three design documents as they stand. Every mechanism was matched against the closest
named prior art, and each is graded:

| grade | meaning |
|---|---|
| **rediscovery** | the same mechanism exists under a name, with the same motivation |
| **recombination** | the parts are known; putting them together this way is not standard |
| **novel** | I cannot place it |

The headline: **almost every mechanism is a rediscovery.** Three things are not, and one of them is small
and sharp enough to be worth writing up on its own. Rediscovery is not a criticism — several of these
traditions have decades of measurements that apply directly, and §6 lists the ones that do.

⚠ Only two references appear anywhere in the design documents: Donnellan (`revision-02` §4) and Lewin's
Zeigarnik account (`revision-01` §5). The three closest relatives of this design are unnamed in it.

---

## 1. Verdict

| mechanism | where | closest prior art | grade |
|---|---|---|---|
| units with gates, wired into a standing network, output over inert data | `model.md` §5 | **propagator networks** (Radul & Sussman) | rediscovery |
| gates **latch**; a unit is sequential, not `f(inputs)` | §5 | **Rete beta memories** (Forgy 1982) | rediscovery |
| revive from axioms; recomputed, never maintained | `rev-01` §3 | **TREAT** (Miranker 1987); spreadsheet recalculation; rematerialize-vs-DRed | rediscovery |
| scope = **support**, read relative to a configuration | `rev-02` §3 | **ATMS environments** (de Kleer 1986) | rediscovery |
| no retraction apparatus, because nothing is labelled | `rev-01` §3 | the Doyle/de Kleer labelling critique, taken to its end | recombination |
| provenance **is** the wiring | `rev-01` §1 | JTMS justifications; why-provenance / provenance semirings | rediscovery |
| graded matching, bands, θ | §4 | fuzzy production systems; possibilistic logic | rediscovery |
| two loops — associative retrieve, exact apply | §7 | **MAC/FAC** (Forbus, Gentner & Law 1995); ACT-R conflict resolution | rediscovery |
| attention bounds retrieval, not application | §7 | ACT-R activation + goal buffer; blackboard control | rediscovery |
| dangling gate = ask = trigger = pinned goal | `rev-01` §5 | a Rete partial-match token; ACT-R's unfilled goal slot | recombination |
| overlays applied lazily, **indexed once per revive**, union-find for `Identify` | `rev-02` §6 | **egg / deferred rebuilding** (Willsey et al. 2021) | rediscovery |
| conflicted read is **absent**; conflict is a positive fact | `rev-02` §6 | Belnap's four-valued logic — but with the opposite collapse | recombination |
| wires as reified occurrences; rules rewiring rules | `rev-02` §5, §7 | computational reflection (Smith, Maes); RDF reification | rediscovery |
| **flipping gate as a non-monotonicity witness** | `rev-02` §6 | — | **novel** |
| **negation weakened *because* retrieval is heuristic** | §7, §8 | — | **novel** |
| **referential/attributive as a disposition** | `rev-02` §4 | — | **novel** |

---

## 2. The three unnamed close relatives

### 2.1 Propagator networks — the closest thing that exists

Radul & Sussman, *The Art of the Propagator* (2009), and Radul's thesis *Propagation Networks: A Flexible
and Expressive Substrate for Computation*. Cells hold partial information; propagators are wired between
them and fire when their inputs change; the **network is the program**; hypotheticals and dependency
tracking are layered on by making the cell contents carry their support.

The overlap with `model.md` §5 + `revision-01` is close enough that the differences are the interesting
part, and there are four:

| | propagators | here |
|---|---|---|
| cell contents | **merge** — information accumulates monotonically, and a cell's value is a lattice join | **create, never merge** (`cnl.md` §1); two live values are a conflict, not a join |
| support | carried **in** the cell, as a TMS-style justification set | read off the wiring **backwards** (`Network.powering()`), stored nowhere |
| termination | runs to **quiescence** | explicitly refused (§2); local surge detection instead |
| substrate | cells are the world | cells are plane 2; the world is plane 1 (`rev-02` §1) |

Row 1 is the real fork and it is worth defending explicitly somewhere in the design, because the propagator
tradition's central bet is the opposite of yours: their merge is what makes multiple contributions to one
cell well-defined and order-insensitive, and `rev-02` §6 spends a whole section rediscovering that two
contributions to one `(node, attr)` cannot be collapsed. You reach *"reify the attribution"* where they
reach *"join in a lattice."* Both work; yours keeps the disagreement visible, theirs keeps the read
single-valued. The docs currently present the reified attribution as forced by a spike finding. It is
actually a **choice against a known alternative**, and it deserves that framing.

Row 2 is a genuine simplification over them and over any TMS, and it is the thing `revision-01` §3 is right
to be proud of.

### 2.2 Rete and TREAT — the revive is a settled argument, and it has numbers

`model.md` §5 says gates latch and a partially-wired unit is a stable state. **That is a Rete network.** A
beta memory is exactly a latched partial match, and Forgy's whole point is that keeping them is what makes
re-evaluation cheap when working memory changes a little.

`revision-01` §3 then throws them away every turn and recomputes from the axioms.

That combination is not a contradiction, but it is a known tradeoff with a name on both sides: **TREAT**
(Miranker 1987) argues precisely that storing join results is a bad deal and that recomputing beats
maintaining on many workloads, and the Rete/TREAT/Gator comparisons are the closest thing to a measurement
you will find for *"is the revive affordable."* `revision-01` §10 lists revive cost as the first thing to
measure; that literature tells you what to measure and roughly where the crossover sits (it moves with
change-rate and with join selectivity, not with graph size).

⚠ **The tension to state plainly:** the design pays Rete's *storage* cost (standing units, latched gates,
`O(circuit)` per turn) while declining Rete's *benefit* (not recomputing what did not change). That is
defensible — `revision-01` §3's argument is that the bookkeeping which buys the benefit is exactly what it
wants to delete — but as written the docs present the revive as a pure win with a cost bolted on at the
end. It is a bet on change-rate: cheap if most axioms move every turn, expensive if few do.

### 2.3 ATMS — `revision-02` §3 rebuilt it, minus the labels

de Kleer, *An Assumption-Based Truth Maintenance System* (AIJ 1986). A datum's **label** is the set of
assumption-environments under which it holds; a read is relative to a **context**; a contradiction condemns
the environment that produced it; alternatives coexist without conflicting.

`revision-02` §3 and §6 state all four of those, in the same order, as consequences of scope-as-support. The
one deliberate difference is the one that matters: **an ATMS computes and stores labels, and you do not.**
Label computation is where the ATMS's exponential blowup lives, and you avoid it two ways — by walking the
wiring backwards on demand instead of maintaining a label, and by the enumerator powering **one**
configuration per turn (`revision-01` §9) rather than reasoning in all environments at once.

That is a real and well-motivated trade: you give up the ATMS's headline capability (reason once, read the
answer under every assumption set) and get a linear-ish cost model instead. Worth saying out loud, because
someone will ask why the multi-context reasoning isn't there, and *"we deliberately do one context per
turn"* is a much better answer than silence.

⚠ The enumerator's cost is then the ATMS's cost re-expressed as **turns** rather than as label size. Three
hypotheses is three turns; the combinatorics have not gone anywhere, they have been moved onto the outer
loop, where the outer budget bounds them and elimination is admitted to be non-exhaustive
(`revision-01` §9). That is the honest version and it is consistent with §8's discipline — it just is not
stated.

---

## 3. What is genuinely novel

### 3.1 The flipping gate as a witness for non-monotonicity — `rev-02` §6

> Mint, edge and attribute only ever make more things readable, so within a stabilization run the readable
> set grows monotonically and a gate can only go absent → present. A gate going present → absent is
> therefore proof that a non-monotone effect fired.

This is the sharpest technical claim in the three documents. The literature handles non-monotonicity
**statically** (stratification — Apt/Blair/Walker, Van Gelder) or **semantically** (well-founded and stable
model semantics), both of which are whole-program analyses computed before or instead of running. Using a
**local, per-gate, O(1) runtime monotonicity violation** as the detector — and then discovering it is the
*same counter* that catches wiring cycles, so the two triggers were never two — is not something I can
place in the production-system, dataflow, or logic-programming literature.

The generalization test it passes is the reason to believe it: `Identify` surges by the identical mechanism
because a conflict reads as absent, which means the detector is keyed on non-monotonicity itself rather than
on deletion. `test_the_detector_is_not_deletion_specific_identify_surges_too` is the load-bearing test in
the repo.

⚠ It is sound in one direction only, and the docs should say so: a flip **proves** non-monotonicity, but
non-monotonicity does not have to produce a flip. `rev-02` §9 already records the escape hatch
(monotone-but-infinite minting is caught only by fuel). The detector is a *witness*, not a decision
procedure, and that is the correct claim to make for it.

### 3.2 Weakening negation because retrieval is admitted incomplete — §7, §8

The resource-bounded reasoning literature — Simon's satisficing, Cherniak's *Minimal Rationality*, Levesque
on vivid/limited inference, Russell & Wefald on bounded optimality, anytime algorithms — bounds **inference**
while keeping the semantics of *"not derivable"* intact. The system computes less, but what it means by
failure does not change.

This design inverts that. `starved` ≠ underivable is a permanent epistemic commitment (§8), and it is what
*licenses* heuristic recall, non-determinism, asynchronous System 1, and the reversal of `ugm`'s
explicit-only RECALL ban. The dependency runs the unusual way: the weak negation is not a consequence of
being resource-bounded, it is the **enabling condition** for a retrieval mechanism that is allowed to be
wrong.

The strongest evidence this was followed through rather than assumed is `model.md` §7's ⚠ note, which
identifies the same hazard `ugm` hit and takes the opposite fix. That is the shape of a real design
commitment.

### 3.3 Referential/attributive as a disposition — `rev-02` §4

Donnellan (1966) and Kripke (1977) locate the referential/attributive distinction in speaker intention or in
pragmatics. `revision-02` §4 gets it from the **execution model**: a mutating rule's identification is
asserted and fixed (referential); a computation unit's holds only while powered and is recomputed when the
world changes (attributive). The description itself is inert and carries neither reading.

I do not know of prior work deriving that distinction from an evaluation discipline. It also does real work
rather than being a curiosity — it is what makes a standing watch and a resolved reference the same object
seen at two dispositions.

---

## 4. What the comparison predicts will bite

**There is no declarative semantics, and the design forecloses one.** Every property in the three documents
is operational: gates latch so `output = f(inputs)` is explicitly false (§5); invariant 8 declines
reproducibility; §2 refuses a global quiescence test. The logic-programming tradition produced well-founded
and stable-model semantics precisely so that a program's meaning is stateable independent of how it ran, and
that is the currency any "is this computation model new" comparison is settled in.

This is not fatal and may be correct for an agent. But it caps what can be claimed: today the strongest
available statement is *"this terminates, and it is explainable"*, not *"this computes X."* Invariant 15
(*graph state is a pure function of (axioms, wiring)*) is the nearest thing to a semantics, and latching plus
scheduler-dependent effect order is in tension with it — `rev-02` §6 finding 4 half-notices this when it
observes that eager application would make the graph depend on the scheduler. **If invariant 15 is meant
literally, it needs an argument that latching cannot make a stabilization result order-dependent, and the
docs do not have one.** That argument is also the closest this design can get to a semantics, which is a
second reason to want it.

**The conflict-as-absent collapse is non-standard and under-argued.** Belnap's four-valued logic gives
`{neither, true, false, both}`; *both* (⊤) normally **propagates** as a distinct value precisely so a
contradiction cannot vanish. `rev-02` §6 collapses ⊤ to *neither*, and defends it on the grounds that §4
already weakened absence so nothing is corrupted. That defence works for the θ-threshold reading of absence
but not obviously for the conflict reading: a conflict is *strong* information rendered as the value that
means *no information*. The positive `conflict` fact is what carries it, so the design is recoverable — but
the argument in the docs is one sentence and the literature has an explicit alternative.

**The enumerator inherits the ATMS's combinatorics as turns** (§2.3 above), unstated.

**The revive is a bet on change-rate** (§2.2 above), stated as a cost but not as a bet.

---

## 5. Known results that answer open questions

Each of these maps onto an item already listed as open.

| open question | where | what the literature offers |
|---|---|---|
| *"Does a conflict need a band?"* | `rev-02` §9 | **Bilattices** (Ginsberg 1988; Fitting's work on bilattices in logic programming). A bilattice is exactly two orders at once — a *truth* axis and a *knowledge* axis — so "two readings at different strengths" and "two readings at equal strength" are different points, and the conflict/degree seam has a settled algebra. This is the single most directly applicable result in this list |
| *"The retrieval mechanism, concretely"* | `model.md` §13 | **MAC/FAC** (Forbus, Gentner & Law 1995) is §7's two loops as a built and measured retrieval architecture: a cheap non-structural filter over a content vector, then expensive structure-mapping on the few survivors. It also has the empirical answer to *"is associative recall over a large store affordable"* |
| *"Revive cost"* | `rev-01` §10 | Rete/TREAT/Gator comparisons (§2.2). Also **Adapton** (Hammer et al. 2014) and **differential dataflow** (McSherry et al. 2013) for what incremental revive would actually cost if it is ever taken — both are demand-driven/incremental with explicit accounts of the bookkeeping `rev-01` §3 deletes, so they are the price list for reversing that decision |
| *"Does the matcher survive reading through `Overlays`?"* | `rev-02` §9 | **egg**'s rebuild (Willsey et al. 2021) is the same operation with published numbers, and its e-matching-over-a-union-find is the thing your matcher becomes. Their result — batch the rebuild once per iteration rather than maintaining congruence per-operation — is your *"index once per revive"* independently derived, which is decent evidence the shape is right |
| *"`Merge` is the case that decides whether lazy is affordable"* | `rev-02` §6 | Same reference; the e-graph literature is *about* this operation |
| *"Self-reinforcing recall"* | `model.md` §13 | Already answered with PageRank damping in `rev-01` §9; the CBR retrieval literature and the MAC/FAC diversity results are the other half |

---

## 6. One inconsistency found

`revision-02` §8's new-invariants list still reads:

> 16. **A read returns a set, never a winner.** Two live overlays disagreeing about one attribute are two
>     readings. If the engine collapses them, the cascade has been built.

§6 of the same document **explicitly rejects** this — *"the first version of this section said 'a set', and
that was wrong"*, *"not picking is not the same as handing the caller a set"* — and `model.md` §12 carries
the corrected form (*one value, or a reported conflict; a conflicted read is absent*).

`revision-02` §8 is stale against its own §6. Since that list reads as the authoritative delta, it should be
corrected to match `model.md` §12 invariant 16.

---

## 7. Reading list, in priority order

1. **Radul & Sussman, *The Art of the Propagator* (2009)** and Radul's thesis — the closest existing system.
   Read for the merge-vs-create fork (§2.1).
2. **de Kleer, *An Assumption-Based Truth Maintenance System* (AIJ 28, 1986)** — `rev-02` §3, plus what you
   gave up by not storing labels.
3. **Willsey et al., *egg: Fast and Extensible Equality Saturation* (POPL 2021)** — deferred rebuilding; the
   `Merge` cost question, already answered.
4. **Miranker, *TREAT: A Better Match Algorithm for AI Production Systems* (AAAI 1987)** and Forgy's Rete
   (AIJ 19, 1982) — the revive-vs-maintain tradeoff with measurements.
5. **Ginsberg, *Multivalued Logics: A Uniform Approach to Inference in AI* (1988)** — bilattices, for the
   conflict-band question.
6. **Forbus, Gentner & Law, *MAC/FAC: A Model of Similarity-Based Retrieval* (Cognitive Science, 1995)** —
   the retrieval mechanism.
7. **Van Gelder, Ross & Schlipf, *The Well-Founded Semantics for General Logic Programs* (JACM 1991)** — not
   to adopt, but as the standard against which §4's "no declarative semantics" should be argued.
8. Belnap, *A Useful Four-Valued Logic* (1977) — for the conflict-as-absent collapse.

---

## 8. Summary judgement

**As a computation model, this is a recombination, not a new paradigm.** Its parts are propagator networks,
Rete-with-TREAT-evaluation, and an ATMS with the labels replaced by a backward walk — three well-explored
traditions that, as far as I can tell, have not been combined in this configuration, and specifically not
under the constraint that *everything persistent must be one homoiconic graph*.

**The novelty that will survive scrutiny is narrower and more interesting than the framing suggests.** The
flipping-gate detector is a small, sharp, apparently-new result about detecting non-monotonicity at runtime
rather than statically. The deliberate weakening of negation to license heuristic retrieval is a real and
unusual epistemic commitment. Both are more defensible claims than *"a new computation model"*, and both are
independent of whether the rest of the architecture works out.

**The one structural gap** is the absence of any statement of what a program *means* apart from how it runs
(§4) — which is also what would let the two novel claims be stated as theorems rather than as observations.

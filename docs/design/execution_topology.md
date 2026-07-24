# Execution Topology — nested queues with dynamic forks and joins

> **Status: DESIGN ONLY (2026-07-24, drafted by the assistant at user request). NOT RATIFIED, NO CODE.**
> This document deliberately changes nothing in `implementation_plan.md` and re-points no arc. Its
> purpose is to answer ONE question that the plan currently contains mislabelled as cosmetics —
> *where does the `resolve_crossings` driver live* — by deriving the answer from a general principle
> instead of a coin flip, and to record the design before Step 4 (`force + vantage as data`) makes an
> implicit commitment to it.
>
> Companions: `scope_reframe_audit.md` (the north star this serves), `reactive_core.md` (the existing
> event queue), `composition_architecture.md`, `../attic/isa_control_machine.md` (the control path this
> extends), `mechanism_policy_separation.md` (where the scheduler must live).
>
> **TRIPWIRE (set by the user's own sequencing rule).** If this design cannot be stated without also
> rewriting Steps 3 and 4 of the scope reframe, that is evidence the queue topology is a NORTH STAR
> rather than a refinement — and the response is to re-point deliberately, not to drift. As drafted,
> it does not: Step 3 is untouched, and Step 4 gains a constraint (§8) rather than a rewrite.

---

## 1. The thesis: there is a UNIFORM COMPUTATION MODEL

The substrate claim of this project is that **there is one uniform representation** — a label-less
attribute graph, S-P-O as a directed path, no privileged partitions, no typed edges. Every
representational question is answered by "it is nodes and relations, like everything else."

**This document asserts the dual, and the dual is the real content of the proposal:**

> **There is one uniform COMPUTATION MODEL.** Every act of reasoning — a demand, a hypothesis, an
> alternative parse, a tool call, a crossing, an utterance being routed — is *the same thing*: work
> queued under a scope, forked when a scope is minted, joined at one declared boundary. No privileged
> control constructs, no mode that exists only in Python, exactly as there are no privileged node
> kinds.

The two claims are the same claim on two axes, and the second is currently FALSE in this codebase.
There are three fork/join pairs implemented three ways (§2) and a 550-line imperative route ladder
(`intake.py:374`) that no rule can see. Those are, in computation-model terms, precisely what a typed
edge or a privileged partition would be in substrate terms: **an island that the uniform account
cannot reach** ([[composability-principle]]).

Stating it this way also fixes what the design is *for*. It is not "queues are a nice execution
strategy". It is: the uniformity that makes the substrate composable is exactly the uniformity the
computation model lacks, and the fork/join-over-scopes topology is the smallest structure that
supplies it — because the substrate's own composition principle (nesting) is already the answer.

---

## 1b. The question, and the answer in one paragraph

> *"What if we flip the entire system to be event-queue driven with focused state — rules fire, and
> depending on where the focus is they do different things, potentially firing more data into the
> queue? A multiqueue with dynamically created forks and joins, to represent scopes / alternative
> computations. The ISA and firmware concepts stay valid; they need a new computation mode above."*

**The engine is already event-driven; what it lacks is a TOPOLOGY — and therefore the uniformity of
§1.** There are three queues today
(§2) and three separately-implemented fork/join pairs, one per layer. The proposal's real content is
not "use a queue" — it is **make the queue topology BE the scope tree**: one queue per scope node,
forked when a scope is minted, joined at exactly one boundary. That is the same consolidation that
fixed the flip-identity class (one materialized copy, merge-back at one boundary), lifted from the
identity layer to the execution layer. It is **strictly better than a single global queue**, for a
reason that is not aesthetic: negation-as-failure needs a well-defined *drained* state, and only a
nested topology can give a local one (§5).

The ISA does not change. The queue mode is a SCHEDULER over programs the machine already runs, and
`SUSPEND`/`Continuation` is already the fork primitive (§6).

---

## 2. What already exists — measured, not assumed

Three fork/join pairs, three implementations, three layers:

| layer | fork | join | where |
|---|---|---|---|
| demand | sub-demands raised in a round | `frame.agenda \|= newly` | `chain.py:1771`, `Frame` at `chain.py:1694` |
| hypothesis | mint `<hypothesis>` scope; assumptions written in PENCIL (scope-tagged control) | on confirm `EMIT` to ink; on refute `DROP_CTRL`-sweep | `suppose.py` |
| crossing | reify + causal MP over `@?h` at the committed-ask gate | **promote** | `scope_crossing.py`, `cnl/query.resolve_crossings` |

And three queues:

- **`Frame.agenda`** (`chain.py:1694`) — the demand work-list. Per-frame, insertion-ordered, seeded
  from the goal, grown only by its own sub-demands. `chain.py:1826` states the locality is deliberate.
- **`reconsider.DIRTY_REG` + `_affected`** — the dirty-grain event queue with a body→head trigger
  dispatch. `reactive.py`'s own docstring: *"one event queue, one trigger dispatch, two reaction kinds
  (retract / derive)"*.
- **pending `<call>` nodes** (`dispatch.py`) — materialized tool calls serviced at each fixpoint, with
  `SUSPEND`/`RESUME` across the async boundary.

PUSH==PULL==FORWARD is already unified through `reactive.fire` + `chain_sip`
([[reactive-core-north-star]]). **So "flip to event-driven" is not a flip.** The engine arrived there;
what did not arrive is a single account of how the queues NEST.

By the composability principle ([[composability-principle]]), three hardcoded fork/joins are three
islands: none of them can be combined with, or nested inside, either of the others without new Python.
That — not throughput, not elegance — is the case for this work.

---

## 3. A correction, and a defect found while checking it

**`<under>` is NOT a labeled edge, and the substrate commitment is intact.** `put_under`
(`scope_tree.py:25`) calls `g.add_relation(node, UNDER, scope)` — the ordinary S-P-O constructor. The
physical shape is a directed path `node → <under>-relnode → scope`, where `<under>` is a NODE (a `<…>`
token, auto-flagged control), exactly as [[spo-directed-path-no-labeled-edges]] requires. The
docstring's `node --<under>--> scope` is *notation for the path* and should be reworded, because it
reads as a labeled edge and invites exactly this (correct) suspicion.

**DEFECT (found 2026-07-24 while checking the above; not yet filed).** `scope_of` documents "One
parent per node in the tree" and returns the FIRST `<under>` relation yielded by `relations_from`.
`put_under`'s guard is `if scope_of(g, node) == scope: return` — which suppresses re-adding the SAME
parent but does NOT prevent adding a SECOND, DIFFERENT parent. Two `put_under` calls with different
scopes therefore leave two memberships, and `scope_of` returns whichever iteration order surfaces
first: an order-dependent, silent mis-scoping.

This is load-bearing for everything below: **"exactly one parent scope per queue" is the invariant of
§4**, and the data structure cannot currently guarantee it. It is also cheap to fix, and it should be
fixed *before* 1c migrates real membership onto `<under>`, not after. Two candidate fixes:

- **(a) enforce** — `put_under` raises on a conflicting existing parent (single-parent becomes an
  invariant of the constructor); or
- **(b) admit multi-parent and derive** — keep several `<under>` relations, and make `scope_of`
  ill-defined by construction, replacing it with `scope_chain` over a genuine DAG. The docstring's own
  aside (*"an `<under>` edge per parent = arbitrary nesting"*) suggests this was contemplated.

**Recommendation: (a).** Multi-parent scopes make the join boundary ambiguous (§4) and buy nothing the
reframe currently needs; nesting is already arbitrary-DEPTH under single-parent. If a genuine
multi-parent case appears, it is a lattice, and it should be designed then, deliberately.

**Also re-check under 1c:** [[scope-nodes-survive-incidental-gc]] exempted `<hypothesis>` from
edge-based GC because a scope node was EDGELESS by design (membership was a valued attr). Once
membership is a relation, scope nodes HAVE edges, and the exemption may become unnecessary — or may
interact. Verify rather than assume; the failure mode last time was silent.

---

## 4. The invariant

> **Every queue has exactly one parent scope and exactly one join boundary.**

Unpacked:

1. **One queue per scope node.** Minting a scope forks a queue; the scope node IS the queue's identity.
   No queue exists without a scope, and no scope runs work outside its queue.
2. **Isolation is the default.** A queue may read base ink and its ancestors' ink (the visibility rule
   already implemented at `scope_tree.is_visible`); it may WRITE only under its own scope.
3. **One join boundary.** Results leave a queue at exactly one place, by the declared crossing rule.
   This is the transplanted lesson of [[derivation-frame-consolidation]]: a read-projection isolates
   reads but not WRITES; only a single merge-back point makes locality real.
4. **Draining is demand-gated and per-queue.** A queue runs when something demands its scope, not
   because it is non-empty. This preserves [[agent-not-theorem-prover]] and is why the topology does
   not re-import eager exhaustive completion.

Composition = nesting, isolation = default, crossing = a DATA rule — the scope reframe's three
commitments, restated in execution terms. That correspondence is the point: **the execution topology
should not be a second structure to keep in sync with the scope tree; it should be the scope tree.**

---

## 5. Why nested, and not one global queue — the NAF argument

This is the argument that decides the shape, and it is a soundness argument rather than a taste one.

Negation-as-failure requires a well-defined DRAINED state: "absence decides" is legal only when
nothing further can arrive. **A single global event queue destroys that property** — no absence is
ever final, because any pending event might still produce the fact. That silently un-sounds the
stratification `run_bank` performs ([[stratification-both-engines]]), and it would do so without a
failing test, which is the worst available failure mode.

A NESTED topology makes the property COMPOSITIONAL instead:

> A scope's NAF is decidable once its own queue AND all its descendants' queues have drained.

The join point is precisely the moment at which "absence decides" becomes legal. This is a *stronger*
guarantee than the global stratification in force today, and it is the only version that survives
`suppose` nested inside `suppose` — which the current single-valued `SCOPE` attr cannot even
represent (`scope_tree.py:25` says so outright: one attr = one scope, which is why scopes don't
compose today).

Two corollaries worth stating, because they are free:

- **Alternatives are sibling queues.** `suppose` branches, counterfactuals, abduction — and the chart
  parser's ambiguous parses ([[homoiconic-grammar-spike]]) — all become siblings, isolated by default,
  promoted only through the declared crossing. The ambiguity case is the cheapest validation of the
  topology available: it exercises fork/join on machinery that is already understood, with no
  semantics at risk.
- **Cycles still drain.** `reactive.py` already argues materialization is monotone, so a reactive cycle
  drains rather than loops. Nesting does not disturb that; it scopes it.

---

## 6. The ISA does not change — the queue mode is the FOURTH computation mode

The user's framing is right, and the reason is stronger than convenience: **the fork primitive already
exists.**

- **`SUSPEND` (`machine.py:1029`) captures the whole control state as a resumable `Continuation`**
  handed to the driver (`machine.py:1119`). A FORK is "suspend, and keep N continuations instead of
  one". A JOIN is "resume the parent with the children's merged state stream".
- **`CALL`/`RET` over `self.stack` (`machine.py:1117`, `1133`) is fork/join with fan-out exactly 1,
  joined immediately.** So the control stack is already a queue topology — a degenerate one. The queue
  mode generalizes the stack into a TREE; it does not replace it.
- **The data path is untouched.** `SEED`/`FOLLOW`/`TEST`/`JOIN`/`GRADE`/`MINT`/`EMIT` and the whole
  match/apply loop are indifferent to which queue is stepping. No new data-path instruction is implied.

So the modes stack, in order of generality, and each is the previous one's generalization:

| # | mode | control state | fan-out |
|---|---|---|---|
| 1 | straight-line `Machine.match`/`apply` | none (a state stream) | — |
| 2 | `ControlMachine` — PC + control stack | `self.ctrl`, `self.stack` | 1 (CALL/RET) |
| 3 | demand frame — per-frame agenda | `Frame.agenda` | N, joined by set-union |
| 4 | **queue mode — per-scope queues, forked and joined** | a tree of queues | N, joined by the crossing rule |

Mode 4 is mode 3 with the frame replaced by a SCOPE and the set-union join replaced by the declared
crossing. Stated that way, the change is smaller than it sounds, and the firmware-over-ISA commitment
([[firmware-over-isa-design]]) is preserved: the scheduler is firmware, expressed as programs, not a
Python driver.

**Minimum plausible opcode delta: two terminators** (`FORK`, `JOIN`) — and possibly zero, if a fork is
expressible as `SUSPEND` plus a scheduler convention. Deciding that is implementation work, not design
work, and it should be settled by a spike rather than by argument.

---

## 7. What IS genuinely new: the scheduler

Not the queues. The **choice of which runnable queue to step next** — today implicit in the call order
of Python drivers, and about to become explicit and load-bearing:

- fairness / starvation across siblings;
- depth-first (finish a hypothesis) vs breadth-first (compare alternatives) — and these are genuinely
  different for `suppose` vs ambiguity;
- per-branch fuel, and what an exhausted branch reports (`UNKNOWN` is the existing honest answer —
  [[think-harder-chapter]]);
- priority when one sibling's result would prune another.

By [[mechanism-policy-separation]] this is POLICY and belongs in the CONTROL REGISTER FILE, not the
data graph — the same call the focus stack got (`focus.py`: pure attention bookkeeping that NO rule
reasons about, therefore `registers`, not `<focus>` nodes). **A rule must never match on a scheduling
decision**; if it could, scheduling would become semantics, which §8 forbids.

This is where the complexity of the whole proposal actually lands, and the design should say so
plainly rather than discovering it during implementation.

---

## 8. What this design FORBIDS: focus must not change what a rule means

The original framing included *"depending on where the focus is, they do different things."* **This
design deliberately does not grant that**, and the constraint is the most important line in the
document.

A rule whose meaning varies with ambient state is DYNAMIC SCOPING. It is less composable, not more —
a rule can no longer be read in isolation, and it is the same locality bug class already paid for once
in [[derivation-frame-consolidation]] (a read-projection isolates reads but not writes; the fix was a
materialized copy with one merge boundary).

The fork/join framing gives the safe version for free:

> **Focus selects WHICH QUEUE is drained. It never selects WHAT A RULE DOES.**

The rule stays statically readable; the scope is an ordinary nested argument, explicit in the fact.
**Relativization, not ambient state** — which is precisely what the reframe already committed to
([[scope-reframe-relativization]]). Focus remains ATTENTION; it never becomes SEMANTICS.

**Consequence for Step 4 (`force + vantage as data`).** A vantage is *which queue you are reading
from*. That is a constraint on Step 4, not a rewrite of it — but it is the reason to have this design
on paper BEFORE Step 4 rather than after, since Step 4 would otherwise commit to an answer implicitly.

---

## 9. The question the plan already contains

`implementation_plan.md` currently lists, as remaining Step 2 work:

> *"(optional) move the `resolve_crossings` driver into `reactive.fire` — a driver-location refinement;
> the substance is done, the crossing is already fully DATA."*

Under this design that is **not a refinement**. `resolve_crossings` is a fixpoint driver scoped to a
crossing; `reactive.fire` is the global event queue. "Where does this driver live" IS "what is the
execution topology", and the answer follows from §4 rather than from convenience:

> `resolve_crossings` is the JOIN of the crossing's queue. It belongs wherever joins live — which
> means it should NOT be fused ad hoc into the global `reactive.fire`, because that would place a
> scope-local join on the global queue and erase exactly the locality §5 depends on.

If the queue mode is adopted, the driver becomes the first instance of the general join and needs no
special home. If it is rejected, fusing it into `reactive.fire` is fine. **Either way the decision
should be taken deliberately; today it is scheduled to be taken by default.**

---

## 10. Sequencing (proposed — not a plan re-point)

1. **Fix the §3 defect first** (single-parent enforcement in `put_under`), independently of everything
   else. It is small, it is a real order-dependent bug, and 1c will entrench it if it lands first.
2. **Ratify or reject this document.** No code.
3. **1c (membership migration onto `<under>`)** — currently marked optional *because nothing depends on
   it*. This design would be its first dependent: the topology's premise is that queues nest the way
   scopes nest, and `reframe_active` is still False on all data (`scope_of` is None everywhere, the
   visibility filter a no-op). **Implementing the queue mode before 1c would mean designing against a
   hypothetical.**
4. **Step 3 (negation-as-interposing-node) proceeds in parallel, unblocked** — it is independent of all
   of the above.
5. **Spike the opcode delta** (§6): can a fork be expressed with existing `SUSPEND` + a scheduler
   convention, or are `FORK`/`JOIN` terminators required? Cheapest decisive experiment: the chart
   parser's ambiguous parses as sibling queues (§5), which risks no semantics.
6. **Decide implement-or-defer at the Step 3 / Step 4 boundary**, with the spike result in hand.

---

## 11. Prior art — this model is well-trodden, in four traditions that rarely cite each other

The answer to *"is this computation model used by any symbolic system in the literature?"* is **yes,
extensively** — but the pieces are distributed across four communities, and the value of knowing this
is mostly that each has already catalogued the failure modes we would otherwise rediscover.

**(A) Contexts / truth maintenance — the SCOPE half.**
- **ATMS (de Kleer 1986)** is the closest classical ancestor of the scope reframe itself: every datum
  carries a LABEL of the environments (assumption sets) under which it holds, and multiple contexts
  are maintained simultaneously rather than by backtracking. JTMS = one context; **ATMS = sibling
  scopes, exactly the alternatives of §5.** The label-propagation algorithm IS a join.
- **Cyc microtheories** and **Guha's "Contexts: A Formalization and Some Applications" (1991)** —
  nested contexts with **lifting rules** to move a proposition from one context to another. "Crossing
  = a data rule" is literally a lifting axiom. This is the most direct precedent for the reframe's
  central commitment, and Cyc's experience is also the cautionary one (microtheory proliferation,
  and lifting rules becoming the hard part — worth reading as a risk, not just a citation).
- **McCarthy's `ist(c, p)`** — "p is true in context c", with explicit entering/exiting. The formal
  root of both of the above.

**(B) Tabled resolution — the COMPLETION half, and the rigorous version of our §5.**
- **SLG resolution / tabling (Warren, Swift; XSB)** maintains a TABLE per subgoal — a queue per
  scope, with the same locality as `Frame.agenda` — and its hard problem is **completion detection**:
  deciding when a table is finished so that negation may be evaluated against it. The answer is
  SCC-based completion over the subgoal dependency graph. **Our §5 argument ("a scope's NAF is
  decidable once its own queue and its descendants' have drained") is a rediscovery of SLG
  completion**, and XSB is the existence proof that it works at scale.
- **Well-founded semantics (Van Gelder, Ross & Schlipf)** and **stable models / ASP (Gelfond &
  Lifschitz)** are the formal accounts of what negation MEANS when completion is not available. If
  the queue topology is adopted, WFS is the semantics to check the design against — it is the
  standard answer to the exact question §5 raises.

**(C) OR-parallel logic programming — the FORK/JOIN-over-alternatives half.**
- **Aurora and Muse** (OR-parallel Prologs, late 1980s–90s) forked alternative branches exactly as
  proposed, and hit **our scope-local identity problem head-on**: how do sibling branches see
  different bindings of the same variable? The catalogued solutions — **binding arrays, hash windows,
  version vectors, and copying** — map one-to-one onto the trade-off already fought here in
  [[derivation-frame-consolidation]] (projection vs materialized copy). We chose copying; so did Muse.
  **This literature is worth reading before implementing, because it is the same problem with thirty
  years of measurements attached.**
- **The Andorra model / Andorra-I** (D.H.D. Warren, Costa) — run determinate work first, fork only
  when forced. That is a ready-made scheduling policy for §7, and a well-studied one.

**(D) Dataflow with nested scopes — the PROGRESS-TRACKING half, and the modern engineering answer.**
- **Timely dataflow / Naiad (McSherry et al.)** is startlingly close to this proposal: computation is
  organized into **nested scopes**, each with its own timestamp coordinate, with explicit `enter`/
  `leave` operators (fork and join) and **frontier-based progress tracking** to determine when a
  nested scope's work is complete. It exists precisely to support *incremental* computation — which
  is what the reactive core is. If one system should be read closely before implementing, it is this
  one: it solves "how do I know this nested scope has drained" as an engineering problem, at scale.
- **Tagged-token dataflow (Arvind's U-interpreter)** and **colored Petri nets** — the older form of
  the same idea: a token's TAG identifies which invocation/iteration/context it belongs to, so a
  dynamic queue topology needs no static structure.

**Adjacent, worth one line each.** **Soar** creates a subgoal on IMPASSE and returns results to the
parent context by chunking — fork-on-impasse, join-by-result, and the closest match in the production-
system tradition (its agenda/conflict-resolution is also the ancestor of our dirty-grain queue).
**Concurrent constraint programming (Saraswat)** — ask/tell over a shared store where agents SUSPEND
until entailment, which is demand-gating with a formal semantics. **Delimited continuations /
algebraic effects** are the PL-side general form of `SUSPEND`/`Continuation` (§6), and would give
`FORK`/`JOIN` a principled typing if we ever want one. **Actor model** contributes dynamic creation
and message queues but notably *not* joins.

**What appears NOT to be in the literature — stated carefully.** Each of the four traditions has a
piece; what I could not find is a system that has all four **in one uniform model over one uniform
substrate, with the model itself represented in that substrate** (rules-as-data, programs-as-data,
the reflexive property this project is actually after). ATMS has contexts but a fixed control regime;
XSB has completion but no scoped alternatives as first-class objects; Naiad has nested scopes but no
epistemics at all; Cyc has lifting but its control is conventional. **That combination is the
plausible novelty — and it is a claim about UNIFORMITY, not about any individual mechanism, each of
which is old and well-understood.** It should be stated that way, since every individual part has a
citation and an implementation that predates us.

---

## 12. Risks

- **Arc-hopping.** The honest reading of this repo's history — unified-representation → scope-reframe
  inside one day, `prop:` built then retired, slice-1c landed → reverted → re-derived, the intake
  rewire attempted and reverted twice — is that the characteristic failure mode is starting a better
  arc, not finishing a worse one. This document is deliberately design-only, and the §0 tripwire is
  the guard.
- **The scheduler is the real cost** (§7), and it is easy to under-estimate because the queues look
  like the work.
- **Provenance.** A promoted fact must record the queue/scope that derived it, or `why` renders
  `(given)` — an order-sensitivity the plan already notes for pre-derived facts.
- **The single merge boundary must stay single** (§4.3). If every queue can write anywhere,
  flip-identity returns, and it returned twice already.
- **Perf is not a motivation and should not be claimed as one.** Judge at session scale
  ([[ugm-scope-session-sized]]); the case here is composability, and if the design is defended on
  throughput it will be defended on the wrong axis.

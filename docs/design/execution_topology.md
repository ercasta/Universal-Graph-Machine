# Execution Topology — nested queues with dynamic forks and joins

> **Status: ⭐ RATIFIED 2026-07-25 by the user, after review.** Drafted 2026-07-24 as design-only; the
> review (§0) settled the four questions it had left open, the §10.5 spike came back GO with a ZERO opcode
> delta (§6b), and two real defects it surfaced are fixed and tested. What is ratified is the MODEL — the
> invariant (§4), the queue-item identity (§4b), the data-flow rule (§4c), the corrected drain condition
> (§5b), and the constraint on Step 4 (§8). What is NOT yet built is the scheduler (§7); §10.3 stands —
> **1c comes before any queue-mode implementation**, so the topology is designed against real data rather
> than a hypothetical.
>
> Its original purpose was to answer ONE question the plan contained mislabelled as cosmetics — *where
> does the `resolve_crossings` driver live* (§9) — by deriving the answer from a general principle instead
> of a coin flip, and to record the design before Step 4 (`force + vantage as data`) made an implicit
> commitment to it.
>
> Companions: `scope_reframe_audit.md` (the north star this serves), `reactive_core.md` (the existing
> event queue), `composition_architecture.md`, `../attic/isa_control_machine.md` (the control path this
> extends), `mechanism_policy_separation.md` (where the scheduler must live).
>
> **TRIPWIRE (set by the user's own sequencing rule).** If this design cannot be stated without also
> rewriting Steps 3 and 4 of the scope reframe, that is evidence the queue topology is a NORTH STAR
> rather than a refinement — and the response is to re-point deliberately, not to drift. As drafted,
> it does not: Step 3 is untouched, and Step 4 gains a constraint (§8) rather than a rewrite.
>
> **REVISED 2026-07-25** after review with the user: §0 records the decisions taken, §3 now separates the
> defect from the single-parent DESIGN question, §4b/§4c are new (queue-item identity; data flow across
> the boundary), and §5 carries a substantive CORRECTION to its own drain condition.
>
> **AMENDED 2026-07-26 — §13 (rules as ACTIVE CELLS).** A second proposal, spiked
> (`bench/spike_cell_network.py`) and folded in as a REFINEMENT rather than a re-point: it supplies the
> DISPATCH half §4b left open (how a rule finds its data) without changing what a queue item is. It
> carries one amendment that reaches back into the ratified core — **§5's drain predicate must be
> restated** (§13.2), because a network of cells is permanently occupied — and promotes monotone
> materialization from an incidental property to the termination argument.

---

## 0. Decisions taken in review (2026-07-25)

Four, from the questions the draft failed to answer. They are recorded here rather than buried in the
sections they amend, because each one closes something the draft left open by omission.

**(0.1) The motivation is EMERGENCE, not parallelism.** In the user's words: *"the reason we are adopting
queues is not parallelism, it is the emergence of the computation model (vs a 'pre-written' algorithm)."*
This is the positive statement that §12's last risk ("perf is not a motivation") only had the negative of.
The queues are worth having because reasoning becomes something the substrate DOES rather than something a
Python driver stages — the computation-model half of the uniformity claim in §1. Any defence of this design
on throughput or concurrency is a defence on the wrong axis, and should be read as evidence of drift.

**(0.2) Queues run SEQUENTIALLY. No parent/child parallelism.** Settled deliberately, not deferred: a
parent drains before its children run. This is what makes §5's drain condition sound without a snapshot
(see the correction in §5) and it costs nothing the engine was using. Sibling parallelism is *possible*
later and is a genuinely open question — it would require either copying the graph (so a sibling cannot
modify the common scope) or a join that takes one child at a time — but it is **out of scope**, precisely
because it would be adopted for a reason (0.1) rejects.

**(0.3) A queue item is a CONTINUATION, not a rule, an instruction, or a fact.** §4b.

**(0.4) Single-parent is a COST decision, not a metaphysical one — and it is separable from the defect.**
§3.

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

*(Re-verified against source 2026-07-25: `scope_tree.py:35` returns the first `<under>` from
`relations_from` (`:40`); the `put_under` guard at `:30` compares against exactly that. Confirmed.)*

**The defect and the design question are SEPARABLE, and the draft conflated them.** Two distinct claims:

1. **The code assumes one parent while the data structure permits several.** That disagreement is a bug
   under *any* design — it yields order-dependent, silent mis-scoping — and it should be closed whichever
   way the design question goes.
2. **Whether scopes SHOULD have one parent** is a separate call, taken below.

Claim 1 is load-bearing for everything after: **"exactly one parent scope per queue" is the invariant of
§4**, and the data structure cannot currently guarantee it. It is cheap to fix, and it should be fixed
*before* 1c migrates real membership onto `<under>`, not after. Two candidate fixes:

- **(a) enforce** — `put_under` raises on a conflicting existing parent (single-parent becomes an
  invariant of the constructor); or
- **(b) admit multi-parent and derive** — keep several `<under>` relations, and make `scope_of`
  ill-defined by construction, replacing it with `scope_chain` over a genuine DAG. The docstring's own
  aside (*"an `<under>` edge per parent = arbitrary nesting"*) suggests this was contemplated.

**Recommendation: (a) — but for a better reason than the draft gave.** The draft said multi-parent "buys
nothing," and that is wrong: multi-membership is meaningful and this document's own §11 supplies the
precedents. A *fact* under two scopes is an **ATMS label** (a datum carrying a set of environments); a
*scope* under two parents is **Cyc microtheory multiple inheritance**. Both are real, both are old.

The honest case for single-parent is a COST argument, and it is about WRITES, not reads:

- **Drain survives a DAG.** §5's condition only needs descendants, which are well-defined on a DAG.
  Multi-parent does not break the soundness argument — this is worth stating because it is the objection
  one expects to be decisive and it is not.
- **The join boundary does not survive it.** §4.3's single merge-back point is the transplanted lesson of
  [[derivation-frame-consolidation]]. Under multi-parent a result leaving a scope has two destinations,
  and saying what the merged thing MEANS requires a label algebra with minimality. That is the ATMS's
  hard part, and §11 already records it as Cyc's cautionary tale (the lifting rules became the expensive
  component). The cost is not the extra edge; it is the algebra the extra edge obliges.
- **Visibility stops being a one-liner.** `is_visible` would have to choose between *any* of the node's
  scopes lying on the vantage's chain (disjunctive — weakens isolation) and *all* of them (conjunctive).
  Neither is obviously right, so "isolation is the default" becomes a semantic decision rather than a
  three-line predicate.

**And the expressiveness loss is smaller than it looks, because the reframe already answers "holds in
both": a CROSSING.** The `denotes` link between a scoped reference and its base referent — together with
the `@!?scope` mint-on-cross read (`chain._relativized_st_matching(mint_missing=True)`) — is how the same
thing is seen from two scopes: two scoped copies plus a promotion rule, never one node with two
memberships. Multi-parent would be a SECOND, competing answer to a question the reframe has already
answered, which is the actual argument against it.

So: single-parent stands, on the ground that **the crossing rule remains the sole way facts move between
scopes**. If a genuine lattice case appears it is an ATMS-style label design, and it deserves to be
designed deliberately rather than arrived at by `put_under` silently accepting a second edge.

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

   **And it must hold in BOTH HOMES, by different means.** The clause above is about the GRAPH; §4b's
   split means the same invariant has a second half in the REGISTERS, and stating only the first is how
   the §6b defect stayed latent. They are the same invariant in shape and nothing alike in mechanism:

   | | GRAPH (facts) | REGISTERS (control) |
   |---|---|---|
   | what is isolated | what a branch may read/write | a branch's control window (`ctrl`, control stack) |
   | enforced by | `<under>` + `is_visible` + the write discipline | COPY discipline at capture/restore (`_copy_frames`) |
   | sharing between siblings | PARTIAL and rule-governed — base ink is deliberately shared, and the join writes to it | TOTAL — there is no register analogue of base |
   | inheritance from the parent | LIVE (§4c), which is what forces the parent-first rule of §5b | a SNAPSHOT at fork (`dict(cont.ctrl)`) |
   | a leak causes | believing something false (an epistemic error) | computing the wrong thing (a control error) — never a change of MEANING, since §8 keeps registers invisible to rules |
   | caught by | inspecting the structure (`scope_of` is checkable) | only by a test that resumes one continuation twice |

   The last row is the practical one: the graph half is *checkable* and the register half is not, so the
   register half needs a standing test rather than an invariant one can look at
   (`test_repeated_resumption_does_not_share_the_caller_register_window`). Fixing either does nothing
   for the other.
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

## 4b. What actually goes through a queue — the ITEM

The draft specified a topology and never said what flows through it. That omission is not cosmetic: the
three queues of §2 each answer differently, which is the §1 non-uniformity showing up at item level.

| queue | item TODAY |
|---|---|
| `Frame.agenda` (`chain.py:1694`) | a **demand** — a goal pattern |
| `reconsider.DIRTY_REG` / `_affected` | a **delta** — a dirty `(pred, obj)` grain |
| pending `<call>` (`dispatch.py`) | a **graph node** |

Three queues, three item types. The answer that follows from §6's own claim — *the ISA does not change,
the queue mode is a scheduler over programs the machine already runs* — is that the item is **none of the
three**:

> **A queue item is a RESUMABLE UNIT OF WORK: a `(program, state-stream, scope)` triple — precisely the
> `Continuation` that `SUSPEND` already produces (`machine.py:1029`, handed to the driver at
> `machine.py:1119`), tagged with the scope that owns it.**

Not rules, not instructions, not graph fragments. Rules and instructions are what the item is suspended
*over*; the graph is the shared store queues read and write under §4.2. **No part of the graph is ever in
a queue.** This also re-unifies the table: the three rows become three ways of CREATING a continuation —
a sub-goal raised (pull), a delta triggering a reaction (push), a tool call crossing an async boundary —
which is [[reactive-core-north-star]]'s PUSH==PULL==FORWARD restated one level up, at the scheduler.

**What this section does NOT say, and §13 supplies.** It settles what FLOWS and is silent on how a rule
FINDS ITS DATA — today "run the bank against the graph", i.e. search. §13 answers that with an index over
parked continuations, and the answer is compatible: the item is still a `Continuation`, unchanged.

**An inconsistency this exposes, and its resolution.** §7/§8 hold that scheduling is policy, lives in
registers, and that no rule may match on it. But the `<call>` queue is *materialized nodes in the graph*,
which rules can and do see. Rather than treat `<call>` as a violation, split the notion three ways:

| | lives in | rules may see it? | why |
|---|---|---|---|
| the **work request** | the GRAPH (a `<call>` node) | **yes** | "I am waiting on X" is something the agent must be able to reason about — it is semantics |
| the **work item** | REGISTERS (a continuation) | no | machinery for resuming; carries no meaning |
| the **scheduling order** | REGISTERS (policy) | no | [[mechanism-policy-separation]]; §8 forbids it becoming semantics |

§8 then holds unchanged: focus selects which queue drains, never what a rule does.

---

## 4c. How data crosses the boundary — and where "global state" went

Two questions the draft also left open: how does data flow parent→child, and how does a child reach the
graph? **They have the same answer, and it is already implemented** — the visibility predicate, which is
not a transfer mechanism at all. From `scope_tree.py:63`:

```python
ms = scope_of(g, node)
if ms is None:     return True               # base ink visible from EVERY vantage
if active is None: return False              # a base read cannot see scoped ink
return ms in scope_chain(g, active)          # `active` itself, or an ancestor
```

Since `scope_chain(active) == [active, parent, grandparent, …]`, a node is visible from `active` iff its
scope is `active` **or an ancestor of it**. `tests/test_scope_reframe_diff.py:56` pins exactly the
asymmetry: `is_visible(child, s2)` is true, while `is_visible(child, s1)` — from the PARENT — is False.

- **parent → child: free, and not a flow.** A child does not receive its parent's data; it INHERITS it by
  reading from a deeper vantage. No copy, no message, no queue traffic. This is lexical scoping, which is
  what makes §8's ban on dynamic scoping affordable: inheritance is static, in the tree, readable off the
  fact.
- **child → parent: only through the join** — the crossing rule (`_promote_held`), §4.3's one boundary.
- **sibling → sibling: nothing.** Only via a common ancestor, through two joins. That isolation is what
  makes the alternatives of §5 sound.

**There is no global state.** `scope_of() is None` means base; base is visible from every vantage; no
`<under>` edge means you ARE the root. **Base is scope `None` = the root of the tree**, so the graph is not
something children reach around the topology to touch — it is the outermost queue's ink, inherited by the
same rule that gives a child its parent's, applied at depth 0. Writes are the asymmetric half: a child
writes only under its own scope and never mutates base directly. The one place base is written from inside
a crossing is `@!?scope` mint-on-cross, and that is not a violation — it fires at the JOIN, not in the
child's queue.

Entity identity crosses by **copy plus link**, never by sharing: the child's `lion` is its own node with
`denotes →` base `lion`. Across the boundary identity holds; visibility does not.

---

## 4d. Trigger-like rules — the WATCHER, and why the pool is not seeded

A question the draft does not address: can this model carry **"watch out for X"** — a standing,
trigger-like rule that fires when something shows up, rather than when something asks? It can, and the
mechanism is mostly already built; but the naive reading ("constantly seed the queue from a pool of
trigger rules") is both the expensive shape and the unsound one, so both halves are recorded here.

**Why it needs a home at all.** Today a watcher has exactly two possible implementations, and both are
bad:

| shape today | why it fails |
|---|---|
| a forward rule that fires eagerly | violates [[agent-not-theorem-prover]]; costs every watcher on every round |
| a demand nobody ever raises | never fires — nothing asks the question |

§4b supplies the third, without new machinery: **a watcher is a continuation parked on a condition.**
That is the *push* row of §4b's table — "a delta triggering a reaction" — already named as one of the
three ways a continuation gets created. A watcher is therefore not a fourth item type; it is the push
constructor used for a standing rule instead of a one-shot reaction.

**Do NOT seed; INDEX.** `reactive.py` already owns the dispatch half — body→head trigger dispatch keyed
by dirty grain (`reconsider.DIRTY_REG`, §2's second row). Watchers should be indexed by trigger condition
and woken on match, not re-enqueued each round:

- re-seeding a pool: `O(watchers × rounds)`;
- indexed wake: `O(matches)`.

The distinction matters beyond cost: a re-seeded pool makes every round non-empty, which is the drain
problem below in its worst form.

**What is genuinely new is the SCOPING, not the firing.** The firing already works. What the topology
adds is that a watcher acquires a place in the tree:

- **Scoped watchers.** *"While considering H, watch out for X"* lives in H's queue and dies when H is
  dropped. Today a trigger rule is unavoidably global — it has no vantage to be relative to. This is
  [[scope-reframe-relativization]] applied to control rather than to content.
- **Sibling isolation.** Independent watchers are sibling queues (§5b's first corollary), so one
  watcher's derivations cannot contaminate another's.
- **A declared crossing.** What the watcher CONCLUDED reaches base through the join (§4.3), not by
  writing wherever it likes — which is the §4.3 invariant doing the work it was introduced for.

**The watcher instance is a work REQUEST.** Per §4b's three-way split, the standing watcher is a graph
node, rule-visible, for the same reason a `<call>` node is: *"I am watching for X"* is something the agent
must be able to reason about, and it makes **"why am I watching for this?"** answerable. Only the resumed
continuation and the wake order stay in registers. A Python trigger table could not answer that question,
which is [[composability-principle]]'s test applied to this mechanism — and it passes only in this shape.

### The hazards — one of them sharp

1. **The sharp one: §5b's drain condition.** A trigger pool is a source of UNBOUNDED ARRIVAL. If a
   watcher may inject work at any time, no absence is ever final and NAF loses the drained state §5
   requires — §5's argument against a single global queue, arriving by a new route. So: **a watcher is
   confined to a queue whose drain is defined, and a scope's NAF is decidable only once its watchers have
   quiesced along with its descendants.** Getting this wrong re-imports precisely the unsoundness the
   nested topology exists to prevent, and does so silently.
2. **Fire on a positive delta, NEVER on an absence.** [[recall-explicit-not-autofire]] is the close
   cousin: auto-firing on a demand MISS was proven unsafe — it flips NAF and is self-reinforcing.
   Push-on-fact is monotone and safe; push-on-absence is neither. This is a hard line, not a default.
3. **§8 is easy to violate here.** A watcher selects which queue drains; it must never change what a rule
   MEANS. The tempting implementation — "watch out for X" sets ambient state that other rules read — is
   dynamic scoping wearing a trigger costume, and §8 forbids it.

**Verdict.** Good fit; the mechanism is mostly present (`SUSPEND` + reactive trigger dispatch); the win is
scoped, composable, introspectable watchers rather than any change to firing behaviour; and the design
cost lands entirely on the drain condition. **Not in scope for the sequencing of §10** — it is a
consequence to record now and build after fork/join, not a fifth mode.

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

### 5b. CORRECTION (2026-07-25): the drain condition above is INSUFFICIENT as stated

The condition names descendants and is silent about ANCESTORS. That silence is unsound, because the
inherited view of §4c is **live, not a snapshot** — `is_visible` evaluates against the current graph at
read time. So a parent that is still running can produce a fact the child would have seen, *after* the
child has drained and already let absence decide. The child's NAF conclusion is then stale by
construction, which is [[reconsider-arc]]'s problem lifted across queues.

Note what this means about §5's own self-description: it calls itself a rediscovery of SLG completion, and
**it rediscovered only half of it.** SLG completion is SCC-based over the subgoal DEPENDENCY graph rather
than tree-based, for exactly this reason — the write topology is a tree, but the READ dependency is not,
and completion must follow read-dependency. Three ways to close it:

- **(i) drain is not bottom-up** — require ancestors drained too, i.e. follow read-dependency and accept
  that completion detection is a graph problem (the full SLG answer; the most general, the most work);
- **(ii) snapshot at fork** — stable, bottom-up drain preserved, but this is the projection-vs-copy
  trade-off again ([[derivation-frame-consolidation]]) with the OR-parallel Prolog measurements attached
  (§11 C: binding arrays, hash windows, version vectors, copying);
- **(iii) schedule the problem away** — a parent drains before its children run. The inherited view is
  then stable BY CONSTRUCTION and the bottom-up condition above becomes correct as written.

**ADOPTED: (iii)**, per decision §0.2. It needs no new mechanism — only a scheduler commitment — and the
concurrency it forgoes between parent and child is concurrency this engine was never going to use.
Two things worth recording about the choice:

- It is the **Andorra policy** that §11 (C) already nominates for §7, arriving here from an independent
  direction. Two derivations converging on one scheduling rule is weak evidence, but it is evidence.
- It is a REAL constraint on §7, not a default: the scheduler may not interleave a parent with its own
  descendants, and any future sibling parallelism (§0.2) must preserve it per-lineage.

**AMENDED AGAIN by §13.2 (2026-07-26).** The condition above says "drained" and means "the queue is
empty". Under the cell model that is no longer expressible — the network is PERMANENTLY OCCUPIED. Read
every occurrence of *drained* below as **empty delta queue AND no ENABLED cell**, and note that its
precondition (monotone materialization) is now load-bearing rather than incidental.

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

### 6b. SPIKED 2026-07-25 — **the opcode delta is ZERO** (`bench/spike_fork_join_opcodes.py`)

Run rather than argued, per §10.5. The hypothesis under test: *the scheduler forks by RESUMING ONE
CONTINUATION N TIMES, once per child scope, and joins by running the crossing after every child drains.*

| case | result |
|---|---|
| 1 — fork at TOP LEVEL (empty control stack) | **PASS** — two siblings, each writing under its own scope, no contamination |
| 2 — fork INSIDE A `CALL` (non-empty stack) | **FAIL** — sibling B observed caller register `depth=6`, sibling A's decrement |
| 2b — same program, frame tuples copied one level deeper | **PASS** — `[7, 7]`, contamination gone |
| 3 — the JOIN | **PASS** — children invisible to base until one boundary promotes a winner |

**VERDICT: GO, zero new terminators.** Fork is resume-N-times; join is the crossing run at drain. §6's
claim that "the fork primitive already exists" holds as stated.

**But the spike found a real latent defect, and case 2b is what makes the verdict decisive rather than
inferred.** `SUSPEND` captures `list(self.stack)` (`machine.py:1229`) — a SHALLOW copy. The frame tuples
`(ret_pc, saved_stream, saved_ctrl)` are shared across every resumption, and `RET` does
`self.ctrl = saved_ctrl` (aliases, does not copy), so a caller-side `SETI`/`DEC` after the return mutates
a dict the next resumption will restore. **A `Continuation` is therefore not currently the immutable value
§4b requires it to be** — it is single-resume-safe only, which is all anything does today, which is why
no test catches it. Case 2b re-runs the identical program with the frames copied one level deeper and the
contamination vanishes, so this is CAPTURE DEPTH, fixable in `SUSPEND`, **not** a missing control
primitive. It is a prerequisite for the queue mode, not an argument against it.

Two things the spike also settled in passing, both worth recording because they were assumptions:

- **State streams are already safe.** `State.bind`/`scaled` return new values (`machine.py:127`), so the
  stream needs no deepening — only the control registers do.
- **The graph needs no forking at all.** Siblings share `g` and stay isolated purely by writing under
  their own scope (§4c), which is the execution-level confirmation that isolation is a WRITE discipline
  rather than a storage one.

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

**Narrowed by §0.2 and §5b.** One degree of freedom is now spent rather than open: **parent-before-children
is FIXED**, because §5b's drain condition depends on it. Queues run sequentially; the scheduler's remaining
latitude is over SIBLING order (and per-branch fuel), not over interleaving a lineage. That is a real
reduction in the §7 design space — most of the classical scheduling literature's difficulty is in the
interleaving — and it is the reason the sequential commitment is cheap rather than merely conservative.

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
   Per §3 this step discharges CLAIM 1 only (code and data must agree); it is correct to land even if the
   single-parent design decision is later revisited.
2. ~~**Ratify or reject this document.**~~ — **RATIFIED 2026-07-25** (see the status header).
3. **1c (membership migration onto `<under>`)** — currently marked optional *because nothing depends on
   it*. This design would be its first dependent: the topology's premise is that queues nest the way
   scopes nest, and `reframe_active` is still False on all data (`scope_of` is None everywhere, the
   visibility filter a no-op). **Implementing the queue mode before 1c would mean designing against a
   hypothetical.**
4. **Step 3 (negation-as-interposing-node) proceeds in parallel, unblocked** — it is independent of all
   of the above.
5. ~~**Spike the opcode delta** (§6)~~ — **DONE 2026-07-25, `bench/spike_fork_join_opcodes.py`: the delta
   is ZERO** (§6b). Existing `SUSPEND` + a scheduler convention suffices; no `FORK`/`JOIN` terminators.
   Carried forward as a PREREQUISITE rather than a step: `SUSPEND`'s capture depth must be fixed
   (`list(self.stack)` aliases the frame register dicts) before any continuation is resumed more than
   once. Small, and — unlike the §3 defect — currently latent, since nothing resumes twice today.
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
until entailment, which is demand-gating with a formal semantics; it is also the closest prior art for
the WATCHERS of §4d, which is why that section needs no new theory. **Delimited continuations /
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
  arc, not finishing a worse one. This document is deliberately design-only, and the TRIPWIRE in the
  status header is the guard.
- **The scheduler is the real cost** (§7), and it is easy to under-estimate because the queues look
  like the work.
- **Provenance.** A promoted fact must record the queue/scope that derived it, or `why` renders
  `(given)` — an order-sensitivity the plan already notes for pre-derived facts.
- **The single merge boundary must stay single** (§4.3). If every queue can write anywhere,
  flip-identity returns, and it returned twice already.
- **Perf is not a motivation and should not be claimed as one.** Judge at session scale
  ([[ugm-scope-session-sized]]); the case here is composability, and if the design is defended on
  throughput it will be defended on the wrong axis. §0.1 states the positive version: the motivation is
  the EMERGENCE of the computation model. Parallelism is not a goal, and §0.2 declines it explicitly —
  if a future argument for this work leans on concurrency, that is drift, not progress.
- **Watchers as unbounded arrival** (§4d). Standing trigger rules are the one feature discussed here that
  can re-open §5's global-queue unsoundness from the inside: if a watcher may enqueue at any time, no
  absence is final. The mitigations — confine watchers to a queue with a defined drain, fire only on a
  positive delta — are cheap to state and easy to lose during implementation, which is why they are a
  risk and not just a note.
- **Stale NAF across queues** (§5b). The live inherited view makes a drained child's absence-decides
  revocable by a later ancestor write; the sequential parent-first rule is what forbids it. If the
  scheduler ever gains the freedom to interleave a lineage, this unsoundness returns SILENTLY — the same
  failure mode §5 warns about, and the reason §5b is a correction rather than an addition.
- **Monotonicity becomes the termination argument** (§13.2). Under the cell model, `reactive.py`'s
  monotonicity claim stops being a pleasant property of the reactive gate and becomes the thing NAF
  stands on: spike cases 4a and 4b are the SAME topology and differ only in whether the write is
  idempotent — one drains in two rounds, the other never drains. Any write path that mints fresh on
  re-derivation (a skolem, a provenance record, an un-deduped `EMIT`) re-opens unbounded arrival from
  inside the network. This is a risk about a layer BELOW the scheduler, which is why it is easy to miss
  while reviewing the scheduler.

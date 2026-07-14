# The Rule ISA — reference semantics (the cheap experiment, built)

> **Status: BUILT as a reference interpreter (2026-07-05; opcode set and conformance suite grown
> since — 17 data-path opcodes: the matching core + `ITERATE`/`VMATCH` and the `MINT`/`EMIT`/
> `DROP_CTRL`/`INTERPOSE`/`RESTORE`/`RETIRE` effects, plus the control path below).** This is the small-step
> operational semantics of the label-less attribute ISA, with a runnable reference machine
> (`ugm/`) and a hand-written conformance suite (`tests/test_isa_machine.py`,
> no rules involved). It realizes "the cheap experiment" of
> `rule-isa-design.md`: write the opcodes as a spec + reference interpreter *before* any
> rule→opcode compiler, and see whether the set enumerates cleanly. Read `rule-isa-design.md`
> (the design + the label-less-substrate revision) and `memory/decision_labelless_substrate`
> first; this is the operational companion to them.
>
> **The machine now has BOTH an ISA plane and a CONTROL plane (control path BUILT 2026-07-14,
> `docs/isa_control_machine.md`).** The opcodes below are the **data path** — a single straight-line
> *basic block* (match-then-apply, run once). The **control path** (`ControlMachine`: a program counter
> over labeled basic blocks + `BRANCH`/`BRANCH_IF`/`CALL`/`RET`/`SUSPEND` + a control stack + `PRIM`
> interpreter steps) is the added half that makes loops, subgoals, fixpoints, and tool waits **compose as
> instructions** instead of Python drivers. See "The control path" below; the two planes together are the
> whole ISA (parallel to a real CPU's data lane + PC/JMP/CALL/RET).

---

## What is built

- **`ugm/attrgraph.py`** — the label-less attribute substrate. Nodes have an
  opaque identity and a bundle of attributes over a *closed key* vocabulary; edges are
  directed and unlabeled. Attributes are `GRADED` (degree in [0,1]) or `VALUED` (data under a
  key, open domain). The one index is `key → {nid}` — **never** by value, which is the
  structural guard that keeps a valued attribute from resurrecting a node label.
- **`ugm/machine.py`** — the reference interpreter: the opcode dataclasses and a
  naive, correctness-first `Machine`.
- **`tests/test_isa_machine.py`** — the conformance suite: hand-written instruction
  sequences exercising the substrate and every opcode, with no rules and no compiler.

This started ISOLATED from the as-built engine (`rewriter.py` over the name-based
`world_model.Graph`) and imported none of it. The bridge — lowering a `Rule` to a program and
differential-testing the two machines — is no longer deferred: see "The lowering + differential
test" below (`ugm/lowering.py`, BUILT) and the goal-directed sections that follow it.

---

## Machine state

A program runs over a **stream of states**. A state is:

```
State = (regs : Register → Identity,      -- a WAM-style register file
         score : [0,1])                    -- accumulated graded degree (t-norm product)
```

`score` starts at 1 and is composed by a t-norm (Gödel `min` by default; Goguen product is
selectable) as graded opcodes fire — this is how a fuzzy match's confidence flows down a
join chain. A **matching** opcode is a nondeterministic transition `State → P(State)` (it may
fork over candidates, prune, or scale). An **effect** opcode is a graph mutation applied once
per surviving state.

The judgement is written `⟨g, st⟩ —ins→ st'` for a match step (multi-valued in `st'`) and
`⟨g, st⟩ —ins⇒ ⟨g', st'⟩` for an effect step (single-valued, mutates `g`).

---

## Two phases: match-then-apply

A **well-formed** program is all matching opcodes followed by all effect opcodes. A matching
opcode after an effect opcode is a `ProgramError`. This is both the "keep the compiler dumb"
discipline of the design and the as-built engine's own collect-pending-then-fire order.

1. **Match phase.** Fold the state stream through the matching opcodes. No graph mutation, so
   no effect can perturb what matches (the semi-naive-safe order).
2. **Apply phase.** For each surviving state, in state order, run the effect opcodes,
   mutating the graph. Effects in one state share that state's registers — so a `MINT`'s
   fresh node is visible to a following `EMIT` in the same firing. Returned states carry the
   post-apply bindings.

---

## Opcodes — the transition relation

Notation: `g` the graph, `st = (r, s)` a state, `r[x]` a register, `deg(n,k)` the graded
degree of key `k` on node `n` (0 if absent/non-graded), `val(n,k)` its valued value,
`⊗` the machine t-norm.

### Matching core (purely positive)

```
SEED reg key [cmp value]
    for n in nodes_with_key(g, key):                 -- enumerate BY KEY only
        if cmp = ⊥ or (VALUED(n,key) and val(n,key) cmp value):
            yield (r[reg ↦ n], s)

FUZZY reg key threshold                                -- graded SEED (soft unification)
    for n in nodes_with_key(g, key):
        d = deg(n,key)
        if d ≥ threshold and d > 0:  yield (r[reg ↦ n], s ⊗ d)

FOLLOW dst src [direction]                             -- pointer-register edge cursor
    for n in (succ|pred)(g, r[src]):  yield (r[dst ↦ n], s)

TEST reg key [cmp value]                               -- crisp filter, no score change
    if has_key(g, r[reg], key) and (cmp = ⊥ or (VALUED and val cmp value)):  yield (r, s)

JOIN dst src [direction key cmp value]                 -- sugar: FOLLOW then TEST on dst
GRADE reg key (threshold | cmp value)                  -- filter a BOUND reg (dual role):
    graded:  if deg(n,key) ≥ threshold > 0:  yield (r, s ⊗ deg(n,key))
    valued:  if VALUED and val(n,key) cmp value:  yield (r, s)

SET reg nid          yield (r[reg ↦ nid], s)           -- bind a known ground identity
DUP dst src          yield (r[dst ↦ r[src]], s)        -- copy a register

SAME a b             if r[a] = r[b]:  yield (r, s)      -- register unification / join consistency
```

There is **no `CHECK-ABSENT` / NAC** opcode. Negation is materialized as a positive
attribute (`is_not`-style) and matched with `TEST`/`SEED` — the decide / de-pythonization
line. The whole matching core is positive and monotone.

### Effects (monotone facts + gated control)

```
MINT out attrs edges [control]                         -- Skolem / reification / chunk head
    n = fresh_node(g, control)
    for (k,a) in attrs:  set_attr(g, n, k, a)
    for tgt in edges:    add_edge(g, n, r[tgt])         -- bare edge back to a RETAINED node
    ⇒ (g', r[out ↦ n], s)

EMIT reg key value [kind]                               -- monotone fact write
    graded:  raise deg(g, r[reg], key) to max(old, value ⊗ s)   -- a degree only goes UP
    valued:  set_attr(g, r[reg], key, VALUED value)

DROP_CTRL src dst                                       -- delete a CONTROL edge, gated
    if edge_is_fact(g, r[src], r[dst]):  raise ControlEdgeError   -- refuse a fact edge
    else remove_edge(g, r[src], r[dst])
```

`MINT` and `EMIT` are additive/monotone: they add a node, raise a degree, or assert a value —
they never lower a degree or delete. `DROP_CTRL` is the sole deleting opcode and it *refuses*
a fact edge (an edge is control iff either endpoint is a control-layer node). Therefore
**"delete a fact edge" is not expressible** — the vision.md §5 invariant is a property of the
opcode set, not a lint pass (design payoff #1, `test_drop_ctrl_refuses_a_fact_edge`).

### INTERPOSE / RESTORE — reversible retraction (BUILT — `tests/test_isa_interpose.py`)

> **Ratified 2026-07-07 (user); implemented as the ISA-native replacement for `retraction.py`'s old
> forward-`rewriter` `rewire cut` (which `lowering.py` refuses as `Unlowerable`).** Originally
> designed here as a reserved, not-yet-built pair; both opcodes are now live in `ugm/machine.py`
> and match the semantics below exactly (`out` optionally binds the minted marker for `INTERPOSE`).

Truth-maintenance (retract a fact + cascade-hide its consequents) needs to *hide* a fact reversibly.
The old `retraction.INTERPOSE_RULE` did it with a `rewire cut` — a fact-edge deletion the opcode set
above **cannot** express, which is why retraction used to be stranded in the forward `rewriter`. The
ISA-native form is a dedicated **reversible** opcode, not a `DROP_CTRL` relaxation and not a
matcher-side "skip if marked" (which would leak retraction-awareness into the pure positive reader):

```
INTERPOSE rel obj marker            -- hide fact  s -[rel]-> obj  by splicing a control `marker`
    assert edge_is_fact(g, r[rel], r[obj])          -- only a live fact edge
    m = fresh_node(g, control=True)  ; set marker attrs on m   -- <retracted> tombstone
    remove_edge(g, r[rel], r[obj])                  -- redirect rel's object edge ...
    add_edge(g, r[rel], m) ; add_edge(g, m, r[obj]) -- ... through the marker (obj preserved)
    ⇒ path is now  s -[rel]-> <marker> -> obj

RESTORE rel obj marker              -- the inverse: un-hide (a `<reconsider>` rule emits this)
    remove_edge(g, r[rel], r[marker]) ; remove_edge(g, r[marker], r[obj])
    add_edge(g, r[rel], r[obj])                     -- reconstruct the original fact edge exactly
```

Why this keeps §5 **structural** while admitting a fact-edge mutation:
- **Obliviousness is structural, needs no reader change.** After `INTERPOSE`, `out(rel) = {marker}`,
  so `_relation_exists(s, rel, obj)` is false *naturally*; the only enumeration edge case (`rel → marker`)
  is dropped by the **existing** inert/control-node skip, because `marker` is a control node. The matcher
  stays a dumb positive reader that never learns what retraction *is* — the "content-blind engine" thesis.
- **The invariant reframes, not weakens.** From *"no opcode mutates a fact edge"* to *"the sole
  fact-edge op is a reversible interposition that preserves its pre-image — no **irreversible** fact
  loss."* `DROP_CTRL` still refuses fact edges; `INTERPOSE` is the one sanctioned fact op. The guarantee
  survives even under **misuse** (interpose and never restore → the fact is *hidden*, always
  reconstructible from the marker's position — never *lost*). Enforced by two checkable structural facts:
  (a) the opcode set is closed and `INTERPOSE` is the only fact op; (b) `INTERPOSE ∘ RESTORE = identity`
  (a unit test on the opcode).
- **Retraction becomes ISA-native.** `lowering.py` drops its `rewire` `Unlowerable`; `retraction.py`'s
  rules lower onto `INTERPOSE` (the `CASCADE_RULE` is already positive+NAC), so TMS joins the ISA and
  stops being a reason to keep the forward `rewriter`. `<retracted>` as ordinary KB vocabulary makes
  belief revision pure banks: a `<reconsider>` rule emits `RESTORE` on new evidence — no special machinery.

Wiring note: the **production** reasoning path is `GoalSolver` (demand-driven, today never retracts), so
this opcode makes retraction *representable + structurally safe in the reference machine*; putting it LIVE
on the backward path is a separate step (a demand-time "is this fact interposed?" that again reuses the
control-node skip) — decide then whether retraction runs on the backward path or only the forward TMS rules.

---

## The control path — control flow as instructions (BUILT 2026-07-14)

> Companion design + slice log: `docs/isa_control_machine.md`. The opcodes above are the machine's **data
> path** — one straight-line *basic block* (match-then-apply, run once, **no program counter**). They have
> no control transfer: every loop / branch / subgoal / fixpoint / tool-wait was faked in a Python driver
> (`run_bank`, `chain_sip`, `service_calls`) or hidden inside an opcode (`ITERATE`'s Python `for`). The
> **control path** adds the missing half — a PC over an addressable program of basic blocks, plus the
> control-transfer instructions — so those forms **compose as instructions**, not procedures. Parallel to
> a real CPU: the data-path opcodes are the ALU/load-store lane; the control path is PC/JMP/CALL/RET.

### The program and the machine

A **program** is an ordered list of labeled **basic blocks** (`ugm/machine.py`'s `ControlMachine` over
`Block`s). A block runs three phases:

- **work** — EITHER the data-path `body` (the match-then-apply opcodes above, run by the base `Machine`)
  OR a single `PRIM` — an *upper-level interpreter step*: a Python callable `fn(g, σ, ctrl) → (σ', flag)`
  the control machine SEQUENCES but does not decode. `PRIM` is the escape hatch that lets the control
  machine RUN the demand solver / fixpoint driver (the "two levels of program", §10 of the design) while
  control stays ISA; its `flag` can land in a control register for a following `BRANCH_IF`.
- **control** — scalar control-register ops (`SETI r,n` / `DEC r`) on the machine's **control registers**
  (loop counters — a home distinct from the per-state `regs` AND from graph nodes: "how the machine
  stepped", not a fact).
- **terminator** — sets the next PC (and, for `CALL`/`RET`, moves the control stack).

The machine carries a **PC** (indexing blocks), a scalar **control-register file** (`ctrl`), and a
**control stack** (`stk`, frames of ⟨return-PC, saved register window⟩). Between blocks it threads the
data-path **state stream** `σ` (`list[State]`). Fetch-decode-execute over the PC.

### The control-transfer instructions (block terminators)

Notation: `pc` the program counter, `label(L)` the block index of label `L`, `ctrl[r]` a control register,
`stk` the control stack, `σ` the state stream, `ε` a single empty state.

```
FALL                 pc ← pc + 1                                          -- fall through (default)
BRANCH L             pc ← label(L)                                        -- unconditional jump (JMP)
BRANCH_IF r cmp v L  pc ← label(L) if ctrl[r] cmp v else pc + 1           -- conditional (JZ/JNZ)
CALL L               push ⟨pc+1, σ, ctrl⟩ on stk ; σ ← [ε] ; pc ← label(L)   -- subroutine (fresh window)
RET                  ⟨pc',σ',ctrl'⟩ ← pop stk ; σ ← σ' ; ctrl ← ctrl' ; pc ← pc'   -- return
SUSPEND [r]          return Continuation⟨program, pc+1, stk, ctrl, σ, ctrl[r]⟩     -- yield to the host
HALT                 stop ; return σ

SETI r n             ctrl[r] ← n            -- (control phase) initialize a loop counter
DEC  r               ctrl[r] ← ctrl[r] - 1  -- (control phase) step a loop counter
```

- **`CALL`/`RET`** push/pop the caller's **register window** (state stream + control snapshot); the callee
  starts with a fresh window over the **shared** graph, so a subgoal's graph writes persist and the caller
  reads them after `RET`. Subgoals nest to arbitrary depth on `stk` — the WAM environment stack, in the
  machine rather than Python.
- **`SUSPEND`** captures the WHOLE control state as a resumable **`Continuation`** (program, resume-PC,
  stack, registers, stream, request) handed back to the driver; `ControlMachine.resume(g, cont, response)`
  continues it. This is the continuation a mid-computation subgoal or an external tool/`ask_user` wait
  needs.
- There is **no backtracking** and no reverse execution: the reasoning is monotone, tabled, set-at-a-time,
  so the control plane is **forward-only** (design §10). "Backward"/demand reasoning is a *program* on this
  forward plane (a tabled solver that `CALL`s subgoals), not a second plane.

### Loops, subgoals, fixpoints, waits — all instructions now (the driver ports)

| Form | As control instructions | Ported driver |
|---|---|---|
| **loop** | `SETI i,N; L: <body>; DEC i; BRANCH_IF i>0,L` | `ITERATE` re-expressed as primitives (differential-tested to reproduce its effects); `ITERATE` STAYS as the bulk/REP convenience |
| **subgoal** | `CALL` (arbitrary depth via `stk`) | `chain_sip`'s NAC negative subgoal — the demand solver's only recursion — de-recursed onto the control stack (generator-based: the yield IS the `CALL`, the driver stack IS the control stack). Proven by a 601-deep NAF stratification that runs under a Python recursion limit of 200 |
| **fixpoint** | a `PRIM` round + `BRANCH_IF`-back over a "changed?" flag | `run_bank`'s `for _ in range(max_rounds)` loop IS this program now; `run_bank` assembles + runs it |
| **tool wait** | sync = inline `PRIM`; async = `SUSPEND`+`RESUME` | the `<call>` dispatcher is a control-machine program; an `AsyncTool` SUSPENDs to the host and RESUMEs with the answer (the streaming boundary). The `<call>` RECORD stays a graph node; only the return/resume mechanics became instructions |

Each port is **behaviour-identical** to the driver it replaces (the reasoning / recognition / planning
suites are the differential oracle). Every Python control driver named in `docs/isa_control_machine.md` §1
now runs as control-machine instructions; the **seam** — "a loop can't contain a subgoal" — is closed.

### Performance posture (unchanged)

The instruction set is the stable CONTRACT; the interpreter is SWAPPABLE (the reference-vs-optimized
split, below). The finer instruction stream is naive-Python-slower, but it is exactly what a compiled
(Rust) `match`-dispatch eats cheaply — Rust buys the CONSTANT. The algorithmic CURVE (session-accretion
NAF) is held by seed-from-focus, not the interpreter. Correctness-first: the reference stays naive +
differential-tested.

---

## What the experiment showed (the honest outcome)

The design set the go/no-go: *clean enumeration → you have the ISA; the still-open features
(existentials, aggregation) keep demanding new opcodes → the semantics isn't ready to freeze.*
Building the reference interpreter, the split is:

- **Enumerates cleanly — freeze-ready:**
  - The **positive matching core** (`SEED`/`FOLLOW`/`TEST`/`JOIN`) is small and closed. It is
    a reification of what `rewriter._match` already does (seed-from-ground + pairwise joins),
    which is why it ported with no surprises.
  - The **two-layer monotonicity invariant** falls out exactly as predicted: with `EMIT`/`MINT`
    monotone and `DROP_CTRL` fact-refusing, illegal fact deletion is unrepresentable. This is
    the strongest result and the clearest win.
  - **Existentials** are just `MINT` (a fresh identity is a Skolem witness) — the fact-side
    existentials gap folds into an opcode already needed for reification and chunking. No new
    primitive. This is a genuinely encouraging sign against the "premature" worry.
  - **The label-less shift simplifies, not complicates:** killing the label/attribute seam
    made matching uniformly attribute comparison, and the value-guard is a one-line index
    discipline (index by key, never by value).

- **Mixed / needs a decision:**
  - `GRADE` carries a **dual role** (graded α-cut *and* valued comparison). It works, but it is
    the one opcode doing two jobs; a cleaner cut may split it (`GRADE` graded-only, valued
    comparison folded into `TEST`). Left dual here to match the design table 1:1.
  - `FUZZY` vs graded-`GRADE` differ only in that `FUZZY` *seeds* (introduces candidates) while
    `GRADE` *filters* a bound register. In the reference they compose identically; the
    distinction is real only once `FUZZY` seeds via an ANN/embedding index (the open Tier-4
    case), which this reference does not build.

- **Does NOT fit yet — the real signal:**
  - **Aggregation** (`count`/`sum`/`compare` over a completed set) has **no opcode** and does
    not want one shaped like the others: every opcode here is a per-state transition, whereas
    aggregation folds ACROSS the whole state stream (a barrier). That is exactly the "keeps
    demanding a new primitive" outcome the design flagged as the sign the waist is still
    moving. It is consistent with the coverage audit calling arithmetic an absent-premise
    class, and with the standing plan to service aggregation as a materialized `<call>` tool
    over a completed set rather than a matching opcode.

**Verdict.** The positive core + monotone/control effects + MINT enumerate cleanly and the §5
invariant is now a property of the instruction set — the freeze-ready part is real and worth
having as a spec. Aggregation (and, relatedly, disjunction) do not fit the per-state opcode
shape and should stay `<call>` calculators, not opcodes. So: freeze the positive-core +
effects ISA; keep aggregation/disjunction outside it. This matches the design's prior and is
the concrete thing the cheap experiment was meant to decide.

---

## The lowering + differential test (BUILT, positive fragment)

`ugm/lowering.py` + `tests/test_isa_lowering.py` (5 tests) close the first "next
slice": a **dumb `Rule` → program lowering**, a name-`Graph` ⇄ `AttrGraph` **bridge**, and a
**fixpoint driver**, differential-tested against `rewriter.run`.

- **Bridge** (`to_attrgraph`): a former node NAME is just the valued attribute `name="…"`, so
  a name-`Graph` maps 1:1 — every node carries `name`, every bare edge is copied, and a
  relation `subject → [rel] → object` stays a bare 2-hop path matched by FOLLOW (the
  name-preserving bridge, not role reification).
- **Lowering** (`lower_rule`): a `Pat(s, p, o)` lowers around its rel node as the pivot —
  SEED the rel by name (literal predicate) or reach it by FOLLOW from a bound/literal-anchored
  endpoint; then reach the subject as the rel's predecessor and the object as its successor,
  binding a fresh var, `SAME`-checking an already-bound one, or `TEST`-ing a literal. RHS Pats
  lower to `MINT` of a reified relation. It is the same seed-from-ground discipline as
  `_triples`, made explicit. Anything outside the fragment (graded, NAC, drop/rewire,
  propagate, fresh-RHS-nodes, RHS-var-predicate) raises `Unlowerable` — explicit, never a
  silent mis-lowering.
- **Fixpoint driver** (`run_to_fixpoint`): applies the program until no NEW firing is possible,
  keying each firing by its binding over the rule's keys and skipping an already-fired key —
  the analog of `rewriter`'s `fired` set, which is what makes a **recursive (transitive)** rule
  terminate.

Two machine ops were added to support joins/reification: `SAME` (register unification — the
join-consistency check when a Pat endpoint is already bound) and `MINT.in_edges` (a reified
relation needs an incoming edge to the rel node).

**Graded α-cut lowering** (`lower_graded`): a non-inverted `GradedCondition` on `?c` with dims
`{d…}` and threshold `t` lowers to one `GRADE(?c, d, threshold=t)` per dim. Under the min
t-norm each dim must clear `t` and the surviving `score` is the min over dims — which is exactly
`rewriter.graded_degree` (min over dims, α-cut, min across conditions). The bridge carries each
embedding dim across as a graded attribute, so `GRADE` reads it. Differential-tested: the
machine's per-state score equals the engine's `graded_degree` for the passing bindings, and the
α-cut gates the same derivations. Inverted ("not at all") conditions raise `Unlowerable` (a
later slice).

**Result.** On the positive/monotone fragment the machine reproduces the engine exactly: a
2-clause conjunction with a literal object, **transitive closure** (recursion via the fixpoint
driver), a **4-clause join whose last clause has both endpoints bound** (exercising `SAME`), a
**graded α-cut rule** (score = `graded_degree`), plus the near-miss (both derive nothing). This
is the swap-safety correspondence the design asked for, on the fragment lowered.

---

## Goal-directed evaluation — acting toward a goal, not rushing to fixpoint

> **The driver direction (§6a "Everything is goal-directed").** `run_to_fixpoint` above is the
> forward-rush — it derives the whole closure whether or not a query needs it, and it exists
> here as the differential-test harness and the contrast. The *direction* the substrate commits
> to (`decision_labelless_substrate`, `vision.md` §6a) is **demand-forward**: a goal is a partial
> attribute-node / partial relation — the same shape as a fact — and answering it materializes
> ONLY what the goal demands. `ugm/goal.py` (`GoalSolver`, `tests/test_isa_goal.py`)
> is the first slice of that driver.

`GoalSolver` is a demand-driven, **tabled** evaluator over the same positive opcode core (no
trail, no NAF — the crisp-core prize the SLD+trail+NAF alternative would forfeit):

- **Rule-head index** — `head_index[rel] → [(rule, head_pat)]` picks only the rules whose head
  could produce the goal.
- **Sideways information passing (SIP)** — the goal's bound args seed the head's variables, and
  each body clause is solved left-to-right so its answers bind the next clause's variables. This
  is what keeps a transitive goal `isa(x, w)` walking only x's chain instead of demanding
  `isa(?, ?)` (which would flood).
- **Tabling** — a global least-fixpoint over the *demanded goals only* (the magic set); answer
  sets and the demanded-goal set grow monotonically over a finite Herbrand base, so a recursive
  rule (transitivity) terminates.

**The contrast, measured** (`test_isa_goal.py`). Over two disjoint `isa` chains
`x→y→z→w` and `a→b→c→d`, `run_to_fixpoint` derives the full closure of *both*; `solve(isa, x, w)`
answers `x→w` and materializes only `{x→z, x→w, y→w}` — a **strict subset**, with **no** fact
from the a-chain ever demanded. That measured difference *is* the shift from forward-rush to
goal-direction.

Scope of the tabled solver: positive relational rules with literal predicates, evaluated over
the bridged graph at the concept/name level (a KB with distinct entity names). Value-level
identity is a later slice; the goal-direction MECHANISM (head-index + SIP + tabling) is what it
pins. Negation is handled by demand-driven completion (below).

**The graded gate on the goal path** (`tests/test_isa_goal_graded.py`). A demanded goal answered
via a rule with a graded condition is **gated by the α-cut**: `GoalSolver._graded_degree` computes,
per condition, the min over its dims of the bound node's graded attribute, α-cuts at the threshold,
and takes the min across conditions — this *is* `rewriter.graded_degree`, now on the demand path.
An answer whose graded condition fails the cut is not produced (an entity below threshold does not
satisfy the goal), and a surviving answer records its degree in `solver.degree[(rel, s, o)]`
(possibilistic — the most-confident derivation). Pinned: a ground goal above the cut passes and
records its degree; below the cut it is gated out with nothing materialized; a free-variable goal
returns only the entities that clear the cut; and the recorded degree equals the engine's
`graded_degree`. This is where goal-direction meets the graded layer — the same filter
`lower_graded` applies forward, applied to what a goal demands.

### Walkers — the long-range demand primitive

The tabled solver expands a demanded goal to a least-fixpoint; for a **long-range reachability**
goal ("is `w` reachable from `x` along `isa`?") that expands the whole reachable chain. A
**walker** (`ugm/walker.py`, `tests/test_isa_walker.py`, `decision_walkers_locality`,
vision §6a/§11) is the bounded alternative: a demand token that carries the goal across the graph
hop by hop, spending **fuel**, and stops on arrival or when it runs dry. Fuel is the content-blind
effort budget (§14) — *"think harder" is literally more fuel*, never a cleverer search. A BFS
frontier keeps it goal-directed (confined to what the source reaches) and a `visited` set
guarantees termination through cycles. On arrival it **materializes a shortcut** — the derived
transitive relation, marked `shortcut: 1` as its provenance — so the next query is O(1)
("discoveries materialize as provenance shortcuts").

Pinned (`test_isa_walker.py`): reaching `w` from `x` needs 3 traversals, so fuel 2 fails and fuel
3 succeeds (the think-harder relation); a walk from the disjoint chain never touches `x`'s facts;
an unreachable target in a cycle terminates instead of hanging; and after a well-fuelled
discovery, a small-fuel repeat query succeeds on the direct shortcut. (In a full in-graph
realization the walker is a CONTROL token with a `fuel` attribute serviced by rules — the main
engine's `ugm/walker.py`; this reference driver models that semantics, matching `goal.py`'s
Python-driver style, and stays positive/monotone — it only ever ADDS a shortcut.)

**Wired into `GoalSolver`** (`tests/test_isa_goal_walker.py`). `GoalSolver(…, walk_fuel=N)` now
carries a **ground reachability goal on a transitive-closure relation** with a fuel-bounded walker
instead of tabling the whole chain — the walker-as-demand integration. `_transitive_closure_rels`
detects the exact shape `R(?a,?c) :- R(?a,?b), R(?b,?c)`; for such an `R`, walking its base edges
*is* the transitive reachability, so the walker returns the same yes/no as tabling while
materializing only the one shortcut. Measured: `solve(isa, x, w)` under `walk_fuel` derives exactly
`{x→w}` where pure tabling derives `{x→z, x→w, y→w}` — a strict subset (bounded work); fuel bounds
the reach (fuel 2 empty, fuel 3 answers); free-variable goals (`isa(x, ?)`) still fall to tabling;
an unreachable ground goal returns empty with nothing materialized. This is the first slice of
goal-direction with bounded long-range demand as one driver; deeper integration (spawning a walker
for a transitive subgoal that arises *inside* a larger tabled query, and linear recursion over a
different base relation) is the follow-up.

### NAC → materialized-positive completion — the last reasoning piece

`tests/test_isa_goal_nac.py`. Negation on the goal path is the `decide` line
(`memory/decision_forcing_a_decision`, `ugm/decide.py`), **not** a `CHECK-ABSENT` filter —
the matching core stays purely positive. A rule's copula NAC `H :- BODY, not ?c is P` is rewritten
(`_lower_nac`) into a **positive body clause** `?c is_not P`, appended after the positive LHS so the
residual has already ground the subject by the time the `is_not` subgoal is demanded. The negative
is produced by a single demand-driven **completion** step (`_complete_negative`): to answer a
demanded `is_not(c, P)`, solve the positive `is(c, P)` to **completion** in a self-contained nested
`GoalSolver`, and materialize `c is_not P` (matched positively everywhere else) iff the positive has
no answer; if the positive *is* derivable it **defeats** the default (the completion yields nothing),
so the consumer rule does not fire — the defeasibility falls out directly, with no separate TMS pass
on the goal path.

Soundness is stratification: the nested solve computes the positive's **complete** extension
independently of the outer fixpoint round, so reading "the positive failed" cannot hit the classic
NAF-in-a-fixpoint bug (empty merely because a producer had not run yet). A negative cycle
(`is(x,p) :- q(x), not is(x,p)`) is caught by the `_completing` up-stack guard and raised as
`NonStratifiable` — never silently mis-answered; only copula `is` NACs lower this slice, and a
relational or variable-object NAC is rejected the same way. `_materialize` was hardened to
mint-and-register a missing endpoint, since a completion object like `urgent` may live only as a rule
literal (never a base node) yet the reified `c is_not urgent` must still anchor to a `urgent` node.

Pinned: the routing of contract scenario 1 reproduced goal-directed (alice → express not regular;
bob → regular not express, via graded urgency); the negative is minted and matched positively and
stays demand-scoped; a free-object consumer enumerates only the undefeated defaults; and
relational / negative-cycle NACs are rejected. **With this, the goal path covers the full
defeasible + graded contract scenario end to end.**

### Predicate-NAC generalization — the copula scheme, for an arbitrary relation (DONE 2026-07-06)

`tests/test_isa_goal_predicate_nac.py`. The copula NAC above (`not ?c is P` → `is_not`) generalizes
with no new mechanism to an ARBITRARY relation marker: `_lower_nac` rewrites `not ?s R o` into a
positive body clause `?s R_not o` (the copula being just `R = is`), records `_neg_of[R_not] = R`, and
`_complete_negative` answers a demanded `R_not(c, P)` by the same nested-complete-solve of `R(c, P)`.
This is the card trader's actual negation surface — `overridden`, `stance`, `excluded`, `reachable`,
`needs_price`, `ranked`, `dominated`, `best` — a literal predicate with a ground object and a
body-bound subject. In slice: literal predicate, ground object, body-bound-or-literal subject. Out of
slice, **rejected explicitly** (never silent): a variable-object NAC (`not ?o blocked_by ?anyp`, ¬∃o)
and a NAC subject the body never binds (`not ?x chosen <yes>`, ¬∃x — the grouped-existential idiom) —
these need the object/candidate universe and are the natural Phase-2 extension.

Differential-tested against the STRATIFIED forward driver (`authoring.run_rules`) on the REAL banks:
`corpus/preference.cnl` stance rules (where `neutral` is a DEFAULT defended by two ground NACs) and
the full `corpus/policy.cnl` override bank (`sell forbidden` UNLESS `overridden` by a higher-ranked
source). The goal-directed completion reproduces the stratified answer exactly, including the demo's
keystone (`today outranks standing` → `sell overridden` → the exclusion lifted). The oracle is
`run_rules` (stratified), NOT `rewriter.run`: the naive single-fixpoint driver evaluates a NAC against
a partial graph and derives the unsound `op stance neutral` alongside `op stance encouraged` — the
completion's nested-complete-solve is the goal-directed analog of stratifying the producer below the
consumer, which is what makes it sound. Full bank-by-opcode map:
`docs/graph low level machine/isa-card-trader-coverage.md` (the ISA arc's Phase-0 coverage map).

### Existential NACs (¬∃) + `DROP_CTRL` subsumed — the planner's block/unblock idiom (DONE 2026-07-06)

`tests/test_isa_goal_existential_nac.py` — the ISA arc's Phase 2. Phase 1 handled a GROUND NAC (a
single negative to materialize). The planner needs the EXISTENTIAL shapes, where the negative is "no
witness exists": a variable-OBJECT NAC (`not ?o blocked_by ?anyp`, ¬∃p) and a grouped free-SUBJECT
NAC (`not ?x add ?c and not ?x preferred`, ¬∃x). `_lower_nac` now PARTITIONS a rule's NACs — a clause
with a NAC-local free var (a binder the positive LHS does not bind) is EXISTENTIAL; a fully-bound
clause stays the ground `R_not` path. Existentials are grouped by shared free var (`_nac_groups_free`,
the forward engine's `not (A and B)` vs `not A and not B` partition) and applied per env as a
demand-driven EMPTINESS check (`_exist_nac_blocks`/`_group_satisfiable`): the head fires iff the group
has NO witness, the group joined and solved to COMPLETION in a nested solve (the soundness discipline
of `_complete_negative` — read the complete extension, not a partial round). (A subtlety the earlier
Phase-1 slice got wrong: `not ?a consume ?b` where `?b` is LHS-bound is NOT ¬∃ — it is a ground NAC;
only a NAC-LOCAL free var makes a clause existential.)

**`DROP_CTRL` is SUBSUMED, not needed** — the load-bearing result. The block/unblock idiom
(`?o blocked_by ?p when … not ?p reachable`; `drop ?o blocked_by ?p when … ?p reachable`;
`?o viable <yes> when … not ?o blocked_by ?anyp`) exists in the forward engine because forward
chaining asserts a `blocked_by` prematurely (before reachability is known) and then RETRACTS it via
`drop` (a control-layer deletion, the `DROP_CTRL` opcode) once the precondition becomes reachable. On
the demand path there is nothing to retract: `blocked_by(o, p)` is computed against COMPLETE
reachability (the ground-NAC completion of `not ?p reachable`), so a stale block is never asserted.
The `drop` rule (empty rhs) is simply INERT on the goal path — never indexed as a producer. This is
DIFFERENTIAL-TESTED against the ACTUAL planner driver — the repeat-`run_rules`-until-stable loop of
`planning.plan`, where `drop` IS load-bearing — over a 2-step precondition chain: the goal-directed
solver reproduces the loop's final `viable` = {opa, opb} and `reachable` = {water, coffee, done}
exactly, with `blocked_by` ending empty in BOTH and no drop firing on the goal path. (A single
stratified `run_rules` sweep UNDER-derives here — it stops at the first stratum's `water`/`opa`; the
mutual viable↔reachable recursion needs the iterated loop, which is why the oracle is the loop.)

**The one Phase-3 residual, isolated.** The `chosen` commit rule
(`?o chosen <yes> when … not ?x chosen <yes> and not ?x add ?c`) has an existential NAC on the rule's
OWN head — a non-stratified SELECTION/choice the forward engine resolves by commit-ORDER, not by
completion. `_lower_nac` REJECTS it (raises `NonStratifiable`, never silently mis-answers): a grouped
existential NAC whose predicate equals a head predicate is a selection, out of the monotone-completion
slice. Loading the WHOLE `corpus/planning.cnl` bank raises on exactly this one rule — every other rule
(positive, ground-NAC, ¬∃p) lowers — so the goal-directed planner (Phase 3) has a precise remaining
scope: operational choice for `chosen`, nothing else.

### The goal-directed planner — plan → act → replan, demand-forward (Phase 3 CORE, DONE 2026-07-07)

> **RETIRED 2026-07-11 (Phase 5.5 slice 4).** `ugm/solve.py` is DELETED. Its Python-hardcoded
> plan→act→check→replan control flow (hardcoded predicate NAMES in the branches — a standing-rule
> violation) is now a KB-DECLARED composition of ITERATE×CHECK over `<check>` verdicts, serviced by the
> EXISTING `<call>` loop (`run_bank(..., tools=mode_registry(rule_g))`); see `tests/test_isa_plan_act_check.py`
> and the CHANGELOG. The section below describes the retired driver — kept as the rationale trail for
> WHAT the declared composition reproduces (the plan-execution semantics), not as as-built code.

`ugm/solve.py` (`derive_plan` + `run_to_goal`; `tests/test_isa_solve.py`, 9 tests). The
forward `plan()`/`solve()` loop SATURATES; this drives the SAME `PLANNING_RULES`/`SOLVE_RULES` through
`GoalSolver` demand-forward — a goal PULLS only its AND-OR chain (MEASURED: goal-directed `reachable` is
a STRICT SUBSET of forward's; it never derives the goal fact it doesn't need). Everything but `chosen`
lowers to Phase-1/2 completion, so the driver owns only the selection:

- **`derive_plan`** demands `best` (transitively pulling need/candidate/viable/cost_settled/dominated
  along the chain), runs the `chosen` selection per need, commits `chosen`, demands `before`.
- **The `chosen` selection = the resolution CHAIN** (the ratified design): preferences (the
  `dominated`/`best` CNL) resolve a unique best DETERMINISTICALLY (the selection mostly SUBSUMED, like
  `DROP_CTRL`); a genuine tie → a KB-prescribed `tie_break` `<call>` (§8 seam); else a DETERMINISTIC-
  ARBITRARY pick (stable node order, NOT RNG — reproducible / provenance-safe). No operational policy
  hidden in the driver.
- **`run_to_goal`** folds act/observe + replan. Control (`chosen`/`done`/viable/ready/…) is DRIVER-held
  and injected into a fresh per-cycle `AttrGraph`; the persistent name-`Graph` carries ONLY monotone
  facts (operators + goal + observed `<now> true`). So the forward engine's whole control-TEARDOWN bank
  (`planning_teardown.cnl`, 15 gated drops) is SUBSUMED — a replan is a driver-state reset; nothing
  control-layer is ever persisted, so there is nothing to tear down (the `DROP_CTRL` subsumption, now
  for the entire replan machinery). Acting reuses `planning._perform_op`.
- **Differential-tested vs `planning.solve`**: happy → `done`, withheld-effect divergence → replan →
  `done`, dead goal → `stuck`. PLUS the two invariants a full-set-parity oracle is blind to:
  DIRECTION-PRESERVATION (strict-subset `reachable`) and TEARDOWN-SUBSUMED (persistent graph stays
  purely monotone through a replan).
- **Perf** (pure, no semantics): `AttrGraph.version` (monotonic mutation counter) + a version-keyed
  `derived_triples` memo — the goal solver snapshots per subgoal across many nested solvers (~38k
  full-graph scans for one small plan → the dominant cost); the cache cut a plan ~12.7s → sub-second.

Phase 3 REMAINDER (DONE 2026-07-07): (1) the rank `<call>` tool serviced GOAL-DIRECTED — `GoalSolver`
gained a `tools` registry (a tool-backed relation → a calculator run ONCE on first demand); `cheaper_than`
is backed by `rank_cheaper_than`, so a `dominated` subgoal demands the ordering, the tool mints it, and a
COST preference breaks a tie by cost (`examples/coffee.py` reproduces `plan()` exactly). (2) the
card-trader stress case — `run_to_goal` drives `cards_frontier_kb.cnl` + value→plan bridge + full
`POLICY_RULES`; the bridge's DERIVED operator effect is observed via demand-forward add-resolution
(`_observe_simulated`), object-scoped exclusion + override work on the demand path
(`tests/test_isa_solve_cards.py`). The ISA arc is now SEMANTICALLY COMPLETE on the planner.

### The honest gate — seed from the ground endpoint (parity slice 1, DONE 2026-07-07)

`tests/test_isa_goal_seed.py` — the first of the three named parity wins. The reference `GoalSolver`
proved SEMANTICS; a scaling probe on a transitive-closure chain measured the SPEED gap starkly (pure
tabling: n=40 → 4s, n=80 → **107s**, ~O(n⁴)). Profiling found the dominant cost was `derived_triples`
— an O(graph) rebuild of the whole triple set, called ~197k times for one n=40 solve because every
`_materialize` bumps `AttrGraph.version` and invalidates its cache mid-derivation.

The fix is the **seed-from-ground / rarest-anchor** discipline (the same `rewriter._match` uses): a
demanded subgoal almost always has its subject (or object) bound by SIP, so `_facts_matching` now
TRAVERSES LOCALLY from the bound node's edges (a relation `s -[rel]-> o` is a rel-node named `rel`, so
from a bound subject its facts are `succ(succ(s) named rel)`) — O(degree), not O(graph). Only a
fully-unbound goal (a genuine free-variable enumeration, which has no ground endpoint to seed from)
falls back to a scan. `_materialize`'s existence check went local for the same reason, plus a shared
`_materialized` memo (the monotone graph means a repeat write is an O(1) set hit, not an O(degree)
re-check). MEASURED: a bound-endpoint solve now makes **ZERO** `derived_triples` scans (pinned by test),
and n=80 tabling dropped **107s → ~15s** (~7×). Exactly answer-preserving — all differential tests
(`test_isa_solve*`, `test_isa_goal_predicate_nac`, …) stay green, so parity of ANSWERS is unchanged;
this is purely the SPEED gate.

### Semi-naïve delta (parity slice 2, DONE 2026-07-07)

`tests/test_isa_goal_semi_naive.py`. The naive fixpoint (`while changed`) re-joined every demanded
goal's whole body every round, rediscovering answers it already had — the O(rounds) redundancy that
kept the curve ~O(n^3.8). Now `solve` is **semi-naïve**: a goal's body is joined in FULL exactly once
(its first evaluation — the seed, `self._full_joined`), and thereafter only against the previous
round's **delta** (`self._delta_by_rel`, the facts newly added ANYWHERE last round). `_delta_join`
does the classic delta-substitution — for each body-clause position, that clause draws from the delta
(`_delta_matching`, relation-indexed then filtered by whatever endpoint SIP has bound) while the others
stay full — so a head fires the round after its LAST body fact appears, and work becomes
~proportional-to-derivations instead of rounds × closure.

The careful part the design flagged — answers flow BOTH through the join tables AND through the graph
side-channel (`_facts_matching` reads materialized facts across DIFFERENT table entries on the same
relation) — is handled by folding EVERY table growth into `next_new`, whether a join derived it or
`_facts_matching` picked up a cross-materialized graph fact. So the delta propagates through both
channels and no derivation is dropped (the arc's "correctness never traded" invariant). This is
answer-preserving by construction and PROVEN so: a randomized differential test sweeps >1000 goals
across 60-odd random interacting-rule programs (transitivity + linear recursion over a different base
relation + a two-relation join) and asserts each demand-driven answer equals the FORWARD CLOSURE
(`run_to_fixpoint`, the independent oracle) filtered to that goal; a structural pin asserts each goal
is full-joined at most once (`solver.full_joins <= #demanded goals`, so the round-churn is gone, no
flaky timing). MEASURED on the pathological chain (walker disabled, pure tabling): n=50 2.27s → 0.59s,
**n=80 15s → 2.9s** (~5× on top of slice 1, ~37× vs the original 107s); the exponent drops ~O(n^3.8) →
~O(n^2.9), one full power of n removed. All 415 differential + scenario tests stay green.

With both parity wins in, the reference `GoalSolver` is now much closer to production-viable; retiring
`rewriter.run` is the remaining call (see "Next slice").

## Next slice (deferred, not built)

0. **The HONEST GATE — production parity (slices 1 & 2 DONE).** The reference `GoalSolver` proves
   SEMANTICS, not SPEED; it cannot REPLACE `rewriter.run` until it reaches parity. Landed:
   df-indexed rarest-anchor SEED (slice 1, seed-from-ground); semi-naïve delta (slice 2, above);
   hub-flooding avoidance is largely subsumed by the local seed (only a fully-free `R(?,?)`
   enumeration scans). REMAINING to actually retire `run`: re-host provenance/tools/the driver onto
   `GoalSolver` and run the whole shipped suite through it, then delete the `rewriter.py` matcher /
   NAC branch / `graded_degree` / propagate handler. That is the substantial shrink the gate exists
   for — no longer blocked on the goal-solver's asymptotics, now a re-hosting + deletion pass. The
   standing alternative is to keep `GoalSolver` as the reference and `rewriter.run` as production.
1. **Deeper walker integration — DONE (2026-07-07).** Both shapes the slice named landed
   (`ugm/{walker,goal}.py`; `tests/test_isa_goal_walker_linear.py`, 8 tests):
   (a) **linear recursion over a DIFFERENT base** — `_closure_bases` maps a derived relation that
   is the transitive closure of a base (`anc(a,b):-parent(a,b)`, `anc(a,c):-parent(a,b),anc(b,c)`,
   left- OR right-recursive) to that base, and the walker gained `mint_rel` so it WALKS `parent`
   while materializing the shortcut AS `anc` (walk one relation, mint another); it stays walkable
   only when the derived relation's rules are EXACTLY {base, step} (any other contributor would be
   invisible to a base-edge walk, so it falls back to tabling). (b) **a walker for an INTERIOR
   reachability subgoal** — `_walk_applicable` now fires for a ground reachability subgoal arising
   inside a larger tabled query (the check moved into the fixpoint loop), so a body clause like
   `anc(?x,?y)` with both ends SIP-bound lands on a walker, not the tabled chain. Plus the
   soundness fix the generalization surfaced: a transitive-closure walker answers ≥1 hop, so
   reflexive `rel(a,a)` holds ONLY via a real cycle (the old 0-hop short-circuit was latently
   unsound). All differential-tested against tabling incl. a 300+-pair random sweep over cyclic
   `parent` graphs.
2. **The in-graph-nodes vs rebuildable-bytecode fork** for instructions — orthogonal to the
   semantics; decide only if/when execution is routed through the ISA for real.
3. **`FUZZY` over an embedding index** (ANN + α-cut) — the graded SEED/JOIN made real, the
   open Tier-4 hub-flooding case.

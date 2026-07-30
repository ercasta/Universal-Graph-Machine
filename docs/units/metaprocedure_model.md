# The metaprocedure model — goal-driven, materialized, centrally gated

**Status: design, 2026-07-30; corrected twice the same day.** Written as the foundation decision to build
forward on `ugm/`'s substrate (`arc_recap.md`'s current Act, `attic/handoff_ugm_reversion_evaluation.md`),
because answering "what should replace `run_bank`'s blind fixpoint driver" turned out to require stating
the whole computation model precisely, not just one mechanism. **Two corrections, both same-day: §1a (the
first draft over-corrected toward graph-resident orchestration) and §1b (the fix to §1a's own "move
mechanism to Python" suggestion — some mechanism must stay a declared, privileged rule, not Python, or
hypothetical reasoning cannot reach it).** Read `model.md` §11 first (homoiconicity is the actual source of
this project's advantage over the Soar/ACT-R/BDI lineage, not goal-orientation or tool dispatch — this
document is what §11 cashes out to, mechanically). Read `STATUS.md` for where this sits in the current work
queue.

**What this document is not:** a proposal to build something new from nothing. Every piece named in §2 below
already exists in `ugm/`, most of it pre-dating this session by a wide margin. What was missing was seeing
them as one model rather than several separate modules, and naming the two precise gaps (§3) that stand
between "this already does what's being asked for" and "this hasn't actually been checked to."

---

## 1. The shape, stated plainly — and the correction that sharpened it

The user's own framing, which this document exists to ground: *the system is goal-driven; the way it
computes is by materializing goals and launching metaprocedures that are themselves materialized in the
graph, "made of" metarules, that use the KB's ordinary rules to do their work; these metaprocedures are
interruptible — a standing "do not do anything dangerous" must be able to stop one mid-flight — which
argues for routing metaprocedure stepping through one central point rather than trusting each procedure to
remember its own safety check. It is explicitly **not** "throw the KB's rules onto the graph and hope
something emerges" — that ungated, everything-fires-if-it-matches shape is `run_bank`'s actual weakness,
not a feature to keep.*

### 1a. The correction — two layers, not one flattened stack

The first draft of this document read "metaprocedures materialized in the graph" as implying the
*orchestration logic itself* — the code that decides which rule to run next, when to check a proposal, how
to dispatch — should also become graph-resident, rule-shaped data. That is one indirection too many, and
the user caught it precisely: **the engine/firmware/ISA is legitimately, correctly a fixed virtual machine,
implemented in Python, that is *not* something a KB author changes.** Its control flow is not the thing
that needs to be graph-resident. What must be graph-resident — because it is what a KB author writes and
what the fixed VM manipulates — is the *content*: business rules, and now confirmed (§2i), rules
*about* rules. A metarule can legitimately be `Pat`-shaped data the same engine matches like anything else
(so it composes with everything else homoiconically — model.md §11's actual point), but the *scheduler*
that decides when to run a metarule, harvest its output, or service a proposal is correctly Python, exactly
the way a CPU's fetch-decode-execute loop is correctly not itself a program the CPU runs. Building a
graph-resident interpreter-of-interpreters would buy nothing and cost real complexity.

Four requirements, restated against this corrected split:

1. **Goals are data.** (Established already — see §2a.)
2. **A metaprocedure's *progress* is graph-resident data — ordinary facts a rule can read** (`chosen`,
   `ready`, `waits_for`, `done`, `discrepancy` — see §2a/§2d), not a Python variable. The VM's own *internal*
   bookkeeping for driving one servicing pass (a loop counter, a resume point) is correctly process-resident
   Python state — a CPU's own registers, not something a business rule inspects. §2e distinguishes these
   precisely; the first draft conflated them.
3. **A metaprocedure "uses" KB rules by dispatching to them** — proposing a unit of work as data, not
   executing domain logic itself.
4. **Every proposed unit of work passes through one shared, fixed VM checkpoint** before it is committed —
   Python code, correctly, consulting graph-resident data (§4) — so a standing constraint cannot be silently
   bypassed by a procedure that forgot to check it.

### 1b. A three-way rule classification, and the correction it forces on §1a

A second, sharper cut, and the reason §1a's own "move mechanism to Python" suggestion needed its own
correction:

1. **Business rules** — end-user authored, ordinary expressive power, write only ordinary content.
2. **"Useful" rules the engine ships** — structurally *identical* to (1), same power, same privilege
   (none): a shipped `urgent = 0.8` degree, the `transitive`/`propagates` schemas, `RULE_FORMS`/
   `FOCUS_FORMS`. A standard library, not mechanism. **Categories 1 and 2 are one privilege class, not
   two** — "who authored it" doesn't matter; "is it ordinary content-shaped" does.
3. **Metarules / metaprocedures** — the actual control-flow/mechanism logic.

This is `mechanism_policy_separation.md`'s own thesis (*"never conflate mechanism with policy"*),
generalized from retraction — where it was already built once — to the whole metaprocedure question.
That document's `RETIRE` opcode is exactly category 3: privileged, *"not in the rule→program lowering
vocabulary"* for ordinary rules, emitted only by the retraction driver.

**But category 3 is not uniformly "move it to Python," and treating it that way is a mistake worth naming
precisely, because it costs a real capability.** `chain_sip` and `suppose()` can only reason *through*
declared `Pat`/`Rule` structure — never through an opaque Python function call. `mechanism_policy_
separation.md`'s own discriminating test settles which side of this a given piece of mechanism falls on:
*does anything reason about it, including reasoning about the reasoning?*

- **Mechanism that derives reasoned-over state** (plan readiness, step ordering, discrepancy) — policy
  rules read it (RANK/REPLAN), `why` explains it, and — the case that forces this correction — a
  hypothesis ("what would you do if the door were locked — would this step still become ready?") needs
  `suppose()`'s in-scope `chain_sip` to walk *through* the derivation, not just query its current value.
  This **must stay a declared rule**, `Pat`-shaped like any business rule, so it is reachable exactly the
  way business content already is — but **privileged at the conclude/write side**: gated so only the
  engine's own mechanism bank may target its reserved predicates, the same shape `RETIRE`'s lowering-
  vocabulary exclusion already has, applied to rule-authoring rather than to an opcode.
- **Mechanism that is pure execution, nothing ever reasons about** (the dispatcher's find-next-call/
  run-handler/consume loop, `ControlMachine`'s PC/branch stepping) — correctly Python. A servicing loop
  explains nothing, exactly like a loop counter (`mechanism_policy_separation.md` §8's original register
  criterion) — moving *this* half to Python costs nothing, because nothing ever needed to reason about it.

**Privilege and scope are orthogonal axes, and keeping them distinct is what makes the hypothesis case
work at all.** Privilege answers *"which rule bank may conclude this predicate."* Scope (`suppose()`'s
already-working `scope=` parameter) answers *"does this firing land in pencil or ink."* The mechanism bank
is *allowed* to conclude `ready`; whether one firing of it happens for real or inside a hypothesis's pencil
scope is the separate, already-solved axis. So "what would you do if X" needs nothing new: `suppose()`
pencils the assumption, `chain_sip` reasons in-scope through the privileged-but-declared readiness rules
exactly as it already does for ordinary business rules, and a hypothetical `ready`/`discrepancy` verdict
comes out without ever touching real ink.

---

## 2. What already exists — mapped precisely, not assumed

### 2a. Procedures are already declared data, not Python

`ugm/cnl/procedure_surface.py`'s `to NAME : A then B then C` surface and `corpus/procedure.cnl`'s
stepping bank turn a named procedure into ordinary facts:

```
brew step get_water        brew step add_beans        brew step heat
get_water step_before add_beans        add_beans step_before heat
```

Running one (`run brew` → `<run> proc brew`) is handled by **three declared rules**, not a Python
interpreter: INVOKE marks each step `chosen` (the pre-made plan, bypassing the planner's own goal-spray —
*"the steps ARE the plan"*), ORDER lifts `step_before` into the planner's `before`, and GAP-FILL routes an
unmet precondition back into the synthesizing planner. `corpus/procedure.cnl`'s own header states the
composition precisely: *"Procedure = pre-made plan; planner = synthesized plan; ONE execution gate — they
compose."* A hand-authored plan and a synthesized one are not two engines; they are two ways of producing
the same `chosen` fact the one execution gate (§2b) reads.

### 2b. There is already ONE central, content-blind dispatcher

`ugm/dispatch.py`'s own docstring states the invariant this document's §4 requirement is asking for,
independently, a year before this conversation: *"a rule never calls a tool, a tool never rewrites; they
couple only through nodes."* A `<call>` is a materialized control node (`<call> --tool--> T`, `<call>
--SLOT--> A`) a rule mints — a **proposal**, not an action. `dispatch.service_calls`/`service_calls_cm` is
the one loop that finds pending calls, runs the registered handler, folds the result back as nodes, and
consumes the call. *"The driver stays dumb... WHICH tools fire, and WHEN, is decided by the rules that emit
the calls."* This is requirement 3 and half of requirement 4 already built: proposing is separate from
applying, and there is exactly one applier.

### 2c. Reasoning modes are calls too, not just external tools

`ugm/mode_calls.py` generalizes the same `<call>` boundary to the firmware's own reasoning modes —
CHECK, CHOOSE, SUPPOSE are invoked *the same way a tool is*: a rule materializes a `<call>` naming the
mode, and the one dumb dispatcher services it. Its own docstring states requirement 3 exactly: *"a mode is
a calculator the substrate invokes at the point a verdict is needed; WHICH mode fires and WHEN is decided
by the rules/procedure that emit the call (DATA), never by the dispatcher (which stays content-blind)."*
So "a metaprocedure uses a KB rule" is not a new idea to build — CHECK/CHOOSE/SUPPOSE are the working
precedent for "invoke a piece of the engine's own reasoning as a serviced call," and `suppose()` (found
earlier this session — see `STATUS.md`) is exactly what SUPPOSE_TOOL wraps.

### 2d. Failure is data, and recovery is more declared rules, not a Python `except`

`corpus/planning_execution.cnl` + `corpus/procedure.cnl`'s DISCREPANCY/EXCLUDE/RANK/REPLAN rules: a step
that finishes without its declared effect showing in the observed world becomes a `discrepancy` **fact**,
which a further declared rule reacts to — ranking untried alternatives, preferring the cheapest, retrying.
*"Failure folds to facts, rules recover — the post-hoc mismatch analogue of GAP-FILL's precondition."*
There is no Python `try`/`except` anywhere in this loop. This is requirement 2's spirit already realized for
*failure* specifically: the metaprocedure's own trouble is graph-resident, not a stack unwind.

### 2e. Two different "states," correctly on two different sides of the VM/content line

`ugm/machine.py`'s `ControlMachine` (PC, `BRANCH`/`BRANCH_IF`, `CALL`/`RET`, `SUSPEND`/`resume`) is the
VM's own internal stepping mechanism — real, working pause/resume (`dispatch.py`'s `service_calls_cm` uses
it: `SUSPEND` hands a `Continuation` to the driver, which resumes it later). Its own docstring is explicit
that this is process-resident by design: *"No graph snapshot: the graph is SHARED and monotone... For a
DURABLE continuation (serialize, resume across a restart) the stack/regs would live in
`AttrGraph.registers`... — not needed for in-process suspend/resume."*

**The first draft of this document treated that as the unclosed gap for requirement 2. It is not, and §1a
is why:** the `Continuation` is VM-internal bookkeeping (how far into servicing one batch of calls the
dispatcher has gotten) — a CPU register, not a fact a business rule would ever need to read. The state
that actually matters for interruptibility — *which step of which procedure is in progress* — is already
graph-resident, and already built: `chosen`, `ready`, `waits_for`, `done`, `discrepancy` (§2a/§2d) are
ordinary facts, exactly the shape an interrupting rule needs to see and act on. There is no gap here once
the two notions of "state" are told apart. (If a *durable, cross-restart* continuation is ever needed, the
module already names where it would live — `AttrGraph.registers` — but nothing has needed that yet, and
"nothing has needed it yet" is a fine reason for it not existing, not a design hole.)

### 2f. Rule-writes-a-rule is an ordinary, repeatable rule — not a bespoke one-shot mechanism

**Corrected from the first draft**, which called this "a one-shot compile." `ugm/cnl/define_surface.py`'s
`define schema` mints a genuine meta-rule (`Pat`-shaped, matched like any other) whose RHS writes flat
graph-resident rule-data (§2i) when its trigger fires — and `store_schema`'s own docstring says it is *"RE-run
against every later triggering declaration,"* not fired once. More tellingly, `ugm/learner.py`'s
`COOCCURRENCE` rule is not bespoke machinery at all: it is an **ordinary rule**, run through the **ordinary**
`run_bank`, whose RHS happens to write the same flat schema `define_surface.py` targets. Nothing about
"a rule writes a rule" needed a special one-shot compile step — an LHS/RHS rule can conclude rule-data the
same way it concludes anything else, repeatedly, as new matches arise. What *is* correctly a fixed,
Python-owned, non-repeated-per-match step is the **lift** (§2i) — turning that graph-resident rule-data into
an executable `Rule` object — and the **scheduling** of when to invoke it (`learn()`, `apply_schemas()`).
Those are VM/firmware, exactly per §1a, and correctly Python.

### 2i. Rules themselves are graph-resident data — general, not schema-specific

The crux finding that produced §1a's correction. `learner.py`'s own docstring names it precisely: *"THE
TARGET IS THE FLAT SCHEMA... A learned rule is written as `<rule> -rl_head/rl_lhs-> <cond>` with
`k_subj`/`k_pred`/`k_obj`."* This is the **same** vocabulary `define_surface.py`'s `compile_schema` writes
(`rl_key`/`rl_lhs`/`rl_head`, `k_subj`/`k_pred`/`k_obj`) — one general, engine-wide graph representation of
"a rule," used identically by two independently-motivated mechanisms (schema-triggered rule generation and
observation-driven rule learning), not two ad hoc encodings. `ugm/cnl/authoring.py`'s `expand_rules` is the
one fixed compiler — *"reads the meta-relations the forms accreted and emits `Rule`s"* — that reflects any
such graph-resident fragment into an executable `Rule`, loudly refusing a malformed one rather than
producing a silently-broken rule. This is the concrete, general, already-working answer to "can a business
rule be graph-resident data the fixed VM manipulates": yes, uniformly, and it is exactly what makes §2f's
rule-writing rules composable with everything else rather than a special case.

### 2g. The general propose→evaluate→apply gate exists, scoped to reactive predicates

`ugm/reactive.py`'s `fire()` (built on `reconsider.py`'s `mark_dirty`/`_affected`) — covered in depth
earlier this session (see `STATUS.md`): a cheap, purely structural **propose** step (`_affected`, a
body→head closure over the dirty set — no fact-matching, no cost), gated by an explicit per-predicate
opt-in (`P is reactive`, an ordinary KB fact — the content, per §1a) before anything is **evaluated**
(`chain_sip`, the real check), and only a genuinely-derived result is **applied** (materialized or,
symmetrically, withdrawn). *"LAZY BY DEFAULT... PER-PREDICATE opt-in: an undeclared predicate stays
pull-only... eager exhaustive completion stays out."* This is requirement 4's shape correctly built: Python
orchestration (`fire`, `_derive`, `sweep`) — VM layer — consulting graph-resident opt-in data.

### 2h. `resolve_crossings` — this session's own generalization, same shape again

Covered in full above: region-select (`_crossing_scopes`, now driven by declared `crosses_scope` data) →
demand-evaluate (`chain_sip` for `holds_base`) → apply (`_promote_held`), bounded by `focus_scope`. A third
independent instance of the identical shape, built for propositional crossing specifically, and correctly
Python-orchestrated for the same reason as §2g. Three working instances of one shape (2g, 2h, CHECK/CHOOSE/
SUPPOSE's dispatch in 2c) is not, per §1a, evidence they should be forced into one function — three fixed
VM-level mechanisms sharing a discipline is fine; §4 asks a narrower, more concrete question about only one
of the gaps this shape leaves.

---

## 3. Two precise, load-bearing gaps — found, not assumed

`corpus/planning_execution.cnl` line 21, the exact point where a plan step's *readiness* becomes a *real
world action*:

```
<exec> ready ?o when ?o chosen <yes> and not ?o unmet ?anyp and not ?o waits_for ?anyb and not ?o done <yes>
<call>? tool act and <call>? arg ?o when <exec> ready ?o
```

**Gap A — runtime, act-dispatch.** The second rule has no guard at all beyond readiness. A `chosen` step
that clears its preconditions mints a real `<call> tool act` — dispatched by `dispatch.py`'s content-blind
servicer — the moment it is ready, unconditionally. Compare `units/prohibition_rules.py`'s validated
finding: a standing `dangerous` fact vetoes an unrelated later command, order-independent, an ordinary
guard. `ugm/`'s planning bank has never had that guard added at the one point a real action leaves the
graph.

**Gap B — load-time, rule-authoring (named by §1b's correction, not yet closed by anything in this
document).** `chosen`, `ready`, `waits_for`, `done` are today plain, ordinary predicates — nothing
structurally stops a business-authored rule from concluding one of them directly (`?s chosen <yes> when ?s
is_a espresso_step`), silently bypassing GAP-FILL/ordering, or forging `ready` for a step that never
actually cleared its preconditions. This is a different failure point from Gap A: Gap A is about a real
action being dispatched without a check; Gap B is about the *readiness state itself* being forgeable by
content that was never supposed to have write access to it at all — and per §1b, closing it must not break
`chain_sip`/`suppose()`'s ability to reach the readiness derivation, so the fix cannot be "make it opaque."

---

## 4. Two enforcement points, not one — resolved by §1a/§1b, not left open

**Gap A's fix (unchanged from the first correction): a runtime checkpoint in the dispatcher.** Every
working precedent in §2 has the fixed, Python-implemented VM consult graph-resident data before acting —
`reactive.py`'s `fire`/`_derive` consults `P is reactive`; `resolve_crossings` consults `crosses_scope`;
`expand_rules` consults rule-data. `dispatch.py`'s central servicer should equally consult a standing,
graph-resident veto marker before running ANY handler (tool/mode/act alike) — not a local NAC on one CNL
rule, which every *future* call-emitting rule would need to remember independently. This costs `dispatch.py`
one bit of content-awareness (a reserved marker name, never a value it interprets) — the same bit every
other VM-level mechanism in §2 already carries.

**Gap B's fix (new, from §1b): a load-time privilege gate on rule authoring, not a runtime check at all.**
The readiness/ordering/`GAP-FILL` derivation must stay a declared rule (§1b — so hypothetical reasoning can
reach it), so the fix cannot be "hide it from matching." It must instead be **who is allowed to write an
RHS targeting a reserved predicate**, checked when a rule is loaded/compiled — the same shape `RETIRE`'s
"not in the ordinary lowering vocabulary" gate already has, applied to CNL rule-authoring instead of an
opcode: a reserved-predicate registry (`chosen`, `ready`, `waits_for`, `done`, and any future veto marker),
and `expand_rules`/the loader refusing — loudly, per its existing discipline (§2i) — any rule from a
non-mechanism bank whose RHS concludes one. `corpus/procedure.cnl`/`planning_execution.cnl`'s own
INVOKE/ORDER/GAP-FILL rules are the one privileged bank allowed to write them; RANK/REPLAN (§1b: correctly
category 1/2, business-tunable cost/preference policy) writes only ordinary predicates (`cost`,
`cheaper_than`, `outranked_by`) and needs no exemption.

**The two gaps are independent and both need closing — one is not a substitute for the other.** Closing
Gap A alone still lets a business rule forge `ready` directly (bypassing the planner's own logic entirely,
never touching the `<call>` the dispatcher gates). Closing Gap B alone still lets a legitimately-`ready`
step's `act` call be serviced with no standing-prohibition check. They sit at different points in the same
pipeline (write access to state → dispatch of an action derived from that state) and the fix at each point
is a different mechanism for the reason §1b gives: Gap B's fix must preserve declared-rule reachability,
Gap A's need not (the dispatcher's servicing loop is genuinely opaque, §1b's second case).

---

## 5. The first probes, proposed

Two separate, minimal, checkable tests — one per gap — not yet built:

**Probe 1 (Gap A — the runtime checkpoint):**
1. Author a two-step toy procedure (`to demo : step_a then step_b`), each step an ordinary `act`-dispatched
   operator with no real side effect beyond marking itself `done`.
2. Run it (`run demo`) far enough that `step_a` completes (its `<call> tool act` serviced, `done` set) —
   confirming §2e's point directly: `step_a`'s progress is visible as an ordinary fact throughout.
3. **Before** `step_b` becomes ready, assert a standing prohibition fact that should cover it (mirroring
   `prohibition_rules.py`'s validated `dangerous` shape), and teach `dispatch.py`'s servicer to check it.
4. Check: does `step_b`'s `<call> tool act` ever get serviced, or does the procedure genuinely halt at that
   step with the prohibition visible as the reason (a fact, not a silent stall) — and does `step_a`'s
   already-done work stay intact (the gate stops the *next* step, never retroactively undoes a completed
   one)?

**Probe 2 (Gap B — the load-time privilege gate, and that it doesn't break hypothesis-reachability):**
1. Author a business-shaped rule whose RHS directly concludes a reserved predicate (`?s chosen <yes> when
   ?s is_a espresso_step`), load it, and check the loader refuses it loudly — the same discipline
   `expand_rules` already applies to a malformed fragment (§2i), extended to an unauthorized target.
2. Confirm the mechanism bank's *own* rules (`procedure.cnl`'s INVOKE/ORDER/GAP-FILL) still load and run
   normally — the gate must distinguish privileged-bank authorship, not reject the predicate outright.
3. **The hypothesis-reachability check, the one that matters most given §1b's correction:** run a
   `suppose()` call whose assumption is an ordinary business fact (e.g., "the door is locked") and whose
   prediction asks whether a plan step would become `ready` under that assumption — confirm the in-scope
   `chain_sip` reasons through the privileged INVOKE/ORDER/readiness rules exactly as it does for
   unprivileged business rules, deriving a hypothetical, pencil-scoped `ready` verdict without touching
   real ink. If this fails, Gap B's fix was implemented as opacity rather than privilege, and §1b's whole
   argument for keeping mechanism declared rather than Python was not actually honored.

If both probes hold, that is real evidence for §1a/§1b together: a small, fixed, reserved-marker-aware VM
checkpoint (Gap A) plus a load-time authorship gate on declared rules (Gap B) are enough — neither needs a
graph-resident interpreter, and neither costs hypothetical reasoning's ability to reach the mechanism.

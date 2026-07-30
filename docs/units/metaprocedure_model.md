# The metaprocedure model — goal-driven, materialized, centrally gated

**Status: design, 2026-07-30; corrected the same day.** Written as the foundation decision to build forward
on `ugm/`'s substrate (`arc_recap.md`'s current Act, `attic/handoff_ugm_reversion_evaluation.md`), because
answering "what should replace `run_bank`'s blind fixpoint driver" turned out to require stating the whole
computation model precisely, not just one mechanism. **The first draft of this document over-corrected —
see §1a — and was revised the same day once that was caught.** Read `model.md` §11 first (homoiconicity is
the actual source of this project's advantage over the Soar/ACT-R/BDI lineage, not goal-orientation or tool
dispatch — this document is what §11 cashes out to, mechanically). Read `STATUS.md` for where this sits in
the current work queue.

**What this document is not:** a proposal to build something new from nothing. Every piece named in §2 below
already exists in `ugm/`, most of it pre-dating this session by a wide margin. What was missing was seeing
them as one model rather than several separate modules, and naming the one precise gap (§3) that stands
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

## 3. The one precise, load-bearing gap — found, not assumed

`corpus/planning_execution.cnl` line 21, the exact point where a plan step's *readiness* becomes a *real
world action*:

```
<exec> ready ?o when ?o chosen <yes> and not ?o unmet ?anyp and not ?o waits_for ?anyb and not ?o done <yes>
<call>? tool act and <call>? arg ?o when <exec> ready ?o
```

The second rule has **no guard at all** beyond readiness. A `chosen` step that clears its preconditions and
ordering mints a real `<call> tool act` — dispatched by `dispatch.py`'s content-blind servicer — the moment
it is ready, unconditionally. This is true whether the step came from the synthesizing planner or from an
authored `to NAME : ...` procedure (§2a: one execution gate, both feed it).

**Compare this to the validated finding on the `units/` side** (`prohibition_rules.py`, the CNL-boundary
work earlier this session/arc): a standing `dangerous` fact vetoes an unrelated later command,
order-independent, with zero new engine machinery — an ordinary NAC guard added to the rule that would
otherwise act. `ugm/`'s planning bank has never had that guard added to its own act-dispatch rule. Nothing
here says it would be hard — Act III's own finding is that a prohibition is *"the closed-world-stance-fact
pattern generalized,"* an ordinary conjunct, and `corpus/procedure.cnl`'s REPLAN family already shows this
bank composes cleanly with additional declared conditions. **But it has not been checked, here, at the one
point where a real action actually leaves the graph.** That is the concrete, falsifiable gap this document
names rather than assumes closed.

---

## 4. Where the check should live — resolved by §1a/§2i, not left open

The first draft left this as an undecided fork. It is not, once §1a's split is applied: the question "should
the veto be a local NAC on one CNL rule, or a check the central dispatcher performs" is really "should this
particular piece of gating logic be graph-resident content, or fixed VM behavior" — and every other
mechanism in §2 answers that the same way. `reactive.py` (§2g) has the VM (`fire`/`_derive`) consult a
graph-resident opt-in fact (`P is reactive`); `resolve_crossings` (§2h) has the VM consult a graph-resident
`crosses_scope` fact; `learner.py`/`define_surface.py` (§2f/§2i) have the VM (`expand_rules`) consult
graph-resident rule-data. In every working precedent, **the fixed, Python-implemented dispatcher is what
consults graph-resident data — not the other way around, and not left to each content-authoring rule to
remember independently.**

So: `dispatch.py`'s central servicer should consult a standing, graph-resident veto (a reserved marker a
prohibition bank populates — mirroring `P is reactive`'s shape) before running ANY handler, tool/mode/act
alike — not a local NAC threaded through `planning_execution.cnl`'s one rule, which would leave every
*future* call-emitting rule to remember the same guard independently, exactly the failure mode the user's
original framing named. This does cost `dispatch.py` one bit of content-awareness (today it is purely
content-blind, per its own docstring) — but it is the *same* bit every other VM-level mechanism in §2
already carries (a reserved marker name, never a value it interprets), not a new kind of coupling.

---

## 5. The first probe, proposed

A minimal, checkable test that the resolved design (§4) actually holds, not yet built:

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
5. If this holds, it is also indirect evidence for §1a generally: a small, fixed, content-aware-only-of-one-
   reserved-marker VM checkpoint is enough — nothing about this probe should need a graph-resident
   interpreter for the checkpoint logic itself.

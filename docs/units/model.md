# The computation model

**Status: design, not code.** Nothing described here is built. `units/` as it stands implements an earlier and
different model — see *What this replaces* at the end. This document is the target; where it disagrees with the
code, the code is wrong.

**What this document is.** The computation model, derived from first principles, with worked examples. It is
organised so that each section only depends on the ones before it. Read it in order; the mechanisms in §5
cannot be understood without §4, and §4 cannot be understood without §3.

---

## 1. The claim

The system holds a **graph of data that persists**, and computes over it by **assembling a transient circuit**.

> Data is the substrate. Computation is scaffolding built over it, used, and thrown away.
>
> Persistent data is itself the **digital twin** of something outside the system — a real Paul, a real
> codebase, a real invoice. Being stale or wrong is a normal condition, not a fault.

Two things follow immediately, and they shape everything else.

**Nothing happens unbidden.** An external event — an utterance, a schedule firing, a tool result — starts a
turn. A goal fires. Firing is what causes units to be created and wired. Absent a goal, the system is silent.
There is no drive toward closure, no completion of the derivable, nothing that runs because it *could*.

**Reasoning has two loops, and they are System 1 and System 2** (§7). An associative outer loop retrieves the
rules that *come to mind* given the data and the goal; a deliberate inner loop applies them exactly. The outer
loop is allowed to be wrong about relevance. The inner loop is not allowed to be wrong about consequence.

---

## 2. What a unit is not

Two disclaimers up front, because both are natural readings of "network of computations" and both are wrong
here.

**It is not event-driven, and there is no scheduler.** A unit is not a subscriber woken by a message bus. The
assembled network is a **circuit**: values enter at an input, each unit transforms what arrives at its gates,
and output falls out the far end. Closer to ETL, or to logic gates, than to actors.

**It is not a fixpoint engine.** There is no work-list running to quiescence, no "output unchanged" termination
test, and no requirement that the network be acyclic. A cycle is fine and iterates.

---

## 3. Data

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
  twice — once over nodes and once over edges.

⚠ **This reverses an earlier position.** `ugm` held that *direction carries the roles* (subject → predicate →
object) and rejected role labels as engine complexity. That works for arity 2 and fails at 3. Direction now
carries only *outward from the occurrence*; the role node carries which role. The reason for the reversal is
uniformity of machinery, not expressive parsimony.

---

## 4. Matching

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

---

## 5. Units, gates, and firing

A **unit** holds a pattern and a transformation. It has **input gates** and one **output**. It sees only what
its gates deliver — there is no ambient store to read, so isolation costs nothing and forbids nothing.

**Gates latch.** A gate retains the last value that arrived on it. When something new arrives on any gate, the
unit fires using the latched values of the others. It does not block waiting for the rest.

**A repeat arrival is a firing.** The same value arriving twice fires the unit twice. There is no
value-comparison test suppressing it, and therefore no notion of quiescence.

**Consequences, stated plainly because two of them are costs:**

- A cycle is legitimate and iterates. Depth is assembled, not pre-wired.
- **A unit is stateful and order-dependent.** Because gates latch, output depends on the order arrivals came in
  across gates, not only on the set of values. So a unit is a sequential circuit, not a combinational one, and
  `output = f(inputs)` is false. Determinism has to be argued, not assumed (§11).
- **A loop dies by running out of data, or by fuel.** It does *not* die by settling. A monotone rule fed the
  same value forever produces the same conclusion forever, quite happily. Termination comes from a gate that
  stops being fed — a recursion reaching the end of a list, a selector finding no referent — or from the
  budget.

---

## 6. Statements, seals, and tunnels

This is the section the architecture exists for.

### A statement is atomic, but built as a chain

> *"When a lion sees a gazelle, it runs to try to catch it."*

Break that in the middle and the meaning is gone. So it is **one logical unit**: it reacts to a seeing
occurrence with a lion agent and a gazelle patient, and emits a running occurrence with catching as its
purpose.

But arbitrary depth means a grammar must be able to **unroll** a statement — you cannot have a flat inventory
of recognised forms. So a statement of any complexity is *built* as a chain of units. Both are true at once:
logically atomic, physically a chain.

The reconciliation is **explicit markers**. A statement wears a **begin** and an **end** marker, and

> **only the end marker is attachable.**

The interior is sealed. Nothing may wire into the middle of *"if tomorrow rains, bring the umbrella"* and
consume *"if tomorrow rains"* on its own. This is why topology alone is insufficient: once you attach something
downstream of a chain's end, that end sits in the middle of a longer chain, and the fact that it *was* an end
is destroyed. A marker survives; a position does not.

**The seal makes the interior unobservable, including to a goal.** Nothing can ask *"does the lion see the
gazelle?"* — that is the antecedent, sealed inside. That is the price, and it is the right price.

### Nesting is physical

A statement can contain a statement. *"Paul knows that when a lion sees a gazelle it runs"* is a sealed span
inside another sealed span. Hypotheses, embedded clauses, attributed beliefs, and counterfactual worlds are all
**the same construct at different containment**. There is no scope object, no world identifier, no
comparability test, no "only a carrier may fork a world."

This is the whole reason for the paradigm flip. In a central-machine design, nesting has to be *translated*
into something a stack-based evaluator can walk, and every rule then has to match the scope it is operating in.
That is what became unmanageable. Here the nesting is a structure, and you get it by building it.

### The chain is a tunnel

A chain of statements establishes a **tunnel**: everything downstream of it computes within the scope that
chain establishes, and **no rule ever re-matches a scope on the graph.** Isolation is not enforced by a check;
it is a consequence of what is wired to what.

**Getting out is one explicit act.** *"Suppose it rains — then I'd need the umbrella — so take the umbrella."*
The only exit is a wire from the tunnel's **end marker** into the enclosing chain. So scope-crossing needs no
permission rule, no crossing predicate, and no data: it is simply whether someone attached to the end marker.
The end marker is the tunnel's **output port** — the one place new rules may attach and the one place a result
may be written back to persistent data.

### Scope in the graph vs scope in the circuit

Both exist, and they are not redundant:

| | holds | role |
|---|---|---|
| **graph** | the nesting, explicitly | scope *survives across turns*; the circuit does not |
| **circuit** | the tunnel | scope is *free during computation*; no rule matches it |

So each turn re-derives the tunnel from the graph's nesting, and write-back maps a tunnel position back into
nesting. The invariant that matters:

> **Scope is written by the boundary, read by the assembler, and never mentioned by a rule.** If any rule's
> pattern names a scope, the design has regressed.

---

## 7. The two loops

A turn is a sequence of **steps**. Each step is:

```
1. RETRIEVE   given the current data (including the goal), which rules come to mind?
2. ASSEMBLE   mint units for them, wire them by the ordinary policy
3. RUN        the circuit runs to completion, bounded by fuel
4. WRITE BACK conclusions and derivations become data
```

and then the next step retrieves against the data step 3 produced. This is the outer loop.

**Step 1 is System 1.** Associative, approximate, not rationally controlled. It is a **similarity match over
the graph** — the same graded matcher of §4, doing recall instead of application. It is allowed to be
incomplete and allowed to be wrong; the cost of a wrong suggestion is a wasted step.

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

---

## 8. Goals and termination

### A goal is data

A goal is a node carrying a description of **what would satisfy it**. It has to be data: it is persisted across
a suspension, and rules must be able to produce subgoals.

Plan, step, subgoal, and expectation are all the same shape — a description of a satisfaction condition — which
is why *"fix the `computeAccrual` function"* decomposes uniformly: rules turn the goal into a plan, the plan's
steps are goals, each step's expectation is that step's satisfaction condition, and checking one is an ordinary
rule match. Nothing about "plan" is a new kind of thing.

### Done is a fact, never an absence

The temptation is to say a step ends when the network stops producing. That conflates four different outcomes.
Each is a **positive fact**:

| fact | meaning | next |
|---|---|---|
| `satisfied` | a rule matched the goal's own satisfaction condition | stop; the answer is in the data |
| `starved` | nothing came to mind, or nothing matched | *not* "underivable" — see §7 |
| `out_of_fuel` | the inner budget was exhausted | a handler unit can be wired to it |
| `awaiting` | a value must come from outside | suspend (§9) |

An LLM agentic loop is the same shape and is worth the comparison: the loop continues while the response's stop
reason is `tool_use` and exits otherwise, and `end_turn` is an **emitted** end-of-turn signal — the model's
positive act of stopping. The reason the API grew *distinct* stop reasons (`end_turn`, `max_tokens`,
`pause_turn`, `refusal`) is precisely that finished, truncated, paused, and declined need to be told apart. A
loop that tests only "no tool call" silently conflates all four. Same lesson, one level up.

### Two budgets

Fuel bounds the **inner** loop — one circuit's run. The **outer** loop needs its own budget, because System 1
will keep offering rules and steps will keep happening. Their exhaustion is not the same fact: *"this
computation didn't converge"* versus *"I stopped thinking about this."* An agent needs to be able to say the
second.

Both are values something can be wired to, not return codes.

---

## 9. The boundary

### Pull

The event that starts a turn brings data in — an utterance interpreted, a schedule firing, a tool result. But
retrieval mid-turn is real too: a subgoal can reach outside, and activating a tool is exactly that. So the
boundary is bidirectional and live, not a load-then-compute phase.

A starved gate is the natural signal: it emits a **miss**, and something wired to the miss goes and looks. That
is the same shape as the out-of-fuel handler, which is a good sign the mechanism is the right size.

### Suspend is a gate that hasn't been filled

A tool call means a gate will be filled later — maybe seconds, maybe after this turn is over. So:

> **Suspension is not continuation machinery.** It is a pending demand, represented as data: *this goal awaits
> a value of this description*.

The turn can end. Resume is then not a special path — it is an ordinary turn whose triggering event happens to
match a pending demand. One mechanism covers four cases: a tool call, fuel exhaustion, a question put to the
user, and a standing watch (*"tell me when the price drops"*). Blocking and holding the circuit in memory
remains available as a pure optimisation for fast calls, but nothing may depend on it.

Two rules make the rebuild sound:

- **Resume continues; it does not replay.** Because derivations are written back, everything already concluded
  arrives as data. The rebuilt circuit does not have to re-reach those conclusions, or reach them the same way.
- **Suspension is a write-back point**, not only turn-end.

And the staleness worry answers itself: if the rebuilt network differs, it differs *because the data changed* —
in which case resuming into the old network would be the wrong behaviour. A stale trigger is reconsideration
arriving between turns instead of within one.

### Write-back

Conclusions **and derivations** are written back. Persisting the derivation is what lets the circuit be thrown
away — it is the thing that makes a turn stateless. It also means provenance is **ordinary data**: rules can
match on it, so the system reasons about its own reasoning with no new mechanism, no separate provenance
channel, and no stratification discipline. Nothing prevents a rule from reading derivations of rules reading
derivations — which is the author's problem, not the engine's (§11).

---

## 10. Walkthrough: one goal, five steps

A small case, end to end, to show how the pieces move together. Note where the **turn** boundaries fall — they
are not the same as step boundaries, and that is the point.

> **Utterance:** *"Should Paul get the loyalty discount?"*

The front end interprets it and writes a goal into the graph. The goal carries its own satisfaction condition —
*a fact about this Paul-node stating discount eligibility, or its denial* — and a fresh mention node for Paul
with `name = "Paul"`. Whether that node is *the real Paul* is not yet decided; a rule will decide it, and can be
wrong.

---

### Step 1 — retrieve, and starve

**Retrieve.** System 1 offers two rules. One is the sealed statement

> *"A customer gets the loyalty discount when they have been a member for over a year and their account is in
> good standing."*

The other is a **birthday discount** rule. Nothing here suggests a birthday; System 1 is associative, not
correct.

**Assemble.** The eligibility statement unrolls into a chain of units with a begin and an end marker. It has two
open gates: one wanting a membership date, one wanting an account standing. The birthday rule gets its own unit.

**Run.** The birthday unit matches nothing and emits nothing — it **starves**. Both eligibility gates are unfed,
so each emits a **miss** carrying the description of what it wanted.

**Write back.** Two pending demands, one per miss. The birthday rule's silence is recorded too: *nothing came to
mind past this point* — which is `starved`, **not** *"Paul has no birthday discount."*

**Outcome:** `awaiting` ×2. One wasted rule, and that is the expected cost of associative retrieval.

---

### Step 2 — the boundary reaches out

The pending demands are visible to the boundary, which activates two tools: the membership system and the
accounts system. Both gates will be filled later.

**The turn ends here.** No circuit is held in memory. What persists is the graph: the goal, the partial
structure, the two pending demands, and the derivation so far.

---

### Step 3 — a tool result resumes the work *(new turn)*

The membership result arrives. That external event starts a turn exactly like the utterance did — resume is not
a special path, it is an ordinary turn whose triggering event matches a pending demand.

**Retrieve.** The goal is still open, so the eligibility statement comes to mind again. So does a date rule for
*over a year*.

**Run.** `member_since = 2019-03` now feeds the first gate. The duration sub-conclusion fires. The second gate
is still unfed and still starves.

**Write back.** *Paul has been a member for over a year*, plus its derivation.

**Outcome:** still `awaiting` — one demand, not two.

⚠ Note what did **not** happen: step 3 rebuilt the circuit from scratch, but it did not re-derive anything.
**Resume continues; it does not replay.** The membership conclusion is now data, so the next step reads it
rather than re-reaching it.

---

### Step 4 — a graded match, and satisfaction *(new turn)*

The accounts result arrives: **two payments late**.

**Retrieve.** The eligibility statement, plus a rule about what counts as good standing — and this one is
graded: *an account with a few late payments is marginally in good standing*.

**Run.** The standing rule matches at reduced strength. The conclusion **inherits the band**, so eligibility
fires — but marginally, not flatly. The goal's satisfaction condition matches the conclusion.

**Write back.** *Paul is eligible for the loyalty discount* at a marginal band, with a derivation that names
both premises and the band it came from.

**Outcome:** `satisfied`. The answer is in the graph, and it is explainable next week because the derivation was
written back with it.

---

### Step 5 — a hypothetical, and one crossing *(new turn)*

> **Follow-up:** *"What if he pays them off?"*

**Retrieve + assemble.** The front end writes a nested statement: a supposition containing *Paul's payments are
settled*. Nesting is physical, so the hypothesis is a sealed span **inside** the current context. Everything
wired downstream of it computes inside that tunnel. No rule anywhere matches on "am I in a hypothesis" — the
rules are the same rules as step 4.

**Run.** Inside the tunnel, standing is clean, so eligibility fires unqualified.

**Cross.** That conclusion is stuck in the tunnel until something attaches to the tunnel's **end marker** — one
wire, one explicit act. Nothing was permitted, no crossing predicate consulted; someone attached to the output
port, or they didn't.

**Write back.** *If the late payments are settled, Paul is fully eligible* — the conclusion carries its
containment, so it is recorded as conditional rather than asserted flatly.

**Outcome:** `satisfied`.

---

### What the walkthrough demonstrates

| | where |
|---|---|
| nothing runs unbidden — the goal fires everything | steps 1, 3, 4 |
| retrieval is allowed to be wrong; the cost is a step | step 1, the birthday rule |
| `starved` ≠ *"underivable"* | step 1 |
| a starved gate is how the system reaches outside | steps 1→2 |
| suspend is a gate that hasn't been filled; the turn ends | step 2 |
| resume continues from data rather than replaying | step 3 |
| degree flows from match strength into the conclusion | step 4 |
| done is a positive fact matching a stated condition | steps 4, 5 |
| a hypothesis is nesting, and crossing is one wire | step 5 |
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

**The front end is a controlled natural language.** Unambiguous by construction. It draws statement boundaries,
mints role nodes, and generates the explicit name-matching a rule needs. It must target data, never an engine
API — otherwise the system can *say* things it cannot *learn*.

**IDs are plumbing.** Pointers to instances are a technical device with no semantic content. Deciding that a
mental node refers to a particular real thing is a *rule's* decision, and can be graded and wrong.

---

## 12. Invariants worth testing

Each is the kind of thing that is obviously right on paper and quietly wrong in a build.

1. **No rule pattern names a scope.** The single strongest signal of regression.
2. **Nesting → tunnel → nesting round-trips.** Rebuild reads nesting to make the tunnel; write-back maps
   tunnel position back to nesting. This is where silent drift will happen.
3. **A unit reads only its gates.** No ambient access, ever.
4. **Units never wire anything.** The assembler is the only writer of topology. If routing is ever learned,
   units *propose* wirings as facts.
5. **Every step ends in exactly one positive outcome fact.** Never in an absence.
6. **Nothing matches by name unless a rule says so** — `name` has no privileged status anywhere in the engine.
7. **A turn is reconstructible from persisted data alone.** No hidden in-memory state is load-bearing.
8. **Only end markers are attachable.** No wire terminates inside a sealed span.
9. `units/` imports nothing from `ugm/`.

---

## 13. Open questions

Genuinely undecided, not oversights.

- **Determinism under latching.** "A turn is stateless because derivation is in the data" assumes a rebuild
  reproduces the result. Latching makes a unit order-dependent, so replay is faithful only if arrival order is
  reconstructible — or if order-dependent cases are rare enough to be a curiosity. Which one decides whether
  invariant 7 (§12) is a guarantee or a good approximation.
- **Write-back and contradiction.** A conclusion disagrees with persistent data. Overwrite, coexist as a second
  graded claim, or refuse? Inside a computation, nesting lets you hold both; write-back has to land somewhere.
- **Can a unit remove?** Never settled. With graded attributes and write-back, *"Paul is 30"* meeting *"Paul is
  31"* is routine, not exotic. (Was `decisions/0032`.)
- **The retrieval function.** §7 says relevance is retrieved by resemblance. What resemblance, concretely — and
  is it authored data like every other similarity judgement, or the one thing the engine fixes?
- **Role node sharing.** Role nodes are per-occurrence and match by declared name-equality. Is that equality
  rule loaded once as ordinary KB data, or restated per rule? The first risks becoming a de-facto vocabulary
  through the back door.
- **The outer budget's shape.** Steps, wall clock, or something the goal itself carries.
- **Homoiconicity.** Deliberately deferred. The computation network may itself be a graph (hyperedge with begin
  and end marker nodes), which makes it tempting; not yet.

---

## Your annotations on `reference.md`, answered

| annotation | where |
|---|---|
| "explain the computation model first" | §§2–8, in dependency order |
| "what *is* the state? a cache of last output?" | §5 — latched gates plus last output; and semantics are **not** functional, which the old doc claimed |
| "prove everything can be expressed via S-P-O — *yesterday Paul and Mary went to the park riding bicycles*" | §3 — it **cannot**, and S-P-O is dropped. Role nodes, worked on that sentence |
| "matching must compare topology and attributes, with fuzzy logic" | §4 — and identity-matching is gone |
| "explain *kind* — are we building superstructures?" | §3, §11 — `kind` is deleted, along with the in-degree taxonomy |
| "explain what `Absent` does" | §4 — exact absence is gone; θ threshold, and the loss is deliberate |
| "roles, lexemes — superstructure, this will not compose" | §3, §11 — the vocabulary/form-set split is deleted; names are ordinary attributes |
| "why should the system look for more expansions? goals should drive this" | §§1, 7, 8 — two loops, nothing unbidden |
| "not only frontier-first: you may only attach at the *end*, and you need a marker" | §6 — the seal |

---

## What this replaces

`docs/units/reference.md` is deleted. `docs/design/substrate_inversion.md` and `docs/units/decisions/` are left
in place as the reasoning trail, but the following are **contradicted** by this document and should not be
treated as current:

| decision | status |
|---|---|
| `0001` computation units are the substrate | **reversed** — data is the substrate (§1) |
| `0002` one unit class, taxonomy from in-degree | dropped — no `kind` (§3) |
| `0004` functional semantics, the cache makes the fixpoint work | **dead** — no fixpoint; latching makes units stateful (§5) |
| `0006` comparability, `0038` only a carrier forks a world | replaced by physical nesting (§6) |
| `0007` scope is a chain never a key | **half** — a chain, yes, but it needs explicit markers (§6) |
| `0009` frontier-first wiring | replaced by end-marker attachment (§6) |
| `0011` two negations, one is cheap | dead — graded matching removes the cheap one (§4) |
| `0012`, `0013` provenance on its own wire, stratified | replaced by provenance as ordinary data (§9) |
| `0017`, `0026` roles/lexemes belong to the form set | **half** — roles are nodes, yes; the shared vocabulary is deleted (§3) |
| `0030` an exhausted budget is `UNKNOWN` | replaced by fuel-as-a-fact (§8) |
| `0040`, `0041` roles positional, calls positional | replaced by role nodes (§3) |
| `0003`, `0005`, `0010`, `0019`, `0031`, `0039` | **survive** — bounded store, index of computation, units never wire, revision by recomputing forward, no `ugm` import, guards-yes-kinds-no |

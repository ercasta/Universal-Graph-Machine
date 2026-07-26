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

- A cycle is legitimate and iterates. Depth is assembled, not pre-wired. ⚠ But see §7 — because the outer loop
  is tight, **cycles inside a circuit may turn out to be nearly unnecessary**, and if that holds, latching and
  refire-on-repeat stop being load-bearing and this section gets simpler. Treat it as a prediction to test, not
  a settled requirement.
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

**Step 1 is System 1.** Associative, approximate, not rationally controlled. Subgraph similarity — the same
graded matcher of §4, doing recall instead of application — or any other associative mechanism. It is allowed
to be incomplete and allowed to be wrong; the cost of a wrong suggestion is a wasted step.

**It is also non-deterministic, deliberately.** The same data and the same goal may bring different rules to
mind on different occasions, so two runs of the same turn may reason differently and reach different places.
This is not a defect to be engineered out — it is what happens to people, and it is acceptable in an agent. It
does mean nothing downstream may assume reproducibility (§12, invariant 8).

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

### Attention bounds retrieval

Application is bounded by wiring — a unit sees only its gates. Retrieval has no such bound: associative recall
against the whole twin is exactly what cannot be afforded. So:

> **Attention bounds retrieval, not application.** System 1 recalls against the attended region of the graph,
> never the whole of it.

This does two jobs at once. It makes retrieval tractable, and it makes retrieval's incompleteness *principled*
rather than a shrug — *"I only considered what I was attending to"* is a statable reason, the same shape as the
`starved` fact. Attention is data, so a rule can conclude *attend to X*, and a retrieval hint is just an act of
attention.

**Two hard requirements, not tuning parameters.**

**A pending goal must stay attended.** Because the loop is tight (below), a goal is re-retrieved dozens of times
before it is satisfied — pinned, or refreshed by its own pendency. Uniform decay turns the tight loop's
advantage (relevance tracks the state) into its failure mode (relevance drifts off the purpose).

**Linguistic competence must be attended even when nothing is.** At the start of a turn attention holds almost
nothing: a transcribed utterance and a fresh goal (§9). System 1 has to surface the interpretation rules out of
that near-empty state or comprehension stalls before it begins. So the bundled interpretation rules are
always-attended in a way domain knowledge is not — a principled asymmetry, not a hack, and the same asymmetry
people have.

⚠ **This reverses a `ugm` finding, and the reversal is the point.** `ugm` built associative recall and concluded
it must be **explicit, never auto-fired**: auto-firing on a demand miss flipped negation-as-failure and was
self-reinforcing. Here recall fires automatically on every step. The hazard is the same; the fix is opposite.
`ugm` banned auto-fire to protect a strong negation; this design **weakens the negation instead**, so there is
no longer a strong claim for recall to corrupt. The self-reinforcement half of that finding is *not* resolved
(§13).

### Why the loop is tight

Steps are fine-grained — one step fires whatever sealed statements came to mind, not a phase of work. Three
consequences are load-bearing:

- **Relevance tracks the evolving state.** Coarse steps judge relevance once and then derive a great deal under
  that judgement, by which time the data it was judged against is gone. Re-retrieving after each small inference
  is the mechanism of *one thought leading to another*: what this step concluded is what the next step notices.
- **Control lives outside the circuit.** Coarse steps force branching and iteration *into* the network. Fine
  steps supply control from outside — the sequence of what gets retrieved next *is* the control flow. This is
  what makes the circuit small, which in turn is what makes discarding it every step affordable.
- **Interruptibility.** Step granularity *is* responsiveness granularity: new input can only be taken into
  account at a step boundary, so a coarse step is an opaque block the agent cannot be steered out of.

**The grain is not a free parameter — the seal fixes it.** A statement is atomic (§6), so the smallest possible
step is one whole sealed statement, never one inference.

**The cost, stated plainly.** Fine grain trades inner-loop work for outer-loop work, and the outer loop is the
expensive one: retrieval now runs on every step. Attention is the mitigation, but where the optimum sits is
empirical and worth measuring early — because if retrieval proves expensive the pressure will be to coarsen
steps, and coarsening gives back all three gains above. Second-order: each step contributes a non-deterministic
retrieval, so a long chain of fine steps has more variance in where it lands than a short chain of coarse ones.
Goal-pinning is what keeps that from becoming a wander.

**Recorded, not yet built — asynchronous System 1.** Retrieval can run concurrently, keeping a buffer of
candidate rules filled ahead of the step that needs them, taking it off the critical path. This is *licensed*
rather than merely fast: a stale buffer trades away no property that was ever claimed, because retrieval is
already incomplete and non-deterministic. The same trick is forbidden for System 2, where application must be
exact — which is a useful check that the asymmetry is cut in the right place. Four notes for when it is built:
**age candidates** (each carries the attention state it was retrieved under) rather than invalidating on an
attention-shift threshold; keep the buffer **diverse rather than top-k**, which is also the mitigation for
self-reinforcement; **record the buffer's contents in the derivation**, so a timing-dependent turn stays
explainable even though it cannot be replayed; and if the buffer also prefetches *data*, **speculate reads,
never actions** — that line belongs in the boundary, not in a rule's judgement. Do not build it before
synchronous retrieval exists and is measurably slow: every parameter in it depends on measurements that cannot
be taken yet.

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

**An outcome attaches to a goal, never to a step.** A tight step may advance several pending goals, so each
gets its own outcome fact.

**Goals form a lineage** — a goal produces subgoals — and that lineage is what carries the explanation. It is an
ordinary relation between ordinary goals; a goal with no parent is just a goal with no parent, not a different
kind of thing. Combined with the outcomes above it distinguishes four states that would otherwise collapse:

| | on the **first** goal of a turn | on a **descendant** |
|---|---|---|
| `starved` | *"I couldn't read it"* — nothing came to mind about how to interpret this | *"I understood you; nothing came to mind"* |
| `out_of_fuel` | *"I gave up trying to read it"* | *"I understood you; I couldn't work it out"* |

Read off chain position, with no new mechanism. Note what this does **not** need: no distinguished
interpretation goal, no comprehension flag, and no positive *"understood"* fact — comprehension succeeded iff the
first goal advanced at all. And the system never concludes an utterance is *meaningless*, only that it could not
read it — the same weak, honest claim as `starved` ≠ underivable.

⚠ Leaning on fuel for *"couldn't work it out"* is one step away from the conflation this section exists to
prevent. It stays clean only while `out_of_fuel` is reported as budget exhaustion and never collapses into a
negative answer: the surface must say *"I couldn't work it out"*, never *"no."*

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

### The boundary transcribes; it never interprets

An LLM translates prose into the CNL, which is unambiguous by construction. The boundary then does as close to
nothing as possible: it **transcribes** CNL into graph structure and mints a goal. Every interpretive judgement
— what this utterance is *about*, whether it asserts or asks or commands, where one statement ends, what refers
to what — happens **inside the loop, as rules.**

> **There is no interpretation stage.** Wherever a seam is placed it becomes brittle and stops composing, so it
> is placed nowhere.

The engine trusts the grammar, and that trust is about *syntax fidelity only*: statement extent is marked in the
CNL surface, and the boundary carries those marks across as ordinary graph data without knowing what they mean.
Rules decide that.

**Four things this buys:**

- **Interpretation is revisable.** A seam commits irrevocably before any reasoning has happened. As rules, a
  mis-parse or a wrong boundary or a wrong scope can be reconsidered by a later step — it is data, and deletions
  apply at write-back (below). This is the endpoint of the surface/interpretation split: structure immutable,
  judgements discardable, contradiction → re-interpret without re-reading.
- **Interpretation composes.** Hypothetical, attributed (*"Paul says X"*), graded (*"probably he means…"*), and
  attention-dependent interpretation are all free, because none of it is a pipeline stage that must be taught
  about hypotheses.
- **Force stops being a router.** Assertion, question, command, authoring, retraction are conclusions rules
  reach, not branches a dispatcher takes.
- **It is learnable.** Interpretation expressed as rules can be authored and revised in-language. A seam in
  Python cannot.

**The seam shrinks but does not reach zero.** Three things cannot move inside, and naming them keeps them from
reappearing informally:

1. **transcription** — CNL text → graph, mechanical, no judgement;
2. **minting the goal** — something outside must create the thing that makes the loop run;
3. **the actual reads and writes** to the outside world.

One function, one node, and an I/O edge. Everything else moves in.

**Two costs.** Comprehension is no longer free — understanding an utterance costs many steps of the expensive
loop, which is where performance pressure will land first. And it depends on linguistic competence being
attended when almost nothing is (§7).

⚠ **`ugm`'s intake routing does not carry over — it *is* the seam.** What survives is thinner: the refusal
discipline (now the translator's honesty, since a well-formed but wrongly-bounded translation is worse than a
refusal — it is silently confident), and forms-as-data, which stops being one feature and becomes the whole
game.

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

Conclusions **and derivations** are written back — and so are **deletions**. A unit may conclude that something
should be removed; that conclusion is an ordinary value that travels to the boundary and is applied there. Two
consequences worth having explicit:

- **The circuit never mutates the store.** A deletion is a *proposal* on a wire, applied at write-back, so
  nothing inside a step reasons over a store that changes under it.
- **A deletion is invisible within its own step.** The step that concluded it still sees the old data; the
  *next* step sees it gone. Which also means contradiction handling is **authored**, not engine policy: a rule
  concludes that the stale age fact should go, exactly as a rule concludes anything else. (This settles
  `decisions/0032`.)

Persisting the derivation is what lets the circuit be thrown away — it is the thing that makes a turn stateless. It also means provenance is **ordinary data**: rules can
match on it, so the system reasons about its own reasoning with no new mechanism, no separate provenance
channel, and no stratification discipline. Nothing prevents a rule from reading derivations of rules reading
derivations — which is the author's problem, not the engine's (§11).

---

## 10. Walkthrough: one goal, comprehension to answer

A small case, end to end, to show how the pieces move together. Note where the **turn** boundaries fall — they
are not the same as step boundaries, and that is the point.

> **Utterance:** *"Should Paul get the loyalty discount?"*

An LLM turns that into CNL; the boundary transcribes it into graph structure and mints one goal — *make sense of
this*. It interprets nothing (§9).

---

### Step 0 — comprehension is steps too

**Retrieve.** Attention holds only the transcribed utterance and the fresh goal, so the always-attended
interpretation rules are what come to mind (§7).

**Run.** Over one or more steps, rules conclude what the utterance is doing: it *asks*; it concerns a person
named Paul; the thing asked is about discount eligibility. A fresh mention node is minted for Paul with
`name = "Paul"` — whether it is *the real Paul* is not decided yet, and a rule will decide it, gradedly, and can
be wrong.

**Write back.** A **subgoal** whose satisfaction condition is *a fact about this Paul-node stating discount
eligibility, or its denial.*

**Outcome:** `satisfied` on the first goal. Note there is no *understood* flag anywhere — comprehension
succeeded because the first goal advanced and produced a subgoal. Had nothing come to mind here, the first goal
would have `starved`, and that is what *"I couldn't read it"* is (§8).

Everything from here is the same loop; only the goal is different.

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

**The front end is a controlled natural language, and the boundary is shallow.** An LLM handles construction and
ambiguity, producing CNL that is unambiguous by construction; the boundary transcribes and interprets nothing
(§9). This division is what makes parsing-as-rules viable — the in-loop grammar only ever parses an unambiguous
language, so the coverage wall that stopped `ugm`'s grammar (real prose at 0/50, the gap ~100% constructional)
is not in the way.

**The front end targets data, never an engine API** — otherwise the system can *say* things it cannot *learn*.
So a statement's **chain and markers are described in the data**, and the assembler only wires what is
described. If the assembler had to *unroll* a statement it would have to know what statements are, and the
outer driver would be doing semantics on day one. The price is that the seal is the only thing making a
statement atomic.

**The CNL grants the shortcut the engine refuses.** Nothing matches by name implicitly (§4), so a rule about
destinations must explicitly match `name = "destination"` — intolerable to write by hand. Role names are
therefore a *surface convention* the grammar expands into explicit matching. The privileged treatment lives in
the front end, where it is inspectable and replaceable, and never in the matcher.

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
5. **Every goal worked on in a step receives exactly one positive outcome fact.** Per goal, not per step, and
   never an absence.
6. **The boundary interprets nothing.** Transcription, minting a goal, and I/O only — every judgement is a rule.
7. **Nothing matches by name unless a rule says so** — `name` has no privileged status anywhere in the engine.
8. **A turn is *resumable* from persisted data alone — not reproducible.** No hidden in-memory state may be
   load-bearing. But re-running a turn need not reach the same place, because System 1 is non-deterministic
   (§7). The test is that work can *continue*, never that it replays identically.
9. **Only end markers are attachable.** No wire terminates inside a sealed span.
10. `units/` imports nothing from `ugm/`.

---

## 13. Open questions

Genuinely undecided, not oversights.

- **The retrieval mechanism, concretely.** Settled in *kind*: associative, non-deterministic, no completeness
  guarantee (§7). Still open in *choice* — subgraph similarity, activation spreading from the goal's nodes, or
  something learned. And whether the similarity function is authored data like every other similarity
  judgement, or the one thing the engine fixes.
- **What a step costs.** Fuel bounds a circuit's run, but the unit of account is undecided: unit firings,
  values produced, or something else.
- **The CNL surface itself.** Settled: the boundary transcribes, rules interpret, statement extent is marked in
  the surface, and the translator must be able to refuse (§9, §11). Undecided: what the surface actually looks
  like — how a statement is delimited, how nesting is written, how a rule is expressed as data, and how much of
  the graph the transcription commits to. This is the next design conversation.
- **What comprehension costs.** Every utterance now takes many steps of the expensive loop before any domain
  reasoning starts. Acceptable in principle; unmeasured in practice, and the first place performance pressure
  will land.
- **Self-reinforcing recall.** Retrieval that surfaces what resembles what is already attended will keep
  confirming itself, and attention narrowing onto its own output is a failure mode with a human analogue.
  Decay, deliberate diversity in recall, or something else — undecided. This is the unresolved half of the
  `ugm` auto-fire finding (§7).
- **Retention, and the growth of the twin.** The circuit is discarded each step, so there is nothing to collect
  there — but the graph grows monotonically, since every step writes conclusions *and* derivations. Attention
  does not answer this: it governs what you *look at*, not what you *keep*. An agent that must explain itself
  next week cannot discard provenance; one that runs for a year cannot keep all of it. `ugm`'s
  focus-reachability GC does not transfer.
- **Whether in-circuit cycles are needed at all.** See §5. If the tight outer loop supplies all iteration that
  requires new data, the only cycles left inside walk a fixed structure to a known end — and latching stops
  being load-bearing.
- **Role node sharing.** Role nodes are per-occurrence and match by declared name-equality. Is that equality
  rule loaded once as ordinary KB data, or restated per rule? The first risks becoming a de-facto vocabulary
  through the back door.
- **The outer budget's shape.** Steps, wall clock, or something the goal itself carries.
- **Homoiconicity.** Deliberately deferred. The computation network may itself be a graph (hyperedge with begin
  and end marker nodes), which makes it tempting; not yet.

---

## What carries over from `ugm`

The top-level shape here converged back onto `ugm` — one persistent graph, goals driving demand, a CNL front end
targeting data, suspend for external calls, provenance and fuel as data, bands, write-back. That convergence
re-derived itself from first principles without being steered for, which is evidence the top level was right the
first time. **What was wrong was one layer down.** Four differences, and they are not equal:

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
| RECALL | *becomes* System 1; the explicit-only ban lifts, for the reason in §7 |
| intake routing (assert / ask / author / command) | **does not carry over — it *is* the seam** (§9). Force becomes a conclusion rules reach |
| refusal discipline / nearest-forms rejection | survives as *design*, relocated to the translator's honesty |
| homoiconic grammar spike (token-passing ≡ chart parsing) | **becomes load-bearing** — it is the evidence that parsing-as-rules works |
| suspend + call | survives, simplified to a gate that hasn't been filled plus a pending demand |
| fuel / budget | survives, and gains a sibling: the outer budget (§8) |
| band lattice + θ | survives, and moves *into* matching rather than sitting alongside it |
| provenance | survives as ordinary data; **stratification is dropped** (§9) |
| coref as declared rules | survives, and gets easier — graded matching is what it always wanted |
| forms / rules as data | survives, and is what the CNL emits |
| reconsider (revising stale NAF conclusions) | **largely absorbed** — every step re-retrieves and write-back can delete, so a special mechanism becomes the outer loop |
| focus-reachability GC | **does not transfer** — see retention, §13 |
| the central matcher / demand chain | **replaced** — this is the flip |

**And the failure mode migrates rather than vanishing.** `ugm` died of every rule juggling scope. Here the
*assembler* owns nesting → tunnel → nesting. That is one place instead of every rule — a real reduction — but it
is the same class of bug relocated, which is why it is invariant 2 (§12).

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

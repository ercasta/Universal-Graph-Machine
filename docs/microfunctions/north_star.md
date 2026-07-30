# The north star, repointed — content as data, mechanism as mini-algorithms

**Status: north star, 2026-07-30. Supersedes the "everything is a rule" reading of `model.md` and
`metaprocedure_model.md` §1b. Written in prose, per this project's standing preference.** The evidence for
the repoint is in `units/mini_algorithm_comparison_experiment.py` (run, three results) and in the three
probes recorded at `graph_data_model.md` §7. Read `the_data_model.md` first — it supplies this document's
entire substance, and survives the repoint essentially unchanged, which is itself the main argument that
the repoint is safe.

---

## 1. The sentence this whole document exists to correct

The bet was always **content as data** — business rules, goals, plans, hypotheses, explanations, all
represented uniformly in one graph, so that anything can be reasoned about, including another rule.

The bet was never **pattern-matching as the execution model**.

Those two got welded together early and stayed welded, and essentially all of the accidental complexity
this project has fought with comes from the weld rather than from either half. Separating them changes
almost nothing about what the system represents, and changes almost everything about how it computes.

---

## 2. Why now — the evidence, not the intuition

Three independent lines converged in one session.

**The arc kept dissolving its own primitives.** Causation turned out to be ordinary content plus a generic
schema. So did force, level, quantification's open case, and four of five relational forms. The "closed
class" shrank under challenge until it was conjunctive matching, negation-as-failure, a band lattice and
five effects. A vocabulary that keeps shrinking every time it is tested is not the thing carrying the
weight.

**The formalization found the machinery already built.** Writing down the data model showed fourteen of
fifteen operations already existed, and that the one genuinely missing piece — a node recording that an
operation was applied — needed no engine work at all. The two probes that closed it used `Emit`, `Link`,
and two `absent(...)` guards. Very little matching was doing very much work.

**And the recurring lessons were all about the formalism, never the domain.** The reflective-axiom
lifecycle, closure-before-NAC, wire-every-source, two-sources-on-one-gate-silently-overwriting — every one
is a fight with the rule machinery. Both corrections the episode-compilation probe needed were formalism
artifacts: applications had no inherent order because rules in one settle do not fire in sequence, and
compilation minted ten procedures instead of one because `Emit` mints fresh per firing. A `for` loop has
ordering for free, and a function that checks whether something exists yet is one line.

Rewriting that probe's compile step as an ordinary function produced **identical data**, needed **zero**
NAC guards, and made the externally-stamped turn ordering unnecessary. That is the whole argument, and it
is measured rather than argued.

---

## 3. The shape, stated plainly

**Two layers, and only two.**

**The graph holds everything the system reasons about.** Business content, goals, plans, procedures,
questions, prohibitions, hypotheses, explanations, records of the system's own reasoning steps, and —
critically, unchanged — *rules themselves, as data*. `the_data_model.md` describes this layer in full and
needs no revision: the concepts, their parts, their lifecycles, and the closure property that lets them
nest without limit are all properties of the representation, not of the execution model. Its operation
catalogue survives verbatim too; only the sentence "an operation is a generic metarule" becomes "an
operation is a mini-algorithm."

**Mini-algorithms read and write that graph.** Ordinary code — the layer the ISA and firmware were always
meant to be. They compose by being called. They communicate *only* through the graph, never by calling
into each other's internals, which is the discipline this project already states in the dispatcher's own
documentation (a rule never calls a tool; they couple only through nodes) and which the
entity-component-system pattern arrived at independently. The data model is therefore not a nice-to-have
under this repoint. It is the *interface*, and it is load-bearing in a way it never quite was before.

**What this preserves, and it is the part worth protecting.** Homoiconicity is untouched. A mini-algorithm
can read rule-shaped data and write rule-shaped data — more easily than a rule can, not less. The thing
that distinguishes this project from the goal-and-plan architectures that preceded it (Soar, ACT-R, and the
game-AI lineage that shipped them commercially) is that behaviour and world live in *one* representation,
so behaviour can be reasoned about and generated. Nothing here touches that. If anything the repoint
sharpens it, because the claim is no longer entangled with a matching engine that was never what made it
true.

---

## 4. Hypothetical reasoning — the objection, and why it does not hold

The strongest argument against this repoint was made twice, deliberately, in `metaprocedure_model.md` §1b:
mechanism that derives reasoned-over state must stay a *declared rule*, because `suppose()` and `chain_sip`
can reason **through** declared structure but never through an opaque function call. Move readiness into
Python and you lose the ability to ask "would this step become ready if the door were locked."

This is wrong, and the error is a hidden assumption: that answering a hypothetical requires walking the
derivation *symbolically*. It does not. **Run the mini-algorithm on hypothetical data and read the answer
off.** Checked directly at the time: a counterfactual ("what if this goal had *not* been achieved")
produced the correct different answer, with real belief unchanged.

Executing on hypothetical data is strictly cheaper than reasoning symbolically about execution, and it is
also more honest, since it answers with what the code would actually do rather than with what a declared
approximation of the code says it would do. §1b defended a real capability by the wrong means.

**⚠ Corrected later the same day — the argument stands, the mechanism it proposed does not.** This section
originally concluded "pen the assumption into a *scratch graph*," which belonged to the copy-on-write
substrate that no longer exists. What replaced it is smaller: **a hypothesis is an ordinary node**, and the
"hypothetical data" a mini-algorithm runs against is an ordinary subgraph hanging off it (§5c's variants,
plus explicit backup nodes where a prior value must be recoverable). No scratch graph, no scope, no
copying the world to ask a question.

The undo journal in `microfunctions/graph.py` is **not** this mechanism and must not be mistaken for it.
Its only job is transactional — a program that raises halfway leaves no half-written graph — its unit is a
single failed run, and **a rollback boundary must never span a dispatch**, because a tool call has already
escaped and no journal reaches it. Hypotheses outlive calls, must be comparable side by side, and must
reach verdicts rules can read; rollback can do none of that, and two nodes can do all of it.

---

## 5. Triggers — the one thing genuinely lost, and how to get it back cheaply

Under ambient rule matching, a standing rule fires whenever the world happens to match it, with nothing
scheduling it. That is how a prohibition recorded *before* a command still blocks that command, and it is
how a watchdog works without anybody wiring it to what it watches. Mini-algorithms do not have this for
free: a function that is never called never runs. This is the real cost of the repoint and it should not be
minimised.

It is, however, a well-solved problem, and the database precedent is the right one — but only if one
distinction is kept sharp, because it is the distinction ambient matching blurs and the reason ambient
matching is expensive.

**Write-triggered, not state-triggered.** A database trigger fires on a *mutation* — an insert, an update,
a delete — at a defined point, synchronously, and may abort the transaction. It does not continuously
evaluate a predicate over the whole table hoping to notice something. Ambient rule matching is the second
thing, which is why it costs a fixpoint loop and why "did this rule already fire for this reason" becomes a
recurring correctness problem rather than a non-question.

For the case that actually motivates triggers here — **intercepting dangerous behaviour** — write-triggering
is not a compromise, it is the correct model. You want to catch the *act*, not a state. And the interception
point already exists and is already singular: the dispatcher is the one place in the entire system where a
proposal becomes a real effect, and its content-blind servicing loop is precisely a `BEFORE` trigger's
position. `metaprocedure_model.md` §4 already proposed exactly this under the name Gap A, for reasons that
had nothing to do with this repoint — which is a good sign. One check, at one choke point, consulting
graph-resident veto data, covers every action that will ever be dispatched, including ones authored later
by rules that never heard of the prohibition.

So the honest accounting is:

- **Guarding an action** — a trigger at the dispatcher. Cheap, singular, and already designed. This covers
  the dangerous-behaviour case entirely.
- **Guarding a state transition** — triggers at the small, fixed set of points where the graph is written
  by mechanism. Ordinary, and the same shape.
- **Noticing a state that no write announced** — genuinely needs a scheduled sweep, because nothing
  happened for a trigger to fire on. This is the residue, it is real, and it is also the case ambient
  matching was quietly paying a fixpoint for on every turn. A sweep makes the cost explicit and
  schedulable instead of ambient. Note this project had already been walking this way on its own:
  reactivity is lazy by default with per-predicate opt-in, and the scheduler was already conceded to be
  correctly Python.

The expectation, stated so it can be wrong: triggers should be a small amount of ordinary machinery with no
surprises, and the surprises — if any — will be about *ordering* (which trigger runs first when two apply)
rather than about mechanism. That is the same arbitration question that is already open and already
unsolved, so it should be tracked there rather than counted as a new problem.

### 5b. Probed, 2026-07-30 — `units/trigger_probe_experiment.py`, and §5 holds as stated

Written as ordinary functions over the graph — no `StandingUnit`, no matching, no settle loop — because
that is precisely what was under test. Five checks:

* **A dangerous action is vetoed at the choke point.** Executed 0, blocked 1.
* **⭐ A prohibition recorded *after* the proposal was minted still blocks it.** This was the decisive
  check — the order-independence ambient matching gave away free, and the property most likely to be
  quietly lost when moving to called code. It holds, and the reason is precise enough to be worth stating
  as a rule for the implementation: **the check must happen at APPLY time, not at MINT time.** A
  proposal is inert data until the executor reaches it, so anything recorded in between counts. Had the
  check been done when the proposal was created, this would have failed.
* **Completed work is not retroactively undone.** The first action executed before the prohibition existed
  and stayed done; the second was blocked. The gate stops the next act and never reaches back.
* **A later-authored action cannot bypass the gate.** A proposal minted by a function written in deliberate
  ignorance of prohibitions was still blocked, because there is structurally one executor. This is the
  argument for a choke point over per-caller checks, and it is now tested rather than asserted.
* **The residue is real, and was demonstrated rather than reasoned about.** A danger that became true with
  no proposal pending was *not* caught by the trigger — nothing fired because nothing happened — and *was*
  found by a scheduled sweep. Write-triggering is complete for guarding acts and structurally cannot cover
  states nothing announced.

⚠ Two checks initially reported the wrong thing because of a defect in the probe itself (a
`with_prohibition_on=None` parameter tested with `is not None`, so passing `False` still installed the
prohibition). Caught because a check that had to be true came back false. Recorded because it is the third
false-or-wrong green in one day's probing, and the pattern is now worth naming as a discipline: **for every
green, ask what would make it vacuous.**

---

## 5c. Microfunctions — the further step, probed 2026-07-30

Raised immediately after §5 and pushed further than the repoint itself: instead of rules with a left- and
right-hand side, have **microfunctions** — ordinary functions taking subgraphs as parameters, where a
*type* is a subgraph schema (a `car` is a chunk with a body and four wheels). A microfunction is *pointed
at* its arguments rather than firing wherever the world happens to match, so wrong firing becomes
structurally impossible. An LLM at the boundary translates natural language into microfunction calls.

Built as `units/microfunction_probe_experiment.py`, five checks, all holding. The findings, in the order
they matter:

**Matching does not disappear — it is demoted, and that is the actual win.** Checking "is this subgraph a
car" *is* a graph pattern match. But it moves from **dispatch** (unbounded, fixpoint-driven, tangled with
NAC and ordering) to **validation** (one known argument, one known call site, bounded, no fixpoint). This
should be stated precisely so nobody later claims matching was eliminated. Established prior art sits
exactly here: SHACL is "a shape a subgraph must satisfy," and Minsky's frames are stereotyped situations
with slots — a car with a body and four wheels is a frame.

**A type is ordinary graph data.** Declared as a node with one `requires` edge per part, read back by an
ordinary function. If types were Python classes the homoiconicity claim would be lost at exactly the point
it matters most; they are not, so a KB can author a type and a microfunction can read one.

**Malformed arguments are refused loudly at the boundary.** A three-wheeled chunk is not a `car` and the
microfunction raises rather than half-executing, reporting expected-versus-actual. This is the same
loud-refusal discipline the rule compiler already applies to a malformed fragment.

**Wrong firing is eliminated — with the caveat that the interesting half of this result is on the rule
side.** Two structurally identical cars; the microfunction pointed at one touched exactly one, which is
close to definitional. The content is the contrast, run in the same graph: the rule-shaped equivalent
touched **both**, because a pattern structurally cannot express "this one." That is the defect class being
removed, demonstrated rather than asserted.

**Microfunctions return a graph rather than mutating one.** Arguments-by-reference would reintroduce
aliasing the rule model never had; returning a graph keeps pencil and ink separate and keeps §4's
hypothesis-by-running available. Verified: the caller's graph is unchanged, the returned one carries the
effect.

**The honest residue, and it is the load-bearing consequence.** With no matching to decide what applies,
*something* must choose both the microfunction and its argument. Typing narrows the candidate set — two
well-typed cars — but does not pick one. **Selection therefore stops being an optimisation and becomes the
only control mechanism there is.** That raises the stakes on the application-node layer (§6.3 of
`graph_data_model.md`, Probes B and C) from "unlocks learning" to "is the control flow," and it needs an
index of which microfunctions could apply to a chunk, which is precisely the associative-retrieval step
`system1_experiment.py` already prototypes. Note GOAP has this same problem and answers it by matching
preconditions against state — so retrieval, not matching, is what actually gets deleted here.

**One practical rule that follows.** Do not search for chunks. "Find the car in this graph" is subgraph
isomorphism in the general case; instead **chunk once at recognition and materialise the chunk as a node**
pointing at its parts, so downstream every reference is a pointer rather than a search. This is where an
LLM at the boundary earns its place, and it is consistent with the parts-as-separate-nodes discipline and
with interning.

---

## 6. What is cut, and what that is worth

The repoint removes the justification for a substantial amount of machinery, and the honest position is
that removal should be *earned per item*, not assumed wholesale. The candidates, each of which needs its
own check before deletion: skolem constants, ATMS environment-consistency across forks, stratification,
theta-gated negation-as-failure, the possibilistic band layer, and demand-driven selection propagation.

Two independent reasons to expect most of these to go. First, they are where the still-open gaps are —
including one verified unsound false positive — so they are costing correctness, not merely code. Second,
and more fundamentally: most of that machinery exists because classical symbolic AI *had no statistical
model*. Bands, defeasible defaults, and elaborate negation stances are all ways of handling ambiguity and
uncertainty symbolically because in 1985 there was no alternative. This project has already committed to a
language model absorbing open-class content. A large fraction of that machinery is therefore solving a
problem that has already been outsourced, and keeping it means paying twice.

The immediate next step is not deletion. It is the audit: take the ten scenarios in
`agentic_scenario_catalog.md` and ask, per scenario, which of those mechanisms it *actually requires*. The
prediction is few to none, and where one seems required, the real requirement will turn out to be a
language-model judgement. That is a cheap, decisive check and it is the same probe-first discipline that
has correctly weakened every claim this session made.

---

## 7. What this does not change

Worth stating explicitly, because a repoint invites over-correction.

The data model stands entirely. The concept vocabulary, the operations, the closure property, and the three
probes' results are all properties of the representation and survive untouched. Goals are still nodes
pointing at claims they want true, resolved by positive marks. A question is still a goal. A learned
procedure is still a procedure whose steps are reasoning operations. The single missing piece is still a
node recording that an operation was applied, and it is still the thing that unlocks selection, lookahead,
episodes and learning.

Termination and conflict arbitration remain open, unchanged and unsolved by anything here. Both are real,
both are separate from this repoint, and the second is the one that will most likely bite first, because
triggers make it concrete.

And the bet is unchanged: one representation for behaviour and world, so a rule can write a rule. That was
always the claim worth defending. What this document does is stop defending it with machinery that was
never what made it true.

# Limits

This page is the honest account of what the machine does not do. It is kept deliberately, because a
system that reasons about itself is exactly the kind that can produce a confident answer where it
should have produced none.

Three kinds of limit are distinguished, because they call for different responses:

* **Known weaknesses** — things that work but not well, where the shape of the better version is
  understood.
* **Capability gaps** — things that cannot be *said*, because no arrangement of what exists
  represents them.
* **Modelling gaps** — things that parse and run and mean the wrong thing, which is the dangerous
  class.

## Known weaknesses

**The planner** is depth-limited best-first, first solution wins. There is no cost model and no
backtracking across a committed subgoal. It is adequate for chains of a handful of steps, which is
the size this system is built for, and it should not be mistaken for a general-purpose planner.

**Copy cost.** A workbench copies everything reachable from the subject, once per frame.
Copy-on-write implements exactly these semantics more cheaply and is the known lever; it is
deliberately not taken until the cost is measured to matter.

**Search is tie-break nondeterministic.** The plan found is invariant; the number of states imagined
to find it is not. Any deterministic computation that ends in a `set` has an undeclared tie-break in
it, which is worth remembering before reading too much into a state count.

**Type schemas constrain one argument at one call site**, so `stack(b, onto)` cannot declare that its
two arguments differ. The planner enforces that itself. Schemas are no longer one level deep —
requirements recurse and two places inside a subgraph can be related — but the one-call-site limit
stands.

**References reach any depth in a `type` block and one hop in a `goal` or `method` one.** This is not
an omission. Conflict detection keys a slot by *(subject, key)*, and goal satisfaction reads the
attribute off the base node, so a navigated subject would be silently mishandled. It is refused
loudly at intake until those understand a path.

**Episode compilation** generalises a sequence of single-argument operations on one subject.
Multi-argument replay is a real question about *analogy* — how a replay maps old bindings to new —
not a missing mechanism.

**No indexing** beyond the maintained reverse index. Enumerating a type's instances is a whole-graph
scan and exists only to seed a candidate list.

**Termination is unsolved.** A runaway program raises at a step limit rather than truncating
silently, which is an honest stand-in rather than an answer.

**Conflict arbitration** reports disagreements; it does not resolve them, except where norms declare
an authority ordering.

**Nothing forks on mock outcomes during pursuit** — it takes the preferred one — so a plan produced
by pursuit has no sibling branches, and recovery cannot offer a contingency for one. The loop leans
on replanning instead. Relatedly, nothing prevents a caller from forking every outcome of every
uncertain call: three calls with three outcomes each is twenty-seven plans, and the discipline
(branch only where being wrong is expensive) is a discipline rather than an enforced rule.

**A re-proposal is not rehearsed.** Replanning returns a chain, and nothing runs that chain on a
workbench first, so it is unverified where the original plan was verified. The blocker is real rather
than missing code: turning a chain into workbench steps needs a rule binding each pending call's
output to a mapping, and for a call that mints something, that is the same open question as episode
compilation. A guessed binding would produce a plan that merely *looks* rehearsed.

**A mistyped action name in a `never` or `must` line** is accepted and silently constrains nothing,
unlike a mistyped *thing* name, which is refused. Failing loudly is the intended fix.

**Where several matching branches or several leaves exist**, recovery takes the first, matching the
planner's first-solution-wins discipline rather than pretending to choose.

## Capability gaps — what cannot be said

Several things that look like gaps are not. Universal quantification over a named edge, cardinality
and emptiness, comparing two named individuals, "if X then Y" on the action side, and threshold-style
preference are all expressible today, sometimes awkwardly. What follows is measured to be genuinely
absent.

### There is *act* and *check*, and no notion of *find*

This is the root of most of the rest. The engine models **acting** — a function whose body changes
the world, read off its instructions — and **checking** — a type, a constraint, a predicate. *Finding*
— an operation whose whole point is to yield a **referent** rather than to make something true — has
no slot in either.

The computation is not missing. A stored program can loop over a directory's files and return the
newest, or mint a selection node and link members into it, and both are provably pure, so a question
may run them. Two other things are missing, and both follow from one cause:

* **A finder is invisible to the planner, and confidently so.** Reading such a body reports that it
  makes nothing true — correct and useless, because a proposal is scored by what it would make true.
  A function that writes nothing can never be proposed as a step toward anything.
* **The surface cannot name what such a program yields.** `newest(d).measured = true`, *the newest
  one*, and a rule body naming a finder are all refused. The machine exists and nothing can point at
  its result.

`find` also sits astride the look/act boundary, which is why it cannot simply be a helper. *Which
file is newest* is answerable from the graph only if the files have been observed; otherwise it is a
question about the disk, and answering it means planning a look. So a finder is sometimes pure and
computable during planning and sometimes a step that must itself be planned, and nothing today
distinguishes the two.

### No way to describe rather than name

Everything the surface can refer to is either a named individual or one node reached by a fixed path.
There is no form for *the files bigger than 1k*, *the newest one*, *the first three*. Superlatives
are the sharpest case: any paraphrase has to name the population inside the demand, and neither a
schema nor a relation between two places inside one can say *and no other*.

This is about **denotation**, not quantification — universal quantification over a bounded named edge
already works. What is missing is the ability to denote a set so that something can be said about it,
chosen from it, or done to each of it. It is the most connected gap on this page: *all the files*,
*the newest*, *the three biggest*, *most of them*, *total size*, *the second one* are all downstream
of it.

### Disjunction

*Either A or B is gone*; *it is a file or a directory*. There is no disjunctive constraint in a goal
and no disjunction in a schema. The nearest available form is a different claim, which is the kind of
near-miss that must not pass as a paraphrase.

The asymmetry is what makes this a real hole rather than an oversight: alternatives exist everywhere
in *plans* — workbench forks, sibling branches, mock outcomes, resumption — and nowhere in
*statements*. The engine can pursue either route and cannot say either fact.

A machine could check a disjunction; means–ends needs to know *which disjunct is open*, the way unmet
constraints do, so closing this needs a report of the right shape rather than a predicate.

### Maintenance

*Keep the directory empty*; *never let the queue exceed ten*; *stay logged in*. Every goal is an
**achievement** goal: unmet constraints are a snapshot, closing records that something became true,
and a closed goal is never reopened. The achievement form parses; the maintenance form has no
expression at all.

This is not the same as a plan constraint, which constrains the route to an achievement; a
maintenance goal constrains the world after arrival, indefinitely. It is also the gap most likely to
be needed by an agent watching something, and the one that would give the slower clock something to
schedule.

### Conditional goals

*If the disk is full, then the log is rotated.* A method guard conditions what to **do**; nothing
conditions what must be **true**.

### Past states of anything but observed attributes

The world graph is a single mutable state. Frames and workbenches are for imagined futures, not
recorded pasts, and observation records sightings of attributes only. So *what did the directory
contain last week*, *was it ever a symlink*, and *undo what you did at step 3* have no
representation. Counterfactuals about the past are downstream of this rather than separate.

### Degree, and belief that is not binary

*Probably*; *almost empty*; *much bigger*. A hypothesis is a node and an outcome is an assumption,
both binary. The old engine's possibilistic layer was deleted deliberately and nothing replaced it,
which is defensible — but it means every hedged statement is currently either dropped or promoted to
certainty, and dropping and promoting are very different errors.

Unlike the gaps above, this one is not machine-closable: nothing derives *probably* from a graph with
no place to record it.

### Beliefs held by someone else

Discourse records who said what, and a norm records its source, so the *provenance of an utterance*
is representable. Agent-indexed **belief** is not: *John thinks the file is missing* has nowhere to
live, and there is nothing to compute it from.

### Aggregation over a population

*Total size*, *the average*, *how many are there*. Counting one edge label exists, accumulation
exists (see below), and a stored program can iterate, so a rule can compute these. What is missing is
any way for a goal or a question to **speak** of them — which is the denotation gap again.

### Arithmetic beyond accumulation — decided, not missing

`ADD` is the only arithmetic opcode. There is no `SUB` and no `MUL`, and this is a decision rather
than where the work stopped: **computing a quantity is a tool's job.** A price, a fee, a spread, a
margin, a position value — the tool computes it and writes the result as a slot, and the instruction
set only accumulates what the world has already handed it. The alternative is an opcode table that
grows once per domain that needs a different sum, which is how a closed set stops being one.

This is a live constraint on how a numeric domain is modelled, so the two consequences are worth
stating plainly.

**Subtraction is expressible only as the addition of a negative the graph already holds.** A negative
*literal* works — `CONST R(x) -140` then `ADD` — but nothing negates a value read out of the world,
so `cash -= ask`, where the ask is a slot, cannot be written. The modelling answer is that the
observing tool writes the signed delta it caused (`cash_delta = -140`) rather than the magnitude, and
the body adds it. That is not a workaround: a tool that knows what a trade costs is the thing that
knows its sign.

**A mock can only predict a numeric effect in terms of a delta already on the graph.** Planning is
structurally incapable of dispatch — `dispatch.service` refuses an imagined target, deliberately and
for the most important safety reason in the design — so a quantity that only a tool can compute has
no value during planning. Where the delta was observed before the plan was made, the mock predicts it
and divergence on the quantity is checkable as usual. Where it was not, the mock cannot state the
number, and the effect is checkable only after the fact. `position_value = count × price` is the
plain case: it is computable by a tool, and not predictable by a mock.

A `NATIVE` is *not* the escape hatch here. `native.py` is explicit that natives are substrate and
their contents must not be business, and domain arithmetic is business.

## Modelling gaps

The verdicts worth separating are: it does not parse; it parses but cannot execute; and — the
dangerous one, which has no common name — **it parses, runs, and means the wrong thing**. A refusal
is a good outcome. A confident wrong model is not.

The general findings that came out of cataloguing these are worth stating on their own, because they
predict where the next one will be:

* **A hardcoded mechanism is an unreachable island.** Wherever engine state lives in a Python
  structure, the system stops being able to compute about it, and every reflective capability fails
  exactly there.
* **An island is created by the second caller.** One hand-placed site is a line of code; two are a
  concern that should have been expressible.
* **Anything expressible is in scope.** The question is never *whether* something belongs, only
  *how* — and the how must be data, never Python, because a Python answer creates the next island.

## What is not verified

Verification is `python -m ugm.selftest`, which currently reports 221 checks with none failing. It is
a single runner rather than a test framework, and its checks are written as named observations so a
reader can see what was actually asserted. Two things follow.

**A green check is only as good as its guard.** Several checks in this suite were found to be vacuous
— passing no matter what the code did — and were fixed by planting a deliberate bug and confirming
the check went red. That practice is the reason to trust the rest, and any new check should earn its
place the same way.

**Performance is judged per utterance and per session**, not at scale. The system is session-sized by
design. No claim is made about large knowledge bases, and the absence of indexing is the honest
reason.

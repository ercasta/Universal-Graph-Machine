 I have two changes to propose, let's decide whether to do this now or later. One is syntactical: instead of rule <something>:, could we use rule(something,implies(...)) and rule(something,causes(...))? Same
  for actions: action(move(?x,?y)) where in this case ?x and ?y mean they will be bound at runtime. This would make everything be "facts". The second change is more significative. Right now we have some
  things automatically done by the engine like saving short term memory. What if we have multiple experts active in parallel, where "parallel" actually means there is an "outer loop" that make them act in a
  specific order; in particular we could have an "expert" dedicated to memorizing things, or do "accessory" work, with a separate "attention" table 

---

# Queued: retire situations, and manage hypotheses EXPLICITLY

Proposed 2026-08-20. Not started. Surveyed and measured below so that whoever
takes it starts from numbers rather than from the argument.

## The proposal

Reasoning about a scenario means **altering the actual graph**, consciously
knowing it is a hypothesis, manually mapping and storing the results and the
plan, and manually reverting the changes afterwards. The engine loses the
situation mechanism entirely: no branch per supposition, no per-situation
interning, no second identity on the node. Rules get stronger; the engine gets
much smaller.

## Why this looks right

**It is the move this repository keeps making and keeps being right about.**
Machinery that DECIDES becomes a fact a corpus reasons about. Situations are the
largest remaining piece of engine-that-decides, and 2026-08-20 retired `prefer`
and the buffs on exactly that argument.

**The dependency ratio is very favourable — engine-deep, user-shallow.**

    76 mentions of `situation` in `graph.py` alone (874 lines)
    plus per-situation interning, BOTH indices keyed by situation, two
    identities per node, `Machine.suppose`/`discharge`, `Graph.carry`,
    `Graph.branch(born=…)`, `Moment.watermark`, the situation register

...and standing on all of it:

    ugm/modality.py     one probe, and its own header says the question it was
                        built to answer has already been ANSWERED and acted on
    ugm/selftest.py     ~16 fixtures
    worked.ugm          one rule concluding `suppose(?p, likely)`
    bundle.ugm          the re-entry rules (`resume`)

No production module builds on suppositions.

**It fixes the leak the current design concedes and never fixed.** Measured, on
the three-rule fixture, leaving the hypothesis behind each time:

    supposition 1   graph 1505 -> 1679   (+174, kept for ever)
    supposition 2-5              (+95 each, kept for ever)
    visible from the caller afterwards: None    <- containment DOES hold

`docs/situations.md` predicts this in its own words -- *the graph is not
reconstructible from the deltas, so a materialisation cannot be discarded...
a long-running agent that supposes constantly accumulates them* -- and says the
fix is the replay stage, which is the one stage of four that was never built.
**An explicit revert IS that discard**, and it arrives without building replay.

**And *consciously knowing* is the strongest part of it.** `situations.md`
again, on the current design: *Today the seat is a register and nothing can
refer to it, which is why `p@current` would be unwritable.* The agent is
currently inside a hypothesis without being able to SAY that it is. Making the
hypothesis a thing the agent asserts, plans over and reverts is what lets it
answer *what would happen if we set fire to the house* as a REPORT rather than
as a side effect.

## DECIDED, 2026-08-20 — and it is smaller than the queue entry above assumed

The author's call, taken in three steps, each of which shrank the job:

    1. hypothetical reasoning is just the REGULAR GRAPH
    2. no mark/revert primitives -- reverting loses the conclusions too, and the
       conclusions are the point
    3. no branching or reverting in the CHAIN either

So this is a **deletion, not a rewrite**. Nothing replaces situations. An agent
reasons about a hypothesis by asserting it and letting the ordinary rules fire;
it knows the conclusions are hypothetical because it RECORDED that, not because
the engine hid them.

⚠ Do not re-derive `mark()`/`revert()` from the queue entry above. It was
considered and rejected for a stated reason: a conclusion written during the
hypothesis is inside the reverted region, so a revert throws away the answer it
was called to get.

### What this costs, measured rather than conceded

**Containment goes, and it is the current design's headline claim.**
`selftest.supposing` asserts *containment: nothing concluded inside is readable
as current belief* -- `symptom(pump7, restricted)` is `None` outside today. It
will hold. That check is inverted, not deleted, so the loss stays measurable.

⭐ **But the lifting objection does NOT apply, and that was worth checking.**
`suppose` exists because a generic lifting rule cannot cross rules that carry
variables. Measured, on the reified `<lift>` rule:

    generic <lift>, ground pipeline     likely(r(x))                     +
    generic <lift>, variable pipeline   likely(action(replace, pump7))   None

That would be fatal to a SCENARIO-RELATIVE replacement, which would need lifting
or per-rule scenario forms. It is irrelevant here: asserting into the real graph
means the ordinary rules fire unchanged, which is the whole appeal.

**97 `instances_of`/`instances_with` call sites** stop being scoped for free.
During a hypothesis they answer about the hypothetical world, which is intended.
It breaks only if something concurrent reads mid-hypothesis -- `probes/experts`,
`core/channels`.

### The inventory, measured

    core/graph.py    57 `situation` + 12 atom/carry/branch. TWELVE dicts keyed
                     by SituationId: _sit_parent, _sit_born, _sit_of, _vis,
                     _atom, _node_by_atom, _identity, _mentions, _interned,
                     _by_rel, _by_arg, _merged. Both indices lose a key
                     component; `_interned` becomes (rel, members).
                     Gone: branch, standing_in, _visible, visible, situation_of,
                     atom_of, node_of, identity_of, carry, rebuild.
    core/gate.py     20. Frame.situation/home and all three pin/restore blocks.
    core/machine.py  16. suppose, discharge, _hypothetical, _own_frame, _leave,
                     the situation register property.
    core/chain.py     4 + 6. ⭐ The chain goes LINEAR, so `at_or_after` collapses
                     to a depth comparison -- `resolve`'s own comment says *a
                     depth comparison cannot replace it once anything forks, and
                     supposing forks by construction.* Nothing forks now.
    selftest.py      73 `situation`, 42 `suppose(`, the whole `situations()`
                     group, and selftest.py:4024 which forks the chain ON PURPOSE.
    corpora          worked.ugm (one rule concluding `suppose`), bundle.ugm's
                     `resume` rules.

⭐⭐⭐ **`Frame` collapses to a singleton.** The engine creates exactly TWO
frames: the root register, and the supposition child. Remove suppositions and
`frame.parent`, `purpose`, `wrap`, `carried` have no second case. §18's call
stack is FACTS, not frames, so it is untouched -- check that before assuming
`Frame` can go entirely.

### Order, and there is no green state in the middle

The indices change key shape in one step or the engine does not run. This is one
large commit, not a staged landing. Do `graph` -> `gate` -> `chain` -> `machine`
-> `selftest` -> corpora, and expect red until the last of them.

## Probed 2026-08-20, on the CURRENT engine, with no changes to it

Four experiments. Everything below was run against `87beb46`; none of it needed
engine support, which is the point.

### 1. Anchors as ordinary nodes — WORKS, but costs every rule

Rules written relative to an anchor by binding: `{ +in(?w, reading(?p, low)) }
=> { +in(?w, symptom(?p, restricted)) }`.

    in(h1, action(replace, pump7))       +       the hypothesis concludes
    in(actual, action(replace, pump7))   None    <- containment, BY BINDING
    action(replace, pump7)               None    the bare form never appears

⭐ The containment CHECK is an ordinary premise. A rule gated on `+world(?w)`
acts in reality and declines in a hypothesis -- *what would happen if we set fire
to the house*, answered without burning it down, with no machinery.

⭐ Reality is an unprivileged anchor (`actual`). No special case.

⚠ **The lifting objection does not apply**, which was worth checking: the
generic reified `<lift>` rule handles a ground pipeline (`likely(r(x))` -> `+`)
and NOT a variable-carrying one (`likely(action(replace, pump7))` -> `None`).
That kills a lifting-based replacement; it says nothing against binding, because
`?w` is bound by ordinary matching.

⚠ **The cost is on EVERY rule**: every premise and conclusion wrapped in
`in(?w, ...)`, on 51 of the 72 authored rules. This is what the swap shape
below avoids, and why the swap shape supersedes it.

### 2. The bundle needs NO anchor — 21 of 72 rules unchanged

The shipped bundle works unchanged over an anchored domain:

    in(actual, boiling(kettle))               +
    pursued(in(actual, water(kettle)))        +     backward reading works
    fits(<pour>, in(actual, water(kettle)))   +     the rule-fitting reader works

Its rules are about the AGENT's machinery (`goal`, `pursued`, `fits`, `quiet`)
and take an anchored proposition as an ARGUMENT without needing anchoring.

### 3. Nesting — flat wins, then drop it

    flat `within(h2, h1)` + one generic <inherit> rule    WORKS
    nested term `in(h1, in(h2, p))`                       produces nothing

⭐ Nesting is ONE rule: `{ +within(?c,?p), +in(?p,?f) } => { +in(?c,?f) }`, and
`?f` binding a whole proposition is handled by the matcher.

⭐⭐⭐ **And use did not leak into mention.** `<inherit>`'s unconstrained `?f`
picked up exactly the four asserted facts and none of the rules' own MENTIONED
antecedent patterns. Anchored rules reify identically to plain ones.

⚠ But `<inherit>` copies eagerly, and measured it is DEARER than doing without:

                                     h1 concludes   entries   nodes
    no h1                                None         159      1600
    h1: only the delta                   None         160      1607
    h1: delta + <inherit>                  +          177      1750
    h1: context asserted BY HAND           +          167      1659

> **A hypothesis must be given its CONTEXT, not just its delta** -- and doing so
> by hand beats blanket inheritance, because the agent copies only what the
> hypothesis needs.

⚠⚠⚠ And the failure is SILENT: under-assembled context (`None`) is
indistinguishable from a genuine negative. Gate it -- *a rule that would have
applied but for premises absent here* is an ordinary aggregate, not machinery.

### 4. SWAP OUT / SWAP BACK — the shape to build, and it needs no rule rewriting

The author's design, and it supersedes anchors: mutate the REAL graph so
ordinary rules fire unchanged, and link individual deltas to the supposition so
reality can be swapped back in. Marked by `(moment, index into its delta)`.

    reality before               boiling = None
    inside the supposition       boiling = +
    after swapping back          boiling = -, heat = -, tap = + (untouched)
    4 deltas linked, 2 about the world

⚠⚠⚠ **Refraction bookkeeping SURVIVED the swap-back** -- `exercised(<boil>)`
and `spent(<boil>, premises(...))`. The agent then believes it already used the
rule on those premises, so **a hypothesis burns that rule's chance to act for
real.** This is the defect to design against.

⚠ **`boiling @peak` was not shown to survive as history.** Every write landed in
the same moment, so there was no past to read. Untested, not refuted -- it needs
the seat to advance between supposing and swapping back.

## THE THREE REFINEMENTS — the author's, and they resolve the above

**1. Refraction should leverage MATERIALISATION.** Materialise the rule
application in the graph instead of keeping separate bookkeeping, and refraction
becomes an ordinary graph check. The leak in experiment 4 then cannot happen:
there is no second kind of record to be left behind, so swapping back removes
the application like anything else. `exercised`/`spent` stop being a special
layer.

**2. Swapping back is SYMMETRIC: + and - return to None, not to -.** Restoring
reality must leave no scar. A proposition never considered and one considered
and rejected are different claims, and experiment 4 produced the second where it
owed the first -- `boiling` went `None` -> `+` -> `-`, and `-` is wrong.

⚠ This is a deliberate departure from *deniable, not forgotten*, scoped to
supposition deltas. The RECORD of what was supposed lives in the chain's
history; it must not live in current belief as a denial.

**3. No special `@` markers -- if everything is in the graph, reads are ordinary
graph readings.** The locus/`at`/`holds_at` apparatus stops being a second way
of asking. Check what this costs before cutting: §12's `at ?m`, `hindsight`, and
`chain`'s two-times (locus vs deposit) are the things it touches.

### What is GAINED, so it is not only a loss

The 95-nodes-per-supposition leak `docs/situations.md` concedes and never fixed
goes away, because there is no hypothesis to leak FROM. And `docs/situations.md`
itself becomes a historical document rather than a description of the engine --
move it, do not leave it describing a mechanism that is gone.

## Two things to design rather than discover

⚠⚠⚠ **Containment stops being structural and becomes a promise.** Today it is
by construction: 106 nodes minted inside the `supposing()` hypothesis, 0 visible
to the caller. Under the proposal containment is whatever the revert actually
does, and a botched revert leaves `burnt(house)` BELIEVED -- silent, and
belief-corrupting, which is the worst failure mode available here.

> The revert must be CHECKED, not trusted. The delta chain is reified, so *are
> we back where we started* is computable. One engine check that refuses to
> continue otherwise is a row, not a mechanism -- and it keeps the guarantee
> while still deleting the machinery.

⚠⚠⚠ **Negation-as-failure and counting are the sharp edge.** `situations.md` is
explicit that stratum-0 structure is where NAF, counting and the rules-as-facts
interpreter all live, and that today BOTH indices are keyed by situation so
aggregates are scoped for free. If a hypothesis mutates the real graph, every
`unsupported` / `blocked` / count asked during it answers about the mutated
world. That is CORRECT while the agent means to be hypothesising, and wrong the
moment anything concurrent reads -- `ugm/experts.py`, `ugm/channels.py`. Decide
it explicitly.

⚠ And sibling hypotheses become a STACK rather than a tree. `Graph.branch(born=…)`
branches from an arbitrary past commit today, and `situations()` checks two
siblings building `on(b, c)` independently. Comparing two scenarios becomes
do-A, record, revert, do-B, record, compare-the-records. Probably fine, arguably
more honest, but it is a real capability change and should be named as one.

## What to measure first

How many places actually read an AGGREGATE across a situation boundary. That
number decides how much of the second warning is theoretical.

## MEASURED 2026-08-20, on `5c0a92f` — and the second warning is almost entirely theoretical

Instrumented `Machine._root`/`_count`/`_supported`/`_verdict` and `Graph._bucket`,
then ran the whole suite. Nothing about the engine changed to take these.

### The aggregates: 15 of 271, and all of ONE kind

    ask          outside a hypothesis   inside one
    _count                6                  0
    _root                12                  0
    _supported            7                  0
    _verdict            231                 15

⭐⭐⭐ **The two the warning names -- counting and negation-as-failure -- never
run inside a hypothesis at all.** `count`, `root` and `support` are 25 asks and
every one of them is at the root situation. The warning's sentence *every
`unsupported` / `blocked` / count asked during it answers about the mutated
world* is, measured, about `blocked` alone.

And the 15 `_verdict` asks live in exactly two groups:

    rule_driven_supposition       13
    crossing_opens_hypotheses      2

Both are checks ABOUT supposing, so they go with the mechanism rather than
surviving to be broken by it. **No check that is about something else asks an
aggregate inside a hypothesis.**

### The concurrent read: exactly ONE, and it is `_deliver`

The warning's real claim is *wrong the moment anything concurrent reads*. Over
the whole suite:

    suppositions opened                              221
    discharged                                       212
    arrivals delivered                                17
      ...while the register was inside a hypothesis    1
    `standing_in` crossings                          499
      ...OUT of a hypothesis, to root                  1

⭐ 498 of the 499 crossings are `Graph.rebuild` carrying a conclusion out at
discharge -- the discharge path, not a concurrent reader. The single genuine
concurrent read is `Machine._deliver`, which stands in the agent's own situation
because the world speaks while the register is inside a hypothesis. That is
**one call site**, not a class of them: `probes/experts` and `core/channels`
were named as suspects in the warning and neither reads across a boundary.

> So the answer to *how much of the second warning is theoretical* is: the
> aggregate half is theoretical for `count`/`root`/`support` and real for
> `blocked` in two checks that are themselves about supposing; the concurrent
> half is one call site, `_deliver`.

### For scale, since the same instrument reports it

    index reads through `_bucket`     463,864
      inside a hypothesis, spanning    59,783   (12.9%)

That is ordinary matching, not aggregation -- it is what stops being scoped for
free, and it is what the proposal INTENDS to stop scoping.

⚠ Instrumented in-process, so the counters do not follow the probes that fork
(`learning/forest`, `learning/practice`). The numbers above are the selftest's.

### ...and the same instrument over the sweep, which found one module the suite hides

Every module with a `main()`, `necessity` excepted. `_verdict` is again the ONLY
aggregate that ever runs inside a hypothesis -- `count`, `root` and `support`
are **0 inside, in every module**, over 1,596 asks.

    module                    asks   inside      index reads    inside
    learning.practice          133       88 (66%)      41,706    24,451
    gates.state                271       15            463,864   59,783
    probes.shapes              271       15            464,067   59,783
    learning.learning          853        0            170,134        0
    learning.teaching            9        0             64,850        0
    learning.forest              3        0             31,271        0
    probes.artefact             30        0             14,729        0
    probes.tools                12        0              2,759        0
    probes.intake                8        0              5,478        0
    probes.quest                 6        0              3,602        0

⚠ `gates.state` and `probes.shapes` run the suite internally, so their 271/15 is
the selftest's number seen twice, not a third measurement.

⭐⭐⭐ **`learning.practice` is the one the suite hides**: 66% of its aggregate
asks and 59% of its index reads happen inside a hypothesis. Nothing else comes
near it. It is the module to run first after the deletion, and the one place the
*aggregates stop being scoped for free* warning has a real population behind it.

⚠ The counters do not follow a probe that forks, so `learning/forest` and
`learning/practice` are undercounted rather than exact.

---

# Queued: from descriptions to rules  ->  `docs/descriptions-to-rules.md`

Probed 2026-08-20 across five sessions of measurement and moved out of this
queue into its own brief, because it is the subject of another session. In one
line: **a corpus can already compile a description into live rules with no engine
change**, and what stands between that and *everything is facts* is a missing
constructor for building a node of runtime arity.

Measured there: the five-rule compiler; the binding check that catches two silent
defects; `adopt`'s order-dependent silent decline; deposit-as-install at 639/641;
variable identity as a claim; and the rule-as-subgraph blocker.

---

# NEXT: suppositions as PROCEDURES, and the one affordance that is missing

The author's, 2026-08-20, on the situations work: retiring situations was meant
to remove Frame/forks/seat/topic **and** to make the agent do suppositions and
plans *a different way -- by explicit node manipulation, potentially leveraging
procedures to manage them*. The deletion is done; **the positive half is not
built**, and this is the brief for it.

## The substrate already exists, and it is already rules

`bundle.ugm`'s call stack (§18) is three rules and no engine:

    <call-spawn>   { +spawn(?c, ?args, ?stage) }
                => { +call(+k, ?args), +stage(+k, ?stage),
                     +awaits(?c, +k), -spawn(?c, ?args, ?stage) }
    <call-advance> { +stage(?c,?p), +awaits(?c,?k), +returned(?k), +advances(?p,?q) }
                => { -stage(?c, ?p), +stage(?c, ?q), -awaits(?c, ?k) }
    <call-return>  { +stage(?c,?p), +awaits(?c,?k), +returned(?k), +closes(?p) }
                => { -stage(?c, ?p), +returned(?c) }

⭐⭐⭐ **This is already explicit node manipulation.** `+k` mints a fresh call
node per application; `+stage`/`-stage` step it; `advances`/`closes` are facts a
corpus deposits, so the ORDER of the steps is data. A supposition is the same
shape: spawn a call, assert the hypothesis, run, record what followed, retract
the world-deltas, return.

⭐ And it is what `docs/todo.md`'s experiment 4 measured by hand -- *4 deltas
linked, 2 about the world* -- with the linking and the swapping-back done by
staged rules instead of by Python.

## ⚠⚠⚠ CORRECTED: there is no un-claim, and the anchored shape does not need one

First written here as *the one thing that is missing*. Measured, the reasoning
was wrong twice over.

**`+not(p)` is not an alternative to `-p`.** `bundle.ugm`'s `<denial>` rule
translates the term form into the sign form, so it lands as ANOTHER ENTRY ABOUT
`p`:

    after +p          p = +   not(p) = None
    after +not(p)     p = -   not(p) = +
    claims about p  : ['+', '-']

Deleting `<denial>` does not help either -- then `+not(p)` leaves `p` at `+`,
which is worse.

**And the sign was never the reason.** `None` means *no entry about this
proposition*. The chain is append-only, so once something has been spoken about,
nothing that can be ADDED makes the chain say nothing about it. `-p`,
`+not(p)`, a `withdraw(?e)` claim -- every one of them is another claim.
Return-to-`None` is unreachable by construction, for any design.

⭐⭐⭐ **So the requirement dissolves rather than being met: the un-claim is only
needed by a supposition that mutates the REAL graph.** The anchored shape never
speaks about reality's `p` at all, so there is nothing to restore and no scar to
leave. `learning/practice.py` is the worked proof -- a rehearsal asserts
`+in(r1, doing(smash(jug1)))`, reality's `intact(jug1)` is never spoken about,
and the practised agent runs clean with no retraction primitive anywhere.

> Refinement 2 of the queue entry above asked for *+ and - return to None, not
> to -*. That is the right requirement of the WRONG design. Under anchors it is
> satisfied vacuously, which is a better outcome than satisfying it.

## What the procedure story therefore needs: nothing new

A supposition-procedure stages over an ANCHOR: spawn a call, assert into scene
`?s`, run, record the conclusions OUT of the scene, close. The only retraction
is `-stage(?c, ?p)`, which the call stack already does and which is about the
procedure's own bookkeeping rather than about the world.

⚠ Whichever it is, it must be checkable: the queue entry above already says
**the revert must be CHECKED, not trusted** -- *are we back where we started* is
computable, and one engine check that refuses to continue otherwise is a row,
not a mechanism.

---

# ⭐⭐⭐ THE GRAPH IS A MUTABLE SCRATCHPAD — the author's, and it reframes the lot

Stated 2026-08-20, after the situations deletion and after the un-claim question
above was answered the wrong way twice:

> *The engine used to provide a VIEW of the current state based on the chain of
> changes. I don't want this any more. I DO want to record what changed so the
> agent can read what changed, but there is always a SINGLE GRAPH, that is a
> single scratchpad, and everything happens in it.*

## What this replaces

    today       the GRAPH holds structure; the CHAIN holds belief as signed
                entries; `resolve` computes a VIEW over the chain -- *the last
                claim about this proposition wins*. `holds(p)` asks the chain.
    proposed    the GRAPH holds belief. It is the state. The CHAIN becomes a LOG
                of what changed, which the agent READS -- not a thing the state
                is computed from.

⭐⭐⭐ **And then DELETE is the un-claim.** Every attempt above to get back to
`None` failed for one reason: an append-only chain can only be added to. A
scratchpad can be erased. *A proposition never considered* and *one considered
and rejected* stop being hard to tell apart, because the first has nothing in
the graph and the second has a denial in it.

## Why this is closer than it looks

    an entry IS already a node    `instance(ENTRY, proposition, sign)`, so
                                  belief is already IN the graph -- it is just
                                  also indexed in `_claims`, and `_claims` is
                                  what `resolve` reads.
    deletion is half built        `Graph._drop_from_index(n, kr, km)` already
                                  takes a node out of `_interned`, `_by_rel` and
                                  `_by_arg`. It was written for `merge`.
    the log is already reified    `in_delta`, `delta_next`, `pred`, `anc`,
                                  `entry_of`, `rests_on`, `licensed_by` are
                                  ordinary relations. *What changed* is already
                                  readable by rules.

⚠ **Presence cannot mean belief on its own**, and this is the trap to design
against: `boiling(?w)` is in the graph as a rule's stored pattern and is not
believed. That is §14's use/mention distinction, and it is why the ENTRY node --
not the proposition node -- has to be the thing that is present or absent.
Deleting the entry retracts the belief; the proposition stays as structure, as
it must, because rules mention it.

## What it costs, and it is not small

    resolve / holds        become *is there a surviving entry about p*
    _claims                stops being an append-only index and needs deletion
    _kept                  is maintained incrementally against `len(seat.delta)`;
                           deletion breaks that stamp
    trail / rests_on       an entry deleted out from under a trail
    gates.state            compares kept-state against a walk; the walk is the
                           thing being retired

⚠⚠⚠ **And the one real question to settle first: what does DELETE mean for
anything that pointed at the deleted node?** `merge` had to answer this and its
answer was the repoint -- *without it, everything said before the merge is
LOST*. Deletion has no repoint available. A rule that consumed an entry, a
`rests_on` edge, an `applied(...)` licence: each is a dangling reference the
moment its target goes. **Decide it before building**, or the first corpus that
retracts will read as a corpus that corrupts.

## Where the in-flight work stands relative to this

The situations deletion and the `seat`/`topic`/`locus` cut are **prerequisites,
not detours**: both remove the view-computation apparatus this proposal is
replacing. `resolve` is already down from *greatest (locus depth, seat depth,
position) filtered by two ancestry walks* to *the last claim*. The next step is
that the last claim stops being a claim at all and becomes a node that is either
there or not.

⚠ The suite conversion for that cut is INCOMPLETE and the tree is red. Last
fully green commit: `6c370d2`.

## ...and belief is an ANCHOR, not a floating fact

The author's, immediately after, and it settles both open questions above:

> *Dangling references: I don't care, they can stay -- hopefully no rule will
> match an incomplete subgraph. And on "believed": the point is that we never
> look for a `boiling` floating around in the graph. We ALWAYS anchor. Maybe to
> `believed(boiling)`; if we want, `believed` can be a hyperedge.*

### This dissolves the use/mention trap rather than guarding against it

The warning written above -- *presence cannot mean belief on its own, because
`boiling(?w)` is in the graph as a rule's stored pattern* -- assumed a bare
proposition was the thing to look for. Anchor it and the problem is gone:

    boiling(?w)              structure. A rule's stored pattern. Never believed.
    believed(boiling(k))     a node. Present = believed. Absent = not.

⭐⭐⭐ **The entry becomes an ordinary anchored proposition.** `entry(p, +)` was
already a node minted by `instance`; `believed(p)` is the same thing with the
sign gone and a name that says what it is. §14's use/mention distinction stops
needing a `mention` flag on the deposit, because USE is anchored and MENTION is
not -- structurally, not by a boolean the writer has to get right.

⭐ **And the substrate is already a hyperedge.** §3: *edges carry no information
beyond connecting, so anything you want to say about a connection has to be a
node.* `g.rel(relation, *members)` is n-ary with ordered members already, so
`believed(p)` needs nothing new, and `believed(p, source, ...)` is available when
it does.

### What falls out

    retract        DELETE the `believed(p)` node. `p` survives as structure,
                   which is correct -- rules mention it. **Back to `None`,
                   with no scar and no un-claim primitive.**
    deny           `believed(not(p))`, which is a DIFFERENT node from
                   `believed(p)`. Both can be absent; that is ignorance.
    signs          `+`/`-`/`?` stop being a member of an entry. §9's denial was
                   already available as a term; `?` becomes `believed(unsure(p))`
                   or is dropped -- decide it.
    scenes         `in(h1, p)` is the same construction one anchor along, so a
                   supposition needs nothing the belief case does not already
                   have. `learning/practice.py` already runs this way.
    the log        unchanged, and still the half the author wants kept: what was
                   added and removed, readable by rules.

### Dangling references: DECIDED -- they stay

Deletion does not repoint and does not cascade. A `rests_on` edge or an
`applied(...)` licence naming a deleted node is left as it is, on the argument
that **no rule matches an incomplete subgraph**: a premise that needs the
deleted node fails to bind, so the dangling half is unreachable rather than
wrong.

⚠ Worth ONE check rather than trust, and it is cheap: after a deletion, does any
rule still fire on a partially-present structure? That is the same shape as
`merge`'s *without the repoint, everything said before the merge is LOST* --
asked of the opposite operation.

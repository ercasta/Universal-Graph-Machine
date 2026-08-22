 I have two changes to propose, let's decide whether to do this now or later. One is syntactical: instead of rule <something>:, could we use rule(something,implies(...)) and rule(something,causes(...))? Same
  for actions: action(move($x,$y)) where in this case $x and $y mean they will be bound at runtime. This would make everything be "facts". The second change is more significative. Right now we have some
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
    worked.ugm          one rule concluding `suppose($p, likely)`
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

 Do not re-derive `mark()`/`revert()` from the queue entry above. It was
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

Rules written relative to an anchor by binding: `{ +in($w, reading($p, low)) }
=> { +in($w, symptom($p, restricted)) }`.

    in(h1, action(replace, pump7))       +       the hypothesis concludes
    in(actual, action(replace, pump7))   None    <- containment, BY BINDING
    action(replace, pump7)               None    the bare form never appears

⭐ The containment CHECK is an ordinary premise. A rule gated on `+world($w)`
acts in reality and declines in a hypothesis -- *what would happen if we set fire
to the house*, answered without burning it down, with no machinery.

⭐ Reality is an unprivileged anchor (`actual`). No special case.

 **The lifting objection does not apply**, which was worth checking: the
generic reified `<lift>` rule handles a ground pipeline (`likely(r(x))` -> `+`)
and NOT a variable-carrying one (`likely(action(replace, pump7))` -> `None`).
That kills a lifting-based replacement; it says nothing against binding, because
`$w` is bound by ordinary matching.

 **The cost is on EVERY rule**: every premise and conclusion wrapped in
`in($w, ...)`, on 51 of the 72 authored rules. This is what the swap shape
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

⭐ Nesting is ONE rule: `{ +within($c,$p), +in($p,$f) } => { +in($c,$f) }`, and
`$f` binding a whole proposition is handled by the matcher.

⭐⭐⭐ **And use did not leak into mention.** `<inherit>`'s unconstrained `$f`
picked up exactly the four asserted facts and none of the rules' own MENTIONED
antecedent patterns. Anchored rules reify identically to plain ones.

 But `<inherit>` copies eagerly, and measured it is DEARER than doing without:

                                     h1 concludes   entries   nodes
    no h1                                None         159      1600
    h1: only the delta                   None         160      1607
    h1: delta + <inherit>                  +          177      1750
    h1: context asserted BY HAND           +          167      1659

> **A hypothesis must be given its CONTEXT, not just its delta** -- and doing so
> by hand beats blanket inheritance, because the agent copies only what the
> hypothesis needs.

 And the failure is SILENT: under-assembled context (`None`) is
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

 **Refraction bookkeeping SURVIVED the swap-back** -- `exercised(<boil>)`
and `spent(<boil>, premises(...))`. The agent then believes it already used the
rule on those premises, so **a hypothesis burns that rule's chance to act for
real.** This is the defect to design against.

 **`boiling @peak` was not shown to survive as history.** Every write landed in
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

 This is a deliberate departure from *deniable, not forgotten*, scoped to
supposition deltas. The RECORD of what was supposed lives in the chain's
history; it must not live in current belief as a denial.

**3. No special `@` markers -- if everything is in the graph, reads are ordinary
graph readings.** The locus/`at`/`holds_at` apparatus stops being a second way
of asking. Check what this costs before cutting: §12's `at $m`, `hindsight`, and
`chain`'s two-times (locus vs deposit) are the things it touches.

### What is GAINED, so it is not only a loss

The 95-nodes-per-supposition leak `docs/situations.md` concedes and never fixed
goes away, because there is no hypothesis to leak FROM. And `docs/situations.md`
itself becomes a historical document rather than a description of the engine --
move it, do not leave it describing a mechanism that is gone.

## Two things to design rather than discover

 **Containment stops being structural and becomes a promise.** Today it is
by construction: 106 nodes minted inside the `supposing()` hypothesis, 0 visible
to the caller. Under the proposal containment is whatever the revert actually
does, and a botched revert leaves `burnt(house)` BELIEVED -- silent, and
belief-corrupting, which is the worst failure mode available here.

> The revert must be CHECKED, not trusted. The delta chain is reified, so *are
> we back where we started* is computable. One engine check that refuses to
> continue otherwise is a row, not a mechanism -- and it keeps the guarantee
> while still deleting the machinery.

 **Negation-as-failure and counting are the sharp edge.** `situations.md` is
explicit that stratum-0 structure is where NAF, counting and the rules-as-facts
interpreter all live, and that today BOTH indices are keyed by situation so
aggregates are scoped for free. If a hypothesis mutates the real graph, every
`unsupported` / `blocked` / count asked during it answers about the mutated
world. That is CORRECT while the agent means to be hypothesising, and wrong the
moment anything concurrent reads -- `ugm/experts.py`, `ugm/channels.py`. Decide
it explicitly.

 And sibling hypotheses become a STACK rather than a tree. `Graph.branch(born=…)`
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

 Instrumented in-process, so the counters do not follow the probes that fork
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

 `gates.state` and `probes.shapes` run the suite internally, so their 271/15 is
the selftest's number seen twice, not a third measurement.

⭐⭐⭐ **`learning.practice` is the one the suite hides**: 66% of its aggregate
asks and 59% of its index reads happen inside a hypothesis. Nothing else comes
near it. It is the module to run first after the deletion, and the one place the
*aggregates stop being scoped for free* warning has a real population behind it.

 The counters do not follow a probe that forks, so `learning/forest` and
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

    <call-spawn>   { +spawn($c, $args, $stage) }
                => { +call(+k, $args), +stage(+k, $stage),
                     +awaits($c, +k), -spawn($c, $args, $stage) }
    <call-advance> { +stage($c,$p), +awaits($c,$k), +returned($k), +advances($p,$q) }
                => { -stage($c, $p), +stage($c, $q), -awaits($c, $k) }
    <call-return>  { +stage($c,$p), +awaits($c,$k), +returned($k), +closes($p) }
                => { -stage($c, $p), +returned($c) }

⭐⭐⭐ **This is already explicit node manipulation.** `+k` mints a fresh call
node per application; `+stage`/`-stage` step it; `advances`/`closes` are facts a
corpus deposits, so the ORDER of the steps is data. A supposition is the same
shape: spawn a call, assert the hypothesis, run, record what followed, retract
the world-deltas, return.

⭐ And it is what `docs/todo.md`'s experiment 4 measured by hand -- *4 deltas
linked, 2 about the world* -- with the linking and the swapping-back done by
staged rules instead of by Python.

##  CORRECTED: there is no un-claim, and the anchored shape does not need one

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
`+not(p)`, a `withdraw($e)` claim -- every one of them is another claim.
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
`$s`, run, record the conclusions OUT of the scene, close. The only retraction
is `-stage($c, $p)`, which the call stack already does and which is about the
procedure's own bookkeeping rather than about the world.

 Whichever it is, it must be checkable: the queue entry above already says
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

 **Presence cannot mean belief on its own**, and this is the trap to design
against: `boiling($w)` is in the graph as a rule's stored pattern and is not
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

 **And the one real question to settle first: what does DELETE mean for
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

 The suite conversion for that cut is INCOMPLETE and the tree is red. Last
fully green commit: `6c370d2`.

## ...and belief is an ANCHOR, not a floating fact

The author's, immediately after, and it settles both open questions above:

> *Dangling references: I don't care, they can stay -- hopefully no rule will
> match an incomplete subgraph. And on "believed": the point is that we never
> look for a `boiling` floating around in the graph. We ALWAYS anchor. Maybe to
> `believed(boiling)`; if we want, `believed` can be a hyperedge.*

### This dissolves the use/mention trap rather than guarding against it

The warning written above -- *presence cannot mean belief on its own, because
`boiling($w)` is in the graph as a rule's stored pattern* -- assumed a bare
proposition was the thing to look for. Anchor it and the problem is gone:

    boiling($w)              structure. A rule's stored pattern. Never believed.
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

 Worth ONE check rather than trust, and it is cheap: after a deletion, does any
rule still fire on a partially-present structure? That is the same shape as
`merge`'s *without the repoint, everything said before the merge is LOST* --
asked of the opposite operation.

### DECIDED: the signs go, and `?` is DROPPED — absence is ignorance

The author's, 2026-08-20: *dropped. Anything unstated is unsure / unknown.*

    +p    believed(p)          a node. Present = believed.
    -p    believed(not(p))     a DIFFERENT node. §9 already had denial as a
                               term; the sign was the redundant one all along.
    $p    nothing.             Absence IS unknown.

⭐⭐⭐ **This dissolves the reason `?` was introduced rather than overriding it.**
`Chain.holds` states it: *`?` is not None: it stops the walk and reports
ignorance, **which is the one thing writing nothing could never say** (§6).*
That is true of an APPEND-ONLY chain, where absence is ambiguous -- never
considered, or not yet derived? -- so ignorance had to be written down to be
distinguishable from silence.

A scratchpad breaks the ambiguity from the other side: **the log records the
erasure.** *Nothing has been said* and *this was believed and I erased it* are
told apart by reading what changed, which is the half of the chain the author
kept. So absence becomes readable, and `?` stops being the only way to say it.

 What to check when it is built, because this is where a dropped distinction
usually comes back: the three-valued reads. `unsure` is reserved vocabulary, a
`?` member is parseable (`? $p` appears in `bundle.ugm`'s `<deviation---
invalidated>`), and §6's *a rule that reads ignorance* is a real pattern. Each
becomes *no `believed(...)` node matches*, which is negation-as-failure -- so
the honest question is whether the four deviation rules still say what they say
when ignorance is absence. **They are the fixture for this change.**

✅ **ASKED AND ANSWERED, 2026-08-22** -- `ugm.probes.collapse`, 10/0, and
`wanting.md` §9.4 carries the tables. They do not say what they say, and that is
the good news: the four become **one**, because the sign in `expects($p, minus)`
was a proposition wearing a sign's clothes. Read it as `expects(not($p))` and no
sign is left in the family at all. The naive translation -- every `-` and `?`
member becoming `no` -- breaks exactly one row, `<deviation---invalidated>` on
an expectation the world MET, which is the direction that looks like success;
and deleting that rule does not save the reading, it moves the loss to the other
expects-minus row. The distinction the merge eats, contradicted vs invalidated,
moves into `not($p)` and comes back as rows.

 Two things this found on the way. The suite had a control for expects-plus and
**none for expects-minus**, so the one row the collapse breaks was the one row
nothing asked -- both controls now run (558). And the migration is a header line
only where a `-` is a consequent: in a MEMBER it is one of two different things,
`no $p` or `+not($p)`, and the corpus has to say which.

---

# QUEUED by the seat/locus cut — reading the past, as rules

The cut is finished and green (503/0, sweep 0/24). Four groups and two modules
were deleted rather than converted, on the author's call *delete now, convert in
a follow-up*. This is the follow-up, and it is **one conversion, not six**:
every one of them bound a moment from an ordinary member, and every one of them
is writable over the structural relations instead.

    at $m                 the locus of the entry that satisfied the member
    in_delta($m, $e),     the same claim, over the raw chain -- and `anc`/`sanc`
    entry_of($e, p, +)    order the moments

⭐ **PROVED REACHABLE before anything was deleted**, not assumed:

    rule <after> = implies( { asking($s), anc($s, $mq), in_delta($mq, $eq),
                              entry_of($eq, acts($q), plus),
                              anc($s, $mp), in_delta($mp, $ep),
                              entry_of($ep, acts($p), plus),
                              sanc($mq, $mp) },
                           { acted_after($q, $p) } )
    → acted_after(goblin, hero)

 **What that version is NOT the same as.** It is stratum 0 -- every antecedent
member is structural -- so its conclusion is MINTED structure, not a deposited
entry, and `_state()` will not show it. Every converted fixture has to read the
graph or add an ordinary rule downstream of the recogniser. `<say>`/`<note>` in
the deleted fixtures already did exactly that, so the shape is known.

What is waiting, and where the record of each is:

| gone | was | recorded at |
|---|---|---|
| `a_rule_can_relate_two_moments` | a member says WHERE its entry sits, and the round trip through `reify` keeps it | comment in `selftest.py` |
| `the_skeleton_is_an_ordinary_member` | an ordinary rule matches the skeleton; a downward pattern is not refused | comment in `selftest.py` |
| `a_span_is_a_locus` | **the design document's own worked example** -- *taking turns* over ten stretches | comment in `selftest.py` |
| `probes/hindsight` | `holds_at` resolving at a named moment; unanchored and generic both decline | `docs/design/hindsight.md` |

##  The one thing the conversion does NOT recover, and it has no home

**Dating a claim to a stretch.** A span was a kind of LOCUS, and that is what
made *it held throughout M1..M4* a different claim from *it held at M1*. Nothing
in the tree can say the first now. `silence_over_a_stretch_is_sayable` is the
nearest survivor and it deliberately does less: a recogniser carries its two
endpoints itself and deposits an ordinary claim, which is `bundle.ugm`'s *the
claim is deposited now, like every other claim, rather than dated to the
stretch*.

The refusal that went with it is the sharp part, because it was load-bearing:

> a claim about an INSTANT does not become a claim about a stretch -- inheriting
> it would answer *did it hold throughout* from an entry that cannot see a
> denial in the middle.

Under the scratchpad design that question gets harder, not easier: belief
becomes presence, and a stretch has no presence. **Decide it before a corpus
needs it**, or the first agent that reasons over a duration will be answering
from an instant and nothing will say so.

---

# FOUND while finishing the cut — three that were not part of it

##  1. `close(<R1>, <R2>)` depends on where the chunk boundary falls

`ugm.probes.walkers` was deleted for this and the finding is the reason to keep
reading. Two rules with identical antecedents contend for one position. The
recall table is matched in chunks of `SHORTLIST = 5`, and the loop stops
widening the moment its window is non-empty -- so a rival on the far side of a
boundary is **never matched**, and the doubt is never noticed.

    23 rules (before)   step at 21, fork at 22   one chunk    window [step, fork]
    21 rules (after)    step at 19, fork at 20   two chunks   window [step]
    SHORTLIST = 6       -- the only change --                 window [step, fork]

The bundle shrank by two rules with the situations deletion, and that was enough.
§15-16 built the noticing and called arbitration total; this says the noticing is
conditional on table position. **Not fixed, because the fix changes the loop
every rule runs through**: keep widening while the next chunk's top score is
within `TOLERANCE` of the window's, so a tie is finished before the loop stops.

##  2. `current_state` was ordering by FIRST mention, and the order is semantics

Introduced by the collapse to one time: `_claims` is keyed by first mention, so
`[got[-1] for got in reversed(...)]` returns a proposition where its FIRST claim
put it. `Machine._state`'s incremental path does not have the bug -- it deletes
and re-inserts -- so the rebuild and the growth disagreed about order on **1,675
of 5,919** comparisons. *A description with two candidates resolves to the most
recent* rests on that order. Fixed: sort by the governing entry's own node,
which is mint order.

⭐ And the reason it was invisible: **`ugm.gates.state` was comparing an index
against itself.** Its slow side called `current_state`, which after the collapse
is one line over `chain._claims` -- the very index the maintained state is built
from. The gate now walks the moments itself. That is the lesson the gate exists
to enforce, applied to the gate.

##  3. `entry_of` matched nothing, silently

`_members_of` required a four-argument member and a three-member entry. An entry
has two members now, so **every rule that reads the chain found zero** --
including the whole of `gates/agreement.py`'s `READ`. Nothing raised. The
name-identity trap's shape with a different name: a member that is well formed,
loads, and matches nothing.

##  4. Two §20 floor gates had NEVER been in a sweep

`tools_sweep.sh` grepped `^def main`; `gates.agreement` and `gates.quiescence`
call their entry point `run`. The file's own header already records this bug
twice -- a hand-written list, then a flat glob -- and this is the third shape:
**the question is not what the function is CALLED, it is whether the module is
a door.** Keyed on `if __name__ == "__main__"` now, which took the sweep from
24 modules to 29 and brought in `gates.bundle`, `probes.backward` and
`probes.compose` as well.

Both gates were broken by the cut and both are converted here. `agreement`'s
`READ` lost `<beaten-locus>` and every remaining rule lost a key -- the read was
ordered by locus first, with deposit order breaking ties *within* a locus, and
there is one order left.

 Its fixture forks on purpose, and the fork had to move OFF the chain's end.
`Chain.resolve` filters by no branch, so with the fork written last the gate
compared a native read that ignores branches against a rule-level read anchored
on the other one. **They disagreed, correctly, and the rule-level answer was the
better of the two.** That is worth keeping in view: the native read's *nothing
forks* precondition is now load-bearing and unchecked.

 **And `quiescence` still exits 1, for a reason older than this branch.**
`<silent>` derives nothing in any of its 12 fixtures -- 5/6 of its own rules
exercised -- and `run()` counts a blind rule as a failure, which is right.
Checked against `6c370d2` rather than assumed: that commit prints the same 5/6
and the same `<-- BLIND`. **A gate nobody ran had been saying this all along.**

`<silent>` needs a candidate that is `unbound` -- a conclusion still generic
after substitution -- and NOT `mentioning`. `SHAPES`' `<attach>` was written to
be exactly that shape (`+resume(hall, <echo>)`, generic only because `<echo>`'s
patterns are) and it is not reaching the rule.  First thing to check: whether
a rule whose consequent NAMES a rule is marked `mentions`, which would make
`unbound` and `mentioning` fire together and `<silent>` unreachable by
construction. Left named rather than fixed, as `gates.state` was before it.

---

# ✅ BUILT: the ATTENTION STACK — `push` and `pop` as postconditions

The author's, 2026-08-21. **Built 2026-08-21** -- see *BUILT 2026-08-21* at the
end of this section for what was measured, what it cost, what was settled and
the one measurement still unclaimed. Everything between here and there is the
argument as it stood before, kept because the numbers were taken against it.

⭐ **The author's call: this is the FIRST thing to implement**, ahead of
`believed(p)` and the queued `at $m` conversion -- and probably in a fresh
session, because nothing above it in this file is a prerequisite.

## The proposal, and it is one thing

`Machine._attention` becomes a stack of frames rather than a flat queue, and the
postcondition vocabulary gains two rows:

    push        start a fresh attention frame
    pop($x)     restore the previous frame, attending $x on it

 **The graph is untouched by both.** This is not a transaction, there is no
rollback, and nothing derived inside a frame stops existing when it is popped.
Popping a set of graph changes is a different feature, it does not exist, and it
is not wanted. Attention management is the whole of this.

## Why: the queue forgets, two ways, and both are constants in the code

    ATTENTION_SPAN = 7   `_push_attention`: *whatever falls off the bottom is
                         forgotten*                        machine.py:1295
    PULL = 6             `_pull`: weight = max(1, PULL - i), so nothing lifts
                         past depth 6                      attention.py:365

So a long sub-line's own writes evict what the agent was doing before it. That
is not a risk, it is the documented behaviour, and it has already cost this
repository twice, in numbers it wrote down itself:

    _attend_written    backed out TWICE (20d, 20h) -- *a queue permanently full
                       of undifferentiated nodes made the agent chase its own
                       tail and quiesce 30 MOVES EARLY*
    _attention_asked   *the dungeon quiesced 32 MOVES EARLY and lost 48
                       CONCLUSIONS*

## ⭐⭐⭐ Why a stack rather than a fourth filter

Three fixes have been tried and all three are **filters on a flat queue**:

    _attention_asked   claimed vs derived
    _bookkeeping       exclude the machinery's own relations
    weight             a learned `attend($x, 3)` outranks a weight-1 push

Each makes the queue's *contents* more selective. None of them can help, because
at span 7 a long enough sub-line evicts anything, however well chosen. **A stack
does not filter -- it suspends.** The outer frame is off the queue entirely, so
it cannot be evicted however long the inner line runs.

 And raising the span is not the answer, because the squeeze is from both
sides: `ugm.selftest` already measures the other end -- *attention that names
everything narrows nothing*.

## It is two rows in a vocabulary that already has three

`attend(...)`, `unattend` and `stop` are parsed in one function (`text.py`'s
`spend()`) and dispatched in one place (`attention.py:651-669`). §5's test is
that adding a connective adds **rows, not branches**, and this adds two rows to
the one list that already exists for exactly this kind of thing.

⭐⭐⭐ **And `stop`'s own design note is already the argument for a rule-decided
pop**, written before anyone asked for one (`text.py:369`):

> *Done is the output of a rule that checks against the goal* -- which the table
> loop's own design says, and had no way to obey. A rule concludes that here is
> over; its postcondition is what ends the run. **The loop still knows nothing
> about goals: it knows a rule spent attention by saying `stop`.**

So `pop` is `stop` scoped to a frame, and `push` is `attend` scoped to a fresh
one. Neither is a new kind of construct.

## ⭐⭐⭐ A frame carries its own RULESET, and that is the second duty

The author's, 2026-08-21. A frame is not only an attention queue:

    frame = (attention queue, the EXPERT whose rules are in play, its table)

So `push` is how one expert CALLS another and `pop` is how it gets the result
back -- the attention stack and the consultation stack are **one construct, not
two**.  The expert is held by NAME, never as a frozen rule list: `pool_of` is
*read, never kept* (`probes/experts.py`), because a registry built at load could
not see a `knows` that a rule concluded.

⭐⭐⭐ **And `probes/experts.py` already names the gap this closes, in its own
words** (`experts.py:147`):

> ...and run it again, because the answer is a new fact its rules have not seen.
> **Nothing is resumed: there is no suspended computation, only a table and a
> chain that has moved.**

An expert today does not wait for a result -- it re-runs its whole loop from the
top once the callee finishes, because there is nothing to suspend into. And
`run()` builds a FRESH `Table` whenever none is passed (`attention.py:438`),
which `experts.py` never does, so the caller's scores are discarded on every
consultation return.

 **The engine already knows what that costs**, in `tick`'s own docstring:

> The table PERSISTS across calls, or a caller stepping by hand would lose every
> buff between one tick and the next and be **measuring a different agent each
> time**.

That is stated about stepping by hand. `experts.py` incurs it on every return,
by construction. A frame that carries the table is what turns its re-run into a
resume, and *wait for the result* into something literally true.

 Two things this adds to OPEN below rather than settles:

    the cycle test    `experts.py` keys on the (expert, question) PAIR, not on
                      the expert -- `A -> B -> A` asking something NEW is
                      ordinary recursion and must be allowed. With frames the
                      stack is the natural key, and the caution below applies
                      with more force, not less.
    the budget        every `run()` carries its own `limit`, so a chain of
                      consultations multiplies the budget silently. A real
                      stack makes *whose budget* a question that has to be
                      answered rather than inherited.

## ⭐⭐⭐ AUTOMATIC EXPERT SELECTION, by TF-IDF — and it is not a proposal

The author's, 2026-08-21. `push` names the NODES to put in the new frame; the
expert is chosen from them, automatically, by **TF-IDF over experts**.

 **This is not *propose, and someone else decides*.** The author's, and it
settles a suggestion of mine that had the wrong shape:

> Like attention, it's life or death. If wrong, nothing can save the system.

**And the design already agrees, in §19's own words.** Recall is life-or-death
and unarguable in exactly this way -- a rule that was never recalled cannot
object that it was not -- and the answer this design gave was never a veto over
the choice. It was a CARVE-OUT for what must never depend on it:

> Recall may be incomplete about what to do. It may not be incomplete about what
> you must not do.

`_forbid` runs outside recall entirely. So the mitigation for an unarguable
selection is not making it arguable; it is knowing what must not ride on it.

### ⭐⭐⭐ And TF-IDF is specifically the repair for a collapse this repo MEASURED

`_salient` compared raw relation sets, and the `practice` rewrite recorded what
that costs: *`_relations_required` collapses to `{goal, in}` for EVERY route, so
`_salient` cannot tell two routes apart and `leaves()` returns NOTHING -- the
agent rehearses, is harmed, blames correctly, and learns nothing, **with no
error anywhere**.*

**IDF is the correction for precisely that pathology.** A relation in every
expert's pool gets near-zero weight and stops drowning the signal; the
discriminating terms carry the score. The naive version of this mechanism has
already failed once here, and this is not a generic scoring choice but the
principled repair of that failure.

⭐ **It also supersedes a hand-rolled guard.** `_pull` takes the STRONGER, not
the sum -- *adding them would make the weight a popularity count*. That `max` is
a crude defence against ubiquity. IDF is the well-founded version of the same
defence, which is what makes a weighted SUM safe here where a raw one was not.

### DECIDED

    the terms       individual terms scored, with BONUSES FOR COMPOUNDS. ⭐ Same
                    shape as attention's own scoring, which already decomposes a
                    proposition into every node it is made of (`_nodes_of`,
                    machine.py:1283) and pushes each part separately. The
                    discussion was had once for rules; this is it for experts.
    when IDF is     ONCE, at startup, when the whole KB is loaded.
    computed
    adding an       ...re-scores every other one, and changes which expert is
    expert          picked for unrelated frames. **A FEATURE, not a bug** --
                    written down here so nobody debugs it as nondeterminism.
    the data        FREE. An expert is already a set of rules (`knows($e, $r)`,
    it needs        read off the graph) and rule -> relation is already indexed
                    (`_by_relation`, attention.py:319). Expert -> terms needs no
                    new structure.

 **Mine, and strike it if it is not wanted.** What an unarguable step cannot
buy back is vetoability; what it must not lose is LEGIBILITY. Every other engine
decision nobody can override is deposited here -- `refused` (the gate's veto),
`unafforded` (*an attempt at something the palette does not afford, on the
record*), `declined`. So deposit the pick **and the scores it beat**. On a
life-or-death step it will be wrong eventually, and `why()` should answer rather
than shrug. That is `deposit-dont-decide.md` applied to a decision that genuinely
cannot be delegated.

 **One interaction to know about, not to relitigate.** IDF is fixed at startup;
pools are *read, never kept*, and `knows($e, $r)` can be CONCLUDED mid-run --
`<inherit>` derives more of them. So an expert's actual pool can grow after its
scores were computed. Decided as stated; recorded so whoever implements it knows
the two facts are in tension by design rather than by oversight.

## DECIDED

    frames carry    the attention queue, the expert whose rules are in play,
                    and that expert's table. Push is a call; pop is a return.
    who pushes      an EXPERT -- supposition, goal, procedure -- never a pure
                    reasoning rule. That is the whole point: a reasoning rule
                    must not be polluted with an external mechanism, and engine
                    support for the frame is what lets pure rules compose.
    what pops       a RULE says so. A goal-management rule that checks whether
                    the goal is reached spends `pop`.  NOT the loop detecting
                    its own quiescence -- that would put the decision back in
                    the engine, and `stop` already settles which way this goes.
    pop carries     `pop($x)` attends $x on the restored frame: the
    one node back   attention-level analogue of a return value. Without it the
                    agent returns from a sub-line with no idea it concluded
                    anything, and has to rediscover it by ordinary matching.
    deposited       a push and a pop are each written down, per `_unattend`'s
                    note: *denied, not forgotten -- dropping a Python set is not
                    readable by any rule and cannot be argued with*. A RECORD of
                    a focus change, not an undo of anything.
    NOT in scope    popping graph changes. See the warning at the top.

## OPEN

1. **A depth bound.** `probes/experts.py` sets `DEPTH = 8` with a cycle test
   keyed on the `(expert, question)` PAIR.  Copy its caution and not only its
   constant: an earlier draft of that file returned to the outer loop instead of
   servicing nested consultations in place, so **the stack was never deeper than
   one, the cycle test could never fire, and a check asserting depth passed
   while the stack was flat.**
2. **Does `stop` become *pop the root*?** Elegant, and not required.
3. **What else a frame holds.** Queue, expert and table are decided above;
   `_widened` is the remaining candidate, since it is already a degenerate pop
   (*the loop admits its table was wrong*).
4. **An unpopped frame.** Is a leak reclaimed, or is it a thing the agent can be
   asked about? The second is this design's usual answer.
5. **What the cycle test keys on** once the stack is frames rather than
   `(expert, question)` pairs.  `A -> B -> A` asking something NEW is ordinary
   recursion and must stay allowed.
6. **Whose budget.** Every `run()` carries its own `limit`; a chain of
   consultations multiplies it silently, and a real stack makes that a question
   rather than an inheritance.
7. **What must NOT ride on the expert pick**, per §19's carve-out. `_forbid`
   already runs outside recall; the same question has to be asked of an
   unarguable expert selection, and it is the only mitigation this design
   accepts for a life-or-death step.
8. **How `push` names its nodes.** The selection is computed FROM them, so the
   notation for saying which they are is the one part of `push` still unwritten.
   `attend($x)` is the precedent -- a host rule's own variable, bound by the
   move that spent it.

## What to measure FIRST, before building

Two things, and neither has a number yet.

1. **Is the eviction loss real in a corpus that already exists?** The figures
   above were measured on the flat queue's *contents*; nobody has measured how
   often a sub-line evicts an outer focus that was still wanted.
2. **Do experts actually discriminate, after IDF?** The overlap is what IDF
   discounts, so the naive-collapse worry is answered by the choice of metric --
   but how much signal is LEFT after discounting is still a number nobody has,
   and it is the number that says whether the pick is a mechanism or a coin
   flip.  `_salient` is the standing warning: it failed silently.
3. **How far does a re-run diverge from a resume?** `probes/experts.py` already
   re-runs the caller with a fresh table on every consultation return, so the
   comparison can be made against the code as it stands: run a consultation
   chain, then run it again passing the caller's table back in, and see whether
   the agent chooses the same moves. If it does not, `tick`'s *measuring a
   different agent each time* has a number for the first time.

 A frame that fixes nothing measurable is a mechanism this design would refuse
on its own terms.

## ⭐⭐⭐ BUILT 2026-08-21 — and the three measurements were taken FIRST

    python -m ugm.probes.frames    21 checks, 0 failing
    python -m ugm.selftest         513 checks, 0 failing   (was 503)

### 1. Is the eviction loss real in a corpus that already exists? YES, and it is enormous

`_push_attention` now counts a **readmit**: a node that fell off the bottom of
the queue and was later wanted back. That is the outer focus a sub-line evicted
while it was still live -- the agent rediscovering by ordinary matching what it
already knew it was doing. Over the probes as they ship, unchanged:

    ugm.probes.dungeon    15 machines,  13,986 readmits,  15 of 15 affected
    ugm.probes.hanoi      36 machines,   8,487 readmits,  25 of 36 affected
    ugm.probes.experts     4 machines,      26 readmits,   4 of 4 affected
    ugm.learning.maze      3 machines,      12 readmits,   3 of 3 affected

Nobody had this number before. The queue's forgetting was argued from two
back-outs and a constant; it is four figures per dungeon run.

 **And the loss is a DEMOTION, not an erasure** -- which nearly made the probe
pass on a technicality. `attend($g)` deposits a standing `attention(g)` claim
and `_attended()` puts a standing claim at the BOTTOM rather than dropping it,
so *was it forgotten* is the wrong question. What the queue loses is the node's
PLACE, and position is the strength: `_pull` weighs depth 0 at 6 and the bottom
of a full queue at 1. Measured on the probe's own corpus: front of the queue ->
position 7 of 9.

### 2. Do experts discriminate after IDF? Partly, and the limit has a shape

Measured on `probes/experts.py`'s own corpus, which was written for a different
probe:

    survey(plot1)  -> surveyor    surveyor 110, geometry 0, arithmetic 0
    area(plot1)    -> geometry    geometry 81, surveyor 81, arithmetic 0
    twice(3)       -> arithmetic  arithmetic 81, geometry 81, surveyor 0

⭐ IDF does what it was chosen for: `question`, `reply` and the rest are in
every pool, score **zero**, and stop drowning the signal. `survey` separates
cleanly.

 **What is LEFT after discounting is a tie between the expert that ANSWERS and
the expert that ASKS**, because both key on `area`. The tie falls to authored
order. That is signal rather than separation, and it is the honest answer to the
question the entry asked. The obvious next lever -- score the ANTECEDENT only,
on the argument that what an expert can be ASKED is its input side -- was tried
and measured: same picks, all scores halved. Not taken, because it buys nothing
and loses the consequent's evidence.

### 3. How far does a re-run diverge from a resume? ZERO — and that is a finding

Measured 2026-08-21 in `probes/experts.py`, which now runs its consultation both
ways over one corpus (`Consultation(resume=...)` is the only variable):

    re-run  geometry:area  geometry:perimeter  arithmetic:double
            geometry:perim-done  surveyor:record  surveyor:recorded
    resume  geometry:area  geometry:perimeter  arithmetic:double
            geometry:perim-done  surveyor:record  surveyor:recorded

**Identical, and structurally so rather than luckily.** With the buffs retired a
score is `STANDING` or `FLOOR` and only `absorb` moves it, so a rebuilt table
and a run-through one agree in `score` and `rank` -- the only two fields that
decide a move. Asserted directly: they differ in `ticked` and in nothing else.

 **So `tick`'s *measuring a different agent each time* is currently INERT.**
It was written when a buff moved a score. Nothing moves one. The table in a
frame is therefore not what the frame buys today -- the QUEUE is (13,986
readmits on dungeon) and the ROUTING is. It belongs in the frame for the day
something moves a score again, and that should be said plainly rather than
implied by the frame carrying it.

### ⭐⭐⭐ 3b. ...and the one way a resume CAN differ runs the OTHER way

Found while measuring 3, and it was a defect in the frame code:

    an expert concludes `knows(medic, <splint>)` while its own frame is open

`pool_of` is *read, never kept*, so `<splint>` is in the expert's POOL on the
next look. A kept table never absorbed it, because the first implementation
treated an expert frame as `fixed` and skipped `absorb` entirely. Measured
before the fix: the re-run applied `<splint>` and concluded `set(bob)`; the
resumed table did not. **A resume that is staler than the re-run it replaces.**

That is `absorb`'s own failure mode in its own words -- *the rule was live, it
was the node the graph described, and it never applied because nothing had a
score for it*. An expert frame now absorbs **from its expert's pool** every
tick: not every authored rule (which would undo the `pool` argument one
construct along) and not nothing (which is this). A frame holds its expert by
NAME precisely so the pool can grow; this is the half of that which reaches the
table.

### THE PORT, and `consult` is gone

`probes/experts.py` ships a second corpus, `PORTED`, in which **nothing names a
callee**:

    rule <ask-area>  = implies( { +survey($r) }, { +question(area($r)) } )
    after <ask-area> => push(area($r))

...and one inherited rule returns, because *what pops is a rule saying so*:

    expert responder
    rule <replied> = implies( { +question($q), +reply($q, $a) }, { +answered($q) } )
    after <replied> => pop($a)

Two hops, one `run()`, no outer loop, no Python stack, no `consult`, no
`answered` lift:

    surveyor: ask-area
      geometry: area
      geometry: replied
    surveyor: record
    surveyor: ask-perim
      geometry: perimeter
        geometry: double        <- picked geometry, not arithmetic
        geometry: replied
      geometry: perim-done
      geometry: replied
    surveyor: recorded

 **The `twice(3)` hop went to geometry rather than to arithmetic**, and the
answer is right anyway because geometry inherits `<double>`. That is the `area`
tie of measurement 2 showing up in the routing: a term shared by the asker and
the answerer scores for both. Defensible, not what a human would have named, and
recorded here rather than tuned away.

⭐ Both paths are kept on purpose. *How far does a re-run diverge from a resume*
is a comparison, and a file with only the new way has nothing to compare against.

### Two more found in the engine while porting

    `Table._target` answered for a bare variable and handed a COMPOUND back
    unchanged -- so `push(area($r))` came back generic and was dropped as
    *ground only*, one layer from the mistake. Spends now substitute the move's
    bindings the way a postcondition's query does, which also makes
    `attend(p($x))` mean something for the first time.

    `run()` set the root frame's table only `if served.table is None`, so a
    second run over a different pool RESUMED the first run's table -- the
    settling run's, holding one rule -- and went quiescent the moment it popped
    back to the root, with nothing to say why. Set unconditionally now: a frame
    keeps its table so a suspended line can be resumed WITHIN a run; across runs
    the caller decides, by passing one or not.

### What the stack costs, stated because the probe would otherwise report only
the column it won on

    343 rules matched flat   ->  358 framed     (+4%)
     55 widenings flat       ->   58 framed
     11 ticks                ->   11 ticks

**It is not a speed-up.** `_pull` lifts from a shorter queue inside a frame, so
the shortlist widens slightly further. The stack buys the line above staying
put, and pays a few percent of matching for it.

### Settled while building, and each was OPEN above

    whose budget    ONE run, one `limit`, across every frame it opens. A chain
                    of consultations does NOT multiply the budget.
    the cycle key   `(expert, frozenset(nodes))` over the whole stack. `A -> B
                    -> A` about something NEW is ordinary recursion and is
                    allowed; the same expert on the same nodes is refused, on
                    the record, as `declined(pushed, $n, already_open)`.
    a depth bound   `FRAME_DEPTH = 8`, a knob (`frame_depth($n)`) beside
                    `attention_span`. Asserted directly in two places, never
                    read off the stack's own output.
    stop vs pop     `stop` still ends the run; a pop with nothing to return to
                    is `declined(popped, $n, at_root)`. *Does `stop` become pop
                    the root* stays open and stays not required.
    what a frame    queue, expert, table, the nodes it was opened on, and the
    holds           `attention` claims it made. `_widened` was a candidate and
                    was not taken -- it is per-run, not per-frame.
    the pool floor  a nested `run()` may not pop the frame its caller was in
                    (`Machine._floor`). Without it a consulted expert could
                    return past its own caller, which is this stack's version
                    of the bug `probes/experts.py` records: a structure that
                    looks like a stack and is not one.
    no expert       a push whose nodes score zero everywhere keeps the rules of
                    the frame BELOW and says so. Picking the first expert
                    declared would be a coin flip wearing a mechanism's clothes.

###  FOUND while building, and it is not part of the stack

`_attention_asked` ordered standing `attention` claims **by iterating a Python
set** -- so which of several equally-claimed nodes lifted hardest was decided by
node id, which is to say by how many atoms the machinery happened to mint before
the corpus was loaded. Adding six reserved names reordered a shortlist in a
check that had been green for weeks, and nothing raised: a set is a perfectly
good answer to *which*, and no answer at all to *which first*.

Read in graph order now. ⭐ The §19 check it broke is SHARPER for it: attention
that names everything now produces **exactly the bare order**, more cheaply --
stated as an identity rather than as a difference, where the old version
asserted "the order still moves" on the strength of the accident.

---

# Measured 2026-08-21, and it belongs to SITUATION MANAGEMENT, not to the stack

Kept separate on purpose -- these were probed while the stack was being argued
and they are a different topic. ** Measured on the CURRENT engine, before
`believed(p)`**, so re-check anything that turns on entries once anchors are the
state.

Containment spreading along structure, as one ordinary rule, works today:

    rule <spread> = implies( { +in($h, $p), +$rel($p) as $t }, { +in($h, $t) } )

    in(h1, secret(a)) + said(secret(a))   ->  in(h1, said(secret(a)))    yes

A variable in the relation slot and `as $t` (`Member.binds`) are both already
supported, so the mechanism needs no engine support at all. Two limits, running
in opposite directions:

     arity 1 only     `$rel($p)` matches single-member instances. Measured:
                        `metal(kettle)` and `boiling(kettle)` reached;
                        `on(kettle, stove)` and `knows(bob, said(secret(a)))`
                        NOT. Containment stops at the first multi-ary relation,
                        and writing a row per (arity, position) is unbounded.
     it over-        `in(h1, kettle)` drags `metal(kettle)` and
    propagates          `boiling(kettle)` in -- world facts about a real kettle.
                        The rule cannot tell *minted inside the hypothesis* from
                        *already true and mentions the same thing*.

⭐ **The engine gap this names is one structural relation, not a mechanism.**
`structural_relations` (`rules.py:1368`) already carries `chain.ENTRY_OF:
_members_of` -- *not stored and not walked, but read off the node's own
members*. A generic member relation is that same kind, one more row in that
dict, and it collapses the arity problem to a single rule:

    { +in($h, $p), +member_of($t, $p) }  =>  { +in($h, $t) }

 **And the collision to settle before an expert is written:**
`learning/practice.py:60` already ships `<observe> = implies( { +world($s),
+did($a) }, { +in($s, did($a)) } )` -- believed world facts are deliberately
copied INTO a scene. So `in($s, p)` already means *p is part of scene s*, and it
cannot also mean *not believed*. Under the anchored shape it does not need to:
**not-believed is the default**, because minting structure believes nothing and
nothing mints a `believed(...)` anchor by accident. The marking job shrinks from
containment to belonging.

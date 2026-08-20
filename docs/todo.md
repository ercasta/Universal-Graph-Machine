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

# Probed 2026-08-20: can RULES compile a DESCRIPTION into working rules?

The author's theory, tested on the case that matters rather than on a toy: take
the DESCRIPTION of how to handle a hypothesis and have rules turn it into the
rules that handle one. Run against `bf702a7`. **Nothing about the engine
changed to take any of this.**

## It works, and the whole compiler is five rules

    fact <anchor> = +anchor(?w)

    rule <twin>       = implies( { +lift(?r), +conn(?r, ?c) },
                                 { +rule(+t), +conn(+t, ?c), +twin(?r, +t) } )
    rule <lift-ant>   = implies( { +twin(?r,?t), +anchor(?w), +ant(?r,?p,?s,?i) },
                                 { +ant(?t, holds_in(?w, ?p), ?s, ?i) } )
    rule <lift-con>   = implies( { +twin(?r,?t), +anchor(?w), +con(?r,?p,?s,?i) },
                                 { +con(?t, holds_in(?w, ?p), ?s, ?i) } )
    rule <lift-at>    = implies( { +twin(?r,?t), +at(?side,?r,?i,?m) },
                                 { +at(?side, ?t, ?i, ?m) } )
    rule <lift-names> = implies( { +twin(?r,?t), +names(?side,?r,?i,?n) },
                                 { +names(?side, ?t, ?i, ?n) } )
    rule <take>       = implies( { +twin(?r, ?t) }, { +adopt(?t) } )

Given two ordinary domain rules that say nothing about hypotheses:

    <symptom>  { +reading(?p, low) }          => { +symptom(?p, restricted) }
    <act>      { +symptom(?p, restricted) }   => { +act(replace, ?p) }

...the compiler authored both anchored twins, and they CHAIN:

    holds_in(actual, symptom(pump7, restricted))    +
    holds_in(actual, act(replace, pump7))           +
    holds_in(h1, symptom(pump9, restricted))        +
    holds_in(h1, act(replace, pump9))               +
    symptom(pump7, restricted)                      None   <- containment
    act(replace, pump9)                             None   <- by BINDING

⭐⭐⭐ **This retires the objection that killed the anchor shape.** Probe 1 above
concedes *the cost is on EVERY rule: every premise and conclusion wrapped in
`in(?w, ...)`, on 51 of the 72 authored rules*, and supersedes anchors on
exactly that. Measured, the cost is **five rules, paid once**, and no domain
rule is touched. The trade the swap-out shape was chosen to avoid is not the
trade that was on offer.

⭐ Multi-member antecedents survive: positions are carried, and one variable
shared across two members stays one variable.

## ⚠⚠⚠ Variable identity is SCOPE identity, and getting it wrong is silent

The same description in two named facts instead of one:

    fact <d-when> = +when(recipe1, seen(?x))     ?x is node 1384
    fact <d-then> = +then(recipe1, known(?x))    ?x is node 1389

Both print `?x`. The rule is authored, is live, prints as
`seen(?x) => known(?x)` -- and concludes **nothing**. One statement instead of
two, and `known(door)` is `+`.

> This falsifies `a_rule_can_author_a_rule`'s own stated reason for being a
> Python tool: *the variable is minted here, once, and used in both patterns --
> **which is exactly what no corpus can do**, and the whole reason this is a
> function rather than a rule.* A corpus CAN do it.

⚠ **Corrected below**: a first draft of this entry said *what a corpus cannot do
is share a variable ACROSS statements*. That is false, and the notation has two
mechanisms for it already.

## ⚠⚠ The slots are dropped by default -- the twin-trap family, in a corpus

Without `<lift-at>` and `<lift-names>`:

    { +boiling(?k) at ?m, +pred(?m,?e) } => { +earlier(?k,?e) }
      compiles to  { holds_in(?w, boiling(?k)), ... }     <- `at ?m` GONE

    { +boiling(?k) as ?n } => { +noted(?n) }
      compiles to a rule concluding about `?n`, which NOTHING now binds

`_reify_locus`'s docstring makes this argument four times about `adopt` and
`compose`. It arrives a fifth time here, one level up, and the mitigation is the
same shape: two more rows. ⚠ `pred` -- a skeleton relation -- also gets wrapped
in `holds_in(...)`, which is wrong and which probe 2's *21 of 72 rules need no
anchor* already predicts. Which relations are structural is itself a
description, and was not built here.

## ⚠⚠⚠ `adopt` RACES the compiler, and declines in silence

Same description, same compiler, same facts. Only the DECLARATION ORDER of
`<take>` differs:

                      twin facts  adopt asks  ant facts  rules authored
    <take> last            1           1          46           1
    <take> FIRST           1           1          46           0

    holds_in(h1, symptom(pump9, restricted))    +  /  None
    refusals recorded                           0  /  0

The description is COMPLETE in the graph in both runs, and the adopt was asked
in both runs. `_adopt` is an `on_write` hook: it reads the description at the
instant `+adopt(?t)` lands, finds `con` still empty, and returns -- once, with
no record and no retry.

> This is the repo's own recurring defect, and `_adopt` is where it now lives:
> *a fourth silent decline -- the agent would not act, and would not know it had
> not.* Every other request in the family answers or says why. Adopt returns
> `None` into the void, and a corpus cannot tell a rule it never adopted from
> one it adopted and that did nothing.

Two candidate repairs, neither taken here: make `adopt` re-askable the way
`_reask` already makes the other requests, or have it record `unadopted(?t,
reason)` so a corpus can ask again. The second is the one the rest of the
vocabulary is shaped like.

---

# Probed 2026-08-20: the binding check, and DEPOSIT-AS-INSTALL instead of `adopt`

Two questions the author asked of the compiling probe above. Both measured on
`cde0e8c`; the engine was not changed to take either.

## 1) One check catches BOTH silent defects, and the engine already has it

`Loader._rule` refuses a rule that *concludes about a variable its antecedent
never binds*. `_adopt` applies no such check -- a text rule is checked and a
graph-described rule is not, and that asymmetry IS the bug. Run over the three
cases:

    two-scope description        consequent `?x` is node 1389, unbound  REFUSED
    one-scope description                              nothing unbound  accepted
    dropped `as` slot            consequent `?n` unbound                REFUSED

⭐⭐⭐ **One check, both defects, and the control passes.** The two-scope trap and
the dropped-slot trap are the same fault seen twice: a consequent variable that
nothing binds. Nothing new has to be invented -- the check has to be moved to
where rules now also come from.

⚠ It cannot fire on every write, because a description arrives over several
ticks and is legitimately incomplete in between. **Complete-but-unbindable is an
aggregate over a finished search**, so it belongs at quiescence, in the family
`blocked` and `unsupported` are already in, rather than at the deposit.

## 2) Deposit-as-install WORKS: 639 of 641, and `adopt` is not needed for it

The author's proposal: stop treating `adopt` as a special request and let a rule
become live in the same place a loaded corpus's rules do. Prototyped as one
`on_write` hook -- when a describing fact lands, re-read that rule and install or
revise it -- with **no `adopt` in the corpus at all**, over the whole suite:

    suite                    641 checks, 2 failing
    wall                     15.1s, of which `_read_rule` 0.0s
    `_read_rule` calls       461     installs 9   revisions 97   no-revision 36

⭐⭐⭐ **Every rule in the suite goes through the round trip and 639 checks still
pass.** That is a far stronger fidelity test of `_read_rule` than adopt has ever
had -- adopt is exercised by a handful of fixtures, this puts all ~100 live rules
through it -- and it costs nothing measurable.

⭐ **And it fixes the race outright.** The order-dependence measured above is
gone: both declaration orders author the rule and conclude `+`. There is no
instant at which the description is read once and abandoned, because every write
re-reads.

### Two implementation facts, learned the hard way and both silent

⚠⚠ **The name must survive a revision.** `show(node)` is `<a>` where the loader
called the rule `a`, so re-installing renamed every corpus rule and a fixture
looking one up by name got nothing.

⚠⚠⚠ **Revise by MUTATING the Rule, never by minting a fresh one.** A new `Rule`
object for the same node is one rule in the graph and a twin in Python, and every
holder of the old reference keeps the stale one. Re-minting failed two
arbitration checks that compare `step.applied.rule is r1`; mutating in place
passed them. **The twin trap, ninth outing, this time in Python object identity
rather than node identity.**

### What it SPENDS, and it is exactly two checks

    FAIL  ...and a tool only PROPOSES: without the rule that adopts, the offer
          is on the record and nothing is live
    FAIL  ⚠ a rule adopted while supposing is REFUSED

The second goes with situations anyway -- `_hypothetical` is on the deletion
list -- so **one property is really at stake: propose/dispose.**

⭐⭐⭐ **And `adopt` is not what carries it.** An arrival already has the
propose/dispose shape without any help: `_report` writes `arrived(ch, p, sign)`,
so a channel that utters a described rule deposits a claim ABOUT one and a
corpus rule must lift it. The hole is the TOOL boundary, not the install: the
`<builder>` answerer writes `rule`/`conn`/`ant`/`con` straight into the graph
with `mention=True`, and under deposit-as-install that installs.

> So the repair is to put propose/dispose where it belongs -- at the boundary a
> description CROSSES -- rather than in a special install request. A tool that
> describes a rule should deposit under `answered(...)` like every other tool
> answer, and a corpus rule should lift it, exactly as it must for an arrival.
> Then `adopt` has nothing left to do that a deposit does not do, and the race,
> the silent decline and the second install path all go with it.

⚠ Not built, and one thing is unmeasured: whether anything depends on a rule
being describable in the graph WITHOUT being live. `reify` writes a description
for every live rule, so the two are already almost the same set -- but *almost*
is what this repo keeps getting caught by.

---

# Measured 2026-08-20: variable scope is UNIFORM, and there is no asymmetry

The author's challenge to the entry above -- *if regular rules do not share
variables across statements, why would dynamically written ones?* -- and it is
right. `Loader.var` states the rule, and it holds for both:

    # Variables are scoped to a rule: `?w` in two rules is two variables,
    # because a rule is a statement and not a fragment of a larger one.

    <a> = implies( { +p(?x) }, { +q(?x) } )     ant ?x 1392   con ?x 1392
    <b> = implies( { +q(?x) }, { +r(?x) } )     ant ?x 1430

⭐⭐⭐ **A rule described in ONE statement behaves exactly like a written one.**
Scope is the statement in both cases. The two-scope failure was not a trap in
variable scoping and not an asymmetry between written and described rules: it was
**half a rule written in each of two statements**, and the variables are two
because the rules are two.

    rule <half> = implies( { +p(?x) }, { } )
      -> REFUSED: line 1: expected a term, found '}'

⚠ **The syntax refuses that for a written rule and cannot refuse it for facts.**
That -- and only that -- is what is really different. A description is facts, and
facts do not have to add up to anything.

## Where the split IS forced, the notation already forces the fix

A source rule's arity varies (`<one>` has 1 antecedent member, `<three>` has 3)
and a compiler rule has a FIXED number of premises, so a COMPUTED description is
necessarily assembled over several firings -- one per member -- and those firings
must agree on the anchor variable. Written without a bound one:

    rule <lift-ant> = implies( { +twin(?r,?t), +ant(?r,?p,?s,?i) },
                               { +ant(?t, holds_in(?w, ?p), ?s, ?i) } )
    -> REFUSED: rule 'lift-ant' concludes about a variable its antecedent
       never binds -- the gate would refuse to deposit it (§13).

⭐⭐⭐ **So `<anchor>` is not a way ROUND a limitation; it is the only well-formed
way to write it, and the parser says so.** A shared variable has to be a BOUND
one, which is how everything else in this engine crosses a boundary.

⚠ An earlier draft of this entry called that a *trap in which lexical looks
referential* and said the unit of authorship stops coinciding with the unit of
the rule. Neither survives: nothing forces a hand-written description to split,
and where a computed one must, the language already refuses the wrong form.

## What is left of the defect, and it is simpler than what was claimed

    The parser refuses a malformed WRITTEN rule.
    Nothing refuses a malformed DESCRIBED one.

Both faults measured above are exactly *a described rule the parser would have
refused* -- the two-scope one and the dropped-`as`-slot one, which is why one
check catches both. The fix is not new machinery and not a new diagnostic: it is
`Loader._rule`'s existing check, applied where rules now also come from.

---

# Probed 2026-08-20: variable identity as a CLAIM, not an intake decision

The author's question, and it is the right way round: *why can't a loaded rule
with two `?w` in it be represented as a subgraph with two distinct `?w` nodes?*

## It can. The engine already has the representation

Two variable nodes plus `Graph.merge` is exactly that shape, and merge is real:

    before   bright(evening_star) is not bright(morning_star)
    merge(morning_star, evening_star)          repointed 2
    after    bright(evening_star) IS bright(morning_star)      congruence
             seen_by(galileo, evening_star) still believed     the repoint

A variable is a leaf, and `_identity`'s own note says *leaves only*. Nothing
refuses the merge, and `identity_of` reports it correctly.

## What does NOT follow is the BEHAVIOUR, and the reason is one line

    C. one shared ?w node                            q(a) = +
    A. two ?w nodes, no coreference                  q(a) = None
    B. two ?w nodes, MERGED before the rule is built q(a) = None
    D. two ?w nodes, built then merged               q(a) = None

`substitute` is `bindings.get(pattern, pattern)` -- a raw node-id lookup that
never consults `identity_of`. Match binds the antecedent's `?w` NODE; substitute
asks for the consequent's `?w` NODE; different keys, whatever the graph says
they are. **So the coreference is real in the index and inert in matching.**

⭐⭐⭐ **And it is a one-line change.** With `substitute` falling back to
`bindings.get(g.identity_of(pattern))`:

    two ?w nodes, MERGED                             q(a) = +

## Why it was not done, in the design's own words

`two_things_can_turn_out_to_be_one`'s docstring states the premise:

> the loader's name table decides it at intake -- *a corpus is a bound, kettle
> means one node inside it, by construction and not by inference, **which is why
> coreference does not arise in authored knowledge at all***

⭐⭐⭐ **That premise is exactly what fails for a COMPUTED description.** A
computed rule is authored knowledge whose identity is NOT settled at intake --
it is assembled over several firings, after intake, by rules. The one case the
design excluded is the case this line of work creates.

## The trade, stated rather than assumed

**For.** Variable identity stops being a mint-time engine decision (the loader's
`scope` dict) and becomes a claim a corpus can make and argue with. That is the
move this repository keeps making. It is guarded by `_merges`, so it costs
nothing until someone corefers.

**Against.** `merge` is GLOBAL and permanent; variable identity is per-rule. The
`Loader.var` comment -- *`?w` in two rules is two variables* -- is a SCOPE claim,
and merge has nowhere to put a scope now that situations are going. Merging two
rules' `?w` would make them one variable everywhere, for ever.

**And the case is already covered.** `<anchor>` -- sharing by BINDING -- handles
the computed description, and the parser refuses the version without it. The
merge route buys the ability to repair a hand-written SPLIT description, which
the entry above concludes should not be written in the first place.

> So: cheap, implementable, and currently without a use `<anchor>` does not
> already serve. Worth having on the record as the answer to *why not*, which is
> **not** "the representation cannot express it" -- it can -- but "match and
> substitute do not read it, and nothing yet needs them to."

---

# Probed 2026-08-20: a rule IS already a subgraph, and it is LOSSY

The author's point: make a rule a regular subgraph, `_rel(implies, X, Y)`, the
way the top-of-file proposal wants `rule(name, implies(...))` and
`action(move(?x,?y))` to make everything a fact.

## Half of it is already true, and the non-interning half is the good half

    <rich> = implies( { +p(?x) at ?mm as ?nn, -b(?x) }, { +q(?nn) } )

    node 1432   relation `implies`   members (1429, 1431)
    antecedent moment -> moment( entry(p(?x), +), entry(b(?x), -) )

⭐ A rule node is `implies(moment(entry(pattern, sign), ...), moment(...))`
already. It is a plain subgraph, and it is built with `Graph.instance`, which
does NOT intern:

    <plain> and <same>, textually identical      nodes 1390 and 1490

⭐⭐⭐ **That is exactly the composition distinction the interning term form
destroys.** `g.rel` interns on (relation, members), so `implies(A, B)` written
twice is ONE node -- and `RuleSet.rule` is explicit that it must be two: *two
rules that happen to say the same thing are still two rules, with different
authors, precedence and provenance*. An explicit constructor is needed for that
reason alone, whatever else it buys.

## ⚠⚠⚠ But the subgraph does not carry the whole rule

    Python Rule   ant[0] pattern=p(?x) sign=+ locus=?mm binds=?nn
    the subgraph  entry(p(?x), +)                 <- two members. Both slots GONE

So there are THREE representations of one rule, each incomplete differently:

    1. the subgraph  implies(moment(entry(p,+)...), moment(...))
                     the identity; non-interned; LOSSY -- no locus, no binds
    2. the Python Rule
                     complete, not in the graph, and a STALE INDEX (measured:
                     deposit-as-install had to MUTATE it, never re-mint)
    3. the reified facts  rule/conn/ant/con + at/names
                     complete and readable by rules, but a fourth vocabulary
                     laid over the node instead of being the node's structure

**The author's proposal is to collapse these to one, and the only thing standing
in the way is that (1) drops two slots.**

## ⭐⭐⭐ And if a rule is a subgraph, the slots get SIMPLER, not harder

`_reify_locus` explains why the slots are separate relations today: *a separate
relation rather than a sixth member of `ant`/`con`, because most members have no
locus and §5 refuses a shape whose arity varies with how much happens to be
known about it.* That argument is about `ant`/`con`, which have no node for the
member and must address it as `at(SIDE, rule, position, locus)`.

**In the subgraph the member IS a node** -- `entry(p(?x), +)` is minted by
`instance`, so it is distinct per occurrence and other facts can be about it. So
the slots hang off it directly:

    at(<entry>, ?m)          instead of   at(ANT, <rule>, 0, ?m)
    names(<entry>, ?n)       instead of   names(ANT, <rule>, 0, ?n)

...and §5 is satisfied without a varying arity, because nothing is added to
`entry` at all.

⭐ **Position stops being an argument too.** `?i` exists because `ant`/`con` are
scattered facts that must be re-sorted; a moment's members are already ordered,
so `_read_rule`'s sort-by-numeral, the `?i` in every compiling rule above, and
the side argument all go.

## What is NOT yet answered

Whether the loop can read a rule straight off the subgraph -- matching reads
`Rule.antecedent`, and nothing has been measured about doing it from
`moment(entry(...))` instead. That is the load-bearing experiment and it was not
run here.

## MEASURED: the two kinds of rule are two different representations

    a LOADED rule's node   <compile>   2 members
        implies( moment(entry(recipe(?d,?a,?c), +)),
                 moment(entry(rule(new(r)), +), entry(conn(new(r), implies), +),
                        entry(ant(new(r), ?a, +, 0), +), ... ) )

    an ADOPTED rule's node   #1554     relation None, 0 members
        live members: seen(?x) => known(?x)

⭐⭐⭐ **A loaded rule IS its subgraph. An adopted rule is a BARE NODE.** Its
content lives only in the reified `ant`/`con` facts and in the Python object.
Anything that reads a rule's structure off its node works for one kind and
returns nothing for the other -- and nothing in the engine reads it, which is
why this has never shown.

## ⚠⚠⚠ ...and reusing a node leaves BOTH readable forms describing the OLD rule

Re-making a rule on an existing node, which is what `adopt` does with the node
the graph named:

    live members  p(?y) => z(?y)
    its subgraph  moment(entry(p(?x), +)) => moment(entry(q(?x), +))
    reified       ant(<r>, p(?x), +, 0)   con(<r>, q(?x), +, 0)

All three disagree, and the two a corpus can read are both wrong. `RuleSet.rule`
mints the moments only when `node is None`, and `reify` returns early on a node
it has seen -- so a supplied node updates neither.

⚠ Not reachable today: `_adopt` declines a node that is already live
(*restating is not revising*). **It becomes reachable the moment revision is
allowed**, which is exactly what deposit-as-install does. That measurement
already found revision must MUTATE the `Rule`; this adds that it must rebuild
the subgraph and re-reify, or the node stops describing the rule.

## What the collapse would buy, and the one thing that blocks it

**Buys:** loaded and adopted rules stop being two representations; the node
cannot go stale against the rule because there is nothing left to disagree with;
`ant`/`con`/`at`/`names` and the position argument all become structure.

**Blocks:** ⭐⭐⭐ **a rule cannot build a node of runtime arity.** A moment has one
entry per member, and a consequent writes terms of arity fixed at authoring.
That is why `ant(?r, ?p, ?s, ?i)` exists as scattered facts with position as an
ARGUMENT: it is the variable-arity structure, spelled as N ground facts because N
ground facts is the only variable-arity thing a rule can produce.

> So the reified vocabulary is not a redundant second representation -- it is
> the workaround for the missing constructor. **`_rel` earns its place exactly
> here**: to make a rule a subgraph, a rule must be able to build one, and that
> needs a constructor taking a relation and a *collection* of members, not a
> term of fixed shape. Explicit composition is the requirement, not a
> preference.

⚠ Nothing in the tree has a list or `cons` idiom to build such a collection from.
That is the thing to design, and it is upstream of everything above.

# New substrate

The new substrate adds entities as first class citizens, and modifies the syntax to allow expressing concepts precisely.

Nodes in the graph can represent entities: in this case they have an atom id.

Nodes in the graph can have multiple labels.

## Representing verbs and time

"Paul is running" = there is a relationship between "paul" and "run" and the "current moment". 


"A glass ball shatters if it crashes" -> a "causes" relationship between the relationship between "crash" and "ball" and a "moment" and "shatter", the same "ball" and another "moment", and a "future" relationship between the two moments.

## Manipulating the substrate

$x denotes an entity.

Relationships are entities. $y($x, $z) :  $y is a relationship i.e. a node pointing to entities $x and $z. it can also be written as:
$y[0] = $x
$y[1] = $z

We can attach "meaning" to relationships by attaching a label to a node 

add_label(y, "loves")

so $y represents $x loves $z.

I need operators to navigate

$x.out: the set of nodes pointed by a node
$y.in: the set of nodes pointing to a node

These can be used to scope a query (to be decided how)

"real world" is a node. 

# Scopes

entities and relationships can be placed under "scopes"

# Attention checkpointing and anti-attention

Attention checkpoint saves the current frame; pop will return to it.

Anti-attention: the LHS of a rule is anti-attended (gets negative bonus to attention)

# Rule RHS
The Rules RHS is a "microprogram". It can:
- iterate over list / sets of nodes
- create new nodes: $z = new
- set or unset atom id on a node
- destroy entities
- follow pointers (in both directions)
- refer to lists by e.g. $x.out
- modify attention
- push / pop / checkpoint the frame
- call tools
- add or remove labels to nodes
- call tools or builtin functions that perform operations (e.g. the "merge" operation on atom ids)

Rules, and their microprograms, are authored, or learned via Genetic Programming


# Shape of LHS:

Examples. Each point produces a set, narrowed vs the referenced sets. Some sets could be shared by multiple rules. Variables are local to the rule. In squared brackets there is the contribution to the rule score. Not all  The overall score of the rule could be computed as sigmoid over the total, also applying optional attention multiplier on the terms (composes with a "standard" attention multiplier).  

Example (roughly represents "started running"):
$z=intake($x, $y) [+3, attention_multiplier:1.2]
$x.label = "Paul" [-2]
attentioned($x)  # special criteria - filters the attentioned nodes.
$y.label = "Runs" [+7]
$standing_before = standing($x)
before($z, $standing_before) [+8]




# Working notes, 2026-08-23

## The line

World knowledge stays declarative facts. Procedure becomes microprogram. A causal or
definitional fact inside a program body is the error case: the planner cannot find it.

`+` and `-` are already microprograms with two ops. This is a widening, not a new kind of thing.

Control flow is not baked in: the tick loop selects the next step from state via attention.
An imperative step body does not change that.

Planning is a rule that reads causal facts and assembles a plan in the graph. Not the engine
running rules backwards.

## LHS

All lines must match. No partial matches, no absent variables in the RHS.

Each line produces a set, narrowed against the referenced sets. Named sets are shareable
across rules; the sharing is authored, not inferred by a compiler.

A shared set is derived state. It needs a differential gate - network result against naive
re-match - from the first commit.

Bracketed contributions are constants, so their sum is a per-rule constant known at load.
Only the attention multipliers vary per application.

    score = sum_i c_i * m_i(what line i bound)

The real content of per-line scoring is which line the multiplier hangs on: "attention on the
event matters, attention on the participants doesn't". A rule-level priority cannot say that.

Per-line weights are the learning seam. A line shared across rules carries one weight learned
across all of them. Better conditioned than GP over bodies.

Multipliers must declare a maximum, or nothing can be bounded.

Sigmoid is order-preserving, so it does nothing for ranking. Deferred; its use is DOUBT, when
two rules score too close. Reconcile then with: doubt is a tie, a cardinal score beside an
ordinal grade.

`no` is needed. Absence, ground by construction, never the pivot.

Disjunction is still missing. Compile to a union of conjunctive branches sharing their prefix.

`attentioned($x)` is reference, not relevance gating. Deixis: which Paul. The 08-22 finding
(attention orders, cannot gate) is about ordering moves and does not apply.

Two Pauls in focus is a modelling error, like a classifier misclassifying. Not the engine's
to catch. The binding is stamped, so it is diagnosable afterwards.

`attentioned($x)` is a good anchor line: the attended pool is small and enumerable, unlike
`$x.label = "Paul"`.

Attention-as-reference and attention-as-priority should be two reads. Otherwise a scheduling
change silently changes what a rule refers to.

## Stopping

`done`, not `enough`. Two endings, two names: `done` = satisfied, `exhausted` = ran dry.

`done` pops the stack. At the ground frame it does not pop: the loop goes quiescent and the
ground frame's attention survives.

Explicit stopping kills the moving-score problem. Quiescence no longer means "nothing left to
derive", so a drifting score cannot prevent it.

Popping is a proposal arbitration can lose. An unsatisfied want at that level beats it.
Otherwise the force model in `wanting.md` is bypassed by any rule that reaches the top.

Every move applicable and nothing has popped: deposit `exhausted(<frame>)` and let a rule
decide - ask, widen, or pop. Do not stop silently. Same argument as `_declined_frame`: a stack
that quietly did nothing is indistinguishable from one that had nothing to do.

Failure mode inverts. Today's bug is stopping early; tomorrow's is never stopping. Keep the run
limit and deposit on hitting it.

## Suspension

Asking the user is suspending, not finishing. The frame stays on the stack with its attention.
The answer resumes it in the context that asked.

Two quiescent states: stack empty (finished) and stack non-empty, nothing applicable (blocked).
Only the second can be woken into context.

Tool calls block. Same mechanism as asking. One suspension mechanism, not two.

A blocking call is the last statement of a microprogram. Otherwise the continuation has to be
storable and intra-step control state becomes graph state. Two tool results = two rules chained
by the first answer arriving.

`awaiting(<frame>, <req>)` while asleep, so the agent can be asked what it is waiting on and
`again(<req>, <occasion>)` has something to fire against.

Single stack means a slow tool stalls everything below it. Deliberate choice; frames as
independent stacks is much harder to add later.

## Ground attention

Nothing pops the ground frame, so nothing erases its attention. It only grows, and attention
that includes everything discriminates nothing.

Not fading. Displacement: the ground attended set is bounded, new attention pushes old out.
Keyed on occasions, not on a timer.

An item falling off ground attention is the agent forgetting what it was talking about. Deposit
it; do not let it be a silence.

## No root

The graph is a scratchpad. Belief is already flat - an anchor node, not a per-moment record.

The cost is saying what held *then*. That is the log and snapshot design, `wanting.md` §12.
State the omission as chosen.

The ground frame is the standing position, not a write destination.

## Identity

`Graph.merge` exists (`graph.py:120`): union-find identity, full repointing, cascade on key
collapse. `unify` respects it (`rules.py:299`), the scratchpad respects it (`scratchpad.py:107`).
No rule can call it. That gap is the doc's strongest argument for microprograms - an effect
`+`/`-` provably cannot express, already built, unreachable from a rule.

`attentioned($x)` picks the referent now; `merge` records that two referents were the same
afterwards. Same problem, two timescales. One section, not two.

Open on merge: `_inert_on` is keyed on propositions, so a merge must revive spent moves on the
merged identity. `rests_on` trails and §12 observations were written under the old identity.
`_identity` is one-way - is a merge revisable, and does it belong under the gate like erasure?

## Engine state that should move to the graph

`_inert` is applications that were tried and changed nothing. Observed after applying, not
predicted. Revoked when a named proposition moves (`_inert_on`).

Decision: it should be rules, not engine. Deposit after applying (`exercised`, `rests_on` both
exist), filter before. No prediction is reintroduced.

Precedent: the precedence table was engine state, moved to graph reads, 6.42s vs 6.38s.

With `done`, inertness is no longer load-bearing for termination. Efficiency only. Not floor.

Cost: it becomes an authoring obligation. A rule that forgets `no exercised(...)` re-applies
forever, silently. A shared named line is the mitigation.

## RHS ops that break footprint readability

`for $e in $x.out: +p($e)` still declares statically that it writes relation `p`. Fine -
`by_conclusion` and `_revive` keep working at relation granularity.

Four ops do not: set/unset atom id, merge, destroy, call tools. They change what existing
propositions refer to, or whether they exist. Different kind of effect, needs its own semantics.

Why this matters, and it is the attention seam's own problem: `_instantiation`, `_went_inert`,
`_revive` and `by_conclusion` all read what a rule *would* conclude, statically. A body whose
effects are unknown until it runs degrades to the minting case - fire once per premise set,
never revive, invisible to backward answering.

So: a microprogram declares a footprint - relations it may read, relations it may write.

Bounded iteration gives termination, not bounded effect size. Nested set iteration is
polynomial and terminating. Cost should be estimable before selection, same place as footprint.

Mutation must emit a change set or delta matching breaks. Once it must, most of the declarative
consequent arrives anyway.

## Syntax conflict

`$x` is the variable sigil in the shipped surface (`+wounded($x)`). The doc uses it for
entities. `<name>` is the rigid designator. Pick.

## Measure first

Antecedent census over shipped corpora and the book's: width, shared prefixes across rules
(= shareable named sets, now that every line is a hard conjunct), computator rate, absence rate,
rules that exist only as disjunctive twins.

Score-variance census: how much of the score is per-rule constant vs multiplier. If multipliers
are near 1, top-k and branch-and-bound are not worth building.

Precedent for censusing before designing: the grade and the precedence table were both retired
by counting what corpora actually write.

## Census, run 2026-08-23

Script: scratchpad `census.py`. Sources: `ugm/rules/*.ugm`, triple-quoted corpora in
`ugm/**/*.py`, fenced blocks and `<textarea>`/`data-corpus` in `book/docs/**/*.md`.
93 chunks found, 78 loaded, 15 skipped (prose with `?` placeholders, `%`, mojibake, two
fragments referring to rules declared elsewhere). 114 distinct rules, 186 antecedent members.

What the population is: teaching corpora. The 3,740-rule corpus the earlier censuses used is
not in the tree. Every number below is about examples written to be read, so treat them as a
lower bound on width and on sharing.

    antecedent width   1: 54.4%   2: 35.1%   3: 6.1%   4: 1.8%   5: 2.6%   mean 1.63
    signs              +: 97.3%   no: 2.7% (5 members)
    computators        1.1% (2)   -- and no corpus statement can declare one; they are
                                     registered from Python via `machine.computator`
    `as $x`            1.1% (2)

Shared members (what a named set would name):

    distinct members            148
    shared by >=2 rules          22  (14.9%)
    occurrences covered          60/186  (32.3%)
    most shared    6 +wounded(?1)   5 +heat(?1,?2)   4 +disrupted(?1)   4 +booked(?2,?1)

Shared prefixes (what left-deep join sharing would buy):

    len 1    13 shared of 91 distinct, 36 rules touched
    len 2     4 shared of 46 distinct, 10 rules touched
    len 3+    0 shared

Disjunctive twins (same consequent, different antecedent):

    13 consequents, 27 rules -- 23.7% of all rules

### What it says

Shared named sets buy nothing measurable as a performance feature. All the sharing is at
length 1, and a length-1 shared set is the argument index doing its job. Only 4 two-member
prefixes are shared, across 10 rules, and nothing longer is shared at all. Keep shared sets
if they are worth it for authoring -- naming a concept once -- but do not justify them by
speed, and do not build beta memories for them.

Disjunction is the best-supported item in the whole design. Nearly a quarter of rules exist
only because a second way of reaching the same conclusion needs a second rule. That is the
"rows, not branches" cost, measured.

`no` is rare (2.7%) and unsubstitutable. Build it; do not index for it.

Mean width 1.63 means joins are mostly trivial today, so nothing in the census justifies
worst-case-optimal joins, best-first walks, or top-k machinery. If path operators (`.in` /
`.out`) land, widths rise and this number must be re-taken -- it is the trigger, not the
answer.

Score-variance census not runnable: no scored corpus exists yet.

### Side finding: the book is stale against the engine

27 chunks use retired syntax -- 19 `causes(`, 10 `-` premises. Both were removed after the
book was written (one connective; the sign collapse). Recovered by rewrite for shape counting;
unrecovered they were 36 of 93 chunks failing to parse, which would have biased the census
towards narrow rules. Independently worth fixing: these examples do not run.

# The shape, drafted against the dungeon

Source recovered: `git show 15d0ed2:ugm/rules/dungeon.ugm` (284 lines, 19 rules, deleted in
HEAD `4c69f0a`). Probe at `15d0ed2:ugm/probes/dungeon.py`, three tools: `<dice>` `roll`,
`<arith>` `calc`, `<compare>` `beats`.

It does not load on today's engine either: it uses `causes` and `-` premises, both retired.
So the port is two steps, and the first one is a control -- port to today's syntax, run it,
then port to the new shape and compare.

## Sigil: no conflict, withdraw the item

`$x` is a variable. A variable binds a node. Nodes are entities. "`$x` denotes an entity" and
"`$x` is a variable" are the same statement once entities are nodes.

`<name>` stays the rigid designator. Nothing to pick.

## LHS

One constraint per line. All must match. Authored order is the walk order unless a pivot is
chosen from the delta.

    p($x, $y)                    test: this proposition is anchored
    $z = p($x, $y)               ...and bind the instance node
    no p($x)                     absence; ground by construction; never the pivot
    $x.label = "Paul"            label test
    attentioned($x)              reference: which one
    $n = calc(sub, $h, $d)       computator: pure, evaluated inline, args ground
    $s = $x.out                  a set, as an opaque value
    [+7, m:1.2]                  optional score contribution on any line

Binding the instance node is not decoration. It is what lets two branches erase different
propositions through one consequent. See the twins below.

**Sets are opaque in the LHS.** `$s = $x.out` binds the set; it does not enumerate it. Only
the RHS iterates. This keeps one binding per application and the walk linear. Enumerating in
the LHS would make every set-valued line a cross product.

**Pure computes in the LHS, impure tools in the RHS.** A computator is asked with ground
arguments and answers with a value; it claims nothing and cannot block. A tool reaches the
world, so it blocks. That is the dividing line, and it deletes the dungeon's entire
`answered(...)` plumbing from antecedents -- see below.

## Alternatives, and the constraint that limits them

    rule <name>
      <shared lines>
      alt:
        <branch 1>   [score]
        <branch 2>   [score]
    ->
      <one consequent>

Compiles to a union of conjunctive branches sharing the prefix. Not a runtime branch.

**Every branch must bind the same variables that the consequent uses.** That is the whole
constraint, and the dungeon shows both sides of it.

## RHS

Sequential statements. Terminating: iteration only over sets already in hand.

    +p($x)  /  -p($x)            deposit, erase
    $z = new                     mint
    label $z "goblin"            add / remove a label
    merge($a, $b)                identity
    destroy($e)
    for $e in $s { ... }         bounded
    attend($x, 3) / unattend
    push(...) / pop($x) / done
    call <dice> roll(d20, hit($a,$d))     tail position only

**Footprint is derived, not declared.** Static scan of the body gives the relations written.
`for $e in $s { +p($e) }` still names `p`. Derived cannot go stale; declared can. The four ops
that cannot be scanned -- merge, destroy, set/unset atom id, call -- are named explicitly, and
they are the same four that need their own semantics anyway.

## The dungeon, ported

### `<wound>` -- the plumbing case

Today: 5 antecedent members, 9 consequent members, of which 6 are erasing the tool round-trip.

    rule <wound> = causes(
      { +hits($a, $d),
        +answered(<dice>, roll(d20, hit($a, $d)), $hitroll),
        +answered(<dice>, roll($dd, hurt($a, $d)), $n),
        +hp($d, $h),
        +answered(<arith>, calc(sub, $h, $n), $new) },
      { -attack($a, $d), -hits($a, $d),
        -hp($d, $h), +hp($d, $new), +done($a),
        -roll(d20, hit($a, $d)),
        -answered(<dice>, roll(d20, hit($a, $d)), $hitroll),
        -roll($dd, hurt($a, $d)),
        -answered(<dice>, roll($dd, hurt($a, $d)), $n) } )

New:

    rule <wound>
      $atk = attack($a, $d)
      $h_it = hits($a, $d)
      $hit = answered(<dice>, roll(d20, hit($a, $d)))
      $dmg = answered(<dice>, roll($dd, hurt($a, $d)))
      $hp  = hp($d, $h)
      $new = calc(sub, $h, $dmg)
    ->
      -$atk; -$h_it; -$hp
      +hp($d, $new)
      +done($a)
      forget $hit; forget $dmg

14 members to 6 lines and 6 statements. Three things did it:

- `calc` is a computator, not a tool, so the `answered(<arith>, ...)` round-trip disappears
  from both sides. One rule (`<subtract>`) disappears with it.
- binding the instance node means the consequent erases `$hp` rather than restating
  `-hp($d, $h)`.
- `forget $x` erases a request and its answer together. That is the corpus's own first law
  (an occasion is consumed, a fact is not) as one statement instead of four members.

**`forget` should be a builtin function, not engine vocabulary.** It is sugar over two
erasures. That it can be sugar is the argument for microprograms in one line.

### The three attack rules -- the twins case

`<hero-acts>`, `<hero-switch>`, `<hero-holds>` all conclude `attack(hero, X)`. The census said
23.7% of rules are twins; here are three of them.

    rule <hero-acts>
      turn(hero); may(hero); present(hero)
      alt:
        $intent = intends(hero, attack($t), $r); present($t)                  [+10]
        $intent = intends(hero, attack($d), $r); no present($d)
                  monster($t); present($t)                                     [+5]
    ->
      -may(hero); -$intent; +attack(hero, $t)

Both branches bind `{$intent, $t}`, which is exactly what the consequent uses. Two rules
become one.

`<hero-holds>` does not merge. It has no intent to erase, so it cannot bind `$intent`, and the
consequent would reference an unbound variable. It stays its own rule.

That is the constraint doing its job, and it is the honest cost of **all lines must match**:
under soft lines all three collapse into one rule with a preference score. Under mandatory
lines they collapse two-to-one and the third survives. The decision buys a linear walk and
pays three rules across this corpus.

### The tool round-trip -- the blocking case

Today `<swing>`, `<check-ac>`, `<hit>`, `<miss>` exist to deposit a request, notice an answer,
compare it, and clean up. `<check-ac>` exists only to ask the compare tool.

`beats` is pure -- it is an ordering, not the world -- so it is a computator, and `<check-ac>`
disappears the same way `<subtract>` did. Only `<dice>` is genuinely a tool.

    rule <swing>
      $atk = attack($a, $d)
      no answered(<dice>, roll(d20, hit($a, $d)))
    ->
      call <dice> roll(d20, hit($a, $d))         -- tail; the frame suspends here

    rule <miss>
      $atk = attack($a, $d)
      $hit = answered(<dice>, roll(d20, hit($a, $d)))
      ac($d, $c)
      no beats($hit, $c)
    ->
      -$atk; +missed($a, $d); +done($a); forget $hit

The `no beats(...)` line is a computator in negative position. That needs deciding: a
computator answers a value, and `no` asks the state. Either computators may be compared
inline (`$hit < $c`) or the negative form is refused. Comparison operators as lines is the
smaller change and reads better.

## Count

19 rules today. Ported: `<subtract>` and `<check-ac>` gone (computators), `<hero-switch>`
merged, so **16**. Members drop much further than rules do -- the win is in the consequents,
which are mostly bookkeeping.

## Decided here

`$x` stays the variable sigil; the conflict was nominal.

Sets are opaque in the LHS. The RHS iterates.

Pure computes in the LHS, impure tools blocking in the RHS tail.

Footprint derived by scan; only merge, destroy, atom id and call are declared.

Alternatives share a consequent; every branch binds what the consequent uses.

## Open after this pass

Comparison in the LHS: operator lines (`$hit < $c`) or negated computators. Operators preferred.

`forget` as builtin or as two statements.

Multiplier maximum, needed before any bound is computable.

Whether `attentioned($x)` is one line form or two (focus vs priority read).

Single stack versus frames as independent stacks. Still the one that is hard to add later.

## Built: labels on nodes, 2026-08-23

`Graph.label / unlabel / labels_of / labelled`. Suite 117/0, ten new checks under §3,
kill-probed (disabling the label transfer in `merge` fails two of them).

A label is a name that picks out a node. Several labels on one node are aliases.

**Aliasing needed no change to the interning key.** `_key` already works in identities, so
merging `adores` into `loves` makes `adores(x, z)` intern to the node `loves(x, z)` already
made. The alias semantics was already paid for by `merge`; only the name table was missing.

So multilabel is not a new representation. It is `merge`, read from the name side.

**Naming is local; labelling is a claim.** `g.atom("kettle")` twice is still two nodes, and
that is deliberate. Making `atom` resolve through the label table was built, measured and
reverted: it removed **zero** twins on `delay.ugm` (the loader's per-corpus table was already
doing the work), and it contradicts an argued position -- *two corpora may be about different
kettles and are never about different 2s* (`text.py:823`). Only an explicit `label` claims
identity.

The first `label` on a node seeds the node's existing name as a label too, so `labels_of` does
not report that a node called `loves` answers only to `adores`. Seeded at label time, never at
mint, so a corpus atom never enters the table by being written.

`unlabel` takes the name back and does **not** unmerge. The nodes are already one.

### What "set / unset atom id" turned out to be

There is no settable id -- ids are mint order. Set is `label` plus the merge it triggers.
Unset is `unlabel`, which is not the inverse: the merge stands.

**So unmerge is the real gap, and it is next.** `identity_of` walks the chain with no path
compression, and says why: *a merge is a claim and the chain is the record of the order the
claims were made in*. The data to undo one was deliberately kept.

Still open from the earlier pass, unchanged: no rule can call `merge` at all.

## Built: interning is a write policy, not a law, 2026-08-23

Suite 126/0. Nine new checks, kill-probed.

`rel(on, a, b)` returns one node however often it is built. `instance(on, a, b)` mints a
distinct one every time. Both are `on(a, b)`. A relationship may be an entity, and two of them
are two things.

**Most of this already worked.** `instance` existed, and `_mint` indexes every relation node by
relation and by argument, so a second `loves(x, z)` was already findable, matchable and
anchorable. Nothing had to be un-interned.

**One real defect, and it is the one to know about.** Absence asked the CANONICAL node:
`no p(x)` grounded its pattern through `rel`, got the interned node, and asked `holds` of that
one -- answering *nothing says it* while a second instance sat believed beside it. Fixed with
a fourth index (`_by_key`: every instance sharing one key), `Graph.like`, and
`Scratchpad.holds_any`, used at the one absence branch in `match`.

The line it draws:

    belief is per ENTITY          `holds` -- anchoring one instance anchors that instance
    absence is per PROPOSITION    `holds_any` -- `no p(x)` asks whether ANYTHING says it

A positive premise already had the right behaviour: it binds each believed instance
separately, because each is a different thing to be about.

### What was NOT done, and why

`rel` still interns. A consequent's `+p(x)` must find-or-create, or a rule that re-derives its
own conclusion mints a fresh node every tick and quiescence never arrives -- that is the
`<meet>` failure exactly, ten identical people from one `seen(alice)`.

So interning is the **default write policy**, and minting a distinct relationship is explicit.
That is the doc's `$z = new`, and it now has a substrate under it.

## Built: the inert set is gone, 2026-08-23

Removed from the engine: `_inert`, `_inert_on`, `_went_inert`, `_revive`, `_instantiation`,
the two gate hooks that fed them, and the per-candidate inert filter in `attention.py`.
Nothing decides any more that a rule has nothing further to give.

Suite 125/0. Vocabulary gate 16/0.

### The finding: it does not waste ticks, it STARVES

`worked.ugm` failed after the removal, and not because its own rules looped. `<intake>` in
`bundle.ugm` won the queue 59 ticks running and the kettle never got a turn.

So the cost of an unguarded rule is not that it repeats. It is that the first unguarded rule
owns the loop, and everything below it in the ordering never runs. Attention orders, and an
unguarded rule is permanently at the front.

### The two guard idioms, both ordinary premises

    ask for the absence of what you wrote     no says($channel, $said)
    spend what you matched                    -may(hero)

Added to `bundle.ugm` (1 rule), `worked.ugm` (3), `delay.ugm` (8), and three inline fixtures.
The second idiom is the dungeon's, and it is the older one: an occasion is consumed, and a
fact is not.

The three checks that asserted on `_inert` now assert the contract that replaced it -- a rule
whose conclusion already holds applies AGAIN, and a guarded corpus settles.

### `no <what you wrote>` is not the same claim inertness made

Inertness was keyed on the APPLICATION and revoked when the world moved under it. `no q($x)`
stops the rule whenever `q(x)` holds, whoever wrote it. Usually the same; not always -- a rule
with a second conclusion still worth writing is now blocked by the first.

That is a real difference and it is the author's to manage, which is the point.

### The probes were retired rather than repaired

`probes/attention.py`, `experts.py`, `frames.py`, `slots.py` deleted. All four were green at
HEAD and went red on the removal -- 6, 7, 1 and 7 checks -- because each carries its own
unguarded corpus.

They were not repaired, on the package's own stated policy: *a probe whose question is SETTLED
is a candidate for retirement rather than a permanent fixture.* Their findings are already
written down, the suite covers attention, frames and experts in its own sections, and git has
them if one is wanted back.

One of them should not have been repaired mechanically in any case. `probes/attention.py`
exists to test whether ordering can silently become defeat, and adding `no <conclusion>` guards
to that fixture is exactly the intervention it was built to catch: it would have gone green and
stopped measuring.

Also removed: the dead `from ..probes.dungeon import fight` branch in `gates/vocabulary.py`,
unreachable since the dungeon corpus was deleted.

### Still owed

An unguarded MINTING rule now breeds rather than spins -- `+p` is idempotent and `new` is not.
No diagnostic exists for it yet. The load-time note (a minting body whose antecedent has no
absence premise and consumes nothing) is still the cheapest catch.

## Built: `unmerge`, revisable only at the top of the record, 2026-08-23

Suite 134/0. Nine new checks, kill-probed.

`Graph.unmerge(keep, drop)` reverses a `merge` call. It is not general reversal -- it is
scoped to exactly what can be undone without guessing, and refuses (`ValueError`, naming the
reason) otherwise. Two conditions, both checked before anything is touched:

    the most recent merge     a merge is a claim and the chain is the record of the order
                               the claims were made in (`identity_of`'s own docstring); a
                               later merge may already rest on this one
    no cascade                a merge that collapses two OTHER nodes onto one key made a
                               decision on its own -- which claim survives -- and splitting
                               that back apart means guessing which claim the collapsed node
                               still stands for. Refused rather than guessed, the same
                               position the engine takes everywhere else: it computes a
                               consequence, it does not make the choice.

Both are things a caller can check in advance (`g._merge_log[-1]`), not surprises.

### The bug `unmerge` found in what was already there

`unmerge` puts `self._merges` back toward zero. Two places in `_mint` and `_index_for_merge`
were keyed on that live count as a stand-in for *has identity-indexing started*, which was a
safe equivalence right up until a count could go DOWN. A node minted in the window between an
unmerge and the next merge fell out of `_keyed`/`_mentions` silently -- indexed as though no
merge had ever happened -- so the next merge's cascade never found it and under-reported,
which is a wrong answer rather than a crash and exactly the shape this package's traps
section warns about. Fixed with a dedicated `_merge_indexed` flag that `_index_for_merge`
sets once and `unmerge` never touches. Caught by the kill-probe for `unmerge` itself before
`unmerge` was even the thing under test -- the cascade-refusal check went from failing to
passing only once this was fixed, so the fix is confirmed load-bearing rather than incidental.

### What this does not settle

Unmerging anything but the top of the record is still not possible, by design rather than by
gap -- reaching further back means deciding what a chain of dependent claims still means once
one in the middle is retracted, which is a modelling question and not a mechanical one. The
doc's own open question (*is a merge revisable, and does it belong under the gate like
erasure?*) is answered for the mechanism -- yes, narrowly -- and left open for the second
half: nothing routes `merge`/`unmerge` through `Gate` yet, so neither is licensed, logged, or
callable from a rule. That is still the doc's standing finding: *no rule can call `merge` at
all.*

## Built: two LHS predicate lines, `attentioned($x)` and a label test, 2026-08-23

Suite 139/0. Five new checks under §20, kill-probed.

The inventory before writing anything found more of the LHS already shipped than this doc
credited it with, under different spelling: `$z = p($x, $y)` **is** `p($x, $y) as $t`
(`Member.binds`, already built); `no p($x)` and inline computators (`$n = calc(...)`) are
exact matches already. What was actually missing was `attentioned($x)` and the label test,
and both landed as one new mechanism: a **predicate**, `RuleSet.predicates`, a computator's
cousin registered the same way (`rel -> function`) but answering a bool over the bound NODES
rather than a value over their shown strings -- a computator's `g.show(arg)` round-trip is
fine for arithmetic and wrong for identity, which is exactly what `attentioned`/`label` ask
about. A predicate filters; it never binds, and `match` never pivots on one, for the
computator's own reason (nothing to enumerate FROM).

Both are reserved, not corpus-registered the way a `<dice>` computator is -- every corpus
gets them, the way every corpus gets `no`. `attentioned` reads `Machine._attended()`, which
already existed; `label` reads `Graph.labels_of`, which §3's build already shipped. No parser
change was needed for either: `attentioned($x)` and `label($x, paul)` are ordinary relation
calls, and the surface already parses those.

**Not built**: `$x.label = "Paul"` dotted-attribute syntax and string literals. `label($x,
paul)` was used instead -- an atom argument, in the corpus's existing bare-name style, with
zero lexer changes. `.label`/`.out`/`.in` dotted access stay open, and widening them is the
same question as the doc's own path-operator item.

### The test that found its own bug

The first version of the label check called `g.atom("label")` twice -- once to build the
predicates dict key, once to build the rule's pattern -- and failed silently: `atom` does not
intern (§3's own rule, deliberately), so the two calls mint two different nodes and the
predicate is never found. Not an engine defect; a probe re-deriving the exact trap §10 of this
doc already named for `g.atom("x")`. Fixed by minting each reserved atom once and reusing it,
which is what a corpus gets for free from the loader's name table and what raw construction
does not.

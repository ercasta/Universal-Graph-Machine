# `selftest.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.


## `situations`

`docs/situations.md`, stages one and two: two identities per node, and
    both indices keyed by the branch that minted into them.

    The defect this closes was not in the read. Containment held for entries --
    an entry carries a locus, so it is situation-relative by construction -- and
    failed for structure, because a stratum-0 conclusion is an interned relation
    instance that belongs to no situation and is enumerated straight out of the
    argument index. No ancestry test was ever consulted on that path, so no
    amount of ancestry could have fixed it.

    ⚠ **The cap is what makes a situation a branch rather than a window.** A
    child sees its parent *as the parent stood when the child was cut*; what the
    parent mints afterwards is a later commit on another branch. Without it a
    hypothesis would watch the world change under it while it reasoned.

## `uncertainty_is_a_proposition`

There is no grade, and `@` is refused. (§10, §12)

    `@likely` was a field on an entry and a closed set of five names in Python,
    composed by weakest link on every write. It is gone, and what replaces it is
    `likely(p)`: an **ordinary proposition**, crossed into a supposition by an
    ordinary rule, coming back out wrapped.

    Measured before deleting, three ways, and they agreed:

    * `ugm.modality` already ranked the grade last of the three treatments --
      **not a term, so no rule can ask about it**; no guard to cross; does not
      nest;
    * the suite authored one in **4 of 3,740 rules** and carried one on **6 of
      32,289 entries**;
    * `weaker` was called from **exactly one place**. The grade was carried,
      composed and printed, and **nothing ever decided on it** -- this repo's
      own *read and not obeyed* defect, arriving at the floor.

    ⭐⭐⭐ **And the closed set went with it.** `GRADES` was five names Python
    knew; now a corpus may have whatever modalities it likes, with whatever
    ordering it authors. §10's *closed is a rate, not a kind*, one place
    further.

    ⚠ What is lost is that weakest link was AUTOMATIC and TOTAL. Nothing is
    concluded from an uncertain premise unless a corpus **crossed**, and what
    comes back is nested where `min` gave one ordinal. That is the trade, and
    the last check here is the price: the ordinal stops being free and becomes
    a corpus's table.

## `mention_propagates`

A rule's consequent can MENTION, and §14 said it could not.

    `+con(?r, ?pat, +)` binds `?pat` to a stored pattern, so anything concluded
    about `?pat` is a ground claim that happens to contain variables. §14 settles
    use against mention by *who is writing* -- machinery mentions, a rule uses --
    and that turned out to be too strong.

    What tells them apart is inheritance: mention propagates through bindings,
    which is checkable because the entries match consumed are already recorded
    for the trail.

    Until this, such a rule was not refused -- it was silently filtered by
    quiescence, because a conclusion still containing variables looked exactly
    like a rule with nothing left to do.

## `the_surface_can_say_what_the_apparatus_is_made_of`

The bundle is authored in the surface, so a corpus can argue with it.

    §2's expressibility criterion, applied to the apparatus itself. While the
    bundle was built in Python it was *data* in every sense the design asks for
    -- nameable, reifiable, defeasible -- except the one nobody had checked:
    that the vocabulary it is written in is the vocabulary a corpus writes in.
    Two relations were not (`arrived`, `not`), and the failure mode was silence
    rather than an error, because `Graph.atom` mints a fresh node per call. A
    corpus rule about `arrived` built a TWIN, matched nothing, and reported
    nothing -- the trap this codebase has now paid for five times.

    So these are interoperation checks, not parse checks. Each pairs a corpus
    rule against a bundled one over the same relation: if the two names were
    different nodes, the bundled half would still work and the corpus half would
    be silently dead, which is exactly what a parse check would miss.

## `a_verdict_names_what_it_settled`

*What am I stuck on?* -- answerable out loud. (§14, §19)

    `docs/quest-feedback.md` §1. Fitting `open(door1)` against
    `{ +have(?w, ?k), +opens(?k, ?d) }` subgoals `opens(?k, door1)`; the world
    satisfies it with `opens(key1, door1)`; the machinery **records
    `binds(plan, ?k, key1)`** -- and then reported `blocked(have(?w, ?k))`.

    ⭐⭐⭐ **The binding was never missing. It was known, written down, and not
    read back**, which is this repository's *read and not obeyed* defect arriving
    at the verdict. And the consequence is not cosmetic: §14 refuses to dispatch a
    generic intent, so **an agent could not say what it was stuck on** unless the
    rule's member happened to be ground. A foreign corpus shaped itself around
    that, carrying `have(p1, key1)` ground for no other reason, and reported that
    *ask for help* was a special case when it should have been the general one.

    ⚠ Instantiated at the VERDICT rather than at the subgoal, because a verdict
    is asked at quiescence -- the latest moment there is, and therefore the one
    that knows the most. When `<expand>` writes the subgoals, nothing has checked
    the siblings yet and the binding does not exist.

## `the_tick_limit_is_on_the_record`

*Did I run out of time?* -- askable at last. (§13, §21)

    ⭐⭐⭐ **A foreign corpus asked for this ahead of every feature on its list**
    (`docs/quest-feedback.md` §0). They wrote three corpora, made six rule bugs,
    and **not one produced an error**: four ran to the tick limit and two were
    silent. What the engine said about a corpus that never terminates was:

        settles      steps=  3/60   last=quiescent   exhausted=0
        runs away    steps= 60/60   last=applied     exhausted=0

    A corpus that is finished and one that never will be differed only in whether
    `len(steps)` happened to equal the limit **the caller chose**. Meanwhile the
    depth and hypothesis budgets both deposit `bounded(...)` when they bite, so
    this was not a considered position -- it was the one bound inconsistent with
    this engine's own practice. §21's defect, eleventh time.

## `silence_over_a_stretch_is_sayable`

*Nothing was declared this round* -- without negation as failure. (§9, §11)

    `docs/dungeon-feedback.md` §4 asked for negation as failure over an open
    domain: *the hero attacks by default when the player has declared nothing
    this round*, which no corpus can write as `-declares(hero, ?what)`, because
    §9's `-` needs an entry that DENIES and absence is not denial. They expressed
    the default as `overrides(<hero-acts>, <hero-holds>)` instead, and named the
    cost exactly: **the default becomes a precedence rather than a condition, so
    you cannot read the rule and learn when it applies.**

    ⭐⭐⭐ **It needed no new negation. It needed a STRETCH.** *Nothing was
    declared* has no truth conditions until you say where you looked; made
    precise it is *nothing arrived on this channel over this span*, which is
    bounded, dated, and a claim about the chain the agent already keeps. And a
    `-` on a STRUCTURAL member has meant *not derived* -- negation as failure --
    since the matchers merged.

    ⭐ **The piece that was missing was named the same morning.** The stopper was
    getting hold of the stretch: `span_of` refuses to enumerate, because any two
    moments form a span. But a moment can be named by **what was deposited
    there** -- `in_delta` and `entry_of` bind it -- and `asking` names now. Two
    bound endpoints is exactly what `span_of` mints from. So the dungeon's oldest
    open item was waiting on spans as loci and nobody knew.

    ⚠ The channel is a ground atom here. Quantifying over channels does not work,
    because a corpus relation cannot be structural: `listens(?c)` stops the rule
    being stratum 0, and then its structural members match nothing. Silence about
    a NAMED channel is sayable; silence about *any* channel is not.

## `a_guard_is_an_ordinary_member`

`unless` is *if not*, and *if not* has been built all along. (§12, §21)

    ⭐⭐⭐ **An open item that was a NAME rather than a gap.** §22 carried
    *`unless` is described and not implemented* beside spans; `compose`'s
    docstring apologised that *the half of guard inheritance §12 describes cannot
    be carried*; Appendix C listed it; and `docs/authoring.md` called it the last
    unbuilt row. All of it was one sentence away from being false:

        rule <regen> = implies( { +wounded(?x), -poisoned(?x) }, { +heals(?x) } )

    That is `unless(<regen>, +poisoned(?x))`, written where §8 says a rule's
    variables live -- **inside its own statement**. Everything that made this look
    hard came from writing the guard somewhere ELSE, where `?x` is a different
    variable and the machinery would have to re-unite them.

    ⚠ **What is genuinely absent is not `unless`, it is AMENDMENT AT A DISTANCE**
    -- adding a guard to a rule you did not write. Naming that `unless` is what
    turned a one-member rule into a missing language feature. And it is now
    deliberately refused rather than open: an ordinary rule may not reach into
    another rule's application, which is §5's wall, and amending a rule is
    harmonization's job -- the agent authors a better rule through `adopt`, where
    the amendment is itself a claim that can be argued with.

## `a_span_is_a_locus`

§11's spans, built -- and §13's worked example, run for the first time.

    §11 has said *a locus is a moment or a span* since it was written, over a
    box reading **DESCRIBED AND NOT IMPLEMENTED**, and §13's *taking turns* --
    this document's own worked example of a shape -- carried the matching one:
    *neither of those two rules can be written in any corpus this engine loads.*
    Both are discharged here.

    ⭐⭐⭐ **And the wall was not where §11 put it.** The section's costs are
    normalisation, the quadratic population and the ancestry check, and all three
    were an afternoon. What actually stood between the document and a running
    example was **three places that read a locus and ignored it** -- the write,
    quiescence, and the resolved state's key -- none of which §11 mentions,
    because each is a line that was correct exactly while every locus was a
    moment. *A wall nobody argued for*, for the fifth time in this file, and this
    time the refusals were not even refusals: they were assumptions with no
    reason to notice they had been made.

## -- §13's worked example, over the raw chain ----

-- §13's worked example, over the raw chain --------------------------
⚠ It has to read the CHAIN rather than the state, and §12 says why in
advance: *a single fact's own history is not relatable -- the superseded
entry is not in the state*. An alternation repeats its actors by
definition, so `acts(anna)` at M1 is superseded by `acts(anna)` at M3 and
the step can never see the earlier turn. §12 names the remedy in the same
breath -- *reaching that means matching over the raw chain, which is what
§6's stratum-0 read is for* -- and since `merged` that is one interpreter
rather than two.

⭐⭐⭐ So the shape is TWO rules and a third: the recogniser reads only
structure, so §6's test makes its conclusion structure; and one ordinary
rule says it, at the span, as a claim that is dated, attributed and
deniable. *One to see it, one to say it*, exactly as `reached` found.

## And containment now covers STRUCTURE, whic

⭐⭐⭐ **And containment now covers STRUCTURE, which is what
`docs/situations.md` was written about.** The check above was already
passing before situations existed and was never the whole story: it asks
the resolved state, which walks ancestry, and the leak was in the layer no
walk is consulted for. Probed then:

    is symptom(pump7, restricted) BELIEVED at the root?   None
    is it in the graph?                                   True

So negation as failure, counting, and the rules-as-facts interpreter --
every reader that enumerates instead of resolving -- could see straight
into a hypothesis. Counted rather than asserted, because the number is the
argument: a supposition of three rules mints scores of nodes, and the
claim is about all of them and not about the two anyone thought to name.

## And the same argument structurally, which

⭐⭐⭐ **And the same argument structurally, which situations found.** The
two checks above ask the resolved state, and they were passing while the
agent's own next MOMENT -- the seat it re-seated itself to, so that the
report would not read as older than everything concluded since -- was
being minted into the hypothesis's branch, because it is built as an
argument to `reseat` and the register was inside the supposition at the
time. Nothing could see it: `pred` is skeleton, so a stratum-0 rule
walking the agent's own chain would have walked off the end of it. A
successor seat was never enough on its own, and this is that sentence one
layer down.

## R2 -- the reading stays recoverable -- but it mo

R2 -- the reading stays recoverable -- but it moved from the licence to the
trail when the phase went, and that is worth stating rather than noticing.
The phase wrote a subgoal itself and stamped it `wanted`. Now `<expand>`
writes it, so its licence is `applied(<expand>)` like any rule's. What
carries the reading is one hop further back: `<expand>` consumed a `need`
entry, and `_fit` licences everything it answers `wanted(<R>, goal)`. So
the guarantee is the ordinary trail rather than a special stamp, which is
§17's own argument -- and it is now checked by walking it.

## What the phase cost, and the reason retiring it

What the phase cost, and the reason retiring it was a behavioural change
rather than a refactor: it ran ahead of recall and returned early, so while
any goal was unexpanded no ordinary rule could apply. A goal the corpus can
satisfy forwards read as blocked.
And what it did NOT fix. `<ask-check>` asks once, when the subgoal appears;
`water(kettle)` is derived forwards a few ticks later and nothing asks
again, because a request is a fact and quiescence refuses to re-conclude
one. The phase had the same blind spot for a different reason and could not
be fixed from a corpus; this one can. §21 carries the re-ask.

## And it NAMES the tap the plan committed to

⭐⭐⭐ **And it NAMES the tap the plan committed to.** This asserted
`blocked(under(kettle, ?t))` and now asserts `blocked(under(kettle, sink))`
-- the same finding with the reason in it: not *something about `under`
failed* but *the plan chose `sink`, and the kettle is not under `sink`*.
A foreign corpus reported the generic form as unutterable, since §14
refuses to dispatch a generic intent, so an agent could not say what it
was stuck on. The binding was known all along and written down as
`binds(plan, ?t, sink)`; the verdict simply never read it back.

## `rival_hypotheses_are_comparable`

Which hypothesis concluded WHAT -- §21's defect for the eighth time.

    The deleted `ugm/hypothesis.py` had `rivals(about)`, and its docstring made
    coexisting rivals the headline advantage over one-at-a-time supposition:
    *two hypotheses coexist, both readable, and choosing between them is an
    ordinary comparison.* This floor kept the first half and lost the second.
    Two suppositions about the same symptom both cross their conclusions to the
    same parent as `likely(q)`, and which frame produced which was recorded only
    as the crossed entry's LICENCE -- `concluded(<frame>)`, a Python field, so no
    rule could ask. A corpus could open rivals and then not compare them.

    Same defect and same fix as `applied(<R>)` -> `exercised`, the entry's grade
    -> the `possible` wrapper, a tool's binding -> `answers(<M>, ask)`, and the
    effort counters -> `widened`/`reached`/`bounded`: **deposit the record.**

        concluded(<frame>, <what>)     this hypothesis reached this

    The discriminating case is deliberately NOT *the two rivals disagree*. Both
    predict `wet(floor)`, which is what makes them rivals worth comparing at all;
    what tells them apart is a prediction only one of them makes. So the join is
    over a shared conclusion and a distinguishing one, and a record that merely
    said *something was concluded here* would pass the first and fail the second.

## It is a record about the frame, not a claim abou

It is a record about the frame, not a claim about the world: bookkeeping,
so a nested frame does not carry `likely(concluded(...))` out. Same
treatment `left` and `quiet` get, and for the same reason.
The record is bookkeeping, so a nested frame does not carry
`likely(concluded(...))` out -- the treatment `left` and `quiet` get.

⚠ This needs its OWN fixture, and finding that out is the finding. Asked of
the rivals above it is a check that cannot fail: they are siblings, so every
`concluded` record is written at the root and no wrapper is ever in a
position to reach one. A `concluded` has to be written INSIDE a frame for
the crossing to have anything to wrap, and only nesting puts it there.
*A fixture can only see a filter that its rules can reach* -- recorded
about a one-member antecedent, arriving here from the frame side.

## `recall_is_narrowable`

§19's first slice: recall stops proposing everything, and what narrows it
    is a knob a corpus can set.

    ⚠⚠⚠ **THE `prefer` TABLE THAT USED TO BE HERE IS GONE, AND SO IS THE
    ORDERING IT FED.** `prefer(<R>, k)` said *when k is in play, bring R to
    mind*; it named a rule id, which is what the whole retirement is about, and
    `_priority` -- the only thing that read it -- went with it. The cap now takes
    rules in AUTHORED order. The three `prefer` facts were left in this fixture
    for one run after the reader went, and they changed nothing: measured, the
    corpus with and without them recalls identically. A fixture that cannot tell
    its own subject from its absence is not testing it, so they are deleted
    rather than kept as decoration.

    ⚠⚠⚠ **AND `_recall` IS NOT ON THE TABLE LOOP'S PATH.** Instrumented, a
    `Machine.run` over this corpus calls `_recall` **zero** times -- the loop
    shortlists through the attention table instead, and the budget knob reaches
    it via `_widen`. `_recall` is still called by `ugm.quiescence`, so this is
    not dead code; but what it narrows is no longer what the agent recalls when
    it moves, and the checks below are about the knob rather than about the loop.
    Recorded here rather than fixed, because deciding where narrowing belongs is
    a design question and not a repair.

## Could that have failed? Not on THIS fixture, any

Could that have failed? Not on THIS fixture, any more, and the reason is
worth more than the check was.

It used to: with a budget of 3 the shortlist filled with bundled rules by
authored order, `<ask-fit>` was never proposed, and the verdict reported a
goal blocked that the corpus could reach. Two later changes each remove that
independently -- §14 moved *what could produce this* off the shortlist and
into `by_conclusion`, so backward reading no longer goes through `_recall`
at all; and §19's third carve-out keeps `standing` rules out of the cap, so
the apparatus cannot be narrowed away in the first place.

So the negative control is reported rather than quietly dropped: the
VERDICT half of the widening argument is now guarded twice over, and this
fixture can no longer kill the line. What still can is below -- widening is
load-bearing for reaching a conclusion, which is the other half and the one
§15 states.

## A FIXTURE THAT WAS BUILT, RUN, AND NEVER A

⚠⚠⚠ **A FIXTURE THAT WAS BUILT, RUN, AND NEVER ASSERTED ON.** It stood
here as `m5` under the comment *the line is still load-bearing, on the
fixture that can kill it*, with no `check` after it -- so the claim was
made in a comment and tested by nothing. Measured when the retirement went
past it, and **the claim is false on this fixture**: with the budget at 3
and `_widen` forced to `False`, the chain still reaches `s(a)` in 0
widenings, because `<a>`, `<b>` and `<c>` are authored first and fit
inside the cap. Burying them behind three other rules does not change it
either, because `_recall` is not on this loop's path at all (see above).

Deleted rather than repaired: the fixture cannot kill the line, and a
replacement that could would have to narrow what the TABLE loop shortlists,
which is a different mechanism and belongs with attention.

## `the_better_move_wins`

Given several applicable rules, choose the best one -- and *best* has to
    mean something the agent can point at.

    Before this, the tie among applicable, undefeated rules was broken by **the
    order they happened to be written in**. That is an accident of authoring
    deciding which move an agent makes, including the moves it cannot take back.

    What it was replaced by was already being computed and thrown away.
    `fits(<R>, w)` is `_fit`'s answer to *could this rule produce what you want*,
    so `<relevant>` turned it into a preference in one line -- and means-ends
    analysis was a bundled rule rather than a policy in the loop.

    ⚠⚠⚠ **`<relevant>` IS GONE WITH `prefer`, AND THE MOVE GOES BACK TO
    AUTHORED ORDER.** This is the sharpest thing the retirement costs, so it is
    checked rather than filed. What survives is the KNOWLEDGE: the backward
    reader still works out which rule serves the goal and still says so, in
    `fits(<toward>, nearer(a))`. What went is the translation of that into a
    number attached to a rule id -- and with it, the agent acting on it.

    Nothing replaced it because nothing could. Attention names a NODE and `fits`
    names a RULE, so *prefer the rules serving my goal* is not a sentence
    attention can say. An agent that wants it back writes the one-line rule into
    its own corpus, which is the same recourse it always had.

    Two limits it had, kept because they are what any replacement must respect:

    **Preference orders; it must not exclude.** Used to filter recall it starved
    `{+blocked(heat(?a, ?w))} => {+doing(heat(anna, ?w))}` -- the most useful rule
    in that corpus, which does not fit the goal at all. Relevance to a goal is
    silent about everything it is not about.

    **The apparatus is not a competitor.** Let loose over everything, preference
    outranked the rules that notice a surprise, so the agent pursued a goal while
    a channel was saying the world had moved. `standing` rules keep their
    authored place.

## `what_the_situation_is_about`

`_in_play` -- the one judgement in the loop that nothing argued for.

    §19 says a preference row is *matched when that key is in play* and never
    says what **in play** means. It is `Machine._in_play`: the relations in the
    current delta, plus each live goal's content and that content's relation.
    A convention, in Python, that no rule can read -- and until this it had no
    check of its own, no section, and no measurement. Every mutation of it was
    caught only incidentally, by checks about something else.

    Four variants against the same fixture as `the_better_move_wins`, which is
    the smallest thing that can tell a goal-serving rule from a useless one.

    | `_in_play` returns | first corpus move |
    |---|---|
    | as shipped | `toward` |
    | nothing | `wander` |
    | the delta only, no goals | `wander` |
    | goals only, no delta | `toward` |
    | everything the state asserts | `wander` |

    ⭐ **The key is not a subset of what is asserted**, which is the finding and
    the reason a sweep is not a substitute. Nothing ever claims `nearer(a)`; what
    is claimed is `goal(nearer(a))`. So an indiscriminate pass over every
    proposition and relation in the state -- strictly more than the shipped key
    -- still misses the one node the preference is keyed on, because the key
    reaches INSIDE a proposition for its argument. More is not nearer.

    ⚠ And the two halves are not one idea. The goal half decides this; the delta
    half decides nothing here, and over the whole suite it carries two checks,
    both about the recall BUDGET rather than about arbitration. Whether the first
    should be facts is therefore open; the second could not be, on an
    append-only chain.

    ⚠⚠ **And the two halves accumulate differently, which is what maintaining
    them found.** *A goal is never denied* was written here as the reason the
    goal half is monotone, and it is a claim about the fixtures rather than about
    the design: `{+nearer(?x)} ⟹ {-goal(nearer(?x))}` is an ordinary rule and
    denies one. So the delta half is a running union -- a moment's delta only
    grows -- and the goal half is a COUNT, because two goals can put one relation
    in play and one of them going away must not take the other's key with it.
    The last check here is that denial, and without it nothing in the suite could
    tell a maintained key set from one that never forgets.

## ...and the key set FORGETS, which is the half no

...and the key set FORGETS, which is the half nothing else here can see.
The keys are maintained where the state is rather than scanned off it, so
what puts a key in play has to be able to take it out again -- and the
only thing that does is a goal being denied. One corpus line apart, so the
control is the same run without the denying rule.
⚠ Each machine's OWN node, and the first version of this shared one. A
graph per machine means `nearer(a)` is a different node in each, so
asking machine 2's key set about machine 1's node passes whatever
happens -- the twin trap, arriving from the two-fixtures side.

## `crossing_opens_hypotheses`

Crossing a modality is **one hypothesis, and more when something says so**
    -- and the number is not a parameter anywhere.

    `likely(p)` is crossed by an ordinary rule concluding `+suppose(p, likely)`.
    Considering the other case is another such rule. So *how many branches* is
    however many `suppose` facts get concluded, gated on whatever the corpus
    gates them on: there is no `k` in the machinery to set, and adding one would
    be §18's mistake again.

    Why the default has to be one: at one branch per uncertain fact the cost is a
    frame per **derivation**, which is linear, and `ugm.modality` measures that.
    At two, n independent uncertainties give 2^n combinations.

    > **The first branch is free and every branch after it is exponential** --
    > which is exactly why the second must be earned rather than assumed.

    Two things this took that were not obvious, and both are the same shape.

## `a_hypothesis_does_not_happen`

Supposing something must not bring it about -- and the reason to insist is
    not tidiness.

    The point of opening a hypothesis about a course of action is to find out
    whether it leads anywhere unacceptable. An agent that finds that out **by
    doing it** has not considered anything. So containment has to cover effects
    before a hypothesis is any use for the question, and it did not: dispatch is
    at the write (§16), and the write never asked where it was standing.

    Measured before the fix: supposing a premise whose rule concludes
    `+doing(fire(missile))` fired the missile. Not a leak in the chain -- the
    conclusion stayed inside and crossed out wrapped, exactly as designed. The
    boundary was ignoring the register, which no amount of correct wrapping fixes
    afterwards, because the act has already happened.

    What this makes possible is the veto §19 already built for norms, used
    forward in time: **explore the branch, and see whether it is refused.**
    Nothing has to be compared -- a hypothesis that reaches a prohibition has
    answered the question by itself.

## §16's ordering trap, arriving a third time and d

§16's ordering trap, arriving a third time and deciding a design again.
Reading `enough` at the top of the tick is necessary and not sufficient:
the rule that CONCLUDES it competes like any other, so an ordinary rule
authored earlier takes one more step first. Being careful has to come
before the move it is about, and `standing` is what says so.

> **Stopping is only as prompt as the recall and arbitration of the rule
> that says stop.** That is why the third carve-out below is not a tidiness
> point: a cap that can drop the rule is a cap that can defer stopping
> indefinitely.

## `no_goal_is_dropped_silently`

An agent that can stop can stop on something it was asked for, and the
    first version of `enough` did exactly that -- silently (§19).

    Measured: with a stop rule and two goals, the run ended with the second
    neither achieved nor blocked nor pursued, and nothing anywhere recording that
    it had been open. The stop was on the record; the abandonment was not.

    The repair is a **veto**, and the argument is §19's own, transferred:

    > Recall may be incomplete about what to do. It may not be incomplete about
    > what you must not do -- or about a goal it is dropping.

    A convention every corpus must remember is the kind this design keeps finding
    it has lost, so this is not the rule a well-written corpus would have written.
    It is machinery at one decision, the third of exactly three that all make the
    same move -- **escalate before believing a decline**: `_widen` at a dry
    shortlist, `_forbid` at a write, this at a stop.

## What is deposited is a fact about the trail; wha

What is deposited is a fact about the trail; what it is worth is a claim,
so what an agent takes forward is ordinary readable corpus text.

⚠⚠⚠ **This world cannot supply a lesson any more, and that is the
rewrite showing rather than a fixture going stale.** A lesson is written
from REGRET and names a NODE; nothing here is regretted, and `<boil>` and
`<pour>`, credited above, are rules. Credit had no node-keyed sentence and
is no longer written -- so the check moves to the world that has a choice
with a cost in it, and this one keeps only the claim it can still make.

## -- and what rooted does NOT unblock, which is

-- and what `rooted` does NOT unblock, which is the finding ----------

⚠⚠⚠ Checking a root goal for SATISFACTION needs one more thing, and it is
not rootedness. With `rooted` in hand a corpus can ask -- `{+goal(?w),
+rooted(?w)} => {+check(?w, ?w)}`, the goal as its own plan, which needs no
engine change because a root goal binds nothing -- and the whole chain
fires: `root`, `rooted`, `check`. `achieved` still does not appear.

The reason is §6's OTHER item: **a request can only be made once.** The
check is asked the moment the goal appears, the state is scanned then, and
re-concluding `+check(w, w)` changes nothing, so quiescence drops it. A
goal satisfied three ticks later is never looked at again.

Measured as a contrast pair rather than asserted, because the two cases
differ only in WHEN the goal became true -- which is the whole claim.

## `a_request_can_be_re_asked`

§6's *a request can only be made once*, and §21's first of the last two hats.

    ⭐⭐⭐ **The request never needed to be fresh. The ENTRY did.** §10's two
    indices exist so that *the same claim, later* is expressible, and `deposit`
    has always taken a second entry about a proposition it has seen. What forbids
    a re-ask is `_would_change` -- quiescence -- and quiescence forbids it of a
    RULE. The machinery re-delivering a request is not a rule restating one, so
    the prohibition never covered this act.

    So the whole of it is a wrapper and one write:

        again(<request>, <occasion>)

    ordinary node, different per occasion, so concluding it is a step; and what
    the machinery does with it is write the wrapped request through the gate,
    where every answerer already listens.

## And it is bound the way a TOOL is, not the wa

⭐⭐ And it is bound the way a TOOL is, not the way the other eight
write-time hooks are -- so a corpus can see it and retire it. §21's *the
apparatus does not eat its own cooking* had been true of every one of
them: `answers(<M>, ask)` shipped with exactly zero apparatus users.

⚠ The criterion for which hooks may follow, because it is not all of them:
**a capability whose absence is the status quo ante is safe to retire.**
Deny this and each question is asked once, which is what the agent did
before and was sound. Deny `_fit` and backward reading stops, which is
§19's carve-out and a different argument.

## WHEN may a request be re-asked, and it is

⚠⚠⚠ **WHEN may a request be re-asked, and it is not free choice.** An
occasion the re-asking itself can produce warrants the next re-ask, which
produces the occasion after that. Here the author picks that trap or avoids
it with ONE WORD, and neither reading of the word is about re-asking:

  implies  the re-ask is part of this moment       -- `quiet` is once per
                                                      seat, and the seat
                                                      does not move
  causes   the re-ask moves the world on           -- so the seat moves, so
                                                      a fresh `quiet` is
                                                      written, so re-ask

Measured rather than reasoned about, because I expected the first to run
away too and it does not.

## `a_domain_can_be_taken_out_of_mind`

§19's recall, for FACTS -- the half it never had.

    The agent has always narrowed which **rules** come to mind: `dormant` until
    something claims `due`. It has never narrowed which **facts** do. The user's
    proposal, and it needs no new vocabulary -- the same relation, a second kind
    of thing, which is the design's own test that a thing belongs (rows, not
    branches).

    A domain is a **channel**: §13 already says the knowledge base is one, and
    every loaded fact is stamped with its source, so *which domain is this from*
    was already recorded and never read.

    Measured on three domains with a goal in one: 22.6s over 600 ticks with all
    of it in mind, 1.6s over 198 with two domains dormant -- **14.5x, and the
    identical 196 conclusions.** It cuts both factors at once, which is why it
    beats either cache built before it.

    ⚠ Unloading is safe to be wrong about (worst case the domain comes back),
    which is exactly why it may be an ordinary defeasible rule. §19's ESCALATION
    -- reaching for more when the search comes up dry -- may not be, and is not
    built here: §21.

## `a_hypothesis_can_be_re_entered`

The user's case: *explore a hypothesis, find you need something you do not
    have, go and get it, and finish the reasoning.*

    ⚠⚠⚠ It could not be done, and the block was one line with a reason true only
    while nothing changes: *supposing the same thing twice derives nothing new.*
    Measured -- explore `broken(pipe)`, want `wet(pipe)`, conclude nothing,
    discharge; then be told `wet(pipe)`, and the hypothesis is **never
    revisited**, not even when a corpus asks for it outright.

    ⭐ The answer is the one session resume gave: **re-enter, do not freeze.**
    Nothing is paused mid-flight -- the frame ran to quiescence and discharged
    honestly -- and what a corpus asks for is the supposition *again*, on the
    occasion of learning something. That is `again`'s own argument, so the
    licence already on the entry is the discriminator and nothing new is
    recorded to know it.

    ⚠ Note what is NOT claimed: this does not pause a half-explored hypothesis.
    A supposition still runs to quiescence inside and discharges. What it buys
    is that finding out more is a reason to think again.

## `its_own_effort_is_reasonable_over`

§21's hidden state, for the counters -- and the user's reason is the right
    one: these should be **reasonable over**.

    An agent that reached past its shortlist, or was stopped by a bound, knows
    something about its own effort. That lived in Python counters, so no rule
    could ask.

    ⭐ **Events, not counts.** A count cannot be a fact here: `widened(2)` and
    `widened(3)` are different propositions and both would hold. §17's pattern
    was always the right one -- deposit the smallest unarguable record and let
    rules say what it means, as `quiet`, `left`, `stopped` and `emitted` do. So
    the claim is *this happened here*, deduped by reading the graph, and *how
    often* stays a question nobody has had to ask.

    ⚠⚠ `_enter`'s comment has said *each reports that it was hit rather than
    stopping silently (§13)* since it was written, and the report was
    `self.exhausted += 1`. **The code claimed a property it did not have.**

## `a_session_can_be_saved_and_resumed`

A session is **what it was told**, and §3's determinism is why that is
    enough.

    Measured before building it: the same corpus reproduces the same 619 entries
    byte for byte, across four `PYTHONHASHSEED`s. So the journal -- corpora
    loaded, arrivals delivered, runs asked for -- is a complete description of
    what the agent knows, and unlike a pickle it is one a person can read, diff
    and argue with.

    ⚠⚠⚠ **Replaying a session must not re-do it.** The boundary is the one place
    effects leave and it cannot tell a repeat from a first time: resume a session
    that opened a door and the door opens again. This is `_hypothetical`'s
    argument in a second place -- supposing must not bring it about, and neither
    must remembering -- and it needs no new vocabulary, because `taken` has
    always meant *decided on and not emitted*, and the bundle already turns it
    into `did`.

## `a_scope_can_span_documents`

§13's name scope, named -- so a book can be more than one document.

    A corpus is a **bound**, and that is why coreference does not arise in
    authored knowledge: `kettle` means one node inside the bound by
    construction, not by inference, and a name outside a scope names nothing.
    The price was that each `load` had a private table, so two documents could
    not be about the same kettle and a book split into chapters was that many
    disconnected islands.

    ⚠ What this deliberately is NOT: `sameas(a, b)` in the graph. Asserting
    identity needs equals-for-equals in matching, and congruence is either
    machinery -- a decision nobody can argue with -- or a rule per relation per
    position. Deciding identity where the name is READ keeps it a construction,
    and identity discovered later becomes a **revision of intake** rather than
    an inference, which is the shape `learned()` already has for rules.

## `a_rule_can_relate_two_moments`

*The goblin acts after the hero.* (§8, §12, §20)

    §12 says a member IS an entry, and that the short form is an abbreviation
    whose locus the frame supplies. That was true of the document and false of
    the engine: `Member` was `(sign, pattern)`, so there was nowhere to put a
    locus and no rule could relate two moments. A foreign corpus answered §8 of
    `docs/authoring.md` by measuring what that cost it -- **24% of its rules
    were clock scaffold**, a round counter re-implementing a moment ordinal,
    plus a token threaded through six acting rules and an arithmetic operator
    that existed only to count rounds.

    ⭐ The matcher had the locus all along; every `Entry` carries one. What was
    missing was a **pattern** for it -- the third time in this session a wall
    turned out to be information nothing looked at.

    ⚠ **What this does NOT buy**, and the foreign corpus was asked which half it
    needed: a matcher sees the **resolved** state, one entry per proposition, so
    two *different* facts at different moments are relatable and a single fact's
    own history is not. They needed only the first and never once wanted the
    second, which is why this is what got built.

## `a_computation_happens_inside_the_application`

Arithmetic in the antecedent, and the transfer becomes atomic. (§12, §22)

    A **computator** is a function given VALUES and returning a value. It is not
    handed the machine, the frame or the entry, so it cannot reach the graph,
    the register or the world -- **purity is structural rather than declared**.
    The deleted engine proved the same property with 45 lines of transitive
    static analysis; not handing the function anything is cheaper and stronger.

    ⭐⭐⭐ **And it closes the atomicity hole.** A tool answers through the write,
    so its answer lands a tick later and a transfer is caught half-done --
    measured this session, an observer saw twelve gold where fifteen existed and
    an agent EMITTED on it. Computed during the match, the result reaches the
    same consequent in the same moment, and there is no in-between to see.

    Where it belongs is §12's **skeleton**: *conditions on the binding that
    claim nothing*, which already houses distinctness. A computator asserts
    nothing about the world; it says how the binding was built.

## The arguments must be ground when it runs, so a

The arguments must be ground when it runs, so a computator member only
computes once earlier members have bound them -- here `n(?x)` is DERIVED,
so the rule matches from a delta rather than on the opening pass.

⚠ The engine also skips pivoting on a computator, and that is an
OPTIMISATION rather than a correctness fix -- measured both ways, the
results are identical because every pivot is tried and the pass whose
pivot is the changed entry finds the applications regardless. The first
version of this comment claimed it was load-bearing; a kill-probe removing
the guard broke nothing, which is how the claim was caught. Third time
today a check's stated reason was wrong while its verdict was right.

## `a_member_can_name_what_it_matched`

`+on(?x, ?y) as ?t` -- reference, not description. (§8, §12)

    `at ?m` says WHERE an entry sits; `as ?t` says WHAT it says, under a name.
    Same one-line mechanism, and it answers a question that had two unsatisfying
    answers before it.

    A whole proposition could always be bound when it arrived as an **argument**
    -- `+tagged(?p)` binds `?p` -- and §12's `?t = on(?x, ?y)` notation, which
    binds the whole *and* its parts, is not in the surface. What a corpus did
    instead was **reconstruct**: match `+?r(?x, ?y)` and rebuild `?r(?x, ?y)`,
    which interning makes the same node, so it is genuine reference and not a
    copy. That works and costs §3's index, because a variable relation has no
    bucket (§4). This says the thing directly and keeps the index.

    ⚠ And two members hoping to co-refer -- `+tagged(?t), +on(?x, ?y)` -- is
    coincidence, not reference: nothing links them, and it appears to work only
    while there is one candidate.

## `the_skeleton_is_an_ordinary_member`

Structure, matched by an ordinary rule. (§5, §6, §11, §12)

    §12 says a skeleton member *has no sign, no locus and no licence; nobody
    asserted it*. That explains why it has no **entry** — and the engine read it
    as *therefore unmatchable*, which does not follow. `pred(M3, M2)` is an
    ordinary relation instance, a node like any other; it was simply not in the
    resolved state, which is what the matcher looked at. Stratum 0 matched the
    very same nodes, with a **second matcher** — the branch §5's *one
    interpreter* forbids and §6 explicitly disclaims (*one more row, not one
    more branch*).

    ⭐⭐⭐ **And containment survives without anything being enforced.** A
    structural member walks from an ANCHORED moment toward the root, and §11
    guarantees that direction is single-valued — *a moment has one parent;
    forking produces several successors, never several parents*. So it cannot
    reach a sibling branch. Nothing is refused to make that true: a pattern that
    would need to walk downward yields nothing, exactly as a rule matching an
    entry nobody wrote matches nothing. §4's *nothing is prohibited* holds, and
    §17's door is still open for the deliberate case — inspecting is matching,
    with an explicit anchor.

## Nothing is prohibited. A downward pattern is l

⚠ Nothing is prohibited. A downward pattern is loadable and finds nothing,
which is the same answer a rule gets for an entry nobody wrote.

⚠⚠⚠ The chain must have grown PAST the anchored moment by the time this
fires, or the check passes for the wrong reason. The first version anchored
at the newest moment, where nothing descends from it yet, and a kill-probe
permitting unanchored walks broke nothing. With `<s1>`/`<s2>` ahead of it
the same probe yields 2 where the shipped engine yields 0.

## Interning is what makes the fixpoint detectabl

⚠ Interning is what makes the fixpoint detectable, and the count has to be
taken BEFORE substitution -- `substitute` builds the grounded node with
`g.rel`, which interns, so a novelty test made afterwards always finds the
fact already present. That bug derived every fact correctly and reported
deriving nothing, so the loop stopped after one pass per layer and the
read answered from a third of its candidates. It failed as a wrong ANSWER
rather than as a crash.
⚠ Settled FIRST, then asserted -- the loop above advanced the chain, so
the seeded seat has ancestors the ordinary path never derived about, and
the first settle legitimately finds them.

## Recursion is not a cycle to be refused -- dep

⚠ Recursion is not a cycle to be refused -- `dep_after` is transitive and
reads itself -- but negation INSIDE a recursion has no stratification at
all, and refusing it loudly is the only honest answer.

⚠⚠ And the trap needs a POSITIVE rule to open it, which is the fixpoint
working from below doing something useful. A relation that only ever
appears negated in its own definition never becomes structural in the
first place -- `<y>` alone leaves `q` outside the skeleton, so the rule is
simply not stratum 0 and there is nothing to stratify. `<q0>` is what
makes `q` structure, and only then can `<y>` negate it recursively.

## A fixpoint has to be shown to REACH one,

⚠⚠⚠ **A fixpoint has to be shown to REACH one**, and *nothing new on the
second run* cannot show it: a novelty test that never fires satisfies that
trivially, and the kill-probe proved it -- breaking novelty broke zero
checks. What discriminates is a derivation deeper than one pass. A
transitive closure over a chain of five needs the layer re-run until it
settles; with novelty broken the layer runs ONCE, each rule sees a
partially built `step`, and the closure comes back short.

This is the shape of the real bug: `substitute` interns the grounded node,
so a novelty test made after it always found the fact present. Everything
derived correctly and the loop believed it had derived nothing.

## A fact's own history, on the ORDINARY loop

⭐⭐⭐ **A fact's own history, on the ORDINARY loop, ending in a claim.**
§22 recorded this as *not sized, materially harder* -- a matcher sees the
RESOLVED state, one entry per proposition, so a superseded entry is simply
not there, and reaching it means matching the raw chain and reopening §6's
bootstrap. It does not reopen it: the rule that reads the chain concludes
STRUCTURE, and a second, ordinary rule reads that structure beside an entry
and concludes a claim. Two rules, no promotion, no second matcher.

Three defects sat between the capability and a corpus being able to use
it, and none of them had a check until this one:
  * `asking` was seeded only by hand, so a corpus's chain rules were dead;
  * quiescence asked `resolve` about a conclusion that never enters the
    chain, so a stratum-0 rule applied for ever -- 60 ticks, measured;
  * a structural fact enters no delta, so the incremental matcher never
    re-triggered the rule that reads it.

## And asking must not answer. For a stratu

⚠⚠⚠ **And asking must not answer.** For a stratum-0 rule the conclusion's
EXISTENCE is the fact, so a quiescence check written with `substitute` --
which interns -- makes the conclusion exist, and whoever asks next is told
there is nothing to do. Caught by `ugm.arbitration`, which runs the fast
and slow paths over one state and reported the fast path choosing a move
the slow path found nothing for: one path's question consumed the other's
answer. Asserted here directly, because a gate that compares two paths can
only see it when the two disagree, and a pure predicate is the property.

## The DISCRIMINATING case, and the check was v

⚠⚠⚠ The DISCRIMINATING case, and the check was vacuous without it.
`<mine>` binds `?d` from the walk before `in_delta` is reached, so
removing the anchoring requirement altogether changes nothing about it
-- the kill-probe broke zero checks. The requirement only ever bites on
a member nothing has bound, and that is the member that would
enumerate the whole history and reach the sibling branch. A check about
what cannot be reached needs a fixture where there is something to
reach AND a pattern that would otherwise reach it.

## has_var is decided at mint, and an index i

⭐ **`has_var` is decided at mint, and an index is a re-implementation of
what it indexes.** It was 91% of the rule-level read -- asked of every
instance in a bucket on every enumeration, re-walking the whole structure
each time -- and deciding it once took the gate from 14.4s to 0.42s. A
node's relation and members are fixed when it is built, so its genericity
is too; the risk is not that the claim is false but that the bookkeeping
drifts, so the walked definition is kept and both are asked of every node
three loaded machines built.

## `a_half_finished_change_is_observable_and_actionable`

A transfer, mid-flight, looks exactly like a finished state. (§8, §19)

    Predicted by a foreign corpus and constructed here. Gold leaves one purse
    and enters another; with the amounts computed by a **tool** that is two
    applications, because an answer arrives through the write on a later tick.
    In between, the state is internally consistent and **false** -- nothing
    contradicts anything, there is simply a moment holding twelve gold where
    fifteen exists.

    ⚠⚠⚠ **And an ordinary rule acts on it.** *Refuse service when the party is
    short* reads the total and the agent EMITS. §19 is emphatic that an act
    cannot be forgone once emitted, so the damage is a decision rather than an
    inconsistency, and the purses are conserved throughout.

    These checks pin the CURRENT behaviour so that fixing it is visible. They
    assert the hole, which is unusual and deliberate: §22 records it as open,
    and a hole nothing asserts is one a later change can close or widen without
    anyone noticing.

## `a_reserved_name_no_longer_changes_meaning_silently`

One node with two meanings. (§5, Appendix C)

    Reported by a foreign corpus, which lost a session to it. `reserved` binds
    `plus`/`minus` to the SIGN atoms and every corpus's table is seeded from it,
    so a domain author writing an arithmetic operator gets the sign:
    `calc(minus, 5, 2)` lands as `calc(-, 5, 2)`, the tool declines a request it
    should have answered, and the run stalls with nothing saying why.

    ⚠ **A report and not a refusal, and that is forced.** `+expects(?p, plus)`
    and `+says(user, ?p, plus)` are legitimate and there are twenty-odd of them,
    so the loader genuinely cannot tell an operator from a sign. What it can do
    is stop being silent -- §5's rule about places the machinery declines
    without saying so, arriving where a name changes meaning under the author.

    ⚠ Numerals are excluded on purpose. `cost(sword, 3)` SHOULD resolve to the
    numeral the machinery uses -- that is sharing, not shadowing -- and the
    first version flagged every integer in every corpus, which is how a
    diagnostic gets ignored.

## `a_relation_can_be_named_by_a_variable`

`?p(?t)` -- the effect named by data. (§3, §5, §12)

    The substrate could always BUILD a relation instance whose relation slot is
    a variable; it is an ordinary generic node. Three separate things refused
    it and none of them was an argument: the surface would not parse it,
    `unify` compared the relation slot by identity, and `substitute` would not
    rebuild one. Nobody had asked which of those was the reason, so it read as
    a wall.

    ⭐ What it buys is *one rule instead of one fact per pair*. A catalogue
    carried as facts is otherwise **ground only**: `achieves(fireball(?t),
    burned(?t))` is refused (a fact may not hold a variable) and the named
    version parses and never fires (applying a stored pattern is `match`, which
    is floor). So an ability catalogue had to be a rule per ability.

    ⚠ **The cost is §3's index, and it lands only on an ANTECEDENT member.** A
    pattern whose relation is unknown has no bucket and takes the ANY bucket, so
    it scans -- measured at 14x the unifications on a small world with 200
    unrelated facts. In a CONSEQUENT it costs nothing at match time and is
    cheaper overall, because one rule replaces N. The advice that follows is the
    same shape §12 gives a bare-variable consequent: exact forwards, expensive
    the other way round.

## A consequent whose RELATION nothing bound is sti

A consequent whose RELATION nothing bound is still refused, exactly as one
whose argument nothing bound always was -- the gate's rule did not need to
learn about this, which is the sign it was the right place for it.
⚠⚠⚠ This used to LOAD and then quietly mint nothing, and the note here
said the gate was the right place for it. It was half right: the gate is
the right place to REFUSE, and the load is the right place to SAY SO --
which is what an unbound *argument* has always got. The two disagreed
because `_vars_in` did not look at a relation, so `?p` was never *wanted*
and the check passed vacuously. Now both are caught where the mistake is
still attributable, which is `Chain.span`'s argument for its own position.

## `a_verb_is_defined_once_and_a_world_is_declared`

Define *buying*; then declare a world in facts. (§3, §12, §20)

    The question this answers is whether an open-class vocabulary buys anything
    an author can feel: can a generic interaction be written once, in no domain
    vocabulary at all, and then a world be *declared* rather than coded?

    ⭐ The hinge is `+?kind(?item)` -- a class named by a variable. *The smith
    sells weapons* is `sells(smith, weapon)`, and applying that class to an item
    is what a relation-slot variable makes possible. Without it, `sells` could
    only ever name a particular item and every merchant would need a rule.

    Three things are checked, and the second and third are the ones that would
    make this pay in practice: a whole new trade is FACTS, a second verb reuses
    the same declarations untouched, and a class hierarchy is one ordinary rule
    -- the smith sells daggers without anything ever saying so.

## `an_amount_is_a_tool_and_an_unknown_amount_is_a_node`

*It falls by 3*, and *it rises by an unknown amount*. (§13, §16, §17, §22)

    §22 recorded these as one open item — *a value member that is constrained
    rather than bound*. They are three questions with three answers, and only
    the last is open.

    ⭐ **A known magnitude is a tool.** Arithmetic is a function, and a request
    answered by a function is what a tool IS. Nothing in the engine has to grow
    a numeral system.

    ⭐ **An unknown magnitude wants a NODE, not a slot.** Name the quantity, not
    the value, and say what is known of it — which is §13's move for plurality
    (*mint one node for the group; its size is a fact about that node*) applied
    to a scalar. The point of the third check is that it is genuinely reasoned
    with rather than merely recorded.

## The twin trap INVERTED, and this fixture i

⚠⚠⚠ **The twin trap INVERTED, and this fixture is what found it.** Not
two nodes for one name, but two ANSWERERS for one node: `_answer` calls
every answerer bound to a relation, so a corpus tool registered on
`compose` and the apparatus's own composer both fired on every such
write. They coexisted only because each declined the other's arity, which
is coincidence and not design -- and it is worse than a twin, because a
tool PROPOSES and the apparatus CONCLUDES (§19), so the corpus's tool got
a share of a request the agent acts on directly.

## `an_example_becomes_a_rule`

Two cases in, one rule out, and it applies to a third. (§17, §14)

    `generalise` is the **dual of `unify`** -- matching asks what two structures
    must agree about, anti-unification asks what they already do -- and it is
    the operation *learn from examples* is made of. It goes in `rules.py` beside
    `unify_patterns` because it is a pattern operation on the floor's own
    vocabulary; the thing that turns it into a RULE is a tool, which is where
    `adopt` said the composer has to live.

    ⭐⭐⭐ **One mapping across the premise and the conclusion.** Generalised
    separately they share no variable, so the rule concludes about something
    nothing binds and the gate refuses it. Generalised together, `door`/`window`
    becomes one `?g0` on both sides and the rule is exactly the one a person
    would have written. That single dictionary is the difference between
    learning and noise, and it is what the kill-probe removes.

    ⚠ **The tool DECLINES rather than generalising anything.** Two examples
    about different relations have a bare variable as their least general
    generalisation -- `{+?g0} => {+?g1}`, a rule that fires on everything and
    concludes nothing anyone asked for. Returning `None` is a real answer (§17),
    and the check is that nothing is adopted.

## `a_rule_can_author_a_rule`

The reverse of `reify`, and the door the whole acquisition family needs.

    A rule has been data since §14's worked example -- `rule(<R>)`, `conn`,
    `ant`, `con` -- and it went **one way**: `RuleSet.rule` was called by the
    parser and by tests and by nothing else. So the agent could answer *which
    rules do I have* and never *and now I have this one*, which is why every
    amendment was a file edit.

    ⭐⭐⭐ **And the composer has to be a TOOL, which the design settled before
    this needed it.** Three walls, each hit in order:

    * a `fact` may not contain a variable at all, so a corpus cannot write a
      rule's patterns;
    * §8 scopes a statement's variables to it, so parts written on separate
      lines could not share a `?x` even if it could;
    * a rule's consequent may only carry variables its antecedent binds, or the
      variables of an existing `<...>`-named rule -- and a rule being *built*
      is not one.

    So the corpus never names the new rule's insides. It reaches them by
    **binding**, which `artefact` established is all any rule needs: composing
    is a function, and §17 says a request answered by a function is a tool.

    ⚠ The tool PROPOSES. What lands is `answered(<builder>, ..., <R>)`, and the
    rule becomes live only because a corpus concluded `adopt(?r)` -- so an
    agent that adopts everything a tool offers is an agent whose corpus said to.

## `compose`

Builds `{+seen(?x)} => {+known(?x)}` and returns its node.

            The variable is minted here, once, and used in **both** patterns --
            which is exactly what no corpus can do, and the whole reason this
            is a function rather than a rule.

            ⚠⚠⚠ **In the CORPUS's name scope**, and the first version was not.
            `g.atom("seen")` mints a fresh node, so the rule it built was about
            a twin of `seen` and matched the corpus's `+seen(door)` never --
            adopted, live, and inert. That is `Loader.answerer`'s own argument
            arriving one level up: it made sure the tool answered the request
            the corpus could write, and this is the same requirement for what
            the tool BUILDS. *Anything that binds a name has to go through the
            table that resolves it* -- seventh time.

## `the_agent_harmonizes_itself`

Do the four pieces compose? (§2, §14, §19)

    `defeated`, `adopt`, `generalise` and the wrapper story all landed the same
    day and had never met. §2 makes composition the criterion, so this is the
    fixture that makes them meet: **learn a rule, adopt it, discover it fights
    a rule the agent already had, and settle the fight from inside.**

    ⭐⭐⭐ **It did not compose, and the break was exactly one thing.** A rule
    could conclude `overrides(<a>, <b>)`, the fact held in the graph, and the
    arbitrator never read it -- §14's precedence table was Python state seeded
    by the LOADER, once, from the surface. So:

    * an agent that reads `defeated(?l, ?w)` and wants to fix it by raising a
      precedence could not;
    * and a rule adopted at runtime could never be ordered against anything,
      because the loader's table is keyed on names a corpus declared and an
      adopted rule has none.

    §21's defect from the far side: not *the machinery knows something no rule
    can ask about*, but **a rule says something the machinery does not listen
    to** -- worse, because the corpus is not even wrong. Now the table is
    maintained from the write (`Machine._precede`), so precedence is dated and
    deniable like every other claim, and `Loader._maybe_precedence` is deleted.

    ⚠⚠ **And a conflict starves the rule that would settle it.** Two rules
    concluding opposite things about the same case oscillate -- `hot`, `cold`,
    `hot`, `cold` -- and the rule concluding the precedence never gets a turn:
    60 ticks, still going. It needs `standing`, which is §19's carve-out for
    the fifth time. This is also the loop-detection case, still unbuilt.

## This check used to assert the OPPOSITE, and the

This check used to assert the OPPOSITE, and the finding it recorded was
real: without `standing`, `<hot>` and `<cold>` undid each other for ever
and `<referee>` -- the rule that would settle the conflict -- never got a
turn. Refraction removed the starvation rather than the fixture: each
instantiation now fires once, so the pair cannot loop, the referee gets
its turn, and the run reaches quiescence in five ticks.

And the conflict is not hidden by that. `contested(<hot>, q(a))` is
deposited, which is the occasion refraction was built with precisely so
that a stopped loop does not become a silent contradiction.

## `what_a_learned_rule_may_conclude`

A learned rule that concludes WRAPPED cannot fight what it was told.

    Acquisition's normal case: the agent generalises `{+hinged(?x)} ⟹ open(?x)`
    from two examples, and it already knows `{+sealed(?x)} ⟹ -open(?x)`. A
    sealed hinged vault is a conflict; an unsealed hinged gate is not. What
    should the corpus do about it?

    Measured four ways, and the answer is *nothing*:

    | the learned rule concludes | precedence | vault | gate | ends |
    |---|---|---|---|---|
    | bare | `overrides` | `-open` | **never applies** | quiescent |
    | bare | `supersedes` | `-open` | `open` | ⚠ **runaway, 300 ticks** |
    | **wrapped** | **none** | `-open` | `likely(open)` | **quiescent, 7 ticks** |

    ⚠ **`overrides` is too broad.** It is per TICK and per RULE, so one sealed
    object suppresses the learned rule for every object -- the gate is hinged
    and not sealed, and the agent still will not conclude it is open. That is
    `rules.py`'s own warning about the two relations, met from the acquisition
    side.

    ⚠ **And `supersedes` is too narrow.** It defeats applications that share a
    consumed ENTRY, and two rules reaching the same conclusion from different
    premises share none: `<secret>` consumes `sealed(vault)`, the learned rule
    consumes `hinged(vault)`. So nothing is defeated and the two oscillate
    forever.

    ⭐⭐⭐ **So the vocabulary that looked missing is not needed.** A learned rule
    concluding `likely(open(?x))` never contradicts `-open(?x)`, because they
    are different propositions -- the agent holds a generalisation and a
    specific fact at once, which is what it should do. The conflict exists only
    if a corpus **crosses**, and then the corpus is the one asserting it and can
    decline. This is the grade deletion paying off somewhere nobody designed
    for: *how strongly a rule may speak* had to be in the conclusion for this to
    be sayable at all.

## The DEFECT, not the symptom. supersedes bein

⚠ The DEFECT, not the symptom. `supersedes` being too narrow shows
as the learned rule's bare conclusion standing despite the authored
denial -- which is what this asserts, and is true either way. How it
shows depends on the loop: the option-set loop OSCILLATES (300 ticks,
`applied`), and the table loop settles on the same wrong answer in 7
and goes quiescent. Asserting the runaway was asserting one loop's
way of being wrong, and it would have read as *fixed* when the
narrowness was untouched.

## `a_defeat_is_on_the_record`

`defeated(<loser>, <winner>)` -- §21's defect for the **tenth** time.

    Measured before building it, because *knowledge acquisition and rule
    harmonization are the pain* (Cyc) is a claim about scale and this repo's
    corpora are one author and a few days old. Over the whole suite:

    | | |
    |---|---|
    | rule pairs whose consequents unify under opposite signs | 3,551 |
    | ...where the unifier is a **bare variable** (`denial`'s `-?p`) | 3,545 |
    | ...genuinely specific | **6** |
    | ...ungoverned by an authored precedence | **1**, and it is a fixture |
    | `_defeated` asked / returning True | 19,341 / **22** |
    | distinct pairs that ever fought | **4**, all authored on purpose |

    ⭐⭐⭐ **There is not one unplanned conflict in this repository**, so a static
    conflict detector shipped today would be unfalsifiable -- 3,545 false
    positives from a single rule and one true positive already harmonized. What
    the measurement DID find is that the 22 defeats left no trace: `defeat`
    computes exactly this, uses it, and throws it away. `ugm.harmony` keeps the
    census, because the day the last column is not zero is the day a detector
    can be gated.

    ⭐ So what ships is the occasion (§19). What to do about a rule that keeps
    losing -- ask its author, raise a precedence, mark it dormant -- is a
    corpus's, and the last check here is a corpus doing it.

    ⚠ `overrides` only. A `supersedes` defeat is about a pair of APPLICATIONS,
    not a pair of rules, and there is no two-rule record to write; that is a
    scope limit rather than an oversight.

## ...and it CANNOT leave the agent, which is t

⚠⚠⚠ ...and it CANNOT leave the agent, which is the wall this fixture
found and the first thing acquisition runs into. `_dispatch` refuses a
generic intent -- *a description cannot be acted on* -- and a rule node is
generic by construction, because it holds the variables of its own
patterns. So every clarification request about a rule is decided on and
never emitted. Recorded as a check rather than fixed, because the fix is
§14's use/mention (the entry already carries `mention`) and that is a
representation decision to be scored, not slipped in.

## `a_join_is_not_a_scan`

A rule joined against itself over one relation -- **what recognition is**.

        rule <s1> = implies( { +child(?p, ?x), +child(?x, ?y) }, { +grand(?p, ?y) } )

    Reported by `pystrider`, who read the index and predicted the cause before
    measuring it, and it was a SECOND quadratic: `quiet`, `weigh`, `heap` and
    `kept` all address the option set -- n ticks, each weighing what could
    apply -- and this one has a **constant** option set and does its damage
    inside one tick. Keyed on the relation alone, member 1 draws every instance
    of `child` for each of member 0's N bindings.

    | over 1,000 facts | `unify` calls |
    |---|---|
    | as reported | 2,006,004 |
    | filed by argument too | 6,004 |
    | ...and the delta's pivot walked first | **3,003** |

    Two changes, and the second matters as much as the first: an argument index
    is no use to the member that has bound nothing yet, so a pass pivoting on
    member 1 still scanned the whole state for member 0. Walking the pivot first
    means every other member is narrowed by what it bound.

    ⚠ **What is reordered is the WALK, never the antecedent.** `consumed` is
    filled by member position, so §12's trail and `heap`'s stamp see exactly
    what authored order gives them; `ugm.arbitration` compares the move on every
    tick of every fixture and `ugm.state` the index it read.

## `a_rule_says_that_it_ran`

`exercised(<R>)` -- the claim `applied(<R>)` was already making, as a
    PROPOSITION rather than as an entry field (§14, §21).

    R5 licenses every derived entry with `applied(<R>)`, so *that this rule ran*
    has been on the trail all along -- and unreadable, because a licence is a
    Python field on the entry. That is the third thing this arc has found in that
    shape, after an entry's grade (§21 item 5) and a tool's binding before
    `answers`, and all three close the same way: put it in the graph.

    What it is FOR: **deadness as a blocked goal.** The user's framing --
    *dying is searching for a rule and finding none* -- means the machinery for
    noticing a dead rule already exists, and the only addition is being able to
    die on it. `ugm.bundle` has caught two dead rules offline this arc
    (`<relevant>` shipping blind, `+open(?w) => +verdict(?w)`); this is the same
    question asked from inside.

    ⚠⚠ **The reaction half is NOT here, and the blocker is §6's, not a new one.**
    `blocked(exercised(<R>))` is deposited whether or not the rule ran, because
    `blocked` means *no RULE fits this* -- true either way, since what concludes
    `exercised` is the machinery. The discriminator would be `achieved`, and §6
    already records that **a root goal is never checked for satisfaction**:
    `<ask-check>` keys on `subgoal(plan, ?w)`, and a goal with no plan is not
    expressible. So this ships the half that is sound and leaves the half that
    needs the root-goal check, which was already §21's.

## `a_tool_is_data`

§21's honest debt, taken: what binds an answerer to a request (§5, §17).

    A tool is not a new kind of thing. `_fit` and `_verdict` are already requests
    **answered by a function rather than by a search** -- stratum 0's escape from
    §5's wall -- and that is the only shape something outside the agent can take,
    because a search the agent cannot inspect is not reasoning it can be held to.
    What was wrong was that the binding was a Python line, so a corpus could not
    ask which tools existed, retire one, or reason about one.

    ⭐⭐⭐ **A tool proposes; it never concludes.** `answered(<M>, ask, y)` is a
    record, and an authored rule with an authored grade turns it into a claim --
    the `arrived` -> `says` path channels have had all along. Otherwise §12's
    weakest link has a link with nothing behind it and `why()` goes dark at the
    one place the agent cannot introspect.

    ⭐⭐ **One credit walk reaches rules and tools alike**, because it follows
    licences and a tool's answer carries one. That is the whole of what *jointly
    trained* honestly means: a shared credit assignment, not a shared update rule.

## `an_episode_teaches_the_next_one`

The learning loop, closed (§19). `ugm.learning` measures it; this holds it.

    Everything upstream of this existed: `review` credits, `blame` attributes a
    lost subgoal, `learned` writes surface text, and forgoing made arbitration
    into a decision instead of a schedule. What did not exist was the join, and
    the run that found it is the check below.

    ⭐⭐⭐ **Suppression is not a decision.** An episode that smashed a jug for
    water blamed the smasher and dropped it from what it recommends -- and then
    smashed the jug again, because omitting a rule leaves it exactly where it
    was: first in authored order. `learned` could say *do not recommend this*
    and could not say *do that instead*, and only the second changes a run.

    ⭐⭐ The missing half was already on the trail. `forgone(A, w)` says `A` was a
    live way of getting `w` and something else was taken, licensed by
    `applied(<winner>)` -- so a blamed winner names its own alternatives. Third
    time credit assignment has needed no new bookkeeping.

## `subgoals_make_blame_sayable`

Splitting a task into subgoals is what makes FAILURE attributable (§19).

    `review` credits and deliberately refuses to blame, because an episode that
    achieved nothing may have been an impossible one -- many rules ran, one
    outcome was bad, and nothing points at an author.

    A lost **subgoal** is different, and the difference is §9's, doing real work
    somewhere new:

    | no entry at all   | it was never reached. Many causes, no author.        |
    | an entry says `-` | something MADE it false, and that entry has a licence |

    So blame is the credit walk run over a denial instead of an assertion. What
    makes it land is that the decomposition names the damage without anyone
    anticipating it: backward reading expanded `juice(jug1)` into subgoals
    including `intact(jug1)`, so the thing the other branch broke was already a
    goal, and its loss is on the record with a licence attached.

## `taking_one_way_passes_up_the_others`

Forgoing: the thing arbitration was assumed to do and did not (§14, §18).

    Arbitration is described as choosing one rule among those that matched. What
    it did was choose one to run **first** -- the losers were deferred, and a
    loop that runs to quiescence applied every one of them eventually. Measured
    before this existed, with acts: `emitted: ['fill(kettle)', 'smash(jug1)']`.
    The agent filled the kettle AND smashed the jug.

    > **A choice that cannot be forgone is not a choice.** That is why ordering
    > could only permute a fixed amount of work, why an exact recall table bought
    > nothing, and why *choose the better rule* had no measurable content: the
    > agent took the better rule and the worse one.

    So `forgone(<R>, <w>)` -- *R was a live way of getting w and I took another*.
    A fourth way for a rule not to run, and the only one that is a **decision**:
    defeat says a rival is better, the veto says never, recall says it did not
    come to mind. This says it was reasonable and was passed up.

    Two things it is deliberately not. It is not a retraction of the goal, which
    was the first thing tried: retract it and credit cannot find what it achieved,
    and a failed act loses the want with nothing left to notice it. And it is not
    silent -- the deposit is licensed by the winner, so *what did you not do, and
    why* is answerable, which is what makes passing up recoverable.

## The judgement, stated as a check because it is

⚠ The judgement, stated as a check because it is the one place this could
be wrong: forgoing is the DEFAULT, so an agent that should have done both
under-does. That is chosen on which error is recoverable -- and this is the
recovery, as one ordinary corpus rule rather than machinery.
Note which three mechanisms have to meet for this to work, none of them
built for it: `enough` makes the agent try to stop, the veto refuses the
stop and deposits `open`, and the retry rule reads that. *What I wanted is
still outstanding, so reconsider what I passed up* -- §21's backtracking
item arriving as a consequence rather than as machinery.

## `doubt_is_a_tie`

Doubt is deposited when the agent has more than one move -- and what that
    replaced was a SCORE.

    ⚠⚠⚠ **THIS FUNCTION'S SUBJECT IS RETIRED, AND THE COST IS GATED BELOW.**
    It used to argue that a preference is a score, that

    > two rules are close exactly when they tie,

    and that this needed no threshold constant because the scale was ordinal.
    `_priority` was the only reader of that score; it is gone with `prefer`, and
    so is `Machine._close`, the tolerance test that consumed it.

    What deposits `close` now is the TABLE LOOP, on a different criterion:
    `len(window) > 1` -- the agent had more than one candidate in front of it.
    That is *I have a choice here*, not *I cannot separate these two*, and the
    difference is the whole of what was lost. An agent can no longer say it is
    doubtful **because two moves are equally recommended**, only that it has
    more than one.

    ⚠⚠ Measured before rewriting, six ways -- a bare tie, a `+prefer` row for
    the loser, that row denied, that row vetoed by a `standing` rule, and the
    tolerance knob at 9 and at 1. **All six gave the identical result**, first
    move `byA` and doubted `True`. Six checks that could no longer fail. They
    are replaced by three that can, one of which asserts the loss itself.

    ⚠ `tolerance(n)` is still parsed and still readable as a knob (`_tolerance`),
    and nothing acts on it any more. It is left standing rather than deleted
    because the knob checks in §21 are about a corpus being able to SAY a
    number, which is a separate claim -- but it steers nothing, and a corpus
    that sets it is talking to no one.

## `support_can_be_withdrawn`

*Nothing holds this up any more* -- the third negative existential, and
    the one that deliberately stops short of doing anything about it.

    §12's argument that `blocked` cannot be a rule applies unchanged: *no
    remaining support* is a claim about every entry that ever claimed `p`, and a
    `-` member says *an entry denies this*, never *for no entry*. So `support(p)`
    is asked and `unsupported(p)` answers, only ever yes.

    ⭐⭐⭐ **And the machinery does not retract.** Losing your reason is not
    acquiring a counter-reason: a source being discredited does not make what it
    told you false, it leaves you without a reason, which is a different state
    and the one you can act on. So `unsupported` is the occasion and the reaction
    is a corpus's -- tear down, re-derive, ask, or nothing. The check that this is
    real is the pair below: the same corpus with and without one line.

    ⚠ It is ASKED, never volunteered, for `blocked`'s reason: a proposition may
    rest on several things, so one withdrawal says nothing until the rest have
    been looked at. That makes it an aggregate over a finished search, which is
    why the fixture asks at `quiet` and not before.

## `a_binding_can_be_reconsidered`

The last of the four hats: *when may a binding be reconsidered?*

    It was stuck for a smaller reason than it looked. A `binds` fact has always
    been deniable -- what denying it achieves is nothing, because `_settle` then
    re-unifies and picks the same first candidate. What was missing was never a
    way to withdraw a choice; it was **a way to say what has already been tried**.

        excluded(<plan>, ?v, x)     not that one, for this plan's variable

    ⭐ A separate relation rather than a denied `binds`, deliberately. Everywhere
    else in this design a denial says *an entry denies this* and steers nothing;
    reading `-binds` as an exclusion would give `-` a second meaning in exactly
    one place. One more piece of vocabulary is the cheaper price.

    ⚠⚠⚠ **And BOTH halves are needed -- either alone is worse than neither.**
    Excluding without denying is inert, because the surviving `binds` pins the
    variable in `_settle`'s env before the exclusion is ever consulted. Denying
    without excluding **runs away**: the variable goes free, the same candidate
    is chosen again, and the rule that denied it denies it again, forever. That
    is `reask`'s criterion in a third place -- *an occasion warrants a re-ask
    only if re-asking cannot produce one* -- and here the occasion is the binding
    the re-ask itself recreates.

    ⚠⚠ The exclusion cannot be written as a corpus FACT, and finding that out
    was the turn's surprise. §8 scopes a statement's variables to it, so the `?t`
    in `fact +excluded(plan(<pour>, water(kettle)), ?t, butt)` is a different node
    from the `?t` inside `<pour>`, and the fact excludes nothing. It has to be
    CONCLUDED by a rule, which binds the plan's own variable through `binds`.
    Same wall as a norm not being revisable from the surface, arriving from the
    binding side.

## `withdrawing_a_binding_withdraws_what_used_it`

The two halves of this arc composing, and the hole that stopped them.

    `_settle` builds its env by READING the plan's bindings, and wrote its answer
    with `consumed=(e, s)` -- so a conclusion that relied on *which tap* did not
    rest on the entry that said which tap. R5 says every entry has a licence and
    a source; §12 says a conclusion is no stronger than what match consumed. Both
    were true here and both were vacuous, because the binding was not consumed.

    Three things were broken by that, and only the third was visible:

    * `unsupported` could not see a withdrawn binding -- so *reconsider a
      binding* and *notice what rested on it* did not join up, which is the
      whole point of doing them in one arc;
    * §12's weakest link could not weaken a conclusion by the grade of the
      binding it assumed -- a `@possible` tap laundering into a `@certain`
      achievement, which is the exact failure `effective_grade` exists to stop;
    * `why()` never mentioned which tap it had assumed.

    ⚠ Only the bindings the goal actually USES are consumed. Consuming the whole
    env would make every sibling's conclusion rest on every other sibling's
    choice, which is the opposite of what plan bindings are for (§18).

## A norm is a belief, and it is consulted as one -

A norm is a belief, and it is consulted as one -- resolved at the writer's
own position, so a hypothesis can carry one. But it CANNOT yet be revised
from the surface, and the reason is worth pinning rather than discovering:
a norm's argument is a description, a description is an authored statement,
and §8 scopes a statement's variables to it. So `-forbidden(doing(harm(?x)))`
written a second time is a different node saying a similar thing, and the
denial lands on nothing.

That is the project's own *never identify by name alone* arriving somewhere
new. Revising a norm needs a way to NAME one, the way `<...>` names a rule.
§21 carries it.

## ...and it never needed the name, which is worth

...and it never needed the name, which is worth pinning because the
opposite is easy to assume. Matching a rule's generic antecedent against a
stored DESCRIPTION treats the description's variables as ordinary nodes, so
`?y` binds to the stored `?x` and substitution rebuilds exactly the node
that was written. A rule refers to a norm the way it refers to a plan or a
frame: by BINDING it, not by naming it.

So naming buys authoring -- a second surface statement about a description
-- and a handle to hang ordinary facts on. It never bought reference.

## §17's every seat move is a write, which §21 ca

§17's *every seat move is a write*, which §21 carried as owed for as long
as it has existed. This fixture is the one that found the move; these are
the record of it.

⭐ **Position was always readable and the seat never was.** `at(?w, ?x)`
is an ordinary fact, which is the whole reason walkers needed no engine
support -- while the register advanced on every `causes` application and
left nothing behind but a re-minted frame node, which no rule can read.
And it is not recoverable from the chain: `pred` says the moment follows,
not that the REGISTER went there, because moments are minted for spans,
predictions and suppositions too.

## `the_chain_mirrors_nothing_of_its_own`

Every field of `Entry` and `Moment` is a cache of the graph, and this is
    what holds it to that.

    The rule this enforces: Python may keep an index to make a lookup fast; it
    may not be the only place something is known. `Entry.locus/proposition/sign`
    are members 0-2 of the entry node, `consumed` is `rests_on`, `licence` is
    `licensed_by`, `source` is `arrived_on`, `mention` is `mentioned`;
    `Moment.predecessor` is `pred`, `delta` is `in_delta`, `depth` is the length
    of the `pred` walk. `Moment.licence` is gone -- it was assigned once and read
    nowhere, while §4 claimed it was what said whether a moment was time or
    derivation.

    Without this, the two can drift silently, which is `ugm.state`'s lesson at
    one construct down: an index is a re-implementation of what it indexes.

## `a_cached_application_can_be_retracted`

§6, §12. Negation as failure on a structural member is evaluated **at
    match time**, and the delta-match cache carries applications across ticks --
    so a structural fact appearing later has to be able to take one back.

    ⚠⚠⚠ It could not. `_applications` step 0 already dropped the cursor of a
    rule whose structural relation had grown, forcing a full re-match, and that
    was correct and useless: step 2's merge skips any key already present, so
    **a re-match could only ever ADD**. The stale application survived and
    applied. Step 1 retires on a later ENTRY; a structural fact has no entry and
    sits in no delta, so that path never saw it.

    The precondition `match` states -- *a negated member names a relation whose
    derivation is finished before this rule is reached* -- holds among the strata
    and not against the ordinary loop, because `in_delta`, `delta_next`,
    `rests_on` and `licensed_by` are deposited on every write.

    ⚠ Written after the fact, and it is a kill-probe rather than a description:
    restore the add-only merge and this check fails while every other one passes.

## `a_line_of_work_can_run_dry_unnoticed`

§2: widening is global, and the record of it is bound to the wrong event.

    The harness asked for a **scoped** widening -- *this line of work found
    nothing* rather than *the machine found nothing* -- and marked the request
    checkable and unchecked, with the honest note that if the window goes empty
    often enough in practice the request evaporates. This is that measurement.

    Two lines of work in one agent, which is the shape a dungeon with a parser
    in it actually has: upkeep that always has something to do, and a reading
    that fails. The reading's floor tier is `<repair>` -- what to do with input
    nothing else understood.

    ⭐⭐⭐ **The request does not evaporate, and the mechanism is not the one the
    document names.** `m._widen()` -- the call that deposits `widened(<seat>)`
    and `reached(<seat>)` -- fires only when the window is empty after the walk
    down the whole table, and the window is never empty while upkeep has work.
    But the shortlist DOES widen, many times per run, and the floor tier IS
    eventually reached: what is missing is not the reaching, it is the RECORD.
    The loop counts its widenings in a `Report` field no rule can read.

    ⚠ And the tier is reached only once the other line of work is exhausted, so
    the agent answers the utterance after the room goes quiet rather than while
    it is being spoken to.

## `attention_is_about_a_node_not_a_rule`

§19: the table, keyed on a thing instead of on a rule.

    `prefer(<R>, key, n)` is the shipped way of saying *this is worth reaching
    for*, and everything it can say is about a RULE. So it can say *swing more
    often* and cannot say *swing at THAT one* -- and the loop takes the first
    surviving application and breaks, so which BINDING wins has always been the
    walk's decision, which is to say authoring order wearing a preference.

    `attention(x)` is the same claim about a node, and it reaches both halves:

        the binding   which of a rule's applications is taken -- EXACT, and
                      free, because `found` is already materialised
        the rule      which rules are matched at all -- APPROXIMATE, via the
                      relations the node is currently spoken of under

    ⭐ The second is a join and not a scan, which is the only reason it is
    affordable: no rule's text mentions `goblin1`, because every rule is
    generic, so *which rules are about goblin1* has no syntactic answer and its
    exact answer is the option set this loop exists not to build.

## This has now been wrong TWICE, in two diff

⚠⚠⚠ **This has now been wrong TWICE, in two different columns, and both
times it read as a finding.** First it asserted the COST, `tried` --
attending to all three ran 157 against 143 for one -- and that gap was an
accident of how much apparatus sat in the table: three more bundle rules
turned it into 193 against 195, pointing the other way, and the check
failed while nothing it was about had changed.

Then it asserted *the untaught move comes back*, and that is false too:
the queue grades by POSITION, so three attended things still have an
order, and the run goes to `r10` rather than back to `r9`.

⚠⚠⚠ And then a THIRD column, when retiring `prefer` un-reserved a name and
shifted every node id: the run now goes to `r9` after all, so *the first
rule differs from bare* is no longer true either. It was another
coincidence -- `applied[0]` is one sample of an ordering. What is asserted
below is the ordering and the COST, which is what *the lift still works*
actually means and is not a fixture's luck.

⭐⭐⭐ What naming everything actually loses is the ability to say WHICH
ONE MATTERS. Attend one thing and its rule goes first. Attend three and
the one you named does not -- some rule is still lifted, just not yours,
which is worse than no lift for a lesson trying to teach something.

## This check used to assert the opposite, an

⭐⭐⭐ **This check used to assert the opposite, and the change is the
result.** It read *with nothing taught, the walk decides* -- and it did,
because nothing put what a move wrote in front of the agent. Now the
machinery attends what a move wrote, so the move after `<spot>` is
already about the goblin `<spot>` was about, with no lesson at all.

⚠ Which means a focus lesson no longer has to teach THIS. What it teaches
is the weight -- that of the things a move touched, one matters more --
and that is what took the dungeon from 32.6 matched/move to 13.0, past
the rule-naming bigram's 17.2.

## ...and a ranking-time trigger is now REFUSED rat

...and a ranking-time trigger is now REFUSED rather than ignored.

⚠⚠⚠ It used to be accepted and silently unable to write: `_rerank` ran it
on rules that had not applied and may never apply, so a deposit from there
would have been the agent claiming to think about what it merely
considered thinking about. `_rerank` is retired with the buffs, so a `when`
trigger now reaches NOTHING -- it would load and never run. A lesson that
silently does nothing is the worst outcome available, so the surface
refuses it and says where to put it instead.

## `a_recursion_is_a_node_with_a_phase`

§18: an ordered plan cannot be guarded on the state of the world.

    Hanoi's recursion is depth-first and ORDERED -- unstack, then place, then
    restack -- and `ugm.hanoi` records four corpora that failed before this one
    worked. The fourth failure decides the shape: guards read off the world are
    ambiguous by construction, because `at(d1, x)` is equally true on the way
    out and on the way back. Measured: `<unstack>` re-fired once the sub-tower
    was replaced, recreating a want it had already met, and the agent cycled for
    ever after five correct moves.

    ⭐⭐⭐ So a call is a NODE carrying its own parameters AND its own phase,
    which is `docs/HANDOFF.md`'s *a multi-tick plan is a node, not a string*
    arriving from the failing side.

    ⚠ Minted per OCCASION, not per parameters, and Hanoi is where that stops
    being a nicety: `solve(d1, x, z, y)` occurs TWICE in a three-disk solution,
    so a call node keyed on its arguments would collide with itself and
    refraction would block the second.

## `the_action_palette_is_declared_and_discoverable`

§4: what the agent may DO, as data.

    ⭐⭐⭐ `conn(?r, causes)` was the nearest thing to an action palette and it
    answers a different question: how a rule relates to the world, not that the
    agent may deliberately do it. *Fire causes smoke* and *I may strike a match*
    are both `causes`.

    ⚠ The signature is generic, so it is MENTIONED rather than claimed -- the
    gate refuses to deposit a proposition with a variable in it, and rightly.
    `afforded(move(?x, ?y))` is a claim ABOUT a pattern, exactly as `reify`
    deposits `ant(<R>, heat(?a, ?w))`.

    ⭐ What the reification buys is the ROUND TRIP: one fallback rule ranges
    over every action, including ones declared after it was written. Without it
    a corpus needs one hand-written fallback per action, and a new action is a
    fallback nobody remembers to add.

## `a_bad_attempt_is_declined_rather_than_ignored`

§9: *nothing happened* and *nothing was wrong* are different answers.

    ⭐⭐⭐ `docs/HANDOFF.md` 19c measured the old behaviour: a policy concluding
    `do(teleport, ann, pet)` deposits it and **nothing happens**, because no
    action rule matches. That silence bounded learning safely and told the agent
    nothing. An attempt is now met by one of two declines, and they come from
    different places on purpose:

        what is LEGAL   the world model's, and a rule says it
        what EXISTS     the palette's, and only the machinery can check it

    ⚠ The machinery has to, because a rule cannot: subsumption runs the pattern
    against the entry, and here the entry is the generic one. Measured --
    `unify(move(?x,?y), move(d1,z))` is True and the reverse is False.

## `outstanding_business_is_not_dropped_in_silence`

§9: an agent may not walk away from a request without saying so.

    ⭐⭐⭐ **Low priority as a PREMISE, not a score.** A watchdog names an
    occasion only the machinery writes, so it is inert until there is nothing
    better to do -- which is what a floor score was reaching for, expressed as a
    fact instead of a number. `<give-up>` has always been one, for goals;
    `<unattended>` is the same thing for a request nobody resolved.

    ⚠⚠⚠ **Both endings, and they are disjoint.** A run that stops SATISFIED
    never goes quiet, and a run that goes quiet never stops satisfied -- Hanoi
    finishes on `enough(solved)` and writes `quiet` not once. Covering one
    leaves the other silent, which is the case `_notice_attempts` exists for.

    ⚠ And neither `quiet` nor `stopped` could carry it alone: `_halt` breaks the
    loop immediately, so a rule keyed on `stopped(...)` never gets a turn.

## `what_was_learned_is_a_document`

§20: a lesson you cannot read is a lesson you cannot argue with.

    ⭐⭐⭐ `ugm.teaching` has claimed since it was written that a lesson is *a
    document -- savable, diffable, arguable, and loadable into a corpus that was
    never taught* -- and it had no `open` and no `write` in it. The text was
    built, loaded, and dropped. This is the half that was missing, and the check
    is the ROUND TRIP: what is written out is what runs.

    ⚠ Three provenance levels over one construct, and only the marker tells them
    apart once they are in one file:

        frozen      the machinery may not touch this
        (plain)     a person wrote it
        learned     play added it

    ⚠⚠ And a learned lesson ADJUSTS rather than replaces. It used to be
    arithmetic -- two postconditions on one rule both spend, so an authored
    `boost(<R>, 5)` beside a learned `boost(<R>, 2)` was 7. With the buffs gone
    it is the absence of `unattend`: three postconditions on one rule each
    attend, and the queue ends up holding ALL of what they named. The lesson
    says *and also this*, which is the same claim without the arithmetic.

## `attention_is_a_bounded_queue`

§19: what the agent is thinking about is a QUEUE, and position is weight.

    ⭐⭐⭐ It replaces three things at once. `unattend` is unnecessary because
    eviction is displacement; `LIFE` is unnecessary because decay is by
    displacement too; and the accumulation problem cannot arise because the
    queue is bounded.

    ⭐ And the gradient is the point. `docs/HANDOFF.md` 20d measured a FLAT lift
    moving 34% of the pool by the same amount every tick -- which reorders
    nothing inside that third. Counting was tried to buy the differentiation
    back and cost the dungeon 44 conclusions; ordering gives it away for free.

    ⚠ Decay by displacement is the better notion than a timer: ten quiet ticks
    should not forget what you were doing, and ten busy ones should.

## `a_count_is_not_monotone`

§1, and the second of the design's four constraints on it.

    A count is true of a moment and the next entry can falsify it -- so
    `counted(p, 2)` and `counted(p, 3)` are different propositions and asserting
    the second leaves the first standing. That is the dungeon's `hp(g1, 5)` and
    `hp(g1, 2)` defect one layer down: an agent that believes there are two
    goblins and three.

    An authored corpus pays this by writing the denial and the assertion as a
    pair (`docs/authoring.md` §0). Nobody can write it here, because nobody but
    the machinery knows what the previous count was, so the machinery owes it.

    ⚠ **Re-asking is the corpus's job and it is the ordinary discipline**: a
    request is a fact, so it is SPENT and re-asserted. Writing the same ask
    again changes nothing and is correctly dropped -- which is the same finding
    the dungeon reported about its dice.

## `a_situation_is_materialised_from_its_deltas`

`docs/situations.md` stage 4, items 1 and 2: replay, from atoms alone.

    Three stages were built and the fourth stood in for by **capped ancestor
    visibility** -- a situation reads THROUGH to its ancestors, each step capped
    at the node counter as it stood at the cut. That computes what replay would
    have produced for the structural layer, on the way past, and it is why the
    suite did not slow down. What it gives up is the whole of this: **the graph
    is not reconstructible from the deltas, so a materialisation cannot be
    discarded**, and nodes minted inside a hypothesis live as long as the graph.

    ⭐⭐⭐ **The atom layer had a hole and only replay could find it.** A delta
    referencing atoms can NAME `healthy(paul)`; naming is not rebuilding,
    because a compound's atom is minted and deliberately not derived from its
    members'. So `_atom_members` and `_atom_leaf` are the floor: the same
    structure again, one level up, in the identity that survives its nodes.

    ⚠ **This rebuilds the structural layer and does not re-deposit the
    entries.** Re-depositing needs the locus materialised too, and a moment is
    not a node the atom layer covers. Stated rather than left to be found.

## The name is not structural and was the one t

⚠⚠⚠ The name is not structural and was the one thing replay lost. A rule
is minted as a compound and named afterwards, so `_mint` never saw
`<r>` -- 110 of 160 propositions round-tripped with identical structure
and a rendering of ninety characters of `implies(moment(entry(...)))`,
which is the exact defect `Graph.name` exists to fix, one layer down.
⚠ Asked of the RULE NODE and not of `built`, which is keyed by the
propositions a delta names -- a rule appears as a MEMBER of `rule(<r>)`
and is rebuilt recursively, so it is never a key here. The first version
of this check looked in `built` and failed while the thing it was about
was working, which is the more useful way round for a check to be wrong.

## `two_things_can_turn_out_to_be_one`

Identity: coreference decided LATE, and what it costs to decide it.

    Until now identity was settled by construction and never inferred -- the
    loader's name table decides it at intake (`text.py`: *a corpus is a bound,
    `kettle` means one node inside it, by construction and not by inference,
    which is why coreference does not arise in authored knowledge at all*), and
    interning decides it for compounds. So two nodes were one node or they were
    unrelated, and there was no third state. This is the third state, and it is
    what a language front end needs: *a man walked in; a man sat down* is two
    referents that may be one man, and intake cannot know.

    ⚠⚠⚠ **The repoint is the whole of the implementation.** `bright(morning)`
    is interned under a key naming morning's identity. Merge the two stars and
    `rel(bright, evening)` computes a key naming the NEW identity, finds
    nothing, and mints a third node -- while the original sits unreachable. Not
    a containment leak: a silent loss of what the agent already believed, which
    is worse, because nothing reports it.

## TWO VOCABULARIES, AND NO RULE MENTIONS A D

⭐⭐⭐ **TWO VOCABULARIES, AND NO RULE MENTIONS A DENOTATION.** This is what
the identity layer is FOR, and it is the answer to *must every rule be
full of `denoted by`*. `denotes` is right while a reading is uncertain and
it belongs at the boundary -- `ugm/rules/dungeon.ugm` has 19 rules and
zero of them. Once the agent COMMITS that two words name one relationship,
merging compiles that commitment into identity, and every rule written in
either vocabulary reads the other's facts unchanged.

⚠⚠⚠ It took three layers to be true, and each was silent on its own:
interning and the argument index (the candidate is filed), `unify` (the
candidate is not thrown away for having the wrong relation node), and the
STATE index plus its cache (the candidate is offered at all). With any one
missing the rule matches nothing, reports nothing, and reads as a corpus
bug -- which is exactly how it was found.

## `a_rule_can_introduce_a_thing`

`+kind`: a consequent may name something that did not exist.

    Everything a consequent could name came from a binding or was written
    literally, so *there is some new person here* was unsayable. The binding
    check refuses `+named(?p, ?x)` with `?p` unbound, and refuses it correctly --
    the gate cannot deposit a variable. `+person` says it instead: the same mark that
    already signals a node coming to be, one level down.

    ⭐⭐⭐ **One node per marker per APPLICATION**, which is what keeps two people
    called Paul apart. The mint is per occasion, not per name -- so it is the
    ANTECEDENT that individuates, and a corpus that reads the occasion gets two
    while one that reads only the name gets one. That is not a defect to fix; it
    is what the corpus asked for.

    ⚠⚠⚠ **Refraction is what stops it running away, and it already existed.**
    An instantiation fires once for a given set of premises, so a minting rule
    cannot re-fire on bindings it has used. Quiescence could never have caught
    this -- a fresh node always changes something, so a minting rule looks
    applicable for ever.

## `the_gap_between_two_spans`

`delta(<have>, <want>, <gap>)`, and why it has to be a tool.

    A rule matches one entry at a time and cannot speak about the SET of its
    matches -- the standing gap this design has recorded since aggregates were
    first asked for. *What stands between where I am and where I want to be* is
    exactly a claim about a set, so it is not a sentence the surface can say.

    `<difference>` computes it and materialises one `missing(<gap>, p)` or
    `extra(<gap>, p)` per difference. That is the half that matters: a set
    answered as a set would need something to walk it, and one entry per
    difference is read by an ordinary rule with an ordinary member. The tool
    proposes the gap; a rule decides what to want.

    A span is either a compound a corpus built -- `state(at(home), holds(p1,
    torch))`, read one deep, because `at(work)` is a proposition IN the span
    and `at` and `work` are what it is made of -- or a MOMENT, which is already
    a node and holds what is asserted there. Two kinds, one rule.

    The apparatus's own records are excluded from a moment's contents. Without
    that, a gap against the world as it stands reports `answers(<composer>,
    compose)` as something to be got rid of: 16 of them, measured, against one
    real difference.

## `a_trigger_reads_what_a_rule_is_about_to_conclude`

The engine consults a corpus's rules on another rule's conclusions.

    A trigger is an ordinary rule marked `intercepts(<T>)`. Nothing about it is
    a new kind of thing: it is recalled, matched and read exactly as any rule
    is, and what makes it a trigger is a claim a corpus can deny.

    It matches against `producing(<R>, p)` -- a fact that exists only while the
    question is being asked, and is never deposited. That is the load-bearing
    part: what a rule is ABOUT to conclude is not something the world holds,
    and a claim that outlived the question would say the rule had concluded
    something it has not.

    What a trigger concludes is read as an instruction about the delta:

        instead(p, q)    q lands where p would have
        drop(p)          p does not land at all
        anything else    lands as well, beside what the rule concluded

    So the three things asked for are one mechanism: marking is adding,
    refusing is dropping, and wrapping is replacing.

    ⭐ The wrapper case is the one that pays for it. A supposition used to be
    written by every rule carrying its own wrapper -- `worked.ugm`'s `<weather>`
    concludes `+likely(rain(?day, afternoon))` -- so *everything concluded under
    this hypothesis is uncertain* had to be said once per rule and could not be
    turned on. As a trigger it is said once, and no rule's consequent mentions
    the wrapper at all.

    Triggers run in table order and each sees the delta the one before it left,
    so two triggers on one conclusion are answerable rather than a race: with
    `<wrap>` standing, `<mark>` marks `likely(boiling(kettle))` and not
    `boiling(kettle)`.

    ⚠ A rewritten conclusion is not what the rule that licensed it said, so
    `why` names the trigger: *rewritten by `<wrap>` from `boiling(kettle)`*.
    The licence still names the application, because that is what produced the
    entry -- what changed is what it produced, and the record has to say both.

## `prohibitions_are_not_recalled`

§19's carve-out, which is the one place the design refuses to be incomplete.

    > **Recall may be incomplete about what to do. It may not be incomplete
    > about what you must not do.**

    A norm used to be a veto at the gate -- a `forbidden(<pattern>)` claim
    consulted on every write. It is a TRIGGER now: an ordinary rule marked
    `intercepts(<T>, after)` that concludes `drop` about what another rule is
    about to conclude. The carve-out survives the fold for the reason that
    always earned it -- triggers are consulted directly, never recalled, never
    ranked, never arbitrated -- and the check that earns it is unchanged:
    `recall_budget = 1`, so the agent cannot reliably bring anything to mind,
    and the forbidden act is still refused while the permitted one happens.

    ⭐ **A prohibition is a QUERY now.** A stored pattern could say only *never
    this shape*; a trigger's antecedent can ask whatever a rule can ask, and it
    says the shape where a shape belongs.

    ⚠ Two properties changed with the fold, and the fixture states both rather
    than dropping them. *Restating a norm does not deny it* is gone -- there is
    no description to restate, only a rule to name. And retiring a norm binds
    what comes AFTER: an application already refused is spent, so what was
    refused stays refused and the next thing the rule reaches is not. The old
    veto re-ran the spent application; measured, this does not, and the fixture
    checks the pump stays unharmed while the valve -- reached after the norm was
    lifted -- does not.

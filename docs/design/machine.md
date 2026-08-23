# `core/machine.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

The interpreter (§14, §16).

    Recall proposes. Match filters. Arbitrate commits. Only the last is total.

The step is *select a rule, apply it*, and object-rules and meta-rules must be
indistinguishable to it -- a flat tower, not a stacked one. There are no phases:
every convention the loop used to enact is a bundled rule or a request answered
at the write, so adding one adds rows rather than branches.

Recall is narrowable, and what narrows it is LEARNED. `attention(x)` is an
ordinary fact, and §15 is emphatic that this is the step where experience belongs
and where being wrong is recoverable -- so the seam is here, and what sits in it
is data a corpus can read, deny and edit. The rule-keyed table that used to sit
here (`prefer(<R>, k)`) is retired: it named rule ids, which go stale the moment
a rule is adopted, composed or renamed.

## The aggregate over bindings, and it is the

**The aggregate over bindings, and it is the GENERAL case of
`rooted`, `unsupported` and `blocked` rather than a fourth of them.**
A rule's antecedent is existential -- each member matches *an entry*,
so a rule says *there is an entry such that*, and a `-` member says
*an entry denies this*, never *for no `$x`*. A rule therefore sees one
binding at a time, and *there are two matches* exists only inside
`match`, which is the floor.

`docs/observations.md` §4 reaches this from four directions and they
collapse to one question -- *how many ground matches does this pattern
have here?* -- with the comparison left to a corpus:

    nothing was told about it        0
    it held throughout        counterexamples 0
    ***the*** goblin                 1
    nothing has handled this yet     0

One request, four uses, and the meaning is the corpus's own rule
rather than four bundled ones. That is *rows, not branches* at the
level of the feature itself.
The marker a consequent writes to introduce a thing, spelled `+kind`
in an argument. See `_apply`.

 **NOT in `reserved`, deliberately.** A keyword would take the word
`new` away from every corpus, and `new` is far too ordinary a word to
spend -- `ugm.vocabulary` exists to count exactly that cost and has a
check named *a reserved name turned out to be a domain word*. The mark
is reachable only from the parser, which builds this node directly, so
a corpus writing `new(car)` means its own `new` and always did.

## Not that one -- what a plan has tried and rule

*Not that one* -- what a plan has tried and ruled out for a variable.

A separate relation rather than a denied `binds`, deliberately. Reading
`-binds(<plan>, $v, sink)` as an exclusion would give `-` a second
meaning it has nowhere else: everywhere in this design a denial says
*an entry denies this*, and it steers nothing. Here it would also have
to steer a search, and a sign that means one thing in general and
something extra in one place is the kind of quiet asymmetry §5 is for
refusing. One more piece of vocabulary is the cheaper price.

## The other silent decline (§5). The loop running

The other silent decline (§5). The loop running out of work is the
third place the machinery declines and the only one that used to say
nothing at all -- so reasoning could stop with goals still open and
nothing in the graph recorded that it had. `quiet(<m>)` is that record,
and a watchdog is then an ORDINARY rule with `+quiet($m)` in its
antecedent: inert until the loop stops, which is precisely when the
aggregate it wants to compute -- *is anything still open?* -- becomes
legitimate, because the search it is an aggregate over has finished.

## The other way to be over, and the design had onl

The other way to be over, and the design had only one (§19). Running out
of work is EXHAUSTION; this is SATISFACTION -- *there is nothing more
worth doing about x*. It has to be a claim rather than a condition in the
loop, because *worth* is a judgement and §4 puts judgements in data; and
it has to exist at all because an agent that stops only when exhausted
does an amount of work its corpus fixes, so nothing it learns can make it
cheaper. Measured: an ideal recall table reached a goal in 8 ticks
instead of 734 and saved nothing, because the loop went to quiescence
anyway.

The argument is *what makes here over* -- a goal, a plan, a woken rule.
The loop never reads it; it is there so that *why did you stop?* has an
answer, which is the criterion §2 calls not-lossy.

## ...and the record that it happened. Same treatme

...and the record that it happened. Same treatment as `left`, `quiet`,
`arrived` and `emitted` (§17): the machinery deposits the smallest
unarguable thing and says nothing about what it means.

It is deliberately NOT `quiet`. `quiet` is what `<give-up>` asks its
verdict at, and `blocked` claims that no rule fits -- an aggregate over a
FINISHED search. A search that stopped because it was satisfied has not
finished, and reporting the goals it never reached as blocked is the
same unsoundness `_widen` exists to prevent, arriving from a second side.

## ...and what the machinery says instead, when it

...and what the machinery says instead, when it will not let a stop
stand. `open(<w>)` is a goal that was still outstanding at the moment
the agent tried to be done with everything.

This is §19's carve-out for the third time, and the argument transfers
verbatim. Recall may be incomplete about what to do; it may not be
incomplete about what you must not do -- or about whether to go on --
or about a goal it is dropping. A corpus can be wrong about what is
worth doing next; it may not silently abandon what it was asked for.
So this is a VETO and not a rule: consulted before the stop is made,
never proposed, never arbitrated, and it cannot be forgotten by a
corpus that did not think of it.

## ...and its opposite, which only becomes sayable

...and its opposite, which only becomes sayable once a task is split.
`harmed(<R>, <key>)`: something the agent wanted was made FALSE, and
this rule is on the support of the entry that made it so.

Episode-level failure has no author -- many rules, one bad outcome, and
nothing to attribute it to. A lost SUBGOAL has one: the negating entry
carries a licence, so the walk that finds credit finds blame by running
over a `-` instead of a `+`.

## Forgoing: the thing arbitration was assumed to d

Forgoing: the thing arbitration was assumed to do and never did.
`forgone(<R>, <w>)` says *R was a live way of getting w and I took
another one*, and it is a fourth way for a rule not to run, distinct
from all three that existed:

  dormant    (`dormant`)                  the corpus took it out
  refused    (a trigger concluded `drop`) it may never happen
  not recalled                            it did not come to mind
  FORGONE                                 it was reasonable and I chose otherwise

Only the last is a decision, and only the last needs to be **deniable**:
the alternative was good, so passing it up has to be revisable when the
goal it served turns out still open. That is why this is a deposit ABOUT
the alternative rather than a retraction of the goal -- retract the goal
and credit cannot find what it achieved, and a failed act loses the want
with nothing left to notice.

## Tools. §21's honest debt, taken: a request answe

Tools. §21's honest debt, taken: a request answered by *a function
rather than a search* is how `fit` and `verdict` escape §5's wall, and
it is the only shape in this design that a thing outside the agent can
legitimately take. What was wrong with it was never the shape -- it was
that the BINDING of answerer to request lived in Python, so a corpus
could not see which tools existed, could not retire one, and could not
reason about one. Two ordinary relations fix all three:

  answers(<M>, ask)          M answers `ask` requests. A FACT, so a
                             corpus can query it (R4) and deny it.
  answered(<M>, ask(x), y)   what M said. A record, not a claim --
                             exactly `arrived` to `says`, and the
                             corpus supplies the trust rule.

**A tool may propose; it may never conclude.** The answer is a
deposit ABOUT what the tool said, so believing it is an authored rule
with a grade. Let a tool write a belief directly and §12's weakest link
has a link with nothing behind it and `why()` stops answering -- the
not-lossy criterion failing at the one place nothing else guards.
Which name table a domain's documents were written in. Provenance
already records WHERE a fact came from (its channel); this records the
scope its names were resolved in, which is the other half and the half
a session needs to be rebuilt into the same nodes rather than twins.
 THE one `loaded` node. `Loader` minted its own with `g.atom`, which
does not intern -- so the licence the loader stamped and the licence
the machine looked for were two nodes with one name, and rendering a
session found no told facts at all. The twin trap, in the code that
exists to describe provenance.

## Re-asking. §6 recorded a request can only b

Re-asking. §6 recorded *a request can only be made once* and §21
carried it as one of the two original four hats still open.

    again(<request>, <occasion>)   ask this again, because of this

What was blocked was never the chain. §10's two indices already make
*the same claim, later* expressible, and `deposit` mints a fresh entry
for a proposition it has seen before without complaint. What forbids a
re-ask is `_would_change` -- quiescence, at the RULE level: an
application that restates what the chain already says is not a step, so
`<ask-check>` concluding `+check(p, w)` a second time is dropped.

So the missing thing is a fresh NODE, which is exactly what the design
said, and a wrapper is one. `again(req, occ)` is an ordinary node that
differs per occasion, so concluding it IS a step; and re-delivering the
wrapped request through the gate reaches whatever answers it, because
answering is an `on_write` hook and a write is a write. A tool becomes
re-askable by the same line that makes `check` re-askable, and neither
answerer learns a thing about re-asking.

## Attention: what the agent is thinking about, sai

Attention: what the agent is thinking about, said about a NODE.

    attention(x)            think about x

It is a claim about a NODE, so it survives what a rule id does not:
rules are adopted, composed and rewritten, and a lesson keyed on
`<R>` goes stale the moment they are. A lesson keyed on what is
salient transfers to a rule authored afterwards. That is why the
rule-keyed table this replaced -- `prefer(<R>, key, n)`, scored per
rule and therefore unable to say *swing at THAT one* -- is retired
rather than kept beside it.

 And it is safe by construction under the action palette: `attention`
is a FACT, so a learned rule that sets it can redirect what the agent
considers and can never act. A learned rule still cannot mint.

## §18's call stack, as facts -- the plumbing under

§18's call stack, as facts -- the plumbing under a recursive plan, and
deliberately NOT a strategy for making one.

    call($c, $args)      a call, its parameters as ONE node
    stage($c, $s)        which step of it we are on
    spawn($c, $a, $s)    ask for a sub-call, starting at stage $s
    awaits($c, $k)       $c cannot go on until $k returns
    returned($c)         it has
    advances($p, $q)     from $p, go to $q when the child returns
    closes($p)           ...or return, if $p was the last step

**The parameters are one NODE, and that is the whole of what
makes this parametric.** Written as `call($c, $d, $f, $t, $s)` the
arity is Hanoi's and no other domain can use it; written as
`call($c, tower($d, $f, $t, $s))` the arity is the domain's business
and the plumbing never sees it. Measured on two domains that share
nothing else -- Hanoi and a countdown -- over the same three rules.

 **`advances`/`closes` are DATA, not rules.** The phase order is what
differs between one recursive plan and the next, so it is a fact a
corpus deposits rather than a rule anybody writes. That is what stops
this being a second planner: the bundle supplies the stack, and the
corpus supplies the strategy.

 Spelled `awaits`/`returned`/`advances` rather than the obvious
`child`/`done`/`then`, and the reason is the census: `child` and `done`
are words a WORLD uses, and reserving one takes it from every corpus
that has a family or a task in it. These are deliberation words and
nothing else.
**The action palette, declared rather than implied.** `action
move($x, $y)` says *this is something the agent may do*, and it says
nothing about how it is done: the request is `$a` deposited, and the
world model's own rules resolve it -- or REFUSE it, which is the whole
point. An illegal move that simply fails to match is indistinguishable
from nothing having happened, and that silence is this repository's
most-recorded failure mode.

 `conn($r, causes)` was the nearest thing to this and it is the wrong
question: it says how a rule relates to the world, not that the agent
may deliberately do it. *Fire causes smoke* and *I may strike a match*
are both `causes`.

 Spelled `afforded`, and NOT `action`, because `ugm.modality` uses
`action(replace, $p)` as a DOMAIN relation -- the recommended repair
for a blocked filter. Reserving `action` took the word from it and
broke two checks. Third time this trap has been walked into in one
thread; the rule is to grep every corpus for a name before reserving
it, and it works only when it is actually run. The surface keyword is
still `action`, because a keyword is not a relation.

 The signature is generic -- `move($x, $y)` -- so it is MENTIONED
rather than claimed, exactly as a rule's own patterns are (`reify`).
The gate refuses to deposit a proposition with a variable in it, and
rightly; what is deposited here is a claim ABOUT a pattern.

## ...and asking for one. attempt(move(d1, z)) is

...and asking for one. `attempt(move(d1, z))` is the agent proposing
to act; the world model's own rules resolve it, or decline it.

**An attempt at something the palette does not afford is DECLINED
BY THE MACHINERY**, and that is the one part of this only the engine
can do. `docs/HANDOFF.md` 19c measured the alternative: a policy
concluding `do(teleport, ann, pet)` deposits it and *nothing happens*,
because no action rule matches. Nothing happening is indistinguishable
from nothing being wrong, and that silence is what this design is
against.

 Deposited, not VETOED. A vetoed attempt never existed, so the agent
cannot learn that it tried something that is not a thing -- and being
able to is the entire reason to have a palette. The machinery notes
the smallest unarguable fact and a rule decides what it means, which
is this repository's standing answer.

 Checked at the WRITE, for the reason a norm used to be checked
there and by the same route: a rule cannot ask it. Subsumption runs
`unify(generic, ground)`, and a rule's premise is the pattern and the
entry is the ground fact -- so `+afforded($a)` against a ground
attempt matches nothing. Measured: `unify(move($x,$y), move(d1,z))`
is True and the reverse is False.

## The second carve-out, and it is the mirror of §1

The second carve-out, and it is the mirror of §19's first. Norms may
not be forgotten because forgetting one is a forbidden act nobody
notices; the BUNDLE may not be forgotten because it is how the agent
reads at all. `intake` not coming to mind is not a worse plan -- it is
a report that never became a belief. Being overridable and being
forgettable are different properties, and only the first was ever
claimed for the bundle.

A fact, not a Python flag, so a corpus can make its own rules standing
and can retire one of ours.

## §19's carve-out is a trigger now

§19's carve-out. A norm is a rule marked `intercepts(<T>, after)` whose
conclusion is `drop(p)`. It is never recalled and never ranked: the loop
consults the triggers directly, which is what keeps *what you must not do*
complete while *what to do* stays incomplete-able.

Recall, as a request -- the fourth. `_recall` narrows which rules are
PROPOSED, and that cannot reach a cross product written inside an
antecedent: `<ask-fit>` used to say `+goal($w), +rule($r)` and matched
|goals| x |rules| ways however few rules were proposed. Measured, it
was 711 of 816 applications on a workload -- an agent asking every rule
it has about every goal it holds, before doing anything.

So *what comes to mind about this?* becomes a question a rule can ask.
Two moves the agent cannot tell apart. Ordinal scoring makes this
exact and constant-free: they are *close* when they tie, and the top
score being unique is what confidence would mean.

Deposited rather than acted on, because what to DO when unsure is a
claim and not machinery -- think longer, ask, suppose one and look,
take the reversible one. §14 keeps arbitration total, so a choice is
still made this tick; the record is what lets the agent know it was
not a confident one.

## ...and HOW CLOSE IS CLOSE was a knob, so it is a

...and HOW CLOSE IS CLOSE was a knob, so it is a fact: `tolerance(2)`.

 NOTHING READS IT ANY MORE. Its only consumer was `Machine._close`,
which compared two `_priority` scores; both went with `prefer`. The
table loop deposits `close` on having more than one candidate, which
needs no threshold. Kept parseable because §21's knob checks are about
a corpus being able to SAY a number -- but a corpus that sets this one
is talking to no one. See `doubt_is_a_tie`.

This is the design's first **cardinal** quantity, and it is a departure
rather than an oversight. §12 says the grade scale is ordinal and that
ordinals do not add; a preference score adds them. What that buys is a
knob that can say *within 2* instead of enumerating which pairs of
grades count as indistinguishable. What it costs is stated in §12's own
terms: two weak preferences can now outweigh one strong one, which an
ordinal scale existed to prevent. §21 carries it.

Zero by default, so the default is an exact tie and no behaviour
depends on a constant nobody chose. A rule can raise it -- which is the
reason it is a fact and not a field: an agent harder to convince when
the next step cannot be taken back writes `+tolerance(3)` while
`doing(...)` is in play, and *how careful am I being* becomes a claim
with a trail.

## The other three knobs, by the SAME argument

The other three knobs, by the SAME argument `tolerance` was made a
fact for: *how careful am I being is a claim with a trail, and a rule
can raise it before an irreversible step.* They were Python fields,
which made them the one kind of decision this design does not allow --
one nobody can ask about or argue with.

    budget(3)       how many rules recall may propose
    depth(4)        how deep a hypothesis may nest
    hypotheses(5)   how many may be open at once

The DEFAULT stays in Python, exactly as `tolerance`'s zero does: a
default nobody has to choose is not a hidden decision, it is the
absence of one.
...and what the machinery does when it reaches one, as EVENTS rather
than counts. A count cannot be a fact here: `widened(2)` and
`widened(3)` are different propositions and both would hold. §17's
pattern is the right one and was always the right one -- deposit the
smallest unarguable record and let rules say what it means, exactly as
`quiet`, `left`, `stopped` and `emitted` do.

    widened(<seat>)        recall reached past its shortlist
    reached(<seat>)        a domain was brought back out of dormancy
    bounded(<which>)       a bound stopped a supposition

 `_enter`'s comment has said *each reports that it was hit rather
than stopping silently (§13)* since it was written, and the report was
`self.exhausted += 1` -- a Python counter no rule can read. The code
claimed a property it did not have.

## The one register (§10): which node the machinery

The one register (§10): which node the machinery is currently reasoning
in. The frame itself is an ordinary node; only the pointer is
privileged.

**And it now moves TWO registers, which is the whole of stage
three** (`docs/situations.md`). The graph has a situation register for
the same reason the machine has a frame one -- minting requires
somewhere to stand -- and the two must never disagree, because a rule
matching inside a supposition reads the indices and the indices are
keyed by situation. Making this a property is what stops them: there
are five assignments to `focus` in the repository, and an engine that
kept them in step by remembering to would be one line from a leak.

## The signs as ARGUMENTS -- expects(p, plus) men

The signs as ARGUMENTS -- `expects(p, plus)` mentions a sign where
`+p` uses one.

 `unsure` is NOT load-bearing for the bundle, and the first
version of this comment said it was. Measured by deleting it: the
machine still builds, because the deviation rules carry §9's `?`
as a member SIGN (`? $p`), which the parser always accepted --
not as an argument. What is real is the ASYMMETRY it was noticed
through: two of three signs could be spoken about and the third
could only be used. `expects(p, plus)` was writable and
`expects(p, unsure)` was not, so a corpus could say *I expected it
to hold* but not *I expected to be unable to say* -- which §9
insists is a claim and not the absence of one. Exercised by
`the_surface_can_say_what_the_apparatus_is_made_of`, because a
vocabulary entry with no user is the thing `ugm.bundle` exists to
catch.

## A session is what it was TOLD. Everythin

**A session is what it was TOLD.** Everything that entered from
outside, in order: corpora loaded, arrivals delivered, runs asked for.
Saving that rather than the object graph is what §3's determinism is
worth -- measured across four hash seeds, the same inputs reproduce
the same 619 entries byte for byte -- and it keeps the save file
READABLE and arguable where a pickle would be neither.
Which document is being read right now, so a rule's reification is
stamped with it. A rule had no provenance at all: `RuleSet.rules` is a
Python list, and nothing said which corpus authored which rule.

## Machinery vocabulary: requests, not claims. Noth

Machinery vocabulary: requests, not claims. Nothing carries these out of
a frame.

`doing` is deliberately NOT here. It is a request, but it is a request
about the world rather than about the machinery, and *what I would do
under this hypothesis* is the one thing a hypothesis about a course of
action is FOR. Kept as bookkeeping, an agent that supposed a premise
and found it would fire a missile came back knowing nothing at all.
What crosses is `likely(doing(...))`, which no dispatch matches --
the boundary keys on `doing`, and a wrapped intent is a claim, not an
intent. This is the closed set of §10 growing by one, and it is a real
cost -- worth listing rather than letting it accumulate (§5).

## A seat move is the machinery's record of its own

A seat move is the machinery's record of its own
advance, not a claim about the supposed world, so
a wrapper has nothing to qualify: without this a
`causes` rule applied under a hypothesis carried
`likely(moved(...))` out of it -- the agent
hedging about where it had been standing. Caught
by `a_cause_moves_the_register`, which is the
fixture that asked for the seat move in the first
place.

## The apparatus eats its own cooking. ans

**The apparatus eats its own cooking.** `answers(<M>, ask)` was
built so that a TOOL's binding could be data -- visible, queryable,
deniable -- and it shipped with exactly zero apparatus users: every
request the machinery answered, it answered because a Python line in
this constructor said so. That is §21's most frequent defect in this
codebase, stated as *something the machinery knows and no rule can ask
about*, and it is the same one `exercised`, the entry's grade and a
tool's binding each closed. The fix is always the same: put it in the
graph.

Six requests, six bindings, all of them facts:

  <fit>       fit      could this rule produce this goal?
  <settle>    check    is this goal already satisfied, in these bindings?
  <verdict>   verdict  did ANYTHING fit it?  -- the aggregate
  <root>      root     is this what I was asked for?
  <remember>  recall   what comes to mind about this?
  <re-ask>    again    ask that again, because of this

 **Deniable is not the same as forgettable, and only two of them
are both.** The criterion is not preference:

> **A capability whose absence is the status quo ante is safe to
> retire.** Deny `<re-ask>` and each question is asked once; deny
> `<root>` and the general stop rule never fires and the agent runs to
> quiescence. Both are what it did before the commit that added them,
> and both were sound.

The other four are §19's carve-out arriving a fifth time -- deny
`<fit>` or `<settle>` and backward reading stops; deny `<verdict>` and
a goal nothing can reach is never reported blocked. So they are marked
`standing`, which is the fact the bundle already uses for exactly this
claim: **overridable but not forgettable**, and `_answer` records a
refusal rather than obeying. A corpus can still argue with any of
them; it cannot make the agent stop reading.

 **`<remember>` is the fourth, and I put it in the safe column
first.** The reasoning was *narrowing off means exhaustive recall,
which is the default* -- and it is wrong about which thing this
answers. `_remember` is not the narrowing; it is the ANSWER to the
recall request, and `<ask-fit>` keys on `recalled($r, $w)`, so nothing
asks `fit` about anything without it. Measured on a goal reachable
only backwards: 15 ticks and two subgoals becomes 4 ticks and none.
The narrowing lives in attention and the budget, which are separately
deniable and were what the criterion was actually about.

## Attention is a bounded QUEUE, newest first

**Attention is a bounded QUEUE, newest first** -- what replaces
`unattend`, `LIFE` and the accumulation problem at once. Position IS
the strength, so the lift is not flat: `docs/HANDOFF.md` 20d measured
a flat one moving 34% of the pool by the same amount every tick,
which reorders nothing inside that third.

 And it decays by DISPLACEMENT rather than by a timer, which is the
better notion: ten quiet ticks should not forget what you were doing,
and ten busy ones should. `LIFE` could never say that.

## `_install_bundle`

Load the conventions that ship as rules rather than as branches (§4).

        This used to build them here, with `self.rules.rule(IMPLIES, [Member(...
        g.rel(...))], ...)`. It does not any more, and the move was a TEST rather
        than a tidy: the design's claim is that the HOW is data, and authoring
        the apparatus in Python meant nobody had ever checked that the surface
        can say what the apparatus is made of.

        It could not. `arrived` and `not` were absent from `reserved`, so
        <intake> and <denial> were unwritable by anyone but the engine -- and,
        worse than unwritable, a corpus naming those relations got a *twin* node
        that matched nothing, silently. That is the trap this codebase has paid
        for four times, arriving from the vocabulary side. Both are load-bearing:
        deleting either name now fails construction, which is the probe.

        So `_vocabulary_is_surface_nameable` runs on every load. A bundled rule
        reaching for a relation a corpus cannot name is now a construction
        error, not a silent divergence.

## The mint marker is the one relation that i

 **The mint marker is the one relation that is surface-reachable
WITHOUT being a reserved name**, and it has to be, or bundling a rule
that introduces something is impossible. `+k` is written as a mark and
the parser builds this node directly, so a corpus never names it and
can never build a second one -- which is exactly the failure this
check exists to prevent, arriving already prevented. Reserving `new`
instead would take the word from every corpus, which
`a_rule_can_introduce_a_thing` refused on purpose.

## An ARGUMENT atom is a twin waiting to happ

 **An ARGUMENT atom is a twin waiting to happen exactly as
a relation is, and this returned early on every one of them.**
`<unattended>` concludes `declined($a, unattended)`; the
bundle's `unattended` was not reserved, so a corpus asking
about it built a second node with the same name and saw
nothing at all. The rule fired. The corpus could not tell.

 Variables are exempt: they are scoped to the statement (§8)
and are not names a corpus needs to reach.

## The POSITION. It was missing and it is pa

 **The POSITION.** It was missing and it is part of the rule
missing and both are part of the rule: an antecedent is a sequence --
§18's tiebreak reads the consumed entries and `consumed` is filled by
member position -- and a consequent member states how strongly it
would conclude. Without them a rule read back out of the graph is a
different rule, silently, and `g.rel` interns, so a rule with two
identical members would have lost one of them as well.

The antecedent carries no grade, and that is not an omission: `Member`
says so -- what a premise was worth is read off the entry that matched
it, not asserted by the rule.

## `suppose`

Enter a supposition: assume `assumption` bare, and reason inside.

        This is the alternative to lifting. Where a lifting rule rewrites
        `likely(X)` into `likely(Y)` and therefore has to name the pattern of
        every rule it crosses, supposing **unwraps** -- inside the frame the
        assumption is an ordinary fact, and the ordinary rules apply to it by
        ordinary matching. Nothing is mentioned, so nothing hits use/mention, and
        rules carrying variables work unchanged.

        Containment is structural rather than promised: the frame's seat is a
        *successor* of the caller's, so the caller's walk never reaches it. What
        was concluded under the supposition is unreadable from outside until
        something deliberately carries a claim out.

        **And that was true of entries and false of structure, which is
        what the situation fixes** (`docs/situations.md`). Probed before it
        existed, on a supposition concluding an ordinary stratum-0 fact inside
        itself:

            is secret(a) BELIEVED at the root?     None      contained
            is said(secret(a)) in the graph?       True      not contained

        The seat could not close that, and no amount of ancestry could: the leak
        was never in the read. `at_or_after` is consulted when an ENTRY is
        resolved, and a structural fact is never resolved -- it is enumerated
        out of the argument index, which spanned everything. So a supposition
        cuts a **branch of the graph** as well as a successor of the chain, and
        the index keyed by that branch is what makes `said(secret(a))` die with
        the hypothesis that built it.

## `_enter`

Open a supposition when one is requested -- at the write, not in a
        phase, and *without* running the reasoning inside it.

        A rule concludes `+suppose(p, likely)` like any other fact. What the
        machinery does that a rule cannot is move the register, because a frame
        is anchored and a rule is generic. It does nothing else.

        The old phase did much more: it opened the frame and then called `run()`
        inside it, to quiescence, before returning. That is a subroutine call,
        and §18 spends its length arguing that nothing may own the loop --
        `if to find an answer, look for causes is control flow, step three owns
        the agent until it returns`. Supposition was exactly that, in the
        machinery rather than in a corpus, and it meant a surprise could not
        preempt reasoning carried out under a hypothesis.

        Reasoning inside a supposition is now ordinary ticks of the ordinary
        loop, with the register pointing inside. The frame is left when the loop
        finds nothing more to do there (`_leave`).

## Whether to suppose again is REASONING, and

**Whether to suppose again is REASONING, and it was Python.**
This line used to drop a second supposition of the same assumption --
*supposing the same thing twice derives nothing new* -- which is true
only while nothing has changed, and it made a hypothesis
unfinishable: explore `broken(pipe)`, find the reasoning wants
`wet(pipe)`, conclude nothing and discharge; then be told `wet(pipe)`,
and the hypothesis is never revisited.

 The first repair was worse: a Python test for *was this licensed by
`again`*, which put the decision back in the machinery one layer down.
Measured instead -- **the dedup was redundant.** Quiescence already
stops a RULE re-concluding `suppose(p, w)`, because the proposition
already holds; the runaway the old comment feared (a rule inside the
frame re-supposing its own assumption) runs 4 ticks to quiescence with
the dedup and 4 without, identically.

So both are gone. What decides that a hypothesis is worth entering
again is a corpus writing `again(suppose(p, w), <occasion>)` -- the
same argument re-asking is built on, and now the only one.

`_supposed` stays as a COUNT, for `hypotheses(n)`: how many distinct
assumptions have been entered.

## `_fit`

Answer a match request (§5's wall, from the side that can be crossed).

        A rule concludes `+fit(<R>, goal)` -- *could this rule produce this?* --
        and the machinery answers, because deciding that a ground goal
        corresponds to a stored generic pattern is `match`, and match is floor.

        What comes back is not a yes and a binding. A binding is a map from
        variables to nodes, and a rule cannot hold one, let alone apply it. So
        the answer is already **instantiated**:

            +fits(<R>, goal)                one, if the rule could
            +need(<R>, goal, <subgoal>)     one per antecedent member, substituted
            +unfit(<R>, goal)               otherwise

        That is the whole service, and its shape is the finding: the missing
        piece was never *match* on its own. Match and substitute travel together,
        because the caller cannot do the second half.

        Everything else stays a rule -- whether to ask, which rule to prefer,
        whether to check satisfaction first, what to write when nothing fits.
        Those are the conventions §18 froze into a phase.

## The entries, not only the map. This buil

 **The entries, not only the map.** This built `env` by READING the
plan's bindings and then wrote its answer with `consumed=(e, s)` -- so a
conclusion that relied on *which tap* did not rest on the entry that
said which tap. Three things followed, and all three are R5's
guarantee failing quietly at the one place a plan commits to something:

  * `unsupported` could not see a withdrawn binding, so the two halves
    of this arc did not compose;
  * §12's weakest link could not weaken a conclusion by the grade of
    the binding it assumed -- a `@possible` tap laundered into a
    `@certain` achievement;
  * `why()` never mentioned which tap it had assumed.

## Not that one. Reconsidering a binding was th

*Not that one.* Reconsidering a binding was the last of the four
hats, and the reason it was stuck is smaller than it looked: a
`binds` fact has always been deniable, and denying it achieves
nothing, because this loop then re-unifies and picks the SAME first
candidate. What was missing was never a way to withdraw a choice;
it was a way to say what has already been tried.

So the binding stays a construction (§18: deciding identity where
the name is read), and reconsidering one is an ordinary claim a
corpus makes and can itself deny.

## `_root`

Answer *is this what I was asked for, or something I asked myself?*

        §6 recorded the gap and §12 recorded why it could not be a rule: a root
        goal is a `goal($w)` with **no** `subgoal($p, $w)`, and a `-` member says
        *an entry denies this*, never *for no `$p`*. That is the same shape as
        `blocked` -- a negative existential over what the rules produced -- so it
        gets the same treatment, which is the point of having settled it once.

        It answers only when the answer is YES. `rooted(w)` is deposited if
        nothing claims `w` is anybody's subgoal; nothing is written otherwise,
        exactly as `_verdict` writes `blocked` only when nothing fits. A
        machinery that answered *no* would be asserting a negative existential of
        its own, and §17's rule is to deposit the smallest unarguable record.

        What it unblocks is one line a corpus could not write before:

            rule <done> = implies( { +goal($w), +rooted($w), +$w },
                                   { +enough($w) } )

        *What I was asked for holds, so I am done.* The version without `rooted`
        is unsound and running it is how the gap was found -- `<expand>` writes
        `+goal(sub)` for every subgoal backward reading derives, so the agent
        stopped at the first satisfied SUBGOAL: measured, tick 51 of a run whose
        goal arrived at 57.

         It is asked, not volunteered, for the reason §19 gives about recall:
        this is a question about a search that has got somewhere, and asking it of
        every goal the moment it appears would answer before `<expand>` had
        written the `subgoal` entry that makes the answer false. The corpus asks
        when it is ready to stop.

## `_count`

Answer *how many ground matches does this pattern have here?*

            count(goblin($x))         a REQUEST, asked by a corpus rule
            counted(goblin($x), 2)    the answer, and it always answers

        **The general case of the three asks above it**, and the reason it
        is worth having is that they are three special cases of one question.
        `rooted`, `unsupported` and `blocked` each enumerate something the rules
        produced and each answers only *yes*, because each is a negative
        existential and §17 says deposit the smallest unarguable record. A count
        is not a negative existential -- it is the measurement all three are
        thresholds on -- so it answers with a number and lets a corpus write the
        comparison:

            { +counted($p, 0) }  =>  nothing was told about it
            { +counted($p, 1) }  =>  ***the*** one that satisfies it
            { +counted($p, 2) }  =>  ambiguous, and what to do about it is mine

         **The matcher does the counting, and that is the whole of why this
        is admissible.** `deposit-dont-decide.md`: the engine may compute
        anything whose result is a fact the rules can read, deny and argue with;
        what it may not do is decide. So the count is not a second enumeration
        written beside `match` -- it builds a one-member probe rule and runs the
        ordinary matcher, which means the number is *the same enumeration a rule
        would have got*, and a corpus can never be told a count that disagrees
        with what it could match for itself.

         **Answered at the ask, not at quiescence.** It is on the write path
        with the other answerers, so `count(...)` is answered the moment it is
        written. That is the opposite of `unsupported` -- which is a claim about
        a FINISHED search and a lie before `quiet` -- and it is right here for
        the reason the whole aggregate exists: a reading with two candidates is
        ambiguous *now*, and a corpus that had to wait for quiescence to find
        out would have acted on one of them already.

         **A count is not monotone, and nothing pretends otherwise.** It is
        true of a moment and the next entry can falsify it. The answer is an
        ordinary dated fact, so the ordinary read supersedes it when the count
        changes -- but only if it is ASKED again, because the machinery does not
        volunteer. A corpus holding a stale count is holding a fact about the
        moment it asked, which is what it is.

## Distinct PROPOSITIONS, not applications, and t

 Distinct PROPOSITIONS, not applications, and this is a GUARD rather
than a repair -- said plainly because the difference matters. The
question is *how many things*, and an application is per surviving
entry; those coincide today, and probed on a proposition denied and
re-asserted they still coincide (2 applications, 2 propositions). So
nothing here has been seen to need it. It is kept because the two are
different questions and only one of them is the one being asked, and
the day `resolve` keeps two live entries for one proposition the count
should not quietly start answering the other.

## Keyed on the ASK, not on the pattern, and

 **Keyed on the ASK, not on the pattern, and that is what makes the
answer readable at all.** A statement's variables are scoped to it
(§8), so the `$x` in one rule's `goblin($x)` is not the `$x` in
another's -- two rules writing the same description build two nodes,
and a corpus had no way to name the thing it had just asked about.
Keyed on `count(goblin($x))` it does, by the route the surface already
gives a description: name the statement.

    fact <goblins> = count(goblin($x))
    rule <ambiguous> = implies( { +counted(<goblins>, 2) }, { ... } )

Read back the pattern with an ordinary structural member if you want
it; the count is about the question that was asked.

## A COUNT IS A FUNCTIONAL ATTRIBUTE, so the

 **A COUNT IS A FUNCTIONAL ATTRIBUTE, so the old one is denied in
the same breath.** `counted(p, 2)` and `counted(p, 3)` are different
propositions, so asserting the second leaves the first standing and
the corpus has two answers to one question -- which is the dungeon's
`hp(g1, 5)` and `hp(g1, 2)` defect exactly, one layer down, and the
design's own second constraint on this feature: *not monotone, by
construction; a count is true of a moment and can be falsified by the
next entry.*

Authored corpora pay this by writing the denial and the assertion as a
pair. Nobody can write it here, because nobody but the machinery knows
what the previous count was -- so the machinery owes it, and the
alternative is an agent that believes there are two goblins and three.

## `_supported`

Answer *does anything still hold this up?* -- the third negative
        existential, and it gets the treatment the other two got.

            support(p)        a REQUEST, asked by a corpus rule
            unsupported(p)    the answer, deposited only when nothing does

        §12's argument against making it a rule is the same one that settled
        `blocked` and `rooted`: *no remaining support* is a claim about every
        entry that ever claimed `p`, and a `-` member says *an entry denies
        this*, never *for no entry*. So it is machinery, and it **answers only
        yes** -- a machinery that answered *no* would be asserting a negative
        existential of its own (§17: deposit the smallest unarguable record).

        **And what it does NOT do is retract.** Losing your reason is not
        acquiring a counter-reason. If a source is discredited, what it told you
        does not thereby become false; you have stopped having a reason, which is
        a different state and the one you can act on. An engine that deposited
        `-p` here would be making a claim about the world that nothing justified,
        and §12's weakest link would have a link with nothing behind it.

        It is also not the machinery's call. *Undo what the plan asserted* and
        *keep believing it until something contradicts it* are both correct, for
        different deployments, so the reaction is a corpus's:

            {+unsupported($p)} => {-$p}                tear down
            {+unsupported($p)} => {+goal($p)}          go and re-derive it
            {+unsupported($p)} => {+doing(ask($p))}    ask
                                                      ...or nothing

         **Asked, never volunteered**, and for `blocked`'s reason exactly: a
        proposition may rest on several things, so withdrawing one says nothing
        until the rest have been looked at. That makes this an aggregate over a
        finished search, legitimate at `quiet` and a lie before it.

        A fact nobody derived rests on nothing and is supported by its own
        assertion -- that is what makes this bottom out rather than regress.

## `_verdict`

Answer *did anything fit this goal?* -- the aggregate, and the last
        thing the goal phase was doing that no rule could do.

        `blocked` is a claim that **no** rule fits. §12's argument that it cannot
        be a rule stands: a positive rule fires when *some* rule does not fit,
        which is a different claim, and a `-` member says *an entry denies this*,
        never *for no `$r`*. It is an aggregate over a finished search.

        Three things make answering it here different from running it in a phase,
        and together they are the reason the phase could go.

        **It runs no search.** Every `fits` entry it counts was produced by the
        rules, through `fit`. This reads the state and nothing else -- so *which
        rules were considered* stays the corpus's business, and recall can still
        narrow it (§19). A phase that searched for itself made recall unreachable.

        **It is asked, not assumed.** A rule decides when a goal is settled --
        `+quiet($m), +goal($w) => +verdict($w)` is the shipped policy, and it is
        overridable like any other. The phase asserted the same policy in control
        flow, where §18 says a convention is invisible and expensive.

        **It is timed by the corpus, not by the loop.** The phase ran ahead of
        recall and returned early, so while any goal was unexpanded no ordinary
        rule could apply -- backward search monopolised the loop and reported a
        goal as blocked that forward reasoning would have satisfied. `ugm.backward`
        measured exactly that. Asking at quiescence cannot starve anything,
        because there is nothing left to starve.

        Two-valued, because a request that answers only when the news is bad is a
        third silent decline (§5).

## `_as_settled`

A goal, with whatever its own plan has since bound filled in.

        **A verdict was reported AS THE RULE WROTE IT, and by the time it is
        reported that is no longer the most informed thing available.** A foreign
        corpus found it (`docs/quest-feedback.md` §1): fitting `open(door1)`
        against `{ +have($w, $k), +opens($k, $d) }` subgoals `opens($k, door1)`,
        the world satisfies it with `opens(key1, door1)`, **and the machinery
        records `binds(plan, $k, key1)`** -- and then said `blocked(have($w, $k))`
        anyway. The binding was not missing. It was known, written down, and not
        read back.

         **The consequence is exactly the one they named, and it is not
        cosmetic**: a generic term cannot be uttered (§14 -- `_dispatch` refuses a
        generic intent, because a description cannot be acted on), so an agent
        could not say what it was stuck on unless the rule's member happened to
        be ground already. They shaped a corpus around it, carrying
        `have(p1, key1)` ground for that reason alone. *Ask for help* was a
        special case when it should have been the general one.

         Instantiated HERE rather than at the subgoal, and the moment is the
        argument: when `<expand>` writes the subgoals nothing has checked them
        yet, so the sibling's binding does not exist. A verdict is asked at
        quiescence, which is the latest moment there is -- so it is the one that
        knows the most.

         **One answer PER PLAN, and the first version of this returned one
        answer and was silently wrong.** A rule fitted to two goals shares its
        variable nodes, so `plan(<unlock>, open(door1))` and
        `plan(<unlock>, open(door2))` both carry a `$k` -- the *same node* --
        bound to `key1` and `key2`, and they subgoal the *same* `have($w, $k)`
        node. Collecting every relevant binding into one environment then let the
        last one win: the agent was stuck on two keys and said one. Arbitrary and
        silent, which is the worst pair this design knows.

         Only bindings from a plan this goal is actually a **subgoal of**. Every
        `binds` fact in the state would drag in an unrelated plan's choices, which
        is what `_check` already refuses one level down.

         **And that last restriction is UNFALSIFIABLE, recorded rather than
        left looking measured.** Removing it breaks nothing, and the reason is
        structural: §8 scopes variables to a statement, so a plan binding a
        variable that occurs in this goal must be built from the same rule -- and
        this goal is that rule's member, so every such plan is already in the set.
        The guard cannot currently be wrong. It is kept for `_check`'s reason,
        and because a second way of building plans would make it load-bearing
        immediately, but no check here can see it and none pretends to.

## What `_forbid` was, and where it went

§19's carve-out, and it is now a trigger.

        > **Recall may be incomplete about what to do. It may not be incomplete
        > about what you must not do.**

        A norm expressed as an ordinary rule is a competitor in recall, and a
        prohibition that fails to come to mind is a forbidden act that nothing
        notices. `_forbid` answered that by taking norms off the recall path
        entirely: a `forbidden(<pattern>)` claim, consulted at the gate on every
        write, indexed by the relation about to be written.

        It is folded into the trigger seam. A prohibition is a rule marked
        `intercepts(<T>, after)` that concludes `drop(p)`, and the carve-out
        survives intact for the same reason it always held: triggers are
        consulted directly, never recalled, never ranked, never arbitrated.
        Measured -- narrow `recall_budget` to 1, so the agent cannot reliably
        bring anything to mind, and the forbidden act is still refused while the
        permitted one still happens.

        **What the fold buys is that a prohibition is a QUERY.** As a stored
        pattern a norm could say only *never this shape*. As a trigger's
        antecedent it can ask anything a rule can ask -- what else holds, who is
        acting, whether an emergency was declared -- and it says the shape in a
        rule's antecedent, which is where a pattern belongs. `forbidden`,
        `_forbid` and the description-headed fact that carried it are all gone,
        and `DESCRIBES` is down to `count`.

         **What changed, and it is not nothing.** The veto ran on EVERY write;
        a trigger runs on what a rule concludes. A prohibition now binds what
        the agent concludes and does, not what a channel reports -- which is the
        right line (recording that someone said something is not the agent doing
        it), but it is a narrower reach than the gate had.

         A drop is recorded as `refused(p, +, <T>)` -- the same relation the
        gate wrote, so a corpus reading refusals reads both, and it names the
        norm. It is not counted as work the application did, or a rule whose
        conclusion is always dropped would never stop applying: measured, 299
        moves to the run limit against 4.

         Retiring a norm binds what comes after it. Deny `intercepts(<T>,
        after)` and the rule stops being a norm, but an application already
        refused is spent -- what was refused stays refused, and the next thing
        the rule reaches is not.

## `_forgo`

Taking one way of getting something is passing up the others.

        This is what arbitration was assumed to do and did not: a rule that lost
        was **deferred**, so quiescence ran it anyway and an agent with two ways
        to do something did both -- including the destructive one. Measured, with
        acts: `emitted: ['fill(kettle)', 'smash(jug1)']`.

        **Passing up is the default, and complementary work is the exception a
        corpus declares.** That is the one judgement here, and it is made on which
        way the error is recoverable rather than on which is more often right:

        | forgo by default | an agent that should have done both under-does. The
        |                  | goal stays open, the veto deposits `open(w)`, and the
        |                  | rule below hands the alternative back. Recoverable.
        | defer by default | an agent that should have done one does both. The jug
        |                  | is smashed. **Not** recoverable.

        So the deposit is deniable, and retrying is one ordinary corpus rule:

            {+open($w), +forgone($r, $w)} => {-forgone($r, $w)}

        *When what I wanted is still outstanding, reconsider what I passed up.*
        That is §21's backtracking item, arriving as a consequence rather than as
        machinery, and it is why this had to be a fact about the alternative
        rather than a retraction of the goal.

         The apparatus is exempt on both sides -- §13's carve-out again. Nearly
        every bundled rule consumes `goal($w)`, so without this, applying one
        would forgo backward reading entire.

## `_reaching`

Does any rule say that `a` reaches `b`? (§11's containment, moved.)

        The machinery consulting a corpus's rules, on demand, with both
        arguments already bound -- the door `_forbid`, `precedence()` and
        `_recall` already use, given a general name. It is ONE backward step and
        not a fixpoint: the consequent is unified with the question, those
        bindings are substituted into the antecedent, and the antecedent is
        matched. Nothing has to be selected, which is the whole point -- a rule
        that had to win a move before the read could answer would make a span
        claim invisible until it did.

         The author's line is about logic BURIED in Python, not about the
        direction of a call. A lookup that argues for nothing is not logic; the
        three span decisions it looks up are, and they are in `bundle.ugm` where
        a corpus can argue with them.

## `_note`

Record that the machinery did something a rule may care about.

        The user's reason, and it is the right one: these should be **reasonable
        over**. An agent that has reached past its shortlist twice, or been
        stopped by a bound, knows something about its own effort -- and until
        now that lived in a Python counter, which is §21's defect for the
        seventh time.

        Deduped by reading the graph: restating is not revising (§8), and the
        claim is *this happened here*, not how often.

        The licence defaults to *the loop ran out of work here*, which is what
        the effort records are about. A caller with a better answer to **why
        this is on the record** passes it, the way `forgone` and `close` name
        the rule that was chosen.

## The palette is the AUTHOR's, and this is w

**The palette is the AUTHOR's, and this is what makes that
true rather than conventional.** Probed before it was: a rule
concluding `+afforded(teleport(a, b))` widened the palette, its
own attempt was then accepted, and nothing said a word. A learned
rule could grant itself an action — which is the exact bound
`docs/HANDOFF.md` 19c's safety argument rests on, and it was
leaking.

An entry's licence is *what produced it* (§5), and a rule's
conclusion is licensed by `applied(<R>)`. A declaration is not. So
the distinction is already in the chain and needs no register of
who said what.

 The affordance is not refused — a corpus may say what it likes,
and a claim ABOUT the palette is not a claim ON it. What it does
not do is COUNT, so the attempt that leans on it is declined like
any other, which is the loud half.

## `_recover`

Nothing applies -- but is that because a domain is out of mind? (§19)

        §19's carve-out for the fourth time, and the argument transfers whole.
        Unloading a domain is **safe to be wrong about**: worst case it comes
        back, which is why *when to unload* may be an ordinary defeasible rule
        and is exactly the seam experience belongs at. Reaching for it again may
        **not** be, and the asymmetry is the same one every time:

            Recall may be incomplete about what to do.
            It may not be incomplete about what it has NOT looked at.

        Because `quiet` is what `<give-up>` asks its verdict at, and `blocked`
        claims that **nothing** answers a goal -- an aggregate over a *finished*
        search. A goal whose evidence is merely dormant would be reported
        unreachable, and the trail would show a completed search that never ran.

         **Only when something is outstanding**, and running it without that
        is how the shape became clear. The unsoundness is precise: `blocked` is
        about a GOAL. A run with nothing outstanding declines nothing -- and
        escalating anyway wakes every domain at the end of every run, which threw
        away the whole 14.5x saving and failed two dormancy checks that were
        right to fail. So this carve-out is narrower than `_widen`'s and says so:
        *escalate before believing a decline about something I was asked for.*

        Everything comes back, not one domain chosen by some order: which to try
        first is a judgement, and §15 refuses orders nobody can justify.

         **It terminates on its own, and a `_widened`-style once-only flag was
        wrong here.** Escalating writes `due` for everything hidden, so nothing
        is out of mind and the next call returns False -- no guard needed. Worse,
        a guard would BLOCK a legitimate second escalation, since the only way
        something becomes hidden again is a corpus claiming it, which is a new
        decline about a new dormancy and deserves a fresh reach. The flag was
        written first, gated by nothing, and removing it is what the kill-probe
        asked for.

## The veto has already been exercised here, and it

The veto has already been exercised here, and it did not merely
cost a tick: it handed the loop back. Reacting to an open goal --
diagnosing it, asking about it, going after it -- is ordinary
reasoning that takes as many steps as it takes, and an `enough`
consulted again on the next tick would cut it off after one.

So an outstanding goal does not delay a stop, it OUTRANKS one, and
the agent finishes the ordinary way: at quiescence, which is the
only claim that nothing is left that was ever true. Note what that
costs and where: nothing, when the goals are achieved or genuinely
unreachable (a blocked goal yields no new work, so the loop quiesces
at once) -- and the whole of the saving when one is reachable, which
is the case where saying *enough* was wrong.

## `_notice_open`

The veto: a stop with a goal still outstanding is not a stop.

        Why this is machinery and not the rule a well-written corpus would have.
        *If I still have a question to ask, there is more worth doing* is true,
        and a corpus that states it needs nothing here. But the guarantee wanted
        is that an agent cannot walk away from what it was asked for **because
        nobody thought of the case**, and a convention every corpus must remember
        is exactly the kind this design keeps finding it has lost. §19 already
        made this argument once, about norms, and the shape is the same one:
        unconditionally consulted, entirely contestable.

        What it is not: a phase. It runs at one machinery decision, the way
        `_forbid` runs at the write and `_widen` runs at quiescence, and all three
        are the same move -- **escalate before believing a decline.**

        | `_widen`  | a shortlist that ran dry is not a search that finished |
        | `_forbid` | a write a norm covers never happens |
        | this      | a stop with a goal still open is not a stop |

        **And the refusal writes**, for the reason §19 gives and for a second one.
        A veto depositing nothing would be a silent decline, which is the failure
        being designed against; and it is what makes this terminate, exactly as a
        norm's refusal is what stops a forbidden rule re-applying. Each goal
        vetoes **once**, so what is guaranteed is that nothing is dropped without
        the agent being given the occasion to react -- not that it always finds an
        answer, which no mechanism can promise.

## And an ATTEMPT nobody resolved, which is t

**And an ATTEMPT nobody resolved, which is the same claim.** A
goal still open and a request still outstanding are both *the agent
was asked for something and it did not happen*, so both veto a stop
once and both go on the record as `open`.

 It has to be HERE and not in a watchdog keyed on `quiet`, and
that is the whole finding. `quiet` is written when the search ran dry,
and an agent that stops SATISFIED never runs dry -- Hanoi finishes on
`enough(solved)` with a stale attempt standing and `quiet` never
written at all. `_halt` then breaks the loop immediately, so a rule
keyed on `stopped(...)` never gets a turn either. Between the two, an
outstanding request could be dropped in silence by an agent that
believed itself finished -- death by silence, and it is the case the
existing carve-out did not cover.

## `_notice_attempts`

An attempt nobody resolved, on the record before the loop ends.

        A goal still open and a request still outstanding are the same
        claim -- *the agent was asked for something and it did not happen* -- so
        both go on the record as `open` and both veto a stop once.

         **Called from BOTH endings, and that is the whole of it.** A run
        that stops SATISFIED never goes quiet, and a run that goes quiet never
        stops satisfied; covering one leaves the other silent. Measured on
        Hanoi, which finishes on `enough(solved)` with a stale attempt standing
        and writes `quiet` not once.

         Neither `quiet` nor `stopped` could carry this on its own: `_halt`
        breaks the loop immediately, so a rule keyed on `stopped(...)` never
        gets a turn, while `quiet` is written only when the search ran dry.

## The machinery says this, not a bundled wat

 **The machinery says this, not a bundled watchdog**, and the
reason is measured rather than aesthetic. A rule keyed on `open`
would be a fourteenth bundled rule, and a bundled rule shifts the
declaration RANK of every rule in every corpus: it cost
`ugm.walkers` its central demonstration -- the `<step>`/`<fork>`
contention stopped showing as two options about one walker -- and
`ugm.teaching` one conclusion. The bundle is not free, and it is
not free in a way that is invisible from inside it.

It is also the more honest owner. *Nothing resolved this and
the loop is ending* is a claim about the loop, which no rule can
see: `_halt` breaks immediately and `quiet` is only written when
the search ran dry. The machinery deposits its own event, exactly
as it does for `unafforded`, and what it MEANS is still a rule's.

## `_wake`

The loop found nothing to do. Say so, in the graph, once per seat.

         And notice what is still outstanding while there is still a tick to
        react in -- the same call `_enough` makes before stopping satisfied.
        The two endings are disjoint and an attempt can be dropped by either.

        §5 named two places the machinery declines -- match and write -- and
        quiescence is the third. It was the only one that declined *silently*,
        and silence is what lets reasoning stop with goals still open and nothing
        anywhere recording that it stopped rather than finished.

        What is deposited is one fact and no interpretation. A watchdog is then
        an ordinary rule with `+quiet($m)` in its antecedent: inert until the
        loop stops, because nothing else ever writes that. No registry of
        watchdogs, no trigger table, no second loop -- the trigger IS the fact,
        and the rule that wants it says so in its antecedent like any other rule.

        Two things fall out that are worth having. Quiescence is the moment an
        **aggregate over a finished search** becomes legitimate, which is where
        §21's homeless `blocked` belongs -- *no rule fits* is only true of a
        search that is over, and now there is a fact that says one is. And
        because waking is an ordinary write, whatever a watchdog concludes is
        ordinary reasoning: preemptable, defeasible, and in the same trace.

        Once per seat, tracked rather than resolved, because the point of the
        entry is to be *new* -- writing it a second time at the same seat would
        make it re-match forever.

## `computator`

Register a function that is COMPUTED during a match (§12, §22).

            { +purse($a, $x), +cost($i, $c), minus($x, $c) as $new }

        **Purity is structural here, not declared.** An answerer is given
        `(machine, frame, entry)` and can do anything; a computator is given
        **values** and returns a value, so it cannot reach the graph, the
        register or the world -- there is nothing to reach them with. The
        deleted engine proved purity with 45 lines of transitive static
        analysis; not handing the function anything is cheaper and stronger.

        And it is what makes an application ATOMIC. A tool answers through
        the write, so its answer lands a tick later and a transfer can be caught
        half-done -- measured, an agent emitted an act on a total that never
        existed (§22). Computed during the match, the result reaches the same
        consequent, in one moment.

         It is registered in the CORPUS's scope, for `Loader.answerer`'s reason:
        a relation is a name, and a name minted beside the corpus's table is a
        relation nobody can write.

## `answerer`

Register something that answers a request. §21's debt, as data.

        A tool is not a new kind of thing. It is the shape `_fit` and `_verdict`
        already have -- **a request answered by a function rather than a search**
        -- which is how stratum 0 escapes §5's wall, and it is the only shape
        something outside the agent can honestly take: a search the agent cannot
        inspect is not reasoning it can be held to.

        What changes here is where the BINDING lives. `_fit` answers `fit` because
        a Python line says so, and the consequences are the ones this design keeps
        finding: a corpus cannot ask which tools exist, cannot retire one on
        evidence, and cannot reason about one. So the binding is a fact:

            answers(<M>, ask)

        deposited like any other, queryable by R4, and **deniable**. Retiring a
        tool is `fact -answers(<oracle>, guess)` and the machinery stops calling
        it -- the same move §9 gave norms, which were also unconditionally
        consulted and still entirely contestable.

        `fn(machine, frame, entry)` returns the answer node, or `None` for *I have
        nothing to say* -- which is a real answer and not a failure, because a
        tool that must answer everything is a tool nothing can decline.

         The name goes in the `<...>` namespace, which is the namespace of
        STATEMENTS, because a tool is something other statements are about.
        One table with rules and named facts, so a tool cannot share a name with
        a rule -- two things with one name is the mistake the marker prevents.

## request may be a NodeId, and for a corpus re

 `request` may be a NodeId, and for a corpus relation it must be.
Registering a tool in Python and naming its request as a STRING mints a
relation beside whatever table the corpus resolves against, so the tool
answers a request nobody can write -- measured, and it is the twin trap
for the third time this session. `Loader.answerer` is the scoped door;
a bare string is right only for a relation `reserved` already carries.
 **And the protocol is checked HERE, at the one place both doors go
through.** Reported by `pystrider`, who registered a two-argument
function through the scoped door and got
`TypeError: <lambda>() takes 2 positional arguments but 3 were given`
out of `gate.write`, at the first write, with nothing saying the
registration was the problem -- one cycle to find. The mistake is easy
to make because the apparatus's own reifier registers `(frame, entry)`
and wraps it, so both arities are visible in this file.

A registration is a declaration, and §5 says a silence is the defect:
this refuses it at the moment the claim is made, which is the only
moment the caller is looking at it.

## `_answer`

Call whatever answers this request, and record what it said.

        Three things it deliberately is not.

        **Not a conclusion.** What lands is `answered(<M>, req, y)` -- a record
        that M said so, the same treatment §17 gives every arrival. Turning it
        into a belief is an authored rule, which may wrap it as weakly as it likes, so a
        confident tool cannot launder a weak answer into a strong claim, and
        §12's weakest link keeps working with nothing added.

        **Not unconditional.** The binding is read from the graph on every write,
        so denying `answers(<M>, ask)` silences the tool immediately and on the
        record. A tool wired in Python could only be silenced by editing Python.

        **Not invisible.** The deposit is licensed by `applied(<M>)` -- the same
        licence a rule's conclusion carries -- so `review` and `blame` walk
        through a tool without knowing it is one. That is the whole of what
        *jointly trained* can honestly mean here: one credit walk, reaching
        rules and tools alike, producing labels for both.

## §19's carve-out, a fifth time, and the argum

 §19's carve-out, a fifth time, and the argument transfers
verbatim: recall may be incomplete about what to DO, never
about how to READ. Retiring a tool is an ordinary revision --
it was somebody's claim that the tool was worth consulting.
Retiring `<fit>` is not an opinion about a tool; it is the
agent losing backward reading, silently, on one corpus line.

So a `standing` binding is **overridable but not
forgettable** -- the same distinction the bundle makes, and
the same fact. The denial is not ignored: it is REFUSED, on
the record, so *I tried to turn this off and was not allowed*
is answerable. A fourth silent decline is what §5 spent the
design's whole vocabulary avoiding.

## `_again`

Re-deliver a request, because a corpus said an occasion warrants it.

        §6: *a request can only be made once.* `<ask-check>` asks whether a
        subgoal is already satisfied at the moment the subgoal appears; if
        forward reasoning satisfies it three ticks later, nothing asks again,
        because re-concluding `+check(p, w)` restates what the chain says and
        quiescence drops it. Requests are facts, and a fact is not an event.

        **The request never needed to be fresh. The ENTRY did.** The chain
        has always taken a second entry for a proposition it has seen -- that is
        §10's two indices, and *the same claim, later* is what they exist for.
        What forbids the re-ask is `_would_change`, and it forbids it of a RULE.
        The machinery re-delivering is not a rule restating, so the prohibition
        was never about this act at all.

        So the whole of it is a wrapper and one write:

            again(<request>, <occasion>)

        an ordinary node, differing per occasion, so concluding it is a step;
        and what this does with it is write the wrapped request through the
        gate, where every answerer already listens. `_settle`, `_fit`,
        `_verdict`, `_root` and `_answer` are `on_write` hooks, so a re-asked
        request reaches all five, and a **tool** becomes re-askable by the same
        line -- which is the property `answers(<M>, ask)` was for. Not one
        answerer knows this exists.

        **Its own binding is a fact**, which no other piece of the apparatus
        can say: this is registered through `answerer`, so `answers(<re-ask>,
        again)` is on the record and `fact -answers(<re-ask>, again)` turns
        re-asking off. §21's *the apparatus does not eat its own cooking* is now
        true of eight hooks rather than nine.

         **What an occasion may be is the whole question, and it is not free
        choice.** An occasion the asking can itself create warrants the next
        re-ask, which creates the occasion after that: `ugm.reask` measures both
        sides of it. The criterion the measurement gives:

        > **An occasion warrants a re-ask only if re-asking cannot produce one.**

        The wrapper is deliberately generic -- it re-delivers whatever it wraps.
        Wrapping something that is not a request re-asserts it, which is honest
        rather than an error: the entry is new, and §10 says what a second entry
        about the same proposition means.

## `_dispatch`

The outbound boundary, at the write rather than in the loop.

        A rule concludes `+doing(p)` like any other fact; this carries it past
        the agent's edge, because a boundary is anchored and a rule is generic.
        It is the mirror of `_deliver`, and between them the boundary has exactly
        two names -- one per direction.

        Everything the old `_act` phase did *besides* crossing is now a rule:
        `<did>` records that the agent acted, and `<assert-act>` asserts the act
        itself. The second is the interesting one. §15 argues that the agent must
        assert what it did -- otherwise it emits an intent into silence and
        nothing downstream ever happens -- and as a phase that argument was
        unarguable. As a rule it is a claim, and an agent that should *not*
        assume its acts succeed is now expressible by overriding it.

## Supposing something must not bring it about.

**Supposing something must not bring it about.** §13 says nothing
leaves a frame and §17 makes containment structural -- but effects
were leaving immediately, because dispatch is at the write and the
write did not ask where it was standing. Measured: supposing a
premise whose rule concludes `+doing(fire(missile))` fired the
missile.

That is not a leak in the chain -- the conclusion stayed inside and
crossed out wrapped, exactly as designed. It is the boundary
ignoring the register, which no amount of correct wrapping can fix
afterwards, because the act has already happened.

It also has to hold before a hypothesis can be used to ASK whether
a course of action is acceptable, which is the whole reason to open
one about an act. An agent that finds out by doing it has not
considered anything.

But the REASONING must not stop here, and stopping it was this
repair's first mistake -- a plan died at its first action instead
of continuing past it. Deciding to act is a **conclusion**; what
planning needs from that conclusion is the action's **assumed
outcome**. So the same record is deposited under a different name:
nothing left the agent, and everything downstream still follows.

## Replaying a session must not re-do it. T

 **Replaying a session must not re-do it.** The boundary is the
one place effects leave, and it does not know a repeat from a
first time -- resume a session that opened a door and it opens the
door again. This is `_hypothetical`'s argument in a second place:
supposing must not bring it about, and neither must remembering.

What it writes instead is `taken`, which the bundle already turns
into `did`. So the agent believes it acted -- it did, in the
session being resumed -- and nothing leaves. No new vocabulary:
`taken` has always meant *decided on and not emitted*.

## `_adopt`

Make a rule the graph describes into a rule the loop reads.

            adopt(<R>)

        **`reify` went one way.** A rule has been data since §14's worked
        example -- `rule(<R>)`, `conn`, `ant`, `con`, all deposited at authoring
        -- and `RuleSet.rule` was called only by the parser and by tests. So the
        agent could be asked *which rules do I have* and could never answer
        *and now I have this one*. Every amendment was a file edit, which is
        why nothing in the harmonization family was buildable.

        This is a **door, not a question**, and belongs with `_dispatch` and
        `_enter` rather than with the six answerers: `_dispatch` is where an
        intent leaves the agent and this is where a rule enters it. What decides
        that a rule is worth having is a corpus concluding `adopt($r)`; what
        happens then is not a judgement.

         **Refused inside a supposition, and this is containment rather than
        caution.** §4 makes a frame's conclusions unreadable from outside by
        construction -- the seat is a successor, so the caller's walk never
        reaches it -- but `RuleSet.rules` is one list shared by every frame. A
        rule adopted while supposing would apply *after* the frame is discharged
        and to everything, so supposing would change what the agent believes,
        which is the one thing supposing must not do. `_dispatch`'s argument
        exactly: **supposing must not bring it about.** Refused on the record,
        naming the supposition, because a silent decline is what §5 spent the
        vocabulary avoiding.

         A generic `adopt` is not acted on, for `_dispatch`'s reason: a
        description of a rule is not a rule.

## `_compose`

Collapse two rules into one, because a corpus asked.

            compose(<a>, <b>)     ⟹     composed(<c>, <a>, <b>)

        §4 calls composition the design's larger optimisation -- it removes
        steps rather than making them cheaper -- and it had no trigger: the
        function existed and only Python called it, which is where `adopt` was
        before it was a door.

        **The corpus decides; the function executes.** Which rules are
        worth collapsing is a judgement, and §21's judgement census says a
        judgement the machinery makes alone is a seam: the agent could not
        notice it was composing the wrong things, because a bad shortcut makes
        worse work and never a wrong conclusion, so no fixture fails. So this
        answers a request and never proposes one. `{+exercised($a), +exercised($b)}
        ⟹ {+compose($a, $b)}` is a corpus's line, and *compose what has run
        often and never surprised* stays §22's open trigger rather than becoming
        a constant in here.

         **Refused inside a supposition, and it is `_adopt`'s argument
        exactly.** `RuleSet.rules` is one list shared by every frame, and
        `compose` appends through `RuleSet.rule` -- so a shortcut built while
        supposing would apply after the frame is discharged and to everything.
        Supposing would change what the agent believes, which is the one thing
        supposing must not do. This guard is the reason composition could not
        simply be wired to the existing function.

         **What it deposits closes a defect rather than adding vocabulary.**
        `composed_from` was a Python dict, so *which rules is this a shortcut
        for* was unanswerable by any rule -- §1's pattern, and the one §22 needs
        for *decompose on surprise*, since the licence has to name the
        constituents for the agent to know which sub-steps to re-run.

         Inherited precedence is deposited here, not appended to a list: since
        precedence is READ from the graph (§18), a defeat that binds a
        constituent has to bind the composition as a **claim** or it does not
        bind at all.

## has_var is not a usable guard here, and

 **`has_var` is not a usable guard here, and copying `_adopt`'s was
the bug.** A LIVE rule node is `causes(moment(...), moment(...))` and
therefore holds the variables of its own patterns, so
`compose(<s1>, <s2>)` reports generic however ground the claim is.
That is §5's use/mention distinction: a ground claim ABOUT a rule names
a node containing variables, and structurally the two are identical.
`_adopt` gets away with the test only because the rule it names has
been described and not yet built.

What tells them apart is membership of the live set: `by_node` answers
*is this a rule* without asking what it looks like. A genuinely generic
`compose($x, $y)` has variables as members, and a variable is in no
rule set, so the same line refuses it.

## -- backward reading ----------------------------

-- backward reading -------------------------------------------------

It used to be here: `_expand_goal`, the last interpreter phase, deleted in
`nophases`. It is now six bundled rules over three requests -- `<ask-fit>`,
`<plan>`, `<expand>`, `<ask-check>`, `<give-up>` -- and `ugm.backward`
measured them against it, one rule deleted at a time, before it went.

What it was NOT doing is the finding. §14's wall (a rule cannot decide that
a ground goal corresponds to a stored generic pattern) was real, and the
phase was never the answer to it -- `fit` is. What the phase added on top
was a precedence claim written in control flow: it ran ahead of recall and
returned early, so while any goal was unexpanded no ordinary rule could
apply. That starved forward reasoning badly enough that a goal the corpus
could satisfy reported as blocked, which `ugm.backward` found by comparing
the two readers rather than by anybody suspecting it.

## Which hypothesis produced which conclusion. It w

Which hypothesis produced which conclusion. It was already recorded --
as the crossed entry's LICENCE, `concluded(<frame>)` -- and a licence
is a Python field on the entry, so no rule could ask. §21's defect for
the eighth time, and it closes the way the other seven did: deposit the
record. `applied(<R>)` became `exercised`, the entry's grade became a
wrapper, a tool's binding became `answers`, the effort counters became
`widened`/`reached`/`bounded`.

What it buys is the one thing `hypothesis.py`'s `rivals(about)` had and
this floor did not: two suppositions about the same thing both cross
their conclusions to the same parent as `likely(q)`, and until now
nothing said which came from where -- so a corpus could open rivals and
not compare them. `+left($f, $a), +concluded($f, $c)` is now a join.

Deduped per discharge, and it is a claim about the frame rather than a
count: a proposition concluded twice inside crossed once, and says so
once. Bookkeeping, so a nested frame does not carry
`likely(concluded(...))` out -- the same treatment `left` gets.

## Carried across the situation boundary, by

**Carried across the situation boundary, by atom.**
This is the one place a node built inside a hypothesis becomes
something the caller says, and before situations there was
nothing to do here because there was no boundary -- which is
exactly the defect. `e.proposition` is a node of the
hypothesis's branch; re-stating it at the caller's seat has to
re-state it in the caller's branch, or the caller's own
indices would end up holding a reference to structure it
cannot see, and the leak would come back through the door
marked *conclusions*.

`carry` re-interns in the target and records where the thing
landed, so the caller's `likely(q)` is about the caller's `q`
-- the one it already had, if it had one.

## `tick`

One move of the loop, for a caller that wants to step and look.

        **This was 129 lines of the option-set loop** -- materialise every
        live application, defeat, filter, arbitrate, apply -- kept alive after
        `Machine.run` became the table loop so that `ugm.attention`'s comparison
        had something to compare against. That comparison is deleted (20k): it
        was not a floor gate but a diff between two designs, one of them retired,
        and its exception list was the tell.

        So the second loop goes with it. What a caller of `tick` wants is *step
        once and look*, and this is that -- the same loop `run` is, bounded to
        one move.

         The table PERSISTS across calls, or a caller stepping by hand would
        lose every buff between one tick and the next and be measuring a
        different agent each time. `run` already takes a table for exactly this
        reason and continues its tick count.

## `run`

Bounded, and it returns a result *and* a state -- because a search that
        stopped is not a search that found nothing (§9, §15).

        **And the bound says so, which is §21's defect for the eleventh
        time and the one a foreign corpus asked for first.** `docs/quest-feedback.md`
        §0: they wrote three corpora, made six rule bugs, and **not one produced an
        error** -- four ran to the tick limit and two were silent. What the engine
        said about a corpus that never terminates:

            settles      steps=  3/60   last=quiescent
            runs away    steps= 60/60   last=applied

        A corpus that is finished and one that never will be differed only in
        whether `len(steps)` happened to equal the limit **the caller chose**, and
        `exhausted` stayed 0 either way. **No rule could ask *did I run out of
        time?*** -- while the depth and hypothesis budgets both deposit
        `bounded(...)` when they bite. The tick limit was the one bound not on the
        record, and that was inconsistent with this engine's own practice rather
        than a considered position.

         Deposited only when the loop is still WORKING at the limit. A run that
        stops because there is nothing left to do has not been bounded by
        anything, and saying it had would make the record useless in the other
        direction.

## THE TABLE LOOP IS THE LOOP

 **What follows is the migration as it stood, kept because the numbers were
taken against it.** The migration is finished: `Machine.run` is a delegation and
`core/attention.py` is the only loop in the tree. Read the paragraph below
as the current position and this one as how it got there.

>  **THE MIGRATION TO THE TABLE LOOP IS STAGED, AND THIS IS THE
SWITCH.** Replacing the body with `attention.run(self, limit).steps`
is one line and it works -- the table loop now returns `Step`s for
exactly that reason. What it costs today is **58 of 549 checks**, and
the list is not noise: `enough` and its open-goal veto, dormancy and
callbacks, proposing a supposition, and the match cache. Each is a
piece of the tick this loop does not do yet.

Left on the option-set loop until those land, so the repository never
stops running -- *subtract, do not rewrite*, which is the discipline
that made every other Python deletion here safe.
**THE TABLE LOOP IS THE LOOP.** What stood here -- materialise every
live application, defeat, filter, arbitrate, apply -- is gone. The
option set was the price of being able to say *nothing else applied*,
and the author's judgement is that it is not worth paying on every
tick: the table is a prefix scan, so a rule below the window costs
nothing at all.

**Held to the loop it replaces before that loop stopped being the
one that runs**, and the numbers are the argument rather than the
decision: 58 of 545 checks failed at the first flip, and the suite is
now green under BOTH -- every check that remains is loop-agnostic,
every check that was not is either ported or deleted with the
machinery it described. `ugm.attention` still gates conclusions on
four corpora, one-sided: the table loop may conclude more, never less,
except `close` and `forgone`.

 The import is local because `attention` imports this module. The
cycle is real, and the alternative -- moving the loop in here -- would
put the table back inside the engine, which is the thing this undoes.

## `_recall`

Never complete, by design (§15). Exhaustive here, which is the
        deliberate-reasoning setting: recall with the budget removed -- with one
        exception, and the exception is the first thing a corpus has ever been
        able to say to this step.

        A rule claimed `dormant` is not proposed until something claims it `due`.
        That is all a callback is. §15 argues recall is where experience belongs
        and where being wrong is recoverable; a pointer hung on a hypothesis is
        experience the corpus supplies instead of learns, arriving at exactly the
        seam that was reserved for it.

        Both are ordinary facts, so both are askable, defeasible and attributable
        -- *which rules is this hypothesis carrying?* is a query, not a field. And
        both are read at the register's own position, so a callback attached
        inside a hypothesis wakes only there.

        Cost, stated rather than discovered: two resolves per rule per tick.
        Cheap now because the rule set is small and `resolve` is a walk; the
        moment it is not, this is an index over two relations, not a redesign.

## Nothing DERIVED narrows this step, and finding o

Nothing DERIVED narrows this step, and finding out why was a session's
clearest negative result. Filtering recall by *what fits the current
goal* starved a rule that reacted to a **blocked** goal --
`{+blocked(heat($a, $w))} => {+doing(heat(anna, $w))}` is the most
useful rule in that corpus and it does not fit the goal at all.

> **Relevance to a goal is one signal, and as a filter it is silent
> about everything it is not about.**

What narrows here stays what a corpus *claimed*: `dormant` unless
`due`. An optional cap is kept for measuring, and defaults to off.

 The cap used to order by `prefer(<R>, key, n)` before cutting. That
was rule-keyed advice and is retired; the cap now takes the rules in
AUTHORED order, which is what a corpus can still argue with. Attention
is the replacement and it does not belong here -- it decides which
rules are matched at all, one step later.

## Two things a cap may not starve, and they are §1

Two things a cap may not starve, and they are §19's carve-out
arriving for the third and fourth time.

A woken callback, because a pointer that recall can drop is not a
pointer.

And the **apparatus**. §16 kept `standing` out of this step's
ORDERING -- it is a claim about precedence once a rule has matched,
and letting it sort filled every shortlist with machinery. Inclusion
is a different claim, and the measurement forced it: with an ideal
table and a budget the run to quiescence got *slower* (239 ticks
against 124 exhaustive), because the better the table was at the
task the further down it pushed the rules that read, notice and
stop. Once stopping is a rule, being late to recall it is being
late to stop.

> Recall may be incomplete about what to do. It may not be
> incomplete about what you must not do -- or about whether to go on.

The cost is stated rather than hidden: a corpus that marks fifty
rules `standing` has no budget left, and that is its own claim about
what must always come to mind.

## `_in_play`

What the situation is about, as a set of relation nodes.

        The current moment's delta -- *what just changed* -- rather than the whole
        state, because a key that matches everything ranks nothing. This is the
        cheapest thing that recurs across situations, and the point of putting it
        here is that it is one method: a better answer replaces it without
        touching the loop, the table, or any rule.

         Both halves are accumulated rather than scanned, and they accumulate
        for different reasons -- which is the same asymmetry `named` measured
        when it asked whether either could be a fact. The delta half is
        **monotone by construction**: a moment's delta only ever grows, so what
        it has mentioned is a running union over a cursor. The goal half is not
        monotone -- a goal can be denied, and then it is no longer in play -- so
        it is a count maintained where the state is, not a union.

## `_attended`

What the agent is thinking ABOUT: the nodes it claims `attention` of.

        The counterpart to `_in_play`, and the difference is the point.
        `_in_play` answers *what is this situation about* with a set of
        RELATIONS, because that is what recurs across situations and so is what
        a table can be keyed on. It cannot discriminate between two goblins:
        `attack` is in play for both.

        Attention answers *what am I thinking about* with the nodes themselves,
        which is exactly the discrimination `prefer` cannot make. It is not a
        better `_in_play` -- it is the other axis, and both are read on the same
        move.

         Ground only. `attention($x)` is a rule that has not matched yet, not a
        claim about anything, and lifting on it would lift everything.

         Insertion-ordered like everything else here, because a caller ranks
        with it: a set would hand the tie-break to a hash. §3.

## `_claimed_attention`

Every standing `attention` claim, as `(node, weight)`, in graph order.

        **A claimed attention may carry its evidence count, exactly as a
        spent one does.** `attend($x, n)` has said *how much* since attention
        was built; `attention(x)` could only ever say *at all*, so a lesson
        written from experience had nowhere to put the one quantity experience
        produces -- how much the route it is about turned out to cost. The
        binary form is the same sentence with the same second member, and the
        unary form still means weight 1, so no corpus changes.

         A weight that is not a numeral is ignored rather than refused: a
        numeral is an atom whose name reads as a number, and `attention(x, soon)`
        is a claim about something else that this read has no business failing
        on. Same policy as `_priority`.

         Ground only. `attention($x)` is a rule that has not matched yet, not
        a claim about anything, and lifting on it would lift everything.

## `_deliver`

Cross the boundary, and nothing else — when the world speaks, not when
        the loop next gets round to asking.

        This is what stays machinery under §5's test, and the reason is §18's:
        a channel is **anchored** and a rule is generic, so no rule can name the
        socket a report came in on. But *being machinery* never made it a phase.
        An arrival is an external event, and an external event is not something
        the agent does; nothing about it belongs in the agent's step.

        So delivery is now the boundary calling in, the same shape as the gate's
        write hooks, and the tick lost its first line.

        This is what stays machinery under §5's test, and the reason is §18's:
        a channel is **anchored** and a rule is generic, so no rule can name the
        socket a report came in on. What the machinery deposits is therefore the
        smallest unarguable record of a boundary event --

            arrived(channel, proposition, sign)      sourced to the channel

        -- and *what that means* is a rule (`<intake>` below). Previously this
        method wrote `says(...)` directly, which made `says` a name the engine
        knew: Appendix C's census, one line of it.

        Two things improve by the split rather than merely moving. The arrival's
        uncertainty now reaches the `says` claim as a wrapper a rule can read instead of
        through a keyword argument, so nothing special-cases it. And provenance
        lands where §17 says it should: the raw arrival is the **channel** record,
        unforgeable and sourced to the socket; the `says` claim above it is
        derived, licensed by a rule, and therefore arguable.

        `says` still carries the reported sign as a member, and the entry is
        always positive -- the channel did speak. Writing `-says(c, p)` would
        claim the channel stayed silent, which is a different fact and not the
        one observed. §21 records the better answer: an arrival should be a
        moment, so a report is a signed delta.

## And the same argument one layer down, whic

**And the same argument one layer down, which situations made
visible.** The comment below says the report belongs to the agent
rather than to what the agent happens to be supposing, and that was
true of the SEAT and false of everything else on this path: the
register is inside the hypothesis, so the successor moment, the
utterance and `arrived(...)` itself were all being minted into the
hypothesis's branch and then deposited into the agent's own delta.
The entry was the agent's and its proposition was not, so a rule at
the root asking what a channel said would have found nothing
structurally -- the world's own testimony, contained inside a guess
about it. `reseat` is not enough on its own for the same reason a
successor seat was never enough on its own.

## The register is inside a hypothesis and the worl

The register is inside a hypothesis and the world has spoken. The
report belongs to the AGENT, not to what the agent happens to be
supposing -- so it lands on a successor of the agent's own seat,
which forks the chain away from the supposition's branch.

Both halves matter. Without the re-seating the entry would be
appended to a moment that already has descendants, and deposit
order is position along the walk, so a report arriving now would
read as older than everything concluded since. Without the fork it
would land inside the supposition and leave it wrapped, which is
what it did: the agent's only record of what a channel said became
`likely(says(...))` -- the world's own testimony, hedged.

## THAT THIS RULE HAS RUN, as a PROPOSITION and

THAT THIS RULE HAS RUN, as a PROPOSITION and not only as a licence.

`applied(<R>)` is already on every derived entry, because R5 needs it
for §12's weakest link -- but a licence is an entry FIELD, so no rule
can read one. That is the same shape as an entry's grade (§21 item 5)
and as a tool's binding before `answers`: something the machinery knows
and no rule can ask about. Both were closed by putting the thing in the
graph, and this is the third.

What it buys is that **deadness becomes a blocked goal**. A corpus that
wants to be sure a rule is load-bearing asserts `+goal(exercised(<R>))`;
if nothing ever runs it, backward reading finds nothing that could
conclude that, `<give-up>` writes `blocked` at `quiet`, and §19's veto
refuses to end quietly on it. No census, no watchdog registry, no
pairing of each rule with a guard -- **dying is already intercepted, so
the whole of the addition is being able to die on this.**

Once per rule, deduped like `reify`: it is a claim about the rule, not
a count of its applications, and re-concluding it every tick would be
noise quiescence has to chew through.

## §6's price, charged by §6's own test. A

**§6's price, charged by §6's own test.** A rule whose antecedent
is entirely structural is applied without a read, so it must conclude
without one: *stratum 0 must produce structure, not entries. If the
walk deposited its intermediate results as claims, it would be reading
entries and the circle would return.* So the conclusion is an ordinary
interned relation instance -- undated, unattributed, deniable by
nothing -- which is exactly what the skeleton is everywhere else.

 That is the whole of the difference between the two matchers. Same
recall, same match, same arbitration, same rule type, same surface;
one more row deciding where the consequent lands, and the row is read
off the antecedent rather than authored. §5's *one interpreter* and
§6's *one more row, not one more branch* are both true of the code now.

 Interning is what makes the fixpoint detectable: a fact already
derived mints no node, so a stratum-0 rule re-applying is a no-op and
quiescence sees it as one.

## A rule may introduce a thing that did not

**A rule may introduce a thing that did not exist.** Everything a
consequent could name until now came from a binding or was written
literally, so *there is some new person here* was unsayable -- the
binding check refuses `+named($p, $x)` with `$p` unbound, correctly,
because the gate cannot deposit a variable. `+person` says it
instead: a mark the application replaces with a node it mints, and it
is the same `+` that already signals a node coming to be.

 **One node per distinct marker per APPLICATION**, so `+a(+p)`
and `+b(+p)` in one consequent are about the same new thing, and
two firings are about two things. That is what keeps two people called
Paul apart: the mint is per occasion, not per name.

 **Refraction is what stops this running away**, and it already
exists: an instantiation fires once for a given set of premises
(`_survives` -> `_spent`), so a minting rule cannot re-fire on the
bindings it already used. What refraction does NOT stop is a
generative CHAIN -- mint, conclude about the new node, mint again --
because those are different bindings every time. Quiescence cannot see
it either: a fresh node always changes something. `bounded(ticks)` is
the backstop, and it reports after the fact.

## `_conclude_at`

A consequent member's own locus (§8), or None for the frame's topic.

         **This was parsed, boundness-checked, reified -- and ignored.**
        `text.py` refuses a consequent whose locus variable no antecedent binds,
        `_reify_locus` records it so the round trip through the graph keeps it,
        and `_apply` then wrote every conclusion at the frame's topic anyway. So
        `{ +noted($p) at $mp }` matching entries at M1 and M2 deposited BOTH at
        M2, and nothing could see it: the two differ only in a field no outcome
        check reads. §21's defect for the eleventh time, and this face of it --
        *a knob read and not obeyed* -- is the one `adopt` recorded about a
        rule's grade, arriving at the locus.
         It is also what spans needed: a span can only be a locus if a rule can
        SAY which locus it concludes at, and until this line the only locus a
        rule could ever produce was the one the frame supplied.

        The locus a rule may name is one the antecedent bound, so it is a moment
        or span already on the frame's walk. The seat check is kept anyway,
        because `reify`/`adopt` can hand this a rule nobody parsed.

         `strict=False` is for quiescence, which asks this about applications
        that may never be chosen. It answers `None` where the strict form
        refuses, so a malformed locus is reported once at the write -- where the
        rule is actually being applied and the mistake is attributable -- rather
        than from inside a verdict about a move nobody made.

## The count is taken BEFORE substitution, an

 **The count is taken BEFORE substitution, and that is the
whole of the fixpoint.** `substitute` builds the grounded node with
`g.rel`, which interns -- so the fact is created there, and a
novelty test made afterwards always finds it already present. The
loop then derived everything correctly and believed it had derived
nothing: one pass per layer, no fixpoint, and a read that answered
from a third of the candidates. It failed as a wrong ANSWER rather
than as a crash, which is the only reason the gate caught it.

## A structural fact enters no delta, so noth

 **A structural fact enters no delta, so nothing re-triggers a
rule that reads it.** Incremental matching is driven by the seat's
delta -- a `Situation` of ENTRIES -- and structure is not an entry,
by §6's whole design. So a rule mentioning a structural relation
was matched in full exactly once, on its first pass, and anything
derived after that stayed invisible to it for ever. Measured: the
stratum-0 half concluded correctly and the ordinary rule reading
its conclusion never fired at all.

 Recorded UNCONDITIONALLY, not on novelty, and that is the
interning trap for the third time in one commit. Quiescence has
already run `substitute` on this conclusion to decide whether it
would change anything -- which INTERNS it -- so by the time the
mint happens the novelty is gone and a novelty-gated record
captures nothing. Over-invalidating by relation costs one extra
full match; under-invalidating loses the conclusion permanently.

## `settle_structure`

Run the stratum-0 rules to fixpoint, layer by layer.

        §6's recall policy, and it is the whole of what makes stratum 0
        different: *recall for stratum 0 is all of them, every time -- the set
        is small and fixed, so the policy is a different table, not a different
        mechanism.* Match is the shared one, the rules are ordinary rules, and
        the conclusion is minted by the shared `_mint_structure`.

         Each LAYER to fixpoint before the next begins, because a negated
        member reads a lower layer and must read a finished one (`RuleSet.strata`).

        **Semi-naive: a rule is re-run only when something it READS has
        grown.** A rule's matches depend on exactly the relations in its
        antecedent, plus the chain, which does not move while this runs. So if
        none of them gained a fact since the rule last ran, it can produce
        nothing new and running it is pure waste -- which is what the naive
        version did, re-running every rule in the layer on every pass.

        It pays where the layer is uneven, and the read's is: `cand` is the
        expensive rule and depends on **nothing derived**, so it runs once
        instead of once per pass, while `dep_after` recurses and keeps its turn.
        **14.4s -> 5.6s** on the same 553 facts.

         And then profiling said the rest was not here at all: `has_var` was
        **91%** of what remained, asked of every instance in a bucket on every
        enumeration and re-walking the whole structure each time. Deciding it at
        mint took the same run to **0.42s**. *Measure before optimising* --
        semi-naive was the right change and the third of the total.

         This is the coarse form -- by RELATION, not by fact. True semi-naive
        would hand each rule only the facts that appeared, the way `match`'s
        `fresh` delta does for the ordinary loop; that cannot be reused here
        because `fresh` is a `Situation` of entries and these are not entries.
        The refinement is available and unmeasured.

## `_kept`

The resolved state here, kept across ticks instead of rebuilt.

        `current_state` is §4's walk and the design calls it the single most
        consequential cost: it collects every proposition the chain has ever
        claimed on this branch and `resolve`s each one. That is O(everything
        known) and it ran **twice a tick**, so it was the binding constraint the
        moment `delta` took matching out of the way.

        The same observation fixes it: a moment is a delta, so the state after
        depositing an entry is the state before, plus that one claim. What is
        kept is `proposition -> (key, entry)` where the key is `resolve`'s own
        ordering -- (locus depth, deposit depth, position) -- so a later claim
        replaces an earlier one exactly when `resolve` would have preferred it,
        and an entry about an EARLIER locus correctly loses to one about a later
        one. Nothing here re-derives the ordering; it reuses it.

         **Order is part of the answer here too, and more sharply than in
        matching.** `current_state` returns propositions **most-recently-claimed
        first**, and §18's *a description with two candidates resolves to the
        most recent* is a semantic claim that rests on it -- not a detail of the
        walk. So an updated proposition is re-inserted at the end of the dict
        and the result is read back reversed, which reproduces the walk's order
        exactly. Getting this wrong in `delta` cost four checks; it is the same
        trap, one layer down.

         A different topic or seat is a different state, so it is a cache miss
        and a full rebuild -- which is the safe direction, and what supposing,
        leaving and re-seating each want.

        **What is kept is the SITUATION, not a list.** Keeping the state and
        then materialising it -- and indexing it, and scanning it for goals --
        once per tick left the tick O(everything known) anyway, which is the
        whole of what `heap` measured and could not fix. The three consumers are
        maintained through the same one-claim-at-a-time walk that maintains the
        state: `Situation.add`/`drop` for the matcher's index, and a count per
        key for `_in_play`. A tick is then O(what changed).

         The keys are a COUNT and not a set, because two goals can put the same
        relation in play and one of them going away must not take the other's key
        with it. The same reason `emitted` had to be read off the graph: a
        derived set that forgets who contributed to it cannot be maintained.

## What is in mind, for FACTS. The agent ha

**What is in mind, for FACTS.** The agent has always narrowed
which rules come to mind -- `dormant` until something claims `due` --
and never which facts do. Same relation, second kind of thing: rows,
not branches. `fact dormant(billing)` takes a domain out of mind, and
because a domain is a channel and every loaded fact carries its
channel as its source, there is nothing to look up but what provenance
already recorded.

Measured before building it: three domains loaded and a goal in one,
23.5s over 600 ticks; with only its own domain in mind, 1.6s over 198,
and **the identical 196 conclusions**. It is the strongest lever
measured all session, because it cuts both factors -- fewer facts make
each tick cheaper AND leave fewer conclusions to draw.

 Unloading is safe to be wrong about: worst case the domain comes
back. That is exactly why it may be an ordinary defeasible rule, where
§19 insists the ESCALATION -- reaching for more when a search comes up
dry -- may not be, since a goal whose evidence is merely out of mind
would otherwise read as `blocked`.

## `_applications`

What could apply here -- carried across ticks instead of rediscovered.

        **The loop was stateless between ticks.** Every tick it re-ran every
        rule's join over the whole state, filtered the result, applied one, and
        threw the rest away; next tick it did all of it again. Measured before
        building this: 5,775 applications matched over a 600-fact corpus, of
        which **75 were new** -- 98.7% waste -- and **92.9% on the kettle
        fixture**, so this was never a big-corpus concern. It has been true since
        the first tick ever ran.

        What makes it fixable without a new representation is that §4 already
        made a moment **a signed delta**, and `Chain.deposit` already records each
        entry's position in it. *What is new since I last looked* is
        `seat.delta[pos:]` -- available all along, and not read.

        So: keep the applications, and each tick match only the delta (`match`'s
        `fresh` argument, one pass per antecedent member). Three things have to
        be right, and each is a way this could be wrong rather than merely slow.

        **A newly proposed rule has no history**, so it gets a full match. Recall
        is not fixed -- `dormant`/`due` and `_widen` change what comes to mind --
        and a rule proposed for the first time on tick 40 was never matched on
        tick 39.

        **The cache belongs to a seat**, because a `Situation` does. Supposing
        forks, `_leave` returns, `_deliver` reseats; each is a different state and
        a cache miss, which is the safe direction.

         **And an application can stop being applicable, which is the part
        that is not merely bookkeeping.** The chain is append-only but `resolve`
        is not monotone: a denial deposited later makes what an application
        consumed no longer the current claim. So each cached application is
        indexed by the propositions it consumed, and a fresh entry about one of
        those re-checks exactly those applications -- an application survives iff
        every entry it consumed is still what `resolve` returns. That is why this
        cannot be a *seen it* set: quiescence has to keep being able to change
        its mind.

## ...and its cached applications with it, be

 **...and its cached applications with it, because a
full re-match can only ADD.** Dropping the cursor asks for
the rule to be matched again, and step 2's merge skips any
key already present -- so a re-match that NO LONGER yields
an application cannot remove it. That is invisible for a
positive member, whose application would merely be
rediscovered, and wrong for a NEGATED structural one:
negation as failure is evaluated at match time, so when the
relation it negates grows, the stale application survives
and applies.

Step 1 retires an application when a later ENTRY unsettles
what it consumed. A structural fact has no entry and sits
in no delta, so that path never sees it -- which is why the
invalidation was present, correct, and unable to help.
Measured: docs/observations.md §3.1.

## A norm is not indexed by what it forbids -- _fo

A norm is not indexed by what it forbids -- `_forbid`
consults every prohibition whose pattern shares a relation
with what is about to be written, so a new one can change
the answer for a proposition no cached verdict mentions.
Blunt on purpose: norms are authored and refusals are rare,
and a precise index here would have to reproduce `_forbid`'s
matching, which is the re-implementation trap `state`
already paid for once.

## 2. Full match for rules newly come to mind; delt

2. Full match for rules newly come to mind; delta match for the rest.

 **The position is PER RULE, and a global one is wrong.** Recall is
not fixed: a rule drops out of mind under a budget and comes back when
`_widen` fires. With one shared cursor, everything deposited while it
was away has already been consumed, so it comes back and is told
nothing is new -- and the chain a->b->c stops at b. That is one
selftest check, and it is the difference between a cache and a leak of
attention: *new* means new **to this rule**, not new to the loop.
Rules mostly share a cursor, so the delta they are shown is mostly the
same one: built per distinct start rather than per rule.

## The stamp, assigned once and never recomputed: a

The stamp, assigned once and never recomputed: an entry's node
is minted from a monotonic counter at deposit, so descending
node order IS most-recently-claimed-first. Measured equivalent
to the recomputed state position over 2,452 ticks, against an
inverted control that disagreed about 686 moves.

`seq` only breaks ties the stamp cannot have -- two candidates
of one rule with the same consumed entries are the same
candidate -- and exists so the heap never compares a `key`,
which holds a frozenset and is not orderable.

## Order is part of the answer, not a detail

 **Order is part of the answer, not a detail of how it was found.**
§18's last tiebreak is authored order and §14 keeps arbitration total,
so *which application is chosen* can turn on where it sat in the list.
A full match yields them in state order, nested-loop over each
antecedent member; a cache yields them in the order they were
discovered, which is tick order. Those differ the moment anything is
deposited, and five checks failed on exactly that -- a description
resolving to the wrong candidate, a plan binding to the wrong sibling.

So the order is reconstructed rather than inherited: rules in the order
recall proposed them, and within a rule, lexicographically by where
each consumed entry sits in the current state -- which is precisely
what the nested loop would have produced.

## Only what could still have something to do

**Only what could still have something to do.** This used to walk
every application ever found, on every tick, and hand them all to five
O(candidates) passes -- which is where the quadratic was, and why
remembering each application's VERDICT bought a constant factor and
left the exponent alone: caching a verdict removes the cost per
candidate, not the candidate.

`live` is maintained where the facts change rather than recomputed:
an application joins it when it is found, leaves when `_would_change`
records that it is a no-op, and rejoins when the entry that made it one
is superseded. So a tick costs O(new + revived), not O(everything).
There is no longer an exception: `supersedes` compared consumed entries
between two applications and so could not be answered from a list one of
them might be missing from, which put the whole set through at the old
cost. With that relation gone, the fast path is the only path.

## What defeat must NOT be given is this li

 **What `defeat` must NOT be given is this list**, and that is the
whole difficulty of the change. `rules.defeat` runs before quiescence
on purpose -- *defeat is about whose antecedent holds, not about who
still has work to do* -- so a rule whose conclusion is already written
must go on defeating its rival, or the boss's rule is obeyed once and
the vice's quietly overwrites it on the next tick. Withholding the
quiet applications from the candidate list is right; withholding them
from defeat is that bug.

So the rules that MATCHED are carried separately, which the trail
reads, and maintaining it costs a set per rule.

## Sorted, because arbitrate picks the FIRS

 **Sorted, because `arbitrate` picks the FIRST among applications of
one rule and until now nothing said which that was.** The heap orders
by consumed entries and then by insertion; this list was in match
order; and the two agreed only because two applications of one rule
could not previously share their consumed entries. A structural member
binds without consuming (§12), so they can -- and `ugm.arbitration`
reported the divergence the hour it became possible.

§10's rule, one level up: *a deterministic computation whose result
depends on an undeclared enumeration order has a tie-break nobody
authored*. Node identity is the stamp everywhere else here, so it is
the stamp here.

## `_instantiation`

What a rule application IS, for the purpose of firing once.

        The rule and **the entries it consumed** -- not its bindings. That
        distinction is the whole difference between this and the dedup `_enter`
        deleted, which keyed on the assumption alone and made a hypothesis
        unfinishable: *explore `broken(pipe)` […] then be told `wet(pipe)`, and
        the hypothesis is never revisited*.

        Being told something new deposits a new ENTRY, so an application that
        consumes it is a different instantiation and runs on its own. An
        application whose premises have not moved is the same one, and repeating
        it derives nothing the first did not.

        The bindings are in the key as well, and leaving them out cost 12 checks
        before it cost anything else. A structural or computed member **consumes
        no entry** -- `match` drops its slot -- so a stratum-0 rule's consumed
        tuple is empty for *every* binding, and keying on premises alone made
        such a rule fire once in its life. That took out the recursion over
        spans, hypothesis explanation and norm retirement together. Premises say
        *what the world showed*; bindings say *which case this is*, and firing
        once means once per case.

## A refused write never happened -- §19 runs the v

A refused write never happened -- §19 runs the veto *before* the
deposit, so "a forbidden entry never exists, not even briefly". An
instantiation fires once when it fires; being turned away at the gate
is not firing, and marking it spent would make refusal permanent.
That is the property measured earlier in this session and nearly lost
here: withdraw the prohibition and the rule applies on its own, which
is `arbitration-is-scheduling`'s *a loser is deferred, not rejected*
holding at the gate as well as in the chooser.

## ...and RETIRE it, rather than leaving it in the

...and RETIRE it, rather than leaving it in the candidate set to be
skipped. Measured: filtering it in `_survives` instead cost the two
optimisations this loop was built around -- `live` and `apps` came out
the same size, which that check's own comment calls the sign that
withholding "has silently stopped working", and weighing went back to
quadratic (60 facts: 1,950 candidates weighed; 120: 7,500). Returning
early from `_survives` skips `_would_change`, so no no-op verdict is
ever cached and every spent candidate is re-walked for ever. A spent
instantiation cannot fire again while its frame lives, so it does not
belong in the candidate set at all.
WITHHELD, not retired. Retiring it outright also removes it from
`by_rule`, and the record of which rules matched here is read from
that. When precedence still existed this was sharper still: an
overriding rule that had fired once stopped counting as having matched
and the defeat silently lapsed, which cost 11 checks. The application
stays on the record; it only leaves the live set, which is the same
treatment a no-op verdict gets.

## `_contest`

The price of refraction, paid rather than accepted.

        Firing once turns a loud contradiction into a silent one. `<grant>`'s
        runaway was not a rule misbehaving: `implies` says *whenever A, B*, and
        the corpus asserted `-B` while `A` still held. The 194 acts were the
        engine believing both. Refraction stops the symptom and leaves the
        contradiction in place -- which is the one failure mode this design is
        least willing to buy, and §8 already names it as unowned: *is this moment
        consistent? is a query somebody must run, and the design does not say
        who.*

        So this is who, for exactly the case refraction creates: a spent
        instantiation's conclusion is denied **while its premises still stand**.
        That is the loop, caught at the moment it would have started, and
        deposited as `contested(<R>, <what>)` for a corpus to answer.

        Cheap because it is indexed by the proposition being written, like
        `_forbid`: a denial about something no spent rule concluded costs one
        dict lookup.

## `_would_change`

Quiescence: an application that restates what the chain already says is
        not a step. Without this the loop would reapply every rule forever, and
        *nothing left to do* would be unsayable.

        **And it was the agent recomputing its entire option set on every
        move.** Profiled at 38% of runtime, ~800 calls a tick; measured before
        this was built, on a chain of `edge` facts:

        | facts | ticks | calls | re-tests returning the SAME answer |
        |---|---|---|---|
        | 200 | 202 | 40,400 | 99.0% |
        | 500 | 502 | 251,000 | 99.6% |
        | 1,000 | 1,002 | 1,002,000 | **99.8%** |

        Third instance of one observation -- `delta` found 98.7% of matching was
        re-derivation, `state` found the walk was rebuilding what a delta could
        extend, and this is *nothing remembers that this question was already
        answered*. The answer is kept beside the applications, in the same cache
        and retired by the same discipline, because it is the same kind of claim.

         **What the measurement corrected.** The cost was assumed to be the
        chain walk; it is the smallest of the three parts. At 1,000 facts:
        `_forbid` 5.31s, `substitute` 3.94s, `resolve` 1.10s. A cache is the
        right fix anyway -- it skips all three -- but *optimise the walk* would
        have bought the least of them.

        **What the verdict depends on**, which is what makes it cacheable: the
        resolves of the propositions this application would write, plus the
        prohibitions consulted about them. Nothing else. So a fresh entry about
        one of those retires it (`quiet_by_prop`), a fresh `forbidden` or
        `refused` flushes the lot, and a fork misses because the cache belongs to
        a seat.  This is not a *seen it* set for the same reason `_applications`
        is not: `resolve` is non-monotone, so quiescence has to keep being able
        to change its mind.

## A stratum-0 verdict is never cached, and f

 **A stratum-0 verdict is never cached, and finding out why took a
runaway.** The cache retires a verdict when a proposition it READ
changes (`quiet_by_prop`); a stratum-0 rule reads no proposition, so
`touched` is empty and a `True` cached on the first tick is never
retired by anything. The same application then applies for ever --
measured at 60 ticks of `applied`, identical bindings, on a rule that
had already drawn its conclusion.

It costs nothing to skip the cache here: the verdict is a
substitution and a count, where the ordinary one is a resolve per
conclusion plus the prohibitions consulted about it.

## A stratum-0 rule is asked about the GRAPH,

 **A stratum-0 rule is asked about the GRAPH, not the state.** Its
conclusion is structure, so it never enters the chain, so `resolve`
below answers `None` for it forever and quiescence says *yes, this
changes something* on every tick. Measured before fixing: a corpus rule
reading the raw chain ran 40 ticks of `applied` and never once went
quiet. The rule was right, the conclusion was right, and the loop could
not tell it had already drawn it.

Monotone, which is why this is sound to cache with no index: a
skeleton fact cannot be denied, so once minting it adds nothing, that
stays true. `resolve` is non-monotone and needs `quiet_by_prop`; this
does not.
 And it asks WITHOUT BUILDING, which is the interning trap's fourth
appearance and the only one that was a semantic defect rather than
bookkeeping. `substitute` interns, so a verdict computed with it makes
the conclusion exist -- and the next caller is told there is nothing to
do. `ugm.arbitration` runs the fast path and the slow one over the same
state, and reported the fast path choosing a move the slow path found
nothing for: **one path's question consumed the other's answer.**
`already_there` is the same walk with no minting in it.

## Genuinely generic: the rule's consequent names s

Genuinely generic: the rule's consequent names something its
antecedent never bound, and there is nothing to deposit. A
conclusion that contains variables because it is ABOUT a rule
is a different case entirely, and dropping it here is how a
rule reasoning about rules used to look exactly like a rule
with nothing to do -- silently, and only at this line.

`touched` stays empty, deliberately: this verdict is a property
of the rule and its bindings, so nothing can ever change it and
it is cached with no index at all.

## At the consequent's OWN locus, and this is

 **At the consequent's OWN locus, and this is the same defect
as the write's twice over.** Quiescence asked whether the
proposition already holds at the frame's TOPIC -- so a rule
concluding `+taking_turns($a, $b) at $s` was told *nothing to do*
the moment any span had it, and §13's recursion produced its first
recognition and stopped. Fixing the write alone was not enough:
the loop never reached the write, because the verdict was computed
about a different locus than the one the conclusion would land at.

## `_is_mention`

Is this application talking ABOUT rules rather than in them?

        §14 says the use/mention distinction is settled by *who is writing* --
        the machinery reifying a rule mentions, a rule's consequent uses. That is
        too strong, and running it is how the gap showed: a rule whose antecedent
        matched `con($r, $pat, +)` binds `$pat` to a stored pattern, and anything
        it concludes about `$pat` is a **ground claim that happens to contain
        variables**. A rule's consequent can mention.

        What tells them apart is inheritance rather than authorship:

        > **Mention propagates through bindings. A conclusion drawn from a
        > mentioned entry is itself a mention.**

        That is checkable rather than declared -- the entries match consumed are
        already recorded, because R5 needs them for the trail. This is the trail
        being load-bearing for something other than explanation, which §16 argues
        is the pattern to expect.

        Inheritance has to start somewhere, and `app.rule.mentions` is the
        source: a rule AUTHORED naming a rule -- `+resume($h, <cb>)`, the `<...>`
        marker the surface already reads for facts -- is mentioning. Without it a
        rule that attaches a rule to something concludes a structurally generic
        proposition from entries that are not mentions, and quiescence drops it
        as *nothing to do*.

## `web`

For each relation name: how often it is READ (an antecedent member)
        and WRITTEN (a consequent member, or a fact deposited).

        **Meaning in an open class is given by the web.** A name nothing
        ever draws a conclusion from, or nothing ever establishes, means nothing
        -- so a corpus containing one is silently smaller than it looks. This is
        the price of §2's open class paying for its own detection: nothing else
        in the engine could tell a proposition awaiting its meaning from a typo.

        Here rather than in an instrument because the loader warns with it and
        `ugm.vocabulary` maps with it, and a second implementation of a thing
        that indexes what it re-implements is what `state` paid for once.

         **A VARIABLE in relation position is not a name, and reporting one
        was this instrument's own bug.** `+$kind($item)` applies a class held in
        a variable (§4's *a class as data*), and `relation_of` answers with the
        variable node, which `show` prints as `$kind`. So a corpus using the
        feature was told nothing writes a relation it never named -- the rule
        derives correctly and the checker called it a defect. Found by sweeping
        the 239 machines the suite builds, which is the only way it could have
        been: the corpus that uses it is inline in a Python fixture, where none
        of this tooling reaches. **The bare variable, distorting a measurement
        for the fourth time.**

## `review`

*Which rules earned the outcome?* -- asked of a finished episode.

        **Offline, and that is a position rather than an implementation detail.**
        Credit needs the outcome and the outcome is not known until the episode
        ends, so nothing here runs in the loop and nothing about the loop changes.
        It is also why this is a method and not a request answered at `quiet`: a
        run that ends satisfied ends at `stopped`, which is terminal, and the
        episodes most worth learning from are exactly the ones that went well.

        **It needs no new bookkeeping**, which is the finding that made it
        buildable. R5 already licenses every derived entry with `applied(<R>)`
        because the trail is load-bearing for §12's weakest link -- so walking
        back from what was achieved reaches the rules that produced it, and only
        those. Measured on a corpus with two ways to get water: the walk returns
        the rule that was used and not the rule that was available.

        What it deposits is `helped(<R>, <key>)` and no interpretation, the same
        split as every other occasion (§17). Turning that into a preference is a
        rule, because *how much a rule having helped once should count* is a
        claim and §4 puts claims in data.

        The key is the goal's **relation**, not the goal. That is the only choice
        here that could have gone otherwise, and it is forced by wanting anything
        to transfer: a row keyed on `boiling(kettle)` is true of one episode.

## `blame`

*Which rules cost the agent something it wanted?* -- the other half,
        and the one that only exists because a task is split into subgoals.

        **Failure at episode level has no author.** Many rules ran, one outcome
        was bad, and nothing attributes it -- which is why `review` deliberately
        refuses to blame: a failed episode may have been an impossible one.

        A lost *subgoal* is different, and the difference is §9's. Two ways a goal
        can fail to hold, and only one of them is somebody's doing:

        | no entry at all | it was never reached. Many causes, no author. |
        | an entry says `-` | something MADE it false, and that entry has a licence. |

        So blame runs the same walk as credit over a denial instead of an
        assertion, and it reaches the decision rather than the physics: measured,
        from a lost `intact(jug1)` back through the rule that broke it, the act
        that was taken, and the rule that chose the act.

        Ground goals only. Backward reading expands into generic subgoals like
        `heat($a, kettle)` which were never meant to hold as stated, and counting
        those as failures would blame every rule for every search.

## `learned`

What this episode has to say to the next one, as surface text.

        Offline learning crossing an episode boundary is a corpus being written,
        and a corpus is text -- so what an agent learned is **readable, editable
        and arguable** rather than a weight somewhere. That is not decoration:
        §19 puts experience in recall precisely because being wrong there is
        recoverable, and it is only recoverable if it can be found and denied.

        **What is written is a claim about a NODE.** A lesson used to say
        `prefer(<use-tap>, water, 3)`, which names a rule, and a rule id is
        stale the moment that rule is adopted, composed or renamed -- keyed on
        an identity, one level up from bindings. `attention(sink, 3)` names the
        thing in the world whose presence is what made the passed-up route
        available, and `_salient` is what works out which thing that is.

        Three depths, and they are the same tree they always were:

            fact +attention(sink, 3)                     depth 0, and GROUND
            { +tap($v0) } => +attention($v0, 3)          depth 0, generic
            { +precious($v1), +tap($v0) } => ...         depth 1, and so on

        The first is what this method returns; the rest are `conditional=True`
        and `refine`. Measured on §19's three-situation world, the ground row
        fixes the world it learned in and is WRONG in the next one, exactly as
        the unconditional `prefer` row was -- the defect was never the score, it
        was the depth.

         **Credit is not written any more, and that is a loss, stated.** The
        old method also recommended the rules that HELPED (`prefer(<squeeze>,
        juice, 3)`), and a rule that helped is a rule, not a node: there is no
        node-keyed sentence that says it. Measured on this world it cost
        nothing, because the credited rules had no rivals to be lifted over --
        which is the honest reason to let it go, and not an argument that credit
        is unsayable in general. §21.

## `_circumstances`

*What about this situation made that the wrong move?*

        The tests of a learned decision tree, and they are read off the trail
        rather than engineered: the ground propositions on the support of what
        was **lost**, less four kinds that cannot discriminate.

        | the lost goals themselves | the conclusion, not a circumstance |
        | machinery bookkeeping     | `goal`, `did`, `doing`, `emitted` are true of every episode |
        | what the CHOOSING rule's antecedent already requires | constant wherever the choice arises at all |
        | anything generic          | §12: a pattern is not an observation |

        What survives is what was true **here** and need not be true next time --
        which is exactly the question a tree's internal node asks. Note it needs
        no new bookkeeping either: R5 keeps the support for the weakest link, and
        this reads it. That is the fifth time.

         **All of them, as a conjunction**, and the choice is made on which error
        is recoverable -- the same judgement forgoing made. An over-specific
        condition simply does not fire, and the agent falls back to what it did
        before; an over-general one advises confidently in situations it has
        never seen. Under-advising is recoverable.

## `_salient`

What the passed-up route is ABOUT and the route that harmed is not.

        **This is the whole of what it takes to key a lesson on a NODE
        instead of on a rule**, and it needs no new bookkeeping. `_instead_of`
        already names the rule that was forgone; a rule id is exactly what goes
        stale when rules are adopted, composed or renamed, which is why `prefer`
        is going. But the two routes agree about the GOAL and disagree about
        what else must hold, and that disagreement is a set difference over
        antecedent relations:

            <use-tap>   goal, tap, under
            <use-jug>   goal, jug, holds
            ----------------------------
            sink        spoken of under `tap` and `under` -- and nothing the
                        jug route requires

        So the lesson is *attend to the tap*, and it transfers to a kettle the
        agent was never told about because a tap is what it names.

         **The test is the LIFT ITSELF, and it has to be, because a
        proxy for it wrote a lesson that could not work.** Attention lifts a
        rule when the attended node is spoken of under a relation that rule's
        antecedent names (`attention._pull`), so *does this node separate the
        two routes* is answerable exactly: lift the alternative, lift neither
        chooser. An earlier version scored candidates by *fewest of the harmed
        route's relations* and took the best available -- which in the vase
        world named `jug1`, a node both routes speak of under `holds`. The
        lesson was written, was well-formed, loaded, and moved nothing.

         **So this returns None, and a whole arm of §19 goes with it.**
        Where two routes are about the SAME things -- `holds(jug1, kettle)` and
        `holds(vase, kettle)`, differing only in which vessel -- there is no
        node that lifts one and not the other, and no attention lesson exists to
        be found. `prefer` names a rule and so could always separate them. That
        is the price of keying on nodes, it is not recoverable by trying harder
        here, and `ugm.learning` measures it rather than this docstring merely
        asserting it.

         Ordered, never a set: the smaller proposition first, then the order
        the state was walked in. §3 -- a derived result does not come out of a
        hash.

## `_generalise`

Render ground propositions as one generic antecedent.

        Every constant becomes a variable, **shared across the conjunction** so
        that `completes(jug1, heirlooms), precious(jug1)` becomes
        `completes($v0, $v1), precious($v0)` -- the join is what makes it a claim
        about a *kind* of situation rather than a longer way of naming this one.

        Generalising is nearly unconstrained here, and that is a property of
        the shape rather than luck: an attention consequent contains exactly ONE
        variable and the antecedent's binder is what bound it, so the loader's
        rule that a consequent variable must be bound by the antecedent is
        satisfied by construction. A learned rule that concluded about the world
        would not have that freedom.

         `names` is an OUT parameter, and it is not a convenience. An
        attention lesson concludes ABOUT A NODE -- `+attention($v0)` -- so its
        consequent variable has to be the one this method happened to assign to
        that node, and a caller that guessed would be writing a rule whose
        conclusion is unbound. Handing the map back is what keeps the naming in
        one place.

## `_advice_rows`

One learned rule per promoted alternative, plus its `standing` line.

        **The BINDER is always in the antecedent, and it is what makes
        an attention lesson generalise at all.** A rule may only conclude about
        a variable its antecedent binds, and this one concludes `+attention($v)`
        -- so the salient node has to be named in a member. `tap($v0)` is that
        member, and pruning may take every test away but never it. Pruned to
        nothing else, the lesson reads *whatever plays the tap's part here, that
        is what to think about*, which transfers to a kettle the agent was never
        told about.

         The name carries no rule id: `<learned-water-tap>` is the want and
        the binder's relation. That is the whole reason for the rewrite, and a
        name is the easiest place to leak the thing you just removed.

         `standing` for the same reason it was needed before -- a learned rule
        whose tests mention `goal($w)` is otherwise read by forgoing as a rival
        way of getting the same want, and passed up before it can advise.

## `refine`

Drop the tests that do not pay. §4's *compose what never surprised*,
        from the other end: **decompose what turns out not to matter.**

        `learned(conditional=True)` takes every circumstance it can see, because
        an over-specific rule fails safe -- it does not fire and the agent falls
        back. But failing safe repeatedly is still failing, and nothing in one
        episode can say which of its circumstances was the operative one. Only
        more episodes can, so this is reduced-error pruning over corpus text:
        greedy backward elimination against a `cost` the caller supplies.

        **Ties go to the MORE GENERAL rule** (`<=`, not `<`). That is the only
        judgement in here, and it is the standard one: between two hypotheses that
        explain the evidence equally, the one with fewer conditions transfers
        further. The opposite bias would keep every accident of the episode it
        learned from.

        `cost(rows) -> number` is the caller's, and it must be, because what an
        episode cost is a question about a world and this object is not one. It
        is also why this is offline and outside the loop, like everything else
        experience does.

         What this is NOT is mutation. It only ever *removes* a test it already
        had; it cannot add one it never saw, merge two rules, or revisit a tree
        that has stopped paying. Those are §21.

## STEEPEST descent, not first-improvement, and

 STEEPEST descent, not first-improvement, and the difference is not
a refinement of a refinement -- it decides whether this works at all.
Taking the first drop that ties prunes the tree to NOTHING: measured,
`{precious, completes}` dropped `precious` for an equal score, then
dropped `completes` for an equal score, and arrived at the
unconditional row it was supposed to improve on -- while dropping
`completes` FIRST scores strictly better and is the answer. A tie is
not evidence that a test is worthless; it is evidence that THIS drop
is neutral, and another may not be.

## `_instead_of`

The live alternatives to what cost the agent something.

        Blame names the rule that did the damage; it is silent about what else
        was available, because the rule that was passed up never ran and so is on
        no trail. **Forgoing already recorded it.** `forgone(A, w)` is deposited
        when `A` was a live way of getting `w` and something else was taken, and
        it is licensed by `applied(<winner>)` -- so *what did I do instead of A*
        is a question the deposit already answers.

        Joining them needs no new bookkeeping, which is the same result credit
        assignment had: a blamed winner names its own forgone alternatives, and
        those are exactly the rules worth promoting. Neither half is a signal
        alone -- blame without forgoing suppresses into the same choice, and
        forgoing without blame recommends whatever was passed up for any reason.

         An alternative that is itself blamed earns nothing; `learned` filters
        both halves through the same suppression, so a world whose every route
        does damage recommends none of them rather than the least-examined one.

## `_rendered`

The session, RENDERED out of the graph -- corpora, in the order they
        were read.

        **There is no journal.** The first version kept one: a Python list
        of everything that came in. It was a side-channel duplicating the chain,
        in a design whose whole thesis is that nothing the machinery knows may
        be unaskable by a rule -- and a kept list can drift from the graph,
        where a rendering cannot. Everything it held was already here:

            the corpus text        rules are nodes; connective, antecedent and
                                   consequent all reprint
            which facts were told  `licence = loaded(p)`, `source = <domain>`
            what the world said    `arrived(c, p, sign)` entries
            the scope of each      `scoped(<domain>, <scope>)`, deposited by the
                                   loader as an ordinary claim about itself

         What is rendered is a **corpus**, never entries. §13 scores *authors
        write entries natively* as a leak -- supply a deposit and you can date a
        claim to when it was not held -- so a saved session replays through the
        ordinary loading path and earns its stamps again.

## `induce`

Grow a decision tree with MORE THAN ONE LEAF, from more than one episode.

    `refine` prunes a single path. A tree is several: *in situations like this
    prefer X; in situations like that prefer Y.* Each episode proposes one leaf --
    the alternative it wishes it had taken, conditioned on what was true when it
    went wrong -- and the leaves are then pruned **jointly** against a cost the
    caller measures.

    **Wrong leaves are expected, and pruning is what makes that safe.** An
    episode only ever knows the cost of the route it ACTUALLY took, so an episode
    that broke a jug proposes *prefer the tap* whether or not the tap is worse --
    which is the oscillation `lesser_of_two_evils` measures, arriving as an
    ordinary over-general hypothesis. Reduced-error pruning is exactly the
    instrument for that: a leaf that does not pay is dropped, and the oscillation
    stops being a special case needing its own mechanism.

    Two edits, one search (steepest descent, as `refine` had to learn): drop a
    whole leaf, or drop one test from a leaf. Ties go to the smaller tree -- fewer
    leaves and fewer conditions both transfer further.

     It still cannot ADD a test no episode saw, nor merge two leaves into one.
    Those are mutation proper, and they are affordable for the same reason the
    rest is: every leaf concludes `attention`, which cannot act, so a bad
    candidate costs ticks and nothing else.

## `advice`

`attention($v, n)`, or `possible(...)` when nothing was observed.

        **How sure is a WRAPPER, not a field**, and this was the argument
        that eventually deleted grades outright. §21's item 5 was that a grade
        is a Python field on the entry, so no rule can read one -- a confidence
        unreadable by the very rules that would act on it. A wrapper is an
        ordinary node, so the lift does not see a wrapped claim at all (an unsure
        lesson must not silently steer), and a corpus rule decides whether to
        take it up:

            rule <venture> = implies( { +possible(attention($x, $n)), +exploring },
                                      { +attention($x, $n) } )

        So **explore/exploit stops being machinery and becomes a claim** --
        defeasible, deniable, on the trail, and switched by an ordinary fact. The
        default with no such rule is to exploit, which is the conservative one.

         And the test is constant-free, which §15 went to some trouble for:
        `observed` versus `never tried` is a distinction the trail makes, not a
        threshold anybody chose. A route the agent has taken is asserted; one it
        has only reasoned about is hedged.

## The synthetic row for an unproposed route is

**The synthetic row for an unproposed route is GONE, and nothing
replaced it.** It existed because a `prefer` row could be written for any
rule from its name alone, so the lesser of two evils could be stated about
a route nobody regretted. An attention lesson cannot be written that way:
it names a node, and which node is salient is a question about an episode
that actually faced the choice. It turns out not to be needed -- the
oscillation tries both routes, so both leaves arrive on their own by the
second episode. Measured; see `ugm.learning`.

## ORDER MATTERS ON A PLATEAU, and this is wher

 ORDER MATTERS ON A PLATEAU, and this is where the search failed.
Reaching the good tree needs TWO edits -- drop the unconditional leaf
AND drop a test -- each individually neutral. A greedy walk that
accepts ties therefore gets wherever the trial order sends it, and the
first version dropped the GOOD leaf and collapsed to the very
unconditional row it was meant to beat.

So ties are broken by doubting the LEAST SPECIFIC leaf first. That is
not a tuning knob: a leaf with no tests fires in every situation, which
makes it the strongest claim in the tree and the first that should have
to earn its place. Leaf-drops before test-drops, fewest tests first.

## `forest`

Many trees over different episodes, combined by union.

    `induce` grows one tree from everything the agent has been through, which
    means one unlucky episode is in every leaf it produces. Bagging is the usual
    answer -- grow several trees from overlapping subsets and combine them.

     **MEASURED, AND IT DOES NOT PAY -- one tree beats the bag.** On the
    situation-dependent fixture: one tree 1, forest 2, nothing 4. The reason is
    recorded in `ugm.learning`, which gates it:

    > **Attention is MONOTONE.** One over-general leaf attends the tap and the
    > leaves that decline cannot take it back, because there is no sentence for
    > *not this one, here* -- `unattend` clears the whole queue.

    What a forest here would need is a combination rule that can REMOVE rather
    than only add -- `dormant` is the obvious candidate and is untried.
    Left as a measured negative result with a gate, not deleted: the day
    ensembling starts paying, the gate fails and sends someone here.

     **THE UNANIMITY HEDGE IS GONE, and it had already stopped running.**
    It grepped each row for `prefer(<` and wrapped what the trees disagreed
    about as `possible(prefer(...))`, which `_priority` declined to count. When
    lessons moved from `prefer` rows to `attention` rows the grep stopped
    matching, so every row came through unwrapped and the unanimity test decided
    nothing -- silently, for a whole session. Deleted rather than re-keyed onto
    `attention`, because the argument it rested on is gone with `_priority`:
    there is no reader that counts an asserted claim and declines a wrapped one,
    so a hedge here would have to be obeyed by a corpus rule instead. `induce`
    still hedges its own unobserved leaves (`advice`), which is a different
    claim -- *never tried* rather than *my trees disagree*.

     The subsets are contiguous slices, not random draws: §3 forbids reading a
    derived result out of an unseeded source, and a bagged forest whose bags are
    unseeded is that bug wearing a hat. Deterministic bags, reproducible trees.

## `_delta` and `_contents`

The gap between two spans, materialised.

    A tool, and it has to be one: a rule cannot speak about the set of its
    matches, so a delta cannot be a rule. `<difference>` answers the request
    `delta(<have>, <want>, <gap>)` with the gap node and writes one
    `missing(<gap>, p)` / `extra(<gap>, p)` per difference, which is what an
    ordinary rule can read.

    It PROPOSES, like every tool: the gap is a record of what was computed, and
    a rule decides whether any of it is worth wanting. `{ +missing(<gap>, $p) }
    => { +goal($p) }` is the whole of turning a gap into a plan, and no plan
    machinery is involved.

    `_contents` says what a span holds. A moment holds what is asserted there,
    minus the apparatus's own records -- a corpus's vocabulary is not the
    apparatus's, and a gap computed against the machinery reports the machinery
    as work to be done. Anything else holds its direct members: one deep,
    because `at(work)` is a proposition in the span and `at` and `work` are
    what that proposition is made of.

    A description is not a difference: a member with a variable in it says
    which states would count, not that one of them is absent, so it is skipped
    rather than reported.

    **The empty gap is deposited too, and that is the half that matters.**
    `matched(<gap>)` lands when nothing differed. A rule can read every
    difference one at a time and still never conclude that there were none:
    `no missing($g, $p)` is a negative existential -- *for no $p* -- and the
    loader refuses it, correctly. The tool has seen the whole set and is the
    only party that can say so, which is what makes satisfaction expressible as
    an ordinary rule: `{ +matched($g) } => { +enough($g) }`.

## `_intercept`, `_producing`, `_obey`

The trigger seam: what a corpus may say about what a rule is about to write.

    One place, and it is the moment between *the rule concluded this* and *this
    was written*. Before it, there is nothing to speak about; after it, the
    entry exists and taking it back is a denial, which is an ordinary rule's
    job and not a trigger's.

     **`producing(<R>, p)` is synthesised and never deposited.** The
    trigger is matched against the current state PLUS those entries, in a
    Situation built for the question and thrown away. Depositing them would
    make the chain say a rule had concluded something it had not, and every
    later read would inherit it.

    A trigger may replace, drop, or add, which was the decision taken when this
    was built -- the alternative was veto-and-add only, which cannot express
    the wrapper case at all. The price is exactly the two things the choice
    named: the trail must say who rewrote what (`rewrote(<T>, old, new)`, and
    `why` reads it), and two triggers on one conclusion need an order (the
    table's, so a corpus can change it with `standing`).

     A trigger does not intercept itself, or a trigger that concluded about
    its own conclusions would have no fixpoint to reach.

     The cost when no corpus has any: one dict lookup. `_claims_any` asks the
    graph whether anything claims `intercepts` before anything is built, and a
    tree with no triggers runs the suite in the same time it did before --
    21.95s against 22.08s, measured.
